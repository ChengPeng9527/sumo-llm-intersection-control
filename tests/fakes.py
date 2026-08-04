from __future__ import annotations


class StubDecisionProvider:
    def __init__(self, decisions: dict[str, str], meta: dict | None = None):
        self._decisions = dict(decisions)
        self._meta = dict(meta or {})
        self.calls = 0

    def __call__(self, vehicle_states: list[dict]) -> tuple[dict[str, str], dict]:
        self.calls += 1
        return dict(self._decisions), dict(self._meta)


class PassThroughPostprocessor:
    def __init__(self):
        self.calls = 0

    def __call__(self, trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
        self.calls += 1
        return {vid: dict(entry) for vid, entry in trace.items()}


class FixedPostprocessor:
    def __init__(self, updates: dict[str, str]):
        self._updates = dict(updates)
        self.calls = 0

    def __call__(self, trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
        self.calls += 1
        updated = {vid: dict(entry) for vid, entry in trace.items()}
        for vid, decision in self._updates.items():
            if vid not in updated:
                continue
            updated[vid]["postprocessed_decision"] = decision
            updated[vid]["postprocess_applied"] = True
            updated[vid]["postprocess_reason"] = "fixed_postprocessor"
            updated[vid]["decision_source"] = "COOPERATIVE_POSTPROCESSOR"
        return updated


class PassThroughSafetyGuard:
    def __init__(self):
        self.calls = 0

    def __call__(self, trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
        self.calls += 1
        return {vid: dict(entry) for vid, entry in trace.items()}


class FixedSafetyGuard:
    def __init__(self, overrides: dict[str, str]):
        self._overrides = dict(overrides)
        self.calls = 0

    def __call__(self, trace: dict[str, dict], vehicle_states: list[dict]) -> dict[str, dict]:
        self.calls += 1
        updated = {vid: dict(entry) for vid, entry in trace.items()}
        for vid, decision in self._overrides.items():
            if vid not in updated:
                continue
            updated[vid]["final_decision"] = decision
            updated[vid]["safety_override"] = decision != updated[vid].get("postprocessed_decision")
            updated[vid]["safety_reason"] = "fixed_guard"
            if updated[vid]["safety_override"]:
                updated[vid]["decision_source"] = "SAFETY_VERIFIER"
        return updated
