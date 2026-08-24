#!/usr/bin/env python3
"""Capture the one-time Feature branch-ref input used by the migration candidate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]


def canonical(value): return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--baseline",required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    baseline=subprocess.check_output(["git","-C",str(ROOT),"rev-parse",args.baseline],text=True).strip(); todo=subprocess.check_output(["git","-C",str(ROOT),"show",f"{baseline}:TODO.md"],text=True)
    feature_ids=re.findall(r"^## Feature: (\d{4}) —",todo,re.M); branches={}
    for fid in feature_ids:
        proc=subprocess.run(["git","-C",str(ROOT),"rev-parse","--verify",f"refs/heads/{fid}"],text=True,capture_output=True)
        branches[fid]={"name":fid,"state":"reachable" if proc.returncode==0 else "unavailable","ref":proc.stdout.strip() if proc.returncode==0 else None}
    result={"schema":"feature-branch-snapshot@v1","baseline_ref":baseline,"branches":branches,"snapshot_digest":""}; result["snapshot_digest"]="sha256:"+hashlib.sha256(canonical({k:v for k,v in result.items() if k!="snapshot_digest"})).hexdigest(); args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
