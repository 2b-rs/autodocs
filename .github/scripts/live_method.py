#!/usr/bin/env python3
"""Verteilungsmethode der Live-Schicht: Vorauswahl, Prompt, Antwortschema, Gatekeeper und Planung.

Eigenständig (Standardbibliothek und ``live_core``), wird mit ``live_core.py`` in das öffentliche Repo kopiert.
Die Methode ist die vermessene von ``cached_sweep_runner.py`` (``--method retrieve --scope global --retrieve-k 20``,
Snippets zuerst, ``--auto-cited``, milde Release-Regel, verdichtete Katalogzeilen) mit zwei Ergänzungen:

1. **Außenwirkung je Einheit (CONCEPT-0060 §6.7).** Jedes Snippet, jede Schaubild-Reihe und jedes Element bekommt
   eine bewusste Entscheidung ``external_effect`` mit betroffenen Modulen und Begründung. Nennt das Modell Module,
   aus denen kein Kandidat vorlag, folgt Stufe 2 mit Kandidaten genau aus diesen Modulen.
2. **Beziehungsart je Zuordnung** (``relation_type``).

Die Bausteine ``lexical_tokens``, ``caveman``, ``LexicalIndex``, ``retrieve_candidates`` und der Prompt sind aus dem
Runner übernommen; ``test_live_distribution`` prüft sie gegen das Original (gleiche Kandidaten, gleicher Prompt ohne
die Ergänzungen). Abweichung: Zitate werden je Einheit vorab aus dem vollen Text bestimmt (``cited``), die
Gegenrichtung erkennt Zitate über genaue IDs statt über Teilzeichenketten.
"""
from __future__ import annotations

import heapq
import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import live_core as core

# ==============================================================================
# Releases (wie cached_sweep_runner.RELEASE_TO_BIT, nur die Namen der Datenstände)
# ==============================================================================

RELEASES = ("R1.0.0", "R1.1.0", "R1.2.0", "R1.3.0", "R1.4.0", "R1.5.1", "R2.1.20", "R3.0.7", "R3.1.5", "R3.2.3",
            "R4.0.3", "R4.1.3", "R4.2.2", "R4.3.1", "R4.4.0", "R17-03", "R17-10", "R18-03", "R18-10", "R18.10.1",
            "R19-03", "R19-11", "R20-11", "R21-11", "R22-11", "R23-11", "R24-11", "R25-11")
ALL_MASK = 0xFFFFFFFF_FFFFFFFF
_REL_ALIASES: Dict[str, int] = {}
for _bit, _name in enumerate(RELEASES):
    _REL_ALIASES[_name] = _bit
    _REL_ALIASES[_name[1:]] = _bit
    if re.match(r"^R\d\d-\d\d$", _name):
        _REL_ALIASES[_name[1:].replace("-", ".")] = _bit
for _alias, _bit in (("R1.5.0", 5), ("1.5.0", 5), ("1.0", 0), ("1.1", 1), ("1.2", 2), ("1.3", 3), ("1.4", 4),
                     ("1.5", 5), ("2.1", 6), ("R2.1", 6), ("3.0", 7), ("R3.0", 7), ("3.1", 8), ("R3.1", 8),
                     ("3.2", 9), ("R3.2", 9), ("4.0", 10), ("R4.0", 10), ("4.1", 11), ("R4.1", 11), ("4.2", 12),
                     ("R4.2", 12), ("4.3", 13), ("R4.3", 13), ("4.4", 14), ("R4.4", 14)):
    _REL_ALIASES[_alias] = _bit


def release_mask(releases: Iterable[str]) -> int:
    mask = 0
    for r in releases:
        clean = str(r).strip()
        bit = _REL_ALIASES.get(clean)
        if bit is None and clean[:1] in ("R", "r"):
            bit = _REL_ALIASES.get(clean[1:])
        if bit is not None:
            mask |= 1 << bit
    return mask


def newest_release(mask: int) -> str:
    if not mask or mask == ALL_MASK:
        return RELEASES[-1]
    return RELEASES[min(mask.bit_length() - 1, len(RELEASES) - 1)]


# ==============================================================================
# Einheiten: Records (Korpus) und Snippet-artige Einträge
# ==============================================================================

@dataclass
class Record:
    """Ein Element des Element-Stores (``versions/data``) im Korpus."""
    id: str
    platform: str          # ap | cp | fo
    module: str
    kind: str
    mask: int
    text: str              # (normative_text or content)[:1200] wie LexicalIndex
    line: str              # Katalogzeile ``ID | kind | text`` (verdichtet, 300 Zeichen)
    doc: str = ""          # _doc_core(source_pdf)
    page: int = 0
    h: str = ""

    @classmethod
    def from_row(cls, r: Dict[str, Any]) -> "Record":
        return cls(r["id"], r["p"], r["m"], r["k"], int(r["mask"], 16), r["text"], r["line"], r.get("doc", ""),
                   int(r.get("pg") or 0), r.get("h", ""))


