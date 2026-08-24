# Integrationscheckpoint-Review — Task `0044-14`

- **Reviewer:** `Kathryn-BEllana-20260822T120000Z`, privilegierter Integrator (zed/claude-opus-5)
- **Zuweisung:** Dispatcher `kathryn` (Projektleiter), Managementanweisung 2026-08-22 („Machen Sie es so.")
- **Datum:** 2026-08-22
- **Gepinnte Baseline:** Branch `0044-14`, Tip `f885ad281`; `main` bei `6a688283b`;
  `git merge-base f885ad281 main` = `6a688283b` (`main` ist Vorfahr → `--ff-only` moeglich,
  eigene Vorgaengerkette nach `DEC-0044-008`).
- **Review-Worktree:** `.review-worktrees/0044-14-bellana-20260822T120000Z`, **detached** von
  `f885ad281` angelegt (der Branch war in `.worktrees/0044-14` ausgecheckt).
- **Autoritaetsgrenzen dieser Session:** kein Merge nach `main`, kein `DONE.md`, keine
  Feature-Schliessung, kein Push, keine Mutation des Root-Checkouts, kein `update-ref`.

## Ergebnis

**`accepted`.**

**Checkpointverdikt: Checkpoint BESTAETIGT** (nicht herabgestuft). Begruendung unten, §7.

## 1. Vorgaenger-Huelle

`0044-14` deklariert **keinen** `PREREQ`; die transitive nicht-abgenommene Vorgaenger-Huelle
ist leer. Einziger Nachfolger, der `0044-14` nennt, ist `0044-08` (`[ ]`, nicht `[d]`) — die
Nachfolgerpruefung nach `AGENTS.md` Schritt 5 schuldet keine Zustandsaenderung. Bestaetigt.

## 2. Abnahmekriterien — Einzelnachweis

| Kriterium | Befund |
|---|---|
| `AGENTS.md` und `branch-workflow.md` sagen: Mutation nur in vorgangseigenen Worktrees, Root wird nicht beschrieben | **erfuellt.** `AGENTS.md` §*Agents mutate only in item-owned worktrees…* (4 Regeln); `branch-workflow.md` §*Where agents mutate: item-owned worktrees only*. Beide nennen ausdruecklich, dass „Governance lebt auf `main`" die *Branch*, nicht das *Verzeichnis* meint — die Kollision `DEC-0044-010`/`DEC-0044-012` ist damit im Text aufgeloest, nicht umgangen. |
| Hygienepruefung als Schritt der Integrationsprozedur, maschinenlaufbar | **erfuellt.** Neuer Schritt 2 der Feature-Integrationsprozedur in `branch-workflow.md` (die Folgeschritte wurden korrekt auf 3–6 umnummeriert); Aufruf, Exit-Codes und Befundtabelle dokumentiert. Werkzeug ist stdlib-only, streng lesend. |
| Vermuteter Mechanismus mit Evidenz bestaetigt oder widerlegt; falls bestaetigt, noetige Auffrischung dokumentiert | **erfuellt — bestaetigt.** Hermetische Fixture `test_update_ref_reproduces_stale_worktree_signature` reproduziert: `git update-ref refs/heads/main <neu> <alt>` laesst `HEAD=<neu>`, Index und Dateien auf `<alt>`. Statt „Auffrischung" dokumentiert der Text die **strengere** Loesung: `update-ref` auf `refs/heads/main` untersagt, Vorruecken per `git -C <root> merge` aus dem Root (`DEC-0044-015`). Das erfuellt das Kriterium mit Ueberdeckung. Positiv hervorzuheben: der Befund ist als **Signatur** formuliert, nicht als Beweis, dass genau dieses Kommando lief. |
| Wiederherstellung aus `preserved/*`-Tags dokumentiert | **erfuellt.** §*Preserved snapshot tags and recovery*: alle acht Tags mit Commit und Inhalt, Aufbewahrungsregel, vier Wiederherstellungskommandos, Pflicht zum Nachtragen neuer Snapshots im selben Commit. **Unabhaengig verifiziert:** alle acht Tags existieren, alle acht Commit-Hashes stimmen exakt. |
| Registrierung in `docs/pipeline/tools.md` | **erfuellt.** Eigener Abschnitt mit Zweck, Aufruf, Exit-Codes, beiden Grenzen und Testdatei. |
| DoD: committet; Autoritaetsdokumente stimmen ueberein | **erfuellt.** `AGENTS.md`, `branch-workflow.md` und `tools.md` sagen dasselbe; die `AGENTS.md`-Kurzfassung verweist fuer Details auf `branch-workflow.md`, ohne abzuweichen. Gegen `DEC-0044-015` auf `main` Wort fuer Wort abgeglichen (Verfahren, Autoritaet, Verbote, erhaltene Kontrolle) — keine Abweichung, keine Ausweitung. |

## 3. Validierung — selbst nachgefahren, eigene Zahlen

| Lauf | Chakotay berichtet | **Mein eigener Lauf** |
|---|---|---|
| `python3 -m unittest test_check_integration_hygiene -v` aus `_src/tools/` | Ran 3 tests, OK | **Ran 3 tests in 5.454s, OK, EXIT=0**, Python 3.14.7 — uebereinstimmend |
| Live-Scan `check_integration_hygiene.py --repo .` | PASS, EXIT=0, 94 Worktrees | **PASS, EXIT=0, 95 registrierte Worktrees** — die 95. ist mein eigener Review-Worktree; die Abweichung ist erklaert und kein Befund |
| `automation_safety.py --json` | (nicht berichtet) | **verdict `PASS`**, 72 Befunde, **keiner** betrifft die Hygienepruefung |

pytest 9.1.1 im Scratch-venv habe ich **nicht** nachgefahren (Netzwerkinstallation ausserhalb
meines Auftrags). Der `unittest`-Pfad ist der in `tools.md` dokumentierte und deckt dieselben
drei Faelle ab; das ist keine offene Luecke, aber es ist eine Zahl, die ich nicht selbst habe.

## 4. Werkzeug gegen Prosa — die zwei benannten Grenzen, unabhaengig geprueft

**Grenze 1 (Index vs. `HEAD`) ist real und ich habe sie reproduziert.** In einem
Scratch-Repository mit sauberem Index und verfaelschter Arbeitsdatei liefert die Pruefung:

```
integration hygiene: PASS      EXIT=0
JSON:  "ok": true      "worktree_equals_index": false
```

Der Root-Restzustand vom 2026-08-21 waere also tatsaechlich als `PASS` durchgegangen.
Die Prosa bildet das **ehrlich und ausreichend** ab: `branch-workflow.md` und `tools.md`
sagen beide explizit, die Pruefung haette genau diesen Zustand nicht gefunden, und
Schritt 2 der Prozedur verlangt `git diff --quiet` im Root **zusaetzlich**. Die daraus
folgende Regel ist befolgbar: drei Ein-Zeilen-Kommandos plus ein Werkzeugaufruf, mit
eindeutigem Abbruchverhalten („abort, not tidy up"). Kein beschoenigender Text.

**Grenze 2 (`FOREIGN_STAGED_TREE` bei normaler Arbeit) ist ebenfalls korrekt abgebildet**:
als Ruhezustandsforderung, aufzuloesen vom Eigentuemer, **nie** durch Zuruecksetzen eines
fremden Worktrees. Praktisch befolgbar, weil es genau den Fall benennt, in dem ein
Integrator sonst versucht waere, fremden Zustand selbst „aufzuraeumen" — der Schaden,
den `DEC-0044-010` ueberhaupt erst ausgeloest hat.

**Nicht blockierende Empfehlung fuer `0044-08`:** `worktree_equals_index` wird bereits
berechnet und im JSON ausgegeben, erzeugt aber keinen Befund. Ein zusaetzlicher
Befundcode — mindestens fuer den Worktree, in dem `refs/heads/main` ausgecheckt ist —
wuerde Grenze 1 maschinell statt nur textlich schliessen. Das ist **kein Mangel gegen die
ausgeschriebenen Kriterien**: diese verlangen wortwoertlich „index equals `HEAD`, no
foreign staged trees, no stale worktree after a ref move", und alle drei sind umgesetzt.
Es ist eine Verbesserung, keine Nachforderung.

## 5. Wirksamkeit — belegt, mit einer Zahlabweichung

Die fuenf Befunde vom 2026-08-22 sind nachvollziehbar dokumentiert: Miles' Claim-Fortschritt
nennt die Fundorte einzeln, und fuer jeden gestagten Baum existiert ein `preserved/*`-Tag,
das ich verifiziert habe.

**Befund (geringfuegig, ausserhalb des Liefergegenstands):** Miles' Claim nennt **vier**
`FOREIGN_STAGED_TREE`-Fundorte (`0019-integration-alexander-…`, `0043-01`, `0044-01`,
`0044-01-task`), und die Tagtabelle in `branch-workflow.md` fuehrt entsprechend **vier**
`staged-*`-Tags. Der Vermerk in `TODO.md` (kathryn) spricht von **drei**. Der
Liefergegenstand ist richtig; die Zahl im `TODO.md`-Vermerk ist eine Untererfassung und
sollte beim Nachziehen nach `main` auf vier korrigiert werden. Kein Abnahmehindernis.

## 6. Autoritaetsgrenzen

- **Kein Ref bewegt.** Root-Checkout zum Reviewzeitpunkt: `HEAD` = `main`, Index leer,
  Arbeitsbaum ohne Abweichung — selbst nachgeprueft.
- **Schreibscope eingehalten.** Der Diff `main...f885ad281` beruehrt genau acht Pfade:
  die zwei Werkzeugdateien, drei Governance-Dateien, zwei Claims, und in `TODO.md` **eine
  einzige Zeile** (Marker `[ ]`→`[x]` plus Claim/REF/Validierung im selben Eintrag). Kein
  fremder Marker, kein fremder Claim, kein fremder Worktree beruehrt.
- **Checkpoint nicht ueberschritten**, `Acceptance: ✓` nicht gesetzt, Governance bewusst
  **nicht** selbst nach `main` gebracht — mit Verweis auf `DEC-0044-012`/`DEC-0044-015`
  und Uebergabe an die Projektleitung. Korrekt.
- **Zur selbstgemeldeten Abweichung (kein zweiter Worktree, Arbeit in Miles'
  `.worktrees/0044-14`): akzeptabel.** Der Claim war durch die Projektleitung in `TODO.md`
  ausdruecklich freigegeben, der Vorgaengerworktree war am zugewiesenen Tip sauber, und
  Git laesst denselben Branch nur einmal auschecken — die Alternative waere ein zweiter
  Checkout desselben Branches gewesen, den Git verweigert, oder ein detached Worktree, aus
  dem heraus nicht auf den Branch haette committet werden koennen. Entscheidend fuer die
  Bewertung ist weniger die Wahl als das Verhalten: er hat sie **von sich aus gemeldet**,
  statt sie zu verschweigen. Genau das ist das erwuenschte Verhalten. Fuer die Zukunft
  sollte `branch-workflow.md` bei Gelegenheit ausdruecklich sagen, dass die Uebernahme
  eines freigegebenen Vorgangsworktrees zulaessig ist — dann muss das kein Agent mehr als
  Abweichung melden.

## 7. Checkpointverdikt

Der Checkpoint war ein **provisorischer konservativer Platzhalter** der Projektleitung,
ausdruecklich zur Bestaetigung oder Herabstufung durch den Architekten freigegeben.

**Ich bestaetige ihn.** Begruendung: das Gegenargument im Backlog („fuegt eine Pflicht
hinzu, keine Faehigkeit") ist fuer die *Prosa* stichhaltig, greift aber am eigentlichen
Risiko vorbei. Der Vorgang liefert **eine Kontrolle, auf die sich Agenten verlassen
werden** — und dieses Review hat empirisch belegt, dass diese Kontrolle in genau dem
Szenario `PASS` meldet, das sie im Bewusstsein der Leser abzudecken scheint (§4). Der
Schutz besteht ausschliesslich darin, dass drei Dokumente diese Grenze ehrlich benennen.
Ein Text, der das kuenftig verliert oder verduennt, stellt die Ueberschaetzung wieder
her, vor der `DEC-0044-010` warnt. Das ist eine Wirkung ueber die eigene Arbeitseinheit
hinaus und rechtfertigt den Checkpoint eigenstaendig — unabhaengig davon, dass die Regel
festlegt, **wo jeder Agent im Projekt ueberhaupt arbeiten darf**.

Eine Herabstufung waere zudem die weiterreichende Handlung: sie entzieht kuenftigen
Aenderungen an diesen Texten die Pruefpflicht. Ich waehle die nicht autoritaetsausweitende
Option. Der Architekt kann bei `0044-08` weiterhin herabstufen; dieses Review liefert ihm
die Evidenz, die dagegen spricht.

## 8. Was ich nicht pruefen konnte

- **pytest 9.1.1 im Scratch-venv** (`/tmp/venv-0044-14`) — nicht nachgefahren, siehe §3.
- **Der eigentliche Live-Vorfall vom 2026-08-21** (138 Dateien / 28683 Loeschungen im
  Root) ist historisch; ich habe ihn nicht rekonstruiert, sondern nur die Existenz und
  Hash-Gleichheit der `preserved/*`-Tags verifiziert, die ihn konservieren.
- **Ob die Prosa nach dem Nachziehen auf `main` konfliktfrei bleibt** — `main` kann sich
  bis zum Merge bewegen. Zum Reviewzeitpunkt ist `main` Vorfahr des Branchtips, ein
  `--ff-only` also moeglich.
- **`0044-13`** (der `reference-transaction`-Hook) ist offen. Die Aussage „der Hook ist ein
  Netz, nicht das Tor" gehoert dorthin und ist hier zu Recht nicht mitgeliefert.

## Aufzeichnung

`Acceptance: ✓` — Task `0044-14`, Integrationscheckpoint bestanden.
Reviewer `Kathryn-BEllana-20260822T120000Z`, 2026-08-22, geprueftes Tip `f885ad281`,
Verdikt **accepted**, Checkpoint **bestaetigt**. Dieser Datensatz ist append-only; die
Uebertragung nach `main` obliegt `kathryn` nach `DEC-0044-015`.
