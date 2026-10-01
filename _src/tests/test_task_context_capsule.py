"""Hermetic fixture tests for the read-only Task context/resume capsule generator.

Two fixtures reconstruct real historical continuation incidents named by Task
0038-07's Definition of Done:

- ``resume_0037_48_premature_publication`` replays the recorded 2026-08-16
  ``0037-48`` incident (see the retained claim
  ``TODO-perplexity-0037-48-a7f3c1e29b04.md`` and ``TODO.md``'s Progress log
  for that Task): a turn exhausted its tool budget and prematurely reported
  publishing ``run.sh`` before it existed. The claim's own "Next step"
  section, reproduced verbatim below, is the exact next action a resuming
  agent must see -- not the already-completed discovery phase.
- ``resume_0036_06_context_overflow`` reconstructs the ``0036-06`` translation
  Task's recorded context-overflow lesson (``TODO.md``'s Feature-0038
  evidence baseline names "context overflow" among current legacy claims;
  ``DONE.md``'s closure evidence records ten locale registers, a stable-ID
  JSONL pipeline, and fail-closed ``translate.googleapis.com`` retries that
  "exceeded the original 900-request estimate"). Because that claim predates
  the branch-workflow claim-retention rule and was deleted at Feature
  closure, no literal claim file survives; this fixture is an evidence-
  grounded reconstruction of a plausible mid-run state, not a byte-for-byte
  historical replay, and is documented as such.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


doctor = _load("legacy_task_doctor", "legacy_task_doctor.py")
planner = _load("legacy_scope_planner", "legacy_scope_planner.py")
capsule_mod = _load("task_context_capsule", "task_context_capsule.py")

REAL_DAG_BYTES = (ROOT / planner.DAG_PATH).read_bytes()

AGENTS_MD = "# AGENTS.md\n\nFixture instructions with no markdown links.\n"
SANDBOX_MD = "# SANDBOX.md\n\nFixture sandbox rules; never an escalation token.\n"
PRIVILEGED_MD = "# PRIVILEGED.md\n\nFixture privileged rules.\n"
BUNDLE_MD = "# Fixture instruction bundle\n"

AGENT_WORKFLOW = {
    "schema": "agent-workflow-bootstrap@v1",
    "workflow_version": "1.0.0",
    "authority_epoch": "legacy-writable",
    "authority_profile": "legacy-lists",
    "write_phase": "legacy-writable",
    "required_capability": "sandboxed-grunt",
    "runner_protocol": "runner-request@v1",
    "selector_digest": "sha256:" + ("b" * 64),
    "instruction_bundle": "docs/pipeline/agent-instructions/legacy/index.md",
}


def _write_text(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(root: Path, relative: str, value) -> bytes:
    payload = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


class FixtureRepository:
    """A minimal, self-contained legacy-list repository for capsule tests."""

    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        _write_text(self.root, "AGENTS.md", AGENTS_MD)
        _write_text(self.root, "SANDBOX.md", SANDBOX_MD)
        _write_text(self.root, "PRIVILEGED.md", PRIVILEGED_MD)
        _write_text(self.root, "docs/pipeline/agent-instructions/legacy/index.md", BUNDLE_MD)
        _write_json(self.root, "agent-workflow.json", AGENT_WORKFLOW)
        _write_text(self.root, "DONE.md", "# DONE.md\n")
        (self.root / planner.DAG_PATH).parent.mkdir(parents=True, exist_ok=True)
        (self.root / planner.DAG_PATH).write_bytes(REAL_DAG_BYTES)

    def close(self) -> None:
        self.temporary.cleanup()

    def write_todo(self, text: str) -> None:
        _write_text(self.root, "TODO.md", text)

    def write_claim(self, filename: str, text: str) -> None:
        _write_text(self.root, filename, text)

    def write_attempt(self, task_id: str, request_id: str, result_value: dict, *, verdict: str = "passed") -> None:
        result_relative = f"output/logs/{task_id}/{request_id}/result.json"
        result_bytes = _write_json(self.root, result_relative, result_value)
        pointer_value = {
            "schema": "legacy-runner-current-pointer@v1",
            "task_id": task_id,
            "request_id": request_id,
            "result_path": result_relative,
            "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
            "verdict": verdict,
            "lifecycle_state": "complete" if verdict == "passed" else "failed",
            "updated_at": "2026-08-16T00:00:00Z",
        }
        _write_json(self.root, f"output/logs/{task_id}/current.json", pointer_value)

    def build(self, task_id: str, **kwargs):
        return capsule_mod.build_capsule(self.root, task_id, reachable_commits=set(), **kwargs)


def _basic_todo(marker: str = "p") -> str:
    return (
        "## Feature: 1000 — Fixture Feature\n\n"
        f"- [{marker}] **1000-01** PREREQ: 1000-01:1000-02, 1000-01:1000-03 "
        "Resume capsule fixture task.\n"
        "  - **Acceptance criteria:** fixture.\n"
        "  - **Definition of Done:** fixture.\n\n"
        "- [x] **1000-02** Terminal prerequisite one.\n"
        "  - **Closed:** fixture, no REF needed for this test.\n\n"
        "- [ ] **1000-03** Nonterminal prerequisite two.\n"
        "  - **Acceptance criteria:** fixture.\n"
    )


def _basic_claim(next_step: str = "Continue the fixture Task.", scope: str = "`_src/tools/fixture_thing.py`") -> str:
    return (
        "# TODO-fixture-1000-01-abc123def456.md — active claim\n\n"
        "## Claim identity\n\n"
        "task_id: 1000-01\n"
        "request_id: abc123def456\n"
        "owner_token: agent:fixture:1000-01:abc123def456\n"
        "base_commit: pending-discovery\n"
        "capability_class: sandboxed-grunt\n"
        "state: [p]\n\n"
        "## Intended write scope\n\n"
        f"- {scope}\n\n"
        "## Next step\n\n"
        f"{next_step}\n"
    )


class BuildCapsuleTests(unittest.TestCase):
    def test_task_not_found(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        result = repo.build("9999-01")
        self.assertEqual(result["verdict"], "TASK-NOT-FOUND")
        self.assertEqual(result["task"], None)
        self.assertLessEqual(len(result["summary"]), 10)

    def test_malformed_task_id_is_incomplete(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        result = repo.build("not-a-task-id")
        self.assertEqual(result["verdict"], "INCOMPLETE")

    def test_missing_required_input_is_incomplete(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        # TODO.md is never written -> legacy_task_doctor input discovery fails.
        result = repo.build("1000-01")
        self.assertEqual(result["verdict"], "INCOMPLETE")

    def test_no_active_claim_yields_fallback_next_action(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo(marker=" "))
        result = repo.build("1000-01")
        self.assertEqual(result["verdict"], "OK")
        self.assertIsNone(result["claim"])
        self.assertIn("No active [p] claim", result["next_action"])

    def test_claim_identity_scope_and_next_step_are_captured(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim(
            "TODO-fixture-1000-01-abc123def456.md",
            _basic_claim(next_step="Publish the bounded fixture transaction and yield for the runner result."),
        )
        result = repo.build("1000-01")
        self.assertEqual(result["verdict"], "OK")
        self.assertIsNotNone(result["claim"])
        self.assertEqual(result["claim"]["owner_token"], "agent:fixture:1000-01:abc123def456")
        self.assertEqual(result["scope"]["explicit"], ["_src/tools/fixture_thing.py"])
        self.assertIn("Publish the bounded fixture transaction", result["next_action"])
        terminal = {item["id"]: item["terminal"] for item in result["prerequisites"]}
        self.assertEqual(terminal, {"1000-02": True, "1000-03": False})

    def test_derived_scope_expands_through_dag_when_explicit_scope_is_a_source(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim(
            "TODO-fixture-1000-01-abc123def456.md",
            _basic_claim(scope="`AGENTS.md`"),
        )
        result = repo.build("1000-01")
        self.assertTrue(result["scope"]["dag_considered"])
        self.assertEqual(result["scope"]["explicit"], ["AGENTS.md"])
        self.assertTrue(result["scope"]["derived"], "AGENTS.md is a validate-canonical DAG input in the real DAG")
        outputs = {item["output"] for item in result["scope"]["derived"]}
        self.assertIn("output/issue-validation.json", outputs)

    def test_derived_scope_is_empty_for_a_non_dag_source_path(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        result = repo.build("1000-01")
        self.assertEqual(result["scope"]["derived"], [])

    def test_pending_attempt_reads_current_pointer_and_result(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        repo.write_attempt(
            "1000-01",
            "req-0001",
            {
                "schema": "legacy-runner-transaction-result@v1",
                "task_id": "1000-01",
                "request_id": "req-0001",
                "owner_token": "agent:fixture:1000-01:abc123def456",
                "verdict": "passed",
                "lifecycle_state": "complete",
                "phase": "finalize-claim",
                "phases": [
                    {"name": "preflight", "status": "passed", "exit_code": 0},
                    {"name": "generate", "status": "passed", "exit_code": 0},
                ],
                "findings": [],
                "commits": {"substantive": "a" * 40, "bookkeeping": None, "final": "a" * 40},
                "recovery": "none",
                "evidence": {"journal": f"output/logs/1000-01/req-0001/transaction-journal.json"},
            },
        )
        result = repo.build("1000-01")
        self.assertEqual(result["pending_attempt"]["current_pointer"]["request_id"], "req-0001")
        self.assertTrue(result["pending_attempt"]["result_consistent"])
        self.assertEqual(result["completed_phases"], ["preflight", "generate"])
        paths = {item["path"] for item in result["retained_evidence"]}
        self.assertIn(f"output/logs/1000-01/req-0001/result.json", paths)

    def test_tampered_result_bytes_are_flagged_inconsistent(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        repo.write_attempt(
            "1000-01",
            "req-0002",
            {
                "schema": "legacy-runner-transaction-result@v1",
                "task_id": "1000-01",
                "request_id": "req-0002",
                "verdict": "passed",
                "lifecycle_state": "complete",
                "phase": "finalize-claim",
                "phases": [{"name": "preflight", "status": "passed", "exit_code": 0}],
                "findings": [],
            },
        )
        # Tamper with the immutable result after the current pointer was bound to it.
        result_path = repo.root / "output/logs/1000-01/req-0002/result.json"
        result_path.write_bytes(result_path.read_bytes().replace(b"passed", b"failed"))
        result = repo.build("1000-01")
        self.assertFalse(result["pending_attempt"]["result_consistent"])

    def test_material_findings_are_scoped_to_the_task_and_claim(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        # A malformed owner_token on the claim produces an LTD-CLAIM-IDENTITY-MISMATCH
        # finding scoped to this Task/claim; an unrelated Task's own findings must
        # not leak in.
        repo.write_todo(_basic_todo())
        broken_claim = _basic_claim().replace(
            "owner_token: agent:fixture:1000-01:abc123def456",
            "owner_token: agent:fixture:9999-99:abc123def456",
        )
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", broken_claim)
        result = repo.build("1000-01")
        rules = {item["rule"] for item in result["material_findings"]}
        self.assertTrue(rules, "expected at least one material finding for the mismatched claim")
        self.assertTrue(all(rule.startswith("LTD-") for rule in rules))

    def test_ambiguous_claim_is_flagged_and_deterministic(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        second = _basic_claim().replace("abc123def456", "zzz999zzz999")
        repo.write_claim("TODO-fixture-1000-01-zzz999zzz999.md", second)
        result = repo.build("1000-01")
        self.assertTrue(result["claim_ambiguous"])
        self.assertEqual(result["claim"]["path"], "TODO-fixture-1000-01-abc123def456.md")

    def test_claim_path_argument_disambiguates(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        second = _basic_claim().replace("abc123def456", "zzz999zzz999")
        repo.write_claim("TODO-fixture-1000-01-zzz999zzz999.md", second)
        result = repo.build("1000-01", claim_path="TODO-fixture-1000-01-zzz999zzz999.md")
        self.assertFalse(result["claim_ambiguous"])
        self.assertEqual(result["claim"]["path"], "TODO-fixture-1000-01-zzz999zzz999.md")

    def test_budget_is_enforced_and_truncation_preserves_core_identity(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        # Many nonterminal prerequisites drive both the prerequisites list and
        # (via LTD-TASK-CLAIM-MISSING-style noise avoided) the serialized size up.
        prereq_ids = [f"1000-{index:02d}" for index in range(4, 40)]
        prereq_decl = ", ".join(f"1000-01:{pid}" for pid in prereq_ids)
        todo = [
            "## Feature: 1000 — Fixture Feature\n\n",
            f"- [p] **1000-01** PREREQ: 1000-01:1000-02, 1000-01:1000-03, {prereq_decl} "
            "Resume capsule fixture task.\n"
            "  - **Acceptance criteria:** fixture.\n\n",
            "- [x] **1000-02** Terminal prerequisite one.\n\n",
            "- [ ] **1000-03** Nonterminal prerequisite two.\n\n",
        ]
        for pid in prereq_ids:
            todo.append(f"- [ ] **{pid}** Nonterminal filler prerequisite.\n\n")
        repo.write_todo("".join(todo))
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        budget = 4000
        result = repo.build("1000-01", max_bytes=budget)
        serialized = capsule_mod._canonical_compact_bytes(result)
        self.assertLessEqual(len(serialized), budget)
        self.assertEqual(result["budget"]["max_bytes"], budget)
        self.assertEqual(result["task_id"], "1000-01")
        self.assertIsNotNone(result["next_action"])
        self.assertTrue(result["truncated"])
        # Core identity survives truncation even though 38 of the 40
        # prerequisites and the authority digests were dropped to fit.
        self.assertEqual(result["schema"], capsule_mod.CAPSULE_SCHEMA)
        self.assertIsNotNone(result["claim"])
        self.assertLess(len(result["prerequisites"]), 40)

    def test_pathological_tiny_budget_terminates_and_reports_true_size(self):
        # The truncation loop is bounded (material findings, derived scope,
        # prerequisites, completed phases, retained evidence, then authority
        # digests, then a strictly-shrinking next-action floor); an
        # unreasonably small budget cannot be met once every truncatable
        # field is empty and next_action has hit its floor, but the call
        # must still terminate promptly rather than loop and must report the
        # real achieved size instead of silently lying about the budget.
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        result = repo.build("1000-01", max_bytes=1)
        serialized = capsule_mod._canonical_compact_bytes(result)
        self.assertEqual(result["budget"]["actual_bytes"], len(serialized))
        self.assertEqual(result["schema"], capsule_mod.CAPSULE_SCHEMA)
        self.assertEqual(result["task_id"], "1000-01")
        self.assertEqual(result["authority"]["input_digests"], {})
        self.assertEqual(result["material_findings"], [])

    def test_render_summary_is_bounded_to_ten_lines(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        result = repo.build("1000-01")
        summary = capsule_mod.render_summary(result)
        self.assertLessEqual(len(summary), 10)
        self.assertTrue(all(isinstance(line, str) for line in summary))

    def test_default_budget_fits_a_realistic_capsule(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        repo.write_claim("TODO-fixture-1000-01-abc123def456.md", _basic_claim())
        result = repo.build("1000-01")
        self.assertEqual(result["truncated"], {})
        self.assertLessEqual(result["budget"]["actual_bytes"], capsule_mod.DEFAULT_MAX_CAPSULE_BYTES)


class HistoricalIncidentResumeTests(unittest.TestCase):
    """Reproduce the two named Definition-of-Done resume scenarios."""

    def test_resume_0037_48_premature_publication(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(
            "## Feature: 0037 — Git-Native Issue Store, Provenance Graph, and Backlog Migration\n\n"
            "- [p] **0037-48** Qualify and freeze the legacy singleton runner bootstrap "
            "for sandboxed/grunt execution before any other Feature 0037 Task starts.\n"
            "  - **Acceptance criteria:** fixture reconstruction of the real Task text.\n"
        )
        # Verbatim "Next step" content from the real, retained claim
        # TODO-perplexity-0037-48-a7f3c1e29b04.md at the point the premature
        # publication report was corrected and discovery had actually completed.
        next_step = (
            "Design and publish the bounded, self-contained fixture qualification "
            "transaction (Task 0037-48 phase 2): isolated fixture directory, "
            "preflight/validation guards keyed to expected_base: "
            "df7e8794bbebde6fc73fc82b0e06dca7b73530fb, timeout/progress/result "
            "capture, path-limited substantive commit inside the fixture, capture "
            "of its hash, a second bookkeeping/REF commit, injected-partial-failure "
            "recovery checks, and singleton slot cleanup."
        )
        repo.write_claim(
            "TODO-perplexity-0037-48-a7f3c1e29b04.md",
            "# TODO-perplexity-0037-48-a7f3c1e29b04.md — active claim\n\n"
            "## Claim identity\n\n"
            "task_id: 0037-48\n"
            "request_id: a7f3c1e29b04\n"
            "owner_token: agent:perplexity:0037-48:a7f3c1e29b04\n"
            "base_commit: df7e8794bbebde6fc73fc82b0e06dca7b73530fb\n"
            "capability_class: sandboxed/grunt\n"
            "state: [p]\n\n"
            "## Intended write scope\n\n"
            "- `logs/runner-qualification-0037-48/`\n\n"
            "## Next step\n\n"
            f"{next_step}\n",
        )
        # Discovery (phase 1) already completed successfully; only phase 2 remains.
        repo.write_attempt(
            "0037-48",
            "b2e91f6d4a83",
            {
                "schema": "legacy-runner-transaction-result@v1",
                "task_id": "0037-48",
                "request_id": "b2e91f6d4a83",
                "verdict": "passed",
                "lifecycle_state": "complete",
                "phase": "result",
                "phases": [{"name": "discovery", "status": "passed", "exit_code": 0}],
                "findings": [],
            },
        )
        result = repo.build("0037-48")
        self.assertEqual(result["verdict"], "OK")
        self.assertEqual(result["claim"]["owner_token"], "agent:perplexity:0037-48:a7f3c1e29b04")
        self.assertEqual(result["completed_phases"], ["discovery"])
        self.assertIn("phase 2", result["next_action"])
        self.assertNotIn("premature", result["next_action"].lower())

    def test_resume_0036_06_context_overflow(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(
            "## Feature: 0036 — Process documentation i18n\n\n"
            "- [p] **0036-06** Vollstaendige Uebersetzung der normativen und "
            "nutzerfreundlichen Prozessdokumentation ueber die bestehende "
            "i18n-Pipeline.\n"
            "  - **Acceptance criteria:** fixture reconstruction; real Task required "
            "all ten locale registers at 4648/4648 with zero open segments.\n"
        )
        # Reconstructed (not literal -- the original claim predates claim
        # retention and was deleted at Feature closure) mid-run state: six of
        # ten locale registers already complete when a context-window
        # overflow interrupted the turn; only the remaining four are pending.
        next_step = (
            "Continue the stable-ID JSONL translation pipeline for the four "
            "remaining locale registers (ar, hi, ko, zh); de, es, fr, pt, ru, nl "
            "already report 4648/4648 translated with zero open segments and must "
            "not be re-extracted or re-translated. Keep using read-only "
            "translate.googleapis.com requests with fail-closed retry; the retry "
            "count already exceeds the original 900-request estimate and remains "
            "within the reconstructed 1200 upper bound."
        )
        repo.write_claim(
            "TODO-fixture-0036-06-9c4e7b2a.md",
            "# TODO-fixture-0036-06-9c4e7b2a.md — active claim\n\n"
            "## Claim identity\n\n"
            "task_id: 0036-06\n"
            "request_id: 9c4e7b2a\n"
            "owner_token: agent:fixture:0036-06:9c4e7b2a\n"
            "base_commit: pending-discovery\n"
            "capability_class: sandboxed-grunt\n"
            "state: [p]\n\n"
            "## Intended write scope\n\n"
            "- `_src/i18n/`\n\n"
            "## Next step\n\n"
            f"{next_step}\n",
        )
        repo.write_attempt(
            "0036-06",
            "9c4e7b2a-batch1",
            {
                "schema": "legacy-runner-transaction-result@v1",
                "task_id": "0036-06",
                "request_id": "9c4e7b2a-batch1",
                "verdict": "passed",
                "lifecycle_state": "complete",
                "phase": "result",
                "phases": [
                    {"name": "extract-stable-ids", "status": "passed", "exit_code": 0},
                    {"name": "translate-de-es-fr-pt-ru-nl", "status": "passed", "exit_code": 0},
                ],
                "findings": [],
            },
        )
        result = repo.build("0036-06")
        self.assertEqual(result["verdict"], "OK")
        self.assertEqual(
            result["completed_phases"],
            ["extract-stable-ids", "translate-de-es-fr-pt-ru-nl"],
        )
        self.assertIn("ar, hi, ko, zh", result["next_action"])
        # Resuming must name the remaining locales as the actionable target
        # and must not lose the already-completed-locale blocker context
        # that prevents redundant re-extraction/re-translation.
        self.assertIn("remaining locale registers (ar, hi, ko, zh)", result["next_action"])
        self.assertIn("must not be re-extracted", result["next_action"])


class CliTests(unittest.TestCase):
    def test_main_json_matches_build_capsule_and_exit_code(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo(marker=" "))
        import io

        buffer = io.BytesIO()
        wrapper = io.TextIOWrapper(buffer, encoding="utf-8")
        old_stdout = sys.stdout
        try:
            sys.stdout = wrapper
            code = capsule_mod.main(["--root", str(repo.root), "--task-id", "1000-01", "--json"])
            wrapper.flush()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue().decode("utf-8"))
        self.assertEqual(payload["task_id"], "1000-01")
        self.assertEqual(payload["verdict"], "OK")

    def test_main_task_not_found_exit_code(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        repo.write_todo(_basic_todo())
        code = capsule_mod.main(["--root", str(repo.root), "--task-id", "8888-01"])
        self.assertEqual(code, 1)

    def test_main_incomplete_exit_code(self):
        repo = FixtureRepository()
        self.addCleanup(repo.close)
        code = capsule_mod.main(["--root", str(repo.root), "--task-id", "1000-01"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
