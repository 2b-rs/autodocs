"""Hermetic capability-matcher tests (0044-05.02)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_src" / "tools"))
from capability_match import InputError, run, validate_profile  # noqa: E402

MATCHER = ROOT / "_src" / "tools" / "capability_match.py"
LEGACY_SCHEMA = ROOT / "issues" / "_schema" / "agent-capability-v1.schema.json"
FIXTURES = ROOT / "_src" / "tests" / "fixtures" / "capability-match"


def _profile(**overrides):
    base = {
        "schema": "task-requirement-profile@v1",
        "profile_id": "p-0044-05.02",
        "task_id": "0044-05.02",
        "process_role": "Implementer",
        "capability_class": "unprivileged",
        "execution_needs": "direct",
        "required_rights": ["git.write"],
        "required_data_handles": ["repo.read"],
        "required_tools": ["python3"],
        "token_budget_class": "large",
        "context_budget_class": "large",
        "cognitive_demand": "high",
        "required_assurances": ["independence.handle"],
        "sources": [{
            "kind": "architecture",
            "reference": "docs/campaign-evidence/0044-05/capability-matcher-architecture.md",
            "derivation": "0044-05.02 contract",
        }],
        "test_scope": {
            "kind": "hermetic",
            "derived_from": ["0044-05.01"],
            "command": "python3 -m unittest _src.tests.test_capability_match",
            "expected_evidence": "exit-0",
        },
        "resource_bounds": {
            "max_cpu_seconds": 1200,
            "max_wall_seconds": 1200,
            "max_memory_mib": 1024,
            "expected_token_range": [16000, 32000],
        },
    }
    base.update(overrides)
    return base


def _desc(agent="gabriel", **overrides):
    base = {
        "schema": "agent-capability-descriptor@v1",
        "descriptor_id": f"d-{agent}",
        "agent_id": agent,
        "process_roles": ["Implementer"],
        "capability_class": "unprivileged",
        "execution_routes": ["direct", "none"],
        "rights": ["git.write"],
        "data_handles": ["repo.read"],
        "tools": ["python3"],
        "token_budget_class": "large",
        "context_budget_class": "large",
        "cognitive_classes_served": ["low", "medium", "high"],
        "assurances": ["independence.handle"],
        "capacity_status": "available",
        "snapshot_reference": "snap-1",
    }
    base.update(overrides)
    return base


def _write(dirpath, name, obj):
    path = Path(dirpath) / name
    path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")
    return path


def _cli(args):
    return subprocess.run(
        [sys.executable, str(MATCHER), *args],
        capture_output=True, text=True, check=False,
    )


class CapabilityMatchTests(unittest.TestCase):
    def test_exact_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            d = _write(tmp, "d.json", _desc())
            encoded, code, result = run(p, [d])
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "single-eligible")
            self.assertEqual(result["eligible_agent_ids"], ["gabriel"])
            self.assertIn("no assignment", result["non_authority_notice"])
            self.assertTrue(encoded.endswith("\n"))

    def test_privileged_superset_direct(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            d = _write(tmp, "d.json", _desc(
                "data",
                process_roles=["Architect", "Implementer"],
                capability_class="privileged",
                rights=["acceptance.review", "git.write", "integration.checkpoint"],
                cognitive_classes_served=["low", "medium", "high", "critical"],
            ))
            _, code, result = run(p, [d])
            self.assertEqual(code, 0)
            self.assertEqual(result["eligible_agent_ids"], ["data"])
            self.assertIn("Acceptance", result["non_authority_notice"])

    def test_sandboxed_none_multiple_classes(self):
        profile = _profile(
            capability_class="sandboxed-grunt",
            execution_needs="none",
            required_rights=[],
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", profile)
            g = _write(tmp, "g.json", _desc(
                "grunt",
                capability_class="sandboxed-grunt",
                execution_routes=["none", "runner"],
                rights=[],
            ))
            u = _write(tmp, "u.json", _desc("unpriv"))
            _, code, result = run(p, [g, u])
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "multiple-eligible")
            self.assertEqual(result["eligible_agent_ids"], ["grunt", "unpriv"])

    def test_ambiguous_two_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            a = _write(tmp, "a.json", _desc("ada"))
            b = _write(tmp, "b.json", _desc("bella"))
            _, code, result = run(p, [b, a])
            self.assertEqual(code, 0)
            self.assertEqual(result["status"], "multiple-eligible")
            self.assertEqual(result["eligible_agent_ids"], ["ada", "bella"])

    def test_none_eligible_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            d = _write(tmp, "d.json", _desc(capacity_status="unavailable", rights=[]))
            _, code, result = run(p, [d])
            self.assertEqual(code, 1)
            self.assertEqual(result["status"], "none-eligible")
            joined = " ".join(result["rejections"][0]["reasons"])
            self.assertIn("CAPACITY_UNAVAILABLE", joined)
            self.assertIn("RIGHT_MISSING:git.write", joined)

    def test_runner_mismatch(self):
        profile = _profile(capability_class="sandboxed-grunt", execution_needs="runner", required_rights=[])
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", profile)
            d = _write(tmp, "d.json", _desc("priv", capability_class="privileged",
                                           cognitive_classes_served=["low", "medium", "high", "critical"]))
            _, code, result = run(p, [d])
            self.assertEqual(code, 1)
            reasons = result["rejections"][0]["reasons"]
            self.assertTrue(any(r.startswith("CAPABILITY_CLASS_INCOMPATIBLE") for r in reasons))
            self.assertTrue(any(r.startswith("EXECUTION_ROUTE_MISSING") for r in reasons))

    def test_authority_mismatch_red_first(self):
        profile = _profile(
            process_role="Integrator",
            capability_class="privileged",
            required_rights=["acceptance.review", "git.write", "integration.checkpoint"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", profile)
            d = _write(tmp, "d.json", _desc(
                "faker",
                process_roles=["Integrator"],
                capability_class="unprivileged",
                rights=["acceptance.review", "git.write", "integration.checkpoint"],
            ))
            _, code, result = run(p, [d])
            self.assertEqual(code, 1)
            self.assertIn("AUTHORITY_CONSTRAINT_FAILED", result["rejections"][0]["reasons"])

    def test_missing_data_tool_assurance(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            d = _write(tmp, "d.json", _desc(data_handles=[], tools=[], assurances=[]))
            _, _, result = run(p, [d])
            reasons = result["rejections"][0]["reasons"]
            self.assertIn("DATA_HANDLE_MISSING:repo.read", reasons)
            self.assertIn("TOOL_MISSING:python3", reasons)
            self.assertIn("ASSURANCE_MISSING:independence.handle", reasons)
            blob = json.dumps(result)
            self.assertNotIn("/Users/", blob)
            self.assertNotIn("SECRET", blob)

    def test_capacity_unknown_and_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            d = _write(tmp, "d.json", _desc(
                capacity_status="unknown",
                token_budget_class="small",
                context_budget_class="small",
            ))
            _, code, result = run(p, [d])
            self.assertEqual(code, 1)
            reasons = result["rejections"][0]["reasons"]
            self.assertEqual(reasons[0], "CAPACITY_UNKNOWN")
            self.assertTrue(any(r.startswith("TOKEN_BUDGET_INSUFFICIENT") for r in reasons))

    def test_invalid_unknown_field_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = _profile()
            bad["extra"] = True
            p = _write(tmp, "p.json", bad)
            d = _write(tmp, "d.json", _desc())
            proc = _cli(["--profile", str(p), "--descriptor", str(d), "--json"])
            self.assertEqual(proc.returncode, 2)
            self.assertIn("invalid-input", proc.stdout)

    def test_duplicate_key_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "p.json"
            p.write_text('{"schema":"task-requirement-profile@v1","schema":"x"}', encoding="utf-8")
            d = _write(tmp, "d.json", _desc())
            proc = _cli(["--profile", str(p), "--descriptor", str(d)])
            self.assertEqual(proc.returncode, 2)

    def test_duplicate_identity_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            a = _write(tmp, "a.json", _desc("same"))
            b = _write(tmp, "b.json", _desc("same", descriptor_id="d-other"))
            proc = _cli(["--profile", str(p), "--descriptor", str(a), "--descriptor", str(b)])
            self.assertEqual(proc.returncode, 2)

    def test_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            a = _write(tmp, "a.json", _desc("ada"))
            b = _write(tmp, "b.json", _desc("bella"))
            first, _, _ = run(p, [b, a])
            second, _, _ = run(p, [a, b])
            self.assertEqual(first, second)

    def test_self_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            d = _write(tmp, "d.json", _desc("gabriel"))
            r = _write(tmp, "r.json", _desc("other", capacity_status="unavailable"))
            proc = _cli(["--profile", str(p), "--descriptor", str(d), "--agent-id", "gabriel"])
            self.assertEqual(proc.returncode, 0)
            proc = _cli(["--profile", str(p), "--descriptor", str(r), "--agent-id", "other"])
            self.assertEqual(proc.returncode, 1)
            proc = _cli(["--profile", str(p), "--descriptor", str(d), "--agent-id", "missing"])
            self.assertEqual(proc.returncode, 2)

    def test_legacy_canary(self):
        before = hashlib.sha256(LEGACY_SCHEMA.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile())
            legacy = {
                "schema": "agent-capability@v1",
                "class": "privileged",
                "policy_digest": "sha256:" + ("ab" * 32),
            }
            d = _write(tmp, "legacy.json", legacy)
            proc = _cli(["--profile", str(p), "--descriptor", str(d), "--json"])
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "invalid-input")
            self.assertEqual(payload["error"], "SCHEMA_UNSUPPORTED_LEGACY")
        after = hashlib.sha256(LEGACY_SCHEMA.read_bytes()).hexdigest()
        self.assertEqual(before, after)

    def test_noncanonical_array_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "p.json", _profile(required_rights=["z.write", "a.write"]))
            d = _write(tmp, "d.json", _desc())
            proc = _cli(["--profile", str(p), "--descriptor", str(d)])
            self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
