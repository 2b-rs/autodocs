#!/usr/bin/env node
'use strict';
/**
 * todo_dependency_graph.js
 *
 * Node.js (pure stdlib, no npm dependencies) port of
 * tools/todo_dependency_graph.py.
 *
 * Parses a TODO.md following the Feature/Task/Subtask ID scheme:
 *
 *   ## Feature: XXXX — <name>
 *   - [ ] **XXXX-YY** ... PREREQ: A(-B)?:C(-D)?[, A(-B)?:C(-D)?...] ... text
 *   - [x] **XXXX-YY.ZZ** ... (subtask, done)
 *
 * and renders a Graphviz dependency graph where each Feature is drawn as a
 * cluster ("box") containing its open (non-"[x]") Tasks/Subtasks as nodes.
 * Finished tasks and fully-finished features are excluded by default.
 *
 * No third-party npm packages are required. The script emits raw DOT text
 * itself and — unless --dot-text-only is given — shells out to the Graphviz
 * `dot` binary to render PNG and/or SVG output directly (SVG needs no
 * external viewer and can be embedded inline in HTML).
 *
 * Edge color/style convention (same as the Python version):
 *   black        same-feature dependency        (XXXX-YY -> XXXX-ZZ)
 *   blue         cross-feature, task-level       (XXXX-YY -> AAAA-BB)
 *   crimson      cross-feature, feature-level    (XXXX-YY -> AAAA, or XXXX -> AAAA)
 *   dashed gray  prerequisite marked "(soft ...)" in the task text
 *
 * Usage:
 *   node todo_dependency_graph.js [--input TODO.md] [--output graph]
 *                                 [--format svg|png|both] [--include-done]
 *                                 [--dot-binary /path/to/dot] [--dot-text-only]
 *
 * Exit codes:
 *   0  success
 *   1  input file not found / unreadable
 *   2  no features or no tasks discovered (nothing to draw)
 *   3  Graphviz `dot` binary not found
 *   4  Graphviz `dot` binary exited with a non-zero status
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const FEATURE_RE = /^##\s*Feature:\s*(\d{4})\s*(?:—|--|-)?\s*(.*)$/;
const TASK_RE = /^-\s*\[([ xup?])\]\s*(?:\*\*)?(\d+-\d+(?:\.\d+)?)(?:\*\*)?\s*(.*)$/;
const PREREQ_BLOCK_RE = /PREREQ:\s*(.+?)(?:\s*(?:—|--)\s|\s*$)/;
const PREREQ_ITEM_RE = /(\d{4}(?:-\d+(?:\.\d+)?)?)\s*:\s*(\d{4}(?:-\d+(?:\.\d+)?)?)/g;
const SOFT_RE = /\(soft\b/i;

const FEATURE_COLORS = [
  '#cfe8ff', '#d6ecff', '#d9f2d9', '#ffe0cc',
  '#ffd6d6', '#ffe680', '#ffe9cc', '#e6dcff',
  '#c9f7f5', '#f7d9e3', '#e3f7c9', '#d9d9f7',
];

function dotQuote(s) {
  return '"' + String(s).replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
}

class Task {
  constructor(id, featureId, mark, text) {
    this.id = id;
    this.featureId = featureId;
    this.mark = mark;
    this.text = text;
    this.prereqs = []; // [ [targetId, isSoft], ... ]
  }
  get done() {
    return this.mark === 'x';
  }
}

class Feature {
  constructor(id, name) {
    this.id = id;
    this.name = name;
    this.tasks = [];
  }
  get done() {
    return this.tasks.length > 0 && this.tasks.every((t) => t.done);
  }
}

/**
 * Parse TODO.md content into an ordered array of Feature instances.
 * @param {string} text raw file content
 * @returns {Feature[]}
 */
function parseTodo(text) {
  const features = new Map();
  const order = [];
  let currentFeature = null;

  const lines = text.split(/\r?\n/);
  for (const rawLine of lines) {
    const line = rawLine.trim();

    const mFeat = FEATURE_RE.exec(line);
    if (mFeat) {
      const fid = mFeat[1];
      const name = (mFeat[2] || '').trim();
      if (!features.has(fid)) {
        features.set(fid, new Feature(fid, name));
        order.push(fid);
      }
      currentFeature = features.get(fid);
      continue;
    }

    const mTask = TASK_RE.exec(line);
    if (mTask && currentFeature) {
      const tid = mTask[1] === undefined ? null : mTask[2]; // guard, unused
      const mark = mTask[1];
      const id = mTask[2];
      const restText = mTask[3] || '';

      const tidFeature = id.split('-', 1)[0];
      const feature = features.get(tidFeature) || currentFeature;

      const task = new Task(id, feature.id, mark, restText);

      const mBlock = PREREQ_BLOCK_RE.exec(restText);
      if (mBlock) {
        const body = mBlock[1];
        const isSoft = SOFT_RE.test(restText);
        let mItem;
        PREREQ_ITEM_RE.lastIndex = 0;
        while ((mItem = PREREQ_ITEM_RE.exec(body)) !== null) {
          const dst = mItem[2];
          task.prereqs.push([dst, isSoft]);
        }
      }

      feature.tasks.push(task);
    }
  }

  return order.map((fid) => features.get(fid));
}

