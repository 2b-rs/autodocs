# Integrationscheckpoint-Review — Task `0038-29`

**Ergebnis: `rejected`** (Mangelliste unter *Befunde*; F1 und F2 verpflichtend).
**Checkpoint-Verdikt: `Integration review: mandatory` BESTÄTIGT** (keine Herabstufung).

Der Mechanismus selbst hat jeden Test bestanden, den ich mir ausdenken konnte, und
braucht keinen Neuentwurf. Die Zurückweisung betrifft **zwei Textstellen**: eine
nachweislich falsche Validierungsaussage in der Completion-Evidence und eine
Korrektheitsbehauptung in einem Governance-Dokument über ein Werkzeug, das sie nicht
einlöst. Beides ist in Minuten korrigierbar; bei Nachreview erwarte ich `accepted`.

---

## 1. Reviewer, Autorität, Unabhängigkeit

| Feld | Wert |
|---|---|
| Reviewer-Persona | `Kathryn-Kolos-20260822T115500Z` — **privilegierter Integrator** |
| Runtime | zed/claude-opus-5 |
| Dispatcher | Projektleiter `kathryn` (Persona Projektleiter — verschieden von meiner) |
| Implementierer | `Kathryn-Tuvok-20260822T113500Z` (Persona Implementierer — verschieden von meiner) |
| Reviewzeitpunkt | 2026-08-22, ca. 11:55–13:00 UTC |
| Review-Worktree | `.review-worktrees/0038-29-kolos-20260822T115500Z` (`--detach` auf `77b6337f0`) |
| Review-Branch | `review-0038-29-kolos-20260822T115500Z` |
| Schreibscope | ausschließlich `docs/campaign-evidence/review-0038-29-20260822/` in diesem Worktree |

**`DEC-0044-013`-Aufzeichnungspflicht:** Meine Persona (Integrator) ist ausdrücklich
verschieden von der des erzeugenden Agenten (Projektleiter `kathryn`) und von der des
Implementierers (`Kathryn-Tuvok`). Das vollständige Briefing, mit dem ich gestartet
wurde, ist in Abschnitt 8 **wortwörtlich und ungekürzt** wiedergegeben, zusammen mit
der Angabe, welchen Kontext ich bekommen habe und welchen nicht.

**Was ich nicht getan habe:** kein Merge nach `main`, kein `DONE.md`-Move, kein Push,
keine Publikation, kein Netzwerkzugriff auf ein Deploy-Ziel, keine Mutation des
Root-Checkouts, kein `git update-ref`, keine Reparatur fremder Arbeit. Ich habe
**kein** `Acceptance: ✓` gesetzt — bei `rejected` wäre ein Acceptance-Record falsch.

**Root-Zustand bei Reviewende (selbst geprüft):** `/Users/tobias.anton/devel/autodocs`
— Arbeitsbaum sauber, Index sauber, `HEAD` = `refs/heads/main` = `c97b21631`.
`main` bewegte sich während meines Reviews durch fremde Sessions (`0044-15`) von
`49d44d651` auf `c97b21631`; von mir nicht.

---

## 2. Geprüfte Baseline

| Gegenstand | Wert |
|---|---|
| Task | `0038-29`, Feature `0038` (Campaign D) |
| Branch / Tip | `0038-29` @ `77b6337f0` |
| Substanzieller Commit | `fcc6b63cdf01b4ebdd443db40f17d7a1c4bcb918` |
| Bookkeeping-Commit | `77b6337f05a6cb4d3fba5d7fabb2b585c1c06c24` |
| Branch-Basis | `main` @ `2f3e29b2a` |
| Claim | `TODO-Kathryn-Tuvok-0038-29-20260822T113500Z.md` (auf dem Branch, mit wortwörtlichem Briefing als Provenienz) |

**Änderungsumfang, selbst nachgezählt** — genau fünf Pfade, keiner außerhalb des
erwarteten Scopes:

```
A  TODO-Kathryn-Tuvok-0038-29-20260822T113500Z.md
M  TODO.md
A  _src/tools/publish_approved_subtree.py          (617 Z.)
A  _src/tools/test_publish_approved_subtree.py     (383 Z.)
M  docs/pipeline/tools.md                          (+105 Z.)
```

**Prerequisite-Abschluss:** Einzige Vorbedingung ist `0038-26`. Sie steht auf `[x]`,
trägt selbst `Integration review: mandatory`, hat ein vollständiges Integrationsreview
durch den privilegierten Integrator `Seven-Tom` mit Verdikt `accepted` und einen
`Acceptance: ✓`-Record mit Review-REF `7458cee4e98651e7a70f67328830c8f3f6b7d5ad`.
Die Acceptance-Vorbedingungshülle ist geschlossen; kein unakzeptierter Vorgänger blockiert.

**Mergefähigkeit:** `git merge-tree --write-tree main 77b6337f0` liefert Exit 0 und
einen sauberen Baum (`c061c2267`) — **konfliktfrei**, obwohl `docs/pipeline/tools.md`
seit der Branch-Basis auf `main` wanderte (`9654ae778` → `5784d35ab`).

---

## 3. Abnahmekriterien, einzeln abgearbeitet

Jede Zeile wurde von mir **selbst ausgeführt**, nicht aus dem Bericht des
Implementierers übernommen. Fixtures unter `/tmp/kolos-review-20260822/` (flüchtig).

### AK-1 — Ein getestetes Werkzeug publiziert genau einen vom Aufrufer benannten Teilbaum · **erfüllt**

Realer `--apply` gegen ein Ziel mit fremdem Inhalt: Quelle 2 Dateien; Ziel enthielt
vorher `index.html`, `style.css`, `en/page.html`, `unrelated/keep.txt` (alle
**außerhalb** des Teilbaums) sowie `score/gone.html`, `score/old/stale.html`
(**innerhalb**, veraltet). Ergebnis: `created=2 modified=0 deleted=2`, Exit 0,
Zielteilbaum entspricht danach exakt dem freigegebenen Digest.

