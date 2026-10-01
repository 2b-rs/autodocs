# Spezifikations-Traceability für die Record-Datenbank

Diese Datei definiert die Anforderungen an Herkunft, Belegbarkeit und Inferenz für die Spezifikations-DB unter `spec/records/`. Sie ergänzt das Schichtenmodell aus `ARCHITEKTUR.md`: kanonische Fakten bleiben in den Spec-Records, aber künftig muss **jeder gespeicherte Fakt** auf konkrete Evidenz zurückführbar sein.

Die Regeln hier gelten für direkt extrahierte Fakten ebenso wie für abgeleitete Eigenschaften, etwa Klassen-Vererbung, Besitzbeziehungen, implizite Typmerkmale oder aus mehreren Fragmenten erschlossene Strukturen.

## Ziele

- Für jedes Spezifikationselement muss nachvollziehbar sein, **woher** jede gespeicherte Information stammt.
- Die Record-Datenbank muss nicht nur explizit genannte Normtexte abbilden, sondern auch **begründete Ableitungen** aus formaler und informeller Evidenz tragen können.
- Inferenz darf massiv genutzt werden, aber niemals spurlos: jede inferierte Eigenschaft braucht maschinenlesbare Herkunft.
- Schwache Evidenz darf gespeichert werden, auch wenn sie noch nicht in einen kanonischen Fakt überführt wurde.
- Generierte HTML-Seiten, Diagramme und CSVs bleiben Wegwerfartefakte; maßgeblich sind Quellen, Evidenz, Claims, Entscheidungen und Spec-Records.

## Grundprinzipien

1. **Kein Fakt ohne Herkunft.** Kein Record-Feld darf ohne Traceability-Eintrag persistiert werden.
2. **Direktes und Inferiertes trennen.** Ein Wert muss als `asserted`, `inferred`, `conflicting`, `rejected` oder ähnlich klassifizierbar sein.
3. **Evidenz ist langlebiger als die aktuelle Interpretation.** Auch verworfene oder schwache Belege dürfen erhalten bleiben.
4. **Ein Fakt kann mehrere Belege haben.** Traceability ist eine Menge von Begründungen, nicht nur ein einzelner Link.
5. **Inferenzregeln sind Teil des Systems.** Wenn ein Fakt durch Schlussfolgerung entsteht, muss erkennbar sein, nach welcher Regel oder welchem Verfahren dies geschah.
6. **Menschliche Review bleibt möglich.** Jeder abgeleitete Fakt muss überprüfbar, kommentierbar und bei Bedarf revidierbar sein.

## Modellbegriffe

### Fakt

Ein kanonisch akzeptierter Property-Wert in `spec/records/`, der für Generierung, Suche und Diagramme verwendet werden darf.

### Evidenz

Ein einzelnes beobachtetes Fragment aus einer Quelle, z. B.:

- ein PDF-Deep-Link mit ID,
- ein PDF-Deep-Link auf ein nicht-ID-basiertes Element,
- ein Satz aus einer Dokumentation,
- eine Signatur oder Deklaration aus Code,
- ein Konstruktor-Record,
- ein UML-Fragment,
- eine Tabelle,
- eine narrative Beschreibung mit schwacher, aber verwertbarer Aussagekraft.

### Claim

Ein aus Evidenz erzeugter Kandidat für eine Eigenschaft, z. B. „`ara::diag::DiagException` hat Parent `ara::core::Exception`“.

### Entscheidung

Der Review- oder Pipeline-Status eines Claims, z. B. akzeptiert, verworfen, unklar, durch Gegenbeleg blockiert.

### Inferenzregel

Eine versionierte Regel, Heuristik oder Pipeline-Komponente, die aus Evidenz einen Claim erzeugt oder stärkt.

## Mindestanforderung: Traceability für jeden gespeicherten Fakt

Jeder gespeicherte Fakt muss mindestens **einen** Traceability-Record besitzen. Ein Traceability-Record muss mindestens eine der folgenden Formen erfüllen:

### A. Direkter Beleg mit ID

Ein Deep-Link in ein offizielles Standard-PDF, der auf ein Spezifikationselement mit passender ID zeigt.

Beispiel:

