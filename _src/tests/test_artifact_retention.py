"""Tests for _src/tools/artifact_retention.py (Task `0038-11`).

Covers the nine named Definition-of-Done fixtures — fixed-path export
deletion, empty service-error files, failed-sentinel outputs, empty request
directories, interrupted attempts, reused log names, live claims, clock
skew, and rollback — plus quarantine round-trip, permanent-manifest
protection, current-pointer protection, and CLI dry-run/apply behavior.
"""
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "artifact_retention.py"

SPEC = importlib.util.spec_from_file_location("artifact_retention", TOOL)
assert SPEC and SPEC.loader
ar = importlib.util.module_from_spec(SPEC)
sys.modules["artifact_retention"] = ar
SPEC.loader.exec_module(ar)

DAY = 86400


def _iso(epoch: float) -> str:
    return ar._now_iso(epoch)


class FixtureTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = 1_800_000_000.0  # fixed reference "now" for determinism

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relative: str, content: str = "") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_result(self, task_id, request_id, *, verdict, finished_at, extra=None):
        value = {
            "schema": "legacy-runner-transaction-result@v1",
            "task_id": task_id,
            "request_id": request_id,
            "verdict": verdict,
            "lifecycle_state": "complete" if verdict == "passed" else "failed",
            "finished_at": _iso(finished_at),
        }
        if extra:
            value.update(extra)
        self.write(f"output/logs/{task_id}/{request_id}/result.json", json.dumps(value))
        return value

    def write_journal(self, task_id, request_id, *, state="running-actions"):
        value = {
            "schema": "legacy-runner-transaction-journal@v1",
            "task_id": task_id,
            "request_id": request_id,
            "state": state,
        }
        self.write(f"output/logs/{task_id}/{request_id}/transaction-journal.json", json.dumps(value))

    def write_current_pointer(self, task_id, request_id):
        value = {
            "schema": "legacy-runner-current-pointer@v1",
            "task_id": task_id,
            "request_id": request_id,
        }
        self.write(f"output/logs/{task_id}/current.json", json.dumps(value))

    def gc(self, **kwargs):
        kwargs.setdefault("now", self.now)
        return ar.gc(self.root, **kwargs)

    def candidate_for(self, report, path_suffix):
        for entry in report["candidates"]:
            if entry["path"].endswith(path_suffix) or path_suffix in entry["path"]:
                return entry
        return None


# ---------------------------------------------------------------------------
# 1. Fixed-path export deletion
# ---------------------------------------------------------------------------


class FixedPathExportTests(FixtureTestCase):
    def test_fixed_path_export_is_out_of_scope_and_never_deleted(self):
        self.write("exports/current/index.html", "<html></html>")
        report = self.gc(apply=True, now=self.now + 400 * DAY)
        # never enumerated as a candidate at all
        self.assertFalse(any("exports/current" in c["path"] for c in report["candidates"]))
        self.assertTrue((self.root / "exports/current/index.html").exists())

    def test_quarantine_brings_fixed_path_export_under_retention(self):
        self.write("exports/current/index.html", "<html></html>")
        descriptor = ar.quarantine_artifact(
            self.root,
            task_id="0038-99",
            request_id="req-1",
            source_path="exports/current",
            kind="export",
            state="superseded",
            now=self.now,
        )
        self.assertFalse((self.root / "exports/current").exists())
        artifact_path = self.root / descriptor["artifact_path"]
        self.assertTrue(artifact_path.exists())
        # far in the future: scratch TTL has long elapsed
        report = self.gc(apply=True, now=self.now + 400 * DAY)
        entry = self.candidate_for(report, "index.html") or self.candidate_for(report, ".quarantine.json")
        self.assertIsNotNone(entry)
        self.assertTrue(entry["deleted"])
        self.assertFalse(artifact_path.exists())


# ---------------------------------------------------------------------------
# 2. Empty service-error files
# ---------------------------------------------------------------------------


