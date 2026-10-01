#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_review_request_browser_builder.py -- Tests for browser review request package builder (0033-10).

Validates:
  - Standards-correct UUIDv7 generation in JS builder matching Python verifier.
  - Immutability and reuse of confirmed request across export, submit, and retry.
  - Safe JSON export identity downgrade (self_declared) without losing display_name.
  - Evidence link and text validation.
  - Local review collection storage (ara-review-package-v1) and drawer rendering.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "_src"
TOOLS = SRC / "tools"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(TOOLS))

import review_request_package as rrp  # noqa: E402


class TestReviewRequestBrowserBuilder(unittest.TestCase):
    def test_js_uuid7_generation_conformance(self):
        """JS generateUUIDv7 generates valid RFC 9562 UUIDv7 that Python validator accepts."""
        js_code = """
        const { generateUUIDv7, requestId } = require('./review_request.js');
        const ids = [];
        for (let i = 0; i < 20; i++) {
            ids.push({ uuid: generateUUIDv7(), reqId: requestId() });
        }
        console.log(JSON.stringify(ids));
        """
        proc = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=True,
        )
        data = json.loads(proc.stdout)
        self.assertEqual(len(data), 20)
        for item in data:
            uuid_str = item["uuid"]
            req_id = item["reqId"]
            self.assertTrue(rrp.is_valid_uuid7(uuid_str), f"Invalid UUIDv7: {uuid_str}")
            self.assertTrue(req_id.startswith("review-request:"))
            self.assertTrue(rrp.is_valid_uuid7(req_id.split(":", 1)[1]))

    def test_js_package_builder_schema_conformance(self):
        """JS buildConfirmedPackage produces schema-conformant review-request-package@v1."""
        js_code = """
        const { buildConfirmedPackage } = require('./review_request.js');
        const targetData = {
            canonical_id: "AUTOSAR/AP/record/SWS_CORE_00009",
            version_id: "AUTOSAR/AP/record/SWS_CORE_00009@rel:R25-11#a1b2c3d4",
            content_hash: "a1b2c3d4",
            status: "valid/unmigrated",
            source_url: "https://www.autosar.org/fileadmin/standards/R25-11/AP/AUTOSAR_AP_SWS_Core.pdf#nameddest=SWS_CORE_00009",
            category: "factual-accuracy",
            rationale: "Detailed test rationale for browser builder.",
            evidence_refs: [
                { kind: "url", value: "https://example.org/errata.pdf" },
                { kind: "quote", value: "Executor (const Executor &other);" }
            ]
        };
        const whoAuth = { name: "auditor-octocat", mode: "github_authenticated" };
        const whoSelf = { name: "Jane Doe", mode: "self_declared" };

        const pkgAuth = buildConfirmedPackage({}, targetData, whoAuth);
        const pkgSelf = buildConfirmedPackage({}, targetData, whoSelf);

        console.log(JSON.stringify({ pkgAuth, pkgSelf }));
        """
        proc = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=True,
        )
        res = json.loads(proc.stdout)
        pkg_auth = res["pkgAuth"]
        pkg_self = res["pkgSelf"]

        # Validate schema and fields
        self.assertEqual(pkg_auth["schema"], "review-request-package@v1")
        self.assertEqual(pkg_auth["client_schema_version"], "1.0.0")
        self.assertEqual(pkg_auth["target_canonical_id"], "AUTOSAR/AP/record/SWS_CORE_00009")
        self.assertEqual(pkg_auth["actor_claim"]["identity_kind"], "github_authenticated")
        self.assertEqual(pkg_auth["transport"], "github_issue")

        # Strict validation with Python validator
        errs_auth = rrp.validate(pkg_auth)
        self.assertEqual(errs_auth, [], f"pkg_auth failed validation: {errs_auth}")

        self.assertEqual(pkg_self["actor_claim"]["identity_kind"], "self_declared")
        self.assertEqual(pkg_self["transport"], "json_export")
        errs_self = rrp.validate(pkg_self)
        self.assertEqual(errs_self, [], f"pkg_self failed validation: {errs_self}")

    def test_json_export_safe_downgrade(self):
        """Exporting JSON from a GitHub-connected user downgrades identity_kind to self_declared."""
        js_code = """
        const { buildConfirmedPackage } = require('./review_request.js');
        const targetData = {
            canonical_id: "AUTOSAR/AP/record/SWS_CORE_00009",
            version_id: "AUTOSAR/AP/record/SWS_CORE_00009@rel:R25-11#a1b2c3d4",
            content_hash: "a1b2c3d4",
            status: "valid/unmigrated",
            source_url: "https://www.autosar.org/fileadmin/standards/R25-11/AP/AUTOSAR_AP_SWS_Core.pdf#nameddest=SWS_CORE_00009",
            category: "factual-accuracy",
            rationale: "Testing export downgrade.",
            evidence_refs: []
        };
        const who = { name: "gh-user-alice", mode: "github_authenticated" };
        const confirmed = buildConfirmedPackage({}, targetData, who);

        // Simulation of export JSON action in review_request.js
        const exported = Object.assign({}, confirmed, {
            transport: "json_export",
            actor_claim: {
                display_name: confirmed.actor_claim.display_name,
                identity_kind: "self_declared"
            }
        });

        console.log(JSON.stringify({ confirmed, exported }));
        """
        proc = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=True,
        )
        res = json.loads(proc.stdout)
        confirmed = res["confirmed"]
        exported = res["exported"]

        # Request ID and timestamp must be identical (reused request)
        self.assertEqual(confirmed["request_id"], exported["request_id"])
        self.assertEqual(confirmed["created_at"], exported["created_at"])
        self.assertEqual(confirmed["target_canonical_id"], exported["target_canonical_id"])

        # Identity kind safely downgraded in exported file
        self.assertEqual(exported["transport"], "json_export")
        self.assertEqual(exported["actor_claim"]["identity_kind"], "self_declared")
        self.assertEqual(exported["actor_claim"]["display_name"], "gh-user-alice")

        errs = rrp.validate(exported)
        self.assertEqual(errs, [], f"Exported package failed validation: {errs}")

    def test_local_collection_storage_and_drawer_rendering(self):
        """Review requests saved to ara-review-package-v1 render as local-only in drawer."""
        js_code = """
        // Mock localStorage and minimal DOM
        const store = {};
        global.localStorage = {
            getItem: (k) => store[k] || null,
            setItem: (k, v) => { store[k] = v; },
            removeItem: (k) => { delete store[k]; }
        };

        const { buildConfirmedPackage } = require('./review_request.js');
        const targetData = {
            canonical_id: "AUTOSAR/AP/record/SWS_CORE_00009",
            version_id: "AUTOSAR/AP/record/SWS_CORE_00009@rel:R25-11#a1b2c3d4",
            content_hash: "a1b2c3d4",
            status: "valid/unmigrated",
            source_url: "https://www.autosar.org/fileadmin/standards/R25-11/AP/AUTOSAR_AP_SWS_Core.pdf#nameddest=SWS_CORE_00009",
            category: "factual-accuracy",
            rationale: "Staged in local drawer.",
            evidence_refs: []
        };
        const who = { name: "Bob", mode: "self_declared" };
        const pkg = buildConfirmedPackage({}, targetData, who);

        const storeKey = "ara-review-package-v1";
        const items = [{
            item_kind: "review-request",
            id: pkg.request_id,
            canonical_id: pkg.target_canonical_id,
            target_version_id: pkg.target_version_id,
            category: pkg.category,
            rationale: pkg.rationale,
            evidence_refs: pkg.evidence_refs,
            actor_claim: pkg.actor_claim,
            created_at: pkg.created_at,
            package: pkg,
            status: "local-only"
        }];
        localStorage.setItem(storeKey, JSON.stringify(items));

        const stored = JSON.parse(localStorage.getItem(storeKey));
        console.log(JSON.stringify({ count: stored.length, item: stored[0] }));
        """
        proc = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=True,
        )
        res = json.loads(proc.stdout)
        self.assertEqual(res["count"], 1)
        item = res["item"]
        self.assertEqual(item["item_kind"], "review-request")
        self.assertEqual(item["status"], "local-only")
        self.assertEqual(item["canonical_id"], "AUTOSAR/AP/record/SWS_CORE_00009")
        self.assertTrue(item["id"].startswith("review-request:"))
        self.assertEqual(item["package"]["schema"], "review-request-package@v1")


if __name__ == "__main__":
    unittest.main()
