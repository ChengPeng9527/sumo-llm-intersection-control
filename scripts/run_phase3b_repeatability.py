"""Manual-only Phase 3B fixed-state repeatability runner."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from math import inf
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import resolve_llm_api_key
from src.controllers.decision_pipeline import execute_llm_candidate_selector_pipeline
from src.llm.candidate_selector import build_candidate_selection_context, run_live_candidate_request
from src.llm.request_config import PHASE2_BASE_URL, PHASE2_MODEL, PHASE2_TIMEOUT_SECONDS, build_candidate_selection_request_kwargs, create_phase2_live_client
from src.safety.route_semantics import describe_edge_pair

SOURCE = Path("results/phase2_formal/batch2_remaining_matrix/runs/s3_cooperative_opportunity_v12_seed1/phase2_formal_batch2_s3_cooperative_opportunity_v12_seed1_gemini_candidate/decision_records.jsonl")
OUTPUT_ROOT = Path("results/phase3b_repeatability")
RESULTS_PATH = Path("release_evidence/targeted_validation/phase3b_repeatability_results.csv")
ANALYSIS_PATH = Path("release_evidence/targeted_validation/phase3b_repeatability_analysis.md")
CONDITIONS = (("W08", 8.0), ("W19", 19.0), ("W20", 20.0), ("W24", 24.0))
REPLICATES_PER_CONDITION = 5


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _template() -> tuple[dict, list[dict], list[list[str]], tuple[str, ...], tuple[str, ...]]:
    records = (json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip())
    record = next(item for item in records if item.get("candidate_disagreement") and item.get("decision_epoch") == 3)
    states = [dict(item) for item in record["privacy_minimised_vehicle_inputs"]]
    groups = [list(item["vehicle_ids"]) for item in record["candidate_set"]]
    straight, right = tuple(record["llm_candidate_id"].split("|")), tuple(record["deterministic_candidate_id"].split("|"))
    if len(groups) != 18 or len(straight) != 2 or len(right) != 4:
        raise RuntimeError("Frozen template no longer has the registered S3-12V structure")
    by_id = {item["vehicle_id"]: item for item in states}
    for item in states:
        semantic = describe_edge_pair(item["incoming_edge"], item["outgoing_edge"])
        if semantic.movement != item["movement"]:
            raise RuntimeError("Frozen route/movement semantics are inconsistent")
        item["route_id"] = semantic.route_id
        if item.get("time_to_intersection") is None:
            item["time_to_intersection"] = inf
    if [by_id[item]["movement"] for item in straight] != ["STRAIGHT", "STRAIGHT"] or {by_id[item]["movement"] for item in right} != {"RIGHT"}:
        raise RuntimeError("Frozen R4/S2 template movements do not match preregistration")
    return record, states, groups, straight, right


def planned_request_ids() -> tuple[str, ...]:
    return tuple(f"{condition}_R{replicate}" for condition, _ in CONDITIONS for replicate in range(1, 6))


def _classify(selected: str, candidate_ids: list[str], straight: tuple[str, ...], right: tuple[str, ...], valid: bool) -> str:
    if not valid or selected not in candidate_ids:
        return "INVALID"
    if selected == "|".join(right):
        return "R4"
    if selected == "|".join(straight):
        return "S2"
    return "OTHER_LEGAL"


def _generation(candidate_ids: list[str]) -> dict:
    request = build_candidate_selection_request_kwargs(candidate_ids)
    return {"provider": "Gemini", "model": PHASE2_MODEL, "timeout_seconds": PHASE2_TIMEOUT_SECONDS, "temperature": "NOT_EXPLICITLY_CONFIGURED", "top_p": "NOT_EXPLICITLY_CONFIGURED", "top_k": "NOT_EXPLICITLY_CONFIGURED", "seed": "NOT_EXPLICITLY_CONFIGURED", "max_output_tokens": request["max_completion_tokens"], "response_mime_type": "application/json", "response_json_schema": request["response_json_schema"]}


def _row(condition: str, replicate: int, waiting: float, record: dict, *, status: str = "NOT_RUN") -> dict:
    return {"request_id": f"{condition}_R{replicate}", "condition_id": condition, "replicate": replicate, "aggregate_waiting_time": waiting, "status": status, "selection_class": status, "selected_candidate_id": "", "selected_candidate_legal": False, "provider_request_success": False, "parser_success": False, "fallback_used": False, "latency_ms": "", "llm_raw_output": "", "timestamp_utc": "", "prompt_hash": "", "candidate_set_hash": "", "candidate_ids": "", "source_scenario_id": record["scenario_id"], "source_seed": record["seed"], "source_decision_epoch": record["decision_epoch"], "provider_failure_reason": "", "parser_failure_reason": "", "request_attempt_count": "", "generation_config": ""}


def _run_one(condition: str, replicate: int, waiting: float, template, provider_call: Callable[[str, list[str]], object]) -> dict:
    record, base_states, groups, straight, right = template
    states = [dict(item) for item in base_states]
    for item in states:
        if item["vehicle_id"] in straight:
            item["waiting_time"] = waiting / 2.0
    _, features, _ = build_candidate_selection_context(states, groups)
    candidate_ids = [item["candidate_id"] for item in features]
    trace = execute_llm_candidate_selector_pipeline(states, groups, lambda prompt: provider_call(prompt, candidate_ids), provider_name="Gemini", model_name=PHASE2_MODEL, llm_mode="phase3b_repeatability")
    entry = next(iter(trace.values()))
    selected = str(entry.get("llm_candidate_id") or "")
    valid = bool(entry.get("provider_request_success")) and bool(entry.get("parser_success")) and not bool(entry.get("fallback_used")) and selected in candidate_ids
    result = _row(condition, replicate, waiting, record, status="VALID" if valid else "INVALID")
    result.update({"selection_class": _classify(selected, candidate_ids, straight, right, valid), "selected_candidate_id": selected, "selected_candidate_legal": selected in candidate_ids, "provider_request_success": entry.get("provider_request_success"), "parser_success": entry.get("parser_success"), "fallback_used": entry.get("fallback_used"), "latency_ms": entry.get("latency_ms"), "llm_raw_output": entry.get("llm_raw_output", ""), "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "prompt_hash": entry.get("prompt_hash", ""), "candidate_set_hash": hashlib.sha256("\n".join(candidate_ids).encode()).hexdigest().upper(), "candidate_ids": json.dumps(candidate_ids), "provider_failure_reason": entry.get("provider_failure_reason", ""), "parser_failure_reason": entry.get("parser_failure_reason", ""), "request_attempt_count": entry.get("request_attempt_count", ""), "generation_config": json.dumps(_generation(candidate_ids), sort_keys=True)})
    return result


def _write_results(rows: list[dict]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def _write_analysis(rows: list[dict], gate_passed: bool) -> None:
    if ANALYSIS_PATH.exists():
        raise RuntimeError("Repeatability analysis already exists; refusing to overwrite")
    lines = ["# Phase 3B Repeatability Analysis", ""]
    if not gate_passed:
        lines += ["Connectivity gate failed. All 20 experimental requests are NOT_RUN.", "Outcome: INCONCLUSIVE."]
    else:
        lines += ["Descriptive only; n=5 per condition is not a strong statistical test.", "", "| Condition | R4 | S2 | OTHER_LEGAL | INVALID |", "| --- | ---: | ---: | ---: | ---: |"]
        for condition, _ in CONDITIONS:
            subset = [row for row in rows if row["condition_id"] == condition]
            counts = {name: sum(row["selection_class"] == name for row in subset) for name in ("R4", "S2", "OTHER_LEGAL", "INVALID")}
            lines.append(f"| {condition} | {counts['R4']}/5 | {counts['S2']}/5 | {counts['OTHER_LEGAL']}/5 | {counts['INVALID']}/5 |")
        lines += ["", "Use only the preregistered categories: REPEATABLE_ORDERED_SHIFT, PARTIAL_REPEATABILITY, NO_CLEAR_REPEATABILITY, or INCONCLUSIVE. Do not infer an internal threshold, fairness optimisation, or superiority."]
    ANALYSIS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def connectivity_gate() -> dict:
    key = resolve_llm_api_key("Gemini")
    url = f"{PHASE2_BASE_URL}/models/{urllib.parse.quote(PHASE2_MODEL, safe='')}:generateContent?key={key}"
    body = {"contents": [{"parts": [{"text": "Return exactly JSON: {\\\"ok\\\":true}"}]}], "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 16}}
    result = {"provider": "Gemini", "model": PHASE2_MODEL, "proxy_detected": bool(urllib.request.getproxies()), "provider_response_success": False}
    started = time.monotonic()
    try:
        request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=PHASE2_TIMEOUT_SECONDS) as response:
            response.read(); result.update({"http_status": response.status, "provider_response_success": response.status == 200})
    except urllib.error.HTTPError as error:
        result.update({"http_status": error.code, "error_type": type(error).__name__, "error_message": str(error.reason)})
    except Exception as error:
        result.update({"http_status": None, "error_type": type(error).__name__, "error_message": str(error)[:500]})
    result["latency_ms"] = round((time.monotonic() - started) * 1000, 2)
    return result


def execute(*, connectivity: Callable[[], dict], provider_call: Callable[[str, list[str]], object]) -> int:
    if OUTPUT_ROOT.exists() or RESULTS_PATH.exists() or ANALYSIS_PATH.exists():
        raise RuntimeError("Repeatability evidence namespace already exists; refusing to overwrite")
    template = _template(); record = template[0]; OUTPUT_ROOT.mkdir(parents=True)
    gate = connectivity(); _write_json(OUTPUT_ROOT / "connectivity.json", gate)
    if not gate.get("provider_response_success"):
        rows = [_row(condition, replicate, waiting, record) for condition, waiting in CONDITIONS for replicate in range(1, 6)]
        _write_results(rows); _write_analysis(rows, False); _write_json(OUTPUT_ROOT / "run_metadata.json", {"status": "CONNECTIVITY_FAILED", "experimental_logical_requests": 0})
        return 1
    raw = OUTPUT_ROOT / "raw_decisions"; raw.mkdir(); rows = []
    for condition, waiting in CONDITIONS:
        for replicate in range(1, 6):
            request_id = f"{condition}_R{replicate}"; print(f"[PHASE3B {request_id} REQUEST START]", flush=True)
            item = _run_one(condition, replicate, waiting, template, provider_call); _write_json(raw / f"{request_id}.json", item); rows.append(item)
            print(f"[PHASE3B {request_id} {item['status']}]", flush=True)
    _write_results(rows); _write_analysis(rows, True)
    _write_json(OUTPUT_ROOT / "run_metadata.json", {"status": "COMPLETED", "provider": "Gemini", "model": PHASE2_MODEL, "conditions": CONDITIONS, "replicates_per_condition": 5, "experimental_logical_requests": 20, "retry_policy": "NO_LOGICAL_REQUEST_REPLACEMENT"})
    print("[PHASE3B DONE]", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--validate-only", action="store_true"); args = parser.parse_args()
    if args.validate_only:
        template = _template()
        for _, waiting in CONDITIONS:
            states = [dict(item) for item in template[1]]
            for item in states:
                if item["vehicle_id"] in template[3]: item["waiting_time"] = waiting / 2.0
            if len(build_candidate_selection_context(states, template[2])[1]) != 18: raise RuntimeError("template candidate set changed")
        if len(planned_request_ids()) != 20: raise RuntimeError("request plan must contain exactly 20 requests")
        print("[PHASE3B VALIDATE-ONLY PASS]", flush=True); return 0
    client = create_phase2_live_client(api_key=resolve_llm_api_key("Gemini"))
    return execute(connectivity=connectivity_gate, provider_call=lambda prompt, ids: run_live_candidate_request(client, model_name=PHASE2_MODEL, prompt=prompt, candidate_ids=ids))


if __name__ == "__main__":
    raise SystemExit(main())
