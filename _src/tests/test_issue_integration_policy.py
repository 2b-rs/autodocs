#!/usr/bin/env python3
"""Adversarial tests for the non-bypassable issue integration gate."""
import importlib.util, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

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
        for name in ("legacy", "future"):
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
