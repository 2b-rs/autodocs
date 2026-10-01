#!/usr/bin/env python3
"""Fail-closed validation for the Task-0046-05 migration candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
ALLOWED={"migrated","compatible-with-bounds","deferred"}


def digest(value): return "sha256:"+hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
def reachable(ref): return subprocess.run(["git","-C",str(ROOT),"cat-file","-e",f"{ref}^{{commit}}"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0


def validate(manifest,inventory,branch_snapshot):
    findings=[]; rows=manifest.get("rows",[]); expected={x["feature_id"] for x in inventory.get("features",[])}; actual=[x.get("feature_id") for x in rows]
    snapshot_digest=digest({k:v for k,v in branch_snapshot.items() if k!="snapshot_digest"})
    if branch_snapshot.get("snapshot_digest")!=snapshot_digest or manifest.get("branch_snapshot_digest")!=snapshot_digest or inventory.get("branch_snapshot_digest")!=snapshot_digest: findings.append("MIGRATION-BRANCH-SNAPSHOT-DIGEST")
    if branch_snapshot.get("baseline_ref")!=manifest.get("baseline_ref"): findings.append("MIGRATION-BRANCH-SNAPSHOT-BASELINE")
    if set(branch_snapshot.get("branches",{}))!=expected: findings.append("MIGRATION-BRANCH-SNAPSHOT-POPULATION")
    if set(actual)!=expected: findings.append("MIGRATION-POPULATION-MISMATCH")
    if len(actual)!=len(set(actual)): findings.append("MIGRATION-DUPLICATE-FEATURE")
    if manifest.get("population_count")!=len(rows): findings.append("MIGRATION-COUNT-MISMATCH")
    if set(manifest.get("allowed_dispositions",[]))!=ALLOWED: findings.append("MIGRATION-DISPOSITION-VOCABULARY")
    if manifest.get("baseline_ref")!=inventory.get("baseline_ref") or manifest.get("todo_digest")!=inventory.get("todo_digest") or manifest.get("branch_snapshot_digest")!=inventory.get("branch_snapshot_digest"): findings.append("MIGRATION-BASELINE-MISMATCH")
    if not reachable(manifest.get("baseline_ref","")): findings.append("MIGRATION-BASELINE-UNREACHABLE")
    by_id={x["feature_id"]:x for x in inventory.get("features",[])}
    for row in rows:
        fid=row.get("feature_id"); inv=by_id.get(fid,{})
        if row.get("baseline_ref")!=manifest.get("baseline_ref"): findings.append(f"MIGRATION-ROW-BASELINE:{fid}")
        if row.get("disposition") not in ALLOWED: findings.append(f"MIGRATION-DISPOSITION:{fid}")
        if row.get("work_units")!=inv.get("work_units") or row.get("mandatory_gates")!=inv.get("mandatory_gates"): findings.append(f"MIGRATION-INVENTORY-DRIFT:{fid}")
        if not row.get("owner") or not row.get("revisit_trigger"): findings.append(f"MIGRATION-OWNER-TRIGGER:{fid}")
        if not row.get("omissions") or not row.get("risk") or not row.get("recovery") or not row.get("validator_result"): findings.append(f"MIGRATION-REQUIRED-FIELD:{fid}")
        branch=row.get("feature_branch",{}); ref=branch.get("ref")
        if branch.get("name")!=fid or branch.get("state") not in {"reachable","unavailable"}: findings.append(f"MIGRATION-BRANCH-IDENTITY:{fid}")
        if branch!=inv.get("feature_branch"): findings.append(f"MIGRATION-BRANCH-BINDING:{fid}")
        if branch!=branch_snapshot.get("branches",{}).get(fid): findings.append(f"MIGRATION-BRANCH-SNAPSHOT-BINDING:{fid}")
        if branch.get("state")=="reachable" and (not ref or not reachable(ref)): findings.append(f"MIGRATION-BRANCH-UNREACHABLE:{fid}")
        if branch.get("state")=="unavailable" and ref is not None: findings.append(f"MIGRATION-BRANCH-STATE:{fid}")
        if row.get("disposition")=="migrated" and (not row.get("wtp_evidence") or not row.get("ip_evidence")): findings.append(f"MIGRATION-HIDDEN-COMPLIANCE:{fid}")
        for evidence in row.get("wtp_evidence",[])+row.get("ip_evidence",[]):
            if not isinstance(evidence,dict) or not evidence.get("path") or not evidence.get("ref"): findings.append(f"MIGRATION-EVIDENCE-BINDING:{fid}")
            elif not reachable(evidence["ref"]): findings.append(f"MIGRATION-EVIDENCE-UNREACHABLE:{fid}")
    expected_digest=digest({k:v for k,v in manifest.items() if k!="manifest_digest"})
    if manifest.get("manifest_digest")!=expected_digest: findings.append("MIGRATION-DIGEST-MISMATCH")
    return {"schema":"feature-migration-validation@v1","valid":not findings,"feature_count":len(rows),"disposition_counts":{x:sum(r.get("disposition")==x for r in rows) for x in sorted(ALLOWED)},"manifest_digest":expected_digest,"findings":sorted(set(findings))}


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--manifest",type=Path,required=True); parser.add_argument("--inventory",type=Path,required=True); parser.add_argument("--branch-map",type=Path,required=True); parser.add_argument("--output",type=Path); args=parser.parse_args(); result=validate(json.loads(args.manifest.read_text()),json.loads(args.inventory.read_text()),json.loads(args.branch_map.read_text())); rendered=json.dumps(result,sort_keys=True,indent=2)+"\n"; print(rendered,end="");
    if args.output: args.output.write_text(rendered)
    raise SystemExit(0 if result["valid"] else 1)
