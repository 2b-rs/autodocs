# Website Review-Request Package and Envelope Contract — v2 candidate (`0033-03`)

**Status:** Review-ready contract candidate; **not approved and not a runtime
implementation claim**. The combined process/schema/privacy/UX suite must pass
`0033-04.01` before implementation Tasks consume it.

**Replaces for future use:** historical `review-request-package@v1`. V1 remains
compatibility input and defect evidence; it never validates as v2.

**Formal schema:**
[`review-request-package-v2.schema.json`](review-request-package-v2.schema.json)
(Draft 2020-12). Exact fixtures/vectors live under
`_src/tests/fixtures/review_request_v2/`.

**Process input:** [`website-review-flag.md`](website-review-flag.md). This
contract cannot change its request/decision, authority, rejected-no-apply,
privacy or external-controller boundaries.

## 1. Contract families and trust boundary

| Schema | Producer | Meaning | Authority boundary |
|---|---|---|---|
| `review-request-package@v2` | Browser/client or approved no-JS normalizer | Immutable, transport-neutral client-controlled request claims | Credential-blind; no verified identity, receipt, server time, route, writer or lifecycle decision |
| `review-request-envelope@v1` | Approved GitHub webhook/API adapter | Normalized trusted transport evidence bound to exact package bytes | Trust comes from the adapter capability and verification path, never from JSON fields alone |
| `review-request-local-envelope@v1` | Local import adapter | Exact canonical JSON import with self-declared assurance | Never verified; later GitHub transport creates a separate linked envelope |
| `review-request-concern@v1` | Deterministic projection | Exact active-concern identity preimage | Not a transport/event/queue identity and not semantic NLP equivalence |

A caller-supplied object containing `verified: true` is untrusted input. A
persisted envelope projection is audit evidence only unless it is loaded from
an authenticated protected store or independently reverified.

## 2. Client package v2

Closed shape (all objects reject additional properties):

```json
{
  "schema": "review-request-package@v2",
  "client": {
    "name": "autodocs-review-ui",
    "version": "2.0.0"
  },
  "event_id": "017f22e2-79b0-7cc3-98c4-dc0c0c07398f",
  "created_at": "2022-02-22T19:22:22.000Z",
  "concern_key": "sha256:<64 lowercase hex>",
  "target": {
    "binding": "versioned",
    "canonical_id": "AUTOSAR/AP/record/SWS_TSYNC_00123",
    "version_id": "AUTOSAR/AP/record/SWS_TSYNC_00123@rel:R25-11#ba7816bf",
    "content_sha256": "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    "status_snapshot": "valid/ai-decided",
    "source_url": "https://example.org/en/modules/tsync.html#SWS_TSYNC_00123"
  },
  "category": "factual-accuracy",
  "rationale": "The published statement needs a factual source review.",
  "evidence_refs": [],
  "actor_claim": {
    "kind": "self-declared",
    "display_name": "reader"
  }
}
```

Top-level keys are exactly those shown. In particular, the package cannot carry
`transport`, `trust`, `verified`, repository/Issue/delivery/receipt, server
timestamps, authoritative actor, queue/status/outcome/decision, route/writer,
credential/session/network or filesystem fields.

### 2.1 Required scalar constraints

- `client.name`: allowlisted producer identifier syntax, 1–64 characters.
- `client.version`: strict SemVer, 5–64 characters; never number/list/coercion.
- `event_id`: lowercase canonical RFC 9562 UUIDv7. Validator parses version,
  variant and 48-bit millisecond time; it must agree with `created_at` within
  the approved skew (candidate: ±5 minutes). UUID time is not target freshness.
- `created_at`: exact UTC millisecond form `YYYY-MM-DDTHH:MM:SS.sssZ`.
- SHA-256 values: `sha256:` plus 64 lowercase hex digits.
- `category`: `factual-accuracy`, `outdated-source`, `missing-context`,
  `ai-hallucination-suspected` or `other`.
- `rationale`: NFC, 3–4000 characters; no forbidden controls. Validation
  preserves bytes and never trims/coerces an accepted value.
- `evidence_refs`: 0–3 closed entries; kinds `url`, `citation`, `note`; at most
  one entry of each kind is a semantic rule; array order is preserved.
- `actor_claim`: `anonymous`, or `self-declared` with 2–80 character display
  name. There is no client `github_authenticated` value.
