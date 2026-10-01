# Entscheidungsvorlage — tote Worktree-Registrierung `as-verify-0038-34`

**Dokumenttyp:** Entscheidungsvorlage. **Dies ist keine Entscheidung.**
**Ersteller:** Projektleiter `michael` (`agent:michael:roster-discovery-cursor:20260825T140300Z`),
Fähigkeitsklasse `privileged`, Rolle gemäß `DEC-ROLE-001` — **ohne Managementautorität**.
Der Projektleiter bereitet vor und moderiert; er trifft sie nicht.
**Adressat:** Management (aktueller User).
**Datum:** 2026-08-25.
**Anlass:** Live-Anweisung in der Michael-Cursor-Session, 2026-08-25 15:27 +02:
„Entscheidungsvorlage bitte.“
**Betroffene Arbeit:** Merge von `roster-discovery-cursor-20260825` (`fee0c1fd6`,
`DEC-0044-022`) nach `main`; danach Feature-Merges in `0037` (mindestens
`0037-11.01`, `0037-17`). Hygiene-Finding `WORKTREE_UNAVAILABLE`.

---

## 0. Zusammenfassung für das Management

Eine Zeile in `docs/pipeline/agent-roster.md` (Cursor statt Grok) liegt fertig
auf einem Branch. Der Shared-Root ist dafür wieder sauber. Der Integrator
`paul` hat die Hygiene **korrekt gestoppt**, weil Git noch eine Worktree-Registrierung
für ein Verzeichnis führt, das nicht mehr existiert.

Das ist **nicht** die Cursor/Grok-Entscheidung. Die hat nur das Roster-Overlay
erlaubt. Die tote Registrierung braucht eine eigene, ausdrückliche Recovery.

| | Entscheidung | Empfehlung |
|---|---|---|
| **E1** | Tote Registrierung `/private/tmp/as-verify-0038-34` | **A — nach Snapshot nur diese Registrierung entfernen** |

**Dringlichkeit:** sofort. Solange die Registrierung steht, ist jeder
`main`-Advance und jedes Feature-Merge, das die Hygieneprüfung laufen lässt,
blockiert — unabhängig davon, wie viel Item-Arbeit bereits `[x]` ist.

---

## 1. Beweislage

Nachgemessen 2026-08-25, unabhängig von der Mailbox.

| Pin | Wert |
|---|---|
| `main` | `28d7a00918498685b1fc13b711840df415142ecf` |
| Roster-Kandidat | `roster-discovery-cursor-20260825` = `fee0c1fd63c1c59a9a6768e576271a68c2e30634` (`DEC-0044-022`) |
| Shared-Root `docs/pipeline/agent-roster.md` | kein Diff gegen `HEAD` |
| Hygiene (paul, read-only) | `--repo /Users/tobias.anton/devel/autodocs --candidate-ref fee0c1fd63c1c59a9a6768e576271a68c2e30634` → `FAIL`, `WORKTREE_UNAVAILABLE: /private/tmp/as-verify-0038-34`, Exit `1` |
| Mail (Koordination, keine Autorität) | jean-luc `1787659907488-ce91b4f7`; paul `1787660384200-59f3b28a` |

Git-Registrierung:

```
worktree /private/tmp/as-verify-0038-34
HEAD 9bcf87edb1ccd0384a9d86910a061a8e3de64fda
detached
prunable gitdir file points to non-existent location
```

- Das Verzeichnis `/private/tmp/as-verify-0038-34` **fehlt**.
- Metadaten liegen noch unter `.git/worktrees/as-verify-0038-34/` (`gitdir` zeigt
  auf `/private/tmp/as-verify-0038-34/.git`).
- `HEAD` dort ist `9bcf87edb` — dasselbe Objekt wie Tip von Branch `0038-34`
  (`bookkeeping(0038-34): mark [x] with real substantive REFs`). Der Commit ist
  über `0038-34` und `review-0038-34-belanna-20260825` erreichbar. **Kein
  einzigartiger Commit geht verloren**, wenn die Registrierung wegfällt.
- Der **Index** dieser Registrierung weicht von `9bcf87edb` ab: 11 Pfade,
  Netto 1647 Löschungen gegenüber dem Commit (u. a. `check_adversarial_evidence.py`
  und die `0038-34-analysis/`-Dateien fehlen im Index). Das ist ein älterer
  Verify-Index, kein neuer unveröffentlichter Feature-Stand. Trotzdem gilt
  `DEC-0044-015`: Zustand, der in keinem Branch sitzt, wird **vor** dem Löschen
  als `preserved/*` gesichert.
