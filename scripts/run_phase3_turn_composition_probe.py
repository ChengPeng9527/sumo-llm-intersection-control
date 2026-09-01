"""Manual-only Phase 3 matched turn-composition fixed-state probe."""
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

from scripts.run_phase3_waiting_distribution_probe import _sha256_json, _write_json, connectivity_gate


SOURCE = Path(
    "results/phase2_formal/batch2_remaining_matrix/runs/"
    "s3_cooperative_opportunity_v12_seed2/"
    "phase2_formal_batch2_s3_cooperative_opportunity_v12_seed2_gemini_candidate/"
    "decision_records.jsonl"
)
OUTPUT_ROOT = Path("results/phase3_turn_composition_probe")
RESULTS_PATH = Path("release_evidence/targeted_validation/phase3_turn_composition_results.csv")
ANALYSIS_PATH = Path("release_evidence/targeted_validation/phase3_turn_composition_analysis.md")
CONDITIONS = ("RIGHT_TARGET_FIRST", "STRAIGHT_TARGET_FIRST")
REPLICATES_PER_CONDITION = 5


def _template() -> tuple[dict, list[dict], list[list[str]], tuple[str, ...], tuple[str, ...]]:
    records = (json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip())
    record = next(item for item in records if item["decision_epoch"] == 2)
    states = [dict(item) for item in record["privacy_minimised_vehicle_inputs"]]
    for item in states:
        if item.get("time_to_intersection") is None:
            item["time_to_intersection"] = inf
        item["route_id"] = describe_edge_pair(item["incoming_edge"], item["outgoing_edge"]).route_id
    groups = [list(item["vehicle_ids"]) for item in record["candidate_set"]]
    right = tuple("phase2_s3_cooperative_opportunity_v12_seed2_2_3|phase2_s3_cooperative_opportunity_v12_seed2_2_1".split("|"))
    straight = tuple("phase2_s3_cooperative_opportunity_v12_seed2_2_5|phase2_s3_cooperative_opportunity_v12_seed2_2_4".split("|"))
    if list(right) not in groups or list(straight) not in groups or len(groups) != 11:
        raise RuntimeError("Frozen matched-turn template no longer has the registered legal candidates")
    by_id = {item["vehicle_id"]: item for item in states}
    if [by_id[item]["movement"] for item in right] != ["RIGHT", "RIGHT"]:
        raise RuntimeError("Registered RIGHT target no longer matches frozen state")
    if [by_id[item]["movement"] for item in straight] != ["STRAIGHT", "STRAIGHT"]:
        raise RuntimeError("Registered STRAIGHT target no longer matches frozen state")
    return record, states, groups, right, straight


def planned_request_ids() -> tuple[str, ...]:
    return tuple(f"{condition}_R{replicate}" for condition in CONDITIONS for replicate in range(1, REPLICATES_PER_CONDITION + 1))


def _normalised_states(base_states: list[dict], right: tuple[str, ...], straight: tuple[str, ...]) -> list[dict]:
    """Pairwise match target local-state fields while retaining real route/movement identity."""
    states = [dict(item) for item in base_states]
    by_id = {item["vehicle_id"]: item for item in states}
    for right_id, straight_id in zip(right, straight, strict=True):
        for field in ("waiting_time", "speed", "distance_to_intersection", "time_to_intersection", "inside_control_zone"):
            by_id[straight_id][field] = by_id[right_id][field]
    return states


def _ordered_groups(groups: list[list[str]], right: tuple[str, ...], straight: tuple[str, ...], condition: str) -> list[list[str]]:
    ordered = [list(group) for group in groups]
    right_index = ordered.index(list(right))
    straight_index = ordered.index(list(straight))
    if condition == "RIGHT_TARGET_FIRST" and right_index > straight_index:
        ordered[right_index], ordered[straight_index] = ordered[straight_index], ordered[right_index]
    elif condition == "STRAIGHT_TARGET_FIRST" and straight_index > right_index:
        ordered[right_index], ordered[straight_index] = ordered[straight_index], ordered[right_index]
    elif condition not in CONDITIONS:
        raise RuntimeError("Unregistered presentation-order condition")
    return ordered


def _classify(selected: str, candidate_ids: list[str], right: tuple[str, ...], straight: tuple[str, ...], valid: bool) -> str:
    if not valid or selected not in candidate_ids:
        return "INVALID"
    if selected == "|".join(right):
        return "RIGHT_2"
    if selected == "|".join(straight):
        return "STRAIGHT_2"
    return "OTHER_LEGAL"


