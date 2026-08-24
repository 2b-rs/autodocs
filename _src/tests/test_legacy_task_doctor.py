import ast
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "legacy_task_doctor"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "legacy_task_doctor",
    TOOLS / "legacy_task_doctor.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
doctor = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = doctor
MODULE_SPEC.loader.exec_module(doctor)


class FixtureRepository:
    def __init__(self, case):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        files = dict(FIXTURE_DATA["common_files"])
        files.update(case.get("files", {}))
        for relative, text in files.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.reachable = set(case.get("reachable_commits", []))

    def close(self):
        self.temporary.cleanup()

    def scan(self):
        return doctor.scan_repository(self.root, reachable_commits=self.reachable)


with (FIXTURES / "cases.json").open(encoding="utf-8") as handle:
    FIXTURE_DATA = json.load(handle)
CASES = {case["name"]: case for case in FIXTURE_DATA["cases"]}


def snapshot_tree(root):
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            result[relative] = ("symlink", stat.S_IMODE(info.st_mode), os.readlink(path))
        elif path.is_file():
            result[relative] = ("file", stat.S_IMODE(info.st_mode), path.read_bytes())
        else:
            result[relative] = ("directory", stat.S_IMODE(info.st_mode), None)
    return result


def rules(report):
    return {finding["rule"] for finding in report["findings"]}


class LegacyTaskDoctorFixtureTests(unittest.TestCase):
    def test_fixture_manifest_and_cases_are_versioned(self):
        manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "legacy-task-doctor-fixture-manifest@v1")
        self.assertEqual(set(manifest["cases"]), set(CASES))
        self.assertEqual(FIXTURE_DATA["schema"], "legacy-task-doctor-fixtures@v1")

    def test_clean_fixture_has_zero_findings(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        report = repo.scan()
        self.assertEqual(report["verdict"], "CLEAN")
        self.assertEqual(report["counts"], {"error": 0, "warning": 0, "info": 0, "total": 0})
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["plans"], [])
        self.assertEqual(report["inventory"]["tasks"], 1)
        self.assertEqual(report["inventory"]["active_claims"], 1)
        self.assertEqual(report["normalized"]["tasks"][0]["id"], "1000-01")
        self.assertEqual(report["normalized"]["claims"][0]["owner_token"], "agent:fixture:1000-01:clean-claim")

    def test_historical_fixture_rule_coverage(self):
        for name, case in sorted(CASES.items()):
            with self.subTest(case=name):
                repo = FixtureRepository(case)
                try:
                    report = repo.scan()
                finally:
                    repo.close()
                expected = set(case["expected_rules"])
                self.assertEqual(rules(report), expected, name)
                self.assertEqual(
                    report["verdict"],
                    "FINDINGS" if expected else "CLEAN",
                )

    def test_marker_and_ref_case_covers_all_ref_classes(self):
        repo = FixtureRepository(CASES["marker-and-refs"])
        self.addCleanup(repo.close)
        report = repo.scan()
        observed = rules(report)
        self.assertIn("LTD-MARKER-UNDEFINED", observed)
        self.assertIn("LTD-REF-HIDDEN", observed)
        self.assertIn("LTD-REF-PLACEHOLDER", observed)
        self.assertIn("LTD-REF-MALFORMED", observed)
        self.assertIn("LTD-REF-DUPLICATE", observed)
        self.assertIn("LTD-REF-UNREACHABLE", observed)
        self.assertIn("LTD-REF-STATE-DIVERGED", observed)

    def test_claim_case_detects_state_identity_scope_and_resume_drift(self):
        repo = FixtureRepository(CASES["claim-drift"])
        self.addCleanup(repo.close)
        report = repo.scan()
        observed = rules(report)
        for rule in (
            "LTD-CLAIM-STATE-DIVERGED",
            "LTD-CLAIM-TERMINAL-RETAINED",
            "LTD-CLAIM-IDENTITY-MISMATCH",
            "LTD-CLAIM-BASE-ABBREVIATED",
            "LTD-CLAIM-SCOPE-INVALID",
            "LTD-CLAIM-SCOPE-MISMATCH",
            "LTD-CLAIM-SCOPE-MISSING",
            "LTD-CLAIM-NEXT-STEP-MISSING",
            "LTD-CLAIM-TASK-MISSING",
            "LTD-TASK-CLAIM-MISSING",
            "LTD-TASK-CLAIM-POINTER-MISMATCH",
        ):
            self.assertIn(rule, observed)

    def test_prerequisite_case_detects_graph_and_parent_state(self):
        repo = FixtureRepository(CASES["prerequisites-and-parent"])
        self.addCleanup(repo.close)
        report = repo.scan()
        cycle = next(finding for finding in report["findings"] if finding["rule"] == "LTD-PREREQ-CYCLE")
        self.assertEqual(cycle["message"], "prerequisite cycle: 1000-02 -> 1000-03 -> 1000-02")
        self.assertIn("LTD-PARENT-CLOSURE-ELIGIBLE", rules(report))
        self.assertIn("LTD-TERMINAL-UNSATISFIED-PREREQ", rules(report))

    def test_bootstrap_case_detects_link_command_and_policy_conflict(self):
        repo = FixtureRepository(CASES["bootstrap-policy"])
        self.addCleanup(repo.close)
        report = repo.scan()
        observed = rules(report)
        self.assertIn("LTD-INSTRUCTION-LINK-MISSING", observed)
        self.assertIn("LTD-INSTRUCTION-NEAR-NAME", observed)
        self.assertIn("LTD-POLICY-CONTRADICTION", observed)
        self.assertIn("LTD-BOOT-COMMAND-MISSING", observed)
        self.assertIn("LTD-BOOT-DIGEST-PLACEHOLDER", observed)

    def test_aligned_sentinel_policies_are_a_clean_negative_control(self):
        repo = FixtureRepository(CASES["aligned-policy"])
        self.addCleanup(repo.close)
        report = repo.scan()
        self.assertEqual(report["verdict"], "CLEAN")
        self.assertEqual(report["findings"], [])


