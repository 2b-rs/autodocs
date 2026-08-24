# Autodocs unified UI/UX design dossier

Status: revision 1, critic corrections incorporated  
Architect: Data, Team Enterprise  
Authority: direct current-user order, 2026-08-24  
Baseline: `main@5fe90e8acb68e7a2796eb1fc28d0005a2c9d48d8`

## Executive decision

Autodocs becomes one evidence-centered knowledge and delivery environment,
not a collection of generated documents and unrelated dashboards. AUTOSAR
Adaptive, AUTOSAR Classic, and S-Core share one exploration model. Curation,
review, work, governance, provenance, validation, reporting, and AI discussion
share the same stable identities, routes, visual system, and traceability graph.

The recommended experience is a calm technical editorial system: warm neutral
surfaces, precise teal navigation, high-information record views, restrained
semantic color, and expressive but non-authoritative overview graphics. It is
beautiful through proportion, typography, causality, and coherence—not through
effects that obscure evidence.

This dossier is a design contract and decomposition input. It does not activate
a new authority model, move files, publish repository-private data, replace
TODO.md, or authorize implementation. Those require separately allocated work
items and recorded decisions.

## 1. Outcomes

The finished product lets a user:

1. navigate any mentioned identifier to a canonical definition or a typed
   missing/redacted/historical explanation;
2. trace every claim in both directions to decisions, reviews, evidence, source
   document/version/page, code, validation, Acceptance, and integration;
3. explore all three documentation universes at equal structural rank;
4. curate uncertain extraction/content with source comparison and safe handoff;
5. review exact immutable candidates with complete protocols and findings;
6. understand the separate implementation, claim, validation, Acceptance,
   checkpoint, integration, trust, freshness, and publication states;
7. use dynamic tickets and dependency graphs without losing accessible tables
   or the authoritative source boundary;
8. discuss content with AI while inspecting the exact context and provenance;
9. finalize a reviewed change through an idempotent, authority-aware workflow;
10. read every information view without JavaScript and in all eleven locales;
11. use the system at 320 px, 400% zoom, by keyboard, screen reader, RTL, print,
    slow network, offline, or degraded-source conditions;
12. evolve schemas, routes, layouts, and components without hand-editing
    thousands of generated pages.

## 2. Information architecture

Six stable domains form the global navigation:

- **Explore:** AUTOSAR Adaptive, AUTOSAR Classic, S-Core, requirements, APIs,
  sources, diagrams, versions, and comparisons.
- **Trace:** typed relationships, provenance paths, coverage, conflicts,
  dependencies, history, and as-of snapshots.
- **Curate:** queues, evidence comparison, proposed changes, conflicts, batch
  triage, claims, submissions, and archive.
- **Review:** requests, protocols, findings, decisions, re-reviews, public
  feedback, and receipts.
- **Work:** portfolio, Features/Tasks/Subtasks, claims, dependencies, decisions,
  Acceptance, checkpoints, integration, validations, evidence, and audit.
- **Reports:** current state, build/publication, extraction, traceability,
  curation, review, validation, campaign, i18n, performance, accessibility,
  security, and report history.

`Discuss` is contextual across every entity. Settings contain language,
appearance, density, privacy, sessions, and notification routing.

The complete view catalog and universal states are normative inputs in
[`ui-ux-view-inventory.md`](ui-ux-view-inventory.md).

## 3. Shared record anatomy

Every knowledge, governance, evidence, and report record uses:

1. canonical identity and exact-version link;
2. source-of-truth versus derived-view label;
3. independently typed status dimensions;
4. source REF/digest, schema, generated-at/as-of, freshness, classification,
   signature/verification;
5. Overview;
6. Relations/Trace;
7. Evidence;
8. Reviews;
9. History;
10. Raw immutable source;
11. actions only when assignment, authority, freshness, and connectivity allow.

