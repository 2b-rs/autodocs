#!/usr/bin/env python3
"""Deterministic, read-only validator for Worktree Topology Plans (0046-02)."""
from __future__ import annotations

import argparse, hashlib, json, re, subprocess, sys
from datetime import datetime
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "worktree-topology-plan@v1"
CANONICALIZATION = "json-sort-utf8-no-floats@v1"
DIGEST_ALGORITHM = "sha256"
REPORT_VERSION = "wtp-validation-report@v1"

@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    message: str

def _walk_no_floats(value: Any, path: str = "") -> None:
    if isinstance(value, float):
        raise ValueError(f"float at {path or '/'}")
    if isinstance(value, dict):
        for key, child in value.items():
            _walk_no_floats(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_no_floats(child, f"{path}/{index}")

def canonical_bytes(plan: dict[str, Any]) -> bytes:
    payload = dict(plan)
    payload.pop("content_digest", None)
    _walk_no_floats(payload)
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")

def content_digest(plan: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(plan)).hexdigest()

def _ref(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not ref:
        return schema
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported schema ref {ref}")
    cur: Any = root
    for part in ref[2:].split("/"):
        cur = cur[part.replace("~1", "/").replace("~0", "~")]
    return cur

def _schema_findings(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "") -> list[Finding]:
    schema = _ref(schema, root)
    out: list[Finding] = []
    p = path or "/"
    if "oneOf" in schema:
        matches = [not _schema_findings(value, item, root, path) for item in schema["oneOf"]]
        return [] if sum(matches) == 1 else [Finding("WTP-SCHEMA-ONEOF", p, "value must match exactly one alternative")]
    if "const" in schema and value != schema["const"]:
        out.append(Finding("WTP-SCHEMA-CONST", p, "value differs from required constant"))
    if "enum" in schema and value not in schema["enum"]:
        out.append(Finding("WTP-SCHEMA-ENUM", p, "value is outside the closed enumeration"))
    typ = schema.get("type")
    ok = typ is None or ({"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str), "boolean": type(value) is bool}.get(typ, True))
    if not ok:
        return out + [Finding("WTP-SCHEMA-TYPE", p, f"expected {typ}")]
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0): out.append(Finding("WTP-SCHEMA-MIN_LENGTH", p, "string is too short"))
        if "pattern" in schema and re.search(schema["pattern"], value) is None: out.append(Finding("WTP-SCHEMA-PATTERN", p, "string does not match pattern"))
        if schema.get("format") == "date-time":
            try: datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError: out.append(Finding("WTP-SCHEMA-FORMAT", p, "string is not an ISO-8601 date-time"))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): out.append(Finding("WTP-SCHEMA-MIN_ITEMS", p, "array has too few items"))
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True, ensure_ascii=False) for x in value}) != len(value):
            out.append(Finding("WTP-SCHEMA-UNIQUE_ITEMS", p, "array items must be unique"))
        for i, child in enumerate(value): out.extend(_schema_findings(child, schema.get("items", {}), root, f"{path}/{i}"))
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value: out.append(Finding("WTP-SCHEMA-REQUIRED", f"{path}/{key}", "required property is missing"))
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value.keys() - props.keys(): out.append(Finding("WTP-SCHEMA-ADDITIONAL", f"{path}/{key}", "additional property is forbidden"))
        for key in value.keys() & props.keys(): out.extend(_schema_findings(value[key], props[key], root, f"{path}/{key}"))
    return out

def _rules_overlap(a: dict[str, str], b: dict[str, str]) -> bool:
    ap, bp = a["path"].rstrip("/"), b["path"].rstrip("/")
    if a["match"] == b["match"] == "exact": return ap == bp
    return ap == bp or (a["match"] == "prefix" and bp.startswith(ap + "/")) or (b["match"] == "prefix" and ap.startswith(bp + "/"))

