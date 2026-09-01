from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import src.experiments.counterfactual_branches as branches
from src.experiments.counterfactual_checkpoint import CHECKPOINT_FILES, REPLAY_ABSOLUTE_TOLERANCE
from src.experiments.counterfactual_replay import ReplayInfrastructureError, candidate_set_hash


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _state(vehicle_id: str, movement: str = "RIGHT") -> dict:
    return {
        "vehicle_id": vehicle_id,
        "route_id": "N_W" if movement == "RIGHT" else "N_S",
        "incoming_edge": "N",
        "outgoing_edge": "-W" if movement == "RIGHT" else "-S",
        "movement": movement,
        "speed": 0.0,
        "distance_to_intersection": 10.0,
        "time_to_intersection": 10.0,
        "waiting_time": 1.0,
        "inside_control_zone": True,
    }


def _fixture():
    states = [_state(vehicle_id) for vehicle_id in ("a", "b", "c", "d")]
    states.extend(_state(vehicle_id, "STRAIGHT") for vehicle_id in ("e", "f"))
    groups = [["a", "b", "c", "d"], ["e", "f"]]
    return states, groups


def _entry(decision):
    return next(iter(decision.trace.values()))


def _comparison(seed: int, r4_wait: float, s2_wait: float) -> dict:
    def side(wait):
        return {
            "completion": True,
            "mean_waiting_time": wait,
            "maximum_waiting_time": wait + 1,
            "episode_duration_seconds": wait + 20,
            "mean_speed": 10.0 - wait,
            "total_waiting_time": wait * 12,
            "waiting_sample_sd": 1.0,
            "throughput": 12,
        }

    return branches.paired_comparison(seed, side(r4_wait), side(s2_wait))


def test_matrix_is_exact_three_historical_seeds_and_two_branches():
    assert [spec.seed for spec in branches.HISTORICAL_STATES] == [1, 2, 3]
    assert [spec.simulation_time for spec in branches.HISTORICAL_STATES] == [21.0, 23.0, 20.0]
    assert branches.BRANCHES == ("R4", "S2")
    assert all(len(spec.r4_candidate_id.split("|")) == 4 for spec in branches.HISTORICAL_STATES)
    assert all(len(spec.s2_candidate_id.split("|")) == 2 for spec in branches.HISTORICAL_STATES)
    assert branches.DEFAULT_OUTPUT_ROOT.name == "s3_r4_vs_s2_branches"


def test_frozen_historical_states_match_candidate_state_and_valid_gemini_provenance():
    for spec in branches.HISTORICAL_STATES:
        state = branches.load_historical_state(spec)
        assert state["r4_candidate_id"] in state["candidate_ids"]
        assert state["s2_candidate_id"] in state["candidate_ids"]
        assert state["candidate_set_hash"] == candidate_set_hash(state["candidate_ids"])


def test_live_checkpoint_must_match_frozen_state_and_candidate_features():
    states, groups = _fixture()
    local_state, candidate_features, _ = branches.build_candidate_selection_context(states, groups)
    representative = {
        "privacy_minimised_vehicle_inputs": local_state,
        "candidate_features": candidate_features,
    }
    branches.validate_live_historical_state(representative, states, groups)
    changed = [dict(state) for state in states]
    changed[0]["waiting_time"] = 2.0
    with pytest.raises(ReplayInfrastructureError, match="traffic state"):
        branches.validate_live_historical_state(representative, changed, groups)


def test_single_force_is_legal_then_all_later_decisions_are_deterministic():
    states, groups = _fixture()
    planner = branches.SingleForcedPlanner(
        forced_candidate_id="e|f",
        historical_source="OBSERVED_GEMINI_S2",
        expected_candidate_set_hash=candidate_set_hash(["a|b|c|d", "e|f"]),
        target_epoch=3,
        safety_guard_fn=lambda trace, _states: trace,
    )

    forced = planner(states, groups, 3, 21, 21.0)
    later = planner(states, groups, 4, 30, 30.0)

    assert _entry(forced)["final_selected_candidate"] == "e|f"
    assert _entry(forced)["selection_source"] == "FORCED_OBSERVED_GEMINI_S2"
    assert _entry(later)["final_selected_candidate"] == "a|b|c|d"
    assert _entry(later)["selection_source"] == "DETERMINISTIC_COMPARATOR"
    assert planner.forced_action_count == 1
    assert planner.provider_calls == 0


