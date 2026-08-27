#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime-budget regression for check_automation_safety /
automation_safety.scan_repository, added for the
validate-py-nontermination-20260827 investigation.

Background: Geordi's Feature-0037 checkpoint recorded validate.py as
INCONCLUSIVE because `python3 _src/validate.py` produced no result within
four bounded 30s intervals. A full profiled run against this repository's 116
real tracked automation paths measured 384.26s wall-clock (see the docstring
on validate.check_automation_safety for the exact reproduction command and
the identified cost concentration in automation_safety's shell-scanning
path) — genuinely slow, not hung, but far past any 30-60s bounded probe.

Design (per Jean-Luc's guidance carried in the dispatch briefing, verbatim):
"Regression bitte robust gegen Host-Streuung: enge absolute Wall-Clock-
Schwelle allein ist ungeeignet. Bevorzugt deterministische Tests fuer
Fortschrittsereignisse/Check-Reihenfolge und ein grosszuegiges, begruendetes
Laufzeitbudget oder Verhaeltnis-/Fixture-Budget mit diagnostischer Ausgabe."

The deterministic progress/order tests live in test_validate_run_checks.py
and need no timing at all. This file adds exactly the generous, justified
wall-clock budget those deterministic tests don't cover:

  1. A fast, always-on structural test: automation_safety.tracked_automation_paths()
     must stay fast (it was never the bottleneck — measured 0.14-0.25s for
     116 paths) using a generous ratio budget relative to a fresh baseline
     measurement, with diagnostic output on failure. This runs in every test
     invocation because it is cheap.
  2. An opt-in (env-var gated, skipped by default) full end-to-end budget
     test against the real repository, asserting a generous ceiling well
     above the measured 384.26s baseline (with headroom for slower hosts),
     and printing full diagnostic timing on failure. Skipped by default
     because a ~6-7 minute test does not belong in the default fast test
     loop; it exists so the budget claim above is independently re-checkable
     on demand, e.g. before trusting a future Feature-0037 checkpoint.
"""
import os
import sys
import time
import unittest
from pathlib import Path

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS = os.path.join(_SRC, "tools")
for path in (_SRC, _TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import automation_safety  # noqa: E402

_ROOT = Path(_SRC).parent

# Measured baseline (validate-py-nontermination-20260827, this investigation):
# tracked_automation_paths(): ~0.14-0.25s for 116 paths.
# Generous ratio: allow up to 20x the slower end of that measured range before
# treating it as a regression signal. This is intentionally loose — the point
# is to catch a real algorithmic regression (e.g. accidental O(n^2) path
# handling), not to police normal host-to-host variance.
_PATH_DISCOVERY_BASELINE_S = 0.25
_PATH_DISCOVERY_BUDGET_RATIO = 20

# Measured baseline for the full end-to-end scan (see validate.py's
# check_automation_safety docstring for the exact reproduction command).
_FULL_SCAN_BASELINE_S = 384.26
_FULL_SCAN_BUDGET_RATIO = 3  # generous: ~19 minutes ceiling on a 384s baseline


class PathDiscoveryBudgetTests(unittest.TestCase):
    def test_tracked_automation_paths_stays_within_generous_ratio_budget(self):
        started = time.time()
        paths, errors = automation_safety.tracked_automation_paths(_ROOT)
        elapsed = time.time() - started
        budget = _PATH_DISCOVERY_BASELINE_S * _PATH_DISCOVERY_BUDGET_RATIO
        self.assertEqual(
            errors, [],
            "tracked_automation_paths reported errors: %r" % (errors,),
        )
        self.assertGreater(
            len(paths), 0,
            "expected at least one tracked automation path in this repository",
        )
        self.assertLessEqual(
            elapsed, budget,
            "tracked_automation_paths took %.3fs for %d paths, budget is "
            "%.3fs (%.0fx measured baseline %.3fs) — this function was never "
            "the bottleneck in the validate-py-nontermination-20260827 "
            "investigation (path discovery, not scanning); a regression here "
            "signals something new, not the known scan_text cost."
            % (elapsed, len(paths), budget, _PATH_DISCOVERY_BUDGET_RATIO,
               _PATH_DISCOVERY_BASELINE_S),
        )


@unittest.skipUnless(
    os.environ.get("RUN_SLOW_VALIDATE_BUDGET") == "1",
    "opt-in: set RUN_SLOW_VALIDATE_BUDGET=1 to run the ~6-7 minute full "
    "automation-safety scan budget check",
)
class FullScanBudgetTests(unittest.TestCase):
    def test_scan_repository_stays_within_generous_ratio_budget(self):
        started = time.time()
        report = automation_safety.scan_repository(
            _ROOT,
            policy_path=_ROOT / automation_safety.DEFAULT_POLICY,
        )
        elapsed = time.time() - started
        budget = _FULL_SCAN_BASELINE_S * _FULL_SCAN_BUDGET_RATIO
        scanned = len(report.get("scanned", report.get("scanned_paths", [])) or [])
        self.assertLessEqual(
            elapsed, budget,
            "scan_repository took %.2fs for %d scanned paths, budget is "
            "%.2fs (%.0fx measured baseline %.2fs, "
            "validate-py-nontermination-20260827). See "
            "validate.check_automation_safety's docstring for the "
            "reproduction command and the identified cost concentration "
            "(automation_safety._shell_structural_text via scan_shell, "
            "not spread evenly across files)."
            % (elapsed, scanned, budget, _FULL_SCAN_BUDGET_RATIO,
               _FULL_SCAN_BASELINE_S),
        )


if __name__ == "__main__":
    unittest.main()
