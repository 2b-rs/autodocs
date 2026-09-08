---
schema_version: "1.0"
id: "0038-32"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-29"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1817"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0038-32:0038-29 Consolidate the two legacy publishers into one, and retire what is left. Claim: `TODO-Worf-Elara-0038-32-20260822T144500Z.md`; owner_token: `agent:worf-elara-20260822t144500z:0038-32:20260822T144500Z`; base_commit: `9601f1934`. REF: `9a698b7a400bdd573a8a5d51697dcb69f3d2f2e4`. Acceptance: ✓ (Integrationscheckpoint-Review `dbaeb2638`, privilegierter Integrator Vorik / Session `Kathryn-Vorik-20260822T153500Z`, 2026-08-22, Verdikt accepted; Report `docs/campaign-evidence/review-0038-32-20260822/report.md`, DEC-0044-013-Aufzeichnung ebd.; Auflage AU-1 nicht blockierend).

## Scope

- **Management direction (2026-08-22):** „die beiden Skripte konsolidieren." Recorded by Projektleiter `kathryn`.
  - **Context:** The repository currently carries **three** publication mechanisms with different selection logic, and on 2026-08-22 that cost a working day. `_src/publish.sh` syncs a fixed directory list (`PUBLIC_DIRS`/`PUBLIC_FILES`) with `rsync -a --delete`, has **no** dry run, and cannot publish anything outside that list. `_src/tools/publish_public_site.sh` exports the whole tracked tree minus an exclude list into an orphan branch, has a real dry run, and can force-push. It also carries a confirmed defect: line 80 takes the file **list** from `git ls-tree <REVISION>` but reads the file **contents** from `$REPO_ROOT`, so invoked against a revision that is not checked out it produces a silently incomplete export — and the pipe masks the failure, because only the second `tar`'s status counts. Both were reproduced hermetically (`0038-29` review round 1, report `536860ce4`, and the rework). `0038-29` added `_src/tools/publish_approved_subtree.py` for the bounded, digest-pinned case; it deliberately replaced nothing.
  - **Problem statement:** Three mechanisms, two of them overlapping in purpose and one of them quietly broken, mean an operator must *choose correctly under time pressure* before an irreversible public action. On 2026-08-22 the correct choice was neither of the two legacy tools, and finding that out took three separate investigations.
  - **Integration review: mandatory.** **Rationale (provisional — conservative default, not an architect decision):** the node decides which mechanism performs an **irreversible public publication** and removes one of the existing paths; a wrong retirement removes a capability someone depends on, and a wrong consolidation carries the known defect into the survivor. Set by Projektleiter `kathryn`, who does not set checkpoints; the architect confirms or downgrades it with a recorded justification, at the latest at Feature `0038` closure.
    - **Architect checkpoint decision (2026-08-24, Architect `seven`, Seven of Nine; recorded per `process-roles.md` §Architect and the `AGENTS.md` checkpoint contract):** **confirmed — mandatory; already exercised.** The node selects the surviving mechanism for irreversible public publication and retires a path; a wrong retirement or a defect carried into the survivor reaches every future release. Crossed under review: privileged integrator `Kathryn-Vorik-20260822T153500Z`, verdict `accepted` (REF `dbaeb2638`). Ratified; no downgrade.

## Acceptance criteria

- **AC-001** Exactly **one** whole-site publisher remains, and it is named. The confirmed `publish_public_site.sh:80` defect is either fixed (contents read from the revision, e.g. `git archive`, so a revision argument means what it says) or the tool is retired — whichever is chosen, the choice is justified in the decision, not assumed. The surviving publisher has a **dry run** that reports the complete intended effect before anything is written, matching what `0038-29` already requires of the bounded tool. Force-push either disappears or keeps its existing explicit approval-reference gate, and the decision states which and why
- **AC-002** it is never silently reachable. The retired path is removed or made inert — not left executable next to its replacement — and every caller, document and runbook referencing it is updated. `docs/pipeline/tools.md` afterwards names, for each publication situation, exactly one applicable tool
- **AC-003** the section introduced by `0038-29` is updated rather than duplicated. `_src/tools/publish_approved_subtree.py` is **not** folded in: bounded digest-pinned publication and whole-site publication stay separate tools with separate guarantees

## Definition of Done

Committed with tests for the surviving publisher's dry run and for whatever replaced the defective content read; `python3 _src/tools/automation_safety.py` passes for every touched script; no credentials, remote or identity defaults are embedded (`0038-26` stands); the retirement and its reason are recorded so nobody restores the old path from history without seeing why it went. If retirement turns out to require a capability nothing else provides, that is reported instead of quietly keeping both.
