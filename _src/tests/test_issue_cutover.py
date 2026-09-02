"""AE evidence for the non-operative cutover core.

Property counts: transition=64, authority=32, ref subsets=8, event chains=8,
recursive canonical permutations=64 (seed 37002); exact total=176.
Baseline f5142ab033947bf16601ed9063f48aa96a8ff0e5 lacks tool/schemas.
"""
from __future__ import annotations
import copy, importlib.util, itertools, json, random, shutil, subprocess, tempfile, unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
S=importlib.util.spec_from_file_location("cut",ROOT/"_src/tools/issue_cutover.py"); assert S and S.loader
CUT=importlib.util.module_from_spec(S); S.loader.exec_module(CUT)
ACTOR="authority:repository-owner"
TOOLS=("issue_import_legacy.py","issue_regenerate.py","issue_validate.py","issue_store.py","issue_views.py","issue_lists.py")

def gr(repo:Path,*args:str,check=True): return subprocess.run(["git","-C",str(repo),*args],check=check,capture_output=True)
def git(repo:Path,*args:str)->str: return gr(repo,*args).stdout.decode().strip()
def event(kind,source,target,seq,previous,package):
    v={"schema":CUT.LEDGER_SCHEMA,"transaction_id":"tx-0037-safe-core","sequence":seq,"event_kind":kind,"from_epoch":source,"to_epoch":target,"allowed_write_authority":CUT.EXPECTED_AUTHORITY[target],"issue_store_frozen":target in CUT.FROZEN_EPOCHS,"previous_event_digest":previous,"payload_digest":package,"actor":ACTOR,"role":CUT.EVENT_ROLES[kind],"signature_policy":"single-authority-self-attestation@v1","signature_verified":True}
    v["event_digest"]=CUT.event_digest(v); return v
def shuffled(v,rng):
    if isinstance(v,dict):
        x=[(k,shuffled(w,rng)) for k,w in v.items()]; rng.shuffle(x); return dict(x)
    if isinstance(v,list): return [shuffled(x,rng) for x in v]
    return v

