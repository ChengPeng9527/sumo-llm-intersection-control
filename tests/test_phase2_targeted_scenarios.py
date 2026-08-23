from __future__ import annotations

from src.controllers.decision_pipeline import execute_cooperative_comparator_pipeline
from src.experiments import scenario_generator
from src.experiments.phase2_targeted_pilot import build_candidate_observation, summarize_candidate_observations
from src.experiments.phase2_closed_loop import initial_condition_record
from src.safety.candidate_groups import build_safe_candidate_groups
from src.safety.route_semantics import describe_route_id, supported_route_ids


SCENARIOS = (
    "S1_BALANCED_MIXED_TURN",
    "S2_SIMULTANEOUS_CONFLICT",
    "S3_COOPERATIVE_OPPORTUNITY",
    "S4_FAIRNESS_PRESSURE",
)


def _generate(monkeypatch, tmp_path, scenario_class, vehicle_count=8, seed=7, suffix="a"):
    monkeypatch.setattr(scenario_generator, "GENERATED_ROOT", tmp_path)
    return scenario_generator.generate_targeted_scenario(
        f"pytest_{scenario_class.lower()}_{suffix}",
        scenario_class,
        seed,
        vehicle_count,
    )


def _states(generation, *, fairness_wait=0.0):
    states = []
    for index, route_id in enumerate(generation["route_sequence"]):
        semantics = describe_route_id(route_id)
        waiting_time = fairness_wait if route_id == generation.get("fairness_target_route") else 0.5
        states.append(
            {
                "vehicle_id": f"vehicle_{index}",
                "route_id": route_id,
                "incoming_edge": semantics.incoming_edge,
                "outgoing_edge": semantics.outgoing_edge,
                "movement": semantics.movement,
                "speed": 4.0,
                "distance_to_intersection": 8.0 + index,
                "time_to_intersection": 2.0 + index * 0.1,
                "waiting_time": waiting_time,
                "inside_control_zone": True,
            }
        )
    return states


def test_s1_generation_is_reproducible_and_balanced(monkeypatch, tmp_path):
    first = _generate(monkeypatch, tmp_path, "S1_BALANCED_MIXED_TURN", suffix="first")
    second = _generate(monkeypatch, tmp_path, "S1_BALANCED_MIXED_TURN", suffix="second")

    assert first["route_sequence"] == second["route_sequence"]
    assert first["departure_times"] == second["departure_times"]
    assert {route.split("_", 1)[0] for route in first["route_sequence"]} == {"N", "E", "S", "W"}
    assert set(first["movement_sequence"]) == {"LEFT", "STRAIGHT", "RIGHT"}


def test_s2_departures_are_clustered_without_same_approach_overlap(monkeypatch, tmp_path):
    generation = _generate(monkeypatch, tmp_path, "S2_SIMULTANEOUS_CONFLICT")
    departures = generation["departure_times"]

    assert max(departures) - min(departures) <= 3
    by_approach: dict[str, list[int]] = {}
    for route_id, departure in zip(generation["route_sequence"], departures):
        by_approach.setdefault(route_id.split("_", 1)[0], []).append(departure)
    assert all(len(values) == len(set(values)) for values in by_approach.values())


def test_s2_eta_simultaneity_requires_two_finite_values():
    states = [
        {
            "vehicle_id": "a",
            "route_id": "N_S",
            "incoming_edge": "N",
            "outgoing_edge": "-S",
            "movement": "STRAIGHT",
            "speed": 0.0,
            "distance_to_intersection": 20.0,
            "time_to_intersection": float("inf"),
            "waiting_time": 3.0,
            "inside_control_zone": True,
        },
        {
            "vehicle_id": "b",
            "route_id": "E_W",
            "incoming_edge": "E",
            "outgoing_edge": "-W",
            "movement": "STRAIGHT",
            "speed": 0.0,
            "distance_to_intersection": 20.0,
            "time_to_intersection": float("inf"),
            "waiting_time": 2.0,
            "inside_control_zone": True,
        },
    ]
    groups = [["a"], ["b"]]
    trace = execute_cooperative_comparator_pipeline(states, groups)
    unavailable = build_candidate_observation(
        scenario_class="S2_SIMULTANEOUS_CONFLICT",
        simulation_step=1,
        vehicle_states=states,
        candidate_groups=groups,
        trace=trace,
    )
    states[1]["time_to_intersection"] = 2.5
    states[0]["time_to_intersection"] = 2.0
    available = build_candidate_observation(
        scenario_class="S2_SIMULTANEOUS_CONFLICT",
        simulation_step=2,
        vehicle_states=states,
        candidate_groups=groups,
        trace=trace,
    )

    assert unavailable["eta_simultaneity_available"] is False
    assert unavailable["arrival_tti_spread"] is None
    assert available["eta_simultaneity_available"] is True
    assert available["arrival_tti_spread"] == 0.5