def semantic_findings(plan: dict[str, Any], expected_work_units: Iterable[str] | None = None) -> list[Finding]:
    f: list[Finding] = []
    nodes = plan.get("nodes", []) if isinstance(plan.get("nodes"), list) else []
    ids = [n.get("node_id") for n in nodes if isinstance(n, dict)]
    units = [n.get("work_unit") for n in nodes if isinstance(n, dict)]
    for code, vals, path in [("WTP-DUPLICATE-NODE", ids, "/nodes"),("WTP-DUPLICATE-WORK-UNIT", units, "/nodes")]:
        if len(vals) != len(set(vals)): f.append(Finding(code, path, "values must be unique"))
    mains = [n for n in nodes if n.get("is_main_worktree") is True]
    if len(mains) != 1 or (mains and (mains[0].get("branch") != "main" or mains[0].get("lifecycle") != "retained" or mains[0].get("write_scope") != [])):
        f.append(Finding("WTP-MAIN-NODE", "/nodes", "exactly one retained read-only main node is required"))
    active = [n for n in nodes if n.get("lifecycle") in {"planned", "active"}]
    for field, code in [("branch","WTP-DUPLICATE-BRANCH"),("worktree_path","WTP-DUPLICATE-WORKTREE")]:
        vals=[n.get(field) for n in active]
        if len(vals)!=len(set(vals)): f.append(Finding(code,"/nodes",f"active {field} values must be unique"))
    node_ids=set(ids)
    unit_nodes={n.get("work_unit"):n for n in nodes if isinstance(n.get("work_unit"),str)}
    graph={x:set() for x in node_ids}
    edge_keys=set()
    for i,e in enumerate(plan.get("edges", [])):
        key=(e.get("from"),e.get("to"),e.get("kind"))
        if key in edge_keys: f.append(Finding("WTP-DUPLICATE-EDGE",f"/edges/{i}","structural edge is duplicated"))
        edge_keys.add(key)
        if e.get("from") not in node_ids or e.get("to") not in node_ids: f.append(Finding("WTP-EDGE-ENDPOINT",f"/edges/{i}","edge endpoint is unknown")); continue
        if e.get("kind") in {"base","prerequisite-content"}: graph[e["from"]].add(e["to"])
    visiting:set[str]=set(); done:set[str]=set()
    def visit(n:str)->bool:
        if n in visiting:return True
        if n in done:return False
        visiting.add(n); cyclic=any(visit(x) for x in graph[n]); visiting.remove(n); done.add(n); return cyclic
    if any(visit(n) for n in list(graph)): f.append(Finding("WTP-GRAPH-CYCLE","/edges","base/prerequisite graph must be acyclic"))
    for i,n in enumerate(nodes):
        unit=n.get("work_unit","")
        if n.get("is_main_worktree") is True: continue
        if isinstance(unit,str) and unit.startswith("task:"):
            expected_base=unit.split(":",1)[1].split("-",1)[0]
        elif isinstance(unit,str) and unit.startswith("subtask:"):
            expected_base=unit.split(":",1)[1].rsplit(".",1)[0]
        else: expected_base=None
        if expected_base is not None and n.get("base_branch") != expected_base:
            f.append(Finding("WTP-BRANCH-HIERARCHY",f"/nodes/{i}/base_branch",f"expected {expected_base}"))
        if isinstance(unit,str) and unit.split(":",1)[-1].split("-",1)[0] != plan.get("feature_id"):
            f.append(Finding("WTP-FEATURE-IDENTITY-MISMATCH",f"/nodes/{i}/work_unit","work unit belongs to another Feature"))
        if not n.get("write_scope"):
            f.append(Finding("WTP-WRITE-SCOPE-EMPTY",f"/nodes/{i}/write_scope","executable work unit requires write ownership"))
        for j,pred in enumerate(n.get("predecessor_constraints", [])):
            producer=unit_nodes.get(pred.get("work_unit"))
            if producer is None:
                f.append(Finding("WTP-PREDECESSOR-UNKNOWN",f"/nodes/{i}/predecessor_constraints/{j}","predecessor work unit is absent"))
            elif (producer.get("node_id"),n.get("node_id"),"prerequisite-content") not in edge_keys:
                f.append(Finding("WTP-PREDECESSOR-EDGE-MISSING",f"/nodes/{i}/predecessor_constraints/{j}","predecessor constraint lacks matching edge"))
    if expected_work_units is None: f.append(Finding("WTP-EXPECTED-POPULATION-REQUIRED","/nodes","complete validation requires expected work units"))
    else:
        expected=set(expected_work_units); actual={u for u in units if isinstance(u,str) and not u.startswith("feature:")}
        if actual != expected: f.append(Finding("WTP-PARTIAL-GRAPH","/nodes","work-unit population differs from expected set"))
    overlap_pairs=set()
    for i,r in enumerate(plan.get("overlap_rules", [])):
        pair=tuple(sorted((r.get("left"),r.get("right"))))
        if pair in overlap_pairs: f.append(Finding("WTP-OVERLAP-DUPLICATE",f"/overlap_rules/{i}","node pair has more than one classification"))
        overlap_pairs.add(pair)
        if pair[0] not in node_ids or pair[1] not in node_ids: f.append(Finding("WTP-OVERLAP-ENDPOINT",f"/overlap_rules/{i}","overlap endpoint is unknown"))
        left=next((n for n in nodes if n.get("node_id")==r.get("left")),None); right=next((n for n in nodes if n.get("node_id")==r.get("right")),None)
        if left and right:
            intersections=[(a,b) for a in left.get("write_scope",[]) for b in right.get("write_scope",[]) if _rules_overlap(a,b)]
            if not intersections: f.append(Finding("WTP-OVERLAP-SPURIOUS",f"/overlap_rules/{i}","classification has no intersecting write scope"))
            for j,path_rule in enumerate(r.get("paths",[])):
                if not any(_rules_overlap(path_rule,a) and _rules_overlap(path_rule,b) for a,b in intersections):
                    f.append(Finding("WTP-OVERLAP-PATH-OUTSIDE",f"/overlap_rules/{i}/paths/{j}","declared path is outside the owned intersection"))
    for i,a in enumerate(active):
        for b in active[i+1:]:
            if any(_rules_overlap(x,y) for x in a.get("write_scope",[]) for y in b.get("write_scope",[])) and tuple(sorted((a["node_id"],b["node_id"]))) not in overlap_pairs:
                f.append(Finding("WTP-OVERLAP-MISSING","/overlap_rules",f"missing classification for {a['node_id']} and {b['node_id']}"))
    checkpoints=plan.get("checkpoints",[])
    checkpoint_units={c.get("work_unit") for c in checkpoints}
    if not checkpoint_units <= set(units): f.append(Finding("WTP-CHECKPOINT-UNKNOWN","/checkpoints","checkpoint work unit is absent"))
    main_id=mains[0].get("node_id") if len(mains)==1 else None
    integration_edges=[e for e in plan.get("edges",[]) if e.get("kind")=="integration-target" and e.get("to")==main_id]
    terminal=[u for u in checkpoint_units if isinstance(u,str) and u.startswith("task:") and any(next((n.get("work_unit") for n in nodes if n.get("node_id")==e.get("from")),None)==u for e in integration_edges)]
    if len(terminal)!=1: f.append(Finding("WTP-TERMINAL-CHECKPOINT","/checkpoints","exactly one terminal integrating Task checkpoint is required"))
    if len(integration_edges)!=1: f.append(Finding("WTP-INTEGRATION-TARGET","/edges","exactly one integration target into main is required"))
    if any(e.get("to")==main_id and e.get("kind")!="integration-target" for e in plan.get("edges",[])):
        f.append(Finding("WTP-MAIN-EDGE-UNAUTHORIZED","/edges","only the terminal integration target may enter main"))
    vp=plan.get("validation_profile",{})
    if len(vp.get("required_stages",[])) != len(set(vp.get("required_stages",[]))): f.append(Finding("WTP-VALIDATION-STAGE-DUPLICATE","/validation_profile/required_stages","stages must be unique"))
    if plan.get("status") == "withdrawn" or (isinstance(plan.get("supersedes"),dict) and plan["supersedes"].get("compatibility")=="incompatible"):
        f.append(Finding("WTP-PLAN-INVALID","/status","withdrawn or incompatible plan is invalid"))
    required_invalid={"unreproducible digest","withdrawn plan","incompatible supersession","partial graph","unknown overlap class","duplicate active branch or worktree"}
    if not required_invalid <= set(plan.get("staleness_policy",{}).get("invalid_conditions",[])): f.append(Finding("WTP-INVALID-CLASSES-INCOMPLETE","/staleness_policy/invalid_conditions","closed invalid classes are incomplete"))
    required_blocking={"/feature_id","/baseline_ref","/nodes","/edges","/overlap_rules","/checkpoints","/activation","/recovery"}
    if not required_blocking <= set(plan.get("staleness_policy",{}).get("blocking_structural_fields",[])): f.append(Finding("WTP-BLOCKING-CLASSES-INCOMPLETE","/staleness_policy/blocking_structural_fields","closed blocking structural fields are incomplete"))
    if plan.get("activation",{}).get("grandfathering") != "forbidden": f.append(Finding("WTP-GRANDFATHERING","/activation/grandfathering","implicit grandfathering is forbidden"))
    if plan.get("activation",{}).get("self_application_feature") != plan.get("feature_id"):
        f.append(Finding("WTP-ACTIVATION-FEATURE-MISMATCH","/activation/self_application_feature","activation Feature must match plan Feature"))
    if plan.get("activation",{}).get("migration_required") is not True:
        f.append(Finding("WTP-MIGRATION-REQUIRED","/activation/migration_required","migration disposition must be explicit"))
    expected_mode={"candidate":"dormant","trial":"trial","active":"active"}.get(plan.get("status"))
    if expected_mode and plan.get("activation",{}).get("mode") != expected_mode:
        f.append(Finding("WTP-ACTIVATION-STATUS-MISMATCH","/activation/mode","activation mode conflicts with plan status"))
    return f

