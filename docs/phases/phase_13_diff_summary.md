# Phase 13 Diff Summary

- Bound controllers to per-scenario `SUMO_CONFIG_PATH` so they no longer fall back to the root 4-vehicle config.
- Generated per-scenario SUMO configuration files alongside per-scenario routes.
- Passed the scenario-specific simulation step count through the experiment runner.
- Verified with real baseline 8-vehicle and 16-vehicle runs.

