from __future__ import annotations

from pathlib import Path

import pytest

from src.controllers.candidate_runtime import CandidateGrantController, PlannerDecision
from src.experiments.counterfactual_checkpoint import (
    CHECKPOINT_FILES,
    REPLAY_ABSOLUTE_TOLERANCE,
    compare_replay_outcomes,
    load_checkpoint,
    save_checkpoint,
)


class _Simulation:
    def __init__(self): self.saved = []; self.loaded = []
    def saveState(self, path): Path(path).write_text("<state/>", encoding="utf-8"); self.saved.append(path)
    def loadState(self, path): self.loaded.append(path)


class _Traci:
    def __init__(self): self.simulation = _Simulation()


def _planner(states, groups, epoch, step, time):
    vehicle_id = states[0]["vehicle_id"]
    return PlannerDecision(trace={vehicle_id: {"selected_vehicle_ids": (vehicle_id,), "final_selected_candidate": vehicle_id, "postprocessed_decision": "PROCEED", "final_decision": "PROCEED"}})


def _safety(trace, _states): return trace


def _controller():
    return CandidateGrantController(planner_mode="DETERMINISTIC_CANDIDATE", planner_fn=_planner, safety_guard_fn=_safety, run_id="run", scenario_id="s3", vehicle_count=2, seed=2)


def _state(vehicle_id="a", inside=True):
    return {"vehicle_id": vehicle_id, "route_id": "N_S", "incoming_edge": "N", "outgoing_edge": "-S", "movement": "STRAIGHT", "speed": 1.0, "distance_to_intersection": 1.0, "time_to_intersection": 1.0, "waiting_time": 0.0, "inside_control_zone": inside}


def _metadata():
    return {"schema_version": 1, "scenario": "S3_COOPERATIVE_OPPORTUNITY", "seed": 2, "simulation_time": 12.0, "decision_epoch": 2, "candidate_set_hash": "ABC", "r4_candidate_id": "r4", "s2_candidate_id": "s2", "config_hashes": {"sumocfg": "123"}, "source_frozen_decision_reference": "phase2/s3/seed2/epoch2"}


def _outcome():
    return {"decision_sequence": ["r4"], "decision_epochs": [1], "candidate_sets": [[{"candidate_id": "r4", "vehicle_ids": ["a"]}]], "selected_candidate_ids": ["r4"], "arrived_vehicle_ids": ["a"], "completion": True, "grant_events": ["start", "end"], "collision_count": 0, "safety_intervention_count": 0, "termination_reason": "ALL_VEHICLES_COMPLETED", "vehicle_trajectories": {"a": [[0.0, 1.0], [1.0, 2.0]]}, "step_records": [{"speed": 1.0}], "waiting_by_vehicle": {"a": 0.0}, "speed_by_vehicle": {"a": 1.0}, "episode_duration_seconds": 2.0, "aggregate_metrics": {"mean_speed": 1.0}}


def test_controller_round_trip_preserves_active_grant_and_completed_records():
    controller = _controller(); controller.update([_state()], simulation_step=4, simulation_time=4.0)
    restored = CandidateGrantController.from_checkpoint_state(controller.checkpoint_state(), planner_fn=_planner, safety_guard_fn=_safety)
    assert restored.decision_epoch_count == controller.decision_epoch_count
    assert restored.active_grant is not None and restored.active_grant.vehicle_ids == ("a",)
    assert restored.active_grant.decision_record == controller.active_grant.decision_record


def test_checkpoint_round_trip_saves_sumo_controller_experiment_and_metadata(tmp_path):
    traci = _Traci(); controller = _controller(); controller.update([_state()], simulation_step=4, simulation_time=4.0)
    checkpoint = tmp_path / "checkpoint"; metadata = _metadata(); experiment = {"step": 4, "events": ["departed"], "maximum_waiting_by_vehicle": {"a": 0.0}, "collision_count": 0}
    save_checkpoint(traci, checkpoint, controller=controller, experiment_state=experiment, metadata=metadata)
    assert {path.name for path in checkpoint.iterdir()} == set(CHECKPOINT_FILES.values())
    restored = load_checkpoint(traci, checkpoint, planner_fn=_planner, safety_guard_fn=_safety, expected_metadata=metadata)
    assert traci.simulation.saved and traci.simulation.loaded
    assert restored.experiment_state == experiment and restored.controller.checkpoint_state() == controller.checkpoint_state()


def test_checkpoint_can_restore_python_state_after_sumo_was_loaded_at_process_start(tmp_path):
    traci = _Traci(); controller = _controller(); checkpoint = tmp_path / "checkpoint"
    save_checkpoint(traci, checkpoint, controller=controller, experiment_state={"step": 4}, metadata=_metadata())

    restored = load_checkpoint(
        traci,
        checkpoint,
        planner_fn=_planner,
        safety_guard_fn=_safety,
        expected_metadata=_metadata(),
        sumo_state_already_loaded=True,
    )

    assert traci.simulation.loaded == []
    assert restored.experiment_state == {"step": 4}


def test_malformed_or_config_mismatched_checkpoint_is_rejected(tmp_path):
    traci = _Traci(); controller = _controller(); checkpoint = tmp_path / "checkpoint"
    save_checkpoint(traci, checkpoint, controller=controller, experiment_state={"step": 0}, metadata=_metadata())
    (checkpoint / CHECKPOINT_FILES["metadata"]).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed checkpoint metadata"):
        load_checkpoint(traci, checkpoint, planner_fn=_planner, safety_guard_fn=_safety, expected_metadata=_metadata())
    save_checkpoint(traci, tmp_path / "checkpoint-two", controller=controller, experiment_state={"step": 0}, metadata=_metadata())
    with pytest.raises(ValueError, match="metadata mismatch"):
        load_checkpoint(traci, tmp_path / "checkpoint-two", planner_fn=_planner, safety_guard_fn=_safety, expected_metadata={"config_hashes": {"sumocfg": "different"}})


def test_checkpoint_refuses_overwrite_and_replay_gate_requires_discrete_and_numeric_equivalence(tmp_path):
    traci = _Traci(); controller = _controller(); checkpoint = tmp_path / "checkpoint"
    save_checkpoint(traci, checkpoint, controller=controller, experiment_state={"step": 0}, metadata=_metadata())
    with pytest.raises(FileExistsError):
        save_checkpoint(traci, checkpoint, controller=controller, experiment_state={"step": 0}, metadata=_metadata())
    baseline = _outcome(); restored = _outcome(); restored["step_records"] = [{"speed": 1.0 + REPLAY_ABSOLUTE_TOLERANCE / 2}]
    assert compare_replay_outcomes(baseline, restored)["replay_equivalent"] is True
    restored["selected_candidate_ids"] = ["s2"]
    assert compare_replay_outcomes(baseline, restored)["replay_equivalent"] is False
    restored = _outcome()
    restored["step_records"] = [{"speed": 1.0 + REPLAY_ABSOLUTE_TOLERANCE * 2}]
    assert compare_replay_outcomes(baseline, restored)["replay_equivalent"] is False
