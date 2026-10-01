import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import supersession_trigger as st  # noqa: E402
import version_store as vs  # noqa: E402
import dependency_graph as dg  # noqa: E402
import confidence as conf  # noqa: E402


class SupersessionTriggerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)

        self._orig_vs_root = vs.SPEC_ROOT if hasattr(vs, "SPEC_ROOT") else None
        self._patch_module_roots(base)
        self.addCleanup(self._restore_module_roots)

    def _patch_module_roots(self, base):
        import version_store, dependency_graph, confidence, supersession_trigger
        self._orig = {}
        for mod, attr in [(version_store, "VERSIONS_ROOT"), (dependency_graph, "EDGES_FILE"),
                          (dependency_graph, "DISMISSED_FILE"), (confidence, "HISTORY_FILE"),
                          (confidence, "REVISITS_FILE"), (confidence, "INVALIDATED_FILE"),
                          (confidence, "FEEDBACK_FILE"), (supersession_trigger, "REPORTS_DIR")]:
            if hasattr(mod, attr):
                self._orig[(mod, attr)] = getattr(mod, attr)
                old_val = getattr(mod, attr)
                new_val = base / Path(old_val).name
                setattr(mod, attr, new_val)

    def _restore_module_roots(self):
        for (mod, attr), val in self._orig.items():
            setattr(mod, attr, val)

    def test_unknown_trigger_kind_is_unresolved_and_not_changed(self):
        report = st.process_trigger("not-a-real-trigger", "AUTOSAR/AP/record/X", "R99-99", "content")
        self.assertFalse(report["changed"])
        self.assertTrue(report["unresolved"])

    def test_first_trigger_for_a_requirement_always_changes(self):
        report = st.process_trigger("new_release", "AUTOSAR/AP/record/X", "R25-11", "first content")
        self.assertTrue(report["changed"])
        self.assertIsNotNone(report["new_version_id"])

    def test_repeating_identical_content_is_a_documented_no_op(self):
        st.process_trigger("new_release", "AUTOSAR/AP/record/Y", "R25-11", "same content")
        report2 = st.process_trigger("scraper_update", "AUTOSAR/AP/record/Y", "R25-11", "same content")
        self.assertFalse(report2["changed"])
        self.assertIsNone(report2["new_version_id"])

    def test_genuinely_different_content_triggers_a_new_version(self):
        st.process_trigger("new_release", "AUTOSAR/AP/record/Z", "R25-11", "v1 content")
        report2 = st.process_trigger("new_release", "AUTOSAR/AP/record/Z", "R32-11", "v2 content, changed")
        self.assertTrue(report2["changed"])

    def test_change_cascades_invalidation_to_dependents(self):
        dg.add_edge("AUTOSAR/AP/record/PARENT", "AUTOSAR/AP/artifact/CHILD", "derived_from")
        st.process_trigger("new_release", "AUTOSAR/AP/record/PARENT", "R25-11", "v1")
        report2 = st.process_trigger("new_release", "AUTOSAR/AP/record/PARENT", "R32-11", "v2 changed")
        self.assertIn("AUTOSAR/AP/artifact/CHILD", report2["dependents_invalidated"])
        self.assertTrue(report2["revisit_enqueued"])
        self.assertTrue(conf.is_invalidated("AUTOSAR/AP/artifact/CHILD"))

    def test_change_with_no_dependents_does_not_enqueue_revisit(self):
        report = st.process_trigger("user_comment", "AUTOSAR/AP/record/LONELY", "R25-11", "v1")
        self.assertFalse(report["revisit_enqueued"])

    def test_write_report_persists_json(self):
        report = st.process_trigger("new_release", "AUTOSAR/AP/record/W", "R25-11", "content")
        path = st.write_report(report)
        self.assertTrue(path.exists())

    def test_summarize_reports_aggregates_correctly(self):
        r1 = st.process_trigger("new_release", "AUTOSAR/AP/record/A1", "R25-11", "a1")
        r2 = st.process_trigger("not-a-real-trigger", "AUTOSAR/AP/record/A2", "R25-11", "a2")
        summary = st.summarize_reports([r1, r2])
        self.assertIn("AUTOSAR/AP/record/A1", summary["changed_requirements"])
        self.assertEqual(len(summary["unresolved"]), 1)

    def test_all_six_named_trigger_kinds_are_accepted(self):
        named = ("new_release", "new_curation_input", "user_comment", "scraper_update",
                 "extraction_bugfix", "new_source_available", "ai_model_change")
        self.assertEqual(set(named), set(st.TRIGGER_KINDS))
        for i, kind in enumerate(named):
            report = st.process_trigger(kind, "AUTOSAR/AP/record/T%d" % i, "R25-11", "content-%d" % i)
            self.assertEqual(report["unresolved"], [])


if __name__ == "__main__":
    unittest.main()
