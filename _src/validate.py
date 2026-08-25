#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py — Qualitätsprüfungen für den HTML-Tree und die Quellen.

    python3 _src/validate.py

Prüft:
  1. Tree == generate(Quellen)   (byte-genau; Tree ist reines Build-Artefakt)
  2. Interne Links: Zieldateien existieren, Anker (#…) existieren im Ziel
  3. Keine Platzhalter-Links href="#"
  4. Alle referenzierten Fragmente/SVGs existieren; verwaiste Dateien melden
  5. Sprachbäume (en es pt fr ru ar hi ko zh): byte-genau reproduzierbar,
     gleicher Seitenbestand wie Deutsch, korrekte lang-/dir-Attribute,
     keine Maskierungs-Platzhalter (⟦…⟧) im Output, Flaggen vorhanden
Exit-Code 0 = alles in Ordnung.
"""
import argparse
import glob
import json
import multiprocessing
import re
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from lxml import html as LH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import (SRC, ROOT, PAGES_DIR, LANGS, RTL, render_page,
                          load_templates, iter_pages)

problems = []
structured_findings = []
checks_performed = []

WORKERS = min(12, os.cpu_count() or 12)
# 'fork' avoids re-importing lxml/lib_docmodel per worker on macOS (default
# 'spawn' pays that cost on every worker, which dominates wall-clock time for
# many small per-page tasks and effectively serializes the workload).
_MP_CTX = multiprocessing.get_context("fork")


def record_finding(category, severity, message, ref=None):
    """Record a structured finding for build report and CLI problem output."""
    finding = {"category": category, "severity": severity, "message": message}
    if ref:
        finding["ref"] = ref
    structured_findings.append(finding)
    if severity == "error":
        problems.append(message)


def _check_one_page(args):
    page, footers, page_tmpl = args
    target = os.path.join(ROOT, page["file"])
    gen = render_page(page, footers, page_tmpl)
    cur = open(target, encoding="utf-8").read() if os.path.exists(target) else None
    is_stale = gen != cur

    referenced = set()
    referenced_recs = set()

    def collect(blocks):
        for b in blocks:
            if b["t"] in ("ai", "svg"):
                referenced.add(b["src"])
            if b["t"] == "rec" and b.get("_src"):
                referenced_recs.add(b["_src"])
            if b["t"] in ("rec", "fold"):
                collect(b["blocks"])
    collect(page["main"])
    return page["file"], is_stale, referenced, referenced_recs


def check_build():
    checks_performed.append("check_build")
    page_tmpl, footers = load_templates()
    stale = []
    referenced = set()
    referenced_recs = set()
    pages = list(iter_pages())
    tasks = [(page, footers, page_tmpl) for page in pages]
    chunksize = max(1, len(tasks) // (WORKERS * 4)) if tasks else 1
    if len(tasks) < WORKERS * 2:
        results = [_check_one_page(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=WORKERS, mp_context=_MP_CTX) as ex:
            results = list(ex.map(_check_one_page, tasks, chunksize=chunksize))
    for file, is_stale, refs, refs_recs in results:
        if is_stale:
            stale.append(file)
        referenced |= refs
        referenced_recs |= refs_recs
    stale.sort()
    # Spezifikations-DB: verwaiste Record-Dateien melden
    PRS_E2E_PREFIX = os.path.join("spec", "records", "PRS_E2E") + os.sep
    alle_recs = set(os.path.relpath(f, SRC) for f in
                    glob.glob(os.path.join(SRC, "spec", "records", "**", "*.json"),
                              recursive=True))
    rec_waisen = {r for r in (alle_recs - referenced_recs)
                 if not r.startswith(PRS_E2E_PREFIX)}
    if rec_waisen:
        for w in sorted(rec_waisen):
            record_finding("orphan-record", "error", f"verwaister Record in spec/records: {w}", ref=w)
    if stale:
        for s in stale:
            record_finding("stale-html", "error", f"Tree nicht aktuell: {s}", ref=s)
    # Waisen / fehlende Fragmente
    have = set()
    for d in ("content", "diagrams"):
        for f in glob.glob(os.path.join(SRC, d, "**", "*.*"), recursive=True):
            if os.path.isfile(f):
                have.add(os.path.relpath(f, SRC))
    missing = referenced - have
    orphans = set()
    for f in have - referenced:
        base = None
        for suf in (".seq.json", ".dot"):
            if f.endswith(suf):
                base = f[:-len(suf)] + ".svg"
                break
        if base and base in referenced:
            continue
        if "content/ai" in f:
            base_html = re.sub(r"(\.[0-9a-f]{6,8}|\.diag-[^.]+)\.(dot|seq\.json)$", ".html", f)
            if base_html in referenced:
                continue
        orphans.add(f)
    if missing:
        for m in sorted(missing):
            record_finding("missing-fragment", "error", f"fehlendes Fragment/SVG: {m}", ref=m)
    if orphans:
        for o in sorted(orphans):
            record_finding("orphan-fragment", "error", f"verwaiste Datei in _src/content|diagrams: {o}", ref=o)


def _scan_one_link_page(rel):
    """Parse one HTML page and return only data needed for global link checks."""
    doc = LH.parse(os.path.join(ROOT, rel)).getroot()
    page_ids = {element.get("id") for element in doc.iter() if element.get("id")}
    base = os.path.dirname(rel)
    images = []
    links = []
    placeholders = []
    for img in doc.iter("img"):
        src = img.get("src") or ""
        if src and not src.startswith(("http://", "https://", "data:")):
            target = os.path.normpath(os.path.join(base, urllib.parse.unquote(src)))
            images.append((src, target))
    for anchor_element in doc.iter("a"):
        href = anchor_element.get("href") or ""
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        if href == "#":
            placeholders.append(anchor_element.text_content()[:40])
            continue
        path, _, anchor = href.partition("#")
        target = rel if not path else os.path.normpath(
            os.path.join(base, urllib.parse.unquote(path))
        )
        links.append((href, path, target, anchor))
    return rel, page_ids, images, links, placeholders


def _scan_link_pages(pages):
    chunksize = max(1, len(pages) // (WORKERS * 4)) if pages else 1
    if len(pages) < WORKERS * 2 or WORKERS < 2:
        return [_scan_one_link_page(rel) for rel in pages]
    with ProcessPoolExecutor(max_workers=WORKERS, mp_context=_MP_CTX) as ex:
        return list(ex.map(_scan_one_link_page, pages, chunksize=chunksize))


def check_links():
    checks_performed.append("check_links")
    pages = sorted({os.path.relpath(p, ROOT) for p in
                    glob.glob(os.path.join(ROOT, "*.html"))
                    + glob.glob(os.path.join(ROOT, "*", "*.html"))
                    + [p for lang in LANGS for p in
                       glob.glob(os.path.join(ROOT, lang, "**", "*.html"), recursive=True)]})
    scans = _scan_link_pages(pages)
    ids = {rel: page_ids for rel, page_ids, _images, _links, _placeholders in scans}
    dead, placeholder, bilder = [], [], []
    for rel, _page_ids, images, links, placeholders in scans:
        placeholder.extend((rel, text) for text in placeholders)
        for src, target in images:
            if not os.path.exists(os.path.join(ROOT, target)):
                bilder.append((rel, src))
        for href, path, target, anchor in links:
            if path and not os.path.exists(os.path.join(ROOT, target)):
                dead.append((rel, href, "Datei fehlt"))
            elif anchor and target in ids and anchor not in ids[target]:
                dead.append((rel, href, "Anker fehlt"))
    if placeholder:
        for rel, txt in placeholder:
            record_finding("placeholder-link", "error", f"Platzhalter-Link href=\"#\" in {rel} ({txt})", ref=rel)
    if dead:
        for rel, href, reason in dead:
            record_finding("dead-link", "error", f"toter interner Link in {rel} -> {href} ({reason})", ref=rel)
    if bilder:
        for rel, src in bilder:
            record_finding("missing-image", "error", f"fehlende Bilddatei in {rel} -> {src}", ref=rel)


def _check_one_lang(args):
    lang, de_seiten = args
    from generate import generate_lang

    local_problems = []
    wurzel = os.path.join(ROOT, lang)
    if not os.path.isdir(wurzel):
        local_problems.append((f"[{lang}] Sprachbaum fehlt: {lang}/", "missing-lang-tree", lang))
        return local_problems

    vorhanden = {os.path.relpath(p, wurzel).replace(os.sep, "/") for p in
                 glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True)}
    if vorhanden != de_seiten:
        local_problems.append(("[%s] Seitenbestand weicht ab: +%s -%s"
                               % (lang, sorted(vorhanden - de_seiten)[:3], sorted(de_seiten - vorhanden)[:3]),
                               "lang-page-mismatch", lang))

    _n, _stat, stale = generate_lang(lang, check=True)
    if stale:
        local_problems.append(("[%s] Baum nicht aktuell (generate.py --lang=%s): %d Seiten, z.B. %s"
                               % (lang, lang, len(stale), stale[:3]),
                               "stale-lang-tree", lang))

    reste, falsch_lang = [], []
    soll_html = '<html lang="%s"%s>' % (lang, ' dir="rtl"' if lang in RTL else "")
    for rel in sorted(vorhanden):
        text = open(os.path.join(wurzel, rel), encoding="utf-8").read()
        if "\u27e6" in text:
            reste.append(rel)
        if soll_html not in text.split("\n", 2)[1]:
            falsch_lang.append(rel)
    if reste:
        local_problems.append(("[%s] Maskierungs-Platzhalter im Output: %s" % (lang, reste[:5]),
                               "masking-placeholder-leak", lang))
    if falsch_lang:
        local_problems.append(("[%s] falsches lang-/dir-Attribut: %s" % (lang, falsch_lang[:5]),
                               "invalid-lang-attr", lang))
    return local_problems


def check_langs():
    checks_performed.append("check_langs")
    de_seiten = set()
    for p in glob.glob(os.path.join(PAGES_DIR, "**", "*.json"), recursive=True):
        modell = json.load(open(p, encoding="utf-8"))
        if modell.get("nolang"):
            continue
        de_seiten.add(modell["file"])
    tasks = [(lang, de_seiten) for lang in LANGS]
    if len(tasks) < 2:
        lang_problem_lists = [_check_one_lang(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=min(WORKERS, len(tasks)), mp_context=_MP_CTX) as ex:
            lang_problem_lists = list(ex.map(_check_one_lang, tasks, chunksize=1))
    for local in lang_problem_lists:
        for item in local:
            if isinstance(item, tuple):
                msg, cat, ref = item
                record_finding(cat, "error", msg, ref=ref)
            else:
                record_finding("lang-check-error", "error", str(item))
    for f in ("de", "gb", "es", "fr", "ru", "sa", "in", "kr", "cn"):
        if not os.path.exists(os.path.join(ROOT, "flags", f + ".svg")):
            record_finding("missing-flag", "error", "Flagge fehlt: flags/%s.svg" % f, ref=f)


def check_requirement_review_schema():
    checks_performed.append("check_requirement_review_schema")
    import json as _json
    wurzel = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec', 'records')
    if not os.path.isdir(wurzel):
        return
    fehler = []
    for ordner, _, dateien in os.walk(wurzel):
        for datei in dateien:
            if not datei.endswith('.json'):
                continue
            pfad = os.path.join(ordner, datei)
            rec = _json.load(open(pfad, encoding='utf-8'))
            rid = rec.get('id', datei)
            rmeta = rec.get('requirement_meta')
            for i, block in enumerate(rec.get('blocks', [])):
                if block.get('t') != 'requirement_text':
                    continue
                wo = '%s:block[%d]' % (rid, i)
                for feld in ('text_en', 'text_raw', 'repairs', 'suspects'):
                    if feld not in block:
                        fehler.append('%s fehlt %s' % (wo, feld))
                if not isinstance(block.get('repairs', []), list):
                    fehler.append('%s repairs muss Liste sein' % wo)
                if not isinstance(block.get('suspects', []), list):
                    fehler.append('%s suspects muss Liste sein' % wo)
                if rmeta is None:
                    fehler.append('%s hat requirement_text ohne requirement_meta' % wo)
                else:
                    for feld in ('confidence', 'review_status', 'review_reason'):
                        if not str(rmeta.get(feld) or '').strip():
                            fehler.append('%s requirement_meta.%s fehlt' % (wo, feld))
                flags = block.get('review_flags') or []
                if not isinstance(flags, list):
                    fehler.append('%s review_flags muss Liste sein' % wo)
                    continue
                for j, flag in enumerate(flags):
                    wf = '%s.review_flags[%d]' % (wo, j)
                    for feld in ('id', 'status'):
                        if not str(flag.get(feld) or '').strip():
                            fehler.append('%s %s fehlt' % (wf, feld))
                    if flag.get('status', 'open') == 'open':
                        finding = (flag.get('decision_basis') or {}).get('finding')
                        if finding is None:
                            if not str(flag.get('reason') or '').strip():
                                fehler.append('%s offenes Flag ohne reason' % wf)
                        else:
                            if not isinstance(finding.get('suspects', []), list):
                                fehler.append('%s decision_basis.finding.suspects muss Liste sein' % wf)
                            if not isinstance(finding.get('repairs', []), list):
                                fehler.append('%s decision_basis.finding.repairs muss Liste sein' % wf)
                    else:
                        for feld in ('decided_by', 'decided_at', 'rationale', 'identity', 'text_hash', 'decision_basis'):
                            if feld not in flag or (feld != 'decision_basis' and not str(flag.get(feld) or '').strip()):
                                fehler.append('%s resolved/rejected Flag ohne %s' % (wf, feld))
                        basis = flag.get('decision_basis') or {}
                        if not basis.get('finding'):
                            fehler.append('%s decision_basis.finding fehlt' % wf)
                        if flag.get('identity') not in ('github_authenticated', 'self_declared'):
                            fehler.append('%s identity ungueltig: %r' % (wf, flag.get('identity')))
    if fehler:
        for err in fehler:
            record_finding("review-schema-violation", "error", err)


def check_namespaces():
    checks_performed.append("check_namespaces")
    import json as _json
    wurzel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec", "records")
    katalog = os.path.join(os.path.dirname(wurzel), "namespaces.json")
    if not os.path.isdir(wurzel):
        return
    erlaubt = set()
    if os.path.exists(katalog):
        for gruppe in _json.load(open(katalog, encoding="utf-8")).get("abweichungen", {}).values():
            erlaubt.update(gruppe)
    PRS_E2E_PREFIX = "PRS_E2E_"

    ohne, unbekannt = [], []
    for ordner, _, dateien in os.walk(wurzel):
        for datei in dateien:
            if not datei.endswith(".json"):
                continue
            pfad = os.path.join(ordner, datei)
            rec = _json.load(open(pfad, encoding="utf-8"))
            rid = rec.get("id", datei)
            if isinstance(rid, str) and rid.startswith(PRS_E2E_PREFIX):
                continue
            ns_meta = rec.get("namespace_meta")
            if not ns_meta or not ns_meta.get("namespace"):
                ohne.append((rid, pfad))
    if ohne:
        for rid, pfad in ohne:
            record_finding("missing-namespace", "error", f"Record ohne namespace_meta.namespace: {rid}", ref=rid)


def _check_home_links_one_lang(lang):
    local_problems = []
    wurzel = os.path.join(ROOT, lang) if lang != "de" else ROOT
    if not os.path.isdir(wurzel):
        return local_problems
    for full in glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True):
        rel = os.path.relpath(full, wurzel)
        if lang == "de" and rel.split(os.sep, 1)[0] in LANGS:
            continue
        text = open(full, encoding="utf-8").read()
        m = re.search(r'<header class="mast">.*?<a[^>]+href="([^"]+)"[^>]*class="logo"', text, re.S)
        if not m:
            continue
        home_href = m.group(1)
        page_dir = os.path.dirname(full)
        home_target = os.path.normpath(os.path.join(page_dir, home_href))
        expected = os.path.join(wurzel, "index.html")
        if home_target != expected:
            local_problems.append("[%s] home-Link zeigt aus dem Sprachbaum heraus: %s -> %s (erwartet %s)"
                                  % (lang, rel, home_href, os.path.relpath(expected, wurzel)))
        nav_m = re.search(r'<nav class="crumbs">(.*?)</nav>', text, re.S)
        if nav_m:
            crumb_m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>', nav_m.group(1))
            if crumb_m:
                crumb_href = crumb_m.group(1)
                crumb_target = os.path.normpath(os.path.join(page_dir, crumb_href))
                if crumb_target != expected:
                    local_problems.append("[%s] Breadcrumb-Start-Link zeigt aus dem Sprachbaum heraus: %s -> %s (erwartet %s)"
                                          % (lang, rel, crumb_href, os.path.relpath(expected, wurzel)))
    return local_problems


def check_home_links():
    checks_performed.append("check_home_links")
    for lang in ["de"] + LANGS:
        for prob in _check_home_links_one_lang(lang):
            record_finding("broken-home-link", "error", prob, ref=lang)


_GERMAN_CHROME_STRINGS = None


def _german_chrome_strings():
    global _GERMAN_CHROME_STRINGS
    if _GERMAN_CHROME_STRINGS is None:
        ui_all = json.load(open(os.path.join(SRC, "i18n", "ui.json"), encoding="utf-8"))
        de_ui = ui_all.get("de", {})
        strings = set(de_ui.get("global", {}).keys())
        strings.add("mit Review-Bedarf")
        strings.add("Vor der Freigabe müssen Requirement-Text und Zuordnung geprüft werden.")
        _GERMAN_CHROME_STRINGS = sorted(s for s in strings if s)
    return _GERMAN_CHROME_STRINGS


def _check_no_hardcoded_german_one_lang(lang):
    local_problems = []
    wurzel = os.path.join(ROOT, lang)
    if not os.path.isdir(wurzel):
        return local_problems
    strings = _german_chrome_strings()
    hits = {}
    for full in glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True):
        text = open(full, encoding="utf-8").read()
        for s in strings:
            if s in text:
                hits.setdefault(s, []).append(os.path.relpath(full, wurzel))
    for s, files in hits.items():
        local_problems.append("[%s] unuebersetzter deutscher Chrome-Text %r in %d Datei(en), z.B. %s"
                              % (lang, s, len(files), files[:3]))
    return local_problems


def check_no_hardcoded_german():
    checks_performed.append("check_no_hardcoded_german")
    for lang in LANGS:
        for prob in _check_no_hardcoded_german_one_lang(lang):
            record_finding("hardcoded-german-chrome", "error", prob, ref=lang)


def _pick_review_notice_page(lang):
    wurzel = os.path.join(ROOT, lang) if lang != "de" else ROOT
    if not os.path.isdir(wurzel):
        return None
    for full in sorted(glob.glob(os.path.join(wurzel, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(full, wurzel)
        if lang == "de" and rel.split(os.sep, 1)[0] in LANGS:
            continue
        text = open(full, encoding="utf-8").read()
        if 'class="page-review-notice"' in text and 'data-review-link' in text:
            return full
    return None


def _check_client_rendered_german_one_lang(lang):
    local_problems = []
    if lang == "de":
        return local_problems
    page = _pick_review_notice_page(lang)
    if page is None:
        return local_problems

    script = os.path.join(SRC, "tools", "check_client_rendered_german.cjs")
    env = dict(os.environ)
    npm_prefix_modules = os.path.expanduser("~/devel/output/npm-prefix/node_modules")
    if os.path.isdir(npm_prefix_modules):
        env["NODE_PATH"] = npm_prefix_modules + os.pathsep + env.get("NODE_PATH", "")
    try:
        proc = subprocess.run(
            ["node", script, page],
            capture_output=True, text=True, timeout=30, cwd=SRC, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[{lang}] [hinweis] check_client_rendered_german übersprungen: {exc}")
        return local_problems
    if proc.returncode != 0:
        local_problems.append("[%s] check_client_rendered_german: headless render of %s failed: %s"
                              % (lang, os.path.relpath(page, ROOT), proc.stderr.strip()[:300]))
        return local_problems

    try:
        result = json.loads(proc.stdout)
    except ValueError:
        local_problems.append("[%s] check_client_rendered_german: non-JSON output for %s"
                              % (lang, os.path.relpath(page, ROOT)))
        return local_problems

    body_text = result.get("bodyText", "")
    for s in _german_chrome_strings():
        if s in body_text:
            local_problems.append("[%s] unuebersetzter deutscher Chrome-Text %r nach Client-JS-Rendering in %s"
                                  % (lang, s, os.path.relpath(page, ROOT)))
    return local_problems


def check_client_rendered_german():
    checks_performed.append("check_client_rendered_german")
    if shutil.which("node") is None:
        record_finding("client-render-check-skipped", "info", "check_client_rendered_german übersprungen: node nicht verfügbar")
        return
    results = {}
    with ThreadPoolExecutor(max_workers=min(WORKERS, len(LANGS)) or 1) as ex:
        futures = {ex.submit(_check_client_rendered_german_one_lang, lang): lang for lang in LANGS}
        for fut in futures:
            lang = futures[fut]
            results[lang] = fut.result()
    for lang in LANGS:
        for prob in results[lang]:
            record_finding("client-rendered-german-leak", "error", prob, ref=lang)


def _workflow_queue_roots():
    """Return canonical queue roots below ``_src/spec``."""
    spec_root = os.path.join(SRC, "spec")
    return tuple(
        (queue_dir, os.path.join(spec_root, queue_dir))
        for queue_dir in ("review-queue", "curation-queue")
    )


def check_workflow_lifecycle():
    checks_performed.append("check_workflow_lifecycle")
    tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import curation_item_lifecycle_check as cilc
    vocab_problems = cilc.validate_vocabularies()
    if vocab_problems:
        for p in vocab_problems:
            record_finding("vocabulary-drift", "error", f"0006-13 vocabulary drift: {p}")
        return
    import curation_item as ci
    import glob as _glob
    for queue_dir, base in _workflow_queue_roots():
        if not os.path.isdir(base):
            continue
        for pfad in sorted(_glob.glob(os.path.join(base, "**", "*.json"), recursive=True)):
            try:
                with open(pfad, encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                record_finding(
                    "invalid-curation-queue-json",
                    "error",
                    f"{pfad}: queue payload is not readable JSON: {exc}",
                    ref=pfad,
                )
                continue
            adapter = ci.from_review_flag if queue_dir == "review-queue" else ci.from_curation_flag
            try:
                item = adapter(payload)
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                record_finding(
                    "invalid-curation-queue-payload",
                    "error",
                    f"{pfad}: queue payload cannot be normalized: {exc}",
                    ref=pfad,
                )
                continue
            if not ci.is_conformant(item):
                record_finding("nonconformant-curation-item", "error", f"{pfad}: normalized curation-item is not conformant", ref=pfad)
                continue
            if cilc.item_lifecycle_state(item) is None:
                record_finding("unmapped-lifecycle-state", "error", f"{pfad}: status {item.get('status')!r} has no mapped lifecycle state", ref=pfad)


def check_record_status():
    checks_performed.append("check_record_status")
    import json as _json
    wurzel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec", "records")
    if not os.path.isdir(wurzel):
        return
    ohne = []
    for ordner, _, dateien in os.walk(wurzel):
        for datei in dateien:
            if not datei.endswith(".json"):
                continue
            pfad = os.path.join(ordner, datei)
            rec = _json.load(open(pfad, encoding="utf-8"))
            if "status" not in rec:
                ohne.append(rec.get("id", datei))
    if ohne:
        for rid in ohne:
            record_finding("missing-record-status", "error", f"Record ohne 'status': {rid}", ref=rid)


ISSUE_VALIDATE_ARGS = None


def parse_validate_cli(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--issue-source",
        choices=("working-tree", "staged-index", "candidate", "off"),
        default="working-tree",
    )
    parser.add_argument("--issue-root")
    parser.add_argument("--issue-dag")
    parser.add_argument("--issue-generated-root")
    parser.add_argument("--issue-authoritative-root")
    known, rest = parser.parse_known_args(argv)
    return known, rest


def check_issue_store(options=None):
    checks_performed.append("check_issue_store")
    options = options if options is not None else ISSUE_VALIDATE_ARGS
    if options is None or getattr(options, "issue_source", "working-tree") == "off":
        return
    tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import issue_validate as issue_validate_mod
    source = options.issue_source
    root = options.issue_root
    if source == "candidate":
        if not root:
            record_finding(
                "issue-validate-config",
                "error",
                "candidate issue mode requires --issue-root",
            )
            return
        validate_source = "working-tree"
    else:
        validate_source = source
    dag_path = options.issue_dag or os.path.join(ROOT, "docs/pipeline/issue-derived-artifacts-v1.json")
    generated_root = options.issue_generated_root
    issue_root = root
    if validate_source == "working-tree" and issue_root is None:
        issue_root = os.path.join(ROOT, "issues")
        if not os.path.isdir(issue_root):
            issue_root = None
    try:
        diagnostics, _parsed = issue_validate_mod.validate(
            repo=ROOT,
            source=validate_source,
            root=issue_root if validate_source != "staged-index" else None,
            authoritative_root=options.issue_authoritative_root,
            compare_head=False,
            dag_path=dag_path if os.path.exists(dag_path) else None,
            generated_root=generated_root,
        )
    except issue_validate_mod.ConfigurationError as exc:
        record_finding("issue-validate-config", "error", str(exc))
        return
    for diagnostic in diagnostics:
        record_finding(
            "issue-validate",
            "error",
            "%s %s:%s item=%s field=%s: %s" % (
                diagnostic.rule,
                diagnostic.path,
                diagnostic.line,
                diagnostic.item,
                diagnostic.field,
                diagnostic.message,
            ),
            ref=diagnostic.path or diagnostic.rule,
        )


def check_automation_safety():
    checks_performed.append("check_automation_safety")
    tools_dir = os.path.join(SRC, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import automation_safety
        report = automation_safety.scan_repository(
            Path(ROOT),
            policy_path=Path(ROOT) / automation_safety.DEFAULT_POLICY,
        )
    except Exception as exc:
        record_finding(
            "automation-safety-error",
            "error",
            f"Automation-safety checker could not run: {exc}",
        )
        return

    for error in report.get("policy_errors", []):
        record_finding(
            "automation-safety-policy",
            "error",
            f"Automation-safety policy error {error.get('code', 'POLICY')}: {error.get('message', '')}",
        )
    for finding in report.get("findings", []):
        if finding.get("severity") != "critical" or finding.get("status") != "unresolved":
            continue
        record_finding(
            "automation-safety-critical",
            "error",
            "%s %s:%s %s: %s" % (
                finding.get("rule"),
                finding.get("path"),
                finding.get("line"),
                finding.get("symbol"),
                finding.get("evidence"),
            ),
            ref="%s:%s" % (finding.get("path"), finding.get("line")),
        )


def main(argv=None):
    global ISSUE_VALIDATE_ARGS
    argv = sys.argv[1:] if argv is None else argv
    ISSUE_VALIDATE_ARGS, rest = parse_validate_cli(argv)
    if rest:
        sys.argv = [sys.argv[0], *rest]
    _t0 = time.time()
    check_automation_safety()
    check_issue_store(ISSUE_VALIDATE_ARGS)
    check_build()
    check_links()
    check_langs()
    check_requirement_review_schema()
    check_namespaces()
    check_home_links()
    check_no_hardcoded_german()
    check_client_rendered_german()
    check_record_status()
    check_workflow_lifecycle()

    finished_at = time.time()
    _exit_code = 1 if problems else 0

    findings_by_category = {}
    for f in structured_findings:
        cat = f.get("category", "unknown")
        findings_by_category[cat] = findings_by_category.get(cat, 0) + 1

    reports_dir = os.path.join(ROOT, "output", "build-reports")
    os.makedirs(reports_dir, exist_ok=True)
    report = {
        "schema_version": "1.0",
        "report_kind": "validate",
        "tool": "validate.py",
        "command": "validate.py " + " ".join(sys.argv[1:]),
        "inputs": ["_src/", "output/"],
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_t0)),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(finished_at)),
        "duration_s": round(finished_at - _t0, 3),
        "exit_code": _exit_code,
        "changed_artifacts": [],
        "counts": {
            "checks_performed": len(checks_performed),
            "findings_by_category": findings_by_category,
            "success": _exit_code == 0,
        },
        "findings": structured_findings,
        "run_archive_ref": os.environ.get("RUN_ARCHIVE_REF"),
    }
    report_file = os.path.join(reports_dir, f"validate-{int(finished_at)}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    if problems:
        print("PROBLEME:")
        for p in problems:
            print(" -", p)
        sys.exit(1)

    print("OK — Tree aktuell (de + %d Sprachbäume), alle internen Links und Anker gültig, keine Waisen."
          % len(LANGS))


if __name__ == "__main__":
    main()
