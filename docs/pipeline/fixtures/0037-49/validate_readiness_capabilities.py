#!/usr/bin/env python3
"""Executable capability/negative-case evaluator for Task 0037-49."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
REQUIRED_ROLES = {
    "process",
    "security",
    "privacy",
    "release",
    "independent-quality",
    "translation-review",
}
REQUIRED_HANDLES = {"autodocs-deploy-key", "agent-commit-key"}


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def evaluate(state: dict) -> str:
    if state["decision"] != "ready":
        return "blocked:decision"
    if state["package_digest"] != state["expected_package_digest"]:
        return "blocked:stale-digest"
    if not REQUIRED_ROLES.issubset(state["roles"]):
        return "blocked:wrong-role"
    if not state["signer_registered"]:
        return "blocked:revoked-signer"
    if not REQUIRED_HANDLES.issubset(state["handles"]):
        return "blocked:unavailable-handle"
    if state["deploy_probe"] != "passed":
        return "blocked:deploy-capability"
    if state["signing_probe"] != "passed":
        return "blocked:signing-capability"
    if state["service_probe"] != "passed":
        return "blocked:service-controls"
    return "readiness-eligible"


def main() -> None:
    authorities = load("issues/_policy/authorities.json")
    handles = load("issues/_policy/credential-handles.json")
    deploy = load("docs/pipeline/0037-49-deploy-key-probe-plural-result.json")
    signing = load("docs/pipeline/0037-49-signing-handle-probe-result.json")
    service = load("docs/pipeline/0037-49-runner-service-qualification-result.json")
    package_digest = "sha256:bf98dffe33da51c29e8952e7cfe10e0bb172d1d50ddb191282ea5c3330909a5f"
    base = {
        "decision": "ready",
        "package_digest": package_digest,
        "expected_package_digest": package_digest,
        "roles": {item["role"] for item in authorities["principals"]},
        "signer_registered": "agent-commit-key" in (ROOT / "issues/_policy/allowed_signers").read_text(encoding="utf-8"),
        "handles": {item["handle_id"] for item in handles["handles"]},
        "deploy_probe": deploy["verdict"],
        "signing_probe": signing["verdict"],
        "service_probe": service["verdict"],
    }
    cases = [("ready", base, "readiness-eligible")]
    mutations = [
        ("reject-decision", {"decision": "reject"}, "blocked:decision"),
        ("stale-digest", {"package_digest": "sha256:" + "0" * 64}, "blocked:stale-digest"),
        ("wrong-role", {"roles": base["roles"] - {"process"}}, "blocked:wrong-role"),
        ("revoked-signer", {"signer_registered": False}, "blocked:revoked-signer"),
        ("unavailable-handle", {"handles": base["handles"] - {"agent-commit-key"}}, "blocked:unavailable-handle"),
        ("deploy-failure", {"deploy_probe": "failed"}, "blocked:deploy-capability"),
        ("signing-failure", {"signing_probe": "failed"}, "blocked:signing-capability"),
        ("service-failure", {"service_probe": "failed"}, "blocked:service-controls"),
    ]
    for case_id, mutation, expected in mutations:
        state = copy.deepcopy(base)
        state.update(mutation)
        cases.append((case_id, state, expected))

    results = []
    for case_id, state, expected in cases:
        actual = evaluate(state)
        assert actual == expected, (case_id, actual, expected)
        results.append({"id": case_id, "expected": expected, "actual": actual, "verdict": "passed"})
    output = {
        "schema": "0037-49-capability-fixture-result@v1",
        "task": "0037-49",
        "verdict": "passed",
        "case_count": len(results),
        "cases": results,
    }
    result_path = ROOT / "docs/pipeline/0037-49-capability-fixture-result.json"
    result_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: {len(results)} executable readiness capability cases")


if __name__ == "__main__":
    main()
