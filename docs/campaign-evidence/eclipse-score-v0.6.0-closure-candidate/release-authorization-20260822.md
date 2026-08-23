# Freigabe zur Veröffentlichung — Feature 0019, v0.6.0 Kuratieransicht

**Kontrolle 3 aus `DEC-0019-002`.** Dieser Datensatz hält die ausdrückliche
Management-Freigabe fest, die der Veröffentlichung vorausgehen muss.

## Freigabe

- **Erteilt am:** 2026-08-22
- **Erteilt von:** Management (aktueller User / Repository-Eigentümer)
- **Wortlaut, verbatim:**

  > Passt, kann so raus..

- **Aufgezeichnet von:** Projektleiter `kathryn`
  (`DEC-ROLE-001`: zeichnet auf, entscheidet nicht)
- **Autoritätsgrundlage der Veröffentlichung:** `DEC-0019-001`
  (Commit `d6777be3a`) — Publikationsautorität für Feature `0019`, in vollem
  Umfang, an `worf`.

## Was genau freigegeben ist

**Exakt dieser Baum, byteidentisch:**

- Vorschau: `/tmp/autodocs-0019-10-preview-20260822T003000Z/export/`
- **Tree-SHA256:** `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`
- Umfang: 2.248 Dateien, davon 2.239 Kandidaten-Seiten plus
  `records/index.html` als Listing-Seite
- Herkunft: Branch `0019-10` bei `de15a703cfc3d7b07865c339ba631aca8932abcf`,
  integrierter Feature-Tip `58b35f1e54cff2b4e718febe2c666cf5e67ae3f5`

**Digest-Verfahren, reproduzierbar** (nachgeliefert von `worf`, ausgeführt und
bestätigt von `kathryn` am 2026-08-22 — exakte Übereinstimmung): SHA-256 über
lexikografisch pfadsortierte Sätze aus UTF-8-Pfadbytes, einem NUL-Byte und dem
**rohen** 32-Byte-SHA-256 der Dateibytes; anschließend SHA-256 über den
Gesamtstrom. Implementiert in
`_src/tools/prepare_score_curation_export.py:204`.

```
python3 -c 'import hashlib,pathlib; r=pathlib.Path("."); f=sorted(p for p in r.rglob("*") if p.is_file() and not p.is_symlink()); print(hashlib.sha256(b"".join(p.relative_to(r).as_posix().encode()+b"\0"+hashlib.sha256(p.read_bytes()).digest() for p in f)).hexdigest())'
```

## Bindende Auflage: keine Änderung nach der Prüfung

**Veröffentlicht wird der Baum mit exakt obigem Digest.** Jede Änderung — auch
eine scheinbar harmlose — erzeugt einen anderen Baum, der die enge
Ausschlussprüfung **nicht** durchlaufen hat und dessen Digest nicht mehr auf die
Freigabe passt. Wer den Baum ändert, veröffentlicht etwas, das das Management
nicht freigegeben hat.

Das betrifft ausdrücklich die zwei bekannten toten relativen Links (siehe
*Bekannte, bewusst nicht behobene Mängel*). Sie werden **vor** der
Veröffentlichung **nicht** repariert.

## Erfüllte Kontrollen nach `DEC-0019-002`

1. **Enge Ausschlussprüfung — `sauber`.** QA-Manager
   `Kathryn-Harry-20260822T113000Z`, unprivilegiert, unabhängig von allen
   Implementierern des Features. Bericht:
   [`../qa-exclusion-check-0019-20260822/report.md`](../qa-exclusion-check-0019-20260822/report.md),
   auf `main` seit `120504cd7`.
   - 2.239 von 2.239 Kandidaten-Seiten tragen den Marker
     `UNVALIDATED — AWAITING CURATOR CONFIRMATION`; **null** ohne Marker,
     mechanisch über alle Seiten geprüft.
   - Einziger `data-validation-state`-Wert im gesamten Baum: `unvalidated`
     (6.723 Vorkommen).
   - Kein Fremdinhalt: null lokale Pfade, null E-Mail-Adressen, null
     Claim-Dateien, null Agenten-/Session-Token. Einziger `status`-Wert:
     `invalid/to-be-confirmed`.
   - Von `kathryn` unabhängig nachgefahren, gleiches Ergebnis. Zwei Treffer auf
     Schlüsselbegriffe einzeln geprüft und als AUTOSAR-Normtext bestätigt
     (Anforderungen zu Reverse Engineering bzw. Schlüsselableitung) — keine
     Zugangsdaten.
