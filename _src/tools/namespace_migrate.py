#!/usr/bin/env python3
"""Schreibt die Namensraum-Zugehoerigkeit explizit in jeden Spec-Record.

Hintergrund: Die Modulzugehoerigkeit ergibt sich (akzeptiert) implizit aus dem
Ablageort `spec/records/<GRUPPE>/`. Der Namensraum war bisher gar nicht
explizit hinterlegt, sondern nur als Fliesstext in der Property-Zeile "Scope"
(bzw. gar nicht) vorhanden. Konsumenten mussten ihn aus gerendertem HTML
zurueckrechnen -- ein Verstoss gegen "ein Fakt, ein Ort" (ARCHITEKTUR.md).

Dieses Skript ist idempotent und ergaenzt je Record einen Block:

    "ns": {
      "namespace": "ara::idsm",       # kanonischer C++-Namensraum (oder null)
      "modul": "idsm",                # aus dem Ablageort abgeleitet
      "quelle": "scope",              # scope | header | gruppe | dienst
      "generiert": false,             # true bei modellgenerierten Platzhaltern
      "abweichung": null              # gesetzt, wenn namespace != ara::<modul>
    }

Aufruf:  python3 tools/namespace_migrate.py [--check]
"""
from __future__ import annotations

import argparse
import collections
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDS = ROOT / "spec" / "records"
MAP_FILE = ROOT / "spec" / "namespaces.json"

# Ablageort (Spec-Gruppe) -> Modul-ID, wie sie auch der Komponentengraph nutzt.
# AP_SWS ist ein Sammelbereich mehrerer Zusatzcluster und wird ueber den
# Namensraum selbst aufgeloest (siehe modul_of()).
GROUP_TO_MODULE = {
    "SWS_AIDSM": "idsm",
    "SWS_ANM": "nm",
    "SWS_CM": "com",
    "SWS_CORE": "core",
    "SWS_CRYPT": "crypto",
    "SWS_DM": "diag",
    "SWS_EM": "exec",
    "SWS_LOG": "log",
    "SWS_PER": "per",
    "SWS_PHM": "phm",
    "SWS_RDS": "rds",
    "SWS_SM": "sm",
    "SWS_TS": "tsync",
    "SWS_UCM": "ucm",
}

SCOPE_KINDS = ("namespace", "class", "struct", "union", "enum class", "enum", "service interface")


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def prop(rec: dict, prefix: str):
    """Erste Property-Zeile, deren Label mit `prefix` beginnt (case-insensitiv)."""
    for blk in rec.get("blocks", []):
        if blk.get("t") != "props":
            continue
        for row in blk.get("rows", []):
            if strip_tags(row.get("th", "")).lower().startswith(prefix):
                return strip_tags(row.get("td", ""))
    return None


def ns_from_scope(scope: str):
    """(namespace, generiert, ist_dienst) aus der Scope-Zeile.

    "namespace ara::core"              -> ara::core
    "class ara::core::Result"          -> ara::core   (letztes Segment = Typ)
    "class <SI-Namespace>::proxy::X"   -> <SI-Namespace>::proxy, generiert
    "service interface PackageManagement" -> kein C++-Namensraum
    """
    s = re.sub(r"\s+", " ", scope or "").strip()
    if not s:
        return None, False, False
    kind = next((k for k in SCOPE_KINDS if s.lower().startswith(k + " ")), None)
    if kind is None:
        return None, False, False
    qual = s[len(kind):].strip()
    if kind == "service interface":
        return None, False, True
    # Modell-Platzhalter (<SI-Namespace>, {<...>}) sind KEINE Template-Argumente:
    # sie stehen fuer generierte Namensraeume und bleiben erhalten.
    generated = bool(re.search(r"<[A-Z][\w-]*(?:-[\w]+)*>", qual)) or ("{" in qual)
    # Echte Template-Argumentlisten vollstaendig (auch geschachtelt) entfernen,
    # damit aus "struct std::hash< ara::core::Optional< T > >" sauber "std" wird
    # und nicht das zerschnittene "std::hash< ara::core".
    if not generated:
        prev = None
        while prev != qual:
            prev = qual
            qual = re.sub(r"<[^<>]*>", "", qual)
        qual = qual.strip()
    parts = [p.strip() for p in qual.split("::") if p.strip()]
    if kind != "namespace":
        parts = parts[:-1]  # letztes Segment ist der Typ selbst
    return ("::".join(parts) or None), generated, False


