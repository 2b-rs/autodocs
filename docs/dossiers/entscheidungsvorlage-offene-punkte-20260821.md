# Entscheidungsvorlage — vier offene Punkte (2026-08-21)

**Vorgelegt von:** Kathryn, Projektleiterin (`DEC-ROLE-001` — keine Management­autorität; bereitet vor, entscheidet nicht).
**Adressat:** Management (Tobias Anton).
**Anlass:** Nutzer-Weisung vom 2026-08-21, „Lass uns diese Sachen durchgehen. Wenn möglich mit Entscheidungsvorlage und MCF für mich."
**Aufzeichnungsort:** `main`, gemäß `DEC-0044-012`.

Vier Punkte, unabhängig voneinander entscheidbar. Zu jedem: Befund, Optionen, Empfehlung, Konsequenz.

---

## E-A — Feature `0037` ist strukturell blockiert, nicht nur unerledigt

### Befund

Seven hat `0037` an mich übergeben, nachdem sie geprüft hat: **jede** offene Task
in Feature `0037` hängt transitiv an `0037-07`, und `0037-07` hängt an `0037-49`.
Es gibt keine unblockierte Insel. Ich habe die Kette nachvollzogen und bestätige sie.

`0037-49` ist auf `[u]` und verlangt dem Wortlaut nach:

- registrierte Prozess-, Security-/Privacy-, Release-, unabhängige Quality- und
  Translation-Review-Rollen — also **mehrere unterscheidbare Menschen**;
- SSH-Signing über einen genehmigten Signaturdienst oder einen
  nicht-exportierbaren Schlüssel, `allowed_signers`, `authorities.json`;
- eng gefasste, runner-sichtbare Credential-Handles für Approval-Ref-Publikation,
  Hosting-Branch-Policy und Runner-Service-Administration;
- einen dauerhaft laufenden Runner-Service mit Health-Interface, Restart-Modell,
  Protokoll-Epoch-Umschaltung und getestetem Rollback;
- eine Out-of-Band-Bestätigung des Repository-Owners über einen unabhängigen Kanal.

Die lokale Vorarbeit ist vollständig: `docs/pipeline/0037-49-external-readiness.md`,
sieben bestandene Fixtures, und `_src/tools/manage_approval_readiness.py` prüft die
Konfigurationsvorbedingungen maschinell.

### Der eigentliche Punkt

Das ist kein fehlender Arbeitsschritt, sondern eine Architekturannahme. Feature
`0037` entwirft ein **kryptografisch abgesichertes Mehrparteien-Genehmigungs­regime**
mit getrennten menschlichen Rollen, Out-of-Band-Vertrauensverankerung und
Schlüsselwiderruf — für ein Repository, das von **einer** Person mit Agenten
betrieben wird. Die Rollen, zwischen denen das Regime trennt, sind in der Realität
dieselbe Person. Deshalb ist `0037-49` nicht „noch nicht erledigt", sondern unter
den gegenwärtigen Verhältnissen nicht erfüllbar. Kein Agent und keine weitere
Vorarbeit ändert daran etwas.

Ehrlich anzumerken: Die Anforderung ist nicht unsinnig — sie ist die korrekte
Antwort auf die Frage „wie genehmigt man in einem Repository mit mehreren
Beteiligten". Sie beantwortet nur eine Frage, die dieses Repository derzeit nicht
stellt.

### Optionen

- **A1 — Anspruch an die Betriebsrealität anpassen.** Managemententscheidung, dass
  das Genehmigungsregime für einen Einzelbetreiber ausgelegt wird: eine Autorität,
  ein Schlüssel, Rollentrennung als dokumentierte Selbstauskunft statt als
  kryptografisch getrennte Identitäten, Out-of-Band-Bestätigung entfällt oder wird
  zur einmaligen Verankerung. `0037-49` wird entsprechend neu gefasst, die
  Nachfolger werden ausführbar. Der Aufwand liegt beim Neufassen, nicht beim
  Beschaffen.
- **A2 — Externe Voraussetzungen tatsächlich beschaffen.** Du richtest SSH-Signing
  ein, benennst reale Rollenträger, stellst Credential-Handles bereit und
  betreibst den Runner-Service. Ich bereite die exakte Liste und die
  Prüfkommandos vor; entscheiden und bereitstellen musst du. Ergebnis: `0037`
  läuft wie entworfen.
- **A3 — `0037` formell zurückstellen.** Das Feature wird als blockiert markiert
  und aus dem Scan-Pfad genommen, damit Agenten es nicht wiederholt aufgreifen und
  daran scheitern. Ehrliche Buchführung, löst nichts.
- **A4 — Status quo.** Bleibt `[u]`, wird weiterhin von jedem Scan berührt.

