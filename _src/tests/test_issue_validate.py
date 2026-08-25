import importlib.util
import json
import os
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

_SHA1_HEX = 40


class FixtureGitError(RuntimeError):
    """Fail-closed isolation error for temporary Git fixtures."""


def _isolated_git_env(repo, *, template=None, hooks_path=None):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    repo = Path(repo).resolve()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = os.devnull
    env["GIT_EDITOR"] = "true"
    env["GIT_SEQUENCE_EDITOR"] = "true"
    env["GIT_PAGER"] = "cat"
    env["GIT_CEILING_DIRECTORIES"] = str(repo.parent)
    keys = [
        ("commit.gpgsign", "false"),
        ("tag.gpgSign", "false"),
        ("gpg.format", "openpgp"),
        ("advice.detachedHead", "false"),
    ]
    if template is not None:
        env["GIT_TEMPLATE_DIR"] = str(template)
        keys.append(("init.templateDir", str(template)))
    if hooks_path is not None:
        keys.append(("core.hooksPath", str(hooks_path)))
    env["GIT_CONFIG_COUNT"] = str(len(keys))
    for index, (name, value) in enumerate(keys):
        env[f"GIT_CONFIG_KEY_{index}"] = name
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    return env


def _contain_under_repo(repo, path):
    root = Path(repo).resolve()
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise FixtureGitError(f"path escapes fixture root: {resolved} not under {root}") from exc
    return resolved


def run_isolated_git(repo, *args, check=True, template=None, hooks_path=None):
    repo = Path(repo).resolve()
    env = _isolated_git_env(repo, template=template, hooks_path=hooks_path)
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise FixtureGitError(f"git {' '.join(args)} failed: {detail}")
    return completed


def _assert_fixture_identity(repo):
    repo = Path(repo).resolve()
    toplevel = run_isolated_git(repo, "rev-parse", "--show-toplevel").stdout.strip()
    git_dir = run_isolated_git(repo, "rev-parse", "--absolute-git-dir").stdout.strip()
    expected_git = str(repo / ".git")
    if Path(toplevel).resolve() != repo:
        raise FixtureGitError(f"show-toplevel {toplevel!r} != {str(repo)!r}")
    if Path(git_dir).resolve() != Path(expected_git).resolve():
        raise FixtureGitError(f"absolute-git-dir {git_dir!r} != {expected_git!r}")


def fixture_add(repo, paths):
    repo = Path(repo).resolve()
    relatives = []
    for path in paths:
        contained = _contain_under_repo(repo, path)
        relatives.append(str(contained.relative_to(repo)))
    if not relatives:
        raise FixtureGitError("git add requires enumerated paths")
    run_isolated_git(repo, "add", "--", *relatives)


def fixture_commit(repo, message):
    repo = Path(repo).resolve()
    _assert_fixture_identity(repo)
    run_isolated_git(repo, "config", "user.email", "fixture@example.invalid")
    run_isolated_git(repo, "config", "user.name", "Fixture")
    run_isolated_git(repo, "commit", "-qm", message)
    head = run_isolated_git(repo, "rev-parse", "HEAD").stdout.strip()
    if len(head) != _SHA1_HEX or any(ch not in "0123456789abcdef" for ch in head):
        raise FixtureGitError(f"HEAD is not a commit sha: {head!r}")
    kind = run_isolated_git(repo, "cat-file", "-t", head).stdout.strip()
    if kind != "commit":
        raise FixtureGitError(f"HEAD is {kind}, not commit")
    git_dir = Path(run_isolated_git(repo, "rev-parse", "--absolute-git-dir").stdout.strip()).resolve()
    object_path = git_dir / "objects" / head[:2] / head[2:]
    if not object_path.is_file():
        raise FixtureGitError(f"commit object not inside fixture git dir: {object_path}")
    return head


def init_isolated_repo(directory):
    repo = Path(directory).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _contain_under_repo(repo, repo)
    template = repo / ".fixture-git-template"
    template.mkdir(exist_ok=True)
    (template / "hooks").mkdir(exist_ok=True)
    hooks = repo / ".git" / "hooks"
    run_isolated_git(repo, "init", "-q", "--template", str(template),
                     template=template, hooks_path=str(hooks))
    _assert_fixture_identity(repo)
    hooks.mkdir(parents=True, exist_ok=True)
    run_isolated_git(repo, "config", "user.email", "fixture@example.invalid",
                     template=template, hooks_path=str(hooks))
    run_isolated_git(repo, "config", "user.name", "Fixture",
                     template=template, hooks_path=str(hooks))
    run_isolated_git(repo, "config", "commit.gpgsign", "false",
                     template=template, hooks_path=str(hooks))
    run_isolated_git(repo, "config", "core.hooksPath", str(hooks),
                     template=template, hooks_path=str(hooks))
    return repo


