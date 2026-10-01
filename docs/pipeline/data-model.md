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

## Record status/history coverage (0006-04)

As of 2026-08-13, every record under `_src/spec/records/` carries a `status` key (previously only the `SWS_LOG` pilot module and a handful of others did). Records that never went through a real curation campaign were mechanically backfilled by `_src/tools/migriere_status_backfill.py` with `status.state="valid/unmigrated"` -- deliberately distinct from `"valid/auto-approved"`, which is reserved for records with a genuine campaign history. Field-level `fields.<name>.state/reason/trace` backfill remains out of scope (no real per-field vote data exists outside the pilot set); `validate.py`'s `check_record_status()` only enforces presence of the top-level `status` key, not field-level detail.

## Vereinheitlichtes Kurations-/Review-Modell (0006-14)

Die beiden oben genannten Warteschlangen (`review-queue`, `curation-queue`)
sind seit **0006-03** zusätzlich über ein gemeinsames Ziel-Schema
beschrieben, **curation-item@v1** (`_src/tools/curation_item.py`,
siehe [`curation-item-schema.md`](curation-item-schema.md)). Beide
Warteschlangen-Formate (`review-flag@v1`, `curation-flag@v1`) bleiben die
tatsächlichen Schreibformate auf Platte; `curation_item.py` liefert nur
lesende Adapter (`from_review_flag()`, `from_curation_flag()`), die beide
auf dieselbe Feldliste normalisieren. Die dazugehörigen Zustände
(`open`/`claimed`/`proposed`/`accepted`/`rejected`/`superseded`/`applied`)
sind Teilmenge des größeren, pipeline-weiten Lebenszyklus aus **0006-06**
(`discovered → queued → claimed → proposed → accepted/rejected → applied →
published → superseded`, siehe [`workflow-lifecycle.md`](workflow-lifecycle.md)).
Dieses Datenmodell ist damit die kanonische Quelle für "was ein
Kurations-Item ist" — neue Datenquellen (z. B. zukünftige S-Core-Elemente,
**0009-05**) sollen auf `curation-item@v1` abgebildet werden, nicht auf ein
neues Ad-hoc-Schema.


## Versioned requirement / evidence / synthesis model (integrated 2026-08-13)

The versioned curation model is now implemented by concrete modules, not just
planned abstractions:

- `version_id.py` defines stable ids for requirement versions, curation ids,
  evidence ids, artifact ids, and hypotheses / typed claims.
- `version_store.py` is the append-only immutable requirement-version store.
- `curation_item.py` pins decisions/evidence to exact `decided_on_version`
  values.
- `dependency_graph.py` models typed graph edges between requirement versions,
  curated decisions, evidence nodes, and synthesized artifacts/claims.
- `confidence.py` tracks confidence history, invalidation, dismissal behavior,
  and revisit enqueueing.
- `typed_claim.py` defines the concrete `typed-claim@v1` schema for
  inspectable synthesized knowledge units.
- `supersession_trigger.py`, `asof_view.py`, and `delta_view.py` provide the
  orchestration/query layer over these append-only stores.

### Worked example A: new AUTOSAR release supersedes a curated requirement

1. `version_store.record_version()` records `AUTOSAR/.../REQ_X@rel:R25-11#...`.
2. A curator decision and related evidence snippets are pinned to that exact
   version id via `decided_on_version` / evidence refs.
3. Later, a new release arrives; `supersession_trigger.process_trigger()`
   detects that `R32-11` has genuinely changed content and records a new
   immutable version.
4. The same trigger reuses `confidence.cascade_invalidate()` to walk
   `dependency_graph.find_dependents()` and mark downstream evidence/artifacts
   invalidated + enqueue revisits.
5. `asof_view.as_of_release(..., 'R25-11')` still reconstructs the older world
   without hiding what is now superseded; `delta_view.delta_view(release='R25-11')`
   summarizes what changed since then.

### Worked example B: human comment triggers AI resynthesis

1. A human comment is represented as a typed claim or graph/comment input,
   not as an invisible overwrite of prior AI text.
2. `supersession_trigger.process_trigger(trigger_kind='user_comment', ...)`
   records a new causal event for the affected requirement/artifact context.
3. Downstream synthesized claims/artifacts are invalidated and revisit work is
   enqueued.
4. A later AI synthesis may emit a new `typed-claim@v1` object that
   `supersedes_claim_ids` from the old AI-inferred claim while preserving the
   old text and its confidence history.

### Worked example C: curator dismissal prunes future propagation but keeps history

1. A curator can dismiss a node/claim for future propagation.
2. In the dependency graph/confidence model, dismissal never severs historical
   edges or deletes prior artifacts; it only blocks future derivation and can
   floor confidence appropriately.
3. In the typed-claim schema this appears as
   `dismissed_from_future_synthesis = true` while evidence refs, prior text,
   supersession links, and confidence history remain auditable.
4. As-of and delta queries therefore keep the node visible as history instead
   of silently removing it.

