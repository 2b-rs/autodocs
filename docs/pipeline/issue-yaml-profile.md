# YAML-Laufzeit-, Abhängigkeits-, Sicherheits- und Serialisierungsprofil für Issue-Items

**Status:** Entwurf, review-bereit (Task `0037-02.01`, Feature `0037`). Normativ für den
Parser/Writer aus Task `0037-08` und die `issue-item@v1`-Formatdefinition (Task `0037-02`).

## 1. Ausgewählte Bibliothek und Version

| Feld | Wert |
|---|---|
| Paket | `ruamel.yaml` |
| Ausgewählte Version (zum Pinnen) | `0.18.14` (aktuelle stabile Release-Reihe zum Zeitpunkt dieses Entwurfs, 2026-08-16) |
| Unterstützte Python-Range | `>=3.7` laut Upstream-Dokumentation; dieses Repository nutzt `python3` `3.9.6` (verifiziert via `python3 --version` im Sandbox-Selbsttest), liegt also innerhalb der Range |
| YAML-Version | YAML 1.2 (Loader/Dumper-Paket, kein YAML-1.1-Fallback für diesen Vertrag) |
| Lizenz | MIT |

**Exakte Paket-Hashes:** Werden nicht in diesem Dokument fabriziert, sondern zum Zeitpunkt
des tatsächlichen Pinnens deterministisch erzeugt (`pip download`/`pip hash` bzw.
`pip-compile --generate-hashes`) und in `requirements.lock` committet. Dieses Dokument
schreibt nur *dass* `requirements.lock` Hashes für `ruamel.yaml==0.18.14` (und dessen
Build-Abhängigkeiten) enthalten muss, nicht deren Zahlenwert — das Toolchain-Provisioning
in Task `0037-39` erzeugt und verifiziert sie ausführbar.

**Referenzquellen:** PyPI-Projektseite `ruamel.yaml` [web:100], Release-Historie via
`libraries.io` [web:113], Duplicate-Key-Verhalten der `ruyaml`/`ruamel.yaml`-Nachfolge-API
[web:106].

## 2. Root-Deklaration

- `pyproject.toml` (Repository-Root) deklariert `ruamel.yaml==0.18.14` als exakte Version
  unter `[project.dependencies]` (kein Bereichsoperator).
- `requirements.lock` (Repository-Root) enthält die vollständige transitive
  Abhängigkeitskette mit Hashes, erzeugt durch einen deterministischen Lock-Lauf.
- Beide Dateien sind Teil der Toolchain-Provisionierung (Task `0037-39`) und werden dort
  ausführbar verifiziert (Import, Versionscheck).

## 3. API-Modus

Der Parser verwendet ausschließlich den **`typ='safe'`**-Modus der neuen API
(`YAML(typ='safe')`), niemals `typ='rt'` (round-trip) oder `typ='unsafe'`, für
**Parsing/Validierung**. Ein separater, eng begrenzter **kontrollierter Writer** (§6) nutzt
den Round-Trip-Modus (`typ='rt'`) ausschließlich, um benannte strukturierte Abschnitte
(Frontmatter) gezielt umzuschreiben, ohne umgebenden Markdown-Text zu berühren.

## 4. Abgelehnte Konstrukte (sicherheitskritisch, harter Parser-Fehler)

Der Parser lehnt jedes der folgenden Konstrukte mit einem harten, spezifischen Fehler ab —
niemals mit stillschweigendem Überschreiben oder Best-Effort-Verhalten:

| Konstrukt | Ablehnung, Begründung |
|---|---|
| Doppelte Mapping-Schlüssel | `yaml.allow_duplicate_keys` bleibt `False` (Default seit `ruyaml`/`ruamel.yaml` ≥0.15.1); YAML 1.2 fordert eindeutige Schlüssel [web:106] |
| Aliase/Anker (`&anchor`, `*alias`) | Erlauben verdeckte Datenverdopplung/-mutation und erschweren deterministisches Diffen; abgelehnt für alle Issue-Item-Eingaben |
| Merge-Keys (`<<:`) | Verdecken die tatsächliche, geschriebene Struktur; abgelehnt |
| Custom-Tags (`!irgendwas`) | Erlauben beliebige Python-Objektkonstruktion außerhalb von `safe`; im `safe`-Modus bereits strukturell ausgeschlossen, zusätzlich explizit geprüft |
| Mehrere Dokumente in einem Stream (`---` mehrfach) | Ein Issue-Item ist exakt ein Dokument; mehrere Dokumente sind ein Formatfehler |
| Nicht-String-Mapping-Schlüssel (Zahlen, Booleans, verschachtelte Strukturen als Schlüssel) | Front-Matter-Schema erfordert String-Schlüssel für deterministisches JSON-Schema-Mapping |
| Implizite Timestamps (unquotiertes `2026-08-16`) | Mehrdeutig zwischen String und Datumstyp je Loader-Konfiguration; müssen quotiert sein (§5) |
| Nicht-endliche Zahlen (`.inf`, `-.inf`, `.nan`) | Kein sinnvoller Anwendungsfall in Issue-Metadaten; Ablehnung verhindert stille Fehlausbreitung |
| NUL-/Steuerzeichen im Text | Verhindert Injektion nicht darstellbarer Bytes in committete Markdown-/YAML-Dateien |
| Übermäßige Aliase/Verschachtelungstiefe/Byte-Größe | Denial-of-Service-Schutz (YAML-Bombe); konkrete Limits: max. Verschachtelungstiefe 20, max. Dokumentgröße 1 MiB, 0 erlaubte Aliase (da Aliase generell abgelehnt werden, §4) |
| Mehrdeutige Booleans/Nulls (`yes`, `no`, `on`, `off`, `~` als Freitext) | YAML-1.1-Erbe, das YAML 1.2 nicht mehr als Bool/Null interpretiert; Eingaben müssen `true`/`false`/leer verwenden, um Missverständnisse zu vermeiden |

