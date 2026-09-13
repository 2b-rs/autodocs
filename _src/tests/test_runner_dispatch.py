"""Hermetic tests for the Task 0037-46.01 typed-action runner queue/dispatcher.

Every test below is tagged with the exact Definition-of-Done category it
covers (see the docstring table at module end). Nothing here activates the
live legacy ``run.sh`` protocol; every fixture repo and ``.runner/`` root is
created fresh under a temporary directory and discarded at teardown.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))

import runner_dispatch as rd  # noqa: E402


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check)


class FixtureRepo:
    """A tiny throwaway git repository used as the "real" repo under test."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rd-fixture-"))
        self.path = self.tmp / "repo"
        self.path.mkdir()
        git(self.path, "init", "-q", "-b", "main")
        git(self.path, "config", "user.email", "test@example.com")
        git(self.path, "config", "user.name", "Test")
        (self.path / "README.md").write_text("hello\n", encoding="utf-8")
        git(self.path, "add", "README.md")
        git(self.path, "commit", "-q", "-m", "init")
        self.main_tip = git(self.path, "rev-parse", "HEAD").stdout.strip()

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def branch(self, name, at=None):
        git(self.path, "branch", name, at or self.main_tip)
        return git(self.path, "rev-parse", name).stdout.strip()

    def commit_on(self, branch, filename, content, message="wip"):
        wt = Path(tempfile.mkdtemp(prefix="rd-wt-"))
        git(self.path, "worktree", "add", "-f", str(wt), branch)
        (wt / filename).write_text(content, encoding="utf-8")
        git(wt, "add", filename)
        git(wt, "commit", "-q", "-m", message)
        tip = git(wt, "rev-parse", "HEAD").stdout.strip()
        git(self.path, "worktree", "remove", "--force", str(wt))
        shutil.rmtree(wt, ignore_errors=True)
        return tip

    def tip(self, ref):
        return git(self.path, "rev-parse", ref).stdout.strip()


class DispatchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rd-runner-"))
        self.runner_root = rd.RunnerRoot(self.tmp / ".runner")
        self.runner_root.ensure_layout()
        self.registry = rd.ActionRegistry()
        self.repo = FixtureRepo()
        self.dispatcher = rd.Dispatcher(self.runner_root, self.registry, repo_root=self.repo.path)

    def tearDown(self):
        self.repo.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- helpers ----------------------------------------------------------

    def make_request(self, action_id, request_id, *, expected_base=None, read_scopes=None,
                      write_scopes=None, preflight_extra=None, args=None, authority_epoch="legacy-writable",
                      timeout=5, network_hosts=None, credential_handles=None, dependencies=None,
                      idempotence_suffix=None):
        expected_base = expected_base or self.repo.main_tip
        args = args or {}
        pf = [f"typed-action:{action_id}"]
        for k, v in args.items():
            pf.append(f"arg:{k}={json.dumps(v) if not isinstance(v, str) else v}")
        pf.extend(preflight_extra or [])
        return {
            "schema": "runner-request@v1",
            "request_id": request_id,
            "claim_owner_token": f"agent:test:0037-46.01:{request_id}",
            "action": self.registry.get(action_id)["envelope_action"] if self.registry.get(action_id) else "read_only_discovery",
            "expected_base": expected_base,
            "authority_epoch": authority_epoch,
            "read_scopes": read_scopes if read_scopes is not None else ["TODO.md"],
            "write_scopes": write_scopes if write_scopes is not None else [],
            "preflight": pf,
            "limits": {"timeout_seconds": timeout, "cpu": 1, "memory_mib": 256},
            "idempotence_key": f"{action_id}:test:{idempotence_suffix or request_id}",
            **({"network_hosts": network_hosts} if network_hosts else {}),
            **({"credential_handles": credential_handles} if credential_handles else {}),
            **({"dependencies": dependencies} if dependencies else {}),
        }

    def publish(self, agent, request_id, request_obj):
        self.runner_root.write_draft(agent, request_id, request_obj)
        return self.runner_root.publish_draft(agent, request_id)

    def default_ctx(self, **overrides):
        kwargs = dict(
            base_commit=self.repo.main_tip,
            capability_class="sandboxed-grunt",
            ref_state={"refs/heads/main": self.repo.main_tip},
        )
        kwargs.update(overrides)
        return rd.PreflightContext(**kwargs)


