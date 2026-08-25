import contextlib
import datetime
import io
import json
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURES = ROOT / "_src" / "tests" / "fixtures" / "automation_safety"
sys.path.insert(0, str(TOOLS))

import automation_safety as safety  # noqa: E402
import build_report  # noqa: E402
import link_verification_evidence as link_evidence  # noqa: E402

# The campaign report path under test does not use PDF discovery.  Keep this
# focused test isolated from concurrent spec_scrape work and its optional
# upstream modules by providing only the import-time attributes it requires.
_previous_spec_scrape = sys.modules.get("spec_scrape")
_spec_scrape_stub = types.ModuleType("spec_scrape")
_spec_scrape_stub.PDF_CACHE = ROOT / "_src" / "spec" / "pdf"
_spec_scrape_stub.RS_DOCS = {}
_spec_scrape_stub.discover_pdfs = lambda *args, **kwargs: []
sys.modules["spec_scrape"] = _spec_scrape_stub
try:
    import spec_extraction_campaign  # noqa: E402
finally:
    if _previous_spec_scrape is None:
        sys.modules.pop("spec_scrape", None)
    else:
        sys.modules["spec_scrape"] = _previous_spec_scrape


class AutomationSafetyFixtureTests(unittest.TestCase):
    # DEC-0038-002 and the independent 0038-33 Architect scope review permit
    # only these five existing AUTO010 identities.  Equality is deliberate:
    # any sixth, moved, renamed, or byte-changed finding requires re-review.
    RUNNER_TRANSACTION_ALLOWED_AUTO010 = frozenset(
        {
            (
                277,
                "_atomic_create",
                "a9585e4f1caf3113aa8a1da53260983471d1e10d5339b4a553f0fcce7a047ea2",
            ),
            (
                1735,
                "Transaction.acquire_lock",
                "bbeb1bc976b167dc0d4939d3788858124cb8cfecdc064b4c6bac40cc1f290fd8",
            ),
            (
                1876,
                "Transaction.materialize_editor_candidate",
                "2027934680f43f964b21625c17ce86672422e5584efeaa904d49a4d17baa8d3c",
            ),
            (
                3332,
                "BranchMergeTransaction._synchronize_worktree",
                "2027934680f43f964b21625c17ce86672422e5584efeaa904d49a4d17baa8d3c",
            ),
            (
                3959,
                "_recovery_lease",
                "d9bae0d944b115d54df1aa8eb1b10f982d72c3427965fb54b216068970284802",
            ),
        }
    )

    def scan(self, name, language):
        path = FIXTURES / name
        return safety.scan_text(name, path.read_text(encoding="utf-8"), language)

    def rules(self, name, language):
        return {finding.rule for finding in self.scan(name, language)}

    def runner_transaction_findings(self):
        relative = "_src/tools/runner_transaction.py"
        text = (ROOT / relative).read_text(encoding="utf-8")
        return safety.scan_text(relative, text, "python")

    def assert_runner_transaction_control(self, findings):
        unconditionally_forbidden = {"AUTO001", "AUTO002", "AUTO009"}
        observed_rules = {finding.rule for finding in findings}
        self.assertTrue(
            unconditionally_forbidden.isdisjoint(observed_rules),
            sorted(observed_rules & unconditionally_forbidden),
        )
        observed_auto010 = {
            (finding.line, finding.symbol, finding.evidence_sha256)
            for finding in findings
            if finding.rule == "AUTO010"
        }
        self.assertEqual(self.RUNNER_TRANSACTION_ALLOWED_AUTO010, observed_auto010)

    def test_link_verification_fixture_freezes_false_green_and_wildcard_commit(self):
        rules = self.rules("link_verification_evidence.py.fixture", "python")
        self.assertTrue({"AUTO001", "AUTO002", "AUTO003", "AUTO009"}.issubset(rules))

    def test_publish_fixture_freezes_identity_and_protected_force_push(self):
        rules = self.rules("publish_public_site.sh.fixture", "shell")
        self.assertTrue({"AUTO004", "AUTO005"}.issubset(rules))

    def test_old_runner_fixture_freezes_wildcard_closure_without_recovery(self):
        rules = self.rules("old_runner_envelope.sh.fixture", "shell")
        self.assertTrue({"AUTO003", "AUTO010"}.issubset(rules))

    def test_mutation_before_gate_fixture_is_critical(self):
        findings = self.scan("mutation_before_gate.sh.fixture", "shell")
        match = [finding for finding in findings if finding.rule == "AUTO008"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_shell_execution_fixture_is_detected(self):
        self.assertIn("AUTO006", self.rules("shell_exec.py.fixture", "python"))

    def test_validation_repair_fixture_is_detected(self):
        self.assertIn("AUTO007", self.rules("validation_repair.py.fixture", "python"))

    def test_checked_read_only_wrapper_is_not_unchecked_mutation(self):
        rules = self.rules("safe_checked_wrapper.py.fixture", "python")
        self.assertNotIn("AUTO001", rules)
        self.assertNotIn("AUTO009", rules)

    def test_per_item_continuation_with_aggregate_nonzero_is_not_false_success(self):
        rules = self.rules("safe_per_item.py.fixture", "python")
        self.assertNotIn("AUTO001", rules)
        self.assertNotIn("AUTO002", rules)

    def test_logging_returncode_without_propagation_is_still_unchecked(self):
        text = """import subprocess

def publish():
    result = subprocess.run([\"git\", \"commit\", \"-m\", \"unsafe\"])
    print(result.returncode)
    return 0
"""
        rules = {finding.rule for finding in safety.scan_text("logged.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO009"}.issubset(rules))

    def test_variable_argv_is_resolved_before_mutation_classification(self):
        text = """import subprocess

def publish():
    command = [\"git\", \"commit\", \"-m\", \"unsafe\"]
    subprocess.run(command)
    return 0
"""
        rules = {finding.rule for finding in safety.scan_text("variable.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO009"}.issubset(rules))

    def test_subprocess_callable_assignment_alias_preserves_command_rules(self):
        text = """import subprocess

execute = subprocess.run

def publish():
    execute([\"git\", \"push\", \"--force\", \"origin\", \"HEAD:refs/heads/main\"], check=True)
"""
        rules = {finding.rule for finding in safety.scan_text("callable_alias.py", text, "python")}
        self.assertTrue({"AUTO004", "AUTO005", "AUTO010"}.issubset(rules))

    def test_subprocess_import_aliases_preserve_command_rules(self):
        module_alias = """import subprocess as sp

def publish():
    sp.run([\"git\", \"push\", \"--force\", \"origin\", \"HEAD:refs/heads/main\"], check=True)
"""
        direct_alias = """from subprocess import run

def publish():
    run([\"git\", \"commit\", \"-m\", \"unsafe\"])
"""
        module_rules = {
            finding.rule for finding in safety.scan_text("module_alias.py", module_alias, "python")
        }
        direct_rules = {
            finding.rule for finding in safety.scan_text("direct_alias.py", direct_alias, "python")
        }
        self.assertTrue({"AUTO004", "AUTO005", "AUTO010"}.issubset(module_rules))
        self.assertTrue({"AUTO001", "AUTO009", "AUTO010"}.issubset(direct_rules))

    def test_conditional_safe_argv_cannot_hide_commit_variant(self):
        text = """import subprocess

def publish(use_status):
    command = [\"git\", \"commit\", \"-m\", \"unsafe\"]
    if use_status:
        command = [\"git\", \"status\", \"--short\"]
    subprocess.run(command)
"""
        rules = {finding.rule for finding in safety.scan_text("conditional.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO009", "AUTO010"}.issubset(rules))

    def test_python_env_prefix_preserves_publication_rules(self):
        text = """import subprocess

subprocess.run(["env", "git", "commit", "-m", "unsafe"])
print("PASS")
"""
        rules = {finding.rule for finding in safety.scan_text("env-prefix.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009", "AUTO010"}.issubset(rules))

    def test_python_env_split_string_preserves_quoted_publication_rules(self):
        text = """import subprocess

subprocess.run(["env", "-S", '\"/usr/bin/git\" commit -m unsafe'])
print("PASS")
"""
        rules = {finding.rule for finding in safety.scan_text("env-split.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009", "AUTO010"}.issubset(rules))

    def test_python_shell_argv_is_fail_closed_and_preserves_inner_publication(self):
        text = """import subprocess

subprocess.run(["sh", "-c", "git commit -m unsafe"])
print("PASS")
"""
        rules = {finding.rule for finding in safety.scan_text("shell-argv.py", text, "python")}
        self.assertTrue(
            {"AUTO001", "AUTO002", "AUTO006", "AUTO009", "AUTO010"}.issubset(rules)
        )

    def test_unknown_unchecked_argv_fails_closed_but_checked_argv_is_safe(self):
        unchecked = "import subprocess\nsubprocess.run(command)\n"
        checked = "import subprocess\nsubprocess.run(command, check=True)\n"
        self.assertIn(
            "AUTO001",
            {finding.rule for finding in safety.scan_text("unknown.py", unchecked, "python")},
        )
        self.assertNotIn(
            "AUTO001",
            {finding.rule for finding in safety.scan_text("checked_unknown.py", checked, "python")},
        )

    def test_conditional_nondominating_safe_assignment_stays_unknown(self):
        text = """import subprocess

def inspect(enabled):
    if enabled:
        command = [\"git\", \"status\", \"--short\"]
    subprocess.run(command)
"""
        self.assertIn(
            "AUTO001",
            {finding.rule for finding in safety.scan_text("nondominating.py", text, "python")},
        )

    def test_sys_exit_zero_does_not_count_as_failure_propagation(self):
        text = """import subprocess
import sys

def stage():
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    if result.returncode != 0:
        sys.exit(0)
"""
        self.assertIn("AUTO001", {finding.rule for finding in safety.scan_text("exit0.py", text, "python")})

    def test_reassigned_result_does_not_validate_an_earlier_subprocess(self):
        text = """import subprocess

def stage(other):
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    result = other
    if result.returncode != 0:
        raise RuntimeError(\"later object failed\")
"""
        self.assertIn("AUTO001", {finding.rule for finding in safety.scan_text("reassigned.py", text, "python")})

    def test_check_returncode_is_accepted_failure_propagation(self):
        text = """import subprocess

def stage():
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    result.check_returncode()
"""
        rules = {finding.rule for finding in safety.scan_text("checked.py", text, "python")}
        self.assertNotIn("AUTO001", rules)

    def test_raise_system_exit_zero_does_not_propagate_failure(self):
        text = """import subprocess

def stage():
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    if result.returncode != 0:
        raise SystemExit(0)
    return 0
"""
        rules = {finding.rule for finding in safety.scan_text("raise_exit0.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_nested_raise_does_not_prove_all_failure_paths_propagate(self):
        text = """import subprocess

def stage(raise_failure):
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    if result.returncode != 0:
        if raise_failure:
            raise RuntimeError(\"failed\")
    return 0
"""
        rules = {finding.rule for finding in safety.scan_text("nested.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_failure_collection_in_always_zero_expression_is_not_propagated(self):
        text = """import subprocess

def stage():
    failures = []
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    if result.returncode != 0:
        failures.append(\"add failed\")
    return 0 if failures else 0
"""
        rules = {finding.rule for finding in safety.scan_text("zero_aggregate.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_all_nested_failure_branches_are_accepted(self):
        text = """import subprocess

def stage(retryable):
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    if result.returncode != 0:
        if retryable:
            raise RuntimeError(\"retry\")
        else:
            return 1
    return 0
"""
        rules = {finding.rule for finding in safety.scan_text("all_branches.py", text, "python")}
        self.assertNotIn("AUTO001", rules)
        self.assertNotIn("AUTO002", rules)

    def test_conditional_result_check_does_not_dominate_failure_path(self):
        text = """import subprocess

def stage(report):
    result = subprocess.run([\"git\", \"add\", \"--\", \"exact.txt\"])
    if report and result.returncode != 0:
        raise RuntimeError(\"failed\")
    return 0
"""
        rules = {finding.rule for finding in safety.scan_text("conditional_check.py", text, "python")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_returned_completed_process_propagates_dynamic_outcome(self):
        text = """import subprocess

def run(argv):
    result = subprocess.run(argv)
    return result
"""
        self.assertNotIn(
            "AUTO001",
            {finding.rule for finding in safety.scan_text("wrapper.py", text, "python")},
        )

    def test_popen_wait_status_and_exception_propagate_dynamic_outcome(self):
        text = """import subprocess

def run(argv):
    process = subprocess.Popen(argv)
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, argv)
"""
        rules = {finding.rule for finding in safety.scan_text("popen.py", text, "python")}
        self.assertNotIn("AUTO001", rules)
        self.assertNotIn("AUTO002", rules)

    def test_ignored_validation_followed_by_pass_is_false_success(self):
        text = """import subprocess

def validate():
    subprocess.run([\"python3\", \"_src/validate.py\"])
    print(\"PASS\")
    return 0
"""
        self.assertIn("AUTO002", {finding.rule for finding in safety.scan_text("false.py", text, "python")})

    def test_recovery_comment_does_not_count_as_durable_state(self):
        text = """import shutil

def clean(path):
    # TODO: add a recovery journal later
    shutil.rmtree(path)
"""
        self.assertIn("AUTO010", {finding.rule for finding in safety.scan_text("cleanup.py", text, "python")})

    def test_unrelated_status_dict_and_write_are_not_durable_state(self):
        text = """import shutil

def clean(target, unrelated):
    note = {\"status\": \"ok\"}
    unrelated.write_text(str(note))
    shutil.rmtree(target)
"""
        self.assertIn("AUTO010", {finding.rule for finding in safety.scan_text("detached.py", text, "python")})

    def test_preoperation_status_for_other_commit_is_not_durable(self):
        text = """import subprocess

def publish(result_path):
    result_path.write_text(\"status=published commit=other\")
    subprocess.run([\"git\", \"commit\", \"-m\", \"current\"], check=True)
"""
        findings = safety.scan_text("preoperation.py", text, "python")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_postoperation_status_for_other_commit_is_not_durable(self):
        text = """import subprocess

def publish(result_path):
    subprocess.run([\"git\", \"commit\", \"-m\", \"current\"], check=True)
    result_path.write_text(\"status=published commit=other\")
"""
        findings = safety.scan_text("postoperation.py", text, "python")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_status_named_write_without_operation_content_is_not_durable(self):
        text = """import shutil

def clean(target, status_path):
    status_path.write_text(\"unrelated\")
    shutil.rmtree(target)
"""
        self.assertIn("AUTO010", {finding.rule for finding in safety.scan_text("named.py", text, "python")})

    def test_structured_operation_linked_outcome_is_durable(self):
        text = """import json
import shutil


def clean(target, status_path):
    shutil.rmtree(target)
    status_path.write_text(json.dumps({"status": "deleted", "target": str(target)}))
"""
        self.assertNotIn(
            "AUTO010",
            {finding.rule for finding in safety.scan_text("linked.py", text, "python")},
        )

    def test_every_missing_python_durable_outcome_has_its_own_identity(self):
        text = """import subprocess


def publish():
    subprocess.run(["git", "commit", "-m", "first"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)
"""
        findings = [
            finding for finding in safety.scan_text("two-publications.py", text, "python")
            if finding.rule == "AUTO010"
        ]
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(finding.severity == "critical" for finding in findings))
        self.assertEqual(len({finding.evidence_sha256 for finding in findings}), 2)

    def test_underscore_recovery_scope_cannot_hide_critical_publication(self):
        text = """import shutil
import subprocess


def _clean(target):
    shutil.rmtree(target)


def _publish():
    subprocess.run(["git", "commit", "-m", "current"], check=True)
"""
        findings = [
            finding for finding in safety.scan_text("private-helpers.py", text, "python")
            if finding.rule == "AUTO010"
        ]
        self.assertTrue(any(finding.severity == "critical" for finding in findings))
        self.assertTrue(any("git" in finding.evidence for finding in findings))

    def test_conditional_python_outcome_does_not_postdominate_mutation(self):
        text = """import shutil


def clean(target, record, status_path):
    shutil.rmtree(target)
    if record:
        status_path.write_text(f"status=deleted target={target}")
"""
        self.assertIn(
            "AUTO010",
            {finding.rule for finding in safety.scan_text("conditional-state.py", text, "python")},
        )

    def test_terminating_python_call_prevents_unreachable_durable_outcome(self):
        text = """import subprocess
import sys


def publish(status_path):
    subprocess.run(["git", "commit", "-m", "current"], check=True)
    sys.exit(0)
    status_path.write_text("status=published commit=current")
"""
        findings = [
            finding for finding in safety.scan_text("terminated.py", text, "python")
            if finding.rule == "AUTO010"
        ]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "critical")

    def test_generator_suspension_prevents_python_durable_outcome(self):
        text = """import subprocess


def publish(status_path):
    subprocess.run(["git", "commit", "-m", "current"], check=True)
    yield
    status_path.write_text("status=published commit=current")
"""
        self.assertIn(
            "AUTO010",
            {finding.rule for finding in safety.scan_text("suspended.py", text, "python")},
        )

    def test_comprehension_writer_is_not_a_guaranteed_python_outcome(self):
        text = """import shutil


def clean(target, status_path, records):
    shutil.rmtree(target)
    [status_path.write_text(f"status=deleted target={target}") for record in records]
"""
        self.assertIn(
            "AUTO010",
            {finding.rule for finding in safety.scan_text("comprehension.py", text, "python")},
        )

    def test_conditional_shell_outcome_does_not_postdominate_mutation(self):
        text = """rm -rf "$TARGET"
if record; then
  printf 'status=deleted target=%s\\n' "$TARGET" > result.log
fi
"""
        self.assertIn(
            "AUTO010",
            {finding.rule for finding in safety.scan_text("conditional-state.sh", text, "shell")},
        )

    def test_same_line_shell_exit_prevents_durable_outcome(self):
        text = """set -e
git commit -m current; exit 0; printf 'status=published commit=current\\n' > result.log
"""
        findings = [
            finding for finding in safety.scan_text("early-exit-state.sh", text, "shell")
            if finding.rule == "AUTO010"
        ]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "critical")

    def test_shell_function_mutator_vocabulary_is_fail_closed(self):
        commands = (
            "chmod 600 target", "chown user target", "cp source target", "install source target",
            "ln source target", "mkdir target", "mv source target", "rm -f target",
            "sed -i backup target", "sed -E -i.bak 's/x/y/' target", "tee target",
            "touch target", "truncate -s 0 target", "/bin/cp source target",
            '"cp" source target', 'command "/bin/rm" -f target',
        )
        for command in commands:
            with self.subTest(command=command):
                text = "set -e\nmutate() {\n  %s\n}\nprintf 'PASS\\n'\n" % command
                rules = {finding.rule for finding in safety.scan_text("mutator.sh", text, "shell")}
                self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules), command)

    def test_shell_aggregate_evidence_binds_every_unchecked_mutation(self):
        original = "mutate() {\n  cp first second\n}\n"
        changed = "mutate() {\n  cp first second\n  :; \"touch\" additional\n}\n"
        first = next(
            finding for finding in safety.scan_text("aggregate.sh", original, "shell")
            if finding.rule == "AUTO001"
        )
        second = next(
            finding for finding in safety.scan_text("aggregate.sh", changed, "shell")
            if finding.rule == "AUTO001"
        )
        self.assertNotEqual(first.evidence_sha256, second.evidence_sha256)
        self.assertIn('"touch" additional', second.evidence)

    def test_shell_env_option_operand_cannot_hide_quoted_publication(self):
        text = """env -u UNUSED "git" commit -m unsafe
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("quoted-env.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009", "AUTO010"}.issubset(rules))

    def test_shell_env_split_string_preserves_quoted_publication_rules(self):
        text = """env -S '\"/usr/bin/git\" commit -m unsafe'
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("env-split.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009", "AUTO010"}.issubset(rules))

    def test_checked_quoted_shell_publication_has_critical_durable_finding(self):
        text = """set -e
env -u UNUSED "git" commit -m current
"""
        findings = [
            finding for finding in safety.scan_text("quoted-checked.sh", text, "shell")
            if finding.rule == "AUTO010"
        ]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "critical")

    def test_single_continued_finding_hashes_the_complete_logical_command(self):
        original = "publish() {\n  git \\\n    push origin HEAD:refs/heads/topic\n}\n"
        changed = original.replace("  git " + "\\", '  "/tmp/evil/git" ' + "\\")
        first = next(
            finding for finding in safety.scan_text("continued-identity.sh", original, "shell")
            if finding.rule == "AUTO009"
        )
        second = next(
            finding for finding in safety.scan_text("continued-identity.sh", changed, "shell")
            if finding.rule == "AUTO009"
        )
        self.assertNotEqual(first.evidence_sha256, second.evidence_sha256)
        self.assertIn("/tmp/evil/git", second.evidence)

    def test_shell_aggregate_evidence_binds_every_unchecked_publication(self):
        original = "publish() {\n  git commit -m first\n}\n"
        changed = "publish() {\n  git commit -m first\n  git push origin HEAD\n}\n"
        first = next(
            finding for finding in safety.scan_text("aggregate-publish.sh", original, "shell")
            if finding.rule == "AUTO009"
        )
        second = next(
            finding for finding in safety.scan_text("aggregate-publish.sh", changed, "shell")
            if finding.rule == "AUTO009"
        )
        self.assertNotEqual(first.evidence_sha256, second.evidence_sha256)
        self.assertIn("git push origin HEAD", second.evidence)

    def test_shell_bare_publication_and_function_pass_are_false_success(self):
        text = """publish() {
  git commit -m unsafe
  echo PASS
}
publish
"""
        rules = {finding.rule for finding in safety.scan_text("publish.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009"}.issubset(rules))

    def test_shell_errexit_propagates_bare_publication_failure(self):
        text = "set -euo pipefail\ngit commit -m checked\n"
        rules = {finding.rule for finding in safety.scan_text("strict.sh", text, "shell")}
        self.assertNotIn("AUTO001", rules)
        self.assertNotIn("AUTO009", rules)

    def test_shell_backslash_continuation_preserves_command_classification(self):
        text = "git \\\n  commit -m unsafe\nprintf 'PASS\\n'\n"
        rules = {finding.rule for finding in safety.scan_text("continued.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009", "AUTO010"}.issubset(rules))

    def test_shell_continued_force_push_preserves_protected_ref_rules(self):
        text = "set -euo pipefail\ngit push \\\n  --force origin HEAD:refs/heads/main\n"
        rules = {finding.rule for finding in safety.scan_text("continued-push.sh", text, "shell")}
        self.assertTrue({"AUTO004", "AUTO005", "AUTO010"}.issubset(rules))

    def test_shell_errexit_is_suppressed_in_if_test(self):
        text = "set -e\nif git commit -m unsafe; then :; fi\nprintf 'PASS\\n'\n"
        rules = {finding.rule for finding in safety.scan_text("if-test.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009"}.issubset(rules))

    def test_shell_errexit_is_suppressed_in_or_list(self):
        text = "set -e\ngit commit -m unsafe || printf 'ignored\\n'\nprintf 'PASS\\n'\n"
        rules = {finding.rule for finding in safety.scan_text("or-list.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009", "AUTO010"}.issubset(rules))

    def test_shell_zero_valued_exit_variable_does_not_propagate(self):
        text = "rc=0\ngit add -- exact.txt || exit $rc\nprintf 'PASS\\n'\n"
        rules = {finding.rule for finding in safety.scan_text("zero-handler.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_shell_explicit_nonzero_exit_propagates_without_errexit(self):
        text = "git commit -m checked || exit $?\n"
        rules = {finding.rule for finding in safety.scan_text("explicit-exit.sh", text, "shell")}
        self.assertNotIn("AUTO001", rules)
        self.assertNotIn("AUTO009", rules)

    def test_uncalled_function_cannot_enable_module_errexit(self):
        text = """enable_errexit() {
  set -e
}
git add -- exact.txt
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("uncalled.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_function_uses_invocation_time_errexit_state(self):
        text = """set -e
stage() {
  git add -- exact.txt
}
set +e
stage
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("invocation-options.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_command_prefix_options_do_not_hide_grouped_background_alias(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage README.md
fn=stage
( time -p "$fn" /definitely/missing ) &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("prefixed-background.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_detached_clobber_redirection_does_not_hide_grouped_background_alias(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage README.md
fn=stage
( >| background.log "$fn" /definitely/missing ) &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("detached-clobber.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_clobber_redirection_does_not_hide_grouped_background_alias(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage README.md
fn=stage
( >|background.log "$fn" /definitely/missing ) &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("clobber-background.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_leading_redirection_does_not_hide_grouped_background_alias(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage README.md
fn=stage
( >background.log "$fn" /definitely/missing ) &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("redirected-background.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_function_keyword_command_word_name_triggers_sticky_boundary(self):
        text = """set -e
function stage-run {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage-run /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("hyphen-function.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_reserved_word_function_declaration_triggers_sticky_boundary(self):
        text = """set -e
if true; then stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}; fi
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("reserved-function.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_continuation_inside_function_keyword_triggers_sticky_boundary(self):
        text = """set -e
funct\\
ion stage {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("split-keyword.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_continued_function_keyword_triggers_sticky_boundary(self):
        text = """set -e
function \\
stage {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("continued-function.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_command_list_function_declaration_triggers_sticky_boundary(self):
        text = """set -e
:; stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("listed-function.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_nonbrace_compound_function_body_stays_fail_closed(self):
        text = """set -e
stage() (
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
)
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("subshell-function.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_function_body_can_start_on_declaration_line(self):
        text = """set -e
stage() { :
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("inline-body.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_split_line_function_declaration_stays_fail_closed(self):
        text = """set -e
stage()
{
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("split-function.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_multiline_quoted_brace_cannot_restore_module_errexit(self):
        text = """set -e
stage() {
  marker='
}
'
  git add -- "$1"
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("multiline-quote.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_heredoc_brace_cannot_restore_module_errexit(self):
        text = """set -e
stage() {
  cat <<'EOF'
}
EOF
  git add -- "$1"
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("heredoc-brace.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_nested_quoted_substitution_does_not_end_function_scope(self):
        text = """set -e
stage() {
  marker="$(printf \"%s\" \"}\")"
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("nested-substitution.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_hash_word_and_inner_group_preserve_function_scope(self):
        text = """set -e
stage() {
  printf '%s\\n' foo#bar; {
    :
  }
  git add -- "$1"
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("hash-group.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_escaped_parameter_pattern_does_not_end_function_scope(self):
        text = """set -e
stage() {
  trimmed=${value%\\}}
  git add -- "$1"
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("parameter-pattern.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_quoted_brace_does_not_end_function_scope(self):
        text = """set -e
stage() {
  printf '%s\\n' '}'
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("quoted-brace.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_grouped_background_alias_cannot_propagate_errexit(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage README.md
fn=stage
( "$fn" /definitely/missing ) &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("grouped-background.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_background_aliased_function_cannot_propagate_errexit(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
fn=stage
"$fn" /definitely/missing &
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("background-alias.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_prior_control_list_command_does_not_hide_aliased_function_call(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage README.md
set +e
fn=stage; call=$fn
: && "$call" /definitely/missing
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("control-list-alias.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_prior_same_line_command_does_not_hide_aliased_function_call(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage existing.txt
set +e
:; fn=stage; call=$fn; "$call" missing.txt
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("prior-command-alias.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_same_line_chained_function_aliases_propagate_option_state(self):
        text = """set -e
stage() {
  git add -- "$1"
  printf 'status=%s target=%s\\n' "$?" "$1" > result.log
}
stage existing.txt
set +e
fn=stage; call=$fn
"$call" missing.txt
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("same-line-aliases.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_chained_function_alias_invocation_propagates_option_state(self):
        text = """set -e
stage() {
  git add -- "$1"
}
stage existing.txt
set +e
fn=stage
call=$fn
"$call" missing.txt
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("chained-function-alias.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_function_alias_invocation_propagates_option_state(self):
        text = """set -e
stage() {
  git add -- "$1"
}
stage existing.txt
set +e
fn=stage
"$fn" missing.txt
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("function-alias.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_function_options_propagate_through_call_chain(self):
        text = """set -e
inner() {
  git add -- exact.txt
}
inner
set +e
outer() {
  inner
}
outer
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("transitive-options.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_shell_wrapper_must_record_or_propagate_child_failure(self):
        text = """swallow() {
  if "$@"; then
    :
  else
    true
  fi
}
swallow git commit -m unsafe
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("swallow.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002"}.issubset(rules))

    def test_shell_unverified_failure_handler_does_not_propagate(self):
        text = """fail() {
  :
}
git add -- exact.txt || fail
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("fake-handler.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_shell_logging_wrapper_does_not_propagate_aggregate_failure(self):
        text = """checked() {
  if "$@"; then
    :
  else
    printf 'failure\\n' >> failures.log
  fi
}
checked git add -- exact.txt
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("logging-wrapper.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO010"}.issubset(rules))

    def test_shell_pipeline_requires_pipefail(self):
        unsafe = "set -e\ngit commit -m unsafe | cat\nprintf 'PASS\\n'\n"
        safe = "set -euo pipefail\ngit commit -m checked | cat\n"
        unsafe_rules = {finding.rule for finding in safety.scan_text("pipeline.sh", unsafe, "shell")}
        safe_rules = {finding.rule for finding in safety.scan_text("pipefail.sh", safe, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009"}.issubset(unsafe_rules))
        self.assertNotIn("AUTO001", safe_rules)
        self.assertNotIn("AUTO009", safe_rules)

    def test_shell_conditional_function_call_suppresses_errexit_inside(self):
        text = """set -e
publish() {
  git commit -m unsafe
}
publish || printf 'ignored\\n'
printf 'PASS\\n'
"""
        rules = {finding.rule for finding in safety.scan_text("function.sh", text, "shell")}
        self.assertTrue({"AUTO001", "AUTO002", "AUTO009", "AUTO010"}.issubset(rules))

    def test_unrelated_git_status_redirect_is_not_durable_state(self):
        text = "rm -rf \"$TARGET\"\ngit status 2>/dev/null\n"
        self.assertIn("AUTO010", {finding.rule for finding in safety.scan_text("status.sh", text, "shell")})

    def test_shell_preoperation_status_for_other_commit_is_not_durable(self):
        text = "set -e\nprintf 'status=published commit=other\\n' > result.log\ngit commit -m current\n"
        findings = safety.scan_text("preoperation.sh", text, "shell")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_shell_postoperation_status_for_other_commit_is_not_durable(self):
        text = "set -e\ngit commit -m current\nprintf 'status=published commit=other\\n' > result.log\n"
        findings = safety.scan_text("postoperation.sh", text, "shell")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_shell_command_substitution_stales_runtime_status(self):
        text = """set -e
git commit -m current
printf 'status=%s commit=current\\n' \\
  "$(set +e; false & wait $!; printf %s $?)" > result.log
"""
        findings = safety.scan_text("substitution-stale.sh", text, "shell")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_shell_same_line_async_command_stales_question_status(self):
        text = "set -e\ngit commit -m current\nfalse & printf 'status=%s target=unknown\\n' \"$?\" > result.log\n"
        findings = safety.scan_text("async-stale.sh", text, "shell")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_shell_same_line_prior_command_stales_question_status(self):
        text = "set -e\ngit commit -m current\nset +e; false; printf 'status=%s target=unknown\\n' \"$?\" > result.log\n"
        findings = safety.scan_text("same-line-stale.sh", text, "shell")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_shell_stale_question_status_is_not_operation_linked(self):
        text = "set -e\ngit commit -m current\ntrue\nprintf 'status=%s target=unknown\\n' \"$?\" > result.log\n"
        findings = safety.scan_text("stale-status.sh", text, "shell")
        match = [finding for finding in findings if finding.rule == "AUTO010"]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0].severity, "critical")

    def test_shell_status_named_write_without_operation_content_is_not_durable(self):
        text = "set -e\nprintf 'unrelated\\n' > status.log\nrm -rf \"$TARGET\"\n"
        self.assertIn("AUTO010", {finding.rule for finding in safety.scan_text("named.sh", text, "shell")})

    def test_shell_operation_linked_outcome_is_durable(self):
        text = "set -e\nrm -rf \"$TARGET\"\nprintf 'status=deleted target=%s\\n' \"$TARGET\" > result.log\n"
        self.assertNotIn(
            "AUTO010",
            {finding.rule for finding in safety.scan_text("linked.sh", text, "shell")},
        )

    def test_force_push_variants_cover_canonical_protected_refs(self):
        python_commands = (
            '["git", "push", "--force", "origin", "HEAD:refs/heads/main"]',
            '["git", "push", "--force-with-lease=refs/heads/main", "origin", "HEAD"]',
            '["git", "push", "origin", "+HEAD:main"]',
        )
        for command in python_commands:
            text = "import subprocess\nsubprocess.run(%s, check=True)\n" % command
            self.assertIn("AUTO004", {f.rule for f in safety.scan_text("push.py", text, "python")})
        for command in (
            "git push --force origin HEAD:refs/heads/main",
            "git push --force-with-lease=refs/heads/main origin HEAD",
            "git push origin +HEAD:main",
        ):
            self.assertIn("AUTO004", {f.rule for f in safety.scan_text("push.sh", command + "\n", "shell")})

    def test_python_mutation_before_gate_is_scoped_per_function(self):
        text = """import shutil
import subprocess

def remove(path):
    shutil.rmtree(path)

def validate():
    subprocess.run([\"python3\", \"_src/validate.py\"], check=True)
"""
        self.assertNotIn("AUTO008", {finding.rule for finding in safety.scan_text("scoped.py", text, "python")})

    def test_every_known_bad_fixture_has_a_failing_aggregate_verdict(self):
        fixtures = {
            "link_verification_evidence.py.fixture": "python",
            "publish_public_site.sh.fixture": "shell",
            "old_runner_envelope.sh.fixture": "shell",
            "mutation_before_gate.sh.fixture": "shell",
            "shell_exec.py.fixture": "python",
            "validation_repair.py.fixture": "python",
        }
        for name, language in fixtures.items():
            relative = (FIXTURES / name).relative_to(ROOT).as_posix()
            report = safety.scan_explicit_paths(ROOT, [relative], language=language)
            self.assertEqual(report["verdict"], "FAIL", name)
            inferred = safety.scan_explicit_paths(ROOT, [relative])
            self.assertEqual(inferred["verdict"], "FAIL", name)
            self.assertGreater(report["counts"]["unresolved_critical"], 0, name)

    def test_current_safe_aggregate_controls_do_not_regress(self):
        controls = {
            "_src/tools/review_request_baseline_audit.py": {"AUTO001", "AUTO002"},
            "_src/tools/review_ingest.py": {"AUTO002"},
            "_src/tools/curation_ingest.py": {"AUTO002"},
            "_src/validate.py": {"AUTO007"},
        }
        for relative, forbidden in controls.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            rules = {finding.rule for finding in safety.scan_text(relative, text, "python")}
            self.assertTrue(forbidden.isdisjoint(rules), f"{relative}: {sorted(rules & forbidden)}")
        self.assert_runner_transaction_control(self.runner_transaction_findings())

    def test_runner_transaction_control_rejects_a_sixth_auto010(self):
        findings = self.runner_transaction_findings()
        sixth = replace(
            next(finding for finding in findings if finding.rule == "AUTO010"),
            line=9999,
            symbol="FutureTransaction.unreviewed_operation",
            evidence="unreviewed destructive operation",
            evidence_sha256=safety.hashlib.sha256(
                b"unreviewed destructive operation"
            ).hexdigest(),
        )
        with self.assertRaises(AssertionError):
            self.assert_runner_transaction_control([*findings, sixth])

    def test_runner_transaction_control_rejects_a_moved_auto010(self):
        findings = self.runner_transaction_findings()
        target = next(finding for finding in findings if finding.line == 277)
        changed = [
            replace(finding, line=finding.line + 1) if finding is target else finding
            for finding in findings
        ]
        with self.assertRaises(AssertionError):
            self.assert_runner_transaction_control(changed)

    def test_runner_transaction_control_rejects_a_renamed_auto010(self):
        findings = self.runner_transaction_findings()
        target = next(finding for finding in findings if finding.line == 1735)
        changed = [
            replace(finding, symbol="Transaction.renamed_lock")
            if finding is target
            else finding
            for finding in findings
        ]
        with self.assertRaises(AssertionError):
            self.assert_runner_transaction_control(changed)

    def test_runner_transaction_control_rejects_changed_evidence_bytes(self):
        findings = self.runner_transaction_findings()
        target = next(finding for finding in findings if finding.line == 1876)
        changed_evidence = target.evidence + "\n# byte drift"
        changed = [
            replace(
                finding,
                evidence=changed_evidence,
                evidence_sha256=safety.hashlib.sha256(
                    changed_evidence.encode("utf-8")
                ).hexdigest(),
            )
            if finding is target
            else finding
            for finding in findings
        ]
        with self.assertRaises(AssertionError):
            self.assert_runner_transaction_control(changed)

    def test_findings_have_exact_stable_source_identity(self):
        finding = self.scan("shell_exec.py.fixture", "python")[0]
        self.assertEqual(finding.path, "shell_exec.py.fixture")
        self.assertGreater(finding.line, 0)
        self.assertEqual(len(finding.evidence_sha256), 64)
        self.assertEqual(
            finding.evidence_sha256,
            safety.hashlib.sha256(finding.evidence.encode("utf-8")).hexdigest(),
        )

    def test_multiline_python_evidence_binds_all_command_arguments(self):
        original = """import subprocess
subprocess.run(
    [\"git\", \"commit\", \"-m\", \"unsafe\"],
)
"""
        changed = original.replace('"unsafe"', '"changed"')
        first = next(f for f in safety.scan_text("multi.py", original, "python") if f.rule == "AUTO009")
        second = next(f for f in safety.scan_text("multi.py", changed, "python") if f.rule == "AUTO009")
        self.assertIn('"unsafe"', first.evidence)
        self.assertNotEqual(first.evidence_sha256, second.evidence_sha256)


class AutomationSafetyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "TODO.md").write_text(
            "- [ ] **0038-14** Deferred mutator classification.\n",
            encoding="utf-8",
        )
        (self.root / "DONE.md").write_text("# Done\n", encoding="utf-8")
        self.script = self.root / "danger.py"
        self.script.write_text(
            "import subprocess\nsubprocess.run(['git', 'commit', '-m', 'unsafe'])\n",
            encoding="utf-8",
        )
        initial = safety.scan_explicit_paths(self.root, ["danger.py"], language="python")
        self.critical = [item for item in initial["findings"] if item["severity"] == "critical"]
        self.assertTrue(self.critical)
        self.policy_path = self.root / "policy.json"
        self.write_policy(self.critical)

    def tearDown(self):
        self.temp.cleanup()

    def write_policy(self, findings, **overrides):
        entries = []
        for finding in findings:
            entry = {
                "path": finding["path"],
                "rule": finding["rule"],
                "line": finding["line"],
                "symbol": finding["symbol"],
                "evidence_sha256": finding["evidence_sha256"],
                "kind": "blocking-task",
                "rationale": "The dedicated lifecycle Task owns this exact legacy risk.",
                "owner_task": "0038-14",
                "expires_after_task": "0038-14",
                "expected_safe_invariant": "No affected source line changes before the owner Task replaces it.",
            }
            entry.update(overrides)
            entries.append(entry)
        self.policy_path.write_text(
            json.dumps({"schema_version": 1, "dispositions": entries}),
            encoding="utf-8",
        )

    def scan(self):
        return safety.scan_explicit_paths(
            self.root,
            ["danger.py"],
            language="python",
            policy_path=self.policy_path,
            today=datetime.date(2026, 8, 17),
        )

    def test_exact_hash_bound_open_task_disposition_passes(self):
        report = self.scan()
        self.assertEqual(report["verdict"], "PASS")
        self.assertEqual(report["counts"]["unresolved_critical"], 0)
        self.assertEqual(report["counts"]["disposed_critical"], len(self.critical))

    def test_source_change_expires_disposition(self):
        self.script.write_text(
            "import subprocess\nsubprocess.run(['git', 'commit', '-m', 'changed'])\n",
            encoding="utf-8",
        )
        report = self.scan()
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any(error["code"] == "POLICY_STALE" for error in report["policy_errors"]))
        self.assertGreater(report["counts"]["unresolved_critical"], 0)

    def test_terminal_owner_task_expires_disposition(self):
        (self.root / "TODO.md").write_text(
            "- [x] **0038-14** Deferred mutator classification.\n",
            encoding="utf-8",
        )
        report = self.scan()
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any("terminal" in error["message"] for error in report["policy_errors"]))

    def test_broad_file_ignore_is_rejected(self):
        self.write_policy(self.critical, path="*.py")
        report = self.scan()
        self.assertEqual(report["verdict"], "FAIL")
        self.assertTrue(any("without glob" in error["message"] for error in report["policy_errors"]))


@unittest.skipUnless(shutil.which("git"), "git is required for tracked discovery")
class AutomationSafetyDiscoveryTests(unittest.TestCase):
    def test_live_discovery_scans_only_tracked_non_fixture_automation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "good.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "untracked.py").write_text("print('not tracked')\n", encoding="utf-8")
            (root / "logs").mkdir()
            (root / "logs" / "archived.sh").write_text("rm -rf /\n", encoding="utf-8")
            fixture_dir = root / "_src" / "tests" / "fixtures"
            fixture_dir.mkdir(parents=True)
            (fixture_dir / "bad.py").write_text("import os; os.system('rm -rf /')\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "add", "good.py", "logs/archived.sh", "_src/tests/fixtures/bad.py"],
                cwd=root,
                check=True,
            )
            paths, errors = safety.tracked_automation_paths(root)
            self.assertEqual(errors, [])
            self.assertEqual(paths, ["good.py"])

    def test_live_scan_inspects_staged_and_worktree_source_variants(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tools = root / "_src" / "tools"
            tools.mkdir(parents=True)
            script = tools / "danger.py"
            script.write_text(
                "import subprocess\nsubprocess.run(['git', 'commit', '-m', 'staged-danger'])\n",
                encoding="utf-8",
            )
            (tools / "automation_safety_policy.json").write_text(
                json.dumps({"schema_version": 1, "dispositions": []}),
                encoding="utf-8",
            )
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")
            (root / "DONE.md").write_text("# DONE\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "_src", "TODO.md", "DONE.md"], cwd=root, check=True)
            script.write_text("print('safe worktree facade')\n", encoding="utf-8")

            report = safety.scan_repository(root)
            self.assertEqual(report["verdict"], "FAIL")
            self.assertTrue(any(f["rule"] == "AUTO009" for f in report["findings"]))

    def test_live_scan_rejects_policy_index_worktree_divergence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tools = root / "_src" / "tools"
            tools.mkdir(parents=True)
            (tools / "safe.py").write_text("print('safe')\n", encoding="utf-8")
            policy = tools / "automation_safety_policy.json"
            policy.write_text('{"schema_version":1,"dispositions":[]}\n', encoding="utf-8")
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")
            (root / "DONE.md").write_text("# DONE\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "_src", "TODO.md", "DONE.md"], cwd=root, check=True)
            policy.write_text('{"schema_version": 1, "dispositions": []}\n', encoding="utf-8")

            report = safety.scan_repository(root)
            self.assertEqual(report["verdict"], "FAIL")
            self.assertTrue(any(e["code"] == "POLICY_DIVERGENCE" for e in report["policy_errors"]))

    def test_staged_policy_deletion_cannot_be_hidden_by_worktree_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tools = root / "_src" / "tools"
            tools.mkdir(parents=True)
            (tools / "safe.py").write_text("print('safe')\n", encoding="utf-8")
            policy = tools / "automation_safety_policy.json"
            policy.write_text('{"schema_version":1,"dispositions":[]}\n', encoding="utf-8")
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")
            (root / "DONE.md").write_text("# DONE\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Automation Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "automation@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "add", "_src", "TODO.md", "DONE.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=root, check=True)
            subprocess.run(
                ["git", "rm", "--cached", "_src/tools/automation_safety_policy.json"],
                cwd=root,
                check=True,
                capture_output=True,
            )

            report = safety.scan_repository(root)
            self.assertEqual(report["verdict"], "FAIL")
            self.assertTrue(any(e["code"] == "POLICY_DIVERGENCE" for e in report["policy_errors"]))


class RemediationBehaviorTests(unittest.TestCase):
    @staticmethod
    def write_required_build_reports(directory, validate_exit=0):
        for kind in build_report.REQUIRED_STAGES:
            payload = {
                "schema_version": "1.0",
                "report_kind": kind,
                "tool": kind,
                "command": kind,
                "inputs": [],
                "started_at": "2026-08-16T00:00:00Z",
                "finished_at": "2026-08-16T00:00:01Z",
                "duration_s": 1,
                "exit_code": validate_exit if kind == "validate" else 0,
                "changed_artifacts": [],
                "counts": {},
                "findings": [],
                "run_archive_ref": None,
            }
            (Path(directory) / (kind + ".json")).write_text(json.dumps(payload), encoding="utf-8")

    def test_link_evidence_scratch_inventory_never_deletes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scratch = root / "_review_request_bisect_tmp"
            scratch.mkdir()
            marker = scratch / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            found = link_evidence.find_ephemeral_paths(root)
            self.assertEqual(found, ["_review_request_bisect_tmp"])
            self.assertTrue(marker.is_file())

    def test_link_evidence_model_validation_never_repairs_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            model = Path(temp) / "process.json"
            original = "{broken\n"
            model.write_text(original, encoding="utf-8")
            findings = link_evidence.validate_page_models([model])
            self.assertEqual(len(findings), 1)
            self.assertEqual(model.read_text(encoding="utf-8"), original)

    def test_build_report_missing_required_stages_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            original = build_report.REPORTS_DIR
            build_report.REPORTS_DIR = temp
            try:
                combined, _path = build_report.combine_reports()
            finally:
                build_report.REPORTS_DIR = original
            self.assertNotEqual(combined["exit_code"], 0)
            categories = {item["category"] for item in combined["findings"]}
            self.assertIn("missing-build-stage", categories)
            self.assertFalse(combined["counts"]["overall_success"])

    def test_build_report_main_propagates_combined_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            original = build_report.REPORTS_DIR
            build_report.REPORTS_DIR = temp
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    result = build_report.main(["combine"])
            finally:
                build_report.REPORTS_DIR = original
            self.assertNotEqual(result, 0)

    def test_build_report_rejects_wrapping_exit_code_and_cli_stays_nonzero(self):
        with tempfile.TemporaryDirectory() as temp:
            self.write_required_build_reports(temp, validate_exit=256)
            original = build_report.REPORTS_DIR
            build_report.REPORTS_DIR = temp
            try:
                combined, _path = build_report.combine_reports()
            finally:
                build_report.REPORTS_DIR = original
            self.assertEqual(combined["exit_code"], 1)
            self.assertTrue(any(item["category"] == "malformed-build-report" for item in combined["findings"]))

            code = (
                "import sys; sys.path.insert(0, %r); import build_report; "
                "build_report.REPORTS_DIR=%r; raise SystemExit(build_report.main(['combine']))"
            ) % (str(TOOLS), temp)
            result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_build_report_malformed_input_is_a_durable_error(self):
        with tempfile.TemporaryDirectory() as temp:
            original = build_report.REPORTS_DIR
            build_report.REPORTS_DIR = temp
            try:
                (Path(temp) / "bad.json").write_text("{broken", encoding="utf-8")
                combined, _path = build_report.combine_reports()
            finally:
                build_report.REPORTS_DIR = original
            categories = {item["category"] for item in combined["findings"]}
            self.assertIn("malformed-build-report", categories)
            self.assertNotEqual(combined["exit_code"], 0)

    def test_spec_campaign_missing_backend_writes_reports_and_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as temp:
            campaign = Path(temp)
            (campaign / "raw").mkdir()
            (campaign / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "campaign": "missing-backend",
                        "documents": [{"name": "Doc"}],
                    }
                ),
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                result = spec_extraction_campaign.main(["report", str(campaign)])
            self.assertEqual(result, 1)
            self.assertTrue((campaign / "scorecard.json").is_file())
            scorecard = json.loads((campaign / "scorecard.json").read_text(encoding="utf-8"))
            self.assertEqual(scorecard["failures"][0]["document"], "Doc")


if __name__ == "__main__":
    unittest.main()
