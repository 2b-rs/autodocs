#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_classic_api_scrape.py — Unit-Tests für den AUTOSAR Classic API-Parser."""

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
TOOLS = SRC / "tools"
sys.path.insert(0, str(TOOLS))

import classic_api_scrape as cas


class TestClassicApiScrape(unittest.TestCase):

    def test_clean_ident_basic(self):
        self.assertEqual(cas.clean_ident("CanIf_Init"), "CanIf_Init")
        self.assertEqual(cas.clean_ident("Det_ \n Report \n Error"), "Det_ReportError")
        self.assertEqual(cas.clean_ident("<User_TxConfirmation>"), "<User_TxConfirmation>")

    def test_clean_ident_strips_footers_and_footnotes(self):
        bad_name = "CanIf_SetTrcvWakeupMode5\n91 of 215 Document ID 12: AUTOSAR_SWS_CANInterface"
        self.assertEqual(cas.clean_ident(bad_name), "CanIf_SetTrcvWakeupMode")

    def test_clean_type_name(self):
        # Basic clean type names
        self.assertEqual(cas.clean_type_name("Dem_ConfigType"), "Dem_ConfigType")
        self.assertEqual(cas.clean_type_name("Dem_DTCKindType"), "Dem_DTCKindType")
        self.assertEqual(cas.clean_type_name("Dem_EventIdType"), "Dem_EventIdType")
        self.assertEqual(cas.clean_type_name("Can_IdType"), "Can_IdType")

        # Cutting off table keywords concatenated with type names
        self.assertEqual(cas.clean_type_name("Can_ConfigTypeKindStructure"), "Can_ConfigType")
        self.assertEqual(cas.clean_type_name("Can_PduTypeKindStructureElementsswPduHandleType"), "Can_PduType")
        self.assertEqual(cas.clean_type_name("Can_IdTypeKindTypeDerivedfromuint32"), "Can_IdType")
        self.assertEqual(cas.clean_type_name("Dem_DTCKindTypeKindTypeDerivedfromuint8"), "Dem_DTCKindType")

        # Multi-line cell with table keywords
        multiline = "Dem_ConfigType\nKind\nStructure\nElements\nComment\nDescription"
        self.assertEqual(cas.clean_type_name(multiline), "Dem_ConfigType")

        # Types not ending in Type
        self.assertEqual(cas.clean_type_name("DETServiceCommentServiceofDefaultErrorTracer"), "DETService")

    def test_clean_syntax(self):
        raw = "void  CanIf_Init \n ( \n const CanIf_ConfigType * ConfigPtr \n )"
        cleaned = cas.clean_syntax(raw)
        self.assertEqual(cleaned, "void CanIf_Init(const CanIf_ConfigType* ConfigPtr);")

    def test_format_function_blocks(self):
        sample = {
            "id": "SWS_CANIF_00001",
            "name": "CanIf_Init",
            "kind": "function",
            "syntax": "void CanIf_Init(const CanIf_ConfigType* ConfigPtr);",
            "desc": "This service initializes internal and external interfaces.",
        }
        blocks = cas.format_function_blocks(sample)
        self.assertEqual(len(blocks), 3)
        self.assertIn("CanIf_Init", blocks[0]["html"])
        self.assertIn("SWS_CANIF_00001", blocks[0]["html"])
        self.assertIn('<span class="kind">function</span>', blocks[0]["html"])
        self.assertIn('<pre class="syntax">void CanIf_Init', blocks[1]["html"])
        self.assertIn("This service initializes", blocks[2]["html"])

    def test_format_type_blocks(self):
        sample = {
            "id": "SWS_DEM_00924",
            "name": "Dem_ConfigType",
            "kind": "type",
            "syntax": "",
            "desc": "Configuration data structure for Dem.",
        }
        blocks = cas.format_function_blocks(sample)
        self.assertEqual(len(blocks), 2, "Types must render without syntax block (exactly 2 blocks: header and desc)")
        self.assertIn("Dem_ConfigType", blocks[0]["html"])
        self.assertIn("SWS_DEM_00924", blocks[0]["html"])
        self.assertIn('<span class="kind">type</span>', blocks[0]["html"])
        # Ensure no syntax block was rendered
        all_html = " ".join(b["html"] for b in blocks)
        self.assertNotIn("class=\"syntax\"", all_html)
        self.assertNotIn("<pre", all_html)
        self.assertIn("Configuration data structure for Dem.", blocks[1]["html"])

    def test_extract_functions_from_det(self):
        pdf = cas.DEFAULT_CACHE_DIR / "AUTOSAR_SWS_DefaultErrorTracer.pdf"
        if not pdf.is_file():
            self.skipTest(f"{pdf} not in cache")

        items = cas.extract_functions_from_pdf(pdf)
        funcs = [it for it in items if it.get("kind") == "function"]
        types = [it for it in items if it.get("kind") == "type"]

        func_names = {f["name"] for f in funcs}
        self.assertTrue(len(funcs) >= 5, f"Expected at least 5 functions, got {len(funcs)}")
        self.assertIn("Det_Init", func_names)
        self.assertIn("Det_ReportError", func_names)
        self.assertIn("Det_Start", func_names)
        self.assertIn("Det_ReportRuntimeError", func_names)

        # Check that functions have real C syntax with parentheses
        for f in funcs:
            self.assertEqual(f["kind"], "function")
            self.assertIn("(", f["syntax"])
            self.assertIn(")", f["syntax"])
            self.assertFalse(f["syntax"].startswith("void ()"))

        # Check types
        type_names = {t["name"] for t in types}
        self.assertIn("Det_ConfigType", type_names)
        for t in types:
            self.assertEqual(t["kind"], "type")
            self.assertEqual(t["syntax"], "", "Types must have empty syntax (no fake syntax)")

    def test_extract_functions_from_canif(self):
        pdf = cas.DEFAULT_CACHE_DIR / "AUTOSAR_SWS_CANInterface.pdf"
        if not pdf.is_file():
            self.skipTest(f"{pdf} not in cache")

        items = cas.extract_functions_from_pdf(pdf)
        funcs = [it for it in items if it.get("kind") == "function"]
        types = [it for it in items if it.get("kind") == "type"]

        func_names = {f["name"] for f in funcs}
        type_names = {t["name"] for t in types}

        self.assertTrue(len(funcs) >= 30, f"Expected at least 30 functions, got {len(funcs)}")
        self.assertIn("CanIf_Init", func_names)
        self.assertIn("CanIf_Transmit", func_names)
        self.assertIn("CanIf_RxIndication", func_names)
        self.assertIn("CanIf_SetControllerMode", func_names)

        # Verify clean type extraction
        self.assertIn("CanIf_ConfigType", type_names)
        self.assertIn("CanIf_PduModeType", type_names)
        self.assertIn("CanIf_NotifStatusType", type_names)

        # Verify garbage requirement items are not parsed as functions or types
        all_names = {it["name"] for it in items}
        self.assertNotIn("mustbePduR_CanIfTxConfirmationc", all_names)

        for t in types:
            self.assertEqual(t["kind"], "type")
            self.assertEqual(t["syntax"], "")

    def test_extract_functions_and_types_from_dem(self):
        pdf = cas.DEFAULT_CACHE_DIR / "AUTOSAR_SWS_DiagnosticEventManager.pdf"
        if not pdf.is_file():
            self.skipTest(f"{pdf} not in cache")

        items = cas.extract_functions_from_pdf(pdf)
        funcs = [it for it in items if it.get("kind") == "function"]
        types = [it for it in items if it.get("kind") == "type"]

        func_names = {f["name"] for f in funcs}
        type_names = {t["name"] for t in types}

        # Check key functions
        self.assertIn("Dem_ClearDTC", func_names)
        self.assertIn("Dem_GetVersionInfo", func_names)
        self.assertIn("Dem_Init", func_names)
        self.assertIn("Dem_Shutdown", func_names)

        # Check key types specified in requirements
        self.assertIn("Dem_ConfigType", type_names)
        self.assertIn("Dem_DTCKindType", type_names)
        self.assertIn("Dem_EventIdType", type_names)
        self.assertIn("Dem_ComponentIdType", type_names)

        # Ensure types have kind 'type' and empty syntax (no fake void Dem_ConfigType();)
        for t in types:
            self.assertEqual(t["kind"], "type")
            self.assertEqual(t["syntax"], "")
            self.assertNotEqual(t["name"], "Dem_DTC", "Dem_DTCKindType should not be truncated to Dem_DTC")

    def test_cluster_map_new_clusters(self):
        for ckey, expected_rec in [("LIN", "CP_LIN.json"), ("FR", "CP_FR.json"), ("SEC", "CP_SEC.json"), ("MEM", "CP_MEM.json")]:
            self.assertIn(ckey, cas.CLUSTER_MAP)
            meta = cas.CLUSTER_MAP[ckey]
            self.assertEqual(meta["record"], expected_rec)
            for mkey, minfo in meta["modules"].items():
                pdf_path = cas.DEFAULT_CACHE_DIR / minfo["pdf"]
                self.assertTrue(pdf_path.is_file(), f"PDF {minfo['pdf']} for {mkey} not found")

    def test_extract_functions_from_lin(self):
        pdf = cas.DEFAULT_CACHE_DIR / "AUTOSAR_SWS_LINDriver.pdf"
        if not pdf.is_file():
            self.skipTest(f"{pdf} not in cache")
        items = cas.extract_functions_from_pdf(pdf)
        func_names = {it["name"] for it in items if it.get("kind") == "function"}
        type_names = {it["name"] for it in items if it.get("kind") == "type"}
        self.assertIn("Lin_Init", func_names)
        self.assertIn("Lin_ConfigType", type_names)

    def test_extract_functions_from_flexray(self):
        pdf = cas.DEFAULT_CACHE_DIR / "AUTOSAR_SWS_FlexRayDriver.pdf"
        if not pdf.is_file():
            self.skipTest(f"{pdf} not in cache")
        items = cas.extract_functions_from_pdf(pdf)
        func_names = {it["name"] for it in items if it.get("kind") == "function"}
        type_names = {it["name"] for it in items if it.get("kind") == "type"}
        self.assertIn("Fr_Init", func_names)
        self.assertIn("Fr_ConfigType", type_names)

    def test_extract_functions_from_security(self):
        pdf = cas.DEFAULT_CACHE_DIR / "AUTOSAR_SWS_SecureOnboardCommunication.pdf"
        if not pdf.is_file():
            self.skipTest(f"{pdf} not in cache")
        items = cas.extract_functions_from_pdf(pdf)
        func_names = {it["name"] for it in items if it.get("kind") == "function"}
        type_names = {it["name"] for it in items if it.get("kind") == "type"}
        self.assertIn("SecOC_Init", func_names)
        self.assertIn("SecOC_ConfigType", type_names)

    def test_extract_functions_from_memory(self):
        pdf = cas.DEFAULT_CACHE_DIR / "AUTOSAR_SWS_MemoryAbstractionInterface.pdf"
        if not pdf.is_file():
            self.skipTest(f"{pdf} not in cache")
        items = cas.extract_functions_from_pdf(pdf)
        func_names = {it["name"] for it in items if it.get("kind") == "function"}
        type_names = {it["name"] for it in items if it.get("kind") == "type"}
        self.assertIn("MemIf_SetMode", func_names)
        self.assertIn("MemIf_Read", func_names)
        self.assertIn("MemIf_ModeType", type_names)

    # -----------------------------------------------------------------------
    # Requirement 3: Type Registry & Syntax Hyperlinking Tests
    # -----------------------------------------------------------------------

    def test_type_registry_standard_types(self):
        """Verify that all standard platform and infrastructure types are registered with SWS IDs."""
        expected_platform_types = [
            "Std_ReturnType", "Std_VersionInfoType", "uint8", "uint16", "uint32", "uint64",
            "sint8", "sint16", "sint32", "sint64", "boolean", "float32", "float64",
            "PduIdType", "PduLengthType", "PduInfoType", "NetworkHandleType",
            "TickType", "StatusType", "TaskType", "EventMaskType", "AlarmType", "ScheduleTableType"
        ]
        for tname in expected_platform_types:
            entry = cas.get_type(tname)
            self.assertIsNotNone(entry, f"Standard type {tname} must be in CLASSIC_TYPE_REGISTRY")
            self.assertTrue(entry.sws_id.startswith("SWS_"), f"Type {tname} must have a valid SWS ID, got {entry.sws_id}")
            self.assertTrue(bool(entry.url), f"Type {tname} must have an associated URL")

    def test_type_registry_bsw_module_types(self):
        """Verify that Chapter 8.2 BSW module types are registered with correct module and anchor."""
        test_cases = [
            ("Dem_EventIdType", "Dem", "SWS_Dem_00925"),
            ("Dem_ConfigType", "Dem", "SWS_Dem_00924"),
            ("Dem_DTCKindType", "Dem", "SWS_Dem_00932"),
            ("Can_PduType", "Can", "SWS_Can_00415"),
            ("Can_ConfigType", "Can", "SWS_Can_00413"),
            ("CanIf_PduModeType", "CanIf", "SWS_CANIF_00137"),
            ("CanIf_ConfigType", "CanIf", "SWS_CANIF_00144"),
            ("Eth_ModeType", "Eth", "SWS_Eth_91008"),
        ]
        for tname, expected_mod, expected_sws in test_cases:
            entry = cas.get_type(tname)
            self.assertIsNotNone(entry, f"BSW type {tname} must be registered")
            self.assertEqual(entry.module.lower(), expected_mod.lower(), f"Module mismatch for {tname}")
            self.assertEqual(entry.sws_id, expected_sws, f"SWS ID mismatch for {tname}")

    def test_link_syntax_types_standard_signature(self):
        """Test linking in 'Std_ReturnType Dem_ClearDTC(uint8 ClientId);'."""
        sig = "Std_ReturnType Dem_ClearDTC(uint8 ClientId);"
        linked = cas.link_syntax_types(sig, current_module="Dem")

        # Std_ReturnType must be linked as a standard type pointing to local std.html
        self.assertIn('<a class="vis-app"', linked)
        self.assertIn('>Std_ReturnType</a>', linked)
        self.assertIn("std.html#SWS_Std_00005", linked)

        # uint8 must be linked as a platform type pointing to local platform.html
        self.assertIn('>uint8</a>', linked)
        self.assertIn("platform.html#SWS_Platform_00013", linked)

        # Function name and parameter name must NOT be linked
        self.assertNotIn('>Dem_ClearDTC</a>', linked)
        self.assertIn("Dem_ClearDTC(", linked)
        self.assertNotIn('>ClientId</a>', linked)
        self.assertIn("ClientId);", linked)

    def test_link_syntax_types_same_module(self):
        """Test linking same-module types in 'void CanIf_Init(const CanIf_ConfigType* ConfigPtr);'."""
        sig = "void CanIf_Init(const CanIf_ConfigType* ConfigPtr);"
        linked = cas.link_syntax_types(sig, current_module="CanIf")

        # CanIf_ConfigType must link to local anchor #{sws_id}
        self.assertIn('<a class="vis-app" href="#SWS_CANIF_00144">CanIf_ConfigType</a>', linked)

        # void, const, pointers, and parameter names must not be hyperlinked
        self.assertTrue(linked.startswith("void CanIf_Init("))
        self.assertIn("const <a", linked)
        self.assertIn("</a>* ConfigPtr);", linked)
        self.assertNotIn('>CanIf_Init</a>', linked)
        self.assertNotIn('>ConfigPtr</a>', linked)

    def test_link_syntax_types_other_module(self):
        """Test linking cross-module types with module_url#sws_id."""
        sig = "void CanIf_Init(const CanIf_ConfigType* ConfigPtr);"
        linked = cas.link_syntax_types(sig, current_module="Dem")

        # CanIf_ConfigType referenced from Dem must link to canif.html#SWS_CANIF_00144
        self.assertIn('<a class="vis-app" href="canif.html#SWS_CANIF_00144">CanIf_ConfigType</a>', linked)

    def test_link_syntax_types_inferred_module(self):
        """Test module inference from function name prefix when current_module is omitted."""
        sig = "void CanIf_Init(const CanIf_ConfigType* ConfigPtr);"
        linked = cas.link_syntax_types(sig)
        # Should infer CanIf from CanIf_Init and treat CanIf_ConfigType as same-module
        self.assertIn('<a class="vis-app" href="#SWS_CANIF_00144">CanIf_ConfigType</a>', linked)

    def test_link_syntax_types_multiple_parameters(self):
        """Test multi-parameter signature with mixed platform and BSW types."""
        sig = "Std_ReturnType Can_Write(Can_HwHandleType Hth, const Can_PduType* PduInfo);"
        linked = cas.link_syntax_types(sig, current_module="Can")

        self.assertIn('>Std_ReturnType</a>', linked)
        self.assertIn('<a class="vis-app" href="#SWS_Can_00429">Can_HwHandleType</a>', linked)
        self.assertIn('<a class="vis-app" href="#SWS_Can_00415">Can_PduType</a>', linked)
        self.assertNotIn('>Hth</a>', linked)
        self.assertNotIn('>PduInfo</a>', linked)
        self.assertNotIn('>Can_Write</a>', linked)

    def test_link_syntax_types_normalizes_split_names(self):
        """Test that split tokens from PDF kerning like 'Can_Config Type' or 'Std_Return Type' are linked."""
        sig = "Std_Return Type Can_Init(const Can_Config Type* Config);"
        linked = cas.link_syntax_types(sig, current_module="Can")
        self.assertIn('>Std_ReturnType</a>', linked)
        self.assertIn('>Can_ConfigType</a>', linked)

    def test_format_function_blocks_links_syntax_and_anchors(self):
        """Test that format_function_blocks produces <pre class="syntax"> with type links and <h3 id="...">."""
        sample = {
            "id": "SWS_CANIF_00001",
            "name": "CanIf_Init",
            "kind": "function",
            "syntax": "void CanIf_Init(const CanIf_ConfigType* ConfigPtr);",
            "desc": "This service initializes internal and external interfaces.",
        }
        blocks = cas.format_function_blocks(sample, current_module="CanIf")
        self.assertEqual(len(blocks), 3)

        # Heading must include id anchor
        self.assertIn('id="SWS_CANIF_00001"', blocks[0]["html"])

        # Syntax block must have type link
        syntax_html = blocks[1]["html"]
        self.assertIn('<pre class="syntax">', syntax_html)
        self.assertIn('<a class="vis-app" href="#SWS_CANIF_00144">CanIf_ConfigType</a>', syntax_html)

    def test_link_parameter_table_and_blocks(self):
        """Test that parameter tables and table cells link embedded types."""
        sample = {
            "id": "SWS_CANIF_00001",
            "name": "CanIf_Init",
            "kind": "function",
            "syntax": "void CanIf_Init(const CanIf_ConfigType* ConfigPtr);",
            "desc": "Init.",
            "params_in": "ConfigPtr Pointer to configuration parameter set of type CanIf_ConfigType",
            "return_value": "Std_ReturnType E_OK / E_NOT_OK",
        }
        pblocks = cas.format_parameter_blocks(sample, current_module="CanIf")
        self.assertTrue(len(pblocks) >= 2)

        all_html = " ".join(b["html"] for b in pblocks)
        self.assertIn('<a class="vis-app" href="#SWS_CANIF_00144">CanIf_ConfigType</a>', all_html)
        self.assertIn("std.html#SWS_Std_00005", all_html)

        # Standalone table linking
        td_html = '<td class="mono">const CanIf_ConfigType* ConfigPtr</td>'
        linked_td = cas.link_parameter_table(td_html, current_module="CanIf")
        self.assertIn('<a class="vis-app" href="#SWS_CANIF_00144">CanIf_ConfigType</a>', linked_td)


if __name__ == "__main__":
    unittest.main()


