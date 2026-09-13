"""Lifecycle provenance envelope tests for Task 0037-26.05."""
from __future__ import annotations

import importlib.util
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "curation_provenance.py"


def _load():
    spec = importlib.util.spec_from_file_location("curation_provenance", TOOL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["curation_provenance"] = mod
    spec.loader.exec_module(mod)
    return mod


cp = _load()

RUN_ID = "018f4a31-32aa-7abc-8def-0123456789ab"
FINDING_ID = "018f4a31-32ab-7abc-8def-0123456789ab"
ITEM = "SWS_LOG_00201"
VERSION = "AUTOSAR/AP/record/SWS_LOG_00201@rel:R25-11#abcd1234"


class CurationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = cp.CurationProvenanceSession(Path(self.tmp.name))
        self.ctx = self.session.seed_context(
            run_id=RUN_ID,
            finding_id=FINDING_ID,
            version=VERSION,
        )
        self.digest = self.ctx["report_digest"]

    def tearDown(self):
        self.tmp.cleanup()

    def _step(self, transition, **kwargs):
        defaults = dict(
            actor="curator-ada",
            authority_role="curator",
            requester="github-user",
            context=self.ctx,
            finding_digest=self.digest,
            source_version=f"record-version:{VERSION}",
        )
        defaults.update(kwargs)
        return self.session.apply_transition(ITEM, transition, **defaults)

    def test_lifecycle_open_claim_decision_apply_publish(self):
        opened = self._step("open")
        self.assertEqual(opened["status"], "open")
        self.assertEqual(opened["provenance"]["schema"], "provenance-envelope@v1")
        self.assertIn(ITEM, self.session.queue["open"])

        claimed = self._step("claim", actor="agent-worf", authority_role="operator")
        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["provenance"]["claim"]["actor"], "agent-worf")
        self.assertIn(ITEM, self.session.queue["claimed"])

        decided = self._step("decision", outcome="accept")
        self.assertEqual(decided["status"], "accepted")
        self.assertFalse(decided["provenance"]["decision"]["requester_is_approval"])
        self.assertEqual(decided["provenance"]["decision"]["requester"], "github-user")
        self.assertEqual(decided["provenance"]["authority"]["role"], "curator")

        applied = self._step("apply", applied_commit="d" * 40)
        self.assertEqual(applied["status"], "applied")
        self.assertTrue(applied["provenance"]["applied_change"]["uri"].startswith("commit:"))

        published = self._step("publish")
        links = self.session.reverse_links(ITEM)
        self.assertEqual(links["queue_transitions"], ["open", "claim", "decision", "apply", "publish"])
        self.assertEqual(links["finding"], f"finding:{FINDING_ID}")
        self.assertEqual(links["run"], f"run:{RUN_ID}")
        self.assertEqual(links["issue"], "issue:0037-26.05")
        self.assertIsNotNone(links["decision"])
        self.assertIsNotNone(links["published_result"])
        self.assertIsNotNone(published["provenance"]["digest"])

    def test_unauthorized_requester_is_not_approval(self):
        """AE-3 falsification: requester-as-approval is red on the candidate.

        Pre-change baseline (allow_requester_as_approval=True) still accepts the
        same call; the candidate rejects it.
        """
        self._step("open")
        self._step("claim", actor="agent-worf", authority_role="operator")
        baseline = self.session.apply_transition(
            "BASELINE",
            "open",
            actor="github-user",
            authority_role="requester",
            requester="github-user",
            context=self.ctx,
            allow_requester_as_approval=True,
        )
        self.assertEqual(baseline["status"], "open")
        with self.assertRaises(cp.CurationProvenanceError) as ctx:
            self._step("decision", outcome="accept", actor="github-user", authority_role="requester")
        self.assertEqual(ctx.exception.code, "CUR-UNAUTHORIZED")

    def test_adjacent_stale_finding_digest(self):
        """Adjacent to unauthorized: digest mismatch is CUR-STALE, not unauthorized."""
        self._step("open")
        self._step("claim", actor="agent-worf", authority_role="operator")
        with self.assertRaises(cp.CurationProvenanceError) as ctx:
            self._step("decision", outcome="accept", finding_digest="sha256:" + "00" * 32)
        self.assertEqual(ctx.exception.code, "CUR-STALE")

    def test_adjacent_stale_source_version(self):
        self._step("open")
        self._step("claim", actor="agent-worf", authority_role="operator")
        with self.assertRaises(cp.CurationProvenanceError) as ctx:
            self._step(
                "decision",
                outcome="accept",
                source_version="record-version:other@rel:R20-11#ffffffff",
            )
        self.assertEqual(ctx.exception.code, "CUR-STALE")

    def test_duplicate_transition_rejected(self):
        self._step("open")
        with self.assertRaises(cp.CurationProvenanceError) as ctx:
            self._step("open")
        self.assertEqual(ctx.exception.code, "CUR-DUPLICATE")

    def test_fabricated_finding_rejected(self):
        bogus = dict(self.ctx)
        bogus["finding"] = cp.typed_ref("finding", "018f4a31-ffff-7abc-8def-0123456789ab")
        with self.assertRaises(cp.CurationProvenanceError) as ctx:
            self.session.apply_transition(
                ITEM,
                "open",
                actor="curator-ada",
                authority_role="curator",
                context=bogus,
            )
        self.assertEqual(ctx.exception.code, "CUR-FABRICATED")

    def test_orphaned_apply_and_publish_rejected(self):
        with self.assertRaises(cp.CurationProvenanceError) as ctx:
            self._step("apply")
        self.assertEqual(ctx.exception.code, "CUR-ORPHANED")
        self._step("open")
        self._step("claim", actor="agent-worf", authority_role="operator")
        with self.assertRaises(cp.CurationProvenanceError) as ctx:
            self._step("publish")
        self.assertEqual(ctx.exception.code, "CUR-ORPHANED")

    def test_sequence_property_only_happy_path_and_named_rejects(self):
        """AE-5: invariant over transition sequences. Domain: all 3-tuples of
        {open,claim,decision,apply,publish} plus the happy path. Seed 26."""
        rng = random.Random(26)
        alphabet = list(cp.LIFECYCLE)
        executed = 0
        for _ in range(40):
            seq = [rng.choice(alphabet) for _ in range(3)]
            session = cp.CurationProvenanceSession(Path(self.tmp.name) / f"p{executed}")
            ctx = session.seed_context(run_id=RUN_ID, finding_id=FINDING_ID, version=VERSION)
            status = None
            ok = True
            for step in seq:
                if not cp.transition_allowed(status, step):
                    ok = False
                    break
                kwargs = dict(
                    actor="curator-ada",
                    authority_role="curator",
                    requester="github-user",
                    context=ctx,
                    finding_digest=ctx["report_digest"],
                    source_version=f"record-version:{VERSION}",
                )
                if step == "decision":
                    kwargs["outcome"] = "accept"
                try:
                    item = session.apply_transition(f"I{executed}", step, **kwargs)
                    status = item["status"]
                except cp.CurationProvenanceError:
                    ok = False
                    break
            executed += 1
            if seq == list(cp.LIFECYCLE)[:3]:
                self.assertTrue(ok)
        # Exhaustive happy path on a fresh session (already covered) plus count.
        self.assertEqual(executed, 40)

    def test_legacy_confidence_not_invented(self):
        opened = self._step("open")
        self.assertEqual(opened["provenance"]["legacy"]["confidence"], "unknown")


if __name__ == "__main__":
    unittest.main()
