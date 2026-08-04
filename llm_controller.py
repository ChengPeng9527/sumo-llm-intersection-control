from __future__ import annotations

import os
import time
from pathlib import Path

import traci

from common import (
    CONFIG,
    apply_decision,
    build_event,
    build_run_metadata,
    calculate_summary,
    create_record,
    distance_to_center,
    estimate_time_to_intersection,
    get_vehicle_route,
    is_in_control_zone,
    print_summary,
    run_artifact_paths,
    write_run_artifacts,
)
from src.llm.fallback_policy import mock_llm_decision
from src.llm.response_parser import parse_llm_response
from src.llm.prompt_builder import build_structured_prompt
from src.safety.route_conflict import validate_conflict_matrix
from ttc_safety import verify_decisions

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


SUMO_BINARY = CONFIG["sumo_gui_binary_path"]
SUMO_CONFIG = Path(os.getenv("SUMO_CONFIG_PATH", str(CONFIG["sumo_config_path"])))
EXPERIMENT_ID = "E03_LLM_4V_S1"
CONTROLLER_NAME = "LLMController"
SCENARIO = os.getenv("SCENARIO_ID", "debug_four_vehicle")
VEHICLE_COUNT = int(os.getenv("VEHICLE_COUNT", "4"))
SEED = CONFIG["default_seed"]
SIMULATION_STEPS = int(os.getenv("SIMULATION_STEPS", str(CONFIG["default_simulation_duration"])))
USE_SAFETY_LAYER = True
LLM_MODE = os.getenv("LLM_MODE", "mock").strip().lower()
LLM_DECISION_INTERVAL = max(1, int(os.getenv("LLM_DECISION_INTERVAL", "1")))
LLM_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else "https://openrouter.ai/api/v1",
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b" if os.getenv("GROQ_API_KEY") else "openrouter/free",
)
RUN_ID = f"{EXPERIMENT_ID}_v{VEHICLE_COUNT}_seed{SEED}_{LLM_MODE}"
ARTIFACTS = run_artifact_paths(RUN_ID)
OUTPUT_CSV = ARTIFACTS["step_records"]


def build_llm_client():
    if LLM_MODE != "real":
        return None
    if not LLM_API_KEY or OpenAI is None:
        return None
    return OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)


CLIENT = build_llm_client()


def build_traffic_state(vehicles):
    state = []
    for vid in vehicles:
        state.append(
            {
                "vehicle_id": vid,
                "route_id": get_vehicle_route(traci, vid),
                "speed": round(traci.vehicle.getSpeed(vid), 2),
                "distance_to_intersection": round(distance_to_center(traci, vid), 2),
                "time_to_intersection": round(estimate_time_to_intersection(traci, vid), 2),
                "inside_control_zone": is_in_control_zone(traci, vid),
            }
        )
    return state


def enforce_zone_policy(traffic_state, raw_decisions):
    final_decisions = dict(raw_decisions)
    for state in traffic_state:
        if not state["inside_control_zone"]:
            final_decisions[state["vehicle_id"]] = "FREE"
    return final_decisions


def decide(vehicles):
    traffic_state = build_traffic_state(vehicles)
    prompt = build_structured_prompt(traffic_state, validate_conflict_matrix())
    vehicle_ids = [v["vehicle_id"] for v in traffic_state]
    if LLM_MODE == "real" and CLIENT is not None:
        start_time = time.perf_counter()
        try:
            response = CLIENT.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content or ""
            raw_decisions, parse_ok = parse_llm_response(content, vehicle_ids)
            raw_decisions = enforce_zone_policy(traffic_state, raw_decisions)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return raw_decisions, prompt, {
                "llm_called": True,
                "llm_model": LLM_MODEL,
                "llm_response_time_ms": round(elapsed_ms, 2),
                "json_parse_success": parse_ok,
                "fallback_used": False,
            }
        except Exception:
            raw_decisions = mock_llm_decision(traffic_state)
            raw_decisions = enforce_zone_policy(traffic_state, raw_decisions)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return raw_decisions, prompt, {
                "llm_called": True,
                "llm_model": LLM_MODEL,
                "llm_response_time_ms": round(elapsed_ms, 2),
                "json_parse_success": False,
                "fallback_used": True,
            }

    if LLM_MODE == "real" and CLIENT is None:
        print("LLM real mode requested but OpenAI client is unavailable; using mock fallback.")

    raw_decisions = mock_llm_decision(traffic_state)
    raw_decisions = enforce_zone_policy(traffic_state, raw_decisions)
    return raw_decisions, prompt, {
        "llm_called": False,
        "llm_model": LLM_MODEL if LLM_MODE == "real" else "",
        "llm_response_time_ms": 0.0,
        "json_parse_success": True,
        "fallback_used": False,
    }