/**
 * Classify a dependency edge's DOT styling category.
 * @param {Task} srcTask
 * @param {string} dstId
 * @returns {'explicit_same'|'explicit_cross'|'implicit_cross'|'soft_cross'}
 */
function classifyEdge(srcTask, dstId) {
  const isSoft = srcTask.prereqs.some(([dst, soft]) => dst === dstId && soft);
  const dstIsFeatureOnly = !dstId.includes('-');
  const sameFeature = dstId.split('-', 1)[0] === srcTask.featureId;

  if (isSoft) return 'soft_cross';
  if (sameFeature && !dstIsFeatureOnly) return 'explicit_same';
  if (dstIsFeatureOnly) return 'implicit_cross';
  return 'explicit_cross';
}

/**
 * Build DOT source text for the (filtered) dependency graph.
 * @param {Feature[]} features
 * @param {boolean} includeDone
 * @returns {{dot: string, nodeCount: number, edgeCount: number, liveFeatureCount: number}}
 */
function buildDot(features, includeDone) {
  const liveFeatures = features.filter((f) => includeDone || !f.done);

  const allTaskIds = new Set();
  for (const f of liveFeatures) {
    for (const t of f.tasks) {
      if (includeDone || !t.done) allTaskIds.add(t.id);
    }
  }
  const liveFeatureIds = new Set(liveFeatures.map((f) => f.id));

  const lines = [];
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

  const edges = []; // [src, dst, kind]

  liveFeatures.forEach((feature, idx) => {
    const color = FEATURE_COLORS[idx % FEATURE_COLORS.length];
    const openTasks = feature.tasks.filter((t) => includeDone || !t.done);
    if (openTasks.length === 0) return;

    lines.push(`  subgraph cluster_${feature.id} {`);
    const label = feature.name ? `${feature.id} — ${feature.name}` : feature.id;
    lines.push(`    label=${dotQuote(label)};`);
    lines.push('    style="rounded,filled";');
    lines.push('    color="#777777";');
    lines.push(`    fillcolor=${dotQuote(color)};`);
    lines.push('    penwidth="1.2";');
    lines.push('    node [fillcolor="white"];');
    lines.push(`    ${dotQuote(feature.id)} [label=${dotQuote(feature.id)}, shape=tab, fillcolor=${dotQuote(color)}, style="filled,bold"];`);
    for (const t of openTasks) {
      lines.push(`    ${dotQuote(t.id)} [label=${dotQuote(t.id)}];`);
    }
    lines.push('  }');

    for (const t of openTasks) {
      for (const [dstId] of t.prereqs) {
        const dstIsFeatureOnly = !dstId.includes('-');
        const targetAlive = allTaskIds.has(dstId) || (dstIsFeatureOnly && liveFeatureIds.has(dstId));
        if (!targetAlive) continue; // prerequisite already finished/removed -> drop the edge
        edges.push([t.id, dstId, classifyEdge(t, dstId)]);
      }
    }
  });

  const styles = {
    explicit_same: 'color="black", penwidth="1.2"',
    explicit_cross: 'color="#1f4e79", penwidth="1.4"',
    implicit_cross: 'color="crimson", penwidth="1.5"',
    soft_cross: 'color="gray50", penwidth="1.2", style="dashed"',
  };
  for (const [src, dst, kind] of edges) {
    lines.push(`  ${dotQuote(src)} -> ${dotQuote(dst)} [${styles[kind]}];`);
  }

  lines.push('  subgraph cluster_legend {');
  lines.push('    label="Legend";');
  lines.push('    style="rounded,dashed";');
  lines.push('    color="#999999";');
  lines.push('    "L1" [label="same-feature / explicit", fillcolor="white"];');
  lines.push('    "L2" [label="cross-feature / explicit", fillcolor="white"];');
  lines.push('    "L3" [label="cross-feature / implicit", fillcolor="white"];');
  lines.push('    "L4" [label="cross-feature / soft", fillcolor="white"];');
  lines.push('    "L1" -> "L1" [color="black", penwidth="1.2"];');
  lines.push('    "L2" -> "L2" [color="#1f4e79", penwidth="1.4"];');
  lines.push('    "L3" -> "L3" [color="crimson", penwidth="1.5"];');
  lines.push('    "L4" -> "L4" [color="gray50", penwidth="1.2", style="dashed"];');
  lines.push('  }');
  lines.push('}');

  return {
    dot: lines.join('\n') + '\n',
    nodeCount: allTaskIds.size,
    edgeCount: edges.length,
    liveFeatureCount: liveFeatures.length,
  };
}

