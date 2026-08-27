# UI/UX critique and revision log

## Quality protocol

Three independent read-only critics examined the baseline and roadmap. None
could edit, accept, integrate, allocate identifiers, or cross a checkpoint.
Completion threshold: zero unresolved P0/P1 findings; every P2 finding is
implemented in the design or explicitly dispositioned.

## Round 1 — information architecture and traceability

### Findings incorporated

- canonical locale-neutral typed identity and route grammar;
- separate current, historical, derived, stale, invalidated, and redacted state;
- bidirectional `Why?` provenance with evidence/rule/version/review semantics;
- complete view/state inventory across knowledge, governance, reporting,
  curation, review, work, administration, and AI;
- typed alias, redirect, fragment, tombstone, restricted, and dangling behavior;
- exact-ID-first search and permission-safe result counts;
- locale-preserving deep links, explicit fallback, Arabic bidi isolation;
- progressive graphs with synchronized accessible tables;
- route/reverse-link/fragment/hreflang/provenance acceptance gates.

Disposition: all P0/P1 findings incorporated into the view inventory and
route/link contract. Design-system and roadmap requirements cover the remaining
medium findings. No open material finding.

## Round 1 — UX, visual design, accessibility, and i18n

### Findings incorporated

- persistent identity header distinguishing authority from projection;
- separate status dimensions rather than one badge;
- authority-safe irreversible actions and permission explanations;
- WCAG 2.2 AA plus manual keyboard/NVDA/VoiceOver/zoom/forced-color gates;
- RTL treated as data integrity for identifiers, hashes, paths, diffs, and time;
- responsive dense-data patterns with no silently dropped fields;
- one shell/record anatomy and removal of report-local design systems;
- complete light/dark/forced-colors/print themes;
- eleven-locale ICU/fallback/pseudolocale contract;
- first-class loading/empty/partial/stale/error/offline/permission states;
- graph/diff/code/print/export accessibility and provenance;
- calm technical editorial direction with optional compact expert mode.

Disposition: all P0/P1 findings incorporated. P2 visual direction and layout
incorporated; Management interview remains for personality and default density,
but either option uses the same compliant system. No open material finding.

## Round 1 — performance, security, privacy, and changeability

### Findings incorporated

- browser PAT flow declared a release-blocking migration; short-lived secure
  server session required;
- deny-by-default classified governance/evidence projection;
- static no-JS read plane and route-specific capability islands;
- graph size caps, adjacency indexes, workers, progressive disclosure;
- CSP, safe DOM/sanitizer, security headers, dependency/SBOM gates;
- immutable read projection versus live authenticated workflow distinction;
- one ICU catalog and schema/version contract;
- authored `src/` versus disposable `www/` layout;
- explicit offline/degraded behavior and no silent queued approval;
- privacy-minimal observability;
- measurable base, island, graph, interaction, build, and cache budgets;
- security/publication/concurrency/schema/rollback acceptance tests.

Disposition: all P0/P1 findings incorporated in the dossier, route contract,
visual system, and roadmap. P2 recommendations incorporated. Service-worker
support is intentionally deferred until sensitive-route exclusion, purge,
versioning, and rollback have a separately accepted contract. No open material
finding.

## Round 2 — contract and visual retest

The critics rejected the first closure statement. Material findings were
reopened and corrected:

- added a 100% inventory-ID route/source/permission/no-JS matrix;
- replaced universal state precedence with per-entity/per-dimension derivation
  and conflict-to-unverifiable semantics;
- added typed URNs, collision/path handling, typed historical versions,
  canonical query and privacy-safe serialization;
- defined three policy-selected restriction outcomes and consistent leakage;
- split public/internal/restricted deployments and added artifact scans;
- restricted provider credentials to a BFF and added CSRF, PKCE, rotation,
  expiry, reauthentication, rate limiting, revocation, and server authorization;
- made F-D/F-K prerequisites for authenticated review/AI/ticket flows and
  required removal of the browser PAT before redesigned release;
- made performance measurements reproducible and added absolute output/build/
  heap/worker gates; mandatory accepted predecessor F-E0 freezes finite numeric
  ceilings before F-E starts instead of inventing unmeasured values;
- replaced accessibility-risky virtualization wording with semantic pagination;
- added a gate trace matrix binding controls to Feature, fixture, test,
  evidence, and terminal checkpoint;
- regenerated the Governance visual with decision-specific state and invariant
  six-domain shell;
- regenerated the mobile/RTL visual with the same EntityRef, translation
  provenance, separated state dimensions, and disabled offline submission;
- annotated the Explore visual's remaining compact exemplar limitations.

The v1 Governance and mobile files are retained only as review provenance and
explicitly rejected as implementation references.

## Round 3 checklist for visual artifacts

Generated mockups are accepted as non-normative references only if they visibly
demonstrate:

- the six-domain shell and exact-ID search;
- canonical identity, source/as-of/freshness, and separate status dimensions;
- evidence/relations/history navigation;
- calm editorial hierarchy with compact dense-data capability;
- governance/reporting coherence without decorative ambiguity;
- RTL and long-string resilience in at least one visual specimen;
- readable graph/table relationship alternatives;
- no impossible authority or misleading “Done” state.

Any generated text error is treated as a mockup limitation; normative labels,
routes, tokens, and semantics remain the written contract.

## Residual Management choices

Not critic defects, but product decisions:

1. calm editorial versus more futuristic visual personality;
2. recommended public/internal/restricted projection versus an explicitly
   risk-accepted public-governance alternative;
3. comfortable versus compact default density.

The architecture does not pause: recommended defaults are used until the user
answers, and the final revision records the decision additively.

## Final independent dispositions

- IA/Traceability critic: `scope-ok` after mechanical confirmation of 119
  unique inventory IDs and 119 exact matrix mappings, state derivation,
  restriction/identity/version semantics, and v2 visual corrections.
- UX/i18n/Accessibility critic: `scope-ok` after v2 visual retest and correction
  of durable generation prompts; no residual P0/P1.
- Performance/Security/Changeability critic: `scope-ok` after F-E0 became a
  mandatory accepted numeric-budget ratification predecessor and all compressed
  budgets were normalized to Brotli-11.

These are architecture-scope reviews, not Task Acceptance, implementation
validation, integration verdicts, or release authority.
