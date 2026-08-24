"""Tests for chore_tool_inventory.py (Task 0038-14).

Two groups:

1. Schema/coverage tests for the classification tool itself (validate()
   against the shipped data file and against deliberately broken fixtures).
2. Fault-injection tests that dynamically exercise the *actual* commit-point
   code of the fully classified mutating tools (review_flags.py,
   curation_flags.py, review_ingest.py, curation_ingest.py,
   migriere_status_backfill.py, sync_to_devel.sh) against temporary
   fixtures, proving -- or, in one deliberately documented case, disproving
   -- the "retries neither duplicate nor erase work" bar from the Task's
   Definition of Done. None of these tests touch the real repository state
   (real /tmp/autodocs, ~/devel/autodocs.bak, or spec/records/).
"""
import copy
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import chore_tool_inventory as cti  # noqa: E402
import review_flags  # noqa: E402
import curation_flags  # noqa: E402
import review_ingest  # noqa: E402
import curation_ingest  # noqa: E402
import migriere_status_backfill as msb  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = TOOLS_DIR / "sync_to_devel.sh"


# --------------------------------------------------------------------------
# Group 1: schema / coverage validation of the inventory tool itself
# --------------------------------------------------------------------------

class InventorySchemaTests(unittest.TestCase):
    def test_shipped_data_passes_check(self):
        data = cti.load_data()
        errors, stats = cti.validate(data, REPO_ROOT)
        self.assertEqual(errors, [])
        self.assertGreater(stats["classified_count"], 0)
        self.assertEqual(stats["stale_inventory_entries"], [])

    def test_every_classified_category_is_recognized(self):
        data = cti.load_data()
        for entry in data["classified"]:
            self.assertIn(entry["category"], cti.CATEGORIES)

    def test_no_path_appears_in_both_classified_and_enumerated(self):
        data = cti.load_data()
        classified = {e["path"] for e in data["classified"]}
        enumerated = {e["path"] for e in data["enumerated"]}
        self.assertEqual(classified & enumerated, set())

    def test_classified_paths_are_a_named_first_pass_subset_not_everything(self):
        data = cti.load_data()
        # Task 0038-14 explicitly scopes its full-classification pass to four
        # named categories; this test locks in the "not exhaustive" property
        # so a future edit cannot silently claim completeness it doesn't have.
        self.assertLess(len(data["classified"]), len(data["enumerated"]) + len(data["classified"]))
        self.assertGreater(len(data["enumerated"]), 0)

    def test_validate_flags_stale_entry_for_untracked_path(self):
        data = cti.load_data()
        broken = copy.deepcopy(data)
        broken["enumerated"].append({
            "path": "_src/tools/does_not_exist_anymore.py",
            "category_guess": "unclassified",
            "note": "synthetic stale entry for test",
        })
        errors, _stats = cti.validate(broken, REPO_ROOT)
        self.assertTrue(any("no longer matches a tracked script" in e for e in errors))

    def test_validate_flags_missing_required_field(self):
        data = cti.load_data()
        broken = copy.deepcopy(data)
        del broken["classified"][0]["write_set"]
        errors, _stats = cti.validate(broken, REPO_ROOT)
        self.assertTrue(any("write_set" in e for e in errors))

    def test_validate_flags_bad_category(self):
        data = cti.load_data()
        broken = copy.deepcopy(data)
        broken["classified"][0]["category"] = "not-a-real-category"
        errors, _stats = cti.validate(broken, REPO_ROOT)
        self.assertTrue(any("not one of" in e for e in errors))

    def test_validate_flags_mutating_category_without_commit_points_or_write_set(self):
        data = cti.load_data()
        broken = copy.deepcopy(data)
        broken["classified"][0]["category"] = "destructive"
        broken["classified"][0]["write_set"] = []
        broken["classified"][0]["commit_points"] = []
        errors, _stats = cti.validate(broken, REPO_ROOT)
        self.assertTrue(any("declares no commit_points and no write_set" in e for e in errors))

    def test_validate_flags_duplicate_path(self):
        data = cti.load_data()
        broken = copy.deepcopy(data)
        broken["classified"].append(copy.deepcopy(broken["classified"][0]))
        errors, _stats = cti.validate(broken, REPO_ROOT)
        self.assertTrue(any("duplicate path" in e for e in errors))

    def test_cli_check_exit_code_zero_on_shipped_data(self):
        rc = cti.main(["--check", "--root", str(REPO_ROOT)])
        self.assertEqual(rc, 0)

    def test_cli_check_exit_code_nonzero_on_broken_data(self):
        data = cti.load_data()
        broken = copy.deepcopy(data)
        broken["schema_version"] = 999
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(broken, fh)
            broken_path = fh.name
        self.addCleanup(os.unlink, broken_path)
        rc = cti.main(["--check", "--root", str(REPO_ROOT), "--data", broken_path])
        self.assertEqual(rc, 1)

    def test_list_classified_filtered_by_category_only_returns_that_category(self):
        data = cti.load_data()
        destructive = [e["path"] for e in data["classified"] if e["category"] == "destructive"]
        self.assertIn("_src/tools/sync_to_devel.sh", destructive)
        self.assertIn("_src/tools/publish_public_site.sh", destructive)


