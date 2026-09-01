"""Real-TraCI deterministic replay-equivalence validation infrastructure."""
from __future__ import annotations

import hashlib
import json
import math
import traceback
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.controllers.candidate_runtime import (
    DETERMINISTIC_CANDIDATE,
    CandidateGrantController,
    PlannerDecision,
)
from src.controllers.decision_pipeline import execute_cooperative_comparator_pipeline
from src.experiments.counterfactual_checkpoint import (
    REPLAY_ABSOLUTE_TOLERANCE,
    compare_replay_outcomes,
    load_checkpoint,
    save_checkpoint,
)
from src.safety.candidate_groups import build_safe_candidate_groups


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "results" / "counterfactual_validation" / "replay_equivalence_attempt3"
SCENARIO_ID = "phase2_s3_cooperative_opportunity_v12_seed1"
SCENARIO_CLASS = "S3_COOPERATIVE_OPPORTUNITY"
SEED = 1
VEHICLE_COUNT = 12
TARGET_DECISION_EPOCH = 3
TARGET_SIMULATION_TIME = 21.0
SOURCE_DETERMINISTIC_RECORDS = (
    PROJECT_ROOT
    / "results"
    / "phase2_formal"
    / "batch2_remaining_matrix"
    / "runs"
    / "s3_cooperative_opportunity_v12_seed1"
    / "phase2_formal_batch2_s3_cooperative_opportunity_v12_seed1_deterministic_candidate"
    / "decision_records.jsonl"
)
SOURCE_GEMINI_RECORDS = SOURCE_DETERMINISTIC_RECORDS.parent.parent / (
    "phase2_formal_batch2_s3_cooperative_opportunity_v12_seed1_gemini_candidate"
) / "decision_records.jsonl"
SCENARIO_ROOT = PROJECT_ROOT / "simulation" / "generated_routes" / SCENARIO_ID
SCENARIO_CONFIG = SCENARIO_ROOT / "simulation.sumocfg"
SOURCE_FROZEN_REFERENCE = (
    "Phase2 formal S3-12V seed 1, decision epoch 3, simulation time 21.0 s; "
    "batch2_remaining_matrix matched deterministic/Gemini records"
)


class ReplayInfrastructureError(RuntimeError):
    """Raised when checkpoint identity or replay infrastructure is invalid."""


class _CheckpointPause(RuntimeError):
    pass


@dataclass(frozen=True)
class ReplayPlan:
    scenario_id: str = SCENARIO_ID
    scenario_class: str = SCENARIO_CLASS
    seed: int = SEED
    vehicle_count: int = VEHICLE_COUNT
    target_decision_epoch: int = TARGET_DECISION_EPOCH
    target_simulation_time: float = TARGET_SIMULATION_TIME
    planner_mode: str = DETERMINISTIC_CANDIDATE
    forced_candidate_id: None = None
    provider_calls: int = 0
    paths: tuple[str, str] = ("reference", "restored")


