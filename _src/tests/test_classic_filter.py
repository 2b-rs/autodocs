#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit and integration tests for Classic Cluster Navigation & Filter Bar."""
from __future__ import annotations

import glob
import os
import subprocess
import sys
import unittest
from pathlib import Path
from lxml import html

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "_src"
sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(_SRC / "tools"))

import lib_docmodel as dm
import generate


class TestClassicFilterIntegration(unittest.TestCase):
    """Integration checks for template, static assets, and generated classic pages."""

    def test_static_script_exists_and_synced(self):
        src_script = _SRC / "static" / "classic-filter.js"
        root_script = _REPO_ROOT / "classic-filter.js"
        self.assertTrue(src_script.is_file(), "_src/static/classic-filter.js must exist")
        self.assertTrue(root_script.is_file(), "classic-filter.js must exist at repo root")
        self.assertEqual(src_script.read_text(encoding="utf-8"), root_script.read_text(encoding="utf-8"))

    def test_template_and_docmodel_bindings(self):
        tmpl_text = (_SRC / "templates" / "page.html.tmpl").read_text(encoding="utf-8")
        self.assertIn("%(classic_filter_js)s", tmpl_text)

        # Verify lib_docmodel renders classic_filter_js
        page_tmpl, footers = dm.load_templates()
        page = {
            "title": "Classic Test",
            "file": "classic/test.html",
            "body_class": "vis-app",
            "nav_html": "Classic > Test",
            "footer": "extracted",
            "main": [{"t": "html", "html": "<h1>Test</h1>"}]
        }
        rendered = dm.render_page(page, footers, page_tmpl)
        self.assertIn('<script src="../classic-filter.js" defer></script>', rendered)

    def test_generated_classic_pages_have_script(self):
        classic_pages = list(_REPO_ROOT.glob("classic/*.html"))
        self.assertGreater(len(classic_pages), 5)
        for page_path in classic_pages:
            with self.subTest(page=page_path.name):
                content = page_path.read_text(encoding="utf-8")
                self.assertIn('classic-filter.js', content)

    def test_real_classic_cluster_structure(self):
        expected_clusters = {
            "classic/diagnostics.html": {
                "modules": ["DEM", "DCM", "DET", "DLT"],
                "total_items": 316,
                "counts": {"DEM": 141, "DCM": 123, "DET": 10, "DLT": 42}
            },
            "classic/can.html": {
                "modules": ["Can", "CanIf", "CanTrcv", "CanTp"],
                "total_items": 112,
                "counts": {"Can": 27, "CanIf": 50, "CanTrcv": 23, "CanTp": 12}
            },
            "classic/ethernet.html": {
                "modules": ["Eth", "EthIf", "TcpIp"],
                "total_items": 198,
                "counts": {"Eth": 42, "EthIf": 92, "TcpIp": 64}
            },
            "classic/memory.html": {
                "modules": ["NvM", "MemIf", "Fee", "Ea"],
                "total_items": 80,
                "counts": {"NvM": 36, "MemIf": 12, "Fee": 16, "Ea": 16}
            }
        }

        for rel_path, exp in expected_clusters.items():
            full_path = _REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"{rel_path} must exist")
            doc = html.parse(str(full_path)).getroot()
            cards = doc.xpath('//a[@class="card"]')
            self.assertGreaterEqual(len(cards), len(exp["modules"]), f"Not enough cards in {rel_path}")

            card_links = [c.attrib.get("href", "") for c in cards]
            for mod in exp["modules"]:
                expected_link = f"modules/{mod.lower()}.html"
                self.assertIn(expected_link, card_links, f"Missing card link {expected_link} in {rel_path}")

            # Verify dedicated module pages and item counts
            cluster_total = 0
            actual_counts = {}
            for mod in exp["modules"]:
                mod_path = _REPO_ROOT / "classic" / "modules" / f"{mod.lower()}.html"
                self.assertTrue(mod_path.is_file(), f"Module page {mod_path} must exist")
                mod_doc = html.parse(str(mod_path)).getroot()
                recs = mod_doc.xpath('//article[@class="rec"]')
                self.assertEqual(len(recs), 1, f"Expected 1 rec article in {mod_path}")
                h3s = recs[0].xpath('.//h3[@class="recname"]')
                actual_counts[mod] = len(h3s)
                cluster_total += len(h3s)

            self.assertEqual(cluster_total, exp["total_items"], f"Total items mismatch for {rel_path}")
            if "counts" in exp:
                self.assertEqual(actual_counts, exp["counts"], f"Module counts mismatch for {rel_path}")

    def test_style_css_contains_classic_filter_rules(self):
        css = (_REPO_ROOT / "style.css").read_text(encoding="utf-8")
        required_selectors = [
            ".classic-filter-bar",
            ".classic-filter-top",
            ".classic-filter-search",
            ".classic-search-input",
            ".classic-search-clear",
            ".classic-kind-switch",
            ".classic-kind-btn",
            ".classic-filter-status",
            ".classic-filter-modules",
            ".classic-pill",
            ".classic-pill-btn",
            ".classic-pill-jump",
            ".classic-module-section",
            ".classic-heading-anchor",
            ".classic-entry",
            ".classic-filter-empty",
            '.classic-pill.is-active',
            '.classic-kind-btn.is-active',
            '[dir="rtl"] .classic-search-icon',
            '[data-density="compact"] .classic-filter-bar',
            '@media (max-width: 767px)',
        ]
        for sel in required_selectors:
            with self.subTest(selector=sel):
                self.assertIn(sel, css)


