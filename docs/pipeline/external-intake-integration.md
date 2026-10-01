# External Intake Integration Architecture (Feature 0016-14)

## Purpose
This document specifies the architecture for integrating unauthenticated or loosely authenticated external intake channels (e.g., GitHub issues, web forms) with the canonical problem/change management system. It ensures that external reports are properly validated and transformed into authenticated, controlled configuration items (SUP.9, SUP.10).

## 1. Segregation of Intake vs. Canonical Records
- **Intake Channel:** External platforms (GitHub, Jira, Zendesk) serve *only* as the intake funnel. They are not the system of record for ECU development.
- **Canonical Record:** The canonical system of record is the Immutable Evidence Repository (Feature 0015-06). A problem or change request only officially exists once it is ingested, authenticated, and assigned a canonical identifier (e.g., `PRB-2026-001`) in the repository.

## 2. Ingestion & Authentication Gateway
To bridge the gap between intake and canonical records:
- **Intake Gateway:** An automated service must monitor the intake channels. Upon detecting a new report, it extracts the structured data (description, severity, reporter).
- **Authentication:** Before the record can be committed to the canonical ledger, it must be authenticated.
  - If the reporter is a known, authenticated project member, the gateway maps their identity.
  - If the reporter is external/anonymous, a designated internal triage authority (e.g., the Project Lead or a Triage Engineer) must review and cryptographically sign the ingestion event, taking ownership of the canonical record.

## 3. Communication & Synchronization
- **Bidirectional Sync:** The integration must support basic bidirectional communication without compromising the integrity of the canonical store.
  - Status updates (e.g., `In Progress`, `Resolved`, `Rejected`) and public resolution comments from the canonical system should be pushed back to the external intake channel.
- **Evidence Retention:** The initial raw payload from the external intake, along with the triage signature and the mapping between the external ID (e.g., `GH-Issue#42`) and the canonical ID, must be retained as immutable evidence.
