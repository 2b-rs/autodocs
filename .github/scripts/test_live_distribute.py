#!/usr/bin/env python3
"""Offline-Test des Live-Verteilungsjobs (live_distribute.py) mit falschem agy, echtem agy_switch.py und einem
lokalen Bare-Repo als autodocs-live. Kein Modellaufruf, keine Secrets, kein Netz.

    python3 .github/scripts/test_live_distribute.py
"""
from __future__ import annotations

import http.server
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import live_core as core  # noqa: E402
import live_distribute as LD  # noqa: E402
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
                         "settings": json.load(open(st)) if os.path.exists(st) else None, "bytes": len(prompt.encode()),
                         "token_in_env": "DASHBOARD_WRITE_TOKEN" in os.environ, "argv": argv}) + "\n")
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


class LiveJobCase(unittest.TestCase):
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

    def job(self, *extra, env_extra=None, timeout=120):
        env = dict(os.environ, PATH=self.path, AUTODOCS_AGY_PROFILES=self.profiles)
        env.pop("DASHBOARD_WRITE_TOKEN", None)
        if env_extra:
            env.update(env_extra)
        cmd = [sys.executable, str(HERE / "live_distribute.py"), "run", "--bundle-file", str(self.bundle), "--bundle-sha256",
               self.sha, "--live-repo", str(self.clone), "--work", str(self.root / "work"), "--state",
               str(self.root / "agy-state.json"), "--concurrency", "2", "--run-id", "t1", *extra]
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)


class LiveDistributeTest(LiveJobCase):
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


TOKEN = "dashboard-write-token-test-9f3a1c"


class FakeLiveWorker:
    """In-process PUT receiver. Does not contact the real Worker (NOT_RUN)."""

    def __init__(self, token=TOKEN, fail_times=0, fail_status=503, echo_token=False):
        self.token = token
        self.fail_times = fail_times
        self.fail_status = fail_status
        self.echo_token = echo_token
        self.requests = []
        self._lock = threading.Lock()
        parent = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, _fmt, *_args):
                return

            def do_PUT(self):
                self._record("PUT")

            def do_GET(self):
                self._record("GET")

            def do_POST(self):
                self._record("POST")

            def _record(self, method):
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw.decode("utf-8")) if raw else None
                except ValueError:
                    body = raw.decode("utf-8", errors="replace")
                with parent._lock:
                    n_fail = parent.fail_times
                    if n_fail > 0:
                        parent.fail_times -= 1
                    parent.requests.append({"method": method, "path": self.path,
                                            "headers": {k: v for k, v in self.headers.items()},
                                            "body": body})
                if n_fail > 0:
                    payload = json.dumps({"error": {"code": "downstream",
                                                    "echo": parent.token if parent.echo_token else "x"}})
                    self.send_response(parent.fail_status)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload.encode("utf-8"))
                    return
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')

        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/dashboard/live-worker.json"
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def _serve(self):
        self._ready.set()
        self.httpd.serve_forever()

    def start(self):
        self._thread.start()
        self._ready.wait(2)

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self._thread.join(timeout=2)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_exc):
        self.stop()


def _scheduled_run(completed, hour, *, stop="budget-time", failed_batches=2, key="cfg"):
    return {
        "config_key": key, "stop": stop, "failed_batches": failed_batches,
        "trigger": {"kind": "scheduled", "provenance": "dispatcher-declared",
                    "scheduled_at": f"2026-10-17T{hour:02d}:00:00Z"},
        "completed_by_kind": {"snippet": completed},
        "elapsed_seconds_by_kind": {"snippet": 2400.0},
    }


