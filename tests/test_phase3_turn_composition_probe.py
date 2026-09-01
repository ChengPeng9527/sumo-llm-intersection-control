from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_phase3_turn_composition_probe.py"


def _module():
    spec = importlib.util.spec_from_file_location("phase3_turn_composition_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _response(candidate_id: str):
    return SimpleNamespace(provider_success=True, choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"selected_candidate_id": candidate_id})) )])


def _paths(module, tmp_path):
    module.OUTPUT_ROOT = tmp_path / "output"; module.RESULTS_PATH = tmp_path / "results.csv"; module.ANALYSIS_PATH = tmp_path / "analysis.md"


def test_registered_matrix_has_two_counterbalanced_orders_and_ten_requests():
    module = _module()
    assert module.CONDITIONS == ("RIGHT_TARGET_FIRST", "STRAIGHT_TARGET_FIRST")
    assert len(module.planned_request_ids()) == 10


def test_targets_are_legal_and_matched_except_for_route_turn_identity():
    module = _module(); _, states, groups, right, straight = module._template(); normalised = module._normalised_states(states, right, straight)
    for condition in module.CONDITIONS:
        _, features, _ = module.build_candidate_selection_context(normalised, module._ordered_groups(groups, right, straight, condition))
        by_id = {item["candidate_id"]: item for item in features}; r, s = by_id["|".join(right)], by_id["|".join(straight)]
        assert (r["group_size"], r["aggregate_waiting_time"], r["maximum_waiting_time"], r["minimum_time_to_intersection"]) == (s["group_size"], s["aggregate_waiting_time"], s["maximum_waiting_time"], s["minimum_time_to_intersection"])
        assert {item["movement"] for item in r["movement_summary"]} == {"RIGHT"}
        assert {item["movement"] for item in s["movement_summary"]} == {"STRAIGHT"}


def test_presentation_order_is_counterbalanced_without_changing_candidate_set_or_state():
    module = _module(); _, states, groups, right, straight = module._template(); normalised = module._normalised_states(states, right, straight)
    first = module._ordered_groups(groups, right, straight, "RIGHT_TARGET_FIRST"); second = module._ordered_groups(groups, right, straight, "STRAIGHT_TARGET_FIRST")
    assert module._sha256_json(sorted(tuple(group) for group in first)) == module._sha256_json(sorted(tuple(group) for group in second))
    assert module._sha256_json(first) != module._sha256_json(second)
    assert module._sha256_json(module.build_candidate_selection_context(normalised, first)[0]) == module._sha256_json(module.build_candidate_selection_context(normalised, second)[0])


def test_one_request_per_replicate_prompt_hash_and_invalid_retention(tmp_path):
    module = _module(); _paths(module, tmp_path); calls = 0
    def provider(_prompt, candidate_ids):
        nonlocal calls; calls += 1
        return _response("illegal" if calls == 1 else candidate_ids[0])
    assert module.execute(connectivity=lambda: {"provider_response_success": True}, provider_call=provider) == 0
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert calls == 10 == len(rows) and rows[0]["selection_class"] == "INVALID"
    assert all(row["prompt_hash"] for row in rows)


def test_connectivity_failure_leaves_all_experimental_requests_not_run(tmp_path):
    module = _module(); _paths(module, tmp_path); calls = 0
    def provider(_prompt, _candidate_ids):
        nonlocal calls; calls += 1; raise AssertionError("must not call provider")
    assert module.execute(connectivity=lambda: {"provider_response_success": False}, provider_call=provider) == 1
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert calls == 0 and len(rows) == 10 and {row["status"] for row in rows} == {"NOT_RUN"}
