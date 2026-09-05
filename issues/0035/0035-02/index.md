---
schema_version: "1.0"
id: "0035-02"
level: "task"
parent: "0035"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-04.01"
  - "0033-10"
  - "0033-13"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2570"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Verifizieren und schliessen, dass der Review-Request gemaess dem genehmigten Vertrag die bereits vorhandene localStorage-Sammelstruktur fuer Reviews/Feedback wiederverwendet, statt einen unverbundenen Speicher-/Submit-Weg zu behalten. PREREQ: 0035-02:0033-04.01, 0035-02:0033-10, 0035-02:0033-13

## Scope

- **Befund (2026-08-15, Nutzer):** Auf der Website existiert bereits eine Struktur, um Reviews und Feedback in localStorage vorzuhalten und spaeter gesammelt zu submitten. Der Flag-for-review-Dialog (`review_request.js`) nutzt diese Struktur nicht — verifiziert durch Volldump: `review_request.js` legt Requests nicht in localStorage ab (nur `ara-review-github-token-v1` / `ara-review-identity` fuer Identitaet) und submitted stattdessen direkt per GitHub-Issue oder JSON-Export im selben Klick.
  - **Nutzer-Screenshot (2026-08-15, `namespaces/ns_log_ara_log_10815c.html#review-SWS_LOG_00210`):** Zeigt einen bereits existierenden "Review-Paket"-Dialog mit Untertitel "Gesammelte Entscheidungen, nur in diesem Browser gespeichert."; einzelne Eintraege je Record-ID mit Freigeben/Ablehnen-Status, Freitext-Kommentar, Autor und Zeitstempel, jeweils einzeln entfernbar (×); Footer-Aktionen `Alle verwerfen`, `JSON exportieren`, `Paket absenden`. Dies ist mutmasslich ein anderes JS-Modul als `review_request.js` und muss lokalisiert werden (Arbeitsname hier: Review-Paket-Modul).
  - **Lokalisiert (2026-08-15, verifiziert per Volldump, 577 Zeilen):** Modul ist `review.js` (Kommentarkopf: "Sammel- und Abgabe-Workflow fuer Requirement-Reviews"), voellig getrennt von `review_request.js`. Storage-Key `ara-review-package-v1` (Array von Items via `load()`/`store()`), GitHub-Token separat unter `ara-review-github-token-v1` (identisch zum Key in `review_request.js` — beide Module teilen sich offenbar bereits die Identitaets-/Token-Ablage, aber nicht die Request-Ablage). Item-Schema pro Entscheidung: `{ id, outcome, decided_by, identity, decided_at (ISO), rationale, decision_basis }`; `id` wird beim Speichern dedupliziert (`filter x.id !== d.id` vor `push`). Sammel-Submit `submitPackage()` baut `payload = { schema: "review-package@v1", identity: "github_authenticated", ... }` und postet per `fetch` einen GitHub-Issue nach `/repos/{repo}/issues` mit dem gesamten Paket als JSON-Codeblock im Issue-Body; `exportPackage()` bietet denselben Payload als lokalen JSON-Download. `repo()` liest das Ziel-Repository aus `<meta name="review-github-repo">`, exakt wie in `review_request.js`.
  - **Schema-Luecke fuer 0035-02:** `review-package@v1` ist ein Item-Array pro Requirement-Entscheidung (`outcome`/`decided_by`/`rationale`/...) und kennt keine Felder aus `review-request-package@v1` (0021-02: `target_canonical_id`, `target_content_hash`, `category`, `evidence_refs` usw.). Eine Wiederverwendung erfordert entweder (a) einen neuen `kind`- oder `schema`-Discriminator, der beide Item-Formen im selben `ara-review-package-v1`-Array unterscheidet, oder (b) eine Konvertierung des Flag-for-review-Pakets in ein `outcome`-aehnliches Item mit `rationale` als Trager und den 0021-02-Feldern in `decision_basis` oder einem neuen optionalen Feld. Diese Entwurfsentscheidung ist vor der Implementierung zu treffen und hier festzuhalten, nicht implizit im Code.
  - **Akzeptanzkriterien:** Ein erzeugter Review-Request wird in der bestehenden Struktur abgelegt und erscheint in deren Sammel-/Uebersichtsansicht; das Paketschema aus 0021-02 (Record-/Versions-ID, Content-Hash, Status-Snapshot, Actor, Kategorie, Rationale, Evidence) bleibt vollstaendig und schema-valide erhalten; ein lokal gehaltener Request wird in der UI klar als lokal/noch nicht eingereicht ausgewiesen; der spaetere Sammel-Submit erzeugt dasselbe Paket wie der direkte Weg.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Umstellung und Tests committed mit `REF`; Nachweis, dass Stale-Erkennung weiterhin greift, wenn ein lokal zwischengespeicherter Request erst nach einer Aenderung des Ziel-Records eingereicht wird.