class TestClassicFilterJsLogic(unittest.TestCase):
    """Executes Node.js test runner against _src/static/classic-filter.js."""

    def test_node_filter_logic(self):
        node_script = r"""
const assert = require('assert');
const path = require('path');
const filter = require('./_src/static/classic-filter.js');

// 1. Test module abbreviation extraction
const abbrevCases = [
  ['Diagnostic Event Manager (DEM)', 'DEM'],
  ['Diagnostic Communication Manager (DCM)', 'DCM'],
  ['Default Error Tracer (DET)', 'DET'],
  ['Diagnostic Log and Trace (DLT)', 'DLT'],
  ['CAN Driver (Can)', 'Can'],
  ['CAN Interface (CanIf)', 'CanIf'],
  ['CAN Transceiver Driver (CanTrcv)', 'CanTrcv'],
  ['CAN Transport Layer (CanTp)', 'CanTp'],
  ['AUTOSAR COM', 'COM'],
  ['PDU Router (PduR)', 'PduR'],
  ['Communication Manager (ComM)', 'ComM'],
  ['Crypto Service Manager (CSM)', 'CSM'],
  ['Crypto Interface (CryIf)', 'CryIf'],
  ['Crypto Driver (Crypto)', 'Crypto'],
  ['AUTOSAR OS', 'OS'],
  ['AUTOSAR RTE', 'RTE'],
  ['NVRAM Manager (NvM)', 'NvM'],
  ['ECU State Manager (EcuM)', 'EcuM'],
  ['BSW Mode Manager (BswM)', 'BswM'],
  ['Watchdog Manager (WdgM)', 'WdgM']
];

for (const [input, expected] of abbrevCases) {
  assert.strictEqual(filter.extractModuleAbbreviation(input), expected, `Failed for ${input}`);
}

// 2. Mock DOM environment for interactive tests
class MockElement {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.style = {};
    this.classList = {
      _classes: new Set(),
      add: (c) => this.classList._classes.add(c),
      remove: (c) => this.classList._classes.delete(c),
      toggle: (c, force) => {
        if (force === undefined) {
          if (this.classList._classes.has(c)) this.classList._classes.delete(c);
          else this.classList._classes.add(c);
        } else if (force) {
          this.classList._classes.add(c);
        } else {
          this.classList._classes.delete(c);
        }
      },
      contains: (c) => this.classList._classes.has(c)
    };
    this.parentNode = null;
    this.hidden = false;
    this._textContent = '';
    this._value = '';
    this.events = {};
  }
  get id() { return this.attributes['id'] || ''; }
  set id(v) { this.attributes['id'] = v; }
  get className() { return Array.from(this.classList._classes).join(' '); }
  set className(v) {
    this.classList._classes = new Set(v ? v.split(/\s+/).filter(Boolean) : []);
  }
  get textContent() {
    if (this.children.length === 0) return this._textContent;
    return this.children.map(c => c.textContent).join('');
  }
  set textContent(v) {
    this._textContent = v;
    this.children = [];
  }
  get value() { return this._value; }
  set value(v) { this._value = v; }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k] || null; }
  appendChild(child) {
    if (child.parentNode) child.parentNode.removeChild(child);
    this.children.push(child);
    child.parentNode = this;
    return child;
  }
  prepend(child) {
    if (child.parentNode) child.parentNode.removeChild(child);
    this.children.unshift(child);
    child.parentNode = this;
    return child;
  }
  insertBefore(newChild, refChild) {
    if (newChild.parentNode) newChild.parentNode.removeChild(newChild);
    const idx = this.children.indexOf(refChild);
    if (idx === -1) this.children.push(newChild);
    else this.children.splice(idx, 0, newChild);
    newChild.parentNode = this;
    return newChild;
  }
  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      this.children.splice(idx, 1);
      child.parentNode = null;
    }
    return child;
  }
  cloneNode(deep) {
    const clone = new MockElement(this.tagName.toLowerCase());
    clone._textContent = this._textContent;
    clone.attributes = { ...this.attributes };
    clone.classList._classes = new Set(this.classList._classes);
    if (deep) {
      this.children.forEach(c => clone.appendChild(c.cloneNode(true)));
    }
    return clone;
  }
  remove() {
    if (this.parentNode) this.parentNode.removeChild(this);
  }
  addEventListener(evt, cb) {
    if (!this.events[evt]) this.events[evt] = [];
    this.events[evt].push(cb);
  }
  dispatchEvent(evt) {
    const name = typeof evt === 'string' ? evt : evt.type;
    const list = this.events[name] || [];
    list.forEach(cb => cb(evt));
  }
  closest(selector) {
    let el = this;
    while (el) {
      if (el.matches && el.matches(selector)) return el;
      el = el.parentNode;
    }
    return null;
  }
  matches(selector) {
    if (selector.startsWith('#')) return this.id === selector.slice(1);
    if (selector.includes('[')) {
      const m = selector.match(/\[([a-z0-9_-]+)(?:=\"?([^\"]*)\"?)?\]/i);
      if (m) {
        const val = this.getAttribute(m[1]);
        if (m[2] !== undefined) return val === m[2];
        return val !== null;
      }
    }
    const parts = selector.split('.');
    const tag = parts[0];
    const cls = parts[1];
    if (tag && this.tagName.toLowerCase() !== tag.toLowerCase()) return false;
    if (cls && !this.classList.contains(cls)) return false;
    return true;
  }
  querySelector(selector) {
    const res = this.querySelectorAll(selector);
    return res.length > 0 ? res[0] : null;
  }
  querySelectorAll(selector) {
    const matches = [];
    const search = (node) => {
      for (const child of node.children) {
        if (child.matches(selector)) matches.push(child);
        search(child);
      }
    };
    search(this);
    return matches;
  }
  scrollIntoView() {}
  focus() {}
  blur() {}
  select() {}
}

global.document = {
  readyState: 'loading',
  documentElement: new MockElement('html'),
  body: new MockElement('body'),
  createElement: (tag) => new MockElement(tag),
  querySelector: (sel) => global.document.body.querySelector(sel),
  querySelectorAll: (sel) => global.document.body.querySelectorAll(sel),
  addEventListener: () => {},
  activeElement: null
};
global.document.documentElement.setAttribute('lang', 'de');
global.window = {
  location: { pathname: '/classic/diagnostics.html', hash: '' },
  addEventListener: () => {}
};

// Build mock DOM:
const main = new MockElement('main');
global.document.body.appendChild(main);

const crumbs = new MockElement('nav');
crumbs.className = 'crumbs';
crumbs.textContent = 'AUTOSAR Classic > Diagnostics';
global.document.body.appendChild(crumbs);

const rec = new MockElement('article');
rec.className = 'rec';
rec.id = 'CP_DIAG';
main.appendChild(rec);

// Add DEM module with 2 functions and 1 type
const h2Dem = new MockElement('h2');
h2Dem.textContent = 'Diagnostic Event Manager (DEM)';
rec.appendChild(h2Dem);

function addRecItem(article, kind, name, sws) {
  const h3 = new MockElement('h3');
  h3.className = 'recname';
  const kSpan = new MockElement('span'); kSpan.className = 'kind'; kSpan.textContent = kind;
  const swsSpan = new MockElement('span'); swsSpan.className = 'sws'; swsSpan.textContent = '[' + sws + ']';
  const nSpan = new MockElement('span'); nSpan.textContent = name + ' ';
  h3.appendChild(kSpan);
  h3.appendChild(nSpan);
  h3.appendChild(swsSpan);
  article.appendChild(h3);

  const pre = new MockElement('pre');
  pre.className = 'syntax';
  pre.textContent = 'void ' + name + '();';
  article.appendChild(pre);

  const desc = new MockElement('div');
  desc.className = 'desc';
  desc.textContent = 'Description for ' + name;
  article.appendChild(desc);
}

addRecItem(rec, 'function', 'Dem_GetVersionInfo', 'SWS_Dem_00177');
addRecItem(rec, 'function', 'Dem_Init', 'SWS_Dem_00181');
addRecItem(rec, 'type', 'Dem_ConfigType', 'SWS_Dem_00924');

// Add DCM module with 1 function
const h2Dcm = new MockElement('h2');
h2Dcm.textContent = 'Diagnostic Communication Manager (DCM)';
rec.appendChild(h2Dcm);
addRecItem(rec, 'function', 'Dcm_GetVersionInfo', 'SWS_Dcm_00065');

// Initialize filter
const instance = filter.init();
assert(instance, 'ClassicFilter.init() must return an instance');
assert.strictEqual(instance.modules.length, 2);
assert.strictEqual(instance.items.length, 4);

// Test Filter Bar UI elements
const filterBar = main.querySelector('.classic-filter-bar');
assert(filterBar, 'filter-bar must be inserted into main');
assert.strictEqual(filterBar.getAttribute('role'), 'region');

// Verify Kind switch buttons
const kindBtns = filterBar.querySelectorAll('.classic-kind-btn');
assert.strictEqual(kindBtns.length, 3);
assert.strictEqual(kindBtns[0].getAttribute('aria-pressed'), 'true'); // Alle
assert.strictEqual(kindBtns[1].getAttribute('aria-pressed'), 'false'); // Funktionen
assert.strictEqual(kindBtns[2].getAttribute('aria-pressed'), 'false'); // Typen

// Verify Module pills
const pills = filterBar.querySelectorAll('.classic-pill');
assert.strictEqual(pills.length, 3); // Alle, DEM, DCM
assert(pills[0].classList.contains('is-active')); // Alle is active

// Test Module Filter Interaction
instance.state.activeModule = 'DEM';
instance.applyFilters();

const demSection = main.querySelector('#mod-dem');
const dcmSection = main.querySelector('#mod-dcm');
assert.strictEqual(demSection.hidden, false, 'DEM section must be visible');
assert.strictEqual(dcmSection.hidden, true, 'DCM section must be hidden');
assert.strictEqual(pills[1].classList.contains('is-active'), true, 'DEM pill must be active');

// Test Kind Filter Interaction
instance.state.activeModule = 'all';
instance.state.activeKind = 'type';
instance.applyFilters();

assert.strictEqual(instance.items[0].entryEl.hidden, true, 'Dem_GetVersionInfo (func) must be hidden');
assert.strictEqual(instance.items[2].entryEl.hidden, false, 'Dem_ConfigType (type) must be visible');

// Test Search Filter Interaction (SWS-ID)
instance.state.activeKind = 'all';
instance.state.searchQuery = '00065';
instance.applyFilters();

assert.strictEqual(instance.items[3].entryEl.hidden, false, 'Dcm item with SWS 00065 must be visible');
assert.strictEqual(instance.items[0].entryEl.hidden, true, 'Dem item must be hidden');
assert.strictEqual(demSection.hidden, true, 'DEM section must be hidden when 0 matches');
assert.strictEqual(dcmSection.hidden, false, 'DCM section must be visible');

// Test Search Filter Interaction (Name search)
instance.state.searchQuery = 'Dem_Init';
instance.applyFilters();
assert.strictEqual(instance.items[1].entryEl.hidden, false, 'Dem_Init must be visible');
assert.strictEqual(instance.items[0].entryEl.hidden, true, 'Dem_GetVersionInfo must be hidden');

// Test Empty State when no match
instance.state.searchQuery = 'NonExistentFunction123';
instance.applyFilters();
const emptyBox = main.querySelector('.classic-filter-empty');
assert.strictEqual(emptyBox.hidden, false, 'Empty box must be shown when 0 items match');

// Test Reset
instance.state.searchQuery = '';
instance.state.activeModule = 'all';
instance.state.activeKind = 'all';
instance.applyFilters();
assert.strictEqual(emptyBox.hidden, true, 'Empty box must be hidden after reset');
assert.strictEqual(demSection.hidden, false, 'DEM section must be visible');
assert.strictEqual(dcmSection.hidden, false, 'DCM section must be visible');
assert.strictEqual(instance.items.every(i => !i.entryEl.hidden), true, 'All items must be visible');

console.log('All Classic Filter JS tests passed successfully!');
        """
        temp_js = _REPO_ROOT / "_temp_test_classic_filter.js"
        temp_js.write_text(node_script, encoding="utf-8")
        try:
            res = subprocess.run(["node", str(temp_js)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Node tests failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
        finally:
            if temp_js.exists():
                temp_js.unlink()


if __name__ == "__main__":
    unittest.main()
