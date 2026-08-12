import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("spec_scrape", TOOLS / "spec_scrape.py")
scrape = importlib.util.module_from_spec(spec); spec.loader.exec_module(scrape)

class MixedCaseIdTests(unittest.TestCase):
    def test_mixed_case_rs_ids_are_canonicalized(self):
        text = "[RS_Diag_04260] Read / Write Access ⌈\nDescription: Canonical text\n⌋"
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            pdf = Path(td) / "mixed.pdf"; pdf.write_bytes(b"placeholder")
            with mock.patch.object(scrape, "pdf_pages", return_value=[text]):
                index = scrape.phase_ids([pdf], pattern=r"^RS_DIAG_", include_refs=False)
            self.assertEqual(index["mixed.pdf"]["ids"], {"RS_DIAG_04260": [1]})
            rec = scrape.parse_record(text, "RS_DIAG_04260")
            self.assertEqual(rec["heading"], "Read / Write Access")
            self.assertEqual(rec["props"]["Description"], "Canonical text")

class DefinitionPrecisionTests(unittest.TestCase):
    def test_history_table_entry_is_rejected_with_evidence(self):
        text = """A.8.3 Deleted Requirements in 19-03
Number Heading
[RS_SM_00201] State Management shall provide the interface over ara::com.
Table A.14: Deleted Requirements in 19-03
"""
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            pdf = Path(td) / "history.pdf"; pdf.write_bytes(b"placeholder")
            with mock.patch.object(scrape, "pdf_pages", return_value=[text]):
                index = scrape.phase_ids([pdf], pattern=r"^RS_", include_refs=False)
            doc = index["history.pdf"]
            self.assertNotIn("RS_SM_00201", doc["ids"])
            self.assertEqual(doc["history_only_ids"], ["RS_SM_00201"])
            self.assertEqual(doc["history_only_evidence"]["RS_SM_00201"][0]["page"], 1)

    def test_dense_definition_list_survives_history_on_same_page(self):
        text = """Body requirements
[RS_PHM_00001] PHM shall provide service headers.
[RS_PHM_00002] PHM shall define the namespace.
A.2 Deleted Requirements in R24-11
Number Heading
[RS_PHM_09999] Obsolete requirement.
Table A.2: Deleted Requirements in R24-11
"""
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            pdf = Path(td) / "mixed.pdf"; pdf.write_bytes(b"placeholder")
            with mock.patch.object(scrape, "pdf_pages", return_value=[text]):
                index = scrape.phase_ids([pdf], pattern=r"^RS_", include_refs=False)
            doc = index["mixed.pdf"]
            self.assertEqual(set(doc["ids"]), {"RS_PHM_00001", "RS_PHM_00002"})
            self.assertEqual(doc["history_only_ids"], ["RS_PHM_09999"])

    def test_include_refs_keeps_history_entries(self):
        text = "A.1 Deleted Requirements in 19-03\n[RS_X_00001] Old\nTable A.1: Deleted Requirements in 19-03"
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            pdf = Path(td) / "refs.pdf"; pdf.write_bytes(b"placeholder")
            with mock.patch.object(scrape, "pdf_pages", return_value=[text]):
                index = scrape.phase_ids([pdf], pattern=r"^RS_", include_refs=True)
            self.assertIn("RS_X_00001", index["refs.pdf"]["ids"])
            self.assertEqual(index["refs.pdf"]["history_only_ids"], [])


class PageStructureTests(unittest.TestCase):
    def test_history_toc_and_bibliography_are_labelled(self):
        text = ("Introduction .......... 4\n"
                "A.1 Deleted Requirements in 19-03\n"
                "[RS_X_00001] Old requirement.\n"
                "Table A.1: Deleted Requirements in 19-03\n"
                "Bibliography\n")
        kinds = scrape.classify_page_structure(text)["kinds"]
        self.assertEqual(kinds, ["bibliography", "history", "toc"])

    def test_body_only_page_has_no_regions(self):
        text = "[RS_Y_00001] A real requirement that opens a spec item.\n"
        value = scrape.classify_page_structure(text)
        self.assertEqual(value["regions"], [])
        self.assertEqual(value["kinds"], [])

    def test_non_body_spans_can_be_filtered_by_kind(self):
        text = "Scope .......... 7\nA.1 Deleted Requirements in 19-03\nTable A.1: Deleted Requirements in 19-03\n"
        self.assertEqual(len(scrape.non_body_spans(text, kinds=["toc"])), 1)
        self.assertEqual(len(scrape.non_body_spans(text, kinds=["history"])), 1)
        self.assertEqual(len(scrape.non_body_spans(text)), 2)


class UpstreamCliIntegrationTests(unittest.TestCase):
    def fixtures(self, root):
        records=root/"SWS_X"; records.mkdir(parents=True)
        value={"id":"SWS_X_00001","blocks":[{"text":"Uses RS_CM_00003"}],"review":{"status":"manual"},"text_hash":"abc","upstream":[]}
        path=records/"SWS_X_00001.json"; path.write_text(json.dumps(value,indent=1)+"\n",encoding="utf-8")
        source={"id":"RS_CM_00003","document":"AUTOSAR_AP_RS_CommunicationManagement.pdf","page":12}
        return path,value,source
    def test_compare_does_not_write(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            path,value,source=self.fixtures(Path(td)); before=path.read_bytes()
            with mock.patch.object(scrape,"RECORDS",Path(td)):
                report=scrape.phase_upstream({source["id"]:source},rebuild=False)
            self.assertEqual(before,path.read_bytes()); self.assertEqual(report["updated"],1); self.assertEqual(report["mode"],"compare")
    def test_rebuild_changes_only_upstream_and_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            path,value,source=self.fixtures(Path(td))
            with mock.patch.object(scrape,"RECORDS",Path(td)):
                first=scrape.phase_upstream({source["id"]:source},rebuild=True); once=path.read_bytes()
                second=scrape.phase_upstream({source["id"]:source},rebuild=True)
            after=json.loads(once); expected=copy.deepcopy(value); expected["upstream"]=[{"id":"RS_CM_00003","document":source["document"],"page":12,"source":"inline"}]
            self.assertEqual(after,expected); self.assertEqual(first["updated"],1); self.assertEqual(second["unchanged"],1); self.assertEqual(once,path.read_bytes())
    def test_missing_is_visible(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            path,value,source=self.fixtures(Path(td))
            with mock.patch.object(scrape,"RECORDS",Path(td)):
                report=scrape.phase_upstream({},rebuild=False)
            self.assertEqual(report["missing"],1); self.assertEqual(path.read_text(encoding="utf-8"),json.dumps(value,indent=1)+"\n")

if __name__ == "__main__": unittest.main()
