# UI/UX implementation roadmap

Status: architecture proposal; identifiers intentionally unallocated  
Rule: allocate Feature/Task/DEC IDs only on current `main` under the assigned
Project Lead. `0045` is already consumed by Agent Memory & Ephemeral
Coordination.

## 1. Prerequisite graph

```text
Governance decisions + baseline inventory
  ├─ Identity/route/relation contracts
  ├─ Design system + application shell
  ├─ i18n/RTL/accessibility foundation
  └─ Classified projection/security foundation
       ├─ Directory/build migration (_src→src, generated HTML→www)
       ├─ Documentation universes (Adaptive, Classic, S-Core)
       ├─ Traceability/search
       ├─ Governance/reporting
       ├─ Authenticated control plane + notifications
       │    ├─ Curation/review/feedback with authenticated submission
       │    └─ AI discussion/submission
       └─ Ticket projection (read-only until control plane accepted)
            └─ Ticket authority cutover (separate decision)
                 └─ Coding-context assembly + VM qualification research
```

Parallelism begins only after shared route/entity/component/i18n/projection
products are committed and consumed as explicit prerequisites.

## 2. Proposed Features

### F-A — Canonical identity, routes, and traceability core

Deliverables: typed EntityRef/RelationRef schemas, resolver, route manifest,
alias/tombstone model, reverse-link indexes, current/history precedence,
search grammar, link crawler, provenance traversal, fixtures.  
Risk: repository-wide cross-item links and current-state interpretation.  
Governance: decision record and independent Architect scope review before gate
activation.  
Terminal integrating Task: mandatory review of route uniqueness, historical
stability, link/failure semantics, and representative end-to-end traces.

### F-B — Design system, shell, and accessibility foundation

Deliverables: tokens/themes, typography, icons, shell, record header, typed
status, navigation, tabs, tables, graph alternative, timelines, diffs, states,
print/export, Storybook-like fixture gallery without production dependency.  
Terminal integrating Task: mandatory review across view/state/theme/viewport,
WCAG 2.2 AA, keyboard, screen readers, zoom, forced colors, and print.

### F-C — i18n, RTL, and localization operations

Deliverables: ICU catalog, glossary, locale registry, exact-entity switching,
fallback/provenance, bidi isolation, pseudolocales, coverage dashboard, queue,
segment review, CJK/Devanagari/Arabic font strategy.  
Terminal integrating Task: mandatory eleven-locale and pseudo-locale visual,
functional, accessibility, and link qualification.

### F-D — Classified projection and frontend security

Deliverables: public/internal/restricted projection schemas, classification and
redaction, secret/PII/path scanning, safe DOM/sanitization, CSP/security
headers, SBOM/integrity, privacy-safe telemetry contract.  
Risk: security/privacy boundary.  
Governance: decision record, Security and privacy reviews.  
Terminal integrating Task: mandatory adversarial publication matrix and
security/privacy checkpoint.

### F-E — Directory and deterministic build migration

Acceptance-before-start predecessor **F-E0 Build Baseline Ratification**:
measure the named current corpus on named hardware with a fixed command,
environment, Brotli-11 tooling, five cold and five warm runs; record median/p95
wall and CPU time, peak RSS, public-output bytes/file count, and reproducibility;
propose and independently ratify finite numeric ceilings and regression
headroom. F-E implementation cannot start before F-E0 is accepted.  
Deliverables: `_src`→`src`; generated root HTML/assets→`www`; authored/source/
generated separation; capability-island bundling; incremental/deterministic
build; immutable asset/cache manifests; legacy redirects; atomic rollback.  
No visual/semantic cutover is combined with filesystem movement.  
Terminal integrating Task: mandatory path parity, reproducibility, link crawl,
performance, deployment, and rollback review.

### F-F — Documentation universes and discovery

Deliverables: equal AUTOSAR Adaptive, AUTOSAR Classic, S-Core landing/catalog/
detail templates; sources, requirements, API/type/service/member, diagrams,
version/diff/comparison, global exact-ID-first search, saved views.  
Terminal integrating Task: mandatory representative corpus review for every
universe, entity family, locale, largest/smallest page, and source trace.

### F-G — Traceability and scalable graph experience

Deliverables: relationship/provenance/dependency/coverage/conflict views,
adjacency indexes, progressive graph worker, clustering, accessible tables,
deep-linked viewport, graph performance and cycle/missing/redaction states.  
Terminal integrating Task: mandatory 1,000-node/10,000-record, no-JS, a11y,
bidirectional-trace, and performance review.

