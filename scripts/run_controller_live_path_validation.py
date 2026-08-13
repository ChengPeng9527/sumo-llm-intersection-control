from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openai import OpenAI

from src.controllers.decision_pipeline import execute_decision_pipeline
from src.llm.diagnostics import build_provider_diagnostics, classify_response_format, infer_parser_failure_reason
from src.llm.postprocessor import apply_cooperative_postprocessing
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
from src.safety.route_conflict import routes_compatible, validate_conflict_matrix
from src.safety.safety_verifier import verify_decisions as verify_state_based_safety


OUTPUT_ROOT = PROJECT_ROOT / "results" / "diagnostics" / "controller_live_path_validation_v1"
PROMPT_ID = "P1_BASELINE"
SEED = 404
VEHICLE_ID = "controller_live_path_vehicle_0"

CONTROLLERS = (
    ("raw_llm", "raw", "raw_llm_summary.json"),
    ("hybrid", "hybrid", "hybrid_summary.json"),
    ("hybrid_safety", "hybrid_safety", "hybrid_safety_summary.json"),
)


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


def _make_client(api_key: str) -> OpenAI:
    return OpenAI(**build_live_client_kwargs(base_url=LIVE_BASE_URL, api_key=api_key))


def _stage_functions(stage_mode: str):
    postprocessor_fn = None
    safety_guard_fn = None
    if stage_mode in {"hybrid", "hybrid_safety"}:
        postprocessor_fn = lambda trace, states: apply_cooperative_postprocessing(  # noqa: E731
            trace,
            states,
            routes_compatible_fn=routes_compatible,
        )
    if stage_mode == "hybrid_safety":
        safety_guard_fn = lambda trace, states: _apply_state_based_safety(trace, states)  # noqa: E731
    return postprocessor_fn, safety_guard_fn


