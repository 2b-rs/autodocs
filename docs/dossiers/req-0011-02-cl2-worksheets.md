# Requirements & Method — Automotive SPICE CL2 Assessment Extension and Worksheets (`0011-02`)

**Item:** Task `0011-02` of Feature `0011`
**Prerequisites:** `0011-01`, `0020-07`
**Bound Decisions & Context:** `DEC-0020-001`, `DEC-0020-002`, `REQ-0020-02-01`..`09`, `REQ-0020-07-01`..`09`
**Capability class:** `unprivileged`
**Confidentiality:** `internal`

---

## 1. Zweck und Geltungsbereich (Purpose & Scope)

Dieses Dokument erweitert die genehmigte Level-1-Assessment-Methode und Worksheet-Struktur (`docs/dossiers/req-0020-07-level-1-worksheets.md` und `docs/pipeline/aspice-cl2-assessment-input.md`) für **Automotive SPICE Capability Level 2 (CL2)**.
Es etabliert **keine parallele Assessment-Methode** und dupliziert keine Level-1-Outcome-Worksheets, sondern erweitert das bestehende 14-Prozess-Framework nahtlos um:
- Die Prozessattribute **PA 2.1 (Performance Management)** und **PA 2.2 (Work Product Management)**,
- Aggregations- und Rating-Regeln für CL2 (`PA 2.1 >= L` und `PA 2.2 >= L`),
- Anforderungen an Assessor-Kompetenz und organisatorische Unabhängigkeit,
- Striktes Refusal-at-Use für nicht-authentische Origins gemäß `DEC-0020-002` und `REQ-0020-02-01..09`,
- Gliederung und Inhalte des formalen CL2 Assessment Reports.

Der Assessment-Gegenstand ist gemäß `DEC-0020-001` die virtuelle Automotive-ECU-Software ohne Kernel (`product_id=virtualized-automotive-ecu`, `project_id=autodocs-ecu-software`, `increment=software-without-kernel`).

---

## 2. Abgedeckte Prozesse (14-Prozess-Nukleus)

Die Bewertung auf CL2 erfolgt für dieselben 14 Prozessinstanzen, die im Level-1-Nukleus definiert sind:
1. `SWE.1` Software Requirements Analysis (`SWE.1-sw-nokernel-1`)
2. `SWE.2` Software Architectural Design (`SWE.2-sw-nokernel-1`)
3. `SWE.3` Software Detailed Design and Unit Construction (`SWE.3-sw-nokernel-1`)
4. `SWE.4` Software Unit Verification (`SWE.4-sw-nokernel-1`)
5. `SWE.5` Software Integration and Integration Testing (`SWE.5-sw-nokernel-1`)
6. `SWE.6` Software Qualification Testing (`SWE.6-sw-nokernel-1`)
7. `MAN.3` Project Management (`MAN.3-sw-nokernel-1`)
8. `MAN.5` Risk Management (`MAN.5-sw-nokernel-1`)
9. `MAN.6` Measurement (`MAN.6-sw-nokernel-1`)
10. `SUP.1` Quality Assurance (`SUP.1-sw-nokernel-1`)
11. `SUP.8` Configuration Management (`SUP.8-sw-nokernel-1`)
12. `SUP.9` Problem Resolution Management (`SUP.9-sw-nokernel-1`)
13. `SUP.10` Change Request Management (`SUP.10-sw-nokernel-1`)
14. `SPL.2` Product Release (`SPL.2-sw-nokernel-1`)

Ausschlüsse: Kernel/OS/HWE/MLE/SYS/VAL Prozesse bleiben für dieses Inkrement out-of-scope (`REQ-0020-04-04..05`, `REQ-0020-07-01`).

---

## 3. Normative Anforderungen für CL2 (`REQ-0011-02-01`..`08`)

### `REQ-0011-02-01` — Erweiterung der Level-1 Worksheets um PA 2.1 und PA 2.2
- **Beschreibung:** Jedes Prozess-Worksheet muss für die jeweilige Prozessinstanz Bewertungsfelder für PA 1.1 (Base Practices / Outcomes), PA 2.1 (Generic Practices 2.1.1–2.1.6) und PA 2.2 (Generic Practices 2.2.1–2.2.4) bereitstellen.
- **Akzeptanz:** Es existiert eine einheitliche Worksheet-Struktur, die CL1-Outcomes mit den CL2-Prozessattributen integriert.

