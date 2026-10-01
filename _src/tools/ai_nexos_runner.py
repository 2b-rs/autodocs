#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ai_nexos_runner.py — Führt KI-Regenerierungsaufträge über das Nexos.ai-Gateway (Hostinger) aus.

Verbindet den autodocs-Kurations-Workflow (_src/ai_workflow.py) mit der
OpenAI-kompatiblen Nexos.ai-API (https://api.nexos.ai/v1).

Aufruf:
  python3 _src/tools/ai_nexos_runner.py --auftrag _src/ai/work/auftrag_001.json
  python3 _src/tools/ai_nexos_runner.py --target classic/modules/canif.html
  python3 _src/tools/ai_nexos_runner.py --target SWS_CANIF_00001 --model claude-3-5-sonnet
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "_src"
AI_DIR = SRC / "ai"
WORK_DIR = AI_DIR / "work"

DEFAULT_BASE_URL = "https://api.nexos.ai/v1"
DEFAULT_MODEL = "gpt-4o"


def call_nexos_chat_completion(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    temperature: float = 0.2,
) -> str:
    """Sendet einen Chat-Completion-Request an die Nexos.ai API."""
    key = api_key or os.environ.get("NEXOS_API_KEY")
    if not key:
        raise ValueError(
            "NEXOS_API_KEY ist erforderlich. Setze die Umgebungsvariable NEXOS_API_KEY "
            "oder übergib --api-key."
        )

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "autodocs-ai-runner/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            choices = res_json.get("choices", [])
            if not choices:
                raise RuntimeError(f"Keine Antwort-Choices von Nexos.ai erhalten: {body}")
            content = choices[0].get("message", {}).get("content", "")
            return content
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Nexos API HTTP Fehler {e.code}: {e.reason}\nDetails: {err_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Verbindungsfehler zu Nexos.ai ({url}): {e.reason}")


def build_system_prompt(policy: Dict[str, Any], richtlinien: str, ausgabeformat: str) -> str:
    """Erstellt den System-Prompt inklusive Richtlinien und Ausgabeformat."""
    return f"""Du bist der offizielle KI-Kurations-Assistent für das autodocs Dokumentations- und Spezifikationssystem (AUTOSAR & S-Core).
Deine Aufgabe ist es, präzise, fachlich fundierte Erklärungen, User Guides und Diagramme zu verfassen.

FOLGENDE RICHTLINIEN SIND STRIKT BINDEND:
{richtlinien}

POLICY-PARAMETER:
{json.dumps(policy, ensure_ascii=False, indent=2)}

ERWARTETES AUSGABEFORMAT:
Antworte AUSSCHLIESSLICH im validen JSON-Format gemäß folgendem Schema:
{ausgabeformat}
"""


def extract_json_response(raw_text: str) -> Dict[str, Any]:
    """Extrahiert ein JSON-Objekt aus der Antwort des Modells."""
    raw = raw_text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def process_auftrag(
    auftrag_path: Path,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    dry_run: bool = False,
) -> Path:
    """Bearbeitet eine auftrag_NNN.json Datei und erzeugt auftrag_NNN.out.json."""
    with open(auftrag_path, "r", encoding="utf-8") as f:
        auftrag_data = json.load(f)

    system_prompt = build_system_prompt(
        auftrag_data.get("policy", {}),
        auftrag_data.get("richtlinien", ""),
        auftrag_data.get("ausgabeformat", ""),
    )

    auftraege = auftrag_data.get("auftraege", [])
    print(f"[{auftrag_path.name}] Verarbeite {len(auftraege)} Fragmente mit Modell {model}...")

    ergebnisse = []
    for idx, item in enumerate(auftraege, start=1):
        frag = item.get("fragment")
        print(f"  ({idx}/{len(auftraege)}) Generiere Inhalt für: {frag}")

        user_content = json.dumps(item, ensure_ascii=False, indent=2)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Bitte bearbeite folgenden Auftrag und liefere das geforderte Ergebnis:\n{user_content}",
            },
        ]

        if dry_run:
            print("    [DRY RUN] Request vorbereitet. Überspringe API-Aufruf.")
            continue

        raw_response = call_nexos_chat_completion(
            messages=messages,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

        parsed = extract_json_response(raw_response)
        if "ergebnisse" in parsed:
            ergebnisse.extend(parsed["ergebnisse"])
        else:
            ergebnisse.append(parsed)

    out_path = auftrag_path.with_name(auftrag_path.name.replace(".json", ".out.json"))
    if not dry_run:
        out_data = {"ergebnisse": ergebnisse}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"Ausgabe geschrieben: {out_path}")

    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Führt KI-Regenerierungsaufträge über das Nexos.ai Gateway aus."
    )
    parser.add_argument("--auftrag", help="Pfad zu einer bestehenden auftrag_*.json Datei")
    parser.add_argument(
        "--target",
        help="Ziel (Fragment, Seitendatei wie classic/modules/canif.html, oder Element-ID)",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"Modell auf Nexos.ai (Default: {DEFAULT_MODEL})"
    )
    parser.add_argument("--api-key", help="Nexos.ai API Key (alternativ NEXOS_API_KEY Env-Var)")
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL, help=f"Nexos API URL (Default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Auftrag vorbereiten und Prompt anzeigen, aber keinen API-Aufruf durchführen",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        default=True,
        help="Nach erfolgreicher Generierung automatisch ai_workflow.py merge ausführen",
    )
    args = parser.parse_args()

    # 1. Auftrag bestimmen oder neu anlegen
    auftrag_file = None
    if args.auftrag:
        auftrag_file = Path(args.auftrag)
        if not auftrag_file.is_absolute():
            auftrag_file = ROOT / auftrag_file
    elif args.target:
        # ai_workflow.py auftrag aufrufen
        import subprocess

        cmd = [sys.executable, str(SRC / "ai_workflow.py"), "auftrag", args.target]
        print(f"Erzeuge Auftrag für {args.target} via ai_workflow.py...")
        subprocess.run(cmd, cwd=str(ROOT), check=True)

        # Zuletzt erzeugten Auftrag finden
        auftraege = sorted(WORK_DIR.glob("auftrag_*.json"))
        if not auftraege:
            print("Fehler: Kein Auftrag in ai/work/ gefunden.", file=sys.stderr)
            sys.exit(1)
        auftrag_file = auftraege[-1]
    else:
        # Neuesten existierenden Auftrag nehmen
        auftraege = sorted(WORK_DIR.glob("auftrag_*.json"))
        if auftraege:
            auftrag_file = auftraege[-1]
        else:
            print(
                "Kein Auftrag angegeben und keine offenen Aufträge gefunden. Nutze --target oder --auftrag.",
                file=sys.stderr,
            )
            sys.exit(1)

    print(f"Verwende Auftrag: {auftrag_file}")

    # 2. Ausführen
    out_file = process_auftrag(
        auftrag_file,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        dry_run=args.dry_run,
    )

    # 3. Mergen
    if not args.dry_run and args.merge and out_file.exists():
        import subprocess

        print(f"\nSpiele generiertes Ergebnis ein ({SRC / 'ai_workflow.py'} merge)...")
        subprocess.run(
            [sys.executable, str(SRC / "ai_workflow.py"), "merge"], cwd=str(ROOT), check=True
        )


if __name__ == "__main__":
    main()
