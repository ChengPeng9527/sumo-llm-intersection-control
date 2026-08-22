from src.controllers.decision_pipeline import execute_llm_candidate_selector_pipeline
from src.llm.candidate_selector import (
    build_candidate_selection_context,
    select_candidate_with_llm,
    summarize_candidate_selections,
)
from src.llm.prompt_builder import build_candidate_selection_prompt
from src.llm.response_parser import parse_candidate_selection_response
from src.safety.cooperative_comparator import select_candidate_group
from tests.fakes import FixedSafetyGuard


def _state(vehicle_id, route_id, *, waiting=0.0, tti=5.0, inside=True):
    incoming, outgoing = route_id.split("_")
    movements = {
        "N_S": "STRAIGHT",
        "S_N": "STRAIGHT",
        "E_W": "STRAIGHT",
        "W_E": "STRAIGHT",
    }
    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "incoming_edge": incoming,
        "outgoing_edge": f"-{outgoing}",
        "movement": movements[route_id],
        "waiting_time": waiting,
        "speed": 4.0,
        "time_to_intersection": tti,
        "inside_control_zone": inside,
        "origin": "private-origin",
        "destination": "private-destination",
        "route_history": ["private-history"],
    }


def _scenario():
    states = [
        _state("a", "N_S", waiting=3, tti=2),
        _state("b", "S_N", waiting=2, tti=3),
        _state("c", "E_W", waiting=1, tti=1),
        _state("outside", "W_E", inside=False),
    ]
    groups = [["a"], ["b"], ["c"], ["a", "b"]]
    return states, groups


def _response(candidate_id):
    return f'{{"selected_candidate_id":"{candidate_id}"}}'


def test_candidate_prompt_uses_only_local_state_and_supplied_candidate_features():
    states, groups = _scenario()
    local_state, candidate_features, _ = build_candidate_selection_context(states, groups)
    prompt = build_candidate_selection_prompt(local_state, candidate_features)

    assert [candidate["candidate_id"] for candidate in candidate_features] == ["a", "b", "c", "a|b"]
    assert "selected_candidate_id" in prompt
    assert "route_id" not in prompt
    assert "private-origin" not in prompt
    assert "private-destination" not in prompt
    assert "private-history" not in prompt


def test_strict_candidate_parser_accepts_one_known_candidate():
    assert parse_candidate_selection_response(_response("a|b"), ["a", "a|b"]) == ("a|b", True, "")


def test_strict_candidate_parser_rejects_malformed_unknown_and_multiple_selection():
    assert parse_candidate_selection_response("not json", ["a"])[2] == "MALFORMED_JSON"
    assert parse_candidate_selection_response(_response("unknown"), ["a"]) == (
        "unknown",
        False,
        "UNKNOWN_CANDIDATE_ID",
    )
    assert parse_candidate_selection_response('{"selected_candidate_id":["a","b"]}', ["a", "b"])[2] == (
        "MULTIPLE_OR_ILLEGAL_SELECTION"
    )
    assert parse_candidate_selection_response('{"selected_candidate_id":"a","other":"b"}', ["a"])[2] == (
        "INVALID_OUTPUT_CONTRACT"
    )


def test_valid_llm_selection_logs_agreement_and_disagreement():
    states, groups = _scenario()
    agreement = select_candidate_with_llm(states, groups, lambda prompt: _response("a|b"))
    disagreement = select_candidate_with_llm(states, groups, lambda prompt: _response("c"))

    assert agreement.deterministic_candidate_id == "a|b"
    assert agreement.llm_candidate_id == "a|b"
    assert agreement.candidate_agreement is True
    assert agreement.provider_success is True
    assert agreement.fallback_used is False
    assert disagreement.deterministic_candidate_id == "a|b"
    assert disagreement.llm_candidate_id == "c"
    assert disagreement.candidate_disagreement is True
    assert disagreement.fallback_used is False


def test_unknown_candidate_falls_back_to_step4_comparator_over_same_candidates():
    states, groups = _scenario()
    result = select_candidate_with_llm(states, groups, lambda prompt: _response("invented"))

    assert result.fallback_used is True
    assert result.fallback_reason == "UNKNOWN_CANDIDATE_ID"
    assert result.fallback_selected_candidate == "a|b"
    assert result.final_selected_candidate == "a|b"
    assert result.deterministic_candidate_id == select_candidate_group(states, groups).selected_candidate_id
    assert result.final_selected_candidate in {candidate["candidate_id"] for candidate in result.candidate_features}


def test_malformed_output_falls_back_to_step4_comparator():
    states, groups = _scenario()
    result = select_candidate_with_llm(states, groups, lambda prompt: "not json")

    assert result.provider_success is True
    assert result.parser_success is False
    assert result.fallback_used is True
    assert result.fallback_reason == "MALFORMED_JSON"
    assert result.final_selected_candidate == "a|b"


def test_provider_failure_uses_deterministic_fallback():
    states, groups = _scenario()

    def failed_provider(prompt):
        raise RuntimeError("provider unavailable")

    result = select_candidate_with_llm(states, groups, failed_provider)

    assert result.provider_success is False
    assert result.parser_success is False
    assert result.fallback_used is True
    assert result.fallback_reason == "PROVIDER_FAILURE"
    assert result.final_selected_candidate == "a|b"
    assert result.selection_source == "DETERMINISTIC_FALLBACK"


def test_pipeline_converts_candidate_to_actions_and_preserves_provenance():
    states, groups = _scenario()
    trace = execute_llm_candidate_selector_pipeline(states, groups, lambda prompt: _response("c"))

    assert trace["c"]["postprocessed_decision"] == "PROCEED"
    assert trace["a"]["postprocessed_decision"] == "WAIT"
    assert trace["b"]["postprocessed_decision"] == "WAIT"
    assert trace["outside"]["final_decision"] == "FREE"
    assert trace["c"]["llm_candidate_id"] == "c"
    assert trace["c"]["deterministic_candidate_id"] == "a|b"
    assert trace["c"]["candidate_disagreement"] is True
    assert trace["c"]["selection_source"] == "LLM_CANDIDATE"
    assert trace["c"]["fallback_used"] is False


def test_safety_guard_remains_downstream_and_does_not_erase_selection_provenance():
    states, groups = _scenario()
    safety = FixedSafetyGuard({"c": "WAIT"})
    trace = execute_llm_candidate_selector_pipeline(
        states,
        groups,
        lambda prompt: _response("c"),
        safety_guard_fn=safety,
    )

    assert safety.calls == 1
    assert trace["c"]["postprocessed_decision"] == "PROCEED"
    assert trace["c"]["final_decision"] == "WAIT"
    assert trace["c"]["safety_intervened"] is True
    assert trace["c"]["selection_source"] == "LLM_CANDIDATE"
    assert trace["c"]["llm_candidate_id"] == "c"


def test_agreement_summary_counts_only_comparable_llm_decisions():
    states, groups = _scenario()
    results = [
        select_candidate_with_llm(states, groups, lambda prompt: _response("a|b")),
        select_candidate_with_llm(states, groups, lambda prompt: _response("c")),
        select_candidate_with_llm(states, groups, lambda prompt: _response("unknown")),
    ]

    assert summarize_candidate_selections(results) == {
        "comparable_decisions": 2,
        "agreement_count": 1,
        "disagreement_count": 1,
        "agreement_rate": 0.5,
    }
