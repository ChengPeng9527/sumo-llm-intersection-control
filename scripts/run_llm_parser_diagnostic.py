from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import CONFIG
from src.controllers.decision_pipeline import execute_decision_pipeline
from src.llm.diagnostics import build_provider_diagnostics, classify_response_format, infer_parser_failure_reason
from src.llm.request_config import build_live_client_kwargs, build_live_request_kwargs
from src.llm.prompt_builder import build_structured_prompt
from src.llm.response_parser import parse_llm_response_details
from src.safety.route_conflict import validate_conflict_matrix

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


OUTPUT_ROOT = Path(CONFIG["results_dir_path"]) / "diagnostics" / "llm_parser_diagnostic"
DEFAULT_ATTEMPTS = max(3, min(5, int(os.getenv("LLM_DIAGNOSTIC_ATTEMPTS", "3"))))


def _build_minimal_traffic_state() -> list[dict]:
    return [
        {
            "vehicle_id": "diag_car0",
            "route_id": "N_S",
            "speed": 5.0,
            "distance_to_intersection": 12.0,
            "time_to_intersection": 2.4,
            "inside_control_zone": True,
        }
    ]


def _build_policy_hints(traffic_state: list[dict]) -> dict:
    priority_vehicle = traffic_state[0]
    return {
        "priority_vehicle_id": priority_vehicle["vehicle_id"],
        "priority_route_id": priority_vehicle["route_id"],
        "controlled_vehicle_count": len(traffic_state),
        "compatible_routes_with_priority": [priority_vehicle["route_id"]],
    }


def _get_provider_config() -> tuple[str, str, str, str]:
    groq_key = os.getenv("GROQ_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if groq_key:
        return "Groq", "https://api.groq.com/openai/v1", "openai/gpt-oss-20b", groq_key
    if openrouter_key:
        return "OpenRouter", "https://openrouter.ai/api/v1", os.getenv("LLM_MODEL", "openrouter/free"), openrouter_key
    raise RuntimeError("No live provider credential available in the current session")


def _build_client(base_url: str, api_key: str):
    if OpenAI is None:
        raise RuntimeError("openai package is required for the diagnostic runner")
    return OpenAI(**build_live_client_kwargs(base_url=base_url, api_key=api_key))


def _run_single_attempt(
    *,
    client,
    provider_name: str,
    model_name: str,
    traffic_state: list[dict],
    attempt_index: int,
) -> dict:
    vehicle_ids = [state["vehicle_id"] for state in traffic_state]
    prompt = build_structured_prompt(traffic_state, validate_conflict_matrix(), _build_policy_hints(traffic_state))
    start = time.perf_counter()
    response = None
    response_text = ""
    parser_ok = False
    raw_decisions: dict[str, str] = {vid: "MISSING" for vid in vehicle_ids}
    validated_decisions: dict[str, str] = {vid: "WAIT" for vid in vehicle_ids}
    parser_failure_reason = ""
    fallback_triggered = False
    fallback_reason = ""
    exception = None
    response_format_category = "EMPTY_RESPONSE"
    provider_request_success = False

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            **build_live_request_kwargs(),
        )
        provider_request_success = True
        if response is not None and getattr(response, "choices", None):
            choice = response.choices[0]
            message = getattr(choice, "message", None)
            response_text = getattr(message, "content", "") or ""
        raw_decisions, validated_decisions, parser_ok = parse_llm_response_details(response_text, vehicle_ids)
        response_format_category = classify_response_format(response_text)
        if not parser_ok:
            parser_failure_reason = "PARSER_FAILURE"
    except Exception as exc:  # pragma: no cover
        exception = exc
        fallback_triggered = True
        fallback_reason = "PROVIDER_REQUEST_EXCEPTION"
        parser_failure_reason = "PROVIDER_REQUEST_EXCEPTION"

    elapsed_ms = (time.perf_counter() - start) * 1000
    if exception is not None:
        raw_decisions = {vid: "WAIT" for vid in vehicle_ids}
        validated_decisions = dict(raw_decisions)

    diagnostics = build_provider_diagnostics(
        provider_name=provider_name,
        model_name=model_name,
        response=response,
        parser_input=response_text,
        parser_success=parser_ok,
        parser_action=raw_decisions.get(vehicle_ids[0], "MISSING") if vehicle_ids else "",
        parser_failure_reason=parser_failure_reason,
        fallback_triggered=fallback_triggered,
        fallback_reason=fallback_reason,
        exception=exception,
        latency_ms=elapsed_ms,
        provider_request_attempted=True,
        provider_request_success=provider_request_success,
    )
    diagnostics["response_format_category"] = response_format_category
    diagnostics["llm_called"] = True
    diagnostics["llm_mode"] = "real"
    diagnostics["llm_model"] = model_name
    diagnostics["json_parse_success"] = parser_ok
    diagnostics["fallback_used"] = fallback_triggered
    diagnostics["parser_failure_reason"] = infer_parser_failure_reason(
        response_text,
        parser_ok,
        diagnostics["parser_action"],
    )

    trace = execute_decision_pipeline(
        traffic_state,
        raw_decisions,
        stage_mode="raw",
        llm_meta=diagnostics,
    )
    first_vehicle = vehicle_ids[0]
    row = trace[first_vehicle]
    diagnostics.update(
        {
            "attempt_index": attempt_index,
            "validated_decision": row["validated_llm_decision"],
            "final_decision": row["final_decision"],
            "decision_source": row["decision_source"],
            "parser_input_redacted": diagnostics["parser_input_redacted"],
            "response_content_redacted": diagnostics["response_content_redacted"],
            "trace": row,
        }
    )
    return diagnostics


