#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spec_scrape.py — Spezifikations-Records aus AUTOSAR-Standard-PDFs gewinnen.

Zweck
-----
Die Spezifikations-DB unter ``_src/spec/records/`` wurde urspruenglich aus den
fertigen Seitenmodellen migriert (siehe ``migriere_spec_db.py``). Damit ist die
DB von der Darstellung abgeleitet, nicht von der Quelle. Dieses Werkzeug dreht
die Richtung um: es liest die normativen AUTOSAR-PDFs und vergleicht sie mit der
DB — oder baut sie neu auf.

Drei Phasen (einzeln oder verkettet aufrufbar):

  1. ``ids``      IDs (SWS_/RS_/PRS_/TPS_-Nummern) aus den PDFs einsammeln,
                  optional gefiltert nach Muster, Dokument oder Modul.
  2. ``props``    zu den IDs aus Phase 1 die Eigenschaften extrahieren
                  (Kind, Header, Scope, Symbol, Syntax, Beschreibung, ...).
  3. ``compare``  gegen die interne Spec-DB abgleichen. Standard ist ein reiner
                  Integritaetsbericht (``--check``); ``--rebuild`` schreibt.

  ``all``         Phase 1 + 2 + 3 in einem Lauf.
  ``crosscheck``  extrahiert denselben Cache getrennt mit pypdf und dem
                  eingebauten Backend, meldet jede Abweichung und prueft beide
                  Ergebnisse unabhaengig gegen die interne Spec-DB.
  ``urls``        druckt die Download-Zeilen fuer die run.sh (die MCP-Sandbox
                  hat keinen Netzzugriff, siehe README-Arbeitspraeferenz).

PDF-Cache und Workflow
----------------------
Die unveraenderten Quelldokumente liegen release-spezifisch unter
``_src/spec/pdf-cache/R25-11/``. ``manifest.sha256`` dokumentiert ihren
Inhalt. Eine run.sh laedt nur fehlende/ungueltige PDFs ueber eine temporaere
Datei und ersetzt niemals einen gueltigen Cache-Eintrag. Der Cache ist damit
zwischen Prueflaeufen wiederverwendbar; ein Release-Wechsel bekommt ein eigenes
Unterverzeichnis.

Extraktionsablauf: Cache aufbauen -> ``crosscheck`` ausfuehren -> zuerst
Backend-Abweichungen klaeren -> erst danach die je Backend gemeldeten
DB-Abweichungen bewerten. ``--rebuild`` ist absichtlich kein Bestandteil des
Quervergleichs; Schreiben erfolgt erst nach manueller Freigabe.

Abhaengigkeiten
---------------
Keine. Ist ``pypdf`` oder ``PyMuPDF`` installiert, wird es benutzt; sonst greift
ein eingebauter, minimaler PDF-Textextraktor (FlateDecode + Tj/TJ-Operatoren).
Der eingebaute Extraktor sortiert Seiten nach Objektnummer statt ueber den
Seitenbaum — fuer die zeilenweise Auswertung der Spec-Tabellen ausreichend.

Aufrufbeispiele (immer vom Repo-Wurzelverzeichnis)
--------------------------------------------------
    python3 _src/tools/spec_scrape.py urls --module log
    CACHE=_src/spec/pdf-cache/R25-11
    python3 _src/tools/spec_scrape.py ids       --pdf-dir "$CACHE" --module log
    python3 _src/tools/spec_scrape.py props     --pdf-dir "$CACHE" --id SWS_LOG_00261 --backend pypdf
    python3 _src/tools/spec_scrape.py crosscheck --pdf-dir "$CACHE" --json
    python3 _src/tools/spec_scrape.py all       --pdf-dir "$CACHE" --check
    python3 _src/tools/spec_scrape.py all       --pdf-dir "$CACHE" --rebuild

Exit-Code 1, wenn im Check-Modus Abweichungen gefunden wurden.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import zlib
from collections import OrderedDict, defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
ROOT = SRC.parent
RECORDS = SRC / "spec" / "records"
RELEASE = "R25-11"
# PDF-Cache: die normativen Standard-PDFs liegen versionsweise unter _src.
PDF_CACHE = SRC / "spec" / "pdf-cache" / RELEASE
BASE_URL = "https://www.autosar.org/fileadmin/standards/" + RELEASE

# ---------------------------------------------------------------------------
# Dokumentregister: Modul -> (Plattformzweig, PDF-Basisname, Record-Praefix)
# ---------------------------------------------------------------------------
DOCS = OrderedDict([
    ("core",   ("AP", "AUTOSAR_AP_SWS_Core",                        "SWS_CORE")),
    ("log",    ("AP", "AUTOSAR_AP_SWS_LogAndTrace",                 "SWS_LOG")),
    ("com",    ("AP", "AUTOSAR_AP_SWS_CommunicationManagement",     "SWS_CM")),
    ("exec",   ("AP", "AUTOSAR_AP_SWS_ExecutionManagement",         "SWS_EM")),
    ("diag",   ("AP", "AUTOSAR_AP_SWS_Diagnostics",                 "SWS_DM")),
    ("per",    ("AP", "AUTOSAR_AP_SWS_Persistency",                 "SWS_PER")),
    ("phm",    ("AP", "AUTOSAR_AP_SWS_PlatformHealthManagement",    "SWS_PHM")),
    ("sm",     ("AP", "AUTOSAR_AP_SWS_StateManagement",             "SWS_SM")),
    ("nm",     ("AP", "AUTOSAR_AP_SWS_NetworkManagement",           "SWS_ANM")),
    ("tsync",  ("AP", "AUTOSAR_AP_SWS_TimeSynchronization",         "SWS_TS")),
    ("crypto", ("AP", "AUTOSAR_AP_SWS_Cryptography",               "SWS_CRYPT")),
    ("idsm",   ("AP", "AUTOSAR_AP_SWS_IntrusionDetectionSystemManager", "SWS_AIDSM")),
    ("rds",    ("AP", "AUTOSAR_AP_SWS_RawDataStream",               "SWS_RDS")),
    ("ucm",    ("AP", "AUTOSAR_AP_SWS_UpdateAndConfigurationManagement", "SWS_UCM")),
    ("shwa",   ("AP", "AUTOSAR_AP_SWS_SafeHardwareAcceleration",    "AP_SWS")),
])

