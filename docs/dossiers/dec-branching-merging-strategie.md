# Managemententscheidungen — Branching- und Merging-Strategie (`DEC-0044-008..011`)

> **Nummernkorrektur (2026-08-21).** Diese Datensätze trugen zunächst
> `DEC-0044-007..010`. `DEC-0044-007` war bereits vergeben: Architektin
> `seven-bellana` hatte darunter die Disposition zum Fast-Forward-Blindfleck
> aufgezeichnet (`docs/dossiers/0044-01-branch-workflow-prose-scope-review.md`
> §5, inzwischen auf `main`, zitiert in `branch-workflow.md` und im Docstring
> von `check_policy_provenance.py`). Umnummeriert auf `008..011`; inhaltlich
> unverändert. Der Fehler entstand, weil die Vorlage gegen `main` bei
> `139b865cb` erstellt wurde, während `0044-01` parallel weiterlief — genau die
> Art Kollision, die entsteht, wenn IDs ohne gemeinsame Vergabestelle vergeben
> werden.

**Verhältnis zu `DEC-0044-007` (Architektin, `0044-01`).** Jene Entscheidung
wählte die Restrisiko-Variante und ergänzte sie um eine Prosaregel: Absorption
außerhalb der eigenen Vorgänger-/Nachfolgerkette erfordert einen `--no-ff`
Merge-Commit. Sie war ausdrücklich auf den mechanischen Check zu `DEC-0044-002`
begrenzt und verwies die repository-weite Frage an das Management. Die
vorliegenden Entscheidungen beantworten genau diese Frage und gehen darüber
hinaus: Sie machen die Herkunft **aufzeichnungspflichtig** (`DEC-0044-008`) und
ergänzen eine Durchsetzungsschicht (`DEC-0044-009`). `DEC-0044-007` bleibt
gültig und wird nicht aufgehoben; ihre Prosaregel ist der Teilfall, den
`DEC-0044-008` verallgemeinert.

**Autorität:** Management (aktueller User), Beschluss vom 2026-08-21:
„Sehr gut, Kathryn. Machen Sie es so." — vollständige Annahme aller vier
Empfehlungen der Entscheidungsvorlage.
**Vorlage:** [`entscheidungsvorlage-branching-merging-strategie.md`](entscheidungsvorlage-branching-merging-strategie.md)
(Commit `8d9469ba3`), erstellt von Projektleiter Kathryn auf Management-Anweisung.
**Protokollant:** `agent:kathryn:projektleiter:branching-strategie:20260821T090000Z`
(`unprivileged`; protokolliert die Entscheidung, trifft sie nicht — `DEC-ROLE-001`).
**Geltung:** ab Beschluss, **ohne Rückwirkung** (siehe `DEC-0044-011`).

---

## `DEC-0044-008` — Herkunft wird aufgezeichnet, nicht rekonstruiert

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

## `DEC-0044-009` — Zweischichtige Durchsetzung: Hook als Netz, Integrator als Tor

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
- **Umsetzung:** derselbe Task wie `DEC-0044-008`; Prosa in
  `branch-workflow.md` bleibt die Autorität.

## `DEC-0044-010` — Root-Checkout ist schreibgeschützt; Hygieneprüfung vor Integration

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

## `DEC-0044-011` — `DEC-0044-002` wird um eine Aufzeichnungspflicht erweitert

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

## `DEC-0044-012` — Governance liegt auf `main`; Abstimmung läuft über die agent-inbox

- **Entscheidung (Management, 2026-08-21).** Zwei Regeln, die zusammengehören:
  1. Änderungen an Governance-Prozessen werden **immer auf `main`** durchgeführt.
     `main` muss in Bezug auf Governance **immer aktuell** sein. Ein
     Governance-Artefakt darf nicht auf einem Branch liegenbleiben, während
     andere Agenten gegen `main` arbeiten.
  2. Agenten stimmen sich über die **agent-inbox** ab.
- **Geltungsbereich.** Governance-Artefakte sind mindestens: Entscheidungs­daten­sätze
  (`DEC-*`), die Autoritätsdateien `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`,
  `CLAUDE.md`, alles unter `docs/pipeline/` sowie der Marker- und
  Prerequisite-Vertrag im `TODO.md`-Header. Fachliche Arbeitsprodukte sind nicht
  gemeint — die laufen unverändert über Vorgangs-Branches nach
  `docs/pipeline/branch-workflow.md`.
- **Fachliche Rechtfertigung.** Der Anlass ist die ID-Kollision bei
  `DEC-0044-007`, oben dokumentiert. Der Datensatz wurde auf einem Branch gegen
  `main` bei `139b865cb` angelegt, während `0044-01` denselben Nummernraum auf
  `main` parallel belegte. Zwei unveränderliche Datensätze trugen dieselbe
  Kennung und beantworteten dieselbe Frage gegensätzlich. Auf `main` angelegt,
  wäre die Kollision beim Anlegen sofort sichtbar gewesen: `main` ist die
  einzige Stelle, an der eine Vergabestelle für IDs überhaupt existieren kann.
  Derselbe Mechanismus erklärt den zweiten Vorfall desselben Tages — die
  `0037-49`-Zustandskorrektur war an einen Branch gebunden statt auf `main`
  sichtbar, weshalb sie mehrfach als fremder, unerklärlicher Hunk auftauchte.
  Governance ist gemeinsamer Zustand; gemeinsamer Zustand auf privaten Branches
  ist nicht abstimmbar, sondern nur nachträglich rekonstruierbar — dieselbe
  Fehlerklasse, die `DEC-0044-008` für die Herkunft bereits verworfen hat.
- **Zur agent-inbox.** Der Postkasten ist kein Telefon: nichts wird zugestellt,
  der Empfänger sieht Post erst in seinem nächsten Zug. Eine Abstimmung ist
  deshalb erst abgeschlossen, wenn die Antwort vorliegt, nicht wenn die Nachricht
  abgeschickt ist. Vor folgenreichen Aktionen — Merge auf `main`, Acceptance,
  Vergabe einer neuen Kennung — ist die Inbox zu lesen. Genau diese Prüfung fiel
  bei der Kollision aus: der Sequenzierungshinweis lag im Postkasten, während der
  Merge lief. Adressen sind fallunterscheidend (`Data` und `data` sind zwei
  Postfächer).
- **Umsetzung.** Diese Entscheidung wird selbst nach ihrer eigenen Regel
  behandelt: direkt auf `main` aufgezeichnet, nicht über einen Branch. Die
  Verankerung in `AGENTS.md` und `docs/pipeline/branch-workflow.md` steht noch
  aus und ist ein eigener Vorgang.
