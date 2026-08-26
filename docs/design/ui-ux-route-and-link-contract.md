# Canonical route, identity, and link contract

Status: design contract candidate  
Principle: locale, filename, display title, and current branch are properties;
none of them is an entity identity.

## 1. Typed identity model

All visible entities implement one `EntityRef`. Its canonical registry key is
a typed URN, never a bare identifier:

```text
EntityRef {
  kind: EntityKind
  urn: "urn:autodocs:{kind}:{percent-encoded-id}:{version-kind}:{version-id}"
  id: stable locale-neutral identifier
  version?: immutable release, REF, digest, or record version
  anchor?: stable typed subsection ID
  locale?: presentation locale only
}
```

All relationships implement one `RelationRef`:

```text
RelationRef {
  kind: RelationKind
  source: EntityRef
  target: EntityRef
  assertion: asserted | inferred | conflicting | rejected
  evidence: EntityRef[]
  rule_version?: string
  valid_from?: immutable baseline
  valid_to?: immutable baseline
  review_state?: unreviewed | accepted | rejected | inconclusive | stale
  classification: public | internal | restricted
}
```

Minimum entity kinds are: documentation collection, release, module,
namespace, type, member, service, requirement, specification record, source
document, source locator, diagram, AI assertion, work item, claim, decision,
policy, provenance event, review request, review, finding, Acceptance decision,
integration checkpoint, integration verdict, validation run, evidence bundle,
artifact, audit event, report, report version, curation item, feedback item,
conversation, build, publication, schema, locale segment, notification, and
user-visible role/authority projection.

Identifiers, hashes, enums, signatures, paths, and ISO timestamps are never
localized. Human titles and summaries may be localized and carry provenance.
Opaque IDs are percent-encoded and decoded as data, never path segments; `/`,
`..`, NUL, separators, and case folding cannot change route structure. Bare IDs
and SHAs may resolve to several typed roles or releases and therefore return a
deterministic typed chooser. The same SHA can legally be candidate, source REF,
review REF, and absorbed commit without identity collision.

## 2. Canonical route families

Logical routes omit deployment-specific `.html`; static output may add it via
the route manifest. Presentation locale is always explicit for localized
knowledge. Governance identity remains locale-neutral; `?lang=` selects a
translation without changing the record identity.

```text
/{locale}/
/{locale}/docs/{universe}/
/{locale}/docs/{universe}/releases/{release}
/{locale}/docs/{universe}/modules/{moduleId}
/{locale}/docs/{universe}/namespaces/{namespaceId}
/{locale}/docs/{universe}/types/{typeId}
/{locale}/docs/{universe}/services/{serviceId}
/{locale}/docs/{universe}/members/{memberId}
/{locale}/requirements/{recordId}
/{locale}/records/{recordId}
/{locale}/sources/{sourceId}
/{locale}/trace/{traceId}

/curate
/curate/items/{curationId}
/review
/review/requests/{requestId}
/review/reviews/{reviewId}
/review/findings/{findingId}

/work
/work/items/{itemId}
/work/items/{itemId}/claims/{claimId}
/work/dependencies/{itemId}

/governance/decisions/{decisionId}
/governance/policies/{policyId}
/governance/provenance/{eventId}
/governance/acceptance/{reviewId}
/governance/checkpoints/{checkpointId}
/governance/integration-reviews/{reviewId}
/governance/verdicts/{verdictId}
/governance/audit/events/{eventId}

/evidence/runs/{runId}
/evidence/bundles/{bundleId}
/evidence/artifacts/{artifactId}
/reports
/reports/{reportType}/{reportId}
/reports/{reportType}/{reportId}/versions/{version}

/discuss/{conversationId}
/settings/language
/settings/appearance
/settings/privacy
/settings/sessions
```

`universe` is `autosar-adaptive`, `autosar-classic`, or `s-core`. They are
siblings. Current hashed filenames remain legacy aliases until link-crawl and
analytics evidence permit their removal.

Collection, workflow, comparison, administration, and system-state routes are
defined per view in
[`ui-ux-view-route-matrix.md`](ui-ux-view-route-matrix.md). That matrix is the
normative 100% inventory-to-route/source/permission/no-JS coverage proof.