def _seed_validator_sources(repo):
    paths = []
    for relative in ("_src/tools/issue_store.py", "issues/_schema/issue-item-v1.schema.json"):
        target = Path(repo) / relative
        _contain_under_repo(repo, target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        paths.append(target)
    return paths


def _files_under(repo):
    repo = Path(repo).resolve()
    files = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or ".fixture-git-template" in path.parts:
            continue
        _contain_under_repo(repo, path)
        files.append(path)
    return files


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
        repo = init_isolated_repo(directory)
        _seed_validator_sources(repo)
        self.base(repo / "issues")
        fixture_add(repo, _files_under(repo))
        fixture_commit(repo, "baseline")
        return repo

    def test_working_tree_and_staged_index_are_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self.init_repo(temp)
            task = repo / "issues/0099/0099-01/index.md"
            valid = task.read_text()
            task.write_text(document("0099-01", "task", "0099", ["0099-99"]))
            fixture_add(repo, [task])
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
            fixture_add(repo, [task])
            fixture_commit(repo, "tombstones")
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
            blob_a = run_isolated_git(
                ROOT, "rev-parse", "HEAD:_src/tools/issue_validate.py").stdout.strip()
            blob_b = run_isolated_git(
                ROOT, "rev-parse", "HEAD:_src/tools/issue_store.py").stdout.strip()
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
                    repo = init_isolated_repo(Path(temp) / "repo")
                    issues = repo / "issues"
                    shutil.copytree(root, issues)
                    _seed_validator_sources(repo)
                    fixture_add(repo, _files_under(repo))
                    fixture_commit(repo, "base")
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
            repo = init_isolated_repo(temp)
            issues = repo / "issues"
            write_item(issues, "0099", document("0099", "feature"))
            write_item(issues, "0099-01", document("0099-01", "task", "0099", state="closed"))
            write_json(issues / "0099/0099-01/closure.json", closure_payload("0099-01"))
            write_json(issues / "0099/0099-01/approval.json", approval_payload())
            _seed_validator_sources(repo)
            fixture_add(repo, _files_under(repo))
            fixture_commit(repo, "closed")
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
            repo = init_isolated_repo(temp)
            issues = repo / "issues"
            write_item(issues, "0099", document("0099", "feature"))
            write_item(issues, "0099-01", document("0099-01", "task", "0099"))
            _seed_validator_sources(repo)
            fixture_add(repo, _files_under(repo))
            fixture_commit(repo, "open")
            task = issues / "0099/0099-01/index.md"
            task.write_text(document("0099-01", "task", "0099", state="in_progress"))
            fixture_add(repo, [task])
            task.write_text(document("0099-01", "task", "0099", state="open"))
            staged, _ = VALIDATE.validate(repo=repo, source="staged-index", compare_head=True,
                                          now=FIXED_NOW)
            working, _ = VALIDATE.validate(repo=repo, source="working-tree", compare_head=True,
                                           now=FIXED_NOW)
            self.assertIn("IV0911", {value.rule for value in staged})
            self.assertNotIn("IV0911", {value.rule for value in working})

    def test_clean_in_progress_with_fresh_claim_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = init_isolated_repo(temp)
            issues = repo / "issues"
            write_item(issues, "0099", document("0099", "feature"))
            write_item(issues, "0099-01", document("0099-01", "task", "0099"))
            _seed_validator_sources(repo)
            fixture_add(repo, _files_under(repo))
            head = fixture_commit(repo, "base")
            write_item(issues, "0099-01", document("0099-01", "task", "0099", state="in_progress"))
            write_json(issues / "0099/0099-01/claim.json", claim_payload("0099-01", base_commit=head))
            diagnostics, _ = VALIDATE.validate(repo=repo, source="working-tree", now=FIXED_NOW)
            self.assertEqual(diagnostics, [])


PROV_FIXTURES = ROOT / "_src/tests/fixtures/0037-09.03"
PROV_CASES = json.loads((PROV_FIXTURES / "cases.json").read_text())["cases"]
LEAK_TOKEN = json.loads((PROV_FIXTURES / "cases.json").read_text())["adversarial_leak_token"]


class ProvenanceIssueValidateTest(unittest.TestCase):
    maxDiff = None

    def seed_issues(self, root):
        write_item(root, "0099", document("0099", "feature"))
        write_item(root, "0099-01", document("0099-01", "task", "0099"))

    def validate_prov(self, prov):
        with tempfile.TemporaryDirectory() as temp:
            issues = Path(temp) / "issues"
            self.seed_issues(issues)
            diagnostics, _ = VALIDATE.validate(
                repo=ROOT, source="working-tree", root=issues, compare_head=False,
                now=FIXED_NOW, provenance_root=prov)
            return {value.rule for value in diagnostics}, diagnostics

    def test_valid_chain_passes(self):
        rules, diagnostics = self.validate_prov(PROV_FIXTURES / "valid-chain")
        self.assertEqual(rules, set(), diagnostics)

    def test_every_provenance_negative_fixture(self):
        for case in PROV_CASES:
            with self.subTest(case=case["name"]):
                rules, diagnostics = self.validate_prov(PROV_FIXTURES / case["dir"])
                self.assertIn(case["rule"], rules, diagnostics)

    def test_adversarial_leak_token_is_detected_under_budget(self):
        self.assertEqual(VALIDATE.MAX_TRAVERSAL, 100000)
        self.assertEqual(VALIDATE.MAX_PROVENANCE_FILES, 20000)
        rules, diagnostics = self.validate_prov(PROV_FIXTURES / "restricted-leak")
        self.assertIn("IV0932", rules, diagnostics)
        self.assertTrue(any(LEAK_TOKEN in value.message for value in diagnostics), diagnostics)

    def test_existing_structural_and_lifecycle_rules_are_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "issues"
            write_item(root, "0099", document("0099", "feature"))
            write_item(root, "0099-01", document("0099-01", "task", "0099", ["0099-99"]))
            diagnostics, _ = VALIDATE.validate(repo=ROOT, source="working-tree", root=root,
                                               compare_head=False)
            self.assertIn("IV0904", {value.rule for value in diagnostics})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "issues"
            write_item(root, "0099", document("0099", "feature"))
            write_item(root, "0099-01", document("0099-01", "task", "0099", state="in_progress"))
            diagnostics, _ = VALIDATE.validate(
                repo=ROOT, source="working-tree", root=root, compare_head=False, now=FIXED_NOW)
            self.assertIn("IV0911", {value.rule for value in diagnostics})


_HOSTILE_GIT_KEYS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_TEMPLATE_DIR",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_PARAMETERS",
)


