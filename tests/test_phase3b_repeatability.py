from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_phase3b_repeatability.py"


def _module():
    spec = importlib.util.spec_from_file_location("phase3b_repeatability_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _response(candidate_id: str):
    return SimpleNamespace(
        provider_success=True,
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({"selected_candidate_id": candidate_id})) )],
    )


def _paths(module, tmp_path):
    module.OUTPUT_ROOT = tmp_path / "output"
    module.RESULTS_PATH = tmp_path / "results.csv"
    module.ANALYSIS_PATH = tmp_path / "analysis.md"


def test_registered_matrix_has_four_conditions_and_twenty_request_ids():
    module = _module()
    assert module.CONDITIONS == (("W08", 8.0), ("W19", 19.0), ("W20", 20.0), ("W24", 24.0))
    assert module.planned_request_ids() == tuple(f"{condition}_R{replicate}" for condition in ("W08", "W19", "W20", "W24") for replicate in range(1, 6))


def test_classifies_r4_s2_other_legal_and_illegal_without_sumo():
    module = _module(); _, states, groups, straight, right = module._template()
    candidate_ids = [item["candidate_id"] for item in module.build_candidate_selection_context(states, groups)[1]]
    assert module._classify("|".join(right), candidate_ids, straight, right, True) == "R4"
    assert module._classify("|".join(straight), candidate_ids, straight, right, True) == "S2"
    other = next(item for item in candidate_ids if item not in {"|".join(right), "|".join(straight)})
    assert module._classify(other, candidate_ids, straight, right, True) == "OTHER_LEGAL"
    assert module._classify("illegal", candidate_ids, straight, right, True) == "INVALID"


def test_exactly_one_logical_call_per_replicate_and_invalid_is_retained(tmp_path):
    module = _module(); _paths(module, tmp_path); calls = []
    def provider(_prompt, candidate_ids):
        calls.append(candidate_ids)
        return _response("illegal" if len(calls) == 1 else candidate_ids[-1])
    assert module.execute(connectivity=lambda: {"provider_response_success": True}, provider_call=provider) == 0
    assert len(calls) == 20
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert len(rows) == 20 and rows[0]["status"] == "INVALID" and rows[0]["selection_class"] == "INVALID"


def test_failed_connectivity_marks_all_requests_not_run_without_provider_call(tmp_path):
    module = _module(); _paths(module, tmp_path); calls = 0
    def provider(_prompt, _candidate_ids):
        nonlocal calls; calls += 1; raise AssertionError("must not be called")
    assert module.execute(connectivity=lambda: {"provider_response_success": False}, provider_call=provider) == 1
    assert calls == 0
    rows = list(csv.DictReader(module.RESULTS_PATH.open(encoding="utf-8")))
    assert len(rows) == 20 and {row["status"] for row in rows} == {"NOT_RUN"}