- **Provenienz.** Nutzer-Prompt vom 2026-08-21, wortwörtlich: „Darum müssen
  änderungen an Governance-Prozessen auch immer auf main durchgeführt werden und
  main muss bzgl. Governance auch immer aktuell sein. In Zukunft stimmt ihr euch
  über agent-inbox ab, ja?"

## Klarstellung zum Geltungsbereich von `DEC-0044-012` (2026-08-21)

**Anlass.** Worf fragt, ob append-only Abnahme-Evidenz unter
`docs/pipeline/approvals/` als Governance-Artefakt zuerst auf `main` entstehen
muss, oder ob sie als Arbeitsprodukt auf dem Vorgangszweig reisen darf. Er hat
einen von einem Architekten geforderten Merge bis zur Klärung angehalten — richtig
so. Data meldet denselben Zweifel für `docs/pipeline/reports.md` in `0043-05`.

**Klarstellung.** Maßgeblich ist nicht der Pfad, sondern die Frage: *Legt das
Artefakt eine Regel für andere fest, oder hält es eine Tatsache über einen
einzelnen Vorgang fest?*

- **Governance, gehört auf `main`:** alles, was eine Regel, einen Vertrag oder
  einen gemeinsamen Nummernraum festlegt — `DEC-*`, die Autoritätsdateien, die
  *Prozessbeschreibungen* unter `docs/pipeline/` (`branch-workflow.md`,
  `task-acceptance.md`, `process-roles.md`, `reports.md` und dergleichen), der
  Marker- und Prerequisite-Vertrag im `TODO.md`-Header.
- **Arbeitsprodukt, reist auf dem Zweig:** vorgangsgebundene, append-only
  **Evidenz** — insbesondere alles unter `docs/pipeline/approvals/`. Diese
  Datensätze legen keine Regel fest; sie bezeugen einen Zustand zu einer exakten
  Baseline.

**Begründung.** `DEC-0044-012` sagt selbst, gewöhnliche Arbeitsprodukte seien
keine Governance-Artefakte. Abnahme-Evidenz ist der Musterfall: Ihr ganzer Zweck
ist die Bindung an einen bestimmten Commit. Sie vorab auf `main` zu verlangen,
zerstörte genau diese Bindung und widerspräche dem Abnahme-Workflow, der Evidenz
an exakte Task-Baselines knüpft. Der Zweck von `DEC-0044-012` war, *gemeinsamen*
Zustand — Regeln und Kennungsvergabe — sichtbar zu halten; eine Aussage über
einen einzelnen Vorgang ist kein gemeinsamer Zustand.

**Folge für die anfragenden Sessions.** Worf darf den nicht-publizierenden Merge
der `0019`-Evidenzpakete auf den Vorgangszweigen ausführen; `DEC-0044-012` steht
dem nicht entgegen. Für `0043-05` gilt: der Anteil an `docs/pipeline/reports.md`
ist Prozessbeschreibung und daher auf `main` nachzuziehen; die Berichte und ihre
Evidenz bleiben auf dem Zweig.

**Status.** Dies ist die Auslegung einer bestehenden Entscheidung durch die
Projektleitung, kein neuer Beschluss — die Unterscheidung „Regel" gegen „Tatsache
über einen Vorgang" ist im Text von `DEC-0044-012` bereits angelegt. Das
Management kann sie jederzeit anders ziehen; bis dahin ist sie die
Arbeitsgrundlage, damit niemand weiter blockiert.

## `DEC-0044-013` — Selbst gestarteter Reviewer: Persona getrennt, Briefing aufgezeichnet

- **Entscheidung (Management, 2026-08-21).** Ein von der prüfenden Session selbst
  gestarteter Subagent darf die `TK-1`-Unabhängigkeit erfüllen, wenn drei
  Bedingungen zugleich gelten: er nimmt **ausdrücklich die Persona des Reviewers
  an**; diese Persona ist **verschieden von der Persona des Erzeugers**; und
  **Prompt und übergebener Kontext werden dokumentiert**. Der Datensatz nennt die
  dispatchende Identität, die Reviewer-Persona, das wortwörtliche Briefing und
  welchen Kontext der Reviewer bekommen hat und welchen nicht.
- **Fachliche Rechtfertigung.** Der Vorfall, der die Frage aufwarf: Seven startete
  für die vierte Reviewrunde zu `0044-01` über ihr eigenes Agent-Tool die Persona
  „Seven-Tom", die die Arbeit dreier ebenfalls von ihr gestarteter Personas
  prüfte, `Acceptance: ✓` setzte und nach `main` integrierte. Sie hat es selbst
  gemeldet. Denselben Fall hatte dieselbe Session bei `0038-26` früher am Tag
  korrekt erkannt und einen Waiver eingeholt. Ermessen ist hier also nicht
  unfähig, sondern unzuverlässig.
  Die gewählte Lösung setzt nicht auf Verbot, sondern auf **Nachprüfbarkeit**: Der
  Zweifel an einem selbst gestarteten Reviewer ist nicht, dass er dieselbe
  Laufzeit benutzt, sondern dass er auf die gewünschte Antwort hin gebrieft worden
  sein könnte. Genau das wird durch das aufgezeichnete Briefing entscheidbar.
  Ohne Briefingtext ist im Nachhinein niemand in der Lage, das zu beurteilen —
  deshalb erfüllt ein **nicht aufgezeichneter** selbst gestarteter Reviewer
  `TK-1` nicht.
- **Abgrenzung.** Die Anforderung getrennter Personas ist keine Formalie: Erzeuger
  und Reviewer müssen unterscheidbar benannt sein, sonst ist der Datensatz nicht
  lesbar. Der Waiver-Pfad für den Fall, dass gar kein Reviewer erreichbar ist,
  bleibt daneben bestehen (Vorbild `0038-26`).
- **Umsetzung.** Verankert in `AGENTS.md` unter „Implementation completion and
  privileged acceptance". Eine maschinelle Prüfung, die einen Acceptance-Record
  ohne aufgezeichnetes Briefing meldet, ist noch offen und wäre ein eigener
  Vorgang.
- **Provenienz.** Nutzer-Antwort vom 2026-08-21, wortwörtlich: „Selbst erzeugte
  Prüfer sind ok, sofern sie die Persona des Prüfers annehmen, der vom Erzeuger
  verschieden sein muss. Der Prompt und der Kontext, den sie übernehmen, muss
  dokumentiert werden."

