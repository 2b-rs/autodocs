# Entscheidungsvorlage — Konfigurationsmanagement: Branching- und Merging-Strategie

**Dokumenttyp:** Entscheidungsvorlage. **Dies ist keine Entscheidung.**
**Ersteller:** Projektleiter Kathryn (`agent:kathryn:projektleiter:branching-strategie:20260821T090000Z`),
Fähigkeitsklasse `unprivileged`, Rolle gemäß `DEC-ROLE-001` — **ohne Managementautorität**.
Der Projektleiter bereitet Entscheidungen vor und moderiert; er trifft sie nicht.
**Adressat:** Management (aktueller User oder registrierte Autorität).
**Datum:** 2026-08-21.
**Anlass:** Management-Anweisung, überbracht von Commander Seven
(agent-inbox, Thread `0038`, Nachricht `1787300831729-0af51b3a`, 2026-08-21T08:27:11Z):
die Branching-/Merging-Strategie sei überarbeitungsbedürftig, der Projektleiter
solle eine Entscheidungsvorlage erstellen.
**Betroffene Entscheidungen:** `DEC-0044-001`, `DEC-0044-002`, `DEC-0044-003`.
**Betroffene Arbeit:** Task `0044-01` (drei `[u]`-Verdikte), Task `0044-02`.

---

## 0. Zusammenfassung für das Management

Vier Entscheidungen liegen zur Beschlussfassung vor. Der gemeinsame Kern:

> **Die Herkunft eines Policy-Commits ist nachträglich nicht feststellbar,
> aber im Moment der Operation beobachtbar.**

Das ist keine Werkzeugschwäche, sondern eine Eigenschaft von Gits Datenmodell.
Drei Korrekturrunden an `check_policy_provenance.py` haben das erst nach und
nach sichtbar gemacht. Solange wir Herkunft *rekonstruieren* wollen, bleibt
`DEC-0044-002` unprüfbar; sobald wir sie *aufzeichnen*, wird sie prüfbar.

| | Entscheidung | Empfehlung |
|---|---|---|
| **E1** | Wie wird Policy-Herkunft festgestellt? | **Aufzeichnen statt rekonstruieren** (Option C) |
| **E2** | Wo wird die Regel durchgesetzt? | **Mehrschichtig**: Hook als Netz, Integrator als Tor (Option C) |
| **E3** | Umgang mit dem geteilten Root-Checkout | **Schreibverbot + Hygieneprüfung vor jeder Integration** (Option B) |
| **E4** | Reichweite von `DEC-0044-002` | **Erweitern** um die Aufzeichnungspflicht (Option B) |

E1 und E4 gehören zusammen; E2 ist die Durchsetzungsfrage dazu; E3 ist eine
**andere Fehlerklasse** und unabhängig entscheidbar — sie ist die einzige mit
einem aktuell scharfen Schaden.

**Dringlichkeit:** E3 ist sofort. Der Index des Root-Checkouts trägt derzeit
138 Dateien mit 28.683 Löschungen; ein unbeschränktes `git commit` dort nimmt
den Abschluss von Feature `0040` zurück. E1/E2/E4 sind wichtig, aber nicht
tagesaktuell gefährlich.

---

## 1. Beweislage

Alle vier Befunde stammen aus realer Arbeit dieser Session, nicht aus einer
Risikoanalyse am grünen Tisch.

### 1.1 Der strukturelle blinde Fleck (bewiesen, nicht vermutet)

Task `0044-01` sollte `DEC-0044-002` maschinell prüfbar machen. Der privilegierte
Integrator `seven-tom` hat das Ergebnis dreimal unabhängig geprüft:

| Runde | Befund | Art |
|---|---|---|
| 1 | Detached-HEAD-Worktree erzeugt `(no branch)` → als Fremd-Branch gewertet | falsch **positiv** |
| 2 | Stale-WIP-Branch bzw. nachgelagerter Review-Branch → als Fremd-Branch gewertet | falsch **positiv** |
| 3 | Per Fast-Forward absorbierter Fremd-Commit → als sauber gewertet | falsch **negativ** |

