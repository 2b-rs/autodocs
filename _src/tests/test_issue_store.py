import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("issue_store", ROOT / "_src/tools/issue_store.py")
STORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STORE)
FIXTURES = ROOT / "_src/tests/fixtures/0037-08"


class IssueStoreTest(unittest.TestCase):
    maxDiff = None

    def test_path_identity_and_rejections(self):
        self.assertEqual(STORE.derive_identity("issues/0099/index.md"), ("0099", "feature", None))
        self.assertEqual(STORE.derive_identity("issues/0099/0099-01/index.md"), ("0099-01", "task", "0099"))
        self.assertEqual(STORE.derive_identity("issues/0099/0099-01.02/index.md"), ("0099-01.02", "subtask", "0099-01"))
        for invalid in ("issues/0099/0099-01/0099-01.02/index.md", "issues/_views/0099.md",
                        "issues/0099/other/index.md", "outside/0099/index.md"):
            with self.subTest(invalid=invalid), self.assertRaises(STORE.IssueStoreError):
                STORE.derive_identity(invalid)

    def test_yaml_profile_contract_fixtures(self):
        directory = ROOT / "issues/_schema/fixtures/yaml-profile"
        accepted = STORE.parse_frontmatter((directory / "accept-minimal-valid.yaml").read_text(), "accept")
        self.assertEqual(accepted["id"], "0099-01")
        for path in sorted(directory.glob("reject-*.yaml")):
            if path.name == "reject-control-character.yaml":
                continue
            with self.subTest(path=path.name), self.assertRaises(STORE.IssueStoreError):
                STORE.parse_frontmatter(path.read_text(), path)
        with self.assertRaisesRegex(STORE.IssueStoreError, "IS0808"):
            STORE._validate_bytes(b'id: "bad\x00value"\n', "control")

    def test_markdown_profile_valid_fixtures(self):
        directory = ROOT / "issues/_schema/fixtures/markdown-profile"
        for path in sorted(directory.glob("valid-*.md")):
            if path.name == "valid-migration-legacy-order.md":
                continue  # migration input, not an index.md body
            text = path.read_text()
            _, body, line = STORE._split_frontmatter(text, path)
            parsed = STORE.parse_markdown_body(body, body_start_line=line, path=path)
            self.assertTrue(parsed["criteria"], path.name)

    def test_markdown_profile_invalid_reused_and_order(self):
        directory = ROOT / "issues/_schema/fixtures/markdown-profile"
        for name in ("invalid-reused-ac-id.md", "invalid-wrong-section-order.md"):
            path = directory / name
            _, body, line = STORE._split_frontmatter(path.read_text(), path)
            with self.subTest(name=name), self.assertRaises(STORE.IssueStoreError):
                STORE.parse_markdown_body(body, body_start_line=line, path=path)
        renumbered = directory / "invalid-renumbered-ac-id.md"
        _, body, line = STORE._split_frontmatter(renumbered.read_text(), renumbered)
        with self.assertRaisesRegex(STORE.IssueStoreError, "IS0830"):
            STORE.parse_markdown_body(body, body_start_line=line, path=renumbered,
                                      prior_ids=["AC-001", "AC-002"])

    def test_full_item_and_golden_are_byte_stable(self):
        path = FIXTURES / "issues/0099/0099-01/index.md"
        first = STORE.parse_issue(path, issues_root=FIXTURES / "issues", repository_root=ROOT)
        second = STORE.parse_issue(path, issues_root=FIXTURES / "issues", repository_root=ROOT)
        encoded = STORE._canonical_json(first)
        self.assertEqual(encoded, STORE._canonical_json(second))
        self.assertEqual(first["criteria"][0]["id"], "AC-001")
        self.assertEqual(first["criteria"][1]["status"], "withdrawn")
        self.assertIn("Καλημέρα", first["sections"]["Goal"]["text"])
        golden = (FIXTURES / "golden-item.json").read_text()
        self.assertEqual(encoded, golden)

    def test_discovery_only_returns_canonical_items(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "issues"
            target = root / "0099/0099-01/index.md"
            target.parent.mkdir(parents=True)
            shutil.copyfile(FIXTURES / "issues/0099/0099-01/index.md", target)
            hidden = root / "_views/index.md"
            hidden.parent.mkdir(parents=True)
            hidden.write_text("generated\n")
            self.assertEqual(STORE.discover(root), [target])

    def test_path_metadata_drift_and_unknown_fields_fail(self):
        source = (FIXTURES / "issues/0099/0099-01/index.md").read_text()
        mutations = {
            "wrong id": source.replace('id: "0099-01"', 'id: "0099-02"'),
            "wrong parent": source.replace('parent: "0099"', 'parent: "0098"'),
            "unknown schema": source.replace('schema_version: "1.0"', 'schema_version: "2.0"'),
            "unknown field": source.replace('state: "open"', 'state: "open"\nsurprise: true'),
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "issues"
            path = root / "0099/0099-01/index.md"
            path.parent.mkdir(parents=True)
            for name, content in mutations.items():
                path.write_text(content)
                with self.subTest(name=name), self.assertRaises(STORE.IssueStoreError):
                    STORE.parse_issue(path, issues_root=root, repository_root=ROOT)

    def test_resource_limits_and_malformed_input_fail(self):
        with self.assertRaisesRegex(STORE.IssueStoreError, "IS0804"):
            STORE._validate_bytes(b"x" * (STORE.MAX_DOCUMENT_BYTES + 1), "large")
        with self.assertRaisesRegex(STORE.IssueStoreError, "IS0817"):
            STORE.parse_frontmatter("root:\n" + "".join("  " * n + f"k{n}:\n" for n in range(22)) + "  " * 22 + "value: x\n")
        with self.assertRaisesRegex(STORE.IssueStoreError, "IS0809"):
            STORE._split_frontmatter("not-frontmatter\n", "bad")
        decomposed = "## Goal\n\nX\n\n## Scope\n\nX\n\n## Acceptance criteria\n\n- **AC-001** cafe\u0301\n\n## Definition of Done\n\nX\n"
        with self.assertRaisesRegex(STORE.IssueStoreError, "IS0848"):
            STORE.parse_markdown_body(decomposed)

    def test_fixed_seed_property_ordering_and_unicode(self):
        randomizer = random.Random(803708)
        fields = [("schema_version", "1.0"), ("id", "0099-01"), ("level", "task"),
                  ("parent", "0099"), ("state", "open"), ("visibility", "internal")]
        outputs = []
        for _ in range(32):
            randomizer.shuffle(fields)
            source = "\n".join(f'{key}: "{value}"' for key, value in fields) + "\n"
            parsed = STORE.parse_frontmatter(source)
            outputs.append(STORE._canonical_json(parsed))
        self.assertEqual(len(set(outputs)), 1)
        self.assertEqual(STORE._canonical_json({"text": "café"}), '{"text":"café"}\n')

    def test_fixed_seed_fuzz_malformed_frontmatter(self):
        randomizer = random.Random(8037081)
        alphabet = "{}[]:&*!~\x00\r\n"
        rejected = 0
        for _ in range(64):
            source = "".join(randomizer.choice(alphabet) for _ in range(40))
            try:
                STORE.parse_frontmatter(source)
            except STORE.IssueStoreError:
                rejected += 1
        self.assertGreaterEqual(rejected, 60)


if __name__ == "__main__":
    unittest.main()