2. **Freigabevorschau geliefert.** Anklickbarer lokaler Link auf den gebauten
   Baum und `overview.html` mit Änderungsübersicht und Seitenlinks; alle Links
   lösen auf, Zahlen decken sich mit `validation.json`.
3. **Ausdrückliche Freigabe** — dieser Datensatz.

## Unberührte Schranke: die Kuratorentscheidung

`CUR-0019-08-20260820` bindet unverändert. Die 2.239 als
`invalid`/`to-be-confirmed` geführten Records bleiben von **faktischer**
Publikation ausgeschlossen; veröffentlicht wird ausschließlich die begrenzte,
durchgehend als unvalidiert markierte Kuratier-/Reviewansicht. Die Freigabe
betrifft die Autorität, nicht den Inhalt.

## Bekannte, bewusst nicht behobene Mängel

- **Zwei tote relative Links**, von der Ausschlussprüfung als
  Nebenbeobachtung notiert, ausdrücklich kein Befund und kein Blocker:
  - `participate.html` → `../../../curation-report.html`
  - alle Record-Seiten → `../../../../review_request.js` (existiert nirgends im
    Baum)

  Sie gehen **mit** in die Veröffentlichung, weil eine Reparatur den geprüften
  Baum verändern und damit Prüfung und Digest entwerten würde. Sie sind als
  Nachfolgearbeit zu führen und in einer späteren Veröffentlichung zu beheben.

## Was diese Freigabe nicht ist

Sie ist **keine** Task- oder Feature-Abnahme, **kein** Integrationsverdikt und
**kein** `DONE.md`-Umzug. Die Integration von Feature `0019` nach `main` und
sein Abschluss bleiben eigenständige privilegierte Akte.

---

## Nachtrag 2026-08-22 — Freigabe auf den vollständigen Website-Abgleich erweitert

**Art:** append-only Erweiterung der Freigabe oben. Der ursprüngliche Text bleibt
unverändert gültig; sein Umfang wird durch diesen Nachtrag erweitert.

### Der Befund, der die Erweiterung nötig machte

Der privilegierte Publikationsoperator `worf-krell-20260822t102000z` hat den
Vorabtest bestanden — exakter Digest
`7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`, 2.248
Dateien, byteidentisch zur freigegebenen Vorschau, Marker und Status gültig,
Deployment-Schlüssel `SHA256:+oo7DoLWJP3RtulD24fsHw57zTp/K3V9WrpGOKFT52M`
genehmigt — und **vor jedem Schreibvorgang gestoppt**. Kein Push, kein
Deployment-Commit, kein Log.

Grund: `_src/publish.sh` synchronisiert eine **feste Liste** von Verzeichnissen
(`PUBLIC_DIRS`: `ar classes en es flags fr hi ko modules namespaces pt ru
services zh`) und Dateien (`PUBLIC_FILES`: `index.html style.css fold.js
review.js`) aus dem lokal generierten Baum. Gegen die Deployment-Baseline
`70fcf5935b5725c92ceccd234a8087268eaee28f` ergibt das **4.133 zusätzliche
Einträge** außerhalb des freigegebenen Teilbaums.

**Verschärfender Befund der Projektleitung:** Der freigegebene Kuratier-Teilbaum
steht in `PUBLIC_DIRS` **überhaupt nicht**. `publish.sh` ist damit nicht nur zu
breit, sondern für den freigegebenen Gegenstand das **falsche Werkzeug** — es
würde die freigegebene Sache nicht veröffentlichen und stattdessen 4.133
ungeprüfte Änderungen mitnehmen.

### Entscheidung des Managements

- **Erteilt am:** 2026-08-22
- **Erteilt von:** Management (aktueller User / Repository-Eigentümer)
- **Entscheidung:** **Alles mitveröffentlichen.** Die Freigabe wird vom exakten
  Teilbaum auf den vollständigen Website-Abgleich erweitert.
- **Ausdrücklich akzeptiertes Risiko:** Die 4.133 zusätzlichen Pfade hat
  **niemand inhaltlich geprüft**. Das war Bestandteil der zur Wahl gestellten
  Option und ist bewusst angenommen.
- **Aufgezeichnet von:** Projektleiter `kathryn` (`DEC-ROLE-001`).

### Auflagen, die trotz der Erweiterung gelten

