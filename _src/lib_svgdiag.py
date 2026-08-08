# -*- coding: utf-8 -*-
"""
lib_svgdiag.py — Bibliothek zur Diagramm-Pipeline.

Zwei Diagrammtypen im Tree:
  1. Graphviz-Diagramme (UML-Klassen-/Ablauf-/Zustandsdiagramme):
     Quelle = .dot-Datei, gerendert mit `dot -Tsvg` + Hausstil-Nachbearbeitung.
  2. Sequenzdiagramme: Quelle = .seq.json, gerendert mit seqgen.py.

Diese Bibliothek enthält:
  - parse_graphviz_svg(): SVG -> Strukturmodell (Knoten, Kanten, Cluster, Reihenfolge)
  - model_to_dot():       Strukturmodell -> .dot-Quelltext (Hausstil-Header)
  - postprocess_dot_svg(): dot-Ausgabe -> Hausstil-SVG (Kommentare/Maße/Stil)
  - diff_models():        Informations-Äquivalenzprüfung zweier Modelle
  - Hilfen zum Auffinden von Datei- und Inline-Diagrammen
"""
import io
import json
import math
import re
import subprocess
from pathlib import Path

from lxml import etree
from lxml import html as LH

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent

# Hausstil-Konstanten (siehe KONVENTIONEN.md)
C_BG = "#f9f8f5"
C_TEXT = "#28251d"
C_ACCENT = "#01696f"
C_MUTED = "#7a7974"
C_FRAME = "#d4d1ca"
FONT = "Helvetica,sans-Serif"


def _ln(el):
    """Lokaler Tag-Name ohne Namespace, kleingeschrieben."""
    if not isinstance(el.tag, str):
        return None
    return el.tag.split('}')[-1].lower()


def _attr(el, *names):
    for n in names:
        for k, v in el.attrib.items():
            if k.split('}')[-1].lower() == n.lower():
                return v
    return None


def parse_svg_root(text):
    """SVG-Text (XML oder HTML-serialisiert) -> lxml-Element."""
    t = text.strip()
    try:
        return etree.fromstring(t.encode('utf-8'))
    except etree.XMLSyntaxError:
        frag = LH.fragment_fromstring(t)
        return frag


def _texts_of(g, exclude_titles=True):
    out = []
    for el in g.iter():
        if _ln(el) == 'text':
            out.append(el)
    return out


def _node_title(g):
    for el in g:
        if _ln(el) == 'title':
            return el.text or ''
    return ''


def _classes(el):
    return (el.get('class') or '').split()


def _find_a(g):
    for el in g.iter():
        if _ln(el) == 'a':
            return el
    return None


def _shape_glyphs(g):
    """Zeichenprimitive direkt unterhalb (ohne Texte/Titel), rekursiv durch <a>/<g>."""
    out = []
    for el in g.iter():
        t = _ln(el)
        if t in ('polygon', 'path', 'ellipse', 'polyline'):
            out.append(el)
    return out


