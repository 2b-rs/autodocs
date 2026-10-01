# Historical website review-request baseline (`0033-01`, v1)

Status: **reproduced historical defect baseline; not release approval**

Baseline schema: `review-request-historical-baseline-manifest@v1`

Report schema: `review-request-historical-baseline-report@v1`

This document freezes the evidence inherited from Feature `0021` before
Feature `0033` changes the process, package, ingestion, queue, generated-page,
or browser behavior. A passing baseline case means that the named historical
defect was reproduced. It does **not** mean the desired behavior is correct.
The corresponding forward assertion remains pending until its named Feature
`0033` owner closes it.

Machine-readable sources and evidence:

- manifest: [`../../_src/tests/fixtures/review_request_baseline/manifest-v1.json`](../../_src/tests/fixtures/review_request_baseline/manifest-v1.json)
- audit tool: [`../../_src/tools/review_request_baseline_audit.py`](../../_src/tools/review_request_baseline_audit.py)
- focused tests: [`../../_src/tests/test_review_request_baseline_audit.py`](../../_src/tests/test_review_request_baseline_audit.py)
- retained run: [`../../logs/review-request-baseline/0033-01-baseline-v1.json`](../../logs/review-request-baseline/0033-01-baseline-v1.json)

## Reproduction contract

Run from the repository root:

```sh
/opt/homebrew/bin/python3 _src/tools/review_request_baseline_audit.py \
  --output logs/review-request-baseline/0033-01-baseline-v1.json
```

The v1 evidence run used CPython 3.14.6, Git 2.50.1 (Apple Git-155), and
Node 26.7.0 on macOS arm64. The report records the full version strings, exact
commands, exit codes, bounded output summaries, immutable commit/tree IDs,
SHA-256 for every pinned artifact and exported tar stream, case expectations
and observations, and before/after mutation snapshots.

The exact historical suite imports `lxml`, but the modern Python interpreter
needed for the historical `X | None` annotations does not have that optional
module. The audit therefore adds a temporary **fail-on-use** `lxml` import shim
inside the extracted test root. Its SHA-256 is recorded in the report. The
shim only permits import; every attribute access raises. The 25 tests pass
without touching it, which itself demonstrates that these tests do not cover
the HTML parser/comparator dependency.

### Isolation and mutation guards

The audit never imports historical code from the live checkout:

1. `git show` verifies every pinned blob hash.
2. `git archive` extracts selected paths from exact refs into a
   `TemporaryDirectory` outside the repository.
3. Historical validator and ingestion modules run in child interpreters.
4. Before ingestion, `curation_flags.QUEUE`, `OPEN_DIR`, `CLAIMED_DIR`, and
   `DONE_DIR` are redirected to a second temporary root.
5. The generated queue file is read and normalized only inside that root.
6. Git porcelain status and byte-level snapshots of every real
   `_src/spec/*-queue` tree are compared before and after all probes.
7. Full child output is retained only in the JSON report; console output is a
   bounded verdict and report digest.

The retained v1 run reports 8/8 observations, 25/25 historical tests, unchanged
Git status, and unchanged real curation/review queue snapshots. No record,
version, page model, generated HTML, user output, or root `run.sh` operation is
part of the audit.

## Historical committed refs

| Historical task | Commit | Tree | Evidence disposition |
|---|---|---|---|
| `0021-01` | `42b0b4a16192589c407c415f231f565685be2024` | `ae17a12a44c3419c9faae0bc3568ca6f534c39ca` | Process draft and related committed blobs are direct provenance, not acceptance. |
| `0021-02` | `3cfdbe72b097b971ef9fd9d4757eed37bef93e1b` | `bab1a2914191dbf3fe9cac05ca27df96d3640154` | Schema prose, validator, fixtures, and tests are direct provenance. |
| `0021-03` | `a03be1e6735f940da1e6e62ba9a408077e6143cb` | `ebcaf9d2bc9fb2c017063b9f9ad0f52f2dc0b7bc` | Ingestion adapter and tests are direct provenance. |
| `0021-04` | `25eef65b6ab36f5e7e5e57ad3392c8116ec182d9` | `c014d75c8a2e6b3a031b8b420aa5e3b8afb0781c` | UX document is direct provenance and explicitly says `Status: drafted`. |
| `0021-05` | `62f638bfd9ff956e417ef617dbcab160448b8406` | `4dc2d7d3cdedafde0c873288bfbb688917d6860f` | Browser/rendering implementation and broad generated tree are direct provenance. |
| `0021-05` bookkeeping | `28d6de7526453554d6e0000a9ddb58490d8ec5cd` | `71b7ab40e8e82da00586c4f45f18faf8452667e7` | Changes `TODO.md` only; it adds no implementation or validation evidence. |