## Korrekturvermerk zu `DEC-0044-014` (2026-08-21, nachgetragen)

**Die Entscheidung bleibt gültig. Ihre tragende Begründung war falsch.**

`DEC-0044-014` stützt sich unten auf den Befund, die Anforderung von `0037-49`
sei „nicht unerfüllt, sondern unerfüllbar". Das stimmt nicht. Sie war zum
Zeitpunkt der Entscheidung **bereits erfüllt** — seit dem 2026-08-16, 16:42 Uhr.

Beleg, nachträglich erhoben: Commit `e0c969976` des Repository-Eigentümers sagt
in seiner eigenen Nachricht wörtlich „All 6 readiness checks pass (EXIT=0)". Der
Befund gilt unverändert; `python3 _src/tools/manage_approval_readiness.py --check
--json` liefert `all_ok: true`, Exit 0. Remote konfiguriert, SSH-Signierung aktiv,
`allowed_signers` mit zwei echten `ssh-ed25519`-Prinzipalen statt Platzhaltern,
`authorities.json` mit echten Fingerabdrücken für alle fünf Rollen, ein
verifizierter Credential-Handle.

**Wie der Fehler entstand.** Drei Sessions nacheinander haben denselben Fehler
gemacht: den **Tickettext** und ein am 2026-08-16 eingefrorenes Reifegrad-Dokument
gelesen, das in jeder Zeile `BLOCKED` sagt, statt den **Zustand** zu messen. Erst
wurde `[d]` gesetzt, dann von Seven vertragskonform auf `[u]` korrigiert, dann
baute ich eine Managemententscheidung darauf. Ein einziger Aufruf des Werkzeugs,
das für genau diese Frage gebaut wurde (`0038-15`), hätte den Fehler in jeder der
drei Runden beendet. Ich habe Sevens Abhängigkeitskette nachgerechnet und
bestätigt, aber nie deren Prämisse geprüft.

**Was von der Entscheidung trägt.** Der Zuschnitt auf Einzelautorität ist
sachlich richtig und bleibt in Kraft — aber er beschreibt, was der Eigentümer
längst gebaut hatte: `authorities.json` legte alle fünf Rollen bereits auf eine
Person, mit dem ausdrücklichen Vermerk „Solo project: approver is also
implementer". Falsch war nicht das *Was*, sondern das *Warum*: Die Neufassung von
`0037-49` hat den Tickettext an eine bestehende Konfiguration angeglichen; sie
hat kein Hindernis beseitigt, weil keines vorlag.

**Folge.** `0037-49` ist am selben Tag geschlossen worden (`[x]`, Bericht
`9d4815c6b`, Buchführung `aaa74b8e6`, Branch `0037-49`) — ohne dass irgendeine
externe Bereitstellung nötig gewesen wäre. Das Feature war fünf Tage lang
grundlos blockiert.

**Lehre, als Vorschlag und nicht als Beschluss.** Ein Vorgang, dessen Blocker
maschinell prüfbar ist, sollte den Prüfbefehl im Ticket nennen, und wer den
Zustand behauptet, sollte ihn ausgeführt haben. Das ist dasselbe Muster wie
`DEC-0044-009` und `LTD-DEFERRED-STALE`: gespeicherte Behauptungen über
ableitbaren Zustand veralten still. Hier hat eine solche Behauptung fünf Tage
lang ein ganzes Feature stillgelegt.

## `DEC-0044-014` — Feature `0037`: Genehmigungsregime auf Einzelbetrieb zuschneiden

- **Entscheidung (Management, 2026-08-21).** Das Genehmigungsregime aus Feature
  `0037` wird auf die tatsächliche Betriebsform zugeschnitten: **eine Autorität,
  ein Schlüssel**, Rollentrennung als dokumentierte Selbstauskunft statt als
  kryptografisch getrennte Identitäten. `0037-49` wird entsprechend neu gefasst,
  damit die abhängigen Vorgänge ausführbar werden.
- **Fachliche Rechtfertigung.** `0037-49` verlangte registrierte Prozess-,
  Security-/Privacy-, Release-, unabhängige Quality- und Translation-Review-Rollen,
  einen genehmigten Signaturdienst, eng gefasste Credential-Handles, einen dauerhaft
  laufenden Runner-Service und eine Out-of-Band-Bestätigung des Repository-Owners.
  Das ist die korrekte Antwort auf die Frage „wie genehmigt man in einem
  Repository mit mehreren Beteiligten" — nur stellt dieses Repository diese Frage
  nicht: Es wird von einer Person mit Agenten betrieben, die fünf getrennten
  Rollen wären dieselbe Person. Die Anforderung war damit nicht unerfüllt, sondern
  unerfüllbar. Seven hat unabhängig festgestellt und ich habe nachvollzogen, dass
  jede offene Task in `0037` transitiv an `0037-07` hängt und `0037-07` an
  `0037-49` — es gab keine unblockierte Insel, an der stattdessen hätte gearbeitet
  werden können.
- **Was erhalten bleibt.** Der Zuschnitt senkt die Zahl der Beteiligten, nicht die
  Prüftiefe: Antrags-/Entscheidungstrennung, Nachvollziehbarkeit, Digest-Bindung
  und die append-only Aufzeichnung bleiben. Was entfällt, ist die Annahme mehrerer
  natürlicher Personen.
- **Umsetzung.** Neufassung von `0037-49` und Prüfung der abhängigen Kriterien in
  `0037-07`, `0037-38`, `0037-43`, `0037-32`, `0037-33`, `0037-36`; eigener
  Vorgang, noch nicht ausgeführt. Die lokale Vorarbeit
  (`docs/pipeline/0037-49-external-readiness.md`, Fixtures,
  `_src/tools/manage_approval_readiness.py`) bleibt gültig und wird angepasst,
  nicht verworfen.
