"""Phase 3C orchestration and read-only derived measurements.

The observer derives reports from persisted artefacts only.  It is deliberately
kept outside the controller path so it cannot influence a passage decision.
"""
from __future__ import annotations

import csv
import json
import shutil
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.common.config import load_project_config
from src.common.metrics import run_artifact_paths
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.phase2_closed_loop import run_phase2_closed_loop_episode
from src.experiments.scenario_generator import _initial_demand_signature, _targeted_demand, _write_scenario
from src.llm.request_config import PHASE2_BASE_URL, PHASE2_MODEL, PHASE2_TIMEOUT_SECONDS
from src.safety.route_semantics import supported_route_catalog


PHASE3C_ID = "phase3c_closed_loop_waiting_divergence"
PHASE3C_SCENARIO = "S3_COOPERATIVE_OPPORTUNITY"
PHASE3C_VEHICLE_COUNT = 12
PHASE3C_SEEDS = (1, 2, 3)
STAGE_DETERMINISTIC = "deterministic-feasibility"
STAGE_GEMINI = "gemini-evaluation"


@dataclass(frozen=True)
class Phase3CCondition:
    name: str
    wave_spacing_seconds: int

    @property
    def scenario_definition(self) -> dict:
        return {
            "purpose": "Phase 3C preregistered waiting-pressure challenge",
            "supported_vehicle_counts": [PHASE3C_VEHICLE_COUNT],
            "route_cycle": ["N_W", "E_N", "S_E", "W_S", "N_S", "S_N", "E_S", "W_N"],
            "depart_offsets": [0, 0, 1, 1, 3, 3, 5, 5],
            "wave_spacing_seconds": self.wave_spacing_seconds,
            "departure_jitter_seconds": 1,
            "simulation_duration_seconds": 300,
        }


PHASE3C_CONDITIONS = (
    Phase3CCondition("MODERATE_WAITING_PRESSURE", 9),
    Phase3CCondition("HIGH_WAITING_PRESSURE", 11),
)


@dataclass(frozen=True)
class Phase3CRunSpec:
    condition: Phase3CCondition
    seed: int
    planner_mode: str

    @property
    def run_id(self) -> str:
        return f"{PHASE3C_ID}_{self.condition.name.lower()}_v12_seed{self.seed}_{self.planner_mode.lower()}"

    @property
    def pair_id(self) -> str:
        return f"{self.condition.name.lower()}_v12_seed{self.seed}"


def phase3c_results_root() -> Path:
    return Path(load_project_config()["results_dir_path"]) / PHASE3C_ID


def build_phase3c_plan(stage: str) -> list[Phase3CRunSpec]:
    if stage == STAGE_DETERMINISTIC:
        planners = (DETERMINISTIC_CANDIDATE,)
    elif stage == STAGE_GEMINI:
        planners = (GEMINI_CANDIDATE,)
    else:
        raise ValueError(f"Unknown Phase 3C stage: {stage}")
    return [
        Phase3CRunSpec(condition, seed, planner)
        for condition in PHASE3C_CONDITIONS
        for seed in PHASE3C_SEEDS
        for planner in planners
    ]


def prepare_phase3c_demand(condition: Phase3CCondition, seed: int) -> dict:
    """Generate only the preregistered route/departure schedule for one pair."""
    definition = condition.scenario_definition
    routes, departures = _targeted_demand(definition, seed, PHASE3C_VEHICLE_COUNT)
    movements = {
        route.route_id: route.movement
        for route in supported_route_catalog()
    }
    scenario_id = f"{PHASE3C_ID}_{condition.name.lower()}_v12_seed{seed}"
    generation = _write_scenario(
        scenario_id=scenario_id,
        density_name="phase3c_targeted",
        seed=seed,
        route_ids=routes,
        departure_times=departures,
        duration=300,
        vehicles_per_hour=0,
        extra_config={
            "scenario_class": PHASE3C_SCENARIO,
            "phase3c_condition": condition.name,
            "purpose": definition["purpose"],
            "movement_sequence": [movements[route_id] for route_id in routes],
            "preregistered_wave_spacing_seconds": condition.wave_spacing_seconds,
        },
    )
    # Match the existing Phase 2 initial-condition contract before the runner starts SUMO.
    generation["initial_demand_signature"] = _initial_demand_signature(
        scenario_name=PHASE3C_SCENARIO,
        seed=seed,
        route_ids=routes,
        departure_times=departures,
    )
    scenario_dir = Path(generation["sumocfg_path"]).parent
    (scenario_dir / "generation_config.json").write_text(
        json.dumps(generation, indent=2), encoding="utf-8"
    )
    return generation


