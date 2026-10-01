# Team pause and phase-out — material direction and architecture decision

## Material user provenance

The following prompts are retained verbatim and in order:

1. “Ich hätte auch gerne, dass ein pausiertes Team über kurz oder lang keine Assignments mehr hat. Beim Team Voyager scheint das nicht geklappt zu haben. Kannst du da mal ein Auge drauf haben bitte.”
2. “Wir brauchen das so für alle Teams. Bitte beachten, dass den Agenten auch im phase-out die Tokens ausgehen können. D.h. es ist möglich, dass ein Agent schon dabei ist einen Auftrag abzugeben, aber dann läuft er in sein Token limit. Daher müssen wir den Auftraggeber dafür verantwortlich machen, dass er zu einem bestimmten Zeitpunkt - idR. nach Ablauf der Deadline - den Status des Auftragnehmers checkt und ihm nach sorgfältiger Abwägung ggfs. den Auftrag entzieht. Für diesen Fall haben wir bereits den Escalation-Mechanismus (Supervisor eskaliert nach Ablauf der Deadline), aber ich bin mir nicht sicher, ob alle Agenten immer richtig darauf reagieren.”

These statements set the product direction. They do not authorize a particular implementation, destructive reclamation, acceptance, release, or external effect.

### `DEC-0050-001` — Team pause is an audited drain with coordinator-owned deadline reclamation

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-09-01T10:38:08Z`
- **Deciding identity:** `agent:data:team-pause-phaseout-architecture-20260901:1788258791125-23f83bfb`
- **Role:** `Architect`
- **Authority reference:** `agent-inbox:1788258791125-23f83bfb`; material user direction above
- **Subject:** Team-independent pause, phase-out, quota exhaustion, deadline escalation and coordinator reclamation
- **Decision:** A team pause creates a generation-bound, append-only drain transaction. It atomically blocks new offer delivery and acceptance for every team member, freezes unresolved pre-award rounds, and marks awarded work `draining` until each assignment reaches a recorded terminal, held, or successor-owned outcome. The accountable coordinator must act on a typed deadline escalation using a retained evidence snapshot and exactly one bounded outcome. The team becomes `quiesced` only when authoritative open-offer, active-assignment and live-claim sets are all empty. Resume uses a new generation and never resurrects reclaimed work. Emergency provider blackout uses the same ownership, preservation and receipt semantics with a shorter fail-safe route.
- **Technical justification:** Existing dashboard hold prevents runtime starts but leaves awards and claims; stop terminates processes; blackout permits hard reclamation; and deadline escalation does not prove coordinator action. A single transactional lifecycle prevents new intake while preserving useful work, makes accountability observable, and removes silence or token exhaustion as a proxy for safe deletion.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `security-or-credential-boundary`
- **Considered alternatives:**
  - **ALT-01:** Generation-bound audited drain and coordinator decision receipt
    - **Disposition:** `selected`
    - **Reason:** It blocks new ownership races while preserving work and makes every reclamation attributable and restart-safe.
  - **ALT-02:** Immediately cancel all team assignments when pause is requested
    - **Disposition:** `rejected`
    - **Reason:** Cancellation can discard in-flight handoffs and treats unavailability as proof that no useful work exists.
  - **ALT-03:** Keep dashboard hold and rely on Project Leads to inspect manually
    - **Disposition:** `rejected`
    - **Reason:** The current gap is precisely the absence of a durable zero proof and mechanically enforced coordinator response.
- **Consequences:**
  - **CON-01:** Offer acceptance must compare-and-swap the current team generation and reject paused or stale generations.
  - **CON-02:** Active awards remain owned until completion, hold, accepted delegation, or recorded cancellation/revocation; a replacement cannot start earlier.
  - **CON-03:** Coordinator extensions are bounded and counted; repeated extension cannot suppress escalation indefinitely.
  - **CON-04:** Quiescence requires a deterministic zero-set receipt across offers, assignments and claims; dashboard counts alone are insufficient.
  - **CON-05:** Blackout reclamation may proceed without contractor response but must preserve reachable work or record preservation failure without destroying evidence.
  - **CON-06:** Rollback disables the new admission gate only through an authorized generation event and retains all prior drain/reclamation history.
- **Affected work units:**
  - `feature:0050`
  - `repository:agent-inbox`
  - `repository:autodocs`
  - `all-team:future-assignment-lifecycle`
- **Affected gates:**
  - `assignment-start:offer-reply-accept`
  - `assignment-transition:deadline-reclamation`
  - `team-availability:pause-resume`
  - `integration:0050-08`
- **Review participation:** `none`
- **No-review reason:** Independent Architect scope review is a separately assigned pre-implementation product at `docs/dossiers/team-pause-phaseout-architect-review.md`; it must support or reject this exact decision and DAG before operative mutation.
- **Waiver:** `none`

## Activation and no-grandfathering

The decision is non-operative until `0050-00` binds this record, the requirements and interface digests, and a supporting distinct Architect review. Activation applies to every nonterminal offer/assignment after migration: unresolved pre-award rounds receive the active pause generation; already-awarded work is projected as `draining`; nothing is silently grandfathered outside the receipts. Historical terminal assignments remain immutable history.
