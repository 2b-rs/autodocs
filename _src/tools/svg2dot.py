# -*- coding: utf-8 -*-
"""
svg2dot.py — Einmalige Rückgewinnung der Diagrammquellen aus den SVGs.

Schritt 1 (--ids):  Vergibt fehlende id-Attribute an Inline-Diagramm-Wrapper
                    in den KI-Fragmenten (div.diagram / div.umlwrap), damit
                    jede Quelle einen stabilen Dateinamen bekommt.
Schritt 2 (Standard): Erzeugt für jedes Graphviz-Diagramm eine .dot-Quelle
                    und prüft per Roundtrip (dot -Tsvg + Nachbearbeitung),
                    dass das neu gerenderte SVG informationsäquivalent ist.

Quellablage:
  Datei-Diagramme:  _src/diagrams/<seite>/svg_NN.dot   (neben dem SVG)
  Inline-Diagramme: _src/content/ai/<seite>/<fragment>.<id>.dot

Sequenzdiagramme (nicht Graphviz) behandelt svg2seq.py.
"""
import csv
import sys
from pathlib import Path

from lxml import html as LH

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lib_svgdiag as D


def assign_ids():
    """Fehlende ids an Inline-Diagramm-Wrapper vergeben (je Seite eindeutig)."""
    changed = 0
    per_page_ids = {}
    for f, el, wraps in D.iter_inline_diagrams():
        page = f.parent.name
        ids = per_page_ids.setdefault(page, set())
        for d in wraps:
            if d.get('id'):
                ids.add(d.get('id'))
    for f, el, wraps in D.iter_inline_diagrams():
        page = f.parent.name
        ids = per_page_ids[page]
        raw = f.read_text(encoding='utf-8')
        dirty = False
        n = 0
        prefix = 'diag'
        if f.name.startswith('rec_'):
            prefix = 'diag-' + f.stem[4:].lower().replace('_', '-')
            prefix = prefix.rsplit('-', 1)[0]  # laufende Fragmentnummer weg
        for d in wraps:
            n += 1
            if d.get('id'):
                continue
            k = 1
            while f'{prefix}-{k:02d}' in ids:
                k += 1
            new_id = f'{prefix}-{k:02d}'
            d.set('id', new_id)
            ids.add(new_id)
            dirty = True
            changed += 1
        if dirty:
            out = LH.tostring(el, encoding='unicode')
            if raw.endswith('\n') and not out.endswith('\n'):
                out += '\n'
            f.write_text(out, encoding='utf-8')
    print(f'{changed} ids vergeben')


def dot_source_path(kind, svg_path=None, frag_path=None, diag_id=None):
    if kind == 'file':
        return svg_path.with_suffix('.dot')
    return frag_path.parent / f'{frag_path.stem}.{diag_id}.dot'


def reconstruct():
    rows = []
    ok = fail = skipped = 0
    # 1) Datei-Diagramme
    jobs = []
    for f in D.iter_file_diagrams():
        text = f.read_text(encoding='utf-8')
        if not D.is_graphviz(text):
            continue
        jobs.append(('file', str(f.relative_to(D.SRC)), text,
                     dot_source_path('file', svg_path=f)))
    # 2) Inline-Diagramme
    for f, el, wraps in D.iter_inline_diagrams():
        for d in wraps:
            text = D.svg_of_wrapper(d)
            if not D.is_graphviz(text):
                continue
            did = d.get('id')
            assert did, f'Wrapper ohne id in {f}'
            jobs.append(('inline', f'{f.relative_to(D.SRC)}#{did}', text,
                         dot_source_path('inline', frag_path=f, diag_id=did)))

    for kind, ref, text, dst in jobs:
        try:
            m1 = D.parse_graphviz_svg(text)
            dot = D.model_to_dot(m1)
            new = D.render_dot(dot)
            m2 = D.parse_graphviz_svg(new)
            diffs = D.diff_models(m1, m2)
        except Exception as ex:
            fail += 1
            rows.append([kind, ref, 'FEHLER', repr(ex)[:200]])
            continue
        if diffs:
            fail += 1
            rows.append([kind, ref, 'ABWEICHUNG', ' | '.join(diffs[:8])[:500]])
        else:
            ok += 1
            dst.write_text(dot, encoding='utf-8')
            rows.append([kind, ref, 'OK', ''])
    with open('/tmp/svg2dot_report.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['ort', 'diagramm', 'status', 'details'])
        w.writerows(rows)
    print(f'OK {ok}, Probleme {fail} (Report: /tmp/svg2dot_report.csv)')
    for r in rows:
        if r[2] != 'OK':
            print(' ', r[1], '->', r[2], r[3][:220])


if __name__ == '__main__':
    if '--ids' in sys.argv:
        assign_ids()
    else:
        reconstruct()