/**
 * Render DOT source to a target format by invoking the Graphviz `dot` binary.
 * @param {string} dotBinary path to dot executable
 * @param {string} dotText DOT source
 * @param {string} format 'svg' | 'png' | any graphviz -T format
 * @param {string} outPath destination file path
 */
function renderWithDot(dotBinary, dotText, format, outPath) {
  const result = spawnSync(dotBinary, [`-T${format}`, '-o', outPath], {
    input: dotText,
    encoding: 'utf-8',
  });
  if (result.error) {
    if (result.error.code === 'ENOENT') {
      throw Object.assign(new Error(`Graphviz binary not found: ${dotBinary}`), { code: 'ENOBIN' });
    }
    throw result.error;
  }
  if (result.status !== 0) {
    throw Object.assign(
      new Error(`Graphviz failed (exit ${result.status}) rendering -T${format}: ${result.stderr}`),
      { code: 'EDOTFAIL' }
    );
  }
}

function parseArgs(argv) {
  const args = {
    input: 'TODO.md',
    output: 'todo_dependency_graph',
    format: 'svg',
    includeDone: false,
    dotBinary: 'dot',
    dotTextOnly: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case '--input': args.input = argv[++i]; break;
      case '--output': args.output = argv[++i]; break;
      case '--format': args.format = argv[++i]; break;
      case '--include-done': args.includeDone = true; break;
      case '--dot-binary': args.dotBinary = argv[++i]; break;
      case '--dot-text-only': args.dotTextOnly = true; break;
      default:
        process.stderr.write(`WARNING: unrecognized argument: ${a}\n`);
    }
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  const inPath = path.resolve(args.input);
  if (!fs.existsSync(inPath) || !fs.statSync(inPath).isFile()) {
    process.stderr.write(`ERROR: input file not found: ${inPath}\n`);
    return 1;
  }

  const text = fs.readFileSync(inPath, 'utf-8');
  const features = parseTodo(text);
  if (features.length === 0) {
    process.stderr.write("ERROR: no '## Feature: XXXX — ...' headings found in input.\n");
    return 2;
  }

  const totalTasks = features.reduce((sum, f) => sum + f.tasks.length, 0);
  if (totalTasks === 0) {
    process.stderr.write("ERROR: features found, but no '- [ ] **XXXX-YY** ...' tasks parsed.\n");
    return 2;
  }

  const { dot, nodeCount, edgeCount, liveFeatureCount } = buildDot(features, args.includeDone);

  const outBase = args.output;
  const dotPath = `${outBase}.dot`;
  fs.writeFileSync(dotPath, dot, 'utf-8');

  const nFeaturesTotal = features.length;
  const nFeaturesDone = features.filter((f) => f.done).length;
  process.stdout.write(
    `Parsed ${nFeaturesTotal} feature(s) (${nFeaturesDone} fully done), ${totalTasks} task(s) total.\n`
  );
  process.stdout.write(
    `Built graph with ${nodeCount} open task node(s), ${liveFeatureCount} live feature cluster(s), and ${edgeCount} dependency edge(s).\n`
  );
  process.stdout.write(`DOT written to: ${dotPath}\n`);

  if (args.dotTextOnly) {
    return 0;
  }

  const formats = args.format === 'both' ? ['svg', 'png'] : [args.format];
  for (const fmt of formats) {
    const outPath = `${outBase}.${fmt}`;
    try {
      renderWithDot(args.dotBinary, dot, fmt, outPath);
    } catch (err) {
      process.stderr.write(`ERROR: ${err.message}\n`);
      return err.code === 'ENOBIN' ? 3 : 4;
    }
    process.stdout.write(`Output written to: ${outPath}\n`);
  }

  return 0;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { parseTodo, buildDot, classifyEdge, dotQuote, Task, Feature };