### `REQ-0011-02-02` — CL2 Aggregations- und Rating-Regel
- **Beschreibung:** Ein Prozess erreicht Capability Level 2 (CL2) genau dann, wenn:
  - `PA 1.1 >= L` (Largely oder Fully achieved),
  - `PA 2.1 >= L` (Largely oder Fully achieved),
  - `PA 2.2 >= L` (Largely oder Fully achieved).
- **Akzeptanz:** Wenn eines der Attribute mit `N` (Not achieved) oder `P` (Partially achieved) bewertet wird, wird für diesen Prozess maximal CL1 (falls `PA 1.1 >= L`) bzw. CL0 ausgewiesen.

### `REQ-0011-02-03` — Verbot von Mittelwertbildung und opportunistischer Aggregation
- **Beschreibung:** Die Bewertung erfolgt rein prozessinstanzbezogen. Es darf keine Durchschnittsbildung über mehrere Prozesse stattfinden. Nachweise dürfen nicht über verschiedene Produkte, Projekte oder Baselines vermischt werden (`REQ-0020-05`, `REQ-0020-07-03`).

### `REQ-0011-02-04` — Nachweisvalidierung und Ausschluss von Substitution (`DEC-0020-002`)
- **Beschreibung:** Für PA 2.1- und PA 2.2-Nachweise gilt das verbindliche Metadatenschema (`product_id`, `project_id`, `process_id`, `process_instance_id`, `baseline_id`, `revision`, `owner`, `origin`, `validity`, `retention`, `confidentiality`).
- **Refusal-at-Use:** Nachweise mit Origin `documentation-execution` (z.B. Feature 0019) oder `controlled-scenario` dürfen nicht als Nachweis für reale ECU-Prozessdurchführung (`ecu-execution`) gewertet werden (`REQ-0020-02-03..07`).

### `REQ-0011-02-05` — Assessor-Kompetenz und Unabhängigkeit
- **Beschreibung:** Das Assessment erfordert einen zertifizierten Competent/Lead Assessor (z.B. intacs™ ASPICE PAM 3.1/4.0). Der Assessor muss unabhängig von den Entwicklern der bewerteten Instanzen sein. Solange kein Assessor benannt ist, lautet das Feld `not-named` (`REQ-0020-07-04`).

### `REQ-0011-02-06` — Generic Practices Mapping für PA 2.1 (Performance Management)
Die Erfüllung von PA 2.1 erfordert objektive Nachweise für:
- **GP 2.1.1 (Process Objectives):** Definierte Leistungsziele für den Prozess.
- **GP 2.1.2 (Process Planning & Monitoring):** Integrierte Ablauf- und Ressourcenplanung sowie laufendes Monitoring.
- **GP 2.1.3 (Process Adjustment):** Steuerungsmaßnahmen und Plananpassungen bei Abweichungen.
- **GP 2.1.4 (Responsibilities & Authorities):** Zugewiesene und kommunizierte Rollen und Befugnisse.
- **GP 2.1.5 (Resources & Information):** Bereitgestellte und genutzte Arbeitsmittel, Tools und Daten.
- **GP 2.1.6 (Interfaces & Communication):** Definierte Schnittstellen und Informationsflüsse zwischen Beteiligten.

### `REQ-0011-02-07` — Generic Practices Mapping für PA 2.2 (Work Product Management)
Die Erfüllung von PA 2.2 erfordert objektive Nachweise für:
- **GP 2.2.1 (Work Product Requirements):** Definierte Anforderungen an Struktur und Inhalt der Arbeitsergebnisse.
- **GP 2.2.2 (Documentation & Control Requirements):** Definierte Vorgaben für Identifikation, Versionierung, Speicherung und Freigabe.
- **GP 2.2.3 (Work Product Identification & Control):** Praktische Umsetzung der Konfigurationskontrolle, Ablage und Traceability.
- **GP 2.2.4 (Work Product Review & Verification):** Durchführung von Reviews/Verifikationen gegen Qualitätskriterien und Behebung von Mängeln.

