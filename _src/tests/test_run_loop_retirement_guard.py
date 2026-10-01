"""Hermetic proof for Task 0037-50.02's singleton retirement guard.

No test starts a host service or rollback executor.  Each case sources the
guard into a disposable shell process and exercises only fixture files.
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "runner-host" / "lib" / "retirement_guard.sh"
LOOP = ROOT / "runner-host" / "run-loop.sh"


class RetirementGuardTest(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="retirement-guard-"))
        self.archive = self.temp / "output" / "run-archive"

    def tearDown(self):
        shutil.rmtree(self.temp, ignore_errors=True)

    def selector(self, value):
        (self.temp / "agent-workflow.json").write_text(json.dumps({"runner_protocol": value}) + "\n")

    def request(self, name="run.sh", text="#!/usr/bin/env bash\necho safe\n"):
        path = self.temp / name
        path.write_text(text)
        return path

    def invoke(self, request, *, sentinel="He's dead, Jim!", callback=""):
        script = r'''
set +e
source "$1"
CALLBACK_FILE="$6"
callback() { printf '%s %s\n' "$1" "$2" >> "$CALLBACK_FILE"; }
if [[ -n "$5" ]]; then
  retirement_guard_admit "$2" "$3" "$4" "He's dead, Jim!" callback
else
  retirement_guard_admit "$2" "$3" "$4" "He's dead, Jim!"
fi
status=$?
printf 'status=%s\narchive=%s\n' "$status" "${RETIREMENT_GUARD_ARCHIVE_PATH:-}"
exit 0
'''
        callback_file = self.temp / "callback.log"
        return subprocess.run(
            ["bash", "-c", script, "guard", str(GUARD), str(self.temp), str(request), str(self.archive), callback, str(callback_file)],
            capture_output=True,
            text=True,
            check=True,
        ), callback_file

    def result(self, completed):
        return dict(line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line)

    def test_healthy_queue_rejection_is_retained(self):
        self.selector("runner-queue@v1")
        completed, _ = self.invoke(self.request())
        result = self.result(completed)
        self.assertEqual("64", result["status"])
        archived = Path(result["archive"])
        self.assertTrue(archived.is_file())
        self.assertIn("SINGLETON_RETIRED", archived.with_suffix(".result.txt").read_text())

    def test_sentinel_is_exempt_while_queue_is_healthy(self):
        self.selector("runner-queue@v1")
        request = self.request(text="#!/usr/bin/env bash\n# He's dead, Jim!\n")
        completed, _ = self.invoke(request)
        self.assertEqual("0", self.result(completed)["status"])
        self.assertTrue(request.exists())

    def test_restored_legacy_passes_through(self):
        self.selector("runner-request@v1")
        request = self.request()
        completed, _ = self.invoke(request)
        self.assertEqual("0", self.result(completed)["status"])
        self.assertTrue(request.exists())

    def test_malformed_selector_parks_fail_closed_and_maps_once(self):
        (self.temp / "agent-workflow.json").write_text('{"runner_protocol": "broken"}\n')
        completed, callback_file = self.invoke(self.request(), callback="test-only")
        result = self.result(completed)
        self.assertEqual("65", result["status"])
        self.assertIn("FAILOVER_REQUIRED", Path(result["archive"]).with_suffix(".result.txt").read_text())
        self.assertEqual(1, len(callback_file.read_text().splitlines()))

    def test_same_second_rejections_do_not_overwrite_each_other(self):
        self.selector("runner-queue@v1")
        first, _ = self.invoke(self.request("first.sh"))
        second, _ = self.invoke(self.request("second.sh"))
        first_path = Path(self.result(first)["archive"])
        second_path = Path(self.result(second)["archive"])
        self.assertNotEqual(first_path, second_path)
        self.assertEqual("echo safe\n", first_path.read_text().splitlines()[-1] + "\n")
        self.assertEqual("echo safe\n", second_path.read_text().splitlines()[-1] + "\n")

    def test_loop_sources_guard_script_relatively(self):
        source_line = 'source "$SCRIPT_DIR/lib/retirement_guard.sh"'
        self.assertIn(source_line, LOOP.read_text())


if __name__ == "__main__":
    unittest.main()
