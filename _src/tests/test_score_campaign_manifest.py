import copy
import hashlib
import json
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "score_campaign_manifest"
sys.path.insert(0, str(TOOLS_DIR))
import score_campaign_manifest as manifest  # noqa: E402


class ScoreCampaignManifestTests(unittest.TestCase):
    def fixture(self, name):
        return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))

    def assertError(self, value, expected):
        self.assertTrue(
            any(expected in error for error in manifest.validate_bom(value)),
            manifest.validate_bom(value),
        )

    def test_complete_fixture_validates(self):
        self.assertEqual(manifest.validate_bom(self.fixture("valid-complete.json")), [])
        self.assertEqual(manifest.validate_bom(self.fixture("valid-complete.json"), require_complete=True), [])

    def test_complete_manifest_requires_retained_snapshot_links(self):
        broken = self.fixture("valid-complete.json")
        del broken["snapshot"]
        self.assertError(broken, "complete BOMs require a snapshot object")

        broken = self.fixture("valid-complete.json")
        broken["sources"][0]["snapshot_archive"] = "outside/communication.tar"
        self.assertError(broken, "snapshot_archive must be under")

    def test_draft_fixture_is_structurally_valid_but_cannot_pass_completion_gate(self):
        draft = self.fixture("draft-blocked.json")
        self.assertEqual(manifest.validate_bom(draft), [])
        errors = manifest.validate_bom(draft, require_complete=True)
        self.assertTrue(any("BOM is not complete" in error for error in errors), errors)

    def test_complete_manifest_rejects_missing_required_source_fields(self):
        broken = self.fixture("valid-complete.json")
        del broken["sources"][0]["archive"]
        self.assertError(broken, "sources[0] is missing keys: archive")
        self.assertError(broken, "sources[0].archive must be an object")

    def test_moving_ref_is_rejected(self):
        broken = self.fixture("valid-complete.json")
        broken["sources"][0]["release_ref"] = "main"
        self.assertError(broken, "must not be a moving ref")

    def test_malformed_commit_and_archive_hash_are_rejected(self):
        broken = self.fixture("valid-complete.json")
        broken["sources"][0]["resolved_commit"] = "ABC"
        broken["sources"][0]["archive"]["sha256"] = "not-a-hash"
        self.assertError(broken, "resolved_commit must be a lowercase full 40-character Git SHA")
        self.assertError(broken, "archive.sha256 must be a lowercase 64-character SHA-256")

    def test_duplicate_repository_is_rejected(self):
        broken = self.fixture("valid-complete.json")
        duplicate = copy.deepcopy(broken["sources"][0])
        broken["sources"].append(duplicate)
        self.assertError(broken, "sources must not repeat repository 'communication'")

    def test_invalid_url_and_source_path_are_rejected(self):
        broken = self.fixture("valid-complete.json")
        broken["sources"][0]["repository_url"] = "https://example.invalid/communication.git"
        broken["sources"][0]["source_paths"] = ["../outside"]
        self.assertError(broken, "repository_url must be https://github.com/eclipse-score/communication.git")
        self.assertError(broken, "source_paths[0] must be a repository-relative path")

    def test_exclusion_requires_rationale_and_cannot_overlap_a_source(self):
        broken = self.fixture("valid-complete.json")
        broken["exclusions"] = [{"repository": "communication", "rationale": ""}]
        self.assertError(broken, "exclusions[0].rationale must be a non-empty explanation")
        self.assertError(broken, "cannot be both a source and an exclusion")

    def test_scraper_pin_must_be_the_expected_path_and_full_sha(self):
        broken = self.fixture("valid-complete.json")
        broken["scraper"] = {"path": "score_scrape.py", "commit": "1234"}
        self.assertError(broken, "scraper.path must be '_src/tools/score_scrape.py'")
        self.assertError(broken, "scraper.commit must be a lowercase full 40-character Git SHA")

    def test_local_checkout_verification_checks_origin_commit_and_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "communication"
            subprocess.run(["git", "init", str(checkout)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "-C", str(checkout), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(checkout), "config", "user.name", "Test User"], check=True)
            (checkout / "source.rst").write_text("fixture source\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(checkout), "add", "source.rst"], check=True)
            subprocess.run(["git", "-C", str(checkout), "commit", "-m", "fixture"], check=True, stdout=subprocess.PIPE)
            subprocess.run(
                ["git", "-C", str(checkout), "remote", "add", "origin", "https://github.com/eclipse-score/communication.git"],
                check=True,
            )
            commit = subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "HEAD"],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            archive = subprocess.run(
                ["git", "-C", str(checkout), "archive", "--format=tar", commit],
                check=True,
                stdout=subprocess.PIPE,
            ).stdout

            bom = self.fixture("valid-complete.json")
            bom["sources"][0]["resolved_commit"] = commit
            bom["sources"][0]["archive"]["sha256"] = hashlib.sha256(archive).hexdigest()
            self.assertEqual(manifest.verify_bom_checkouts(bom, {"communication": checkout}), [])

            bom["sources"][0]["archive"]["sha256"] = "0" * 64
            errors = manifest.verify_bom_checkouts(bom, {"communication": checkout})
            self.assertTrue(any("checkout archive" in error for error in errors), errors)

    def test_cli_reports_draft_gate_failure(self):
        result = subprocess.run(
            [
                sys.executable,
                str(TOOLS_DIR / "score_campaign_manifest.py"),
                "--require-complete",
                str(FIXTURES_DIR / "draft-blocked.json"),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("BOM is not complete", result.stderr)


if __name__ == "__main__":
    unittest.main()
