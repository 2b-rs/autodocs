"""DOM/consumer tests for tools/todo-dependency-graph.html (Task 0037-22)."""

from __future__ import annotations

import html.parser
import importlib.util
import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "tools/todo-dependency-graph.html"
CORE_JS = ROOT / "tools/todo-graph-core.js"
FIXTURES = ROOT / "_src/tests/fixtures/0037-12"

SPEC = importlib.util.spec_from_file_location(
    "todo_graph_adapter", ROOT / "_src/tools/todo_graph_adapter.py")
ADP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADP)

LEGEND_KEYS = (
    "explicit_same",
    "explicit_cross",
    "feature_closure",
    "relation",
    "done_edge",
    "open",
    "in_progress",
    "blocked",
    "withdrawn",
    "missing_malformed",
    "closed",
    "archived",
)


class _Collector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.script_src = []
        self._in_script = False
        self._script_src = None
        self.ids = set()
        self.legend = set()
        self.aria = {}
        self.roles = []
        self.skip = []
        self.checkboxes = []
        self.buttons = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        ad = dict(attrs)
        if "id" in ad:
            self.ids.add(ad["id"])
        if tag == "script":
            self._in_script = True
            self._script_src = ad.get("src")
            if ad.get("src"):
                self.script_src.append(ad["src"])
        if tag == "span" and ad.get("data-legend"):
            self.legend.add(ad["data-legend"])
        if "aria-label" in ad:
            self.aria[ad.get("id") or tag] = ad["aria-label"]
        if "role" in ad:
            self.roles.append((tag, ad["role"], ad.get("id")))
        if tag == "a" and "skip" in (ad.get("class") or ""):
            self.skip.append(ad.get("href"))
        if tag == "input" and ad.get("type") == "checkbox":
            self.checkboxes.append(ad.get("id"))
        if tag == "button":
            self.buttons.append(ad.get("id"))

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
            self._script_src = None

    def handle_data(self, data):
        if self._in_script and not self._script_src:
            self.scripts.append(data)
        self.text.append(data)


def _parse_html():
    parser = _Collector()
    parser.feed(HTML.read_text(encoding="utf-8"))
    return parser