The manifest pins SHA-256 values for 22 critical blobs, including the process,
schema, UX, validator, ingestion/queue adapters, tests/checker, page renderer,
client script, project manifest, a real generated page, and bookkeeping.

## `local-*` provenance and cumulative evidence

The labels `local-20260815-0021-06`, `local-20260815-0021-07`, and
`local-20260815-0021-08` do not resolve as commits, tags, trees, blobs, or other
Git objects. Their authoritative disposition is therefore:

> **unrecoverable / no independent evidence credit**

Unreachable checkpoints currently preserved in this object database provide
context, but they are mixed working-tree snapshots, are garbage-collectable,
and are not portable clone evidence. They do not retroactively make the local
labels valid refs or authenticate the claimed test/release results.

| Claim | Closest contextual checkpoint/tree | What can be learned | Evidence credit |
|---|---|---|---|
| `0021-06` / `local-20260815-0021-06` | commit `6c42ddd683ff0cb2d2ff96e2b939587732acb3c5`; tree `d0de741a1325fdf2546fdc4152e6c4d2ee6dd89e` | Mixed snapshot contains history/report implementation and claim text while authoritative markers disagree. | None for Task completion or validation. |
| `0021-07` / `local-20260815-0021-07` | commit `7bf41f77a373d6dddfd84624c14cfe37d6f5844b`; tree `58c0ee078a30fe8352ebaf7ab9c3e2c41c5079c8` | Mixed snapshot contains prose claims for report build, focused tests, all-language generation, and validation. | None for a reproducible end-to-end gate. |
| `0021-08` / `local-20260815-0021-08` | commit `2a37cd9d75619c0186c7b330f4c52e63c070125e`; tree `3da5119524d3f35925f0c10f440bdb8403ebbeee` | Closest cumulative content includes guidance, residual-limit wording, and `ship as-is`; prerequisite markers and timestamps contradict orderly closure. | None for release authorization. |
| Feature closure context | commit `d01b4cde377d71d2ef8d0592b4aae91748408b2a`; tree `96e290f6c911a572e66e856824e1947ee204ca35` | First mixed checkpoint with Feature `0021` moved into `DONE.md`; implementation/guidance match the preceding mixed snapshot. | Context only. |

Some byte-identical implementation blobs later became reachable in unrelated
commits `f6aab79cb52ce12d127c4ddde7e129c022eec326` (tree
`d09c54d56445df9bcdd80cbe69e3cbc754b9f9da`) and
`eb843d0c907451619f0ec70d6e065c2dfed15cb2` (tree
`72fd759ec77ac39ec0c779029db9f9841bd973e1`). Those later cumulative trees can
support code inspection; they cannot authenticate the earlier test run,
release decision, or Task-specific closure chronology.

## Executable defect observations

