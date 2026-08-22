from __future__ import annotations

import csv
import json
import os
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import CONFIG
from src.llm.diagnostics import build_provider_diagnostics, classify_response_format, infer_parser_failure_reason
from src.llm.prompt_builder import build_structured_prompt
from src.llm.request_config import LIVE_BASE_URL, LIVE_MODEL, LIVE_PROVIDER_NAME, build_live_request_kwargs, create_live_client
from src.llm.response_parser import parse_llm_response_details
from src.safety.route_conflict import get_route_ids, routes_compatible, validate_conflict_matrix

OUTPUT_ROOT = PROJECT_ROOT / "results" / "diagnostics" / "provider_reliability_v1"
REQUEST_COUNT = 50
VARIANTS = (
    (404, 4),
    (505, 4),
    (606, 4),
    (404, 8),
    (505, 8),
)
VALID_ACTIONS = {"PROCEED", "WAIT", "FREE"}


def _build_traffic_state(seed: int, vehicle_count: int) -> list[dict[str, object]]:
    rnd = random.Random(seed)
    route_ids = get_route_ids()
    chosen_routes = rnd.choices(route_ids, k=vehicle_count)
    states: list[dict[str, object]] = []
    for index, route_id in enumerate(chosen_routes):
        states.append(
            {
                "vehicle_id": f"smoke_v{vehicle_count}_s{seed}_{index}",
                "route_id": route_id,
                "speed": round(3.0 + index * 0.5, 2),
                "distance_to_intersection": round(18.0 - index * 2.5, 2),
                "time_to_intersection": round(6.0 + index * 0.75, 2),
                "inside_control_zone": True,
            }
        )
    return states


