import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "_src/tools/automation_safety_policy.json"
REPORT_DIR = ROOT / "logs/validate-automation-safety/0040-10"

policy = json.loads(POLICY_PATH.read_text())
assert POLICY_PATH.read_bytes() == (REPORT_DIR / "final-policy.json").read_bytes()

run_report = json.loads((REPORT_DIR / "final-run-loop.json").read_text())
focused = json.loads((REPORT_DIR / "remediation-focused-scan.json").read_text())
worktree_full = json.loads((REPORT_DIR / "final-worktree-full-scan.json").read_text())
live_full = json.loads((REPORT_DIR / "final-full-scan.json").read_text())
dossier = (ROOT / "docs/dossiers/0040-10-automation-safety-scope-and-dispositions.md").read_text()
source = (ROOT / "_src/run-loop.sh").read_text()

run_entries = [item for item in policy["dispositions"] if item["path"] == "_src/run-loop.sh"]
run_keys = {
    (item["path"], item["rule"], item["line"], item["symbol"], item["evidence_sha256"])
    for item in run_entries
}
report_keys = {
    (item["path"], item["rule"], item["line"], item["symbol"], item["evidence_sha256"])
    for item in run_report["findings"]
}
assert len(run_entries) == len(run_keys) == 21
assert run_keys == report_keys
assert sum(item["rule"] == "AUTO010" for item in run_entries) == 9
assert run_report["verdict"] == "PASS"
assert run_report["counts"] == {
    "advisory": 0,
    "disposed_critical": 10,
    "findings": 21,
    "policy_errors": 0,
    "unresolved_critical": 0,
}

expected_baseline = {
    (
        "_src/tools/provision_tmp_worktree.sh",
        "AUTO001",
        41,
        "<module>",
        "e460b86b406a54658989c2017713330f0ea889d7fa2682d11157c97751c40133",
        "0038-14",
    ),
    (
        "_src/tools/provision_worker_clone.sh",
        "AUTO001",
        86,
        "<module>",
        "1d26f6ffd567197b8cd9b1c279c6660aa1ffa83108c3468be5bcb03e2b2887b7",
        "0041-05",
    ),
    (
        "_src/tools/provision_worker_clone.sh",
        "AUTO010",
        86,
        "<module>",
        "1d26f6ffd567197b8cd9b1c279c6660aa1ffa83108c3468be5bcb03e2b2887b7",
        "0041-05",
    ),
}
actual_baseline = {
    (
        item["path"],
        item["rule"],
        item["line"],
        item["symbol"],
        item["evidence_sha256"],
        item["owner_task"],
    )
    for item in policy["dispositions"]
    if item["path"]
    in {
        "_src/tools/provision_tmp_worktree.sh",
        "_src/tools/provision_worker_clone.sh",
    }
}
assert actual_baseline == expected_baseline
assert focused["verdict"] == "PASS"
assert focused["counts"]["unresolved_critical"] == 0
assert focused["counts"]["policy_errors"] == 0
assert worktree_full["verdict"] == "PASS"
assert worktree_full["counts"]["unresolved_critical"] == 0
assert worktree_full["counts"]["policy_errors"] == 0
assert live_full["counts"]["policy_errors"] == 0
assert live_full["counts"]["unresolved_critical"] == 10
assert {
    item["path"] for item in live_full["findings"] if item["status"] == "unresolved"
} == {"_src/run-loop.sh"}

assert source.index("cleanup_runner_state()") < source.index('if ! mkdir -p "$OUTPUT_DIR"')
assert source.index('if ! mkdir -p "$RUNNER_TMP_DIR"') < source.index(
    "RUNNER_TMP_DIR_CREATED=true"
) < source.index("trap 'cleanup_runner_state") < source.index(
    'if ! chmod 700 "$RUNNER_TMP_DIR"'
)
assert "if declare -F resume_applescript" in source
assert (
    'if (( original_status != 0 )); then\n    exit "$original_status"\n  fi\n'
    '  exit "$cleanup_status"'
) in source

assert len(re.findall(r"^\| C[0-9]+ \|", dossier, re.MULTILINE)) == 10
assert len(re.findall(r"^\| H[0-9]+ \|", dossier, re.MULTILINE)) == 11
assert len(re.findall(r"^\| B[0-9]+ \|", dossier, re.MULTILINE)) == 3
for value in (
    "agent:zed:0040-10:20260818T141307Z-894c3cd8b63b",
    "2026-08-18T14:13:07Z",
    "6d9ae83a-8d45-479a-9807-13f22b8745a5",
    "nine `AUTO010`",
):
    assert value in dossier
assert "Acceptance identity:** none" in dossier

print("PASS remediation policy/source/report/dossier consistency")
print("run-loop=21 exact dispositions; AUTO010=9; baseline-blockers=3")
print(
    "worktree-full unresolved-critical=0 policy-errors=0; "
    "live pre-commit unresolved-critical=10 policy-errors=0"
)
