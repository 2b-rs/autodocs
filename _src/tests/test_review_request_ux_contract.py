# pyright: basic

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UX = ROOT / "docs" / "pipeline" / "review-request-ux.md"
SCENARIOS = ROOT / "docs" / "dossiers" / "0033-04-ux-scenarios.md"


class ReviewRequestUxContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ux = UX.read_text(encoding="utf-8")
        cls.scenarios = SCENARIOS.read_text(encoding="utf-8")

    def test_candidate_is_unapproved_and_has_no_runtime_authority(self):
        self.assertIn("**not approved**", self.ux)
        self.assertIn("not a browser/store/\ntransport implementation", self.ux)
        self.assertIn("never creates a queue\nitem", self.ux)
        self.assertIn("does not change this record", self.ux)
        self.assertNotIn("Status: drafted", self.ux)

    def test_eligible_action_excludes_legacy_invalid_and_nonrecord_contexts(self):
        self.assertIn("published, eligible `valid/*` record", self.ux)
        self.assertIn("`valid/curator-decided`", self.ux)
        self.assertIn("excluded `invalid/*`", self.ux)
        self.assertIn("multi-record, index, report, diagram, search, download or process page", self.ux)
        self.assertIn("No package is constructed", self.ux)

    def test_fields_evidence_identity_and_public_disclosure_are_closed(self):
        for token in (
            "`category`", "`rationale`", "`evidence_refs`", "derived `kind=url`",
            "derived `kind=note`", "`anonymous` or `self-declared`",
            "no GitHub-authenticated client value exists", "public and difficult to delete",
            "secrets/restricted personal data must\nnot be entered",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.ux)

    def test_confirmation_export_retry_and_server_fields_bind_exact_bytes(self):
        for token in (
            "exact canonical package bytes", "one package builder for\ndirect and collected paths",
            "`exported`", "Downloaded — not submitted or queued.",
            "reuses the exact event ID, package\nbytes, digest and concern key",
            "Server-owned envelope fields", "only after a trusted adapter/status\nprojection supplies them",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.ux)
        self.assertNotIn("page-age check", self.ux)

    def test_single_typed_store_migration_is_non_destructive_and_credential_blind(self):
        for token in (
            "one physical database `ara-review-browser`, version `2`", "object store `collection`",
            "`entry_type=feedback`", "`payload_schema=review-request-package@v2`",
            "PAT, token and\nidentity convenience keys are excluded", "Source is preserved",
            "same ID/different digest aborts", "tombstones prevent resurrection",
            "Multi-tab\nupdates", "Clear-local-data",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.ux)

    def test_accessibility_mobile_and_nojs_requirements_are_implementable(self):
        for token in (
            "unique accessible name", "unique `aria-labelledby`", "traps focus",
            "returns focus", "polite live region", "assertive bounded region",
            "**768 px and above**", "**below 768 px**", "44 CSS-pixel minimum targets",
            "static URL that pretends to mint package\nmetadata", "trusted ingress adapter refetches the Issue",
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.ux)

    def test_fourteen_executable_scenarios_each_map_to_later_tests(self):
        ids = re.findall(r"\| (UX-\d{2}) \|", self.scenarios)
        self.assertEqual(ids, [f"UX-{number:02d}" for number in range(1, 15)])
        for scenario_id in ids:
            row = next(line for line in self.scenarios.splitlines() if f"| {scenario_id} |" in line)
            with self.subTest(scenario_id=scenario_id):
                self.assertRegex(row, r"`0033-[0-9.]+(?:/[0-9.]+)?`")
                self.assertIn("UXC-", row)
        lower_scenarios = self.scenarios.lower()
        for required in ("duplicate race", "stale", "json", "github", "signed-out", "retry", "cancel", "mobile", "keyboard", "post-ingestion"):
            with self.subTest(required=required):
                self.assertIn(required, lower_scenarios)


if __name__ == "__main__":
    unittest.main()
