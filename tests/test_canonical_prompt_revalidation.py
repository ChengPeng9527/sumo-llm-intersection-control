from __future__ import annotations

import json
import random

from src.experiments.canonical_prompt_revalidation import (
    PROMPT_IDS,
    build_prompt_comparison_rows,
    build_request_trace_rows,
    build_run_manifest,
    choose_prompt_order,
    group_rows_by_request,
    select_development_seed,
    should_allow_technical_rerun,
    summarize_request_groups,
    verify_frozen_request_config,
    verify_prompt_hashes,
)


def test_prompt_hash_verification_matches_expected():
    audit = verify_prompt_hashes()

    assert audit.matches is True
    assert audit.current == audit.expected


def test_frozen_request_config_verification_matches_expected():
    audit = verify_frozen_request_config()

    assert audit.matches is True
    assert audit.current == audit.expected
    assert audit.current["model"] == "openai/gpt-oss-20b"
    assert audit.current["max_completion_tokens"] == 512
    assert audit.current["reasoning_effort"] == "low"
    assert audit.current["timeout"] == 30.0
    assert audit.current["max_retries"] == 4


def test_execution_order_persistence_is_stable_in_manifest(tmp_path):
    rng = random.Random(7)
    seed = select_development_seed(rng=rng)
    order = choose_prompt_order(rng=random.Random(11))
    manifest = build_run_manifest(
        selected_seed=seed,
        prompt_order=order,
        prompt_hash_audit=verify_prompt_hashes(),
        request_config_audit=verify_frozen_request_config(),
        vehicle_count=4,
        density="low",
        scenario_id="canonical_prompt_revalidation_seed404_v4",
    )

    assert manifest["selected_seed"] == seed
    assert manifest["prompt_order"] == order
    assert manifest["prompt_order"] != list(PROMPT_IDS)

    path = tmp_path / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    restored = json.loads(path.read_text(encoding="utf-8"))
    assert restored["prompt_order"] == order
    assert restored["selected_seed"] == seed


def test_provider_failure_excluded_from_prompt_comparison():
    rows = [
        {
            "llm_called": "True",
            "simulation_step": "1",
            "provider_request_success": "True",
            "parser_success": "True",
            "fallback_used": "False",
            "fallback_triggered": "False",
            "validated_llm_decision": "PROCEED",
            "parser_action": "PROCEED",
            "llm_response_time_ms": "12.5",
            "response_content_length": "18",
        },
        {
            "llm_called": "True",
            "simulation_step": "2",
            "provider_request_success": "False",
            "parser_success": "False",
            "fallback_used": "True",
            "fallback_triggered": "True",
            "validated_llm_decision": "WAIT",
            "parser_action": "MISSING",
            "llm_response_time_ms": "99.0",
            "response_content_length": "0",
        },
    ]

    grouped = group_rows_by_request(rows)
    summary = summarize_request_groups(grouped)

    assert summary["total_live_requests"] == 2
    assert summary["provider_success_count"] == 1
    assert summary["provider_failure_count"] == 1
    assert summary["parser_success_given_provider_success"] == 1.0
    assert summary["semantic_fallback_given_provider_success"] == 0.0
    assert summary["genuine_proceed_count"] == 1
    assert summary["genuine_wait_count"] == 0
    assert summary["genuine_free_count"] == 0


def test_technical_rerun_limit():
    assert should_allow_technical_rerun(0, 0) is True
    assert should_allow_technical_rerun(0, 1) is False
    assert should_allow_technical_rerun(1, 0) is False


def test_prompt_comparison_rows_aggregate_technical_reruns():
    prompt_results = [
        {
            "prompt_id": "P1_BASELINE",
            "seed": 404,
            "vehicle_count": 4,
            "technical_rerun": False,
            "request_groups": [
                [
                    {
                        "llm_called": "True",
                        "simulation_step": "1",
                        "provider_request_success": "True",
                        "parser_success": "True",
                        "fallback_used": "False",
                        "fallback_triggered": "False",
                        "validated_llm_decision": "PROCEED",
                        "parser_action": "PROCEED",
                        "llm_response_time_ms": "10",
                        "response_content_length": "12",
                    }
                ]
            ],
        },
        {
            "prompt_id": "P1_BASELINE",
            "seed": 404,
            "vehicle_count": 4,
            "technical_rerun": True,
            "request_groups": [
                [
                    {
                        "llm_called": "True",
                        "simulation_step": "2",
                        "provider_request_success": "True",
                        "parser_success": "True",
                        "fallback_used": "False",
                        "fallback_triggered": "False",
                        "validated_llm_decision": "WAIT",
                        "parser_action": "WAIT",
                        "llm_response_time_ms": "20",
                        "response_content_length": "14",
                    }
                ]
            ],
        },
    ]

    rows = build_prompt_comparison_rows(prompt_results)
    p1 = next(row for row in rows if row["prompt_id"] == "P1_BASELINE")

    assert p1["run_count"] == 2
    assert p1["technical_rerun_count"] == 1
    assert p1["provider_success_count"] == 2
    assert p1["genuine_proceed_count"] == 1
    assert p1["genuine_wait_count"] == 1
    assert p1["mean_successful_request_latency_ms"] == 15.0


def test_request_trace_rows_include_gate_diagnostics():
    rows = [
        {
            "llm_called": "True",
            "simulation_step": "7",
            "provider_request_success": "False",
            "parser_success": "False",
            "fallback_used": "True",
            "fallback_triggered": "True",
            "fallback_reason": "MISSING_CREDENTIAL",
            "llm_branch_entered": "True",
            "live_provider_gate_entered": "True",
            "live_provider_enabled": "True",
            "credential_available": "False",
            "live_client_constructed": "False",
            "provider_call_function_entered": "False",
            "provider_request_kwargs_built": "False",
            "provider_request_attempted": "False",
            "provider_request_skipped": "True",
            "provider_skip_reason": "MISSING_CREDENTIAL",
            "fallback_trigger_reason": "MISSING_CREDENTIAL",
            "llm_raw_decision": "FREE",
            "validated_llm_decision": "FREE",
            "final_decision": "FREE",
            "response_content_length": "0",
        }
    ]

    trace_rows = build_request_trace_rows(prompt_id="P1_BASELINE", request_groups=[rows], technical_rerun=False)

    assert trace_rows[0]["prompt_id"] == "P1_BASELINE"
    assert trace_rows[0]["provider_request_attempted"] is False
    assert trace_rows[0]["provider_request_skipped"] is True
    assert trace_rows[0]["provider_skip_reason"] == "MISSING_CREDENTIAL"
    assert trace_rows[0]["fallback_trigger_reason"] == "MISSING_CREDENTIAL"

