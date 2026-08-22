from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.request_config import create_live_client

from src.controllers.decision_pipeline import execute_decision_pipeline
from src.llm.diagnostics import (
    build_provider_diagnostics,
    classify_response_format,
    infer_parser_failure_reason,
)
from src.llm.prompt_builder import build_structured_prompt
from src.llm.provider_gate_diagnostics import build_live_provider_gate_diagnostics
from src.llm.request_config import (
    LIVE_BASE_URL,
    LIVE_MAX_COMPLETION_TOKENS,
    LIVE_MAX_RETRIES,
    LIVE_MODEL,
    LIVE_PROVIDER_NAME,
    LIVE_REASONING_EFFORT,
    LIVE_TIMEOUT_SECONDS,
    build_live_client_kwargs,
    build_live_request_kwargs,
)
from src.llm.response_parser import parse_llm_response_details
from src.safety.route_conflict import validate_conflict_matrix

OUTPUT_ROOT = PROJECT_ROOT / "results" / "diagnostics" / "provider_gate_smoke_v1"
PROMPT_ID = "PROVIDER_GATE_SMOKE"
EXPERIMENT_ID = "PGS_PROVIDER_GATE_SMOKE"
CONTROLLER_NAME = "ProviderGateSmokeDirect"
SEED = 404
VEHICLE_COUNT = 1
VEHICLE_ID = "provider_gate_smoke_vehicle_0"
LLM_MODE = "real"
STAGE_MODE = "raw"


def _git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _redact_error(text: object) -> str:
    if text is None:
        return ""
    redacted = str(text)
    for token in (os.getenv("GROQ_API_KEY", ""), os.getenv("OPENROUTER_API_KEY", "")):
        if token:
            redacted = redacted.replace(token, "[REDACTED]")
    return redacted


def _build_traffic_state() -> list[dict[str, object]]:
    return [
        {
            "vehicle_id": VEHICLE_ID,
            "route_id": "N_S",
            "speed": 5.0,
            "distance_to_intersection": 12.0,
            "time_to_intersection": 2.4,
            "inside_control_zone": True,
        }
    ]


