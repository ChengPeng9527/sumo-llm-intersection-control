from src.llm.response_parser import parse_llm_response


def test_parse_llm_response_handles_fenced_json():
    text = """```json
{
  "car0": "PROCEED",
  "car1": "invalid"
}
```"""

    decisions, ok = parse_llm_response(text, ["car0", "car1"])

    assert ok is True
    assert decisions["car0"] == "PROCEED"
    assert decisions["car1"] == "WAIT"


def test_parse_llm_response_falls_back_to_wait_on_bad_json():
    decisions, ok = parse_llm_response("not json", ["car0"])

    assert ok is False
    assert decisions["car0"] == "WAIT"
