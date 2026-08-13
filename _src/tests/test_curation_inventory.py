import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import curation_inventory as ci  # noqa: E402


class CurationInventoryTests(unittest.TestCase):
    def test_build_inventory_returns_all_four_categories(self):
        inv = ci.build_inventory()
        names = {c["category"] for c in inv["categories"]}
        self.assertEqual(len(names), 4)

    def test_review_queue_and_curation_queue_are_first_class(self):
        inv = ci.build_inventory()
        for cat in inv["categories"]:
            if cat["category"] in ("review-queue (open)", "curation-queue (open)"):
                self.assertEqual(cat["classification"], "first_class")

    def test_residual_is_report_only(self):
        self.assertEqual(ci.classification_for("extraction_report.RESIDUAL"), "report_only")

    def test_pilot_review_status_is_historical_archive(self):
        self.assertEqual(
            ci.classification_for("SWS_LOG requirement_meta.review_*"), "historical_archive")

    def test_classification_for_unknown_category_returns_none(self):
        self.assertIsNone(ci.classification_for("not-a-real-category"))

    def test_by_classification_partitions_categories_correctly(self):
        inv = ci.build_inventory()
        total_via_categories = len(inv["categories"])
        total_via_partition = sum(len(v) for v in inv["by_classification"].values())
        self.assertEqual(total_via_categories, total_via_partition)

    def test_real_counts_are_non_trivial_in_this_sandbox(self):
        inv = ci.build_inventory()
        counts = {c["category"]: c["count"] for c in inv["categories"]}
        self.assertGreater(counts["review-queue (open)"], 0)
        self.assertGreater(counts["curation-queue (open)"], 0)

    def test_queue_open_items_missing_dir_returns_empty(self):
        self.assertEqual(ci._queue_open_items("does-not-exist-queue"), [])


if __name__ == "__main__":
    unittest.main()
