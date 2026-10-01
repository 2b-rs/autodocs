# Integrationscheckpoint-Review — Task 0038-32 (Konsolidierung der Legacy-Publisher)

- **Verdikt:** **accepted** (append-only)
- **Reviewer-Persona:** Vorik, privilegierter Integrator (Session `Kathryn-Vorik-20260822T153500Z`)
- **Auftraggebende Identität (Dispatcher):** Projektleiter `kathryn` (Session-Persona Kathryn — von der Reviewer-Persona verschieden)
- **Datum:** 2026-08-22 (UTC)
- **Gegenstand:** Branch `0038-32`, Basis `main` `9601f1934`; REFs `9a698b7a4` (substanziell), `180e93f05` (Buchhaltung)
- **Implementierer:** `Worf-Elara-20260822T144500Z` (unprivilegiert, Dispatcher `worf` — vom Reviewer und dessen Dispatcher unabhängig); Claim `TODO-Worf-Elara-0038-32-20260822T144500Z.md` auf dem Branch
- **Checkpoint:** Knoten trägt `Integration review: mandatory` (provisorischer konservativer Default von `kathryn`; Architektenbestätigung steht spätestens bei Feature-0038-Abschluss aus)
- **Review-Branch/Worktree:** `review-0038-32-vorik-20260822T153500Z` / `.review-worktrees/0038-32-vorik-20260822T153500Z`
- **Verfahren:** `docs/pipeline/task-acceptance.md`; Kontrakt gepinnt auf den vollen Task-Text `0038-32` in `TODO.md` (Basis `9601f1934`, identisch auf `main` `77c4d0aee`). Prärequisit `0038-29` terminal und in der Basis erreichbar; keine weiteren nicht-akzeptierten Prärequisite im transitiven Abschluss.

## 1. Prüfergebnisse je Akzeptanzkriterium

| Kriterium | Ergebnis |
|---|---|
| Genau **ein** Ganzseiten-Publisher überlebt und ist benannt | **erfüllt** — `_src/tools/publish_public_site.sh`; `_src/publish.sh` entfernt; benannt in `docs/pipeline/tools.md`, `_src/README.md`, `docs/pipeline/automation-safety.md` |
| Beheben-oder-Stilllegen-Wahl **begründet, nicht angenommen** | **erfüllt** — Begründung dreifach aufgezeichnet (tools.md-Konsolidierungsblock, TODO-Completion-Record, Claim §Decision): die feste `PUBLIC_DIRS`/`PUBLIC_FILES`-Allowlist von `publish.sh` ist die strukturelle Ursache des 0019/0038-29-Vorfalls; die "ganzer Baum minus Ausschlüsse"-Selektion des Überlebenden hat diese Fehlerklasse nicht |
| Überlebender hat **Dry-Run**, der die volle beabsichtigte Wirkung vor jedem Schreiben meldet | **erfüllt** — `--dry-run` vorhanden (aus 0038-26), von Tests abgedeckt (`test_dry_run_requires_identity_but_not_remote` u.a.) |
| Force-Push: Entscheidung sagt **welches und warum**, nie still erreichbar | **erfüllt** — behalten, unverändertes 0038-26-Gate (`PUBLISH_ALLOW_FORCE_PUSH=1` **und** `PUBLISH_FORCE_APPROVAL_REF`); Begründung explizit in `docs/pipeline/tools.md` Punkt 2; Gate-Tests grün nachgelaufen |
| Stillgelegter Pfad entfernt oder inert; **jeder Aufrufer/jedes Dokument/Runbook** aktualisiert | **erfüllt mit Auflage** — Datei entfernt; `PublishShRetirementTests` beweist, dass kein getracktes Skript mehr dorthin ausruft; Repo-Grep des Reviewers: alle Restnennungen sind append-only-Historie (Reviews, Release-Records, Claims, Logs, geschlossene Task-Texte). Auflage AU-1 unten für zwei ASPICE-Snapshots |
| `docs/pipeline/tools.md` nennt je Situation genau ein Werkzeug; 0038-29-Abschnitt aktualisiert statt dupliziert | **erfüllt** — Faustregel-Absatz + Konsolidierungsblock in situ |
| `publish_approved_subtree.py` **nicht** eingefaltet | **erfüllt** — Datei im Diff unberührt |
| Keine Credentials/Remote-/Identitätsdefaults (`0038-26` steht) | **erfüllt** — `PUBLISH_REMOTE`/`PUBLISH_IDENTITY_*` weiter zwingend; Regressionstests grün |

## 2. Unabhängig nachvollzogene Validierung (vom Reviewer selbst ausgeführt, Review-Worktree)

- `python3 -m unittest _src.tests.test_publish_scripts` — **12/12 OK** (Exit 0), inkl. `test_export_reads_content_from_a_revision_other_than_the_worktree`
- `python3 -m unittest _src.tests.test_chore_tool_inventory` — **26/26 OK** (Exit 0)
- `python3 _src/tools/automation_safety.py --json` (repo-weit) — **verdict PASS**
- `python3 -m unittest _src.tests.test_automation_safety` — 120/121; der eine Fehler (`runner_transaction.py` `AUTO010`, `test_current_safe_aggregate_controls_do_not_regress`) ist vorbestehend, wird von Item `0038-33` (auf `main` `77c4d0aee` angelegt) getrackt; der Branch berührt weder `runner_transaction.py` noch `test_automation_safety.py`
- **Fehlerpfad-Härte des Fixes empirisch:** in einem Wegwerf-Repo scheitert der Aufruf mit ungültiger Revision hart mit **Exit 128** (`fatal: Not a valid object name`); `set -euo pipefail` am Skriptkopf macht auch einen `git archive`-Fehlschlag in der Pipe hart. Die alte Pipe-Falle (nur der zweite `tar` zählte) existiert nicht mehr: der erste `tar` ist entfernt, `git archive` ist erstes Pipe-Glied und wird von `pipefail` erfasst; die `EXPORT_LIST` stammt aus `git ls-tree` **derselben** Revision, sodass jeder gelistete Name im Archiv existiert (ein fehlender Name ließe zudem `tar -T` nonzero enden)
- **Regressionstest-Hermetik:** ausschließlich `tempfile`-Scratch-Repos, keine Netzwerk-Remotes, bereinigte Identitäts-Env; das Szenario ist exakt das Defektszenario (Commit A ausgecheckt, Export von Commit B verlangt, B-Inhalt gefordert)

