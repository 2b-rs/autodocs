# Fundstellenliste — Feature 0041, Tasks `0041-02` und `0041-03`

**Status:** Aufklärungsprodukt. Keine Autoritätsdokumente wurden in diesem Durchgang
geändert. Grundlage: [`re-intake-worker-isolation-and-checkin.md`](re-intake-worker-isolation-and-checkin.md)
(`RQ-CI-01`…`05`, `RQ-REF-01`…`03`, Befunde H und K), `TODO.md` Feature-0041-Abschnitt
(Zeilen 76–120), `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`,
[`branch-workflow.md`](../pipeline/branch-workflow.md),
[`task-acceptance.md`](../pipeline/task-acceptance.md).

**Methode:** `grep -n` (case-insensitive) nach `bookkeeping`, `hash`, `REF`, `two-commit`
über `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `TODO.md` (nur Kopf + Feature-0041-
Block), sowie den gesamten Baum unter `docs/pipeline/`. Jeder Treffer wurde gelesen und
klassifiziert. Vier Kategorien laut Auftrag:

- **A** — schreibt/beschreibt einen separaten Bookkeeping-Commit
- **B** — beschreibt die Hash-Injektion des substantiellen Commits in den Bookkeeping-Commit
- **C** — setzt `REF` als Bedingung für `[x]`/`[w]`
- **D** — erwähnt `REF` im Zusammenhang mit Abnahme (Kontext; meist **nicht** zu ändern,
  teils sogar die künftige Ziel-Stelle von Entscheidung 3)

## Tier 1 — Primäre Autoritätsdokumente (im Feature-DoD namentlich genannt)

`TODO.md`, `AGENTS.md`, `SANDBOX.md`, `branch-workflow.md`, `task-acceptance.md` sind
laut Feature-DoD (`TODO.md:87`) die fünf Dokumente, die am Ende „wortwörtlich“
übereinstimmen müssen.

| # | Datei:Zeile | Zitat (gekürzt) | Kategorie | Betrifft | Was daraus werden muss |
|---|---|---|---|---|---|
| 1 | `TODO.md:17` | „`[w]` … Record a `Reason:` and real disposition `REF`.“ | C | 0041-03 | `REF` aus der `[w]`-Definition entfernen; Verweis auf den `[x]`→`✓`-Übergang setzen. |
| 2 | `TODO.md:18` | „`[x]` … and real substantive `REF` are committed.“ | C | 0041-03 | Dieselbe Streichung für `[x]`. Dies ist die zentrale Marker-Definition im Header — höchste Priorität. |
| 3 | `TODO.md:19` | „…full reachable review `REF` as defined by `docs/pipeline/task-acceptance.md`.“ | D | beides (Zielstelle) | Bleibt inhaltlich bestehen — ist bereits die *Acceptance*-REF-Stelle. Ggf. ergänzen, wann sie optional ist (`RQ-REF-03`), sonst nur zu prüfen, dass sie nach Streichung von #1/#2 weiterhin die *einzige* REF-Bedingung im Header ist. |
| 4 | `TODO.md:21` | „Unless a Task states a stricter gate, `[x]` requires … and the commit `REF`; `[w]` requires … reason, and `REF`.“ | C | 0041-03 | Kernsatz. `REF` aus dem `[x]`/`[w]`-Satz entfernen; ersetzen durch den neuen Trailer-Anforderungssatz (Ticket-ID + Base-Ref) für `[x]`/`[w]`, `REF` in den Abnahme-Satz (#3) verschieben. |
| 5 | `AGENTS.md:56` | „…complete its implementation only with the required committed deliverables, validation, evidence, and real REF.“ (Autonomous backlog repair, Paket-Abschluss eines Eltern-Tasks) | C | 0041-03 | `real REF` aus der Aufzählung streichen. |
| 6 | `AGENTS.md:78` | „`[x]` and `[w]` mean that implementation … is committed with the required evidence and real `REF`; they satisfy ordinary implementation start gates but do not satisfy Feature closure.“ | C | 0041-03 | Kernsatz im Abschnitt „Implementation completion and privileged acceptance“. `REF` streichen/verschieben. |
| 7 | `AGENTS.md:84` | „Acceptance evidence is committed before a separate path-isolated bookkeeping commit adds `Acceptance: ✓` with the real review REF and required digests.“ | D | 0041-03 (Zielstelle) | **Nicht** die durch 0041-02 abgeschaffte Bookkeeping-Art — das ist der *Abnahme*-Bookkeeping-Commit, der bleibt. Ggf. Formulierung ergänzen, wann `REF` hier optional ist. |
| 8 | `AGENTS.md:96` (Schritt 4, „Completing implementation work“) | „After the substantive commit hash is known and reachable, update authoritative implementation bookkeeping: mark `[x]` or `[w]`, add the required real `REF`, …“ | A, B (implizit), C | beides | Schritt neu fassen: kein Warten auf „hash is known and reachable“ mehr nötig, da derselbe Commit den Trailer trägt; `REF`-Pflicht streichen. |
| 9 | `AGENTS.md:98` (Schritt 6) | „Commit implementation bookkeeping separately unless the capability-specific execution procedure in `SANDBOX.md` permits a safe transaction that creates both commits and injects the substantive hash into the bookkeeping commit. Never amend a commit to add its own hash.“ | A, B | 0041-02 | **Die deutlichste Fundstelle.** Ganzer Satz beschreibt exakt den Mechanismus, den `RQ-CI-01/05` abschafft. Muss durch den Trailer-Mechanismus ersetzt werden. „Never amend…“-Klausel bleibt sinnvoll (gilt weiter für andere Fälle) und sollte nicht ersatzlos verschwinden. |
| 10 | `AGENTS.md:99` (Schritt 7) | „…complete the independent acceptance procedure and its separate evidence/bookkeeping commits.“ | D | — | Betrifft die *Abnahme*-Bookkeeping-Commits, nicht `[p]`→`[x]`. Unverändert lassen, nur prüfen, dass „bookkeeping commits“ hier nicht fälschlich als das gestrichene Muster gelesen wird. |
| 11 | `AGENTS.md:108` (Check-in provenance) | „…A bookkeeping commit references the substantive provenance instead of duplicating it unless separately prompted.“ | A (tangential) | 0041-02 | Allgemeine Provenance-Regel, die *jeden* Bookkeeping-Commit betrifft (auch künftige Abnahme-Bookkeeping-Commits). Bleibt anwendbar, sollte aber nicht mehr implizieren, dass ein `[p]`→`[x]`-Bookkeeping-Commit der Normalfall ist. |
| 12 | `AGENTS.md:164–168` (Suggestion log, Zed-Eintrag) | „…commit-substantive… commit-bookkeeping… finalize-claim…“ / „two-commit REF closure“ (indirekt über referenzierte Datei) | A, C (historisch) | — | **Nicht editieren** — Suggestion-Log ist laut eigener Regel append-only, keine andere Session darf fremde Einträge umschreiben. Nur zur Kenntnis: der Vorschlag beschreibt das alte Muster; bei Gelegenheit könnte ein neuer Suggestion-Log-Eintrag auf die Ablösung verweisen, das ist aber nicht Teil dieses Tasks. |
| 13 | `SANDBOX.md:68` | „…the authorized path-limited commit/bookkeeping transaction.“ | A | 0041-02 | Generischer Verweis auf „die“ Commit/Bookkeeping-Transaktion im Batching-Absatz für throttled Sessions. Nach Wegfall des Zweischritts umformulieren (z. B. „the authorized path-limited check-in“). |
| 14 | `SANDBOX.md:84` | „Its first bounded runner transaction must qualify discovery, validation, path-limited commits, **two-commit REF bookkeeping**, failure recovery, and slot cleanup on fixtures…“ | A, B, C | beides | Wörtlich „two-commit REF bookkeeping“ — exakt das abzuschaffende Muster, in einer Qualifikationsanforderung für den Feature-0037-Bootstrap-Agenten. Muss auf den neuen Trailer-Mechanismus umgestellt werden (oder als historische Qualifikation markiert werden, falls diese Bootstrap-Qualifikation bereits abgeschlossen ist — das wäre separat zu prüfen). |
| 15 | `SANDBOX.md:94` | „After the substantive commit hash is known and reachable, the agent updates implementation bookkeeping … `[x]`/`[w]`, real `REF`, … Bookkeeping is committed separately unless an approved runner transaction safely creates both commits and injects the first hash into the second. … Never amend a commit to add its own hash.“ | A, B, C | beides | **Zweitdeutlichste Fundstelle**, das Sandbox-Pendant zu `AGENTS.md:98`. Enthält beide Entscheidungen in einem Absatz (Bookkeeping-Zweischritt UND `REF`-Pflicht). Muss vollständig neu gefasst werden. |
| 16 | `SANDBOX.md:96` | „…never inferred from runner success or requested through generic shell/bookkeeping actions.“ | D | — | Bezieht sich auf Abnahme-Bookkeeping (Verbot, sie generisch anzufordern), nicht auf den gestrichenen Zweischritt. Vermutlich unverändert lassbar, aber Formulierung nach der Änderung erneut lesen — „bookkeeping actions“ könnte doppeldeutig wirken, sobald der Normalfall kein Bookkeeping-Commit mehr ist. |
| 17 | `docs/pipeline/branch-workflow.md:170` | „…moves the Feature to `DONE.md` via the path-isolated bookkeeping commit that `task-acceptance.md` requires.“ | D | — | Feature-*Closure*-Bookkeeping-Commit (Abnahme-Ebene), nicht der `[p]`→`[x]`-Zweischritt. Unverändert lassen; nur sicherstellen, dass niemand diesen Satz beim Aufräumen versehentlich mitstreicht. |
| 18 | `docs/pipeline/branch-workflow.md:289` | „…implements, commits work + claim, marks `[x]`.“ (Worked example „Linear Feature, one grunt“) | A (implizit) | 0041-02 | Sehr knapp formuliert, sagt nicht explizit „zwei Commits“, ist aber auch nicht explizit mit dem neuen Trailer vereinbar. Niedrige Priorität, aber der Text nennt zufällig `0041-02` selbst als Beispiel-ID im zweiten Worked Example — beim Überarbeiten prüfen, ob das Beispiel den neuen Trailer zeigen sollte. |
| 19 | `docs/pipeline/task-acceptance.md:74` | „The implementation owner completes the existing claim at `[x]` or `[w]`, **commits the substantive result and bookkeeping**, finalizes the implementation claim, …“ | A | 0041-02 | Explizite Zweischritt-Beschreibung aus Sicht des Abnahme-Dokuments. Muss zu „commits the substantive result (carrying the check-in trailer)“ werden. |
| 20 | `docs/pipeline/task-acceptance.md:79` (Abnahmepaket-Liste, Punkt 2) | „exact substantive **and bookkeeping** commits, candidate tree, expected parent/base, and authority epoch;“ | A | 0041-02 | Das Abnahmepaket verlangt heute zwei Commit-Referenzen zum Pinnen der Baseline. Nach 0041-02 gibt es nur noch den substantiellen Commit (mit Trailer) — Formulierung anpassen, sonst verlangt das Abnahmepaket künftig etwas, das nicht mehr entsteht. |
| 21 | `docs/pipeline/task-acceptance.md:42–51` (Muster-Rendering `**Acceptance:** ✓`) | „`- **Review REF:** \`<full reachable 40-hex commit>\`“ | D | 0041-03 (Zielstelle) | Zielort für die verschobene `REF`-Pflicht. `RQ-REF-03` verlangt, explizit zu benennen, wann sie Pflicht/optional ist — dieser Abschnitt braucht **neuen** Text, nicht nur eine Streichung anderswo. |
| 22 | `docs/pipeline/task-acceptance.md:64` | „…treating privilege, a green command, or a Task `REF` as acceptance.“ (Non-bypass-Regel) | D | — | Bleibt gültig und wird nach der Verschiebung sogar wichtiger (ein `REF` an `[x]`/`[w]` existiert dann evtl. gar nicht mehr). Nur auf Kohärenz prüfen, keine inhaltliche Änderung nötig. |

## Tier 2 — `PRIVILEGED.md` (nicht im Feature-DoD namentlich gelistet, aber strukturell identische Instruktion)

`PRIVILEGED.md` steht nicht in der Fünfer-Liste des Feature-DoD, enthält aber exakt
dasselbe Muster für privilegierte Sessions, die selbst substantielle Arbeit
abschließen. Ohne Angleichung entsteht hier derselbe `T8`-Widerspruch, den das
Feature beseitigen soll — ich flagge es daher trotzdem.

| # | Datei:Zeile | Zitat (gekürzt) | Kategorie | Betrifft | Was daraus werden muss |
|---|---|---|---|---|---|
| 23 | `PRIVILEGED.md:118` (Schritt 8, Abnahmeverfahren) | „commit review evidence first, then use a separate path-isolated bookkeeping commit for `Acceptance: ✓` with the real review REF and required digests.“ | D | 0041-03 (Zielstelle) | Abnahme-eigener Bookkeeping-Commit — bleibt, ist die *korrekte* neue Heimat der `REF`-Pflicht. |
| 24 | `PRIVILEGED.md:138` (Abschnitt „Commits and completion“) | „For substantive Task completion, create the substantive commit before recording its real hash in authoritative bookkeeping. Commit bookkeeping separately unless an approved transaction safely creates both commits without self-reference or partial-state ambiguity.“ | A, B | 0041-02 | Privilegiertes Gegenstück zu `AGENTS.md:98` / `SANDBOX.md:94`, für den Fall, dass ein privilegierter Agent selbst implementiert. Sollte im selben Zug korrigiert werden — sonst gilt für Privilegierte weiterhin der alte Zweischritt. **Nicht in der Fünfer-Liste des Feature-DoD — Entscheidung, ob `0041-02`/`-03` das mit erledigen oder ob ein Folge-Task nötig ist, liegt beim Menschen.** |

## Tier 3 — Sekundäre Prozess-/Werkzeugdokumentation (nicht Feature-DoD-Scope, gleiches Muster)

Diese Dokumente sind entweder als „Draft“/„review-ready“ für das noch nicht
vollzogene Feature `0037`-Cutover markiert (laut eigenem Status-Header und laut
`AGENTS.md:5`: „Until Feature `0037` completes its authorized cutover, `TODO.md`
and `DONE.md` are the authoritative backlog“) oder beschreiben ein bereits
implementiertes Werkzeug (`runner_transaction.py`), das den Zweischritt technisch
ausführt. Sie sind **nicht** Teil der fünf im Feature-DoD genannten Dokumente und
wurden daher nicht in die primäre Fundstellenliste aufgenommen — ich liste sie
trotzdem, weil sie beim nächsten Lesen denselben Widerspruch erzeugen, sobald
`0041-02`/`-03` landen.

| Datei:Zeile | Zitat (gekürzt) | Kategorie | Hinweis |
|---|---|---|---|
| `docs/pipeline/agent-execution.md:13` | „…path-limited substantive commit, and optional separate bookkeeping commit that injects a real prior `REF`.“ | A, B, C | Beschreibt exakt das alte Muster als „allowed runner transaction“. Status: „review-ready contract for Task `0037-45`“, nicht aktuell bindend, aber technisch das, was `runner_transaction.py` heute ausführt. |
| `docs/pipeline/runner-transaction.md:42` | „**Never amend:** the substantive and bookkeeping commits are created as separate objects. The bookkeeping commit records the real substantive hash.“ | A, B | Implementierte Werkzeugdoku für `_src/tools/runner_transaction.py` — das Werkzeug selbst führt den Zweischritt technisch aus. Eine reine Dokumentänderung in `AGENTS.md`/`SANDBOX.md` widerspräche dann dem tatsächlichen Werkzeugverhalten, bis das Werkzeug angepasst wird. **Das ist der Punkt mit dem größten praktischen Risiko**, siehe Rückmeldung unten. |
| `docs/pipeline/runner-transaction.md:190,231,240` | „Prepare REF bookkeeping commit object“ / „two-commit REF closure“ / „`close-task-v1`: … a parented REF bookkeeping commit that closes the Task…“ | A, B, C | Gleiche Werkzeugdoku, weitere Fundstellen. |
| `docs/pipeline/task-acceptance.md:142,180` | „A separate path-isolated bookkeeping commit adds `Acceptance: ✓`…“ / „…separate evidence and bookkeeping commits…“ | D | Abnahme-eigenes Muster, bleibt — bereits oben in Tier 1 als Kontext erwähnt, hier nur der Vollständigkeit halber referenziert. |
| `docs/pipeline/issue-lifecycle.md:54` | „…the closer follows the two-commit rule: first commit the substantive deliverable …, then commit the lifecycle/bookkeeping update carrying that first commit's `REF`.“ | A, B, C | Explizit „two-commit rule“. Status: „Draft, review-ready … Until the authorized Feature-0037 cutover, committed `TODO.md`, `DONE.md` … remain authoritative“ — also selbst nicht aktuell bindend, aber inhaltlich zu korrigieren, bevor `0037` cutover. |
| `docs/pipeline/legacy-task-editor.md:135,136,138` | „render `[x]`, one full REF, and closure evidence.“ / „render `[w]`, full disposition REF …“ / „`ref-injection`… insert when no visible REF exists…“ | C | Werkzeugdoku für `_src/tools/legacy_task_editor.py`, das laut eigenem Status bis `0038-05.02` ohnehin nur `verified-coordinator-required` liefert (keine autoritative Mutation). Trotzdem inhaltlich an die neue REF-Semantik anzupassen, sobald das Werkzeug reaktiviert wird. |
| `docs/pipeline/tools.md:95` | „Fail-closed Legacy-Transaktion für `generate → validate → promote → substantive commit → REF bookkeeping → claim finalization`…“ | A, B, C | Katalogeintrag, referenziert dieselbe Werkzeugkette. |

## Zusammenfassung nach Kategorie (nur Tier 1 + Tier 2, ohne Tier 3 und ohne Suggestion-Log-Eintrag #12)

- **A — separater Bookkeeping-Commit vorgeschrieben/beschrieben:** 10 Stellen (#8, #9, #11, #13, #14, #15, #18, #19, #20, #24)
- **B — Hash-Injektion beschrieben:** 5 Stellen (#8, #9, #14, #15, #24)
- **C — `REF` als Bedingung für `[x]`/`[w]`:** 8 Stellen (#1, #2, #4, #5, #6, #8, #14, #15)
- **D — `REF` im Abnahme-Zusammenhang (Kontext/Zielstelle, meist unverändert zu lassen):** 8 Stellen (#3, #7, #10, #16, #17, #21, #22, #23)

(Einzelne Stellen tragen mehrere Kategorien, daher Summe > 24.)

## Trailer-Format-Vorschlag (Schritt 2)

### Anforderungen aus `re-intake-worker-isolation-and-checkin.md`

- `RQ-CI-02`: Ticket-ID im substantiellen Commit.
- `RQ-CI-03`: Base-Ref, gegen die die Änderung erfolgte.
- `RQ-CI-04`: beides maschinenlesbar an definierter Stelle.
- `RQ-CI-05`: Markerstand aus Commit-Metadaten ableitbar, kein Zweischritt mehr.

### Format

Git-Trailer-Konvention (RFC-822-Stil, `git interpret-trailers`-kompatibel): ein
Block aus `Key: value`-Zeilen ganz am Ende der Commit-Nachricht, durch eine
Leerzeile vom Fließtext getrennt, keine Leerzeile innerhalb des Blocks. Das Repo
nutzt dieses Muster bereits für `Co-Authored-By:` (siehe z. B. Commit
`a18dc4858fb4c19ef1cbb9b610ea070ef5807a92`), der neue Trailer reiht sich dort ein.

Zwei neue Schlüssel:

| Schlüssel | Wert | Validierungsregel |
|---|---|---|
| `Task-ID` | `XXXX-YY[.ZZ]` | Muss dem ID-Schema aus `TODO.md` entsprechen (`^\d{4}-\d{2}(\.\d{2})?$`); identisch mit der Task-/Subtask-ID, die `[p]`→`[x]`/`[w]` wechselt. |
| `Base-Ref` | `<40 lowercase hex>` | Voller, erreichbarer Commit-Hash — dieselbe Regel, die `legacy-task-doctor.md` bereits für `REF` durchsetzt (`LTD-REF-MALFORMED`: „not a full lowercase commit ID“). Empfehlung: identisch mit dem `base_commit`, das laut `AGENTS.md`/`SANDBOX.md` ohnehin schon in der Claim-Datei geführt wird — keine neue Datenquelle, nur eine zusätzliche Veröffentlichungsstelle. |

Mehrfachwerte (z. B. ein aggregierender Parent-Abschluss-Commit, der mehrere
Subtask-IDs abschließt) sind über wiederholte `Task-ID:`-Zeilen abzubilden — Git-
Trailer erlauben mehrfache Vorkommen desselben Schlüssels (wie bei mehreren
`Co-Authored-By:`-Zeilen üblich).

### Ausgearbeitetes Beispiel

```
docs(0041-02): establish self-describing check-in trailer

