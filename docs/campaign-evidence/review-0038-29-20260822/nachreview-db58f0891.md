# Nachreview Integrationscheckpoint — Task `0038-29` gegen `db58f0891`

**Ergebnis: `accepted`.**
**Checkpoint-Verdikt: `Integration review: mandatory` — unverändert BESTÄTIGT.**

Fortsetzung desselben Reviewauftrags. Erstreview: `536860ce4`
(`report.md` in diesem Verzeichnis), Verdikt `rejected` gegen `77b6337f0`.
Reviewer, Persona und Autoritätsgrenzen unverändert:
`Kathryn-Kolos-20260822T115500Z`, privilegierter Integrator, zed/claude-opus-5.

---

## 1. Geprüfte Baseline

| Gegenstand | Wert |
|---|---|
| Neuer Tip | `0038-29` @ `db58f0891` |
| Substanziell (Nacharbeit) | `25df30367` |
| Bookkeeping | `db58f0891` |
| Vorheriger, von mir zurückgewiesener Stand | `77b6337f0` |
| Implementierer der Nacharbeit | `Kathryn-Chakotay-20260822T124000Z`, unprivilegiert, anderer Agent als der Erstimplementierer |
| Review-Worktree | `.review-worktrees/0038-29-kolos-r2-db58f0891` (`--detach` auf `db58f0891`) |
| Review-Branch | `review-0038-29-kolos-20260822T115500Z-r2` |

Änderungsumfang `77b6337f0 → db58f0891` — fünf Pfade, keiner außerhalb des erwarteten
Scopes, **kein** Altpublisher berührt:

```
A  TODO-Kathryn-Chakotay-0038-29-20260822T124000Z.md   +128
M  TODO.md                                               +4 -2
M  _src/tools/publish_approved_subtree.py              +155 -28
M  _src/tools/test_publish_approved_subtree.py         +122 -7
M  docs/pipeline/tools.md                               +48 -5
```

`_src/publish.sh` (`8bdbbe96a…`) und `_src/tools/publish_public_site.sh`
(`a65c1f75e…`) sind über beide Commits hinweg **objektidentisch** mit `main`.

---

## 2. Die vier Kernbefunde, einzeln nachgeprüft

### F1 — Falsche Validierungsaussage · **geschlossen**

`TODO.md` benennt die Korrektur jetzt ausdrücklich, statt sie still zu ersetzen:

> **Corrected 2026-08-22 after review finding F1 (`536860ce4`): the original wording
> „0 findings for the two new files" was false.**

Der neue Text gibt an: `verdict: PASS`, exit 0, `unresolved_critical: 0`,
`policy_errors: 0`, `advisory: 38`, `disposed_critical: 24`, `findings: 73`, **ein**
`AUTO010`-Advisory auf `publish_approved_subtree.py:491`, **0** auf der Testdatei.

**Mein eigener Lauf gegen den committeten Stand `db58f0891`:**

```
verdict: PASS, exit 0
counts: {"advisory": 38, "disposed_critical": 24, "findings": 73,
         "policy_errors": 0, "unresolved_critical": 0}
findings auf dem Werkzeug: 1  -> AUTO010 high advisory line 491 'target.unlink()'
findings auf der Testdatei: 0
```

Zeile für Zeile deckungsgleich. Die Verschiebung 432 → 491 erklärt sich vollständig
aus den 155 eingefügten Zeilen. Die Art der Korrektur ist genau richtig: eine falsche
Zahl still gegen eine richtige zu tauschen hätte den Vorgang gerettet, aber die Spur
gelöscht; der Datensatz sagt jetzt, was falsch war und warum es korrigiert wurde.

### F2 — Verschwiegener Defekt von Werkzeug 2 · **geschlossen, und über das Verlangte hinaus**

Die Tabellenzeile behauptet keine Revisionstreue mehr, sondern trennt ausdrücklich
Dateiliste (aus der Revision) von Inhalten (aus dem Arbeitsverzeichnis) und schließt
mit „**nur korrekt, wenn die gewünschte Revision zugleich ausgecheckt ist**". Darunter
steht ein eigener, als solcher gekennzeichneter Defekthinweis.

