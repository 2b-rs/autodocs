"""Tests for _src/tools/candidate_budget.py (Task `0038-13`).

Covers the six named Definition-of-Done fixtures — a 4,503-file generation,
stale fixed export path, incomplete language trees, synthetic-only UI data,
actual downloaded payload mismatch, and clean-checkout reproduction — plus
general budget-contract validation, sole-writer/diff/negative-path checks,
and atomic/recoverable promotion coverage (including the "no unrelated
generated family is swept in" guard).
"""
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "candidate_budget.py"

SPEC = importlib.util.spec_from_file_location("candidate_budget", TOOL)
assert SPEC and SPEC.loader
cb = importlib.util.module_from_spec(SPEC)
sys.modules["candidate_budget"] = cb
SPEC.loader.exec_module(cb)


def _budget(**overrides):
    value = {
        "schema": cb.BUDGET_SCHEMA,
        "budget_id": "b1",
        "task_id": "0038-13",
        "sole_writer": "0038-13:generator",
        "allowed_paths": ["**"],
        "file_count": {"min": 0, "max": 1_000_000},
        "total_bytes": {"min": 0, "max": 1_000_000_000},
    }
    value.update(overrides)
    return value


class FixtureTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relative: str, content: bytes = b"") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def candidate_dir(self, task_id="0038-13", request_id="req-1"):
        return cb.candidate_root(self.root, task_id=task_id, request_id=request_id)


# ---------------------------------------------------------------------------
# candidate_root() — run-specific, non-fixed-path generation target
# ---------------------------------------------------------------------------


class CandidateRootTests(FixtureTestCase):
    def test_run_specific_path_shape(self):
        cdir = self.candidate_dir()
        self.assertEqual(cdir, self.root / "output" / "logs" / "0038-13" / "req-1" / ".candidates")

    def test_rejects_unsafe_segments(self):
        for bad in ("../escape", "a/b", "."):
            with self.assertRaises(cb.BudgetError) as ctx:
                cb.candidate_root(self.root, task_id=bad, request_id="req-1")
            self.assertEqual(ctx.exception.rule, "CB-BAD-ID")


# ---------------------------------------------------------------------------
# build_manifest() — determinism / "clean-checkout reproduction" fixture
# ---------------------------------------------------------------------------


class CleanCheckoutReproductionTests(FixtureTestCase):
    """DoD fixture: clean-checkout reproduction."""

    def test_manifest_digest_is_content_only(self):
        cdir_a = self.candidate_dir(request_id="req-a")
        (cdir_a / "en" / "index.html").parent.mkdir(parents=True)
        (cdir_a / "en" / "index.html").write_bytes(b"<html>content</html>")
        manifest_a = cb.build_manifest(cdir_a, now=1_000)

        # A second, independent "clean checkout" generation with identical
        # content but a different request id, directory, and timestamp.
        cdir_b = self.candidate_dir(request_id="req-b")
        (cdir_b / "en" / "index.html").parent.mkdir(parents=True)
        (cdir_b / "en" / "index.html").write_bytes(b"<html>content</html>")
        manifest_b = cb.build_manifest(cdir_b, now=2_000)

        self.assertEqual(manifest_a["manifest_digest"], manifest_b["manifest_digest"])
        self.assertNotEqual(manifest_a["generated_at"], manifest_b["generated_at"])

    def test_expected_manifest_zero_diff_reproduces(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "en" / "index.html"), b"hello world")
        manifest = cb.build_manifest(cdir)

        budget = cb.load_budget(self._write_budget(_budget(expected_manifest=[
            {"path": "en/index.html", "digest": manifest["files"][0]["digest"]},
        ])))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "PASS")

    def _write_budget(self, value):
        path = self.root / "budget.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path


# ---------------------------------------------------------------------------
# 4,503-file generation fixture
# ---------------------------------------------------------------------------


