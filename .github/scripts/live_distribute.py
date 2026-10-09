#!/usr/bin/env python3
"""Online-Job der Live-Verteilung (CONCEPT-0060 §6.7, CONCEPT-0061): Snippets, Schaubild-Reihen und Elemente
(Fragmente) inkrementell zuordnen und jede Entscheidung als Kettenglied in ``autodocs-live`` festhalten.

Läuft im Workflow ``live-distribution.yml`` des öffentlichen Website-Repos (Kopie aus ``_src/tools`` des
Quell-Repos, siehe ``live_bundle.py vendor``) und lokal in den Tests.

    live_distribute.py pending --bundle-url URL --bundle-sha256 SHA --live-repo DIR
    live_distribute.py run --bundle-url URL --bundle-sha256 SHA --live-repo DIR [Budget]
    live_distribute.py finalize --live-repo DIR [--commit]
    live_distribute.py verify --live-repo DIR [--bundle-file F]
    live_distribute.py status --live-repo DIR

Ablauf von ``run``: Bündel laden und prüfen (SHA-256, Manifest, Code-Hashes), Kette prüfen, offene Einheiten des
Plans bestimmen (Schlüssel nicht im Protokoll), Batches bilden (Snippets, dann Schaubilder, dann Elemente; Größe
und Prompt-Bytes begrenzt), je Batch agy über ``agy_switch.py`` aufrufen (gesperrt: eigenes HOME je Arbeitsplatz,
settings.json erlaubt nur Lesen im leeren Aufrufverzeichnis, jeder Befehl verboten, nie
``--dangerously-skip-permissions``), Antworten prüfen, Entscheidungen anhängen, danach die Prüfregeln (Patrouille
Stufe 1) über die neuen Entscheidungen, Laufglied, Zeiger, Statusdatei, lokaler Commit. Gepusht wird in einem
eigenen Workflow-Schritt mit dem Deploy-Key; dieser Prozess sieht keinen Schlüssel.

Das Log nennt nur Zahlen, Kosten zu API-Listenpreisen und die Profilnamen (leo, neo); nie Prompts oder Antworten.

Exit: 0 fertig oder Budget erreicht oder nichts zu tun, 75 alle Profile erschöpft, 77 kein Profil angemeldet,
65 Kette oder Bündel ungültig, 78 Konfiguration (Code-Stand, fehlende Eingaben), 1 sonstige Fehler.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import live_core as core  # noqa: E402
import live_method as M  # noqa: E402

EXIT_OK, EXIT_ERROR, EXIT_DATA, EXIT_EXHAUSTED, EXIT_LOGIN, EXIT_CONFIG = 0, 1, 65, 75, 77, 78
# Was in einem agy-HOME bleiben darf (wie abo_relay.mjs); Verläufe, Transkripte und Logs werden nach jedem Aufruf gelöscht.
KEEP_HOME = (".gemini",)
KEEP_GEMINI = ("antigravity-cli",)
KEEP_CLI = ("antigravity-oauth-token", "installation_id", "settings.json", "bin", "builtin", "updater",
            "last_check.timestamp")
# Einheiten je Aufruf (K des vermessenen Laufs); die Byte-Grenze teilt größere Batches. agy bringt je Aufruf rund
# 16.000 Tokens Grundlast mit (Fit über die Aufrufe des Laufs vom 9. Oktober), volle Batches sind deshalb billiger.
BATCH = {"snippet": 20, "figure": 20, "element": 12}
# Linux begrenzt ein einzelnes Argument auf 128 KiB (agy -p); bis 100.000 Bytes bleibt ein Aufruf auch unter der
# Schwelle von ~47.000 Tokens, ab der agy in Agentenschleifen fiel.
MAX_PROMPT_BYTES = 100_000


def log(msg: str) -> None:
    print("live: " + msg, flush=True)


# ==============================================================================
# Daten des Bündels
# ==============================================================================

class Data:
    """Korpus, Einheiten und Universum aus einem geöffneten Bündel."""

    def __init__(self, bundle: core.Bundle):
        self.bundle = bundle
        self.records: Dict[str, M.Record] = {}
        for r in bundle.rows("corpus.jsonl"):
            rec = M.Record.from_row(r)
            self.records[rec.id] = rec
        self.snippets: Dict[str, M.Item] = {}
        for r in bundle.rows("snippets.jsonl"):
            it = M.Item.from_snippet_row(r)
            self.snippets[it.id] = it
        self.figure_rows: Dict[str, Dict[str, Any]] = {r["figure_id"]: r for r in bundle.rows("figure_texts.jsonl")}
        self.elements = {r["id"]: r for r in bundle.rows("elements.jsonl")}
        self.module_index = M.module_index(self.records.values())
        self._figures: Dict[str, M.Item] = {}
        self._mod_idx: Dict[str, M.LexicalIndex] = {}
        self._lock = threading.Lock()

    def item(self, ref: str, platform: Optional[str] = None) -> Optional[M.Item]:
        if ref in self.snippets:
            return self.snippets[ref]
        with self._lock:
            if ref not in self._figures and ref in self.figure_rows:
                self._figures[ref] = M.item_from_figure(self.figure_rows[ref], platform)
            return self._figures.get(ref)

    def module_candidates(self, modules: List[str], text: str, exclude: Set[str], k: int) -> List[str]:
        out: List[str] = []
        for m in modules:
            with self._lock:
                idx = self._mod_idx.get(m)
                if idx is None:
                    idx = self._mod_idx[m] = M.record_index([r for r in self.records.values() if r.module == m])
            added = 0
            for rid, _ in idx.search(text, k + len(exclude)):
                if added >= k:
                    break
                if rid not in exclude and rid not in out:
                    out.append(rid)
                    added += 1
        return out

    def universe(self, matrix_strong: Dict[Tuple[str, str], str]) -> core.Universe:
        items = {sid: {"mask": it.mask, "mod": it.module} for sid, it in self.snippets.items()}
        for fid, row in self.figure_rows.items():
            rels = row.get("releases") or []
            items[fid] = {"mask": M.release_mask(rels) if rels else M.ALL_MASK, "mod": "figure"}
        els = {eid: {"m": e.get("m"), "k": e.get("k"), "mask": int(e.get("mask", "0x0"), 16)} for eid, e in self.elements.items()}
        return core.Universe(els, items, M.ALL_MASK, matrix_strong)


def strong_matrix_rows(bundle: core.Bundle, snippet_ids: Set[str]) -> Dict[Tuple[str, str], str]:
    out: Dict[Tuple[str, str], str] = {}
    for r in bundle.rows("assignment_matrix.jsonl"):
        sid = r.get("snippet_id")
        if sid in snippet_ids and float(r.get("confidence") or 0) >= 0.95 and r.get("target_element"):
            out[(r["target_element"], sid)] = str(r.get("relation_type") or r.get("role") or "constitutive")
    return out


# ==============================================================================
# agy über agy_switch.py, Arbeitsplätze mit eigener Sperre
# ==============================================================================

def _prune(d: Path, keep: Tuple[str, ...]) -> None:
    if not d.is_dir():
        return
    for p in d.iterdir():
        if p.name in keep:
            continue
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p, ignore_errors=True)
        else:
            try:
                p.unlink()
            except OSError:
                pass


def lockdown_settings(call_dir: Path) -> str:
    return json.dumps({"permissions": {"allow": [f"read_file({os.path.realpath(call_dir)}/*)"],
                                       "deny": ["command(*)", "command(regex:.*)"]}})


class Slot:
    """Arbeitsplatz eines Threads: je Profil eine Kopie des HOME (nur Token, Installations-ID, Programmteile) mit
    eigener settings.json, die nur das Lesen im leeren Aufrufverzeichnis erlaubt. Der Verzeichnisname bleibt
    ``agy-profile-<name>``, damit agy_switch.py den Sperrzustand unter leo/neo führt."""

    def __init__(self, idx: int, base_profiles: List[str], root: Path):
        self.idx = idx
        self.dir = root / f"w{idx}"
        self.call_dir = self.dir / "call"
        self.call_dir.mkdir(parents=True, exist_ok=True)
        self.call_dir = Path(os.path.realpath(self.call_dir))
        self.homes: List[Path] = []
        old = os.umask(0o077)
        try:
            for base in base_profiles:
                src = Path(base) / ".gemini" / "antigravity-cli"
                home = self.dir / Path(base.rstrip("/")).name
                cli = home / ".gemini" / "antigravity-cli"
                cli.mkdir(parents=True, exist_ok=True)
                for f in ("antigravity-oauth-token", "installation_id"):
                    if (src / f).is_file():
                        shutil.copyfile(src / f, cli / f)
                (cli / "settings.json").write_text(lockdown_settings(self.call_dir), encoding="utf-8")
                self.homes.append(home)
        finally:
            os.umask(old)

    @property
    def profiles(self) -> str:
        return ",".join(str(h) for h in self.homes)

    def scrub(self) -> None:
        for home in self.homes:
            _prune(home, KEEP_HOME)
            _prune(home / ".gemini", KEEP_GEMINI)
            _prune(home / ".gemini" / "antigravity-cli", KEEP_CLI)
        _prune(self.call_dir, ())

    def lock(self) -> bool:
        """Sperre vor jedem Aufruf neu schreiben (agy könnte die Datei selbst ändern) und das Aufrufverzeichnis
        leeren. False, wenn das nicht gelingt: dann kein Aufruf."""
        expect = lockdown_settings(self.call_dir)
        try:
            _prune(self.call_dir, ())
            for home in self.homes:
                p = home / ".gemini" / "antigravity-cli" / "settings.json"
                core.write_atomic(p, expect.encode("utf-8"))
                os.chmod(p, 0o600)
                if p.read_text(encoding="utf-8") != expect:
                    return False
        except OSError:
            return False
        return not any(self.call_dir.iterdir())


@dataclass
class CallResult:
    outcome: str                       # ok | exhausted | login | error | contaminated | empty | timeout
    structured: Optional[Dict[str, Any]] = None
    tokens: Dict[str, int] = field(default_factory=lambda: {"input": 0, "cached": 0, "output": 0, "thinking": 0})
    profile: str = ""
    rc: int = 0
    wall_s: float = 0.0
    steps: int = 0


_GROUPS: Set[int] = set()


def _terminate(signum, _frame) -> None:
    """Abbruch des Laufs (Workflow-Abbruch, Strg-C): laufende agy-Gruppen mit beenden."""
    for pg in list(_GROUPS):
        try:
            os.killpg(pg, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    os._exit(128 + signum)


def _run_group(cmd: List[str], timeout: float, env: Dict[str, str], cwd: str) -> Tuple[int, str, str, bool]:
    """Prozess in eigener Gruppe; bei Zeitüberschreitung wird die ganze Gruppe (auch agy) beendet."""
    with tempfile.TemporaryFile("w+", encoding="utf-8") as out, tempfile.TemporaryFile("w+", encoding="utf-8") as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err, env=env, cwd=cwd,
                                start_new_session=True, text=True)
        _GROUPS.add(proc.pid)
        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            _GROUPS.discard(proc.pid)
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            if proc.poll() is None:
                proc.wait(timeout=10)
        out.seek(0)
        err.seek(0)
        return proc.returncode if not timed_out else 124, out.read(), err.read(), timed_out


class Agy:
    def __init__(self, switch: Path, state: Path, model: str, effort: str, timeout_s: int, python: str):
        self.switch, self.state, self.model, self.effort = switch, state, model, effort
        self.timeout_s, self.python = timeout_s, python

    def env(self, slot: Slot) -> Dict[str, str]:
        src = os.environ
        env = {"PATH": src.get("PATH", "/usr/bin:/bin"), "LANG": src.get("LANG", "C.UTF-8"),
               "AUTODOCS_AGY_PROFILES": slot.profiles, "AGY_STATE": str(self.state)}
        for k in ("RUNNER_TEMP", "TMPDIR", "TZ"):
            if src.get(k):
                env[k] = src[k]
        return env

    def call(self, slot: Slot, prompt: str, schema: Dict[str, Any]) -> CallResult:
        if not slot.lock():
            return CallResult("error", rc=EXIT_CONFIG)
        cmd = [self.python, str(self.switch), "--state", str(self.state), "--",
               "-p", prompt, "--model", self.model, "--effort", self.effort, "--output-format", "stream-json",
               "--json-schema", json.dumps(schema, separators=(",", ":")), "--disable-slash-commands",
               "--print-timeout", f"{self.timeout_s}s"]
        t0 = time.monotonic()
        try:
            rc, out, err, timed_out = _run_group(cmd, self.timeout_s + 60, self.env(slot), str(slot.call_dir))
        except OSError:                        # z. B. E2BIG: Prompt zu lang für ein Argument
            return CallResult("error", rc=EXIT_ERROR, wall_s=time.monotonic() - t0)
        finally:
            slot.scrub()
        wall = time.monotonic() - t0
        sw: Dict[str, Any] = {}
        for line in err.splitlines():
            if line.startswith("agy-switch: "):
                try:
                    sw = json.loads(line[len("agy-switch: "):])
                except ValueError:
                    sw = {}
        profile = str(sw.get("profile") or "")
        if timed_out:
            return CallResult("timeout", profile=profile, rc=rc, wall_s=wall)
        if rc == EXIT_EXHAUSTED:
            return CallResult("exhausted", profile=profile, rc=rc, wall_s=wall)
        if rc == EXIT_LOGIN:
            return CallResult("login", profile=profile, rc=rc, wall_s=wall)
        result, steps, bad = M.parse_agy_stream(out)
        tokens = M.usage_tokens((result or {}).get("usage") or {})
        n_steps = sum(steps.values())
        if bad:
            return CallResult("contaminated", None, tokens, profile, rc, wall, n_steps)
        if rc != 0:
            return CallResult("error", None, tokens, profile, rc, wall, n_steps)
        structured = (result or {}).get("structured_output")
        if not isinstance(structured, dict) or (result or {}).get("status", "SUCCESS") != "SUCCESS":
            return CallResult("empty", None, tokens, profile, rc, wall, n_steps)
        return CallResult("ok", structured, tokens, profile, rc, wall, n_steps)


# ==============================================================================
# Budget
# ==============================================================================

class Budget:
    def __init__(self, max_calls: int, max_minutes: float, max_usd: float):
        self.max_calls, self.max_s, self.max_usd = max_calls, max_minutes * 60.0, max_usd
        self.t0 = time.monotonic()
        self.calls = 0
        self.usd = 0.0
        self.stop: Optional[str] = None
        self._lock = threading.Lock()

    def reason(self) -> Optional[str]:
        if self.stop:
            return self.stop
        if self.max_calls and self.calls >= self.max_calls:
            return "budget-calls"
        if self.max_s and time.monotonic() - self.t0 >= self.max_s:
            return "budget-time"
        if self.max_usd and self.usd >= self.max_usd:
            return "budget-usd"
        return None

    def take(self) -> bool:
        """Einen Aufruf reservieren (False: Budget erschöpft oder Lauf angehalten)."""
        with self._lock:
            if self.reason():
                return False
            self.calls += 1
            return True

    def spend(self, usd: float) -> None:
        with self._lock:
            self.usd += usd

    _RANK = {"needs-login": 3, "exhausted": 2, "errors": 1}

    def halt(self, why: str) -> None:
        """Lauf anhalten; ein schwererer Grund (Anmeldung > Kontingent > Fehler) ersetzt einen leichteren."""
        with self._lock:
            if self.stop is None or self._RANK.get(why, 0) > self._RANK.get(self.stop, 0):
                self.stop = why


# ==============================================================================
# Batches und Entscheidungen
# ==============================================================================

@dataclass
class Batch:
    kind: str
    units: List[Dict[str, Any]]
    prompt: str


@dataclass
class BatchResult:
    batch: Batch
    bodies: List[Dict[str, Any]] = field(default_factory=list)
    calls: int = 0
    retries: int = 0
    stage2_calls: int = 0
    usd: float = 0.0
    tokens: Dict[str, int] = field(default_factory=lambda: {"input": 0, "cached": 0, "output": 0, "thinking": 0})
    profiles: Dict[str, int] = field(default_factory=dict)
    outcome: str = "ok"
    unanswered: int = 0
    incomplete: int = 0


class Job:
    def __init__(self, a: argparse.Namespace, bundle: core.Bundle, data: Data, live: core.LiveLog, agy: Optional[Agy],
                 budget: Budget, run_id: str):
        self.a, self.bundle, self.data, self.live, self.agy, self.budget, self.run_id = a, bundle, data, live, agy, budget, run_id
        self.assets = {"bundle": bundle.sha256, "manifest": bundle.manifest_hash}
        self.call_no = 0
        self._lock = threading.Lock()
        self.sizes = {"snippet": a.batch_snippets, "figure": a.batch_figures, "element": a.batch_elements}

    # --- Prompts ---------------------------------------------------------------------------------------
    def items_for(self, units: List[Dict[str, Any]]) -> List[M.Item]:
        return [self.data.item(u["ref"], u.get("p")) for u in units]

    def build_prompt(self, kind: str, units: List[Dict[str, Any]]) -> str:
        if kind == "element":
            recs = [self.data.records[u["ref"]] for u in units]
            pool_ids = list(dict.fromkeys(c for u in units for c in u["cand"]))
            pool = [it for it in (self.data.item(c) for c in pool_ids) if it is not None]
            return M.reverse_prompt(recs, pool)
        return M.forward_prompt(self.data.records, self.items_for(units), {u["ref"]: u["cand"] for u in units})

    def fit(self, u: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Einheit, deren Prompt schon allein die Grenze überschreitet (z. B. ein Element, das hunderte Snippets
        zitieren): gezeigte Kandidaten von hinten kürzen (zitierte und Seiten-Nachbarn stehen vorn). Zitatkanten ordnet
        der Job für alle Kandidaten deterministisch zu; ``trimmed`` hält fest, wie viele das Modell nicht sah."""
        cap = self.a.max_prompt_bytes
        if len(self.build_prompt(u["kind"], [u]).encode("utf-8")) <= cap:
            return u
        cand = list(u["cand"])
        lo, hi = 0, len(cand)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if len(self.build_prompt(u["kind"], [dict(u, cand=cand[:mid])]).encode("utf-8")) <= cap:
                lo = mid
            else:
                hi = mid - 1
        if lo == 0:
            return None
        return dict(u, cand=cand[:lo], cand_all=cand, trimmed=len(cand) - lo)

    def batches(self, todo: List[Dict[str, Any]]) -> Iterator[Batch]:
        cur: List[Dict[str, Any]] = []
        prompt = ""
        for u in todo:
            if u["kind"] == "element" and u["ref"] not in self.data.records:
                continue
            if u["kind"] != "element" and self.data.item(u["ref"], u.get("p")) is None:
                continue
            u = self.fit(u)
            if u is None:
                log("Einheit zu groß für einen Aufruf, übersprungen")
                continue
            if cur and (u["kind"] != cur[0]["kind"] or len(cur) >= self.sizes[cur[0]["kind"]]):
                yield Batch(cur[0]["kind"], cur, prompt)
                cur, prompt = [], ""
            trial = self.build_prompt(u["kind"], cur + [u])
            if cur and len(trial.encode("utf-8")) > self.a.max_prompt_bytes:
                yield Batch(cur[0]["kind"], cur, prompt)
                cur, trial = [u], self.build_prompt(u["kind"], [u])
            else:
                cur = cur + [u]
            prompt = trial
        if cur:
            yield Batch(cur[0]["kind"], cur, prompt)

    # --- Aufruf mit Wiederholung ------------------------------------------------------------------------
    def _call(self, slot: Slot, prompt: str, schema: Dict[str, Any], res: BatchResult) -> Optional[Dict[str, Any]]:
        attempts = [prompt]
        strict = M.STRICT_RETRY_RULE + prompt + M.STRICT_RETRY_RULE
        if len(strict.encode("utf-8")) <= self.a.max_prompt_bytes + 2000:
            attempts.append(strict)
        for n, text in enumerate(attempts):
            if not self.budget.take():
                res.outcome = res.outcome if res.outcome != "ok" else "budget"
                return None
            r = self.agy.call(slot, text, schema)
            usd = M.list_price(self.agy.model, r.tokens)
            self.budget.spend(usd)
            res.calls += 1
            res.retries += 1 if n else 0
            res.usd += usd
            for key in res.tokens:
                res.tokens[key] += r.tokens.get(key, 0)
            if r.profile:
                res.profiles[r.profile] = res.profiles.get(r.profile, 0) + 1
            if r.outcome == "ok":
                res.last_profile = r.profile      # type: ignore[attr-defined]
                res.attempt = n + 1               # type: ignore[attr-defined]
                return r.structured
            res.outcome = r.outcome
            if r.outcome == "exhausted":
                self.budget.halt("exhausted")
                return None
            if r.outcome == "login":
                self.budget.halt("needs-login")
                return None
            if r.outcome not in ("contaminated", "empty", "error"):
                return None                      # Zeitüberschreitung: nicht wiederholen
        return None

    # --- Verarbeitung eines Batches ------------------------------------------------------------------
    def process(self, batch: Batch, slot: Slot) -> BatchResult:
        res = BatchResult(batch)
        res.last_profile = ""              # type: ignore[attr-defined]
        res.attempt = 1                    # type: ignore[attr-defined]
        try:
            if batch.kind == "element":
                self._process_reverse(batch, slot, res)
            else:
                self._process_forward(batch, slot, res)
        except Exception as exc:          # ein fehlerhafter Batch hält den Lauf nicht an
            res.bodies = []
            res.outcome = f"exception:{type(exc).__name__}"
        return res

    def _decision_body(self, u: Dict[str, Any], decision: Dict[str, Any], prompt: str, profile: str, share_usd: float,
                       extra_inputs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        best = sorted(decision["assignments"], key=lambda a: (-a["confidence"], core.RELATION_TYPES.index(a["relation_type"])
                      if a["relation_type"] in core.RELATION_TYPES else 99, a["target_element"], a["snippet_id"]))
        with self._lock:
            self.call_no += 1
            call_no = self.call_no
        mask = int(u.get("mask") or "0x0", 16)
        return {
            "kind": "decision",
            "id": core.identity(u["kind"], u["ref"], M.newest_release(mask)),
            "unit": u["unit"], "unit_key": u["key"], "unit_kind": u["kind"],
            "inputs": list(u["inputs"]) + list(extra_inputs or []),
            "assets": self.assets, "basis": u.get("basis"), "parent": u.get("prior"),
            "reason": {"kind": "never-decided" if u.get("status") == "new" else "input-changed", "ref": u.get("prior")},
            "decisions": [],
            "decision": decision,
            "relation_type": best[0]["relation_type"] if best else core.NO_RELATION,
            "confidence": round(best[0]["confidence"], 4) if best else 0.0,
            "rationale": decision.get("effect_rationale", ""),
            "model": self.agy.model, "effort": self.agy.effort, "backend": "agy", "profile": profile or "unbekannt",
            "prompt_hash": core.sha256_hex(prompt.encode("utf-8")), "call": f"{self.run_id}/{call_no}",
            "list_price_usd": round(share_usd, 6), "author": "worker", "run": self.run_id, "at": core.utc_now(),
        }

    def _assign(self, answer: Dict[str, Any], it: M.Item, cand: List[str], source: str,
                have: Dict[str, Dict[str, Any]], rejected: List[Dict[str, Any]]) -> None:
        best: Dict[str, Dict[str, Any]] = {}
        for m in answer.get("matches") or []:
            if m["id"] not in best or m["confidence"] > best[m["id"]]["confidence"]:
                best[m["id"]] = m
        for rid, m in best.items():
            why = M.gate(self.data.records.get(rid), it.mask)
            if why:
                rejected.append({"target": rid, "reason": why, "confidence": round(m["confidence"], 4)})
                continue
            row = {"target_element": rid, "snippet_id": it.id, "relation_type": m["relation_type"],
                   "confidence": round(m["confidence"], 4), "rationale": m["rationale"], "source": source}
            if rid not in have or row["confidence"] > have[rid]["confidence"]:
                have[rid] = row

    def _process_forward(self, batch: Batch, slot: Slot, res: BatchResult) -> None:
        items = self.items_for(batch.units)
        structured = self._call(slot, batch.prompt, M.FORWARD_SCHEMA, res)
        if structured is None:
            return
        parsed, _problems = M.parse_answer(structured, [it.id for it in items], "snippet_id", "record_id")
        res.unanswered = len(items) - len(parsed)
        profile = res.last_profile                      # type: ignore[attr-defined]
        states: List[Tuple[Dict[str, Any], M.Item, Dict[str, Any]]] = []
        need2: Dict[str, List[str]] = {}
        for u, it in zip(batch.units, items):
            ans = parsed.get(it.id)
            if ans is None:
                continue
            have: Dict[str, Dict[str, Any]] = {}
            rejected: List[Dict[str, Any]] = []
            self._assign(ans, it, u["cand"], "model", have, rejected)
            for c in it.cited:                       # deterministische Zitatkanten (--auto-cited)
                if c in self.data.records and c not in have:
                    have[c] = {"target_element": c, "snippet_id": it.id, "relation_type": "EXPLICIT_REFERENCE",
                               "confidence": 0.95, "rationale": "EXPLICIT_REFERENCE (deterministic citation)",
                               "source": "deterministic"}
            mods, unknown = M.resolve_modules(ans["modules"], self.data.module_index)
            covered = {self.data.records[c].module for c in u["cand"] if c in self.data.records}
            need = [m for m in mods if m not in covered][:core.METHOD["stage2_max_modules"]] if ans["external_effect"] else []
            decision = {"external_effect": ans["external_effect"], "modules": mods, "modules_unresolved": unknown,
                        "effect_rationale": ans["effect_rationale"], "candidates": list(u["cand"]),
                        "stage2": {"status": "none"}, "_have": have, "rejected": rejected}
            if u.get("trimmed"):
                decision["trimmed"] = u["trimmed"]
            if need:
                need2[it.id] = need
            states.append((u, it, decision))
        stage2_inputs: Dict[str, List[Dict[str, Any]]] = {}
        stage2_cost = 0.0
        if need2:
            sub = [(u, it, d) for u, it, d in states if it.id in need2]
            cands2 = {it.id: self.data.module_candidates(need2[it.id], it.text, set(u["cand"]), core.METHOD["stage2_k"])
                      for u, it, _ in sub}
            sub = [(u, it, d) for u, it, d in sub if cands2[it.id]]
            for u, it, d in states:
                if it.id in need2 and not cands2.get(it.id):
                    d["stage2"] = {"status": "no-candidates", "modules": need2[it.id]}
            if sub:
                prompt2 = M.forward_prompt(self.data.records, [it for _, it, _ in sub], cands2, stage2=True)
                usd_before = res.usd
                calls_before = res.calls
                structured2 = None
                if len(prompt2.encode("utf-8")) <= self.a.max_prompt_bytes:
                    structured2 = self._call(slot, prompt2, M.FORWARD_SCHEMA, res)
                res.stage2_calls += res.calls - calls_before
                stage2_cost = res.usd - usd_before
                parsed2 = M.parse_answer(structured2, [it.id for _, it, _ in sub], "snippet_id", "record_id")[0] if structured2 else {}
                for u, it, d in sub:
                    cand2 = cands2[it.id]
                    if structured2 is None:
                        d["stage2"] = {"status": "deferred" if res.outcome in ("budget",) or self.budget.reason() else "failed",
                                       "modules": need2[it.id], "candidates": cand2}
                        continue
                    ans2 = parsed2.get(it.id) or {"matches": []}
                    ans2 = {"matches": [m for m in ans2.get("matches") or [] if m["id"] in set(cand2)]}
                    self._assign(ans2, it, cand2, "stage2", d["_have"], d["rejected"])
                    d["stage2"] = {"status": "done", "modules": need2[it.id], "candidates": cand2,
                                   "prompt_hash": core.sha256_hex(prompt2.encode("utf-8"))}
                    stage2_inputs[it.id] = [{"kind": "candidates-stage2", "ref": "+".join(need2[it.id]),
                                             "hash": core.obj_hash(cand2)}]
        stage1_cost = res.usd - stage2_cost
        n1 = max(1, len(states))
        n2 = max(1, sum(1 for _, it, _ in states if it.id in stage2_inputs))
        for u, it, d in states:
            have = d.pop("_have")
            d["assignments"] = sorted(have.values(), key=lambda a: a["target_element"])
            d["rejected"] = d["rejected"][:20]
            if d["stage2"].get("status") in ("failed", "deferred"):
                res.incomplete += 1
            share = stage1_cost / n1 + (stage2_cost / n2 if it.id in stage2_inputs else 0.0)
            d["attempt"] = res.attempt                  # type: ignore[attr-defined]
            res.bodies.append(self._decision_body(u, d, batch.prompt, profile, share, stage2_inputs.get(it.id)))

    def _process_reverse(self, batch: Batch, slot: Slot, res: BatchResult) -> None:
        recs = [self.data.records[u["ref"]] for u in batch.units]
        structured = self._call(slot, batch.prompt, M.REVERSE_SCHEMA, res)
        if structured is None:
            return
        parsed, _problems = M.parse_answer(structured, [r.id for r in recs], "record_id", "snippet_id")
        res.unanswered = len(recs) - len(parsed)
        profile = res.last_profile                      # type: ignore[attr-defined]
        n = max(1, len(parsed))
        pool = {c for u in batch.units for c in u["cand"]}      # wie der Runner: alle Snippets des Batch-Pools
        for u, rec in zip(batch.units, recs):
            ans = parsed.get(rec.id)
            if ans is None:
                continue
            have: Dict[str, Dict[str, Any]] = {}
            rejected: List[Dict[str, Any]] = []
            best: Dict[str, Dict[str, Any]] = {}
            for m in ans["matches"]:
                if m["id"] not in best or m["confidence"] > best[m["id"]]["confidence"]:
                    best[m["id"]] = m
            for sid, m in best.items():
                it = self.data.item(sid)
                if sid not in pool or it is None:
                    rejected.append({"target": sid, "reason": "not_in_pool", "confidence": round(m["confidence"], 4)})
                    continue
                why = M.gate(rec, it.mask)
                if why:
                    rejected.append({"target": sid, "reason": why, "confidence": round(m["confidence"], 4)})
                    continue
                have[sid] = {"target_element": rec.id, "snippet_id": sid, "relation_type": m["relation_type"],
                             "confidence": round(m["confidence"], 4), "rationale": m["rationale"], "source": "model"}
            for sid in u.get("cand_all") or u["cand"]:
                it = self.data.item(sid)
                if it is not None and sid not in have and rec.id in it.cited:
                    have[sid] = {"target_element": rec.id, "snippet_id": sid, "relation_type": "EXPLICIT_REFERENCE",
                                 "confidence": 0.95, "rationale": "EXPLICIT_REFERENCE (deterministic citation)",
                                 "source": "deterministic"}
            mods, unknown = M.resolve_modules(ans["modules"], self.data.module_index)
            d = {"external_effect": ans["external_effect"], "modules": mods, "modules_unresolved": unknown,
                 "effect_rationale": ans["effect_rationale"], "candidates": list(u["cand"]),
                 "stage2": {"status": "none"}, "rejected": rejected[:20],
                 "assignments": sorted(have.values(), key=lambda a: a["snippet_id"]),
                 "attempt": res.attempt}                    # type: ignore[attr-defined]
            if u.get("trimmed"):
                d["trimmed"] = u["trimmed"]
            res.bodies.append(self._decision_body(u, d, batch.prompt, profile, res.usd / n))


# ==============================================================================
# Bündel beschaffen, Code-Stand prüfen
# ==============================================================================

def obtain_bundle(a: argparse.Namespace, work: Path) -> core.Bundle:
    sha = (a.bundle_sha256 or "").strip().lower()
    if a.bundle_file:
        archive = Path(a.bundle_file)
    else:
        if not a.bundle_url:
            raise core.BundleError("weder --bundle-file noch --bundle-url angegeben")
        if not re.match(r"^[0-9a-f]{64}$", sha):
            raise core.BundleError("--bundle-sha256 (64 Hex-Zeichen) ist Pflicht beim Herunterladen")
        if not a.bundle_url.startswith("https://"):
            raise core.BundleError("--bundle-url muss https:// sein")
        cache = Path(a.bundle_cache) if a.bundle_cache else work
        cache.mkdir(parents=True, exist_ok=True)
        archive = cache / f"live-bundle-{sha}.tar.gz"
        if not archive.exists() or core.file_sha256(archive) != sha:
            tmp = archive.with_suffix(".part")
            req = urllib.request.Request(a.bundle_url, headers={"User-Agent": "autodocs-live-distribution"})
            with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as fh:
                shutil.copyfileobj(resp, fh, 1 << 20)
            os.replace(tmp, archive)
            log(f"Bündel geladen: {archive.stat().st_size / 1e6:.1f} MB")
    return core.open_bundle(archive, work / "bundle", sha or None)


def check_code(bundle: core.Bundle) -> List[str]:
    want = bundle.manifest.get("code") or {}
    have = core.code_hashes(HERE)
    return [f"{n}: Bündel {want.get(n, '-')[:12]} / Job {have.get(n, '-')[:12]}" for n in core.CODE_FILES
            if want.get(n) != have.get(n)]


# ==============================================================================
# Status, Commit
# ==============================================================================

def profile_state(path: Optional[Path]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        st = json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
    except (OSError, ValueError):
        st = {}
    now = time.time()
    for name, s in sorted(st.items()):
        if not re.match(r"^[a-z0-9-]{1,20}$", str(name)):
            continue
        until = float(s.get("cooldown_until") or 0)
        out[name] = {"needs_login": bool(s.get("needs_login")),
                     "cooldown_until": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(until)) if until > now else None}
    return out


def build_status(live: core.LiveLog, plan: List[Dict[str, Any]], bundle: core.Bundle, state: Optional[Path]) -> Dict[str, Any]:
    decided = live.decided_keys()
    by_kind: Dict[str, Dict[str, int]] = {}
    for u in plan:
        b = by_kind.setdefault(u["kind"], {"planned": 0, "done": 0})
        b["planned"] += 1
        b["done"] += 1 if u["key"] in decided else 0
    total = sum(b["planned"] for b in by_kind.values())
    done = sum(b["done"] for b in by_kind.values())
    runs = [e for e in live.entries if e.get("kind") == "run"]
    findings: Dict[str, int] = {}
    for e in live.entries:
        if e.get("kind") == "finding":
            c = e["finding"].get("class", "other")
            findings[c] = findings.get(c, 0) + 1
    head = live.head
    return {
        "schema": "live-status@v1",
        "updated": core.utc_now(),
        "chain": {"seq": head["seq"] if head else 0, "hash12": head["hash"][:12] if head else None,
                  "decisions": len(live.decisions())},
        "bundle": {"sha12": bundle.sha256[:12], "created": bundle.manifest.get("created"),
                   "source_commit": (bundle.manifest.get("source_commit") or "")[:12]},
        "plan": {"total": total, "done": done, "remaining": total - done,
                 "progress": round(done / total, 4) if total else 1.0, "by_kind": by_kind},
        "cost": {"list_price_usd_total": round(sum(float(r.get("list_price_usd") or 0) for r in runs), 4),
                 "runs": len(runs), "currency": "USD, API-Listenpreise"},
        "last_runs": [{k: r.get(k) for k in ("run", "ended", "stop", "calls", "decided", "findings", "list_price_usd",
                                              "profiles")} for r in runs[-10:]],
        "findings": findings,
        "profiles": profile_state(state),
    }


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_AUTHOR_NAME="autodocs-live-worker", GIT_COMMITTER_NAME="autodocs-live-worker",
               GIT_AUTHOR_EMAIL="autodocs-live-worker@users.noreply.github.com",
               GIT_COMMITTER_EMAIL="autodocs-live-worker@users.noreply.github.com")
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=check)