Der Hinweis enthält ein Detail, das **in meinem Erstbericht nicht stand**: die Pipe
maskiert den Fehlschlag. Ich habe das nicht übernommen, sondern **selbst hermetisch
nachgestellt** — frisches `git init`, eine Datei nur in der Revision, danach entfernt,
dann exakt das Muster aus Zeile 80:

```
Dateiliste aus der Revision : always.txt only-in-rev.txt   (2 Pfade)
tar -cf - -C "$REPO_ROOT" -T "$LIST" | tar -xf - -C "$OUT"
Pipeline-Exit ($?)          : 0
stderr des ersten tar       : tar: only-in-rev.txt: Cannot stat: No such file or directory
                              tar: Error exit delayed from previous errors.
exportiert                  : always.txt                   (1 Pfad)
```

**Bestätigt.** Der erste `tar` scheitert und meldet es, der Pipeline-Status ist der des
zweiten, und der Lauf produziert lautlos einen unvollständigen Export. Chakotays
Zusatzbefund ist richtig und macht den Defekthinweis deutlich brauchbarer als meine
eigene Formulierung es gewesen wäre: er erklärt, *warum* der Fehlschlag unbemerkt
bleibt, und nicht nur *dass* er es tut.

**Eine kleine Ungenauigkeit im Beleg** (nicht sperrend, siehe N2): der Hinweis
verweist für die Beobachtung „`Cannot stat` für alle 2.248 Pfade" auf „siehe
Integrationsreview zu `0038-29`". Diese Beobachtung stand in meinem Erstbericht
`536860ce4` nicht. Mit diesem Nachreview steht der reproduzierte Mechanismus dort nun
tatsächlich, der Verweis wird also durch das vorliegende Dokument eingelöst; sauberer
wäre, zusätzlich Chakotays Claim-Datei zu nennen, in der die 2.248-Pfad-Beobachtung
selbst festgehalten ist.

### F3 — „Exit 1 = nichts publiziert" war unwahr · **geschlossen, durch Verhaltensänderung**

Er hat nicht den Text geglättet, sondern das Verhalten geändert — die richtige
Entscheidung, denn eine reine Textlösung hätte den erreichbaren Zustand *Ziel mutiert,
null Evidenz* bestehen lassen. Neu: `PublicationIncomplete(Refusal)`, ein
`progress`-Dict, das `destination_mutated` unmittelbar **vor** dem ersten Schreib- und
vor dem ersten Löschvorgang umlegt, ein `incomplete`-Evidenzsatz und ein
`verify-failed`-Journalsatz.

Ich habe **beide** Pfade durch echte Fehlerinjektion ausgelöst, nicht am Test des
Implementierers geprüft:

**(a) `OSError` mitten in der Schreibphase** — Ziel enthält ein Verzeichnis dort, wo
eine Quelldatei hin muss; die alphabetisch erste Datei wird vorher erfolgreich
geschrieben:

```
exit 1
stderr: filesystem error AFTER the destination was already modified,
        publication not completed: [Errno 21] Is a directory: …/.z.html.87985.tmp -> …/z.html
Evidenz: state=incomplete  published=False  destination_mutated=True
         written=['a.html']  removed=[]  authorization_ref=DEC-X
Journal: write status=0
aussen: unverändert
```

**(b) Nachverifikation schlägt fehl** — `_write_file` gepatcht, so dass nach dem
zweiten Schreiben eine fremde Datei im Zielteilbaum auftaucht (simulierte
Fremdeinwirkung während des Laufs):

```
run() rc = 1
stderr: post-publication verification failed: … The destination WAS modified and is
        left as it stands; see the incomplete evidence record
Evidenz: state=incomplete  published=False  destination_mutated=True
         written=['a.html','b.html']  removed=[]
Journal: write status=0 / write status=0 / verify-failed status=1
Zielteilbaum: a.html, b.html, INTRUDER.html
aussen: unverändert
```

