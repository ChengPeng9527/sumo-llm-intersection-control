import copy
import json
from pathlib import Path

import pytest

from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.phase3c_closed_loop import (
    PHASE3C_CONDITIONS,
    STAGE_DETERMINISTIC,
    STAGE_GEMINI,
    build_phase3c_plan,
    build_final_comparison,
    observe_decision_epoch,
    observe_episode,
    require_stage2_authorization,
    stage1_feasibility,
)
from scripts.run_phase3c_closed_loop import inspect_stage1_output_root


RIGHT_ID = "right-1|right-2|right-3|right-4"
STRAIGHT_ID = "straight-n|straight-s"


def _record(*, disagreement=False):
    return {
        "run_id": "phase3c-test", "planner": GEMINI_CANDIDATE, "decision_epoch": 3, "simulation_time": 21.0,
        "deterministic_candidate_id": RIGHT_ID, "llm_candidate_id": STRAIGHT_ID if disagreement else RIGHT_ID,
        "candidate_agreement": not disagreement, "candidate_disagreement": disagreement,
        "provider_request_success": True, "parser_success": True, "fallback_used": False, "latency_ms": 12.0,
        "candidate_features": [
            {"candidate_id": RIGHT_ID, "vehicle_ids": ["right-1", "right-2", "right-3", "right-4"], "group_size": 4, "aggregate_waiting_time": 8.0, "maximum_waiting_time": 5.0, "movement_summary": [{"movement": "RIGHT", "incoming_edge": edge} for edge in ("N", "E", "S", "W")]},
            {"candidate_id": STRAIGHT_ID, "vehicle_ids": ["straight-n", "straight-s"], "group_size": 2, "aggregate_waiting_time": 20.0, "maximum_waiting_time": 10.0, "movement_summary": [{"movement": "STRAIGHT", "incoming_edge": "N"}, {"movement": "STRAIGHT", "incoming_edge": "S"}]},
        ],
    }


def test_observer_detects_target_tradeoff_without_mutating_controller_record():
    record = _record(disagreement=True)
    original = copy.deepcopy(record)
    observed = observe_decision_epoch(record)
    assert record == original
    assert observed["candidate_count"] == 2
    assert observed["eligible_tradeoff_epoch"] is True
    assert observed["waiting_contrast_straight_minus_right"] == 12.0
    assert observed["target_tradeoff_disagreement"] is True


def test_observer_uses_vehicle_maximum_waiting_for_sample_sd_and_approaches():
    observation = observe_episode(
        [_record()],
        {"run_id": "phase3c-test", "planner_mode": DETERMINISTIC_CANDIDATE, "mean_speed": 7.0, "episode_duration_seconds": 30.0, "throughput": 2, "completion_rate": 1.0, "collision_count": 0, "safety_intervention_count": 0, "grant_timeout_count": 0},
        [
            {"vehicle_id": "a", "incoming_edge": "N", "waiting_time": "2"},
            {"vehicle_id": "a", "incoming_edge": "N", "waiting_time": "3"},
            {"vehicle_id": "b", "incoming_edge": "S", "waiting_time": "7"},
        ],
    )
    assert observation["waiting_mean_observed"] == 5.0
    assert observation["waiting_max_observed"] == 7.0
    assert observation["waiting_sample_sd_observed"] == pytest.approx(2.8284271247)
    assert observation["per_approach_waiting"]["N"]["mean"] == 3.0
    assert observation["per_approach_waiting"]["S"]["maximum"] == 7.0


def test_stage1_plan_is_deterministic_only_and_stage2_is_explicit_gemini_only():
    stage1 = build_phase3c_plan(STAGE_DETERMINISTIC)
    stage2 = build_phase3c_plan(STAGE_GEMINI)
    assert len(stage1) == len(stage2) == 6
    assert all(spec.planner_mode == DETERMINISTIC_CANDIDATE for spec in stage1)
    assert all(spec.planner_mode == GEMINI_CANDIDATE for spec in stage2)
    assert [(spec.condition.name, spec.seed) for spec in stage1] == [(spec.condition.name, spec.seed) for spec in stage2]


def test_stage2_requires_human_approval_and_preregistered_state_gate():
    with pytest.raises(PermissionError):
        require_stage2_authorization(stage1_report={"stage1_gate_passed": True}, explicitly_approved=False)
    with pytest.raises(RuntimeError):
        require_stage2_authorization(stage1_report={"stage1_gate_passed": False}, explicitly_approved=True)


def test_stage1_gate_uses_state_emergence_not_selection_or_traffic_performance():
    observations = []
    for condition in PHASE3C_CONDITIONS:
        for seed in (1, 2, 3):
            observations.append({
                "condition": condition.name, "seed": seed, "eligible_tradeoff_epoch_count": 1,
                "first_eligible_waiting_contrast": 10.0 if condition.name == "MODERATE_WAITING_PRESSURE" else 12.0,
                "planner_disagreement_count": 99, "throughput": 0,
            })
    report = stage1_feasibility(observations)
    assert report["stage1_gate_passed"] is True
    assert report["criterion"]["selection_or_traffic_outcomes_used"] is False


def test_strict_invalid_gemini_episode_is_visible_for_exclusion():
    observation = observe_episode([], {"planner_mode": GEMINI_CANDIDATE, "llm_episode_valid": False}, [])
    assert observation["llm_episode_valid"] is False


def test_phase3c_output_namespace_and_final_comparison_do_not_reference_frozen_evidence():
    stage1 = {"condition": "MODERATE_WAITING_PRESSURE", "seed": 1, "planner": DETERMINISTIC_CANDIDATE, "eligible_tradeoff_epoch_count": 1}
    stage2 = {"condition": "MODERATE_WAITING_PRESSURE", "seed": 1, "planner": GEMINI_CANDIDATE, "llm_episode_valid": False, "target_tradeoff_disagreement_count": 0}
    rows = build_final_comparison([stage1, stage2])
    assert len(rows) == 1
    assert rows[0]["gemini_llm_episode_valid"] is False
    assert all("phase2" not in spec.run_id for spec in build_phase3c_plan(STAGE_DETERMINISTIC))


def test_stage1_allows_an_empty_or_known_pre_sumo_bootstrap_root(tmp_path: Path):
    root = tmp_path / "phase3c"
    root.mkdir()
    assert inspect_stage1_output_root(root)[:2] == (True, "empty_root")
    (root / "deterministic-feasibility_manifest.json").write_text(json.dumps({
        "extension_id": "phase3c_closed_loop_waiting_divergence",
        "stage": "deterministic-feasibility",
        "status": "invalid",
        "runs": [],
        "failed_run": {"error_type": "KeyError", "error": "'initial_demand_signature'"},
    }), encoding="utf-8")
    allowed, reason, preserved = inspect_stage1_output_root(root)
    assert allowed is True and reason == "known_pre_sumo_bootstrap_failure"
    assert preserved["runs"] == []


@pytest.mark.parametrize("path", ["runs/seed1/summary.json", "stage1_feasibility_report.json", "unknown.txt"])
def test_stage1_rejects_completed_partial_or_ambiguous_evidence(tmp_path: Path, path: str):
    root = tmp_path / "phase3c"
    target = root / path
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")
    allowed, _, _ = inspect_stage1_output_root(root)
    assert allowed is False
