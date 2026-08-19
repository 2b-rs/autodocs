#!/usr/bin/env python3
"""Hermetic fail-closed tests for run-loop GitHub credential handles."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / "run-loop.sh"


class RunLoopCredentialHandleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="run-loop-credential-")
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.credentials = self.home / ".config" / "autodocs" / "credentials"
        self.request = self.root / "request" / "run.sh"
        self.credentials.mkdir(parents=True)
        self.credentials.chmod(0o700)
        self.request.parent.mkdir()
        self.request.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.request.chmod(0o700)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def invoke(self, handle: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home),
                "RUNNER_CREDENTIAL_DIR": str(self.credentials),
                "GITHUB_SSH_CREDENTIAL_HANDLE": handle,
            }
        )
        return subprocess.run(
            [str(RUNNER), "--once", "--skip-self-test", str(self.request)],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )

    def assert_no_secret_path(self, result: subprocess.CompletedProcess[str]) -> None:
        output = result.stdout + result.stderr
        self.assertNotIn(str(self.credentials), output)
        self.assertNotIn("BEGIN OPENSSH PRIVATE KEY", output)

    def test_unknown_handle_is_rejected(self) -> None:
        result = self.invoke("unknown-handle")
        self.assertEqual(2, result.returncode)
        self.assertIn("unsupported GitHub SSH credential handle: unknown-handle", result.stderr)
        self.assert_no_secret_path(result)

    def test_missing_handle_is_rejected(self) -> None:
        result = self.invoke("autodocs-deploy-key")
        self.assertEqual(1, result.returncode)
        self.assertIn("unavailable for handle: autodocs-deploy-key", result.stderr)
        self.assert_no_secret_path(result)

    def test_wrong_fingerprint_is_rejected(self) -> None:
        key = self.credentials / "autodocs-deploy-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "wrong-fixture", "-f", str(key)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        result = self.invoke("autodocs-deploy-key")
        self.assertEqual(1, result.returncode)
        self.assertIn("fingerprint mismatch for handle: autodocs-deploy-key", result.stderr)
        self.assert_no_secret_path(result)


    def test_matching_handle_is_agent_only_and_agent_is_stopped(self) -> None:
        key = self.credentials / "autodocs-deploy-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "positive-fixture", "-f", str(key)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        key.chmod(0o600)
        fingerprint = subprocess.run(
            ["ssh-keygen", "-lf", str(key), "-E", "sha256"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.split()[1]
        fixture_runner = self.root / "run-loop.sh"
        source = RUNNER.read_text(encoding="utf-8").replace(
            "SHA256:wtCFvdCIurWZj2NT4deL9Rg9uwqsL5nj17jlaoTW7a0", fingerprint, 1
        )
        fixture_runner.write_text(source, encoding="utf-8")
        fixture_runner.chmod(0o700)
        evidence = self.root / "agent-evidence.txt"
        self.request.write_text(
            "#!/bin/sh\nset -eu\n"
            "test -n \"${SSH_AUTH_SOCK:-}\"\n"
            "test -z \"${GITHUB_SSH_KEY_PATH:-}\"\n"
            f"ssh-add -l -E sha256 | grep -F {fingerprint!r} >/dev/null\n"
            f"printf '%s\\n' \"$SSH_AGENT_PID\" > {str(evidence)!r}\n",
            encoding="utf-8",
        )
        self.request.chmod(0o700)
        env = os.environ.copy()
        env.update({
            "HOME": str(self.home),
            "RUNNER_CREDENTIAL_DIR": str(self.credentials),
            "GITHUB_SSH_CREDENTIAL_HANDLE": "autodocs-deploy-key",
        })
        result = subprocess.run(
            [str(fixture_runner), "--once", "--skip-self-test", "--no-sandbox", "--notifier", "/usr/bin/true", str(self.request)],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=True,
        )
        agent_pid = int(evidence.read_text(encoding="utf-8").strip())
        with self.assertRaises(ProcessLookupError):
            os.kill(agent_pid, 0)
        self.assert_no_secret_path(result)


if __name__ == "__main__":
    unittest.main()
