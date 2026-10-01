# `DEC-0044-028` — Responsibility allocation is distinct from authority

This record captures the current user's binding clarification of ordinary
work-package and Feature responsibility. It does not implement the correction,
rewrite earlier user instructions, grant a claim, or confer privileged process
authority. The supporting pre-mutation Architect review is recorded separately
in [`0044-028-responsibility-allocation-scope-review.md`](0044-028-responsibility-allocation-scope-review.md).

### `DEC-0044-028` — Capable roles may carry responsibility without receiving authority

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-26T14:45:00Z`
- **Deciding identity:** Management (current user / repository owner)
- **Role:** Management
- **Authority reference:** Current-user clarification recorded by Project Lead `jean-luc` in `agent-inbox:1787755052173-45def431`; formal Architect assignment and exact decision text in `agent-inbox:1787755235010-2b87af70`; Acceptance-boundary clarification in `agent-inbox:1787755266031-c9f5098a`
- **Subject:** Who may assume ordinary Feature or work-package responsibility, who may select a concrete Project Lead or owner, and which authorities do not follow from that allocation
- **Decision:** Any role or session that satisfies the work unit's recorded capability requirements may assume ordinary responsibility for a Feature or work package. A Project Lead may select, agree, assign, reassign, or delegate that ordinary responsibility without a separate Management decision, provided the allocation is explicit, the recipient is sufficiently capable for the exact contract, existing ownership and write-scope rules are respected, and any required briefing is complete. Capability matching is eligibility evidence, not the allocation itself. Responsibility allocation grants no capability class, privilege, claim token, write-scope expansion, independence, Acceptance authority, integration authority, release authority, waiver, specialist approval, risk acceptance, external credential/configuration authority, or permission to resolve `[u]`. A Project Lead is not automatically a registered Acceptance authority: an Acceptance review still begins only after exact assignment by the current user or an expressly registered Acceptance authority. Integration, Feature closure, release, and other privileged acts likewise retain their exact separate assignment and authority rules. Earlier concrete user selections and reservations, including Seven's recorded selection for `0039-01`, remain effective unless expressly superseded through an authoritative handoff or decision; this general rule does not silently revoke them.
- **Technical justification:** Current governance conflates three different questions: whether a session is capable, who allocates ordinary responsibility, and who holds authority for a privileged act. `docs/pipeline/process-roles.md` says Management assigns roles, while `docs/pipeline/capability-matching.md` says an orchestrator chooses among eligible agents and `AGENTS.md` already makes a dispatcher responsible for an exact briefing. Feature `0039` then turns ordinary ownership into a blanket current-user-selected privileged-session gate, even where the content work requires no privileged act. That coupling unnecessarily blocks capable owners and obscures the real controls. Separating eligibility, allocation, claim ownership, and authority preserves the user's ability to direct work, lets Project Leads coordinate ordinary work, and keeps Acceptance, integration, release, waiver, independence, and risk decisions fail-closed under their existing exact authorities.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
- **Considered alternatives:**
  - **ALT-01:** Separate capability eligibility, ordinary responsibility allocation, claim ownership, and authority-bearing acts; allow Project Leads to allocate ordinary responsibility while preserving exact privileged assignments and prior concrete user reservations.
    - **Disposition:** `selected`
    - **Reason:** This implements the clarified rule with the smallest change while preserving every safety, independence, and authority boundary.
  - **ALT-02:** Continue requiring the current user to select every ordinary Feature or work-package owner and require every owner to be privileged.
    - **Disposition:** `rejected`
    - **Reason:** It conflates ownership with authority, contradicts capability-derived execution, and creates avoidable task-start blocks.
  - **ALT-03:** Treat Project-Lead selection as granting Acceptance, integration, release, or other privileged authority.
    - **Disposition:** `rejected`
    - **Reason:** Assignment of ordinary responsibility cannot establish privilege, independence, registered authority, or specialist approval and would defeat the repository's exact-assignment controls.
  - **ALT-04:** Apply the general rule retroactively by silently cancelling every earlier named user reservation.
    - **Disposition:** `rejected`
    - **Reason:** Concrete user selections are specific authoritative history; silent cancellation would destroy provenance and appropriate existing responsibility.
- **Consequences:**
  - **CON-01:** `docs/pipeline/process-roles.md` becomes the canonical statement that ordinary responsibility allocation is distinct from authority-bearing role instantiation and that Management retains waivers, `[u]` resolution, process changes, material architecture/risk/security/release decisions, external credential/configuration decisions, and expressly reserved authorities.
  - **CON-02:** `AGENTS.md` and `docs/pipeline/capability-matching.md` are aligned so a Project Lead or dispatcher may choose among sufficiently capable recipients, records the exact assignment/briefing, and cannot turn matcher output or allocation into authority, ownership proof, independence, Acceptance, integration, or release permission.
  - **CON-03:** Feature `0039` projections are corrected atomically: ordinary content ownership no longer requires a current-user-selected privileged session; privileged approval, Acceptance, registry/tool promotion, integration, and Feature closure remain separately assigned. Real prerequisites and explicit risk gates remain intact.
  - **CON-04:** Seven's existing `0039-01` selection remains effective. The internally stale statement that a user selection is still the sole next action is corrected additively without erasing the original selection or source provenance.
  - **CON-05:** Harry's existing `0039-02` process-owner designation is complete for ordinary responsibility. Its implementation capability is derived from the exact work contract; any privileged acts are split out and assigned separately rather than upgrading ownership by implication.
  - **CON-06:** The correction is one atomic governance change across every changed projection. Partial activation that updates the canonical role rule but leaves contradictory reservation gates, or removes gates without preserving privileged-act boundaries, is forbidden. Rollback reverts the changed projections together and preserves this decision and review evidence.
  - **CON-07:** No active claim or concrete prior assignment is appropriated. Reassignment of an already named owner requires an explicit handoff or superseding authority; ordinary Project-Lead agreement governs only where no stronger specific instruction controls.
  - **CON-08:** Implementation is performed by an identity distinct from Architect `agent:data:0044-028:responsibility-allocation-20260826T144109Z` and begins only after this decision and its supporting review are reachable from `main`. Acceptance and integration remain later, separately assigned acts.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0039`
  - `task:0039-01`
  - `task:0039-02`
  - `task:0039-03`
  - `task:0039-05`
  - `feature:0044`
  - `path:AGENTS.md`
  - `path:TODO.md`
  - `path:docs/pipeline/process-roles.md`
  - `path:docs/pipeline/capability-matching.md`
  - `path:docs/dossiers/README.md`
  - `path:docs/studies/README.md`