- canonical package size: at most 32,768 bytes including trailing LF.

HTML-like or Markdown-like user text is not authority and is never interpreted.
The schema blocks control characters; contextual output encoding/base64url
transport prevents injection. Abuse/security policy may quarantine malicious
meaning without pretending schema alone can classify intent. Errors/logs never
echo secret or malicious raw values.

### 2.2 Target binding

`target.binding` is exactly one of:

- `versioned`: non-null `version_id` required;
- `legacy-hash-only`: `version_id` must be null and the class must be explicitly
  approved by `PROC-0033-02-03` (schema validity alone does not enable it).

Semantic validation proves:

1. canonical ID parses and resolves through the authoritative project/kind
   registry;
2. version ID canonical prefix equals `canonical_id` byte-for-byte;
3. version-ID hash8 suffix equals the first eight hex digits of the submitted
   full SHA-256;
4. the authoritative version store binds that exact version to that exact full
   SHA-256;
5. current record/version/full hash/eligible status/source URL match at lookup
   and again under the queue-write reservation.

Any material mismatch is hard stale/ineligible. A matching version with a
mismatching full digest is an invariant breach/possible hash8 collision and is
quarantined. The historical “both hash and version must mismatch” soft rule is
removed. For approved legacy hash-only targets, any full-hash mismatch is hard
stale. Age, UUID time and page build time never substitute for live lookup.

## 3. Canonical bytes and digest profile

Profile name: `autodocs-canonical-json-nfc-lf@v1`.

1. Reject over-limit input before parsing.
2. UTF-8 only, no BOM; reject malformed Unicode and duplicate object keys.
3. Only contract-declared JSON types; package numbers are forbidden. Envelope
   integers, where used, remain in exact I-JSON range.
4. Keys and strings must already be NFC; reject rather than silently normalize.
5. Reject non-finite/floating values.
6. Serialize with sorted object keys, compact `,`/`:` separators,
   `ensure_ascii=false`; arrays retain contract order.
7. Append exactly one LF; no other leading/trailing bytes.
8. Parse and reserialize must be byte-identical.
9. Digest exact tracked/canonical bytes, never a prose reconstruction.

All contract keys are ASCII, so Python Unicode code-point ordering and JCS
UTF-16 key ordering coincide for this closed schema. Future non-ASCII property
names require a versioned canonicalization review.

`package_sha256` is SHA-256 over exact canonical package bytes. It belongs in
an envelope, not recursively in the package.

### 3.1 Event and concern identities

- `event_id` identifies one intentional immutable package version.
- Ambiguous network retry and later transfer of an exact export reuse the same
  package bytes/event/concern key.
- Any intentional edit mints a new event and `created_at`.
- Evidence-only edits mint a new event/package digest but retain the same
  concern key.
- Rationale/category/target identity edits recompute the concern key.

Concern preimage is exact canonical JSON plus LF:

```json
{
  "schema": "review-request-concern@v1",
  "target": {
    "binding": "versioned|legacy-hash-only",
    "canonical_id": "...",
    "version_id": "...|null",
    "content_sha256": "sha256:..."
  },
  "category": "...",
  "rationale": "..."
}
```

Excluded: event/time/client, actor claim, evidence, status snapshot, source URL
and every envelope field. Thus supplementary evidence or another requester does
not create a parallel exact concern. Paraphrases remain distinct and are
handled by quotas/curator linkage; `PROC-0033-02-06` must approve this exact-key
limitation.

## 4. Duplicate, retry, replay and concurrency

| Observation | Required result |
|---|---|
| Same event + package digest + stable trust binding | Exact retry; return prior immutable result |
| Same event, different package digest | Collision/tampering; reject or quarantine before write |
| Same event/package via another delivery/Issue/import | Separate linked envelope/attempt, never another request item |
| Same webhook delivery ID + same raw-body digest | Idempotent redelivery |
| Same delivery ID + different raw-body digest | Replay collision/tampering; quarantine |
| New event + same concern while any leading item is active | Return privacy-safe leading request; no second item |
| Different concern on same target | May create a distinct item subject to approved quotas |
| Exact retry after terminal close | Return terminal prior result; never reopen |
| New event after terminal result | Apply approved recurrence and link predecessor; never rewrite terminal history |
| Concurrent same-event/same-concern attempts | Atomically reserve event, replay and active concern keys; exactly one may create an item |
| Target changes between lookup and commit | Compare-and-set fails; no item/history/temp artifact |

