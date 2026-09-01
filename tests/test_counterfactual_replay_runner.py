from __future__ import annotations

import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

import src.experiments.counterfactual_replay as replay
from src.controllers.candidate_runtime import CandidateGrantController, PlannerDecision
from src.experiments.counterfactual_checkpoint import REPLAY_ABSOLUTE_TOLERANCE


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _state(vehicle_id: str = "a") -> dict:
    return {
        "vehicle_id": vehicle_id,
        "route_id": "N_S",
        "incoming_edge": "N",
        "outgoing_edge": "-S",
        "movement": "STRAIGHT",
        "speed": 1.0,
        "distance_to_intersection": 2.0,
        "time_to_intersection": 2.0,
        "waiting_time": 0.0,
        "inside_control_zone": True,
    }


def _planner(states, groups, epoch, step, simulation_time):
    vehicle_id = groups[0][0]
    return PlannerDecision(
        trace={
            vehicle_id: {
                "selected_vehicle_ids": (vehicle_id,),
                "final_selected_candidate": vehicle_id,
                "postprocessed_decision": "PROCEED",
                "final_decision": "PROCEED",
            }
        }
    )


def _controller(hook=None):
    return CandidateGrantController(
        planner_mode="DETERMINISTIC_CANDIDATE",
        planner_fn=_planner,
        safety_guard_fn=lambda trace, states: trace,
        run_id="technical-replay",
        scenario_id="s3",
        vehicle_count=1,
        seed=1,
        before_planner_hook=hook,
    )


def _outcome() -> dict:
    return {
        "decision_sequence": [1, 2, 3],
        "decision_epochs": [1, 2, 3],
        "candidate_sets": [[{"candidate_id": "r4", "vehicle_ids": ["a"]}]],
        "selected_candidate_ids": ["a", "b", "r4"],
        "arrived_vehicle_ids": ["a"],
        "completion": True,
        "grant_events": [{"decision_epoch": 3, "candidate_id": "r4"}],
        "collision_count": 0,
        "safety_intervention_count": 0,
        "termination_reason": "ALL_VEHICLES_COMPLETED",
        "vehicle_trajectories": [{"simulation_time": 21.0, "position": [1.0, 2.0]}],
        "step_records": [{"simulation_time": 21.0, "speed": 1.0}],
        "waiting_by_vehicle": {"a": 0.0},
        "speed_by_vehicle": {"a": 1.0},
        "episode_duration_seconds": 40.0,
        "aggregate_metrics": {"mean_speed": 1.0, "mean_waiting_time": 0.0},
        "decision_records": [{"decision_epoch": 3, "selected_candidate_id": "r4"}],
    }


def test_replay_plan_has_two_deterministic_paths_without_provider_or_forced_action():
    plan = replay.ReplayPlan()

    assert replay.DEFAULT_OUTPUT_ROOT.name == "replay_equivalence_attempt3"
    assert plan.paths == ("reference", "restored")
    assert plan.planner_mode == "DETERMINISTIC_CANDIDATE"
    assert plan.provider_calls == 0
    assert plan.forced_candidate_id is None


