from __future__ import annotations

import json
import re


VALID_ACTIONS = {"PROCEED", "WAIT", "FREE"}


def _extract_json_text(response_text: str) -> str:
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        return fenced_match.group(1)
    object_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if object_match:
        return object_match.group()
    return response_text.strip()


def _normalize_action(action: object) -> str:
    if not isinstance(action, str):
        return "WAIT"
    action = action.strip().upper()
    return action if action in VALID_ACTIONS else "WAIT"


def parse_llm_response(response_text: str, vehicles: list[str]) -> tuple[dict[str, str], bool]:
    _, validated, ok = parse_llm_response_details(response_text, vehicles)
    return validated, ok


def parse_llm_response_details(response_text: str, vehicles: list[str]) -> tuple[dict[str, str], dict[str, str], bool]:
    try:
        payload = json.loads(_extract_json_text(response_text))
        decisions = payload.get("decisions", payload)
        raw_decisions = {}
        validated_decisions = {}
        if isinstance(decisions, list):
            for item in decisions:
                vid = item.get("vehicle_id")
                raw_action = item.get("decision", "MISSING")
                action = _normalize_action(raw_action)
                if vid in vehicles:
                    raw_decisions[vid] = raw_action if isinstance(raw_action, str) else "MISSING"
                    validated_decisions[vid] = action
        elif isinstance(decisions, dict):
            for vid in vehicles:
                raw_action = decisions.get(vid, "MISSING")
                raw_decisions[vid] = raw_action if isinstance(raw_action, str) else "MISSING"
                validated_decisions[vid] = _normalize_action(raw_action)
        else:
            raw_decisions = {vid: "MISSING" for vid in vehicles}
            validated_decisions = {vid: "WAIT" for vid in vehicles}
        for vid in vehicles:
            raw_decisions.setdefault(vid, "MISSING")
            validated_decisions.setdefault(vid, "WAIT")
        return raw_decisions, validated_decisions, True
    except Exception:
        raw_decisions = {vid: "MISSING" for vid in vehicles}
        validated_decisions = {vid: "WAIT" for vid in vehicles}
        return raw_decisions, validated_decisions, False
