from __future__ import annotations

import csv
import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common import CONFIG
from src.common.metrics import calculate_summary, run_artifact_paths, write_json, write_jsonl
from src.experiments import canonical_prompt_revalidation as cpr

PROJECT_ROOT = Path(CONFIG["project_root"])
FINAL_OUTPUT_ROOT = PROJECT_ROOT / "results" / "prompt_development" / "canonical_prompt_final_revalidation_v1"
PROMPT_SOURCE_ROOT = PROJECT_ROOT / "results" / "prompt_development" / "canonical_prompt_selection_v1" / "prompt_candidates"
DEVELOPMENT_BATCH_PLANS = [
    (404, ("P1_BASELINE", "P2_STRUCTURED", "P3_COOPERATIVE_OBJECTIVE")),
    (505, ("P2_STRUCTURED", "P3_COOPERATIVE_OBJECTIVE", "P1_BASELINE")),
    (606, ("P3_COOPERATIVE_OBJECTIVE", "P1_BASELINE", "P2_STRUCTURED")),
]
DEFAULT_VEHICLE_COUNT = 4
DEFAULT_DENSITY = "low"
DEFAULT_LLM_MODE = "real"
DEFAULT_DECISION_INTERVAL = 1
DEFAULT_COOLDOWN_SECONDS = 25


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        if not rows:
            return
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _prompt_text_length(prompt_id: str) -> int:
    return len((PROMPT_SOURCE_ROOT / f"{prompt_id}.txt").read_text(encoding="utf-8"))


def _find_rng_seed_for_order(seed: int, target_order: tuple[str, ...]) -> int:
    for candidate in range(100000):
        rng = random.Random(candidate)
        cpr.select_development_seed((seed,), rng=rng)
        order = cpr.choose_prompt_order(cpr.PROMPT_IDS, rng=rng)
        if tuple(order) == tuple(target_order):
            return candidate
    raise RuntimeError(f"Unable to find RNG seed for prompt order {target_order}")


def _mean(values: list[float]) -> float:
    values = [float(value) for value in values if value is not None]
    return sum(values) / len(values) if values else 0.0


