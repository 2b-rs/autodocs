#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lib_docmodel.py — Gemeinsames Datenmodell für Extraktion (extract.py) und
Generierung (generate.py). Projektspezifika (Bereiche, Sprachen, Flaggen)
stehen im Manifest _src/site.json — dieses Modul und alle Skripte sind
projektneutral gehalten (siehe ARCHITEKTUR.md).

Seitenmodell (JSON, _src/sources/pages/<pfad>.json):
  {
    "file":       "classes/cl_….html",   Zielpfad relativ zur Doku-Wurzel
    "title":      "…",                    <title>-Text (unkodiert)
    "body_class": "vis-app" | null,
    "nav_html":   "…",                    inneres HTML von <nav class="crumbs">
    "footer":     "extracted" | …,        Schlüssel in _src/templates/footers.json
    "main_lead":  "\n",                   führender Text in <main>
    "main":       [ Block, … ]
  }

Blocktypen (jeder Block hat "tail": Text NACH dem Element, meist "\n" oder ""):
  html   {"html": "<h2 …>…</h2>"}                     beliebiges Element, verbatim
  svg    {"wrap_class","wrap_attrs","pre","src","inner_tail"}
                                                       Diagramm-Wrapper; SVG liegt
                                                       als Datei unter _src/diagrams/
  ai     {"src": "content/ai/…/x.html"}                KI-Block als Fragmentdatei
  rec    {"attrs","lead","blocks":[…]}                 <article class="rec"> mit
                                                       rekursiven Unterblöcken
  rec-ref {"src": "spec/records/SWS_CORE/SWS_….json"}   Verweis auf einen Record
                                                       der Spezifikations-DB; wird
                                                       beim Laden (load_page) zu
                                                       einem rec-Block aufgelöst
                                                       (Merkfeld "_src" = Quelle)
  fold   {"attrs","summary","lead","blocks":[…]}       klappbarer Abschnitt:
                                                       <details><summary>H2</summary>…>;
                                                       "summary" = H2-Element verbatim,
                                                       "lead" = Text nach </summary>
  props  {"attrs","rows":[{"th","th_attrs","td","td_attrs"},…]}
                                                       Eigenschafts-Tabelle
  params {"attrs","rows":[{"cells":[{"tag","attrs","html"},…],"tail"},…],"lead"}
                                                       Parameter-/Rückgabe-Tabelle