class LargeGenerationTests(unittest.TestCase):
    """DoD fixture: a 4,503-file generation.

    The on-disk generation + hashing pass is genuinely I/O-heavy at this
    scale, so it is done exactly **once** in ``setUpClass`` and shared by
    both assertions (matching budget, and one-file-short budget) rather than
    regenerating the whole tree per test method.
    """

    FILE_COUNT = 4503

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cdir = cb.candidate_root(cls.root, task_id="0038-13", request_id="req-1")
        cdir.mkdir(parents=True)
        for index in range(cls.FILE_COUNT):
            (cdir / f"file-{index:05d}.txt").write_bytes(f"content-{index}".encode("utf-8"))
        cls.manifest = cb.build_manifest(cdir)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_matching_budget_passes(self):
        self.assertEqual(self.manifest["file_count"], self.FILE_COUNT)
        budget = cb._validate_budget(_budget(file_count={"min": self.FILE_COUNT, "max": self.FILE_COUNT}))
        report = cb.evaluate(budget, self.manifest)
        self.assertEqual(report["verdict"], "PASS")

    def test_short_generation_blocks(self):
        # One file short of the expected budget — synthesized from the same
        # real generated manifest (no second disk pass) by dropping one entry.
        short_files = self.manifest["files"][:-1]
        short_manifest = {
            **self.manifest,
            "files": short_files,
            "file_count": len(short_files),
            "total_bytes": sum(item["bytes"] for item in short_files),
        }
        self.assertEqual(short_manifest["file_count"], self.FILE_COUNT - 1)

        budget = cb._validate_budget(_budget(file_count={"min": self.FILE_COUNT, "max": self.FILE_COUNT}))
        report = cb.evaluate(budget, short_manifest)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(f["code"] == "CB-FILE-COUNT" for f in report["findings"]))


# ---------------------------------------------------------------------------
# Incomplete language trees fixture
# ---------------------------------------------------------------------------


class IncompleteLanguageTreeTests(FixtureTestCase):
    """DoD fixture: incomplete language trees."""

    def test_missing_locale_subtree_blocks(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "en" / "index.html"), b"english content here")
        self.write(str(cdir.relative_to(self.root) / "fr" / "index.html"), b"french content here!!")
        # "es" is declared required but never generated.
        manifest = cb.build_manifest(cdir)

        budget = cb._validate_budget(_budget(required_subtrees=["en", "fr", "es"]))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "FAIL")
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("CB-INCOMPLETE-SUBTREE", codes)
        self.assertTrue(any(f["path"] == "es" for f in report["findings"]))

    def test_complete_locale_subtrees_pass(self):
        cdir = self.candidate_dir()
        for locale in ("en", "fr", "es"):
            self.write(str(cdir.relative_to(self.root) / locale / "index.html"), b"content")
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(required_subtrees=["en", "fr", "es"]))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "PASS")


# ---------------------------------------------------------------------------
# Synthetic-only UI data fixture
# ---------------------------------------------------------------------------


class SyntheticOnlyUiDataTests(FixtureTestCase):
    """DoD fixture: synthetic-only UI data (Feature `0021` "synthetic-only
    green" pattern — many files that are identical templated stand-ins rather
    than production-realistic rendered content)."""

    def test_uniform_stub_content_blocks(self):
        cdir = self.candidate_dir()
        for index in range(10):
            self.write(str(cdir.relative_to(self.root) / f"widget-{index}.json"), b'{"placeholder": true}')
        manifest = cb.build_manifest(cdir)

        budget = cb._validate_budget(_budget(max_duplicate_digest_ratio=0.5))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(f["code"] == "CB-SYNTHETIC-CONTENT" for f in report["findings"]))

    def test_varied_realistic_content_passes(self):
        cdir = self.candidate_dir()
        for index in range(10):
            self.write(str(cdir.relative_to(self.root) / f"widget-{index}.json"), json.dumps({"id": index, "payload": "x" * index}).encode())
        manifest = cb.build_manifest(cdir)

        budget = cb._validate_budget(_budget(max_duplicate_digest_ratio=0.5))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "PASS")


# ---------------------------------------------------------------------------
# Actual downloaded payload mismatch fixture
# ---------------------------------------------------------------------------