Beide Male: Exit 1, ausdrückliche Meldung „das Ziel WURDE verändert", vollständiger
`incomplete`-Evidenzsatz mit `written`/`removed`, passender Journalsatz, und **nichts
außerhalb des Teilbaums berührt**. Der Zustand ist damit rekonstruierbar — genau das,
was F3 verlangt hat.

**Die unqualifizierte Zusicherung der Vor-Schreib-Schranken bleibt bestehen.** Ich habe
alle 21 Verweigerungsfälle aus dem Erstreview gegen den neuen Stand wiederholt (Abschnitt 3):
in keinem einzigen wurde geschrieben, und in keinem einzigen entstand fälschlich ein
`incomplete`-Evidenzsatz. Der neue Pfad feuert nur dort, wo er soll.

### F4 — Verweigerungen aus dem Ziel meldeten „source" · **geschlossen**

`collect_regular_files(root, label=…)` reicht die Beschriftung durch. Nachgeprüft:

| Auslöser | vorher | jetzt |
|---|---|---|
| Symlink im Zielteilbaum | „symbolic link in **source** …" | „symbolic link in **destination subtree** is not publishable: link.txt" |
| Zielteilbaum ist eine reguläre Datei | „**source** is not an existing directory" | „**destination subtree** is not an existing directory: …/dest/score" |
| Quelle fehlt wirklich | „source …" | „source …" (unverändert korrekt, eigener Test dafür vorhanden) |

### F5, F6, F8 — **erledigt**

- **F6** verhaltenswirksam und von mir verifiziert: ohne `--evidence` meldet der
  Dry-Run „`… 23 more (full list only with --evidence; not recorded in this run)`",
  mit `--evidence` weiterhin „`… 23 more (full list in the evidence record)`".
- **F5** und **F8** in `tools.md` dokumentiert (blockierender Symlink im Ziel;
  Dateirechte werden nicht übernommen).

### F7, F9 — bewusst nicht geändert

Korrekt. F7 hatte ich ausdrücklich nicht zur Änderung verlangt; F9 ist ein akzeptiertes
Restrisiko, dessen Erkennbarkeit F3 sogar verbessert.

---

## 3. Hat die Nacharbeit etwas kaputt gemacht?

**Nein.** Alle 21 Angriffs- und Randfälle des Erstreviews erneut gegen `db58f0891`:

| Fall | Exit | Fall | Exit |
|---|---|---|---|
| falscher Digest + `--apply` | 1 | Symlink (Datei) in der Quelle | 1 |
| `--subtree ../escape` | 1 | Symlink (Verzeichnis) in der Quelle | 1 |
| `--subtree /etc` | 1 | Quelle ist selbst ein Symlink | 1 |
| `--subtree score/../../out` | 1 | Ziel-Teilbaum über Symlink | 1 |
| `--subtree _src` | 1 | dito, verschachtelt | 1 |
| `--apply` ohne `--evidence` | 1 | Quelle == Zielwurzel | 1 |
| leere `--authorization-ref` | 1 | Quelle im Zielteilbaum | 1 |
| nicht-hex Digest | 1 | Evidenz im Teilbaum | 1 |
| fehlende `--authorization-ref` | 2 | Journal im Teilbaum | 1 |
| kein Modus gewählt | 2 | Privatpfad in der Quelle | 1 |
| | | Evidenz existiert bereits | 1 |

**21/21 korrekt.** Danach: Zielverzeichnis unverändert, kein `TOPSECRET` aus den
Symlink-Zielen im Ziel, **keine** Evidenzdatei angelegt, und die vier unbeteiligten
Dateien außerhalb byteidentisch.

Weiter nachgefahren:

- **Glücklicher Pfad**: `created=2 modified=0 deleted=2`, leeres Verzeichnis gepruned,
  Exit 0, Zieldigest == freigegebener Digest; die vier fremden Dateien außerhalb
  **byteidentisch** (`diff` leer). Zweiter Lauf: Exit 0, idempotent.