# ---------------------------------------------------------------------------
# 1. Draft visibility
# ---------------------------------------------------------------------------

class DraftVisibilityTests(DispatchTestCase):
    def test_draft_not_visible_until_atomic_publish(self):
        req = self.make_request("runner.discovery@v1", "r1")
        self.runner_root.write_draft("agentA", "r1", req)
        self.assertEqual(self.runner_root.list_ready_requests(), [])
        self.runner_root.publish_draft("agentA", "r1")
        self.assertEqual(self.runner_root.list_ready_requests(), ["r1"])

    def test_incomplete_draft_cannot_be_published(self):
        d = self.runner_root.draft_dir("agentA", "r2")
        d.mkdir(parents=True)
        (d / "manifest.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(rd.RunnerDispatchError):
            self.runner_root.publish_draft("agentA", "r2")

    def test_publish_is_same_filesystem_rename_not_copy(self):
        req = self.make_request("runner.discovery@v1", "r3")
        self.runner_root.write_draft("agentA", "r3", req)
        src = self.runner_root.draft_dir("agentA", "r3")
        self.assertTrue(src.is_dir())
        self.runner_root.publish_draft("agentA", "r3")
        self.assertFalse(src.exists())
        self.assertTrue((self.runner_root.requests / "r3").is_dir())


# ---------------------------------------------------------------------------
# 2. Concurrent publication / claiming
# ---------------------------------------------------------------------------

class ConcurrentClaimTests(DispatchTestCase):
    def test_only_one_thread_wins_the_claim(self):
        req = self.make_request("runner.discovery@v1", "race1")
        self.publish("agentA", "race1", req)
        wins = []
        errs = []

        def try_claim():
            try:
                self.runner_root.claim("race1", "worker-" + threading.current_thread().name)
                wins.append(1)
            except rd.RunnerDispatchError:
                errs.append(1)

        threads = [threading.Thread(target=try_claim) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(wins), 1)
        self.assertEqual(len(errs), 7)


# ---------------------------------------------------------------------------
# 3. Stale base / epoch / ref
# ---------------------------------------------------------------------------

class StalePreflightTests(DispatchTestCase):
    def test_stale_base_rejected(self):
        req = self.make_request("runner.discovery@v1", "s1", expected_base="a" * 40)
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["STALE_BASE"], findings)

    def test_stale_epoch_rejected(self):
        req = self.make_request("runner.discovery@v1", "s2", authority_epoch="issue-store-writable")
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["STALE_EPOCH"], findings)

    def test_stale_pinned_ref_rejected(self):
        stale_tip = "b" * 40
        req = self.make_request(
            "runner.discovery@v1", "s3",
            read_scopes=[f"ref:refs/heads/main@{stale_tip}"],
        )
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["STALE_REF"], findings)

    def test_fresh_pinned_ref_accepted(self):
        req = self.make_request(
            "runner.discovery@v1", "s4",
            read_scopes=[f"ref:refs/heads/main@{self.repo.main_tip}"],
        )
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertTrue(ok, findings)


# ---------------------------------------------------------------------------
# 4. Scope collision
# ---------------------------------------------------------------------------

class ScopeCollisionTests(DispatchTestCase):
    def test_second_claim_on_overlapping_write_scope_rejected(self):
        claim_file = self.repo.tmp / "TODO-agentA-c1.md"
        claim_file.write_text("owner_token: agent:a:1:1\n", encoding="utf-8")
        req1 = self.make_request(
            "claim.finalize@v1", "c1",
            args={"claim_path": str(claim_file), "owner_token": "agent:a:1:1", "expected_state": "[x]"},
            write_scopes=["TODO.md"],
        )
        req2 = self.make_request(
            "claim.finalize@v1", "c2",
            args={"claim_path": str(claim_file), "owner_token": "agent:a:1:1", "expected_state": "[x]"},
            write_scopes=["TODO.md"],
        )
        self.publish("agentA", "c1", req1)
        self.publish("agentB", "c2", req2)
        self.dispatcher.max_workers = 2
        # Leave c1 claimed but unresolved (no result yet) to model an in-flight request.
        self.runner_root.claim("c1", "w1")
        collisions = self.runner_root.currently_claimed_write_scopes(exclude_request_id="c2")
        self.assertIn({"TODO.md"}, collisions)
        result = self.dispatcher.claim_and_execute("c2", "w2", self.default_ctx())
        self.assertEqual(result["status"], "rejected")
        self.assertIn(rd.FINDING["SCOPE_COLLISION"], result["findings"])