### AK-2 — Digest ist Pflichtargument, wird unmittelbar vor dem Schreiben neu berechnet, Abweichung ⇒ Verweigerung · **erfüllt**

- Fehlendes `--expected-tree-digest` ⇒ argparse, **Exit 2**.
- `--expected-tree-digest notadigest` ⇒ **Exit 1**, „must be a 64-character hex sha256".
- Abweichung bei `--apply` ⇒ **Exit 1**, „refusing publication: tree digest mismatch",
  **Ziel unverändert** — die unbeteiligte Datei und die veraltete Datei im Teilbaum
  standen danach byteidentisch noch da.
- **Neuberechnung vor dem ersten Schreibvorgang, selbst provoziert** (In-Process, über
  die CLI nicht rennbar): Plan gebaut, dann Quelle manipuliert, dann `apply_plan`.
  - Inhaltsänderung einer bestehenden Datei ⇒ `Refusal: … tree digest mismatch
    immediately before writing (expected 950cda24…, actual ffe2d226…)`; der
    Zielteilbaum **existierte danach nicht einmal**.
  - Neue Datei nach der Planung ⇒ ebenfalls Verweigerung, nichts geschrieben.

  Der Kernanspruch „die Quelle darf sich zwischen Planung und Schreiben nicht ändern"
  ist damit nicht nur behauptet, sondern von mir ausgelöst worden.

**Exit-Codes wurden direkt gemessen**, nicht hinter einer Pipe
(`cmd; rc=$?` bzw. `cmd >/dev/null 2>&1; echo $?`). Verweigerungen: **1**.
Aufruffehler: **2**. Erfolg: **0**.

### AK-3 — Digest-Verfahren ist das von `prepare_score_curation_export.py`, von Hand nachrechenbar · **erfüllt, mit Nachdruck**

Der Punkt mit dem höchsten Risiko: zwei Digest-Verfahren im Repository würden die
Bindung wertlos machen. Ich habe **drei** Implementierungen gegen den **echten
freigegebenen Baum** (`/tmp/autodocs-0019-10-preview-20260822T003000Z/export`,
2.248 Dateien) rechnen lassen:

| Implementierung | Ergebnis | Dateien |
|---|---|---|
| Meine eigene, aus dem Spezifikationstext in `TODO.md` neu geschrieben | `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283` | 2248 |
| Der **wortwörtlich transkribierte Ausdruck** aus `prepare_score_curation_export.py` (Branch `0019`, Z. 204) | `7c514686ba…08283` | 2248 |
| `publish_approved_subtree.compute_tree_digest()` | `7c514686ba…08283` | 2248 |
| **Bekannter, vom Management freigegebener Wert** | `7c514686ba…08283` | 2248 |

**Vier von vier identisch.** Es gibt kein zweites Verfahren; die Reimplementierung
weicht nicht ab.

Zusätzlich habe ich die in `docs/pipeline/tools.md` abgedruckte Shell-Pipeline
(`find … | LC_ALL=C sort | while read … printf '%s\0' … xxd -r -p | shasum -a 256`)
auf einem eigenen 25-Datei-Fixture ausgeführt: `950cda245e9981ad…cde9000044` —
**identisch** mit Werkzeug und meiner unabhängigen Implementierung. Ein Reviewer kann
den Digest tatsächlich von Hand nachrechnen; die Doku ist hier korrekt.

**Befund des Implementierers bestätigt:** `_src/tools/prepare_score_curation_export.py`
liegt nicht auf `main`, nur auf `0019`/`0019-10`. Ein Import war tatsächlich unmöglich.
Die gewählte Lösung (identische Reimplementierung plus ein Test, der den Digest
unabhängig aus der Spezifikation nachrechnet) ist unter dieser Bedingung richtig, und
der Umstand wurde gemeldet statt verschwiegen.

### AK-4 — Nichts außerhalb des Teilbaums wird angelegt, geändert oder gelöscht · **erfüllt (eigener Test)**

SHA-256-Manifest **aller** Dateien unterhalb der Zielwurzel außer `./score`, vor und
nach einem echten `--apply`, das 2 Dateien schrieb, 2 löschte und ein leer gewordenes
Verzeichnis entfernte:

```
681e784c…  ./en/page.html
c543e06c…  ./index.html
6f2ba12d…  ./style.css
f05c3aee…  ./unrelated/keep.txt
```

`diff` vorher/nachher: **leer**. Byteidentität außerhalb des Teilbaums bestätigt.

Randfälle, alle von mir gebaut, alle **Exit 1**, keiner mit Schreibwirkung:

| # | Fall | Meldung |
|---|---|---|
| T3 | `--subtree ../escape` | „must not traverse upwards" |
| T5 | `--subtree score/../../out` | „must not traverse upwards" |
| T4 | `--subtree /etc` (führendes `/`) | „must be relative, not absolute" |
| T6 | `--subtree _src` | „private path component '_src' would enter the destination" |
| S1 | Symlink (Datei) in der Quelle, Ziel außerhalb | „symbolic link in source is not publishable: leak.txt" |
| S2 | Symlink (Verzeichnis) in der Quelle, Ziel außerhalb | „symbolic link in source is not publishable: secretdir" |
| S3 | `--source` ist selbst ein Symlink | „source is not an existing directory" |
| S4/S5 | Zielteilbaum führt über einen Symlink (auch verschachtelt) | „destination subtree path traverses a symbolic link" |
| S6 | Quelle == Zielwurzel | „source and destination subtree must not overlap" |
| S7 | Quelle liegt im Zielteilbaum | „source and destination subtree must not overlap" |
| S10 | Quellpfad enthält `_src`-Komponente | „private path component '_src' … via score/_src/f.txt" |
| — | Zielteilbaum ist eine reguläre Datei | verweigert, Dateiinhalt unverändert |