def test_s3_contains_competing_compatible_mixed_turn_groups(monkeypatch, tmp_path):
    generation = _generate(monkeypatch, tmp_path, "S3_COOPERATIVE_OPPORTUNITY")
    states = _states(generation)
    groups = build_safe_candidate_groups(states)

    assert len(groups) > 1
    assert max(map(len, groups)) >= 4
    assert len([group for group in groups if len(group) > 1]) >= 2
    assert {state["movement"] for state in states} == {"LEFT", "STRAIGHT", "RIGHT"}


def test_s4_encodes_waiting_pressure_against_a_larger_legal_group(monkeypatch, tmp_path):
    generation = _generate(monkeypatch, tmp_path, "S4_FAIRNESS_PRESSURE")
    threshold = generation["intended_waiting_pressure_seconds"]
    states = _states(generation, fairness_wait=threshold + 2)
    groups = build_safe_candidate_groups(states)
    trace = execute_cooperative_comparator_pipeline(states, groups)
    observation = build_candidate_observation(
        scenario_class=generation["scenario_class"],
        simulation_step=1,
        vehicle_states=states,
        candidate_groups=groups,
        trace=trace,
        fairness_target_route=generation["fairness_target_route"],
        intended_waiting_pressure_seconds=threshold,
    )

    assert generation["fairness_target_route"] == "N_E"
    assert observation["fairness_pressure_present"] is True
    assert observation["fairness_target_waiting_time"] >= threshold
    assert len(observation["selected_vehicle_ids"]) > 1


def test_targeted_vehicle_counts_and_routes_are_exact_and_legal(monkeypatch, tmp_path):
    supported = set(supported_route_ids())
    requested = [(name, 8) for name in SCENARIOS] + [
        ("S3_COOPERATIVE_OPPORTUNITY", 12),
        ("S4_FAIRNESS_PRESSURE", 16),
    ]
    for index, (scenario_class, vehicle_count) in enumerate(requested):
        generation = _generate(
            monkeypatch,
            tmp_path,
            scenario_class,
            vehicle_count=vehicle_count,
            suffix=str(index),
        )
        assert generation["vehicle_count"] == vehicle_count
        assert len(generation["route_sequence"]) == vehicle_count
        assert len(generation["departure_times"]) == vehicle_count
        assert set(generation["route_sequence"]).issubset(supported)
        assert all(describe_route_id(route_id).movement in {"LEFT", "STRAIGHT", "RIGHT"} for route_id in generation["route_sequence"])


def test_targeted_seed_semantics_and_paired_initial_conditions_are_explicit(monkeypatch, tmp_path):
    s1_first = _generate(monkeypatch, tmp_path, "S1_BALANCED_MIXED_TURN", seed=1, suffix="seed1")
    s1_repeat = _generate(monkeypatch, tmp_path, "S1_BALANCED_MIXED_TURN", seed=1, suffix="seed1")
    s2_first = _generate(monkeypatch, tmp_path, "S2_SIMULTANEOUS_CONFLICT", seed=1, suffix="s2seed1")
    s2_second = _generate(monkeypatch, tmp_path, "S2_SIMULTANEOUS_CONFLICT", seed=2, suffix="s2seed2")

    assert initial_condition_record(s1_first) == initial_condition_record(s1_repeat)
    assert s1_first["seed_semantics"]["departure_timing_changes"] is True
    assert s1_first["seed_semantics"]["route_assignment_changes"] is False
    assert s2_first["route_sequence"] == s2_second["route_sequence"]
    assert s2_first["departure_times"] == s2_second["departure_times"]
    assert s2_first["seed_semantics"]["sumo_car_following_changes"] is True
    assert s2_first["initial_demand_signature"] != s2_second["initial_demand_signature"]


def test_phase1_density_generation_retains_seeded_gap_behavior(monkeypatch, tmp_path):
    monkeypatch.setattr(scenario_generator, "GENERATED_ROOT", tmp_path)
    config = scenario_generator.generate_scenario("pytest_phase1_low", "low", 7, vehicle_count=8)

    assert config["vehicle_count"] == 8
    assert len(config["departure_times"]) == 8
    assert all(4 <= right - left <= 12 for left, right in zip(config["departure_times"], config["departure_times"][1:]))
    assert set(config["route_sequence"]).issubset({"N_S", "S_N", "E_W", "W_E"})


def test_candidate_richness_summary_uses_candidate_decisions_not_vehicle_rows():
    observations = [
        {
            "candidate_count": 3,
            "candidate_group_sizes": [1, 1, 2],
            "has_multiple_candidates": True,
            "has_multi_vehicle_candidate": True,
            "fairness_pressure_present": False,
            "safety_intervention_count": 0,
        },
        {
            "candidate_count": 1,
            "candidate_group_sizes": [1],
            "has_multiple_candidates": False,
            "has_multi_vehicle_candidate": False,
            "fairness_pressure_present": True,
            "safety_intervention_count": 1,
        },
    ]
    summary = summarize_candidate_observations(observations)

    assert summary["controlled_decisions"] == 2
    assert summary["candidate_sets_with_multiple_legal_candidates"] == 1
    assert summary["candidate_richness_ratio"] == 0.5
    assert summary["cooperative_opportunity_ratio"] == 0.5
    assert summary["maximum_compatible_group_size"] == 2
    assert summary["safety_intervention_count"] == 1