# ---------------------------------------------------------------------------
# 5. Unknown / generic action
# ---------------------------------------------------------------------------

class UnknownGenericActionTests(DispatchTestCase):
    def test_unknown_action_rejected(self):
        req = self.make_request("no.such.action@v1", "u1")
        req["preflight"] = ["typed-action:no.such.action@v1"]
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["UNKNOWN_ACTION"], findings)

    def test_generic_shell_action_forbidden(self):
        req = self.make_request("runner.discovery@v1", "u2")
        req["preflight"] = ["typed-action:shell.run@v1", "arg:cmd=rm -rf /"]
        req["idempotence_key"] = "shell.run@v1:test:u2"
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["GENERIC_FORBIDDEN"], findings)

    def test_registry_has_no_generic_action_entries(self):
        for action_id in self.registry.actions:
            self.assertFalse(self.registry.is_forbidden(action_id))


# ---------------------------------------------------------------------------
# 6. Unavailable dependency / credential
# ---------------------------------------------------------------------------

class DependencyCredentialTests(DispatchTestCase):
    def test_unavailable_dependency_rejected(self):
        req = self.make_request("runner.discovery@v1", "d1", dependencies=["0099-99"])
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx(available_dependencies=set()))
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["UNAVAILABLE_DEPENDENCY"], findings)

    def test_available_dependency_accepted(self):
        req = self.make_request("runner.discovery@v1", "d2", dependencies=["0099-99"])
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx(available_dependencies={"0099-99"}))
        self.assertTrue(ok, findings)

    def test_unavailable_credential_rejected(self):
        req = self.make_request("sign.create@v1", "d3", credential_handles=["signing:owner"])
        ctx = self.default_ctx(capability_class="privileged", credential_store=set())
        ok, findings, _ = rd.preflight(req, self.registry, ctx)
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["UNAVAILABLE_CREDENTIAL"], findings)

    def test_credential_not_allowed_for_action_without_credential_authority(self):
        req = self.make_request("runner.discovery@v1", "d4", credential_handles=["signing:owner"])
        ctx = self.default_ctx(credential_store={"signing:owner"})
        ok, findings, _ = rd.preflight(req, self.registry, ctx)
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["CREDENTIAL_NOT_ALLOWED"], findings)

    def test_available_credential_on_privileged_action_accepted(self):
        req = self.make_request(
            "sign.create@v1", "d5", credential_handles=["signing:owner"],
            args={"credential_handle": "signing:owner", "payload_digest": "sha256:" + "0" * 64},
        )
        ctx = self.default_ctx(capability_class="privileged", credential_store={"signing:owner"})
        ok, findings, _ = rd.preflight(req, self.registry, ctx)
        self.assertTrue(ok, findings)


# ---------------------------------------------------------------------------
# 7. Network denial
# ---------------------------------------------------------------------------

class NetworkDenialTests(DispatchTestCase):
    def test_network_host_not_allowlisted_rejected(self):
        req = self.make_request("env.bootstrap-known-hosts@v1", "n1", network_hosts=["evil.example.com"],
                                 args={"host": "evil.example.com"})
        ctx = self.default_ctx(network_allowed_hosts={"github.com"})
        ok, findings, _ = rd.preflight(req, self.registry, ctx)
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["NETWORK_DENIED"], findings)

    def test_network_on_action_without_network_authority_rejected(self):
        req = self.make_request("runner.discovery@v1", "n2", network_hosts=["github.com"])
        ctx = self.default_ctx(network_allowed_hosts={"github.com"})
        ok, findings, _ = rd.preflight(req, self.registry, ctx)
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["NETWORK_DENIED"], findings)

    def test_allowlisted_network_host_accepted(self):
        req = self.make_request("env.bootstrap-known-hosts@v1", "n3", network_hosts=["github.com"],
                                 args={"host": "github.com"})
        ctx = self.default_ctx(network_allowed_hosts={"github.com"})
        ok, findings, _ = rd.preflight(req, self.registry, ctx)
        self.assertTrue(ok, findings)


# ---------------------------------------------------------------------------
# 8. Timeout / cancel
# ---------------------------------------------------------------------------

