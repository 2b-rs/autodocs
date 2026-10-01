"""Behavioral tests for the whole-site publisher `_src/tools/publish_public_site.sh`
(originally Task `0038-26`; consolidated onto this single tool by Task `0038-32`,
which retired the former `_src/publish.sh`).

These tests exercise the script for real (via `subprocess`), but only ever
against local, disposable scratch Git remotes created under a `tempfile`
directory for the duration of each test. No test ever configures a remote
that resolves to `2b-rs/autodocs` or performs any network call; `git@`,
`https://`, and `ssh://` remotes are never used here on purpose, since the
whole point of Task `0038-26` is that such a destination must now be
supplied explicitly rather than being reachable by omission.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLISH_SH = ROOT / "_src" / "publish.sh"
PUBLISH_PUBLIC_SITE_SH = ROOT / "_src" / "tools" / "publish_public_site.sh"
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))

import automation_safety as safety  # noqa: E402


def _run_git(args, cwd, env=None):
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout


def _base_env(base):
    import os

    env = dict(os.environ)
    env["HOME"] = str(base)
    env.pop("GIT_AUTHOR_NAME", None)
    env.pop("GIT_AUTHOR_EMAIL", None)
    env.pop("GIT_COMMITTER_NAME", None)
    env.pop("GIT_COMMITTER_EMAIL", None)
    return env


class PublishShRetirementTests(unittest.TestCase):
    """Task `0038-32` retired `_src/publish.sh` in favor of a single
    whole-site publisher (`_src/tools/publish_public_site.sh`), because its
    fixed `PUBLIC_DIRS`/`PUBLIC_FILES` directory allowlist was the exact
    structural cause of the `0019`/2026-08-22 incident: a newly approved
    subtree existed in no fixed list and would not have been published.
    These tests freeze the retirement so the file is not silently
    resurrected without anyone seeing why it was removed; see
    `docs/pipeline/tools.md` ("Konsolidierung 0038-32") for the recorded
    decision and justification."""

    def test_publish_sh_no_longer_exists(self):
        self.assertFalse(
            PUBLISH_SH.exists(),
            "_src/publish.sh was retired by Task 0038-32 (see "
            "docs/pipeline/tools.md); it must not be resurrected without a "
            "recorded decision reversing that retirement.",
        )

    def test_no_other_script_still_shells_out_to_publish_sh(self):
        for path in sorted(ROOT.rglob("*.sh")):
            if ".git" in path.parts or "output" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn(
                "_src/publish.sh",
                text,
                "%s still references the retired _src/publish.sh" % path,
            )


class PublishScriptsAutomationSafetyRegressionTests(unittest.TestCase):
    """Freezes the fix: no more hard-coded identity/destination or bare
    unconditional force-push, without re-litigating findings this Task does
    not own (candidate isolation / broad staging stay with Task 0038-13)."""

    def test_publish_public_site_sh_has_no_identity_destination_or_force_findings(self):
        text = PUBLISH_PUBLIC_SITE_SH.read_text(encoding="utf-8")
        findings = safety.scan_text("_src/tools/publish_public_site.sh", text, "shell")
        by_line = {(finding.rule, finding.line) for finding in findings}
        # The three findings Task 0038-13 owns (line 38 twice, and the
        # module-level broad-staging finding whose evidence text is the
        # unchanged "git add -A" line, which Task 0038-32's fix moved from
        # line 86 to line 91 without changing its evidence_sha256 -- see the
        # mechanically-refreshed automation_safety_policy.json entry) remain.
        self.assertIn(("AUTO008", 38), by_line)
        self.assertIn(("AUTO010", 38), by_line)
        self.assertIn(("AUTO003", 91), by_line)
        # The findings Tasks 0038-26/0038-32 own (identity, destination,
        # force-push, and the old defective content-read at line 80) must
        # not have crept back in under any line.
        for rule, line in by_line:
            self.assertFalse(
                rule in ("AUTO004", "AUTO005"),
                "unexpected residual finding %s at line %s" % (rule, line),
            )

    def test_no_literal_publish_bot_or_public_repo_remote_remains(self):
        text = PUBLISH_PUBLIC_SITE_SH.read_text(encoding="utf-8")
        self.assertNotIn("2b-rs/autodocs", text)
        self.assertNotIn("publish-bot", text)
        self.assertNotIn("user.name=", text)
        self.assertNotIn("user.email=", text)

    def test_content_read_no_longer_reads_repo_root_working_tree(self):
        """Regression guard for the confirmed 0038-32 defect: the export's
        file CONTENTS must come from the requested REVISION's git object
        (e.g. via `git archive "$REVISION"`), never from a `tar -C
        "$REPO_ROOT"` read of the checked-out working tree, which silently
        produced an incomplete export against a non-checked-out revision."""
        text = PUBLISH_PUBLIC_SITE_SH.read_text(encoding="utf-8")
        self.assertNotIn('tar -cf - -C "$REPO_ROOT"', text)
        self.assertIn('git archive "$REVISION"', text)


class PublishPublicSiteEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="publish-public-site-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.env = _base_env(self.tmp)

    def _scratch_source_repo(self, content="v1"):
        src = self.tmp / ("source-repo-" + content)
        src.mkdir()
        _run_git(["init", "--quiet", "-b", "trunk", str(src)], cwd=self.tmp)
        (src / "index.html").write_text("<html>%s</html>" % content, encoding="utf-8")
        (src / "docs").mkdir(exist_ok=True)
        (src / "docs" / "internal.md").write_text("internal, must be excluded", encoding="utf-8")
        (src / "DONE-owner-9999-01-request.md").write_text(
            "accepted claim provenance, must be excluded", encoding="utf-8"
        )
        _run_git(["add", "-A"], cwd=src, env=self.env)
        _run_git(
            ["-c", "user.name=Source", "-c", "user.email=source@example.invalid",
             "commit", "--quiet", "-m", content],
            cwd=src,
            env=self.env,
        )
        return src

    def _run_script(self, src, args, extra_env):
        import os

        env = dict(os.environ)
        env.update(self.env)
        env.update(extra_env)
        return subprocess.run(
            ["bash", str(PUBLISH_PUBLIC_SITE_SH), *args],
            cwd=str(src),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_dry_run_requires_identity_but_not_remote(self):
        src = self._scratch_source_repo()
        result = self._run_script(src, ["--dry-run"], {})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PUBLISH_IDENTITY_NAME is required", result.stderr)

        result_ok = self._run_script(src, ["--dry-run"], {
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
        })
        self.assertEqual(result_ok.returncode, 0, msg=result_ok.stderr)
        self.assertIn("Dry run only; not pushing", result_ok.stdout)

    def test_excludes_docs_from_export_and_does_not_leave_hardcoded_identity(self):
        src = self._scratch_source_repo()
        result = self._run_script(src, ["--dry-run"], {
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
        })
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        export_dir = src / "output" / "publish-export" / "tree"
        self.assertTrue((export_dir / "index.html").exists())
        self.assertFalse((export_dir / "docs").exists())
        self.assertFalse((export_dir / "DONE-owner-9999-01-request.md").exists())
        author = _run_git(
            ["log", "-1", "--format=%an <%ae>"],
            cwd=export_dir,
        ).strip()
        self.assertEqual(author, "Test Publisher <test-publisher@example.invalid>")

    def test_export_reads_content_from_a_revision_other_than_the_worktree(self):
        """The confirmed 0038-32 defect, reproduced and fixed: exporting a
        REVISION that is NOT the currently checked-out commit must still
        yield that revision's content, not the working tree's."""
        src = self._scratch_source_repo(content="v1")
        v1_sha = _run_git(["rev-parse", "trunk"], cwd=src).strip()

        (src / "index.html").write_text("<html>v2</html>", encoding="utf-8")
        _run_git(["add", "-A"], cwd=src, env=self.env)
        _run_git(
            ["-c", "user.name=Source", "-c", "user.email=source@example.invalid",
             "commit", "--quiet", "-m", "v2"],
            cwd=src,
            env=self.env,
        )
        v2_sha = _run_git(["rev-parse", "trunk"], cwd=src).strip()

        # Check out v1 in the working tree, but ask the script to export v2
        # -- the revision that is NOT checked out.
        _run_git(["checkout", "--quiet", v1_sha], cwd=src, env=self.env)
        self.assertEqual(
            (src / "index.html").read_text(encoding="utf-8"), "<html>v1</html>",
            "test setup: working tree must be at v1 content",
        )

        result = self._run_script(src, ["--dry-run", v2_sha], {
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
        })
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        export_dir = src / "output" / "publish-export" / "tree"
        exported = (export_dir / "index.html").read_text(encoding="utf-8")
        self.assertEqual(
            exported, "<html>v2</html>",
            "export must read REVISION's git object content (v2), not the "
            "checked-out working tree's content (v1) -- this is the "
            "confirmed defect Task 0038-32 fixed",
        )

    def test_missing_remote_fails_closed_after_dry_run_check(self):
        src = self._scratch_source_repo()
        result = self._run_script(src, [], {
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PUBLISH_REMOTE is required", result.stderr)

    def test_default_push_is_not_forced_and_rejects_divergent_history(self):
        origin = self.tmp / "origin.git"
        _run_git(["init", "--quiet", "--bare", str(origin)], cwd=self.tmp)

        identity = {
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
            "PUBLISH_REMOTE": str(origin),
        }

        src1 = self._scratch_source_repo(content="v1")
        first = self._run_script(src1, [], identity)
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        first_sha = _run_git(["rev-parse", "main"], cwd=origin).strip()

        # A second, unrelated orphan export pushed without opting into
        # force must be REJECTED by git itself (non-fast-forward) — proving
        # there is no unconditional --force left on the default path.
        src2 = self._scratch_source_repo(content="v2")
        second = self._run_script(src2, [], identity)
        self.assertNotEqual(second.returncode, 0, msg=second.stdout + second.stderr)
        second_sha = _run_git(["rev-parse", "main"], cwd=origin).strip()
        self.assertEqual(first_sha, second_sha, "default push must not have mutated the protected ref")

    def test_force_push_requires_explicit_approval_ref(self):
        origin = self.tmp / "origin.git"
        _run_git(["init", "--quiet", "--bare", str(origin)], cwd=self.tmp)
        src = self._scratch_source_repo(content="v1")
        result = self._run_script(src, [], {
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
            "PUBLISH_REMOTE": str(origin),
            "PUBLISH_ALLOW_FORCE_PUSH": "1",
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PUBLISH_FORCE_APPROVAL_REF is required", result.stderr)

    def test_gated_force_push_succeeds_and_records_recovery_evidence(self):
        origin = self.tmp / "origin.git"
        _run_git(["init", "--quiet", "--bare", str(origin)], cwd=self.tmp)
        identity = {
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
            "PUBLISH_REMOTE": str(origin),
        }

        src1 = self._scratch_source_repo(content="v1")
        first = self._run_script(src1, [], identity)
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        first_sha = _run_git(["rev-parse", "main"], cwd=origin).strip()

        src2 = self._scratch_source_repo(content="v2")
        forced_env = dict(identity)
        forced_env["PUBLISH_ALLOW_FORCE_PUSH"] = "1"
        forced_env["PUBLISH_FORCE_APPROVAL_REF"] = "TEST-APPROVAL-0038-26"
        second = self._run_script(src2, [], forced_env)
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        self.assertIn("approval=TEST-APPROVAL-0038-26", second.stderr)
        self.assertIn("pre_force_sha=%s" % first_sha, second.stderr)

        second_sha = _run_git(["rev-parse", "main"], cwd=origin).strip()
        self.assertNotEqual(first_sha, second_sha)


if __name__ == "__main__":
    unittest.main()
