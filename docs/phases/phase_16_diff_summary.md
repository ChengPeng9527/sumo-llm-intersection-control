# Phase 16 Diff Summary

- Rewrote the structured prompt to be throughput-biased while still preserving safety rules.
- Added policy hints so the LLM can see the current priority route and compatible routes.
- Promoted compatible inside-zone WAIT decisions to PROCEED before safety verification.
- Verified the effect with 8-vehicle and 16-vehicle real Groq runs.