## 5. Kanonisches Serialisierungsformat

| Regel | Wert |
|---|---|
| Zeichenkodierung | UTF-8, ohne BOM |
| Zeilenenden | LF (`\n`), niemals CRLF |
| Schlüsselreihenfolge | Deklarationsreihenfolge im Schema (`issues/_schema/`), nicht alphabetisch; Writer erhält die Schema-Reihenfolge |
| Einrückung | Zwei Leerzeichen pro Ebene, keine Tabs |
| Timestamps | Immer quotiert (`"2026-08-16"`), niemals implizit typisiert (§4) |
| Abschließender Zeilenumbruch | Genau ein `\n` am Dateiende, kein zusätzlicher leerer Block |
| Frontmatter-Begrenzer | `---` als öffnende und schließende Zeile, exakt wie in `issue-store.md` §4 referenziert |

## 6. Kontrollierte Writer — Scope-Beschränkung

Writer dürfen **ausschließlich** folgende Regionen einer `index.md`-Datei umschreiben:

- Den YAML-Frontmatter-Block zwischen den beiden `---`-Begrenzern.
- Benannte, im Schema deklarierte strukturierte Markdown-Abschnitte (z. B. eine
  `## Acceptance criteria`-Liste mit stabilen `AC-NNN`-IDs, sobald Task `0037-02.02` deren
  exaktes Markup definiert).

Alle anderen Bytes (Prosa, Überschriften auu00dferhalb deklarierter Abschnitte,
freie Fußnoten) bleiben byteidentisch erhalten. Ein Writer, der eine Änderung außerhalb
dieser Regionen feststellt, muss mit einem harten Fehler abbrechen statt die Änderung zu
übernehmen oder zu verwerfen.

## 7. Verhältnis zu `issue-store.md`

Dieses Dokument definiert **wie** YAML innerhalb eines Issue-Items geparst/geschrieben wird.
`docs/pipeline/issue-store.md` definiert **wo** Issue-Items liegen und wer sie schreiben darf.
Die vollständige `issue-item@v1`-Feldliste (welche Frontmatter-Felder existieren) ist
Gegenstand des übergeordneten Tasks `0037-02` und der Subtasks `0037-02.02`/`0037-02.03`.

## 8. Fixtures (Pflicht für Definition of Done)

Ausführbare Probe-Fixtures unter `issues/_schema/fixtures/yaml-profile/`, jede mit einer
deklarierten erwarteten Entscheidung (`accept`/`reject`) und Begründung als Kommentarzeile.
Diese Fixtures führen **keine** produktive Parser-Logik ein — sie sind Eingabedaten für einen
späteren Test-Harness (Task `0037-08`ff.), nicht ausführbarer Code selbst:

| Fixture | Erwartung |
|---|---|
| `accept-minimal-valid.yaml` | `accept` — minimales gültiges Frontmatter, alle Regeln aus §5 erfüllt |
| `reject-duplicate-key.yaml` | `reject` — doppelter Schlüssel `id` |
| `reject-alias.yaml` | `reject` — enthält `&anchor`/`*alias` |
| `reject-merge-key.yaml` | `reject` — enthält `<<:`-Merge |
| `reject-multi-document.yaml` | `reject` — zwei `---`-getrennte Dokumente |
| `reject-non-string-key.yaml` | `reject` — numerischer Mapping-Schlüssel |
| `reject-implicit-timestamp.yaml` | `reject` — unquotiertes Datum als Wert |
| `reject-non-finite-number.yaml` | `reject` — `.inf`-Wert |
| `reject-control-character.yaml` | `reject` — eingebettetes NUL-Byte (als Escape-Kommentar dokumentiert, da NUL nicht direkt in eine `.yaml`-Textdatei eingebettet werden kann) |
| `reject-ambiguous-boolean.yaml` | `reject` — `yes`/`no` als Freitext statt `true`/`false` |
| `reject-excessive-depth.yaml` | `reject` — Verschachtelungstiefe > 20 |

## 9. Offene Anschlusspunkte

- Vollständige Feldliste und Markdown-Profil: Task `0037-02.02`.
- Ausführbare normalisierte Objektschemata: Task `0037-02.03`.
- Toolchain-Provisionierung (`pyproject.toml`, `requirements.lock` mit echten Hashes,
  ausführbare Verifikation): Task `0037-39`.
