# Controlled agent/profile feedback lifecycle

**Status:** proposed architecture for Feature `0046`; non-operative. This contract does not authorize profile mutation, approval, publication, Supervisor reload, or relaxation of `DEC-0044-029`.

## Lifecycle and trust boundaries

1. **Submit.** A bounded UX captures feedback, target and observed baseline. The ingress validates shape and authentication but treats free text as untrusted.
2. **Record.** An append-only journal creates or resolves an idempotent `agent-profile-feedback@v1` record. Subsequent events reference its stable ID and prior-event digest.
3. **Analyze.** An isolated analyzer classifies the feedback and emits `agent-profile-proposal@v1`: exact source baseline, proposed patch, rationale, evidence, privacy/publication impact, tests, conflicts and rollback plan. It has no mutation authority.
4. **Decide.** An authorized human reviews a rendered diff and records approve/reject/revise in `agent-profile-decision@v1`. Authorization and baseline freshness are rechecked at decision and promotion time.
5. **Promote source.** A compare-and-swap promotion applies only a current approved proposal to the authoritative source and emits immutable candidate/ref and digests. `agents.json` schema, descriptor references, role/capability policies and provenance validate before the candidate is eligible.
6. **Regenerate privately.** Deterministic generation produces private provider/runtime profiles, full prompts and a manifest in an isolated candidate. Size, schema and whole-population validation complete before promotion.
7. **Project publicly.** A separate allow-list transform produces redacted public descriptions. In the invoking item-owned source worktree it stages `output/publish-export/tree` and `output/publish-export/files_to_export.txt`; the tree is a fresh standalone Git repository on `publish-main`. A retained dry-run manifest binds source ref, export commit and file digests.
8. **Promote independently.** Authorized promotion moves the private candidate into agent-inbox/provider configuration and atomically publishes the public candidate to `2b-rs/autodocs`/GitHub Pages. Generated public output never becomes source-history `main`.
9. **Activate and prove.** Supervisor consumes the exact private published revision, reloads/restarts, and writes an activation/health receipt. The publisher records remote commit and public reachability/content proof. A completion receipt links both outcomes to the approved source candidate.
10. **Supersede or roll back.** Any failure or later approved change appends a supersession/rollback event; source, private activation and public publication are reconciled independently to named revisions.

## State machine

`received → classified → proposed → {rejected | revision-requested | approved} → source-candidate → validated → {private-promoted, public-promoted} → activated → complete`

Every transition is compare-and-swap guarded and idempotent. `complete` requires `private-promoted`, `public-promoted`, Supervisor exact-revision activation, health proof, and public promotion receipt. Partial states remain explicit and recoverable; they never imply completion.

## Records and minimum bindings

| Record | Required binding |
|---|---|
| `agent-profile-feedback@v1` | feedback ID, target, observed baseline, attribution/anonymous policy result, visibility, input digest, idempotency key |
| `agent-profile-proposal@v1` | feedback IDs, exact authoritative baseline, patch/diff digest, classification, rationale, evidence, risks, public/private effects, validation and rollback plan |
| `agent-profile-decision@v1` | proposal digest, authorized human identity/authority, approve/reject/revise, revision if any, timestamp |
| `agent-profile-source-candidate@v1` | decision, compare-and-swap baseline, candidate ref/tree, schema and policy validation digests |
| `agent-profile-private-manifest@v1` | source candidate, generator/config versions, per-profile digests/sizes, allowlisted destinations |
| `agent-profile-public-manifest@v1` | source candidate, redaction policy, source worktree identity, staging paths, export commit, file digests, leakage-test result |
| `agent-profile-activation-receipt@v1` | private revision requested/loaded, provider/config revision, Supervisor epoch, health proof |
| `agent-profile-publication-receipt@v1` | export commit, remote `2b-rs/autodocs` commit, GitHub Pages proof, atomic-promotion outcome |
| `agent-profile-completion@v1` | approved source candidate plus exact private activation and public publication receipts |
| `agent-profile-supersession@v1` | prior/current revisions, cause, authority, rollback/promote results, unresolved divergence |

## Security, privacy and authority invariants

- Feedback text is data, never an instruction to the analyzer or executor.
- AI may analyze and propose; only a separately authorized human may approve/revise/reject; only the promotion component may mutate authoritative state.
- Approval is proposal- and baseline-specific, single-use and replay protected.
- Public projection is allow-list based. A deny-list alone is insufficient. Raw sources, prompts, provider profiles, internal policy, credentials, private identities and restricted feedback are forbidden exports.
- Redaction/retention events preserve integrity and audit metadata while minimizing retained personal content.
- Anonymous input, if later authorized, cannot exercise approval or promotion authority.
- `DEC-0044-029` remains a hard compatibility boundary: neither feedback nor proposal records use agent-memory storage.

## Cross-item decision and review gate

Before the first operative mutation that establishes or changes any of these gate scopes, a conforming `decision-record@v1` and supporting review by a Management-instantiated Architect distinct from the Implementer must be reachable:

- who may submit anonymously and what attribution/retention applies;
- who may approve/revise/reject and the required independence;
- authoritative source and compare-and-swap promotion semantics;
- shared role/capability descriptor changes affecting multiple agents or future Tasks;
- public/private projection boundary and publication eligibility;
- private promotion, Supervisor activation/health, rollback and completion gates;
- any interaction with `DEC-0044-029` or agent-memory routing.

The decision record names affected agents, role/capability consumers, future Task routing/execution contracts, both repositories, publication and activation gates. Planning, fixtures and non-operative schemas may proceed before that gate. Operative mutation may not.

## Failure and recovery rules

- **Stale baseline/conflict:** reject promotion; retain proposal and conflict evidence; require rebase plus a new decision.
- **Duplicate/replay:** return the original logical result or a typed conflict; never create a second promotion.
- **Partial regeneration/export:** quarantine all candidate outputs; do not promote a mixed set.
- **Private promoted/public failed:** runtime may remain on the prior active revision unless an explicit policy authorizes asymmetric activation; reconcile through retry or rollback and never emit completion.
- **Public promoted/private failed:** retain the public receipt, roll public projection back or complete private recovery under recorded authority; never claim activation.
- **Supervisor restart:** replay the durable desired-revision request; compare requested, published and loaded revisions; emit one idempotent receipt.
- **Health failure:** restore named last-known-good private revision and record health/rollback outcome.
- **Publication rebuild:** `output/publish-export/tree` is destructively rebuilt only inside the exact item-owned source worktree by the established publisher; retain the pre-promotion manifest/digests outside the rebuilt tree.

## Validation floor

Schema/property tests cover all records and transition guards. Integration tests cover approval/promotion authority, generator and public-export boundaries, provider promotion and Supervisor exact-revision activation. End-to-end fixtures cover both receipts, GitHub Pages projection, restart reconciliation and rollback. Negative whole-population leakage checks scan every public asset. Tests include every case enumerated in `REQ-0046-16` and the requirements dossier’s negative matrix.
