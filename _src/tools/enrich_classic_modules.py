#!/usr/bin/env python3
"""enrich_classic_modules.py — Enriches AUTOSAR Classic module records with:

1. Overview section at the top:
   - <h3>Funktionen — Übersicht</h3> with <ul class="mlist"> and <code class="sig">
   - <h3>Typen — Übersicht</h3> (if types present)
   - Followed by <h2 class="sect">Funktionen — Detailansicht</h2>
2. Linked Requirement-ID:
   - <span class="sws"><a href="../../versions.html?id=SWS_..." title="...">[SWS_...]</a></span>
3. Direct PDF link to exact anchor / nameddest:
   - <a href="https://www.autosar.org/fileadmin/standards/R20-11/CP/<Doc>.pdf#nameddest=SWS_..."
        class="sws-pdf-link" target="_blank" rel="noopener noreferrer" title="...">📄 PDF</a>
4. Cleans any OCR table noise/trailing metadata from function syntax signatures.

Usage:
    python3 _src/tools/enrich_classic_modules.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "_src"
RECORDS_DIR = SRC_DIR / "spec" / "records" / "classic" / "modules"
VERSIONS_DIR = SRC_DIR / "spec" / "versions" / "AUTOSAR" / "CP" / "record"

sys.path.insert(0, str(SRC_DIR / "tools"))
from classic_api_scrape import CLUSTER_MAP

# Cache for page numbers looked up from record .jsonl
_PAGE_CACHE: Dict[str, Optional[int]] = {}


def get_sws_page(sws_id: str) -> Optional[int]:
    """Look up page number for an SWS requirement from CP record versions."""
    if sws_id in _PAGE_CACHE:
        return _PAGE_CACHE[sws_id]

    fn = VERSIONS_DIR / f"{sws_id}.jsonl"
    if not fn.is_file():
        _PAGE_CACHE[sws_id] = None
        return None

    try:
        lines = fn.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not line.strip():
                continue
            data = json.loads(line)
            # Prefer R20-11, but accept any release
            content = data.get("content", "")
            m = re.search(r"(\d+)\s+of\s+(\d+)", content)
            if m:
                p = int(m.group(1))
                _PAGE_CACHE[sws_id] = p
                return p
    except Exception:
        pass

    _PAGE_CACHE[sws_id] = None
    return None


# Patterns for canonical AUTOSAR identifiers
_CANONICAL_PATTERNS: Optional[List[Tuple[re.Pattern, str]]] = None


def get_canonical_patterns() -> List[Tuple[re.Pattern, str]]:
    """Build compiled regexes for all known AUTOSAR canonical names sorted longest first."""
    global _CANONICAL_PATTERNS
    if _CANONICAL_PATTERNS is not None:
        return _CANONICAL_PATTERNS

    all_names = set()
    for f in RECORDS_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            for b in d.get("blocks", []):
                m = re.search(r'<span class="kind">[^<]+</span>\s*([A-Za-z0-9_]+)', b.get("html", ""))
                if m:
                    all_names.add(m.group(1))
        except Exception:
            pass

    for extra in [
        "Std_ReturnType", "Std_VersionInfoType", "PduIdType", "PduInfoType", "PduLengthType",
        "NetworkHandleType", "uint8", "uint16", "uint32", "uint64", "sint8", "sint16", "sint32",
        "sint64", "boolean", "float32", "float64"
    ]:
        all_names.add(extra)

    patterns = []
    for name in sorted(all_names, key=len, reverse=True):
        if len(name) < 3:
            continue
        tokens = re.findall(r"[A-Z][a-z0-9]*|[a-z0-9]+|_", name)
        pat = r"\b" + r"\s*".join(re.escape(t) for t in tokens) + r"\b"
        patterns.append((re.compile(pat, re.IGNORECASE), name))

    _CANONICAL_PATTERNS = patterns
    return _CANONICAL_PATTERNS


def clean_syntax(raw_syntax: str, is_func: bool = True, symbol_name: str = "") -> str:
    """Normalize multi-line C syntax, repairing split tokens, module prefixes, and removing table residue."""
    s = re.sub(r"</?pre[^>]*>", "", raw_syntax).strip()

    # 1. Join split underscore
    s = re.sub(r"([A-Za-z0-9])\s+_\s*([A-Za-z0-9])", r"\1_\2", s)
    s = re.sub(r"([A-Za-z0-9])\s+_", r"\1_", s)
    s = re.sub(r"_\s+([A-Za-z0-9])", r"_\1", s)

    # 2. Strip OCR document headers and remnants from parameter lists
    s = re.sub(r"AUTOSAR\s+CP\s+R\d+.*?AUTOSAR_SWS_[A-Za-z0-9_\s]+(?=\)|,|\*|<a|\bPduIdType\b|\b[A-Za-z0-9_]+Type\b)", "", s, flags=re.IGNORECASE)
    s = re.sub(r"AUTOSAR\s+CP\s+R\d+.*?Document\s+ID\s*:\s*\S+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"Document\s+ID\s*:\s*\S+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*[a-z]\s+(?=<a|\b[A-Za-z0-9_]+Type\b)", "(", s)

    # 3. Canonical symbols replacement
    for pat, name in get_canonical_patterns():
        if pat.search(s):
            s = pat.sub(name, s)

    # 4. If symbol_name is specified and appears spaced, ensure it is exact
    if symbol_name:
        tokens = re.findall(r"[A-Z][a-z0-9]*|[a-z0-9]+|_", symbol_name)
        pat_sym = r"\b" + r"\s*".join(re.escape(t) for t in tokens) + r"\b"
        s = re.sub(pat_sym, symbol_name, s, flags=re.IGNORECASE)

    # 5. Common parameter word splits inside parameter lists
    for p_from, p_to in [
        (r"\b(Rx|Tx)\s+PduId\b", r"\1PduId"),
        (r"\b(Rx|Tx)\s+Pdu\b", r"\1Pdu"),
        (r"\bPdu\s+Id\b", "PduId"),
        (r"\bConfig\s+Ptr\b", "ConfigPtr"),
        (r"\bVersion\s+Info\b", "VersionInfo"),
        (r"\bPtr\s+To\s+SamplePtr\b", "PtrToSamplePtr"),
        (r"\bTrcv\s+Wu\s+ReasonPtr\b", "TrcvWuReasonPtr"),
        (r"\bCurrent\s+Power\s+State\b", "CurrentPowerState"),
        (r"\bTarget\s+Power\s+State\b", "TargetPowerState"),
        (r"\bPower\s+State\b", "PowerState"),
        (r"\bData\s+Buffer", "DataBuffer"),
        (r"\bNetwork\s+Handle\b", "NetworkHandle"),
        (r"\bSch\s+Handle\b", "SchHandle"),
        (r"\bTransceiver\s+Mode\b", "TransceiverMode"),
    ]:
        s = re.sub(p_from, p_to, s, flags=re.IGNORECASE)

    if is_func:
        # Trim any table OCR junk after closing parenthesis of function signature
        m_paren = re.search(r"^(.*?\(.*?\))(?:[^;]*;?)?.*$", s, re.DOTALL)
        if m_paren:
            s = m_paren.group(1).strip() + ";"
        elif not s.endswith(";"):
            s = s + ";"
    else:
        if ";" in s:
            s = s[:s.rfind(";") + 1].strip()

    # Normalize whitespace around punctuation
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s*\*\s*", "* ", s)
    s = re.sub(r"\s+;", ";", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_function_sig(cleaned_syntax: str, func_name: str, sws_id: str) -> str:
    """Construct <code class="sig"> return_type <a class="fn" href="#SWS_ID">Name</a> (params); </code>."""
    s = cleaned_syntax.strip()
    idx_paren = s.find("(")
    if idx_paren != -1:
        prefix = s[:idx_paren].strip()
        params = s[idx_paren:].strip()
        letters = list(re.escape(func_name))
        fn_pattern = r"\s*".join(letters)
        m_fn = re.search(fn_pattern, prefix, re.IGNORECASE)
        if m_fn:
            ret_type = prefix[:m_fn.start()].strip()
            fn_part = f'<a class="fn" href="#{sws_id}">{func_name}</a>'
            sig = f"{ret_type} {fn_part} {params}" if ret_type else f"{fn_part} {params}"
            return " ".join(sig.split())
        else:
            parts = prefix.rsplit(None, 1)
            if len(parts) == 2:
                ret_type, _ = parts
                return f"{ret_type} <a class=\"fn\" href=\"#{sws_id}\">{func_name}</a> {params}"
            return f'<a class="fn" href="#{sws_id}">{func_name}</a> {params}'
    else:
        return f'<a class="fn" href="#{sws_id}">{func_name}</a>;'


def build_type_sig(cleaned_syntax: str, type_name: str, sws_id: str, desc: str) -> str:
    """Construct <code class="sig"> for types, structs, and enums in the overview."""
    desc_lower = desc.lower()
    syntax_lower = cleaned_syntax.lower()
    fn_link = f'<a class="fn" href="#{sws_id}">{type_name}</a>'

    if "enum" in syntax_lower or "enumeration" in desc_lower or "enum" in desc_lower or type_name.endswith(("ModeType", "StateType", "StatusType", "ResultType", "ReasonType", "ActionType", "ReturnType", "ErrorType")):
        return f'enum {fn_link}'
    elif "struct" in syntax_lower or "struct" in desc_lower or "structure" in desc_lower or type_name.endswith("ConfigType"):
        return f'struct {fn_link}'
    elif cleaned_syntax.startswith("typedef"):
        tokens = cleaned_syntax.split()
        if len(tokens) >= 3 and tokens[-1].rstrip(";").endswith(type_name):
            base_type = " ".join(tokens[1:-1])
            return f'typedef {base_type} {fn_link};'
        return f'typedef {fn_link}'
    else:
        return fn_link


def clean_desc_for_dim(raw_desc: str) -> str:
    """Extract a concise single-line description for the <span class="dim">."""
    txt = re.sub(r"<[^>]+>", "", raw_desc).strip()
    # Strip any scraped document header/footer remnants
    txt = re.sub(r"AUTOSAR\s+CP\s+R\d+.*?$", "", txt, flags=re.IGNORECASE).strip()
    txt = re.sub(r"Document\s+ID\s+\d+.*?$", "", txt, flags=re.IGNORECASE).strip()
    txt = " ".join(txt.split())
    if "." in txt:
        first_sentence = txt.split(".")[0].strip()
        if len(first_sentence) >= 15:
            txt = first_sentence + "."
    if len(txt) > 130:
        txt = txt[:127].rsplit(" ", 1)[0] + "..."
    return txt


def get_module_pdf(mod_key: str) -> Tuple[str, str]:
    """Retrieve PDF filename and human heading for a module from CLUSTER_MAP."""
    mod_lower = mod_key.lower()
    for cname, cinfo in CLUSTER_MAP.items():
        for mname, minfo in cinfo["modules"].items():
            if mname.lower() == mod_lower:
                return minfo.get("pdf", ""), minfo.get("heading", mod_key)
    return "", mod_key


def enrich_module_record(record_path: Path) -> bool:
    """Enrich a single module record JSON file in place."""
    try:
        with open(record_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"Error reading {record_path}: {exc}")
        return False

    mod_key = data.get("module") or record_path.stem
    pdf_doc, heading = get_module_pdf(mod_key)
    if not pdf_doc:
        print(f"Warning: No PDF found for {mod_key}")

    blocks = data.get("blocks", [])
    if not blocks:
        return False

    lead_block = None
    items = []
    curr_item: Optional[Dict[str, Any]] = None

    for b in blocks:
        h = b.get("html", "")
        # Keep lead block (<h2>...<p class="lead">...)
        if lead_block is None and "<p class=\"lead\">" in h:
            lead_block = b
            continue

        # Skip previous overview or section blocks so the script is idempotent
        if "Funktionen — Übersicht" in h or "Typen — Übersicht" in h or "Detailansicht" in h:
            continue
        if '<ul class="mlist">' in h:
            continue

        if '<h3 class="recname"' in h:
            if curr_item:
                items.append(curr_item)
            curr_item = {"header": b, "syntax": None, "desc": None, "extra": []}
        elif curr_item is not None:
            if '<pre class="syntax"' in h:
                curr_item["syntax"] = b
            elif '<div class="desc"' in h:
                curr_item["desc"] = b
            else:
                curr_item["extra"].append(b)

    if curr_item:
        items.append(curr_item)

    if not items:
        return False

    funcs_overview = []
    types_overview = []
    new_detail_blocks = []

    for it in items:
        header_html = it["header"]["html"]
        m_kind_name = re.search(r'<span class="kind">([^<]+)</span>\s*(.*?)\s*<span class="sws"', header_html)
        m_id = re.search(r'id="([^"]+)"', header_html)
        if not m_kind_name or not m_id:
            # Fallback if structure deviates
            new_detail_blocks.append(it["header"])
            if it["syntax"]:
                new_detail_blocks.append(it["syntax"])
            if it["desc"]:
                new_detail_blocks.append(it["desc"])
            new_detail_blocks.extend(it["extra"])
            continue

        kind = m_kind_name.group(1).strip()
        name = m_kind_name.group(2).strip()
        sws_id = m_id.group(1).strip()

        # Clean any trailing document stem mistakenly joined to function name (e.g. LinIf_GetPIDTableAUTOSAR_SWS_LINInterface)
        if "AUTOSAR" in name and not name.startswith("AUTOSAR"):
            name = re.sub(r"AUTOSAR.*$", "", name).strip()

        # Clean syntax for both functions and types
        syntax_html = it["syntax"]["html"] if it["syntax"] else ""
        cleaned_syntax = ""
        desc_html = it["desc"]["html"] if it["desc"] else ""
        raw_desc_text = re.sub(r"<[^>]+>", "", desc_html).strip()

        if it["syntax"]:
            cleaned_syntax = clean_syntax(syntax_html, is_func=(kind == "function"), symbol_name=name)
            it["syntax"]["html"] = f'<pre class="syntax">{cleaned_syntax}</pre>'

        dim_desc = clean_desc_for_dim(desc_html) if desc_html else f"{kind.capitalize()} {name}."

        # Page and PDF links
        page = get_sws_page(sws_id)
        if page:
            pdf_title = f"Spezifikations-PDF im Original öffnen: {pdf_doc} (Anker: #{sws_id}, S. {page})"
        else:
            pdf_title = f"Spezifikations-PDF im Original öffnen: {pdf_doc} (Anker: #{sws_id})"
        pdf_url = f"https://www.autosar.org/fileadmin/standards/R20-11/CP/{pdf_doc}#nameddest={sws_id}"

        sws_link = f'<a href="../../versions.html?id={sws_id}" title="Requirement im Versions- &amp; Revisions-Explorer anzeigen">[{sws_id}]</a>'
        pdf_link = f'<a href="{pdf_url}" target="_blank" rel="noopener noreferrer" class="sws-pdf-link" title="{pdf_title}">📄 PDF</a>'

        new_header_html = f'<h3 class="recname" id="{sws_id}"><span class="kind">{kind}</span> {name} <span class="sws">{sws_link}</span> {pdf_link}</h3>'
        it["header"]["html"] = new_header_html

        # Add to overview
        if kind == "function":
            sig = build_function_sig(cleaned_syntax or f"{name}();", name, sws_id)
            funcs_overview.append(f'  <li><code class="sig">{sig}</code> <span class="dim">{dim_desc}</span></li>')
        else:
            sig = build_type_sig(cleaned_syntax, name, sws_id, raw_desc_text)
            types_overview.append(f'  <li><code class="sig">{sig}</code> <span class="dim">{dim_desc}</span></li>')

        new_detail_blocks.append(it["header"])
        if it["syntax"]:
            new_detail_blocks.append(it["syntax"])
        if it["desc"]:
            new_detail_blocks.append(it["desc"])
        new_detail_blocks.extend(it["extra"])

    # Build Overview HTML blocks
    overview_blocks = []
    if funcs_overview:
        overview_blocks.append({
            "t": "html",
            "html": "<h3>Funktionen — Übersicht</h3>\n<ul class=\"mlist\">\n" + "\n".join(funcs_overview) + "\n</ul>",
            "tail": "\n"
        })
    if types_overview:
        overview_blocks.append({
            "t": "html",
            "html": "<h3>Typen — Übersicht</h3>\n<ul class=\"mlist\">\n" + "\n".join(types_overview) + "\n</ul>",
            "tail": "\n"
        })

    if funcs_overview and types_overview:
        divider_title = "Funktionen &amp; Typen — Detailansicht"
    elif types_overview:
        divider_title = "Typen — Detailansicht"
    else:
        divider_title = "Funktionen — Detailansicht"

    overview_blocks.append({
        "t": "html",
        "html": f'<h2 class="sect">{divider_title}</h2>',
        "tail": "\n"
    })

    final_blocks = ([lead_block] if lead_block else []) + overview_blocks + new_detail_blocks
    data["blocks"] = final_blocks

    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")

    return True


def main():
    records = sorted(RECORDS_DIR.glob("*.json"))
    print(f"Enriching {len(records)} classic module records under {RECORDS_DIR}...")
    success_count = 0
    for r in records:
        if enrich_module_record(r):
            success_count += 1
    print(f"Successfully enriched {success_count}/{len(records)} module records.")


if __name__ == "__main__":
    main()
