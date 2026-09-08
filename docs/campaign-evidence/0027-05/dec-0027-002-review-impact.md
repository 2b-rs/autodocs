# Review-impact statement — corrected SUP.8 decision `DEC-0027-002`

## Pins and authority

- Current-main base: `c27b8001fcd7b6a504aaf7fe36c481711d5e9d81`.
- Abandoned duplicate candidate: `897487036cd97c12784e67c5e68e7c687f6afade:docs/dossiers/dec-0027-001-sup8-package-and-gates.md`.
- Earlier retained MAN.3 allocation: `8772645587:docs/dossiers/dec-0027-001-man3-plan-gate-scope.md`.
- Independent SUP.8 scope review: `e4d6b34757950962040628d8c1e3974bf05dd91e`, verdict `supports-with-conditions`.
- Deterministic reconciliation direction: `agent-inbox:1787906519329-e38ca275`.

## Exact impact

The corrected record changes identity and allocation ownership only:

1. SUP.8 is reissued as collision-free `DEC-0027-002`; `DEC-0027-001` remains
   exclusively the earlier MAN.3 record.
2. The abandoned duplicate path is absent from this candidate and retained
   only by immutable commit/path provenance.
3. SUP.8 no longer claims to allocate `0027-11`. It consumes the same single
   terminal Feature Task allocated by MAN.3 and contributes its SUP.8 parent
   prerequisite, reconciliation criteria and checkpoint constraints to that
   one merged contract.
4. The six-child graph, `.04:0020-09` seam, six shared record interfaces,
   checkpoint locations, evidence-origin refusal, no-grandfathering, deferred
   security/store decisions, rollback, estimates and role separation remain
   substantively unchanged.

## Currency assessment request

The independent reviewer or separately authorized governance Integrator must
compare this exact candidate with `897487036` and record whether review
`e4d6b3475` remains current. Any change beyond the two reconciliations above
requires renewed supporting Architect review before mutation. This statement
is not review credit, Acceptance, integration authority, or activation.

No `TODO.md`, interface, implementation, ECU evidence, external system,
Acceptance record, Feature state or `main` reference is changed by this candidate.
