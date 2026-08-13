# Repository Recovery Plan

## Scope

This plan records the recovery boundary between:

- canonical repository: `D:\Sumo\sumo_train`
- recovery source: `D:\Sumo1\sumo_train`

The canonical repository is the only location where formal changes may be made.
The recovery source is read-only evidence for reconstruction and comparison.

## Current Canonical State

- Branch: `phase-18-decision-pipeline-separation`
- Canonical HEAD: `3bd76ac0f252cfdf897eadde40dda6b2bd9532e4`
- Research design freeze commit present: yes
- Phase 18 decision pipeline separation is already frozen in canonical history.
- Parser compatibility patch has been live revalidated.
- Canonical four-controller pilot has been revalidated successfully.

## Evidence Summary

The canonical repository already contains:

- separated decision pipeline stages
- raw, hybrid, and hybrid+safety controller paths
- structured logging and trace fields
- phase documentation for live revalidation and pilot readiness
- pilot runner entry point

The recovery source contains a later working-tree reconstruction that is useful for
cross-checking pilot execution and documentation, but it is not a valid canonical
history source.

## Recovery Findings

### Non-behavioral fixes already observed

- `scripts/run_dissertation_pilot.py` has a path/bootstrap fix to make `src` imports resolvable from the script entry point.
- Current canonical working tree also includes parser diagnostic and pilot evidence notes under `docs/research/`.

### Behavioral differences to avoid migrating

The recovery source includes a simplified controller layout and a minimal local
pipeline implementation that does not match the canonical research architecture.
These differences must not be copied into canonical code because they would alter
the dissertation method rather than only repair execution.

## Allowed Canonical Actions

Only the following categories are allowed in canonical:

1. import/path/bootstrap corrections
2. headless SUMO launch and lifecycle cleanup
3. TraCI shutdown and residual process handling
4. logging, trace, and artifact-writing robustness
5. pilot runner orchestration
6. pilot reporting and documentation

## Disallowed Actions

Do not:

- rewrite the decision strategy
- change prompt construction
- alter safety rules
- alter cooperative post-processing logic
- fabricate git history
- overwrite canonical with the recovery source
- run formal dissertation experiments automatically

## Recovery Steps

1. Keep canonical method files unchanged unless a strictly non-behavioral fix is required for execution.
2. Keep the pilot runner aligned with canonical module paths and artifact schemas.
3. Preserve the recovery source as a comparison archive only.
4. Run canonical unit tests before any live pilot revalidation.
5. Revalidate the pilot only after environment prerequisites are present.

## Verification Targets

Before any formal experiment starts, confirm:

- canonical repository state is clean enough for traceable evidence
- `pytest` passes in canonical
- pilot runner can execute without import or cleanup failures
- live LLM path remains traceable and documented separately from historical evidence

## Decision Rule

If the canonical repository and the recovery source differ in method semantics,
the canonical method takes precedence and the recovery source is not migrated.

If the only differences are import/bootstrap/lifecycle/logging details, those
may be repaired in canonical without changing research behavior.