### `REQ-0011-02-08` — Report Content & Abgrenzung
- **Beschreibung:** Der finale Assessment-Report muss Scope, Instanzen, Nachweisregister, detaillierte Bewertungen für PA 1.1, PA 2.1, PA 2.2 sowie Findings enthalten. Er muss explizit klarstellen, dass das PAM 4.0 Assessment kein Nachweis nach ISO/SAE 21434 oder ISO 26262 ist (`REQ-0020-06`, `REQ-0020-07-07`).

---

## 4. CL2 Prozess-Worksheet Template (Erweiterung des Level-1 Worksheets)

Für jede der 14 Prozessinstanzen (`<process>-sw-nokernel-1`):

```markdown
### Prozess-Worksheet: [PROCESS_ID] — [PROCESS_NAME]
- **Instanz:** [PROCESS_ID]-sw-nokernel-1
- **Produkt:** virtualized-automotive-ecu (`project_id=autodocs-ecu-software`, `increment=software-without-kernel`)
- **Verantwortung:** internal (Software oberhalb des Kernels)
- **Lead Assessor:** [not-named] | **Unabhängigkeit bestätigt:** [Ja/Nein/not-named]

#### 1. Level-1 Base Practices & Outcomes (PA 1.1)
| Practice / Outcome | Validierte Evidenz (ID, Rev, Origin, Baseline) | Interview / Beobachtung | Bewertung (N/P/L/F) | Schwächen / Findings |
|---|---|---|---|---|
| Outcome 1 | ... | ... | [blank] | ... |
| Outcome 2 | ... | ... | [blank] | ... |
| ... | ... | ... | [blank] | ... |
**PA 1.1 Rating & Rationale:** [blank bis 0025] (CL1 erfordert PA 1.1 >= L)

#### 2. Level-2 Process Attribute 2.1: Performance Management
| Generic Practice | Validierte Evidenz (`ecu-execution`) | Bewertung (N/P/L/F) | Findings / Rationale |
|---|---|---|---|
| GP 2.1.1 Process Performance Objectives | ... | [blank] | ... |
| GP 2.1.2 Process Planning & Monitoring | ... | [blank] | ... |
| GP 2.1.3 Process Adjustment | ... | [blank] | ... |
| GP 2.1.4 Responsibilities & Authorities | ... | [blank] | ... |
| GP 2.1.5 Resources & Information | ... | [blank] | ... |
| GP 2.1.6 Interfaces & Communication | ... | [blank] | ... |
**PA 2.1 Rating & Rationale:** [blank bis 0025]

#### 3. Level-2 Process Attribute 2.2: Work Product Management
| Generic Practice | Validierte Evidenz (`ecu-execution`) | Bewertung (N/P/L/F) | Findings / Rationale |
|---|---|---|---|
| GP 2.2.1 Work Product Requirements | ... | [blank] | ... |
| GP 2.2.2 Storage & Control Requirements | ... | [blank] | ... |
| GP 2.2.3 Identification & Control | ... | [blank] | ... |
| GP 2.2.4 Review & Verification | ... | [blank] | ... |
**PA 2.2 Rating & Rationale:** [blank bis 0025]

#### 4. Gesamteinstufung Prozessinstanz (CL0 / CL1 / CL2)
- **PA 1.1:** [blank] | **PA 2.1:** [blank] | **PA 2.2:** [blank]
- **Erreichtes Capability Level:** [blank bis 0025]
- **CL2 Regel:** CL2 wird nur vergeben, wenn PA 1.1 >= L UND PA 2.1 >= L UND PA 2.2 >= L.
```

---

## 5. Offene Entscheidungen & Ausschlüsse

- **Offene Entscheidungen:** Benennung des konkreten Lead Assessors (`PD-0020-07-01`) sowie Festlegung konkreter Stichproben (`PD-0020-07-02`).
- **Ausschlüsse:** Das Ausfüllen konkreter Ratings (`N/P/L/F`) bleibt späteren Assessment-Durchführungs-Tasks (`0025`) vorbehalten. Dieses Dossier führt keine vorzeitigen Capability-Claims ein.