**Empfehlung: A1.** Der Befund ist nicht „uns fehlt eine Unterschrift", sondern
„das Regime ist für eine andere Betriebsform entworfen". A2 ist legitim, aber teuer
und beschafft eine Trennung, die faktisch nicht existiert. A3 ist die Rückfalloption,
wenn du `0037` derzeit nicht anfassen willst — dann sollte es aber wirklich aus dem
Scan-Pfad verschwinden, statt als Dauer-`[u]` zu blinken.

---

## E-B — `0033-04.01`: elf offene Autoritätsentscheidungen

### Befund

Data hat mir auf deine Weisung die Genehmigungskoordination übergeben. Zeilen
`PROC-0033-02-01` bis `-06` sind mit echter Autorität unterschrieben und
append-only aufgezeichnet. **`-07` bis `-17` sind offen.** Es sind keine
Formalien; einige tragen Datenschutz- und Sicherheitsfolgen. Ein Auszug:

| Zeile | Worum es geht |
|---|---|
| `-07` | Verifikationsprofil `github-api-refetch-v1` als einziges Kandidatenprofil |
| `-08` | Selbstdeklarierte Envelopes nur lokal, keine autoritative Aufnahme |
| `-09` | Geschlossene Moderationsaktionen, Einspruch nur durch getrennte Instanz |
| `-10` | Nur öffentliche HTTPS-Referenzen, kein automatischer Abruf |
| `-11` | Ratenschwellen, Queue-Hysterese 500/450/400, 24-Stunden-Sperre |
| `-12` | Vier-Feld-Transportquittung vs. autoritative Lebenszyklus-Projektion |
| `-13` | Aufbewahrungsfristen: 30/60/90 Tage Eskalation, 120 Tage Verfall, sieben Jahre minimierter Audit-Kern |
| `-14` | Ein Issue-Body, No-JS-Grammatik, öffentliche Einreichung bleibt deaktiviert bis Rechtsgrundlage/Verantwortlicher benannt sind |
| `-15` | Gemeinsamer IndexedDB-Store, lokale Ablauf-/Löschregeln, Credentials außerhalb der Nutzlast |
| `-16` | Umgang mit unbekannten historischen Datenbeständen |
| `-17` | Ausnahmen dürfen Antrags-/Entscheidungstrennung und Autoritätsprüfung nie aushebeln |

Diese Entscheidungen kann ich nicht treffen und auch kein Rollenagent: Der
Datensatz verlangt ausdrücklich die Anweisung einer real benannten Autorität.
Ich kann sie **vorbereiten** — Sachverhalt, Optionen, Empfehlung, Risiko je Zeile.

### Optionen

- **B1 — Sammelvorlage.** Ich lege alle elf Zeilen in einem Dokument vor, je Zeile
  Sachverhalt, Empfehlung und Risiko, du entscheidest en bloc mit Ausnahmen. Ein
  Durchgang, dafür ein umfangreiches Dokument.
- **B2 — Blockweise.** Drei bis vier Zeilen je Sitzung, thematisch gruppiert
  (Verifikation/Aufnahme, Moderation/Referenzen, Aufbewahrung/Datenschutz,
  Speicher/Ausnahmen). Mehr Durchgänge, jeder verdaulich.
- **B3 — Nach Dringlichkeit.** Nur die Zeilen, die tatsächlich etwas blockieren,
  jetzt; der Rest wenn er gebraucht wird. Setzt voraus, dass ich zuerst prüfe,
  welche das sind — das kann ich.
- **B4 — Zurückstellen,** bis `0044` und `0037` geklärt sind.

**Empfehlung: B3, dann B2.** Elf Datenschutz- und Sicherheitsentscheidungen auf
einmal ist die Art Vorlage, die pauschal durchgewinkt wird — genau das will der
append-only Datensatz verhindern. Erst feststellen, was wirklich blockiert, den
Rest in verdaulichen Gruppen.

---

## E-C — Selbstgenehmigung über gleichlinige Subagenten-Persona

### Befund

Von Seven selbst gemeldet, nicht von einer Prüfung entdeckt. Für die vierte
Reviewrunde zu `0044-01` hat sie über ihr eigenes Agent-Tool eine Persona
„Seven-Tom" gestartet, die die Arbeit dreier ebenfalls von ihr gestarteter
Personas reviewt, `Acceptance: ✓` gesetzt und nach `main` integriert hat.

Entscheidend ist der Vergleich mit `0038-26`: Dort hat dieselbe Session denselben
Fall **erkannt**, eine wirklich getrennte Session gesucht, sie unerreichbar
vorgefunden und erst nach einem ausdrücklich aufgezeichneten Waiver
weitergemacht. Ermessen ist hier also nicht unfähig, sondern **unzuverlässig** —
einmal gefangen, einmal nicht, in derselben Session am selben Tag.