class EmptyServiceErrorFileTests(FixtureTestCase):
    def test_empty_service_error_file_is_pruned_as_tombstone(self):
        self.write("output/logs/0038-11/req-empty-err/service-error.log", "")
        req_dir = self.root / "output/logs/0038-11/req-empty-err"
        os.utime(req_dir, (self.now - 10 * DAY, self.now - 10 * DAY))
        report = self.gc(apply=False, now=self.now)
        entry = self.candidate_for(report, "req-empty-err")
        self.assertEqual(entry["state"], "empty-tombstone")
        self.assertTrue(entry["eligible"])

        applied = self.gc(apply=True, now=self.now)
        self.assertFalse(req_dir.exists())


# ---------------------------------------------------------------------------
# 3. Failed-sentinel outputs
# ---------------------------------------------------------------------------


class FailedSentinelTests(FixtureTestCase):
    def test_failed_sentinel_is_retained_under_failed_trace_tier(self):
        sentinel = self.write("output/logs/0038-11/req-sentinel/FAILED", "boom")
        os.utime(sentinel, (self.now - 5 * DAY, self.now - 5 * DAY))
        req_dir = sentinel.parent
        os.utime(req_dir, (self.now - 5 * DAY, self.now - 5 * DAY))

        report = self.gc(apply=False, now=self.now)
        entry = self.candidate_for(report, "req-sentinel")
        self.assertEqual(entry["tier"], "failed-trace")
        self.assertEqual(entry["state"], "legacy-sentinel")
        self.assertFalse(entry["eligible"])  # 5 days < 30-day failed-trace TTL

        report_later = self.gc(apply=True, now=self.now + 40 * DAY)
        self.assertFalse(req_dir.exists())


# ---------------------------------------------------------------------------
# 4. Empty request directories
# ---------------------------------------------------------------------------


class EmptyRequestDirectoryTests(FixtureTestCase):
    def test_completely_empty_request_directory_is_prunable(self):
        req_dir = self.root / "output/logs/0038-11/req-blank"
        req_dir.mkdir(parents=True)
        os.utime(req_dir, (self.now - DAY, self.now - DAY))
        report = self.gc(apply=True, now=self.now)
        entry = self.candidate_for(report, "req-blank")
        self.assertEqual(entry["state"], "empty-tombstone")
        self.assertTrue(entry["deleted"])
        self.assertFalse(req_dir.exists())


# ---------------------------------------------------------------------------
# 5. Interrupted attempts
# ---------------------------------------------------------------------------


class InterruptedAttemptTests(FixtureTestCase):
    def test_journal_without_result_is_never_deleted(self):
        self.write_journal("0038-11", "req-interrupted", state="promoting-outputs")
        req_dir = self.root / "output/logs/0038-11/req-interrupted"
        report = self.gc(apply=True, now=self.now + 400 * DAY)
        entry = self.candidate_for(report, "req-interrupted")
        self.assertEqual(entry["reason"], "retained:unfinalized-journal")
        self.assertFalse(entry["deleted"])
        self.assertTrue(req_dir.exists())


# ---------------------------------------------------------------------------
# 6. Reused log names
# ---------------------------------------------------------------------------


class ReusedLogNameTests(FixtureTestCase):
    def test_stray_top_level_run_current_log_is_never_trusted(self):
        stray = self.write("output/logs/0038-11/run-current.log", "attempt 7 of many, reused name\n")
        report = self.gc(apply=True, now=self.now + 400 * DAY)
        entry = self.candidate_for(report, "run-current.log")
        self.assertEqual(entry["reason"], "retained:unknown-state")
        self.assertFalse(entry["deleted"])
        self.assertTrue(stray.exists())

    def test_stray_nonempty_file_inside_request_dir_is_unknown_state(self):
        self.write("output/logs/0038-11/req-stray/notes.txt", "some free-text notes\n")
        req_dir = self.root / "output/logs/0038-11/req-stray"
        report = self.gc(apply=True, now=self.now + 400 * DAY)
        entry = self.candidate_for(report, "req-stray")
        self.assertEqual(entry["reason"], "retained:unknown-state")
        self.assertTrue(req_dir.exists())


# ---------------------------------------------------------------------------
# 7. Live claims
# ---------------------------------------------------------------------------


