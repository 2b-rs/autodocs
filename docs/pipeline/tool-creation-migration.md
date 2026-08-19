# Reusable Tool Process Migration and Retirement Plan

## Controlled adoption

1. Keep current tool, runner, catalog, and authority behavior unchanged while this process is a candidate.
2. Baseline a reviewed process version, templates, validator digest, reconciliation, pilot evidence, findings, and tailoring records only through an explicit authority decision.
3. Inventory existing tools without retroactive qualification. Missing historical data remains unknown.
4. Apply the candidate process first to newly authorized proposals; a process record cannot register an action, promote a candidate, or modify a production tool.
5. After measured paired pilots, the authority decides adopt, revise, or reject. Absent that decision, this package remains candidate-only.

## Authority mapping

| Concern | Legacy authority | Post-`0037` authority |
|---|---|---|
| Proposal/evidence | `TODO.md` plus committed process records | issue records and provenance graph |
| Candidate execution | isolated, separately authorized mechanism | queue request with a candidate-confinement action/profile |
| Registered production action | no inference from this package | `0037-46.01` typed registry and dispatcher |
| Results/retention | committed evidence and retained runtime results | issue-linked immutable queue results |
| Retirement | owner decision plus current records | typed-action disablement and issue lifecycle record |

No transition dual-maintains control authority. A failed migration preserves the old authority, retains an append-only failure report, and resumes only from pinned source identities.

## Compatibility, deprecation, and retirement

Breaking input/output/finding/status/effect changes require a new contract major version and impact analysis. Compatible additions require safe defaults and consumer checks. Deprecation records a successor or manual fallback, consumer migration window, qualification status, and warning/disable plan. Retirement verifies consumer, action, configuration, credential, and scheduled-job removal; preserves immutable results and historical interpretation; and removes ordinary execution authority before any source cleanup.
