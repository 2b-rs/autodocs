# UI/UX view inventory

Status: design contract candidate  
Authority: current-user UI/UX architecture order, 2026-08-24  
Scope: the complete public documentation, work, governance, review, curation,
reporting, and conversational experience.

## 1. Inventory method

The inventory treats a view as a stable user goal, not as an HTML filename.
Every view has a canonical entity, presentation variants, permissions, data
states, and a no-JavaScript/read-only baseline. Generated detail pages share a
template; individual requirements, classes, Tasks, decisions, and reports are
instances rather than new view types.

Current baseline evidence includes:

- root landing, process, traceability, curation, open-review, extraction,
  build/publication, and E2E requirement pages;
- 16 module pages, 41 namespace pages, 340 class/type pages, eight service
  pages, and their requirement anchors;
- German plus ten translations: English, Spanish, Portuguese, French,
  Russian, Arabic, Hindi, Korean, Chinese, and Dutch;
- local review collection, GitHub issue submission, curation/review queues,
  ticket schemas, TODO/claim bookkeeping, decision dossiers, validation logs,
  campaign evidence, Acceptance and integration records;
- future S-Core and AUTOSAR Classic documentation, DHTML ticket management,
  AI discussion, editorial submission, notification, and VM/test context.

## 2. Global shell and system views

| ID | View | Primary purpose | Essential regions/actions |
|---|---|---|---|
| SYS-01 | Role-aware home | Orient without moving information by role | product status, continue work, recent evidence, release/version, domain shortcuts |
| SYS-02 | Global search | Resolve exact IDs first, then concepts | omnibox, typed groups, filters, freshness, restricted-result-safe counts |
| SYS-03 | Command palette | Keyboard navigation and safe commands | recent entities, route actions, permission explanations |
| SYS-04 | Activity and notifications | Show review, curation, build, and governance events | unread/read, type, urgency, entity link, as-of, notification settings |
| SYS-05 | User/preferences | Locale, theme, density, motion, saved views | no authority inference from identity |
| SYS-06 | Help and terminology | Explain status vocabularies and relation types | glossary, shortcuts, accessibility, provenance reading guide |
| SYS-07 | Access denied | Explain visibility without leaking protected data | reason class, request path, safe return |
| SYS-08 | Not found / tombstone | Preserve typed missing/superseded history | last known ID/type, successor, archived ref, redaction-safe message |
| SYS-09 | Offline/degraded | Preserve readable last-known state | as-of/ref, unavailable sources, retry, mutation disabled |
| SYS-10 | Maintenance | Planned operational interruption | scope, start/end, read-only alternatives |
| SYS-11 | Print/export | Produce self-identifying evidence | ID, baseline, digest, as-of, classification, signature state, page count |
| SYS-12 | Release/version chooser | Compare current and historical projections | release, branch/baseline, locale coverage, current marker |

Persistent top navigation is `Explore`, `Trace`, `Curate`, `Review`, `Work`,
and `Reports`. `Discuss` is a contextual affordance, not a seventh information
silo. Role-aware homes may alter shortcuts, never canonical locations.

## 3. Knowledge and specification views

| ID | View | Canonical entity | Required tabs or subordinate views |
|---|---|---|---|
| KN-01 | Documentation universe | documentation collection | AUTOSAR Adaptive, AUTOSAR Classic, S-Core, releases, coverage |
| KN-02 | Module catalog | module collection | cards/table, facets, relationships, coverage |
| KN-03 | Module detail | module | Overview, API, Requirements, Trace, Evidence, History |
| KN-04 | Namespace catalog/detail | namespace | members, types, services, used-by, source |
| KN-05 | Type/class detail | type | synopsis, members, requirements, diagrams, evidence, reviews |
| KN-06 | Service detail | service | interface, events/fields/methods, compatibility, requirements |
| KN-07 | API/member detail | member | signature, semantics, availability, source, inbound/outbound links |
| KN-08 | Requirement detail | requirement record | exact text, metadata, upstream/downstream, evidence, reviews, history |
| KN-09 | Generic specification record | typed spec record | raw/localized text, relations, validity, provenance |
| KN-10 | Source catalog | source-document collection | standard, platform, release, language, availability |
| KN-11 | Source detail / locator | source document/version/page | PDF/named destination, extracted region, last verified, legal notice |
| KN-12 | Diagram detail/fullscreen | diagram | semantic legend, zoom, source, text alternative, export |
| KN-13 | AI explanation detail | generated assertion | AI label, derivation, cited facts, confidence, review status |
| KN-14 | Version history/diff | entity versions | exact baselines, semantic diff, unchanged context, raw |
| KN-15 | Comparison | two entities/versions/locales | aligned fields, missing/fallback labels, shareable selection |
| KN-16 | Backlinks/used-by | inbound relations | typed source, relation, baseline, export |
| KN-17 | Orphan/coverage queue | coverage finding set | missing source/target, severity, curation route |