class TimeoutCancelTests(DispatchTestCase):
    def test_timeout_marks_failed_with_finding(self):
        def slow(ctx):
            time.sleep(2)
            return rd.ExecOutcome("succeeded")

        self.dispatcher.handlers["runner.discovery@v1"] = slow
        req = self.make_request("runner.discovery@v1", "t1", timeout=1)
        self.publish("agentA", "t1", req)
        result = self.dispatcher.claim_and_execute("t1", "w1", self.default_ctx())
        self.assertEqual(result["status"], "failed")
        self.assertIn(rd.FINDING["TIMEOUT"], result["findings"])

    def test_cancel_flag_marks_cancelled(self):
        release = threading.Event()

        def coop(ctx):
            for _ in range(50):
                if ctx.is_cancelled():
                    release.set()
                    return rd.ExecOutcome("cancelled", findings=[rd.FINDING["CANCELLED"]])
                time.sleep(0.02)
            return rd.ExecOutcome("succeeded")

        self.dispatcher.handlers["runner.discovery@v1"] = coop
        req = self.make_request("runner.discovery@v1", "t2", timeout=5)
        self.publish("agentA", "t2", req)

        def do_execute():
            self.result = self.dispatcher.claim_and_execute("t2", "w1", self.default_ctx())

        th = threading.Thread(target=do_execute)
        th.start()
        time.sleep(0.05)
        self.dispatcher.cancel("t2")
        th.join(timeout=5)
        self.assertTrue(release.wait(timeout=2))
        self.assertEqual(self.result["status"], "cancelled")


# ---------------------------------------------------------------------------
# 9. Partial mutation / crash / restart
# ---------------------------------------------------------------------------

class PartialMutationCrashTests(DispatchTestCase):
    def test_crashing_handler_writes_no_partial_git_state(self):
        before = self.repo.tip("refs/heads/main")

        def boom(ctx):
            raise RuntimeError("simulated mid-mutation crash")

        self.dispatcher.handlers["git.base-branch@v1"] = boom
        req = self.make_request(
            "git.base-branch@v1", "p1",
            args={"item_id": "0099-01", "parent_branch": "main", "expected_parent_tip": self.repo.main_tip},
            write_scopes=["ref:refs/heads/0099-01"],
        )
        self.publish("agentA", "p1", req)
        result = self.dispatcher.claim_and_execute("p1", "w1", self.default_ctx())
        self.assertEqual(result["status"], "failed")
        self.assertIn("RD-HANDLER-EXCEPTION", result["findings"])
        self.assertEqual(self.repo.tip("refs/heads/main"), before)
        branch_exists = subprocess.run(
            ["git", "-C", str(self.repo.path), "rev-parse", "--verify", "--quiet", "refs/heads/0099-01"],
            capture_output=True,
        ).returncode
        self.assertNotEqual(branch_exists, 0)

    def test_reclaim_stale_lease_after_simulated_crash(self):
        req = self.make_request("runner.discovery@v1", "p2")
        self.publish("agentA", "p2", req)
        past = datetime.now(timezone.utc) - timedelta(seconds=10)
        self.runner_root.claim("p2", "worker-dead", lease_seconds=1, now=past)
        # No result was ever written (simulated crash mid-execution).
        self.assertIsNone(self.runner_root.read_result("p2"))
        reclaimed = self.runner_root.reclaim_stale_leases()
        self.assertIn("p2", reclaimed)
        # Now it can be reclaimed by a fresh worker.
        self.runner_root.claim("p2", "worker-fresh")
        self.assertIsNotNone(self.runner_root.read_lease("p2"))


# ---------------------------------------------------------------------------
# 10. Tampered result
# ---------------------------------------------------------------------------

class TamperedResultTests(DispatchTestCase):
    def test_tampering_with_result_is_detected(self):
        req = self.make_request("runner.discovery@v1", "tr1")
        self.publish("agentA", "tr1", req)
        self.dispatcher.claim_and_execute("tr1", "w1", self.default_ctx())
        self.assertTrue(self.runner_root.verify_result_untampered("tr1"))
        path = self.runner_root.result_path("tr1")
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["status"] = "succeeded" if obj["status"] != "succeeded" else "failed"
        path.write_text(json.dumps(obj), encoding="utf-8")
        self.assertFalse(self.runner_root.verify_result_untampered("tr1"))

    def test_result_is_write_once_immutable(self):
        req = self.make_request("runner.discovery@v1", "tr2")
        self.publish("agentA", "tr2", req)
        self.dispatcher.claim_and_execute("tr2", "w1", self.default_ctx())
        with self.assertRaises(rd.RunnerDispatchError):
            self.runner_root.write_result("tr2", {
                "schema": "runner-result@v1", "request_id": "tr2", "status": "succeeded",
                "started_at": rd.now_iso(), "finished_at": rd.now_iso(),
                "base_observed": self.repo.main_tip, "authority_epoch_observed": "legacy-writable",
                "outputs": [], "findings": [],
            })