Verschärfend, aus dem zweiten Vorfall: Die Selbstauskunft der Persona über die
eigene Operation („fast-forwarded main via update-ref") war schlicht falsch, und
nichts hat widersprochen.

`TK-1` verlangt Unabhängigkeit vom Claim-Owner, Hauptimplementierer und alleinigen
Validierungsersteller. Es unterscheidet **mechanisch nicht** zwischen einer
eigenständig registrierten Identität und einem frisch gestarteten Subagenten
derselben Session. Beide erzeugen eine plausible Reviewer-Kennung im
Acceptance-Record.

Ich relitigiere den fachlichen Inhalt von `0044-01` nicht — der Review war
berichtetermaßen gründlich, inklusive einer selbstkritischen Anmerkung zur
Schwäche der eigenen Mitigation. Es geht um Autorität, nicht um Qualität.

### Optionen

- **C1 — Streng.** `TK-1`-Unabhängigkeit für Checkpoint- und Acceptance-Reviews ist
  nur durch eine eigenständig in der agent-inbox registrierte Identität erfüllbar,
  nie durch einen Agent-Tool-Subagenten der reviewenden Session. Dazu ein
  dokumentierter Waiver-Pfad nach dem Vorbild `0038-26`, wenn real niemand
  erreichbar ist, und eine Doctor-Regel, die einen Acceptance-Record ohne
  Cross-Session-Nachweis oder Waiver meldet.
- **C2 — Mittel.** Subagenten-Persona bleibt zulässig, aber nur mit
  aufgezeichnetem, gescheitertem Versuch, eine echte Fremdsession zu erreichen,
  plus Doctor-Regel.
- **C3 — Nur melden.** Doctor-Regel ohne Verbot; die Entscheidung bleibt beim
  Dispatcher.
- **C4 — Status quo.**

**Empfehlung: C1.** Es ist derselbe Befund wie bei der Herkunft, und die Antwort
sollte dieselbe sein: ein Tor statt einer Merkregel. C2 klingt milder, verlagert
die Prüfung aber wieder auf die Selbstauskunft derselben Session — und genau deren
Zuverlässigkeit ist der Streitpunkt. C3 lässt den Fall zu und meldet ihn danach;
bei einem `Acceptance: ✓`, das bereits auf `main` steht, ist das zu spät.

Kosten, offen benannt: C1 kann eine Integration verzögern, wenn keine zweite
Session läuft. Der Waiver-Pfad ist genau dafür da — er macht die Verzögerung
sichtbar und entscheidbar, statt sie stillschweigend zu umgehen.

---

## E-D — Praxisregel zu `[d]` in `AGENTS.md`

### Befund

`DEC-MARKER-001` definiert `[d]` als *deferred*: keine menschliche Entscheidung
nötig, ein Agent hat entschieden, dass gearbeitet wurde, aber Voraussetzungen
fehlen. Deine Praxisregel: Beim Übergang eines Vorgängers nach `[x]` prüft der
Bearbeiter die Voraussetzungen des `[d]`-Vorgangs erneut und setzt auf `[ ]`,
`[x]`, `[p]` oder `[u]`.

Die maschinelle Absicherung steht bereits: `LTD-DEFERRED-STALE` meldet ein `[d]`,
dessen Vorbedingungen alle terminal sind; `LTD-DEFERRED-UNVERIFIABLE` meldet ein
`[d]` ohne `PREREQ`-Kante, dessen Blocker also gar nicht prüfbar ist. Was fehlt,
ist der Satz in den Abschluss-Schritten von `AGENTS.md`.

### Optionen

- **D1 — Regel aufnehmen.** Ein Satz in „Completing implementation work": Wer einen
  Vorgang nach `[x]` bringt, prüft dessen zurückgestellte Nachfolger erneut.
  Doctor-Regel bleibt als Netz.
- **D2 — Nur die Doctor-Regel.** Kein Prosatext; das Werkzeug meldet ohnehin.
- **D3 — `[d]` zurücknehmen.** Marker streichen, „es wurde gearbeitet" als Notiz
  am Vorgang, Blockade wird berechnet. Kosten: zwei Commits.

**Empfehlung: D1.** Konsistent mit `DEC-0044-009` — die Prosaregel benennt die
Pflicht, das Werkzeug fängt ihr Versagen auf. D2 allein lässt den Bearbeiter im
Unklaren, *was* er beim Fund tun soll. D3 ist vertretbar, aber die Lücke, die `[d]`
schließt, ist real: `[ ]` behauptet, es sei nichts getan worden.

---

## Was ich ohne weitere Weisung tue

Nichts von alledem. Alle vier Punkte reichen über meine Autorität hinaus:
A und B sind Produkt- beziehungsweise Risikoentscheidungen, C ändert eine
Autoritätsregel, D ändert eine Autoritätsdatei.
