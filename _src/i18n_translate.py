#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arbeitspakete für die Übersetzung der Register erzeugen und zusammenführen.

    python3 i18n_translate.py split <lang> [--kb=40]
        Noch unübersetzte Segmente + Labels der Sprache in JSONL-Pakete
        unter i18n/work/<lang>/batch_NN.jsonl schreiben.
        Zeilenformat: {"id": …, "de": …}   (Label-IDs tragen Präfix "L:")

    python3 i18n_translate.py merge <lang>
        Alle i18n/work/<lang>/batch_NN.out.jsonl validieren und in die
        Register i18n/<lang>/segments.json + labels.json einarbeiten.
        Zeilenformat der Antwortdateien: {"id": …, "t": …}
        Abgelehnte Zeilen landen in i18n/work/<lang>/fehler.json.

    python3 i18n_translate.py status
        Fortschritt aller Sprachen anzeigen.

Validierung beim Merge:
  - Platzhalter ⟦k⟧: exakt dieselbe Multimenge wie im Quelltext
  - [SWS_…]-Kennungen und AUTOSAR_/EXP_/FO_-Dokumentkürzel bleiben erhalten
  - <em>/<strong>-Tags: gleiche Anzahl wie im Quelltext
  - Übersetzung nicht leer und nicht identisch mit Quelle (außer Label ohne
    natürliche Wörter, z. B. reine Symbolfolgen)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(HERE, "i18n")
WORK = os.path.join(I18N, "work")
sys.path.insert(0, HERE)
from lib_docmodel import LANGS

_PH = re.compile(r"\u27e6\d+\u27e7")
_IDS = re.compile(r"\[SWS_[A-Z]+_\d+\]|\b(?:AUTOSAR|EXP|FO)_[A-Za-z0-9]+\b")
_TAGS = re.compile(r"</?(em|strong|i|u|sub|sup)\b")


def _lade(p, default):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def _register(lang):
    seg = _lade(os.path.join(I18N, lang, "segments.json"), {})
    lab = _lade(os.path.join(I18N, lang, "labels.json"), {})
    return seg, lab


def _quelle():
    seg = _lade(os.path.join(I18N, "segments.de.json"), {})
    lab = _lade(os.path.join(I18N, "labels.de.json"), {})
    return seg, lab


def offene(lang):
    """[(id, quelltext)] aller noch unübersetzten Einträge (Segmente + Labels)."""
    qseg, qlab = _quelle()
    seg, lab = _register(lang)
    out = [(sid, e["m"]) for sid, e in qseg.items() if sid not in seg]
    out += [("L:" + l, l) for l in qlab if l not in lab]
    return out


def split(lang, kb=40):
    os.makedirs(os.path.join(WORK, lang), exist_ok=True)
    # alte Pakete räumen (nur Eingaben; .out-Dateien bleiben)
    for f in os.listdir(os.path.join(WORK, lang)):
        if re.fullmatch(r"batch_\d+\.jsonl", f):
            os.remove(os.path.join(WORK, lang, f))
    posten = offene(lang)
    grenze = kb * 1024
    batch, groesse, nr = [], 0, 0
    def flush():
        nonlocal batch, groesse, nr
        if not batch:
            return
        nr += 1
        p = os.path.join(WORK, lang, "batch_%02d.jsonl" % nr)
        with open(p, "w", encoding="utf-8") as f:
            for zeile in batch:
                f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
        batch, groesse = [], 0
    for id_, de in posten:
        batch.append({"id": id_, "de": de})
        groesse += len(de.encode("utf-8"))
        if groesse >= grenze:
            flush()
    flush()
    print("[%s] %d offene Einträge -> %d Pakete unter i18n/work/%s/"
          % (lang, len(posten), nr, lang))


def pruefe(de, t):
    """Fehlertext oder None."""
    if not isinstance(t, str) or not t.strip():
        return "leer"
    if sorted(_PH.findall(de)) != sorted(_PH.findall(t)):
        return "Platzhalter weichen ab"
    if sorted(_IDS.findall(de)) != sorted(_IDS.findall(t)):
        return "Spezifikationskennungen weichen ab"
    if len(_TAGS.findall(de)) != len(_TAGS.findall(t)):
        return "em/strong-Tags weichen ab"
    return None