class PerformanceEtaTest(unittest.TestCase):
    SNIPPET_OPEN = {"snippet": {"planned": 34030, "done": 0},
                    "figure": {"planned": 0, "done": 0},
                    "element": {"planned": 0, "done": 0}}
    CONFIG = {"key": "cfg", "kinds": ["snippet", "figure", "element"]}

    def test_n1_emits_provisional_estimate(self):
        perf = LD._performance([_scheduled_run(480, 15)], self.SNIPPET_OPEN, self.CONFIG)
        scheduled = perf["scheduled"]
        self.assertEqual("provisional", scheduled["confidence"])
        self.assertEqual(1, scheduled["sample_count"])
        self.assertEqual(255225.0, scheduled["eta_seconds"])
        self.assertEqual([255225.0, 255225.0], scheduled["range_seconds"])
        self.assertEqual("provisional", perf["by_kind"]["snippet"]["scheduled"]["confidence"])

    def test_n2_real_samples_calendar_oracle(self):
        # 480 and 576 decisions/hour, remaining 34030 → 59–71h range, ~64.5h center.
        perf = LD._performance([_scheduled_run(480, 15), _scheduled_run(576, 16)], self.SNIPPET_OPEN, self.CONFIG)
        scheduled = perf["scheduled"]
        self.assertEqual("provisional", scheduled["confidence"])
        self.assertEqual(2, scheduled["sample_count"])
        self.assertEqual(232022.7, scheduled["eta_seconds"])
        self.assertEqual([212687.5, 255225.0], scheduled["range_seconds"])
        self.assertEqual(528.0, perf["by_kind"]["snippet"]["scheduled"]["yield_per_hour"])
        self.assertAlmostEqual(scheduled["eta_seconds"] / 3600.0, 64.5, places=1)
        self.assertAlmostEqual(scheduled["range_seconds"][0] / 3600.0, 59.08, places=1)
        self.assertAlmostEqual(scheduled["range_seconds"][1] / 3600.0, 70.9, places=1)

    def test_n3_emits_stable_estimate(self):
        runs = [_scheduled_run(480, 15), _scheduled_run(528, 16), _scheduled_run(576, 17)]
        perf = LD._performance(runs, self.SNIPPET_OPEN, self.CONFIG)
        self.assertEqual("stable", perf["scheduled"]["confidence"])
        self.assertEqual(3, perf["scheduled"]["sample_count"])
        self.assertEqual(232022.7, perf["scheduled"]["eta_seconds"])
        self.assertEqual("stable", perf["by_kind"]["snippet"]["scheduled"]["confidence"])

    def test_budget_time_with_failed_or_timeout_batches_still_counts(self):
        included = LD._performance([_scheduled_run(480, 15, failed_batches=4)], self.SNIPPET_OPEN, self.CONFIG)
        self.assertEqual(1, included["scheduled"]["sample_count"])
        self.assertIsNotNone(included["scheduled"]["eta_seconds"])
        self.assertEqual(1, included["by_kind"]["snippet"]["active"]["sample_count"])

    def test_excludes_errors_exhausted_needs_login_malformed_and_wrong_config(self):
        bad = [
            _scheduled_run(480, 15, stop="errors", failed_batches=0),
            _scheduled_run(480, 16, stop="exhausted", failed_batches=0),
            _scheduled_run(480, 17, stop="needs-login", failed_batches=0),
            {**_scheduled_run(480, 18), "config_key": "other"},
            {**_scheduled_run(480, 19), "failed_batches": True},
            {**_scheduled_run(480, 20), "completed_by_kind": {"snippet": True, "figure": 0, "element": 0}},
        ]
        perf = LD._performance(bad, self.SNIPPET_OPEN, self.CONFIG)
        self.assertEqual(0, perf["scheduled"]["sample_count"])
        self.assertIsNone(perf["scheduled"]["eta_seconds"])
        self.assertIsNone(perf["scheduled"]["confidence"])

    def test_does_not_invent_total_eta_when_a_remaining_kind_lacks_samples(self):
        plan = {"snippet": {"planned": 34030, "done": 0},
                "figure": {"planned": 10, "done": 0},
                "element": {"planned": 0, "done": 0}}
        perf = LD._performance([_scheduled_run(480, 15), _scheduled_run(576, 16)], plan, self.CONFIG)
        self.assertIsNotNone(perf["by_kind"]["snippet"]["scheduled"]["eta_seconds"])
        self.assertIsNone(perf["by_kind"]["figure"]["scheduled"]["eta_seconds"])
        self.assertIsNone(perf["scheduled"]["eta_seconds"])
        self.assertIsNone(perf["scheduled"]["confidence"])


