from __future__ import annotations

import csv
import json
import shutil
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.controllers.decision_pipeline import run_pipeline_controller
from src.experiments.scenario_generator import generate_scenario


SUMO_BINARY = ROOT.parent / "bin" / "sumo.exe"
SMOKE_ROOT = ROOT / "results" / "phase18_smoke"
EDGE_MAP = {
    "N_S": ("N", "-S"),
    "S_N": ("S", "-N"),
    "E_W": ("E", "-W"),
    "W_E": ("W", "-E"),
}


@contextmanager
def patched_smoke_roots(base_dir: Path):
    import src.common.metrics as metrics
    import src.experiments.scenario_generator as scenario_generator

    original_results_dir = metrics.RESULTS_DIR
    original_raw_results_dir = metrics.RAW_RESULTS_DIR
    original_summaries_dir = metrics.SUMMARIES_DIR
    original_figures_dir = metrics.FIGURES_DIR
    original_generated_root = scenario_generator.GENERATED_ROOT

    metrics.RESULTS_DIR = base_dir / "results"
    metrics.RAW_RESULTS_DIR = metrics.RESULTS_DIR / "raw"
    metrics.SUMMARIES_DIR = metrics.RESULTS_DIR / "summaries"
    metrics.FIGURES_DIR = metrics.RESULTS_DIR / "figures"
    scenario_generator.GENERATED_ROOT = base_dir / "generated_routes"

    try:
        yield
    finally:
        metrics.RESULTS_DIR = original_results_dir
        metrics.RAW_RESULTS_DIR = original_raw_results_dir
        metrics.SUMMARIES_DIR = original_summaries_dir
        metrics.FIGURES_DIR = original_figures_dir
        scenario_generator.GENERATED_ROOT = original_generated_root


def rewrite_routes_file(routes_path: Path, scenario_id: str) -> None:
    root = ET.Element("routes")
    ET.SubElement(
        root,
        "vType",
        attrib={
            "id": "car",
            "accel": "2.6",
            "decel": "4.5",
            "sigma": "0.5",
            "length": "5",
            "maxSpeed": "13.89",
        },
    )
    for route_id in ["N_S", "S_N", "E_W", "W_E"]:
        edge_a, edge_b = EDGE_MAP[route_id]
        ET.SubElement(root, "route", attrib={"id": route_id, "edges": f"{edge_a} {edge_b}"})

    vehicle_specs = [
        (f"{scenario_id}_0", "N_S", 0),
        (f"{scenario_id}_1", "N_S", 1),
        (f"{scenario_id}_2", "E_W", 2),
        (f"{scenario_id}_3", "W_E", 3),
    ]
    for vehicle_id, route_id, depart in vehicle_specs:
        ET.SubElement(
            root,
            "vehicle",
            attrib={
                "id": vehicle_id,
                "type": "car",
                "route": route_id,
                "depart": str(depart),
                "departLane": "best",
            },
        )

    ET.ElementTree(root).write(routes_path, encoding="utf-8", xml_declaration=True)


