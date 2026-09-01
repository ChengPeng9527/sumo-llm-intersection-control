from __future__ import annotations

class StrictLLMFailure(RuntimeError):
    def __init__(self, message: str, decision_record: dict):
        super().__init__(message)
        self.decision_record = dict(decision_record)


def is_valid_llm_decision(record: dict) -> bool:
    return bool(record.get("provider_request_success")) and bool(record.get("parser_success")) and not bool(record.get("fallback_used"))

def summarize_llm_validity(records: list[dict], *, llm_evaluation: bool) -> dict:
    valid=sum(is_valid_llm_decision(r) for r in records); fallback=sum(bool(r.get("fallback_used")) for r in records)
    failed=sum(not is_valid_llm_decision(r) for r in records) if llm_evaluation else 0
    return {"llm_valid_decisions":valid,"llm_failed_decisions":failed,"fallback_decisions":fallback,"llm_episode_valid":(valid>=1 and failed==0 and fallback==0) if llm_evaluation else None}

def enforce_strict_llm_decision(record: dict, *, strict_llm_mode: bool) -> None:
    if strict_llm_mode and not is_valid_llm_decision(record):
        print("[LLM FAILURE]", flush=True); print("[EPISODE INVALID]", flush=True)
        record = dict(record)
        record["strict_valid"] = False
        record["failure_reason"] = "STRICT_LLM_INVALID_DECISION"
        raise StrictLLMFailure("STRICT_LLM_INVALID_DECISION", record)