@dataclass
class Item:
    """Snippet oder Schaubild-Reihe als Einheit des Lese-Schritts."""
    id: str
    platform: str
    module: str
    doc: str
    page: int
    refs: List[str]
    cited: List[str]       # zitierte IDs aus dem vollen Text (Referenzen und IDs im Text)
    text: str              # höchstens METHOD["snippet_chars"] Zeichen
    mask: int = ALL_MASK
    is_figure: bool = False
    is_table: bool = False
    caption: str = ""

    @classmethod
    def from_snippet_row(cls, r: Dict[str, Any]) -> "Item":
        return cls(r["id"], r["p"], r.get("mod", ""), r.get("doc", ""), int(r.get("page") or 0), list(r.get("refs") or []),
                   list(r.get("cited") or []), r.get("text", ""), int(r.get("mask", "0x" + "F" * 16), 16),
                   bool(r.get("fig")), bool(r.get("tab")), r.get("cap", ""))


ID_IN_TEXT = re.compile(r"\b(?:SWS|RS|PRS|TPS|SRS|AP|ECUC|CONSTR)_[A-Za-z0-9_]*\d[A-Za-z0-9_]*")


def cited_ids(refs: Sequence[str], full_text: str) -> List[str]:
    return list(dict.fromkeys(list(refs) + ID_IN_TEXT.findall(full_text or "")))


def figure_text(row: Dict[str, Any]) -> str:
    """Lesetext einer Schaubild-Reihe aus ``figure_texts.jsonl`` (wie load_figure_items: Beschriftung, Bildtexte,
    Kurzfassung der Beschreibung)."""
    return " ".join(x for x in (row.get("caption") or "", ("Labels: " + row["labels"]) if row.get("labels") else "",
                                ("Description: " + row["description"]) if row.get("description") else "") if x)


def figure_platform(row: Dict[str, Any]) -> str:
    doc = str(row.get("doc") or "")
    if re.search(r"(?:^|_)(?:AP|Adaptive)(?:_|[A-Z]|$)", doc) or "Adaptive" in doc:
        return "ap"
    if re.search(r"(?:^|_)FO(?:_|$)", doc):
        return "fo"
    return "cp"


def item_from_figure(row: Dict[str, Any], platform: Optional[str] = None) -> Item:
    text = figure_text(row)
    rels = row.get("releases") or []
    return Item(row["figure_id"], platform or figure_platform(row), "figure", str(row.get("doc") or ""),
                int(row.get("page") or 0), [], cited_ids([], text), text[:core.METHOD["snippet_chars"]],
                release_mask(rels) if rels else ALL_MASK, True, False, str(row.get("caption") or ""))


def item_payload(it: Item, max_chars: int, with_module: bool = False) -> Dict[str, Any]:
    """Snippet für den Prompt (wie snippet_payload des Runners, ohne Maskierung)."""
    p: Dict[str, Any] = {"id": it.id, "doc": it.doc, "page": it.page, "refs": list(it.refs), "text": it.text[:max_chars]}
    if with_module:
        p["mod"] = it.module
    return p


def item_hash(it: Item) -> str:
    """Hash dessen, was das Modell von der Einheit sieht (Text, Referenzen, Modul), plus Zitate und Releases."""
    return core.obj_hash({"p": item_payload(it, core.METHOD["snippet_chars"], with_module=True), "cited": it.cited,
                          "mask": f"0x{it.mask:X}"})


def record_hash(r: Record) -> str:
    return core.obj_hash({"id": r.id, "k": r.kind, "m": r.module, "mask": f"0x{r.mask:X}", "line": r.line, "text": r.text})


# ==============================================================================
# Lexikalische Vorauswahl (aus cached_sweep_runner, Ergebnis identisch)
# ==============================================================================

_STOPWORDS = set("""a an the of to in on for and or is are be been being by with as at from that this these those
it its shall should may can must will not no if then than which who whom whose when where while into onto via per
such any all each every other another same also only both either neither nor so do does did done has have had
having was were there their them they he she we you your our i me my mine upon within without between among about
above below under over after before during since until through across against along around beyond toward towards
e g i e etc see figure table chapter section page document id autosar specification""".split())
_HTML_ENT = re.compile(r"&(?:amp;)*(lt|gt|amp|quot|apos|nbsp);")
_BOILER = [re.compile(p) for p in (
    r"Upstream(?: requirements)?\s*:\s*(?:(?:RS|SRS|FO_RS|RS_AP|SWS|PRS|TPS)_[A-Za-z0-9_\-]+\s*,?\s*)+",
    r"Header-Datei\s+#include\s+\"[^\"]*\"", r"\bclass mono\b", r"Literaturverzeichnis[^.]*\.",
    r"Specification of [A-Z][A-Za-z ]+ AUTOSAR (?:AP|CP) R\d\d-\d\d", r"\d+ of \d+ Document ID \d+:\s*\S+",
    r"Status: DRAFT", r"[⌈⌋]",
)]


