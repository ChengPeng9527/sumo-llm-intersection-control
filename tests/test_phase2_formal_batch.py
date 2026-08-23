from __future__ import annotations

from copy import deepcopy

from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.phase2_formal_batch import (
    FORMAL_SCENARIOS,
    build_paired_comparison,
    build_phase2_formal_batch_plan,
    extract_disagreements,
    validate_formal_pair,
)


def _result(planner: str, run_id: str) -> dict:
    return {
        "run_id": run_id,
        "initial_conditions": {
            "scenario_id": "phase2_s1_balanced_mixed_turn_v8_seed1",
            "scenario_class": "S1_BALANCED_MIXED_TURN",
            "vehicle_count": 8,
            "seed": 1,
            "route_sequence": ["N_W", "E_W"],
            "departure_times": [0, 3],
            "movement_sequence": ["RIGHT", "STRAIGHT"],
            "seed_semantics": {"route_assignment_changes": False},
            "initial_demand_signature": "shared-signature",
        },
        "artifact_paths": {"run_dir": f"results/raw/{run_id}"},
        "summary": {"planner_mode": planner},
        "decision_records": [],
    }


def test_formal_batch_plan_is_exactly_six_independent_paired_runs():
    plan = build_phase2_formal_batch_plan()

    assert len(plan) == 6
    assert [spec.order for spec in plan] == list(range(1, 7))
    assert [spec.scenario_class for spec in plan[::2]] == list(FORMAL_SCENARIOS)
    assert [spec.planner_mode for spec in plan] == [
        DETERMINISTIC_CANDIDATE,
        GEMINI_CANDIDATE,
    ] * 3
    assert {spec.vehicle_count for spec in plan} == {8}
    assert {spec.seed for spec in plan} == {1}
    assert len({spec.run_id for spec in plan}) == 6


def test_formal_pair_requires_matching_initial_conditions_and_independent_outputs():
    deterministic = _result(DETERMINISTIC_CANDIDATE, "deterministic-run")
    gemini = _result(GEMINI_CANDIDATE, "gemini-run")

    assert validate_formal_pair(deterministic, gemini) == []

    mismatched = deepcopy(gemini)
    mismatched["initial_conditions"]["departure_times"] = [0, 4]
    assert "paired_initial_condition_mismatch:departure_times" in validate_formal_pair(
        deterministic,
        mismatched,
    )

    colliding = deepcopy(gemini)
    colliding["run_id"] = deterministic["run_id"]
    colliding["artifact_paths"]["run_dir"] = deterministic["artifact_paths"]["run_dir"]
    errors = validate_formal_pair(deterministic, colliding)
    assert "paired_runs_not_independent" in errors
    assert "paired_artifact_directory_collision" in errors


def test_paired_comparison_uses_gemini_minus_deterministic_deltas():
    common = {
        "scenario_class": "S1_BALANCED_MIXED_TURN",
        "vehicle_count": 8,
        "seed": 1,
        "initial_demand_signature": "shared-signature",
        "completion_rate": 1.0,
        "maximum_waiting_time": 8.0,
        "collision_count": 0,
        "safety_intervention_count": 0,
        "fallback_count": 0,
        "gemini_request_count": 0,
        "agreement_count": 0,
        "disagreement_count": 0,
        "total_tokens": 0,
    }
    deterministic = {
        **common,
        "run_id": "deterministic-run",
        "planner": DETERMINISTIC_CANDIDATE,
        "throughput": 8,
        "mean_waiting_time": 4.0,
        "mean_speed": 6.0,
        "episode_duration_seconds": 20.0,
    }
    gemini = {
        **common,
        "run_id": "gemini-run",
        "planner": GEMINI_CANDIDATE,
        "throughput": 8,
        "mean_waiting_time": 5.5,
        "mean_speed": 5.5,
        "episode_duration_seconds": 22.0,
    }

    comparison = build_paired_comparison([deterministic, gemini])[0]

    assert comparison["initial_demand_signature_match"] is True
    assert comparison["mean_waiting_time_delta"] == 1.5
    assert comparison["mean_speed_delta"] == -0.5
    assert comparison["episode_duration_delta_seconds"] == 2.0


def test_disagreement_extraction_keeps_decision_context():
    result = _result(GEMINI_CANDIDATE, "gemini-run")
    result["decision_records"] = [
        {
            "simulation_time": 4.0,
            "candidate_disagreement": True,
            "candidate_set": ["candidate_1", "candidate_2"],
            "deterministic_candidate_id": "candidate_1",
            "llm_candidate_id": "candidate_2",
            "candidate_features": [{"candidate_id": "candidate_1"}],
            "privacy_minimised_vehicle_inputs": [
                {"vehicle_id": "veh_0", "waiting_time": 7.0}
            ],
            "safety_interventions_during_grant": 0,
            "grant_clearance_reason": "ALL_GRANTED_VEHICLES_LEFT_CONTROL_SCOPE",
            "grant_duration_seconds": 3.0,
        },
        {"candidate_disagreement": False},
    ]

    disagreements = extract_disagreements([result])

    assert len(disagreements) == 1
    assert disagreements[0]["maximum_waiting_time"] == 7.0
    assert disagreements[0]["deterministic_candidate_id"] == "candidate_1"
    assert disagreements[0]["gemini_candidate_id"] == "candidate_2"