This resolves the central governance risk: visually similar green badges can
never make `[x]` appear accepted, an accepted Task appear integrated, a
submitted review appear ingested, or a derived report appear authoritative.

## 4. Traceability architecture

One typed identity registry and one typed relation registry generate routes,
links, reverse links, search documents, breadcrumbs, graphs, tables, exports,
and tombstones. Handwritten identifier links are prohibited.

Every rendered assertion supports `Why?` and reverse `Where used?`. Assertions
carry asserted/inferred/conflicting/rejected status; relations carry evidence,
rule version, validity, review state, and classification. Historical links pin
immutable versions. Current pages mark prior reviews/reports stale when their
candidate changes while preserving append-only history.

The full grammar, failure semantics, search, locale, provenance, privacy, and
link gates are in
[`ui-ux-route-and-link-contract.md`](ui-ux-route-and-link-contract.md).

## 5. Visual concept

The visual system combines an engineering atlas with a rigorous audit console.
Overview pages are spacious and orienting; inspect pages are evidence-first;
action pages are deliberate and explicit. Governance feels solemn through
identity, density, and confirmation—not a separate brand.

The same shell supports light, dark, forced-colors/high-contrast, and print.
Users may choose comfortable or compact density. Responsive layout uses a
12-column wide canvas, readable prose measure, full-width data regions, and a
context rail that becomes a drawer. Tables remain primary for audit; graphs
always have synchronized accessible alternatives.

Tokens, component anatomy, responsive behavior, statuses, graph grammar,
interaction safety, themes, localization, and accessibility are in
[`ui-ux-design-tokens.md`](ui-ux-design-tokens.md).

## 6. Eleven-language design

The locales are German, English, Spanish, Portuguese, French, Russian, Arabic,
Hindi, Korean, Chinese, and Dutch. Locale is presentation, never identity.
Language switching preserves entity/version/anchor/filter. Unavailable content
shows an explicit fallback language rather than navigating home or pretending
translation completeness.

One ICU catalog owns UI strings. Normative record text, translations, and
generated explanations are separate layers with independent provenance and
freshness. Identifiers and technical enums never translate. Arabic uses
logical layout and bidi isolation; chronology, code, IDs, hashes, and graph
direction do not reverse. Pseudolocales test 60% expansion and RTL before any
human translation is accepted.

## 7. Static read plane and authenticated control plane

The read plane is deterministic static HTML/JSON, progressively enhanced and
usable without JavaScript. Generated output is disposable and reproduced from
authored sources, schemas, and adapters. Route-specific capability islands load
search, graph, curation, review, or discussion only when needed.

The control plane is narrow and authenticated. A backend-for-frontend holds
provider credentials; the browser gets only an opaque rotated short-TTL secure
session. Mutations use CSRF protection, reauthentication where required, exact
target digest, authority and assignment checks, idempotency, optimistic
concurrency, append-only receipts, and recovery. Offline mode exports a draft
only.

Public, internal, and restricted UI are different deployment artifacts and
trust boundaries. The public build contains no internal/restricted bytes,
identifiers, counts, hashes, routes, indexes, manifests, or cache artifacts.
Internal/restricted responses require authorization and separate private/no-
store cache policy. Unknown classification fails closed. Raw TODO claims, mail,
agent memory, runner records, absolute paths, secrets, private evidence, and
personal data are not published by path discovery.

## 8. Performance architecture and budgets

The current baseline contains about 7,100 HTML files and 372 MB of site data.
Representative root pages are already large (`index.html` ~486 KB,
`traceability.html` ~643 KB), and the current template loads review and graph
features broadly. The redesign must not hydrate the corpus or load the complete
relationship graph.

Budgets:

| Surface | Budget |
|---|---|
| Base mobile route | ≤100 KB Brotli-11 HTML + critical CSS; ≤35 KB Brotli-11 executable JS; ≤3 requests—including fonts—before the first H1 and primary content are painted and keyboard-readable |
| Core Web Vitals | p75 LCP ≤2.5 s, INP ≤200 ms, CLS ≤0.10 on representative 4G/4× CPU |
| Review/curation island | ≤50 KB Brotli-11 JS, loaded on invocation |
| Graph engine + worker | ≤180 KB Brotli-11, graph routes only |
| Initial graph data | ≤150 KB Brotli-11, ≤500 rendered nodes, ≤1,000 rendered edges; a 1,000+ raw-node fixture must aggregate/page below the rendered cap |
| Graph interaction | first useful ≤2.5 s; pan/filter ≤100 ms; no main-thread task >50 ms |
| Large tables | 10,000 records supported through server/build-time pagination and semantic tables; virtualization is optional enhancement, never the sole accessible carrier |
| Incremental build | p95 ≤5 s for one content record |
| Full build | mandatory predecessor `F-E0 Build Baseline Ratification` freezes numeric wall/CPU/RSS/public-output ceilings, named hardware, corpus, command, environment, and cold/warm profiles before F-E implementation starts; thereafter ≤10% regression and byte-identical output for identical inputs |

Large graphs use build-time adjacency indexes, 1–2-hop progressive fetch,
aggregation, workers, abortable layout/search, deep links, and accessible
tables. CI records command, hardware, warm/cold cache, compression, corpus,
wall/CPU/RSS, output size, JS heap, long tasks, and worker termination/leaks.
Immutable assets use fingerprinted year caching; HTML/manifests revalidate;
authenticated and sensitive responses use partitioned private caching or
`no-store`.

Numeric full-build ceilings are deliberately not invented without measurement.
`F-E0` is an acceptance-before-start predecessor: it runs the agreed current
baseline on the named reference machine at least five cold and five warm times,
records median and p95 wall/CPU/RSS/output, proposes finite ceilings with
rationale and headroom, and receives independent performance/architecture
review. F-E cannot start until that committed ratification product is accepted.

## 9. Security, privacy, and authority

Release blockers:

- eliminate GitHub PAT storage in localStorage/sessionStorage/URL/DOM/logs;
- enforce classified projections and secret/PII/path scanning;
- adopt strong CSP, `nosniff`, Referrer-Policy, Permissions-Policy,
  frame/object/base restrictions, dependency integrity/SBOM, and audited DOM
  construction/sanitization;
- prevent restricted existence leakage through search, counts, autocomplete,
  backlinks, errors, exports, or telemetry;
- state actor, assignment, authority, exact baseline, side effects, recovery,
  and signature status before authoritative actions;
- distinguish transport, ingestion, review, Acceptance, integration, and
  publication in UI and receipts.

Telemetry is aggregate and privacy-minimal: Web Vitals, route/template/schema
versions, asset/build ID, error category, and graph cardinality. It excludes
names, rationale, evidence, tokens, full URLs, and raw queries; consent/DNT,
retention, sampling, deletion, and local diagnostic export are defined first.

## 10. Proposed repository and publication layout

The future layout removes leading underscores and separates authored material,
contracts, generators, build output, and runtime deployment:

```text
src/
  adapters/              repository/spec/governance ingestion
  content/               authored explanations and editorial sources
  design-system/         tokens, components, icons, fixtures
  generators/            deterministic HTML/JSON/search/route builders
  i18n/                  ICU catalogs, glossary, locale metadata, pseudo-locales
  schemas/               entity, relation, projection, action, report schemas
  templates/             shell and view templates
  tests/                 unit, fixture, browser, visual, a11y, perf, security
  tools/                 validation and migration tools

www/                     disposable publish root; generated, never hand-edited
  assets/                fingerprinted CSS/JS/fonts/icons/images/workers
  data/                  classified versioned view projections and indexes
  de/ en/ es/ pt/ fr/ ru/ ar/ hi/ ko/ zh/ nl/
  curate/ review/ work/ governance/ evidence/ reports/ discuss/ settings/
  route-manifest.json
  release-manifest.json

deploy/public/           public-only artifact; zero internal/restricted bytes
deploy/internal/         authenticated artifact and private indexes
deploy/restricted/       per-request authorized projections; no-store default

docs/design/             architecture and design contracts
docs/features/           branch-bound Feature memory only
logs/agent-memory/       versioned long-term agent/role/capability memory
logs/                     retained validation/build evidence by policy
issues/                   canonical issue/work schemas and records during cutover
```

