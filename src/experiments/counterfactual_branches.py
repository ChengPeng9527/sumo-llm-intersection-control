"""Preregistered same-state R4/S2 counterfactual continuation runner."""
from __future__ import annotations

import json
import statistics
import traceback
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.controllers.candidate_runtime import (
    DETERMINISTIC_CANDIDATE,
    CandidateGrantController,
    PlannerDecision,
)
from src.controllers.decision_pipeline import build_decision_trace, execute_cooperative_comparator_pipeline
from src.experiments.counterfactual_checkpoint import (
    CHECKPOINT_FILES,
    REPLAY_ABSOLUTE_TOLERANCE,
    load_checkpoint,
    save_checkpoint,
)
from src.experiments.counterfactual_replay import (
    PROJECT_ROOT,
    ExperimentState,
    RealSumoReplayRunner,
    ReplayInfrastructureError,
    _CheckpointPause,
    _candidate_ids,
    _read_jsonl,
    _sha256,
    _write_json,
    candidate_set_hash,
    validate_checkpoint_identity,
)
from src.llm.postprocessor import apply_interface_rule
from src.llm.candidate_selector import build_candidate_selection_context
from src.safety.cooperative_comparator import (
    build_decisions_from_selection,
    select_candidate_group,
)


DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT / "results" / "counterfactual_validation" / "s3_r4_vs_s2_branches"
)
REPLAY_GATE_PATH = (
    PROJECT_ROOT
    / "results"
    / "counterfactual_validation"
    / "replay_equivalence_attempt3"
    / "comparison.json"
)
FROZEN_RUN_ROOT = PROJECT_ROOT / "results" / "phase2_formal" / "batch2_remaining_matrix" / "runs"
VEHICLE_COUNT = 12
TARGET_DECISION_EPOCH = 3
BRANCHES = ("R4", "S2")
PRIMARY_NUMERIC_FIELDS = (
    "total_waiting_time",
    "mean_waiting_time",
    "maximum_waiting_time",
    "episode_duration_seconds",
)


@dataclass(frozen=True)
class HistoricalBranchSpec:
    seed: int
    scenario_id: str
    simulation_time: float
    r4_candidate_id: str
    s2_candidate_id: str


HISTORICAL_STATES = (
    HistoricalBranchSpec(
        seed=1,
        scenario_id="phase2_s3_cooperative_opportunity_v12_seed1",
        simulation_time=21.0,
        r4_candidate_id=(
            "phase2_s3_cooperative_opportunity_v12_seed1_1_10|"
            "phase2_s3_cooperative_opportunity_v12_seed1_1_11|"
            "phase2_s3_cooperative_opportunity_v12_seed1_1_8|"
            "phase2_s3_cooperative_opportunity_v12_seed1_1_9"
        ),
        s2_candidate_id=(
            "phase2_s3_cooperative_opportunity_v12_seed1_1_4|"
            "phase2_s3_cooperative_opportunity_v12_seed1_1_5"
        ),
    ),
    HistoricalBranchSpec(
        seed=2,
        scenario_id="phase2_s3_cooperative_opportunity_v12_seed2",
        simulation_time=23.0,
        r4_candidate_id=(
            "phase2_s3_cooperative_opportunity_v12_seed2_2_10|"
            "phase2_s3_cooperative_opportunity_v12_seed2_2_11|"
            "phase2_s3_cooperative_opportunity_v12_seed2_2_8|"
            "phase2_s3_cooperative_opportunity_v12_seed2_2_9"
        ),
        s2_candidate_id=(
            "phase2_s3_cooperative_opportunity_v12_seed2_2_4|"
            "phase2_s3_cooperative_opportunity_v12_seed2_2_5"
        ),
    ),
    HistoricalBranchSpec(
        seed=3,
        scenario_id="phase2_s3_cooperative_opportunity_v12_seed3",
        simulation_time=20.0,
        r4_candidate_id=(
            "phase2_s3_cooperative_opportunity_v12_seed3_3_11|"
            "phase2_s3_cooperative_opportunity_v12_seed3_3_10|"
            "phase2_s3_cooperative_opportunity_v12_seed3_3_9|"
            "phase2_s3_cooperative_opportunity_v12_seed3_3_8"
        ),
        s2_candidate_id=(
            "phase2_s3_cooperative_opportunity_v12_seed3_3_4|"
            "phase2_s3_cooperative_opportunity_v12_seed3_3_5"
        ),
    ),
)


