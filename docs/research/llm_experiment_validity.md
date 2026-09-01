# LLM Experiment Validity

`VALID_LLM_DECISION` requires provider success, parser success, and no fallback. System completion is distinct from LLM effectiveness validity. An LLM-evaluation episode is valid only with at least one valid decision and zero failed/fallback decisions; invalid episodes remain recorded and are excluded from effectiveness aggregates. Robustness fallback runs remain permitted but are not LLM effectiveness evidence.

`STRICT_LLM_MODE` defaults to `false`. When enabled for a new LLM evaluation, the first invalid decision emits `[LLM FAILURE]` and `[EPISODE INVALID]` and raises `StrictLLMFailure`; cleanup may run but cannot make the episode valid.
