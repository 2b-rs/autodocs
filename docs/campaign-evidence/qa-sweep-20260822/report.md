# QA-Sweep 2026-08-22 — Kathryn-Harry-20260822T003000Z

Rolle: QA-Manager (unabhaengige Pruefung, keine Abnahme, keine Integration).
Worktree: `.worktrees/qa-harry-20260822T003000Z`, Branch `qa-sweep-20260822`, Basis `main` (f332e62f7).

## Aufgabe A — Nachgeholte Testsuiten

Scratch-venv unter `.worktrees/qa-harry-20260822T003000Z/.venv-qa` (python3 -m venv; pip install pytest lxml).
`python -m pytest --version` -> pytest 9.1.1.

### `_src/tests/test_build_ledger.py`

`python -m pytest _src/tests/test_build_ledger.py -v`

**26 passed, 12 subtests passed, 0 failed.** Keine roten Tests.

### `_src/tests/test_legacy_handoff_manifest.py`

`python -m pytest _src/tests/test_legacy_handoff_manifest.py -v`

**34 passed, 0 failed.** Keine roten Tests.

Gesamt: **60 von 60 Tests gruen.** Kein einziger roter Test, keine Fehlermeldung zu berichten.
Der am 2026-08-22 wiederhergestellte Inhalt (Commit `27930dc9c`) ist damit unabhaengig
bestaetigt: byteexakt UND funktionsfaehig unter echter Testausfuehrung, nicht nur "importiert sauber".

## Aufgabe B — Historien-Sweep: einmaliger Vorfall oder Muster?

Methode:
1. `git log --since="30 days ago" --no-merges --numstat main` fuer alle Nicht-Merge-Commits ausgewertet,
   nach Loeschungsueberschuss (deletions - insertions) sortiert (569 Commits im Zeitraum, davon
   534 Nicht-Merge-Commits ausgewertet).
2. Fuer jeden Commit mit deutlichem Loeschungsueberschuss (>50 Zeilen netto) die Commit-Nachricht
   gegen den tatsaechlichen Inhalt geprueft.
3. Zusaetzlich alle 35 Merge-Commits im Zeitraum einzeln gegen ihren ersten Elternteil verglichen
   (`git diff --shortstat <merge>^1 <merge>`), um zu pruefen, ob ein Merge selbst (nicht nur ein
   gewoehnlicher Commit) nach main geloeschten Inhalt einbringt. Alle 35 sind netto-positiv
   (Additions > Deletions); keiner zeigt das Loeschungsmuster des Vorfalls.

### Bestaetigter Verlust (heute repariert, nicht mehr offen)

- **`4b95d99db`** (DEC-0044-012, 2026-08-21 17:39:43, direkt auf main) — geloescht: 4869 Zeilen aus
  drei bereits integrierten, unbeteiligten Vorgaengen: `0038-16.01`
  (`legacy_handoff_manifest.py`, `test_legacy_handoff_manifest.py`,
  `legacy-handoff-manifest-v1.json`, `legacy-handoff-manifest.md`), `0043-02`
  (`build_ledger.py`, `test_build_ledger.py`, `build-ledger.md`, `build-ledger.jsonl`), `0038-28`
  (`docs/pipeline/fixtures/0038-28/reverification.json`, `README.md`). Alle drei Branches waren
  nachweislich Vorfahren von `4b95d99db^`. Repariert durch `27930dc9c` (2026-08-22 01:06:21,
  Branch `repair-4b95d99db`) — 19 von 21 Pfaden byteexakt aus `4b95d99db^` zurueckgeholt, `TODO.md`
  chirurgisch per Reverse-Apply korrigiert. **Verifiziert in diesem Sweep:** alle genannten Pfade
  existieren aktuell auf main (`1edc98ec1`), UND (Aufgabe A) die zugehoerigen Testsuiten laufen
  gruen. Status: **nicht mehr offen.**

### Erklaerte/legitime Loeschungen (kein Verlust)

Commits mit auffaelligem Loeschungsueberschuss, deren Nachricht die Loeschung deckt und deren
Inhalt beim Nachlesen zur Nachricht passt:

- `ac2e9f5376` "spec: migrate schema language..." (del=20474/add=17295, 3535 Dateien) — grossflaechige
  Schema-Migration, Loeschung und Neuanlage etwa im Gleichgewicht, durch die Nachricht erklaert.
- `2d6493cafb` "feat(0038-27): reconcile automation-safety dispositions..." (del=1496/add=19) —
  Nachricht listet jede Loeschung einzeln auf (6 retirierte One-off-Skripte, 2 Findings am
  Ursprung behoben); inhaltlich gepruefte, beabsichtigte Retirierung.
- `3660701735` "closure(0040): reconcile and remove carried predecessor claims..." (del=905/add=115)
  — beabsichtigtes Entfernen abgeschlossener Claim-Dateien nach Feature-Integration.
- `505caf6f75` "chore: remove superseded CLI scripts ..." (del=619/add=0) — Dateiname im Betreff
  deckt die Loeschung vollstaendig.
- `0f21b9f14b` "Policy: reconcile context-efficiency claim" (del=60/add=0) — Entfernen einer
  temporaeren Koordinations-Claim-Datei nach Verifikation des zugehoerigen Substantive-Ref;
  Commit-Body nennt Datei und Grund.
- `baeb530b6e` (Uebersetzung, del=369/add=266), `183a4633d9`, `508537ec13`, `bad253b238`,
  `410020f693` "Remove BACKLOG.md", `5e2e62cab7` "Remove one-shot local initialization script" —
  jeweils Datei-/Zweck im Betreff genannt, Loeschung beabsichtigt und plausibel.

### Unklare Faelle

Keine. Jeder Commit mit signifikantem Loeschungsueberschuss im 30-Tage-Fenster liess sich anhand
von Commit-Nachricht und Stichprobe des Diffs eindeutig als legitim oder (im einen Fall) als
Vorfall einordnen. Insbesondere zeigte keiner der 35 Merge-Commits im Zeitraum das Loesch-Muster
von `4b95d99db` (ein Merge kann per Definition auch unbeabsichtigt Fremdarbeit "verlieren", wenn
er einen veralteten Vorgaengerbaum bringt — das war hier nicht der Fall).

### Ergebnis

`4b95d99db` ist nach dieser Stichprobe der **einzige** Vorfall dieser Art in den letzten 30 Tagen
auf `main`. Kein weiterer offener Verlust gefunden. (Vorbehalt: reine `--numstat`-Schwellenwert-
Heuristik auf Nicht-Merge-Commits plus Merge-Elternteil-Diff deckt keine Faelle ab, in denen
Loeschung und Neuanlage sich in der Zeilenzahl exakt die Waage halten, aber inhaltlich anderes
Material ersetzen — dafuer waere ein pfadgenauer Abgleich noetig, siehe Aufgabe C.)

## Aufgabe C — Vorschlag fuer ein dauerhaftes Netz

Siehe Eintrag im Suggestion-Log von `AGENTS.md` (in diesem Worktree committet, nicht auf main).
Kernidee: ein **Pre-Merge-Pfad-Erhaltungscheck**, der vor jedem Vorruecken von `refs/heads/main`
(direkter Commit ODER Merge) prueft, ob ein Pfad verschwindet oder sich stark verkuerzt, der auf
main via einem bereits als `[x]`/`[w]` verbuchten Item-Branch eingebracht wurde, dessen Tip
Vorfahre des neuen `main`-Standes ist. Bei Fund: Vorgang **blockieren**, nicht automatisch heilen,
und eine strukturierte Meldung an den commitenden/mergenden Agenten sowie per agent-inbox an
`kathryn` (oder die jeweils aktuelle Projektleitung) ausgeben. Ergaenzend ein taeglicher
Abgleichsbericht (`main` gegen alle bekannten integrierten Branch-Tips aus `TODO.md`/`DONE.md`
REF-Feldern), der denselben Pfad-Verschwindet-Test nachtraeglich als Netz faehrt, falls der
Pre-Merge-Hook umgangen oder nicht ausgefuehrt wurde — analog zur bereits beschlossenen
Reference-Transaction-Hook-Philosophie aus DEC-0044-008: der Hook ist ein Netz, nicht das Tor;
massgeblich bleibt die Pruefung am Integrationscheckpoint.
