"""Tests for _src/tools/manage_approval_readiness.py (Task 0038-15).

Covers the eight fixture categories required by the Task's Definition of
Done — ready, missing role, wrong fingerprint, stale policy, unavailable
handle, absent service control, revoke, and malformed policy — plus the
supporting invariants: read-only JSON-default behavior, no in-place policy
mutation, schema-version enforcement, and metadata-vs-verified capability
distinction.

Real SSH key material used below is synthetic, generated solely for this
test file (not the project's live signing/deploy keys), and only the
*public* half is ever embedded.
"""
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "manage_approval_readiness.py"
SPEC = importlib.util.spec_from_file_location("manage_approval_readiness", TOOL)
assert SPEC and SPEC.loader
mar = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mar
SPEC.loader.exec_module(mar)

# Two synthetic ed25519 test keys generated for this test module only.
# Fingerprints below were independently confirmed with `ssh-keygen -lf`.
KEY_A_TYPE = "ssh-ed25519"
KEY_A_DATA = "AAAAC3NzaC1lZDI1NTE5AAAAILsdyHKcHVeWN+gIgF/3uiu0aZqbi8AeSitshNvIxeBt"
KEY_A_LINE = f"{KEY_A_TYPE} {KEY_A_DATA} roleA"
KEY_A_FP = "SHA256:0kxOVpj52oe5Fj5SgRvYK7745bh8BmvD1uc7K8xra0A"

KEY_B_TYPE = "ssh-ed25519"
KEY_B_DATA = "AAAAC3NzaC1lZDI1NTE5AAAAIAEqX4NdA/0N9zEpl85RO02lsCwQqb+c0qQwHHfNI45s"
KEY_B_LINE = f"{KEY_B_TYPE} {KEY_B_DATA} roleB"
KEY_B_FP = "SHA256:tiFhsEI0t7wcoCM7KmTXfX5y3H+Z7Y2J1AZGZWu5+TA"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


ALL_ROLES = ("repository-owner", "architecture-approver", "security", "privacy", "release")


def base_authorities(roles_present=ALL_ROLES):
    principals = []
    for role in roles_present:
        principals.append({
            "role": role,
            "identity": f"{role} <owner@example.com>",
            "ssh_fingerprint": KEY_A_FP,
            "key_type": "ssh-ed25519",
        })
    return {
        "schema": "issue-authorities@v1",
        "independent_channel": "https://example.com/owner.keys",
        "principals": principals,
    }


def base_credential_handles():
    return {
        "schema": "credential-handles@v1",
        "handles": [{
            "handle_id": "deploy-key",
            "scope": "push refs/x to origin",
            "public_key": KEY_B_LINE,
            "fingerprint": KEY_B_FP,
        }],
    }


def base_runner_service():
    return {
        "schema": "runner-service@v1",
        "health_check": "true",
        "restart_path": "restart.sh",
        "rollback_path": "rollback.sh",
        "operator": "tobias.anton",
    }


# allowed_signers format: "<principal> namespaces=\"git\" <type> <data>"
ALLOWED_SIGNERS_TEXT = f'owner@example.com namespaces="git" {KEY_A_TYPE} {KEY_A_DATA}\n'


class ReadinessFixture:
    """Builds a temp repo root with issues/_policy/* and a real git repo
    (for remote/signing-key config checks) that can be patched per test."""

    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=self.root, check=True)
        self.paths = mar.policy_paths(self.root)
        write_json(self.paths["authorities"], base_authorities())
        write_json(self.paths["credential_handles"], base_credential_handles())
        write_json(self.paths["runner_service"], base_runner_service())
        self.paths["allowed_signers"].parent.mkdir(parents=True, exist_ok=True)
        self.paths["allowed_signers"].write_text(ALLOWED_SIGNERS_TEXT, encoding="utf-8")
        (self.root / "docs" / "pipeline").mkdir(parents=True, exist_ok=True)
        (self.paths["package_review"]).write_text("{}", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=self.root, check=True)

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def configure_signing(self, key_pub_path: Path):
        self.git("config", "--local", "gpg.format", "ssh")
        self.git("config", "--local", "user.signingkey", str(key_pub_path))
        self.git("config", "--local", "gpg.ssh.allowedSignersFile", str(self.paths["allowed_signers"]))

    def configure_remote(self, url="git@example.com:org/repo.git"):
        self.git("remote", "add", "origin", url)

    def close(self):
        self.temporary.cleanup()