- Property: `record.upstream = RS_AP_00119`
- Trace: PDF-Link mit `#nameddest=SWS_DM_00516`

### B. Direkter Beleg ohne ID

Ein Deep-Link in ein offizielles Standarddokument auf ein Element ohne eigene ID, aber mit ausreichend präzisem Locator, z. B. Seitenbereich, Überschrift, Tabellenzeile, Diagrammknoten oder Syntaxblock.

Dies ist zulässig, wenn die Spezifikation die relevante Information nicht als eigenes SWS-/RS-Element normiert.

### C. Inferenz mit internem Stützrecord

Ein Deep-Link in ein offizielles Standarddokument **plus** Verweis auf mindestens einen internen Spec-Record eines anderen Kindes, aus dem die Eigenschaft teilweise oder vollständig abgeleitet wurde.

Dies ist die Mindestform für Eigenschaften, die nicht direkt als normierter Einzel-Record vorliegen, aber aus der Spezifikation robust erschließbar sind.

Beispiel „Parent-Klasse“:

- Class-Record: `ara::diag::DiagException`
- Property: `parents = ["ara::core::Exception"]`
- Externe Evidenz: Deep-Link auf die Klassendeklaration `class DiagException : public ara::core::Exception`
- Interner Stützrecord: Konstruktor-Record `SWS_DM_00516`, weil er den Record-Kontext `class ara::diag::DiagException` explizit bestätigt

### D. Mehrquellen-Argument

Eine Liste von Deep-Links in Standarddokumente, dazu kurze Zitate bzw. Extrakte und **eine Prosa-Begründung**, warum diese Evidenzmenge hinreichend ist, um den gespeicherten Wert zu inferieren.

Dies ist besonders wichtig für schwächer strukturierte oder informelle Eigenschaften, bei denen kein einzelner Satz allein genügt.

Beispiele:

- Parent-Name nur aus mehreren Stellen indirekt ableitbar
- Ownership oder Rollenbeziehung aus Prosa, Tabelle und Signatur gemeinsam erschließbar
- Verhalten oder semantische Klassifikation aus Dokumentation, Code und Spezifikationshinweisen kombiniert

## Neue Anforderung: explizite Class-Records

Klassen dürfen künftig nicht mehr nur implizit durch Member-Records mit `Scope = class ...` existieren.

Stattdessen gilt:

- Für **jede** Klasse wird ein eigener Spec-Record geführt.
- Dieser Class-Record ist der kanonische Ort für Klassen-Metadaten wie Name, Header, Parent-Beziehungen, Basisklassen, Interfaces, semantische Rollen oder andere typbezogene Eigenschaften.
- Member-Records bleiben eigenständige Records, referenzieren aber die Klasse weiterhin über Scope oder eine explizite Parent-/Owner-Referenz.
- Beim Einstellen eines Member-Records in die Spec Record-Datenbank muss geprüft werden, ob ein entsprechender Class Record existiert. Falls nicht, wird er erstellt.
- Erstellung von Spec Records immer mit Datum, Zeit, und Begründung (z.B. Scraping von (Referenzdokument))
- Spec Records kriegen eine Anderungshistorie!

Damit ist die Klasse selbst als Entität adressierbar, reviewbar und tracebar.

## Neue Anforderung: explizite Requirement-Records

Normative Anforderungen dürfen künftig nicht mehr ausschließlich als Beschreibung, Upstream-Referenz oder impliziter Kontext eines API-, Class- oder Member-Records erscheinen.

Stattdessen gilt:

- Für jede explizit im Standard mit eigener ID ausgewiesene Anforderung wird ein eigener Requirement-Record unter `spec/records/<PREFIX>/<ID>.json` geführt.
- Der Requirement-Record ist der kanonische Ort für Anforderungstext, Überschrift, Upstream-Beziehungen, Status, Dokumentfundstelle und Traceability.
- Der normative Originaltext wird im Block `requirement_text` wörtlich und sprachlich unverändert gespeichert. Er ist nicht KI-generiert und wird bei der HTML-Generierung als englischer Originaltext ausgegeben.
- API-, Class- und Member-Records bleiben eigenständig. Sie dürfen über `covers` bzw. `covered_by` mit Requirement-Records verknüpft werden, ersetzen den Requirement-Record aber nicht.
- Requirement-Records erhalten bei Erstellung Datum, Kampagne, Begründung, Actor und Änderungshistorie.
- Ein Requirement-Record wird nur additiv angelegt; ein vorhandener Record darf durch einen automatischen Extraktionslauf nicht überschrieben werden.

