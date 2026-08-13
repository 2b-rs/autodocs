import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import curation_item as ci  # noqa: E402
import curation_item_lifecycle_check as cilc  # noqa: E402
import workflow_lifecycle as wl  # noqa: E402


class CurationItemLifecycleTests(unittest.TestCase):
    def test_vocabularies_are_currently_consistent(self):
        self.assertEqual(cilc.validate_vocabularies(), [])

    def test_every_curation_item_status_has_a_lifecycle_state(self):
        for status in ci.VALID_STATUSES:
            state = cilc.STATUS_TO_LIFECYCLE_STATE.get(status)
            self.assertIsNotNone(state, f"no lifecycle state mapped for status {status!r}")
            self.assertIn(state, wl.STATES)

    def test_from_review_flag_open_maps_to_queued(self):
        item = ci.from_review_flag({"id": "SWS_LOG_00201"})
        self.assertEqual(item["status"], "open")
        self.assertEqual(cilc.item_lifecycle_state(item), "queued")

    def test_from_review_flag_claimed_maps_to_claimed(self):
        item = ci.from_review_flag({"id": "SWS_LOG_00201", "claimed_by": "agent-1"})
        self.assertEqual(item["status"], "claimed")
        self.assertEqual(cilc.item_lifecycle_state(item), "claimed")

    def test_from_review_flag_completed_maps_to_applied(self):
        item = ci.from_review_flag({"id": "SWS_LOG_00201", "claimed_by": "agent-1", "completed_at": "2026-08-13T00:00:00Z"})
        self.assertEqual(item["status"], "applied")
        self.assertEqual(cilc.item_lifecycle_state(item), "applied")

    def test_from_curation_flag_outcomes_map_correctly(self):
        accepted = ci.from_curation_flag({"id": "SWS_LOG_00201", "outcome": "accepted"})
        rejected = ci.from_curation_flag({"id": "SWS_LOG_00201", "outcome": "rejected"})
        proposed = ci.from_curation_flag({"id": "SWS_LOG_00201"})
        self.assertEqual((accepted["status"], rejected["status"], proposed["status"]),
                         ("accepted", "rejected", "proposed"))
        self.assertEqual(cilc.item_lifecycle_state(accepted), "accepted")
        self.assertEqual(cilc.item_lifecycle_state(rejected), "rejected")
        self.assertEqual(cilc.item_lifecycle_state(proposed), "proposed")

    def test_is_conformant_rejects_unknown_status(self):
        item = ci.from_review_flag({"id": "SWS_LOG_00201"})
        item["status"] = "not-a-real-status"
        self.assertFalse(ci.is_conformant(item))

    def test_is_conformant_rejects_wrong_schema_version(self):
        item = ci.from_review_flag({"id": "SWS_LOG_00201"})
        item["schema"] = "curation-item@v2"
        self.assertFalse(ci.is_conformant(item))

    def test_is_conformant_rejects_missing_required_field(self):
        item = ci.from_review_flag({"id": "SWS_LOG_00201"})
        del item["campaign"]
        self.assertFalse(ci.is_conformant(item))

    def test_item_lifecycle_state_none_for_unknown_status(self):
        item = ci.from_review_flag({"id": "SWS_LOG_00201"})
        item["status"] = "not-a-real-status"
        self.assertIsNone(cilc.item_lifecycle_state(item))

    def test_every_lifecycle_transition_reachable_from_a_curation_item_status_is_itself_valid(self):
        terminal_statuses = {"rejected", "superseded"}
        for status, state in cilc.STATUS_TO_LIFECYCLE_STATE.items():
            outgoing = wl.VALID_TRANSITIONS.get(state, ())
            if status in terminal_statuses:
                self.assertEqual(outgoing, (), f"{status}/{state} expected terminal, has transitions {outgoing}")
            else:
                self.assertTrue(outgoing, f"{status}/{state} expected non-terminal, has no transitions")


if __name__ == "__main__":
    unittest.main()
