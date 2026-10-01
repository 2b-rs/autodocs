import json
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))

from validate_lifecycle_trace import LifecycleTraceValidator, load_candidate_graph  # noqa: E402


def create_valid_graph_data():
    return {
        "nodes": [
            {
                "node_id": "REQ-SYS-01",
                "node_type": "ArtifactNode",
                "responsibility_origin": {"role": "Requirements Engineer", "agent": "doctor"},
                "identity": {"process_id": "SYS.2"},
                "baseline": {"baseline_id": "BASE-V060", "variant_id": "posix-ecu"},
                "status_info": {"status": "APPROVED"},
            },
            {
                "node_id": "TC-SYS5-01",
                "node_type": "VerificationMeasureNode",
                "verification_base": "SYS.5",
                "responsibility_origin": {"role": "QA-Manager", "agent": "jake"},
                "identity": {"process_id": "SYS.5"},
                "baseline": {"baseline_id": "BASE-V060", "variant_id": "posix-ecu"},
                "status_info": {"status": "APPROVED"},
            },
            {
                "node_id": "RES-SYS5-01",
                "node_type": "VerificationResultNode",
                "responsibility_origin": {"role": "QA-Manager", "agent": "jake"},
                "identity": {"process_id": "SYS.5"},
                "baseline": {"baseline_id": "BASE-V060", "variant_id": "posix-ecu"},
                "status_info": {"status": "VERIFIED"},
                "execution_environment": "env-hil-ecu-bench-01",
            },
        ],
        "edges": [
            {
                "source_id": "TC-SYS5-01",
                "target_id": "REQ-SYS-01",
                "edge_type": "verifies_measure",
            },
            {
                "source_id": "RES-SYS5-01",
                "target_id": "TC-SYS5-01",
                "edge_type": "results_in",
            },
        ],
    }


def test_validator_valid_graph():
    data = create_valid_graph_data()
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    assert len(findings) == 0


def test_validator_wrong_verification_basis():
    data = create_valid_graph_data()
    # Change verification_base to SWE.4 which cannot verify SYS.2
    data["nodes"][1]["verification_base"] = "SWE.4"
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    finding_codes = [f["finding_code"] for f in findings]
    assert "WRONG_VERIFICATION_BASIS" in finding_codes


def test_validator_orphan_node():
    data = create_valid_graph_data()
    # Add an unconnected orphan node
    data["nodes"].append({
        "node_id": "ORPHAN-01",
        "node_type": "ArtifactNode",
        "responsibility_origin": {"role": "Requirements Engineer"},
        "identity": {"process_id": "SYS.2"},
        "baseline": {"baseline_id": "BASE-V060", "variant_id": "posix-ecu"},
        "status_info": {"status": "DRAFT"},
    })
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    finding_codes = [f["finding_code"] for f in findings]
    assert "ORPHAN_NODE" in finding_codes


def test_validator_stale_baseline():
    data = create_valid_graph_data()
    # Make target baseline different from source
    data["nodes"][0]["baseline"]["baseline_id"] = "BASE-DEPRECATED-OLD"
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    finding_codes = [f["finding_code"] for f in findings]
    assert "STALE_BASELINE" in finding_codes


def test_validator_cross_variant_edge():
    data = create_valid_graph_data()
    # Make variant incompatible
    data["nodes"][0]["baseline"]["variant_id"] = "baremetal-arm"
    data["nodes"][1]["baseline"]["variant_id"] = "posix-x86"
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    finding_codes = [f["finding_code"] for f in findings]
    assert "CROSS_VARIANT_EDGE" in finding_codes


def test_validator_responsibility_mismatch():
    data = create_valid_graph_data()
    # Assign Programmer to sign off SYS.2 requirements
    data["nodes"][0]["responsibility_origin"]["role"] = "Programmer"
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    finding_codes = [f["finding_code"] for f in findings]
    assert "RESPONSIBILITY_MISMATCH" in finding_codes


def test_validator_illegal_status():
    data = create_valid_graph_data()
    data["nodes"][0]["status_info"]["status"] = "CUSTOM_RANDOM_STATE"
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    finding_codes = [f["finding_code"] for f in findings]
    assert "ILLEGAL_STATUS" in finding_codes


def test_validator_non_ecu_evidence_substitution():
    data = create_valid_graph_data()
    # Substitute dummy mock environment
    data["nodes"][2]["execution_environment"] = "generic_mock_testbench"
    validator = LifecycleTraceValidator(data)
    findings = validator.validate()
    finding_codes = [f["finding_code"] for f in findings]
    assert "NON_ECU_EVIDENCE_SUBSTITUTION" in finding_codes


def test_cli_execution(tmp_path):
    script_path = str(TOOLS / "validate_lifecycle_trace.py")
    graph_file = tmp_path / "valid_graph.json"
    graph_file.write_text(json.dumps(create_valid_graph_data()), encoding="utf-8")

    # Run clean validation
    proc = subprocess.run([sys.executable, script_path, str(graph_file), "--json"], capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["valid"] is True
    assert payload["finding_count"] == 0

    # Run invalid validation (malformed JSON)
    bad_file = tmp_path / "malformed.json"
    bad_file.write_text("{ unclosed json: ", encoding="utf-8")
    proc_bad = subprocess.run([sys.executable, script_path, str(bad_file)], capture_output=True, text=True)
    assert proc_bad.returncode == 2
