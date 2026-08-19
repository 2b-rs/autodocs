import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("feature_definition_validator", ROOT / "_src/tools/validate_feature_definition_package.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
MANIFEST = json.loads((ROOT / "docs/pipeline/evidence/0039-01/feature-definition-evidence.json").read_text())


class FeatureDefinitionValidatorTests(unittest.TestCase):
    def test_current_manifest_passes(self):
        self.assertEqual([], validator.validate(MANIFEST, ROOT))

    def test_cycle_fails(self):
        data = copy.deepcopy(MANIFEST)
        data["prerequisites"].append({"consumer": "0039-04", "producer": "0039-01", "type": "producer"})
        self.assertIn("FDB-004", {item["code"] for item in validator.validate(data, ROOT)})

    def test_unresolved_coverage_fails(self):
        data = copy.deepcopy(MANIFEST)
        data["criteria"][0]["verified_by"] = ["E-999"]
        self.assertIn("FDB-002", {item["code"] for item in validator.validate(data, ROOT)})

    def test_missing_evidence_path_fails(self):
        data = copy.deepcopy(MANIFEST)
        data["evidence"][0]["path"] = "missing.md"
        self.assertIn("FDB-003", {item["code"] for item in validator.validate(data, ROOT)})


if __name__ == "__main__":
    unittest.main()
