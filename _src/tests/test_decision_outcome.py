import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import decision_outcome as do  # noqa: E402
import curation_flags as cf  # noqa: E402


class DecisionOutcomeTests(unittest.TestCase):
    def test_register_hook_rejects_unknown_outcome_class(self):
        with self.assertRaises(ValueError):
            do.register_hook("not-a-real-class", lambda payload: None)

    def test_run_hooks_rejects_unknown_outcome_class(self):
        with self.assertRaises(ValueError):
            do.run_hooks("not-a-real-class", {})

    def test_registered_hook_runs_with_payload(self):
        seen = []
        do.register_hook("new_fixture", seen.append)
        errors = do.run_hooks("new_fixture", {"id": "X"})
        self.assertEqual(errors, [])
        self.assertEqual(seen, [{"id": "X"}])

    def test_broken_hook_error_is_collected_not_raised(self):
        def boom(payload):
            raise RuntimeError("deliberate test failure")
        do.register_hook("migration", boom)
        errors = do.run_hooks("migration", {"id": "Y"})
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], RuntimeError)

    def test_run_hooks_with_no_registered_hooks_returns_empty(self):
        self.assertEqual(do.run_hooks("allowlist_exception", {}), [])


class CompleteFlagOutcomeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        self._orig_queue = cf.QUEUE
        self._orig_open = cf.OPEN_DIR
        self._orig_claimed = cf.CLAIMED_DIR
        self._orig_done = cf.DONE_DIR
        base = Path(self._tmp.name)
        cf.QUEUE = base
        cf.OPEN_DIR = base / "open"
        cf.CLAIMED_DIR = base / "claimed"
        cf.DONE_DIR = base / "done"
        self.addCleanup(self._restore)

    def _restore(self):
        cf.QUEUE = self._orig_queue
        cf.OPEN_DIR = self._orig_open
        cf.CLAIMED_DIR = self._orig_claimed
        cf.DONE_DIR = self._orig_done

    def _write_flag(self, rid="SWS_TEST_00001"):
        cf.write_curation_flag({
            "id": rid, "outcome": "accepted", "decided_by": "tester",
            "decided_at": "2026-08-13T00:00:00Z", "rationale": "test fixture",
        })
        return cf.OPEN_DIR / (rid + ".json")

    def test_complete_flag_defaults_outcome_class_to_no_action(self):
        path = self._write_flag()
        target = cf.complete_flag(path)
        payload = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(payload["outcome_class"], "no_action")
        self.assertNotIn("outcome_detail", payload)

    def test_complete_flag_records_explicit_outcome_class_and_detail(self):
        path = self._write_flag("SWS_TEST_00002")
        target = cf.complete_flag(path, outcome_class="allowlist_exception", outcome_detail="RESIDUAL entry added for SWS_TEST_00002")
        payload = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(payload["outcome_class"], "allowlist_exception")
        self.assertEqual(payload["outcome_detail"], "RESIDUAL entry added for SWS_TEST_00002")

    def test_complete_flag_runs_matching_hook(self):
        seen = []
        do.register_hook("db_value_update", seen.append)
        path = self._write_flag("SWS_TEST_00003")
        cf.complete_flag(path, outcome_class="db_value_update")
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["outcome_class"], "db_value_update")

    def test_complete_flag_rejects_unknown_outcome_class(self):
        path = self._write_flag("SWS_TEST_00004")
        with self.assertRaises(ValueError):
            cf.complete_flag(path, outcome_class="totally-made-up")


if __name__ == "__main__":
    unittest.main()
