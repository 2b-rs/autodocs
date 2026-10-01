"""Reparatur von PDF-Extraktionsartefakten mit belegter Herkunft.

Jede Aenderung am normativen Text ist eine versionierte Regel und wird als
Eintrag in ``repairs`` protokolliert. Der Rohtext bleibt immer erhalten.
Nicht beweisbare Faelle werden nicht geraten, sondern als ``suspects``
gemeldet und fuehren zu einem Review-Flag.
"""

import re

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
HYPHEN_RE = re.compile(r"([A-Za-z]{2,})-\s+([a-z]{2,})")
SPLIT_RE = re.compile(r"\b([A-Za-z])\s+([a-z]+)\b")
CAMEL_RE = re.compile(r"[a-z][A-Z]")

SAFE_SINGLE = {"a", "i"}

RULES = {
    "dehyphenate": "dehyphenate@v1",
    "ligature": "ligature_split@v2",
}


def build_lexicon(pages):
    """Dokumenteigenes Lexikon: Wort -> Haeufigkeit (kleingeschrieben).

    Der Guard stammt bewusst aus dem PDF selbst und nicht aus einem externen
    Woerterbuch. Nur so ist eine Reparatur durch das Dokument belegt.
    """
    lex = {}
    for page in pages or ():
        for m in WORD_RE.finditer(page or ""):
            tok = m.group(0)
            key = tok.lower()
            lex[key] = lex.get(key, 0) + 1
            if CAMEL_RE.search(tok):
                # CamelCase-Bezeichner zusaetzlich original vorhalten, damit
                # sie als bekannte Namen und nicht als Artefakt gelten.
                lex.setdefault(tok, 0)
                lex[tok] += 1
    return lex


def _known(lex, word, min_count=1):
    return lex.get((word or "").lower(), 0) >= min_count


def dehyphenate(text, lex, repairs):
    """``sys- tem`` -> ``system``, aber nur bei belegter ungetrennter Form."""
    def sub(m):
        joined = m.group(1) + m.group(2)
        if _known(lex, joined, 2):
            repairs.append({"rule": RULES["dehyphenate"],
                            "from": m.group(0), "to": joined})
            return joined
        return m.group(0)
    return HYPHEN_RE.sub(sub, text or "")


def rejoin_splits(text, lex, repairs):
    """``T o`` -> ``To``: ersetzt die handgepflegte Endungsliste."""
    def sub(m):
        head, tail = m.group(1), m.group(2)
        if head.lower() in SAFE_SINGLE:
            return m.group(0)
        joined = head + tail
        if _known(lex, joined, 3) and not _known(lex, tail, 3):
            repairs.append({"rule": RULES["ligature"],
                            "from": m.group(0), "to": joined})
            return joined
        return m.group(0)
    return SPLIT_RE.sub(sub, text or "")


def detect_missing_spaces(text, identifiers=()):
    """Fehlende Leerzeichen erkennen, aber niemals automatisch korrigieren.

    ``LogStream`` ist ein gueltiger Bezeichner, ``aLog`` ein Artefakt. Ohne
    Beleg aus der Record-DB wird deshalb nur gemeldet.
    """
    known = {str(i).lower() for i in identifiers or ()}
    out = []
    for m in WORD_RE.finditer(text or ""):
        tok = m.group(0)
        if not CAMEL_RE.search(tok) or tok.lower() in known:
            continue
        out.append(tok)
    return sorted(set(out))


def repair_text(raw, lexicon=None, identifiers=()):
    """Rohtext reparieren und dabei vollstaendig protokollieren."""
    repairs = []
    lex = lexicon or {}
    text = dehyphenate(raw or "", lex, repairs)
    text = rejoin_splits(text, lex, repairs)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return {
        "text_en": text,
        "text_raw": raw,
        "repairs": repairs,
        "suspects": detect_missing_spaces(text, identifiers),
    }


def assess(entry, agreement=None):
    """Confidence und Review-Status aus Evidenzlage ableiten.

    ``agreement`` ist True/False bei Backend-Kreuzvergleich, sonst None.
    """
    if entry.get("suspects"):
        return "medium", "pending", "missing_space_suspects"
    if agreement is False:
        return "medium", "pending", "backend_mismatch"
    if agreement is True:
        return "high", "accepted", "backend_agreement"
    return "medium", "pending", "single_backend"
