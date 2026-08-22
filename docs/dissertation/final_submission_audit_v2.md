# Final Submission Audit v2

Repository: `D:\Sumo\sumo_train`

## Blocking issue

- The only confirmed blocker was the Figure 3/Table 3 denominator mismatch. It is resolved in `full_draft_submission_v5.md` and the new Figure 3 asset.

## Figure checks

- Figure 1: PASS
- Figure 2: PASS
- Figure 3: PASS
- Figure 4: PASS

## Numerical consistency

- 8V live-provider attempts: 2784
- 8V live-provider successes: 4
- 8V live-provider failures: 2780
- `fallback_used == fallback_triggered` in the live-provider rows that were checked: yes

## Output files

- `docs/dissertation/full_draft_submission_v5.md`
- `docs/dissertation/full_draft_submission_v5.docx`
- `docs/dissertation/figure_3_denominator_audit_v1.md`
- `docs/dissertation/final_submission_audit_v2.md`
- `docs/dissertation/figures/final/figure_3_provider_success_fallback_v2.png`

## Verdict

- READY_FOR_FINAL_FORMATTING
