#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kuratierungs-Workflow für KI-generierte Erklärungen (Texte + Diagramme).

Verwaltet die Herkunftsakten (_src/ai/traces/**) und den Zyklus
Invalidieren → Auftrag → Merge, mit dem einzelne KI-Fragmente oder ganze
Seitenbereiche neu erzeugt werden, wenn neues Wissen hinzukommt, Records
sich ändern oder die Policy (_src/ai/policy.json) angepasst wird.
Inhaltliche Leitplanken: _src/ai/RICHTLINIEN.md.

Kommandos
  status                       Überblick: legacy/aktuell/veraltet, Records
                               geändert (Hash-Abgleich), Traces ohne Fragment,
                               Fragmente ohne Trace, Policy-Versionen
  zeige <fragment>             Trace eines Fragments zusammengefasst anzeigen
  invalidiere [ziele] [--grund=…]
                               Fragmente als „veraltet“ markieren; Ziele:
                               --quelle=<dok-id>  alle Nutzer eines Quelldokuments
                               --element=<ID>     alle zu einem Spezifikationselement
                               <pfad>             einzelnes Fragment (rel. zu _src
                                                  oder content/ai/…)
  auftrag <ziel> [<ziel>…]     Regenerierungsauftrag nach ai/work/ schreiben;
                               Ziel: Fragmentpfad, Seitendatei (classes/x.html),
                               Element-ID oder --veraltet (alle veralteten)
  merge                        ai/work/auftrag_*.out.json prüfen und einspielen
                               (Fragmente, Diagrammquellen, Traces)

Typischer Ablauf: siehe ai/RICHTLINIEN.md, Abschnitt „Regenerierung“.
Nach merge wie üblich: render_diagrams.py (falls Diagramme geändert),
generate.py, validate.py, i18n_extract.py.
"""
import datetime
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_docmodel import SRC, AI_DIR, record_relpath, record_hash

AI = os.path.join(SRC, "ai")
TRACES = os.path.join(AI, "traces")
WORK = os.path.join(AI, "work")


def lade_policy():
    return json.load(open(os.path.join(AI, "policy.json"), encoding="utf-8"))


def dump(pfad, obj):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def iter_traces():
    for p in sorted(glob.glob(os.path.join(TRACES, "**", "*.json"), recursive=True)):
        yield p, json.load(open(p, encoding="utf-8"))


def trace_pfad(fragment_rel):
    """content/ai/<u>/<stem>.html → ai/traces/<u>/<stem>.json (absolut)."""
    unter = os.path.relpath(os.path.join(SRC, fragment_rel), AI_DIR)
    return os.path.join(TRACES, unter[:-len(".html")] + ".json")


def norm_fragment(arg):
    """Nutzerangabe → Fragmentpfad relativ zu _src, oder None."""
    for kand in (arg, os.path.join("content", "ai", arg)):
        if os.path.exists(os.path.join(SRC, kand)) and kand.startswith("content/ai/"):
            return kand
    return None


def records_geaendert(t):
    return sorted(e for e, h in (t.get("elemente_stand") or {}).items()
                  if record_hash(e) != h)


# ---------------------------------------------------------------- status ---

def cmd_status():
    policy = lade_policy()
    stati, versionen, geaendert, ohne_fragment = {}, {}, [], []
    traced = set()
    for p, t in iter_traces():
        stati[t["status"]] = stati.get(t["status"], 0) + 1
        v = t.get("policy_version")
        versionen[v] = versionen.get(v, 0) + 1
        traced.add(t["fragment"])
        if not os.path.exists(os.path.join(SRC, t["fragment"])):
            ohne_fragment.append(t["fragment"])
        elif t["status"] != "veraltet" and records_geaendert(t):
            geaendert.append((t["fragment"], records_geaendert(t)))
    alle = {os.path.relpath(f, SRC)
            for f in glob.glob(os.path.join(AI_DIR, "**", "*.html"), recursive=True)}
    ohne_trace = sorted(alle - traced)

    print("Policy-Version aktuell: %s (Stand %s)" % (policy["version"], policy["stand"]))
    print("Traces: %d  —  Status: %s" % (sum(stati.values()),
          ", ".join("%s=%d" % kv for kv in sorted(stati.items()))))
    print("erzeugt mit Policy-Version: %s"
          % ", ".join("%s=%d" % kv for kv in sorted(versionen.items(), key=str)))
    if geaendert:
        print("\nVERALTET (assoziierte Records geändert seit Erzeugung): %d" % len(geaendert))
        for f, els in geaendert[:20]:
            print("  %s  ← %s" % (f, ", ".join(els)))
        if len(geaendert) > 20:
            print("  … und %d weitere" % (len(geaendert) - 20))
        print("  → ai_workflow.py invalidiere/auftrag, siehe RICHTLINIEN.md")
    if ohne_trace:
        print("\nFragmente OHNE Trace: %d (tools/backfill_traces.py?)" % len(ohne_trace))
        for f in ohne_trace[:10]:
            print("  ", f)
    if ohne_fragment:
        print("\nTraces ohne Fragment (Fragment gelöscht? Trace mit entfernen): %d"
              % len(ohne_fragment))
        for f in ohne_fragment[:10]:
            print("  ", f)
    offene = sorted(glob.glob(os.path.join(WORK, "auftrag_*.json")))
    offene = [p for p in offene if not p.endswith(".out.json")]
    if offene:
        print("\nOffene Aufträge in ai/work/: %d" % len(offene))


# ----------------------------------------------------------------- zeige ---

def cmd_zeige(arg):
    frag = norm_fragment(arg)
    if not frag:
        sys.exit("Fragment nicht gefunden: %s" % arg)
    t = json.load(open(trace_pfad(frag), encoding="utf-8"))
    ge = records_geaendert(t)
    print(json.dumps(t, ensure_ascii=False, indent=1))
    if ge:
        print("\nACHTUNG — Records geändert seit Erzeugung: %s" % ", ".join(ge))


# ----------------------------------------------------------- invalidiere ---

def cmd_invalidiere(args):
    grund = "manuell"
    ziele, quelle, element = [], None, None
    for a in args:
        if a.startswith("--grund="):
            grund = a.split("=", 1)[1]
        elif a.startswith("--quelle="):
            quelle = a.split("=", 1)[1]
        elif a.startswith("--element="):
            element = a.split("=", 1)[1]
        else:
            f = norm_fragment(a)
            if not f:
                sys.exit("Fragment nicht gefunden: %s" % a)
            ziele.append(f)
    n = 0
    for p, t in iter_traces():
        treffer = (t["fragment"] in ziele
                   or (quelle and quelle in t.get("quellen", []))
                   or (element and element in t.get("elemente", [])))
        if not treffer or t["status"] == "veraltet":
            continue
        t["status"] = "veraltet"
        t["invalidiert"] = {"datum": datetime.date.today().isoformat(),
                            "grund": grund,
                            "ausloeser": quelle or element or "direkt"}
        dump(p, t)
        n += 1
    print("als veraltet markiert: %d Fragmente" % n)


# --------------------------------------------------------------- auftrag ---

AUSGABEFORMAT = """Erwartete Ausgabe: JSON-Datei mit demselben Namen wie dieser Auftrag,
Endung .out.json statt .json, im selben Verzeichnis. Aufbau:
{"ergebnisse": [{
  "fragment":  "<wie im Auftrag>",
  "html":      "<vollständiges <div class=\\"ai …\\">-Fragment, deutsch>",
  "diagramme": {"<pfad relativ zu _src>": "<Quelltext .dot | .seq.json>"},
  "trace": {"prompt": "<der bearbeitete Auftragstext>",
            "modell": "<verwendetes Modell>",
            "wissen":   [{"aussage": "...", "quelle": "<dok-id>", "fundstelle": "..."}],
            "annahmen": [{"annahme": "...", "begruendung": "..."}],
            "transkript": "<Denkprozess/Begründungsgang dieses Laufs>",
            "diagramme": {"<pfad>": {"entscheidung": "...", "annahmen": [...],
                                     "transkript": "..."}}}}]}
Alle Vorgaben aus policy und richtlinien sind bindend (Belegpflicht,
Annahmen-Budget, Diagramm-Kriterien, ai-note, deutsche Sprache)."""


def sammle_ziele(args):
    """Auftragsziele → Liste von Fragmentpfaden (rel. zu _src)."""
    frags = []
    traces = list(iter_traces())
    for a in args:
        if a == "--veraltet":
            frags += [t["fragment"] for _, t in traces if t["status"] == "veraltet"]
            continue
        f = norm_fragment(a)
        if f:
            frags.append(f)
            continue
        if a.endswith(".html"):        # Seitendatei → alle Fragmente der Seite
            passend = [t["fragment"] for _, t in traces if t["seite"] == a]
            if not passend:
                sys.exit("keine Fragmente zu Seite: %s" % a)
            frags += passend
            continue
        passend = [t["fragment"] for _, t in traces if a in t.get("elemente", [])]
        if not passend:
            sys.exit("kein Ziel aufgelöst für: %s (weder Fragment, Seite noch Element-ID)" % a)
        frags += passend
    return sorted(set(frags))


def cmd_auftrag(args):
    policy = lade_policy()
    richtlinien = open(os.path.join(AI, "RICHTLINIEN.md"), encoding="utf-8").read()
    frags = sammle_ziele(args)
    auftraege = []
    for frag in frags:
        tp = trace_pfad(frag)
        t = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else None
        records = {}
        for e in (t or {}).get("elemente", []):
            rp = os.path.join(SRC, record_relpath(e))
            if os.path.exists(rp):
                records[e] = json.load(open(rp, encoding="utf-8"))
        diag = {}
        basis = os.path.join(SRC, frag)[:-len(".html")]
        for q in sorted(glob.glob(basis + ".*.dot") + glob.glob(basis + ".*.seq.json")):
            diag[os.path.relpath(q, SRC)] = open(q, encoding="utf-8").read()
        auftraege.append({
            "fragment": frag,
            "seite": t["seite"] if t else None,
            "art": t["art"] if t else None,
            "records": records,
            "bisheriges_fragment": open(os.path.join(SRC, frag), encoding="utf-8").read()
                                   if os.path.exists(os.path.join(SRC, frag)) else None,
            "bisherige_diagramme": diag,
            "trace": t,
        })
    quellen = json.load(open(os.path.join(AI, "quellen.json"), encoding="utf-8"))
    os.makedirs(WORK, exist_ok=True)
    vorhanden = glob.glob(os.path.join(WORK, "auftrag_*.json"))
    nn = 1 + max([int(m.group(1)) for p in vorhanden
                  for m in [re.search(r"auftrag_(\d+)", p)] if m] or [0])
    pfad = os.path.join(WORK, "auftrag_%03d.json" % nn)
    dump(pfad, {"erzeugt": datetime.date.today().isoformat(),
                "policy": policy,
                "richtlinien": richtlinien,
                "quellenregister": quellen,
                "ausgabeformat": AUSGABEFORMAT,
                "auftraege": auftraege})
    print("Auftrag geschrieben: %s (%d Fragmente)" % (os.path.relpath(pfad, SRC), len(auftraege)))
    print("Ergebnis als %s daneben legen, dann: ai_workflow.py merge"
          % os.path.basename(pfad).replace(".json", ".out.json"))


# ----------------------------------------------------------------- merge ---

def pruefe_html(html_text):
    """Strukturprüfung eines Fragments; Liste von Fehlertexten."""
    from lxml import html as LH
    fehler = []
    try:
        el = LH.fragment_fromstring(html_text)
    except Exception as e:
        return ["HTML nicht parsebar: %s" % e]
    if el.tag != "div" or "ai" not in (el.get("class") or "").split():
        fehler.append("Wurzel ist kein <div class=\"ai …\">")
    if not el.xpath(".//p[contains(@class,'ai-note')]"):
        fehler.append("abschließende <p class=\"ai-note\"> fehlt")
    if "⟦" in html_text or "⟧" in html_text:
        fehler.append("i18n-Platzhalter (⟦…⟧) im kanonischen Text")
    return fehler


def cmd_merge():
    policy = lade_policy()
    heute = datetime.date.today().isoformat()
    eingespielt, diagramm_dabei = 0, False
    for outp in sorted(glob.glob(os.path.join(WORK, "auftrag_*.out.json"))):
        daten = json.load(open(outp, encoding="utf-8"))
        for erg in daten["ergebnisse"]:
            frag = erg["fragment"]
            fehler = pruefe_html(erg["html"])
            if fehler:
                print("ABGELEHNT %s: %s" % (frag, "; ".join(fehler)))
                continue
            tinfo = erg.get("trace", {})
            budget = policy["annahmen"]["budget_je_text"]
            if len(tinfo.get("annahmen", [])) > budget:
                print("WARNUNG %s: %d Annahmen > Budget %d (policy.json)"
                      % (frag, len(tinfo["annahmen"]), budget))
            # Fragment + Diagrammquellen schreiben
            fp = os.path.join(SRC, frag)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            open(fp, "w", encoding="utf-8").write(erg["html"])
            for rel, quelltext in (erg.get("diagramme") or {}).items():
                dp = os.path.join(SRC, rel)
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                open(dp, "w", encoding="utf-8").write(quelltext)
                diagramm_dabei = True
            # Trace aktualisieren
            tp = trace_pfad(frag)
            t = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {
                "fragment": frag, "seite": None, "art": None, "elemente": [],
                "zitate": [], "quellen": [], "diagramme": {}}
            t["prompt"] = tinfo.get("prompt")
            t["modell"] = tinfo.get("modell") or (policy["modell"] or {}).get("erklaerungen")
            t["policy_version"] = policy["version"]
            t["wissen"] = tinfo.get("wissen", [])
            t["annahmen"] = tinfo.get("annahmen", [])
            t["zitate"] = sorted(set(re.findall(
                r"\[((?:SWS|RS|EXP|TR|FO|PRS|TPS)_[A-Za-z0-9_]+)\]", erg["html"])))
            t["quellen"] = sorted(set(t.get("quellen", []))
                                  | {w.get("quelle") for w in t["wissen"] if w.get("quelle")})
            for rel, dinfo in (tinfo.get("diagramme") or {}).items():
                t.setdefault("diagramme", {})[rel] = dinfo
            t.setdefault("laeufe", []).append({
                "datum": heute, "modell": t["modell"],
                "policy_version": policy["version"],
                "transkript": tinfo.get("transkript")})
            t["status"] = "aktuell"
            t.pop("invalidiert", None)
            t["elemente_stand"] = {e: record_hash(e) for e in t.get("elemente", [])}
            dump(tp, t)
            eingespielt += 1
        os.rename(outp, outp + ".eingespielt")
    print("eingespielt: %d Fragmente" % eingespielt)
    if eingespielt:
        schritte = ["python3 _src/generate.py --lang=alle", "python3 _src/validate.py",
                    "python3 _src/i18n_extract.py  (→ neue Segmente übersetzen)"]
        if diagramm_dabei:
            schritte.insert(0, "python3 _src/render_diagrams.py")
        print("Nächste Schritte:\n  " + "\n  ".join(schritte))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "status":
        cmd_status()
    elif cmd == "zeige" and rest:
        cmd_zeige(rest[0])
    elif cmd == "invalidiere" and rest:
        cmd_invalidiere(rest)
    elif cmd == "auftrag" and rest:
        cmd_auftrag(rest)
    elif cmd == "merge":
        cmd_merge()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