- **Affected gates:**
  - `task-start:0039-01`
  - `task-start:0039-02`
  - `task-start:0039-03`
  - `task-start:0039-05`
  - `integration:0039`
  - `feature-closure:0039`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0044-028:responsibility-allocation-20260826T144109Z`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports`
    - **Note:** Management-instantiated Architect review is bound to the exact decision candidate in `docs/dossiers/0044-028-responsibility-allocation-scope-review.md`; Data is not the Implementer or Integrator.
- **Waiver:** `none`

#### `DEC-0044-028-C001`

- **Event format:** `decision-record-correction@v1`
- **Target record:** `DEC-0044-028`
- **Recorded at:** `2026-08-26T14:50:00Z`
- **Correcting identity:** `agent:data:0044-028:responsibility-allocation-20260826T144109Z`
- **Role:** `Architekt`
- **Authority reference:** `DEC-0044-028`; independent STOP finding `agent-inbox:1787755616970-fa5798ce`; Project Lead correction assignment `agent-inbox:1787755651657-f758eefb`; registered Management identity evidence in `docs/dossiers/dec-capability-classes.md` and `docs/dossiers/dec-0038-005-restore-terminal-integration-task.md`
- **Correction reason:** The base record rendered the deciding authority as descriptive prose rather than the repository owner's registered stable identity. This recording-only correction preserves the same current-user Management decision and changes no decision content, reach, gate, reservation, or authority boundary.
- **Target field:** `Deciding identity`
- **Previous effective block SHA-256:** `7990d83b2cc9772c177cfe26d0aadaa2ec8433a5555a838b37705f30c919cce9`
- **Replacement block:**
  ```markdown
  - **Deciding identity:** `authority:repository-owner`
  ```
