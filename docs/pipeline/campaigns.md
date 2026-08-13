# Kampagnentypen

Eine **Kampagne** ist laut `SPEC_BUILD_PROCESS.md` jeder benannte Neuaufbau
der Spec-DB, mit eigener ID, damit History und Reports zuordenbar bleiben.
Unten: das generische Namensschema aus dem Prozessdokument, plus die
konkreten Kampagnen-IDs, die tatsächlich in den Records dieses Repos
gefunden wurden.

## Generisches Schema (aus `SPEC_BUILD_PROCESS.md`)

```
campaign: <YYYY-MM>-<kurzbeschreibung>
trigger:  <Auslöser, z. B. "spec update after tool improvement">
release:  <AUTOSAR-Release, z. B. R25-11>
scope:    <Teilmenge der Records, z. B. "alle Records unter spec/records/">
```

Manifest-Pfad: `spec/campaigns/<id>.json` (Auslöser, Release, Werkzeugstand /
Git-Commit von `spec_scrape.py`, Backend-Liste, PDF-Cache-Hash).

**Implementierungsstatus des Manifests (0006-08, 2026-08-13)**: implementiert in
`_src/tools/campaign_manifest.py`. `write_manifest()` legt `spec/campaigns/<id>.json`
an (Trigger, Release, Scope, Git-Commit von `spec_scrape.py`, Backend-Liste,
`corpus_hash` -- ein hash8 einer deterministischen (Pfad, mtime)-Auflistung aller
Records, kein Volltext-Hash -- sowie ein `queue_snapshot` mit offen/claimed/done-
Zählern beider Warteschlangen). `append_decision()`/`append_report()` ergänzen
append-only Listen `curator_decisions`/`published_reports`. Die drei in Records
gefundenen Kampagnen-IDs unten sind rückwirkend als Manifeste materialisiert.
Siehe `docs/pipeline/campaign-manifest-schema.md` für das vollständige Feldschema.

## Tatsächlich vorkommende Kampagnen-IDs in den Records

| Kampagnen-ID | Wo gefunden | Zweck (aus Kontext) |
|---|---|---|
| `2026-08-sws-log-pilot-after-tool-improvement` | `status.campaign`, `history[].campaign` in 71 `SWS_LOG`-Records | Pilotlauf des vollen Kampagnenzyklus (Phase 0–2: invalidieren → neu bewerten → auto-approve) nach einer Werkzeugverbesserung, beschränkt auf ein Modul als Testlauf |
| `requirement-import` | Standardwert von `--campaign` in `spec_scrape.py reqs --write-reqs` | Generischer Vorgabename für das additive Schreiben von Prosa-Requirements in die DB, wenn kein expliziter `--campaign`-Wert übergeben wird |
| `legacy-desc-import` | `requirement_meta.review_reason` in einigen `SWS_LOG`-Records | Kennzeichnet Records, deren Beschreibung aus einem älteren, weniger vertrauten Importpfad stammt — markiert als `review_status: "pending"` |

## Kampagnentyp nach Auslöser (abgeleitet)

| Auslöser | Beispiel | Wo im Prozess |
|---|---|---|
| Werkzeugverbesserung (Parser-Fix, neue Heuristik) | `2026-08-sws-log-pilot-after-tool-improvement` | Phase 0–6, voller Zyklus |
| Requirement-Text-Import (additiv, aus PDF-Prosa) | `requirement-import` | Nur `spec_scrape.py reqs --write-reqs`, kein voller Kampagnenzyklus nötig |
| Upstream-Metadaten-Rebuild (RS-Verknüpfung) | (kein eigener Kampagnenname im Code gefunden — `upstream --rebuild` trägt selbst keine `--campaign`-Option) | Nur Phase, kein volles Kampagnen-Manifest |
| Legacy-Description-Import | `legacy-desc-import` | Erzeugt `review_status: pending`, wartet auf Kurator/KI-Agent |
| Evidenz-Ernte aus informellem Dokument | (Muster: `spec: evidence harvest <document> (campaign <id>, …)`) | Phase 5, kein Beispiel in den Records gefunden |
| KI-Content-Regenerierung (Seiten/Diagramme) | (kein Kampagnenname — `ai_workflow.py` nutzt stattdessen `ai/work/auftrag_*.json`-Dateien, keine Kampagnen-ID) | Eigener, separater Zyklus (Invalidieren→Auftrag→Merge), nicht Teil des Spec-DB-Kampagnenmodells |

## Wichtige Beobachtung

Die Kampagne `2026-08-sws-log-pilot-after-tool-improvement` ist bislang die
einzige, die den vollen, im Prozessdokument beschriebenen Zyklus (Entwerten
→ Neubewertung → Freigabe) tatsächlich in Records nachweisbar durchlaufen
hat — begrenzt auf `SWS_LOG` als Pilotmodul. Der viel größere
`upstream`-Rebuild (2.925 Records, alle anderen Module) läuft dagegen
**außerhalb** dieses Kampagnenmodells: Er trägt keinen `campaign`-Wert, kein
Manifest, und keinen `history`-Eintrag — er ist reine Feldanreicherung ohne
Statusänderung.
