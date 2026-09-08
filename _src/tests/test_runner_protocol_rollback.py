import json, shutil, tempfile, unittest
from pathlib import Path
from _src.tools.runner_protocol_rollback import FAILURES, EVENTS, MARKER, BLOCKED, execute, load_bundle, sha256_bytes
ROOT=Path(__file__).resolve().parents[2]
class RollbackTests(unittest.TestCase):
 def setUp(self):
  self.tmp=Path(tempfile.mkdtemp());self.addCleanup(shutil.rmtree,self.tmp,True)
  p=self.tmp/"issues/_policy";p.mkdir(parents=True);shutil.copy(ROOT/"issues/_policy/runner-protocol-rollback-v1.json",p)
  (self.tmp/"agent-workflow.json").write_text("bad\n");(p/"runner-service.json").write_text("bad\n")
 def test_bundle_is_corrected_lineage_and_digest_bound(self):
  targets=load_bundle(self.tmp);self.assertEqual({t["path"] for t in targets},{"agent-workflow.json","issues/_policy/runner-service.json"})
  self.assertTrue(all(sha256_bytes(t["payload"])==t["sha256"] for t in targets))
 def test_service_is_restored_before_selector_and_events_verified(self):
  r=execute(self.tmp);self.assertTrue(r["ok"]);self.assertEqual(json.loads((self.tmp/MARKER).read_text())["status"],"restored")
  self.assertEqual([json.loads(x)["event"] for x in (self.tmp/EVENTS).read_text().splitlines()],["rollback-started","rollback-restored"])
  self.assertEqual(json.loads((self.tmp/"agent-workflow.json").read_text())["runner_protocol"],"runner-request@v1")
 def test_every_failure_is_durably_blocked(self):
  for failure in FAILURES:
   with self.subTest(failure=failure):
    r=execute(self.tmp,timeout=0,fail_at=failure);self.assertFalse(r["ok"]);self.assertTrue((self.tmp/BLOCKED).exists())
 def test_active_claim_drain_timeout_blocks(self):
  claims=self.tmp/".runner/claims";claims.mkdir(parents=True);(claims/"a.lease.json").write_text("{}")
  self.assertFalse(execute(self.tmp,timeout=0)["ok"]);self.assertEqual(json.loads((self.tmp/BLOCKED).read_text())["reason"],"failure")
 def test_existing_lock_is_exclusive(self):
  (self.tmp/".runner/rollback-v1.lock").mkdir(parents=True);self.assertEqual(execute(self.tmp)["reason"],"lock")
if __name__=="__main__":unittest.main()
