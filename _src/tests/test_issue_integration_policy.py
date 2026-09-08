#!/usr/bin/env python3
"""Adversarial tests for the non-bypassable issue integration gate."""
import copy, hashlib, importlib.util, itertools, json, shutil, subprocess, sys, tempfile, unittest
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

    def write_claimless_0037_31_candidate(self, **proof_updates):
        evidence = {
            "provenance/migrations/issue-store/0037-31-final-frozen-candidate.md":
                "task_id: 0037-31\nassignment_id: 1788519031177-793919ee\n",
            "docs/dossiers/0037-31-final-frozen-migration-20260904.md":
                "task_id: 0037-31\nassignment_id: 1788519031177-793919ee\n",
        }
        for path, text in evidence.items():
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        reports = {}
        for name in ("migration-report.json", "migration-state.json"):
            path = f"{POL.CLAIMLESS_0037_31_RUN_ROOT}/reports/{name}"
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"schema": name, "status": "promoted"}) + "\n", encoding="utf-8")
            reports[name.replace(".json", "").replace("-", "_") + "_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        proof = {
            "schema": "claimless-frozen-assignment-proof@v1", "task_id": "0037-31",
            "assignment_id": POL.CLAIMLESS_0037_31_ASSIGNMENT,
            "atomic_award": POL.CLAIMLESS_0037_31_ASSIGNMENT,
            "item_identity": POL.CLAIMLESS_0037_31_ITEM,
            "claim_mode": "claimless-frozen-transaction", "authority_epoch": "legacy-frozen",
            "source_commit": POL.CLAIMLESS_0037_31_SOURCE,
            "source_tree": POL.CLAIMLESS_0037_31_SOURCE_TREE,
            "closure_transaction": POL.CLAIMLESS_0037_31_TRANSACTION,
            "run_id": POL.CLAIMLESS_0037_31_RUN_ID,
            "run_root": POL.CLAIMLESS_0037_31_RUN_ROOT + "/",
            "allowed_paths": sorted(POL.CLAIMLESS_0037_31_SCOPE),
            "evidence_paths": sorted(POL.CLAIMLESS_0037_31_EVIDENCE),
            "companion_sha256": {path: hashlib.sha256(text.encode()).hexdigest() for path, text in evidence.items()},
        }
        proof.update(proof_updates)
        manifest = {"task_id": "0037-31", "assignment_id": POL.CLAIMLESS_0037_31_ASSIGNMENT,
                    "authority_proof": proof,
                    "candidate": {"root": POL.CLAIMLESS_0037_31_RUN_ROOT + "/",
                                  "identity": "1" * 64, "tree_digest": "2" * 64,
                                  "reports": reports}}
        target = self.root / POL.CLAIMLESS_0037_31_MANIFEST
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")

    def report_fixture(self):
        proof = {
            "candidate_identity": "f23a0cb083515f964e624658ba2cd89252e9cc16708a1d41e85f8a276a1beb10",
            "candidate_tree_digest": "61bc158665cf84e8c8ba4b394ea15724525d97d97a58dafa4ef61cffd4def3d9",
            "legacy_tree_digest": "95084ca98c1d84bca6215da5d8763084ebc0f2a90c5a4e9d33a3a38aa96423d8",
            "disposition_manifest_sha256": "8" * 64,
        }
        summary = {"blocking": 0, "error": 0, "info": 1, "total": 2, "warning": 1}
        pairs = [{"finding_id": f"IMP-{n:016x}", "rule": "IMP-CLAIM-OPAQUE"} for n in range(930)]
        coverage = {"pairs": pairs, "blocking_after_coverage": False,
                    "closure_json_synthesized": False, "credit_granted": False,
                    "disposition_manifest_digest": "sha256:" + "8" * 64}
        report = {"run_id": POL.PROMOTION_0037_31_RUN_ID, "status": "promoted",
                  "finding_summary": summary, "disposition_input": {
                  "path": POL.PROMOTION_0037_31_DISPOSITIONS, "digest": "sha256:" + "8" * 64},
                  "candidate": {"identity": proof["candidate_identity"],
                  "observed_tree_digest": proof["candidate_tree_digest"],
                  "logical_root": POL.PROMOTION_0037_31_RUN_ROOT + "/"}}
        state = {"run_id": POL.PROMOTION_0037_31_RUN_ID, "status": "promoted", "phase": "promoted",
                 "finding_summary": summary, "source": {"commit": POL.CLAIMLESS_0037_31_SOURCE,
                 "tree": POL.CLAIMLESS_0037_31_SOURCE_TREE, "tree_digest": proof["legacy_tree_digest"],
                 "working_tree_clean": True}, "candidate": {"identity": proof["candidate_identity"],
                 "tree_digest": proof["candidate_tree_digest"], "promotable": True,
                 "root": POL.PROMOTION_0037_31_RUN_ROOT + "/"}}
        import_manifest = {"blocking": False, "approval_emitted": False, "claim_json_emitted": False,
                           "closure_json_emitted": False, "disposition_coverage": coverage}
        findings = [{"severity": "blocking"} for _ in range(930)] + [{"severity": "warning"}]
        runs = [{"result": "covered", "source_commit": POL.CLAIMLESS_0037_31_SOURCE,
                 "disposition_manifest_digest": "sha256:" + "8" * 64}]
        return proof, report, state, coverage, import_manifest, findings, runs

    def test_exact_retained_tree_real_git_negative_property_matrix(self):
        root = POL.PROMOTION_0037_31_RETAINED_RUN_ROOT
        for name, text in (("a.txt", "a"), ("nested/b.txt", "b"), ("nested/c.txt", "c")):
            target = self.root/root/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
        good = self.commit("retained baseline")
        tree = self.git("rev-parse", f"{good}:{root}").stdout.strip()
        listing = subprocess.run(["git", "ls-tree", "-r", good, "--", root], cwd=self.root, capture_output=True, check=True).stdout
        digest = hashlib.sha256(listing).hexdigest()
        expected = POL._exact_tree_manifest(self.root, good, root, tree, digest, 3)
        self.assertEqual(3, len(expected))
        mutations = ("absent", "extra", "blob", "mode", "symlink")
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.git("reset", "--hard", good); self.git("clean", "-fd")
                a=self.root/root/"a.txt"
                if mutation == "absent": a.unlink()
                elif mutation == "extra": (self.root/root/"extra.txt").write_text("x")
                elif mutation == "blob": a.write_text("changed")
                elif mutation == "mode": a.chmod(0o755)
                else: a.unlink(); a.symlink_to("nested/b.txt")
                bad=self.commit(mutation)
                self.assertIsNone(POL._exact_tree_manifest(self.root,bad,root,tree,digest,3))
        self.assertIsNone(POL._exact_tree_manifest(self.root,good,root,"0"*40,digest,3))
        self.assertIsNone(POL._exact_tree_manifest(self.root,good,root,tree,"0"*64,3))

    def test_retention_envelope_exhaustive_975_set_and_alias_boundaries(self):
        retained={f"{POL.PROMOTION_0037_31_RETAINED_RUN_ROOT}/p/{n:04d}" for n in range(975)}
        base=set(retained)|set(POL.PROMOTION_0037_31_FILES)|{POL.PROMOTION_0037_31_RUN_ROOT+"/reports/x"}
        self.assertTrue(POL._promotion_path_envelope_valid(base,sorted(base),retained))
        cases=[]
        for path in sorted(retained):
            cases.append(base-{path})
        cases += [base|{POL.PROMOTION_0037_31_RETAINED_RUN_ROOT+"/extra"},
                  base|{POL.PROMOTION_0037_31_RETAINED_RUN_ROOT+"0/alias"},
                  base|{"foreign/path"}]
        for changed in cases:
            self.assertFalse(POL._promotion_path_envelope_valid(changed,sorted(changed),retained))
        self.assertFalse(POL._promotion_path_envelope_valid(base,sorted(base-{next(iter(retained))}),retained))
        self.assertEqual(978, len(cases))

    def test_real_authority_signature_fields_and_record_multiplicity(self):
        disposition=json.loads((ROOT/POL.PROMOTION_0037_31_DISPOSITIONS).read_text())
        entries=disposition["entries"]
        material=entries[0]["signature_material"]
        records=POL.issue_import_legacy._load_authority_records(material,ROOT)
        self.assertTrue(POL._authority_records_valid(entries,records))
        for field,value in (("principal","wrong@example.invalid"),("commit","0"*40),
                            ("blob_digest","sha256:"+"0"*64),("path","wrong.json")):
            bad=dict(material); bad[field]=value
            with self.subTest(field=field), self.assertRaises(POL.issue_import_legacy.ImportErrorClosed):
                POL.issue_import_legacy._load_authority_records(bad,ROOT)
        self.assertFalse(POL._authority_records_valid(entries,records[:-1]))
        self.assertFalse(POL._authority_records_valid(entries,records+[records[0]]))
        bad=copy.deepcopy(entries); bad[0]["payload_digest"]="sha256:"+"0"*64
        self.assertFalse(POL._authority_records_valid(bad,records))

    def test_report_binding_real_negative_matrix(self):
        values=list(self.report_fixture())
        self.assertTrue(POL._promotion_reports_valid(*values))
        mutations = []
        mutations.append(lambda v: v[3].update(pairs=v[3]["pairs"][:-1]))
        mutations.append(lambda v: v[3].update(pairs=v[3]["pairs"]+[dict(v[3]["pairs"][0],finding_id="IMP-extra")]))
        mutations.append(lambda v: v[5].pop())
        mutations.append(lambda v: v[5].append({"severity":"warning"}))
        mutations.append(lambda v: v[3].update(credit_granted=True))
        mutations.append(lambda v: v[3].update(blocking_after_coverage=True))
        mutations.append(lambda v: v[2]["source"].update(tree="0"*40))
        mutations.append(lambda v: v[2].update(run_id="nested/run"))
        mutations.append(lambda v: v[1]["disposition_input"].update(digest="sha256:"+"0"*64))
        mutations.append(lambda v: v[1]["candidate"].update(identity="0"*64))
        mutations.append(lambda v: v[6][0].update(source_commit="0"*40))
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                case=list(copy.deepcopy(self.report_fixture())); mutate(case)
                self.assertFalse(POL._promotion_reports_valid(*case))

    def test_invalid_empty_or_null_promotion_never_uses_historical_fallback(self):
        self.write_frozen(); frozen=self.commit("frozen")
        for promotion in ({}, None, {"policy_proof": {}}):
            with self.subTest(promotion=promotion):
                self.git("reset","--hard",frozen); self.git("clean","-fd")
                self.write_claimless_0037_31_candidate()
                path=self.root/POL.CLAIMLESS_0037_31_MANIFEST
                value=json.loads(path.read_text()); value["promotion"]=promotion
                path.write_text(json.dumps(value)+"\n")
                candidate=self.commit("invalid promotion")
                result=self.evaluate(base=frozen,candidate=candidate,enforce=False)
                self.assertEqual("rejected",result["status"])

    def test_proof_kind_boundary_cross_product_uses_canonical_envelope(self):
        retained={POL.PROMOTION_0037_31_RETAINED_RUN_ROOT+"/exact"}
        valid=set(retained)|set(POL.PROMOTION_0037_31_FILES)|{POL.PROMOTION_0037_31_RUN_ROOT+"/exact"}
        cases=0
        for proof_kind in ("historical","promotion","mixed-invalid"):
            for boundary in ("canonical","implementation"):
                for matching in (False,True):
                    observed=set(valid)
                    if not matching: observed.add("foreign/canonical-only")
                    declared=sorted(valid if boundary=="implementation" else observed)
                    actual=POL._promotion_path_envelope_valid(observed,declared,retained)
                    expected=proof_kind=="promotion" and matching
                    if proof_kind=="promotion": self.assertEqual(expected,actual)
                    else: self.assertFalse(expected)
                    cases+=1
        self.assertEqual(12,cases)

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

    def test_claimless_0037_31_manifest_is_the_only_complete_green_row(self):
        self.write_frozen(); self.base=self.commit("frozen")
        self.write_claimless_0037_31_candidate(); candidate=self.commit("claimless exact")
        self.assertEqual("passed", self.evaluate(candidate=candidate)["status"])

    def test_claimless_0037_31_manifest_rejects_each_wrong_binding(self):
        self.write_frozen(); frozen=self.commit("frozen")
        mutations = {
            "task_id": "0037-32", "assignment_id": "1788519031177-00000000",
            "atomic_award": "1788519031177-00000000", "item_identity": "0037-31-other",
            "claim_mode": "claim-bound", "authority_epoch": "issue-store-writable",
            "source_commit": "0" * 40, "source_tree": "0" * 40,
            "closure_transaction": "0" * 40, "run_id": "0037-31-other-run",
            "run_root": "_src/output/issue-migration/other/", "allowed_paths": [],
            "evidence_paths": [], "companion_sha256": {},
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                self.git("reset", "--hard", frozen); self.git("clean", "-fd")
                self.write_claimless_0037_31_candidate(**{field: value})
                result=self.evaluate(base=frozen,candidate=self.commit(field),enforce=False)
                self.assertEqual("POLICY-FROZEN-AUTHORITY-PROOF-REQUIRED", result["violations"][0]["code"])

    def test_claimless_0037_31_proof_field_subsets_fail_closed(self):
        self.write_frozen(); frozen=self.commit("frozen")
        required=("task_id", "assignment_id", "claim_mode", "authority_epoch")
        cases=0
        for present in itertools.product((False, True), repeat=len(required)):
            self.git("reset", "--hard", frozen); self.git("clean", "-fd")
            self.write_claimless_0037_31_candidate()
            path=self.root/POL.CLAIMLESS_0037_31_MANIFEST
            value=json.loads(path.read_text())
            for keep, key in zip(present, required):
                if not keep: value["authority_proof"].pop(key)
            path.write_text(json.dumps(value)+"\n")
            result=self.evaluate(base=frozen,candidate=self.commit(str(present)),enforce=False)
            self.assertEqual("passed" if all(present) else "rejected", result["status"])
            cases += 1
        self.assertEqual(16, cases)

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
