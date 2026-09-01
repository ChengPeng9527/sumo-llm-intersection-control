from src.experiments.llm_validity import is_valid_llm_decision, summarize_llm_validity
def test_validity_contract_and_zero_decision():
 assert is_valid_llm_decision({'provider_request_success':True,'parser_success':True,'fallback_used':False})
 assert not summarize_llm_validity([],llm_evaluation=True)['llm_episode_valid']
def test_failures_and_robustness_are_invalid():
 r={'provider_request_success':False,'parser_success':False,'fallback_used':True}
 assert summarize_llm_validity([r],llm_evaluation=True)['llm_episode_valid'] is False
 assert summarize_llm_validity([r],llm_evaluation=False)['llm_episode_valid'] is None
