"""Flag-Dateien fuer KI-Review-Jobs mit kollisionsfreier Uebernahme.

Ein Flag entsteht ausschliesslich aus dem Extraktionsprozess und traegt die
Agentenanweisung mit, damit Anweisung und Befund nicht auseinanderlaufen.
Die Uebernahme erfolgt per ``os.rename`` und ist damit atomar: Bei parallelen
Subagenten gewinnt genau einer, alle anderen laufen in ``FileNotFoundError``.
"""

import json
import os
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path

QUEUE = Path(__file__).resolve().parents[1] / "spec" / "review-queue"
OPEN_DIR = QUEUE / "open"
CLAIMED_DIR = QUEUE / "claimed"
DONE_DIR = QUEUE / "done"

SCHEMA = "review-flag@v1"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_dirs():
    for d in (OPEN_DIR, CLAIMED_DIR, DONE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _atomic_write(path, payload):
    tmp = path.with_suffix(path.suffix + ".tmp-%s" % uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def build_instruction(rid, reason, entry, record_path):
    """Agentenanweisung deterministisch aus dem Prozessbefund erzeugen."""
    steps = [
        "Oeffne %s und vergleiche requirement_text.text_raw mit text_en." % record_path,
        "Pruefe jeden Eintrag in requirement_text.repairs auf Korrektheit.",
    ]
    if reason == "missing_space_suspects":
        steps.append(
            "Entscheide fuer jeden Token in suspects (%s), ob es ein gueltiger "
            "C++-Bezeichner ist oder ein fehlendes Leerzeichen. Korrigiere nur "
            "belegbare Faelle und ergaenze je Korrektur einen repairs-Eintrag "
            "mit rule=manual_space@v1." % ", ".join(entry.get("suspects") or ()))
    elif reason == "backend_mismatch":
        steps.append(
            "Die PDF-Backends liefern abweichenden Text. Bestimme anhand des "
            "Deep-Links die korrekte Fassung und dokumentiere die Entscheidung.")
    else:
        steps.append(
            "Nur ein Backend verfuegbar. Bestaetige den Text gegen den "
            "Deep-Link oder markiere ihn als unsicher.")
    steps += [
        "Setze requirement_meta.trace[0].review.status auf accepted oder rejected.",
        "Aendere niemals den englischen Normtext ueber die belegte Reparatur hinaus.",
        "Rufe abschliessend review_flags.complete_flag(...) auf.",
    ]
    return {
        "goal": "Normtext von %s verifizieren und Review-Status setzen." % rid,
        "forbidden": [
            "Neuen Normtext formulieren",
            "text_raw veraendern oder entfernen",
            "Reparaturen ohne repairs-Eintrag vornehmen",
        ],
        "steps": steps,
    }


def write_review_flag(rid, reason, entry, record_path, campaign,
                      confidence="medium"):
    """Flag additiv anlegen; ein bereits offenes Flag wird nicht ueberschrieben."""
    _ensure_dirs()
    path = OPEN_DIR / (rid + ".json")
    if path.exists():
        return None
    _atomic_write(path, {
        "schema": SCHEMA,
        "id": rid,
        "created": _now(),
        "campaign": campaign,
        "reason": reason,
        "confidence": confidence,
        "record": str(record_path),
        "finding": {
            "suspects": entry.get("suspects") or [],
            "repairs": entry.get("repairs") or [],
        },
        "instruction": build_instruction(rid, reason, entry, record_path),
    })
    return path


def list_open_flags():
    _ensure_dirs()
    return sorted(OPEN_DIR.glob("*.json"))


def claim_flag(path, agent=None):
    """Flag atomar uebernehmen. Rueckgabe None, wenn ein anderer schneller war."""
    _ensure_dirs()
    path = Path(path)
    agent = agent or "%s-%s" % (socket.gethostname(), os.getpid())
    target = CLAIMED_DIR / ("%s.%s.json" % (path.stem, agent))
    try:
        os.rename(path, target)
    except OSError:
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["claimed_by"] = agent
    payload["claimed_at"] = _now()
    _atomic_write(target, payload)
    return target


def complete_flag(path, outcome, note=None):
    """Bearbeitetes Flag nach Abschluss loeschen.

    Die revisionssichere Entscheidungsdokumentation wird vor diesem Aufruf
    im Requirement-Record gespeichert. Flags dienen nur der Jobkontrolle und
    Synchronisierung; nach dem Abschluss bleibt deshalb kein Queue-Artefakt.
    """
    _ensure_dirs()
    path = Path(path)
    path.unlink()
    return None


def release_flag(path):
    """Uebernahme zuruecknehmen, etwa bei Abbruch eines Subagenten."""
    path = Path(path)
    rid = path.stem.split(".")[0]
    target = OPEN_DIR / (rid + ".json")
    os.rename(path, target)
    return target