class LiveClaimTests(FixtureTestCase):
    def test_claim_filename_blocks_deletion(self):
        self.write_result("0038-11", "req-live", verdict="passed", finished_at=self.now - 400 * DAY)
        self.write("TODO-someagent-0038-11-20260101T000000Z.md", "claim\n")
        report = self.gc(apply=True, now=self.now)
        entry = self.candidate_for(report, "req-live")
        self.assertEqual(entry["reason"], "retained:live-claim")
        self.assertTrue((self.root / "output/logs/0038-11/req-live").exists())

    def test_todo_pending_marker_blocks_deletion(self):
        self.write_result("0038-11", "req-live2", verdict="passed", finished_at=self.now - 400 * DAY)
        self.write("TODO.md", "- [p] **0038-11** PREREQ: none Some task text\n")
        report = self.gc(apply=True, now=self.now)
        entry = self.candidate_for(report, "req-live2")
        self.assertEqual(entry["reason"], "retained:live-claim")

    def test_unrelated_task_without_claim_is_not_blocked(self):
        self.write_result("0038-11", "req-unrelated", verdict="passed", finished_at=self.now - 400 * DAY)
        self.write("TODO-someagent-0038-12-20260101T000000Z.md", "unrelated claim\n")
        report = self.gc(apply=True, now=self.now)
        entry = self.candidate_for(report, "req-unrelated")
        self.assertEqual(entry["reason"], "eligible")
        self.assertTrue(entry["deleted"])


# ---------------------------------------------------------------------------
# 8. Clock skew
# ---------------------------------------------------------------------------


class ClockSkewTests(FixtureTestCase):
    def test_future_finished_at_is_never_treated_as_old(self):
        # finished_at is *after* "now" -- a naive abs(now - finished_at) could
        # make this look arbitrarily old under a large skew; it must not be
        # deleted regardless of how far in the future it is.
        self.write_result("0038-11", "req-future", verdict="failed", finished_at=self.now + 1000 * DAY)
        report = self.gc(apply=True, now=self.now)
        entry = self.candidate_for(report, "req-future")
        self.assertEqual(entry["reason"], "retained:future-timestamp")
        self.assertFalse(entry["deleted"])


# ---------------------------------------------------------------------------
# 9. Rollback
# ---------------------------------------------------------------------------


class RollbackTests(FixtureTestCase):
    def test_rolled_back_attempt_is_failed_trace_and_removed_atomically(self):
        self.write_result(
            "0038-11",
            "req-rollback",
            verdict="failed",
            finished_at=self.now - 40 * DAY,
            extra={"promotion_backups_retained": True},
        )
        self.write(
            "output/logs/0038-11/req-rollback/promotion-journal.json",
            json.dumps({"schema": "legacy-runner-promotion-journal@v1", "status": "rolled-back", "records": []}),
        )
        self.write("output/logs/0038-11/req-rollback/backup/original.txt", "pre-rollback content")

        req_dir = self.root / "output/logs/0038-11/req-rollback"
        report = self.gc(apply=False, now=self.now)
        entry = self.candidate_for(report, "req-rollback")
        self.assertEqual(entry["tier"], "failed-trace")
        self.assertTrue(entry["eligible"])  # 40 days > 30-day failed-trace TTL

        applied = self.gc(apply=True, now=self.now)
        self.assertFalse(req_dir.exists())  # result, journal, and backup removed together
        self.assertFalse((req_dir / "promotion-journal.json").exists())
        self.assertFalse((req_dir / "backup" / "original.txt").exists())


# ---------------------------------------------------------------------------
# Additional coverage: quarantine API, permanent-manifest, current pointer,
# TTL tiers, dry-run default, CLI.
# ---------------------------------------------------------------------------


