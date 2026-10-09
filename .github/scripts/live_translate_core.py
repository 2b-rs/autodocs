#!/usr/bin/env python3
"""Übersetzung in der Live-Schicht (CONCEPT-0061 §15): KI-Fragmente der Website inkrementell in die zehn Zielsprachen.

Eigenständig (Standardbibliothek und ``findings.py``) und unverändert in das öffentliche Website-Repo kopiert
(``live_translate_bundle.py vendor``). Das Übersetzungsbündel trägt den SHA-256 dieser Datei und von ``findings.py``
im Manifest; der Online-Job verweigert die Arbeit, wenn seine Kopien abweichen (INV-LIVE-09). ``live_core.py`` und
``live_method.py`` der Verteilung bleiben unberührt, damit deren gepinntes Bündel gültig bleibt.

Bestandteile:

* **Segmentierung** wie ``_src/lib_i18n.py`` ohne lxml: Blattsegmente (``p``, ``li``, ``h3``–``h6``, ``td``, ``th`` …
  ohne Block-Nachfahren), Maskierung geschützter Inline-Elemente (``a``, ``code``, ``span``, ``svg``, ``br``, ``img``)
  durch ``⟦k⟧``, Segmentschlüssel ``sha1(maskierter Text)[:12]``. Gleicher Schlüssel wie im Übersetzungsspeicher
  ``_src/i18n/segments.de.json`` / ``_src/i18n/<lang>/segments.json``. Ergänzung: **Laufsegmente** für Text in
  Nicht-Blatt-Blöcken (``li`` mit Unterliste u. ä.), damit kein deutscher Text übrig bleibt.
* **Wiederaufbau** positionsgetreu: nur die Innenbereiche der Segmente werden ersetzt, alles andere (Diagramme, SVG,
  Attribute, Verweise) bleibt byte-gleich; Platzhalter werden durch die Originalbytes ersetzt.
* **Rezept** ``translate-segments@1``: deterministischer Prompt, Antwortschema, Prüfung je Segment (Platzhalter,
  Markup, Kennungen, geschützte Tokens, deutscher Rest, Längenverhältnis) und je Fragment (Gerüst, Invarianten).
* **Einheiten**: eine je (Fragment, Zielsprache), Schlüssel aus Quell-Hash, Rezept, geschützten Begriffen und Glossar.
* **Kette** ``live/translation`` (Glieder ``translation``, ``tm``, ``finding``, ``run``) und **Bündel**.
"""
from __future__ import annotations

import datetime as _dt
import gzip
import hashlib
import html as _html
import io
import json
import math
import os
import re
import tarfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

import findings as fnd

# ==============================================================================
# Kanonisches JSON, Hashes (gleiche Definition wie live_core)
# ==============================================================================


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def obj_hash(obj: Any) -> str:
    return sha256_hex(canonical(obj))


def text_sha256(text: str) -> str:
    return sha256_hex(text.encode("utf-8"))


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def jsonl_lines(rows: Iterable[Dict[str, Any]]) -> bytes:
    return b"".join(canonical(r) + b"\n" for r in rows)


def read_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


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
# Sprachen, Stufen, Modelle, Preise
# ==============================================================================

LANGS = ("en", "es", "pt", "fr", "ru", "ar", "hi", "ko", "zh", "nl")          # Reihenfolge wie site.json
LANG_RANK = {l: i for i, l in enumerate(LANGS)}
LANG_NAMES = {"en": "English", "es": "Spanish (español)", "pt": "Portuguese (português)", "fr": "French (français)",
              "ru": "Russian (русский)", "ar": "Arabic (العربية)", "hi": "Hindi (हिन्दी)", "ko": "Korean (한국어)",
              "zh": "Simplified Chinese (简体中文)", "nl": "Dutch (Nederlands)"}
# Stufen der Reihenfolge: Leitfäden (Module, Cluster), API-Leitfäden (Namespaces, Klassen, Services), Elemente.
TIERS = ("guide", "api", "element")
TIER_RANK = {t: i for i, t in enumerate(TIERS)}
# Vorgabe nach dem ersten vollen Lauf (Lauf 37940217154): Flash „medium“ dachte im Mittel 13.037 Tokens je Aufruf
# (73 % der Ausgabe); „low“ denkt praktisch nicht (Verteilung und Schaubild-Arbeit: 0 Denk-Tokens).
DEFAULT_MODELS = {"guide": "gemini-3.8-flash-low", "api": "gemini-3.8-flash-low", "element": "gemini-3.8-flash-low"}
EFFORT_SUFFIXES = ("-low", "-medium", "-high", "-max")
# USD je 1 Mio. Tokens (Eingabe, gecachte Eingabe, Ausgabe; Denk-Tokens wie Ausgabe).
# gemini-3.8-flash: ai.google.dev/gemini-api/docs/pricing, geprüft 2026-10-09, gültig bis 2026-12-31.
# gemini-3.1-pro: Preisliste der Agentensteuerung (prices.json, abgerufen 2026-09-15 von derselben Seite,
# "preview pricing", Kontext < 200k); heute nicht erneut geprüft.
PRICES = {"gemini-3.8-flash": (0.75, 0.075, 3.75), "gemini-3.1-pro": (2.00, 0.20, 12.00)}


def model_base(model: str) -> str:
    for suf in EFFORT_SUFFIXES:
        if model.endswith(suf):
            return model[: -len(suf)]
    return model


def model_effort(model: str, default: str = "") -> str:
    for suf in EFFORT_SUFFIXES:
        if model.endswith(suf):
            return suf[1:]
    return default


def price_for(model: str) -> Tuple[float, float, float]:
    base = model_base(model)
    if base in PRICES:
        return PRICES[base]
    return PRICES["gemini-3.1-pro"] if "pro" in base else PRICES["gemini-3.8-flash"]


# agy meldet ``output_tokens`` einschließlich der Denk-Tokens: in allen 400 gespeicherten Transkripten gilt
# total_tokens = input_tokens + output_tokens, und in allen 2.074 Aufrufen des ersten vollen Laufs ist
# thinking_tokens ≤ output_tokens. Denk-Tokens werden deshalb nicht noch einmal addiert (bis Preisbasis 1 geschah das).
PRICE_BASIS = "output-includes-thinking@2"


def list_price(model: str, tok: Dict[str, int]) -> float:
    pin, pcached, pout = price_for(model)
    return (tok.get("input", 0) * pin + tok.get("cached", 0) * pcached + tok.get("output", 0) * pout) / 1e6


def legacy_overcharge(model: str, tok: Dict[str, int]) -> float:
    """Zu viel berechneter Betrag nach Preisbasis 1 (Denk-Tokens doppelt): für die Korrektur alter Laufglieder."""
    return tok.get("thinking", 0) * price_for(model)[2] / 1e6


def usage_tokens(usage: Dict[str, Any]) -> Dict[str, int]:
    def g(k: str) -> int:
        v = (usage or {}).get(k)
        return int(v) if isinstance(v, (int, float)) else 0
    return {"input": g("input_tokens"), "cached": g("cache_read_tokens"), "output": g("output_tokens"),
            "thinking": g("thinking_tokens")}


ALLOWED_TOOLS = {"finish"}


def parse_agy_stream(text: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, int], List[str]]:
    """Ergebnis-Ereignis, Schritte je Art und verbotene Werkzeugaufrufe (wie live_method.parse_agy_stream)."""
    result: Optional[Dict[str, Any]] = None
    steps: Dict[str, int] = {}
    seen: Set[Any] = set()
    bad: List[str] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("event") == "result" and isinstance(ev.get("result"), dict):
            result = ev["result"]
        elif ev.get("event") == "step_update":
            su = ev.get("step_update") or {}
            key = su.get("step_index")
            if key is None:
                key = f"_{len(seen)}"
            if key in seen:
                continue
            seen.add(key)
            st = str(su.get("step_type") or "unknown")
            steps[st] = steps.get(st, 0) + 1
            tool = su.get("tool_name")
            if tool and str(tool) not in ALLOWED_TOOLS:
                bad.append(str(tool))
        elif not ev.get("event") and isinstance(ev.get("structured_output"), dict):
            result = ev
    if "auto-denied" in (text or "") or "cannot prompt for" in (text or ""):
        bad.append("denied")
    return result, steps, bad


# ==============================================================================
# HTML: Zerlegung und Baum (Verhalten des HTML-Parsers von libxml2/lxml, soweit die Fragmente es brauchen)
# ==============================================================================

VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
                  "track", "wbr"))
# wie lib_i18n
PROTECT = frozenset(("a", "code", "svg", "br", "span", "img"))
BLOCKTAGS = frozenset(("p", "li", "h3", "h4", "h5", "h6", "figcaption", "dt", "dd", "caption"))
ZELLTAGS = frozenset(("td", "th"))
SEG_TAGS = BLOCKTAGS | ZELLTAGS
# Inline-Markup, das als Markup im Segmenttext bleibt (Laufsegmente; in Blattsegmenten bleibt jedes nicht geschützte
# Kind Markup, wie in lib_i18n.maskiere)
INLINE = frozenset(("em", "strong", "b", "i", "u", "s", "sub", "sup", "var", "small", "mark", "abbr", "q", "cite",
                    "dfn", "kbd", "samp", "tt", "del", "ins", "time", "bdi", "bdo", "wbr", "font"))
_P_CLOSERS = frozenset(("address", "article", "aside", "blockquote", "details", "div", "dl", "dd", "dt", "fieldset",
                        "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header",
                        "hr", "li", "main", "menu", "nav", "ol", "p", "pre", "section", "table", "ul"))
_P_SCOPE = frozenset(("td", "th", "table", "caption", "li", "dd", "dt", "div", "blockquote", "section", "article",
                      "aside", "ul", "ol", "dl", "figure", "button", "object", "template"))

_TOKEN = re.compile(r"<!--.*?(?:-->|\Z)|<![^>]*>?|<\?[^>]*>?|</?[A-Za-z](?:\"[^\"]*\"|'[^']*'|[^'\">])*>|[^<]+|<",
                    re.S)
_TAGNAME = re.compile(r"</?([A-Za-z][^\s/>]*)")
_ATTR = re.compile(r"""([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?""")


class Node:
    __slots__ = ("kind", "tag", "attrs", "s", "cs", "ce", "e", "kids", "parent", "has_seg")

    def __init__(self, kind: str, tag: str = "", attrs: Optional[List[Tuple[str, Optional[str]]]] = None,
                 s: int = 0, e: int = 0):
        self.kind = kind            # root | el | text | comment
        self.tag = tag
        self.attrs = attrs or []
        self.s, self.cs, self.ce, self.e = s, e, e, e
        self.kids: List["Node"] = []
        self.parent: Optional["Node"] = None
        self.has_seg = False        # enthält ein Element aus SEG_TAGS als Nachfahren

    def cls(self) -> str:
        for k, v in self.attrs:
            if k == "class":
                return v or ""
        return ""

    def iter(self) -> Iterator["Node"]:
        stack = [self]
        while stack:
            n = stack.pop()
            yield n
            stack.extend(reversed(n.kids))