Damit ist die Anforderung selbst adressierbar, kommentierbar, reviewbar, renderbar und über den gesamten Weg von PDF-Evidenz bis zur dokumentierten API-Beziehung tracebar.

## Schema für Requirement-Records

Ein Requirement-Record verwendet die allgemeine Record-Struktur mit `id`, `attrs`, `blocks`, `status` und `history` und ergänzt sie um `requirement_meta`.

Empfohlenes logisches Modell:

```json
{
  "id": "SWS_LOG_00227",
  "attrs": [["class", "rec req"], ["id", "SWS_LOG_00227"]],
  "blocks": [
    { "t": "html", "html": "<h3 class=\"recname\">…</h3>" },
    {
      "t": "requirement_text",
      "text_en": "The Logging framework shall append an EOL sequence to each message in console output.",
      "status_flag": null
    },
    {
      "t": "ai",
      "kind": "comment",
      "src": "content/ai/requirements/SWS_LOG_00227/comment_01.html"
    }
  ],
  "requirement_meta": {
    "heading": "Newline addition in console output",
    "upstream": ["RS_LT_00002"],
    "status_flag": null,
    "origin": "explicit",
    "module": "log",
    "document": "AUTOSAR_AP_SWS_LogAndTrace",
    "page": 44,
    "covers": [],
    "covered_by": [],
    "trace": []
  },
  "status": {
    "state": "valid/imported",
    "reason": "scrape",
    "campaign": "2026-08-requirement-import-log"
  },
  "history": []
}
```

Die konkrete HTML-Auszeichnung darf sich weiterentwickeln. Verbindlich sind die semantischen Felder und die Herkunft des normativen Textes.

## Explizite Requirements

Ein explizites Requirement stammt unmittelbar aus einem mit eigener ID bezeichneten Standardabschnitt.

Für `requirement_meta.origin = "explicit"` gilt:

- Der Text in `requirement_text.text_en` benötigt mindestens einen direkten, starken PDF-Trace mit ID und reproduzierbarem Locator (Form A).
- Der Trace enthält mindestens Dokument, Deep-Link, ID, Seite, Extraktor-/Regelversion, extrahierten Text, Confidence und Review-Status.
- Der Status `valid/imported` bedeutet ausschließlich, dass der normativ markierte Text technisch aus dem angegebenen Standardabschnitt importiert wurde. Er bedeutet **nicht**, dass eine menschliche Inhaltsreview oder eine Implementierungsbestätigung erfolgt ist.
- Upstream-Referenzen werden als Fakten aus demselben Fundabschnitt gespeichert, wenn sie dort explizit genannt sind.
- Statusmarker wie `DRAFT` werden getrennt als `status_flag` erhalten und dürfen nicht in den Requirement-Text eingemischt werden.

Ein direkter Import soll Traceability mindestens in dieser Form erzeugen:

```json
{
  "mode": "pdf_deep_link",
  "sources": [
    {
      "kind": "pdf_deep_link",
      "document": "AUTOSAR_AP_SWS_LogAndTrace",
      "url": "…#nameddest=SWS_LOG_00227",
      "locator": "named destination SWS_LOG_00227; page 44"
    }
  ],
  "extracts": [
    "The Logging framework shall append an EOL sequence to each message in console output."
  ],
  "reasoning": "Direkt aus dem normativen, mit der ID gekennzeichneten PDF-Abschnitt extrahiert.",
  "rule": "pdf_requirement_text_between_delimiters@v1",
  "confidence": "high",
  "evidence_strength": "strong",
  "review": { "status": "accepted" }
}
```

## Implizite Requirements

Ein implizites Requirement ist keine wörtlich als eigene Anforderung im Standard vorhandene Aussage. Es wird aus vorhandener Evidenz, expliziten Requirements, API-Records, Code oder anderen zulässigen Quellen als nachvollziehbarer Kandidat abgeleitet.