def run():
    traci.start([str(SUMO_BINARY), "-c", str(SUMO_CONFIG), "--start"])
    records = []
    events = []
    all_seen_vehicles = set()
    departed_seen = set()
    arrived_seen = set()
    cached_raw_decisions = {}
    cached_llm_meta = {
        "llm_called": False,
        "llm_model": "",
        "llm_response_time_ms": 0.0,
        "json_parse_success": True,
        "fallback_used": False,
    }

    for step in range(SIMULATION_STEPS):
        traci.simulationStep()
        departed_ids = list(traci.simulation.getDepartedIDList())
        arrived_ids = list(traci.simulation.getArrivedIDList())
        simulation_time = step * CONFIG["simulation_step_length"]
        for vid in departed_ids:
            if vid not in departed_seen:
                departed_seen.add(vid)
                events.append(
                    build_event(
                        run_id=RUN_ID,
                        event_type="departed",
                        simulation_step=step,
                        simulation_time_seconds=simulation_time,
                        vehicle_id=vid,
                        details="vehicle entered the simulation",
                    )
                )
        for vid in arrived_ids:
            if vid not in arrived_seen:
                arrived_seen.add(vid)
                events.append(
                    build_event(
                        run_id=RUN_ID,
                        event_type="arrived",
                        simulation_step=step,
                        simulation_time_seconds=simulation_time,
                        vehicle_id=vid,
                        details="vehicle left the simulation",
                    )
                )
        vehicles = list(traci.vehicle.getIDList())
        all_seen_vehicles.update(vehicles)

        if step % LLM_DECISION_INTERVAL == 0 or not cached_raw_decisions:
            raw_decisions, _prompt, llm_meta = decide(vehicles)
            cached_raw_decisions = dict(raw_decisions)
            cached_llm_meta = dict(llm_meta)
        else:
            raw_decisions = dict(cached_raw_decisions)
            llm_meta = {
                "llm_called": False,
                "llm_model": cached_llm_meta.get("llm_model", ""),
                "llm_response_time_ms": 0.0,
                "json_parse_success": cached_llm_meta.get("json_parse_success", True),
                "fallback_used": cached_llm_meta.get("fallback_used", False),
            }

        if USE_SAFETY_LAYER:
            final_decisions, conflict_flags, conflict_types, priority_reason = verify_decisions(
                traci,
                vehicles,
                raw_decisions,
            )
        else:
            final_decisions = dict(raw_decisions)
            conflict_flags = {vid: False for vid in vehicles}
            conflict_types = {vid: "" for vid in vehicles}
            priority_reason = ""

        for vid in vehicles:
            raw_decision = raw_decisions.get(vid, "WAIT")
            final_decision = final_decisions.get(vid, "WAIT")
            conflict = conflict_flags.get(vid, False)
            apply_decision(traci, vid, final_decision)
            records.append(
                create_record(
                    experiment_id=EXPERIMENT_ID,
                    controller=CONTROLLER_NAME,
                    scenario=SCENARIO,
                    seed=SEED,
                    step=step,
                    traci=traci,
                    veh_id=vid,
                    raw_decision=raw_decision,
                    final_decision=final_decision,
                    conflict=conflict,
                    conflict_type=conflict_types.get(vid, ""),
                    priority_reason=priority_reason,
                    run_id=RUN_ID,
                    safety_enabled=USE_SAFETY_LAYER,
                    simulation_time_seconds=simulation_time,
                    vehicle_count=VEHICLE_COUNT,
                    llm_mode=LLM_MODE,
                    llm_called=llm_meta["llm_called"],
                    llm_model=llm_meta["llm_model"],
                    llm_response_time_ms=llm_meta["llm_response_time_ms"],
                    json_parse_success=llm_meta["json_parse_success"],
                    fallback_used=llm_meta["fallback_used"],
                    departed=vid in departed_seen,
                    arrived=False,
                )
            )
        time.sleep(0.03)

    traci.close(False)
    metadata = build_run_metadata(
        run_id=RUN_ID,
        controller=CONTROLLER_NAME,
        safety_enabled=USE_SAFETY_LAYER,
        scenario_id=SCENARIO,
        density="debug",
        vehicle_count=VEHICLE_COUNT,
        seed=SEED,
        llm_mode=LLM_MODE,
        llm_model=LLM_MODEL if LLM_MODE == "real" else "",
        status="completed",
    )
    metadata["departed_count"] = len(departed_seen)
    metadata["arrived_count"] = len(arrived_seen)
    metadata["collision_count"] = 0
    write_run_artifacts(RUN_ID, records, events, metadata)
    summary = calculate_summary(records, all_seen_vehicles, run_metadata=metadata)
    print_summary("LLM Mock Controller With Safety Metrics", summary, OUTPUT_CSV)


if __name__ == "__main__":
    run()
