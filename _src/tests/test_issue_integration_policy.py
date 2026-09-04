#!/usr/bin/env python3
"""Adversarial tests for the non-bypassable issue integration gate."""
import importlib.util, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("issue_integration_policy", ROOT / "_src/tools/issue_integration_policy.py")
POL = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(POL)

class IssueIntegrationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q"); self.git("config", "user.email", "test@example.invalid"); self.git("config", "user.name", "Test")
        (self.root / "_src/tools").mkdir(parents=True)
        shutil.copy2(ROOT / "_src/tools/agent_bootstrap.py", self.root / "_src/tools/agent_bootstrap.py")
        for name in ("legacy", "current", "future"):
            dest = self.root / f"docs/pipeline/agent-instructions/{name}/index.md"; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f"docs/pipeline/agent-instructions/{name}/index.md", dest)
        self.write_legacy(); self.base = self.commit("base")

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=check)

    def commit(self, message):
        self.git("add", "-A"); self.git("commit", "-q", "-m", message, "--allow-empty")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def write_legacy(self, **updates):
        value = dict(POL.LEGACY_V1_CONTRACT); value["selector_digest"] = "sha256:" + "a" * 64; value.update(updates)
        (self.root / "agent-workflow.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))

    def write_v2(self, **updates):
        bundle = "docs/pipeline/agent-instructions/future/index.md"
        value = {"schema":"agent-workflow-bootstrap@v2","workflow_version":"2.0.0",
                 "authority_epoch":"issue-store-writable","authority_profile":"issue-store",
                 "write_phase":"issue-store-writable","required_capability":"unprivileged",
                 "execution_model":"direct","instruction_bundle":{"path":bundle,"members":POL.validate_instruction_bundle(self.root,bundle)}}
        value.update(updates); value["selector_digest"] = POL.compute_selector_digest(value)
        (self.root / "agent-workflow.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))

    def write_frozen(self):
        bundle = "docs/pipeline/agent-instructions/current/index.md"
        value = {"schema":"agent-workflow-bootstrap@v2","workflow_version":"2.0.0",
                 "authority_epoch":"legacy-frozen","authority_profile":"legacy-lists",
                 "write_phase":"frozen","required_capability":"unprivileged",
                 "execution_model":"direct","instruction_bundle":{"path":bundle,"members":POL.validate_instruction_bundle(self.root,bundle)}}
        value["selector_digest"] = POL.compute_selector_digest(value)
        (self.root / "agent-workflow.json").write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))

    def evaluate(self, base=None, candidate=None, enforce=True):
        return POL.evaluate_integration_policy(self.root, base_ref=base or self.base,
            candidate_ref=candidate or "HEAD", enforce_rules=enforce)

    def test_live_legacy_placeholder_candidate_passes_only_exact_contract(self):
        (self.root/"TODO.md").write_text("# conforming\n"); candidate=self.commit("legacy")
        result=self.evaluate(candidate=candidate); self.assertEqual("passed",result["status"])

    def test_placeholder_rejects_every_noncanonical_legacy_tuple(self):
        fields={"workflow_version":"9.9.9","authority_epoch":"legacy-restored","authority_profile":"issue-store",
                "write_phase":"frozen","required_capability":"invented","runner_protocol":"invented@v9",
                "instruction_bundle":"docs/pipeline/agent-instructions/future/index.md"}
        for field,value in fields.items():
            with self.subTest(field=field):
                self.git("reset","--hard",self.base); self.write_legacy(**{field:value}); bad=self.commit(field)
                with self.assertRaises(POL.IntegrationPolicyViolation): self.evaluate(candidate=bad)

    def test_v2_binds_selector_and_complete_bundle_member_digests(self):
        self.write_v2(); good=self.commit("v2"); self.assertEqual("passed",self.evaluate(candidate=good)["status"])
        for mutation in ("selector","member","missing"):
            with self.subTest(mutation=mutation):
                self.git("reset","--hard",good); value=json.loads((self.root/"agent-workflow.json").read_text())
                if mutation=="selector": value["selector_digest"]="sha256:"+"0"*64
                elif mutation=="member":
                    key=next(iter(value["instruction_bundle"]["members"])); value["instruction_bundle"]["members"][key]="sha256:"+"0"*64
                    value["selector_digest"]=POL.compute_selector_digest(value)
                else:
                    value["instruction_bundle"]["members"]={}; value["selector_digest"]=POL.compute_selector_digest(value)
                (self.root/"agent-workflow.json").write_text(json.dumps(value)); bad=self.commit(mutation)
                with self.assertRaises(POL.IntegrationPolicyViolation): self.evaluate(base=good,candidate=bad)

    def test_v2_rejects_unsupported_metadata_and_false_policy_fields(self):
        cases=(("workflow_version","9.9.9"),("required_capability","invented"),("execution_model","queue"),
               ("transaction_id","wrong"),("policy_digest","sha256:"+"0"*64))
        for field,value in cases:
            with self.subTest(field=field):
                self.git("reset","--hard",self.base); self.write_v2(**{field:value}); bad=self.commit(field)
                with self.assertRaises(POL.IntegrationPolicyViolation): self.evaluate(candidate=bad)

    def test_issue_store_rejects_generated_and_legacy_claim_edits(self):
        self.write_v2(); (self.root/"TODO.md").write_text("bad"); (self.root/"TODO-worf.md").write_text("bad")
        result=self.evaluate(candidate=self.commit("bad"),enforce=False)
        self.assertEqual(("rejected",2),(result["status"],result["violations_count"]))

    def test_frozen_rejects_ordinary_claim_and_backlog_with_stable_codes(self):
        self.write_frozen(); self.base=self.commit("frozen")
        for path,code in (("TODO-stale-client-after-freeze.md","POLICY-FROZEN-LEGACY-CLAIM-PROHIBITED"),
                          ("DONE-ordinary-worker.md","POLICY-FROZEN-LEGACY-CLAIM-PROHIBITED"),
                          ("TODO.md","POLICY-FROZEN-BACKLOG-EDIT-PROHIBITED"),
                          ("DONE.md","POLICY-FROZEN-BACKLOG-EDIT-PROHIBITED")):
            with self.subTest(path=path):
                self.git("reset","--hard",self.base); (self.root/path).write_text("mutation\n"); candidate=self.commit(path)
                result=self.evaluate(candidate=candidate,enforce=False)
                self.assertEqual(code,result["violations"][0]["code"])

    def test_frozen_exact_closure_proof_is_the_only_backlog_exception(self):
        self.write_frozen(); self.base=self.commit("frozen")
        paths = POL.runner_transaction.FROZEN_CLOSURE_MUTATION_PATHS
        for path in paths:
            target = self.root/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_text("exact closure\n")
        manifest = self.root/POL.FROZEN_CLOSURE_MANIFEST; manifest.parent.mkdir(parents=True,exist_ok=True); manifest.write_text("{}\n")
        candidate=self.commit("closure")
        with mock.patch.object(POL.runner_transaction,"verify_frozen_closure_delta",return_value={"status":"passed"}):
            self.assertEqual("passed",self.evaluate(candidate=candidate)["status"])
        with mock.patch.object(POL.runner_transaction,"verify_frozen_closure_delta",side_effect=POL.runner_transaction.FrozenClosureViolation("FCD-BINDING","stale","manifest")):
            result=self.evaluate(candidate=candidate,enforce=False)
            self.assertEqual("POLICY-FROZEN-CLOSURE-FCD-BINDING",result["violations"][0]["code"])

    def test_frozen_cutover_claim_requires_machine_verifiable_authority_binding(self):
        self.write_frozen(); self.base=self.commit("frozen")
        path=self.root/"TODO-wesley-0037-30-recovery.md"
        path.write_text("task: 0037-30\n"); missing=self.commit("missing proof")
        result=self.evaluate(candidate=missing,enforce=False)
        self.assertEqual("POLICY-FROZEN-AUTHORITY-PROOF-REQUIRED",result["violations"][0]["code"])
        self.git("reset","--hard",self.base)
        path.write_text("task: 0037-30\nassignment: 1788479030641-5c11cf8d\nowner_token: agent:wesley:0037-30:1788479030641-5c11cf8d\n")
        allowed=self.commit("bound proof")
        self.assertEqual("passed",self.evaluate(candidate=allowed)["status"])

    def test_frozen_adjacent_cutover_evidence_and_metadata_are_allowed(self):
        self.write_frozen(); self.base=self.commit("frozen")
        evidence=self.root/"docs/dossiers/0037-31-recovery.md"; evidence.parent.mkdir(parents=True,exist_ok=True)
        evidence.write_text("task: 0037-31\nassignment: 1788479030641-5c11cf8d\n")
        json_evidence=self.root/"provenance/migrations/issue-store/0037-31-recovery.json"; json_evidence.parent.mkdir(parents=True,exist_ok=True)
        json_evidence.write_text('{"task_id":"0037-31","assignment_id":"1788479030641-5c11cf8d"}\n')
        paired_markdown=self.root/"provenance/migrations/issue-store/0037-31-recovery.md"
        paired_markdown.write_text("# 0037-31 signed report companion\n")
        claim=self.root/"TODO-wesley-0037-31-recovery.md"
        claim.write_text("task: 0037-31\nassignment: 1788479030641-5c11cf8d\nowner_token: agent:wesley:0037-31:1788479030641-5c11cf8d\n")
        metadata=self.root/"_src/tests/test_issue_integration_policy.py"; metadata.parent.mkdir(parents=True,exist_ok=True)
        metadata.write_text("metadata\n")
        candidate=self.commit("adjacent allowed")
        self.assertEqual("passed",self.evaluate(candidate=candidate)["status"])

    def test_frozen_path_classifier_exhaustive_finite_domain(self):
        cases = {
            "TODO.md":"legacy-backlog", "DONE.md":"legacy-backlog",
            "TODO-agent.md":"legacy-claim", "DONE-agent.md":"legacy-claim",
            "TODO-wesley-0037-29-x.md":"legacy-claim", "TODO-wesley-0037-41-x.md":"legacy-claim",
            "TODO-wesley-0037-30-x.md":"cutover-record", "DONE-wesley-0037-39-x.md":"cutover-record",
            "TODO-wesley-0037-40-x.md":"cutover-record", "docs/dossiers/0037-30-r.md":"cutover-evidence",
            "docs/dossiers/0037-40-r.md":"cutover-evidence", "docs/dossiers/0037-41-r.md":"unrestricted",
            "provenance/migrations/issue-store/0037-31-r.json":"cutover-evidence",
            "provenance/migrations/issue-store/0037-29-r.json":"unrestricted",
            "agent-workflow.json":"epoch-metadata", ".github/workflows/issue-policy.yml":"epoch-metadata",
            "_src/tools/issue_integration_policy.py":"epoch-metadata",
            "_src/tests/test_issue_integration_policy.py":"epoch-metadata",
            "_src/output/issue-migration/items.json":"migration-output", "issues/0037/item.json":"migration-output",
            "src/ordinary.py":"unrestricted", "provenance/TODO-agent.md":"unrestricted",
        }
        self.assertEqual(22,len(cases))
        for path,expected in cases.items():
            with self.subTest(path=path): self.assertEqual(expected,POL.classify_frozen_path(path))

    def test_missing_invalid_and_nonancestor_boundaries_reject(self):
        candidate=self.commit("candidate")
        for kwargs in ({},{"base_ref":"missing","candidate_ref":candidate},{"base_ref":self.base,"candidate_ref":"missing"}):
            with self.subTest(kwargs=kwargs),self.assertRaises(POL.IntegrationPolicyViolation):
                POL.evaluate_integration_policy(self.root,**kwargs)
        self.git("checkout","-q","--orphan","sibling"); self.git("rm","-q","-rf","."); self.write_legacy(); sibling=self.commit("sibling")
        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx: self.evaluate(base=candidate,candidate=sibling)
        self.assertEqual("NON-ANCESTOR-BOUNDARY",ctx.exception.code)

    def test_candidate_identity_and_dirty_tree_reject(self):
        candidate=self.commit("candidate"); self.commit("later")
        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx: self.evaluate(candidate=candidate)
        self.assertEqual("CANDIDATE-TREE-MISMATCH",ctx.exception.code)
        self.git("reset","--hard",candidate); (self.root/"agent-workflow.json").write_text("{}")
        with self.assertRaises(POL.IntegrationPolicyViolation) as ctx: self.evaluate(candidate=candidate)
        self.assertEqual("CANDIDATE-TREE-MISMATCH",ctx.exception.code)

    def test_cli_requires_explicit_refs(self):
        candidate=self.commit("candidate"); tool=str(ROOT/"_src/tools/issue_integration_policy.py")
        missing=subprocess.run([sys.executable,tool,"--root",str(self.root),"--json"],capture_output=True)
        self.assertNotEqual(0,missing.returncode)
        ok=subprocess.run([sys.executable,tool,"--root",str(self.root),"--base-ref",self.base,
                           "--candidate-ref",candidate,"--json"],capture_output=True,text=True)
        self.assertEqual(0,ok.returncode,ok.stderr)

if __name__=="__main__": unittest.main()