class DownloadedPayloadMismatchTests(FixtureTestCase):
    """DoD fixture: actual downloaded payload mismatch — a declared download
    is present but its real byte size is far below what production traffic
    would produce, i.e. it is a synthesized in-memory stand-in."""

    def test_undersized_download_blocks(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "assets" / "spec.pdf"), b"stub")  # 4 bytes
        manifest = cb.build_manifest(cdir)

        budget = cb._validate_budget(_budget(realism=[
            {"pattern": "assets/*.pdf", "min_bytes": 10_000, "kind": "downloaded"},
        ]))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "FAIL")
        finding = next(f for f in report["findings"] if f["code"] == "CB-UNREALISTIC-PAYLOAD")
        self.assertIn("downloaded", finding["message"])

    def test_missing_download_target_is_inconclusive_finding(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "other.txt"), b"unrelated")
        manifest = cb.build_manifest(cdir)

        budget = cb._validate_budget(_budget(
            allowed_paths=["**"],
            realism=[{"pattern": "assets/*.pdf", "min_bytes": 10_000, "kind": "downloaded"}],
        ))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(f["code"] == "CB-MISSING-REALISM-TARGET" for f in report["findings"]))

    def test_production_realistic_download_passes(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "assets" / "spec.pdf"), b"%PDF-1.4" + b"x" * 20_000)
        manifest = cb.build_manifest(cdir)

        budget = cb._validate_budget(_budget(realism=[
            {"pattern": "assets/*.pdf", "min_bytes": 10_000, "kind": "downloaded"},
        ]))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "PASS")


# ---------------------------------------------------------------------------
# Stale fixed export path fixture (promotion-time sole-writer guard)
# ---------------------------------------------------------------------------


class StaleFixedExportPathTests(FixtureTestCase):
    """DoD fixture: stale fixed export path — a shared destination already
    owned by a different producer must never be silently overwritten."""

    def _prepare(self, sole_writer="0038-13:generator"):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "out.txt"), b"generated payload")
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(sole_writer=sole_writer))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "PASS")
        return cdir, manifest, budget, report

    def test_foreign_owner_blocks_overwrite(self):
        cdir, manifest, budget, report = self._prepare()
        destination = self.root / "fixed-export"
        destination.mkdir(parents=True)
        # A stale export from an unrelated, differently-named producer already lives here.
        cb._atomic_write_json(destination / "current.json", {
            "schema": cb.POINTER_SCHEMA, "budget_id": "other", "task_id": "other-task",
            "sole_writer": "some-other-legacy-exporter", "request_id": "old-req",
            "manifest_digest": "sha256:deadbeef", "promoted_at": "2020-01-01T00:00:00Z",
        })
        with self.assertRaises(cb.BudgetError) as ctx:
            cb.promote(self.root, budget, cdir, destination, manifest=manifest, report=report, request_id="req-1", apply=True)
        self.assertEqual(ctx.exception.rule, "CB-OWNER-CONFLICT")
        # The stale pointer must remain untouched.
        pointer = cb.current_pointer(destination)
        self.assertEqual(pointer["sole_writer"], "some-other-legacy-exporter")

    def test_same_owner_may_promote_again(self):
        cdir, manifest, budget, report = self._prepare(sole_writer="owner-a")
        destination = self.root / "fixed-export"
        result1 = cb.promote(self.root, budget, cdir, destination, manifest=manifest, report=report, request_id="req-1", apply=True)
        self.assertTrue(result1["applied"])

        # A second generation by the SAME declared sole_writer, new request id.
        cdir2 = self.candidate_dir(request_id="req-2")
        self.write(str(cdir2.relative_to(self.root) / "out.txt"), b"generated payload v2")
        manifest2 = cb.build_manifest(cdir2)
        report2 = cb.evaluate(budget, manifest2)
        result2 = cb.promote(self.root, budget, cdir2, destination, manifest=manifest2, report=report2, request_id="req-2", apply=True)
        self.assertTrue(result2["applied"])
        self.assertEqual(cb.current_pointer(destination)["request_id"], "req-2")


# ---------------------------------------------------------------------------
# Promotion: atomic / recoverable, and "no unrelated generated family swept in"
# ---------------------------------------------------------------------------


