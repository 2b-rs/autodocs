"""Behavioral tests for the legacy publishers `_src/publish.sh` and
`_src/tools/publish_public_site.sh` (Task 0038-26).

These tests exercise the scripts for real (via `subprocess`), but only ever
against local, disposable scratch Git remotes created under a `tempfile`
directory for the duration of each test. No test ever configures a remote
that resolves to `2b-rs/autodocs` or performs any network call; `git@`,
`https://`, and `ssh://` remotes are never used here on purpose, since the
whole point of this Task is that such a destination must now be supplied
explicitly rather than being reachable by omission.
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

PUBLIC_DIRS = (
    "ar", "classes", "en", "es", "flags", "fr", "hi", "ko",
    "modules", "namespaces", "pt", "ru", "services", "zh",
)
PUBLIC_FILES = ("index.html", "style.css", "fold.js", "review.js")


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


class PublishScriptsAutomationSafetyRegressionTests(unittest.TestCase):
    """Freezes the fix: no more hard-coded identity/destination or bare
    unconditional force-push, without re-litigating findings this Task does
    not own (candidate isolation / broad staging stay with Task 0038-13)."""

    def test_publish_sh_has_no_hardcoded_integration_or_missing_recovery_state(self):
        text = PUBLISH_SH.read_text(encoding="utf-8")
        findings = safety.scan_text("_src/publish.sh", text, "shell")
        rules = {finding.rule for finding in findings}
        self.assertNotIn("AUTO005", rules)
        self.assertNotIn("AUTO010", rules)
        self.assertNotIn("AUTO004", rules)
        self.assertNotIn("AUTO001", rules)

    def test_publish_public_site_sh_has_no_identity_destination_or_force_findings(self):
        text = PUBLISH_PUBLIC_SITE_SH.read_text(encoding="utf-8")
        findings = safety.scan_text("_src/tools/publish_public_site.sh", text, "shell")
        by_line = {(finding.rule, finding.line) for finding in findings}
        # The three findings Task 0038-13 owns (lines 38 and 86, untouched by
        # this Task) are expected to remain exactly where they were.
        self.assertIn(("AUTO008", 38), by_line)
        self.assertIn(("AUTO010", 38), by_line)
        self.assertIn(("AUTO003", 86), by_line)
        # The four findings this Task owned (identity at 92, destination at
        # 104, force-push at 105) must be gone entirely.
        for rule, line in by_line:
            self.assertFalse(
                line in (92, 104, 105) and rule in ("AUTO004", "AUTO005"),
                "unexpected residual finding %s at line %s" % (rule, line),
            )

    def test_no_literal_publish_bot_or_public_repo_remote_remains(self):
        for path in (PUBLISH_SH, PUBLISH_PUBLIC_SITE_SH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("2b-rs/autodocs", text)
            self.assertNotIn("publish-bot", text)
            self.assertNotIn("user.name=", text)
            self.assertNotIn("user.email=", text)


class PublishShEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="publish-sh-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _fake_root_with_script(self):
        fake_root = self.tmp / "fake-repo-root"
        (fake_root / "_src").mkdir(parents=True)
        shutil.copy2(PUBLISH_SH, fake_root / "_src" / "publish.sh")
        (fake_root / "_src" / "publish.sh").chmod(0o755)
        for dir_name in PUBLIC_DIRS:
            target = fake_root / dir_name
            target.mkdir()
            (target / "stub.html").write_text("<html>stub</html>", encoding="utf-8")
        for file_name in PUBLIC_FILES:
            (fake_root / file_name).write_text("stub", encoding="utf-8")
        return fake_root

    def _seeded_bare_origin(self, env):
        origin = self.tmp / "origin.git"
        _run_git(["init", "--quiet", "--bare", str(origin)], cwd=self.tmp)
        seed = self.tmp / "seed"
        seed.mkdir()
        _run_git(["init", "--quiet", "-b", "main", str(seed)], cwd=self.tmp)
        (seed / "README.md").write_text("seed\n", encoding="utf-8")
        _run_git(["add", "-A"], cwd=seed, env=env)
        _run_git(
            ["-c", "user.name=Seed", "-c", "user.email=seed@example.invalid",
             "commit", "--quiet", "-m", "seed"],
            cwd=seed,
            env=env,
        )
        _run_git(["push", "--quiet", str(origin), "main"], cwd=seed, env=env)
        return origin

    def _run_publish(self, fake_root, extra_env):
        import os

        env = dict(os.environ)
        env.update(extra_env)
        return subprocess.run(
            ["bash", str(fake_root / "_src" / "publish.sh")],
            cwd=str(fake_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_missing_publish_remote_fails_closed_without_side_effects(self):
        fake_root = self._fake_root_with_script()
        publish_dir = self.tmp / "publish-dir-should-not-exist"
        result = self._run_publish(fake_root, {
            "PUBLISH_DIR": str(publish_dir),
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PUBLISH_REMOTE is required", result.stderr)
        self.assertFalse(publish_dir.exists())

    def test_missing_identity_fails_closed(self):
        fake_root = self._fake_root_with_script()
        result = self._run_publish(fake_root, {
            "PUBLISH_DIR": str(self.tmp / "publish-dir"),
            "PUBLISH_REMOTE": str(self.tmp / "unused.git"),
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PUBLISH_IDENTITY_NAME is required", result.stderr)

    def test_end_to_end_push_to_local_scratch_remote_uses_configured_identity(self):
        fake_root = self._fake_root_with_script()
        env_for_seed = _base_env(self.tmp)
        origin = self._seeded_bare_origin(env_for_seed)
        publish_dir = self.tmp / "publish-dir"
        result_log = self.tmp / "publish-result.log"
        result = self._run_publish(fake_root, {
            "PUBLISH_DIR": str(publish_dir),
            "PUBLISH_REMOTE": str(origin),
            "PUBLISH_IDENTITY_NAME": "Test Publisher",
            "PUBLISH_IDENTITY_EMAIL": "test-publisher@example.invalid",
            "PUBLISH_RESULT_LOG": str(result_log),
            "HOME": str(self.tmp),
        })
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Published via explicitly configured", result.stdout)

        # The bare origin's main branch must now carry a commit authored
        # under the explicitly configured identity, never the old
        # hard-coded 'publish-bot'/'tobias.anton@accenture.com' pair.
        author = _run_git(
            ["log", "-1", "--format=%an <%ae>", "main"],
            cwd=origin,
        ).strip()
        self.assertEqual(author, "Test Publisher <test-publisher@example.invalid>")
        self.assertNotIn("publish-bot", author)

        # Durable per-phase result journal recorded real phases, ending in
        # a successful push.
        log_text = result_log.read_text(encoding="utf-8")
        self.assertIn("phase=push status=0", log_text)
        self.assertIn("phase=complete status=0", log_text)

        # Safety guard preserved: no private paths leaked into the publish
        # clone.
        self.assertFalse((publish_dir / "_src").exists())


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
        author = _run_git(
            ["log", "-1", "--format=%an <%ae>"],
            cwd=export_dir,
        ).strip()
        self.assertEqual(author, "Test Publisher <test-publisher@example.invalid>")

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