- Derzeit ist **nur diese eine** Worktree-Registrierung `prunable`. Ein globales
  `git worktree prune` träfe heute nur sie — trotzdem soll die Freigabe **namentlich
  diesen einen Pfad** nennen, nicht „alle prunablen Worktrees“.

Was das **nicht** ist:

- kein zweites Roster-Overlay (Root-Datei ist sauber);
- keine Freigabe, 182 Worktrees unter `.worktrees/` zu löschen (Benjamin-Bitte,
  bereits abgelehnt);
- kein Schließen von `0020-01` (steht `[u]` VERTAGT).

---

## 2. Der eigentliche Punkt

Die Hygieneprüfung muss jede registrierte Worktree-Pfadexistenz prüfen
(`WORKTREE_UNAVAILABLE` in `docs/pipeline/branch-workflow.md`). Ein fehlendes
`/tmp`-Verify-Verzeichnis von `0038-34` ist kein inhaltlicher Einwand gegen
`DEC-0044-022`. Es ist ein **toter Zeiger**, der die Prüfung fail-closed hält.

Die Cursor-Entscheidung hat Recovery des Roster-Overlays autorisiert, nicht
das Entfernen fremder Worktree-Registrierungen. Deshalb liegt E1 bei dir.

---

## 3. Optionen (E1)

- **A — Nach Snapshot nur diese Registrierung entfernen (Empfehlung).**
  1. Integrator `paul` sichert den Index/Metadatenbaum der Registrierung als
     `preserved/*`-Tag (Inhalt: Index zu `9bcf87edb`, nicht der fehlende
     Dateibaum unter `/private/tmp`).
  2. Danach nur:
     `git worktree remove /private/tmp/as-verify-0038-34`
     (bei Bedarf `--force`, weil der Pfad fehlt). **Kein** globales
     `git worktree prune` über andere Registrierungen.
  3. Hygiene erneut gegen `fee0c1fd6`. Bei PASS: Merge nach `main` durch `paul`
     (nicht durch die Projektleitung). Danach können Feature-Merges in `0037`
     wieder versucht werden, sofern keine *neue* Hygiene-Sperre erscheint.
- **B — Stehen lassen.**
  Registrierung bleibt. `paul` bleibt gestoppt. `DEC-0044-022` und die
  `[x]`-Item-Branches von Discovery (`0037-11.01`, `0037-17`, `0037-10.01`,
  `0037-22`, `0037-23.01`) bleiben außerhalb von `main` / Feature `0037`.
- **C — Verzeichnis wieder anlegen, Registrierung behalten.**
  Ein leeres oder neu ausgechecktes `/private/tmp/as-verify-0038-34` kann
  `WORKTREE_UNAVAILABLE` in `INDEX_NOT_HEAD` / `FOREIGN_STAGED_TREE` verwandeln
  (Index weicht ab). Löst den Stau nicht zuverlässig und belebt ein
  Verify-Worktree ohne Auftrag.

**Empfehlung: A.** Der Commit ist auf Branch `0038-34` erreichbar. Der Index
ist ein veralteter Verify-Stand; Snapshot schützt vor der theoretischen
Einzigartigkeit. B ist nur sinnvoll, wenn du Integrationen bewusst weiter
blockieren willst. C ist schlechter als A.

---

## 4. Was nach A *nicht* mitentschieden ist

- Kein Massen-Prune anderer Worktrees.
- Kein Advance von `main` durch die Projektleitung.
- Keine Abnahme, kein Checkpoint, kein `DONE.md`.
- Keine Änderung an `0020-01`.

---

## 5. Wie du antwortest

Eine Zeile reicht, zum Beispiel `A` oder `B` oder `C`.
Mailbox-Nachrichten sind keine Entscheidung.

---

## 6. Disposition (Management, 2026-08-25 15:33 +02)

**Ausgewählt: A**, plus ausdrücklicher Satz, dass sekundäre Worktrees den
kanonischen Checkout weiter blockieren dürfen. Wortlaut:

> Ja, toten Eintrag entfernen. Das Vorhandensein sekundärer Worktrees darf
> generell einen checkout ins Repository vom kanonischen Pfad aus blockieren.

Aufgezeichnet als `DEC-0044-023`. Snapshot-Tag
`preserved/as-verify-0038-34-index-20260825` (`d825cff53560878bcfeb4e504113945a21ae0abc`).
Kein Gate-Umbau, kein Massen-Prune.
