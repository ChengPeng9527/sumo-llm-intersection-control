from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openai import OpenAI

from src.controllers.decision_pipeline import run_live_llm_request
from src.llm.diagnostics import (
    build_provider_diagnostics,
    classify_response_format,
    infer_parser_failure_reason,
)
from src.llm.prompt_builder import build_structured_prompt
from src.llm.request_config import (
    LIVE_BASE_URL,
    LIVE_MAX_COMPLETION_TOKENS,
    LIVE_MAX_RETRIES,
    LIVE_MODEL,
    LIVE_PROVIDER_NAME,
    LIVE_REASONING_EFFORT,
    LIVE_TIMEOUT_SECONDS,
    build_live_client_kwargs,
)
from src.llm.response_parser import parse_llm_response_details
from src.safety.route_conflict import get_route_ids, routes_compatible, validate_conflict_matrix

OUTPUT_ROOT = PROJECT_ROOT / "results" / "diagnostics" / "four_vehicle_completion_budget_validation_v1"
VEHICLE_COUNTS = (4,)
SEEDS = (404, 505, 606)
VALID_ACTIONS = {"PROCEED", "WAIT", "FREE"}


def _git_output(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip()


def _build_client(api_key: str) -> OpenAI:
    return OpenAI(**build_live_client_kwargs(base_url=LIVE_BASE_URL, api_key=api_key))


def _build_states(vehicle_count: int, seed: int) -> list[dict[str, object]]:
    rnd = random.Random(seed)
    route_ids = get_route_ids()
    chosen_routes = rnd.sample(route_ids, k=vehicle_count)
    states: list[dict[str, object]] = []
    for index, route_id in enumerate(chosen_routes):
        states.append(
            {
                "vehicle_id": f"budget_v{vehicle_count}_s{seed}_{index}",
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
    compatible_routes = [
        state["route_id"]
        for state in states
        if routes_compatible(str(priority_vehicle["route_id"]), str(state["route_id"]))
    ]
    return {
        "priority_vehicle_id": priority_vehicle["vehicle_id"],
        "priority_route_id": priority_vehicle["route_id"],
        "controlled_vehicle_count": len(states),
        "compatible_routes_with_priority": compatible_routes,
    }


def _extract_response_text(response: object) -> str:
    if response is None:
        return ""
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", "")
        if isinstance(content, str):
            return content
        if content is not None:
            return str(content)
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content
    return str(content) if content is not None else ""


def _extract_json_text(response_text: str) -> str:
    text = (response_text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
        if candidate:
            return candidate
    if "{" in text:
        return text[text.find("{") :]
    if "[" in text:
        return text[text.find("[") :]
    return text


def _classify_failure(response_text: str, parser_success: bool, finish_reason: str) -> str:
    if parser_success:
        return "NONE"
    text = (response_text or "").strip()
    if text and text.startswith("{") and text.endswith("}"):
        if finish_reason == "length":
            return "COMPLETION_BUDGET_TOO_LOW_CONFIRMED"
        return "OUTPUT_TRUNCATION_PROBABLE"
    if finish_reason == "length":
        return "COMPLETION_BUDGET_TOO_LOW_CONFIRMED"
    return "PARSER_FAILURE_OTHER"


def _parse_usage(response: object) -> dict[str, Any]:
    diagnostics = build_provider_diagnostics(
        provider_name=LIVE_PROVIDER_NAME,
        model_name=LIVE_MODEL,
        response=response,
        parser_input="",
        parser_success=False,
        parser_action="",
        parser_failure_reason="",
        fallback_triggered=False,
        fallback_reason="",
        latency_ms=0.0,
        provider_request_attempted=True,
        provider_request_success=response is not None,
    )
    return {
        "finish_reason": diagnostics.get("finish_reason") or "NOT_AVAILABLE",
        "prompt_tokens": diagnostics.get("prompt_tokens"),
        "completion_tokens": diagnostics.get("completion_tokens"),
        "total_tokens": diagnostics.get("total_tokens"),
        "reasoning_tokens": diagnostics.get("reasoning_tokens"),
        "visible_completion_tokens": diagnostics.get("visible_completion_tokens"),
    }


def main() -> int:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise SystemExit("FOUR_VEHICLE_BUDGET_VALIDATION_BLOCKED_NO_GROQ_KEY")
    if OpenAI is None:
        raise SystemExit("FOUR_VEHICLE_BUDGET_VALIDATION_BLOCKED_OPENAI_CLIENT_UNAVAILABLE")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    client = _build_client(api_key)
    request_config = {
        "provider": LIVE_PROVIDER_NAME,
        "base_url": LIVE_BASE_URL,
        "model": LIVE_MODEL,
        "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
        "reasoning_effort": LIVE_REASONING_EFFORT,
        "timeout": LIVE_TIMEOUT_SECONDS,
        "max_retries": LIVE_MAX_RETRIES,
    }
    samples: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for vehicle_count in VEHICLE_COUNTS:
        attempts = 0
        for seed in SEEDS:
            if attempts >= len(SEEDS):
                break
            states = _build_states(vehicle_count, seed)
            expected_ids = [state["vehicle_id"] for state in states]
            prompt = build_structured_prompt(states, validate_conflict_matrix(), _build_policy_hints(states))
            start = time.perf_counter()
            response = None
            response_text = ""
            exception_type = ""
            try:
                response = run_live_llm_request(client, llm_model=LIVE_MODEL, prompt=prompt)
                response_text = _extract_response_text(response)
            except Exception as exc:
                exception_type = type(exc).__name__
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            diagnostics = build_provider_diagnostics(
                provider_name=LIVE_PROVIDER_NAME,
                model_name=LIVE_MODEL,
                response=response,
                parser_input=response_text,
                parser_success=False,
                parser_action="",
                parser_failure_reason="",
                fallback_triggered=False,
                fallback_reason="",
                exception=None if exception_type == "" else RuntimeError(exception_type),
                latency_ms=elapsed_ms,
                provider_request_attempted=True,
                provider_request_success=response is not None,
            )
            parsed_ids: list[str] = []
            missing_ids = list(expected_ids)
            unknown_ids: list[str] = []
            duplicate_ids: list[str] = []
            invalid_action_count = 0
            canonical_schema_compliance = False
            parser_success = False
            fallback_reason = "PARSER_FAILURE"
            raw_decisions: dict[str, str] = {}
            validated_decisions: dict[str, str] = {}
            try:
                payload = json.loads(_extract_json_text(response_text))
            except Exception:
                payload = None
            if isinstance(payload, dict) and isinstance(payload.get("decisions"), dict):
                decisions = payload["decisions"]
                parsed_ids = list(decisions.keys())
                missing_ids = [vid for vid in expected_ids if vid not in decisions]
                unknown_ids = [vid for vid in decisions if vid not in expected_ids]
                invalid_action_count = sum(1 for action in decisions.values() if str(action).strip().upper() not in VALID_ACTIONS)
                canonical_schema_compliance = not missing_ids and not unknown_ids and invalid_action_count == 0 and len(parsed_ids) == len(expected_ids)
                parser_success = canonical_schema_compliance
                if parser_success:
                    raw_decisions, validated_decisions, _ = parse_llm_response_details(response_text, expected_ids)
                    fallback_reason = ""
            elif isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict) and isinstance(item.get("vehicle_id"), str):
                        parsed_ids.append(item["vehicle_id"])
                missing_ids = [vid for vid in expected_ids if vid not in parsed_ids]
                unknown_ids = [vid for vid in parsed_ids if vid not in expected_ids]
                duplicate_ids = [vid for vid, count in Counter(parsed_ids).items() if count > 1]
                invalid_action_count = sum(
                    1
                    for item in payload
                    if isinstance(item, dict) and str(item.get("action", item.get("decision", ""))).strip().upper() not in VALID_ACTIONS
                )
                canonical_schema_compliance = not missing_ids and not unknown_ids and not duplicate_ids and invalid_action_count == 0
                parser_success = False
            elif isinstance(payload, dict):
                parsed_ids = [key for key in payload.keys() if key not in {"action", "decision", "vehicle_id", "decisions"}]
                missing_ids = [vid for vid in expected_ids if vid not in parsed_ids]
                unknown_ids = [vid for vid in parsed_ids if vid not in expected_ids]
                invalid_action_count = sum(1 for vid in parsed_ids if str(payload.get(vid)).strip().upper() not in VALID_ACTIONS)
                canonical_schema_compliance = not missing_ids and not unknown_ids and invalid_action_count == 0 and len(parsed_ids) == len(expected_ids)
                parser_success = False
            finish_reason = diagnostics.get("finish_reason") or "NOT_AVAILABLE"
            sample = {
                "vehicle_count": vehicle_count,
                "seed": seed,
                "attempt_index": attempts + 1,
                "expected_vehicle_ids": expected_ids,
                "provider_request_attempted": True,
                "provider_request_success": response is not None,
                "response_received": bool(response_text),
                "http_status": diagnostics.get("http_status", None),
                "finish_reason": finish_reason,
                "prompt_tokens": diagnostics.get("prompt_tokens"),
                "completion_tokens": diagnostics.get("completion_tokens"),
                "total_tokens": diagnostics.get("total_tokens"),
                "reasoning_tokens": diagnostics.get("reasoning_tokens"),
                "visible_completion_tokens": diagnostics.get("visible_completion_tokens"),
                "response_content_length": len(response_text),
                "response_content_redacted": response_text[:900],
                "response_shape": classify_response_format(response_text),
                "parser_success": parser_success,
                "parser_failure_reason": "" if parser_success else infer_parser_failure_reason(response_text, parser_success, raw_decisions.get(expected_ids[0], "")),
                "parsed_vehicle_ids": parsed_ids,
                "missing_vehicle_ids": missing_ids,
                "unknown_vehicle_ids": unknown_ids,
                "duplicate_vehicle_ids": duplicate_ids,
                "invalid_action_count": invalid_action_count,
                "canonical_schema_compliance": canonical_schema_compliance,
                "failure_classification": _classify_failure(response_text, parser_success, finish_reason),
                "latency_ms": elapsed_ms,
                "exception_type": exception_type,
                "raw_decisions": raw_decisions,
                "validated_decisions": validated_decisions,
            }
            samples.append(sample)
            attempts += 1

        provider_success_rows = [row for row in samples if row["provider_request_success"]]
        parser_success_rows = [row for row in provider_success_rows if row["parser_success"]]
        truncated_rows = [row for row in provider_success_rows if row["failure_classification"] == "COMPLETION_BUDGET_TOO_LOW_CONFIRMED" or row["failure_classification"] == "OUTPUT_TRUNCATION_PROBABLE"]
        summary_rows.append(
            {
                "vehicle_count": vehicle_count,
                "attempt_count": attempts,
                "provider_success_count": len(provider_success_rows),
                "parser_success_count": len(parser_success_rows),
                "parser_success_given_provider_success": (len(parser_success_rows) / len(provider_success_rows)) if provider_success_rows else 0.0,
                "truncated_response_count": len(truncated_rows),
                "finish_reason_distribution": dict(Counter(row["finish_reason"] for row in provider_success_rows)),
                "completion_tokens_distribution": dict(Counter(str(row["completion_tokens"]) for row in provider_success_rows)),
                "reasoning_tokens_values": sorted({row["reasoning_tokens"] for row in provider_success_rows}),
                "canonical_schema_compliance_count": sum(1 for row in provider_success_rows if row["canonical_schema_compliance"]),
                "mean_completion_tokens": (
                    sum((row["completion_tokens"] or 0) for row in provider_success_rows) / len(provider_success_rows)
                    if provider_success_rows else 0.0
                ),
            }
        )

    payload = {
        "repository": _git_output("rev-parse", "--show-toplevel"),
        "branch": _git_output("branch", "--show-current"),
        "head": _git_output("rev-parse", "HEAD"),
        "request_config": request_config,
        "summary_rows": summary_rows,
        "samples": samples,
    }
    (OUTPUT_ROOT / "four_vehicle_completion_budget_validation_summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT_ROOT / "four_vehicle_completion_budget_validation_trace.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in samples) + "\n", encoding="utf-8")
    print(json.dumps(summary_rows, indent=2, ensure_ascii=False))
    print(f"SUMMARY_PATH={OUTPUT_ROOT / 'four_vehicle_completion_budget_validation_summary.json'}")
    print(f"TRACE_PATH={OUTPUT_ROOT / 'four_vehicle_completion_budget_validation_trace.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