Für `requirement_meta.origin = "implicit"` gilt zwingend:

- Es darf keinen Status `asserted` allein aufgrund einer KI-Generierung geben.
- `inferred_from` ist Pflicht und enthält mindestens eine Quelle oder einen stützenden Spec-Record samt Rolle und Begründung.
- Jeder Trace verwendet eine versionierte Inferenzregel, begründet die Schlussfolgerung und führt Gegen- oder Unsicherheits-Evidenz auf, sofern vorhanden.
- Die initiale Confidence darf höchstens `medium` sein, wenn keine direkte normative Formulierung existiert.
- Ohne menschliche oder regelbasierte Entscheidung bleibt der Record in einem reviewbaren Zustand, etwa `proposed/inferred`.
- Der generierte Text muss als abgeleitete Anforderung erkennbar bleiben und darf nicht als offizieller AUTOSAR-Originaltext ausgegeben werden.

Empfohlenes Modell für `inferred_from`:

```json
[
  {
    "id": "SWS_LOG_00227",
    "role": "normative-source",
    "reason": "Die explizite Anforderung setzt für Console-Output eine zeilenweise Nachrichtensemantik voraus."
  },
  {
    "id": "SWS_LOG_00046",
    "role": "implementing-api-record",
    "reason": "Der API-Record beschreibt die Ausgabeoperation, an die die abgeleitete Anforderung gebunden ist."
  }
]
```

## Coverage und Rückverfolgbarkeit

`covers` und `covered_by` bilden die fachliche Beziehung zwischen Requirements und Spec-Records ab:

- `requirement_meta.covers` verweist auf Records, deren Verhalten oder Schnittstelle durch das Requirement eingeschränkt, definiert oder erklärt wird.
- `requirement_meta.covered_by` verweist auf Records, die das Requirement implementieren, konkretisieren oder als Evidenz für dessen Umsetzung dienen.
- Jede Coverage-Kante trägt mindestens Ziel-ID, Beziehungstyp, Status, Traceability und Review-Status.
- Eine fehlende Coverage ist kein Fehler beim PDF-Import; sie zeigt zunächst nur, dass die Anforderung noch nicht auf API-, Class- oder Member-Records abgebildet wurde.
- Ein HTML-Renderer darf aus diesen Kanten Anforderungsseiten, Implementierungsübersichten und Traceability-Matrizen erzeugen.

Empfohlenes Kantenmodell:

```json
{
  "id": "SWS_LOG_00046",
  "relation": "implemented_by",
  "status": "inferred",
  "trace": [
    {
      "mode": "cross_record_inference",
      "supporting_records": [{ "id": "SWS_LOG_00227", "role": "requirement" }],
      "rule": "requirement_to_api_coverage@v1",
      "confidence": "medium",
      "review": { "status": "pending" }
    }
  ]
}
```

## KI-Kommentare zu Requirements

KI-Kommentare sind kein Teil des normativen Requirements und werden niemals in `requirement_text.text_en` gespeichert.

Stattdessen gilt:

- Kommentare werden als separater Block `t: "ai"` mit `kind: "comment"` eingebunden.
- Der Inhalt liegt unter `content/ai/requirements/<Requirement-ID>/`.
- Jeder Kommentar folgt `ai/RICHTLINIEN.md`, trägt seine Herkunft und grenzt Interpretation, Annahme und Originaltext sichtbar voneinander ab.
- Ein KI-Kommentar kann Verständnisfragen, fachliche Folgen, Implementierungsrisiken, offene Coverage oder mögliche Ableitungs-Kandidaten erläutern.
- Ein KI-Kommentar darf keine neue, scheinbar offizielle AUTOSAR-Anforderung behaupten. Entsteht aus einer Analyse ein Kandidat, wird er als separater impliziter Requirement-Record mit `origin = "implicit"` und vollständigem `inferred_from`-Argument angelegt.

## Anforderung an das Feld `parents`

Class-Records dürfen ein optionales Feld `parents` tragen.

Wenn `parents` existiert, dann gilt:

- jeder Parent-Eintrag enthält mindestens den Parent-Namen,
- jeder Parent-Eintrag enthält mindestens einen Traceability-Record,
- der Eintrag muss markieren, ob der Parent **direkt behauptet** oder **inferiert** wurde,
- bei Inferenz muss die zugrunde liegende Regel oder das Verfahren referenzierbar sein,
- bei widersprüchlicher Evidenz muss der Konflikt modelliert statt verschwiegen werden.

Empfohlenes logisches Modell:

```json
{
  "name": "ara::core::Exception",
  "status": "inferred",
  "trace": [
    {
      "mode": "cross_record_inference",
      "sources": [
        {
          "kind": "pdf_deep_link",
          "document": "SWS_DM",
          "url": "...",
          "locator": "class declaration"
        }
      ],
      "supporting_records": [
        {
          "id": "SWS_DM_00516",
          "role": "constructor"
        }
      ],
      "citations": [],
      "reasoning": "Die Klassendeklaration nennt die Basisklasse; der Konstruktor-Record bestätigt die Identität und den Scope der Klasse.",
      "rule": "class_parent_from_declaration_plus_scope_record@v1",
      "confidence": "high",
      "review": {
        "status": "accepted"
      }
    }
  ]
}
```

Die konkrete JSON-Form kann sich noch ändern; verbindlich sind die semantischen Anforderungen, nicht die exakte Schlüsselnamenswahl.

## Schwache Evidenz und informelle Spezifikationsteile

Das System muss künftig bewusst auch **informelle**, **narrative** oder **nur indirekt verwertbare** Quellenbestandteile aufnehmen können.

Dazu zählen etwa:

- erläuternde Prosa in Standards,
- nicht normierte Tabellen oder Notizen,
- UML-Diagramme,
- Code-Snippets,
- Beispielsignaturen,
- offizielle Dokumentation außerhalb der Kern-PDFs,
- Quellcode oder Header-Dateien,
- Kommentare,
- Benennungs- und Strukturkonventionen,
- implizite Beziehungen zwischen Konstruktoren, Aliasen, Members und Ownern.

Diese schwachen Belege sollen **nicht** automatisch zu Fakten erklärt werden. Sie sollen aber systematisch speicherbar sein, damit spätere Inferenz-Pipelines darauf aufbauen können.

Dafür wird zwischen mindestens drei Evidenzstärken unterschieden:

- `strong`: direkt explizit, normativ oder eindeutig deklarativ
- `medium`: formal vorhanden, aber nur indirekt eigenschaftsbildend
- `weak`: informell, kontextuell oder argumentativ verwertbar

Optional kann zusätzlich `contradicting` bzw. `negative` modelliert werden.

## Vorschlag für Schichten unterhalb der Generierung

Die bisherige Spezifikations-DB speichert primär akzeptierte Records. Für tracebare Inferenz wird mittelfristig eine feinere Trennung empfohlen:

1. **Quellenregister**
   - offizielle Standards,
   - Dokumentation,
   - Code-Repositories,
   - Header-Snapshots,
   - Versionsstände,
   - stabile IDs und Deep-Link-Muster.

2. **Evidenzspeicher**
   - atomare Beobachtungen aus Quellen,
   - mit Locator, Zitat/Extrakt, Quelle, Parser/Extractor-Version.

3. **Claim-Speicher**
   - aus Evidenz erzeugte Kandidaten,
   - inkl. Regel, Confidence, Aggregation und Konflikten.

4. **Decision-/Review-Speicher**
   - Annahme, Ablehnung, offene Fragen, Reviewer-Kommentare.

5. **Spec-Records**
   - nur akzeptierte, kanonische Fakten,
   - jeweils mit Rückverweis auf die tragenden Traceability-Records.

Die aktuelle `spec/records/`-Struktur kann zunächst weiterverwendet werden. Wichtig ist, dass das Modell semantisch bereits auf diese Trennung vorbereitet wird.

## Anforderungen an eine künftige Extraktionspipeline