def _bbox_of_points(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _parse_points(s):
    pts = []
    for tok in (s or '').replace(',', ' ').split():
        pts.append(float(tok))
    return list(zip(pts[0::2], pts[1::2]))


def _glyph_bbox(el):
    t = _ln(el)
    if t in ('polygon', 'polyline'):
        return _bbox_of_points(_parse_points(el.get('points')))
    if t == 'ellipse':
        cx, cy = float(el.get('cx')), float(el.get('cy'))
        rx, ry = float(el.get('rx')), float(el.get('ry'))
        return cx - rx, cy - ry, cx + rx, cy + ry
    if t == 'path':
        nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', el.get('d', ''))]
        xs, ys = nums[0::2], nums[1::2]
        if not xs:
            return 0, 0, 0, 0
        return min(xs), min(ys), max(xs), max(ys)
    return 0, 0, 0, 0


def _is_degenerate(el):
    """Trennlinien in UML-Boxen: entartete Polygone (Höhe 0)."""
    if _ln(el) != 'polygon':
        return False
    x0, y0, x1, y1 = _glyph_bbox(el)
    return abs(y1 - y0) < 0.01 or abs(x1 - x0) < 0.01


def _text_info(t):
    return {
        'text': t.text or '',
        'x': float(t.get('x', '0')),
        'y': float(t.get('y', '0')),
        'size': float(t.get('font-size', '12')),
        'bold': (t.get('font-weight') == 'bold'),
        'italic': (t.get('font-style') == 'italic'),
        'anchor': t.get('text-anchor', 'middle'),
        'fill': t.get('fill', C_TEXT),
    }


def _link_info(g):
    a = _find_a(g)
    if a is None:
        return None
    return {
        'href': _attr(a, 'href') or '',
        'title': _attr(a, 'title') or None,
        'target': _attr(a, 'target') or None,
        'class': ' '.join(c for c in _classes(a)) or None,
    }


def _dash(el):
    return bool(el.get('stroke-dasharray'))


def _parse_node(g):
    """g.node -> Knotenmodell."""
    n = {'id': _node_title(g)}
    extra = [c for c in _classes(g) if c != 'node']
    if extra:
        n['class'] = ' '.join(extra)
    link = _link_info(g)
    if link:
        n['link'] = link
    glyphs = _shape_glyphs(g)
    texts = [_text_info(t) for t in _texts_of(g)]
    texts.sort(key=lambda t: t['y'])
    seps = [gl for gl in glyphs if _is_degenerate(gl)]
    real = [gl for gl in glyphs if not _is_degenerate(gl)]
    ells = [gl for gl in real if _ln(gl) == 'ellipse']
    boxes = [gl for gl in real if _ln(gl) in ('polygon', 'path')]

    bb = None
    for gl in real:
        b = _glyph_bbox(gl)
        bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]),
                                   max(bb[2], b[2]), max(bb[3], b[3]))
    if bb is None and texts:
        bb = (min(t['x'] for t in texts), min(t['y'] for t in texts),
              max(t['x'] for t in texts), max(t['y'] for t in texts))
    n['bbox'] = bb

    # UML-Box mit Kompartimenten?
    if seps and boxes:
        n['kind'] = 'uml'
        sep_ys = sorted(set(round(_glyph_bbox(s)[1], 1) for s in seps))
        comps = [[] for _ in range(len(sep_ys) + 1)]
        for t in texts:
            k = sum(1 for sy in sep_ys if t['y'] > sy)
            comps[k].append(t)
        n['compartments'] = [
            [{'text': t['text'], 'bold': t['bold'], 'italic': t['italic'],
              'anchor': t['anchor']} for t in comp]
            for comp in comps
        ]
        frame = [b for b in boxes if (b.get('fill') in (None, 'none'))]
        fillbg = [b for b in boxes if b.get('fill') not in (None, 'none')]
        n['fill'] = fillbg[0].get('fill') if fillbg else C_BG
        n['stroke'] = (frame[0].get('stroke') if frame else C_ACCENT)
        n['sepcolor'] = seps[0].get('fill') or seps[0].get('stroke') or C_ACCENT
        return n

    # Einfache Formen
    n['kind'] = 'simple'
    if len(ells) >= 2 and not boxes:
        n['shape'] = 'doublecircle'
        outer = max(ells, key=lambda e: float(e.get('rx')))
        inner = min(ells, key=lambda e: float(e.get('rx')))
        n['fill'] = inner.get('fill', 'none')
        n['stroke'] = outer.get('stroke', C_TEXT)
        n['width'] = round(2 * float(inner.get('rx')) / 72, 3)
    elif len(ells) == 1 and not boxes:
        e = ells[0]
        rx, ry = float(e.get('rx')), float(e.get('ry'))
        fill = e.get('fill', 'none')
        if rx <= 7 and abs(rx - ry) < 0.01 and fill not in ('none', C_BG, '#ffffff'):
            n['shape'] = 'point'
            n['width'] = round(2 * rx / 72, 3)
        elif abs(rx - ry) < 0.5:
            n['shape'] = 'circle'
        else:
            n['shape'] = 'ellipse'
        n['fill'] = fill
        n['stroke'] = e.get('stroke', C_TEXT)
        n['penwidth'] = e.get('stroke-width')
        n['dashed'] = _dash(e)
    elif boxes:
        gl = boxes[0]
        if _ln(gl) == 'path':
            n['shape'] = 'box'
            n['rounded'] = True
        else:
            pts = _parse_points(gl.get('points'))
            uniq = []
            for p in pts:
                if p not in uniq:
                    uniq.append(p)
            xs = sorted(set(round(p[0], 1) for p in uniq))
            ys = sorted(set(round(p[1], 1) for p in uniq))
            if len(uniq) == 4 and (len(xs) > 2 or len(ys) > 2):
                n['shape'] = 'diamond'
            else:
                n['shape'] = 'box'
        n['fill'] = gl.get('fill', 'none')
        n['stroke'] = gl.get('stroke', C_TEXT)
        n['penwidth'] = gl.get('stroke-width')
        n['dashed'] = _dash(gl)
    else:
        n['shape'] = 'plaintext'

    lines = []
    for t in texts:
        lines.append({'text': t['text'], 'bold': t['bold'],
                      'italic': t['italic'], 'size': t['size']})
    n['lines'] = lines
    if texts:
        n['fontcolor'] = texts[0]['fill']
        n['fontsize'] = texts[0]['size']
    return n


