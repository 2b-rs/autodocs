#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for validate.py's check-progress instrumentation
(run_checks / CHECKS), added for the validate-py-nontermination-20260827
investigation.

Design note (per Jean-Luc's guidance carried in the dispatch briefing):
"Regression bitte robust gegen Host-Streuung: enge absolute Wall-Clock-
Schwelle allein ist ungeeignet. Bevorzugt deterministische Tests für
Fortschrittsereignisse/Check-Reihenfolge und ein grosszuegiges, begruendetes
Laufzeitbudget oder Verhaeltnis-/Fixture-Budget mit diagnostischer Ausgabe."

So: the tests below assert deterministic behavior (progress events fire once
per check, in the declared order, with correct 1-based "n/total" framing) via
fake, instantaneous check callables — no dependency on wall-clock timing.
A separate, generous, justified real-runtime budget test lives in
test_validate_automation_safety_budget.py and uses a ratio/fixture budget
with diagnostic output on failure, not a tight absolute-time assertion.
"""
import io
import os
import sys
import unittest

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS = os.path.join(_SRC, "tools")
for path in (_SRC, _TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import validate  # noqa: E402


class RunChecksProgressTests(unittest.TestCase):
    def test_progress_events_fire_once_per_check_in_order(self):
        calls = []

        def make_check(name):
            def _check():
                calls.append(name)
            return _check

        names = ["alpha", "beta", "gamma"]
        checks = [(n, make_check(n)) for n in names]
        out = io.StringIO()
        clock = iter([0.0, 0.1, 0.1, 0.4, 0.4, 0.9]).__next__
        timings = validate.run_checks(checks, out=out, clock=clock)

        # Every check ran exactly once, in declared order.
        self.assertEqual(calls, names)

        # Deterministic pairing of (name, elapsed) in the same order.
        self.assertEqual([t[0] for t in timings], names)
        self.assertEqual(len(timings), 3)

        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 6, "expected one start + one done line per check")
        # start/done alternate, 1-based index, correct total.
        for i, name in enumerate(names, start=1):
            start_line = lines[(i - 1) * 2]
            done_line = lines[(i - 1) * 2 + 1]
            self.assertIn("%d/3 start %s" % (i, name), start_line)
            self.assertIn("%d/3 done" % i, done_line)
            self.assertIn(name, done_line)

    def test_progress_events_fire_even_when_total_is_one(self):
        out = io.StringIO()
        ran = []
        checks = [("only", lambda: ran.append("only"))]
        clock = iter([5.0, 5.0]).__next__
        timings = validate.run_checks(checks, out=out, clock=clock)
        self.assertEqual(ran, ["only"])
        self.assertEqual(timings, [("only", 0.0)])
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("1/1 start only", lines[0])
        self.assertIn("1/1 done  only", lines[1])

    def test_empty_check_list_produces_no_output_and_no_timings(self):
        out = io.StringIO()
        timings = validate.run_checks([], out=out)
        self.assertEqual(timings, [])
        self.assertEqual(out.getvalue(), "")

    def test_a_failing_check_still_emits_its_start_line_before_raising(self):
        # A progress line for the check that is about to run must already be
        # visible before that check can fail — this is the whole point of the
        # instrumentation: a caller watching output sees which check is in
        # flight, even if it never finishes.
        out = io.StringIO()

        def boom():
            raise RuntimeError("simulated failure")

        checks = [("ok", lambda: None), ("boom", boom), ("never", lambda: None)]
        with self.assertRaises(RuntimeError):
            validate.run_checks(checks, out=out)
        lines = out.getvalue().splitlines()
        self.assertIn("1/3 start ok", lines[0])
        self.assertIn("1/3 done  ok", lines[1])
        self.assertIn("2/3 start boom", lines[2])
        # No done line for "boom" (it raised) and no start line for "never".
        self.assertEqual(len(lines), 3)

    def test_checks_constant_matches_the_12_functions_main_used_to_call_directly(self):
        # Locks in check identity and order so a future edit to CHECKS is a
        # visible, intentional change rather than a silent drop/reorder.
        expected_order = [
            "check_automation_safety",
            "check_build",
            "check_links",
            "check_langs",
            "check_requirement_review_schema",
            "check_namespaces",
            "check_home_links",
            "check_no_hardcoded_german",
            "check_client_rendered_german",
            "check_record_status",
            "check_workflow_lifecycle",
            "check_report_freshness",
        ]
        self.assertEqual([name for name, _fn in validate.CHECKS], expected_order)
        for name, fn in validate.CHECKS:
            self.assertEqual(fn.__name__, name)


if __name__ == "__main__":
    unittest.main()