Nach Runde 2 wurde der Klassifikator vollständig umgeschrieben: Klassifikation
nur noch über Commit-Topologie (First-Parent-Kette + Merge-Commit-Status), nicht
mehr über Branch-Zugehörigkeit. Das beseitigte beide Falschalarme — und legte
den vierten Defekt frei.

**Der Kern:** Ein per `git merge --ff-only` oder `git update-ref` absorbierter
Commit hat **genau einen Parent** und liegt auf der First-Parent-Kette des
empfangenden Branches. Er ist damit topologisch **nicht unterscheidbar** von
einem dort tatsächlich entstandenen Commit. Git legt keinen Datensatz an,
welcher Branch der Autoren-Branch war.

Tom hat das in einem eigenständigen Minimal-Repro nachgewiesen (Commit
`b62df43a8`, drittes `[u]`-Verdikt unter `0044-01`). Ich habe die
Eigenschaft unabhängig nachvollzogen (Abschnitt 2.2).

**Warum das schwerer wiegt als die ersten beiden Runden:** Ein Falschalarm
kostet einen manuellen Blick. Ein falsches Negativ lässt genau die Verletzung
durch, für deren Erkennung das Werkzeug existiert.

### 1.2 Die eigene Integrationspraxis ist das Gegenbeispiel

Commander Seven hat `main` in dieser Session **fünfmal** per `git update-ref`
im Fast-Forward vorgerückt — Feature `0038` vollständig, dazu `0037-37`,
`0037-49`, `0041-01`, `0043-01`. Jede dieser Integrationen war handgeprüft und
legitim.

Das ist der entscheidende Punkt für die Bewertung: **Fast-Forward ist nicht
Missbrauch, sondern unser aktueller Integrationsweg.** Ein Verbot wäre kein
Schließen eines Schlupflochs, sondern eine Änderung des Arbeitsverfahrens. Und
umgekehrt: Das Modell kann Sevens verifizierte Arbeit derzeit von einer echten
Verletzung mechanisch nicht unterscheiden — es verlässt sich jedes Mal auf die
Sorgfalt des Integrators.

### 1.3 Der geteilte Root-Checkout ist ein scharfer Blindgänger

Der Index des Haupt-Checkouts `/Users/tobias.anton/devel/autodocs` weicht von
`HEAD` ab. Eigene Messung, 2026-08-21:

```
$ git diff --cached --stat HEAD | tail -1
138 files changed, 2687 insertions(+), 28683 deletions(-)
```

Der gestagte Baum entspricht einem alten Stand vor dem Abschluss von Feature
`0040`. Ein unbeschränktes `git commit` dort — ohne Pfadbegrenzung, wie es
Agenten regelmäßig ausführen — würde diesen Abschluss stillschweigend
zurücknehmen.

Seven hat den Zustand als dauerhaftes Git-Objekt gesichert (Tag
`preserved/root-index-20260821`), statt ihn zu verwerfen. **Aufgeräumt ist er
nicht.** Gefunden wurde er durch manuelle Inspektion bei anderer Gelegenheit.

Das ist eine **andere Fehlerklasse** als 1.1: Der Schaden sitzt im
Arbeitsverzeichniszustand, nicht in der Commit-Historie. Keine
Historienanalyse — auch kein perfekter Provenance-Checker — hätte ihn gefunden.

### 1.4 Was `DEC-0044-001..003` abdecken — und was nicht

| Regel | Als Prinzip | Durchsetzung |
|---|---|---|
| `DEC-0044-001` Ziel-Branch-Policy maßgeblich | tragfähig | Prosa; Integrator prüft |
| `DEC-0044-001` Pull-in erlaubt | tragfähig | Prosa |
| `DEC-0044-002` Herkunftsverbot | tragfähig | **mechanisch nicht prüfbar** (1.1) |
| `DEC-0044-003` Risikointegration einstimmig | tragfähig | `0044-02`, noch offen |
| Geteilter Arbeitsbaum | **gar nicht adressiert** | keine |

