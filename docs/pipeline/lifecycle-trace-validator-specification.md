# Standalone Lifecycle Traceability Graph Validator Specification (0022-02.02)

## 1. Document Control & Tool Metadata
- **Tool Identifier**: `_src/tools/validate_lifecycle_trace.py`
- **Feature / Task**: `0022-02.02` (PREREQ: `0022-02.01`)
- **Governing Standard**: Automotive SPICE (PAM 3.1 / PAM 4.0) Bidirectional Traceability & ISO 26262 Tool Qualification
- **Tool Custodian**: `jake` (QA-Manager, Team DeepSpace9)
- **Status**: `REVIEW`
- **Scope & Governance Bounds**:
  - Validates lifecycle trace graphs over **explicit candidate roots only** (passed via CLI arguments).
  - Enforces bounded inputs ($\le 10\text{ MB}$) and fail-closed handling of malformed/corrupted files.
  - **Does NOT register `_src/validate.py` or any default shared pre-commit gate**.
  - **Does NOT rewrite or alter evidence records**.
  - **Grants zero ECU-process credit from tool execution alone** (audit tool only).

---

## 2. Detected Finding Rules & Validation Catalog

| Finding Code | Description & Trigger Condition | Severity | Example Trigger |
| :--- | :--- | :--- | :--- |
| **`WRONG_VERIFICATION_BASIS`** | Verification measure or result linked across improper verification boundaries (e.g. `SWE.4` testing `SYS.2` or `VAL.1` testing `SWE.3`). | `ERROR` | Unit test measure verifying System Architecture instead of Detailed Design. |
| **`ORPHAN_NODE`** | Disconnected node lacking mandatory incoming or outgoing traceability edges. | `ERROR` | Requirement or design node with zero traces to tests or architecture. |
| **`STALE_BASELINE`** | Traceability edge connecting nodes from divergent or mismatched `baseline_id`s. | `ERROR` | Test measure on `BASE-V060` linked to requirement on `BASE-DEPRECATED`. |
| **`CROSS_VARIANT_EDGE`** | Traceability edge connecting mutually incompatible `variant_id`s. | `ERROR` | Edge connecting `baremetal-arm` implementation to `posix-x86` hardware rig. |
| **`RESPONSIBILITY_MISMATCH`**| Node author/role does not possess authority to sign off the target process area. | `ERROR` | Developer signing off on safety or QA sign-off nodes. |
| **`ILLEGAL_STATUS`** | Node `status` string is missing or not in allowed lifecycle states (`APPROVED`, `VERIFIED`, `CLOSED`, etc.). | `ERROR` | Custom untracked state string (e.g. `DONE_PENDING`). |
| **`NON_ECU_EVIDENCE_SUBSTITUTION`** | Verification result node attempts to substitute generic mock/dummy environments for mandated ECU testbeds. | `ERROR` | Qualification result referencing `generic_mock_testbench` instead of SIL/HIL. |

---

## 3. CLI Usage, Deterministic Exit Codes & Output Formats

### 3.1 Command Line Interface
```bash
# Formatted text summary:
python3 _src/tools/validate_lifecycle_trace.py path/to/lifecycle_graph.json

# Deterministic JSON output:
python3 _src/tools/validate_lifecycle_trace.py path/to/lifecycle_graph.json --json
```

### 3.2 Deterministic Exit Codes
- **`0`**: Valid graph (0 findings detected).
- **`1`**: Validation findings detected (one or more finding codes returned).
- **`2`**: Malformed input / file size exceeded / CLI usage error (Fail-Closed rejection).

---

## 4. Test Verification Evidence
- Automated test suite: `_src/tests/test_validate_lifecycle_trace.py`
- Test Results: **9/9 tests passed (100% OK)** covering clean graphs, all 7 finding classes, and CLI fail-closed execution.
- QA Sign-Off: `jake` (QA-Manager, Team DeepSpace9).
