from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_phase3_waiting_distribution_probe.py"


def _module():
    spec = importlib.util.spec_from_file_location("phase3_waiting_distribution_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _response(candidate_id: str):
    return SimpleNamespace(
        provider_success=True,
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"selected_candidate_id": candidate_id})))],
    )


def _paths(module, tmp_path):
    module.OUTPUT_ROOT = tmp_path / "output"
    module.RESULTS_PATH = tmp_path / "results.csv"
    module.ANALYSIS_PATH = tmp_path / "analysis.md"


def test_registered_conditions_are_exact_and_have_fixed_aggregate_waiting():
    module = _module()
    assert module.CONDITIONS == (("BALANCED", (10.0, 10.0)), ("MODERATELY_SKEWED", (7.0, 13.0)), ("HIGHLY_SKEWED", (2.0, 18.0)))
    assert len(module.planned_request_ids()) == 15
    assert all(sum(distribution) == module.FIXED_AGGREGATE_WAITING for _, distribution in module.CONDITIONS)


def test_only_target_individual_waiting_changes_and_candidate_set_remains_identical():
    module = _module()
    _, base_states, groups, straight, _ = module._template()
    reference = {item["vehicle_id"]: item for item in base_states}
    hashes = set()
    state_hashes = set()
    for _, distribution in module.CONDITIONS:
        states = module._states_for_distribution(base_states, straight, distribution)
        current = {item["vehicle_id"]: item for item in states}
        for vehicle_id, item in current.items():
            if vehicle_id in straight:
                assert item["waiting_time"] in distribution
            else:
                assert item == reference[vehicle_id]
        local_state, features, _ = module.build_candidate_selection_context(states, groups)
        assert sum(item["waiting_time"] for item in local_state if item["vehicle_id"] in straight) == 20.0
        assert len(features) == 18
        hashes.add(module._sha256_json(groups))
        state_hashes.add(module._sha256_json(local_state))
    assert len(hashes) == 1
    assert len(state_hashes) == 3


def test_one_request_per_registered_replicate_and_prompt_hash_is_nonempty(tmp_path):
    module = _module()
    _paths(module, tmp_path)
    calls = []

    def provider(prompt, candidate_ids):
        calls.append(prompt)
        return _response(candidate_ids[-1])

    assert module.execute(connectivity=lambda: {"provider_response_success": True}, provider_call=provider) == 0
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert len(calls) == 15 == len(rows)
    assert all(row["prompt_hash"] for row in rows)
    assert len({row["candidate_set_hash"] for row in rows}) == 1
    assert len({row["input_state_hash"] for row in rows}) == 3


def test_invalid_response_is_retained_without_replacement(tmp_path):
    module = _module()
    _paths(module, tmp_path)
    calls = 0

    def provider(_prompt, candidate_ids):
        nonlocal calls
        calls += 1
        return _response("illegal" if calls == 1 else candidate_ids[0])

    assert module.execute(connectivity=lambda: {"provider_response_success": True}, provider_call=provider) == 0
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert calls == 15
    assert rows[0]["status"] == "INVALID"
    assert rows[0]["selection_class"] == "INVALID"


def test_connectivity_failure_marks_all_requests_not_run_without_provider_call(tmp_path):
    module = _module()
    _paths(module, tmp_path)
    calls = 0

    def provider(_prompt, _candidate_ids):
        nonlocal calls
        calls += 1
        raise AssertionError("provider must not be called")

    assert module.execute(connectivity=lambda: {"provider_response_success": False}, provider_call=provider) == 1
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert calls == 0
    assert len(rows) == 15
    assert {row["status"] for row in rows} == {"NOT_RUN"}
