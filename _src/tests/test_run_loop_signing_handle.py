#!/usr/bin/env python3
"""Hermetic fail-closed tests for runner-visible SSH signing handles."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / "run-loop.sh"
EXPECTED_FINGERPRINT = "SHA256:YWg/nPlBol+BkcbC/S0yIDBaw7xpKmfSjreQM8rgDjU"


class RunLoopSigningHandleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="run-loop-signing-")
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.key = self.root / "credentials" / "agent-commit-key"
        self.request = self.root / "request" / "run.sh"
        self.key.parent.mkdir(parents=True)
        self.request.parent.mkdir()
        self.request.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.request.chmod(0o700)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def invoke(self, handle: str, runner: Path = RUNNER) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home),
                "AUTODOCS_SIGNING_KEY_PATH": str(self.key),
                "AUTODOCS_SIGNING_CREDENTIAL_HANDLE": handle,
            }
        )
        return subprocess.run(
            [
                str(runner),
                "--once",
                "--skip-self-test",
                "--no-sandbox",
                "--notifier",
                "/usr/bin/true",
                str(self.request),
            ],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )

    def assert_no_secret_path(self, result: subprocess.CompletedProcess[str]) -> None:
        output = result.stdout + result.stderr
        self.assertNotIn(str(self.key.parent), output)
        self.assertNotIn("BEGIN OPENSSH PRIVATE KEY", output)

    def generate_key(self, comment: str) -> str:
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(self.key)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.key.chmod(0o600)
        return subprocess.run(
            ["ssh-keygen", "-lf", str(self.key), "-E", "sha256"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.split()[1]

    def test_unknown_handle_is_rejected(self) -> None:
        result = self.invoke("unknown-signing-handle")
        self.assertEqual(2, result.returncode)
        self.assertIn("unsupported signing credential handle: unknown-signing-handle", result.stderr)
        self.assert_no_secret_path(result)

    def test_missing_handle_is_rejected(self) -> None:
        result = self.invoke("agent-commit-key")
        self.assertEqual(1, result.returncode)
        self.assertIn("signing credential is unavailable for handle: agent-commit-key", result.stderr)
        self.assert_no_secret_path(result)

    def test_wrong_fingerprint_is_rejected(self) -> None:
        self.generate_key("wrong-signing-fixture")
        result = self.invoke("agent-commit-key")
        self.assertEqual(1, result.returncode)
        self.assertIn("signing credential fingerprint mismatch for handle: agent-commit-key", result.stderr)
        self.assert_no_secret_path(result)

    def test_matching_handle_signs_via_agent_and_agent_is_stopped(self) -> None:
        fingerprint = self.generate_key("positive-signing-fixture")
        fixture_runner = self.root / "run-loop.sh"
        source = RUNNER.read_text(encoding="utf-8").replace(EXPECTED_FINGERPRINT, fingerprint, 1)
        fixture_runner.write_text(source, encoding="utf-8")
        fixture_runner.chmod(0o700)

        payload = self.root / "readiness.json"
        evidence = self.root / "agent-evidence.txt"
        self.request.write_text(
            "#!/bin/sh\nset -eu\n"
            "test -n \"${SSH_AUTH_SOCK:-}\"\n"
            "test -z \"${AUTODOCS_SIGNING_KEY_PATH:-}\"\n"
            "test -r \"$AUTODOCS_SIGNING_PUBLIC_KEY_PATH\"\n"
            f"ssh-add -l -E sha256 | grep -F {fingerprint!r} >/dev/null\n"
            f"printf '%s\\n' '{{\"schema\":\"readiness@v1\"}}' > {str(payload)!r}\n"
            f"ssh-keygen -Y sign -f \"$AUTODOCS_SIGNING_PUBLIC_KEY_PATH\" -n autodocs-readiness {str(payload)!r} >/dev/null\n"
            f"printf '%s\\n' \"$SSH_AGENT_PID\" > {str(evidence)!r}\n",
            encoding="utf-8",
        )
        self.request.chmod(0o700)
        result = self.invoke("agent-commit-key", fixture_runner)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

        allowed = self.root / "allowed_signers"
        public_key = self.key.with_suffix(".pub").read_text(encoding="utf-8").split()
        allowed.write_text(
            f"agent-commit@autodocs.invalid namespaces=\"autodocs-readiness\" {public_key[0]} {public_key[1]}\n",
            encoding="utf-8",
        )
        with payload.open("rb") as payload_stream:
            verification = subprocess.run(
                [
                    "ssh-keygen",
                    "-Y",
                    "verify",
                    "-f",
                    str(allowed),
                    "-I",
                    "agent-commit@autodocs.invalid",
                    "-n",
                    "autodocs-readiness",
                    "-s",
                    str(payload) + ".sig",
                ],
                stdin=payload_stream,
                text=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(0, verification.returncode, verification.stderr.decode())
        agent_pid = int(evidence.read_text(encoding="utf-8").strip())
        with self.assertRaises(ProcessLookupError):
            os.kill(agent_pid, 0)
        self.assert_no_secret_path(result)


if __name__ == "__main__":
    unittest.main()