def _row(condition: str, replicate: int, record: dict, *, status: str = "NOT_RUN") -> dict:
    return {
        "request_id": f"{condition}_R{replicate}", "condition_id": condition, "replicate": replicate,
        "status": status, "selection_class": status, "selected_candidate_id": "", "selected_candidate_legal": False,
        "provider_request_success": False, "parser_success": False, "fallback_used": False, "latency_ms": "", "llm_raw_output": "",
        "timestamp_utc": "", "prompt_hash": "", "candidate_set_hash": "", "candidate_presentation_hash": "", "input_state_hash": "", "candidate_ids": "",
        "right_target_id": "", "straight_target_id": "", "target_group_size": 2, "target_aggregate_waiting_time": 2.0, "target_maximum_waiting_time": 2.0,
        "source_scenario_id": record["scenario_id"], "source_seed": record["seed"], "source_decision_epoch": record["decision_epoch"],
        "provider_failure_reason": "", "parser_failure_reason": "", "request_attempt_count": "", "generation_config": json.dumps({"provider": "Gemini", "model": PHASE2_MODEL}, sort_keys=True),
    }


def _run_one(condition: str, replicate: int, template, provider_call: Callable[[str, list[str]], object]) -> dict:
    record, base_states, groups, right, straight = template
    states = _normalised_states(base_states, right, straight)
    ordered_groups = _ordered_groups(groups, right, straight, condition)
    local_state, features, _ = build_candidate_selection_context(states, ordered_groups)
    candidate_ids = [item["candidate_id"] for item in features]
    feature_by_id = {item["candidate_id"]: item for item in features}
    right_id, straight_id = "|".join(right), "|".join(straight)
    for feature in (feature_by_id[right_id], feature_by_id[straight_id]):
        if feature["group_size"] != 2 or feature["aggregate_waiting_time"] != 2.0 or feature["maximum_waiting_time"] != 2.0:
            raise RuntimeError("Target candidate matching invariant failed")
    if feature_by_id[right_id]["minimum_time_to_intersection"] != feature_by_id[straight_id]["minimum_time_to_intersection"]:
        raise RuntimeError("Target ETA matching invariant failed")
    sent_prompts: list[str] = []
    def capture_prompt(prompt: str):
        sent_prompts.append(prompt)
        return provider_call(prompt, candidate_ids)
    trace = execute_llm_candidate_selector_pipeline(states, ordered_groups, capture_prompt, provider_name="Gemini", model_name=PHASE2_MODEL, llm_mode="phase3_turn_composition")
    entry = next(iter(trace.values()))
    selected = str(entry.get("llm_candidate_id") or "")
    valid = bool(entry.get("provider_request_success")) and bool(entry.get("parser_success")) and not bool(entry.get("fallback_used")) and selected in candidate_ids
    result = _row(condition, replicate, record, status="VALID" if valid else "INVALID")
    result.update({
        "selection_class": _classify(selected, candidate_ids, right, straight, valid), "selected_candidate_id": selected,
        "selected_candidate_legal": selected in candidate_ids, "provider_request_success": entry.get("provider_request_success"),
        "parser_success": entry.get("parser_success"), "fallback_used": entry.get("fallback_used"), "latency_ms": entry.get("latency_ms"),
        "llm_raw_output": entry.get("llm_raw_output", ""), "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "prompt_hash": hashlib.sha256(sent_prompts[0].encode("utf-8")).hexdigest().upper() if sent_prompts else "",
        "candidate_set_hash": _sha256_json(sorted((tuple(group) for group in ordered_groups))), "candidate_presentation_hash": _sha256_json(ordered_groups),
        "input_state_hash": _sha256_json(local_state), "candidate_ids": json.dumps(candidate_ids), "right_target_id": right_id, "straight_target_id": straight_id,
        "provider_failure_reason": entry.get("provider_failure_reason", ""), "parser_failure_reason": entry.get("parser_failure_reason", ""), "request_attempt_count": entry.get("request_attempt_count", ""),
    })
    return result


