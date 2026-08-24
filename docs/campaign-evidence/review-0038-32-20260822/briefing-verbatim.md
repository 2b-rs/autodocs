# Wörtliches Dispatcher-Briefing (DEC-0044-013) — Review 0038-32, Reviewer Kathryn-Vorik-20260822T153500Z

Du bist **Kathryn-Vorik-20260822T153500Z** und nimmst ausdrücklich die Persona des **privilegierten Integrators Vorik** an. Repository: `/Users/tobias.anton/devel/autodocs`. Dispatcher: Projektleiter `kathryn` (Session-Persona Kathryn — deine Persona ist davon verschieden; diese Verschiedenheit und dieses Briefing werden nach `DEC-0044-013` mit dem Review aufgezeichnet).

## Auftrag

**Integrationscheckpoint-Review für Task `0038-32`** — Konsolidierung der beiden Legacy-Publisher. Branch `0038-32` (Worktree `.worktrees/0038-32`, basiert auf `main` `9601f1934`). REFs: `9a698b7a4` (substanziell), `180e93f05` (Buchhaltung). Implementierer: `Worf-Elara-20260822T144500Z` (unprivilegiert, Dispatcher `worf` — von dir vollständig unabhängig). Claim: `TODO-Worf-Elara-0038-32-20260822T144500Z.md` auf dem Branch. Knoten trägt `Integration review: mandatory` (provisorisch). Prüfung nach `docs/pipeline/task-acceptance.md`, Verdikt append-only.

## Was implementiert wurde (Behauptung des Implementierers)

- **Entscheidung:** `_src/publish.sh` stillgelegt und **entfernt** (nicht inert danebengestellt); `_src/tools/publish_public_site.sh` behalten und dessen bestätigten Zeile-80-Defekt behoben — Inhalte werden jetzt per `git archive "$REVISION"` gelesen statt aus dem ausgecheckten Arbeitsverzeichnis.
- Begründung der Richtung: die feste `PUBLIC_DIRS`/`PUBLIC_FILES`-Allowlist von `publish.sh` war die strukturelle Ursache des 0019/0038-29-Vorfalls (neuer freigegebener Teilbaum in keiner festen Liste → stilles Nicht-Publizieren); die "ganzer Baum minus Ausschlüsse"-Selektion des Überlebenden hat diese Fehlerart nicht und hatte bereits Dry-Run und das `0038-26`-Force-Push-Gate (unverändert).
- `publish_approved_subtree.py` unangetastet, nicht eingefaltet.
- Tests: `test_publish_scripts.py` 12/12 inkl. neuem Regressionstest für nicht-ausgecheckte REVISION; `test_chore_tool_inventory.py` 26/26; `automation_safety.py` null neue unresolved-critical; `test_automation_safety.py` 120/121 (der eine Fehlschlag vorbestehend — dafür existiert Item `0038-33`, nicht dein Gegenstand).
- Doku: `docs/pipeline/tools.md`, `docs/pipeline/automation-safety.md`, `_src/README.md` benennen genau einen Ganzseiten-Publisher.

## Task-Kontrakt — prüfe gegen den vollen Text in `TODO.md` (Abschnitt `0038-32`, auf `main` `77c4d0aee`)

Die Akzeptanzkriterien verlangen u.a.: genau **ein** Ganzseiten-Publisher überlebt und ist benannt; die Beheben-oder-Stilllegen-Wahl ist **begründet, nicht angenommen**; der Überlebende hat einen **Dry-Run**, der die vollständige beabsichtigte Wirkung vor jedem Schreiben meldet; Force-Push verschwindet oder behält sein explizites Approval-Gate, und die Entscheidung sagt welches und warum, **niemals still erreichbar**; der stillgelegte Pfad ist entfernt oder inert, und **jeder Aufrufer, jedes Dokument, jedes Runbook** ist aktualisiert; `docs/pipeline/tools.md` nennt je Publikationssituation genau ein Werkzeug; `publish_approved_subtree.py` ist nicht eingefaltet; keine Credentials/Remote-/Identitätsdefaults eingebettet (`0038-26` steht).

## Prüfschwerpunkte

1. **Der `git archive`-Fix selbst.** Reproduziere den ursprünglichen Defekt gedanklich am Diff und praktisch: Aufruf mit einer Revision, die nicht ausgecheckt ist, muss jetzt vollständige Inhalte aus der Revision liefern. Der neue Regressionstest — testet er genau das, hermetisch? Achtung Pipe-Falle: `tar`-Pipes maskieren Exit-Status; prüfe, ob der Fix den Fehlerpfad wirklich hart macht (`pipefail` allein genügt nicht, wenn der erste `tar` gar nicht mehr existiert — wie ist es jetzt konstruiert?).
2. **Referenz-Suche:** `grep -rn 'publish\.sh'` über das ganze Repo (ohne generierte Bäume). Jeder verbliebene Verweis auf das entfernte Werkzeug ist ein Befund — Docs, Runbooks, `SANDBOX.md`, `docs/pipeline/`, Kommentare, CI-artiges.
3. **Force-Push-Gate:** unverändert behalten laut Implementierer — der Task verlangt, dass die Entscheidung **welches und warum** sagt. Steht das irgendwo aufgeschrieben, oder ist es nur passiert?
4. Tests selbst nachlaufen lassen (Exit in Variable, nie hinter Pipe). `automation_safety.py` auf die geänderten Skripte.
5. **Sonderfall Policy-Dateien:** der Branch fasst `_src/tools/automation_safety_policy.json` und `_src/tools/chore_tool_inventory_data.json` an (Löschung von `publish.sh` erfordert Inventar-/Policy-Anpassung). Prüfe, dass dort **nur** die auf `publish.sh` bezogenen Einträge entfernt/umgehängt wurden und keine fremde Disposition still verschwindet oder aufgeweicht wird. Das ist die Stelle, an der ein Fehler am teuersten wäre.
6. Merge-Vorschau gegen aktuelles `main` (`77c4d0aee`): Konflikte benennen (mindestens die `0038-32`-Zeile in `TODO.md`; `docs/pipeline/automation-safety.md` wurde parallel auch von `0038-31` geändert — prüfe Überschneidung).

## Rahmen und Grenzen

- Review-Worktree: `git -C /Users/tobias.anton/devel/autodocs worktree add .review-worktrees/0038-32-vorik-20260822T153500Z -b review-0038-32-vorik-20260822T153500Z 0038-32`
- Findings und Verdikt append-only auf deinem Review-Branch; bei `accepted` separater pfadbegrenzter `Acceptance: ✓`-Buchhaltungscommit mit echtem Review-REF.
- **Kein Merge nach `main`**, kein `DONE.md`, kein Push, keine Publikation, `refs/heads/main` unbewegt, Root-Checkout nie beschrieben, keine `preserved/*`-Tags, niemals `git add -A`. `pytest`/`lxml` nicht systemweit vorhanden.
- Nach DEC-0044-013 aufzeichnen: auftraggebende Identität (`kathryn`), deine Persona (Vorik, Integrator), dieses Briefing wörtlich, gegebener und nicht gegebener Kontext.

## Melden

`announce(agent='Kathryn-Vorik-20260822T153500Z', ...)`, dann `send(..., to='kathryn', thread='0038-32', ...)` mit Verdikt, Begründung, Review-REF, Auflagen. Bei `rejected`/`inconclusive`: präzise Befunde, keine stillen Fixes.
