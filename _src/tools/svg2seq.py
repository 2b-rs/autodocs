# -*- coding: utf-8 -*-
"""
svg2seq.py — Einmalige Rückgewinnung der Sequenzdiagramm-Spezifikationen
(.seq.json) aus den handgebauten Bestands-SVGs.

Vorgehen: geometrische Deutung (Lebenslinien, Kästen, Pfeile, Notizen,
alt/opt-Rahmen), danach Roundtrip-Prüfung: Spec -> seqgen.render_seq ->
erneut deuten -> Spezifikationen müssen übereinstimmen; zusätzlich müssen
alle Textinhalte des Originals im Neu-Render enthalten sein.

Ablage wie bei den .dot-Quellen:
  Datei-Diagramme:  _src/diagrams/<seite>/svg_NN.seq.json
  Inline-Diagramme: _src/content/ai/<seite>/<fragment>.<id>.seq.json
"""
import json
import re
import sys
from pathlib import Path

from lxml import html as LH

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lib_svgdiag as D
import seqgen


def _f(el, a, d=0.0):
    try:
        return float(el.get(a))
    except (TypeError, ValueError):
        return d


def parse_seq_svg(text):
    """Handgebautes Sequenz-SVG -> Spezifikation (dict)."""
    root = D.parse_svg_root(text)
    svg = root if D._ln(root) == 'svg' else root.find('.//svg')

    els = []
    for el in svg.iter():
        t = D._ln(el)
        if t in ('text', 'line', 'rect', 'path'):
            anc = el.getparent()
            link = None
            while anc is not None:
                if D._ln(anc) == 'a':
                    link = {'href': D._attr(anc, 'href'),
                            'klasse': anc.get('class')}
                    break
                anc = anc.getparent()
            els.append((t, el, link))

    spec = {'titel': None, 'teilnehmer': [], 'schritte': []}
    lifel = []          # x-Zentren
    boxes = []          # (x, label, link)
    items = []          # (y, schritt-dict)  für Sortierung
    texts_free = []

    # 1. Grundgerüst
    for t, el, link in els:
        if t == 'line':
            if el.get('stroke-dasharray') == '4,4' and _f(el, 'x1') == _f(el, 'x2'):
                lifel.append(_f(el, 'x1'))
        elif t == 'rect':
            if el.get('fill') not in (None, 'none') and _f(el, 'y') < 100:
                boxes.append([_f(el, 'x') + _f(el, 'width') / 2, None, link])
    lifel = sorted(set(lifel))

    def part_idx(x):
        return min(range(len(lifel)), key=lambda i: abs(lifel[i] - x))

    # 2. Elemente deuten
    notes = []       # (bbox, zeilen)
    frames = []      # (top, bottom)
    for t, el, link in els:
        if t == 'text':
            ti = {'text': el.text or '', 'x': _f(el, 'x'), 'y': _f(el, 'y'),
                  'size': _f(el, 'font-size', 11),
                  'bold': el.get('font-weight') == 'bold',
                  'italic': el.get('font-style') == 'italic',
                  'anchor': el.get('text-anchor', 'start')}
            if ti['bold'] and ti['y'] < 40:
                spec['titel'] = ti['text']
            elif 50 < ti['y'] < 100 and ti['anchor'] == 'middle' and boxes:
                b = min(boxes, key=lambda b_: abs(b_[0] - ti['x']))
                if abs(b[0] - ti['x']) < 5:
                    b[1] = (b[1] or []) + [(ti['y'], ti['text'])]
                else:
                    texts_free.append(ti)
            else:
                texts_free.append(ti)
        elif t == 'line':
            dash = el.get('stroke-dasharray')
            mk = el.get('marker-end') or ''
            y1, y2 = _f(el, 'y1'), _f(el, 'y2')
            x1, x2 = _f(el, 'x1'), _f(el, 'x2')
            if dash == '4,4':
                continue
            if mk:
                pfeil = ('annahme' if 'arrA' in mk
                         else 'offen' if 'arrO' in mk else 'voll')
                st = {'art': 'nachricht', 'von': part_idx(x1),
                      'nach': part_idx(x2), 'text': [], 'pfeil': pfeil}
                if dash:
                    st['gestrichelt'] = True
                items.append([y1, st, (min(x1, x2) + max(x1, x2)) / 2])
            elif dash and abs(y1 - y2) < 0.1:
                items.append([y1, {'art': 'trenner'}, None])
        elif t == 'rect':
            if el.get('fill') in (None, 'none') and _f(el, 'width') > 100:
                top, h = _f(el, 'y'), _f(el, 'height')
                frames.append((top, top + h))
                items.append([top, {'art': 'rahmen', 'typ': 'alt'}, None])
                items.append([top + h, {'art': 'rahmen-ende'}, None])
        elif t == 'path':
            d = el.get('d', '')
            mk = el.get('marker-end') or ''
            m_self = re.match(r'M ([\d.]+) ([\d.]+) h ([\d.]+) v ([\d.]+) h -\3\s*$', d)
            if mk and m_self:
                x, y = float(m_self.group(1)), float(m_self.group(2))
                pfeil = ('annahme' if 'arrA' in mk
                         else 'offen' if 'arrO' in mk else 'voll')
                st = {'art': 'selbst', 'teilnehmer': part_idx(x), 'text': [],
                      'pfeil': pfeil}
                items.append([y, st, x])
            elif 'l 10 10' in d:
                m = re.match(r'M ([\d.]+) ([\d.]+) h ([\d.]+) l 10 10 v ([\d.]+) h -([\d.]+) z', d)
                if m:
                    left, top = float(m.group(1)), float(m.group(2))
                    w = float(m.group(5))
                    h = float(m.group(4)) + 10
                    st = {'art': 'notiz', 'ueber': None, 'text': []}
                    notes.append(((left, top, left + w, top + h), st))
                    items.append([top, st, left + w / 2])
            # Falz und alt-Tab: keine eigenen Schritte

    # 3. Freitexte zuordnen
    for ti in texts_free:
        x, y = ti['x'], ti['y']
        # Notizzeile?
        hit = None
        for (l, t_, r, b), st in notes:
            if l - 1 <= x <= r + 1 and t_ <= y <= b + 1:
                hit = st
                break
        if hit is not None:
            hit['text'].append(ti['text'])
            continue
        # alt/opt-Schlüsselwort am Rahmen-Tab
        fr_hit = None
        for (top, bottom) in frames:
            if abs(y - (top + 15)) < 3 and x < 120:
                fr_hit = top
                break
        if fr_hit is not None:
            for it in items:
                if it[1].get('art') == 'rahmen' and abs(it[0] - fr_hit) < 0.1:
                    if ti['bold']:
                        it[1]['typ'] = ti['text']
                    else:
                        it[1]['guard'] = ti['text']
                    break
            continue
        # Guard unter einem Trenner
        sep_hit = None
        for it in items:
            if it[1].get('art') == 'trenner' and 0 < y - it[0] <= 20 and x < 120:
                sep_hit = it[1]
                break
        if sep_hit is not None:
            sep_hit['guard'] = ti['text']
            continue
        # Selbstnachricht-Beschriftung (neben der Schleife) oder
        # Nachrichtenbeschriftung (zentriert über der Linie). Zentrierte
        # Texte bevorzugt der Nachricht zuordnen, linksbündige der Schleife.
        self_hit = None
        for it in items:
            if it[1].get('art') == 'selbst' and it[2] is not None:
                if -70 <= x - it[2] <= 130 and -30 <= y - it[0] <= 45:
                    self_hit = it[1]
                    break
        best = None
        for it in items:
            if it[1].get('art') == 'nachricht':
                dy = it[0] - y
                dx = abs((it[2] or 0) - x)
                if 0 < dy <= 45 and dx < 80:
                    if best is None or dy < best[0]:
                        best = (dy, it[1])
        if ti['anchor'] == 'middle' and best:
            best[1]['text'].append((y, ti['text']))
            continue
        if self_hit is not None:
            self_hit['text'].append((y, ti['text']))
            continue
        if best:
            best[1]['text'].append((y, ti['text']))
            continue
        raise ValueError(f'Text nicht zuordenbar: {ti["text"]!r} @ {x},{y}')

    # Mehrzeilige Texte nach y sortieren
    for _, st, _m in items:
        if isinstance(st.get('text'), list) and st['text'] \
                and isinstance(st['text'][0], tuple):
            st['text'] = [t for _, t in sorted(st['text'])]

    # 4. Teilnehmer und Schritte finalisieren
    boxes.sort(key=lambda b: b[0])
    for x, name, link in boxes:
        zeilen = [t for _, t in sorted(name or [])]
        tnr = {'name': zeilen[0] if len(zeilen) == 1 else zeilen}
        if link:
            tnr['href'] = link['href']
            if link.get('klasse') and link['klasse'] != 'vis-app':
                tnr['klasse'] = link['klasse']
        spec['teilnehmer'].append(tnr)

    items.sort(key=lambda it: it[0])
    for _, st, mid in items:
        if st['art'] == 'notiz':
            # beteiligte Teilnehmer über Mittelpunkt bestimmen
            best = None
            for i in range(len(lifel)):
                for j in range(i, len(lifel)):
                    c = (lifel[i] + lifel[j]) / 2
                    d_ = abs(c - mid)
                    if best is None or d_ < best[0]:
                        best = (d_, [i] if i == j else [i, j])
            st['ueber'] = best[1]
        if st.get('pfeil') == 'voll':
            del st['pfeil']
        spec['schritte'].append(st)
    return spec


