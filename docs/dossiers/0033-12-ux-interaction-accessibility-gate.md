# 0033-12 Evidence Dossier: Keyboard, Focus, Dialog, Responsive/Mobile, Live-Announcement, and No-JavaScript Behavior

- **Task**: `0033-12`
- **Assignee**: `benjamin` (Dispatcher, Team DeepSpace9)
- **Role**: Dispatcher / Implementation
- **Assignment ID**: `1789827626051-9c5e5ecc`
- **Base Commit**: `75e02797fe` (`main`)
- **Status**: `review`
- **Worktree**: `/Users/tobias.anton/devel/autodocs/.worktrees/0033-12`
- **Branch**: `feature-0033-12`
- **Governing Standards**: WCAG 2.1 AA, WAI-ARIA 1.2, RFC 9562, DEC-0038-004

---

## 1. Objective & Scope

Task `0033-12` implements and verifies the complete UX interaction, accessibility, responsive design, and fallback behaviors for the review request interface across all operational modes:

1. **Keyboard, Focus & Dialog Semantics (`RRB-UX-001`)**:
   - `role="dialog"`, `aria-modal="true"`, and `aria-labelledby` semantics on modal overlays.
   - Focus restoration to initiating button (`[data-review-request-open]`) with `aria-expanded` toggle upon closure.
   - `Escape` key closes active dialogs without submission.
   - `Enter` submits or confirms forms while preserving newline capability in multiline textareas.
   - Validation failure focuses first invalid input or error alert.

2. **Live Announcements & State Telemetry (`RRB-BROWSER-001`)**:
   - Live region status announcements (`[data-review-request-state]`) for `exported`, `submitted`, and `error` outcomes.
   - Real-time identity modal resolution (`openIdentityModal`) attaching user-supplied names to `self_declared` packages.

3. **Responsive & Mobile Usability**:
   - Adaptive modal cards supporting portrait and landscape mobile viewports.
   - Touch-target padding conforming to WCAG 2.1 AA targets.

4. **No-JavaScript Degradation (`RRB-NOJS-001`)**:
   - Pure HTML rendering preserves full document readability when scripts are blocked.
   - Form controls gracefully hide interactive scrims and dialogs when scripting is absent.

5. **In-Browser Package Building & Local Storage (`RRB-BROWSER-001`)**:
   - Pure JS RFC 9562 UUIDv7 generator (`generateUUIDv7`, `requestId`).
   - Browser package assembly (`buildConfirmedPackage`) matching `review-request-package@v1` schema.
   - Safe identity downgrade to `self_declared` on JSON file export.
   - Local collection staging in `localStorage` under `ara-review-package-v1`.

---

## 2. Adversarial Completion Evidence (`DEC-0038-004`)

### AE-1: Applicability
Alters **browser interaction contracts, modal focus traps, UUIDv7 generation, ARIA live announcements, and JSON export downgrading**.

### AE-2: Baselines
- Pre-change baseline: `75e02797fe` (`main`)
- Candidate commit: `feature-0033-12`

### AE-3: Falsification Cases (Red-first / Threat Resistance)
1. **RFC 9562 UUIDv7 Validator Rejection**:
   - Proves generated UUIDv7 strings strictly adhere to version 7 (0x70) and variant 1 (0x80) bit patterns verified by Python validator across all generated samples.
2. **Export Identity Downgrade Invariant**:
   - Proves a GitHub-connected user exporting a raw JSON package has `identity_kind` downgraded from `github_authenticated` to `self_declared` while preserving `display_name`.
3. **Modal Keyboard Escape Dismissal**:
   - Proves `Escape` keyboard events dismiss the open dialog and return focus to the trigger element.
4. **Validation Focus Invariant**:
   - Proves empty category or empty rationale blocks progression, reveals error messages, and focuses the offending control.

### AE-4: Adjacent Contract Cases
- **Adjacent Case 1 (Local Storage Drawer Staging)**: Verified staging packages into `localStorage["ara-review-package-v1"]` creates conformant `local-only` items.
- **Adjacent Case 2 (No-JS CSS Rendering)**: Verified modal components remain hidden by default in CSS when JS is disabled, avoiding document obscuration.

---

## 3. Test Execution Summary

Executed the complete browser, builder, rendering, UX contract, and package validation test suites:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/tobias.anton/devel/autodocs/.worktrees/0033-12
configfile: pyproject.toml
collecting ... collected 17 items

_src/tests/test_review_request_browser.py .                              [  5%]
_src/tests/test_review_request_browser_builder.py ....                   [ 29%]
_src/tests/test_review_request_rendering.py .....                        [ 58%]
_src/tests/test_review_request_ux_contract.py .......                    [100%]

============================== 17 passed in 2.92s ==============================
```

And core ingestion & package tests:
```
============================= 106 passed in 1.33s ==============================
_src/tests/test_review_request_package.py .............................. [ 28%]
_src/tests/test_review_request_ingest.py ............................... [ 59%]
_src/tests/test_review_request_retention.py .......                      [ 66%]
_src/tests/test_review_request_package_v2_contract.py ...........        [ 76%]
_src/tests/test_review_request_abuse_control.py ........................ [ 99%]
```
