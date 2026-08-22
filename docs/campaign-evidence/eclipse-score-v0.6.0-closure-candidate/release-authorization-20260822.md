# Freigabe zur Veröffentlichung — Feature 0019, v0.6.0 Kuratieransicht

**Kontrolle 3 aus `DEC-0019-002`.** Dieser Datensatz hält die ausdrückliche
Management-Freigabe fest, die der Veröffentlichung vorausgehen muss.

## Freigabe

- **Erteilt am:** 2026-08-22
- **Erteilt von:** Management (aktueller User / Repository-Eigentümer)
- **Wortlaut, verbatim:**

  > Passt, kann so raus..

- **Aufgezeichnet von:** Projektleiter `kathryn`
  (`DEC-ROLE-001`: zeichnet auf, entscheidet nicht)
- **Autoritätsgrundlage der Veröffentlichung:** `DEC-0019-001`
  (Commit `d6777be3a`) — Publikationsautorität für Feature `0019`, in vollem
  Umfang, an `worf`.

## Was genau freigegeben ist

**Exakt dieser Baum, byteidentisch:**

- Vorschau: `/tmp/autodocs-0019-10-preview-20260822T003000Z/export/`
- **Tree-SHA256:** `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`
- Umfang: 2.248 Dateien, davon 2.239 Kandidaten-Seiten plus
  `records/index.html` als Listing-Seite
- Herkunft: Branch `0019-10` bei `de15a703cfc3d7b07865c339ba631aca8932abcf`,
  integrierter Feature-Tip `58b35f1e54cff2b4e718febe2c666cf5e67ae3f5`

**Digest-Verfahren, reproduzierbar** (nachgeliefert von `worf`, ausgeführt und
bestätigt von `kathryn` am 2026-08-22 — exakte Übereinstimmung): SHA-256 über
lexikografisch pfadsortierte Sätze aus UTF-8-Pfadbytes, einem NUL-Byte und dem
**rohen** 32-Byte-SHA-256 der Dateibytes; anschließend SHA-256 über den
Gesamtstrom. Implementiert in
`_src/tools/prepare_score_curation_export.py:204`.

```
python3 -c 'import hashlib,pathlib; r=pathlib.Path("."); f=sorted(p for p in r.rglob("*") if p.is_file() and not p.is_symlink()); print(hashlib.sha256(b"".join(p.relative_to(r).as_posix().encode()+b"\0"+hashlib.sha256(p.read_bytes()).digest() for p in f)).hexdigest())'
```

## Bindende Auflage: keine Änderung nach der Prüfung

**Veröffentlicht wird der Baum mit exakt obigem Digest.** Jede Änderung — auch
eine scheinbar harmlose — erzeugt einen anderen Baum, der die enge
Ausschlussprüfung **nicht** durchlaufen hat und dessen Digest nicht mehr auf die
Freigabe passt. Wer den Baum ändert, veröffentlicht etwas, das das Management
nicht freigegeben hat.

Das betrifft ausdrücklich die zwei bekannten toten relativen Links (siehe
*Bekannte, bewusst nicht behobene Mängel*). Sie werden **vor** der
Veröffentlichung **nicht** repariert.

## Erfüllte Kontrollen nach `DEC-0019-002`

1. **Enge Ausschlussprüfung — `sauber`.** QA-Manager
   `Kathryn-Harry-20260822T113000Z`, unprivilegiert, unabhängig von allen
   Implementierern des Features. Bericht:
   [`../qa-exclusion-check-0019-20260822/report.md`](../qa-exclusion-check-0019-20260822/report.md),
   auf `main` seit `120504cd7`.
   - 2.239 von 2.239 Kandidaten-Seiten tragen den Marker
     `UNVALIDATED — AWAITING CURATOR CONFIRMATION`; **null** ohne Marker,
     mechanisch über alle Seiten geprüft.
   - Einziger `data-validation-state`-Wert im gesamten Baum: `unvalidated`
     (6.723 Vorkommen).
   - Kein Fremdinhalt: null lokale Pfade, null E-Mail-Adressen, null
     Claim-Dateien, null Agenten-/Session-Token. Einziger `status`-Wert:
     `invalid/to-be-confirmed`.
   - Von `kathryn` unabhängig nachgefahren, gleiches Ergebnis. Zwei Treffer auf
     Schlüsselbegriffe einzeln geprüft und als AUTOSAR-Normtext bestätigt
     (Anforderungen zu Reverse Engineering bzw. Schlüsselableitung) — keine
     Zugangsdaten.
2. **Freigabevorschau geliefert.** Anklickbarer lokaler Link auf den gebauten
   Baum und `overview.html` mit Änderungsübersicht und Seitenlinks; alle Links
   lösen auf, Zahlen decken sich mit `validation.json`.
3. **Ausdrückliche Freigabe** — dieser Datensatz.

## Unberührte Schranke: die Kuratorentscheidung

`CUR-0019-08-20260820` bindet unverändert. Die 2.239 als
`invalid`/`to-be-confirmed` geführten Records bleiben von **faktischer**
Publikation ausgeschlossen; veröffentlicht wird ausschließlich die begrenzte,
durchgehend als unvalidiert markierte Kuratier-/Reviewansicht. Die Freigabe
betrifft die Autorität, nicht den Inhalt.

## Bekannte, bewusst nicht behobene Mängel

- **Zwei tote relative Links**, von der Ausschlussprüfung als
  Nebenbeobachtung notiert, ausdrücklich kein Befund und kein Blocker:
  - `participate.html` → `../../../curation-report.html`
  - alle Record-Seiten → `../../../../review_request.js` (existiert nirgends im
    Baum)

  Sie gehen **mit** in die Veröffentlichung, weil eine Reparatur den geprüften
  Baum verändern und damit Prüfung und Digest entwerten würde. Sie sind als
  Nachfolgearbeit zu führen und in einer späteren Veröffentlichung zu beheben.

## Was diese Freigabe nicht ist

Sie ist **keine** Task- oder Feature-Abnahme, **kein** Integrationsverdikt und
**kein** `DONE.md`-Umzug. Die Integration von Feature `0019` nach `main` und
sein Abschluss bleiben eigenständige privilegierte Akte.
