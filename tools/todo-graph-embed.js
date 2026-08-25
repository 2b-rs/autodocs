// todo-graph-embed.js
//
// Optional, self-guarding embed for the start page. Fetches
// issues/_views/dependency-graph.json (never TODO.md). Missing catalog
// (published site) is a silent no-op. Malformed/stale JSON fails visibly
// inside the host element. Uses TodoGraphCore only.

(function () {
  'use strict';

  var host = document.getElementById('tr-todo-graph');
  if (!host) return;

  var core = window.TodoGraphCore;
  if (!core || typeof core.loadGraph !== 'function' || typeof core.buildDot !== 'function') {
    if (host.parentNode) host.parentNode.removeChild(host);
    return;
  }

  var STORAGE_KEY = 'todoGraphEmbed.open';
  var GRAPH_URL = 'issues/_views/dependency-graph.json';

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
      return v === null ? true : v === '1';
    } catch (e) {
      return true;
    }
  }

  function setPersistedOpen(isOpen) {
    try {
      window.localStorage.setItem(STORAGE_KEY, isOpen ? '1' : '0');
    } catch (e) {}
  }

  function showError(message) {
    host.textContent = 'Dependency graph error: ' + message;
    host.setAttribute('data-graph-error', '1');
  }

  function renderGraph(text) {
    var graph;
    try {
      graph = core.loadGraph(text);
    } catch (err) {
      showError(err.message);
      return;
    }
    var built;
    try {
      built = core.buildDot(graph, { taskLabelMaxLen: 50 });
    } catch (err) {
      showError(err.message);
      return;
    }

    return loadScript('tools/vendor/hpcc-js-wasm-graphviz.umd.js').then(function () {
      var hpcc = window['@hpcc-js/wasm/graphviz'];
      if (!hpcc || !hpcc.Graphviz) return;
      return hpcc.Graphviz.load().then(function (gv) {
        var svg = gv.layout(built.dot, 'svg', 'dot');
        var legend =
          '<div style="font-size:.8rem;color:#596274;margin:.4rem 0 .8rem;display:flex;flex-wrap:wrap;gap:0;">' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:3px;border-radius:2px;background:black;"></i>same-feature / start-gate</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:3px;border-radius:2px;background:#1f4e79;"></i>cross-feature / start-gate</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:3px;border-radius:2px;background:crimson;"></i>feature-closure</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:22px;height:0;border-top:2px dashed #6a1b9a;"></i>relation</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;border:1px solid #c7ccd6;background:#ffffff;"></i>open</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#fff3b0;"></i>in_progress</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#ffb3b3;"></i>blocked</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#e8d5ff;"></i>withdrawn [w]</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#d9d9d9;"></i>missing/malformed</span>' +
            '<span style="display:inline-flex;align-items:center;gap:.3rem;margin-right:1.1rem;"><i style="display:inline-block;width:10px;height:10px;background:#ffffff;border:1px solid #808080;"></i><span style="color:#808080;">closed</span></span>' +
          '</div>';
        var wrap = document.createElement('details');
        wrap.className = 'fold';
        wrap.open = getPersistedOpen();
        wrap.innerHTML =
          '<summary><h2 class="sect" style="display:inline">Issue graph (internal)</h2></summary>' +
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

  fetch(GRAPH_URL, { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('graph catalog not available (HTTP ' + res.status + ')');
      return res.text();
    })
    .then(renderGraph)
    .catch(function (err) {
      if (err && err.message && err.message.indexOf('HTTP') !== -1) {
        if (host && host.parentNode) host.parentNode.removeChild(host);
        return;
      }
      if (host && host.getAttribute('data-graph-error') === '1') return;
      if (host && host.parentNode) host.parentNode.removeChild(host);
    });
})();