Kontrolle auf Datenabfluss: In den Symlink-Fällen zeigten die Links auf eine Datei mit
Inhalt `TOPSECRET` außerhalb der Quelle. `grep -rl TOPSECRET <ziel>` nach allen Läufen:
**keine Treffer**. Der Symlink-Vektor — der einzige, über den ein „genau dieser
Teilbaum"-Werkzeug unbemerkt Fremdinhalt publizieren könnte — ist dicht.

### AK-5 — Löschungen nur innerhalb, nur was die Quelle nicht mehr enthält, vorher gemeldet · **erfüllt**

Im echten `--apply` wurden `score/gone.html` und `score/old/stale.html` gelöscht. Die
**vollständige** Liste (nicht die Stichprobe) wird ausgegeben, vor dem ersten Schreib-
**und** vor dem ersten Löschvorgang:

```
  deletions to be performed inside score (2):
    D score/gone.html
    D score/old/stale.html
```

Gelöscht wurde ausschließlich innerhalb; das leer gewordene `score/old/` wurde
zusätzlich entfernt (ebenfalls innerhalb). Alle vier Dateien außerhalb blieben
byteidentisch (AK-4).

### AK-6 — Schutzschranken aus `_src/publish.sh` bleiben in Kraft, keine eingebetteten Defaults · **erfüllt**

- Private Komponenten `_src`, `output`, `.gitignore`, **plus `.git`** (gegenüber
  `publish.sh` erweitert, nicht abgeschwächt), geprüft für den Teilbaumnamen *und* für
  jeden Quellpfad; beides von mir ausgelöst.
- Keine eingebetteten Defaults: `--source`, `--destination-root`, `--subtree`,
  `--expected-tree-digest`, `--authorization-ref` sind alle `required=True`.
- Statischer Scan der neuen Datei auf
  `socket|urllib|http|requests|subprocess|os.system|popen|github|2b-rs|git@|ssh://|token|password|secret`:
  **kein Treffer**. Importe ausschließlich stdlib (`argparse hashlib json os sys
  datetime pathlib typing`). Das Werkzeug kann strukturell nichts publizieren,
  committen oder senden — es schreibt nur ins Dateisystem. Die
  `PUBLISH_IDENTITY_*`/`PUBLISH_REMOTE`-Auslegung des Implementierers (seine
  Selbstmeldung 2) ist damit korrekt und nicht ausweichend: eine Commit-Identität kann
  in einem Werkzeug ohne Commit nicht vorkommen.

### AK-7 — Dry-Run meldet die vollständige beabsichtigte Wirkung, schreibt nichts · **erfüllt** (siehe F6)

25-Datei-Fixture mit `--sample 3`:

```
  counts            : source_files=25 created=25 modified=0 deleted=0 unchanged=0
  created (25), showing 3:
    C score/f1.html
    C score/f10.html
    C score/f11.html
    ... 22 more (full list in the evidence record)
```

Zahlen je Kategorie vollständig, Stichprobe begrenzt, Rest ausdrücklich ausgewiesen,
Exit 0, nichts geschrieben. Die Ausgabe endet mit der expliziten Zusicherung
„outside the subtree: nothing is created, modified or deleted by this tool".

### AK-8 — Keine erfundene Autorität · **erfüllt**

- `--authorization-ref` fehlt ⇒ Exit 2; leer/nur Leerzeichen ⇒ Exit 1.
- `--apply` ohne `--evidence` ⇒ Exit 1: „publication evidence is not optional".
- Vorhandene Evidenzdatei ⇒ Exit 1, kein Überschreiben.
- Evidenz oder Journal **innerhalb** des publizierten Teilbaums ⇒ Exit 1 (beide
  getrennt geprüft) — verhindert, dass die Evidenz sich selbst mitpubliziert.
- Im erfolgreichen Lauf steht `authorization_ref` im JSON und in der Konsolenausgabe.

### Definition of Done

| DoD-Punkt | Status |
|---|---|
| Tests für Digest-Treffer, Digest-Fehltreffer, fremder Zielinhalt, Löschmeldung, Privatpfad, Dry-Run-Vollständigkeit | erfüllt — 22 Tests, von mir **selbst** erneut ausgeführt: `Ran 22 tests … OK`, Exit 0 |
| Registriert in `docs/pipeline/tools.md` mit ausgeschriebenem Digest-Verfahren | erfüllt (Verfahren plus nachrechenbare Shell-Pipeline, verifiziert) |
| `_src/publish.sh` bleibt Ganzseiten-Publisher, wird nicht ersetzt | erfüllt |
| Verhältnis der Werkzeuge dokumentiert | in der Form erfüllt, **inhaltlich fehlerhaft** → **F2** |
| `automation_safety.py` besteht für das neue Werkzeug | Verdikt PASS, aber die Evidenzangabe dazu ist falsch → **F1** |
| Keine Credentials, Remote-Konfiguration, Ziel-Defaults eingebettet | erfüllt, statisch verifiziert |

### Explizite Nicht-Ziele

Alle drei eingehalten, von mir geprüft: nichts publiziert (kein Netzwerkzugriff
möglich, keiner erfolgt); die autorisierte `0019`-Freigabe ist unangetastet; wer
publizieren darf, ist unverändert.

---

## 4. Eigene Zahlen

| Messung | Mein Ergebnis |
|---|---|
| `python3 _src/tools/test_publish_approved_subtree.py` | **22 Tests, OK**, Exit 0, 3,5 s |
| `python3 _src/tools/automation_safety.py --json` | **`verdict: PASS`**, Exit 0 |
| `counts` daraus | `unresolved_critical: 0`, `policy_errors: 0`, `advisory: 38`, `disposed_critical: 24`, `findings: 73` |
| Findings auf `_src/tools/publish_approved_subtree.py` | **1** — `AUTO010`, `severity: high`, `status: advisory`, Zeile 432, Symbol `apply_plan`, Evidenz `target.unlink()` |
| Findings auf `_src/tools/test_publish_approved_subtree.py` | 0 |
| Digest über den echten freigegebenen Baum, 3 unabhängige Implementierungen | 3 × `7c514686ba…08283`, 2248 Dateien, == freigegebener Wert |
| Doku-Shell-Pipeline gegen Werkzeug | identisch (`950cda24…`) |
| Eigene Guard-Tests | 13 Verweigerungsfälle, **13/13** korrekt (Exit 1 bzw. 2), keiner mit Schreibwirkung |
| Byteidentität außerhalb des Teilbaums nach echtem `--apply` | 4/4 Dateien identisch, `diff` leer |
| Altpublisher unverändert | `_src/publish.sh` `8bdbbe96a…`, `_src/tools/publish_public_site.sh` `a65c1f75e…` — Objekt-Hashes auf `main` und auf `77b6337f0` **identisch** |
| Merge `0038-29` → `main` | konfliktfrei (`merge-tree --write-tree` Exit 0, Baum `c061c2267`) |

