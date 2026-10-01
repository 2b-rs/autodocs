# 0033-03 — Review-request package/envelope v2 reconciliation

**Status:** Review-ready contract package; implementation result for Task
`0033-03`, not process/privacy/UX approval, runtime validation, trusted ingress,
queue migration, release authorization or Task Acceptance.

**Candidate base after prerequisite merge:**
`53a5c68d9c28c7177080f49056fc52d8be27d564`

**Process input:** `0033-02` substantive REF
`ac4b2579a52f4e6acc94873de6964e0aab059663`.

**Claim:** `TODO-zed-0033-03-20260819T065436Z-d9be66d964ba.md`.

## 1. Selected contract design

The historical mixed `review-request-package@v1` model is replaced for future
use by four distinct identities and three contract families:

| Identity/contract | Purpose | Explicit non-purpose |
|---|---|---|
| UUIDv7 `event_id` | One immutable intentional package version | Not concern, delivery, Issue, envelope or queue identity |
| `concern_key` | SHA-256 over exact target/category/rationale projection | Not NLP equivalence and excludes actor/transport/evidence |
| `package_sha256` | SHA-256 over exact canonical package bytes | Not recursively stored in package |
| Envelope/Issue/delivery/queue IDs | Separate transport/persistence attempts | Never overwrite event/concern history |
| `review-request-package@v2` | Closed credential-blind client claims | No transport/trust/receipt/server/route/writer/decision fields |
| `review-request-envelope@v1` | Approved adapter-produced GitHub evidence | JSON shape or `verified` flag cannot establish trust |
| `review-request-local-envelope@v1` | Exact self-declared local import | Never authenticated; later GitHub evidence is additive |

Formal Draft 2020-12 schema:
`docs/pipeline/review-request-package-v2.schema.json`.

Normative candidate prose:
`docs/pipeline/review-request-package-schema.md`.

## 2. Historical finding disposition

| Finding | V1 defect | Candidate correction | Implementation owner |
|---|---|---|---|
| `RRB-SCHEMA-001` | Open/coercive fields/types; client trust/server fields accepted | Closed object branches, formal schema, recursive reserved-field and semantic-security contract, field-addressed negatives | `0033-05`, `0033-08` |
| `RRB-IDENT-001` | Random event called deterministic; no vectors; confirmation/retry drift and contradictory duplicate keys | Real RFC 9562 UUIDv7 vector, immutable edit/retry rule, separate exact concern/package/attempt identities, canonical bytes/digests | `0033-05`, `0033-07`, `0033-10`, `0033-11` |
| `RRB-TRUST-001` | Client transport/bare actor stood in for trusted GitHub evidence | Credential-blind package and separate API/webhook/combined/local envelope families; no profiles enabled before approval | `0033-06`, `0033-08` |
| `RRB-PRIV-001` | Trust/actor retention conflated and contradicted done queue | Field classification references approved `PROC-*` choices; credentials forbidden; source-preserving migration/quarantine | `0033-07.02`, `0033-07.03` |

This Task closes the design gap only. Runtime findings remain open until their
named implementation/assurance Tasks pass.

## 3. Exact canonical profile and vectors

Profile `autodocs-canonical-json-nfc-lf@v1` requires UTF-8/no BOM,
duplicate-key rejection, NFC input, closed declared types, no floats,
lexicographically sorted ASCII keys, compact separators, preserved array order
and exactly one LF. Parse/recanonicalize is byte-identical.

Pinned RFC 9562 Appendix A vector:

- UUID: `017f22e2-79b0-7cc3-98c4-dc0c0c07398f`
- Unix milliseconds: `1645557742000`
- UTC: `2022-02-22T19:22:22.000Z`
- version `7`, RFC variant.

Tracked package vectors:

| Fixture | Event | Canonical bytes | Package SHA-256 |
|---|---|---:|---|
| `valid-github.json` | RFC Appendix A vector | 923 | `sha256:d96aa35239f18edfa7f03f79bde648979b451336dac820c2d97b33b8f38e60ab` |
| `valid-json-export.json` | `01a018cc-e3e0-7123-8000-0000075bcd15` | 847 | `sha256:e4ce6a5823941c4bd24407de89a273180c5a124e6747b24d2e3eee145558a0f1` |
| `valid-nojs-normalized.json` | `01a018cd-41a0-7234-8000-00003ade68b1` | 855 | `sha256:e89fe419817c3690614e030692b84330cf84883be998716ee2a0a9abf6646d64` |

`canonical-vectors.json` tracks exact package, concern-preimage and envelope
strings, byte sizes and digests. Reviewers never reconstruct them from this
table.

## 4. Target freshness and duplicate contract

Versioned target acceptance requires canonical prefix, version-ID hash8, full
SHA-256, authoritative version-store entry, current latest version, eligible
status and authoritative source URL to agree at lookup and under the atomic
queue reservation. Any mismatch is hard stale/ineligible; a version/full-hash
invariant breach is quarantined. Approved unversioned legacy relies on full
SHA-256 only; age is never freshness evidence.

One policy covers:

- same event/package/stable trust = exact retry;
- same event/different package = collision/tampering;
- separate delivery/Issue/envelope attempts linked to unchanged package;
- exact webhook replay only when delivery and raw-body digest both match;
- all nonterminal states included in active-concern uniqueness;
- terminal exact redelivery returns prior result;
- new terminal successor event follows approved recurrence;
- concurrent event/concern reservation plus target compare-and-set creates at
  most one item.

