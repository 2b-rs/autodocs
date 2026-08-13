// todo-graph-embed.js
//
// Optional, self-guarding embed for the start page (index.html and its
// translated siblings). Behavior:
//   1. Try to fetch "TODO.md" (relative to the page).
//   2. If that fails (404, network error, or the file simply isn't part of
//      this deployment) -> do nothing. No Graphviz-WASM script is loaded,
//      no graph is rendered, no trace is left in the DOM.
//   3. Only if TODO.md loads successfully do we lazily load the vendored
//      Graphviz-WASM bundle (tools/vendor/hpcc-js-wasm-graphviz.umd.js) and
//      render the dependency graph into #tr-todo-graph.
//
// This means: in the published/public build (where TODO.md is intentionally
// NOT shipped), this script is a no-op and costs one small failed fetch --
// the ~800KB WASM bundle is never requested and never loaded.
//
// Parsing/DOT-building logic lives in tools/todo-graph-core.js (deduplicated
// 2026-08-13; see that file's header comment). This file must be loaded
// after todo-graph-core.js.
//
// The <details> collapse state of the rendered "TODO (internal)" section is
// persisted to localStorage so it survives page reloads/navigation.

(function () {
  'use strict';

  var host = document.getElementById('tr-todo-graph');
  if (!host) return;

  var core = window.TodoGraphCore;
  if (!core) {
    // todo-graph-core.js failed to load or wasn't included on this page.
    if (host.parentNode) host.parentNode.removeChild(host);
    return;
  }

  var STORAGE_KEY = 'todoGraphEmbed.open';

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('failed to load ' + src)); };
      document.body.appendChild(s);
    });
  }

  function getPersistedOpen() {
    try {
      var v = window.localStorage.getItem(STORAGE_KEY);
      return v === null ? true : v === '1'; // default: expanded on first visit
    } catch (e) {
      return true; // localStorage unavailable (private mode, etc.) -> default open
    }
  }

  function setPersistedOpen(isOpen) {
    try {
      window.localStorage.setItem(STORAGE_KEY, isOpen ? '1' : '0');
    } catch (e) {
      // localStorage unavailable -> silently ignore, collapse state just
      // won't persist across reloads for this session.
    }
  }

  function renderGraph(text) {
    var features = core.parseTodo(text);
    if (features.length === 0) return;
    var totalTasks = features.reduce(function (sum, f) { return sum + f.tasks.length; }, 0);
    if (totalTasks === 0) return;

    var built = core.buildDot(features, { taskLabelMaxLen: 50 });

    return loadScript('tools/vendor/hpcc-js-wasm-graphviz.umd.js').then(function () {
      var hpcc = window['@hpcc-js/wasm/graphviz'];
      if (!hpcc || !hpcc.Graphviz) return;
      return hpcc.Graphviz.load().then(function (gv) {
        var svg = gv.layout(built.dot, 'svg', 'dot');
        var legend =
          '<div style="font-size:.8rem;color:#596274;margin:.4rem 0 .8rem;display:flex;flex-wrap:wrap;gap:0;">' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:3px;border-radius:2px;background:black;"></i>same-feature / explicit</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:3px;border-radius:2px;background:#1f4e79;"></i>cross-feature / explicit</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:3px;border-radius:2px;background:crimson;"></i>cross-feature / implicit</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:0;border-top:2px dashed gray;"></i>cross-feature / soft</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;border:1px solid #c7ccd6;background:#ffffff;"></i>open [ ]</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#fff3b0;"></i>partial [p]</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#ffb3b3;"></i>unclear [u]</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#d9d9d9;"></i>unknown [?]</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#b6e3b6;"></i>done [x]</span>' +
          '</div>';
        var wrap = document.createElement('details');
        wrap.className = 'fold';
        wrap.open = getPersistedOpen();
        wrap.innerHTML =
          '<summary><h2 class="sect" style="display:inline">TODO (internal)</h2></summary>' +
          legend +
          svg;
        var svgEl = wrap.querySelector('svg');
        if (svgEl) {
          svgEl.removeAttribute('width');
          svgEl.removeAttribute('height');
          svgEl.style.width = '100%';
          svgEl.style.height = 'auto';
          svgEl.style.display = 'block';
        }
        wrap.addEventListener('toggle', function () {
          setPersistedOpen(wrap.open);
        });
        host.replaceWith(wrap);
      });
    });
  }

  fetch('TODO.md', { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('TODO.md not available (HTTP ' + res.status + ')');
      return res.text();
    })
    .then(renderGraph)
    .catch(function () {
      // TODO.md not present in this deployment (expected for the published
      // site) -> silently do nothing. No WASM bundle is fetched, no graph
      // is rendered, the placeholder div is simply removed.
      if (host && host.parentNode) host.parentNode.removeChild(host);
    });
})();