class LiveWorkerTelemetryTest(LiveJobCase):
    """Public client for PUT /dashboard/live-worker.json.

    Real Worker/DO persistence and the public dashboard GET overlay: NOT_RUN.
    Those are owned by the existing WSS source candidate, not this repository.
    """

    def telemetry_env(self, receiver, **extra):
        env = {
            "DASHBOARD_WRITE_TOKEN": receiver.token,
            "DASHBOARD_LIVE_WORKER_URL": receiver.url,
            "AUTODOCS_LIVE_WORKER_STATE": str(self.root / "live-worker-state.json"),
            "GITHUB_RUN_ID": "555001",
            "GITHUB_RUN_ATTEMPT": "2",
        }
        env.update(extra)
        return env

    def test_start_progress_terminal_order_and_fragment_shape(self):
        with FakeLiveWorker() as receiver:
            env = self.telemetry_env(receiver)
            with mock.patch.dict(os.environ, env, clear=False):
                self.assertEqual(0, LD.main(["dashboard", "--event", "start"]))
            r = self.job(env_extra=env)
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            with mock.patch.dict(os.environ, env, clear=False):
                self.assertEqual(0, LD.main(["dashboard", "--event", "terminal"]))
        events = [req["body"]["event"] for req in receiver.requests]
        self.assertGreaterEqual(len(events), 3)
        self.assertEqual("start", events[0])
        self.assertIn("progress", events)
        self.assertEqual(1, events.count("terminal"))
        self.assertEqual("terminal", events[-1])
        seqs = [req["body"]["seq"] for req in receiver.requests]
        self.assertEqual(seqs, sorted(seqs))
        self.assertEqual(seqs, list(range(1, len(seqs) + 1)))
        for req in receiver.requests:
            self.assertEqual("PUT", req["method"])
            self.assertEqual("/dashboard/live-worker.json", req["path"])
            self.assertEqual(f"Bearer {TOKEN}", req["headers"].get("Authorization"))
            body = req["body"]
            self.assertEqual(LD.LIVE_WORKER_SCHEMA, body["schema"])
            self.assertEqual({"run_id": "555001", "run_attempt": 2, "unknown": []}, body["github"])
            self.assertIn(body["event"], ("start", "progress", "terminal"))
            self.assertIn("phase", body)
            self.assertIn("state", body)
            self.assertIn("timestamp", body)
            self.assertIsInstance(body["interval"]["started"], str)
            unknown = body["progress"]["unknown"]
            if body["progress"]["done"] is None:
                self.assertIn("done", unknown)
            else:
                self.assertNotIn("done", unknown)
                self.assertIsInstance(body["progress"]["done"], int)
            if body["progress"]["total"] is None:
                self.assertIn("total", unknown)
            else:
                self.assertNotIn("total", unknown)
                self.assertIsInstance(body["progress"]["total"], int)
            if body["event"] == "start":
                self.assertEqual(["done", "total"], body["progress"]["unknown"])
                self.assertIsNone(body["interval"]["ended"])
            if body["event"] == "terminal":
                self.assertIsNotNone(body["interval"]["ended"])
                self.assertIsNotNone(body["outcome"])
                self.assertIsNotNone(body["reason"])
                self.assertNotIn(TOKEN, json.dumps(body))
            self.assertNotIn("/dashboard.json", req["path"])
        start = receiver.requests[0]["body"]
        self.assertEqual(["done", "total"], start["progress"]["unknown"])
        progress = next(req["body"] for req in receiver.requests if req["body"]["event"] == "progress")
        self.assertIsInstance(progress["progress"]["done"], int)
        self.assertIsInstance(progress["progress"]["total"], int)
        self.assertGreaterEqual(progress["progress"]["total"], progress["progress"]["done"])
        self.assertEqual([], progress["progress"]["unknown"])
        self.assertIn("completed", progress["counters"])

    def test_retry_resends_same_seq(self):
        with FakeLiveWorker(fail_times=2) as receiver:
            env = self.telemetry_env(receiver)
            with mock.patch.dict(os.environ, env, clear=False):
                self.assertEqual(0, LD.main(["dashboard", "--event", "start"]))
        self.assertEqual(3, len(receiver.requests))
        seqs = [req["body"]["seq"] for req in receiver.requests]
        self.assertEqual([1, 1, 1], seqs)
        self.assertEqual(receiver.requests[0]["body"], receiver.requests[1]["body"])
        self.assertEqual(receiver.requests[1]["body"], receiver.requests[2]["body"])

    def test_receiver_failure_does_not_suppress_distribution(self):
        with FakeLiveWorker(fail_times=99, echo_token=True) as receiver:
            env = self.telemetry_env(receiver)
            r = self.job(env_extra=env)
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            combined = r.stdout + r.stderr
            self.assertIn("telemetry warning", combined)
            self.assertNotIn(TOKEN, combined)
        st = core.verify_chain(self.clone)
        self.assertTrue(st.ok, st.errors)
        self.assertGreaterEqual(len([e for e in st.entries if e["kind"] == "decision"]), 4)

    def test_token_not_in_agy_argv_env_or_logs(self):
        with FakeLiveWorker() as receiver:
            env = self.telemetry_env(receiver)
            r = self.job(env_extra=env)
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            combined = r.stdout + r.stderr
            self.assertNotIn(TOKEN, combined)
            self.assertNotIn(TOKEN, " ".join(map(str, r.args)))
            log_text = self.log.read_text()
            self.assertNotIn(TOKEN, log_text)
            for line in log_text.splitlines():
                row = json.loads(line)
                self.assertFalse(row["token_in_env"])
                self.assertNotIn(TOKEN, json.dumps(row["argv"]))
            self.assertNotIn(TOKEN, str(LD._scrubbed_env(env)))
            self.assertNotIn("DASHBOARD_WRITE_TOKEN", LD._scrubbed_env(env))
            with mock.patch.dict(os.environ, env, clear=False):
                git_env = LD._git_env()
            self.assertNotIn("DASHBOARD_WRITE_TOKEN", git_env)
            self.assertNotIn(TOKEN, git_env.values())
            for req in receiver.requests:
                self.assertEqual(f"Bearer {TOKEN}", req["headers"].get("Authorization"))
                self.assertNotIn(TOKEN, json.dumps(req["body"]))

    def test_refuses_canonical_dashboard_json_path(self):
        with FakeLiveWorker() as receiver:
            env = self.telemetry_env(receiver)
            env["DASHBOARD_LIVE_WORKER_URL"] = f"http://127.0.0.1:{receiver.port}/dashboard.json"
            with mock.patch.dict(os.environ, env, clear=False):
                self.assertEqual(0, LD.main(["dashboard", "--event", "start"]))
            self.assertEqual([], receiver.requests)


if __name__ == "__main__":
    unittest.main()