def _frozen_record_path(spec: HistoricalBranchSpec, planner: str) -> Path:
    run_root = FROZEN_RUN_ROOT / f"s3_cooperative_opportunity_v12_seed{spec.seed}"
    matches = sorted(run_root.glob(f"*_{planner}/decision_records.jsonl"))
    if len(matches) != 1:
        raise ReplayInfrastructureError(
            f"Expected one frozen {planner} decision record for seed {spec.seed}"
        )
    return matches[0]


def _record_at_target(path: Path) -> dict[str, Any]:
    matches = [
        row
        for row in _read_jsonl(path)
        if int(row.get("decision_epoch", -1)) == TARGET_DECISION_EPOCH
    ]
    if len(matches) != 1:
        raise ReplayInfrastructureError(f"Expected one epoch-3 record: {path}")
    return matches[0]


def load_historical_state(spec: HistoricalBranchSpec) -> dict[str, Any]:
    deterministic_path = _frozen_record_path(spec, "deterministic_candidate")
    gemini_path = _frozen_record_path(spec, "gemini_candidate")
    deterministic = _record_at_target(deterministic_path)
    gemini = _record_at_target(gemini_path)
    shared_fields = ("candidate_set", "candidate_features", "privacy_minimised_vehicle_inputs")
    if any(deterministic.get(field) != gemini.get(field) for field in shared_fields):
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} is not a matched pre-decision state")
    if float(deterministic.get("simulation_time", -1.0)) != spec.simulation_time:
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} simulation time has drifted")
    candidate_ids = [row["candidate_id"] for row in deterministic["candidate_set"]]
    if deterministic.get("deterministic_candidate_id") != spec.r4_candidate_id:
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} R4 candidate has drifted")
    if gemini.get("llm_candidate_id") != spec.s2_candidate_id:
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} S2 candidate has drifted")
    if spec.r4_candidate_id not in candidate_ids or spec.s2_candidate_id not in candidate_ids:
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} branch candidate is not legal")
    if not (
        gemini.get("provider_request_success") is True
        and gemini.get("parser_success") is True
        and gemini.get("fallback_used") is False
    ):
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} Gemini observation is invalid")
    movements = {
        row["candidate_id"]: [entry["movement"] for entry in row["movement_summary"]]
        for row in deterministic["candidate_features"]
    }
    if movements.get(spec.r4_candidate_id) != ["RIGHT"] * 4:
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} R4 composition is invalid")
    if movements.get(spec.s2_candidate_id) != ["STRAIGHT"] * 2:
        raise ReplayInfrastructureError(f"Frozen seed {spec.seed} S2 composition is invalid")
    return {
        "candidate_ids": candidate_ids,
        "candidate_set_hash": candidate_set_hash(candidate_ids),
        "r4_candidate_id": spec.r4_candidate_id,
        "s2_candidate_id": spec.s2_candidate_id,
        "deterministic_record_path": str(deterministic_path.relative_to(PROJECT_ROOT)),
        "gemini_record_path": str(gemini_path.relative_to(PROJECT_ROOT)),
        "privacy_minimised_vehicle_inputs": deterministic["privacy_minimised_vehicle_inputs"],
        "candidate_features": deterministic["candidate_features"],
        "source_frozen_decision_reference": (
            f"Frozen Phase2 S3-12V seed {spec.seed}, epoch {TARGET_DECISION_EPOCH}, "
            f"simulation time {spec.simulation_time:.1f} s"
        ),
    }


def validate_live_historical_state(
    representative: dict[str, Any],
    vehicle_states: list[dict],
    candidate_groups: list[list[str]],
) -> None:
    local_state, candidate_features, _ = build_candidate_selection_context(
        vehicle_states, candidate_groups
    )
    if local_state != representative["privacy_minimised_vehicle_inputs"]:
        raise ReplayInfrastructureError("Live checkpoint traffic state does not match frozen Phase2")
    if candidate_features != representative["candidate_features"]:
        raise ReplayInfrastructureError("Live checkpoint candidate features do not match frozen Phase2")