def _candidate_descriptor(feature: dict) -> dict:
    movements = list(feature.get("movement_summary", []))
    return {
        "candidate_id": str(feature.get("candidate_id", "")),
        "group_size": int(feature.get("group_size", len(feature.get("vehicle_ids", [])))),
        "aggregate_waiting_time": float(feature.get("aggregate_waiting_time") or 0.0),
        "maximum_waiting_time": float(feature.get("maximum_waiting_time") or 0.0),
        "turn_composition": [str(item.get("movement", "UNKNOWN")) for item in movements],
        "incoming_approaches": [str(item.get("incoming_edge", "")) for item in movements],
    }


def _is_four_right(candidate: dict) -> bool:
    return candidate["group_size"] == 4 and all(move == "RIGHT" for move in candidate["turn_composition"])


def _is_opposite_straight(candidate: dict) -> bool:
    approaches = frozenset(candidate["incoming_approaches"])
    return (
        candidate["group_size"] == 2
        and all(move == "STRAIGHT" for move in candidate["turn_composition"])
        and approaches in {frozenset(("N", "S")), frozenset(("E", "W"))}
    )


def observe_decision_epoch(record: dict) -> dict:
    """Derive a Phase 3C observation without mutating canonical provenance."""
    candidates = [_candidate_descriptor(feature) for feature in record.get("candidate_features", [])]
    right_candidates = [candidate for candidate in candidates if _is_four_right(candidate)]
    straight_candidates = [candidate for candidate in candidates if _is_opposite_straight(candidate)]
    target_right = right_candidates[0] if len(right_candidates) == 1 else None
    target_straight = straight_candidates[0] if len(straight_candidates) == 1 else None
    eligible = target_right is not None and target_straight is not None
    deterministic = str(record.get("deterministic_candidate_id", ""))
    gemini = str(record.get("llm_candidate_id", ""))
    return {
        "run_id": record.get("run_id", ""),
        "planner": record.get("planner", ""),
        "decision_epoch": record.get("decision_epoch"),
        "simulation_time": record.get("simulation_time"),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "candidate_group_sizes": {item["candidate_id"]: item["group_size"] for item in candidates},
        "candidate_aggregate_waiting": {item["candidate_id"]: item["aggregate_waiting_time"] for item in candidates},
        "deterministic_selected_candidate_id": deterministic,
        "gemini_selected_candidate_id": gemini,
        "candidate_agreement": record.get("candidate_agreement"),
        "candidate_disagreement": bool(record.get("candidate_disagreement")),
        "target_four_right_candidate_ids": [item["candidate_id"] for item in right_candidates],
        "target_two_straight_candidate_ids": [item["candidate_id"] for item in straight_candidates],
        "target_four_right_present": target_right is not None,
        "target_two_straight_present": target_straight is not None,
        "both_target_candidates_simultaneously_legal": eligible,
        "target_right_waiting": target_right["aggregate_waiting_time"] if target_right else None,
        "target_straight_waiting": target_straight["aggregate_waiting_time"] if target_straight else None,
        "waiting_contrast_straight_minus_right": (
            target_straight["aggregate_waiting_time"] - target_right["aggregate_waiting_time"]
            if eligible
            else None
        ),
        "eligible_tradeoff_epoch": eligible,
        "target_tradeoff_disagreement": bool(
            eligible
            and record.get("candidate_disagreement")
            and deterministic in {item["candidate_id"] for item in right_candidates}
            and gemini in {item["candidate_id"] for item in straight_candidates}
        ),
        "provider_request_success": bool(record.get("provider_request_success")),
        "parser_success": bool(record.get("parser_success")),
        "fallback_used": bool(record.get("fallback_used")),
        "latency_ms": record.get("latency_ms"),
    }