def caveman(text: str) -> str:
    t = _HTML_ENT.sub(lambda m: {"lt": "<", "gt": ">", "amp": "&", "quot": '"', "apos": "'", "nbsp": " "}[m.group(1)], text)
    for rx in _BOILER:
        t = rx.sub(" ", t)
    t = t.replace("{<hierarchical-namespace-list- lower-proxy>}", "NS").replace("{<hierarchical-namespace-list- lower-skeleton>}", "NS")
    t = re.sub(r"\{<hierarchical-[a-z\- ]+>\}", "NS", t)
    out = []
    for w in t.split():
        core_w = w.strip(".,;:()[]\"'").lower()
        if core_w in _STOPWORDS and not any(ch in w for ch in "_:<>(){}"):
            continue
        out.append(w)
    return " ".join(out)


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def lexical_tokens(text: str) -> List[str]:
    toks: List[str] = []
    for m in _TOKEN_RE.finditer(text):
        w = m.group(0)
        lw = w.lower()
        if len(lw) < 2 or lw in _STOPWORDS:
            continue
        toks.append(lw)
        parts = [p for p in re.split(r"_|(?<=[a-z0-9])(?=[A-Z])", w) if p]
        if len(parts) > 1:
            toks.extend(p.lower() for p in parts if len(p) > 2 and p.lower() not in _STOPWORDS)
    return toks


def doc_core(name: str) -> str:
    n = (name or "").rsplit("/", 1)[-1]
    if n.lower().endswith(".pdf"):
        n = n[:-4]
    return re.sub(r"^(?:AUTOSAR_|CP_|AP_|FO_)+", "", n).lower()


KIND_CODES = {"requirement": "req", "api-function": "fn", "api-class": "cls", "api-type": "typ",
              "api-enumeration": "enu", "api-variable": "var", "api-serviceinterface": "si",
              "api-implementationdatatype": "idt", "api-struct": "str", "api-constant": "cst", "api-method": "mth",
              "api-typedef": "tdf"}


def kind_code(kind: str) -> str:
    if kind in KIND_CODES:
        return KIND_CODES[kind]
    k = kind.replace("api-", "")
    return k[:3] or "rec"


def record_line(record_id: str, kind: str, text: str, max_chars: int = 300) -> str:
    """Katalogzeile wie cached_sweep_runner.record_line(compact=True, short_kind=True)."""
    return f"{record_id} | {kind_code(kind or 'requirement')} | {caveman(' '.join(text.split()))[:max_chars]}"


class LexicalIndex:
    """BM25 über (Art, Text) wie im Runner. Die Termgewichte werden beim Aufbau vorberechnet; dieselbe Folge von
    Gleitkommaoperationen ergibt dieselben Werte und dieselbe Rangfolge."""

    def __init__(self, docs: Sequence[Tuple[str, str, str, int]], k1: float = 1.2, b: float = 0.75, max_chars: int = 1200):
        """docs: (id, kind, text, Seite) mit text bereits gekürzt oder ungekürzt (hier auf max_chars gekürzt);
        Seiten-Nachbarn über (doc, page) liefert ``by_page``."""
        self.ids = [d[0] for d in docs]
        self.k1, self.b = k1, b
        tfs: List[Dict[str, int]] = []
        df: Dict[str, int] = {}
        lens = []
        for _id, kind, text, _pg in docs:
            tf: Dict[str, int] = {}
            for t in lexical_tokens(f"{kind} {text[:max_chars]}"):
                tf[t] = tf.get(t, 0) + 1
            tfs.append(tf)
            lens.append(sum(tf.values()))
            for t in tf:
                df[t] = df.get(t, 0) + 1
        n = max(1, len(docs))
        self.avgdl = (sum(lens) / n) if lens else 1.0
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.post: Dict[str, List[Tuple[int, float]]] = {}
        for i, tf in enumerate(tfs):
            for t, f in tf.items():
                idf = self.idf[t]
                denom = f + self.k1 * (1 - self.b + self.b * lens[i] / self.avgdl)
                self.post.setdefault(t, []).append((i, idf * f * (self.k1 + 1) / denom))
        self.by_page: Dict[Tuple[str, int], List[str]] = {}

    def search(self, text: str, k: int) -> List[Tuple[str, float]]:
        q: Dict[str, int] = {}
        for t in lexical_tokens(text):
            q[t] = q.get(t, 0) + 1
        scores: Dict[int, float] = {}
        for t, qf in q.items():
            if not self.idf.get(t):
                continue
            m = min(qf, 3)
            for i, w in self.post[t]:
                scores[i] = scores.get(i, 0.0) + w * m
        ids = self.ids
        top = heapq.nsmallest(k, scores.items(), key=lambda x: (-x[1], ids[x[0]]))
        return [(ids[i], round(sc, 3)) for i, sc in top]


def record_index(records: Sequence[Record]) -> LexicalIndex:
    idx = LexicalIndex([(r.id, r.kind, r.text, r.page) for r in records])
    for r in records:
        if r.doc and r.page:
            idx.by_page.setdefault((r.doc, int(r.page)), []).append(r.id)
    return idx


