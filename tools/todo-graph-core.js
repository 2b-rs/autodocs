// todo-graph-core.js
//
// Canonical browser-safe adapter for issue-dependency-graph@v1 JSON.
// Consumers: tools/todo-dependency-graph.html and tools/todo-graph-embed.js.
// Python twin: _src/tools/todo_graph_adapter.py (byte-compared in tests).
// Never parses YAML, Markdown, TODO.md, or DONE.md.

(function (global) {
  'use strict';

  var SCHEMA = 'issue-dependency-graph@v1';
  var AUTHORITY = 'generated-view';
  var REQUIRED_TOP = ['schema', 'authority', 'nodes', 'edges', 'digests', 'generation_id'];
  var REQUIRED_NODE = ['id', 'level', 'lifecycle_status', 'endpoint_status'];
  var REQUIRED_EDGE = ['source', 'target', 'kind', 'endpoint_status'];
  var ENDPOINT_OK = { present: 1, missing: 1, malformed: 1 };

  var FEATURE_COLORS = [
    '#cfe8ff', '#d6ecff', '#d9f2d9', '#ffe0cc',
    '#ffd6d6', '#ffe680', '#ffe9cc', '#e6dcff',
    '#c9f7f5', '#f7d9e3', '#e3f7c9', '#d9d9f7',
  ];
  var MARK_COLORS = {
    ' ': '#ffffff',
    'p': '#fff3b0',
    'u': '#ffb3b3',
    'w': '#e8d5ff',
    '?': '#d9d9d9',
    'x': '#b6e3b6',
  };
  var DONE_FONT_COLOR = '#808080';
  var DONE_EDGE_COLOR = '#d9d9d9';

  function GraphAdapterError(message) {
    var err = new Error(message);
    err.name = 'GraphAdapterError';
    return err;
  }

  function htmlEscape(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

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
    var trimmed = cleaned.slice(0, maxLen).replace(/\s+\S*$/, '');
    return trimmed + '\u2026';
  }

  function looksLikeMarkdown(text) {
    var head = String(text).replace(/^\s+/, '').slice(0, 800);
    if (head.indexOf('---') === 0) return true;
    if (head.indexOf('## Feature:') !== -1 || head.indexOf('# ') === 0) return true;
    if (head.indexOf('PREREQ:') !== -1 && head.indexOf('- [') !== -1) return true;
    return false;
  }

  function lifecycleToMark(lifecycleStatus, endpointStatus) {
    if (endpointStatus === 'missing' || endpointStatus === 'malformed') return '?';
    var status = lifecycleStatus || '';
    if (status === 'open') return ' ';
    if (status === 'in_progress') return 'p';
    if (status === 'blocked') return 'u';
    if (status === 'withdrawn') return 'w';
    if (status === 'closed' || status.indexOf('closed:') === 0) return 'x';
    return '?';
  }

  function featurePrefix(itemId) {
    var text = String(itemId || '');
    if (text.indexOf('-') === -1) {
      return (text.length === 4 && /^\d{4}$/.test(text)) ? text : '_unresolved';
    }
    return text.split('-')[0];
  }

  function classifyEdge(sourceId, targetId, gate, kind) {
    if (gate === 'feature-closure') return 'feature_closure';
    if (kind && kind !== 'prerequisite') return 'relation';
    var srcF = featurePrefix(sourceId);
    var dstF = featurePrefix(targetId);
    var dstIsFeature = String(targetId).indexOf('-') === -1;
    if (srcF === dstF && !dstIsFeature) return 'explicit_same';
    if (dstIsFeature) return 'feature_closure';
    return 'explicit_cross';
  }

  function validateGraph(document) {
    if (!document || typeof document !== 'object' || Array.isArray(document)) {
      throw GraphAdapterError('graph document must be a JSON object');
    }
    var allowed = { schema: 1, authority: 1, nodes: 1, edges: 1, digests: 1, generation_id: 1 };
    Object.keys(document).forEach(function (key) {
      if (!allowed[key]) throw GraphAdapterError('unknown graph fields: ' + key);
    });
    REQUIRED_TOP.forEach(function (key) {
      if (!(key in document)) throw GraphAdapterError('missing required field ' + key);
    });
    if (document.schema !== SCHEMA) {
      throw GraphAdapterError('unsupported schema ' + JSON.stringify(document.schema) + '; expected ' + SCHEMA);
    }
    if (document.authority !== AUTHORITY) {
      throw GraphAdapterError('authority ' + JSON.stringify(document.authority) + ' is not ' + AUTHORITY);
    }
    var gen = document.generation_id;
    if (typeof gen !== 'string' || gen.indexOf('sha256:') !== 0 || gen.length !== 71) {
      throw GraphAdapterError('malformed or missing generation_id');
    }
    var nodes = document.nodes;
    var edges = document.edges;
    if (!Array.isArray(nodes) || !Array.isArray(edges)) {
      throw GraphAdapterError('nodes and edges must be arrays');
    }
    var seen = Object.create(null);
    nodes.forEach(function (node, index) {
      if (!node || typeof node !== 'object') throw GraphAdapterError('node[' + index + '] is not an object');
      REQUIRED_NODE.forEach(function (key) {
        if (!(key in node)) throw GraphAdapterError('node[' + index + '] missing ' + key);
      });
      if (seen[node.id]) throw GraphAdapterError('duplicate node id ' + JSON.stringify(node.id));
      seen[node.id] = node;
      if (!ENDPOINT_OK[node.endpoint_status]) {
        throw GraphAdapterError('node ' + JSON.stringify(node.id) + ' bad endpoint_status ' + JSON.stringify(node.endpoint_status));
      }
    });
    edges.forEach(function (edge, index) {
      if (!edge || typeof edge !== 'object') throw GraphAdapterError('edge[' + index + '] is not an object');
      REQUIRED_EDGE.forEach(function (key) {
        if (!(key in edge)) throw GraphAdapterError('edge[' + index + '] missing ' + key);
      });
      if (!ENDPOINT_OK[edge.endpoint_status]) {
        throw GraphAdapterError('edge[' + index + '] bad endpoint_status ' + JSON.stringify(edge.endpoint_status));
      }
      if (edge.endpoint_status !== 'present' && !seen[edge.target]) {
        throw GraphAdapterError(
          'unresolved edge target ' + JSON.stringify(edge.target) +
          ' missing from nodes (silently dropped endpoints are forbidden)');
      }
      if (!seen[edge.source]) {
        throw GraphAdapterError('edge source ' + JSON.stringify(edge.source) + ' missing from nodes');
      }
    });
    return document;
  }

  function loadGraph(text) {
    if (typeof text !== 'string') throw GraphAdapterError('graph input must be text');
    if (looksLikeMarkdown(text)) {
      throw GraphAdapterError(
        'refused Markdown/TODO.md/DONE.md/YAML input; load issues/_views/dependency-graph.json');
    }
    var document;
    try {
      document = JSON.parse(text);
    } catch (exc) {
      throw GraphAdapterError('malformed graph JSON: ' + exc.message);
    }
    return validateGraph(document);
  }

  function nodeLabel(node, taskLabelMaxLen) {
    var status = node.endpoint_status || 'present';
    var mark = lifecycleToMark(node.lifecycle_status, status);
    var title = node.id;
    var extra = [];
    if (status === 'missing') extra.push('missing');
    else if (status === 'malformed') extra.push('malformed');
    if (node.archive_status) extra.push(String(node.archive_status));
    if (node.lifecycle_status === 'withdrawn' || mark === 'w') extra.push('[w]');
    var suffix = extra.length ? (' ' + extra.join(' ')) : '';
    if (taskLabelMaxLen) {
      var body = truncate(node.lifecycle_status || '', taskLabelMaxLen);
      return title + suffix + '\n' + body;
    }
    return title + suffix;
  }

  function buildDot(graph, opts) {
    opts = opts || {};
    var taskLabelMaxLen = opts.taskLabelMaxLen || null;
    var includeClosed = opts.includeClosed !== false;
    var includeWithdrawn = opts.includeWithdrawn !== false;
    var includeUnresolved = opts.includeUnresolved !== false;

    var nodes = graph.nodes.slice();
    var edges = graph.edges.slice();

    function isVisible(node) {
      var mark = lifecycleToMark(node.lifecycle_status, node.endpoint_status);
      var ep = node.endpoint_status;
      if ((ep === 'missing' || ep === 'malformed') && !includeUnresolved) return false;
      if (mark === 'x' && !includeClosed) return false;
      if (mark === 'w' && !includeWithdrawn) return false;
      return true;
    }

    var visibleIds = {};
    nodes.forEach(function (n) { if (isVisible(n)) visibleIds[n.id] = true; });
    if (includeUnresolved) {
      var hiddenRequired = [];
      edges.forEach(function (edge) {
        if (edge.endpoint_status !== 'present' && !visibleIds[edge.target]) {
          hiddenRequired.push(edge.target);
        }
      });
      if (hiddenRequired.length) {
        throw GraphAdapterError('unresolved endpoints would be dropped by filter: ' + hiddenRequired.sort().join(','));
      }
    }

    var featureIds = [];
    var clusters = {};
    nodes.slice().sort(function (a, b) { return String(a.id) < String(b.id) ? -1 : (String(a.id) > String(b.id) ? 1 : 0); })
      .forEach(function (node) {
        if (!visibleIds[node.id]) return;
        var fid;
        if (node.level === 'feature' || (
          node.level == null && String(node.id).indexOf('-') === -1 &&
          /^\d{4}$/.test(String(node.id)))) {
          fid = node.id;
        } else {
          fid = featurePrefix(node.id);
          if (node.level == null && fid === '_unresolved') fid = '_unresolved';
        }
        if (!clusters[fid]) {
          clusters[fid] = [];
          featureIds.push(fid);
        }
        clusters[fid].push(node);
      });

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

    var nodeById = {};
    nodes.forEach(function (n) { nodeById[n.id] = n; });
    var renderedNodes = 0;

    featureIds.forEach(function (fid, idx) {
      var members = clusters[fid];
      if (!members || !members.length) return;
      var color = FEATURE_COLORS[idx % FEATURE_COLORS.length];
      var clusterName = fid === '_unresolved' ? 'unresolved' : fid;
      var label = fid === '_unresolved' ? 'unresolved endpoints' : fid;
      lines.push('  subgraph cluster_' + clusterName + ' {');
      lines.push('    label=' + dotQuote(label) + ';');
      lines.push('    style="rounded,filled";');
      lines.push('    color="#777777";');
      lines.push('    fillcolor=' + dotQuote(color) + ';');
      lines.push('    penwidth="1.2";');
      lines.push('    node [fillcolor="white"];');
      members.forEach(function (node) {
        var nid = node.id;
        var mark = lifecycleToMark(node.lifecycle_status, node.endpoint_status);
        var labelText = nodeLabel(node, taskLabelMaxLen);
        var urlAttr = node.url ? (', URL=' + dotQuote(node.url)) : '';
        if (node.level === 'feature' && node.endpoint_status === 'present') {
          var featLabel = node.archive_status ? labelText : nid;
          lines.push('    ' + dotQuote(nid) + ' [label=' + dotQuote(featLabel) + ', shape=tab, fillcolor=' +
            dotQuote(color) + ', style="filled,bold"' + urlAttr + '];');
        } else if (mark === 'x' && node.endpoint_status === 'present') {
          var htmlLabel = htmlDoneLabel(labelText, color);
          lines.push('    ' + dotQuote(nid) + ' [shape="none", margin="0", label=' + htmlLabel + urlAttr + '];');
        } else {
          var fill = MARK_COLORS[mark] || '#ffffff';
          var extra = '';
          if (node.endpoint_status === 'missing') extra = ', style="dashed,filled", color="#b3261e"';
          else if (node.endpoint_status === 'malformed') extra = ', style="dashed,filled", color="#e65100"';
          lines.push('    ' + dotQuote(nid) + ' [label=' + dotQuote(labelText) + ', fillcolor=' +
            dotQuote(fill) + extra + urlAttr + '];');
        }
        renderedNodes += 1;
      });
      lines.push('  }');
    });

    var styles = {
      explicit_same: 'color="black", penwidth="1.2"',
      explicit_cross: 'color="#1f4e79", penwidth="1.4"',
      feature_closure: 'color="crimson", penwidth="1.5"',
      relation: 'color="#6a1b9a", penwidth="1.3", style="dashed"',
    };
    var drawn = 0;
    var unresolvedEdges = 0;
    edges.slice().sort(function (a, b) {
      var ka = a.source + '\0' + a.kind + '\0' + a.target;
      var kb = b.source + '\0' + b.kind + '\0' + b.target;
      return ka < kb ? -1 : (ka > kb ? 1 : 0);
    }).forEach(function (edge) {
      if (!visibleIds[edge.source] || !visibleIds[edge.target]) {
        if (includeUnresolved && edge.endpoint_status !== 'present') {
          throw GraphAdapterError('would drop unresolved edge ' + edge.source + '->' + edge.target);
        }
        return;
      }
      var src = nodeById[edge.source];
      var srcMark = lifecycleToMark(src.lifecycle_status, src.endpoint_status);
      var klass = classifyEdge(edge.source, edge.target, edge.gate, edge.kind);
      var style = (srcMark === 'x')
        ? ('color=' + dotQuote(DONE_EDGE_COLOR) + ', penwidth="1.2"')
        : styles[klass];
      if (edge.endpoint_status === 'missing') style += ', style="dotted"';
      else if (edge.endpoint_status === 'malformed') style += ', style="dashed", color="#e65100"';
      if (edge.gate) style += ', edgetooltip=' + dotQuote(edge.gate);
      lines.push('  ' + dotQuote(edge.source) + ' -> ' + dotQuote(edge.target) + ' [' + style + '];');
      drawn += 1;
      if (edge.endpoint_status !== 'present') unresolvedEdges += 1;
    });

    lines.push('}');
    var unresolvedNodeCount = 0;
    nodes.forEach(function (n) {
      if ((n.endpoint_status === 'missing' || n.endpoint_status === 'malformed') && visibleIds[n.id]) {
        unresolvedNodeCount += 1;
      }
    });
    return {
      dot: lines.join('\n') + '\n',
      nodeCount: renderedNodes,
      edgeCount: drawn,
      liveFeatureCount: featureIds.length,
      unresolvedEdgeCount: unresolvedEdges,
      unresolvedNodeCount: unresolvedNodeCount,
    };
  }

  function counts(graph) {
    var nodes = graph.nodes;
    var edges = graph.edges;
    function ncount(pred) {
      var c = 0;
      nodes.forEach(function (n) { if (pred(n)) c += 1; });
      return c;
    }
    function ecount(pred) {
      var c = 0;
      edges.forEach(function (e) { if (pred(e)) c += 1; });
      return c;
    }
    return {
      nodes: nodes.length,
      edges: edges.length,
      features: ncount(function (n) { return n.level === 'feature'; }),
      tasks: ncount(function (n) { return n.level === 'task'; }),
      subtasks: ncount(function (n) { return n.level === 'subtask'; }),
      withdrawn: ncount(function (n) {
        return lifecycleToMark(n.lifecycle_status, n.endpoint_status) === 'w';
      }),
      missing_nodes: ncount(function (n) { return n.endpoint_status === 'missing'; }),
      malformed_nodes: ncount(function (n) { return n.endpoint_status === 'malformed'; }),
      start_gate_edges: ecount(function (e) { return e.gate === 'start-gate'; }),
      feature_closure_edges: ecount(function (e) { return e.gate === 'feature-closure'; }),
      unresolved_edges: ecount(function (e) { return e.endpoint_status !== 'present'; }),
    };
  }

  var api = {
    loadGraph: loadGraph,
    validateGraph: validateGraph,
    buildDot: buildDot,
    counts: counts,
    lifecycleToMark: lifecycleToMark,
    classifyEdge: classifyEdge,
    dotQuote: dotQuote,
    truncate: truncate,
    FEATURE_COLORS: FEATURE_COLORS,
    MARK_COLORS: MARK_COLORS,
    DONE_FONT_COLOR: DONE_FONT_COLOR,
    DONE_EDGE_COLOR: DONE_EDGE_COLOR,
  };

  global.TodoGraphCore = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof window !== 'undefined' ? window : globalThis);