def _waiting_aggregates(step_records: list[dict]) -> dict:
    by_vehicle: dict[str, tuple[str, float]] = {}
    for row in step_records:
        vehicle_id = str(row.get("vehicle_id", ""))
        if not vehicle_id:
            continue
        waiting = float(row.get("waiting_time") or 0.0)
        approach = str(row.get("incoming_edge", ""))
        prior = by_vehicle.get(vehicle_id)
        if prior is None or waiting > prior[1]:
            by_vehicle[vehicle_id] = (approach, waiting)
    values = [waiting for _, waiting in by_vehicle.values()]
    per_approach: dict[str, list[float]] = {}
    for approach, waiting in by_vehicle.values():
        per_approach.setdefault(approach or "UNKNOWN", []).append(waiting)
    return {
        "waiting_mean_observed": statistics.fmean(values) if values else 0.0,
        "waiting_max_observed": max(values, default=0.0),
        "waiting_sample_sd_observed": statistics.stdev(values) if len(values) >= 2 else 0.0,
        "per_approach_waiting": {
            approach: {
                "vehicle_count": len(items),
                "mean": statistics.fmean(items),
                "maximum": max(items),
                "sample_sd": statistics.stdev(items) if len(items) >= 2 else 0.0,
            }
            for approach, items in sorted(per_approach.items())
        },
    }


