import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("issue_validate", ROOT / "_src/tools/issue_validate.py")
VALIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATE)
CASES = json.loads((ROOT / "_src/tests/fixtures/0037-09.01/cases.json").read_text())["cases"]


def document(item_id, level, parent=None, prerequisites=(), criteria=None, state="open"):
    fields = [
        'schema_version: "1.0"', f'id: "{item_id}"', f'level: "{level}"',
    ]
    if parent is not None:
        fields.append(f'parent: "{parent}"')
    fields += [f'state: "{state}"', 'visibility: "internal"']
    if prerequisites:
        fields.append("prerequisites:")
        fields.extend(f'  - "{value}"' for value in prerequisites)
    criteria = criteria or ["- **AC-001** Valid criterion."]
    return "---\n" + "\n".join(fields) + "\n---\n\n" + """## Goal

Fixture goal.

## Scope

Fixture scope.

## Acceptance criteria

""" + "\n".join(criteria) + "\n\n" + """## Definition of Done

Fixture complete.
"""


def write_item(root, item_id, content):
    if len(item_id) == 4:
        path = root / item_id / "index.md"
    else:
        path = root / item_id[:4] / item_id / "index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


class IssueValidateTest(unittest.TestCase):
    maxDiff = None

    def validate_root(self, root):
        diagnostics, parsed = VALIDATE.validate(repo=ROOT, source="working-tree", root=root,
                                                compare_head=False)
        return {value.rule for value in diagnostics}, diagnostics, parsed

    def base(self, root):
        write_item(root, "0099", document("0099", "feature"))
        write_item(root, "0099-01", document("0099-01", "task", "0099"))

    def apply_mutation(self, root, mutation):
        self.base(root)
        task = root / "0099/0099-01/index.md"
        source = task.read_text()
        if mutation == "noncanonical_path":
            target = root / "0099/0099-01/0099-01.01/index.md"
            target.parent.mkdir(parents=True)
            target.write_text(document("0099-01.01", "subtask", "0099-01"))
        elif mutation == "wrong_id":
            task.write_text(source.replace('id: "0099-01"', 'id: "0099-02"'))
        elif mutation == "duplicate_item_id":
            task.write_text(source.replace('id: "0099-01"', 'id: "0099"'))
        elif mutation == "duplicate_criterion":
            task.write_text(source.replace("- **AC-001** Valid criterion.",
                                           "- **AC-001** First.\n- **AC-001** Reused."))
        elif mutation == "malformed_criterion":
            task.write_text(source.replace("AC-001", "AC-1"))
        elif mutation == "wrong_parent":
            task.write_text(source.replace('parent: "0099"', 'parent: "0098"'))
        elif mutation == "unknown_field":
            task.write_text(source.replace('state: "open"', 'state: "open"\nunknown: true'))
        elif mutation == "markdown_order":
            task.write_text(source.replace("## Goal", "## TEMP").replace(
                "## Acceptance criteria", "## Goal").replace("## TEMP", "## Acceptance criteria"))
        elif mutation == "self_dependency":
            task.write_text(document("0099-01", "task", "0099", ["0099-01"]))
        elif mutation == "missing_endpoint":
            task.write_text(document("0099-01", "task", "0099", ["0099-99"]))
        elif mutation == "feature_gate":
            task.write_text(document("0099-01", "task", "0099", ["0099"]))
        elif mutation == "cycle":
            task.write_text(document("0099-01", "task", "0099", ["0099-02"]))
            write_item(root, "0099-02", document("0099-02", "task", "0099", ["0099-01"]))
        elif mutation == "oversize":
            task.write_text(source.replace("Fixture scope.", "x" * (VALIDATE.STORE.MAX_DOCUMENT_BYTES + 1)))
        else:
            raise AssertionError(mutation)

    def test_clean_working_tree_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "issues"
            self.base(root)
            rules, diagnostics, parsed = self.validate_root(root)
            self.assertEqual(rules, set(), diagnostics)
            self.assertEqual(set(value["item"]["id"] for value in parsed.values()), {"0099", "0099-01"})

    def test_every_tracked_negative_fixture_has_expected_rule(self):
        for case in CASES:
            with self.subTest(case=case["name"]), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "issues"
                self.apply_mutation(root, case["mutation"])
                rules, diagnostics, _ = self.validate_root(root)
                self.assertIn(case["rule"], rules, diagnostics)

    def test_diagnostics_are_stable_sorted_and_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "issues"
            self.apply_mutation(root, "missing_endpoint")
            _, first, _ = self.validate_root(root)
            _, second, _ = self.validate_root(root)
            self.assertEqual(first, second)
            diagnostic = first[0]
            self.assertTrue(diagnostic.item)
            self.assertTrue(diagnostic.path)
            self.assertTrue(diagnostic.field)
            self.assertTrue(diagnostic.rule)

    def init_repo(self, directory):
        repo = Path(directory)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Fixture"], check=True)
        for relative in ("_src/tools/issue_store.py", "issues/_schema/issue-item-v1.schema.json"):
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.base(repo / "issues")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "baseline"], check=True)
        return repo

    def test_working_tree_and_staged_index_are_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.init_repo(temp)
            task = repo / "issues/0099/0099-01/index.md"
            valid = task.read_text()
            task.write_text(document("0099-01", "task", "0099", ["0099-99"]))
            subprocess.run(["git", "-C", str(repo), "add", str(task)], check=True)
            task.write_text(valid)  # unstaged repair must not affect staged validation
            staged, _ = VALIDATE.validate(repo=repo, source="staged-index", compare_head=True)
            working, _ = VALIDATE.validate(repo=repo, source="working-tree", compare_head=True)
            self.assertIn("IV0904", {value.rule for value in staged})
            self.assertNotIn("IV0904", {value.rule for value in working})

    def test_tombstone_reuse_and_removal_compare_against_head(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.init_repo(temp)
            task = repo / "issues/0099/0099-01/index.md"
            task.write_text(document("0099-01", "task", "0099", criteria=[
                "- **AC-001** ~~Retired.~~ (withdrawn, 2026-08-24: obsolete)",
                "- **AC-002** Active.",
            ]))
            subprocess.run(["git", "-C", str(repo), "add", str(task)], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "tombstones"], check=True)
            task.write_text(document("0099-01", "task", "0099", criteria=[
                "- **AC-001** Illegally reused.",
            ]))
            diagnostics, _ = VALIDATE.validate(repo=repo, source="working-tree", compare_head=True)
            rules = {value.rule for value in diagnostics}
            self.assertIn("IV0908", rules)
            self.assertIn("IV0907", rules)

    def test_explicit_authoritative_and_candidate_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            authoritative = parent / "authoritative"
            candidate = parent / "candidate"
            self.base(authoritative)
            shutil.copytree(authoritative, candidate)
            task = candidate / "0099/0099-01/index.md"
            task.write_text(document("0099-01", "task", "0099", ["0099-99"]))
            diagnostics, _ = VALIDATE.validate(repo=ROOT, source="working-tree", root=candidate,
                                               authoritative_root=authoritative)
            self.assertIn("IV0904", {value.rule for value in diagnostics})

    def test_fixed_seed_property_and_fuzz_are_bounded(self):
        randomizer = random.Random(370901)
        for _ in range(32):
            count = randomizer.randint(2, 12)
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "issues"
                write_item(root, "0099", document("0099", "feature"))
                for number in range(1, count):
                    item_id = f"0099-{number:02d}"
                    previous = [] if number == 1 else [f"0099-{number - 1:02d}"]
                    write_item(root, item_id, document(item_id, "task", "0099", previous))
                diagnostics, _ = VALIDATE.validate(repo=ROOT, source="working-tree", root=root,
                                                   compare_head=False)
                self.assertEqual(diagnostics, [])

    def test_exit_codes(self):
        self.assertEqual(VALIDATE.result_payload([], "working-tree", 0)["exit_code"], VALIDATE.EXIT_OK)
        self.assertEqual(VALIDATE.result_payload([VALIDATE.Diagnostic("X", "bad")], "working-tree", 0)["exit_code"],
                         VALIDATE.EXIT_INVALID)
        self.assertEqual(VALIDATE.main(["--source", "staged-index", "--root", "issues"]),
                         VALIDATE.EXIT_USAGE)