# ---------------------------------------------------------------------------
# 11. Retry
# ---------------------------------------------------------------------------

class RetryTests(DispatchTestCase):
    def test_duplicate_idempotence_key_after_success_is_rejected(self):
        req1 = self.make_request("runner.discovery@v1", "ry1", idempotence_suffix="same-key")
        self.publish("agentA", "ry1", req1)
        r1 = self.dispatcher.claim_and_execute("ry1", "w1", self.default_ctx())
        self.assertEqual(r1["status"], "succeeded")

        req2 = self.make_request("runner.discovery@v1", "ry2", idempotence_suffix="same-key")
        self.publish("agentA", "ry2", req2)
        r2 = self.dispatcher.claim_and_execute("ry2", "w2", self.default_ctx())
        self.assertEqual(r2["status"], "rejected")
        self.assertIn(rd.FINDING["DUPLICATE_IDEMPOTENCE"], r2["findings"])

    def test_retry_after_failure_is_allowed_and_linked(self):
        def boom(ctx):
            raise RuntimeError("fails once")

        self.dispatcher.handlers["runner.discovery@v1"] = boom
        req1 = self.make_request("runner.discovery@v1", "ry3", idempotence_suffix="retry-key")
        self.publish("agentA", "ry3", req1)
        r1 = self.dispatcher.claim_and_execute("ry3", "w1", self.default_ctx())
        self.assertEqual(r1["status"], "failed")

        del self.dispatcher.handlers["runner.discovery@v1"]
        req2 = self.make_request("runner.discovery@v1", "ry4", idempotence_suffix="retry-key")
        self.publish("agentA", "ry4", req2)
        r2 = self.dispatcher.claim_and_execute("ry4", "w2", self.default_ctx())
        self.assertEqual(r2["status"], "succeeded")
        self.assertEqual(r2.get("retry_of"), "ry3")


# ---------------------------------------------------------------------------
# 12. Every Git/ref action's rollback
# ---------------------------------------------------------------------------

