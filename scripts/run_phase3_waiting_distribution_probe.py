"""Manual-only Phase 3 fixed-state individual-waiting distribution probe."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from math import inf
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import resolve_llm_api_key
from src.controllers.decision_pipeline import execute_llm_candidate_selector_pipeline
from src.llm.candidate_selector import build_candidate_selection_context, run_live_candidate_request
from src.llm.request_config import PHASE2_MODEL, create_phase2_live_client
from src.safety.route_semantics import describe_edge_pair

from scripts.run_phase3b_repeatability import connectivity_gate


SOURCE = Path(
    "results/phase2_formal/batch2_remaining_matrix/runs/"
    "s3_cooperative_opportunity_v12_seed1/"
    "phase2_formal_batch2_s3_cooperative_opportunity_v12_seed1_gemini_candidate/"
    "decision_records.jsonl"
)
OUTPUT_ROOT = Path("results/phase3_waiting_distribution_probe")
RESULTS_PATH = Path("release_evidence/targeted_validation/phase3_waiting_distribution_results.csv")
ANALYSIS_PATH = Path("release_evidence/targeted_validation/phase3_waiting_distribution_analysis.md")
CONDITIONS = (
    ("BALANCED", (10.0, 10.0)),
    ("MODERATELY_SKEWED", (7.0, 13.0)),
    ("HIGHLY_SKEWED", (2.0, 18.0)),
)
REPLICATES_PER_CONDITION = 5
FIXED_AGGREGATE_WAITING = 20.0


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def _template() -> tuple[dict, list[dict], list[list[str]], tuple[str, ...], tuple[str, ...]]:
    records = (json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip())
    record = next(item for item in records if item.get("candidate_disagreement") and item.get("decision_epoch") == 3)
    states = [dict(item) for item in record["privacy_minimised_vehicle_inputs"]]
    groups = [list(item["vehicle_ids"]) for item in record["candidate_set"]]
    straight = tuple(record["llm_candidate_id"].split("|"))
    right = tuple(record["deterministic_candidate_id"].split("|"))
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
    if [by_id[item]["movement"] for item in straight] != ["STRAIGHT", "STRAIGHT"]:
        raise RuntimeError("Frozen S2 template movements do not match preregistration")
    if {by_id[item]["movement"] for item in right} != {"RIGHT"}:
        raise RuntimeError("Frozen R4 template movements do not match preregistration")
    return record, states, groups, straight, right


def planned_request_ids() -> tuple[str, ...]:
    return tuple(
        f"{condition}_R{replicate}"
        for condition, _ in CONDITIONS
        for replicate in range(1, REPLICATES_PER_CONDITION + 1)
    )


def _states_for_distribution(base_states: list[dict], straight: tuple[str, ...], distribution: tuple[float, float]) -> list[dict]:
    if len(straight) != 2 or sum(distribution) != FIXED_AGGREGATE_WAITING:
        raise RuntimeError("Registered distribution must contain two values totaling the fixed aggregate")
    states = [dict(item) for item in base_states]
    waiting_by_id = dict(zip(straight, distribution, strict=True))
    for item in states:
        if item["vehicle_id"] in waiting_by_id:
            item["waiting_time"] = waiting_by_id[item["vehicle_id"]]
    return states


def _classify(selected: str, candidate_ids: list[str], straight: tuple[str, ...], right: tuple[str, ...], valid: bool) -> str:
    if not valid or selected not in candidate_ids:
        return "INVALID"
    if selected == "|".join(right):
        return "R4"
    if selected == "|".join(straight):
        return "S2"
    return "OTHER_LEGAL"


def _row(condition: str, replicate: int, distribution: tuple[float, float], record: dict, *, status: str = "NOT_RUN") -> dict:
    return {
        "request_id": f"{condition}_R{replicate}",
        "condition_id": condition,
        "replicate": replicate,
        "s2_individual_waiting_values": json.dumps(distribution),
        "s2_aggregate_waiting_time": FIXED_AGGREGATE_WAITING,
        "status": status,
        "selection_class": status,
        "selected_candidate_id": "",
        "selected_candidate_legal": False,
        "provider_request_success": False,
        "parser_success": False,
        "fallback_used": False,
        "latency_ms": "",
        "llm_raw_output": "",
        "timestamp_utc": "",
        "prompt_hash": "",
        "candidate_set_hash": "",
        "input_state_hash": "",
        "candidate_ids": "",
        "source_scenario_id": record["scenario_id"],
        "source_seed": record["seed"],
        "source_decision_epoch": record["decision_epoch"],
        "provider_failure_reason": "",
        "parser_failure_reason": "",
        "request_attempt_count": "",
        "generation_config": json.dumps({"provider": "Gemini", "model": PHASE2_MODEL}, sort_keys=True),
    }


def _run_one(condition: str, replicate: int, distribution: tuple[float, float], template, provider_call: Callable[[str, list[str]], object]) -> dict:
    record, base_states, groups, straight, right = template
    states = _states_for_distribution(base_states, straight, distribution)
    local_state, features, _ = build_candidate_selection_context(states, groups)
    candidate_ids = [item["candidate_id"] for item in features]
    sent_prompts: list[str] = []

    def capture_prompt(prompt: str):
        sent_prompts.append(prompt)
        return provider_call(prompt, candidate_ids)

    trace = execute_llm_candidate_selector_pipeline(
        states,
        groups,
        capture_prompt,
        provider_name="Gemini",
        model_name=PHASE2_MODEL,
        llm_mode="phase3_waiting_distribution",
    )
    entry = next(iter(trace.values()))
    selected = str(entry.get("llm_candidate_id") or "")
    valid = bool(entry.get("provider_request_success")) and bool(entry.get("parser_success")) and not bool(entry.get("fallback_used")) and selected in candidate_ids
    result = _row(condition, replicate, distribution, record, status="VALID" if valid else "INVALID")
    result.update(
        {
            "selection_class": _classify(selected, candidate_ids, straight, right, valid),
            "selected_candidate_id": selected,
            "selected_candidate_legal": selected in candidate_ids,
            "provider_request_success": entry.get("provider_request_success"),
            "parser_success": entry.get("parser_success"),
            "fallback_used": entry.get("fallback_used"),
            "latency_ms": entry.get("latency_ms"),
            "llm_raw_output": entry.get("llm_raw_output", ""),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "prompt_hash": hashlib.sha256(sent_prompts[0].encode("utf-8")).hexdigest().upper() if sent_prompts else "",
            "candidate_set_hash": _sha256_json(groups),
            "input_state_hash": _sha256_json(local_state),
            "candidate_ids": json.dumps(candidate_ids),
            "provider_failure_reason": entry.get("provider_failure_reason", ""),
            "parser_failure_reason": entry.get("parser_failure_reason", ""),
            "request_attempt_count": entry.get("request_attempt_count", ""),
        }
    )
    return result


def _write_results(rows: list[dict]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_analysis(rows: list[dict], gate_passed: bool) -> None:
    if ANALYSIS_PATH.exists():
        raise RuntimeError("Distribution analysis already exists; refusing to overwrite")
    lines = ["# Phase 3 Waiting Distribution Analysis", ""]
    if not gate_passed:
        lines += ["Connectivity gate failed. All experimental requests are NOT_RUN.", "Outcome: INCONCLUSIVE."]
    else:
        lines += ["Descriptive only; five replicates per condition do not support population inference.", "", "| Condition | R4 | S2 | OTHER_LEGAL | INVALID |", "| --- | ---: | ---: | ---: | ---: |"]
        for condition, _ in CONDITIONS:
            subset = [row for row in rows if row["condition_id"] == condition]
            counts = {name: sum(row["selection_class"] == name for row in subset) for name in ("R4", "S2", "OTHER_LEGAL", "INVALID")}
            lines.append(f"| {condition} | {counts['R4']}/5 | {counts['S2']}/5 | {counts['OTHER_LEGAL']}/5 | {counts['INVALID']}/5 |")
        lines += ["", "Apply only the preregistered classification in `phase3_waiting_distribution_preregistration.md`."]
    ANALYSIS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(*, connectivity: Callable[[], dict], provider_call: Callable[[str, list[str]], object]) -> int:
    if OUTPUT_ROOT.exists() or RESULTS_PATH.exists() or ANALYSIS_PATH.exists():
        raise RuntimeError("Waiting-distribution evidence namespace already exists; refusing to overwrite")
    template = _template()
    record = template[0]
    OUTPUT_ROOT.mkdir(parents=True)
    gate = connectivity()
    _write_json(OUTPUT_ROOT / "connectivity.json", gate)
    if not gate.get("provider_response_success"):
        rows = [_row(condition, replicate, distribution, record) for condition, distribution in CONDITIONS for replicate in range(1, REPLICATES_PER_CONDITION + 1)]
        _write_results(rows)
        _write_analysis(rows, False)
        _write_json(OUTPUT_ROOT / "run_metadata.json", {"status": "CONNECTIVITY_FAILED", "experimental_logical_requests": 0})
        return 1
    raw = OUTPUT_ROOT / "raw_decisions"
    raw.mkdir()
    rows = []
    for condition, distribution in CONDITIONS:
        for replicate in range(1, REPLICATES_PER_CONDITION + 1):
            request_id = f"{condition}_R{replicate}"
            print(f"[PHASE3 DISTRIBUTION {request_id} REQUEST START]", flush=True)
            item = _run_one(condition, replicate, distribution, template, provider_call)
            _write_json(raw / f"{request_id}.json", item)
            rows.append(item)
            print(f"[PHASE3 DISTRIBUTION {request_id} {item['status']} ]", flush=True)
    _write_results(rows)
    _write_analysis(rows, True)
    _write_json(
        OUTPUT_ROOT / "run_metadata.json",
        {
            "status": "COMPLETED",
            "provider": "Gemini",
            "model": PHASE2_MODEL,
            "conditions": CONDITIONS,
            "replicates_per_condition": REPLICATES_PER_CONDITION,
            "experimental_logical_requests": len(planned_request_ids()),
            "retry_policy": "NO_LOGICAL_REQUEST_REPLACEMENT",
        },
    )
    print("[PHASE3 DISTRIBUTION DONE]", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        template = _template()
        state_hashes = set()
        candidate_hashes = set()
        for _, distribution in CONDITIONS:
            states = _states_for_distribution(template[1], template[3], distribution)
            local_state, features, _ = build_candidate_selection_context(states, template[2])
            if len(features) != 18:
                raise RuntimeError("template candidate set changed")
            state_hashes.add(_sha256_json(local_state))
            candidate_hashes.add(_sha256_json(template[2]))
        if len(planned_request_ids()) != 15 or len(state_hashes) != len(CONDITIONS) or len(candidate_hashes) != 1:
            raise RuntimeError("registered distribution plan is inconsistent")
        print("[PHASE3 DISTRIBUTION VALIDATE-ONLY PASS]", flush=True)
        return 0
    client = create_phase2_live_client(api_key=resolve_llm_api_key("Gemini"))
    return execute(
        connectivity=connectivity_gate,
        provider_call=lambda prompt, ids: run_live_candidate_request(client, model_name=PHASE2_MODEL, prompt=prompt, candidate_ids=ids),
    )


if __name__ == "__main__":
    raise SystemExit(main())
