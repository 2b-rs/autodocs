# Daten- und Verzeichnismodell

## Hauptverzeichnisse

| Pfad | Inhalt | Wer schreibt? |
|---|---|---|
| `_src/spec/records/<MODULE>/<ID>.json` | Die eigentliche Spec-DB — ein Record pro Requirement/Klassen-ID, gruppiert nach Modul (z. B. `SWS_RDS`, `SWS_LOG`, `AP_SWS`, `SWS_DM`, `SWS_CRYPT`) | `spec_scrape.py`, `spec_upstream.py`, `review_ingest.py`, `curation_ingest.py`, Migrationsskripte |
| `_src/spec/traceability/<RS_ID>.json` | Kanonische, pro-RS-ID gemergte Traceability-Records aus Chapter-6-"satisfied_by"-Tabellen aller SWS-Dokumente | `spec_scrape.py trace`, `merge_trace_parts.py` |
| `_src/spec/upstream/evidence/<document>/<id>/<backend>.json` | Unveränderliche rohe Backend-Textausschnitte je ID/Dokument/Backend, VOR Normalisierung | `upstream_evidence.py` |
| `_src/spec/review-queue/{open,claimed,done}/` | Flag-Warteschlange für KI-Review-Jobs (Requirement-Text-Unsicherheiten aus der Extraktion) | `review_flags.py` |
| `_src/spec/curation-queue/{open,claimed,done}/` | Flag-Warteschlange für Kurationsanfragen (Extraktion konnte nicht automatisch entscheiden) | `curation_flags.py`, `curation_ingest.py` |
| `_src/spec/campaigns/<id>.json` | Kampagnen-Manifest (Auslöser, Release, Werkzeugstand, Backend-Liste, PDF-Cache-Hash) | **Beschrieben, aber nicht im Repo gefunden** — Konzept ohne Belegdatei |
| `_src/ai/traces/**` | Herkunftsakten für KI-generierte Erklärungen (Texte + Diagramme) | `ai_workflow.py`, `backfill_traces.py` |
| `_src/ai/quellen.json` | Quellenregister für den KI-Bestand | `backfill_traces.py` |
| `_src/ai/policy.json` | Policy-Version, steuert wann KI-Fragmente neu generiert werden müssen | Manuell gepflegt |
| `_src/ai/work/auftrag_*.json` / `*.out.json` | Regenerierungsaufträge (In) und deren Ergebnisse (Out) im Invalidieren→Auftrag→Merge-Zyklus | `ai_workflow.py auftrag` / externer KI-Agent / `ai_workflow.py merge` |
| `_src/i18n/segments.de.json`, `_src/i18n/<lang>/segments.json`, `labels.json` | Mehrsprachigkeits-Register: deutsches Quellregister und übersetzte Register je Sprache | `i18n_extract.py`, `i18n_translate.py` |
| `i18n/work/<lang>/batch_NN.jsonl` | Übersetzungs-Arbeitspakete (noch unübersetzte Segmente/Labels) | `i18n_translate.py split` |
| `_src/data/*.csv` | Generierte, kondensierte Analyse-Sichten (nie Quelle der Wahrheit) | `build_indexes.py` |
| `output/spec-validation/<release>/crosscheck-<campaign>.json` | Archivierter, unveränderlicher Crosscheck-Lauf (Kampagnen-Input) | `spec_scrape.py crosscheck --json` (manuell umgeleitet) |
| `output/run-archive/run-<timestamp>-n<seq>.{sh,log}` | Vollständiges Archiv jeder ausgeführten Task (Skript + Log) | Task-Runner-Infrastruktur, automatisch |

## Record-Feldstruktur (Kernfelder, aus mehreren Quellen zusammengetragen)

```json
{
  "id": "SWS_RDS_00123",
  "document": "AUTOSAR_AP_SWS_RawDataStream.pdf",
  "page": 42,
  "heading": "...",
  "upstream": [ { "rs_id": "RS_...", "document": "AUTOSAR_AP_RS_General.pdf" } ],
  "namespace": "...",
  "enclosing": "...",
  "props": { "Kind": "...", "Header file": "...", "Scope": "..." },
  "fields": {
    "<FeldName>": {
      "value": "...",
      "state": "valid/corrected",
      "reason": "database error, detected after new import",
      "votes": { "pypdf": "...", "builtin": "...", "legacy": "..." },
      "trace": [ { "mode": "direct_id", "sources": [ "..." ] } ]
    }
  },
  "status": { "state": "...", "reason": "...", "campaign": "..." },
  "history": [ { "campaign": "...", "date": "...", "from": "...", "to": "...", "reason": "...", "actor": "tool|ai|curator" } ],
  "requirement_meta": {
    "trace": [ { "review": { "status": "accepted|rejected" } } ],
    "review_status": "pending",
    "review_reason": "legacy-desc-import"
  },
  "requirement_text": {
    "text_raw": "...",
    "text_en": "...",
    "repairs": [ { "rule": "manual_space@v1" } ],
    "suspects": [ "..." ]
  }
}
```

**Hinweis**: Nicht jedes Feld ist in jedem Record vorhanden — `fields`,
`history`, `status.campaign` erscheinen bislang hauptsächlich in den
`SWS_LOG`-Pilot-Records; die meisten `SWS_RDS`-Records tragen bislang nur
`upstream` als neu hinzugekommenes Feld ohne begleitenden `status`/`history`-
Eintrag (siehe Beobachtung in `campaigns.md`).

## Evidenz-Feldstruktur (Phase 5, `SPEC_BUILD_PROCESS.md`)

```json
"evidence": [
  { "text": "wörtliches Zitat", "source": "...", "locator": "...", "strength": "strong|medium|weak" }
],
"counter_evidence": [ { "...": "..." } ]
```

**Status**: Nur als Schema in der Prozessbeschreibung erwähnt — keine
Belegdatei mit tatsächlichen `evidence[]`-Einträgen in diesem Format
gefunden (zu unterscheiden von `upstream_evidence.py`'s separatem
Rohbeobachtungs-Speicher).