ID_RE = re.compile(r"\b(?:AP_)?(?:SWS|RS|PRS|TPS)_[A-Z][A-Z0-9]*_\d{4,5}\b")

# Beschriftungen der Eigenschaftstabellen in den SWS-Dokumenten.
LABELS = [
    "Kind", "Header file", "Forwarding header file", "Scope", "Symbol",
    "Underlying type", "Syntax", "Values", "Parameters (in)",
    "Parameters (inout)", "Parameters (out)", "Return value",
    "Exception Safety", "Thread Safety", "Description", "Notes",
    "Type", "Default value", "Errors",
]
LABEL_RE = re.compile(r"^(%s)\s*:?\s*(.*)$" % "|".join(re.escape(x) for x in LABELS))
UPSTREAM_RE = re.compile(r"Upstream requirements?:\s*(.+)")

# Deutsche th-Beschriftungen der DB -> kanonische PDF-Beschriftung.
DB_LABEL_MAP = {
    "header-datei": "Header file",
    "header file": "Header file",
    "weiterleitungs-header": "Forwarding header file",
    "forwarding header file": "Forwarding header file",
    "scope": "Scope",
    "geltungsbereich": "Scope",
    "symbol": "Symbol",
    "basistyp": "Underlying type",
    "underlying type": "Underlying type",
    "rückgabewert": "Return value",
    "return value": "Return value",
    "ausnahmesicherheit": "Exception Safety",
    "exception safety": "Exception Safety",
    "thread-sicherheit": "Thread Safety",
    "thread safety": "Thread Safety",
    "syntax": "Syntax",
}
# Diese Felder werden verglichen (Rest ist nur informativ).
COMPARED = ["Kind", "Header file", "Scope", "Symbol", "Underlying type"]


# ===========================================================================
# PDF-Textextraktion
# ===========================================================================
def _decode_pdf_string(raw: bytes) -> str:
    """PDF-Literalstring (…) bzw. Hexstring <…> -> Text."""
    if raw.startswith(b"<"):
        hexdigits = re.sub(rb"[^0-9A-Fa-f]", b"", raw[1:-1])
        if len(hexdigits) % 2:
            hexdigits += b"0"
        data = bytes.fromhex(hexdigits.decode("ascii"))
        if data[:2] in (b"\xfe\xff", b"\xff\xfe"):
            return data.decode("utf-16", "replace")
        return data.decode("latin-1", "replace")
    body, out, i = raw[1:-1], [], 0
    while i < len(body):
        ch = body[i : i + 1]
        if ch == b"\\" and i + 1 < len(body):
            nxt = body[i + 1 : i + 2]
            simple = {b"n": "\n", b"r": "\n", b"t": "\t", b"b": "", b"f": "",
                      b"(": "(", b")": ")", b"\\": "\\"}
            if nxt in simple:
                out.append(simple[nxt]); i += 2; continue
            if nxt.isdigit():
                oct_digits = b""
                j = i + 1
                while j < len(body) and len(oct_digits) < 3 and body[j : j + 1].isdigit():
                    oct_digits += body[j : j + 1]; j += 1
                out.append(chr(int(oct_digits, 8))); i = j; continue
            if nxt in (b"\n", b"\r"):
                i += 2; continue
            out.append(nxt.decode("latin-1", "replace")); i += 2; continue
        out.append(ch.decode("latin-1", "replace")); i += 1
    return "".join(out)


_OPS = re.compile(rb"""
    (?P<lit>\((?:\\.|[^\\()])*\))\s*(?:Tj|')
  | (?P<hex><[0-9A-Fa-f\s]*>)\s*Tj
  | (?P<arr>\[(?:\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>|[^\]()])*\])\s*TJ
  | (?P<brk>T\*|TD|Td|ET|BT)
""", re.S | re.X)
_ARR_ITEM = re.compile(rb"\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]*>|-?\d+(?:\.\d+)?")


def _content_to_text(content: bytes) -> str:
    """Content-Stream -> Text. Positionierungsoperatoren werden zu Zeilenumbruechen,
    grosse negative Kernwerte in TJ-Arrays zu Leerzeichen."""
    parts = []
    for m in _OPS.finditer(content):
        if m.group("brk"):
            parts.append("\n")
        elif m.group("lit") or m.group("hex"):
            parts.append(_decode_pdf_string(m.group("lit") or m.group("hex")))
        else:
            for item in _ARR_ITEM.finditer(m.group("arr")):
                tok = item.group(0)
                if tok[:1] in (b"(", b"<"):
                    parts.append(_decode_pdf_string(tok))
                else:
                    try:
                        if float(tok) <= -100:
                            parts.append(" ")
                    except ValueError:
                        pass
    return "".join(parts)


