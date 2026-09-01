"""Fail-closed checkpoint primitives for future same-state counterfactual branches."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.controllers.candidate_runtime import CandidateGrantController, PlannerDecision


CHECKPOINT_FILES = {
    "sumo_state": "sumo_state.xml",
    "controller_state": "controller_state.json",
    "experiment_state": "experiment_state.json",
    "metadata": "checkpoint_metadata.json",
}
REQUIRED_METADATA = {
    "schema_version", "scenario", "seed", "simulation_time", "decision_epoch", "candidate_set_hash",
    "r4_candidate_id", "s2_candidate_id", "config_hashes", "source_frozen_decision_reference",
}
DISCRETE_REPLAY_FIELDS = (
    "decision_sequence", "decision_epochs", "candidate_sets", "selected_candidate_ids", "arrived_vehicle_ids", "completion", "grant_events",
    "collision_count", "safety_intervention_count", "termination_reason",
)
NUMERIC_REPLAY_FIELDS = (
    "vehicle_trajectories", "step_records", "waiting_by_vehicle", "speed_by_vehicle", "episode_duration_seconds",
    "aggregate_metrics",
)
REPLAY_ABSOLUTE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class RestoredCheckpoint:
    controller: CandidateGrantController
    experiment_state: dict[str, Any]
    metadata: dict[str, Any]


def _json_copy(value: Any, *, label: str) -> Any:
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not JSON serializable") from exc


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Malformed checkpoint file: {path.name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Checkpoint file must contain an object: {path.name}")
    return value


def validate_checkpoint_metadata(metadata: dict[str, Any], *, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(metadata, dict) or set(metadata) != REQUIRED_METADATA or metadata.get("schema_version") != 1:
        raise ValueError("Malformed checkpoint metadata")
    if not isinstance(metadata["config_hashes"], dict) or not metadata["config_hashes"]:
        raise ValueError("Checkpoint metadata requires non-empty config_hashes")
    if not metadata["candidate_set_hash"] or not metadata["r4_candidate_id"] or not metadata["s2_candidate_id"]:
        raise ValueError("Checkpoint metadata is missing candidate provenance")
    if expected:
        for key, expected_value in expected.items():
            if metadata.get(key) != expected_value:
                raise ValueError(f"Checkpoint metadata mismatch: {key}")
    return _json_copy(metadata, label="checkpoint metadata")


def save_checkpoint(
    traci: Any,
    checkpoint_dir: Path,
    *,
    controller: CandidateGrantController,
    experiment_state: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    """Persist SUMO and Python runtime state. Existing evidence is never overwritten."""
    if checkpoint_dir.exists():
        raise FileExistsError(f"Checkpoint directory already exists: {checkpoint_dir}")
    checked_metadata = validate_checkpoint_metadata(metadata)
    checked_experiment_state = _json_copy(experiment_state, label="experiment state")
    controller_state = controller.checkpoint_state()
    checkpoint_dir.mkdir(parents=True)
    try:
        traci.simulation.saveState(str(checkpoint_dir / CHECKPOINT_FILES["sumo_state"]))
        _write_json(checkpoint_dir / CHECKPOINT_FILES["controller_state"], controller_state)
        _write_json(checkpoint_dir / CHECKPOINT_FILES["experiment_state"], checked_experiment_state)
        _write_json(checkpoint_dir / CHECKPOINT_FILES["metadata"], checked_metadata)
    except Exception:
        # A partial checkpoint is unsafe for replay and must never be treated as restorable.
        raise


def load_checkpoint(
    traci: Any,
    checkpoint_dir: Path,
    *,
    planner_fn: Callable[[list[dict], list[list[str]], int, int, float], PlannerDecision | dict[str, dict]],
    safety_guard_fn: Callable[[dict[str, dict], list[dict]], dict[str, dict]],
    expected_metadata: dict[str, Any],
    sumo_state_already_loaded: bool = False,
) -> RestoredCheckpoint:
    paths = {name: checkpoint_dir / filename for name, filename in CHECKPOINT_FILES.items()}
    if not checkpoint_dir.is_dir() or any(not path.is_file() for path in paths.values()):
        raise ValueError("Incomplete checkpoint")
    metadata = validate_checkpoint_metadata(_read_json(paths["metadata"]), expected=expected_metadata)
    controller_state = _read_json(paths["controller_state"])
    experiment_state = _read_json(paths["experiment_state"])
    controller = CandidateGrantController.from_checkpoint_state(
        controller_state,
        planner_fn=planner_fn,
        safety_guard_fn=safety_guard_fn,
    )
    if not sumo_state_already_loaded:
        traci.simulation.loadState(str(paths["sumo_state"]))
    return RestoredCheckpoint(controller=controller, experiment_state=experiment_state, metadata=metadata)


def _compare_numeric(left: Any, right: Any, *, path: str, tolerance: float, mismatches: list[str]) -> None:
    if isinstance(left, bool) or isinstance(right, bool):
        if left != right:
            mismatches.append(path)
        return
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if abs(float(left) - float(right)) > tolerance:
            mismatches.append(path)
        return
    if isinstance(left, dict) and isinstance(right, dict) and set(left) == set(right):
        for key in left:
            _compare_numeric(left[key], right[key], path=f"{path}.{key}", tolerance=tolerance, mismatches=mismatches)
        return
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            _compare_numeric(a, b, path=f"{path}[{index}]", tolerance=tolerance, mismatches=mismatches)
        return
    if left != right:
        mismatches.append(path)


def compare_replay_outcomes(
    uninterrupted: dict[str, Any],
    restored: dict[str, Any],
    *,
    tolerance: float = REPLAY_ABSOLUTE_TOLERANCE,
) -> dict[str, Any]:
    if tolerance < 0:
        raise ValueError("Replay tolerance must be non-negative")
    missing = [field for field in (*DISCRETE_REPLAY_FIELDS, *NUMERIC_REPLAY_FIELDS) if field not in uninterrupted or field not in restored]
    if missing:
        raise ValueError(f"Replay outcome missing required fields: {', '.join(missing)}")
    mismatches: list[str] = []
    for field in DISCRETE_REPLAY_FIELDS:
        if uninterrupted[field] != restored[field]:
            mismatches.append(field)
    for field in NUMERIC_REPLAY_FIELDS:
        _compare_numeric(uninterrupted[field], restored[field], path=field, tolerance=tolerance, mismatches=mismatches)
    return {"replay_equivalent": not mismatches, "tolerance": tolerance, "mismatches": mismatches}