def _attrs(tok: str, name_len: int) -> List[Tuple[str, Optional[str]]]:
    body = tok[1 + name_len:-1]
    if body.endswith("/"):
        body = body[:-1]
    out: List[Tuple[str, Optional[str]]] = []
    seen: Set[str] = set()
    for m in _ATTR.finditer(body):
        name = m.group(1).lower()
        if name in seen:
            continue
        seen.add(name)
        raw = next((g for g in (m.group(2), m.group(3), m.group(4)) if g is not None), None)
        out.append((name, _html.unescape(raw) if raw is not None else None))
    return out


def _close(stack: List[Node], i: int, pos: int) -> None:
    for n in stack[i:]:
        n.ce = n.e = pos
    del stack[i:]


def _implicit_close(stack: List[Node], name: str, pos: int) -> None:
    if any(n.tag == "svg" for n in stack):          # Fremdinhalt: keine HTML-Regeln
        return

    def find(targets, scope) -> int:
        for i in range(len(stack) - 1, 0, -1):
            t = stack[i].tag
            if t in targets:
                return i
            if t in scope:
                return -1
        return -1

    if name in _P_CLOSERS:
        i = find(("p",), _P_SCOPE)
        if i > 0:
            _close(stack, i, pos)
    if name == "li":
        i = find(("li",), ("ul", "ol", "menu", "table", "div", "td", "th"))
        if i > 0:
            _close(stack, i, pos)
    elif name in ("dt", "dd"):
        i = find(("dt", "dd"), ("dl", "table", "div"))
        if i > 0:
            _close(stack, i, pos)
    elif name in ("td", "th"):
        i = find(("td", "th"), ("tr", "table"))
        if i > 0:
            _close(stack, i, pos)
    elif name == "tr":
        i = find(("tr",), ("table", "thead", "tbody", "tfoot"))
        if i > 0:
            _close(stack, i, pos)
    elif name in ("thead", "tbody", "tfoot"):
        i = find(("thead", "tbody", "tfoot"), ("table",))
        if i > 0:
            _close(stack, i, pos)


def parse_html(src: str) -> Node:
    """Baum mit Quellpositionen (Starttag s..cs, Inhalt cs..ce, Endtag ce..e)."""
    root = Node("root", "#root", [], 0, 0)
    root.cs, root.ce, root.e = 0, len(src), len(src)
    stack = [root]
    for m in _TOKEN.finditer(src):
        tok = m.group(0)
        s, e = m.span()
        if tok.startswith("<!") or tok.startswith("<?"):
            n = Node("comment", "", None, s, e)
        elif tok.startswith("</") and len(tok) > 2 and tok[2].isalpha():
            name = _TAGNAME.match(tok).group(1).lower()
            for i in range(len(stack) - 1, 0, -1):
                if stack[i].tag == name:
                    for x in stack[i + 1:]:
                        x.ce = x.e = s
                    stack[i].ce, stack[i].e = s, e
                    del stack[i:]
                    break
            continue
        elif tok.startswith("<") and len(tok) > 1 and tok[1].isalpha():
            name = _TAGNAME.match(tok).group(1)
            attrs = _attrs(tok, len(name))
            name = name.lower()
            _implicit_close(stack, name, s)
            n = Node("el", name, attrs, s, e)
            n.parent = stack[-1]
            stack[-1].kids.append(n)
            if name not in VOID and not tok.endswith("/>"):
                stack.append(n)
            continue
        else:
            n = Node("text", "", None, s, e)
        n.parent = stack[-1]
        stack[-1].kids.append(n)
    _close(stack, 1, len(src))

    def mark(n: Node) -> bool:
        flag = False
        for k in n.kids:
            if k.kind == "el":
                sub = mark(k)
                flag = flag or sub or k.tag in SEG_TAGS
        n.has_seg = flag
        return flag
    mark(root)
    return root


def esc(t: str) -> str:
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _attr_value(v: str) -> str:
    v = v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if '"' in v:
        if "'" not in v:
            return "'" + v + "'"
        v = v.replace('"', "&quot;")
    return '"' + v + '"'


def serialize(src: str, n: Node) -> str:
    """Serialisierung wie lxml.html.tostring(encoding='unicode', with_tail=False)."""
    if n.kind == "text":
        return esc(_html.unescape(src[n.s:n.e]))
    if n.kind == "comment":
        return src[n.s:n.e]
    a = "".join((" " + k) if v is None else (" %s=%s" % (k, _attr_value(v))) for k, v in n.attrs)
    if n.tag in VOID:
        return "<%s%s>" % (n.tag, a)
    return "<%s%s>%s</%s>" % (n.tag, a, "".join(serialize(src, k) for k in n.kids), n.tag)


# ==============================================================================
# Segmente
# ==============================================================================

PH = re.compile(r"⟦(\d+)⟧")
_PROSA = re.compile(r"[A-Za-zÄÖÜäöüß]{2}")


def hat_prosa(text: str) -> bool:
    return bool(_PROSA.search(text))


def seg_id(masked: str) -> str:
    """Segmentschlüssel wie lib_i18n.seg_id (über den gestrippten maskierten Text)."""
    return hashlib.sha1(masked.encode("utf-8")).hexdigest()[:12]


@dataclass
class Segment:
    kind: str                 # leaf | run
    block: str                # Blockart für den Prompt: h, p, li, td, cap, note, run
    s: int                    # Innenbereich in der Quelle
    e: int
    masked: str               # maskierter Text (ungestrippt)
    prot: List[Node]          # geschützte Elemente in Platzhalter-Reihenfolge

    @property
    def m(self) -> str:
        return self.masked.strip()

    @property
    def sid(self) -> str:
        return seg_id(self.m)

    @property
    def lead(self) -> str:
        return self.masked[: len(self.masked) - len(self.masked.lstrip())]

    @property
    def trail(self) -> str:
        return self.masked[len(self.masked.rstrip()):]


def mask_items(src: str, items: Sequence[Node]) -> Tuple[str, List[Node]]:
    out: List[str] = []
    prot: List[Node] = []
    for it in items:
        if it.kind == "text":
            out.append(esc(_html.unescape(src[it.s:it.e])))
        elif it.kind == "comment":
            out.append(src[it.s:it.e])
        elif it.tag in PROTECT:
            prot.append(it)
            out.append("⟦%d⟧" % (len(prot) - 1))
        else:
            out.append(serialize(src, it))
    return "".join(out), prot


def _block_kind(n: Node) -> str:
    if n.tag in ("h3", "h4", "h5", "h6"):
        return "h"
    if n.tag in ("td", "th"):
        return "td"
    if n.tag == "li":
        return "li"
    c = n.cls().split()
    if "diagram-note" in c or n.tag in ("figcaption", "caption"):
        return "cap"
    if "ai-note" in c:
        return "note"
    return "p"


def _leaves(root: Node) -> List[Node]:
    out: List[Node] = []
    for n in root.iter():
        if n is not root and n.kind == "el" and n.tag in SEG_TAGS and not n.has_seg:
            out.append(n)
    return out


def segments(src: str, root: Optional[Node] = None, prose_only: bool = True) -> List[Segment]:
    """Blattsegmente (wie lib_i18n.leaf_segmente + maskiere) und Laufsegmente, nach Quellposition sortiert.
    ``prose_only``: nur Segmente mit Prosa (wie i18n_extract); sonst alle nicht leeren (Gerüstvergleich)."""
    root = root or parse_html(src)
    segs: List[Segment] = []
    leaves = _leaves(root)
    leaf_ids = {id(n) for n in leaves}
    for n in leaves:
        masked, prot = mask_items(src, n.kids)
        segs.append(Segment("leaf", _block_kind(n), n.cs, n.ce, masked, prot))

    def flush(items: List[Node]) -> None:
        if not items:
            return
        masked, prot = mask_items(src, items)
        segs.append(Segment("run", "run", items[0].s, items[-1].e, masked, prot))

    def runs(n: Node) -> None:
        cur: List[Node] = []
        for k in n.kids:
            if k.kind == "comment":          # unsichtbar: nie übersetzen, trennt Läufe
                flush(cur)
                cur = []
                continue
            inline = k.kind == "text" or (k.kind == "el" and (k.tag in PROTECT or k.tag in INLINE)
                                          and not k.has_seg and id(k) not in leaf_ids)
            if inline:
                cur.append(k)
                continue
            flush(cur)
            cur = []
            if id(k) in leaf_ids:
                continue
            runs(k)
        flush(cur)

    runs(root)
    out = []
    for sg in sorted(segs, key=lambda x: (x.s, x.e)):
        m = sg.m
        if not m:
            continue
        if prose_only and not hat_prosa(PH.sub("", m)):
            continue
        out.append(sg)
    return out


# ==============================================================================
# Verweise in Dokumentstellen (span.docref) je Sprache
# ==============================================================================

PAGE_FMT = {"en": "p. {n}", "es": "p. {n}", "pt": "p. {n}", "fr": "p. {n}", "nl": "p. {n}", "ru": "с. {n}",
            "ar": "ص. {n}", "hi": "पृ. {n}", "ko": "{n}쪽", "zh": "第{n}页"}
FIG_FMT = {"en": "Fig. {n}", "es": "Fig. {n}", "pt": "Fig. {n}", "fr": "Fig. {n}", "nl": "Afb. {n}", "ru": "Рис. {n}",
           "ar": "الشكل {n}", "hi": "चित्र {n}", "ko": "그림 {n}", "zh": "图 {n}"}
_DR_QUOTE = re.compile("„([^“”\"]*)[“”\"]")
_DR_KAPITEL = re.compile(r"\bKapitel\s+(\d+(?:\.\d+)*)")
_DR_KAP = re.compile(r"\bKap\.\s*(\d+(?:\.\d+)*)")
_DR_PAGE = re.compile(r"(?<![\w.])S\.\s*(\d+(?:\s*[–-]\s*\d+)?)")
_DR_FIG = re.compile(r"\bAbb\.\s*(\d+(?:\.\d+)*)")


def localize_docref(text: str, lang: str, docref: Optional[Dict[str, str]] = None) -> str:
    """Deutsche Verpackung einer Dokumentstelle (``S. 12``, ``Abb. 7.1``, ``Kapitel 3``, „…“) in die Zielsprache;
    Dokumentnamen und Zitate bleiben wörtlich (wie lib_i18n.lokalisiere_docref)."""
    dr = docref or {}
    za, zz = dr.get("zitat_a", "“"), dr.get("zitat_z", "”")
    t = _DR_QUOTE.sub(lambda m: za + m.group(1) + zz, text)
    t = _DR_KAPITEL.sub(lambda m: dr.get("kapitel_fmt", "Chapter {n}").replace("{n}", m.group(1)), t)
    t = _DR_KAP.sub(lambda m: dr.get("kap_fmt", "ch. {n}").replace("{n}", m.group(1)), t)
    t = _DR_FIG.sub(lambda m: FIG_FMT.get(lang, "Fig. {n}").replace("{n}", m.group(1)), t)
    t = _DR_PAGE.sub(lambda m: PAGE_FMT.get(lang, "p. {n}").replace("{n}", re.sub(r"\s+", "", m.group(1))), t)
    return t