## 3. Sonderfall Policy-Dateien (Prüfschwerpunkt 5)

- `_src/tools/automation_safety_policy.json`: Diff besteht ausschließlich aus `"line": 86 → 91` am `0038-16`-eigenen `AUTO003`-Eintrag für `publish_public_site.sh` plus einem append-only-Satz am Ende der Rationale (Original wörtlich erhalten). `evidence_sha256`, `owner_task`, `expires_after_task`, `kind`, Invariante unverändert. Präzedenz: 0038-26/`AUTO010`. **Keine fremde Disposition entfernt oder aufgeweicht.**
- `_src/tools/chore_tool_inventory_data.json`: Diff = ausschließlich Entfernung des fünfzeiligen Eintrags für das gelöschte `_src/publish.sh`. `chore_tool_inventory`-Tests 26/26, `--check` grün.

## 4. Merge-Vorschau gegen aktuelles `main` (Prüfschwerpunkt 6)

`main` stand zum Reviewzeitpunkt auf `9226adfdf` (weiter als die im Briefing genannten `77c4d0aee`; dazwischen: Anlage 0044-16/0038-33 und die 0038-30-Integration). `git merge-tree --write-tree main 0038-32` → **Exit 0, konfliktfrei** (Ergebnisbaum `1d6affab0`). `TODO.md` und `docs/pipeline/tools.md` sind beidseitig geändert, mergen aber automatisch; die `0038-32`-Zeile trägt im Ergebnis korrekt `[x]` + REF. `docs/pipeline/automation-safety.md` wurde auf `main` seit der Basis **nicht** geändert (0038-31 ist noch offen) — die im Briefing vermutete Überschneidung existiert nicht.

## 5. Befunde und Auflagen

- **AU-1 (Auflage, nicht blockierend):** `docs/ASPICE/05-evidence-register.md:107` und `docs/ASPICE/03-current-state-assessment.md:292` nennen `_src/publish.sh` noch als Publikationsmechanismus. Beide sind datierte Assessment-Snapshots, keine Runbooks und keine Aufrufer; kein Operator wird von dort auf ein Werkzeug geleitet. Bei der nächsten inhaltlichen Berührung der ASPICE-Dokumente ist die Nennung auf `publish_public_site.sh` zu aktualisieren bzw. als historisch zu markieren. Ebenso nennt `docs/brainstorming/` (nicht normativ) das alte Werkzeug.
- **Hinweis (kein Befund):** Der Checkpoint-Marker bleibt provisorisch; die Architektenbestätigung oder -herabstufung mit Begründung ist weiterhin spätestens beim Feature-0038-Abschluss fällig (unverändert aus dem Task-Text).

## 6. Verdikt

**accepted.** Alle Akzeptanzkriterien und die Definition of Done sind erfüllt; die Validierung wurde unabhängig wiederholt; die Policy-Datei-Änderungen sind minimal und korrekt; die Integration nach `main` ist konfliktfrei möglich. Der eigentliche Merge nach `main`, die `Acceptance: ✓`-Übernahme nach `main` und jede `DONE.md`-Bewegung sind **nicht** Teil dieses Reviews und verbleiben beim dafür autorisierten Integrationsschritt.

## 7. DEC-0044-013-Aufzeichnung (selbst gestarteter Reviewer)

- **Auftraggebende Identität:** `kathryn` (Projektleiter; Session-Persona Kathryn)
- **Reviewer-Persona:** Vorik, privilegierter Integrator — explizit angenommen, von der Persona des Erzeugers verschieden
- **Gegebener Kontext:** das untenstehende wörtliche Briefing; Lesezugriff auf das gesamte Repository; agent-inbox (Broadcasts gelesen, u.a. kathryns 0038-32-Anlage `1787407564711-33c2e398`)
- **Nicht gegebener Kontext:** keine Vorab-Bewertung des Implementierungsergebnisses durch den Dispatcher über die im Briefing wiedergegebenen Behauptungen des Implementierers hinaus; kein Kontakt zum Implementierer oder zu `worf` vor dem Verdikt; das Briefing benennt Prüfschwerpunkte und erwartete Konfliktstellen, nicht das Verdikt
- **Korrekturvermerk zum Briefing:** Die in Prüfschwerpunkt 6 erwartete parallele `automation-safety.md`-Änderung durch `0038-31` existiert auf `main` nicht (0038-31 ist offen, unintegriert); die Merge-Vorschau ist konfliktfrei. Das Briefing hat damit einen Konflikt vermutet, der nicht eintrat — kein Hinweis auf ein hingewiesenes Verdikt.
- **Wörtliches Briefing:** siehe `briefing-verbatim.md` im selben Verzeichnis (byteidentisch übernommen).
