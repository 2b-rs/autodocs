import copy
import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "score_campaign_manifest"
sys.path.insert(0, str(TOOLS_DIR))
import score_source_snapshot as snapshot  # noqa: E402


class ScoreSourceSnapshotTests(unittest.TestCase):
    def fixture(self, name):
        return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))

    def write_archive(self, path, files):
        path.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(path, "w") as archive:
            for name, content in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(content)
                member.mtime = 0
                archive.addfile(member, io.BytesIO(content))

    def test_offline_inventory_reconstructs_selected_artifacts_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bom = copy.deepcopy(self.fixture("valid-complete.json"))
            source = bom["sources"][0]
            snapshot_root = "retained/example"
            source["snapshot_archive"] = f"{snapshot_root}/archives/communication.tar"
            bom["snapshot"]["root"] = snapshot_root
            bom["snapshot"]["inventory"] = f"{snapshot_root}/inventory.json"
            archive_path = root / source["snapshot_archive"]
            self.write_archive(
                archive_path,
                {
                    "LICENSE": b"Apache-2.0\n",
                    "docs/a.rst": b"source a\n",
                    "docs/nested/b.rst": b"source b\n",
                    "unselected.txt": b"not selected\n",
                },
            )
            source["archive"]["sha256"] = snapshot.sha256_file(archive_path)
            bom["snapshot"]["inventory_sha256"] = "0" * 64

            inventory_path, digest, artifact_count = snapshot.write_inventory(bom, root)
            bom["snapshot"]["inventory_sha256"] = digest

            self.assertEqual(artifact_count, 2)
            self.assertEqual(snapshot.verify_snapshot(bom, root), (digest, 2))
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            artifacts = inventory["sources"][0]["artifacts"]
            self.assertEqual([artifact["path"] for artifact in artifacts], ["docs/a.rst", "docs/nested/b.rst"])
            self.assertEqual(artifacts[0]["repository"], "communication")
            self.assertEqual(artifacts[0]["release_ref"], "v0.6.0")
            self.assertEqual(artifacts[0]["resolved_commit"], source["resolved_commit"])
            self.assertEqual(
                artifacts[0]["locator"],
                "https://github.com/eclipse-score/communication/blob/"
                "0123456789abcdef0123456789abcdef01234567/docs/a.rst",
            )
            self.assertEqual(artifacts[0]["sha256"], hashlib.sha256(b"source a\n").hexdigest())

            archive_path.write_bytes(b"tampered")
            with self.assertRaisesRegex(snapshot.SnapshotError, "has SHA-256"):
                snapshot.verify_snapshot(bom, root)


if __name__ == "__main__":
    unittest.main()
