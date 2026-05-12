#!/usr/bin/env python3
"""
Adapter: drive EventLens AH API with the acceptance pack's 31 test cases,
export results in the pack's expected JSONL format for scoring.

Usage:
  python tests/acceptance/run_with_pack.py \
    --cases /data/eventlens_ah_acceptance_pack/fixtures/acceptance_cases.jsonl \
    --api-base http://localhost:8000 \
    --output /data/eventlens_ah_acceptance_pack/outputs/system_results.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


class PackAdapter:
    """Drives the EventLens AH API and exports pack-format JSONL."""

    def __init__(self, api_base: str):
        self.api_base = api_base.rstrip("/")

    # ── HTTP helpers ──────────────────────────────────────────────

    def _post(self, path: str, body: dict | None = None) -> tuple[int, Any]:
        url = f"{self.api_base}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode(errors="replace")
            return e.code, {"error": body_text}
        except Exception as exc:
            return 0, {"error": str(exc)}

    def _get(self, path: str) -> tuple[int, Any]:
        url = f"{self.api_base}{path}"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode(errors="replace")
            return e.code, {"error": body_text}
        except Exception as exc:
            return 0, {"error": str(exc)}

    # ── Per-case pipeline ────────────────────────────────────────

    def run_case(self, case: dict) -> dict:
        case_id = case["case_id"]

        # Step 1: Create document
        status, doc = self._post("/api/raw-documents/", {
            "source": case.get("source", "acceptance_test"),
            "source_type": case.get("source_type", "news"),
            "title": case.get("title", ""),
            "content": case.get("content", ""),
            "language": "zh",
            "url": f"acceptance://{case_id}",
            "published_at": case.get("published_at"),
        })
        if status not in (200, 201) or not isinstance(doc, dict):
            return self._empty_result(case_id, f"document_create_failed: {doc}")

        doc_id = doc["id"]

        # Step 2: Extract event
        status, events = self._post("/api/events/extract", {"document_ids": [doc_id]})
        if status not in (200, 201) or not isinstance(events, list) or len(events) == 0:
            return self._empty_result(case_id, None, generated=False)

        event = events[0]
        event_id = event["id"]

        # Step 3: Map assets
        self._post(f"/api/events/{event_id}/map-assets")

        # Step 4: Generate hypothesis
        self._post(f"/api/events/{event_id}/generate-hypothesis")

        # Step 5: Score
        self._post(f"/api/events/{event_id}/score")

        # Step 6: Price reactions
        self._post(f"/api/events/{event_id}/price-reactions")

        # Give async operations a moment to settle
        time.sleep(0.3)

        # Step 7: Gather results from detail endpoints
        _, event_detail = self._get(f"/api/events/{event_id}")
        _, assets_data = self._get(f"/api/events/{event_id}/assets")
        _, hypotheses_data = self._get(f"/api/events/{event_id}/hypotheses")
        _, llm_runs = self._get(f"/api/events/{event_id}/llm-runs")

        return self._normalize(case_id, event_detail, assets_data, hypotheses_data, llm_runs)

    def _empty_result(self, case_id: str, error: str | None = None, generated: bool = False) -> dict:
        result: dict = {
            "case_id": case_id,
            "generated_event": generated,
            "event_type": "",
            "event_summary": "",
            "primary_entity": "",
            "market_scope": "",
            "direction": "",
            "materiality_score": 0.0,
            "novelty_score": 0.0,
            "urgency_score": 0.0,
            "credibility_score": 0.0,
            "confidence_score": 0.0,
            "risk_score": 0.0,
            "event_alpha_score": 0.0,
            "asset_links": [],
            "hypothesis": {},
            "llm_run": {},
        }
        if error:
            result["error"] = error
        return result

    def _normalize(
        self,
        case_id: str,
        event: dict | None,
        assets: list | None,
        hypotheses: list | None,
        llm_runs: list | None,
    ) -> dict:
        if not isinstance(event, dict):
            return self._empty_result(case_id, "event_detail_failed")

        hypothesis = {}
        if isinstance(hypotheses, list) and len(hypotheses) > 0:
            hyp = hypotheses[0]
            hypothesis = {
                "hypothesis_text": hyp.get("hypothesis_text", ""),
                "impact_chain": hyp.get("impact_chain", ""),
                "supporting_evidence": hyp.get("supporting_evidence", []),
                "counter_evidence": hyp.get("counter_evidence", []),
                "trigger_conditions": hyp.get("trigger_conditions", []),
                "invalidation_conditions": hyp.get("invalidation_conditions", []),
                "time_horizon": hyp.get("time_horizon", ""),
                "risk_notes": hyp.get("risk_notes", ""),
            }

        asset_links = []
        if isinstance(assets, list):
            for a in assets:
                if isinstance(a, dict):
                    asset_links.append({
                        "symbol": a.get("symbol", ""),
                        "impact_direction": a.get("impact_direction", ""),
                        "impact_strength": a.get("impact_strength", 0),
                        "reason": a.get("reason", ""),
                        "confidence_score": a.get("confidence_score", 0),
                    })

        llm_run = {}
        if isinstance(llm_runs, list) and len(llm_runs) > 0:
            first = llm_runs[0]
            llm_run = {
                "model_name": first.get("model_name", ""),
                "prompt_version": first.get("prompt_version", ""),
                "input_hash": first.get("input_hash", ""),
                "latency_ms": first.get("latency_ms"),
            }

        return {
            "case_id": case_id,
            "generated_event": bool(event.get("event_type") or event.get("event_summary")),
            "event_type": event.get("event_type", ""),
            "event_summary": event.get("event_summary", ""),
            "primary_entity": event.get("primary_entity", ""),
            "market_scope": event.get("market_scope", ""),
            "direction": event.get("direction", ""),
            "materiality_score": event.get("materiality_score") or 0.0,
            "novelty_score": event.get("novelty_score") or 0.0,
            "urgency_score": event.get("urgency_score") or 0.0,
            "credibility_score": event.get("credibility_score") or 0.0,
            "confidence_score": event.get("confidence_score") or 0.0,
            "risk_score": event.get("risk_score") or 0.0,
            "event_alpha_score": event.get("event_alpha_score") or 0.0,
            "asset_links": asset_links,
            "hypothesis": hypothesis,
            "llm_run": llm_run,
        }

    # ── Run all ───────────────────────────────────────────────────

    def run(self, cases: list[dict], output_path: Path) -> int:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        total = len(cases)
        ok_count = 0

        with output_path.open("w", encoding="utf-8") as out:
            for i, case in enumerate(cases):
                case_id = case["case_id"]
                print(f"[{i+1:02d}/{total}] {case_id}: {case.get('title', '')[:70]}", end=" ", flush=True)

                result = self.run_case(case)
                out.write(json.dumps(result, ensure_ascii=False) + "\n")
                out.flush()

                if result.get("generated_event") or "error" in result:
                    ok_count += 1

                status_str = ""
                if result.get("error"):
                    status_str = f"ERROR: {result['error'][:60]}"
                elif result.get("generated_event"):
                    status_str = f"event={result['event_type']}, alpha={result.get('event_alpha_score', 0):.3f}, assets={len(result.get('asset_links', []))}"
                else:
                    status_str = "no_event"
                print(status_str)

        print(f"\nDone. {ok_count}/{total} cases processed. Output: {output_path}")
        return 0


def load_cases(path: Path) -> list[dict]:
    cases: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run EventLens AH acceptance tests against the external pack"
    )
    parser.add_argument(
        "--cases", required=True, type=Path,
        help="Path to acceptance_cases.jsonl from the pack",
    )
    parser.add_argument(
        "--api-base", default="http://localhost:8000",
        help="Base URL of the running backend",
    )
    parser.add_argument(
        "--output", required=True, type=Path,
        help="Output path for system_results.jsonl",
    )
    args = parser.parse_args()

    if not args.cases.exists():
        print(f"ERROR: cases file not found: {args.cases}")
        sys.exit(1)

    cases = load_cases(args.cases)
    print(f"Loaded {len(cases)} cases from {args.cases}")
    print(f"API base: {args.api_base}")
    print(f"Output: {args.output}\n")

    adapter = PackAdapter(args.api_base)
    adapter.run(cases, args.output)


if __name__ == "__main__":
    main()