# --------------------------------------------------------------------------
# Group 2: fault injection against the real classified tools
# --------------------------------------------------------------------------

class ReviewFlagsFaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        self._orig_queue = review_flags.QUEUE
        self._orig_open = review_flags.OPEN_DIR
        self._orig_claimed = review_flags.CLAIMED_DIR
        self._orig_done = review_flags.DONE_DIR
        base = Path(self._tmp.name) / "review-queue"
        review_flags.QUEUE = base
        review_flags.OPEN_DIR = base / "open"
        review_flags.CLAIMED_DIR = base / "claimed"
        review_flags.DONE_DIR = base / "done"
        self.addCleanup(self._restore)

    def _restore(self):
        review_flags.QUEUE = self._orig_queue
        review_flags.OPEN_DIR = self._orig_open
        review_flags.CLAIMED_DIR = self._orig_claimed
        review_flags.DONE_DIR = self._orig_done

    def test_write_review_flag_retry_does_not_duplicate(self):
        entry = {"suspects": [], "repairs": []}
        first = review_flags.write_review_flag("REQ-1", "backend_mismatch", entry, "recpath", "campaign-1")
        self.assertIsNotNone(first)
        # Retry with the same rid (e.g. a caller re-running after a timeout).
        second = review_flags.write_review_flag("REQ-1", "backend_mismatch", entry, "recpath", "campaign-1")
        self.assertIsNone(second)  # commit point refuses to overwrite an open flag
        self.assertEqual(len(review_flags.list_open_flags()), 1)

    def test_claim_flag_retry_is_race_safe(self):
        entry = {"suspects": [], "repairs": []}
        path = review_flags.write_review_flag("REQ-2", "backend_mismatch", entry, "recpath", "campaign-1")
        first_claim = review_flags.claim_flag(path, agent="agent-a")
        self.assertIsNotNone(first_claim)
        # A second claim attempt against the now-moved source path must fail
        # closed (no partial/duplicated claimed state), not silently invent one.
        second_claim = review_flags.claim_flag(path, agent="agent-b")
        self.assertIsNone(second_claim)
        claimed_files = list(review_flags.CLAIMED_DIR.glob("*.json"))
        self.assertEqual(len(claimed_files), 1)


class CurationFlagsFaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        self._orig_queue = curation_flags.QUEUE
        self._orig_open = curation_flags.OPEN_DIR
        self._orig_claimed = curation_flags.CLAIMED_DIR
        self._orig_done = curation_flags.DONE_DIR
        base = Path(self._tmp.name) / "curation-queue"
        curation_flags.QUEUE = base
        curation_flags.OPEN_DIR = base / "open"
        curation_flags.CLAIMED_DIR = base / "claimed"
        curation_flags.DONE_DIR = base / "done"
        self.addCleanup(self._restore)

    def _restore(self):
        curation_flags.QUEUE = self._orig_queue
        curation_flags.OPEN_DIR = self._orig_open
        curation_flags.CLAIMED_DIR = self._orig_claimed
        curation_flags.DONE_DIR = self._orig_done

    def _decision(self, rid="REQ-9"):
        return {
            "id": rid, "outcome": "accept", "decided_by": "alice",
            "identity": "self_declared", "decided_at": "2026-08-20T00:00:00Z",
            "rationale": "use spelling from line X",
        }

    def test_write_curation_flag_retry_does_not_duplicate(self):
        first = curation_flags.write_curation_flag(self._decision())
        self.assertIsNotNone(first)
        second = curation_flags.write_curation_flag(self._decision())
        self.assertIsNone(second)
        self.assertEqual(len(curation_flags.list_open_flags()), 1)

    def test_complete_flag_crash_between_archive_and_unlink_is_recoverable(self):
        """Fault injection: simulate a process crash inside complete_flag()
        after the DONE_DIR archive write succeeds but before the source
        unlink runs, then prove a retry converges to the correct terminal
        state without losing or duplicating the record.
        """
        path = curation_flags.write_curation_flag(self._decision("REQ-10"))
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["completed_at"] = "2026-08-20T00:00:01Z"
        payload["outcome_class"] = "no_action"

        # Simulate the first (interrupted) half of complete_flag(): archive
        # written, source NOT yet unlinked (this is exactly what a crash
        # between curation_flags.py's line ~160 write and ~161 unlink would
        # leave behind).
        curation_flags._ensure_dirs()
        target = curation_flags.DONE_DIR / path.name
        curation_flags._atomic_write(target, payload)
        # Source is still present -- nothing lost, and duplicated (archived +
        # still-open) rather than erased, which is the safe direction to fail in.
        self.assertTrue(path.exists())
        self.assertTrue(target.exists())

        # Retry: caller re-invokes complete_flag() on the still-present source.
        final_target = curation_flags.complete_flag(path, note="resumed after simulated crash")
        self.assertEqual(final_target, target)
        self.assertFalse(path.exists())  # source now cleaned up
        final_payload = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(final_payload["id"], "REQ-10")
        self.assertEqual(final_payload["operator_note"], "resumed after simulated crash")
        # Exactly one archived record for this id -- the retry updated the
        # archive in place rather than duplicating it.
        self.assertEqual(len(list(curation_flags.DONE_DIR.glob("REQ-10*.json"))), 1)


