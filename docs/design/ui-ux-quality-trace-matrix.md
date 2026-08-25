# Quality and release-gate trace matrix

Status: normative design-to-implementation handoff  
Evidence paths are proposed stable families; each future Task pins exact files,
commands, profiles, baselines, and digests in its own contract.

| Gate | Owning Feature(s) | Fixture/profile | Required test | Evidence artifact | Terminal checkpoint |
|---|---|---|---|---|---|
| Q-01 Canonical identity/routes | F-A | every EntityKind; duplicate ID/release; same SHA in four roles; hostile opaque ID | registry uniqueness, typed chooser, encoding/traversal, alias/redirect | `evidence/routes/registry.json`, crawler report | F-A integration |
| Q-02 Links/fragments/hreflang | F-A,F-C | all routes × 11 locales; missing target/fragment | crawl canonical/internal/reverse links, fragments, alternates, fallback, tombstone | `evidence/routes/link-crawl.json` | F-A and F-C integration |
| Q-03 Provenance both directions | F-A,F-G,F-H | requirement→Task→commit→run→finding→review→Acceptance/integration; asserted/inferred/conflicting/rejected | traverse exact refs/digests forward/reverse, edge semantics and validity | `evidence/trace/golden-paths.json` | F-G and F-H integration |
| Q-04 Current-state truth tables | F-A,F-H | Task `[x]` not accepted; stale review; rejected integration; Decision proposal/effective/superseded | per-dimension derivation, conflict→unverifiable, no cross-dimension inference | `evidence/state/truth-tables.json` | F-H integration |
| Q-05 Classified deployment | F-D,F-H | public/internal/restricted plus secret, name, path, unknown class, hidden route/hash/count | build failure and actual public-artifact negative scan; authorization/cache partition tests | `evidence/security/projection-scan.json` | F-D Security checkpoint |
| Q-06 Browser credential absence | F-D,F-K,F-I | authenticated and static/export flows | prove no PAT/provider token in storage/DOM/URL/log/export/cache; BFF cookie/rotation/expiry/revoke | `evidence/security/session-e2e.json` | F-K Security checkpoint |
| Q-07 CSRF/authz/concurrency | F-K | CSRF, fixation, stale digest, duplicate idempotency, interrupted submit, unauthorized/unassigned actor | Origin/Referer+token, rotation, reauth, 409, one effect, receipt reconciliation, server authz | `evidence/control-plane/adversarial.json` | F-K Security/QA checkpoint |
| Q-08 CSP/XSS/dependencies | F-D | injected HTML/script/URL, all route families, dependency graph | CSP report-only then enforcing, sanitizer/DOM tests, headers, SBOM/license/vulnerability | `evidence/security/browser-policy.json`, SBOM | F-D Security checkpoint |
| Q-09 No-JS/read plane | F-B,F-F–J | representative view and all data states | essential content/links/forms/export readable; graphs/tables fall back; no false mutation | `evidence/no-js/route-matrix.json` | each consuming Feature integration |
| Q-10 Accessibility | F-B and consumers | 320/768/1440; 200% text; 400% zoom; forced colors; reduced motion | HTML/axe/contrast plus keyboard, NVDA/Firefox, VoiceOver/Safari, focus/modal/live error/graph table | `evidence/a11y/{feature}/` | F-B and each UI integration |
| Q-11 Locale/i18n/RTL | F-C and consumers | 11 locales, +60% pseudo, pseudo-RTL, hostile Arabic+SHA/path/SWS | keys/variables/plurals, same-entity switch, fallback provenance, bidi copy/paste, visual regression | `evidence/i18n/{feature}/` | F-C and each UI integration |
| Q-12 Visual system/state | F-B and consumers | every component state/theme/density/viewport, longest strings | visual regression, typed statuses, no color-only meaning, readable default and compact | `evidence/visual/{feature}/` | F-B and each UI integration |
| Q-13 Base performance | F-E,F-F | smallest/median/largest docs and reports; named mobile throttle | Brotli bytes, requests-to-readable, LCP/INP/CLS, JS heap/long tasks | `evidence/performance/base.json` | F-E/F-F integration |
| Q-14 Graph scale | F-G | 500 rendered; 1,000 raw aggregation; cycles/missing/redacted; repeated navigation | payload/worker/first useful/interaction budgets, accessible table, cancel/terminate/no leak | `evidence/performance/graphs.json` | F-G integration |
| Q-15 Large data | F-B,F-G,F-H,F-J | 10,000 tickets/evidence rows | server/build pagination, semantic headers/positions, keyboard/focus/back, exact export, optional virtualization | `evidence/performance/tables.json`, a11y log | consuming integration |
| Q-16 Deterministic build | F-E0→F-E | fixed current corpus, named hardware/environment/command/Brotli-11, ≥5 cold + ≥5 warm runs, one-record edit | F-E0 records median/p95 wall+CPU, peak RSS, bytes/file count and independently ratifies finite ceilings before F-E starts; F-E asserts byte identity, incremental p95, ceilings, ≤10% regression | `evidence/build/baseline-ratification.json`, benchmark, manifests | F-E0 Acceptance-before-start; F-E integration |
| Q-17 Cache/offline/rollback | F-E,F-K | public immutable, HTML revalidate, private/restricted, interrupted release | cache headers/partition, no sensitive cache, offline draft only, atomic manifest rollback | `evidence/release/recovery.json` | F-E and F-K integration |
| Q-18 Schema compatibility | F-A,F-D | current, previous supported, additive future, unsupported major, malformed | deterministic pure migration, visible degraded state, rollback restores prior manifest | `evidence/schema/compatibility.json` | F-A/F-D integration |
| Q-19 Privacy/telemetry | F-D,F-K | rationale, actor, evidence, token, full URL/query, restricted entities | assert absence from analytics/console/errors/cache; consent/DNT/retention/deletion | `evidence/privacy/telemetry.json` | F-D privacy checkpoint |
| Q-20 Print/export/raw integrity | F-B,F-H | decision, review, evidence bundle, report, Arabic/long ID | ID/ref/digest/as-of/classification/signature/page numbers; readable links; raw digest exact | `evidence/export/{feature}/` | F-B/F-H integration |
| Q-21 Review/curation safety | F-I | online/offline, stale target, permission, partial transport, re-review | local-ready ≠ submitted; export-only offline; exact package; receipts; focus/errors; no authority inference | `evidence/review/e2e.json` | F-I integration |
| Q-22 Ticket parity/cutover | F-J,F-M | TODO/claims/issues conflicts, expired/takeover/cycle/cross-feature | projection parity, accessible DAG, dual-read reconciliation, cutover/rollback ledger | `evidence/tickets/parity.json` | F-J then F-M integration |
| Q-23 AI context/proposal | F-L,F-O | missing/conflicting/restricted evidence, prompt injection, oversized context | visible exact context, source citations, redaction, proposal-only authority, evaluation and VM isolation | `evidence/ai/context-eval.json` | F-L/F-O integration |
| Q-24 Notification delivery | F-K | duplicate, delayed, bounce, retry/dead-letter, consent revoked | idempotent routing, no secret/content leakage, status/recovery, retention/deletion | `evidence/notifications/delivery.json` | F-K integration |