class PromotionAtomicRecoverableTests(FixtureTestCase):
    def _prepare(self, allowed_paths=("**",)):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "keep.txt"), b"keep me")
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(allowed_paths=list(allowed_paths)))
        report = cb.evaluate(budget, manifest)
        return cdir, manifest, budget, report

    def test_dry_run_makes_no_change(self):
        cdir, manifest, budget, report = self._prepare()
        destination = self.root / "dest"
        result = cb.promote(self.root, budget, cdir, destination, manifest=manifest, report=report, request_id="req-1", apply=False)
        self.assertFalse(result["applied"])
        self.assertFalse(destination.exists())

    def test_blocked_report_refuses_promotion(self):
        cdir, manifest, budget, _report = self._prepare()
        failing_report = {"verdict": "FAIL", "findings": [{"code": "X"}]}
        with self.assertRaises(cb.BudgetError) as ctx:
            cb.promote(self.root, budget, cdir, self.root / "dest", manifest=manifest, report=failing_report, request_id="req-1", apply=True)
        self.assertEqual(ctx.exception.rule, "CB-BLOCKED-VERDICT")

    def test_recovers_after_crash_before_pointer_write(self):
        cdir, manifest, budget, report = self._prepare()
        destination = self.root / "dest"
        # Simulate a crash that completed the tree rename but never wrote current.json:
        # manually stage the exact promoted tree the real promote() would have produced.
        request_dir = destination / "req-1"
        request_dir.mkdir(parents=True)
        (request_dir / "keep.txt").write_bytes(b"keep me")
        self.assertIsNone(cb.current_pointer(destination))

        result = cb.promote(self.root, budget, cdir, destination, manifest=manifest, report=report, request_id="req-1", apply=True)
        self.assertTrue(result["applied"])
        pointer = cb.current_pointer(destination)
        self.assertEqual(pointer["request_id"], "req-1")
        # No leftover staging directory from the recovery path.
        self.assertFalse((destination.parent / "dest.stage-req-1").exists())

    def test_mismatched_leftover_is_a_collision_not_silently_replaced(self):
        cdir, manifest, budget, report = self._prepare()
        destination = self.root / "dest"
        request_dir = destination / "req-1"
        request_dir.mkdir(parents=True)
        (request_dir / "keep.txt").write_bytes(b"WRONG CONTENT")

        with self.assertRaises(cb.BudgetError) as ctx:
            cb.promote(self.root, budget, cdir, destination, manifest=manifest, report=report, request_id="req-1", apply=True)
        self.assertEqual(ctx.exception.rule, "CB-REQUEST-COLLISION")
        # Original (wrong) content must survive untouched — no destructive overwrite.
        self.assertEqual((request_dir / "keep.txt").read_bytes(), b"WRONG CONTENT")

    def test_unrelated_family_never_promoted_even_if_report_is_stale(self):
        cdir, manifest, budget, report = self._prepare(allowed_paths=["keep.txt"])
        # A stray file from a different generated family lands in the candidate
        # root (e.g. leftover from a previous unrelated run sharing the dir).
        self.write(str(cdir.relative_to(self.root) / "unrelated-family.bin"), b"not ours")
        stale_manifest = cb.build_manifest(cdir)  # now includes the stray file
        stale_report = {"verdict": "PASS", "findings": []}  # caller forgot to re-evaluate

        destination = self.root / "dest"
        result = cb.promote(self.root, budget, cdir, destination, manifest=stale_manifest, report=stale_report, request_id="req-1", apply=True)
        self.assertTrue(result["applied"])
        self.assertIn("unrelated-family.bin", result["skipped_unallowed"])
        promoted = destination / "req-1"
        self.assertTrue((promoted / "keep.txt").exists())
        self.assertFalse((promoted / "unrelated-family.bin").exists())


# ---------------------------------------------------------------------------
# General budget-contract validation
# ---------------------------------------------------------------------------