def _parse_edge(g, node_centers):
    e = {}
    t = _node_title(g)
    t = t.replace('&#45;', '-')
    m = re.match(r'(.*?)(->|--|&#45;&gt;)(.*)', t)
    e['tail'], e['head'] = m.group(1), m.group(3)
    extra = [c for c in _classes(g) if c != 'edge']
    if extra:
        e['class'] = ' '.join(extra)
    link = _link_info(g)
    if link:
        e['link'] = link
    paths = [el for el in g.iter() if _ln(el) == 'path']
    polys = [el for el in g.iter() if _ln(el) in ('polygon', 'polyline')]
    texts = [_text_info(x) for x in _texts_of(g)]
    if paths:
        p = paths[0]
        e['color'] = p.get('stroke', C_TEXT)
        e['penwidth'] = p.get('stroke-width')
        e['dashed'] = _dash(p)
        nums = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', p.get('d', ''))]
        e['p0'] = (nums[0], nums[1]) if len(nums) >= 2 else None
        e['p1'] = (nums[-2], nums[-1]) if len(nums) >= 2 else None
    heads = []
    for poly in polys:
        fill = poly.get('fill', 'none')
        heads.append('normal' if fill not in ('none', C_BG, '#ffffff') else 'empty')
    if not heads:
        e['arrowhead'] = 'none'
    elif len(heads) == 1:
        e['arrowhead'] = heads[0]
    else:
        # Beide Enden mit Spitze: Zuordnung über Nähe zu Kopf-/Fußknoten
        e['arrowhead'] = heads[0]
        e['arrowtail'] = heads[1]
        e['dir'] = 'both'
        hc = node_centers.get(e['head'])
        tc = node_centers.get(e['tail'])
        if hc and tc and len(polys) == 2:
            b0 = _glyph_bbox(polys[0])
            c0 = ((b0[0] + b0[2]) / 2, (b0[1] + b0[3]) / 2)
            dh = math.dist(c0, hc)
            dt = math.dist(c0, tc)
            if dt < dh:
                e['arrowhead'], e['arrowtail'] = heads[1], heads[0]
    if texts:
        e['label'] = [t_['text'] for t_ in texts]
        e['fontsize'] = texts[0]['size']
        e['fontcolor'] = texts[0]['fill']
        e['labelitalic'] = texts[0]['italic']
    return e