### F-H — Unified governance and reporting

Deliverables: work items, claims, decisions, policies, provenance, Acceptance,
checkpoints, integration reviews/verdicts, validations, evidence, audit,
authority matrix; unified report center and all report families.  
Risk: authoritative versus derived-state confusion.  
Governance: explicit derivation precedence and classified publication decision.  
Terminal integrating Task: mandatory prerequisite-closed governance semantics,
stale-baseline, append-only history, print/export, privacy, and report parity
review.

### F-I — Curation, review, and public feedback

Prerequisites: F-D and F-K for every authenticated submission. Until both are
accepted, F-I is static read plus local export-only; the current browser-PAT
flow is removed/disabled before any redesigned page ships.  
Deliverables: queues, source comparison, diff/proposal, discussion, review
requests/protocols/findings/decisions/re-review, receipts, public feedback,
archive; migration away from browser PAT.  
Risk: credentials, authority, personal data, external GitHub effects.  
Terminal integrating Task: mandatory Security/QA/UX review of authentication,
authority, concurrency, failure recovery, accessibility, and privacy.

### F-J — DHTML ticket projection and cutover preparation

Deliverables: backlog/list/detail/DAG/roadmap/query/conflict views; typed adapter
from TODO/claims/issues; parity and dual-read reports; mutation preview.  
Initial mode is read-only projection; authenticated mutation also requires
accepted F-D and F-K.  
Terminal integrating Task: mandatory parity and failure review. The web system
does not become authoritative here.

### F-K — Authenticated control plane and notifications

Deliverables: GitHub App/OAuth or equivalent short-lived sessions; role/
assignment/authority checks; idempotent actions; receipts; email/in-app
notifications; consent, retention, revocation, retry/dead-letter operations.  
Risk: credentials, external side effects, personal data.  
Terminal integrating Task: mandatory Security, QA, and operator review with
adversarial concurrency and delivery recovery.

### F-L — AI discussion and reviewed submission

Prerequisites: F-D and F-K.  
Deliverables: contextual assistant, conversation, context inspector, source
citations, proposed change/diff, finalization, update run, recovery; model and
prompt provenance; no autonomous authority.  
Terminal integrating Task: mandatory hallucination/provenance/privacy/context
boundary and end-to-end submission review.

### F-M — Ticket authority cutover

Prerequisites: F-J, F-K, complete parity, migration rehearsal, rollback, and a
separate Management decision.  
Deliverables: cutover ledger, freeze/dual-write strategy, reconciliation,
monitoring, rollback.  
Terminal integrating Task: mandatory privileged cutover review. No implicit
grandfathering of prior ticket data.

### F-N — AUTOSAR Classic import and eleven-locale content expansion

Deliverables: licensed/authorized source intake, extraction, entity mapping,
coverage, translation/provenance, curation, performance qualification.  
Terminal integrating Task: mandatory source/legal/coverage/i18n/quality review.

### F-O — Coding-context assembly and VM research

Deliverables: research hypotheses, context manifest, retrieval/coverage method,
S-Core mapping, implementation plan synthesis, custom VM threat model and
prototype tests, objective evaluation. This is research, not a promised fully
autonomous production capability.  
Terminal integrating Task: mandatory research evidence and safety review before
any autonomous code execution scope expands.

## 3. Cross-Feature acceptance matrix

### Requirements bindings for proposed Features

The identifiers below refer to
[`ui-ux-requirements-baseline.md`](ui-ux-requirements-baseline.md). `F-*`
labels remain planning proposals: this matrix creates neither Feature
allocation nor implementation, checkpoint, or acceptance authority.

