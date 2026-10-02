#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""curation_ingest.py — Kurationsentscheidungen aus dem Extraktionsbericht uebernehmen.

Der Extraktionsbericht (``extraction_report.py``) zeigt am Seitenanfang
Kurationsanfragen: Faelle, die die Extraktion nicht automatisch entscheiden
konnte, mit Screenshot, aktuellem Extraktionsergebnis und einer
Klartext-Erklaerung, was heute passiert und welche Entscheidung gefragt ist.
Die Person, die den Bericht liest, entscheidet im selben Review-Widget wie
bei normalen Requirement-Reviews (``review.js``) und sendet das Paket als
GitHub-Issue ab — nur mit ``kind: "curation_request"`` statt
``requirement_text``.

Dieses Werkzeug liest ein solches Paket (als JSON-Export ODER direkt aus
einem GitHub-Issue-Body, siehe ``--issue-body``) und legt fuer jede
Entscheidung ein Flag in ``spec/curation-queue/open/`` an
(``curation_flags.write_curation_flag``). Von dort holt sich ein KI-Agent
die Anfrage, schlaegt eine konkrete, belegte Aenderung vor (Diff oder neuer
``RESIDUAL``-Eintrag) und legt sie als Review vor. Angewandt wird sie NICHT
automatisch: Die Person, die die Extraktionsskripte betreibt, hat die letzte
Entscheidung und ruft danach manuell ``curation_flags.complete_flag()`` auf.

Aufruf (immer vom Repo-Wurzelverzeichnis)
-----------------------------------------
    python3 _src/tools/curation_ingest.py --check paket.json
    python3 _src/tools/curation_ingest.py --apply paket.json
    python3 _src/tools/curation_ingest.py --apply --issue-body issue-42.md

Exit-Code 1 bei Formatfehlern.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import curation_flags as cf

PACKAGE_SCHEMA = "review-package@v1"
VALID_OUTCOMES = ("accept", "reject")
VALID_IDENTITY = ("github_authenticated", "self_declared")

CODE_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


CURATOR_ENVELOPE_SCHEMA = "curator-decision-envelope@v1"
CURATOR_VALID_OUTCOMES = ("accept", "reject", "request_revision")
DECISION_KEY_RE = re.compile(r"^decision:[^:]+:[^:]+$")

from canonical_id import parse_canonical_id  # noqa: E402 (0006-02 propagation)