def ns_from_header(header: str):
    """Fallback: "ara/idsm/common.h" -> ara::idsm."""
    if not header:
        return None
    m = re.search(r"([A-Za-z0-9_/]+)\.h\b", header.replace('"', " ").replace("<", " "))
    if not m:
        return None
    parts = [p for p in m.group(1).split("/") if p][:-1]
    return "::".join(parts) or None


def modul_of(group: str, namespace: str | None) -> str | None:
    if group in GROUP_TO_MODULE:
        return GROUP_TO_MODULE[group]
    if namespace:
        seg = namespace.split("::")
        if len(seg) >= 2 and seg[0] in ("ara", "apext"):
            return seg[1]
    return None


def build(rec: dict, group: str) -> dict:
    scope = prop(rec, "scope")
    namespace, generated, is_service = ns_from_scope(scope) if scope else (None, False, False)
    quelle = "scope" if (namespace or is_service) else None

    if namespace is None and not is_service:
        header = prop(rec, "header")
        namespace = ns_from_header(header)
        if namespace:
            quelle = "header"

    if namespace is None and not is_service:
        # AP_SWS buendelt mehrere Zusatzcluster; die Cluster-Kennung steckt im
        # Record-Praefix (AP_SWS_SHWA_00101 -> shwa), sonst hilft die Gruppe.
        m = re.match(r"AP_SWS_([A-Za-z]+)_", rec.get("id", "") or "")
        if m:
            namespace = f"ara::{m.group(1).lower()}"
            quelle = "id-praefix"

    if namespace is None and not is_service:
        mod = GROUP_TO_MODULE.get(group)
        if mod:
            namespace = f"ara::{mod}"
            quelle = "gruppe"

    if is_service:
        quelle = "dienst"

    modul = modul_of(group, namespace)
    erwartet = f"ara::{modul}" if modul else None
    abweichung = None
    if namespace and erwartet:
        root = namespace.split("::")
        if not (root[0] == "ara" and len(root) >= 2 and root[1] == modul):
            if namespace.startswith("apext::"):
                abweichung = "apext-erweiterung"
            elif generated:
                abweichung = "modellgenerierter-namensraum"
            elif root[0] == "std":
                abweichung = "std-spezialisierung"
            else:
                abweichung = "fremder-namensraum"
    elif is_service:
        abweichung = "dienstschnittstelle-ohne-namensraum"

    return {
        "namespace": namespace,
        "modul": modul,
        "quelle": quelle,
        "generiert": bool(generated),
        "abweichung": abweichung,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="nur pruefen, nichts schreiben")
    args = ap.parse_args()

    files = sorted(RECORDS.rglob("*.json"))
    changed = 0
    stats = collections.Counter()
    exceptions = collections.defaultdict(list)

    for path in files:
        rec = json.loads(path.read_text(encoding="utf-8"))
        group = path.relative_to(RECORDS).parts[0]
        ns = build(rec, group)
        stats[ns["quelle"] or "unbekannt"] += 1
        if ns["abweichung"]:
            exceptions[ns["abweichung"]].append((rec.get("id"), ns["namespace"], ns["modul"]))
        if rec.get("ns") != ns:
            changed += 1
            if not args.check:
                rec["ns"] = ns
                path.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    if not args.check:
        payload = {
            "schema": "ara-api-namespaces/v1",
            "gruppe_zu_modul": GROUP_TO_MODULE,
            "abweichungen": {k: sorted({n for _, n, _ in v if n}) for k, v in exceptions.items()},
        }
        MAP_FILE.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"records: {len(files)}  geaendert: {changed}")
    print("quellen:", dict(stats))
    print("abweichungen:")
    for kind, items in sorted(exceptions.items(), key=lambda kv: -len(kv[1])):
        namespaces = sorted({n for _, n, _ in items if n})
        print(f"  {kind:34s} {len(items):4d}  {', '.join(namespaces[:6]) or '-'}")
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
