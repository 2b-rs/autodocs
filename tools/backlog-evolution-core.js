// backlog-evolution-core.js
// Dual-format loader for the backlog 3D evolution visualizer.
// Python twin: _src/tools/backlog_evolution.py

(function (global) {
  'use strict';

  var SCHEMA = 'backlog-evolution@v1';
  var GRAPH_SCHEMA = 'issue-dependency-graph@v1';
  var CATALOG_SCHEMA = 'issue-catalog@v1';
  var FEATURE_RE = /^##\s*Feature:\s*(\d{4})\s*(?:\u2014|--|-)?\s*(.*)$/;
  var TASK_RE = /^-\s*\[([ xup?wd])\]\s*(?:\*\*)?(\d{4}-\d{2}(?:\.\d{2})?)(?:\*\*)?\s*:?\s*(.*)$/i;
  var PREREQ_BLOCK_RE = /PREREQ:\s*(.+?)(?:\s*(?:\u2014|--)\s|\s*$)/;
  var PREREQ_ITEM_RE = /(\d{4}(?:-\d{2}(?:\.\d{2})?)?)\s*:\s*(\d{4}(?:-\d{2}(?:\.\d{2})?)?)/g;
  var SOFT_RE = /\(soft\b/i;
  var ACCEPTANCE_RE = /Acceptance:\s*[✓✔]/;
  var PALETTE = [
    '#38bdf8', '#818cf8', '#c084fc', '#f472b6', '#fb7185',
    '#34d399', '#2dd4bf', '#a78bfa', '#fb923c', '#facc15',
    '#4ade80', '#60a5fa', '#e879f9', '#22d3ee', '#f87171'
  ];

  function EvolutionError(message) {
    var err = new Error(message);
    err.name = 'EvolutionError';
    return err;
  }

  function looksLikeMarkdown(text) {
    var head = String(text).replace(/^\s+/, '').slice(0, 800);
    if (head.indexOf('---') === 0) return true;
    if (head.indexOf('## Feature:') !== -1 || head.indexOf('# ') === 0) return true;
    if (head.indexOf('PREREQ:') !== -1 && head.indexOf('- [') !== -1) return true;
    if (TASK_RE.test(head) || /^-\s*\[[ xup?wd]\]/im.test(head)) return true;
    return false;
  }

  function hasAcceptance(text) {
    return ACCEPTANCE_RE.test(String(text || ''));
  }

  function promoteAcceptedMark(mark, text) {
    mark = String(mark || ' ').toLowerCase();
    if (mark === 'x' && hasAcceptance(text)) return 'a';
    return mark;
  }

  function lifecycleToMark(lifecycleStatus, endpointStatus, title, priorMark) {
    if (endpointStatus === 'missing' || endpointStatus === 'malformed') return '?';
    var status = lifecycleStatus || '';
    if (hasAcceptance(title) || status === 'closed' || status === 'closed:completed') return 'a';
    if (status === 'in_progress') return 'p';
    if (status === 'blocked') return 'u';
    if (status === 'withdrawn') return 'w';
    if (status === 'closed' || status.indexOf('closed:') === 0) return 'x';
    if (status === 'open' && (priorMark === 'x' || priorMark === 'a')) return priorMark;
    if (status === 'open') return ' ';
    return '?';
  }

  function parseTodoMarkdown(text) {
    var features = [];
    var order = [];
    var byId = {};
    var marks = {};
    var current = null;
    String(text).split(/\r?\n/).forEach(function (raw) {
      var line = raw.trim();
      var mFeat = FEATURE_RE.exec(line);
      FEATURE_RE.lastIndex = 0;
      if (mFeat) {
        var fid = mFeat[1];
        var name = (mFeat[2] || '').trim();
        if (!byId[fid]) {
          var feat = { id: fid, name: name, color: PALETTE[order.length % PALETTE.length], tasks: [] };
          byId[fid] = feat;
          order.push(fid);
          features.push(feat);
        } else if (name && !byId[fid].name) {
          byId[fid].name = name;
        }
        current = byId[fid];
        return;
      }
      var mTask = TASK_RE.exec(line);
      TASK_RE.lastIndex = 0;
      if (mTask) {
        var mark = String(mTask[1] || ' ').toLowerCase();
        var tid = mTask[2];
        var rest = (mTask[3] || '').trim();
        if (rest.charAt(0) === ':') rest = rest.slice(1).trim();
        var prefix = tid.split('-')[0];
        var feature = byId[prefix] || current;
        if (!feature) {
          feature = { id: prefix, name: prefix, color: PALETTE[order.length % PALETTE.length], tasks: [] };
          byId[prefix] = feature;
          order.push(prefix);
          features.push(feature);
        }
        var prereqs = [];
        var block = PREREQ_BLOCK_RE.exec(rest);
        PREREQ_BLOCK_RE.lastIndex = 0;
        if (block) {
          var soft = SOFT_RE.test(rest);
          PREREQ_ITEM_RE.lastIndex = 0;
          var item;
          while ((item = PREREQ_ITEM_RE.exec(block[1])) !== null) {
            prereqs.push({ from: tid, to: item[2], soft: soft });
          }
        }
        var task = { id: tid, text: rest, description: '', prereqs: prereqs };
        var existing = feature.tasks.filter(function (t) { return t.id === tid; })[0];
        if (!existing) feature.tasks.push(task);
        else { existing.text = rest; existing.prereqs = prereqs; }
        marks[tid] = promoteAcceptedMark(mark, rest);
        current = feature;
      }
    });
    return { features: features, marks: marks, fids: features.map(function (f) { return f.id; }) };
  }

  function featuresFromCatalog(catalog) {
    var items = catalog.items || [];
    var byId = {};
    var features = [];
    var order = [];
    var marks = {};
    items.forEach(function (item) {
      if (item.level !== 'feature') return;
      var feat = { id: item.id, name: item.title || item.id, color: PALETTE[order.length % PALETTE.length], tasks: [] };
      byId[item.id] = feat;
      order.push(item.id);
      features.push(feat);
    });
    items.forEach(function (item) {
      var mark = lifecycleToMark(item.lifecycle_status, item.endpoint_status, item.title || item.name);
      if (item.level === 'feature') {
        if (item.id) marks[item.id] = mark;
        return;
      }
      if (item.level !== 'task' && item.level !== 'subtask') return;
      var parent = item.parent || String(item.id || '').split('-')[0];
      var feat = byId[parent];
      if (!feat) {
        feat = { id: parent || '_unresolved', name: parent || '_unresolved', color: PALETTE[order.length % PALETTE.length], tasks: [] };
        byId[feat.id] = feat;
        order.push(feat.id);
        features.push(feat);
      }
      feat.tasks.push({
        id: item.id,
        text: item.title || '',
        description: '',
        prereqs: (item.prerequisites || []).filter(Boolean).map(function (target) {
          return { from: item.id, to: target, soft: false };
        })
      });
      marks[item.id] = mark;
    });
    return { features: features, marks: marks, fids: features.map(function (f) { return f.id; }) };
  }

  function featuresFromGraph(graph) {
    var nodes = graph.nodes || [];
    var edges = graph.edges || [];
    var byId = {};
    var features = [];
    var order = [];
    var marks = {};
    nodes.forEach(function (node) {
      if (!node.id) return;
      marks[node.id] = lifecycleToMark(node.lifecycle_status, node.endpoint_status, node.title || node.name);
      if (node.level === 'feature' || (node.level == null && String(node.id).indexOf('-') === -1)) {
        var feat = { id: node.id, name: node.id, color: PALETTE[order.length % PALETTE.length], tasks: [] };
        byId[node.id] = feat;
        order.push(node.id);
        features.push(feat);
      }
    });
    nodes.forEach(function (node) {
      if (!node.id || node.level === 'feature') return;
      var prefix = String(node.id).split('-')[0];
      var feat = byId[prefix];
      if (!feat) {
        feat = { id: prefix, name: prefix, color: PALETTE[order.length % PALETTE.length], tasks: [] };
        byId[prefix] = feat;
        order.push(prefix);
        features.push(feat);
      }
      feat.tasks.push({ id: node.id, text: '', description: '', prereqs: [] });
    });
    var tasksById = {};
    features.forEach(function (f) {
      (f.tasks || []).forEach(function (t) { tasksById[t.id] = t; });
    });
    edges.forEach(function (edge) {
      var task = tasksById[edge.source];
      if (!task) return;
      task.prereqs.push({ from: edge.source, to: edge.target, soft: false });
    });
    return { features: features, marks: marks, fids: features.map(function (f) { return f.id; }) };
  }

  function assemble(timeline, features, source) {
    var numbered = (timeline || []).map(function (snap, idx) {
      var item = {};
      Object.keys(snap).forEach(function (k) { item[k] = snap[k]; });
      item.idx = idx;
      return item;
    });
    return {
      schema: SCHEMA,
      authority: 'generated-view',
      features: features || [],
      timeline: numbered,
      task_history: {},
      source: source || {}
    };
  }

  function snapshotFromParsed(parsed, hash, msg) {
    return {
      idx: 0,
      hash: hash,
      date: '',
      msg: msg,
      fids: parsed.fids,
      marks: parsed.marks,
      changes: parsed.features.map(function (f) {
        return { type: 'feat_add', fid: f.id, name: f.name };
      })
    };
  }

  function normalize(document) {
    if (!document || typeof document !== 'object' || Array.isArray(document)) {
      throw EvolutionError('evolution document must be a JSON object');
    }
    if (document.schema === SCHEMA) {
      if (!Array.isArray(document.features) || !Array.isArray(document.timeline)) {
        throw EvolutionError('backlog-evolution@v1 requires features and timeline arrays');
      }
      return {
        schema: SCHEMA,
        authority: document.authority || 'generated-view',
        features: document.features,
        timeline: document.timeline,
        task_history: document.task_history || {},
        source: document.source || {}
      };
    }
    if (document.FEATURES || document.features) {
      return {
        schema: SCHEMA,
        authority: 'legacy-baked',
        features: document.FEATURES || document.features || [],
        timeline: document.TIMELINE || document.timeline || [],
        task_history: document.TASK_HISTORY || document.task_history || {},
        source: { format: 'legacy-baked' }
      };
    }
    if (document.schema === CATALOG_SCHEMA) {
      var fromCat = featuresFromCatalog(document);
      return assemble([snapshotFromParsed(fromCat, 'issue-store', 'issue-store catalog')], fromCat.features, { format: 'issue-catalog@v1' });
    }
    if (document.schema === GRAPH_SCHEMA) {
      var fromGraph = featuresFromGraph(document);
      return assemble([snapshotFromParsed(fromGraph, 'issue-graph', 'issue-dependency-graph')], fromGraph.features, { format: GRAPH_SCHEMA });
    }
    throw EvolutionError('unsupported evolution document schema');
  }

  function load(text) {
    if (typeof text !== 'string') throw EvolutionError('evolution input must be text');
    if (looksLikeMarkdown(text)) {
      var parsed = parseTodoMarkdown(text);
      return assemble([snapshotFromParsed(parsed, 'todo.md', 'TODO.md')], parsed.features, { format: 'todo.md' });
    }
    var document;
    try {
      document = JSON.parse(text);
    } catch (exc) {
      throw EvolutionError('malformed evolution JSON: ' + exc.message);
    }
    return normalize(document);
  }

  function fetchText(url) {
    return fetch(url, { cache: 'no-store' }).then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status + ' ' + url);
      return res.text();
    });
  }

  function loadFromUrls(urls) {
    var list = urls || [
      '../issues/_views/backlog-evolution.json',
      '../issues/_views/catalog.json',
      '../issues/_views/dependency-graph.json',
      '../TODO.md'
    ];
    var errors = [];
    function next(i) {
      if (i >= list.length) {
        return Promise.reject(EvolutionError(
          'no readable backlog-evolution source (' + errors.join('; ') + ')'
        ));
      }
      return fetchText(list[i]).then(function (text) {
        return load(text);
      }).catch(function (err) {
        errors.push(String(err && err.message ? err.message : err));
        return next(i + 1);
      });
    }
    return next(0);
  }

  var api = {
    SCHEMA: SCHEMA,
    load: load,
    loadFromUrls: loadFromUrls,
    parseTodoMarkdown: parseTodoMarkdown,
    lifecycleToMark: lifecycleToMark,
    featuresFromCatalog: featuresFromCatalog,
    featuresFromGraph: featuresFromGraph,
    normalize: normalize
  };

  global.BacklogEvolutionCore = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof window !== 'undefined' ? window : globalThis);
