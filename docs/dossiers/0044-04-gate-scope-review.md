# Scope-Prüfung `0044-04` — Gates A1 und A2 (`DEC-0044-016`)

- **Prüfer:** `Kathryn-Tom-20260822T004500Z`, Architekt (Persona Tom Paris)
- **Prüfer-Identität:** `agent:kathryn-tom-20260822t004500z:0044-04-gate-scope-review:20260822T004500Z`
- **Capability class:** `privileged` (direkte Ausführung; kein Runner-Protokoll)
- **Instanziiert durch:** Projektleiter `kathryn`, in Ausführung der Management­wahl zu Frage 4 der Erhebung zu `DEC-0044-016`
- **Rolle in diesem Vorgang:** ausschließlich Architekt. Kein Implementierer, kein Integrator, kein Abnehmer.
- **Gegenstand:** die in `DEC-0044-016` beschlossene Reichweite und Autorität der Gates A1 und A2 für die noch zu schreibende Feature-Breakdown-Prozessanweisung (`0044-04`)
- **Rechtsgrundlage der Prüfung:** `AGENTS.md`, Abschnitt *Cross-item gate-scope review exception*, Bedingung (2); `docs/pipeline/process-roles.md` §5, Bedingung 2
- **Datum:** 2026-08-22

## 0. Was diese Prüfung ist — und was nicht

Sie prüft die **vorgeschlagene Reichweite und Autorität vor der Mutation**. Sie ist
**keine** Task-Abnahme, **kein** Integrationsreview, **kein** Integrationsverdikt und
erzeugt **kein** `Acceptance: ✓`. Sie erlaubt niemandem, einen Checkpoint zu
überschreiten, und sie hebt den `Integration review: mandatory` auf `0044-04` nicht auf.

Ich habe in dieser Prüfung **keinen** Validierungslauf durchgeführt, und ich würde aus
einem grünen Lauf auch nichts ableiten: ein grünes Ergebnis beweist nicht, dass eine
Reichweite richtig, vollständig oder autorisiert ist. Diese Feststellung steht so in
`AGENTS.md` und in `process-roles.md` §5, und sie gilt hier wörtlich.

Ich habe die Anweisung **nicht** mitgeschrieben und werde sie nicht schreiben. Das ist
der Zweck meiner Beauftragung.

### 0.1 Baseline (gepinnt)

| Artefakt | Zustand |
|---|---|
| `main` bei Prüfbeginn | `1edc98ec1` |
| `main` bei Prüfabschluss | `146a975d6` |
| Delta dazwischen | `5e18f678e` + Merge `146a975d6` — berührt von den geprüften Pfaden **nur** `AGENTS.md`, und dort ausschließlich einen angehängten Eintrag im Vorschlagslog (QA-Sweep). Ohne Wirkung auf diese Prüfung. |
| `DEC-0044-016` | `1edc98ec1`, `docs/dossiers/dec-branching-merging-strategie.md`, Abschnitt `DEC-0044-016` |
| Herkunftsquittung | `docs/dossiers/dec-0044-016-provenance.txt`, sha256 `803c11dededc4c4239251d65a231cba19113fdaae207be52d6079567c6e2d761` — **deckt sich mit dem im Commit `1edc98ec1` genannten Digest**; die Quittung ist seit dem Commit unverändert |
| `docs/pipeline/decision-record.md` | sha256 `dea2c93ad046d67a129d6b30b7715609a49afde26f47e5039cc2c2159cdb66c0` |
| `docs/pipeline/process-roles.md` | sha256 `02007d8f22927ba2740235bd8d0a4772aaa476db2fe4b1591e8505f8389f4096` |
| `docs/pipeline/branch-workflow.md` | sha256 `2da48e805adf91bd6da34eb9d42f85ede1fbb8c6e81daf37baf985b13279e63a` |
| `TODO.md` | sha256 `3bf4837452ab73c3d1136b2683e4afabc649e76169c67b5f36c41deaa4befaff` |
| `AGENTS.md` | sha256 `c8304cd61f148fc314ac490b478d114e8b37c51c2587ae954538e9f1a5ff825f` |
| Claim des Implementierers | `TODO-Data-Riker-0044-04-20260821T221000Z.md` auf Branch `0044-04`, Tip `b098882fa` |

### 0.2 Unabhängigkeit und Briefing

`DEC-0044-013` (2026-08-21) verlangt für einen **selbst gestarteten Prüfer** drei Dinge:
getrennte Persona, von der erzeugenden Session verschieden, und **aufgezeichnetes
Briefing samt übergebenem Kontext**. Formal gilt `DEC-0044-013` der Abnahme, nicht der
Scope-Prüfung. Ich wende es hier **sinngemäß** an, weil die Fehlerform identisch ist —
ohne den Briefingtext kann später niemand feststellen, ob der Prüfer auf die Antwort
gezeigt bekam — und weil die Aufzeichnung nichts kostet.

- **Dispatchende Identität:** `kathryn` (Projektleiter, zed/claude-opus-5)
- **Prüfer-Persona:** Architekt Tom Paris — verschieden von der Persona der
  dispatchenden Session (Projektleiter Kathryn Janeway)
- **Verhältnis zum Implementierer:** `Data-Riker-20260821T221000Z` hält den `0044-04`-Claim
  und wäre der Implementierer. Ich bin eine frische Session ohne jede vorherige Beteiligung
  an `0044-04`. Die von `process-roles.md` §5 geforderte Verschiedenheit vom Implementierer
  ist erfüllt.
