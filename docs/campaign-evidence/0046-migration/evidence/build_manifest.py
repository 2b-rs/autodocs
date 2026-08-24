#!/usr/bin/env python3
"""Reproducibly build the Task-0046-05 migration candidate from one Git baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/"docs/campaign-evidence/0046-migration"


def git(*args: str) -> str:
    return subprocess.check_output(["git","-C",str(ROOT),*args],text=True).strip()


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()


def sha(value: bytes) -> str:
    return "sha256:"+hashlib.sha256(value).hexdigest()


def inventory(baseline: str):
    todo=subprocess.check_output(["git","-C",str(ROOT),"show",f"{baseline}:TODO.md"])
    text=todo.decode(); heads=list(re.finditer(r"^## Feature: (\d{4}) — (.+)$",text,re.M)); rows=[]
    for index,match in enumerate(heads):
        block=text[match.end():heads[index+1].start() if index+1<len(heads) else len(text)]
        fid,title=match.groups(); task_matches=list(re.finditer(rf"^- \[[^]]\] \*\*({fid}(?:-[0-9]+(?:\.[0-9]+)?)?)\*\*",block,re.M)); tasks=[m.group(1) for m in task_matches]; gates=[]
        for j,item in enumerate(task_matches):
            task_block=block[item.end():task_matches[j+1].start() if j+1<len(task_matches) else len(block)]
            if re.search(r"Integration review:\**\s+\**mandatory",task_block,re.I): gates.append(item.group(1))
        proc=subprocess.run(["git","-C",str(ROOT),"rev-parse","--verify",f"refs/heads/{fid}"],text=True,capture_output=True)
        branch_ref=proc.stdout.strip() if proc.returncode==0 else None
        rows.append({"feature_id":fid,"title":title,"work_units":tasks,"mandatory_gates":gates,"feature_branch":{"name":fid,"state":"reachable" if branch_ref else "unavailable","ref":branch_ref}})
    return todo,rows


def build(baseline: str) -> None:
    baseline=git("rev-parse",baseline); todo,items=inventory(baseline); rows=[]
    for item in items:
        fid=item["feature_id"]; is_trial=fid=="0046"
        rows.append({
            **item,
            "baseline_ref":baseline,
            "disposition":"compatible-with-bounds" if is_trial else "deferred",
            "wtp_evidence":[{"path":"docs/pipeline/worktree-topology-plan.md","ref":"4d84c169d89465d8aa35b852333f12c1479efab3"}] if is_trial else [],
            "ip_evidence":[{"path":"docs/campaign-evidence/0046-trial/integration-plan.json","ref":"4d84c169d89465d8aa35b852333f12c1479efab3"}] if is_trial else [],
            "omissions":["complete issued WTP instance","current bound executable IP","migration checkpoint decision"] if is_trial else ["Feature-specific WTP","Feature-specific IP","independent migration review"],
            "risk":"Trial artifacts are dormant and incomplete; compatibility grants no execution authority." if is_trial else "Unknown topology/overlap/closure compatibility; existing governance remains controlling.",
            "owner":f"Projektleitung or explicitly assigned owner for Feature {fid}",
            "revisit_trigger":"After complete conforming WTP/IP candidates and independent migration review exist." if is_trial else "Before any WTP/IP gate is applied to this Feature, or when its assigned owner prepares migration.",
            "recovery":"Withdraw/supersede this manifest row; retain prior rules, claims, Acceptance, verdicts, and history.",
            "validator_result":{"state":"compatible-bounded-no-activation" if is_trial else "deferred-explicit-unknown","evidence_ref":baseline}
        })
    manifest={"schema":"feature-migration-manifest@v1","baseline_ref":baseline,"todo_digest":sha(todo),"allowed_dispositions":["migrated","compatible-with-bounds","deferred"],"population_count":len(rows),"rows":rows,"manifest_digest":""}
    manifest["manifest_digest"]=sha(canonical({k:v for k,v in manifest.items() if k!="manifest_digest"}))
    OUT.mkdir(parents=True,exist_ok=True); (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    evidence=OUT/"evidence"; evidence.mkdir(exist_ok=True); (evidence/"inventory.json").write_text(json.dumps({"schema":"feature-inventory@v1","baseline_ref":baseline,"todo_digest":sha(todo),"features":items},ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    counts={d:sum(r["disposition"]==d for r in rows) for d in manifest["allowed_dispositions"]}
    lines=["# Feature 0046 migration/compatibility candidate","",f"Pinned baseline: `{baseline}`","",f"TODO digest: `{manifest['todo_digest']}`","",f"Manifest digest: `{manifest['manifest_digest']}`","", "This is a dormant migration candidate, not activation, Acceptance, or a QA conclusion. Existing governance remains controlling for every deferred or bounded-compatible Feature.","","## Result","",f"Exact active-Feature population: **{len(rows)}**. Dispositions: migrated **{counts['migrated']}**, compatible-with-bounds **{counts['compatible-with-bounds']}**, deferred **{counts['deferred']}**.","","| Feature | Branch baseline | Work units | Gates | Disposition |", "|---|---|---:|---:|---|"]
    for row in rows: lines.append(f"| {row['feature_id']} | `{row['feature_branch']['ref'] or 'unavailable'}` | {len(row['work_units'])} | {len(row['mandatory_gates'])} | `{row['disposition']}` |")
    lines += ["","## Interpretation","","Feature `0046` is bounded-compatible only with its dormant candidate contracts and trial IP; it lacks a complete issued WTP instance and receives no activation or execution authority. Every other Feature is explicitly deferred because complete Feature-specific WTP/IP evidence and an independent migration decision are absent. Missing Feature branches are recorded as unavailable, never replaced by an invented ref.","","## Reproduction","","```sh",f"python3 docs/campaign-evidence/0046-migration/evidence/build_manifest.py --baseline {baseline}","python3 docs/campaign-evidence/0046-migration/evidence/validate_manifest.py --manifest docs/campaign-evidence/0046-migration/manifest.json --inventory docs/campaign-evidence/0046-migration/evidence/inventory.json","```","","A distinct QA participant must independently audit process conformance; this report intentionally contains no QA verdict."]
    (OUT/"report.md").write_text("\n".join(lines)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--baseline",required=True); args=parser.parse_args(); build(args.baseline)
