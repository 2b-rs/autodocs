# 0033-04 UX candidate — executable scenarios and test map

**Status:** Review-ready scenario contract; not approval or implementation
coverage. Test IDs name later implementation tests. `UXC-*` checks in
`_src/tests/test_review_request_ux_contract.py` validate this mapping now.

| ID | Scenario and expected result | Later automated test | Current contract check |
|---|---|---|---|
| UX-01 | Eligible `valid/curator-decided` record opens Request review and shows immutable target/status/source. | `0033-10` `test_valid_curated_disclosure` | UXC-01 |
| UX-02 | Active duplicate before open replaces action with privacy-safe reference. | `0033-10` `test_duplicate_before_open` | UXC-02 |
| UX-03 | Duplicate race after confirmation returns authoritative duplicate; no second item. | `0033-06/07` `test_duplicate_race_no_write` | UXC-03 |
| UX-04 | Live version/hash changes before ingest; only authoritative ingest returns stale and no queue write. | `0033-06/07` `test_stale_at_ingest_no_write` | UXC-04 |
| UX-05 | Exact confirmed canonical bytes export as JSON and remain `exported`, not submitted/queued. | `0033-10/11` `test_export_exact_confirmed_bytes` | UXC-05 |
| UX-06 | GitHub transfer receipt is shown as submitted-with-receipt; no queue claim is made. | `0033-11` `test_receipt_not_ingestion` | UXC-06 |
| UX-07 | A signed-in client exporting JSON remains self-declared/anonymous; no GitHub-authenticated client package is created. | `0033-10/11` `test_authenticated_json_downgrade` | UXC-07 |
| UX-08 | Signed-out no-JS Issue submission reaches trusted normalization; absent GitHub submission/configuration fails safely. | `0033-06/12` `test_nojs_success_and_failure` | UXC-08 |
| UX-09 | Transport failure/unknown preserves bytes; retry reuses the immutable event; edit mints a new event. | `0033-11` `test_retry_and_edit_identity` | UXC-09 |
| UX-10 | Cancel restores trigger focus and does not claim remote cancellation or record mutation. | `0033-10/12` `test_cancel_focus_and_nonmutation` | UXC-10 |
| UX-11 | Desktop and <768 px mobile layouts preserve target summary and usable controls. | `0033-12/13` `test_desktop_mobile_layout` | UXC-11 |
| UX-12 | Keyboard opening, focus trap/restoration, labelled dialog, field errors and live regions work. | `0033-12/13` `test_keyboard_focus_and_live_regions` | UXC-12 |
| UX-13 | Legacy source migration is typed, source-preserving, idempotent, tombstone-safe and excludes credentials. | `0033-10.01` `test_migration_multitab_quota_clear` | UXC-13 |
| UX-14 | Trusted status projection shows ingested/queued and later governed result only after server evidence. | `0033-11/14` `test_post_ingestion_traceability` | UXC-14 |

## Scenario execution constraints

Later tests use temporary browser storage, fake receipt/status adapters and
isolated target/queue fixtures. They must prove no record/page/generated-output,
credential, public-host or live Issue effect. Browser tests do not substitute a
synthetic target object for production metadata coverage required by `0033-13`.

## Traceability

- `UX-01`–`UX-04`: eligibility, duplicate and live-staleness requirements.
- `UX-05`–`UX-09`: exact-byte package, identity, receipt and no-JS trust
  boundaries.
- `UX-10`–`UX-12`: cancellation, accessible keyboard/mobile interaction.
- `UX-13`: single typed collection and non-destructive migration.
- `UX-14`: truthful post-ingestion and governed lifecycle feedback.

No scenario authorizes a concrete transport profile, retention period, public
projection or production write. Those remain explicit approval decisions.