1. **Der geprüfte Teilbaum bleibt byteidentisch.** Sein Digest muss unmittelbar
   vor dem Push erneut stimmen. Weicht er ab: nicht pushen.
2. **Aufschlüsselung vor dem Push liefern.** Der Operator legt vor, was die
   4.133 Einträge sind — nach Kategorie und Änderungsart (neu / geändert /
   gelöscht), mit Beispielen. Das Management hat diese Aufschlüsselung zugesagt
   bekommen; sie wird geliefert, nicht nachgereicht.
3. **Harte Abbruchbedingungen.** Der Operator veröffentlicht **nicht** und
   meldet stattdessen, wenn eine der folgenden Bedingungen zutrifft:
   - Der Abgleich würde auf dem Ziel vorhandene veröffentlichte Inhalte
     **löschen** (`rsync --delete` wirkt innerhalb der Zielverzeichnisse);
   - er berührt Pfade **außerhalb** von `PUBLIC_DIRS`/`PUBLIC_FILES`;
   - eine private Pfad-Schranke (`_src`, `output`, `.gitignore`) schlägt an;
   - der Digest des geprüften Teilbaums stimmt nicht mehr.
   Diese Bedingungen sind **nicht** miterweitert. Das Management hat den Umfang
   erweitert, nicht die Sorgfalt aufgehoben.
4. **Die Inhaltsschranke bleibt unberührt.** `CUR-0019-08-20260820` gilt
   weiter: die 2.239 `invalid`/`to-be-confirmed` Records bleiben von faktischer
   Publikation ausgeschlossen; veröffentlicht wird die durchgehend als
   unvalidiert markierte Kuratier-/Reviewansicht.

### Nachfolgearbeit

Dass für einen begrenzten, freigegebenen Teilbaum kein passendes
Veröffentlichungswerkzeug existiert, ist ein echter Werkzeugmangel und keine
Einzelfall-Panne. Er ist als Vorgang zu führen: ein Mechanismus, der genau einen
freigegebenen Teilbaum mit geprüftem Digest veröffentlicht, ohne den restlichen
Website-Abgleich mitzuziehen. Bis dahin ist jede künftige Teilbaum-Freigabe
derselben Erweiterungsentscheidung ausgesetzt.

---

## Berichtigung 2026-08-22 — Die Zahl 4.133 ist unbelegt; die Publikation ist blockiert

**Art:** append-only Berichtigung. Der Text oben bleibt stehen. Er enthält eine
Angabe, die sich nicht belegen lässt, und die Managemententscheidung beruhte
darauf.

### 1. Die Zahl 4.133 hat keinen dauerhaften Beleg

Der privilegierte Operator `worf` hat gezielt nach einem durablen Nachweis
gesucht — Log oder Quittung von `worf-krell-20260822t102000z`,
Preflight-Ausgabe, Diff-Kommando — und **keinen gefunden**. Die Zahl existiert
ausschließlich als Prosa in diesem Datensatz.

Sie kann nicht aus einem Trockenlauf von `_src/publish.sh` stammen: dieses
Werkzeug **hat keinen**. Ob sie aus `_src/tools/publish_public_site.sh` oder aus
einem Handvergleich stammt, ist unbestimmt.

**Verantwortung:** Die Projektleitung (`kathryn`) hat die Zahl in die
Entscheidungsvorlage an das Management übernommen und in diesen Datensatz
geschrieben, ohne ihre Herkunft zu prüfen. Sie war Grundlage der Erweiterung
oben. Das ist ein Fehler der Aufzeichnung, nicht des meldenden Operators.

### 2. Neuer Defekt in `_src/tools/publish_public_site.sh` — stille Unvollständigkeit

Gefunden von `worf`, von der Projektleitung am Quelltext bestätigt (Zeile 80):

```
tar -cf - -C "$REPO_ROOT" -T "$EXPORT_LIST" | tar -xf - -C "$EXPORT_DIR"
```

Die **Dateiliste** stammt aus `git ls-tree -r "$REVISION"` — korrekt. Die
**Dateiinhalte** liest `tar` aber aus `$REPO_ROOT`, also aus dem *aktuell
ausgecheckten Arbeitsverzeichnis*, nicht aus dem Git-Objekt der Revision.