class BudgetContractTests(unittest.TestCase):
    def test_valid_budget_round_trips(self):
        value = _budget()
        normalized = cb._validate_budget(value)
        self.assertEqual(normalized["schema"], cb.BUDGET_SCHEMA)
        self.assertEqual(normalized["diff_tolerance"], {"max_added": 0, "max_removed": 0, "max_changed": 0})

    def test_wrong_schema_rejected(self):
        with self.assertRaises(cb.BudgetError) as ctx:
            cb._validate_budget(_budget(schema="wrong@v1"))
        self.assertEqual(ctx.exception.rule, "CB-SCHEMA")

    def test_missing_required_key_rejected(self):
        value = _budget()
        del value["sole_writer"]
        with self.assertRaises(cb.BudgetError) as ctx:
            cb._validate_budget(value)
        self.assertEqual(ctx.exception.rule, "CB-SHAPE")

    def test_unknown_key_rejected(self):
        with self.assertRaises(cb.BudgetError):
            cb._validate_budget(_budget(unknown_field=True))

    def test_empty_allowed_paths_rejected(self):
        with self.assertRaises(cb.BudgetError) as ctx:
            cb._validate_budget(_budget(allowed_paths=[]))
        self.assertEqual(ctx.exception.rule, "CB-ALLOWED-PATHS")

    def test_inverted_bounds_rejected(self):
        with self.assertRaises(cb.BudgetError) as ctx:
            cb._validate_budget(_budget(file_count={"min": 10, "max": 1}))
        self.assertEqual(ctx.exception.rule, "CB-BOUNDS")

    def test_require_negative_path_without_patterns_rejected(self):
        with self.assertRaises(cb.BudgetError) as ctx:
            cb._validate_budget(_budget(require_negative_path=True, negative_path_patterns=[]))
        self.assertEqual(ctx.exception.rule, "CB-NEGATIVE-PATH")

    def test_bad_duplicate_ratio_rejected(self):
        with self.assertRaises(cb.BudgetError) as ctx:
            cb._validate_budget(_budget(max_duplicate_digest_ratio=1.5))
        self.assertEqual(ctx.exception.rule, "CB-DUP-RATIO")


# ---------------------------------------------------------------------------
# Negative-path requirement (guards against happy-path-only evidence)
# ---------------------------------------------------------------------------


class NegativePathTests(FixtureTestCase):
    def test_missing_negative_path_blocks(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "success" / "report.json"), b"{}")
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(require_negative_path=True, negative_path_patterns=["error/**", "*-failed.json"]))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(f["code"] == "CB-MISSING-NEGATIVE-PATH" for f in report["findings"]))

    def test_present_negative_path_passes(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "success" / "report.json"), b"{}")
        self.write(str(cdir.relative_to(self.root) / "error" / "timeout.json"), b"{}")
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(require_negative_path=True, negative_path_patterns=["error/**"]))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "PASS")


# ---------------------------------------------------------------------------
# Sole-writer identity mismatch and unallowed-path evaluation findings
# ---------------------------------------------------------------------------


class MiscEvaluationTests(FixtureTestCase):
    def test_writer_identity_mismatch_flagged(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "a.txt"), b"content")
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(sole_writer="expected-writer"))
        report = cb.evaluate(budget, manifest, writer_identity="different-writer")
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(f["code"] == "CB-SOLE-WRITER" for f in report["findings"]))

    def test_unallowed_path_flagged(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "modules" / "a.html"), b"content")
        self.write(str(cdir.relative_to(self.root) / "scratch" / "b.tmp"), b"content")
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(allowed_paths=["modules/**"]))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "FAIL")
        finding = next(f for f in report["findings"] if f["code"] == "CB-UNALLOWED-PATH")
        self.assertEqual(finding["path"], "scratch/b.tmp")

    def test_total_bytes_bound_enforced(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "big.bin"), b"x" * 5000)
        manifest = cb.build_manifest(cdir)
        budget = cb._validate_budget(_budget(total_bytes={"min": 0, "max": 100}))
        report = cb.evaluate(budget, manifest)
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(f["code"] == "CB-TOTAL-BYTES" for f in report["findings"]))

    def test_unexplained_diff_blocks_but_explained_diff_passes(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "a.txt"), b"new content")
        manifest = cb.build_manifest(cdir)
        expected = [{"path": "a.txt", "digest": "sha256:" + "0" * 64}, {"path": "b.txt", "digest": "sha256:" + "1" * 64}]

        budget_blocking = cb._validate_budget(_budget(expected_manifest=expected))
        report_blocking = cb.evaluate(budget_blocking, manifest)
        self.assertEqual(report_blocking["verdict"], "FAIL")
        codes = {f["code"] for f in report_blocking["findings"]}
        self.assertIn("CB-UNEXPLAINED-DIFF-CHANGED", codes)
        self.assertIn("CB-UNEXPLAINED-DIFF-REMOVED", codes)

        budget_explained = cb._validate_budget(_budget(expected_manifest=expected, explained_diffs=["a.txt", "b.txt"]))
        report_explained = cb.evaluate(budget_explained, manifest)
        self.assertEqual(report_explained["verdict"], "PASS")


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------