class FixtureGitIsolationTest(unittest.TestCase):
    def test_hostile_git_env_does_not_mutate_foreign_or_root(self):
        root_head = run_isolated_git(ROOT, "rev-parse", "HEAD").stdout.strip()
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            foreign = parent / "foreign"
            intended = parent / "intended"
            foreign.mkdir()
            marker = foreign / "KEEP.txt"
            marker.write_text("foreign-canary\n")
            hostile_config = parent / "hostile.gitconfig"
            hostile_config.write_text("[commit]\n\tgpgsign = true\n[core]\n\thooksPath = /tmp\n")
            hostile_template = parent / "hostile-template"
            (hostile_template / "hooks").mkdir(parents=True)
            (hostile_template / "hooks" / "pre-commit").write_text(
                "#!/bin/sh\necho injected > \"{}/pwned\"\n".format(foreign)
            )
            os.chmod(hostile_template / "hooks" / "pre-commit", 0o755)
            saved = {key: os.environ.get(key) for key in _HOSTILE_GIT_KEYS}
            os.environ["GIT_DIR"] = str(foreign / ".git")
            os.environ["GIT_WORK_TREE"] = str(foreign)
            os.environ["GIT_INDEX_FILE"] = str(foreign / "index")
            os.environ["GIT_COMMON_DIR"] = str(foreign / ".git")
            os.environ["GIT_OBJECT_DIRECTORY"] = str(foreign / "objects")
            os.environ["GIT_TEMPLATE_DIR"] = str(hostile_template)
            os.environ["GIT_CONFIG_GLOBAL"] = str(hostile_config)
            os.environ["GIT_CONFIG_PARAMETERS"] = "'commit.gpgsign=true' 'core.hooksPath=/tmp'"
            try:
                repo = init_isolated_repo(intended)
                payload = repo / "tracked.txt"
                payload.write_text("intended\n")
                fixture_add(repo, [payload])
                head = fixture_commit(repo, "isolated")
            finally:
                for key, value in saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            self.assertTrue((repo / ".git").is_dir())
            self.assertEqual(run_isolated_git(repo, "rev-parse", "HEAD").stdout.strip(), head)
            self.assertFalse((foreign / ".git").exists())
            self.assertFalse((foreign / "index").exists())
            self.assertFalse((foreign / "pwned").exists())
            self.assertEqual(marker.read_text(), "foreign-canary\n")
            self.assertEqual(run_isolated_git(ROOT, "rev-parse", "HEAD").stdout.strip(), root_head)
            gpgsign = run_isolated_git(repo, "config", "--get", "commit.gpgsign").stdout.strip()
            self.assertEqual(gpgsign, "false")
            hooks = run_isolated_git(repo, "config", "--get", "core.hooksPath").stdout.strip()
            self.assertEqual(Path(hooks).resolve(), (repo / ".git" / "hooks").resolve())

    def test_add_rejects_path_outside_fixture(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = init_isolated_repo(Path(temp) / "repo")
            outsider = Path(temp) / "outside.txt"
            outsider.write_text("nope\n")
            with self.assertRaises(FixtureGitError):
                fixture_add(repo, [outsider])
            status = run_isolated_git(repo, "status", "--porcelain").stdout
            self.assertEqual(status, "")

    def test_identity_mismatch_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "empty"
            repo.mkdir()
            with self.assertRaises(FixtureGitError):
                _assert_fixture_identity(repo)


if __name__ == "__main__":
    unittest.main()
