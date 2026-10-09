#!/usr/bin/env python3
"""Befunde im Format ``finding@v1`` (Fachkonzept Patrouille, §4.1).

Ein Befund beschreibt, was an einem KI-Text falsch ist, mit Beleg, Vorschlag und Quellen. Gleiche Befunde
verschiedener Quellen fallen über die ID zusammen; ihre Konfidenz wird über unabhängige Quellen kombiniert
(c = 1 − Π(1 − cᵢ), §4.4). Kein Modellaufruf, deterministisch.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SCHEMA = "finding@v1"
# distribution-decision: Entscheidung der Live-Verteilung (CONCEPT-0061, Prüfregeln in live_core.py).
SUBJECT_KINDS = ("figure-description", "figure-delta", "element-guide", "module-guide", "spec-record",
                 "distribution-decision")
# Konzept §4.1 plus zwei Belegarten der Wortlisten-Regeln (§4.2): die Liste belegter Verleser und die Textstelle;
# dazu drei Belegarten der Verteilungsregeln: Glied im Entscheidungsprotokoll, Element-Universum des Bündels,
# konsolidierte Zuordnungsmatrix.
EVIDENCE_TYPES = ("pdf-words", "labels", "prep-analysis", "spec-record", "other-version", "image-region",
                  "consumer-context", "known-misreads", "text-passage", "decision-log", "element-universe",
                  "assignment-matrix")
FIX_TYPES = ("replace", "reclassify", "remove-claim", "regenerate")
SOURCE_KINDS = ("validator", "consumer", "patrol", "human")
SEVERITIES = ("hoch", "mittel", "gering")
STATUSES = ("offen", "bestätigt", "behoben-auto", "behoben-mensch", "verworfen", "strittig")


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_claim(claim: str) -> str:
    """Behauptung für die ID: Unicode NFC, Leerraum zusammengefasst, ohne Schlusspunkt, Kleinschreibung."""
    c = unicodedata.normalize("NFC", claim or "")
    c = re.sub(r"\s+", " ", c).strip().rstrip(".").strip()
    return c.casefold()


def finding_id(subject: Dict[str, Any], cls: str, claim: str) -> str:
    key = "|".join((subject.get("kind", ""), subject.get("id", ""), cls, normalize_claim(claim)))
    return "FND-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def combine(confidences: Iterable[float]) -> float:
    """c = 1 − Π(1 − cᵢ)."""
    rest = 1.0
    for c in confidences:
        rest *= 1.0 - max(0.0, min(1.0, float(c)))
    return round(1.0 - rest, 6)


def source(kind: str, name: str, confidence: float, run: str, at: Optional[str] = None,
           model: Optional[str] = None) -> Dict[str, Any]:
    if kind not in SOURCE_KINDS:
        raise ValueError(f"unbekannte Quellenart {kind!r}")
    s = {"kind": kind, "name": name, "run": run, "at": at or now(), "confidence": float(confidence)}
    if model:
        s["model"] = model
    return s


def make(subject: Dict[str, Any], cls: str, claim: str, evidence: List[Dict[str, Any]],
         proposed_fix: Optional[Dict[str, Any]], src: Dict[str, Any], severity: str) -> Dict[str, Any]:
    """Neuen Befund (Status offen) aus einer Quelle anlegen."""
    if subject.get("kind") not in SUBJECT_KINDS:
        raise ValueError(f"unbekannte Gegenstandsart {subject.get('kind')!r}")
    if severity not in SEVERITIES:
        raise ValueError(f"unbekannte Schwere {severity!r}")
    for e in evidence:
        if e.get("type") not in EVIDENCE_TYPES:
            raise ValueError(f"unbekannte Belegart {e.get('type')!r}")
    if proposed_fix is not None and proposed_fix.get("type") not in FIX_TYPES:
        raise ValueError(f"unbekannte Korrekturart {proposed_fix.get('type')!r}")
    return {
        "schema": SCHEMA,
        "id": finding_id(subject, cls, claim),
        "subject": dict(subject),
        "class": cls,
        "claim": claim,
        "evidence": list(evidence),
        "proposed_fix": proposed_fix,
        "sources": [dict(src)],
        "confidence": combine([src["confidence"]]),
        "severity": severity,
        "status": "offen",
        "attempts": 0,
        "history": [{"at": src["at"], "actor": f"{src['kind']}:{src['name']}", "event": "erstellt",
                     "status": "offen"}],
    }


def _ev_key(e: Dict[str, Any]) -> str:
    return json.dumps(e, sort_keys=True, ensure_ascii=False)


def merge_one(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Befund new in old einarbeiten (gleiche ID). Quellen gleicher Art und gleichen Namens zählen einmal (höchste
    Konfidenz, jüngster Lauf); Status, Versuche und Verlauf von old bleiben erhalten."""
    if old["id"] != new["id"]:
        raise ValueError("verschiedene Befunde")
    out = dict(old)
    by: Dict[tuple, Dict[str, Any]] = {}
    for s in list(old.get("sources") or []) + list(new.get("sources") or []):
        k = (s.get("kind"), s.get("name"))
        cur = by.get(k)
        if cur is None:
            by[k] = dict(s)
            continue
        latest = s if str(s.get("at", "")) >= str(cur.get("at", "")) else cur
        by[k] = dict(latest, confidence=max(float(cur["confidence"]), float(s["confidence"])))
    added = [k for k in by if k not in {(s.get("kind"), s.get("name")) for s in old.get("sources") or []}]
    out["sources"] = list(by.values())
    out["confidence"] = combine(s["confidence"] for s in out["sources"])
    seen = {_ev_key(e) for e in old.get("evidence") or []}
    out["evidence"] = list(old.get("evidence") or []) + [e for e in new.get("evidence") or []
                                                         if _ev_key(e) not in seen]
    if not out.get("proposed_fix") and new.get("proposed_fix"):
        out["proposed_fix"] = new["proposed_fix"]
    if SEVERITIES.index(new.get("severity", "gering")) < SEVERITIES.index(out.get("severity", "gering")):
        out["severity"] = new["severity"]
    hist = list(old.get("history") or [])
    for k in added:
        s = by[k]
        hist.append({"at": s.get("at"), "actor": f"{k[0]}:{k[1]}", "event": "quelle", "status": out["status"]})
    out["history"] = hist
    return out


def merge(findings: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Befunde mit gleicher ID zusammenführen; Reihenfolge des ersten Auftretens bleibt."""
    out: Dict[str, Dict[str, Any]] = {}
    for f in findings:
        out[f["id"]] = merge_one(out[f["id"]], f) if f["id"] in out else f
    return list(out.values())


def read(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return out
    for line in p.open(encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def write(path: Path, findings: Iterable[Dict[str, Any]]) -> None:
    """Atomar schreiben (temporäre Datei im Zielverzeichnis, dann os.replace)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for f in findings:
                fh.write(json.dumps(f, ensure_ascii=False, sort_keys=False) + "\n")
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