def is_git(repo: Path) -> bool:
    return (repo / ".git").exists() and shutil.which("git") is not None


def commit(repo: Path, message: str) -> bool:
    if not is_git(repo):
        return False
    paths = [p for p in (core.CHAIN_DIR, "status") if (repo / p).exists()]
    if not paths:
        return False
    git(repo, "add", "-A", "--", *paths)
    if not git(repo, "diff", "--cached", "--quiet", check=False).returncode:
        return False
    git(repo, "commit", "-q", "-m", message)
    return True


def uncommitted_segments(repo: Path) -> List[Path]:
    seg = segment_dir(repo)
    if not seg.is_dir():
        return []
    if not is_git(repo):
        return []
    out = git(repo, "status", "--porcelain", "--untracked-files=all", "--", core.LOG_DIR, check=False).stdout
    return [repo / line[3:].strip() for line in out.splitlines() if line[3:].strip().endswith(".jsonl")]


def segment_dir(repo: Path) -> Path:
    return Path(repo) / core.LOG_DIR


# ==============================================================================
# Befehle
# ==============================================================================

def prepare(a: argparse.Namespace, work: Path, repo: Path):
    """Bündel, Code-Stand, Kette und offene Einheiten. Rückgabe (rc, bundle, live, plan, todo)."""
    try:
        bundle = obtain_bundle(a, work)
    except (core.BundleError, OSError, ValueError) as exc:
        log(f"Bündel unbrauchbar: {exc}")
        return (EXIT_DATA if isinstance(exc, core.BundleError) else EXIT_CONFIG), None, None, None, None
    drift = check_code(bundle)
    if drift:
        log("Code-Stand des Jobs passt nicht zum Bündel (live_bundle.py vendor ausführen): " + "; ".join(drift))
        return EXIT_CONFIG, None, None, None, None
    try:
        live = core.LiveLog(repo)
    except core.ChainError as exc:
        log(f"Kette in autodocs-live ungültig: {exc}")
        return EXIT_DATA, None, None, None, None
    head = bundle.live_head()
    if head and not core.contains(live.state, head):
        log(f"Kette enthält den Kopf des Bündels nicht (seq {head.get('seq')}, {str(head.get('hash'))[:12]}): Historie umgeschrieben?")
        return EXIT_DATA, None, None, None, None
    plan = list(bundle.rows("plan.jsonl"))
    decided = live.decided_keys()
    kinds = set(k for k in (a.kinds or "").split(",") if k) or set(core.UNIT_KINDS)
    todo = [u for u in plan if u["key"] not in decided and u["kind"] in kinds]
    counts = {k: sum(1 for u in todo if u["kind"] == k) for k in core.UNIT_KINDS}
    log(f"Bündel {bundle.sha256[:12]} (Quelle {(bundle.manifest.get('source_commit') or '?')[:10]}), Kette {len(live.entries)} "
        f"Glieder, Plan {len(plan)} Einheiten, offen {len(todo)} " + " ".join(f"{k}={v}" for k, v in counts.items()))
    return EXIT_OK, bundle, live, plan, todo


