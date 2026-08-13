import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import workflow_lifecycle as wl  # noqa: E402


class WorkflowLifecycleTests(unittest.TestCase):
    def test_all_tool_transitions_reference_valid_states(self):
        for name, spec in wl.TOOL_TRANSITIONS.items():
            for f in spec["from"]:
                self.assertIn(f, wl.STATES, f"{name}: unknown from-state {f!r}")
            self.assertIn(spec["to"], wl.STATES, f"{name}: unknown to-state {spec['to']!r}")

    def test_all_tool_transitions_are_declared_valid(self):
        for name, spec in wl.TOOL_TRANSITIONS.items():
            for f in spec["from"]:
                self.assertTrue(
                    wl.validate_transition(f, spec["to"]),
                    f"{name}: {f} -> {spec['to']} not in VALID_TRANSITIONS",
                )

    def test_terminal_states_have_no_outgoing_transitions(self):
        self.assertEqual(wl.VALID_TRANSITIONS["rejected"], ())
        self.assertEqual(wl.VALID_TRANSITIONS["superseded"], ())

    def test_validate_transition_rejects_unknown_states(self):
        with self.assertRaises(ValueError):
            wl.validate_transition("bogus", "queued")
        with self.assertRaises(ValueError):
            wl.validate_transition("queued", "bogus")

    def test_validate_transition_true_false(self):
        self.assertTrue(wl.validate_transition("queued", "claimed"))
        self.assertFalse(wl.validate_transition("rejected", "applied"))

    def test_every_tool_mentioned_in_todo_is_mapped(self):
        required_prefixes = (
            "review_flags.", "curation_flags.", "review_ingest.",
            "curation_ingest.", "hypothesis_store.",
        )
        for prefix in required_prefixes:
            self.assertTrue(
                any(name.startswith(prefix) for name in wl.TOOL_TRANSITIONS),
                f"no TOOL_TRANSITIONS entry for {prefix}*",
            )


if __name__ == "__main__":
    unittest.main()