def _build_policy_hints(traffic_state: list[dict[str, object]]) -> dict[str, object]:
    priority_vehicle = traffic_state[0]
    return {
        "priority_vehicle_id": priority_vehicle["vehicle_id"],
        "priority_route_id": priority_vehicle["route_id"],
        "controlled_vehicle_count": len(traffic_state),
        "compatible_routes_with_priority": [priority_vehicle["route_id"]],
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    api_key = os.getenv("GROQ_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise SystemExit("PROVIDER_GATE_SMOKE_BLOCKED_NO_GROQ_KEY")

    if False:
        raise SystemExit("PROVIDER_GATE_SMOKE_BLOCKED_OPENAI_CLIENT_UNAVAILABLE")

    traffic_state = _build_traffic_state()
    prompt = build_structured_prompt(traffic_state, validate_conflict_matrix(), _build_policy_hints(traffic_state))
    client = create_live_client(base_url=LIVE_BASE_URL, api_key=api_key)

    gate_meta = build_live_provider_gate_diagnostics(
        llm_mode=LLM_MODE,
        credential_available=bool(api_key),
        openai_available=True,
        live_client_constructed=True,
        llm_branch_entered=True,
        provider_call_function_entered=True,
        provider_request_kwargs_built=True,
        provider_request_attempted=True,
        provider_request_skipped=False,
        eligible_vehicle_count=len(traffic_state),
        decision_source="LLM_RAW",
    )

    start = time.perf_counter()
    response = None
    response_text = ""
    raw_decisions: dict[str, str] = {VEHICLE_ID: "MISSING"}
    validated_decisions: dict[str, str] = {VEHICLE_ID: "WAIT"}
    parser_success = False
    parser_failure_reason = ""
    fallback_triggered = False
    fallback_reason = ""
    exception: Exception | None = None
    provider_request_success = False
    response_format_category = "EMPTY_RESPONSE"

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
        raw_decisions, validated_decisions, parser_success = parse_llm_response_details(response_text, [VEHICLE_ID])
        response_format_category = classify_response_format(response_text)
        parser_failure_reason = "" if parser_success else infer_parser_failure_reason(response_text, parser_success, raw_decisions.get(VEHICLE_ID, ""))
    except Exception as exc:  # pragma: no cover - smoke failure is reported in output
        exception = exc
        fallback_triggered = True
        fallback_reason = "PROVIDER_REQUEST_EXCEPTION"
        parser_failure_reason = "PROVIDER_REQUEST_EXCEPTION"

    elapsed_ms = (time.perf_counter() - start) * 1000
    diagnostics = build_provider_diagnostics(
        provider_name=LIVE_PROVIDER_NAME,
        model_name=LIVE_MODEL,
        response=response,
        parser_input=response_text,
        parser_success=parser_success,
        parser_action=raw_decisions.get(VEHICLE_ID, "MISSING"),
        parser_failure_reason=parser_failure_reason,
        fallback_triggered=fallback_triggered,
        fallback_reason=fallback_reason,
        exception=exception,
        latency_ms=elapsed_ms,
        provider_request_attempted=True,
        provider_request_success=provider_request_success,
    )
    diagnostics.update(
        {
            **gate_meta,
            "llm_called": True,
            "llm_branch_entered": True,
            "llm_mode": LLM_MODE,
            "llm_model": LIVE_MODEL,
            "json_parse_success": parser_success,
            "fallback_used": fallback_triggered,
            "response_format_category": response_format_category,
            "decision_source": "LLM_RAW" if provider_request_success else "FALLBACK",
        }
    )

    trace = execute_decision_pipeline(
        traffic_state,
        raw_decisions,
        stage_mode=STAGE_MODE,
        llm_meta=diagnostics,
    )
    row = trace[VEHICLE_ID]

    summary = {
        "repository": str(PROJECT_ROOT),
        "branch": _git_output("branch", "--show-current"),
        "head": _git_output("rev-parse", "HEAD"),
        "provider": LIVE_PROVIDER_NAME,
        "base_url": LIVE_BASE_URL,
        "model": LIVE_MODEL,
        "request_count": 1,
        "provider_success_count": 1 if provider_request_success else 0,
        "provider_failure_count": 0 if provider_request_success else 1,
        "http_status": diagnostics.get("http_status", None),
        "parser_success": parser_success,
        "raw_decision": raw_decisions.get(VEHICLE_ID, "MISSING"),
        "validated_decision": validated_decisions.get(VEHICLE_ID, "WAIT"),
        "postprocessed_decision": row.get("postprocessed_decision", ""),
        "final_decision": row.get("final_decision", ""),
        "decision_source": row.get("decision_source", ""),
        "provider_request_attempted": diagnostics.get("provider_request_attempted", False),
        "provider_request_success": diagnostics.get("provider_request_success", False),
        "provider_request_skipped": diagnostics.get("provider_request_skipped", False),
        "provider_skip_reason": diagnostics.get("provider_skip_reason", ""),
        "live_provider_gate_entered": diagnostics.get("live_provider_gate_entered", False),
        "live_provider_enabled": diagnostics.get("live_provider_enabled", False),
        "credential_available": diagnostics.get("credential_available", False),
        "live_client_constructed": diagnostics.get("live_client_constructed", False),
        "provider_call_function_entered": diagnostics.get("provider_call_function_entered", False),
        "provider_request_kwargs_built": diagnostics.get("provider_request_kwargs_built", False),
        "fallback_trigger_reason": diagnostics.get("fallback_trigger_reason", ""),
        "exception_type": diagnostics.get("exception_type", ""),
        "exception_message_redacted": diagnostics.get("exception_message_redacted", ""),
        "redacted_error_summary": _redact_error(diagnostics.get("exception_message_redacted", "")),
        "latency_ms": round(elapsed_ms, 2),
        "response_content_present": diagnostics.get("response_content_present", False),
        "response_content_length": diagnostics.get("response_content_length", 0),
        "response_content_redacted": diagnostics.get("response_content_redacted", ""),
        "parser_input_present": diagnostics.get("parser_input_present", False),
        "parser_input_length": diagnostics.get("parser_input_length", 0),
        "parser_input_redacted": diagnostics.get("parser_input_redacted", ""),
        "evidence_path": str(OUTPUT_ROOT),
        "source_artifacts": {
            "summary": str(OUTPUT_ROOT / "gate_smoke_summary.json"),
            "trace": str(OUTPUT_ROOT / "gate_smoke_trace.json"),
        },
    }

    trace_rows = [
        {
            "prompt_id": PROMPT_ID,
            "request_index": 1,
            "technical_rerun": False,
            "timestamp": 0,
            "provider_success": provider_request_success,
            "http_status": diagnostics.get("http_status", None),
            "exception_type": diagnostics.get("exception_type", ""),
            "redacted_error": diagnostics.get("exception_message_redacted", ""),
            "latency_ms": round(elapsed_ms, 2),
            "parser_success": parser_success,
            "parsed_action": raw_decisions.get(VEHICLE_ID, "MISSING"),
            "fallback": fallback_triggered,
            "fallback_reason": fallback_reason or parser_failure_reason,
            "llm_branch_entered": diagnostics.get("llm_branch_entered", False),
            "live_provider_gate_entered": diagnostics.get("live_provider_gate_entered", False),
            "live_provider_enabled": diagnostics.get("live_provider_enabled", False),
            "credential_available": diagnostics.get("credential_available", False),
            "live_client_constructed": diagnostics.get("live_client_constructed", False),
            "provider_call_function_entered": diagnostics.get("provider_call_function_entered", False),
            "provider_request_kwargs_built": diagnostics.get("provider_request_kwargs_built", False),
            "provider_request_attempted": diagnostics.get("provider_request_attempted", False),
            "provider_request_skipped": diagnostics.get("provider_request_skipped", False),
            "provider_skip_reason": diagnostics.get("provider_skip_reason", ""),
            "fallback_trigger_reason": diagnostics.get("fallback_trigger_reason", ""),
            "raw_decision": raw_decisions.get(VEHICLE_ID, "MISSING"),
            "validated_decision": validated_decisions.get(VEHICLE_ID, "WAIT"),
            "final_decision": row.get("final_decision", ""),
            "response_length": diagnostics.get("response_content_length", 0),
        }
    ]

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    _write_json(OUTPUT_ROOT / "gate_smoke_summary.json", summary)
    _write_json(OUTPUT_ROOT / "gate_smoke_trace.json", trace_rows)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