"""
import hashlib
import html as _html
import json
import os
import re
from lxml import etree, html as LH
import sys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "tools"))
from version_id import requirement_version_id, content_hash8

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)

PAGES_DIR = os.path.join(SRC, "sources", "pages")
AI_DIR = os.path.join(SRC, "content", "ai")
DIAG_DIR = os.path.join(SRC, "diagrams")
TMPL_DIR = os.path.join(SRC, "templates")
DATA_DIR = os.path.join(SRC, "data")
SPEC_DIR = os.path.join(SRC, "spec", "records")

VOID_TAGS = {"meta", "link", "br", "hr", "img", "input"}

# ------------------------------------------------- Projektmanifest (site.json)
# Alle projektspezifischen Konstanten (Bereiche, Sprachen) kommen aus dem
# Manifest; ein neues Projekt braucht nur ein eigenes site.json + Templates.
with open(os.path.join(SRC, "site.json"), encoding="utf-8") as _f:
    SITE = json.load(_f)

BEREICHE = SITE["bereiche"]              # Unterverzeichnis -> Seitentyp

# ------------------------------------------------------------- Sprachen
# Die kanonische Sprache liegt an der Wurzel; jede Zielsprache erhält einen
# Spiegelbaum unter <lang>/ (siehe lib_i18n.py, WARTUNG.md).
KANONISCH = SITE["sprachen"]["kanonisch"]
LANGS = list(SITE["sprachen"]["ziele"])
RTL = set(SITE["sprachen"]["rtl"])
FLAGGE = SITE["sprachen"]["flaggen"]
SPRACHNAME = SITE["sprachen"]["namen"]


def langswitch_html(page_file, lang):
    """Flaggenleiste (Sprachumschalter) für eine Seite.
    page_file ist der Pfad relativ zur Doku-Wurzel (ohne Sprachpräfix)."""
    depth = page_file.count("/") + (1 if lang != KANONISCH else 0)
    prefix = "../" * depth
    teile = []
    for l in [KANONISCH] + LANGS:
        ziel = page_file if l == KANONISCH else "%s/%s" % (l, page_file)
        cls = ' class="cur"' if l == lang else ""
        teile.append(
            '<a%s href="%s" title="%s" hreflang="%s"><img src="%sflags/%s.svg" alt="%s"></a>'
            % (cls, prefix + ziel, SPRACHNAME[l], l, prefix, FLAGGE[l], l.upper()))
    return '<div class="langs">%s</div>' % "".join(teile)


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(t):
    return esc(t).replace('"', "&quot;")


def esc_once(t):
    """Wie esc(), aber fuer Texte, die bereits HTML-Entities enthalten koennen.

    Spec-Headings kommen teils vorescaped aus der Quelle (z. B.
    "function operator&lt;&lt;"). Ein zweites esc() wuerde daraus
    "operator&amp;lt;&amp;lt;" machen, was der Leser als Rohtext sieht.
    Deshalb zuerst entschaerfen, dann genau einmal escapen.
    """
    return esc(_html.unescape(t or ""))


def serialize(el):
    """Element ohne tail serialisieren (HTML-Serialisierung, UTF-8-Text)."""
    s = etree.tostring(el, encoding="unicode", method="html")
    # tostring hängt den tail an — abschneiden:
    if el.tail:
        assert s.endswith(el.tail)
        s = s[: -len(el.tail)]
    return s


def inner_html(el):
    parts = [esc(el.text) if el.text else ""]
    for c in el:
        parts.append(etree.tostring(c, encoding="unicode", method="html"))
    return "".join(parts)


def open_tag(tag, attrs):
    a = "".join(' %s="%s"' % (k, esc_attr(v)) for k, v in attrs)
    return "<%s%s>" % (tag, a)


def attrs_list(el):
    return [[k, v] for k, v in el.items()]


# ------------------------------------------- Spezifikations-DB (spec/records)
# Jeder Spezifikations-Record (<article class="rec">) liegt als eigene
# JSON-Datei unter _src/spec/records/<GRUPPE>/<ID>.json (Gruppe = die ersten
# beiden Namensbestandteile der ID, z.B. SWS_CORE). Seitenmodelle referenzieren
# Records über rec-ref-Blöcke; load_page() löst sie auf. So bleiben die
# Spezifikationselemente eine eigenständige, seitenunabhängig adressierbare
# Plain-Text-Datenbank (Schlüssel: SWS-ID).

def record_gruppe(rid):
    teile = rid.split("_")
    return "_".join(teile[:2]) if len(teile) >= 3 else "_SONSTIGE"


def record_relpath(rid):
    """Ablagepfad eines Records relativ zu _src/."""
    return "spec/records/%s/%s.json" % (record_gruppe(rid), rid)


def record_hash(rid):
    """SHA1 der Record-Datei (für Veraltet-Erkennung in ai/traces), sonst None."""
    p = os.path.join(SRC, record_relpath(rid))
    if not os.path.exists(p):
        return None
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def load_record(relsrc, srcdir=SRC):
    with open(os.path.join(srcdir, relsrc), encoding="utf-8") as f:
        return json.load(f)


def save_record(rec, srcdir=SRC):
    """rec-Block (ohne tail) als Record-Datei schreiben; liefert relpath."""
    rid = dict(rec["attrs"])["id"]
    rel = record_relpath(rid)
    inhalt = {"id": rid, "attrs": rec["attrs"], "lead": rec.get("lead", ""),
              "blocks": rec["blocks"]}
    pfad = os.path.join(srcdir, rel)
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(inhalt, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return rel


def resolve_recs(blocks, srcdir=SRC):
    """rec-ref-Blöcke in-place zu rec-Blöcken auflösen (rekursiv).
    Das Merkfeld "_src" hält die Herkunftsdatei (für extract/validate)."""
    out = []
    for b in blocks:
        if b["t"] == "rec-ref":
            r = load_record(b["src"], srcdir)
            b = {"t": "rec", "attrs": r["attrs"], "lead": r.get("lead", ""),
                 "blocks": r["blocks"], "tail": b.get("tail", ""),
                 "_src": b["src"]}
            if r.get("requirement_meta"):
                b["requirement_meta"] = r["requirement_meta"]
            if r.get("status"):
                b["status"] = r["status"]
            if r.get("history"):
                b["history"] = r["history"]
            if r.get("status"):
                b["status"] = r["status"]
            if r.get("history"):
                b["history"] = r["history"]
            if r.get("status"):
                b["status"] = r["status"]
            if r.get("history"):
                b["history"] = r["history"]
            if r.get("status"):
                b["status"] = r["status"]
            if r.get("history"):
                b["history"] = r["history"]
            if r.get("status"):
                b["status"] = r["status"]
            if r.get("history"):
                b["history"] = r["history"]
            if r.get("status"):
                b["status"] = r["status"]
            if r.get("history"):
                b["history"] = r["history"]
            if r.get("status"):
                b["status"] = r["status"]
            if r.get("history"):
                b["history"] = r["history"]
        if b["t"] in ("rec", "fold"):
            b = dict(b, blocks=resolve_recs(b["blocks"], srcdir))
        out.append(b)
    return out


def externalize_recs(page, srcdir=SRC):
    """Inverse zu resolve_recs: rec-Blöcke mit Record-ID in die Spezifikations-DB
    schreiben und im Seitenmodell durch rec-ref ersetzen. Nur für Blöcke, deren
    attrs eine id tragen; andere bleiben inline."""
    geschrieben = []

    def walk(blocks):
        out = []
        for b in blocks:
            if b["t"] == "rec" and dict(b["attrs"]).get("id"):
                rel = save_record(b, srcdir)
                geschrieben.append(rel)
                out.append({"t": "rec-ref", "src": rel, "tail": b.get("tail", "")})
            elif b["t"] == "fold":
                out.append(dict(b, blocks=walk(b["blocks"])))
            else:
                out.append(b)
        return out

    page["main"] = walk(page["main"])
    return geschrieben


def load_page(path, srcdir=SRC):
    """Seitenmodell laden, rec-ref-Verweise auflösen. Alle lesenden Skripte
    (generate, validate, build_indexes, i18n_extract) nutzen diesen Weg."""
    with open(path, encoding="utf-8") as f:
        page = json.load(f)
    page["main"] = resolve_recs(page["main"], srcdir)
    return page


def save_page(page, srcdir=SRC):
    """Seitenmodell kanonisch schreiben (Records ausgelagert, ohne Merkfelder)."""
    import copy
    p = copy.deepcopy(page)
    externalize_recs(p, srcdir)
    out = os.path.join(srcdir, "sources", "pages", re.sub(r"\.html$", ".json", p["file"]))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return out


def iter_pages(only=None, srcdir=SRC):
    """Alle Seitenmodelle (aufgelöst) in stabiler Reihenfolge liefern."""
    import glob as _glob
    pages_dir = os.path.join(srcdir, "sources", "pages")
    for p in sorted(_glob.glob(os.path.join(pages_dir, "**", "*.json"), recursive=True)):
        page = load_page(p, srcdir)
        if only and page["file"] not in only:
            continue
        yield page


# ---------------------------------------------------------------- Rendering

_REVIEW_REASON_LABELS = {
    "legacy_desc_import": ("Legacy-Beschreibung prüfen", "Der Beschreibungstext wurde aus einer älteren Dokumentationsquelle übernommen und konnte nicht mit hoher Sicherheit gegen die aktuelle Spezifikation verifiziert werden."),
    "text_repair": ("Textkorrektur prüfen", "Der importierte Requirement-Text wurde automatisch repariert. Die vorgeschlagene Fassung muss fachlich bestätigt werden."),
    "ambiguous_import": ("Mehrdeutigen Import prüfen", "Beim Import wurden mehrdeutige oder widersprüchliche Informationen erkannt."),
    "low_confidence": ("Unsichere Zuordnung prüfen", "Die Zuordnung zur API oder Spezifikationsstelle hat eine geringe Konfidenz."),
}

def _review_reason(reason):
    key = str(reason or "review_requested")
    return _REVIEW_REASON_LABELS.get(key, (key.replace("_", " ").title(), "Für diese Anforderung liegt ein offener Review-Hinweis vor. Inhalt, Zuordnung und Formulierung müssen bestätigt werden."))

def _review_meta_html(payload):
    meta = payload.get("meta") or {}
    finding = (payload.get("decision_basis") or {}).get("finding") or {}
    title, explanation = _review_reason(meta.get("review_reason"))
    def row(label, value, cls=""):
        if value in (None, "", [], {}): return ""
        if isinstance(value, (list, dict)): value = json.dumps(value, ensure_ascii=False, indent=2)
        return '<div class="review-meta-row%s"><dt>%s</dt><dd>%s</dd></div>' % ((" "+cls) if cls else "", esc(label), esc_once(str(value)))
    rows = [
        row("Review-Grund", title, "review-meta-emphasis"),
        row("Warum ist ein Review nötig?", explanation),
        row("API-Element", meta.get("heading")),
        row("Requirement-ID", payload.get("id")),
        row("Flag-ID", payload.get("flag_id")),
        row("Status", meta.get("review_status")),
        row("Konfidenz", meta.get("confidence")),
        row("Herkunft", meta.get("origin")),
        row("Modul", meta.get("module")),
        row("Spezifikationsdokument", meta.get("document")),
        row("Seite", meta.get("page")),
        row("Upstream", meta.get("upstream")),
        row("Auffälligkeiten", finding.get("suspects")),
        row("Automatische Reparaturen", finding.get("repairs")),
        row("Review-Anweisung", (payload.get("decision_basis") or {}).get("instruction")),
        row("Text-Hash", payload.get("text_hash"), "review-meta-hash"),
    ]
    original = meta.get("text_raw")
    proposed = meta.get("text_en")
    text = '<section class="review-target" aria-labelledby="review-target-%s"><h3 id="review-target-%s">Was muss freigegeben werden?</h3><p>Bestätige, dass der folgende Requirement-Text fachlich korrekt ist, zur genannten API gehört und ohne irreführende Importartefakte veröffentlicht werden kann.</p><blockquote lang="en">%s</blockquote>' % (esc_attr(payload.get("id") or "requirement"), esc_attr(payload.get("id") or "requirement"), esc(proposed or original or ""))
    if original and proposed and original != proposed:
        text += '<details class="review-original"><summary>Importierten Originaltext anzeigen</summary><pre>%s</pre></details>' % esc(original)
    text += '</section><section class="review-context"><h3>Prüfkontext</h3><dl class="review-meta">%s</dl></section>' % "".join(rows)
    return text

def _canonical_anchor(rid, data=None):
    """0006-02: namespace anchor by project/kind if known on payload, else bare rid."""
    if data and data.get("project") and data.get("kind"):
        import sys as _sys
        from pathlib import Path as _Path
        _tools_dir = str(_Path(__file__).resolve().parent / "tools")
        if _tools_dir not in _sys.path:
            _sys.path.insert(0, _tools_dir)
        from canonical_id import canonical_id, slug
        return slug(canonical_id(rid, data["project"], data["kind"]))
    return rid


def _review_page_enhancements(main, notice_ui=None):
    """Top-Hinweis und Badges aus den eingebetteten Review-Payloads ableiten.
    notice_ui: optionales dict mit singular/plural/body fuer die Sprache des
    Sprachbaums (0008-01); None/fehlend -> deutscher Text (unveraendertes
    Verhalten fuer den kanonischen deutschen Baum)."""
    payloads = []
    for raw in re.findall(r'<script type="application/json" class="review-data">(.*?)</script>', main, re.S):
        try: payloads.append(json.loads(raw.replace("<\\/", "</")))
        except (ValueError, TypeError): pass
    if not payloads: return main, ""
    seen, items = set(), []
    for data in payloads:
        rid = str(data.get("id") or "")
        if not rid or rid in seen: continue
        seen.add(rid); items.append(data)
        # Badge direkt nach dem Funktionslink in der Methoden-/Funktionsübersicht.
        anchor_rid = _canonical_anchor(rid, data)
        # 0008-0x fix: badge must sit AFTER the whole <code class="sig">...</code>
        # signature, not right after the bare function-name link -- splicing it in
        # right after the <a class="fn"> link (the old behavior) interjected it
        # between the function name and its own parameter list, breaking the
        # signature visually ("Arg [Review] (T &&arg, ...)"). Capture everything from
        # the fn-link through the signature's closing </code> tag so the badge can be
        # emitted after that closing tag instead.
        pattern = r'(<a class="fn" href="#%s">.*?</a>.*?</code>)' % re.escape(anchor_rid)
        badge = r'\1 <a class="review-needed-badge" href="#review-%s" title="Offener Review: direkt zum Review-Panel"><span aria-hidden="true">!</span> Review</a>' % esc_attr(anchor_rid)
        main = re.sub(pattern, badge, main, count=1)
    links = []
    for data in items:
        rid = str(data.get("id")); heading = ((data.get("meta") or {}).get("heading") or rid).split(" [", 1)[0]
        heading = _html.unescape(re.sub(r"<[^>]+>", "", heading))
        links.append('<a class="page-review-link" href="#review-%s" data-review-link="%s">%s</a>' % (esc_attr(_canonical_anchor(rid, data)), esc_attr(rid), esc_once(heading)))
    nu = notice_ui or {}
    singular = nu.get("singular") or nu.get("title_singular") or "%d API element needs review"
    plural = nu.get("plural") or nu.get("title_plural") or "%d API elements need review"
    body = nu.get("body") or "Before release, requirement text and mapping must be reviewed."
    title = (singular if len(items) == 1 else plural) % len(items)
    notice = ('<aside class="page-review-notice" role="note" aria-labelledby="page-review-title">'
              '<span class="page-review-icon" aria-hidden="true">!</span><div>'
              '<strong id="page-review-title">%s</strong><p>%s</p>'
              '<div class="page-review-links">%s</div></div></aside>'
              % (title, body, "".join(links)))
    return main, notice







_KNOWN_CURATION_IDS = None
_REVIEW_REQUEST_INDEX = None


def _load_open_review_request_index(srcdir=SRC):
    """0021-06: Scan curation-queue/open+claimed for website review-request items,
    keyed by target canonical_id (and its short leaf alias).

    Exported JSON packages and submitted-but-not-ingested GitHub issues are
    intentionally invisible here: only trusted ingestion creates queue files,
    and only queue presence should affect record history/report views.
    """
    global _REVIEW_REQUEST_INDEX
    if _REVIEW_REQUEST_INDEX is None:
        _REVIEW_REQUEST_INDEX = {}
        queue_base = os.path.join(srcdir, "spec", "curation-queue")
        for state_dir in ("open", "claimed"):
            p = os.path.join(queue_base, state_dir)
            if not os.path.isdir(p):
                continue
            for name in sorted(os.listdir(p)):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(p, name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                except Exception:
                    continue
                if payload.get("item_kind") != "review-request":
                    continue
                basis = payload.get("decision_basis") or {}
                canonical_id = basis.get("target_canonical_id") or payload.get("canonical_id") or payload.get("id")
                if not canonical_id:
                    continue
                entry = {
                    "queue_state": "claimed" if state_dir == "claimed" else "open",
                    "queue_path": path,
                    "request_id": basis.get("request_id") or payload.get("id") or "",
                    "target_version_id": basis.get("target_version_id") or "",
                    "target_content_hash": basis.get("target_content_hash") or "",
                    "target_status_snapshot": basis.get("target_status_snapshot") or "",
                    "transport": basis.get("transport") or "",
                    "category": basis.get("category") or "",
                    "authoritative_actor": basis.get("authoritative_actor") or "",
                    "identity": payload.get("identity") or "",
                    "decided_by": payload.get("decided_by") or "",
                    "created": payload.get("created") or payload.get("created_at") or payload.get("decided_at") or "",
                    "source_url": basis.get("source_url") or "",
                }
                for key in (canonical_id, str(canonical_id).split("/")[-1]):
                    _REVIEW_REQUEST_INDEX[key] = entry
    return _REVIEW_REQUEST_INDEX


def _review_request_state_for_record(record_id, rec_meta=None, srcdir=SRC):
    if not record_id:
        return None
    rec_meta = dict(rec_meta or {})
    canonical_id = rec_meta.get("canonical_id") or record_id
    index = _load_open_review_request_index(srcdir)
    return index.get(canonical_id) or index.get(str(canonical_id).split("/")[-1])


def _get_known_curation_ids(srcdir=SRC):
    global _KNOWN_CURATION_IDS
    if _KNOWN_CURATION_IDS is None:
        _KNOWN_CURATION_IDS = set()
        data_path = os.path.join(srcdir, "data", "curation-items.json")
        if os.path.exists(data_path):
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                    for item in payload.get("items", []):
                        cid = item.get("canonical_id", "")
                        if cid:
                            _KNOWN_CURATION_IDS.add(cid)
                            _KNOWN_CURATION_IDS.add(cid.split("/")[-1])
            except Exception:
                pass
    return _KNOWN_CURATION_IDS

from canonical_id import parse_canonical_id, resolve_legacy, is_valid

_HREF_URL_RE = re.compile(r'href=[\"\x27](https?://[^\s\"\x27]+)[\"\x27]')
_REL_RE = re.compile(r"standards/(R[0-9]{2}-[0-9]{2})/")


def _extract_blocks_text(blocks):
    texts = []
    if isinstance(blocks, str):
        t = re.sub(r"<[^>]+>", " ", blocks)
        t = " ".join(t.split())
        if t:
            texts.append(t)
    elif isinstance(blocks, list):
        for item in blocks:
            texts.extend(_extract_blocks_text(item))
    elif isinstance(blocks, dict):
        for k, v in blocks.items():
            if k not in ("attrs", "status", "history", "upstream", "namespace_meta", "t", "src"):
                texts.extend(_extract_blocks_text(v))
    return texts


def _extract_source_url(blocks):
    if isinstance(blocks, str):
        m = _HREF_URL_RE.search(blocks)
        if m:
            return m.group(1)
    elif isinstance(blocks, list):
        for item in blocks:
            u = _extract_source_url(item)
            if u:
                return u
    elif isinstance(blocks, dict):
        for k, v in blocks.items():
            if k not in ("status", "history", "namespace_meta"):
                u = _extract_source_url(v)
                if u:
                    return u
    return ""


def _find_record_data_on_disk(record_id, srcdir=SRC):
    if not record_id:
        return None
    bare_id = str(record_id).split("/")[-1]
    records_root = os.path.join(srcdir, "spec", "records")
    if not os.path.isdir(records_root):
        return None
    parts = bare_id.split("_")
    candidate_modules = []
    if len(parts) >= 2:
        candidate_modules.append(parts[0] + "_" + parts[1])
        candidate_modules.append(parts[0])
    for mod in candidate_modules:
        p = os.path.join(records_root, mod, bare_id + ".json")
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    for root_dir, _, files in os.walk(records_root):
        if (bare_id + ".json") in files:
            try:
                with open(os.path.join(root_dir, bare_id + ".json"), "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return None


def _render_review_request_panel(record_id, rec_meta, status, page_dir_depth=0, srcdir=SRC, rec_blocks=None):
    """0021-05 / 0033-09: Render the record-page re-review trigger + bound payload data.

    Derives full canonical identity through project/kind registry, authoritative
    latest version through version store / content hash algorithm, and stable deep
    source locator without requiring synthetic per-record metadata.
    """
    rec_meta = dict(rec_meta or {})
    if not record_id:
        return ""

    parsed_cid = parse_canonical_id(str(record_id))
    if parsed_cid is not None:
        canonical_id = str(record_id)
    else:
        canonical_id = resolve_legacy(str(record_id))

    queue_state = _review_request_state_for_record(canonical_id, rec_meta, srcdir)
    if queue_state:
        rec_meta["has_open_review_request"] = True
        rec_meta.setdefault("existing_request_url", "")

    disk_record = None
    if not rec_meta.get("source_url") or not rec_meta.get("content_text"):
        disk_record = _find_record_data_on_disk(record_id, srcdir)

    source_url = rec_meta.get("source_url") or ""
    if not source_url:
        if rec_blocks:
            source_url = _extract_source_url(rec_blocks)
        if not source_url and disk_record:
            source_url = _extract_source_url(disk_record.get("blocks", []))

    release = rec_meta.get("release")
    if not release and source_url:
        m_rel = _REL_RE.search(source_url)
        if m_rel:
            release = m_rel.group(1)
    if not release:
        release = "R25-11"

    content_text = rec_meta.get("content_text") or rec_meta.get("text") or rec_meta.get("value") or ""
    if not content_text:
        if rec_blocks:
            content_text = " ".join(_extract_blocks_text(rec_blocks)).strip()
        if not content_text and disk_record:
            content_text = " ".join(_extract_blocks_text(disk_record.get("blocks", []))).strip()

    content_hash = rec_meta.get("content_hash") or (content_hash8(content_text) if content_text else None)
    version_id = rec_meta.get("version_id") or (requirement_version_id(canonical_id, release, content_text) if release and content_text else None)

    current_state = (status or {}).get("state")
    if not current_state and disk_record:
        current_state = (disk_record.get("status") or {}).get("state")
    if not current_state:
        current_state = "unspecified"

    title = rec_meta.get("title")
    if not title and disk_record:
        title = disk_record.get("title") or canonical_id
    if not title:
        title = canonical_id

    has_open_request = bool(rec_meta.get("has_open_review_request"))

    payload = {
        "canonical_id": canonical_id,
        "version_id": version_id,
        "content_hash": content_hash,
        "status": current_state,
        "source_url": source_url,
        "title": title,
        "category_default": "missing-context" if str(current_state).startswith("invalid/") else "",
        "has_open_review_request": has_open_request,
        "existing_request_url": rec_meta.get("existing_request_url") or "",
    }
    rid = esc_attr(canonical_id)
    status_label = esc(current_state)
    btn = ('<p class="review-request-duplicate" data-review-request-duplicate><strong>Review request already open.</strong> ' +
           ('<a href="%s">View request &rarr;</a>' % esc_attr(payload["existing_request_url"]) if payload["existing_request_url"] else 'A second request cannot be opened until the current one is resolved.') +
           '</p>') if has_open_request else ('<button type="button" class="review-request-trigger" data-review-request-open aria-haspopup="dialog" aria-expanded="false">Flag for review</button>' if str(current_state).startswith('valid/') else '<button type="button" class="review-request-trigger" data-review-request-open aria-haspopup="dialog" aria-expanded="false">Add supporting evidence</button>')
    queue_summary = ''
    if queue_state:
        queue_summary = (
            '<div class="review-request-queue-state"><p><strong>Open review request in queue.</strong> '
            'Current queue state: <code>%s</code>. Request ID: <code>%s</code>.</p>'
            '<dl class="review-request-bound">'
            '%s%s%s'
            '</dl></div>'
            % (
                esc(queue_state.get("queue_state") or "open"),
                esc(queue_state.get("request_id") or "-"),
                ('<dt>Target version</dt><dd><code>%s</code></dd>' % esc(queue_state.get("target_version_id"))) if queue_state.get("target_version_id") else '',
                ('<dt>Status snapshot</dt><dd><code>%s</code></dd>' % esc(queue_state.get("target_status_snapshot"))) if queue_state.get("target_status_snapshot") else '',
                ('<dt>Requester trust</dt><dd><code>%s</code>%s</dd>' % (esc(queue_state.get("identity") or '-'), (' / ' + esc(queue_state.get("authoritative_actor"))) if queue_state.get("authoritative_actor") else '')),
            )
        )

    return ('<section class="review-request-panel" data-review-request-root>'
            '<script type="application/json" class="review-request-data">%s</script>'
            '<div class="review-request-summary">'
            '<p class="review-request-lead">Request a governed re-review of this record. The record is not changed immediately.</p>'
            '<dl class="review-request-bound"><dt>Record</dt><dd><code>%s</code></dd>'
            '<dt>Status</dt><dd>%s</dd>'
            '%s%s%s</dl>%s%s'
            '<p class="review-request-state" data-review-request-state hidden></p>'
            '</div></section>'
            % (json.dumps(payload, ensure_ascii=False).replace('</', '<\/'),
               esc(canonical_id), status_label,
               ('<dt>Version</dt><dd><code>%s</code></dd>' % esc(version_id)) if version_id else '',
               ('<dt>Content hash</dt><dd><code>%s</code></dd>' % esc(content_hash)) if content_hash else '',
               ('<dt>Source</dt><dd><a href="%s">%s</a></dd>' % (esc_attr(source_url), esc(source_url))) if source_url else '',
               btn, queue_summary))

def _render_rec_history_html(record_id, status, history, page_dir_depth=0, srcdir=SRC):
    """0006-11: Render curator-visible history timeline and status badge for a record."""
    if not status and not history:
        return ""
    
    st_state = (status or {}).get("state", "unspecified")
    st_reason = (status or {}).get("reason", "")
    st_campaign = (status or {}).get("campaign", "")
    
    # State badge styling class
    badge_cls = "rec-status-neutral"
    if "valid" in st_state or st_state in ("applied", "accepted"):
        badge_cls = "rec-status-valid"
    elif "invalid" in st_state or st_state == "rejected":
        badge_cls = "rec-status-invalid"
    elif "proposed" in st_state or "hypothesized" in st_state or "pending" in st_state:
        badge_cls = "rec-status-proposed"

    rows = []
    for h in (history or []):
        dt = esc(h.get("date", "-"))
        actor = esc(h.get("actor", "-"))
        frm = esc(h.get("from") or "none")
        to = esc(h.get("to") or "-")
        reason = esc(h.get("reason", ""))
        camp = esc(h.get("campaign", ""))
        rows.append(f"<tr><td>{dt}</td><td><span class=\"rec-actor\">{actor}</span></td><td><code>{frm}</code> &rarr; <code>{to}</code></td><td>{reason}</td><td><small>{camp}</small></td></tr>")

    history_table = ""
    if rows:
        history_table = f"""<table class="rec-history-table">