- **Digest gegen den echten freigegebenen Baum**
  (`/tmp/autodocs-0019-10-preview-20260822T003000Z/export`):
  `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`, 2248 Dateien —
  **unverändert korrekt**.
- **Testsuite**: `Ran 30 tests … OK`, Exit 0 (vorher 22). Die 8 neuen Tests treffen
  genau F3/F4/F6 und enthalten zusätzlich
  `test_ordinary_refusal_leaves_the_destination_untouched` — eine Regressionsschranke
  für exakt die Zusicherung, um die es bei F3 ging. Gut gewählt.
- **`automation_safety`**: unverändert `PASS`, Exit 0, Zählstände identisch zum
  Erstreview.

---

## 4. Neue Befunde aus diesem Nachreview

### N1 — minor, nicht sperrend. Scheitert das Schreiben der Evidenz selbst, entkommt ein Traceback.

Gefunden beim gezielten Suchen nach Pfaden, die F3 neu geöffnet haben könnte.

`--evidence` wird beim Start nur auf **Nicht-Existenz** geprüft, nicht auf
Benutzbarkeit. Ein Pfad wie `<datei>/ev.json` (Elternteil ist eine reguläre Datei)
kommt daher durch alle Schranken, das Ziel wird **vollständig geschrieben**, und erst
danach scheitert `_write_evidence()` an
`evidence_path.parent.mkdir(...)`. Weil `_write_evidence()` in den beiden
Ausnahmebehandlungen (`except PublicationIncomplete`, `except OSError`) *außerhalb*
des `try` liegt, wird der `FileExistsError` nicht mehr gefangen:

```
FileExistsError: [Errno 17] File exists: /tmp/.../blocker
exit = 1
Ziel danach: 1 Datei geschrieben, KEINE Evidenz
aussen: unverändert
```

Reproduziert auf **beiden** Pfaden — dem gewöhnlichen Erfolgspfad und dem
`incomplete`-Pfad.

Einordnung, damit die Schwere nicht überzeichnet wird:

- Es wird **keine Schranke** geschwächt: alle Pfad-, Symlink-, Überlappungs-,
  Autoritäts- und Digest-Prüfungen greifen unverändert vorher.
- Es wird **nichts Falsches publiziert**: die Zieldateien sind korrekt geschrieben.
- Außerhalb des Teilbaums bleibt alles unberührt (geprüft).
- Der Exit-Code ist weiterhin `1`.
- Der *Zustand* ist nicht neu: auf dem alten Stand endete derselbe Aufruf in
  „filesystem error, publication not completed" — ebenfalls Ziel mutiert, ebenfalls
  keine Evidenz. **Neu ist nur, dass die Meldung jetzt ein Traceback ist** statt eines
  Satzes. Insofern eine kosmetische Regression auf einem Pfad, den F3 nicht adressiert
  hat, plus eine Validierungslücke, die es vorher schon gab.

**Empfehlung (ein Vorschlag, keine Auflage):** `--evidence` beim Start zusätzlich auf
Benutzbarkeit prüfen — Elternteil ist ein Verzeichnis oder anlegbar. Damit würde N1 zu
einer **Vor-Schreib-Verweigerung**, also strikt besser als jede Behandlung im
Nachhinein; ergänzend `_write_evidence()` in den beiden Handlern in `try/except OSError`
fassen, damit ein Fehlschlag dort als Satz und nicht als Traceback erscheint.

### N2 — kosmetisch. Ein Beleg im Defekthinweis zeigt auf ein Dokument, das ihn nicht enthielt.

Siehe F2 oben. Der Verweis „siehe Integrationsreview zu `0038-29`" für die
2.248-Pfad-Beobachtung wird durch das vorliegende Nachreview eingelöst; ein zusätzlicher
Verweis auf Chakotays Claim-Datei wäre genauer. Nicht sperrend.

### N3 — Bestätigung des vorgelegten Nebenfunds: `automation_safety` zählt auf einem schmutzigen Baum doppelt.

`kathryn` hat mich ausdrücklich um Bestätigung gebeten. **Bestätigt, reproduziert.**

