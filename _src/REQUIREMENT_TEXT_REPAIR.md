# Reparatur von PDF-Extraktionsartefakten

Verbindlich fuer alle Requirement-Records. Ergaenzt `SPEC_TRACEABILITY.md`
und `KONVENTIONEN.md`.

## Grundsatz

Der aus dem PDF extrahierte Normtext ist Evidenz, kein Redaktionsgegenstand.
Jede Veraenderung ist deshalb eine versionierte, protokollierte Regel. Was
nicht belegbar ist, wird **nicht geraten**, sondern zum Review eskaliert.

## Drei Ebenen

### 1. Rohtext erhalten

Der Block `requirement_text` traegt immer beides:

- `text_raw` — exakt wie extrahiert, nie veraendert, nie entfernt
- `text_en` — bereinigte Fassung fuer Anzeige und Weiterverarbeitung
- `repairs` — Liste aller angewandten Regeln mit `rule`, `from`, `to`
- `suspects` — erkannte, aber bewusst nicht korrigierte Verdachtsfaelle

Ohne `text_raw` waere eine Fehlkorrektur spaeter nicht nachweisbar.

### 2. Nur beweisbare Reparaturen automatisch

Der Guard ist ein **dokumenteigenes Lexikon**: Alle Woerter des jeweiligen
PDF werden gezaehlt. Eine Reparatur gilt nur als belegt, wenn die
zusammengezogene Form im selben Dokument haeufig ungetrennt vorkommt.
Externes Woerterbuchwissen ist unzulaessig.

| Regel | Muster | Bedingung |
|---|---|---|
| `dehyphenate@v1` | `sys- tem` | `system` kommt >= 2x ungetrennt vor |
| `ligature_split@v2` | `T o`, `T race` | Zielwort >= 3x belegt, Rest nicht eigenstaendig |

`ligature_split@v2` ersetzt die frueher handgepflegte Endungsliste
(`race|emplate|ype|ime|hread|able`) in `fix_ligatures`. Einzelne Artikel
(`a`, `I`) sind per `SAFE_SINGLE` geschuetzt.

### 3. Fehlende Leerzeichen nur melden

`aLog` ist ein Artefakt, `LogStream` ein gueltiger Bezeichner. Eine
automatische Trennung waere nicht entscheidbar. Deshalb gilt:

- CamelCase-Token werden gegen die Bezeichner der Spec-DB gepruefen
- bekannte Bezeichner sind unauffaellig
- alle uebrigen landen in `suspects` und erzwingen ein Review

Die Whitelist stammt ausschliesslich aus `spec/records/`, **nicht** aus dem
PDF: Die Artefakte stehen selbst im PDF und wuerden sich sonst gegenseitig
legitimieren.

## Confidence und Review-Status

| Lage | Confidence | Review | Reason |
|---|---|---|---|
| Backends stimmen ueberein, keine Verdachtsfaelle | `high` | `accepted` | `backend_agreement` |
| Backends weichen ab | `medium` | `pending` | `backend_mismatch` |
| Nur ein Backend | `medium` | `pending` | `single_backend` |
| Verdachtsfaelle vorhanden | `medium` | `pending` | `missing_space_suspects` |

Verdachtsfaelle dominieren: Sie erzwingen ein Review auch bei
Backend-Uebereinstimmung.

## Review-Queue fuer KI-Subagenten

`spec/review-queue/` mit drei Verzeichnissen:

```
open/      offene Jobs, eine Datei je Requirement-ID
claimed/   uebernommen, Dateiname traegt die Agenten-ID
done/      abgeschlossen, revisionssicher
```

### Kollisionsfreiheit

Die Uebernahme erfolgt per `os.rename` von `open/` nach `claimed/`. Das ist
auf POSIX atomar: Bei parallelen Subagenten gewinnt genau einer, alle
anderen erhalten `None` und gehen zum naechsten Flag. Es gibt keine
Lock-Datei und keinen Zeitstempel-Vergleich, die auseinanderlaufen koennten.

### Anweisung entstammt dem Prozess

Die Flag-Datei enthaelt die Agentenanweisung, aber sie wird nicht von Hand
geschrieben, sondern in `review_flags.build_instruction()` deterministisch
aus dem Befund erzeugt. Anweisung und Datenlage koennen dadurch nicht
auseinanderlaufen. Jedes Flag traegt `schema: review-flag@v1`.

```json
{
 "schema": "review-flag@v1",
 "id": "SWS_LOG_00008",
 "reason": "missing_space_suspects",
 "confidence": "medium",
 "record": "_src/spec/records/SWS_LOG/SWS_LOG_00008.json",
 "finding": { "suspects": ["aLog", "levelFatal"], "repairs": [] },
 "instruction": {
  "goal": "Normtext von SWS_LOG_00008 verifizieren und Review-Status setzen.",
  "forbidden": ["Neuen Normtext formulieren", "text_raw veraendern"],
  "steps": ["..."]
 }
}
```

### Agenten-Ablauf

1. `list_open_flags()` liefert offene Jobs
2. `claim_flag(path, agent)` — bei `None` weitermachen, nicht warten
3. Anweisung aus dem Flag ausfuehren, Record anpassen
4. `complete_flag(path, outcome, note)` verschiebt nach `done/`
5. `release_flag(path)` bei Abbruch, damit der Job nicht verlorengeht

Das Flag wird nicht geloescht, sondern archiviert. Der Bearbeitungsverlauf
bleibt damit pruefbar.

## Messwerte SWS_LOG (R25-11, pypdf)

- 47 Prosa-Requirements extrahiert
- 28 belegte Reparaturen automatisch angewandt
- 25 Records mit Verdachtsfaellen, 22 ohne

Die Verdachtsliste enthaelt bewusst auch gueltige Modellnamen wie `logSink`
oder `LogAndTraceInterface`. Das ist gewollt: Lieber ein Review zu viel als
eine stille Falschkorrektur am Normtext.
