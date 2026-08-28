from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import common
from src.common.config import load_project_config
from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.controllers.decision_pipeline import run_pipeline_controller
from src.llm.request_config import PHASE2_BASE_URL, PHASE2_MODEL


SCENARIO_ID = "phase2_s3_cooperative_opportunity_v12_seed1"
SCENARIO_CLASS = "S3_COOPERATIVE_OPPORTUNITY"
PACKAGE_PRESENTATION_ROOT = PROJECT_ROOT / "release_evidence" / "presentation"
PACKAGED_GENERATED_ROOT = PACKAGE_PRESENTATION_ROOT / "generated_route"
LOCAL_GENERATED_ROOT = PROJECT_ROOT / "simulation" / "generated_routes" / SCENARIO_ID
GENERATED_ROOT = PACKAGED_GENERATED_ROOT if PACKAGED_GENERATED_ROOT.exists() else LOCAL_GENERATED_ROOT
NORMAL_CONFIG = GENERATED_ROOT / (
    "portable_simulation.sumocfg" if GENERATED_ROOT == PACKAGED_GENERATED_ROOT else "simulation.sumocfg"
)
PACKAGED_PRESENTATION_CONFIG = (
    PACKAGE_PRESENTATION_ROOT / "config" / "s3_v12_seed1_presentation.sumocfg"
)
LOCAL_PRESENTATION_CONFIG = (
    PROJECT_ROOT / "config" / "presentation" / "s3_v12_seed1_presentation.sumocfg"
)
PRESENTATION_CONFIG = (
    PACKAGED_PRESENTATION_CONFIG
    if PACKAGED_PRESENTATION_CONFIG.exists()
    else LOCAL_PRESENTATION_CONFIG
)
GENERATION_CONFIG = GENERATED_ROOT / "generation_config.json"
LOCAL_FROZEN_PAIR_ROOT = (
    PROJECT_ROOT
    / "results"
    / "phase2_formal"
    / "batch2_remaining_matrix"
    / "runs"
    / "s3_cooperative_opportunity_v12_seed1"
)
LOCAL_FROZEN_DETERMINISTIC_RECORDS = (
    LOCAL_FROZEN_PAIR_ROOT
    / "phase2_formal_batch2_s3_cooperative_opportunity_v12_seed1_deterministic_candidate"
    / "decision_records.jsonl"
)
LOCAL_FROZEN_GEMINI_RECORDS = (
    LOCAL_FROZEN_PAIR_ROOT
    / "phase2_formal_batch2_s3_cooperative_opportunity_v12_seed1_gemini_candidate"
    / "decision_records.jsonl"
)
PACKAGED_FROZEN_DETERMINISTIC_RECORDS = (
    PACKAGE_PRESENTATION_ROOT / "replay" / "deterministic" / "decision_records.jsonl"
)
PACKAGED_FROZEN_GEMINI_RECORDS = (
    PACKAGE_PRESENTATION_ROOT / "replay" / "gemini" / "decision_records.jsonl"
)
FROZEN_DETERMINISTIC_RECORDS = (
    PACKAGED_FROZEN_DETERMINISTIC_RECORDS
    if PACKAGED_FROZEN_DETERMINISTIC_RECORDS.exists()
    else LOCAL_FROZEN_DETERMINISTIC_RECORDS
)
FROZEN_GEMINI_RECORDS = (
    PACKAGED_FROZEN_GEMINI_RECORDS
    if PACKAGED_FROZEN_GEMINI_RECORDS.exists()
    else LOCAL_FROZEN_GEMINI_RECORDS
)

ACTION_COLORS = {
    "WAIT": (232, 93, 69, 255),
    "PROCEED": (61, 214, 140, 255),
    "FREE": (111, 177, 219, 255),
}


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _candidate_ids_from_prompt(prompt: str) -> list[str]:
    marker = "Candidate groups:\n"
    if marker not in prompt:
        raise RuntimeError("Frozen replay received a prompt without Candidate groups")
    groups = json.loads(prompt.split(marker, 1)[1])
    return [str(group["candidate_id"]) for group in groups]


class FrozenGeminiReplay:
    def __init__(self, records: list[dict]):
        self.records = records
        self.index = 0

    def __call__(self, prompt: str) -> str:
        if self.index >= len(self.records):
            raise RuntimeError("Replay produced more decision epochs than frozen evidence")
        frozen = self.records[self.index]
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest().upper()
        if prompt_hash != frozen.get("prompt_hash"):
            raise RuntimeError(
                f"Frozen replay state mismatch at decision epoch {self.index + 1}: prompt hash differs"
            )
        current_candidates = _candidate_ids_from_prompt(prompt)
        frozen_candidates = [str(item["candidate_id"]) for item in frozen["candidate_set"]]
        if current_candidates != frozen_candidates:
            raise RuntimeError(
                f"Frozen replay candidate mismatch at decision epoch {self.index + 1}"
            )
        selected = str(frozen.get("llm_candidate_id", ""))
        if selected not in current_candidates:
            raise RuntimeError(
                f"Frozen replay selection is not currently legal at decision epoch {self.index + 1}"
            )
        self.index += 1
        return json.dumps({"selected_candidate_id": selected}, separators=(",", ":"))

    def assert_complete(self) -> None:
        if self.index != len(self.records):
            raise RuntimeError(
                f"Replay consumed {self.index} of {len(self.records)} frozen decision epochs"
            )