## 5. Trust profiles represented but disabled

The closed schema can represent:

1. `github-api-refetch-v1`;
2. `github-webhook-sha256-v1`;
3. `github-webhook-sha256+api-refetch-v1` (logical AND);
4. `local-import-v1` (always self-declared, never trusted).

Fixture manifest intentionally records:

```json
"approval_state":"candidate-not-approved",
"enabled_github_profiles":[]
```

`0033-04.01` selects exact enabled profiles, allowlists, actor-mismatch policy,
retention revision and no-JS normalization. Schema support is not activation.
PAT/header/signature/secret/session/network identifiers are absent from every
package/envelope fixture.

## 6. Compatibility and migration

Five explicit compatibility cases cover:

- resolvable v1 GitHub source requiring authoritative target plus new migration
  event;
- null-version v1 awaiting `PROC-0033-02-03` or rejection;
- malformed v1 actionable rejection;
- v1 client trust/session fields restricted quarantine;
- persisted request-shaped decision/terminal ambiguity quarantine.

No v1 object validates directly as v2. Migration preserves source bytes/digest,
removes untrusted transport/authentication claims, derives full target identity
only from authoritative stores, and never fabricates curator decision, apply,
publication or trusted actor. Structural queue migration remains `0033-07`;
privacy/disposal remains `0033-07.02`.

## 7. Requirement-to-evidence matrix

| `0033-03` requirement | Artifact/evidence |
|---|---|
| Proper UUIDv7 event ID separate from concern identity | Schema definitions; prose sections 2–3; RFC vector/test |
| Intentional edit vs exact retry | Prose section 3.1; canonical vectors; same-concern test |
| Canonical byte/digest vectors | `canonical-vectors.json`; canonical fixture test |
| Unified duplicate/replay/concurrency policy | Prose section 4; invalid matrix; dossier section 4 |
| Canonical/version/hash and unversioned staleness | Schema target oneOf; prose section 2.2; target negative cases |
| Client claim separated from trusted transport | Separate package/envelope/local-envelope defs and positives; reserved-field negatives |
| Webhook/API/both profile support with no caller verification | Schema envelope profile; prose section 5; empty enabled-profile manifest |
| Closed fields/types/lengths/counts/semver/timestamps | Draft 2020-12 schema; closure/semantic tests |
| URL, Unicode, control/injection and sensitive-field handling | Prose section 7; 28 negative cases; recursive scan test |
| Version negotiation/migration/quarantine | Prose section 8; five compatibility cases |
| Retention/redaction remains approval-bound | Prose section 9; `PROC-*` mapping; manifest candidate state |
| GitHub/JSON/no-JS examples | Three canonical positive envelopes |
| Requirement-to-test matrix | This table plus section 8 below |

## 8. Validation matrix

New contract test `_src/tests/test_review_request_package_v2_contract.py`
performs 11 deterministic tests:

1. all seven fixture JSON files are duplicate-free canonical UTF-8 with one LF
   (the NFD negative value is retained as negative data without pretending it
   is a valid package);
2. Draft 2020-12 identity and closed object definitions;
3. three positive envelope/package semantic checks;
4. RFC UUIDv7 time/version/variant vector;
5. exact concern/package/envelope bytes, sizes and SHA-256;
6. all 28 negative cases reach their intended rule;
7. no package claims transport/authority;
8. concern identity excludes actor/evidence/event/time/source while package
   identity changes;
9. five compatibility cases and source reachability;
10. manifest counts/candidate/disabled profile truthfulness;
11. historical v1 artifacts remain separate and available.

Focused regression must also run historical v1 package and baseline-audit tests,
proving additive design work did not rewrite historical evidence.

## 9. Review findings and open decisions

Independent read-only design reviews agreed on the package/envelope separation,
full SHA, UUIDv7 parsing, stable identities, hard-stale behavior, closed fields,
no caller trust, source-preserving compatibility and disabled profile gate.
Their main design alternatives were resolved as follows:

- concern key includes target identity, category and exact rationale but excludes
  evidence, actor, event/time and transport so supplementary evidence remains
  the same active concern;
- package limit is 32 KiB (not 16 KiB) to align the Task/architecture count-size
  boundary while rationale remains 4000 and evidence count 3;
- safe text allows inert HTML-/Markdown-like content subject to control/NFC/
  size rules and contextual encoding; semantic moderation quarantines malicious
  meaning rather than trusting a blacklist;
- GitHub machine package uses exact base64url bytes, not raw Markdown fences;
- full SHA is authoritative; historical hash8 remains only a cross-check inside
  existing version IDs.

Still unapproved: profile activation, legacy classes, self-declared/anonymous
intake, exact recurrence/duplicate choice, URL host/fetch policy, actor mismatch,
projections/results, clocks/controllers, abuse quotas/moderator role, Browser
Store/PAT mechanism and residual risks. These remain in the same
`PROC-0033-02-*` review suite.

## 10. Scope boundary

No historical v1 validator/fixture was changed. No production validator,
ingestion adapter, queue writer, browser script, store, record, report, GitHub
Issue, credential, approval or external state is modified by this contract
Task. Runtime implementation begins only after `0033-04.01` approval and under
its separately claimed Tasks.
