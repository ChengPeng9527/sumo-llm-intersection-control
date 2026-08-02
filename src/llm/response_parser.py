from __future__ import annotations

import json
import re


VALID_ACTIONS = {"PROCEED", "WAIT", "FREE"}


def parse_llm_response(response_text: str, vehicles: list[str]) -> tuple[dict[str, str], bool]:
    try:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        payload = json.loads(match.group() if match else response_text)
        decisions = payload.get("decisions", payload)
        if isinstance(decisions, list):
            parsed = {}
            for item in decisions:
                vid = item.get("vehicle_id")
                action = str(item.get("decision", "WAIT")).upper()
                if vid in vehicles and action in VALID_ACTIONS:
                    parsed[vid] = action
        elif isinstance(decisions, dict):
            parsed = {}
            for vid in vehicles:
                action = str(decisions.get(vid, "WAIT")).upper()
                if action not in VALID_ACTIONS:
                    action = "WAIT"
                parsed[vid] = action
        else:
            parsed = {}
        for vid in vehicles:
            parsed.setdefault(vid, "WAIT")
        return parsed, True
    except Exception:
        return {vid: "WAIT" for vid in vehicles}, False