def verify_frozen_disagreement() -> dict:
    deterministic = _read_jsonl(FROZEN_DETERMINISTIC_RECORDS)
    gemini = _read_jsonl(FROZEN_GEMINI_RECORDS)
    deterministic_by_time = {float(record["simulation_time"]): record for record in deterministic}
    disagreements = [record for record in gemini if record.get("candidate_disagreement")]
    if not disagreements:
        raise RuntimeError("Frozen Gemini evidence contains no disagreement")

    verified = []
    for gemini_record in disagreements:
        simulation_time = float(gemini_record["simulation_time"])
        deterministic_record = deterministic_by_time.get(simulation_time)
        if deterministic_record is None:
            raise RuntimeError(f"No paired deterministic decision at t={simulation_time}")
        gemini_candidates = [item["candidate_id"] for item in gemini_record["candidate_set"]]
        deterministic_candidates = [item["candidate_id"] for item in deterministic_record["candidate_set"]]
        if gemini_candidates != deterministic_candidates:
            raise RuntimeError(f"Paired candidate sets differ at t={simulation_time}")

        deterministic_id = deterministic_record["selected_candidate_id"]
        gemini_id = gemini_record["selected_candidate_id"]
        features = {item["candidate_id"]: item for item in gemini_record["candidate_features"]}
        if deterministic_id not in features or gemini_id not in features:
            raise RuntimeError(f"A selected group is absent from candidate features at t={simulation_time}")
        gemini_movements = [
            item["movement"] for item in features[gemini_id].get("movement_summary", [])
        ]
        if features[deterministic_id]["group_size"] != 4:
            raise RuntimeError(f"Deterministic disagreement group is not size four at t={simulation_time}")
        if features[gemini_id]["group_size"] != 2 or gemini_movements != ["STRAIGHT", "STRAIGHT"]:
            raise RuntimeError(f"Gemini disagreement group is not the logged straight pair at t={simulation_time}")
        verified.append(
            {
                "simulation_time": simulation_time,
                "deterministic_vehicle_ids": features[deterministic_id]["vehicle_ids"],
                "gemini_vehicle_ids": features[gemini_id]["vehicle_ids"],
            }
        )
    return {"verified": True, "disagreements": verified}


def _load_generation() -> dict:
    generation = json.loads(GENERATION_CONFIG.read_text(encoding="utf-8"))
    if generation.get("scenario_id") != SCENARIO_ID:
        raise RuntimeError("Unexpected generated scenario identity")
    if generation.get("scenario_class") != SCENARIO_CLASS:
        raise RuntimeError("Unexpected generated scenario class")
    if int(generation.get("vehicle_count", 0)) != 12 or int(generation.get("seed", 0)) != 1:
        raise RuntimeError("Presentation scenario must remain S3 12V seed 1")
    return generation


def _install_action_coloring():
    original = common.apply_decision

    def apply_with_color(traci, vehicle_id, decision):
        original(traci, vehicle_id, decision)
        color = ACTION_COLORS.get(decision)
        if color is not None:
            traci.vehicle.setColor(vehicle_id, color)

    common.apply_decision = apply_with_color
    return original


def _run_episode(
    *,
    config_path: Path,
    use_gui: bool,
    enable_action_coloring: bool,
    planner: str,
    run_label: str,
) -> dict:
    generation = _load_generation()
    project = load_project_config()
    replay = None
    provider_call = None
    planner_mode = DETERMINISTIC_CANDIDATE
    llm_mode = "mock"
    controller_name = "DeterministicCandidateController"
    if planner == "gemini-replay":
        replay = FrozenGeminiReplay(_read_jsonl(FROZEN_GEMINI_RECORDS))
        provider_call = replay
        planner_mode = GEMINI_CANDIDATE
        llm_mode = "real"
        controller_name = "FrozenGeminiReplayController"

    original_apply = common.apply_decision
    if enable_action_coloring:
        original_apply = _install_action_coloring()
    try:
        result = run_pipeline_controller(
            experiment_id=f"{run_label}_{SCENARIO_CLASS.lower()}",
            controller_name=controller_name,
            stage_mode="hybrid_safety",
            scenario=SCENARIO_ID,
            vehicle_count=12,
            seed=1,
            sumo_binary=Path(
                project["sumo_gui_binary_path"] if use_gui else project["sumo_binary_path"]
            ),
            sumo_config=config_path,
            simulation_steps=int(generation["simulation_duration_seconds"]),
            llm_mode=llm_mode,
            llm_decision_interval=1,
            llm_model=PHASE2_MODEL,
            llm_base_url=PHASE2_BASE_URL,
            llm_api_key="",
            prompt_version="phase2-candidate-v1",
            candidate_planner_mode=planner_mode,
            grant_timeout_seconds=45.0,
            candidate_provider_call=provider_call,
            max_candidate_provider_requests=len(replay.records) if replay else 0,
            initial_demand_signature=generation["initial_demand_signature"],
        )
    finally:
        common.apply_decision = original_apply
    if replay is not None:
        replay.assert_complete()
        result["presentation_replay"] = True
        result["external_requests"] = 0
    return result