---

## 5. Befunde

### F1 — **major, verpflichtend.** Die Completion-Evidence behauptet null Findings; es ist eines.

`TODO.md`, Completion-Evidence zu `0038-29`, wörtlich:

> `python3 _src/tools/automation_safety.py --json` → **`verdict: PASS`, exit 0,
> `policy_errors: 0`, 0 findings for the two new files**

Die ersten drei Angaben stimmen und habe ich reproduziert. Die vierte ist falsch.
Mein eigener Lauf liefert für `_src/tools/publish_approved_subtree.py`:

```json
{ "rule": "AUTO010", "severity": "high", "status": "advisory",
  "line": 432, "symbol": "apply_plan", "evidence": "        target.unlink()" }
```

Das ist **ein Finding hoher Schwere**, wenn auch mit Status `advisory` und daher ohne
Einfluss auf Verdikt oder `policy_errors`. Sachlich ist der Fund unkritisch — es ist
genau die Löschoperation, die dieser Task fordert, geschrankt und vorab gemeldet.
**Der Mangel ist die Aussage, nicht der Code.**

Warum das an einem Checkpoint für einen irreversiblen externen Effekt zählt:
`AGENTS.md` verlangt ausdrücklich, keine Validierung zu behaupten, die so nicht
gelaufen ist. Ein `Acceptance: ✓` über einer Evidenzzeile, die ich soeben widerlegt
habe, wäre genau das gefällige `accepted`, vor dem mein Auftrag warnt. Eine falsche
Zahl in der Evidenz ist für jeden späteren Leser außerdem nicht von einer
verschwiegenen Zahl unterscheidbar.

**Erforderliche Korrektur:** Evidenzzeile auf den wahren Befund umstellen — etwa
„`verdict: PASS`, exit 0, `policy_errors: 0`, `unresolved_critical: 0`; **ein**
`AUTO010`-Finding (severity `high`, status `advisory`) auf
`publish_approved_subtree.py:432` (`target.unlink()`), das die geschrankte, vorab
gemeldete Löschoperation dieses Tasks beschreibt" — und, falls das Policy-Schema es
zulässt, eine reguläre Disposition dafür prüfen. Kein Codeeingriff nötig.

### F2 — **major, verpflichtend.** Die neue Governance-Tabelle behauptet für `publish_public_site.sh` eine Revisionstreue, die es nicht hat, und verschweigt seinen bekannten Defekt.

Die neue Tabelle in `docs/pipeline/tools.md` beschreibt Werkzeug 2 als:

> **gesamter getrackter Baum minus Ausschlussliste** (`_src/`, `docs/`, `logs/`,
> Agentendateien, …) **zu einer Revision**

Nachgeprüft in `_src/tools/publish_public_site.sh`: die Datei**liste** stammt korrekt
aus der Revision, die **Inhalte** nicht. Zeile 80:

```sh
tar -cf - -C "$REPO_ROOT" -T "$EXPORT_LIST" | tar -xf - -C "$EXPORT_DIR"
```

`-C "$REPO_ROOT"` liest aus dem **ausgecheckten Arbeitsverzeichnis**, nicht aus der
Revision. Mit einer nicht ausgecheckten Revision erzeugt das einen **lautlos
unvollständigen** Export — genau der Defekt, den mein Auftrag als einen der beiden
Anlässe dieses Vorgangs nennt.

Die Formulierung „zu einer Revision" behauptet damit eine Eigenschaft, die das
Werkzeug nicht einlöst, und die Tabelle erwähnt den Defekt an keiner Stelle. Das wiegt
schwerer als eine Ungenauigkeit an beliebiger Stelle, weil dieser Abschnitt
erklärtermaßen dafür da ist, dass „niemand raten muss, welches Werkzeug gilt", und
weil er in einem Governance-Dokument steht, das nach `DEC-0044-012` unmittelbar nach
`main` getragen wird. Ein Operator, der morgen eine revisionsgebundene Freigabe
umzusetzen hat, wird von dieser Zeile in Richtung des defekten Werkzeugs gelenkt.

Zur Fairness: Die DoD verlangt wörtlich nur das Verhältnis **zweier** Werkzeuge
(`publish.sh` und das neue). Der Implementierer hat freiwillig alle drei dokumentiert
— das ist besser als gefordert, hat aber die Genauigkeitspflicht für den dritten
Eintrag mit übernommen. Die Korrektur ist **ein Satz**, kein Rückbau der Tabelle.

**Erforderliche Korrektur:** In der Zeile zu `publish_public_site.sh` festhalten, dass
die Auswahl aus der Revision stammt, die Inhalte jedoch aus dem Arbeitsverzeichnis
(`:80`), und dass das Werkzeug deshalb **nur mit ausgecheckter Revision** ein
korrektes Ergebnis liefert — mit dem Hinweis, dass dies ein offener Defekt und kein
beabsichtigtes Verhalten ist. Ob der Defekt einen eigenen Vorgang bekommt, ist eine
Entscheidung der Projektleitung/Architektur und nicht Gegenstand dieses Tasks.

### F3 — minor, empfohlen. „Exit 1 = es wurde nichts publiziert" ist auf einem Pfad unwahr.