def test_illegal_force_candidate_hash_mismatch_and_second_force_fail_closed():
    states, groups = _fixture()
    expected_hash = candidate_set_hash(["a|b|c|d", "e|f"])
    illegal = branches.SingleForcedPlanner(
        forced_candidate_id="missing",
        historical_source="DETERMINISTIC_R4",
        expected_candidate_set_hash=expected_hash,
        target_epoch=3,
        safety_guard_fn=lambda trace, _states: trace,
    )
    with pytest.raises(ReplayInfrastructureError, match="not legal"):
        illegal(states, groups, 3, 21, 21.0)

    mismatch = branches.SingleForcedPlanner(
        forced_candidate_id="e|f",
        historical_source="OBSERVED_GEMINI_S2",
        expected_candidate_set_hash="WRONG",
        target_epoch=3,
        safety_guard_fn=lambda trace, _states: trace,
    )
    with pytest.raises(ReplayInfrastructureError, match="candidate set"):
        mismatch(states, groups, 3, 21, 21.0)

    valid = branches.SingleForcedPlanner(
        forced_candidate_id="e|f",
        historical_source="OBSERVED_GEMINI_S2",
        expected_candidate_set_hash=expected_hash,
        target_epoch=3,
        safety_guard_fn=lambda trace, _states: trace,
    )
    valid(states, groups, 3, 21, 21.0)
    with pytest.raises(ReplayInfrastructureError, match="Repeated intervention"):
        valid(states, groups, 3, 21, 21.0)


def test_checkpoint_hash_identity_detects_any_change(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    for filename in CHECKPOINT_FILES.values():
        (checkpoint / filename).write_text(filename, encoding="utf-8")
    before = branches._checkpoint_hashes(checkpoint)
    (checkpoint / CHECKPOINT_FILES["controller_state"]).write_text("changed", encoding="utf-8")
    after = branches._checkpoint_hashes(checkpoint)
    assert before != after


def test_replay_gate_requires_exact_attempt3_success(tmp_path):
    gate = tmp_path / "comparison.json"
    gate.write_text(
        '{"gate":"REPLAY_EQUIVALENT","replay_equivalent":true,"mismatches":[],"tolerance":0.000001}',
        encoding="utf-8",
    )
    assert branches.verify_replay_gate(gate)["replay_equivalent"] is True
    gate.write_text(
        '{"gate":"REPLAY_NOT_EQUIVALENT","replay_equivalent":false,"mismatches":["x"],"tolerance":0.000001}',
        encoding="utf-8",
    )
    with pytest.raises(ReplayInfrastructureError, match="has not passed"):
        branches.verify_replay_gate(gate)


def test_paired_calculation_and_preregistered_classification_are_fixed():
    better_s2 = [_comparison(seed, 5.0, 4.0) for seed in (1, 2, 3)]
    assert better_s2[0]["S2_minus_R4"]["mean_waiting_time"] == -1.0
    assert branches.classify_primary_outcomes(better_s2) == (
        "S2_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES"
    )
    minimal = [
        _comparison(seed, 5.0, 5.0 + REPLAY_ABSOLUTE_TOLERANCE / 24)
        for seed in (1, 2, 3)
    ]
    assert branches.classify_primary_outcomes(minimal) == "MINIMAL_SYSTEM_CONSEQUENCE"
    mixed = [_comparison(1, 5.0, 4.0), _comparison(2, 4.0, 5.0), _comparison(3, 5.0, 5.0)]
    assert branches.classify_primary_outcomes(mixed) == "MIXED_TRADEOFF"
    assert branches.classify_primary_outcomes(mixed[:2]) == "INCONCLUSIVE"


def test_runner_refuses_existing_output_and_has_no_gemini_execution_dependency(tmp_path, monkeypatch):
    output = tmp_path / "existing"
    output.mkdir()
    sumo = tmp_path / "sumo.exe"
    sumo.write_bytes(b"fake")
    runner = branches.SameStateCounterfactualRunner(sumo_binary=sumo, output_root=output)
    with pytest.raises(FileExistsError):
        runner._assert_preflight()
    source = Path(branches.__file__).read_text(encoding="utf-8")
    assert "run_live_candidate_request" not in source
    assert "GEMINI_CANDIDATE" not in source


def test_runner_script_imports_from_repository_root():
    completed = subprocess.run(
        [sys.executable, "scripts/run_same_state_counterfactual_branches.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "six preregistered same-state" in completed.stdout