class CliTests(FixtureTestCase):
    def _run(self, argv):
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = cb.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def _write_budget(self, value):
        path = self.root / "budget.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_manifest_command(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "x.txt"), b"hi")
        rc, out, _err = self._run(["manifest", "--root", str(self.root), "--task-id", "0038-13", "--request-id", "req-1", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(out)
        self.assertEqual(payload["file_count"], 1)

    def test_evaluate_command_pass_and_fail(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "x.txt"), b"hi")
        budget_path = self._write_budget(_budget())
        rc, out, _err = self._run(["evaluate", "--root", str(self.root), "--budget", str(budget_path), "--task-id", "0038-13", "--request-id", "req-1", "--json"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["verdict"], "PASS")

        strict_budget_path = self._write_budget(_budget(file_count={"min": 5, "max": 5}))
        rc2, out2, _err2 = self._run(["evaluate", "--root", str(self.root), "--budget", str(strict_budget_path), "--task-id", "0038-13", "--request-id", "req-1", "--json"])
        self.assertEqual(rc2, 1)
        self.assertEqual(json.loads(out2)["verdict"], "FAIL")

    def test_evaluate_command_contract_error_is_inconclusive(self):
        bad_budget_path = self.root / "bad.json"
        bad_budget_path.write_text("{not json", encoding="utf-8")
        rc, out, _err = self._run(["evaluate", "--root", str(self.root), "--budget", str(bad_budget_path), "--task-id", "0038-13", "--request-id", "req-1", "--json"])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["verdict"], "INCONCLUSIVE")

    def test_promote_command_dry_run_then_apply(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "x.txt"), b"hi")
        budget_path = self._write_budget(_budget())
        rc, out, _err = self._run(["evaluate", "--root", str(self.root), "--budget", str(budget_path), "--task-id", "0038-13", "--request-id", "req-1", "--out-report", str(self.root / "report.json"), "--json"])
        self.assertEqual(rc, 0)

        destination = self.root / "dest"
        rc_dry, out_dry, _e = self._run(["promote", "--root", str(self.root), "--budget", str(budget_path), "--task-id", "0038-13", "--request-id", "req-1", "--destination", str(destination), "--report", str(self.root / "report.json"), "--json"])
        self.assertEqual(rc_dry, 0)
        self.assertFalse(json.loads(out_dry)["applied"])
        self.assertFalse(destination.exists())

        rc_apply, out_apply, _e2 = self._run(["promote", "--root", str(self.root), "--budget", str(budget_path), "--task-id", "0038-13", "--request-id", "req-1", "--destination", str(destination), "--report", str(self.root / "report.json"), "--apply", "--json"])
        self.assertEqual(rc_apply, 0)
        self.assertTrue(json.loads(out_apply)["applied"])
        self.assertTrue((destination / "req-1" / "x.txt").exists())

    def test_promote_command_blocked_report_exits_nonzero(self):
        cdir = self.candidate_dir()
        self.write(str(cdir.relative_to(self.root) / "x.txt"), b"hi")
        budget_path = self._write_budget(_budget())
        failing_report_path = self.root / "fail_report.json"
        failing_report_path.write_text(json.dumps({"verdict": "FAIL", "findings": []}), encoding="utf-8")

        rc, _out, err = self._run(["promote", "--root", str(self.root), "--budget", str(budget_path), "--task-id", "0038-13", "--request-id", "req-1", "--destination", str(self.root / "dest"), "--report", str(failing_report_path), "--apply"])
        self.assertEqual(rc, 1)
        self.assertIn("CB-BLOCKED-VERDICT", err)


if __name__ == "__main__":
    unittest.main()
