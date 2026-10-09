#!/usr/bin/env python3
"""Live-Schicht der Verteilung: Kettenglieder, Datenbündel und Prüfregeln (CONCEPT-0061, CONCEPT-0060).

Dieses Modul ist eigenständig (Standardbibliothek und ``findings.py``) und wird unverändert in das öffentliche
Website-Repo kopiert (``.github/scripts/``, siehe ``live_bundle.py vendor``). Das Bündel trägt den SHA-256 dieser
Datei, von ``live_method.py`` und ``findings.py`` im Manifest; der Online-Job verweigert die Arbeit, wenn seine
Kopien abweichen. So sprechen lokaler Bau, Online-Job und Konsolidierung immer dasselbe Format.

Bestandteile:

* Kanonisches JSON und Hashes (``canonical``, ``obj_hash``).
* Entscheidungsprotokoll als Hash-Kette (``LiveLog``): Segmente ``live/distribution/log/<seq8>.jsonl``, je Lauf ein
  neues Segment, das danach nie mehr verändert wird; ``live/distribution/latest.json`` ist der einzige bewegliche
  Zeiger. Jedes Glied trägt ``seq``, ``parent_hash`` (Hash des vorigen Glieds) und ``hash`` (SHA-256 des kanonischen
  Glieds ohne ``hash``). ``verify_chain`` erkennt veränderte, entfernte, umgestellte und angehängte Glieder.
* Datenbündel (``write_bundle``/``open_bundle``): deterministisches ``tar.gz`` mit fester Mitgliederliste, Manifest mit
  Hashes, sichere Entpackung, Schutz gegen PDFs und Geheimnisse.
* Arbeitseinheiten und Schlüssel (``unit_key``): Eine Einheit ist ein Snippet, eine Schaubild-Reihe oder ein Element
  (Fragment); ihr Schlüssel ist der Hash ihrer Eingaben. Gleicher Schlüssel im Protokoll = erledigt.
* Prüfregeln der Patrouille, Stufe 1 (``validate_decisions``): Befunde ``finding@v1`` zu neuen Entscheidungen.
"""
from __future__ import annotations

import datetime as _dt
import gzip
import hashlib
import io
import json
import os
import re
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

import findings as fnd

# ==============================================================================
# Kanonisches JSON, Hashes
# ==============================================================================