Vorgehen: im committeten Zustand drei Leerzeilen in
`_src/tools/publish_approved_subtree.py` eingefügt (nicht committet), sodass die
`AUTO010`-Zeile sich verschiebt; ein physischer Aufruf von
`python3 _src/tools/automation_safety.py --json`; danach `git checkout --` zur
Wiederherstellung.

| | sauberer Baum | schmutziger Baum |
|---|---|---|
| `findings` | 73 | **74** |
| `advisory` | 38 | **39** |
| `AUTO010` auf dem Werkzeug | 1 (Zeile 491) | **2** (Zeilen 491 **und** 494) |
| `evidence_sha256` beider Einträge | — | **identisch** (`ba10f4fccc3b…`) |
| `verdict` | PASS | PASS |

Es ist dieselbe Codestelle, zweimal gezählt: einmal aus dem Index, einmal aus dem
Arbeitsbaum. Chakotays Ursachenanalyse (`_read_tracked_sources()` scannt beide, wenn sie
auseinanderlaufen, während `_dedupe()` auf die Zeilennummer schlüsselt) deckt sich mit
dem Beobachteten.

Zwei Punkte, die ich der Projektleitung für den eigenen Vorgang mitgeben möchte:

1. **Die Doppelzählung ist stumm.** Nichts in der Ausgabe kennzeichnet einen der beiden
   Einträge als Index-/Arbeitsbaum-Dublette; das identische `evidence_sha256` ist der
   einzige Hinweis, und nur, wenn jemand danach sieht.
2. **Die Fehlerrichtung ist Inflation, nicht Verdeckung** — ein echtes Finding kann so
   nicht verschwinden. Aber die aufgeblähten Zahlen sind genau jene, die Agenten in ihre
   Completion-Evidence übertragen, und ein Reviewer auf sauberem Baum kann sie dann nicht
   reproduzieren. Das ist dieselbe Fehlerklasse, an der diese Lieferung mit F1 schon
   einmal gescheitert ist. Chakotays Vorgehen — maßgebliche Zahlen erst **nach** dem
   substanziellen Commit nehmen — ist die richtige Gegenmaßnahme und sollte, wenn ein
   Vorgang daraus wird, als Regel für alle Agenten festgehalten werden.

Kein Defekt von `0038-29`. Ein eigener Vorgang ist gerechtfertigt.

---

## 5. Ergebnis

**`accepted`.**

Beide Pflichtmängel sind geschlossen, und zwar ehrlich:

- **F1** ist nicht still korrigiert, sondern als Korrektur benannt — die Spur bleibt
  lesbar. Die neuen Zahlen decken sich exakt mit meiner eigenen Messung.
- **F2** ist korrigiert und **übertrifft** die verlangte Korrektur: der
  Pipe-Maskierungsmechanismus erklärt, warum der Defekt unbemerkt bleibt. Ich habe ihn
  unabhängig hermetisch nachgestellt; er stimmt.
- **F3** ist als Verhaltensänderung gelöst statt als Textkosmetik. Beide Fehlerpfade
  habe ich durch echte Fehlerinjektion ausgelöst; beide liefern jetzt einen
  rekonstruierbaren Zustand.
- **F4, F5, F6, F8** erledigt; **F7, F9** korrekt unangetastet.

Keine Regression: 21/21 Verweigerungsfälle unverändert korrekt, kein Schreibvorgang,
keine fälschlich erzeugte Evidenz, Byteidentität außerhalb des Teilbaums erneut belegt,
Digest gegen den echten freigegebenen Baum unverändert, Altpublisher objektidentisch,
30/30 Tests, `automation_safety` unverändert `PASS`.

**N1** bleibt offen und ist bewusst **nicht** sperrend: es schwächt keine Schranke,
publiziert nichts Falsches, berührt nichts außerhalb des Teilbaums, hinterlässt
denselben Zielzustand wie vor der Nacharbeit und unterscheidet sich vom alten Verhalten
nur durch ein Traceback statt eines Satzes. Es gehört in eine spätere Runde, nicht in
eine zweite Zurückweisung. **N2** ist kosmetisch, **N3** ist kein Defekt dieses Tasks.