def observe_episode(
    decision_records: list[dict],
    summary: dict,
    step_records: list[dict],
) -> dict:
    epochs = [observe_decision_epoch(record) for record in decision_records]
    eligible = [epoch for epoch in epochs if epoch["eligible_tradeoff_epoch"]]
    first = eligible[0] if eligible else None
    observation = {
        "run_id": summary.get("run_id", epochs[0]["run_id"] if epochs else ""),
        "planner": summary.get("planner_mode", epochs[0]["planner"] if epochs else ""),
        "decision_epochs": epochs,
        "eligible_tradeoff_epoch_count": len(eligible),
        "first_eligible_tradeoff_epoch": first["decision_epoch"] if first else None,
        "first_eligible_tradeoff_simulation_time": first["simulation_time"] if first else None,
        "first_eligible_waiting_contrast": first["waiting_contrast_straight_minus_right"] if first else None,
        "planner_disagreement_count": sum(epoch["candidate_disagreement"] for epoch in epochs),
        "target_tradeoff_disagreement_count": sum(epoch["target_tradeoff_disagreement"] for epoch in epochs),
        "mean_speed": summary.get("mean_speed"),
        "episode_duration_seconds": summary.get("episode_duration_seconds"),
        "throughput": summary.get("throughput"),
        "completion_rate": summary.get("completion_rate"),
        "collisions": summary.get("collision_count"),
        "safety_interventions": summary.get("safety_intervention_count", summary.get("safety_override_count")),
        "grant_timeout": summary.get("grant_timeout_count"),
        "llm_episode_valid": summary.get("llm_episode_valid"),
    }
    observation.update(_waiting_aggregates(step_records))
    return observation


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_step_records(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_observer_output(target: Path, result: dict) -> dict:
    paths = result["artifact_paths"]
    observation = observe_episode(
        result.get("decision_records") or read_jsonl(Path(paths["decision_records"])),
        result["summary"],
        read_step_records(Path(paths["step_records"])),
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(observation, indent=2), encoding="utf-8")
    return observation


def stage1_feasibility(observations: list[dict]) -> dict:
    """Predeclared state-emergence gate; it never reads Gemini selections."""
    by_condition: dict[str, list[dict]] = {}
    for observation in observations:
        condition = str(observation.get("condition", ""))
        by_condition.setdefault(condition, []).append(observation)
    eligible_counts = {
        condition: sum(item["eligible_tradeoff_epoch_count"] >= 1 for item in items)
        for condition, items in by_condition.items()
    }
    paired_contrasts = 0
    moderate = {item.get("seed"): item for item in by_condition.get("MODERATE_WAITING_PRESSURE", [])}
    high = {item.get("seed"): item for item in by_condition.get("HIGH_WAITING_PRESSURE", [])}
    for seed in sorted(set(moderate) & set(high)):
        left = moderate[seed].get("first_eligible_waiting_contrast")
        right = high[seed].get("first_eligible_waiting_contrast")
        if left is not None and right is not None and right > left:
            paired_contrasts += 1
    gate_passed = (
        all(eligible_counts.get(condition.name, 0) >= 2 for condition in PHASE3C_CONDITIONS)
        and paired_contrasts >= 2
    )
    return {
        "criterion": {
            "minimum_eligible_runs_per_condition": 2,
            "minimum_matched_seeds_with_high_greater_than_moderate_waiting_contrast": 2,
            "selection_or_traffic_outcomes_used": False,
        },
        "eligible_runs_by_condition": eligible_counts,
        "matched_seeds_with_high_greater_waiting_contrast": paired_contrasts,
        "stage1_gate_passed": gate_passed,
    }


def require_stage2_authorization(*, stage1_report: dict, explicitly_approved: bool) -> None:
    if not explicitly_approved:
        raise PermissionError("Stage 2 requires explicit human approval after Stage 1 review")
    if not bool(stage1_report.get("stage1_gate_passed")):
        raise RuntimeError("STOP_PHASE3C: preregistered state-emergence criterion not met")


def direct_connectivity_gate(api_key: str) -> dict:
    """One bounded native request, used only by a future manually invoked Stage 2."""
    url = f"{PHASE2_BASE_URL}/models/{urllib.parse.quote(PHASE2_MODEL, safe='')}:generateContent?key={api_key}"
    body = {"contents": [{"parts": [{"text": "Return exactly JSON: {\"ok\":true}"}]}], "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 16}}
    started = time.monotonic()
    try:
        request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=PHASE2_TIMEOUT_SECONDS) as response:
            response.read()
            status = response.status
        return {"passed": status == 200, "http_status": status, "latency_ms": round((time.monotonic() - started) * 1000, 2)}
    except urllib.error.HTTPError as error:
        return {"passed": False, "http_status": error.code, "latency_ms": round((time.monotonic() - started) * 1000, 2), "error_type": type(error).__name__}
    except Exception as error:
        return {"passed": False, "http_status": None, "latency_ms": round((time.monotonic() - started) * 1000, 2), "error_type": type(error).__name__, "error_message": str(error).replace(api_key, "[REDACTED]")}


def copy_result_artifacts(result: dict, destination: Path) -> None:
    source = Path(result["artifact_paths"]["run_dir"])
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite Phase 3C evidence: {destination}")
    shutil.copytree(source, destination)


def build_final_comparison(observations: list[dict]) -> list[dict]:
    """Pair independently observed Stage 1 and Stage 2 outputs by initial condition."""
    grouped: dict[tuple[str, int], dict[str, dict]] = {}
    for observation in observations:
        key = (str(observation["condition"]), int(observation["seed"]))
        grouped.setdefault(key, {})[str(observation["planner"])] = observation
    rows: list[dict] = []
    for (condition, seed), pair in sorted(grouped.items()):
        deterministic = pair.get(DETERMINISTIC_CANDIDATE, {})
        gemini = pair.get(GEMINI_CANDIDATE, {})
        rows.append({
            "condition": condition,
            "seed": seed,
            "deterministic_eligible_tradeoff_epoch_count": deterministic.get("eligible_tradeoff_epoch_count"),
            "gemini_eligible_tradeoff_epoch_count": gemini.get("eligible_tradeoff_epoch_count"),
            "gemini_llm_episode_valid": gemini.get("llm_episode_valid"),
            "gemini_target_tradeoff_disagreement_count": gemini.get("target_tradeoff_disagreement_count"),
            "deterministic_completion_rate": deterministic.get("completion_rate"),
            "gemini_completion_rate": gemini.get("completion_rate"),
            "deterministic_mean_speed": deterministic.get("mean_speed"),
            "gemini_mean_speed": gemini.get("mean_speed"),
            "deterministic_waiting_mean_observed": deterministic.get("waiting_mean_observed"),
            "gemini_waiting_mean_observed": gemini.get("waiting_mean_observed"),
            "deterministic_collisions": deterministic.get("collisions"),
            "gemini_collisions": gemini.get("collisions"),
        })
    return rows