def _apply_state_based_safety(trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
    vehicles = [state["vehicle_id"] for state in vehicle_states]

    def guard_fn(states: list[dict], raw_decisions: dict[str, str]):
        return verify_state_based_safety(states, raw_decisions)

    from src.controllers.decision_pipeline import _build_runtime_trace_from_guard  # local import for reuse

    return _build_runtime_trace_from_guard(trace, vehicle_states, guard_fn)


def _probe_controller(stage_name: str, stage_mode: str) -> dict[str, object]:
    api_key = os.getenv("GROQ_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise SystemExit("CONTROLLER_LIVE_PATH_VALIDATION_BLOCKED_NO_GROQ_KEY")
    if OpenAI is None:
        raise SystemExit("CONTROLLER_LIVE_PATH_VALIDATION_BLOCKED_OPENAI_CLIENT_UNAVAILABLE")

    traffic_state = _build_traffic_state()
    prompt = build_structured_prompt(traffic_state, validate_conflict_matrix(), _build_policy_hints(traffic_state))
    client = _make_client(api_key)

    gate_meta = build_live_provider_gate_diagnostics(
        llm_mode="real",
        credential_available=True,
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

    response = None
    response_text = ""
    raw_decisions: dict[str, str] = {VEHICLE_ID: "MISSING"}
    validated_decisions: dict[str, str] = {VEHICLE_ID: "WAIT"}
    parser_success = False
    fallback_triggered = False
    fallback_reason = ""
    exception: Exception | None = None
    response_format_category = "EMPTY_RESPONSE"
    provider_request_success = False

    start = time.perf_counter()
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
    except Exception as exc:  # pragma: no cover - manual live probe failure is reported in JSON
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
        parser_action=raw_decisions.get(VEHICLE_ID, "MISSING"),
        parser_failure_reason="" if parser_success else infer_parser_failure_reason(response_text, parser_success, raw_decisions.get(VEHICLE_ID, "")),
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
            "llm_mode": "real",
            "llm_model": LIVE_MODEL,
            "json_parse_success": parser_success,
            "fallback_used": fallback_triggered,
            "response_format_category": response_format_category,
            "decision_source": "LLM_RAW" if provider_request_success else "FALLBACK",
        }
    )

    postprocessor_fn, safety_guard_fn = _stage_functions(stage_mode)
    trace = execute_decision_pipeline(
        traffic_state,
        raw_decisions,
        stage_mode=stage_mode,
        llm_meta=diagnostics,
        postprocessor_fn=postprocessor_fn,
        safety_guard_fn=safety_guard_fn,
    )
    row = trace[VEHICLE_ID]

    response_received = bool(response_text)
    summary = {
        "repository": str(PROJECT_ROOT),
        "branch": _git_output("branch", "--show-current"),
        "head": _git_output("rev-parse", "HEAD"),
        "controller": stage_name,
        "stage_mode": stage_mode,
        "provider": LIVE_PROVIDER_NAME,
        "base_url": LIVE_BASE_URL,
        "model": LIVE_MODEL,
        "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
        "reasoning_effort": LIVE_REASONING_EFFORT,
        "timeout": LIVE_TIMEOUT_SECONDS,
        "max_retries": LIVE_MAX_RETRIES,
        "request_count": 1,
        "provider_request_attempted": diagnostics.get("provider_request_attempted", False),
        "provider_request_success": diagnostics.get("provider_request_success", False),
        "provider_request_skipped": diagnostics.get("provider_request_skipped", False),
        "provider_skip_reason": diagnostics.get("provider_skip_reason", ""),
        "response_received": response_received,
        "parser_success": parser_success,
        "raw_decision": raw_decisions.get(VEHICLE_ID, "MISSING"),
        "validated_decision": validated_decisions.get(VEHICLE_ID, "WAIT"),
        "postprocessed_decision": row.get("postprocessed_decision", ""),
        "final_decision": row.get("final_decision", ""),
        "decision_source": row.get("decision_source", ""),
        "fallback_used": diagnostics.get("fallback_used", False),
        "fallback_reason": row.get("fallback_reason", ""),
        "safety_override": row.get("safety_override", False),
        "llm_branch_entered": diagnostics.get("llm_branch_entered", False),
        "live_provider_gate_entered": diagnostics.get("live_provider_gate_entered", False),
        "live_provider_enabled": diagnostics.get("live_provider_enabled", False),
        "credential_available": diagnostics.get("credential_available", False),
        "live_client_constructed": diagnostics.get("live_client_constructed", False),
        "provider_call_function_entered": diagnostics.get("provider_call_function_entered", False),
        "provider_request_kwargs_built": diagnostics.get("provider_request_kwargs_built", False),
        "latency_ms": round(elapsed_ms, 2),
        "http_status": diagnostics.get("http_status", None),
        "exception_type": diagnostics.get("exception_type", ""),
        "redacted_exception_message": diagnostics.get("exception_message_redacted", ""),
        "response_content_present": diagnostics.get("response_content_present", False),
        "response_content_length": diagnostics.get("response_content_length", 0),
        "response_content_redacted": diagnostics.get("response_content_redacted", ""),
        "parser_input_present": diagnostics.get("parser_input_present", False),
        "parser_input_length": diagnostics.get("parser_input_length", 0),
        "parser_input_redacted": diagnostics.get("parser_input_redacted", ""),
        "postprocessor_stage_reached": stage_mode in {"hybrid", "hybrid_safety"},
        "safety_stage_reached": stage_mode == "hybrid_safety",
        "controller_live_path_valid": bool(
            diagnostics.get("provider_request_success")
            and parser_success
            and response_received
            and row.get("final_decision", "")
        ),
        "evidence_path": str(OUTPUT_ROOT),
        "source_artifacts": {
            "summary": str(OUTPUT_ROOT / f"{stage_name}_summary.json"),
        },
        "raw_trace": row,
        "raw_response": _redact_error(response_text),
        "redacted_exception_message": _redact_error(diagnostics.get("exception_message_redacted", "")),
    }
    return summary


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    summaries: dict[str, dict[str, object]] = {}
    for stage_name, stage_mode, filename in CONTROLLERS:
        summary = _probe_controller(stage_name, stage_mode)
        summaries[stage_name] = summary
        _write_json(OUTPUT_ROOT / filename, summary)

    combined = {
        "repository": str(PROJECT_ROOT),
        "branch": _git_output("branch", "--show-current"),
        "head": _git_output("rev-parse", "HEAD"),
        "provider": LIVE_PROVIDER_NAME,
        "base_url": LIVE_BASE_URL,
        "model": LIVE_MODEL,
        "controllers": {
            name: {
                "provider_request_attempted": data["provider_request_attempted"],
                "provider_request_success": data["provider_request_success"],
                "parser_success": data["parser_success"],
                "response_received": data["response_received"],
                "raw_decision": data["raw_decision"],
                "validated_decision": data["validated_decision"],
                "postprocessed_decision": data["postprocessed_decision"],
                "final_decision": data["final_decision"],
                "decision_source": data["decision_source"],
                "fallback_used": data["fallback_used"],
                "fallback_reason": data["fallback_reason"],
                "safety_override": data["safety_override"],
                "latency_ms": data["latency_ms"],
                "exception_type": data["exception_type"],
                "redacted_exception_message": data["redacted_exception_message"],
                "llm_branch_entered": data["llm_branch_entered"],
                "live_provider_gate_entered": data["live_provider_gate_entered"],
                "live_provider_enabled": data["live_provider_enabled"],
                "credential_available": data["credential_available"],
                "live_client_constructed": data["live_client_constructed"],
                "provider_call_function_entered": data["provider_call_function_entered"],
                "provider_request_kwargs_built": data["provider_request_kwargs_built"],
            }
            for name, data in summaries.items()
        },
        "all_three_live_paths_valid": all(data["controller_live_path_valid"] for data in summaries.values()),
        "prompt_changed": False,
        "method_changed": False,
        "frozen_request_config": {
            "provider": LIVE_PROVIDER_NAME,
            "base_url": LIVE_BASE_URL,
            "model": LIVE_MODEL,
            "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
            "reasoning_effort": LIVE_REASONING_EFFORT,
            "timeout": LIVE_TIMEOUT_SECONDS,
            "max_retries": LIVE_MAX_RETRIES,
            "prompt": PROMPT_ID,
        },
        "files_modified": ["scripts/run_controller_live_path_validation.py"],
        "evidence_path": str(OUTPUT_ROOT),
        "final_verdict": (
            "ALL_LLM_CONTROLLER_LIVE_PATHS_VALIDATED"
            if all(data["controller_live_path_valid"] for data in summaries.values())
            else "PARTIAL_LLM_CONTROLLER_LIVE_PATH_VALIDATION"
        ),
        "next_action": "Use the controller_live_path_validation evidence to decide whether to return to canonical prompt revalidation or proceed to the next dissertation checkpoint.",
    }
    _write_json(OUTPUT_ROOT / "controller_live_path_summary.json", combined)
    print(json.dumps(combined, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