- **Offen gelegte Einschränkung:** Gebrieft hat mich dieselbe Session, die den zu prüfenden
  Datensatz aufgezeichnet hat. Das Briefing fordert allerdings ausdrücklich die Prüfung
  genau dieser Aufzeichnung („auch wenn ich sie selbst verursacht haben könnte") und stellt
  alle fünf Verdikte gleichrangig frei. Das mindert die Rahmungswirkung, hebt sie nicht auf.
  Wer diese Prüfung liest, soll den Umstand kennen.
- **Übergebener Kontext:** ausschließlich der unten wörtlich wiedergegebene Briefingtext.
  Keine Vorabbewertung, kein Entwurf, keine Ergebnisvorgabe. Alle Belege habe ich selbst aus
  dem Repository gelesen; jede Belegstelle ist unten benannt.
- **Nicht übergeben:** der Chatverlauf der Fragebogen-Erhebung; die Inbox-Nachricht von
  `Data` an `kathryn` vom 2026-08-21T23:03:08Z (nicht an mich adressiert).

#### Briefing, wörtlich

```text
Du bist **Kathryn-Tom-20260822T004500Z**, Architekt im Projekt autodocs (/Users/tobias.anton/devel/autodocs).

Melde dich zuerst an: `announce(agent: "Kathryn-Tom-20260822T004500Z", role: "privilegierter Architekt, unabhaengige Scope-Pruefung fuer 0044-04; kein Implementierer, kein Integrator", runtime: "zed/claude-opus-5")`, dann `inbox(agent: "Kathryn-Tom-20260822T004500Z")`.

## Einordnung (verbindlich, nach AGENTS.md "Dispatching a subagent")

- **capability_class: `privileged`.** Du fuehrst Git und Kommandos **direkt** aus. NIEMALS das Runner-Protokoll, niemals auf `run.sh` warten.
- **Dispatcher:** Projektleiter `kathryn` (kleingeschrieben).
- **Vorgang:** `0044-04`. **Arbeite lesend**; wenn du schreiben musst, dann nur in einem eigenen Worktree `.worktrees/review-0044-04-tom-20260822T004500Z` von `main`.
- **Schreibscope:** ausschliesslich dein Reviewbericht unter `docs/dossiers/0044-04-gate-scope-review.md` in deinem Worktree, plus eine eigene Claim-/Notizdatei. Sonst nichts.

## Was du NICHT tust

- Du schreibst **nicht** die Policy/Prozessanweisung von `0044-04`. Deine Unabhaengigkeit von der Implementierung ist der ganze Zweck deiner Existenz hier.
- Keine Abnahme (`Acceptance: ✓`), kein Integrationsknoten, kein Merge nach `main`, kein `DONE.md`.
- Keine Mutation des Root-Checkouts `/Users/tobias.anton/devel/autodocs` (`DEC-0044-010`). Kein `git update-ref` auf `refs/heads/main`. Kein Push.
- Fremde Claims nicht anfassen.

## Dein Auftrag: die Scope-Pruefung nach AGENTS.md

`AGENTS.md`, Abschnitt **"Cross-item gate-scope review exception"**, verlangt vor der ersten Mutation einer qualifizierenden Gate-Reichweite **zwei** Dinge: (1) einen konformen Entscheidungsdatensatz und (2) eine Scope-Pruefung durch einen Architekten, dessen Identitaet von der des Implementierers verschieden ist.

Bedingung (1) ist erfuellt: **`DEC-0044-016`**, Commit `1edc98ec1` auf `main`, in `docs/dossiers/dec-branching-merging-strategie.md`. Du bist Bedingung (2).

**Lies zuerst:** `DEC-0044-016` und die zugehoerige Herkunftsquittung `docs/dossiers/dec-0044-016-provenance.txt`; den Task `0044-04` in `TODO.md`; `AGENTS.md` (Abschnitt Cross-item gate-scope review exception); `docs/pipeline/decision-record.md` (kanonisches `cross-item-blast-radius`-Praedikat); `docs/pipeline/process-roles.md`.

**Beantworte, jeweils mit Begruendung und Belegstelle:**

1. **Ist das Praedikat richtig angewandt?** Sind A1 (Integrierbarkeitspruefung zur Branch-Zeit) und A2 (Aufzeichnung von Reihenfolgeabweichungen) tatsaechlich qualifizierende cross-item-Gates nach dem kanonischen Praedikat — oder hat `Data-Riker-20260821T221000Z` zu weit gegriffen? Beide Antworten sind zulaessig; wenn er zu weit gegriffen hat, sag es.

2. **Ist die beschlossene Reichweite tragfaehig?**
   - A1 verlangt als Mindestevidenz **einen Satz** im Vorgangsdatensatz statt eines Werkzeuglaufs. Reicht das, um den Schaden abzufangen, den A1 abfangen soll? Wo genau ist die Grenze dieser Kontrolle — welche Faelle rutschen durch?
   - A2 loest nur bei Fremdbetroffenheit aus, gebunden an dasselbe cross-item-Praedikat. Ist dieser Ausloeser in der Praxis **entscheidbar**, oder verlagert er nur die Unschaerfe? Wer stellt die Betroffenheit fest, und wann?

3. **Ist der Worked Example tragfaehig?** Feature `0043` wurde gewaehlt. Prueft das die Anweisung wirklich, oder ist `0043` dafuer zu speziell/zu weit fortgeschritten? `Data` hat einen Vorbehalt zu Owner/Provenance genannt — geh dem nach.

4. **Fehlt etwas?** Nennt der Datensatz alle betroffenen Arbeitseinheiten und Gates? `DEC-0044-016` nennt `0044-05`, `0044-06`, `0044-08` als fortwirkend. Stimmt das, und ist es vollstaendig?

5. **Widerspruchsfreiheit:** Kollidiert die beschlossene Reichweite mit `DEC-0044-006`, `DEC-0044-008`, `DEC-0044-010`, `DEC-0044-015` oder mit `branch-workflow.md`? Insbesondere: A1 spricht ueber Integrierbarkeit zur Branch-Zeit, `DEC-0044-015` ueber den letzten Integrationsschritt — beissen die sich irgendwo?

**Wichtiger Hinweis zur Herkunft der Entscheidung:** Sie wurde ueber einen Fragebogen in bewusst einfacher Sprache erhoben, ohne die Bezeichner A1/A2/`0044-04`/`0043` und ohne den Begriff cross-item-Gate — auf ausdrueckliche Bitte des Managements. Die Rueckuebersetzung in die Gate-Semantik hat die Projektleitung vorgenommen. **Pruefe diese Uebersetzung ausdruecklich mit**: Die Quittung enthaelt alle vier Fragen mit saemtlichen angebotenen Optionen im Wortlaut. Deckt die aufgezeichnete Entscheidung wirklich, was gefragt und gewaehlt wurde — oder hat die Projektleitung dabei etwas hineingelesen? Das ist eine echte Fehlerquelle und ich will sie geprueft haben, auch wenn ich sie selbst verursacht haetenkoennte.

## Verdikt

Schliesse mit genau einem von: **`scope-ok`**, **`scope-ok-mit-auflagen`** (Auflagen einzeln und umsetzbar auflisten), **`scope-zu-weit`**, **`scope-zu-eng`**, **`unschluessig`** (und was fehlt, um schluessig zu werden).

Deine Pruefung ist **keine** Task-Abnahme, kein Integrationsreview und kein `Acceptance: ✓`. Sie prueft die vorgeschlagene Reichweite und Autoritaet **vor** der Mutation. Ein gruener Validierungslauf beweist nicht, dass eine Reichweite richtig, vollstaendig oder autorisiert ist — schreib nichts, was das behaupten wuerde.

## Abschluss

Committe den Bericht in deinem Worktree auf Branch `review-0044-04-tom-20260822T004500Z`. Melde dann per `agent-inbox` **eine** Nachricht an `kathryn` (kleingeschrieben) mit: Verdikt, den drei bis fuenf wichtigsten Befunden, etwaigen Auflagen, sowie Branch und Commit-Hash. Sag klar, wenn du etwas nicht pruefen konntest und warum.
```

### 0.3 Begriffsklärung vorweg — „Fall A1/A2" gegen „Gate A1/A2"

`branch-workflow.md` (Zeilen 163–167) definiert A1–A4 als **Fehlerfälle bei der
Integration**, nicht als Gates:

- **A1** — Planungsfehler, vorbestehend: die Policy von `A` hätte die Integration schon
  zum Branch-Zeitpunkt nicht erlaubt.
- **A2** — Planungsfehler, Reihenfolgeabweichung: die Policy von `A` hat sich geändert,
  weil in anderer Reihenfolge implementiert wurde als geplant.

`DEC-0044-016` spricht dagegen von „Gate A1" und „Gate A2" und meint damit die
**Verhinderungspflichten**, die `branch-workflow.md` an `0044-04` adressiert
(Zeilen 173–179). Die Kurzform ist in `TODO.md` bei `0044-04` bereits etabliert
(„verified at branch time (A1)", „how order deviations are recorded (A2)") und deshalb
zulässig. Sie ist aber eine **Homonymie**: „A1" bezeichnet je nach Dokument den Schadensfall
oder das Gegenmittel. Ich verwende unten durchgängig **Gate A1** / **Gate A2** für die
Pflichten und **Fall A1** … **Fall A4** für die Tabelle. Die Anweisung sollte dasselbe tun.

---

## 1. Ist das Prädikat richtig angewandt?

**Ergebnis: Ja. `Data-Riker` hat nicht zu weit gegriffen — die Einstufung ist korrekt und
für Gate A1 sogar zurückhaltend formuliert.**

Der kanonische Test (`decision-record.md` §2, Zeile `cross-item-blast-radius`) lautet: Die
Entscheidung **kann** Start, Validierung, Abnahme, Integration, Veröffentlichung oder
Abschluss **mindestens einer anderen** Arbeitseinheit blockieren, **oder** deren Vertrag
ändern. Es genügt eine der beiden Hälften; die Modalität ist „kann", nicht „tut".

**Gate A1** ist eine Pflicht am **Start** jeder künftigen Arbeitseinheit. Eine Pflicht, die
am Start greift und deren Nichterfüllung den Start unzulässig macht, blockiert per
Konstruktion den Start anderer Einheiten. Das ist nicht die schwächere „kann"-Variante,
sondern der Vollfall. Zusätzlich ändert sie den **Vertrag** jeder künftigen Einheit: deren
Vorgangsdatensatz muss ein Feld führen, das er heute nicht führt.

**Gate A2** ändert die Evidenzpflicht abweichender Einheiten und damit ebenfalls deren
Vertrag. Auch das ist die Vertragshälfte des Prädikats, nicht die Blockadehälfte — und die
Vertragshälfte allein genügt.

Beide sind zudem `material-architecture-or-repository-behavior` („durable process rule"):
die Anweisung wird nach der Definition of Done von `0044-04` aus `AGENTS.md` und
`process-roles.md` verlinkt und ist damit repositoryweit verbindlich.

Der Vier-Fälle-Vergleich in `process-roles.md` §5 stützt das eindeutig: der Positivfall
(`0038-03`, ein hart verdrahteter Validator, der Validierung und Abschluss anderer Tasks
blockieren kann) liegt strukturell gleich; die drei Negativfälle (task-lokaler Validator,
Tippfehler in geteiltem Pfad, hypothetischer gewöhnlicher Bug) treffen ersichtlich nicht zu.
Der Schlüssel ist ausdrücklich die **Reichweite**, nicht die Checkpoint-Markierung.

Auch die Gegenprobe fällt eindeutig aus: `DEC-0044-006` deckt die neue Anweisung **nicht**
ab. Sein eigener Entscheidungstext (`docs/dossiers/0044-01-branch-workflow-prose-scope-review.md`,
Abschnitt `DEC-0044-006`) beschreibt sich selbst als reinen **Verankerungsakt** („The
decision content itself is not new — it transcribes the already-decided table") und hält in
`CON-02` fest: „No existing gate behavior changes — this is anchoring, not a new rule". Die
Gate-Semantik, das Evidenzminimum und die Anwendungsfläche der Anweisung sind dort
unentschieden. `Data-Riker`s Feststellung im Claim ist damit belegt, nicht bloß plausibel.

**Belegstellen:** `docs/pipeline/decision-record.md` §2; `docs/pipeline/process-roles.md`
§5 nebst Vier-Fälle-Tabelle; `docs/pipeline/branch-workflow.md` Z. 163–179;
`docs/dossiers/0044-01-branch-workflow-prose-scope-review.md`, `DEC-0044-006`, `CON-02`;
`TODO-Data-Riker-0044-04-20260821T221000Z.md`, Abschnitt *Cross-item gate-scope analysis*.

---

## 2. Ist die beschlossene Reichweite tragfähig?

### 2.1 Gate A1 — ein Satz statt Werkzeuglauf

**Ergebnis: Die Richtung ist tragfähig und passt zur bereits beschlossenen Haltung des
Repositorys. Die Kontrolle hat aber vier klar benennbare Lücken, von denen eine echt ist
und geschlossen werden muss.**

#### Warum die Richtung stimmt

Das Repository hat dieselbe Abwägung vor einem Tag schon einmal getroffen und aufgezeichnet.
`DEC-0044-008` stellt fest, dass Herkunft **aufgezeichnet** und nicht rekonstruiert wird,
weil jede rein nachträgliche Prüfung „entweder zu streng oder zu lax" ist. `DEC-0044-011`
kehrt dazu die Beweislast um und akzeptiert das Restrisiko ausdrücklich: „Wer den Nachweis
weglässt, den Hook umgeht und am Checkpoint nicht auffällt, bleibt unentdeckt. … Ziel ist,
dass ein Verstoß **auffällt**, nicht dass er unmöglich wird."

Gate A1 mit Satz-Minimum ist strukturell **derselbe Handel**: der Handelnde zeichnet auf,
der Checkpoint des Integrators bleibt das Tor, das Restrisiko ist die falsche
Selbstauskunft. Das ist keine neue Aufweichung, sondern die konsequente Fortschreibung
einer schon getragenen Linie. Wer A1 einen Werkzeuglauf abverlangte, müsste erklären, warum
für die Integrierbarkeitsprognose gelten soll, was für die Herkunft ausdrücklich verworfen
wurde.

Die Management-Begründung („Der teure Fall ist der, in dem jemand tagelang an etwas baut,
das am Ende nicht zusammenpasst") trifft den Nutzen präzise: der Wert liegt im **erzwungenen
Hinsehen zum richtigen Zeitpunkt**, nicht in der Beweiskraft des Artefakts.

#### Wo die Grenze verläuft — was durchrutscht

1. **Der Negativfall ist nicht entschieden.** `DEC-0044-016` legt fest, *was* aufgezeichnet
   wird („passt / passt nicht"), aber nirgends, *was geschieht, wenn „passt nicht"
   herauskommt*. Wird der Branch nicht angelegt? Wird der Plan korrigiert? Die Reihenfolge?
   Wird eskaliert? Ein Gate ohne definierten Negativzweig ist kein Gate, sondern eine Notiz —
   und ausgerechnet der Fall, den A1 abfangen soll, endet dann in einem Satz, den niemandem
   zu befolgen aufgetragen ist. **Das ist die einzige echte Lücke in dieser Prüfung**, und sie
   ist billig zu schließen (Auflage A-04).
2. **Rituelle Erfüllung.** Zwischen einem echten Abgleich und einem hingeschriebenen „passt"
   unterscheidet nichts. Das ist der bewusst getragene Preis der Satz-Lösung und deckungsgleich
   mit dem Restrisiko in `DEC-0044-011`. Tragbar — aber nur, wenn ausdrücklich dasteht, dass
   der Satz ein **Netz** ist und die A1/A2-Triage des Integrators am Checkpoint das **Tor**
   bleibt, und dass ein **fehlender** Satz ein Befund gegen den Vorgang ist und keine neutrale
   Leerstelle (Auflagen A-05, A-06). `DEC-0044-009` hat diese Formulierung bereits geprägt;
   sie muss hier nur wiederverwendet werden.
3. **Das falsche Ziel geprüft.** Wogegen wird verglichen — gegen `main` oder gegen den
   unmittelbaren Elternbranch? Dazu unten §6.1 und Auflage A-03. Ohne Festlegung ist der Satz
   nicht auswertbar, weil sein Bezugspunkt offenbleibt.
4. **Nachträgliche Policy-Änderung.** Naheliegender Einwand, aber **kein** Mangel: Wenn sich
   die Zielpolicy nach dem Branchen ändert, ist das nach der Tabelle in §2.1 des Intake-Dossiers
   **Fall A3** („Policy hat sich geändert, weil nachträglich ein Feature hinzukam oder eine
   Abweicherlaubnis erteilt wurde") — ausdrücklich **kein** Planungsfehler, und über die
   Ersetzungsregel (`RQ-IP-03`, `DEC-0044-005`) beim Integrator aufgehoben. Gate A1 ist
   korrekterweise ein Zeitpunkt-Check; die Veralterung ist woanders geregelt. Ich führe das
   auf, weil es der erste Einwand ist, den jeder Leser haben wird, und er sich sauber auflöst.

#### Der Reibungspunkt mit `RQ-IP-02`

`RQ-IP-02` verlangt wörtlich: „Der Feature-Breakdown-Prozess verhindert die
Planungsfehlerfälle A1/A2 (Tabelle §2.1) **mechanisch prüfbar**". Ein freier Prosasatz ist auf
keiner Ebene mechanisch prüfbar. Das ist auflösbar, aber nur, wenn man es ausspricht: die
Anweisung muss den „einen Satz" als **strukturiertes Feld** definieren (fester Feldname,
Verdikt aus geschlossenem Vokabular, geprüftes Ziel, Grundlage). Dann sind **Vorhandensein
und Wohlgeformtheit** maschinell prüfbar — die **Richtigkeit** der Aussage bleibt es nicht,
und genau das muss als getragenes Restrisiko dastehen (Auflage A-06). Ohne Struktur bleibt
`RQ-IP-02` auf dieser Achse unerfüllt und der Widerspruch fällt spätestens bei `0044-08` an.

Nebenbefund zur Rückverfolgbarkeit: `0044-04` führt unter *Requirements covered* nur
`RQ-AP-01` … `RQ-AP-03`. `RQ-IP-02` ist nominell `0044-01` zugeordnet, das seinerseits nur
noch **verweist** („the breakdown instruction of `0044-04` is referenced as the prevention
point"). Die materielle Pflicht aus `RQ-IP-02` hat damit derzeit **keinen Eigentümer**
(Auflage A-09).

### 2.2 Gate A2 — Auslöser nur bei Fremdbetroffenheit

**Ergebnis: Der Auslöser ist in der Praxis entscheidbar, aber nur mit drei Ergänzungen. Ohne
sie verlagert er die Unschärfe tatsächlich nur — und zwar zu der Partei mit dem geringsten
Interesse am Aufschreiben.**

Die Anbindung an das bereits definierte Prädikat statt eines zweiten Tests ist **richtig**
und genau das, was `Data-Riker` in seinem Claim gefordert hat. Ein zweiter, eigener
Betroffenheitstest wäre eine neue Fehlerquelle. Insofern: gute Entscheidung.

Drei Probleme:

1. **Der Datensatztext ist enger als das Prädikat, mit dem er sich gleichsetzt.** Der
   kanonische Test sagt „**kann** blockieren … **oder** deren Vertrag ändern" (Modalverb,
   potenziell). `DEC-0044-016` sagt „wenn sie die Arbeit einer anderen Einheit **blockiert**
   oder deren Vertrag **verändert**" (Indikativ, tatsächlich) — und behauptet im selben
   Absatz, es handele sich um „denselben cross-item-Prädikatstest". Das ist ein innerer
   Widerspruch auf genau der Achse, die zählt. Im Zweifelsfall setzt sich in der Praxis die
   engere Formulierung durch, weil sie dem Aufzeichnungspflichtigen entgegenkommt. Der
   kanonische Wortlaut ist zu übernehmen (Auflage A-07).
2. **Zuständigkeit und Zeitpunkt fehlen.** Wer stellt Fremdbetroffenheit fest, und wann?
   Naheliegend ist der Eigentümer der abweichenden Einheit im Moment der Abweichung — aber
   das ist genau die Partei, die die Wirkung **am schlechtesten** überblickt: ob eine andere
   Einheit blockiert wird, zeigt sich typischerweise erst an deren Start oder bei der
   Integration. Die Anweisung muss Zuständigkeit, Zeitpunkt und die Zweifelsregel benennen
   („im Zweifel aufzeichnen" — die Aufzeichnung ist billig, ihr Fehlen teuer) (Auflage A-08).
3. **Kein Nachforderungsrecht.** Ohne die ausdrückliche Befugnis des Integrators, am
   Checkpoint eine fehlende A2-Aufzeichnung nachzufordern, ist die Regel
   **selbstzertifizierend**: allein der potenziell Fehlbare entscheidet, ob er
   aufzeichnungspflichtig war. Auch das ist mit einem Satz zu heilen (Auflage A-08).

**Voraussetzung, die noch fehlt:** Eine „Abweichung von der geplanten Reihenfolge" ist nur
feststellbar, wenn eine **geplante Reihenfolge erfasst** ist. `RQ-IP-02` verlangt das
ausdrücklich („die vorgesehene Implementierungsreihenfolge ist erfasst"), und `TODO.md`
verlangt es bei `0044-04` ebenfalls („the derivation of its prerequisites (with the planned
implementation order where order matters)"). `DEC-0044-016` entscheidet dazu nichts. Gate A2
hängt damit derzeit an einer Pflicht, die niemand beschlossen hat (Auflage A-09).

---

## 3. Ist der Worked Example tragfähig?

**Ergebnis: Nur eingeschränkt. `Data`s Vorbehalt ist berechtigt — und die Lage ist schlechter
als der Vorbehalt vermuten lässt. `0043` ist nicht „zu speziell", sondern in weiten Teilen
bereits vergeben oder gesperrt. Für Gate A2 taugt es derzeit gar nicht.**

`Data-Riker` hatte im Claim festgehalten, `0043` sei „not yet an authorized example: it must
be rechecked on current `main` for active claims, Feature ownership, current branches, and
conflict-free write scope". Ich habe das nachgeprüft. Befund:

| Task | Marker auf `main` | Tatsächlicher Zustand | Für Gate A1 prospektiv erprobbar? |
|---|---|---|---|
| `0043-01` | `[x]` | terminal, Branch `d4741e906` | nein — abgeschlossen |
| `0043-02` | `[x]` | terminal, Branch `946e5e4ab`, **unintegriert** | nein — abgeschlossen |
| `0043-03` | `[ ]` | **kein Branch**, frei | **ja** |
| `0043-04` | `[ ]` | auf Branch `[u]`, Claim `TODO-Data-Aria-0043-04-20260821T093000Z.md`, Branch `b9bef3f42` — **gehalten, weil es selbst eine eigene Gate-Scope-Prüfung erwartet** | nein — gesperrt, Branch existiert bereits |
| `0043-05` | `[ ]` | auf Branch `[p]`, Claim `TODO-Data-Julia-0043-05-20260821T090700Z.md`, Branch `afcba7663` mit umfangreicher laufender Arbeit | nein — fremder aktiver Claim, Branch existiert bereits |
| `0043-06` | `[ ]` | kein Branch; hängt an `0043-02` und `0043-05` | ja, aber erst nach `0043-05` |
| `0043-07` | `[ ]` | kein Branch; integrierender Task, hängt an allem | ja, aber zuletzt |

Daraus folgen vier Feststellungen:

1. **Gate A1 ist ein Branch-Zeitpunkt-Gate.** Wo der Branch bereits existiert, lässt es sich
   nicht mehr prospektiv anwenden, sondern nur nachträglich unterstellen. Das ist keine
   Erprobung. Real erprobbar ist heute **`0043-03`** — und später `0043-06` und `0043-07`.
   Die Pilotfläche ist damit ein Task, nicht ein Feature (Auflage A-11).
2. **Zwei der offenen Tasks sind nicht verfügbar.** `0043-05` hat einen aktiven fremden
   Eigentümer und darf nicht angefasst werden. `0043-04` steht auf `[u]` und wartet
   ausgerechnet auf **dieselbe** Kontrolle — eine unabhängige Architekten-Scope-Prüfung nebst
   konformem Entscheidungsdatensatz — für ein anderes Gate (die `validate.py`-Frischeprüfung).
   Beide sind für den Pilot gesperrt.
3. **Gate A2 kann in `0043` derzeit überhaupt nicht erprobt werden.** Ich finde in `0043`
   keinen Fall einer Reihenfolgeabweichung mit Fremdbetroffenheit. `0043-05` hat keine
   Prerequisites, seine Bearbeitung vor `0043-03` verletzt daher keine geplante Reihenfolge.
   Wird der Pilot wie beschlossen gefahren, erlangt **die Hälfte der Anweisung, die das
   Management gerade eingeschränkt hat, ungeprüft allgemeine Geltung**. Das ist tragbar, aber
   nur ausgesprochen, nicht stillschweigend (Auflage A-12).
4. **Die dem Management vorgelegte Begründung war unvollständig.** Die gewählte Option lautete:
   „Läuft gerade, ist überschaubar und hat noch offene Teile — der Testlauf kostet also kaum
   Extra-Aufwand." Beim Beschluss unerwähnt: ein Task auf `[u]`, ein Task in fremder Hand, ein
   terminaler aber unintegrierter Vorgänger, und dass genau ein Task prospektiv erprobbar ist.
   Das ist **kein Übersetzungsfehler**, sondern ein Mangel der Entscheidungsgrundlage — und
   nach meinem Urteil der ernstere von beiden. Die Wahl bleibt gangbar, wenn sie auf
   `0043-03`/`0043-06`/`0043-07` eingeschränkt wird; das Management ist über die korrigierte
   Lage zu unterrichten, damit es revidieren kann, wenn es will (Auflage A-11).

Ich verenge die Wahl bewusst nur dort, wo die Verengung **determinierbar** ist: `0043-04` und
`0043-05` sind schon nach geltenden Regeln unerreichbar (fremder Claim, `[u]`-Halt). Sie
auszunehmen ist keine neue Entscheidung, sondern die Feststellung einer bestehenden.

**Nebenbefund, `0043-02` betreffend:** `0043-04`s Claim hält fest, dass `0043-04` nur
`0043-01` als Prerequisite deklariert, obwohl der `0043-02`-Ledger-Vertrag `0043-03` und
`0043-04` ausdrücklich als Konsumenten nennt. Das ist ein Prerequisite-Defekt in `0043` — und
zugleich ein hübscher Beleg dafür, dass die Anweisung gebraucht wird. Er gehört **nicht** in
diese Prüfung und ist unter `0043` zu behandeln; ich vermerke ihn nur, damit er nicht
verlorengeht.

---

## 4. Fehlt etwas? Betroffene Arbeitseinheiten und Gates

**Ergebnis: Die genannten Einheiten stimmen, die Liste ist aber unvollständig — und die
größte Auslassung ist ausgerechnet der Worked Example.**

Geprüft, was `DEC-0044-016` nennt:

- `0044-05` — trifft zu. `PREREQ: 0044-05:0044-04`; die Schemata müssen das A1-Feld
  aufnehmen.
- `0044-06` — trifft zu. `PREREQ: 0044-06:0044-04`. (Randbemerkung: die Definition of Done
  von `0044-06` beschreibt einen „normative section consumed by `0044-04`'s instruction",
  also die **Gegenrichtung** zur Prerequisite-Kante. Vorbestehend, nicht durch diese
  Entscheidung verursacht, gehört nach `0044-08`.)
- `0044-08` — trifft zu, integrierender Task des Features.

Was fehlt:

1. **`feature:0043` und seine Tasks.** Die Entscheidung wendet die Anweisung auf ein
   **anderes Feature** an. Das ist der Lehrbuchfall von cross-item-Reichweite: Tasks in `0043`
   bekommen eine Startpflicht, die sie heute nicht haben. `0043` steht in der Liste
   „Betroffene Arbeitseinheiten und Gates" **nicht**. `Data-Riker` hatte genau das gefordert
   („names … the candidate worked-example Feature and tasks, plus affected gates
   `task-start:<example-task>`"). Das ist die gravierendste Auslassung (Auflage A-02).
2. **`AGENTS.md` und `process-roles.md`.** Die Definition of Done von `0044-04` verlangt
   Verlinkung aus beiden. Beides sind Autoritätsdateien nach `DEC-0044-012`; die Reichweite ist
   damit **repositoryweit**, nicht auf `0044-05/06/08` begrenzt. Als `path:`- bzw.
   `repository:`-Einheit zu führen (Auflage A-02).
3. **`0044-07`** — transitiv über `0044-05` betroffen. Geringe Tragweite, der Vollständigkeit
   halber.
4. **`0044-12` / `0044-13`.** Wenn Gate A1 ein Pflichtfeld erzeugt, sind die Trailer-Konvention
   (`0044-12`) und der `reference-transaction`-Hook (`0044-13`) die naheliegenden
   Durchsetzungsorte. Keine zwingende Betroffenheit, aber eine, die vor dem Schreiben der
   Anweisung bedacht sein will, damit nicht dritte Mechanik entsteht.
5. **Gates fehlen ganz in der Syntax des Formats.** `decision-record@v1` §3.1 verlangt
   Gate-Referenzen der Form `task-start:<ID>`, `integration:<ID>`, `feature-closure:<ID>`.
   `DEC-0044-016` nennt stattdessen prosaisch „Gate A1" und „Gate A2". Die ehrliche Angabe ist
   `task-start:*` für jede künftige Einheit, dazu `task-start:0043-03` (und die weiteren
   Pilot-Tasks), `integration:0044` und `feature-closure:0044` (Auflage A-02).

### 4.1 Formkonformität — der Datensatz ist kein `decision-record@v1`

`AGENTS.md` verlangt für Bedingung (1) ausdrücklich **„a conforming `decision-record@v1`"**.
`DEC-0044-016` ist das nicht. Es fehlen: `Record format`, `Role`, `Triggers`, `Considered
alternatives` (mindestens zwei, genau eine `selected`), `Consequences` in Listenform mit
`CON-NN`, `Affected work units` und `Affected gates` in der vorgeschriebenen Syntax,
`Review participation` und `Waiver`.

Zur Einordnung, damit das nicht als Formalismus abgetan wird:

- Es ist **kein Einzelfall**: kein einziger Datensatz in
  `docs/dossiers/dec-branching-merging-strategie.md` (`DEC-0044-008` … `DEC-0044-016`) trägt
  das v1-Format. Das ist ein Altbestandsproblem des ganzen Dossiers, nicht ein Fehler dieser
  Aufzeichnung allein.
- Es ist trotzdem **hier** relevant, weil `AGENTS.md` die Konformität ausgerechnet für die
  Gate-Scope-Ausnahme zur Bedingung macht — und weil der Maßstab im Repository **bereits
  erfüllt vorliegt**: `DEC-0044-005`, `DEC-0044-006` und `DEC-0044-007` in
  `docs/dossiers/0044-01-branch-workflow-prose-scope-review.md` sind vollständig v1-konform,
  und zwar für **denselben** Ausnahmetatbestand am **selben** Gegenstand. Der Vorgänger hat
  die Latte gelegt.
- Und es ist **operativ bindend**, nicht bloß kosmetisch: `process-roles.md` §5 verlangt, dass
  der unabhängige Architekt die Reichweite „reviews and supports **in the record**" — in einem
  `Review participation`-Block (`PART-NN`) des Datensatzes. Den hat `DEC-0044-016` nicht. **Es
  gibt derzeit keinen konformen Ort, an dem diese Prüfung eingetragen werden kann.** Das ist
  der Grund, warum ich A-01 als blockierend führe: ohne Slot bleibt Bedingung (2) formal
  offen, egal wie gründlich die Prüfung war.

Ein `decision-record-legacy-map@v1` (§6) wäre der additive Weg, wenn der Datensatz nicht
umgeschrieben werden soll. Was gewählt wird, ist Sache des Aufzeichnenden; irgendetwas davon
muss geschehen.

---

## 5. Widerspruchsfreiheit

Geprüft gegen `DEC-0044-006`, `DEC-0044-008`, `DEC-0044-010`, `DEC-0044-015` und
`branch-workflow.md`.

### 5.1 `DEC-0044-015` gegen Gate A1 — kein Konflikt

Sie beißen sich **nicht**. Sie liegen auf verschiedenen Ebenen: Gate A1 ist eine **Prognose
zum Branch-Zeitpunkt** über die Zulässigkeit unter der Zielpolicy; `DEC-0044-015` regelt die
**Mechanik des letzten Refs-Vorrückens** (im Root-Checkout ausführen, `merge --ff-only`/
`--no-ff` statt `update-ref`). Kein gemeinsamer Gegenstand, kein Konflikt.

Eine **Wechselwirkung** gibt es aber, und sie ist wichtig: `DEC-0044-015` bestätigt, dass
`main` das Ziel ist, an dem sich Governance bewegt, und `DEC-0044-012` schreibt vor, dass
Governance **immer** auf `main` liegt und `main` insoweit stets aktuell ist. Die Policy, gegen
die Gate A1 prüft, wandert also auf `main` — nicht auf dem Elternbranch eines Vorgangs. Wird
Gate A1 nur gegen den unmittelbaren Elternbranch ausgewertet, ist es strukturell **blind für
genau die Grenze, an der sich die Policy tatsächlich bewegt**. Das ist kein Widerspruch,
sondern eine Auslegungsfrage, die die Anweisung beantworten muss (Auflage A-03) — und sie
deckt sich mit dem Übersetzungsbefund in §6.1.

### 5.2 `DEC-0044-006` gegen Gate A2 — Spannung, auflösbar

`branch-workflow.md` Z. 177–179 sagt heute, verankert durch `DEC-0044-006`, unbedingt:

> „a deviation from the planned order is itself captured there **as a recorded decision**
> rather than surfacing later as an integration failure"

`DEC-0044-016` fügt eine Bedingung hinzu: nur bei Fremdbetroffenheit. `DEC-0044-016` behauptet
zugleich, es ändere `DEC-0044-006` nicht und hebe keine bestehende Gate-Semantik auf. **Diese
Behauptung ist in dieser Pauschalität nicht haltbar** — der verankerte Satz liest sich
unbedingt, der Beschluss macht ihn bedingt.

Die Spannung ist auflösbar, und zwar sauber: `decision-record.md` §2 sagt ausdrücklich „No
record is required when **no** trigger applies". Wenn „recorded decision" in
`branch-workflow.md` einen `decision-record@v1` meint, dann war die Pflicht **immer schon**
triggergebunden, und `DEC-0044-016` **präzisiert** nur, statt zu verengen. Diese Lesart halte
ich für die richtige. Sie muss aber im Text stehen, statt sich aus drei Dokumenten ergeben zu
müssen (Auflage A-07). Formulierungsvorschlag zur Prüfung durch den Implementierer: die
A2-Pflicht als Anwendung von `decision-record@v1` §2 ausweisen, nicht als eigene Regel.

### 5.3 `DEC-0044-008` / `DEC-0044-011` — konsistent, sogar stützend

Kein Widerspruch. Im Gegenteil: das Satz-Minimum von Gate A1 folgt derselben Linie
(aufzeichnen statt rekonstruieren, Netz plus Tor, benanntes Restrisiko). Siehe §2.1. Die
Anweisung sollte diese Herleitung ausdrücklich zitieren — sie ist ihr bestes Argument.

### 5.4 `DEC-0044-010` / `DEC-0044-015` — kein Konflikt, aber ein Ausführungshinweis

Gate A1 verlangt eine Prüfung **beim Anlegen eines Branches**. Das Anlegen geschieht in
vorgangseigenen Worktrees, der Root bleibt schreibgeschützt. Kein Konflikt. Sollte die
Anweisung jemals ein Werkzeug vorsehen, das Refs bewegt oder im Root arbeitet, gälte
`DEC-0044-015` unverändert; die Anweisung darf dazu keine Ausnahme schaffen.

### 5.5 Buchhaltungsbefund — Markerdivergenz zwischen `main` und Vorgangs-Branches

`DEC-0044-016` hält fest: „`0044-04` bleibt `[p]`". Auf `main` steht `0044-04` jedoch auf
`[ ]` (Zeile 176); das `[p]` samt Claim-Verweis liegt ausschließlich auf Branch `0044-04`.
Dasselbe Muster bei `0043-04` (`[u]` nur auf Branch, `[ ]` auf `main`) und `0043-05` (`[p]`
nur auf Branch, `[ ]` auf `main`).

Konsequenz: drei Vorgänge, die auf `main` **frei aussehen**, sind in Wahrheit beansprucht oder
gesperrt. Nach der Startregel in `AGENTS.md` scannt jede neue Session `TODO.md` von oben und
greift den ersten offenen, unbeanspruchten Task — sie würde hier zugreifen. Das ist keine
theoretische Sorge: es ist derselbe Mechanismus, der laut `DEC-0044-012` schon einmal zur
Doppelvergabe einer `DEC`-Kennung geführt hat. Vor dem Pilot in Deckung zu bringen
(Auflage A-13).

---

## 6. Prüfung der Rückübersetzung (Fragebogen → Gate-Semantik)

Grundlage: `docs/dossiers/dec-0044-016-provenance.txt`, Digest unverändert seit dem Commit.
Die Quittung führt alle vier Fragen mit **sämtlichen** angebotenen Optionen und der jeweils
gewählten. Sie hält selbst fest, dass die Abbildung von der einfachen Sprache zurück in die
Gate-Semantik durch die aufzeichnende Session erfolgte, und fordert Leser ausdrücklich auf,
sie zu prüfen statt sie zu unterstellen. Das ist gute Praxis und macht diese Prüfung erst
möglich.

**Gesamturteil: Die Übersetzung ist im Kern redlich. Sie enthält vier Abweichungen — eine
Erweiterung, zwei Verengungen und eine nicht gestellte Gleichsetzung. Keine davon verkehrt
die Entscheidung; alle vier sind zu kennzeichnen, zwei davon inhaltlich zu korrigieren.**

### 6.1 Frage 1 → Gate A1: eine Erweiterung, eine Zieländerung

Gefragt: „ob seine Arbeit später überhaupt sauber zurück **ins Hauptprojekt** passt?"
Gewählt: „Beim Start einmal prüfen und **in einem Satz** festhalten: passt oder passt nicht."

Aufgezeichnet: „ob die Arbeit unter der Policy **des Integrationsziels** zurückführbar ist.
Mindestevidenz ist ein Satz im Vorgangsdatensatz: Ergebnis (passt / passt nicht) **und woran
es festgemacht wurde**."

- **Zieländerung (materiell):** „Hauptprojekt" → „Integrationsziel". Das Management wurde nach
  der Rückführbarkeit ins **Hauptprojekt** gefragt, also nach `main`. „Integrationsziel" ist
  für einen Task der Feature-Branch, für einen Subtask der Task-Branch. Je nach Lesart ist das
  eine Ausweitung (mehr Ziele) oder eine Verengung (nur der unmittelbare Elternbranch, `main`
  gar nicht) — in jedem Fall **nicht das Gefragte**, und es trifft nach §5.1 ausgerechnet die
  Grenze, an der sich Policy bewegt. Zu korrigieren (Auflage A-03).
- **Erweiterung (benigne):** „und woran es festgemacht wurde" stand in keiner Option. Ich halte
  den Zusatz sachlich für richtig — ohne Grundlage ist der Satz wertlos — aber er ist eine
  Zutat des Aufzeichnenden und muss als solche kenntlich sein (Auflage A-15).
- **Getroffen:** „beim Start" → „beim Anlegen eines Arbeits-Branches" ist eine zulässige
  Präzisierung; sie deckt sich mit der Definition von Fall A1 („zum Branch-Zeitpunkt").
- **Nicht gefragt, deshalb unentschieden:** Frage 1 adressiert ausschließlich den, „der
  anfängt zu arbeiten" — also den Implementierer. `RQ-IP-02` verlangt daneben, dass **die
  vorgesehene Reihenfolge erfasst** ist, was eine Pflicht des Breakdown-Verantwortlichen ist.
  Zu dieser Hälfte hat das Management keine Frage bekommen und folglich nichts entschieden.
  Der Datensatz behauptet das auch nicht — aber die Lücke fällt sonst niemandem auf
  (Auflage A-09).

### 6.2 Frage 2 → Gate A2: eine Verengung, eine ungefragte Gleichsetzung

Gefragt/gewählt: „Notiert wird nur, wenn die Abweichung jemand anderem **die Arbeit** blockiert
oder verändert."

Aufgezeichnet: „wenn sie die Arbeit einer anderen Einheit blockiert oder **deren Vertrag**
verändert. … Auslöser ist damit **derselbe cross-item-Prädikatstest**, den
`decision-record@v1` bereits definiert."

- **Verengung:** „jemand anderem die **Arbeit** verändert" → „deren **Vertrag** verändert".
  Eine Abweichung, die eine andere Einheit zur Nacharbeit zwingt, ihre Baseline entwertet oder
  sie warten lässt, **ohne** ihren Vertrag zu ändern, wäre nach der gewählten Option
  aufzeichnungspflichtig, nach dem Datensatz nicht. Zu korrigieren oder als bewusste
  Einschränkung auszuweisen (Auflage A-07).
- **Ungefragte Gleichsetzung:** Die Identifikation mit dem kanonischen Prädikat wurde nicht
  angeboten und konnte nicht gewählt werden — das Management hat den Begriff auf eigenen Wunsch
  nie gesehen. Sie ist eine Zuordnung des Aufzeichnenden. **Ich halte sie für richtig** (ein
  zweiter Betroffenheitstest wäre eine Fehlerquelle, und `Data-Riker` hat sie ausdrücklich
  gefordert), aber sie darf nicht als Wortlaut des Managements erscheinen — zumal der
  Datensatztext, wie in §2.2 gezeigt, das Prädikat gar nicht korrekt wiedergibt (Indikativ
  statt Modal). Kennzeichnen und den kanonischen Wortlaut übernehmen (Auflagen A-07, A-15).

### 6.3 Frage 3 → Worked Example: wörtlich getreu, Grundlage unvollständig

Die Aufzeichnung gibt die gewählte Option inhaltlich korrekt wieder. Der Mangel liegt nicht in
der Übersetzung, sondern in der **Tatsachengrundlage**, auf der die Option formuliert war
(„kostet kaum Extra-Aufwand") — siehe §3, Punkt 4.

Zusätzlich ein Punkt, der weder in Frage noch Datensatz aufgelöst ist: Die Option lautet, die
Anleitung werde erprobt, **„bevor sie für alle gilt"**, und der Datensatz übernimmt das
(„bevor sie allgemein gilt"). Die Definition of Done von `0044-04` verlangt jedoch die
Verlinkung aus `AGENTS.md` — womit die Anweisung **mit dem Commit** allgemein verbindlich
wird. Erprobung-vor-Geltung und die DoD sind so nicht gleichzeitig erfüllbar. Entweder trägt
die Anweisung eine ausdrückliche Geltungsklausel (Pilot zuerst, allgemeine Geltung nach
Auswertung), oder die DoD ist zu korrigieren (Auflage A-10). Das ist eine echte
Umsetzungsfalle, kein Formalie-Streit.

### 6.4 Frage 4 → Gegenlesen: Autoritätsbezeichnung verschoben

Gewählt: „Ein eigener Prüfer, den **ich** starte — **Ich** setze einen unabhängigen
Architekten darauf an, der nicht selbst an der Anleitung schreibt."

Aufgezeichnet: „ein von **der Projektleitung** instanziierter Architekt."

`AGENTS.md` und `process-roles.md` §5 verlangen einen **Management-instantiated** Architect.
Die Projektleitung hat unter `DEC-ROLE-001` keine Managementautorität — sie sagt das selbst
(Rundruf vom 2026-08-21T20:41Z: „Ich habe unter `DEC-ROLE-001` keine Managementautoritaet").
Der Datensatz schreibt die Instanziierung damit ausgerechnet dort der Projektleitung zu, wo
die Regel Management verlangt.

**Der Sache nach ist die Bedingung erfüllt:** Das Management hat die Option „Ein eigener
Prüfer, den ich starte" ausdrücklich gewählt; die Projektleitung hat diese Wahl nur
ausgeführt, und die Quittung belegt das. **Der Aufzeichnung nach ist sie es nicht:** ein
späterer Leser sieht „Projektleitung instanziiert" und muss die Bedingung als verfehlt
bewerten. Zu heilen durch einen Satz, der die Wahl des Managements zitiert und die
Projektleitung als **ausführend, nicht entscheidend** ausweist (Auflage A-14). Das ist die
kleinste der vier Abweichungen — und die einzige, die eine **Autoritätsachse** berührt,
deshalb führe ich sie als blockierend.

---

## 7. Auflagen

Jede Auflage ist einzeln umsetzbar. **B** = vor der ersten Policy-Mutation zu erfüllen;
**T** = im Text der Anweisung zu erfüllen, prüfbar am verpflichtenden Integrationsreview von
`0044-04`.

### Datensatz und Autorität

- **A-01 (B) — Formkonformität herstellen.** `DEC-0044-016` in ein `decision-record@v1`
  konformes Format bringen oder additiv einen konformen Datensatz bzw. eine
  `decision-record-legacy-map@v1` nachziehen. Erforderlich sind mindestens `Record format`,
  `Role`, `Triggers`, `Considered alternatives` (≥2, genau eine `selected`, jede mit Grund),
  `Consequences` (`CON-NN`), `Affected work units`, `Affected gates`, `Review participation`,
  `Waiver`. **Ohne `Review participation`-Block existiert kein Ort, an dem diese Prüfung nach
  `process-roles.md` §5 eingetragen werden kann** — die Bedingung (2) bliebe formal offen.
  Maßstab liegt vor: `DEC-0044-005/006/007`.
- **A-02 (B) — Betroffene Einheiten und Gates vervollständigen.** Aufnehmen: `feature:0043`
  und die benannten Pilot-Tasks; `path:AGENTS.md`; `path:docs/pipeline/process-roles.md`;
  `repository:autodocs`; `task:0044-07`. Gates in der Syntax von `decision-record@v1` §3.1:
  `task-start:0043-03` (und weitere Pilot-Tasks), `integration:0044`, `feature-closure:0044`,
  sowie die repositoryweite Startwirkung ausdrücklich benannt.
- **A-14 (B) — Autoritätskette des Prüfers richtigstellen.** Festhalten, dass **das
  Management** die Instanziierung des unabhängigen Prüfers gewählt hat (Frage 4, Option „Ein
  eigener Prüfer, den ich starte") und die Projektleitung sie lediglich ausgeführt hat, damit
  die von `AGENTS.md`/`process-roles.md` verlangte Eigenschaft „Management-instantiated" eine
  nachvollziehbare Grundlage hat.
- **A-15 (B) — Zutaten als Zutaten kennzeichnen.** Jede Stelle, an der der Datensatz über den
  Fragebogen hinausgeht, als Zuordnung des Aufzeichnenden ausweisen — namentlich „woran es
  festgemacht wurde" (§6.1) und die Gleichsetzung des A2-Auslösers mit dem kanonischen
  Prädikat (§6.2). Beide halte ich sachlich für richtig; sie dürfen nur nicht als Wortlaut des
  Managements erscheinen.

### Gate A1

- **A-03 (T) — Prüfziel festlegen.** Die Anweisung benennt, gegen wessen Policy Gate A1
  prüft. Gefragt war das Hauptprojekt (`main`); aufgezeichnet ist „Integrationsziel". Mindestens
  `main` festlegen; werden zusätzlich Zwischenziele geprüft, ist das als Erweiterung gegenüber
  der Managementwahl auszuweisen. Der A1-Satz nennt das geprüfte Ziel ausdrücklich.
- **A-04 (T) — Negativzweig entscheiden.** Festlegen, was bei „passt nicht" geschieht: Branch
  nicht anlegen, Plan korrigieren, Reihenfolge ändern, eskalieren — und wer entscheidet.
  `DEC-0044-016` regelt die Evidenz, nicht die Konsequenz. Ein Gate ohne Negativzweig ist
  keine Kontrolle.
- **A-05 (T) — Netz und Tor benennen.** Ausdrücklich aufnehmen: der A1-Satz ist ein **Netz**;
  die A1/A2-Triage des Integrators am Checkpoint bleibt das **Tor**; ein **fehlender** A1-Satz
  ist ein Befund gegen den Vorgang, keine neutrale Leerstelle. Formulierung aus
  `DEC-0044-009`/`DEC-0044-011` übernehmen.
- **A-06 (T) — Satz strukturieren und `RQ-IP-02` ehrlich verorten.** Den „einen Satz" als
  strukturiertes Feld definieren (fester Feldname, Verdikt aus geschlossenem Vokabular,
  geprüftes Ziel, Grundlage). Dazu klarstellen: `RQ-IP-02`s „mechanisch prüfbar" wird auf der
  Ebene **Vorhandensein und Wohlgeformtheit der Pflichtangabe** eingelöst, **nicht** auf der
  Ebene einer berechneten Integrierbarkeit; das Restrisiko der falschen Selbstauskunft ist als
  getragen zu benennen.
- **A-09 (T) — Architektenseite von `RQ-IP-02` regeln.** Die Pflicht des
  Breakdown-Verantwortlichen, die **vorgesehene Implementierungsreihenfolge zu erfassen**, ist
  in der Anweisung zu regeln. Ohne erfasste Sollreihenfolge ist eine „Abweichung" nicht
  feststellbar und Gate A2 hat keinen Bezugspunkt. Zusätzlich: `RQ-IP-02` in *Requirements
  covered* von `0044-04` nachtragen, damit die Anforderung einen Eigentümer hat.

### Gate A2

- **A-07 (T) — Kanonischen Wortlaut übernehmen.** „**kann** … blockieren … **oder deren
  Vertrag ändern" statt des Indikativs; die Verengung „Arbeit" → „Vertrag" gegenüber der
  gewählten Option entweder zurücknehmen oder als bewusste Einschränkung ausweisen. Die
  A2-Pflicht als **Anwendung** von `decision-record@v1` §2 darstellen, nicht als eigene Regel
  — das löst zugleich die Spannung zu `DEC-0044-006` (§5.2).
- **A-08 (T) — Zuständigkeit, Zeitpunkt, Zweifelsregel, Nachforderung.** Benennen: wer die
  Fremdbetroffenheit feststellt (Eigentümer der abweichenden Einheit) und wann (im Moment der
  Abweichung); die Zweifelsregel („im Zweifel aufzeichnen"); und das Recht des Integrators,
  am Checkpoint eine fehlende A2-Aufzeichnung nachzufordern. Ohne Nachforderungsrecht ist die
  Regel selbstzertifizierend.

### Pilot / Worked Example

- **A-10 (T) — Geltungsklausel oder DoD-Korrektur.** Das Management hat „erproben, **bevor**
  sie für alle gilt" gewählt; die DoD von `0044-04` verlangt Verlinkung aus `AGENTS.md`, was
  sie mit dem Commit allgemein verbindlich macht. Entweder trägt die Anweisung eine
  ausdrückliche Geltungsklausel (Pilot verbindlich für die benannten `0043`-Tasks, allgemeine
  Geltung erst nach Auswertung, spätestens bei `0044-08`), oder die DoD ist entsprechend zu
  korrigieren.
- **A-11 (B) — Pilotfläche einschränken und Grundlage richtigstellen.** Den Pilot auf
  `0043-03`, `0043-06`, `0043-07` beschränken — die einzigen Tasks ohne Branch, an denen Gate
  A1 prospektiv erprobbar ist. `0043-04` (`[u]`, eigene Gate-Scope-Prüfung ausstehend) und
  `0043-05` (aktiver fremder Claim) sind ausgenommen; `0043-01`/`0043-02` sind terminal. Dem
  Management ist mitzuteilen, dass die Option „kostet kaum Extra-Aufwand" auf einer
  unvollständigen Lagebeschreibung beruhte, damit es die Wahl bei Bedarf revidieren kann.
- **A-12 (T) — Ungeprüftes Gate A2 ausdrücklich tragen.** In `0043` existiert derzeit kein
  Fall einer Reihenfolgeabweichung mit Fremdbetroffenheit; der Pilot kann Gate A2 daher nicht
  erproben. Entweder wird ein zweiter Erprobungsfall benannt, oder es ist festzuhalten, dass
  Gate A2 ungeprüft allgemeine Geltung erlangt — als bewusst getragenes Restrisiko, nicht
  stillschweigend.

### Buchhaltung

- **A-13 (B) — Markerdivergenz beseitigen.** `0044-04` (`[p]`), `0043-04` (`[u]`) und
  `0043-05` (`[p]`) tragen ihren wahren Marker nur auf ihren Vorgangs-Branches; auf `main`
  stehen alle drei auf `[ ]` und sehen frei aus. Vor Pilotbeginn in Deckung bringen, sonst
  greift eine scannende Session zu. Der Satz „`0044-04` bleibt `[p]`" in `DEC-0044-016`
  trifft auf den autoritativen Backlog derzeit nicht zu.

---

## 8. Verdikt

## `scope-ok-mit-auflagen`

Die Einstufung von Gate A1 und Gate A2 als qualifizierende cross-item-Gates ist **richtig**;
`Data-Riker` hat nicht zu weit gegriffen. Die beschlossene Reichweite ist **im Kern
tragfähig** und fügt sich in die vom Repository bereits getroffene Linie „aufzeichnen statt
rekonstruieren, Netz plus Tor, Restrisiko benannt" (`DEC-0044-008`/`-009`/`-011`) ein. Ich
sehe keinen Grund, das Satz-Minimum von Gate A1 zu verwerfen oder einen Werkzeuglauf zu
fordern — dieselbe Abwägung wurde für die Herkunftsaufzeichnung schon bewusst so getroffen.

Die Reichweite ist aber an mehreren Stellen **unvollständig festgelegt**, nicht falsch: Der
Negativzweig von Gate A1 ist unentschieden, das Prüfziel offen, die Liste betroffener
Einheiten lässt ausgerechnet den Worked Example aus, der A2-Auslöser widerspricht in seinem
Wortlaut dem Prädikat, mit dem er sich gleichsetzt, und der Datensatz ist nicht
formkonform — mit der praktischen Folge, dass diese Prüfung derzeit nirgends eingetragen
werden kann. Der Worked Example `0043` ist tragfähig, aber nur für einen Bruchteil seiner
Tasks und für Gate A2 gar nicht.

Die Rückübersetzung aus dem Fragebogen ist **im Kern redlich**. Sie enthält vier
Abweichungen: eine benigne Erweiterung, zwei Verengungen und eine nicht gestellte
Gleichsetzung. Keine verkehrt die Entscheidung. Die schwerwiegendere Schwäche liegt nicht in
der Übersetzung, sondern in der **Tatsachengrundlage zu Frage 3**: das Management wurde nicht
darüber unterrichtet, dass zwei der offenen `0043`-Tasks gesperrt bzw. fremdvergeben sind.

Nichts davon erfordert eine neue Managemententscheidung; alle Auflagen sind aus Feature-Ziel,
aufgezeichneten Entscheidungen und Repository-Evidenz determinierbar. Einzige Ausnahme ist die
**Mitteilungspflicht** aus A-11 — das Management soll die korrigierte Lage kennen, auch wenn
die Wahl eingeschränkt gangbar bleibt.

**Wirkung:** Die Bedingung (2) aus `AGENTS.md` ist mit dieser Prüfung **inhaltlich erbracht**,
formal aber erst dann vollständig, wenn A-01 einen Ort schafft, an dem sie im Datensatz
eingetragen werden kann. Die als **(B)** markierten Auflagen — A-01, A-02, A-11, A-13, A-14,
A-15 — sind **vor der ersten Policy-Mutation** zu erfüllen. Die als **(T)** markierten sind im
Text der Anweisung zu erfüllen und am verpflichtenden Integrationsreview von `0044-04` zu
prüfen.

Diese Prüfung erlaubt niemandem, einen Checkpoint zu überschreiten, hebt den
`Integration review: mandatory` auf `0044-04` nicht auf und erzeugt kein `Acceptance: ✓`.

---

## 9. Was ich nicht prüfen konnte

1. **Die Vollständigkeit der Erhebung selbst.** Mir lag nur die Quittung vor, nicht der
   Chatverlauf. Der Digest deckt sich mit dem im Commit `1edc98ec1` genannten — das belegt
   **Unverändertheit seit dem Commit**, nicht Vollständigkeit **bei der Erhebung**. Wäre in der
   Quittung eine Frage, eine Option oder eine Korrektur des Managements ausgelassen worden,
   könnte ich das nicht erkennen.
2. **Die Anweisung selbst.** Sie existiert nicht. Diese Prüfung betrifft ausschließlich die
   beschlossene Reichweite, nicht deren spätere Umsetzung. Ob die geschriebene Anweisung die
   Auflagen einlöst, ist am Integrationsreview von `0044-04` zu prüfen, nicht hier.
3. **`Data-Riker`s vollständige Analyse.** Ich habe seinen committeten Claim auf Branch
   `0044-04` (`b098882fa`) gelesen. Seine Inbox-Meldung an `kathryn` vom 2026-08-21T23:03:08Z
   lag mir nicht vor — sie war nicht an mich adressiert. Falls sie über den Claim hinausgeht,
   ist dieser Teil ungeprüft.
4. **Keine Werkzeugläufe.** Ich habe keine Validierung ausgeführt. Das ist Absicht: ein grünes
   Ergebnis beweist nichts über die Richtigkeit einer Reichweite, und ich wollte nichts in
   diesen Bericht schreiben, was so gelesen werden könnte.
5. **Aktueller Zustand der `0043`-Claims.** Ich habe die Claim-Dateien auf den Branches
   `0043-04` und `0043-05` gelesen (Tips `b9bef3f42`, `afcba7663`). Ob `Data-Aria` und
   `Data-Julia` noch aktive Sessions sind, kann ich nicht feststellen — der Postkasten zeigt
   Zählerstände, keine Lebendigkeit. Ich habe die Claims deshalb als **gültig** behandelt und
   nicht angefasst, wie es `AGENTS.md` verlangt.
