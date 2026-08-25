#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arbeitspakete für die Übersetzung der Register erzeugen und zusammenführen.

    python3 i18n_translate.py split <lang> [--kb=40]
        Noch unübersetzte Segmente + Labels der Sprache in JSONL-Pakete
        unter i18n/work/<lang>/batch_NN.jsonl schreiben.
        Zeilenformat: {"id": …, "de": …}   (Label-IDs tragen Präfix "L:")

    python3 i18n_translate.py merge <lang> [--only=batch_NN.out.jsonl]
        Alle oder nur die explizit ausgewählte Antwortdatei unter
        i18n/work/<lang>/ validieren und in die Register
        i18n/<lang>/segments.json + labels.json einarbeiten.
        Zeilenformat der Antwortdateien: {"id": …, "t": …}
        Abgelehnte Zeilen landen in i18n/work/<lang>/fehler.json.

    python3 i18n_translate.py status
        Fortschritt aller Sprachen anzeigen.

    python3 i18n_translate.py issues-extract
    python3 i18n_translate.py issues-split <lang>
    python3 i18n_translate.py issues-merge <lang> --input FILE --translator ID --run-id ID
    python3 i18n_translate.py issues-status
        Öffentliche englische Issue-Titel aus Katalog + Privacy-Projektion
        synchronisieren, Übersetzungsarbeit teilen/zusammenführen und die
        Vollständigkeit aller in site.json konfigurierten Sprachen berichten.

Validierung beim Merge:
  - Platzhalter ⟦k⟧: exakt dieselbe Multimenge wie im Quelltext
  - [SWS_…]/[RS_…]-Kennungen und AUTOSAR_/EXP_/FO_-Dokumentkürzel bleiben erhalten
  - <em>/<strong>-Tags: gleiche Anzahl wie im Quelltext
  - Übersetzung nicht leer und nicht identisch mit Quelle (außer Label ohne
    natürliche Wörter, z. B. reine Symbolfolgen)
