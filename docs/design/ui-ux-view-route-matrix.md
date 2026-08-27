# View → route → source → permission matrix

Status: normative coverage matrix for the view inventory  
Rule: every inventory ID appears exactly once. Routes are logical and may be
materialized as `.html` by the static route manifest.

## Codes

Sources: `K` classified knowledge projection; `T` trace/relation index; `W`
work/governance projection; `E` evidence/report projection; `L` live control
plane; `U` user-local preference/draft; `A` administrative projection.  
Permissions: `P` public projection; `I` authenticated internal; `R` per-request
restricted; `Actor` assigned action authority; `Admin` administrative role.
Comma means the view supports multiple policy-selected projections, never that
they share an artifact.  
No-JS: `Full` complete read view/form export; `Read` complete information but
interactive enhancement absent; `Draft` local/exportable non-submitted form;
`Status` static status/recovery information.

Query grammar is the canonical safe schema from the route contract. `{id}` and
similar opaque values are percent-encoded typed IDs. All collection filters,
sort, page/cursor, `at`, locale, and selection are URL-preserved.

## System

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| SYS-01 | `/{locale}/` | K,W,E | P,I | Full |
| SYS-02 | `/{locale}/search?q=&filters=` | K,T,W,E | P,I,R | Full |
| SYS-03 | `/{locale}/commands` | K,W,U | P,I | Read |
| SYS-04 | `/activity` | L | I,R | Full |
| SYS-05 | `/settings/profile` | U,L | I | Full |
| SYS-06 | `/{locale}/help/{topic?}` | K | P | Full |
| SYS-07 | `/system/access-denied?return=` | L | P,I | Status |
| SYS-08 | `/system/not-found?ref=` or typed tombstone route | K,T,W | P,I,R | Status |
| SYS-09 | `/system/offline?return=` | U | P,I | Status |
| SYS-10 | `/system/maintenance` | L | P,I | Status |
| SYS-11 | canonical entity route + `?view=print|export` | K,W,E | P,I,R | Full |
| SYS-12 | `/{locale}/releases/{release?}` | K,E | P,I | Full |

## Knowledge and discovery

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| KN-01 | `/{locale}/docs` | K | P,I | Full |
| KN-02 | `/{locale}/docs/{universe}/modules` | K | P,I | Full |
| KN-03 | `/{locale}/docs/{universe}/modules/{id}` | K,T | P,I | Full |
| KN-04 | `/{locale}/docs/{universe}/namespaces[/{id}]` | K,T | P,I | Full |
| KN-05 | `/{locale}/docs/{universe}/types/{id}` | K,T | P,I | Full |
| KN-06 | `/{locale}/docs/{universe}/services/{id}` | K,T | P,I | Full |
| KN-07 | `/{locale}/docs/{universe}/members/{id}` | K,T | P,I | Full |
| KN-08 | `/{locale}/requirements/{id}` | K,T | P,I | Full |
| KN-09 | `/{locale}/records/{id}` | K,T | P,I,R | Full |
| KN-10 | `/{locale}/sources` | K | P,I | Full |
| KN-11 | `/{locale}/sources/{id}?at=` | K,E | P,I,R | Full |
| KN-12 | `/{locale}/diagrams/{id}` | K,T | P,I | Full |
| KN-13 | `/{locale}/ai-assertions/{id}` | K,T,E | P,I,R | Full |
| KN-14 | canonical entity + `/history` or `/versions/{kind}/{version}` | K,T,W,E | P,I,R | Full |
| KN-15 | `/{locale}/compare?left=&right=` | K,T | P,I,R | Full |
| KN-16 | canonical entity + `/backlinks` | T | P,I,R | Full |
| KN-17 | `/{locale}/coverage/orphans` | T | P,I | Full |