| Proposed Feature | Bound requirements |
|---|---|
| F-A | RQ-UIUX-003, RQ-UIUX-004, RQ-UIUX-005, RQ-UIUX-025, RQ-UIUX-026, RQ-UIUX-031, RQ-UIUX-032 |
| F-B | RQ-UIUX-002, RQ-UIUX-011, RQ-UIUX-012, RQ-UIUX-013, RQ-UIUX-014, RQ-UIUX-015, RQ-UIUX-018, RQ-UIUX-024, RQ-UIUX-026, RQ-UIUX-031, RQ-UIUX-032 |
| F-C | RQ-UIUX-014, RQ-UIUX-032 |
| F-D | RQ-UIUX-020, RQ-UIUX-021, RQ-UIUX-022, RQ-UIUX-023, RQ-UIUX-025, RQ-UIUX-032 |
| F-E0 | RQ-UIUX-019 |
| F-E | RQ-UIUX-016, RQ-UIUX-019, RQ-UIUX-025, RQ-UIUX-026, RQ-UIUX-029, RQ-UIUX-032 |
| F-F | RQ-UIUX-001, RQ-UIUX-002, RQ-UIUX-012, RQ-UIUX-016, RQ-UIUX-032 |
| F-G | RQ-UIUX-004, RQ-UIUX-012, RQ-UIUX-017, RQ-UIUX-018, RQ-UIUX-032 |
| F-H | RQ-UIUX-004, RQ-UIUX-005, RQ-UIUX-011, RQ-UIUX-015, RQ-UIUX-018, RQ-UIUX-021, RQ-UIUX-024, RQ-UIUX-032 |
| F-I | RQ-UIUX-002, RQ-UIUX-006, RQ-UIUX-007, RQ-UIUX-012, RQ-UIUX-020, RQ-UIUX-032 |
| F-J | RQ-UIUX-002, RQ-UIUX-008, RQ-UIUX-012, RQ-UIUX-018, RQ-UIUX-028, RQ-UIUX-032 |
| F-K | RQ-UIUX-007, RQ-UIUX-020, RQ-UIUX-023, RQ-UIUX-027 |
| F-L | RQ-UIUX-002, RQ-UIUX-009, RQ-UIUX-020, RQ-UIUX-032 |
| F-M | RQ-UIUX-008, RQ-UIUX-028 |
| F-N | RQ-UIUX-001, RQ-UIUX-014, RQ-UIUX-030, RQ-UIUX-032 |
| F-O | RQ-UIUX-010, RQ-UIUX-032 |

Every Feature contract maps requirements to: source inputs, architecture
decision, prerequisites and planned order, capability/rights/data/tool profile,
test scope/kind, runtime/CPU range, cognitive demand, uncertainty, risk,
recovery, exact branch target, and checkpoint rationale.

Common gates:

- route/link/fragment/hreflang/tombstone crawler;
- exact provenance path in both directions;
- 11 locales plus expanded/RTL pseudo-locales;
- WCAG 2.2 AA automated and manual journeys;
- 320/768/1440/1920 visual regression, themes, zoom, print;
- no-JS, loading/empty/partial/stale/error/offline/permission/redaction states;
- performance budgets and low-end device/network tests;
- classification, secret/PII/path, CSP/XSS, dependency, and authority tests;
- schema compatibility, deterministic output, migration, atomic rollback;
- idempotency, stale target, interrupted submit, unauthorized/unassigned actor;
- current/historical/derived state and append-only invalidation semantics.

F-E0 is a benchmark/ratification work product, not a moving baseline. Its
accepted numbers become immutable contract inputs; changing them requires an
additive decision and impact review before further comparison.

## 4. Recovery strategy

Each release is an immutable manifest of routes, assets, schemas, projections,
and source refs. Publication atomically swaps the manifest. The prior manifest
and compatible data remain available for immediate rollback. Migrations use
dual-read and comparison before cutover. Sensitive/control-plane Features can
be disabled without removing the static read plane. Legacy routes remain until
measured traffic and complete link parity justify separately reviewed removal.

## 5. Advisory sizing

Ranges assume established shared contracts and one focused implementer per
work unit; they are architecture guidance, not schedule promises.

| Feature class | Tokens/test design | Runtime/CPU | Cognitive demand | Uncertainty | Material risk |
|---|---:|---:|---|---|---|
| Shared contract (A–D) | 40k–120k | medium | very high | 25–45% | high |
| Build/migration (E) | 50k–140k | high | high | 25–40% | high |
| Read experiences (F–H) | 50k–160k each | medium–high | high | 20–40% | medium–high |
| Interactive/control (I–M) | 70k–200k each | high | very high | 30–55% | very high |
| Content scale (N) | 80k–250k | very high | high | 35–60% | high |
| Research (O) | bounded experiments | very high | frontier | 50–75% | very high |

No Task should inherit these ranges wholesale. The assigned Architect splits
each Feature into bounded Tasks and exactly one terminal integrating Task.