def _summarize(attempts: list[dict], output_root: Path) -> dict:
    return {
        "provider": attempts[0]["provider_name"] if attempts else "",
        "base_url": "https://api.groq.com/openai/v1" if attempts and attempts[0]["provider_name"] == "Groq" else "https://openrouter.ai/api/v1",
        "model": attempts[0]["model_name"] if attempts else "",
        "request_count": len(attempts),
        "parser_success_count": sum(1 for attempt in attempts if attempt["parser_success"]),
        "fallback_count": sum(1 for attempt in attempts if attempt["fallback_triggered"]),
        "provider_request_success_count": sum(1 for attempt in attempts if attempt["provider_request_success"]),
        "response_content_present_count": sum(1 for attempt in attempts if attempt["response_content_present"]),
        "unique_response_format_categories": sorted({attempt["response_format_category"] for attempt in attempts}),
        "unique_parser_failure_reasons": sorted({attempt["parser_failure_reason"] for attempt in attempts if attempt["parser_failure_reason"]}),
        "evidence_path": str(output_root),
    }


def main() -> int:
    provider_name, base_url, model_name, api_key = _get_provider_config()
    client = _build_client(base_url, api_key)
    output_root = OUTPUT_ROOT
    output_root.mkdir(parents=True, exist_ok=True)
    traffic_state = _build_minimal_traffic_state()

    attempts: list[dict] = []
    max_attempts = DEFAULT_ATTEMPTS
    for attempt_index in range(1, max_attempts + 1):
        attempt = _run_single_attempt(
            client=client,
            provider_name=provider_name,
            model_name=model_name,
            traffic_state=traffic_state,
            attempt_index=attempt_index,
        )
        attempts.append(attempt)
        if attempt_index == 3 and max_attempts > 3:
            format_categories = {item["response_format_category"] for item in attempts}
            parser_outcomes = {item["parser_success"] for item in attempts}
            if len(format_categories) == 1 and len(parser_outcomes) == 1:
                break
        if attempt_index >= 3 and len({item["response_format_category"] for item in attempts}) == 1 and len({item["parser_success"] for item in attempts}) == 1:
            break

    summary = _summarize(attempts, output_root)
    with (output_root / "live_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with (output_root / "trace.json").open("w", encoding="utf-8") as f:
        json.dump(attempts, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
