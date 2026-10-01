# QA-Vorschlag: Prozessrollenmodell für Feature `0040-01`

**Rolle des Verfassers:** QA-Manager (Prozessqualität)
**Session:** `agent:claude:re-intake:20260818T003223Z-845170c0e4da`
**Autorität:** `DEC-0040-001` (begrenzter Autoritätsverzicht, Kunde, 2026-08-18)
**Status:** Vorschlag zur kritischen Bewertung. **Nicht normativ**, solange die
trilaterale Einigung nicht protokolliert und übernommen ist.
**Eingangsdokumente:** `docs/dossiers/re-intake-evidence-traceability-and-roles.md`
(`RQ-ROLE-01/02/04`, Befunde C und D, `DEC-0040-003`); `TODO.md` Task `0040-01`;
`AGENTS.md`; `SANDBOX.md`; `PRIVILEGED.md`; `docs/pipeline/task-acceptance.md`;
`docs/pipeline/branch-workflow.md`.

---

## 1. Zweck und Geltungsbereich

Dieses Modell regelt, **wer wofür verantwortlich ist** im Entwicklungsprozess
dieses Repositories. Es regelt **nicht**, was eine Session technisch ausführen
darf — das bleibt Sache der Fähigkeitsklassen in `SANDBOX.md`.

Es gilt für den **eigenen Prozess dieses Repos**. Es ist strikt getrennt von den
Produktdomänenrollen in `docs/pipeline/roles.md` (Kurator, KI-Entscheider,
Validator) und von der ASPICE-Bewertung eines ECU-Produkts in den Features
`0011`–`0032`. Alle Normverweise sind **Prozessunterstützung, keine bewertete
Capability**.

## 2. Grundsatz: zwei Achsen, ein Mapping

**Achse 1 — Fähigkeitsklasse.** Was eine Session ausführen darf: Shell, Git,
Netz, Anmeldedaten, Abnahmebefugnis. Bestand: `sandboxed/grunt`,
`lokal-nichtprivilegiert`, `lokal-privilegiert`.

**Achse 2 — Prozessrolle.** Wofür eine Session fachlich verantwortlich ist.
Neu, hier definiert.

Die Achsen sind **orthogonal**. Ein Architekt kann sandboxed sein; ein
privilegierter Agent kann Implementierer sein. Der zentrale Satz, der aus Befund
D folgt und den das Modell durchgängig tragen muss:

> **Privileg ist nicht Unabhängigkeit.** Befugnis sagt, was jemand *tun* kann.
> Unabhängigkeit sagt, wessen Arbeit jemand *beurteilen* darf.

Damit die Trennung nicht folgenlos bleibt (`DEC-0040-003`), gehört zu jeder
Rolle eine **Mindest-Fähigkeitsklasse** und eine Liste von
**Unvereinbarkeiten**.

## 3. Die sechs Rollen

### 3.1 Requirements Engineer (RE)

- **Zweck:** Eingehende Anforderungen aufnehmen, prüfen, analysieren, zerlegen.
- **Arbeitsprodukte:** Anforderungsdokument mit verbatim übernommener Quelle,
  stabile Anforderungs-IDs, Analysebefunde, offene Fragen, Rückverfolgbarkeit
  Anforderung ↔ Quelle ↔ Norm.
- **Darf allein entscheiden:** Zerlegung, IDs, Formulierung, welche Fragen an
  den Kunden gehen.
- **Darf nicht allein entscheiden:** den Zuschnitt der daraus folgenden Arbeit
  (Architekt), ob eine Anforderung angenommen wird (Management).
- **Kernpflicht:** die Kundenprämisse **hinterfragen**, nicht nur aufnehmen.
  Belegfall: Befunde A und C dieses Features entstanden ausschließlich dadurch.
- **ASPICE-Bezug (unterstützend):** SWE.1 / SYS.2.

### 3.2 Architekt

- **Zweck:** Ein Feature so zerlegen, dass Implementierer mit minimalem
  Eigenreasoning arbeiten können; Abnahmekriterien festlegen;
  Integrationsknoten benennen.
- **Arbeitsprodukte:** Feature-Zerlegung, Abnahmekriterien, Definition of Done,
  Vorbedingungsgraph, Integrationsknoten mit Begründung, No-Checkpoint-
  Begründung für nicht markierte Knoten.
- **Darf allein entscheiden:** Schnitt und Reihenfolge der Tasks,
  Abnahmekriterien, wo Integrationsprüfungen sitzen.
- **Darf nicht allein entscheiden:** eine Zuschnittsentscheidung mit
  Blockadewirkung über das Feature hinaus ohne Entscheidungsdatensatz
  (`RQ-DEC-05`); Abnahme eigener Zerlegung.