def _write_results(rows: list[dict]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def _write_analysis(rows: list[dict], gate_passed: bool) -> None:
    if ANALYSIS_PATH.exists():
        raise RuntimeError("Turn-composition analysis already exists; refusing to overwrite")
    lines = ["# Phase 3 Turn-Composition Analysis", ""]
    if not gate_passed:
        lines += ["Connectivity gate failed. All 10 experimental requests are NOT_RUN.", "Outcome: INCONCLUSIVE."]
    else:
        lines += ["Descriptive only; n=5 per presentation order.", "", "| Condition | RIGHT_2 | STRAIGHT_2 | OTHER_LEGAL | INVALID |", "| --- | ---: | ---: | ---: | ---: |"]
        for condition in CONDITIONS:
            subset = [row for row in rows if row["condition_id"] == condition]
            counts = {name: sum(row["selection_class"] == name for row in subset) for name in ("RIGHT_2", "STRAIGHT_2", "OTHER_LEGAL", "INVALID")}
            lines.append(f"| {condition} | {counts['RIGHT_2']}/5 | {counts['STRAIGHT_2']}/5 | {counts['OTHER_LEGAL']}/5 | {counts['INVALID']}/5 |")
    ANALYSIS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def execute(*, connectivity: Callable[[], dict], provider_call: Callable[[str, list[str]], object]) -> int:
    if OUTPUT_ROOT.exists() or RESULTS_PATH.exists() or ANALYSIS_PATH.exists():
        raise RuntimeError("Turn-composition evidence namespace already exists; refusing to overwrite")
    template = _template(); record = template[0]; OUTPUT_ROOT.mkdir(parents=True)
    gate = connectivity(); _write_json(OUTPUT_ROOT / "connectivity.json", gate)
    if not gate.get("provider_response_success"):
        rows = [_row(condition, replicate, record) for condition in CONDITIONS for replicate in range(1, REPLICATES_PER_CONDITION + 1)]
        _write_results(rows); _write_analysis(rows, False); _write_json(OUTPUT_ROOT / "run_metadata.json", {"status": "CONNECTIVITY_FAILED", "experimental_logical_requests": 0})
        return 1
    raw = OUTPUT_ROOT / "raw_decisions"; raw.mkdir(); rows = []
    for condition in CONDITIONS:
        for replicate in range(1, REPLICATES_PER_CONDITION + 1):
            request_id = f"{condition}_R{replicate}"; print(f"[PHASE3 TURN {request_id} REQUEST START]", flush=True)
            row = _run_one(condition, replicate, template, provider_call); _write_json(raw / f"{request_id}.json", row); rows.append(row)
            print(f"[PHASE3 TURN {request_id} {row['status']} ]", flush=True)
    _write_results(rows); _write_analysis(rows, True)
    _write_json(OUTPUT_ROOT / "run_metadata.json", {"status": "COMPLETED", "provider": "Gemini", "model": PHASE2_MODEL, "conditions": CONDITIONS, "replicates_per_condition": REPLICATES_PER_CONDITION, "experimental_logical_requests": len(planned_request_ids()), "retry_policy": "NO_LOGICAL_REQUEST_REPLACEMENT"})
    print("[PHASE3 TURN DONE]", flush=True); return 0


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--validate-only", action="store_true"); args = parser.parse_args()
    if args.validate_only:
        template = _template(); record, states, groups, right, straight = template; normalised = _normalised_states(states, right, straight)
        presentation_hashes = set()
        for condition in CONDITIONS:
            ordered = _ordered_groups(groups, right, straight, condition); _, features, _ = build_candidate_selection_context(normalised, ordered)
            by_id = {item["candidate_id"]: item for item in features}; r, s = by_id["|".join(right)], by_id["|".join(straight)]
            if len(features) != 11 or (r["group_size"], r["aggregate_waiting_time"], r["maximum_waiting_time"], r["minimum_time_to_intersection"]) != (s["group_size"], s["aggregate_waiting_time"], s["maximum_waiting_time"], s["minimum_time_to_intersection"]): raise RuntimeError("matched target invariant failed")
            presentation_hashes.add(_sha256_json(ordered))
        if len(planned_request_ids()) != 10 or len(presentation_hashes) != 2: raise RuntimeError("registered turn plan is inconsistent")
        print("[PHASE3 TURN VALIDATE-ONLY PASS]", flush=True); return 0
    client = create_phase2_live_client(api_key=resolve_llm_api_key("Gemini"))
    return execute(connectivity=connectivity_gate, provider_call=lambda prompt, ids: run_live_candidate_request(client, model_name=PHASE2_MODEL, prompt=prompt, candidate_ids=ids))


if __name__ == "__main__":
    raise SystemExit(main())