Removes the separate bookkeeping commit for the [p] -> [x]/[w] transition.
The substantive commit now carries the ticket ID and the base-ref it was
made against in a machine-readable trailer, so the marker transition is
derivable from commit metadata alone instead of a second, hash-dependent
commit.

Task-ID: 0041-02
Base-Ref: a18dc4858fb4c19ef1cbb9b610ea070ef5807a92

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

`a18dc4858fb4c19ef1cbb9b610ea070ef5807a92` ist der reale, aktuelle `HEAD`-Commit
dieses Repos zum Zeitpunkt der Erstellung dieser Liste (`git rev-parse HEAD`) —
im Beispiel als Platzhalter für „die Branch-Spitze, von der aus die Arbeit
begann“ verwendet, nicht als Behauptung, dass `0041-02` gegen genau diesen Commit
gearbeitet hätte.

### Offene Entscheidungen für die menschliche Sichtung

1. **Semantik von `Base-Ref` genau festlegen:** Ist es der Commit, von dem der
   Item-Branch abgezweigt wurde (`branch-workflow.md`s Base-and-Merge-Regel), oder
   der zuletzt gemergte Prerequisite-Tip, falls mehrere Merges stattfanden? Ich
   empfehle Ersteres (Branch-Ursprung), weil es mit dem bereits geführten
   `base_commit`-Claim-Feld übereinstimmt und eindeutig ist; die gemergten
   Prerequisite-Tips sind bereits per `branch-workflow.md` in der Claim-Datei
   dokumentiert und müssen nicht dupliziert werden.
2. **Werkzeugfolgen (Tier 3):** `_src/tools/runner_transaction.py` implementiert
   den Zweischritt technisch. Eine reine Dokumentänderung an den fünf
   Autoritätsdokumenten lässt das Werkzeug zurück — Diskrepanz zwischen
   Dokuanweisung und tatsächlichem Werkzeugverhalten, bis ein Folge-Task das
   Werkzeug anpasst. Vermutlich braucht `0041-02`/`0041-04`/`0041-05` einen
   ausdrücklichen Verweis darauf, oder es entsteht ein neuer Task.
3. **`PRIVILEGED.md:138`** (Tier 2): gehört inhaltlich zu `0041-02`, ist aber
   nicht in der Fünfer-Liste des Feature-DoD genannt. Bitte entscheiden, ob es in
   den Scope von `0041-02` fällt oder einen eigenen Folge-Task braucht.
