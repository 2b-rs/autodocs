# -*- coding: utf-8 -*-
"""
render_diagrams.py — Rendert alle Diagramme aus ihren Quellen neu.

Quellenlage:
  Graphviz-Diagramme:   .dot-Dateien
  Sequenzdiagramme:     .seq.json-Dateien (Format siehe seqgen.py)

Ablageorte (Quelle liegt immer neben dem Ziel):
  Datei-Diagramme:   _src/diagrams/<seite>/svg_NN.dot|.seq.json
                     -> _src/diagrams/<seite>/svg_NN.svg
  Inline-Diagramme:  _src/content/ai/<seite>/<fragment>.<diag-id>.dot|.seq.json
                     -> ersetzt das <svg> im Wrapper <div id="<diag-id>">
                        des Fragments <fragment>.html

Aufruf (aus dem Wurzelverzeichnis des Trees):
  python3 _src/render_diagrams.py                 # alles neu rendern
  python3 _src/render_diagrams.py --pruefe-alt    # zusätzlich prüfen, dass die
                                                  # neuen SVGs informationsgleich
                                                  # zu den bisherigen sind
  python3 _src/render_diagrams.py classes/cl_x    # nur Quellen, deren Pfad das
                                                  # Muster enthält

Danach den Tree neu generieren:  python3 _src/generate.py
"""
import json
import re
import sys
from pathlib import Path

from lxml import html as LH

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(1, str(Path(__file__).resolve().parent / "tools"))
import lib_svgdiag as D
import seqgen

AI = D.SRC / 'content' / 'ai'


def _render_quelle(src):
    """Quelldatei -> SVG-Text in Zielform (Datei-Form bei .dot via flag)."""
    if src.name.endswith('.seq.json'):
        spec = json.loads(src.read_text(encoding='utf-8'))
        return seqgen.render_seq(spec)
    raise ValueError(src)


def _gleich_gv(alt, neu):
    d = D.diff_models(D.parse_graphviz_svg(alt), D.parse_graphviz_svg(neu))
    return not d, d


def _gleich_seq(alt, neu):
    import svg2seq
    a = json.dumps(svg2seq.parse_seq_svg(alt), sort_keys=True, ensure_ascii=False)
    b = json.dumps(svg2seq.parse_seq_svg(neu), sort_keys=True, ensure_ascii=False)
    return a == b, 'Spezifikationen weichen ab'


def datei_jobs():
    """[(quelle, ziel-svg, art)] für Datei-Diagramme."""
    jobs = []
    for src in sorted((D.SRC / 'diagrams').rglob('*.dot')):
        jobs.append((src, src.with_suffix('.svg'), 'gv'))
    for src in sorted((D.SRC / 'diagrams').rglob('*.seq.json')):
        ziel = src.parent / (src.name[:-len('.seq.json')] + '.svg')
        jobs.append((src, ziel, 'seq'))
    return jobs


def inline_jobs():
    """[(quelle, fragment, diag-id, art)] für Inline-Diagramme."""
    jobs = []
    for src in sorted(AI.rglob('*.dot')):
        stem, did = src.name[:-len('.dot')].split('.', 1)
        jobs.append((src, src.parent / (stem + '.html'), did, 'gv'))
    for src in sorted(AI.rglob('*.seq.json')):
        stem, did = src.name[:-len('.seq.json')].split('.', 1)
        jobs.append((src, src.parent / (stem + '.html'), did, 'seq'))
    return jobs


def render_datei(src, art, inline):
    if art == 'gv':
        roh = D.render_dot(src.read_text(encoding='utf-8'))
        return D.postprocess_dot_svg(roh, inline=inline)
    # Sequenzdiagramme haben in Datei- und Inline-Form dieselbe Wurzel
    neu = _render_quelle(src)
    frag = LH.fragment_fromstring(neu)
    return LH.tostring(frag, encoding='unicode')


def main():
    pruefe_alt = '--pruefe-alt' in sys.argv
    muster = [a for a in sys.argv[1:] if not a.startswith('--')]

    def passt(p):
        return not muster or any(m in str(p) for m in muster)

    ok = fail = 0

    # 1. Datei-Diagramme
    for src, ziel, art in datei_jobs():
        if not passt(src):
            continue
        try:
            neu = render_datei(src, art, inline=False)
            if pruefe_alt and ziel.exists():
                alt = ziel.read_text(encoding='utf-8')
                gleich, d = (_gleich_gv if art == 'gv' else _gleich_seq)(alt, neu)
                if not gleich:
                    raise ValueError(f'nicht informationsgleich: {d}')
            ziel.write_text(neu + '\n', encoding='utf-8')
            ok += 1
        except Exception as ex:
            fail += 1
            print(f'PROBLEM {src.relative_to(D.SRC)}: {str(ex)[:300]}')

    # 2. Inline-Diagramme (Fragmente patchen)
    frag_cache = {}
    for src, fragdatei, did, art in inline_jobs():
        if not passt(src):
            continue
        try:
            neu = render_datei(src, art, inline=True)
            if fragdatei not in frag_cache:
                raw = fragdatei.read_text(encoding='utf-8')
                frag_cache[fragdatei] = [LH.fragment_fromstring(raw),
                                         raw.endswith('\n')]
            el = frag_cache[fragdatei][0]
            wrap = None
            for d_ in el.iterdescendants():
                if d_.get('id') == did:
                    wrap = d_
                    break
            if wrap is None:
                raise ValueError(f'Wrapper {did} nicht gefunden')
            alte = [k for k in wrap if D._ln(k) == 'svg']
            if len(alte) != 1:
                raise ValueError(f'{len(alte)} SVGs im Wrapper {did}')
            if pruefe_alt:
                alt = D.svg_of_wrapper(wrap)
                gleich, d = (_gleich_gv if art == 'gv' else _gleich_seq)(alt, neu)
                if not gleich:
                    raise ValueError(f'nicht informationsgleich: {d}')
            neu_el = LH.fragment_fromstring(neu)
            neu_el.tail = alte[0].tail
            wrap.replace(alte[0], neu_el)
            ok += 1
        except Exception as ex:
            fail += 1
            print(f'PROBLEM {src.relative_to(D.SRC)}: {str(ex)[:300]}')

    for fragdatei, (el, nl) in frag_cache.items():
        out = LH.tostring(el, encoding='unicode')
        if nl and not out.endswith('\n'):
            out += '\n'
        fragdatei.write_text(out, encoding='utf-8')

    print(f'OK {ok}, Probleme {fail}'
          + (f' — {len(frag_cache)} Fragmente aktualisiert' if frag_cache else ''))
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