def canonical(obj: Any) -> bytes:
    """Kanonische Bytes: Schlüssel sortiert, ohne Leerraum, UTF-8 ohne Escapes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def obj_hash(obj: Any) -> str:
    return sha256_hex(canonical(obj))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jsonl_lines(rows: Iterable[Dict[str, Any]]) -> bytes:
    """JSONL mit kanonischen Zeilen (deterministisch)."""
    return b"".join(canonical(r) + b"\n" for r in rows)


def read_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


# ==============================================================================
# Methode und Einheiten
# ==============================================================================

# Version der Verteilungsmethode (Prompt, Schema, Kandidaten). Eine Änderung, die Entscheidungen inhaltlich ändert,
# erhöht METHOD_ID; damit werden alle Einheiten neu geplant (neue Schlüssel).
METHOD_ID = "retrieve-effect@1"
METHOD = {
    "id": METHOD_ID,
    "retrieve_k": 20,
    "record_chars": 300,
    "snippet_chars": 4000,
    "reverse_snippet_chars": 900,
    "release_gate": "lenient",
    "auto_cited": True,
    "stage2_k": 8,
    "stage2_max_modules": 3,
}
DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_EFFORT = "low"
UNIT_KINDS = ("snippet", "figure", "element")
KIND_ORDER = {k: i for i, k in enumerate(UNIT_KINDS)}
IDENTITY_DIR = {"snippet": "snippets", "figure": "figures", "element": "elements"}
# Beziehungsarten (CONCEPT-0055 Stufe 4 und die in der Zuordnungsmatrix belegten Werte).
RELATION_TYPES = ("API_IMPLEMENTATION", "EXPLICIT_REFERENCE", "ARCHITECTURAL_CONTEXT", "SEQUENCE_FLOW",
                  "PARAMETER_CONSTRAINT", "EXCEPTION_HANDLING", "CALLER_CONTRACT", "EXPLAINS_RATIONALE")
RELATION_FALLBACK = "UNSPECIFIED"
NO_RELATION = "NONE"


def unit_id(kind: str, ref: str) -> str:
    return f"{kind}:{ref}"


def split_unit(unit: str) -> Tuple[str, str]:
    kind, _, ref = unit.partition(":")
    return kind, ref


def identity(kind: str, ref: str, release: str) -> str:
    """Identität nach CONCEPT-0061 §3.1 für die Verteilung: ``distribution/<kind>s/<ref>@<release>``."""
    return f"distribution/{IDENTITY_DIR[kind]}/{ref}@{release}"


def unit_key(unit: str, inputs: Sequence[Dict[str, Any]], method_id: str = METHOD_ID) -> str:
    """Schlüssel einer Einheit: Hash aus Einheit, Methode und Eingaben (je ``{kind, ref, hash}``)."""
    norm = sorted(({"kind": i["kind"], "ref": i["ref"], "hash": i["hash"]} for i in inputs),
                  key=lambda i: (i["kind"], i["ref"]))
    return obj_hash({"unit": unit, "method": method_id, "inputs": norm})[:32]


# ==============================================================================
# Hash-Kette (Entscheidungsprotokoll)
# ==============================================================================

CHAIN_DIR = "live/distribution"
LOG_DIR = CHAIN_DIR + "/log"
POINTER = CHAIN_DIR + "/latest.json"
STATUS_FILE = "status/distribution.json"
POINTER_SCHEMA = "live-pointer@v1"
ENTRY_SCHEMAS = {"decision": "live-decision@v1", "finding": "live-finding@v1", "run": "live-run@v1"}
REQUIRED = {
    "decision": ("unit", "unit_key", "inputs", "decision", "relation_type", "confidence", "rationale", "model",
                 "profile", "list_price_usd", "run", "at"),
    "finding": ("finding", "run", "at"),
    "run": ("run", "at"),
}
_SEGMENT = re.compile(r"^(\d{8})\.jsonl$")


class ChainError(RuntimeError):
    pass


def entry_hash(entry: Dict[str, Any]) -> str:
    return obj_hash({k: v for k, v in entry.items() if k != "hash"})


def seal(body: Dict[str, Any], parent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Glied aus ``body`` bilden: ``seq``, ``parent_hash``, ``hash``."""
    e = {k: v for k, v in body.items() if k not in ("seq", "parent_hash", "hash")}
    e["seq"] = int(parent["seq"]) + 1 if parent else 1
    e["parent_hash"] = parent["hash"] if parent else None
    e["hash"] = entry_hash(e)
    return e


@dataclass
class ChainState:
    ok: bool
    errors: List[str]
    entries: List[Dict[str, Any]]
    pointer: Optional[Dict[str, Any]]
    segments: List[str]

    @property
    def head(self) -> Optional[Dict[str, Any]]:
        return self.entries[-1] if self.entries else None


def segment_files(root: Path) -> List[Path]:
    d = Path(root) / LOG_DIR
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file() and not p.name.startswith("."))


