"""Hermetic tests for the non-operative Feature 0037 cutover safe core.

AE-1..AE-5 evidence contract:
- exact baseline: f5142ab033947bf16601ed9063f48aa96a8ff0e5 (tool and v2 schemas absent)
- candidate: carrying commit containing this file
- falsification: ``test_cli_inspect_prepare_verify`` is red on the baseline because
  ``_src/tools/issue_cutover.py`` is absent and green on the candidate.
- adjacent cases: stale OID, extra ref, changed serialization, and missing
  activation audit each exercise a distinct neighboring contract dimension.
- exhaustive properties: 64 epoch-transition pairs, 32 epoch/authority pairs,
  8 existing/absent ref subsets, 8 event-chain prefixes, and 64 canonical-key
  permutations. Canonical permutation seed: 37002. Exact executed count: 176.
"""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
import random
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src/tools/issue_cutover.py"
SPEC = importlib.util.spec_from_file_location("issue_cutover", TOOL)
assert SPEC and SPEC.loader
CUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CUT)
D0 = "sha256:" + "0" * 64
D1 = "sha256:" + "1" * 64
ACTOR = "authority:repository-owner"


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.STDOUT).decode().strip()


def event(sequence: int = 1, from_epoch: str = "legacy_active", to_epoch: str = "legacy_active", previous: str | None = None, transaction_id: str = "tx-0037-safe-core") -> dict[str, Any]:
    payload = {
        "schema": CUT.LEDGER_SCHEMA,
        "transaction_id": transaction_id,
        "sequence": sequence,
        "event_kind": "inspect",
        "from_epoch": from_epoch,
        "to_epoch": to_epoch,
        "allowed_write_authority": CUT.EXPECTED_AUTHORITY[to_epoch],
        "issue_store_frozen": to_epoch in {"legacy_frozen", "prepared", "post_cutover_audit", "point_of_no_return", "write_frozen_repair"},
        "previous_event_digest": previous,
        "payload_digest": D0,
        "actor": ACTOR,
        "role": "control_actor",
        "signature_policy": "single-authority-self-attestation@v1",
        "signature_verified": True,
    }
    payload["event_digest"] = CUT.digest_value(payload)
    return payload


