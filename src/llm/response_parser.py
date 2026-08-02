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
    try:
        payload = json.loads(_extract_json_text(response_text))
        decisions = payload.get("decisions", payload)
        if isinstance(decisions, list):
            parsed = {}
            for item in decisions:
                vid = item.get("vehicle_id")
                action = _normalize_action(item.get("decision", "WAIT"))
                if vid in vehicles:
                    parsed[vid] = action
        elif isinstance(decisions, dict):
            parsed = {}
            for vid in vehicles:
                parsed[vid] = _normalize_action(decisions.get(vid, "WAIT"))
        else:
            parsed = {}
        for vid in vehicles:
            parsed.setdefault(vid, "WAIT")
        return parsed, True
    except Exception:
        return {vid: "WAIT" for vid in vehicles}, False