<thead><tr><th>Date</th><th>Actor</th><th>Transition</th><th>Reason / Rationale</th><th>Campaign</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>"""

    curation_report_link = ""
    known_cids = _get_known_curation_ids(srcdir)
    if record_id and record_id in known_cids:
        rel_prefix = "../" * page_dir_depth
        curation_report_link = f'<p class="rec-curation-link"><a href="{rel_prefix}curation-report.html#{esc_attr(record_id)}">View in Curation Report &rarr;</a></p>'

    html = f"""<details class="rec-history-panel">
<summary>
<span class="rec-status-badge {badge_cls}">Status: {esc(st_state)}</span>
<span class="rec-history-summary-text">Curation & History ({len(history or [])} transition{'s' if len(history or []) != 1 else ''})</span>
</summary>
<div class="rec-history-body">
<dl class="rec-status-details">
<dt>Current State</dt><dd><code>{esc(st_state)}</code></dd>
{f'<dt>Reason</dt><dd>{esc(st_reason)}</dd>' if st_reason else ''}
{f'<dt>Campaign</dt><dd><code>{esc(st_campaign)}</code></dd>' if st_campaign else ''}
</dl>
{history_table}
{curation_report_link}
</div>
</details>"""
    return html

def render_blocks(blocks, page_dir_depth, srcdir=SRC, record_id=None, requirement_meta=None):
    out = []
    for b in blocks:
        t = b["t"]
        if t == "html":
            out.append(b["html"])
        elif t == "ai":
            with open(os.path.join(srcdir, b["src"]), encoding="utf-8") as f:
                out.append(f.read().rstrip("\n"))
        elif t == "svg":
            attrs = [[k, v] for k, v in b["wrap_attrs"]]
            out.append(open_tag("div", attrs))
            out.append(b.get("pre", ""))
            with open(os.path.join(srcdir, b["src"]), encoding="utf-8") as f:
                out.append(f.read().rstrip("\n"))
            out.append(b.get("inner_tail", ""))
            out.append("</div>")
        elif t == "rec":
            rec_requirement_meta = b.get("requirement_meta") or requirement_meta
            rec_id = dict(b.get("attrs", [])).get("id") or record_id
            review_request_html = _render_review_request_panel(rec_id, b.get("review_request") or {}, b.get("status"), page_dir_depth, srcdir, rec_blocks=b.get("blocks"))
            history_html = _render_rec_history_html(rec_id, b.get("status"), b.get("history"), page_dir_depth, srcdir)
            out.append(open_tag("article", b["attrs"]))
            out.append(esc(b.get("lead", "")))
            out.append(render_blocks(b["blocks"], page_dir_depth, srcdir, rec_id, rec_requirement_meta))
            if review_request_html:
                out.append(review_request_html)
            if history_html:
                out.append(history_html)
            out.append("</article>")
        elif t == "fold":
            out.append(open_tag("details", b["attrs"]))
            out.append("<summary>")
            out.append(b["summary"])
            out.append("</summary>")
            out.append(esc(b.get("lead", "")))
            out.append(render_blocks(b["blocks"], page_dir_depth, srcdir, dict(b.get("attrs", [])).get("id") or record_id, b.get("requirement_meta") or requirement_meta))
            out.append("</details>")
        elif t == "props":
            out.append(open_tag("table", b["attrs"]))
            for r in b["rows"]:
                out.append("<tr>")
                out.append(open_tag("th", r.get("th_attrs", [])))
                out.append(r["th"])
                out.append("</th>")
                out.append(open_tag("td", r.get("td_attrs", [])))
                out.append(r["td"])
                out.append("</td></tr>")
            out.append("</table>")
        elif t == "requirement_text":
            flags = [f for f in b.get("review_flags", []) if f.get("status", "open") == "open"]
            review_state = str(b.get("review_status") or b.get("status") or (requirement_meta or {}).get("review_status") or "").strip().lower()
            reviewable = bool(flags or b.get("suspects") or review_state in ("pending", "review", "open"))
            attrs = [["class", "reqtext" + (" unreviewed" if reviewable else "")], ["lang", "en"]]
            if b.get("status_flag"):
                out.append('<p class="reqstatus">%s</p>' % esc(b["status_flag"]))
            out.append(open_tag("p", attrs))
            out.append(esc(b["text_en"]))
            out.append("</p>")
            if reviewable:
                meta = dict(requirement_meta or {})
                basis = {"finding": {"suspects": b.get("suspects", []), "repairs": b.get("repairs", [])},
                         "instruction": (flags[0].get("instruction") if flags else None)}
                payload = {"id": record_id or b.get("requirement_id"),
                           "flag_id": (flags[0].get("id") if flags else record_id),
                           "text_hash": hashlib.sha256(json.dumps({"raw": b.get("text_raw"), "repairs": b.get("repairs", [])}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
                           "decision_basis": basis,
                           "meta": {"heading": meta.get("heading"), "review_reason": meta.get("review_reason"),
                                    "review_status": review_state or meta.get("review_status"), "confidence": meta.get("confidence"),
                                    "origin": meta.get("origin"), "module": meta.get("module"), "document": meta.get("document"),
                                    "page": meta.get("page"), "upstream": meta.get("upstream"), "trace": meta.get("trace"),
                                    "text_raw": b.get("text_raw"), "text_en": b.get("text_en")}}
                rid = esc_attr(payload["id"] or "requirement")
                out.append('<details class="review-panel" id="review-%s"><summary><span class="review-summary-mark" aria-hidden="true">?</span><span><span data-i18n="review">Validate requirement</span><small>%s</small></span><span class="review-summary-state" aria-hidden="true"></span></summary>' % (rid, esc_once(meta.get("heading") or payload["id"] or "")))
                out.append('<script type="application/json" class="review-data">%s</script>' % json.dumps(payload, ensure_ascii=False).replace("</", "<\/"))
                out.append('<div class="review-panel-body">%s<div class="review-fields">' % _review_meta_html(payload))
                out.append('<div class="review-form"><label class="review-field review-field-wide"><span data-i18n="why">Rationale</span><textarea class="review-why" required></textarea></label></div><div class="review-actions"><p class="review-identity" data-review-identity hidden></p><div class="review-decision" role="group" aria-label="Decision"><button type="button" class="review-choice review-choice-accept" data-review-outcome="accept"><span class="review-choice-icon" aria-hidden="true">✓</span><span data-i18n="accept">Approve</span></button><button type="button" class="review-choice review-choice-reject" data-review-outcome="reject"><span class="review-choice-icon" aria-hidden="true">×</span><span data-i18n="reject">Reject</span></button></div></div></div></div></details>')
        elif t == "params":
            out.append(open_tag("table", b["attrs"]))
            for r in b["rows"]:
                out.append("<tr>")
                for c in r["cells"]:
                    out.append(open_tag(c["tag"], c.get("attrs", [])))
                    out.append(c["html"])
                    out.append("</%s>" % c["tag"])
                out.append("</tr>")
            out.append("</table>")
        else:
            raise ValueError("unbekannter Blocktyp: %r" % t)
        out.append(b.get("tail", ""))
    return "".join(out)


def render_page(page, footers, page_tmpl, srcdir=SRC, lang=KANONISCH, notice_ui=None):
    """Seite rendern. lang steuert nur das Chrome (html-lang, dir, Umschalter);
    für Sprachbäume muss das Seitenmodell bereits übersetzt und page["file"]
    der Pfad OHNE Sprachpräfix sein (der Aufrufer schreibt nach <lang>/…)."""
    depth = page["file"].count("/") + (1 if lang != KANONISCH else 0)
    prefix = "../" * depth
    # 0008-02: "prefix" is for SHARED root assets (style.css, fold.js) which live
    # once at the tree root, so it must cross the language subdir too. The home
    # link must instead land in <lang>/index.html (or the German root index.html
    # when lang is canonical), which is only page-file-depth "../" levels up from
    # a page inside the language tree -- one level shallower than "prefix".
    lang_prefix = "../" * page["file"].count("/")
    body_cls = ' class="%s"' % esc_attr(page["body_class"]) if page.get("body_class") else ""
    main = render_blocks(page["main"], depth, srcdir)
    main, review_notice = _review_page_enhancements(main, notice_ui)
    has_review = bool(review_notice)
    if review_notice:
        main = review_notice + main
    graph_marker = "@@COMPONENT_GRAPH_JSON@@"
    if graph_marker in main:
        graph_file = os.path.join(ROOT, "data", "component-graph.json")
        with open(graph_file, encoding="utf-8") as f:
            graph_json = f.read().replace("</", "<\/")
        main = main.replace(graph_marker, graph_json)
    return page_tmpl % {
        "title": esc(page["title"]),
        "htmllang": lang,
        "dir": ' dir="rtl"' if lang in RTL else "",
        "langswitch": "" if page.get("nolang") else langswitch_html(page["file"], lang),
        "css": prefix + "style.css",
        "js": prefix + "fold.js",
        "review_js": prefix + "review.js",
        "review_request_js": prefix + "review_request.js",
        "reviewbar": ('<div class="reviewbar" aria-label="Requirement reviews"><button type="button" class="reviewbar-package" data-review-open aria-expanded="false"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M21 8v13H3V8M1 3h22v5H1zM10 12h4"/></svg><span>Reviews</span><span class="review-count" data-review-count>0</span></button><button type="button" class="reviewbar-github" data-review-token><svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg><span data-gh-label>Connect GitHub</span><span class="reviewbar-status" aria-hidden="true"></span></button></div>' if has_review else ""),
        "cytoscape_js": prefix + "cytoscape.min.js",
        "graph_js": prefix + "component-graph.js",
        "home": lang_prefix + "index.html",
        "body_class": body_cls,
        "nav": page["nav_html"],
        "main_lead": esc(page.get("main_lead", "")),
        "main": main,
        "footer": footers[page["footer"]],
    }


PAGE_TEMPLATE_FILE = os.path.join(TMPL_DIR, "page.html.tmpl")


def load_templates(srcdir=SRC):
    with open(os.path.join(srcdir, "templates", "page.html.tmpl"), encoding="utf-8") as f:
        page_tmpl = f.read()
    with open(os.path.join(srcdir, "templates", "footers.json"), encoding="utf-8") as f:
        footers = json.load(f)
    return page_tmpl, footers


# ---------------------------------------------------------------- Vergleich

def _norm_ws(s):
    if s is None:
        return ""
    return s


def dom_equal(e1, e2, path="", lenient=False, errors=None):
    """Strukturvergleich zweier Elementbäume. lenient: Whitespace-only-Texte
    werden auf Ebene von body/header/footer normalisiert."""
    if errors is None:
        errors = []

    def txt(t, lenient_here):
        t = t or ""
        if lenient_here and (t.strip() == ""):
            return ""
        return t

    if e1.tag != e2.tag:
        errors.append("%s: tag %r != %r" % (path, e1.tag, e2.tag))
        return errors
    def norm_attrs(d):
        # lxml serialisiert Leerzeichen in URLs als %20 — äquivalent behandeln
        return {k: (v.replace(" ", "%20") if k == "href" else v) for k, v in d.items()}

    if norm_attrs(dict(e1.attrib)) != norm_attrs(dict(e2.attrib)):
        errors.append("%s<%s>: attrs %r != %r" % (path, e1.tag, dict(e1.attrib), dict(e2.attrib)))
    lenient_here = lenient or (isinstance(e1.tag, str) and e1.tag in ("body", "header", "footer", "html", "head"))
    if txt(e1.text, lenient_here) != txt(e2.text, lenient_here):
        errors.append("%s<%s>: text %r != %r" % (path, e1.tag, (e1.text or "")[:80], (e2.text or "")[:80]))
    c1 = list(e1)
    c2 = list(e2)
    if len(c1) != len(c2):
        errors.append("%s<%s>: children %d != %d" % (path, e1.tag, len(c1), len(c2)))
        return errors
    for i, (a, b) in enumerate(zip(c1, c2)):
        if txt(a.tail, lenient_here) != txt(b.tail, lenient_here):
            errors.append("%s<%s>[%d]: tail %r != %r" % (path, e1.tag, i, (a.tail or "")[:80], (b.tail or "")[:80]))
        dom_equal(a, b, "%s/%s[%d]" % (path, str(a.tag)[:20], i), lenient, errors)
    return errors


def compare_html(file1, html2_text):
    d1 = LH.parse(file1).getroot()
    d2 = LH.document_fromstring(html2_text)
    return dom_equal(d1, d2)