| Finding | Historical ref | Frozen defective observation | Pending fixed behavior owner |
|---|---|---|---|
| `RRB-SCHEMA-001` | `3cfdbe72…` | A package with list/object-valued schema, status, URL, rationale, actor/evidence values plus caller-authored `trust`, `received_at`, `server_timestamp`, and `session_id` returns zero validation errors. | `0033-03`, `0033-05`, `0033-08` |
| `RRB-SCHEMA-002` | `3cfdbe72…` | Integer `request_id` reaches `re.Pattern.match()` and raises `TypeError`. | `0033-05`, `0033-08` |
| `RRB-INGEST-001` | `a03be1e6…` | `ingest(package, apply=True)` succeeds when both current hash and version are omitted and writes an isolated queue item. | `0033-06`, `0033-08`, `0033-14` |
| `RRB-QUEUE-001` | `a03be1e6…` | The raw item omits top-level canonical linkage; normalization derives the target from the request ID, defaults `origin=curator` and `status=proposed`, retains unsupported `item_kind=review-request`, and fails `is_conformant()`. | `0033-07`, `0033-08`, `0033-09`, `0033-14` |
| `RRB-META-001` | `62f638bf…` | Real page `classes/cl_ara_core_Future_420ba8.html`, record `SWS_CORE_00322`, embeds bare ID, null version/hash, `valid/unmigrated`, and empty source URL. | `0033-09`, `0033-10`, `0033-13` |
| `RRB-NOJS-001` | `62f638bf…` | The same real page has JavaScript trigger buttons but no `<noscript>` or non-JavaScript review intake link. | `0033-04`, `0033-12`, `0033-13` |
| `RRB-BROWSER-001` | `62f638bf…` | Coverage is one 390×844 WebKit export path with synthetic complete metadata, pre-seeded identity, click-only operation, and inspection of `.review-request-data` rather than downloaded bytes. | `0033-10`–`0033-13` |
| `RRB-VALID-001` | `62f638bf…` | All 25 exact focused tests pass while the seven observations above remain true. | `0033-08`, `0033-13`, `0033-15`, `0033-16` |

## Original `0021` criterion-to-evidence matrix

Historical `[x]` markers are administrative history only. “Partial” below
means a committed artifact exists, not that the criterion was accepted.

