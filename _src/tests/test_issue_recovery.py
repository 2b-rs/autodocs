import hashlib
import itertools
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src/tools/issue_recovery.py"
ACTIONS = ROOT / "_src/runner/issue-recovery-actions-v1.json"


class IssueRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "issues/items").mkdir(parents=True)
        (self.repo / "provenance").mkdir()
        (self.repo / "claims").mkdir()
        (self.repo / "artifacts").mkdir()
        (self.repo / "sessions").mkdir()
        (self.repo / "agent-workflow.json").write_text(json.dumps({
            "schema": "agent-workflow-bootstrap@v1", "authority_profile": "issue-store",
            "authority_epoch": "issue-store-writable", "write_phase": "issue-store-writable"
        }))
        for name, value in (("issues/items/0037-44.json", "issue"),
                            ("issues/items/0037-44.criteria.json", "criterion"),
                            ("issues/items/0037-44.closure.json", "closure"),
                            ("provenance/p.jsonl", "event\n"),
                            ("claims/c.json", "claim"), ("artifacts/a.bin", "artifact"),
                            ("sessions/s.json", "session")):
            path = self.repo / name
            path.write_text(value)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, ok=True):
        cp = subprocess.run([sys.executable, str(TOOL), *args], cwd=ROOT,
                            text=True, capture_output=True)
        if ok and cp.returncode:
            self.fail(cp.stdout + cp.stderr)
        return cp, json.loads(cp.stdout)

    def test_freeze_export_restore_replay_repair_release(self):
        control = self.repo / "control.json"
        _, frozen = self.run_cli("freeze", "--repo", str(self.repo), "--control", str(control),
                                 "--expected-generation", "0", "--actor", "wesley")
        self.assertEqual(frozen["generation"], 1)
        self.assertEqual(json.loads((self.repo / "agent-workflow.json").read_text())["authority_epoch"],
                         "issue-store-write-frozen")
        selector = json.loads((self.repo / "agent-workflow.json").read_text())
        preimage = dict(selector); claimed = preimage.pop("selector_digest")
        self.assertEqual(claimed, "sha256:" + hashlib.sha256(
            json.dumps(preimage, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
        self.assertFalse((self.repo / "sessions/s.json").exists())
        self.assertFalse((self.repo / "claims/c.json").exists())
        bundle = self.repo / "bundle.json"
        self.run_cli("export", "--repo", str(self.repo), "--control", str(control),
                     "--bundle", str(bundle))
        exported = json.loads(bundle.read_text())
        self.assertTrue({"issues", "provenance", "claims", "artifacts"}.issubset(
            {entry["path"].split("/", 1)[0] for entry in exported["entries"]}))
        restored = self.repo / "restored"
        self.run_cli("restore", "--bundle", str(bundle), "--target", str(restored))
        self.assertEqual((restored / "issues/items/0037-44.json").read_text(), "issue")
        self.assertEqual((restored / "issues/items/0037-44.criteria.json").read_text(), "criterion")
        self.assertEqual((restored / "issues/items/0037-44.closure.json").read_text(), "closure")
        events = self.repo / "events.json"
        events.write_text(json.dumps([{"id": "e1", "sequence": 1, "path": "issues/items/new.json",
                                      "content": "new"}]))
        self.run_cli("replay", "--target", str(restored), "--events", str(events))
        self.run_cli("replay", "--target", str(restored), "--events", str(events))
        self.assertEqual((restored / "issues/items/new.json").read_text(), "new")
        repair = self.repo / "repair.json"
        repair.write_text(json.dumps([{"path": "issues/items/new.json",
                                      "expected_sha256": hashlib.sha256(b"new").hexdigest(),
                                      "content": "repaired"}]))
        self.run_cli("repair", "--target", str(restored), "--control", str(control),
                     "--plan", str(repair))
        release = self.repo / "release.json"
        payload = {"schema": "issue-recovery-release@v1", "actor": "owner",
                   "generation": 1, "signature_verified": True}
        payload["payload_sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        release.write_text(json.dumps(payload))
        self.run_cli("release", "--repo", str(self.repo), "--control", str(control),
                     "--release", str(release), "--expected-generation", "1")
        self.assertEqual(json.loads(control.read_text())["generation"], 2)

    def test_refusals_and_conflict(self):
        control = self.repo / "control.json"
        cp, out = self.run_cli("freeze", "--repo", str(self.repo), "--control", str(control),
                                "--expected-generation", "9", "--actor", "x", ok=False)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(out["code"], "RECOVERY-STALE-EPOCH")
        self.run_cli("freeze", "--repo", str(self.repo), "--control", str(control),
                     "--expected-generation", "0", "--actor", "x")
        target = self.repo / "target"
        (target / "issues").mkdir(parents=True)
        (target / "issues/x").write_text("old")
        events = self.repo / "events.json"
        events.write_text(json.dumps([{"id": "e1", "sequence": 1, "path": "issues/x", "content": "new"}]))
        cp, out = self.run_cli("replay", "--target", str(target), "--events", str(events), ok=False)
        self.assertEqual(out["code"], "RECOVERY-REPLAY-COLLISION")

    def test_adjacent_malformed_bundle_and_unsigned_release_refuse(self):
        bad = self.repo / "bad.json"
        bad.write_text(json.dumps({"schema": "issue-recovery-export@v1", "entries": [],
                                   "manifest_sha256": "0" * 64}))
        cp, out = self.run_cli("restore", "--bundle", str(bad),
                                "--target", str(self.repo / "bad-target"), ok=False)
        self.assertEqual(out["code"], "RECOVERY-BUNDLE-DIGEST")
        control = self.repo / "control.json"
        self.run_cli("freeze", "--repo", str(self.repo), "--control", str(control),
                     "--expected-generation", "0", "--actor", "x")
        release = self.repo / "unsigned.json"
        release.write_text(json.dumps({"schema": "issue-recovery-release@v1",
                                       "generation": 1, "signature_verified": False}))
        cp, out = self.run_cli("release", "--repo", str(self.repo), "--control", str(control),
                                "--release", str(release), "--expected-generation", "1", ok=False)
        self.assertEqual(out["code"], "RECOVERY-UNSIGNED-RELEASE")

    def test_typed_action_registry_is_fixed_and_complete(self):
        registry = json.loads(ACTIONS.read_text())
        ids = [item["id"] for item in registry["actions"]]
        self.assertEqual(ids, [f"issue-recovery.{name}@v1" for name in
                              ("freeze", "export", "restore", "replay", "repair", "regenerate", "release")])
        self.assertTrue(all(item["argv"][:2] == ["python3", "_src/tools/issue_recovery.py"]
                            for item in registry["actions"]))
        self.assertNotIn("shell", json.dumps(registry).lower())

    def test_regeneration_delegates_only_while_frozen(self):
        control = self.repo / "control.json"
        self.run_cli("freeze", "--repo", str(self.repo), "--control", str(control),
                     "--expected-generation", "0", "--actor", "x")
        tool_dir = self.repo / "_src/tools"
        tool_dir.mkdir(parents=True)
        (tool_dir / "issuectl.py").write_text(
            "import json\nprint(json.dumps({'status':'PASS','stages':7}))\n")
        _, out = self.run_cli("regenerate", "--repo", str(self.repo), "--control", str(control),
                              "--output-root", str(self.repo / "views"))
        self.assertEqual(out["result"], {"status": "PASS", "stages": 7})

    def test_exactly_once_property_all_small_permutations(self):
        cases = 0
        for order in itertools.permutations(range(3)):
            cases += 1
            target = self.repo / ("p" + "".join(map(str, order)))
            target.mkdir()
            events = [{"id": f"e{i}", "sequence": i, "path": f"issues/{i}", "content": str(i)}
                      for i in order]
            path = self.repo / ("events" + "".join(map(str, order)) + ".json")
            path.write_text(json.dumps(events))
            self.run_cli("replay", "--target", str(target), "--events", str(path))
            self.run_cli("replay", "--target", str(target), "--events", str(path))
            self.assertEqual({p.name for p in (target / "issues").iterdir()}, {"0", "1", "2"})
        self.assertEqual(cases, 6)


if __name__ == "__main__":
    unittest.main()