## Trace and provenance

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| TR-01 | `/{locale}/trace` | T,E | P,I | Full |
| TR-02 | `/{locale}/trace/entities/{id}?hops=&selected=` | T | P,I,R | Full table |
| TR-03 | `/{locale}/trace/provenance/{id}` | T,E | P,I,R | Full |
| TR-04 | `/{locale}/trace/coverage?source=&target=` | T,E | P,I | Full |
| TR-05 | `/work/dependencies/{id}?selected=` | T,W | I,R | Full |
| TR-06 | `/governance/provenance/{id}/graph` | T,W,E | I,R | Full |
| TR-07 | `/{locale}/trace/conflicts/{id}` | T,E | P,I,R | Full |
| TR-08 | canonical trace/entity route + `?at={kind}:{version}` | T,E | P,I,R | Full |

## Curation

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| CU-01 | `/curate` | K,L | I,R | Full |
| CU-02 | `/curate/items/{id}` | K,T,L | I,R,Actor | Full |
| CU-03 | `/curate/items/{id}/evidence` | K,E | I,R | Full |
| CU-04 | `/curate/items/{id}/proposal` | K,L,U | I,R,Actor | Draft |
| CU-05 | `/curate/conflicts/{id}` | K,T,L | I,R,Actor | Full |
| CU-06 | `/curate/batch?selection=` | K,L,U | I,Actor | Draft |
| CU-07 | `/curate/items/{id}/claim` | W,L | I,R,Actor | Full |
| CU-08 | `/curate/submissions/{id}/preview` | K,W,E,U | I,Actor | Full |
| CU-09 | `/curate/submissions/{id}/receipt` | L,E | I,R | Full |
| CU-10 | `/curate/archive` | K,W,E | I,R | Full |

## Review and feedback

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| RV-01 | canonical entity + `?panel=annotation&anchor=` | K,L,U | P,I,R | Draft |
| RV-02 | `/review/threads/{id}` | L,E | P,I,R | Full |
| RV-03 | `/review/requests/new?target=` | K,U,L | P,I,R | Draft |
| RV-04 | `/review/requests/{id}/preview` | U,L | P,I,R | Full |
| RV-05 | `/review/requests/{id}/receipt` | L,E | P,I,R | Full |
| RV-06 | `/review` | W,L | I,R | Full |
| RV-07 | `/review/protocols/{id}` | W,E | P,I,R | Full |
| RV-08 | `/review/findings[/{id}]` | W,E,L | I,R | Full |
| RV-09 | `/review/reviews/{id}` | W,E | I,R | Full |
| RV-10 | `/review/reviews/{id}/re-review?candidate=` | W,E,L | I,R,Actor | Full |
| RV-11 | `/{locale}/feedback/new?target=` | K,U,L | P | Draft |
| RV-12 | `/{locale}/feedback/{receipt}` | L,E | P | Full |

## Work and governance

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| GW-01 | `/work` | W,T | I,R | Full |
| GW-02 | `/work/items/{featureId}` | W,T,E | I,R | Full |
| GW-03 | `/work/items/{itemId}` | W,T,E | I,R | Full |
| GW-04 | `/work/items/{itemId}/claims/{claimId}` | W,E | I,R | Full |
| GW-05 | `/governance/decisions` | W | P,I,R | Full |
| GW-06 | `/governance/decisions/{id}` | W,T,E | P,I,R | Full |
| GW-07 | `/governance/provenance` | W,T | I,R | Full |
| GW-08 | `/governance/provenance/{id}` | W,T,E | I,R | Full |
| GW-09 | `/governance/acceptance` | W,E | I,R | Full |
| GW-10 | `/governance/acceptance/{id}` | W,T,E | I,R | Full |
| GW-11 | `/governance/checkpoints` | W,T,E | I,R | Full |
| GW-12 | `/governance/integration-reviews/{id}` | W,T,E,L | I,R,Actor | Full |
| GW-13 | `/governance/verdicts/{id}` | W,T,E | I,R | Full |
| GW-14 | `/evidence/runs/{id}` | E,T | I,R | Full |
| GW-15 | `/evidence/bundles/{id}` | E,T | I,R | Full |
| GW-16 | `/governance/audit?target=` | W,T,E | I,R | Full |
| GW-17 | `/governance/audit/events/{id}` | W,T,E | I,R | Full |
| GW-18 | `/governance/authorities` | W | I,R | Full |
| GW-19 | `/governance/registry/{kind?}` | W,A | I,R | Full |
| GW-20 | canonical entity + `/raw?at=` | K,W,E | I,R | Full |