| Original task / criterion | Direct and contrary evidence | Finding IDs | Disposition |
|---|---|---|---|
| `0021-01`: exhaustive eligibility/exclusions, role authority, review-vs-curation routing, valid-record re-review, stale/duplicate/abuse behavior, and no website mutation | `42b0b4a1:docs/pipeline/website-review-flag.md` says any published record, leaves item-kind and retention questions open, supplies no abuse policy, routes requests identically to decision-bearing curation requests, and relies on role prose rather than authentication. The no-browser-record-write rule is stated. | `RRB-PROC-001`, `RRB-AUTH-001`, `RRB-PRIV-001` | Partial contract; criterion not met. |
| `0021-01` DoD: internal consistency and committed testable normative requirements | The document calls itself drafted, claims consistency despite unresolved choices, and conflicts with rejection/closure and retention behavior later visible in code. | `RRB-PROC-001`, `RRB-AUTH-001` | Not met. |
| `0021-02`: complete package fields; deterministic identity; authoritative transport trust; unambiguous duplicate, canonicalization, stale, sensitive-field, and retention rules | `3cfdbe72` adds fields and prose, but event identity is random while described as deterministic; canonical serialization is disconnected from identity; duplicate/stale rules conflict across layers; caller-reserved fields are not prohibited; retention contradicts completed storage. | `RRB-SCHEMA-001`, `RRB-IDENT-001`, `RRB-TRUST-001`, `RRB-PRIV-001` | Partial schema draft; criterion not met. |
| `0021-02` DoD: executable schema, valid/invalid examples, deterministic fixtures, and transport-neutral semantics | Handwritten validator and three fixtures exist. The adversarial package passes, integer ID crashes, URL/status/version/evidence types are unchecked, and no pinned deterministic identity vector exists. | `RRB-SCHEMA-001`, `RRB-SCHEMA-002`, `RRB-IDENT-001` | Executable baseline exists but DoD not met. |
| `0021-03`: validate, resolve live target, derive trusted identity from transport, de-duplicate, preserve lossless mapping, write conformant open item, and leave no rejected side effects | `a03be1e6:_src/tools/review_request_ingest.py` accepts optional caller-supplied live values, treats a bare actor argument as authority, scans only open items, writes then patches, and loses/misplaces canonical/origin/lifecycle linkage. Rejected paths are tested only against the temporary unit-test queue. | `RRB-INGEST-001`, `RRB-TRUST-001`, `RRB-QUEUE-001`, `RRB-QUEUE-002` | Core boundary bypassable and output nonconformant. |
| `0021-03` DoD: happy/unknown/stale/malformed/duplicate/category/attribution/spoof/mapping tests plus schema/lifecycle conformance | Tests cover 12 selected cases but no unknown live record, internal lookup, claimed/concurrent duplicates, writer failure, real-store mutation matrix, conformance assertion, or governed lifecycle. “Lossless” checks only nested selected fields. | `RRB-QUEUE-001`, `RRB-QUEUE-002`, `RRB-VALID-001` | Test count green; DoD not met. |
| `0021-04`: placement, fields, disclosure, consent, confirmation, exact state semantics, keyboard/focus, mobile, and no-JS | `25eef65b:docs/pipeline/review-request-ux.md` describes these states but remains `Status: drafted`; it promises controls on invalid published pages, a static prefilled no-JS URL, page-age staleness, and transport outcomes unsupported by implementation. | `RRB-UX-001`, `RRB-IDENT-001`, `RRB-NOJS-001` | Draft, not approved or implementable as written. |
| `0021-04` DoD: approved authoritative contract and executable standard/valid/stale/duplicate/failure scenarios | No approval record exists. The five scenarios are prose; later browser coverage exercises only synthetic JSON export. | `RRB-UX-001`, `RRB-BROWSER-001`, `RRB-PROV-001` | Not met. |
| `0021-05`: real generated action binds canonical/version/hash/status/source, validates locally, emits schema package, uses GitHub/JSON without mutation, and distinguishes exported/submitted/queued | Action/dialog code exists, but the real page probe proves missing target metadata. The GitHub receipt is discarded, confirmation and transport can mint different IDs, and no queue result channel exists. | `RRB-META-001`, `RRB-IDENT-001`, `RRB-UX-001` | Synthetic path implemented; production criterion not met. |
| `0021-05` DoD: desktop/mobile/browser, keyboard/focus/errors/cancel/transport/no-JS, deterministic generated HTML | Only one WebKit mobile export test exists; it pre-seeds identity and reads server payload. No desktop/other engine, downloaded bytes, GitHub receipt/failure, focus trap, no-JS, stale/duplicate, or cancellation breadth is tested. Commit changes 4,503 files, preventing a review-scoped determinism conclusion. | `RRB-BROWSER-001`, `RRB-NOJS-001`, `RRB-VALID-001`, `RRB-REGEN-001` | Not met despite 25 green focused tests. |
| `0021-06`: request discoverability and traceability in record/history/reports, lifecycle/status/target/actor privacy, durable queue and receipt links, and no false queue state | Closest mixed tree renders selected state and report fields. The queue “link” is a filesystem path in code text, `existing_request_url` is empty, no transport receipt is indexed, and wrong canonical mapping undermines target linkage. | `RRB-TRACE-001`, `RRB-QUEUE-001`, `RRB-PRIV-001` | Contextual implementation only; no independent completion credit. |
| `0021-06` DoD: real open/accepted/rejected generated/report assertions, rejected-pre-ingest no-write proof, link and DOM validation | Terminal report tests inject handcrafted items rather than driving lifecycle. Rejected completion normalizes as applied, and no retained Task-specific run or ref exists. | `RRB-TRACE-001`, `RRB-AUTH-001`, `RRB-PROV-001` | Not reproducibly met. |
| `0021-07`: end-to-end record → browser → validated ingestion → queue → proposal → human accept/reject → governed apply/close, with anti-bypass negatives | The closest cumulative tests are isolated package, ingestion, rendering, normalization/report, and export-only browser checks. There is no authenticated lifecycle, real live lookup, accepted/rejected branch, or record immutability proof. | `RRB-INGEST-001`, `RRB-TRUST-001`, `RRB-AUTH-001`, `RRB-VALID-001` | No end-to-end fixture. |
| `0021-07` DoD: automated suite/validation reports, resolved findings, reproducible traceability | Mixed claim prose says reports, focused tests, all-language generation, and validation passed; there is no task-specific committed report. Broad generated state cannot isolate the feature. | `RRB-VALID-001`, `RRB-REGEN-001`, `RRB-PROV-001` | No independent evidence credit. |
| `0021-08`: submit/triage/decide/follow guidance, authority-safe reports, and security/privacy/process limitations | Closest mixed tree adds guidance and four limitations. Guidance names a nonexistent `review_request_ingest.py --apply` CLI/GitHub-body path; privacy/retention and authenticated authority remain contradictory; reports inherit wrong linkage. | `RRB-OPS-001`, `RRB-PRIV-001`, `RRB-TRACE-001` | Guidance exists only as mixed cumulative context and is operationally inaccurate. |
| `0021-08` DoD: full green evidence, committed feature artifacts, explicit release decision and residual follow-ups | Local label is not an object. `ship as-is; no blocking residual items` conflicts with visible live-lookup, trust, conformance, production metadata, no-JS, lifecycle, and test gaps. The residual wording mentions identity strength, self-declared identity, triage latency, and export state but omits the blockers. | `RRB-PROV-001`, `RRB-RELEASE-001`, `RRB-VALID-001` | Release statement revoked; DoD not met. |