- **Provenienz.** Nutzer-Entscheidung vom 2026-08-21 auf die Vorlage
  `docs/dossiers/entscheidungsvorlage-offene-punkte-20260821.md`, Option A1
  („Auf dich zuschneiden").

## Ausführungsprotokoll zu `DEC-0044-010` — Bereinigung des Root-Index

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

**Offener Punkt — inzwischen weitgehend erledigt (Nachprüfung 2026-08-21).**
`0037-49` steht in `HEAD` bereits auf `[u]`: Seven hat den undefinierten Marker
`[d]` unabhängig repariert (Bookkeeping-Notiz unter `0037-49`). Der im Snapshot
verbliebene Hunk ist damit inhaltlich überholt. **Offen bleibt nur die
Bedeutungsfrage:** `[d]` wurde vom User selbst eingeführt (Commit `4dc9d9166`,
2026-08-16) und war als *deferred* gemeint, stand aber nie in der Marker-Legende
des `TODO.md`-Headers — dort sind nur `[ ]`, `[u]`, `[p]`, `[?]`, `[w]`, `[x]`
definiert. Die Korrektur auf `[u]` war gegen den Vertrag richtig, ersetzt aber
„zurückgestellt" durch „menschliche Entscheidung nötig". Ob `[d]` als eigener
Marker in die Legende gehört, ist eine offene Managemententscheidung.

**Ursprünglicher Befund, historisch:** Die zurückgestellte `TODO.md` enthielt einen
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

---

## `DEC-0044-015` — Wie ein Governance-Commit nach `main` gelangt, ohne den Root-Checkout zu veralten

- **Entscheidung (Management, 2026-08-21):** `DEC-0044-010` (Root-Checkout ist
  schreibgeschützt) wird um eine **eng begrenzte Ausnahme** ergänzt. Der letzte
  Schritt einer Integration nach `main` — und nur dieser — wird **im
  Root-Checkout** ausgeführt, weil `main` dort ausgecheckt ist. Alles andere
  bleibt verboten.
- **Fachliche Rechtfertigung:** `DEC-0044-010` und `DEC-0044-012` (Governance
  immer auf `main`) kollidieren in ihrem Wortlaut, solange `main` im
  Root-Checkout ausgecheckt ist. Git erlaubt keinen zweiten Worktree auf
  derselben Referenz. Ein `git update-ref refs/heads/main` aus einem
  losgelösten Worktree bewegt die Referenz **an Index und Arbeitsbaum des Roots
  vorbei** und erzeugt genau den veralteten Zustand, dessen Schaden
  `DEC-0044-010` überhaupt erst ausgelöst hat — bestätigt unter `0044-14`
  (Implementierer `Data-Miles-20260821T195500Z`, Reproduktion des Mechanismus).
  Ein `git merge` **im Root** bewegt dagegen Referenz, Index und Arbeitsbaum in
  einem Schritt und kann den Root deshalb nicht veralten lassen. Die Ausnahme
  ist damit keine Aufweichung von `DEC-0044-010`, sondern das einzige Verfahren,
  das dessen Schutzziel tatsächlich erreicht.
- **Autorisiertes Verfahren:**
  1. Governance-Arbeit in einem **vorgangseigenen Worktree** auf eigenem Branch
     von `main` autorieren und dort committen (Trailer nach `DEC-0044-008`).
  2. **Preflight, hart:** im Root gilt `git diff --quiet`, `git diff --cached
     --quiet`, und `HEAD` ist `refs/heads/main`. Andernfalls **Abbruch**.
  3. `main` vorrücken **aus dem Root heraus**: `git -C <root> merge --ff-only
     <branch>`, bzw. `--no-ff`, wenn der Branch nach `DEC-0044-008` nicht auf der
     direkten Vorgängerkette liegt.
  4. Worktree und Hilfsbranch entfernen.
- **Autorität:** ausschließlich **privilegierter Integrator oder
  Projektleitung**. Kein unprivilegierter Worker bewegt `refs/heads/main`.
- **Verbindliche Verbote:** `git update-ref` auf `refs/heads/main` ist
  **untersagt**. Jede andere Mutation des Root-Checkouts — Autorieren, `commit
  -a`, Aufräumen, Zurücksetzen — bleibt untersagt. Bei fehlgeschlagenem
  Preflight wird **abgebrochen, nicht aufgeräumt**; eine Bereinigung des Roots
  ist ein eigener, separat autorisierter Wiederherstellungsvorgang.
- **Erhaltene Kontrolle:** Die Hygieneprüfung aus `DEC-0044-010` bleibt
  Vorbedingung und wird durch dieses Verfahren nicht ersetzt.
- **Geltung:** ab Beschluss, ohne Rückwirkung. Die Verankerung des Verfahrens in
  `AGENTS.md` und `branch-workflow.md` erfolgt unter Task `0044-14`, dessen
  Abnahmekriterium „falls bestätigt, ist die erforderliche Auffrischung (oder
  das Loslösen des Root-Checkouts) dokumentiert" damit erfüllbar wird.

**Autorität:** Management (aktueller User), Beschluss vom 2026-08-21:
„Ja, DEC-0044-009 ist ratifiziert." — Der User bezog sich auf die
Root-Checkout-Regel; deren korrekte Kennung ist `DEC-0044-010`. Die
Verwechslung stammt aus einem frühen Rundruf der Projektleitung mit der später
korrigierten Nummerierung `007..010` und wird hier festgehalten, damit sie nicht
erneut auftritt.
**Vorbereitet von:** Projektleiter `kathryn` (`DEC-ROLE-001`: protokolliert,
entscheidet nicht).
**Fachliche Prüfung vor Beschluss:** privilegierter Koordinator `Data`
(2026-08-21T20:49Z, agent-inbox, Thread `work-dispatch`) — „no technical flaw in
the branch-to-root `git merge --ff-only/--no-ff` sequence"; die von `Data`
verlangten Auflagen (benannte Autorität, Preflight, Abbruch statt Aufräumen,
`update-ref`-Verbot, Prüfer bleibt Vorbedingung) sind oben vollständig
übernommen.

---

## `DEC-0044-016` — Umfang der Gates A1 und A2 für die Feature-Breakdown-Anweisung (`0044-04`)

- **Recorded at:** 2026-08-22T00:00:00Z
- **Deciding identity:** Management (aktueller User / Repository-Eigentümer)
- **Recording identity:** `agent:kathryn:projektleiter:0044-04-gate-scope:20260822T000000Z`
- **Role of the recorder:** Projektleiter unter `DEC-ROLE-001` — zeichnet auf,
  entscheidet nicht
- **Authority reference:** vier Managemententscheidungen aus einem strukturierten
  Fragebogen, wörtlich in
  [`dec-0044-016-provenance.txt`](dec-0044-016-provenance.txt)
- **Anlass:** Architekt `Data-Riker-20260821T221000Z` beanspruchte `0044-04` bei
  `b098882fac` und stellte fest, dass die A1-Prüfung zur Branch-Zeit und die
  A2-Aufzeichnung von Reihenfolgeabweichungen **qualifizierende
  cross-item-Gates** sind: sie können Start, Validierung, Abnahme, Integration
  oder Abschluss anderer Arbeitseinheiten blockieren. `DEC-0044-006` deckt die
  neue Anweisung nicht ab. Gemeldet von `Data`, agent-inbox Thread
  `work-dispatch`, 2026-08-21T23:03:08Z.

### Betroffene Arbeitseinheiten und Gates

- **Arbeitseinheit:** `0044-04` (Feature-Breakdown-Prozessanweisung), mit
  Fortwirkung auf `0044-05` (Schemata/Matcher), `0044-06` (Bedarfsklassen) und
  `0044-08` (Feature-Integration).
- **Gate A1:** Prüfung der Integrierbarkeit unter der Zielpolicy **zum Zeitpunkt
  der Branch-Erstellung**.
- **Gate A2:** Aufzeichnung von Abweichungen von der geplanten
  Implementierungsreihenfolge.

### Entscheidung

**A1 — Vorabprüfung: ja, aber schlank.** Beim Anlegen eines Arbeits-Branches
wird einmal geprüft, ob die Arbeit unter der Policy des Integrationsziels
zurückführbar ist. Mindestevidenz ist **ein Satz im Vorgangsdatensatz**:
Ergebnis (passt / passt nicht) und woran es festgemacht wurde. Ein Werkzeuglauf
mit abgelegtem Ergebnis wird **nicht** verlangt.

> *Begründung des Managements:* Der teure Fall ist der, in dem jemand tagelang an
> etwas baut, das am Ende nicht zusammenpasst. Den fängt ein Satz beim Start ab.
> Ein voller Nachweis bremst jeden Arbeitsbeginn spürbar, ohne diesen Fall besser
> abzufangen.

**A2 — Reihenfolgeabweichung: nur bei Fremdbetroffenheit.** Eine Abweichung von
der geplanten Reihenfolge wird aufgezeichnet, **wenn sie die Arbeit einer anderen
Einheit blockiert oder deren Vertrag verändert**. Sonst nicht. Auslöser ist damit
derselbe cross-item-Prädikatstest, den `decision-record@v1` bereits definiert;
`0044-04` erfindet keinen zweiten.

> *Begründung des Managements:* Lückenlose Aufzeichnung erzeugt lange Notizen,
> die am Ende niemand liest. Sie soll dort greifen, wo sie jemand braucht.

**Worked Example: Feature `0043` (Berichtswesen/Build-Evidenz).** Die Anweisung
wird an `0043` erprobt, bevor sie allgemein gilt — laufend, überschaubar, mit
offenen Teilen, also ohne nennenswerten Zusatzaufwand. Entspricht dem Vorschlag
von `Data`, vorbehaltlich der von `Data` genannten Owner-/Provenance-Prüfung.

**Gegenlesen: ein von der Projektleitung instanziierter Architekt.** Die
Scope-Prüfung übernimmt ein Architekt, den die Projektleitung ansetzt und der
**nicht** an der Anweisung mitschreibt. `Data` prüft nicht die eigene Arbeit.

> *Begründung des Managements:* Die Anweisung formt jede künftige Planung; ein
> Denkfehler hier vererbt sich besonders weit.

### Was diese Entscheidung nicht tut

- Sie ersetzt **nicht** die Scope-Prüfung. Sie ist die Entscheidungsgrundlage,
  die `AGENTS.md` vor der ersten Mutation einer qualifizierenden Gate-Reichweite
  verlangt; die **zweite** Bedingung — Prüfung durch einen von der
  Implementierung unabhängigen Architekten — ist damit *beauftragt*, nicht
  erfüllt.
- Sie ist **keine** Autorisierung für `Data-Riker-20260821T221000Z`, die Policy
  zu schreiben. `Data` hat ausdrücklich darum gebeten, seinen Claim nicht als
  solche zu lesen; dem wird entsprochen.
- Sie ändert `DEC-0044-006` nicht und hebt keine bestehende Gate-Semantik auf.
- `0044-04` trägt weiterhin `Integration review: mandatory`. Dieser Checkpoint
  ist **nicht** gewaivt; der Waiver `DEC-0019-002` gilt ausschließlich für
  Feature `0019`.

### Konsequenzen

- `0044-04` bleibt `[p]`. Die gebundene Vorbereitung ist mit diesem Datensatz
  abgeschlossen; die Policy-Mutation bleibt gesperrt, bis die
  Architekten-Scope-Prüfung vorliegt.
- Die Projektleitung setzt den unabhängigen Architekten an und meldet das
  Ergebnis an `Data`.

---

## `DEC-0044-017` — Konforme Neufassung von `DEC-0044-016`: Gate-Umfang A1/A2 für `0044-04`

**Verhältnis zu `DEC-0044-016`:** Dieser Datensatz **korrigiert und ersetzt
inhaltlich** `DEC-0044-016`. `DEC-0044-016` bleibt append-only stehen und wird
nicht gelöscht; es war formal kein `decision-record@v1` und bot deshalb keinen
Ort, an dem die vorgeschriebene Architekten-Scope-Prüfung eingetragen werden
konnte (Befund des Architekten `Kathryn-Tom-20260822T004500Z`,
[`0044-04-gate-scope-review.md`](0044-04-gate-scope-review.md)). Wo beide
Datensätze voneinander abweichen, gilt **dieser**.

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-08-22T01:15:00Z`
- **Deciding identity:** `authority:repository-owner`
- **Role:** `Management`
- **Authority reference:** `task:0044-04`
- **Subject:** Reichweite und Mindestevidenz der beiden Gates der
  Feature-Breakdown-Prozessanweisung `0044-04` — A1 (Prüfung der
  Integrierbarkeit unter der Zielpolicy zum Zeitpunkt der Branch-Erstellung)
  und A2 (Aufzeichnung von Abweichungen der Implementierungsreihenfolge) —
  einschließlich des Verhaltens im Negativfall von A1 und der Auswahl des
  Erprobungsvorhabens.
- **Decision:**
  1. **A1 — schlank, mit Abbruchzweig.** Beim Anlegen eines Arbeits-Branches
     wird einmal geprüft, ob die Arbeit unter der Policy des Integrationsziels
     zurückführbar ist. Mindestevidenz ist **ein Satz im Vorgangsdatensatz**:
     Ergebnis (passt / passt nicht) und woran es festgemacht wurde. Ein
     Werkzeuglauf mit abgelegtem Ergebnis wird **nicht** verlangt.
  2. **A1-Negativfall — rollenbasierte Meldung, Arbeit läuft weiter.** Lautet
     das Ergebnis „passt nicht", wird der Befund **gemeldet, nicht nur
     notiert**: an einen **Integrator**, der bei Bedarf an einen
     **Projektleiter** eskaliert. Adressiert wird vorzugsweise, wer mit dem
     Vorgang befasst ist; ist diese Person nicht verfügbar, wird auf eine
     andere Vertretung **derselben Rolle** zurückgegriffen. Die Meldung ist
     rollenbasiert, nicht personengebunden — ein abwesender Einzelner darf das
     Gate nicht aushebeln.
  3. **A2 — nur bei Fremdbetroffenheit.** Eine Abweichung von der geplanten
     Reihenfolge wird aufgezeichnet, **wenn sie die Arbeit einer anderen
     Einheit blockiert oder deren Vertrag verändert**. Sonst nicht. Auslöser
     ist der kanonische `cross-item-blast-radius`-Prädikatstest aus
     [`decision-record@v1`](../pipeline/decision-record.md#2-wann-ein-datensatz-verpflichtend-ist);
     `0044-04` definiert kein zweites Prädikat.
  4. **Erprobung wird aufgeteilt.** **A1** wird an Task `0043-03` erprobt — dem
     einzigen Task in Feature `0043`, der dafür prospektiv frei ist. **A2** wird
     an `0043` **nicht** erprobt, weil dort keine erprobbare
     Reihenfolgeabweichung vorliegt; sie wird am **nächsten neu zerlegten
     Feature** erprobt. Die Anweisung darf für A2 erst dann als erprobt gelten.
  5. **Gegenlesen durch einen vom Management beauftragten Architekten.** Die
     Scope-Prüfung nach `AGENTS.md` erfolgt durch einen Architekten, den das
     Management beauftragt und den die Projektleitung in dessen Auftrag
     instanziiert; er schreibt die Anweisung nicht mit. Ausgeführt, siehe
     *Review participation*.
- **Technical justification:** A1 und A2 sind qualifizierende cross-item-Gates:
  ihr deklariertes Verhalten kann Start, Validierung, Abnahme, Integration oder
  Abschluss anderer Arbeitseinheiten blockieren. `DEC-0044-006` bezeichnet sich
  in seinem eigenen `CON-02` als reiner Verankerungsakt und deckt die neue
  Anweisung nicht ab; ein eigener Datensatz war daher verpflichtend. Das
  Satz-Minimum von A1 folgt demselben Handel wie `DEC-0044-008`/`DEC-0044-011`:
  aufzeichnen statt rekonstruieren, weil die vollständige Information nur zum
  Zeitpunkt der Handlung vorliegt. Ein Gate ohne Abbruchzweig ist jedoch keine
  Kontrolle, sondern eine Notiz — deshalb der rollenbasierte Meldeweg. Dass die
  Arbeit trotz Negativbefund beginnt, ist bewusst: der teure Schaden ist die
  spät entdeckte Fehlplanung, nicht der frühe Start; die Meldung macht sie ab
  Minute eins sichtbar.
- **Triggers:**
  - `cross-item-blast-radius`
- **Considered alternatives:**
  - **ALT-01:** A1 schlank (ein Satz), A2 nur bei Fremdbetroffenheit,
    Erprobung aufgeteilt
    - **Disposition:** `selected`
    - **Reason:** Fängt den teuren Fall (tagelange Arbeit auf falscher Basis)
      beim Start ab, ohne jeden Arbeitsbeginn mit einem Werkzeuglauf zu
      belasten; hält die A2-Aufzeichnung dort, wo sie jemand liest.
  - **ALT-02:** A1 mit vollem Werkzeugnachweis und abgelegtem Ergebnis
    - **Disposition:** `rejected`
    - **Reason:** Bremst jeden Arbeitsbeginn spürbar, ohne den Zielschaden
      besser abzufangen.
  - **ALT-03:** A2 zeichnet jede Reihenfolgeabweichung auf
    - **Disposition:** `rejected`
    - **Reason:** Erzeugt lange Notizen, die niemand liest; verlagert die
      Kontrolle von Wirkung auf Vollständigkeit.
  - **ALT-04:** Gar keine Vorabprüfung
    - **Disposition:** `rejected`
    - **Reason:** Probleme fallen erst beim Zusammenführen auf, dann teurer.
  - **ALT-05:** A1-Negativfall hält die Arbeit an, bis geklärt
    - **Disposition:** `rejected`
    - **Reason:** Blockiert eine arbeitsfähige Einheit, während auf eine
      Antwort gewartet wird; die Meldung erreicht dasselbe Ziel ohne
      Stillstand.
  - **ALT-06:** A1-Negativfall wird nur im Vorgang notiert
    - **Disposition:** `rejected`
    - **Reason:** Ohne aktive Meldung fällt der Befund erst auf, wenn jemand
      nachliest — möglicherweise nie.
  - **ALT-07:** Erprobung beider Regeln ausschließlich an Feature `0043`
    - **Disposition:** `rejected`
    - **Reason:** A2 ist dort nachweislich nicht erprobbar; die Anweisung
      wäre als erprobt ausgewiesen, ohne es für A2 zu sein.
- **Consequences:**
  - **CON-01:** `0044-04` bleibt `[p]`. Die Policy-Mutation ist ab diesem
    Datensatz **freigegeben**, da beide Bedingungen der
    Cross-item-gate-scope-review-Ausnahme nun erfüllt sind: der Datensatz hier
    und die Prüfung unter *Review participation*.
  - **CON-02:** Die Anweisung gilt für **A2 erst dann als erprobt**, wenn ein
    neu zerlegtes Feature sie durchlaufen hat. Bis dahin ist jede Aussage,
    `0044-04` sei vollständig erprobt, unzutreffend.
  - **CON-03:** Die 15 Auflagen des Architekten aus
    [`0044-04-gate-scope-review.md`](0044-04-gate-scope-review.md) bleiben
    verbindlich; sechs davon sind vor der ersten Policy-Mutation zu erfüllen.
  - **CON-04:** Der rollenbasierte Meldeweg setzt voraus, dass die Rollen
    Integrator und Projektleiter besetzt und über die agent-inbox erreichbar
    sind. Ist keine Vertretung erreichbar, ist das selbst ein meldepflichtiger
    Zustand und kein stiller Durchlauf.
  - **CON-05:** `0044-04` trägt weiterhin `Integration review: mandatory`. Der
    Waiver `DEC-0019-002` gilt ausschließlich für Feature `0019`.
- **Affected work units:**
  - `task:0044-04`
  - `task:0044-05`
  - `task:0044-06`
  - `task:0044-08`
  - `task:0043-03`
  - `feature:0043`
  - `feature:0044`
- **Affected gates:**
  - `task-start:0044-04`
  - `integration:0044-08`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:Kathryn-Tom-20260822T004500Z`
    - **Role:** `Architekt`
    - **Participation:** `reviewed`
    - **Position:** `supports-with-conditions`
    - **Note:** Unabhängige Scope-Prüfung nach `AGENTS.md`,
      Verdikt `scope-ok-mit-auflagen`, Bericht
      [`0044-04-gate-scope-review.md`](0044-04-gate-scope-review.md),
      Commit `35262eff2`. Bestätigt, dass das cross-item-Prädikat richtig
      angewandt ist und `DEC-0044-006` die Anweisung nicht abdeckt. Stellte den
      fehlenden A1-Abbruchzweig fest (hier durch Entscheidung 2 geschlossen),
      die Formnichtkonformität von `DEC-0044-016` (durch diesen Datensatz
      geschlossen), die Untauglichkeit von `0043` für A2 (durch Entscheidung 4
      geschlossen) sowie vier Abweichungen in der Rückübersetzung der
      Projektleitung aus dem Fragebogen. 15 Auflagen, sechs vor der ersten
      Policy-Mutation.
  - **PART-02:**
    - **Identity:** `agent:Data`
    - **Role:** `Integrator`
    - **Participation:** `consulted`
    - **Note:** Meldete die Gate-Qualifikation und verlangte Datensatz plus
      unabhängige Architektenprüfung vor jeder Policy-Mutation
      (agent-inbox, Thread `work-dispatch`, 2026-08-21T23:03:08Z). Bat
      ausdrücklich darum, den Claim von `Data-Riker-20260821T221000Z` nicht als
      Schreibautorisierung zu lesen; dem wird entsprochen.
- **Waiver:** `none`

### Korrektur der vier Übersetzungsabweichungen

Die Entscheidung wurde auf ausdrücklichen Wunsch des Managements über einen
Fragebogen in bewusst einfacher Sprache erhoben, ohne Bezeichner und ohne den
Begriff cross-item-Gate. Die Rückübersetzung nahm die Projektleitung vor. Der
Architekt hat sie geprüft und im Kern als redlich befunden, aber vier
Abweichungen benannt. Sie werden hier korrigiert und nicht relativiert:

1. **„Hauptprojekt" → „Integrationsziel".** Materielle Erweiterung: gefragt war
   nach `main`, aufgezeichnet wurde das jeweilige Integrationsziel. Der breitere
   Begriff wird **beibehalten**, weil ein Branch auch gegen ein Feature-Ziel
   integriert wird und die engere Lesart eine Lücke ließe — die Erweiterung wird
   hiermit aber als solche **offengelegt und ausdrücklich mitentschieden**.
2. **„die Arbeit verändert" → „deren Vertrag verändert".** Verengung. Der
   Vertragsbegriff wird beibehalten, weil er dem kanonischen Prädikat entspricht;
   die Verengung ist damit gewollt und nicht versehentlich.
3. **Gleichsetzung mit dem kanonischen Prädikat.** Diese Gleichsetzung war
   ungefragt und stand in `DEC-0044-016` indikativ statt als Entscheidung. Sie
   ist hier als Entscheidung 3 ausdrücklich getroffen.
4. **„ein Prüfer, den ich starte" → „von der Projektleitung instanziiert".** Die
   Regel verlangt einen **vom Management** beauftragten Architekten. Der
   Fragebogen ließ offen, dass „ich" in der Antwortoption die Projektleitung
   meinte, weil die Projektleitung die Option selbst so formuliert hatte. Der
   Sachverhalt: Das Management hat den Architekten **beauftragt**, die
   Projektleitung hat ihn in diesem Auftrag **instanziiert**. Entscheidung 5
   sagt das nun korrekt.

---

### Additive Korrektur zu `DEC-0044-017` — Vervollständigung der betroffenen Einheiten und Gates (Auflage A-02)

**Art:** append-only Korrektur. Der Text von `DEC-0044-017` bleibt unverändert
stehen; die Listen **Affected work units** und **Affected gates** dort sind
unvollständig und werden hier vollständig ersetzt. Wo beide voneinander
abweichen, gelten die Listen dieser Korrektur.

- **Recorded at:** `2026-08-22T10:30:00Z`
- **Deciding identity:** `agent:kathryn:projektleiter:0044-017-korrektur:20260822T103000Z`
- **Role:** `Projektleiter`
- **Authority reference:** Auflage **A-02** aus
  [`0044-04-gate-scope-review.md`](0044-04-gate-scope-review.md) (Architekt
  `Kathryn-Tom-20260822T004500Z`, Verdikt `scope-ok-mit-auflagen`, Commit
  `35262eff2`), deren Verbindlichkeit `DEC-0044-017` in `CON-03` selbst
  festschreibt.
- **Anlass:** Gemeldet von `Data` und `data-leah-20260822t092629z` (agent-inbox,
  Thread `0044-04`, 2026-08-22T09:26Z, 09:30Z und 09:46Z). `Data` hält die
  Policy-Mutation an `0044-04` bis zu dieser Korrektur an — zu Recht: der
  Datensatz erklärte alle 15 Auflagen für bindend, erfüllte A-02 aber nicht.
  Der Fehler liegt beim Aufzeichnenden, nicht beim Melder.

**Affected work units — vollständig:**

- `task:0044-04`
- `task:0044-05`
- `task:0044-06`
- `task:0044-07`
- `task:0044-08`
- `task:0043-03`
- `feature:0043`
- `feature:0044`
- `path:AGENTS.md`
- `path:docs/pipeline/process-roles.md`
- `repository:autodocs`

**Affected gates — vollständig:**

- `task-start:0044-04`
- `task-start:0043-03`
- `integration:0044`
- `integration:0044-08`
- `feature-closure:0044`

**Repositoryweite Startwirkung, ausdrücklich benannt:** Die Anweisung aus
`0044-04` erzeugt über Gate A1 eine Pflicht, die **jede künftige
Branch-Erstellung** im Repository betrifft — in der Syntax des Formats
`task-start:*`. `AGENTS.md` und `docs/pipeline/process-roles.md` sind
Autoritätsdateien nach `DEC-0044-012`; ihre Änderung wirkt auf alle Agenten,
nicht nur auf die Kette `0044-05/06/08`. Diese Reichweite war in
`DEC-0044-017` sachlich vorhanden, aber nicht als Einheit geführt.

**Nicht aufgenommen, mit Begründung:** `0044-12` und `0044-13` nennt die
Scope-Prüfung als *mögliche* Durchsetzungsorte für ein A1-Pflichtfeld, ohne
zwingende Betroffenheit (Bericht, Abschnitt 4, Punkt 4). Sie werden hier
**nicht** als betroffene Einheiten geführt, sind aber beim Schreiben der
Anweisung zu bedenken, damit keine dritte Mechanik neben Trailer-Konvention und
`reference-transaction`-Hook entsteht. Wer beim Schreiben feststellt, dass die
Anweisung dort doch eingreift, führt sie additiv nach.

**Unverändert:** Alle Entscheidungen 1–5 aus `DEC-0044-017`, sämtliche
`CON-01`…`CON-05`, die `Review participation` und die 15 Auflagen. Diese
Korrektur ergänzt Listen; sie ändert keine Entscheidung.

---

## Identifier-Reservierung 2026-08-22 — `DEC-0044-018` und `DEC-0044-019`

**Art:** append-only Reservierungsvermerk. Kein Entscheidungsdatensatz, keine Entscheidung.

`AGENTS.md` verlangt, dass ein `DEC-`-Bezeichner vor seiner Verwendung gegen
`main` geprüft wird, weil `main` der einzige Ort ist, an dem ein
Zuteilungspunkt überhaupt existieren kann. Genau diese Regel entstand, weil ein
auf einem Zweig entworfener Entscheidungsdatensatz eine Nummer belegte, die auf
`main` bereits vergeben war — zwei append-only Datensätze unter einer Kennung,
die dieselbe Frage gegenteilig beantworteten.

Hiermit sind reserviert, geprüft gegen `main` (höchste belegte Nummer war
`DEC-0044-017`):

| Kennung | Reserviert für | Anfordernde Instanz | Gegenstand laut Vorlage |
|---|---|---|---|
| `DEC-0044-018` | Task `0044-02` | Dispatcher `data`, vorbereitet durch `Data-Nora-20260822T150414Z` | Risiko-Integrationsverfahren: unabhängige Integrator-/QA-/Architekten-Sessions, Einstimmigkeit, befristete Policy-Aussetzung mit Umfang/Dauer/Wiederherstellungsnachweis, Eskalation bei Nicht-Einstimmigkeit über das bestehende `[u]`-Integrationsverdikt |
| `DEC-0044-019` | Task `0044-03` | Dispatcher `data` | Verbindliche ausführbare Testverpflichtung an verpflichtenden Checkpoints, proportional aus Architekturrisiken/Schnittstellen/Invarianten/externen Effekten abgeleitet; Nachweis nennt Kommando, Eingabe, Kandidat, Digest, Ergebnis; fehlende Automatisierung erfordert ausdrücklichen manuellen Rückfallpfad samt aufgezeichneter Lücke und Fail-/`[u]`-Weg, niemals ein stilles Bestehen |

**Was diese Reservierung nicht ist:** keine Genehmigung des Inhalts, keine
Scope-Prüfung, keine Abnahme. Beide Vorgänge erfüllen nach übereinstimmender
Einschätzung ihrer Vorbereiter das kanonische `cross-item-blast-radius`-Prädikat
und benötigen vor der qualifizierenden Mutation zusätzlich die unabhängige
Scope-Prüfung eines von Management instanziierten Architekten. Die Reservierung
verhindert lediglich, dass zwei Sessions dieselbe Nummer belegen.

**Verfällt** die Reservierung, wenn einer der beiden Vorgänge ohne
Entscheidungsdatensatz abgeschlossen wird: dann ist die Nummer hier ausdrücklich
als unbenutzt zu vermerken und wird **nicht** neu vergeben — eine Lücke in der
Nummernfolge ist harmlos, eine doppelt belegte Nummer nicht.

**Aufgezeichnet von:** Projektleiter `kathryn` (`DEC-ROLE-001`) auf Anforderung
von Dispatcher `data` (agent-inbox `1787411895011-243c3652`, 2026-08-22T15:18:15Z).

---

## Identifier-Reservierung 2026-08-22 — `DEC-0038-002`

**Art:** append-only Reservierungsvermerk. Kein Entscheidungsdatensatz, keine Entscheidung.

Geprüft gegen `main`; höchste belegte Nummer der `DEC-0038-`-Reihe war
`DEC-0038-001`.

| Kennung | Reserviert für | Anfordernde Instanz | Gegenstand laut Vorlage |
|---|---|---|---|
| `DEC-0038-002` | Task `0038-33` | Dispatcher `harry`; Architekt `Harry-Seven-20260822T153500Z`, Implementierer `Harry-Bashir-20260822T152700Z` | Behandlung der fünf bestehenden `AUTO010`-Befunde in `_src/tools/runner_transaction.py` gegenüber der geteilten Aggregatkontrolle `_src/tests/test_automation_safety.py` |

**Vorgesehener Pfad des Datensatzes:** `docs/dossiers/dec-0038-automation-safety-aggregate-control.md`.

**Was dieser Vermerk festhält, ohne die Entscheidung vorwegzunehmen:** Der
Architekt hat den Scope bereits unabhängig geprüft (Branch
`review-0038-33-scope-harry-seven-20260822T153500Z`, `966442b10`) und das
kanonische `cross-item-blast-radius`-Prädikat bejaht. Seine Feststellung —
die Kontrolle wurde am 2026-08-17 (`ec251f2a6`) eingeführt und **datiert allen
fünf Befunden vor**, die erst danach entstanden (`2e688ab6c`, `4231f93b2`,
`2d510d08e`, `b70238ad0`) — stützt die Lesart „veraltete Kontrolle", nicht
„Regression der fünf Operationen". Ob das zutrifft, entscheidet der
Datensatz, nicht diese Reservierung.

**Ausdrücklich festgehaltene Grenze aus der Architektenprüfung:** Eine
pauschale Datei- oder Regelausnahme ist unzulässig. Das zulässige Minimum ist
eine exakt geschlossene Allow-Set-Bindung an Zeile, Symbol **und** vollen
Hash, deren Gleichheit asserted wird; jeder neue `AUTO010` sowie `AUTO001`,
`AUTO002` und `AUTO009` bleiben verboten. Änderungen an Policy, Scanner oder
Laufzeit sind nicht gedeckt.

**Aufgezeichnet von:** Projektleiter `kathryn` (`DEC-ROLE-001`) auf Anforderung
von `Harry-Seven-20260822T153500Z` (agent-inbox `1787413040296-5846e0a5`) und
Dispatcher `harry` (`1787413514209-b4eba140`), 2026-08-22.