def parse_graphviz_svg(text):
    """Graphviz-SVG -> Strukturmodell (dict)."""
    root = parse_svg_root(text)
    svg = root if _ln(root) == 'svg' else root.find('.//svg')
    g0 = None
    for el in svg.iter():
        if _ln(el) == 'g' and 'graph' in _classes(el):
            g0 = el
            break
    model = {'nodes': {}, 'edges': [], 'clusters': [], 'order': [],
             'graph': {}}

    # Reihenfolge der Original-Statements aus den Graphviz-Kommentaren
    for el in g0.iter():
        if isinstance(el.tag, str):
            continue
        if not isinstance(el, etree._Comment):
            continue
        c = (el.text or '').strip()
        if not c or c.startswith('Generated') or c.startswith('Title:') \
           or c.startswith('Pages:'):
            continue
        c = c.replace('&#45;', '-').replace('&gt;', '>')
        if '->' in c:
            a, b = c.split('->', 1)
            model['order'].append(('edge', a.strip(), b.strip()))
        else:
            model['order'].append(('node', c.strip()))

    # Graph-Label: Texte direkt unter g0 (nicht in node/edge/cluster)
    direct_texts = []
    for el in g0:
        if _ln(el) == 'text':
            direct_texts.append(_text_info(el))
    if direct_texts:
        model['graph']['label'] = [t['text'] for t in direct_texts]
        model['graph']['fontsize'] = direct_texts[0]['size']
        model['graph']['fontcolor'] = direct_texts[0]['fill']
        model['graph']['bold'] = direct_texts[0]['bold']
        tr = g0.get('transform', '')
        mm = re.search(r'translate\([\d.\- ]+ ([\d.\-]+)\)', tr)
        h = float(mm.group(1)) if mm else 0
        model['graph']['labelloc'] = 't' if abs(direct_texts[0]['y']) > h * 0.55 else 'b'

    groups = {'node': [], 'edge': [], 'cluster': []}
    for el in g0.iter():
        if _ln(el) == 'g':
            cs = _classes(el)
            for k in groups:
                if k in cs:
                    groups[k].append(el)

    for g in groups['cluster']:
        cl = {'id': _node_title(g)}
        glyphs = [x for x in _shape_glyphs(g)]
        texts = [_text_info(t) for t in _texts_of(g)]
        if glyphs:
            gl = glyphs[0]
            cl['rounded'] = (_ln(gl) == 'path')
            cl['fill'] = gl.get('fill', 'none')
            cl['stroke'] = gl.get('stroke', C_FRAME)
            cl['dashed'] = _dash(gl)
            cl['bbox'] = _glyph_bbox(gl)
        if texts:
            cl['label'] = [t['text'] for t in texts]
            cl['fontsize'] = texts[0]['size']
            cl['fontcolor'] = texts[0]['fill']
            # Label oben oder unten im Cluster?
            b = cl.get('bbox')
            if b:
                cl['labelloc'] = 't' if abs(texts[0]['y'] - b[1]) < abs(texts[0]['y'] - b[3]) else 'b'
        model['clusters'].append(cl)

    centers = {}
    for g in groups['node']:
        n = _parse_node(g)
        model['nodes'][n['id']] = n
        if n.get('bbox'):
            b = n['bbox']
            centers[n['id']] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

    for g in groups['edge']:
        model['edges'].append(_parse_edge(g, centers))

    # Clusterzugehörigkeit geometrisch
    for cid, cl in enumerate(model['clusters']):
        b = cl.get('bbox')
        if not b:
            continue
        cl['members'] = []
        for nid, c in centers.items():
            inside = (b[0] <= c[0] <= b[2] and b[1] <= c[1] <= b[3])
            if inside:
                smaller = False
                for c2 in model['clusters']:
                    if c2 is cl or not c2.get('bbox'):
                        continue
                    b2 = c2['bbox']
                    if (b2[0] >= b[0] and b2[1] >= b[1] and b2[2] <= b[2]
                            and b2[3] <= b[3]
                            and b2[0] <= c[0] <= b2[2] and b2[1] <= c[1] <= b2[3]):
                        smaller = True
                        break
                if not smaller:
                    cl['members'].append(nid)

    # rankdir: Mehrheitsvotum über die Einzelkanten (SVG-y wächst nach unten).
    # Breite Diagramme ohne dominante Kantenrichtung sind TB/BT: unverbundene
    # Komponenten packt dot ohnehin horizontal.
    votes = {'LR': 0, 'RL': 0, 'TB': 0, 'BT': 0}
    for e in model['edges']:
        tc, hc = centers.get(e['tail']), centers.get(e['head'])
        if not (tc and hc):
            continue
        dx, dy = hc[0] - tc[0], hc[1] - tc[1]
        if abs(dx) > abs(dy):
            votes['LR' if dx >= 0 else 'RL'] += 1
        elif abs(dy) > 0:
            votes['TB' if dy >= 0 else 'BT'] += 1
    if any(votes.values()):
        model['graph']['rankdir'] = max(votes, key=votes.get)
    else:
        model['graph']['rankdir'] = 'TB'
    return model


