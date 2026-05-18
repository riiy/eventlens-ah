import json
import re

import httpx
from loguru import logger

from app.llm.base import BaseLLMProvider
from app.schemas.llm_outputs import (
    AssetMappingOutput,
    ExtractedEventOutput,
    HypothesisOutput,
)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Generic OpenAI-compatible JSON-output provider."""

    def __init__(
        self,
        model_name: str,
        api_key: str | None,
        base_url: str,
        *,
        missing_api_key_message: str = "API key is not configured.",
    ) -> None:
        super().__init__(model_name)
        self.api_key = api_key
        resolved_base_url = base_url.rstrip("/")
        if resolved_base_url.endswith("/chat/completions"):
            resolved_base_url = resolved_base_url[: -len("/chat/completions")]
        self.base_url = resolved_base_url
        self.missing_api_key_message = missing_api_key_message
        if not self.api_key:
            logger.warning("{}", self.missing_api_key_message)

    @staticmethod
    def _extract_json_object(content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    @staticmethod
    def _normalize_score(value: object, default: float = 0.5) -> float:
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
        if isinstance(value, str):
            token = value.strip().lower()
            label_map = {
                "very low": 0.1,
                "low": 0.25,
                "medium": 0.5,
                "moderate": 0.5,
                "high": 0.75,
                "strong": 0.8,
                "very high": 0.95,
            }
            if token in label_map:
                return label_map[token]
            try:
                return max(0.0, min(1.0, float(token)))
            except ValueError:
                return default
        return default

    @staticmethod
    def _normalize_string_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            parts = re.split(r"[\n,;|]+", text)
            return [part.strip() for part in parts if part.strip()]
        return [str(value).strip()]

    def _normalize_extracted_event(self, data: dict) -> dict:
        normalized = dict(data)
        normalized["related_entities"] = self._normalize_string_list(
            normalized.get("related_entities")
        )
        normalized["risk_flags"] = self._normalize_string_list(
            normalized.get("risk_flags")
        )
        for field in (
            "materiality_score",
            "novelty_score",
            "urgency_score",
            "confidence_score",
            "risk_score",
        ):
            normalized[field] = self._normalize_score(normalized.get(field), 0.5)
        normalized["event_type"] = str(
            normalized.get("event_type", "other")
        ).strip() or "other"
        normalized["market_scope"] = str(
            normalized.get("market_scope", "UNKNOWN")
        ).strip() or "UNKNOWN"
        normalized["direction"] = str(
            normalized.get("direction", "UNKNOWN")
        ).strip() or "UNKNOWN"
        normalized["event_summary"] = str(
            normalized.get("event_summary", "")
        ).strip()
        normalized["primary_entity"] = str(
            normalized.get("primary_entity", "")
        ).strip()
        normalized["reasoning_summary"] = str(
            normalized.get("reasoning_summary", "")
        ).strip()
        return normalized

    def _normalize_asset_mapping(self, data: dict) -> dict:
        links = []
        for raw_link in data.get("asset_links", []):
            link = dict(raw_link)
            link["symbol"] = str(link.get("symbol", "")).strip()
            link["name"] = str(link.get("name", "")).strip()
            link["market"] = str(link.get("market", "UNKNOWN")).strip() or "UNKNOWN"
            link["impact_direction"] = (
                str(link.get("impact_direction", "NEUTRAL")).strip() or "NEUTRAL"
            )
            link["impact_strength"] = self._normalize_score(
                link.get("impact_strength"), 0.5
            )
            link["confidence_score"] = self._normalize_score(
                link.get("confidence_score"), 0.7
            )
            link["reason"] = str(link.get("reason", "")).strip()
            if link["symbol"]:
                links.append(link)
        return {"asset_links": links}

    def _normalize_hypothesis(self, data: dict) -> dict:
        normalized = dict(data)
        for field in (
            "impact_chain",
            "supporting_evidence",
            "counter_evidence",
            "trigger_conditions",
            "invalidation_conditions",
        ):
            normalized[field] = self._normalize_string_list(normalized.get(field))
        risk_notes = normalized.get("risk_notes")
        if isinstance(risk_notes, list):
            normalized["risk_notes"] = "; ".join(
                item.strip() for item in map(str, risk_notes) if item.strip()
            )
        else:
            normalized["risk_notes"] = str(risk_notes or "").strip()
        normalized["hypothesis_text"] = str(
            normalized.get("hypothesis_text", "")
        ).strip()
        normalized["time_horizon"] = str(
            normalized.get("time_horizon", "")
        ).strip()
        return normalized

    async def _call_api(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> dict:
        if not self.api_key:
            raise NotImplementedError(self.missing_api_key_message)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
            if not isinstance(content, str):
                raise ValueError("LLM response content is not a string")
            return self._extract_json_object(content)

    async def extract_event(
        self, title: str, content: str, source: str, published_at: str
    ) -> ExtractedEventOutput:
        system_prompt = (
            "You extract structured market-event JSON from financial news or company "
            "announcements. Return JSON only. "
            "event_type must be one of: earnings_surprise, policy_change, "
            "merger_acquisition, product_launch, regulatory_action, geopolitical, "
            "industry_disruption, management_change, market_anomaly, other. "
            "market_scope must be one of: A_SHARE, HK_SHARE, BOTH, UNKNOWN. "
            "direction must be one of: POSITIVE, NEGATIVE, NEUTRAL, MIXED, UNKNOWN. "
            "All scores must be floats in [0,1]. related_entities and risk_flags "
            "must be arrays of strings."
        )
        user_prompt = {
            "title": title,
            "content": content,
            "source": source,
            "published_at": published_at,
            "required_fields": {
                "event_type": "string",
                "event_summary": "string",
                "primary_entity": "string",
                "related_entities": ["string"],
                "market_scope": "string",
                "direction": "string",
                "materiality_score": 0.0,
                "novelty_score": 0.0,
                "urgency_score": 0.0,
                "confidence_score": 0.0,
                "risk_score": 0.0,
                "reasoning_summary": "string",
                "risk_flags": ["string"],
            },
        }
        data = await self._call_api(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ]
        )
        return ExtractedEventOutput.model_validate(
            self._normalize_extracted_event(data)
        )

    async def map_event_to_assets(
        self,
        event_summary: str,
        event_type: str,
        primary_entity: str,
        assets: list[dict],
    ) -> AssetMappingOutput:
        system_prompt = (
            "You map a market event to relevant assets. Return JSON only. "
            "Return {'asset_links': [...]} where each link contains symbol, name, market, "
            "impact_direction, impact_strength, reason, confidence_score. "
            "impact_direction must be one of POSITIVE, NEGATIVE, NEUTRAL, MIXED. "
            "Only include assets that are directly relevant."
        )
        user_prompt = {
            "event_summary": event_summary,
            "event_type": event_type,
            "primary_entity": primary_entity,
            "assets": assets,
        }
        data = await self._call_api(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ]
        )
        return AssetMappingOutput.model_validate(self._normalize_asset_mapping(data))

    async def generate_hypothesis(
        self,
        event_summary: str,
        event_type: str,
        linked_assets: list[dict],
    ) -> HypothesisOutput:
        system_prompt = (
            "You generate a concise investment research hypothesis from an event and its "
            "linked assets. Return JSON only with: hypothesis_text, impact_chain, "
            "supporting_evidence, counter_evidence, trigger_conditions, "
            "invalidation_conditions, time_horizon, risk_notes. All list fields must "
            "be arrays of strings."
        )
        logger.debug(
            "Generating hypothesis with event_summary={}, event_type={}, linked_assets={}",
            event_summary,
            event_type,
            linked_assets,
        )
        user_prompt = {
            "event_summary": event_summary,
            "event_type": event_type,
            "linked_assets": linked_assets,
        }
        data = await self._call_api(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
            ]
        )
        return HypothesisOutput.model_validate(self._normalize_hypothesis(data))