"""
import json
import hashlib
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(HERE, "i18n")
WORK = os.path.join(I18N, "work")
sys.path.insert(0, HERE)
from lib_docmodel import LANGS

REPORTS_DIR = os.path.join(HERE, "..", "output", "build-reports")
SITE_PATH = os.path.join(HERE, "site.json")
PUBLIC_ISSUES_PATH = os.path.join(HERE, "data", "issue-graph-public.json")
CATALOG_PATH = os.path.join(HERE, "..", "issues", "_views", "catalog.json")
ISSUE_SCHEMA = "issue-title-translations@v1"
ISSUE_SOURCE_LOCALE = "en"
ISSUE_STATUSES = {"canonical", "pending", "translated", "stale"}


def _write_report(report_kind, tool, command, inputs, started_at, exit_code,
                   changed_artifacts, counts, findings):
    """Emit a build-report JSON conforming to docs/pipeline/build-report-schema.md."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    finished_at = time.time()
    report = {
        "schema_version": "1.0",
        "report_kind": report_kind,
        "tool": tool,
        "command": command,
        "inputs": inputs,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at)),
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(finished_at)),
        "duration_s": round(finished_at - started_at, 3),
        "exit_code": exit_code,
        "changed_artifacts": changed_artifacts,
        "counts": counts,
        "findings": findings,
        "run_archive_ref": os.environ.get("RUN_ARCHIVE_REF"),
    }
    fname = "%s-%d.json" % (report_kind, int(finished_at))
    with open(os.path.join(REPORTS_DIR, fname), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return report

_PH = re.compile(r"\u27e6\d+\u27e7")
_IDS = re.compile(
    r"\[(?:SWS|RS)_[A-Za-z]+_\d+\]|\b(?:AUTOSAR|EXP|FO)_[A-Za-z0-9]+\b"
)
_TAGS = re.compile(r"</?(em|strong|i|u|sub|sup)\b")


def _lade(p, default):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as stream:
        return json.load(stream)


def configured_issue_languages(site_path=SITE_PATH):
    site = _lade(site_path, {})
    languages = site.get("sprachen", {})
    canonical, targets = languages.get("kanonisch"), languages.get("ziele")
    if not isinstance(canonical, str) or not canonical:
        raise ValueError("site.json: sprachen.kanonisch fehlt")
    if not isinstance(targets, list) or not all(isinstance(v, str) and v for v in targets):
        raise ValueError("site.json: sprachen.ziele ist ungültig")
    result = []
    for language in [canonical] + targets:
        if language in result:
            raise ValueError("site.json: doppelte Sprache %s" % language)
        result.append(language)
    return result


def _sha256_text(value):
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


_ISSUE_ID = re.compile(r"^\d{4}(?:-\d{2}(?:\.\d{2})?)?$")
_PROTECTED = re.compile(
    r"`[^`\n]+`|\{\{[^{}\n]+\}\}|\{[A-Za-z_][A-Za-z0-9_.-]*\}|"
    r"⟦\d+⟧|%(?:\([^)]+\))?[a-zA-Z]|\$[A-Za-z_][A-Za-z0-9_]*|"
    r"\b(?:REF:\s*)?[0-9a-f]{40}\b|sha256:[0-9a-f]{64}|"
    r"\b\d{4}(?:-\d{2}(?:\.\d{2})?)?\b"
)


def issue_protected_tokens(value):
    return sorted(_PROTECTED.findall(value)) if isinstance(value, str) else []


def _validate_issue_record(record, language, expected=None):
    required = {"item_id", "source_locale", "source_title_hash", "translation",
                "translator", "run", "status"}
    optional = {"expected_source_title_hash"}
    if not isinstance(record, dict) or set(record) - required - optional or not required <= set(record):
        raise ValueError("ungültiges issue-title record schema")
    item_id = record["item_id"]
    if not isinstance(item_id, str) or not _ISSUE_ID.fullmatch(item_id):
        raise ValueError("ungültige item_id")
    if record["source_locale"] != ISSUE_SOURCE_LOCALE:
        raise ValueError("source_locale muss en sein")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", record["source_title_hash"] or ""):
        raise ValueError("ungültiger source_title_hash für %s" % item_id)
    if record["status"] not in ISSUE_STATUSES or not isinstance(record["translation"], str):
        raise ValueError("ungültiger Status/translation für %s" % item_id)
    for key in ("translator", "run"):
        if record[key] is not None and not isinstance(record[key], dict):
            raise ValueError("%s metadata ist ungültig" % key)
    if record["status"] in {"canonical", "translated"} and not record["translation"].strip():
        raise ValueError("fertige Übersetzung ist leer: %s" % item_id)
    if language == ISSUE_SOURCE_LOCALE and record["status"] != "canonical":
        raise ValueError("englischer Record ist nicht canonical: %s" % item_id)
    if language != ISSUE_SOURCE_LOCALE and record["status"] == "canonical":
        raise ValueError("nicht-englischer Record ist canonical: %s" % item_id)
    if record["status"] == "stale":
        wanted = record.get("expected_source_title_hash")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", wanted or "") or wanted == record["source_title_hash"]:
            raise ValueError("stale Record ohne abweichenden erwarteten Hash: %s" % item_id)
    elif "expected_source_title_hash" in record:
        raise ValueError("expected_source_title_hash nur bei stale erlaubt: %s" % item_id)
    if expected is not None:
        if item_id not in expected:
            raise ValueError("wrong-item record: %s" % item_id)
        wanted = expected[item_id]["source_title_hash"]
        actual = record.get("expected_source_title_hash", record["source_title_hash"])
        if actual != wanted:
            raise ValueError("stale source hash: %s" % item_id)
        if record["status"] in {"canonical", "translated"}:
            if issue_protected_tokens(expected[item_id]["title"]) != issue_protected_tokens(record["translation"]):
                raise ValueError("geschützte Tokens weichen ab: %s" % item_id)
    return record


def _issue_document(language, records):
    return {"schema": ISSUE_SCHEMA, "language": language, "source_locale": ISSUE_SOURCE_LOCALE,
            "records": sorted(records, key=lambda value: value["item_id"])}


def _load_issue_document(path, language, expected=None):
    doc = _lade(path, _issue_document(language, []))
    if not isinstance(doc, dict) or set(doc) != {"schema", "language", "source_locale", "records"}:
        raise ValueError("ungültiges issues.json Dokument: %s" % path)
    if doc["schema"] != ISSUE_SCHEMA or doc["language"] != language or doc["source_locale"] != ISSUE_SOURCE_LOCALE:
        raise ValueError("issues.json Header stimmt nicht: %s" % path)
    if not isinstance(doc["records"], list):
        raise ValueError("issues.json records ist keine Liste: %s" % path)
    seen = set()
    for record in doc["records"]:
        _validate_issue_record(record, language, expected=expected)
        if record["item_id"] in seen:
            raise ValueError("doppelter issue-title Record: %s" % record["item_id"])
        seen.add(record["item_id"])
    return doc


def _write_issue_document(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(doc, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def extract_issue_titles(catalog_path=CATALOG_PATH, public_path=PUBLIC_ISSUES_PATH,
                         site_path=SITE_PATH, i18n_dir=I18N):
    catalog, public = _lade(catalog_path, {}), _lade(public_path, {})
    catalog_items = {item.get("id"): item for item in catalog.get("items", []) if isinstance(item, dict)}
    expected, public_ids = {}, set()
    for item in public.get("items", []):
        item_id = item.get("id")
        if item_id in public_ids:
            raise ValueError("doppeltes public item: %s" % item_id)
        public_ids.add(item_id)
        source = catalog_items.get(item_id)
        if not source or source.get("visibility") != "public-summary":
            raise ValueError("wrong-item/public visibility: %s" % item_id)
        title = source.get("title")
        digest = _sha256_text(title) if isinstance(title, str) else None
        if digest != source.get("title_source_hash") or digest != item.get("title_source_hash"):
            raise ValueError("source-title hash mismatch: %s" % item_id)
        expected[item_id] = {"title": title, "source_title_hash": digest}
    languages = configured_issue_languages(site_path)
    if ISSUE_SOURCE_LOCALE not in languages:
        raise ValueError("canonical source locale en fehlt in site.json")
    for language in languages:
        path = os.path.join(i18n_dir, language, "issues.json")
        old = _load_issue_document(path, language) if os.path.exists(path) else _issue_document(language, [])
        prior, records = {r["item_id"]: r for r in old["records"]}, []
        for item_id, source in sorted(expected.items()):
            previous = prior.get(item_id)
            if language == ISSUE_SOURCE_LOCALE:
                record = {"item_id": item_id, "source_locale": ISSUE_SOURCE_LOCALE,
                          "source_title_hash": source["source_title_hash"], "translation": source["title"],
                          "translator": {"id": "canonical-source", "method": "catalog"},
                          "run": {"id": "hermetic-extract"}, "status": "canonical"}
            elif previous and previous["source_title_hash"] == source["source_title_hash"]:
                record = previous
            elif previous and previous["translation"]:
                record = dict(previous)
                record["status"] = "stale"
                record["expected_source_title_hash"] = source["source_title_hash"]
            else:
                record = {"item_id": item_id, "source_locale": ISSUE_SOURCE_LOCALE,
                          "source_title_hash": source["source_title_hash"], "translation": "",
                          "translator": None, "run": None, "status": "pending"}
            _validate_issue_record(record, language, expected=expected)
            records.append(record)
        _write_issue_document(path, _issue_document(language, records))
    return expected


def split_issue_titles(language, site_path=SITE_PATH, i18n_dir=I18N, output_path=None):
    if language not in configured_issue_languages(site_path):
        raise ValueError("nicht konfigurierte Sprache: %s" % language)
    canonical = _load_issue_document(os.path.join(i18n_dir, ISSUE_SOURCE_LOCALE, "issues.json"), ISSUE_SOURCE_LOCALE)
    expected = {r["item_id"]: {"title": r["translation"], "source_title_hash": r["source_title_hash"]}
                for r in canonical["records"]}
    doc = _load_issue_document(os.path.join(i18n_dir, language, "issues.json"), language, expected=expected)
    rows = [{"item_id": r["item_id"], "source_locale": ISSUE_SOURCE_LOCALE,
             "source_title": expected[r["item_id"]]["title"],
             "source_title_hash": expected[r["item_id"]]["source_title_hash"],
             "protected_tokens": issue_protected_tokens(expected[r["item_id"]]["title"])}
            for r in doc["records"] if r["status"] in {"pending", "stale"}]
    output_path = output_path or os.path.join(i18n_dir, "work", language, "issues.jsonl")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def merge_issue_titles(language, input_path, translator, run_id, site_path=SITE_PATH, i18n_dir=I18N):
    if language == ISSUE_SOURCE_LOCALE or language not in configured_issue_languages(site_path):
        raise ValueError("issue-title Merge-Zielsprache ungültig: %s" % language)
    canonical = _load_issue_document(os.path.join(i18n_dir, ISSUE_SOURCE_LOCALE, "issues.json"), ISSUE_SOURCE_LOCALE)
    expected = {r["item_id"]: {"title": r["translation"], "source_title_hash": r["source_title_hash"]}
                for r in canonical["records"]}
    target_path = os.path.join(i18n_dir, language, "issues.json")
    target = _load_issue_document(target_path, language, expected=expected)
    by_id, seen, incoming = {r["item_id"]: r for r in target["records"]}, set(), []
    with open(input_path, encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if set(row) != {"item_id", "source_title_hash", "translation"}:
                raise ValueError("merge row schema line %d" % line_number)
            item_id = row["item_id"]
            if item_id in seen:
                raise ValueError("duplicate merge item: %s" % item_id)
            seen.add(item_id)
            if item_id not in expected or item_id not in by_id:
                raise ValueError("wrong-item record: %s" % item_id)
            if row["source_title_hash"] != expected[item_id]["source_title_hash"]:
                raise ValueError("stale source hash: %s" % item_id)
            if issue_protected_tokens(row["translation"]) != issue_protected_tokens(expected[item_id]["title"]):
                raise ValueError("geschützte Tokens weichen ab: %s" % item_id)
            record = {"item_id": item_id, "source_locale": ISSUE_SOURCE_LOCALE,
                      "source_title_hash": row["source_title_hash"], "translation": row["translation"],
                      "translator": {"id": translator}, "run": {"id": run_id}, "status": "translated"}
            _validate_issue_record(record, language, expected=expected)
            incoming.append(record)
    for record in incoming:
        by_id[record["item_id"]] = record
    _write_issue_document(target_path, _issue_document(language, list(by_id.values())))
    return len(incoming)


def issue_title_status(site_path=SITE_PATH, i18n_dir=I18N, public_path=None):
    result = {"schema": "issue-title-translation-status@v1", "complete": True, "languages": {}}
    canonical = _load_issue_document(os.path.join(i18n_dir, ISSUE_SOURCE_LOCALE, "issues.json"), ISSUE_SOURCE_LOCALE)
    expected = {r["item_id"]: {"title": r["translation"], "source_title_hash": r["source_title_hash"]}
                for r in canonical["records"]}
    projection_ids = set(expected)
    if public_path is None and os.path.abspath(i18n_dir) == os.path.abspath(I18N):
        public_path = PUBLIC_ISSUES_PATH
    if public_path and os.path.exists(public_path):
        projection = _lade(public_path, {})
        projection_ids = {item.get("id") for item in projection.get("items", [])
                          if isinstance(item, dict) and isinstance(item.get("id"), str)}
    for language in configured_issue_languages(site_path):
        path = os.path.join(i18n_dir, language, "issues.json")
        if not os.path.exists(path):
            counts = {"canonical": 0, "translated": 0, "pending": len(projection_ids), "stale": 0,
                      "missing_file": 1, "missing_records": len(projection_ids)}
        else:
            doc = _load_issue_document(path, language, expected=expected)
            counts = {name: 0 for name in sorted(ISSUE_STATUSES)}
            counts["missing_file"] = 0
            for record in doc["records"]:
                counts[record["status"]] += 1
            counts["missing_records"] = len(projection_ids - {r["item_id"] for r in doc["records"]})
        complete = (not counts["missing_file"] and not counts["missing_records"]
                    and not counts["pending"] and not counts["stale"])
        result["languages"][language] = {"complete": complete, "counts": counts}
        result["complete"] = result["complete"] and complete
    return result


def _register(lang):
    seg = _lade(os.path.join(I18N, lang, "segments.json"), {})
    lab = _lade(os.path.join(I18N, lang, "labels.json"), {})
    return seg, lab


def _bestehender_einzug(path, default=2):
    """Preserve a register's established JSON indentation (not global style)."""
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if line.strip() and line.lstrip().startswith('"'):
                return len(line) - len(line.lstrip())
    return default


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


def _waehle_batches(dateien, only=None):
    batches = sorted(f for f in dateien
                     if re.fullmatch(r"batch_\d+\.out\.jsonl", f))
    if only is None:
        return batches
    requested = list(dict.fromkeys(only))
    invalid = [f for f in requested
               if not re.fullmatch(r"batch_\d+\.out\.jsonl", f)]
    missing = [f for f in requested if f not in batches]
    if invalid or missing:
        details = []
        if invalid:
            details.append("ungültig: %s" % ", ".join(invalid))
        if missing:
            details.append("fehlt: %s" % ", ".join(missing))
        raise ValueError("Batch-Auswahl abgelehnt (%s)" % "; ".join(details))
    return requested


def merge(lang, only=None):
    _t0 = time.time()
    qseg, qlab = _quelle()
    seg, lab = _register(lang)
    d = os.path.join(WORK, lang)
    fehler, uebernommen = [], 0
    _batches_consumed = 0
    dateien = os.listdir(d) if os.path.isdir(d) else []
    for f in _waehle_batches(dateien, only=only):
        _batches_consumed += 1
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
    seg_path = os.path.join(I18N, lang, "segments.json")
    lab_path = os.path.join(I18N, lang, "labels.json")
    seg_indent = _bestehender_einzug(seg_path)
    lab_indent = _bestehender_einzug(lab_path)
    json.dump(seg, open(seg_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=seg_indent)
    json.dump(lab, open(lab_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=lab_indent)
    if only:
        scope = "-".join(os.path.splitext(os.path.splitext(f)[0])[0] for f in only)
        fp = os.path.join(d, "fehler.%s.json" % scope)
    else:
        fp = os.path.join(d, "fehler.json")
    if fehler:
        json.dump(fehler, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    elif os.path.exists(fp):
        os.remove(fp)
    rest = len(offene(lang))
    print("[%s] übernommen: %d, abgelehnt: %d, noch offen: %d%s"
          % (lang, uebernommen, len(fehler), rest,
             "  (Details: %s)" % os.path.relpath(fp, HERE) if fehler else ""))
    _changed = [os.path.join("i18n", lang, "segments.json"), os.path.join("i18n", lang, "labels.json")]
    if fehler:
        _changed.append(os.path.relpath(fp, HERE))
    _write_report(
        report_kind="i18n_merge", tool="i18n_translate.py",
        command="i18n_translate.py merge %s%s" % (
            lang, " --only=%s" % ",".join(only) if only else ""),
        inputs=[lang] + (list(only) if only else []),
        started_at=_t0, exit_code=(1 if fehler else 0),
        changed_artifacts=_changed,
        counts={"batches_consumed": _batches_consumed, "accepted": uebernommen,
                "rejected": len(fehler), "register_changes": uebernommen},
        findings=[{"category": "merge-reject", "severity": "error",
                   "message": "%s: %s" % (e.get("id", "?"), e.get("grund", "?"))} for e in fehler],
    )
    return len(fehler)


def status():
    qseg, qlab = _quelle()
    gesamt = len(qseg) + len(qlab)
    print("Sprache  übersetzt  offen   (von %d)" % gesamt)
    for lang in LANGS:
        rest = len(offene(lang))
        print("  %-5s  %8d  %5d" % (lang, gesamt - rest, rest))


def main():
    issue_commands = {"issues-extract", "issues-split", "issues-merge", "issues-status"}
    if len(sys.argv) >= 2 and sys.argv[1] in issue_commands:
        cmd, args = sys.argv[1], sys.argv[2:]
        try:
            if cmd == "issues-extract":
                extract_issue_titles()
            elif cmd == "issues-status":
                print(json.dumps(issue_title_status(), ensure_ascii=False, indent=2, sort_keys=True))
            elif cmd == "issues-split":
                if not args:
                    raise ValueError("issues-split braucht eine Sprache")
                split_issue_titles(args[0])
            else:
                if len(args) < 7 or args[1] != "--input" or "--translator" not in args or "--run-id" not in args:
                    raise ValueError("issues-merge LANG --input PATH --translator ID --run-id ID")
                merge_issue_titles(args[0], args[2], args[args.index("--translator") + 1],
                                   args[args.index("--run-id") + 1])
        except (ValueError, OSError, json.JSONDecodeError) as ex:
            sys.exit(str(ex))
        return
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
        only = None
        for arg in sys.argv[3:]:
            if arg.startswith("--only="):
                only = [name for name in arg[7:].split(",") if name]
        try:
            errors = merge(lang, only=only)
        except ValueError as ex:
            sys.exit(str(ex))
        sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
