# Curator Decision Protocol — Process Definition (`review-package@v1`, `review.js`)

Status: Normative process specification for Task **0036-01** (Feature `0036` — Review-Prozess-Dokumentation: Illustriert, verlinkt, mehrsprachig).  
Authoritative implementation reference: `review.js`, `_src/tools/review_ingest.py`, and `_src/tools/workflow_lifecycle.py`.

---

## 1. Context & Purpose

The **Curator Decision Protocol** governs how direct validation decisions (approval or rejection of requirement text and ambiguous extraction candidates) are captured, packaged client-side in the browser via `review.js`, and submitted for integration into specification records.

Unlike the *Flag-for-Review* reader request flow (`review-request-package@v1` / Feature `0021`/`0035`), which initiates a triage queue item (`discovered -> queued`), the Curator Decision Protocol represents an **already-decided outcome** (`outcome: accept | reject`) made by a human reviewer or curator against an active review panel.

---

## 2. Item & Package Schemas

### 2.1 Individual Decision Item (`Decision`)
Every decision captured by an inline review panel contains the following normative fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `string` | Target requirement or element identifier (e.g., `SWS_Diag_00012`). |
| `flag_id` | `string` | Associated review flag identifier (e.g., `RF_SWS_Diag_00012_01`). |
| `text_hash` | `string` | SHA-256 (or cryptographic digest) of the requirement text at review time. |
| `kind` | `string` | Element type; defaults to `"requirement_text"`. |
| `outcome` | `string` | Decided verdict: `"accept"` (Freigabe) or `"reject"` (Ablehnung). |
| `decided_by` | `string` | Name or handle of the reviewer (GitHub login or self-declared name). |
| `identity` | `string` | Identity trust mode: `"github_authenticated"` or `"self_declared"`. |
| `decided_at` | `string` | ISO 8601 UTC timestamp of the decision. |
| `rationale` | `string` | Mandatory substantive explanation justifying the decision. |
| `decision_basis` | `object` / `string` | Contextual evidence, source PDF reference, or extraction candidate metadata. |

### 2.2 Review Package (`review-package@v1`)
Multiple decision items are aggregated into an atomic envelope stored locally or submitted upstream:

```json
{
  "schema": "review-package@v1",
  "identity": "github_authenticated",
  "submitted_at": "2026-08-16T17:10:00.000Z",
  "decisions": [
    {
      "id": "SWS_Diag_00012",
      "flag_id": "RF_SWS_Diag_00012_01",
      "text_hash": "a1b2c3d4...",
      "kind": "requirement_text",
      "outcome": "accept",
      "decided_by": "octocat",
      "identity": "github_authenticated",
      "decided_at": "2026-08-16T17:09:30.000Z",
      "rationale": "Matches section 4.2.1 of AUTOSAR specification.",
      "decision_basis": { "page": 42, "source_version": "R20-11" }
    }
  ]
}
```

---

## 3. Storage & Client-Side State Management

Client-side state is strictly isolated to the visitor's browser using `localStorage`:

- **Decision Buffer Store (`ara-review-package-v1`)**: Stores an array of serialised decision items. Decided items are immediately reflected in the UI (badges hidden, panel marked `.is-done`, drawer count badge incremented).
- **GitHub Token Store (`ara-review-github-token-v1`)**: Stores an optional personal access token with issue-write permissions.
- **Identity Store (`ara-review-identity`)**: Stores self-declared reviewer names when GitHub authentication is not active.

---

## 4. Transport & Submission Mechanisms

### 4.1 GitHub Issue Submission (Authenticated Batch Submit)
When connected with a valid GitHub token (`activeToken()`):
1. The client verifies the token via `GET https://api.github.com/user` to resolve `user.login`.
2. A single GitHub issue is opened against the configured target repository (`meta[name="review-github-repo"]`, default `2b-rs/autodocs`).
3. Title: `Requirement review package (<count>)`.
4. Body: Markdown fenced code block containing the formatted `review-package@v1` JSON payload.
5. Upon successful creation (HTTP 201), the local package buffer (`ara-review-package-v1`) is cleared.

### 4.2 JSON File Download (Unauthenticated Fallback Export)
When unauthenticated, the reviewer exports `ara-review-<ISO-TIMESTAMP>.json` with `identity: "self_declared"` and a prominent warning:
- *"Unauthenticated fallback: the stated identity is self-declared, so the acceptance rate may be lower."*

---

## 5. Lifecycle Semantics & Consistency with `workflow-lifecycle.md`

### 5.1 Direct Transition (`discovered -> applied`)
In the unified lifecycle (`docs/pipeline/workflow-lifecycle.md`):
- Unlike defect reports and flags that transition through `discovered -> queued -> claimed -> proposed -> accepted`, curator decisions captured via `review.js` represent **direct determinations**.
- When ingested by `_src/tools/review_ingest.py`, a verified `review-package@v1` payload applies decisions directly to record files and closes matching open flags without creating a preliminary queue item (`discovered -> applied` bypass).

### 5.2 Role Alignment with `roles.md`
- **Reviewer / Curator (`curator`)**: Authority to emit terminal accept/reject decisions.
- **Ingestion Tool (`tool`)**: Validates text hash, schema structure, and authorization before updating the repository.

---

## 6. Traceability & Non-Bypass Guarantees

1. **Hash Verification**: `text_hash` ensures decisions cannot be applied to drifted requirement text.
2. **Immutable Audit Trail**: Ingested packages record `decided_by`, `decided_at`, and `rationale` directly in the specification record's history metadata.
3. **No Direct DOM Mutation**: `review.js` cannot mutate backend files directly; all modifications pass through verified git-controlled ingestion scripts.
