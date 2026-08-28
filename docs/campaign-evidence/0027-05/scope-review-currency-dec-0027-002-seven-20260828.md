# Review-currency assessment — `DEC-0027-002` against prior review `e4d6b3475`

**Review kind:** bounded read-only currency assessment of my own prior independent scope review.
**Not** a new scope review, not Acceptance, not an integration verdict. Activates nothing.

**Reviewer:** Architect `seven` — OFFER `1787906997940-3488ce0b`, ACCEPT `1787907123651-c8e895bc`,
AWARD `1787907156037-8abb0606`.

| | |
|---|---|
| Corrected candidate | `286a7c4933c6edb3e201814708ac85bc2125b414` |
| Declared base | `main@c27b8001fcd7b6a504aaf7fe36c481711d5e9d81` — **preserved, not rebased or repinned** |
| Abandoned candidate | `897487036cd97c12784e67c5e68e7c687f6afade` |
| Prior review | `e4d6b34757950962040628d8c1e3974bf05dd91e` |
| Candidate delta vs declared base | 3 paths, **+158/−0**, purely additive |

**Determination: the prior review `e4d6b3475` REMAINS CURRENT. Both conditions are discharged, and
there is no material architecture change.**

---

## C-1 — collision-free `DEC-0027-002`: **discharged**

```
286a7c493 : docs/dossiers/dec-0027-002-sup8-package-and-gates.md
            ### `DEC-0027-002` — Decompose ECU SUP.8 and constrain the shared Feature
                                 integration floor
897487036 : docs/dossiers/dec-0027-001-sup8-package-and-gates.md   (abandoned)
8772645587: docs/dossiers/dec-0027-001-man3-plan-gate-scope.md     (retains DEC-0027-001)
```

**MAN.3 keeps `DEC-0027-001`; SUP.8 moves to `DEC-0027-002`.** The duplicate allocation that made
`F-SUP8-01` binding no longer exists between these two records. **Which record kept the number was
the Project Lead's call and I did not make it** — I record only that the collision is resolved.

## C-2 — exactly one MAN.3-owned `0027-11`: **discharged, and in the stronger of the two forms**

My finding `F-SUP8-02` was that **both** records created `0027-11`, each claiming to be the
exactly-one terminal integrating Task. I named two acceptable resolutions: one record creates it and
the other consumes it, or the two contracts merge. **The candidate takes the first, explicitly:**

> *"decision `DEC-0027-001` **owns the allocation** of Feature `0027`'s exactly-one terminal
> integrating Task `0027-11`; this decision **consumes** that same Task and contributes the
> completed SUP.8 …"*
>
> *"… amend the one `0027-11` contract allocated by `DEC-0027-001`; it **must not create a second
> `0027-11` or weaken MAN.3** …"*

**The rule is now defended, not merely obeyed.** `ALT-05` was widened from *"Add checkpoints to every
child package"* to *"**Allocate another terminal integration Task for SUP.8** or add checkpoints to
every child package"*, rejected because *"`0027-11` is already the single Feature composition
boundary"*. **A second allocation is now a named, rejected alternative** rather than an omission —
which is what makes the discharge durable instead of incidental.

## Material architecture change: **no**

Measured field by field, abandoned `897487036` against corrected `286a7c493`:

```
Triggers                 IDENTICAL
Affected work units      IDENTICAL
Affected gates           IDENTICAL
Considered alternatives  DIFFERS  ← only here
```

**The sole substantive difference is the allocation/consumption reframing**, in exactly two places:

- `ALT-01`: *"and one terminal Feature integrating Task"* → *"and **contribution to the one
  MAN.3-allocated** terminal Feature integrating Task"*.
- `ALT-05`: extended to reject a second terminal integration Task, with `0027-11` named as the
  already-single composition boundary.

**Six children, their ordering, `.04:0020-09`, the three checkpoints, the shared record interfaces,
the evidence-origin boundary, no-grandfathering, security/store deferral and rollback are unchanged**
— `Affected work units` and `Affected gates` are byte-identical, which is the strongest available
evidence that reach did not move.

**The title change is therefore accurate rather than cosmetic.** *"Add the Feature integration
floor"* → *"**constrain** the shared Feature integration floor"* describes precisely what changed:
the record stopped allocating the floor and started constraining its own contribution to a floor
allocated elsewhere. **This is a relationship correction, not an architecture change**, and my prior
review's substantive support survives it intact.

## Drift to current `main` — measured separately, attributable to neither candidate

```
c27b8001f → 8beceeff8 :  4 files, +135/−0
  docs/campaign-evidence/…/g3-activation-sha-c001-saru-20260828.md
  docs/dossiers/dec-0044-027-policy-provenance-recording.md
```

**Target-only governance evidence from the `0044` line.** It does not touch `0027`, the SUP.8
record, or anything this review measured. **The candidate remains correctly pinned to its declared
base**, and I neither rebased nor repinned it, as instructed. **None of this drift is attributable to
the candidate or its author** — recorded explicitly because attributing target drift to an
implementer is the exact error I made against this same author's `0044-029` work earlier today and
had to withdraw.

## Standing from the prior review

Everything supported in `e4d6b3475` stands: six children isolating six risk classes; `0020-09` at the
mechanism/ECU-reality seam; six versioned records with the `DEC-0020-001/-002` identity boundary;
three checkpoints each at a named boundary; **`CON-06` keeping mechanism evidence non-ECU**;
no-grandfathering; store/credential deferral where absence blocks only the needing package; rollback
that never deletes history; and the author barred from accepting its own decomposition.

**`C-3` from the prior review remains open and remains advisory**: the allocation mechanism will
recur, because a `main`-only view cannot see unmerged candidates. **This candidate did not cause that
defect and cannot cure it.** Its resolution is a process matter whose owner is not this author — and
the present correction is evidence the mechanism is real, not evidence it is fixed.

## Boundaries

Read-only. No integration, no `TODO`/backlog/interface mutation, no activation, no Acceptance, no
`main`/`DONE.md` movement, no scope expansion, no rebase or repin of the candidate. Write scope was
this artefact and the claim on this item-owned branch. This assessment pins the corrected candidate
exactly and does not extend to any successor commit.
