# Managemententscheidungen — Branching- und Merging-Strategie (`DEC-0044-007..010`)

**Autorität:** Management (aktueller User), Beschluss vom 2026-08-21:
„Sehr gut, Kathryn. Machen Sie es so." — vollständige Annahme aller vier
Empfehlungen der Entscheidungsvorlage.
**Vorlage:** [`entscheidungsvorlage-branching-merging-strategie.md`](entscheidungsvorlage-branching-merging-strategie.md)
(Commit `8d9469ba3`), erstellt von Projektleiter Kathryn auf Management-Anweisung.
**Protokollant:** `agent:kathryn:projektleiter:branching-strategie:20260821T090000Z`
(`unprivileged`; protokolliert die Entscheidung, trifft sie nicht — `DEC-ROLE-001`).
**Geltung:** ab Beschluss, **ohne Rückwirkung** (siehe `DEC-0044-010`).

---

## `DEC-0044-007` — Herkunft wird aufgezeichnet, nicht rekonstruiert

- **Entscheidung:** Policy-Commits weisen ihre Herkunft im Commit-Objekt nach
  (Trailer, z. B. `Policy-Origin-Branch:`). Werden Commits von einem anderen
  Branch als der direkten Vorgängerkette übernommen, geschieht das über einen
  echten Merge-Commit (`--no-ff`), nicht per Fast-Forward.
- **Fachliche Rechtfertigung:** Git speichert keinen Autoren-Branch. Ein per
  `git merge --ff-only`/`git update-ref` absorbierter Commit hat genau einen
  Parent und liegt auf der First-Parent-Kette — topologisch identisch mit einem
  nativ entstandenen. Drei unabhängige Reviewrunden unter `0044-01` haben das
  belegt (zwei falsch-positive, dann ein falsch-negativer Befund, Verdikte
  `fd2cf9237`, `c80ad6258`, `b62df43a8`). Jede rein nachträgliche lokale Prüfung
  ist deshalb entweder zu streng oder zu lax. Aufgezeichnete Herkunft ist die
  einzige mit Gits Datenmodell verträgliche Lösung.
- **Umsetzung:** neuer Task unter Feature `0044` (Trailer-Konvention,
  `branch-workflow.md`, Anpassung von `_src/tools/check_policy_provenance.py`).

## `DEC-0044-008` — Zweischichtige Durchsetzung: Hook als Netz, Integrator als Tor

- **Entscheidung:** Ein `reference-transaction`-Hook erkennt und protokolliert
  Fremdherkunft im Moment der Ref-Änderung. Verbindliches Tor bleibt die Prüfung
  des Integrators am Integrationscheckpoint. Ein fehlender, entfernter oder
  umgangener Hook gilt **niemals** als „geprüft".
- **Fachliche Rechtfertigung:** Zur Transaktionszeit ist die Information
  vollständig vorhanden; nachträglich nicht. Verifiziert (Kathryn, 2026-08-21,
  isolierte Scratch-Repositories, Git 2.50.1): Der Hook feuert bei
  `git merge --ff-only` **und** bei `git update-ref` — `update-ref` umgeht
  `pre-commit` vollständig, `reference-transaction` nicht — und kann die
  Fremdherkunft im Moment der Operation feststellen. Hooks sind jedoch nicht
  versioniert, werden nicht mitgeklont und sind umgehbar; sie sind ein Netz,
  keine Garantie. Worktrees teilen sich das gemeinsame `.git`-Verzeichnis, ein
  Hook wirkt daher in allen zugleich.
- **Umsetzung:** derselbe Task wie `DEC-0044-007`; Prosa in
  `branch-workflow.md` bleibt die Autorität.

## `DEC-0044-009` — Root-Checkout ist schreibgeschützt; Hygieneprüfung vor Integration

- **Entscheidung:** Agenten mutieren ausschließlich in vorgangseigenen
  Worktrees. Der Root-Checkout `/Users/tobias.anton/devel/autodocs` wird nicht
  mehr beschrieben. Vor jeder Integration wird geprüft, dass Index und `HEAD`
  übereinstimmen und keine fremden gestagten Bäume vorliegen.
- **Fachliche Rechtfertigung:** Der Schaden sitzt hier im
  Arbeitsverzeichniszustand, nicht in der Historie; keine historienbasierte
  Kontrolle erfasst ihn. Gefunden wurde er nur durch manuelle Inspektion. Das
  Repository betreibt 78 Worktrees — der Root-Checkout war der einzige, der
  keinem Vorgang gehörte und trotzdem beschrieben wurde.
- **Umsetzung:** Regel in `AGENTS.md`/`branch-workflow.md`; Hygieneprüfung als
  Schritt der Integrationsprozedur. Ausführungsprotokoll siehe unten.

## `DEC-0044-010` — `DEC-0044-002` wird um eine Aufzeichnungspflicht erweitert

- **Entscheidung:** Das Herkunftsverbot wird ergänzt: Wer einen Policy-Commit
  auf einen Branch bringt, macht dessen Herkunft nachweisbar. Absorption ohne
  solchen Nachweis gilt als Verletzung, unabhängig vom Mechanismus. Die Regel
  gilt **ab Beschluss**; Altbestand trägt keine Nachweise und wird nicht
  nachgerüstet.
- **Fachliche Rechtfertigung:** Beweislastumkehr. Bisher musste der Prüfer eine
  Verletzung nachweisen und konnte es nachweislich nicht; künftig belegt der
  Einbringende die Herkunft.
