# Flag-for-Review Request Protocol — Process Definition (`review-request-package@v1`, `review_request.js`)

Status: Normative process specification for Task **0036-02** (Feature `0036` — Review-Prozess-Dokumentation: Illustriert, verlinkt, mehrsprachig).  
Consolidates and supersedes `docs/pipeline/website-review-flag.md` and `docs/pipeline/review-request-package-schema.md` with Feature `0035` storage isolation and defect root cause insights.  
Authoritative implementation reference: `review_request.js`, `_src/tools/review_request_package.py`, and `_src/tools/review_request_ingest.py`.

---

## 1. Context & Objectives

The **Flag-for-Review Request Protocol** governs how website visitors and external consumers report inaccuracies, outdated references, missing context, or suspected AI hallucinations against published specification records (including records in `valid/*` state).

Unlike the **Curator Decision Protocol** (`review.js` / `review-package@v1`), which captures authoritative accept/reject determinations made by qualified curators and applies them directly (`discovered -> applied`), the Flag-for-Review flow initiates an asynchronous triage request:

$$\text{discovered} \longrightarrow \text{queued} \longrightarrow \text{claimed} \longrightarrow \text{proposed} \longrightarrow \text{accepted} \longrightarrow \text{applied}$$

No browser client, unauthenticated reader, or AI agent has the authority to mutate specification records directly through this protocol.

---

## 2. Package Schema (`review-request-package@v1`)

A submitted review request envelope contains the following normative fields validated by `_src/tools/review_request_package.py`:

| Field | Type | Description |
| :--- | :--- | :--- |
| `schema` | `string` | Must be `"review-request-package@v1"`. |
| `client_schema_version` | `string` | Format version of the client emitter (e.g., `"1.0"`). |
| `request_id` | `string` | Unique UUIDv7 identifier prefixed with `review-request:` (regex: `^review-request:[0-9a-f-]{36}$`). |
| `target_canonical_id` | `string` | Canonical identifier of the target requirement (e.g., `SWS_Diag_00012`). |
| `target_version_id` | `string` | Specific version identifier of the record at request time. |
| `target_content_hash` | `string` | 8-character hex prefix (`^[0-9a-f]{8}$`) of the requirement content digest. |
| `target_status_snapshot`| `string` | Status of the record when viewed (e.g., `draft`, `valid/reviewed`). |
| `source_url` | `string` | URL or relative page path where the flag was raised. |
| `category` | `string` | Enumerated classification: `"factual-accuracy"`, `"outdated-source"`, `"missing-context"`, `"ai-hallucination-suspected"`, or `"other"`. |
| `rationale` | `string` | Substantive user explanation (minimum 10 characters, maximum 4000 characters). |
| `actor_claim` | `object` | Reviewer identity payload (`{ "identity": "github_authenticated" \| "self_declared", "name": "..." }`). |
| `created_at` | `string` | ISO 8601 UTC timestamp. |
| `transport` | `string` | Submission channel: `"github_issue"` or `"json_export"`. |
| `evidence_links` | `array` | Optional list of external URLs citing supporting evidence. |

---

## 3. Storage Architecture & Isolation Boundaries (Feature 0035)

Feature `0035` resolved critical storage conflicts by establishing explicit boundaries between the two browser widgets:

```
+-------------------------------------------------------------------------------+
|                             BROWSER LOCALSTORAGE                              |
+-------------------------------------------------------------------------------+
|  SHARED IDENTITY & AUTHENTICATION STATE (Safe Cross-Widget Reuse)             |
|  - "ara-review-github-token-v1": GitHub Personal Access Token with repo scope  |
|  - "ara-review-identity": Self-declared nickname / handle (cleanName, >= 2 ch)|
+-------------------------------------------------------------------------------+
|  ISOLATED WIDGET DATA STORES                                                  |
|  - "ara-review-package-v1": Exclusively used by review.js (Curator Drawer)    |
|  - review_request.js: Single-shot immediate modal (Zero persistent store)    |
+-------------------------------------------------------------------------------+
```

1. **Storage Isolation**:
   - `review.js` requires persistent local storage (`ara-review-package-v1`) to accumulate a multi-item batch of curator decisions across navigation.
   - `review_request.js` is an immediate, single-shot request dialog. It does **not** persist unsubmitted request drafts in `localStorage`, eliminating state collisions with the curator drawer.
2. **Safe Credential & Identity Reuse**:
   - Both widgets share `ara-review-github-token-v1` so that a user authenticating via GitHub once remains authenticated across both curation and flag-for-review actions.
   - Both widgets share `ara-review-identity` to avoid prompting for a reviewer nickname multiple times in the same session.

---

## 4. Root Cause Analysis & Hardening of the Submit Defect (Feature 0035)

### 4.1 Defect Root Cause
During Feature `0033`/`0035` investigation, review request submissions intermittently failed at the ingestion boundary. The root cause analysis identified three failure modes:
1. **Unescaped JSON in Markdown Fences**: Browser-generated payloads containing raw quotes or backslashes in the `rationale` field were improperly interpolated into GitHub issue Markdown blocks, causing JSON parse errors during webhook ingestion.
2. **Missing Ingest Target Verification**: When a requirement record was updated between page build time and request submission, the `target_content_hash` mismatched, causing silent rejection without actionable client feedback.
3. **Payload Structure Drift**: Differences between client-side field naming (`actor_claim` vs `decided_by`) and ingestion expectations.

### 4.2 Applied Hardening
- **Client JSON Serialization**: `review_request.js` now encapsulates payloads using explicit `JSON.stringify()` formatting inside standardized ` ```json ` blocks.
- **Strict Ingestion Verification (`review_request_ingest.py`)**: The server-side ingestion handler performs structural schema checks, canonical ID resolution, hash drift warnings, and deduplication against open curation flags.
- **State Feedback**: `review_request.js` exposes clear state banners (`.review-request-state.is-error` / `.is-success`) indicating submission progress, GitHub rate limits, or verification rejections.

---

## 5. Non-Bypass & Lifecycle Guarantees

1. **Mandatory Queue Entry (`discovered -> queued`)**:
   - Ingestion creates an immutable flag file under `_src/spec/curation-queue/` (or `_src/spec/review-queue/`).
   - The status of the target record in `_src/spec/records/` is untouched.
2. **AI Agent Triage (`queued -> claimed -> proposed`)**:
   - AI agents claim open requests, investigate referenced evidence, and format structured proposals. Agents cannot mark proposals as accepted.
3. **Human Curator Authority (`proposed -> accepted -> applied`)**:
   - Only a human curator can approve a proposal, merge the change into git, and invoke `curation_flags.complete_flag()` to transition the item to `applied`.
