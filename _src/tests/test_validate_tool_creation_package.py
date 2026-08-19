import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("tool_creation_validator", ROOT / "_src/tools/validate_tool_creation_package.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
MANIFEST = json.loads((ROOT / "docs/pipeline/evidence/0039-02/tool-creation-evidence.json").read_text())


class ToolCreationValidatorTests(unittest.TestCase):
    def codes(self, data):
        return {item["code"] for item in validator.validate(data, ROOT)}

    def test_current_manifest_passes(self):
        self.assertEqual([], validator.validate(MANIFEST, ROOT))

    def test_altered_study_digest_fails(self):
        data = copy.deepcopy(MANIFEST)
        data["reconciliation"]["study_sha256"] = "0" * 64
        self.assertIn("TCP-002", self.codes(data))

    def test_missing_control_fails(self):
        data = copy.deepcopy(MANIFEST)
        data["controls"].pop()
        self.assertIn("TCP-003", self.codes(data))

    def test_missing_pilot_shape_fails(self):
        data = copy.deepcopy(MANIFEST)
        data["pilots"][1]["shape"] = "new-capability"
        self.assertIn("TCP-004", self.codes(data))

    def test_deployment_decision_fails(self):
        data = copy.deepcopy(MANIFEST)
        data["pilots"][0]["decision"] = "deployed"
        self.assertIn("TCP-005", self.codes(data))

    def test_incomplete_reconciliation_fails(self):
        reconciliation = json.loads((ROOT / MANIFEST["reconciliation"]["path"]).read_text())
        reconciliation["recommendations"].pop()
        temporary = ROOT / "docs/pipeline/evidence/0039-02/.test-study-reconciliation.json"
        try:
            temporary.write_text(json.dumps(reconciliation))
            data = copy.deepcopy(MANIFEST)
            data["reconciliation"]["path"] = str(temporary.relative_to(ROOT))
            self.assertIn("TCP-002", self.codes(data))
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