Modul-Docstring und `tools.md` sagen beide: „Exit-Codes: `0` Erfolg, `1` Verweigerung
(es wurde nichts publiziert)". Die `Refusal`-Klasse dokumentiert sich als „Nothing has
been written."

Es gibt einen erreichbaren Pfad, auf dem das nicht stimmt: `apply_plan()` schreibt und
löscht zuerst, berechnet **danach** den Digest des Zielteilbaums neu und wirft bei
Abweichung `Refusal` („post-publication verification failed"). Dann ist das Ziel
bereits verändert, und die Evidenzdatei wird **nicht mehr geschrieben**, weil die
Ausnahme vor dem Evidenzblock greift. Der Operator sieht Exit 1 und eine Meldung,
deren dokumentierte Bedeutung „nichts passiert" ist, während das Ziel mutiert und ohne
Evidenz zurückbleibt.

Das Werkzeug versagt hier **laut**, nicht leise — die richtige Richtung. Der Mangel
ist die Zusicherung. Empfehlung: Exit-Code-Doku und `Refusal`-Docstring präzisieren
(eigener Text für die Nachverifikation) und in diesem Pfad einen Fehler-Evidenzsatz
schreiben, damit der Zustand des Ziels rekonstruierbar bleibt. Ich konnte den Pfad nur
durch Codelektüre feststellen, nicht auslösen.

### F4 — minor, empfohlen. Verweigerungen aus dem **Ziel** melden „source".

Reproduziert:

- Symlink **im Zielteilbaum** ⇒ „symbolic link in **source** is not publishable: link.txt"
- Zielteilbaum ist eine reguläre Datei ⇒ „**source** is not an existing directory: …/dest/score"

Ursache: `destination_inventory()` benutzt `collect_regular_files()` wieder, dessen
Meldungen fest „source" sagen. Ein Operator untersuchte das falsche Verzeichnis.
Behebung: Label-Parameter durchreichen.

### F5 — minor. Ein vorhandener Symlink irgendwo im Zielteilbaum macht die Publikation unmöglich.

Folge derselben Wiederverwendung: Enthält der Zielteilbaum bereits einen Symlink,
verweigert das Werkzeug, statt ihn zu ersetzen oder zu löschen. Fail-closed und damit
sicher, aber undokumentiert; ein Operator mit gewachsenem Deploy-Verzeichnis würde
davon überrascht. Bitte in `tools.md` benennen.

### F6 — minor. Der Dry-Run verweist auf eine Evidenzdatei, die es nicht geben muss.

Die Ausgabe endet mit „… n more (full list in the evidence record)". `--evidence` ist
im Dry-Run jedoch **optional**; ohne es existiert die vollständige Liste nirgends. Das
Kriterium ist wörtlich erfüllt (Zahlen plus begrenzte Stichprobe), der Verweis läuft
aber ins Leere. Empfehlung: Formulierung an das tatsächliche Vorhandensein von
`--evidence` koppeln.

### F7 — informativ, kein Mangel. Die Privatpfad-Schranke prüft `--destination-root` nicht.

`check_private_components()` prüft den Teilbaumnamen und jeden Quellpfad, nicht die
Zielwurzel selbst; `--destination-root <repo>/_src --subtree score` wäre möglich. Das
ist mit „keine eingebetteten Defaults, alles explizit benannt" vereinbar und der
Aufrufer benennt das Ziel bewusst — die Prosa in `tools.md` („kein privater
Pfadbestandteil darf ins Ziel") ist nur etwas weiter formuliert als die Implementierung
reicht. Keine Änderung gefordert.

### F8 — informativ. Dateirechte werden nicht übernommen.

`_write_file()` überträgt nur Bytes; Modus/Executable-Bit gehen verloren. Für einen
HTML-Baum bedeutungslos, relevant nur, falls das Werkzeug je für ausführbare Artefakte
benutzt würde. Erwähnenswert in `tools.md`.

### F9 — informativ, Restrisiko. Lokales TOCTOU.

Zwischen der Digest-Verifikation und den einzelnen `read_bytes()`/`os.replace()` bleibt
ein Zeitfenster, ebenso zwischen der Symlink-Prüfung der Zielpfad-Komponenten und dem
Schreiben. Beides erfordert einen lokalen Angreifer auf derselben Maschine und wird
durch die Nachverifikation des Zieldigests abgefangen (mit der Einschränkung aus F3).
Unter dem Bedrohungsmodell „ein Operator, eine Maschine" akzeptabel.

---

## 6. Ergebnis

**`rejected`.**

Nicht wegen des Mechanismus. Das Werkzeug tut, was `0038-29` verlangt, und es tut es
sauber: es verweigert in jedem Fall, in dem es verweigern muss; es fasst nichts
außerhalb des Teilbaums an, auch nicht über Symlinks; es benutzt dasselbe
Digest-Verfahren wie die Freigabe und nicht ein zweites; es kann strukturell nichts
publizieren, senden oder committen. Von 13 selbst konstruierten Angriffs- und
Randfällen ist keiner durchgekommen. Der Implementierer hat drei unbequeme Befunde
selbst gemeldet, und alle drei waren bei Nachprüfung zutreffend.

Zurückgewiesen wird es wegen **F1** und **F2** — beides Aussagen über die Arbeit, die
der Arbeit nicht entsprechen:

- **F1:** Die Completion-Evidence behauptet „0 findings"; tatsächlich ist es ein
  Finding hoher Schwere (advisory). Über einer nachweislich falschen
  Validierungsaussage kann ich kein `Acceptance: ✓` setzen; das ist der Kern der
  Regel, keine Formalie.
- **F2:** Die neue Governance-Tabelle schreibt dem defekten Werkzeug 2 eine
  Revisionstreue zu, die es nicht hat, und erwähnt seinen Defekt nicht — an genau der
  Stelle, die verhindern soll, dass ein Operator das falsche Werkzeug wählt.

Beide Korrekturen sind reine Textänderungen an bereits vorhandenen Stellen; kein
Redesign, kein neuer Test, keine neue Entscheidung nötig. Der Task geht nach
`docs/pipeline/task-acceptance.md` zurück auf `[p]`, weil die Korrekturarbeit
umsetzbar ist. **Nach Behebung von F1 und F2 erwarte ich bei Nachreview `accepted`**;
F3 und F4 sollten bei derselben Gelegenheit miterledigt werden, F5–F9 sind
Verbesserungen ohne Sperrwirkung.

Ich habe für diesen Task **kein** `Acceptance: ✓` gesetzt.

---

## 7. Checkpoint-Verdikt

**`Integration review: mandatory` — BESTÄTIGT. Keine Herabstufung.**

Der Auftrag stellte beides frei. Ich bestätige, aus vier Gründen:

1. **Der Knoten liefert den Mechanismus für einen irreversiblen externen Effekt.** Er
   publiziert selbst nicht, bestimmt aber, *was* der nachgelagerte Schritt publiziert.
   Ein Fehler in den Schranken wird zu öffentlichem, dauerhaftem Inhalt, den niemand
   freigegeben hat — genau die Klasse, für die der `AGENTS.md`-Header einen Checkpoint
   verlangt.
2. **Das Versagen dieses Werkzeugs wäre lautlos.** Sein gesamter Sicherheitswert steckt
   in den Pfad-, Symlink- und Digest-Schranken. Fällt eine aus, sieht ein falscher Lauf
   exakt aus wie ein richtiger: Exit 0, Evidenz geschrieben, „publication complete".
   Es gibt keine zweite Instanz, die das bemerkt — der menschliche Operator war die
   Kontrolle, die im Ausgangsvorfall gerade noch griff und die dieser Task ersetzen soll.
3. **Dieses Review hat den Nutzen praktisch belegt.** Zwei Mängel (F1, F2), die eine
   grüne Testsuite und ein grünes `automation_safety` nicht anzeigen, wären ohne den
   Checkpoint nach `main` gewandert — einer davon in ein Governance-Dokument. Grüne
   Tests beweisen nicht, dass die Arbeit richtig, vollständig oder autorisiert ist.
4. **Kein Gegenargument trägt.** Der Task ist klein und gut getestet — aber Größe und
   Testabdeckung sind nicht das Kriterium; die Reichweite des Fehlers ist es.

**Zusätzliche Empfehlung an den Architekten** (nicht meine Entscheidung): Der
Checkpoint sollte nicht nur für diese Erstlieferung gelten, sondern für **jede künftige
Änderung an `_src/tools/publish_approved_subtree.py`**. Die Schranken sind das Produkt;
eine spätere, harmlos wirkende Änderung an `check_relative_path()`,
`collect_regular_files()` oder `resolve_destination_subtree()` hat dieselbe Reichweite
wie die Erstlieferung, würde aber ohne eine solche Festlegung als gewöhnliche Wartung
durchgehen.

Meine Bestätigung des Defaults ersetzt die Architektenentscheidung nicht. `kathryn` hat
den Marker als konservativen Default gesetzt und das offen so vermerkt; ich bestätige
ihn als Integrator am Knoten. Die verbindliche Bestätigung oder eine begründete
Herabstufung bleibt beim Architekten, spätestens beim Abschluss von Feature `0038`.

---

## 8. Aufgezeichnetes Briefing und Kontext (`DEC-0044-013`)

### 8.1 Welchen Kontext ich hatte

**Bekommen:**

- den in 8.2 wörtlich wiedergegebenen Briefingtext, einschließlich der
  Vorabverifikationen des Dispatchers (22 Tests, Altpublisher unverändert, Trockenlauf
  gegen den echten Baum, Gegenprobe mit falschem Digest) und der drei Selbstmeldungen
  des Implementierers;
- Lesezugriff auf das gesamte Repository, alle Branches und alle Worktrees;
- die agent-inbox (11 Nachrichten, u. a. `kathryn`s Rundruf vom 2026-08-22T11:15:16Z
  zur Anlage von `0038-29` sowie die Entscheidungen `DEC-0044-008..015`);
- die Autoritätsdateien `AGENTS.md`, `CLAUDE.md`, `SANDBOX.md`, `TODO.md`,
  `docs/pipeline/task-acceptance.md`, `docs/pipeline/branch-workflow.md`;
- das reale freigegebene Exportverzeichnis
  `/tmp/autodocs-0019-10-preview-20260822T003000Z/export` (2.248 Dateien).

**Nicht bekommen und nicht benutzt:**

- keine Vorgabe, wie das Ergebnis lauten soll. Der Briefingtext nennt `accepted`,
  `rejected` und `inconclusive` gleichrangig und bezeichnet ein gefälliges `accepted`
  ausdrücklich als den einzigen echten Fehler;
- keinen Kontakt zum Implementierer `Kathryn-Tuvok-20260822T113500Z`, weder vor noch
  während des Reviews;
- keine Zugangsdaten, keinen Netzwerkzugriff auf `2b-rs/autodocs` oder ein anderes
  Deploy-Ziel;
- keine Schreibrechte außerhalb dieses Reviewberichts.

**Bemerkenswert für die Unabhängigkeitsbewertung:** Der Briefingtext enthält
Vorabverifikationen des Dispatchers, die ich hätte übernehmen können. Ich habe jede
davon **eigenständig wiederholt** (Testsuite, Objekt-Hash-Vergleich der Altpublisher,
Digest gegen den echten Baum, Gegenprobe mit falschem Digest) und darüber hinaus 13
eigene Angriffsfälle gebaut, die im Briefing nicht vorkamen. Die beiden Befunde, die
zur Zurückweisung führen (F1, F2), stammen aus dieser eigenen Prüfung — F2 allerdings
aus einer Frage, die das Briefing gestellt hat („Erwähnt die Doku den Defekt von
Werkzeug 2 oder verschweigt sie ihn?").

### 8.2 Briefing, wortwörtlich und ungekürzt

> Du bist **Kathryn-Tuvok-Review-20260822T115500Z** — nein, halt. Deine Persona ist **Kathryn-Kolos-20260822T115500Z**, privilegierter Integrator im Projekt autodocs (/Users/tobias.anton/devel/autodocs). Du bist ausdruecklich **nicht** derselbe wie der Implementierer `Kathryn-Tuvok-20260822T113500Z`.
>
> Melde dich an: `announce(agent: "Kathryn-Kolos-20260822T115500Z", role: "privilegierter Integrator, Integrationscheckpoint-Review Task 0038-29; kein Merge nach main, kein DONE.md, keine Publikation", runtime: "zed/claude-opus-5")`, dann `inbox(agent: "Kathryn-Kolos-20260822T115500Z")`.
>
> ## Einordnung (AGENTS.md "Dispatching a subagent")
>
> - **capability_class: `privileged`.** Git und Kommandos **direkt**. NIEMALS Runner-Protokoll, nie auf `run.sh` warten.
> - **Dispatcher:** Projektleiter `kathryn` (kleingeschrieben), im Auftrag des Managements, das diese Session angewiesen hat, Arbeit zu verteilen und Blocker aufzuloesen.
> - **Vorgang:** `0038-29`, Branch `0038-29`, Tip `77b6337f0`. Der Branch ist in `.worktrees/0038-29` ausgecheckt — leg dir einen **detached** Review-Worktree an: `git worktree add --detach .review-worktrees/0038-29-kolos-20260822T115500Z 77b6337f0`.
> - **Schreibscope:** ausschliesslich dein Reviewbericht unter `docs/campaign-evidence/review-0038-29-20260822/` in deinem Review-Worktree plus eine Notizdatei. Du darfst `Acceptance: ✓` fuer `0038-29` setzen, wenn du zustimmst — nur in deinem Worktree; `kathryn` traegt es nach `main`.
>
> ## Was du NICHT tust
> Kein Merge nach `main`, kein `DONE.md`, kein Push, **keine Publikation und kein Netzwerkzugriff auf das Deploy-Ziel**. Keine Mutation des Root-Checkouts (`DEC-0044-010`), kein `git update-ref`. Du reparierst nichts.
>
> ## Unabhaengigkeit und Aufzeichnungspflicht
>
> `DEC-0044-013`: Ein selbst gestarteter Reviewer erfuellt die Unabhaengigkeit nur mit **ausdruecklicher, vom erzeugenden Agenten verschiedener Persona** UND **aufgezeichnetem Briefing und Kontext**. Deine Persona (Integrator) ist verschieden von der des Dispatchers (Projektleiter) und vom Implementierer (Tuvok). **Nimm diesen Briefingtext wortwoertlich in deinen Bericht auf**, mit Angabe, welchen Kontext du bekommen hast und welchen nicht.
>
> ## Warum dieser Vorgang besonders zaehlt
>
> `0038-29` liefert den Mechanismus fuer einen **irreversiblen externen Effekt**: das Veroeffentlichen ins oeffentliche Web. Der Anlass ist real und frisch. Am 2026-08-22 sollte ein vom Management freigegebener Exportbaum publiziert werden. Dabei kam heraus:
>
> - `_src/publish.sh` synchronisiert eine **feste** Verzeichnisliste, in der der freigegebene Teilbaum gar nicht vorkommt — es haette das Freigegebene nicht publiziert.
> - `_src/tools/publish_public_site.sh` holt die Dateiliste korrekt aus `git ls-tree <REVISION>`, liest die **Inhalte** aber aus dem ausgecheckten Arbeitsverzeichnis (Zeile 80). Mit einer nicht ausgecheckten Revision erzeugt es **lautlos einen unvollstaendigen Export**.
> - Eine Zahl (`4.133` betroffene Zusatzpfade), auf der eine Managemententscheidung beruhte, liess sich hinterher **nicht belegen**.
>
> Kurz: Die vorhandenen Werkzeuge haben genau die Fehler, die dieser Vorgang verhindern soll. Ein nachsichtiges `accepted` hier ist teurer als anderswo.
>
> ## Ausgangslage
>
> Implementierer `Kathryn-Tuvok-20260822T113500Z`, unprivilegiert. Geliefert: `_src/tools/publish_approved_subtree.py` (617 Z.), `_src/tools/test_publish_approved_subtree.py` (383 Z.), Abschnitt in `docs/pipeline/tools.md`, Claim mit dem woertlichen Briefing als Provenienz. Commits `fcc6b63cd` (substanziell) und `77b6337f0` (Bookkeeping `[x]`, REF `fcc6b63cd`).
>
> `kathryn` hat bereits **selbst** verifiziert, nicht nur gelesen:
> - `python3 _src/tools/test_publish_approved_subtree.py` → **22 Tests, OK**.
> - Beide Altpublisher sind **byteidentisch unveraendert** (Objekt-Hashes verglichen).
> - **Trockenlauf gegen den echten freigegebenen Baum** (`/tmp/autodocs-0019-10-preview-20260822T003000Z/export`, Digest `7c514686ba…08283`): Digest stimmt, `source_files=2248 created=2248 modified=0 deleted=0`, Ausgabe sagt ausdruecklich, dass ausserhalb des Teilbaums nichts angefasst wird.
> - **Gegenprobe mit falschem Digest und `--apply`**: Exit **1**, Meldung „refusing publication: tree digest mismatch", Ziel unveraendert — inklusive einer vorher angelegten unbeteiligten Datei.
>
> Der Implementierer meldet drei Punkte selbst, statt sie zu verschweigen: (1) `prepare_score_curation_export.py` liegt nicht auf `main`, das Digest-Verfahren wurde daher nach Spezifikation neu implementiert und durch einen unabhaengig rechnenden Test gepinnt; (2) ein Identitaetsparameter kommt nicht vor, weil das Werkzeug keinen Commit erzeugt; (3) `docs/pipeline/tools.md` ist Governance und liegt nur auf dem Branch.
>
> ## Dein Auftrag
>
> Review nach [`docs/pipeline/task-acceptance.md`](docs/pipeline/task-acceptance.md). Pruef insbesondere:
>
> 1. **Alle Abnahmekriterien einzeln** gegen `0038-29` in `TODO.md`. Sie sind dort vollstaendig ausgeschrieben; arbeite sie ab, nicht summarisch.
> 2. **Der wichtigste Test:** Wird wirklich nichts ausserhalb des Teilbaums angefasst? Ueberzeug dich **selbst** in einem Scratch-Ziel mit unbeteiligtem Inhalt — nicht am Test des Implementierers. Pruef auch die Randfaelle: Symlink in der Quelle, `..` im Teilbaumnamen, Quelle und Ziel ueberlappend, Teilbaumname mit fuehrendem `/`.
> 3. **Digest-Wiederverwendung statt Neuerfindung.** Das Verfahren ist in `prepare_score_curation_export.py` (auf Branch `0019-10`/`0019`) implementiert. Vergleich die Reimplementierung gegen jene Quelle **und** gegen den bekannten Wert. Weicht sie ab, ist das ein Befund — zwei Digest-Verfahren im Repository waeren genau der Zustand, der die Bindung wertlos macht.
> 4. **Verweigert es zuverlaessig?** Digest-Abweichung, Quelle aendert sich zwischen Planung und Schreiben, fehlende Evidenz, fehlende Autoritaetsreferenz. Pruef die Exit-Codes selbst — Vorsicht bei `$?` hinter einer Pipe, das misst das falsche Kommando.
> 5. **Loeschungen:** nur innerhalb, vollstaendig vorher gemeldet. Bau den Fall.
> 6. **Bleiben die Altwerkzeuge unangetastet** und ist ihr Verhaeltnis zum neuen Werkzeug in `tools.md` so dokumentiert, dass ein Operator morgen weiss, welches gilt? Erwaehnt die Doku den Defekt von Werkzeug 2 oder verschweigt sie ihn?
> 7. **`automation_safety`** selbst laufen lassen, eigene Zahlen berichten.
> 8. **Autoritaetsgrenzen:** nichts ausserhalb des Scopes, nichts publiziert, `main` unbewegt.
> 9. **Checkpoint-Verdikt:** `0038-29` traegt `Integration review: mandatory` als konservativen Default der Projektleitung, **keine** Architektenentscheidung. Bestaetigen oder begruendet herabstufen — beides zulaessig. Bedenke dabei, dass der Knoten einen irreversiblen externen Effekt ermoeglicht.
>
> ## Ergebnis
>
> Genau eines: **`accepted`**, **`rejected`** (Mangelliste) oder **`inconclusive`** (was fehlt). Dazu getrennt das Checkpoint-Verdikt.
>
> Ein `rejected` oder `inconclusive` ist wertvoll. Ein gefaelliges `accepted` ist der einzige echte Fehler. Gruene Tests beweisen nicht, dass die Arbeit richtig, vollstaendig oder autorisiert ist — dieser Vorgang existiert, weil heute zwei Werkzeuge mit gruenem Vorabtest das Falsche getan haetten.
>
> ## Abschluss
>
> Committe deinen Bericht auf Branch `review-0038-29-kolos-20260822T115500Z`. Melde per `agent-inbox` an `kathryn` in **einer** Nachricht: Ergebnis, Checkpoint-Verdikt, deine eigenen Zahlen, die wichtigsten Befunde, Branch und Commit-Hash, und was du nicht pruefen konntest.

---

## 9. Was ich nicht prüfen konnte

1. **Das nachgelagerte Publizieren selbst.** Das Werkzeug endet beim Dateisystem;
   Commit und Push nach `2b-rs/autodocs` sind ein getrennter, separat autorisierter
   Schritt. Ich hatte weder Auftrag noch Zugang dafür und habe keinen Netzwerkzugriff
   auf ein Deploy-Ziel unternommen. Ob die Kette *Werkzeug → Operator-Commit → Push*
   insgesamt das Freigegebene und nur das Freigegebene publiziert, ist damit **nicht**
   durch dieses Review abgedeckt.
2. **Die Zahl `4.133`.** Mein Auftrag nennt sie als nachträglich unbelegbar. Sie stammt
   aus dem Ausgangsvorfall, nicht aus dieser Lieferung; ich habe sie nicht nachgerechnet
   und dieses Review hängt nicht an ihr.
3. **Den Fehlerpfad aus F3** (Nachverifikation schlägt nach dem Schreiben fehl) konnte
   ich nur durch Codelektüre feststellen, nicht auslösen — er verlangt eine Änderung am
   Ziel während des laufenden Schreibvorgangs.
4. **Verhalten bei Nicht-ASCII-Pfaden und Unicode-Normalisierung.** Geprüft wurde auf
   macOS/APFS mit ASCII-Pfaden. Das Digest-Verfahren ist ausdrücklich UTF-8-basiert und
   der reale 2.248-Datei-Baum reproduzierte korrekt, aber ein Baum mit Umlauten oder
   NFC/NFD-Unterschieden wurde nicht getestet. Für den bestehenden `ara::*`-Baum ohne
   Belang, für künftige Teilbäume mit übersetzten Dateinamen möglicherweise nicht.
5. **Gleichzeitige Läufe.** Zwei parallele `--apply` auf dieselbe Zielwurzel wurden
   nicht getestet; es gibt kein Sperrmittel im Werkzeug.
6. **Ob `docs/pipeline/tools.md` nach `main` gelangt.** Das ist nach `DEC-0044-012`
   Sache des Dispatchers. Ich habe verifiziert, dass der Merge `0038-29` → `main`
   konfliktfrei ist (`merge-tree --write-tree` Exit 0) — mehr nicht.

---

*Erstellt von `Kathryn-Kolos-20260822T115500Z`, privilegierter Integrator,
zed/claude-opus-5, 2026-08-22. Kein `Acceptance: ✓` gesetzt. `main` von mir nicht
bewegt. Nichts publiziert.*