class CutoverFixture(unittest.TestCase):
    temp: tempfile.TemporaryDirectory[str]
    base: Path
    repo: Path
    source: str
    manifest: dict[str, Any]
    manifest_path: Path

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, check=True, capture_output=True)
        git(self.repo, "config", "user.email", "cutover@example.invalid")
        git(self.repo, "config", "user.name", "Cutover Fixture")
        (self.repo / "seed").write_text("seed\n", encoding="utf-8")
        git(self.repo, "add", "seed")
        git(self.repo, "commit", "-m", "seed")
        self.source = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "branch", "candidate", self.source)
        (self.repo / "agent-workflow.json").write_text("{\"authority\":\"legacy\"}\n", encoding="utf-8")
        tools = self.repo / "_src/tools"
        tools.mkdir(parents=True)
        adapter_source = (
            "import argparse\nfrom pathlib import Path\n"
            "p=argparse.ArgumentParser(); p.add_argument('--output', required=True); a=p.parse_args()\n"
            "root=Path(a.output); root.mkdir(parents=True, exist_ok=True)\n"
            "(root/'artifact.json').write_text('{\\\"ok\\\":true}\\n', encoding='utf-8')\n"
        )
        for name in ("issue_import_legacy.py", "issue_regenerate.py"):
            (tools / name).write_text(adapter_source, encoding="utf-8")
        schemas = self.repo / "issues/_schema"
        schemas.mkdir(parents=True)
        for name in ("cutover-transaction-manifest-v1.schema.json", "cutover-control-ledger-v2.schema.json"):
            (schemas / name).write_bytes((ROOT / "issues/_schema" / name).read_bytes())
        self.manifest = self.make_manifest()
        self.manifest_path = self.base / "manifest.json"
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def make_manifest(self) -> dict[str, Any]:
        selector = self.repo / "agent-workflow.json"
        q_payload = {"clients": [], "jobs": [], "claims": [], "observed_at_oid": self.source}
        tool_paths = ["_src/tools/issue_import_legacy.py", "_src/tools/issue_regenerate.py"]
        schema_paths = ["issues/_schema/cutover-transaction-manifest-v1.schema.json", "issues/_schema/cutover-control-ledger-v2.schema.json"]
        roles = {role: ACTOR for role in CUT.REQUIRED_ROLES}
        signatures = [
            {"role": role, "actor": ACTOR, "policy": "single-authority-self-attestation@v1", "payload_digest": D0, "verified": True}
            for role in sorted(CUT.REQUIRED_ROLES)
        ]
        return {
            "schema": CUT.MANIFEST_SCHEMA,
            "transaction_id": "tx-0037-safe-core",
            "source": {"ref": "refs/heads/main", "oid": self.source, "digest": D0},
            "candidate": {"ref": "refs/heads/candidate", "oid": self.source, "digest": D1, "prepared_patch_digest": D1},
            "authority_snapshot": {
                "epoch": "legacy_active", "allowed_write_authority": "legacy", "issue_store_frozen": False,
                "authorities": [ACTOR], "selector_path": "agent-workflow.json", "selector_digest": CUT.digest_bytes(selector.read_bytes()),
                "token_digest": CUT.digest_value({
                    "epoch": "legacy_active", "allowed_write_authority": "legacy", "issue_store_frozen": False,
                    "authorities": [ACTOR], "selector_path": "agent-workflow.json", "selector_digest": CUT.digest_bytes(selector.read_bytes()),
                }),
            },
            "identities": {
                "tools": [{"path": path, "digest": CUT.digest_bytes((self.repo / path).read_bytes())} for path in tool_paths],
                "schemas": [{"path": path, "digest": CUT.digest_bytes((self.repo / path).read_bytes())} for path in schema_paths],
            },
            "refs": [{"name": "refs/autodocs/cutover-test/control", "expected_oid": None, "target_oid": self.source}],
            "roles": roles,
            "signatures": signatures,
            "approvals": [{"ref": "refs/autodocs/approval/0037/tx-safe", "base_oid": self.source, "role": "approver", "actor": ACTOR, "package_digest": D1, "signature_verified": True}],
            "quiescence": {**q_payload, "digest": CUT.digest_value(q_payload)},
            "ledger": [event()],
            "adapters": [
                {"id": "importer", "executable": "_src/tools/issue_import_legacy.py", "argv": ["--output", "{output}"], "output_subdir": "imported"},
                {"id": "regenerator", "executable": "_src/tools/issue_regenerate.py", "argv": ["--output", "{output}"], "output_subdir": "regenerated"},
            ],
            "outputs": [
                {"path": "imported/artifact.json", "digest": CUT.digest_bytes(b'{"ok":true}\n')},
                {"path": "regenerated/artifact.json", "digest": CUT.digest_bytes(b'{"ok":true}\n')},
            ],
            "findings": [],
            "cas": {"disposable_test_repo": False, "declared_refs": ["refs/autodocs/cutover-test/control"]},
        }

    def write_manifest(self, *, canonical: bool = True):
        text = CUT.canonical_json(self.manifest) if canonical else json.dumps(self.manifest, indent=2) + "\n"
        self.manifest_path.write_text(text, encoding="utf-8")

    def assert_rejected(self, mutate: Callable[[dict[str, Any]], object], code: str | None = None):
        value = copy.deepcopy(self.manifest)
        mutate(value)
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.validate_manifest(value)
        if code:
            self.assertEqual(raised.exception.code, code)