# ---------------------------------------------------------------- dot-Ausgabe

def _esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def _num(x):
    """Zahl kompakt formatieren (12.0 -> 12)."""
    f = float(x)
    return str(int(f)) if f == int(f) else str(f)


def _merge_classes(item):
    """Klassen aus g-Element und <a>-Wrapper zusammenführen."""
    parts = []
    for src in (item.get('class'), (item.get('link') or {}).get('class')):
        for c in (src or '').split():
            if c not in parts:
                parts.append(c)
    return ' '.join(parts)


def _hesc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _label_from_lines(lines):
    """Mehrzeilige dot-Labelzeichenkette: Zeilen einzeln maskieren,
    dann mit der dot-Umbruchsequenz \\n verbinden."""
    return '\\n'.join(_esc(l['text']) for l in lines)


def _uml_html_label(n):
    rows = []
    for i, comp in enumerate(n['compartments']):
        if i > 0:
            rows.append('<HR/>')
        if not comp:
            comp = [{'text': ' ', 'bold': False, 'italic': False,
                     'anchor': 'start'}]
        cells = []
        for t in comp:
            txt = _hesc(t['text']) or ' '
            if t['italic']:
                txt = f'<I>{txt}</I>'
            if t['bold']:
                txt = f'<B>{txt}</B>'
            cells.append((txt, t['anchor']))
        if len(cells) == 1 and cells[0][1] != 'start':
            rows.append(f'<TR><TD>{cells[0][0]}</TD></TR>')
        else:
            inner = ''.join(f'{c}<BR ALIGN="LEFT"/>' for c, _ in cells)
            rows.append(f'<TR><TD ALIGN="LEFT" BALIGN="LEFT">{inner}</TD></TR>')
    body = ''.join(rows)
    return (f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" '
            f'BGCOLOR="{n.get("fill", C_BG)}" COLOR="{n.get("stroke", C_ACCENT)}">'
            f'{body}</TABLE>>')


def _node_stmt(n):
    a = {}
    if n['kind'] == 'uml':
        a['shape'] = 'plain'
        a['label'] = _uml_html_label(n)
    else:
        shape = n.get('shape', 'box')
        a['shape'] = shape
        if shape != 'point':
            a['label'] = '"%s"' % _label_from_lines(n.get('lines', []))
        styles = []
        if n.get('rounded'):
            styles.append('rounded')
        if n.get('dashed'):
            styles.append('dashed')
        if n.get('fill') not in (None, 'none'):
            styles.append('filled')
            a['fillcolor'] = '"%s"' % n['fill']
        if styles:
            a['style'] = '"%s"' % ','.join(styles)
        if n.get('stroke'):
            a['color'] = '"%s"' % n['stroke']
        if n.get('fontcolor'):
            a['fontcolor'] = '"%s"' % n['fontcolor']
        if n.get('fontsize') and n['fontsize'] != 12:
            a['fontsize'] = _num(n['fontsize'])
        if n.get('penwidth'):
            a['penwidth'] = n['penwidth']
        if shape in ('point', 'doublecircle') and n.get('width'):
            a['width'] = str(n['width'])
        if n.get('lines') and any(l['bold'] for l in n['lines']):
            a['fontname'] = '"Helvetica-Bold"'
    if n.get('link'):
        l = n['link']
        if l.get('href'):
            a['URL'] = '"%s"' % _esc(l['href'])
        if l.get('title'):
            a['tooltip'] = '"%s"' % _esc(l['title'])
        if l.get('target'):
            a['target'] = '"%s"' % l['target']
    cls = _merge_classes(n)
    if cls:
        a['class'] = '"%s"' % cls
    attrs = ', '.join(f'{k}={v}' for k, v in a.items())
    return f'"{_esc(n["id"])}" [{attrs}]'