@dataclass
class ExperimentState:
    step: int = 0
    simulation_time: float = 0.0
    departed_vehicle_ids: list[str] = field(default_factory=list)
    arrived_vehicle_ids: list[str] = field(default_factory=list)
    all_seen_vehicle_ids: list[str] = field(default_factory=list)
    maximum_waiting_by_vehicle: dict[str, float] = field(default_factory=dict)
    speed_total: float = 0.0
    speed_observation_count: int = 0
    collision_count: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    vehicle_trajectories: list[dict[str, Any]] = field(default_factory=list)
    step_records: list[dict[str, Any]] = field(default_factory=list)
    termination_reason: str = "UNEXPECTED_SUMO_TERMINATION"

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self.__dict__, allow_nan=False))

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ExperimentState":
        if not isinstance(value, dict) or set(value) != set(cls().__dict__):
            raise ReplayInfrastructureError("Malformed replay experiment state")
        return cls(**json.loads(json.dumps(value, allow_nan=False)))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ReplayInfrastructureError(f"Frozen decision evidence is missing: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _record_for_epoch(path: Path, epoch: int) -> dict[str, Any]:
    matches = [row for row in _read_jsonl(path) if int(row.get("decision_epoch", -1)) == epoch]
    if len(matches) != 1:
        raise ReplayInfrastructureError(f"Expected one frozen decision record for epoch {epoch}: {path}")
    return matches[0]


def _candidate_ids(candidate_groups: list[list[str]]) -> list[str]:
    return ["|".join(group) for group in candidate_groups]


def candidate_set_hash(candidate_ids: list[str]) -> str:
    payload = json.dumps(candidate_ids, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def required_config_hashes() -> dict[str, str]:
    paths = {
        "network": PROJECT_ROOT / "net.net.xml",
        "scenario_routes": SCENARIO_ROOT / "routes.xml",
        "scenario_sumocfg": SCENARIO_CONFIG,
        "scenario_generation_config": SCENARIO_ROOT / "generation_config.json",
        "project_config": PROJECT_ROOT / "config" / "project_config.yaml",
        "experiment_matrix": PROJECT_ROOT / "config" / "experiment_matrix.yaml",
        "route_conflicts": PROJECT_ROOT / "config" / "route_conflicts.yaml",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise ReplayInfrastructureError(f"Required replay configuration is missing: {missing}")
    return {name: _sha256(path) for name, path in paths.items()}


def load_representative_state() -> dict[str, Any]:
    deterministic = _record_for_epoch(SOURCE_DETERMINISTIC_RECORDS, TARGET_DECISION_EPOCH)
    gemini = _record_for_epoch(SOURCE_GEMINI_RECORDS, TARGET_DECISION_EPOCH)
    deterministic_ids = [row["candidate_id"] for row in deterministic.get("candidate_set", [])]
    gemini_ids = [row["candidate_id"] for row in gemini.get("candidate_set", [])]
    if deterministic_ids != gemini_ids or not deterministic_ids:
        raise ReplayInfrastructureError("Frozen matched candidate sets are missing or inconsistent")
    if float(deterministic.get("simulation_time", -1.0)) != TARGET_SIMULATION_TIME:
        raise ReplayInfrastructureError("Frozen representative simulation time has drifted")
    r4_id = str(deterministic.get("deterministic_candidate_id", ""))
    s2_id = str(gemini.get("llm_candidate_id", ""))
    if r4_id not in deterministic_ids or s2_id not in deterministic_ids or r4_id == s2_id:
        raise ReplayInfrastructureError("Frozen R4/S2 disagreement provenance is invalid")
    return {
        "candidate_ids": deterministic_ids,
        "candidate_set_hash": candidate_set_hash(deterministic_ids),
        "r4_candidate_id": r4_id,
        "s2_candidate_id": s2_id,
        "source_frozen_decision_reference": SOURCE_FROZEN_REFERENCE,
    }


def build_checkpoint_metadata(representative: dict[str, Any], config_hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "scenario": SCENARIO_ID,
        "seed": SEED,
        "simulation_time": TARGET_SIMULATION_TIME,
        "decision_epoch": TARGET_DECISION_EPOCH,
        "candidate_set_hash": representative["candidate_set_hash"],
        "r4_candidate_id": representative["r4_candidate_id"],
        "s2_candidate_id": representative["s2_candidate_id"],
        "config_hashes": config_hashes,
        "source_frozen_decision_reference": representative["source_frozen_decision_reference"],
    }


def _identity_numeric_equal(left: Any, right: Any, tolerance: float = REPLAY_ABSOLUTE_TOLERANCE) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= tolerance
    if isinstance(left, dict) and isinstance(right, dict) and set(left) == set(right):
        return all(_identity_numeric_equal(left[key], right[key], tolerance) for key in left)
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return all(_identity_numeric_equal(a, b, tolerance) for a, b in zip(left, right, strict=True))
    return left == right


def validate_checkpoint_identity(
    reference: dict[str, Any],
    observed: dict[str, Any],
    *,
    tolerance: float = REPLAY_ABSOLUTE_TOLERANCE,
) -> None:
    mismatches: list[str] = []
    _collect_identity_mismatches(reference, observed, path="identity", tolerance=tolerance, mismatches=mismatches)
    if mismatches:
        raise ReplayInfrastructureError(f"Pre-checkpoint identity mismatch: {', '.join(mismatches)}")


def _collect_identity_mismatches(
    left: Any,
    right: Any,
    *,
    path: str,
    tolerance: float,
    mismatches: list[str],
) -> None:
    if isinstance(left, bool) or isinstance(right, bool):
        if left != right:
            mismatches.append(path)
        return
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if abs(float(left) - float(right)) > tolerance:
            mismatches.append(path)
        return
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            mismatches.append(path)
            return
        for key in left:
            _collect_identity_mismatches(
                left[key], right[key], path=f"{path}.{key}", tolerance=tolerance, mismatches=mismatches
            )
        return
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            mismatches.append(path)
            return
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            _collect_identity_mismatches(
                a, b, path=f"{path}[{index}]", tolerance=tolerance, mismatches=mismatches
            )
        return
    if left != right:
        mismatches.append(path)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Counterfactual Replay-Equivalence Report",
        "",
        f"- Gate: `{result['gate']}`",
        f"- Scenario: `{SCENARIO_ID}`",
        f"- Seed: `{SEED}`",
        f"- Decision epoch: `{TARGET_DECISION_EPOCH}`",
        f"- Simulation time: `{TARGET_SIMULATION_TIME}` s",
        f"- Planner: `{DETERMINISTIC_CANDIDATE}` on both paths",
        f"- Numerical absolute tolerance: `{REPLAY_ABSOLUTE_TOLERANCE}`",
        f"- Forced candidate: `NONE`",
        f"- Gemini/API calls: `0`",
        "",
        "This is a technical restore-equivalence gate, not a scientific counterfactual result.",
    ]
    if result.get("mismatches"):
        lines.extend(("", "## Mismatches", "", *[f"- `{item}`" for item in result["mismatches"]]))
    if result.get("error"):
        lines.extend(("", "## Infrastructure error", "", f"`{result['error']}`"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class RealSumoReplayRunner:
    def __init__(self, *, sumo_binary: Path, output_root: Path = DEFAULT_OUTPUT_ROOT):
        self.sumo_binary = Path(sumo_binary)
        self.output_root = Path(output_root)
        self.plan = ReplayPlan()
        self.scenario_id = self.plan.scenario_id
        self.scenario_class = self.plan.scenario_class
        self.seed = self.plan.seed
        self.vehicle_count = self.plan.vehicle_count
        self.target_decision_epoch = self.plan.target_decision_epoch
        self.target_simulation_time = self.plan.target_simulation_time
        self.scenario_config = SCENARIO_CONFIG
        self.representative = load_representative_state()
        self.config_hashes = required_config_hashes()
        self.metadata = build_checkpoint_metadata(self.representative, self.config_hashes)
        self.checkpoint_dir = self.output_root / "checkpoint"
        self.sumo_version: Any = None
        self.current_stage = "INITIALIZATION"

    def _assert_new_output(self) -> None:
        if self.output_root.exists():
            raise FileExistsError(f"Replay-equivalence output root already exists: {self.output_root}")
        if not self.sumo_binary.is_file():
            raise ReplayInfrastructureError(f"SUMO binary is missing: {self.sumo_binary}")
        self.output_root.mkdir(parents=True)

    @staticmethod
    def _traffic_state(traci: Any, vehicle_ids: list[str]) -> list[dict[str, Any]]:
        from common import distance_to_center, estimate_time_to_intersection, get_vehicle_route, is_in_control_zone
        from src.safety.route_semantics import describe_route_id

        states = []
        for vehicle_id in vehicle_ids:
            route_id = get_vehicle_route(traci, vehicle_id)
            semantics = describe_route_id(route_id)
            states.append(
                {
                    "vehicle_id": vehicle_id,
                    "route_id": route_id,
                    "incoming_edge": semantics.incoming_edge,
                    "outgoing_edge": semantics.outgoing_edge,
                    "movement": semantics.movement,
                    "speed": round(traci.vehicle.getSpeed(vehicle_id), 2),
                    "distance_to_intersection": round(distance_to_center(traci, vehicle_id), 2),
                    "time_to_intersection": round(estimate_time_to_intersection(traci, vehicle_id), 2),
                    "waiting_time": round(traci.vehicle.getWaitingTime(vehicle_id), 2),
                    "inside_control_zone": is_in_control_zone(traci, vehicle_id),
                }
            )
        return states

    @staticmethod
    def _neutralize_signal(traci: Any) -> None:
        for signal_id in traci.trafficlight.getIDList():
            state = traci.trafficlight.getRedYellowGreenState(signal_id)
            traci.trafficlight.setRedYellowGreenState(signal_id, "G" * len(state))

    @staticmethod
    def _safety_guard(traci: Any) -> Callable[[dict[str, dict], list[dict]], dict[str, dict]]:
        from src.controllers.decision_pipeline import _build_runtime_trace_from_guard
        from ttc_safety import verify_decisions

        def guard(trace: dict[str, dict], states: list[dict]) -> dict[str, dict]:
            vehicles = [state["vehicle_id"] for state in states]
            return _build_runtime_trace_from_guard(
                trace,
                states,
                lambda current_states, raw: verify_decisions(traci, vehicles, raw),
            )

        return guard

    def _controller(self, traci: Any, hook: Callable | None = None) -> CandidateGrantController:
        safety_guard = self._safety_guard(traci)

        def planner(states: list[dict], groups: list[list[str]], epoch: int, step: int, sim_time: float) -> PlannerDecision:
            return PlannerDecision(
                trace=execute_cooperative_comparator_pipeline(states, groups, safety_guard_fn=safety_guard)
            )

        return CandidateGrantController(
            planner_mode=DETERMINISTIC_CANDIDATE,
            planner_fn=planner,
            safety_guard_fn=safety_guard,
            run_id="counterfactual_replay_equivalence",
            scenario_id=self.scenario_id,
            vehicle_count=self.vehicle_count,
            seed=self.seed,
            before_planner_hook=hook,
        )

    def _identity(
        self,
        traci: Any,
        controller: CandidateGrantController,
        states: list[dict],
        groups: list[list[str]],
        epoch: int,
        step: int,
        simulation_time: float,
    ) -> dict[str, Any]:
        ids = _candidate_ids(groups)
        vehicles = []
        for state in sorted(states, key=lambda row: row["vehicle_id"]):
            vehicle_id = state["vehicle_id"]
            x, y = traci.vehicle.getPosition(vehicle_id)
            vehicles.append(
                {
                    "vehicle_id": vehicle_id,
                    "position": [float(x), float(y)],
                    "speed": float(traci.vehicle.getSpeed(vehicle_id)),
                    "route_id": state["route_id"],
                    "route_edges": list(traci.vehicle.getRoute(vehicle_id)),
                    "lane_id": traci.vehicle.getLaneID(vehicle_id),
                    "waiting_time": float(traci.vehicle.getWaitingTime(vehicle_id)),
                }
            )
        return {
            "simulation_step": int(step),
            "simulation_time": float(simulation_time),
            "vehicle_ids": [row["vehicle_id"] for row in vehicles],
            "vehicles": vehicles,
            "candidate_ids": ids,
            "candidate_set_hash": candidate_set_hash(ids),
            "active_grant": controller.checkpoint_state()["active_grant"],
            "controller_epoch": controller.decision_epoch_count,
            "next_decision_epoch": int(epoch),
            "config_hashes": self.config_hashes,
        }

    def _validate_target(self, identity: dict[str, Any]) -> None:
        if identity["next_decision_epoch"] != self.target_decision_epoch:
            return
        if identity["simulation_time"] != self.target_simulation_time:
            raise ReplayInfrastructureError("Target epoch occurred at an unexpected simulation time")
        if identity["candidate_ids"] != self.representative["candidate_ids"]:
            raise ReplayInfrastructureError("Live candidate set does not match frozen representative state")
        if identity["candidate_set_hash"] != self.representative["candidate_set_hash"]:
            raise ReplayInfrastructureError("Live candidate-set hash does not match frozen evidence")

    @staticmethod
    def _saved_simulation_time(state_path: Path) -> float:
        try:
            value = float(ET.parse(state_path).getroot().attrib["time"])
        except (OSError, ET.ParseError, KeyError, TypeError, ValueError) as exc:
            raise ReplayInfrastructureError(f"Cannot recover saved SUMO time: {state_path}") from exc
        if not math.isfinite(value) or value < 0:
            raise ReplayInfrastructureError(f"Invalid saved SUMO time: {value}")
        return value

    def _sumo_command(
        self,
        *,
        load_state_path: Path | None = None,
        begin_time: float | None = None,
    ) -> list[str]:
        if (load_state_path is None) != (begin_time is None):
            raise ReplayInfrastructureError("SUMO restore startup requires both load_state_path and begin_time")
        command = [
            str(self.sumo_binary), "-c", str(self.scenario_config), "--start", "--seed", str(self.seed),
            "--no-step-log", "true", "--no-warnings", "true",
            "--save-state.precision", "15", "--save-state.rng", "true",
        ]
        if load_state_path is not None:
            command.extend(("--load-state", str(load_state_path), "--begin", str(begin_time)))
        return command

    def _start(
        self,
        traci: Any,
        *,
        load_state_path: Path | None = None,
        begin_time: float | None = None,
    ) -> None:
        traci.start(self._sumo_command(load_state_path=load_state_path, begin_time=begin_time))
        self.sumo_version = traci.getVersion()
        self._neutralize_signal(traci)

    @staticmethod
    def _close(traci: Any) -> None:
        try:
            traci.close(False)
        except Exception:
            pass

    def _update_observations(self, traci: Any, state: ExperimentState, traffic: list[dict]) -> None:
        for vehicle in traffic:
            vehicle_id = vehicle["vehicle_id"]
            state.speed_total += float(vehicle["speed"])
            state.speed_observation_count += 1
            try:
                waiting = float(traci.vehicle.getAccumulatedWaitingTime(vehicle_id))
            except Exception:
                waiting = float(vehicle["waiting_time"])
            state.maximum_waiting_by_vehicle[vehicle_id] = max(
                state.maximum_waiting_by_vehicle.get(vehicle_id, 0.0), waiting
            )
            x, y = traci.vehicle.getPosition(vehicle_id)
            state.vehicle_trajectories.append(
                {
                    "simulation_step": state.step,
                    "simulation_time": state.simulation_time,
                    "vehicle_id": vehicle_id,
                    "position": [float(x), float(y)],
                    "speed": float(traci.vehicle.getSpeed(vehicle_id)),
                    "waiting_time": waiting,
                }
            )

    def _outcome(self, controller: CandidateGrantController, state: ExperimentState) -> dict[str, Any]:
        records = controller.decision_records
        departed_count = len(state.departed_vehicle_ids)
        arrived_count = len(state.arrived_vehicle_ids)
        aggregate = {
            "departed": departed_count,
            "arrived": arrived_count,
            "completion_rate": arrived_count / departed_count if departed_count else 0.0,
            "mean_waiting_time": (
                sum(state.maximum_waiting_by_vehicle.values()) / departed_count if departed_count else 0.0
            ),
            "maximum_waiting_time": max(state.maximum_waiting_by_vehicle.values(), default=0.0),
            "mean_speed": state.speed_total / state.speed_observation_count if state.speed_observation_count else 0.0,
        }
        return {
            "decision_sequence": [int(row["decision_epoch"]) for row in records],
            "decision_epochs": [int(row["decision_epoch"]) for row in records],
            "candidate_sets": [row["candidate_set"] for row in records],
            "selected_candidate_ids": [row["selected_candidate_id"] for row in records],
            "arrived_vehicle_ids": state.arrived_vehicle_ids,
            "completion": arrived_count == self.vehicle_count,
            "grant_events": [
                {
                    "decision_epoch": row["decision_epoch"],
                    "candidate_id": row["selected_candidate_id"],
                    "vehicle_ids": row["grant_vehicle_ids"],
                    "start_step": row["grant_start_step"],
                    "end_step": row["grant_end_step"],
                    "clearance_reason": row["grant_clearance_reason"],
                }
                for row in records
            ],
            "collision_count": state.collision_count,
            "safety_intervention_count": sum(
                int(row.get("safety_interventions_during_grant", 0)) for row in records
            ),
            "termination_reason": state.termination_reason,
            "vehicle_trajectories": state.vehicle_trajectories,
            "step_records": state.step_records,
            "waiting_by_vehicle": state.maximum_waiting_by_vehicle,
            "speed_by_vehicle": {
                row["vehicle_id"]: row["speed"] for row in state.vehicle_trajectories[-self.vehicle_count:]
            },
            "episode_duration_seconds": state.simulation_time,
            "aggregate_metrics": aggregate,
            "decision_records": records,
        }

    def _continue(
        self,
        traci: Any,
        controller: CandidateGrantController,
        state: ExperimentState,
        *,
        simulation_steps: int,
        resume_pending_step: bool = False,
    ) -> dict[str, Any]:
        from common import CONFIG, apply_decision, resolve_sumo_termination_reason

        pending = bool(resume_pending_step)
        while state.step < simulation_steps:
            self._neutralize_signal(traci)
            if not pending:
                traci.simulationStep()
                state.simulation_time = state.step * float(CONFIG["simulation_step_length"])
                for vehicle_id in traci.simulation.getDepartedIDList():
                    if vehicle_id not in state.departed_vehicle_ids:
                        state.departed_vehicle_ids.append(vehicle_id)
                        state.events.append(
                            {
                                "event_type": "departed",
                                "vehicle_id": vehicle_id,
                                "simulation_step": state.step,
                                "simulation_time": state.simulation_time,
                            }
                        )
                for vehicle_id in traci.simulation.getArrivedIDList():
                    if vehicle_id not in state.arrived_vehicle_ids:
                        state.arrived_vehicle_ids.append(vehicle_id)
                        state.events.append(
                            {
                                "event_type": "arrived",
                                "vehicle_id": vehicle_id,
                                "simulation_step": state.step,
                                "simulation_time": state.simulation_time,
                            }
                        )
            vehicle_ids = list(traci.vehicle.getIDList())
            for vehicle_id in vehicle_ids:
                if vehicle_id not in state.all_seen_vehicle_ids:
                    state.all_seen_vehicle_ids.append(vehicle_id)
            traffic = self._traffic_state(traci, vehicle_ids)
            if not pending:
                self._update_observations(traci, state, traffic)
            pending = False
            update = controller.update(
                traffic,
                simulation_step=state.step,
                simulation_time=state.simulation_time,
            )
            for vehicle_id in vehicle_ids:
                decision = update.trace[vehicle_id]["final_decision"]
                apply_decision(traci, vehicle_id, decision)
                state.step_records.append(
                    {
                        "simulation_step": state.step,
                        "simulation_time": state.simulation_time,
                        "vehicle_id": vehicle_id,
                        "speed": float(traci.vehicle.getSpeed(vehicle_id)),
                        "waiting_time": float(traci.vehicle.getWaitingTime(vehicle_id)),
                        "final_decision": decision,
                    }
                )
            try:
                state.collision_count += int(traci.simulation.getCollidingVehiclesNumber())
            except Exception:
                pass
            state.termination_reason = resolve_sumo_termination_reason(
                simulation_step=state.step,
                simulation_steps=simulation_steps,
                expected_remaining=int(traci.simulation.getMinExpectedNumber()),
                arrived_count=len(state.arrived_vehicle_ids),
                target_vehicle_count=self.vehicle_count,
            )
            if state.termination_reason:
                break
            state.step += 1
        controller.finish(simulation_step=state.step, simulation_time=state.simulation_time)
        return self._outcome(controller, state)

    def _run_reference(self, traci: Any, *, simulation_steps: int) -> tuple[dict[str, Any], dict[str, Any]]:
        checkpoint_identity: dict[str, Any] = {}

        def hook(controller, states, groups, epoch, step, simulation_time):
            if epoch != self.target_decision_epoch:
                return
            identity = self._identity(traci, controller, states, groups, epoch, step, simulation_time)
            self._validate_target(identity)
            checkpoint_identity.update(identity)

        controller = self._controller(traci, hook)
        state = ExperimentState()
        self.current_stage = "PATH_A_START"
        self._start(traci)
        try:
            self.current_stage = "PATH_A_CONTINUATION"
            outcome = self._continue(traci, controller, state, simulation_steps=simulation_steps)
        finally:
            self._close(traci)
        if not checkpoint_identity:
            raise ReplayInfrastructureError("Reference path never reached the representative checkpoint")
        return outcome, checkpoint_identity

    def _run_restored(
        self,
        traci: Any,
        reference_identity: dict[str, Any],
        *,
        simulation_steps: int,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        state = ExperimentState()
        saved_identity: dict[str, Any] = {}

        def save_hook(controller, states, groups, epoch, step, simulation_time):
            if epoch != self.target_decision_epoch:
                return
            identity = self._identity(traci, controller, states, groups, epoch, step, simulation_time)
            self._validate_target(identity)
            validate_checkpoint_identity(reference_identity, identity)
            self.current_stage = "PATH_B_SAVE_CHECKPOINT"
            save_checkpoint(
                traci,
                self.checkpoint_dir,
                controller=controller,
                experiment_state=state.to_dict(),
                metadata=self.metadata,
            )
            saved_identity.update(identity)
            _write_json(self.output_root / "restored" / "saved_checkpoint_identity.json", saved_identity)
            raise _CheckpointPause()

        controller = self._controller(traci, save_hook)
        self.current_stage = "PATH_B_PRECHECKPOINT_START"
        self._start(traci)
        try:
            try:
                self.current_stage = "PATH_B_PRECHECKPOINT_CONTINUATION"
                self._continue(traci, controller, state, simulation_steps=simulation_steps)
            except _CheckpointPause:
                pass
            else:
                raise ReplayInfrastructureError("Checkpoint path did not pause at the representative state")
        finally:
            self.current_stage = "PATH_B_PRECHECKPOINT_CLOSE"
            self._close(traci)

        sumo_state_path = self.checkpoint_dir / "sumo_state.xml"
        saved_sumo_time = self._saved_simulation_time(sumo_state_path)
        self.current_stage = "PATH_B_RESTART_FROM_SAVED_STATE"
        self._start(traci, load_state_path=sumo_state_path, begin_time=saved_sumo_time)
        safety_guard = self._safety_guard(traci)

        def planner(states, groups, epoch, step, simulation_time):
            return PlannerDecision(
                trace=execute_cooperative_comparator_pipeline(states, groups, safety_guard_fn=safety_guard)
            )

        try:
            self.current_stage = "PATH_B_LOAD_STATE"
            restored = load_checkpoint(
                traci,
                self.checkpoint_dir,
                planner_fn=planner,
                safety_guard_fn=safety_guard,
                expected_metadata=self.metadata,
                sumo_state_already_loaded=True,
            )
            self.current_stage = "PATH_B_PYTHON_STATE_RESTORE"
            restored_state = ExperimentState.from_dict(restored.experiment_state)
            traffic = self._traffic_state(traci, list(traci.vehicle.getIDList()))
            groups = build_safe_candidate_groups(traffic)
            loaded_identity = self._identity(
                traci,
                restored.controller,
                traffic,
                groups,
                self.target_decision_epoch,
                restored_state.step,
                restored_state.simulation_time,
            )
            _write_json(self.output_root / "restored" / "loaded_checkpoint_identity.json", loaded_identity)
            self.current_stage = "PATH_B_LOADED_IDENTITY_VALIDATION"
            validate_checkpoint_identity(saved_identity, loaded_identity)
            self.current_stage = "PATH_B_RESTORED_CONTINUATION"
            outcome = self._continue(
                traci,
                restored.controller,
                restored_state,
                simulation_steps=simulation_steps,
                resume_pending_step=True,
            )
        finally:
            self._close(traci)
        return outcome, saved_identity, loaded_identity

    def run(self, *, simulation_steps: int = 480) -> dict[str, Any]:
        self._assert_new_output()
        result: dict[str, Any]
        try:
            import traci

            self.current_stage = "PATH_A"
            reference, reference_identity = self._run_reference(traci, simulation_steps=simulation_steps)
            _write_json(self.output_root / "reference" / "outcome.json", reference)
            _write_json(self.output_root / "reference" / "decision_records.json", reference["decision_records"])
            _write_json(self.output_root / "reference" / "checkpoint_identity.json", reference_identity)
            print("[PATH B CHECKPOINT/RESTORE]", flush=True)
            self.current_stage = "PATH_B"
            restored, saved_identity, loaded_identity = self._run_restored(
                traci, reference_identity, simulation_steps=simulation_steps
            )
            _write_json(self.output_root / "restored" / "outcome.json", restored)
            _write_json(self.output_root / "restored" / "decision_records.json", restored["decision_records"])
            _write_json(self.output_root / "restored" / "saved_checkpoint_identity.json", saved_identity)
            _write_json(self.output_root / "restored" / "loaded_checkpoint_identity.json", loaded_identity)
            comparison = compare_replay_outcomes(reference, restored)
            result = {
                "gate": "REPLAY_EQUIVALENT" if comparison["replay_equivalent"] else "REPLAY_NOT_EQUIVALENT",
                **comparison,
                "source_historical_state": SOURCE_FROZEN_REFERENCE,
                "scenario": SCENARIO_ID,
                "seed": SEED,
                "decision_epoch": TARGET_DECISION_EPOCH,
                "simulation_time": TARGET_SIMULATION_TIME,
                "sumo_version": self.sumo_version,
                "config_hashes": self.config_hashes,
                "controller_checkpoint_hash": _sha256(self.checkpoint_dir / "controller_state.json"),
                "experiment_state_hash": _sha256(self.checkpoint_dir / "experiment_state.json"),
            }
        except Exception as exc:
            result = {
                "gate": "REPLAY_INFRASTRUCTURE_ERROR",
                "replay_equivalent": False,
                "tolerance": REPLAY_ABSOLUTE_TOLERANCE,
                "mismatches": [],
                "error_type": type(exc).__name__,
                "error": str(exc),
                "failure_stage": self.current_stage,
                "traceback": traceback.format_exc(),
            }
        _write_json(self.output_root / "comparison.json", result)
        _write_report(self.output_root / "replay_equivalence_report.md", result)
        return result
