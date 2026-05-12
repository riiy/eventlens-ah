#!/usr/bin/env python3
"""
EventLens AH MVP 自动验收脚本

对 30 条标注样本逐一走完 7 步闭环，按验收标准逐项打分，
输出 JSON 结果文件 + 控制台摘要。

用法:
  python tests/acceptance/run_acceptance.py \
    --samples tests/acceptance/samples.json \
    --api-base http://localhost:8000

验收阈值 (来自验收文档):
  JSON 解析成功率 >= 95%
  字段完整率 >= 95%
  错误资产映射率 <= 15%
  买卖建议次数 = 0
  噪音标记高分率 <= 10%
  核心链路完成率 >= 90%
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── 验收阈值 ───────────────────────────────────────────────
THRESHOLDS = {
    "json_parse_success_rate": 0.95,
    "field_completeness_rate": 0.95,
    "wrong_asset_mapping_rate": 0.15,
    "buy_sell_recommendation_count": 0,
    "noise_flagged_as_high_score_rate": 0.10,
    "core_pipeline_completion_rate": 0.90,
}

# 买卖建议敏感词
BUY_SELL_KEYWORDS = [
    "买入", "卖出", "建议买入", "建议卖出", "推荐买入", "推荐卖出",
    "建仓", "减仓", "加仓", "清仓", "买入评级", "卖出评级",
    "强烈推荐", "买入推荐", "卖出推荐", "做多", "做空",
    "buy", "sell", "long", "short", "recommend buying", "recommend selling",
]

# 事件必填字段
EVENT_REQUIRED_FIELDS = [
    "event_type", "event_summary", "primary_entity", "market_scope",
    "direction", "materiality_score", "novelty_score", "urgency_score",
    "confidence_score", "risk_score",
]

HYPOTHESIS_REQUIRED_FIELDS = [
    "hypothesis_text", "impact_chain", "supporting_evidence",
    "counter_evidence", "trigger_conditions", "invalidation_conditions",
]


class AcceptanceRunner:
    def __init__(self, samples_path: str, api_base: str):
        self.api_base = api_base.rstrip("/")
        self.samples = self._load_samples(samples_path)
        self.results = []
        self.summary = {}

    def _load_samples(self, path: str) -> list[dict]:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        samples = data if isinstance(data, list) else data.get("samples", [])
        if not samples:
            print(f"ERROR: No samples found in {path}")
            sys.exit(1)
        return samples

    # ── HTTP helpers ────────────────────────────────────────

    def _post(self, path: str, body: dict | None = None) -> tuple[int, dict | list | None]:
        url = f"{self.api_base}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            return e.code, {"error": body}
        except Exception as e:
            return 0, {"error": str(e)}

    def _get(self, path: str) -> tuple[int, dict | list | None]:
        url = f"{self.api_base}{path}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            return e.code, {"error": body}
        except Exception as e:
            return 0, {"error": str(e)}

    # ── Per-sample pipeline ──────────────────────────────────

    def run_sample(self, sample: dict, index: int) -> dict:
        doc = sample["document"]
        annotations = sample.get("annotations", {})
        result = {
            "sample_id": sample.get("id", f"sample_{index:03d}"),
            "index": index,
            "title": doc.get("title", ""),
            "steps": {},
            "checks": {},
            "errors": [],
        }

        # Step 1: 信息入库
        status, created_doc = self._post("/api/raw-documents/", {
            "source": doc.get("source", "acceptance_test"),
            "source_type": doc.get("source_type", "news"),
            "title": doc.get("title", ""),
            "content": doc.get("content", ""),
            "language": doc.get("language", "zh"),
            "url": doc.get("url"),
            "published_at": doc.get("published_at"),
        })
        if status not in (200, 201) or not isinstance(created_doc, dict):
            result["steps"]["ingest"] = {"ok": False, "error": str(created_doc)}
            result["errors"].append("step1_ingest_failed")
            return result
        result["steps"]["ingest"] = {"ok": True, "document_id": created_doc["id"]}
        doc_id = created_doc["id"]

        # Step 2: 事件抽取
        status, events = self._post("/api/events/extract", {"document_ids": [doc_id]})
        if status not in (200, 201) or not isinstance(events, list):
            result["steps"]["extract"] = {"ok": False, "error": str(events)}
            result["errors"].append("step2_extract_failed")
            return result

        if len(events) == 0:
            # No event extracted — check if that's expected
            should_gen = annotations.get("should_generate_event", True)
            is_noise = annotations.get("is_noise", False)
            result["steps"]["extract"] = {
                "ok": not should_gen,
                "event_count": 0,
                "expected_no_event": not should_gen or is_noise,
            }
            if should_gen and not is_noise:
                result["errors"].append("step2_no_event_extracted")
            return result

        event = events[0]
        result["steps"]["extract"] = {"ok": True, "event_id": event["id"], "event": event}
        event_id = event["id"]

        # Validate JSON parse + field completeness
        result["checks"]["json_parse_ok"] = True
        result["checks"]["field_completeness"] = self._check_fields(
            event, EVENT_REQUIRED_FIELDS
        )
        result["checks"]["has_buy_sell"] = self._scan_buy_sell(event)

        # Check expected direction
        expected_dir = annotations.get("expected_direction")
        if expected_dir and event.get("direction") != expected_dir:
            result["checks"]["direction_match"] = False
            result["checks"]["direction_expected"] = expected_dir
            result["checks"]["direction_actual"] = event.get("direction")

        # Step 3: 标的映射
        status, links = self._post(f"/api/events/{event_id}/map-assets")
        if status not in (200, 201):
            result["steps"]["map"] = {"ok": False, "error": str(links)}
            result["errors"].append("step3_map_failed")
            return result

        links_list = links if isinstance(links, list) else []
        result["steps"]["map"] = {"ok": True, "asset_count": len(links_list), "links": links_list}

        # Check wrong asset mapping
        expected_assets = annotations.get("expected_assets", [])
        if expected_assets:
            mapped_symbols = {l.get("symbol", "") for l in links_list}
            expected_set = set(expected_assets)
            wrong = mapped_symbols - expected_set
            result["checks"]["wrong_assets"] = list(wrong)
            result["checks"]["wrong_asset_count"] = len(wrong)

        if len(links_list) == 0:
            # No assets mapped — hypothesis generation will fail
            result["steps"]["hypothesis"] = {"ok": False, "reason": "no_assets"}
            result["steps"]["score"] = {"ok": False, "reason": "no_assets"}
            result["steps"]["price"] = {"ok": False, "reason": "no_assets"}
            return result

        # Step 4+5: 假设生成 (含风险反证)
        status, hypothesis = self._post(f"/api/events/{event_id}/generate-hypothesis")
        if status in (200, 201) and isinstance(hypothesis, dict):
            result["steps"]["hypothesis"] = {"ok": True, "hypothesis": hypothesis}
            result["checks"]["hypothesis_field_ok"] = self._check_fields(
                hypothesis, HYPOTHESIS_REQUIRED_FIELDS
            )
            result["checks"]["has_counter_evidence"] = (
                len(hypothesis.get("counter_evidence", [])) > 0
            )
            result["checks"]["has_trigger_conditions"] = (
                len(hypothesis.get("trigger_conditions", [])) > 0
            )
            result["checks"]["has_invalidation_conditions"] = (
                len(hypothesis.get("invalidation_conditions", [])) > 0
            )
            result["checks"]["has_impact_chain"] = (
                len(hypothesis.get("impact_chain", [])) > 0
            )
            result["checks"]["hypo_has_buy_sell"] = self._scan_buy_sell(hypothesis)
        else:
            result["steps"]["hypothesis"] = {"ok": False, "error": str(hypothesis)}
            result["errors"].append("step4_hypothesis_failed")

        # Step 6: 打分排序
        status, scored = self._post(f"/api/events/{event_id}/score")
        if status in (200, 201) and isinstance(scored, dict):
            result["steps"]["score"] = {"ok": True, "alpha_score": scored.get("event_alpha_score")}
            # 噪音检查: is_noise sample should not get high alpha
            if annotations.get("is_noise"):
                result["checks"]["noise_alpha"] = scored.get("event_alpha_score", 0)
                result["checks"]["noise_flagged_high"] = scored.get("event_alpha_score", 0) > 0.6
        else:
            result["steps"]["score"] = {"ok": False, "error": str(scored)}

        # Step 7: 后续表现记录
        status, reactions = self._post(f"/api/events/{event_id}/price-reactions")
        if status in (200, 201) and isinstance(reactions, list):
            result["steps"]["price"] = {"ok": True, "reaction_count": len(reactions)}
        else:
            result["steps"]["price"] = {"ok": False, "error": str(reactions)}

        return result

    # ── Checks ──────────────────────────────────────────────

    def _check_fields(self, obj: dict, required: list[str]) -> bool:
        return all(obj.get(f) is not None for f in required)

    def _scan_buy_sell(self, obj: dict) -> list[str]:
        text = json.dumps(obj, ensure_ascii=False).lower()
        return [kw for kw in BUY_SELL_KEYWORDS if kw.lower() in text]

    # ── Run all & report ─────────────────────────────────────

    def run(self) -> dict:
        print(f"\n{'='*60}")
        print(f"  EventLens AH MVP 自动验收")
        print(f"  样本数: {len(self.samples)}")
        print(f"  API: {self.api_base}")
        print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*60}\n")

        for i, sample in enumerate(self.samples):
            sid = sample.get("id", f"sample_{i:03d}")
            print(f"[{i+1:02d}/{len(self.samples)}] {sid}: {sample['document'].get('title', '')[:60]}")
            result = self.run_sample(sample, i)
            self.results.append(result)

            # Print per-sample status
            step_oks = []
            for step_name in ["ingest", "extract", "map", "hypothesis", "score", "price"]:
                step = result["steps"].get(step_name, {})
                icon = "✓" if step.get("ok") else "✗"
                step_oks.append(f"{step_name}={icon}")
            print(f"         {' | '.join(step_oks)}")
            if result.get("checks", {}).get("has_buy_sell"):
                print(f"         !! BUY/SELL keywords: {result['checks']['has_buy_sell']}")
            if result.get("errors"):
                print(f"         ERRORS: {', '.join(result['errors'])}")

        return self._compute_summary()

    def _compute_summary(self) -> dict:
        n = len(self.results)

        # Step-level pass rates
        step_ok = {name: 0 for name in ["ingest", "extract", "map", "hypothesis", "score", "price"]}
        json_parse_ok = 0
        field_complete_ok = 0
        total_buy_sell = 0
        total_wrong_assets = 0
        total_asset_checks = 0
        noise_count = 0
        noise_high_score = 0
        counter_evidence_ok = 0
        hypo_count = 0
        errors_by_type: dict[str, int] = {}

        for r in self.results:
            for name in step_ok:
                if r["steps"].get(name, {}).get("ok"):
                    step_ok[name] += 1
            if r["checks"].get("json_parse_ok"):
                json_parse_ok += 1
            if r["checks"].get("field_completeness"):
                field_complete_ok += 1
            buy_sell = r["checks"].get("has_buy_sell", [])
            total_buy_sell += len(buy_sell)
            if "wrong_asset_count" in r.get("checks", {}):
                total_asset_checks += 1
                total_wrong_assets += r["checks"]["wrong_asset_count"]
            if r["steps"].get("hypothesis", {}).get("ok"):
                hypo_count += 1
                if r["checks"].get("has_counter_evidence"):
                    counter_evidence_ok += 1
            # noise check
            sample = self.samples[r["index"]] if r["index"] < len(self.samples) else {}
            if sample.get("annotations", {}).get("is_noise"):
                noise_count += 1
                if r["checks"].get("noise_flagged_high"):
                    noise_high_score += 1
            for err in r.get("errors", []):
                errors_by_type[err] = errors_by_type.get(err, 0) + 1

        # Pipeline completion rate
        core_complete = sum(
            1 for r in self.results
            if all(r["steps"].get(s, {}).get("ok") for s in ["ingest", "extract", "map"])
        )

        summary = {
            "total_samples": n,
            "step_pass_rates": {k: v / n for k, v in step_ok.items()},
            "step_pass_counts": step_ok,
            "json_parse_rate": json_parse_ok / n,
            "field_completeness_rate": field_complete_ok / n,
            "buy_sell_count": total_buy_sell,
            "wrong_asset_count": total_wrong_assets,
            "wrong_asset_checked_count": total_asset_checks,
            "core_completion_rate": core_complete / n,
            "noise_count": noise_count,
            "noise_high_score_count": noise_high_score,
            "noise_high_score_rate": noise_high_score / noise_count if noise_count > 0 else 0,
            "hypothesis_with_counter_evidence": counter_evidence_ok,
            "hypothesis_total": hypo_count,
            "errors_by_type": errors_by_type,
        }

        # Threshold checks
        summary["thresholds"] = {
            "json_parse": (summary["json_parse_rate"] >= THRESHOLDS["json_parse_success_rate"]),
            "field_completeness": (summary["field_completeness_rate"] >= THRESHOLDS["field_completeness_rate"]),
            "wrong_asset": (
                summary["wrong_asset_count"] / summary["wrong_asset_checked_count"]
                <= THRESHOLDS["wrong_asset_mapping_rate"]
            ) if summary["wrong_asset_checked_count"] > 0 else True,
            "buy_sell": (summary["buy_sell_count"] == THRESHOLDS["buy_sell_recommendation_count"]),
            "noise": (summary["noise_high_score_rate"] <= THRESHOLDS["noise_flagged_as_high_score_rate"]),
            "core_completion": (summary["core_completion_rate"] >= THRESHOLDS["core_pipeline_completion_rate"]),
        }
        summary["all_thresholds_pass"] = all(summary["thresholds"].values())

        self.summary = summary
        return summary

    def print_summary(self):
        s = self.summary
        print(f"\n{'='*60}")
        print(f"  验收摘要")
        print(f"{'='*60}\n")

        print("── 流水线步骤通过率 ──")
        for name, count in s["step_pass_counts"].items():
            rate = s["step_pass_rates"][name]
            bar = "█" * int(rate * 20) + "░" * (20 - int(rate * 20))
            print(f"  {name:12s}  {count:2d}/{s['total_samples']:2d}  {bar}  {rate*100:5.1f}%")

        print(f"\n── 质量指标 ──")
        print(f"  JSON 解析成功率:        {s['json_parse_rate']*100:5.1f}%  (阈值 >= {THRESHOLDS['json_parse_success_rate']*100:.0f}%)")
        print(f"  字段完整率:              {s['field_completeness_rate']*100:5.1f}%  (阈值 >= {THRESHOLDS['field_completeness_rate']*100:.0f}%)")
        print(f"  买卖建议次数:            {s['buy_sell_count']}        (阈值 = {THRESHOLDS['buy_sell_recommendation_count']})")
        if s["wrong_asset_checked_count"] > 0:
            wrong_rate = s["wrong_asset_count"] / s["wrong_asset_checked_count"]
            print(f"  错误资产映射:            {wrong_rate*100:5.1f}%  (阈值 <= {THRESHOLDS['wrong_asset_mapping_rate']*100:.0f}%)")
        print(f"  噪音高分率:              {s['noise_high_score_rate']*100:5.1f}%  (阈值 <= {THRESHOLDS['noise_flagged_as_high_score_rate']*100:.0f}%)")
        print(f"  核心链路完成率:          {s['core_completion_rate']*100:5.1f}%  (阈值 >= {THRESHOLDS['core_pipeline_completion_rate']*100:.0f}%)")
        if s["hypothesis_total"] > 0:
            print(f"  假设含反证:              {s['hypothesis_with_counter_evidence']}/{s['hypothesis_total']}")

        print(f"\n── 阈值判定 ──")
        for check, passed in s["thresholds"].items():
            icon = "✓" if passed else "✗"
            label = {
                "json_parse": "JSON 解析",
                "field_completeness": "字段完整",
                "wrong_asset": "资产映射",
                "buy_sell": "买卖建议",
                "noise": "噪音高分",
                "core_completion": "核心链路",
            }.get(check, check)
            print(f"  {icon} {label}")

        if s["errors_by_type"]:
            print(f"\n── 错误分布 ──")
            for err, count in sorted(s["errors_by_type"].items(), key=lambda x: -x[1]):
                print(f"  {err}: {count}")

        print(f"\n── 总体结果 ──")
        if s["all_thresholds_pass"]:
            print(f"  [32m验收通过[0m")
        else:
            print(f"  [31m验收不通过 — {sum(1 for v in s['thresholds'].values() if not v)} 项未达标[0m")
        print()

    def save_results(self, output_path: str):
        report = {
            "report_type": "EventLens AH MVP Acceptance Test",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "api_base": self.api_base,
            "thresholds_used": THRESHOLDS,
            "summary": {
                k: v for k, v in self.summary.items()
                if k != "thresholds"
            },
            "threshold_checks": self.summary.get("thresholds", {}),
            "all_thresholds_pass": self.summary.get("all_thresholds_pass", False),
            "per_sample": self.results,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Detailed results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="EventLens AH MVP Acceptance Test")
    parser.add_argument(
        "--samples",
        default=os.path.join(os.path.dirname(__file__), "samples.json"),
        help="Path to samples JSON file",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="Base URL of the running backend API",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for detailed JSON results",
    )
    args = parser.parse_args()

    # Resolve samples path
    samples_path = Path(args.samples)
    if not samples_path.exists():
        print(f"ERROR: Samples file not found: {samples_path}")
        sys.exit(1)

    runner = AcceptanceRunner(str(samples_path), args.api_base)
    runner.run()
    runner.print_summary()

    # Save results
    if args.output:
        runner.save_results(args.output)
    else:
        out_dir = Path(__file__).parent
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        runner.save_results(str(out_dir / f"acceptance_results_{timestamp}.json"))

    # Exit code
    if not runner.summary.get("all_thresholds_pass", False):
        sys.exit(1)


if __name__ == "__main__":
    main()