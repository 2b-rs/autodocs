#!/usr/bin/env python3
"""Offline-Test des Live-Verteilungsjobs (live_distribute.py) mit falschem agy, echtem agy_switch.py und einem
lokalen Bare-Repo als autodocs-live. Kein Modellaufruf, keine Secrets, kein Netz.

    python3 .github/scripts/test_live_distribute.py
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import live_core as core  # noqa: E402
import live_method as M  # noqa: E402

MARK = "ZEBRAQUAGGA"

FAKE_AGY = r'''#!__PY__
import json, os, re, sys
cfg = json.load(open(__CONFIG__))
argv = sys.argv[1:]
home = os.environ.get("HOME", "")
name = os.path.basename(home.rstrip("/")).replace("agy-profile-", "")
prompt = argv[argv.index("-p") + 1]
st = os.path.join(home, ".gemini", "antigravity-cli", "settings.json")
with open(__LOG__, "a") as fh:
    fh.write(json.dumps({"profile": name, "cwd": os.path.realpath(os.getcwd()), "skip": "--dangerously-skip-permissions" in argv,
                         "settings": json.load(open(st)) if os.path.exists(st) else None, "bytes": len(prompt.encode())}) + "\n")
mode = cfg.get(name, "ok")
if mode == "exhausted":
    print("RESOURCE_EXHAUSTED quota reached. Resets in 2h", file=sys.stderr); sys.exit(3)
out = {"assignments": []}
m = re.search(r"<snippets>\n(.*?)\n</snippets>", prompt, re.S)
rows = [json.loads(l) for l in m.group(1).splitlines()] if m else []
if "Record ids: " in prompt:
    for rid in re.search(r"Record ids: (.*)\n", prompt).group(1).split(", "):
        out["assignments"].append({"record_id": rid, "external_effect": False, "effect_modules": [], "effect_rationale": "x",
                                   "matches": [{"snippet_id": r["id"], "confidence": 0.9, "relation_type": "API_IMPLEMENTATION",
                                                "rationale": "x"} for r in rows[:1]]})
else:
    for r in rows:
        out["assignments"].append({"snippet_id": r["id"], "external_effect": False, "effect_modules": [], "effect_rationale": "x",
                                   "matches": [{"record_id": c, "confidence": 0.9, "relation_type": "SEQUENCE_FLOW",
                                                "rationale": "x"} for c in r.get("cand", [])[:1]]})
print(json.dumps({"event": "step_update", "step_update": {"step_index": 0, "step_type": "agent_response"}}))
print(json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": out,
                  "usage": {"input_tokens": 1000, "output_tokens": 100, "cache_read_tokens": 0, "thinking_tokens": 0}}}))
'''


def make_bundle(root: Path) -> Path:
    def rec(rid, plat, mod, kind, text, mask):
        row = {"id": rid, "p": plat, "m": mod, "k": kind, "mask": f"0x{mask:X}", "text": text[:1200],
               "line": M.record_line(rid, kind, text), "doc": "", "pg": 0}
        row["h"] = M.record_hash(M.Record.from_row(dict(row, h="")))
        return row
    full = (1 << 28) - 1
    corpus = [rec("SWS_CM_00001", "ap", "CM", "api-function", "Definition of API function FindService for proxies.", full),
              rec("SWS_CM_00002", "ap", "CM", "requirement", "The skeleton shall offer the service instance.", full),
              rec("SWS_PduR_00001", "cp", "PduR", "requirement", "The PduR shall route I-PDUs to the lower layer.", full)]
    snips = [{"id": "SNIP_A", "p": "ap", "mod": "Com", "doc": "D", "page": 1, "refs": ["SWS_CM_00001"], "cited": ["SWS_CM_00001"],
              "text": f"FindService [SWS_CM_00001] finds proxies. {MARK}", "mask": f"0x{full:X}", "fig": False, "tab": False, "cap": ""},
             {"id": "SNIP_B", "p": "cp", "mod": "PduR", "doc": "E", "page": 2, "refs": [], "cited": [],
              "text": "The PduR routes I-PDUs to the lower layer.", "mask": f"0x{full:X}", "fig": False, "tab": False, "cap": ""}]
    figs = [{"schema": "figure-text@1", "figure_id": "FIG-cccccccccccccccc", "caption": "Figure 1: Offer", "doc": "AUTOSAR_AP_X",
             "page": 3, "releases": ["R25-11"], "labels": "Skeleton | OfferService", "description": "The skeleton offers.",
             "description_source": None}]
    elements = [{"id": r["id"], "p": r["p"], "m": r["m"], "k": r["k"], "mask": r["mask"], "frag": r["k"] != "requirement"}
                for r in corpus]
    records = [M.Record.from_row(r) for r in corpus]
    items = [M.Item.from_snippet_row(s) for s in snips]
    figures = [M.item_from_figure(f, "ap") for f in figs]
    inp = M.PlanInputs(records, items, figures, [r for r in records if r.kind != "requirement"])
    cands = M.compute_candidates(inp, 20)
    plan, stats = M.build_plan(inp, {}, set(), cands)
    files = {"corpus.jsonl": core.jsonl_lines(corpus), "elements.jsonl": core.jsonl_lines(elements),
             "snippets.jsonl": core.jsonl_lines(snips), "figure_texts.jsonl": core.jsonl_lines(figs),
             "assignment_matrix.jsonl": b"", "plan.jsonl": core.jsonl_lines(plan), "live_head.json": b"{}\n"}
    res = core.write_bundle(root / "bundle.tar.gz", files, {"created": "2026-10-09T00:00:00Z", "source_commit": "0" * 40,
                                                             "method": core.METHOD, "code": core.code_hashes(HERE),
                                                             "plan": stats})
    return Path(res["path"])


class LiveDistributeTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="live-wf-test-"))
        self.bundle = make_bundle(self.root)
        self.sha = core.file_sha256(self.bundle)
        self.cfg = self.root / "fake.json"
        self.log = self.root / "fake.log"
        self.cfg.write_text(json.dumps({"leo": "ok", "neo": "ok"}))
        bindir = self.root / "bin"
        bindir.mkdir()
        agy = bindir / "agy"
        agy.write_text(FAKE_AGY.replace("__PY__", sys.executable).replace("__CONFIG__", repr(str(self.cfg)))
                       .replace("__LOG__", repr(str(self.log))))
        agy.chmod(agy.stat().st_mode | stat.S_IXUSR)
        self.path = f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"
        profiles = []
        for n in ("leo", "neo"):
            cli = self.root / f"agy-profile-{n}" / ".gemini" / "antigravity-cli"
            cli.mkdir(parents=True)
            (cli / "antigravity-oauth-token").write_text("{}")
            profiles.append(str(cli.parents[1]))
        self.profiles = ",".join(profiles)
        self.bare = self.root / "live.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.bare)], check=True)
        self.clone = self.root / "clone"
        subprocess.run(["git", "clone", "-q", str(self.bare), str(self.clone)], check=True, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def job(self, *extra):
        env = dict(os.environ, PATH=self.path, AUTODOCS_AGY_PROFILES=self.profiles)
        cmd = [sys.executable, str(HERE / "live_distribute.py"), "run", "--bundle-file", str(self.bundle), "--bundle-sha256",
               self.sha, "--live-repo", str(self.clone), "--work", str(self.root / "work"), "--state",
               str(self.root / "agy-state.json"), "--concurrency", "2", "--run-id", "t1", *extra]
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=300)

    def test_run_commit_push_resume(self):
        r = self.job()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn(MARK, r.stdout + r.stderr)
        st = core.verify_chain(self.clone)
        self.assertTrue(st.ok, st.errors)
        dec = [e for e in st.entries if e["kind"] == "decision"]
        self.assertEqual(len(dec), 4)          # 2 Snippets, 1 Schaubild, 1 Fragment
        self.assertEqual([e["unit_kind"] for e in dec], ["snippet", "snippet", "figure", "element"])
        calls = [json.loads(l) for l in self.log.read_text().splitlines()]
        for c in calls:
            self.assertFalse(c["skip"])
            self.assertEqual(c["settings"]["permissions"]["allow"], [f"read_file({c['cwd']}/*)"])
        subprocess.run(["git", "-C", str(self.clone), "push", "-q", "origin", "HEAD:refs/heads/main"], check=True)
        r2 = self.job()
        self.assertEqual(r2.returncode, 0)
        self.assertIn("nichts zu tun", r2.stdout)
        fin = subprocess.run([sys.executable, str(HERE / "live_distribute.py"), "finalize", "--live-repo", str(self.clone)],
                             capture_output=True, text=True)
        self.assertEqual(fin.returncode, 0, fin.stdout + fin.stderr)

    def test_exhausted_exit_75(self):
        self.cfg.write_text(json.dumps({"leo": "exhausted", "neo": "exhausted"}))
        r = self.job()
        self.assertEqual(r.returncode, 75, r.stdout + r.stderr)
        state = json.loads((self.root / "agy-state.json").read_text())
        self.assertEqual(sorted(state), ["leo", "neo"])

    def test_switch_to_second_profile(self):
        self.cfg.write_text(json.dumps({"leo": "exhausted", "neo": "ok"}))
        r = self.job("--concurrency", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        dec = [e for e in core.verify_chain(self.clone).entries if e["kind"] == "decision"]
        self.assertEqual({e["profile"] for e in dec}, {"neo"})

    def test_vendored_copies_match_manifest(self):
        meta = json.loads((HERE / "live_vendor.json").read_text())
        for name, sha in meta["files"].items():
            self.assertEqual(core.file_sha256(HERE / name), sha, name)


if __name__ == "__main__":
    unittest.main()
