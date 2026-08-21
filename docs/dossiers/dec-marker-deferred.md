# `DEC-MARKER-001` — `[d]` (deferred) wird ein definierter Implementierungsmarker

**Autorität:** Management (aktueller User), Entscheidung vom 2026-08-21.
**Protokollant:** Projektleiter Kathryn
(`agent:kathryn:projektleiter:branching-strategie:20260821T090000Z`,
`unprivileged`) — protokolliert, entscheidet nicht (`DEC-ROLE-001`).
**Betrifft:** die Marker-Legende im Kopf von `TODO.md` (Vertrag),
`_src/tools/legacy_task_doctor.py`, deren Fixtures.
**Vorgeschichte:** `4dc9d9166` (2026-08-16, User führt `[d]` auf `0037-49` ein),
`58a5b5f32` und Sevens Reparaturnotiz unter `0037-49` (Korrektur auf `[u]`,
weil `[d]` im Vertrag nicht definiert war).

## Entscheidung

`[d]` — **deferred** — wird als Implementierungsmarker definiert:

> Es ist **keine menschliche Entscheidung** erforderlich. Ein Agent hat
> entschieden, dass an dem Ticket gearbeitet wurde, aktuell aber nicht
> weitergearbeitet werden kann, weil Voraussetzungen für die Arbeit nicht
> erfüllt sind.

**Praxisregel:** Bei Abschluss eines Vorgängers — also dessen Übergang nach
`[x]` — prüft der Bearbeiter die Voraussetzungen des `[d]`-Tickets erneut und
setzt es anschließend auf `[ ]`, `[x]`, `[p]` oder `[u]`.

**Nebenläufigkeit ausdrücklich toleriert:** Ohne Locking können sich zwei
Agenten dabei in die Quere kommen. Das ist hingenommen, weil man auf ein
`[d]`-Ticket jederzeit wieder draufschauen kann.

## Fachliche Rechtfertigung

Die Marker-Legende kannte bisher keinen Zustand für „begonnen, aber blockiert,
ohne dass ein Mensch gebraucht wird". Die verfügbaren Marker erzwangen eine
falsche Aussage: `[p]` behauptet laufende Arbeit, `[ ]` verwirft die geleistete
Arbeit, und `[u]` behauptet eine erforderliche menschliche Entscheidung. Genau
diese Fehlzuordnung ist real eingetreten — `0037-49` trug `[d]`, wurde als
undefiniert erkannt und auf `[u]` korrigiert; formal richtig gegen den Vertrag,
aber semantisch eine andere Aussage als die beabsichtigte.

Die Unterscheidung zu `[u]` ist der Kern: **`[u]` heißt, ein Mensch ist die
nächste Handlung; `[d]` heißt ausdrücklich, dass er es nicht ist.** Das hält den
`[u]`-Eskalationspfad frei von Blockaden, die sich von selbst auflösen, sobald
ein Vorgänger terminal wird.

Die tolerierte Nebenläufigkeit ist bewusst gewählt: Ein Locking-Mechanismus
wäre teurer als der Schaden. Der schlimmste Fall ist doppelte Prüfarbeit an
einem Ticket, das ohnehin jederzeit erneut angesehen werden kann.

## Konsequenzen

- **Vertrag:** `[d]` steht in der Marker-Legende von `TODO.md`.
- **Werkzeug:** `legacy_task_doctor.py` erkennt `d` als gültigen Marker
  (`VALID_MARKERS`); `LTD-MARKER-UNDEFINED` wird für `[d]` nicht mehr gemeldet.
  Das betrifft auch Claim-Dateien mit `state: [d]` — etwa
  `TODO-perplexity-0037-49-20260816-1447.md`, die dadurch wieder vertragskonform
  ist.
- **Fixtures:** Der historische Testfall `marker-and-refs` benutzte `[d]` als
  Beispiel eines undefinierten Markers und wurde auf `[z]` umgestellt, damit
  `LTD-MARKER-UNDEFINED` weiterhin abgedeckt bleibt. 54/54 Tests grün.
- **Neue Pflicht bei Abschluss:** Wer einen Vorgänger auf `[x]` setzt, prüft
  dessen `[d]`-Nachfolger erneut. Das ist eine Handlungspflicht, die aus dieser
  Entscheidung folgt und in die Abschluss-Schritte von `AGENTS.md` gehört —
  siehe offener Punkt unten.

## Nicht entschieden

- **`0037-49` bleibt `[u]`.** Unter der neuen Definition wäre `[d]` dort
  trotzdem falsch: Der verbliebene Blocker ist die externe menschliche
  Autorisierung, also genau der `[u]`-Fall. Sevens Korrektur bleibt im Ergebnis
  richtig, wenn auch die ursprüngliche Begründung („undefinierter Marker") durch
  diese Entscheidung überholt ist.
- **Rückwirkende Neubewertung** anderer Tickets findet nicht statt.

## Offener Punkt

Die Praxisregel ist bisher nur hier und in der Legende festgehalten. Sie gehört
zusätzlich in die Abschluss-Schritte von `AGENTS.md` („Completing implementation
work"), damit sie am Ort ihrer Anwendung steht und nicht nur im Vertragskopf.
Nicht in dieser Änderung enthalten, weil `AGENTS.md` eine Autoritätsdatei mit
eigener Reichweite ist.

## Provenance

Auslösender User-Prompt, wörtlich:

> Richtig, "d" bedeutet letztlich, dass keine menschliche Entscheidung nötig
> ist, dass aber ein Agent entschieden hat, dass an dem Ticket gearbeitet
> wurde, aber aktuell nicht weitergearbeitet werden kann, weil Voraussetzungen
> für die Arbeit nicht erfüllt sind. Für die Praxis bedeutet es, dass bei
> Abschluss eines Vorgängers (also dessen übergang nach [x]) der Bearbeiter die
> Voraussetzungen des [d] tickets erneut prüfen und es dann entsprechend auf
> [ ], [x], [p] oder [u] setzen soll. Hierbei können sich ohne Locking
> natürlich zwei Agenten in die Quere kommen, das ist aber nicht so schlimm,
> weil man auf ein [d] ticket ja jederzeit wieder draufschauen kann.

Vorangegangen war die Feststellung, dass `[d]` nie in der Legende stand, sowie
die Frage des Users: „[d] war deferred, oder? Ich hatte das irgendwann mal
festgelegt."