class ContractTests(CutoverFixture):
    def test_cli_inspect_prepare_verify(self):
        out = self.base / "cutover-prepared"
        buffer = StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(CUT.main(["inspect", "--repo", str(self.repo), "--manifest", str(self.manifest_path)]), 0)
        self.assertEqual(json.loads(buffer.getvalue())["status"], "PASS")
        buffer = StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(CUT.main(["prepare", "--repo", str(self.repo), "--manifest", str(self.manifest_path), "--output-root", str(out)]), 0)
        first = json.loads(buffer.getvalue())
        self.assertEqual(first["mutation"], "disposable-output-only")
        self.assertFalse(first["idempotent"])
        buffer = StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(CUT.main(["prepare", "--repo", str(self.repo), "--manifest", str(self.manifest_path), "--output-root", str(out)]), 0)
        self.assertTrue(json.loads(buffer.getvalue())["idempotent"])
        buffer = StringIO()
        with redirect_stdout(buffer):
            self.assertEqual(CUT.main(["verify", "--repo", str(self.repo), "--manifest", str(self.manifest_path), "--output-root", str(out)]), 0)
        self.assertEqual(json.loads(buffer.getvalue())["status"], "PASS")

    def test_all_effect_commands_are_unconditionally_disabled(self):
        for command in CUT.EFFECT_COMMANDS:
            with self.subTest(command=command):
                buffer = StringIO()
                with redirect_stdout(buffer):
                    rc = CUT.main([command, "--repo", "/does/not/exist", "--manifest", "/also/missing"])
                result = json.loads(buffer.getvalue())
                self.assertEqual(rc, 2)
                self.assertEqual(result["code"], CUT.BLOCKED_EFFECT_CODE)
                self.assertEqual(result["mutation"], "none")

    def test_no_force_or_override_path_parses(self):
        with self.assertRaises(SystemExit):
            CUT.main(["activate", "--repo", str(self.repo), "--manifest", str(self.manifest_path), "--force"])

    def test_absolute_paths_and_canonical_manifest_required(self):
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT._absolute(Path("repo"), "--repo")
        self.assertEqual(raised.exception.code, "CUTOVER-ABSOLUTE-PATH")
        self.write_manifest(canonical=False)
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.read_manifest(self.manifest_path)
        self.assertEqual(raised.exception.code, "CUTOVER-NONCANONICAL")

    def test_prepare_retry_changed_input_and_drift_reject(self):
        out = self.base / "cutover-retry"
        CUT.prepare(self.repo, out, self.manifest)
        changed = copy.deepcopy(self.manifest)
        changed["candidate"]["digest"] = D0
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.prepare(self.repo, out, changed)
        self.assertEqual(raised.exception.code, "CUTOVER-TRANSACTION-REUSE")
        (out / "imported/artifact.json").write_text("drift\n", encoding="utf-8")
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.prepare(self.repo, out, self.manifest)
        self.assertEqual(raised.exception.code, "CUTOVER-PREPARED-DRIFT")

    def test_missing_integrated_adapter_executable_rejects_without_promotion(self):
        (self.repo / "_src/tools/issue_regenerate.py").unlink()
        out = self.base / "cutover-missing-executable"
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.prepare(self.repo, out, self.manifest)
        self.assertEqual(raised.exception.code, "CUTOVER-MISSING-EXECUTABLE")
        self.assertFalse(out.exists())

    def test_inspect_detects_stale_source_candidate_selector_and_ref(self):
        git(self.repo, "update-ref", "refs/autodocs/cutover-test/control", self.source)
        git(self.repo, "branch", "-D", "candidate")
        (self.repo / "agent-workflow.json").write_text("drift\n", encoding="utf-8")
        result = CUT.inspect(self.repo, self.manifest)
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("CUTOVER-STALE-OID", codes)
        self.assertIn("CUTOVER-CANDIDATE-DRIFT", codes)
        self.assertIn("CUTOVER-SELECTOR-MISMATCH", codes)

    def test_verify_retained_output_drift(self):
        out = self.base / "cutover-verify-drift"
        CUT.prepare(self.repo, out, self.manifest)
        (out / "regenerated/artifact.json").write_text("changed\n", encoding="utf-8")
        result = CUT.verify(self.repo, self.manifest, out)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("CUTOVER-OUTPUT-DRIFT", {finding["code"] for finding in result["findings"]})

    def test_at_least_32_named_negative_contract_cases(self):
        cases = [
            ("malformed", lambda m: m.__setitem__("refs", "bad"), None),
            ("unknown", lambda m: m.__setitem__("surprise", 1), "CUTOVER-UNKNOWN-FIELD"),
            ("sequence", lambda m: m["ledger"][0].__setitem__("sequence", 2), "CUTOVER-SEQUENCE"),
            ("digest", lambda m: m["source"].__setitem__("digest", "bad"), "CUTOVER-DIGEST"),
            ("event-digest", lambda m: m["ledger"][0].__setitem__("event_digest", D0), "CUTOVER-EVENT-DIGEST"),
            ("transaction", lambda m: m["ledger"][0].__setitem__("transaction_id", "different-tx"), "CUTOVER-TRANSACTION-MISMATCH"),
            ("stale-ref-shape", lambda m: m["refs"][0].__setitem__("expected_oid", "f"), "CUTOVER-OID"),
            ("extra-ref", lambda m: m["cas"].__setitem__("declared_refs", ["refs/extra"]), "CUTOVER-EXTRA-REF"),
            ("null-ref-target-shape", lambda m: m["refs"][0].__setitem__("target_oid", ""), "CUTOVER-OID"),
            ("wrong-approval", lambda m: m["approvals"][0].__setitem__("role", "auditor"), "CUTOVER-WRONG-APPROVAL"),
            ("wrong-control-role", lambda m: m["ledger"][0].__setitem__("role", "unknown"), "CUTOVER-WRONG-CONTROL-ROLE"),
            ("wrong-signature-role", lambda m: m["signatures"][0].__setitem__("actor", "other"), "CUTOVER-WRONG-SIGNATURE-ROLE"),
            ("wrong-signature-policy", lambda m: m["signatures"][0].__setitem__("policy", "other"), "CUTOVER-WRONG-SIGNATURE-POLICY"),
            ("alias-ambiguity", lambda m: m["identities"]["tools"][0].__setitem__("path", "_src/../tool"), "CUTOVER-PATH"),
            ("selector-path", lambda m: m["authority_snapshot"].__setitem__("selector_path", "/selector"), "CUTOVER-PATH"),
            ("dual-authority", lambda m: m["authority_snapshot"].__setitem__("authorities", [ACTOR, "other"]), "CUTOVER-EXACTLY-ONE-AUTHORITY"),
            ("frozen-write", lambda m: m["authority_snapshot"].__setitem__("issue_store_frozen", True), "CUTOVER-FROZEN-STATE"),
            ("legacy-after-switch", lambda m: (m["authority_snapshot"].__setitem__("epoch", "issue_store_active"), m["authority_snapshot"].__setitem__("allowed_write_authority", "legacy")), "CUTOVER-DUAL-AUTHORITY"),
            ("identity-drift-shape", lambda m: m["identities"]["tools"][0].__setitem__("digest", D0[:-1]), "CUTOVER-DIGEST"),
            ("regeneration-adapter", lambda m: m["adapters"].pop(), "CUTOVER-ADAPTER"),
            ("quiescence-client", lambda m: m["quiescence"]["clients"].append("stale"), "CUTOVER-NOT-QUIESCENT"),
            ("quiescence-job", lambda m: m["quiescence"]["jobs"].append("job"), "CUTOVER-NOT-QUIESCENT"),
            ("quiescence-claim", lambda m: m["quiescence"]["claims"].append("claim"), "CUTOVER-NOT-QUIESCENT"),
            ("main-ref", lambda m: (m["refs"][0].__setitem__("name", "refs/heads/main"), m["cas"].__setitem__("declared_refs", ["refs/heads/main"])), "CUTOVER-MAIN-REF"),
            ("cas-duplicate", lambda m: m["refs"].append(copy.deepcopy(m["refs"][0])), "CUTOVER-EXTRA-REF"),
            ("crash-receipt-shape", lambda m: m["outputs"].__setitem__(slice(None), "bad"), "CUTOVER-MALFORMED"),
            ("retry-id", lambda m: m.__setitem__("transaction_id", "bad"), "CUTOVER-TRANSACTION-ID"),
            ("rollback-illegal", lambda m: (m["ledger"][0].__setitem__("from_epoch", "point_of_no_return"), m["ledger"][0].__setitem__("to_epoch", "legacy_restored")), "CUTOVER-ILLEGAL-TRANSITION"),
            ("activation-event", lambda m: m["ledger"][0].__setitem__("event_kind", 7), None),
            ("effects-policy", lambda m: m["roles"].__setitem__("integrator", "other"), "CUTOVER-WRONG-ROLE"),
            ("dry-run-main", lambda m: m["cas"].__setitem__("disposable_test_repo", "yes"), "CUTOVER-CAS"),
            ("missing-executable-contract", lambda m: m["adapters"][0].__setitem__("executable", "missing.py"), "CUTOVER-ADAPTER"),
            ("authority-token", lambda m: m["authority_snapshot"].__setitem__("token_digest", D0), "CUTOVER-AUTHORITY-TOKEN"),
            ("prepared-patch-approval", lambda m: m["candidate"].__setitem__("prepared_patch_digest", D0), "CUTOVER-WRONG-APPROVAL"),
            ("finding-shape", lambda m: m["findings"].append({"code": "X", "severity": "error", "path": "manifest", "message": "bad"}), "CUTOVER-FINDING"),
        ]
        self.assertGreaterEqual(len(cases), 32)
        for name, mutate, code in cases:
            with self.subTest(case=name):
                self.assert_rejected(mutate, code)


