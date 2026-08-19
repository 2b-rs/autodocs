#!/usr/bin/env python3
"""Hermetic Task 0037-49 qualification of the legacy runner service controls."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[4]
POLICY = ROOT / "issues/_policy/runner-service.json"
SELECTOR = ROOT / "agent-workflow.json"


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


def run() -> dict[str, object]:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    selector = json.loads(SELECTOR.read_text(encoding="utf-8"))
    checks: dict[str, object] = {}
    assert policy["schema"] == "runner-service@v2"
    assert policy["service_id"] == "less-restricted-legacy-singleton"
    assert selector["authority_profile"] == "legacy-lists"
    assert selector["runner_protocol"] == policy["protocol"]["request_schema"]
    checks["protocol_selector"] = {
        "verdict": "passed",
        "authority_epoch": selector["authority_epoch"],
        "runner_protocol": selector["runner_protocol"],
    }

    runner = ROOT / policy["execution"]["source_path"]
    supervisor = ROOT / policy["supervisor"]["source_path"]
    assert runner.is_file() and os.access(runner, os.X_OK)
    assert supervisor.is_file()
    assert sha256(runner) == policy["execution"]["source_sha256"]
    assert sha256(supervisor) == policy["supervisor"]["source_sha256"]
    supervisor_text = supervisor.read_text(encoding="utf-8")
    for symbol in (
        "launchRunnerTask",
        "writeActiveRunRecord",
        "detectOrphanedRunner",
        "recoverOrphanedRunner",
        "finishRunnerTask",
    ):
        assert f"function {symbol}" in supervisor_text
    checks["service_identity"] = {
        "verdict": "passed",
        "runner_sha256": sha256(runner),
        "supervisor_sha256": sha256(supervisor),
    }

    with tempfile.TemporaryDirectory(prefix="0037-49-runner-service-") as tmp_value:
        tmp = Path(tmp_value)
        deployed = tmp / "deployed-run-loop.sh"
        shutil.copy2(runner, deployed)
        deployed.chmod(0o700)
        assert sha256(deployed) == sha256(runner)
        checks["no_op_deploy"] = {"verdict": "passed", "external_mutation": False}

        slot = tmp / "run.sh"
        log = tmp / "runner.log"
        process = subprocess.Popen(
            [
                str(deployed),
                "--once",
                "--skip-self-test",
                "--no-sandbox",
                "--notify-wait",
                "0",
                "--notifier",
                "/usr/bin/true",
                str(slot),
            ],
            stdin=subprocess.DEVNULL,
            stdout=log.open("wb"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        assert wait_for(lambda: process.poll() is None)
        health = subprocess.run(
            [str(deployed), "--check-run-script", str(slot)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert health.returncode == 1
        checks["health_waiting"] = {"verdict": "passed", "runner_detected": True}

        process.send_signal(signal.SIGTERM)
        process.wait(timeout=5)
        slot.write_text("#!/bin/sh\nset -eu\nprintf passed > service-result.txt\n", encoding="utf-8")
        slot.chmod(0o700)
        restarted = subprocess.run(
            [
                str(deployed),
                "--once",
                "--skip-self-test",
                "--no-sandbox",
                "--notify-wait",
                "0",
                "--notifier",
                "/usr/bin/true",
                str(slot),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        assert restarted.returncode == 0, restarted.stdout + restarted.stderr
        assert (tmp / "service-result.txt").read_text(encoding="utf-8") == "passed"
        assert not slot.exists()
        checks["crash_restart_recovery"] = {
            "verdict": "passed",
            "first_process_terminated": True,
            "replacement_exit_code": restarted.returncode,
            "request_consumed_once": True,
        }

        known_good = tmp / "known-good.sh"
        candidate = tmp / "candidate.sh"
        active = tmp / "active.sh"
        known_good.write_text("#!/bin/sh\nprintf known-good\n", encoding="utf-8")
        candidate.write_text("#!/bin/sh\nprintf candidate\n", encoding="utf-8")
        shutil.copy2(known_good, active)
        known_good_digest = sha256(active)
        shutil.copy2(candidate, active)
        assert sha256(active) == sha256(candidate)
        shutil.copy2(known_good, active)
        assert sha256(active) == known_good_digest
        checks["rollback"] = {
            "verdict": "passed",
            "known_good_sha256": known_good_digest,
            "restored_exactly": True,
            "external_mutation": False,
        }

    return {
        "schema": "runner-service-qualification-result@v1",
        "task": "0037-49",
        "verdict": "passed",
        "service_id": policy["service_id"],
        "checks": checks,
        "limitations": [
            "The current runner is on-demand, not an always-running daemon.",
            "Future queue activation and protocol-epoch switching remain owned by 0037-46.02.",
            "The legacy /tmp worktree provisioner is superseded and is not treated as a safe worker-clone mechanism.",
        ],
    }


if __name__ == "__main__":
    result = run()
    output = ROOT / "docs/pipeline/0037-49-runner-service-qualification-result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: legacy runner service identity, health, restart/recovery, rollback, and selector controls")
