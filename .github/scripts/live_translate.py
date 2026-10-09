#!/usr/bin/env python3
"""Online-Job der Live-Übersetzung (CONCEPT-0061 §15): KI-Fragmente inkrementell in die zehn Zielsprachen übersetzen
und jede Übersetzung als Kettenglied in ``autodocs-live`` (``live/translation``) festhalten.

Läuft im Workflow ``live-translation.yml`` des öffentlichen Website-Repos (Kopie aus ``_src/tools``, siehe
``live_translate_bundle.py vendor``) und lokal in den Tests.

    live_translate.py pending  --bundle-url URL --bundle-sha256 SHA --live-repo DIR
    live_translate.py run      --bundle-url URL --bundle-sha256 SHA --live-repo DIR [Budget] [--dry-run]
    live_translate.py finalize --live-repo DIR [--commit]
    live_translate.py verify   --live-repo DIR [--bundle-file F]
    live_translate.py status   --live-repo DIR

Ablauf von ``run``: Bündel laden und prüfen (SHA-256, Manifest, Code-Hashes), Kette prüfen, offene Einheiten bestimmen
(Schlüssel nicht in der Kette), Übersetzungsspeicher aus Bündel (Register ``_src/i18n/<lang>/segments.json``) und
Kette aufbauen, fehlende Segmente in Aufrufe bündeln (eine Sprache und ein Modell je Aufruf, geschätzte Ausgabe
≤ ``--max-output-tokens``, Prompt ≤ ``--max-prompt-bytes``), agy über ``agy_switch.py`` mit derselben Sperre wie die
Verteilung aufrufen (``live_distribute.Slot``), jede Segmentübersetzung prüfen (abgelehnt: einmal mit Hinweisen
wiederholen, sonst Befund), angenommene Segmente als ``tm``-Glied anhängen, fertige Einheiten zusammensetzen, als
Fragment prüfen und als ``translation``-Glied (oder Befund) anhängen; Laufglied, Zeiger, Status, lokaler Commit.

Parallelität: bis ``--concurrency`` Arbeitsplätze; die wirksame Grenze startet bei der Hälfte, steigt nach
erfolgreichen Aufrufen und halbiert sich, wenn agy_switch ein erschöpftes Profil meldet oder die Latenz je
Ausgabe-Token stark steigt. Sind beide Profile im Kontingent gesperrt, startet der Lauf keine Aufrufe mehr (Exit 75),
damit Verteilung und Abo-Relais den Rest des Kontingents behalten.

Das Log nennt nur Zahlen, Kosten zu API-Listenpreisen und die Profilnamen (leo, neo); nie Prompts, Texte oder Antworten.
Exit: 0 fertig/Budget/nichts zu tun, 75 alle Profile erschöpft, 77 kein Profil angemeldet, 65 Kette oder Bündel
ungültig, 78 Konfiguration, 1 sonstige Fehler.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import live_translate_core as C  # noqa: E402
import live_distribute as LD  # noqa: E402  (Sperre der Arbeitsplätze, Prozessgruppen, Budget: eine Quelle)

EXIT_OK, EXIT_ERROR, EXIT_DATA, EXIT_EXHAUSTED, EXIT_LOGIN, EXIT_CONFIG = 0, 1, 65, 75, 77, 78
MAX_MINUTES_CAP = 320.0            # Job-Grenze von GitHub: 6 h; Rest für Einrichtung, Abschluss und Übertragung
HARD_PROMPT_BYTES = 100_000        # agy -p: ein Argument, Linux 128 KiB


def log(msg: str) -> None:
    print("live-tr: " + msg, flush=True)


# ==============================================================================
# agy
# ==============================================================================

@dataclass
class CallResult:
    outcome: str                        # ok | exhausted | login | error | contaminated | empty | timeout
    structured: Optional[Dict[str, Any]] = None
    tokens: Dict[str, int] = field(default_factory=lambda: {"input": 0, "cached": 0, "output": 0, "thinking": 0})
    profile: str = ""
    rc: int = 0
    wall_s: float = 0.0
    switched: bool = False              # agy_switch wechselte wegen eines erschöpften Profils


class Agy:
    def __init__(self, switch: Path, state: Path, effort: str, python: str):
        self.switch, self.state, self.effort, self.python = switch, state, effort, python

    def env(self, slot: LD.Slot) -> Dict[str, str]:
        src = os.environ
        env = {"PATH": src.get("PATH", "/usr/bin:/bin"), "LANG": src.get("LANG", "C.UTF-8"),
               "AUTODOCS_AGY_PROFILES": slot.profiles, "AGY_STATE": str(self.state)}
        for k in ("RUNNER_TEMP", "TMPDIR", "TZ"):
            if src.get(k):
                env[k] = src[k]
        return env

    def command(self, prompt: str, model: str, timeout_s: int) -> List[str]:
        cmd = [self.python, str(self.switch), "--state", str(self.state), "--", "-p", prompt, "--model", model]
        if not C.model_effort(model):
            cmd += ["--effort", self.effort]   # Modell-IDs mit -low/-medium/-high tragen die Stufe selbst
        return cmd + ["--output-format", "stream-json", "--json-schema",
                      json.dumps(C.TRANSLATION_SCHEMA, separators=(",", ":")), "--disable-slash-commands",
                      "--print-timeout", f"{timeout_s}s"]

    def call(self, slot: LD.Slot, prompt: str, model: str, timeout_s: int) -> CallResult:
        if not slot.lock():
            return CallResult("error", rc=EXIT_CONFIG)
        t0 = time.monotonic()
        try:
            rc, out, err, timed_out = LD._run_group(self.command(prompt, model, timeout_s), timeout_s + 60,
                                                    self.env(slot), str(slot.call_dir))
        except OSError:
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
        switched = any(isinstance(t, dict) and t.get("result") == "exhausted" for t in sw.get("tried") or [])
        if timed_out:
            return CallResult("timeout", profile=profile, rc=rc, wall_s=wall, switched=switched)
        if rc == EXIT_EXHAUSTED:
            return CallResult("exhausted", profile=profile, rc=rc, wall_s=wall, switched=True)
        if rc == EXIT_LOGIN:
            return CallResult("login", profile=profile, rc=rc, wall_s=wall)
        result, _steps, bad = C.parse_agy_stream(out)
        tokens = C.usage_tokens((result or {}).get("usage") or {})
        if bad:
            return CallResult("contaminated", None, tokens, profile, rc, wall, switched)
        if rc != 0:
            return CallResult("error", None, tokens, profile, rc, wall, switched)
        structured = (result or {}).get("structured_output")
        if not isinstance(structured, dict) or (result or {}).get("status", "SUCCESS") != "SUCCESS":
            return CallResult("empty", None, tokens, profile, rc, wall, switched)
        return CallResult("ok", structured, tokens, profile, rc, wall, switched)


class Throttle:
    """Wirksame Parallelität: startet bei der Hälfte von ``--concurrency``, +1 nach ``limit`` unauffälligen
    Aufrufen, ×0,5 bei Kontingentmeldung (Profilwechsel in agy_switch), ×0,75 wenn die Latenz je 1.000
    Ausgabe-Tokens über das 1,8-Fache der Anfangsmessung steigt; höchstens eine Senkung je 30 s."""

    def __init__(self, maximum: int, minimum: int = 1, start: Optional[int] = None):
        self.max, self.min = max(1, maximum), max(1, minimum)
        self.limit = min(self.max, max(self.min, start if start else (self.max + 1) // 2))
        self.ok_since = 0
        self.samples: List[float] = []
        self.base: Optional[float] = None
        self.ewma: Optional[float] = None
        self.last_cut = -1e9
        self.cuts = 0
        self.peak = self.limit
        self.low = self.limit
        self._lock = threading.Lock()

    def _cut(self, factor: float) -> None:
        now = time.monotonic()
        if now - self.last_cut < 30:
            return
        self.limit = max(self.min, int(self.limit * factor))
        self.low = min(self.low, self.limit)
        self.last_cut, self.ok_since = now, 0
        self.cuts += 1

    def observe(self, r: CallResult) -> None:
        with self._lock:
            if r.switched or r.outcome == "exhausted":
                self._cut(0.5)
                return
            if r.outcome != "ok":
                return
            out = r.tokens.get("output", 0) + r.tokens.get("thinking", 0)
            if out >= 1000:
                per = r.wall_s / (out / 1000.0)
                if self.base is None:
                    self.samples.append(per)
                    if len(self.samples) >= 6:
                        self.base = statistics.median(self.samples)
                self.ewma = per if self.ewma is None else 0.8 * self.ewma + 0.2 * per
                if self.base and self.ewma > 1.8 * self.base:
                    self._cut(0.75)
                    return
            self.ok_since += 1
            if self.ok_since >= self.limit and self.limit < self.max:
                self.limit += 1
                self.peak = max(self.peak, self.limit)
                self.ok_since = 0


# ==============================================================================
# Bündel, Code-Stand
# ==============================================================================

def obtain_bundle(a: argparse.Namespace, work: Path) -> C.Bundle:
    sha = (a.bundle_sha256 or "").strip().lower()
    if a.bundle_file:
        archive = Path(a.bundle_file)
    else:
        if not a.bundle_url:
            raise C.BundleError("weder --bundle-file noch --bundle-url angegeben")
        if not re.match(r"^[0-9a-f]{64}$", sha):
            raise C.BundleError("--bundle-sha256 (64 Hex-Zeichen) ist Pflicht beim Herunterladen")
        if not a.bundle_url.startswith("https://"):
            raise C.BundleError("--bundle-url muss https:// sein")
        cache = Path(a.bundle_cache) if a.bundle_cache else work
        cache.mkdir(parents=True, exist_ok=True)
        archive = cache / f"live-translation-bundle-{sha}.tar.gz"
        if not archive.exists() or C.file_sha256(archive) != sha:
            tmp = archive.with_suffix(".part")
            req = urllib.request.Request(a.bundle_url, headers={"User-Agent": "autodocs-live-translation"})
            with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as fh:
                shutil.copyfileobj(resp, fh, 1 << 20)
            os.replace(tmp, archive)
            log(f"Bündel geladen: {archive.stat().st_size / 1e6:.1f} MB")
    return C.open_bundle(archive, work / "bundle", sha or None)


def check_code(bundle: C.Bundle) -> List[str]:
    want = bundle.manifest.get("code") or {}
    have = C.code_hashes(HERE)
    return [f"{n}: Bündel {want.get(n, '-')[:12]} / Job {have.get(n, '-')[:12]}" for n in C.CODE_FILES
            if want.get(n) != have.get(n)]


def parse_models(a: argparse.Namespace) -> Dict[str, str]:
    models = dict(C.DEFAULT_MODELS)
    if a.model_guide:
        models["guide"] = a.model_guide
    if a.model_text:
        models["api"] = models["element"] = a.model_text
    for spec in a.model or []:
        tier, _, mid = spec.partition("=")
        if tier in C.TIERS and mid:
            models[tier] = mid
    for tier, mid in models.items():
        if not re.match(r"^[a-z0-9][a-z0-9.\-]{2,60}$", mid):
            raise ValueError(f"ungültige Modell-ID für {tier}")
    return models


def prepare(a: argparse.Namespace, work: Path, repo: Path):
    """Bündel, Code-Stand, Kette, offene Einheiten. Rückgabe (rc, bundle, log, plan, todo)."""
    try:
        bundle = obtain_bundle(a, work)
    except (C.BundleError, OSError, ValueError) as exc:
        log(f"Bündel unbrauchbar: {exc}")
        return (EXIT_DATA if isinstance(exc, C.BundleError) else EXIT_CONFIG), None, None, None, None
    drift = check_code(bundle)
    if drift:
        log("Code-Stand des Jobs passt nicht zum Bündel (live_translate_bundle.py vendor): " + "; ".join(drift))
        return EXIT_CONFIG, None, None, None, None
    try:
        tlog = C.TranslationLog(repo)
    except C.ChainError as exc:
        log(f"Kette live/translation ungültig: {exc}")
        return EXIT_DATA, None, None, None, None
    head = bundle.live_head()
    if head and not C.contains(tlog.state, head):
        log(f"Kette enthält den Kopf des Bündels nicht (seq {head.get('seq')}): Historie umgeschrieben?")
        return EXIT_DATA, None, None, None, None
    plan = list(bundle.rows("plan.jsonl"))
    entries = tlog.entries
    if getattr(a, "retry_findings", False):
        decided = {e["unit_key"] for e in entries if e.get("kind") == "translation"}
    else:
        decided = C.decided_keys(entries)
    langs = [x for x in (a.langs or "").split(",") if x] or list(C.LANGS)
    tiers = [x for x in (a.tiers or "").split(",") if x] or list(C.TIERS)
    todo = [u for u in plan if u["key"] not in decided and u["lang"] in langs and u["tier"] in tiers]
    by_tier = {t: sum(1 for u in todo if u["tier"] == t) for t in C.TIERS}
    log(f"Bündel {bundle.sha256[:12]} (Quelle {(bundle.manifest.get('source_commit') or '?')[:10]}), Kette "
        f"{len(entries)} Glieder, Plan {len(plan)} Einheiten, offen {len(todo)} "
        + " ".join(f"{k}={v}" for k, v in by_tier.items()))
    return EXIT_OK, bundle, tlog, plan, todo


def profiles_ready(state_path: Path, homes: List[str]) -> Tuple[int, int]:
    """(bereite Profile, angemeldete Profile) laut Sperrzustand."""
    try:
        st = json.loads(Path(state_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    now = time.time()
    ready = logged = 0
    for h in homes:
        name = os.path.basename(h.rstrip("/")).replace("agy-profile-", "")
        s = st.get(name) or {}
        if s.get("needs_login"):
            continue
        logged += 1
        if float(s.get("cooldown_until") or 0) <= now:
            ready += 1
    return ready, logged


# ==============================================================================
# Befehle
# ==============================================================================

def cmd_pending(a: argparse.Namespace) -> int:
    rc, _b, _l, _p, todo = prepare(a, Path(a.work or tempfile.mkdtemp(prefix="live-tr-")), Path(a.live_repo))
    n = len(todo) if todo is not None else 0
    out = a.github_output or os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"pending={n if rc == EXIT_OK else 'error'}\nrc={rc}\n")
    if rc == EXIT_OK and not n:
        log("nichts zu tun")
    return rc


@dataclass
class BatchResult:
    batch: C.Batch
    accepted: Dict[str, str] = field(default_factory=dict)
    failed: Dict[str, List[str]] = field(default_factory=dict)
    answered: bool = False
    calls: int = 0
    retries: int = 0
    usd: float = 0.0
    tokens: Dict[str, int] = field(default_factory=lambda: {"input": 0, "cached": 0, "output": 0, "thinking": 0})
    profiles: Dict[str, int] = field(default_factory=dict)
    profile: str = ""
    outcome: str = "ok"
    wall_s: float = 0.0


class Job:
    def __init__(self, a, bundle: C.Bundle, tlog: C.TranslationLog, agy: Optional[Agy], budget: LD.Budget,
                 throttle: Throttle, run_id: str, models: Dict[str, str]):
        self.a, self.bundle, self.tlog, self.agy, self.budget, self.throttle = a, bundle, tlog, agy, budget, throttle
        self.run_id, self.models = run_id, models
        self.assets = {"bundle": bundle.sha256, "manifest": bundle.manifest_hash}
        self.terms = bundle.terms()
        self.frags = bundle.fragments()
        self.tm = bundle.tm()
        self.tm_loaded = self.tm.load_chain(tlog.entries)
        self.tm_models: Dict[str, str] = {e["hash"][:12]: e.get("model", "") for e in tlog.entries if e.get("kind") == "tm"}
        self.seg_cost: Dict[Tuple[str, str, str], float] = {}
        self.tot = {"calls": 0, "retries": 0, "usd": 0.0, "failed_batches": 0, "segments": 0, "rejected": 0,
                    "tokens": {"input": 0, "cached": 0, "output": 0, "thinking": 0}, "profiles": {}, "models": {},
                    "units": {t: 0 for t in C.TIERS}, "by_lang": {}, "findings": 0, "assembled_only": 0}
        self.ratio_obs: Dict[str, List[float]] = {}

    # --- Aufruf in einem Arbeitsplatz -------------------------------------------------------------------
    def process(self, b: C.Batch, slot: LD.Slot) -> BatchResult:
        res = BatchResult(b)
        try:
            attempts = [b.prompt]
            strict = C.STRICT_RETRY_RULE + b.prompt + C.STRICT_RETRY_RULE
            if len(strict.encode("utf-8")) <= HARD_PROMPT_BYTES:
                attempts.append(strict)
            structured = None
            for n, text in enumerate(attempts):
                if len(text.encode("utf-8")) > HARD_PROMPT_BYTES:
                    res.outcome = "too-large"
                    return res
                if not self.budget.take():
                    res.outcome = "budget"
                    return res
                r = self.agy.call(slot, text, b.model, self.a.call_timeout)
                self.throttle.observe(r)
                usd = C.list_price(b.model, r.tokens)
                self.budget.spend(usd)
                res.calls += 1
                res.retries += 1 if n else 0
                res.usd += usd
                res.wall_s += r.wall_s
                for k in res.tokens:
                    res.tokens[k] += r.tokens.get(k, 0)
                if r.profile:
                    res.profiles[r.profile] = res.profiles.get(r.profile, 0) + 1
                if r.outcome == "ok":
                    structured, res.profile = r.structured, r.profile
                    break
                res.outcome = r.outcome
                if r.outcome == "exhausted":
                    self.budget.halt("exhausted")
                    return res
                if r.outcome == "login":
                    self.budget.halt("needs-login")
                    return res
                if r.outcome not in ("contaminated", "empty", "error"):
                    return res
            if structured is None:
                return res
            res.outcome, res.answered = "ok", True
            got, _problems = C.parse_translations(structured, [it.bid for it in b.items])
            for it, c in zip(b.items, b.claims):
                t = got.get(it.bid)
                if t is None:
                    res.failed[c.sid] = ["missing"]
                    continue
                t2 = C.normalize_output(t, b.lang)
                probs = C.check_segment(c.de, t2, b.lang, self.terms)
                if probs:
                    res.failed[c.sid] = probs
                else:
                    res.accepted[c.sid] = t2
        except Exception as exc:          # ein fehlerhafter Aufruf hält den Lauf nicht an
            res.outcome = f"exception:{type(exc).__name__}"
            res.answered = False
        return res

    # --- Ergebnisse in die Kette --------------------------------------------------------------------------
    def record(self, sch: C.Scheduler, r: BatchResult) -> None:
        b = r.batch
        t = self.tot
        t["calls"] += r.calls
        t["retries"] += r.retries
        t["usd"] += r.usd
        for k in t["tokens"]:
            t["tokens"][k] += r.tokens.get(k, 0)
        for p, n in r.profiles.items():
            t["profiles"][p] = t["profiles"].get(p, 0) + n
        mm = t["models"].setdefault(b.model, {"calls": 0, "usd": 0.0, "output": 0})
        mm["calls"] += r.calls
        mm["usd"] += r.usd
        mm["output"] += r.tokens.get("output", 0)
        if not r.answered:
            if r.outcome == "timeout" or r.outcome.startswith("exception:"):
                sch.requeue(b)
            else:
                sch.abandon(b)
            return
        origin = ""
        if r.accepted:
            segs = []
            total = sum(len(c.de) for c in b.claims if c.sid in r.accepted) or 1
            for c in b.claims:
                if c.sid in r.accepted:
                    segs.append({"sid": c.sid, "scope": c.scope, "src": C.text_sha256(c.de)[:16], "path": c.path,
                                 "t": r.accepted[c.sid]})
                    self.seg_cost[(b.lang, c.sid, c.scope)] = r.usd * len(c.de) / total
            e = self.tlog.append({
                "kind": "tm", "lang": b.lang, "segments": segs, "model": b.model,
                "effort": C.model_effort(b.model, self.a.effort), "backend": "agy", "profile": r.profile or "unbekannt",
                "attempt": b.attempt, "call": f"{self.run_id}/{b.no}", "recipe": C.RECIPE_ID,
                "recipe_hash": C.RECIPE_HASH, "prompt_hash": C.text_sha256(b.prompt), "tokens": r.tokens,
                "list_price_usd": round(r.usd, 6), "rejected": len(r.failed), "author": "worker",
                "assets": self.assets, "run": self.run_id, "at": C.utc_now()})
            origin = "tm:" + e["hash"][:12]
            self.tm_models[e["hash"][:12]] = b.model
            if r.tokens.get("output"):
                chars = sum(len(c.de) for c in b.claims)
                self.ratio_obs.setdefault(b.lang, []).append(
                    max(0.05, (r.tokens["output"] - C.SEG_JSON_TOKENS * len(b.claims)) / max(1, chars)))
                obs = self.ratio_obs[b.lang][-8:]
                sch.ratios[b.lang] = min(0.8, max(0.1, statistics.median(obs)))
        t["segments"] += len(r.accepted)
        t["rejected"] += len(r.failed)
        sch.complete(b, r.accepted, r.failed, origin)

    def finalize_unit(self, sch: C.Scheduler, u: C.UnitState) -> None:
        u.done = True
        plan = u.plan
        lang = plan["lang"]
        tr, origins, failed = sch.assemble(u)
        if any(ps != ["missing"] for _, ps in failed):
            self.add_finding(plan, failed, "translation-invalid")
            return
        if failed:                          # nicht übersetzt (z. B. Budget): Einheit bleibt offen
            return
        f = u.frag
        out = C.rebuild(f.html, f.segs, tr, lang, self.terms.docref.get(lang))
        probs = C.check_fragment(f.html, out, f.segs, tr, lang)
        if probs:
            self.add_finding(plan, [("fragment", probs)], "translation-structure")
            return
        scopes = dict(u.sids)
        cost = sum(self.seg_cost.get((lang, sid, scopes.get(sid, "")), 0.0) for sid in set(u.claimed))
        models = sorted({self.tm_models.get(o[3:], "") for _, o in origins if o.startswith("tm:")} - {""})
        new = sum(1 for sid in set(u.claimed) if (lang, sid, scopes.get(sid, "")) in self.seg_cost)
        hits = words = 0
        for i, sg in enumerate(f.segs):
            h, w = C.german_markers(tr[i], lang, keep=C.protected_tokens(sg.m))
            hits += h
            words += w
        de_len = sum(C.prose_len(sg.m) for sg in f.segs) or 1
        t_len = sum(C.prose_len(tr[i]) for i in range(len(f.segs)))
        self.tlog.append({
            "kind": "translation", "unit": plan["unit"], "unit_key": plan["key"],
            "id": C.identity(f.path, lang, f.release), "lang": lang, "path": f.path, "tier": plan["tier"],
            "release": f.release, "source_sha256": f.sha256, "trace_output": f.trace_output,
            "output_sha256": C.text_sha256(out),
            "inputs": [{"kind": "fragment", "ref": f.path, "hash": f.sha256},
                       {"kind": "protected-terms", "ref": "_src/i18n/protected_terms.json", "hash": plan["terms"]},
                       {"kind": "glossary", "ref": lang, "hash": plan["glossary"]},
                       {"kind": "recipe", "ref": C.RECIPE_ID, "hash": C.RECIPE_HASH}],
            "assets": self.assets, "parent": plan.get("prior"),
            "reason": {"kind": "source-changed" if plan.get("status") == "stale" else "never-translated",
                       "ref": plan.get("prior")},
            "decisions": [], "segments": origins, "models": models,
            "stats": {"segments": len(f.segs), "new_segments": new, "reused": len(f.segs) - new,
                      "german_markers": hits, "words": words, "ratio": round(t_len / de_len, 3)},
            "list_price_usd": round(cost, 6), "author": "worker", "run": self.run_id, "at": C.utc_now()})
        self.tot["units"][plan["tier"]] += 1
        self.tot["by_lang"][lang] = self.tot["by_lang"].get(lang, 0) + 1
        if not new:
            self.tot["assembled_only"] += 1

    def add_finding(self, plan: Dict[str, Any], problems: List[Tuple[str, List[str]]], cls: str) -> None:
        f = C.translation_finding(plan, problems, cls, self.run_id)
        self.tlog.append({"kind": "finding", "finding": f, "unit": plan["unit"], "unit_key": plan["key"],
                          "lang": plan["lang"], "path": plan["path"], "run": self.run_id, "at": C.utc_now()})
        self.tot["findings"] += 1


def summarize_estimate(est: Dict[str, Any]) -> str:
    w = est["wall_hours"]
    return (f"{est['calls']} Aufrufe, {est['list_price_usd']} $ Listenpreis, Tokens ein {est['tokens']['input']} aus "
            f"{est['tokens']['output']} Denken {est['tokens']['thinking']}, Laufzeit "
            + ", ".join(f"{k} parallel {v} h" for k, v in w.items()))


def cmd_run(a: argparse.Namespace) -> int:
    run_id = a.run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    work = Path(a.work or tempfile.mkdtemp(prefix="live-tr-"))
    repo = Path(a.live_repo)
    try:
        models = parse_models(a)
    except ValueError as exc:
        log(f"Konfiguration: {exc}")
        return EXIT_CONFIG
    rc, bundle, tlog, plan, todo = prepare(a, work, repo)
    if rc != EXIT_OK:
        return rc
    if not todo:
        log("nichts zu tun")
        return EXIT_OK
    max_minutes = min(float(a.max_minutes), MAX_MINUTES_CAP)
    budget = LD.Budget(a.max_calls, max_minutes, a.max_usd)
    throttle = Throttle(a.concurrency, a.min_concurrency)
    log("Modelle " + ", ".join(f"{t}={m}" for t, m in models.items()) + f", Budget {a.max_calls} Aufrufe, "
        f"{max_minutes:g} min, {a.max_usd or 'ohne'} $, Parallelität bis {a.concurrency}")
    if a.dry_run:
        job = Job(a, bundle, tlog, None, budget, throttle, run_id, models)
        est = C.estimate(todo, job.frags, job.tm, job.terms, models, a.max_output_tokens)
        flash = {t: "gemini-3.8-flash-medium" for t in C.TIERS}
        est_flash = C.estimate(todo, job.frags, job.tm, job.terms, flash, a.max_output_tokens)
        log("Trockenlauf, kein Modellaufruf. Schätzung (gewählte Modelle): " + summarize_estimate(est))
        log("Schätzung (alles Flash): " + summarize_estimate(est_flash))
        for m, v in est["by_model"].items():
            log(f"  {m}: {round(v['calls'])} Aufrufe, Prompt höchstens {v['prompt_bytes_max']} Bytes, {round(v['usd'], 2)} $")
        return EXIT_OK
    base_profiles = [p for p in os.environ.get("AUTODOCS_AGY_PROFILES", "").split(",") if p]
    if not base_profiles:
        log("keine agy-Profile (setup-agy, AUTODOCS_AGY_PROFILES)")
        return EXIT_LOGIN
    state = Path(a.state or os.environ.get("AGY_STATE") or (work / "agy-state.json"))
    ready, logged = profiles_ready(state, base_profiles)
    if not logged:
        log("Kein Profil angemeldet (Sperrzustand)")
        return EXIT_LOGIN
    if not ready:
        log("Alle Profile im Kontingent gesperrt: Übersetzung startet keine Aufrufe (Rest für Verteilung und Relais)")
        return EXIT_EXHAUSTED
    agy = Agy(Path(a.switch), state, a.effort, a.python)
    slots_root = Path(a.slots or (work / "agy-workers"))
    slots = [LD.Slot(i, base_profiles, slots_root) for i in range(max(1, a.concurrency))]
    free: List[LD.Slot] = list(slots)
    job = Job(a, bundle, tlog, agy, budget, throttle, run_id, models)
    sch = C.Scheduler(todo, job.frags, job.tm, job.terms, models, a.max_output_tokens, a.max_prompt_bytes)
    started = C.utc_now()
    consecutive_fail = 0
    in_flight: Dict[Any, LD.Slot] = {}
    exhausted_gen = False
    log(f"Übersetzungsspeicher: {len(job.tm.reg)} Register-Einträge, {job.tm_loaded} aus der Kette")
    with ThreadPoolExecutor(max_workers=len(slots)) as ex:
        while True:
            while free and not exhausted_gen and not budget.reason() and len(in_flight) < throttle.limit:
                b = sch.next_batch()
                for u in sch.ready():
                    job.finalize_unit(sch, u)
                if b is None:
                    exhausted_gen = not sch.retry
                    break
                slot = free.pop()
                in_flight[ex.submit(job.process, b, slot)] = slot
            for u in sch.ready():
                job.finalize_unit(sch, u)
            if not in_flight:
                if exhausted_gen or budget.reason():
                    break
                b = None
                exhausted_gen = True
                continue
            done, _ = wait(list(in_flight), return_when=FIRST_COMPLETED)
            for fut in done:
                free.append(in_flight.pop(fut))
                r: BatchResult = fut.result()
                job.record(sch, r)
                if r.answered:
                    consecutive_fail = 0
                    exhausted_gen = False
                elif r.outcome not in ("budget", "exhausted", "login"):
                    job.tot["failed_batches"] += 1
                    consecutive_fail += 1
                    log(f"Aufruf ohne Ergebnis ({r.batch.lang}, {len(r.batch.claims)} Segmente): {r.outcome}")
                    if consecutive_fail >= a.max_failures:
                        budget.halt("errors")
                if job.tot["calls"] and job.tot["calls"] % 25 == 0 and r.calls:
                    log(f"Fortschritt: {sum(job.tot['units'].values())} Einheiten, {job.tot['calls']} Aufrufe, "
                        f"{job.tot['usd']:.2f} $, Parallelität {throttle.limit}")
            for u in sch.ready():
                job.finalize_unit(sch, u)
    for b in sch.retry:
        sch.abandon(b)
    stop = budget.reason() or "done"
    decided = C.decided_keys(tlog.entries)
    remaining = sum(1 for u in todo if u["key"] not in decided)
    t = job.tot
    run_entry = {"kind": "run", "run": run_id, "at": C.utc_now(), "started": started, "ended": C.utc_now(),
                 "stop": stop, "assets": dict(job.assets, source_commit=bundle.manifest.get("source_commit"),
                                              created=bundle.manifest.get("created")),
                 "code": C.code_hashes(HERE), "recipe": C.RECIPE_ID, "recipe_hash": C.RECIPE_HASH, "models": models,
                 "budget": {"max_calls": a.max_calls, "max_minutes": max_minutes, "max_usd": a.max_usd},
                 "concurrency": {"max": a.concurrency, "start": (a.concurrency + 1) // 2, "peak": throttle.peak,
                                 "low": throttle.low, "final": throttle.limit, "cuts": throttle.cuts},
                 "calls": t["calls"], "retries": t["retries"], "failed_batches": t["failed_batches"],
                 "segments": t["segments"], "rejected_segments": t["rejected"], "translated": sum(t["units"].values()),
                 "translated_by_tier": t["units"], "translated_by_lang": t["by_lang"],
                 "assembled_from_tm": t["assembled_only"], "findings": t["findings"], "tokens": t["tokens"],
                 "list_price_usd": round(t["usd"], 6),
                 "models_usage": {m: {"calls": v["calls"], "usd": round(v["usd"], 6), "output": v["output"]}
                                  for m, v in t["models"].items()},
                 "profiles": t["profiles"], "remaining": remaining}
    if t["calls"] or sum(t["units"].values()) or t["findings"]:
        tlog.append(run_entry)
        tlog.write_pointer(run_id, bundle.sha256[:12])
        C.write_atomic(repo / C.STATUS_FILE, (json.dumps(build_status(tlog, plan, bundle, state), indent=1,
                                                        sort_keys=True, ensure_ascii=False) + "\n").encode())
        check = C.verify_chain(repo)
        if not check.ok:
            log("Kette nach dem Schreiben ungültig: " + "; ".join(check.errors[:3]))
            return EXIT_DATA
        if a.commit:
            commit(repo, f"live-translation {run_id}: {sum(t['units'].values())} Übersetzungen, {t['findings']} "
                         f"Befunde, {t['calls']} Aufrufe, {t['usd']:.2f} $ Listenpreis")
    prof = ", ".join(f"{p} {n}" for p, n in sorted(t["profiles"].items())) or "-"
    log(f"Ende ({stop}): {sum(t['units'].values())} Übersetzungen "
        + " ".join(f"{k}={v}" for k, v in t["units"].items())
        + f", davon {t['assembled_only']} nur aus dem Speicher, {t['segments']} neue Segmente, {t['rejected']} "
        f"abgelehnt, {t['findings']} Befunde, {t['calls']} Aufrufe (Wiederholungen {t['retries']}), Tokens ein "
        f"{t['tokens']['input']} aus {t['tokens']['output']} Denken {t['tokens']['thinking']}, {t['usd']:.4f} $ "
        f"Listenpreis, Profile {prof}, Parallelität {throttle.low}–{throttle.peak} (Senkungen {throttle.cuts}), "
        f"offen {remaining}")
    return {"exhausted": EXIT_EXHAUSTED, "needs-login": EXIT_LOGIN, "errors": EXIT_ERROR}.get(stop, EXIT_OK)


# ==============================================================================
# Status, Commit, Abschluss
# ==============================================================================

def build_status(tlog: C.TranslationLog, plan: List[Dict[str, Any]], bundle: C.Bundle, state: Optional[Path]) -> Dict[str, Any]:
    decided = C.decided_keys(tlog.entries)
    translated = {e["unit_key"] for e in tlog.entries if e.get("kind") == "translation"}
    by_tier: Dict[str, Dict[str, int]] = {}
    by_lang: Dict[str, Dict[str, int]] = {}
    for u in plan:
        for d, k in ((by_tier, u["tier"]), (by_lang, u["lang"])):
            b = d.setdefault(k, {"planned": 0, "done": 0, "rejected": 0})
            b["planned"] += 1
            b["done"] += 1 if u["key"] in translated else 0
            b["rejected"] += 1 if (u["key"] in decided and u["key"] not in translated) else 0
    total = len(plan)
    done = sum(1 for u in plan if u["key"] in decided)
    runs = [e for e in tlog.entries if e.get("kind") == "run"]
    findings: Dict[str, int] = {}
    for e in tlog.entries:
        if e.get("kind") == "finding":
            c = e["finding"].get("class", "other")
            findings[c] = findings.get(c, 0) + 1
    head = tlog.head
    return {
        "schema": "live-translation-status@v1", "updated": C.utc_now(),
        "chain": {"seq": head["seq"] if head else 0, "hash12": head["hash"][:12] if head else None,
                  "translations": sum(1 for e in tlog.entries if e.get("kind") == "translation"),
                  "tm_entries": sum(1 for e in tlog.entries if e.get("kind") == "tm")},
        "bundle": {"sha12": bundle.sha256[:12], "created": bundle.manifest.get("created"),
                   "source_commit": (bundle.manifest.get("source_commit") or "")[:12]},
        "plan": {"total": total, "done": done, "remaining": total - done,
                 "progress": round(done / total, 4) if total else 1.0, "by_tier": by_tier, "by_lang": by_lang},
        "cost": {"list_price_usd_total": round(sum(float(r.get("list_price_usd") or 0) for r in runs), 4),
                 "runs": len(runs), "currency": "USD, API-Listenpreise"},
        "last_runs": [{k: r.get(k) for k in ("run", "ended", "stop", "calls", "translated", "findings",
                                              "list_price_usd", "profiles", "models_usage")} for r in runs[-10:]],
        "findings": findings, "profiles": LD.profile_state(state),
    }


def commit(repo: Path, message: str) -> bool:
    if not LD.is_git(repo):
        return False
    paths = [p for p in (C.CHAIN_DIR, C.STATUS_FILE) if (repo / p).exists()]
    if not paths:
        return False
    LD.git(repo, "add", "-A", "--", *paths)
    if not LD.git(repo, "diff", "--cached", "--quiet", check=False).returncode:
        return False
    LD.git(repo, "commit", "-q", "-m", message)
    return True


def uncommitted_segments(repo: Path) -> List[Path]:
    if not (Path(repo) / C.LOG_DIR).is_dir() or not LD.is_git(repo):
        return []
    out = LD.git(repo, "status", "--porcelain", "--untracked-files=all", "--", C.LOG_DIR, check=False).stdout
    return [repo / line[3:].strip() for line in out.splitlines() if line[3:].strip().endswith(".jsonl")]


def cmd_finalize(a: argparse.Namespace) -> int:
    repo = Path(a.live_repo)
    for seg in uncommitted_segments(repo):
        cut = C.repair_tail(seg)
        if cut:
            log(f"unvollständige letzte Zeile in {seg.name} entfernt ({cut} Bytes)")
    st = C.verify_chain(repo, check_pointer=False)
    if not st.ok:
        log("Kette ungültig: " + "; ".join(st.errors[:5]))
        return EXIT_DATA
    if st.head and (st.pointer or {}).get("hash") != st.head["hash"]:
        tl = C.TranslationLog(repo, allow_invalid=True)
        runs = [e for e in tl.entries if e.get("kind") == "run"]
        tl.write_pointer(runs[-1]["run"] if runs else "finalize", (st.pointer or {}).get("basis"))
        log("Zeiger auf den Kopf der Kette gesetzt")
    final = C.verify_chain(repo)
    if not final.ok:
        log("Kette ungültig: " + "; ".join(final.errors[:5]))
        return EXIT_DATA
    if a.commit and commit(repo, f"live-translation: Abschluss bei Glied {final.head['seq'] if final.head else 0}"):
        log("Abschluss-Commit erstellt")
    log(f"Kette gültig: {len(final.entries)} Glieder, Kopf {final.head['hash'][:12] if final.head else '-'}")
    return EXIT_OK


def cmd_verify(a: argparse.Namespace) -> int:
    st = C.verify_chain(Path(a.live_repo))
    if not st.ok:
        for err in st.errors[:20]:
            log("Fehler: " + err)
        return EXIT_DATA
    if a.bundle_file:
        b = C.open_bundle(Path(a.bundle_file), Path(tempfile.mkdtemp(prefix="live-tr-verify-")), a.bundle_sha256 or None)
        if not C.contains(st, b.live_head()):
            log("Kette enthält den Kopf des Bündels nicht")
            return EXIT_DATA
    log(f"Kette gültig: {len(st.entries)} Glieder in {len(st.segments)} Segmenten")
    return EXIT_OK


def cmd_status(a: argparse.Namespace) -> int:
    p = Path(a.live_repo) / C.STATUS_FILE
    if not p.exists():
        log("noch kein Status")
        return EXIT_OK
    st = json.loads(p.read_text(encoding="utf-8"))
    pl = st.get("plan", {})
    log(f"Fortschritt {pl.get('done')}/{pl.get('total')} ({100 * float(pl.get('progress') or 0):.1f} %), Kosten gesamt "
        f"{st.get('cost', {}).get('list_price_usd_total')} $ Listenpreis, Läufe {st.get('cost', {}).get('runs')}")
    return EXIT_OK


def cmd_summary(a: argparse.Namespace) -> int:
    """Markdown für $GITHUB_STEP_SUMMARY: nur Zahlen, Kosten zu Listenpreisen, Profil- und Modellnamen."""
    p = Path(a.live_repo) / C.STATUS_FILE
    if not p.exists():
        print("Live-Übersetzung: noch kein Status")
        return EXIT_OK
    st = json.loads(p.read_text(encoding="utf-8"))
    pl, cost = st.get("plan", {}), st.get("cost", {})
    lines = ["### Live-Übersetzung", "",
             f"Fortschritt **{pl.get('done')}/{pl.get('total')}** Einheiten ({100 * float(pl.get('progress') or 0):.1f} %), "
             f"offen {pl.get('remaining')}; Kosten gesamt **{cost.get('list_price_usd_total')} $** "
             f"(API-Listenpreise) in {cost.get('runs')} Läufen.", "",
             "| Stufe | geplant | übersetzt | verworfen |", "|---|---:|---:|---:|"]
    for k, v in (pl.get("by_tier") or {}).items():
        lines.append(f"| {k} | {v.get('planned')} | {v.get('done')} | {v.get('rejected')} |")
    lines += ["", "| Sprache | geplant | übersetzt |", "|---|---:|---:|"]
    for k, v in (pl.get("by_lang") or {}).items():
        lines.append(f"| {k} | {v.get('planned')} | {v.get('done')} |")
    last = (st.get("last_runs") or [])[-1:] or []
    for r in last:
        models = ", ".join(f"{m}: {u.get('calls')} Aufrufe, {u.get('usd')} $" for m, u in (r.get("models_usage") or {}).items())
        profs = ", ".join(f"{p} {n}" for p, n in sorted((r.get("profiles") or {}).items()))
        lines += ["", f"Letzter Lauf `{r.get('run')}` ({r.get('stop')}): {r.get('translated')} Übersetzungen, "
                      f"{r.get('findings')} Befunde, {r.get('calls')} Aufrufe, {r.get('list_price_usd')} $; "
                      f"Modelle {models or '-'}; Profile {profs or '-'}."]
    print("\n".join(lines))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def bundle_args(x: argparse.ArgumentParser) -> None:
        x.add_argument("--bundle-url", default=os.environ.get("LIVE_TR_BUNDLE_URL", ""))
        x.add_argument("--bundle-sha256", default=os.environ.get("LIVE_TR_BUNDLE_SHA256", ""))
        x.add_argument("--bundle-file", default=None)
        x.add_argument("--bundle-cache", default=None)
        x.add_argument("--live-repo", required=True)
        x.add_argument("--work", default=None)
        x.add_argument("--langs", default="", help="nur diese Sprachen (kommagetrennt, leer = alle)")
        x.add_argument("--tiers", default="", help="nur diese Stufen: guide,api,element (leer = alle)")
        x.add_argument("--retry-findings", action="store_true", help="mit Befund geschlossene Einheiten neu versuchen")

    pe = sub.add_parser("pending")
    bundle_args(pe)
    pe.add_argument("--github-output", default=None)
    r = sub.add_parser("run")
    bundle_args(r)
    r.add_argument("--slots", default=None)
    r.add_argument("--switch", default=str(HERE / "agy_switch.py"))
    r.add_argument("--python", default=sys.executable)
    r.add_argument("--state", default=None)
    r.add_argument("--model-guide", default="", help=f"Modell der Modul-/Cluster-Leitfäden (Vorgabe {C.DEFAULT_MODELS['guide']})")
    r.add_argument("--model-text", default="", help=f"Modell der übrigen Texte (Vorgabe {C.DEFAULT_MODELS['element']})")
    r.add_argument("--model", action="append", default=[], help="STUFE=MODELL (guide, api, element)")
    r.add_argument("--effort", default="medium", help="nur für Modell-IDs ohne Stufe im Namen")
    r.add_argument("--max-calls", type=int, default=400)
    r.add_argument("--max-minutes", type=float, default=25.0, help=f"höchstens {MAX_MINUTES_CAP:g}")
    r.add_argument("--max-usd", type=float, default=0.0)
    r.add_argument("--max-failures", type=int, default=6)
    r.add_argument("--concurrency", type=int, default=16)
    r.add_argument("--min-concurrency", type=int, default=2)
    r.add_argument("--call-timeout", type=int, default=480)
    r.add_argument("--max-output-tokens", type=int, default=9000, help="geschätzte Ausgabe je Aufruf")
    r.add_argument("--max-prompt-bytes", type=int, default=90000)
    r.add_argument("--run-id", default=None)
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--no-commit", dest="commit", action="store_false", default=True)
    f = sub.add_parser("finalize")
    f.add_argument("--live-repo", required=True)
    f.add_argument("--commit", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("--live-repo", required=True)
    v.add_argument("--bundle-file", default=None)
    v.add_argument("--bundle-sha256", default=None)
    s = sub.add_parser("status")
    s.add_argument("--live-repo", required=True)
    sm = sub.add_parser("summary", help="Zusammenfassung für $GITHUB_STEP_SUMMARY")
    sm.add_argument("--live-repo", required=True)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    a = build_parser().parse_args(argv)
    fn = {"run": cmd_run, "pending": cmd_pending, "finalize": cmd_finalize, "verify": cmd_verify,
          "status": cmd_status, "summary": cmd_summary}[a.cmd]
    if os.environ.get("LIVE_DEBUG") == "1":
        return fn(a)
    try:
        return fn(a)
    except Exception as exc:       # öffentliches Log: nur Art und Stelle
        tb = exc.__traceback__
        while tb is not None and tb.tb_next is not None:
            tb = tb.tb_next
        where = f"{Path(tb.tb_frame.f_code.co_filename).name}:{tb.tb_lineno}" if tb else "?"
        log(f"unerwarteter Fehler {type(exc).__name__} in {where} (Details lokal mit LIVE_DEBUG=1)")
        return EXIT_ERROR


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, LD._terminate)
    signal.signal(signal.SIGINT, LD._terminate)
    sys.exit(main())