def verify_chain(root: Path, check_pointer: bool = True) -> ChainState:
    """Liest und prüft die ganze Kette. Fehler: unbekannte Dateien, Segmentnamen, Parse-Fehler, Lücken in ``seq``,
    falscher ``parent_hash``, falscher ``hash``, fehlende Pflichtfelder, Zeiger ungleich Kopf."""
    root = Path(root)
    errors: List[str] = []
    entries: List[Dict[str, Any]] = []
    names: List[str] = []
    prev: Optional[Dict[str, Any]] = None
    for seg in segment_files(root):
        names.append(seg.name)
        m = _SEGMENT.match(seg.name)
        if not m:
            errors.append(f"{seg.name}: unerwartete Datei im Protokoll")
            continue
        first = int(m.group(1))
        expected = (int(prev["seq"]) + 1) if prev else 1
        if first != expected:
            errors.append(f"{seg.name}: Segment beginnt bei {first}, erwartet {expected}")
        raw = seg.read_bytes()
        if not raw:
            errors.append(f"{seg.name}: leeres Segment")
            continue
        if not raw.endswith(b"\n"):
            errors.append(f"{seg.name}: letzte Zeile unvollständig")
        for n, line in enumerate(raw.split(b"\n"), 1):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except ValueError as exc:
                errors.append(f"{seg.name}:{n}: kein JSON ({exc})")
                continue
            loc = f"{seg.name}:{n}"
            if not isinstance(e, dict):
                errors.append(f"{loc}: kein Objekt")
                continue
            kind = e.get("kind")
            if kind not in ENTRY_SCHEMAS or e.get("schema") != ENTRY_SCHEMAS[kind]:
                errors.append(f"{loc}: unbekannte Art/Schema {kind!r}/{e.get('schema')!r}")
            missing = [f for f in REQUIRED.get(kind, ()) if f not in e]
            if missing:
                errors.append(f"{loc}: Pflichtfelder fehlen: {', '.join(missing)}")
            want_seq = (int(prev["seq"]) + 1) if prev else 1
            if e.get("seq") != want_seq:
                errors.append(f"{loc}: seq {e.get('seq')} statt {want_seq}")
            want_parent = prev["hash"] if prev else None
            if e.get("parent_hash") != want_parent:
                errors.append(f"{loc}: parent_hash passt nicht zum vorigen Glied")
            if e.get("hash") != entry_hash(e):
                errors.append(f"{loc}: hash stimmt nicht (Glied verändert)")
            entries.append(e)
            prev = e
    pointer = None
    pp = root / POINTER
    if pp.exists():
        try:
            pointer = json.loads(pp.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"latest.json: kein JSON ({exc})")
    if check_pointer:
        if entries and pointer is None:
            errors.append("latest.json fehlt")
        elif pointer is not None:
            head = entries[-1] if entries else None
            if not head:
                errors.append("latest.json ohne Glieder")
            else:
                if pointer.get("hash") != head["hash"]:
                    errors.append("latest.json zeigt nicht auf den Kopf der Kette")
                if pointer.get("seq") != head["seq"] or pointer.get("head_of") != head["seq"]:
                    errors.append("latest.json: seq/head_of ungleich Kettenlänge")
    return ChainState(not errors, errors, entries, pointer, names)


def contains(state: ChainState, anchor: Optional[Dict[str, Any]]) -> bool:
    """Liegt ein früher gesehener Kopf (``{seq, hash}``) unverändert in der Kette? (erkennt umgeschriebene Historie)"""
    if not anchor or not anchor.get("hash"):
        return True
    seq = int(anchor.get("seq") or 0)
    return 0 < seq <= len(state.entries) and state.entries[seq - 1]["hash"] == anchor["hash"]


