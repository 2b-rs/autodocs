"""Allowlist, leak, schema, determinism, reverse, and mutation tests for 0037-23.01."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_src" / "tools"))
from privacy_projector import (  # noqa: E402
    PrivacyProjectorError,
    project,
    reverse_check,
)

PUBLIC = {
    "id": "0099",
    "level": "feature",
    "state": "in_progress",
    "visibility": "public-summary",
    "title": "must not appear",
    "title_source_hash": "sha256:" + ("aa" * 32),
    "url": "/issues/0099/",
    "prerequisites": ["0098"],
}
INTERNAL = {
    "id": "0098",
    "level": "task",
    "state": "open",
    "visibility": "internal",
    "title": "SECRETLEAK private",
    "title_source_hash": "sha256:" + ("bb" * 32),
    "prerequisites": [],
}


def catalog(*items):
    return {"schema": "issue-catalog@v1", "items": list(items)}


class PrivacyProjectorTests(unittest.TestCase):
    def test_allowlist_omits_title_and_restricted(self):
        document, encoded = project(catalog(PUBLIC, INTERNAL))
        self.assertEqual(document["restricted_item_count"], 1)
        self.assertEqual([item["id"] for item in document["items"]], ["0099"])
        item = document["items"][0]
        self.assertEqual(item["title_key"], "issues.0099.title")
        self.assertNotIn("title", item)
        self.assertEqual(item["public_prerequisites"], [])
        self.assertNotIn("0098", encoded)
        self.assertNotIn("must not appear", encoded)
        reverse_check(document, catalog(PUBLIC, INTERNAL))

    def test_fail_unknown_visibility(self):
        bad = dict(PUBLIC, visibility="public-full")
        with self.assertRaises(PrivacyProjectorError):
            project(catalog(bad))

    def test_fail_missing_state(self):
        bad = dict(PUBLIC)
        del bad["state"]
        with self.assertRaises(PrivacyProjectorError):
            project(catalog(bad))

    def test_security_label_restricted(self):
        secret = dict(PUBLIC, id="0100", labels=["security"])
        document, encoded = project(catalog(secret, INTERNAL))
        self.assertEqual(document["restricted_item_count"], 2)
        self.assertEqual(document["items"], [])
        self.assertNotIn("0100", encoded)

    def test_dangling_unknown_prereq(self):
        dangling = dict(PUBLIC, prerequisites=["ghost"])
        with self.assertRaises(PrivacyProjectorError):
            project(catalog(dangling))

    def test_leak_token(self):
        leaky = dict(PUBLIC, url="/private/claim.json")
        with self.assertRaises(PrivacyProjectorError):
            project(catalog(leaky))

    def test_determinism(self):
        first, a = project(catalog(INTERNAL, PUBLIC))
        second, b = project(catalog(INTERNAL, PUBLIC))
        self.assertEqual(a, b)
        self.assertEqual(first, second)

    def test_drop_incident_edges(self):
        graph = {
            "edges": [
                {"source": "0099", "target": "0098", "kind": "prerequisite"},
                {"source": "0099", "target": "0099", "kind": "self"},
            ]
        }
        document, encoded = project(catalog(PUBLIC, INTERNAL), graph)
        self.assertEqual(document["edges"], [
            {"kind": "self", "source": "0099", "target": "0099"},
        ])
        self.assertNotIn("0098", encoded)

    def test_mutation_extra_item_key_fails_closed(self):
        document, _ = project(catalog(PUBLIC, INTERNAL))
        document["items"][0]["owner"] = "leaked"
        with self.assertRaises(PrivacyProjectorError):
            reverse_check(document, catalog(PUBLIC, INTERNAL))
        # extra keys on the emitted item are not in the allowlist contract
        self.assertNotIn("owner", project(catalog(PUBLIC, INTERNAL))[0]["items"][0])

    def test_cli_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps(catalog(PUBLIC, INTERNAL)), encoding="utf-8")
            dest_root = root / "repo"
            (dest_root / "_src" / "tools").mkdir(parents=True)
            (dest_root / "_src" / "tools" / "privacy_projector.py").write_bytes(
                (ROOT / "_src" / "tools" / "privacy_projector.py").read_bytes()
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "_src" / "tools" / "privacy_projector.py"),
                    "--repository-root", str(dest_root),
                    "--catalog-json", str(catalog_path),
                    "--write",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out = json.loads((dest_root / "_src" / "data" / "issue-graph-public.json").read_text())
            self.assertEqual(out["schema"], "issue-graph-public@v1")
            self.assertEqual(out["restricted_item_count"], 1)


if __name__ == "__main__":
    unittest.main()
