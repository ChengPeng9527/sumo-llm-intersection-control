import pytest
from src.experiments.llm_validity import StrictLLMFailure, enforce_strict_llm_decision, summarize_llm_validity
from src.experiments.phase2_formal_matrix import summarize_conditions

@pytest.mark.parametrize('record',[{'provider_request_success':False,'parser_success':False,'fallback_used':True},{'provider_request_success':True,'parser_success':False,'fallback_used':True},{'provider_request_success':True,'parser_success':True,'fallback_used':True}])
def test_strict_invalid_decisions_fail_and_remain_invalid(record):
    with pytest.raises(StrictLLMFailure) as error: enforce_strict_llm_decision(record,strict_llm_mode=True)
    assert error.value.decision_record['strict_valid'] is False
    assert error.value.decision_record['failure_reason']=='STRICT_LLM_INVALID_DECISION'
    assert summarize_llm_validity([record],llm_evaluation=True)['llm_episode_valid'] is False
def test_aggregate_excludes_invalid_llm_and_keeps_deterministic():
    base={'departed':8,'arrived':8,'completion_rate':1,'throughput':8,'maximum_waiting_time':1,'collision_count':0}
    rows=[dict(base,scenario_class='S',vehicle_count=8,planner='GEMINI_CANDIDATE',seed=1,llm_episode_valid=False,mean_waiting_time=1,mean_speed=1,episode_duration_seconds=1,decision_epoch_count=1,grant_count=1,gemini_request_count=1,fallback_count=1,safety_intervention_count=0,grant_timeout_count=0,total_tokens=0),dict(base,scenario_class='S',vehicle_count=8,planner='DETERMINISTIC_CANDIDATE',seed=1,mean_waiting_time=1,mean_speed=1,episode_duration_seconds=1,decision_epoch_count=1,grant_count=1,gemini_request_count=0,fallback_count=0,safety_intervention_count=0,grant_timeout_count=0,total_tokens=0)]
    result=summarize_conditions(rows); by={row['planner']:row for row in result}; assert by['GEMINI_CANDIDATE']['seed_count']==0 and by['GEMINI_CANDIDATE']['excluded_llm_episodes']==1 and by['DETERMINISTIC_CANDIDATE']['seed_count']==1