class GitRefActionTests(DispatchTestCase):
    def test_base_branch_succeeds_and_creates_identical_tree(self):
        req = self.make_request(
            "git.base-branch@v1", "g1",
            args={"item_id": "0099-01", "parent_branch": "main", "expected_parent_tip": self.repo.main_tip},
            write_scopes=["ref:refs/heads/0099-01"],
        )
        self.publish("agentA", "g1", req)
        result = self.dispatcher.claim_and_execute("g1", "w1", self.default_ctx())
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(self.repo.tip("refs/heads/0099-01"), self.repo.main_tip)

    def test_base_branch_rejects_on_stale_parent_tip(self):
        req = self.make_request(
            "git.base-branch@v1", "g2",
            args={"item_id": "0099-02", "parent_branch": "main", "expected_parent_tip": "c" * 40},
            write_scopes=["ref:refs/heads/0099-02"],
        )
        self.publish("agentA", "g2", req)
        result = self.dispatcher.claim_and_execute("g2", "w1", self.default_ctx())
        self.assertEqual(result["status"], "rejected")
        exists = subprocess.run(
            ["git", "-C", str(self.repo.path), "rev-parse", "--verify", "--quiet", "refs/heads/0099-02"],
            capture_output=True,
        ).returncode
        self.assertNotEqual(exists, 0)

    def test_merge_prereqs_conflict_leaves_target_branch_untouched(self):
        item_tip = self.repo.branch("0099-03")
        branch_a = self.repo.branch("0099-src-a", at=item_tip)
        self.repo.commit_on("0099-src-a", "conflict.txt", "A-version\n", "a-version")
        tip_a = self.repo.tip("refs/heads/0099-src-a")
        branch_b = self.repo.branch("0099-src-b", at=item_tip)
        self.repo.commit_on("0099-src-b", "conflict.txt", "B-version\n", "b-version")
        tip_b = self.repo.tip("refs/heads/0099-src-b")

        before = self.repo.tip("refs/heads/0099-03")
        req = self.make_request(
            "git.merge-prereqs@v1", "g3",
            args={
                "item_id": "0099-03", "expected_base": before,
                "sources": [{"branch": "0099-src-a", "tip": tip_a}, {"branch": "0099-src-b", "tip": tip_b}],
            },
            write_scopes=["conflict.txt"],
        )
        self.publish("agentA", "g3", req)
        result = self.dispatcher.claim_and_execute("g3", "w1", self.default_ctx())
        self.assertEqual(result["status"], "failed")
        self.assertIn(rd.FINDING["MERGE_CONFLICT"], result["findings"])
        self.assertEqual(self.repo.tip("refs/heads/0099-03"), before)

    def test_merge_prereqs_sequential_success(self):
        item_tip = self.repo.branch("0099-04")
        src1 = self.repo.branch("0099-src1", at=item_tip)
        self.repo.commit_on("0099-src1", "one.txt", "1\n", "one")
        tip1 = self.repo.tip("refs/heads/0099-src1")
        src2 = self.repo.branch("0099-src2", at=item_tip)
        self.repo.commit_on("0099-src2", "two.txt", "2\n", "two")
        tip2 = self.repo.tip("refs/heads/0099-src2")

        req = self.make_request(
            "git.merge-prereqs@v1", "g4",
            args={
                "item_id": "0099-04", "expected_base": item_tip,
                "sources": [{"branch": "0099-src1", "tip": tip1}, {"branch": "0099-src2", "tip": tip2}],
            },
            write_scopes=["one.txt", "two.txt"],
        )
        self.publish("agentA", "g4", req)
        result = self.dispatcher.claim_and_execute("g4", "w1", self.default_ctx())
        self.assertEqual(result["status"], "succeeded")
        self.assertNotEqual(self.repo.tip("refs/heads/0099-04"), item_tip)

    def test_integrate_checkpoint_requires_privileged_capability(self):
        feature_tip = self.repo.branch("0099")
        src = self.repo.branch("0099-05", at=feature_tip)
        self.repo.commit_on("0099-05", "x.txt", "x\n", "x")
        req = self.make_request(
            "git.integrate-checkpoint@v1", "g5",
            args={"item_id": "0099", "target_kind": "feature", "expected_base": feature_tip, "source_branch": "0099-05"},
            write_scopes=["x.txt"],
        )
        self.publish("agentA", "g5", req)
        ctx = self.default_ctx(capability_class="sandboxed-grunt")
        result = self.dispatcher.claim_and_execute("g5", "w1", ctx)
        self.assertEqual(result["status"], "rejected")
        self.assertIn(rd.FINDING["AUTHORITY_VIOLATION"], result["findings"])
        self.assertEqual(self.repo.tip("refs/heads/0099"), feature_tip)

    def test_integrate_checkpoint_succeeds_for_privileged(self):
        feature_tip = self.repo.branch("0099f")
        self.repo.branch("0099f-01", at=feature_tip)
        self.repo.commit_on("0099f-01", "y.txt", "y\n", "y")
        req = self.make_request(
            "git.integrate-checkpoint@v1", "g6",
            args={"item_id": "0099f", "target_kind": "feature", "expected_base": feature_tip, "source_branch": "0099f-01"},
            write_scopes=["y.txt"],
        )
        self.publish("agentA", "g6", req)
        ctx = self.default_ctx(capability_class="privileged")
        result = self.dispatcher.claim_and_execute("g6", "w1", ctx)
        self.assertEqual(result["status"], "succeeded")
        self.assertNotEqual(self.repo.tip("refs/heads/0099f"), feature_tip)

    def test_rollback_ref_cleanup_restores_ref(self):
        moved = self.repo.branch("0099-mv")
        new_tip = self.repo.commit_on("0099-mv", "z.txt", "z\n", "z")
        req = self.make_request(
            "git.rollback-ref-cleanup@v1", "g7",
            args={"ref": "refs/heads/0099-mv", "expected_current": new_tip, "restore_to": moved},
            write_scopes=["ref:refs/heads/0099-mv"],
        )
        self.publish("agentA", "g7", req)
        result = self.dispatcher.claim_and_execute("g7", "w1", self.default_ctx())
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(self.repo.tip("refs/heads/0099-mv"), moved)

    def test_approval_ref_create_append_cas_rejects_stale_current(self):
        req = self.make_request(
            "approval.ref-create-append-cas@v1", "g8",
            args={"ref": "refs/autodocs/approval/0037-99", "expected_current": "d" * 40, "new_value": self.repo.main_tip},
            write_scopes=["ref:refs/autodocs/approval/0037-99"],
        )
        ctx = self.default_ctx(capability_class="privileged", credential_store=set())
        self.publish("agentA", "g8", req)
        result = self.dispatcher.claim_and_execute("g8", "w1", ctx)
        self.assertEqual(result["status"], "rejected")

    def test_approval_ref_create_append_cas_creates_new_ref(self):
        req = self.make_request(
            "approval.ref-create-append-cas@v1", "g9",
            args={"ref": "refs/autodocs/approval/0037-98", "expected_current": "", "new_value": self.repo.main_tip},
            write_scopes=["ref:refs/autodocs/approval/0037-98"],
        )
        ctx = self.default_ctx(capability_class="privileged")
        self.publish("agentA", "g9", req)
        result = self.dispatcher.claim_and_execute("g9", "w1", ctx)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(self.repo.tip("refs/autodocs/approval/0037-98"), self.repo.main_tip)