def _build_policy_hints(states: list[dict[str, object]]) -> dict[str, object]:
    priority_vehicle = min(states, key=lambda state: state.get("time_to_intersection", float("inf")))
    priority_route = str(priority_vehicle.get("route_id", ""))
    compatible_routes = [
        str(state["route_id"])
        for state in states
        if priority_route and routes_compatible(priority_route, str(state["route_id"]))
    ]
    return {
        "priority_vehicle_id": priority_vehicle["vehicle_id"],
        "priority_route_id": priority_route,
        "controlled_vehicle_count": len(states),
        "compatible_routes_with_priority": compatible_routes,
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def main() -> int:
    api_key = os.getenv("GROQ_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise SystemExit("PROVIDER_RELIABILITY_SMOKE_BLOCKED_NO_API_KEY")

    client = create_live_client(base_url=LIVE_BASE_URL, api_key=api_key)
    output_root = OUTPUT_ROOT
    output_root.mkdir(parents=True, exist_ok=True)

    attempts: list[dict[str, object]] = []
    variants = [VARIANTS[index % len(VARIANTS)] for index in range(REQUEST_COUNT)]

    for request_index, (seed, vehicle_count) in enumerate(variants, start=1):
        states = _build_traffic_state(seed, vehicle_count)
        prompt = build_structured_prompt(states, validate_conflict_matrix(), _build_policy_hints(states))
        vehicle_ids = [state["vehicle_id"] for state in states]
        start = time.perf_counter()
        response = None
        response_text = ""
        raw_decisions, validated_decisions, parser_success = parse_llm_response_details("", vehicle_ids)
        exception = None
        fallback_triggered = False
        fallback_reason = ""
        provider_request_success = False
        try:
            response = client.chat.completions.create(
                model=LIVE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                **build_live_request_kwargs(),
            )
            provider_request_success = True
            if response is not None and getattr(response, "choices", None):
                choice = response.choices[0]
                message = getattr(choice, "message", None)
                response_text = getattr(message, "content", "") or ""
            raw_decisions, validated_decisions, parser_success = parse_llm_response_details(response_text, vehicle_ids)
            fallback_reason = "" if parser_success else "PARSER_FAILURE"
        except Exception as exc:  # pragma: no cover - smoke failures are captured in output
            exception = exc
            fallback_triggered = True
            fallback_reason = "PROVIDER_REQUEST_EXCEPTION"

        elapsed_ms = (time.perf_counter() - start) * 1000
        diagnostics = build_provider_diagnostics(
            provider_name=LIVE_PROVIDER_NAME,
            model_name=LIVE_MODEL,
            response=response,
            parser_input=response_text,
            parser_success=parser_success,
            parser_action=raw_decisions.get(vehicle_ids[0], "MISSING") if vehicle_ids else "",
            parser_failure_reason="" if parser_success else infer_parser_failure_reason(response_text, parser_success, raw_decisions.get(vehicle_ids[0], "")),
            fallback_triggered=fallback_triggered,
            fallback_reason=fallback_reason,
            exception=exception,
            latency_ms=elapsed_ms,
            provider_request_attempted=True,
            provider_request_success=provider_request_success,
        )
        diagnostics.update(
            {
                "request_index": request_index,
                "seed": seed,
                "vehicle_count": vehicle_count,
                "prompt_vehicle_ids": vehicle_ids,
                "response_format_category": classify_response_format(response_text),
                "validated_decision_count": sum(1 for action in validated_decisions.values() if action in VALID_ACTIONS),
                "response_text_length": len(response_text),
            }
        )
        attempts.append(diagnostics)

    success_rows = [row for row in attempts if _bool(row.get("provider_request_success"))]
    failure_rows = [row for row in attempts if not _bool(row.get("provider_request_success"))]
    parser_success_rows = [row for row in success_rows if _bool(row.get("parser_success"))]
    latency_values = [float(row.get("latency_ms") or 0.0) for row in attempts]
    completion_values = [row.get("completion_tokens") for row in success_rows if row.get("completion_tokens") is not None]
    reasoning_values = [row.get("reasoning_tokens") for row in success_rows if row.get("reasoning_tokens") is not None]

    summary = {
        "repository": str(PROJECT_ROOT),
        "provider": LIVE_PROVIDER_NAME,
        "base_url": LIVE_BASE_URL,
        "model": LIVE_MODEL,
        "request_count": len(attempts),
        "success_count": len(success_rows),
        "failure_count": len(failure_rows),
        "success_rate": (len(success_rows) / len(attempts)) if attempts else 0.0,
        "parser_success_count": len(parser_success_rows),
        "parser_success_given_success": (len(parser_success_rows) / len(success_rows)) if success_rows else 0.0,
        "retry_count_distribution": dict(Counter(str(row.get("retry_count")) for row in attempts)),
        "http_status_distribution": dict(Counter(str(row.get("http_status")) for row in attempts if row.get("http_status") not in (None, ""))),
        "exception_type_distribution": dict(Counter(str(row.get("exception_type")) for row in failure_rows if row.get("exception_type"))),
        "failure_reason_distribution": dict(Counter(str(row.get("fallback_reason")) for row in failure_rows if row.get("fallback_reason"))),
        "response_format_distribution": dict(Counter(str(row.get("response_format_category")) for row in attempts)),
        "mean_latency_ms": (sum(latency_values) / len(latency_values)) if latency_values else 0.0,
        "median_latency_ms": statistics.median(latency_values) if latency_values else 0.0,
        "mean_completion_tokens": (sum(float(value) for value in completion_values) / len(completion_values)) if completion_values else 0.0,
        "mean_reasoning_tokens": (sum(float(value) for value in reasoning_values) / len(reasoning_values)) if reasoning_values else 0.0,
        "completion_tokens_values": sorted({int(value) for value in completion_values}),
        "reasoning_tokens_values": sorted({int(value) for value in reasoning_values}),
        "retry_after_seconds_values": sorted({row.get("retry_after_seconds") for row in attempts if row.get("retry_after_seconds") not in (None, "")}),
        "gate_passed": len(success_rows) / len(attempts) >= 0.95 if attempts else False,
        "parser_gate_passed": (len(parser_success_rows) / len(success_rows) >= 0.95) if success_rows else False,
        "evidence_path": str(output_root),
    }

    _write_json(output_root / "provider_reliability_smoke_summary.json", summary)
    _write_json(output_root / "provider_reliability_smoke_trace.json", attempts)
    (output_root / "provider_reliability_smoke_trace.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in attempts) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["gate_passed"] and summary["parser_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