def _edge_stmt(e):
    a = {}
    if e.get('label'):
        if e.get('labelitalic'):
            a['fontname'] = '"Helvetica-Oblique"'
        a['label'] = '"%s"' % '\\n'.join(_esc(x) for x in e['label'])
    if e.get('fontsize') and e['fontsize'] != 11:
        a['fontsize'] = _num(e['fontsize'])
    if e.get('fontcolor') and e['fontcolor'] != C_TEXT:
        a['fontcolor'] = '"%s"' % e['fontcolor']
    if e.get('color') and e['color'] != C_TEXT:
        a['color'] = '"%s"' % e['color']
    if e.get('dashed'):
        a['style'] = 'dashed'
    if e.get('penwidth'):
        a['penwidth'] = e['penwidth']
    if e.get('arrowhead', 'normal') != 'normal':
        a['arrowhead'] = e['arrowhead']
    if e.get('dir'):
        a['dir'] = e['dir']
        if e.get('arrowtail'):
            a['arrowtail'] = e['arrowtail']
    if e.get('link'):
        l = e['link']
        if l.get('href'):
            a['URL'] = '"%s"' % _esc(l['href'])
        if l.get('title'):
            a['tooltip'] = '"%s"' % _esc(l['title'])
        if l.get('target'):
            a['target'] = '"%s"' % l['target']
    cls = _merge_classes(e)
    if cls:
        a['class'] = '"%s"' % cls
    s = f'"{_esc(e["tail"])}" -> "{_esc(e["head"])}"'
    if a:
        s += ' [' + ', '.join(f'{k}={v}' for k, v in a.items()) + ']'
    return s


def model_to_dot(model, name='G'):
    g = model['graph']
    out = []
    out.append(f'digraph {name} {{')
    ga = [f'rankdir={g.get("rankdir", "TB")}',
          f'bgcolor="transparent"',
          f'fontname="{FONT}"']
    if g.get('label'):
        lines = g['label'] if isinstance(g['label'], list) else [g['label']]
        ga.append('label="%s"' % '\\n'.join(_esc(x) for x in lines))
        ga.append(f'labelloc={g.get("labelloc", "t")}')
        ga.append(f'fontsize={_num(g.get("fontsize", 13))}')
        ga.append(f'fontcolor="{g.get("fontcolor", C_TEXT)}"')
        if g.get('bold'):
            ga.append('fontname="Helvetica-Bold"')
    out.append('  graph [' + ', '.join(ga) + ']')
    out.append(f'  node [fontname="{FONT}", fontsize=12, color="{C_ACCENT}", '
               f'fontcolor="{C_TEXT}"]')
    out.append(f'  edge [fontname="{FONT}", fontsize=11, color="{C_TEXT}", '
               f'fontcolor="{C_TEXT}", penwidth=1.1]')
    out.append('')

    members = {}
    for cl in model['clusters']:
        for m in cl.get('members', []):
            members[m] = cl['id']

    emitted = set()
    order = list(model['order'])
    for nid in model['nodes']:
        if ('node', nid) not in order:
            order.append(('node', nid))
    edge_models = {}
    for e in model['edges']:
        edge_models.setdefault((e['tail'], e['head']), []).append(e)

    # Clusterblöcke zuerst (Knoten in Originalreihenfolge)
    for cl in model['clusters']:
        cid = cl['id']
        out.append(f'  subgraph "{cid}" {{')
        ca = []
        if cl.get('label'):
            ca.append('label="%s"' % '\\n'.join(_esc(x) for x in cl['label']))
            ca.append(f'fontsize={_num(cl.get("fontsize", 13))}')
            ca.append(f'fontcolor="{cl.get("fontcolor", C_MUTED)}"')
            ca.append(f'labelloc={cl.get("labelloc", "b")}')
        st = []
        if cl.get('rounded'):
            st.append('rounded')
        if cl.get('dashed'):
            st.append('dashed')
        if cl.get('fill') not in (None, 'none'):
            st.append('filled')
            ca.append(f'fillcolor="{cl["fill"]}"')
        if st:
            ca.append('style="%s"' % ','.join(st))
        ca.append(f'color="{cl.get("stroke", C_FRAME)}"')
        for c in ca:
            out.append(f'    graph [{c}]')
        for kind, *rest in order:
            if kind == 'node' and members.get(rest[0]) == cid \
                    and rest[0] not in emitted:
                out.append('    ' + _node_stmt(model['nodes'][rest[0]]))
                emitted.add(rest[0])
        out.append('  }')

    for item in order:
        if item[0] == 'node':
            nid = item[1]
            if nid in emitted or nid not in model['nodes']:
                continue
            out.append('  ' + _node_stmt(model['nodes'][nid]))
            emitted.add(nid)
        else:
            _, a, b = item
            for e in edge_models.get((a, b), []):
                if e.get('_done'):
                    continue
                out.append('  ' + _edge_stmt(e))
                e['_done'] = True
                break
    for e in model['edges']:
        if not e.get('_done'):
            out.append('  ' + _edge_stmt(e))
        e.pop('_done', None)
    out.append('}')
    return '\n'.join(out) + '\n'