def test_runner_script_bootstraps_repository_imports_when_executed_directly():
    completed = subprocess.run(
        [sys.executable, "scripts/run_counterfactual_replay_equivalence.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Run deterministic real-SUMO replay-equivalence validation" in completed.stdout


def test_before_planner_hook_observes_preselection_state_and_propagates_pause():
    observed = {}

    def hook(controller, states, groups, epoch, step, simulation_time):
        observed.update(
            epoch=epoch,
            controller_epoch=controller.decision_epoch_count,
            active_grant=controller.active_grant,
            groups=groups,
        )
        raise replay._CheckpointPause()

    controller = _controller(hook)
    with pytest.raises(replay._CheckpointPause):
        controller.update([_state()], simulation_step=21, simulation_time=21.0)

    assert observed == {"epoch": 1, "controller_epoch": 0, "active_grant": None, "groups": [["a"]]}
    assert controller.decision_epoch_count == 0
    assert controller.decision_records == []


def test_checkpoint_identity_accepts_tolerance_and_rejects_discrete_or_excess_numeric_change():
    reference = {
        "candidate_ids": ["r4", "s2"],
        "vehicle": {"id": "a", "position": [1.0, 2.0]},
        "config_hashes": {"network": "ABC"},
    }
    within = json.loads(json.dumps(reference))
    within["vehicle"]["position"][0] += REPLAY_ABSOLUTE_TOLERANCE / 2
    replay.validate_checkpoint_identity(reference, within)

    excess = json.loads(json.dumps(reference))
    excess["vehicle"]["position"][0] += REPLAY_ABSOLUTE_TOLERANCE * 2
    with pytest.raises(replay.ReplayInfrastructureError, match="identity mismatch"):
        replay.validate_checkpoint_identity(reference, excess)

    changed = json.loads(json.dumps(reference))
    changed["candidate_ids"] = ["s2", "r4"]
    with pytest.raises(replay.ReplayInfrastructureError, match="identity mismatch"):
        replay.validate_checkpoint_identity(reference, changed)


def test_sumo_command_preserves_rng_and_precision_for_one_micro_unit_tolerance(tmp_path, monkeypatch):
    runner = object.__new__(replay.RealSumoReplayRunner)
    runner.sumo_binary = tmp_path / "sumo.exe"
    runner.scenario_config = tmp_path / "simulation.sumocfg"
    runner.seed = 1
    command = runner._sumo_command()

    assert command[command.index("--save-state.precision") + 1] == "15"
    assert command[command.index("--save-state.rng") + 1] == "true"
    assert "--load-state.offset" not in command


def test_restored_sumo_starts_from_snapshot_time_without_second_route_replay(tmp_path):
    runner = object.__new__(replay.RealSumoReplayRunner)
    runner.sumo_binary = tmp_path / "sumo.exe"
    runner.scenario_config = tmp_path / "simulation.sumocfg"
    runner.seed = 1
    state_path = tmp_path / "sumo_state.xml"
    state_path.write_text('<snapshot time="22.000"/>', encoding="utf-8")

    saved_time = runner._saved_simulation_time(state_path)
    command = runner._sumo_command(load_state_path=state_path, begin_time=saved_time)

    assert saved_time == 22.0
    assert command[command.index("--load-state") + 1] == str(state_path)
    assert command[command.index("--begin") + 1] == "22.0"


def test_restore_startup_rejects_incomplete_load_state_arguments(tmp_path):
    runner = object.__new__(replay.RealSumoReplayRunner)
    runner.sumo_binary = tmp_path / "sumo.exe"

    with pytest.raises(replay.ReplayInfrastructureError, match="requires both"):
        runner._sumo_command(load_state_path=tmp_path / "sumo_state.xml")


def test_representative_state_requires_matching_frozen_candidate_sets(tmp_path, monkeypatch):
    deterministic = tmp_path / "deterministic.jsonl"
    gemini = tmp_path / "gemini.jsonl"
    common = {
        "decision_epoch": 3,
        "simulation_time": 21.0,
        "candidate_set": [
            {"candidate_id": "r4", "vehicle_ids": ["a", "b", "c", "d"]},
            {"candidate_id": "s2", "vehicle_ids": ["e", "f"]},
        ],
        "deterministic_candidate_id": "r4",
    }
    deterministic.write_text(json.dumps(common) + "\n", encoding="utf-8")
    gemini.write_text(json.dumps({**common, "llm_candidate_id": "s2"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(replay, "SOURCE_DETERMINISTIC_RECORDS", deterministic)
    monkeypatch.setattr(replay, "SOURCE_GEMINI_RECORDS", gemini)

    representative = replay.load_representative_state()
    assert representative["candidate_ids"] == ["r4", "s2"]
    assert representative["r4_candidate_id"] == "r4"
    assert representative["s2_candidate_id"] == "s2"

    gemini.write_text(
        json.dumps({**common, "candidate_set": common["candidate_set"][:1], "llm_candidate_id": "s2"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(replay.ReplayInfrastructureError, match="candidate sets"):
        replay.load_representative_state()


def test_experiment_state_round_trip_rejects_incomplete_restore():
    state = replay.ExperimentState(step=21, simulation_time=21.0)
    assert replay.ExperimentState.from_dict(state.to_dict()) == state
    malformed = state.to_dict()
    malformed.pop("collision_count")
    with pytest.raises(replay.ReplayInfrastructureError, match="Malformed"):
        replay.ExperimentState.from_dict(malformed)


def test_runner_constructs_reference_checkpoint_restore_and_equivalence_gate(tmp_path, monkeypatch):
    class FakeRunner(replay.RealSumoReplayRunner):
        def __init__(self):
            self.output_root = tmp_path / "replay_equivalence"
            self.checkpoint_dir = self.output_root / "checkpoint"
            self.sumo_binary = tmp_path / "sumo.exe"
            self.sumo_binary.write_bytes(b"fake")
            self.plan = replay.ReplayPlan()
            self.vehicle_count = 12
            self.representative = {"candidate_ids": ["r4", "s2"]}
            self.config_hashes = {"network": "ABC"}
            self.metadata = {}
            self.sumo_version = ["fake", "1.0"]
            self.current_stage = "INITIALIZATION"
            self.calls = []

        def _run_reference(self, traci, *, simulation_steps):
            self.calls.append("reference")
            return _outcome(), {"candidate_ids": ["r4", "s2"], "position": [1.0, 2.0]}

        def _run_restored(self, traci, reference_identity, *, simulation_steps):
            self.calls.append("restored")
            self.checkpoint_dir.mkdir(parents=True)
            (self.checkpoint_dir / "controller_state.json").write_text("{}", encoding="utf-8")
            (self.checkpoint_dir / "experiment_state.json").write_text("{}", encoding="utf-8")
            return _outcome(), reference_identity, reference_identity

    monkeypatch.setitem(sys.modules, "traci", types.SimpleNamespace())
    runner = FakeRunner()
    result = runner.run(simulation_steps=50)

    assert runner.calls == ["reference", "restored"]
    assert result["gate"] == "REPLAY_EQUIVALENT"
    assert (runner.output_root / "reference" / "outcome.json").is_file()
    assert (runner.output_root / "reference" / "decision_records.json").is_file()
    assert (runner.output_root / "restored" / "outcome.json").is_file()
    assert (runner.output_root / "restored" / "decision_records.json").is_file()
    assert (runner.output_root / "comparison.json").is_file()
    assert (runner.output_root / "replay_equivalence_report.md").is_file()
