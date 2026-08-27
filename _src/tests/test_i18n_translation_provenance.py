"""Provenance for i18n segment/title/diagram registers (Task `0037-27.04`).

Adversarial completion evidence (DEC-0038-004):
- AE-2 baselines: pre-change `2064704457f98c66fb6f77ad3c263415864fe2ff`;
  candidate this Task's implementation of `i18n_translation_provenance.py`.
- AE-3 falsification: source-hash drift with the same source_id is invisible to
  presence-only register lookup (`offene`/key membership) and is reported
  stale by `inspect_language_work`.
- AE-4 adjacent: protected-token mismatch (reject) and missing locale (report).
- AE-5: seeded enumeration over missing-id subsets; invariant that missing
  cardinality equals the omitted set size.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "0037-27.04"
TOOL = ROOT / "_src" / "tools" / "i18n_translation_provenance.py"
STORE = ROOT / "_src" / "tools" / "provenance_store.py"
TRANSLATE = ROOT / "_src" / "i18n_translate.py"

SPEC = importlib.util.spec_from_file_location("i18n_translation_provenance", TOOL)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules["i18n_translation_provenance"] = mod
SPEC.loader.exec_module(mod)

PS_SPEC = importlib.util.spec_from_file_location("provenance_store", STORE)
assert PS_SPEC and PS_SPEC.loader
ps = importlib.util.module_from_spec(PS_SPEC)
sys.modules["provenance_store"] = ps
PS_SPEC.loader.exec_module(ps)

TR_SPEC = importlib.util.spec_from_file_location("i18n_translate", TRANSLATE)
assert TR_SPEC and TR_SPEC.loader
tr = importlib.util.module_from_spec(TR_SPEC)
sys.modules["i18n_translate"] = tr
TR_SPEC.loader.exec_module(tr)

COMMIT = "2064704457f98c66fb6f77ad3c263415864fe2ff"
RUN_ID = "018f4a31-2704-7abc-8def-0123456789ab"
SET_ID = "018f4a31-2704-7abc-8def-0123456789ac"
EVENT_PRODUCED = "018f4a31-2704-7abc-8def-0123456789ad"
EVENT_DERIVED = "018f4a31-2704-7abc-8def-0123456789ae"
EVENT_INVALID = "018f4a31-2704-7abc-8def-0123456789af"
STAMP = "2026-08-27T12:39:00Z"
ENDED = "2026-08-27T12:40:00Z"
TITLE_SOURCE = (
    "Extend i18n registers with provenance "
    "`REF: 2064704457f98c66fb6f77ad3c263415864fe2ff` for 0037-27.04 and {name}."
)
TITLE_ES = (
    "Extienda los registros i18n con procedencia "
    "`REF: 2064704457f98c66fb6f77ad3c263415864fe2ff` para 0037-27.04 y {name}."
)


def _ids():
    return {
        "produced-by": EVENT_PRODUCED,
        "derived-from": EVENT_DERIVED,
        "invalidated-by": EVENT_INVALID,
    }


class I18nTranslationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = ps.ProvenanceStore(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _context(self):
        return dict(
            translator={"id": "human-curator", "method": "human"},
            model={"id": "none", "kind": "human-authored"},
            policy={"id": "i18n-protected-tokens@v1"},
            config={"merge": "i18n_translate.merge", "preserve_registers": True},
        )

    def test_traces_segment_title_and_diagram_to_run(self):
        segments_de = json.loads((FIXTURES / "segments.de.json").read_text(encoding="utf-8"))
        segments_en = json.loads((FIXTURES / "segments.en.json").read_text(encoding="utf-8"))
        labels_en = json.loads((FIXTURES / "labels.en.json").read_text(encoding="utf-8"))
        entries = [
            {
                "family": "segment",
                "source_id": "seg-prose-01",
                "source_text": segments_de["seg-prose-01"]["m"],
                "source_locale": "de",
                "target_locale": "en",
                "translation": segments_en["seg-prose-01"],
                "merge_decision": "accepted",
            }
        ]
        recorded = mod.record_translation_run(
            self.store,
            run_id=RUN_ID,
            set_id=SET_ID,
            event_ids=_ids(),
            started_at=STAMP,
            ended_at=ENDED,
            commit=COMMIT,
            issue="0037-27.04",
            criterion="AC-i18n-provenance",
            producer_path="_src/i18n_translate.py",
            family="segment",
            target_locale="en",
            register_path="_src/i18n/en/segments.json",
            entries=entries,
            **self._context(),
        )
        trace = mod.trace_to_run(recorded["envelope"], "seg-prose-01")
        self.assertEqual(RUN_ID, trace["run_id"])
        self.assertEqual(mod.sha256_text(segments_de["seg-prose-01"]["m"]), trace["source_hash"])
        self.assertEqual("en", trace["target_locale"])
        self.assertEqual("human-curator", trace["translator"]["id"])
        self.assertTrue((self.root / recorded["path"]).is_file())

        title_entry = mod.validate_entry(
            {
                "family": "title",
                "source_id": "0037-27.04",
                "source_text": TITLE_SOURCE,
                "source_locale": "en",
                "target_locale": "es",
                "translation": TITLE_ES,
                "merge_decision": "accepted",
            }
        )
        self.assertEqual(tr.issue_protected_tokens(TITLE_SOURCE), title_entry["protected_tokens"])
        diagram_entry = mod.validate_entry(
            {
                "family": "diagram",
                "source_id": "Warteschlange",
                "source_text": "Warteschlange",
                "source_locale": "de",
                "target_locale": "en",
                "translation": labels_en["Warteschlange"],
                "merge_decision": "accepted",
            }
        )
        self.assertEqual("Queue", diagram_entry["translation"])
        self.assertEqual(mod.sha256_text("Queue"), diagram_entry["output_digest"])

    def test_rejects_protected_token_and_source_hash_mismatch(self):
        with self.assertRaisesRegex(mod.I18nProvenanceError, "I18N-PROTECTED"):
            mod.validate_entry(
                {
                    "family": "segment",
                    "source_id": "seg-prose-01",
                    "source_text": "Der Puffer speichert [SWS_CM_00001] über ⟦0⟧.",
                    "source_locale": "de",
                    "target_locale": "en",
                    "translation": "The buffer stores [SWS_CM_99999] via ⟦0⟧.",
                    "merge_decision": "accepted",
                }
            )
        with self.assertRaisesRegex(mod.I18nProvenanceError, "I18N-PROTECTED"):
            mod.validate_entry(
                {
                    "family": "title",
                    "source_id": "0037-27.04",
                    "source_text": TITLE_SOURCE,
                    "source_locale": "en",
                    "target_locale": "es",
                    "translation": TITLE_ES.replace("0037-27.04", "0037-99.99"),
                    "merge_decision": "accepted",
                }
            )
        with self.assertRaisesRegex(mod.I18nProvenanceError, "I18N-SOURCE-HASH"):
            mod.validate_entry(
                {
                    "family": "diagram",
                    "source_id": "Warteschlange",
                    "source_text": "Warteschlange",
                    "source_hash": "sha256:" + "0" * 64,
                    "source_locale": "de",
                    "target_locale": "en",
                    "translation": "Queue",
                    "merge_decision": "accepted",
                }
            )

    def test_presence_only_lookup_misses_stale_hash_inspector_reports(self):
        source_items = {"seg-prose-01": "Der Puffer speichert [SWS_CM_00001] über ⟦0⟧."}
        target_items = {"seg-prose-01": "The buffer stores [SWS_CM_00001] via ⟦0⟧."}
        presence_only_open = [sid for sid in source_items if sid not in target_items]
        self.assertEqual([], presence_only_open)
        changed = {"seg-prose-01": "Der Puffer speichert [SWS_CM_00001] über ⟦0⟧. Neu."}
        recorded = {
            "seg-prose-01": {"source_hash": mod.sha256_text(source_items["seg-prose-01"])}
        }
        report = mod.inspect_language_work(
            family="segment",
            source_locale="de",
            target_locale="en",
            source_items=changed,
            target_items=target_items,
            recorded=recorded,
            required_locales=["en", "es"],
            present_locales=["en"],
        )
        self.assertEqual(["seg-prose-01"], report["stale"])
        self.assertFalse(report["complete"])
        self.assertEqual(["es"], report["absent_locales"])
        missing_report = mod.inspect_language_work(
            family="diagram",
            source_locale="de",
            target_locale="fr",
            source_items={"Warteschlange": "Warteschlange"},
            target_items={},
            required_locales=["en", "fr"],
        )
        self.assertEqual(["Warteschlange"], missing_report["missing"])
        self.assertFalse(missing_report["complete"])

    def test_title_stale_and_fallback_decisions(self):
        live = TITLE_SOURCE + " Updated."
        items = {"0037-27.04": TITLE_ES}
        recorded = {
            "0037-27.04": {
                "source_hash": mod.sha256_text(TITLE_SOURCE),
                "status": "stale",
                "expected_source_title_hash": mod.sha256_text(live),
            }
        }
        report = mod.inspect_language_work(
            family="title",
            source_locale="en",
            target_locale="es",
            source_items={"0037-27.04": live},
            target_items=items,
            recorded=recorded,
        )
        self.assertEqual(["0037-27.04"], report["stale"])
        fallback_entry = mod.validate_entry(
            {
                "family": "segment",
                "source_id": "seg-prose-01",
                "source_text": "Hallo",
                "source_locale": "de",
                "target_locale": "en",
                "translation": "Hallo",
                "merge_decision": "fallback",
                "fallback": True,
            }
        )
        self.assertTrue(fallback_entry["fallback"])
        self.assertEqual("fallback", fallback_entry["merge_decision"])

    def test_missing_cardinality_property(self):
        rng = random.Random(2704)
        source_ids = [f"s{i:02d}" for i in range(12)]
        source_items = {sid: f"Quelle {sid}" for sid in source_ids}
        executed = 0
        for _ in range(32):
            omit = set(rng.sample(source_ids, rng.randint(0, len(source_ids))))
            target_items = {
                sid: f"Target {sid}" for sid in source_ids if sid not in omit
            }
            report = mod.inspect_language_work(
                family="segment",
                source_locale="de",
                target_locale="en",
                source_items=source_items,
                target_items=target_items,
            )
            self.assertEqual(sorted(omit), report["missing"])
            self.assertEqual(len(omit), report["counts"]["missing"])
            executed += 1
        self.assertEqual(32, executed)

    def test_human_registers_remain_authoritative_inputs(self):
        dest = self.root / "_src" / "i18n" / "en" / "segments.json"
        dest.parent.mkdir(parents=True)
        original = (FIXTURES / "segments.en.json").read_text(encoding="utf-8")
        dest.write_text(original, encoding="utf-8")
        before = hashlib.sha256(original.encode("utf-8")).digest()
        entries = [
            {
                "family": "segment",
                "source_id": "seg-prose-01",
                "source_text": json.loads((FIXTURES / "segments.de.json").read_text())["seg-prose-01"]["m"],
                "source_locale": "de",
                "target_locale": "en",
                "translation": json.loads(original)["seg-prose-01"],
                "merge_decision": "accepted",
            }
        ]
        mod.record_translation_run(
            self.store,
            run_id=RUN_ID,
            set_id=SET_ID,
            event_ids=_ids(),
            started_at=STAMP,
            ended_at=ENDED,
            commit=COMMIT,
            issue="0037-27.04",
            criterion="AC-i18n-provenance",
            producer_path="_src/i18n_translate.py",
            family="segment",
            target_locale="en",
            register_path="_src/i18n/en/segments.json",
            entries=entries,
            **self._context(),
        )
        after = hashlib.sha256(dest.read_bytes()).digest()
        self.assertEqual(before, after)

    def test_writers_bind_existing_provenance_schema(self):
        self.assertTrue((ROOT / "provenance/_schema/run-v1.schema.json").is_file())
        for kind, name in mod.BOUND_SCHEMAS.items():
            self.assertTrue((ROOT / "provenance" / "_schema" / name).is_file(), kind)
            mod.load_bound_schema(kind)
        entries = [
            {
                "family": "segment",
                "source_id": "seg-prose-01",
                "source_text": json.loads((FIXTURES / "segments.de.json").read_text())["seg-prose-01"]["m"],
                "source_locale": "de",
                "target_locale": "en",
                "translation": json.loads((FIXTURES / "segments.en.json").read_text())["seg-prose-01"],
                "merge_decision": "accepted",
            }
        ]
        recorded = mod.record_translation_run(
            self.store,
            run_id=RUN_ID,
            set_id=SET_ID,
            event_ids=_ids(),
            started_at=STAMP,
            ended_at=ENDED,
            commit=COMMIT,
            issue="0037-27.04",
            criterion="AC-i18n-provenance",
            producer_path="_src/i18n_translate.py",
            family="segment",
            target_locale="en",
            register_path="_src/i18n/en/segments.json",
            entries=entries,
            **self._context(),
        )
        run = json.loads(
            (self.root / "provenance" / "runs" / f"{recorded['envelope']['run_id']}.json").read_text()
        )
        mod.validate_against_bound_schema("run", run)
        with self.assertRaises(mod.I18nProvenanceError) as ctx:
            mod.validate_against_bound_schema("run", {**run, "local_fork_field": 1})
        self.assertEqual(ctx.exception.code, "I18N-SCHEMA-DEVIATION")


if __name__ == "__main__":
    unittest.main()
