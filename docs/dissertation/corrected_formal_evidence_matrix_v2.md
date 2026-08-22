# Corrected Formal Evidence Matrix v2

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

Final evidence provenance:

- 4V source: `results/formal_experiment/dissertation_formal_v2/`
- 8V source: `results/formal_experiment/dissertation_formal_v4/`
- Excluded: `formal_v2` nominal 8V, `formal_v3`

## Evidence matrix

| Claim | Evidence source | Exact metric/data | Confidence | Suitable section | Limitation / caveat |
|---|---|---|---|---|---|
| The canonical live request configuration is Groq / `openai/gpt-oss-20b` / 256 tokens / low reasoning / 30 s timeout / 0 retries. | `src/llm/request_config.py`, `results/formal_experiment/dissertation_formal_v4/run_manifest.json` | `provider = Groq`, `base_url = https://api.groq.com/openai/v1`, `model = openai/gpt-oss-20b`, `max_completion_tokens = 256`, `reasoning_effort = low`, `timeout = 30.0`, `max_retries = 0` | High | Methodology / System Design | Frozen request budget, not a performance claim. |
| `formal_v2` 4V is valid evidence. | `results/formal_experiment/dissertation_formal_v2/runs/` | 12 runs, all with 4 observed / departed / arrived vehicles and zero collisions | High | Results | Usable 4-vehicle evidence only. |
| `formal_v2` nominal 8V runs are invalid. | `results/formal_experiment/dissertation_formal_v2/runs/` | configured 8 vehicles, but raw traces only show 4 observed / departed / arrived vehicles | High | Limitations / Results boundary | Must not be reported as 8-vehicle evidence. |
| `formal_v3` is intermediate evidence only. | `results/formal_experiment/dissertation_formal_v3/runs/` | corrected 8V loading, but two rule-based runs did not complete all 8 arrivals within the 400-step window | High | Limitations / Execution history | Exclude from final results because it is not the final valid 8V batch. |
| `formal_v4` is the corrected 8V evidence set. | `results/formal_experiment/dissertation_formal_v4/runs/` | 12/12 runs observed 8 vehicles, departed 8, arrived 8, collision count 0 | High | Results | This is the final 8V source. |
| Rule-based control is slower than the LLM-assisted architectures in the tested scenarios. | `results/formal_experiment/dissertation_formal_v2/`, `results/formal_experiment/dissertation_formal_v4/` | formal v2 4V rule-based mean waiting `82` steps vs LLM-assisted `15` steps; formal v4 8V rule-based mean waiting `242.042` steps vs LLM-assisted `15.292` steps | High | Results / Discussion | Traffic advantage belongs to the pipeline under tested conditions, not to a pure model-only controller. |
| LLM-assisted controllers maintain low waiting time in both 4V and 8V corrected evidence. | `results/formal_experiment/dissertation_formal_v2/`, `results/formal_experiment/dissertation_formal_v4/` | formal v2 4V mean waiting `15`; formal v4 8V mean waiting `15.292` | High | Results | Descriptive only; not a causal proof of model superiority. |
| Raw LLM, hybrid, and hybrid+safety have very low provider success rates in the corrected formal evidence. | `results/formal_experiment/dissertation_formal_v2/`, `results/formal_experiment/dissertation_formal_v4/` | formal v4 overall provider attempts `2784`, successes `4`, failures `2780` | High | Results / Discussion | Most live attempts fall back; must not be written as pure LLM performance. |
| Provider reliability is the main validity threat for formal LLM-bearing results. | formal v2 and formal v4 raw traces | provider attempts greatly exceed successes; finish reasons are mostly unavailable, exceptions mostly `RateLimitError` | High | Discussion / Limitations | The traffic metrics are pipeline outcomes under heavy fallback, not idealized LLM-only behavior. |
| Cooperative post-processing was implemented but has no visible effect in the valid formal evidence. | `results/formal_experiment/dissertation_formal_v2/` and `results/formal_experiment/dissertation_formal_v4/` raw traces | formal v2 valid 4V recorded 0 interventions; formal v4 corrected 8V recorded 0 interventions | High | Results / Discussion / Limitations | Any historical intervention occurred only in the invalid nominal `formal_v2` 8V traces and must not be used in the final dissertation evidence. |
| Safety overrides were not observed in the formal evidence. | formal v2 / formal v4 raw traces | `safety_override_count = 0` throughout | Medium | Results / Limitations | Zero observed overrides do not prove the verifier is unnecessary. |
| The corrected 8V evidence shows the system can complete all planned vehicles without collisions under the tested low-density scenarios. | `results/formal_experiment/dissertation_formal_v4/` | 12/12 runs, 8/8 observed/departed/arrived, collision count 0 | High | Results | Limited to the tested topology and traffic density. |