- **ASPICE-Bezug (unterstützend):** SWE.2 / SYS.3.

### 3.3 Implementierer

- **Zweck:** Das Arbeitsprodukt herstellen und validieren.
- **Arbeitsprodukte:** Deliverable, Tests, Validierungsevidenz, Claim, `REF`.
- **Darf allein entscheiden:** technische Umsetzung innerhalb des deklarierten
  Schreibbereichs; Backlog-Reparatur nach den bestehenden Regeln.
- **Darf nicht allein entscheiden:** Abnahme eigener Arbeit; Erweiterung des
  Schreibbereichs; Einbau eines blockierenden Tors ohne Entscheidungsdatensatz.
- **ASPICE-Bezug (unterstützend):** SWE.3.

### 3.4 Integrator

- **Zweck:** Arbeit nach oben zusammenführen, an Integrationsknoten prüfen,
  Abnahme erteilen oder `[u]`-Verdikt setzen.
- **Arbeitsprodukte:** Merge, Reviewbefunde, `Acceptance: ✓` oder
  `[u]`-Integrationsverdikt, Reconciliation der Claim-Dateien.
- **Darf allein entscheiden:** ob ein Knoten die Prüfung besteht.
- **Darf nicht allein entscheiden:** ein eigenes `[u]`-Verdikt auflösen; einen
  Integrationsknoten überspringen.
- **ASPICE-Bezug (unterstützend):** SWE.5 / SYS.4.

### 3.5 QA-Manager

- **Zweck:** Prozessqualität. Prüft, ob **nach dem Prozess gearbeitet wurde** —
  nicht, ob das Produkt fachlich gut ist.
- **Arbeitsprodukte:** Prozessdefinitionen, Prozessbefunde, Eskalationen.
- **Darf allein entscheiden:** ob ein Prozessverstoß vorliegt; ob eskaliert
  wird.
- **Darf nicht allein entscheiden:** Produktinhalte; Abnahme von Arbeitsprodukten
  (das ist der Integrator); Aufhebung einer Prozessregel (das ist Management).
- **Kernmerkmal:** **Eskalationsrecht ohne Weisungsbindung.** Der QA-Manager
  muss einen Befund an das Management melden können, auch wenn Architekt,
  Implementierer und Integrator anderer Meinung sind.
- **ASPICE-Bezug (unterstützend):** SUP.1, insbesondere die dort geforderte
  Unabhängigkeit.

### 3.6 Management

- **Zweck:** Autorität oberhalb des Prozesses. Rollen zuweisen, Verzichte
  erteilen, `[u]` auflösen, Prozess ändern.
- **Träger:** der aktuelle Benutzer oder eine registrierte Autorität. **Nie ein
  Agent.**