def validate_curator_envelope(envelope: dict, current_baseline_digest: str | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if envelope.get("schema") != CURATOR_ENVELOPE_SCHEMA:
        errors.append(f"unbekanntes Schema: {envelope.get('schema')!r}")
        return errors, warnings

    decision_key = envelope.get("decision_key")
    if not decision_key or not DECISION_KEY_RE.match(str(decision_key)):
        errors.append(f"ungueltiges decision_key Format: {decision_key!r}")

    proposal_id = envelope.get("proposal_id")
    if not proposal_id or not str(proposal_id).strip():
        errors.append("proposal_id fehlt oder ist leer")

    baseline_digest = envelope.get("baseline_digest")
    if not baseline_digest or not str(baseline_digest).strip():
        errors.append("baseline_digest fehlt oder ist leer")
    elif current_baseline_digest and baseline_digest != current_baseline_digest:
        errors.append(f"baseline_digest veraltet/stale: {baseline_digest} != {current_baseline_digest}")

    curator = envelope.get("curator")
    if not isinstance(curator, dict) or not curator.get("identity"):
        errors.append("curator.identity fehlt oder ist leer")
    elif curator.get("auth_mode") == "self_declared":
        warnings.append("Nicht authentifizierte Curator-Entscheidung (self_declared)")

    decision = envelope.get("decision")
    if not isinstance(decision, dict):
        errors.append("decision Block fehlt")
    else:
        outcome = decision.get("outcome")
        if outcome not in CURATOR_VALID_OUTCOMES:
            errors.append(f"ungueltiges outcome: {outcome!r}, muss eins von {CURATOR_VALID_OUTCOMES} sein")
        if not decision.get("rationale") or not str(decision.get("rationale")).strip():
            errors.append("decision.rationale fehlt oder ist leer")

    return errors, warnings


def load_package(pfad: Path, from_issue_body: bool) -> dict:
    raw = pfad.read_text(encoding="utf-8")
    if from_issue_body:
        m = CODE_FENCE_RE.search(raw)
        if not m:
            raise ValueError("Kein ```json ...``` Block im Issue-Body gefunden")
        raw = m.group(1)
    return json.loads(raw)


def validate_package(paket: dict) -> list:
    fehler = []
    if paket.get("schema") != PACKAGE_SCHEMA:
        fehler.append("unbekanntes Paket-Schema: %r" % paket.get("schema"))
    if paket.get("identity") not in VALID_IDENTITY:
        fehler.append("unbekannte identity: %r" % paket.get("identity"))
    decisions = [d for d in (paket.get("decisions") or [])
                 if d.get("kind") == "curation_request"]
    if not decisions:
        fehler.append("Paket enthaelt keine Kurationsanfragen (kind=curation_request)")
        return fehler
    for i, d in enumerate(decisions):
        wo = "decisions[%d]" % i
        for feld in ("id", "outcome", "decided_by", "decided_at", "rationale"):
            if not str(d.get(feld) or "").strip():
                fehler.append("%s: Feld %s fehlt oder ist leer" % (wo, feld))
        if d.get("outcome") not in VALID_OUTCOMES:
            fehler.append("%s: outcome muss accept oder reject sein" % wo)
    return fehler


def ingest(paket_pfad: Path, apply: bool, from_issue_body: bool) -> dict:
    paket = load_package(paket_pfad, from_issue_body)
    bericht = {"paket": str(paket_pfad), "identity": paket.get("identity"),
               "angewandt": apply, "fehler": [], "ergebnisse": []}

    if isinstance(paket, dict) and paket.get("schema") == CURATOR_ENVELOPE_SCHEMA:
        errors, warnings = validate_curator_envelope(paket)
        bericht["schema"] = CURATOR_ENVELOPE_SCHEMA
        bericht["fehler"] = errors
        bericht["warnungen"] = warnings
        bericht["decision_key"] = paket.get("decision_key")
        bericht["proposal_id"] = paket.get("proposal_id")
        bericht["outcome"] = (paket.get("decision") or {}).get("outcome")
        if not errors:
            bericht["status"] = "ok"
            bericht["routing"] = {
                "pl_offer_required": True,
                "target_recipe": "curator_decision_routing",
                "envelope_bound": True
            }
            bericht["ergebnisse"].append({
                "id": paket.get("target_canonical_id") or paket.get("proposal_id"),
                "status": "ok",
                "decision_key": paket.get("decision_key"),
                "outcome": (paket.get("decision") or {}).get("outcome"),
                "dry_run": not apply,
            })
        else:
            bericht["status"] = "rejected"
            bericht["ergebnisse"].append({
                "id": paket.get("target_canonical_id") or paket.get("proposal_id") or "unknown",
                "status": "rejected",
                "fehler": errors,
            })
        _record_curation_ingest(paket_pfad, bericht)
        return bericht

    if isinstance(paket, dict) and paket.get("schema") == "feedback-recipe-contract@v1":
        import feedback_recipe_contract as frc
        res = frc.consume_feedback_recipe_handoff(paket, apply=apply)
        bericht["schema"] = "feedback-recipe-contract@v1"
        bericht["status"] = res.get("status")
        bericht["queue_item_id"] = res.get("queue_item_id")
        bericht["queue_item_path"] = res.get("queue_item_path")
        bericht["next_event"] = res.get("next_event")
        bericht["fehler"] = res.get("errors", [])
        bericht["warnungen"] = res.get("warnings", [])
        if res.get("status") == frc.FeedbackConsumerOutcome.OK:
            bericht["ergebnisse"].append({
                "id": res.get("target_canonical_id"),
                "status": "ok",
                "pfad": res.get("queue_item_path"),
                "dry_run": not apply,
            })
        else:
            bericht["ergebnisse"].append({
                "id": res.get("target_canonical_id") or "unknown",
                "status": res.get("status"),
                "fehler": res.get("errors", []),
            })
        _record_curation_ingest(paket_pfad, bericht)
        return bericht

    bericht["fehler"] = validate_package(paket)
    if bericht["fehler"]:
        _record_curation_ingest(paket_pfad, bericht)
        return bericht

    if paket["identity"] == "self_declared":
        bericht.setdefault("warnungen", []).append(
            "Nicht authentifiziertes Paket: decided_by ist Selbstauskunft. "
            "Die Betreiberin/der Betreiber sollte das vor dem Merge inhaltlich pruefen.")

    decisions = [d for d in paket["decisions"] if d.get("kind") == "curation_request"]
    for _d in decisions:
        _parsed = parse_canonical_id(_d.get("id", ""))
        if _parsed is not None:
            _d["id"] = _parsed["id"]
            _d["project"], _d["kind_project"] = _parsed["project"], _parsed["kind"]
    for d in decisions:
        if not apply:
            bericht["ergebnisse"].append({"id": d["id"], "status": "ok", "dry_run": True})
            continue
        pfad = cf.write_curation_flag(d, campaign=paket.get("campaign") or "html-curation")
        if pfad is None:
            bericht["ergebnisse"].append(
                {"id": d["id"], "status": "skipped",
                 "grund": "bereits eine offene Kurationsanfrage fuer diese ID"})
        else:
            bericht["ergebnisse"].append({"id": d["id"], "status": "ok", "pfad": str(pfad)})
    _record_curation_ingest(paket_pfad, bericht)
    return bericht


def _record_curation_ingest(paket_pfad: Path, bericht: dict) -> None:
    """Write a universal mutation receipt; ingest itself must still succeed."""
    tools_dir = str(Path(__file__).resolve().parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import mutation_ledger as mutation_audit
    except ImportError:
        return
    outputs = []
    for row in bericht.get("ergebnisse") or []:
        pfad = row.get("pfad") or row.get("queue_item_path")
        if pfad:
            outputs.append(pfad)
    errors = bericht.get("fehler") or []
    try:
        mutation_audit.record_mutation(
            "curation-ingest",
            str(bericht.get("identity") or "curation-ingest"),
            {
                "paket": str(paket_pfad),
                "angewandt": bericht.get("angewandt"),
                "status": bericht.get("status"),
                "schema": bericht.get("schema"),
                "ergebnisse": len(bericht.get("ergebnisse") or []),
                "fehler": errors,
            },
            inputs=[paket_pfad] if Path(paket_pfad).is_file() else None,
            outputs=outputs or None,
            success=not errors,
            root=mutation_audit.discover_root(paket_pfad),
            metadata={"source": "curation_ingest.py"},
        )
    except Exception:
        return


def ingest_queue_snippets(apply: bool = False) -> dict:
    """Scans spec/curation-queue/open for snippet proposals and processes them into the dependency graph."""
    import dependency_graph as dg

    open_flags = cf.list_open_flags()
    results = []
    for flag_path in open_flags:
        try:
            payload = json.loads(flag_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        rid = str(payload.get("target_record") or payload.get("id") or "")
        is_snippet = payload.get("item_kind") == "evidence-snippet" or rid.startswith("SNIP_")
        if not is_snippet:
            continue

        outcome = payload.get("outcome")
        rationale = payload.get("rationale") or "Curation proposal ingested"
        if not apply:
            results.append({
                "id": rid,
                "path": str(flag_path),
                "status": "dry_run",
                "action": "would_dismiss" if outcome in ("proposed_change", "reject") else "would_confirm",
            })
        else:
            if outcome in ("proposed_change", "reject"):
                dg.dismiss_node(rid, reason=rationale)
                dg.add_edge("curation_ingest", rid, "dismisses", meta={"proposal_file": flag_path.name, "rationale": rationale})
                completed = cf.complete_flag(flag_path, note=f"Ingested snippet proposal: {rationale}", outcome_class="no_action")
                results.append({
                    "id": rid,
                    "path": str(completed),
                    "status": "dismissed",
                    "action": "dismissed_and_completed",
                })
            elif outcome == "accept":
                dg.add_edge("curation_ingest", rid, "confirms", meta={"proposal_file": flag_path.name, "rationale": rationale})
                completed = cf.complete_flag(flag_path, note=f"Confirmed snippet: {rationale}", outcome_class="no_action")
                results.append({
                    "id": rid,
                    "path": str(completed),
                    "status": "confirmed",
                    "action": "confirmed_and_completed",
                })

    bericht = {
        "paket": "spec/curation-queue/open (snippets)",
        "identity": "curation_ingest--snippets",
        "angewandt": apply,
        "status": "ok",
        "fehler": [],
        "warnungen": [],
        "snippets_processed": len(results),
        "ergebnisse": results,
    }
    _record_curation_ingest(Path("spec/curation-queue/open"), bericht)
    return bericht


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paket", nargs="?", type=Path, default=None, help="Review-Paket (JSON) oder Issue-Body (mit --issue-body)")
    ap.add_argument("--snippets", action="store_true", help="Offene Snippet-Kurationsanträge aus spec/curation-queue/open verarbeiten")
    ap.add_argument("--apply", action="store_true", help="Flags anlegen/übernehmen (Standard: nur pruefen)")
    ap.add_argument("--issue-body", action="store_true",
                    help="Eingabedatei ist ein GitHub-Issue-Body mit ```json ...``` Block")
    ap.add_argument("--json", action="store_true", help="Bericht als JSON")
    args = ap.parse_args(argv)

    if args.snippets or args.paket is None:
        if args.paket is None and not args.snippets:
            ap.error("Entweder ein Paket-Pfad oder --snippets angeben")
        bericht = ingest_queue_snippets(apply=args.apply)
    else:
        bericht = ingest(args.paket, args.apply, args.issue_body)

    if args.json:
        print(json.dumps(bericht, ensure_ascii=False, indent=1))
    else:
        print("Paket:    %s (%s)" % (bericht["paket"], bericht.get("identity")))
        for w in bericht.get("warnungen", []):
            print("WARNUNG:  %s" % w)
        for f in bericht["fehler"]:
            print("FEHLER:   %s" % f)
        for r in bericht["ergebnisse"]:
            print("%-9s %s%s" % (r["status"], r["id"],
                                  (" -> %s" % r["path"]) if r.get("path") else ((" -> %s" % r["pfad"]) if r.get("pfad") else "")))
        print("%d Kurationsanfragen, %s"
              % (len(bericht["ergebnisse"]), "angelegt/übernommen" if bericht["angewandt"] else "nur geprueft"))

    return 1 if bericht["fehler"] else 0


if __name__ == "__main__":
    sys.exit(main())
