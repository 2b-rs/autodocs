import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import asof_view as av  # noqa: E402
import version_store as vs  # noqa: E402
import dependency_graph as dg  # noqa: E402
import confidence as conf  # noqa: E402


class AsOfViewTests(unittest.TestCase):
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

    def test_as_of_release_before_any_version_returns_none_version(self):
        view = av.as_of_release("AUTOSAR/AP/record/NEW", "R01-01")
        self.assertIsNone(view["version"])

    def test_as_of_release_returns_the_correct_historical_version_not_the_latest(self):
        vs.record_version("AUTOSAR/AP/record/X", "R25-11", "old text")
        vs.record_version("AUTOSAR/AP/record/X", "R32-11", "new text")
        view = av.as_of_release("AUTOSAR/AP/record/X", "R25-11")
        self.assertEqual(view["version"]["content"], "old text")

    def test_as_of_release_at_the_latest_release_returns_latest_version(self):
        vs.record_version("AUTOSAR/AP/record/Y", "R25-11", "old text")
        vs.record_version("AUTOSAR/AP/record/Y", "R32-11", "new text")
        view = av.as_of_release("AUTOSAR/AP/record/Y", "R32-11")
        self.assertEqual(view["version"]["content"], "new text")

    def test_as_of_date_picks_version_recorded_at_or_before_the_date(self):
        vs.record_version("AUTOSAR/AP/record/Z", "R25-11", "v1")
        first = vs.list_versions("AUTOSAR/AP/record/Z")[0]
        view = av.as_of_date("AUTOSAR/AP/record/Z", first["recorded_at"])
        self.assertEqual(view["version"]["content"], "v1")

    def test_artifact_graph_snapshot_never_hides_invalidated_dependents(self):
        dg.add_edge("AUTOSAR/AP/record/PARENT", "AUTOSAR/AP/artifact/CHILD", "derived_from")
        conf.mark_invalidated("AUTOSAR/AP/artifact/CHILD", "superseded")
        view = av.as_of_release("AUTOSAR/AP/record/PARENT", "R25-11")
        self.assertIn("AUTOSAR/AP/artifact/CHILD", view["artifact_graph"])
        self.assertTrue(view["artifact_graph"]["AUTOSAR/AP/artifact/CHILD"]["invalidated"])

    def test_artifact_graph_snapshot_never_hides_dismissed_dependents(self):
        dg.add_edge("AUTOSAR/AP/record/PARENT2", "AUTOSAR/AP/artifact/CHILD2", "derived_from")
        dg.dismiss_node("AUTOSAR/AP/artifact/CHILD2", "reviewed and dropped")
        view = av.as_of_release("AUTOSAR/AP/record/PARENT2", "R25-11")
        self.assertTrue(view["artifact_graph"]["AUTOSAR/AP/artifact/CHILD2"]["dismissed"])

    def test_no_version_means_no_decisions_returned(self):
        view = av.as_of_release("AUTOSAR/AP/record/NOVER", "R01-01")
        self.assertEqual(view["decisions"], [])

    def test_as_of_release_view_shape_has_all_contract_fields(self):
        view = av.as_of_release("AUTOSAR/AP/record/SHAPE", "R25-11")
        for key in ("canonical_id", "as_of", "version", "decisions", "artifact_graph"):
            self.assertIn(key, view)


if __name__ == "__main__":
    unittest.main()