S-Core and AUTOSAR appear at the same hierarchy level. Platform, standard,
release, and module are filters—not separate visual products.

## 4. Traceability and provenance views

| ID | View | Purpose | Non-negotiable alternative |
|---|---|---|---|
| TR-01 | Trace overview | coverage, conflict, orphan, review, freshness indicators | summary table |
| TR-02 | Entity relationship graph | explore typed inbound/outbound relations | synchronized tree/table |
| TR-03 | Provenance path | answer “Why is this shown?” end to end | ordered evidence chain |
| TR-04 | Coverage matrix | map source requirements to API/docs/tests | accessible table/export |
| TR-05 | Dependency DAG | feature/task ordering and blockers | topological list plus edge table |
| TR-06 | Provenance event graph | append-only mutations and absorptions | chronological event table |
| TR-07 | Conflict comparison | show asserted/inferred/conflicting/rejected claims | field-by-field evidence view |
| TR-08 | Historical as-of snapshot | reconstruct a prior baseline | immutable raw manifest |

Every graph node exposes type, stable ID, title, state, and classification.
Every edge exposes direction, relation type, assertion status, evidence, rule
version, validity, and review state. A canvas or SVG is never the sole carrier.

## 5. Curation and editorial views

| ID | View | Purpose | Actions |
|---|---|---|---|
| CU-01 | Curation workspace | queue health and assignment | filter, save view, claim eligible work |
| CU-02 | Curation item | decide one source/content ambiguity | inspect evidence, discuss, propose, defer |
| CU-03 | Evidence comparison | compare source screenshot/text/current output | zoom, align, cite exact region |
| CU-04 | Proposed edit/diff | make intent and generated impact explicit | edit rationale, preview, validate |
| CU-05 | Conflict resolution | reconcile competing proposals | compare authority/evidence, escalate |
| CU-06 | Batch triage | classify repeated findings safely | select, preview scope, reversible batch action |
| CU-07 | Assignment/claim | record ownership without implying authority | lease, scope, collision, takeover history |
| CU-08 | Submission preview | freeze proposed package | manifest, affected entities, tests, privacy |
| CU-09 | Submission receipt | prove transport, not acceptance | idempotency key, destination, status, retry |
| CU-10 | Completed/archive | find prior decisions and impacts | as-of search, reopen rules, backlinks |

## 6. Review and feedback views

| ID | View | Purpose | Required safeguards |
|---|---|---|---|
| RV-01 | Context annotation drawer | discuss a specific entity/field | anchored selection, thread, provenance |
| RV-02 | Annotation thread | preserve questions and replies | actor/classification, status, links |
| RV-03 | Review request composer | create a bounded request | candidate, question, context, forbidden actions |
| RV-04 | Review preview/submit | verify exact package | identity mode, privacy, target, idempotency |
| RV-05 | Review receipt | distinguish submitted/ingested/assigned | transport and processing timeline |
| RV-06 | Review queue | prioritize pending reviews | competence/authority/independence filters |
| RV-07 | Review protocol | render applicable checklist and contract | version, scope, authority, test obligation |
| RV-08 | Findings register/detail | track each material finding | severity, evidence, owner, disposition, retest |
| RV-09 | Review decision | record accepted/rejected/inconclusive | exact baseline/digests, signer, authority, history |
| RV-10 | Re-review | compare corrected candidate | old/new baseline, closed/open findings |
| RV-11 | Public feedback | collect non-authoritative feedback | consent, privacy, status token, abuse handling |
| RV-12 | Feedback status | show receipt and published response | no private queue leakage |