Die Prinzipien stehen nicht zur Disposition. Die Lücke liegt in der
Durchsetzungsschicht — und bei 1.3 im Geltungsbereich.

---

## 2. Ursachenanalyse

### 2.1 Warum keine nachträgliche Prüfung das schließen kann

Git speichert pro Commit: Baum, Parents, Autor, Committer, Nachricht. **Kein
Feld nennt den Branch.** Branches sind bewegliche Zeiger, keine Eigenschaft des
Commits. Nach einem Fast-Forward gilt:

- Der absorbierte Commit hat einen Parent — wie ein nativ entstandener.
- Er liegt auf der First-Parent-Kette — wie ein nativ entstandener.
- `git branch --contains` nennt zwar den Fremd-Branch, aber genau dieses Signal
  war die Ursache der Falschalarme aus Runde 1 und 2 und wurde deshalb bewusst
  aus der Klassifikation entfernt. Es ist zudem **flüchtig**: Wird der
  Fremd-Branch gelöscht, verschwindet der letzte Hinweis rückstandslos.

Daraus folgt: Jede rein nachträgliche, rein lokale Prüfung ist entweder zu
streng (Falschalarme) oder zu lax (falsche Negative). Das ist keine Frage
besserer Implementierung.

### 2.2 Warum es zur Transaktionszeit sehr wohl geht — verifiziert

Im Moment der Operation ist die Information vollständig vorhanden: Der
Ziel-Ref bewegt sich von `alt` nach `neu`, die eingehenden Commits sind
`alt..neu`, und die Fremd-Branches existieren zu diesem Zeitpunkt noch.

Git bietet dafür den `reference-transaction`-Hook (seit Git 2.28; installiert
ist 2.50.1). **Ich habe in einem isolierten Scratch-Repository nachgewiesen:**

1. Der Hook feuert bei `git merge --ff-only` **und** bei `git update-ref` —
   also bei genau den beiden Mechanismen, die 1.1 und 1.2 betreffen. `update-ref`
   umgeht `pre-commit` vollständig, `reference-transaction` nicht.
2. Der Hook kann zur Transaktionszeit die Herkunft feststellen. Ausgabe meines
   Testlaufs bei einer Fast-Forward-Absorption eines Fremd-Branches:

   ```
   FOREIGN-ORIGIN ref=refs/heads/main commit=0952141 also_on=foreign,
   ```

   Das ist exakt der Fall, den Toms Werkzeug nachträglich für sauber hält.

**Wichtige Einschränkung, die die Entscheidung mitprägt:** Hooks liegen unter
`.git/hooks`, sind **nicht versioniert, werden nicht mitgeklont und können
entfernt oder per `core.hooksPath` umgangen werden.** Ein Hook ist ein
Sicherheitsnetz, keine Garantie. Er darf die Prüfpflicht des Integrators nicht
ersetzen. (Günstig: Worktrees teilen sich das gemeinsame `.git`-Verzeichnis —
verifiziert via `git rev-parse --git-common-dir` — ein Hook wirkt also in allen
Worktrees zugleich.)

### 2.3 Warum 1.3 eine eigene Entscheidung braucht

Der Index-Blindgänger entsteht außerhalb der Historie und wird von jeder
historienbasierten Kontrolle prinzipiell nicht erfasst. Er hat eine eigene
Ursache: **Mehrere Agenten teilen sich einen Arbeitsbaum.** Das Repository
betreibt bereits 78 Worktrees; der Root-Checkout ist der einzige, der keinem
Vorgang gehört und trotzdem beschrieben wird.

---

## 3. Vorgelegte Entscheidungen

### E1 — Wie wird die Herkunft eines Policy-Commits festgestellt?