## 3. Identifier resolver

One generated registry maps exact identifiers and aliases to `EntityRef`.
Resolution order is deterministic:

1. exact typed ID (`SWS_*`, `RS_*`, `DEC-*`, Feature/Task/Subtask, claim,
   review, run, report, full SHA/digest);
2. canonical technical name or unique alias;
3. localized title/term;
4. full-text relevance.

All identifier mentions in rendered prose, tables, logs, diffs, diagrams,
review protocols, and reports pass through this resolver. Unknown candidates
remain visible as `unresolved identifier`, are never linked heuristically, and
enter the coverage queue. Ambiguous aliases show a typed chooser.

## 4. Stable anchors and linkable fields

Anchors are semantic and generator-owned: `overview`, `relations`, `evidence`,
`reviews`, `history`, `raw`, plus stable record/member/field IDs. Heading text
and translation never determine an anchor. Every record header and evidence
row provides `Copy link`; copied links include an immutable version when the
context is historical or review-sensitive.

Changing locale, theme, or density preserves entity, version, anchor, query,
filters, selected graph node, and—where feasible—scroll/focus. Browser Back
restores filters, pagination, graph viewport, selection, and focus target.

## 5. Current, historical, and derived state

Every governance/work/report detail has a persistent State Header:

- entity kind and stable ID;
- independently typed lifecycle states;
- authoritative source and whether this is a projection;
- exact source REF/digest and schema version;
- generated-at and as-of timestamps;
- current/fresh, stale, superseded, invalidated, inconclusive, or unverifiable;
- authority/signature state and privacy class;
- predecessor/successor, superseded-by, invalidated-by, and full history.

There is no universal cross-dimension precedence. Each entity schema declares
a derivation function per state dimension:

```text
derive(entity, dimension, baseline, as_of, audience):
  select the dimension's authoritative source type
  require exact baseline compatibility and effective interval
  apply authorized additive correction, supersession, and invalidation events
  reject conflicting same-rank records as unverifiable
  never infer a different dimension
  return value + source refs + rule version + freshness + conflict set
```

Task marker, claim, validation, Acceptance, checkpoint, integration,
publication, trust/signature, and freshness therefore have separate authorities
and truth tables. Decision proposal, approval, effectivity, supersession, and
invalidation are likewise separate. An immutable historical record is true
history but not automatically current. Derived views never overwrite history.

A candidate change automatically marks baseline-bound reviews and derived
reports stale. It never rewrites their original label. `[x]`, Acceptance,
checkpoint review, integration, publication, trust, and freshness are separate
dimensions, not one progress badge.

## 6. Provenance traversal

Every rendered normative fact, generated explanation, diagram edge, Task
status, and report assertion exposes `Why?`:

```text
rendered assertion
→ record property / work state
→ derivation rule or decision
→ review / finding / disposition
→ evidence extract or validation run
→ exact source document, version, page or immutable artifact
```

Reverse traversal is equally required. Each edge is typed and baseline-bound.
Source URLs are locators, not identity; external AUTOSAR documents record
document ID, release, page/named destination, last-verified time, and cached
evidence metadata.

## 7. Alias, redirect, tombstone, and failure semantics

The route manifest classifies every old or missing route as one of:

- permanent alias to the same entity;
- explicit historical version;
- superseded entity with successor;
- redacted/restricted entity using one audience-policy outcome: (a)
  indistinguishable not-found, (b) existence-only restricted notice, or (c)
  redacted detail;
- archived/tombstoned entity with last known identity;
- structured dangling relation requiring repair;
- ordinary unknown route.

Aliases preserve safe query parameters and valid fragments. Missing fragments
show the entity and a structured `section no longer exists` notice. Broken
provenance never degrades to an unexplained 404. Offline external sources show
the evidence identity and last verification, not a false missing record.

The selected restriction outcome applies consistently to search, counts,
autocomplete, backlinks, route manifests, raw/source, export, error wording,
logs, caches, and telemetry. Public artifacts cannot contain restricted route
entries or hashes even when their page is unreachable.

