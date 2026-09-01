from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_phase3_group_size_waiting_probe.py"


def _module():
    spec = importlib.util.spec_from_file_location("phase3_group_size_waiting_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _response(candidate_id: str):
    return SimpleNamespace(
        provider_success=True,
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps({"selected_candidate_id": candidate_id})
                )
            )
        ],
    )


def _paths(module, tmp_path):
    module.PREREGISTRATION_PATH = Path(__file__)
    module.OUTPUT_ROOT = tmp_path / "output"
    module.RESULTS_PATH = tmp_path / "results.csv"
    module.ANALYSIS_PATH = tmp_path / "analysis.md"


def test_exact_registered_matrix_and_request_count():
    module = _module()
    assert tuple(
        (item["condition_id"], item["group_size_advantage"], item["waiting_regime"], item["s2_waiting"])
        for item in module.CONDITIONS
    ) == (
        ("G1_LOW", 1, "LOW", 8.0),
        ("G1_HIGH", 1, "HIGH", 20.0),
        ("G2_LOW", 2, "LOW", 8.0),
        ("G2_HIGH", 2, "HIGH", 20.0),
    )
    assert module.REPLICATES_PER_CELL == 3
    assert len(module.planned_request_ids()) == 12
    assert len(set(module.planned_request_ids())) == 12


def test_group_size_waiting_controls_legality_and_order():
    module = _module()
    template = module._template()
    fixtures = {
        item["condition_id"]: module._condition_fixture(template, item)
        for item in module.CONDITIONS
    }
    assert [len(fixtures[name]["candidate_ids"]) for name in fixtures] == [13, 13, 18, 18]
    for condition in module.CONDITIONS:
        fixture = fixtures[condition["condition_id"]]
        assert fixture["larger_id"] in fixture["candidate_ids"]
        assert fixture["s2_id"] in fixture["candidate_ids"]
        assert fixture["candidate_ids"][-2:] == [fixture["s2_id"], fixture["larger_id"]]
        assert fixture["larger_feature"]["group_size"] - fixture["s2_feature"]["group_size"] == condition["group_size_advantage"]
        assert fixture["larger_feature"]["aggregate_waiting_time"] == 0.0
        assert fixture["s2_feature"]["aggregate_waiting_time"] == condition["s2_waiting"]
        assert {item["movement"] for item in fixture["larger_feature"]["movement_summary"]} == {"RIGHT"}
        assert [item["movement"] for item in fixture["s2_feature"]["movement_summary"]] == ["STRAIGHT", "STRAIGHT"]
        assert fixture["larger_feature"]["minimum_time_to_intersection"] is None
        assert fixture["s2_feature"]["minimum_time_to_intersection"] is None


def test_only_registered_state_fields_change():
    module = _module()
    template = module._template()
    by_condition = {
        item["condition_id"]: module._condition_fixture(template, item)
        for item in module.CONDITIONS
    }
    for prefix in ("G1", "G2"):
        low = {item["vehicle_id"]: item for item in by_condition[f"{prefix}_LOW"]["states"]}
        high = {item["vehicle_id"]: item for item in by_condition[f"{prefix}_HIGH"]["states"]}
        assert low.keys() == high.keys()
        s2 = set(template["s2"])
        for vehicle_id in low:
            if vehicle_id in s2:
                assert low[vehicle_id]["waiting_time"] == 4.0
                assert high[vehicle_id]["waiting_time"] == 10.0
                left = dict(low[vehicle_id]); right = dict(high[vehicle_id])
                left.pop("waiting_time"); right.pop("waiting_time")
                assert left == right
            else:
                assert low[vehicle_id] == high[vehicle_id]

    g1 = {item["vehicle_id"]: item for item in by_condition["G1_LOW"]["states"]}
    g2 = {item["vehicle_id"]: item for item in by_condition["G2_LOW"]["states"]}
    assert set(g2) - set(g1) == {template["omitted_for_g1"]}
    for vehicle_id in g1:
        assert g1[vehicle_id] == g2[vehicle_id]


def test_one_call_per_request_prompt_hash_invalid_retention_and_source_untouched(tmp_path):
    module = _module()
    _paths(module, tmp_path)
    calls = []
    source_hash = hashlib.sha256(module.SOURCE.read_bytes()).hexdigest()

    def provider(_prompt, candidate_ids):
        calls.append(candidate_ids)
        return _response("illegal" if len(calls) == 1 else candidate_ids[-1])

    assert module.execute(
        connectivity=lambda: {"provider_response_success": True},
        provider_call=provider,
    ) == 0
    assert len(calls) == 12
    assert hashlib.sha256(module.SOURCE.read_bytes()).hexdigest() == source_hash
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert len(rows) == 12
    assert rows[0]["status"] == "INVALID" and rows[0]["selection_class"] == "INVALID"
    assert all(row["prompt_hash"] for row in rows)
    assert all(row["candidate_set_hash"] for row in rows)
    assert all(row["candidate_presentation_hash"] for row in rows)
    assert all(row["input_state_hash"] for row in rows)
    assert all(row["request_attempt_count"] == "1" for row in rows)
    assert len(list((module.OUTPUT_ROOT / "raw_decisions").glob("*.json"))) == 12


def test_connectivity_failure_marks_all_not_run_without_experimental_call(tmp_path):
    module = _module()
    _paths(module, tmp_path)
    calls = 0

    def provider(_prompt, _candidate_ids):
        nonlocal calls
        calls += 1
        raise AssertionError("experimental provider must not be called")

    assert module.execute(
        connectivity=lambda: {"provider_response_success": False},
        provider_call=provider,
    ) == 1
    assert calls == 0
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert len(rows) == 12
    assert {row["status"] for row in rows} == {"NOT_RUN"}


def test_preregistered_classification_rules():
    module = _module()

    def rows(mapping):
        result = []
        for condition, selections in mapping.items():
            result.extend(
                {"condition_id": condition, "selection_class": selection}
                for selection in selections
            )
        return result

    full = rows(
        {
            "G1_LOW": ["LARGER_GROUP"] * 3,
            "G1_HIGH": ["SMALLER_HIGH_WAIT"] * 3,
            "G2_LOW": ["LARGER_GROUP"] * 3,
            "G2_HIGH": ["LARGER_GROUP"] * 2 + ["SMALLER_HIGH_WAIT"],
        }
    )
    assert module.classify_result(full) == "SIZE_WAITING_TRADEOFF_OBSERVED"

    waiting_only = rows(
        {
            "G1_LOW": ["LARGER_GROUP"] * 3,
            "G1_HIGH": ["SMALLER_HIGH_WAIT"] * 3,
            "G2_LOW": ["LARGER_GROUP"] * 3,
            "G2_HIGH": ["SMALLER_HIGH_WAIT"] * 3,
        }
    )
    assert module.classify_result(waiting_only) == "PARTIAL_SIZE_WAITING_TRADEOFF"

    inconclusive = rows(
        {
            "G1_LOW": ["INVALID", "INVALID", "LARGER_GROUP"],
            "G1_HIGH": ["SMALLER_HIGH_WAIT"] * 3,
            "G2_LOW": ["LARGER_GROUP"] * 3,
            "G2_HIGH": ["SMALLER_HIGH_WAIT"] * 3,
        }
    )
    assert module.classify_result(inconclusive) == "INCONCLUSIVE"


def test_runner_has_no_sumo_dependency_or_retry_loop():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "import traci" not in source
    assert "sumolib" not in source
    assert "subprocess" not in source
    assert "while " not in source
    assert "REPLICATES_PER_CELL = 3" in source