def _node_harness(mode, payload_path=None, extra=None):
    html_text = HTML.read_text(encoding="utf-8")
    script = r"""
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const htmlPath = process.argv[1];
const corePath = process.argv[2];
const mode = process.argv[3];
const payloadPath = process.argv[4] || '';
const extra = process.argv[5] || '';
const html = fs.readFileSync(htmlPath, 'utf8');
const inline = [];
html.replace(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g, (m, body, offset) => {
  if (/src=/.test(m.slice(0, m.indexOf('>')))) return m;
  inline.push(body);
  return m;
});
if (!inline.length) {
  process.stdout.write(JSON.stringify({ok:false,error:'no inline script'}));
  process.exit(0);
}

function makeEl(tag, id) {
  const el = {
    tagName: String(tag).toUpperCase(),
    id: id || '',
    className: '',
    hidden: false,
    textContent: '',
    innerHTML: '',
    disabled: false,
    checked: true,
    href: '',
    scrollLeft: 0,
    scrollTop: 0,
    style: {},
    attrs: {},
    children: [],
    parentNode: null,
    setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'href') this.href = String(v); },
    getAttribute(k) { return this.attrs[k]; },
    appendChild(c) {
      c.parentNode = this;
      this.children.push(c);
      const t = c.textContent || '';
      const href = c.href || (c.attrs && c.attrs.href) || '';
      let snippet = '';
      if (c.tagName === 'A') snippet = '<a href="'+href+'" data-internal-link="1">'+t+'</a>';
      else if (c.tagName === 'LI') {
        snippet = '<li data-item-id="'+(c.attrs['data-item-id']||'')+'">'+c.innerHTML+'</li>';
      } else if (c.attrs && c.attrs['data-redacted-endpoint']) {
        snippet = '<span data-redacted-endpoint="1">'+t+'</span>';
      } else {
        snippet = '<span>'+t+'</span>' + (c.innerHTML || '');
      }
      this.innerHTML += snippet;
      this.textContent += t;
      return c;
    },
    addEventListener() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  return el;
}

const byId = {};
['status','provenance','graph-container','graph-stage','item-list','btn-rerender',
 'btn-zoom-in','btn-zoom-out','btn-zoom-reset','chk-include-done','chk-include-w'
].forEach((id) => { byId[id] = makeEl(id.startsWith('chk') ? 'input' : (id.startsWith('btn') ? 'button' : 'div'), id); });
byId['chk-include-done'].checked = extra !== 'no-closed';
byId['chk-include-w'].checked = extra !== 'no-w';
byId['graph-container'].tagName = 'DIV';

const listeners = { keydown: [], click: {}, wheel: [] };
const fetchCalls = [];
let graphvizPresent = extra !== 'no-graphviz';
const catalogText = payloadPath ? fs.readFileSync(payloadPath, 'utf8') : '';

function installCore(ctx) {
  const code = fs.readFileSync(corePath, 'utf8');
  vm.runInContext(code, ctx, {filename: corePath});
}

const document = {
  getElementById(id) { return byId[id] || null; },
  createElement(tag) {
    const el = makeEl(tag);
    el.outerSnippet = '';
    return el;
  },
  addEventListener(type, fn) { if (type === 'keydown') listeners.keydown.push(fn); },
};
const windowObj = { TodoGraphCore: null, localStorage: { getItem(){return null;}, setItem(){} } };
const hpcc = graphvizPresent ? {
  Graphviz: {
    load() {
      return Promise.resolve({
        layout(dot) {
          const urls = [];
          const re = /URL="([^"]+)"/g;
          let m;
          while ((m = re.exec(dot))) urls.push(m[1]);
          const anchors = urls.map(u => '<a href="'+u+'">node</a>').join('');
          return '<svg xmlns="http://www.w3.org/2000/svg">'+anchors+'</svg>';
        }
      });
    }
  }
} : undefined;

const ctx = vm.createContext({
  window: windowObj,
  document,
  globalThis: {},
  console,
  fetch(url, opts) {
    fetchCalls.push({url, opts});
    if (extra === 'http-404') {
      return Promise.resolve({ok: false, status: 404, text() { return Promise.resolve(''); }});
    }
    return Promise.resolve({ok: true, status: 200, text() { return Promise.resolve(catalogText); }});
  },
  Promise,
  Array,
  Object,
  String,
  Math,
  JSON,
  Error,
  module: {exports: {}},
  exports: {},
});
ctx.globalThis = ctx;
ctx.window = windowObj;
windowObj.document = document;
installCore(ctx);
windowObj.TodoGraphCore = ctx.TodoGraphCore || ctx.module.exports;
ctx.window.TodoGraphCore = windowObj.TodoGraphCore;
if (graphvizPresent) ctx.globalThis['@hpcc-js/wasm/graphviz'] = hpcc;

vm.runInContext(inline[inline.length - 1], ctx, {filename: 'todo-dependency-graph.html'});

function wait(p) { return Promise.resolve(p); }

async function run() {
  const page = ctx.window.TodoGraphPage;
  if (mode === 'static-api') {
    process.stdout.write(JSON.stringify({
      ok: true,
      GRAPH_URL: page.GRAPH_URL,
      TRACKED_ASSETS: page.TRACKED_ASSETS,
      hasParseTodo: typeof windowObj.TodoGraphCore.parseTodo === 'function',
      hasLoadGraph: typeof windowObj.TodoGraphCore.loadGraph === 'function'
    }));
    return;
  }
  if (mode === 'render') {
    await page.renderFromText(catalogText);
    process.stdout.write(JSON.stringify({
      ok: true,
      status: byId.status.textContent,
      statusError: byId.status.className === 'error',
      provenance: byId.provenance.textContent,
      provenanceHidden: byId.provenance.hidden,
      itemHtml: byId['item-list'].innerHTML,
      itemCount: byId['item-list'].children.length,
      stage: byId['graph-stage'].innerHTML,
      zoom: page.getZoom(),
      fetchCalls
    }));
    return;
  }
  if (mode === 'fetch') {
    await page.loadAndRender();
    process.stdout.write(JSON.stringify({
      ok: true,
      status: byId.status.textContent,
      statusError: byId.status.className === 'error',
      fetchCalls
    }));
    return;
  }
  if (mode === 'zoom-keys') {
    await page.renderFromText(catalogText);
    page.handleKey({key: '+', preventDefault() {}, target: {tagName: 'DIV'}});
    const afterPlus = page.getZoom();
    page.handleKey({key: '0', preventDefault() {}, target: {tagName: 'DIV'}});
    const afterZero = page.getZoom();
    page.handleKey({key: 'ArrowRight', preventDefault() {}, target: {tagName: 'BODY'}});
    process.stdout.write(JSON.stringify({
      ok: true, afterPlus, afterZero, scrollLeft: byId['graph-container'].scrollLeft
    }));
    return;
  }
  if (mode === 'missing-gv') {
    await page.renderFromText(catalogText);
    process.stdout.write(JSON.stringify({
      ok: true,
      status: byId.status.textContent,
      statusError: byId.status.className === 'error'
    }));
    return;
  }
  process.stdout.write(JSON.stringify({ok:false,error:'unknown mode'}));
}
run().catch((err) => {
  process.stdout.write(JSON.stringify({ok:false,error:String(err && err.stack || err)}));
});
"""
    args = ["node", "-e", script, str(HTML), str(CORE_JS), mode, str(payload_path or ""), extra or ""]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class TodoDependencyGraphHtmlTest(unittest.TestCase):
    maxDiff = None

    def test_no_todo_md_fetch_and_tracked_assets_only(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertNotIn("../TODO.md", html)
        self.assertNotIn("fetch('../TODO.md'", html)
        self.assertNotIn('fetch("../TODO.md"', html)
        self.assertNotIn('fetch("../TODO.md"', html.replace("'", '"'))
        self.assertIn("../issues/_views/dependency-graph.json", html)
        self.assertIn("python3 -m http.server", html)
        parser = _parse_html()
        self.assertEqual(
            parser.script_src,
            ["todo-graph-core.js", "vendor/hpcc-js-wasm-graphviz.umd.js"],
        )
        self.assertNotIn("cdn", html.lower())
        api = _node_harness("static-api")
        self.assertTrue(api["ok"], api)
        self.assertEqual(api["GRAPH_URL"], "../issues/_views/dependency-graph.json")
        self.assertEqual(
            api["TRACKED_ASSETS"],
            ["todo-graph-core.js", "vendor/hpcc-js-wasm-graphviz.umd.js"],
        )
        self.assertFalse(api["hasParseTodo"])
        self.assertTrue(api["hasLoadGraph"])

    def test_legend_covers_every_state_and_edge_class(self):
        parser = _parse_html()
        self.assertEqual(set(LEGEND_KEYS), parser.legend)
        html = HTML.read_text(encoding="utf-8")
        for key in LEGEND_KEYS:
            self.assertIn(f'data-legend="{key}"', html)

    def test_accessibility_landmarks_and_keyboard_controls(self):
        parser = _parse_html()
        self.assertIn("graph-container", parser.ids)
        self.assertIn("item-nav", parser.ids)
        self.assertIn("status", parser.ids)
        self.assertIn("#graph-container", parser.skip)
        self.assertIn("chk-include-done", parser.checkboxes)
        self.assertIn("chk-include-w", parser.checkboxes)
        for bid in ("btn-zoom-in", "btn-zoom-out", "btn-zoom-reset", "btn-rerender"):
            self.assertIn(bid, parser.buttons)
        html = HTML.read_text(encoding="utf-8")
        self.assertIn('aria-live="polite"', html)
        self.assertIn('role="status"', html)
        self.assertIn('role="toolbar"', html)
        self.assertIn('role="region"', html)
        self.assertIn('tabindex="0"', html)
        self.assertIn("Skip to graph", html)
        js = _node_harness("zoom-keys", FIXTURES / "golden-graph.json")
        self.assertTrue(js["ok"], js)
        self.assertGreater(js["afterPlus"], 1)
        self.assertEqual(js["afterZero"], 1)
        self.assertEqual(js["scrollLeft"], 40)

    def test_golden_catalog_count_and_edge_parity(self):
        path = FIXTURES / "golden-graph.json"
        graph = ADP.load_graph(path.read_text(encoding="utf-8"))
        tallies = ADP.counts(graph)
        built = ADP.build_dot(graph)
        js = _node_harness("render", path)
        self.assertTrue(js["ok"], js)
        self.assertFalse(js["statusError"], js["status"])
        self.assertIn(f"Catalog nodes={tallies['nodes']}", js["status"])
        self.assertIn(f"features={tallies['features']}", js["status"])
        self.assertIn(f"tasks={tallies['tasks']}", js["status"])
        self.assertIn(f"subtasks={tallies['subtasks']}", js["status"])
        self.assertIn(f"withdrawn={tallies['withdrawn']}", js["status"])
        self.assertIn(f"missing={tallies['missing_nodes']}", js["status"])
        self.assertIn(f"malformed={tallies['malformed_nodes']}", js["status"])
        self.assertIn(f"edges={tallies['edges']}", js["status"])
        self.assertIn(f"start-gate={tallies['start_gate_edges']}", js["status"])
        self.assertIn(f"feature-closure={tallies['feature_closure_edges']}", js["status"])
        self.assertIn(f"unresolved={tallies['unresolved_edges']}", js["status"])
        self.assertIn(f"Rendered {built['nodeCount']} node(s)", js["status"])
        self.assertIn(f"{built['edgeCount']} edge(s)", js["status"])
        self.assertIn(f"unresolved edges kept: {built['unresolvedEdgeCount']}", js["status"])
        self.assertIn("generation_id=" + graph["generation_id"], js["provenance"])
        self.assertIn("schema_sha256=" + graph["digests"]["schema_sha256"], js["provenance"])
        self.assertIn("tool_sha256=" + graph["digests"]["tool_sha256"], js["provenance"])
        self.assertIn("config_sha256=" + graph["digests"]["config_sha256"], js["provenance"])
        self.assertIn(
            "catalog_generation_id=" + graph["digests"]["catalog_generation_id"],
            js["provenance"],
        )
        self.assertNotIn("run_id", js["provenance"].lower())
        self.assertNotIn("execution-run", js["provenance"].lower())
        self.assertNotIn("execution_run", js["status"].lower())

    def test_every_state_and_edge_class_visible_in_golden_dot_and_nav(self):
        path = FIXTURES / "golden-graph.json"
        graph = ADP.load_graph(path.read_text(encoding="utf-8"))
        built = ADP.build_dot(graph)
        dot = built["dot"]
        self.assertIn('color="black"', dot)
        self.assertIn('color="#1f4e79"', dot)
        self.assertIn("crimson", dot)
        self.assertIn("#6a1b9a", dot)
        self.assertIn("#d9d9d9", dot)
        self.assertIn("[w]", dot)
        self.assertIn("missing", dot)
        self.assertIn("malformed", dot)
        self.assertIn("archived-not-accepted", dot)
        js = _node_harness("render", path)
        ids = {n["id"] for n in graph["nodes"]}
        for nid in ids:
            self.assertIn(nid, js["itemHtml"])
        self.assertIn('data-redacted-endpoint', js["itemHtml"])
        self.assertIn("/issues/0081/", js["itemHtml"])
        self.assertIn("/issues/0081/", js["stage"])

    def test_item_navigation_links_and_redacted_endpoints(self):
        path = FIXTURES / "golden-graph.json"
        js = _node_harness("render", path)
        self.assertIn('href="/issues/0081/"', js["itemHtml"])
        self.assertIn("not a valid id (redacted/no url)", js["itemHtml"])
        self.assertIn("0090-01", js["itemHtml"])
        self.assertIn("missing", js["itemHtml"])
        self.assertIn("malformed", js["itemHtml"])
        self.assertIn("archived-not-accepted", js["itemHtml"])

    def test_malformed_and_stale_data_fail_visibly(self):
        stale = _node_harness("render", FIXTURES / "stale-schema.json")
        self.assertTrue(stale["ok"], stale)
        self.assertTrue(stale["statusError"])
        self.assertTrue(stale["status"].startswith("ERROR:"))
        self.assertIn("schema", stale["status"].lower())
        md = _node_harness("render", FIXTURES / "legacy-todo.md")
        self.assertTrue(md["statusError"])
        self.assertIn("Markdown", md["status"])
        self.assertNotIn("../TODO.md", md["status"].split("ERROR:")[0])
        dup = _node_harness("render", FIXTURES / "duplicate-ids.json")
        self.assertTrue(dup["statusError"])
        self.assertIn("duplicate", dup["status"].lower())
        dropped = _node_harness("render", FIXTURES / "dropped-endpoint.json")
        self.assertTrue(dropped["statusError"])
        self.assertIn("silently dropped", dropped["status"])

    def test_missing_catalog_endpoint_is_actionable(self):
        js = _node_harness("fetch", FIXTURES / "golden-graph.json", "http-404")
        self.assertTrue(js["statusError"])
        self.assertIn("HTTP 404", js["status"])
        self.assertEqual(js["fetchCalls"][0]["url"], "../issues/_views/dependency-graph.json")
        self.assertNotIn("TODO.md", js["fetchCalls"][0]["url"])

    def test_missing_graphviz_assets_fail_visibly(self):
        js = _node_harness("missing-gv", FIXTURES / "golden-graph.json", "no-graphviz")
        self.assertTrue(js["statusError"], js)
        self.assertIn("Graphviz", js["status"])
        self.assertIn("vendor/hpcc-js-wasm-graphviz.umd.js", js["status"])

    def test_filtering_preserves_unresolved_instead_of_dropping(self):
        path = FIXTURES / "golden-graph.json"
        js = _node_harness("render", path, "no-closed")
        self.assertTrue(js["ok"], js)
        if js["statusError"]:
            self.assertIn("ERROR:", js["status"])
        else:
            self.assertIn("Catalog nodes=", js["status"])


if __name__ == "__main__":
    unittest.main()
