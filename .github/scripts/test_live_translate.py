#!/usr/bin/env python3
"""Offline-Test des Live-Übersetzungsjobs (live_translate.py) mit falschem agy, echtem agy_switch.py und einem lokalen
Bare-Repo als autodocs-live. Kein Modellaufruf, keine Secrets, kein Netz.

    python3 .github/scripts/test_live_translate.py
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import live_translate_core as C  # noqa: E402

MARK = "ZEBRAQUAGGA"
GUIDE = ('<div class="ai module-guide">\n<h4>Rolle im Überblick</h4>\n<p>Der Proxy der Adaptive Platform findet Dienste '
         'über <code>FindService</code> (<a class="spec-record-ref" data-req="SWS_CM_00001">[SWS_CM_00001]</a>) '
         '<span class="docref" data-doc="AUTOSAR_AP_SWS_CommunicationManagement" data-page="12">SWS CM S. 12</span>.</p>\n'
         '<div class="diagram" id="diag-a"><svg viewbox="0 0 9 9"><text>Nutzer</text></svg></div>\n'
         '<p class="diagram-note">Kontextdiagramm der Suche nach Diensten über die Service Discovery.</p>\n'
         f'<p class="ai-note">Dieser Leitfaden wurde automatisiert erstellt. {MARK}</p>\n</div>\n')
ELEMENT = ('<div class="ai usage">\n<p>Die Funktion <code>{fn}</code> liefert <code>Std_ReturnType</code> zurück.</p>\n'
           '<h4>Aufruf und Semantik</h4>\n<p class="ai-note">Dieser Nutzungshinweis wurde automatisiert generiert.</p>\n</div>\n')
FRAGS = {"modules/com/anchor_r25_11.html": GUIDE,
         "classic/elements/SWS_Adc_00001/anchor_r20_11.html": ELEMENT.format(fn="Adc_Init"),
         "classic/elements/SWS_Adc_00002/anchor_r20_11.html": ELEMENT.format(fn="Adc_DeInit")}

FAKE_AGY = r'''#!__PY__
import json, os, re, sys
cfg = json.load(open(__CONFIG__))
argv = sys.argv[1:]
home = os.environ.get("HOME", "")
name = os.path.basename(home.rstrip("/")).replace("agy-profile-", "")
prompt = argv[argv.index("-p") + 1]
st = os.path.join(home, ".gemini", "antigravity-cli", "settings.json")
rows = [json.loads(l) for l in re.search(r"<segments>\n(.*?)\n</segments>", prompt, re.S).group(1).splitlines()]
lang = re.search(r"documentation about AUTOSAR .*? into (.*?)\.\n", prompt, re.S).group(1)
with open(__LOG__, "a") as fh:
    fh.write(json.dumps({"profile": name, "model": argv[argv.index("--model") + 1], "effort": "--effort" in argv,
                         "skip": "--dangerously-skip-permissions" in argv, "cwd": os.path.realpath(os.getcwd()),
                         "settings": json.load(open(st)) if os.path.exists(st) else None, "lang": lang,
                         "de": [r["de"] for r in rows]}) + "\n")
if cfg.get(name) == "exhausted":
    print("RESOURCE_EXHAUSTED quota reached. Resets in 2h", file=sys.stderr); sys.exit(3)
line = re.search(r"Protected terms \(keep exactly\): (.*)\n", prompt).group(1)
prot = [] if line.startswith("(none") else line.split(", ")
word = "文字" if lang.startswith("Simplified Chinese") else ("글자" if lang.startswith("Korean") else "lorem")
def keep(t):
    return bool(re.search(r"[_:0-9]|\w\.\w", t) or re.search(r"[a-z][A-Z]", t) or (t.isupper() and len(t) > 1))
def tr(de):
    out = []
    for p in re.split(r"(<(?:code|a|span)\b[^>]*>.*?</(?:code|a|span)>|<[^>]+>|⟦\d+⟧|&[a-z]+;)", de):
        if not p or p[0] in "<⟦&":
            out.append(p); continue
        masked = {}
        for i, t in enumerate(sorted(prot, key=len, reverse=True)):
            if t in p:
                masked["\x01%d\x02" % i] = t
                p = re.sub(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", "\x01%d\x02" % i, p)
        p = re.sub(r"[\w:.\-/]*\w", lambda m: m.group(0) if "\x01" in m.group(0) or re.search(r"[_:]|\w\.\w", m.group(0)) else re.sub(r"[^-/]+", lambda q: q.group(0) if keep(q.group(0)) else re.sub(r"[^\W\d_]+", word, q.group(0)), m.group(0)), p)
        for k, t in masked.items():
            p = p.replace(k, t)
        out.append(p)
    return "".join(out)
res = {"translations": [{"id": r["id"], "t": tr(r["de"])} for r in rows]}
print(json.dumps({"event": "step_update", "step_update": {"step_index": 0, "step_type": "agent_response"}}))
print(json.dumps({"event": "result", "result": {"status": "SUCCESS", "structured_output": res,
                  "usage": {"input_tokens": 16000 + len(prompt) // 4, "output_tokens": 400, "cache_read_tokens": 0, "thinking_tokens": 0}}}))
'''


def make_bundle(root: Path) -> Path:
    frags = []
    rows = []
    for path, html in FRAGS.items():
        sha = C.sha256_hex(html.encode())
        r = {"path": path, "html": html, "sha256": sha, "tier": C.fragment_tier(path), "release": C.fragment_release(path),
             "trace_output": sha, "proxy": 1, "channel": "fragment"}
        rows.append(r)
        frags.append(C.Fragment.from_row(r))
    terms = C.Terms.from_json({"protected": ["Adaptive Platform", "Service Discovery"],
                               "docref": {"en": {"zitat_a": "“", "zitat_z": "”"}}})
    plan, stats = C.build_plan(frags, terms)
    files = {"fragments.jsonl": C.jsonl_lines(rows), "tm.jsonl": b"",
             "terms.json": (json.dumps(terms.to_json(), sort_keys=True) + "\n").encode(),
             "plan.jsonl": C.jsonl_lines(plan), "live_head.json": b"{}\n"}
    res = C.write_bundle(root / "bundle.tar.gz", files, {"created": "2026-10-09T00:00:00Z", "source_commit": "0" * 40,
                                                          "recipe": {"id": C.RECIPE_ID, "hash": C.RECIPE_HASH},
                                                          "code": C.code_hashes(HERE), "plan": stats})
    return Path(res["path"])


class LiveTranslateTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="live-tr-wf-"))
        self.bundle = make_bundle(self.root)
        self.cfg, self.log = self.root / "fake.json", self.root / "fake.log"
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
        self.state = self.root / "agy-state.json"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def calls(self):
        return [json.loads(l) for l in self.log.read_text().splitlines()] if self.log.exists() else []

    def job(self, *extra, cmd="run"):
        env = dict(os.environ, PATH=self.path, AUTODOCS_AGY_PROFILES=self.profiles)
        args = [sys.executable, str(HERE / "live_translate.py"), cmd, "--bundle-file", str(self.bundle), "--bundle-sha256",
                C.file_sha256(self.bundle), "--live-repo", str(self.clone), "--work", str(self.root / "work")]
        if cmd == "run":
            args += ["--state", str(self.state), "--concurrency", "3", "--run-id", "t1", "--max-output-tokens", "300"]
        return subprocess.run(args + list(extra), capture_output=True, text=True, env=env, timeout=300)

    def test_run_commit_push_resume(self):
        r = self.job()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn(MARK, r.stdout + r.stderr)
        st = C.verify_chain(self.clone)
        self.assertTrue(st.ok, st.errors)
        tr = [e for e in st.entries if e["kind"] == "translation"]
        self.assertEqual(len(tr), len(FRAGS) * 10)
        calls = self.calls()
        for c in calls:
            self.assertFalse(c["skip"])
            self.assertFalse(c["effort"])
            self.assertEqual(c["settings"]["permissions"]["allow"], [f"read_file({c['cwd']}/*)"])
        self.assertEqual({c["model"] for c in calls}, {"gemini-3.8-flash-low"})
        seen = [(c["lang"], d) for c in calls for d in c["de"]]
        self.assertEqual(len(seen), len(set(seen)))                  # Übersetzungsspeicher: jedes Segment einmal
        run = [e for e in st.entries if e["kind"] == "run"][-1]
        self.assertGreater(run["list_price_usd"], 0)
        self.assertEqual(set(run["models_usage"]), {"gemini-3.8-flash-low"})
        self.assertEqual(run["price_basis"], C.PRICE_BASIS)
        summary = subprocess.run(
            [sys.executable, str(HERE / "live_translate.py"), "summary", "--live-repo", str(self.clone)],
            capture_output=True, text=True)
        self.assertIn("Live-Übersetzung", summary.stdout)
        self.assertNotIn(MARK, summary.stdout)
        subprocess.run(["git", "-C", str(self.clone), "push", "-q", "origin", "HEAD:refs/heads/main"], check=True)
        r2 = self.job()
        self.assertEqual(r2.returncode, 0)
        self.assertIn("nichts zu tun", r2.stdout)
        fin = subprocess.run([sys.executable, str(HERE / "live_translate.py"), "finalize", "--live-repo", str(self.clone)],
                             capture_output=True, text=True)
        self.assertEqual(fin.returncode, 0, fin.stdout + fin.stderr)

    def test_exhaustion(self):
        self.state.write_text(json.dumps({n: {"cooldown_until": time.time() + 3600} for n in ("leo", "neo")}))
        r = self.job()
        self.assertEqual(r.returncode, 75, r.stdout + r.stderr)
        self.assertEqual(self.calls(), [])
        self.state.unlink()
        self.cfg.write_text(json.dumps({"leo": "exhausted", "neo": "exhausted"}))
        r = self.job()
        self.assertEqual(r.returncode, 75, r.stdout + r.stderr)
        self.assertEqual(sorted(json.loads(self.state.read_text())), ["leo", "neo"])

    def test_switch_and_dry_run(self):
        r = self.job("--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Trockenlauf", r.stdout)
        self.assertEqual(self.calls(), [])
        self.cfg.write_text(json.dumps({"leo": "exhausted", "neo": "ok"}))
        r = self.job("--concurrency", "1", "--langs", "en")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tms = [e for e in C.verify_chain(self.clone).entries if e["kind"] == "tm"]
        self.assertEqual({e["profile"] for e in tms}, {"neo"})

    def test_vendored_copies_match_manifest(self):
        meta = json.loads((HERE / "live_translate_vendor.json").read_text())
        for name, sha in list(meta["files"].items()) + list(meta["shared"].items()):
            self.assertEqual(C.file_sha256(HERE / name), sha, name)


if __name__ == "__main__":
    unittest.main()
