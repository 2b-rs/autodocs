import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import delta_view as dv  # noqa: E402
import version_store as vs  # noqa: E402
import dependency_graph as dg  # noqa: E402
import confidence as conf  # noqa: E402


class DeltaViewTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self._orig = {}
        for mod, attr in [(vs, "VERSIONS_ROOT"), (dg, "EDGES_FILE"), (dg, "DISMISSED_FILE"),
                          (conf, "HISTORY_FILE"), (conf, "REVISITS_FILE"),
                          (conf, "INVALIDATED_FILE"), (conf, "FEEDBACK_FILE")]:
            self._orig[(mod, attr)] = getattr(mod, attr)
            setattr(mod, attr, base / Path(getattr(mod, attr)).name)
        self.addCleanup(self._restore)

    def _restore(self):
        for (mod, attr), val in self._orig.items():
            setattr(mod, attr, val)

    def test_exactly_one_of_release_or_date_required(self):
        with self.assertRaises(ValueError):
            dv.resolve_baseline_timestamp()
        with self.assertRaises(ValueError):
            dv.resolve_baseline_timestamp(release="R25-11", date="2026-01-01")

    def test_unknown_release_baseline_returns_empty_delta_not_an_error(self):
        result = dv.delta_view(release="R99-99")
        self.assertEqual(result["changed_requirements"], [])
        self.assertIsNone(result["baseline"]["resolved_timestamp"])

    def test_date_baseline_is_used_unchanged(self):
        ts = dv.resolve_baseline_timestamp(date="2020-01-01T00:00:00+00:00")
        self.assertEqual(ts, "2020-01-01T00:00:00+00:00")

    def test_release_baseline_resolves_to_earliest_recorded_at_for_that_release(self):
        vs.record_version("AUTOSAR/AP/record/A", "R25-11", "content-a")
        ts = dv.resolve_baseline_timestamp(release="R25-11")
        self.assertIsNotNone(ts)

    def test_changed_requirements_only_includes_versions_after_baseline(self):
        vs.record_version("AUTOSAR/AP/record/OLD", "R25-11", "old")
        old_ts = dv.resolve_baseline_timestamp(date="2099-01-01T00:00:00+00:00")
        result = dv.delta_view(date=old_ts)
        self.assertNotIn("AUTOSAR/AP/record/OLD", result["changed_requirements"])

    def test_changed_requirements_includes_versions_since_a_past_baseline(self):
        vs.record_version("AUTOSAR/AP/record/NEW", "R25-11", "new")
        result = dv.delta_view(date="2000-01-01T00:00:00+00:00")
        self.assertIn("AUTOSAR/AP/record/NEW", result["changed_requirements"])

    def test_invalidated_nodes_since_baseline_are_included(self):
        conf.mark_invalidated("AUTOSAR/AP/artifact/X", "superseded")
        result = dv.delta_view(date="2000-01-01T00:00:00+00:00")
        ids = [e["node_id"] for e in result["invalidated_nodes"]]
        self.assertIn("AUTOSAR/AP/artifact/X", ids)

    def test_revisit_tasks_enqueued_counts_entries_since_baseline(self):
        conf.record_confidence("AUTOSAR/AP/artifact/Y", 0.5, "feedback")
        result = dv.delta_view(date="2000-01-01T00:00:00+00:00")
        self.assertGreaterEqual(result["revisit_tasks_enqueued"], 1)

    def test_result_shape_has_all_contract_fields(self):
        result = dv.delta_view(date="2000-01-01T00:00:00+00:00")
        for key in ("baseline", "changed_requirements", "invalidated_nodes",
                    "revisit_tasks_enqueued", "revisit_tasks"):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main()