Active means `open/queued`, `claimed`, `proposed` and accepted-awaiting-apply/
close. Transport attempt/envelope/Issue/delivery/queue identities are distinct.

## 5. Trusted GitHub envelope

`review-request-envelope@v1` is produced only by an approved adapter and embeds
the unchanged package plus digest. Shared closed fields include:

- `profile`, envelope UUIDv7, server `received_at`;
- exact package and `package_sha256`;
- verification method/policy/check time (non-secret key identifier only where
  applicable);
- numeric-as-string repository/owner/installation, Issue and actor IDs plus
  observed names/URLs/times;
- exact Issue body digest and package extraction/normalization method;
- profile-specific attempt/replay evidence;
- `stable_binding_sha256` over repository/installation/Issue/actor/body/package
  identity;
- approved retention-policy reference.

No envelope retains PAT, bearer/header/cookie, webhook signature value/secret,
IP, browser fingerprint, session or local path.

Supported candidate profiles (none operationally enabled before
`0033-04.01`):

1. `github-api-refetch-v1`: authenticated API refetch, repository/installation
   allowlist, exact Issue/body/actor/package binding and revision replay check.
2. `github-webhook-sha256-v1`: HMAC-SHA-256 over exact raw HTTP bytes before
   JSON parse; retain delivery/body digest, not signature/header/secret.
3. `github-webhook-sha256+api-refetch-v1`: logical **AND**; both observations
   must agree exactly. It is not fallback/OR.

Package extraction methods:

- `embedded-base64url-v2`: exactly one fixed HTML-comment machine block with
  one unpadded base64url line; decoded bytes are exact canonical package bytes.
  General Markdown/fence scraping is forbidden.
- `github-issue-form-v1`: exact allowlisted headings/fields are normalized into
  a new package by the trusted no-JS adapter; duplicate/unknown headings fail.

API/webhook adapter invocation and protected trust store—not `profile` or
`verified` JSON—establish trust.

## 6. Local import envelope

`review-request-local-envelope@v1` records `local-import-v1`, exact package,
digest, source kind/media type/digest/size and `assurance=self-declared`.

- No filename/path is retained.
- Source bytes equal canonical package bytes and digest.
- Operator identity does not upgrade requester assurance.
- Later GitHub transport appends a separate envelope bound to unchanged package
  bytes; it never mutates/replaces local history.

## 7. Closed fields, URLs, text and sensitive data

Every object and branch has `additionalProperties=false`; there are no arbitrary
metadata/extensions maps. Future fields require a schema version.

Semantic validation recursively rejects reserved/server-owned field names at
any depth, including `trust`, `verified`, authoritative actor, server/received
time, receipt, repository/installation/Issue/delivery, queue/status/outcome/
decision, claim/decide actor, route/writer, authorization/token/credential/
password/secret/private key/cookie/session/IP/fingerprint/user-agent/local path
and signature fields.

It also scans values for high-confidence credential material (GitHub/AWS tokens,
bearer/cookie/header, PEM private key, credentialed URL) without echoing the
value. Schema cannot reliably detect all secrets or malicious meaning.

URLs require parsed absolute HTTPS, no userinfo/backslash/disallowed port, no
localhost/private/link-local/loopback/multicast/unspecified targets and no
control/whitespace. Target URL uses an approved publication host and nonempty
record fragment; evidence URL is reference-only and never automatically
fetched. IDNA, DNS/redirect/SSRF checks are semantic and repeat at every fetch
hop if a later approved feature ever fetches.

## 8. Compatibility and migration

V1 never passes v2 schema directly. A source-preserving migration record may
create v2 only when:

1. v1 contains only documented client fields and passes strict new text/URL
   constraints;
2. v1 `transport` is retained only as an untrusted historical claim and removed
   from v2;
3. every actor becomes self-declared; GitHub authority comes only from a new
   verified envelope;
4. canonical target resolves authoritatively;
5. one exact full SHA-256/version snapshot matches v1 canonical/version/hash8;
6. null version belongs to an approved legacy class;
7. a new valid migration event is minted once under an atomic source-digest
   map if the old UUID is invalid; old ID remains restricted provenance only;