## 7. Work, governance, and audit views

All record details use the same anatomy: identity header; independently typed
state dimensions; overview; relations; evidence; reviews; history; raw source;
and, only when authorized, actions.

| ID | View | Canonical entity | Key state dimensions |
|---|---|---|---|
| GW-01 | Portfolio/backlog | work collection | lifecycle, dependency readiness, risk, checkpoint |
| GW-02 | Feature detail | feature | implementation, prerequisite closure, checkpoints, Acceptance, integration |
| GW-03 | Task/subtask detail | work item | marker, claim, validation, Acceptance, target branch |
| GW-04 | Claim detail/history | claim | active/released/expired/takeover, owner token, scope collision |
| GW-05 | Decision register | decision collection | effective/superseded/invalidated, affected gates |
| GW-06 | Decision detail | decision record | authority, alternatives, consequences, review participation |
| GW-07 | Provenance register | provenance collection | validity, origin, baseline, absorption, verification |
| GW-08 | Provenance record | provenance event | source/target ref, trailer/digest, chain, raw |
| GW-09 | Acceptance register | acceptance decisions | current/stale/invalidated, item, reviewer independence |
| GW-10 | Acceptance detail | acceptance review | contract, candidate, prerequisite closure, validation, decision |
| GW-11 | Checkpoint queue | integration obligations | readiness, assigned integrator, induced batch |
| GW-12 | Integration review | checkpoint review | candidate, target, tests, induced Acceptance, verdict |
| GW-13 | Integration verdict | append-only verdict | author, authority, timestamp, rejected items, tip, resolution |
| GW-14 | Validation run | validation execution | profile, environment, exact baseline, results, logs |
| GW-15 | Evidence bundle | manifest | entries, digests, classification, retention, missing evidence |
| GW-16 | Audit timeline | entity or repository events | event type, actor, authority, ref, prior/next state |
| GW-17 | Audit event | immutable event | raw record, signature, linked entities, correction |
| GW-18 | Authority/role matrix | authority policy projection | role, assignment, competence, independence, waiver |
| GW-19 | Policy/schema registry | versioned contracts | effective version, compatibility, migrations |
| GW-20 | Raw/source inspector | immutable artifact | exact bytes/text, digest, copy/download, sanitization note |

The UI never merges these independent dimensions into one status:

1. implementation marker (`open`, `in-progress`, `implemented`, `waived`,
   `user-decision`);
2. claim/lease and collision state;
3. validation state;
4. Acceptance state;
5. checkpoint requirement and review verdict;
6. integration/publication state;
7. trust/signature state;
8. freshness/current-baseline state;
9. transport/ingestion state;
10. permission/classification state.

## 8. Report and operational views

| ID | View | Purpose | Required context |
|---|---|---|---|
| RP-01 | Report center | one index for every report family | type, status, as-of, baseline, source, owner |
| RP-02 | Status/current-state report | operational truth projection | authoritative inputs, freshness, unresolved conflicts |
| RP-03 | Build/publication report | build vs publication outcome | exact commit, environment, artifacts, deploy state |
| RP-04 | Extraction report index | version history | release, deltas, parser/rule version |
| RP-05 | Extraction report detail | quality, changes, evidence | curation links, affected records/pages, screenshots |
| RP-06 | Traceability report | coverage and breaks | exact graph/index version, gaps, drill-down |
| RP-07 | Curation report | open/resolved editorial questions | queue state, affected data, review actions |
| RP-08 | Review report/protocol | review evidence and decision | candidate, checklist, findings, signatures |
| RP-09 | Validation report | test obligation and execution | profile, logs, results, exceptions |
| RP-10 | Campaign/feature report | delivery narrative and evidence | goals, work graph, checkpoints, outcomes |
| RP-11 | i18n coverage report | locale completeness/quality | keys, content, fallback, review, bidi/visual results |
| RP-12 | Performance report | budgets and regressions | route/device/network, field/lab metrics |
| RP-13 | Accessibility report | WCAG evidence | automated/manual matrix, assistive tech, exceptions |
| RP-14 | Security/privacy report | exposure and control findings | classification, redaction, role matrix, remediation |
| RP-15 | Report version/delta | compare report baselines | generated-at, source changes, stale/invalidated state |

