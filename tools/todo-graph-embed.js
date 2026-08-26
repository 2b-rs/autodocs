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
  var UI_URL = '_src/i18n/ui.json';
  var ui;

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
    host.textContent = ((ui && ui.strings.error) || '') + ': ' + message;
    host.setAttribute('data-graph-error', '1');
    if (ui) host.setAttribute('lang', ui.language);
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
        var s = ui.strings;
        var legend =
          '<div style="font-size:.8rem;color:#596274;margin:.4rem 0 .8rem;display:flex;flex-wrap:wrap;gap:0;">' +
            '<span data-graph-ui="legend_explicit_same">' + s.legend_explicit_same + '</span>' +
            '<span data-graph-ui="legend_explicit_cross">' + s.legend_explicit_cross + '</span>' +
            '<span data-graph-ui="legend_feature_closure">' + s.legend_feature_closure + '</span>' +
            '<span data-graph-ui="legend_relation">' + s.legend_relation + '</span>' +
            '<span data-graph-ui="state_open">' + s.state_open + '</span>' +
            '<span data-graph-ui="state_in_progress">' + s.state_in_progress + '</span>' +
            '<span data-graph-ui="state_blocked">' + s.state_blocked + '</span>' +
            '<span data-graph-ui="state_withdrawn">' + s.state_withdrawn + '</span>' +
            '<span data-graph-ui="state_missing_malformed">' + s.state_missing_malformed + '</span>' +
            '<span data-graph-ui="state_closed">' + s.state_closed + '</span>' +
          '</div>';
        var wrap = document.createElement('details');
        wrap.className = 'fold';
        wrap.open = getPersistedOpen();
        wrap.innerHTML =
          '<summary><h2 class="sect" style="display:inline">' + s.title + '</h2></summary>' +
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
        wrap.setAttribute('lang', ui.language);
        if (ui.fallback) wrap.setAttribute('data-i18n-fallback', 'canonical-en');
      });
    });
  }

  Promise.all([
    fetch(GRAPH_URL, { cache: 'no-store' }),
    fetch(UI_URL, { cache: 'no-store' })
  ])
    .then(function (responses) {
      if (!responses[0].ok) throw new Error('graph catalog HTTP ' + responses[0].status);
      if (!responses[1].ok) throw new Error('graph UI HTTP ' + responses[1].status);
      return Promise.all([responses[0].text(), responses[1].json()]);
    })
    .then(function (values) {
      var language = (document.documentElement.getAttribute('lang') || 'en').split('-')[0];
      ui = core.graphUi(values[1], language, true);
      return renderGraph(values[0]);
    })
    .catch(function (err) {
      if (err && err.message && err.message.indexOf('HTTP') !== -1) {
        if (host && host.parentNode) host.parentNode.removeChild(host);
        return;
      }
      if (host && host.getAttribute('data-graph-error') === '1') return;
      if (host && host.parentNode) host.parentNode.removeChild(host);
    });
})();
