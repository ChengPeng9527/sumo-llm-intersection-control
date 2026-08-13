from __future__ import annotations

import contextlib
import csv
import hashlib
import json
import os
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from common import CONFIG
from src.common.metrics import write_json, write_jsonl
from src.controllers.decision_pipeline import run_live_llm_request
from src.experiments.scenario_generator import generate_scenario
from src.llm.diagnostics import build_provider_diagnostics, classify_response_format, infer_parser_failure_reason
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
from src.safety.route_conflict import validate_conflict_matrix

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


PROJECT_ROOT = Path(CONFIG["project_root"])
PROMPT_SOURCE_ROOT = (
    PROJECT_ROOT / "results" / "prompt_development" / "canonical_prompt_selection_v1" / "prompt_candidates"
)
OUTPUT_ROOT = PROJECT_ROOT / "results" / "prompt_development" / "canonical_prompt_revalidation_v1"

PROMPT_IDS = ("P1_BASELINE", "P2_STRUCTURED", "P3_COOPERATIVE_OBJECTIVE")
EXPECTED_PROMPT_HASHES = {
    "P1_BASELINE": "EA435588BE1CAFC099D02685060CF00223852D8834CDFCF4DAFE66233C474ECD",
    "P2_STRUCTURED": "09852507B087CAA59F88E4E67720F179F62A0F19356AE2898C880ADC3FF78EB2",
    "P3_COOPERATIVE_OBJECTIVE": "B7C0873AAAEF80BC15F13F8F034BBB7A106FC89416969FDAFC4C66661B978989",
}
EXPECTED_REQUEST_CONFIG = {
    "provider": LIVE_PROVIDER_NAME,
    "base_url": LIVE_BASE_URL,
    "model": LIVE_MODEL,
    "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
    "reasoning_effort": LIVE_REASONING_EFFORT,
    "timeout": LIVE_TIMEOUT_SECONDS,
    "max_retries": LIVE_MAX_RETRIES,
}
DEFAULT_NEW_SEEDS = (404, 505, 606, 707, 808, 909)
DEFAULT_COOLDOWN_SECONDS = 25
ALLOWED_DECISIONS = {"PROCEED", "WAIT", "FREE"}
MAX_TECHNICAL_RERUNS = 1


@dataclass(frozen=True)
class RequestConfigAudit:
    matches: bool
    current: dict[str, object]
    expected: dict[str, object]


@dataclass(frozen=True)
class PromptHashAudit:
    matches: bool
    current: dict[str, str]
    expected: dict[str, str]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_prompt_texts(prompt_source_root: Path = PROMPT_SOURCE_ROOT) -> dict[str, str]:
    return {prompt_id: (prompt_source_root / f"{prompt_id}.txt").read_text(encoding="utf-8") for prompt_id in PROMPT_IDS}


def verify_prompt_hashes(prompt_source_root: Path = PROMPT_SOURCE_ROOT) -> PromptHashAudit:
    current = {prompt_id: _sha256(prompt_source_root / f"{prompt_id}.txt") for prompt_id in PROMPT_IDS}
    return PromptHashAudit(matches=current == EXPECTED_PROMPT_HASHES, current=current, expected=dict(EXPECTED_PROMPT_HASHES))


def verify_frozen_request_config() -> RequestConfigAudit:
    current = {
        "provider": LIVE_PROVIDER_NAME,
        "base_url": LIVE_BASE_URL,
        "model": LIVE_MODEL,
        "max_completion_tokens": LIVE_MAX_COMPLETION_TOKENS,
        "reasoning_effort": LIVE_REASONING_EFFORT,
        "timeout": LIVE_TIMEOUT_SECONDS,
        "max_retries": LIVE_MAX_RETRIES,
    }
    return RequestConfigAudit(matches=current == EXPECTED_REQUEST_CONFIG, current=current, expected=dict(EXPECTED_REQUEST_CONFIG))


def select_development_seed(
    seed_candidates: Sequence[int] = DEFAULT_NEW_SEEDS,
    *,
    rng: random.Random | None = None,
) -> int:
    choices = [seed for seed in seed_candidates if seed not in {101, 202, 303}]
    if not choices:
        raise ValueError("No eligible development seeds available")
    rng = rng or random.SystemRandom()
    return rng.choice(list(choices))


