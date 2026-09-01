from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, median, stdev

from src.common.config import load_project_config
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.common.metrics import run_artifact_paths
from src.experiments.phase2_formal_batch import (
    REQUIRED_DECISION_RECORD_FIELDS,
    build_paired_comparison,
    summarize_formal_run,
    validate_formal_pair,
    validate_formal_run_result,
    write_csv,
    write_json,
)


FORMAL_MATRIX_BATCH_ID = "batch2_remaining_matrix"
FORMAL_MATRIX_RUN_LABEL = "phase2_formal_batch2"
FORMAL_RESULTS_DIR = Path(load_project_config()["results_dir_path"]) / "phase2_formal"
FORMAL_MATRIX_RESULTS_ROOT = FORMAL_RESULTS_DIR / FORMAL_MATRIX_BATCH_ID
BATCH1_RESULTS_ROOT = FORMAL_RESULTS_DIR / "batch1_seed1"

FORMAL_MATRIX_CONDITIONS = (
    ("S1_BALANCED_MIXED_TURN", 8, (2, 3)),
    ("S2_SIMULTANEOUS_CONFLICT", 8, (1, 2, 3)),
    ("S3_COOPERATIVE_OPPORTUNITY", 8, (2, 3)),
    ("S4_FAIRNESS_PRESSURE", 8, (2, 3)),
    ("S3_COOPERATIVE_OPPORTUNITY", 12, (1, 2, 3)),
    ("S4_FAIRNESS_PRESSURE", 16, (1, 2, 3)),
)
PRIMARY_METRICS = (
    "departed",
    "arrived",
    "completion_rate",
    "throughput",
    "mean_waiting_time",
    "maximum_waiting_time",
    "mean_speed",
    "episode_duration_seconds",
    "collision_count",
)
PAIRED_DELTA_METRICS = (
    "completion_rate_delta",
    "throughput_delta",
    "mean_waiting_time_delta",
    "maximum_waiting_time_delta",
    "mean_speed_delta",
    "episode_duration_delta_seconds",
    "collision_delta",
    "safety_intervention_delta",
)


@dataclass(frozen=True)
class Phase2FormalMatrixRunSpec:
    order: int
    scenario_class: str
    vehicle_count: int
    seed: int
    planner_mode: str
    run_id: str

    @property
    def pair_id(self) -> str:
        return f"{self.scenario_class.lower()}_v{self.vehicle_count}_seed{self.seed}"


def matrix_run_id(scenario_class: str, vehicle_count: int, seed: int, planner_mode: str) -> str:
    return (
        f"{FORMAL_MATRIX_RUN_LABEL}_{scenario_class.lower()}"
        f"_v{vehicle_count}_seed{seed}_{planner_mode.lower()}"
    )


def build_remaining_matrix_plan() -> list[Phase2FormalMatrixRunSpec]:
    plan: list[Phase2FormalMatrixRunSpec] = []
    order = 1
    for scenario_class, vehicle_count, seeds in FORMAL_MATRIX_CONDITIONS:
        for seed in seeds:
            for planner_mode in (DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE):
                plan.append(
                    Phase2FormalMatrixRunSpec(
                        order=order,
                        scenario_class=scenario_class,
                        vehicle_count=vehicle_count,
                        seed=seed,
                        planner_mode=planner_mode,
                        run_id=matrix_run_id(
                            scenario_class,
                            vehicle_count,
                            seed,
                            planner_mode,
                        ),
                    )
                )
                order += 1
    return plan


def matrix_run_target(spec: Phase2FormalMatrixRunSpec) -> Path:
    return FORMAL_MATRIX_RESULTS_ROOT / "runs" / spec.pair_id / spec.run_id


def load_json(path: Path) -> dict | list:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_persisted_formal_run(manifest_row: dict) -> dict:
    formal_dir = Path(manifest_row["formal_results_path"])
    validation = load_json(formal_dir / "formal_validation.json")
    artifacts = run_artifact_paths(manifest_row["run_id"])
    artifact_paths = {
        name: str(formal_dir / path.name)
        for name, path in artifacts.items()
    }
    return {
        "run_id": manifest_row["run_id"],
        "initial_conditions": validation["initial_conditions"],
        "summary": load_json(formal_dir / "summary.json"),
        "artifact_paths": artifact_paths,
        "decision_records": read_jsonl(formal_dir / "decision_records.jsonl"),
    }


