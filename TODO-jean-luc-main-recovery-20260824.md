# Main recovery coordination claim

- owner_token: `agent:jean-luc:main-recovery:20260824T182300Z`
- capability_class: `privileged`
- execution_authority: current user selected Option B on 2026-08-24
- incident_ref: `6d9a9ba116419fc0631412870f9d5914d3fda7c2`
- authorized_target: `a3cee63085bdee02521c0437d8696ee1afaa872e`
- branch: `recovery-main-6d9a9ba-option-b-20260824`
- worktree: `.worktrees/recovery-main-6d9a9ba-option-b-20260824`
- write_scope: `docs/pipeline/branch-workflow.md`, this claim, and the exact user-requested memory files already present as root divergence
- status: preparation; root/main unchanged pending preservation tag, hygiene, hard preflight, and Integrator sequence review

## Recovery contract

1. Preserve the incident commit as `preserved/main-incident-6d9a9ba-20260824` before it leaves `main` reachability.
2. Carry the legitimate root Memory changes into this branch before clearing the root worktree.
3. Run integration hygiene and the root hard preflight; any unexplained finding aborts.
4. Under the user's explicit Option-B authority, restore root/main to `a3cee63085bdee02521c0437d8696ee1afaa872e` without `git update-ref`.
5. Fast-forward the recovery documentation branch from root so the preserved-tag record and Memory changes remain on `main`.
6. Verify tag target, main ancestry, clean tracked root/index, retained 0037 Task branches, and no accidental Feature integration.
