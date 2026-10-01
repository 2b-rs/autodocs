# Dossier: 0007-02 Record Shape Resolution & RS_LT Numbered-Subsection Analysis

- **Item ID:** `0007-02`
- **Feature:** Feature 0007 (Spec Extraction Truth Set / Benchmark)
- **Status:** Complete / Verified
- **Authority Reference:** `local-20260815-0007-02`

---

## 1. Goal & Objective

Resolve the claimed "dense-definition-list / inline-heading without marker" record shape from concrete source evidence and ensure the verified `RS_LT` numbered-subsection variant in `AUTOSAR_FO_RS_LogAndTrace` is retained as a distinct, first-class shape in the extraction taxonomy.

---

## 2. Source Evidence & Investigation Findings

### 2.1 Investigation of `RS_PHM_00001..00003` (`AUTOSAR_AP_RS_PlatformHealthManagement.pdf`)
- **Source Locators:** `AUTOSAR_AP_RS_PlatformHealthManagement.pdf` (R25-11), Page 21, Appendix A.3.3.
- **Findings:**
  - The IDs `RS_PHM_00001`, `RS_PHM_00002`, and `RS_PHM_00003` were removed in release R24-11 and do not exist as live requirement definitions in R25-11.
  - On page 21, they appear exclusively within the Appendix table "A.3.3 Deleted Requirements in R24-11", a standard `Number Heading` change-history table identical to other Added/Changed/Deleted appendix structures.
  - They do **not** represent a new "dense definition list, inline heading, no marker" shape.
  - In `_src/tests/fixtures/spec_extraction/negative-history.json`, all three IDs are explicitly categorized as `expected: not_definition` with `reason: history_only`.
- **Verdict:** The hypothetical "dense definition list" shape without markers is unsupported by live specification evidence and is retired.

### 2.2 Retention of the Verified `RS_LT` Numbered-Subsection Shape (`AUTOSAR_FO_RS_LogAndTrace.pdf`)
- **Source Locators:** `AUTOSAR_FO_RS_LogAndTrace.pdf`, e.g., requirements `RS_LT_00001` through `RS_LT_00037`.
- **Layout Specification:**
  - In `AUTOSAR_FO_RS_LogAndTrace`, requirement titles are rendered in the numbered subsection line immediately preceding the `[RS_LT_xxxxx]` tag:
    ```
    4.2.1.1.8 The LT shall transmit log and trace messages ...
    [RS_LT_00001]
    ```
  - `_src/tools/spec_scrape.py` enforces this through the dedicated fallback pattern:
    ```python
    SUBSECTION_HEADING_RE = re.compile(r"^\d+(?:\.\d+)+\s+(.*\S)$")
    ```
  - This pattern correctly binds the subsection title without capturing unrelated running headers, footers, or non-definition prose.
- **Verdict:** The `RS_LT` numbered-subsection variant is retained as a distinct, verified shape category in the extraction toolchain.

---

## 3. Verification & Test Evidence

- **Regression Test Suites:**
  - `pytest _src/tests/test_spec_extraction_campaign.py _src/tests/test_spec_extraction_benchmark.py`
  - **Result:** `16 passed in 1.10s (100% OK)`
- **Negative History Coverage:**
  - Negative history assertions in `_src/tests/fixtures/spec_extraction/negative-history.json` prevent change-history table entries from being misclassified as requirement definitions.