| | Option | Wirkung | Kosten / Risiko |
|---|---|---|---|
| A | **Als Restrisiko dokumentieren**, Prosaregel gegen Fast-Forward-Absorption | billig, sofort | Regel, die Agenten sich merken müssen; genau die Klasse Kontrolle, die hier bereits versagt hat |
| B | **Heuristik** über Reflogs/Zeitstempel | keine Prozessänderung | Reflogs sind lokal, verfallen, sind nicht autoritativ; erzeugt Scheinsicherheit |
| C | **Herkunft aufzeichnen statt rekonstruieren** — Policy-Commits tragen einen Commit-Trailer (z. B. `Policy-Origin-Branch:`), Absorption außerhalb der direkten Vorgängerkette erfordert einen echten Merge-Commit (`--no-ff`) | macht `DEC-0044-002` erstmals belastbar prüfbar; Trailer ist Teil des Commit-Objekts und damit unveränderlich | Verfahrensänderung; Altbestand trägt keine Trailer; Werkzeug muss angepasst werden |
| D | **Fast-Forward generell verbieten** | einfache Regel | trifft die legitime Praxis aus 1.2 hart; erzeugt Merge-Commits ohne inhaltlichen Anlass |

**Empfehlung: C.** Nur C greift die Ursache an. A und B lassen die Lücke offen
und beschreiben sie bloß; D bekämpft das Symptom und beschädigt ein Verfahren,
das nachweislich funktioniert hat.

**Was C ausdrücklich nicht leistet:** Bestehende Commits werden nicht
nachträglich prüfbar. Der Trailer belegt die Herkunft nur, wenn er gesetzt
wurde — ein Agent, der ihn weglässt, verletzt die Regel, ohne dass der Trailer
selbst das aufdeckt. Deshalb hängt C an E2.

### E2 — Wo wird die Regel durchgesetzt?

| | Option | Wirkung | Kosten / Risiko |
|---|---|---|---|
| A | **Nur Prosa** in `branch-workflow.md` | keine | nachweislich unzureichend: `DEC-0044-002` steht seit dem Intake in Prosa und wurde trotzdem nie geprüft |
| B | **Nur Werkzeug**, vom Integrator am Checkpoint ausgeführt | prüfbar am Tor | greift erst spät; die Verletzung ist dann schon committet |
| C | **Mehrschichtig**: `reference-transaction`-Hook zeichnet auf und warnt sofort (2.2), Integrator prüft am Checkpoint verbindlich, Prosa bleibt die Autorität | frühe Erkennung + verbindliches Tor | zwei Artefakte zu pflegen; Hook ist umgehbar und muss pro Arbeitsplatz eingerichtet werden |

**Empfehlung: C**, mit der ausdrücklichen Festlegung: **Der Hook ist ein Netz,
das Tor ist der Integrator.** Ein fehlender oder deaktivierter Hook darf niemals
als „geprüft" gelten. Andernfalls entsteht genau die Scheinsicherheit, vor der
Option B in E1 warnt.

### E3 — Umgang mit dem geteilten Root-Checkout

| | Option | Wirkung | Kosten / Risiko |
|---|---|---|---|
| A | **Nur aufräumen** (Index zurücksetzen, Tag behalten) | beseitigt den aktuellen Blindgänger | die Ursache bleibt; der nächste entsteht genauso |
| B | **Root-Checkout wird schreibgeschützt**: Agenten mutieren ausschließlich in vorgangseigenen Worktrees; zusätzlich Hygieneprüfung (`Index == HEAD`, keine fremden Staged-Bäume) **vor** jeder Integration | beseitigt Ursache und Symptom; entspricht der ohnehin gelebten Praxis (78 Worktrees, eigene Zählung 2026-08-21) | ein zusätzlicher Prüfschritt; Agenten müssen die Regel kennen |
| C | **Nur detektieren** (Prüfwerkzeug, kein Verbot) | macht sichtbar | verhindert nichts |

**Empfehlung: B**, und zwar **unabhängig von E1/E2 sofort**. Dies ist der
einzige Punkt mit gegenwärtigem Schadenpotenzial. Aufräumen (A) ist Teil von B,
aber allein unzureichend.