# ------------------------------------------------------------- Rendern

def render_dot(dot_text):
    """dot -Tsvg ausführen, Hausstil-Nachbearbeitung, SVG-Text liefern."""
    p = subprocess.run(['dot', '-Tsvg'], input=dot_text.encode('utf-8'),
                       capture_output=True)
    if p.returncode != 0:
        raise RuntimeError('dot fehlgeschlagen: ' + p.stderr.decode()[:400])
    return postprocess_dot_svg(p.stdout.decode('utf-8'))


def postprocess_dot_svg(svg_text, inline=False):
    """Graphviz-Ausgabe in Hausstil-SVG überführen.

    - XML-Prolog/DOCTYPE und "Generated by"-Kommentare entfernen
    - Klassenattribut des Knotens auf das <a> spiegeln (CSS: svg a.vis-*)
    - responsive Stilattribute am Wurzelelement
    """
    svg_text = re.sub(r'<\?xml[^>]*\?>\s*', '', svg_text)
    svg_text = re.sub(r'<!DOCTYPE[^>]*>\s*', '', svg_text)
    svg_text = re.sub(r'<!--\s*Generated by graphviz[^>]*-->\s*', '', svg_text)
    svg_text = re.sub(r'<!--\s*(Title|Pages):[^>]*-->\s*', '', svg_text)
    root = etree.fromstring(svg_text.encode('utf-8'))
    NS = 'http://www.w3.org/2000/svg'
    for g in root.iter('{%s}g' % NS):
        cs = _classes(g)
        vis = [c for c in cs if c.startswith('vis-') or c in ('ext', 'dbox')]
        if vis and ('node' in cs or 'edge' in cs):
            a = g.find('.//{%s}a' % NS)
            if a is not None and not a.get('class'):
                a.set('class', ' '.join(vis))
    if inline:
        vb = root.get('viewBox') or root.get('viewbox') or '0 0 800 100'
        w = float(vb.split()[2])
        root.attrib.pop('width', None)
        root.attrib.pop('height', None)
        root.set('style', 'max-width:%dpx' % round(w * 4 / 3))
    else:
        root.set('style', 'max-width:100%;height:auto')
    out = etree.tostring(root, encoding='unicode')
    # In HTML-Serialisierungsform bringen (wie im Tree gespeichert)
    frag = LH.fragment_fromstring(out)
    return LH.tostring(frag, encoding='unicode')


# ------------------------------------------------------- Äquivalenzprüfung

def _norm_label_lines(x):
    if isinstance(x, list):
        return tuple(s.strip() for s in x if s.strip())
    return (x.strip(),) if x and x.strip() else ()


