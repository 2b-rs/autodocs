# Independent review — UI/UX requirements baseline

- **Review item:** `ui-ux-requirements-baseline-review-20260824`
- **Reviewer:** `agent:troy:ui-ux-requirements-baseline-review-20260824:20260824T082352Z` (QA-Manager, Team Enterprise)
- **Candidate:** `5109048a1a8bc00d1b1f4e1d5af9bbd7045274ac`
- **Candidate lineage inspected:** substantive `a2c47d306a6261862db44c97b24463d955be3889`; whitespace correction `376bc83703d1445874544d35b5a395eba51a8601`
- **Verdict:** `needs-correction`
- **Authority boundary:** This is independent review evidence only. It neither accepts the baseline nor allocates, integrates, or authorizes implementation.

## Scope and method

I inspected the candidate baseline, its claim, the UI/UX design dossier, view inventory, route matrix, quality trace matrix, implementation roadmap, and candidate diff. The review recomputed identifiers and set equality rather than relying on the implementation claim.

## Findings

### F-UIUX-RQ-REVIEW-001 — product-decision inventory is incomplete and substitutes a different choice

- **Observation:** The baseline declares `D-01` through `D-05` to be the *only* unresolved product choices ([baseline:24-32, 77-79](ui-ux-requirements-baseline.md#2-classification-and-decision-handles)). The source dossier explicitly identifies three Management choices: Personality, **Visibility** (the public/internal/restricted projection and default-deny choice), and Density ([dossier:292-306](ui-ux-design-dossier.md#13-management-interview-decisions)). The baseline covers Personality as `D-02` and Density as `D-01`, but its `D-03` is an initial public-feedback identity policy, which is a different choice. `RQ-UIUX-021` instead says the classification policy remains external authority ([baseline:60](ui-ux-requirements-baseline.md#3-atomic-requirements)).
- **Inference:** The candidate cannot truthfully claim that its D-handle list is complete: the explicit Visibility choice has neither an equivalent D-handle nor an identified disposition. This weakens the required Management-interview/escalation trace and could let a classified-projection contract proceed without the named product decision.
- **Severity:** `major`.
- **Owner:** Requirements Engineer / Project Lead; Management resolves the choice.
- **Required next step:** Add a distinct unresolved decision handle for the dossier's Visibility/classified-projection choice (or demonstrate a one-to-one equivalent), trace it to `RQ-UIUX-021`, F-D/F-H, and Q-05/Q-08/Q-19 as applicable, and then re-evaluate whether the resulting D-handle inventory is complete. Do not silently replace the feedback-identity question or make a Management decision in the correction.

## Verified observations

- **Source wording/provenance:** The candidate preserves a verbatim German user-request quotation and identifies its input as `ui-ux-design-dossier-20260824@1d749458859726323d5c2fb9bae32766a0da9b12`; the tracked candidate claim links the preparer to the direct Project Lead assignment. This review found no textual mismatch between the baseline's stated scope and the dossier's described product outcomes. The original authenticated user transcript is not in the candidate tree, so this review does not independently authenticate that external source.
- **Requirement IDs:** 32 requirement rows, uniquely and contiguously numbered `RQ-UIUX-001` through `RQ-UIUX-032`.
- **View coverage:** inventory and route matrix each contain 119 unique IDs and their sorted ID sets are identical.
- **Bidirectional trace coverage:** the set of baseline RQ IDs equals the distinct RQ-ID sets in both the roadmap Feature bindings and quality-gate bindings (32 each). The quality matrix contains Q-01 through Q-24; the roadmap contains F-A through F-O plus F-E0.
- **Testability and boundaries:** each RQ supplies a SHALL statement, acceptance intent, and stated assumptions/exclusions. The candidate keeps proposed F labels, D handles, and requirement preparation IDs non-authoritative; no Acceptance/integration/implementation authority is asserted.
- **Diff hygiene:** `git diff --check 1d749458859726323d5c2fb9bae32766a0da9b12 5109048a1a8bc00d1b1f4e1d5af9bbd7045274ac` exited zero. The candidate changes only the preparer claim, baseline, quality bindings, and roadmap bindings.

## Reproducible commands

```sh
git diff --check 1d749458859726323d5c2fb9bae32766a0da9b12 5109048a1a8bc00d1b1f4e1d5af9bbd7045274ac
rg '^\\| (SYS|KN|TR|CU|RV|GW|RP|TK|AI|AD)-[0-9]{2} \\|' docs/design/ui-ux-view-inventory.md
rg '^\\| (SYS|KN|TR|CU|RV|GW|RP|TK|AI|AD)-[0-9]{2} \\|' docs/design/ui-ux-view-route-matrix.md
rg '^\\| RQ-UIUX-[0-9]{3} \\|' docs/design/ui-ux-requirements-baseline.md
rg -o 'RQ-UIUX-[0-9]{3}' docs/design/ui-ux-implementation-roadmap.md
rg -o 'RQ-UIUX-[0-9]{3}' docs/design/ui-ux-quality-trace-matrix.md
```

The exact set/count comparison and contiguous-sequence check were executed in the review worktree; all mechanical checks passed. The verdict remains `needs-correction` solely because of F-UIUX-RQ-REVIEW-001.

## Re-review R2 — corrected candidate `ae11b1f8b`

- **Re-reviewed candidate:** `ae11b1f8beacaaf4a84998ed6f99b2d5cf3533fd`
- **Previous candidate:** `5109048a1a8bc00d1b1f4e1d5af9bbd7045274ac`
- **Verdict:** `review-ready`
- **Finding disposition:** `F-UIUX-RQ-REVIEW-001` is `closed`.

### Independent correction inspection

- The candidate adds `D-06 Visibility and classified governance publication` using the dossier's public/internal/restricted, default-deny recommendation and preserves explicit risk acceptance for a full-public alternative. It does not decide the choice.
- `D-03` remains the distinct feedback-identity question.
- `RQ-UIUX-021` now explicitly names unresolved D-06 and retains F-D/F-H plus Q-05/Q-08/Q-19 trace.
- The handoff now describes six identified unresolved choices and correctly distinguishes the dossier's Personality, Visibility, and Density interview choices from feedback identity, ticket cutover, and telemetry policy.

### R2 recomputation

- Six unique contiguous D handles (`D-01` through `D-06`).
- 32 unique contiguous RQ rows; exact RQ-set equality with the roadmap and quality reverse bindings.
- 119 unique inventory IDs and 119 unique route-matrix IDs with exact set equality.
- `git diff --check 1d749458859726323d5c2fb9bae32766a0da9b12 ae11b1f8beacaaf4a84998ed6f99b2d5cf3533fd` exited zero.
- The correction delta from `5109048a1` changes only the Requirements Engineer's claim and the requirements baseline.

No open review finding remains. `review-ready` means this preparation baseline is ready for the Project Lead's next bounded process step; it is not Acceptance, an architecture decision, an implementation authorization, or an integration verdict.