def _read_csv(path: str) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _semantic_step_rows(result: dict) -> list[dict]:
    fields = (
        "simulation_step",
        "simulation_time_seconds",
        "vehicle_id",
        "route_id",
        "incoming_edge",
        "outgoing_edge",
        "movement",
        "speed_before_action",
        "speed_after_action",
        "distance_to_intersection",
        "time_to_intersection",
        "waiting_time",
        "inside_control_zone",
        "candidate_groups",
        "selected_candidate_id",
        "selected_vehicle_ids",
        "final_decision",
        "collision",
    )
    return [
        {field: row.get(field, "") for field in fields}
        for row in _read_csv(result["artifact_paths"]["step_records"])
    ]


def _semantic_decisions(result: dict) -> list[dict]:
    ignored = {
        "run_id",
        "request_id",
        "request_started_at",
        "request_finished_at",
        "latency_ms",
        "planner_wall_latency_ms",
    }
    return [
        {key: value for key, value in record.items() if key not in ignored}
        for record in result["decision_records"]
    ]


def _semantic_events(result: dict) -> list[dict]:
    return [
        {
            key: value
            for key, value in json.loads(line).items()
            if key != "run_id"
        }
        for line in Path(result["artifact_paths"]["events"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_integrity_check() -> dict:
    normal = _run_episode(
        config_path=NORMAL_CONFIG,
        use_gui=False,
        enable_action_coloring=False,
        planner="deterministic",
        run_label="presentation_mvp_integrity_normal",
    )
    presentation = _run_episode(
        config_path=PRESENTATION_CONFIG,
        use_gui=False,
        enable_action_coloring=True,
        planner="deterministic",
        run_label="presentation_mvp_integrity_visual",
    )
    summary_fields = (
        "departed",
        "arrived",
        "completion_rate",
        "throughput",
        "mean_waiting_time",
        "maximum_waiting_time",
        "mean_speed",
        "collision_count",
        "decision_epoch_count",
        "grant_count",
        "grant_timeout_count",
        "safety_intervention_count",
    )
    normal_summary = {field: normal["summary"].get(field) for field in summary_fields}
    presentation_summary = {
        field: presentation["summary"].get(field) for field in summary_fields
    }
    checks = {
        "summary": normal_summary == presentation_summary,
        "step_rows": _semantic_step_rows(normal) == _semantic_step_rows(presentation),
        "candidate_decisions": _semantic_decisions(normal) == _semantic_decisions(presentation),
        "grant_events": _semantic_events(normal) == _semantic_events(presentation),
    }
    report = {
        "identical": all(checks.values()),
        "checks": checks,
        "normal_summary": normal_summary,
        "presentation_summary": presentation_summary,
        "normal_run_id": normal["run_id"],
        "presentation_run_id": presentation["run_id"],
    }
    if not report["identical"]:
        raise RuntimeError("Presentation integrity comparison failed: " + json.dumps(report))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the isolated Phase 2 SUMO presentation MVP")
    parser.add_argument(
        "--planner",
        choices=("deterministic", "gemini-replay"),
        default="deterministic",
        help="Gemini replay uses frozen decisions and makes no external request.",
    )
    parser.add_argument("--headless", action="store_true", help="Use sumo.exe instead of SUMO-GUI")
    parser.add_argument("--integrity-check", action="store_true")
    parser.add_argument("--verify-disagreement", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify_disagreement:
        print(json.dumps(verify_frozen_disagreement(), indent=2))
        return 0
    if args.integrity_check:
        print(json.dumps(run_integrity_check(), indent=2))
        return 0

    disagreement = verify_frozen_disagreement()
    mode = (
        "FROZEN GEMINI REPLAY - NOT A NEW EXPERIMENT"
        if args.planner == "gemini-replay"
        else "DETERMINISTIC COMPARATOR"
    )
    print(f"Presentation mode: {mode}")
    print(f"Verified frozen disagreement events: {len(disagreement['disagreements'])}")
    result = _run_episode(
        config_path=PRESENTATION_CONFIG,
        use_gui=not args.headless,
        enable_action_coloring=True,
        planner=args.planner,
        run_label=f"presentation_mvp_{args.planner.replace('-', '_')}",
    )
    print(json.dumps({"run_id": result["run_id"], "summary": result["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