def _protected_src(src: str, n: Node, lang: str, docref: Optional[Dict[str, str]]) -> str:
    raw = src[n.s:n.e]
    if n.tag == "span" and "docref" in n.cls().split() and n.kids and all(k.kind == "text" for k in n.kids):
        inner = _html.unescape(src[n.cs:n.ce])
        loc = localize_docref(inner, lang, docref)
        if loc != inner:
            return src[n.s:n.cs] + esc(loc) + src[n.ce:n.e]
    return raw


def unmask(src: str, text: str, prot: Sequence[Node], lang: str, docref: Optional[Dict[str, str]] = None) -> str:
    def repl(m: "re.Match[str]") -> str:
        i = int(m.group(1))
        return _protected_src(src, prot[i], lang, docref) if i < len(prot) else m.group(0)
    return PH.sub(repl, text)


def rebuild(src: str, segs: Sequence[Segment], translated: Dict[int, str], lang: str,
            docref: Optional[Dict[str, str]] = None) -> str:
    """Fragment in der Zielsprache: Innenbereiche der Segmente ersetzen (``translated``: Index -> maskierter Text),
    alles andere bleibt byte-gleich. Segmente ohne Übersetzung bleiben unverändert."""
    out: List[str] = []
    pos = 0
    for i, sg in enumerate(segs):
        t = translated.get(i)
        if t is None:
            continue
        out.append(src[pos:sg.s])
        out.append(sg.lead + unmask(src, t, sg.prot, lang, docref) + sg.trail)
        pos = sg.e
    out.append(src[pos:])
    return "".join(out)


# ==============================================================================
# Geschützte Begriffe, Glossar
# ==============================================================================

TERMS_SCHEMA = "i18n-protected-terms@v1"


@dataclass
class Terms:
    """Geschützte Begriffe (sprachunabhängig, bleiben wörtlich) und Glossare je Sprache (Deutsch -> Ziel).
    ``vocab``: Bezeichner, die in ``<code>``-Elementen der Fragmente vorkommen (``code_vocab``); Binnenmajuskel-Wörter
    sind nur dann hart geschützt (sonst deutsche Pseudo-Bezeichner wie ``SubFunktion``)."""
    protected: List[str] = field(default_factory=list)
    glossary: Dict[str, Dict[str, str]] = field(default_factory=dict)
    docref: Dict[str, Dict[str, str]] = field(default_factory=dict)
    vocab: Optional[Set[str]] = None
    _rx: Optional[Dict[str, "re.Pattern[str]"]] = None
    _rx_loose: Optional[Dict[str, "re.Pattern[str]"]] = None

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Terms":
        prot = list(data.get("protected") or []) + list(data.get("terms") or [])
        for terms in (data.get("categories") or {}).values():
            prot.extend(terms)
        return cls(sorted(set(prot), key=lambda t: (-len(t), t)),
                   {l: dict(sorted((data.get("glossary") or {}).get(l, {}).items())) for l in LANGS},
                   dict((data.get("docref") or {})))

    def to_json(self) -> Dict[str, Any]:
        return {"schema": TERMS_SCHEMA, "protected": self.protected, "glossary": self.glossary, "docref": self.docref}

    def _regexes(self) -> Dict[str, "re.Pattern[str]"]:
        if self._rx is None:
            self._rx = {t: re.compile(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])") for t in self.protected}
        return self._rx

    def protected_in(self, text: str) -> List[str]:
        rx = self._regexes()
        return sorted(t for t in self.protected if t in text and rx[t].search(text))

    def protected_loose(self, text: str) -> List[str]:
        """Wie ``protected_in``, aber auch in Bindestrich-Komposita (``Dem-Meldung``); nur für die Restprüfung."""
        if self._rx_loose is None:
            self._rx_loose = {t: re.compile(r"(?<!\w)" + re.escape(t) + r"(?!\w)") for t in self.protected}
        return sorted(t for t in self.protected if t in text and self._rx_loose[t].search(text))

    def glossary_in(self, text: str, lang: str) -> Dict[str, str]:
        low = text.lower()
        return {k: v for k, v in self.glossary.get(lang, {}).items() if k.lower() in low}


# ==============================================================================
# Prüfung
# ==============================================================================

# Version der Prüfregeln (nicht Teil des Rezept-Hashs: gelockerte Regeln machen angenommene Übersetzungen nicht
# ungültig). Befunde älterer Prüfregeln schließen ihre Einheit nicht mehr (``decided_keys``).
CHECKS_VERSION = 3
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_INLINE_TEXT = re.compile(r"<(strong|em|b|i)>([^<]+)</\1>")
_CODE_EL = re.compile(r"<code\b[^>]*>(.*?)</code>", re.S)
_IDENT_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def strip_comments(text: str) -> str:
    return _COMMENT.sub("", text)


def code_vocab(htmls: Iterable[str]) -> Set[str]:
    """Bezeichner aus allen ``<code>``-Elementen (verschachtelt eingeschlossen)."""
    out: Set[str] = set()
    for h in htmls:
        for m in _CODE_EL.finditer(h):
            out.update(_IDENT_WORD.findall(_html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))))
    return out

