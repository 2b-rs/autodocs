"""Tests for _src/tools/task_evidence_pack.py (Task 0038-12).

Covers the synthetic contract (dedup, secret/glob/unrelated-run/scratch
rejection, criterion mapping, verify) plus a demonstration against the real
184-file/10,384-line historical evidence commit `50b20829` referenced by the
Feature `0038` "Evidence baseline (2026-08-16)" paragraph in `TODO.md`, using
its `_src/logs/validate-review-request-ui/**` subtree (28 files) and one
genuinely unrelated path from `logs/backlog-bookkeeping-and-commit/0037-01-*`
in the same commit.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "task_evidence_pack.py"

SPEC = importlib.util.spec_from_file_location("task_evidence_pack", TOOL)
assert SPEC and SPEC.loader
evp = importlib.util.module_from_spec(SPEC)
sys.modules["task_evidence_pack"] = evp
SPEC.loader.exec_module(evp)

HISTORICAL_COMMIT = "50b20829"
REVIEW_UI_PREFIX = "_src/logs/validate-review-request-ui/"
UNRELATED_PATH = "logs/backlog-bookkeeping-and-commit/0037-01-e5f6081c37b4/01-scoped-status-before.txt"


def _git(root, *args):
    proc = subprocess.run(["git", *args], cwd=str(root), capture_output=True, check=True)
    return proc.stdout.decode("utf-8")


def _init_repo(root):
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")


def _commit_all(root, message="commit"):
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD").strip()


class IsolatedRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.blob_root = self.root / "blobs"
        _init_repo(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path


class BuildPackDedupTests(IsolatedRepoTestCase):
    def test_identical_content_dedupes_to_one_blob(self):
        self.write("logs/a/out.txt", "same payload\n")
        self.write("logs/b/out.txt", "same payload\n")
        manifest = evp.build_pack(
            self.root,
            self.blob_root,
            task_id="0038-12",
            argv=["tool"],
            action="build",
            base_commit="deadbeef",
            tool_name="task_evidence_pack",
            tool_version="1",
            environment_id=None,
            exit_status=0,
            item_specs=[{"path": "logs/a/out.txt"}, {"path": "logs/b/out.txt"}],
            criteria=[],
            counts={},
        )
        evidence = manifest["counts"]["evidence"]
        self.assertEqual(evidence["declared_items"], 2)
        self.assertEqual(evidence["blob_items"], 2)
        self.assertEqual(evidence["unique_blobs"], 1)
        self.assertEqual(evidence["deduplicated_items"], 1)
        digests = {item["digest"] for item in manifest["items"]}
        self.assertEqual(len(digests), 1)
        blob_file = evp._blob_path(self.blob_root, next(iter(digests)))
        self.assertTrue(blob_file.is_file())

    def test_dry_run_writes_nothing(self):
        self.write("logs/a/out.txt", "payload\n")
        manifest = evp.build_pack(
            self.root,
            self.blob_root,
            task_id="0038-12",
            argv=[],
            action="build",
            base_commit="deadbeef",
            tool_name="t",
            tool_version="1",
            environment_id=None,
            exit_status=0,
            item_specs=[{"path": "logs/a/out.txt"}],
            criteria=[],
            counts={},
            dry_run=True,
        )
        self.assertFalse(self.blob_root.exists())
        self.assertEqual(manifest["counts"]["evidence"]["blob_items"], 1)


class RejectionTests(IsolatedRepoTestCase):
    def test_rejects_secret_material(self):
        self.write("logs/a/creds.txt", "AKIAABCDEFGHIJKLMNOP\n")
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
                base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                exit_status=0, item_specs=[{"path": "logs/a/creds.txt"}], criteria=[], counts={},
            )
        self.assertEqual(ctx.exception.rule, "EVP-SECRET-AWS-KEY")
        self.assertFalse(self.blob_root.exists())

    def test_rejects_broad_glob(self):
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
                base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                exit_status=0, item_specs=[{"path": "logs/*.txt"}], criteria=[], counts={},
            )
        self.assertEqual(ctx.exception.rule, "EVP-BROAD-GLOB")

    def test_rejects_unrelated_run_evidence(self):
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
                base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                exit_status=0,
                item_specs=[{"path": "logs/0099-99-other-task/output.txt"}],
                criteria=[], counts={},
            )
        self.assertEqual(ctx.exception.rule, "EVP-UNRELATED-RUN")

    def test_related_task_id_allowlist_permits_path(self):
        self.write("logs/0099-99-other-task/output.txt", "ok\n")
        manifest = evp.build_pack(
            self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
            base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
            exit_status=0,
            item_specs=[{"path": "logs/0099-99-other-task/output.txt"}],
            criteria=[], counts={}, related_task_ids=["0099-99"],
        )
        self.assertEqual(manifest["counts"]["evidence"]["declared_items"], 1)

    def test_rejects_scratch_as_sole_closure_proof(self):
        (self.root / ".gitignore").write_text("output/\n", encoding="utf-8")
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
                base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                exit_status=0, item_specs=[], criteria=[], counts={},
                full_log_specs=[{"path": "output/logs/scratch/run.log", "digest": "sha256:" + "0" * 64}],
            )
        self.assertEqual(ctx.exception.rule, "EVP-SCRATCH-SOLE-PROOF")

    def test_non_ignored_full_log_with_no_items_is_allowed(self):
        # No .gitignore entry covers this path, so it is not "scratch".
        manifest = evp.build_pack(
            self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
            base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
            exit_status=0, item_specs=[], criteria=[], counts={},
            full_log_specs=[{"path": "output/logs/tracked/run.log", "digest": "sha256:" + "0" * 64}],
        )
        self.assertEqual(manifest["counts"]["evidence"]["full_logs"], 1)

    def test_rejects_bad_task_id(self):
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                self.root, self.blob_root, task_id="not-an-id", argv=[], action="build",
                base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                exit_status=0, item_specs=[], criteria=[], counts={},
            )
        self.assertEqual(ctx.exception.rule, "EVP-BAD-TASK-ID")

    def test_rejects_unknown_privacy_class(self):
        self.write("logs/a/out.txt", "payload\n")
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
                base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                exit_status=0,
                item_specs=[{"path": "logs/a/out.txt", "privacy_class": "secret"}],
                criteria=[], counts={},
            )
        self.assertEqual(ctx.exception.rule, "EVP-PRIVACY-CLASS")

    def test_rejects_oversized_blob(self):
        self.write("logs/a/big.txt", "x" * 100)
        original = evp.MAX_BLOB_BYTES
        evp.MAX_BLOB_BYTES = 10
        try:
            with self.assertRaises(evp.EvidencePackError) as ctx:
                evp.build_pack(
                    self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
                    base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                    exit_status=0, item_specs=[{"path": "logs/a/big.txt"}], criteria=[], counts={},
                )
            self.assertEqual(ctx.exception.rule, "EVP-BLOB-TOO-LARGE")
        finally:
            evp.MAX_BLOB_BYTES = original


class CriterionMappingTests(IsolatedRepoTestCase):
    def test_valid_criterion_mapping_is_retained(self):
        self.write("logs/a/out.txt", "payload\n")
        manifest = evp.build_pack(
            self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
            base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
            exit_status=0,
            item_specs=[{"path": "logs/a/out.txt", "criteria": ["c1"]}],
            criteria=[{"id": "c1", "satisfied_by": ["logs/a/out.txt"]}],
            counts={},
        )
        self.assertEqual(manifest["criteria"], [{"id": "c1", "satisfied_by": ["logs/a/out.txt"]}])

    def test_unknown_item_in_criterion_is_rejected(self):
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
                base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
                exit_status=0, item_specs=[],
                criteria=[{"id": "c1", "satisfied_by": ["never/declared.txt"]}], counts={},
            )
        self.assertEqual(ctx.exception.rule, "EVP-CRITERION-UNKNOWN-ITEM")


class TrackedRefTests(IsolatedRepoTestCase):
    def test_committed_script_is_a_tracked_ref_not_a_blob(self):
        self.write("tool.py", "print('hello')\n")
        head = _commit_all(self.root, "add tool")
        manifest = evp.build_pack(
            self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
            base_commit=head, tool_name="t", tool_version="1", environment_id=None,
            exit_status=0, item_specs=[{"path": "tool.py"}], criteria=[], counts={},
        )
        item = manifest["items"][0]
        self.assertEqual(item["kind"], "tracked-ref")
        self.assertEqual(item["source_commit"], head)
        self.assertFalse(self.blob_root.exists())

    def test_uncommitted_script_falls_back_to_blob(self):
        self.write("uncommitted.py", "print('hi')\n")
        manifest = evp.build_pack(
            self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
            base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
            exit_status=0, item_specs=[{"path": "uncommitted.py"}], criteria=[], counts={},
        )
        self.assertEqual(manifest["items"][0]["kind"], "blob")


class VerifyPackTests(IsolatedRepoTestCase):
    def _build_one_blob_pack(self):
        self.write("logs/a/out.txt", "payload\n")
        return evp.build_pack(
            self.root, self.blob_root, task_id="0038-12", argv=[], action="build",
            base_commit="deadbeef", tool_name="t", tool_version="1", environment_id=None,
            exit_status=0, item_specs=[{"path": "logs/a/out.txt"}], criteria=[], counts={},
        )

    def test_clean_pack_verifies(self):
        manifest = self._build_one_blob_pack()
        findings = evp.verify_pack(self.root, self.blob_root, manifest)
        self.assertEqual(findings, [])

    def test_tampered_blob_is_detected(self):
        manifest = self._build_one_blob_pack()
        digest = manifest["items"][0]["digest"]
        blob_file = evp._blob_path(self.blob_root, digest)
        blob_file.write_bytes(b"tampered")
        findings = evp.verify_pack(self.root, self.blob_root, manifest)
        self.assertTrue(any("EVP-VERIFY-BLOB-DIGEST" in f for f in findings))

    def test_missing_blob_is_detected(self):
        manifest = self._build_one_blob_pack()
        digest = manifest["items"][0]["digest"]
        evp._blob_path(self.blob_root, digest).unlink()
        findings = evp.verify_pack(self.root, self.blob_root, manifest)
        self.assertTrue(any("EVP-VERIFY-BLOB-MISSING" in f for f in findings))

    def test_tampered_manifest_digest_is_detected(self):
        manifest = self._build_one_blob_pack()
        manifest = dict(manifest)
        manifest["task_id"] = "0038-13"
        findings = evp.verify_pack(self.root, self.blob_root, manifest)
        self.assertTrue(any("EVP-VERIFY-MANIFEST-DIGEST" in f for f in findings))


class CliTests(IsolatedRepoTestCase):
    def test_build_then_verify_round_trip(self):
        self.write("logs/a/out.txt", "payload\n")
        out_manifest = self.root / "pack.json"
        rc = evp.main([
            "build",
            "--root", str(self.root),
            "--blob-root", str(self.blob_root),
            "--out-manifest", str(out_manifest),
            "--task-id", "0038-12",
            "--action", "build",
            "--base-commit", "deadbeef",
            "--tool-name", "t",
            "--exit-status", "0",
            "--items-json", json.dumps([{"path": "logs/a/out.txt"}]),
            "--json",
        ])
        self.assertEqual(rc, 0)
        self.assertTrue(out_manifest.is_file())

        rc = evp.main([
            "verify",
            "--root", str(self.root),
            "--blob-root", str(self.blob_root),
            "--manifest", str(out_manifest),
            "--json",
        ])
        self.assertEqual(rc, 0)

    def test_build_cli_fails_closed_on_secret(self):
        self.write("logs/a/creds.txt", "AKIAABCDEFGHIJKLMNOP\n")
        out_manifest = self.root / "pack.json"
        rc = evp.main([
            "build",
            "--root", str(self.root),
            "--blob-root", str(self.blob_root),
            "--out-manifest", str(out_manifest),
            "--task-id", "0038-12",
            "--action", "build",
            "--base-commit", "deadbeef",
            "--tool-name", "t",
            "--exit-status", "0",
            "--items-json", json.dumps([{"path": "logs/a/creds.txt"}]),
            "--json",
        ])
        self.assertEqual(rc, 1)
        self.assertFalse(out_manifest.exists())


@unittest.skipUnless((ROOT / ".git").exists(), "requires the real repository history")
class HistoricalEvidenceBaselineTests(unittest.TestCase):
    """Demonstrates the Definition of Done against the real 184-file/10,384-line
    historical evidence commit `50b20829` cited in the Feature 0038 "Evidence
    baseline" paragraph of TODO.md."""

    @classmethod
    def setUpClass(cls):
        try:
            subprocess.run(["git", "cat-file", "-e", HISTORICAL_COMMIT], cwd=str(ROOT), check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise unittest.SkipTest(f"historical commit {HISTORICAL_COMMIT} not reachable in this clone")
        listing = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", HISTORICAL_COMMIT],
            cwd=str(ROOT), check=True, capture_output=True,
        ).stdout.decode("utf-8").splitlines()
        cls.review_ui_paths = sorted(p for p in listing if p.startswith(REVIEW_UI_PREFIX))
        assert len(cls.review_ui_paths) == 28, f"expected the known 28-file review-ui subtree, found {len(cls.review_ui_paths)}"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.blob_root = Path(self.tmp.name) / "blobs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_review_request_ui_subtree_losslessly_packed_and_deduped(self):
        item_specs = [{"path": path, "commit": HISTORICAL_COMMIT} for path in self.review_ui_paths]
        manifest = evp.build_pack(
            ROOT, self.blob_root,
            task_id="0036-05",
            argv=["task_evidence_pack.py", "build"],
            action="historical-baseline-demo",
            base_commit=HISTORICAL_COMMIT,
            tool_name="task_evidence_pack",
            tool_version="1",
            environment_id=None,
            exit_status=0,
            item_specs=item_specs,
            criteria=[{"id": "evidence-baseline-2026-08-16", "satisfied_by": self.review_ui_paths}],
            counts={"historical_commit": HISTORICAL_COMMIT},
        )
        evidence = manifest["counts"]["evidence"]
        # Lossless: every one of the 28 historical files is represented exactly once.
        self.assertEqual(evidence["declared_items"], 28)
        self.assertEqual(len(manifest["items"]), 28)
        # Duplicate probe scripts (four_url_probe.cjs, make_review_fixture.py each
        # appear twice in the historical commit) are tracked-refs, not copied bytes.
        self.assertEqual(evidence["tracked_ref_items"], 6)
        self.assertEqual(evidence["blob_items"], 22)
        # Duplicate non-script evidence (identical .rc/.txt content across
        # timestamped directories) is deduplicated in the blob store.
        self.assertLess(evidence["unique_blobs"], evidence["blob_items"])
        self.assertGreater(evidence["deduplicated_items"], 0)
        # Navigable/auditable: the pack verifies clean against the blob store and
        # the historical commit's tracked blobs.
        findings = evp.verify_pack(ROOT, self.blob_root, manifest)
        self.assertEqual(findings, [])

    def test_mixing_in_an_unrelated_task_run_is_rejected(self):
        item_specs = [{"path": self.review_ui_paths[0], "commit": HISTORICAL_COMMIT}]
        item_specs.append({"path": UNRELATED_PATH, "commit": HISTORICAL_COMMIT})
        with self.assertRaises(evp.EvidencePackError) as ctx:
            evp.build_pack(
                ROOT, self.blob_root,
                task_id="0036-05",
                argv=[], action="historical-baseline-demo", base_commit=HISTORICAL_COMMIT,
                tool_name="task_evidence_pack", tool_version="1", environment_id=None,
                exit_status=0, item_specs=item_specs, criteria=[], counts={},
            )
        self.assertEqual(ctx.exception.rule, "EVP-UNRELATED-RUN")


if __name__ == "__main__":
    unittest.main()