def scripted_mock_llm(stage_mode: str):
    def provider(traffic_state: list[dict]) -> dict[str, str]:
        controlled = [state for state in traffic_state if state.get("inside_control_zone")]
        if not controlled:
            return {state["vehicle_id"]: "FREE" for state in traffic_state}

        priority = min(controlled, key=lambda state: state.get("time_to_intersection", float("inf")))
        priority_route = priority.get("route_id", "")
        decisions: dict[str, str] = {}

        for state in traffic_state:
            vid = state["vehicle_id"]
            route_id = state.get("route_id", "")
            if not state.get("inside_control_zone"):
                decisions[vid] = "FREE"
            elif stage_mode == "raw":
                decisions[vid] = "PROCEED" if route_id == priority_route or vid == priority["vehicle_id"] else "WAIT"
            elif stage_mode == "hybrid":
                decisions[vid] = "PROCEED" if vid == priority["vehicle_id"] else "WAIT"
            else:
                decisions[vid] = "PROCEED"
        return decisions

    return provider


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_mode(base_dir: Path, stage_mode: str) -> dict:
    import src.common.metrics as metrics
    import src.llm.fallback_policy as fallback_policy

    scenario_id = f"phase18_smoke_{stage_mode}"
    scenario_config = generate_scenario(scenario_id, "low", 1, vehicle_count=4)
    routes_path = Path(scenario_config["sumocfg_path"]).with_name("routes.xml")
    rewrite_routes_file(routes_path, scenario_id)

    original_mock = fallback_policy.mock_llm_decision
    fallback_policy.mock_llm_decision = scripted_mock_llm(stage_mode)
    try:
        experiment_id = f"PHASE18_{stage_mode.upper()}_SMOKE"
        run_pipeline_controller(
            experiment_id=experiment_id,
            controller_name=f"Phase18Smoke{stage_mode.title()}",
            stage_mode=stage_mode,
            scenario=scenario_id,
            vehicle_count=4,
            seed=1,
            sumo_binary=SUMO_BINARY,
            sumo_config=Path(scenario_config["sumocfg_path"]),
            simulation_steps=60,
            llm_mode="mock",
            llm_decision_interval=1,
            llm_model="",
            llm_base_url="",
            llm_api_key="",
            prompt_version="v2-stage-separated",
        )
    finally:
        fallback_policy.mock_llm_decision = original_mock

    run_id = f"PHASE18_{stage_mode.upper()}_SMOKE_v4_seed1_mock"
    artifact_paths = metrics.run_artifact_paths(run_id)
    step_records = artifact_paths["step_records"]
    run_metadata = artifact_paths["run_metadata"]
    events = artifact_paths["events"]

    if not step_records.exists():
        raise AssertionError(f"Missing step records for {stage_mode}: {step_records}")
    if not run_metadata.exists():
        raise AssertionError(f"Missing run metadata for {stage_mode}: {run_metadata}")
    if not events.exists():
        raise AssertionError(f"Missing event log for {stage_mode}: {events}")

    rows = read_csv_rows(step_records)
    if not rows:
        raise AssertionError(f"No step records were written for {stage_mode}")

    required_fields = {
        "controller",
        "llm_raw_decision",
        "validated_llm_decision",
        "postprocessed_decision",
        "final_decision",
        "safety_override",
        "decision_source",
        "llm_mode",
        "simulation_step",
        "vehicle_id",
    }
    missing_fields = required_fields - set(rows[0].keys())
    if missing_fields:
        raise AssertionError(f"Missing smoke test columns for {stage_mode}: {sorted(missing_fields)}")

    allowed_actions = {"PROCEED", "WAIT", "FREE"}
    if any(row["final_decision"] not in allowed_actions for row in rows):
        raise AssertionError(f"Unexpected final decision value in {stage_mode}")

    if len({row["controller"] for row in rows}) != 1:
        raise AssertionError(f"Mixed controller names found in {stage_mode}")
    if len({row["llm_mode"] for row in rows}) != 1 or rows[0]["llm_mode"] != "mock":
        raise AssertionError(f"Unexpected llm_mode in {stage_mode}")

    with run_metadata.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    if metadata.get("status") != "completed":
        raise AssertionError(f"Smoke metadata did not complete for {stage_mode}")

    with events.open("r", encoding="utf-8") as f:
        event_lines = [line for line in f.read().splitlines() if line.strip()]
    if not event_lines:
        raise AssertionError(f"No events were recorded for {stage_mode}")

    return {
        "stage_mode": stage_mode,
        "rows": len(rows),
        "controller": rows[0]["controller"],
        "decision_sources": sorted({row["decision_source"] for row in rows}),
        "outside_rule_rows": sum(1 for row in rows if row["outside_control_zone_rule_applied"] == "True"),
        "postprocess_rows": sum(1 for row in rows if row["postprocess_applied"] == "True"),
        "safety_override_rows": sum(1 for row in rows if row["safety_override"] == "True"),
        "step_records": str(step_records),
        "run_metadata": str(run_metadata),
        "events": str(events),
    }


def main() -> int:
    warnings.filterwarnings("default", category=RuntimeWarning)
    if not SUMO_BINARY.exists():
        raise FileNotFoundError(f"Missing SUMO binary: {SUMO_BINARY}")

    SMOKE_ROOT.mkdir(parents=True, exist_ok=True)
    work_root = SMOKE_ROOT / "phase18_sumo_smoke"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)

    with patched_smoke_roots(work_root):
        summaries = [run_mode(work_root, mode) for mode in ("raw", "hybrid", "hybrid_safety")]

    summary_path = work_root / "smoke_summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")

    print(json.dumps(summaries, indent=2))
    print(f"Smoke summary saved to: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
