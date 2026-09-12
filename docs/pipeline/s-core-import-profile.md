# S-Core Import Profile (Feature 0019-03)

## Purpose
This document defines the architectural profile for importing data from S-Core, mapping external artifacts into canonical representations while explicitly identifying unsupported or rejected inputs.

## 1. Source Selectors & Supported Artifact Classes
The extraction adapter only processes specific artifact classes from S-Core:
- **Supported:**
  - `ProblemReport` (maps to SUP.9)
  - `ChangeRequest` (maps to SUP.10)
  - `RiskItem` (maps to MAN.5)
- **Ignored / Non-goals:**
  - `DiscussionThread`, `WikiPage`, `MeetingMinutes`, `BuildLog`
  - Internal S-Core configurations or permissions matrices.

## 2. Field Mapping
The data model mapping enforces standard compliance:
- `S-Core: ID` -> `Canonical: external_id`
- `S-Core: Title/Summary` -> `Canonical: title`
- `S-Core: Severity` -> `Canonical: priority` (must be normalized to {Critical, High, Medium, Low})
- `S-Core: Submitter` -> `Canonical: reporter`
- `S-Core: CreationDate` -> `Canonical: created_at`

## 3. Status Defaults & Triage
- Newly imported S-Core records default to a status of `Draft` or `Intake-Pending`.
- They do not enter the active workflow (e.g., `In Progress`) until cryptographically authenticated and accepted by a designated Triage Authority, consistent with the External Intake Integration architecture (Feature 0016-14).
- State transitions mapping (e.g., S-Core `Closed` -> Canonical `Closed-Resolved`) require verification of mandatory closure evidence. If closure evidence is missing, the record remains in `Intake-Pending`.
