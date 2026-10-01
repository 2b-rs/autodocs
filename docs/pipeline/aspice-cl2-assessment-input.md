# ASPICE CL2 Assessment Input and Worksheets Scaffolding

**Referenz:** `DEC-0020-001`, `DEC-0020-002`, `REQ-0020-02-01`..`09`, `REQ-0020-07-01`..`09`
**Zieldatum:** [MANAGEMENT_PARAMETER: Zieldatum_Assessment]
**Lead Assessor Name:** [MANAGEMENT_PARAMETER: Assessor_Name]
**Co-Assessor Name:** [MANAGEMENT_PARAMETER: Co_Assessor_Name]
**Confidentiality:** `internal`

---

## 1. Scope / Assessment-Gegenstand

Entsprechend der Managemententscheidung (`DEC-0020-001`) und dem Prozessmodell umfasst der Assessment-Gegenstand:
- **Produkt/Variante:** Virtualized Automotive ECU (`product_id=virtualized-automotive-ecu`)
- **Projekt:** `autodocs-ecu-software` (`project_id=autodocs-ecu-software`)
- **Inkrement / Baseline:** `software-without-kernel` (`increment=software-without-kernel`) — System- und Applikationssoftware oberhalb des Kernels. Der Kernel befindet sich noch in Entwicklung und wird später hinzugefügt.
- **Ausschluss:** Kernel, OS, Hardware- und Fertigungsprozesse (`HWE.1`–`HWE.4`), Machine Learning Engineering (`MLE.1`–`MLE.4`), komplettes ECU-System-Lifecycle (`SYS.1`–`SYS.5`, `VAL.1`), `ACQ.4`, `SUP.11`, `PIM.3`, `REU.2` sowie vollständige CS/FS-Nachweise nach ISO/SAE 21434 oder ISO 26262 sind im aktuellen Inkrement nicht enthalten (`REQ-0020-06`, `REQ-0020-07-07`).
- **Verbindliche Claim-Formulierung (`DEC-0020-001`):** *„Wir entwickeln ausschließlich System- und Applikationssoftware für ein virtualisiertes Automotive-Steuergerät. Der Kernel befindet sich noch in Entwicklung und wird später hinzugefügt.“*

---

## 2. Prozessauswahl (14-Prozess-Nukleus für CL2)

Das Assessment nach ASPICE (PAM 3.1 / PAM 4.0) erweitert die 14 ausgewählten Prozesse des genehmigten Level-1-Nukleus (`REQ-0020-04-03`, `REQ-0020-07-01`) einheitlich auf Capability Level 2 (CL2):

### Software Engineering Prozesse (SWE)
- `SWE.1` Software Requirements Analysis (Instance: `SWE.1-sw-nokernel-1`)
- `SWE.2` Software Architectural Design (Instance: `SWE.2-sw-nokernel-1`)
- `SWE.3` Software Detailed Design and Unit Construction (Instance: `SWE.3-sw-nokernel-1`)
- `SWE.4` Software Unit Verification (Instance: `SWE.4-sw-nokernel-1`)
- `SWE.5` Software Integration and Integration Testing (Instance: `SWE.5-sw-nokernel-1`)
- `SWE.6` Software Qualification Testing (Instance: `SWE.6-sw-nokernel-1`)

### Management & Support Prozesse
- `MAN.3` Project Management (Instance: `MAN.3-sw-nokernel-1`)
- `MAN.5` Risk Management (Instance: `MAN.5-sw-nokernel-1`)
- `MAN.6` Measurement (Instance: `MAN.6-sw-nokernel-1`)
- `SUP.1` Quality Assurance (Instance: `SUP.1-sw-nokernel-1`)
- `SUP.8` Configuration Management (Instance: `SUP.8-sw-nokernel-1`)
- `SUP.9` Problem Resolution Management (Instance: `SUP.9-sw-nokernel-1`)
- `SUP.10` Change Request Management (Instance: `SUP.10-sw-nokernel-1`)
- `SPL.2` Product Release (Instance: `SPL.2-sw-nokernel-1`)

---

## 3. Capability Level 2 Attribute (PA 2.1 & PA 2.2)

Für jeden der 14 Prozesse werden zusätzlich zu den Level-1 Base Practices (PA 1.1) die folgenden Prozessattribute für CL2 bewertet:

### PA 2.1: Performance Management
- **PA 2.1 Practice 1:** Objectives for the performance of the process are identified.
- **PA 2.1 Practice 2:** Performance of the process is planned and monitored.
- **PA 2.1 Practice 3:** Performance of the process is adjusted to meet plans and objectives.
- **PA 2.1 Practice 4:** Responsibilities and authorities for performing the process are defined, allocated, and communicated.
- **PA 2.1 Practice 5:** Resources and information necessary for performing the process are identified, made available, allocated, and used.
- **PA 2.1 Practice 6:** Interfaces between involved parties are managed to ensure effective communication and clear assignment of responsibility.

### PA 2.2: Work Product Management
- **PA 2.2 Practice 1:** Requirements for the work products of the process are defined.
- **PA 2.2 Practice 2:** Requirements for documentation and control of the work products are defined (identification, traceability, storage, approval).
- **PA 2.2 Practice 3:** Work products are appropriately identified, stored, and controlled in accordance with defined requirements.
- **PA 2.2 Practice 4:** Work products are reviewed or verified against requirements and adjusted as necessary.

---

## 4. Bewertungsregeln, Aggregation und Einstufungsrationale (CL2 Aggregation / Rating Rules)

### 4.1 N-P-L-F Rating-Skala
Gemäß ISO/IEC 33020 / ASPICE PAM:
- **N (Not achieved):** 0% bis 15%
- **P (Partially achieved):** >15% bis 50%
- **L (Largely achieved):** >50% bis 85%
- **F (Fully achieved):** >85% bis 100%

### 4.2 Aggregations- und CL2-Einstufungsregeln
1. **CL1 Voraussetzung:** Ein Prozess erreicht CL1 nur dann, wenn `PA 1.1` mindestens mit `L` oder `F` bewertet wurde (`REQ-0020-07-06`).
2. **CL2 Einstufung:** Ein Prozess erreicht **Capability Level 2 (CL2)** genau dann, wenn:
   - `PA 1.1 >= L` (Level 1 erreicht) **UND**
   - `PA 2.1 >= L` (Performance Management weitgehend/vollständig erreicht) **UND**
   - `PA 2.2 >= L` (Work Product Management weitgehend/vollständig erreicht).
3. **Keine Mittelwertbildung über Prozesse:** Aggregation und Rating erfolgen strikt per benannter Prozessinstanz. Eine Mittelwertbildung über unterschiedliche Prozesse hinweg ist unzulässig (`REQ-0020-07-03`).
4. **Verbot der opportunistischen Aggregation:** Eine Prozessinstanz darf nicht aus gemischten `product_id`, `project_id`, `process_instance_id` oder `baseline_id` zusammengestellt werden (`REQ-0020-05`).

---

## 5. Nachweisvalidierung und Ausschluss von Substitutionen (`DEC-0020-002`, `REQ-0020-02-01..09`)

### 5.1 Kanonische Ursprungsklassifikation (Origin Set)
Jeder Nachweis muss zwingend genau einen kanonischen Ursprung aus der geschlossenen Menge tragen:
- `process-definition`: Prozessrichtlinien, Methoden, Templates.
- `implemented-mechanism`: Automatisierte Werkzeuge, Schemata, Validatoren, Repository-Gating.
- `documentation-execution`: Nachweise aus reinen Dokumentations-/Extraktionsläufen (z.B. Feature `0019`).
- `ecu-execution`: Authentische Ausführungsnachweise aus der genehmigten ECU-Software-Entwicklung (`product_id=virtualized-automotive-ecu`).
- `controlled-scenario`: Synthetische Tests, Fixtures oder Rehearsals.

### 5.2 Refusal at Use / Keine Substitution
- **Verbot von Substituten:** Für die Bewertung von `PA 1.1`, `PA 2.1` und `PA 2.2` der ECU-Software dürfen ausschließlich Nachweise mit Origin `ecu-execution` (bzw. für allgemeine Prozessvorgaben `process-definition` und `implemented-mechanism` in ihrer jeweiligen Rolle) herangezogen werden.
- `documentation-execution`, `controlled-scenario` sowie Fremd-Artefakte dürfen **nicht** als Nachweis für reale ECU-Prozessdurchführung verwendet werden (`DEC-0020-002`, `REQ-0020-02-03`, `REQ-0020-02-06`, `REQ-0020-02-07`).
- Nachweise aus Kernel-, Hardware- oder Gesamtsystemumfängen werden für dieses Inkrement abgewiesen (`REQ-0020-02-08`).
- Interviews dienen der Verifikation und Kontextualisierung, ersetzen aber keine fehlenden objektiven Artefakte (`REQ-0020-07-02`).

