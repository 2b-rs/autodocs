#!/usr/bin/env python3
"""
validate_lifecycle_trace.py - Standalone Lifecycle Traceability Graph Validator (0022-02.02)

Validates lifecycle trace graphs over explicit candidate roots only.
Performs fail-closed, bounded input checks and reports deterministic findings.
Does NOT register any default shared gate and does NOT modify input evidence.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, List, Set, Tuple

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB bound

ALLOWED_STATUSES: Set[str] = {
    "DRAFT",
    "SUBMITTED",
    "IN_REVIEW",
    "APPROVED",
    "VERIFIED",
    "CLOSED",
    "CLOSED_ACCEPTED",
    "CLOSED_REJECTED",
    "CLOSED_SUPERSEDED",
    "REJECTED",
    "SUPERSEDED",
}

VALID_VERIFICATION_BASES: Dict[str, Set[str]] = {
    "SWE.4": {"SWE.3", "WP-SWE3-CODE"},
    "SWE.5": {"SWE.2", "WP-SWE2-ARCH"},
    "SWE.6": {"SWE.1", "WP-SWE1-REQ"},
    "SYS.4": {"SYS.3", "WP-SYS3-ARCH"},
    "SYS.5": {"SYS.2", "WP-SYS2-SYSREQ"},
    "VAL.1": {"SYS.1", "WP-SYS1-STK"},
}

DISALLOWED_MOCK_ENVIRONMENTS: Set[str] = {
    "mock_host",
    "dummy_testbench",
    "generic_mock",
    "uncalibrated_sim",
}

ROLE_AUTHORITY_MAPPINGS: Dict[str, Set[str]] = {
    "QA-Manager": {"SUP.1", "SWE.6", "SYS.5", "VAL.1"},
    "Requirements Engineer": {"SYS.1", "SYS.2", "SWE.1"},
    "System Architect": {"SYS.3", "SWE.2"},
    "Programmer": {"SWE.3", "SWE.4"},
    "Integrator": {"SWE.5", "SYS.4", "SUP.8"},
    "Safety Officer": {"MAN.5", "SYS.2", "SYS.3", "SYS.5"},
    "Project Lead": {"MAN.3", "SUP.10"},
}


class LifecycleTraceValidator:
    def __init__(self, raw_data: Dict[str, Any]):
        self.raw_data = raw_data
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.findings: List[Dict[str, Any]] = []

    def validate(self) -> List[Dict[str, Any]]:
        self.findings = []
        if not isinstance(self.raw_data, dict):
            self._add_finding("MALFORMED_INPUT", "Root data must be a JSON object", "root")
            return self.findings

        nodes_list = self.raw_data.get("nodes", [])
        edges_list = self.raw_data.get("edges", [])

        if not isinstance(nodes_list, list) or not isinstance(edges_list, list):
            self._add_finding("MALFORMED_INPUT", "'nodes' and 'edges' must be lists", "root")
            return self.findings

        # Index nodes
        for node in nodes_list:
            if not isinstance(node, dict) or "node_id" not in node:
                self._add_finding("MALFORMED_NODE", "Node missing 'node_id' or not an object", "unknown")
                continue
            node_id = str(node["node_id"])
            if node_id in self.nodes:
                self._add_finding("DUPLICATE_NODE_ID", f"Duplicate node_id '{node_id}'", node_id)
            self.nodes[node_id] = node

        self.edges = [e for e in edges_list if isinstance(e, dict)]

        # Execute check rules
        self._check_node_schemas()
        self._check_edges_and_orphans()
        self._check_verification_bases()
        self._check_baselines_and_variants()
        self._check_responsibility_and_status()
        self._check_evidence_substitution()

        # Deterministically sort findings by finding_code then target
        self.findings.sort(key=lambda x: (x["finding_code"], x.get("target_id", "")))
        return self.findings

    def _add_finding(self, finding_code: str, message: str, target_id: str, severity: str = "ERROR"):
        self.findings.append({
            "finding_code": finding_code,
            "message": message,
            "target_id": target_id,
            "severity": severity,
        })

    def _check_node_schemas(self):
        for node_id, node in self.nodes.items():
            node_type = node.get("node_type")
            if node_type not in {"ArtifactNode", "VerificationMeasureNode", "VerificationResultNode"}:
                self._add_finding("ILLEGAL_NODE_TYPE", f"Unknown node_type '{node_type}'", node_id)

            # Check status
            status_info = node.get("status_info", {})
            status = status_info.get("status") if isinstance(status_info, dict) else None
            if not status or status not in ALLOWED_STATUSES:
                self._add_finding("ILLEGAL_STATUS", f"Invalid or missing status '{status}'", node_id)

    def _check_edges_and_orphans(self):
        connected_nodes: Set[str] = set()

        for edge in self.edges:
            source_id = str(edge.get("source_id", ""))
            target_id = str(edge.get("target_id", ""))
            edge_type = edge.get("edge_type", "")

            if not source_id or source_id not in self.nodes:
                self._add_finding("DANGLING_EDGE_SOURCE", f"Edge source '{source_id}' does not exist", source_id)
            else:
                connected_nodes.add(source_id)

            if not target_id or target_id not in self.nodes:
                self._add_finding("DANGLING_EDGE_TARGET", f"Edge target '{target_id}' does not exist", target_id)
            else:
                connected_nodes.add(target_id)

            if not edge_type:
                self._add_finding("MISSING_EDGE_TYPE", "Edge missing 'edge_type'", f"{source_id}->{target_id}")

        for node_id in self.nodes:
            if node_id not in connected_nodes:
                self._add_finding("ORPHAN_NODE", f"Node '{node_id}' is disconnected from graph", node_id)

    def _check_verification_bases(self):
        for edge in self.edges:
            edge_type = edge.get("edge_type")
            source_id = str(edge.get("source_id", ""))
            target_id = str(edge.get("target_id", ""))

            if edge_type in {"verifies_measure", "validates_measure"}:
                source_node = self.nodes.get(source_id, {})
                target_node = self.nodes.get(target_id, {})

                verif_base = source_node.get("verification_base") or source_node.get("verif_base")
                target_process = (target_node.get("identity", {}).get("process_id") or
                                  target_node.get("process_id"))

                if verif_base and verif_base in VALID_VERIFICATION_BASES:
                    allowed_targets = VALID_VERIFICATION_BASES[verif_base]
                    if target_process and target_process not in allowed_targets:
                        self._add_finding(
                            "WRONG_VERIFICATION_BASIS",
                            f"Measure '{source_id}' on base '{verif_base}' cannot verify target process '{target_process}'",
                            source_id
                        )

    def _check_baselines_and_variants(self):
        for edge in self.edges:
            source_id = str(edge.get("source_id", ""))
            target_id = str(edge.get("target_id", ""))

            source_node = self.nodes.get(source_id, {})
            target_node = self.nodes.get(target_id, {})

            if not source_node or not target_node:
                continue

            src_base = source_node.get("baseline", {})
            tgt_base = target_node.get("baseline", {})

            # Check Stale Baseline mismatch
            src_base_id = src_base.get("baseline_id") if isinstance(src_base, dict) else None
            tgt_base_id = tgt_base.get("baseline_id") if isinstance(tgt_base, dict) else None
            if src_base_id and tgt_base_id and src_base_id != tgt_base_id:
                self._add_finding(
                    "STALE_BASELINE",
                    f"Baseline mismatch across edge: '{src_base_id}' vs '{tgt_base_id}'",
                    f"{source_id}->{target_id}"
                )

            # Check Cross-Variant edge
            src_var = src_base.get("variant_id") if isinstance(src_base, dict) else None
            tgt_var = tgt_base.get("variant_id") if isinstance(tgt_base, dict) else None
            if src_var and tgt_var and src_var != tgt_var and src_var != "common" and tgt_var != "common":
                self._add_finding(
                    "CROSS_VARIANT_EDGE",
                    f"Incompatible variant link between '{src_var}' and '{tgt_var}'",
                    f"{source_id}->{target_id}"
                )

    def _check_responsibility_and_status(self):
        for node_id, node in self.nodes.items():
            resp = node.get("responsibility_origin", {})
            role = resp.get("role") if isinstance(resp, dict) else None
            process = node.get("identity", {}).get("process_id")

            if role and process and role in ROLE_AUTHORITY_MAPPINGS:
                allowed_procs = ROLE_AUTHORITY_MAPPINGS[role]
                if process not in allowed_procs:
                    self._add_finding(
                        "RESPONSIBILITY_MISMATCH",
                        f"Role '{role}' is not authorized to sign off process '{process}'",
                        node_id
                    )

    def _check_evidence_substitution(self):
        for node_id, node in self.nodes.items():
            if node.get("node_type") == "VerificationResultNode":
                env = node.get("execution_environment") or node.get("env_digest")
                if isinstance(env, str):
                    for mock in DISALLOWED_MOCK_ENVIRONMENTS:
                        if mock in env.lower():
                            self._add_finding(
                                "NON_ECU_EVIDENCE_SUBSTITUTION",
                                f"Verification result '{node_id}' uses unapproved mock environment '{env}'",
                                node_id
                            )


def load_candidate_graph(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' does not exist.")

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size ({file_size} bytes) exceeds limit of {MAX_FILE_SIZE_BYTES} bytes.")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Validate candidate lifecycle traceability graph (0022-02.02)."
    )
    parser.add_argument("graph", nargs="?", help="Path to lifecycle graph JSON file.")
    parser.add_argument("--graph", dest="graph_opt", help="Path to lifecycle graph JSON file.")
    parser.add_argument("--json", action="store_true", help="Output findings in JSON format.")
    args = parser.parse_args()

    target_file = args.graph_opt or args.graph
    if not target_file:
        sys.stderr.write("Error: Missing graph file path. Pass file as positional arg or --graph <path>.\n")
        sys.exit(2)

    try:
        raw_data = load_candidate_graph(target_file)
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(2)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Fail-Closed Error: Malformed JSON in '{target_file}': {e}\n")
        sys.exit(2)
    except Exception as e:
        sys.stderr.write(f"Error reading file '{target_file}': {e}\n")
        sys.exit(2)

    validator = LifecycleTraceValidator(raw_data)
    findings = validator.validate()

    result_payload = {
        "target_file": target_file,
        "valid": len(findings) == 0,
        "finding_count": len(findings),
        "findings": findings,
    }

    if args.json:
        print(json.dumps(result_payload, indent=2, sort_keys=True))
    else:
        print(f"=== Lifecycle Trace Validation Report: {target_file} ===")
        print(f"Status: {'VALID' if result_payload['valid'] else 'INVALID'}")
        print(f"Findings: {result_payload['finding_count']}")
        for f in findings:
            print(f"  [{f['finding_code']}] ({f['severity']}) Target: {f.get('target_id', '')} - {f['message']}")

    sys.exit(0 if result_payload["valid"] else 1)


if __name__ == "__main__":
    main()
