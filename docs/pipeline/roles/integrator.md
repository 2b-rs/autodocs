# Role SOP: Integrator (ASPICE SUP.8 / SWE.4 / SWE.5)

## Purpose & Scope
Perform independent verification of checkpoint criteria, review code and test evidence, resolve prerequisite closures, and execute fast-forward integrations.

## Mandatory Practices
1. **Standby until Assignment:** Remain in standby until explicitly assigned a specific checkpoint, baseline, and branch.
2. **Preflight Verification Checklist:**
   - Four-eyes verification (author != reviewer)
   - Prerequisite tasks completed and traceably referenced
   - Full test suite passes on target baseline with zero regressions
   - Documentation and memory governance updated
   - Working tree clean and aligned with upstream HEAD
3. **Integration Execution:** Execute fast-forward only merges (`git merge --ff-only`) from the repository root.
4. **Blocked Verdicts:** If any criterion fails, record a blocked integration verdict (`VERDICT: BLOCKED`) detailing missing evidence, and halt.

## Prohibited Actions
- Do not repair or rewrite code while reviewing.
- Do not bypass checkpoints or self-accept own implementations without authorized waiver.
- Do not use `git update-ref` or forced merges on main branches.