def validate_persisted_formal_run(result: dict, spec: Phase2FormalMatrixRunSpec) -> list[str]:
    errors = validate_formal_run_result(result, spec)
    records = result["decision_records"]
    for index, record in enumerate(records, start=1):
        if REQUIRED_DECISION_RECORD_FIELDS - set(record):
            errors.append(f"decision_{index}_incomplete_provenance")
    return errors


def load_completed_batch(root: Path) -> tuple[dict, list[dict]]:
    manifest = load_json(root / "run_manifest.json")
    if manifest.get("status") != "completed_valid":
        raise RuntimeError(f"Batch is not completed_valid: {root}")
    results = [load_persisted_formal_run(row) for row in manifest["runs"]]
    return manifest, results


def _describe(values: list[float]) -> dict:
    numeric = [float(value) for value in values]
    return {
        "n": len(numeric),
        "mean": fmean(numeric) if numeric else 0.0,
        "standard_deviation": stdev(numeric) if len(numeric) > 1 else 0.0,
        "minimum": min(numeric, default=0.0),
        "maximum": max(numeric, default=0.0),
    }


def summarize_conditions(run_summaries: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
    for row in run_summaries:
        grouped[(row["scenario_class"], int(row["vehicle_count"]), row["planner"])].append(row)

    summaries: list[dict] = []
    for (scenario_class, vehicle_count, planner), rows in sorted(grouped.items()):
        total_rows = list(rows)
        if planner == GEMINI_CANDIDATE:
            rows = [row for row in rows if row.get("llm_episode_valid") is True]
        summary = {
            "scenario_class": scenario_class,
            "vehicle_count": vehicle_count,
            "planner": planner,
            "seed_count": len(rows),
            "seeds": sorted(row["seed"] for row in rows),
            "total_llm_episodes": len(total_rows) if planner == GEMINI_CANDIDATE else 0,
            "valid_llm_episodes": len(rows) if planner == GEMINI_CANDIDATE else 0,
            "invalid_llm_episodes": (len(total_rows) - len(rows)) if planner == GEMINI_CANDIDATE else 0,
            "excluded_llm_episodes": (len(total_rows) - len(rows)) if planner == GEMINI_CANDIDATE else 0,
        }
        for metric in PRIMARY_METRICS:
            summary[metric] = _describe([row[metric] for row in rows])
        for metric in (
            "decision_epoch_count",
            "grant_count",
            "gemini_request_count",
            "fallback_count",
            "safety_intervention_count",
            "grant_timeout_count",
            "total_tokens",
        ):
            summary[metric] = _describe([row[metric] for row in rows])
        summaries.append(summary)
    return summaries


def summarize_paired_deltas(pairs: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for pair in pairs:
        grouped[(pair["scenario_class"], int(pair["vehicle_count"]))].append(pair)
    summaries: list[dict] = []
    for (scenario_class, vehicle_count), rows in sorted(grouped.items()):
        summary = {
            "scenario_class": scenario_class,
            "vehicle_count": vehicle_count,
            "seed_count": len(rows),
            "seeds": sorted(row["seed"] for row in rows),
            "initial_demand_signature_matches": all(
                row["initial_demand_signature_match"] for row in rows
            ),
        }
        for metric in PAIRED_DELTA_METRICS:
            summary[metric] = _describe([row[metric] for row in rows])
        summaries.append(summary)
    return summaries


def build_extended_paired_comparison(run_summaries: list[dict]) -> list[dict]:
    comparisons = build_paired_comparison(run_summaries)
    for comparison in comparisons:
        comparison["maximum_waiting_time_delta"] = (
            comparison["gemini_maximum_waiting_time"]
            - comparison["deterministic_maximum_waiting_time"]
        )
        comparison["collision_delta"] = (
            comparison["gemini_collision_count"] - comparison["deterministic_collision_count"]
        )
        comparison["safety_intervention_delta"] = (
            comparison["gemini_safety_interventions"]
            - comparison["deterministic_safety_interventions"]
        )
    return comparisons


def _fairness_context(record: dict, scenario_class: str) -> dict:
    if scenario_class != "S4_FAIRNESS_PRESSURE":
        return {"fairness_pressure_context": False, "fairness_target_waiting_time": None}
    target_states = [
        state
        for state in record.get("privacy_minimised_vehicle_inputs", [])
        if state.get("incoming_edge") == "N" and state.get("outgoing_edge") == "-E"
    ]
    waiting_times = [float(state.get("waiting_time", 0.0)) for state in target_states]
    return {
        "fairness_pressure_context": bool(target_states),
        "fairness_target_waiting_time": max(waiting_times, default=None),
    }


def extract_complete_disagreements(results: list[dict]) -> list[dict]:
    disagreements: list[dict] = []
    for result in results:
        initial = result["initial_conditions"]
        for record in result["decision_records"]:
            if not record.get("candidate_disagreement"):
                continue
            candidate_features = record.get("candidate_features", [])
            states = record.get("privacy_minimised_vehicle_inputs", [])
            selected_features = [
                feature
                for feature in candidate_features
                if feature.get("candidate_id") == record.get("llm_candidate_id")
            ]
            disagreements.append(
                {
                    "run_id": result["run_id"],
                    "scenario_class": initial["scenario_class"],
                    "vehicle_count": initial["vehicle_count"],
                    "seed": initial["seed"],
                    "simulation_time": record.get("simulation_time"),
                    "candidate_set": record.get("candidate_set", []),
                    "candidate_features": candidate_features,
                    "candidate_group_sizes": [
                        feature.get("group_size", 0) for feature in candidate_features
                    ],
                    "deterministic_candidate_id": record.get("deterministic_candidate_id", ""),
                    "gemini_candidate_id": record.get("llm_candidate_id", ""),
                    "gemini_selected_features": selected_features,
                    "aggregate_waiting_time": sum(
                        float(state.get("waiting_time", 0.0)) for state in states
                    ),
                    "maximum_waiting_time": max(
                        (float(state.get("waiting_time", 0.0)) for state in states),
                        default=0.0,
                    ),
                    "eta_features": [
                        state.get("time_to_intersection") for state in states
                    ],
                    "fallback_used": record.get("fallback_used", False),
                    "fallback_reason": record.get("fallback_reason", ""),
                    "safety_interventions": record.get("safety_interventions_during_grant", 0),
                    "actual_granted_group": record.get("grant_vehicle_ids", []),
                    "grant_clearance_reason": record.get("grant_clearance_reason", ""),
                    "grant_duration_seconds": record.get("grant_duration_seconds"),
                    **_fairness_context(record, initial["scenario_class"]),
                }
            )
    return disagreements


def summarize_gemini_decisions(results: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for result in results:
        if result["summary"].get("planner_mode") != GEMINI_CANDIDATE:
            continue
        initial = result["initial_conditions"]
        grouped[(initial["scenario_class"], int(initial["vehicle_count"]))].extend(
            result["decision_records"]
        )

    summaries: list[dict] = []
    for (scenario_class, vehicle_count), records in sorted(grouped.items()):
        attempted = [record for record in records if record.get("provider_request_attempted")]
        comparable = [record for record in records if record.get("candidate_agreement") is not None]
        latencies = [float(record.get("latency_ms") or 0.0) for record in attempted]
        summary = {
            "scenario_class": scenario_class,
            "vehicle_count": vehicle_count,
            "decision_count": len(records),
            "comparable_decision_count": len(comparable),
            "agreement_count": sum(record.get("candidate_agreement") is True for record in comparable),
            "disagreement_count": sum(record.get("candidate_disagreement") is True for record in comparable),
            "provider_request_count": len(attempted),
            "provider_success_count": sum(bool(record.get("provider_request_success")) for record in attempted),
            "parser_success_count": sum(bool(record.get("parser_success")) for record in attempted),
            "fallback_count": sum(bool(record.get("fallback_used")) for record in records),
            "safety_intervention_count": sum(
                int(record.get("safety_interventions_during_grant", 0)) for record in records
            ),
            "prompt_tokens": sum(int(record.get("prompt_tokens") or 0) for record in records),
            "completion_tokens": sum(int(record.get("completion_tokens") or 0) for record in records),
            "total_tokens": sum(int(record.get("total_tokens") or 0) for record in records),
            "latency_ms": _describe(latencies),
        }
        summary["agreement_rate"] = (
            summary["agreement_count"] / len(comparable) if comparable else 0.0
        )
        summary["provider_success_rate"] = (
            summary["provider_success_count"] / len(attempted) if attempted else 0.0
        )
        summary["parser_success_rate"] = (
            summary["parser_success_count"] / len(attempted) if attempted else 0.0
        )
        summary["fallback_rate"] = summary["fallback_count"] / len(records) if records else 0.0
        summary["safety_intervention_rate"] = (
            summary["safety_intervention_count"] / len(records) if records else 0.0
        )
        summaries.append(summary)
    return summaries


def write_complete_matrix_summaries(results: list[dict], output_root: Path) -> dict:
    if output_root.exists():
        raise FileExistsError(f"Complete matrix summary already exists: {output_root}")
    run_summaries = [summarize_formal_run(result) for result in results]
    paired_comparisons = build_extended_paired_comparison(run_summaries)
    condition_summaries = summarize_conditions(run_summaries)
    paired_delta_summaries = summarize_paired_deltas(paired_comparisons)
    gemini_summaries = summarize_gemini_decisions(results)
    disagreements = extract_complete_disagreements(results)
    output_root.mkdir(parents=True, exist_ok=False)
    write_json(output_root / "all_run_summaries.json", run_summaries)
    write_csv(output_root / "all_run_summaries.csv", run_summaries)
    write_json(output_root / "all_paired_comparisons.json", paired_comparisons)
    write_csv(output_root / "all_paired_comparisons.csv", paired_comparisons)
    write_json(output_root / "condition_summaries.json", condition_summaries)
    write_json(output_root / "paired_delta_summaries.json", paired_delta_summaries)
    write_json(output_root / "gemini_decision_summaries.json", gemini_summaries)
    write_json(output_root / "all_disagreements.json", disagreements)
    write_json(
        output_root / "complete_matrix_summary.json",
        {
            "formal_run_count": len(run_summaries),
            "paired_condition_count": len(paired_comparisons),
            "valid_completion_count": sum(
                row["completion_rate"] == 1.0 for row in run_summaries
            ),
            "gemini_request_count": sum(row["provider_request_count"] for row in gemini_summaries),
            "provider_success_count": sum(row["provider_success_count"] for row in gemini_summaries),
            "parser_success_count": sum(row["parser_success_count"] for row in gemini_summaries),
            "fallback_count": sum(row["fallback_count"] for row in gemini_summaries),
            "agreement_count": sum(row["agreement_count"] for row in gemini_summaries),
            "disagreement_count": len(disagreements),
            "prompt_tokens": sum(row["prompt_tokens"] for row in gemini_summaries),
            "completion_tokens": sum(row["completion_tokens"] for row in gemini_summaries),
            "total_tokens": sum(row["total_tokens"] for row in gemini_summaries),
            "collision_count": sum(row["collision_count"] for row in run_summaries),
            "safety_intervention_count": sum(
                row["safety_intervention_count"] for row in run_summaries
            ),
            "grant_timeout_count": sum(row["grant_timeout_count"] for row in run_summaries),
        },
    )
    return {
        "run_summaries": run_summaries,
        "paired_comparisons": paired_comparisons,
        "condition_summaries": condition_summaries,
        "paired_delta_summaries": paired_delta_summaries,
        "gemini_summaries": gemini_summaries,
        "disagreements": disagreements,
    }
