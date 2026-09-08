# Decision Preparation: Agent Profile Feedback Loop

**Item:** 0046
**Question:** Which policy should govern anonymous submission, approval authority, and the exact publication/activation gates for the agent profile feedback loop?
**Deciding Role:** Management
**Observed Fact:** The `agents.json` profile is currently manually edited. Implementing the automated feedback loop introduces a cross-item blast radius, affecting all agents and future Tasks. The architecture proposed in `docs/pipeline/agent-profile-feedback-loop.md` separates proposing from mutating, but requires a formal management decision on anonymous policies, who holds approval authority, and what constitutes the public projection boundary.
**Paused Action:** Operative mutation for the feedback loop (Tasks 0046-01 through 0046-06) is blocked pending this decision.
**Permanent Records:**
- `docs/pipeline/agent-profile-feedback-loop.md`
- `docs/dossiers/agent-profile-feedback-loop-requirements.md`
- `docs/dossiers/0046-feedback-profile-architect-scope-review.md`

## Options
### Option 1: Authenticated-only, Project Lead approval
**Summary:** Only authenticated users can submit feedback. Project Leads hold approval authority.
**Consequences:** High accountability. Lower volume of feedback. Abuse risks are minimized. Fits well with existing Project Lead roles.

### Option 2: Allow anonymous, Management approval
**Summary:** Anonymous submissions are allowed, but Management must approve any resulting proposals.
**Consequences:** Higher volume of feedback. Anonymous submitters cannot promote. Management becomes a bottleneck for profile updates.

## Recommendation
**Option 1**
**Reason:** Ensures strong accountability and minimizes abuse risks at the ingress layer while delegating approval authority to Project Leads, preventing a Management bottleneck without relaxing security.