def _entropy_from_counts(counts: dict[str, float]) -> float:
    total = sum(float(value) for value in counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in counts.values():
        probability = float(value) / total
        if probability > 0:
            entropy -= probability * math.log2(probability)
    return entropy


def _load_prompt_comparison(case_root: Path) -> list[dict[str, object]]:
    rows = _read_csv_rows(case_root / "prompt_comparison.csv")
    normalized: list[dict[str, object]] = []
    for row in rows:
        normalized.append(
            {
                "prompt_id": row.get("prompt_id", ""),
                "seed": int(float(row.get("seed", 0) or 0)),
                "vehicle_count": int(float(row.get("vehicle_count", 0) or 0)),
                "run_count": int(float(row.get("run_count", 0) or 0)),
                "technical_rerun_count": int(float(row.get("technical_rerun_count", 0) or 0)),
                "total_live_requests": int(float(row.get("total_live_requests", 0) or 0)),
                "provider_success_count": int(float(row.get("provider_success_count", 0) or 0)),
                "provider_failure_count": int(float(row.get("provider_failure_count", 0) or 0)),
                "parser_success_given_provider_success": float(row.get("parser_success_given_provider_success", 0.0) or 0.0),
                "semantic_fallback_given_provider_success": float(row.get("semantic_fallback_given_provider_success", 0.0) or 0.0),
                "ambiguous_invalid_response_count": int(float(row.get("ambiguous_invalid_response_count", 0) or 0)),
                "genuine_proceed_count": int(float(row.get("genuine_proceed_count", 0) or 0)),
                "genuine_wait_count": int(float(row.get("genuine_wait_count", 0) or 0)),
                "genuine_free_count": int(float(row.get("genuine_free_count", 0) or 0)),
                "genuine_proceed_rate": float(row.get("genuine_proceed_rate", 0.0) or 0.0),
                "genuine_wait_rate": float(row.get("genuine_wait_rate", 0.0) or 0.0),
                "genuine_free_rate": float(row.get("genuine_free_rate", 0.0) or 0.0),
                "mean_successful_request_latency_ms": float(row.get("mean_successful_request_latency_ms", 0.0) or 0.0),
                "mean_response_length": float(row.get("mean_response_length", 0.0) or 0.0),
            }
        )
    return normalized


def _summarize_case_row(
    *,
    prompt_row: dict[str, object],
    case_seed: int,
    execution_order: int,
    prompt_order: tuple[str, ...],
    order_rng_seed: int,
    case_root: Path,
    llm_mode: str,
    vehicle_count: int,
) -> dict[str, object]:
    prompt_id = str(prompt_row["prompt_id"])
    run_id = f"CPR_{prompt_id}_v{vehicle_count}_seed{case_seed}_{llm_mode}"
    artifacts = run_artifact_paths(run_id)
    step_rows = _read_csv_rows(artifacts["step_records"])
    with artifacts["run_metadata"].open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    run_summary = calculate_summary(step_rows, metadata)
    prompt_text = (PROMPT_SOURCE_ROOT / f"{prompt_id}.txt").read_text(encoding="utf-8")
    total_live_requests = int(prompt_row["total_live_requests"])
    provider_success_count = int(prompt_row["provider_success_count"])
    provider_failure_count = int(prompt_row["provider_failure_count"])
    genuine_counts = {
        "PROCEED": int(prompt_row["genuine_proceed_count"]),
        "WAIT": int(prompt_row["genuine_wait_count"]),
        "FREE": int(prompt_row["genuine_free_count"]),
    }
    if total_live_requests == 0:
        run_validity = "INVALID_EXECUTION_RUN"
    elif provider_success_count == 0:
        run_validity = "INVALID_PROVIDER_RUN"
    elif provider_failure_count > 0 or float(prompt_row["parser_success_given_provider_success"]) < 1.0:
        run_validity = "VALID_RUN_WITH_PROVIDER_FAILURES"
    else:
        run_validity = "VALID_PROMPT_RUN"

    return {
        "case_seed": case_seed,
        "execution_order": execution_order,
        "prompt_order": " > ".join(prompt_order),
        "order_rng_seed": order_rng_seed,
        "case_root": str(case_root),
        "prompt_id": prompt_id,
        "seed": case_seed,
        "vehicle_count": vehicle_count,
        "run_id": run_id,
        "run_validity": run_validity,
        "technical_rerun_count": int(prompt_row["technical_rerun_count"]),
        "run_count": int(prompt_row["run_count"]),
        "total_live_requests": total_live_requests,
        "provider_success_count": provider_success_count,
        "provider_failure_count": provider_failure_count,
        "provider_success_rate": provider_success_count / total_live_requests if total_live_requests else 0.0,
        "parser_success_given_provider_success": float(prompt_row["parser_success_given_provider_success"]),
        "semantic_fallback_given_provider_success": float(prompt_row["semantic_fallback_given_provider_success"]),
        "ambiguous_invalid_response_count": int(prompt_row["ambiguous_invalid_response_count"]),
        "genuine_proceed_count": int(prompt_row["genuine_proceed_count"]),
        "genuine_wait_count": int(prompt_row["genuine_wait_count"]),
        "genuine_free_count": int(prompt_row["genuine_free_count"]),
        "genuine_proceed_rate": float(prompt_row["genuine_proceed_rate"]),
        "genuine_wait_rate": float(prompt_row["genuine_wait_rate"]),
        "genuine_free_rate": float(prompt_row["genuine_free_rate"]),
        "genuine_action_entropy": _entropy_from_counts(genuine_counts),
        "genuine_max_action_share": max((count / provider_success_count) for count in genuine_counts.values()) if provider_success_count else 0.0,
        "mean_successful_request_latency_ms": float(prompt_row["mean_successful_request_latency_ms"]),
        "mean_response_length": float(prompt_row["mean_response_length"]),
        "scheduled_vehicles": int(run_summary.get("vehicles_observed", vehicle_count)),
        "departed_vehicles": int(run_summary.get("departed", 0)),
        "arrived_vehicles": int(run_summary.get("arrived", 0)),
        "completion_rate": float(run_summary.get("completion_rate", 0.0)),
        "mean_waiting_time": float(run_summary.get("mean_waiting_time", 0.0)),
        "mean_speed": float(run_summary.get("mean_speed", 0.0)),
        "episode_duration": float(run_summary.get("episode_duration", 0.0)),
        "collision_count": int(run_summary.get("collision_count", 0)),
        "live_request_count": int(run_summary.get("proceed_count", 0)) + int(run_summary.get("wait_count", 0)) + int(run_summary.get("free_count", 0)),
        "provider": run_summary.get("provider", "Groq"),
        "model": run_summary.get("model", "openai/gpt-oss-20b"),
        "prompt_text_length": len(prompt_text),
        "prompt_sha256": _sha256(PROMPT_SOURCE_ROOT / f"{prompt_id}.txt"),
    }


def _aggregate_prompt_rows(run_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in run_rows:
        grouped[str(row["prompt_id"])].append(row)

    rows: list[dict[str, object]] = []
    for prompt_id in cpr.PROMPT_IDS:
        prompt_rows = grouped.get(prompt_id, [])
        if not prompt_rows:
            continue
        provider_success_count = sum(int(row["provider_success_count"]) for row in prompt_rows)
        provider_failure_count = sum(int(row["provider_failure_count"]) for row in prompt_rows)
        total_live_requests = sum(int(row["total_live_requests"]) for row in prompt_rows)
        parser_success_count = sum(float(row["parser_success_given_provider_success"]) * int(row["provider_success_count"]) for row in prompt_rows)
        fallback_count = sum(float(row["semantic_fallback_given_provider_success"]) * int(row["provider_success_count"]) for row in prompt_rows)
        genuine_proceed_count = sum(int(row["genuine_proceed_count"]) for row in prompt_rows)
        genuine_wait_count = sum(int(row["genuine_wait_count"]) for row in prompt_rows)
        genuine_free_count = sum(int(row["genuine_free_count"]) for row in prompt_rows)
        completion_rate = _mean([float(row["completion_rate"]) for row in prompt_rows])
        mean_waiting_time = _mean([float(row["mean_waiting_time"]) for row in prompt_rows])
        mean_speed = _mean([float(row["mean_speed"]) for row in prompt_rows])
        episode_duration = _mean([float(row["episode_duration"]) for row in prompt_rows])
        collision_count = sum(int(row["collision_count"]) for row in prompt_rows)
        technical_rerun_count = sum(int(row["technical_rerun_count"]) for row in prompt_rows)
        prompt_text_length = int(prompt_rows[0]["prompt_text_length"])
        prompt_sha256 = str(prompt_rows[0]["prompt_sha256"])
        genuine_counts = {
            "PROCEED": genuine_proceed_count,
            "WAIT": genuine_wait_count,
            "FREE": genuine_free_count,
        }
        rows.append(
            {
                "prompt_id": prompt_id,
                "run_count": len(prompt_rows),
                "technical_rerun_count": technical_rerun_count,
                "total_live_requests": total_live_requests,
                "provider_success_count": provider_success_count,
                "provider_failure_count": provider_failure_count,
                "provider_success_rate": provider_success_count / total_live_requests if total_live_requests else 0.0,
                "parser_success_count": parser_success_count,
                "parser_success_given_provider_success": parser_success_count / provider_success_count if provider_success_count else 0.0,
                "semantic_fallback_count": fallback_count,
                "semantic_fallback_given_provider_success": fallback_count / provider_success_count if provider_success_count else 0.0,
                "ambiguous_invalid_response_count": sum(int(row["ambiguous_invalid_response_count"]) for row in prompt_rows),
                "genuine_proceed_count": genuine_proceed_count,
                "genuine_wait_count": genuine_wait_count,
                "genuine_free_count": genuine_free_count,
                "genuine_proceed_rate": genuine_proceed_count / provider_success_count if provider_success_count else 0.0,
                "genuine_wait_rate": genuine_wait_count / provider_success_count if provider_success_count else 0.0,
                "genuine_free_rate": genuine_free_count / provider_success_count if provider_success_count else 0.0,
                "genuine_action_entropy": _entropy_from_counts(genuine_counts),
                "genuine_max_action_share": max((count / provider_success_count) for count in genuine_counts.values()) if provider_success_count else 0.0,
                "mean_successful_request_latency_ms": _mean([float(row["mean_successful_request_latency_ms"]) for row in prompt_rows]),
                "mean_response_length": _mean([float(row["mean_response_length"]) for row in prompt_rows]),
                "completion_rate": completion_rate,
                "mean_waiting_time": mean_waiting_time,
                "mean_speed": mean_speed,
                "episode_duration": episode_duration,
                "collision_count": collision_count,
                "scheduled_vehicles": sum(int(row["scheduled_vehicles"]) for row in prompt_rows),
                "departed_vehicles": sum(int(row["departed_vehicles"]) for row in prompt_rows),
                "arrived_vehicles": sum(int(row["arrived_vehicles"]) for row in prompt_rows),
                "prompt_text_length": prompt_text_length,
                "prompt_sha256": prompt_sha256,
            }
        )
    return rows


def _select_prompt(aggregated_rows: list[dict[str, object]]) -> dict[str, object]:
    if not aggregated_rows:
        return {
            "selected_prompt": "PROMPT_SELECTION_INCONCLUSIVE",
            "confidence": "Low",
            "selection_rationale": "No prompt rows were available for comparison.",
            "comparison_basis": [],
        }

    scores: dict[str, tuple[float, ...]] = {}
    for row in aggregated_rows:
        scores[str(row["prompt_id"])] = (
            float(row["provider_success_rate"]),
            float(row["parser_success_given_provider_success"]),
            -float(row["ambiguous_invalid_response_count"]),
            -float(row["semantic_fallback_given_provider_success"]),
            float(row["genuine_action_entropy"]),
            -float(row["genuine_max_action_share"]),
            float(row["completion_rate"]),
            -float(row["collision_count"]),
            -float(row["mean_waiting_time"]),
            float(row["mean_speed"]),
            -float(row["episode_duration"]),
            -float(row["prompt_text_length"]),
            -float(row["technical_rerun_count"]),
        )

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_prompt, best_score = ranked[0]
    tied = [prompt_id for prompt_id, score in ranked if score == best_score]
    if len(tied) > 1:
        if "P1_BASELINE" in tied:
            return {
                "selected_prompt": "P1_BASELINE",
                "confidence": "Low",
                "selection_rationale": "Prompt metrics were tied, so the provisional canonical prompt was retained because evidence was not strong enough for a harder claim.",
                "comparison_basis": tied,
            }
        return {
            "selected_prompt": "PROMPT_SELECTION_INCONCLUSIVE",
            "confidence": "Low",
            "selection_rationale": "Prompt metrics were tied and no prompt had a clear evidence advantage.",
            "comparison_basis": tied,
        }

    runner_up_score = ranked[1][1] if len(ranked) > 1 else None
    confidence = "High"
    if runner_up_score is not None:
        major_groups = [
            (0, 3),   # contract reliability
            (4, 5),   # decision behavior
            (6, 7),   # safety
            (8, 10),  # efficiency
            (11, 12), # reproducibility / complexity
        ]
        group_wins = 0
        for start, end in major_groups:
            if best_score[start : end + 1] > runner_up_score[start : end + 1]:
                group_wins += 1
        if group_wins < 3:
            confidence = "Medium"
    rationale = "Selected by the strongest combined contract reliability, decision-behavior, safety, efficiency, and reproducibility evidence."
    if best_prompt == "P1_BASELINE":
        rationale = "P1_BASELINE remained the best-supported option after conservative comparison across reliability, safety, efficiency, and simplicity metrics."
    return {
        "selected_prompt": best_prompt,
        "confidence": confidence,
        "selection_rationale": rationale,
        "comparison_basis": [prompt_id for prompt_id, _ in ranked],
    }


def main() -> int:
    output_root = FINAL_OUTPUT_ROOT
    output_root.mkdir(parents=True, exist_ok=True)

    prompt_hash_audit = cpr.verify_prompt_hashes()
    request_config_audit = cpr.verify_frozen_request_config()
    if not prompt_hash_audit.matches:
        raise SystemExit("PROMPT_VERSION_MISMATCH")
    if not request_config_audit.matches:
        raise SystemExit("FROZEN_REQUEST_CONFIG_MISMATCH")

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        write_json(
            output_root / "provider_precheck.json",
            {
                "provider": "Groq",
                "model": "openai/gpt-oss-20b",
                "status": "missing_credential",
                "failure_classification": "PROVIDER_PRECHECK_FAILED",
                "request_attempted": False,
            },
        )
        raise SystemExit("PROVIDER_PRECHECK_FAILED")

    provider_precheck = cpr.run_provider_probe(api_key)
    write_json(output_root / "provider_precheck.json", provider_precheck)
    if not provider_precheck.get("provider_request_success"):
        raise SystemExit(str(provider_precheck.get("failure_classification", "PROVIDER_PRECHECK_FAILED")))

    original_run_provider_probe = cpr.run_provider_probe
    cpr.run_provider_probe = lambda _api_key: dict(provider_precheck)
    try:
        case_roots: list[Path] = []
        run_rows: list[dict[str, object]] = []
        trace_rows: list[dict[str, object]] = []
        order_rng_seeds: dict[str, int] = {}
        prompt_orders: dict[str, list[str]] = {}

        for seed, target_order in DEVELOPMENT_BATCH_PLANS:
            order_rng_seed = _find_rng_seed_for_order(seed, target_order)
            order_rng_seeds[str(seed)] = order_rng_seed
            prompt_orders[str(seed)] = list(target_order)
            case_root = output_root / f"seed{seed}"
            case_roots.append(case_root)
            cpr.run_revalidation(
                output_root=case_root,
                seed_candidates=(seed,),
                rng=random.Random(order_rng_seed),
                cooldown_seconds=DEFAULT_COOLDOWN_SECONDS,
                density=DEFAULT_DENSITY,
                vehicle_count=DEFAULT_VEHICLE_COUNT,
                llm_mode=DEFAULT_LLM_MODE,
                decision_interval=DEFAULT_DECISION_INTERVAL,
            )
            prompt_rows = _load_prompt_comparison(case_root)
            prompt_rows_map = {row["prompt_id"]: row for row in prompt_rows}
            for execution_order, prompt_id in enumerate(target_order, start=1):
                row = _summarize_case_row(
                    prompt_row=prompt_rows_map[prompt_id],
                    case_seed=seed,
                    execution_order=execution_order,
                    prompt_order=target_order,
                    order_rng_seed=order_rng_seed,
                    case_root=case_root,
                    llm_mode=DEFAULT_LLM_MODE,
                    vehicle_count=DEFAULT_VEHICLE_COUNT,
                )
                run_rows.append(row)
            trace_path = case_root / "request_trace.jsonl"
            if trace_path.exists():
                trace_rows.extend(json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip())

        aggregated_rows = _aggregate_prompt_rows(run_rows)
        selection = _select_prompt(aggregated_rows)
        final_verdict = "CANONICAL_PROMPT_SELECTED_READY_TO_FREEZE" if selection["selected_prompt"] != "PROMPT_SELECTION_INCONCLUSIVE" else "PROMPT_SELECTION_INCONCLUSIVE"

        write_json(
            output_root / "run_manifest.json",
            {
                "repository": str(PROJECT_ROOT),
                "branch": "phase-18-decision-pipeline-separation",
                "head": os.popen("git rev-parse HEAD").read().strip(),
                "prompt_candidates": list(cpr.PROMPT_IDS),
                "development_batch_plans": [
                    {"seed": seed, "prompt_order": list(order), "order_rng_seed": order_rng_seeds.get(str(seed), 0)}
                    for seed, order in DEVELOPMENT_BATCH_PLANS
                ],
                "vehicle_count": DEFAULT_VEHICLE_COUNT,
                "density": DEFAULT_DENSITY,
                "llm_mode": DEFAULT_LLM_MODE,
                "decision_interval": DEFAULT_DECISION_INTERVAL,
                "prompt_hashes": dict(prompt_hash_audit.current),
                "request_config": dict(request_config_audit.current),
                "case_roots": [str(path) for path in case_roots],
                "created_at_epoch_seconds": __import__("time").time(),
            },
        )
        _write_csv(output_root / "run_level_results.csv", run_rows)
        _write_csv(output_root / "prompt_comparison.csv", aggregated_rows)
        write_jsonl(output_root / "request_trace.jsonl", trace_rows)
        write_json(
            output_root / "prompt_selection_summary.json",
            {
                "provider_precheck": provider_precheck,
                "prompt_hashes": dict(prompt_hash_audit.current),
                "request_config": dict(request_config_audit.current),
                "run_count": len(run_rows),
                "valid_run_count": sum(1 for row in run_rows if str(row["run_validity"]).startswith("VALID")),
                **selection,
                "final_verdict": final_verdict,
            },
        )

        print(json.dumps({
            "run_manifest": str(output_root / "run_manifest.json"),
            "provider_precheck": str(output_root / "provider_precheck.json"),
            "run_level_results": str(output_root / "run_level_results.csv"),
            "prompt_comparison": str(output_root / "prompt_comparison.csv"),
            "request_trace": str(output_root / "request_trace.jsonl"),
            "prompt_selection_summary": str(output_root / "prompt_selection_summary.json"),
            "selected_prompt": selection["selected_prompt"],
            "confidence": selection["confidence"],
            "final_verdict": final_verdict,
        }, indent=2))
        return 0
    finally:
        cpr.run_provider_probe = original_run_provider_probe


if __name__ == "__main__":
    raise SystemExit(main())