def verify_replay_gate(path: Path = REPLAY_GATE_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReplayInfrastructureError(f"Replay-equivalence gate is unavailable: {path}") from exc
    if not (
        value.get("gate") == "REPLAY_EQUIVALENT"
        and value.get("replay_equivalent") is True
        and value.get("mismatches") == []
        and float(value.get("tolerance", -1.0)) == REPLAY_ABSOLUTE_TOLERANCE
    ):
        raise ReplayInfrastructureError("Replay-equivalence attempt3 has not passed the frozen gate")
    return value


def config_hashes_for_scenario(scenario_id: str) -> dict[str, str]:
    scenario_root = PROJECT_ROOT / "simulation" / "generated_routes" / scenario_id
    paths = {
        "network": PROJECT_ROOT / "net.net.xml",
        "scenario_routes": scenario_root / "routes.xml",
        "scenario_sumocfg": scenario_root / "simulation.sumocfg",
        "scenario_generation_config": scenario_root / "generation_config.json",
        "project_config": PROJECT_ROOT / "config" / "project_config.yaml",
        "experiment_matrix": PROJECT_ROOT / "config" / "experiment_matrix.yaml",
        "route_conflicts": PROJECT_ROOT / "config" / "route_conflicts.yaml",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise ReplayInfrastructureError(f"Counterfactual configuration is missing: {missing}")
    return {name: _sha256(path) for name, path in paths.items()}


def execute_forced_legal_candidate_pipeline(
    vehicle_states: list[dict],
    candidate_groups: list[list[str]],
    forced_candidate_id: str,
    *,
    historical_source: str,
    safety_guard_fn: Callable[[dict[str, dict], list[dict]], dict[str, dict]],
) -> dict[str, dict]:
    group_by_id = {"|".join(group): tuple(group) for group in candidate_groups}
    if forced_candidate_id not in group_by_id:
        raise ReplayInfrastructureError(f"Forced candidate is not legal: {forced_candidate_id}")
    selected_vehicle_ids = group_by_id[forced_candidate_id]
    deterministic = select_candidate_group(vehicle_states, candidate_groups)
    decisions = build_decisions_from_selection(vehicle_states, selected_vehicle_ids)
    trace = build_decision_trace(
        vehicle_states,
        decisions,
        decisions,
        llm_meta={
            "decision_source": "COUNTERFACTUAL_INTERVENTION",
            "candidate_groups": tuple(tuple(group) for group in candidate_groups),
            "candidate_ranking": deterministic.ranking_trace(),
            "selected_candidate_id": forced_candidate_id,
            "selected_vehicle_ids": selected_vehicle_ids,
            "candidate_selection_reason": "preregistered_single_legal_candidate_intervention",
            "deterministic_candidate_id": deterministic.selected_candidate_id,
            "final_selected_candidate": forced_candidate_id,
            "selection_source": f"FORCED_{historical_source}",
            "forced_candidate_legality": True,
            "forced_action_count": 1,
        },
    )
    for entry in trace.values():
        entry["postprocessed_decision"] = entry["validated_llm_decision"]
        entry["final_decision"] = entry["validated_llm_decision"]
    trace = apply_interface_rule(trace, vehicle_states, target_field="postprocessed_decision")
    for entry in trace.values():
        if entry["outside_control_zone_rule_applied"]:
            entry["final_decision"] = "FREE"
    return safety_guard_fn(trace, vehicle_states)


class SingleForcedPlanner:
    """Force one preregistered legal choice, then permanently use the comparator."""

    def __init__(
        self,
        *,
        forced_candidate_id: str,
        historical_source: str,
        expected_candidate_set_hash: str,
        target_epoch: int,
        safety_guard_fn: Callable[[dict[str, dict], list[dict]], dict[str, dict]],
    ) -> None:
        self.forced_candidate_id = forced_candidate_id
        self.historical_source = historical_source
        self.expected_candidate_set_hash = expected_candidate_set_hash
        self.target_epoch = target_epoch
        self.safety_guard_fn = safety_guard_fn
        self.forced_action_count = 0
        self.provider_calls = 0

    def __call__(
        self,
        vehicle_states: list[dict],
        candidate_groups: list[list[str]],
        epoch: int,
        step: int,
        simulation_time: float,
    ) -> PlannerDecision:
        del step, simulation_time
        if self.forced_action_count == 0:
            if epoch != self.target_epoch:
                raise ReplayInfrastructureError("Restored branch did not begin at the intervention epoch")
            observed_hash = candidate_set_hash(_candidate_ids(candidate_groups))
            if observed_hash != self.expected_candidate_set_hash:
                raise ReplayInfrastructureError("Intervention candidate set does not match checkpoint provenance")
            trace = execute_forced_legal_candidate_pipeline(
                vehicle_states,
                candidate_groups,
                self.forced_candidate_id,
                historical_source=self.historical_source,
                safety_guard_fn=self.safety_guard_fn,
            )
            self.forced_action_count = 1
            return PlannerDecision(trace=trace)
        if epoch <= self.target_epoch:
            raise ReplayInfrastructureError("Repeated intervention epoch is invalid")
        return PlannerDecision(
            trace=execute_cooperative_comparator_pipeline(
                vehicle_states,
                candidate_groups,
                safety_guard_fn=self.safety_guard_fn,
            )
        )


def _checkpoint_hashes(checkpoint_dir: Path) -> dict[str, str]:
    paths = {name: checkpoint_dir / filename for name, filename in CHECKPOINT_FILES.items()}
    if any(not path.is_file() for path in paths.values()):
        raise ReplayInfrastructureError("Counterfactual checkpoint is incomplete")
    return {name: _sha256(path) for name, path in paths.items()}


def _route_approaches(routes_path: Path) -> dict[str, str]:
    try:
        root = ET.parse(routes_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise ReplayInfrastructureError(f"Cannot parse route provenance: {routes_path}") from exc
    route_edges = {
        route.attrib["id"]: route.attrib["edges"].split()[0]
        for route in root.findall("route")
        if "id" in route.attrib and "edges" in route.attrib
    }
    return {
        vehicle.attrib["id"]: route_edges[vehicle.attrib["route"]]
        for vehicle in root.findall("vehicle")
        if vehicle.attrib.get("route") in route_edges
    }


def branch_summary(
    outcome: dict[str, Any],
    *,
    routes_path: Path,
    forced_candidate_id: str,
    historical_source: str,
    forced_action_count: int,
) -> dict[str, Any]:
    waits = [float(value) for value in outcome["waiting_by_vehicle"].values()]
    approach_by_vehicle = _route_approaches(routes_path)
    per_approach: dict[str, list[float]] = {}
    for vehicle_id, wait in outcome["waiting_by_vehicle"].items():
        approach = approach_by_vehicle.get(vehicle_id, "UNKNOWN")
        per_approach.setdefault(approach, []).append(float(wait))
    arrival_times = {
        row["vehicle_id"]: float(row["simulation_time"])
        for row in outcome.get("events", [])
        if row.get("event_type") == "arrived"
    }
    return {
        "completion": bool(outcome["completion"]),
        "throughput": len(outcome["arrived_vehicle_ids"]),
        "total_waiting_time": sum(waits),
        "mean_waiting_time": float(outcome["aggregate_metrics"]["mean_waiting_time"]),
        "maximum_waiting_time": float(outcome["aggregate_metrics"]["maximum_waiting_time"]),
        "episode_duration_seconds": float(outcome["episode_duration_seconds"]),
        "waiting_sample_sd": statistics.stdev(waits) if len(waits) > 1 else 0.0,
        "per_approach_waiting": {
            approach: {
                "total": sum(values),
                "mean": statistics.fmean(values),
                "maximum": max(values),
            }
            for approach, values in sorted(per_approach.items())
        },
        "mean_speed": float(outcome["aggregate_metrics"]["mean_speed"]),
        "arrival_sequence": list(outcome["arrived_vehicle_ids"]),
        "arrival_times": arrival_times,
        "decision_count": len(outcome["decision_records"]),
        "subsequent_decision_count": sum(
            int(row["decision_epoch"]) > TARGET_DECISION_EPOCH
            for row in outcome["decision_records"]
        ),
        "subsequent_selected_candidates": [
            row["selected_candidate_id"]
            for row in outcome["decision_records"]
            if int(row["decision_epoch"]) > TARGET_DECISION_EPOCH
        ],
        "collision_count": int(outcome["collision_count"]),
        "safety_intervention_count": int(outcome["safety_intervention_count"]),
        "grant_timeout_count": sum(
            row.get("clearance_reason") == "GRANT_TIMEOUT" for row in outcome["grant_events"]
        ),
        "forced_candidate_id": forced_candidate_id,
        "forced_candidate_legality": True,
        "forced_action_count": forced_action_count,
        "historical_source": historical_source,
    }


def paired_comparison(seed: int, r4: dict[str, Any], s2: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "total_waiting_time",
        "mean_waiting_time",
        "maximum_waiting_time",
        "episode_duration_seconds",
        "waiting_sample_sd",
        "mean_speed",
        "throughput",
    )
    return {
        "seed": seed,
        "R4": {field: r4[field] for field in ("completion", *fields)},
        "S2": {field: s2[field] for field in ("completion", *fields)},
        "S2_minus_R4": {
            "completion": int(s2["completion"]) - int(r4["completion"]),
            **{field: float(s2[field]) - float(r4[field]) for field in fields},
        },
    }


def classify_primary_outcomes(comparisons: list[dict[str, Any]]) -> str:
    if len(comparisons) != 3:
        return "INCONCLUSIVE"
    for row in comparisons:
        if not isinstance(row.get("R4"), dict) or not isinstance(row.get("S2"), dict):
            return "INCONCLUSIVE"
    all_minimal = all(
        row["R4"]["completion"] == row["S2"]["completion"]
        and all(
            abs(float(row["S2"][field]) - float(row["R4"][field])) <= REPLAY_ABSOLUTE_TOLERANCE
            for field in PRIMARY_NUMERIC_FIELDS
        )
        for row in comparisons
    )
    if all_minimal:
        return "MINIMAL_SYSTEM_CONSEQUENCE"

    def consistently_better(preferred: str, other: str) -> bool:
        return all(
            int(row[preferred]["completion"]) >= int(row[other]["completion"])
            and all(
                float(row[preferred][field]) <= float(row[other][field]) + REPLAY_ABSOLUTE_TOLERANCE
                for field in PRIMARY_NUMERIC_FIELDS
            )
            and (
                int(row[preferred]["completion"]) > int(row[other]["completion"])
                or any(
                    float(row[preferred][field]) < float(row[other][field]) - REPLAY_ABSOLUTE_TOLERANCE
                    for field in PRIMARY_NUMERIC_FIELDS
                )
            )
            for row in comparisons
        )

    if consistently_better("S2", "R4"):
        return "S2_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES"
    if consistently_better("R4", "S2"):
        return "R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES"
    return "MIXED_TRADEOFF"


class CounterfactualSeedRunner(RealSumoReplayRunner):
    def __init__(self, *, sumo_binary: Path, seed_root: Path, spec: HistoricalBranchSpec):
        self.sumo_binary = Path(sumo_binary)
        self.output_root = Path(seed_root)
        self.spec = spec
        self.scenario_id = spec.scenario_id
        self.scenario_class = "S3_COOPERATIVE_OPPORTUNITY"
        self.seed = spec.seed
        self.vehicle_count = VEHICLE_COUNT
        self.target_decision_epoch = TARGET_DECISION_EPOCH
        self.target_simulation_time = spec.simulation_time
        self.scenario_root = PROJECT_ROOT / "simulation" / "generated_routes" / spec.scenario_id
        self.scenario_config = self.scenario_root / "simulation.sumocfg"
        self.representative = load_historical_state(spec)
        self.config_hashes = config_hashes_for_scenario(spec.scenario_id)
        self.metadata = {
            "schema_version": 1,
            "scenario": spec.scenario_id,
            "seed": spec.seed,
            "simulation_time": spec.simulation_time,
            "decision_epoch": TARGET_DECISION_EPOCH,
            "candidate_set_hash": self.representative["candidate_set_hash"],
            "r4_candidate_id": spec.r4_candidate_id,
            "s2_candidate_id": spec.s2_candidate_id,
            "config_hashes": self.config_hashes,
            "source_frozen_decision_reference": self.representative[
                "source_frozen_decision_reference"
            ],
        }
        self.checkpoint_dir = self.output_root / "checkpoint"
        self.sumo_version: Any = None
        self.current_stage = "INITIALIZATION"

    def _new_controller(
        self,
        traci: Any,
        planner: Callable,
        *,
        run_id: str,
        hook: Callable | None = None,
    ) -> CandidateGrantController:
        return CandidateGrantController(
            planner_mode=DETERMINISTIC_CANDIDATE,
            planner_fn=planner,
            safety_guard_fn=self._safety_guard(traci),
            run_id=run_id,
            scenario_id=self.scenario_id,
            vehicle_count=self.vehicle_count,
            seed=self.seed,
            before_planner_hook=hook,
        )

    def prepare_checkpoint(self, traci: Any, *, simulation_steps: int) -> tuple[dict, dict]:
        state = ExperimentState()
        identity: dict[str, Any] = {}
        safety_guard = self._safety_guard(traci)

        def planner(states, groups, epoch, step, simulation_time):
            return PlannerDecision(
                trace=execute_cooperative_comparator_pipeline(
                    states, groups, safety_guard_fn=safety_guard
                )
            )

        def hook(controller, states, groups, epoch, step, simulation_time):
            if epoch != self.target_decision_epoch:
                return
            observed = self._identity(traci, controller, states, groups, epoch, step, simulation_time)
            self._validate_target(observed)
            validate_live_historical_state(self.representative, states, groups)
            save_checkpoint(
                traci,
                self.checkpoint_dir,
                controller=controller,
                experiment_state=state.to_dict(),
                metadata=self.metadata,
            )
            identity.update(observed)
            _write_json(self.output_root / "checkpoint_identity.json", identity)
            raise _CheckpointPause()

        controller = self._new_controller(
            traci, planner, run_id=f"counterfactual_seed{self.seed}_checkpoint", hook=hook
        )
        self._start(traci)
        try:
            try:
                self._continue(traci, controller, state, simulation_steps=simulation_steps)
            except _CheckpointPause:
                pass
            else:
                raise ReplayInfrastructureError("Historical intervention checkpoint was not reached")
        finally:
            self._close(traci)
        hashes = _checkpoint_hashes(self.checkpoint_dir)
        _write_json(self.output_root / "checkpoint_hashes.json", hashes)
        return identity, hashes

    def run_branch(
        self,
        traci: Any,
        *,
        branch: str,
        checkpoint_identity: dict[str, Any],
        checkpoint_hashes: dict[str, str],
        simulation_steps: int,
    ) -> dict[str, Any]:
        if branch not in BRANCHES:
            raise ValueError(f"Unsupported counterfactual branch: {branch}")
        branch_dir = self.output_root / branch
        branch_dir.mkdir()
        if _checkpoint_hashes(self.checkpoint_dir) != checkpoint_hashes:
            raise ReplayInfrastructureError("Checkpoint changed between paired branches")
        forced_candidate_id = (
            self.spec.r4_candidate_id if branch == "R4" else self.spec.s2_candidate_id
        )
        historical_source = "DETERMINISTIC_R4" if branch == "R4" else "OBSERVED_GEMINI_S2"
        sumo_state_path = self.checkpoint_dir / CHECKPOINT_FILES["sumo_state"]
        saved_sumo_time = self._saved_simulation_time(sumo_state_path)
        controller: CandidateGrantController | None = None
        state: ExperimentState | None = None
        planner: SingleForcedPlanner | None = None
        try:
            self._start(traci, load_state_path=sumo_state_path, begin_time=saved_sumo_time)
            safety_guard = self._safety_guard(traci)
            planner = SingleForcedPlanner(
                forced_candidate_id=forced_candidate_id,
                historical_source=historical_source,
                expected_candidate_set_hash=self.representative["candidate_set_hash"],
                target_epoch=self.target_decision_epoch,
                safety_guard_fn=safety_guard,
            )
            restored = load_checkpoint(
                traci,
                self.checkpoint_dir,
                planner_fn=planner,
                safety_guard_fn=safety_guard,
                expected_metadata=self.metadata,
                sumo_state_already_loaded=True,
            )
            controller = restored.controller
            state = ExperimentState.from_dict(restored.experiment_state)
            traffic = self._traffic_state(traci, list(traci.vehicle.getIDList()))
            from src.safety.candidate_groups import build_safe_candidate_groups

            groups = build_safe_candidate_groups(traffic)
            loaded_identity = self._identity(
                traci,
                controller,
                traffic,
                groups,
                self.target_decision_epoch,
                state.step,
                state.simulation_time,
            )
            validate_checkpoint_identity(checkpoint_identity, loaded_identity)
            _write_json(branch_dir / "loaded_checkpoint_identity.json", loaded_identity)
            controller.run_id = f"counterfactual_seed{self.seed}_{branch.lower()}"
            outcome = self._continue(
                traci,
                controller,
                state,
                simulation_steps=simulation_steps,
                resume_pending_step=True,
            )
            outcome["events"] = state.events
            if planner.forced_action_count != 1:
                raise ReplayInfrastructureError("Branch did not execute exactly one forced action")
            forced_records = [
                row
                for row in outcome["decision_records"]
                if str(row.get("selection_source", "")).startswith("FORCED_")
            ]
            if len(forced_records) != 1:
                raise ReplayInfrastructureError("Forced-action provenance count is not exactly one")
            if forced_records[0]["decision_epoch"] != self.target_decision_epoch:
                raise ReplayInfrastructureError("Forced action occurred at the wrong decision epoch")
            if any(
                row.get("selection_source") != "DETERMINISTIC_COMPARATOR"
                for row in outcome["decision_records"]
                if int(row["decision_epoch"]) > self.target_decision_epoch
            ):
                raise ReplayInfrastructureError("Post-intervention policy was not deterministic")
            summary = branch_summary(
                outcome,
                routes_path=self.scenario_root / "routes.xml",
                forced_candidate_id=forced_candidate_id,
                historical_source=historical_source,
                forced_action_count=planner.forced_action_count,
            )
            metadata = {
                "scenario": self.scenario_id,
                "seed": self.seed,
                "decision_epoch": self.target_decision_epoch,
                "simulation_time": self.target_simulation_time,
                "branch": branch,
                "checkpoint_hashes": checkpoint_hashes,
                "candidate_set_hash": self.representative["candidate_set_hash"],
                "forced_candidate_id": forced_candidate_id,
                "forced_candidate_legality": True,
                "historical_source": historical_source,
                "forced_action_count": planner.forced_action_count,
                "post_intervention_policy": DETERMINISTIC_CANDIDATE,
                "provider_calls": 0,
                "config_hashes": self.config_hashes,
            }
            _write_json(branch_dir / "summary.json", summary)
            _write_json(branch_dir / "step_records.json", outcome["step_records"])
            _write_json(branch_dir / "vehicle_trajectories.json", outcome["vehicle_trajectories"])
            _write_json(branch_dir / "decision_records.json", outcome["decision_records"])
            _write_json(branch_dir / "grant_events.json", outcome["grant_events"])
            _write_json(branch_dir / "branch_metadata.json", metadata)
            return summary
        except Exception as exc:
            failure = {
                "branch": branch,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "forced_action_count": planner.forced_action_count if planner else 0,
                "decision_records": controller.decision_records if controller else [],
                "step_records": state.step_records if state else [],
            }
            _write_json(branch_dir / "failure.json", failure)
            raise
        finally:
            self._close(traci)


class SameStateCounterfactualRunner:
    def __init__(self, *, sumo_binary: Path, output_root: Path = DEFAULT_OUTPUT_ROOT):
        self.sumo_binary = Path(sumo_binary)
        self.output_root = Path(output_root)

    def _assert_preflight(self) -> dict[str, Any]:
        if self.output_root.exists():
            raise FileExistsError(f"Counterfactual output root already exists: {self.output_root}")
        if not self.sumo_binary.is_file():
            raise ReplayInfrastructureError(f"SUMO binary is missing: {self.sumo_binary}")
        gate = verify_replay_gate()
        for spec in HISTORICAL_STATES:
            load_historical_state(spec)
        return gate

    def run(self, *, simulation_steps: int = 480) -> dict[str, Any]:
        gate = self._assert_preflight()
        self.output_root.mkdir(parents=True)
        _write_json(
            self.output_root / "study_metadata.json",
            {
                "research_question": (
                    "From the same pre-decision state, what downstream consequences follow from "
                    "forcing observed S2 rather than deterministic R4?"
                ),
                "historical_seeds": [spec.seed for spec in HISTORICAL_STATES],
                "branches": list(BRANCHES),
                "scientific_continuation_runs": 6,
                "checkpoint_preparation_sessions": 3,
                "provider_calls": 0,
                "replay_gate": gate,
                "replay_gate_sha256": _sha256(REPLAY_GATE_PATH),
                "interpretation_categories": [
                    "S2_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES",
                    "R4_CONSISTENTLY_BETTER_ON_PRIMARY_OUTCOMES",
                    "MIXED_TRADEOFF",
                    "MINIMAL_SYSTEM_CONSEQUENCE",
                    "INCONCLUSIVE",
                ],
            },
        )
        import traci

        comparisons: list[dict[str, Any]] = []
        for spec in HISTORICAL_STATES:
            seed_root = self.output_root / f"seed{spec.seed}"
            seed_root.mkdir()
            runner = CounterfactualSeedRunner(
                sumo_binary=self.sumo_binary, seed_root=seed_root, spec=spec
            )
            checkpoint_identity, checkpoint_hashes = runner.prepare_checkpoint(
                traci, simulation_steps=simulation_steps
            )
            summaries = {
                branch: runner.run_branch(
                    traci,
                    branch=branch,
                    checkpoint_identity=checkpoint_identity,
                    checkpoint_hashes=checkpoint_hashes,
                    simulation_steps=simulation_steps,
                )
                for branch in BRANCHES
            }
            comparison = paired_comparison(spec.seed, summaries["R4"], summaries["S2"])
            _write_json(seed_root / "comparison.json", comparison)
            comparisons.append(comparison)
        mean_differences = {
            field: statistics.fmean(row["S2_minus_R4"][field] for row in comparisons)
            for field in (
                "mean_waiting_time",
                "maximum_waiting_time",
                "episode_duration_seconds",
                "mean_speed",
            )
        }
        result = {
            "valid_seed_pairs": len(comparisons),
            "paired_comparisons": comparisons,
            "descriptive_mean_S2_minus_R4": mean_differences,
            "interpretation": classify_primary_outcomes(comparisons),
            "provider_calls": 0,
            "scientific_continuation_runs": 6,
        }
        _write_json(self.output_root / "paired_analysis.json", result)
        self._write_report(result)
        return result

    def _write_report(self, result: dict[str, Any]) -> None:
        lines = [
            "# Same-State S3 R4 versus S2 Counterfactual Report",
            "",
            f"- Valid paired seeds: `{result['valid_seed_pairs']}/3`",
            f"- Interpretation: `{result['interpretation']}`",
            "- Gemini/API calls: `0`",
            "",
            "This experiment estimates local single-action intervention effects within three replayed historical states. It does not evaluate the complete Gemini policy or establish general planner superiority.",
            "",
            "## Paired results",
            "",
            "| Seed | Metric | R4 | S2 | S2-R4 |",
            "|---:|---|---:|---:|---:|",
        ]
        for row in result["paired_comparisons"]:
            for field in (
                "mean_waiting_time",
                "maximum_waiting_time",
                "episode_duration_seconds",
                "mean_speed",
            ):
                lines.append(
                    f"| {row['seed']} | {field} | {row['R4'][field]:.6f} | "
                    f"{row['S2'][field]:.6f} | {row['S2_minus_R4'][field]:+.6f} |"
                )
        (self.output_root / "counterfactual_report.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