- **Restrisiko, ausdrücklich akzeptiert:** Wer den Nachweis weglässt, den Hook
  umgeht und am Checkpoint nicht auffällt, bleibt unentdeckt. Vollständige
  mechanische Sicherheit ist mit lokalem Git und kooperativen Agenten nicht
  erreichbar. Ziel ist, dass ein Verstoß **auffällt**, nicht dass er unmöglich
  wird.
- **Umsetzung:** Änderung von `DEC-0044-002` im Intake-Dossier durch das
  Management bzw. additiver Verweis; `0044-02` führt die Aufzeichnungspflicht
  von Anfang an mit.

---

## Ausführungsprotokoll zu `DEC-0044-009` — Bereinigung des Root-Index

Ausgeführt von `agent:kathryn:projektleiter:branching-strategie:20260821T090000Z`
am 2026-08-21 auf Management-Freigabe („Machen Sie es so").

**Vorbefund.** Der Index des Root-Checkouts trug einen Baum aus der Zeit vor dem
Abschluss von Feature `0040`: 138 Dateien, 2687 Einfügungen, 28683 Löschungen
gegenüber `HEAD` (`139b865cb`).

**Sicherung vor dem Eingriff.** Der Index-Baum entsprach exakt dem bereits
gesicherten Tag `preserved/root-index-20260821` (Tree `b95deccc`, bit-identisch
geprüft). Der **Arbeitsbaum** entsprach jedoch **keinem** der beiden vorhandenen
Sicherungstags (Arbeitsbaum-Tree `773edcec`, gemessen über einen temporären
Index ohne Berührung des echten Index; `preserved/root-unstaged-draft-20260821`
trägt `dd75de67`). Deshalb wurde vor dem Eingriff ein vollständiger Snapshot
angelegt:

- `preserved/root-worktree-20260821-kathryn` → Commit `88e335c27`,
  Tree `773edcec7` (Arbeitsbaum inklusive bis dahin untracked Dateien).

**Eingriff.** `git reset -q HEAD -- .` im Root-Checkout. Ergebnis verifiziert:
`git diff --cached --stat HEAD` ist leer.

**Nachtrag: Arbeitsbaum ebenfalls bereinigt (2026-08-21, später am selben Tag).**

Der zunächst offen gelassene Restbefund wurde nach Klärung geschlossen. Kriterium
war nicht eine Frist, sondern der Nachweis, dass niemand dort arbeitet — eine
„Runde" ist keine Zeitspanne, da der Briefkasten erst zustellt, wenn eine Session
ihren nächsten Zug macht.

Nachweis vor dem Eingriff:

- **Zeitstempel:** die zuletzt geänderte Datei im Root-Checkout war rund 28
  Stunden alt (2026-08-20 09:46 lokal). Eine dort arbeitende Session hinterlässt
  frische mtimes.
- **Lebende Sessions:** vier, keine davon im Root-Checkout schreibend; alle
  Roster-Agenten mit Claim nennen ausdrücklich ihren eigenen Worktree.
- **Direkte Rückfrage** an die einzige nie am Briefkasten registrierte Session
  (`b1ed11db`, RE-/Analysefunktion, kein Claim, keine Lease). Antwort: „Keine
  Arbeit im Root-Checkout", belegt durch `git merge-base --is-ancestor` für alle
  neun Commits jener Session gegen `HEAD`.

Eingriff: `git restore --source=HEAD --worktree -- .`. Verifiziert: Arbeitsbaum
und Index stimmen mit `HEAD` überein, getrackte Abweichungen 0; `DONE.md` enthält
wieder 88 Erwähnungen von `0040` (vorher 0). Die 25 untracked Einträge
(`.worktrees/`, `.zed/`, Claim-Dateien u. a.) blieben unberührt — es wurde
bewusst **kein** `git clean` ausgeführt.

**Offener Punkt zur Entscheidung.** Die zurückgestellte `TODO.md` enthielt einen
Hunk, den `HEAD` nicht kennt: die Zustandskorrektur zu `0037-49` (Marker `[d]` →
`[u]`, „State correction (2026-08-19, user-directed)"). Er stammt von keiner der
befragten Sessions. Er ist vollständig gesichert — `git show
preserved/root-worktree-20260821-kathryn:TODO.md` ist byteidentisch mit dem
zurückgestellten Stand — lebt aber jetzt nur noch im Snapshot. **Bevor der Tag
aufgeräumt wird, muss entschieden werden, ob diese Korrektur regulär nach `HEAD`
gehört.** Inhaltlich spricht dafür, dass `[d]` kein im Contract definierter
Marker ist. (Befund gemeldet von Session `b1ed11db`.)

**Ursprünglicher Restbefund, zum Zeitpunkt der Index-Bereinigung — historisch:**

**Damals offen, inzwischen behoben (siehe Nachtrag).** Der **Arbeitsbaum** des
Root-Checkouts weicht weiterhin von `HEAD` ab (127 Dateien, 1241 Einfügungen,
39401 Löschungen); `DONE.md` auf Platte enthält null Erwähnungen von `0040`,
`HEAD` dagegen 88. Ein `git commit -a` dort würde den Abschluss von Feature
`0040` weiterhin zurücknehmen; ein einfaches `git commit` nach dieser
Bereinigung nicht mehr.

Der Arbeitsbaum wurde **nicht** zurückgesetzt, weil er potenziell lebende Arbeit
fremder Sessions enthält und die Freigabe den Index betraf. Die Wiederherstellung
ist jederzeit verlustfrei möglich (`preserved/root-worktree-20260821-kathryn`).
Empfehlung: Eine benannte Session bestätigt, dass keine lebende fremde Arbeit
betroffen ist, und stellt den Root-Checkout dann auf `HEAD` zurück.