class PropertyTests(CutoverFixture):
    def test_exhaustive_transition_pair_matrix_64_cases(self):
        count = 0
        for source, target in itertools.product(CUT.EPOCHS, repeat=2):
            count += 1
            item = event(from_epoch=source, to_epoch=target) if target in CUT.LEGAL_TRANSITIONS[source] else None
            if item is None:
                bad = event()
                bad["from_epoch"], bad["to_epoch"] = source, target
                bad["allowed_write_authority"] = CUT.EXPECTED_AUTHORITY[target]
                bad["issue_store_frozen"] = target in {"legacy_frozen", "prepared", "post_cutover_audit", "point_of_no_return", "write_frozen_repair"}
                bad["event_digest"] = CUT.digest_value({key: value for key, value in bad.items() if key != "event_digest"})
                with self.assertRaises(CUT.CutoverError):
                    CUT.validate_ledger([bad], "tx-0037-safe-core")
            else:
                CUT.validate_ledger([item], "tx-0037-safe-core")
        self.assertEqual(count, 64)

    def test_exhaustive_authority_write_matrix_32_cases(self):
        count = 0
        for epoch, authority in itertools.product(CUT.EPOCHS, CUT.WRITE_AUTHORITIES):
            count += 1
            self.assertEqual(authority == CUT.EXPECTED_AUTHORITY[epoch], sum([authority == CUT.EXPECTED_AUTHORITY[epoch]]) == 1)
        self.assertEqual(count, 32)

    def test_generated_existing_absent_ref_subsets_8_cases(self):
        refs = [f"refs/autodocs/cutover-test/r{index}" for index in range(3)]
        count = 0
        for mask in range(8):
            expectations = []
            for index, ref in enumerate(refs):
                expectations.append({"name": ref, "expected_oid": self.source if mask & (1 << index) else None, "target_oid": self.source})
            transaction = CUT.plan_cas(expectations, refs)
            self.assertIn(b"start\0", transaction)
            self.assertIn(b"prepare\0commit\0", transaction)
            count += 1
        self.assertEqual(count, 8)

    def test_event_chain_prefixes_8_cases(self):
        path = ["legacy_active", "legacy_frozen", "prepared", "issue_store_active", "post_cutover_audit", "point_of_no_return", "write_frozen_repair", "issue_store_active"]
        events = []
        previous = None
        for index, target in enumerate(path):
            source = path[index - 1] if index else "legacy_active"
            current = event(index + 1, source, target, previous)
            events.append(current)
            previous = current["event_digest"]
            CUT.validate_ledger(events, "tx-0037-safe-core")
        self.assertEqual(len(events), 8)

    def test_canonical_permutations_64_cases_seed_37002(self):
        rng = random.Random(37002)
        expected = CUT.canonical_json(self.manifest)
        items = list(self.manifest.items())
        for _ in range(64):
            rng.shuffle(items)
            self.assertEqual(CUT.canonical_json(dict(items)), expected)


