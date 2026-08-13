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

## Versionierungs- und ID-Schema für Cross-Release-Nachverfolgbarkeit (Entwurf, 0006-15..22)

> Status: **Entwurf** — beschreibt die Zielarchitektur für `TODO.md`
> Feature 0006, Aufgaben 0006-15 bis 0006-22. Noch nicht implementiert.
> Motivations-Szenario: eine kuratierte Entscheidung zu einem Requirement
> wird durch ein neues AUTOSAR-Release überholt; alle davon abhängigen
> Evidenzen, Synthesen und KI-Artefakte müssen auffindbar, aber nichts darf
> gelöscht werden.

### Versionierungsgranularität

Für AUTOSAR AP wird auf **Requirement-Ebene** versioniert (nicht Feld- oder
Dokumentebene). Jede inhaltliche Änderung eines Requirements über Releases
hinweg erzeugt eine neue, unveränderliche Version.

### ID-Familien

| ID-Familie | Schema | Beispiel | Charakteristik |
|---|---|---|---|
| Kanonische Requirement-Identität | `project/kind/id` | `AUTOSAR/AP/record/SWS_UCM_00348` | releaseunabhängig, stabil über alle Releases |
| Requirement-Version | `<canonical-id>@rel:<release>#<content-hash8>` | `AUTOSAR/AP/record/SWS_UCM_00348@rel:R25-11#a1c9f3e2` | ein unveränderlicher Inhalts-Snapshot pro Release |
| Kurationsentscheidung | `curation:<uuid7>` | `curation:018f2b3a-...` | unveränderlich nach Entscheidung, nur "superseded", nie gelöscht |
| Evidenz-Snippet | `evidence:<uuid7>` | `evidence:018f2c4d-...` | Ergebnis des ersten KI-Durchlaufs (Scraping), fest an eine Requirement-Version gebunden |
| Artefakt / Synthese | `artifact:<uuid7>` | `artifact:018f2d1a-...` | Ergebnis des zweiten KI-Durchlaufs (Beschreibung, Amendment, Hypothese, Resynthese) |
| Supersession-Kante | `supersedes:<old-version-id>-><new-version-id>` | — | explizite Kante, nicht aus Zeitstempeln abgeleitet |

UUIDv7 wird für Kurationsentscheidungen, Evidenz-Snippets und Artefakte
verwendet, da es über nebenläufige Schreibpfade (Queue, Browser, KI-Agent)
hinweg zeitlich sortierbar bleibt (siehe 0006-06). Die Hash-Länge/-Funktion
für Requirement-Versionen ist in 0006-15 final festzulegen.

### Speicherstruktur (Zielbild)

- **Requirement-Version-Store** (neu, 0006-16): Append-only-Ablage je
  Requirement-Version-ID; der bestehende Record-Store
  (`_src/spec/records/<MODULE>/<ID>.json`) wird zu einem "current pointer"
  auf die jeweils aktuelle Version.
- **Kurationsentscheidung** trägt `decided_on_version` (Requirement-Version-ID),
  gesetzt zum Entscheidungszeitpunkt (0006-17).
- **Evidenz-Snippet** trägt `source_version` (Requirement-Version-ID) sowie
  Text, Quelle, Locator, Stärke und die vom KI-Scraper vergebene Begründung
  für die Zuordnung (0006-17).
- **Artefakt/Synthese** referenziert Evidenz-Snippets, Kurationsentscheidungen
  und ggf. frühere Artefakte (Resynthese) über `evidence_refs[]`.

### Abhängigkeitsgraph (0006-18)

Knotentypen: `requirement-version`, `curation-decision`, `evidence-snippet`,
`artifact/synthesis`, `human-comment`.

Kantentypen: `derived_from`, `quotes`, `supersedes`, `revisits`,
`comments_on`, `dismisses`, `confirms`.

**Wichtig**: `artifact -> artifact`-Kanten sind explizit erlaubt und nötig,
da die KI ihre eigene vorherige Synthese zusammen mit neuen/geänderten
Fakten oder Kommentaren erneut zusammenfassen kann (Resynthese). Eine
lebendige Mensch-KI-Diskussion, in der der Kurator einen KI-Kommentar nie
vollständig verwirft, kann daher beliebig viele Hops erzeugen — der Graph
ist **nicht** auf eine feste Hop-Zahl begrenzt.

Invalidierungs-/Revisit-Erkennung erfolgt als Graphtraversierung bis zum
Fixpunkt (mit Visited-Set zur Zyklensicherheit), nicht als Traversierung
mit fester Tiefe. Die Traversierung terminiert, wenn keine weiteren
abhängigen Knoten erreichbar sind oder ein vom Kurator verworfener
("dismissed") Knoten erreicht wird — Dismissal ist der Mechanismus, der die
Weiterpropagierung stoppt.

### Invalidierung und Konfidenz (0006-19, 0006-21)

- `invalidated`/`stale` ist ein von der Lifecycle-Statusmaschine
  (discovered → queued → claimed → proposed → accepted/rejected → applied →
  published → superseded, siehe 0006-06) **unabhängiges** Flag, das per
  Graph-Kaskade gesetzt wird, nicht durch eine Kurator-Aktion.
- Invalidierte Artefakte bleiben abrufbar und werden nie gelöscht, nur
  markiert.
- Jede KI-generierte Wissenseinheit trägt ein append-only
  `confidence_history[]` (Wert, Zeitpunkt, zugrunde liegende Version,
  Eingaben). Alte Konfidenzwerte bleiben erhalten und müssen mit denselben
  Eingaben neu berechenbar sein, auch nachdem das zugrunde liegende
  Requirement, ein Kommentar, eine Quelle oder das verwendete KI-Modell
  durch eine neuere Version abgelöst wurde.
- Innerhalb einer Synthese wird pro Claim (Aussage/Abschnitt) unterschieden:
  Hard Fact, kuratierter Fakt, Nutzerkommentar, KI-inferiertes Wissen. Jeder
  Claim trägt eigene `evidence_refs[]`, `confidence` und
  `confidence_history[]` (siehe 0006-21).

### Auslöser für Neubewertung (0006-20)

Ein generischer Supersession-Trigger-Job ersetzt den reinen
Release-Diff-Gedanken. Auslöser umfassen: neues AUTOSAR-Release, neue
Kurationseingabe, Nutzerkommentar, Scraper-Update, Extraktions-Bugfix, neu
verfügbare Quellen, geändertes KI-Modell/geänderte Einstellungen. Jeder
Auslöser erzeugt neue unveränderliche Versionen (wo zutreffend) und stößt
die Graphtraversierung an, um abhängiges Wissen zu invalidieren und/oder
zur KI-Neubewertung einzureihen.

### Org/project registry

Canonical identity uses the release-free form `org/project/item_type/id`. Valid `org/project` pairs and their supported `item_type` values are registered in `_src/spec/projects.json`; consumers must not maintain private copies of this enum. `AUTOSAR` and `ECLIPSE` are organizations; `AP`, `CP`, `FOUNDATION`, and `S-Core` are projects run by those organizations. A registry entry records the organization, the project, a curator-facing display name, and the open set of curatable item types currently supported for that project.

AUTOSAR AP, CP, and Foundation currently expose document-extracted `record` items. Eclipse S-Core initially registers `module`, `component-interface`, and `design-doc` item types; adding another item type or org/project pair requires an explicit registry change so validators and downstream tools can reject accidental or misspelled identity dimensions.
