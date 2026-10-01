#!/usr/bin/env python3
"""Hermetic property/refusal matrix for the composed WTP/IP gate."""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOOLS=Path(__file__).resolve().parent
sys.path.insert(0,str(TOOLS))
SPEC=importlib.util.spec_from_file_location("composed",TOOLS/"validate_worktree_integration_plans.py"); assert SPEC and SPEC.loader
composed=importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name]=composed; SPEC.loader.exec_module(composed)


class ComposedGateTests(unittest.TestCase):
    REF="1"*40
    @classmethod
    def setUpClass(cls):
        cls.wtp_schema=json.loads((ROOT/"docs/pipeline/worktree-topology-plan.schema.json").read_text())
        cls.ip_schema=json.loads((ROOT/"docs/pipeline/integration-plan.schema.json").read_text())
        cls.base_wtp=json.loads((ROOT/"docs/pipeline/worktree-topology-plan.template.json").read_text())
        cls.base_ip=json.loads((ROOT/"docs/pipeline/integration-plan.template.json").read_text())

    def plans(self):
        w=copy.deepcopy(self.base_wtp); ip=copy.deepcopy(self.base_ip); b=ip["wtp_binding"]
        b.update(ref=self.REF,content_digest=composed.wtp_tool.content_digest(w),feature_id=w["feature_id"],baseline_ref=w["baseline_ref"],status=w["status"],validation_profile=w["validation_profile"])
        for item in b["consumption"]: item["disposition"]="consumed"
        snap=ip["topology_snapshot"]; snap.update(state="complete",node_ids=[n["node_id"] for n in w["nodes"]],edge_ids=[composed.edge_id(e) for e in w["edges"]],overlap_rule_ids=[composed.overlap_id(x) for x in w["overlap_rules"]],checkpoint_work_units=[x["work_unit"] for x in w["checkpoints"]])
        for c in ip["acceptance_closures"]:
            c["wtp_ref"]=self.REF; c["wtp_digest"]=b["content_digest"]; c["member_manifest_digest"]=composed.digest(c["members"]); c["closure_digest"]=composed.digest(c,{"closure_digest","audit_timestamp"})
        ip["content_digest"]=composed.digest(ip,{"content_digest"})
        return ip,w

    def report(self,mutate=None):
        ip,w=self.plans()
        if mutate: mutate(ip,w)
        ip["content_digest"]=composed.digest(ip,{"content_digest"})
        return composed.validate(ip,w,self.ip_schema,self.wtp_schema,wtp_ref=self.REF)

    def codes(self,mutate=None): return {x["code"] for x in self.report(mutate)["findings"]}

    def test_positive_dormant_plan_and_canonical_carriage_equivalence(self):
        ip,w=self.plans(); reverse=dict(reversed(list(ip.items())))
        self.assertEqual(composed.digest(ip,{"content_digest"}),composed.digest(reverse,{"content_digest"}))
        reverse["content_digest"]=composed.digest(reverse,{"content_digest"})
        self.assertTrue(composed.validate(reverse,w,self.ip_schema,self.wtp_schema,wtp_ref=self.REF)["valid"])

    def test_identity_ref_digest_version_feature_baseline_status_matrix(self):
        cases=[
            (lambda i,w:i["wtp_binding"].update(ref="2"*40),"WIP-WTP-REF-MISMATCH"),
            (lambda i,w:i["wtp_binding"].update(content_digest="sha256:"+"2"*64),"WIP-WTP-DIGEST-MISMATCH"),
            (lambda i,w:i["wtp_binding"].update(schema_version="broken"),"WIP-WTP-VERSION-MISMATCH"),
            (lambda i,w:i.update(feature_id="9999"),"WIP-FEATURE-MISMATCH"),
            (lambda i,w:i.update(baseline_ref="2"*40),"WIP-BASELINE-MISMATCH"),
            (lambda i,w:(w.update(status="withdrawn"),i["wtp_binding"].update(status="withdrawn",supersession_compatibility="withdrawn")),"WIP-WTP-INVALID")]
        for mutation,code in cases:
            with self.subTest(code=code): self.assertIn(code,self.codes(mutation))

    def test_partial_node_edge_overlap_checkpoint_and_consumption(self):
        cases=[("node_ids","WIP-NODE-CONSUMPTION"),("edge_ids","WIP-EDGE-CONSUMPTION"),("checkpoint_work_units","WIP-CHECKPOINT-CONSUMPTION")]
        for key,code in cases:
            with self.subTest(code=code): self.assertIn(code,self.codes(lambda i,w,k=key:i["topology_snapshot"][k].clear()))
        self.assertIn("WIP-CONSUMPTION-INCOMPLETE",self.codes(lambda i,w:i["wtp_binding"]["consumption"].pop()))

    def test_undeclared_reconciliation_and_unknown_overlap(self):
        self.assertIn("WIP-RECONCILIATION-UNDECLARED",self.codes(lambda i,w:i["steps"][0].update(reconciliation_alternative="novel")))
        self.assertIn("WIP-OVERLAP-UNKNOWN",self.codes(lambda i,w:i["steps"][0].update(overlap_rule="unknown")))

    def test_absorption_order_and_unresolved_consequential_pin(self):
        def unordered(i,w): i["steps"][0].update(operation="absorb-prerequisite",prerequisite_order=[])
        self.assertIn("WIP-ABSORPTION-ORDER",self.codes(unordered))
        def unresolved(i,w): i.update(status="ready"); i["steps"][0].update(consequential=True,state="ready")
        self.assertIn("WIP-PIN-UNRESOLVED",self.codes(unresolved))
        self.assertIn("WIP-ABSORPTION-UNREACHABLE",self.codes(lambda i,w:i["steps"][0].update(operation="absorb-prerequisite",prerequisite_order=["task:9999-01"])))

    def test_unreachable_ref_is_refused(self):
        ip,w=self.plans(); report=composed.validate(ip,w,self.ip_schema,self.wtp_schema,wtp_ref=self.REF,ref_checker=lambda _:False)
        self.assertIn("WIP-REF-UNREACHABLE",{x["code"] for x in report["findings"]})

    def test_sequential_overlap_pass_and_concurrent_collision_fail(self):
        ip,w=self.plans(); self.assertTrue(composed.validate(ip,w,self.ip_schema,self.wtp_schema,wtp_ref=self.REF)["valid"])
        def overlap(i,w,klass):
            rule={"left":"main-root","right":"task-0000-01","class":klass,"paths":[{"match":"prefix","path":"example/0000-01"}],"order":"main then task","authority":"test","evidence_required":["test"]}; w["nodes"][0]["write_scope"]=[{"match":"prefix","path":"example/0000-01"}]; w["overlap_rules"]=[rule]; w["content_digest"]=composed.wtp_tool.content_digest(w); rid=composed.overlap_id(rule); i["wtp_binding"]["content_digest"]=w["content_digest"]; i["topology_snapshot"]["overlap_rule_ids"]=[rid]; i["steps"][0].update(overlap_rule=rid,state="ready",prerequisite_order=["task:0000-01"])
            for c in i["acceptance_closures"]: c["wtp_digest"]=w["content_digest"]; c["closure_digest"]=composed.digest(c,{"closure_digest","audit_timestamp"})
        def collision(i,w): overlap(i,w,"concurrent-exclusive")
        self.assertIn("WIP-CONCURRENT-COLLISION",self.codes(collision))
        def sequential(i,w): overlap(i,w,"ordered-predecessor")
        self.assertNotIn("WIP-CONCURRENT-COLLISION",self.codes(sequential))

    def test_closure_digest_manifest_candidate_and_invalidation_matrix(self):
        def current_member(i,w):
            c=i["acceptance_closures"][0]; c["state"]="current"; c["integration_target_pin"]={"state":"exact","ref":"3"*40}; c["members"]=[{"work_unit":"task:0000-01","candidate_ref":"3"*40,"candidate_tree_digest":"sha256:"+"3"*64,"contract_ref":"4"*40,"contract_digest":"sha256:"+"4"*64,"disposition":"completed","bookkeeping_ref":"5"*40,"claim_ref":"6"*40,"acceptance_ref":"7"*40,"acceptance_record_digest":"sha256:"+"7"*64,"accepted_candidate_ref":"3"*40,"reviewer_identity":"agent:test:reviewer:one","authority_ref":"AUTH","invalidation_state":"current","evidence_manifest_ref":"8"*40,"evidence_manifest_digest":"sha256:"+"8"*64}]; c["member_manifest_digest"]=composed.digest(c["members"]); c["closure_digest"]=composed.digest(c,{"closure_digest","audit_timestamp"})
        ip,w=self.plans(); current_member(ip,w); ip["content_digest"]=composed.digest(ip,{"content_digest"}); self.assertTrue(composed.validate(ip,w,self.ip_schema,self.wtp_schema,wtp_ref=self.REF)["valid"])
        def stale(i,w): current_member(i,w); i["acceptance_closures"][0]["members"][0]["invalidation_state"]="invalidated"
        self.assertIn("WIP-ACCEPTANCE-NOT-CURRENT",self.codes(stale))
        def mismatch(i,w): current_member(i,w); i["acceptance_closures"][0]["members"][0]["accepted_candidate_ref"]="9"*40
        self.assertIn("WIP-ACCEPTANCE-CANDIDATE-MISMATCH",self.codes(mismatch))

    def test_refresh_event_pass_and_structural_drift_requires_revision(self):
        def refresh(i,w):
            e={"event_id":"refresh-1","sequence":1,"event_type":"refresh","stale_class":"source-tip","old_pin":"1"*40,"new_pin":"2"*40,"reason":"runtime tip advanced","ancestry_result":"ancestor","overlap_result":"unchanged","closure_result":"recomputed","hygiene_result":"pass","actor_identity":"agent:test:integrator:one","evidence_ref":"E1","evidence_digest":"sha256:"+"1"*64,"event_digest":"","created_at":"2026-08-24T20:00:00Z"}; e["event_digest"]=composed.digest(e,{"event_digest","created_at"}); i["events"].append(e)
        ip,w=self.plans(); refresh(ip,w); ip["content_digest"]=composed.digest(ip,{"content_digest"}); self.assertTrue(composed.validate(ip,w,self.ip_schema,self.wtp_schema,wtp_ref=self.REF)["valid"])
        codes=self.codes(lambda i,w:w["nodes"][1].update(branch="structural-drift")); self.assertIn("WIP-WTP-DIGEST-MISMATCH",codes); self.assertIn("WIP-REVISION-REQUIRED",codes)

    def test_checkpoint_and_test_profile_cannot_be_skipped(self):
        self.assertIn("WIP-CHECKPOINT-SKIPPED",self.codes(lambda i,w:i["steps"][-1].update(checkpoint_work_unit="none")))
        def skip_profile(i,w):
            for s in i["steps"]: s["validation"]=[{"command":"unrelated","baseline":"x","environment":"x","expected_exit":0,"evidence_ref":"x"}]
        self.assertIn("WIP-TEST-PROFILE-SKIPPED",self.codes(skip_profile))

    def test_final_main_position_preflight_authority_and_dormant_execution(self):
        self.assertIn("WIP-FINAL-MAIN-POSITION",self.codes(lambda i,w:i["steps"].reverse()))
        self.assertIn("WIP-FINAL-MAIN-PREFLIGHT",self.codes(lambda i,w:i["steps"][-1].update(hygiene=[{"command":"clean","baseline":"x","environment":"x","expected_exit":0,"evidence_ref":"x"}])))
        def execute(i,w): i["steps"][-1].update(consequential=True,state="ready",source_pin={"state":"exact","ref":"1"*40},target_pin_before={"state":"exact","ref":"2"*40},target_tree_before={"state":"exact","ref":"3"*40})
        codes=self.codes(execute); self.assertIn("WIP-DORMANT-CONSEQUENTIAL",codes); self.assertIn("WIP-FINAL-MAIN-AUTHORITY",codes); self.assertIn("WIP-ACCEPTANCE-BLOCKING",codes)

    def test_normalized_digest_is_stable(self):
        a=self.report(); b=self.report(); self.assertEqual(a["closure_set_digest"],b["closure_set_digest"])

    def test_refusal_manifest_covers_every_declared_literal_code(self):
        manifest=json.loads((TOOLS/"fixtures/worktree-integration-plans/refusal-matrix.json").read_text())
        source=(TOOLS/"validate_worktree_integration_plans.py").read_text()
        literals=set(re.findall(r'"(WIP-[A-Z0-9_-]+)"',source))
        dynamic={"WIP-IP-SCHEMA","WIP-WTP-SCHEMA","WIP-WTP-SEMANTIC-"}
        self.assertEqual(literals-dynamic,set(manifest["codes"]))

    def test_cli_has_zero_undeclared_side_effects(self):
        ref=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
        ip,w=self.plans(); ip["wtp_binding"]["ref"]=ref
        for c in ip["acceptance_closures"]:
            c["wtp_ref"]=ref; c["closure_digest"]=composed.digest(c,{"closure_digest","audit_timestamp"})
        ip["content_digest"]=composed.digest(ip,{"content_digest"})
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td); ip_path=tmp/"ip.json"; wtp_path=tmp/"wtp.json"; dirty=tmp/"foreign-dirty.txt"
            ip_path.write_text(json.dumps(ip)); wtp_path.write_text(json.dumps(w)); dirty.write_bytes(b"preserve-me\n")
            before={p.name:p.read_bytes() for p in tmp.iterdir()}
            proc=subprocess.run([sys.executable,str(TOOLS/"validate_worktree_integration_plans.py"),str(ip_path),str(wtp_path),"--ip-schema",str(ROOT/"docs/pipeline/integration-plan.schema.json"),"--wtp-schema",str(ROOT/"docs/pipeline/worktree-topology-plan.schema.json"),"--wtp-ref",ref,"--repo",str(ROOT)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertEqual(before,{p.name:p.read_bytes() for p in tmp.iterdir()})


if __name__=="__main__": unittest.main()
