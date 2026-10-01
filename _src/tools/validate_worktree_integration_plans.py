#!/usr/bin/env python3
"""Read-only composed validator for WTP@v1 and IP@v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import worktree_topology_plan as wtp_tool

IP_SCHEMA = "integration-plan@v1"
CANONICALIZATION = "json-sort-utf8-no-floats@v1"
DIGEST_ALGORITHM = "sha256"
REPORT_SCHEMA = "worktree-integration-validation@v1"


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    message: str


def canonical_bytes(value: Any, omitted: Iterable[str] = ()) -> bytes:
    omitted_set=set(omitted)
    def clean(item: Any) -> Any:
        if isinstance(item,float): raise ValueError("floating-point values are forbidden")
        if isinstance(item,dict): return {k:clean(v) for k,v in item.items() if k not in omitted_set}
        if isinstance(item,list): return [clean(v) for v in item]
        return item
    return json.dumps(clean(value),sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")


def digest(value: Any, omitted: Iterable[str] = ()) -> str:
    return "sha256:"+hashlib.sha256(canonical_bytes(value,omitted)).hexdigest()


def edge_id(edge: dict[str,Any]) -> str:
    return f"{edge.get('kind')}:{edge.get('from')}->{edge.get('to')}"


def overlap_id(rule: dict[str,Any]) -> str:
    left,right=sorted((str(rule.get("left")),str(rule.get("right"))))
    return f"{left}|{right}|{rule.get('class')}"


def _codes_from_schema(value: Any, schema: dict[str,Any], prefix: str) -> list[Finding]:
    return [Finding(f"{prefix}-{x.code[len('WTP-SCHEMA-'):] if x.code.startswith('WTP-SCHEMA-') else x.code}",x.path,x.message) for x in wtp_tool._schema_findings(value,schema,schema)]


def _duplicates(items: list[Any]) -> bool:
    return len(items)!=len(set(items))


def _closure_findings(closure: dict[str,Any], index: int, binding: dict[str,Any]) -> list[Finding]:
    p=f"/acceptance_closures/{index}"; out=[]
    if closure.get("wtp_ref")!=binding.get("ref") or closure.get("wtp_digest")!=binding.get("content_digest"):
        out.append(Finding("WIP-CLOSURE-WTP-MISMATCH",p,"closure binds another WTP identity"))
    if closure.get("closure_digest")!=digest(closure,{"closure_digest","audit_timestamp"}):
        out.append(Finding("WIP-CLOSURE-DIGEST-MISMATCH",p+"/closure_digest","closure digest is not reproducible"))
    members=closure.get("members",[])
    if [m.get("work_unit") for m in members]!=sorted(m.get("work_unit") for m in members):
        out.append(Finding("WIP-CLOSURE-MEMBER-ORDER",p+"/members","members must be lexicographic"))
    if closure.get("member_manifest_digest")!=digest(members):
        out.append(Finding("WIP-CLOSURE-MANIFEST-MISMATCH",p+"/member_manifest_digest","member manifest digest differs"))
    for j,m in enumerate(members):
        mp=f"{p}/members/{j}"
        if m.get("accepted_candidate_ref")!=m.get("candidate_ref"):
            out.append(Finding("WIP-ACCEPTANCE-CANDIDATE-MISMATCH",mp,"Acceptance binds another candidate"))
        if m.get("invalidation_state")!="current":
            out.append(Finding("WIP-ACCEPTANCE-NOT-CURRENT",mp+"/invalidation_state","Acceptance is stale or invalidated"))
    if closure.get("state")!="current" and members:
        out.append(Finding("WIP-CLOSURE-STATE-INCONSISTENT",p,"non-current closure cannot carry authoritative members"))
    return out


def validate(ip: dict[str,Any], wtp: dict[str,Any], ip_schema: dict[str,Any], wtp_schema: dict[str,Any], *, wtp_ref: str, ref_checker=None) -> dict[str,Any]:
    out: list[Finding]=[]
    try: ip_digest=digest(ip,{"content_digest"})
    except (TypeError,ValueError,UnicodeError) as exc:
        ip_digest=None; out.append(Finding("WIP-FLOAT-FORBIDDEN","/",str(exc)))
    try: wtp_digest=wtp_tool.content_digest(wtp)
    except (TypeError,ValueError,UnicodeError) as exc:
        wtp_digest=None; out.append(Finding("WIP-WTP-DIGEST-UNREPRODUCIBLE","/wtp_binding",str(exc)))
    out.extend(_codes_from_schema(ip,ip_schema,"WIP-IP-SCHEMA"))
    out.extend(_codes_from_schema(wtp,wtp_schema,"WIP-WTP-SCHEMA"))
    for key,want,code in (("schema_version",IP_SCHEMA,"WIP-IP-VERSION"),("canonicalization_version",CANONICALIZATION,"WIP-CANONICALIZATION"),("digest_algorithm",DIGEST_ALGORITHM,"WIP-DIGEST-ALGORITHM")):
        if ip.get(key)!=want: out.append(Finding(code,f"/{key}","unsupported IP identity version"))
    if ip.get("content_digest")!=ip_digest: out.append(Finding("WIP-IP-DIGEST-MISMATCH","/content_digest","IP digest differs"))
    if ref_checker is not None and not ref_checker(wtp_ref): out.append(Finding("WIP-REF-UNREACHABLE","/wtp_binding/ref","WTP REF is not a reachable commit"))

    binding=ip.get("wtp_binding",{})
    comparisons=(("ref",wtp_ref,"WIP-WTP-REF-MISMATCH"),("content_digest",wtp_digest,"WIP-WTP-DIGEST-MISMATCH"),("schema_version",wtp.get("schema_version"),"WIP-WTP-VERSION-MISMATCH"),("canonicalization_version",wtp.get("canonicalization_version"),"WIP-WTP-VERSION-MISMATCH"),("digest_algorithm",wtp.get("digest_algorithm"),"WIP-WTP-VERSION-MISMATCH"),("feature_id",wtp.get("feature_id"),"WIP-FEATURE-MISMATCH"),("baseline_ref",wtp.get("baseline_ref"),"WIP-BASELINE-MISMATCH"),("status",wtp.get("status"),"WIP-WTP-STATUS-MISMATCH"),("validation_profile",wtp.get("validation_profile"),"WIP-VALIDATION-PROFILE-MISMATCH"))
    for key,want,code in comparisons:
        if binding.get(key)!=want: out.append(Finding(code,f"/wtp_binding/{key}","binding differs from WTP"))
    if ip.get("feature_id")!=wtp.get("feature_id"): out.append(Finding("WIP-FEATURE-MISMATCH","/feature_id","IP and WTP Features differ"))
    if ip.get("baseline_ref")!=wtp.get("baseline_ref"): out.append(Finding("WIP-BASELINE-MISMATCH","/baseline_ref","IP and WTP baselines differ"))
    if wtp.get("status")=="withdrawn" or binding.get("supersession_compatibility") in {"withdrawn","incompatible"}:
        out.append(Finding("WIP-WTP-INVALID","/wtp_binding/status","withdrawn/incompatible WTP is invalid"))
    if binding.get("content_digest")!=wtp_digest:
        out.append(Finding("WIP-REVISION-REQUIRED","/wtp_binding/content_digest","structural WTP drift requires a new IP revision"))
    expected_units=[n.get("work_unit") for n in wtp.get("nodes",[]) if isinstance(n.get("work_unit"),str) and not n["work_unit"].startswith("feature:")]
    for finding in wtp_tool.semantic_findings(wtp,expected_units):
        suffix=finding.code[4:] if finding.code.startswith("WTP-") else finding.code
        out.append(Finding("WIP-WTP-SEMANTIC-"+suffix,finding.path,finding.message))

    required_consumption={"identity-and-versions","feature-and-baseline","nodes-and-edges","scopes-and-overlaps","checkpoints","staleness-and-invalid-classes","validation-and-activation","recovery-and-authority"}
    consumed={x.get("input") for x in binding.get("consumption",[])}
    if consumed!=required_consumption: out.append(Finding("WIP-CONSUMPTION-INCOMPLETE","/wtp_binding/consumption","WTP interface consumption is not exact"))

    snap=ip.get("topology_snapshot",{}); expected_nodes={n.get("node_id") for n in wtp.get("nodes",[])}; expected_edges={edge_id(e) for e in wtp.get("edges",[])}; expected_overlaps={overlap_id(x) for x in wtp.get("overlap_rules",[])}; expected_checkpoints={x.get("work_unit") for x in wtp.get("checkpoints",[])}
    if snap.get("state")=="complete":
        for key,actual,want,code in (("node_ids",set(snap.get("node_ids",[])),expected_nodes,"WIP-NODE-CONSUMPTION"),("edge_ids",set(snap.get("edge_ids",[])),expected_edges,"WIP-EDGE-CONSUMPTION"),("overlap_rule_ids",set(snap.get("overlap_rule_ids",[])),expected_overlaps,"WIP-OVERLAP-CONSUMPTION"),("checkpoint_work_units",set(snap.get("checkpoint_work_units",[])),expected_checkpoints,"WIP-CHECKPOINT-CONSUMPTION")):
            if actual!=want: out.append(Finding(code,f"/topology_snapshot/{key}","snapshot is partial or foreign"))
    elif any(x.get("disposition")=="consumed" and x.get("input") in {"nodes-and-edges","scopes-and-overlaps","checkpoints"} for x in binding.get("consumption",[])):
        out.append(Finding("WIP-TOPOLOGY-UNAVAILABLE","/topology_snapshot/state","consumed topology must be complete"))

    closures=ip.get("acceptance_closures",[]); closure_ids=[x.get("closure_id") for x in closures]
    if _duplicates(closure_ids): out.append(Finding("WIP-CLOSURE-DUPLICATE","/acceptance_closures","closure IDs must be unique"))
    for i,c in enumerate(closures): out.extend(_closure_findings(c,i,binding))
    closure_map={x.get("closure_id"):x for x in closures}

    alternatives={x.get("alternative_id"):x for x in ip.get("reconciliation_alternatives",[])}
    overlap_rules={overlap_id(x):x for x in wtp.get("overlap_rules",[])}
    unit_set={n.get("work_unit") for n in wtp.get("nodes",[])}
    predecessor_pairs={(p.get("work_unit"),n.get("work_unit")) for n in wtp.get("nodes",[]) for p in n.get("predecessor_constraints",[])}
    steps=ip.get("steps",[]); sequences=[x.get("sequence") for x in steps]; step_ids=[x.get("step_id") for x in steps]
    if sequences!=list(range(1,len(steps)+1)) or _duplicates(step_ids): out.append(Finding("WIP-STEP-ORDER","/steps","steps require unique contiguous sequence and IDs"))
    final_indexes=[i for i,s in enumerate(steps) if s.get("operation")=="final-main"]
    if len(final_indexes)!=1 or final_indexes[0]!=len(steps)-1: out.append(Finding("WIP-FINAL-MAIN-POSITION","/steps","final-main must occur exactly once and last"))
    if ip.get("status") not in {"ready","executing"} and any(s.get("consequential") for s in steps): out.append(Finding("WIP-DORMANT-CONSEQUENTIAL","/steps","non-operative plan has consequential step"))
    for i,s in enumerate(steps):
        p=f"/steps/{i}"
        if s.get("reconciliation_alternative") not in alternatives: out.append(Finding("WIP-RECONCILIATION-UNDECLARED",p+"/reconciliation_alternative","strategy was not declared"))
        if s.get("overlap_rule") not in expected_overlaps and s.get("overlap_rule") not in alternatives: out.append(Finding("WIP-OVERLAP-UNKNOWN",p+"/overlap_rule","overlap reference is unknown"))
        overlap=overlap_rules.get(s.get("overlap_rule"))
        if overlap and overlap.get("class")=="concurrent-exclusive" and s.get("state")=="ready": out.append(Finding("WIP-CONCURRENT-COLLISION",p+"/overlap_rule","concurrent-exclusive write scopes cannot activate together"))
        if overlap and overlap.get("class")=="ordered-predecessor" and not s.get("prerequisite_order"): out.append(Finding("WIP-ABSORPTION-ORDER",p+"/prerequisite_order","ordered overlap lacks predecessor order"))
        if s.get("consequential") and any(s.get(k,{}).get("state")!="exact" for k in ("source_pin","target_pin_before","target_tree_before")): out.append(Finding("WIP-PIN-UNRESOLVED",p,"consequential step requires exact pins"))
        closure=closure_map.get(s.get("acceptance_closure_id"))
        if closure is None: out.append(Finding("WIP-CLOSURE-UNKNOWN",p+"/acceptance_closure_id","closure is absent"))
        elif s.get("operation") in {"checkpoint-review","final-main"} and s.get("consequential") and closure.get("state")!="current": out.append(Finding("WIP-ACCEPTANCE-BLOCKING",p,"checkpoint crossing lacks current closure"))
        if s.get("operation")=="absorb-prerequisite" and not s.get("prerequisite_order"): out.append(Finding("WIP-ABSORPTION-ORDER",p+"/prerequisite_order","absorption order is absent"))
        order=s.get("prerequisite_order",[])
        if any(unit not in unit_set for unit in order): out.append(Finding("WIP-ABSORPTION-UNREACHABLE",p+"/prerequisite_order","order references a work unit outside the WTP"))
        positions={unit:j for j,unit in enumerate(order)}
        if any(a in positions and b in positions and positions[a]>=positions[b] for a,b in predecessor_pairs): out.append(Finding("WIP-ABSORPTION-ORDER",p+"/prerequisite_order","predecessor appears after its consumer"))
        if ref_checker is not None:
            for key in ("source_pin","target_pin_before","target_tree_before"):
                pin=s.get(key,{})
                if pin.get("state")=="exact" and not ref_checker(pin.get("ref","")): out.append(Finding("WIP-REF-UNREACHABLE",p+f"/{key}","exact pin is not a reachable object"))
        if s.get("operation")=="final-main":
            if s.get("target_branch")!="main": out.append(Finding("WIP-FINAL-MAIN-TARGET",p+"/target_branch","final-main must target main"))
            evidence=" ".join(str(x.get("command","")) for x in s.get("hygiene",[])).lower()
            if "hygiene" not in evidence or ("root" not in evidence and "preflight" not in evidence): out.append(Finding("WIP-FINAL-MAIN-PREFLIGHT",p+"/hygiene","root preflight and hygiene are required"))
            authority=s.get("authority",{}); auth_text=(str(authority.get("required_role",""))+" "+str(authority.get("authority_ref",""))).lower()
            if s.get("consequential") and ("privileged" not in auth_text or authority.get("authority_ref") in {"not-granted","none",""}): out.append(Finding("WIP-FINAL-MAIN-AUTHORITY",p+"/authority","current privileged external authority is absent"))

    referenced_checkpoints={s.get("checkpoint_work_unit") for s in steps if s.get("checkpoint_work_unit")!="none"}
    if expected_checkpoints-set(referenced_checkpoints): out.append(Finding("WIP-CHECKPOINT-SKIPPED","/steps","one or more WTP checkpoints are not planned"))
    validation_text=" ".join(str(v.get("command","")) for s in steps for v in s.get("validation",[])).lower()
    if not any(s.get("operation")=="integration-test" for s in steps) and "validation profile" not in validation_text:
        out.append(Finding("WIP-TEST-PROFILE-SKIPPED","/steps","integration test or declared validation profile is absent"))

    events=ip.get("events",[])
    if [e.get("sequence") for e in events]!=list(range(1,len(events)+1)): out.append(Finding("WIP-EVENT-ORDER","/events","events must be append-only ordered"))
    for i,e in enumerate(events):
        if e.get("event_digest")!=digest(e,{"event_digest","created_at"}): out.append(Finding("WIP-EVENT-DIGEST-MISMATCH",f"/events/{i}/event_digest","event digest differs"))
    normalized={"ip_digest":ip_digest,"wtp_digest":wtp_digest,"topology":{"nodes":sorted(expected_nodes),"edges":sorted(expected_edges),"overlaps":sorted(expected_overlaps),"checkpoints":sorted(expected_checkpoints)},"closures":[{"id":c.get("closure_id"),"digest":c.get("closure_digest")} for c in sorted(closures,key=lambda x:str(x.get("closure_id")))]}
    out=sorted(set(out))
    return {"schema":REPORT_SCHEMA,"valid":not out,"plan_digest":ip_digest,"closure_set_digest":digest(normalized),"findings":[asdict(x) for x in out]}


def _load(path: Path) -> dict[str,Any]:
    def pairs(values):
        out={}
        for k,v in values:
            if k in out: raise ValueError(f"duplicate key: {k}")
            out[k]=v
        return out
    return json.loads(path.read_text(encoding="utf-8"),parse_float=lambda _:(_ for _ in ()).throw(ValueError("float token")),object_pairs_hook=pairs)


def main(argv: list[str]|None=None) -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("ip",type=Path); ap.add_argument("wtp",type=Path); ap.add_argument("--ip-schema",type=Path,default=Path("docs/pipeline/integration-plan.schema.json")); ap.add_argument("--wtp-schema",type=Path,default=Path("docs/pipeline/worktree-topology-plan.schema.json")); ap.add_argument("--wtp-ref",required=True); ap.add_argument("--repo",type=Path,default=Path("."))
    ns=ap.parse_args(argv)
    def reachable(ref: str) -> bool:
        return bool(ref) and subprocess.run(["git","-C",str(ns.repo),"cat-file","-e",f"{ref}^{{object}}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False).returncode==0
    try: report=validate(_load(ns.ip),_load(ns.wtp),_load(ns.ip_schema),_load(ns.wtp_schema),wtp_ref=ns.wtp_ref,ref_checker=reachable)
    except (KeyError,OSError,TypeError,ValueError,UnicodeError,json.JSONDecodeError) as exc: report={"schema":REPORT_SCHEMA,"valid":False,"plan_digest":None,"closure_set_digest":None,"findings":[asdict(Finding("WIP-INPUT-ERROR","/",str(exc)))]}
    print(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)); return 0 if report["valid"] else 1


if __name__=="__main__": raise SystemExit(main())
