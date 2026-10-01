# -*- coding: utf-8 -*-
"""
seqgen.py — Generator für Sequenzdiagramme im Hausstil.

Quelle ist eine .seq.json-Spezifikation:

{
  "titel": "Storage öffnen und nutzen",
  "teilnehmer": [
    {"name": "Adaptive Application"},
    {"name": "ara::per", "href": "../namespaces/ns_per_ara_per_d9a3e9.html",
     "klasse": "vis-app"}
  ],
  "schritte": [
    {"art": "nachricht", "von": 0, "nach": 1, "text": ["Open…Storage(...)"],
     "pfeil": "voll",        # voll | offen | annahme
     "gestrichelt": false},  # true bei Antworten/Rückgaben
    {"art": "selbst", "teilnehmer": 1, "text": ["intern qualifizieren"]},
    {"art": "notiz", "ueber": [0, 2], "text": ["Hinweistext …"]},
    {"art": "rahmen", "typ": "alt", "guard": "[Fehler wird gesetzt]"},
    {"art": "trenner", "guard": "[anderer Fall]"},
    {"art": "rahmen-ende"}
  ]
}

Layoutkonstanten sind bewusst fest verdrahtet (kanonisches Raster), damit alle
Sequenzdiagramme des Trees identisch wirken. Nur Inhalte gehören in die Spec.
"""
import json

# Raster
X0 = 135          # Zentrum des ersten Teilnehmers
GAP = 210         # Abstand der Teilnehmerzentren
BOX_W, BOX_H = 186, 38
TITLE_Y = 24
BOX_Y = 56
LIFE_Y = 102      # Beginn der Lebenslinien
LEAD = 13         # Zeilenhöhe 11pt-Text
FRAME_X = 40      # Rahmen: Abstand vom linken/rechten Rand

C_TEXT = '#28251d'
C_ACCENT = '#01696f'
C_GRAY = '#8a867c'
C_NOTE = '#f0eeea'
C_ASSUME = '#b58900'

# Näherung der Helvetica-Zeichenbreiten (1/1000 em), für Notizbreiten
_W = {}
for c in 'ilj.,:;!|': _W[c] = 280
for c in 'ftrI()[]/ ': _W[c] = 340
for c in 'abcdeghknopqsuvxyz': _W[c] = 545
for c in 'mw': _W[c] = 820
for c in 'ABCDEFGHKNOPQRSTUVXYZÄÖÜ': _W[c] = 700
for c in 'MW': _W[c] = 900
for c in '0123456789äöüß-_': _W[c] = 560


def _text_w(s, size=11):
    return sum(_W.get(c, 600) for c in s) * size / 1000.0


