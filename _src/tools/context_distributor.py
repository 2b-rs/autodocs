#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""context_distributor.py — Distributionslauf für gepinnte Inbound-Referenzen und Agenten-Kontexte.

Zweck
-----
1. Sucht und extrahiert Querverweise auf ein Zielmodul (z. B. LinIf) aus Fremdspezifikationen
   im lokalen PDF-Cache (_src/spec/pdf-cache/).
2. Speichert Fundstellen als unveränderliche, geprüfte Snippets unter _src/spec/snippets/.
   Damit wird sichergestellt:
     - Traceability & Reproduzierbarkeit (keine Abhängigkeit von flüchtigen externen Webseiten/PDFs).
     - Präzision & Poisoning-Schutz (eindeutiger Nachweis, ob KI halluziniert oder Kontext falsch war).
     - Hohe Informationsdichte (nur relevante Sätze/Absätze statt ganzer PDF-Bände).
3. Assembliert ein reproduzierbares "Agenten-Kontext-Dossier" (_src/ai/dossiers/),
   das vom KI-Workflow (_src/ai_workflow.py) als bindender Kontext verwendet wird.
4. Erzeugt eine interaktive, für Menschen im Frontend browsbare HTML-Ansicht des Dossiers.
5. Vorbereitet für konzeptionelle/akademische Inbound-Referenzen mit Nützlichkeits-Scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS_DIR = Path(__file__).resolve().parent
_SRC_DIR = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import spec_scrape as ss
import dependency_graph as dg

LOG = logging.getLogger("context_distributor")
if not LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    LOG.addHandler(_h)
LOG.setLevel(logging.INFO)

SNIPPETS_DIR = _SRC_DIR / "spec" / "snippets"
DOSSIERS_DIR = _SRC_DIR / "ai" / "dossiers"
PDF_CACHE_R20 = _SRC_DIR / "spec" / "pdf-cache" / "R20-11" / "AUTOSAR" / "CLASSIC"
QUELLEN_FILE = _SRC_DIR / "ai" / "quellen.json"
PAGES_DIR = _SRC_DIR / "sources" / "pages"


def sha256_text(text: str) -> str:
    """Berechnet den SHA-256-Hash eines Texts."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lade_quellen() -> Dict[str, Any]:
    """Lädt das globale Quellenregister."""
    if not QUELLEN_FILE.exists():
        return {}
    with open(QUELLEN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def lade_policy() -> Dict[str, Any]:
    """Lädt die zentrale KI-Policy."""
    policy_file = _SRC_DIR / "ai" / "policy.json"
    if policy_file.exists():
        with open(policy_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def finde_pdf_fuer_dok(dok_name: str) -> Optional[Path]:
    """Findet die lokale PDF-Datei zu einer Dokument-ID."""
    kandidat = PDF_CACHE_R20 / f"{dok_name}.pdf"
    if kandidat.exists():
        return kandidat
    return None


def bereinige_text(text: str) -> str:
    """Normalisiert Leerraum und Zeilenumbrüche für ein Snippet."""
    # Mehrfache Leerzeilen und Whitespaces normalisieren
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extrahiere_snippets_fuer_modul(
    modul_name: str,
    suchbegriffe: List[str],
    cluster_dokumente: List[str],
) -> List[Dict[str, Any]]:
    """Durchsucht Cluster-Dokumente nach Suchbegriffen und liefert Snippet-Kandidaten."""
    gefundene_snippets = []
    
    for dok_id in cluster_dokumente:
        pdf_pfad = finde_pdf_fuer_dok(dok_id)
        if not pdf_pfad:
            LOG.warning("PDF für Quelle %s nicht im Cache gefunden: %s", dok_id, pdf_pfad)
            continue
            
        LOG.info("Scanne %s...", dok_id)
        pages = ss.pdf_pages(pdf_pfad, backend="builtin")
        
        for p_idx, raw_page in enumerate(pages, start=1):
            if not any(term in raw_page for term in suchbegriffe):
                continue
                
            # Finde SWS-Identifier auf dieser Seite
            sws_treffer = re.findall(r"\[(SWS_[A-Za-z0-9_]+)\]", raw_page)
            
            # Zerlege Seite in Absätze
            absatz_bloecke = raw_page.split("\n\n")
            for block in absatz_bloecke:
                if any(term in block for term in suchbegriffe) and len(block.strip()) > 30:
                    clean = bereinige_text(block)
                    
                    # Relevanz & Kategorie heuristisch schätzen
                    kategorie = "inbound_call" if any(f"{modul_name}_" in term for term in suchbegriffe) else "architectural_role"
                    score = 0.9 if sws_treffer else 0.75
                    
                    sws_id = sws_treffer[0] if sws_treffer else None
                    snippet_id = f"SNIP_{modul_name}_{dok_id[:16]}_P{p_idx}_{len(gefundene_snippets)+1:02d}"
                    
                    snippet = {
                        "id": snippet_id,
                        "target_module": modul_name,
                        "source_document": dok_id,
                        "source_page": p_idx,
                        "source_element": sws_id,
                        "category": kategorie,
                        "concept_tags": [modul_name.lower(), "autosar_cp", kategorie],
                        "relevance_score": score,
                        "relevance_rationale": f"Automatisch extrahierter Beleg aus {dok_id} (Seite {p_idx}) mit Treffern für {modul_name}.",
                        "verbatim_text": clean,
                        "sha256": sha256_text(clean),
                        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    }
                    gefundene_snippets.append(snippet)
                    
    return gefundene_snippets


def speichere_snippets(modul_name: str, snippets: List[Dict[str, Any]], plattform: str = "classic") -> Path:
    """Speichert gepinnte Snippets in _src/spec/snippets/<plattform>/modules/<modul>.json."""
    ziel_dir = SNIPPETS_DIR / plattform / "modules"
    ziel_dir.mkdir(parents=True, exist_ok=True)
    ziel_datei = ziel_dir / f"{modul_name.lower()}.json"
    
    daten = {
        "schema_version": "1.0",
        "target_module": modul_name,
        "platform": plattform,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snippet_count": len(snippets),
        "snippets": snippets,
    }
    
    with open(ziel_datei, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
        f.write("\n")
        
    LOG.info("Gepinnte Snippets gespeichert: %s (%d Snippets)", ziel_datei, len(snippets))
    return ziel_datei


def erstelle_agenten_dossier(modul_name: str, plattform: str = "classic") -> Tuple[Path, Dict[str, Any]]:
    """Assembliert das vollständige, reproduzierbare Agenten-Kontext-Dossier."""
    # 1. Lokale Spezifikations-Records laden
    record_datei = _SRC_DIR / "spec" / "records" / plattform / "modules" / f"{modul_name}.json"
    spec_records = []
    if record_datei.exists():
        with open(record_datei, "r", encoding="utf-8") as f:
            rec_data = json.load(f)
            spec_records = rec_data.get("blocks", [])

    # 2. Pinned Inbound-Snippets laden (mit Dismissal-Status aus dem Dependency Graph)
    snippets_datei = SNIPPETS_DIR / plattform / "modules" / f"{modul_name.lower()}.json"
    inbound_snippets = []
    if snippets_datei.exists():
        with open(snippets_datei, "r", encoding="utf-8") as f:
            snip_data = json.load(f)
            for snip in snip_data.get("snippets", []):
                snip["dismissed"] = dg.is_dismissed(snip.get("id", ""))
                inbound_snippets.append(snip)

    # 3. Quellenregister-Metadaten für alle berührten Quellen sammeln
    alle_quellen = lade_quellen()
    beteiligte_quellen_ids = sorted(list({s["source_document"] for s in inbound_snippets}))
    quellen_meta = {qid: alle_quellen.get(qid, {"titel": qid, "typ": "SWS"}) for qid in beteiligte_quellen_ids}

    # 4. Modell- & Ausführungsparameter laden (Standard: Temperatur 0.0 für Reproduzierbarkeit)
    policy = lade_policy()
    modell_cfg = policy.get("modell", {})
    primaer = modell_cfg.get("primaer", {})
    
    execution_params = {
        "model": primaer.get("modell", modell_cfg.get("erklaerungen", "gemini-3.8-flash-high")),
        "display_name": primaer.get("display_name", "Gemini 3.8 Flash (High)"),
        "thinking_effort": primaer.get("thinking_effort", "high"),
        "temperature": primaer.get("temperature", 0.0),
        "reproducible_mode": True,
    }

    # 5. Dossier zusammenstellen
    dossier_content: Dict[str, Any] = {
        "dossier_version": "1.1",
        "target_module": modul_name,
        "platform": plattform,
        "assembled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_parameters": execution_params,
        "reproducibility": {
            "policy_version": policy.get("version", 1),
            "model": execution_params["model"],
            "display_name": execution_params["display_name"],
            "thinking_effort": execution_params["thinking_effort"],
            "temperature": execution_params["temperature"],
            "spec_record_count": len(spec_records),
            "inbound_snippet_count": len(inbound_snippets),
            "source_documents": beteiligte_quellen_ids,
        },
        "spec_records": spec_records,
        "inbound_snippets": inbound_snippets,
        "quellen_register": quellen_meta,
        "bisheriges_fragment": (_SRC_DIR / "content" / "ai" / plattform / "modules" / modul_name.lower() / "main_01.html").read_text(encoding="utf-8") if (_SRC_DIR / "content" / "ai" / plattform / "modules" / modul_name.lower() / "main_01.html").exists() else "",
    }

    # Hash über kanonische Serialisierung bilden
    kanonisch_json = json.dumps(dossier_content, sort_keys=True, ensure_ascii=False)
    dossier_digest = hashlib.sha256(kanonisch_json.encode("utf-8")).hexdigest()
    dossier_content["dossier_sha256"] = dossier_digest

    ziel_dir = DOSSIERS_DIR / plattform / "modules"
    ziel_dir.mkdir(parents=True, exist_ok=True)
    ziel_datei = ziel_dir / f"{modul_name.lower()}.json"

    with open(ziel_datei, "w", encoding="utf-8") as f:
        json.dump(dossier_content, f, ensure_ascii=False, indent=2)
        f.write("\n")

    LOG.info("Agenten-Dossier geschrieben: %s (SHA: %s)", ziel_datei, dossier_digest[:12])
    return ziel_datei, dossier_content


KNOWN_CLASSIC_MODULES = {
    "linif": "LinIf",
    "linsm": "LinSM",
    "lin": "Lin",
    "lintrcv": "LinTrcv",
    "pdur": "PduR",
    "comm": "ComM",
    "com": "Com",
    "ecum": "EcuM",
    "canif": "CanIf",
    "can": "Can",
    "cantp": "CanTp",
    "cantrcv": "CanTrcv",
    "comstack": "ComStack",
    "std": "Std",
    "os": "Os",
    "rte": "Rte",
    "dem": "Dem",
    "dcm": "Dcm",
    "det": "Det",
    "secoc": "SecOC",
    "bswm": "BswM",
    "crypto": "Crypto",
    "cryif": "CryIf",
    "csm": "Csm",
    "ethif": "EthIf",
    "eth": "Eth",
    "frif": "FrIf",
    "frsm": "FrSM",
    "frtp": "FrTp",
    "frtrcv": "FrTrcv",
    "fr": "Fr",
    "idsm": "IdsM",
    "keym": "KeyM",
    "memif": "MemIf",
    "nvm": "NvM",
    "pwm": "Pwm",
    "tcpip": "TcpIp",
    "wdgm": "WdgM",
    "wdg": "Wdg",
    "adc": "Adc",
    "dlt": "Dlt",
    "ea": "Ea",
    "fee": "Fee",
    "platform": "Platform",
}

CLASSIC_CLUSTERS = {
    "lin": {
        "title": "LIN",
        "name": "lin",
        "description": "AUTOSAR Classic LIN Cluster",
        "modules": [
            ("Lin", "AUTOSAR_SWS_LINDriver"),
            ("LinIf", "AUTOSAR_SWS_LINInterface"),
            ("LinSM", "AUTOSAR_SWS_LINStateManager"),
            ("LinTrcv", "AUTOSAR_SWS_LINTransceiverDriver"),
        ],
        "page": "classic/lin.json",
    }
}


def resolve_spec_record_target(rec_id: str, current_module: str = "LinIf", is_cluster: bool = False) -> Optional[Tuple[str, str]]:
    """Löst einen Spezifikations-Identifier (z.B. SWS_LinSM_00079) in (url, target_type) auf."""
    m = re.match(r"^(SWS|SRS|TPS)_([A-Za-z0-9]+)_", rec_id)
    if not m:
        return None
    prefix = m.group(2).lower()
    if prefix == "comtype":
        prefix = "comstack"
    if is_cluster:
        if prefix in KNOWN_CLASSIC_MODULES:
            return f"modules/{prefix}.html#{rec_id}", "cluster_module"
        return None
    cur = current_module.lower()
    if prefix == cur:
        return f"#{rec_id}", "local"
    if prefix in KNOWN_CLASSIC_MODULES:
        return f"{prefix}.html#{rec_id}", "cross_module"
    return None


def linkify_spec_references(text: str, current_module: str = "LinIf", is_cluster: bool = False) -> str:
    """Verwandelt Spezifikations-Referenzen wie [SWS_LinSM_00079] oder SWS_LinIf_00503 in klickbare Links."""
    pattern = re.compile(r"(\[)?\b(SWS_[A-Za-z0-9]+_[0-9A-Za-z]+)\b(\])?")
    def repl(match):
        has_lb = bool(match.group(1))
        rec_id = match.group(2)
        has_rb = bool(match.group(3))
        target_info = resolve_spec_record_target(rec_id, current_module, is_cluster=is_cluster)
        if not target_info:
            return match.group(0)
        url, kind = target_info
        bracket_pre = "[" if (has_lb or has_rb) else ""
        bracket_post = "]" if (has_lb or has_rb) else ""
        if kind == "local":
            title = f"Zu {rec_id} im aktuellen Modul springen"
        else:
            mod_key = url.split('.')[0].replace("modules/", "")
            mod_title = KNOWN_CLASSIC_MODULES.get(mod_key, mod_key)
            title = f"Zu {rec_id} in {mod_title} springen"
        return f'<a href="{url}" class="rec-jump-link" data-rec-id="{rec_id}" title="{title}">{bracket_pre}<code>{rec_id}</code>{bracket_post}</a>'
    return pattern.sub(repl, text)


def extrahiere_spec_records(records: List[Dict[str, Any]], module_name: str = "LinIf", doc_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Extrahiert alle konstituierenden Spezifikations-Records des Moduls mit Syntax und Beschreibung."""
    extracted = []
    default_doc = doc_name or f"AUTOSAR_SWS_{module_name}"
    for i, b in enumerate(records):
        if not isinstance(b, dict) or b.get("t") != "html":
            continue
        h = b.get("html", "")
        m = re.search(
            r'<h3 class=["\']recname["\']\s+id=["\']([^"\']+)["\']><span class=["\']kind["\']>([^<]+)</span>\s*(.+?)\s*<span class=["\']sws["\']>(?:<a[^>]*>)?\[([^\]]+)\]',
            h,
        )
        if m:
            rec_id = m.group(1).strip()
            kind = m.group(2).strip()
            name = m.group(3).strip()
            name = re.sub(r"AUTOSAR_SWS_\w+", "", name).strip()
            sws = m.group(4).strip()
            syntax = ""
            desc = ""
            for next_b in records[i + 1 :]:
                if not isinstance(next_b, dict) or next_b.get("t") != "html":
                    continue
                nh = next_b.get("html", "")
                if 'class="recname"' in nh or "class='recname'" in nh or "<h2" in nh:
                    break
                if 'class="syntax"' in nh or "class='syntax'" in nh:
                    syntax = nh
                elif 'class="desc"' in nh or "class='desc'" in nh:
                    desc = nh

            dismissed = dg.is_dismissed(rec_id)
            extracted.append({
                "id": rec_id,
                "kind": kind,
                "name": name,
                "sws": sws,
                "syntax": syntax,
                "desc": desc,
                "module": module_name,
                "document": default_doc,
                "dismissed": dismissed,
            })
    return extracted