# ---------------------------------------------------------------------------
# 13. Claim retention
# ---------------------------------------------------------------------------

class ClaimRetentionTests(DispatchTestCase):
    def test_lease_persists_until_result_then_can_be_released(self):
        req = self.make_request("runner.discovery@v1", "cr1")
        self.publish("agentA", "cr1", req)
        self.runner_root.claim("cr1", "w1")
        self.assertIsNotNone(self.runner_root.read_lease("cr1"))
        # Release the pre-existing manual claim so claim_and_execute can re-claim it.
        self.runner_root.release_claim("cr1")
        # a fresh claim/execute cycle is now possible
        result = self.dispatcher.claim_and_execute("cr1", "w2", self.default_ctx())
        self.assertEqual(result["status"], "succeeded")

    def test_claim_finalize_rejects_foreign_owner_token(self):
        claim_file = self.repo.tmp / "TODO-foreign-0099-abc.md"
        claim_file.write_text("owner_token: agent:other:0099:abc\n", encoding="utf-8")
        req = self.make_request(
            "claim.finalize@v1", "cr2",
            args={"claim_path": str(claim_file), "owner_token": "agent:me:0099:xyz", "expected_state": "[x]"},
            write_scopes=[str(claim_file.name)],
        )
        self.publish("agentA", "cr2", req)
        result = self.dispatcher.claim_and_execute("cr2", "w1", self.default_ctx())
        self.assertEqual(result["status"], "rejected")
        self.assertIn(rd.FINDING["CLAIM_FOREIGN_TOKEN"], result["findings"])


# ---------------------------------------------------------------------------
# 14. Schema validity / registry integrity (supporting coverage)
# ---------------------------------------------------------------------------

class SchemaAndRegistryTests(DispatchTestCase):
    def test_malformed_request_rejected_by_schema(self):
        req = self.make_request("runner.discovery@v1", "sc1")
        del req["expected_base"]
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["SCHEMA_INVALID"], findings)

    def test_registry_actions_cover_every_manifest_category(self):
        categories = {a["category"] for a in self.registry.raw["actions"]}
        for expected in ("context", "action", "approval-readiness", "evidence", "recovery", "validation"):
            self.assertIn(expected, categories)

    def test_missing_required_argument_rejected(self):
        req = self.make_request("git.base-branch@v1", "sc2", args={})
        req["preflight"] = ["typed-action:git.base-branch@v1"]
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx())
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["MISSING_ARG"], findings)

    def test_secret_like_value_in_request_is_rejected(self):
        req = self.make_request("sign.create@v1", "sc3", args={
            "credential_handle": "-----BEGIN PRIVATE KEY----- abc",
            "payload_digest": "sha256:" + "0" * 64,
        })
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx(capability_class="privileged"))
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["SECRET_LEAK"], findings)

    def test_governance_path_write_rejected_without_governance_authority(self):
        req = self.make_request(
            "claim.finalize@v1", "sc4", write_scopes=["AGENTS.md"],
            args={"claim_path": "x", "owner_token": "agent:a:1:1", "expected_state": "[x]"},
        )
        ok, findings, _ = rd.preflight(req, self.registry, self.default_ctx(governance_write_ok=False))
        self.assertFalse(ok)
        self.assertIn(rd.FINDING["GOVERNANCE_SCOPE"], findings)


if __name__ == "__main__":
    unittest.main()