class QuarantineApiTests(FixtureTestCase):
    def test_quarantine_writes_descriptor_with_digests_and_retry_flag(self):
        self.write("output/logs/0038-11/req-1/scratch/partial-export.html", "<html>partial</html>")
        descriptor = ar.quarantine_artifact(
            self.root,
            task_id="0038-11",
            request_id="req-1",
            source_path="output/logs/0038-11/req-1/scratch",
            kind="export",
            state="partial",
            error=("EXP-TIMEOUT", "export timed out mid-write"),
            retry_eligible=True,
            now=self.now,
        )
        self.assertEqual(descriptor["schema"], "artifact-quarantine@v1")
        self.assertEqual(descriptor["state"], "partial")
        self.assertTrue(descriptor["retry_eligible"])
        self.assertEqual(descriptor["error"]["rule"], "EXP-TIMEOUT")
        self.assertTrue(descriptor["source_digest"].startswith("sha256:"))
        self.assertEqual(descriptor["source_digest"], descriptor["output_digest"])
        artifact_path = self.root / descriptor["artifact_path"]
        self.assertTrue(artifact_path.is_dir())
        sidecar = artifact_path.parent / f"{artifact_path.name}.quarantine.json"
        self.assertTrue(sidecar.exists())

    def test_quarantine_rejects_glob_source(self):
        with self.assertRaises(ar.RetentionError) as ctx:
            ar.quarantine_artifact(
                self.root,
                task_id="0038-11",
                request_id="req-1",
                source_path="output/logs/0038-11/*",
                kind="export",
                state="partial",
                now=self.now,
            )
        self.assertEqual(ctx.exception.rule, "RET-BROAD-GLOB")

    def test_quarantine_rejects_missing_source(self):
        with self.assertRaises(ar.RetentionError) as ctx:
            ar.quarantine_artifact(
                self.root,
                task_id="0038-11",
                request_id="req-1",
                source_path="output/logs/0038-11/req-1/does-not-exist",
                kind="export",
                state="partial",
                now=self.now,
            )
        self.assertEqual(ctx.exception.rule, "RET-SOURCE-MISSING")

    def test_quarantine_rejects_bad_state(self):
        self.write("output/logs/0038-11/req-1/x.txt", "x")
        with self.assertRaises(ar.RetentionError) as ctx:
            ar.quarantine_artifact(
                self.root,
                task_id="0038-11",
                request_id="req-1",
                source_path="output/logs/0038-11/req-1/x.txt",
                kind="export",
                state="not-a-real-state",
                now=self.now,
            )
        self.assertEqual(ctx.exception.rule, "RET-BAD-STATE")

    def test_dry_run_quarantine_does_not_move_anything(self):
        source = self.write("output/logs/0038-11/req-1/x.txt", "x")
        ar.quarantine_artifact(
            self.root,
            task_id="0038-11",
            request_id="req-1",
            source_path="output/logs/0038-11/req-1/x.txt",
            kind="export",
            state="partial",
            now=self.now,
            dry_run=True,
        )
        self.assertTrue(source.exists())


class PermanentManifestTests(FixtureTestCase):
    def test_evidence_pack_referenced_path_is_never_silently_deleted(self):
        self.write_result("0038-11", "req-referenced", verdict="passed", finished_at=self.now - 400 * DAY)
        referenced_path = "output/logs/0038-11/req-referenced/result.json"
        manifest = {
            "schema": "task-evidence-pack@v1",
            "task_id": "0038-12",
            "items": [{"path": referenced_path, "kind": "blob", "digest": "sha256:deadbeef"}],
        }
        self.write("output/logs/0038-12/req-pack/evidence-pack.json", json.dumps(manifest))

        report = self.gc(apply=True, now=self.now)
        entry = self.candidate_for(report, "req-referenced")
        self.assertEqual(entry["reason"], "retained:permanent-manifest")
        self.assertTrue((self.root / referenced_path).exists())

    def test_unreferenced_terminal_attempt_is_still_eligible(self):
        self.write_result("0038-11", "req-unreferenced", verdict="passed", finished_at=self.now - 400 * DAY)
        report = self.gc(apply=True, now=self.now)
        entry = self.candidate_for(report, "req-unreferenced")
        self.assertEqual(entry["reason"], "eligible")
        self.assertTrue(entry["deleted"])


