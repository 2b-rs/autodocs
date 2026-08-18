# Entscheidungsdatensätze und Base-Ref-Analyse zu Feature `0041`

**Format:** nach `RQ-DEC-01/02/03` (Zeitpunkt, entscheidende Identität, fachliche
Rechtfertigung), append-only. Auslöser der Aufzeichnungspflicht ist `TK-2`
(`docs/pipeline/process-roles.md`): alle vier Entscheidungen wirken über die
Arbeitseinheit hinaus, in der sie getroffen wurden.

---

## `DEC-0041-001` — Worker-Arbeitsbäume werden Klone

- **Zeitpunkt:** 2026-08-18
- **Entscheidende Instanz:** aktueller Benutzer (Management)
- **Entscheidung:** Sekundäre Arbeitsbäume für Worker werden auf `git clone` / `git push` umgestellt.
- **Fachliche Rechtfertigung:** Der bisherige Aufbau teilte `.git` zwischen `/tmp/autodocs` und dem kanonischen Repo — bei der Symlink-Variante zusätzlich `HEAD` und Index. Ein Commit im einen Baum bewegte den `HEAD` des anderen, dessen Arbeitsbaum stehenblieb. Das erzeugte den Anschein verlorener Arbeit und darauf aufbauend einen Falschvorwurf gegen eine korrekt arbeitende Session.
- **Bewusst aufgegeben:** Der bisherige Vorteil „instantly durable im gemeinsamen Objektspeicher". Dauerhaftigkeit beginnt jetzt beim Push. Das ist der Preis der Isolation.
- **Umsetzung:** `0041-01`, committet als `8aafc0cb4`.

## `DEC-0041-002` — Der separate Bookkeeping-Commit entfällt

- **Zeitpunkt:** 2026-08-18
- **Entscheidende Instanz:** aktueller Benutzer (Management)
- **Entscheidung:** Der Bookkeeping-Commit für den Übergang `[p]` → `[x]`/`[w]` entfällt. Stattdessen trägt der substantielle Check-in-Commit die Ticket-ID und die Base-Ref.
- **Fachliche Rechtfertigung:** Der Zweischritt ist strukturell fragil — der zweite Commit hängt vom Hash des ersten ab, kann also erst danach geschrieben werden, und nichts erzwingt ihn. Vier Tasks stehen belegt in diesem Zustand: `0007-01`, `0037-37`, `0038-02`, `0038-18`. Die Entscheidung entfernt die Ursache, statt sie zu überwachen.
- **Umsetzung:** `0041-02`.

## `DEC-0041-003` — `REF`-Tagging wandert in die Abnahme

- **Zeitpunkt:** 2026-08-18
- **Entscheidende Instanz:** aktueller Benutzer (Management)
- **Entscheidung:** `REF` ist nicht mehr Bedingung für `[x]`/`[w]`, sondern Bestandteil des Übergangs `[x]` → `✓`, und dort häufig optional.
- **Fachliche Rechtfertigung:** Folgt aus `DEC-0041-002`: ohne Bookkeeping-Commit gibt es zum Zeitpunkt `[x]` keinen Ort mehr, an dem ein `REF` entstünde. Die Angabe gehört dorthin, wo sie geprüft wird.
- **Offen:** In welchen Fällen `REF` verpflichtend bleibt, ist bei der Umsetzung ausdrücklich zu benennen — „häufig optional" ist keine prüfbare Bedingung.
- **Umsetzung:** `0041-03`.

## `DEC-0041-004` — Semantik der Base-Ref

- **Zeitpunkt:** 2026-08-18
- **Entscheidende Instanz:** aktueller Benutzer (Management), nach Analyse und Gegenvorschlag des Requirements Engineers
- **Gegenstand:** Was genau benennt die `Base-Ref` im Check-in-Trailer?
- **Entscheidung:**

  > **Base-Ref ist der Commit, auf dem der Branch stand, unmittelbar bevor die erste substantielle Änderung erfolgte.**

  Dazu die maschinell prüfbare Invariante:

  > `git merge-base --is-ancestor <Base-Ref> <tragender Commit>` muss zutreffen.