def choose_prompt_order(prompt_ids: Sequence[str] = PROMPT_IDS, *, rng: random.Random | None = None) -> list[str]:
    order = list(prompt_ids)
    rng = rng or random.SystemRandom()
    rng.shuffle(order)
    return order


def build_run_manifest(
    *,
    selected_seed: int,
    prompt_order: Sequence[str],
    prompt_hash_audit: PromptHashAudit,
    request_config_audit: RequestConfigAudit,
    vehicle_count: int,
    density: str,
    scenario_id: str,
) -> dict[str, object]:
    return {
        "repository": str(PROJECT_ROOT),
        "branch": "phase-18-decision-pipeline-separation",
        "selected_seed": selected_seed,
        "prompt_order": list(prompt_order),
        "prompt_hashes": dict(prompt_hash_audit.current),
        "prompt_hashes_expected": dict(prompt_hash_audit.expected),
        "prompt_hashes_match": prompt_hash_audit.matches,
        "request_config": dict(request_config_audit.current),
        "request_config_expected": dict(request_config_audit.expected),
        "request_config_match": request_config_audit.matches,
        "vehicle_count": vehicle_count,
        "density": density,
        "scenario_id": scenario_id,
        "technical_rerun_limit_per_prompt": MAX_TECHNICAL_RERUNS,
        "cooldown_seconds_between_runs": DEFAULT_COOLDOWN_SECONDS,
        "output_root": str(OUTPUT_ROOT),
        "prompt_source_root": str(PROMPT_SOURCE_ROOT),
        "created_at_epoch_seconds": time.time(),
    }


def build_provider_probe_traffic_state() -> list[dict]:
    return [
        {
            "vehicle_id": "probe_car0",
            "route_id": "N_S",
            "speed": 5.0,
            "distance_to_intersection": 12.0,
            "time_to_intersection": 2.4,
            "inside_control_zone": True,
        }
    ]


def build_provider_probe_policy_hints(traffic_state: list[dict]) -> dict:
    priority_vehicle = traffic_state[0]
    return {
        "priority_vehicle_id": priority_vehicle["vehicle_id"],
        "priority_route_id": priority_vehicle["route_id"],
        "controlled_vehicle_count": len(traffic_state),
        "compatible_routes_with_priority": [priority_vehicle["route_id"]],
    }


def build_provider_probe_prompt() -> str:
    traffic_state = build_provider_probe_traffic_state()
    return build_structured_prompt(traffic_state, validate_conflict_matrix(), build_provider_probe_policy_hints(traffic_state))


def _build_provider_client(api_key: str):
    if OpenAI is None:
        raise RuntimeError("openai package is required for the canonical prompt revalidation runner")
    return OpenAI(**build_live_client_kwargs(base_url=LIVE_BASE_URL, api_key=api_key))


def run_provider_probe(api_key: str) -> dict[str, object]:
    traffic_state = build_provider_probe_traffic_state()
    prompt = build_provider_probe_prompt()
    client = _build_provider_client(api_key)
    start = time.perf_counter()
    response = None
    response_text = ""
    parser_success = False
    raw_decisions: dict[str, str] = {traffic_state[0]["vehicle_id"]: "MISSING"}
    validated_decisions: dict[str, str] = {traffic_state[0]["vehicle_id"]: "WAIT"}
    exception = None
    fallback_triggered = False
    fallback_reason = ""
    response_format_category = "EMPTY_RESPONSE"
    provider_request_success = False

    try:
        response = run_live_llm_request(client, llm_model=LIVE_MODEL, prompt=prompt)
        provider_request_success = True
        if response is not None and getattr(response, "choices", None):
            choice = response.choices[0]
            message = getattr(choice, "message", None)
            response_text = getattr(message, "content", "") or ""
        raw_decisions, validated_decisions, parser_success = parse_llm_response_details(response_text, [traffic_state[0]["vehicle_id"]])
        response_format_category = classify_response_format(response_text)
    except Exception as exc:  # pragma: no cover - handled locally when run manually
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
        parser_action=raw_decisions.get(traffic_state[0]["vehicle_id"], "MISSING"),
        parser_failure_reason="" if parser_success else "PROVIDER_REQUEST_EXCEPTION",
        fallback_triggered=fallback_triggered,
        fallback_reason=fallback_reason,
        exception=exception,
        latency_ms=elapsed_ms,
        provider_request_attempted=True,
        provider_request_success=provider_request_success,
    )
    diagnostics.update(
        {
            "request_attempted": True,
            "response_format_category": response_format_category,
            "validated_decision": validated_decisions.get(traffic_state[0]["vehicle_id"], "WAIT"),
            "final_decision": validated_decisions.get(traffic_state[0]["vehicle_id"], "WAIT"),
            "failure_classification": classify_probe_failure(exception, provider_request_success),
        }
    )
    return diagnostics