class ReviewIngestFaultInjectionTests(unittest.TestCase):
    """apply_decision() commit-point behavior, verified dynamically rather
    than assumed from reading the source."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        self._record_path = Path(self._tmp.name) / "REQ-1.json"
        record = {
            "id": "REQ-1",
            "blocks": [{"t": "requirement_text", "text_raw": "hello world", "repairs": []}],
            "status": {"state": "proposed/x"},
        }
        self._record_path.write_text(json.dumps(record), encoding="utf-8")

        self._orig_find_record = review_ingest.find_record
        self._orig_queue = review_ingest.QUEUE
        review_ingest.find_record = lambda rid: self._record_path
        review_ingest.QUEUE = Path(self._tmp.name) / "review-queue"
        (review_ingest.QUEUE / "open").mkdir(parents=True, exist_ok=True)
        (review_ingest.QUEUE / "claimed").mkdir(parents=True, exist_ok=True)
        self.addCleanup(self._restore)

    def _restore(self):
        review_ingest.find_record = self._orig_find_record
        review_ingest.QUEUE = self._orig_queue

    def _decision(self):
        text_hash = review_ingest.text_hash("hello world", [])
        return {
            "id": "REQ-1", "text_hash": text_hash, "outcome": "accept",
            "decided_by": "alice", "decided_at": "2026-08-20T00:00:00Z",
            "rationale": "looks fine", "flag_id": "REQ-1",
        }

    def test_apply_decision_review_flags_entry_is_idempotent(self):
        d = self._decision()
        paket = {"identity": "self_declared", "campaign": "c1"}
        review_ingest.apply_decision(d, paket, apply=True)
        review_ingest.apply_decision(d, paket, apply=True)  # retry
        record = json.loads(self._record_path.read_text())
        self.assertEqual(len(record["blocks"][0]["review_flags"]), 1)

    def test_apply_decision_history_duplicates_on_retry_KNOWN_DEFECT(self):
        """DOCUMENTS A REAL DEFECT, does not endorse it.

        review_ingest.apply_decision()'s history[] append is not guarded by
        the same flag_id-keyed idempotency check that protects
        review_flags[]. An at-least-once retry of the *same* decision (e.g.
        caller-side timeout retry, or the same GitHub issue re-ingested)
        duplicates the audit-log entry. Classified and flagged in
        chore_tool_inventory_data.json under review_ingest.py's findings;
        not fixed here because review_ingest.py is outside Task 0038-14's
        declared write scope. This test exists so the defect is verified
        evidence, not a claim from reading the source, and so a future fix
        has a red test to turn green.
        """
        d = self._decision()
        paket = {"identity": "self_declared", "campaign": "c1"}
        review_ingest.apply_decision(d, paket, apply=True)
        review_ingest.apply_decision(d, paket, apply=True)  # retry
        record = json.loads(self._record_path.read_text())
        self.assertEqual(len(record["history"]), 2,
                          "expected the known duplication defect; if this now "
                          "fails, review_ingest.py.apply_decision() may have "
                          "been fixed -- update chore_tool_inventory_data.json's "
                          "review_ingest.py findings/category accordingly")


class CurationIngestFaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        self._orig_queue = curation_flags.QUEUE
        self._orig_open = curation_flags.OPEN_DIR
        self._orig_claimed = curation_flags.CLAIMED_DIR
        self._orig_done = curation_flags.DONE_DIR
        base = Path(self._tmp.name) / "curation-queue"
        curation_flags.QUEUE = base
        curation_flags.OPEN_DIR = base / "open"
        curation_flags.CLAIMED_DIR = base / "claimed"
        curation_flags.DONE_DIR = base / "done"
        self.addCleanup(self._restore)

    def _restore(self):
        curation_flags.QUEUE = self._orig_queue
        curation_flags.OPEN_DIR = self._orig_open
        curation_flags.CLAIMED_DIR = self._orig_claimed
        curation_flags.DONE_DIR = self._orig_done

    def test_retry_is_idempotent_via_write_curation_flag_guard(self):
        paket = {
            "schema": curation_ingest.PACKAGE_SCHEMA, "identity": "self_declared",
            "campaign": "html-curation",
            "decisions": [{
                "kind": "curation_request", "id": "REQ-5", "outcome": "accept",
                "decided_by": "alice", "decided_at": "2026-08-20T00:00:00Z",
                "rationale": "use existing spelling",
            }],
        }
        pfad = Path(self._tmp.name) / "paket.json"
        pfad.write_text(json.dumps(paket), encoding="utf-8")

        first = curation_ingest.ingest(pfad, apply=True, from_issue_body=False)
        self.assertEqual(first["ergebnisse"][0]["status"], "ok")
        second = curation_ingest.ingest(pfad, apply=True, from_issue_body=False)  # retry
        self.assertEqual(second["ergebnisse"][0]["status"], "skipped")
        self.assertEqual(len(curation_flags.list_open_flags()), 1)


class MigriereStatusBackfillFaultInjectionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        self._orig_records = msb.RECORDS
        msb.RECORDS = Path(self._tmp.name) / "records"
        msb.RECORDS.mkdir(parents=True, exist_ok=True)
        self.addCleanup(self._restore)

    def _restore(self):
        msb.RECORDS = self._orig_records

    def _write_record(self, name, payload):
        (msb.RECORDS / name).write_text(json.dumps(payload), encoding="utf-8")

    def test_retry_skips_completed_records(self):
        self._write_record("a.json", {"id": "a"})
        self._write_record("b.json", {"id": "b"})
        rc1 = msb.main(["--apply"])
        self.assertEqual(rc1, 0)
        rec_a_after_1 = (msb.RECORDS / "a.json").read_text()
        rec_b_after_1 = (msb.RECORDS / "b.json").read_text()
        self.assertIn("status", json.loads(rec_a_after_1))
        self.assertIn("status", json.loads(rec_b_after_1))
        self.assertEqual(len(json.loads(rec_a_after_1)["history"]), 1)

        rc2 = msb.main(["--apply"])  # retry over an already-fully-migrated set
        self.assertEqual(rc2, 0)
        rec_a_after_2 = (msb.RECORDS / "a.json").read_text()
        rec_b_after_2 = (msb.RECORDS / "b.json").read_text()
        # Byte-identical: the retry did not touch already-migrated records
        # (no duplicate history entries, no re-write at all).
        self.assertEqual(rec_a_after_1, rec_a_after_2)
        self.assertEqual(rec_b_after_1, rec_b_after_2)

    def test_corrupted_record_fails_loud_without_touching_others(self):
        """Fault injection: simulate a crash mid-write leaving one record
        truncated (the concrete, verified consequence of this tool's
        non-atomic Path.write_text commit point), and prove the retry does
        not silently accept corrupted data and does not disturb any other
        already-migrated record.
        """
        self._write_record("a.json", {"id": "a"})
        self._write_record("b.json", {"id": "b"})
        rc1 = msb.main(["--apply"])
        self.assertEqual(rc1, 0)

        # Introduce a THIRD, not-yet-migrated record whose write gets
        # interrupted mid-flight -- simulate by hand-truncating valid JSON.
        (msb.RECORDS / "c.json").write_text('{"id": "c"', encoding="utf-8")  # truncated, invalid JSON

        with self.assertRaises(json.JSONDecodeError):
            msb.main(["--apply"])  # retry: fails loud on the corrupted record

        # Already-migrated records a/b must be completely untouched by the
        # aborted retry (no partial re-processing, no duplication, no loss).
        rec_a = json.loads((msb.RECORDS / "a.json").read_text())
        rec_b = json.loads((msb.RECORDS / "b.json").read_text())
        self.assertEqual(len(rec_a["history"]), 1)
        self.assertEqual(len(rec_b["history"]), 1)


@unittest.skipUnless(SYNC_SCRIPT.is_file(), "sync_to_devel.sh not found")
class SyncToDevelFaultInjectionTests(unittest.TestCase):
    """sync_to_devel.sh hard-codes its SRC/DST/LOG/LOCK paths (by design --
    it is a fixed hourly backup job, not a general-purpose CLI). To fault-
    inject it safely we copy its exact body into a temporary script with
    only those four path constants substituted to fixture paths, then
    execute the real, unmodified control-flow/guard logic as a subprocess.
    The real script under _src/tools/ is never executed or modified."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.src = base / "src"
        self.dst = base / "dst"
        self.log = base / "sync.log"
        self.lock = base / "sync.lock"
        self.script_path = base / "sync_to_devel_fixture.sh"
        self._write_fixture_script()

    def _write_fixture_script(self):
        original = SYNC_SCRIPT.read_text(encoding="utf-8")
        patched = original.replace(
            'SRC="/private/tmp/autodocs"', 'SRC="%s"' % self.src,
        ).replace(
            'DST="$HOME/devel/autodocs.bak"', 'DST="%s"' % self.dst,
        ).replace(
            'LOG="$HOME/devel/autodocs-sync.log"', 'LOG="%s"' % self.log,
        ).replace(
            'LOCK="$HOME/devel/.autodocs-sync.lock"', 'LOCK="%s"' % self.lock,
        )
        # Sanity check the substitution actually took (fails loud if
        # sync_to_devel.sh's constant lines are ever reworded).
        assert 'SRC="%s"' % self.src in patched, "SRC substitution did not match; script layout changed"
        assert 'DST="%s"' % self.dst in patched, "DST substitution did not match; script layout changed"
        assert 'LOCK="%s"' % self.lock in patched, "LOCK substitution did not match; script layout changed"
        self.script_path.write_text(patched, encoding="utf-8")
        self.script_path.chmod(self.script_path.stat().st_mode | stat.S_IEXEC)

    def _run(self):
        return subprocess.run(
            ["/bin/bash", str(self.script_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )

    def _make_valid_source(self, file_count=1010):
        self.src.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(self.src)], check=True)
        (self.src / "AGENTS.md").write_text("agents", encoding="utf-8")
        src_dir = self.src / "_src"
        src_dir.mkdir(parents=True, exist_ok=True)
        for i in range(file_count):
            (src_dir / ("f%d.txt" % i)).write_text("x", encoding="utf-8")

    def test_lock_prevents_concurrent_run(self):
        self.lock.mkdir(parents=True)  # simulate another run already in flight
        result = self._run()
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.dst.exists())  # nothing touched
        log_text = self.log.read_text(encoding="utf-8")
        self.assertIn("SKIP", log_text)

    def test_missing_git_guard_aborts_before_destructive_rsync(self):
        self.src.mkdir(parents=True)  # source exists but has no .git
        result = self._run()
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.dst.exists())
        self.assertIn("ABORT", self.log.read_text(encoding="utf-8"))

    def test_truncated_source_guard_aborts_before_destructive_rsync(self):
        (self.src / ".git").mkdir(parents=True)
        (self.src / "AGENTS.md").write_text("agents", encoding="utf-8")
        src_dir = self.src / "_src"
        src_dir.mkdir(parents=True, exist_ok=True)
        for i in range(5):  # far below the 1000-file guard threshold
            (src_dir / ("f%d.txt" % i)).write_text("x", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.dst.exists())
        self.assertIn("ABORT", self.log.read_text(encoding="utf-8"))
        self.assertIn("truncated", self.log.read_text(encoding="utf-8"))

    def test_retry_after_success_is_a_no_op(self):
        self._make_valid_source(file_count=1000)
        first = self._run()
        self.assertEqual(first.returncode, 0)
        self.assertTrue(self.dst.exists())
        snapshot = sorted((p.relative_to(self.dst), p.stat().st_size)
                          for p in self.dst.rglob("*") if p.is_file())

        second = self._run()  # retry against an unchanged source
        self.assertEqual(second.returncode, 0)
        snapshot_after_retry = sorted((p.relative_to(self.dst), p.stat().st_size)
                                      for p in self.dst.rglob("*") if p.is_file())
        self.assertEqual(snapshot, snapshot_after_retry)
        log_lines = [ln for ln in self.log.read_text(encoding="utf-8").splitlines() if "OK:" in ln]
        self.assertEqual(len(log_lines), 2)  # both runs completed and logged, no duplication of DST content

    def test_deleted_source_file_propagates_as_delete_not_duplication(self):
        self._make_valid_source(file_count=1010)  # margin above the 1000-file guard so one deletion cannot trip it
        self._run()
        self.assertTrue((self.dst / "_src" / "f0.txt").exists())
        (self.src / "_src" / "f0.txt").unlink()
        self._run()
        self.assertFalse((self.dst / "_src" / "f0.txt").exists())  # --delete propagated, not left as stale duplicate


if __name__ == "__main__":
    unittest.main()