The current `_src`→`src` and root HTML→`www` migration is a dedicated reversible
Feature, not a rename mixed with the visual redesign. Generated root assets
remain served through legacy redirects until route parity and link-crawl gates
pass. S-Core elevation and AUTOSAR Classic import are separate content Features
that consume the shared route/entity model.

## 11. Build and changeability

Every projection includes `$schema`, `schema_version`, canonical ID, source
REF/digest, classification, generation time, and compatibility range. Additive
fields are tolerated; unsupported major versions show a visible degraded state.
Migrations are pure fixture-tested transforms. Atomic publication retains the
previous release manifest and supports one-command rollback.

Generated HTML is never manually fixed. View manifests, entity adapters,
shared templates, semantic components, route registry, and ICU catalog are the
only authoring points. A component change is tested once across the view/state/
locale/theme matrix rather than patched into each report.

## 12. Quality definition

“Perfect” is not a testable disposition. The release threshold is:

- complete view, route, entity, relation, state, permission, and source mapping;
- zero unresolved P0/P1 critic findings;
- every P2 finding implemented or explicitly dispositioned with evidence;
- zero unexplained broken internal identifiers, links, anchors, canonical
  routes, hreflang pairs, reverse links, or provenance edges;
- WCAG 2.2 AA and manual assistive-technology journeys;
- all eleven locales plus expanded and RTL pseudo-locales;
- performance, security, privacy, concurrency, no-JS, offline, schema,
  migration, deterministic build, rollback, and print/export gates;
- visual regression at 320/768/1440/1920, themes, zoom, longest strings, RTL;
- Management approval of the three remaining product choices below.

## 13. Management interview decisions

The architecture is robust under either answer, but implementation should pin:

1. **Personality:** recommended calm technical editorial core, expressive
   graphics only on non-evidentiary overview surfaces; alternative is a more
   futuristic cockpit character.
2. **Visibility:** recommended `public`, `internal`, `restricted` classified
   projections, default deny; alternative full public governance is rejected
   unless Management accepts privacy/security exposure explicitly.
3. **Density:** recommended comfortable default plus persistent compact expert
   mode; alternative compact-by-default favors current maintainers over new
   readers.

## 14. Governance activation and rollback

This dossier is self-applying only to its own evidence and critique process. It
does not implicitly grandfather current pages or activate cross-item gates.
Future decision records must separately authorize: canonical route migration,
classified governance publication, control-plane authentication, ticket-system
authority cutover, email delivery/data retention, telemetry/privacy, and final
release/cutover.

Each implementation Feature declares target policy, exact predecessor products,
one terminal integrating Task marked `Integration review: mandatory`, test
obligation, migration/rollback, security/privacy reach, and no-checkpoint
justification for every irreversible/external/credential boundary left
unmarked. The implementation roadmap contains the proposed graph.

## References

- [View inventory](ui-ux-view-inventory.md)
- [View-to-route/source/permission matrix](ui-ux-view-route-matrix.md)
- [Route and link contract](ui-ux-route-and-link-contract.md)
- [Visual system and tokens](ui-ux-design-tokens.md)
- [Visual reference set](assets/ui-ux-visual-reference.md)
- [Implementation roadmap](ui-ux-implementation-roadmap.md)
- [Quality trace matrix](ui-ux-quality-trace-matrix.md)
- [Critique log](ui-ux-critique-log.md)