Die Extraktionspipeline soll nicht nur direkt strukturierte Daten extrahieren, sondern auch Evidenz sammeln, Claims erzeugen und Inferenz nachvollziehbar machen.
Ggfs. gibt es mehrere Extraktionspipelines nebeneinander. Eine Pipeline extrahiert harte Evidenz und erstellt somit automatisch gültige Spec Records. Die andere läuft nach und benutzt vorhandene harte Evidenz als Kontext, um beim Sichten informeller Dokumentation die richtigen Schlussfolgerungen ziehen zu können. Die zweite Pipeline wird dann KI-gestützt sein und sicherlich in erster Linie Evidenz zu existierenden Spec Records beitragen. Sie kann zwar auch neue "erfinden", aber es bedarf einer dokumentierte Decision/Review, um diese dann in den Stand eines gültigen Spec Record zu heben. Diese Entscheidung muss im Spec Record nachvollziehbar dokumentiert werden.

### 1. Quellenregistrierung

Jede verarbeitete Quelle braucht:

- stabile Source-ID,
- Typ (`standard_pdf`, `official_docs`, `code`, `headers`, ...),
- Version/Release,
- Herkunftsnachweis,
- Verfahren zur Bildung stabiler Deep-Links oder Locator.

### 2. Anchor- und Locator-Extraktion

Für jede Quelle müssen präzise Referenzpunkte gewonnen werden, z. B.:

- `#nameddest`-Ziele in PDFs,
- Seitenbereiche,
- Kapitel- und Tabellenanker,
- HTML-Elemente in offizieller Online-Dokumentation,
- Symbolnamen und Quellcode-Spannen in Headern.

### 3. Evidenz-Harvesting

Nicht nur Records extrahieren, sondern alle relevanten Beobachtungen sammeln:

- Klassendeklarationen,
- Methodensignaturen,
- Membertabellen,
- Aliasdefinitionen,
- Includes und Header,
- UML-/Diagrammrelationen,
- narrative Formulierungen,
- Beispiele,
- Code- oder Header-APIs.

### 4. Entity Resolution

Namensvarianten und Fragmente müssen auf kanonische Entitäten aufgelöst werden:

- Kurzname vs. vollqualifizierter Name,
- Alias vs. eigentliche Klasse,
- Owner-/Scope-Zuordnung,
- Sprachvarianten oder abweichende Schreibweisen.

### 5. Claim-Erzeugung

Versionierte Regeln erzeugen aus Evidenz Property-Kandidaten, z. B.:

- Parent aus Klassendeklaration,
- Klassenexistenz aus Konstruktor + Scope,
- Owner-Beziehung aus Scope,
- Ergebnis-/Typbeziehungen aus Signaturen,
- semantische Rollen aus Benennung + Dokumentation,
- Beziehungen aus UML-Kanten.

### 6. Evidenz-Aggregation

Mehrere schwache oder mittlere Hinweise sollen zusammengeführt werden können. Dabei muss sichtbar bleiben:

- welche Evidenz den Claim stützt,
- welche Evidenz dagegen spricht,
- welche Regel zur Aggregation benutzt wurde,
- warum die resultierende Confidence hoch, mittel oder niedrig ist.

### 7. Review und Entscheidung

Nicht jeder Claim wird automatisch akzeptiert. Die Pipeline muss manuelle oder halbautomatische Review zulassen:

- akzeptieren,
- verwerfen,
- zurückstellen,
- als umstritten markieren,
- Begründung ergänzen.

### 8. Publikation

Nur akzeptierte Facts werden standardmäßig in die kanonischen Spec-Records gespiegelt und damit in Seiten, Indizes und Diagramme übernommen. Evidenz, Claims und Reviews bleiben darunter erhalten.

## Konkreter Anwendungsfall: Klassen und Parent-Beziehungen

Für Klassen soll die Pipeline mindestens folgende Wege unterstützen:

### Fall 1: Parent direkt in explizitem Class-Record aus Standard ableitbar

- Klassendeklaration vorhanden
- Base-Class direkt genannt
- PDF-Deep-Link verweist auf denselben normativen Ausschnitt
- Parent kann mit `status = asserted` oder `status = inferred` (je nach Modellentscheidung) gespeichert werden

### Fall 2: Klasse bisher nur implizit vorhanden

- Class-Record wird neu angelegt
- Klassenname wird aus Scope-/Seitenmodell oder Deklarationsfundstelle gewonnen
- Parent wird über Deklarations-Evidenz und mindestens einen Stützrecord inferiert
- typischer Stützrecord: Konstruktor oder Methodensignatur mit eindeutigem Klassen-Scope

