#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n_diagrams.py — Übersetzte Diagramme materialisieren.

Für jede Sprache und jede Diagrammquelle wird die Quelle über das
Label-Register (_src/i18n/<lang>/labels.json) übersetzt. Weicht die
übersetzte Quelle vom Original ab, wird sie neu gerendert und abgelegt:

  Datei-Diagramme:   _src/diagrams/<seite>/svg_NN.dot|.seq.json
                     -> _src/i18n/<lang>/diagrams/<seite>/svg_NN.svg
  Inline-Diagramme:  _src/content/ai/<pfad>/<fragment>.<diag-id>.dot|.seq.json
                     -> _src/i18n/<lang>/inline/<pfad>/<fragment>.<diag-id>.svg

generate.py --lang setzt diese SVGs automatisch ein; fehlt eine Datei,
bleibt das deutsche Diagramm stehen (Fallback).

Aufruf (aus dem Wurzelverzeichnis des Trees):
  python3 _src/i18n_diagrams.py            # alle Sprachen
  python3 _src/i18n_diagrams.py en zh      # nur bestimmte Sprachen
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_svgdiag as D
import seqgen
from lxml import html as LH
from lib_i18n import I18N, LANGS, uebersetze_dot, uebersetze_seq

AI = D.SRC / 'content' / 'ai'
DIAG = D.SRC / 'diagrams'
REPORTS_DIR = D.SRC.parent / "output" / "build-reports"


def _write_report(counts, findings, exit_code, started_at, langs):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    finished_at = time.time()
    report = {
        "schema_version": "1.0", "report_kind": "i18n_diagrams", "tool": "i18n_diagrams.py",
        "command": "i18n_diagrams.py " + " ".join(langs), "inputs": langs,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at)),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(finished_at)),
        "duration_s": round(finished_at - started_at, 3), "exit_code": exit_code,
        "changed_artifacts": [], "counts": counts, "findings": findings,
        "run_archive_ref": os.environ.get("RUN_ARCHIVE_REF"),
    }
    fn = REPORTS_DIR / ("i18n_diagrams-%d.json" % int(finished_at))
    fn.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


def render_dot_svg(text, inline):
    return D.postprocess_dot_svg(D.render_dot(text), inline=inline)


def render_seq_svg(spec):
    frag = LH.fragment_fromstring(seqgen.render_seq(spec))
    return LH.tostring(frag, encoding='unicode')


def main():
    _t0 = time.time()
    langs = [a for a in sys.argv[1:] if not a.startswith('--')] or LANGS
    _totals = {"sources_considered": 0, "translated_written": 0, "unchanged_skipped": 0, "stale_deleted": 0}
    _findings = []
    for lang in langs:
        lab_pfad = Path(I18N) / lang / 'labels.json'
        if not lab_pfad.exists():
            print('%s: kein labels.json — übersprungen' % lang)
            _findings.append({"category": "no-labels-register", "severity": "warning",
                               "message": "%s: kein labels.json" % lang})
            continue
        lab = json.loads(lab_pfad.read_text(encoding='utf-8'))
        n = ok = fail = 0
        jobs = []
        for src in sorted(DIAG.rglob('*.dot')):
            jobs.append((src, Path(I18N) / lang / 'diagrams'
                         / src.relative_to(DIAG).with_suffix('.svg'), 'dot', False))
        for src in sorted(DIAG.rglob('*.seq.json')):
            rel = src.relative_to(DIAG)
            ziel = Path(I18N) / lang / 'diagrams' / rel.parent / (rel.name[:-len('.seq.json')] + '.svg')
            jobs.append((src, ziel, 'seq', False))
        for src in sorted(AI.rglob('*.dot')):
            jobs.append((src, Path(I18N) / lang / 'inline'
                         / src.relative_to(AI).with_suffix('.svg'), 'dot', True))
        for src in sorted(AI.rglob('*.seq.json')):
            rel = src.relative_to(AI)
            ziel = Path(I18N) / lang / 'inline' / rel.parent / (rel.name[:-len('.seq.json')] + '.svg')
            jobs.append((src, ziel, 'seq', True))

        for src, ziel, art, inline in jobs:
            raw = src.read_text(encoding='utf-8')
            try:
                if art == 'dot':
                    neu = uebersetze_dot(raw, lab)
                    if neu == raw:
                        # keine Übersetzung (mehr) nötig — veraltete Zieldatei entfernen,
                        # damit generate.py auf das Originaldiagramm zurückfällt
                        if ziel.exists():
                            _totals["stale_deleted"] += 1
                        else:
                            _totals["unchanged_skipped"] += 1
                        ziel.unlink(missing_ok=True)
                        continue
                    svg = render_dot_svg(neu, inline=inline)
                else:
                    spec = json.loads(raw)
                    neu = uebersetze_seq(spec, lab)
                    if neu == spec:
                        if ziel.exists():
                            _totals["stale_deleted"] += 1
                        else:
                            _totals["unchanged_skipped"] += 1
                        ziel.unlink(missing_ok=True)
                        continue
                    svg = render_seq_svg(neu)
                ziel.parent.mkdir(parents=True, exist_ok=True)
                ziel.write_text(svg + '\n', encoding='utf-8')
                ok += 1
                _totals["translated_written"] += 1
            except Exception as ex:
                fail += 1
                print('PROBLEM %s [%s]: %s' % (src.relative_to(D.SRC), lang, str(ex)[:200]))
                _findings.append({"category": "render-failure", "severity": "error",
                                   "message": "%s [%s]: %s" % (src.relative_to(D.SRC), lang, str(ex)[:200])})
            n += 1
            _totals["sources_considered"] += 1
        print('%s: %d übersetzte Diagramme gerendert, %d Probleme' % (lang, ok, fail))
    _exit_code = 1 if any(f["severity"] == "error" for f in _findings) else 0
    _write_report(_totals, _findings, _exit_code, _t0, langs)
    sys.exit(_exit_code)


if __name__ == '__main__':
    main()