class LegacyTaskDoctorDeterminismTests(unittest.TestCase):
    def test_report_json_is_byte_deterministic_for_every_fixture(self):
        for name, case in sorted(CASES.items()):
            with self.subTest(case=name):
                repo = FixtureRepository(case)
                try:
                    first = doctor._canonical_json(repo.scan())
                    second = doctor._canonical_json(repo.scan())
                finally:
                    repo.close()
                self.assertEqual(first, second)
                self.assertTrue(first.endswith("\n"))
                self.assertNotIn(str(repo.root), first)

    def test_tracked_current_determinism_evidence_is_digest_bound(self):
        evidence_path = (
            ROOT
            / "logs"
            / "legacy-task-doctor"
            / "0038-04-current-determinism.json"
        )
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertEqual(
            evidence["schema"],
            "legacy-task-doctor-current-determinism@v1",
        )
        self.assertTrue(evidence["identical"])
        self.assertEqual(
            evidence["reports"][0]["sha256"],
            evidence["reports"][1]["sha256"],
        )
        self.assertEqual(evidence["reports"][0]["bytes"], evidence["reports"][1]["bytes"])
        self.assertLessEqual(evidence["summary_lines"], 10)
        self.assertTrue(all(value == 0 for value in evidence["plan_safety"].values()))
        # This evidence is a historical snapshot bound to Task 0038-04's own
        # closure commit, not to whatever the tool currently contains: later
        # prerequisite-approved Tasks (e.g. 0038-21) extend the same tool, so
        # comparing against live worktree bytes would make this assertion
        # fail for every subsequent tool change regardless of 0038-04's own
        # correctness. Recover 0038-04's recorded REF from TODO.md and
        # compare the evidence digest against the tool blob at that
        # historical commit instead, which is what the evidence actually
        # attests to and decouples it from later tool evolution.
        todo_text = (ROOT / "TODO.md").read_text(encoding="utf-8")
        ref_match = re.search(r"\*\*0038-04\*\*[^\n]*REF:\s*([0-9a-f]{40})", todo_text)
        self.assertIsNotNone(ref_match, "0038-04 REF not found in TODO.md")
        historical_ref = ref_match.group(1)
        historical_tool = subprocess.run(
            ["git", "show", f"{historical_ref}:_src/tools/legacy_task_doctor.py"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        ).stdout
        self.assertEqual(
            evidence["tool"]["sha256"],
            doctor.hashlib.sha256(historical_tool).hexdigest(),
        )
        required_current_rules = {
            "LTD-MARKER-UNDEFINED",
            "LTD-REF-HIDDEN",
            "LTD-REF-MALFORMED",
            "LTD-CLAIM-STATE-DIVERGED",
            "LTD-CLAIM-TERMINAL-RETAINED",
            "LTD-CLAIM-IDENTITY-MISMATCH",
            "LTD-INSTRUCTION-LINK-MISSING",
            "LTD-INSTRUCTION-NEAR-NAME",
            "LTD-POLICY-CONTRADICTION",
        }
        self.assertTrue(required_current_rules.issubset(evidence["rule_counts"]))

    def test_summary_is_bounded_and_is_embedded_in_json(self):
        repo = FixtureRepository(CASES["claim-drift"])
        self.addCleanup(repo.close)
        report = repo.scan()
        summary = doctor.render_summary(report)
        self.assertLessEqual(len(summary), 10)
        self.assertEqual(list(summary), report["summary"])
        self.assertTrue(summary[0].startswith("legacy-task-doctor FINDINGS:"))

    def test_findings_have_stable_evidence_digests(self):
        repo = FixtureRepository(CASES["marker-and-refs"])
        self.addCleanup(repo.close)
        report = repo.scan()
        for finding in report["findings"]:
            digest = doctor.hashlib.sha256(finding["evidence"].encode("utf-8")).hexdigest()
            self.assertEqual(finding["evidence_sha256"], digest)

    def test_plans_use_only_allowed_advisory_actions_and_actors(self):
        allowed = {
            "owner-reconcile-claim": "claim-owner-or-authorized-maintainer",
            "claim-and-perform-package-closure": "eligible-task-agent",
            "policy-authority-reconcile": "policy-owner-or-authorized-maintainer",
            "verify-or-reconcile-reference": "backlog-owner-or-authorized-maintainer",
            "review-and-reconcile-prerequisite": "backlog-owner-or-authorized-maintainer",
            "review-and-reconcile-exact-entry": "backlog-owner-or-authorized-maintainer",
            "assign-privileged-integrator": "privileged-integrator",
        }
        for name, case in sorted(CASES.items()):
            with self.subTest(case=name):
                repo = FixtureRepository(case)
                try:
                    report = repo.scan()
                finally:
                    repo.close()
                self.assertEqual(len(report["plans"]), len(report["findings"]))
                for plan in report["plans"]:
                    self.assertFalse(plan["automatic"])
                    self.assertFalse(plan["destructive"])
                    self.assertTrue(plan["target_paths"])
                    self.assertIn(plan["action"], allowed)
                    self.assertEqual(plan["required_actor"], allowed[plan["action"]])
                    for target in plan["target_paths"]:
                        self.assertTrue(doctor._safe_relative_path(target), target)
                    rendered = json.dumps(plan, sort_keys=True).lower()
                    self.assertNotIn("takeover", rendered)
                    self.assertNotIn("delete-foreign", rendered)
                    self.assertNotIn("run.sh", rendered)

    def test_input_drift_fails_incomplete_and_suppresses_plans(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        with mock.patch.object(doctor, "_verify_inputs", return_value=["TODO.md"]):
            report = repo.scan()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn("LTD-INPUT-CHANGED", rules(report))
        self.assertEqual(report["plans"], [])

    def test_missing_input_error_is_root_independent(self):
        reports = []
        for _index in range(2):
            repo = FixtureRepository(CASES["clean"])
            try:
                (repo.root / "TODO.md").unlink()
                reports.append(doctor._canonical_json(repo.scan()))
                self.assertNotIn(str(repo.root), reports[-1])
            finally:
                repo.close()
        self.assertEqual(reports[0], reports[1])

    def test_multiline_probe_error_stays_one_summary_line(self):
        repo = FixtureRepository(CASES["marker-and-refs"])
        self.addCleanup(repo.close)
        failure = doctor.DoctorInputError(
            "LTD-GIT-PROBE",
            ".git",
            "line one\nline two\nline three",
        )
        with mock.patch.object(doctor, "_git_reachable_commits", side_effect=failure):
            report = doctor.scan_repository(repo.root)
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertEqual(len(report["summary"]), 1)
        self.assertNotIn("\n", report["summary"][0])

    def test_reachability_ref_change_makes_scan_incomplete(self):
        repo = FixtureRepository(CASES["marker-and-refs"])
        self.addCleanup(repo.close)
        with mock.patch.object(
            doctor,
            "_git_reachable_commits",
            side_effect=[{"a" * 40}, {"a" * 40, "b" * 40}],
        ):
            report = doctor.scan_repository(repo.root)
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn("LTD-INPUT-CHANGED", rules(report))
        self.assertEqual(report["plans"], [])


class LegacyTaskDoctorReadOnlyTests(unittest.TestCase):
    def test_api_scan_preserves_every_fixture_byte_mode_and_type(self):
        for name, case in sorted(CASES.items()):
            with self.subTest(case=name):
                repo = FixtureRepository(case)
                try:
                    before = snapshot_tree(repo.root)
                    repo.scan()
                    after = snapshot_tree(repo.root)
                finally:
                    repo.close()
                self.assertEqual(after, before)

    def test_clean_cli_emits_only_json_and_preserves_tree(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        before = snapshot_tree(repo.root)
        completed = subprocess.run(
            [sys.executable, str(TOOLS / "legacy_task_doctor.py"), "--root", str(repo.root), "--json"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        after = snapshot_tree(repo.root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["verdict"], "CLEAN")
        self.assertEqual(completed.stderr, "")
        self.assertEqual(after, before)

    def test_finding_cli_human_summary_is_at_most_ten_lines(self):
        repo = FixtureRepository(CASES["bootstrap-policy"])
        self.addCleanup(repo.close)
        before = snapshot_tree(repo.root)
        completed = subprocess.run(
            [sys.executable, str(TOOLS / "legacy_task_doctor.py"), "--root", str(repo.root)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        after = snapshot_tree(repo.root)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(after, before)
        lines = completed.stdout.splitlines()
        self.assertLessEqual(len(lines), 10)
        self.assertTrue(lines[0].startswith("legacy-task-doctor FINDINGS:"))
        self.assertEqual(completed.stderr, "")

    def test_production_module_has_no_file_mutation_api(self):
        source = (TOOLS / "legacy_task_doctor.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"write_text", "write_bytes", "unlink", "rename", "replace", "mkdir", "rmdir", "touch"}
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        self.assertEqual(forbidden & used, set())
        self.assertNotIn("shell=True", source)

    def test_git_probe_is_one_fixed_read_only_argv(self):
        completed = subprocess.CompletedProcess(
            ["git"], 0, stdout=b"a" * 40 + b"\n", stderr=b""
        )
        with mock.patch.object(doctor.subprocess, "run", return_value=completed) as run:
            observed = doctor._git_reachable_commits(Path("."))
        self.assertEqual(observed, {"a" * 40})
        argv = run.call_args.args[0]
        self.assertEqual(argv, ["git", "--no-optional-locks", "rev-list", "--all"])
        self.assertNotIn("run.sh", " ".join(argv))
        self.assertFalse(run.call_args.kwargs.get("shell", False))


class LegacyTaskDoctorFocusedBehaviorTests(unittest.TestCase):
    def make_repo(self, todo, done="# DONE — Completed Features\n", extra=None, reachable=None):
        case = {
            "files": {"TODO.md": todo, "DONE.md": done, **(extra or {})},
            "reachable_commits": list(reachable or []),
        }
        repo = FixtureRepository(case)
        self.addCleanup(repo.close)
        return repo

    def test_missing_required_input_is_incomplete(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        (repo.root / "TODO.md").unlink()
        report = repo.scan()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn("LTD-INPUT-MISSING", rules(report))

    def test_symlink_claim_is_rejected_without_following_it(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        target = repo.root / "outside.md"
        target.write_text("secret", encoding="utf-8")
        symlink = repo.root / "TODO-fixture-1000-02-symlink.md"
        try:
            symlink.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        report = repo.scan()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn("LTD-INPUT-NONREGULAR", rules(report))

    def test_invalid_workflow_fields_are_reported(self):
        invalid = json.dumps(
            {
                "schema": "wrong",
                "workflow_version": "v1",
                "authority_epoch": "issue-store-writable",
                "authority_profile": "legacy-lists",
                "write_phase": "legacy-writable",
                "required_capability": "unknown",
                "runner_protocol": "wrong",
                "selector_digest": "bad",
                "instruction_bundle": "elsewhere.md",
                "extra": True,
            }
        ) + "\n"
        repo = self.make_repo(
            "# TODO\n\n## Feature: 1000 — Invalid selector\n- [ ] **1000-01** Open.\n",
            extra={"agent-workflow.json": invalid},
        )
        report = repo.scan()
        self.assertIn("LTD-BOOT-INVALID", rules(report))
        self.assertIn("LTD-BOOT-UNKNOWN-FIELD", rules(report))
        self.assertIn("LTD-BOOT-CROSS-FIELD", rules(report))

    def test_duplicate_task_across_todo_and_done_is_reported(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Open\n- [ ] **1000-01** Open.\n",
            done=f"# DONE\n\n## Feature: 0999 — Done\nCompleted: now — REF: {ref_value}\n- [x] **1000-01** Duplicate. REF: {ref_value}\n",
            reachable={ref_value},
        )
        self.assertIn("LTD-ID-DUPLICATE", rules(repo.scan()))

    def test_reachable_full_reference_is_accepted(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Refs\n- [x] **1000-01** Done. REF: {ref_value}\n",
            reachable={ref_value},
        )
        observed = rules(repo.scan())
        self.assertNotIn("LTD-REF-MALFORMED", observed)
        self.assertNotIn("LTD-REF-UNREACHABLE", observed)
        self.assertNotIn("LTD-REF-MISSING", observed)

    def test_feature_with_terminal_direct_tasks_is_closure_eligible(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Ready\n- [x] **1000-01** Done. REF: {ref_value}\n- [w] **1000-02** Closed. REF: {ref_value}\n  - **Reason:** fixture\n",
            reachable={ref_value},
        )
        self.assertIn("LTD-FEATURE-CLOSURE-ELIGIBLE", rules(repo.scan()))

    def test_parent_is_not_eligible_when_one_child_is_nonterminal(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Parent\n- [ ] **1000-01** Parent.\n- [x] **1000-01.01** Done. REF: {ref_value}\n- [ ] **1000-01.02** Open.\n",
            reachable={ref_value},
        )
        findings = [item for item in repo.scan()["findings"] if item["rule"] == "LTD-PARENT-CLOSURE-ELIGIBLE"]
        self.assertEqual(findings, [])

    def test_deferred_task_is_flagged_once_its_prerequisites_are_terminal(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Deferred\n- [x] **1000-01** Predecessor. REF: {ref_value}\n- [d] **1000-02** PREREQ: 1000-02:1000-01 Deferred successor.\n",
            reachable={ref_value},
        )
        self.assertIn("LTD-DEFERRED-STALE", rules(repo.scan()))

    def test_deferred_task_with_a_live_blocker_is_not_flagged(self):
        repo = self.make_repo(
            "# TODO\n\n## Feature: 1000 — Deferred\n- [ ] **1000-01** Predecessor.\n- [d] **1000-02** PREREQ: 1000-02:1000-01 Deferred successor.\n",
        )
        observed = rules(repo.scan())
        self.assertNotIn("LTD-DEFERRED-STALE", observed)
        self.assertNotIn("LTD-DEFERRED-UNVERIFIABLE", observed)

    def test_deferred_task_without_an_explicit_prerequisite_is_unverifiable(self):
        repo = self.make_repo(
            "# TODO\n\n## Feature: 1000 — Deferred\n- [d] **1000-01** Deferred with no recorded blocker.\n",
        )
        observed = rules(repo.scan())
        self.assertIn("LTD-DEFERRED-UNVERIFIABLE", observed)
        self.assertNotIn("LTD-DEFERRED-STALE", observed)

    def test_identity_parser_ignores_request_history_fields(self):
        clean = CASES["clean"]
        repo = FixtureRepository(clean)
        self.addCleanup(repo.close)
        claim = repo.root / "TODO-fixture-1000-01-clean-claim.md"
        claim.write_text(
            claim.read_text(encoding="utf-8")
            + "\n## Runner history\n\nrequest_id: later-request\nbase_commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
            encoding="utf-8",
        )
        report = repo.scan()
        observed = rules(report)
        self.assertNotIn("LTD-CLAIM-FIELD-DUPLICATE", observed)
        self.assertNotIn("LTD-CLAIM-IDENTITY-MISMATCH", observed)

    def test_legacy_backticked_identity_field_is_visible(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        claim = repo.root / "TODO-fixture-1000-01-clean-claim.md"
        text = claim.read_text(encoding="utf-8").replace(
            "owner_token: agent:fixture:1000-01:clean-claim",
            "- `owner_token`: agent:fixture:1000-01:clean-claim",
        )
        claim.write_text(text, encoding="utf-8")
        report = repo.scan()
        self.assertIn("LTD-CLAIM-FIELD-NONCANONICAL", rules(report))

    def test_orphan_active_claim_never_produces_clean(self):
        repo = FixtureRepository(CASES["claim-drift"])
        self.addCleanup(repo.close)
        report = repo.scan()
        orphan = [
            finding
            for finding in report["findings"]
            if finding["rule"] == "LTD-CLAIM-TASK-MISSING"
        ]
        self.assertEqual([finding["subject"] for finding in orphan], ["1000-99"])

    def test_only_open_unclaimed_parents_receive_closure_pickup_advice(self):
        ref_value = "a" * 40
        todo = f"""# TODO

## Feature: 1000 — Parent states
- [p] **1000-01** In progress parent.
- [x] **1000-01.01** Done. REF: {ref_value}
- [u] **1000-02** Human-gated parent.
- [x] **1000-02.01** Done. REF: {ref_value}
- [?] **1000-03** Unknown parent.
- [x] **1000-03.01** Done. REF: {ref_value}
"""
        repo = self.make_repo(todo, reachable={ref_value})
        report = repo.scan()
        eligible = [
            finding["subject"]
            for finding in report["findings"]
            if finding["rule"] == "LTD-PARENT-CLOSURE-ELIGIBLE"
        ]
        self.assertEqual(eligible, [])
        self.assertFalse(
            any(
                plan["action"] == "claim-and-perform-package-closure"
                for plan in report["plans"]
            )
        )

    def test_integration_readiness_not_ready_reports_nonterminal_task(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Not ready\n- [x] **1000-01** Done. REF: {ref_value}\n- [ ] **1000-02** Open.\n",
            reachable={ref_value},
        )
        report = repo.scan()
        self.assertNotIn("LTD-FEATURE-INTEGRATION-READY", rules(report))
        entries = {item["feature"]: item for item in report["integration_readiness"]}
        self.assertIn("1000", entries)
        entry = entries["1000"]
        self.assertFalse(entry["ready"])
        self.assertEqual(entry["nonterminal_tasks"], ["1000-02"])
        self.assertEqual(entry["nonterminal_prerequisites"], [])
        self.assertEqual(entry["unaccepted_checkpoints"], [])
        self.assertEqual(entry["in_scope_tasks"], ["1000-01", "1000-02"])

    def test_integration_readiness_ready_linear_chain_emits_notice(self):
        ref_a = "a" * 40
        ref_b = "b" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Ready linear\n"
            f"- [x] **1000-01** First. REF: {ref_a}\n"
            f"- [x] **1000-02** PREREQ: 1000-02:1000-01 Second. REF: {ref_b}\n",
            reachable={ref_a, ref_b},
        )
        report = repo.scan()
        self.assertIn("LTD-FEATURE-INTEGRATION-READY", rules(report))
        notice = next(
            finding
            for finding in report["findings"]
            if finding["rule"] == "LTD-FEATURE-INTEGRATION-READY"
        )
        self.assertEqual(notice["subject"], "1000")
        self.assertIn("privileged integrator", notice["message"])
        self.assertIn("1000", notice["message"])
        plan = next(
            plan
            for plan in report["plans"]
            if plan["rule"] == "LTD-FEATURE-INTEGRATION-READY"
        )
        self.assertEqual(plan["action"], "assign-privileged-integrator")
        self.assertEqual(plan["required_actor"], "privileged-integrator")
        self.assertFalse(plan["automatic"])
        self.assertFalse(plan["destructive"])
        entries = {item["feature"]: item for item in report["integration_readiness"]}
        self.assertTrue(entries["1000"]["ready"])

    def test_integration_readiness_ready_parallel_subtasks_includes_subtask_scope(self):
        ref_a, ref_b, ref_c = "a" * 40, "b" * 40, "c" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Ready parallel\n"
            f"- [x] **1000-01** Parent. REF: {ref_a}\n"
            f"- [x] **1000-01.01** Child one. REF: {ref_b}\n"
            f"- [x] **1000-01.02** Child two. REF: {ref_c}\n",
            reachable={ref_a, ref_b, ref_c},
        )
        report = repo.scan()
        self.assertIn("LTD-FEATURE-INTEGRATION-READY", rules(report))
        entries = {item["feature"]: item for item in report["integration_readiness"]}
        entry = entries["1000"]
        self.assertTrue(entry["ready"])
        self.assertEqual(entry["in_scope_tasks"], ["1000-01", "1000-01.01", "1000-01.02"])

    def test_integration_readiness_blocked_by_unaccepted_mandatory_checkpoint(self):
        ref_a = "a" * 40
        ref_b = "b" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Blocked\n"
            f"- [x] **1000-01** Checkpoint. REF: {ref_a}\n"
            "  - **Integration review:** mandatory. **Rationale (architect):** fixture.\n"
            f"- [x] **1000-02** PREREQ: 1000-02:1000-01 Dependent. REF: {ref_b}\n",
            reachable={ref_a, ref_b},
        )
        report = repo.scan()
        self.assertNotIn("LTD-FEATURE-INTEGRATION-READY", rules(report))
        entries = {item["feature"]: item for item in report["integration_readiness"]}
        entry = entries["1000"]
        self.assertFalse(entry["ready"])
        self.assertEqual(entry["unaccepted_checkpoints"], ["1000-01"])
        self.assertEqual(entry["nonterminal_tasks"], [])

    def test_integration_readiness_accepted_mandatory_checkpoint_is_ready(self):
        ref_a = "a" * 40
        ref_b = "b" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Accepted checkpoint\n"
            f"- [x] **1000-01** Checkpoint. REF: {ref_a}\n"
            "  - **Integration review:** mandatory. **Rationale (architect):** fixture.\n"
            "  - **Acceptance:** ✓ reviewed by fixture-integrator on 2026-08-20T00:00:00Z.\n"
            f"- [x] **1000-02** PREREQ: 1000-02:1000-01 Dependent. REF: {ref_b}\n",
            reachable={ref_a, ref_b},
        )
        report = repo.scan()
        self.assertIn("LTD-FEATURE-INTEGRATION-READY", rules(report))
        entries = {item["feature"]: item for item in report["integration_readiness"]}
        entry = entries["1000"]
        self.assertTrue(entry["ready"])
        self.assertEqual(entry["unaccepted_checkpoints"], [])

    def test_integration_readiness_ignores_done_features_and_empty_scope(self):
        repo = self.make_repo(
            "# TODO\n\n## Feature: 1000 — No tasks yet\n",
            done="# DONE\n\n## Feature: 0999 — Historical\nCompleted: now — REF: " + "a" * 40 + "\n- [x] **0999-01** Done. REF: " + "a" * 40 + "\n",
            reachable={"a" * 40},
        )
        report = repo.scan()
        self.assertEqual(report["integration_readiness"], [])

    def test_checkpoint_well_formed_produces_no_findings_and_exposes_both_polarities(self):
        repo = FixtureRepository(CASES["checkpoint-well-formed"])
        self.addCleanup(repo.close)
        report = repo.scan()
        self.assertNotIn("LTD-CHECKPOINT-MISSING-AUTHORITY", rules(report))
        self.assertNotIn("LTD-CHECKPOINT-MALFORMED", rules(report))
        self.assertNotIn("LTD-CHECKPOINT-UNFLAGGED-HIGH-RISK", rules(report))
        states = {item["task"]: item for item in report["checkpoint_states"]}
        self.assertEqual(states["1000-01"]["attribute"], "mandatory")
        self.assertTrue(states["1000-01"]["architect_tagged"])
        self.assertEqual(states["1000-01"]["marker"], "x")
        self.assertEqual(states["1000-01"]["required_integration_state"], "pending")
        self.assertEqual(states["1000-02"]["attribute"], "not-mandatory")
        self.assertTrue(states["1000-02"]["architect_tagged"])
        self.assertEqual(states["1000-02"]["required_integration_state"], "none")

    def test_checkpoint_missing_architect_tag_is_flagged(self):
        repo = FixtureRepository(CASES["checkpoint-missing-authority"])
        self.addCleanup(repo.close)
        report = repo.scan()
        self.assertIn("LTD-CHECKPOINT-MISSING-AUTHORITY", rules(report))
        states = {item["task"]: item for item in report["checkpoint_states"]}
        self.assertEqual(states["1000-01"]["attribute"], "mandatory")
        self.assertFalse(states["1000-01"]["architect_tagged"])
        self.assertTrue(states["1000-01"]["rationale_present"])

    def test_checkpoint_unflagged_high_risk_node_is_flagged(self):
        repo = FixtureRepository(CASES["checkpoint-unflagged-high-risk"])
        self.addCleanup(repo.close)
        report = repo.scan()
        self.assertIn("LTD-CHECKPOINT-UNFLAGGED-HIGH-RISK", rules(report))
        states = {item["task"]: item for item in report["checkpoint_states"]}
        self.assertIsNone(states["1000-01"]["attribute"])
        self.assertTrue(states["1000-01"]["high_risk_unflagged"])
        self.assertEqual(states["1000-01"]["required_integration_state"], "none")

    def test_checkpoint_malformed_polarity_is_flagged_and_treated_as_pending(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Malformed checkpoint\n"
            f"- [x] **1000-01** Checkpoint task. REF: {ref_value}\n"
            "  - **Integration review:** unclear. **Rationale (architect):** ambiguous polarity fixture.\n",
            reachable={ref_value},
        )
        report = repo.scan()
        self.assertIn("LTD-CHECKPOINT-MALFORMED", rules(report))
        states = {item["task"]: item for item in report["checkpoint_states"]}
        self.assertEqual(states["1000-01"]["attribute"], "malformed")
        self.assertEqual(states["1000-01"]["required_integration_state"], "pending")

    def test_checkpoint_accepted_mandatory_node_reports_passed(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Accepted checkpoint state\n"
            f"- [x] **1000-01** Checkpoint task. REF: {ref_value}\n"
            "  - **Integration review:** mandatory. **Rationale (architect):** fixture.\n"
            "  - **Acceptance:** ✓ reviewed by fixture-integrator on 2026-08-20T00:00:00Z.\n",
            reachable={ref_value},
        )
        report = repo.scan()
        self.assertEqual(rules(report), {"LTD-FEATURE-CLOSURE-ELIGIBLE", "LTD-FEATURE-INTEGRATION-READY"})
        states = {item["task"]: item for item in report["checkpoint_states"]}
        self.assertEqual(states["1000-01"]["required_integration_state"], "passed")

    def test_checkpoint_states_cover_subtasks_too(self):
        ref_value = "a" * 40
        repo = self.make_repo(
            f"# TODO\n\n## Feature: 1000 — Subtask checkpoint\n"
            f"- [x] **1000-01** Parent. REF: {ref_value}\n"
            f"- [x] **1000-01.01** Child checkpoint. REF: {ref_value}\n"
            "  - **Integration review:** mandatory. **Rationale (architect):** fixture subtask checkpoint.\n",
            reachable={ref_value},
        )
        report = repo.scan()
        states = {item["task"]: item for item in report["checkpoint_states"]}
        self.assertIn("1000-01.01", states)
        self.assertEqual(states["1000-01.01"]["attribute"], "mandatory")

    def test_feature_and_partial_task_prerequisite_grammar_is_strict(self):
        repo = FixtureRepository(CASES["prerequisites-and-parent"])
        self.addCleanup(repo.close)
        report = repo.scan()
        malformed = [
            finding
            for finding in report["findings"]
            if finding["rule"] == "LTD-PREREQ-MALFORMED"
        ]
        self.assertGreaterEqual(len(malformed), 4)
        self.assertTrue(
            any(
                finding["subject"] == "1000-09"
                and "comma-separated" in finding["message"]
                for finding in malformed
            )
        )
        edges = {
            (edge["dependent"], edge["prerequisite"])
            for edge in report["normalized"]["prerequisites"]
        }
        self.assertIn(("1000-09", "1000-02"), edges)
        lhs_subjects = {
            finding["subject"]
            for finding in report["findings"]
            if finding["rule"] == "LTD-PREREQ-LHS"
        }
        self.assertTrue({"1000", "1000-04"}.issubset(lhs_subjects))

    def test_multiline_comment_ref_is_hidden_and_cannot_close_task(self):
        repo = FixtureRepository(CASES["marker-and-refs"])
        self.addCleanup(repo.close)
        report = repo.scan()
        refs = [
            ref
            for ref in report["normalized"]["refs"]
            if ref["subject_id"] == "1000-07"
        ]
        self.assertEqual([ref["visibility"] for ref in refs], ["hidden"])
        findings = {
            finding["rule"]
            for finding in report["findings"]
            if finding["subject"] == "1000-07"
        }
        self.assertEqual(findings, {"LTD-REF-HIDDEN", "LTD-REF-MISSING"})

    def test_claim_filename_agent_component_must_match_exactly(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        old = repo.root / "TODO-fixture-1000-01-clean-claim.md"
        new = repo.root / "TODO-other-1000-01-clean-claim.md"
        old.rename(new)
        todo = repo.root / "TODO.md"
        todo.write_text(
            todo.read_text(encoding="utf-8").replace(old.name, new.name),
            encoding="utf-8",
        )
        report = repo.scan()
        self.assertIn("LTD-CLAIM-IDENTITY-MISMATCH", rules(report))

    def test_unsafe_scope_is_not_accepted_as_exact(self):
        repo = FixtureRepository(CASES["claim-drift"])
        self.addCleanup(repo.close)
        report = repo.scan()
        invalid = [
            finding
            for finding in report["findings"]
            if finding["rule"] == "LTD-CLAIM-SCOPE-INVALID"
        ]
        self.assertEqual(len(invalid), 1)
        self.assertIn("../outside.py", invalid[0]["message"])

    def test_instruction_markdown_target_must_be_in_root_regular_file(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        agents = repo.root / "AGENTS.md"
        agents.write_text("# Agents\n\nSee [bad](docs/bad.md).\n", encoding="utf-8")
        bad = repo.root / "docs" / "bad.md"
        bad.mkdir(parents=True)
        self.assertIn("LTD-INSTRUCTION-LINK-MISSING", rules(repo.scan()))
        bad.rmdir()
        try:
            bad.symlink_to(repo.root / "SANDBOX.md")
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        self.assertIn("LTD-INSTRUCTION-LINK-MISSING", rules(repo.scan()))
        bad.unlink()
        real = repo.root / "docs" / "real"
        real.mkdir()
        (real / "policy.md").write_text("# Policy\n", encoding="utf-8")
        intermediate = repo.root / "docs" / "external"
        intermediate.symlink_to(real, target_is_directory=True)
        agents.write_text(
            "# Agents\n\nSee [bad](docs/external/policy.md).\n",
            encoding="utf-8",
        )
        self.assertIn("LTD-INSTRUCTION-LINK-MISSING", rules(repo.scan()))

    def test_malformed_task_and_feature_headers_are_not_silent_legacy_entries(self):
        repo = self.make_repo(
            "# TODO\n\n## Feature: 100 — Bad feature\n- [ ] **1000-1** Bad Task.\n"
        )
        observed = rules(repo.scan())
        self.assertIn("LTD-FEATURE-HEADER-MALFORMED", observed)
        self.assertIn("LTD-TASK-HEADER-MALFORMED", observed)

    def test_next_step_must_be_final_and_not_placeholder(self):
        for replacement in (
            "## Next step\n\nTBD.\n",
            "## Next step\n\nImplement.\n\n## Progress\n\nNot final.\n",
        ):
            with self.subTest(replacement=replacement):
                repo = FixtureRepository(CASES["clean"])
                try:
                    claim = repo.root / "TODO-fixture-1000-01-clean-claim.md"
                    text = claim.read_text(encoding="utf-8")
                    text = re.sub(r"## Next step[\s\S]*$", replacement, text)
                    claim.write_text(text, encoding="utf-8")
                    self.assertIn("LTD-CLAIM-NEXT-STEP-MISSING", rules(repo.scan()))
                finally:
                    repo.close()

    def test_duplicate_bootstrap_json_keys_fail_closed(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        workflow = repo.root / "agent-workflow.json"
        text = workflow.read_text(encoding="utf-8")
        workflow.write_text(
            text.replace(
                '{"schema":',
                '{"schema":"duplicate","schema":',
                1,
            ),
            encoding="utf-8",
        )
        report = repo.scan()
        self.assertIn("LTD-BOOT-INVALID", rules(report))
        self.assertTrue(
            any("duplicate JSON key" in finding["message"] for finding in report["findings"])
        )

    def test_report_schema_and_normalized_inventory_are_closed_surfaces(self):
        repo = FixtureRepository(CASES["clean"])
        self.addCleanup(repo.close)
        report = repo.scan()
        self.assertEqual(report["schema"], "legacy-task-doctor-report@v1")
        self.assertEqual(
            set(report),
            {
                "schema",
                "verdict",
                "inputs",
                "authority",
                "inventory",
                "normalized",
                "counts",
                "findings",
                "plans",
                "integration_readiness",
                "checkpoint_states",
                "summary",
            },
        )
        self.assertEqual(
            set(report["normalized"]),
            {"features", "tasks", "legacy_entries", "claims", "refs", "prerequisites"},
        )


if __name__ == "__main__":
    unittest.main()