def _esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def render_seq(spec):
    """Spezifikation -> SVG-Text (HTML-serialisierbar)."""
    tn = spec['teilnehmer']
    n = len(tn)
    W = 2 * X0 + GAP * (n - 1)
    cx = [X0 + GAP * i for i in range(n)]

    body = []       # alles unterhalb der Lebenslinien-Definitionen
    markers = set()
    cur = LIFE_Y
    frames = []     # offene Rahmen: (top, [separator-/kopf-elemente])
    frame_parts = []

    def marker_for(pfeil):
        m = {'voll': 'arrF', 'offen': 'arrO', 'annahme': 'arrA'}[pfeil or 'voll']
        markers.add(m)
        return m

    for s in spec['schritte']:
        art = s['art']
        if art == 'nachricht':
            lines = s.get('text', [])
            k = len(lines)
            y = cur + 17 + LEAD * k
            x1, x2 = cx[s['von']], cx[s['nach']]
            mid = (x1 + x2) / 2
            for j, t in enumerate(lines):
                ty = y - 6 - LEAD * (k - 1 - j)
                body.append(f'<text x="{mid}" y="{ty}" text-anchor="middle" '
                            f'font-size="11" fill="{C_TEXT}">{_esc(t)}</text>')
            dash = ' stroke-dasharray="6,4"' if s.get('gestrichelt') else ''
            mk = marker_for(s.get('pfeil'))
            color = C_ASSUME if s.get('pfeil') == 'annahme' else C_TEXT
            body.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
                        f'stroke="{color}" stroke-width="1.1"{dash} '
                        f'marker-end="url(#{mk})"></line>')
            cur = y + 4
        elif art == 'selbst':
            lines = s.get('text', [])
            k = len(lines)
            x = cx[s['teilnehmer']]
            y = cur + 10
            mk = marker_for(s.get('pfeil'))
            body.append(f'<path d="M {x} {y} h 46 v 22 h -46" fill="none" '
                        f'stroke="{C_TEXT}" stroke-width="1.1" '
                        f'marker-end="url(#{mk})"></path>')
            # Beim letzten Teilnehmer würde die Beschriftung rechts über den
            # Rand laufen -> dann links der Schleife, rechtsbündig setzen.
            rechts = s['teilnehmer'] < n - 1
            tx, anker = (x + 54, 'start') if rechts else (x - 8, 'end')
            for j, t in enumerate(lines):
                body.append(f'<text x="{tx}" y="{y + 15 + LEAD * j}" '
                            f'text-anchor="{anker}" font-size="11" '
                            f'fill="{C_TEXT}">{_esc(t)}</text>')
            cur = max(y + 22, y + 15 + LEAD * (k - 1) + 8 if k else 0) + 4
        elif art == 'notiz':
            lines = s.get('text', [])
            k = len(lines)
            ue = s['ueber']
            if len(ue) == 1:
                center = cx[ue[0]]
            else:
                center = (cx[ue[0]] + cx[ue[-1]]) / 2
            w = round(max(_text_w(t) for t in lines) + 26)
            left = round(center - w / 2, 1)
            top = cur + 13
            h = 16 + LEAD * k
            body.append(f'<path d="M {left} {top} h {w - 10} l 10 10 v {h - 10} '
                        f'h -{w} z" fill="{C_NOTE}" stroke="{C_GRAY}" '
                        f'stroke-width="1"></path>')
            body.append(f'<path d="M {round(left + w - 10, 1)} {top} v 10 h 10" '
                        f'fill="none" stroke="{C_GRAY}" stroke-width="1"></path>')
            for j, t in enumerate(lines):
                body.append(f'<text x="{round(left + 8, 1)}" '
                            f'y="{top + 14 + LEAD * j}" font-size="11" '
                            f'fill="{C_TEXT}">{_esc(t)}</text>')
            cur = top + h
        elif art == 'rahmen':
            top = cur + 14
            frames.append((top, len(frame_parts)))
            frame_parts.append(None)  # Platzhalter, Rechteck kommt bei Ende
            body.append(f'<path d="M {FRAME_X} {top} h 46 v 14 l -8 8 h -38 z" '
                        f'fill="{C_NOTE}" stroke="{C_GRAY}" '
                        f'stroke-width="1"></path>')
            body.append(f'<text x="{FRAME_X + 8}" y="{top + 15}" font-size="11" '
                        f'font-weight="bold" fill="{C_TEXT}">'
                        f'{_esc(s.get("typ", "alt"))}</text>')
            if s.get('guard'):
                body.append(f'<text x="{FRAME_X + 56}" y="{top + 15}" '
                            f'font-size="11" font-style="italic" '
                            f'fill="{C_TEXT}">{_esc(s["guard"])}</text>')
            cur = top + 16
        elif art == 'trenner':
            y = cur + 18
            body.append(f'<line x1="{FRAME_X}" y1="{y}" x2="{W - FRAME_X}" '
                        f'y2="{y}" stroke="{C_GRAY}" stroke-width="1" '
                        f'stroke-dasharray="5,3"></line>')
            cur = y
            if s.get('guard'):
                body.append(f'<text x="{FRAME_X + 12}" y="{y + 15}" '
                            f'font-size="11" font-style="italic" '
                            f'fill="{C_TEXT}">{_esc(s["guard"])}</text>')
                cur = y + 19
        elif art == 'rahmen-ende':
            top, idx = frames.pop()
            bottom = cur + 18
            frame_parts[idx] = (f'<rect x="{FRAME_X}" y="{top}" '
                                f'width="{W - 2 * FRAME_X}" '
                                f'height="{bottom - top}" fill="none" '
                                f'stroke="{C_GRAY}" stroke-width="1.1"></rect>')
            cur = bottom
        else:
            raise ValueError(f'unbekannte Schrittart: {art}')

    life_end = cur + 20
    H = life_end + 14

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewbox="0 0 {W} {H}" '
           f'font-family="Helvetica,sans-Serif" style="max-width:{W}px">']
    if spec.get('titel'):
        out.append(f'<text x="{W / 2}" y="{TITLE_Y}" text-anchor="middle" '
                   f'font-size="13" font-weight="bold" fill="{C_TEXT}">'
                   f'{_esc(spec["titel"])}</text>')
    for x in cx:
        out.append(f'<line x1="{x}" y1="{LIFE_Y}" x2="{x}" y2="{life_end}" '
                   f'stroke="{C_GRAY}" stroke-dasharray="4,4" '
                   f'stroke-width="1"></line>')
    for i, t in enumerate(tn):
        box = (f'<rect x="{cx[i] - BOX_W // 2}" y="{BOX_Y}" width="{BOX_W}" '
               f'height="{BOX_H}" fill="#ffffff" stroke="{C_ACCENT}" '
               f'stroke-width="1.2"></rect>')
        deco = ' text-decoration="underline"' if t.get('href') else ''
        names = t['name'] if isinstance(t['name'], list) else [t['name']]
        k = len(names)
        lbl = ''
        for j, nm in enumerate(names):
            ty = round(BOX_Y + 23 - 6.5 * (k - 1) + 13 * j, 1)
            lbl += (f'<text x="{cx[i]}" y="{ty}" text-anchor="middle" '
                    f'font-size="12" fill="{C_ACCENT}"{deco}>{_esc(nm)}</text>')
        if t.get('href'):
            cls = t.get('klasse', 'vis-app')
            out.append(f'<a class="{cls}" href="{_esc(t["href"])}">{box}{lbl}</a>')
        else:
            out.append(box + lbl)

    defs = ['<defs>']
    if 'arrF' in markers or not markers:
        defs.append('<marker id="arrF" markerwidth="11" markerheight="9" '
                    'refx="10" refy="4.5" orient="auto">'
                    f'<polygon points="0 0, 11 4.5, 0 9" fill="{C_TEXT}">'
                    '</polygon></marker>')
    if 'arrA' in markers:
        defs.append('<marker id="arrA" markerwidth="11" markerheight="9" '
                    'refx="10" refy="4.5" orient="auto">'
                    f'<polygon points="0 0, 11 4.5, 0 9" fill="{C_ASSUME}">'
                    '</polygon></marker>')
    if 'arrO' in markers:
        defs.append('<marker id="arrO" markerwidth="12" markerheight="10" '
                    'refx="11" refy="5" orient="auto">'
                    f'<polyline points="1 1, 11 5, 1 9" fill="none" '
                    f'stroke="{C_TEXT}" stroke-width="1.2"></polyline></marker>')
    defs.append('</defs>')
    out.extend(defs)
    out.extend(x for x in frame_parts if x)
    out.extend(body)
    out.append('</svg>')
    return ''.join(out)


def render_seq_file(path):
    with open(path, encoding='utf-8') as fh:
        return render_seq(json.load(fh))