def cmd_pending(a: argparse.Namespace) -> int:
    """Nur zählen (vor der Einrichtung von agy): ``pending=<n>`` nach $GITHUB_OUTPUT bzw. --github-output."""
    rc, _bundle, _live, _plan, todo = prepare(a, Path(a.work or tempfile.mkdtemp(prefix="live-work-")), Path(a.live_repo))
    n = len(todo) if todo is not None else 0
    out = a.github_output or os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"pending={n if rc == EXIT_OK else 'error'}\nrc={rc}\n")
    if rc == EXIT_OK and not n:
        log("nichts zu tun")
    return rc


def cmd_run(a: argparse.Namespace) -> int:
    run_id = a.run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    work = Path(a.work or tempfile.mkdtemp(prefix="live-work-"))
    repo = Path(a.live_repo)
    rc, bundle, live, plan, todo = prepare(a, work, repo)
    if rc != EXIT_OK:
        return rc
    if not todo:
        log("nichts zu tun")
        return EXIT_OK
    data = Data(bundle)
    budget = Budget(a.max_calls, a.max_minutes, a.max_usd)
    if a.dry_run:
        job = Job(a, bundle, data, live, None, budget, run_id)
        sizes = []
        for b in job.batches(todo):
            sizes.append(len(b.prompt.encode("utf-8")))
            if len(sizes) >= max(1, a.max_calls or 20):
                break
        log(f"Trockenlauf: erste {len(sizes)} Batches, Prompt-Bytes Median {sorted(sizes)[len(sizes) // 2] if sizes else 0}, "
            f"Maximum {max(sizes) if sizes else 0}; kein Modellaufruf")
        return EXIT_OK
    base_profiles = [p for p in os.environ.get("AUTODOCS_AGY_PROFILES", "").split(",") if p]
    if not base_profiles:
        log("keine agy-Profile (setup-agy, AUTODOCS_AGY_PROFILES)")
        return EXIT_LOGIN
    state = Path(a.state or os.environ.get("AGY_STATE") or (work / "agy-state.json"))
    agy = Agy(Path(a.switch), state, a.model, a.effort, a.call_timeout, a.python)
    slots_root = Path(a.slots or (work / "agy-workers"))
    slots = [Slot(i, base_profiles, slots_root) for i in range(max(1, a.concurrency))]
    free: List[Slot] = list(slots)
    job = Job(a, bundle, data, live, agy, budget, run_id)
    new_decisions: List[Dict[str, Any]] = []
    tot = {"calls": 0, "retries": 0, "stage2_calls": 0, "usd": 0.0, "failed_batches": 0, "unanswered": 0,
           "incomplete": 0, "tokens": {"input": 0, "cached": 0, "output": 0, "thinking": 0}, "profiles": {},
           "by_kind": {k: 0 for k in core.UNIT_KINDS}}
    consecutive_fail = 0
    started = core.utc_now()
    gen = job.batches(todo)
    in_flight: Dict[Any, Tuple[Slot, str]] = {}
    pending: Optional[Batch] = None
    exhausted_gen = False
    with ThreadPoolExecutor(max_workers=len(slots)) as ex:
        while True:
            while free and not exhausted_gen and not budget.reason():
                if pending is None:
                    pending = next(gen, None)
                    if pending is None:
                        exhausted_gen = True
                        break
                # Reihenfolge der Arten: eine spätere Art startet erst, wenn die frühere ganz abgeschlossen ist
                if any(kind != pending.kind for _, kind in in_flight.values()):
                    break
                slot = free.pop()
                in_flight[ex.submit(job.process, pending, slot)] = (slot, pending.kind)
                pending = None
            if not in_flight:
                break
            done, _ = wait(list(in_flight), return_when=FIRST_COMPLETED)
            for f in done:
                free.append(in_flight.pop(f)[0])
                r: BatchResult = f.result()
                for body in r.bodies:
                    e = live.append(body)
                    new_decisions.append(e)
                    tot["by_kind"][e["unit_kind"]] += 1
                tot["calls"] += r.calls
                tot["retries"] += r.retries
                tot["stage2_calls"] += r.stage2_calls
                tot["usd"] += r.usd
                tot["unanswered"] += r.unanswered
                tot["incomplete"] += r.incomplete
                for k in tot["tokens"]:
                    tot["tokens"][k] += r.tokens.get(k, 0)
                for p, n in r.profiles.items():
                    tot["profiles"][p] = tot["profiles"].get(p, 0) + n
                if r.bodies:
                    consecutive_fail = 0
                    if len(new_decisions) and len(new_decisions) % 50 < len(r.bodies):
                        log(f"Fortschritt: {len(new_decisions)} Entscheidungen, {tot['calls']} Aufrufe, "
                            f"{tot['usd']:.3f} $ Listenpreis")
                elif r.calls and r.outcome not in ("budget", "exhausted", "login"):
                    tot["failed_batches"] += 1
                    consecutive_fail += 1
                    log(f"Batch ohne Ergebnis ({r.batch.kind}, {len(r.batch.units)} Einheiten): {r.outcome}")
                    if consecutive_fail >= a.max_failures:
                        budget.halt("errors")
    stop = budget.reason() or "done"
    # Patrouille Stufe 1: Prüfregeln über die neuen Entscheidungen
    findings_new = run_validators(bundle, data, live, new_decisions, run_id)
    known = live.finding_ids()
    n_findings = 0
    for f in findings_new:
        if f["id"] in known:
            continue
        live.append({"kind": "finding", "finding": f, "unit": f["subject"]["id"], "run": run_id, "at": core.utc_now()})
        known.add(f["id"])
        n_findings += 1
    remaining = len(todo) - len([e for e in new_decisions if core.decision_complete(e)])
    run_entry = {"kind": "run", "run": run_id, "at": core.utc_now(), "started": started, "ended": core.utc_now(),
                 "stop": stop, "assets": dict(job.assets, source_commit=bundle.manifest.get("source_commit"),
                                              created=bundle.manifest.get("created")),
                 "code": core.code_hashes(HERE),
                 "model": a.model, "effort": a.effort, "concurrency": len(slots),
                 "budget": {"max_calls": a.max_calls, "max_minutes": a.max_minutes, "max_usd": a.max_usd},
                 "calls": tot["calls"], "retries": tot["retries"], "stage2_calls": tot["stage2_calls"],
                 "failed_batches": tot["failed_batches"], "unanswered_units": tot["unanswered"],
                 "incomplete": tot["incomplete"], "decided": len(new_decisions), "decided_by_kind": tot["by_kind"],
                 "findings": n_findings, "tokens": tot["tokens"], "list_price_usd": round(tot["usd"], 6),
                 "profiles": tot["profiles"], "remaining": remaining}
    if tot["calls"] or new_decisions:
        live.append(run_entry)
        live.write_pointer(run_id, bundle.sha256[:12])
        core.write_atomic(repo / core.STATUS_FILE, (json.dumps(build_status(live, plan, bundle, state), indent=1,
                                                               sort_keys=True, ensure_ascii=False) + "\n").encode())
        check = core.verify_chain(repo)
        if not check.ok:
            log("Kette nach dem Schreiben ungültig: " + "; ".join(check.errors[:3]))
            return EXIT_DATA
        if a.commit:
            commit(repo, f"live-distribution {run_id}: {len(new_decisions)} Entscheidungen, {n_findings} Befunde, "
                         f"{tot['calls']} Aufrufe, {tot['usd']:.2f} $ Listenpreis")
    prof = ", ".join(f"{p} {n}" for p, n in sorted(tot["profiles"].items())) or "-"
    log(f"Ende ({stop}): {len(new_decisions)} Entscheidungen " + " ".join(f"{k}={v}" for k, v in tot["by_kind"].items())
        + f", {n_findings} Befunde, {tot['calls']} Aufrufe (Wiederholungen {tot['retries']}, Stufe 2 {tot['stage2_calls']}), "
        f"Tokens ein {tot['tokens']['input']} aus {tot['tokens']['output']}, {tot['usd']:.4f} $ Listenpreis, "
        f"Profile {prof}, offen {remaining}")
    if stop == "exhausted":
        return EXIT_EXHAUSTED
    if stop == "needs-login":
        return EXIT_LOGIN
    if stop == "errors":
        return EXIT_ERROR
    return EXIT_OK