class CurrentPointerTests(FixtureTestCase):
    def test_current_pointer_target_is_never_deleted_even_past_ttl(self):
        self.write_result("0038-11", "req-old", verdict="passed", finished_at=self.now - 400 * DAY)
        self.write_result("0038-11", "req-current", verdict="passed", finished_at=self.now - 400 * DAY)
        self.write_current_pointer("0038-11", "req-current")

        report = self.gc(apply=True, now=self.now)
        old_entry = self.candidate_for(report, "req-old")
        current_entry = self.candidate_for(report, "req-current")
        self.assertEqual(old_entry["reason"], "eligible")
        self.assertTrue(old_entry["deleted"])
        self.assertEqual(current_entry["reason"], "retained:current-pointer")
        self.assertFalse(current_entry["deleted"])
        self.assertTrue((self.root / "output/logs/0038-11/req-current").exists())


class TierTtlTests(FixtureTestCase):
    def test_successful_log_and_failed_trace_have_different_ttls(self):
        self.write_result("0038-11", "req-pass-10d", verdict="passed", finished_at=self.now - 10 * DAY)
        self.write_result("0038-11", "req-fail-10d", verdict="failed", finished_at=self.now - 10 * DAY)
        report = self.gc(apply=False, now=self.now)
        passed_entry = self.candidate_for(report, "req-pass-10d")
        failed_entry = self.candidate_for(report, "req-fail-10d")
        # 10 days > 7-day successful-log TTL, but < 30-day failed-trace TTL
        self.assertEqual(passed_entry["reason"], "eligible")
        self.assertEqual(failed_entry["reason"], "retained:ttl-not-elapsed")

    def test_custom_ttl_override(self):
        self.write_result("0038-11", "req-pass-1d", verdict="passed", finished_at=self.now - 1 * DAY)
        report = self.gc(apply=False, now=self.now, ttl_by_tier={"successful-log": 12 * 3600})
        entry = self.candidate_for(report, "req-pass-1d")
        self.assertEqual(entry["reason"], "eligible")


class TaskIdFilterTests(FixtureTestCase):
    def test_task_id_filter_scopes_the_scan(self):
        self.write_result("0038-11", "req-a", verdict="passed", finished_at=self.now - 400 * DAY)
        self.write_result("0038-99", "req-b", verdict="passed", finished_at=self.now - 400 * DAY)
        report = self.gc(apply=True, now=self.now, task_ids=["0038-11"])
        self.assertIsNotNone(self.candidate_for(report, "req-a"))
        self.assertIsNone(self.candidate_for(report, "req-b"))
        self.assertTrue((self.root / "output/logs/0038-99/req-b").exists())


class CliTests(FixtureTestCase):
    def _run(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ar.main(argv)
        return rc, buf.getvalue()

    def test_plan_command_defaults_to_no_deletion(self):
        self.write_result("0038-11", "req-cli", verdict="passed", finished_at=self.now - 400 * DAY)
        rc, out = self._run(["plan", "--root", str(self.root), "--now", _iso(self.now), "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertTrue(payload["dry_run"])
        self.assertTrue((self.root / "output/logs/0038-11/req-cli").exists())

    def test_gc_requires_explicit_apply_flag_to_delete(self):
        self.write_result("0038-11", "req-cli2", verdict="passed", finished_at=self.now - 400 * DAY)
        rc, out = self._run(["gc", "--root", str(self.root), "--now", _iso(self.now), "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertTrue(payload["dry_run"])
        self.assertTrue((self.root / "output/logs/0038-11/req-cli2").exists())

        rc, out = self._run(["gc", "--root", str(self.root), "--now", _iso(self.now), "--apply", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertFalse(payload["dry_run"])
        self.assertFalse((self.root / "output/logs/0038-11/req-cli2").exists())

    def test_quarantine_cli_round_trip(self):
        self.write("output/logs/0038-11/req-cli3/thing.txt", "content")
        rc, out = self._run(
            [
                "quarantine",
                "--root",
                str(self.root),
                "--task-id",
                "0038-11",
                "--request-id",
                "req-cli3",
                "--source",
                "output/logs/0038-11/req-cli3/thing.txt",
                "--kind",
                "scratch",
                "--state",
                "interrupted",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertEqual(payload["state"], "interrupted")
        self.assertTrue((self.root / payload["artifact_path"]).exists())


if __name__ == "__main__":
    unittest.main()