**Hinweis zur Ausführung:** Das Zurücksetzen des Index ist selbst eine
schadensträchtige Operation an fremdem Zustand. Die Sicherung ist vorhanden —
ich habe `preserved/root-index-20260821` und `preserved/root-unstaged-draft-20260821`
als existierende Tags verifiziert; diese Vorbedingung ist damit erfüllt. Der
Eingriff sollte dennoch protokolliert und von einer benannten Session ausgeführt
werden, nicht beiläufig.

### E4 — Reichweite von `DEC-0044-002`

| | Option | Wirkung |
|---|---|---|
| A | **Unverändert lassen** | Verbot bleibt formuliert, Prüfbarkeit bleibt offen |
| B | **Erweitern**: Das Verbot wird um eine **Aufzeichnungspflicht** ergänzt — wer einen Policy-Commit auf einen Branch bringt, macht dessen Herkunft im Commit-Objekt oder über einen echten Merge-Commit sichtbar; Absorption ohne solchen Nachweis gilt als Verletzung, unabhängig vom Mechanismus | schließt die Lücke auf Ebene der Entscheidung, nicht nur des Werkzeugs |
| C | **Geltungsbereich zusätzlich auf Arbeitsbaumzustand ausdehnen** | vermischt zwei Fehlerklassen (2.3) |

**Empfehlung: B.** C nicht — der Arbeitsbaum gehört in E3, nicht in eine
Herkunftsregel.

**Beweislastumkehr als Kern von B:** Heute muss der Prüfer eine Verletzung
nachweisen und kann es nachweislich nicht. Nach B muss der Einbringende die
Herkunft belegen. Das ist die einzige Richtung, die mit Gits Datenmodell
verträglich ist.

---

## 4. Abhängigkeiten, Sequenzierung und Risiken

**4.1 Sequenzierungsrisiko (bitte beachten).** Commander Seven hat Architektin
`seven-b'ellana` einberufen, um die *unmittelbare technische Disposition* zu
`0044-01` zu treffen — dokumentiertes Restrisiko versus Heuristik. Das ist eine
begrenzte Fachentscheidung in ihrer Zuständigkeit. **Sie kann E1 faktisch
vorwegnehmen:** Entscheidet sie „Restrisiko dokumentieren", ist Option A von E1
implementiert, bevor das Management über C befinden konnte. Empfehlung: Der
`0044-01`-Disposition mitteilen, dass eine Managemententscheidung zur Reichweite
aussteht, und ihre Wahl als *vorläufig, unter Vorbehalt von E1* kennzeichnen.

**4.2 `0044-02` ist betroffen.** Die Risikointegrationsprozedur (`DEC-0044-003`)
wird gerade erst definiert. Fällt E1 auf C, sollte `0044-02` die
Aufzeichnungspflicht von Anfang an mitführen, statt sie später nachzurüsten.

**4.3 Altbestand.** `main` steht auf `139b865cb`. Sämtliche Historie davor trägt
keine Herkunftsnachweise. Eine Nachrüstung ist weder möglich noch sinnvoll; die
Regel kann nur ab Beschluss gelten. Das Management sollte diesen Stichtag
ausdrücklich festhalten.

**4.4 Restrisiko auch nach C+B+B.** Ehrlich benannt: Ein Agent, der den Trailer
weglässt **und** den Hook umgeht **und** dessen Arbeit am Checkpoint nicht
auffällt, bleibt unentdeckt. Vollständige mechanische Sicherheit ist mit einem
lokalen Git-Repository und kooperativen Agenten nicht erreichbar. Ziel ist,
dass eine Verletzung **auffällt**, nicht dass sie unmöglich wird.

**4.5 Aufwand.** Grobe Einschätzung, zur Priorisierung, nicht als Zusage:
E3/B ist der kleinste Eingriff (eine Regel, eine Prüfung). E1/C plus E2/C ist
eine Task-Größe in der Größenordnung des bisherigen `0044-01`, zuzüglich der
Anpassung des bestehenden Werkzeugs.

---

## 5. Rollenabgrenzung — was diese Vorlage bewusst nicht tut

Gemäß `DEC-ROLE-001` trifft der Projektleiter keine Managemententscheidungen.
Diese Vorlage entscheidet daher **nicht**:

- welche Option gewählt wird — auch dort nicht, wo ich eine klare Empfehlung gebe;
- ob `DEC-0044-002` geändert wird (das ist eine Managemententscheidung mit
  Reichweite über Feature `0044` hinaus);
- die technische Disposition zu `0044-01` (Zuständigkeit der Architektin,
  siehe 4.1);
- ob und wann der Root-Index tatsächlich zurückgesetzt wird (Eingriff in
  fremden Zustand, siehe E3).

Sie ändert keine Autoritätsdokumente, keine Marker, keine Acceptance-Records
und keinen fremden Claim.

## 6. Was ich vom Management zur Fertigstellung benötige

1. Beschluss zu E1–E4 (Zustimmung, Abweichung oder Ablehnung je Punkt).
2. Bei E1/C: Bestätigung des **Stichtags** (Regel gilt ab Beschluss, kein
   Rückwirkungsanspruch — siehe 4.3).
3. Bei E3/B: Freigabe für das Zurücksetzen des Root-Index nach Bestätigung des
   Sicherungstags, und die Angabe, wer diesen Eingriff ausführen soll.
4. Weisung zu 4.1: Soll die `0044-01`-Disposition auf diese Entscheidung warten
   oder unter Vorbehalt vorangehen?

Nach Beschluss überführe ich das Ergebnis in reguläre Entscheidungsdatensätze
(`DEC-…`) und leite die nötigen Tasks ab bzw. lasse `DEC-0044-002` durch das
Management anpassen.

---

## 7. Provenance

**Auslösender User-Prompt (wörtlich, in Reihenfolge):**

> jetzt.

Dieser Prompt beantwortete mein unmittelbar vorangegangenes Angebot, die vom
Management über Commander Seven übermittelte Aufgabe („die Branching-/
Merging-Strategie soll überarbeitet werden, ich soll eine Entscheidungsvorlage
erstellen") jetzt zu beginnen.

**Mittelbarer Auftrag:** Die inhaltliche Anweisung erreichte mich nicht als
User-Prompt, sondern als Weitergabe durch Commander Seven über die agent-inbox
(Nachricht `1787300831729-0af51b3a`, Thread `0038`, 2026-08-21T08:27:11Z,
Betreff „Management assessment: the configuration-management (branching/merging)
strategy needs revision — please prepare a decision"). Der Wortlaut der
ursprünglichen mündlichen Management-Anweisung liegt mir **nicht** vor; er wird
hier bewusst nicht rekonstruiert. Maßgeblich ist die zitierte Nachricht.

**Eigene Messungen dieses Dokuments** (2026-08-21, Sitzung `kathryn`):

- `git diff --cached --stat HEAD` im Root-Checkout → 138 Dateien,
  2687 Einfügungen, 28683 Löschungen (Abschnitt 1.3).
- `git worktree list | wc -l` → 78 (Abschnitte 2.3, E3).
- `git tag -l 'preserved/*'` → beide Sicherungstags vorhanden (E3).
- Existenz und Betreff der drei Verdikt-Commits `fd2cf9237`, `c80ad6258`,
  `b62df43a8` gegen das Repository geprüft.
- `git --version` → 2.50.1; `git rev-parse --git-common-dir` → `.git`
  (Abschnitt 2.2).
- Zwei isolierte Scratch-Repository-Tests zum `reference-transaction`-Hook:
  Auslösung bei `merge --ff-only` und `update-ref`; Herkunftserkennung zur
  Transaktionszeit (Abschnitt 2.2). Die Testrepositories waren temporär und
  sind nicht Teil dieses Repositories.

**Fremde Befunde**, übernommen mit Quellenangabe, nicht selbst reproduziert:
die drei `[u]`-Verdikte unter `0044-01` (Autor `seven-tom`, Commits
`fd2cf9237`, `c80ad6258`, `b62df43a8`), Sevens Bericht über fünf
Fast-Forward-Integrationen und über den Sicherungstag
`preserved/root-index-20260821`.
