from __future__ import annotations

import json
import re


VALID_ACTIONS = {"PROCEED", "WAIT", "FREE"}
ACTION_LABELS = ("action", "decision")


def _build_fallback(vehicles: list[str]) -> tuple[dict[str, str], dict[str, str], bool]:
    raw_decisions = {vid: "MISSING" for vid in vehicles}
    validated_decisions = {vid: "WAIT" for vid in vehicles}
    return raw_decisions, validated_decisions, False


def _coerce_action(action: object) -> tuple[str, bool]:
    if not isinstance(action, str):
        return "WAIT", False
    normalized = action.strip().upper()
    if normalized in VALID_ACTIONS:
        return normalized, True
    return "WAIT", False


def _extract_json_text(response_text: str) -> str:
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        candidate = fenced_match.group(1).strip()
        if candidate:
            return candidate
    stripped = response_text.strip()
    start_indexes = [index for index in (stripped.find("["), stripped.find("{")) if index != -1]
    if start_indexes:
        candidate = stripped[min(start_indexes):]
        try:
            _, end = json.JSONDecoder().raw_decode(candidate)
            return candidate[:end]
        except json.JSONDecodeError:
            pass
    return response_text.strip()


def _find_textual_action(response_text: str) -> tuple[str, bool]:
    text = response_text.strip()
    if not text:
        return "WAIT", False

    def _extract_label(pattern: str) -> tuple[str, bool]:
        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
        if not matches:
            return "WAIT", False
        actions = {match.group(1).upper() for match in matches if match.group(1).upper() in VALID_ACTIONS}
        if len(actions) != 1:
            return "WAIT", False
        chosen = next(iter(actions))
        remaining = text
        for match in reversed(matches):
            remaining = remaining[:match.start()] + remaining[match.end():]
        other_actions = {action.upper() for action in re.findall(r"\b(PROCEED|WAIT|FREE)\b", remaining, re.IGNORECASE)}
        if other_actions and other_actions != {chosen}:
            return "WAIT", False
        return chosen, True

    final_action, ok = _extract_label(r"\bfinal decision\b\s*[:\-]?\s*(PROCEED|WAIT|FREE)\b")
    if ok:
        return final_action, True

    decision_action, ok = _extract_label(r"\bdecision\b\s*[:\-]?\s*(PROCEED|WAIT|FREE)\b")
    if ok:
        return decision_action, True

    action_tokens = {token.upper() for token in re.findall(r"\b(PROCEED|WAIT|FREE)\b", text, re.IGNORECASE)}
    if len(action_tokens) == 1:
        return next(iter(action_tokens)), True
    return "WAIT", False


def _normalize_action(action: object) -> str:
    normalized, _ = _coerce_action(action)
    return normalized


def _resolve_exact_vehicle_mapping(payload: dict[str, object], vehicles: list[str]) -> tuple[dict[str, str], dict[str, str], bool]:
    vehicle_ids = set(vehicles)
    if set(payload.keys()) != vehicle_ids:
        return _build_fallback(vehicles)
    raw_decisions: dict[str, str] = {}
    validated_decisions: dict[str, str] = {}
    for vid in vehicles:
        action, ok = _coerce_action(payload.get(vid))
        if not ok:
            return _build_fallback(vehicles)
        raw_decisions[vid] = action
        validated_decisions[vid] = action
    return raw_decisions, validated_decisions, True


def _resolve_decision_object(payload: dict[str, object], vehicles: list[str]) -> tuple[dict[str, str], dict[str, str], bool]:
    vehicle_ids = set(vehicles)
    if "decisions" in payload:
        decisions = payload.get("decisions")
        if isinstance(decisions, dict):
            return _resolve_exact_vehicle_mapping(decisions, vehicles)
        if isinstance(decisions, list):
            return _resolve_decision_payload(decisions, vehicles)
        return _build_fallback(vehicles)

    if "vehicle_id" in payload and any(label in payload for label in ACTION_LABELS):
        vehicle_id = payload.get("vehicle_id")
        if not isinstance(vehicle_id, str) or vehicle_id not in vehicle_ids:
            return _build_fallback(vehicles)
        raw_action = payload.get("action", payload.get("decision"))
        action, ok = _coerce_action(raw_action)
        if not ok:
            return _build_fallback(vehicles)
        return {vehicle_id: action, **{vid: "MISSING" for vid in vehicles if vid != vehicle_id}}, {vehicle_id: action, **{vid: "WAIT" for vid in vehicles if vid != vehicle_id}}, True

    direct_action = None
    direct_label = None
    for label in ACTION_LABELS:
        if label in payload:
            direct_label = label
            direct_action = payload.get(label)
            break
    if direct_label is not None:
        if len(vehicles) != 1:
            return _build_fallback(vehicles)
        action, ok = _coerce_action(direct_action)
        if not ok:
            return _build_fallback(vehicles)
        vid = vehicles[0]
        return {vid: action}, {vid: action}, True

    raw_decisions = {}
    validated_decisions = {}
    seen_any_current_vehicle = False
    for vid in vehicles:
        if vid in payload:
            seen_any_current_vehicle = True
            action, ok = _coerce_action(payload.get(vid))
            if not ok:
                return _build_fallback(vehicles)
            raw_decisions[vid] = action
            validated_decisions[vid] = action
    if seen_any_current_vehicle and len(raw_decisions) == len(vehicles):
        for vid in vehicles:
            raw_decisions.setdefault(vid, "MISSING")
            validated_decisions.setdefault(vid, "WAIT")
        return raw_decisions, validated_decisions, True
    return _build_fallback(vehicles)