- **Verworfene Alternative (Vorschlag des Benutzers):** Fallunterscheidung nach Anzahl der Prerequisites — bei einem Prerequisite dessen substantieller Commit bzw. Review-Commit, bei mehreren das Ergebnis des Preintegration-Merge.
- **Fachliche Rechtfertigung der Verwerfung:** siehe Analyse unten. Kurz: das Unterscheidungsmerkmal ist nicht die Anzahl der Prerequisites, sondern ob die Preintegration einen neuen Commit erzeugt hat. Ein einzelnes Prerequisite kann sehr wohl einen echten Merge erzeugen; die Regel hätte dann einen Commit benannt, auf dem nachweislich nicht aufgesetzt wurde.
- **Fachliche Rechtfertigung der Verwerfung des Review-Commits:** Abnahmedatensätze entstehen als eigene Bookkeeping-Commits auf dem Feature-Branch und sind in der Regel **kein Vorfahr** der Arbeit. Zudem ist der Abnahmestand veränderlich — ein Prerequisite kann nach Arbeitsbeginn abgenommen werden —, die Base-Ref hingegen nicht. „Worauf habe ich aufgesetzt" und „welchen Abnahmestand hatte das damals" sind zwei Fakten; der zweite gehört in den Claim, wo die Einzeltips nach `branch-workflow.md` ohnehin festzuhalten sind.
- **Umsetzung:** `0041-02` (Trailer-Format), Invariante als Prüfung.

---

## Analyse: Kann git den Verzweigungspunkt rekonstruieren?

**Anlass.** Die Frage war, ob eine explizite `Base-Ref` überhaupt nötig ist, oder
ob sich der Startzustand eines Branches nachträglich aus git ableiten lässt.

**Ergebnis: nein — und ausgerechnet im Preintegration-Fall gar nicht.**

**Versuchsaufbau.** Ein Feature-Branch `0042`, ein Prerequisite-Task `0042-01`,
der davon abzweigt, danach ein Weiterlaufen des Feature-Branches, dann ein Task
`0042-02`, der vom aktuellen Feature-Branch abzweigt und das Prerequisite
hineinmergt. **Nur ein einziges Prerequisite** — und dennoch ein echter Merge:

```
* 809ed74  0042-02 substantielle Arbeit
*   3c1741d  Merge branch '0042-01' into 0042-02   <- tatsächlicher Startzustand
|\
| * 547f288  0042-01 Arbeit                        <- Prerequisite-Tip
* | 7b9923e  F1: Feature-Branch läuft weiter       <- Parent-Tip
|/
* 3819c0f  F0
```

**Messung.**

| Abfrage | Ergebnis |
|---|---|
| `git merge-base 0042-02 0042` | `7b9923e` — Parent-Tip |
| `git merge-base 0042-02 0042-01` | `547f288` — Prerequisite-Tip |
| `git merge-base --fork-point 0042 0042-02` | `7b9923e` |
| **tatsächlicher Startzustand** | **`3c1741d` — von keiner Abfrage geliefert** |

**Auswertung.**

1. Git kennt die **Eingänge** des Preintegration-Merge, nie sein **Ergebnis**. Es
   existiert kein Metadatum, das markiert, ab welchem Commit die Arbeit begann.
2. `merge-base` setzt voraus, dass beide Branches noch existieren. Nach dem
   Hochmerge und Löschen des Task-Branches ist auch diese Auskunft verloren.
3. Der Versuch widerlegt zugleich die verworfene Alternative: Er hat genau ein
   Prerequisite, und dessen Tip `547f288` enthält `F1` (`7b9923e`) nicht. Die
   Fallunterscheidung nach Prerequisite-Anzahl hätte hier eine falsche Base-Ref
   eingetragen.
4. Die beschlossene Formulierung erzeugt in beiden Fällen dieselbe richtige
   Angabe: ist die Preintegration ein Fast-Forward, fällt der Prerequisite-Tip
   automatisch heraus; ist sie ein echter Merge, der Merge-Commit. Es braucht
   keine Fallunterscheidung.
5. Die Invariante `--is-ancestor` hätte beide Fehlerfälle abgewiesen: den
   falschen Prerequisite-Tip ebenso wie den Review-Commit.

**Nicht geprüft.** Ob squash-merges oder rebases in diesem Repo vorkommen; beide
würden die Invariante verletzen, ohne dass die Base-Ref sachlich falsch wäre. Bei
der Umsetzung von `0041-02` ist zu entscheiden, ob solche Verfahren
ausgeschlossen oder gesondert behandelt werden.