Ich setze `Acceptance: ✓` in meinem Worktree, wie von der Projektleitung ausdrücklich
autorisiert. Der Acceptance-Record steht in `TODO.md` unter `0038-29` und bindet
Vertrag, Werkzeugmanifest und Review-REF.

---

## 6. Checkpoint-Verdikt

**`Integration review: mandatory` — unverändert BESTÄTIGT.** Die Begründung aus dem
Erstbericht (Abschnitt 7 in `report.md`) gilt fort und ist durch diese Runde eher
gestärkt worden: der Knoten liefert den Mechanismus für einen irreversiblen externen
Effekt, sein gesamter Sicherheitswert steckt in Schranken, deren Ausfall lautlos wäre,
und die Nacharbeit selbst hat gezeigt, wie leicht eine Verhaltensänderung an dieser
Stelle einen neuen Randpfad öffnet (N1) — gefunden, weil jemand gezielt danach gesucht
hat, nicht weil ein Test angeschlagen hätte.

Die Empfehlung aus dem Erstbericht bleibt bestehen: den Checkpoint auf **jede künftige
Änderung an `_src/tools/publish_approved_subtree.py`** erstrecken. Die Schranken sind
das Produkt. Die verbindliche Bestätigung oder eine begründete Herabstufung bleibt beim
Architekten, spätestens beim Abschluss von Feature `0038`.

---

## 7. Autoritätsgrenzen und Aufzeichnung

Unverändert eingehalten: kein Merge nach `main`, kein `DONE.md`, kein Push, keine
Publikation, kein Netzwerkzugriff auf ein Deploy-Ziel, keine Mutation des
Root-Checkouts, kein `git update-ref`. `refs/heads/main` von mir nicht bewegt. Der
Branch `0038-29` (`db58f0891`) ist von mir nicht verändert worden; meine Arbeit liegt
auf `review-0038-29-kolos-20260822T115500Z-r2`.

Einzige Mutation außerhalb meines Berichts: für N3 habe ich in meinem **eigenen,
losgelösten** Review-Worktree drei Leerzeilen in eine Datei eingefügt, den Scan laufen
lassen und den Zustand mit `git checkout --` sofort wiederhergestellt. Kein Branch, kein
Commit und kein fremder Worktree war davon berührt.

**`DEC-0044-013`:** Persona (privilegierter Integrator) unverändert verschieden von der
des Dispatchers (Projektleiter `kathryn`), des Erstimplementierers
(`Kathryn-Tuvok-20260822T113500Z`) und des Nacharbeit-Implementierers
(`Kathryn-Chakotay-20260822T124000Z`). Das Erstbriefing steht wortwörtlich in
`report.md` Abschnitt 8.2. Das Briefing dieser zweiten Runde ist unten wortwörtlich
aufgezeichnet.

### 7.1 Welchen Kontext ich in dieser Runde hatte

**Bekommen:** das unten wiedergegebene Briefing, einschließlich Chakotays Selbstangaben
und der Angabe, dass `kathryn` 30 Tests und den Digest bereits selbst nachgefahren hat;
weiterhin Lesezugriff auf das gesamte Repository und die agent-inbox.

**Nicht bekommen und nicht benutzt:** keine Vorgabe, wie das Ergebnis lauten soll — das
Briefing sagt ausdrücklich, ein erneutes `rejected` sei völlig in Ordnung; keinen Kontakt
zu einem der beiden Implementierer; keine Zugangsdaten; keinen Netzwerkzugriff.

**Wichtig für die Unabhängigkeit:** `kathryn` bot ausdrücklich an, die bereits
nachgefahrenen Prüfungen nicht zu wiederholen. Ich habe sie **trotzdem alle selbst
ausgeführt** (30 Tests, Digest gegen den echten Baum, `automation_safety`) und zusätzlich
21 Angriffsfälle, zwei Fehlerinjektionen, die hermetische Pipe-Nachstellung und die
N3-Reproduktion gebaut. N1 stammt aus dieser eigenen Prüfung und kommt in keiner der
Vorlagen vor.