class ParseAllowedSignersTest(unittest.TestCase):
    def test_active_entry_parses_and_fingerprints(self):
        entries = mar.parse_allowed_signers(ALLOWED_SIGNERS_TEXT)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertFalse(e["malformed"])
        self.assertFalse(e["revoked"])
        self.assertEqual(e["fingerprint"], KEY_A_FP)

    def test_malformed_short_line(self):
        entries = mar.parse_allowed_signers("owner@example.com ssh-ed25519\n")
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["malformed"])

    def test_revoked_comment_marks_entry(self):
        text = f'owner@example.com namespaces="git" {KEY_A_TYPE} {KEY_A_DATA}  # revoked 2026-08-20\n'
        entries = mar.parse_allowed_signers(text)
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["revoked"])

    def test_blank_and_comment_lines_skipped(self):
        text = "\n# just a comment\n   \n"
        self.assertEqual(mar.parse_allowed_signers(text), [])


class FingerprintComputationTest(unittest.TestCase):
    def test_matches_real_ssh_keygen_output(self):
        self.assertEqual(mar._fingerprint_from_keydata(KEY_A_TYPE, KEY_A_DATA), KEY_A_FP)
        self.assertEqual(mar._fingerprint_from_keydata(KEY_B_TYPE, KEY_B_DATA), KEY_B_FP)

    def test_invalid_base64_returns_none(self):
        self.assertIsNone(mar._fingerprint_from_keydata("ssh-ed25519", "not-base64!!"))

    def test_unknown_key_type_returns_none(self):
        self.assertIsNone(mar._fingerprint_from_keydata("ssh-unknown", KEY_A_DATA))


class PlaceholderTest(unittest.TestCase):
    def test_placeholder_markers(self):
        for bad in ("SHA256:<FINGERPRINT>", "", None, "TODO", "placeholder-value"):
            self.assertTrue(mar._is_placeholder(bad))

    def test_real_value_not_placeholder(self):
        self.assertFalse(mar._is_placeholder(KEY_A_FP))


class ReadyCaseTest(unittest.TestCase):
    """Fixture category: ready — every check passes."""

    def setUp(self):
        self.fx = ReadinessFixture()
        self.fx.configure_remote()
        self.fx.configure_signing(self.fx.root / "does-not-need-to-exist.pub")
        # user.signingkey must point at an existing file for the metadata check.
        key_file = self.fx.root / "signing.pub"
        key_file.write_text(f"{KEY_A_TYPE} {KEY_A_DATA} owner\n", encoding="utf-8")
        self.fx.git("config", "--local", "user.signingkey", str(key_file))

    def tearDown(self):
        self.fx.close()

    def test_all_checks_ok(self):
        results = mar.run_checks(self.fx.root)
        statuses = {r["label"]: r["status"] for r in results}
        self.assertTrue(all(s == "OK" for s in statuses.values()), statuses)

    def test_authorities_and_credential_handle_are_verified_not_just_metadata(self):
        results = mar.run_checks(self.fx.root)
        by_label = {r["label"]: r for r in results}
        self.assertEqual(by_label["authorities.json complete"]["capability"], "verified")
        self.assertEqual(by_label["Credential handle"]["capability"], "verified")
        self.assertEqual(by_label["allowed_signers populated"]["capability"], "verified")

    def test_cmd_check_json_all_ok(self):
        with mock.patch("sys.stdout") as _stdout:
            rc = mar.cmd_check(self.fx.root, True)
        self.assertEqual(rc, 0)


class MissingRoleTest(unittest.TestCase):
    """Fixture category: missing role."""

    def setUp(self):
        self.fx = ReadinessFixture()
        write_json(self.fx.paths["authorities"], base_authorities(roles_present=(
            "repository-owner", "security", "privacy", "release")))  # architecture-approver missing

    def tearDown(self):
        self.fx.close()

    def test_authorities_blocked_missing_role(self):
        result = mar.check_authorities(self.fx.root, [])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("missing role: architecture-approver", result["detail"])


