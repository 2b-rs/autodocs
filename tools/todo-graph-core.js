// todo-graph-core.js
//
// Single, canonical browser-safe implementation of the TODO.md parser and
// Graphviz DOT builder used by both browser consumers:
//   - tools/todo-dependency-graph.html (standalone maintainer tool)
//   - tools/todo-graph-embed.js (live embed on the published start page)
//
// This replaces two previously independent, manually-"kept in sync" copies
// of the same ~150 lines of logic for the active browser consumers (2026-08-13).
// The live embed was migrated immediately; the standalone maintainer page was
// later re-pointed at this module on 2026-08-14 after a drift bug was traced
// to its stale inline copy. The formerly separate Node.js CLI
// (tools/todo_dependency_graph.js) and Python CLI (tools/todo_dependency_
// graph.py) twins were removed the same day (not used for static artifact
// generation); this browser module is now the sole implementation.
//
// Exposes a single global: window.TodoGraphCore = { parseTodo, buildDot,
// dotQuote, truncate, FEATURE_COLORS, MARK_COLORS, DONE_FONT_COLOR,
// DONE_EDGE_COLOR }.

(function (global) {
  'use strict';

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

  // See TODO.md's "HOW TO USE" section for the authoritative meaning of each
  // marker: ' '=open, 'p'=partial (agent-workable, in progress), 'u'=unclear
  // (blocked on human/manager discussion), '?'=unknown, 'x'=done.
  var MARK_COLORS = {
    ' ': '#ffffff',
    'p': '#fff3b0',
    'u': '#ffb3b3',
    '?': '#d9d9d9',
    'x': '#b6e3b6',
  };
  // 'x' (done) is rendered unfilled with this font color instead of using
  // MARK_COLORS.x as a fill — finished tasks recede visually but stay legible.
  var DONE_FONT_COLOR = '#808080';
  // Edges originating FROM a done task render in this light grey instead of
  // their normal classification color (re-added 2026-08-14; was dropped
  // during the 2026-08-13 revert/squash that produced 73f27778 despite that
  // commit's message still claiming it was present). Edges merely pointing
  // AT a done task are unaffected and keep their normal classification.
  var DONE_EDGE_COLOR = '#d9d9d9';

  function htmlEscape(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // Builds an HTML-like Graphviz label: task text on the left, a
  // right-aligned checkmark glyph in its own cell, wrapped in a
  // rounded table filled with the enclosing feature's color so done
  // tasks still read as part of that feature. The grey text/checkmark
  // is now the only visual distinction from non-done tasks.
  // multiLineLabel may contain '\n' (id + wrapped task text).
  function htmlDoneLabel(multiLineLabel, featureColor) {
    var textHtml = multiLineLabel.split('\n').map(htmlEscape).join('<BR/>');
    return '<' +
      '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" STYLE="ROUNDED" COLOR="#808080" BGCOLOR="' + featureColor + '">' +
      '<TR>' +
      '<TD ALIGN="LEFT"><FONT COLOR="' + DONE_FONT_COLOR + '">' + textHtml + '</FONT></TD>' +
      '<TD ALIGN="RIGHT" VALIGN="MIDDLE"><FONT COLOR="' + DONE_FONT_COLOR + '">&#10003;</FONT></TD>' +
      '</TR>' +
      '</TABLE>' +
      '>';
  }
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

  // opts: { taskLabelMaxLen: number|null }
  // All features and tasks are always rendered (no done-item filtering);
  // finished features are expected to have been moved to DONE.md already.
  // taskLabelMaxLen: if set, node labels are "<id>\n<truncated text>" (used by
  // the embed, which has limited horizontal space); if omitted/null, node
  // labels are just "<id>" (used by the standalone tool, which renders a
  // large canvas and lets the user zoom/scroll).
  function buildDot(features, opts) {
    opts = opts || {};
    var taskLabelMaxLen = opts.taskLabelMaxLen || null;

    // No filtering: every feature and task is rendered. Fully-finished
    // features are expected to already have been moved out to DONE.md by
    // convention, and finished tasks inside still-open features must stay
    // visible (they carry their own [x] styling via MARK_COLORS).
    var liveFeatures = features;

    var allTaskIds = new Set();
    liveFeatures.forEach(function (f) {
      f.tasks.forEach(function (t) { allTaskIds.add(t.id); });
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
      var openTasks = feature.tasks;
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
        var taskLabel = taskLabelMaxLen ? (t.id + '\n' + truncate(t.text, taskLabelMaxLen)) : t.id;
        if (t.mark === 'x') {
          // Done: rounded box filled with the feature's color, grey text,
          // plus a right-aligned checkmark glyph. HTML-like labels are
          // required to place the checkmark in its own cell instead of
          // inline with the text.
          var htmlLabel = htmlDoneLabel(taskLabel, color);
          lines.push('    ' + dotQuote(t.id) + ' [shape="none", margin="0", label=' + htmlLabel + '];');
        } else {
          var fill = MARK_COLORS[t.mark] || '#ffffff';
          lines.push('    ' + dotQuote(t.id) + ' [label=' + dotQuote(taskLabel) + ', fillcolor=' + dotQuote(fill) + '];');
        }
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
    var taskById = new Map();
    liveFeatures.forEach(function (f) {
      f.tasks.forEach(function (t) { taskById.set(t.id, t); });
    });
    edges.forEach(function (e) {
      var srcTask = taskById.get(e[0]);
      var style = (srcTask && srcTask.mark === 'x')
        ? 'color=' + dotQuote(DONE_EDGE_COLOR) + ', penwidth="1.2"'
        : styles[e[2]];
      lines.push('  ' + dotQuote(e[0]) + ' -> ' + dotQuote(e[1]) + ' [' + style + '];');
    });

    lines.push('}');

    return {
      dot: lines.join('\n') + '\n',
      nodeCount: allTaskIds.size,
      edgeCount: edges.length,
      liveFeatureCount: liveFeatures.length,
    };
  }

  global.TodoGraphCore = {
    parseTodo: parseTodo,
    buildDot: buildDot,
    dotQuote: dotQuote,
    truncate: truncate,
    featureDone: featureDone,
    FEATURE_COLORS: FEATURE_COLORS,
    MARK_COLORS: MARK_COLORS,
    DONE_FONT_COLOR: DONE_FONT_COLOR,
    DONE_EDGE_COLOR: DONE_EDGE_COLOR,
  };
})(window);
