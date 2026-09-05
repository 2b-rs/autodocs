#!/usr/bin/env python3
"""Adversarial tests for the non-bypassable issue integration gate."""
import hashlib, importlib.util, itertools, json, shutil, subprocess, sys, tempfile, unittest
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

    def promotion_fixture(self):
        report_digests = {key: hashlib.sha256(path.encode()).hexdigest()
                          for key, path in POL.PROMOTION_0037_31_REPORTS.items()}
        companion_paths = POL.PROMOTION_0037_31_EVIDENCE - {POL.CLAIMLESS_0037_31_MANIFEST}
        companion_digests = {path: hashlib.sha256(("companion:" + path).encode()).hexdigest()
                             for path in companion_paths}
        companion_digests[POL.PROMOTION_0037_31_AUTHORITY] = "512ae4acec856e74625ea6c6dd3ad5fafd03b901fe29e51af84fc9548001fe55"
        companion_digests[POL.PROMOTION_0037_31_DISPOSITIONS] = "82275efcd478fe3518b33ca9f61876077ae8c3e8594f0c6ba6064d6567b079b9"
        changed = set(POL.PROMOTION_0037_31_FILES) | set(POL.PROMOTION_0037_31_REPORTS.values()) | {
            POL.PROMOTION_0037_31_RETAINED_RUN_ROOT + "/retained.txt",
        }
        proof = {
            "schema": "0037-31-promotion-policy-proof@v1", "task_id": "0037-31",
            "assignment_id": POL.PROMOTION_0037_31_ASSIGNMENT,
            "delegation_offer": POL.PROMOTION_0037_31_DELEGATION,
            "extension_award": POL.PROMOTION_0037_31_EXTENSION_AWARD,
            "authority_decisions": ["DEC-0037-034", "DEC-0037-035"],
            "canonical_base": POL.PROMOTION_0037_31_CANONICAL_BASE,
            "overlay_base_candidate": POL.PROMOTION_0037_31_BASE_CANDIDATE,
            "source_commit": POL.CLAIMLESS_0037_31_SOURCE,
            "source_tree": POL.CLAIMLESS_0037_31_SOURCE_TREE,
            "legacy_tree_digest": "95084ca98c1d84bca6215da5d8763084ebc0f2a90c5a4e9d33a3a38aa96423d8",
            "run_id": POL.PROMOTION_0037_31_RUN_ID,
            "run_root": POL.PROMOTION_0037_31_RUN_ROOT + "/",
            "authority_sha256": companion_digests[POL.PROMOTION_0037_31_AUTHORITY],
            "disposition_manifest_sha256": companion_digests[POL.PROMOTION_0037_31_DISPOSITIONS],
            "candidate_identity": "f23a0cb083515f964e624658ba2cd89252e9cc16708a1d41e85f8a276a1beb10",
            "candidate_tree_digest": "61bc158665cf84e8c8ba4b394ea15724525d97d97a58dafa4ef61cffd4def3d9",
            "reports": report_digests, "evidence_paths": sorted(POL.PROMOTION_0037_31_EVIDENCE),
            "changed_paths": sorted(changed), "companion_sha256": companion_digests,
            "historical_proof": {
                "assignment_id": POL.CLAIMLESS_0037_31_ASSIGNMENT,
                "closure_transaction": POL.CLAIMLESS_0037_31_TRANSACTION,
                "run_id": POL.CLAIMLESS_0037_31_RUN_ID,
                "report_sha256": "9b5660a92d50757dd20f950286c8a24b62978c2dd0ed3250177ba62343d2ea7e",
            },
        }
        manifest = {"promotion": {"policy_proof": proof}}
        pairs = [{"finding_id": f"IMP-{n:016x}", "rule": "IMP-CLAIM-OPAQUE"} for n in range(930)]
        objects = {
            POL.CLAIMLESS_0037_31_MANIFEST: manifest,
            POL.PROMOTION_0037_31_REPORTS["migration_report_sha256"]: {
                "status": "promoted", "candidate": {"identity": proof["candidate_identity"],
                "observed_tree_digest": proof["candidate_tree_digest"]}},
            POL.PROMOTION_0037_31_REPORTS["migration_state_sha256"]: {
                "status": "promoted", "phase": "promoted", "candidate": {"identity": proof["candidate_identity"],
                "tree_digest": proof["candidate_tree_digest"], "promotable": True}},
            POL.PROMOTION_0037_31_REPORTS["disposition_coverage_sha256"]: {
                "pairs": pairs, "blocking_after_coverage": False,
                "closure_json_synthesized": False, "credit_granted": False},
            POL.PROMOTION_0037_31_REPORTS["import_manifest_sha256"]: {
                "blocking": False, "approval_emitted": False, "claim_json_emitted": False,
                "closure_json_emitted": False},
            POL.PROMOTION_0037_31_DISPOSITIONS: {"entries": []},
        }
        findings = [{"severity": "blocking"} for _ in range(930)] + [{"severity": "warning"}]
        blobs = {
            POL.PROMOTION_0037_31_REPORTS["findings_sha256"]: json.dumps(findings),
            POL.PROMOTION_0037_31_REPORTS["disposition_runs_sha256"]: json.dumps({"result": "covered"}) + "\n",
            "provenance/migrations/issue-store/0037-31-final-frozen-candidate.md":
                POL.PROMOTION_0037_31_ASSIGNMENT + " " + POL.PROMOTION_0037_31_RUN_ID,
            "docs/dossiers/0037-31-final-frozen-migration-20260904.md":
                POL.PROMOTION_0037_31_ASSIGNMENT + " " + POL.PROMOTION_0037_31_RUN_ID,
        }
        digests = {**report_digests, **companion_digests}
        digest_by_path = {path: report_digests[key] for key, path in POL.PROMOTION_0037_31_REPORTS.items()}
        digest_by_path.update(companion_digests)
        return changed, proof, objects, blobs, digest_by_path

    def evaluate_promotion_fixture(self, mutate=None, changed_mutation=None):
        changed, proof, objects, blobs, digests = self.promotion_fixture()
        if mutate:
            mutate(proof)
        if changed_mutation:
            changed_mutation(changed)
        def candidate_json(_root, _candidate, path): return objects.get(path)
        def candidate_blob(_root, _candidate, path): return blobs.get(path, "")
        def candidate_digest(_root, candidate, path):
            if path.startswith(POL.PROMOTION_0037_31_RETAINED_RUN_ROOT + "/"):
                return "f" * 64
            return digests.get(path)
        with mock.patch.object(POL, "_candidate_json", side_effect=candidate_json), \
             mock.patch.object(POL, "_candidate_blob", side_effect=candidate_blob), \
             mock.patch.object(POL, "_candidate_blob_sha256", side_effect=candidate_digest), \
             mock.patch.object(POL, "_regular_candidate_blob", return_value=True), \
             mock.patch.object(POL, "_promotion_authority_valid", return_value=True):
            return POL._promotion_0037_31_proof(self.root, "c" * 40,
                POL.CLAIMLESS_0037_31_MANIFEST, changed)

    def test_promotion_closed_proof_accepts_only_complete_exact_fixture(self):
        self.assertIs(True, self.evaluate_promotion_fixture())

    def test_promotion_each_static_binding_wrong_or_missing_fails_closed(self):
        fields = (
            "schema", "task_id", "assignment_id", "delegation_offer", "extension_award",
            "authority_decisions", "canonical_base", "overlay_base_candidate", "source_commit",
            "source_tree", "legacy_tree_digest", "run_id", "run_root", "authority_sha256",
            "disposition_manifest_sha256", "candidate_identity", "candidate_tree_digest",
            "reports", "evidence_paths", "changed_paths", "companion_sha256", "historical_proof",
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertIs(False, self.evaluate_promotion_fixture(lambda proof, f=field: proof.pop(f)))

    def test_promotion_changed_path_property_domain(self):
        adjacent = {
            "relative/file": True, "/absolute": False, "../traversal": False,
            "a/../alias": False, "a/./dot": False, "a\\backslash": False,
            "": False, "prefix/../collision": False,
        }
        for path, expected in adjacent.items():
            with self.subTest(path=path):
                self.assertEqual(expected, POL._canonical_promotion_path(path) is not None)
        foreign = lambda changed: changed.add("_src/output/issue-migration/0037-31-promoted-dispositions-20260904-r20/alias")
        self.assertIs(False, self.evaluate_promotion_fixture(changed_mutation=foreign))
        omitted = lambda changed: changed.remove(POL.PROMOTION_0037_31_AUTHORITY)
        self.assertIs(False, self.evaluate_promotion_fixture(changed_mutation=omitted))

    def test_recognized_invalid_promotion_never_falls_back_to_historical_proof(self):
        manifest = {"promotion": {"policy_proof": {}}}
        with mock.patch.object(POL, "_candidate_json", return_value=manifest), \
             mock.patch.object(POL, "_claimless_0037_31_proof", return_value=True):
            self.assertIs(False, POL.frozen_authority_proof(
                self.root, "c" * 40, POL.CLAIMLESS_0037_31_MANIFEST,
                {POL.CLAIMLESS_0037_31_MANIFEST}))

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
