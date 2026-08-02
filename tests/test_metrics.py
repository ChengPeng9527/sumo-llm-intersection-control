from src.common.metrics import calculate_summary, empty_record


def test_empty_record_contains_unified_fields():
    record = empty_record(run_id="r1", experiment_id="e1", controller="c1")
    assert record["run_id"] == "r1"
    assert record["experiment_id"] == "e1"
    assert record["controller"] == "c1"
    assert "safety_override" in record
    assert "llm_response_time_ms" in record
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
    summary = calculate_summary(records, run_metadata={"departed_count": 2, "arrived_count": 1})
    assert summary["vehicles_observed"] == 2
    assert summary["departed"] == 2
    assert summary["arrived"] == 1
    assert summary["completion_rate"] == 0.5