Reports are explicitly labelled `derived view—not authority` unless their
record type is itself the signed authoritative artifact. Report-specific CSS
may implement unique diagrams only; shells, tables, statuses, evidence, print,
themes, and controls use shared components.

## 9. DHTML ticket and dependency views

| ID | View | Purpose |
|---|---|
| TK-01 | Ticket board/list | browse/filter work without losing authoritative semantics |
| TK-02 | Ticket detail | full Feature/Task/Subtask contract and evidence |
| TK-03 | Dependency explorer | interactive DAG plus accessible table/topological order |
| TK-04 | Milestone/campaign roadmap | group Features and checkpoints over time |
| TK-05 | Work query builder | save/share typed filters |
| TK-06 | Change preview | show exact backlog mutation before submission |
| TK-07 | Conflict/takeover | handle stale/CAS/collision/lease conditions |
| TK-08 | Migration comparison | compare TODO projection with web-ticket projection |

The web ticket system starts as a projection. It becomes authoritative only
after a separately decided, reversible cutover with parity, dual-read, and
rollback evidence.

## 10. AI discussion and context views

| ID | View | Purpose | Guardrail |
|---|---|---|---|
| AI-01 | Contextual assistant | discuss current entity | context manifest always visible |
| AI-02 | Conversation workspace | multi-turn inquiry | source citations, model/run metadata, privacy |
| AI-03 | Context inspector | show exactly what the AI sees | include/exclude, token/cost estimate, redaction |
| AI-04 | Proposed change | structured editable output | diff, provenance, validation plan, no auto-accept |
| AI-05 | Submission/finalization | freeze reviewed result | actor, authority, manifest, idempotency, rollback |
| AI-06 | Automation run | build/update execution | exact baseline, logs, results, partial failure |
| AI-07 | Coding-context assembly | AUTOSAR→S-Core implementation context | requirement coverage, dependencies, tests, gaps |
| AI-08 | VM/test execution | run generated implementation safely | sandbox profile, inputs, artifacts, failures |

## 11. Administration and localization views

| ID | View | Purpose |
|---|---|
| AD-01 | Locale coverage dashboard | distinguish UI-string, content, glossary, and review coverage |
| AD-02 | Translation queue | prioritize missing/stale segments |
| AD-03 | Segment editor/review | source, translation, variables, glossary, history |
| AD-04 | Glossary/term registry | stable technical terms and forbidden translations |
| AD-05 | Build/generation run | source-to-output manifest and logs |
| AD-06 | Publication preview/dry run | validate the exact deployable site |
| AD-07 | Content/schema registry | entity and relation contracts, compatibility |
| AD-08 | Source/health dashboard | degraded external PDFs, queues, indexes, notifications |
| AD-09 | Notification routing | email/event rules, consent, secrets-safe configuration |

## 12. Universal state matrix

Every data-driven view has fixtures for: default, empty, filtered-empty,
loading, partial, stale, error, offline, permission-denied, redacted,
conflict, superseded, rejected, inconclusive, invalidated, expired,
takeover-pending, tombstoned, and very-large. Actions additionally cover
unauthorized, unassigned, stale-candidate, confirmation, submitting,
success/receipt, retryable failure, non-retryable failure, and indeterminate
transport state.

## 13. Cross-view acceptance rule

The inventory is complete only when every row maps to a canonical route,
entity/data source, permission class, responsive anatomy, localization
behavior, state fixtures, no-JS baseline, performance budget, accessibility
journey, and future implementation owner. That mapping is defined by the
route/link contract and implementation roadmap; missing mappings block the
design checkpoint.
