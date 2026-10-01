# Provenance Contract

## Identity and immutability

`typed-reference@v1` uses canonical `<kind>:<identifier>` URIs and binds the URI scheme to `kind`. Events, runs, and findings use UUIDv7. Within one authority, an ID maps to exactly one canonical payload: an identical payload is an idempotent replay; a different payload with the same ID is a collision and must be rejected. Events are append-only; correction uses a later `supersedes` or `invalidated-by` event.

## Relation table

| Relation | Source kinds | Target kinds | Cardinality/replay |
|---|---|---|---|
| `detected-during` | `finding` | `run`, `campaign` | 1 source to one or more targets; duplicate canonical edges are replay |
| `reported-by` | `finding` | `issue`, `curation-item` | 1 source to one or more targets; duplicate canonical edges are replay |
| `remediates` | `commit`, `issue` | `finding`, `issue` | 1 source to one or more targets; duplicate canonical edges are replay |
| `implements` | `commit`, `artifact`, `record-version` | `issue`, `criterion`, `decision` | 1 source to one or more targets; duplicate canonical edges are replay |
| `verifies` | `run`, `evidence` | `criterion`, `issue`, `artifact`, `record-version` | 1 source to one or more targets; duplicate canonical edges are replay |
| `triggered` | `issue`, `finding`, `decision` | `run`, `campaign` | 1 source to one or more targets; duplicate canonical edges are replay |
| `produced-by` | `artifact`, `artifact-set`, `record-version`, `evidence` | `run`, `campaign` | 1 source to one or more targets; duplicate canonical edges are replay |
| `derived-from` | `artifact`, `artifact-set`, `record-version`, `evidence` | `artifact`, `artifact-set`, `record-version`, `evidence` | 1 source to one or more targets; duplicate canonical edges are replay |
| `invalidated-by` | `artifact`, `artifact-set`, `record-version`, `evidence`, `finding` | `finding`, `decision`, `run` | 1 source to one or more targets; duplicate canonical edges are replay |
| `regenerated-by` | `artifact`, `artifact-set`, `record-version` | `run`, `campaign` | 1 source to one or more targets; duplicate canonical edges are replay |
| `supersedes` | `issue`, `finding`, `decision`, `artifact`, `artifact-set`, `record-version`, `evidence` | `issue`, `finding`, `decision`, `artifact`, `artifact-set`, `record-version`, `evidence` | 1 source to one or more targets; duplicate canonical edges are replay |
| `published-as` | `artifact`, `artifact-set`, `record-version` | `artifact`, `evidence` | 1 source to one or more targets; duplicate canonical edges are replay |
| `decides` | `decision` | `issue`, `finding`, `criterion` | 1 source to one or more targets; duplicate canonical edges are replay |
| `blocks` | `issue`, `finding`, `decision` | `issue`, `criterion`, `run`, `campaign` | 1 source to one or more targets; duplicate canonical edges are replay |

Self-edges are rejected except a `record-version derived-from record-version` edge where source and target URIs differ. Consumers enforce acyclicity for `derived-from`, `supersedes`, and `blocks`.

## Privacy and redaction

Every object is `public`, `internal`, or `restricted` and records `synthetic`, `development-test`, `production`, or `assessment` where environment applies. Restricted references require an explicit `redacted` flag; restricted findings require `redaction_reason`. Public projection omits restricted URIs, digests, evidence, and free text rather than replacing them with fabricated values. Downgrading classification requires a new decision/event and never mutates history.

## Evidence

Evidence is a typed immutable reference to a committed path/range, immutable digest, reachable commit, or policy-approved durable external record. Mutable generated views and uncommitted local output are not evidence.

## Examples and invalid coverage

`provenance/fixtures/valid/provenance-chain.json` contains run, finding, all endpoint kinds, and all relation examples. `provenance/fixtures/invalid/` contains isolated UUID/redaction failures plus one URI-kind mismatch for every endpoint kind, one endpoint-compatibility failure for every relation, and invalid classification/environment values.