def model_signature(model):
    """Informationsgehalt eines Diagramms als vergleichbare Struktur."""
    nodes = {}
    for nid, n in model['nodes'].items():
        if n['kind'] == 'uml':
            lbl = tuple(tuple(t['text'].strip() for t in comp if t['text'].strip())
                        for comp in n['compartments'])
        else:
            lbl = tuple(l['text'].strip() for l in n.get('lines', [])
                        if l['text'].strip())
        link = n.get('link') or {}
        nodes[nid] = {
            'label': lbl,
            'href': link.get('href', ''),
            'class': n.get('class') or link.get('class') or '',
            'shape': n.get('shape', 'uml' if n['kind'] == 'uml' else ''),
            'dashed': bool(n.get('dashed')),
            'fill': (n.get('fill') or 'none').lower(),
            'stroke': (n.get('stroke') or '').lower(),
        }
    edges = []
    for e in model['edges']:
        link = e.get('link') or {}
        edges.append({
            'pair': (e['tail'], e['head']),
            'label': tuple(s.strip() for s in e.get('label', []) if s.strip()),
            'dashed': bool(e.get('dashed')),
            'arrowhead': e.get('arrowhead', 'normal'),
            'href': link.get('href', ''),
            'color': (e.get('color') or '').lower(),
        })
    edges.sort(key=lambda x: (x['pair'], x['label']))
    clusters = sorted(
        (tuple(cl.get('label', [])), tuple(sorted(cl.get('members', []))))
        for cl in model['clusters'])
    graph = {
        'label': _norm_label_lines(model['graph'].get('label')),
    }
    return {'nodes': nodes, 'edges': edges, 'clusters': clusters,
            'graph': graph}


def diff_models(m1, m2):
    """Vergleicht zwei Modelle; Liste der Abweichungen (leer = äquivalent)."""
    s1, s2 = model_signature(m1), model_signature(m2)
    diffs = []
    for nid in sorted(set(s1['nodes']) | set(s2['nodes'])):
        a, b = s1['nodes'].get(nid), s2['nodes'].get(nid)
        if a is None or b is None:
            diffs.append(f'Knoten {nid}: nur in {"alt" if b is None else "neu"}')
            continue
        for k in a:
            if a[k] != b[k]:
                diffs.append(f'Knoten {nid}.{k}: {a[k]!r} != {b[k]!r}')
    if len(s1['edges']) != len(s2['edges']):
        diffs.append(f'Kantenzahl: {len(s1["edges"])} != {len(s2["edges"])}')
    for a, b in zip(s1['edges'], s2['edges']):
        for k in a:
            if a[k] != b[k]:
                diffs.append(f'Kante {a["pair"]}.{k}: {a[k]!r} != {b[k]!r}')
    if s1['clusters'] != s2['clusters']:
        diffs.append(f'Cluster: {s1["clusters"]!r} != {s2["clusters"]!r}')
    if s1['graph'] != s2['graph']:
        diffs.append(f'Graph-Label: {s1["graph"]!r} != {s2["graph"]!r}')
    return diffs


# ------------------------------------------------- Diagramm-Fundstellen

def iter_file_diagrams():
    """Alle Datei-Diagramme unter _src/diagrams/ (ohne _inline-Quellen)."""
    for f in sorted((SRC / 'diagrams').rglob('*.svg')):
        yield f


def iter_inline_diagrams():
    """(Fragmentpfad, Wrapper-Div, Fragment-Wurzel) je Inline-Diagramm."""
    for f in sorted((SRC / 'content' / 'ai').rglob('*.html')):
        raw = f.read_text(encoding='utf-8')
        if '<svg' not in raw:
            continue
        el = LH.fragment_fromstring(raw)
        wraps = []
        for d in el.iterdescendants():
            if d.tag == 'div' and set(_classes(d)) & {'diagram', 'umlwrap'}:
                if d.find('.//svg') is not None:
                    wraps.append(d)
        if wraps:
            yield f, el, wraps


def svg_of_wrapper(d):
    svg = d.find('.//svg')
    return LH.tostring(svg, encoding='unicode')


def is_graphviz(svg_text):
    return 'class="graph"' in svg_text or "class='graph'" in svg_text
