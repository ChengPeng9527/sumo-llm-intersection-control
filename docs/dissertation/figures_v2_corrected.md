# Corrected Figure Specification v2

Repository: `D:\Sumo\sumo_train`
Branch: `phase-18-decision-pipeline-separation`
HEAD: `b27052bdf2521fdfc710a3b3c7b9710396f59ebe`

This document records the four dissertation figures that should be rendered from the corrected evidence base.

## Figure 1. Mean waiting time by controller and scale

- **Purpose**: show the traffic-efficiency gap between rule-based and LLM-assisted control.
- **Source**: `docs/dissertation/results_v3_corrected.md`, corrected summary data.
- **Y-axis**: waiting time in steps.
- **X-axis**: controller.
- **Grouping**: 4V vs 8V.
- **Caption**: *Mean waiting time by controller and vehicle scale in the corrected dissertation evidence. Error bars should represent one standard deviation across the three seeds in each cell.*

## Figure 2. Mean speed by controller and scale

- **Purpose**: show the motion-efficiency counterpart to waiting time.
- **Source**: `docs/dissertation/results_v3_corrected.md`, corrected summary data.
- **Y-axis**: mean speed in m/s.
- **X-axis**: controller.
- **Grouping**: 4V vs 8V.
- **Caption**: *Mean speed by controller and vehicle scale in the corrected dissertation evidence. Error bars should represent one standard deviation across the three seeds in each cell.*

## Figure 3. Provider success and fallback rate by LLM controller and scale

- **Purpose**: show the reliability bottleneck in the live-provider path.
- **Source**: `docs/dissertation/results_v3_corrected.md`, corrected summary data.
- **Y-axis**: rate.
- **X-axis**: LLM controller.
- **Grouping**: 4V vs 8V.
- **Caption**: *Provider success and fallback rate for live LLM-bearing controllers in the corrected dissertation evidence. The figure should make clear that provider success is low and fallback is dominant.*

## Figure 4. Provider latency by controller and scale

- **Purpose**: show the latency cost of the live provider path.
- **Source**: `docs/dissertation/results_v3_corrected.md`, corrected summary data.
- **Y-axis**: latency in milliseconds.
- **X-axis**: LLM controller.
- **Grouping**: 4V vs 8V.
- **Caption**: *Provider latency by controller and vehicle scale in the corrected dissertation evidence. Error bars should represent one standard deviation across the three seeds in each cell.*

## Notes

- The corrected 8V evidence must be used; the nominal 8V `formal_v2` traces are invalid and should not be plotted.
- Zero collisions and zero safety overrides are important contextual notes, but they do not require standalone figures.
