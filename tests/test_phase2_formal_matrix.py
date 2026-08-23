from __future__ import annotations

from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.phase2_formal_matrix import (
    FORMAL_MATRIX_CONDITIONS,
    build_extended_paired_comparison,
    build_remaining_matrix_plan,
    extract_complete_disagreements,
    summarize_paired_deltas,
)


def _summary(planner: str, seed: int, waiting: float) -> dict:
    return {
        "run_id": f"run-{planner}-{seed}",
        "scenario_class": "S4_FAIRNESS_PRESSURE",
        "vehicle_count": 8,
        "seed": seed,
        "planner": planner,
        "initial_demand_signature": f"signature-{seed}",
        "completion_rate": 1.0,
        "throughput": 8,
        "mean_waiting_time": waiting,
        "maximum_waiting_time": waiting + 2,
        "mean_speed": 7.0,
        "episode_duration_seconds": 42.0,
        "collision_count": 0,
        "safety_intervention_count": 0,
        "fallback_count": 0,
        "gemini_request_count": 3,
        "agreement_count": 3,
        "disagreement_count": 0,
        "total_tokens": 10,
    }


def test_remaining_matrix_plan_is_exactly_thirty_runs_and_fifteen_pairs():
    plan = build_remaining_matrix_plan()

    assert len(plan) == 30
    assert len({spec.run_id for spec in plan}) == 30
    assert [spec.order for spec in plan] == list(range(1, 31))
    assert sum(spec.planner_mode == GEMINI_CANDIDATE for spec in plan) == 15
    assert sum(spec.planner_mode == DETERMINISTIC_CANDIDATE for spec in plan) == 15
    assert len({spec.pair_id for spec in plan}) == 15
    assert FORMAL_MATRIX_CONDITIONS[1] == ("S2_SIMULTANEOUS_CONFLICT", 8, (1, 2, 3))


def test_extended_paired_comparison_and_condition_delta_summary_include_safety_metrics():
    rows = [
        _summary(DETERMINISTIC_CANDIDATE, 1, 3.0),
        _summary(GEMINI_CANDIDATE, 1, 4.5),
        _summary(DETERMINISTIC_CANDIDATE, 2, 2.0),
        _summary(GEMINI_CANDIDATE, 2, 2.0),
    ]

    comparisons = build_extended_paired_comparison(rows)
    summaries = summarize_paired_deltas(comparisons)

    assert comparisons[0]["collision_delta"] == 0
    assert comparisons[0]["safety_intervention_delta"] == 0
    assert comparisons[0]["maximum_waiting_time_delta"] == 1.5
    assert summaries[0]["mean_waiting_time_delta"]["n"] == 2
    assert summaries[0]["mean_waiting_time_delta"]["mean"] == 0.75


def test_complete_disagreement_record_has_fairness_and_grant_context():
    result = {
        "run_id": "gemini-run",
        "initial_conditions": {
            "scenario_class": "S4_FAIRNESS_PRESSURE",
            "vehicle_count": 8,
            "seed": 1,
        },
        "decision_records": [
            {
                "candidate_disagreement": True,
                "simulation_time": 5.0,
                "candidate_set": ["a", "b"],
                "candidate_features": [
                    {"candidate_id": "a", "group_size": 1},
                    {"candidate_id": "b", "group_size": 2},
                ],
                "deterministic_candidate_id": "a",
                "llm_candidate_id": "b",
                "privacy_minimised_vehicle_inputs": [
                    {
                        "incoming_edge": "N",
                        "outgoing_edge": "-E",
                        "waiting_time": 6.0,
                        "time_to_intersection": 1.5,
                    }
                ],
                "fallback_used": False,
                "fallback_reason": "",
                "safety_interventions_during_grant": 0,
                "grant_vehicle_ids": ["vehicle-1"],
                "grant_clearance_reason": "ALL_GRANTED_VEHICLES_LEFT_CONTROL_SCOPE",
                "grant_duration_seconds": 4.0,
            }
        ],
    }

    disagreement = extract_complete_disagreements([result])[0]

    assert disagreement["candidate_group_sizes"] == [1, 2]
    assert disagreement["fairness_pressure_context"] is True
    assert disagreement["fairness_target_waiting_time"] == 6.0
    assert disagreement["actual_granted_group"] == ["vehicle-1"]
