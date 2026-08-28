# G3 evidence — `DEC-0044-027-C001` activation/carry SHA

**Recorder:** `agent:saru:0044-12-g3:20260828T083500Z`, Architect, Team Discovery
**Award:** `agent-inbox:1787906004782-6a33f43c` against `main@c27b8001fcd7b6a504aaf7fe36c481711d5e9d81`
**Index:** append-only correction in `docs/dossiers/dec-0044-027-policy-provenance-recording.md` → `DEC-0044-027-C001`
**G3 source:** `docs/campaign-evidence/0044-12/belanna-integration-review-20260826T154058Z.md:17`

This file is an evidence/index pointer. It is not a new decision, not Task Acceptance, and not integration.

## Named activation/carry commit

- SHA: `054024476b55f02d60f2dc7a0d52c48c148c52bf`
- Subject: `0044-12: carry historic reviewed catch-up`
- Trailer: `Policy-Origin-Branch: main`
- Ancestor of awarded `main` `c27b8001fcd7b6a504aaf7fe36c481711d5e9d81`: verified `git merge-base --is-ancestor`

## Correction digest

- Target field: `Consequences`
- Previous effective block SHA-256: `9ec6ffd34b85d8011d65b553445584af3d2a7861cebb818b6805969177cc8f15`
- Preimage: UTF-8 LF bytes of the published `Consequences` block on the awarded baseline (lines starting at `- **Consequences:**` through `CON-09`, per `docs/pipeline/decision-record.md` §5)
- Replacement names `054024476b55f02d60f2dc7a0d52c48c148c52bf` inside CON-05; CON-01..CON-04 and CON-06..CON-09 are byte-identical to the previous block

## Out of this recording

No product/tool/policy mutation. No `0044-13`. No Acceptance. No `main` advance.