Folge: Wird das Werkzeug mit einer Revision aufgerufen, die **nicht**
ausgecheckt ist, existieren die gelisteten Pfade auf Platte nicht. `worf` hat
das reproduziert: Aufruf aus dem Root-Checkout (dort ist `main` ausgecheckt)
gegen Revision `58b35f1e5` meldete `Cannot stat` für alle 2.248
`eclipse-score-v0.6.0-curation-review/`-Pfade und mehrere
`provenance/0019-*`-Dateien — und erzeugte trotzdem einen „Export", der den
kuratierten Baum **lautlos nicht enthält**.

**Präzisierung gegenüber dem Meldetext:** `worf` schrieb, das Skript habe „kein
`pipefail`". Das trifft nicht zu — Zeile 2 setzt `set -euo pipefail`. Der
strukturelle Defekt besteht davon unabhängig und ist der wesentliche Punkt: die
Herkunft der Inhalte ist falsch. Ob der Lauf zusätzlich hätte abbrechen müssen,
ist eine zweite, kleinere Frage.

Das Werkzeug ist damit nur korrekt, wenn die gewünschte Revision zugleich
ausgecheckt ist. Mit Revisionsargument aus einem anderen Worktree aufgerufen
liefert es still einen unvollständigen Baum. Für ein **Publikationswerkzeug**
ist das die gefährlichste Fehlerart überhaupt.

`worf` hat aus diesem fehlerhaften Lauf **keinen** Digest berechnet und das
gitignorierte Scratch-Verzeichnis gelöscht, um keinen falschen Artefakteindruck
zu hinterlassen.

### 3. `main` trackt den freigegebenen Baum nicht

Bestätigt: `git ls-tree main` enthält **null** Pfade unter
`eclipse-score-v0.6.0-curation-review/`. Der freigegebene Baum lebt
ausschließlich auf dem integrierten `0019`-Zweig (`58b35f1e5`).

### 4. Weder Werkzeug 1 noch Werkzeug 2 ist derzeit ein gangbarer Weg

- **Werkzeug 1** (`_src/publish.sh`): synchronisiert eine feste Verzeichnisliste,
  in der der freigegebene Teilbaum nicht vorkommt — es würde den freigegebenen
  Gegenstand nicht veröffentlichen. Sein Löschverhalten (`rsync -a --delete` je
  Zielverzeichnis) ließ sich **nicht** empirisch prüfen: es existiert kein
  lokaler Klon des Deploy-Ziels, und ein Lesezugriff auf das reale Remote wurde
  ohne gesonderte Freigabe nicht versucht.
- **Werkzeug 2** (`_src/tools/publish_public_site.sh`): trägt den Defekt aus
  Abschnitt 2 und kann ohne `PUBLISH_ALLOW_FORCE_PUSH=1` **überhaupt nicht
  pushen** — Git lehnt den historienfremden Orphan-Branch gegen ein bestehendes
  `main` als Non-Fast-Forward ab. Force-Push ist von der Projektleitung
  untersagt und von keiner Managemententscheidung gedeckt.

**Ergebnis: Die Publikation von Feature `0019` ist blockiert.** Sie steht nicht
an einer fehlenden Freigabe — die liegt vor —, sondern daran, dass kein
verifiziert sicherer Weg existiert, sie auszuführen.

### Was nicht geschehen ist

Kein Push, kein Force-Update, keine Nutzung von Zugangsdaten, keine
Netzwerkoperation gegen das Deploy-Ziel. Das Ziel ist unverändert.

### Was gültig bleibt