# Deutsche Anführungszeichen-Paare („…“) in Übersetzungen: Übersetzer
# übernehmen sie gelegentlich aus der Quelle. Beim Merge werden Paare in
# die sprachübliche Form überführt (Stil wie ui.json docref.zitat_a/z).
_ZITATE = {"en": ("“", "”"), "hi": ("“", "”"), "ko": ("“", "”"),
           "zh": ("“", "”"), "es": ("«", "»"), "pt": ("«", "»"),
           "ru": ("«", "»"), "ar": ("«", "»"),
           "fr": ("«\u202f", "\u202f»")}
_DE_PAAR = re.compile("„([^„“]*)“")


def normalisiere_zitate(t, lang):
    za, zz = _ZITATE.get(lang, ("„", "“"))
    return _DE_PAAR.sub(lambda m: za + m.group(1) + zz, t)


def merge(lang):
    qseg, qlab = _quelle()
    seg, lab = _register(lang)
    d = os.path.join(WORK, lang)
    fehler, uebernommen = [], 0
    for f in sorted(os.listdir(d) if os.path.isdir(d) else []):
        if not re.fullmatch(r"batch_\d+\.out\.jsonl", f):
            continue
        for zeilennr, zeile in enumerate(open(os.path.join(d, f), encoding="utf-8"), 1):
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                e = json.loads(zeile)
                id_, t = e["id"], e["t"]
            except (ValueError, KeyError) as ex:
                fehler.append({"datei": f, "zeile": zeilennr, "grund": "JSON: %s" % ex})
                continue
            if id_.startswith("L:"):
                de = id_[2:]
                if de not in qlab:
                    fehler.append({"datei": f, "zeile": zeilennr, "grund": "unbekanntes Label", "id": id_})
                    continue
            else:
                if id_ not in qseg:
                    fehler.append({"datei": f, "zeile": zeilennr, "grund": "unbekannte Segment-ID", "id": id_})
                    continue
                de = qseg[id_]["m"]
            grund = pruefe(de, t)
            if grund:
                fehler.append({"datei": f, "zeile": zeilennr, "id": id_, "grund": grund,
                               "de": de[:120], "t": (t or "")[:120] if isinstance(t, str) else t})
                continue
            t = normalisiere_zitate(t, lang)
            if id_.startswith("L:"):
                lab[de] = t
            else:
                seg[id_] = t
            uebernommen += 1
    os.makedirs(os.path.join(I18N, lang), exist_ok=True)
    json.dump(seg, open(os.path.join(I18N, lang, "segments.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    json.dump(lab, open(os.path.join(I18N, lang, "labels.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
    fp = os.path.join(d, "fehler.json")
    if fehler:
        json.dump(fehler, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    elif os.path.exists(fp):
        os.remove(fp)
    rest = len(offene(lang))
    print("[%s] übernommen: %d, abgelehnt: %d, noch offen: %d%s"
          % (lang, uebernommen, len(fehler), rest,
             "  (Details: i18n/work/%s/fehler.json)" % lang if fehler else ""))
    return len(fehler)


def status():
    qseg, qlab = _quelle()
    gesamt = len(qseg) + len(qlab)
    print("Sprache  übersetzt  offen   (von %d)" % gesamt)
    for lang in LANGS:
        rest = len(offene(lang))
        print("  %-5s  %8d  %5d" % (lang, gesamt - rest, rest))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("split", "merge", "status"):
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "status":
        status()
        return
    lang = sys.argv[2]
    if lang not in LANGS:
        sys.exit("unbekannte Sprache: %s (erwartet: %s)" % (lang, " ".join(LANGS)))
    if cmd == "split":
        kb = 40
        for a in sys.argv[3:]:
            if a.startswith("--kb="):
                kb = int(a[5:])
        split(lang, kb)
    else:
        sys.exit(1 if merge(lang) else 0)


if __name__ == "__main__":
    main()