### 7.2 Briefing dieser Runde, wortwörtlich und ungekürzt

> Kathryn-Kolos-20260822T115500Z — Nachreview zu 0038-29, deine Befunde sind bearbeitet. Deine Rolle, Persona und Autoritaetsgrenzen bleiben unveraendert; dies ist die Fortsetzung desselben Reviewauftrags, kein neuer.
>
> DEIN VERDIKT WAR RICHTIG UND IST ANGENOMMEN. Beide Pflichtmaengel waren echt. F2 war der wertvollste Fund des Tages: eine Governance-Doku, die dem defekten Werkzeug genau die Eigenschaft zuschreibt, die es nicht hat — das waere nach main gewandert und haette kuenftige Operatoren in Richtung des kaputten Werkzeugs gelenkt.
>
> NEUER STAND: Branch `0038-29`, Tip `db58f0891`. Zwei neue Commits ueber dem von dir geprueften `77b6337f0`:
>   `25df30367` substanziell — F1, F2, F3, F4, F5, F6, F8
>   `db58f0891` bookkeeping
>
> Implementierer der Nacharbeit: `Kathryn-Chakotay-20260822T124000Z`, unprivilegiert, anderer Agent als der Erstimplementierer.
>
> WAS ER GEMACHT HAT (seine Angaben, von mir noch nicht vollstaendig geprueft — pruef sie selbst):
> - **F1**: Evidenzzeile in TODO.md auf das gemessene Ergebnis umgestellt; die falsche Formulierung ist ausdruecklich als korrigiert benannt statt still ersetzt. Er bestaetigt deine Messung: ein AUTO010, high/advisory, auf dem Werkzeug, 0 auf der Testdatei.
> - **F2**: Tabellenzeile korrigiert plus ausdruecklicher Defektvermerk zu `publish_public_site.sh:80`, mit der Bedingung, unter der das Werkzeug korrekt ist. **Er hat den Defekt selbst in einer isolierten Fixture reproduziert und ein Detail gefunden, das in deinem Bericht nicht steht: die Pipe maskiert den Fehlschlag** — nur der Status des zweiten `tar` zaehlt, deshalb laeuft der Durchlauf weiter. Steht jetzt in tools.md.
> - **F3**: Er hat sich fuer die Verhaltensaenderung entschieden, nicht fuer die blosse Textpraezisierung. Neue `PublicationIncomplete(Refusal)`: eine fehlgeschlagene Nachverifikation und ein `OSError` mitten im Schreiben sagen jetzt „das Ziel WURDE veraendert", schreiben einen Evidenzsatz mit `"state": "incomplete"` samt `written`/`removed` und haengen einen `verify-failed`-Journalsatz an. Exit bleibt 1; die Zusicherung der Vor-Schreib-Schranken bleibt unqualifiziert und ist getestet. Begruendung: eine reine Textloesung liesse einen erreichbaren Zustand zurueck — Ziel mutiert, null Evidenz —, den niemand rekonstruieren kann.
> - **F4**: `collect_regular_files(root, label=…)` durchgereicht; Verweigerungen aus dem Ziel benennen jetzt das Ziel.
> - **F5, F8**: in tools.md dokumentiert. **F6**: Rest-Hinweis im Dry-Run zeigt nur dann auf den Evidenzsatz, wenn `--evidence` gegeben wurde.
> - **Nicht geaendert**: F7 (du hast keine Aenderung verlangt), F9 (akzeptiertes Restrisiko TOCTOU; F3 verbessert die Erkennbarkeit).
>
> SEINE ZAHLEN: 30 Tests OK (vorher 22); automation_safety unveraendert PASS/exit 0, das eine AUTO010 jetzt auf Zeile 491; Digest gegen den echten Baum unveraendert `7c514686ba…08283`, 2248 Dateien; beide Altpublisher byteidentisch.
>
> VON MIR SELBST NACHGEFAHREN, damit du es nicht doppelt tun musst — aber pruef es trotzdem, wenn du magst: 30 Tests OK, und `compute_tree_digest()` liefert gegen `/tmp/autodocs-0019-10-preview-20260822T003000Z/export` weiterhin exakt den freigegebenen Digest.
>
> EIN NEBENFUND VON IHM, den ich dir vorlege, weil er deine eigene Messung betrifft: Auf einem **uncommitteten** Baum zaehlt `automation_safety.py` ein verschobenes Finding doppelt — er sah zwei AUTO010-Eintraege (Zeilen 432 und 491) mit identischer Evidenz bei einem physischen Aufruf. Ursache laut ihm: `_read_tracked_sources()` in `_src/tools/automation_safety.py:2649` scannt Index UND Arbeitsbaum, wenn sie auseinanderlaufen, waehrend `_dedupe()` auf die Zeilennummer schluesselt. Er hat seine massgeblichen Zahlen deshalb nach dem substanziellen Commit genommen. Das ist kein 0038-29-Defekt, sondern ein Messartefakt des Gates, das eine Evidenzzahl verfaelschen kann — also genau die Fehlerklasse, an der diese Lieferung schon einmal gescheitert ist. Sag mir in deiner Rueckmeldung, ob du das bestaetigst; wenn ja, lege ich dafuer einen eigenen Vorgang an.
>
> DEIN AUFTRAG JETZT: Nachreview gegen `db58f0891`. Konzentrier dich auf F1 bis F4 und darauf, ob die Nacharbeit etwas kaputt gemacht hat — insbesondere ob die Vor-Schreib-Schranken ihre unqualifizierte Zusicherung behalten und ob F3 keinen neuen Pfad geoeffnet hat, auf dem das Ziel ohne Evidenz mutiert zurueckbleibt. Deine 13 Angriffsfaelle noch einmal gegen den neuen Stand waeren wertvoll.
>
> Unveraendert: kein Merge nach main, kein DONE.md, kein Push, keine Publikation, kein Netzzugriff, keine Root-Mutation. Du darfst `Acceptance: ✓` in deinem Worktree setzen, wenn du diesmal zustimmst — ich trage es nach main.
>
> Ergebnis wieder genau eines: accepted / rejected / inconclusive, plus Checkpoint-Verdikt. Ein erneutes rejected ist voellig in Ordnung, wenn es begruendet ist.
>
> -- kathryn, Projektleiter