## Completion rule

### Requirements bindings

These bindings point to the preparation IDs in
[`ui-ux-requirements-baseline.md`](ui-ux-requirements-baseline.md). They add
requirements traceability without allocating work or changing any gate.

| Gate | Bound requirements |
|---|---|
| Q-01 | RQ-UIUX-003, RQ-UIUX-025, RQ-UIUX-032 |
| Q-02 | RQ-UIUX-002, RQ-UIUX-003, RQ-UIUX-014, RQ-UIUX-025, RQ-UIUX-029, RQ-UIUX-032 |
| Q-03 | RQ-UIUX-004, RQ-UIUX-011, RQ-UIUX-030, RQ-UIUX-032 |
| Q-04 | RQ-UIUX-005, RQ-UIUX-011, RQ-UIUX-031, RQ-UIUX-032 |
| Q-05 | RQ-UIUX-021, RQ-UIUX-032 |
| Q-06 | RQ-UIUX-007, RQ-UIUX-020 |
| Q-07 | RQ-UIUX-006, RQ-UIUX-007, RQ-UIUX-020 |
| Q-08 | RQ-UIUX-021, RQ-UIUX-022 |
| Q-09 | RQ-UIUX-001, RQ-UIUX-002, RQ-UIUX-012, RQ-UIUX-031, RQ-UIUX-032 |
| Q-10 | RQ-UIUX-002, RQ-UIUX-013, RQ-UIUX-015, RQ-UIUX-032 |
| Q-11 | RQ-UIUX-001, RQ-UIUX-013, RQ-UIUX-014, RQ-UIUX-031, RQ-UIUX-032 |
| Q-12 | RQ-UIUX-015, RQ-UIUX-026, RQ-UIUX-031, RQ-UIUX-032 |
| Q-13 | RQ-UIUX-016, RQ-UIUX-032 |
| Q-14 | RQ-UIUX-017, RQ-UIUX-032 |
| Q-15 | RQ-UIUX-008, RQ-UIUX-018, RQ-UIUX-032 |
| Q-16 | RQ-UIUX-019, RQ-UIUX-026, RQ-UIUX-029 |
| Q-17 | RQ-UIUX-019, RQ-UIUX-025, RQ-UIUX-029 |
| Q-18 | RQ-UIUX-025, RQ-UIUX-026, RQ-UIUX-030 |
| Q-19 | RQ-UIUX-006, RQ-UIUX-009, RQ-UIUX-021, RQ-UIUX-023 |
| Q-20 | RQ-UIUX-011, RQ-UIUX-015, RQ-UIUX-024 |
| Q-21 | RQ-UIUX-006, RQ-UIUX-007, RQ-UIUX-020 |
| Q-22 | RQ-UIUX-008, RQ-UIUX-028 |
| Q-23 | RQ-UIUX-009, RQ-UIUX-010 |
| Q-24 | RQ-UIUX-007, RQ-UIUX-023, RQ-UIUX-027 |

An implementation Task may narrow this matrix only when its declared surface is
provably unaffected. It may not replace a named test with “manual inspection”
without identifying the manual procedure, competence, exact candidate,
environment, evidence, and repeatability. Every terminal integrating Task
expands prerequisite-closed evidence and records each applicable `Q-*` result.
