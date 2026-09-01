from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from src.controllers.candidate_runtime import DETERMINISTIC_CANDIDATE, GEMINI_CANDIDATE
from src.experiments.phase3_directional_service_imbalance import (
    CONDITION,
    EFFICIENCY_MATERIAL_TOLERANCES,
    FIXED_BASE_DEPARTURES,
    FIXED_ROUTE_SEQUENCE,
    HISTORICAL_S3_MAX_TARGET_AGGREGATE_WAITING,
    SEEDS,
    STAGE1,
    STAGE2,
    VEHICLE_COUNT,
    build_fixed_demand,
    build_plan,
    classify_benefit,
    observe_episode,
    percentile,
    require_stage2_authorization,
    stage1_feasibility,
    valid_gemini_observation,
    verify_matched_initial_conditions,
    waiting_metrics,
)
from src.experiments.llm_validity import StrictLLMFailure
from src.experiments.scenario_generator import _targeted_demand, load_experiment_matrix


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_phase3_directional_service_imbalance.py"
FROZEN_PHASE2 = (
    Path(__file__).resolve().parents[1]
    / "release_evidence/phase2/complete_matrix_summary/complete_matrix_summary.json"
)


def _runner_module():
    spec = importlib.util.spec_from_file_location("directional_stress_runner_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_scenario_preserves_s3_first_twelve_and_adds_one_r4_wave():
    definition = load_experiment_matrix()["targeted_scenarios"]["S3_COOPERATIVE_OPPORTUNITY"]
    for seed in SEEDS:
        original_routes, original_departures = _targeted_demand(definition, seed, 12)
        routes, departures, source_indices = build_fixed_demand(seed)
        source_order = sorted(range(VEHICLE_COUNT), key=lambda index: source_indices.index(index))
        route_by_source = {source: route for source, route in zip(source_indices, routes)}
        assert routes[:12] == original_routes
        assert departures[:12] == original_departures
        assert [route_by_source[index] for index in range(12, 16)] == ["N_W", "E_N", "S_E", "W_S"]
        assert len(source_order) == VEHICLE_COUNT
    assert FIXED_ROUTE_SEQUENCE[:12] == tuple(definition["route_cycle"] * 2)[:12]
    assert FIXED_BASE_DEPARTURES[-4:] == (18, 18, 19, 19)


def test_exact_seeds_run_ids_and_staged_planners_are_frozen():
    stage1 = build_plan(STAGE1)
    stage2 = build_plan(STAGE2)
    assert SEEDS == (1, 2, 3)
    assert [spec.seed for spec in stage1] == [1, 2, 3]
    assert all(spec.condition == CONDITION for spec in stage1 + stage2)
    assert all(spec.planner_mode == DETERMINISTIC_CANDIDATE for spec in stage1)
    assert all(spec.planner_mode == GEMINI_CANDIDATE for spec in stage2)
    assert all(CONDITION.lower() in spec.run_id for spec in stage1 + stage2)
    assert all(spec.planner_mode.lower() in spec.run_id for spec in stage1 + stage2)
    assert all(f"seed{spec.seed}" in spec.run_id for spec in stage1 + stage2)


def _decision(epoch: int, selected: str, target_waiting: float, *, target_legal: bool = True) -> dict:
    target_id = "straight-n|straight-s"
    features = [
        {
            "candidate_id": "right-n|right-e|right-s|right-w",
            "vehicle_ids": ["right-n", "right-e", "right-s", "right-w"],
            "group_size": 4,
            "aggregate_waiting_time": 8.0,
            "maximum_waiting_time": 3.0,
            "minimum_time_to_intersection": None,
            "movement_summary": [
                {"movement": "RIGHT", "incoming_edge": approach}
                for approach in ("N", "E", "S", "W")
            ],
        }
    ]
    if target_legal:
        features.append({
            "candidate_id": target_id,
            "vehicle_ids": ["straight-n", "straight-s"],
            "group_size": 2,
            "aggregate_waiting_time": target_waiting,
            "maximum_waiting_time": target_waiting / 2,
            "minimum_time_to_intersection": None,
            "movement_summary": [
                {"movement": "STRAIGHT", "incoming_edge": "N"},
                {"movement": "STRAIGHT", "incoming_edge": "S"},
            ],
        })
    return {
        "decision_epoch": epoch,
        "simulation_time": float(epoch * 10),
        "candidate_features": features,
        "selected_candidate_id": selected,
        "deterministic_candidate_id": "right-n|right-e|right-s|right-w",
        "llm_candidate_id": selected,
        "candidate_agreement": selected == "right-n|right-e|right-s|right-w",
        "candidate_disagreement": selected != "right-n|right-e|right-s|right-w",
        "provider_request_success": True,
        "parser_success": True,
        "fallback_used": False,
        "latency_ms": 10.0,
        "grant_start_time": float(epoch * 10),
        "grant_end_time": float(epoch * 10 + 8),
        "grant_duration_seconds": 8.0,
        "grant_clearance_reason": "ALL_GRANTED_VEHICLES_LEFT_CONTROL_SCOPE",
    }


def _summary(planner=DETERMINISTIC_CANDIDATE, **overrides):
    value = {
        "run_id": "test",
        "planner_mode": planner,
        "departed": 16,
        "arrived": 16,
        "completion_rate": 1.0,
        "episode_duration_seconds": 60.0,
        "mean_speed": 7.0,
        "collision_count": 0,
        "safety_intervention_count": 0,
        "grant_timeout_count": 0,
    }
    value.update(overrides)
    return value


def test_observer_tracks_repeated_eligible_nonservice_and_grant_provenance():
    records = [
        _decision(1, "right-n|right-e|right-s|right-w", 25.0),
        _decision(2, "right-n|right-e|right-s|right-w", 32.0),
        _decision(3, "straight-n|straight-s", 40.0),
    ]
    observation = observe_episode(records, _summary(), [], ["straight-n", "straight-s"])
    assert observation["repeated_eligible_but_not_selected_count"] == 2
    assert observation["longest_consecutive_eligible_but_not_selected"] == 2
    assert observation["maximum_target_aggregate_waiting_while_not_selected"] == 32.0
    assert observation["decision_epochs"][1]["eligible_but_not_selected_count_to_date"] == 2
    assert observation["decision_epochs"][2]["eligible_but_not_selected_streak"] == 0
    assert observation["decision_epochs"][0]["grant_clearance_reason"]


def test_waiting_distribution_p95_and_approach_metrics_are_fixed():
    records = []
    for vehicle, approach, waiting in (
        ("a", "N", 1), ("b", "N", 3), ("c", "S", 9), ("d", "E", 7)
    ):
        records.append({"vehicle_id": vehicle, "incoming_edge": approach, "waiting_time": waiting})
        records.append({"vehicle_id": vehicle, "incoming_edge": approach, "waiting_time": waiting - 1})
    metrics = waiting_metrics(records)
    assert percentile([1, 3, 7, 9], 0.95) == pytest.approx(8.7)
    assert metrics["total_waiting"] == 20.0
    assert metrics["maximum_vehicle_waiting"] == 9.0
    assert metrics["p95_vehicle_waiting"] == pytest.approx(8.7)
    assert metrics["approach_mean_waiting"] == {"E": 7.0, "N": 2.0, "S": 9.0}
    assert metrics["maximum_approach_mean_waiting"] == 9.0
    assert metrics["approach_waiting_range"] == 7.0


def test_feasibility_gate_requires_two_complete_safe_repeated_nonservice_runs():
    passing = {
        **_summary(),
        "target_eligible_epoch_count": 2,
        "repeated_eligible_but_not_selected_count": 2,
        "longest_consecutive_eligible_but_not_selected": 2,
        "maximum_target_aggregate_waiting_while_not_selected": HISTORICAL_S3_MAX_TARGET_AGGREGATE_WAITING + 1,
        "collisions": 0,
        "safety_interventions": 0,
        "grant_timeouts": 0,
    }
    observations = [{**passing, "seed": 1}, {**passing, "seed": 2}, {**passing, "seed": 3, "collisions": 1}]
    report = stage1_feasibility(observations)
    assert report["passing_seeds"] == 2
    assert report["stage1_gate_passed"] is True
    observations[1]["longest_consecutive_eligible_but_not_selected"] = 1
    assert stage1_feasibility(observations)["stage1_gate_passed"] is False
    assert report["criterion"]["gemini_selection_or_outcome_used"] is False


def test_stage2_requires_reviewed_gate_and_explicit_new_authorization():
    with pytest.raises(PermissionError):
        require_stage2_authorization({"stage1_gate_passed": True}, False)
    with pytest.raises(RuntimeError):
        require_stage2_authorization({"stage1_gate_passed": False}, True)
    require_stage2_authorization({"stage1_gate_passed": True}, True)


def test_stage2_requires_exact_matched_initial_demand_signatures():
    stage1 = {
        "runs": [
            {"seed": seed, "status": "valid", "initial_conditions": {"initial_demand_signature": f"sig-{seed}"}}
            for seed in SEEDS
        ]
    }
    stage2 = {
        "runs": [
            {"seed": seed, "status": "valid", "initial_conditions": {"initial_demand_signature": f"sig-{seed}"}}
            for seed in SEEDS
        ]
    }
    verify_matched_initial_conditions(stage1, stage2)
    stage2["runs"][1]["initial_conditions"]["initial_demand_signature"] = "wrong"
    with pytest.raises(RuntimeError, match="seed2"):
        verify_matched_initial_conditions(stage1, stage2)


def _outcome(seed, planner, *, service=10.0, efficiency=100.0, valid=True):
    value = {
        "seed": seed,
        "planner": planner,
        "total_waiting": efficiency,
        "mean_waiting": efficiency / 16,
        "episode_duration_seconds": efficiency,
        "maximum_vehicle_waiting": service,
        "p95_vehicle_waiting": service,
        "maximum_approach_mean_waiting": service,
        "approach_waiting_range": service,
    }
    if planner == GEMINI_CANDIDATE:
        value.update({
            "llm_valid_decisions": 1 if valid else 0,
            "llm_failed_decisions": 0 if valid else 1,
            "fallback_decisions": 0,
            "llm_episode_valid": valid,
        })
    return value


def test_strict_invalid_gemini_is_excluded_and_benefit_rules_are_preregistered():
    assert EFFICIENCY_MATERIAL_TOLERANCES == {
        "total_waiting": 10.0,
        "mean_waiting": 1.0,
        "episode_duration_seconds": 2.0,
    }
    rows = []
    for seed in SEEDS:
        rows.append(_outcome(seed, DETERMINISTIC_CANDIDATE, service=12.0, efficiency=100.0))
        rows.append(_outcome(seed, GEMINI_CANDIDATE, service=9.0, efficiency=100.0, valid=seed != 3))
    result = classify_benefit(rows)
    assert result["valid_matched_seed_count"] == 2
    assert result["classification"] == "MULTI_DOMAIN_BENEFIT"
    assert valid_gemini_observation(rows[-1]) is False


def test_stage1_runner_uses_no_gemini_and_preserves_independent_namespace(tmp_path, monkeypatch):
    module = _runner_module()
    monkeypatch.setattr(module, "_new_manifest", lambda stage: {"stage": stage, "status": "running", "runs": []})
    calls = []

    def demand(seed):
        return {
            "scenario_id": f"scenario_{seed}", "scenario_class": CONDITION,
            "vehicle_count": 16, "seed": seed, "route_sequence": list(FIXED_ROUTE_SEQUENCE),
            "departure_times": list(FIXED_BASE_DEPARTURES), "movement_sequence": ["RIGHT"] * 16,
            "seed_semantics": {}, "initial_demand_signature": f"signature-{seed}",
            "target_smaller_vehicle_ids": ["straight-n", "straight-s"],
        }

    def episode(generation, **kwargs):
        calls.append(kwargs)
        return {"summary": _summary(), "artifact_paths": {"run_dir": "unused"}}

    def observer(_path, _result, _targets):
        return {**_summary(), "target_eligible_epoch_count": 0}

    observations = module.run_specs(
        tmp_path / "results", STAGE1, demand_factory=demand, episode_runner=episode,
        artifact_copier=lambda _result, _destination: None, observer_writer=observer,
    )
    assert len(observations) == 3
    assert all(call["planner_mode"] == DETERMINISTIC_CANDIDATE for call in calls)
    assert all(call["api_key"] == "" and call["strict_llm_mode"] is False for call in calls)
    assert "phase2_formal" not in str(tmp_path / "results")


def test_pure_observer_work_does_not_touch_frozen_phase2_evidence():
    before = hashlib.sha256(FROZEN_PHASE2.read_bytes()).hexdigest()
    build_fixed_demand(1)
    waiting_metrics([])
    stage1_feasibility([])
    after = hashlib.sha256(FROZEN_PHASE2.read_bytes()).hexdigest()
    assert before == after


def _fake_stage2_generation(seed: int) -> dict:
    return {
        "scenario_id": f"directional_stress_seed{seed}",
        "scenario_class": CONDITION,
        "vehicle_count": 16,
        "seed": seed,
        "route_sequence": list(FIXED_ROUTE_SEQUENCE),
        "departure_times": list(FIXED_BASE_DEPARTURES),
        "movement_sequence": ["RIGHT"] * 16,
        "seed_semantics": {},
        "initial_demand_signature": f"signature-{seed}",
        "target_smaller_vehicle_ids": ["straight-n", "straight-s"],
    }


def _expected_initial_conditions() -> dict[int, dict]:
    from src.experiments.phase2_closed_loop import initial_condition_record

    return {
        seed: initial_condition_record(_fake_stage2_generation(seed))
        for seed in SEEDS
    }


def _valid_stage2_observer(_path, result, _targets):
    return {
        **_summary(
            GEMINI_CANDIDATE,
            llm_valid_decisions=1,
            llm_failed_decisions=0,
            fallback_decisions=0,
            llm_episode_valid=True,
        ),
        "seed_from_result": result["seed"],
    }


def _strict_failure_record(kind: str, secret: str) -> dict:
    record = {
        "provider_request_success": True,
        "provider_failure_reason": "",
        "exception_type": "",
        "exception_message_redacted": "",
        "http_status": 200,
        "parser_success": True,
        "parser_failure_reason": "",
        "fallback_used": False,
        "selected_candidate_id": "right-group",
        "candidate_ranking": [{"candidate_id": "right-group"}, {"candidate_id": "straight-group"}],
        "latency_ms": 123.0,
        "llm_raw_output": '{"selected_candidate_id":"right-group"}',
        "response_content_redacted": "safe response",
    }
    if kind == "provider":
        record.update({
            "provider_request_success": False,
            "provider_failure_reason": "NETWORK_FAILURE",
            "exception_type": "TimeoutError",
            "exception_message_redacted": f"request failed with {secret}",
            "http_status": None,
            "parser_success": False,
            "parser_failure_reason": "PROVIDER_FAILURE",
            "fallback_used": True,
        })
    elif kind == "parser":
        record.update({
            "parser_success": False,
            "parser_failure_reason": "INVALID_OUTPUT_CONTRACT",
            "fallback_used": True,
        })
    elif kind == "fallback":
        record["fallback_used"] = True
    return record


@pytest.mark.parametrize("failure_kind", ["provider", "parser", "fallback"])
def test_strict_failure_persists_required_sanitized_evidence_and_nonzero_status(
    tmp_path, monkeypatch, failure_kind
):
    module = _runner_module()
    monkeypatch.setattr(
        module,
        "_new_manifest",
        lambda stage: {"stage": stage, "status": "running", "runs": []},
    )
    secret = "TEST_GEMINI_SECRET_123"

    def episode(_generation, **_kwargs):
        record = _strict_failure_record(failure_kind, secret)
        raise StrictLLMFailure("STRICT_LLM_INVALID_DECISION", record)

    root = tmp_path / "stage2"
    observations = module.run_specs(
        root,
        STAGE2,
        api_key=secret,
        demand_factory=_fake_stage2_generation,
        episode_runner=episode,
        artifact_copier=lambda _result, _destination: None,
        observer_writer=_valid_stage2_observer,
        expected_initial_conditions=_expected_initial_conditions(),
    )
    manifest = json.loads((root / f"{STAGE2}_manifest.json").read_text(encoding="utf-8"))
    assert observations == []
    assert manifest["status"] == "invalid"
    assert manifest["invalid_episode_count"] == 3
    assert module.stage2_exit_code(manifest) != 0
    assert len(manifest["runs"]) == 3
    for row in manifest["runs"]:
        output = Path(row["output"])
        failure = json.loads((output / "failure.json").read_text(encoding="utf-8"))
        decision = json.loads((output / "failure_decision.json").read_text(encoding="utf-8"))
        assert failure["status"] == "INVALID"
        assert failure["llm_episode_valid"] is False
        assert decision["strict_valid"] is False
        assert decision["llm_episode_valid"] is False
        assert decision["failure_reason"] == "STRICT_LLM_INVALID_DECISION"
        for field in (
            "provider_request_success", "provider_failure_reason", "exception_type",
            "exception_message_redacted", "http_status", "parser_success",
            "parser_failure_reason", "fallback_used", "selected_candidate_id",
            "selected_candidate_is_legal", "latency_ms", "llm_raw_output",
            "response_content_redacted",
        ):
            assert field in decision
        combined = (output / "failure.json").read_text(encoding="utf-8") + (
            output / "failure_decision.json"
        ).read_text(encoding="utf-8") + json.dumps(row)
        assert secret not in combined


def test_all_strict_valid_stage2_runs_have_no_failure_artifacts_and_exit_zero(tmp_path, monkeypatch):
    module = _runner_module()
    monkeypatch.setattr(module, "_new_manifest", lambda stage: {"stage": stage, "status": "running", "runs": []})
    calls = []

    def episode(generation, **kwargs):
        calls.append((generation["seed"], kwargs))
        return {"seed": generation["seed"], "summary": _summary(GEMINI_CANDIDATE), "artifact_paths": {"run_dir": "unused"}}

    root = tmp_path / "stage2"
    observations = module.run_specs(
        root, STAGE2, api_key="secret", demand_factory=_fake_stage2_generation,
        episode_runner=episode, artifact_copier=lambda _result, _destination: None,
        observer_writer=_valid_stage2_observer,
        expected_initial_conditions=_expected_initial_conditions(),
    )
    manifest = json.loads((root / f"{STAGE2}_manifest.json").read_text(encoding="utf-8"))
    assert len(observations) == 3 and len(calls) == 3
    assert manifest["status"] == "completed"
    assert module.stage2_exit_code(manifest) == 0
    assert all(call[1]["strict_llm_mode"] is True for call in calls)
    assert not list(root.rglob("failure*.json"))


def test_mixed_stage2_retains_success_and_failure_excludes_failed_seed_without_retry(
    tmp_path, monkeypatch
):
    module = _runner_module()
    monkeypatch.setattr(module, "_new_manifest", lambda stage: {"stage": stage, "status": "running", "runs": []})
    calls = []

    def episode(generation, **_kwargs):
        seed = generation["seed"]
        calls.append(seed)
        if seed == 2:
            raise StrictLLMFailure(
                "STRICT_LLM_INVALID_DECISION",
                _strict_failure_record("parser", "unused-secret"),
            )
        return {"seed": seed, "summary": _summary(GEMINI_CANDIDATE), "artifact_paths": {"run_dir": "unused"}}

    root = tmp_path / "stage2"
    observations = module.run_specs(
        root, STAGE2, api_key="secret", demand_factory=_fake_stage2_generation,
        episode_runner=episode, artifact_copier=lambda _result, _destination: None,
        observer_writer=_valid_stage2_observer,
        expected_initial_conditions=_expected_initial_conditions(),
    )
    manifest = json.loads((root / f"{STAGE2}_manifest.json").read_text(encoding="utf-8"))
    assert calls == [1, 2, 3]
    assert [item["seed"] for item in observations] == [1, 3]
    assert [row["status"] for row in manifest["runs"]] == ["valid", "invalid", "valid"]
    assert (Path(manifest["runs"][0]["output"]) / "directional_service_observer.json").is_file()
    assert (Path(manifest["runs"][1]["output"]) / "failure_decision.json").is_file()
    assert manifest["status"] == "invalid"
    assert module.stage2_exit_code(manifest) == 1


def test_stage2_generation_is_matched_before_episode_runner_is_called(tmp_path, monkeypatch):
    module = _runner_module()
    monkeypatch.setattr(module, "_new_manifest", lambda stage: {"stage": stage, "status": "running", "runs": []})
    calls = 0

    def episode(_generation, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("mismatched generation must fail before the episode")

    expected = _expected_initial_conditions()
    expected[1]["initial_demand_signature"] = "different"
    with pytest.raises(RuntimeError, match="seed1"):
        module.run_specs(
            tmp_path / "stage2", STAGE2, api_key="secret",
            demand_factory=_fake_stage2_generation, episode_runner=episode,
            artifact_copier=lambda _result, _destination: None,
            observer_writer=_valid_stage2_observer,
            expected_initial_conditions=expected,
        )
    assert calls == 0