def _inflate(raw: bytes, body: bytes) -> bytes:
    """FlateDecode inkl. PNG-Predictor (/Predictor >= 10), sonst Rohdaten."""
    if b"/FlateDecode" not in body:
        return raw
    try:
        data = zlib.decompress(raw)
    except zlib.error:
        try:
            data = zlib.decompressobj().decompress(raw)
        except zlib.error:
            return b""
    m = re.search(rb"/Predictor\s+(\d+)", body)
    if not m or int(m.group(1)) < 10:
        return data
    cols = int((re.search(rb"/Columns\s+(\d+)", body) or [b"", b"1"])[1])
    colors = int((re.search(rb"/Colors\s+(\d+)", body) or [b"", b"1"])[1])
    bpc = int((re.search(rb"/BitsPerComponent\s+(\d+)", body) or [b"", b"8"])[1])
    bpp = max(1, colors * bpc // 8)
    rowlen = cols * colors * bpc // 8
    out, prev = bytearray(), bytearray(rowlen)
    pos = 0
    while pos + 1 + rowlen <= len(data):
        ft = data[pos]
        row = bytearray(data[pos + 1 : pos + 1 + rowlen])
        pos += 1 + rowlen
        for i in range(rowlen):
            a = row[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                row[i] = (row[i] + a) & 0xFF
            elif ft == 2:
                row[i] = (row[i] + b) & 0xFF
            elif ft == 3:
                row[i] = (row[i] + (a + b) // 2) & 0xFF
            elif ft == 4:
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        out += row
        prev = row
    return bytes(out)


def _collect_objects(data: bytes) -> dict:
    """Alle Objekte einsammeln — klassisch und aus Objektstroemen (/ObjStm).

    Moderne PDFs (auch die AUTOSAR-Dokumente) legen die meisten Objekte in
    komprimierten Objektstroemen ab; ohne deren Aufloesung findet man keine
    einzige Seite.
    """
    bodies, streams = {}, {}
    for m in re.finditer(rb"(\d+)\s+\d+\s+obj(.*?)endobj", data, re.S):
        num, body = int(m.group(1)), m.group(2)
        bodies[num] = body
        sm = re.search(rb"stream\r?\n(.*?)\r?\n?endstream", body, re.S)
        if sm:
            streams[num] = _inflate(sm.group(1), body)
    for num, body in list(bodies.items()):
        if not re.search(rb"/Type\s*/ObjStm", body) or num not in streams:
            continue
        payload = streams[num]
        n = int((re.search(rb"/N\s+(\d+)", body) or [b"", b"0"])[1])
        first = int((re.search(rb"/First\s+(\d+)", body) or [b"", b"0"])[1])
        header = payload[:first].split()
        for i in range(min(n, len(header) // 2)):
            onum, off = int(header[2 * i]), int(header[2 * i + 1])
            ende = (int(header[2 * i + 3]) + first) if 2 * i + 3 < len(header) else len(payload)
            bodies.setdefault(onum, payload[first + off : ende])
    return bodies, streams


def _builtin_pdf_pages(path: Path) -> list:
    """Minimalparser ohne Fremdbibliothek.

    Seiten werden ueber den Seitenbaum (/Type /Pages -> /Kids) geordnet, damit
    die Reihenfolge der Dokumentreihenfolge entspricht; nur falls kein Baum
    auffindbar ist, greift die Objektnummern-Reihenfolge.
    """
    data = path.read_bytes()
    bodies, streams = _collect_objects(data)
    seiten = [n for n, b in bodies.items() if re.search(rb"/Type\s*/Page[^s]", b + b" ")]

    reihenfolge, gesehen = [], set()

    def kids_of(num, tiefe=0):
        if tiefe > 64 or num in gesehen:
            return
        gesehen.add(num)
        body = bodies.get(num, b"")
        if re.search(rb"/Type\s*/Page[^s]", body + b" "):
            reihenfolge.append(num)
            return
        km = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
        if km:
            for kid in re.findall(rb"(\d+)\s+\d+\s+R", km.group(1)):
                kids_of(int(kid), tiefe + 1)

    wurzeln = [n for n, b in bodies.items()
               if re.search(rb"/Type\s*/Pages", b) and b"/Parent" not in b]
    for w in wurzeln:
        kids_of(w)
    if not reihenfolge:
        reihenfolge = sorted(seiten)

    ergebnis = []
    for num in reihenfolge:
        body = bodies.get(num, b"")
        refs = [int(r) for r in re.findall(rb"/Contents\s+(\d+)\s+\d+\s+R", body)]
        arr = re.search(rb"/Contents\s*\[(.*?)\]", body, re.S)
        if arr:
            refs += [int(r) for r in re.findall(rb"(\d+)\s+\d+\s+R", arr.group(1))]
        ergebnis.append("".join(_content_to_text(streams[r]) for r in refs if r in streams))
    return ergebnis


BACKENDS = ("pypdf", "mupdf", "builtin")


def _pypdf_pages(path: Path) -> list:
    from pypdf import PdfReader  # type: ignore
    return [(page.extract_text() or "") for page in PdfReader(str(path)).pages]


def _mupdf_pages(path: Path) -> list:
    import fitz  # type: ignore
    with fitz.open(str(path)) as doc:
        return [page.get_text() for page in doc]


_BACKEND_FN = {"pypdf": _pypdf_pages, "mupdf": _mupdf_pages,
               "builtin": _builtin_pdf_pages}
_BACKEND_MODUL = {"pypdf": "pypdf", "mupdf": "fitz"}


def available_backends() -> list:
    """Backends, die auf diesem Rechner benutzbar sind (builtin immer)."""
    ok = []
    for name in BACKENDS:
        if name == "builtin" or importlib.util.find_spec(_BACKEND_MODUL[name]):
            ok.append(name)
    return ok


def pdf_pages(path: Path, backend: str = "auto") -> list:
    """Seitentexte eines PDFs.

    ``auto`` nimmt den erstbesten verfuegbaren Backend. Ein ausdruecklich
    genannter Backend wird **nicht** stillschweigend durch einen anderen
    ersetzt — sonst waere der Quervergleich wertlos.

    Die Backends liefern unterschiedlich strukturierten Text (pypdf haengt
    Tabellenzellen ohne Trenner aneinander, der eingebaute Extraktor setzt
    Umbrueche an den Positionierungsoperatoren). Das gleicht
    ``normalize_layout`` aus; deshalb duerfen die Ergebnisse verglichen werden.
    """
    if backend != "auto":
        if backend not in _BACKEND_FN:
            raise SystemExit("unbekannter Backend: %s" % backend)
        return _BACKEND_FN[backend](path)
    for name in available_backends():
        try:
            return _BACKEND_FN[name](path)
        except Exception:
            continue
    return _builtin_pdf_pages(path)


# ===========================================================================
# Phase 1 — IDs einsammeln
# ===========================================================================
def discover_pdfs(pdf_dir: Path, modules=None, docs=None) -> list:
    wanted_names = None
    if modules or docs:
        wanted_names = set()
        for mod in modules or ():
            if mod not in DOCS:
                raise SystemExit("unbekanntes Modul: %s (bekannt: %s)"
                                 % (mod, ", ".join(DOCS)))
            wanted_names.add(DOCS[mod][1])
        for doc in docs or ():
            wanted_names.add(Path(doc).stem)
    found = []
    for path in sorted(pdf_dir.rglob("*.pdf")):
        if wanted_names is None or path.stem in wanted_names:
            found.append(path)
    return found


def phase_ids(pdfs, pattern=None, only_ids=None, include_refs=False,
              backend="auto") -> dict:
    """-> {pdf-name: {id: [seitenzahlen]}}"""
    rx = re.compile(pattern) if pattern else None
    keep = set(only_ids or ())
    result = OrderedDict()
    for path in pdfs:
        pages = [strip_noise(x) for x in pdf_pages(path, backend)]
        hits = defaultdict(list)
        for pageno, text in enumerate(pages, 1):
            definiert = set(DEF_RE.findall(text))
            for rid in ID_RE.findall(text):
                if rx and not rx.search(rid):
                    continue
                if keep and rid not in keep:
                    continue
                if not include_refs and rid not in definiert:
                    continue          # blosse Referenz (z. B. Upstream-Angabe)
                if pageno not in hits[rid]:
                    hits[rid].append(pageno)
        result[path.name] = {"path": str(path), "pages": len(pages),
                            "ids": {k: v for k, v in sorted(hits.items())}}
    return result


# ===========================================================================
# Phase 2 — Eigenschaften je ID
# ===========================================================================
DEF_RE = re.compile(r"\[((?:AP_)?(?:SWS|RS|PRS|TPS)_[A-Z][A-Z0-9]*_\d{4,5})\]")


def _record_slice(text: str, rid: str) -> str:
    """Textausschnitt ab der ID-Definition bis zum Beginn des naechsten Records.

    Grenze ist entweder das Spec-Item-Ende (⌋) oder die naechste in eckigen
    Klammern stehende ID — sonst laufen die Eigenschaften des Folgerecords in
    den aktuellen hinein.
    """
    m = DEF_RE.search(text, 0) and re.search(r"\[%s\]" % re.escape(rid), text)
    if not m:
        m = re.search(re.escape(rid), text)
        if not m:
            return ""
    rest = text[m.end():]
    grenzen = []
    ende = rest.find("⌋")
    if ende >= 0:
        grenzen.append(ende)
    nxt = DEF_RE.search(rest)
    if nxt:
        grenzen.append(nxt.start())
    return rest[:min(grenzen)] if grenzen else rest[:6000]


# Umbruch vor jeder Beschriftung — bewusst OHNE \b, weil pypdf die Zellen ohne
# Trenner aneinanderhaengt ("ara::logSymbol: LogLevel"); dort steht zwischen
# Wortende und Beschriftung keine Wortgrenze.
NORM_RE = re.compile(r"(?<!^)(?=(?:%s)\s*:)" % "|".join(re.escape(x) for x in
                     LABELS + ["Upstream requirements", "Upstream requirement"]))


# pypdf trennt Ligaturen ("T race"), der eingebaute Extraktor nicht — deshalb
# tolerieren die Muster eingestreute Leerzeichen.
def _lose(wort: str) -> str:
    return r"\s*".join(re.escape(c) for c in wort)


NOISE_RES = [
    # Vollstaendige Fusszeile: Titel (ggf. mit Ligaturrest) + Release + Seite.
    re.compile(r"Specification\s+of\s+[A-Za-z]+(?:\s+[A-Za-z]{1,12}){0,6}?"
               r"\s*AUTOSAR\s*AP\s*R\d\d\s*-?\s*\d*", re.I),
    re.compile(r"AUTOSAR\s*AP\s*R\d\d\s*-?\s*\d*", re.I),
    re.compile(r"Specification\s+of\s+[A-Za-z]+(?:\s+[A-Za-z]{1,12}){0,6}", re.I),
    re.compile(r"Document\s*ID\s*\d+\s*:\s*\S+", re.I),
    re.compile(r"\d+\s+of\s+\d+"),
    re.compile(_lose("AUTOSARCONFIDENTIAL"), re.I),
    re.compile(r"[\u25b3\u25bd\u25b2\u25bc]"),
]

# Reste am Ende eines Zellwerts: Seitenzahl, Dokumentnummer, Trennzeichen.
# Eine Seitenzahl darf nur als eigenstaendiges Token entfernt werden. Die alte
# Variante entfernte beliebige Endziffern und kuerzte dadurch gueltige Namen wie
# ``namespace ara::crypto::x509`` zu ``namespace ara::crypto::x``.
TAIL_RE = re.compile(
    r"(?:\s|\u2014|\u2013|(?<![A-Za-z0-9_])\d{1,4}|of|"
    r"Document\s*ID\s*\d*:?|[.,;:])+$"
)


LIGATUR_RE = re.compile(r"\b((?:AP_)?(?:SWS|RS|PRS|TPS))_([A-Z][A-Z0-9]*(?:\s[A-Z0-9]+)*)_(\d{4,5})\b")


def fix_ligatures(text: str) -> str:
    """Von pypdf zerrissene Bezeichner wieder zusammenfuegen.

    pypdf trennt Ligaturen ("RS_L T_00003", "Log and T race"). Innerhalb von
    Spec-IDs ist ein Leerzeichen nie gueltig, daher kann es dort gefahrlos
    entfernt werden.
    """
    text = LIGATUR_RE.sub(lambda m: "%s_%s_%s" % (m.group(1),
                                                  m.group(2).replace(" ", ""),
                                                  m.group(3)), text or "")
    # "T race" -> "Trace", "T emplate" -> "Template": Grossbuchstabe, Leerzeichen,
    # Kleinbuchstabenrest. Nur bei bekannten Woertern, um echte Wortgrenzen
    # nicht zu zerstoeren.
    return re.sub(r"\b([A-Z]) (race|emplate|ype|ime|hread|able)\b",
                  lambda m: m.group(1) + m.group(2), text)


def strip_noise(text: str) -> str:
    """Seitenkopf und -fuss entfernen.

    Die Eigenschaftstabellen laufen ueber Seitengrenzen; ohne diese Bereinigung
    landet die Fusszeile mitten im Zellwert ("std::uint8_t ▽ 52 of 122 Document
    ID 853: ...").
    """
    text = fix_ligatures(text)
    for _ in range(2):            # Titel kann durch Umbruch zweigeteilt sein
        for rx in NOISE_RES:
            text = rx.sub(" ", text)
        text = fix_ligatures(text)
    # Alleinstehende Ligaturreste einer bereits entfernten Fusszeile.
    text = re.sub(r"(?m)^[ \t]*(race|emplate|ime|hread|able|ype)[ \t]*$", " ", text)
    return text


def _clean_value(value: str) -> str:
    """Zellwert von Seitenzahl-/Fusszeilenresten befreien."""
    value = strip_noise(value).strip()
    value = re.sub(r"\s{2,}", " ", value)
    value = re.sub(r"\s+(race|emplate|ime|hread|able|ype)\s*$", "", value)
    return TAIL_RE.sub("", value).strip()


def normalize_layout(text: str) -> str:
    """Zeilenstruktur erzwingen.

    Je nach Backend (pypdf, PyMuPDF, eingebauter Extraktor) kommen die
    Tabellenzellen mit, ohne oder mit falsch gesetzten Zeilenumbruechen an.
    Deshalb wird vor jeder bekannten Beschriftung und vor jeder in eckigen
    Klammern stehenden ID hart umbrochen — danach ist die Auswertung
    backend-unabhaengig.
    """
    text = re.sub(r"[ \t]+", " ", strip_noise(text))
    text = DEF_RE.sub(lambda m: "\n[%s]\n" % m.group(1), text)
    return NORM_RE.sub("\n", text)


def parse_record(text: str, rid: str) -> dict:
    """Eigenschaften eines Spec-Records aus dem PDF-Text."""
    chunk = _record_slice(normalize_layout(text), rid)
    rec = {"id": rid, "props": OrderedDict(), "upstream": [], "heading": None}
    if not chunk:
        return rec
    for ups in UPSTREAM_RE.finditer(chunk):
        for uid in ID_RE.findall(ups.group(1).split("\n")[0]):
            if uid not in rec["upstream"]:
                rec["upstream"].append(uid)
    head = chunk.lstrip("\n").split("\n", 1)[0].strip()
    head = re.split(r"\s*(?:Upstream requirements?|Kind)\s*:", head)[0].strip()
    if head and not LABEL_RE.match(head):
        rec["heading"] = head[:120]
    current, buf = None, []
    for line in chunk.split("\n"):
        line = line.strip()
        if not line:
            continue
        m = LABEL_RE.match(line)
        if m:
            if current:
                rec["props"][current] = _clean_value(" ".join(buf))
            current, buf = m.group(1), ([m.group(2).strip()] if m.group(2).strip() else [])
        elif current:
            buf.append(line)
    if current:
        rec["props"][current] = _clean_value(" ".join(buf))
    ns, enclosing = namespace_from_scope(rec["props"].get("Scope", ""))
    rec["namespace"], rec["enclosing"] = ns, enclosing
    return rec


def namespace_from_scope(scope: str):
    """'namespace ara::log' -> ('ara::log', None);
    'class ara::log::LogStream' -> ('ara::log', 'ara::log::LogStream')."""
    s = re.sub(r"^(namespace|class|struct|enum(?:\s+class)?|union)\s+", "",
               (scope or "").strip()).strip()
    while re.search(r"<[^<>]*>", s):          # verschachtelte Template-Argumente
        s = re.sub(r"<[^<>]*>", "", s)
    s = s.strip()
    if not s:
        return None, None
    parts = [p for p in (seg.strip() for seg in s.split("::")) if p]
    if not parts or parts[0] not in ("ara", "apext", "std"):
        return None, None
    if (scope or "").strip().startswith("namespace"):
        return "::".join(parts), None
    ns = [p for p in parts if p[:1].islower() or p[:1] == "_"]
    types = parts[len(ns):]
    if not ns:
        return None, None
    return "::".join(ns), ("::".join(parts) if types else None)


def phase_props(index: dict, only_ids=None, backend="auto") -> dict:
    keep = set(only_ids or ())
    out = OrderedDict()
    for name, info in index.items():
        pages = [strip_noise(x) for x in pdf_pages(Path(info["path"]), backend)]
        for rid, pagenos in info["ids"].items():
            if keep and rid not in keep:
                continue
            best = None
            for pageno in pagenos:
                joined = "\n".join(pages[pageno - 1 : pageno + 1])  # Seitenumbruch mitnehmen
                rec = parse_record(joined, rid)
                if rec["props"] or rec["upstream"]:
                    best = rec
                    break
            rec = best or {"id": rid, "props": {}, "upstream": [], "heading": None,
                          "namespace": None, "enclosing": None}
            rec["document"] = name
            rec["page"] = pagenos[0] if pagenos else None
            out[rid] = rec
    return out


# ===========================================================================
# Phase 3 — Abgleich mit der internen Spec-DB
# ===========================================================================
def _strip_html(value: str) -> str:
    import html as _html
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", value or ""))).strip()


def load_db(prefixes=None) -> dict:
    """Spec-DB einlesen -> {id: {'path','kind','props','ns'}}."""
    db = {}
    if not RECORDS.is_dir():
        return db
    for path in sorted(RECORDS.rglob("*.json")):
        if prefixes and not any(path.parent.name == p for p in prefixes):
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        props, kind = OrderedDict(), None
        for block in rec.get("blocks", []):
            if block.get("t") == "props":
                for row in block.get("rows", []):
                    label = DB_LABEL_MAP.get(_strip_html(row.get("th", "")).lower().rstrip(":"))
                    if label:
                        props.setdefault(label, _strip_html(row.get("td", "")))
            if block.get("t") == "html" and "recname" in (block.get("html") or ""):
                m = re.search(r'<span class="kind">(.*?)</span>', block["html"], re.S)
                if m:
                    kind = _strip_html(m.group(1))
        db[rec.get("id") or path.stem] = {
            "path": path, "kind": kind, "props": props, "ns": rec.get("ns") or {},
        }
    return db


def _norm(value: str) -> str:
    v = re.sub(r"\s+", " ", (value or "")).strip().rstrip(".").lower()
    return re.sub(r'^#include\s*["<]|[">]$', "", v).strip()


def phase_compare(scraped: dict, prefixes=None, rebuild=False, vollstaendig=True) -> dict:
    db = load_db(prefixes)
    report = {"checked": 0, "only_in_pdf": [], "only_in_db": [], "diffs": [],
              "namespace_diffs": [], "enclosing_diffs": [],
              "namespace_legacy_schema": [], "empty_extraction": [], "written": []}
    for rid, rec in scraped.items():
        if not rec["props"]:
            report["empty_extraction"].append(rid)
        if rid not in db:
            report["only_in_pdf"].append(rid)
            continue
        report["checked"] += 1
        entry = db[rid]
        for label in COMPARED:
            pdf_val = rec["props"].get(label)
            db_val = entry["kind"] if label == "Kind" else entry["props"].get(label)
            if pdf_val and db_val and _norm(pdf_val) != _norm(db_val):
                report["diffs"].append({"id": rid, "field": label,
                                        "pdf": pdf_val[:120], "db": db_val[:120]})
            elif pdf_val and not db_val:
                report["diffs"].append({"id": rid, "field": label,
                                        "pdf": pdf_val[:120], "db": None})
        # Namespace und umschliessender Typ sind zwei verschiedene Fakten und
        # werden getrennt verglichen. Wo die DB noch dem Altschema folgt und
        # den umschliessenden Typ im Feld ``namespace`` fuehrt, ist das kein
        # Datenfehler des Inhalts, sondern ein Schemarest: eigener Topf,
        # damit nichts still verschwindet (siehe SPEC_BUILD_PROCESS.md).
        pdf_ns, pdf_enc = rec.get("namespace"), rec.get("enclosing")
        db_ns, db_enc = entry["ns"].get("namespace"), entry["ns"].get("enclosing")
        if pdf_ns and db_ns and _norm(pdf_ns) != _norm(db_ns):
            if db_enc is None and pdf_enc and _norm(db_ns) == _norm(pdf_enc):
                report["namespace_legacy_schema"].append(
                    {"id": rid, "namespace": pdf_ns, "enclosing": pdf_enc,
                     "db": db_ns, "rule": "enclosing-in-namespace"})
            elif db_enc is None and pdf_enc and _norm(pdf_enc).startswith(_norm(db_ns) + "::"):
                report["namespace_legacy_schema"].append(
                    {"id": rid, "namespace": pdf_ns, "enclosing": pdf_enc,
                     "db": db_ns, "rule": "enclosing-prefix-in-namespace"})
            else:
                report["namespace_diffs"].append({"id": rid, "pdf": pdf_ns, "db": db_ns})
        if pdf_enc and db_enc and _norm(pdf_enc) != _norm(db_enc):
            report["enclosing_diffs"].append({"id": rid, "pdf": pdf_enc, "db": db_enc})
    # "nur in der DB" ist ausschliesslich bei einem vollstaendigen Dokumentlauf
    # eine echte Aussage — bei --id/--limit/--pattern waere die Liste blosses
    # Rauschen (alles, was der Teillauf nicht angefasst hat).
    if vollstaendig and scraped:
        report["only_in_db"] = sorted(set(db) - set(scraped))
    else:
        report["only_in_db_unterdrueckt"] = True
    if rebuild:
        report["written"] = _rebuild(scraped, db)
    return report


def _rebuild(scraped: dict, db: dict) -> list:
    """Autoritative PDF-Felder in die DB zurueckschreiben.

    Konservativ: nur der ``ns``-Block und ein ``quelle``-Vermerk werden
    aktualisiert bzw. ergaenzt. Darstellungsbloecke (HTML, KI-Fragmente,
    Property-Zeilen) bleiben unberuehrt — sie werden vom Generator gebraucht.
    """
    written = []
    for rid, rec in scraped.items():
        entry = db.get(rid)
        if not entry or not rec.get("namespace"):
            continue
        data = json.loads(entry["path"].read_text(encoding="utf-8"))
        ns = dict(data.get("ns") or {})
        before = dict(ns)
        ns["namespace"] = rec["namespace"]
        if rec.get("enclosing"):
            ns["enclosing"] = rec["enclosing"]
        ns.setdefault("modul", entry["ns"].get("modul"))
        ns["quelle"] = "pdf"
        if rec.get("enclosing"):
            ns["umschliessend"] = rec["enclosing"]
        if ns == before:
            continue
        data["ns"] = ns
        entry["path"].write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
        written.append(rid)
    return written


# ===========================================================================
# Quervergleich der Extraktions-Backends
# ===========================================================================
def compare_backend_results(results: dict) -> list:
    """Feldgenauer Vergleich: IDs, Metadaten, Upstream und alle PDF-Properties."""
    names = list(results)
    if len(names) < 2:
        return []
    left, right = names[0], names[1]
    a, b = results[left], results[right]
    deviations = []
    for rid in sorted(set(a) | set(b)):
        if rid not in a or rid not in b:
            deviations.append({"id": rid, "field": "record",
                               left: "present" if rid in a else "missing",
                               right: "present" if rid in b else "missing"})
            continue
        fields = {"heading", "namespace", "enclosing", "document", "page"}
        for field in sorted(fields):
            av, bv = a[rid].get(field), b[rid].get(field)
            if _norm(str(av or "")) != _norm(str(bv or "")):
                deviations.append({"id": rid, "field": field, left: av, right: bv})
        au, bu = sorted(a[rid].get("upstream") or []), sorted(b[rid].get("upstream") or [])
        if au != bu:
            deviations.append({"id": rid, "field": "upstream", left: au, right: bu})
        for field in sorted(set(a[rid].get("props", {})) | set(b[rid].get("props", {}))):
            av = a[rid].get("props", {}).get(field)
            bv = b[rid].get("props", {}).get(field)
            if _norm(str(av or "")) != _norm(str(bv or "")):
                deviations.append({"id": rid, "field": "props." + field,
                                   left: av, right: bv})
    return deviations


def phase_crosscheck(pdfs, pattern=None, only_ids=None, include_refs=False,
                     backends=("pypdf", "builtin"), prefixes=None,
                     limit=None) -> dict:
    missing = [x for x in backends if x not in available_backends()]
    if missing:
        raise SystemExit("Backend nicht verfuegbar: %s" % ", ".join(missing))
    results, indexes = OrderedDict(), OrderedDict()
    for backend in backends:
        idx = phase_ids(pdfs, pattern, only_ids, include_refs, backend)
        if limit:
            for info in idx.values():
                info["ids"] = dict(list(info["ids"].items())[:limit])
        indexes[backend] = idx
        results[backend] = phase_props(idx, only_ids, backend)
    complete = not (only_ids or limit or pattern)
    db_reports = {name: phase_compare(records, prefixes, rebuild=False,
                                      vollstaendig=complete)
                  for name, records in results.items()}
    return {"release": RELEASE, "backends": list(backends),
            "documents": [p.name for p in pdfs],
            "record_counts": {k: len(v) for k, v in results.items()},
            "backend_deviations": compare_backend_results(results),
            "database": db_reports}


# ===========================================================================
# urls — Downloadzeilen fuer die run.sh
# ===========================================================================
def phase_urls(modules=None, out_dir="output/pdf") -> str:
    mods = list(modules) if modules else list(DOCS)
    lines = ["#!/bin/zsh", "set -euo pipefail", 'cd "${0:A:h}"',
             "mkdir -p %s" % out_dir, ""]
    for mod in mods:
        branch, stem, _ = DOCS[mod]
        lines.append('curl -fL --retry 3 -o "%s/%s.pdf" \\\n  "%s/%s/%s.pdf"'
                     % (out_dir, stem, BASE_URL, branch, stem))
    lines += ["", "python3 _src/tools/spec_scrape.py all --pdf-dir %s --check" % out_dir, ""]
    return "\n".join(lines)


# ===========================================================================
# CLI
# ===========================================================================
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("phase", choices=["ids", "props", "compare", "all", "crosscheck", "urls"])
    ap.add_argument("--pdf-dir", type=Path, default=PDF_CACHE)
    ap.add_argument("--module", action="append", help="Modulkuerzel, z. B. log (mehrfach)")
    ap.add_argument("--doc", action="append", help="PDF-Basisname (mehrfach)")
    ap.add_argument("--id", action="append", help="nur diese ID(s)")
    ap.add_argument("--pattern", help="Regex-Filter fuer IDs, z. B. '^SWS_LOG_'")
    ap.add_argument("--include-refs", action="store_true",
                    help="auch blosse ID-Referenzen aufnehmen, nicht nur Definitionen")
    ap.add_argument("--check", action="store_true", help="nur pruefen (Standard)")
    ap.add_argument("--rebuild", action="store_true", help="DB schreiben")
    ap.add_argument("--json", action="store_true", help="Rohdaten als JSON ausgeben")
    ap.add_argument("--limit", type=int, help="nur die ersten N IDs (Phase 2/3)")
    ap.add_argument("--backend", choices=["auto", "pypdf", "mupdf", "builtin"],
                    default="auto", help="Extraktions-Backend (Standard: auto)")
    ap.add_argument("--cross-backend", action="append",
                    choices=["pypdf", "mupdf", "builtin"],
                    help="Backends fuer crosscheck (Standard: pypdf + builtin)")
    args = ap.parse_args(argv)

    if args.phase == "urls":
        print(phase_urls(args.module))
        return 0

    if not args.pdf_dir.is_dir():
        print("PDF-Verzeichnis fehlt: %s" % args.pdf_dir, file=sys.stderr)
        print("Tipp: 'urls'-Phase erzeugt die Download-Zeilen fuer die run.sh "
              "(die Sandbox hat keinen Netzzugriff).", file=sys.stderr)
        return 2
    pdfs = discover_pdfs(args.pdf_dir, args.module, args.doc)
    if not pdfs:
        print("keine passenden PDFs in %s" % args.pdf_dir, file=sys.stderr)
        return 2

    prefixes = {DOCS[m][2] for m in (args.module or [])} or None
    if args.phase == "crosscheck":
        report = phase_crosscheck(pdfs, args.pattern, args.id, args.include_refs,
                                  tuple(args.cross_backend or ("pypdf", "builtin")),
                                  prefixes, args.limit)
        print(json.dumps(report, ensure_ascii=False, indent=1))
        db_bad = any(r["diffs"] or r["namespace_diffs"] or r["only_in_pdf"]
                     for r in report["database"].values())
        return 1 if report["backend_deviations"] or db_bad else 0

    index = phase_ids(pdfs, args.pattern, args.id, args.include_refs, args.backend)
    if args.phase == "ids":
        if args.json:
            print(json.dumps(index, ensure_ascii=False, indent=1))
        else:
            for name, info in index.items():
                print("%s — %d Seiten, %d IDs" % (name, info["pages"], len(info["ids"])))
                for rid, pages in list(info["ids"].items())[: args.limit or 20]:
                    print("   %-18s Seite %s" % (rid, ", ".join(map(str, pages[:4]))))
        return 0

    if args.limit:
        for info in index.values():
            info["ids"] = dict(list(info["ids"].items())[: args.limit])
    scraped = phase_props(index, args.id, args.backend)
    if args.phase == "props":
        if args.json:
            print(json.dumps(scraped, ensure_ascii=False, indent=1))
        else:
            for rid, rec in scraped.items():
                print("\n%s  (%s, Seite %s)" % (rid, rec["document"], rec["page"]))
                if rec.get("heading"):
                    print("   Titel      : %s" % rec["heading"])
                if rec.get("upstream"):
                    print("   Upstream   : %s" % ", ".join(rec["upstream"]))
                if rec.get("namespace"):
                    print("   Namensraum : %s%s" % (rec["namespace"],
                          "  (in %s)" % rec["enclosing"] if rec.get("enclosing") else ""))
                for label, value in rec["props"].items():
                    print("   %-11s: %s" % (label, value[:100]))
        return 0

    vollstaendig = not (args.id or args.limit or args.pattern)
    report = phase_compare(scraped, prefixes,
                           rebuild=args.rebuild and not args.check,
                           vollstaendig=vollstaendig)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 1 if (report["diffs"] or report["namespace_diffs"] or report["only_in_pdf"]) else 0
    print("verglichen: %d Records" % report["checked"])
    for key, title in (("only_in_pdf", "nur im PDF (fehlen in der DB)"),
                       ("only_in_db", "nur in der DB (im PDF nicht gefunden)"),
                       ("empty_extraction", "ohne extrahierbare Eigenschaften")):
        items = report[key]
        if items:
            print("%s (%d): %s%s" % (title, len(items), ", ".join(items[:8]),
                                     " …" if len(items) > 8 else ""))
    for diff in report["diffs"][:20]:
        print("  ABWEICHUNG %s %s: PDF=%r DB=%r"
              % (diff["id"], diff["field"], diff["pdf"], diff["db"]))
    for diff in report["namespace_diffs"][:20]:
        print("  NAMENSRAUM %s: PDF=%s DB=%s" % (diff["id"], diff["pdf"], diff["db"]))
    if report["written"]:
        print("geschrieben: %d Records" % len(report["written"]))
    problems = report["diffs"] or report["namespace_diffs"] or report["only_in_pdf"]
    print("OK — DB deckt sich mit den PDFs." if not problems else "PROBLEME gefunden.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
