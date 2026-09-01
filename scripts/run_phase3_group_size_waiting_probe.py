"""Manual-only Phase 3 group-size x aggregate-waiting probe runner."""
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
from src.llm.request_config import (
    PHASE2_BASE_URL,
    PHASE2_MODEL,
    PHASE2_TIMEOUT_SECONDS,
    build_candidate_selection_request_kwargs,
    create_phase2_live_client,
)
from src.safety.route_semantics import describe_edge_pair


SOURCE = Path(
    "results/phase2_formal/batch2_remaining_matrix/runs/"
    "s3_cooperative_opportunity_v12_seed2/"
    "phase2_formal_batch2_s3_cooperative_opportunity_v12_seed2_gemini_candidate/"
    "decision_records.jsonl"
)
PREREGISTRATION_PATH = Path(
    "release_evidence/targeted_validation/phase3_group_size_waiting_preregistration.md"
)
OUTPUT_ROOT = Path("results/phase3_group_size_waiting_probe")
RESULTS_PATH = Path(
    "release_evidence/targeted_validation/phase3_group_size_waiting_results.csv"
)
ANALYSIS_PATH = Path(
    "release_evidence/targeted_validation/phase3_group_size_waiting_analysis.md"
)

CONDITIONS = (
    {"condition_id": "G1_LOW", "group_size_advantage": 1, "waiting_regime": "LOW", "s2_waiting": 8.0},
    {"condition_id": "G1_HIGH", "group_size_advantage": 1, "waiting_regime": "HIGH", "s2_waiting": 20.0},
    {"condition_id": "G2_LOW", "group_size_advantage": 2, "waiting_regime": "LOW", "s2_waiting": 8.0},
    {"condition_id": "G2_HIGH", "group_size_advantage": 2, "waiting_regime": "HIGH", "s2_waiting": 20.0},
)
REPLICATES_PER_CELL = 3


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_json(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def _candidate_id(group: list[str] | tuple[str, ...]) -> str:
    return "|".join(group)


def _template() -> dict:
    records = (
        json.loads(line)
        for line in SOURCE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    record = next(
        item
        for item in records
        if item.get("candidate_disagreement") and item.get("decision_epoch") == 3
    )
    if int(record.get("seed", -1)) != 2 or len(record.get("candidate_set", [])) != 18:
        raise RuntimeError("Frozen anchor no longer matches S3-12V seed 2 epoch 3")

    states = [dict(item) for item in record["privacy_minimised_vehicle_inputs"]]
    groups = [list(item["vehicle_ids"]) for item in record["candidate_set"]]
    s2 = tuple(str(record["llm_candidate_id"]).split("|"))
    r4 = tuple(str(record["deterministic_candidate_id"]).split("|"))
    by_id = {item["vehicle_id"]: item for item in states}

    for item in states:
        semantic = describe_edge_pair(item["incoming_edge"], item["outgoing_edge"])
        if semantic.movement != item["movement"]:
            raise RuntimeError("Frozen route/movement semantics are inconsistent")
        item["route_id"] = semantic.route_id
        if item.get("time_to_intersection") is None:
            item["time_to_intersection"] = inf

    r3_candidates = []
    for group in groups:
        if len(group) != 3 or not set(group).issubset(r4):
            continue
        if {by_id[vehicle_id]["movement"] for vehicle_id in group} == {"RIGHT"}:
            r3_candidates.append(tuple(group))
    if len(s2) != 2 or len(r4) != 4 or len(r3_candidates) != 1:
        raise RuntimeError("Frozen anchor does not contain unique registered R3/R4/S2 targets")
    r3 = r3_candidates[0]
    omitted = tuple(set(r4) - set(r3))
    if len(omitted) != 1:
        raise RuntimeError("R3 must differ from R4 by exactly one vehicle")
    if [by_id[item]["movement"] for item in s2] != ["STRAIGHT", "STRAIGHT"]:
        raise RuntimeError("S2 target movement structure changed")
    if {by_id[item]["movement"] for item in r4} != {"RIGHT"}:
        raise RuntimeError("R4 target movement structure changed")
    if any(by_id[item].get("time_to_intersection") != inf for item in set(r4) | set(s2)):
        raise RuntimeError("Registered seed-2 target ETA matching no longer holds")

    return {
        "record": record,
        "states": states,
        "groups": groups,
        "s2": s2,
        "r3": r3,
        "r4": r4,
        "omitted_for_g1": omitted[0],
    }


def planned_request_ids() -> tuple[str, ...]:
    return tuple(
        f"{condition['condition_id']}_R{replicate}"
        for condition in CONDITIONS
        for replicate in range(1, REPLICATES_PER_CELL + 1)
    )


def _condition_fixture(template: dict, condition: dict) -> dict:
    s2 = template["s2"]
    larger = template["r3"] if condition["group_size_advantage"] == 1 else template["r4"]
    active_ids = {item["vehicle_id"] for item in template["states"]}
    if condition["group_size_advantage"] == 1:
        active_ids.remove(template["omitted_for_g1"])

    states = [dict(item) for item in template["states"] if item["vehicle_id"] in active_ids]
    for item in states:
        if item["vehicle_id"] in template["r4"]:
            item["waiting_time"] = 0.0
        if item["vehicle_id"] in s2:
            item["waiting_time"] = condition["s2_waiting"] / 2.0

    complete_groups = [
        list(group) for group in template["groups"] if set(group).issubset(active_ids)
    ]
    target_ids = {_candidate_id(s2), _candidate_id(larger)}
    non_targets = [group for group in complete_groups if _candidate_id(group) not in target_ids]
    ordered_groups = non_targets + [list(s2), list(larger)]

    local_state, features, _ = build_candidate_selection_context(states, ordered_groups)
    candidate_ids = [item["candidate_id"] for item in features]
    feature_by_id = {item["candidate_id"]: item for item in features}
    larger_id = _candidate_id(larger)
    s2_id = _candidate_id(s2)
    expected_count = 13 if condition["group_size_advantage"] == 1 else 18
    if len(candidate_ids) != expected_count:
        raise RuntimeError("Registered candidate richness changed")
    if larger_id not in feature_by_id or s2_id not in feature_by_id:
        raise RuntimeError("Registered legal target missing from condition")
    if candidate_ids[-2:] != [s2_id, larger_id]:
        raise RuntimeError("Registered target presentation order changed")

    larger_feature = feature_by_id[larger_id]
    s2_feature = feature_by_id[s2_id]
    if larger_feature["group_size"] - s2_feature["group_size"] != condition["group_size_advantage"]:
        raise RuntimeError("Group-size contrast does not match condition")
    if larger_feature["aggregate_waiting_time"] != 0.0:
        raise RuntimeError("Larger-group waiting control changed")
    if s2_feature["aggregate_waiting_time"] != condition["s2_waiting"]:
        raise RuntimeError("S2 aggregate-waiting control changed")

    return {
        "states": states,
        "groups": ordered_groups,
        "local_state": local_state,
        "features": features,
        "candidate_ids": candidate_ids,
        "larger_id": larger_id,
        "s2_id": s2_id,
        "larger_feature": larger_feature,
        "s2_feature": s2_feature,
    }


def _classify(selected: str, fixture: dict, valid: bool) -> str:
    if not valid or selected not in fixture["candidate_ids"]:
        return "INVALID"
    if selected == fixture["larger_id"]:
        return "LARGER_GROUP"
    if selected == fixture["s2_id"]:
        return "SMALLER_HIGH_WAIT"
    return "OTHER_LEGAL"


def _generation_config(candidate_ids: list[str]) -> dict:
    request = build_candidate_selection_request_kwargs(candidate_ids)
    return {
        "provider": "Gemini",
        "model": PHASE2_MODEL,
        "timeout_seconds": PHASE2_TIMEOUT_SECONDS,
        "temperature": "NOT_EXPLICITLY_CONFIGURED",
        "top_p": "NOT_EXPLICITLY_CONFIGURED",
        "top_k": "NOT_EXPLICITLY_CONFIGURED",
        "seed": "NOT_EXPLICITLY_CONFIGURED",
        "max_output_tokens": request["max_completion_tokens"],
        "response_mime_type": "application/json",
        "response_json_schema": request["response_json_schema"],
    }


def _blank_row(condition: dict, replicate: int, template: dict, *, status: str = "NOT_RUN") -> dict:
    larger_size = 2 + condition["group_size_advantage"]
    return {
        "request_id": f"{condition['condition_id']}_R{replicate}",
        "condition_id": condition["condition_id"],
        "replicate": replicate,
        "waiting_regime": condition["waiting_regime"],
        "group_size_advantage": condition["group_size_advantage"],
        "larger_group_size": larger_size,
        "smaller_group_size": 2,
        "larger_group_aggregate_waiting": 0.0,
        "smaller_group_aggregate_waiting": condition["s2_waiting"],
        "larger_group_individual_waiting": "",
        "smaller_group_individual_waiting": json.dumps([condition["s2_waiting"] / 2.0] * 2),
        "larger_group_turn_composition": "RIGHT|" * (larger_size - 1) + "RIGHT",
        "smaller_group_turn_composition": "STRAIGHT|STRAIGHT",
        "larger_group_minimum_eta": "UNAVAILABLE",
        "smaller_group_minimum_eta": "UNAVAILABLE",
        "candidate_count": 13 if condition["group_size_advantage"] == 1 else 18,
        "candidate_ids": "",
        "larger_candidate_id": "",
        "smaller_candidate_id": "",
        "selected_candidate_id": "",
        "selection_class": status,
        "selected_candidate_legal": False,
        "status": status,
        "provider_request_success": False,
        "parser_success": False,
        "fallback_used": False,
        "latency_ms": "",
        "llm_raw_output": "",
        "timestamp_utc": "",
        "prompt_hash": "",
        "input_state_hash": "",
        "candidate_set_hash": "",
        "candidate_presentation_hash": "",
        "generation_config": "",
        "provider_failure_reason": "",
        "parser_failure_reason": "",
        "request_attempt_count": "",
        "source_scenario_id": template["record"]["scenario_id"],
        "source_seed": template["record"]["seed"],
        "source_decision_epoch": template["record"]["decision_epoch"],
    }


def _run_one(
    condition: dict,
    replicate: int,
    template: dict,
    provider_call: Callable[[str, list[str]], object],
) -> dict:
    fixture = _condition_fixture(template, condition)
    sent_prompts: list[str] = []

    def call(prompt: str):
        sent_prompts.append(prompt)
        return provider_call(prompt, fixture["candidate_ids"])

    trace = execute_llm_candidate_selector_pipeline(
        fixture["states"],
        fixture["groups"],
        call,
        provider_name="Gemini",
        model_name=PHASE2_MODEL,
        llm_mode="phase3_group_size_waiting_probe",
    )
    entry = next(iter(trace.values()))
    selected = str(entry.get("llm_candidate_id") or "")
    valid = (
        entry.get("provider_request_success") is True
        and entry.get("parser_success") is True
        and entry.get("fallback_used") is False
        and selected in fixture["candidate_ids"]
    )
    result = _blank_row(condition, replicate, template, status="VALID" if valid else "INVALID")
    result.update(
        {
            "larger_group_individual_waiting": json.dumps(
                [0.0] * fixture["larger_feature"]["group_size"]
            ),
            "candidate_ids": json.dumps(fixture["candidate_ids"]),
            "larger_candidate_id": fixture["larger_id"],
            "smaller_candidate_id": fixture["s2_id"],
            "selected_candidate_id": selected,
            "selection_class": _classify(selected, fixture, valid),
            "selected_candidate_legal": selected in fixture["candidate_ids"],
            "provider_request_success": entry.get("provider_request_success"),
            "parser_success": entry.get("parser_success"),
            "fallback_used": entry.get("fallback_used"),
            "latency_ms": entry.get("latency_ms"),
            "llm_raw_output": entry.get("llm_raw_output", ""),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "prompt_hash": hashlib.sha256(sent_prompts[0].encode("utf-8")).hexdigest().upper()
            if sent_prompts
            else "",
            "input_state_hash": _sha256_json(fixture["local_state"]),
            "candidate_set_hash": _sha256_json(sorted(tuple(group) for group in fixture["groups"])),
            "candidate_presentation_hash": _sha256_json(fixture["groups"]),
            "generation_config": json.dumps(
                _generation_config(fixture["candidate_ids"]), sort_keys=True
            ),
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


def _counts(rows: list[dict], condition_id: str) -> dict[str, int]:
    subset = [row for row in rows if row["condition_id"] == condition_id]
    return {
        key: sum(row["selection_class"] == key for row in subset)
        for key in ("LARGER_GROUP", "SMALLER_HIGH_WAIT", "OTHER_LEGAL", "INVALID")
    }


def classify_result(rows: list[dict]) -> str:
    counts = {condition["condition_id"]: _counts(rows, condition["condition_id"]) for condition in CONDITIONS}
    if any(3 - item["INVALID"] < 2 for item in counts.values()):
        return "INCONCLUSIVE"

    waiting_effect = False
    waiting_consistent = True
    for prefix in ("G1", "G2"):
        low, high = counts[f"{prefix}_LOW"], counts[f"{prefix}_HIGH"]
        s2_delta = high["SMALLER_HIGH_WAIT"] - low["SMALLER_HIGH_WAIT"]
        larger_delta = low["LARGER_GROUP"] - high["LARGER_GROUP"]
        waiting_effect = waiting_effect or (s2_delta >= 2 and larger_delta >= 2)
        waiting_consistent = waiting_consistent and s2_delta >= 0 and larger_delta >= 0

    size_effect = False
    size_consistent = True
    for regime in ("LOW", "HIGH"):
        g1, g2 = counts[f"G1_{regime}"], counts[f"G2_{regime}"]
        larger_delta = g2["LARGER_GROUP"] - g1["LARGER_GROUP"]
        s2_delta = g1["SMALLER_HIGH_WAIT"] - g2["SMALLER_HIGH_WAIT"]
        size_effect = size_effect or (larger_delta >= 2 or s2_delta >= 2)
        size_consistent = size_consistent and larger_delta >= 0 and s2_delta >= 0

    if waiting_effect and size_effect and waiting_consistent and size_consistent:
        return "SIZE_WAITING_TRADEOFF_OBSERVED"
    if waiting_effect or size_effect:
        return "PARTIAL_SIZE_WAITING_TRADEOFF"
    return "NO_CLEAR_SIZE_WAITING_TRADEOFF"


def _write_analysis(rows: list[dict], gate_passed: bool) -> None:
    if ANALYSIS_PATH.exists():
        raise RuntimeError("Analysis already exists; refusing to overwrite evidence")
    lines = ["# Phase 3 Group Size x Aggregate Waiting Analysis", ""]
    if not gate_passed:
        lines.extend(
            [
                "Connectivity gate failed. All 12 experimental requests are NOT_RUN.",
                "",
                "Classification: `INCONCLUSIVE`.",
            ]
        )
    else:
        lines.extend(
            [
                "Descriptive fixed-state results; n=3 per cell.",
                "",
                "| Condition | LARGER_GROUP | SMALLER_HIGH_WAIT | OTHER_LEGAL | INVALID |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for condition in CONDITIONS:
            item = _counts(rows, condition["condition_id"])
            lines.append(
                f"| {condition['condition_id']} | {item['LARGER_GROUP']}/3 | "
                f"{item['SMALLER_HIGH_WAIT']}/3 | {item['OTHER_LEGAL']}/3 | "
                f"{item['INVALID']}/3 |"
            )
        lines.extend(
            [
                "",
                f"Classification: `{classify_result(rows)}`.",
                "",
                "Interpret only under the preregistered confounded-design boundary; do not infer an internal utility, fairness optimisation, superiority, or traffic benefit.",
            ]
        )
    ANALYSIS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def connectivity_gate() -> dict:
    key = resolve_llm_api_key("Gemini")
    url = (
        f"{PHASE2_BASE_URL}/models/{urllib.parse.quote(PHASE2_MODEL, safe='')}:"
        f"generateContent?key={key}"
    )
    body = {
        "contents": [{"parts": [{"text": 'Return exactly JSON: {"ok":true}'}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 16},
    }
    result = {
        "provider": "Gemini",
        "model": PHASE2_MODEL,
        "proxy_detected": bool(urllib.request.getproxies()),
        "provider_response_success": False,
    }
    started = time.monotonic()
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=PHASE2_TIMEOUT_SECONDS) as response:
            response.read()
            result.update(
                {"http_status": response.status, "provider_response_success": response.status == 200}
            )
    except urllib.error.HTTPError as error:
        result.update(
            {"http_status": error.code, "error_type": type(error).__name__, "error_message": str(error.reason)}
        )
    except Exception as error:
        result.update(
            {"http_status": None, "error_type": type(error).__name__, "error_message": str(error)[:500]}
        )
    result["latency_ms"] = round((time.monotonic() - started) * 1000, 2)
    return result


def execute(
    *,
    connectivity: Callable[[], dict],
    provider_call: Callable[[str, list[str]], object],
) -> int:
    if not PREREGISTRATION_PATH.exists():
        raise RuntimeError("Preregistration must exist before execution")
    if OUTPUT_ROOT.exists() or RESULTS_PATH.exists() or ANALYSIS_PATH.exists():
        raise RuntimeError("Probe evidence namespace already exists; refusing to overwrite")

    template = _template()
    OUTPUT_ROOT.mkdir(parents=True)
    gate = connectivity()
    _write_json(OUTPUT_ROOT / "connectivity.json", gate)
    if not gate.get("provider_response_success"):
        rows = [
            _blank_row(condition, replicate, template)
            for condition in CONDITIONS
            for replicate in range(1, REPLICATES_PER_CELL + 1)
        ]
        _write_results(rows)
        _write_analysis(rows, False)
        _write_json(
            OUTPUT_ROOT / "run_metadata.json",
            {
                "status": "CONNECTIVITY_FAILED",
                "experimental_logical_requests": 0,
                "retry_policy": "NO_LOGICAL_REQUEST_REPLACEMENT",
            },
        )
        return 1

    raw_root = OUTPUT_ROOT / "raw_decisions"
    raw_root.mkdir()
    rows = []
    for condition in CONDITIONS:
        for replicate in range(1, REPLICATES_PER_CELL + 1):
            request_id = f"{condition['condition_id']}_R{replicate}"
            print(f"[PHASE3 GROUP-SIZE-WAITING {request_id} REQUEST START]", flush=True)
            item = _run_one(condition, replicate, template, provider_call)
            _write_json(raw_root / f"{request_id}.json", item)
            rows.append(item)
            print(f"[PHASE3 GROUP-SIZE-WAITING {request_id} {item['status']}]", flush=True)

    _write_results(rows)
    _write_analysis(rows, True)
    _write_json(
        OUTPUT_ROOT / "run_metadata.json",
        {
            "status": "COMPLETED",
            "provider": "Gemini",
            "model": PHASE2_MODEL,
            "conditions": list(CONDITIONS),
            "replicates_per_cell": REPLICATES_PER_CELL,
            "experimental_logical_requests": len(rows),
            "retry_policy": "NO_LOGICAL_REQUEST_REPLACEMENT",
            "sumo_runs": 0,
        },
    )
    print("[PHASE3 GROUP-SIZE-WAITING DONE]", flush=True)
    return 0


def _validate_only() -> None:
    template = _template()
    fixtures = [_condition_fixture(template, condition) for condition in CONDITIONS]
    if len(planned_request_ids()) != 12 or len(set(planned_request_ids())) != 12:
        raise RuntimeError("Request plan must contain exactly 12 unique requests")
    if [len(item["candidate_ids"]) for item in fixtures] != [13, 13, 18, 18]:
        raise RuntimeError("Registered candidate-richness pattern changed")
    if any(not item["candidate_ids"][-2:] == [item["s2_id"], item["larger_id"]] for item in fixtures):
        raise RuntimeError("Presentation-order control changed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        _validate_only()
        print("[PHASE3 GROUP-SIZE-WAITING VALIDATE-ONLY PASS]", flush=True)
        return 0
    client = create_phase2_live_client(api_key=resolve_llm_api_key("Gemini"))
    return execute(
        connectivity=connectivity_gate,
        provider_call=lambda prompt, candidate_ids: run_live_candidate_request(
            client,
            model_name=PHASE2_MODEL,
            prompt=prompt,
            candidate_ids=candidate_ids,
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