### 5.3 Pflicht-Metadaten pro Nachweis
Jedes eingereichte Artefakt muss folgende Metadaten vollständig aufweisen:
- `product_id`: `virtualized-automotive-ecu`
- `project_id`: `autodocs-ecu-software`
- `process_id`: (z.B. `SWE.1`)
- `process_instance_id`: (z.B. `SWE.1-sw-nokernel-1`)
- `baseline_id`: (z.B. `software-without-kernel-v1`)
- `revision`: Version / Commit SHA
- `owner`: Verantwortliche Person / Rolle
- `origin`: Genau ein kanonischer Origin-Wert
- `validity`: Gültigkeitsstatus (z.B. `valid`)
- `retention`: Aufbewahrungsdauer / Pfad
- `confidentiality`: Einstufung (mindestens `internal`)

---

## 6. Assessor-Kompetenz und Unabhängigkeit (`REQ-0020-07-04`)

- **Kompetenznachweis:** Das Assessment darf nur durch zertifizierte Assessoren (z.B. intacs™ Certified Lead Assessor / Competent Assessor für ASPICE PAM 3.1 / PAM 4.0) mit nachgewiesener Erfahrung im Automotive-Software-Engineering durchgeführt werden.
- **Unabhängigkeit:** Der Lead Assessor und das Assessment-Team müssen organisatorisch und disziplinarisch unabhängig von den Entwicklern/Performern der bewerteten Prozessinstanzen sein.
- **Status bis zur Benennung:** Solange kein namentlicher Assessor bestellt ist, wird der Status mit `not-named` geführt. Bis zur formalen Durchführung und Gegenzeichnung durch den Assessor gilt das Dokument als Worksheet/Scaffolding und nicht als abgeschlossenes Assessment. Management-Waiver ersetzen keine Assessor-Benennung.

---

## 7. Aufbau des Assessment-Reports (Report Content Scaffolding)

Der finale CL2 Assessment Report muss zwingend folgende Bestandteile enthalten:
1. **Assessment-Identifikation & Scope:** Verbatim Scope-Statement (`DEC-0020-001`), Zieldatum, Sponsoren, Lead Assessor und Team.
2. **Prozessumfang & Instanzen:** Die 14 benannten Prozessinstanzen mit Rollen- und Verantwortlichkeitsabgrenzung.
3. **Assessment-Methode:** Bewertungsregeln nach ASPICE PAM 4.0 / ISO/IEC 33020, N-P-L-F Ratingkriterien, Evidenzprüfpfade.
4. **Validierte Evidenzbasis:** Nachweisregister mit `0020-02`-Metadaten und Bestätigung des Ausschlusses nicht-authentischer Origins.
5. **Detaillierte Prozessbewertungen:**
   - Level 1 Outcome & PA 1.1 Rationale
   - Level 2 PA 2.1 Performance Management Bewertung (GP 2.1.1–2.1.6)
   - Level 2 PA 2.2 Work Product Management Bewertung (GP 2.2.1–2.2.4)
   - Festgestellte Stärken, Schwächen, Risiken und Abweichungen (Findings / Non-Conformances)
6. **Capability Level Profil (CL0 bis CL2):** Tabellarische und grafische Übersicht der erreichten Prozessreifegrade.
7. **Haftungsausschluss / Normenabgrenzung:** Ausdrücklicher Hinweis, dass das ASPICE PAM 4.0 Assessment keinen Ersatz oder formalen Nachweis für ISO/SAE 21434 (Cybersecurity) oder ISO 26262 (Funktionale Sicherheit) darstellt (`REQ-0020-06`, `REQ-0020-07-07`).
8. **Vertraulichkeitsvermerk & Freigabe:** Einstufung `internal`, Unterschriften Lead Assessor und Management-Sponsor.