_IDS = re.compile(r"\[(?:SWS|RS)_[A-Za-z]+_\d+\]|\b(?:AUTOSAR|EXP|FO)_[A-Za-z0-9]+\b")     # wie i18n_translate.pruefe
_TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9]*)((?:\s+[^\s=>/]+(?:=(?:\"[^\"]*\"|'[^']*'))?)*)\s*>")
_ATOMIC = re.compile(r"<(code|a|span)\b[^>]*>.*?</\1>", re.S)
_FORBIDDEN_OUT = re.compile(r"<\s*script|javascript:|\bon[a-z]+\s*=|[\x00-\x08\x0b\x0c\x0e-\x1f]", re.I)
_BARE_AMP = re.compile(r"&(?![A-Za-z][A-Za-z0-9]*;|#\d+;|#[xX][0-9A-Fa-f]+;)")
_HARD_PATTERNS = [
    r"\[(?:SWS|RS|SRS|TPS|PRS|ECUC|CONSTR)_[A-Za-z0-9_]+\]",
    r"\b(?:SWS|RS|SRS|TPS|PRS|ECUC|CONSTR|AP)_[A-Za-z0-9_]*\d[A-Za-z0-9_]*\b",
    r"\b(?:AUTOSAR|EXP|FO)_[A-Za-z0-9_]+\b",
    r"\b[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z0-9_]+)+\b",
    r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]*[A-Za-z0-9]\b",
    r"\b[\w.-]+\.(?:h|hpp|c|cpp|arxml|json|xml|yaml|dot)\b",
    r"\b0x[0-9A-Fa-f]+\b",
    r"\bNRC\s+0x[0-9A-Fa-f]{2}\b",
    r"\bR\d\d-\d\d\b|\bR\d+\.\d+(?:\.\d+)?\b",
    r"\b(?:uint8|uint16|uint32|uint64|sint8|sint16|sint32|sint64|boolean|float32|float64)\b",
    r"\b[A-Z][A-Z0-9]*[A-Z0-9](?:/[A-Z0-9]+)?\b",
]
_TOKENS = re.compile("|".join("(?:%s)" % p for p in _HARD_PATTERNS))
_CAMEL = re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9]*\b|\b[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*\b")
_ACRONYM = re.compile(r"^[A-Z][A-Z0-9]*[A-Z0-9](?:/[A-Z0-9]+)?$")
# Großbuchstaben-Wörter des deutschen Texts, die übersetzt werden dürfen (deutsche Kürzel und Großschreibung)
_NOT_PROTECTED = frozenset(("KI", "DE", "ZB", "BZW", "GGF", "USW", "CA", "EU", "UND", "ODER", "NICHT", "KEIN", "KEINE",
                            "MUSS", "SOLL", "KANN", "WENN", "DANN", "SONST", "NUR", "ALLE"))
# Deutsche Funktionswörter, die in keiner Zielsprache als Wort vorkommen (Ausnahmen je Sprache unten)
GERMAN_WORDS = frozenset("""und oder nicht wird werden ist sind für mit eine einer eines einem einen dem auf bei über sich
auch nach wenn dass zum zur vom beim sowie durch diese dieser dieses diesem diesen kann können muss müssen wurde wurden
zwischen jedoch damit dabei ohne gegen aus ein im sie hier noch bereits jeweils sonst dann nur keine keinen gibt liefert
siehe gemäß laut zurück sowohl etwa weitere weiteren weil deshalb dafür dazu wobei welche welcher welches unter zwei drei
somit daher denn also werden der die das den des""".split())
# Nur kleingeschriebene Funktionswörter zählen (Großschreibung ist meist ein Name: das Modul „Dem“).
GERMAN_EXCEPT = {"en": {"also", "die", "will", "am", "an", "in", "so", "was", "bin", "hat", "war", "man", "dem"},
                 "nl": {"werden", "die", "den", "der", "des", "in", "is", "dan", "also", "zwei", "hier", "noch",
                        "überhaupt"},
                 "fr": {"des", "sur"}, "es": {"sin"}, "pt": {"das"}, "ru": set(), "ar": set(), "hi": set(),
                 "ko": set(), "zh": set()}
_UMLAUT = re.compile(r"[äöüßÄÖÜ]")
# Trema der Zielsprache ist kein Umlaut (nl coördinatie, es lingüístico, fr capharnaüm)
_UMLAUT_LANG = {"nl": re.compile(r"ß"), "es": re.compile(r"[äößÄÖ]"), "pt": re.compile(r"[äößÄÖ]"),
                "fr": re.compile(r"[äößÄÖ]")}
_WORD = re.compile(r"[^\W\d_]+")
SEG_RATIO = {"zh": (0.10, 1.10), "ko": (0.18, 1.40)}
SEG_RATIO_DEFAULT = (0.33, 2.50)
FRAG_RATIO = {"zh": (0.15, 0.85), "ko": (0.25, 1.05)}
FRAG_RATIO_DEFAULT = (0.45, 1.90)
_QUOTES = {"en": ("“", "”"), "hi": ("“", "”"), "ko": ("“", "”"), "zh": ("“", "”"), "es": ("«", "»"),
           "pt": ("«", "»"), "ru": ("«", "»"), "ar": ("«", "»"), "fr": ("« ", " »"), "nl": ("“", "”")}
_DE_PAIR = re.compile("„([^„“]*)“")


def strip_markup(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", PH.sub(" ", text))).strip()


_ARTICLE_NEXT = re.compile(r"\s+[a-zäöüß]")


def _article_only(term: str, text: str, terms: "Terms") -> bool:
    """Geschützter Begriff, der zugleich ein deutsches Funktionswort ist („Dem“ / „dem“), und an allen Stellen als
    Artikel steht (gefolgt von einem kleingeschriebenen Wort: „Dem durch … typisierten Port“): nicht verlangt."""
    if term.lower() not in GERMAN_WORDS:
        return False
    hits = list(terms._regexes()[term].finditer(text))
    return bool(hits) and all(_ARTICLE_NEXT.match(text, m.end()) for m in hits)


def protected_tokens(de: str, vocab: Optional[Set[str]] = None, soft: bool = False) -> List[str]:
    """Geschützte Tokens eines maskierten deutschen Texts. Hart: Kennungen, Bezeichner mit ``_``/``::``, Dateinamen,
    Hex, Releases, Typnamen (wie ``ai_localize`` INV-02), Kürzel ab drei Zeichen; Kürzel aus zwei Zeichen (ID, IO,
    OS …) und Binnenmajuskel-Wörter nur, wenn sie im Code-Vokabular stehen (ohne Vokabular: alle wie bisher).
    ``soft=True`` liefert zusätzlich die übrigen bezeichnerartigen Tokens (für die Restprüfung)."""
    plain = _html.unescape(strip_markup(strip_comments(de)))
    out = []
    for m in _TOKENS.finditer(plain):
        tok = m.group(0)
        if tok in _NOT_PROTECTED or len(tok) < 2:
            if soft and len(tok) >= 2:
                out.append(tok)
            continue
        if vocab is not None and len(tok) == 2 and _ACRONYM.match(tok) and tok not in vocab and not soft:
            continue
        out.append(tok)
    for m in _CAMEL.finditer(plain):
        tok = m.group(0)
        if soft or vocab is None or tok in vocab:
            out.append(tok)
    return sorted(set(out))


def _present(tok: str, text: str) -> bool:
    if tok in text:
        return True
    for suf in ("es", "s"):
        if tok.endswith(suf) and len(tok) > len(suf) + 1 and tok[: -len(suf)] in text:
            return True
    return False


def german_markers(text: str, lang: str, keep: Sequence[str] = ()) -> Tuple[int, int]:
    """(deutsche Merkmale, Wörter) im Klartext ohne Markup, Kommentare, Platzhalter und geschützte Tokens/Begriffe:
    kleingeschriebene deutsche Funktionswörter und Wörter mit Umlaut (ohne Trema der Zielsprache)."""
    plain = _html.unescape(strip_markup(strip_comments(text)))
    for k in sorted(set(keep), key=len, reverse=True):
        plain = plain.replace(k, " ")
    words = _WORD.findall(plain)
    exc = GERMAN_EXCEPT.get(lang, set())
    uml = _UMLAUT_LANG.get(lang, _UMLAUT)
    hits = sum(1 for w in words if (w.islower() and w in GERMAN_WORDS and w not in exc)
               or (uml.search(w) and w.lower() not in exc))
    return hits, len(words)


def is_german(text: str) -> bool:
    hits, _ = german_markers(text, "xx")
    return hits > 0


def prose_len(text: str, keep: Sequence[str] = ()) -> int:
    """Zeichen der Prosa ohne Leerraum, Markup, Platzhalter und (optional) geschützte Tokens."""
    plain = _html.unescape(strip_markup(text))
    for k in sorted(set(keep), key=len, reverse=True):
        plain = plain.replace(k, " ")
    return len(re.sub(r"\s+", "", plain))


def _tag_tokens(text: str) -> Tuple[List[str], Optional[str]]:
    """Alle Tags (als Zeichenkette) und ggf. ein Verschachtelungsfehler."""
    toks: List[str] = []
    stack: List[str] = []
    for m in _TAG.finditer(text):
        toks.append(m.group(0))
        name = m.group(2).lower()
        if name in VOID:
            continue
        if m.group(1):
            if not stack or stack[-1] != name:
                return toks, "nesting"
            stack.pop()
        else:
            stack.append(name)
    return toks, ("unclosed" if stack else None)


def normalize_output(t: str, lang: str) -> str:
    """Deterministische Nacharbeit: deutsche Anführungszeichen in die Sprachform, nacktes ``&`` maskieren."""
    za, zz = _QUOTES.get(lang, ("“", "”"))
    t = _DE_PAIR.sub(lambda m: za + m.group(1) + zz, t.strip())
    return _BARE_AMP.sub("&amp;", t)


def check_segment(de: str, t: Any, lang: str, terms: Optional[Terms] = None) -> List[str]:
    """Prüfung einer Segmentübersetzung (maskiert). Rückgabe: Liste von Problemen ``code`` oder ``code:detail``."""
    if not isinstance(t, str) or not t.strip():
        return ["empty"]
    de, t = strip_comments(de), strip_comments(t)       # unsichtbar, nie geprüft (die Antwort darf sie weglassen)
    p: List[str] = []
    if "```" in t:
        p.append("markdown")
    if _FORBIDDEN_OUT.search(t):
        p.append("forbidden")
    if sorted(PH.findall(de)) != sorted(PH.findall(t)) or re.search("[⟦⟧]", PH.sub("", t)):
        p.append("placeholders")
    tags_de, _ = _tag_tokens(de)
    tags_t, nest = _tag_tokens(t)
    if Counter(tags_de) != Counter(tags_t) or nest or "<" in _TAG.sub("", t):
        p.append("markup")
    if Counter(_ATOMIC.findall(de)) != Counter(_ATOMIC.findall(t)) or \
            sorted(m.group(0) for m in _ATOMIC.finditer(de)) != sorted(m.group(0) for m in _ATOMIC.finditer(t)):
        p.append("markup")
    if sorted(_IDS.findall(de)) != sorted(_IDS.findall(t)):
        p.append("ids")
    plain_t = _html.unescape(strip_markup(t))
    vocab = terms.vocab if terms else None
    toks = protected_tokens(de, vocab)
    # Kürzel aus zwei Zeichen (ID, IO, OS …) dürfen übersetzt werden (arabisch „معرّف“, russisch „ОС“): nie verlangt
    missing = [tok for tok in toks if not (len(tok) == 2 and _ACRONYM.match(tok))
               and not _present(tok, plain_t) and not _present(tok, t)]
    plain_de = _html.unescape(strip_markup(de))
    terms_de = [x for x in terms.protected_in(plain_de) if not _article_only(x, plain_de, terms)] if terms else []
    missing += [x for x in terms_de if x not in plain_t]
    if missing:
        p.append("protected:" + ",".join(sorted(set(missing))[:5]))
    loose = terms.protected_loose(plain_t) if terms else []
    hits, words = german_markers(t, lang, keep=protected_tokens(de, vocab, soft=True) + list(terms_de) + loose)
    if hits >= 2 or (hits and words <= 12):
        p.append("german")
    if t.strip() == de.strip() and is_german(de):
        p.append("untranslated")
    # deutsche Hervorhebung unverändert übernommen (<strong>Zuweisung und Konsistenz:</strong> in russischem Text)
    for m in _INLINE_TEXT.finditer(de):
        inner = m.group(2)
        if len(inner) >= 4 and m.group(0) in t and german_markers(inner, lang, keep=toks + terms_de)[0]:
            p.append("untranslated")
            break
    keep = list(toks) + list(terms_de)
    n_de = prose_len(de, keep)
    if n_de >= 40:
        lo, hi = SEG_RATIO.get(lang, SEG_RATIO_DEFAULT)
        r = prose_len(t, keep) / n_de
        if not lo <= r <= hi:
            p.append("length")
    return sorted(set(p))


def problem_codes(problems: Iterable[str]) -> List[str]:
    return sorted({x.split(":", 1)[0] for x in problems})


@dataclass
class Structure:
    outside: List[Any]
    inside: List[Tuple[str, Tuple[Tuple[str, Tuple], ...]]]


def structure(src: str) -> Structure:
    """Gerüst eines Fragments: Elemente außerhalb der Segmente (Tag, Attribute, Tiefe) und je Segment die Multimenge
    der Elemente darin. Gleiches Gerüst = gleiche Tags, Attribute, Verweise, Diagramme; nur Text darf sich ändern."""
    root = parse_html(src)
    segs = segments(src, root, prose_only=False)
    spans = [(sg.s, sg.e) for sg in segs]
    outside: List[Any] = []
    inside: List[Tuple[str, Tuple]] = []
    import bisect
    starts = [s for s, _ in spans]

    def in_seg(n: Node) -> int:
        i = bisect.bisect_right(starts, n.s) - 1
        if i >= 0 and spans[i][0] <= n.s and n.e <= spans[i][1] and n.s < spans[i][1]:
            return i
        return -1

    per: Dict[int, Counter] = {i: Counter() for i in range(len(segs))}

    def walk(n: Node, depth: int) -> None:
        for k in n.kids:
            if k.kind != "el":
                continue
            i = in_seg(k)
            if i >= 0:
                per[i][(k.tag, tuple(k.attrs))] += 1
            else:
                outside.append((depth, k.tag, tuple(k.attrs)))
            walk(k, depth + 1)
    walk(root, 0)
    for i, sg in enumerate(segs):
        inside.append((sg.kind, tuple(sorted(per[i].items()))))
    return Structure(outside, inside)


def check_fragment(src: str, out: str, segs: Sequence[Segment], translated: Dict[int, str], lang: str,
                   terms: Optional[Terms] = None) -> List[str]:
    """Prüfung des wiederaufgebauten Fragments gegen die Quelle (Gerüst, Verweise, Diagramme, deutscher Rest,
    Längenverhältnis). Rückgabe: Probleme."""
    p: List[str] = []
    a, b = structure(src), structure(out)
    if a.outside != b.outside:
        p.append("skeleton")
    if a.inside != b.inside:
        p.append("skeleton-inline")
    reqs = lambda x: sorted(re.findall(r'<a\s+class=["\']spec-record-ref["\'][^>]*data-req=["\']([^"\']+)["\']', x))
    if reqs(src) != reqs(out):
        p.append("spec-refs")
    if src.count('<div class="diagram"') != out.count('<div class="diagram"') or src.count("<svg") != out.count("<svg"):
        p.append("diagrams")
    if out.lstrip().startswith('<div class="ai') != src.lstrip().startswith('<div class="ai'):
        p.append("root")
    if "```" in out and "```" not in src:
        p.append("markdown")
    hits = words = de_len = t_len = 0
    for i, sg in enumerate(segs):
        t = translated.get(i)
        if t is None:
            continue
        keep = protected_tokens(sg.m, soft=True)
        if terms:
            keep += terms.protected_loose(_html.unescape(strip_markup(t)))
        h, w = german_markers(t, lang, keep=keep)
        hits += h
        words += w
        de_len += prose_len(sg.m)
        t_len += prose_len(t)
    if hits > max(3, 0.01 * words):
        p.append("german")
    if de_len >= 200:
        lo, hi = FRAG_RATIO.get(lang, FRAG_RATIO_DEFAULT)
        if not lo <= t_len / de_len <= hi:
            p.append("length")
    return p


# ==============================================================================
# Rezept: Prompt und Antwort
# ==============================================================================

RECIPE_ID = "translate-segments@1"
NO_TOOLS_RULE = ("Werkzeuge sind nicht erlaubt: keine Dateien lesen oder schreiben, keine Skripte, keine Suche im "
                 "Arbeitsverzeichnis. Der Prompt enthält alles. Antworte direkt mit dem JSON.\n")
STRICT_RETRY_RULE = ("STRENG: Im vorigen Versuch wurden verbotene Werkzeuge benutzt. Benutze KEIN Werkzeug. Keine "
                     "Befehle, keine Dateisuche, keine Transkripte. Antworte nur mit dem JSON.\n")
INSTRUCTIONS = """You translate German segments of AI-written technical documentation about AUTOSAR (module and cluster
user guides, namespace, class and service guides, usage notes of API elements, diagram captions) into {lang_name}.

After these instructions follow the segments, one JSON object per line: {{"id": segment id, "f": fragment, "k": block
kind, "de": German text}}. Block kinds: h heading, p paragraph, li list item, td table cell, cap diagram caption,
note closing note, run text run. A segment is HTML-escaped inline text: keep entities such as &lt; &gt; &amp; as they are.

Rules (checked by a machine; a segment that breaks one is rejected):
1. Placeholders ⟦0⟧, ⟦1⟧, … stand for protected content (links, code, references). Keep every placeholder of a
   segment exactly once; never invent, drop or renumber one; place it where the {lang_short} grammar needs it.
2. Inline markup such as <strong>…</strong>, <em>…</em>, <var>…</var> and any <code>, <a> or <span> element inside
   it stays exactly as it is (same tags, same attributes, same content); translate only the plain text around and
   inside formatting tags. Never add tags.
3. Keep verbatim and untranslated: identifiers and code (Std_ReturnType, E_OK, ara::com, GetNewSamples, Dcm_Dem.h),
   requirement and document ids ([SWS_CM_00701], RS_AP_00111, AUTOSAR_AP_SWS_…), release names (R25-11), acronyms
   (PDU, NRC, DTC, SOME/IP) and every protected term listed below (AUTOSAR module, cluster, platform and document
   names). Keep English quotations from the specification verbatim.
4. Glossary: where a German term listed below occurs, use the given rendering.
5. Style: precise technical register, consistent terminology, no direct address of the reader unless the source has
   it; resolve German compounds idiomatically, no word-by-word calques; use {lang_short} typography and quotation
   marks. "Interpretation:", "Annahme", "vermutlich" mark cautious statements: keep the cautious tone.{extra_style}
6. Translate every segment completely; no German words may remain except protected terms.
Answer only with the JSON object {{"translations": [{{"id": …, "t": …}}]}} containing every segment id exactly once.
"""
EXTRA_STYLE = {"ar": " Write normal Arabic prose; Latin identifiers stay Latin; insert no direction marks.",
               "zh": " Use Simplified Chinese with full-width punctuation in prose.",
               "fr": " Use French spacing before double punctuation (narrow no-break space).",
               "hi": " Write Hindi in Devanagari; keep established English technical terms in Latin script."}
LANG_SHORT = {"en": "English", "es": "Spanish", "pt": "Portuguese", "fr": "French", "ru": "Russian", "ar": "Arabic",
              "hi": "Hindi", "ko": "Korean", "zh": "Chinese", "nl": "Dutch"}
TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {"translations": {"type": "array", "items": {
        "type": "object", "properties": {"id": {"type": "string"}, "t": {"type": "string"}},
        "required": ["id", "t"], "additionalProperties": False}}},
    "required": ["translations"], "additionalProperties": False}
RECIPE = {"id": RECIPE_ID, "segmenter": "lib_i18n-leaf+runs@1", "instructions": INSTRUCTIONS, "extra": EXTRA_STYLE,
          "no_tools": NO_TOOLS_RULE, "schema": TRANSLATION_SCHEMA, "page_fmt": PAGE_FMT, "fig_fmt": FIG_FMT,
          "checks": "segment@1+fragment@1", "max_terms": 60, "max_glossary": 80}
RECIPE_HASH = obj_hash(RECIPE)[:16]
# Überarbeitung des Prompts ohne neuen Rezeptstand (angenommene Übersetzungen bleiben gültig, Schlüssel bleiben):
# 2 = Kommentare entfernt, Bezeichner und Kürzel des Aufrufs ausdrücklich gelistet. Steht in jedem tm-Glied.
PROMPT_REVISION = 2
PROMPT_MAX_IDENTS = 80
FRAGMENT_KIND_LABEL = {"modules": "module guide", "clusters": "cluster guide", "classes": "class guide",
                       "namespaces": "namespace guide", "services": "service guide", "elements": "usage note"}


@dataclass
class PromptItem:
    bid: str
    frag: int
    block: str
    de: str


def fragment_label(path: str) -> str:
    parts = path.split("/")
    platform = "Classic Platform" if parts[0] == "classic" else "Adaptive Platform"
    if parts[0] == "classic":
        parts = parts[1:]
    kind = FRAGMENT_KIND_LABEL.get(parts[0], parts[0])
    return f"{kind} {parts[1] if len(parts) > 2 else ''} ({platform})".replace("  ", " ")


def build_prompt(lang: str, items: Sequence[PromptItem], frags: Sequence[str], terms: Terms,
                 notes: Optional[Dict[str, List[str]]] = None) -> str:
    """Deterministischer Prompt: gleiche Sprache, Segmente, Fragmente, Begriffe und Hinweise ergeben gleiche Bytes."""
    items = [PromptItem(it.bid, it.frag, it.block, strip_comments(it.de).strip()) for it in items]
    text = "\n".join(it.de for it in items)
    plain = _html.unescape(strip_markup(text))
    prot = terms.protected_in(plain)[:RECIPE["max_terms"]]
    idents = sorted({t for it in items for t in protected_tokens(it.de, terms.vocab)} - set(prot))[:PROMPT_MAX_IDENTS]
    gloss = sorted(terms.glossary_in(plain, lang).items())[:RECIPE["max_glossary"]]
    head = NO_TOOLS_RULE + "\n" + INSTRUCTIONS.format(lang_name=LANG_NAMES[lang], lang_short=LANG_SHORT[lang],
                                                      extra_style=EXTRA_STYLE.get(lang, ""))
    head += "\nProtected terms (keep exactly): " + (", ".join(prot) if prot else "(none in this batch)") + "\n"
    if idents:
        head += "Identifiers and acronyms in this batch (keep exactly, also in Cyrillic, Arabic, Devanagari, Hangul and " \
                "Chinese text): " + ", ".join(idents) + "\n"
    head += "Glossary (German → %s): %s\n" % (LANG_SHORT[lang], "; ".join(f"{a} → {b}" for a, b in gloss) if gloss
                                               else "(none in this batch)")
    head += "Fragments: " + "; ".join(f"f{i}: {fragment_label(p)}" for i, p in enumerate(frags)) + "\n"
    if notes:
        head += ("\nREPEAT: these segments were rejected before; fix exactly the named problems:\n"
                 + "\n".join(f"- id {bid}: {', '.join(v)}" for bid, v in sorted(notes.items(), key=lambda kv: int(kv[0])))
                 + "\n")
    lines = [json.dumps({"id": it.bid, "f": it.frag, "k": it.block, "de": it.de}, ensure_ascii=False,
                        separators=(",", ":")) for it in items]
    ids = ", ".join(it.bid for it in items)
    return (head + "<segments>\n" + "\n".join(lines) + "\n</segments>\nSegment ids in this batch: " + ids
            + "\nReturn the JSON object now.\n" + NO_TOOLS_RULE)


PROBLEM_HINTS = {"placeholders": "keep every placeholder ⟦n⟧ exactly once", "markup": "keep the inline tags exactly",
                 "ids": "keep requirement/document ids", "protected": "keep identifiers and protected terms verbatim",
                 "german": "translate all German words", "untranslated": "translate the segment",
                 "length": "translate completely, nothing added or omitted", "empty": "give a translation",
                 "markdown": "no code fences", "forbidden": "no scripts or event attributes", "missing": "answer this id"}


def parse_translations(obj: Any, ids: Sequence[str]) -> Tuple[Dict[str, str], List[str]]:
    out: Dict[str, str] = {}
    problems: List[str] = []
    want = set(ids)
    if not isinstance(obj, dict) or not isinstance(obj.get("translations"), list):
        return out, ["no 'translations' list"]
    for x in obj["translations"]:
        if not isinstance(x, dict):
            problems.append("entry is not an object")
            continue
        bid = str(x.get("id", "")).strip()
        if bid not in want:
            problems.append("unknown id")
            continue
        if bid in out:
            problems.append("duplicate id")
            continue
        if isinstance(x.get("t"), str):
            out[bid] = x["t"]
    for bid in sorted(want - set(out), key=lambda v: int(v) if v.isdigit() else 0):
        problems.append(f"missing {bid}")
    return out, problems


# ==============================================================================
# Fragmente, Einheiten, Schlüssel, Reihenfolge
# ==============================================================================

def fragment_tier(path: str) -> str:
    parts = path.split("/")
    if parts[0] == "classic":
        parts = parts[1:]
    if parts[0] in ("modules", "clusters"):
        return "guide"
    if parts[0] in ("classes", "namespaces", "services"):
        return "api"
    return "element"


def fragment_release(path: str, fallback: str = "") -> str:
    m = re.search(r"anchor_r(\d\d)_(\d\d)\.html$", path)
    return f"R{m.group(1)}-{m.group(2)}" if m else fallback


def fragment_guide(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if name.startswith("impl_anchor_"):
        return "impl"
    if name.startswith("groups_"):
        return "groups"
    return "user"


def identity(path: str, lang: str, release: str) -> str:
    """Identität nach CONCEPT-0061 §3.1: ``<kind>/<slug>/<guide>.<lang>@<release>``."""
    return f"{path.rsplit('/', 1)[0]}/{fragment_guide(path)}.{lang}@{release or 'R?'}"


def unit_id(path: str, lang: str) -> str:
    return f"tr:{path}@{lang}"


def split_unit(unit: str) -> Tuple[str, str]:
    body = unit[3:] if unit.startswith("tr:") else unit
    path, _, lang = body.rpartition("@")
    return path, lang


_SCOPE_CACHE: Dict[Tuple[int, str, str], str] = {}


def tm_scope(lang: str, de: str, terms: Terms) -> str:
    """Gültigkeitsbereich eines TM-Eintrags: Rezept, Sprache und die im Segment vorkommenden Begriffe/Glossarwörter.
    Ändert sich ein Begriff, den das Segment enthält, wird nur dieses Segment neu übersetzt."""
    k = (id(terms), lang, de)
    hit = _SCOPE_CACHE.get(k)
    if hit is None:
        plain = _html.unescape(strip_markup(de))
        hit = _SCOPE_CACHE[k] = obj_hash({"r": RECIPE_HASH, "l": lang, "p": terms.protected_in(plain),
                                          "g": sorted(terms.glossary_in(plain, lang).items())})[:16]
    return hit


def fragment_terms(segs: Sequence[Segment], terms: Terms, lang: str) -> Tuple[str, str]:
    plain = _html.unescape(strip_markup("\n".join(sg.m for sg in segs)))
    return (obj_hash(terms.protected_in(plain))[:16],
            obj_hash([sorted(terms.glossary_in(plain, lang).items()), terms.docref.get(lang) or {}])[:16])


def _fragment_terms_cached(f: "Fragment", terms: Terms, lang: str) -> Tuple[str, str]:
    cache = f.__dict__.setdefault("_terms_cache", {})
    if "plain" not in cache:
        cache["plain"] = _html.unescape(strip_markup("\n".join(sg.m for sg in f.segs)))
        cache["prot"] = obj_hash(terms.protected_in(cache["plain"]))[:16]
    if lang not in cache:
        cache[lang] = obj_hash([sorted(terms.glossary_in(cache["plain"], lang).items()), terms.docref.get(lang) or {}])[:16]
    return cache["prot"], cache[lang]


def unit_key(unit: str, source_sha: str, terms_h: str, gloss_h: str) -> str:
    """Schlüssel einer Einheit: Hash des deutschen Quellfragments, Rezeptstand und der für das Fragment wirksamen
    geschützten Begriffe und Glossareinträge. Gleicher Schlüssel in der Kette = erledigt."""
    return obj_hash({"unit": unit, "recipe": RECIPE_ID, "recipe_hash": RECIPE_HASH, "source": source_sha,
                     "terms": terms_h, "glossary": gloss_h})[:32]


@dataclass
class Fragment:
    path: str
    html: str
    sha256: str
    tier: str
    release: str
    proxy: int = 0
    trace_output: str = ""
    channel: str = "fragment"          # fragment: Sprachvariante unter content/ai/<lang>; register: nur TM-Einträge
    _segs: Optional[List[Segment]] = None

    @classmethod
    def from_row(cls, r: Dict[str, Any]) -> "Fragment":
        return cls(r["path"], r["html"], r["sha256"], r.get("tier") or fragment_tier(r["path"]),
                   r.get("release") or fragment_release(r["path"]), int(r.get("proxy") or 0), r.get("trace_output", ""),
                   r.get("channel") or "fragment")

    @property
    def segs(self) -> List[Segment]:
        if self._segs is None:
            self._segs = segments(self.html)
        return self._segs


CHUNK_CHARS = 250000           # mehrere volle Aufrufe je Sprache und Abschnitt (geringe Grundlast je Zeichen)


def build_plan(frags: Sequence[Fragment], terms: Terms, langs: Sequence[str] = LANGS,
               decided: Optional[Set[str]] = None, latest: Optional[Dict[str, Dict[str, Any]]] = None,
               chunk_chars: int = CHUNK_CHARS) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Arbeitsliste: alle (Fragment, Sprache), deren Schlüssel nicht in der Kette steht.

    Reihenfolge: Stufe (Leitfäden, API, Elemente), dann innerhalb der Stufe nach Reichweite (``proxy``, absteigend,
    dann Pfad). Fragmente einer Stufe werden zu Abschnitten von etwa ``chunk_chars`` deutschen Zeichen gebündelt; je
    Abschnitt kommen alle Sprachen in Site-Reihenfolge nacheinander. So füllt ein Abschnitt in einer Sprache einen
    Aufruf, und jede Seite wird früh in allen Sprachen fertig."""
    decided = decided or set()
    latest = latest or {}
    stats: Dict[str, Any] = {"total": 0, "decided": 0, "new": 0, "stale": 0, "by_tier": {}, "by_lang": {}}
    plan: List[Dict[str, Any]] = []
    for tier in TIERS:
        group = sorted((f for f in frags if f.tier == tier), key=lambda f: (-f.proxy, f.path))
        chunks: List[List[Fragment]] = []
        cur: List[Fragment] = []
        size = 0
        for f in group:
            n = sum(len(sg.m) for sg in f.segs)
            if cur and size + n > chunk_chars:
                chunks.append(cur)
                cur, size = [], 0
            cur.append(f)
            size += n
        if cur:
            chunks.append(cur)
        for ci, chunk in enumerate(chunks):
            for lang in langs:
                for f in chunk:
                    unit = unit_id(f.path, lang)
                    th, gh = _fragment_terms_cached(f, terms, lang)
                    key = unit_key(unit, f.sha256, th, gh)
                    for b, k in ((stats, None), (stats["by_tier"].setdefault(tier, {"total": 0, "decided": 0,
                                                                                    "new": 0, "stale": 0}), None),
                                 (stats["by_lang"].setdefault(lang, {"total": 0, "decided": 0, "new": 0, "stale": 0}),
                                  None)):
                        b["total"] += 1
                    if key in decided:
                        for b in (stats, stats["by_tier"][tier], stats["by_lang"][lang]):
                            b["decided"] += 1
                        continue
                    prior = latest.get(unit)
                    status = "stale" if prior else "new"
                    for b in (stats, stats["by_tier"][tier], stats["by_lang"][lang]):
                        b[status] += 1
                    plan.append({"unit": unit, "key": key, "path": f.path, "lang": lang, "tier": tier,
                                 "chunk": ci, "status": status, "prior": prior["hash"] if prior else None,
                                 "source_sha256": f.sha256, "terms": th, "glossary": gh,
                                 "release": f.release, "proxy": f.proxy})
    for i, u in enumerate(plan, 1):
        u["order"] = i
    return plan, stats


# ==============================================================================
# Übersetzungsspeicher
# ==============================================================================

class TM:
    """Segmentschlüssel -> Übersetzung je Sprache. Register-Einträge (``_src/i18n/<lang>/segments.json``) gelten
    unabhängig vom Gültigkeitsbereich; Einträge aus der Kette nur im selben Bereich (``tm_scope``). Der erste gültige
    Eintrag gewinnt (Register vor Kette, Kette in Gliedreihenfolge): gleiche Segmente werden einmal übersetzt und
    überall gleich verwendet."""

    def __init__(self) -> None:
        self.reg: Dict[Tuple[str, str], str] = {}
        self.live: Dict[Tuple[str, str, str], Tuple[str, str]] = {}      # (lang, sid, scope) -> (t, origin)

    def add_register(self, lang: str, sid: str, t: str) -> None:
        self.reg.setdefault((lang, sid), t)

    def add_live(self, lang: str, sid: str, scope: str, t: str, origin: str) -> bool:
        k = (lang, sid, scope)
        if k in self.live:
            return False
        self.live[k] = (t, origin)
        return True

    def copy(self) -> "TM":
        c = TM()
        c.reg, c.live = dict(self.reg), dict(self.live)
        return c

    def get(self, lang: str, sid: str, scope: str) -> Optional[Tuple[str, str]]:
        if (lang, sid) in self.reg:
            return self.reg[(lang, sid)], "reg"
        return self.live.get((lang, sid, scope))

    def load_chain(self, entries: Iterable[Dict[str, Any]]) -> int:
        n = 0
        for e in entries:
            if e.get("kind") != "tm":
                continue
            for s in e.get("segments") or []:
                n += self.add_live(e["lang"], s["sid"], s["scope"], s["t"], "tm:" + e["hash"][:12])
        return n


# ==============================================================================
# Planung der Aufrufe (gemeinsam für Job und Schätzung)
# ==============================================================================

# Sichtbare Ausgabe-Tokens je deutschem Zeichen und je Segment, gemessen im ersten vollen Lauf (2.074 Aufrufe,
# Ausgabe ohne Denk-Tokens = 0,251·Zeichen + 49,7·Segmente; je Sprache mit 50 Tokens je Segment angepasst).
# Der Job führt die Werte je Sprache aus den gemeldeten sichtbaren Tokens nach.
OUT_TOKENS_PER_CHAR = {"en": 0.162, "es": 0.241, "pt": 0.309, "fr": 0.248, "ru": 0.232, "ar": 0.303, "hi": 0.269,
                       "ko": 0.277, "zh": 0.161, "nl": 0.292}
SEG_JSON_TOKENS = 50
PROMPT_BASE_BYTES = 6000


@dataclass
class Claim:
    sid: str
    scope: str
    de: str
    block: str
    path: str
    unit: str


@dataclass
class Batch:
    no: int
    lang: str
    model: str
    tier: str
    claims: List[Claim]
    attempt: int = 1
    notes: Optional[Dict[str, List[str]]] = None
    frags: List[str] = field(default_factory=list)
    items: List[PromptItem] = field(default_factory=list)
    prompt: str = ""

    def finish(self, terms: Terms) -> "Batch":
        frags: List[str] = []
        for c in self.claims:
            if c.path not in frags:
                frags.append(c.path)
        self.frags = frags
        self.items = [PromptItem(str(i + 1), frags.index(c.path), c.block, c.de) for i, c in enumerate(self.claims)]
        notes = None
        if self.notes:
            by_sid = {c.sid: str(i + 1) for i, c in enumerate(self.claims)}
            notes = {by_sid[s]: [PROBLEM_HINTS.get(x, x) for x in v] for s, v in self.notes.items() if s in by_sid}
        self.prompt = build_prompt(self.lang, self.items, frags, terms, notes)
        return self

    @property
    def de_chars(self) -> int:
        return sum(len(c.de) for c in self.claims)


@dataclass
class UnitState:
    plan: Dict[str, Any]
    frag: Fragment
    sids: List[Tuple[str, str]]               # (sid, scope) je Segment in Reihenfolge
    open: Set[Tuple[str, str]] = field(default_factory=set)
    claimed: List[str] = field(default_factory=list)   # von dieser Einheit beanspruchte Segmente (Kostenanteil)
    done: bool = False


class Scheduler:
    """Bildet Aufrufe aus den offenen Einheiten in Planreihenfolge. Jedes fehlende Segment wird genau einmal
    beansprucht (erste Einheit in Planreihenfolge); Einheiten, deren Segmente andere Aufrufe übersetzen, warten.
    Ein Aufruf enthält nur Segmente einer Sprache und eines Modells und bleibt unter der geschätzten Ausgabegrenze
    und der Prompt-Grenze."""

    def __init__(self, units: Sequence[Dict[str, Any]], frags: Dict[str, Fragment], tm: TM, terms: Terms,
                 models: Dict[str, str], max_out_tokens: int = 9000, max_prompt_bytes: int = 90000,
                 max_segments: int = 400, ratios: Optional[Dict[str, float]] = None):
        self.tm, self.terms, self.models = tm, terms, models
        self.max_out, self.max_bytes, self.max_segs = max_out_tokens, max_prompt_bytes, max_segments
        self.ratios = dict(OUT_TOKENS_PER_CHAR, **(ratios or {}))
        self.units: List[UnitState] = []
        self.claims: Dict[Tuple[str, str, str], int] = {}      # (lang, sid, scope) -> Batch-Nr. in Arbeit
        self.failed: Dict[Tuple[str, str, str], List[str]] = {}
        self.waiting: Dict[Tuple[str, str, str], List[UnitState]] = {}
        self.retry: List[Batch] = []
        # abgelehnte Segmente je (Sprache, Modell) sammeln und als volle Wiederholungsaufrufe senden
        self.pool: Dict[Tuple[str, str], List[Tuple[Claim, List[str]]]] = {}
        self.cursor = 0
        self.no = 0
        self._ready: List[UnitState] = []
        for u in units:
            f = frags[u["path"]]
            st = UnitState(u, f, [(sg.sid, tm_scope(u["lang"], sg.m, terms)) for sg in f.segs])
            self.units.append(st)

    def model_for(self, u: UnitState) -> str:
        return self.models.get(u.plan["tier"]) or DEFAULT_MODELS[u.plan["tier"]]

    def est_out(self, lang: str, de: str) -> float:
        return self.ratios.get(lang, 0.28) * len(de) + SEG_JSON_TOKENS

    def _resolved(self, lang: str, sid: str, scope: str) -> bool:
        return self.tm.get(lang, sid, scope) is not None or (lang, sid, scope) in self.failed

    def _visit(self, u: UnitState) -> List[Tuple[str, str, str, Segment]]:
        """Fehlende, nicht beanspruchte Segmente der Einheit; meldet die Einheit für alle offenen Segmente an."""
        lang = u.plan["lang"]
        todo = []
        seen: Set[Tuple[str, str]] = set()
        for sg, (sid, scope) in zip(u.frag.segs, u.sids):
            if (sid, scope) in seen:
                continue
            seen.add((sid, scope))
            k = (lang, sid, scope)
            if self._resolved(lang, sid, scope):
                continue
            u.open.add((sid, scope))
            self.waiting.setdefault(k, []).append(u)
            if k not in self.claims:
                todo.append((lang, sid, scope, sg))
        if not u.open:
            self._ready.append(u)
        return todo

    def _pool_batch(self, key: Tuple[str, str]) -> Batch:
        lang, model = key
        items = self.pool[key]
        take: List[Tuple[Claim, List[str]]] = []
        out_tok = 0.0
        while items and (not take or (out_tok + self.est_out(lang, items[0][0].de) <= self.max_out
                                      and len(take) < self.max_segs)):
            c, notes = items.pop(0)
            take.append((c, notes))
            out_tok += self.est_out(lang, c.de)
        if not items:
            del self.pool[key]
        self.no += 1
        rb = Batch(self.no, lang, model, "retry", [c for c, _ in take], attempt=2, notes={c.sid: n for c, n in take})
        for c, _ in take:
            self.claims[(lang, c.sid, c.scope)] = rb.no
        return rb.finish(self.terms)

    def _pool_full(self) -> Optional[Tuple[str, str]]:
        for key, items in self.pool.items():
            if len(items) >= self.max_segs or sum(self.est_out(key[0], c.de) for c, _ in items) >= self.max_out:
                return key
        return None

    def pooled(self) -> int:
        return sum(len(v) for v in self.pool.values())

    def next_batch(self) -> Optional[Batch]:
        if self.retry:
            return self.retry.pop(0)
        full = self._pool_full()
        if full:
            return self._pool_batch(full)
        b = self._next_new()
        if b is None and self.pool:                    # keine neue Arbeit: gesammelte Wiederholungen senden
            key = max(self.pool, key=lambda k: (len(self.pool[k]), k))
            return self._pool_batch(key)
        return b

    def _next_new(self) -> Optional[Batch]:
        batch: Optional[Batch] = None
        out_tok = 0.0
        size = PROMPT_BASE_BYTES
        while self.cursor < len(self.units):
            u = self.units[self.cursor]
            if not getattr(u, "_visited", False):
                u._pending = self._visit(u)            # type: ignore[attr-defined]
                u._visited = True                      # type: ignore[attr-defined]
            pend = u._pending                          # type: ignore[attr-defined]
            model = self.model_for(u)
            lang = u.plan["lang"]
            if pend and batch is not None and (batch.lang != lang or batch.model != model):
                break
            while pend:
                k_lang, sid, scope, sg = pend[0]
                if (k_lang, sid, scope) in self.claims or self._resolved(k_lang, sid, scope):
                    pend.pop(0)
                    continue
                need = self.est_out(lang, sg.m)
                nbytes = len(sg.m.encode("utf-8")) + 48
                if batch is not None and batch.claims and (out_tok + need > self.max_out or size + nbytes > self.max_bytes
                                                           or len(batch.claims) >= self.max_segs):
                    return self._emit(batch)
                if batch is None:
                    self.no += 1
                    batch = Batch(self.no, lang, model, u.plan["tier"], [])
                batch.claims.append(Claim(sid, scope, sg.m, sg.block, u.frag.path, u.plan["unit"]))
                self.claims[(k_lang, sid, scope)] = batch.no
                u.claimed.append(sid)
                out_tok += need
                size += nbytes
                pend.pop(0)
            self.cursor += 1
        return self._emit(batch) if batch is not None and batch.claims else None

    def _emit(self, batch: Batch) -> Batch:
        return batch.finish(self.terms)

    def complete(self, batch: Batch, accepted: Dict[str, str], failed: Dict[str, List[str]], origin: str,
                 retry: bool = True) -> None:
        """Ergebnis eines Aufrufs: angenommene Segmente in den TM, abgelehnte einmal wiederholen, sonst als
        gescheitert vermerken. Wartende Einheiten, deren Segmente nun alle aufgelöst sind, werden bereit."""
        for c in batch.claims:
            k = (batch.lang, c.sid, c.scope)
            self.claims.pop(k, None)
            if c.sid in accepted:
                self.tm.add_live(batch.lang, c.sid, c.scope, accepted[c.sid], origin)
            elif retry and batch.attempt == 1:
                self.pool.setdefault((batch.lang, batch.model), []).append(
                    (c, problem_codes(failed.get(c.sid) or ["missing"])))
                self.claims[k] = -1                    # bleibt beansprucht, bis der Sammelaufruf läuft
            else:
                self.failed[k] = failed.get(c.sid) or ["missing"]
        for c in batch.claims:
            k = (batch.lang, c.sid, c.scope)
            if k in self.claims:
                continue
            for u in self.waiting.pop(k, []):
                u.open.discard((c.sid, c.scope))
                if not u.open and not u.done:
                    self._ready.append(u)

    def abandon(self, batch: Batch) -> None:
        """Aufruf nicht gelaufen (Budget, Kontingent): Segmente freigeben; Einheiten bleiben offen."""
        for c in batch.claims:
            self.claims.pop((batch.lang, c.sid, c.scope), None)

    def abandon_pool(self) -> int:
        n = 0
        for (lang, _m), items in self.pool.items():
            for c, _ in items:
                self.claims.pop((lang, c.sid, c.scope), None)
                n += 1
        self.pool.clear()
        return n

    def requeue(self, batch: Batch) -> bool:
        """Aufruf ohne Antwort (Zeitüberschreitung, Ausnahme) einmal neu einreihen; danach freigeben."""
        if batch.attempt > 1:
            self.abandon(batch)
            return False
        self.no += 1
        rb = Batch(self.no, batch.lang, batch.model, batch.tier, list(batch.claims), attempt=2, notes=batch.notes)
        for c in rb.claims:
            self.claims[(batch.lang, c.sid, c.scope)] = rb.no
        self.retry.append(rb.finish(self.terms))
        return True

    def ready(self) -> List[UnitState]:
        out = [u for u in self._ready if not u.done]
        self._ready = []
        return out

    def assemble(self, u: UnitState) -> Tuple[Dict[int, str], List[List[str]], List[Tuple[str, List[str]]]]:
        """Übersetzungen je Segmentindex, Herkunft je Segment, gescheiterte Segmente."""
        lang = u.plan["lang"]
        tr: Dict[int, str] = {}
        origins: List[List[str]] = []
        failed: List[Tuple[str, List[str]]] = []
        for i, (sid, scope) in enumerate(u.sids):
            k = (lang, sid, scope)
            if k in self.failed:
                failed.append((sid, self.failed[k]))
                continue
            hit = self.tm.get(lang, sid, scope)
            if hit is None:
                failed.append((sid, ["missing"]))
                continue
            tr[i] = hit[0]
            origins.append([sid, hit[1]])
        return tr, origins, failed


# ==============================================================================
# Schätzung (Aufrufe, Tokens, Listenpreis, Laufzeit)
# ==============================================================================

# Gemessen im ersten vollen Lauf (Lauf 37940217154, gemini-3.8-flash-medium, 2.074 Aufrufe mit Antwort):
# Eingabe je Aufruf (ungecacht + gecacht) = 17.203 + 1,298 · deutsche Zeichen, davon 28,2 % gecacht.
IN_FIXED_TOKENS = 17203
IN_TOKENS_PER_CHAR = 1.298
CACHED_SHARE = 0.282
# Denk-Tokens je Aufruf nach Stufe: medium gemessen (Mittel 13.037); low gemessen 0 (Verteilung, effort low);
# high und Pro: Annahme.
THINKING = {"low": 0, "medium": 13037, "high": 26000, "max": 40000}
# Dauer je Aufruf bei 16 parallelen Aufrufen (Flash, gemessen aus den Zeitstempeln: 6,7 s + Ausgabe/470 Tokens/s,
# Ausgabe einschließlich Denken); Pro: Annahme.
LATENCY = {"flash": {"base_s": 6.7, "tok_s": 470.0}, "pro": {"base_s": 10.0, "tok_s": 110.0}}


def thinking_for(model: str) -> int:
    return THINKING.get(model_effort(model, "medium"), THINKING["medium"])


def latency_class(model: str) -> str:
    return "pro" if "pro" in model_base(model) else "flash"


def estimate(units: Sequence[Dict[str, Any]], frags: Dict[str, Fragment], tm: TM, terms: Terms,
             models: Dict[str, str], max_out_tokens: int = 9000, concurrencies: Sequence[int] = (4, 6, 8, 16, 24),
             retry_rate: float = 0.05) -> Dict[str, Any]:
    """Aufrufe, Tokens (mit Denken), Listenpreis und Dauer durch Simulation der Aufrufbildung; Kennzahlen je Aufruf
    aus dem ersten vollen Lauf (``IN_*``, ``OUT_TOKENS_PER_CHAR``, ``THINKING``, ``LATENCY``). ``retry_rate``: Anteil
    zusätzlicher Aufrufe (gemessen: 5,7 % Aufrufe ohne angenommenes Segment; Ablehnungen werden gesammelt)."""
    sch = Scheduler(units, frags, tm.copy(), terms, models, max_out_tokens)
    by_model: Dict[str, Dict[str, float]] = {}
    while True:
        b = sch.next_batch()
        if b is None:
            break
        vis = sum(sch.est_out(b.lang, c.de) for c in b.claims)
        think = thinking_for(b.model)
        inp = IN_FIXED_TOKENS + IN_TOKENS_PER_CHAR * b.de_chars
        lc = LATENCY[latency_class(b.model)]
        m = by_model.setdefault(b.model, {"calls": 0, "input": 0.0, "cached": 0.0, "output": 0.0, "thinking": 0.0,
                                          "call_s": 0.0, "segments": 0, "de_chars": 0, "prompt_bytes_max": 0})
        m["calls"] += 1
        m["input"] += inp * (1 - CACHED_SHARE)
        m["cached"] += inp * CACHED_SHARE
        m["output"] += vis + think                     # wie agy: Ausgabe einschließlich Denken
        m["thinking"] += think
        m["call_s"] += lc["base_s"] + (vis + think) / lc["tok_s"]
        m["segments"] += len(b.claims)
        m["de_chars"] += b.de_chars
        m["prompt_bytes_max"] = max(m["prompt_bytes_max"], len(b.prompt.encode("utf-8")))
        sch.complete(b, {c.sid: c.de for c in b.claims}, {}, "estimate")
    tot = {"calls": 0, "usd": 0.0, "call_s": 0.0, "input": 0, "cached": 0, "output": 0, "thinking": 0}
    for model, m in by_model.items():
        f = 1.0 + retry_rate
        for k in ("calls", "input", "cached", "output", "thinking", "call_s"):
            m[k] *= f
        m["usd"] = list_price(model, {"input": int(m["input"]), "cached": int(m["cached"]), "output": int(m["output"]),
                                      "thinking": int(m["thinking"])})
        m["chars_per_call"] = round(m["de_chars"] / max(1, m["calls"] / f))
        for k in ("calls", "usd", "call_s", "input", "cached", "output", "thinking"):
            tot[k] += m[k]
    wall = {str(c): round(tot["call_s"] / c / 3600, 2) for c in concurrencies}
    return {"by_model": {k: {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                         for k, v in by_model.items()},
            "calls": round(tot["calls"]), "list_price_usd": round(tot["usd"], 2),
            "tokens": {"input": round(tot["input"]), "cached": round(tot["cached"]), "output": round(tot["output"]),
                       "thinking": round(tot["thinking"])},
            "call_hours": round(tot["call_s"] / 3600, 2), "wall_hours": wall,
            "units": len(units), "max_out_tokens": max_out_tokens, "retry_rate": retry_rate,
            "price_basis": PRICE_BASIS}


# ==============================================================================
# Befunde
# ==============================================================================

def translation_finding(unit: Dict[str, Any], problems: List[Tuple[str, List[str]]], cls: str, run: str,
                        at: Optional[str] = None) -> Dict[str, Any]:
    at = at or utc_now()
    path, lang = unit["path"], unit["lang"]
    codes = sorted({c for _, ps in problems for c in problem_codes(ps)})
    claim = f"Übersetzung nach {lang} verworfen ({', '.join(codes) or 'unbekannt'})."
    ev = [{"type": "text-passage", "ref": f"{path}#{sid}@{lang}", "excerpt": ", ".join(ps)[:300]}
          for sid, ps in problems[:5]]
    subject = {"kind": "module-guide" if unit["tier"] == "guide" else "element-guide", "id": f"{path}@{lang}"}
    return fnd.make(subject, cls, claim, ev, {"type": "regenerate", "patch": {"recipe": RECIPE_ID}},
                    fnd.source("validator", "translation-check", 0.9, run, at), "mittel")


# ==============================================================================
# Kette live/translation
# ==============================================================================

CHAIN_DIR = "live/translation"
LOG_DIR = CHAIN_DIR + "/log"
POINTER = CHAIN_DIR + "/latest.json"
STATUS_FILE = "status/translation.json"
POINTER_SCHEMA = "live-pointer@v1"
ENTRY_SCHEMAS = {"translation": "live-translation@v1", "tm": "live-tm@v1", "finding": "live-finding@v1",
                 "run": "live-translation-run@v1"}
REQUIRED = {
    "translation": ("unit", "unit_key", "lang", "path", "source_sha256", "output_sha256", "segments", "models",
                    "list_price_usd", "run", "at"),
    "tm": ("lang", "segments", "model", "profile", "list_price_usd", "run", "at"),
    "finding": ("finding", "unit", "unit_key", "run", "at"),
    "run": ("run", "at"),
}
_SEGMENT_NAME = re.compile(r"^(\d{8})\.jsonl$")
# Ein voller Lauf schreibt mehrere zehn MB (Übersetzungen im TM); GitHub weist Dateien über 100 MB ab. Ein Lauf beginnt
# deshalb ab 16 MB ein neues Segment (Name = erste seq); die Prüfung verlangt nur lückenlose Folge.
SEGMENT_MAX_BYTES = 16 * 1024 * 1024


class ChainError(RuntimeError):
    pass


def entry_hash(entry: Dict[str, Any]) -> str:
    return obj_hash({k: v for k, v in entry.items() if k != "hash"})


def seal(body: Dict[str, Any], parent: Optional[Dict[str, Any]]) -> Dict[str, Any]:
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
    """Ganze Kette prüfen (wie live_core.verify_chain); zusätzlich: Übersetzungsglieder verweisen nur auf frühere
    TM-Glieder."""
    root = Path(root)
    errors: List[str] = []
    entries: List[Dict[str, Any]] = []
    names: List[str] = []
    prev: Optional[Dict[str, Any]] = None
    tm_hashes: Set[str] = set()
    for seg in segment_files(root):
        names.append(seg.name)
        m = _SEGMENT_NAME.match(seg.name)
        if not m:
            errors.append(f"{seg.name}: unerwartete Datei im Protokoll")
            continue
        expected = (int(prev["seq"]) + 1) if prev else 1
        if int(m.group(1)) != expected:
            errors.append(f"{seg.name}: Segment beginnt bei {int(m.group(1))}, erwartet {expected}")
        raw = seg.read_bytes()
        if not raw:
            errors.append(f"{seg.name}: leeres Segment")
            continue
        if not raw.endswith(b"\n"):
            errors.append(f"{seg.name}: letzte Zeile unvollständig")
        for n, line in enumerate(raw.split(b"\n"), 1):
            if not line.strip():
                continue
            loc = f"{seg.name}:{n}"
            try:
                e = json.loads(line)
            except ValueError as exc:
                errors.append(f"{loc}: kein JSON ({exc})")
                continue
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
            if e.get("parent_hash") != (prev["hash"] if prev else None):
                errors.append(f"{loc}: parent_hash passt nicht zum vorigen Glied")
            if e.get("hash") != entry_hash(e):
                errors.append(f"{loc}: hash stimmt nicht (Glied verändert)")
            if kind == "tm" and isinstance(e.get("hash"), str):
                tm_hashes.add(e["hash"][:12])
            if kind == "translation":
                for pair in e.get("segments") or []:
                    o = pair[1] if isinstance(pair, list) and len(pair) == 2 else ""
                    if o.startswith("tm:") and o[3:] not in tm_hashes:
                        errors.append(f"{loc}: Segment verweist auf unbekanntes TM-Glied {o[3:]}")
                        break
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
    if not anchor or not anchor.get("hash"):
        return True
    seq = int(anchor.get("seq") or 0)
    return 0 < seq <= len(state.entries) and state.entries[seq - 1]["hash"] == anchor["hash"]


def decided_keys(entries: Iterable[Dict[str, Any]]) -> Set[str]:
    """Erledigt: Übersetzungsglied oder Befund mit dem Schlüssel der Einheit (verworfene Übersetzung bleibt
    geschlossen, bis sich Quelle, Rezept oder Begriffe ändern; ``--retry-findings`` öffnet sie)."""
    return {e["unit_key"] for e in entries if e.get("unit_key") and (
        e.get("kind") == "translation"
        or (e.get("kind") == "finding" and int(e.get("checks") or 1) >= CHECKS_VERSION))}


def latest_translations(entries: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        if e.get("kind") == "translation":
            out[e["unit"]] = e
    return out


class TranslationLog:
    """Protokoll in einem Arbeitsbaum von ``autodocs-live`` (je Lauf ein neues Segment, Zeile für Zeile auf die
    Platte, nie verändert); ``live/translation/latest.json`` ist der einzige bewegliche Zeiger."""

    def __init__(self, root: Path, allow_invalid: bool = False):
        self.root = Path(root)
        self.state = verify_chain(self.root)
        if not self.state.ok and not allow_invalid:
            raise ChainError("Kette ungültig: " + "; ".join(self.state.errors[:5]))
        self.entries: List[Dict[str, Any]] = list(self.state.entries)
        self._segment: Optional[Path] = None
        self._bytes = 0
        self.max_segment_bytes = SEGMENT_MAX_BYTES

    @property
    def head(self) -> Optional[Dict[str, Any]]:
        return self.entries[-1] if self.entries else None

    def append(self, body: Dict[str, Any]) -> Dict[str, Any]:
        kind = body.get("kind")
        if kind not in ENTRY_SCHEMAS:
            raise ChainError(f"unbekannte Gliedart {kind!r}")
        body = dict(body, schema=ENTRY_SCHEMAS[kind])
        missing = [f for f in REQUIRED[kind] if f not in body]
        if missing:
            raise ChainError(f"Pflichtfelder fehlen: {', '.join(missing)}")
        e = seal(body, self.head)
        line = canonical(e) + b"\n"
        if self._segment is not None and self._bytes and self._bytes + len(line) > self.max_segment_bytes:
            self._segment = None
        if self._segment is None:
            d = self.root / LOG_DIR
            d.mkdir(parents=True, exist_ok=True)
            self._segment = d / f"{e['seq']:08d}.jsonl"
            self._bytes = 0
            if self._segment.exists():
                raise ChainError(f"Segment {self._segment.name} existiert bereits")
        with open(self._segment, "ab") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        self._bytes += len(line)
        self.entries.append(e)
        return e

    def write_pointer(self, run: str, basis: Optional[str] = None) -> Optional[Dict[str, Any]]:
        head = self.head
        if head is None:
            return None
        seg = self._segment.name if self._segment else (self.state.segments[-1] if self.state.segments else "")
        ptr = {"schema": POINTER_SCHEMA, "chain": "translation", "hash": head["hash"], "hash12": head["hash"][:12],
               "seq": head["seq"], "head_of": head["seq"], "segment": f"log/{seg}", "at": head["at"],
               "reason": {"kind": "translation", "ref": run}, "basis": basis}
        write_atomic(self.root / POINTER, (json.dumps(ptr, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode())
        return ptr


def repair_tail(segment: Path) -> int:
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


# ==============================================================================
# Bündel
# ==============================================================================

BUNDLE_SCHEMA = "live-translation-bundle@v1"
BUNDLE_MEMBERS = ("manifest.json", "fragments.jsonl", "tm.jsonl", "terms.json", "plan.jsonl", "live_head.json")
CODE_FILES = ("live_translate_core.py", "findings.py")
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
    unknown = sorted(set(files) - set(BUNDLE_MEMBERS))
    if unknown:
        raise BundleError(f"nicht vorgesehene Bündel-Dateien: {', '.join(unknown)}")
    missing = [n for n in BUNDLE_MEMBERS if n != "manifest.json" and n not in files]
    if missing:
        raise BundleError(f"Bündel unvollständig: {', '.join(missing)}")
    man = dict(manifest, schema=BUNDLE_SCHEMA, files={})
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
            ti.size, ti.mtime, ti.mode, ti.uid, ti.gid = len(data), int(mtime), 0o644, 0, 0
            ti.uname = ti.gname = ""
            tar.addfile(ti, io.BytesIO(data))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name("." + out.name + ".tmp")
    with open(tmp, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
            gz.write(buf.getvalue())
    os.replace(tmp, out)
    return {"path": str(out), "sha256": file_sha256(out), "bytes": out.stat().st_size,
            "raw_bytes": sum(len(v) for v in payload.values()), "manifest": man, "manifest_hash": sha256_hex(man_bytes)}


@dataclass
class Bundle:
    directory: Path
    manifest: Dict[str, Any]
    sha256: str = ""

    def path(self, name: str) -> Path:
        return self.directory / name

    def rows(self, name: str) -> Iterator[Dict[str, Any]]:
        return read_jsonl(self.path(name))

    @property
    def manifest_hash(self) -> str:
        return file_sha256(self.path("manifest.json"))

    def live_head(self) -> Optional[Dict[str, Any]]:
        return json.loads(self.path("live_head.json").read_text(encoding="utf-8")) or None

    def terms(self) -> Terms:
        return Terms.from_json(json.loads(self.path("terms.json").read_text(encoding="utf-8")))

    def fragments(self) -> Dict[str, Fragment]:
        return {r["path"]: Fragment.from_row(r) for r in self.rows("fragments.jsonl")}

    def tm(self) -> TM:
        tm = TM()
        for r in self.rows("tm.jsonl"):
            tm.add_register(r["lang"], r["sid"], r["t"])
        return tm


def open_bundle(archive: Path, dest: Path, expected_sha256: Optional[str] = None) -> Bundle:
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
