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
// Parsing/DOT-building logic is the browser-safe subset of
// tools/todo_dependency_graph.js (kept in sync manually; see that file for
// the canonical, tested implementation and its Node.js CLI/SVG counterpart).

(function () {
  'use strict';

  var host = document.getElementById('tr-todo-graph');
  if (!host) return;

  var FEATURE_RE = /^##\s*Feature:\s*(\d{4})\s*(?:\u2014|--|-)?\s*(.*)$/;
  var TASK_RE = /^-\s*\[([ xup?])\]\s*(?:\*\*)?(\d+-\d+(?:\.\d+)?)(?:\*\*)?\s*(.*)$/;
  var PREREQ_BLOCK_RE = /PREREQ:\s*(.+?)(?:\s*(?:\u2014|--)\s|\s*$)/;
  var PREREQ_ITEM_RE = /(\d{4}(?:-\d+(?:\.\d+)?)?)\s*:\s*(\d{4}(?:-\d+(?:\.\d+)?)?)/g;
  var SOFT_RE = /\(soft\b/i;
  var FEATURE_COLORS = [
    '#cfe8ff', '#d6ecff', '#d9f2d9', '#ffe0cc',
    '#ffd6d6', '#ffe680', '#ffe9cc', '#e6dcff',
    '#c9f7f5', '#f7d9e3', '#e3f7c9', '#d9d9f7',
  ];

  function dotQuote(s) {
    return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
  }

  function truncate(text, maxLen) {
    var cleaned = String(text || '').replace(/\s+/g, ' ').trim();
    if (cleaned.length <= maxLen) return cleaned;
    return cleaned.slice(0, maxLen).replace(/\s+\S*$/, '') + '\u2026';
  }

  function parseTodo(text) {
    var features = new Map();
    var order = [];
    var currentFeature = null;

    text.split(/\r?\n/).forEach(function (rawLine) {
      var line = rawLine.trim();

      var mFeat = FEATURE_RE.exec(line);
      if (mFeat) {
        var fid = mFeat[1];
        var name = (mFeat[2] || '').trim();
        if (!features.has(fid)) {
          features.set(fid, { id: fid, name: name, tasks: [] });
          order.push(fid);
        }
        currentFeature = features.get(fid);
        return;
      }

      var mTask = TASK_RE.exec(line);
      if (mTask && currentFeature) {
        var mark = mTask[1];
        var id = mTask[2];
        var restText = mTask[3] || '';
        var tidFeature = id.split('-', 1)[0];
        var feature = features.get(tidFeature) || currentFeature;
        var task = {
          id: id,
          featureId: feature.id,
          mark: mark,
          text: restText,
          prereqs: [],
          get done() { return this.mark === 'x'; },
        };

        var mBlock = PREREQ_BLOCK_RE.exec(restText);
        if (mBlock) {
          var body = mBlock[1];
          var isSoft = SOFT_RE.test(restText);
          PREREQ_ITEM_RE.lastIndex = 0;
          var mItem;
          while ((mItem = PREREQ_ITEM_RE.exec(body)) !== null) {
            task.prereqs.push([mItem[2], isSoft]);
          }
        }
        feature.tasks.push(task);
      }
    });

    return order.map(function (fid) { return features.get(fid); });
  }

  function featureDone(feature) {
    return feature.tasks.length > 0 && feature.tasks.every(function (t) { return t.done; });
  }

  function classifyEdge(srcTask, dstId) {
    var isSoft = srcTask.prereqs.some(function (p) { return p[0] === dstId && p[1]; });
    var dstIsFeatureOnly = dstId.indexOf('-') === -1;
    var sameFeature = dstId.split('-', 1)[0] === srcTask.featureId;
    if (isSoft) return 'soft_cross';
    if (sameFeature && !dstIsFeatureOnly) return 'explicit_same';
    if (dstIsFeatureOnly) return 'implicit_cross';
    return 'explicit_cross';
  }

  function buildDot(features, includeDone) {
    var liveFeatures = features.filter(function (f) { return includeDone || !featureDone(f); });

    var allTaskIds = new Set();
    liveFeatures.forEach(function (f) {
      f.tasks.forEach(function (t) { if (includeDone || !t.done) allTaskIds.add(t.id); });
    });
    var liveFeatureIds = new Set(liveFeatures.map(function (f) { return f.id; }));

    var lines = [];
    lines.push('digraph todo_dependency_graph {');
    lines.push('  rankdir=LR;');
    lines.push('  splines=true;');
    lines.push('  overlap=false;');
    lines.push('  bgcolor="white";');
    lines.push('  pad="0.3";');
    lines.push('  nodesep="0.25";');
    lines.push('  ranksep="0.8";');
    lines.push('  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize="10", margin="0.08,0.05"];');
    lines.push('  edge [fontname="Helvetica", fontsize="9"];');

    var edges = [];

    liveFeatures.forEach(function (feature, idx) {
      var color = FEATURE_COLORS[idx % FEATURE_COLORS.length];
      var openTasks = feature.tasks.filter(function (t) { return includeDone || !t.done; });
      if (openTasks.length === 0) return;

      lines.push('  subgraph cluster_' + feature.id + ' {');
      var label = feature.name ? feature.id + ' \u2014 ' + feature.name : feature.id;
      lines.push('    label=' + dotQuote(label) + ';');
      lines.push('    style="rounded,filled";');
      lines.push('    color="#777777";');
      lines.push('    fillcolor=' + dotQuote(color) + ';');
      lines.push('    penwidth="1.2";');
      lines.push('    node [fillcolor="white"];');
      lines.push('    ' + dotQuote(feature.id) + ' [label=' + dotQuote(feature.id) + ', shape=tab, fillcolor=' + dotQuote(color) + ', style="filled,bold"];');
      openTasks.forEach(function (t) {
        var taskLabel = t.id + '\n' + truncate(t.text, 50);
        lines.push('    ' + dotQuote(t.id) + ' [label=' + dotQuote(taskLabel) + '];');
      });
      lines.push('  }');

      openTasks.forEach(function (t) {
        t.prereqs.forEach(function (p) {
          var dstId = p[0];
          var dstIsFeatureOnly = dstId.indexOf('-') === -1;
          var targetAlive = allTaskIds.has(dstId) || (dstIsFeatureOnly && liveFeatureIds.has(dstId));
          if (!targetAlive) return;
          edges.push([t.id, dstId, classifyEdge(t, dstId)]);
        });
      });
    });

    var styles = {
      explicit_same: 'color="black", penwidth="1.2"',
      explicit_cross: 'color="#1f4e79", penwidth="1.4"',
      implicit_cross: 'color="crimson", penwidth="1.5"',
      soft_cross: 'color="gray50", penwidth="1.2", style="dashed"',
    };
    edges.forEach(function (e) {
      lines.push('  ' + dotQuote(e[0]) + ' -> ' + dotQuote(e[1]) + ' [' + styles[e[2]] + '];');
    });

    lines.push('}');
    return lines.join('\n') + '\n';
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('failed to load ' + src)); };
      document.body.appendChild(s);
    });
  }

  function renderGraph(text) {
    var features = parseTodo(text);
    if (features.length === 0) return;
    var totalTasks = features.reduce(function (sum, f) { return sum + f.tasks.length; }, 0);
    if (totalTasks === 0) return;

    var dot = buildDot(features, false);

    return loadScript('tools/vendor/hpcc-js-wasm-graphviz.umd.js').then(function () {
      var hpcc = window['@hpcc-js/wasm/graphviz'];
      if (!hpcc || !hpcc.Graphviz) return;
      return hpcc.Graphviz.load().then(function (gv) {
        var svg = gv.layout(dot, 'svg', 'dot');
        var wrap = document.createElement('section');
        wrap.innerHTML =
          '<h2 class="sect">Internal TODO Dependency Graph ' +
          '<span class="ai-badge" title="internal, not part of the API reference">internal</span></h2>' +
          svg;
        var svgEl = wrap.querySelector('svg');
        if (svgEl) {
          svgEl.removeAttribute('width');
          svgEl.removeAttribute('height');
          svgEl.style.width = '100%';
          svgEl.style.height = 'auto';
          svgEl.style.display = 'block';
        }
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