LC_CASES = json.loads((ROOT / "_src/tests/fixtures/0037-09.02/cases.json").read_text())["cases"]
FIXED_NOW = VALIDATE.dt.datetime(2026, 8, 25, 12, 0, tzinfo=VALIDATE.dt.timezone.utc)


def claim_payload(item_id, **overrides):
    payload = {
        "schema_version": "1.0",
        "item_id": item_id,
        "state": "active",
        "owner": {"identity": "agent:fixture"},
        "worktree_id": "wt-fixture",
        "clone_id": "clone-fixture",
        "base_commit": "0" * 40,
        "write_scopes": [f"issues/0099/{item_id}/"],
        "issued_at": "2026-08-25T10:00:00+00:00",
        "expires_at": "2026-08-25T14:00:00+00:00",
        "lease_nonce": "fixtureLeaseNonce01",
        "cas_ref": f"refs/autodocs/claims/{item_id}",
    }
    payload.update(overrides)
    payload["cas_ref_digest"] = VALIDATE._claim_digest(payload)
    return payload


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def closure_payload(item_id, *, disposition="completed", evidence=None, commit_refs=None,
                    criteria_status="checked", validation_result="pass"):
    return {
        "schema_version": "1.0",
        "item_id": item_id,
        "disposition": disposition,
        "closed_at": "2026-08-25T11:00:00+00:00",
        "closed_by": "agent:fixture",
        "criteria": [{"id": "AC-001", "status": criteria_status,
                      "evidence": evidence or ["sha256:" + "ab" * 32]}],
        "commit_refs": commit_refs or ["a" * 40, "b" * 40],
        "validation": [{"name": "fixture", "result": validation_result}],
        "reason": "fixture",
        "decision_ref": "c" * 40,
    }