---

## 8. Was ich auch in dieser Runde nicht prüfen konnte

Unverändert gegenüber `report.md` Abschnitt 9:

1. **Das nachgelagerte Publizieren** (Operator-Commit und Push nach `2b-rs/autodocs`) —
   kein Auftrag, kein Zugang, kein Netzwerkzugriff unternommen. Die Kette
   *Werkzeug → Commit → Push* ist durch dieses Review **nicht** abgedeckt.
2. **Die Zahl `4.133`** aus dem Ausgangsvorfall — nicht nachgerechnet, dieses Review
   hängt nicht daran.
3. **Nicht-ASCII-Pfade und NFC/NFD-Normalisierung** — weiterhin nur ASCII auf
   macOS/APFS geprüft.
4. **Parallele `--apply`-Läufe** auf dieselbe Zielwurzel — weiterhin kein Sperrmittel im
   Werkzeug, weiterhin nicht getestet.
5. **Die 2.248-Pfad-Beobachtung** aus Chakotays `publish_public_site.sh`-Fixture habe ich
   nicht in dieser Größe wiederholt; ich habe stattdessen den **Mechanismus** hermetisch
   an einem Zwei-Datei-Fall nachgestellt und bestätigt.

---

*Erstellt von `Kathryn-Kolos-20260822T115500Z`, privilegierter Integrator,
zed/claude-opus-5, 2026-08-22. `Acceptance: ✓` in diesem Worktree gesetzt, nicht auf
`main`. `main` von mir nicht bewegt. Nichts publiziert.*