Die Freigabe des Managements (Abschnitt „Freigabe" oben) und die Erweiterung
bleiben als **Willensäußerung** gültig; die Inhaltsschranke aus
`CUR-0019-08-20260820` ebenfalls. Berichtigt wird die **Tatsachengrundlage**,
auf der die Erweiterung erging. Ob das Management bei seiner Entscheidung
bleibt, wenn die Zahl unbelegt ist, ist ihm vorzulegen.

---

## Freigabe 2026-08-22 — enger Weg autorisiert, Erweiterung wird nicht in Anspruch genommen

**Art:** append-only Ergänzung. Die Freigabe und die Berichtigung oben bleiben
unverändert stehen.

- **Erteilt am:** 2026-08-22
- **Erteilt von:** Management (aktueller User / Repository-Eigentümer), Wortlaut:
  „gut, gib Worf das ok."
- **Aufgezeichnet von:** Projektleiter `kathryn` (`DEC-ROLE-001`)

### Was sich gegenüber der Erweiterung ändert

Die Erweiterung auf den vollständigen Website-Abgleich wurde erteilt, weil zum
damaligen Zeitpunkt nur *alles* oder *nichts* möglich war. Diese Zwangslage
besteht nicht mehr: `_src/tools/publish_approved_subtree.py` ist abgenommen und
auf `main` (Integration `0180fa854`, Checkpoint bestanden, zweirundiges Review).

**Der enge Weg wird genommen. Die Erweiterung wird nicht in Anspruch genommen.**
Die 4.133 ungeprüften Pfade werden **nicht** veröffentlicht; die unbelegte Zahl
aus der Berichtigung ist damit gegenstandslos, ohne dass sie nachträglich
geklärt werden müsste.

### Autorisierter Ablauf

Vorgelegt vom privilegierten Operator `worf`, hier autorisiert:

1. Persistenten lokalen Klon von `PUBLISH_REMOTE` verwenden (derselbe, den
   `_src/publish.sh` als `PUBLISH_DIR` nutzt), **kein** Orphan-Baum.
2. `publish_approved_subtree.py --apply` mit
   `--expected-tree-digest 7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`
   und `--authorization-ref`, schreibt ausschließlich unter
   `<PUBLISH_DIR>/eclipse-score-v0.6.0-curation-review/`.
3. **Pfadbegrenzt** committen — ausdrücklich **nicht** `git add -A`, damit ein
   abweichender Rest des Klons nicht mitgenommen wird.
4. Normaler Fast-Forward-`push`. **Kein Force.**

Dieser Weg umgeht beide bekannten Werkzeugdefekte: die feste Verzeichnisliste
von Werkzeug 1 spielt keine Rolle, weil der Pfad explizit gewählt wird; der
Revisions-/Arbeitsverzeichnis-Fehler von Werkzeug 2 spielt keine Rolle, weil
weder `tar` noch ein Revisionsargument beteiligt sind; der Force-Zwang von
Werkzeug 2 entfällt, weil kein fremder Historienbaum entsteht.

### Entschieden: Zielpfad

Der Teilbaum wird als **oberstes Verzeichnis**
`eclipse-score-v0.6.0-curation-review/` veröffentlicht. Begründung: so liegt er
auf dem integrierten `0019`-Zweig, und genau dieser Baum ist vom Digest gedeckt.
Die resultierende öffentliche Adresse ist
<https://2b-rs.github.io/autodocs/eclipse-score-v0.6.0-curation-review/>.

**Bekannte Folge, die dadurch nicht behoben wird:** Die unter `0019-13`
erfassten toten relativen Links entstehen aus einer Einbettungsannahme des
Renderers und bleiben in jeder Platzierung bestehen. Sie sind bereits als
mitveröffentlichter Mangel festgehalten; die Platzierung ändert daran nichts und
wird nicht dafür verbogen.

### Entschieden: Handkommandos statt Wrapper

Schritte 3 und 4 dürfen als **pfadbegrenzte Handkommandos** ausgeführt werden.
Ein eigenes Wrapper-Skript wird für diesen einen Vorgang **nicht** verlangt: es
wäre ungetestet, ungeprüft und würde eine dritte Publikationsmechanik neben die
beiden bestehenden stellen — genau der Zustand, den `0038-29` beenden soll. Die
Absicherung liegt in der Pfadbegrenzung und in der Vorlagepflicht unten, nicht
in zusätzlichem Code.

### Bindende Auflagen

1. **Dry-Run vor `--apply`**, Ergebnis der Projektleitung vorlegen.
2. **Digest unmittelbar vor dem Schreiben** erneut gegen den freigegebenen Wert
   prüfen. Abweichung: nicht veröffentlichen.
3. **Vor `git push` melden** — was der pfadbegrenzte Commit enthält und was der
   Klon sonst noch an Abweichungen trägt. Erst nach Bestätigung pushen.
4. **Kein Force-Push.** Unverändert und ausnahmslos.
5. Ergäbe der Klon, dass der Push kein Fast-Forward wäre: **anhalten und
   melden**, nicht erzwingen.
6. Die Inhaltsschranke aus `CUR-0019-08-20260820` bleibt unberührt.

### Nach der Veröffentlichung

Zu melden und in die `0019-10`-Buchhaltung einzutragen: Ziel-URL, Commit im
Deploy-Repository, Digest des tatsächlich veröffentlichten Teilbaums, Zeitpunkt,
sowie die Autoritätsreferenzen `DEC-0019-001`, `d394f39f8` und dieser Nachtrag.