def item_index(items: Sequence[Item], max_chars: int = 2000) -> LexicalIndex:
    """Snippet-Index für die Gegenrichtung (wie SnippetIndex des Runners: Art leer, Text bis 2000 Zeichen)."""
    return LexicalIndex([(it.id, "", it.text[:max_chars], 0) for it in items], max_chars=max_chars)


def retrieve_candidates(index: LexicalIndex, items: Sequence[Item], k: int, max_chars: int = 4000,
                        chunk: int = 400, page_cap: int = 12, known: Optional[Set[str]] = None) -> Dict[str, List[str]]:
    """Kandidaten je Einheit wie im Runner: zitierte IDs im Katalog, Records derselben PDF-Seite, dann BM25 bis K
    (Ganztext und Abschnitte im Wechsel)."""
    known = set(index.ids) if known is None else known
    out: Dict[str, List[str]] = {}
    for s in items:
        text = s.text[:max_chars]
        cands: List[str] = [c for c in s.cited if c in known]
        if index.by_page and s.doc and s.page:
            core_doc = doc_core(s.doc)
            for pg in (s.page, s.page + 1, s.page - 1):
                for rid in index.by_page.get((core_doc, pg), [])[:page_cap]:
                    if rid not in cands:
                        cands.append(rid)
        ranked: List[str] = [rid for rid, _ in index.search(text, k + len(cands))]
        if len(text) > chunk * 1.5:
            # die Top-K einer Suche sind der Anfang der Top-(K+n) derselben Suche (totale Ordnung nach Wert, ID):
            # der Runner sucht hier ein zweites Mal, das Ergebnis ist dasselbe
            whole = ranked[:k]
            parts = [text[i:i + chunk] for i in range(0, len(text), chunk)]
            per = max(3, k // len(parts))
            for part in parts:
                ranked.extend(rid for rid, _ in index.search(part, per))
            chunked = [r for r in ranked[len(whole) + len(cands):]]
            ranked = [x for pair in zip(whole, chunked) for x in pair] + whole[len(chunked):] + chunked[len(whole):]
        added = 0
        for rid in ranked:
            if added >= k:
                break
            if rid not in cands:
                cands.append(rid)
                added += 1
        out[s.id] = cands
    return out


def reverse_candidates(index: LexicalIndex, records: Sequence[Record], citers: Dict[str, List[str]], k: int) -> Dict[str, List[str]]:
    """Kandidaten-Snippets je Element: Snippets, die die ID zitieren, dann BM25 über den Elementtext."""
    out: Dict[str, List[str]] = {}
    for r in records:
        cands: List[str] = list(dict.fromkeys(citers.get(r.id, [])))
        added = 0
        for sid, _ in index.search(f"{r.kind} {r.text[:1200]}", k + len(cands)):
            if added >= k:
                break
            if sid not in cands:
                cands.append(sid)
                added += 1
        out[r.id] = cands
    return out


# ==============================================================================
# Prompt und Antwortschema
# ==============================================================================

PROMPT_INSTRUCTIONS = """You assign documentation snippets to AUTOSAR specification records.

Below is the COMPLETE record catalogue of one universe, one JSON object per line:
{"id": record id, "mod": module, "rel": release bitmask, "text": normative text (truncated)}.
After the catalogue follows a batch of snippets (verbatim text from AUTOSAR PDFs, one JSON object per line):
{"id": snippet id, "doc": source document, "page": page, "refs": record ids cited verbatim in the text, "text": the text}.

Task: for EVERY snippet in the batch, list the catalogue records the snippet is evidence for or
directly specifies, explains, constrains or illustrates. Rules:
- Use only record ids that appear in the catalogue. Never invent ids.
- A snippet may match zero, one or several records. Prefer precision: list a record only if the snippet's
  content concerns that record's requirement (same API, type, state, parameter, behaviour), not merely the
  same module. Table-of-contents lines, headers, footers and boilerplate match nothing.
- Ids cited verbatim in the snippet (refs) are strong candidates but must also exist in the catalogue.
- Citation lists: if a snippet is mainly a list of cited record ids (an index, a "see also" or cross-reference list,
  a list of requirements returned/affected), assign EVERY cited id that exists in the catalogue, confidence 1.0,
  rationale starting with "EXPLICIT_REFERENCE". This rule overrides the table-of-contents rule above.
- confidence: 0.0-1.0 (1.0 = the snippet is literally the record text or cites it; 0.6 = plausible but
  indirect). rationale: one short line naming the shared concept.
- Do not use any tools, do not read files, do not search. Answer only with the JSON object matching the
  schema: {"assignments": [{"snippet_id": ..., "matches": [{"record_id": ..., "confidence": ..., "rationale": ...}]}]}.
  Include every snippet id of the batch exactly once, with "matches": [] when nothing fits.
"""

RETRIEVE_INTRO = ("Below is a PRESELECTED part of the record catalogue (records chosen lexically for this batch), one record "
                  "per line: `RECORD_ID | kind | text`. Each snippet lists its preselected candidate ids in \"cand\"; the "
                  "right records are usually among them, but judge every candidate by its text.")

NO_TOOLS_RULE = ("Werkzeuge sind nicht erlaubt: keine Dateien lesen oder schreiben, keine Skripte, keine Suche im "
                 "Arbeitsverzeichnis. Der Prompt enthält alles. Antworte direkt mit dem JSON.\n")
STRICT_RETRY_RULE = ("STRENG: Im vorigen Versuch wurden verbotene Werkzeuge benutzt. Benutze KEIN Werkzeug. Keine Befehle, "
                     "keine Dateisuche, keine Transkripte. Antworte nur mit dem JSON.\n")

EFFECT_RULES = """
Two additions are stored for every snippet and read by later runs instead of being re-decided:
- EXTERNAL EFFECT: decide deliberately. "external_effect" is true when the snippet's content reaches beyond its own
  module ("mod"; for figures the module the document "doc" specifies): it specifies, constrains or uses an interface,
  data, timing or behaviour of OTHER modules (callers, callees, providers, consumers). It is false when the snippet
  only concerns its own module's internals, or is boilerplate. "effect_modules": the other modules affected, as the
  module abbreviations used in record ids (PduR for SWS_PduR_*, CanIf, Com, CM for SWS_CM_*, CORE, ...), [] when
  external_effect is false. "effect_rationale": at most 15 words.
- RELATION TYPE: every match carries "relation_type", one of API_IMPLEMENTATION (specifies or implements the record's
  API, type or behaviour), EXPLICIT_REFERENCE (cites the record), ARCHITECTURAL_CONTEXT (places it in the
  architecture), SEQUENCE_FLOW (call sequence, timing, state flow), PARAMETER_CONSTRAINT (limits, configuration,
  formulas), EXCEPTION_HANDLING (errors, recovery), CALLER_CONTRACT (preconditions another module must meet),
  EXPLAINS_RATIONALE (motivation).
The JSON object therefore carries per snippet also "external_effect", "effect_modules", "effect_rationale", and per
match also "relation_type".
"""

STAGE2_RULES = """
STAGE 2: in an earlier answer you stated that the snippets below affect other modules. The catalogue part below
contains candidate records from exactly those modules. List only matches among these candidates; repeat your
external effect decision unchanged.
"""

REVERSE_INSTRUCTIONS = """You assign AUTOSAR specification records to documentation snippets (the reverse direction).
Below are the RECORDS to place (new or changed), one per line `RECORD_ID | kind | text`, and after them a pool of
CANDIDATE snippets (verbatim text from AUTOSAR PDFs, preselected lexically), one JSON object per line
{"id": snippet id, "doc": document, "page": page, "text": text}.
Task: for EVERY record, list the candidate snippets that are evidence for it, i.e. snippets that specify, explain,
constrain, illustrate or explicitly cite that record (same API, type, state, parameter, behaviour), not merely the
same module. Prefer precision. A record may match zero or several snippets. Use only snippet ids from the pool.
confidence 0.0-1.0; rationale: one short line. Answer only with the JSON object
{"assignments": [{"record_id": ..., "matches": [{"snippet_id": ..., "confidence": ..., "rationale": ...}]}]},
every record id exactly once, "matches": [] when nothing fits.
"""

REVERSE_EFFECT_RULES = """
Two additions are stored for every record and read by later runs instead of being re-decided:
- EXTERNAL EFFECT: decide deliberately. "external_effect" is true when the record (an API function, type, class,
  enumeration, method, variable or requirement) is part of an interface that other modules use, provide, call,
  configure or observe across a module boundary; false when it is internal to its own module. "effect_modules": the
  other modules involved, as the module abbreviations used in record ids, [] when false. "effect_rationale": at most
  15 words.
- RELATION TYPE: every match carries "relation_type", one of API_IMPLEMENTATION, EXPLICIT_REFERENCE,
  ARCHITECTURAL_CONTEXT, SEQUENCE_FLOW, PARAMETER_CONSTRAINT, EXCEPTION_HANDLING, CALLER_CONTRACT, EXPLAINS_RATIONALE.
The JSON object therefore carries per record also "external_effect", "effect_modules", "effect_rationale", and per
match also "relation_type".
"""

_MATCH_PROPS = {"confidence": {"type": "number"}, "rationale": {"type": "string"}, "relation_type": {"type": "string"}}


def _schema(unit_field: str, match_field: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {"assignments": {"type": "array", "items": {
            "type": "object",
            "properties": {
                unit_field: {"type": "string"},
                "external_effect": {"type": "boolean"},
                "effect_modules": {"type": "array", "items": {"type": "string"}},
                "effect_rationale": {"type": "string"},
                "matches": {"type": "array", "items": {
                    "type": "object", "properties": dict({match_field: {"type": "string"}}, **_MATCH_PROPS),
                    "required": [match_field, "confidence", "relation_type", "rationale"],
                    "additionalProperties": False}},
            },
            "required": [unit_field, "external_effect", "effect_modules", "effect_rationale", "matches"],
            "additionalProperties": False}}},
        "required": ["assignments"],
        "additionalProperties": False,
    }


FORWARD_SCHEMA = _schema("snippet_id", "record_id")
REVERSE_SCHEMA = _schema("record_id", "snippet_id")


def base_retrieve_prompt(text_lines: Sequence[str], items: Sequence[Item], cands: Optional[Dict[str, List[str]]],
                         max_chars: int = 4000, no_tools_rule: bool = True, snippets_first: bool = True,
                         auto_cited: bool = True, extra_rules: str = "", with_module: bool = False) -> str:
    """Prompt wie cached_sweep_runner.build_method_prompt("retrieve", ...); ``extra_rules`` wird an die
    Anweisungen angehängt (leer: identisch zum Runner)."""
    base = PROMPT_INSTRUCTIONS
    if auto_cited:
        base = re.sub(r"- Ids cited verbatim in the snippet.*?rule above\.\n",
                      "- Record ids that the snippet cites verbatim are assigned automatically: do NOT list them. List only\n"
                      "  ADDITIONAL records whose requirement the snippet content concerns.\n- rationale: at most 8 words.\n",
                      base, flags=re.S)
    instr = base.replace(
        "Below is the COMPLETE record catalogue of one universe, one JSON object per line:\n"
        '{"id": record id, "mod": module, "rel": release bitmask, "text": normative text (truncated)}.',
        RETRIEVE_INTRO) + extra_rules
    rule = NO_TOOLS_RULE if no_tools_rule else ""
    head = (rule + "\n" if rule else "") + instr
    catalogue = "\n<catalogue>\n" + "\n".join(text_lines) + "\n</catalogue>\n"
    lines = []
    for it in items:
        pl = item_payload(it, max_chars, with_module)
        if cands is not None:
            pl["cand"] = cands.get(it.id, [])
        lines.append(json.dumps(pl, ensure_ascii=False, separators=(',', ':')))
    snip_block = "<snippets>\n" + "\n".join(lines) + "\n</snippets>\n"
    tail = "Snippet ids in this batch: " + ", ".join(it.id for it in items) + "\nReturn the JSON object now.\n" + rule
    if snippets_first:
        head = head.replace("Below is", "After the snippets follows").replace(
            "After the catalogue follows a batch of snippets", "First comes a batch of snippets")
        return head + snip_block + catalogue + tail
    return head + catalogue + snip_block + tail


def forward_prompt(records: Dict[str, Record], items: Sequence[Item], cands: Dict[str, List[str]],
                   stage2: bool = False) -> str:
    union = sorted(dict.fromkeys(rid for it in items for rid in cands.get(it.id, []) if rid in records))
    lines = [records[rid].line for rid in union]
    extra = EFFECT_RULES + (STAGE2_RULES if stage2 else "")
    return base_retrieve_prompt(lines, items, cands, core.METHOD["snippet_chars"], extra_rules=extra, with_module=True)


def reverse_prompt(records: Sequence[Record], pool: Sequence[Item]) -> str:
    rule = NO_TOOLS_RULE
    snip_lines = [json.dumps(dict(item_payload(it, core.METHOD["reverse_snippet_chars"]), refs=[]), ensure_ascii=False,
                             separators=(',', ':')) for it in pool]
    return (rule + REVERSE_INSTRUCTIONS + REVERSE_EFFECT_RULES + "\n<records>\n" + "\n".join(r.line for r in records)
            + "\n</records>\n<snippets>\n" + "\n".join(snip_lines) + "\n</snippets>\nRecord ids: "
            + ", ".join(r.id for r in records) + "\nReturn the JSON object now.\n" + rule)


def norm_relation(value: Any) -> str:
    v = re.sub(r"[^A-Z_]", "", str(value or "").upper().replace(" ", "_").replace("-", "_"))
    return v if v in core.RELATION_TYPES else core.RELATION_FALLBACK


def _clamp(v: Any) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


def parse_answer(obj: Any, wanted: Sequence[str], unit_field: str, match_field: str) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """Antwort -> {einheit: {external_effect, modules, effect_rationale, matches: [{id, confidence, relation_type,
    rationale}]}} und Probleme. Unbekannte Einheiten werden verworfen, fehlende gemeldet."""
    problems: List[str] = []
    want = set(wanted)
    out: Dict[str, Dict[str, Any]] = {}
    if not isinstance(obj, dict) or not isinstance(obj.get("assignments"), list):
        return out, ["no 'assignments' list in response"]
    for a in obj["assignments"]:
        if not isinstance(a, dict):
            problems.append("assignment is not an object")
            continue
        uid = str(a.get(unit_field, "")).strip()
        if uid not in want:
            problems.append(f"unknown unit {uid[:40]!r}")
            continue
        matches = a.get("matches")
        if not isinstance(matches, list):
            problems.append(f"{uid}: matches is not a list")
            continue
        clean = []
        for m in matches:
            if not isinstance(m, dict) or not str(m.get(match_field, "")).strip():
                problems.append(f"{uid}: match without {match_field}")
                continue
            clean.append({"id": str(m[match_field]).strip(), "confidence": _clamp(m.get("confidence")),
                          "relation_type": norm_relation(m.get("relation_type")),
                          "rationale": " ".join(str(m.get("rationale", "")).split())[:300]})
        mods = a.get("effect_modules") if isinstance(a.get("effect_modules"), list) else []
        cur = out.setdefault(uid, {"external_effect": bool(a.get("external_effect") is True),
                                   "modules": [str(x).strip()[:40] for x in mods if str(x).strip()][:12],
                                   "effect_rationale": " ".join(str(a.get("effect_rationale", "")).split())[:300],
                                   "matches": []})
        cur["matches"].extend(clean)
    for uid in sorted(want - set(out)):
        problems.append(f"missing unit {uid}")
    return out, problems


def resolve_modules(names: Iterable[str], module_index: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """Modulnamen der Antwort auf Modulcodes des Korpus abbilden (ohne Groß-/Kleinschreibung)."""
    ok, unknown = [], []
    for n in names:
        key = re.sub(r"[^a-z0-9]", "", str(n).lower())
        code = module_index.get(key)
        (ok if code else unknown).append(code or str(n))
    return list(dict.fromkeys(ok)), list(dict.fromkeys(unknown))


def module_index(records: Iterable[Record]) -> Dict[str, str]:
    idx: Dict[str, str] = {}
    for r in records:
        idx.setdefault(re.sub(r"[^a-z0-9]", "", r.module.lower()), r.module)
    return idx


# ==============================================================================
# Gatekeeper
# ==============================================================================

def gate(record: Optional[Record], unit_mask: int) -> Optional[str]:
    """Milde Release-Regel: None = zulässig, sonst Grund (``unknown_id``, ``release``)."""
    if record is None:
        return "unknown_id"
    if unit_mask != ALL_MASK and record.mask != ALL_MASK:
        lo = (unit_mask & -unit_mask).bit_length() - 1
        if record.mask.bit_length() - 1 < lo:
            return "release"
    return None


# ==============================================================================
# agy stream-json, Verbrauch und Listenpreis
# ==============================================================================

PRICES = {"gemini-3.8-flash": (0.75, 0.075, 3.75)}       # USD je 1M Tokens: input, cached input, output (Stand 2026-10-08)
ALLOWED_TOOLS = {"finish"}


def parse_agy_stream(text: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, int], List[str]]:
    """Ergebnis-Ereignis, Schritte je Art und verbotene Werkzeugaufrufe (alles außer ``finish``)."""
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
            result = ev                                   # --output-format json
    if "auto-denied" in (text or "") or "cannot prompt for" in (text or ""):
        bad.append("denied")
    return result, steps, bad


def usage_tokens(usage: Dict[str, Any]) -> Dict[str, int]:
    def g(k: str) -> int:
        v = (usage or {}).get(k)
        return int(v) if isinstance(v, (int, float)) else 0
    return {"input": g("input_tokens"), "cached": g("cache_read_tokens"), "output": g("output_tokens"),
            "thinking": g("thinking_tokens")}


def list_price(model: str, tok: Dict[str, int]) -> float:
    """Kosten zu API-Listenpreisen; Denk-Tokens zählen wie Ausgabe (so rechnet die Gemini-API ab)."""
    pin, pcached, pout = PRICES.get(model, PRICES[core.DEFAULT_MODEL])
    return (tok["input"] * pin + tok["cached"] * pcached + (tok["output"] + tok["thinking"]) * pout) / 1e6


# ==============================================================================
# Planung (gemeinsam für lokalen Planer und Tests)
# ==============================================================================

@dataclass
class PlanInputs:
    records: List[Record]
    items: List[Item]                 # Snippets
    figures: List[Item]               # Schaubild-Reihen
    elements: List[Record]            # Element-Einheiten (Fragmente)
    basis: Dict[str, str] = field(default_factory=dict)      # unit -> Hash12 der Bestandszeilen


_CTX: Dict[str, Any] = {}


def _prepare(inp: PlanInputs, k: int) -> None:
    """Indizes im Elternprozess bauen; ein fork-Pool erbt sie (copy-on-write)."""
    pool = inp.items + inp.figures
    citers: Dict[str, List[str]] = {}
    for it in pool:
        for c in it.cited:
            citers.setdefault(c, []).append(it.id)
    _CTX.clear()
    _CTX.update(k=k, rec_index=record_index(inp.records), known={r.id for r in inp.records},
                item_index=item_index(pool), citers=citers, by_id={it.id: it for it in pool},
                rec_by_id={r.id: r for r in inp.elements})


def _cand_job(job: Tuple[str, List[str]]) -> Dict[str, List[str]]:
    kind, ids = job
    k = _CTX["k"]
    if kind == "fwd":
        items = [_CTX["by_id"][i] for i in ids]
        return {f"f:{i}": c for i, c in retrieve_candidates(_CTX["rec_index"], items, k, known=_CTX["known"]).items()}
    recs = [_CTX["rec_by_id"][i] for i in ids]
    return {f"r:{i}": c for i, c in reverse_candidates(_CTX["item_index"], recs, _CTX["citers"], k).items()}


def compute_candidates(inp: PlanInputs, k: int, workers: int = 0, chunk: int = 100,
                       only: Optional[Set[str]] = None, progress: Optional[Callable[[int, int], None]] = None
                       ) -> Dict[str, List[str]]:
    """Kandidaten aller Einheiten (``f:<id>`` vorwärts, ``r:<id>`` Gegenrichtung). ``only``: nur diese Schlüssel
    (Rest aus einem Zwischenspeicher des Aufrufers). ``workers`` > 1: fork-Pool (CPU-gebundene BM25-Suche)."""
    _prepare(inp, k)
    fwd = [it.id for it in inp.items + inp.figures if only is None or f"f:{it.id}" in only]
    rev = [r.id for r in inp.elements if only is None or f"r:{r.id}" in only]
    jobs = [("fwd", fwd[i:i + chunk]) for i in range(0, len(fwd), chunk)]
    jobs += [("rev", rev[i:i + chunk]) for i in range(0, len(rev), chunk)]
    out: Dict[str, List[str]] = {}
    done = 0
    if workers > 1 and len(jobs) > 1:
        import multiprocessing as mp
        try:
            ctx = mp.get_context("fork")
        except ValueError:
            ctx = None
        if ctx is not None:
            with ctx.Pool(workers) as pool:
                for part in pool.imap_unordered(_cand_job, jobs):
                    out.update(part)
                    done += 1
                    if progress:
                        progress(done, len(jobs))
            return out
    for job in jobs:
        out.update(_cand_job(job))
        done += 1
        if progress:
            progress(done, len(jobs))
    return out


def build_plan(inp: PlanInputs, decisions: Dict[str, Dict[str, Any]], decided_keys: Set[str],
               cands: Dict[str, List[str]], k: int = 20) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Arbeitsliste: alle Einheiten, deren Schlüssel nicht im Protokoll steht. Reihenfolge: Snippets, Schaubilder,
    Elemente; je Art nach Plattform, Modul, Dokument, Seite, ID (ähnliche Einheiten teilen Kandidaten und damit
    Prompt-Platz). Status: ``new`` (nie entschieden), ``stale`` (Eingaben geändert, ``prior`` = alte Entscheidung).
    Rückgabe (plan, Statistik)."""
    rec_h = {r.id: record_hash(r) for r in inp.records}
    pool_h = {it.id: item_hash(it) for it in inp.items + inp.figures}
    plan: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {"total": 0, "decided": 0, "new": 0, "stale": 0, "by_kind": {}}

    def add(kind: str, ref: str, platform: str, module: str, own_hash: str, cand: List[str], cand_h: Dict[str, str],
            sort: Tuple, mask: int):
        unit = core.unit_id(kind, ref)
        cand_hash = core.obj_hash([[c, cand_h.get(c, "")] for c in cand])
        inputs = [{"kind": kind, "ref": ref, "hash": own_hash},
                  {"kind": "candidates", "ref": f"bm25-global-k{k}", "hash": cand_hash}]
        key = core.unit_key(unit, inputs)
        bk = stats["by_kind"].setdefault(kind, {"total": 0, "decided": 0, "new": 0, "stale": 0})
        stats["total"] += 1
        bk["total"] += 1
        if key in decided_keys:
            stats["decided"] += 1
            bk["decided"] += 1
            return
        prior = decisions.get(unit)
        status = "stale" if prior else "new"
        stats[status] += 1
        bk[status] += 1
        plan.append({"unit": unit, "kind": kind, "ref": ref, "key": key, "status": status,
                     "prior": prior["hash"] if prior else None, "basis": inp.basis.get(unit),
                     "p": platform, "mod": module, "mask": f"0x{mask:X}", "inputs": inputs, "cand": cand,
                     "_sort": (core.KIND_ORDER[kind], 0 if status == "new" else 1) + sort})

    for it in inp.items:
        add("snippet", it.id, it.platform, it.module, pool_h[it.id], cands.get(f"f:{it.id}", []), rec_h,
            (it.platform, it.module.lower(), it.doc, it.page, it.id), it.mask)
    for it in inp.figures:
        add("figure", it.id, it.platform, it.module, pool_h[it.id], cands.get(f"f:{it.id}", []), rec_h,
            (it.platform, it.doc, it.page, it.id), it.mask)
    for r in inp.elements:
        add("element", r.id, r.platform, r.module, rec_h[r.id], cands.get(f"r:{r.id}", []), pool_h,
            (r.platform, r.module.lower(), r.kind, r.id), r.mask)
    plan.sort(key=lambda u: u["_sort"])
    for i, u in enumerate(plan, 1):
        del u["_sort"]
        u["order"] = i
    return plan, stats