def run_validators(bundle: core.Bundle, data: Data, live: core.LiveLog, new: List[Dict[str, Any]], run_id: str) -> List[Dict[str, Any]]:
    if not new:
        return []
    refs = {core.split_unit(e["unit"])[1] for e in new}
    refs |= {a["snippet_id"] for e in new for a in (e.get("decision") or {}).get("assignments") or []}
    uni = data.universe(strong_matrix_rows(bundle, refs))
    out = core.validate_decisions(new, live.latest_decisions(), uni, run_id, all_decisions=live.decisions())
    for e in new:
        kind, ref = core.split_unit(e["unit"])
        if kind == "figure" and ref in data.figure_rows:
            row = data.figure_rows[ref]
            subject = ((row.get("description_source") or {}).get("figure_id")) or ref
            out += core.figure_text_findings(subject, row.get("description") or "", run_id)
    return core.fnd.merge(out)


def cmd_finalize(a: argparse.Namespace) -> int:
    repo = Path(a.live_repo)
    for seg in uncommitted_segments(repo):
        cut = core.repair_tail(repo, seg)
        if cut:
            log(f"unvollständige letzte Zeile in {seg.name} entfernt ({cut} Bytes)")
    state = core.verify_chain(repo, check_pointer=False)
    if not state.ok:
        log("Kette ungültig: " + "; ".join(state.errors[:5]))
        return EXIT_DATA
    if state.head:
        ptr = state.pointer or {}
        if ptr.get("hash") != state.head["hash"]:
            live = core.LiveLog(repo, allow_invalid=True)
            runs = [e for e in live.entries if e.get("kind") == "run"]
            live.write_pointer(runs[-1]["run"] if runs else "finalize", ptr.get("basis"))
            log("Zeiger auf den Kopf der Kette gesetzt")
    final = core.verify_chain(repo)
    if not final.ok:
        log("Kette ungültig: " + "; ".join(final.errors[:5]))
        return EXIT_DATA
    if a.commit and commit(repo, f"live-distribution: Abschluss bei Glied {final.head['seq'] if final.head else 0}"):
        log("Abschluss-Commit erstellt")
    log(f"Kette gültig: {len(final.entries)} Glieder, Kopf {final.head['hash'][:12] if final.head else '-'}")
    return EXIT_OK