class Fixture(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(); self.base=Path(self.t.name).resolve(); self.repo=self.base/"repo"; self.repo.mkdir()
        gr(self.repo,"init","-b","main"); git(self.repo,"config","user.email","x@example.invalid"); git(self.repo,"config","user.name","Fixture")
        dst=self.repo/"_src/tools"; dst.mkdir(parents=True)
        for name in TOOLS: shutil.copyfile(ROOT/"_src/tools"/name,dst/name)
        inv=self.repo/"provenance/migrations/issue-store/tools"; inv.mkdir(parents=True); shutil.copyfile(ROOT/"provenance/migrations/issue-store/tools/issue_legacy_inventory.py",inv/"issue_legacy_inventory.py")
        shutil.copytree(ROOT/"_src/tests/fixtures/0037-11.01/issues",self.repo/"issues"); shutil.copytree(ROOT/"issues/_schema",self.repo/"issues/_schema")
        docs=self.repo/"docs/pipeline"; docs.mkdir(parents=True); shutil.copyfile(ROOT/"docs/pipeline/issue-derived-artifacts-v1.json",docs/"issue-derived-artifacts-v1.json")
        shutil.copyfile(ROOT/"agent-workflow.json",self.repo/"agent-workflow.json")
        (self.repo/"TODO.md").write_text("## Feature: 0099 — Fixture\n\n- [ ] **0099-01** Safe.\n  - **Acceptance criteria:** Safe.\n  - **Definition of Done:** Safe.\n"); (self.repo/"DONE.md").write_text("# DONE\n"); (self.repo/"seed").write_text("source\n")
        gr(self.repo,"add","."); gr(self.repo,"commit","-m","source"); self.source=git(self.repo,"rev-parse","HEAD")
        gr(self.repo,"checkout","-b","candidate"); (self.repo/"seed").write_text("candidate\n"); gr(self.repo,"add","seed"); gr(self.repo,"commit","-m","candidate"); self.candidate=git(self.repo,"rev-parse","HEAD")
        self.manifest=self.build(); self.path=self.base/"manifest.json"; self.path.write_text(CUT.canonical_json(self.manifest))
    def tearDown(self): self.t.cleanup()
    def adapter_config(self): return [{"id":"importer","config":{"source":"manifest-source","files":["TODO.md","DONE.md"]}},{"id":"regenerator","config":{"mode":"write-disposable","dag_path":"docs/pipeline/issue-derived-artifacts-v1.json"}}]
    def calibrate(self,partial):
        stage=self.base/"calibration"; stage.mkdir(); partial["adapters"]=self.adapter_config()
        got=CUT._run_adapters(self.repo,stage,partial); shutil.rmtree(stage); return [{"adapter":x["adapter"],"tree_digest":x["tree_digest"]} for x in got]
    def build(self):
        source={"ref":"refs/heads/main",**CUT.git_identity(self.repo,self.source)}; candidate={"ref":"refs/heads/candidate",**CUT.git_identity(self.repo,self.candidate)}; patch=CUT.patch_identity(self.repo,self.source,self.candidate)
        selector=self.repo/"agent-workflow.json"; snap={"baseline_oid":self.source,"epoch":"legacy_active","allowed_write_authority":"legacy","issue_store_frozen":False,"authorities":[ACTOR],"selector_path":"agent-workflow.json","selector_digest":CUT.digest_bytes(selector.read_bytes())}; snap["token_digest"]=CUT.snapshot_token(snap)
        roles={r:ACTOR for r in CUT.REQUIRED_ROLES}
        m={"schema":CUT.MANIFEST_SCHEMA,"transaction_id":"tx-0037-safe-core","source":source,"candidate":candidate,"prepared_patch":patch,"authority_snapshot":snap,"identities":{"tools":[{"path":f"_src/tools/{n}","digest":CUT.digest_bytes((self.repo/"_src/tools"/n).read_bytes())} for n in TOOLS],"schemas":[{"path":f"issues/_schema/{n}","digest":CUT.digest_bytes((self.repo/"issues/_schema"/n).read_bytes())} for n in ("cutover-transaction-manifest-v1.schema.json","cutover-control-ledger-v2.schema.json")]},"refs":[{"name":"refs/autodocs/cutover-test/control","expected_oid":None,"target_oid":self.candidate}],"roles":roles,"signatures":[],"approvals":{},"quiescence":{},"ledger":[],"adapters":self.adapter_config(),"outputs":[],"findings":[],"cas":{"disposable_test_repo":False,"declared_refs":["refs/autodocs/cutover-test/control"]}}
        package=CUT.package_digest(m); m["signatures"]=[{"role":r,"actor":ACTOR,"policy":"single-authority-self-attestation@v1","payload_digest":CUT.signature_payload_digest(package,r,ACTOR),"verified":True} for r in sorted(CUT.REQUIRED_ROLES)]; m["approvals"]={"ref":"refs/autodocs/approval/0037/tx","base_oid":self.source,"role":"approver","actor":ACTOR,"payload_digest":package,"signature_verified":True}
        q={"clients":[],"jobs":[],"claims":[],"observed_at_oid":self.source,"snapshot_token":snap["token_digest"]}; q["digest"]=CUT.digest_value(q); m["quiescence"]=q; m["ledger"]=[event("inspect","legacy_active","legacy_active",1,None,package)]; m["outputs"]=self.calibrate(m); return m
    def code(self,m):
        try: CUT.validate_manifest(m)
        except CUT.CutoverError as e: return e.code
        return "PASS"
    def state(self):
        refs=gr(self.repo,"show-ref",check=False).stdout; count=gr(self.repo,"count-objects","-v").stdout
        files=[p.relative_to(self.repo).as_posix() for p in self.repo.rglob("*") if ".git" not in p.parts and p.is_file()]; locks=[p.as_posix() for p in self.repo.rglob("*.lock")]; sigs=[p.as_posix() for p in self.repo.rglob("*signature*")]
        return refs,count,sorted(files),locks,sigs

class Contract(Fixture):
    def test_real_adapters_cli_prepare_verify_and_retry(self):
        out=self.base/"cutover-product"; b=StringIO()
        with redirect_stdout(b): self.assertEqual(CUT.main(["prepare","--repo",str(self.repo),"--manifest",str(self.path),"--output-root",str(out)]),0)
        self.assertEqual(json.loads(b.getvalue())["status"],"PASS"); self.assertEqual(CUT.verify(self.repo,self.manifest,out)["status"],"PASS"); self.assertTrue(CUT.prepare(self.repo,out,self.manifest)["idempotent"])
    def test_effects_disabled_no_override(self):
        for cmd in CUT.EFFECT_COMMANDS:
            b=StringIO()
            with redirect_stdout(b): self.assertEqual(CUT.main([cmd,"--repo","/missing","--manifest","/missing"]),2)
            self.assertEqual(json.loads(b.getvalue())["code"],CUT.BLOCKED_EFFECT_CODE)
        with self.assertRaises(SystemExit): CUT.main(["activate","--repo","/x","--manifest","/y","--force"])
    def test_identity_recomputation_and_retained_extra(self):
        self.assertEqual(CUT.inspect(self.repo,self.manifest)["status"],"PASS"); bad=copy.deepcopy(self.manifest); bad["candidate"]["tree_digest"]="sha256:"+"0"*64; before=self.state(); self.assertIn("CUTOVER-CANDIDATE-IDENTITY-DRIFT",{x["code"] for x in CUT.inspect(self.repo,bad)["findings"]}); self.assertEqual(before,self.state())
        out=self.base/"cutover-extra"; CUT.prepare(self.repo,out,self.manifest); (out/"extra").write_text("x"); retained=CUT.tree_manifest(out); self.assertIn("CUTOVER-RETAINED-EXTRA",{x["code"] for x in CUT.verify(self.repo,self.manifest,out)["findings"]}); self.assertEqual(retained,CUT.tree_manifest(out))
    def test_symlink_identity_and_failed_prepare_zero_mutation(self):
        victim=self.repo/"_src/tools/issue_lists.py"; real=victim.with_suffix(".real"); victim.rename(real); victim.symlink_to(real.name); before=self.state(); result=CUT.inspect(self.repo,self.manifest); self.assertIn("CUTOVER-IDENTITY-PATH",{x["code"] for x in result["findings"]})
        out=self.base/"cutover-fail"; bad=copy.deepcopy(self.manifest); bad["outputs"][0]["tree_digest"]="sha256:"+"0"*64
        with self.assertRaises(CUT.CutoverError) as e: CUT.prepare(self.repo,out,bad)
        self.assertEqual(e.exception.code,"CUTOVER-OUTPUT-DRIFT"); self.assertEqual(before,self.state()); self.assertFalse(out.exists())
    def test_35_semantic_negative_codes(self):
        cases=[]
        def add(code,fn): cases.append((code,fn))
        add("CUTOVER-UNKNOWN-FIELD",lambda m:m.__setitem__("x",1)); add("CUTOVER-MISSING-FIELD",lambda m:m.pop("refs")); add("CUTOVER-TRANSACTION-ID",lambda m:m.__setitem__("transaction_id","bad")); add("CUTOVER-OID",lambda m:m["source"].__setitem__("commit_oid","x")); add("CUTOVER-DIGEST",lambda m:m["source"].__setitem__("tree_digest","x")); add("CUTOVER-PATCH-BINDING",lambda m:m["prepared_patch"].__setitem__("base_oid",m["candidate"]["commit_oid"])); add("CUTOVER-EPOCH",lambda m:m["authority_snapshot"].__setitem__("epoch","x")); add("CUTOVER-AUTHORITY-MATRIX",lambda m:m["authority_snapshot"].__setitem__("allowed_write_authority","none")); add("CUTOVER-FROZEN-STATE",lambda m:m["authority_snapshot"].__setitem__("issue_store_frozen",True)); add("CUTOVER-EXACTLY-ONE-AUTHORITY",lambda m:m["authority_snapshot"]["authorities"].append("x")); add("CUTOVER-AUTHORITY-TOKEN",lambda m:m["authority_snapshot"].__setitem__("token_digest","sha256:"+"0"*64)); add("CUTOVER-SNAPSHOT-BASELINE",lambda m:m["authority_snapshot"].__setitem__("baseline_oid",m["candidate"]["commit_oid"])); add("CUTOVER-PATH",lambda m:m["identities"]["tools"][0].__setitem__("path","../x")); add("CUTOVER-IDENTITY",lambda m:m["identities"]["tools"].append(copy.deepcopy(m["identities"]["tools"][0]))); add("CUTOVER-MAIN-REF",lambda m:m["refs"][0].__setitem__("name","refs/heads/main")); add("CUTOVER-DUPLICATE-REF",lambda m:m["refs"].append(copy.deepcopy(m["refs"][0]))); add("CUTOVER-ROLE-SET",lambda m:m["roles"].pop("auditor")); add("CUTOVER-ROLE-AUTHORITY",lambda m:m["roles"].__setitem__("auditor","x")); add("CUTOVER-SIGNATURE-SET",lambda m:m["signatures"].pop()); add("CUTOVER-SIGNATURE-ACTOR",lambda m:m["signatures"][0].__setitem__("actor","x")); add("CUTOVER-SIGNATURE-POLICY",lambda m:m["signatures"][0].__setitem__("policy","x")); add("CUTOVER-SIGNATURE-PAYLOAD",lambda m:m["signatures"][0].__setitem__("payload_digest","sha256:"+"0"*64)); add("CUTOVER-APPROVAL-REF",lambda m:m["approvals"].__setitem__("ref","refs/x")); add("CUTOVER-APPROVAL-BASE",lambda m:m["approvals"].__setitem__("base_oid",m["candidate"]["commit_oid"])); add("CUTOVER-APPROVAL-ACTOR",lambda m:m["approvals"].__setitem__("actor","x")); add("CUTOVER-APPROVAL-PAYLOAD",lambda m:m["approvals"].__setitem__("payload_digest","sha256:"+"0"*64)); add("CUTOVER-QUIESCENCE-CLIENTS",lambda m:m["quiescence"]["clients"].append("x")); add("CUTOVER-QUIESCENCE-JOBS",lambda m:m["quiescence"]["jobs"].append("x")); add("CUTOVER-QUIESCENCE-CLAIMS",lambda m:m["quiescence"]["claims"].append("x")); add("CUTOVER-QUIESCENCE-BINDING",lambda m:m["quiescence"].__setitem__("snapshot_token","sha256:"+"0"*64)); add("CUTOVER-QUIESCENCE-DIGEST",lambda m:m["quiescence"].__setitem__("digest","sha256:"+"0"*64)); add("CUTOVER-ADAPTER-SET",lambda m:m["adapters"].pop()); add("CUTOVER-IMPORTER-CONFIG",lambda m:m["adapters"][0]["config"].__setitem__("source","x")); add("CUTOVER-REGENERATOR-MODE",lambda m:m["adapters"][1]["config"].__setitem__("mode","check")); add("CUTOVER-OUTPUT-SET",lambda m:m["outputs"].pop()); add("CUTOVER-UNDECLARED-REF",lambda m:m["cas"].__setitem__("declared_refs",["refs/x"])); add("CUTOVER-EVENT-KIND",lambda m:m["ledger"][0].__setitem__("event_kind","x"))
        self.assertGreaterEqual(len(cases),32)
        for expected,fn in cases:
            with self.subTest(expected=expected):
                m=copy.deepcopy(self.manifest); fn(m)
                if expected == "CUTOVER-EVENT-KIND": m["ledger"][0]["event_digest"]=CUT.event_digest(m["ledger"][0])
                if expected == "CUTOVER-SNAPSHOT-BASELINE": m["authority_snapshot"]["token_digest"]=CUT.snapshot_token(m["authority_snapshot"])
                self.assertEqual(self.code(m),expected)

class Properties(Fixture):
    def test_transition_and_authority_matrices(self):
        roles={r:ACTOR for r in CUT.REQUIRED_ROLES}; count=0
        for a,b in itertools.product(CUT.EPOCHS,repeat=2):
            kind=next((k for k,pairs in CUT.EVENT_TRANSITIONS.items() if (a,b) in pairs),"inspect"); e=event(kind,a,b,1,None,"sha256:"+"0"*64)
            try: CUT.validate_ledger([e],"tx-0037-safe-core",roles,ACTOR); accepted=True
            except CUT.CutoverError: accepted=False
            self.assertEqual(accepted,any((a,b) in pairs for pairs in CUT.EVENT_TRANSITIONS.values())); count+=1
        self.assertEqual(count,64)
        for epoch,authority in itertools.product(CUT.EPOCHS,CUT.WRITE_AUTHORITIES):
            s=copy.deepcopy(self.manifest["authority_snapshot"]); s["epoch"]=epoch; s["allowed_write_authority"]=authority; s["issue_store_frozen"]=epoch in CUT.FROZEN_EPOCHS; s["token_digest"]=CUT.snapshot_token(s)
            try: CUT._validate_snapshot(s); accepted=True
            except CUT.CutoverError: accepted=False
            self.assertEqual(accepted,authority==CUT.EXPECTED_AUTHORITY[epoch])
    def test_event_prefixes_and_recursive_canonical(self):
        roles={r:ACTOR for r in CUT.REQUIRED_ROLES}; path=[("inspect","legacy_active","legacy_active"),("freeze","legacy_active","legacy_frozen"),("prepare","legacy_frozen","prepared"),("switch","prepared","issue_store_active"),("audit","issue_store_active","post_cutover_audit"),("point-of-no-return","post_cutover_audit","point_of_no_return"),("repair","point_of_no_return","write_frozen_repair"),("repair","write_frozen_repair","issue_store_active")]; events=[]; previous=None
        for i,(k,a,b) in enumerate(path,1): e=event(k,a,b,i,previous,"sha256:"+"0"*64); events.append(e); previous=e["event_digest"]; CUT.validate_ledger(events,"tx-0037-safe-core",roles,ACTOR)
        rng=random.Random(37002); expected=CUT.canonical_json(self.manifest)
        for _ in range(64): x=shuffled(self.manifest,rng); CUT.validate_manifest(x); self.assertEqual(CUT.canonical_json(x),expected)

class SchemaFixtures(unittest.TestCase):
    def test_schema_json_and_runtime_fixtures(self):
        for name in ("cutover-transaction-manifest-v1.schema.json","cutover-control-ledger-v2.schema.json"): json.loads((ROOT/"issues/_schema"/name).read_text())
        root=ROOT/"issues/_schema/fixtures/cutover-transaction-manifest-v1"; index=json.loads((root/"manifest.json").read_text())
        for rel in index["valid"]: CUT.validate_manifest(json.loads((root/rel).read_text()))
        for rel in index["invalid"]:
            with self.assertRaises(CUT.CutoverError): CUT.validate_manifest(json.loads((root/rel).read_text()))
        root=ROOT/"issues/_schema/fixtures/cutover-control-ledger-v2"; index=json.loads((root/"manifest.json").read_text()); roles={r:ACTOR for r in CUT.REQUIRED_ROLES}
        for rel in index["valid"]: CUT.validate_ledger([json.loads((root/rel).read_text())],"tx-0037-safe-core",roles,ACTOR)
        for rel in index["invalid"]:
            with self.assertRaises(CUT.CutoverError): CUT.validate_ledger([json.loads((root/rel).read_text())],"tx-0037-safe-core",roles,ACTOR)

class CAS(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(); self.repo=Path(self.t.name).resolve()/"repo"; self.repo.mkdir(); gr(self.repo,"init","-b","trunk"); git(self.repo,"config","user.email","x@y"); git(self.repo,"config","user.name","X"); (self.repo/".issue-cutover-disposable-test-repo").write_text("issue-cutover-disposable-test-repo@v1\n"); (self.repo/"a").write_text("a"); gr(self.repo,"add","."); gr(self.repo,"commit","-m","a"); self.a=git(self.repo,"rev-parse","HEAD"); (self.repo/"b").write_text("b"); gr(self.repo,"add","b"); gr(self.repo,"commit","-m","b"); self.b=git(self.repo,"rev-parse","HEAD")
    def tearDown(self): self.t.cleanup()
    def snap(self): return gr(self.repo,"show-ref",check=False).stdout,gr(self.repo,"count-objects","-v").stdout,sorted(p.as_posix() for p in self.repo.rglob("*.lock")),sorted(p.as_posix() for p in self.repo.rglob("*signature*"))
    def test_ref_subsets_real_execution_8(self):
        for mask in range(8):
            refs=[f"refs/autodocs/cutover-test/{mask}-{i}" for i in range(3)]; ex=[]
            for i,r in enumerate(refs):
                old=self.a if mask&(1<<i) else None
                if old: git(self.repo,"update-ref",r,old)
                ex.append({"name":r,"expected_oid":old,"target_oid":self.b})
            self.assertEqual(CUT.execute_disposable_cas(self.repo,ex,refs,dry_run=False)["status"],"APPLIED")
    def test_target_missing_dry_run_and_competitor_zero_mutation(self):
        ref="refs/autodocs/cutover-test/x"; before=self.snap()
        with self.assertRaises(CUT.CutoverError) as e: CUT.execute_disposable_cas(self.repo,[{"name":ref,"expected_oid":None,"target_oid":"1"*40}],[ref],dry_run=True)
        self.assertEqual(e.exception.code,"CUTOVER-CAS-TARGET-MISSING"); self.assertEqual(before,self.snap())
        self.assertEqual(CUT.execute_disposable_cas(self.repo,[{"name":ref,"expected_oid":None,"target_oid":self.b}],[ref],dry_run=True)["mutation"],"none"); self.assertEqual(before,self.snap())
    def test_competitor_is_all_or_none(self):
        refs=["refs/autodocs/cutover-test/competitor-a","refs/autodocs/cutover-test/competitor-b"]; git(self.repo,"update-ref",refs[0],self.b); before=self.snap()
        with self.assertRaises(CUT.CutoverError) as e: CUT.execute_disposable_cas(self.repo,[{"name":refs[0],"expected_oid":self.a,"target_oid":self.a},{"name":refs[1],"expected_oid":None,"target_oid":self.b}],refs,dry_run=False)
        self.assertEqual(e.exception.code,"CUTOVER-CAS-COMPETITOR"); self.assertEqual(before,self.snap())
    def test_three_crashes_and_recovery_retry(self):
        for point,code,changed in (("before-prepare","CUTOVER-CAS-CRASH-BEFORE-PREPARE",False),("between-prepare-commit","CUTOVER-CAS-CRASH-BETWEEN",False),("after-commit-before-receipt","CUTOVER-CAS-CRASH-AFTER-COMMIT",True)):
            ref=f"refs/autodocs/cutover-test/{point}"; receipt=self.repo.parent/f"{point}.json"; before=self.snap()
            with self.assertRaises(CUT.CutoverError) as e: CUT.execute_disposable_cas(self.repo,[{"name":ref,"expected_oid":None,"target_oid":self.b}],[ref],dry_run=False,crash_at=point,receipt_path=receipt)
            self.assertEqual(e.exception.code,code); self.assertEqual(CUT.resolve_ref(self.repo,ref)==self.b,changed); self.assertFalse(receipt.exists())
            if changed: self.assertEqual(CUT.execute_disposable_cas(self.repo,[{"name":ref,"expected_oid":None,"target_oid":self.b}],[ref],dry_run=False,receipt_path=receipt)["status"],"RECOVERED")
            else: self.assertEqual(before,self.snap())

if __name__=="__main__": unittest.main()