def _resolve_decision_payload(payload: object, vehicles: list[str]) -> tuple[dict[str, str], dict[str, str], bool]:
    if not vehicles:
        return {}, {}, True
    if isinstance(payload, list):
        raw_decisions = {vid: "MISSING" for vid in vehicles}
        validated_decisions = {vid: "WAIT" for vid in vehicles}
        seen_vehicle_ids: set[str] = set()
        for item in payload:
            if not isinstance(item, dict):
                return _build_fallback(vehicles)
            vehicle_id = item.get("vehicle_id")
            if not isinstance(vehicle_id, str):
                return _build_fallback(vehicles)
            if vehicle_id not in vehicles:
                return _build_fallback(vehicles)
            if vehicle_id in seen_vehicle_ids:
                return _build_fallback(vehicles)
            raw_action = item.get("action", item.get("decision"))
            action, ok = _coerce_action(raw_action)
            if not ok:
                return _build_fallback(vehicles)
            seen_vehicle_ids.add(vehicle_id)
            raw_decisions[vehicle_id] = action
            validated_decisions[vehicle_id] = action
        if seen_vehicle_ids != set(vehicles):
            return _build_fallback(vehicles)
        return raw_decisions, validated_decisions, True
    if isinstance(payload, dict):
        return _resolve_decision_object(payload, vehicles)
    return _build_fallback(vehicles)


def _parse_textual_response(response_text: str, vehicles: list[str]) -> tuple[dict[str, str], dict[str, str], bool]:
    if not vehicles:
        return {}, {}, True
    action, ok = _find_textual_action(response_text)
    if not ok:
        return _build_fallback(vehicles)
    if len(vehicles) != 1:
        return _build_fallback(vehicles)
    vid = vehicles[0]
    return {vid: action}, {vid: action}, True


def parse_llm_response(response_text: str, vehicles: list[str]) -> tuple[dict[str, str], bool]:
    _, validated, ok = parse_llm_response_details(response_text, vehicles)
    return validated, ok


def parse_llm_response_details(response_text: str, vehicles: list[str]) -> tuple[dict[str, str], dict[str, str], bool]:
    try:
        payload = json.loads(_extract_json_text(response_text))
        raw_decisions, validated_decisions, ok = _resolve_decision_payload(payload, vehicles)
        if ok:
            return raw_decisions, validated_decisions, True
        return _build_fallback(vehicles)
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return _parse_textual_response(response_text, vehicles)


def parse_candidate_selection_response(
    response_text: str,
    candidate_ids: list[str] | tuple[str, ...],
) -> tuple[str, bool, str]:
    if not isinstance(response_text, str) or not response_text.strip():
        return "", False, "EMPTY_RESPONSE"
    try:
        payload = json.loads(response_text.strip())
    except (json.JSONDecodeError, TypeError, ValueError):
        return "", False, "MALFORMED_JSON"
    if not isinstance(payload, dict) or set(payload) != {"selected_candidate_id"}:
        return "", False, "INVALID_OUTPUT_CONTRACT"
    selected_candidate_id = payload.get("selected_candidate_id")
    if not isinstance(selected_candidate_id, str):
        return "", False, "MULTIPLE_OR_ILLEGAL_SELECTION"
    selected_candidate_id = selected_candidate_id.strip()
    if selected_candidate_id not in set(candidate_ids):
        return selected_candidate_id, False, "UNKNOWN_CANDIDATE_ID"
    return selected_candidate_id, True, ""