def _norm(spec):
    return json.dumps(spec, sort_keys=True, ensure_ascii=False)


def all_seq_jobs():
    jobs = []
    for f in D.iter_file_diagrams():
        t = f.read_text(encoding='utf-8')
        if not D.is_graphviz(t):
            jobs.append((t, f.with_suffix('.seq.json'), str(f.relative_to(D.SRC))))
    for f, el, wraps in D.iter_inline_diagrams():
        for d_ in wraps:
            t = D.svg_of_wrapper(d_)
            if not D.is_graphviz(t):
                did = d_.get('id')
                dst = f.parent / f'{f.stem}.{did}.seq.json'
                jobs.append((t, dst, f'{f.relative_to(D.SRC)}#{did}'))
    return jobs


def main():
    ok = fail = 0
    for text, dst, ref in all_seq_jobs():
        try:
            spec = parse_seq_svg(text)
            neu = seqgen.render_seq(spec)
            spec2 = parse_seq_svg(neu)
            if _norm(spec) != _norm(spec2):
                raise ValueError('Roundtrip-Abweichung:\n  A: %s\n  B: %s'
                                 % (_norm(spec)[:600], _norm(spec2)[:600]))
            # Alle Originaltexte müssen im Neu-Render vorkommen
            alt_texte = sorted(x.text or '' for x in
                               D.parse_svg_root(text).iter() if D._ln(x) == 'text')
            neu_texte = sorted(x.text or '' for x in
                               D.parse_svg_root(neu).iter() if D._ln(x) == 'text')
            if alt_texte != neu_texte:
                raise ValueError(f'Textverlust: {set(alt_texte) ^ set(neu_texte)}')
            dst.write_text(json.dumps(spec, ensure_ascii=False, indent=1) + '\n',
                           encoding='utf-8')
            ok += 1
        except Exception as ex:
            fail += 1
            print(f'PROBLEM {ref}: {str(ex)[:400]}')
    print(f'OK {ok}, Probleme {fail}')


if __name__ == '__main__':
    main()