def classify_probe_failure(exception: Exception | None, provider_request_success: bool) -> str:
    if provider_request_success:
        return "NONE"
    if exception is None:
        return "UNKNOWN_NETWORK_FAILURE"
    name = type(exception).__name__
    message = str(exception).lower()
    if "proxy" in name.lower() or "proxy" in message:
        return "PROXY_CONFIGURATION_FAILURE"
    if "ssl" in name.lower() or "tls" in message:
        return "DNS_OR_TLS_FAILURE"
    if "timeout" in name.lower() or "timed out" in message:
        return "UNKNOWN_NETWORK_FAILURE"
    if "resolve" in message or "dns" in message:
        return "DNS_OR_TLS_FAILURE"
    if "401" in message or "unauthorized" in message:
        return "LIVE_PROVIDER_AUTH_FAILED"
    if "403" in message or "forbidden" in message:
        return "LIVE_PROVIDER_AUTH_FAILED"
    if "429" in message or "rate limit" in message:
        return "LIVE_PROVIDER_RATE_LIMITED"
    if "5" in message and "error" in message:
        return "LIVE_PROVIDER_HTTP_ERROR"
    return "UNKNOWN_NETWORK_FAILURE"


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def group_rows_by_request(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if _to_bool(row.get("llm_called")):
            grouped[_to_int(row.get("simulation_step"))].append(row)
    return [grouped[step] for step in sorted(grouped)]


def build_request_trace_rows(
    *,
    prompt_id: str,
    request_groups: Sequence[Sequence[dict[str, str]]],
    technical_rerun: bool = False,
) -> list[dict[str, object]]:
    trace_rows: list[dict[str, object]] = []
    for request_index, group in enumerate(request_groups, start=1):
        if not group:
            continue
        row = dict(group[0])
        trace_rows.append(
            {
                "prompt_id": prompt_id,
                "request_index": request_index,
                "technical_rerun": technical_rerun,
                "timestamp": row.get("simulation_time_seconds", ""),
                "provider_success": _to_bool(row.get("provider_request_success")),
                "http_status": row.get("http_status", ""),
                "exception_type": row.get("exception_type", ""),
                "redacted_error": row.get("exception_message_redacted", ""),
                "latency_ms": _to_float(row.get("llm_response_time_ms")),
                "parser_success": _to_bool(row.get("parser_success")),
                "parsed_action": row.get("parser_action", ""),
                "fallback": _to_bool(row.get("fallback_used")) or _to_bool(row.get("fallback_triggered")),
                "fallback_reason": row.get("fallback_reason", "") or row.get("parser_failure_reason", ""),
                "llm_branch_entered": _to_bool(row.get("llm_branch_entered")),
                "live_provider_gate_entered": _to_bool(row.get("live_provider_gate_entered")),
                "live_provider_enabled": _to_bool(row.get("live_provider_enabled")),
                "credential_available": _to_bool(row.get("credential_available")),
                "live_client_constructed": _to_bool(row.get("live_client_constructed")),
                "provider_call_function_entered": _to_bool(row.get("provider_call_function_entered")),
                "provider_request_kwargs_built": _to_bool(row.get("provider_request_kwargs_built")),
                "provider_request_attempted": _to_bool(row.get("provider_request_attempted")),
                "provider_request_skipped": _to_bool(row.get("provider_request_skipped")),
                "provider_skip_reason": row.get("provider_skip_reason", ""),
                "fallback_trigger_reason": row.get("fallback_trigger_reason", ""),
                "raw_decision": row.get("llm_raw_decision", ""),
                "validated_decision": row.get("validated_llm_decision", ""),
                "final_decision": row.get("final_decision", ""),
                "response_length": _to_int(row.get("response_content_length")),
            }
        )
    return trace_rows


def summarize_request_groups(request_groups: Sequence[Sequence[dict[str, str]]]) -> dict[str, object]:
    grouped_rows = [list(group) for group in request_groups if group]
    request_count = len(grouped_rows)
    success_rows = [group[0] for group in grouped_rows if _to_bool(group[0].get("provider_request_success"))]
    failure_rows = [group[0] for group in grouped_rows if not _to_bool(group[0].get("provider_request_success"))]
    parser_success_rows = [row for row in success_rows if _to_bool(row.get("parser_success"))]
    fallback_rows = [row for row in success_rows if _to_bool(row.get("fallback_used")) or _to_bool(row.get("fallback_triggered"))]
    invalid_rows = [
        row
        for row in success_rows
        if not _to_bool(row.get("parser_success")) or row.get("parser_action", "") not in ALLOWED_DECISIONS
    ]
    genuine_rows = [row for row in success_rows if row.get("validated_llm_decision", "") in ALLOWED_DECISIONS]
    decision_counter = Counter(row.get("validated_llm_decision", "") for row in genuine_rows if row.get("validated_llm_decision", ""))
    latency_values = [_to_float(row.get("llm_response_time_ms")) for row in success_rows]
    response_lengths = [_to_int(row.get("response_content_length")) for row in success_rows if row.get("response_content_length") is not None]

    provider_success_count = len(success_rows)
    parser_success_count = len(parser_success_rows)
    fallback_count = len(fallback_rows)
    return {
        "total_live_requests": request_count,
        "provider_success_count": provider_success_count,
        "provider_failure_count": len(failure_rows),
        "parser_success_given_provider_success": (parser_success_count / provider_success_count) if provider_success_count else 0.0,
        "semantic_fallback_given_provider_success": (fallback_count / provider_success_count) if provider_success_count else 0.0,
        "ambiguous_invalid_response_count": len(invalid_rows),
        "genuine_proceed_count": decision_counter.get("PROCEED", 0),
        "genuine_wait_count": decision_counter.get("WAIT", 0),
        "genuine_free_count": decision_counter.get("FREE", 0),
        "genuine_proceed_rate": (decision_counter.get("PROCEED", 0) / provider_success_count) if provider_success_count else 0.0,
        "genuine_wait_rate": (decision_counter.get("WAIT", 0) / provider_success_count) if provider_success_count else 0.0,
        "genuine_free_rate": (decision_counter.get("FREE", 0) / provider_success_count) if provider_success_count else 0.0,
        "mean_successful_request_latency_ms": (sum(latency_values) / len(latency_values)) if latency_values else 0.0,
        "mean_response_length": (sum(response_lengths) / len(response_lengths)) if response_lengths else 0.0,
    }


def should_allow_technical_rerun(provider_success_count: int, technical_rerun_count: int) -> bool:
    return provider_success_count == 0 and technical_rerun_count < MAX_TECHNICAL_RERUNS


@contextlib.contextmanager
def patched_prompt_builder(prompt_text: str):
    import src.llm.prompt_builder as prompt_builder_module

    original = prompt_builder_module.build_structured_prompt

    def _patched(*args, **kwargs):
        return prompt_text

    prompt_builder_module.build_structured_prompt = _patched
    try:
        yield
    finally:
        prompt_builder_module.build_structured_prompt = original


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _resolve_prompt_path(prompt_id: str) -> Path:
    return PROMPT_SOURCE_ROOT / f"{prompt_id}.txt"


def _load_prompt_text(prompt_id: str) -> str:
    return _resolve_prompt_path(prompt_id).read_text(encoding="utf-8")


def run_single_prompt_run(
    *,
    prompt_id: str,
    prompt_text: str,
    seed: int,
    vehicle_count: int,
    density: str,
    llm_mode: str,
    llm_api_key: str,
    decision_interval: int,
    technical_rerun: bool = False,
) -> dict[str, object]:
    scenario_id = f"canonical_prompt_revalidation_{prompt_id.lower()}_seed{seed}_v{vehicle_count}"
    scenario_config = generate_scenario(scenario_id, density, seed, vehicle_count=vehicle_count)
    from src.controllers.decision_pipeline import run_pipeline_controller

    experiment_id = f"CPR_{prompt_id}"
    run_id = f"{experiment_id}_v{vehicle_count}_seed{seed}_{llm_mode}"
    live_client = _build_provider_client(llm_api_key) if llm_mode == "real" else None
    with patched_prompt_builder(prompt_text):
        run_pipeline_controller(
            experiment_id=experiment_id,
            controller_name="CanonicalPromptRevalidation",
            stage_mode="raw",
            scenario=scenario_id,
            vehicle_count=vehicle_count,
            seed=seed,
            sumo_binary=Path(CONFIG["sumo_gui_binary_path"]),
            sumo_config=Path(scenario_config["sumocfg_path"]),
            simulation_steps=int(scenario_config["simulation_duration_seconds"]),
            llm_mode=llm_mode,
            llm_decision_interval=decision_interval,
            llm_model=LIVE_MODEL,
            llm_base_url=LIVE_BASE_URL,
            llm_api_key=llm_api_key,
            llm_client=live_client,
            prompt_version="v2-stage-separated",
        )

    from src.common.metrics import run_artifact_paths

    artifacts = run_artifact_paths(run_id)
    rows = _read_csv_rows(artifacts["step_records"])
    request_groups = group_rows_by_request(rows)
    summary = summarize_request_groups(request_groups)
    return {
        "prompt_id": prompt_id,
        "prompt_text_path": str(_resolve_prompt_path(prompt_id)),
        "run_id": run_id,
        "scenario_id": scenario_id,
        "seed": seed,
        "vehicle_count": vehicle_count,
        "density": density,
        "technical_rerun": technical_rerun,
        "request_groups": request_groups,
        "summary": summary,
        "step_records_path": str(artifacts["step_records"]),
        "run_metadata_path": str(artifacts["run_metadata"]),
        "events_path": str(artifacts["events"]),
    }


def build_prompt_comparison_rows(prompt_results: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for result in prompt_results:
        grouped[str(result["prompt_id"])].append(dict(result))

    rows: list[dict[str, object]] = []
    for prompt_id in PROMPT_IDS:
        runs = grouped.get(prompt_id, [])
        all_request_groups: list[list[dict[str, str]]] = []
        technical_rerun_count = 0
        for run in runs:
            all_request_groups.extend(run["request_groups"])
            if run["technical_rerun"]:
                technical_rerun_count += 1
        summary = summarize_request_groups(all_request_groups)
        rows.append(
            {
                "prompt_id": prompt_id,
                "seed": runs[0]["seed"] if runs else "",
                "vehicle_count": runs[0]["vehicle_count"] if runs else "",
                "run_count": len(runs),
                "technical_rerun_count": technical_rerun_count,
                **summary,
            }
        )
    return rows


def build_revalidation_summary(prompt_comparison_rows: Sequence[dict[str, object]], prompt_order: Sequence[str], selected_seed: int) -> dict[str, object]:
    prompt_rows = {row["prompt_id"]: row for row in prompt_comparison_rows}
    selected_prompt = "P1_BASELINE"
    if prompt_rows:
        p1 = prompt_rows.get("P1_BASELINE")
        p2 = prompt_rows.get("P2_STRUCTURED")
        p3 = prompt_rows.get("P3_COOPERATIVE_OBJECTIVE")
        if p1:
            invalidates_p1 = p1["ambiguous_invalid_response_count"] > 0 or p1["parser_success_given_provider_success"] < 1.0
            if invalidates_p1 and p2 and p3 and (p2["provider_success_count"] > p1["provider_success_count"] or p3["provider_success_count"] > p1["provider_success_count"]):
                selected_prompt = "P2_STRUCTURED" if p2["provider_success_count"] >= p3["provider_success_count"] else "P3_COOPERATIVE_OBJECTIVE"
    return {
        "prompt_order": list(prompt_order),
        "selected_seed": selected_seed,
        "selected_prompt": selected_prompt,
        "prompt_count": len(prompt_comparison_rows),
        "provisional_canonical_prompt": "P1_BASELINE",
        "selection_policy": "retain P1 unless valid-provider evidence shows a real prompt defect",
        "method_changed": False,
    }


def run_revalidation(
    *,
    output_root: Path = OUTPUT_ROOT,
    seed_candidates: Sequence[int] = DEFAULT_NEW_SEEDS,
    rng: random.Random | None = None,
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
    density: str = "low",
    vehicle_count: int = 4,
    llm_mode: str = "real",
    decision_interval: int = 1,
) -> dict[str, object]:
    output_root.mkdir(parents=True, exist_ok=True)
    prompt_hash_audit = verify_prompt_hashes()
    request_config_audit = verify_frozen_request_config()
    if not prompt_hash_audit.matches:
        raise RuntimeError("PROMPT_VERSION_MISMATCH")
    if not request_config_audit.matches:
        raise RuntimeError("FROZEN_REQUEST_CONFIG_MISMATCH")

    selected_seed = select_development_seed(seed_candidates, rng=rng)
    prompt_order = choose_prompt_order(PROMPT_IDS, rng=rng)
    run_manifest = build_run_manifest(
        selected_seed=selected_seed,
        prompt_order=prompt_order,
        prompt_hash_audit=prompt_hash_audit,
        request_config_audit=request_config_audit,
        vehicle_count=vehicle_count,
        density=density,
        scenario_id=f"canonical_prompt_revalidation_seed{selected_seed}_v{vehicle_count}",
    )
    write_json(output_root / "run_manifest.json", run_manifest)

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        provider_probe = {
            "provider": LIVE_PROVIDER_NAME,
            "model": LIVE_MODEL,
            "status": "missing_credential",
            "failure_classification": "LOCAL_CREDENTIAL_ACCESS_FAILED",
            "request_attempted": False,
        }
        write_json(output_root / "provider_probe.json", provider_probe)
        raise RuntimeError("LOCAL_CREDENTIAL_ACCESS_FAILED")

    provider_probe = run_provider_probe(api_key)
    write_json(output_root / "provider_probe.json", provider_probe)
    if not provider_probe["provider_request_success"]:
        raise RuntimeError(provider_probe["failure_classification"])

    prompt_texts = load_prompt_texts()
    prompt_results: list[dict[str, object]] = []
    request_trace_rows: list[dict[str, object]] = []
    rerun_counts = {prompt_id: 0 for prompt_id in PROMPT_IDS}

    for index, prompt_id in enumerate(prompt_order):
        prompt_result = run_single_prompt_run(
            prompt_id=prompt_id,
            prompt_text=prompt_texts[prompt_id],
            seed=selected_seed,
            vehicle_count=vehicle_count,
            density=density,
            llm_mode=llm_mode,
            llm_api_key=api_key,
            decision_interval=decision_interval,
            technical_rerun=False,
        )
        prompt_results.append(prompt_result)
        request_trace_rows.extend(
            build_request_trace_rows(
                prompt_id=prompt_id,
                request_groups=prompt_result["request_groups"],
                technical_rerun=False,
            )
        )

        if should_allow_technical_rerun(int(prompt_result["summary"]["provider_success_count"]), rerun_counts[prompt_id]):
            rerun_counts[prompt_id] += 1
            time.sleep(cooldown_seconds)
            rerun_result = run_single_prompt_run(
                prompt_id=prompt_id,
                prompt_text=prompt_texts[prompt_id],
                seed=selected_seed,
                vehicle_count=vehicle_count,
                density=density,
                llm_mode=llm_mode,
                llm_api_key=api_key,
                decision_interval=decision_interval,
                technical_rerun=True,
            )
            prompt_results.append(rerun_result)
            request_trace_rows.extend(
                build_request_trace_rows(
                    prompt_id=prompt_id,
                    request_groups=rerun_result["request_groups"],
                    technical_rerun=True,
                )
            )

        if index < len(prompt_order) - 1:
            time.sleep(cooldown_seconds)

    comparison_rows = build_prompt_comparison_rows(prompt_results)
    comparison_path = output_root / "prompt_comparison.csv"
    with comparison_path.open("w", encoding="utf-8", newline="") as f:
        if comparison_rows:
            writer = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()))
            writer.writeheader()
            writer.writerows(comparison_rows)

    write_jsonl(output_root / "request_trace.jsonl", request_trace_rows)
    summary = build_revalidation_summary(comparison_rows, prompt_order, selected_seed)
    summary["provider_probe"] = provider_probe
    summary["prompt_hashes"] = dict(prompt_hash_audit.current)
    summary["request_config"] = dict(request_config_audit.current)
    summary["result_count"] = len(prompt_results)
    write_json(output_root / "revalidation_summary.json", summary)
    return summary
