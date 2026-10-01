# Rollen

Quelle: `_src/SPEC_BUILD_PROCESS.md` (Abschnitt "Rollen"), ergänzt um Rollen aus
`curation_flags.py`, `review_flags.py`, `review_ingest.py`, `ai_workflow.py`.

| Rolle | Beschreibung | Implementiert? | Belege |
|---|---|---|---|
| **Werkzeug** (`tool`) | `spec_scrape.py` und seine Extraktions-Backends (`pypdf`, `builtin`, optional `mupdf`). Führt Extraktion, Vergleich und automatisches Schreiben aus (z. B. `upstream --rebuild`). | Ja — lauffähiges CLI | `SPEC_BUILD_PROCESS.md`; `spec_scrape.py` |
| **Kurator** (`curator`) | Mensch, trifft die letzte Entscheidung bei Grenzfällen, Freigaben und Kurationsanfragen. Im Code auch "Person, die die Extraktionsskripte betreibt" genannt. | Ja — durch manuelle CLI-Aufrufe (`--apply`, `complete_flag()`) | `SPEC_BUILD_PROCESS.md`; `curation_flags.py`; `curation_ingest.py` |
| **KI-Entscheider** (`ai`, Status `valid/ai-decided`) | Schlägt Werte für strittige Extraktionsfälle vor (`invalid/to-be-confirmed`), mit Rationale und Confidence. Entscheidet nur über *Extraktionswahrheit*, nie über Normtext. | Nur als Prozess/Schema beschrieben — kein eigenständiges CLI-Tool gefunden, das "Phase 3" automatisiert; das Statusfeld `valid/ai-decided` existiert im Schema | `SPEC_BUILD_PROCESS.md` Phase 3 |
| **KI-Extraktor** | Liest informelle Dokumente (Prosa, Doku, Beispiele, Code) und liefert Evidenz je Record; kann neue Elemente als `hypothesized/unconfirmed` vorschlagen. | Nur als Prozess beschrieben (Phase 5); kein dediziertes CLI gefunden, nur Datenstruktur (`upstream_evidence.py` persistiert *rohe* Beobachtungen, nicht dasselbe wie "informelle Evidenz") | `SPEC_BUILD_PROCESS.md` Phase 5 |
| **Validator** | Prüft Statusfelder, Traceability und Konsistenz vor Freigabe/Publikation. Konkret abgebildet durch `spec_scrape.py trace-check` (Konsistenzprüfung Record ↔ Traceability-Tabellen) und `validate.py` (HTML-Baum-Qualität). | Teilweise — `trace-check` ist implementiert; ein Gesamt-"Validator" für das volle Statusmodell (Phase 6, Punkt 1) ist nicht als ein einzelnes Tool erkennbar | `SPEC_BUILD_PROCESS.md` Phase 6; `spec_scrape.py trace-check`; `_src/validate.py` |
| **KI-Agent (Review/Kuration)** | Übernimmt atomar ein offenes Flag aus `spec/review-queue/` oder `spec/curation-queue/`, schlägt eine konkrete, belegte Änderung vor (Diff oder `RESIDUAL`-Eintrag) und legt sie als Review/PR vor. **Wendet nichts selbst an.** | Ja — Warteschlangen-Mechanik (`review_flags.py`, `curation_flags.py`) ist voll implementiert; die eigentliche KI-Entscheidungslogik ist ein externer Aufruf, kein Repo-Code | `review_flags.py`; `curation_flags.py` |
| **Autor (Review-Einreichende Person)** | Trifft im Browser (`review.js`-Widget) eine Freigabe-/Ablehnungsentscheidung zu einem Requirement-Text oder einer Kurationsanfrage und sendet sie als GitHub-Issue oder JSON-Download ab. Zwei Vertrauensstufen: `github_authenticated` (durch GitHub-Login belegt) vs. `self_declared` (Selbstauskunft, strenger geprüft). | Ja — Konsument ist `review_ingest.py` / `curation_ingest.py` | `review_ingest.py` Docstring |

## Rollenbeziehungen (Kurzform)

```
Werkzeug ──extrahiert──> Rohbefund
   │
   ▼
Validator ──markiert Uneinigkeit──> Flag (review-queue / curation-queue)
   │
   ▼
KI-Agent ──übernimmt Flag, schlägt Änderung vor──> Diff/PR (wird NICHT selbst angewandt)
   │
   ▼
Kurator ──prüft, mergt oder verwirft, ruft complete_flag()──> Record aktualisiert
```

Daneben, parallel:

```
Autor (Browser, review.js) ──sendet Paket──> GitHub-Issue oder JSON-Download
   │
   ▼
review_ingest.py / curation_ingest.py ──prüft text_hash, Authentizität──> Record aktualisiert (einziger Schreibweg für diese Paket-Art)
```

## Zuständigkeitsgrenzen im vereinheitlichten Modell (0006-14)

Damit die Rollen-Tabelle oben nicht implizit lässt, wer im vereinheitlichten
Kurations-/Review-Modell (**0006-03**/**0006-06**) was darf, hier explizit:

| Zuständigkeit | Wer |
|---|---|
| **Nur Mensch** (`curator`) | Endgültige Entscheidung (`accepted`/`rejected`), tatsächliches Anwenden auf einen Record (`applied`), Betrieb der Extraktionsskripte (`--apply`). Kein Tool und keine KI darf einen Record ohne diesen Schritt final ändern. |
| **KI darf vorschlagen** (`ai`) | Einen `proposed`-Zustand erzeugen: eine konkrete Änderung (`ai-amendment`) oder ein neues hypothetisches Element (`ai-hypothesis`, **0006-05**). Wendet nichts selbst an — Ausnahme: `review_flags.complete_flag()` erlaubt `proposed → applied` direkt, weil dieser Pfad keinen separaten Kurator-Freigabeschritt vom Schreiben der Entscheidung trennt (siehe `workflow-lifecycle.md`); die Entscheidung selbst stammt aber weiterhin von einem Menschen, der das Review-Paket einreicht. |
| **Werkzeug darf automatisch** (`tool`) | Zustandsübergänge, die keine inhaltliche Entscheidung sind: `discovered → queued` (Flag anlegen), `queued → claimed`/`claimed → queued` (atomare Warteschlangen-Mechanik), `applied → published` (regulärer `generate.py`-Lauf). Trifft niemals `accepted`/`rejected`. |

Siehe [`data-model.md`](data-model.md) für das zugehörige Schema und
[`workflow-lifecycle.md`](workflow-lifecycle.md) für die vollständige
Zustandsmaschine samt Tool-zu-Übergang-Zuordnung.


## Versioned curation roles

Curators and maintainers now operate against append-only requirement versions,
version-pinned decisions/evidence, and typed synthesized claims rather than a
single mutable "current truth" document. Curator actions can invalidate or
prune future propagation, but must preserve auditability of prior versions,
confidence history, and supersession links.