def lade_richtlinien() -> str:
    r_path = _SRC_DIR / "ai" / "RICHTLINIEN.md"
    if r_path.is_file():
        text = r_path.read_text(encoding="utf-8")
        # Schneide interne Entwickler-Dokumentation (Trace-Dateien-Tabelle und CLI-Regenerierungsworkflow) ab
        if "## Trace-Dateien" in text:
            text = text.split("## Trace-Dateien")[0].strip()
        return text
    return ""


def baue_auftrag_entry(
    modul: str,
    plattform: str = "classic",
    snippets: Optional[List[Dict[str, Any]]] = None,
    dossier_digest: str = "",
    is_cluster: bool = False,
    cluster_modules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    from ai_workflow import trace_pfad
    from lib_docmodel import SRC, record_relpath

    if is_cluster:
        frag = f"content/ai/{plattform}/clusters/{modul.lower()}/main_01.html"
        seite = f"{plattform}/{modul.lower()}.html"
        art = "cluster-guide"
    else:
        frag = f"content/ai/{plattform}/modules/{modul.lower()}/main_01.html"
        seite = f"{plattform}/modules/{modul.lower()}.html"
        art = "module-guide"

    tp = trace_pfad(frag)
    t = None
    if os.path.exists(tp):
        try:
            t = json.loads(open(tp, encoding="utf-8").read())
        except Exception:
            pass
    if not t:
        local_tp = os.path.join(SRC, frag)[:-len(".html")] + ".trace.json"
        if os.path.exists(local_tp):
            try:
                t = json.loads(open(local_tp, encoding="utf-8").read())
            except Exception:
                pass

    # Isolierte, saubere Spezifikations-Records (ohne redundanten 150 KB Modul-HTML-Ballast)
    records = {}
    for e in (t or {}).get("elemente", []):
        jl = _SRC_DIR / "spec" / "versions" / "AUTOSAR" / "CP" / "record" / f"{e}.jsonl"
        if jl.is_file():
            # Neueste Version des Datensatzes als kompakter, belegbarer Text (Token-effizient)
            lines = [line.strip() for line in jl.read_text(encoding="utf-8").splitlines() if line.strip()]
            if lines:
                rec_obj = json.loads(lines[-1])
                records[e] = {
                    "id": e,
                    "content": rec_obj.get("content", ""),
                    "source_pdf": rec_obj.get("meta", {}).get("source_pdf", "")
                }
        else:
            # Fallback: Isoliere gezielt die Blöcke dieses Elements
            rp = os.path.join(SRC, record_relpath(e))
            if os.path.exists(rp):
                try:
                    mod_rec = json.loads(open(rp, encoding="utf-8").read())
                    blocks = mod_rec.get("blocks", [])
                    matched = []
                    for i, b in enumerate(blocks):
                        if e in b.get("html", ""):
                            matched.append(b)
                            for next_b in blocks[i+1:i+4]:
                                if any(x in next_b.get("html", "") for x in ["<h3", "<h2"]):
                                    break
                                matched.append(next_b)
                            break
                    records[e] = matched or {"id": e}
                except Exception:
                    pass

    diag = {}
    basis = os.path.join(SRC, frag)[:-len(".html")]
    for q in sorted(list(Path(os.path.dirname(basis)).glob(Path(basis).name + ".*.dot")) + list(Path(os.path.dirname(basis)).glob(Path(basis).name + ".*.seq.json"))):
        diag[os.path.relpath(str(q), SRC)] = q.read_text(encoding="utf-8")

    frag_path = os.path.join(SRC, frag)
    bisheriges_frag = open(frag_path, encoding="utf-8").read() if os.path.exists(frag_path) else None

    # Sauberes Vorwissen OHNE Metadaten vergangener Generierungsläufe (laeufe, alter prompt, altes modell, elemente_stand)
    clean_trace = None
    if t:
        clean_trace = {
            "wissen": t.get("wissen", []),
            "annahmen": t.get("annahmen", []),
        }

    # Bereinigte Inbound-Snippets ohne interne DB-Hashes
    clean_snippets = []
    for s in (snippets or []):
        clean_snippets.append({
            "id": s.get("id"),
            "source_element": s.get("source_element"),
            "source_document": s.get("source_document"),
            "source_page": s.get("source_page"),
            "category": s.get("category"),
            "verbatim_text": s.get("verbatim_text"),
        })

    auftrag: Dict[str, Any] = {
        "fragment": frag,
        "seite": seite,
        "art": art,
        "konstituierende_records": records,
        "inbound_snippets": clean_snippets,
        "bisheriges_fragment": bisheriges_frag,
        "bisherige_diagramme": diag,
        "bisheriger_wissensstand": clean_trace,
        "dossier_sha256": dossier_digest,
    }
    if is_cluster and cluster_modules:
        auftrag["cluster_modules"] = cluster_modules
    return auftrag


def generiere_agenten_prompt_text(
    dossier: Dict[str, Any],
    extracted_records: Optional[List[Dict[str, Any]]] = None,
    snippets: Optional[List[Dict[str, Any]]] = None,
    modul: Optional[str] = None,
    plattform: str = "classic",
) -> str:
    """Erzeugt den originalgetreuen 1:1 LLM-Prompt (System-Prompt + User-Auftrags-JSON) für KI-Modelle."""
    from ai_workflow import lade_policy, AUSGABEFORMAT
    policy = lade_policy()
    richtlinien = lade_richtlinien()

    is_cluster = dossier.get("is_cluster", False) or "target_cluster" in dossier
    if is_cluster:
        modul = dossier.get("target_cluster", "LIN")
        cluster_modules = dossier.get("cluster_modules", [])
    else:
        if modul is None:
            modul = dossier.get("target_module", "LinIf")
        cluster_modules = None

    if snippets is None:
        snippets = dossier.get("inbound_snippets", [])
    digest = dossier.get("dossier_sha256", "")

    system_prompt = (
        "Du bist der offizielle KI-Kurations-Assistent für das autodocs Dokumentations- und Spezifikationssystem (AUTOSAR & S-Core).\n"
        "Deine Aufgabe ist es, präzise, fachlich fundierte Erklärungen, User Guides und Diagramme zu verfassen.\n\n"
        "FOLGENDE RICHTLINIEN SIND STRIKT BINDEND:\n"
        f"{richtlinien.strip()}\n\n"
        "POLICY-PARAMETER:\n"
        f"{json.dumps(policy, ensure_ascii=False, indent=2)}\n\n"
        "ERWARTETES AUSGABEFORMAT:\n"
        "Antworte AUSSCHLIESSLICH im validen JSON-Format gemäß folgendem Schema:\n"
        f"{AUSGABEFORMAT.strip()}"
    )

    auftrag_entry = baue_auftrag_entry(
        modul,
        plattform=plattform,
        snippets=snippets,
        dossier_digest=digest,
        is_cluster=is_cluster,
        cluster_modules=cluster_modules,
    )
    user_prompt = (
        "Bitte bearbeite folgenden Auftrag und liefere das geforderte Ergebnis:\n"
        f"{json.dumps(auftrag_entry, ensure_ascii=False, indent=2)}"
    )

    return (
        "================================================================================\n"
        "[SYSTEM PROMPT]\n"
        "================================================================================\n"
        f"{system_prompt}\n\n"
        "================================================================================\n"
        "[USER PROMPT]\n"
        "================================================================================\n"
        f"{user_prompt}\n"
    )


def generiere_rich_text_html(
    dossier: Dict[str, Any],
    extracted_records: List[Dict[str, Any]],
    snippets: List[Dict[str, Any]],
    modul: str,
) -> str:
    """Erzeugt eine formatierte, lesbare Fließtext-Dokumentation des Kontext-Dossiers."""
    is_cluster = dossier.get("is_cluster", False) or "target_cluster" in dossier
    title_label = f"Cluster {modul}" if is_cluster else modul
    repro = dossier.get("reproducibility", {})
    exec_params = dossier.get("execution_parameters", {})
    digest = dossier.get("dossier_sha256", "")[:16]
    model_display = exec_params.get("display_name") or repro.get("display_name") or exec_params.get("model") or "Gemini 3.8 Flash (High)"
    effort = exec_params.get("thinking_effort") or repro.get("thinking_effort") or "high"
    temp = exec_params.get("temperature", repro.get("temperature", 0.0))

    html_parts = [
        '<div class="dossier-rich-content" style="padding: 14px 18px; max-width: 900px; margin: 0 auto; line-height: 1.6;">',
        '  <div class="rich-header" style="border-bottom: 2px solid #01696f; padding-bottom: 12px; margin-bottom: 20px;">',
        f'    <h2 style="color: #01696f; margin: 0 0 6px;">Agenten-Kontext &amp; Nachweis-Dossier: {title_label}</h2>',
        '    <p style="margin: 0; color: #555; font-size: 0.95em;">Formatierte Leseansicht des vollständigen Spezifikationskontexts für die Generierung von Modul-Guides und Traceability.</p>',
        '  </div>',
        '  <div class="rich-meta-box" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; background: #fdfcf9; border: 1px solid #e5dfd3; border-radius: 6px; padding: 14px; margin-bottom: 24px;">',
        f'    <div><strong>Modell:</strong> {model_display}</div>',
        f'    <div><strong>Thinking Effort:</strong> <code>{effort}</code></div>',
        f'    <div><strong>Temperatur:</strong> <code>{temp}</code> (deterministisch)</div>',
        f'    <div><strong>Dossier-SHA:</strong> <code>{digest}…</code></div>',
        f'    <div><strong>Records:</strong> {len(extracted_records)} APIs &amp; Typen</div>',
        f'    <div><strong>Inbound-Snippets:</strong> {len(snippets)} Belege</div>',
        '  </div>',
        f'  <h3 style="color: #005f73; border-bottom: 1px solid #ddd; padding-bottom: 6px;">1. Konstituierende Spezifikations-Records ({len(extracted_records)})</h3>',
        '  <div class="rich-records-list" style="margin-bottom: 30px;">',
    ]

    for rec in extracted_records:
        name = rec["name"]
        kind = rec["kind"]
        sws = rec["sws"]
        doc = rec["document"]
        syntax = rec["syntax"]
        desc = rec["desc"]
        sws_linked = linkify_spec_references(sws, modul, is_cluster=is_cluster)
        desc_linked = linkify_spec_references(desc, modul, is_cluster=is_cluster) if desc else '<em>(Keine weitere Beschreibung vorhanden)</em>'

        html_parts.append('    <div class="rich-record-entry" style="margin-bottom: 16px; padding: 12px 14px; border-left: 3px solid #005f73; background: #fafafa; border-radius: 0 4px 4px 0;">')
        html_parts.append(f'      <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;"><strong>{name}</strong> <span style="font-size:0.85em; color:#666;">[{sws_linked}] · {doc} · <em>{kind}</em></span></div>')
        if syntax:
            html_parts.append(f'      <div style="margin: 6px 0; font-family: monospace; font-size: 0.9em; background: #f0f0ee; padding: 6px 8px; border-radius: 3px;">{syntax}</div>')
        html_parts.append(f'      <div style="font-size: 0.92em; color: #333; margin-top: 6px;">{desc_linked}</div>')
        html_parts.append('    </div>')

    html_parts.append('  </div>')
    html_parts.append(f'  <h3 style="color: #01696f; border-bottom: 1px solid #ddd; padding-bottom: 6px;">2. Extrahierte &amp; Gepinnte Inbound-Snippets ({len(snippets)})</h3>')
    html_parts.append('  <div class="rich-snippets-list">')

    for snip in snippets:
        doc = snip.get("source_document", "")
        page = snip.get("source_page", 0)
        sws = snip.get("source_element") or "Abschnitt"
        cat = snip.get("category", "inbound")
        score = snip.get("relevance_score", 1.0)
        rationale = snip.get("relevance_rationale", "")
        text = snip.get("verbatim_text", "").replace("\n", "<br>")
        sws_linked = linkify_spec_references(sws, modul, is_cluster=is_cluster)
        text_linked = linkify_spec_references(text, modul, is_cluster=is_cluster)

        html_parts.append('    <div class="rich-snippet-entry" style="margin-bottom: 16px; padding: 12px 14px; border-left: 3px solid #01696f; background: #f7faf9; border-radius: 0 4px 4px 0;">')
        html_parts.append(f'      <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;"><strong>{sws_linked}</strong> <span style="font-size:0.85em; color:#666;">{doc} (Seite {page}) · {cat} (Score: {score:.2f})</span></div>')
        if rationale:
            html_parts.append(f'      <div style="font-size: 0.88em; color: #555; margin: 4px 0;"><em>Zweck:</em> {linkify_spec_references(rationale, modul, is_cluster=is_cluster)}</div>')
        html_parts.append(f'      <blockquote style="margin: 6px 0; padding: 8px 12px; background: #ffffff; border-left: 2px solid #01696f; font-family: Georgia, serif; font-size: 0.93em; line-height: 1.45;">{text_linked}</blockquote>')
        html_parts.append('    </div>')

    html_parts.append('  </div>')
    html_parts.append('</div>')
    return "\n".join(html_parts)


def generiere_dossier_html(dossier: Dict[str, Any]) -> str:
    """Erzeugt ein interaktives Zwei-Spalten-Workbench-Modal des Agenten-Kontext-Dossiers."""
    is_cluster = dossier.get("is_cluster", False) or "target_cluster" in dossier
    plattform = dossier.get("platform", "classic")
    if is_cluster:
        modul = dossier.get("target_cluster", "LIN")
        cluster_name = dossier.get("cluster_name", modul.lower())
        cluster_modules = dossier.get("cluster_modules", [])
        modal_id = f"dossier-modal-cluster-{cluster_name.lower()}"
        modal_title = f"Agenten-Kontext &amp; Nachweis-Dossier (Cluster {modul})"
        section_desc = f"Volltext der Kernspezifikationen aller Cluster-Module ({', '.join(cluster_modules)}). Auch die Eigenschaft „konstituierend“ kann beanstandet oder im Verbund mit Nachbarschnittstellen diskutiert werden."
        frag_rel = f"content/ai/{plattform}/clusters/{cluster_name.lower()}/main_01.html"
    else:
        modul = dossier.get("target_module", "Unbekannt")
        cluster_name = None
        cluster_modules = []
        modal_id = f"dossier-modal-{modul.lower()}"
        modal_title = f"Agenten-Kontext &amp; Nachweis-Dossier ({modul})"
        section_desc = "Volltext der Kernspezifikation. Auch die Eigenschaft „konstituierend“ kann beanstandet oder im Verbund mit Nachbarschnittstellen diskutiert werden."
        frag_rel = f"content/ai/{plattform}/modules/{modul.lower()}/main_01.html"

    repro = dossier.get("reproducibility", {})
    exec_params = dossier.get("execution_parameters", {})
    digest = dossier.get("dossier_sha256", "")[:16]
    snippets = dossier.get("inbound_snippets", [])
    records = dossier.get("spec_records", [])

    model_display = exec_params.get("display_name") or repro.get("display_name") or exec_params.get("model") or "Gemini 3.8 Flash (Medium)"
    effort = exec_params.get("thinking_effort") or repro.get("thinking_effort") or "medium"
    temp = exec_params.get("temperature", repro.get("temperature", 0.0))

    # Extrahiere alle konstituierenden Records (Funktionen, Typen, Callbacks) mit Syntax und Beschreibung
    if dossier.get("extracted_records"):
        extracted_records = dossier["extracted_records"]
    else:
        extracted_records = extrahiere_spec_records(records, modul)

    raw_prompt_text = generiere_agenten_prompt_text(dossier, extracted_records, snippets, modul=modul, plattform=plattform)
    rich_text_html = generiere_rich_text_html(dossier, extracted_records, snippets, modul)

    viewer_body: List[str] = [
        '      <div class="dossier-header">',
        '        <p class="ai-note"><strong>Agenten-Kontext &amp; Nachweis-Dossier (Audit-Trail)</strong>: '
        'Dieser kondensierte, verifizierte Kontext wurde dem Agenten für die Kommentargenerierung vorgegeben. '
        'Alle Inbound-Referenzen stammen aus unveränderlichen, im Repository gepinnten Snippets. '
        'Sowohl konstituierende Records als auch Fremd-Snippets können im Volltext kuratiert und mit der KI diskutiert werden.</p>',
        '        <div class="dossier-meta-grid" style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 12px 0 16px; font-size: 0.88em; background: #f8f6f0; padding: 12px; border-radius: 6px; border: 1px solid #e2ded4;">',
        f'          <div><strong>Modell:</strong> <span>{model_display}</span></div>',
        f'          <div><strong>Thinking Effort:</strong> <code style="background:#eaf2f1; padding:2px 5px; border-radius:3px;">{effort}</code></div>',
        f'          <div><strong>Temperatur:</strong> <code style="background:#eaf2f1; padding:2px 5px; border-radius:3px;">{temp}</code> <span style="font-size:0.82em; color:#01696f;">(deterministisch)</span></div>',
        f'          <div><strong>Dossier-SHA:</strong> <code>{digest}…</code></div>',
        f'          <div><strong>Konstituierende Records:</strong> {len(extracted_records)}</div>',
        f'          <div><strong>Gepinnte Inbound-Snippets:</strong> {len(snippets)}</div>',
        f'          <div><strong>Quellendokumente:</strong> {len(repro.get("source_documents", []))}</div>',
        '        </div>',
        '      </div>',
    ]

    num_func = len([r for r in extracted_records if r.get("kind") == "function"])
    num_type = len([r for r in extracted_records if r.get("kind") == "type"])
    num_inbound = len(snippets)
    total_items = len(extracted_records) + num_inbound

    # 0. Multiselection Batch Action Bar (erscheint nur, wenn die Auswahl nicht leer ist)
    viewer_body.append('      <div class="dossier-selection-bar" id="dossier-selection-bar" hidden>')
    viewer_body.append('        <div class="selection-info">')
    viewer_body.append('          <span class="selection-indicator" aria-hidden="true">☑</span>')
    viewer_body.append('          <strong id="selection-count">0</strong> <span id="selection-label">Elemente ausgewählt</span>')
    viewer_body.append('          <span class="selection-key-hint">(Ctrl+Klick: Umschalten · Shift+Klick: Bereich · Shift+↑↓)</span>')
    viewer_body.append('        </div>')
    viewer_body.append('        <div class="selection-actions">')
    viewer_body.append('          <button type="button" class="curation-btn btn-confirm" id="btn-batch-confirm" title="Alle ausgewählten Elemente bestätigen">')
    viewer_body.append('            <span class="vote-icon">👍</span> <span>Bestätigen</span> (<span class="batch-count" id="batch-confirm-count">0</span>)')
    viewer_body.append('          </button>')
    viewer_body.append('          <button type="button" class="curation-btn btn-dismiss" id="btn-batch-dismiss" title="Alle ausgewählten Elemente beanstanden">')
    viewer_body.append('            <span class="vote-icon">👎</span> <span>Beanstanden</span> (<span class="batch-count" id="batch-dismiss-count">0</span>)')
    viewer_body.append('          </button>')
    viewer_body.append('          <button type="button" class="curation-btn btn-discuss" id="btn-batch-discuss" title="Alle ausgewählten Elemente gemeinsam mit KI diskutieren">')
    viewer_body.append('            <span class="vote-icon">💬</span> <span>Mit KI diskutieren</span> (<span class="batch-count" id="batch-discuss-count">0</span>)')
    viewer_body.append('          </button>')
    viewer_body.append('          <button type="button" class="btn-clear-selection" id="btn-clear-selection" title="Auswahl aufheben">✕ Auswahl aufheben</button>')
    viewer_body.append('        </div>')
    viewer_body.append('      </div>')

    # Sticky Filter- & Ansichts-Toolbar
    viewer_body.append('      <div class="dossier-toolbar" id="dossier-toolbar">')
    viewer_body.append('        <div class="dossier-search-bar">')
    viewer_body.append('          <span class="dossier-search-icon" aria-hidden="true">🔍</span>')
    viewer_body.append('          <input type="search" class="dossier-search-input" id="dossier-search-input" placeholder="Nach Name, SWS-ID, Modul, Dokument oder Text filtern…" autocomplete="off" aria-label="Dossier-Elemente filtern">')
    viewer_body.append('          <button type="button" class="btn-clear-dossier-search" id="btn-clear-dossier-search" title="Suche leeren" hidden>&times;</button>')
    viewer_body.append('        </div>')
    viewer_body.append('        <div class="dossier-filter-row">')
    viewer_body.append('          <div class="dossier-filter-group" role="group" aria-label="Nach Element-Art filtern">')
    viewer_body.append('            <span class="filter-group-label">Art:</span>')
    viewer_body.append(f'            <button type="button" class="dossier-filter-pill is-active" data-filter-kind="all">Alle <span class="pill-count" id="count-kind-all">{total_items}</span></button>')
    viewer_body.append(f'            <button type="button" class="dossier-filter-pill" data-filter-kind="inbound">Inbound <span class="pill-count" id="count-kind-inbound">{num_inbound}</span></button>')
    viewer_body.append(f'            <button type="button" class="dossier-filter-pill" data-filter-kind="function">Funktionen <span class="pill-count" id="count-kind-func">{num_func}</span></button>')
    viewer_body.append(f'            <button type="button" class="dossier-filter-pill" data-filter-kind="type">Typen <span class="pill-count" id="count-kind-type">{num_type}</span></button>')
    viewer_body.append('          </div>')
    viewer_body.append('          <div class="dossier-filter-group" role="group" aria-label="Nach Kurationsstatus filtern">')
    viewer_body.append('            <span class="filter-group-label">Status:</span>')
    viewer_body.append('            <button type="button" class="dossier-filter-pill is-active" data-filter-status="all">Alle</button>')
    viewer_body.append('            <button type="button" class="dossier-filter-pill" data-filter-status="unrated">Unbewertet</button>')
    viewer_body.append('            <button type="button" class="dossier-filter-pill" data-filter-status="confirmed">👍 Bestätigt</button>')
    viewer_body.append('            <button type="button" class="dossier-filter-pill" data-filter-status="dismissed">👎 Beanstandet</button>')
    viewer_body.append('            <button type="button" class="dossier-filter-pill" data-filter-status="queued">⏳ Im Paket</button>')
    viewer_body.append('            <button type="button" class="dossier-filter-pill" data-filter-status="in-discussion">💬 In Diskussion</button>')
    viewer_body.append('          </div>')
    viewer_body.append('          <div class="dossier-view-toggle-group">')
    viewer_body.append('            <button type="button" class="dossier-toggle-btn is-active" id="btn-view-compact" title="Kompakte Einzeiler-Ansicht">☰ Kompakt</button>')
    viewer_body.append('            <button type="button" class="dossier-toggle-btn" id="btn-view-detailed" title="Volltext-Detailansicht">☷ Detailliert</button>')
    viewer_body.append('            <button type="button" class="dossier-toggle-btn" id="btn-toggle-all-expand" title="Alle Elemente aus- oder einklappen">⊞ Alle ausklappen</button>')
    viewer_body.append('          </div>')
    viewer_body.append('        </div>')
    viewer_body.append('        <div class="dossier-filter-summary">')
    viewer_body.append(f'          <span id="dossier-visible-count">{total_items} von {total_items} Elementen angezeigt</span>')
    viewer_body.append('          <button type="button" class="btn-reset-dossier-filters" id="btn-reset-dossier-filters" hidden>Filter zurücksetzen</button>')
    viewer_body.append('        </div>')
    viewer_body.append('      </div>')

    # 1. Konstituierende Spezifikations-Records des Moduls im Volltext & Kuratierbar
    viewer_body.append('      <div class="dossier-section-head section-head-constituting" style="margin-top: 18px; margin-bottom: 8px;">')
    if is_cluster:
        viewer_body.append(f'        <h3>📋 Konstituierende Spezifikations-Records des Clusters ({len(extracted_records)} APIs &amp; Typen aus {len(cluster_modules)} Modulen)</h3>')
    else:
        viewer_body.append(f'        <h3>📋 Konstituierende Spezifikations-Records des Moduls ({len(extracted_records)} APIs &amp; Typen)</h3>')
    viewer_body.append(f'        <p class="desc" style="font-size: 0.9em; color: #555; margin: 4px 0 10px;">{section_desc}</p>')
    viewer_body.append('      </div>')

    if extracted_records:
        viewer_body.append('      <div class="records-container" id="records-container" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 26px;">')
        for rec in extracted_records:
            rec_id = rec["id"]
            name = rec["name"]
            kind = rec["kind"]
            sws = rec["sws"]
            doc = rec["document"]
            syntax = rec["syntax"]
            desc = rec["desc"]
            rec_mod = rec.get("module") or modul
            dismissed = rec.get("dismissed", False)

            status_class = "status-dismissed" if dismissed else "status-neutral"
            status_text = "Ausgeschlossen (dismissed)" if dismissed else "Unbewertet"

            sws_linked = linkify_spec_references(sws, modul, is_cluster=is_cluster)
            desc_linked = linkify_spec_references(desc, modul, is_cluster=is_cluster) if desc else '<p><em>(Keine weitere Spezifikationsbeschreibung vorhanden)</em></p>'

            pdf_url = f"https://www.autosar.org/fileadmin/standards/R20-11/CP/{doc}.pdf"
            if "SWS_" in sws:
                pdf_url += f"#nameddest={sws}"
            pdf_badge = f'<a href="{pdf_url}" target="_blank" rel="noopener noreferrer" class="sws-pdf-link" style="font-size: 0.82em; color: #01696f; text-decoration: underline;" title="AUTOSAR-Dokument für {doc} öffnen">📄 PDF</a>'

            if is_cluster:
                jump_badge = f'<a href="modules/{rec_mod.lower()}.html#{rec_id}" class="rec-jump-link record-item-chip" data-rec-id="{rec_id}" style="font-size: 0.82em; color: #01696f; text-decoration: underline;" title="Zu {name} im Modul {rec_mod} springen">↗ Im Modul {rec_mod}</a>'
                mod_chip = f'<span class="chip-module" style="background:#e8f4f8; color:#01696f; font-weight:600; padding:2px 6px; border-radius:3px; font-size:0.78em;">{rec_mod}</span>'
            else:
                jump_badge = f'<a href="#{rec_id}" class="rec-jump-link record-item-chip" data-rec-id="{rec_id}" style="font-size: 0.82em; color: #01696f; text-decoration: underline;" title="Zu {name} im Dokument springen">↗ Im Dokument</a>'
                mod_chip = ''

            viewer_body.append(f'        <div class="snippet-card constituting-record-card is-collapsed" id="{rec_id}" data-snippet-id="{rec_id}" data-sws="{sws}" data-doc="{doc}" data-module="{rec_mod}" data-name="{name}" data-kind="{kind}" data-is-constituting="true">')
            viewer_body.append(f'          <div class="snippet-card-header" data-card-toggle="{rec_id}" tabindex="0" role="button" aria-expanded="false" title="Klicken zum Auf-/Zuklappen der Details">')
            viewer_body.append('            <div class="snippet-card-summary">')
            viewer_body.append('              <span class="card-chevron" aria-hidden="true">▸</span>')
            viewer_body.append(f'              <input type="checkbox" class="card-select-checkbox" data-select-card="{rec_id}" title="Element auswählen" aria-label="Element {name} auswählen">')
            viewer_body.append(f'              <strong class="snippet-title">{name}</strong>')
            viewer_body.append(f'              <code class="snippet-sws">[{sws}]</code>')
            if mod_chip:
                viewer_body.append(f'              {mod_chip}')
            viewer_body.append(f'              <span class="chip-kind kind-{kind}">{kind}</span>')
            viewer_body.append(f'              <span class="chip-doc">{doc}</span>')
            viewer_body.append('            </div>')
            viewer_body.append('            <div class="snippet-card-header-actions">')
            viewer_body.append('              <div class="curation-status-box">')
            viewer_body.append(f'                <span class="curation-status-pill {status_class}" data-badge-for="{rec_id}">{status_text}</span>')
            viewer_body.append('              </div>')
            viewer_body.append(f'              <div class="curation-btn-group" data-snippet-id="{rec_id}">')
            viewer_body.append(f'                <button type="button" class="curation-btn btn-confirm" data-action="confirm" data-snippet="{rec_id}" title="Als konstituierend bestätigen (Daumen hoch)">')
            viewer_body.append('                  <span class="vote-icon">👍</span> <span class="vote-label">Bestätigen</span>')
            viewer_body.append('                </button>')
            viewer_body.append(f'                <button type="button" class="curation-btn btn-dismiss {"is-active" if dismissed else ""}" data-action="dismiss" data-snippet="{rec_id}" title="Als konstituierend beanstanden (Daumen runter - falsche Zuordnung)">')
            viewer_body.append('                  <span class="vote-icon">👎</span> <span class="vote-label">Beanstanden</span>')
            viewer_body.append('                </button>')
            viewer_body.append(f'                <button type="button" class="curation-btn btn-discuss" data-action="discuss" data-snippet="{rec_id}" title="Mit KI über Herkunft & \'konstituierend\'-Eigenschaft diskutieren">')
            viewer_body.append('                  <span class="vote-icon">💬</span> <span class="vote-label">Mit KI diskutieren</span>')
            viewer_body.append('                </button>')
            viewer_body.append('              </div>')
            viewer_body.append('            </div>')
            viewer_body.append('          </div>')
            viewer_body.append('          <div class="snippet-card-body">')
            viewer_body.append('            <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">')
            viewer_body.append(f'              <div><strong>{doc}</strong> <span style="font-size: 0.85em; color: #666;">({sws_linked}) · {pdf_badge} · {jump_badge}</span></div>')
            viewer_body.append(f'              <div><span style="background: #e3f2fd; color: #0d47a1; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; font-weight: bold;">Konstituierend · {kind}</span></div>')
            viewer_body.append('            </div>')
            if syntax:
                viewer_body.append(f'            <div style="margin-bottom: 8px;">{syntax}</div>')
            viewer_body.append(f'            <blockquote style="margin: 0 0 8px; padding: 8px 12px; background: #faf9f5; border-left: 3px solid #005f73; font-family: Georgia, serif; font-size: 0.95em; line-height: 1.45;">{desc_linked}</blockquote>')
            viewer_body.append(f'            <div style="font-size: 0.78em; color: #888; display: flex; justify-content: space-between; margin-top: 6px;"><span>Eigenschaft: <em>Konstituierende Modul-Spezifikation</em></span><span>Record-ID: <code>{rec_id}</code></span></div>')
            viewer_body.append('          </div>')
            viewer_body.append('        </div>')
        viewer_body.append('      </div>')

    # 2. Extrahierte & Gepinnte Inbound-Snippets (Fremdspezifikationen)
    viewer_body.append('      <div class="dossier-section-head section-head-inbound" style="margin-top: 24px; margin-bottom: 8px;">')
    viewer_body.append(f'        <h3>Extrahierte &amp; Gepinnte Inbound-Snippets ({len(snippets)} Belege)</h3>')
    viewer_body.append('        <p class="desc" style="font-size: 0.9em; color: #555; margin: 4px 0 10px;">Verifizierte Textbelege aus Nachbardokumenten, die Anforderungen und Aufrufverträge für dieses Modul definieren.</p>')
    viewer_body.append('      </div>')
    viewer_body.append('      <div class="snippets-container" id="snippets-container" style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px;">')

    for snip in snippets:
        s_id = snip.get("id", "")
        doc = snip.get("source_document", "")
        page = snip.get("source_page", 0)
        sws = snip.get("source_element") or "Abschnitt / Fließtext"
        cat = snip.get("category", "inbound")
        score = snip.get("relevance_score", 1.0)
        tags = ", ".join(snip.get("concept_tags", []))
        rationale = snip.get("relevance_rationale", "")
        text = snip.get("verbatim_text", "").replace("\n", "<br>")
        sha = snip.get("sha256", "")[:10]

        dismissed = snip.get("dismissed", False)
        status_class = "status-dismissed" if dismissed else "status-neutral"
        status_text = "Ausgeschlossen (dismissed)" if dismissed else "Unbewertet"

        sws_linked = linkify_spec_references(sws, modul, is_cluster=is_cluster)
        text_linked = linkify_spec_references(text, modul, is_cluster=is_cluster)
        rationale_linked = linkify_spec_references(rationale, modul, is_cluster=is_cluster) if rationale else ""

        pdf_url = f"https://www.autosar.org/fileadmin/standards/R20-11/CP/{doc}.pdf"
        if "SWS_" in sws:
            pdf_url += f"#nameddest={sws}"
        pdf_badge = f'<a href="{pdf_url}" target="_blank" rel="noopener noreferrer" class="sws-pdf-link" style="font-size: 0.82em; color: #01696f; text-decoration: underline;" title="AUTOSAR-Dokument für {doc} (S. {page}) öffnen">📄 PDF</a>'

        viewer_body.append(f'        <div class="snippet-card inbound-snippet-card is-collapsed" id="{s_id}" data-snippet-id="{s_id}" data-sws="{sws}" data-doc="{doc}" data-page="{page}" data-name="{sws}" data-kind="inbound" data-is-inbound="true">')
        viewer_body.append(f'          <div class="snippet-card-header" data-card-toggle="{s_id}" tabindex="0" role="button" aria-expanded="false" title="Klicken zum Auf-/Zuklappen der Details">')
        viewer_body.append('            <div class="snippet-card-summary">')
        viewer_body.append('              <span class="card-chevron" aria-hidden="true">▸</span>')
        viewer_body.append(f'              <input type="checkbox" class="card-select-checkbox" data-select-card="{s_id}" title="Element auswählen" aria-label="Element {sws} auswählen">')
        viewer_body.append(f'              <strong class="snippet-title">{sws}</strong>')
        viewer_body.append(f'              <span class="chip-kind kind-inbound">{cat}</span>')
        viewer_body.append(f'              <span class="chip-doc">{doc} (S. {page})</span>')
        viewer_body.append('            </div>')
        viewer_body.append('            <div class="snippet-card-header-actions">')
        viewer_body.append('              <div class="curation-status-box">')
        viewer_body.append(f'                <span class="curation-status-pill {status_class}" data-badge-for="{s_id}">{status_text}</span>')
        viewer_body.append('              </div>')
        viewer_body.append(f'              <div class="curation-btn-group" data-snippet-id="{s_id}">')
        viewer_body.append(f'                <button type="button" class="curation-btn btn-confirm" data-action="confirm" data-snippet="{s_id}" title="Snippet bestätigen (Daumen hoch)">')
        viewer_body.append('                  <span class="vote-icon">👍</span> <span class="vote-label">Bestätigen</span>')
        viewer_body.append('                </button>')
        viewer_body.append(f'                <button type="button" class="curation-btn btn-dismiss {"is-active" if dismissed else ""}" data-action="dismiss" data-snippet="{s_id}" title="Snippet beanstanden (Daumen runter)">')
        viewer_body.append('                  <span class="vote-icon">👎</span> <span class="vote-label">Beanstanden</span>')
        viewer_body.append('                </button>')
        viewer_body.append(f'                <button type="button" class="curation-btn btn-discuss" data-action="discuss" data-snippet="{s_id}" title="Mit KI über Herkunft & Sinnhaftigkeit diskutieren">')
        viewer_body.append('                  <span class="vote-icon">💬</span> <span class="vote-label">Mit KI diskutieren</span>')
        viewer_body.append('                </button>')
        viewer_body.append('              </div>')
        viewer_body.append('            </div>')
        viewer_body.append('          </div>')
        viewer_body.append('          <div class="snippet-card-body">')
        viewer_body.append('            <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 6px; margin-bottom: 6px;">')
        viewer_body.append(f'              <div><strong>{doc}</strong> <span style="font-size: 0.85em; color: #666;">(S. {page} · {sws_linked}) · {pdf_badge}</span></div>')
        viewer_body.append(f'              <div><span style="background: #eef5f5; color: #01696f; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; font-weight: bold;">{cat}</span> <span style="background: #fdf6e2; color: #8a6d3b; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">Score: {score:.2f}</span></div>')
        viewer_body.append('            </div>')
        if rationale_linked:
            viewer_body.append(f'            <div style="font-size: 0.85em; color: #444; margin-bottom: 8px;"><em>Zweck:</em> {rationale_linked}</div>')
        viewer_body.append(f'            <blockquote style="margin: 0 0 8px; padding: 8px 12px; background: #faf9f5; border-left: 3px solid #01696f; font-family: Georgia, serif; font-size: 0.95em; line-height: 1.45;">{text_linked}</blockquote>')
        viewer_body.append(f'            <div style="font-size: 0.78em; color: #888; display: flex; justify-content: space-between; margin-top: 6px;"><span>Tags: {tags}</span><span>Snippet-SHA: <code>{sha}…</code></span></div>')
        viewer_body.append('          </div>')
        viewer_body.append('        </div>')

    viewer_body.append('      </div>')
    viewer_pane_html = "\n".join(viewer_body)

    # 3. Companion Chat Pane (Zweites Chat-Fenster neben dem Dossier)
    chat_pane_html = '''      <aside class="dossier-chat-pane" id="dossier-chat-pane" hidden>
        <div class="chat-pane-head">
          <div class="chat-pane-title-group">
            <h4 style="margin: 0; font-size: 14px; font-weight: 700; color: #01696f; display: flex; align-items: center; gap: 6px;">
              <span>💬</span> KI-Kurations-Diskussion
            </h4>
            <span class="chat-attached-count" id="chat-attached-count">0 Elemente im Fokus</span>
          </div>
          <button type="button" class="btn-chat-pane-close" id="btn-close-chat-pane" title="Diskussions-Fenster schließen" aria-label="Diskussions-Fenster schließen">✕</button>
        </div>
        <div class="chat-attached-bar" id="chat-attached-bar">
          <div class="chat-attached-label">Fokus:</div>
          <div class="chat-attached-chips" id="chat-attached-chips">
            <span class="chat-attached-empty-hint">Kein Element ausgewählt (klicke bei einem Element auf „💬 Mit KI diskutieren“)</span>
          </div>
          <button type="button" class="btn-clear-attached" id="btn-clear-attached" title="Alle Elemente aus Diskussion lösen" hidden>✕ Alle lösen</button>
        </div>
        <div class="chat-pane-thread" id="chat-pane-thread" role="log" aria-live="polite">
          <div class="chat-bubble bubble-assistant" id="chat-thread-initial-msg">
            Hallo! Wähle ein oder mehrere Elemente (Inbound-Snippets oder konstituierende Records) aus dem Dossier mit <strong>„💬 Mit KI diskutieren“</strong> aus, um Herkunft, Schnittstellenbezug oder Beanstandungen gemeinsam zu analysieren.
          </div>
        </div>
        <div class="chat-pane-chips" id="chat-pane-chips">
          <button type="button" class="workbench-prompt-chip" data-prompt="Woher stammen die ausgewählten Elemente genau und in welchem Kontext stehen sie?">📌 Herkunft analysieren</button>
          <button type="button" class="workbench-prompt-chip" data-prompt="Welcher Schnittstellenbezug und welche Relevanz besteht zwischen den ausgewählten Elementen für dieses Modul?">⚖️ Schnittstellenbezug prüfen</button>
          <button type="button" class="workbench-prompt-chip chip-criticism" data-prompt="Ich beanstande die Zuordnung der ausgewählten Elemente mit folgender fachlicher Begründung: ">⚠️ Beanstandung begründen</button>
        </div>
        <form class="chat-pane-form" id="chat-pane-form">
          <input type="text" class="chat-pane-input" id="chat-pane-input" placeholder="Begründung oder Frage zur Prüfung an die KI senden…" maxlength="1000" autocomplete="off">
          <button type="submit" class="chat-pane-send-btn" id="chat-pane-send-btn">Senden</button>
        </form>
        <div class="chat-pane-proposal-box" id="chat-pane-proposal-box" hidden>
          <div class="proposal-card-header" style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; color: #01696f;">💡 Von KI geprüfter Kurationsvorschlag</span>
            <button type="button" class="btn-dismiss-proposal" id="btn-dismiss-proposal" title="Vorschlag verwerfen" aria-label="Vorschlag verwerfen" style="background:none; border:none; font-size:14px; cursor:pointer; color:#777;">✕</button>
          </div>
          <div class="proposal-card-body" id="chat-pane-proposal-text" style="font-size: 12.5px; margin: 8px 0; background: #fff8e1; padding: 10px; border-radius: 4px; border-left: 3px solid #ffb300; white-space: pre-wrap;"></div>
          <div class="proposal-exit-section" style="margin-top: 10px; padding-top: 8px; border-top: 1px dashed #dcd7ce;">
            <div class="proposal-exit-title" style="font-size: 11.5px; font-weight: 700; color: #555; margin-bottom: 6px;">Wähle den Übernahmeweg:</div>
            <div class="proposal-card-actions" style="display: flex; flex-direction: column; gap: 6px;">
              <button type="button" class="btn-proposal-exit btn-exit-queue" id="btn-submit-workbench-proposal" title="In das globale Review-Paket für GitHub-Issue / offiziellen PR übernehmen">
                📦 Exit 1: In Curation-Queue einreihen (Review-Paket)
              </button>
              <button type="button" class="btn-proposal-exit btn-exit-local" id="btn-apply-justified-locally" title="Direkt im lokalen Audit-Dossier als 'begründet beanstandet' vermerken">
                ✓ Exit 2: Direkt als „begründet“ im Dossier vermerken
              </button>
            </div>
          </div>
        </div>
      </aside>'''

    if is_cluster:
        frag_file = _SRC_DIR / "content" / "ai" / plattform / "clusters" / cluster_name.lower() / "main_01.html"
    else:
        frag_file = _SRC_DIR / "content" / "ai" / plattform / "modules" / modul.lower() / "main_01.html"
    current_output_text = dossier.get("bisheriges_fragment") or (frag_file.read_text(encoding="utf-8") if frag_file.exists() else "")

    modal_html = f'''<dialog id="{modal_id}" class="dossier-modal dossier-workbench" data-dossier-sha="{dossier.get("dossier_sha256", "")}" aria-labelledby="{modal_id}-title">
  <div class="dossier-modal-head">
    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <h3 id="{modal_id}-title"><span class="ai-badge" style="font-size:0.75em; padding:2px 6px; background:#01696f; color:#fff; border-radius:3px;">Audit-Dossier</span> {modal_title}</h3>
      <div class="dossier-mode-switcher" role="tablist" aria-label="Dossier-Ansichtsmodus">
        <button type="button" class="dossier-mode-tab is-active" data-view-mode="prompt" role="tab" aria-selected="true" title="Originaler 1:1 LLM-Prompt (System- + User-Prompt) als Text (Default)">📝 Plaintext Prompt</button>
        <button type="button" class="dossier-mode-tab" data-view-mode="output" role="tab" aria-selected="false" title="Aktueller Output, Modell-Vorschau und Side-by-Side-Vergleich">🔄 Output &amp; Vergleich</button>
        <button type="button" class="dossier-mode-tab" data-view-mode="editor" role="tab" aria-selected="false" title="Interaktiver Kurations-Editor">🛠️ Kurations-Editor</button>
      </div>
      <button type="button" class="btn-toggle-workbench-chat" id="btn-toggle-workbench-chat" title="KI-Diskussionsfenster ein-/ausblenden" hidden>
        💬 Diskussion <span class="header-chat-badge" id="header-chat-badge" hidden>0</span>
      </button>
    </div>
    <button type="button" class="dossier-close-btn" aria-label="Schließen">✕</button>
  </div>
  <div class="dossier-modal-body">
    <!-- Ansicht 1: Plaintext Prompt (Exklusiv) -->
    <div class="dossier-view-mode dossier-view-prompt" id="dossier-view-prompt">
      <div class="raw-pane-toolbar">
        <div class="raw-prompt-help">
          Originalgetreuer 1:1 Prompt gemäß <code>_src/ai_workflow.py</code> &amp; <code>_src/ai/policy.json</code>. Im Textfeld editierbar.
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <button type="button" class="btn-copy-raw-prompt" id="btn-copy-raw-prompt" title="Vollständigen Text-Prompt in die Zwischenablage kopieren">📋 Prompt kopieren</button>
          <span class="copy-success-hint" id="copy-success-hint" hidden>✓ Kopiert!</span>
        </div>
      </div>
      <textarea id="raw-prompt-textarea" class="raw-prompt-text raw-prompt-textarea" spellcheck="false" data-module="{modul}" data-fragment="{frag_rel}" style="width:100%; height:100%; min-height:460px; font-family:var(--font-mono, monospace); font-size:0.85em; line-height:1.5; padding:12px; border:1px solid var(--border-default, #ccc); border-radius:6px; box-sizing:border-box; background:var(--bg-canvas, #fafafa); color:var(--color-ink, #222);">{html.escape(raw_prompt_text)}</textarea>
      <pre class="raw-prompt-text" id="raw-prompt-text" style="display:none;" aria-hidden="true">{html.escape(raw_prompt_text)}</pre>
    </div>

    <!-- Ansicht 2: Output & Vergleich mit Unter-Reiter-Konzept (Aktueller Output, Vorschau, Diff) -->
    <div class="dossier-view-mode dossier-view-output" id="dossier-view-output" hidden>
      <!-- Sub-Tab Bar -->
      <div class="raw-subtab-bar" role="tablist" aria-label="Output- und Vergleichs-Reiter">
        <!-- Rechter Reiter 1: Aktueller Output -->
        <div class="raw-subtab is-active" data-subtab="current" role="tab" id="subtab-btn-current" aria-selected="true">
          <span class="subtab-click-area" data-action="select-subtab" data-subtab="current" title="Bisheriger Stand (Ist-Zustand des Fragments)">
            <span class="subtab-icon">📄</span>
            <span class="subtab-title">Aktueller Output</span>
          </span>
          <button type="button" class="btn-compare-tab" data-compare-id="current" title="Diesen Stand vergleichen (Klick, dann Ziel-Reiter wählen)" aria-label="Aktuellen Output vergleichen">
            <span class="compare-icon">⚖️</span>
          </button>
        </div>

        <!-- Dynamische Preview-Reiter Container -->
        <div class="raw-preview-tabs-list" id="raw-preview-tabs-list" style="display:contents;">
          <!-- Initialer Vorschau-Reiter -->
          <div class="raw-subtab raw-subtab-preview" data-subtab="preview-1" data-preview-id="1" data-state="idle" role="tab" id="subtab-preview-1" aria-selected="false">
            <span class="subtab-click-area" data-action="select-subtab" data-subtab="preview-1" title="Vorschau-Ergebnis anzeigen / starten">
              <span class="subtab-icon">⚡</span>
              <span class="subtab-title">Vorschau</span>
            </span>
            <div class="subtab-controls" id="subtab-controls-preview-1">
              <select class="subtab-select-model" title="Modell auswählen">
                <option value="gemini-3.8-flash" data-provider="agy" selected>Gemini 3.8 Flash</option>
                <option value="composer-2.5" data-provider="cursor">Cursor Composer 2.5</option>
              </select>
              <select class="subtab-select-effort" title="Reasoning / Effort auswählen">
                <option value="medium" selected>med</option>
                <option value="low">low</option>
                <option value="high">high</option>
              </select>
              <button type="button" class="btn-subtab-start" data-preview-id="1" title="Generierung starten">⚡ Start</button>
            </div>
            <button type="button" class="btn-compare-tab" data-compare-id="preview-1" title="Diesen Stand vergleichen" style="display:none;" aria-label="Vergleichen">
              <span class="compare-icon">⚖️</span>
            </button>
            <button type="button" class="btn-subtab-close" data-preview-id="1" title="Diesen Lauf schließen" style="display:none;" aria-label="Schließen">✕</button>
          </div>
        </div>

        <!-- Verknüpfungs-Symbol Badge -->
        <div class="raw-tab-link-badge" id="raw-tab-link-badge" style="display:none;" title="Vergleich aktiv — Klick kehrt zur Einzelansicht zurück">
          <span class="link-symbol-icon">⇄</span>
          <span class="link-label" id="raw-tab-link-label">Verknüpft</span>
          <span class="link-close-icon">✕</span>
        </div>
      </div>

      <!-- Optionale Vergleichs-Hinweisleiste -->
      <div class="raw-compare-hint-bar" id="raw-compare-hint-bar" style="display:none;">
        <span id="raw-compare-hint-text">💡 Klicke nun auf einen zweiten Reiter, um den Side-by-Side-Vergleich zu öffnen.</span>
        <button type="button" class="btn-cancel-compare-pick" id="btn-cancel-compare-pick" style="background:none; border:none; color:inherit; font-weight:bold; cursor:pointer;">Abbrechen</button>
      </div>

      <!-- Content-Bereich unter den Reitern -->
      <div class="raw-subtab-content-area" id="raw-subtab-content-area">
        <!-- Content 1: Aktueller Output (bisheriger Stand direkt angezeigt) -->
        <div class="raw-content-pane raw-pane-current" id="raw-pane-current">
          <pre class="raw-code-box" id="raw-current-output-code">{html.escape(current_output_text)}</pre>
        </div>

        <!-- Content 2: Vorschau-Panes Container -->
        <div class="raw-preview-panes-container" id="raw-preview-panes-container">
          <div class="raw-content-pane raw-pane-preview" id="raw-pane-preview-1" style="display:none;">
            <div class="preview-idle-banner" style="padding:40px 20px; text-align:center; color:var(--color-ink-muted, #666); background:var(--bg-canvas, #fafafa); border:1px dashed var(--border-default, #ccc); border-radius:8px;">
              <div style="font-size:2rem; margin-bottom:8px;">⚡</div>
              <div style="font-weight:600; font-size:1rem; margin-bottom:6px;">Noch keine Vorschau generiert</div>
              <div style="font-size:0.85rem; max-width:440px; margin:0 auto 16px;">Wähle oben im Reiter Modell und Effort aus und klicke auf <strong>⚡ Start</strong>, um die Generierung anzustoßen.</div>
              <button type="button" class="btn-subtab-start-pane" data-preview-id="1" style="padding:6px 16px; font-size:0.9rem; font-weight:700; background:var(--color-teal-600, #01696f); color:#fff; border:none; border-radius:6px; cursor:pointer;">⚡ Generierung jetzt starten</button>
            </div>
          </div>
        </div>

        <!-- Content 3: Side-by-Side Diff View -->
        <div class="raw-pane-compare-diff" id="raw-pane-compare-diff" style="display:none;">
          <div class="raw-diff-compare-header" style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:var(--bg-subtle, #f0f0ee); border:1px solid var(--border-default, #ddd); border-radius:8px 8px 0 0; margin-bottom:-1px;">
            <div class="raw-diff-titles" style="display:flex; align-items:center; gap:8px; font-size:0.88rem; font-weight:700;">
              <span class="diff-icon" aria-hidden="true">⚖️</span>
              <span class="diff-tag-left" id="diff-tag-left" style="background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px;">Basis: Aktueller Output</span>
              <span class="diff-tag-arrow" style="color:var(--color-ink-muted, #888); font-weight:bold;">⇄</span>
              <span class="diff-tag-right" id="diff-tag-right" style="background:#dcfce7; color:#15803d; padding:2px 8px; border-radius:4px;">Ziel: Vorschau</span>
            </div>
            <button type="button" class="btn-unlink-compare" id="btn-unlink-compare" title="Vergleich beenden und zur Einzelansicht zurückkehren" style="background:none; border:1px solid var(--border-default, #ccc); border-radius:4px; padding:3px 8px; font-size:0.78rem; cursor:pointer; color:var(--color-ink-muted, #666);">✕ Vergleich beenden</button>
          </div>
          <div class="raw-diff-body" id="raw-diff-body" style="background:var(--bg-surface, #fff); border:1px solid var(--border-default, #ddd); border-top:none; border-radius:0 0 8px 8px; padding:12px;"></div>
        </div>
      </div>

      <!-- Versteckte Datenablage für aktuellen Output -->
      <div id="raw-current-output-data" style="display:none;" aria-hidden="true">{html.escape(current_output_text)}</div>
    </div>

    <!-- Ansicht 3: Kurations-Editor & Workbench -->
    <div class="dossier-view-mode dossier-view-editor" id="dossier-view-editor" hidden>
      <div class="dossier-workbench-layout">
        <div class="dossier-viewer-pane">
{viewer_pane_html}
        </div>
{chat_pane_html}
      </div>
    </div>
  </div>
</dialog>'''

    # WICHTIG: KEIN inline_html erzeugen! Das Dossier erscheint ausschließlich im Modal, nie als DIV im Fließtext.
    return modal_html


def aktualisiere_seitenmodell_mit_dossier(modul_name: str, dossier_html: str, plattform: str = "classic") -> Path:
    """Fügt das Dossier als dynamisches Modal (außerhalb des Fließtexts) in das Seitenmodell ein."""
    seiten_datei = PAGES_DIR / plattform / "modules" / f"{modul_name.lower()}.json"
    if not seiten_datei.exists():
        raise FileNotFoundError(f"Seitenmodell nicht gefunden: {seiten_datei}")

    with open(seiten_datei, "r", encoding="utf-8") as f:
        seite = json.load(f)

    haupt_bloecke = seite.get("main", [])

    fold_id = f"ai-context-dossier-{modul_name.lower()}"
    modal_id = f"dossier-modal-{modul_name.lower()}"

    bereinigte_bloecke = []
    for b in haupt_bloecke:
        # Alte Folds herausfiltern
        if b.get("t") == "fold":
            attrs = dict(b.get("attrs", []))
            if attrs.get("id") == fold_id or "ai-dossier-fold" in attrs.get("class", ""):
                continue
        # Alte Modal/Dossier-HTML-Blöcke herausfiltern
        if b.get("t") == "html" and (modal_id in b.get("html", "") or "ai-context-dossier" in b.get("html", "")):
            continue
        bereinigte_bloecke.append(b)
    # Ergänze die Action-Toolbar (Diskutieren, Feedback, Review) im Modul-Guide-Fold
    guide_fold_id = f"ai-guide-{modul_name.lower()}"
    guide_actions_html = (
        f'<div class="ai-commentary-actions">\n'
        f'  <button type="button" class="btn-discuss-ai" data-open-discuss="{guide_fold_id}" title="Modul-Guide und Diagramm mit KI diskutieren">💬 Mit KI diskutieren</button>\n'
        f'  <button type="button" class="btn-feedback-action" data-feedback-open data-target-id="User Guide: {modul_name}" title="Fehler, Mangel oder Halluzination im Guide melden">⚠️ Feedback melden</button>\n'
        f'  <button type="button" class="btn-curate-link dossier-open-link" data-dossier-target="{modal_id}" title="Audit-Dossier, Nachweise und Prompt-Kuration öffnen">🛠️ Audit-Dossier &amp; Kuration</button>\n'
        f'  <button type="button" class="btn-curate-link" data-review-open title="Review-Paket (GitHub-Issue / JSON) öffnen">📦 Review-Paket</button>\n'
        f'</div>'
    )
    for b in bereinigte_bloecke:
        if b.get("t") == "fold":
            attrs = dict(b.get("attrs", []))
            if attrs.get("id") == guide_fold_id:
                fold_blocks = [fb for fb in b.get("blocks", []) if "ai-commentary-actions" not in fb.get("html", "")]
                fold_blocks.append({"t": "html", "html": guide_actions_html, "tail": "\n"})
                b["blocks"] = fold_blocks

    # Füge das Modal als reinen, unsichtbaren HTML-Block am Ende ein
    modal_block = {
        "t": "html",
        "html": dossier_html,
        "tail": "\n"
    }
    bereinigte_bloecke.append(modal_block)

    seite["main"] = bereinigte_bloecke
    with open(seiten_datei, "w", encoding="utf-8") as f:
        json.dump(seite, f, ensure_ascii=False, indent=1)
        f.write("\n")

    LOG.info("Seitenmodell aktualisiert: Modal eingebettet (kein Fold/DIV im Fließtext): %s", seiten_datei)
    return seiten_datei


def kuratierte_linif_snippets() -> List[Dict[str, Any]]:
    """Erzeugt das kuratierte Set verifizierter Inbound-Snippets für LinIf."""
    jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snippets = [
        {
            "id": "SNIP_LinIf_LinSM_ScheduleRequest_01",
            "target_module": "LinIf",
            "source_document": "AUTOSAR_SWS_LINStateManager",
            "source_page": 27,
            "source_element": "SWS_LinSM_00079",
            "category": "inbound_call",
            "concept_tags": ["schedule_table", "lin_master", "inbound_call"],
            "relevance_score": 0.98,
            "relevance_rationale": "Verbindliche Festlegung, dass LinSM Schedule-Wechsel sofort an LinIf_ScheduleRequest delegiert.",
            "verbatim_text": "[SWS_LinSM_00079] If the function LinSM_ScheduleRequest is called, the LinSM module shall forward (and not wait for the next main function call) the request to the LinIf module using the function call LinIf_ScheduleRequest.",
            "sha256": sha256_text("[SWS_LinSM_00079] If the function LinSM_ScheduleRequest is called, the LinSM module shall forward (and not wait for the next main function call) the request to the LinIf module using the function call LinIf_ScheduleRequest."),
            "captured_at": jetzt,
        },
        {
            "id": "SNIP_LinIf_LinSM_GotoSleep_02",
            "target_module": "LinIf",
            "source_document": "AUTOSAR_SWS_LINStateManager",
            "source_page": 26,
            "source_element": "SWS_LinSM_00036",
            "category": "inbound_call",
            "concept_tags": ["power_management", "sleep_mode", "inbound_call"],
            "relevance_score": 0.95,
            "relevance_rationale": "Spezifiziert den synchronen Aufruf von LinIf_GotoSleep bei Übergang in COMM_NO_COMMUNICATION.",
            "verbatim_text": "[SWS_LinSM_00036] If the ComM module calls LinSM_RequestComMode requesting COMM_NO_COMMUNICATION the LinSM module shall directly call (and not wait for next main function call) the LinIf module function LinIf_GotoSleep on the specified network.",
            "sha256": sha256_text("[SWS_LinSM_00036] If the ComM module calls LinSM_RequestComMode requesting COMM_NO_COMMUNICATION the LinSM module shall directly call (and not wait for next main function call) the LinIf module function LinIf_GotoSleep on the specified network."),
            "captured_at": jetzt,
        },
        {
            "id": "SNIP_LinIf_PduR_Transmit_03",
            "target_module": "LinIf",
            "source_document": "AUTOSAR_SWS_PDURouter",
            "source_page": 122,
            "source_element": "Table 11.3.1",
            "category": "routing_contract",
            "concept_tags": ["pdu_router", "sporadic_frame", "trigger_transmit"],
            "relevance_score": 0.92,
            "relevance_rationale": "Dokumentiert die Schnittstelle zwischen PduR und LinIf_Transmit für sporadische LIN-Frames.",
            "verbatim_text": "Routing table entry: TargetFctPtr: LinIf_Transmit. Description: Multicast using CanIf and LinIf. Note that for LinIf this is a sporadic frame (will later be a TriggerTransmit call).",
            "sha256": sha256_text("Routing table entry: TargetFctPtr: LinIf_Transmit. Description: Multicast using CanIf and LinIf. Note that for LinIf this is a sporadic frame (will later be a TriggerTransmit call)."),
            "captured_at": jetzt,
        },
        {
            "id": "SNIP_LinIf_PduR_Confirmation_04",
            "target_module": "LinIf",
            "source_document": "AUTOSAR_SWS_PDURouter",
            "source_page": 31,
            "source_element": "Section 7.x",
            "category": "callback_requirement",
            "concept_tags": ["tx_confirmation", "pdu_router", "callback"],
            "relevance_score": 0.90,
            "relevance_rationale": "Bestätigt die Callback-Pflicht des LinIf gegenüber dem PduR nach erfolgreichem Frame-Versand.",
            "verbatim_text": "Example: The LinIf will call PduR_LinIfTxConfirmation upon successful completion of the frame transmission on the physical bus.",
            "sha256": sha256_text("Example: The LinIf will call PduR_LinIfTxConfirmation upon successful completion of the frame transmission on the physical bus."),
            "captured_at": jetzt,
        },
        {
            "id": "SNIP_LinIf_LinDriver_Wakeup_05",
            "target_module": "LinIf",
            "source_document": "AUTOSAR_SWS_LINDriver",
            "source_page": 44,
            "source_element": "SWS_Lin_00098",
            "category": "driver_interaction",
            "concept_tags": ["hardware_abstraction", "mcu_wakeup", "driver_contract"],
            "relevance_score": 0.94,
            "relevance_rationale": "Beschreibt die Rollenverteilung zwischen LinIf und Lin Driver bei Transceiver-Wakeup-Signalen.",
            "verbatim_text": "[SWS_Lin_00098] After a wake up caused by LIN bus Transceiver the function Lin_CheckWakeup will be called by the LIN Interface module to identify the corresponding LIN channel (see SWS_LinIf_00503). In this case, LIN Driver only plays a role on validation of this wake up signal.",
            "sha256": sha256_text("[SWS_Lin_00098] After a wake up caused by LIN bus Transceiver the function Lin_CheckWakeup will be called by the LIN Interface module to identify the corresponding LIN channel (see SWS_LinIf_00503). In this case, LIN Driver only plays a role on validation of this wake up signal."),
            "captured_at": jetzt,
        },
        {
            "id": "SNIP_LinIf_Arch_Concept_06",
            "target_module": "LinIf",
            "source_document": "AUTOSAR_EXP_LayeredSoftwareArchitecture",
            "source_page": 44,
            "source_element": "Document ID 53, Page 44",
            "category": "conceptual_architecture",
            "concept_tags": ["tdma", "schedule_slot", "just_in_time", "layered_architecture"],
            "relevance_score": 0.96,
            "relevance_rationale": "Grundlegendes Architekturkonzept: Erklärt, warum LinIf Daten erst unmittelbar vor dem Slot abruft.",
            "verbatim_text": "Integration of LIN into AUTOSAR: LIN Interface controls the WakeUp/Sleep API and allows the slaves to keep the bus awake (decentralized approach). When sending a LIN frame, the LIN Interface requests the data for the frame (I-PDU) from the PDU Router at the point in time when it requires the data (i.e. right before sending the LIN frame).",
            "sha256": sha256_text("Integration of LIN into AUTOSAR: LIN Interface controls the WakeUp/Sleep API and allows the slaves to keep the bus awake (decentralized approach). When sending a LIN frame, the LIN Interface requests the data for the frame (I-PDU) from the PDU Router at the point in time when it requires the data (i.e. right before sending the LIN frame)."),
            "captured_at": jetzt,
        }
    ]
    return snippets


def erstelle_cluster_dossier(cluster_name: str = "lin", plattform: str = "classic") -> Tuple[Path, Dict[str, Any]]:
    """Assembliert das vollständige, reproduzierbare Agenten-Kontext-Dossier für einen Cluster."""
    cluster_cfg = CLASSIC_CLUSTERS.get(cluster_name.lower())
    if not cluster_cfg:
        raise ValueError(f"Unbekannter Cluster: {cluster_name}")

    cluster_title = cluster_cfg["title"]
    cluster_modules_info = cluster_cfg["modules"]

    # 1. Spezifikations-Records aller Module im Cluster aggregieren
    all_spec_records = []
    extracted_records = []

    for mod_name, doc_name in cluster_modules_info:
        rec_datei = _SRC_DIR / "spec" / "records" / plattform / "modules" / f"{mod_name}.json"
        if rec_datei.exists():
            with open(rec_datei, "r", encoding="utf-8") as f:
                rec_data = json.load(f)
                blocks = rec_data.get("blocks", [])
                all_spec_records.extend(blocks)
                mod_extracted = extrahiere_spec_records(blocks, module_name=mod_name, doc_name=doc_name)
                extracted_records.extend(mod_extracted)

    # 2. Pinned Inbound-Snippets für Cluster laden
    snippets_datei = SNIPPETS_DIR / plattform / "clusters" / f"{cluster_name.lower()}.json"
    inbound_snippets = []
    if snippets_datei.exists():
        with open(snippets_datei, "r", encoding="utf-8") as f:
            snip_data = json.load(f)
            for snip in snip_data.get("snippets", []):
                snip["dismissed"] = dg.is_dismissed(snip.get("id", ""))
                inbound_snippets.append(snip)

    # 3. Quellenregister-Metadaten für alle berührten Quellen sammeln
    alle_quellen = lade_quellen()
    beteiligte_quellen_ids = sorted(list(
        {s["source_document"] for s in inbound_snippets} |
        {doc_name for _, doc_name in cluster_modules_info}
    ))
    quellen_meta = {qid: alle_quellen.get(qid, {"titel": qid, "typ": "SWS"}) for qid in beteiligte_quellen_ids}

    # 4. Modell- & Ausführungsparameter laden
    policy = lade_policy()
    modell_cfg = policy.get("modell", {})
    primaer = modell_cfg.get("primaer", {})

    execution_params = {
        "model": primaer.get("modell", modell_cfg.get("erklaerungen", "gemini-3.8-flash-high")),
        "display_name": primaer.get("display_name", "Gemini 3.8 Flash (High)"),
        "thinking_effort": primaer.get("thinking_effort", "high"),
        "temperature": primaer.get("temperature", 0.0),
        "reproducible_mode": True,
    }

    # 5. Cluster-Dossier zusammenstellen
    frag_path = _SRC_DIR / "content" / "ai" / plattform / "clusters" / cluster_name.lower() / "main_01.html"
    bisheriges_frag = frag_path.read_text(encoding="utf-8") if frag_path.exists() else ""

    dossier_content: Dict[str, Any] = {
        "dossier_version": "1.1",
        "target_cluster": cluster_title,
        "is_cluster": True,
        "cluster_name": cluster_name.lower(),
        "cluster_modules": [m[0] for m in cluster_modules_info],
        "platform": plattform,
        "assembled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution_parameters": execution_params,
        "reproducibility": {
            "policy_version": policy.get("version", 1),
            "model": execution_params["model"],
            "display_name": execution_params["display_name"],
            "thinking_effort": execution_params["thinking_effort"],
            "temperature": execution_params["temperature"],
            "spec_record_count": len(extracted_records),
            "inbound_snippet_count": len(inbound_snippets),
            "source_documents": beteiligte_quellen_ids,
        },
        "spec_records": all_spec_records,
        "extracted_records": extracted_records,
        "inbound_snippets": inbound_snippets,
        "quellen_register": quellen_meta,
        "bisheriges_fragment": bisheriges_frag,
    }

    # Hash über kanonische Serialisierung bilden
    kanonisch_json = json.dumps(dossier_content, sort_keys=True, ensure_ascii=False)
    dossier_digest = hashlib.sha256(kanonisch_json.encode("utf-8")).hexdigest()
    dossier_content["dossier_sha256"] = dossier_digest

    ziel_dir = DOSSIERS_DIR / plattform / "clusters"
    ziel_dir.mkdir(parents=True, exist_ok=True)
    ziel_datei = ziel_dir / f"{cluster_name.lower()}.json"

    with open(ziel_datei, "w", encoding="utf-8") as f:
        json.dump(dossier_content, f, ensure_ascii=False, indent=2)
        f.write("\n")

    LOG.info("Cluster-Agenten-Dossier geschrieben: %s (SHA: %s)", ziel_datei, dossier_digest[:12])
    return ziel_datei, dossier_content


def aktualisiere_seitenmodell_mit_cluster_dossier(cluster_name: str, dossier_html: str, plattform: str = "classic") -> Path:
    """Fügt den Cluster Guide Fold und das Dossier-Modal in das Cluster-Seitenmodell ein."""
    cluster_key = cluster_name.lower()
    seiten_datei = PAGES_DIR / plattform / f"{cluster_key}.json"
    if not seiten_datei.exists():
        raise FileNotFoundError(f"Cluster-Seitenmodell nicht gefunden: {seiten_datei}")

    with open(seiten_datei, "r", encoding="utf-8") as f:
        seite = json.load(f)

    haupt_bloecke = seite.get("main", [])
    fold_id = f"ai-cluster-guide-{cluster_key}"
    modal_id = f"dossier-modal-cluster-{cluster_key}"

    cluster_actions_html = (
        f'<div class="ai-commentary-actions">\n'
        f'  <button type="button" class="btn-discuss-ai" data-open-discuss="{fold_id}" title="Cluster-Guide und Diagramm mit KI diskutieren">💬 Mit KI diskutieren</button>\n'
        f'  <button type="button" class="btn-feedback-action" data-feedback-open data-target-id="Cluster Guide: {cluster_name.upper()}" title="Fehler, Mangel oder Halluzination im Guide melden">⚠️ Feedback melden</button>\n'
        f'  <button type="button" class="btn-curate-link dossier-open-link" data-dossier-target="{modal_id}" title="Audit-Dossier, Nachweise und Prompt-Kuration öffnen">🛠️ Audit-Dossier &amp; Kuration</button>\n'
        f'  <button type="button" class="btn-curate-link" data-review-open title="Review-Paket (GitHub-Issue / JSON) öffnen">📦 Review-Paket</button>\n'
        f'</div>'
    )

    cluster_fold = {
        "t": "fold",
        "attrs": [
            ["class", "fold"],
            ["id", fold_id]
        ],
        "summary": '<h2 class="sect">Cluster Guide <span class="ai-badge" title="AI generated">KI-generiert / AI generated</span></h2>',
        "lead": "",
        "blocks": [
            {
                "t": "ai",
                "src": f"content/ai/{plattform}/clusters/{cluster_key}/main_01.html",
                "tail": "\n"
            },
            {
                "t": "html",
                "html": cluster_actions_html,
                "tail": "\n"
            }
        ],
        "tail": "\n"
    }

    modal_block = {
        "t": "html",
        "html": dossier_html,
        "tail": "\n"
    }

    # Bereinige alte Folds und Modals
    bereinigte = []
    for b in haupt_bloecke:
        if b.get("t") == "fold":
            attrs = dict(b.get("attrs", []))
            if attrs.get("id") == fold_id or "ai-cluster-guide" in attrs.get("id", ""):
                continue
        if b.get("t") == "html" and modal_id in b.get("html", ""):
            continue
        bereinigte.append(b)

    neue_bloecke = []
    fold_eingefuegt = False

    for b in bereinigte:
        if b.get("t") == "html" and '<h2 class="sect">Module im Cluster</h2>' in b.get("html", ""):
            html_text = b["html"]
            parts = html_text.split('<h2 class="sect">Module im Cluster</h2>')
            if len(parts) == 2:
                if parts[0].strip():
                    neue_bloecke.append({"t": "html", "html": parts[0].strip(), "tail": "\n"})
                neue_bloecke.append(cluster_fold)
                fold_eingefuegt = True
                neue_bloecke.append({"t": "html", "html": '<h2 class="sect">Module im Cluster</h2>' + parts[1], "tail": "\n"})
                continue
        neue_bloecke.append(b)

    if not fold_eingefuegt:
        if len(neue_bloecke) > 1:
            neue_bloecke.insert(2, cluster_fold)
        else:
            neue_bloecke.append(cluster_fold)

    neue_bloecke.append(modal_block)

    seite["main"] = neue_bloecke
    with open(seiten_datei, "w", encoding="utf-8") as f:
        json.dump(seite, f, ensure_ascii=False, indent=1)
        f.write("\n")

    LOG.info("Cluster-Seitenmodell aktualisiert: Fold und Modal eingebettet in %s", seiten_datei)
    return seiten_datei


def main():
    parser = argparse.ArgumentParser(
        description="Distributionslauf für gepinnte Inbound-Referenzen und Agenten-Kontexte."
    )
    parser.add_argument("--module", default="LinIf", help="Name des Zielmoduls (Standard: LinIf)")
    parser.add_argument("--cluster", default=None, help="Name des Zielclusters (z. B. lin)")
    parser.add_argument("--platform", default="classic", help="Plattform (classic/adaptive)")
    parser.add_argument("--action", choices=["extract", "pin", "dossier", "render", "all"], default="all",
                        help="Auszuführende Aktion (Standard: all)")
    parser.add_argument("--update-page", action="store_true", default=True,
                        help="Aktualisiert das Seitenmodell für menschliche Browsbarkeit im Frontend")

    args = parser.parse_args()

    plattform = args.platform

    if args.cluster:
        cl_name = args.cluster.lower()
        print(f"=== Starte Kontext-Distributionslauf für Cluster {cl_name.upper()} ({plattform}) ===")
        dossier_pfad, dossier = erstelle_cluster_dossier(cl_name, plattform=plattform)
        dossier_html = generiere_dossier_html(dossier)
        if args.update_page:
            aktualisiere_seitenmodell_mit_cluster_dossier(cl_name, dossier_html, plattform=plattform)
        print("=== Cluster-Distributionslauf erfolgreich abgeschlossen ===")
        return

    modul = args.module
    print(f"=== Starte Kontext-Distributionslauf für {modul} ({plattform}) ===")

    if args.action in ("extract", "pin", "all"):
        if modul.lower() == "linif":
            snippets = kuratierte_linif_snippets()
        else:
            snippets = extrahiere_snippets_fuer_modul(modul, [f"{modul}_", modul], [])
        speichere_snippets(modul, snippets, plattform=plattform)

    if args.action in ("dossier", "all"):
        dossier_pfad, dossier = erstelle_agenten_dossier(modul, plattform=plattform)
        dossier_html = generiere_dossier_html(dossier)

        if args.update_page:
            aktualisiere_seitenmodell_mit_dossier(modul, dossier_html, plattform=plattform)

    print("=== Distributionslauf erfolgreich abgeschlossen ===")


if __name__ == "__main__":
    main()