### Fall 3: Parent nur aus mehreren Quellen erschließbar

- mehrere Deep-Links plus Zitate
- eine kurze prose Herleitung, warum daraus genau dieser Parent folgt
- Confidence kleiner als bei direkter Deklaration möglich
- Review besonders wichtig

## Mindestfelder für Traceability-Records

Jeder Traceability-Record soll mindestens folgende Informationen tragen können:

- `mode`
- `sources[]`
- `supporting_records[]` (optional, aber bei Inferenz wichtig)
- `citations[]` oder `extracts[]`
- `reasoning`
- `rule`
- `confidence`
- `review.status`
- `created_by` oder `pipeline_stage`
- `timestamp`

Empfohlene zusätzliche Felder:

- `evidence_strength`
- `counter_evidence[]`
- `notes`
- `reviewer`
- `decision_id`
- `supersedes`
- `extractor_version`

## Qualitätsregeln

1. **Keine stille Inferenz.** Wenn ein Wert inferiert ist, muss das sichtbar sein.
2. **Keine stille Normalisierung.** Umbenennungen, Namespace-Auflösung und Alias-Folgen zählen als Transformation und sollen nachvollziehbar bleiben.
3. **Keine zerstörende Verdichtung.** Einzelbelege dürfen nicht verloren gehen, nur weil ein Claim später akzeptiert wurde.
4. **Konflikte sichtbar halten.** Widersprechende Evidenz wird gespeichert, nicht gelöscht.
5. **Links müssen überprüfbar sein.** Deep-Links und Locator müssen maschinell validierbar oder zumindest reproduzierbar sein.
6. **Regeln versionieren.** Änderungen an Inferenzlogik müssen reproduzierbar bleiben.

## Offene Gestaltungsfragen

Diese Datei legt die Anforderungen fest. Folgende Designfragen sind bewusst noch offen und sollen iterativ entschieden werden:

- eigener Evidenzspeicher vs. direkte Einbettung in Spec-Records,
- globales Claim-/Decision-Modell vs. record-lokale Umsetzung,
- zentrale Inferenzregel-Registry,
- Umgang mit negativen oder widersprüchlichen Belegen,
- Review-Workflow und UI,
- Confidence-Skala und Freigabeschwellen,
- Versionierung über Releases und Dokumentstände hinweg,
- Unterstützung für Evidenz aus Code-Repositories und Header-Snapshots.

## Kurzfristige Umsetzungsschritte

1. Für alle Klassen eigene Class-Records einführen.
2. Ein optionales Feld `parents` samt Traceability-Struktur definieren.
3. Bestehende Fälle wie `DiagException` auf Class-Records mit Parent-Trace migrieren.
4. Deep-Link- und Locator-Schema für nicht-ID-basierte Fundstellen festlegen.
5. Erste Inferenzregel für „Parent aus Deklaration + Stützrecord“ implementieren.
6. Schwache Evidenz als speicherbares Objekt modellieren, auch wenn sie noch nicht publiziert wird.
7. Validator erweitern: kein kanonischer Fakt ohne Traceability.

## Brainstorming: mögliche Pipeline-Bausteine

Mögliche Bausteine für eine robuste Evidenz- und Inferenzpipeline:

- PDF-Parser für benannte Ziele, Kapitelstruktur, Tabellen und Syntaxblöcke,
- semantischer Segmentierer für Deklarationen, Prosa, UML und Notizen,
- Code-/Header-Indexer für Klassen, Basisklassen, Signaturen und Includes,
- linker-resolver für Deep-Links und Quellanker,
- entity-resolver für FQN, Aliase und Scope-Zuordnung,
- regelbasierter Claim-Generator,
- LLM-gestützter Kandidatengenerator für schwache Evidenz,
- Conflict-Detector,
- Review-Queue,
- Traceability-Validator,
- Publisher, der nur akzeptierte Fakten in die Record-DB schreibt.

## Normativer Status

Diese Datei ist bindend für neue Arbeiten an der Spec-DB und für die Erweiterung der Extraktionspipeline. Wo bestehende Records den Regeln noch nicht genügen, sind die Regeln Zielzustand und schrittweise nachzuziehen.