class LiveLog:
    """Protokoll in einem Arbeitsbaum von ``autodocs-live``. Lesen prüft die ganze Kette; Schreiben hängt Glieder an
    ein neues Segment dieses Laufs an (Zeile für Zeile, sofort auf die Platte)."""

    def __init__(self, root: Path, allow_invalid: bool = False):
        self.root = Path(root)
        self.state = verify_chain(self.root)
        if not self.state.ok and not allow_invalid:
            raise ChainError("Kette ungültig: " + "; ".join(self.state.errors[:5]))
        self.entries: List[Dict[str, Any]] = list(self.state.entries)
        self._segment: Optional[Path] = None

    @property
    def head(self) -> Optional[Dict[str, Any]]:
        return self.entries[-1] if self.entries else None

    def decisions(self) -> List[Dict[str, Any]]:
        return [e for e in self.entries if e.get("kind") == "decision"]

    def decided_keys(self) -> Set[str]:
        """Schlüssel abgeschlossener Entscheidungen (eine Entscheidung mit fehlgeschlagener Stufe 2 gilt als offen)."""
        return {e["unit_key"] for e in self.decisions() if decision_complete(e)}

    def latest_decisions(self) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for e in self.decisions():
            out[e["unit"]] = e
        return out

    def finding_ids(self) -> Set[str]:
        return {e["finding"]["id"] for e in self.entries if e.get("kind") == "finding"}

    def append(self, body: Dict[str, Any]) -> Dict[str, Any]:
        kind = body.get("kind")
        if kind not in ENTRY_SCHEMAS:
            raise ChainError(f"unbekannte Gliedart {kind!r}")
        body = dict(body, schema=ENTRY_SCHEMAS[kind])
        missing = [f for f in REQUIRED[kind] if f not in body]
        if missing:
            raise ChainError(f"Pflichtfelder fehlen: {', '.join(missing)}")
        e = seal(body, self.head)
        if self._segment is None:
            d = self.root / LOG_DIR
            d.mkdir(parents=True, exist_ok=True)
            self._segment = d / f"{e['seq']:08d}.jsonl"
            if self._segment.exists():
                raise ChainError(f"Segment {self._segment.name} existiert bereits")
        line = canonical(e) + b"\n"
        with open(self._segment, "ab") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        self.entries.append(e)
        return e

    def write_pointer(self, run: str, basis: Optional[str] = None) -> Optional[Dict[str, Any]]:
        head = self.head
        if head is None:
            return None
        seg = self._segment.name if self._segment else (self.state.segments[-1] if self.state.segments else "")
        ptr = {"schema": POINTER_SCHEMA, "chain": "distribution", "hash": head["hash"], "hash12": head["hash"][:12],
               "seq": head["seq"], "head_of": head["seq"], "segment": f"log/{seg}", "at": head["at"],
               "reason": {"kind": "distribution", "ref": run}, "basis": basis}
        write_atomic(self.root / POINTER, (json.dumps(ptr, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode())
        return ptr


def decision_complete(e: Dict[str, Any]) -> bool:
    """Eine Entscheidung, deren Stufe 2 fehlschlug oder am Budget scheiterte, gilt als offen (wird neu geplant)."""
    st2 = (e.get("decision") or {}).get("stage2") or {}
    return st2.get("status") not in ("failed", "deferred")


def repair_tail(root: Path, segment: Path) -> int:
    """Unvollständige letzte Zeile eines (noch nicht übertragenen) Segments abschneiden. Rückgabe: entfernte Bytes."""
    raw = segment.read_bytes()
    if not raw or raw.endswith(b"\n"):
        return 0
    cut = raw.rfind(b"\n") + 1
    if cut == 0:
        segment.unlink()
        return len(raw)
    with open(segment, "r+b") as fh:
        fh.truncate(cut)
    return len(raw) - cut


def write_atomic(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


# ==============================================================================
# Datenbündel
# ==============================================================================

BUNDLE_SCHEMA = "live-bundle@v1"
BUNDLE_MEMBERS = ("manifest.json", "corpus.jsonl", "elements.jsonl", "snippets.jsonl", "figure_texts.jsonl",
                  "assignment_matrix.jsonl", "plan.jsonl", "live_head.json")
CODE_FILES = ("live_core.py", "live_method.py", "findings.py")
# Was nie in ein Bündel darf: PDFs und Zugangsdaten.
_FORBIDDEN = [(re.compile(rb"%PDF-\d"), "PDF-Inhalt"), (re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "privater Schlüssel"),
              (re.compile(rb"\"refresh_token\"\s*:"), "OAuth-Token"), (re.compile(rb"antigravity-oauth-token"), "agy-Token"),
              (re.compile(rb"\bghp_[A-Za-z0-9]{36}\b"), "GitHub-Token"), (re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}"), "GitHub-Token"),
              (re.compile(rb"\bAKIA[0-9A-Z]{16}\b"), "AWS-Schlüssel"), (re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "Slack-Token")]


class BundleError(RuntimeError):
    pass


def code_hashes(directory: Path) -> Dict[str, str]:
    d = Path(directory)
    return {name: file_sha256(d / name) for name in CODE_FILES if (d / name).exists()}


def scan_forbidden(name: str, data: bytes) -> None:
    for rx, what in _FORBIDDEN:
        m = rx.search(data)
        if m:
            raise BundleError(f"{name}: {what} gefunden (Offset {m.start()}); Bündel verweigert")


def write_bundle(out: Path, files: Dict[str, bytes], manifest: Dict[str, Any], mtime: int = 0) -> Dict[str, Any]:
    """Deterministisches ``tar.gz``: feste Reihenfolge (``BUNDLE_MEMBERS``), feste Zeit, Eigentümer 0, Modus 0644,
    gzip ohne Namen und Zeit. Das Manifest erhält Hash, Größe und Zeilenzahl je Datei. Rückgabe: Kennzahlen."""
    unknown = sorted(set(files) - set(BUNDLE_MEMBERS))
    if unknown:
        raise BundleError(f"nicht vorgesehene Bündel-Dateien: {', '.join(unknown)}")
    missing = [n for n in BUNDLE_MEMBERS if n != "manifest.json" and n not in files]
    if missing:
        raise BundleError(f"Bündel unvollständig: {', '.join(missing)}")
    man = dict(manifest)
    man["schema"] = BUNDLE_SCHEMA
    man["files"] = {}
    for name in BUNDLE_MEMBERS[1:]:
        data = files[name]
        scan_forbidden(name, data)
        man["files"][name] = {"sha256": sha256_hex(data), "bytes": len(data), "lines": data.count(b"\n")}
    man_bytes = (json.dumps(man, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    scan_forbidden("manifest.json", man_bytes)
    payload = dict(files, **{"manifest.json": man_bytes})
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name in BUNDLE_MEMBERS:
            data = payload[name]
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            ti.mtime = int(mtime)
            ti.mode = 0o644
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = ""
            ti.type = tarfile.REGTYPE
            tar.addfile(ti, io.BytesIO(data))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name("." + out.name + ".tmp")
    with open(tmp, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
            gz.write(buf.getvalue())
    os.replace(tmp, out)
    return {"path": str(out), "sha256": file_sha256(out), "bytes": out.stat().st_size,
            "raw_bytes": sum(len(v) for v in payload.values()), "manifest": man,
            "manifest_hash": sha256_hex(man_bytes)}


@dataclass
class Bundle:
    directory: Path
    manifest: Dict[str, Any]
    sha256: str = ""
    _cache: Dict[str, Any] = field(default_factory=dict)

    def path(self, name: str) -> Path:
        return self.directory / name

    def rows(self, name: str) -> Iterator[Dict[str, Any]]:
        return read_jsonl(self.path(name))

    @property
    def manifest_hash(self) -> str:
        return file_sha256(self.path("manifest.json"))

    def live_head(self) -> Optional[Dict[str, Any]]:
        data = json.loads(self.path("live_head.json").read_text(encoding="utf-8"))
        return data or None


def open_bundle(archive: Path, dest: Path, expected_sha256: Optional[str] = None) -> Bundle:
    """Bündel prüfen und entpacken: SHA-256 des Archivs (falls angegeben), nur vorgesehene, flache Namen, reguläre
    Dateien, danach die Hashes aus dem Manifest."""
    archive = Path(archive)
    digest = file_sha256(archive)
    if expected_sha256 and digest != expected_sha256.strip().lower():
        raise BundleError(f"SHA-256 des Bündels {digest[:12]}… ungleich erwartetem {expected_sha256[:12]}…")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    seen: Set[str] = set()
    with tarfile.open(archive, mode="r:gz") as tar:
        for ti in tar.getmembers():
            if ti.name not in BUNDLE_MEMBERS or "/" in ti.name or ti.name.startswith("."):
                raise BundleError(f"unerwartetes Mitglied {ti.name!r}")
            if not ti.isreg():
                raise BundleError(f"Mitglied {ti.name!r} ist keine reguläre Datei")
            if ti.name in seen:
                raise BundleError(f"Mitglied {ti.name!r} doppelt")
            seen.add(ti.name)
            fh = tar.extractfile(ti)
            write_atomic(dest / ti.name, fh.read() if fh else b"")
    missing = [n for n in BUNDLE_MEMBERS if n not in seen]
    if missing:
        raise BundleError(f"Bündel unvollständig: {', '.join(missing)}")
    man = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    if man.get("schema") != BUNDLE_SCHEMA:
        raise BundleError(f"unbekanntes Bündelschema {man.get('schema')!r}")
    for name, meta in (man.get("files") or {}).items():
        if file_sha256(dest / name) != meta.get("sha256"):
            raise BundleError(f"{name}: Hash weicht vom Manifest ab")
    return Bundle(dest, man, digest)


# ==============================================================================
# Prüfregeln der Patrouille, Stufe 1 (über Entscheidungen der Verteilung)
# ==============================================================================

DIST_RULES = {
    # Klasse: (Schwere, Startkonfidenz)
    "dist-unknown-target": ("hoch", 0.95),
    "dist-release-mismatch": ("gering", 0.6),
    "dist-duplicate-decision": ("mittel", 0.9),
    "dist-contradiction": ("gering", 0.5),
    "dist-relation-conflict": ("gering", 0.5),
    "dist-effect-inconsistent": ("gering", 0.6),
}
BLOCKING_SEVERITIES = ("hoch", "mittel")
ACCEPT_CONFIDENCE = 0.70          # wie der Gatekeeper: darunter auto_dismissed


def _first_bit(mask: int) -> int:
    return (mask & -mask).bit_length() - 1 if mask else -1


def release_conflict(unit_mask: int, element_mask: int, all_mask: int) -> bool:
    """Milde Release-Regel des Runners: unvereinbar, wenn das Element vor dem frühesten Release der Einheit endet."""
    if not unit_mask or not element_mask or unit_mask == all_mask or element_mask == all_mask:
        return False
    return element_mask.bit_length() - 1 < _first_bit(unit_mask)


@dataclass
class Universe:
    """Was die Prüfregeln über Einheiten und Elemente wissen müssen."""
    elements: Dict[str, Dict[str, Any]]          # id -> {m, k, mask}
    items: Dict[str, Dict[str, Any]]             # snippet/figure id -> {mask, mod}
    all_mask: int = (1 << 64) - 1
    matrix_strong: Dict[Tuple[str, str], str] = field(default_factory=dict)   # (target, snippet) -> relation (>= 0.95)


def _subject(e: Dict[str, Any]) -> Dict[str, Any]:
    return {"kind": "distribution-decision", "id": e["unit"]}


def _ev(e: Dict[str, Any], excerpt: str) -> Dict[str, Any]:
    return {"type": "decision-log", "ref": f"{e['unit']}@{e['hash'][:12]}", "excerpt": excerpt[:300]}


def _mk(cls: str, e: Dict[str, Any], claim: str, evidence: List[Dict[str, Any]], run: str, at: str,
        fix: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    sev, conf = DIST_RULES[cls]
    return fnd.make(_subject(e), cls, claim, evidence, fix, fnd.source("validator", cls, conf, run, at), sev)


def _pairs(e: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list((e.get("decision") or {}).get("assignments") or [])


def validate_decisions(new: List[Dict[str, Any]], latest: Dict[str, Dict[str, Any]], uni: Universe, run: str,
                       at: Optional[str] = None, all_decisions: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Befunde zu den neuen Entscheidungen ``new``. ``latest``: neueste Entscheidung je Einheit (inklusive ``new``),
    ``all_decisions``: alle Entscheidungen der Kette (für doppelte Schlüssel). Deterministisch, ohne Modell."""
    at = at or utc_now()
    out: List[Dict[str, Any]] = []
    by_key: Dict[str, List[Dict[str, Any]]] = {}
    for e in all_decisions or []:
        by_key.setdefault(e["unit_key"], []).append(e)
    # Paarsicht der aktuellen Entscheidungen beider Richtungen
    pair_pos: Dict[Tuple[str, str], List[Tuple[Dict[str, Any], Dict[str, Any]]]] = {}
    seen_cands: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for e in latest.values():
        for a in _pairs(e):
            pair_pos.setdefault((a["target_element"], a["snippet_id"]), []).append((e, a))
        kind, ref = split_unit(e["unit"])
        for c in (e.get("decision") or {}).get("candidates") or []:
            key = (ref, c) if kind == "element" else (c, ref)
            seen_cands[key] = e
    for e in new:
        kind, ref = split_unit(e["unit"])
        dec = e.get("decision") or {}
        # 1. Ziel oder Snippet existiert nicht
        for a in _pairs(e):
            tgt, sid = a["target_element"], a["snippet_id"]
            if tgt not in uni.elements:
                out.append(_mk("dist-unknown-target", e, f"Zuordnung an `{tgt}`, das im Element-Universum fehlt.",
                               [_ev(e, f"{sid} -> {tgt} ({a.get('relation_type')}, {a.get('confidence')})"),
                                {"type": "element-universe", "ref": "elements.jsonl", "excerpt": f"{tgt} fehlt"}],
                               run, at, {"type": "remove-claim", "patch": {"old": tgt, "new": ""}}))
            if sid not in uni.items:
                out.append(_mk("dist-unknown-target", e, f"Zuordnung des unbekannten Snippets `{sid}`.",
                               [_ev(e, f"{sid} -> {tgt}"), {"type": "element-universe", "ref": "snippets.jsonl",
                                                            "excerpt": f"{sid} fehlt"}], run, at,
                               {"type": "remove-claim", "patch": {"old": sid, "new": ""}}))
            # 2. Release-Schnitt
            el, it = uni.elements.get(tgt), uni.items.get(sid)
            if el and it and release_conflict(int(it.get("mask") or 0), int(el.get("mask") or 0), uni.all_mask):
                out.append(_mk("dist-release-mismatch", e,
                               f"`{sid}` -> `{tgt}`: das Element endet vor dem frühesten Release des Snippets.",
                               [_ev(e, f"{sid} -> {tgt} ({a.get('source')}, {a.get('confidence')})"),
                                {"type": "element-universe", "ref": "elements.jsonl",
                                 "excerpt": f"mask element 0x{int(el.get('mask') or 0):X}, snippet 0x{int(it.get('mask') or 0):X}"}],
                               run, at))
        # 3. Doppelte Entscheidung mit gleichem Schlüssel und anderem Inhalt
        same = [d for d in by_key.get(e["unit_key"], []) if d["hash"] != e["hash"]]
        for d in same:
            if obj_hash(_decision_core(d)) != obj_hash(_decision_core(e)):
                out.append(_mk("dist-duplicate-decision", e,
                               f"Zwei Entscheidungen mit gleichem Schlüssel {e['unit_key'][:12]} widersprechen sich.",
                               [_ev(e, "neu"), _ev(d, "früher")], run, at))
                break
        # 4. Widerspruch der Richtungen und Beziehungsart
        for a in _pairs(e):
            pair = (a["target_element"], a["snippet_id"])
            if float(a.get("confidence") or 0) < 0.85:
                continue
            other = seen_cands.get(pair)
            if other is not None and other["unit"] != e["unit"] and not any(
                    (b["target_element"], b["snippet_id"]) == pair for b in _pairs(other)):
                out.append(_mk("dist-contradiction", e,
                               f"`{pair[1]}` -> `{pair[0]}` zugeordnet, die Gegenrichtung ({other['unit']}) sah das Paar "
                               "als Kandidaten und ordnete es nicht zu.",
                               [_ev(e, f"{a.get('relation_type')} {a.get('confidence')}"), _ev(other, "nicht zugeordnet")],
                               run, at))
            for oe, ob in pair_pos.get(pair, []):
                if oe["unit"] != e["unit"] and float(ob.get("confidence") or 0) >= 0.85 and \
                        ob.get("relation_type") != a.get("relation_type"):
                    out.append(_mk("dist-relation-conflict", e,
                                   f"`{pair[1]}` -> `{pair[0]}`: Beziehungsart {a.get('relation_type')} gegen "
                                   f"{ob.get('relation_type')} aus {oe['unit']}.",
                                   [_ev(e, str(a.get("relation_type"))), _ev(oe, str(ob.get("relation_type")))], run, at))
                    break
        # Konsolidierter Bestand: starke Zuordnungen (>= 0.95), die das Modell als Kandidaten sah und nicht zuordnete
        # (ein Befund je Entscheidung, Ziele sortiert, damit die Befund-ID über Läufe stabil bleibt)
        if kind in ("snippet", "figure"):
            assigned = {b["target_element"] for b in _pairs(e)}
            lost = sorted(c for c in dict.fromkeys(dec.get("candidates") or [])
                          if uni.matrix_strong.get((c, ref)) and c not in assigned)
            if lost:
                shown = ", ".join(f"`{c}`" for c in lost[:5]) + (f" und {len(lost) - 5} weitere" if len(lost) > 5 else "")
                out.append(_mk("dist-contradiction", e,
                               f"Im Bestand stark zugeordnet (>= 0,95), hier trotz Kandidatur nicht zugeordnet: {shown}.",
                               [_ev(e, "nicht zugeordnet")] + [
                                   {"type": "assignment-matrix", "ref": "assignment_matrix.jsonl",
                                    "excerpt": f"{ref} -> {c} {uni.matrix_strong[(c, ref)]}"} for c in lost[:5]],
                               run, at))
        # 5. Außenwirkung und Module passen nicht zusammen
        own = (uni.items.get(ref) or {}).get("mod") if kind != "element" else (uni.elements.get(ref) or {}).get("m")
        ext = bool(dec.get("external_effect"))
        mods = [m for m in dec.get("modules") or [] if m]
        foreign = sorted({(uni.elements.get(b["target_element"]) or {}).get("m") or "" for b in _pairs(e)
                          if float(b.get("confidence") or 0) >= 0.85} - {"", str(own or "")}, key=str.lower)
        if ext and not mods:
            out.append(_mk("dist-effect-inconsistent", e, "Außenwirkung ohne betroffene Module.",
                           [_ev(e, str(dec.get("effect_rationale") or ""))], run, at))
        elif kind != "element" and not ext and own and own.lower() != "figure" and len(foreign) >= 2:
            out.append(_mk("dist-effect-inconsistent", e,
                           f"Keine Außenwirkung, aber starke Zuordnungen an andere Module ({', '.join(foreign[:4])}).",
                           [_ev(e, str(dec.get("effect_rationale") or ""))], run, at))
    return fnd.merge(out)


def _decision_core(e: Dict[str, Any]) -> Dict[str, Any]:
    d = e.get("decision") or {}
    return {"external_effect": d.get("external_effect"), "modules": sorted(d.get("modules") or []),
            "pairs": sorted((a["target_element"], a["snippet_id"], a.get("relation_type")) for a in d.get("assignments") or [])}


# Bekannte Verleser (figure_identifiers.KNOWN_MISREADS); test_live_distribution prüft die Gleichheit.
KNOWN_MISREADS = (("Retum", "Return"), ("retum", "return"), ("Pattem", "Pattern"), ("pattem", "pattern"))
_KNOWN_RE = re.compile("|".join(f"{a}(?=[A-Z_0-9]|s?$|ed|ing)" for a, _ in KNOWN_MISREADS))
_IDENT = re.compile(r"(?<![\w])(?:[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+|[A-Za-z][a-z0-9]*[A-Z][A-Za-z0-9]*)(?![\w])")
_MIN_LEN = 6


def figure_text_findings(figure_id: str, text: str, run: str, at: Optional[str] = None) -> List[Dict[str, Any]]:
    """Regel ``identifier-misread`` der Bildprüfung (figure_validators) ohne PDF-Wörter: belegte Verleser in der
    Beschreibung einer Schaubild-Reihe. Gleiche Befund-IDs wie der lokale Lauf (gleicher Gegenstand und Satz)."""
    import collections
    at = at or utc_now()
    out = []
    known = dict(KNOWN_MISREADS)
    counts = collections.Counter(m.group(0) for m in _IDENT.finditer((text or "").replace("\\n", " ")))
    for tok, n in sorted(counts.items()):
        if len(tok) < _MIN_LEN:
            continue
        fixed = _KNOWN_RE.sub(lambda k: known[k.group(0)], tok)
        if fixed == tok:
            continue
        ev = [{"type": "known-misreads", "ref": "figure_identifiers.KNOWN_MISREADS",
               "excerpt": ", ".join(f"{a}→{b}" for a, b in KNOWN_MISREADS)}]
        out.append(fnd.make({"kind": "figure-description", "id": figure_id}, "identifier-misread",
                            f"`{tok}` ist eine Ableseverwechslung von `{fixed}`.", ev,
                            {"type": "replace", "patch": {"old": tok, "new": fixed, "count": n}},
                            fnd.source("validator", "identifier-misread", 0.95, run, at), "mittel"))
    return out