## Stable finding register and forward gates

| Finding ID | Historical defect | Forward tasks that must turn it into a passing assertion |
|---|---|---|
| `RRB-PROC-001` | Incomplete/contradictory process, eligibility, abuse, routing, closure, and retention contract. | `0033-02`, `0033-04.01`, `0033-07.04` |
| `RRB-SCHEMA-001` | Permissive types, unknown fields, and reserved trust/server metadata. | `0033-03`, `0033-05`, `0033-08` |
| `RRB-SCHEMA-002` | Uncaught non-string request-ID crash. | `0033-05`, `0033-08` |
| `RRB-IDENT-001` | Inconsistent event identity, idempotency, canonicalization, duplicate, retry, and stale rules. | `0033-03`, `0033-04`, `0033-10`, `0033-11` |
| `RRB-INGEST-001` | Optional live-target verification permits applying without lookup. | `0033-06`, `0033-08`, `0033-14` |
| `RRB-TRUST-001` | Bare actor argument substitutes for a verified, body-bound transport envelope. | `0033-03`, `0033-06`, `0033-08`, `0033-14` |
| `RRB-QUEUE-001` | Missing/wrong canonical linkage, origin, status, kind, and conformance. | `0033-07`, `0033-08`, `0033-09`, `0033-14` |
| `RRB-QUEUE-002` | Non-atomic post-write patch and incomplete duplicate/race handling. | `0033-07`, `0033-08` |
| `RRB-UX-001` | Draft-only transport, failure, focus, responsive, and state behavior. | `0033-04`, `0033-10`, `0033-11`, `0033-12` |
| `RRB-META-001` | Null/bare production target metadata. | `0033-09`, `0033-10`, `0033-13` |
| `RRB-NOJS-001` | Inert no-JavaScript experience. | `0033-04`, `0033-12`, `0033-13` |
| `RRB-BROWSER-001` | Synthetic single-engine/mobile/export-only coverage and wrong payload observation point. | `0033-10`, `0033-11`, `0033-12`, `0033-13` |
| `RRB-TRACE-001` | Missing durable public queue/receipt trace and synthetic terminal-state evidence. | `0033-07`, `0033-11`, `0033-14` |
| `RRB-AUTH-001` | No authenticated lifecycle boundary; rejected completion can normalize as applied. | `0033-02`, `0033-07.01`, `0033-08`, `0033-14` |
| `RRB-PRIV-001` | Retention/deletion contradiction and absent policy enforcement across projections/stores. | `0033-02`, `0033-03`, `0033-07.02`, `0033-07.03`, `0033-15.01` |
| `RRB-OPS-001` | Guidance names an intake CLI/flow that does not exist. | `0033-15.01` |
| `RRB-VALID-001` | Green focused tests fail to exercise production and anti-bypass acceptance. | `0033-08`, `0033-13`, `0033-15`, `0033-16` |
| `RRB-REGEN-001` | Broad 4,503-file regeneration lacks a clean review/determinism boundary. | `0033-13`, `0033-15`, `0033-16` |
| `RRB-PROV-001` | `local-*` labels have no object; mixed checkpoints have no independent Task evidence credit. | `0033-15`, `0033-15.02`, `0033-16`, `0033-16.01` |
| `RRB-RELEASE-001` | Unsupported `ship as-is` / no-blocker release statement. | `0033-04.01`, `0033-07.03`, `0033-15.01`, `0033-15.02`, `0033-16`, `0033-16.01` |

Later Tasks may refine a finding into more granular test IDs, but they must retain
this ID as the historical trace key. A Task must not mark one of these findings
closed merely because the v1 baseline continues to reproduce it; closure needs
the Task's stated fixed-behavior gate and exact candidate evidence.
