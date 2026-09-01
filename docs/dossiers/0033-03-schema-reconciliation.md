# 0033-03 — review-request-package@v2 / envelope reconciliation (Class R candidate)

**Class:** R (reconstructed proposal). Not operative. Not `docs/pipeline/`
content. May only become Class O through `0033-04.01` approval.

**Status:** review-ready, unapproved, awaiting `0033-04.01`.

**Task:** `0033-03`. **Chain:** `chain-0033-chakotay`.

**Base pin:** `main@3736170586e85047ab68691f0596689610688d9c`.

**Process input:** `0033-02` Class R candidate,
`docs/dossiers/0033-02-process-reconciliation.md`, REF `99fdc4a2b`, this branch.

**Baseline findings addressed:** `RRB-SCHEMA-001`, `RRB-IDENT-001`,
`RRB-TRUST-001` (interface impact), `RRB-PRIV-001`.

**Informed by (Class E, cited only, never merged):** historical substantive
commit `7c21351cfa` (`docs/pipeline/review-request-package-schema.md` and
`docs/pipeline/review-request-package-v2.schema.json` at that ref). This
document and its accompanying fixtures under
`_src/tests/fixtures/review_request_v2/` are a fresh reconstruction: field
names and identity concepts are informed by the historical defect analysis
(random `request_id` called deterministic, three incompatible duplicate
rules, null-version staleness gap), but the schema below, its exact vectors,
and the contract tests are authored fresh against the current baseline.

---

## 1. Selected identity and contract design

Four distinct identities replace the historical single mixed `request_id`:

| Identity | Purpose | Explicit non-purpose |
|---|---|---|
| `event_id` (RFC 9562 UUIDv7) | One immutable, time-ordered package version | Not a concern key, not delivery/Issue/envelope identity |
| `concern_key` (SHA-256 over canonical target/category/rationale projection) | Deduplicates same-concern submissions | Not NLP similarity; excludes actor, transport, evidence, timestamps |
| `package_sha256` (SHA-256 over canonical package bytes) | Detects tamper/collision on retry | Never itself stored inside the package it hashes |
| envelope/Issue/delivery IDs | Separate transport attempts | Never overwrite `event_id`/`concern_key` history |

Three contract families:

1. **`review-request-package@v2`** — the closed, credential-blind client
   claim. Candidate formal schema:
   `_src/tests/fixtures/review_request_v2/review-request-package-v2.schema.candidate.json`
   (Class R; landing an approved version to `docs/pipeline/` is
   `0033-04.01`'s exclusive act, per architect scope review §2/§6).
2. **`review-request-envelope@v1`** — the trusted adapter-produced GitHub
   evidence wrapper. Presence of this envelope, not a client-supplied
   `verified` field, is what establishes trust.
3. **`review-request-local-envelope@v1`** — self-declared local/no-JS import.
   Never authenticated; later GitHub evidence is additive, never assumed.

## 2. Canonicalization profile and pinned vectors

Profile `autodocs-canonical-json-nfc-lf@v1`: UTF-8, no BOM, reject duplicate
keys, NFC-normalized strings, closed declared field set (no
`additionalProperties`), no floating-point numbers, object keys sorted
lexicographically by UTF-8 byte value, compact separators (`,`/`:`, no
whitespace), array order preserved as authored, exactly one trailing LF.
Parse → recanonicalize must be byte-identical.

Pinned vectors, computed and verified executable
(`_src/tests/test_review_request_package_v2_contract.py::TestCanonicalVectors`):

| Vector | Canonical byte length | Digest |
|---|---:|---|
| `valid-package-v2-01` (full package) | 254 | `sha256:533a20625205590aedd935f46b9af42be4f6fb6d124aa1e0c1a24479a85d7683` |
| `concern-key-preimage-01` (target/category/rationale only) | 150 | `sha256:fe305d2299e75649199c024d37803ae793825947d7131910130e132891787230` |
| RFC 9562 Appendix A vector | — | `017f22e2-79b0-7cc3-98c4-dc0c0c07398f`, version 7, RFC variant |

The concern-key preimage vector deliberately omits `event_id` and every
trust/actor/evidence field, closing `RRB-IDENT-001`'s "canonical
serialization disconnected from identity/deduplication" gap by construction:
the same concern always hashes to the same `concern_key` regardless of which
transport attempt or retry produced it.

## 3. Duplicate, replay, and concurrency policy

One policy, not three, covers every case named in `0033-03`'s acceptance
criteria (proven exhaustively over the finite nonterminal/terminal state
partition, see §5 below and the executable tests):

- **same `event_id` + identical canonical `package_sha256`** = exact retry,
  idempotent — return the prior result, never re-process;
- **same `event_id` + different `package_sha256`** = collision or tampering,
  refused, logged to the restricted abuse channel (`0033-02` §5);
- **different `event_id`, same `concern_key`, both nonterminal** = the later
  one is `superseded` and linked to the earlier active request;
- **different `event_id`, same `concern_key`, earlier is terminal** = the
  later one proceeds independently — a terminal decision never blocks a fresh
  submission for the same concern, because circumstances may have changed;
- **exact webhook redelivery** (same delivery ID and raw-body digest) = no-op,
  return prior result;
- **distinct transport attempts for the same event** (retry via a different
  channel) = linked to the same `event_id`, never treated as a new concern.

Active-uniqueness therefore holds the invariant: **at most one nonterminal
request per `concern_key` at any time.** This is verified as a set/enumeration
property, not just asserted in prose — see §5.

## 4. Target freshness (staleness) rule

`target_version_id` is bound to `target_canonical_id` **and** a content hash.
Authoritative current-version lookup at decision time determines staleness;
age is never used as a staleness signal (closing `RRB-IDENT-001`'s
"null-version records could never become hard-stale" defect). For versioned
targets, a mismatch between the request's bound version hash and the current
authoritative version is hard-stale. For unversioned/legacy targets (no
version dimension exists), staleness is determined by full-content-hash
comparison only, never by elapsed time.

## 5. Set/invariant evidence (AE-5)

- **Invariant:** across all nonterminal (`open`, `claimed`) requests sharing a
  `concern_key`, at most one is active; any additional nonterminal request for
  the same concern is `superseded`.
- **Enumeration boundary:** the finite state set from the `0033-02` process
  candidate §4.1 (`open`, `claimed`, `applied`, `rejected`, `refused`,
  `quarantined`, `stale`, `superseded`), partitioned exhaustively and
  disjointly into nonterminal vs. terminal.
- **Executed evidence:** `_src/tests/test_review_request_package_v2_contract.py`
  class `TestDuplicateAndSetInvariant`, 4 tests, exercising: exhaustive/disjoint
  state partition; two nonterminal same-concern requests collapsing to one
  active; two different-concern requests both remaining active; a terminal
  same-concern request not blocking a new active one. Actual executed case
  count: 4 tests / 4 assertions on the invariant, run in this environment
  (`python3 -m pytest _src/tests/test_review_request_package_v2_contract.py -q`
  → 13 passed).

## 6. Trust profiles represented but disabled

The candidate schema can represent four trust profiles
(`github-api-refetch-v1`, `github-webhook-sha256-v1`,
`github-webhook-sha256+api-refetch-v1`, `local-import-v1`), but the fixture
manifest declares `"approval_state":"candidate-not-approved"` and
`"enabled_github_profiles":[]`. Representing a profile in the schema is not
activating it — `0033-04.01` selects exact enabled profiles, allowlists, and
actor-mismatch policy. No package or envelope fixture contains a PAT, header,
signature, secret, or session identifier (enforced by the forbidden-field
check in every contract test).

## 7. Compatibility and migration

Five distinct dispositions, each with a named fixture case
(`_src/tests/fixtures/review_request_v2/compatibility-cases.json`,
`TestCompatibilityCases`):

1. resolvable historical `v1` export → migrate to `v2`, minting a fresh
   `event_id`, preserving the `v1` payload as source-preserving evidence;
2. `v1` export whose target no longer resolves → quarantine with an
   actionable rejection, never silently dropped;
3. already-persisted malformed legacy queue item → quarantine with an
   actionable rejection;
4. a future, unrecognized package `kind` → reject as unsupported version;
5. exact same-`event_id` retry → idempotent, return the prior result (§3).

## 8. Falsification and adjacent-case evidence (AE-3/AE-4)

This is net-new candidate design work with no prior operative behavior to
regress against — there is no pre-change baseline for a contract that has
never been operative (§0 note in the test module). AE-3's red/green-on-two-
baselines form therefore does not apply in its literal sense; what is
provided instead is the falsification set the candidate itself must reject,
exercised as executable evidence:

- `TestInvalidCasesRejected` — 5 distinct adjacent invalid cases (additional
  field, server-owned field, malformed UUID, missing required target,
  forbidden credential field), each asserted to violate for its stated
  reason. All 5 pass (i.e., are correctly rejected) against the candidate
  validator.
- `TestValidFixturesConform` — the 3 valid fixtures (GitHub-trusted,
  JSON-export, no-JS/local) each conform with zero violations, confirming the
  validator does not over-reject legitimate shapes.

## 9. Requirement-to-artifact matrix

| `0033-03` acceptance criterion (from `TODO.md`) | Evidence |
|---|---|
| RFC 9562 UUIDv7 event/request ID + deterministic concern key from canonical bytes | §1, §2 |
| edits mint new event; retry reuses same event ID; canonical byte/digest vectors | §2 |
| one duplicate policy across retry/collision/linked-attempt/replay/active-state cases | §3, §5 |
| `target_version_id` bound to `target_canonical_id` + content hash; hash-only staleness for unversioned; no age-based claims | §4 |
| separate client package vs. trusted GitHub/local envelope, including JSON-export/later-transfer | §1, §6 |
| supported GitHub trust profiles, `0033-04.01` selects | §6 |
| allowed fields, sensitive/server-owned fields, timestamps, semver, URL rules, retention/redaction | schema `properties`/`not` block in the candidate schema; retention deferred to `0033-02` §6 |
| version negotiation, migration/quarantine/rejection for legacy exports and malformed persisted items | §7 |

## 10. Scope statement

This Task's entire Class R deliverable is this dossier plus
`_src/tests/fixtures/review_request_v2/**` and
`_src/tests/test_review_request_package_v2_contract.py`. No `docs/pipeline/**`
path is touched; landing an approved schema there is `0033-04.01`'s and a
later Task's act.

## 11. Validation performed

- `python3 -m pytest _src/tests/test_review_request_package_v2_contract.py -q`
  → **13 passed**, this environment, this commit.
- Manual cross-check: every `0033-03` acceptance-criterion clause in current
  `TODO.md` (line 1733–1737) maps to a section above (§9 matrix).
- `git diff --name-only main...chain-0033-chakotay` (checked after this
  commit): no path under `docs/pipeline/**` or any governance file.
- Not run: `_src/validate.py` (no generated-tree source changed by this Task).

## 12. Provenance

Requested by dispatch briefing (Dispatcher `chakotay`, atomic AWARD
`1787970210735-b3950909`, thread `0033-chain`), executed under claim
`TODO-Chakotay-Paris-0033-chain-20260830T113000Z.md`,
owner_token `agent:chakotay-paris:0033-chain:20260830T113000Z`. Authored
2026-08-30 against `main@3736170586e85047ab68691f0596689610688d9c`.