def _ref_findings(plan_path: Path, plan_ref: str | None, repo: Path) -> list[Finding]:
    if not plan_ref:
        return [Finding("WTP-REF-REQUIRED","/","a committed WTP REF is required")]
    if re.fullmatch(r"[0-9a-f]{40}",plan_ref) is None:
        return [Finding("WTP-REF-FORMAT","/","WTP REF must be a full commit hash")]
    resolved=subprocess.run(["git","-C",str(repo),"cat-file","-e",f"{plan_ref}^{{commit}}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
    if resolved.returncode:
        return [Finding("WTP-REF-UNREACHABLE","/", "WTP REF does not resolve to a commit")]
    try: rel=plan_path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError: return [Finding("WTP-REF-PATH","/","plan must be inside the repository")]
    committed=subprocess.run(["git","-C",str(repo),"show",f"{plan_ref}:{rel}"],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False)
    if committed.returncode or committed.stdout != plan_path.read_bytes():
        return [Finding("WTP-REF-CONTENT-MISMATCH","/","REF does not contain the exact plan bytes at this path")]
    return []

def validate(plan: dict[str, Any], schema: dict[str, Any], expected_work_units: Iterable[str] | None = None, ref_findings: Iterable[Finding] = ()) -> dict[str, Any]:
    findings: list[Finding] = []
    try: _walk_no_floats(plan)
    except ValueError as exc: findings.append(Finding("WTP-FLOAT-FORBIDDEN","/",str(exc)))
    for key, expected, code in [("schema_version",SCHEMA_VERSION,"WTP-SCHEMA-VERSION"),("canonicalization_version",CANONICALIZATION,"WTP-CANONICALIZATION-UNSUPPORTED"),("digest_algorithm",DIGEST_ALGORITHM,"WTP-DIGEST-ALGORITHM-UNSUPPORTED")]:
        if plan.get(key)!=expected: findings.append(Finding(code,f"/{key}","unsupported identity algorithm/version"))
    findings.extend(_schema_findings(plan,schema,schema))
    try:
        actual=content_digest(plan)
        if plan.get("content_digest")!=actual: findings.append(Finding("WTP-DIGEST-MISMATCH","/content_digest",f"expected {actual}"))
    except ValueError: actual=None
    findings.extend(semantic_findings(plan,expected_work_units))
    findings.extend(ref_findings)
    findings=sorted(set(findings))
    return {"schema":REPORT_VERSION,"valid":not findings,"content_digest":actual,"findings":[asdict(x) for x in findings]}

def main(argv:list[str]|None=None)->int:
    ap=argparse.ArgumentParser(); ap.add_argument("plan",type=Path); ap.add_argument("--schema",type=Path,default=Path("docs/pipeline/worktree-topology-plan.schema.json")); ap.add_argument("--expected-work-unit",action="append"); ap.add_argument("--plan-ref"); ap.add_argument("--repo",type=Path,default=Path("."))
    ns=ap.parse_args(argv)
    try:
        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any]={}
            for key,value in pairs:
                if key in result: raise ValueError(f"duplicate object key: {key}")
                result[key]=value
            return result
        plan=json.loads(ns.plan.read_text(encoding="utf-8"),parse_float=lambda _: (_ for _ in ()).throw(ValueError("float token")),object_pairs_hook=reject_duplicates)
        schema=json.loads(ns.schema.read_text(encoding="utf-8"))
        report=validate(plan,schema,ns.expected_work_unit,_ref_findings(ns.plan,ns.plan_ref,ns.repo))
    except (OSError,json.JSONDecodeError,UnicodeError,ValueError) as exc:
        report={"schema":REPORT_VERSION,"valid":False,"content_digest":None,"findings":[asdict(Finding("WTP-INPUT-ERROR","/",str(exc)))]}
    print(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)); return 0 if report["valid"] else 1

if __name__=="__main__": raise SystemExit(main())
