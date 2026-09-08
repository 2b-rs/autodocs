"""Focused regressions for the 0019 handoff candidate-scope binding."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / 'docs/pipeline/approvals/0019-acceptance-packages/handoff-scope-correction-20260822T013000Z/validate_handoff_scope.py'
SPEC = importlib.util.spec_from_file_location('handoff_scope_validator', VALIDATOR)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HandoffScopeRegressionTests(unittest.TestCase):
    def test_manifest_includes_merged_corrective_claim(self) -> None:
        expected = MODULE.expected_scope()
        claim = 'A\tTODO-worf-martok-0019-11-20260821T220000Z-c7a91d42.md'
        self.assertIn(claim, expected)
        MODULE.validate_scope(expected, expected)

    def test_unexpected_file_is_rejected(self) -> None:
        expected = MODULE.expected_scope()
        with self.assertRaisesRegex(SystemExit, 'candidate scope differs'):
            MODULE.validate_scope([*expected, 'A\tunexpected-file.txt'], expected)


if __name__ == '__main__':
    unittest.main()