Historical identity is typed: `/versions/{versionKind}/{encodedVersion}` or
`?at={versionKind}:{encodedVersion}` where `versionKind` is `release`, `ref`,
`sha256`, or `record`. Canonical query keys are versioned and allow only
`at`, `lang`, `q`, declared filters, sort, page/cursor, selected entity, and a
bounded graph viewport token. Secrets, actor-entered rationale, private IDs,
raw evidence, and authentication state are never serialized. Unknown keys are
dropped; non-canonical ordering redirects to the normalized URL.

## 8. Search and filter contract

One search surface groups results by type and exposes source, freshness, and
classification-safe state. Filters include universe, release, entity type,
module, lifecycle, review/Acceptance/integration state, origin, assertion,
confidence, locale/content availability, date, role/owner projection, and
authority class. Search/filter/sort/page are shareable URL parameters.

Restricted fixtures contribute neither text snippets nor differential counts.
Zero-result state distinguishes no match, filtered-out, offline index, and
permission-limited results. Exact-ID resolution is offered before relaxed
search.

## 9. Locale contract

Supported UI locales are `de`, `en`, `es`, `pt`, `fr`, `ru`, `ar`, `hi`, `ko`,
`zh`, and `nl`. Locale names are shown as autonyms with text; flags are optional
decoration only. Canonical and reciprocal `hreflang` links are generated.

Switching locale retains the same entity/version/anchor. Missing translation
renders the canonical language in place with `Fallback: {language}` and a
link to translation status. It never silently returns to a home page.

Arabic uses logical CSS and mirrors navigation where semantically correct.
IDs, hashes, code, paths, signatures, timestamps, diffs, and mixed technical
tokens use LTR isolation with `bdi`; chronology and graph direction do not
reverse. Dates/numbers may be formatted for display while exact ISO values
remain copyable.

ICU message catalogs are the only UI-label source. Type checking covers keys,
variables, plurals, and select cases. Pseudolocales test 60% expansion and RTL.
Normative record bodies remain source-language artifacts; translations are
separately identified projections.

## 10. Security and publication boundary

Repository files are never served directly as governance pages. Classification
defines separate deployment artifacts and trust boundaries, not metadata in one
public tree:

- the public build contains no internal/restricted bytes, IDs, counts, hashes,
  filenames, search entries, route entries, manifests, or cache artifacts;
- internal projections are served only after authenticated authorization with
  separate indexes/manifests and private cache partitioning;
- restricted projections are authorized per request, enumeration-safe, and
  `no-store` unless a stricter approved partition exists.

Every projection carries source REF/digest, schema, generation time, redaction
reason where visible, and freshness. Unknown classification, secrets, personal
data, absolute internal paths, mailbox content, memory, runner secrets, or
unrestricted evidence fail closed. A deploy-artifact negative test scans the
actual public output, not only sources.

Read visibility and mutation authority are independent. Hiding a control does
not confer or enforce authority. Every mutation uses a short-lived authenticated
server session, exact target digest, assignment/authority check, idempotency
key, optimistic concurrency, explicit confirmation, append-only receipt, and
recovery path. Static/offline mode is export-only.

Browser-stored GitHub PATs and provider OAuth/device tokens are prohibited. A
backend-for-frontend holds the GitHub App/OAuth provider credential; the browser
receives only an opaque rotated short-TTL session cookie with `HttpOnly`,
`Secure`, and `SameSite=Strict`. The control plane requires OAuth state/PKCE,
Origin/Referer verification plus CSRF token, fixation prevention and rotation,
idle and absolute expiry, high-risk reauthentication, rate limiting, revocation,
and server-side authorization on every action. No credential/token appears in
DOM, URL, Web Storage, logs, exports, telemetry, service workers, or caches.

## 11. Automated link gates

CI must verify:

- unique canonical resolution for every typed entity/version;
- every internal link and fragment;
- incoming and outgoing relation symmetry;
- alias/redirect query and fragment preservation;
- canonical and reciprocal hreflang rules;
- same-entity locale switching and explicit fallback;
- typed tombstone/redaction/dangling behavior;
- exact historical/review baseline stability after HEAD advances;
- external source identity and last-verification metadata;
- zero unsafe schemes, leaked restricted targets, or handwritten bypasses.

Intentional missing-target fixtures must fail the build or produce a tested
typed tombstone—never a silent 404.
