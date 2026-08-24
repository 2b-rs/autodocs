#!/usr/bin/env python3
"""Dormant digest-bound rollback executor; it has no admission/deployment call site."""
from __future__ import annotations
import argparse,base64,hashlib,json,os,time
from pathlib import Path
from typing import Any
POLICY="issues/_policy/runner-protocol-rollback-v1.json"; MARKER=".runner/rollback-v1.json"; LOCK=".runner/rollback-v1.lock"; BLOCKED=".runner/rollback-blocked.json"; EVENTS=".runner/rollback-events.jsonl"
FAILURES=("digest","write","verify","lock","timeout","event")
def sha256_bytes(data:bytes)->str:return "sha256:"+hashlib.sha256(data).hexdigest()
def atomic_write(p:Path,data:bytes)->None:
 p.parent.mkdir(parents=True,exist_ok=True); q=p.with_name(p.name+".rollback-tmp");q.write_bytes(data);os.replace(q,p)
def load_bundle(repo:Path)->list[dict[str,Any]]:
 o=json.loads((repo/POLICY).read_text()); assert o.get("schema")=="runner-protocol-rollback@v1" and o.get("lineage_commit")=="46fdd63983"
 out=[]; seen=set()
 for t in o.get("targets",[]):
  d=base64.b64decode(t["base64"],validate=True)
  if t.get("path") not in {"agent-workflow.json","issues/_policy/runner-service.json"} or t["path"] in seen or sha256_bytes(d)!=t.get("sha256"):raise ValueError("bundle digest mismatch")
  seen.add(t["path"]);out.append({**t,"payload":d})
 if len(out)!=2:raise ValueError("invalid targets")
 return out
def _event(repo:Path,event:dict[str,Any],fail:str|None=None)->None:
 if fail=="event":raise RuntimeError("injected event failure")
 p=repo/EVENTS;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("a") as f:f.write(json.dumps(event,sort_keys=True)+"\n");f.flush();os.fsync(f.fileno())
def _block(repo:Path,reason:str,marker:dict[str,Any])->dict[str,Any]:
 s={"schema":"runner-protocol-rollback-blocked@v1","status":"blocked","reason":reason,"marker":marker};atomic_write(repo/BLOCKED,(json.dumps(s,sort_keys=True)+"\n").encode());return s
def execute(repo:Path,*,timeout:float=30,fail_at:str|None=None)->dict[str,Any]:
 if fail_at not in (*FAILURES,None):raise ValueError("unknown failure injection")
 m={"schema":"runner-protocol-rollback-marker@v1","status":"running","lineage_commit":"46fdd63983"};lock=repo/LOCK
 try:lock.parent.mkdir(parents=True,exist_ok=True);os.mkdir(lock)
 except FileExistsError:return _block(repo,"lock",m)
 try:
  if fail_at=="lock":raise RuntimeError("injected lock failure")
  atomic_write(repo/MARKER,(json.dumps(m,sort_keys=True)+"\n").encode());_event(repo,{"event":"rollback-started"},fail_at)
  if fail_at=="digest":raise ValueError("injected digest failure")
  targets=load_bundle(repo);deadline=time.monotonic()+timeout
  while list((repo/".runner/claims").glob("*.lease.json")):
   if fail_at=="timeout" or time.monotonic()>=deadline:raise TimeoutError("active-claim drain timed out")
   time.sleep(.01)
  for t in sorted(targets,key=lambda x:0 if x["path"].endswith("runner-service.json") else 1):
   if fail_at=="write":raise OSError("injected write failure")
   atomic_write(repo/t["path"],t["payload"])
   if fail_at=="verify" or sha256_bytes((repo/t["path"]).read_bytes())!=t["sha256"]:raise RuntimeError("restore verification failed")
  m["status"]="restored";atomic_write(repo/MARKER,(json.dumps(m,sort_keys=True)+"\n").encode());_event(repo,{"event":"rollback-restored"},fail_at);return {"ok":True,"status":"restored","marker":m}
 except Exception as e:
  m.update(status="blocked",error=str(e));_block(repo,fail_at or "failure",m)
  try:_event(repo,{"event":"rollback-blocked","reason":fail_at or "failure"})
  except Exception:pass
  return {"ok":False,"status":"blocked","reason":fail_at or "failure"}
 finally:
  try:os.rmdir(lock)
  except OSError:pass
def prove(repo:Path,failure_store:str|None=None)->dict[str,Any]:return execute(repo,fail_at=failure_store)
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--repo",default=".");p.add_argument("--prove",action="store_true");p.add_argument("--failure-store",choices=FAILURES);a=p.parse_args();r=prove(Path(a.repo).resolve(),a.failure_store) if a.prove else execute(Path(a.repo).resolve());print(json.dumps(r,sort_keys=True));return 0 if r["ok"] else 1
if __name__=="__main__":raise SystemExit(main())