class CasTests(unittest.TestCase):
    temp: tempfile.TemporaryDirectory[str]
    repo: Path
    one: str
    two: str

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name).resolve() / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-b", "trunk"], cwd=self.repo, check=True, capture_output=True)
        git(self.repo, "config", "user.email", "cas@example.invalid")
        git(self.repo, "config", "user.name", "CAS Fixture")
        (self.repo / ".issue-cutover-disposable-test-repo").write_text("issue-cutover-disposable-test-repo@v1\n", encoding="utf-8")
        (self.repo / "one").write_text("one\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "one")
        self.one = git(self.repo, "rev-parse", "HEAD")
        (self.repo / "two").write_text("two\n", encoding="utf-8")
        git(self.repo, "add", "two")
        git(self.repo, "commit", "-m", "two")
        self.two = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self):
        self.temp.cleanup()

    def test_atomic_multi_ref_success_and_post_cas_recovery_inspection(self):
        refs = ["refs/autodocs/cutover-test/a", "refs/autodocs/cutover-test/b"]
        git(self.repo, "update-ref", refs[0], self.one)
        result = CUT.execute_disposable_cas(self.repo, [
            {"name": refs[0], "expected_oid": self.one, "target_oid": self.two},
            {"name": refs[1], "expected_oid": None, "target_oid": self.two},
        ], refs, dry_run=False)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual([CUT.resolve_ref(self.repo, ref) for ref in refs], [self.two, self.two])

    def test_competitor_is_all_or_none(self):
        refs = ["refs/autodocs/cutover-test/a", "refs/autodocs/cutover-test/b"]
        git(self.repo, "update-ref", refs[0], self.two)
        before = {ref: CUT.resolve_ref(self.repo, ref) for ref in refs}
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.execute_disposable_cas(self.repo, [
                {"name": refs[0], "expected_oid": self.one, "target_oid": self.one},
                {"name": refs[1], "expected_oid": None, "target_oid": self.two},
            ], refs, dry_run=False)
        self.assertEqual(raised.exception.code, "CUTOVER-CAS-COMPETITOR")
        self.assertEqual({ref: CUT.resolve_ref(self.repo, ref) for ref in refs}, before)

    def test_dry_run_writes_no_ref_object_file_lock_or_signature(self):
        ref = "refs/autodocs/cutover-test/dry"
        before = sorted(path.relative_to(self.repo).as_posix() for path in self.repo.rglob("*"))
        result = CUT.execute_disposable_cas(self.repo, [{"name": ref, "expected_oid": None, "target_oid": self.two}], [ref], dry_run=True)
        after = sorted(path.relative_to(self.repo).as_posix() for path in self.repo.rglob("*"))
        self.assertEqual(result["mutation"], "none")
        self.assertIsNone(CUT.resolve_ref(self.repo, ref))
        self.assertEqual(before, after)

    def test_main_and_undeclared_refs_rejected(self):
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.plan_cas([{"name": "refs/heads/main", "expected_oid": None, "target_oid": self.one}], ["refs/heads/main"])
        self.assertEqual(raised.exception.code, "CUTOVER-MAIN-REF")
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.plan_cas([{"name": "refs/autodocs/cutover-test/x", "expected_oid": None, "target_oid": self.one}], ["refs/autodocs/cutover-test/y"])
        self.assertEqual(raised.exception.code, "CUTOVER-EXTRA-REF")

    def test_non_disposable_repository_rejected(self):
        (self.repo / ".issue-cutover-disposable-test-repo").unlink()
        with self.assertRaises(CUT.CutoverError) as raised:
            CUT.execute_disposable_cas(self.repo, [{"name": "refs/autodocs/cutover-test/x", "expected_oid": None, "target_oid": self.one}], ["refs/autodocs/cutover-test/x"], dry_run=True)
        self.assertEqual(raised.exception.code, "CUTOVER-CAS-NOT-DISPOSABLE")


class SchemaFixtureTests(unittest.TestCase):
    def test_fixture_manifests_are_complete_and_runtime_classified(self):
        for schema_name, validator in (
            ("cutover-transaction-manifest-v1", CUT.validate_manifest),
            ("cutover-control-ledger-v2", lambda value: CUT.validate_ledger([value], value.get("transaction_id", "missing"))),
        ):
            root = ROOT / "issues/_schema/fixtures" / schema_name
            index = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            for relative in index["valid"]:
                validator(json.loads((root / relative).read_text(encoding="utf-8")))
            for relative in index["invalid"]:
                with self.assertRaises(CUT.CutoverError, msg=relative):
                    validator(json.loads((root / relative).read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