## Reports

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| RP-01 | `/reports` | E | P,I,R | Full |
| RP-02 | `/reports/status/{id?}` | E,W | I,R | Full |
| RP-03 | `/reports/build/{id}` | E | P,I,R | Full |
| RP-04 | `/reports/extraction` | E | P,I | Full |
| RP-05 | `/reports/extraction/{id}/versions/{kind}/{version}` | E,K | P,I | Full |
| RP-06 | `/reports/traceability/{id}` | E,T | P,I,R | Full |
| RP-07 | `/reports/curation/{id}` | E,K | P,I,R | Full |
| RP-08 | `/reports/review/{id}` | E,W | I,R | Full |
| RP-09 | `/reports/validation/{id}` | E | I,R | Full |
| RP-10 | `/reports/campaign/{id}` | E,W,T | P,I,R | Full |
| RP-11 | `/reports/i18n/{id}` | E,A | P,I | Full |
| RP-12 | `/reports/performance/{id}` | E | P,I | Full |
| RP-13 | `/reports/accessibility/{id}` | E | P,I | Full |
| RP-14 | `/reports/security/{id}` | E | I,R | Full |
| RP-15 | `/reports/{type}/{id}/compare?left=&right=` | E | P,I,R | Full |

## Tickets

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| TK-01 | `/work/tickets` | W,T | I,R | Full |
| TK-02 | `/work/items/{id}` | W,T,E | I,R | Full |
| TK-03 | `/work/dependencies/{id?}` | W,T | I,R | Full |
| TK-04 | `/work/roadmaps/{id}` | W,T | I,R | Full |
| TK-05 | `/work/queries/new` or `/work/queries/{id}` | W,U | I,R | Full |
| TK-06 | `/work/changes/{id}/preview` | W,U,L | I,Actor | Full |
| TK-07 | `/work/conflicts/{id}` | W,L | I,R,Actor | Full |
| TK-08 | `/work/migration/compare?at=` | W,T,E | I,R | Full |

## AI and automation

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| AI-01 | canonical entity + `?panel=discuss` | K,W,U,L | I,R | Read |
| AI-02 | `/discuss/{id}` | U,L,E | I,R | Full transcript |
| AI-03 | `/discuss/{id}/context` | K,W,E,U | I,R | Full |
| AI-04 | `/discuss/{id}/proposal` | U,L,E | I,R,Actor | Draft |
| AI-05 | `/discuss/{id}/submission` | U,L,E | I,R,Actor | Full |
| AI-06 | `/automation/runs/{id}` | L,E | I,R | Full |
| AI-07 | `/context-assembly/{id}` | K,T,E | I,R | Full |
| AI-08 | `/vm/runs/{id}` | L,E | I,R | Full |

## Administration and localization

| ID | Route | Source | Permission | No-JS |
|---|---|---|---|---|
| AD-01 | `/admin/i18n/coverage` | A,E | I,Admin | Full |
| AD-02 | `/admin/i18n/queue` | A,L | I,Admin | Full |
| AD-03 | `/admin/i18n/segments/{id}` | A,L,E | I,Admin | Full |
| AD-04 | `/admin/i18n/glossary` | A | I,Admin | Full |
| AD-05 | `/admin/builds/{id}` | A,E,L | I,Admin | Full |
| AD-06 | `/admin/publications/{id}/preview` | A,E | I,Admin | Full |
| AD-07 | `/admin/registry/{kind}` | A,W | I,Admin | Full |
| AD-08 | `/admin/health` | A,L,E | I,Admin | Full |
| AD-09 | `/admin/notifications` | A,L | I,Admin | Full |

## Mechanical coverage gate

A generator reads the inventory and this matrix and fails on a missing or
duplicate ID, invalid route pattern, unknown source/permission/no-JS code,
unregistered query/fragment, missing state fixtures, or a route whose public
projection references internal/restricted manifests. The expected count is the
exact count of inventory table IDs, never a manually maintained constant.