def approval_payload(verified=True):
    return {
        "schema": "issue-approval@v1",
        "package_commit": "d" * 40,
        "package_digest": "sha256:" + "ab" * 32,
        "approval_ref": "refs/autodocs/approval/fixture",
        "approver_role": "closer",
        "signature_verified": verified,
    }


class LifecycleIssueValidateTest(unittest.TestCase):
    maxDiff = None

    def validate_root(self, root, **kwargs):
        diagnostics, parsed = VALIDATE.validate(
            repo=ROOT, source="working-tree", root=root, compare_head=False,
            now=FIXED_NOW, **kwargs)
        return {value.rule for value in diagnostics}, diagnostics, parsed

    def seed(self, root, *, feature_state="open", task_state="open"):
        write_item(root, "0099", document("0099", "feature", state=feature_state))
        write_item(root, "0099-01", document("0099-01", "task", "0099", state=task_state))

    def apply_mutation(self, root, mutation):
        if mutation == "illegal_transition":
            self.seed(root, task_state="open")
            write_json(root / "0099/0099-01/closure.json", closure_payload("0099-01"))
            return {"compare_head": False}
        if mutation == "missing_claim":
            self.seed(root, task_state="in_progress")
            return {}
        if mutation == "expired_claim":
            self.seed(root, task_state="in_progress")
            write_json(root / "0099/0099-01/claim.json", claim_payload(
                "0099-01", expires_at="2026-08-25T11:00:00+00:00"))
            return {}
        if mutation == "overlapping_claim":
            self.seed(root, task_state="in_progress")
            write_item(root, "0099-02", document("0099-02", "task", "0099", state="in_progress"))
            write_json(root / "0099/0099-01/claim.json", claim_payload(
                "0099-01", write_scopes=["issues/0099/"]))
            write_json(root / "0099/0099-02/claim.json", claim_payload(
                "0099-02", write_scopes=["issues/0099/0099-02/index.md"]))
            return {}
        if mutation == "stale_base":
            self.seed(root, task_state="in_progress")
            write_json(root / "0099/0099-01/claim.json", claim_payload(
                "0099-01", base_commit="1" * 40))
            return {}
        if mutation == "invalid_claim_ref":
            self.seed(root, task_state="in_progress")
            payload = claim_payload("0099-01", cas_ref="refs/autodocs/claims/0099-99")
            write_json(root / "0099/0099-01/claim.json", payload)
            return {}
        if mutation == "missing_closure":
            self.seed(root, task_state="closed")
            return {}
        if mutation == "unchecked_criterion":
            self.seed(root, task_state="closed")
            write_json(root / "0099/0099-01/closure.json",
                       closure_payload("0099-01", criteria_status="not-applicable"))
            write_json(root / "0099/0099-01/approval.json", approval_payload())
            return {}
        if mutation == "placeholder_evidence":
            self.seed(root, task_state="closed")
            write_json(root / "0099/0099-01/closure.json",
                       closure_payload("0099-01", evidence=["pending"]))
            write_json(root / "0099/0099-01/approval.json", approval_payload())
            return {}
        if mutation == "revoked_signature":
            self.seed(root, task_state="closed")
            write_json(root / "0099/0099-01/closure.json", closure_payload("0099-01"))
            write_json(root / "0099/0099-01/approval.json", approval_payload())
            write_json(root / "0099/0099-01/decisions/0001-approval.json", {
                "schema_version": "1.0",
                "decision_id": "revoked-approval",
                "item_id": "0099-01",
                "kind": "approval",
                "status": "rejected",
                "decided_at": "2026-08-25T11:00:00+00:00",
                "authority": {"kind": "human", "identity": "reviewer"},
                "rationale": "revoked",
            })
            return {}
        if mutation == "invalid_signature":
            self.seed(root, task_state="closed")
            write_json(root / "0099/0099-01/closure.json", closure_payload("0099-01"))
            write_json(root / "0099/0099-01/approval.json", approval_payload(False))
            return {}
        if mutation == "non_commit_ref":
            self.seed(root, task_state="closed")
            blob_a = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD:_src/tools/issue_validate.py"],
                text=True).strip()
            blob_b = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD:_src/tools/issue_store.py"],
                text=True).strip()
            write_json(root / "0099/0099-01/closure.json",
                       closure_payload("0099-01", commit_refs=[blob_a, blob_b]))
            write_json(root / "0099/0099-01/approval.json", approval_payload())
            return {}
        if mutation == "same_commit_ref":
            self.seed(root, task_state="closed")
            write_json(root / "0099/0099-01/closure.json",
                       closure_payload("0099-01", commit_refs=["a" * 40]))
            write_json(root / "0099/0099-01/approval.json", approval_payload())
            return {}
        if mutation == "false_feature_closure":
            self.seed(root, feature_state="closed", task_state="open")
            write_json(root / "0099/closure.json", closure_payload("0099", disposition="completed"))
            return {}
        if mutation == "archive_inflation":
            self.seed(root, task_state="closed")
            write_json(root / "0099/0099-01/closure.json",
                       closure_payload("0099-01", disposition="archived-not-accepted",
                                       validation_result="pass"))
            return {}
        raise AssertionError(mutation)

    def test_every_lifecycle_negative_fixture(self):
        for case in LC_CASES:
            with self.subTest(case=case["name"]), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "issues"
                extra = self.apply_mutation(root, case["mutation"]) or {}
                kwargs = {"now": FIXED_NOW, "compare_head": extra.get("compare_head", False)}
                if case["mutation"] == "stale_base":
                    # Isolated git repo: HEAD is not an ancestor of 1*40.
                    repo = Path(temp) / "repo"
                    repo.mkdir()
                    subprocess.run(["git", "init", "-q", str(repo)], check=True)
                    subprocess.run(["git", "-C", str(repo), "config", "user.email", "f@e.invalid"], check=True)
                    subprocess.run(["git", "-C", str(repo), "config", "user.name", "F"], check=True)
                    issues = repo / "issues"
                    shutil.copytree(root, issues)
                    for relative in ("_src/tools/issue_store.py", "issues/_schema/issue-item-v1.schema.json"):
                        target = repo / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(ROOT / relative, target)
                    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
                    diagnostics, _ = VALIDATE.validate(
                        repo=repo, source="working-tree", compare_head=True, now=FIXED_NOW)
                    rules = {value.rule for value in diagnostics}
                else:
                    diagnostics, parsed = VALIDATE.validate(
                        repo=ROOT, source="working-tree", root=root, **kwargs)
                    rules = {value.rule for value in diagnostics}
                    del parsed
                self.assertIn(case["rule"], rules, diagnostics)

    def test_illegal_transition_against_head(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "f@e.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "F"], check=True)
            issues = repo / "issues"
            write_item(issues, "0099", document("0099", "feature"))
            write_item(issues, "0099-01", document("0099-01", "task", "0099", state="closed"))
            write_json(issues / "0099/0099-01/closure.json", closure_payload("0099-01"))
            write_json(issues / "0099/0099-01/approval.json", approval_payload())
            for relative in ("_src/tools/issue_store.py", "issues/_schema/issue-item-v1.schema.json"):
                target = repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "closed"], check=True)
            task = issues / "0099/0099-01/index.md"
            task.write_text(document("0099-01", "task", "0099", state="open"))
            diagnostics, _ = VALIDATE.validate(repo=repo, source="working-tree", now=FIXED_NOW)
            self.assertIn("IV0910", {value.rule for value in diagnostics})

    def test_dispositions_and_states_have_dedicated_coverage(self):
        dispositions = ("completed", "wontfix", "superseded", "duplicate", "cancelled",
                        "archived-not-accepted")
        states = ("open", "in_progress", "blocked", "closed", "withdrawn")
        self.assertEqual(set(states), set(VALIDATE.LEGAL_TRANSITIONS))
        self.assertEqual(len(dispositions), 6)
        completed_only = {"IV0916", "IV0917", "IV0919", "IV0920"}
        for disposition in dispositions:
            with self.subTest(disposition=disposition), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "issues"
                self.seed(root, task_state="closed")
                kwargs = {"disposition": disposition}
                if disposition == "archived-not-accepted":
                    kwargs["validation_result"] = "fail"
                write_json(root / "0099/0099-01/closure.json",
                           closure_payload("0099-01", **kwargs))
                rules, diagnostics, _ = self.validate_root(root)
                if disposition == "completed":
                    self.assertTrue(completed_only.intersection(rules), diagnostics)
                else:
                    self.assertFalse(completed_only.intersection(rules), diagnostics)

    def test_lifecycle_working_tree_and_staged_index(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "f@e.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "F"], check=True)
            issues = repo / "issues"
            write_item(issues, "0099", document("0099", "feature"))
            write_item(issues, "0099-01", document("0099-01", "task", "0099"))
            for relative in ("_src/tools/issue_store.py", "issues/_schema/issue-item-v1.schema.json"):
                target = repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "open"], check=True)
            task = issues / "0099/0099-01/index.md"
            task.write_text(document("0099-01", "task", "0099", state="in_progress"))
            subprocess.run(["git", "-C", str(repo), "add", str(task)], check=True)
            task.write_text(document("0099-01", "task", "0099", state="open"))
            staged, _ = VALIDATE.validate(repo=repo, source="staged-index", compare_head=True,
                                          now=FIXED_NOW)
            working, _ = VALIDATE.validate(repo=repo, source="working-tree", compare_head=True,
                                           now=FIXED_NOW)
            self.assertIn("IV0911", {value.rule for value in staged})
            self.assertNotIn("IV0911", {value.rule for value in working})

    def test_clean_in_progress_with_fresh_claim_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "f@e.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "F"], check=True)
            issues = repo / "issues"
            write_item(issues, "0099", document("0099", "feature"))
            write_item(issues, "0099-01", document("0099-01", "task", "0099"))
            for relative in ("_src/tools/issue_store.py", "issues/_schema/issue-item-v1.schema.json"):
                target = repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
            head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"],
                                           text=True).strip()
            write_item(issues, "0099-01", document("0099-01", "task", "0099", state="in_progress"))
            write_json(issues / "0099/0099-01/claim.json", claim_payload("0099-01", base_commit=head))
            diagnostics, _ = VALIDATE.validate(repo=repo, source="working-tree", now=FIXED_NOW)
            self.assertEqual(diagnostics, [])


if __name__ == "__main__":
    unittest.main()
