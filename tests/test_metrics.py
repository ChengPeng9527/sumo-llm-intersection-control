from types import SimpleNamespace

from src.common.logging_schema import FIELDNAMES
from src.common.metrics import calculate_summary, empty_record
import common


def test_empty_record_contains_unified_fields():
    record = empty_record(run_id="r1", experiment_id="e1", controller="c1")
    assert record["run_id"] == "r1"
    assert record["experiment_id"] == "e1"
    assert record["controller"] == "c1"
    assert record["vehicle_count"] == 4
    assert "safety_override" in record
    assert "llm_response_time_ms" in record
    assert "finish_reason" in record
    assert "completion_tokens" in record
    assert "priority_reason" in record


def test_calculate_summary_uses_unified_schema():
    records = [
        empty_record(
            run_id="r1",
            experiment_id="e1",
            controller="c1",
            vehicle_id="veh0",
            speed_after_action=0.0,
            final_decision="WAIT",
        ),
        empty_record(
            run_id="r1",
            experiment_id="e1",
            controller="c1",
            vehicle_id="veh1",
            speed_after_action=5.0,
            final_decision="PROCEED",
        ),
    ]
    summary = calculate_summary(records, run_metadata={"departed_count": 2, "arrived_count": 1, "vehicle_count": 8})
    assert summary["vehicles_observed"] == 2
    assert summary["departed"] == 2
    assert summary["arrived"] == 1
    assert summary["completion_rate"] == 0.5
    assert summary["vehicle_count"] == 8


def test_logging_schema_fieldnames_are_unique():
    assert len(FIELDNAMES) == len(set(FIELDNAMES))


class _FakeTraciVehicle:
    def getRouteID(self, veh_id):
        return "N_S"

    def getSpeed(self, veh_id):
        return 5.0

    def getPosition(self, veh_id):
        return (0.0, 0.0)


class _FakeTraci:
    def __init__(self):
        self.vehicle = _FakeTraciVehicle()


def _patch_common_geometry(monkeypatch):
    monkeypatch.setattr(common, "get_vehicle_route", lambda traci, veh_id: "N_S")
    monkeypatch.setattr(common, "route_direction_from_route_id", lambda route_id: "north_south")
    monkeypatch.setattr(common, "distance_to_center", lambda traci, veh_id: 12.0)
    monkeypatch.setattr(common, "estimate_time_to_intersection", lambda traci, veh_id: 2.4)
    monkeypatch.setattr(common, "is_in_control_zone", lambda traci, veh_id: True)


def test_create_record_preserves_request_provenance_for_shared_request(monkeypatch):
    _patch_common_geometry(monkeypatch)
    traci = _FakeTraci()
    provenance = {
        "request_id": "req-123",
        "request_simulation_step": 7,
        "http_attempt_id": 1,
        "prompt_hash": "HASH123",
        "request_started_at": "2026-08-18T10:00:00.000+00:00",
        "request_finished_at": "2026-08-18T10:00:01.000+00:00",
        "requested_provider": "Gemini",
        "requested_model": "gemini-3.6-flash",
        "actual_provider": "Gemini",
        "actual_model": "gemini-3.6-flash",
        "provider_switch_count": 0,
        "provider_chain": ("Gemini",),
        "provider_failure_reason": "",
        "provider_success": True,
        "provider_request_success": True,
        "provider_name": "Gemini",
        "model_name": "gemini-3.6-flash",
        "provider_request_attempted": True,
        "llm_called": True,
        "llm_mode": "real",
    }

    row1 = common.create_record(
        experiment_id="exp",
        controller="RawLLMController",
        scenario="scenario",
        seed=1,
        step=7,
        traci=traci,
        veh_id="veh0",
        raw_decision="PROCEED",
        final_decision="PROCEED",
        **provenance,
    )
    row2 = common.create_record(
        experiment_id="exp",
        controller="RawLLMController",
        scenario="scenario",
        seed=1,
        step=7,
        traci=traci,
        veh_id="veh1",
        raw_decision="WAIT",
        final_decision="WAIT",
        **provenance,
    )

    assert row1["request_id"] == "req-123"
    assert row2["request_id"] == "req-123"
    assert row1["request_simulation_step"] == 7
    assert row1["http_attempt_id"] == 1
    assert row1["prompt_hash"] == "HASH123"
    assert row1["request_started_at"] == "2026-08-18T10:00:00.000+00:00"
    assert row1["request_finished_at"] == "2026-08-18T10:00:01.000+00:00"
    assert row1["requested_provider"] == "Gemini"
    assert row1["actual_provider"] == "Gemini"
    assert row1["provider_success"] is True
    assert {row1["request_id"], row2["request_id"]} == {"req-123"}


def test_create_record_preserves_request_provenance_for_failure_fallback(monkeypatch):
    _patch_common_geometry(monkeypatch)
    traci = _FakeTraci()
    provenance = {
        "request_id": "req-fail",
        "request_simulation_step": 9,
        "http_attempt_id": 2,
        "prompt_hash": "HASHFAIL",
        "request_started_at": "2026-08-18T10:05:00.000+00:00",
        "request_finished_at": "2026-08-18T10:05:02.000+00:00",
        "requested_provider": "Gemini",
        "requested_model": "gemini-3.6-flash",
        "actual_provider": "Gemini",
        "actual_model": "gemini-3.6-flash",
        "provider_switch_count": 0,
        "provider_chain": ("Gemini",),
        "provider_failure_reason": "INTERNAL",
        "provider_success": False,
        "provider_request_success": False,
        "provider_name": "Gemini",
        "model_name": "gemini-3.6-flash",
        "provider_request_attempted": True,
        "fallback_used": True,
        "fallback_triggered": True,
        "fallback_reason": "PROVIDER_REQUEST_EXCEPTION",
        "exception_type": "ProviderRequestError",
        "exception_message_redacted": "internal",
        "llm_called": True,
        "llm_mode": "real",
    }

    row = common.create_record(
        experiment_id="exp",
        controller="RawLLMController",
        scenario="scenario",
        seed=1,
        step=9,
        traci=traci,
        veh_id="veh0",
        raw_decision="WAIT",
        final_decision="WAIT",
        **provenance,
    )

    assert row["request_id"] == "req-fail"
    assert row["http_attempt_id"] == 2
    assert row["fallback_used"] is True
    assert row["fallback_triggered"] is True
    assert row["provider_request_success"] is False
    assert row["provider_success"] is False
    assert row["provider_failure_reason"] == "INTERNAL"
    assert row["exception_type"] == "ProviderRequestError"
