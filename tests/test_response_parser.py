from src.llm.response_parser import parse_llm_response, parse_llm_response_details


def test_parse_llm_response_handles_fenced_json():
    text = """```json
{
  "car0": "PROCEED",
  "car1": "invalid"
}
```"""

    decisions, ok = parse_llm_response(text, ["car0", "car1"])

    assert ok is False
    assert decisions["car0"] == "WAIT"
    assert decisions["car1"] == "WAIT"


def test_parse_llm_response_falls_back_to_wait_on_bad_json():
    decisions, ok = parse_llm_response("not json", ["car0"])

    assert ok is False
    assert decisions["car0"] == "WAIT"


def test_parse_llm_response_handles_canonical_decisions_object_multi_vehicle():
    text = """{
  "decisions": {
    "car0": "PROCEED",
    "car1": "WAIT"
  }
}"""

    raw, validated, ok = parse_llm_response_details(text, ["car0", "car1"])

    assert ok is True
    assert raw["car0"] == "PROCEED"
    assert raw["car1"] == "WAIT"
    assert validated["car0"] == "PROCEED"
    assert validated["car1"] == "WAIT"


def test_parse_llm_response_rejects_canonical_decisions_missing_vehicle():
    text = """{
  "decisions": {
    "car0": "PROCEED"
  }
}"""

    decisions, ok = parse_llm_response(text, ["car0", "car1"])

    assert ok is False
    assert decisions["car0"] == "WAIT"
    assert decisions["car1"] == "WAIT"


def test_parse_llm_response_rejects_canonical_decisions_with_synthetic_vehicle():
    text = """{
  "decisions": {
    "car0": "PROCEED",
    "synthetic_car": "WAIT"
  }
}"""

    decisions, ok = parse_llm_response(text, ["car0"])

    assert ok is False
    assert decisions["car0"] == "WAIT"


def test_parse_llm_response_handles_top_level_json_list_single_vehicle_action():
    text = """[
  {
    "vehicle_id": "car0",
    "action": "PROCEED"
  }
]"""

    raw, validated, ok = parse_llm_response_details(text, ["car0"])

    assert ok is True
    assert raw["car0"] == "PROCEED"
    assert validated["car0"] == "PROCEED"


def test_parse_llm_response_handles_top_level_json_list_single_vehicle_decision_alias():
    text = """[
  {
    "vehicle_id": "car0",
    "decision": "WAIT"
  }
]"""

    raw, validated, ok = parse_llm_response_details(text, ["car0"])

    assert ok is True
    assert raw["car0"] == "WAIT"
    assert validated["car0"] == "WAIT"


def test_parse_llm_response_handles_top_level_json_list_multi_vehicle():
    text = """[
  {
    "vehicle_id": "car0",
    "action": "PROCEED"
  },
  {
    "vehicle_id": "car1",
    "action": "WAIT"
  }
]"""

    raw, validated, ok = parse_llm_response_details(text, ["car0", "car1"])

    assert ok is True
    assert raw["car0"] == "PROCEED"
    assert raw["car1"] == "WAIT"
    assert validated["car0"] == "PROCEED"
    assert validated["car1"] == "WAIT"


def test_parse_llm_response_rejects_conflicting_duplicate_vehicle():
    text = """[
  {
    "vehicle_id": "car0",
    "action": "WAIT"
  },
  {
    "vehicle_id": "car0",
    "action": "PROCEED"
  }
]"""

    decisions, ok = parse_llm_response(text, ["car0"])

    assert ok is False
    assert decisions["car0"] == "WAIT"


def test_parse_llm_response_rejects_unknown_vehicle_only():
    text = """[
  {
    "vehicle_id": "unknown",
    "action": "PROCEED"
  }
]"""

    decisions, ok = parse_llm_response(text, ["car0"])

    assert ok is False
    assert decisions["car0"] == "WAIT"


def test_parse_llm_response_rejects_missing_action():
    text = """[
  {
    "vehicle_id": "car0"
  }
]"""

    decisions, ok = parse_llm_response(text, ["car0"])

    assert ok is False
    assert decisions["car0"] == "WAIT"


def test_parse_llm_response_rejects_invalid_action():
    text = """[
  {
    "vehicle_id": "car0",
    "action": "GO"
  }
]"""

    decisions, ok = parse_llm_response(text, ["car0"])

    assert ok is False
    assert decisions["car0"] == "WAIT"


def test_parse_llm_response_handles_object_action():
    decisions, ok = parse_llm_response('{"action":"PROCEED"}', ["car0"])

    assert ok is True
    assert decisions["car0"] == "PROCEED"


def test_parse_llm_response_handles_object_decision_alias():
    decisions, ok = parse_llm_response('{"decision":"WAIT"}', ["car0"])

    assert ok is True
    assert decisions["car0"] == "WAIT"
