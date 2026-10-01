#!/usr/bin/env python3
"""Focused WTP canonicalization and fail-closed semantic tests."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("wtp", Path(__file__).with_name("worktree_topology_plan.py"))
assert SPEC and SPEC.loader
wtp = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = wtp
SPEC.loader.exec_module(wtp)


class WorktreeTopologyPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads((ROOT / "docs/pipeline/worktree-topology-plan.schema.json").read_text())
        cls.template = json.loads((ROOT / "docs/pipeline/worktree-topology-plan.template.json").read_text())

    def plan(self):
        return copy.deepcopy(self.template)

    def validate(self, plan, expected=("task:0000-01",)):
        plan["content_digest"] = wtp.content_digest(plan)
        return wtp.validate(plan, self.schema, expected)

    def codes(self, plan, expected=("task:0000-01",)):
        return {x["code"] for x in self.validate(plan, expected)["findings"]}

    def test_positive_minimal_and_unsorted_canonical_input(self):
        plan = self.plan()
        reverse = dict(reversed(list(plan.items())))
        self.assertEqual(wtp.content_digest(plan), wtp.content_digest(reverse))
        self.assertTrue(self.validate(reverse)["valid"])

    def test_positive_full_plan(self):
        plan = self.plan()
        producer = copy.deepcopy(plan["nodes"][1])
        producer.update(node_id="task-0000-02", work_unit="task:0000-02", branch="0000-02", worktree_path="/absolute/repository/.worktrees/0000-02")
        producer["write_scope"] = [{"match":"prefix","path":"example/0000-02"}]
        plan["nodes"].append(producer)
        plan["nodes"][1]["predecessor_constraints"] = [{"work_unit":"task:0000-02","required_state":"implementation-terminal","compatibility_ref":"none"}]
        plan["edges"].append({"from":"task-0000-02","to":"task-0000-01","kind":"prerequisite-content","condition":"producer terminal","evidence_required":["commit"]})
        self.assertTrue(self.validate(plan, ("task:0000-01","task:0000-02"))["valid"])

    def test_digest_mismatch(self):
        plan=self.plan(); plan["authority_ref"]="changed"
        report=wtp.validate(plan,self.schema,("task:0000-01",))
        self.assertIn("WTP-DIGEST-MISMATCH",{x["code"] for x in report["findings"]})

    def test_float_fails_closed(self):
        plan=self.plan(); plan["topology_revision"]=1.5
        report=wtp.validate(plan,self.schema,("task:0000-01",))
        self.assertIn("WTP-FLOAT-FORBIDDEN",{x["code"] for x in report["findings"]})

    def test_duplicate_work_unit_branch_and_worktree(self):
        plan=self.plan(); duplicate=copy.deepcopy(plan["nodes"][1]); duplicate["node_id"]="other"; plan["nodes"].append(duplicate)
        codes=self.codes(plan,("task:0000-01",))
        self.assertTrue({"WTP-DUPLICATE-WORK-UNIT","WTP-DUPLICATE-BRANCH","WTP-DUPLICATE-WORKTREE"} <= codes)

    def test_partial_graph_requires_population_and_detects_missing_node(self):
        plan=self.plan(); plan["nodes"].pop()
        self.assertIn("WTP-PARTIAL-GRAPH",self.codes(plan))
        report=wtp.validate(self.plan(),self.schema,None)
        self.assertIn("WTP-EXPECTED-POPULATION-REQUIRED",{x["code"] for x in report["findings"]})

    def test_missing_predecessor_edge(self):
        plan=self.plan(); plan["nodes"][1]["predecessor_constraints"]=[{"work_unit":"task:0000-01","required_state":"implementation-terminal","compatibility_ref":"none"}]
        self.assertIn("WTP-PREDECESSOR-EDGE-MISSING",self.codes(plan))

    def test_cyclic_prerequisite(self):
        plan=self.plan(); plan["edges"].extend([
            {"from":"task-0000-01","to":"main-root","kind":"prerequisite-content","condition":"x","evidence_required":["x"]},
            {"from":"main-root","to":"task-0000-01","kind":"prerequisite-content","condition":"x","evidence_required":["x"]}])
        self.assertIn("WTP-GRAPH-CYCLE",self.codes(plan))

    def test_missing_and_unknown_overlap(self):
        plan=self.plan(); other=copy.deepcopy(plan["nodes"][1]); other.update(node_id="other",work_unit="task:0000-02",branch="0000-02",worktree_path="/tmp/other"); plan["nodes"].append(other)
        self.assertIn("WTP-OVERLAP-MISSING",self.codes(plan,("task:0000-01","task:0000-02")))
        plan["overlap_rules"]=[{"left":"task-0000-01","right":"other","class":"mystery","paths":[{"match":"prefix","path":"example/0000-01"}],"order":"none","authority":"none","evidence_required":["none"]}]
        self.assertIn("WTP-SCHEMA-ENUM",self.codes(plan,("task:0000-01","task:0000-02")))

    def test_wrong_main_and_missing_terminal_checkpoint(self):
        plan=self.plan(); plan["nodes"][0]["write_scope"]=[{"match":"exact","path":"TODO.md"}]
        self.assertIn("WTP-MAIN-NODE",self.codes(plan))
        plan=self.plan(); plan["checkpoints"]=[]
        self.assertIn("WTP-TERMINAL-CHECKPOINT",self.codes(plan))

    def test_implicit_grandfathering_and_lifecycle_invalidity(self):
        plan=self.plan(); plan["activation"]["grandfathering"]="allowed"
        self.assertIn("WTP-GRANDFATHERING",self.codes(plan))
        for mutation in (lambda p:p.update(status="withdrawn"), lambda p:p.update(supersedes={"ref":"0"*40,"digest":"sha256:"+"0"*64,"compatibility":"incompatible"})):
            plan=self.plan(); mutation(plan)
            self.assertIn("WTP-PLAN-INVALID",self.codes(plan))

    def test_branch_hierarchy(self):
        plan=self.plan(); plan["nodes"][1]["base_branch"]="wrong"
        self.assertIn("WTP-BRANCH-HIERARCHY",self.codes(plan))

    def test_unsupported_identity_algorithm_fails_closed(self):
        plan=self.plan(); plan["digest_algorithm"]="sha512"
        self.assertIn("WTP-DIGEST-ALGORITHM-UNSUPPORTED",self.codes(plan))

    def test_cli_ref_identity_and_dirty_worktree_non_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); subprocess.run(["git","init","-q",repo],check=True)
            subprocess.run(["git","-C",repo,"config","user.email","test@example.invalid"],check=True); subprocess.run(["git","-C",repo,"config","user.name","WTP Test"],check=True)
            (repo/"plan.json").write_text(json.dumps(self.template,indent=2)+"\n"); (repo/"schema.json").write_text(json.dumps(self.schema)+"\n")
            subprocess.run(["git","-C",repo,"add","plan.json","schema.json"],check=True); subprocess.run(["git","-C",repo,"commit","-qm","fixture"],check=True)
            ref=subprocess.check_output(["git","-C",repo,"rev-parse","HEAD"],text=True).strip(); dirty=repo/"foreign-dirty.txt"; dirty.write_text("do not touch\n")
            before=subprocess.check_output(["git","-C",repo,"status","--porcelain=v1"],text=True)
            proc=subprocess.run(["python3",str(Path(wtp.__file__)),str(repo/"plan.json"),"--schema",str(repo/"schema.json"),"--expected-work-unit","task:0000-01","--plan-ref",ref,"--repo",str(repo)],text=True,capture_output=True)
            self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertEqual(before,subprocess.check_output(["git","-C",repo,"status","--porcelain=v1"],text=True)); self.assertEqual(dirty.read_text(),"do not touch\n")


if __name__ == "__main__":
    unittest.main()
