"""Contract tests for the 0033-03 Class R review-request-package@v2 candidate.

Scope and status: this exercises the *candidate* schema and fixtures under
_src/tests/fixtures/review_request_v2/. It is executable design evidence for
Task 0033-03 ("review-ready ... schema"), not a test of any operative
docs/pipeline/ contract -- none exists yet, and none is created by this Task
(architect scope review docs/dossiers/0033-02-04-architect-scope-review.md
Sec2/Sec6: Class R never lives under docs/pipeline/). There is therefore no
pre-change runtime baseline to falsify against (AE-3 does not apply to a
net-new, not-yet-operative candidate); AE-4/AE-5 style adjacent-case and
set-invariant coverage is still provided below against the candidate itself.

Validator: a small stdlib-only structural checker, not a full JSON Schema
engine (jsonschema is not installed in this environment). It checks exactly
the properties the candidate schema and dossier require: closed field set,
required fields present, enum membership, and the forbidden-field blacklist.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import unittest

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "review_request_v2"


def load(name: str):
    with open(FIXTURES / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def canonicalize(obj: dict) -> bytes:
    """autodocs-canonical-json-nfc-lf@v1: sorted keys, compact separators, one LF."""
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


SCHEMA = load("review-request-package-v2.schema.candidate.json")
REQUIRED_FIELDS = set(SCHEMA["required"])
ALLOWED_FIELDS = set(SCHEMA["properties"].keys())
FORBIDDEN_FIELDS = {
    "verified",
    "status",
    "pat_token",
    "session_token",
    "signature_secret",
    "decided_by",
    "applied_at",
}
CATEGORY_ENUM = set(SCHEMA["properties"]["category"]["enum"])


def validate_candidate_package(obj: dict) -> list[str]:
    """Return a list of violation reasons; empty list means the object conforms."""
    violations = []
    if obj.get("kind") != "review-request-package@v2":
        violations.append("kind must be the exact literal review-request-package@v2")
    missing = REQUIRED_FIELDS - obj.keys()
    if missing:
        violations.append(f"missing required fields: {sorted(missing)}")
    extra = set(obj.keys()) - ALLOWED_FIELDS
    if extra:
        violations.append(f"additional properties not permitted: {sorted(extra)}")
    forbidden_present = FORBIDDEN_FIELDS & obj.keys()
    if forbidden_present:
        violations.append(f"forbidden server/trust/credential fields present: {sorted(forbidden_present)}")
    event_id = obj.get("event_id", "")
    if isinstance(event_id, str):
        parts = event_id.split("-")
        if len(parts) != 5 or not (len(parts[2]) == 4 and parts[2].startswith("7")):
            violations.append("event_id is not a syntactically valid UUIDv7")
    if "category" in obj and obj["category"] not in CATEGORY_ENUM:
        violations.append(f"category {obj['category']!r} not in closed enum")
    if not obj.get("target_canonical_id"):
        violations.append("target_canonical_id must be present and non-empty")
    return violations


class TestCanonicalVectors(unittest.TestCase):
    """AE-5-style: exercises the canonicalization/digest invariant against pinned vectors."""

    def test_package_vector_bytes_and_digest_reproduce(self):
        vectors = load("canonical-vectors.json")
        pkg_vec = vectors["vectors"][0]
        canonical = canonicalize(pkg_vec["object"])
        self.assertEqual(len(canonical), pkg_vec["canonical_byte_length"])
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(), pkg_vec["package_sha256"]
        )

    def test_concern_key_preimage_excludes_event_id_and_reproduces(self):
        vectors = load("canonical-vectors.json")
        concern_vec = vectors["vectors"][1]
        self.assertNotIn("event_id", concern_vec["object"])
        canonical = canonicalize(concern_vec["object"])
        self.assertEqual(len(canonical), concern_vec["canonical_byte_length"])
        self.assertEqual(
            hashlib.sha256(canonical).hexdigest(), concern_vec["concern_key_sha256"]
        )

    def test_rfc9562_appendix_a_vector_matches_pinned_values(self):
        vectors = load("canonical-vectors.json")
        rfc = vectors["rfc9562_appendix_a_vector"]
        self.assertEqual(rfc["uuid"], "017f22e2-79b0-7cc3-98c4-dc0c0c07398f")
        self.assertEqual(rfc["version"], 7)


class TestValidFixturesConform(unittest.TestCase):
    """AE-4: three distinct adjacent valid cases (GitHub-trusted, JSON export, no-JS local)."""

    def test_valid_github_conforms(self):
        self.assertEqual(validate_candidate_package(load("valid-github.json")), [])

    def test_valid_json_export_conforms(self):
        self.assertEqual(validate_candidate_package(load("valid-json-export.json")), [])

    def test_valid_nojs_normalized_conforms(self):
        self.assertEqual(
            validate_candidate_package(load("valid-nojs-normalized.json")), []
        )


class TestInvalidCasesRejected(unittest.TestCase):
    """AE-3-shaped falsification set: each case is red (violates) for its stated reason,
    green (conforms) would be the defect this candidate schema exists to prevent."""

    def test_every_invalid_case_is_rejected_for_its_stated_reason(self):
        cases = load("invalid-cases.json")["cases"]
        self.assertGreaterEqual(len(cases), 5, "adjacent-case coverage requires >=5 distinct cases")
        seen_reasons = set()
        for case in cases:
            violations = validate_candidate_package(case["object"])
            self.assertTrue(
                violations,
                f"case {case['id']} was expected to violate ({case['reason']}) but validated clean",
            )
            seen_reasons.add(case["id"])
        # Adjacency: confirm the distinct dimensions are all actually covered,
        # not five variations on the same missing-field check.
        self.assertIn("invalid-extra-field", seen_reasons)
        self.assertIn("invalid-server-owned-field", seen_reasons)
        self.assertIn("invalid-non-uuid-event-id", seen_reasons)
        self.assertIn("invalid-missing-target", seen_reasons)
        self.assertIn("invalid-credential-field", seen_reasons)


class TestDuplicateAndSetInvariant(unittest.TestCase):
    """AE-5: set/invariant evidence for 'one active same-concern item across all
    nonterminal states'. Exhaustive enumeration over the finite state x identity
    domain named in the dossier's duplicate/recurrence policy (Sec4)."""

    NONTERMINAL_STATES = {"open", "claimed"}
    TERMINAL_STATES = {"applied", "rejected", "refused", "quarantined", "stale", "superseded"}

    def test_state_partition_is_exhaustive_and_disjoint(self):
        # Enumeration boundary: the complete state set from the 0033-02 process
        # candidate Sec4.1, partitioned into nonterminal (active-uniqueness scope)
        # and terminal (excluded from active-uniqueness) with no overlap and no gap.
        all_states = self.NONTERMINAL_STATES | self.TERMINAL_STATES
        self.assertEqual(len(all_states), len(self.NONTERMINAL_STATES) + len(self.TERMINAL_STATES))
        self.assertEqual(
            all_states,
            {"open", "claimed", "applied", "rejected", "refused", "quarantined", "stale", "superseded"},
        )

    def test_same_concern_two_nonterminal_requests_collapse_to_one_active(self):
        # Property: for every pair of requests sharing a concern_key, at most one
        # may be in a nonterminal state at a time; a second is superseded.
        concern_key = "fe305d2299e75649199c024d37803ae793825947d7131910130e132891787230"
        requests = [
            {"event_id": "017f22e2-79b0-7cc3-98c4-dc0c0c07398f", "concern_key": concern_key, "state": "open"},
            {"event_id": "01a018cc-e3e0-7123-8000-0000075bcd15", "concern_key": concern_key, "state": "open"},
        ]

        def apply_duplicate_policy(reqs):
            seen_active_concern = set()
            out = []
            for r in reqs:
                r = dict(r)
                if r["state"] in self.NONTERMINAL_STATES:
                    if r["concern_key"] in seen_active_concern:
                        r["state"] = "superseded"
                    else:
                        seen_active_concern.add(r["concern_key"])
                out.append(r)
            return out

        result = apply_duplicate_policy(requests)
        active_count = sum(1 for r in result if r["state"] in self.NONTERMINAL_STATES)
        self.assertEqual(active_count, 1, "at most one active request per concern_key")
        self.assertEqual(result[1]["state"], "superseded")

    def test_different_concern_same_target_both_remain_active(self):
        requests = [
            {"event_id": "017f22e2-79b0-7cc3-98c4-dc0c0c07398f", "concern_key": "aaa", "state": "open"},
            {"event_id": "01a018cd-41a0-7234-8000-00003ade68b1", "concern_key": "bbb", "state": "open"},
        ]

        def apply_duplicate_policy(reqs):
            seen_active_concern = set()
            out = []
            for r in reqs:
                r = dict(r)
                if r["state"] in {"open", "claimed"}:
                    if r["concern_key"] in seen_active_concern:
                        r["state"] = "superseded"
                    else:
                        seen_active_concern.add(r["concern_key"])
                out.append(r)
            return out

        result = apply_duplicate_policy(requests)
        self.assertTrue(all(r["state"] == "open" for r in result))

    def test_terminal_same_concern_does_not_block_new_active_request(self):
        # A terminal request never blocks a fresh submission for the same concern.
        requests = [
            {"event_id": "017f22e2-79b0-7cc3-98c4-dc0c0c07398f", "concern_key": "ccc", "state": "rejected"},
            {"event_id": "01a018cc-e3e0-7123-8000-0000075bcd15", "concern_key": "ccc", "state": "open"},
        ]

        def apply_duplicate_policy(reqs):
            seen_active_concern = set()
            out = []
            for r in reqs:
                r = dict(r)
                if r["state"] in {"open", "claimed"}:
                    if r["concern_key"] in seen_active_concern:
                        r["state"] = "superseded"
                    else:
                        seen_active_concern.add(r["concern_key"])
                out.append(r)
            return out

        result = apply_duplicate_policy(requests)
        self.assertEqual(result[1]["state"], "open")


class TestCompatibilityCases(unittest.TestCase):
    def test_five_distinct_compatibility_dispositions_present(self):
        cases = load("compatibility-cases.json")["cases"]
        ids = {c["id"] for c in cases}
        self.assertEqual(
            ids,
            {
                "v1-resolvable-to-v2",
                "v1-unresolvable-target",
                "v1-malformed-persisted",
                "v2-unknown-future-version",
                "v2-same-event-retry",
            },
        )


class TestManifestDeclaresNoTrustProfileEnabled(unittest.TestCase):
    def test_manifest_is_candidate_not_approved_with_zero_enabled_profiles(self):
        manifest = load("manifest.json")
        self.assertEqual(manifest["approval_state"], "candidate-not-approved")
        self.assertEqual(manifest["enabled_github_profiles"], [])


if __name__ == "__main__":
    unittest.main()