class WrongFingerprintTest(unittest.TestCase):
    """Fixture category: wrong fingerprint."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_authorities_fingerprint_not_in_allowed_signers(self):
        _, active = mar.check_allowed_signers(self.fx.root)
        result = mar.check_authorities(self.fx.root, active)
        # authorities.json uses KEY_A_FP which IS in allowed_signers by default;
        # corrupt it to a well-formed but wrong fingerprint.
        bad = base_authorities()
        bad["principals"][0]["ssh_fingerprint"] = KEY_B_FP  # not in allowed_signers
        write_json(self.fx.paths["authorities"], bad)
        result = mar.check_authorities(self.fx.root, active)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("wrong fingerprint", result["detail"])

    def test_credential_handle_fingerprint_mismatch(self):
        bad = base_credential_handles()
        bad["handles"][0]["fingerprint"] = KEY_A_FP  # does not match public_key (KEY_B)
        write_json(self.fx.paths["credential_handles"], bad)
        result = mar.check_credential_handle(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("wrong fingerprint", result["detail"])


class StalePolicyTest(unittest.TestCase):
    """Fixture category: stale policy (schema version missing/mismatched)."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_authorities_stale_schema_blocks(self):
        stale = base_authorities()
        stale["schema"] = "issue-authorities@v0"
        write_json(self.fx.paths["authorities"], stale)
        result = mar.check_authorities(self.fx.root, [])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("stale policy", result["detail"])

    def test_authorities_missing_schema_field_blocks(self):
        stale = base_authorities()
        del stale["schema"]
        write_json(self.fx.paths["authorities"], stale)
        result = mar.check_authorities(self.fx.root, [])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("stale policy", result["detail"])

    def test_credential_handles_stale_schema_blocks(self):
        stale = base_credential_handles()
        stale["schema"] = "credential-handles@v0"
        write_json(self.fx.paths["credential_handles"], stale)
        result = mar.check_credential_handle(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("stale policy", result["detail"])

    def test_runner_service_stale_schema_blocks(self):
        stale = base_runner_service()
        stale["schema"] = "runner-service@v0"
        write_json(self.fx.paths["runner_service"], stale)
        result = mar.check_runner_service(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("stale policy", result["detail"])


class UnavailableHandleTest(unittest.TestCase):
    """Fixture category: unavailable handle — metadata present but capability
    cannot be independently verified."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_handle_missing_public_key_is_unavailable(self):
        data = base_credential_handles()
        del data["handles"][0]["public_key"]
        write_json(self.fx.paths["credential_handles"], data)
        result = mar.check_credential_handle(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["capability"], "unavailable")
        self.assertIn("capability unavailable", result["detail"])

    def test_no_active_handles_is_unavailable(self):
        data = base_credential_handles()
        data["handles"][0]["revoked"] = True
        write_json(self.fx.paths["credential_handles"], data)
        result = mar.check_credential_handle(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["capability"], "unavailable")


class AbsentServiceControlTest(unittest.TestCase):
    """Fixture category: absent service control."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_missing_rollback_path_blocks(self):
        data = base_runner_service()
        del data["rollback_path"]
        write_json(self.fx.paths["runner_service"], data)
        result = mar.check_runner_service(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("rollback_path", result["detail"])

    def test_never_executes_health_check_command(self):
        data = base_runner_service()
        data["health_check"] = "touch /tmp/should-never-be-created-by-readiness-check.marker"
        write_json(self.fx.paths["runner_service"], data)
        marker = Path("/tmp/should-never-be-created-by-readiness-check.marker")
        if marker.exists():
            marker.unlink()
        mar.check_runner_service(self.fx.root)
        self.assertFalse(marker.exists())


class RevokeTest(unittest.TestCase):
    """Fixture category: revoke."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_revoked_principal_role_becomes_missing(self):
        data = base_authorities()
        for p in data["principals"]:
            if p["role"] == "security":
                p["revoked"] = True
        write_json(self.fx.paths["authorities"], data)
        result = mar.check_authorities(self.fx.root, [])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("missing role: security", result["detail"])

    def test_revoked_credential_handle_excluded(self):
        data = base_credential_handles()
        data["handles"][0]["revoked"] = True
        write_json(self.fx.paths["credential_handles"], data)
        result = mar.check_credential_handle(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("no active", result["detail"])

    def test_revoked_signer_excluded_from_active(self):
        text = f'owner@example.com namespaces="git" {KEY_A_TYPE} {KEY_A_DATA}  # revoked\n'
        self.fx.paths["allowed_signers"].write_text(text, encoding="utf-8")
        result, active = mar.check_allowed_signers(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(active, [])


class MalformedPolicyTest(unittest.TestCase):
    """Fixture category: malformed policy."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_malformed_authorities_json(self):
        self.fx.paths["authorities"].write_text("{not valid json", encoding="utf-8")
        result = mar.check_authorities(self.fx.root, [])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("malformed policy", result["detail"])

    def test_malformed_credential_handles_json(self):
        self.fx.paths["credential_handles"].write_text("[1,2,", encoding="utf-8")
        result = mar.check_credential_handle(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("malformed policy", result["detail"])

    def test_malformed_runner_service_json(self):
        self.fx.paths["runner_service"].write_text("not json at all", encoding="utf-8")
        result = mar.check_runner_service(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("malformed policy", result["detail"])

    def test_malformed_allowed_signers_line(self):
        self.fx.paths["allowed_signers"].write_text("just two tokens\n", encoding="utf-8")
        result, active = mar.check_allowed_signers(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("malformed policy", result["detail"])
        self.assertEqual(active, [])


class MissingFileTest(unittest.TestCase):
    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_missing_authorities_file(self):
        self.fx.paths["authorities"].unlink()
        result = mar.check_authorities(self.fx.root, [])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("File missing", result["detail"])

    def test_missing_allowed_signers_file(self):
        self.fx.paths["allowed_signers"].unlink()
        result, active = mar.check_allowed_signers(self.fx.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(active, [])


class NeverExposesPrivateKeyPathTest(unittest.TestCase):
    """The signing-key check must never echo the configured key path."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_signing_key_detail_never_contains_configured_path(self):
        secret_looking_path = str(self.fx.root / "very" / "secret" / "id_ed25519")
        self.fx.git("config", "--local", "user.signingkey", secret_looking_path)
        result = mar.check_signing_key(self.fx.root)
        self.assertNotIn(secret_looking_path, result["detail"])
        self.assertNotIn(secret_looking_path, json.dumps(result))

    def test_missing_signing_key_message_has_no_path(self):
        result = mar.check_signing_key(self.fx.root)
        self.assertIn("user.signingkey not set", result["detail"])


class ProposeAuthoritiesPatchTest(unittest.TestCase):
    """The candidate/diff replacement for the removed in-place patch."""

    def setUp(self):
        self.fx = ReadinessFixture()
        placeholder = base_authorities()
        placeholder["principals"][0]["ssh_fingerprint"] = "SHA256:<FINGERPRINT>"
        write_json(self.fx.paths["authorities"], placeholder)
        self.key_file = self.fx.root / "signing.pub"
        self.key_file.write_text(f"{KEY_A_TYPE} {KEY_A_DATA} owner\n", encoding="utf-8")
        self.fx.git("config", "--local", "user.signingkey", str(self.key_file))

    def tearDown(self):
        self.fx.close()

    def test_never_writes_tracked_authorities_file(self):
        original = self.fx.paths["authorities"].read_text(encoding="utf-8")
        out_dir = self.fx.root / "output" / "approval-readiness"
        rc = mar.cmd_propose_authorities_patch(self.fx.root, out_dir=out_dir)
        self.assertEqual(rc, 0)
        self.assertEqual(self.fx.paths["authorities"].read_text(encoding="utf-8"), original,
                          "tracked policy file must never be mutated")

    def test_candidate_and_diff_are_written(self):
        out_dir = self.fx.root / "output" / "approval-readiness"
        mar.cmd_propose_authorities_patch(self.fx.root, out_dir=out_dir)
        candidate = out_dir / "authorities.candidate.json"
        diff = out_dir / "authorities.candidate.diff"
        self.assertTrue(candidate.exists())
        self.assertTrue(diff.exists())
        candidate_data = json.loads(candidate.read_text(encoding="utf-8"))
        self.assertEqual(candidate_data["principals"][0]["ssh_fingerprint"], KEY_A_FP)
        self.assertIn("authorities.candidate.json", diff.read_text(encoding="utf-8"))

    def test_no_placeholders_reports_nothing_to_propose(self):
        write_json(self.fx.paths["authorities"], base_authorities())  # no placeholders
        out_dir = self.fx.root / "output" / "approval-readiness"
        rc = mar.cmd_propose_authorities_patch(self.fx.root, out_dir=out_dir)
        self.assertEqual(rc, 0)
        self.assertFalse((out_dir / "authorities.candidate.json").exists())

    def test_missing_signing_key_fails_closed(self):
        self.fx.git("config", "--local", "--unset", "user.signingkey")
        out_dir = self.fx.root / "output" / "approval-readiness"
        rc = mar.cmd_propose_authorities_patch(self.fx.root, out_dir=out_dir)
        self.assertEqual(rc, 1)
        self.assertFalse(out_dir.exists())


class MainDefaultBehaviorTest(unittest.TestCase):
    """No-argument invocation must be the safe read-only JSON default and
    must not mutate anything."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_no_args_runs_json_check(self):
        buf = []
        with mock.patch("builtins.print", side_effect=lambda *a, **k: buf.append(" ".join(str(x) for x in a))):
            mar.main(["--root", str(self.fx.root)])
        output = "\n".join(buf)
        data = json.loads(output)
        self.assertEqual(data["schema"], "approval-readiness-result@v1")
        self.assertIn("checks", data)

    def test_no_args_does_not_touch_authorities_file(self):
        before = self.fx.paths["authorities"].read_text(encoding="utf-8")
        with mock.patch("builtins.print"):
            mar.main(["--root", str(self.fx.root)])
        after = self.fx.paths["authorities"].read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_check_text_mode_still_available(self):
        with mock.patch("builtins.print") as mocked_print:
            rc = mar.main(["--root", str(self.fx.root), "--check"])
        self.assertIn(rc, (0, 1))
        joined = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list if c.args)
        self.assertIn("Approval Readiness Check", joined)

    def test_legacy_patch_authorities_flag_is_alias(self):
        placeholder = base_authorities()
        placeholder["principals"][0]["ssh_fingerprint"] = "SHA256:<FINGERPRINT>"
        write_json(self.fx.paths["authorities"], placeholder)
        key_file = self.fx.root / "signing.pub"
        key_file.write_text(f"{KEY_A_TYPE} {KEY_A_DATA} owner\n", encoding="utf-8")
        self.fx.git("config", "--local", "user.signingkey", str(key_file))
        before = self.fx.paths["authorities"].read_text(encoding="utf-8")
        with mock.patch("builtins.print"):
            rc = mar.main(["--root", str(self.fx.root), "--patch-authorities"])
        self.assertEqual(rc, 0)
        after = self.fx.paths["authorities"].read_text(encoding="utf-8")
        self.assertEqual(before, after, "legacy --patch-authorities alias must not mutate the tracked file")
        self.assertTrue((self.fx.root / "output" / "approval-readiness" / "authorities.candidate.json").exists())


class RootParameterizationTest(unittest.TestCase):
    """policy_paths()/check functions must never fall back to REPO_ROOT when
    an explicit root is given (a real regression risk when refactoring from
    module-level path constants)."""

    def setUp(self):
        self.fx = ReadinessFixture()

    def tearDown(self):
        self.fx.close()

    def test_authorities_check_uses_given_root_not_repo_root(self):
        self.fx.paths["authorities"].unlink()
        result = mar.check_authorities(self.fx.root, [])
        self.assertEqual(result["status"], "BLOCKED")
        # If this had silently used REPO_ROOT, the real repo's populated
        # authorities.json would make this OK instead.


if __name__ == "__main__":
    unittest.main()