def cmd_verify(a: argparse.Namespace) -> int:
    state = core.verify_chain(Path(a.live_repo))
    if not state.ok:
        for err in state.errors[:20]:
            log("Fehler: " + err)
        return EXIT_DATA
    if a.bundle_file:
        b = core.open_bundle(Path(a.bundle_file), Path(tempfile.mkdtemp(prefix="live-verify-")), a.bundle_sha256 or None)
        if not core.contains(state, b.live_head()):
            log("Kette enthält den Kopf des Bündels nicht")
            return EXIT_DATA
    log(f"Kette gültig: {len(state.entries)} Glieder in {len(state.segments)} Segmenten")
    return EXIT_OK


def cmd_status(a: argparse.Namespace) -> int:
    p = Path(a.live_repo) / core.STATUS_FILE
    if not p.exists():
        log("noch kein Status")
        return EXIT_OK
    st = json.loads(p.read_text(encoding="utf-8"))
    pl = st.get("plan", {})
    log(f"Fortschritt {pl.get('done')}/{pl.get('total')} ({100 * float(pl.get('progress') or 0):.1f} %), "
        f"Kosten gesamt {st.get('cost', {}).get('list_price_usd_total')} $ Listenpreis, Läufe {st.get('cost', {}).get('runs')}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def bundle_args(x: argparse.ArgumentParser) -> None:
        x.add_argument("--bundle-url", default=os.environ.get("LIVE_BUNDLE_URL", ""))
        x.add_argument("--bundle-sha256", default=os.environ.get("LIVE_BUNDLE_SHA256", ""))
        x.add_argument("--bundle-file", default=None)
        x.add_argument("--bundle-cache", default=None, help="Verzeichnis für heruntergeladene Bündel (Schlüssel: SHA-256)")
        x.add_argument("--live-repo", required=True, help="Arbeitsbaum von autodocs-live")
        x.add_argument("--work", default=None)
        x.add_argument("--kinds", default="", help="nur diese Arten (snippet,figure,element)")

    pe = sub.add_parser("pending", help="offene Einheiten zählen (ohne agy)")
    bundle_args(pe)
    pe.add_argument("--github-output", default=None)
    r = sub.add_parser("run", help="Plan abarbeiten")
    bundle_args(r)
    r.add_argument("--slots", default=None, help="Verzeichnis der Arbeitsplätze (Standard <work>/agy-workers)")
    r.add_argument("--switch", default=str(HERE / "agy_switch.py"))
    r.add_argument("--python", default=sys.executable)
    r.add_argument("--state", default=None, help="Sperrzustand der Profile (Standard $AGY_STATE)")
    r.add_argument("--model", default=core.DEFAULT_MODEL)
    r.add_argument("--effort", default=core.DEFAULT_EFFORT)
    r.add_argument("--max-calls", type=int, default=300)
    r.add_argument("--max-minutes", type=float, default=40.0)
    r.add_argument("--max-usd", type=float, default=0.0, help="Obergrenze in $ Listenpreis (0 = keine)")
    r.add_argument("--max-failures", type=int, default=5, help="aufeinanderfolgende Batches ohne Ergebnis bis zum Abbruch")
    r.add_argument("--concurrency", type=int, default=4)
    r.add_argument("--call-timeout", type=int, default=300)
    r.add_argument("--batch-snippets", type=int, default=BATCH["snippet"])
    r.add_argument("--batch-figures", type=int, default=BATCH["figure"])
    r.add_argument("--batch-elements", type=int, default=BATCH["element"])
    r.add_argument("--max-prompt-bytes", type=int, default=MAX_PROMPT_BYTES)
    r.add_argument("--run-id", default=None)
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--no-commit", dest="commit", action="store_false", default=True)
    f = sub.add_parser("finalize", help="Segmentende reparieren, Zeiger setzen, prüfen, committen")
    f.add_argument("--live-repo", required=True)
    f.add_argument("--commit", action="store_true")
    v = sub.add_parser("verify", help="Kette prüfen")
    v.add_argument("--live-repo", required=True)
    v.add_argument("--bundle-file", default=None)
    v.add_argument("--bundle-sha256", default=None)
    s = sub.add_parser("status", help="Fortschritt anzeigen")
    s.add_argument("--live-repo", required=True)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    a = build_parser().parse_args(argv)
    fn = {"run": cmd_run, "pending": cmd_pending, "finalize": cmd_finalize, "verify": cmd_verify, "status": cmd_status}[a.cmd]
    if os.environ.get("LIVE_DEBUG") == "1":
        return fn(a)
    try:
        return fn(a)
    except Exception as exc:       # öffentliches Log: nur Art und Stelle, keine Meldung (sie könnte Daten enthalten)
        tb = exc.__traceback__
        while tb is not None and tb.tb_next is not None:
            tb = tb.tb_next
        where = f"{Path(tb.tb_frame.f_code.co_filename).name}:{tb.tb_lineno}" if tb else "?"
        log(f"unerwarteter Fehler {type(exc).__name__} in {where} (Details lokal mit LIVE_DEBUG=1)")
        return EXIT_ERROR


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGINT, _terminate)
    sys.exit(main())