- **Bestand:** bereits im `TODO.md`-Header verankert („Management may change or
  circumvent the process"); hier nur als Rolle sichtbar gemacht.

## 4. Mapping: Rolle → Fähigkeitsklasse

| Rolle | Mindest-Fähigkeitsklasse | Begründung |
|---|---|---|
| Requirements Engineer | sandboxed/grunt | Liest und schreibt Dokumente; braucht keine Ausführungsrechte. |
| Architekt | sandboxed/grunt | Erzeugt Backlog- und Entwurfstext; keine Ausführungsrechte nötig. |
| Implementierer | aufgabenabhängig | Ergibt sich aus dem Schreib- und Ausführungsbereich der Task, nicht aus der Rolle. |
| Integrator | **lokal-privilegiert** | Merges über Integrationsknoten, `Acceptance: ✓`, `DONE.md` sind privilegiert (Bestand `branch-workflow.md`). |
| QA-Manager | **lokal-nichtprivilegiert genügt** | Braucht Lesezugriff auf alles und ein Meldeziel — **keine** Schreibprivilegien. Privileg würde die Unabhängigkeit nicht erhöhen, aber die Versuchung schaffen, Befunde selbst zu „reparieren" statt zu melden. |
| Management | außerhalb des Modells | Menschliche Autorität; keine Fähigkeitsklasse. |

**Wesentlicher Punkt:** Der QA-Manager ist die einzige Rolle, deren Wirksamkeit
**sinkt**, wenn man ihr mehr Rechte gibt. Das ist die praktische Konsequenz aus
„Privileg ist nicht Unabhängigkeit".

## 5. Unvereinbarkeiten: Trennungskern und Tailoring

Dieses Projekt wird von einem Menschen mit Agenten betrieben. Ein Modell, das
fünf getrennte Sessions je Feature verlangt, wäre unwirtschaftlich und würde
umgangen. Deshalb wird unterschieden zwischen einem **harten Trennungskern**
und **tailorbaren** Trennungen.

### 5.1 Trennungskern — nicht verhandelbar, kein Verzicht möglich

> **TK-1: Wer ein Arbeitsprodukt herstellt, erteilt ihm an einem
> Integrationsknoten keine Abnahme.**

Das ist die einzige Trennung ohne Ausnahme. Begründung: Sie ist die
Mindestbedingung dafür, dass Abnahme überhaupt eine Aussage trifft. Fällt sie,
ist jede weitere Trennung Kosmetik. Sie deckt sich mit der bestehenden Regel in
`AGENTS.md` (Selbstabnahme verboten) und mit SUP.1.

**Konsequenz für den laufenden Fall:** `DEC-0040-001` erteilt dieser Session
Vollprivileg. TK-1 bleibt davon **unberührt** — ein Autoritätsverzicht des
Managements kann TK-1 nicht aufheben, weil TK-1 keine Befugnisfrage ist, sondern
eine Aussagefrage. Für `0040-09` bedeutet das: die Integrationsprüfung dieses
Features braucht eine andere Instanz als diese Session, oder das Ergebnis trägt
den Vermerk, dass es keine unabhängige Abnahme ist.

### 5.2 Tailorbare Trennungen — Zusammenlegung mit Entscheidungsdatensatz

| Trennung | Regelfall | Zusammenlegung erlaubt, wenn … |
|---|---|---|
| RE ≠ Architekt | getrennt empfohlen | … Entscheidungsdatensatz vorliegt. Zusammenlegung ist in der Praxis üblich und risikoarm. |
| Architekt ≠ Implementierer | getrennt | … der Task keinen Integrationsknoten trägt **und** ein Datensatz vorliegt. |
| QA-Manager ≠ Implementierer desselben Gegenstands | getrennt | **nie** für denselben Gegenstand; für verschiedene Gegenstände frei. |
| Integrator ≠ Implementierer | siehe TK-1 | nicht tailorbar, soweit TK-1 reicht. |

Ein Tailoring ohne Datensatz ist ein Prozessverstoß, kein Kavaliersdelikt: Es
löscht die Spur, an der später erkennbar wäre, wessen Urteil wie unabhängig war.

## 6. Rollenzuweisung

1. Eine Session **deklariert** ihre Prozessrolle im Claim (`process_role`),
   zusätzlich zur Fähigkeitsklasse.
2. Die Rollen **RE, Architekt, Implementierer** darf eine Session sich aus dem
   Task-Zuschnitt selbst zuweisen.
3. Die Rollen **Integrator und QA-Manager** erfordern eine **ausdrückliche
   Zuweisung durch das Management**. Das entspricht der bestehenden Regel, dass
   eine Abnahmeprüfung nur auf ausdrückliche Zuweisung beginnt.
4. Wechselt eine Session die Rolle, wird der Wechsel im Claim vermerkt.
   Ein Rollenwechsel hebt TK-1 nicht auf: Wer implementiert hat, bleibt für
   diesen Gegenstand Implementierer.

## 7. Was dieser Vorschlag bewusst nicht tut

- Er schafft **keine neuen Fähigkeitsklassen**. Die drei bestehenden bleiben.
- Er ändert **keine** Marker-, Abnahme- oder Merge-Semantik.
- Er verlangt **keine** zusätzlichen Sessions pro Feature — Abschnitt 5.2 ist
  ausdrücklich dafür da, das zu vermeiden.
- Er behauptet **keine** ASPICE-Konformität.

## 8. Punkte, an denen ich Widerspruch erwarte

Offen benannt, damit die Bewertung sie nicht erst suchen muss:

- **P1:** TK-1 macht `0040-09` für diese Session unmöglich sauber abzuschließen.
  Das ist beabsichtigt, aber es kostet.
- **P2:** Sechs Rollen sind für ein Ein-Personen-Projekt womöglich zu viele.
  Verteidigung: Abschnitt 5.2 senkt die Kosten, nicht die Rollenzahl. Gegenfrage
  an die Bewertung: Wäre eine kleinere Rollenzahl ehrlicher?
- **P3:** Die Mindest-Fähigkeitsklasse „nichtprivilegiert" für den QA-Manager
  könnte in der Praxis bedeuten, dass er Befunde nicht selbst beheben darf und
  damit Reibung erzeugt. Das ist gewollt, aber diskutabel.
- **P4:** Der Nutzen der Rollen ist erst messbar, wenn der Prozess läuft. Bis
  dahin sind sie Kosten ohne belegten Ertrag.