8. v2 concern/package bytes and digests are recomputed.

| Legacy case | Disposition |
|---|---|
| Fully resolvable, no extra/sensitive fields | Additive normalization record; source bytes unchanged |
| Unknown schema major | Actionable unsupported-version rejection |
| Client-authored trust/server/session/credential fields | Restricted quarantine, never silently drop-and-accept |
| Hash8 has zero/multiple full-hash matches | Ambiguous quarantine |
| Null version without approved class | Ineligible/actionable rejection |
| Non-NFC/coercion/meaning guess needed | Quarantine |
| Persisted request-time `decided_by` or ambiguous applied/rejected terminal | `legacy-semantic-ambiguous`; no inferred authority/outcome |

Structural queue migration belongs to `0033-07`; privacy/disposal to
`0033-07.02`. Migration never fabricates curator acceptance, apply, publication
or authenticated requester identity.

## 9. Retention and approval boundary

Schema classifies fields but does not approve clocks. Implementations bind the
exact later-approved policy revision from `website-review-flag.md`:

- legacy unversioned: `PROC-0033-02-03`;
- concern/recurrence: `-06`;
- trust/mismatch: `-07`;
- moderation/quarantine: `-09`;
- URL/fetch: `-10`;
- abuse/replay: `-11`;
- projections/results: `-12`;
- clocks/holds/backups/disposal: `-13`;
- public GitHub/controller: `-14`;
- local collection/credential: `-15`;
- existing data migration/history limits: `-16`.

The candidate 30/90/180-day periods are not effective until the approval gate
accepts exact versions.

## 10. JSON Schema versus semantic validator

Draft 2020-12 enforces closed shapes, required fields, types, enums, lexical
patterns, lengths/counts and package/envelope families. It cannot by itself
establish:

- raw byte size/UTF-8/BOM/duplicate keys/depth/token bounds;
- canonical bytes, NFC, digest equality or UUID timestamp relationship;
- registry/version-store/live-target consistency;
- parsed URL/IDNA/DNS/allowlist/private-address/redirect behavior;
- webhook HMAC/API trust and protected adapter provenance;
- body/package/actor/repository binding or replay/concurrency/CAS;
- secret/malicious/abusive/sensitive meaning;
- output encoding, retention, holds, redaction/disposal or no-side-effect
  behavior.

Runtime validation must not coerce, trim, remove unknown fields, apply schema
defaults or mutate input. Every error is stable, field-addressed and safe.

## 11. Required test matrix

The fixture manifest and `0033-03-schema-reconciliation.md` map exact cases.
Minimum categories:

- valid versioned GitHub, local JSON and no-JS-normalized examples;
- RFC 9562 UUIDv7 Appendix A vector, canonical concern/package/envelope bytes,
  counts and SHA-256;
- every required field/type/enum/length/count/additional-property boundary;
- integer event ID diagnostics, wrong UUID version/variant/time/case;
- canonical ID/version/full-hash/live-target/status/source mismatches;
- null-version approved/unapproved paths and no age fallback;
- exact retry, edit, envelope attempt, webhook replay, active duplicate,
  terminal recurrence and concurrent reservation;
- recursive reserved/sensitive fields and credential-shaped values;
- Unicode NFC/control/bidi, JSON/Markdown/HTML/log/path/URL attacks with safe
  diagnostics/output behavior;
- webhook/API/combined/local envelope positives and missing signature, wrong
  scope, body/package mismatch, profile disagreement and untrusted-envelope
  negatives;
- v1 resolvable, unsupported, sensitive, ambiguous hash/null-version and
  persisted semantic-ambiguity dispositions;
- zero production record/version/queue/history/report mutation for every
  rejection/quarantine profile except its separately approved audit channel.

## 12. Open decisions

This contract deliberately does not activate:

- any GitHub profile;
- legacy hash-only classes;
- self-declared/anonymous intake policy;
- exact concern/recurrence/duplicate policy beyond the candidate;
- URL host/private-target/fetch policy;
- actor mismatch handling;
- public projection/receipt channel;
- retention clocks/controller wording;
- abuse telemetry/quotas/moderator authority;
- Browser Store/PAT mechanism.

They remain visible in `PROC-0033-02-01`–`17` for the exact same
`0033-04.01` review suite. A green contract test is not approval.
