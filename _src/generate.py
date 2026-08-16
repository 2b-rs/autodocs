#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — Erzeugt den kompletten HTML-Tree aus den Quellen unter _src/.

    python3 _src/generate.py            # schreibt alle deutschen Seiten nach ../
    python3 _src/generate.py --check    # schreibt nichts, vergleicht nur (DOM)
    python3 _src/generate.py classes/cl_ara_core_Future_420ba8.html   # einzelne Seite(n)
    python3 _src/generate.py --lang=en  # zusätzlich Sprachbaum ../en/ erzeugen
    python3 _src/generate.py --lang=alle   # alle Sprachbäume (en es fr ru ar hi ko zh)

Sprachbäume (Details in lib_i18n.py): Deutsch ist kanonisch; Übersetzungen
kommen aus _src/i18n/. Segmente ohne Übersetzung bleiben deutsch (Fallback,
wird gezählt und gemeldet).

Quellen: _src/sources/pages/**.json  (Seitenmodelle / Komposition)
         _src/spec/records/**.json   (Spezifikations-DB, via rec-ref referenziert)
         _src/content/ai/**          (KI-Fragmente, referenziert aus den Modellen)
         _src/diagrams/**            (SVG-Diagramme, referenziert aus den Modellen)
         _src/templates/             (Seiten-Chrome, Footer-Varianten)
         _src/site.json              (Projektmanifest: Bereiche, Sprachen)
Danach:  python3 _src/validate.py    (Prüfungen, siehe WARTUNG.md)
"""
import json
import multiprocessing
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import (SRC, ROOT, LANGS, render_page, load_templates,
                          compare_html, iter_pages)

WORKERS = min(12, os.cpu_count() or 12)
# 'fork' avoids re-importing lxml/lib_docmodel per worker (macOS defaults to
# 'spawn', which pays that import cost on every one of the 12 workers and
# dominates wall-clock time for a fast, many-small-tasks workload like this).
_MP_CTX = multiprocessing.get_context("fork")


def _render_one(args):
    page, footers, page_tmpl, check = args
    html_text = render_page(page, footers, page_tmpl)
    target = os.path.join(ROOT, page["file"])
    if check:
        errs = compare_html(target, html_text) if os.path.exists(target) else ["Datei fehlt"]
        return page["file"], None, errs
    return page["file"], html_text, None


def generate_lang(lang, only=None, check=False, announce=True):
    """Einen Sprachbaum ../<lang>/ erzeugen (oder mit check=True nur byte-genau
    vergleichen). Liefert (Seitenzahl, Statistik, Liste abweichender Dateien)."""
    from lib_i18n import lade_register, lade_soll, uebersetze_seite, globale_ersetzungen, Statistik
    seg, _lab, ui = lade_register(lang)
    page_tmpl, footers = load_templates()
    footers = dict(footers, **ui.get("footers", {}))
    stat = Statistik(soll=lade_soll())
    n, stale = 0, []
    for page in iter_pages(only):
        if page.get("nolang"):
            continue          # nur-deutsche Seite (z. B. Traceability-Bericht)
        uebers = uebersetze_seite(page, lang, seg, ui, stat)
        html_text = render_page(uebers, footers, page_tmpl, lang=lang, notice_ui=ui.get("review_notice"))
        html_text = globale_ersetzungen(html_text, ui)
        target = os.path.join(ROOT, lang, page["file"])
        if check:
            cur = open(target, encoding="utf-8").read() if os.path.exists(target) else None
            if cur != html_text:
                stale.append("%s/%s" % (lang, page["file"]))
        else:
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(html_text)
        n += 1
    if not check and announce:
        print("generiert [%s]: %d Seiten, Treffer %d, fehlende Übersetzungen (Fallback deutsch): %d eindeutige Segmente"
              % (lang, n, stat.treffer, len(stat.fehlend)))
    return n, stat, stale


def _generate_lang_one(args):
    lang, only, check = args
    n, stat, stale = generate_lang(lang, only, check, announce=False)
    return lang, n, stat.treffer, len(stat.fehlend), stale


def generate_languages(langs, only=None, check=False):
    """Generate independent language trees concurrently and return results in
    input order. Duplicate languages are collapsed to prevent concurrent writes
    to the same output tree."""
    ordered_langs = list(dict.fromkeys(langs))
    unsupported = [lang for lang in ordered_langs if lang not in LANGS]
    if unsupported:
        raise ValueError("unsupported language(s): %s" % ", ".join(unsupported))
    tasks = [(lang, only, check) for lang in ordered_langs]
    if len(tasks) < 2 or WORKERS < 2:
        results = [_generate_lang_one(task) for task in tasks]
    else:
        with ProcessPoolExecutor(
            max_workers=min(WORKERS, len(tasks)), mp_context=_MP_CTX
        ) as ex:
            results = list(ex.map(_generate_lang_one, tasks, chunksize=1))
    if not check:
        for lang, n, hits, missing, _stale in results:
            print("generiert [%s]: %d Seiten, Treffer %d, fehlende Übersetzungen (Fallback deutsch): %d eindeutige Segmente"
                  % (lang, n, hits, missing))
    return results


def main():
    _t0 = time.time()
    args = [a for a in sys.argv[1:]]
    check = "--check" in args
    langs = []
    for a in args:
        if a.startswith("--lang="):
            w = a.split("=", 1)[1]
            langs = list(LANGS) if w in ("alle", "all") else w.split(",")
    only = set(a for a in args if not a.startswith("--")) or None

    page_tmpl, footers = load_templates()
    pages = list(iter_pages(only))
    n, bad = 0, 0
    tasks = [(page, footers, page_tmpl, check) for page in pages]
    chunksize = max(1, len(tasks) // (WORKERS * 4)) if tasks else 1
    if len(tasks) < WORKERS * 2:
        rendered = [_render_one(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=WORKERS, mp_context=_MP_CTX) as ex:
            rendered = list(ex.map(_render_one, tasks, chunksize=chunksize))
    results = {file: (html_text, errs) for file, html_text, errs in rendered}
    for page in pages:
        html_text, errs = results[page["file"]]
        if check:
            if errs:
                bad += 1
                print("ABWEICHUNG %s" % page["file"])
                for e in errs[:5]:
                    print("   ", e)
        else:
            target = os.path.join(ROOT, page["file"])
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(html_text)
        n += 1
    print(("geprüft" if check else "generiert") + ": %d Seiten" % n + (", Abweichungen: %d" % bad if check else ""))
    _fallback_by_lang, _lang_page_counts, _changed_targets = {}, {}, []
    if not check:
        for lang, _n_lang, _hits, _missing, _stale in generate_languages(langs, only):
            _lang_page_counts[lang] = _n_lang
            _fallback_by_lang[lang] = _missing
    _exit_code = 1 if bad else 0
    if not check:
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "build-reports")
        os.makedirs(reports_dir, exist_ok=True)
        finished_at = time.time()
        report = {
            "schema_version": "1.0", "report_kind": "html_generate", "tool": "generate.py",
            "command": "generate.py " + " ".join(args), "inputs": langs or ["de"],
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_t0)),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(finished_at)),
            "duration_s": round(finished_at - _t0, 3), "exit_code": _exit_code,
            "changed_artifacts": _changed_targets,
            "counts": {"pages_generated_per_lang": {"de": n, **_lang_page_counts},
                       "fallback_to_german": _fallback_by_lang, "changed_targets": len(_changed_targets)},
            "findings": [],
            "run_archive_ref": os.environ.get("RUN_ARCHIVE_REF"),
        }
        fn = os.path.join(reports_dir, "html_generate-%d.json" % int(finished_at))
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
    sys.exit(_exit_code)


if __name__ == "__main__":
    main()
