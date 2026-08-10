(() => {
  "use strict";
  const host = document.querySelector("[data-component-graph]");
  if (!host) return;
  const ownScript = document.querySelector('script[src$="component-graph.js"]');
  const root = new URL(".", ownScript ? ownScript.src : document.baseURI);
  const dataUrl = new URL("data/component-graph.json", root);
  const embedded = document.getElementById("component-graph-data");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ui = {
    loading: host.dataset.loading || "Graph wird geladen …",
    failed: host.dataset.failed || "Der Komponentengraph konnte nicht geladen werden."
  };

  // Fixed edge-weight threshold for the default hub view (previously a user-adjustable slider).
  const MIN_WEIGHT = 0; // unused legacy constant; edge visibility no longer depends on weight

  host.innerHTML = `<div class="component-graph-toolbar"><p class="component-graph-caption dim" data-graph-caption></p><button type="button" class="component-graph-reset-button" data-graph-keep-selected hidden>Nicht-Markierte entfernen</button><button type="button" class="component-graph-reset-button" data-graph-restore hidden>Alle entfernen</button><label class="graph-anchor-force">Ankerkraft <input type="range" min="0" max="300" step="5" value="10" data-graph-anchor-force><output data-graph-anchor-output>10%</output></label></div>
  <div class="component-graph-split"><div class="component-graph-stage" role="img" aria-label="Radiale Clusterkarte der API-Komponenten mit Federphysik"><p class="dim">${ui.loading}</p></div><div class="component-graph-removed-panel"><div class="component-graph-removed-titlebar"><div class="component-graph-removed-title" data-graph-removed-title>Meistgenutzte Klassen</div><input class="component-graph-removed-search" data-graph-removed-search type="search" placeholder="Klasse suchen" aria-label="Geparkte Klassen filtern"><button type="button" class="component-graph-collapse-all" data-graph-collapse-all aria-label="Alle einklappen" title="Alle einklappen"><span class="component-graph-collapse-caret" aria-hidden="true"></span></button><button type="button" class="component-graph-removed-add-all" data-graph-restore-filtered>Alle hinzufügen</button></div><div class="component-graph-removed-canvas" data-graph-removed></div></div></div>`;

  const stage = host.querySelector(".component-graph-stage");
  const caption = host.querySelector("[data-graph-caption]");
  const restoreButton = host.querySelector("[data-graph-restore]");
  const keepSelectedButton = host.querySelector("[data-graph-keep-selected]");
  const removedCanvas = host.querySelector("[data-graph-removed]");
  const removedPanel = host.querySelector(".component-graph-removed-panel");
  const removedTitle = host.querySelector("[data-graph-removed-title]");
  const removedSearch = host.querySelector("[data-graph-removed-search]");
  const restoreFilteredButton = host.querySelector("[data-graph-restore-filtered]");
  const collapseAllButton = host.querySelector("[data-graph-collapse-all]");

  const nodeLabel = (n) => n.label || n.shortLabel || n.id;

  // ---------- UML detail levels ----------
  // Every component node can be shown at three levels of detail. Left-clicking a node cycles
  // through them, so a single class can be expanded without blowing up the whole graph.
  //   0 -- name (+ namespace): the compact caption the graph has always used
  //   1 -- UML box with at most UML_PREVIEW members per compartment
  //   2 -- UML box with every documented member
  const UML_PREVIEW = 5;
  // The level is derived from interaction state, never stored: hovering a node shows
  // everything, selecting it shows the preview, anything else stays at the bare name.
  const levelFor = (selected, hovered) => (hovered ? 2 : selected ? 1 : 0);

  // Visibility markers follow UML: + public, # protected, - private.
  const UML_VIS = { public: "+", protected: "#", private: "-" };
  const umlMember = (m) => {
    if (typeof m === "string") return m;
    if (!m || typeof m !== "object") return "";
    const sign = UML_VIS[m.access] || "+";
    const type = m.type ? `: ${m.type}` : "";
    return `${sign} ${m.name || "?"}${m.params || ""}${type}`;
  };

  // A compartment: at most `max` entries, with a trailing ellipsis line when truncated.
  const umlCompartment = (members, max) => {
    const all = (members || []).map(umlMember).filter(Boolean);
    if (!all.length) return [];
    if (max === Infinity || all.length <= max) return all;
    return all.slice(0, max).concat([`… ${all.length - max} weitere`]);
  };

  // Build the multi-line caption for a node at a given detail level. Compartments are
  // separated by a rule of box-drawing characters -- Cytoscape renders one text block per
  // node, so the separators are part of the label rather than real geometry.
  const RULE = "──────────";

  // Cytoscape's `width: "label"` mis-measures our monospaced multi-line captions, so the box
  // stayed small while the text spilled over the border. We measure the label ourselves with
  // a canvas 2D context using the exact same font and hand Cytoscape explicit dimensions.
  const UML_FONT_SIZE = 9;
  const UML_FONT = `${UML_FONT_SIZE}px ui-monospace, SFMono-Regular, Menlo, monospace`;
  const UML_LINE_HEIGHT = UML_FONT_SIZE * 1.32;
  const NAME_FONT_SIZE = 10;
  const NAME_FONT = `${NAME_FONT_SIZE}px Satoshi, Inter, system-ui, sans-serif`;
  const NAME_LINE_HEIGHT = NAME_FONT_SIZE * 1.35;
  const UML_PAD = 10;
  let measureCtx = null;
  const measureLabel = (textBlock, font, lineHeight = UML_LINE_HEIGHT) => {
    if (!measureCtx) {
      const c = document.createElement("canvas");
      measureCtx = c.getContext("2d");
    }
    const lines = String(textBlock).split("\n");
    if (!measureCtx) {
      // Canvas unavailable (very old browser): fall back to a character-count estimate.
      const cols = Math.max(...lines.map((l) => l.length), 1);
      return { w: cols * UML_FONT_SIZE * 0.62, h: lines.length * UML_LINE_HEIGHT };
    }
    measureCtx.font = font;
    let w = 0;
    for (const line of lines) w = Math.max(w, measureCtx.measureText(line).width);
    return { w, h: lines.length * lineHeight };
  };

  // Box geometry for a node at a given level: level 0 keeps Cytoscape's own label sizing,
  // expanded levels get measured pixel dimensions so the border always encloses the text.
  const umlBoxFor = (labelText, level) => {
    if (!level) return null;
    // Measure in the font the level actually renders in, otherwise the border would not
    // enclose the caption: level 1 is the proportional UI font, level 2 the monospace one.
    const { w, h } = measureLabel(labelText, level === 1 ? NAME_FONT : UML_FONT, level === 1 ? NAME_LINE_HEIGHT : UML_LINE_HEIGHT);
    return {
      // A little slack on top of the measurement absorbs sub-pixel rounding.
      umlW: Math.ceil(w + 2 * UML_PAD + 4),
      umlH: Math.ceil(h + 2 * UML_PAD),
      umlTextW: Math.ceil(w + 2)
    };
  };

  const umlLabelFor = (n, level) => {
    const name = n.shortLabel || n.label || n.id;
    if (!level) return nodeLabel(n);
    // Level 1 is the identity card: the canonical name split over two lines, namespace on
    // top, type name below. No stereotype, no compartments, no metadata.
    if (level === 1) {
      const ns1 = n.namespace || namespaceOf(n);
      return ns1 ? `${ns1}\n${name}` : name;
    }
    const max = level >= 2 ? Infinity : UML_PREVIEW;
    const lines = [];
    if (n.stereotype) lines.push(`«${n.stereotype}»`);
    else if (n.kind && n.kind !== "class") lines.push(`«${n.kind}»`);
    lines.push(name);
    const ns = n.namespace || namespaceOf(n);
    if (ns) lines.push(ns);
    const attrs = umlCompartment(n.attributes, max);
    const ops = umlCompartment(n.operations, max);
    // Without generated member data the expanded box would be an empty frame; showing the
    // known metadata keeps the level meaningful until the builder emits members.
    if (!attrs.length && !ops.length) {
      const meta = [];
      if (n.module) meta.push(`Modul: ${n.module}`);
      if (n.visibility) meta.push(`Sichtbarkeit: ${n.visibility}`);
      if (level >= 2 && n.namespaceDeviation) meta.push(`Abweichung: ${n.namespaceDeviation}`);
      if (meta.length) lines.push(RULE, ...meta);
      return withRules(lines);
    }
    if (attrs.length) lines.push(RULE, ...attrs);
    if (ops.length) lines.push(RULE, ...ops);
    return withRules(lines);
  };

  // Stretch every separator to the width of the widest real line, so the compartment rules
  // span the whole box the way they do in a drawn UML class diagram.
  const withRules = (lines) => {
    const width = Math.max(...lines.filter((l) => l !== RULE).map((l) => l.length), 4);
    return lines.map((l) => (l === RULE ? "─".repeat(width) : l)).join("\n");
  };

  // Derive the C++ namespace a class/struct lives in from its qualified label,
  // e.g. "ara::com::proxy::Foo" -> namespace "ara::com::proxy". Normalizes
  // "namespace X" prefixes and drops the final segment (the type name itself).
  const normNsSegment = (s) => {
    const t = (s || "").trim();
    return t.startsWith("namespace ") ? t.slice("namespace ".length) : t;
  };
  const namespaceOf = (n) => {
    const label = n.label || "";
    const parts = label.split("::").map(normNsSegment).filter(Boolean);
    if (parts.length < 2) return null;
    const nsParts = parts.slice(0, -1);
    return nsParts.join("::");
  };
  const matchesQuery = (n, q) => {
    if (!q) return true;
    const hay = `${n.label || ""} ${n.shortLabel || ""} ${n.id || ""}`.toLowerCase();
    return hay.includes(q);
  };

  // Curated display order for the well-known modules. Any further module present in the
  // graph data is appended before "other" by registerModules() below, so a new AUTOSAR
  // cluster never silently falls back to the unnamed/grey bucket.
  const MODULE_ORDER = ["core", "com", "diag", "crypto", "per", "exec", "sm", "phm", "log", "tsync", "fw", "idsm", "nm", "rds", "shwa", "other"];
  const MODULE_COLOR = {
    core: "#01696f", com: "#0b5177", diag: "#964219", crypto: "#7a39bb", per: "#437a22",
    exec: "#006494", sm: "#a13544", phm: "#da7101", log: "#5c5b56", tsync: "#0c4e54",
    fw: "#8a6d1f", idsm: "#7d2f5e", nm: "#1f6f4a", rds: "#4a4fa6", shwa: "#8c5a2b",
    other: "#7a7974"
  };

  // Deterministic fallback hue for modules that appear in the data but have no curated
  // color: derived from the id so the same module always renders in the same color.
  const derivedModuleColor = (id) => {
    let h = 0;
    for (let i = 0; i < id.length; i += 1) h = (h * 31 + id.charCodeAt(i)) % 360;
    return `hsl(${h}, 46%, 34%)`;
  };

  // Ensures every module found in the graph data has both a rank and a color before the
  // graph, the module boxes and the parked tray are rendered.
  const registerModules = (modules) => {
    (modules || []).forEach((m) => {
      const id = m && m.id;
      if (!id) return;
      if (!MODULE_COLOR[id]) MODULE_COLOR[id] = derivedModuleColor(id);
      if (MODULE_ORDER.indexOf(id) === -1) {
        MODULE_ORDER.splice(Math.max(0, MODULE_ORDER.indexOf("other")), 0, id);
      }
    });
  };

  // ---------- scoring / hub subset (unchanged logic) ----------
  const scoreGraph = (graph) => {
    const byId = new Map(graph.nodes.map((n) => [n.id, n]));
    const score = new Map(), degree = new Map(), cross = new Map(), coreCross = new Map();
    const add = (map, id, v) => map.set(id, (map.get(id) || 0) + v);
    graph.edges.forEach((e) => {
      add(score, e.source, e.weight); add(score, e.target, e.weight);
      add(degree, e.source, 1); add(degree, e.target, 1);
      const s = byId.get(e.source), t = byId.get(e.target);
      if (!s || !t || s.module === t.module) return;
      add(cross, e.source, 1); add(cross, e.target, 1);
      if (s.module === "core" || t.module === "core") {
        add(coreCross, e.source, e.weight); add(coreCross, e.target, e.weight);
      }
    });
    graph.nodes.forEach((n) => {
      n.score = score.get(n.id) || 0;
      n.degree = degree.get(n.id) || 0;
      n.crossDegree = cross.get(n.id) || 0;
      n.coreCross = coreCross.get(n.id) || 0;
      n.defaultVisible = false;
      n.hubRank = n.coreCross * 100 + n.crossDegree * 8 + n.score * 0.15 + n.degree;
    });
  };

  const markDefaultSubset = (graph) => {
    const byModule = new Map();
    graph.nodes.forEach((n) => {
      const arr = byModule.get(n.module) || [];
      arr.push(n);
      byModule.set(n.module, arr);
    });
    (byModule.get("core") || []).slice().sort((a, b) => b.hubRank - a.hubRank).forEach((n, i) => {
      n.defaultVisible = i < 10 && (n.coreCross >= 40 || n.crossDegree >= 12 || n.score >= 110);
    });
    byModule.forEach((nodes, mod) => {
      if (mod === "core") return;
      nodes.sort((a, b) => b.hubRank - a.hubRank);
      const cap = mod === "diag" || mod === "crypto" ? 5 : mod === "com" || mod === "per" ? 4 : 3;
      nodes.slice(0, cap).forEach((n) => {
        if (n.coreCross >= 8 || n.score >= 20 || n.crossDegree >= 2) n.defaultVisible = true;
      });
      if (nodes[0]) nodes[0].defaultVisible = true;
    });
    graph.edges.forEach((e) => {
      const s = graph.nodesById.get(e.source), t = graph.nodesById.get(e.target);
      if (!s || !t || s.module === t.module) return;
      const coreEdge = s.module === "core" || t.module === "core";
      if (coreEdge && e.weight >= 14) { s.defaultVisible = true; t.defaultVisible = true; }
    });
  };

  // ---------- radial home positions (anchors for the spring simulation) ----------
  const packInDisc = (ids, homes, ox, oy, radius, faceAngle) => {
    const n = ids.length;
    if (!n) return;
    if (n === 1) { homes.set(ids[0], { x: ox, y: oy }); return; }
    const rings = Math.max(1, Math.ceil(Math.sqrt(n)));
    let idx = 0;
    for (let r = 0; r < rings && idx < n; r++) {
      const count = r === 0 ? 1 : Math.min(n - idx, Math.max(6, Math.round(2 * Math.PI * (r + 1))));
      const rr = r === 0 ? 0 : (radius * r) / rings;
      for (let k = 0; k < count && idx < n; k++, idx++) {
        const ang = faceAngle != null
          ? faceAngle + (k - (count - 1) / 2) * (0.55 / Math.max(count, 1))
          : (k / count) * Math.PI * 2 - Math.PI / 2;
        homes.set(ids[idx], { x: ox + Math.cos(ang) * rr, y: oy + Math.sin(ang) * rr });
      }
    }
    while (idx < n) {
      const ang = (idx / n) * Math.PI * 2 - Math.PI / 2;
      homes.set(ids[idx], { x: ox + Math.cos(ang) * radius * 0.92, y: oy + Math.sin(ang) * radius * 0.92 });
      idx++;
    }
  };

  // Recursively packs a container's direct children into a disc, then, for any child that is
  // itself a namespace sub-container, packs its own children into a smaller nested disc around
  // that position — this is what lets classes nest inside their namespace boxes inside the module box.
  const packChildrenRecursive = (containerNode, homes, ox, oy, radius, faceAngle) => {
    const kids = containerNode.children().filter((c) => c.style("display") !== "none");
    const ids = kids.map((c) => c.id());
    packInDisc(ids, homes, ox, oy, radius, faceAngle);
    kids.forEach((k) => {
      if (k.data("kind") !== "namespace") return;
      const home = homes.get(k.id());
      if (!home) return;
      const grandkids = k.children().filter((c) => c.style("display") !== "none");
      const n = grandkids.length;
      const subR = Math.max(70, Math.sqrt(Math.max(n, 1)) * 58);
      packChildrenRecursive(k, homes, home.x, home.y, subR, faceAngle);
    });
  };

  const computeHomes = (cy) => {
    const homes = new Map();
    const modAnchors = new Map();
    const moduleNodes = cy.nodes().filter((n) => n.data("kind") === "module");
    const visibleModules = moduleNodes.filter((m) => m.children().some((c) => c.style("display") !== "none"));
    if (visibleModules.empty()) return { homes, modAnchors };
    const ordered = visibleModules.toArray().sort((a, b) => {
      const ia = MODULE_ORDER.indexOf(a.data("module")), ib = MODULE_ORDER.indexOf(b.data("module"));
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
    const core = ordered.find((m) => m.data("module") === "core") || ordered[0];
    const ring = ordered.filter((m) => m.id() !== core.id());
    // Radii scale with how much content actually has to fit, otherwise the ring modules start
    // life inside one another and the simulation has to untangle a knot at every load.
    const totalVisible = visibleModules.toArray().reduce((sum, m) => sum + m.descendants().filter((c) => c.style("display") !== "none").length, 0);
    const coreKids = core.descendants().filter((c) => c.style("display") !== "none").length;
    const CORE_R = Math.max(210, 60 + Math.sqrt(Math.max(coreKids, 1)) * 62);
    const RING_R = Math.max(980, CORE_R + 420 + Math.sqrt(Math.max(totalVisible, 1)) * 58);
    const cx = 0, cy0 = 0;
    modAnchors.set(core.id(), { x: cx, y: cy0 });
    packChildrenRecursive(core, homes, cx, cy0, CORE_R * 0.78, null);
    ring.forEach((mod, i) => {
      const ang = -Math.PI / 2 + (i / Math.max(ring.length, 1)) * Math.PI * 2;
      const mx = cx + Math.cos(ang) * RING_R, my = cy0 + Math.sin(ang) * RING_R;
      modAnchors.set(mod.id(), { x: mx, y: my });
      const kidCount = mod.children().filter((c) => c.style("display") !== "none").length;
      const localR = Math.max(150, Math.sqrt(Math.max(kidCount, 1)) * 105);
      const pull = 0.12;
      const ox = mx * (1 - pull) + cx * pull, oy = my * (1 - pull) + cy0 * pull;
      packChildrenRecursive(mod, homes, ox, oy, localR, ang + Math.PI);
    });
    return { homes, modAnchors };
  };

  // ---------- spring-physics simulation ----------
  const SIM = {
    // Anchors only provide the coarse radial structure; they are deliberately weak so
    // that the separation forces below can resolve overlaps instead of being overruled.
    ANCHOR_K: 0.009, // multiplied by anchorScale, initialised to 0.1 (10%) below
    EDGE_K_CORE: 0.035,
    EDGE_K_CROSS: 0.016,
    EDGE_K_INTRA: 0.008,
    REST_CORE: 210,
    REST_CROSS: 340,
    REST_INTRA: 60,
    // Long-range soft repulsion (inverse square) keeps clusters loose ...
    REPEL_K: 26000,
    REPEL_MIN: 60,
    REPEL_CUTOFF2: 420000,
    // ... while the hard shell below guarantees the label boxes never overlap.
    COLLIDE_PAD: 16,
    COLLIDE_K: 0.16,
    MODULE_REPEL_K: 7200000,
    MODULE_REPEL_MIN: 620,
    // Grab behaviour: a soft, size-aware shell around the held node nudges neighbours
    // aside instead of firing them across the canvas.
    POINTER_PUSH_K: 0.14,
    POINTER_CLEARANCE: 54,
    DAMPING: 0.86,
    DRAG_DAMPING: 0.55,
    MAX_SPEED: 26,
    IDLE_AMPLITUDE: 2.2,
    IDLE_FREQ: 0.0009
  };

  const createSimulation = (cy) => {
    let anchorScale = 0.1;
    let homes = new Map();
    let modAnchors = new Map();
    let raf = null;
    let t0 = performance.now();
    const state = new Map(); // id -> {x,y,vx,vy,phase}
    const draggingIds = new Set();

    const nodesList = () => cy.nodes().filter((n) => n.data("kind") !== "module" && n.data("kind") !== "namespace" && n.style("display") !== "none");

    const seed = (recenter) => {
      const r = computeHomes(cy);
      homes = r.homes;
      modAnchors = r.modAnchors;
      nodesList().forEach((n) => {
        const id = n.id();
        const home = homes.get(id) || { x: 0, y: 0 };
        let s = state.get(id);
        if (!s || recenter) {
          const pos = recenter || !s ? home : n.position();
          s = { x: pos.x, y: pos.y, vx: 0, vy: 0, phase: Math.random() * Math.PI * 2 };
          state.set(id, s);
          n.position({ x: s.x, y: s.y });
        }
      });
      // drop stale state for hidden/removed nodes
      Array.from(state.keys()).forEach((id) => {
        if (!homes.has(id)) state.delete(id);
      });
      sizeNodes();
    };

    const sizeNodes = () => {
      cy.nodes().forEach((n) => {
        if (n.data("kind") === "module") return;
        // Expanded UML boxes carry their own measured geometry (umlW/umlH) and must not be
        // squeezed back into the hub-rank pill size -- that inline width/height is exactly
        // what made a clicked node keep its old dimensions while the caption grew.
        if (n.data("uml")) {
          n.removeStyle("width height font-size");
          n.style("border-width", 2.2);
          return;
        }
        const hr = n.data("hubRank") || 0;
        const tt = Math.min(1, hr / 400);
        // Level 0 renders as a dot, so the pill geometry is replaced by a small disc. The hub
        // rank still shows through as diameter: busier components read as bigger dots.
        const d = 9 + tt * 13;
        n.style("width", d);
        n.style("height", d);
        n.style("font-size", 10 + tt * 3);
        n.style("border-width", 1);
      });
    };

    const edgeParams = (e) => {
      if (e.data("coreLink")) return { k: SIM.EDGE_K_CORE, rest: SIM.REST_CORE };
      if (e.data("cross")) return { k: SIM.EDGE_K_CROSS, rest: SIM.REST_CROSS };
      return { k: SIM.EDGE_K_INTRA, rest: SIM.REST_INTRA };
    };

    const step = (now) => {
      const dt = Math.min(2, (now - t0) / 16.67) || 1;
      t0 = now;
      const nodes = nodesList();
      const ids = nodes.map((n) => n.id());
      const fx = new Map(ids.map((id) => [id, 0]));
      const fy = new Map(ids.map((id) => [id, 0]));

      // 1) anchor springs (toward radial home, with gentle idle float)
      nodes.forEach((n) => {
        const id = n.id();
        const s = state.get(id);
        if (!s || draggingIds.has(id)) return;
        const home = homes.get(id);
        if (!home) return;
        let hx = home.x, hy = home.y;
        if (!reduceMotion) {
          hx += Math.cos(now * SIM.IDLE_FREQ + s.phase) * SIM.IDLE_AMPLITUDE;
          hy += Math.sin(now * SIM.IDLE_FREQ * 1.3 + s.phase) * SIM.IDLE_AMPLITUDE;
        }
        fx.set(id, fx.get(id) + (hx - s.x) * SIM.ANCHOR_K * anchorScale);
        fy.set(id, fy.get(id) + (hy - s.y) * SIM.ANCHOR_K * anchorScale);
      });

      // 2) edge springs (this is what creates the visible "tug" and force feedback)
      cy.edges().forEach((e) => {
        if (e.style("display") === "none") return;
        const s = e.source(), t = e.target();
        const sid = s.id(), tid = t.id();
        const ss = state.get(sid), ts = state.get(tid);
        if (!ss || !ts) return;
        const dx = ts.x - ss.x, dy = ts.y - ss.y;
        const dist = Math.max(1, Math.hypot(dx, dy));
        const { k, rest } = edgeParams(e);
        const stretch = dist - rest;
        const f = k * stretch;
        const nx = dx / dist, ny = dy / dist;
        if (!draggingIds.has(sid)) { fx.set(sid, fx.get(sid) + nx * f); fy.set(sid, fy.get(sid) + ny * f); }
        if (!draggingIds.has(tid)) { fx.set(tid, fx.get(tid) - nx * f); fy.set(tid, fy.get(tid) - ny * f); }
        // tension feedback: color/width react live to how stretched the spring is
        const tension = Math.max(0, Math.min(1, Math.abs(stretch) / (rest * 0.9)));
        const prev = e.data("tension") || 0;
        if (Math.abs(prev - tension) > 0.03) e.data("tension", tension);
      });

      // 3) local separation. Two cooperating terms:
      //    - a soft inverse-square repulsion that spreads clusters out over a wide radius
      //    - a hard "collision shell" sized from the actual rendered box of each node, so
      //      labels drift into a non-overlapping configuration instead of piling up.
      const halfW = new Map();
      const halfH = new Map();
      nodes.forEach((n) => {
        halfW.set(n.id(), n.width() / 2);
        halfH.set(n.id(), n.height() / 2);
      });
      for (let i = 0; i < nodes.length; i++) {
        const idA = ids[i];
        const a = state.get(idA);
        if (!a) continue;
        for (let j = i + 1; j < nodes.length; j++) {
          const idB = ids[j];
          const b = state.get(idB);
          if (!b) continue;
          let dx = a.x - b.x, dy = a.y - b.y;
          let d2 = dx * dx + dy * dy;
          if (d2 > SIM.REPEL_CUTOFF2) continue; // ignore far pairs
          const raw = Math.sqrt(d2) || 0.01;
          const d = Math.max(SIM.REPEL_MIN, raw);
          let nx = dx / raw, ny = dy / raw;
          if (!isFinite(nx) || !isFinite(ny)) { nx = Math.cos(i); ny = Math.sin(i); }
          let f = SIM.REPEL_K / (d * d);
          // collision shell: minimum centre distance from both boxes plus padding
          const minX = halfW.get(idA) + halfW.get(idB) + SIM.COLLIDE_PAD;
          const minY = halfH.get(idA) + halfH.get(idB) + SIM.COLLIDE_PAD;
          const overlapX = minX - Math.abs(dx);
          const overlapY = minY - Math.abs(dy);
          if (overlapX > 0 && overlapY > 0) {
            // resolve along the axis of least penetration -> boxes slide apart smoothly
            if (overlapX < overlapY) {
              const push = overlapX * SIM.COLLIDE_K * (dx >= 0 ? 1 : -1);
              if (!draggingIds.has(idA)) fx.set(idA, fx.get(idA) + push);
              if (!draggingIds.has(idB)) fx.set(idB, fx.get(idB) - push);
            } else {
              const push = overlapY * SIM.COLLIDE_K * (dy >= 0 ? 1 : -1);
              if (!draggingIds.has(idA)) fy.set(idA, fy.get(idA) + push);
              if (!draggingIds.has(idB)) fy.set(idB, fy.get(idB) - push);
            }
          }
          if (!draggingIds.has(idA)) { fx.set(idA, fx.get(idA) + nx * f); fy.set(idA, fy.get(idA) + ny * f); }
          if (!draggingIds.has(idB)) { fx.set(idB, fx.get(idB) - nx * f); fy.set(idB, fy.get(idB) - ny * f); }
        }
      }

      // 3a) module-vs-module repulsion: push whole module clusters apart via their live centroids,
      // so the outer module boxes keep clear separation instead of drifting into each other.
      const modGroups = new Map();
      nodes.forEach((n) => {
        const mod = n.data("module");
        if (!mod) return;
        const s = state.get(n.id());
        if (!s) return;
        const g = modGroups.get(mod) || [];
        g.push(n.id());
        modGroups.set(mod, g);
      });
      const modCentroids = new Map();
      modGroups.forEach((memberIds, mod) => {
        let sx = 0, sy = 0;
        memberIds.forEach((id) => { const s = state.get(id); sx += s.x; sy += s.y; });
        modCentroids.set(mod, { x: sx / memberIds.length, y: sy / memberIds.length, members: memberIds });
      });
      const modKeys = Array.from(modCentroids.keys());
      for (let i = 0; i < modKeys.length; i++) {
        for (let j = i + 1; j < modKeys.length; j++) {
          const A = modCentroids.get(modKeys[i]);
          const B = modCentroids.get(modKeys[j]);
          const dx = A.x - B.x, dy = A.y - B.y;
          const d = Math.max(SIM.MODULE_REPEL_MIN, Math.hypot(dx, dy) || 0.01);
          const f = SIM.MODULE_REPEL_K / (d * d);
          const nx = dx / d, ny = dy / d;
          A.members.forEach((id) => {
            if (draggingIds.has(id)) return;
            fx.set(id, fx.get(id) + nx * f);
            fy.set(id, fy.get(id) + ny * f);
          });
          B.members.forEach((id) => {
            if (draggingIds.has(id)) return;
            fx.set(id, fx.get(id) - nx * f);
            fy.set(id, fy.get(id) - ny * f);
          });
        }
      }

      // 3b) pointer push: a grabbed node gently shoves whatever it runs into. The force is a
      // penetration-depth spring against a clearance shell derived from both node sizes, so it
      // is exactly zero at contact distance and grows smoothly the deeper the overlap gets --
      // neighbours glide aside and settle back instead of being catapulted away.
      draggingIds.forEach((dragId) => {
        const drag = state.get(dragId);
        if (!drag) return;
        const dragHW = halfW.get(dragId) || 45;
        const dragHH = halfH.get(dragId) || 20;
        nodes.forEach((n) => {
          const id = n.id();
          if (id === dragId || draggingIds.has(id)) return;
          const s = state.get(id);
          if (!s) return;
          const dx = s.x - drag.x;
          const dy = s.y - drag.y;
          const raw = Math.hypot(dx, dy) || 0.01;
          const clearance = Math.hypot(dragHW + (halfW.get(id) || 45), dragHH + (halfH.get(id) || 20)) + SIM.POINTER_CLEARANCE;
          if (raw > clearance) return;
          const penetration = clearance - raw;
          const f = penetration * SIM.POINTER_PUSH_K;
          const nx = dx / raw, ny = dy / raw;
          fx.set(id, fx.get(id) + nx * f);
          fy.set(id, fy.get(id) + ny * f);
        });
      });

      // 4) integrate
      cy.batch(() => {
        nodes.forEach((n) => {
          const id = n.id();
          const s = state.get(id);
          if (!s) return;
          if (draggingIds.has(id)) {
            const p = n.position();
            s.vx = p.x - s.x;
            s.vy = p.y - s.y;
            s.x = p.x;
            s.y = p.y;
            return;
          }
          const damping = SIM.DAMPING;
          s.vx = (s.vx + fx.get(id) * dt) * damping;
          s.vy = (s.vy + fy.get(id) * dt) * damping;
          const speed = Math.hypot(s.vx, s.vy);
          if (speed > SIM.MAX_SPEED) { s.vx = (s.vx / speed) * SIM.MAX_SPEED; s.vy = (s.vy / speed) * SIM.MAX_SPEED; }
          s.x += s.vx * dt;
          s.y += s.vy * dt;
          n.position({ x: s.x, y: s.y });
        });
      });

      raf = requestAnimationFrame(step);
    };

    const start = () => {
      if (raf) return;
      t0 = performance.now();
      raf = requestAnimationFrame(step);
    };
    const stop = () => { if (raf) { cancelAnimationFrame(raf); raf = null; } };

    const settleOnce = (iterations) => {
      // reduced-motion path: relax synchronously without a visible animation loop
      for (let i = 0; i < iterations; i++) step(t0 + 16.6 * (i + 1));
      stop();
    };

    const grab = (id) => draggingIds.add(id);
    const free = (id) => draggingIds.delete(id);

    // sizeNodes is exposed so the UML detail toggle can restore the physics-driven pill size
    // when a node collapses back to level 0.
    const setAnchorScale = (value) => { anchorScale = Math.max(0, Number(value) || 0); };
    return { seed, start, stop, settleOnce, grab, free, sizeNodes, setAnchorScale, get modAnchors() { return modAnchors; } };
  };

  Promise.all([
    embedded ? Promise.resolve(JSON.parse(embedded.textContent)) : fetch(dataUrl).then((r) => {
      if (!r.ok) throw new Error(`Graph data: HTTP ${r.status}`);
      return r.json();
    }),
    window.cytoscape ? Promise.resolve() : Promise.reject(new Error("cytoscape.min.js not loaded"))
  ]).then(([graph]) => {
    scoreGraph(graph);
    graph.nodesById = new Map(graph.nodes.map((n) => [n.id, n]));
    markDefaultSubset(graph);

    const defaultCount = graph.nodes.filter((n) => n.defaultVisible).length;
    if (caption) {
      caption.textContent = `Federphysik-Karte · Standard: ${defaultCount} Hub-Komponenten (Kern = ara::core) · Ziehen erzeugt Zugspannung entlang der Kanten.`;
    }

    stage.textContent = "";

    // Build namespace sub-containers per module: any class/struct whose qualified
    // label carries a namespace path (e.g. "ara::com::proxy::Foo") gets nested inside
    // a compound box for that namespace, which itself lives inside the module box.
    const namespaceIds = new Map(); // key `module::ns::path` -> { id, label, module }
    graph.nodes.forEach((n) => {
      const ns = namespaceOf(n);
      n.namespacePath = ns;
      if (!ns) return;
      const key = `${n.module}::${ns}`;
      if (!namespaceIds.has(key)) {
        namespaceIds.set(key, { id: `ns:${key}`, label: ns, module: n.module });
      }
    });

    registerModules(graph.modules);

    const elements = [
      ...graph.modules.map((m) => ({ data: { id: `module:${m.id}`, label: m.label, module: m.id, kind: "module", color: MODULE_COLOR[m.id] || MODULE_COLOR.other } })),
      ...Array.from(namespaceIds.values()).map((ns) => ({ data: { id: ns.id, label: ns.label, module: ns.module, kind: "namespace", parent: `module:${ns.module}`, color: MODULE_COLOR[ns.module] || MODULE_COLOR.other } })),
      ...graph.nodes.map((n) => {
        const nsKey = n.namespacePath ? `ns:${n.module}::${n.namespacePath}` : null;
        const parent = nsKey && namespaceIds.has(nsKey) ? nsKey : `module:${n.module}`;
        // `uml` carries the current detail level so it can be used in style selectors;
        // `label` is always the caption for that level.
        // Nodes start collapsed; selection and hover drive the level from then on.
        return { data: {
          ...n, parent, uml: 0, label: nodeLabel(n), compactLabel: nodeLabel(n),
          fullLabel: n.label, color: MODULE_COLOR[n.module] || MODULE_COLOR.other
        } };
      }),
      ...graph.edges.map((e) => {
        const s = graph.nodesById.get(e.source), t = graph.nodesById.get(e.target);
        const cross = s && t && s.module !== t.module ? 1 : 0;
        const coreLink = s && t && (s.module === "core" || t.module === "core") && cross ? 1 : 0;
        return { data: { ...e, cross, coreLink, tension: 0 } };
      })
    ];

    const cy = cytoscape({
      container: stage,
      elements,
      minZoom: 0.12,
      maxZoom: 2.6,
      wheelSensitivity: 0.22,
      motionBlur: !reduceMotion,
      // The built-in box selection is replaced by our own marquee overlay further down: it
      // needs desktop modifier semantics and custom visuals, which the native one cannot do.
      boxSelectionEnabled: false,
      selectionType: "additive",
      layout: { name: "preset", fit: false },
      style: [
        { selector: "node", style: {
          "background-color": "#f9f8f5", "border-color": "data(color)", "border-width": 1.6,
          label: "data(label)", "font-size": 10.5, color: "#28251d", "text-wrap": "wrap",
          "text-max-width": 168, "text-valign": "center", "text-halign": "center",
          width: "label", height: "label", "padding": 8,
          shape: "round-rectangle", "overlay-padding": 2, "z-index": 10,
          "transition-property": "background-color, border-color", "transition-duration": "120ms"
        }},
        // Expanded UML boxes: monospaced, left-aligned text so the compartment rules line up.
        // Expanded boxes are sized from a real text measurement (see umlBoxFor): the width,
        // height and wrap limit all come from node data, so the border always encloses the
        // caption instead of the text spilling out of an undersized box.
        { selector: "node[uml > 0]", style: {
          "font-family": "ui-monospace, SFMono-Regular, Menlo, monospace", "font-size": 9,
          "text-wrap": "wrap", "text-max-width": "data(umlTextW)", "text-justification": "left",
          width: "data(umlW)", height: "data(umlH)", padding: 0,
          "border-width": 2.2, "background-color": "#fbfbf9", "z-index": 30
        }},
        // Level 1 carries no compartment rules, so the monospaced left-aligned treatment that
        // exists to line those rules up would only make the name card look ragged. Centre it
        // in the UI font and let the namespace read as a quieter caption above the type name.
        { selector: "node[uml = 1]", style: {
          "font-family": "'Satoshi', 'Inter', system-ui, sans-serif", "font-size": 10,
          "text-justification": "center", "text-halign": "center", "text-valign": "center"
        }},
        { selector: "node[uml = 2]", style: { "z-index": 32 } },
        { selector: "node[module = 'core']", style: { "background-color": "#d7e4e0", "border-color": "#01696f", "border-width": 2.2 } },
        // Level 0 is a bare dot: no caption at all, just a filled disc in the module colour.
        // Placed AFTER the core rule so the module tint cannot override the fill.
        { selector: "node[uml = 0]", style: {
          label: "", shape: "ellipse",
          "background-color": "data(color)", "background-opacity": 1,
          "border-color": "data(color)", "border-width": 1,
          "overlay-padding": 6, "z-index": 10
        }},
        { selector: "node[kind = 'module']", style: {
          "background-color": "#f3f0ec", "background-opacity": 0.5, "border-color": "data(color)",
          "border-width": 2, "border-style": "dashed", label: "data(label)", "font-size": 14,
          "font-weight": 700, color: "data(color)", "text-valign": "top", "text-halign": "center",
          "text-margin-y": -10, padding: 30, shape: "ellipse", "z-index": 1
        }},
        { selector: "node[kind = 'module'][module = 'core']", style: { "background-color": "#cedcd8", "background-opacity": 0.4, "border-style": "solid", "border-width": 2.5, padding: 38 } },
        { selector: "node.dragging", style: { "border-width": 3.2, "background-color": "#fff", "z-index": 50 } },
        { selector: "node:selected", style: { "border-width": 3.4, "border-color": "#a13544", "background-color": "#fff4f4", "z-index": 55 } },
        { selector: "node.sel-highlight", style: { opacity: 1, "z-index": 60 } },
        // Marquee preview states: what the current band would do on release.
        { selector: "node.marquee-will-select", style: {
          "border-color": "#a13544", "border-width": 3, "background-color": "#fdeff0",
          "overlay-color": "#a13544", "overlay-opacity": 0.12, "overlay-padding": 6, "z-index": 62
        }},
        { selector: "node.marquee-will-drop", style: {
          "border-color": "#7a7974", "border-width": 2, "background-color": "#f1efec",
          "overlay-color": "#7a7974", "overlay-opacity": 0.10, "overlay-padding": 4, "z-index": 61
        }},
        { selector: "node.marquee-flash", style: {
          "overlay-color": "#a13544", "overlay-opacity": 0.28, "overlay-padding": 10, "z-index": 64
        }},
        // Dots have no caption and almost no area, so the states above -- which communicate
        // through background colour -- would make them read as empty holes. Keep them filled
        // and let the ring around them carry the state instead.
        { selector: "node[uml = 0].marquee-will-select", style: { "background-color": "data(color)", "border-color": "#a13544", "border-width": 3 } },
        { selector: "node[uml = 0].marquee-will-drop", style: { "background-color": "data(color)", "border-color": "#7a7974", "border-width": 2 } },
        { selector: "node[uml = 0].dragging", style: { "background-color": "data(color)", "border-color": "#28251d", "border-width": 2.4 } },
        { selector: "edge.sel-highlight", style: { opacity: 1, "line-color": "#a13544", "target-arrow-color": "#a13544", width: 2.4, "z-index": 58 } },
        { selector: "edge", style: {
          width: "mapData(weight, 1, 60, 1.2, 4.8)", "line-color": "#9c9890", "target-arrow-color": "#8f8b84",
          "target-arrow-shape": "triangle", "curve-style": "bezier", opacity: 0.62, "arrow-scale": 0.85,
          "z-index": 12, events: "no"
        }},
        { selector: "edge[cross = 1]", style: { opacity: 0.4, "line-color": "#8aa3a5", "target-arrow-color": "#6d888a" } },
        { selector: "edge[coreLink = 1]", style: { opacity: 0.58, "line-color": "#01696f", "target-arrow-color": "#01696f", width: "mapData(weight, 1, 60, 1, 4.6)" } },
        { selector: "edge", style: { "line-color": "mapData(tension, 0, 1, #01696f, #a13544)" } },
        { selector: "edge[cross = 0][coreLink = 0]", style: { "line-color": "mapData(tension, 0, 1, #b6b4ae, #a13544)" } },
        { selector: "edge", style: { width: "mapData(tension, 0, 1, 0.6, 5.5)" } },
        // Connection-type styling: reference edges (undirected, neutral) vs. inheritance
        // edges (directed, hollow arrowhead). Declared after the tension-driven color
        // rules above so the fixed per-type color always wins over the live stretch tint.
        { selector: "edge[type = 'reference']", style: {
          "line-color": "#c9c6c0", "target-arrow-shape": "none", "source-arrow-shape": "none"
        }},
        { selector: "edge[type = 'inheritance']", style: {
          "line-color": "#7ec4e8", "target-arrow-color": "#7ec4e8",
          "target-arrow-shape": "triangle", "target-arrow-fill": "hollow",
          "source-arrow-shape": "none", "arrow-scale": 1.1, opacity: 0.85, "z-index": 14
        }},
        // When a reference and an inheritance edge both connect the same pair of nodes,
        // bezier curve-style (set on the base "edge" selector above) automatically fans
        // multiple parallel edges into distinct curved arcs instead of overlapping lines.
        { selector: "edge[weight >= 8]", style: { "z-index": 6 } },
        { selector: ".faded", style: { opacity: 0.18 } },
        // compound module boxes composite their own opacity onto every child node,
        // so a faded module container would drag down even fully-highlighted children.
        // Keep module containers themselves out of the fade so nested highlighting is visible.
        { selector: "node[kind = 'module'].faded", style: { opacity: 1 } },
        { selector: ".focus", style: { opacity: 1, "z-index": 30 } },
        { selector: "node.focus", style: { "z-index": 40 } },
        { selector: "node.hover-root", style: { "z-index": 45 } },
        { selector: "node.hover-neighbor", style: { "z-index": 42 } },
        { selector: "edge.hover-edge", style: { opacity: 1, width: 4.2, "z-index": 35 } }
      ]
    });

    const isModule = (n) => n.data("kind") === "module";
    const isContainer = (n) => n.data("kind") === "module" || n.data("kind") === "namespace";
    // Compound containers are viewport/drag targets, never selection targets. Cytoscape's
    // native compound selection can otherwise select the container together with all of its
    // descendants before our tap handler gets a chance to restore the leaf selection.
    cy.nodes().filter(isContainer).unselectify();

    // Nodes the user has dragged off the main canvas; they appear in the tray until restored.
    // Start with the seven most-connected classes parked to reduce initial visual density.
    const INITIAL_PARKED_COUNT = 7;
    let removedSearchTerm = "";
    const initialParked = graph.nodes.filter((n) => {
      if (!(n.kind === "class" || n.kind === "struct")) return false;
      const label = (n.shortLabel || n.label || "").toLowerCase();
      return !(/(^|::)(vector|array|string|span|map|unordered_map|set|unordered_set|list|deque|queue|stack|optional|variant|pair|tuple|unique_ptr|shared_ptr)$/.test(label));
    }).slice().sort((a, b) => (b.degree || 0) - (a.degree || 0) || (b.score || 0) - (a.score || 0)).slice(0, INITIAL_PARKED_COUNT).map((n) => n.id);
    const userRemoved = new Set(initialParked);
    let hasUserParkedNode = false;
    // Assigned further down, once apply()/applySelectionHighlight() exist. Tray items are
    // rebuilt continuously, so their handlers call through this indirection.
    let selectParkedFromTray = () => {};
    // Is this parked node currently selected? Selected parked nodes stay in the tray but are
    // highlighted there, and they bypass both the text filter and module collapsing.
    // Selection lookups happen O(n log n) times per tray render (filter + sort comparator).
    // One getElementById per call was needlessly expensive with hundreds of parked nodes, so
    // the selected ids are cached and invalidated whenever the selection changes.
    let selectedIdCache = null;
    const invalidateSelectionCache = () => { selectedIdCache = null; };
    const selectedIdSet = () => {
      if (!selectedIdCache) {
        selectedIdCache = new Set(cy.nodes(":selected").map((n) => n.id()));
      }
      return selectedIdCache;
    };
    const isNodeSelected = (nodeId) => selectedIdSet().has(nodeId);
    const selectedParkedIds = () => Array.from(userRemoved).filter((id) => isNodeSelected(id));
    const hasSelectedParked = () => selectedParkedIds().length > 0;

    const filteredRemovedNodes = () => {
      const query = removedSearchTerm.trim().toLowerCase();
      return graph.nodes
        .filter((n) => userRemoved.has(n.id) && (n.kind === "class" || n.kind === "struct"))
        // A selected item is always listed, even when the search term would filter it out.
        .filter((n) => isNodeSelected(n.id) || !query || nodeLabel(n).toLowerCase().includes(query) || (n.label || "").toLowerCase().includes(query))
        // Keep a stable relevance/name order while the group is expanded. Desktop-style
        // click/shift-click selection must not move items under the pointer as it changes.
        .sort((a, b) => (b.degree || 0) - (a.degree || 0)
          || (b.score || 0) - (a.score || 0) || nodeLabel(a).localeCompare(nodeLabel(b)));
    };
    // Preserve each module group's disclosure state when filtering or parking rerenders the tray.
    const collapsedRemovedModules = new Set();
    const moduleLabels = new Map((graph.modules || []).map((m) => [m.id, m.label || m.id]));
    const moduleRank = (id) => {
      const rank = MODULE_ORDER.indexOf(id);
      return rank < 0 ? MODULE_ORDER.length : rank;
    };
    let trayRenderScheduled = false;
    // Flat, visually ordered list of the node ids currently rendered in the tray. Shift-click
    // ranges follow what the user sees. Expanded categories retain stable relevance/name order;
    // only collapsed breakthrough lists place selected items at the top.
    let trayOrder = [];
    // The item that was focused last; anchor for shift-click range selection.
    let trayFocusId = null;
    const layoutRemovedTray = () => {
      if (!removedCanvas) return;
      removedCanvas.innerHTML = "";
      trayOrder = [];
      const removedNodes = filteredRemovedNodes();
      const groups = new Map();
      removedNodes.forEach((node) => {
        const moduleId = node.module || "other";
        if (!groups.has(moduleId)) groups.set(moduleId, []);
        groups.get(moduleId).push(node);
      });

      Array.from(groups.entries())
        .sort(([a], [b]) => moduleRank(a) - moduleRank(b) || String(moduleLabels.get(a) || a).localeCompare(String(moduleLabels.get(b) || b)))
        .forEach(([moduleId, nodes]) => {
          const group = document.createElement("details");
          group.className = "component-graph-removed-group";
          group.dataset.module = moduleId;
          group.style.setProperty("--module-color", MODULE_COLOR[moduleId] || MODULE_COLOR.other);
          // Search results are expanded temporarily without overwriting the user's choice.
          // Collapsing does NOT hide selected entries: when a collapsed group contains a
          // selection, those entries are rendered next to the summary (see breakthrough list
          // below), so a collapse-all never makes a highlighted item disappear.
          const groupHasSelected = nodes.some((n) => isNodeSelected(n.id));
          group.open = removedSearchTerm.trim() ? true : !collapsedRemovedModules.has(moduleId);
          if (groupHasSelected) group.classList.add("has-selected");
          group.addEventListener("toggle", () => {
            if (removedSearchTerm.trim()) return;
            // The <details> "toggle" event is dispatched ASYNCHRONOUSLY, so the programmatic
            // `group.open = ...` above also produces one after this listener is attached.
            // Acting on that echo would re-render the tray, which builds fresh <details>
            // elements, which emit their own echo -> an endless render loop that froze the
            // page (most visible with "Alle entfernen", where every module group is created
            // at once). Only a state change that the DOM did not already agree with is a
            // genuine user toggle.
            const wantOpen = !collapsedRemovedModules.has(moduleId);
            if (group.open === wantOpen) return; // echo of our own assignment -> ignore
            if (group.open) collapsedRemovedModules.delete(moduleId);
            else collapsedRemovedModules.add(moduleId);
            // Re-render so the breakthrough list appears/disappears with the collapse state.
            if (!trayRenderScheduled) {
              trayRenderScheduled = true;
              requestAnimationFrame(() => { trayRenderScheduled = false; layoutRemovedTray(); });
            }
          });

          const summary = document.createElement("summary");
          summary.className = "component-graph-removed-group-summary";
          const label = moduleLabels.get(moduleId) || moduleId;
          const selCountInGroup = nodes.filter((n) => isNodeSelected(n.id)).length;
          summary.textContent = selCountInGroup > 0
            ? `${label} (${nodes.length}) · ${selCountInGroup} markiert`
            : `${label} (${nodes.length})`;
          // Dragging the group header onto the canvas unparks the entire module.
          summary.draggable = true;
          summary.addEventListener("dragstart", (ev) => {
            ev.dataTransfer.effectAllowed = "move";
            ev.dataTransfer.setData("text/plain", `module:${moduleId}`);
            summary.classList.add("dragging");
          });
          summary.addEventListener("dragend", () => summary.classList.remove("dragging"));
          group.appendChild(summary);

          // When the group is collapsed, its selected entries are still rendered -- directly
          // under the summary, outside the <details> content -- so a selection can never be
          // hidden by collapsing. Expanded groups render the full list as usual.
          const rendered = group.open
            ? nodes
            : nodes.filter((n) => isNodeSelected(n.id)).sort((a, b) =>
                (b.degree || 0) - (a.degree || 0)
                || (b.score || 0) - (a.score || 0)
                || nodeLabel(a).localeCompare(nodeLabel(b)));
          const list = document.createElement("div");
          list.className = group.open
            ? "component-graph-removed-group-list"
            : "component-graph-removed-group-list component-graph-removed-breakthrough";
          rendered.forEach((node) => {
            const item = document.createElement("button");
            item.type = "button";
            item.className = "component-graph-removed-item";
            if (isNodeSelected(node.id)) {
              item.classList.add("selected");
              item.setAttribute("aria-pressed", "true");
            }
            if (node.id === trayFocusId) item.classList.add("focused");
            item.style.setProperty("--module-color", MODULE_COLOR[node.module || "other"] || MODULE_COLOR.other);
            item.draggable = true;
            item.dataset.nodeId = node.id;
            trayOrder.push(node.id);
            item.innerHTML = `<span class="component-graph-removed-name">${node.label || node.shortLabel || node.id}</span><span class="component-graph-removed-meta">Degree ${node.degree || 0}</span>`;
            item.addEventListener("dragstart", (ev) => {
              ev.dataTransfer.effectAllowed = "move";
              ev.dataTransfer.setData("text/plain", node.id);
              item.classList.add("dragging");
            });
            item.addEventListener("dragend", () => item.classList.remove("dragging"));
            // Click semantics inside the panel (the class page is still reachable via the
            // node on the canvas, so a plain click is free to mean "select" here):
            //   plain  -> focus + select only this item
            //   ctrl   -> focus + toggle this item, keep the rest
            //   shift  -> focus + select the visual span from the previous focus to here
            item.addEventListener("click", (ev) => {
              ev.preventDefault();
              // A double-click navigates (see below); its first click must not also run a
              // plain exclusive select, otherwise the selection flickers on the way out.
              if (ev.detail > 1) return;
              if (ev.shiftKey) selectTrayRangeTo(node.id);
              else if (ev.ctrlKey || ev.metaKey) toggleTrayItem(node.id);
              else selectTrayItemExclusively(node.id);
            });
            // Double-click opens the class page -- same gesture as on the canvas.
            item.addEventListener("dblclick", (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              if (node.url) location.href = new URL(node.url, root).href;
            });
            // Right-clicking a tray entry toggles its selection. The node STAYS parked; it is
            // merely highlighted inside this panel until the user adds it back explicitly.
            item.addEventListener("contextmenu", (ev) => {
              ev.preventDefault();
              ev.stopPropagation();
              const el = cy.getElementById(node.id);
              if (!el || el.empty()) return;
              if (el.selected()) el.unselect(); else el.select();
              selectParkedFromTray(node.id);
            });
            list.appendChild(item);
          });
          group.appendChild(list);
          removedCanvas.appendChild(group);
          // A collapsed <details> hides everything after the <summary>, so the breakthrough
          // list is lifted out of the group and placed right behind it in the panel.
          if (!group.open) {
            if (rendered.length) {
              list.style.setProperty("--module-color", MODULE_COLOR[moduleId] || MODULE_COLOR.other);
              removedCanvas.appendChild(list);
            } else {
              list.remove();
            }
          }
        });
      if (removedTitle) removedTitle.textContent = hasUserParkedNode ? "Ausgewählte Klassen" : "Meistgenutzte Klassen";
      const parkedCount = Array.from(userRemoved).length;
      if (removedPanel) {
        removedPanel.hidden = parkedCount === 0;
        // Height is owned by the stylesheet (locked to the canvas height); the item list
        // scrolls internally, so no measuring/growing happens here any more.
        removedPanel.style.minHeight = "";
        removedPanel.style.height = "";
      }
    };
    // ---------- parked-item selection gestures ----------
    // "Focus" is purely a panel concept: the item last interacted with. It is the anchor for
    // shift ranges and is rendered with an outline. It does not imply selection by itself.
    const focusTrayItem = (nodeId) => {
      trayFocusId = nodeId;
      requestAnimationFrame(() => {
        const el = removedCanvas && removedCanvas.querySelector(`[data-node-id="${CSS.escape(nodeId)}"]`);
        if (el && el.scrollIntoView) el.scrollIntoView({ block: "nearest" });
      });
    };
    const afterTraySelectionChange = () => {
      invalidateSelectionCache();
      applySelectionHighlight();
      refreshRemovedUi();
    };
    // Plain click: this item becomes the only selected parked item. Selections on the canvas
    // are left untouched -- the panel and the canvas hold independent selections.
    const selectTrayItemExclusively = (nodeId) => {
      focusTrayItem(nodeId);
      cy.batch(() => {
        cy.nodes(":selected").filter((n) => isParked(n)).unselect();
        const el = cy.getElementById(nodeId);
        if (el && el.nonempty()) el.select();
      });
      afterTraySelectionChange();
    };
    // Ctrl/Cmd click: additive toggle, everything else keeps its state.
    const toggleTrayItem = (nodeId) => {
      focusTrayItem(nodeId);
      const el = cy.getElementById(nodeId);
      if (el && el.nonempty()) { if (el.selected()) el.unselect(); else el.select(); }
      afterTraySelectionChange();
    };
    // Shift click: select the contiguous visual span between the previous focus and this item.
    // Without a previous focus this degrades to an exclusive click.
    const selectTrayRangeTo = (nodeId) => {
      const from = trayOrder.indexOf(trayFocusId);
      const to = trayOrder.indexOf(nodeId);
      if (trayFocusId === null || from < 0 || to < 0) { selectTrayItemExclusively(nodeId); return; }
      const [lo, hi] = from <= to ? [from, to] : [to, from];
      const span = trayOrder.slice(lo, hi + 1);
      focusTrayItem(nodeId);
      cy.batch(() => {
        span.forEach((id) => {
          const el = cy.getElementById(id);
          if (el && el.nonempty()) el.select();
        });
      });
      afterTraySelectionChange();
    };

    // Which parked ids a drag of `nodeId` should unpark:
    //   - dragged item is selected   -> the whole parked selection travels with it
    //   - dragged item is unselected -> only that item
    // All parked node ids belonging to one module group (ignores the text filter, since a
    // module drag means "this whole module", not "the part that currently matches").
    const parkedIdsOfModule = (moduleId) => graph.nodes
      .filter((n) => userRemoved.has(n.id) && (n.module || "other") === moduleId)
      .map((n) => n.id);

    // Dragging a module header: the selection acts as a filter *within* that module.
    //   module has selected items -> only those are unparked, other modules stay untouched
    //   module has no selection    -> the whole module is unparked
    const moduleDragPayload = (moduleId) => {
      const all = parkedIdsOfModule(moduleId);
      const selected = all.filter((id) => isNodeSelected(id));
      return selected.length ? selected : all;
    };

    // Dragging an item: a selected item carries the entire parked selection across all
    // modules; an unselected item travels alone.
    const dragPayloadFor = (nodeId) => {
      if (!isNodeSelected(nodeId)) return [nodeId];
      const sel = selectedParkedIds();
      return sel.length ? sel : [nodeId];
    };
    // Unpark one or many nodes in a single pass, then frame the result.
    // `frame` controls the viewport reaction:
    //   "neighborhood" -- zoom to the restored node and its neighbours (button restores)
    //   "none"         -- leave the viewport alone (drag & drop: the user chose the spot)
    // Every mode additionally opens the view up afterwards if the graph grew beyond it.
    const restoreNodesToMainGraph = (nodeIds, frame = "neighborhood") => {
      const ids = (Array.isArray(nodeIds) ? nodeIds : [nodeIds]).filter((id) => userRemoved.has(id));
      if (!ids.length) return [];
      ids.forEach((id) => userRemoved.delete(id));
      apply(false);
      const restored = cy.collection();
      ids.forEach((id) => {
        const el = cy.getElementById(id);
        if (el && el.nonempty()) restored.merge(el);
      });
      if (restored.nonempty() && frame !== "none") {
        clearHover();
        // A single restored node gets the hover focus treatment; a group would just flicker.
        if (restored.length === 1) applyHover(restored);
        const eles = restored.length === 1
          ? restored.closedNeighborhood().filter((el) => el.style("display") !== "none")
          : restored.filter((el) => el.style("display") !== "none");
        // Never zoom IN past the current level: framing one or two nodes would otherwise fill
        // the whole stage and lose all context. Zooming out to reveal them is fine.
        const target = fitTargetFor(eles, 80);
        if (target && target.zoom > cy.zoom()) {
          cy.animate({
            zoom: cy.zoom(),          // hold the current level
            center: { eles },         // just bring the arrivals into view
            duration: reduceMotion ? 0 : 260,
            easing: "ease-out-cubic"
          });
        } else {
          cy.animate({ fit: { eles, padding: 80 }, duration: reduceMotion ? 0 : 260, easing: "ease-out-cubic" });
        }
      }
      // The arrivals are pushed into place by the springs over the next moment, so a single
      // immediate check is not enough -- watch for a short while and widen as they spread.
      startFocusFollow();
      return ids;
    };
    const restoreNodeToMainGraph = (nodeId) => restoreNodesToMainGraph([nodeId]);
    const sim = createSimulation(cy);
    const anchorSlider = host.querySelector("[data-graph-anchor-force]");
    const anchorOutput = host.querySelector("[data-graph-anchor-output]");
    if (anchorSlider) {
      anchorSlider.addEventListener("input", () => {
        const percent = Number(anchorSlider.value);
        sim.setAnchorScale(percent / 100);
        if (anchorOutput) anchorOutput.value = `${percent}%`;
        sim.start();
      });
    }
    // ---------- unified focus controller ----------
    // Viewport framing is derived from a single explicit `focus` state instead of the
    // previous mix of auto-fit loops, reveal loops, and per-gesture zoom calls. There are
    // exactly three kinds of focus, and each one has exactly one framing rule:
    //   background -> fit every visible element
    //   module     -> fit that module's visible descendants
    //   node       -> keep the node centred; choose zoom so all selected visible nodes fit
    // The same rule is re-applied continuously while the layout settles, so growth/removal/
    // dragging never need a separate widen-only code path.
    let focus = { type: "background" };
    let focusFollowActive = false;
    let focusFollowTimer = null;
    let focusFollowDeadline = 0;

    // Our own fit animations emit "zoom"/"pan" events on every frame. Without this guard a
    // manual-gesture listener would cancel the follow loop on its own first frame.
    let viewportGuardUntil = 0;
    const now = () => (typeof performance !== "undefined" && performance.now ? performance.now() : Date.now());
    const isProgrammaticViewportChange = () => now() < viewportGuardUntil;

    const FOCUS_FIT_DURATION = 360;
    const FOCUS_FOLLOW_INTERVAL = 260;
    // How long the loop keeps chasing the still-settling force layout after a visibility change.
    const FOCUS_FOLLOW_WINDOW = 3000;
    const FOCUS_ZOOM_EPS = 0.02;   // 2% relative zoom change
    const FOCUS_PAN_EPS = 12;      // px

    const visibleElements = () => cy.elements().filter((el) => el.style("display") !== "none");

    const fitTargetFor = (eles, padding) => {
      const bb = eles.boundingBox();
      if (!bb || bb.w <= 0 || bb.h <= 0) return null;
      const w = cy.width(), h = cy.height();
      if (w <= 0 || h <= 0) return null;
      let zoom = Math.min((w - 2 * padding) / bb.w, (h - 2 * padding) / bb.h);
      zoom = Math.max(cy.minZoom(), Math.min(cy.maxZoom(), zoom));
      return {
        zoom,
        pan: { x: (w - zoom * (bb.x1 + bb.x2)) / 2, y: (h - zoom * (bb.y1 + bb.y2)) / 2 }
      };
    };

    // Resolves the current focus to the element set and padding that define its framing.
    // Returns null when the focus target no longer exists (e.g. a parked/removed node) --
    // callers fall back to the background focus in that case.
    const framingFor = (f) => {
      if (f.type === "module") {
        const mod = cy.getElementById(f.id);
        if (!mod || mod.empty()) return null;
        const visible = mod.descendants().filter((n) => !isContainer(n) && n.style("display") !== "none");
        if (visible.empty()) return null;
        return { eles: visible, padding: 54, center: null };
      }
      if (f.type === "node") {
        const node = cy.getElementById(f.id);
        if (!node || node.empty() || node.style("display") === "none") return null;
        // All visible selected nodes (plus the focused node itself) must fit; the focused
        // node stays centred rather than the bounding box's own centre.
        const selected = cy.nodes(":selected").filter((n) => !isContainer(n) && n.style("display") !== "none");
        const eles = selected.length > 0 ? selected.union(node) : node;
        return { eles, padding: 80, center: node };
      }
      const vis = visibleElements();
      if (vis.empty()) return null;
      return { eles: vis, padding: 40, center: null };
    };

    // Computes the pan that keeps `center` at the viewport centre for a given zoom.
    const panForCenteredZoom = (center, zoom) => {
      const p = center.position ? center.position() : center.renderedMidpoint();
      const w = cy.width(), h = cy.height();
      return { x: w / 2 - zoom * p.x, y: h / 2 - zoom * p.y };
    };

    // Zoom out around a rendered pointer position just far enough to include `eles`. Keeping
    // the model point under the pointer fixed makes a hold preview widen in place instead of
    // pulling the node away from the user's mouse.
    const zoomOutAroundPointerToFit = (eles, pointer, padding = 48) => {
      if (!eles || eles.empty() || !pointer) return false;
      const bb = eles.boundingBox();
      const w = cy.width(), h = cy.height();
      const currentZoom = cy.zoom();
      if (!bb || currentZoom <= 0 || w <= 2 * padding || h <= 2 * padding) return false;
      const pan = cy.pan();
      const anchor = { x: (pointer.x - pan.x) / currentZoom, y: (pointer.y - pan.y) / currentZoom };
      const limits = [];
      const addLimit = (available, distance) => {
        if (distance > 0) limits.push(available / distance);
      };
      addLimit(pointer.x - padding, anchor.x - bb.x1);
      addLimit(w - padding - pointer.x, bb.x2 - anchor.x);
      addLimit(pointer.y - padding, anchor.y - bb.y1);
      addLimit(h - padding - pointer.y, bb.y2 - anchor.y);
      if (!limits.length) return false;
      let zoom = Math.min(currentZoom, ...limits);
      zoom = Math.max(cy.minZoom(), Math.min(cy.maxZoom(), zoom));
      if (zoom >= currentZoom * (1 - FOCUS_ZOOM_EPS)) return false;
      const targetPan = { x: pointer.x - zoom * anchor.x, y: pointer.y - zoom * anchor.y };
      const duration = reduceMotion ? 0 : FOCUS_FIT_DURATION;
      stopFocusFollow();
      viewportGuardUntil = Math.max(viewportGuardUntil, now() + duration + 150);
      cy.stop(false, false);
      if (duration > 0) cy.animate({ zoom, pan: targetPan, duration, easing: "ease-out-cubic" });
      else { cy.zoom(zoom); cy.pan(targetPan); }
      return true;
    };

    // Applies the current focus's framing. Returns true if the viewport moved (or would need
    // to), so the follow loop can tell when the layout has settled.
    const applyFocusFraming = (animated = true, onlyIfMeaningful = false) => {
      let framing = framingFor(focus);
      if (!framing && focus.type !== "background") {
        focus = { type: "background" };
        framing = framingFor(focus);
      }
      if (!framing) return false;
      const { eles, padding, center } = framing;
      let target;
      if (center) {
        // Node focus is symmetric around the focused node, not around the selected set's
        // geometric centre. This keeps even a strongly one-sided selection fully visible.
        const bb = eles.boundingBox();
        const cp = center.position();
        const halfW = cy.width() / 2 - padding;
        const halfH = cy.height() / 2 - padding;
        if (!bb || halfW <= 0 || halfH <= 0) return false;
        const horizontalExtent = Math.max(cp.x - bb.x1, bb.x2 - cp.x, 1);
        const verticalExtent = Math.max(cp.y - bb.y1, bb.y2 - cp.y, 1);
        let zoom = Math.min(halfW / horizontalExtent, halfH / verticalExtent);
        zoom = Math.max(cy.minZoom(), Math.min(cy.maxZoom(), zoom));
        target = { zoom, pan: panForCenteredZoom(center, zoom) };
      } else {
        target = fitTargetFor(eles, padding);
        if (!target) return false;
      }
      if (onlyIfMeaningful) {
        const z = cy.zoom(), p = cy.pan();
        const zoomOff = Math.abs(target.zoom - z) / Math.max(z, 1e-6);
        const panOff = Math.hypot(target.pan.x - p.x, target.pan.y - p.y);
        if (zoomOff < FOCUS_ZOOM_EPS && panOff < FOCUS_PAN_EPS) return false;
      }
      const duration = animated && !reduceMotion ? FOCUS_FIT_DURATION : 0;
      viewportGuardUntil = Math.max(viewportGuardUntil, now() + duration + 150);
      if (duration > 0) {
        cy.stop(false, false);
        cy.animate({ zoom: target.zoom, pan: target.pan, duration, easing: "ease-out-cubic" });
      } else {
        cy.zoom(target.zoom);
        cy.pan(target.pan);
      }
      return true;
    };

    const stopFocusFollow = () => {
      focusFollowActive = false;
      focusFollowDeadline = 0;
      if (focusFollowTimer) { clearTimeout(focusFollowTimer); focusFollowTimer = null; }
    };

    // Re-applies the current focus's framing repeatedly while the force layout is still
    // settling (e.g. after a park/restore/reveal), stopping once two passes in a row move
    // nothing. Superseded by simply calling setFocus() again, which restarts this loop.
    const startFocusFollow = () => {
      stopFocusFollow();
      focusFollowActive = true;
      focusFollowDeadline = now() + (reduceMotion ? 400 : FOCUS_FOLLOW_WINDOW);
      let idleTicks = 0;
      const tick = () => {
        if (!focusFollowActive) return;
        const moved = applyFocusFraming(true, true);
        idleTicks = moved ? 0 : idleTicks + 1;
        if (idleTicks >= 2) { stopFocusFollow(); return; }
        if (now() >= focusFollowDeadline) {
          focusFollowTimer = setTimeout(() => {
            if (!focusFollowActive) return;
            applyFocusFraming(true, true);
            stopFocusFollow();
          }, reduceMotion ? 60 : FOCUS_FOLLOW_INTERVAL);
          return;
        }
        focusFollowTimer = setTimeout(tick, reduceMotion ? 120 : FOCUS_FOLLOW_INTERVAL);
      };
      requestAnimationFrame(tick);
    };

    // Sets the focus and immediately (re-)starts the follow loop so the framing tracks the
    // layout as it settles. This is the single entry point every click/park/restore handler
    // now calls instead of choosing between fit/reveal/auto-fit helpers.
    const setFocus = (next, animated = true) => {
      focus = next;
      applyFocusFraming(animated, false);
      startFocusFollow();
    };


    const apply = (recenter) => {
      // The interactive map intentionally opens on its curated hub subset. With controls
      // removed, this is the sole visibility policy; module clicks only change the viewport.
      cy.batch(() => {
        cy.nodes().forEach((n) => {
          if (isContainer(n)) return; // containers are derived below from leaf children
          // Parked stays parked, even when selected: a selected parked node is highlighted in
          // the tray instead of being returned to the canvas.
          n.style("display", userRemoved.has(n.id()) ? "none" : "element"); // show the full graph, minus anything the user dragged out
        });
        // Resolve nested compound containers bottom-up.
        cy.nodes().filter((n) => n.data("kind") === "namespace").forEach((p) => {
          const any = p.children().some((c) => c.style("display") !== "none");
          p.style("display", any ? "element" : "none");
        });
        cy.nodes().filter(isModule).forEach((p) => {
          const any = p.children().some((c) => c.style("display") !== "none");
          p.style("display", any ? "element" : "none");
        });
        cy.edges().forEach((e) => {
          const visibleEnds = e.source().style("display") !== "none" && e.target().style("display") !== "none";
          e.style("display", visibleEnds ? "element" : "none");
        });

      });

      sim.seed(recenter);
      // The focus follow loop (started by the caller after a park) performs its own fits.
      // Firing an extra one here raced against it: two overlapping fit animations toward
      // slightly different targets are exactly what reads as a jump.
      if (recenter && !focusFollowActive) requestAnimationFrame(() => applyFocusFraming(true));

      if (reduceMotion) {
        sim.settleOnce(90);
      } else {
        sim.start();
      }

      if (caption) {
        const shown = cy.nodes().filter((n) => !isContainer(n) && n.style("display") !== "none").length;
        caption.textContent = `Federphysik-Karte · Vollständiger Graph · ${shown} Komponenten · Modul anklicken zum Zentrieren` +
          (reduceMotion ? "" : " · Ziehen verdrängt nahe Komponenten");
      }
      refreshRemovedUi();
    };

    // Keep the auxiliary UI in sync with userRemoved after every graph update.
    const refreshRemovedUi = () => {
      if (restoreButton) {
        const selectedLeaves = cy.nodes(":selected").filter((n) => !isContainer(n) && n.style("display") !== "none");
        const visibleLeafCount = cy.nodes().filter((n) => !isContainer(n) && n.style("display") !== "none").length;
        restoreButton.hidden = visibleLeafCount === 0;
        if (selectedLeaves.length > 0) {
          restoreButton.textContent = selectedLeaves.length <= 1
            ? "Markierte entfernen"
            : `Markierte entfernen (${selectedLeaves.length})`;
        } else {
          restoreButton.textContent = visibleLeafCount <= 1
            ? "Alle entfernen"
            : `Alle entfernen (${visibleLeafCount})`;
        }
      }
      if (keepSelectedButton) {
        // Only meaningful while something is selected and there is at least one unselected
        // node on the canvas that could be parked.
        const selectedLeaves = cy.nodes(":selected").filter((n) => !isContainer(n) && n.style("display") !== "none");
        const unselectedVisible = cy.nodes().filter((n) => !isContainer(n) && n.style("display") !== "none" && !n.selected());
        const show = selectedLeaves.length > 0 && unselectedVisible.length > 0;
        keepSelectedButton.hidden = !show;
        if (show) {
          keepSelectedButton.textContent = unselectedVisible.length <= 1
            ? "Nicht-Markierte entfernen"
            : `Nicht-Markierte entfernen (${unselectedVisible.length})`;
        }
      }
      if (collapseAllButton) {
        const parkedModules = Array.from(new Set(
          graph.nodes.filter((n) => userRemoved.has(n.id)).map((n) => n.module || "other")
        ));
        collapseAllButton.hidden = parkedModules.length === 0;
        collapseAllButton.disabled = !!removedSearchTerm.trim(); // search forces all groups open
        const everyCollapsed = parkedModules.length > 0 && parkedModules.every((m) => collapsedRemovedModules.has(m));
        // The triangle points down when groups are open (click = collapse) and right when they
        // are collapsed (click = expand), mirroring the per-group disclosure markers.
        collapseAllButton.classList.toggle("collapsed", everyCollapsed);
        collapseAllButton.setAttribute("aria-expanded", everyCollapsed ? "false" : "true");
        const collapseLabel = everyCollapsed ? "Alle ausklappen" : "Alle einklappen";
        collapseAllButton.setAttribute("aria-label", collapseLabel);
        collapseAllButton.title = collapseLabel;
      }
      if (restoreFilteredButton) {
        const filteredCount = filteredRemovedNodes().length;
        const selCount = selectedParkedIds().length;
        restoreFilteredButton.hidden = userRemoved.size === 0;
        // A selection inside the panel takes precedence: the button then adds exactly the
        // highlighted entries back to the canvas.
        if (selCount > 0) {
          restoreFilteredButton.disabled = false;
          restoreFilteredButton.classList.add("has-selected");
          restoreFilteredButton.textContent = selCount <= 1
            ? "Auswahl hinzufügen"
            : `Auswahl hinzufügen (${selCount})`;
        } else {
          restoreFilteredButton.disabled = filteredCount === 0;
          restoreFilteredButton.classList.remove("has-selected");
          restoreFilteredButton.textContent = removedSearchTerm.trim()
            ? (filteredCount <= 1 ? "Treffer hinzufügen" : `Treffer hinzufügen (${filteredCount})`)
            : (userRemoved.size <= 1 ? "Alle hinzufügen" : `Alle hinzufügen (${userRemoved.size})`);
        }
      }
      layoutRemovedTray();
    };

    const boot = () => {
      if (stage.clientWidth <= 0 || stage.clientHeight <= 0) {
        throw new Error(`Graph container has no size: ${stage.clientWidth}x${stage.clientHeight}`);
      }
      apply(true);
    };

    requestAnimationFrame(() => {
      try { boot(); } catch (_) { requestAnimationFrame(boot); }
    });

    if (restoreButton) {
      restoreButton.addEventListener("click", () => {
        const selectedLeaves = cy.nodes(":selected").filter((n) => !isContainer(n) && n.style("display") !== "none");
        const targetLeaves = selectedLeaves.length > 0 ? selectedLeaves : cy.nodes().filter((n) => !isContainer(n) && n.style("display") !== "none");
        if (targetLeaves.empty()) return;
        targetLeaves.forEach((n) => userRemoved.add(n.id()));
        // Parked nodes keep their selection: they stay marked inside the panel, so the user
        // can immediately act on the same set again (e.g. add it back).
        cy.nodes().filter((n) => isContainer(n)).unselect();
        hasUserParkedNode = true;
        clearHover();
        startFocusFollow();
        apply(true);
      });
    }
    if (keepSelectedButton) {
      // Park every visible component that is NOT selected, keeping the selection on the canvas.
      keepSelectedButton.addEventListener("click", () => {
        const selectedLeaves = cy.nodes(":selected").filter((n) => !isContainer(n) && n.style("display") !== "none");
        if (selectedLeaves.empty()) return;
        const victims = cy.nodes().filter((n) => !isContainer(n) && n.style("display") !== "none" && !n.selected());
        if (victims.empty()) return;
        victims.forEach((n) => userRemoved.add(n.id()));
        hasUserParkedNode = true;
        clearHover();
        startFocusFollow();
        apply(true);
      });
    }
    if (collapseAllButton) {
      // Collapse every module group in the tray. Selected entries break through the collapse
      // and stay visible (rendered outside the collapsed <details>), so nothing marked is lost.
      collapseAllButton.addEventListener("click", () => {
        const allCollapsed = Array.from(new Set(
          graph.nodes.filter((n) => userRemoved.has(n.id)).map((n) => n.module || "other")
        ));
        if (allCollapsed.length === 0) return;
        const everyCollapsed = allCollapsed.every((m) => collapsedRemovedModules.has(m));
        if (everyCollapsed) allCollapsed.forEach((m) => collapsedRemovedModules.delete(m));
        else allCollapsed.forEach((m) => collapsedRemovedModules.add(m));
        refreshRemovedUi();
      });
    }
    if (removedSearch) {
      removedSearch.addEventListener("input", () => {
        removedSearchTerm = removedSearch.value || "";
        refreshRemovedUi();
      });
    }
    if (restoreFilteredButton) {
      restoreFilteredButton.addEventListener("click", () => {
        // With entries highlighted in the panel, only those are added back; otherwise the
        // current filter result (or everything) is restored as before.
        const selIds = selectedParkedIds();
        const toRestore = selIds.length > 0 ? selIds : filteredRemovedNodes().map((n) => n.id);
        if (toRestore.length === 0) return;
        toRestore.forEach((id) => userRemoved.delete(id));
        clearHover();
        apply(true);
        // Adding a batch back can grow the graph well past the current frame; keep widening
        // until the newcomers have settled inside it.
        startFocusFollow();
        applySelectionHighlight();
      });
    }
    if (removedCanvas) {
      removedCanvas.addEventListener("dragover", (ev) => {
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
      });
      stage.addEventListener("dragover", (ev) => {
        if (!ev.dataTransfer.types.includes("text/plain")) return;
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
      });
      stage.addEventListener("drop", (ev) => {
        const payload = ev.dataTransfer.getData("text/plain");
        if (!payload) return;
        ev.preventDefault();
        const rect = stage.getBoundingClientRect();
        const rendered = { x: ev.clientX - rect.left, y: ev.clientY - rect.top };
        // Payload is either "module:<id>" (drag of a group header) or a plain node id.
        const ids = payload.startsWith("module:")
          ? moduleDragPayload(payload.slice("module:".length))
          : dragPayloadFor(payload);
        // Drag & drop places the nodes exactly where the pointer released them, so the
        // viewport must stay put -- reframing here is what yanked the view in too close.
        const unparked = restoreNodesToMainGraph(ids, "none");
        if (!unparked.length) return;
        // Moving an item from the panel to the canvas is a pure relocation: it must not
        // change the selection status. A marked item stays marked after it lands, an
        // unmarked one stays unmarked. Marks on items that stayed parked are untouched.
        // Drop point is the anchor; multiple nodes are fanned around it so they do not
        // all land on the exact same coordinate and explode apart in the first frame.
        const R = 26;
        unparked.forEach((id, i) => {
          const el = cy.getElementById(id);
          if (!el || el.empty()) return;
          const a = (2 * Math.PI * i) / Math.max(1, unparked.length);
          const pos = unparked.length === 1
            ? rendered
            : { x: rendered.x + Math.cos(a) * R, y: rendered.y + Math.sin(a) * R };
          el.renderedPosition(pos);
          sim.grab(id);
          sim.free(id);
        });
        if (reduceMotion) sim.settleOnce(60); else sim.start();
        startFocusFollow();
      });
    }

    cy.on("select unselect", "node", () => {
      invalidateSelectionCache();
      applySelectionHighlight();
      refreshRemovedUi();
    });

    // hover neighborhood focus (paused while dragging so it doesn't fight the drag)
    let isDraggingAny = false;

    // Track the pointer's last known position (relative to the stage) so we can tell,
    // at the moment of release, whether the mouse itself — not the node — is outside the canvas.
    let lastPointerInStage = { x: stage.clientWidth / 2, y: stage.clientHeight / 2 };
    let pointerInsideStage = true;
    stage.addEventListener("pointermove", (ev) => {
      const rect = stage.getBoundingClientRect();
      lastPointerInStage = { x: ev.clientX - rect.left, y: ev.clientY - rect.top };
      pointerInsideStage = true;
    });
    stage.addEventListener("pointerleave", () => { pointerInsideStage = false; });
    // Pointer events are captured by the dragged element in most browsers, so listen on the
    // window too while dragging to reliably detect the pointer leaving the stage bounds.
    window.addEventListener("pointermove", (ev) => {
      if (!isDraggingAny) return;
      const rect = stage.getBoundingClientRect();
      lastPointerInStage = { x: ev.clientX - rect.left, y: ev.clientY - rect.top };
      pointerInsideStage = ev.clientX >= rect.left && ev.clientX <= rect.right && ev.clientY >= rect.top && ev.clientY <= rect.bottom;
    });
    // ---------- selection highlight ----------
    // Parked nodes MAY be selected, but they stay in the tray: their selection is expressed by
    // a highlight inside the parked-items panel, not by returning to the canvas. Container
    // boxes are never a valid selection target.
    const isParked = (n) => userRemoved.has(n.id());
    const purgeParkedSelection = () => {
      const stale = cy.nodes(":selected").filter((n) => isContainer(n));
      if (stale.nonempty()) stale.unselect();
    };
    // The canvas highlight only ever concerns nodes that are actually on the canvas.
    const liveSelection = () => {
      purgeParkedSelection();
      return cy.nodes(":selected").filter((n) => !isContainer(n) && !isParked(n));
    };
    const hasSelection = () => liveSelection().nonempty();

    // When a selection exists, exactly the selected nodes (plus the edges strictly between
    // them) stay lit; everything else is faded. With no selection, nothing is faded.
    const applySelectionHighlight = () => {
      const sel = liveSelection();
      if (sel.empty()) {
        cy.elements().removeClass("faded focus sel-highlight");
        // Every selection change funnels through here, so this is the one place that has to
        // bring the UML detail levels back in line -- marquee, tray, keyboard and click paths
        // all get it for free.
        syncAllDetail();
        return;
      }
      cy.batch(() => {
        cy.elements().removeClass("focus hover-root hover-neighbor hover-edge sel-highlight");
        cy.elements().addClass("faded");
        sel.removeClass("faded").addClass("focus sel-highlight");
        sel.edgesWith(sel).removeClass("faded").addClass("focus sel-highlight");
      });
      syncAllDetail();
    };

    // Wire the tray's right-click hook now that the highlight helper exists. Selecting a parked
    // item does NOT unpark it -- only the canvas highlight and the tray rendering are refreshed.
    selectParkedFromTray = () => {
      applySelectionHighlight();
      refreshRemovedUi();
    };

    // ---------- UML level of detail, driven by selection + hover ----------
    // Level is never stored per node: it is recomputed from the two pieces of interaction
    // state below, so the display can never drift out of sync with what is selected.
    let umlHoverId = null;
    // Nodes currently inside the marquee band. They peek at level 2 for the duration of the
    // drag so the user can read what the band is about to capture, then fall back to whatever
    // their selection state dictates once the band is gone.
    let umlPeek = new Set();
    // While a selected component is held with the primary button, show the next frontier at
    // level 2. The set is preview-only: it never changes the selection and is cleared when
    // the pointer is released or cancelled.
    let frontierHoldPeek = new Set();

    // Bring one node's caption and geometry in line with its current state.
    const syncNodeDetail = (n) => {
      if (isContainer(n)) return;
      const id = n.id();
      const want = levelFor(n.selected(), umlHoverId === id || umlPeek.has(id) || frontierHoldPeek.has(id));
      if ((n.data("uml") || 0) === want) return;
      const raw = graph.nodesById.get(id) || n.data();
      const text = umlLabelFor(raw, want);
      n.data({ uml: want, label: text, ...(umlBoxFor(text, want) || { umlW: null, umlH: null, umlTextW: null }) });
      // The physics loop writes width/height as inline styles, which outrank the stylesheet;
      // expanded boxes must shed them, collapsed ones need them back.
      if (want) n.removeStyle("width height font-size");
      else sim.sizeNodes();
    };

    // Reconcile every visible component. Cheap enough to run on each selection/hover change,
    // and it keeps a single source of truth for the level.
    const syncAllDetail = () => {
      cy.batch(() => {
        cy.nodes().forEach((n) => {
          if (!isContainer(n) && n.style("display") !== "none") syncNodeDetail(n);
        });
      });
    };

    const clearHover = () => {
      cy.elements().removeClass("faded focus hover-root hover-neighbor hover-edge");
      // A cleared hover must not wipe an active selection highlight.
      applySelectionHighlight();
    };
    const applyHover = (n) => {
      cy.elements().removeClass("faded focus hover-root hover-neighbor hover-edge");
      cy.elements().addClass("faded");
      const neighborhood = n.neighborhood();
      n.removeClass("faded").addClass("focus hover-root");
      neighborhood.removeClass("faded");
      neighborhood.nodes().addClass("focus hover-neighbor");
      neighborhood.edges().addClass("focus hover-edge");
    };
    cy.on("mouseover", "node", (e) => {
      if (isDraggingAny) return;
      const n = e.target;
      if (isContainer(n)) return;
      // Hover always raises THIS node to the full member list, whether or not a selection
      // exists -- the detail level and the fade highlight are independent concerns.
      if (umlHoverId !== n.id()) { umlHoverId = n.id(); syncAllDetail(); }
      // An explicit selection outranks transient hover for the FADE highlight: while
      // something is selected the highlight must show the selection and nothing else.
      if (hasSelection()) return;
      applyHover(n);
    });
    cy.on("mouseout", "node", (e) => {
      const n = e.target;
      if (!isContainer(n) && umlHoverId === n.id()) { umlHoverId = null; syncAllDetail(); }
      if (!isDraggingAny) clearHover();
    });

    // drag = force feedback: grabbed node pins to pointer, springs pull its neighbors live
    // Leaves currently held because their module/namespace box is being dragged.
    let containerDragLeaves = null;
    // Cytoscape may emit tiny drag movements during an otherwise stationary click. Require a
    // real pointer displacement before entering drag mode.
    const NODE_DRAG_THRESHOLD = 5;
    let pendingGrab = null;
    // Leaves moving together because the grabbed node was part of a multi-node selection.
    let coDragLeaves = null;
    // Selected leaves that Cytoscape does NOT move on its own during the current drag, plus
    // the reference node whose motion they copy. Cytoscape co-drags the selection only when a
    // *selected leaf* is grabbed; a container drag moves just its own descendants. These
    // "passengers" close that gap so any left-drag translates the whole selection uniformly.
    let dragPassengers = null;
    let dragReference = null;
    let dragLastRefPos = null;

    // Everything that should travel with the pointer: the visible, unparked selection.
    const uniformDragSet = () => cy.nodes(":selected")
      .filter((c) => !isContainer(c) && c.style("display") !== "none" && !isParked(c));

    // `moved` is the collection Cytoscape already translates by itself.
    const armPassengers = (reference, moved) => {
      const movedIds = new Set(moved.map((c) => c.id()));
      const rest = uniformDragSet().filter((c) => !movedIds.has(c.id()));
      if (rest.empty() || !reference || reference.empty()) { dragPassengers = null; return; }
      dragPassengers = rest;
      dragReference = reference;
      dragLastRefPos = { ...reference.position() };
      dragPassengers.forEach((c) => { sim.grab(c.id()); c.addClass("dragging"); });
    };

    // Apply the reference node's per-frame delta to every passenger.
    cy.on("drag", "node", () => {
      if (!dragPassengers || !dragReference || dragReference.empty()) return;
      const cur = dragReference.position();
      const dx = cur.x - dragLastRefPos.x;
      const dy = cur.y - dragLastRefPos.y;
      if (dx === 0 && dy === 0) return;
      dragLastRefPos = { x: cur.x, y: cur.y };
      cy.batch(() => dragPassengers.forEach((c) => {
        const p = c.position();
        c.position({ x: p.x + dx, y: p.y + dy });
      }));
    });

    const releasePassengers = () => {
      if (!dragPassengers) return;
      dragPassengers.forEach((c) => { sim.free(c.id()); c.removeClass("dragging"); });
      dragPassengers = null;
      dragReference = null;
      dragLastRefPos = null;
    };

    const beginNodeDrag = (n) => {
      if (!n || n.empty() || isDraggingAny) return;
      isDraggingAny = true;
      n.addClass("dragging");
      if (focus.type === "background" ||
          (focus.type === "node" && focus.id === n.id()) ||
          (isContainer(n) && focus.type === "module" && focus.id === n.id())) {
        startFocusFollow();
      }
      if (isContainer(n)) {
        containerDragLeaves = n.descendants().filter((c) => !isContainer(c) && c.style("display") !== "none");
        if (containerDragLeaves.empty()) { containerDragLeaves = null; isDraggingAny = false; n.removeClass("dragging"); return; }
        containerDragLeaves.forEach((c) => sim.grab(c.id()));
        armPassengers(containerDragLeaves.first(), containerDragLeaves);
        if (reduceMotion) sim.start();
        return;
      }
      coDragLeaves = n.selected() ? uniformDragSet() : null;
      if (coDragLeaves && coDragLeaves.length > 1) {
        coDragLeaves.forEach((c) => { sim.grab(c.id()); c.addClass("dragging"); });
      } else {
        coDragLeaves = null;
        sim.grab(n.id());
      }
      armPassengers(n, coDragLeaves || cy.collection().merge(n));
      applyHover(n);
      if (reduceMotion) sim.start();
    };

    cy.on("grab", "node", (e) => {
      const oe = e.originalEvent || {};
      pendingGrab = {
        node: e.target,
        x: Number.isFinite(oe.clientX) ? oe.clientX : lastPointerInStage.x,
        y: Number.isFinite(oe.clientY) ? oe.clientY : lastPointerInStage.y
      };
    });

    cy.on("drag", "node", (e) => {
      if (!pendingGrab || pendingGrab.node.id() !== e.target.id()) return;
      const oe = e.originalEvent || {};
      const x = Number.isFinite(oe.clientX) ? oe.clientX : lastPointerInStage.x;
      const y = Number.isFinite(oe.clientY) ? oe.clientY : lastPointerInStage.y;
      if (Math.hypot(x - pendingGrab.x, y - pendingGrab.y) < NODE_DRAG_THRESHOLD) return;
      const n = pendingGrab.node;
      pendingGrab = null;
      beginNodeDrag(n);
    });

    // Removal decision is based on the mouse position at release time, not the node's
    // position — a node can be dragged far while the cursor (and thus the drop point) stays
    // inside the canvas, and should NOT be removed in that case.
    const isPointerOutsideCanvas = () => !pointerInsideStage
      || lastPointerInStage.x < 0 || lastPointerInStage.y < 0
      || lastPointerInStage.x > stage.clientWidth || lastPointerInStage.y > stage.clientHeight;

    cy.on("free", "node", (e) => {
      const n = e.target;
      pendingGrab = null;
      // No movement crossed the threshold: this was a click. Cytoscape has already released
      // its native grab here, and our simulation/drag mode was never entered.
      if (!isDraggingAny) { n.removeClass("dragging"); return; }
      if (isContainer(n)) {
        // Release every leaf that was held on behalf of this box and let the springs take over.
        isDraggingAny = false;
        n.removeClass("dragging");
        if (containerDragLeaves) {
          containerDragLeaves.forEach((c) => sim.free(c.id()));
          containerDragLeaves = null;
        }
        releasePassengers();
        if (reduceMotion) sim.settleOnce(60); else sim.start();
        return;
      }
      isDraggingAny = false;
      n.removeClass("dragging");
      // Passengers exclude the grabbed node itself, so merge it back in for the park path.
      const movedTogether = coDragLeaves || (dragPassengers ? dragPassengers.union(n) : null);
      if (coDragLeaves) {
        coDragLeaves.forEach((c) => { sim.free(c.id()); c.removeClass("dragging"); });
        coDragLeaves = null;
      } else {
        sim.free(n.id());
      }
      releasePassengers();
      clearHover();

      // Removed only when the mouse itself was outside the canvas at the moment of release.
      if (isPointerOutsideCanvas()) {
        // The tray now scrolls, so it no longer has a capacity limit — every drag-out parks.
        // Dragging a whole selection out parks the entire group, matching what was moved.
        if (movedTogether) movedTogether.forEach((c) => userRemoved.add(c.id()));
        else userRemoved.add(n.id());
        // The nodes keep their selection and continue to be marked inside the panel.
        hasUserParkedNode = true;
        applySelectionHighlight();
        // Order matters: arm the auto-fit loop first so apply() does not additionally
        // schedule its own competing fit for the same park.
        startFocusFollow();
        apply(true);
        return;
      }

      if (reduceMotion) {
        sim.settleOnce(60);
      }
    });

    // A module box is a navigational target: click it to center and zoom to its visible hubs.
    // Left-clicking a module/namespace box selects its members only. Zooming into the module
    // is a double-click gesture (see dbltap below) so single click stays a pure selection action.
    // The handler is registered after frontierNode/selectableNode exist (see below), so the
    // actual work lives in selectContainerMembers, defined further down.
    // Delay the single-click action briefly so the first half of a double-click cannot select
    // every member. Detect the second tap here instead of waiting for Cytoscape's dbltap event;
    // this makes module zoom react as soon as the second click arrives.
    // Single click selects the box members, double click zooms and must NOT leave a member
    // selection behind. Timing alone is not enough: the first click may already have committed
    // its selection before the second arrives (and Cytoscape additionally selects the box's
    // descendants on its own). So the second tap explicitly RESTORES the selection snapshot
    // taken before the first tap, which undoes both effects, and only then zooms.
    const CONTAINER_DBL_MS = 500;
    let pendingContainerTap = null;
    let containerTapSnapshot = null;

    const canvasSelectionIds = () =>
      new Set(cy.nodes(":selected").filter((c) => !isParked(c)).map((c) => c.id()));

    const restoreCanvasSelection = (ids) => {
      cy.batch(() => {
        cy.nodes(":selected").forEach((c) => { if (!isParked(c) && !ids.has(c.id())) c.unselect(); });
        ids.forEach((id) => {
          const c = cy.getElementById(id);
          if (c && c.nonempty() && !c.selected()) c.select();
        });
      });
    };

    // Capture selection before Cytoscape applies its compound-node tap selection. A plain
    // namespace click is navigation only and must leave the previous leaf selection intact.
    cy.on("tapstart", "node[kind = 'module'], node[kind = 'namespace']", () => {
      containerTapSnapshot = canvasSelectionIds();
    });

    cy.on("tap", "node[kind = 'module'], node[kind = 'namespace']", (e) => {
      if (e.originalEvent) e.originalEvent.preventDefault();
      const n = e.target;
      const mods = e.originalEvent || {};

      if (n.data("kind") === "namespace" && !mods.shiftKey && !mods.ctrlKey && !mods.metaKey && !mods.altKey) {
        if (pendingContainerTap) {
          clearTimeout(pendingContainerTap.timer);
          pendingContainerTap = null;
        }
        restoreCanvasSelection(containerTapSnapshot || canvasSelectionIds());
        n.unselect();
        applySelectionHighlight();
        refreshRemovedUi();
        setFocus({ type: "module", id: n.id() });
        containerTapSnapshot = null;
        return;
      }

      const now = performance.now();
      setFocus({ type: "module", id: n.id() });

      if (pendingContainerTap && pendingContainerTap.id === n.id() && now - pendingContainerTap.at <= CONTAINER_DBL_MS) {
        clearTimeout(pendingContainerTap.timer);
        const before = pendingContainerTap.before;
        pendingContainerTap = null;
        // Undo whatever the first click (or Cytoscape) selected -- a zoom changes the viewport
        // only, never the selection.
        restoreCanvasSelection(before);
        n.unselect();
        applySelectionHighlight();
        refreshRemovedUi();
        setFocus({ type: "module", id: n.id() });
        return;
      }

      if (pendingContainerTap) clearTimeout(pendingContainerTap.timer);
      const modifierState = { shiftKey: !!mods.shiftKey, ctrlKey: !!mods.ctrlKey, metaKey: !!mods.metaKey };
      const before = canvasSelectionIds();
      const timer = setTimeout(() => {
        pendingContainerTap = null;
        selectContainerMembers(n, modifierState);
      }, 220);
      pendingContainerTap = { id: n.id(), at: now, timer, before };
    });

    // ---------- right-click selection / neighbourhood growth ----------
    // Right-clicking an unselected component selects it. Right-clicking a component that is
    // already selected grows the selection: starting from that component we walk the transitive
    // set of nodes that are both connected and already selected (a "selected island"), collect
    // every not-yet-selected direct neighbour of that island, and select those too. Repeated
    // right-clicks therefore expand the selection ring by ring along the real edges.
    // Two different predicates, and the distinction is the whole point:
    //  - frontierNode: may be part of the CURRENT frontier, i.e. may be traversed when the
    //    connected selected region is determined. Parked nodes are excluded, so the frontier
    //    is computed solely on the non-parked graph and never propagates through the tray.
    //  - acquirableNode: may become part of the NEW frontier, i.e. may be picked up as a
    //    neighbour. Parked nodes ARE allowed here; they get selected and highlighted in the
    //    parked-items panel without returning to the canvas.
    const frontierNode = (n) => n && n.isNode() && !isContainer(n) && !isParked(n) && n.style("display") !== "none";
    const acquirableNode = (n) => n && n.isNode() && !isContainer(n);
    const selectableNode = frontierNode;

    const selectedIsland = (startNode) => {
      // Breadth-first over edges, staying inside the set of currently selected, non-parked
      // nodes. Hidden edges (which lead into the tray) are not traversed.
      const island = new Map([[startNode.id(), startNode]]);
      const queue = [startNode];
      while (queue.length) {
        const cur = queue.shift();
        cur.connectedEdges().forEach((edge) => {
          if (edge.style("display") === "none") return;
          [edge.source(), edge.target()].forEach((cand) => {
            if (island.has(cand.id())) return;
            if (!frontierNode(cand) || !cand.selected()) return;
            island.set(cand.id(), cand);
            queue.push(cand);
          });
        });
      }
      return island;
    };

    const frontierAdditionsFrom = (startNode) => {
      const island = selectedIsland(startNode);
      const additions = new Map();
      island.forEach((member) => {
        // ALL neighbours of the frontier are acquired, including parked ones. Their edges are
        // hidden on the canvas, but the connection is real, so we deliberately do not filter
        // by edge visibility here -- only the frontier itself was restricted to visible nodes.
        member.connectedEdges().forEach((edge) => {
          [edge.source(), edge.target()].forEach((cand) => {
            const id = cand.id();
            if (island.has(id) || additions.has(id)) return;
            if (!acquirableNode(cand) || cand.selected()) return;
            additions.set(id, cand);
          });
        });
      });
      return additions;
    };

    const growSelectionFrom = (startNode) => {
      const additions = frontierAdditionsFrom(startNode);
      if (!additions.size) return 0;
      cy.batch(() => additions.forEach((n) => n.select()));
      return additions.size;
    };

    // Right-clicking a module/namespace box selects exactly that container's components and
    // clears every other selection -- a quick way to isolate one module as the new frontier.
    // Selecting the members of a module/namespace box. Only unparked, visible components
    // count as members -- parked ones are represented in the panel and are deliberately left
    // alone by every variant, so the panel state is never touched from here.
    //   plain -> members become the selection (everything else is dropped)
    //   shift -> members are added to the current selection
    //   ctrl  -> if all members are already selected, unselect them; otherwise select them
    function selectContainerMembers(box, mods) {
      const members = box.descendants().filter((c) => frontierNode(c));
      if (members.empty()) return;
      const additive = !!mods.shiftKey;
      const toggle = !!(mods.ctrlKey || mods.metaKey);
      cy.batch(() => {
        if (toggle) {
          const allSelected = members.every((c) => c.selected());
          members.forEach((c) => { if (allSelected) c.unselect(); else c.select(); });
        } else if (additive) {
          members.forEach((c) => c.select());
        } else {
          // Replace, but only on the canvas: parked selections stay as they are.
          cy.nodes(":selected").forEach((c) => { if (!isParked(c)) c.unselect(); });
          members.forEach((c) => c.select());
        }
      });
      applySelectionHighlight();
      refreshRemovedUi();
    }

    // One proven commit path for every gesture that grows a frontier.
    const commitFrontierGrowth = (n) => {
      growSelectionFrom(n);
      applySelectionHighlight();
      refreshRemovedUi();
    };

    cy.on("cxttap", "node", (e) => {
      const n = e.target;
      // Containers are handled by their own listener above.
      if (isContainer(n)) return;
      // Only nodes actually on the canvas can start or extend a frontier here; parked nodes
      // are reachable via the tray panel's own right-click handler.
      if (!frontierNode(n)) return;
      if (e.originalEvent) { e.originalEvent.preventDefault(); e.originalEvent.stopPropagation(); }
      // Right-click always grows the frontier from this node, regardless of prior selection
      // state -- selection is a left-click concern, growth is a right-click concern.
      commitFrontierGrowth(n);
    });

    // Right-clicking empty canvas clears the selection; in both cases the native browser
    // context menu is suppressed so the gesture stays inside the graph.
    cy.on("cxttap", (e) => {
      if (e.target !== cy) return;
      if (e.originalEvent) e.originalEvent.preventDefault();
      cy.nodes(":selected").unselect(); // right-click clears canvas AND panel selection
      applySelectionHighlight();
      refreshRemovedUi();
    });

    // ---------- marquee (drag-window) selection on the canvas ----------
    // Left-drag on empty canvas spans a rubber band and selects the nodes inside it. Modifier
    // semantics mirror the parked panel:
    //   plain  -> the band's content becomes the new canvas selection (replace)
    //   ctrl   -> each node inside the band is toggled against its state at drag start
    //   shift  -> the band's content is added to the existing selection (union)
    // Parked nodes are never affected: the band only sees what is drawn on the canvas.
    const marquee = document.createElement("div");
    marquee.className = "component-graph-marquee";
    marquee.hidden = true;
    stage.appendChild(marquee);

    let marqueeActive = false;
    let suppressNextBackgroundTap = false;
    let marqueePointerId = null;
    let marqueeOrigin = null;      // rendered coords where the drag started
    let marqueeCurrent = null;     // last known pointer position during the drag
    let marqueeBaseline = null;    // Set of ids selected at drag start (for ctrl toggling)
    let marqueePanWasEnabled = true;
    let marqueeModifiers = { shift: false, ctrl: false };
    const MARQUEE_THRESHOLD = 4;   // px before a click turns into a drag

    // Modifier state is tracked separately from pointer events: keydown/keyup carry it too,
    // so the band can react to Ctrl/Shift while the mouse is standing still.
    const readModifiers = (ev) => { marqueeModifiers = { shift: !!ev.shiftKey, ctrl: !!(ev.ctrlKey || ev.metaKey) }; };
    const marqueeMode = () => (marqueeModifiers.shift ? "add" : marqueeModifiers.ctrl ? "toggle" : "replace");

    const renderedBoxOf = (n) => n.renderedBoundingBox({ includeLabels: false, includeOverlays: false });

    // Pointer position relative to the stage. `offsetX/Y` is relative to the *event target*,
    // which may be the inner Cytoscape canvas or a child layer, so it cannot be trusted here.
    const stagePoint = (ev) => {
      const r = stage.getBoundingClientRect();
      return { x: ev.clientX - r.left, y: ev.clientY - r.top };
    };

    // Own hit test against rendered bounding boxes -- avoids depending on the private
    // cy.renderer() internals, and matches exactly what the marquee itself considers a hit.
    const nodeAtRendered = (pt) => cy.nodes().filter((n) => {
      if (n.style("display") === "none") return false;
      const bb = renderedBoxOf(n);
      return pt.x >= bb.x1 && pt.x <= bb.x2 && pt.y >= bb.y1 && pt.y <= bb.y2;
    }).nonempty();

    // Nodes whose rendered bounding box intersects the band. Containers are excluded so a
    // sweep does not accidentally pick up whole module boxes.
    // Hit-test the node's CENTRE, not its bounding box. Box intersection would feed back on
    // itself now that a covered node grows to level 2: the bigger box keeps intersecting the
    // band even after the band has shrunk off it, so nodes would stick. The centre point is
    // unaffected by the level, which keeps the band's captured set stable while it is dragged.
    const nodesInMarquee = (rect) => cy.nodes().filter((n) => {
      if (isContainer(n) || n.style("display") === "none") return false;
      const p = n.renderedPosition();
      return p.x >= rect.x1 && p.x <= rect.x2 && p.y >= rect.y1 && p.y <= rect.y2;
    });

    const marqueeRect = (cur) => ({
      x1: Math.min(marqueeOrigin.x, cur.x), y1: Math.min(marqueeOrigin.y, cur.y),
      x2: Math.max(marqueeOrigin.x, cur.x), y2: Math.max(marqueeOrigin.y, cur.y)
    });

    const paintMarquee = (rect, mode) => {
      marquee.style.left = `${rect.x1}px`;
      marquee.style.top = `${rect.y1}px`;
      marquee.style.width = `${rect.x2 - rect.x1}px`;
      marquee.style.height = `${rect.y2 - rect.y1}px`;
      marquee.dataset.mode = mode;
    };

    // Live preview: nodes that the current band would end up selecting get a class so the
    // user sees the outcome before releasing.
    const previewMarquee = (rect, mode) => {
      const inside = new Set(nodesInMarquee(rect).map((n) => n.id()));
      cy.batch(() => {
        cy.nodes().forEach((n) => {
          if (isContainer(n) || n.style("display") === "none") return;
          const id = n.id();
          const hit = inside.has(id);
          const was = marqueeBaseline.has(id);
          const willBeSelected = mode === "add" ? (was || hit)
            : mode === "toggle" ? (hit ? !was : was)
            : hit;
          n.toggleClass("marquee-hit", hit);
          n.toggleClass("marquee-will-select", willBeSelected && !was);
          n.toggleClass("marquee-will-drop", !willBeSelected && was);
        });
      });
      // Everything the band currently covers reads out in full, regardless of whether the
      // mode would select or drop it -- the point is to see WHAT is under the band.
      umlPeek = inside;
      syncAllDetail();
    };

    const clearMarqueePreview = () => {
      cy.nodes().removeClass("marquee-hit marquee-will-select marquee-will-drop");
      if (umlPeek.size) { umlPeek = new Set(); syncAllDetail(); }
    };

    const endMarquee = (commit, ev) => {
      if (!marqueeActive) return;
      marqueeActive = false;
      marquee.hidden = true;
      marquee.classList.remove("active");
      cy.userPanningEnabled(marqueePanWasEnabled);
      if (marqueePointerId !== null && stage.releasePointerCapture) {
        try { stage.releasePointerCapture(marqueePointerId); } catch (_) {}
      }
      marqueePointerId = null;
      clearMarqueePreview();
      if (!commit) { marqueeBaseline = null; marqueeOrigin = null; marqueeCurrent = null; return; }

      // Use the last tracked position rather than the release event: on pointerup the
      // coordinates can already be stale/clamped, and modifier state is read from our own
      // tracker so a key released just before the mouse button still counts correctly.
      const rect = marqueeRect(marqueeCurrent || stagePoint(ev));
      const mode = marqueeMode();
      const inside = nodesInMarquee(rect);
      const insideIds = new Set(inside.map((n) => n.id()));

      // Resolve the target set once, then enforce it. Enforcing (rather than just applying)
      // matters because the browser still delivers mouseup to Cytoscape *after* our
      // pointerup, and its background handling clears the selection -- which is exactly why
      // a plain sweep appeared to select nothing while add/toggle seemed to survive.
      const targetIds = new Set();
      cy.nodes().forEach((n) => {
        if (isContainer(n) || n.style("display") === "none") return;
        const id = n.id();
        const hit = insideIds.has(id);
        const was = marqueeBaseline.has(id);
        const shouldSelect = mode === "add" ? (was || hit)
          : mode === "toggle" ? (hit ? !was : was)
          : hit;
        if (shouldSelect) targetIds.add(id);
      });
      // Parked nodes are outside the band's authority and keep whatever state they had.
      cy.nodes(":selected").forEach((n) => { if (isParked(n)) targetIds.add(n.id()); });

      const enforceSelection = () => {
        cy.batch(() => {
          cy.nodes().forEach((n) => {
            if (isContainer(n)) { if (n.selected()) n.unselect(); return; }
            const want = targetIds.has(n.id());
            if (want && !n.selected()) n.select();
            else if (!want && n.selected()) n.unselect();
          });
        });
        applySelectionHighlight();
        refreshRemovedUi();
      };

      marqueeBaseline = null;
      marqueeOrigin = null;
      marqueeCurrent = null;
      // Cytoscape emits a synthetic background "tap" right after the drag; it must not refit
      // the view. The flag is cleared by the tap handler itself, or by the guard below.
      suppressNextBackgroundTap = true;

      enforceSelection();
      // Re-assert after the native mouseup/tap has been processed, so nothing that runs later
      // in the same gesture can undo the sweep.
      requestAnimationFrame(() => {
        enforceSelection();
        suppressNextBackgroundTap = false;
        const flash = cy.collection();
        inside.forEach((n) => { if (n.selected()) flash.merge(n); });
        if (flash.nonempty() && !reduceMotion) {
          flash.addClass("marquee-flash");
          setTimeout(() => flash.removeClass("marquee-flash"), 260);
        }
      });
    };

    // Also swallow the click that follows a completed sweep, so no click-level handler can
    // reinterpret the release as a background click.
    stage.addEventListener("click", (ev) => {
      if (!suppressNextBackgroundTap) return;
      ev.preventDefault();
      ev.stopPropagation();
    }, true);

    stage.addEventListener("pointerdown", (ev) => {
      if (ev.button !== 0) return;                    // left button only
      if (marqueeActive) return;
      // Only when the drag starts on empty canvas -- never on top of a node/container.
      const pt = stagePoint(ev);
      if (nodeAtRendered(pt)) return;
      marqueeOrigin = pt;
      marqueeCurrent = pt;
      readModifiers(ev);
      marqueeBaseline = new Set(cy.nodes(":selected").filter((n) => !isParked(n)).map((n) => n.id()));
      marqueePointerId = ev.pointerId;
      // Armed but not yet active: only a real movement past the threshold starts the band,
      // so a plain background click still behaves as a click.
      marqueeActive = "armed";
    });

    stage.addEventListener("pointermove", (ev) => {
      if (!marqueeActive || !marqueeOrigin) return;
      const cur = stagePoint(ev);
      if (marqueeActive === "armed") {
        if (Math.abs(cur.x - marqueeOrigin.x) < MARQUEE_THRESHOLD &&
            Math.abs(cur.y - marqueeOrigin.y) < MARQUEE_THRESHOLD) return;
        marqueeActive = true;
        marquee.hidden = false;
        marquee.classList.add("active");
        marqueePanWasEnabled = cy.userPanningEnabled();
        cy.userPanningEnabled(false);   // the band owns the drag, not the viewport
        stopFocusFollow();
        clearHover();
        if (stage.setPointerCapture && marqueePointerId !== null) {
          try { stage.setPointerCapture(marqueePointerId); } catch (_) {}
        }
      }
      marqueeCurrent = cur;
      readModifiers(ev);
      refreshMarqueeVisuals();
    });

    // Repaint the band from the tracked state. Used by pointermove and, crucially, by
    // keydown/keyup so pressing or releasing Ctrl/Shift changes the box immediately even
    // while the mouse is standing perfectly still.
    function refreshMarqueeVisuals() {
      if (marqueeActive !== true || !marqueeOrigin || !marqueeCurrent) return;
      const mode = marqueeMode();
      const rect = marqueeRect(marqueeCurrent);
      paintMarquee(rect, mode);
      previewMarquee(rect, mode);
    }

    // Modifier changes during an active sweep: update immediately, no mouse motion needed.
    const onMarqueeKeyState = (ev) => {
      if (marqueeActive !== true) return;
      const before = `${marqueeModifiers.shift}|${marqueeModifiers.ctrl}`;
      readModifiers(ev);
      if (`${marqueeModifiers.shift}|${marqueeModifiers.ctrl}` === before) return;
      refreshMarqueeVisuals();
    };
    window.addEventListener("keydown", onMarqueeKeyState, true);
    window.addEventListener("keyup", onMarqueeKeyState, true);

    // Capture phase + stopPropagation: while a band is active the release belongs to the
    // marquee alone. Letting it reach Cytoscape's own mouseup is what cleared the fresh
    // selection on a plain sweep.
    stage.addEventListener("pointerup", (ev) => {
      if (marqueeActive === "armed") { marqueeActive = false; marqueeBaseline = null; marqueeOrigin = null; marqueeCurrent = null; return; }
      if (marqueeActive !== true) return;
      if (ev.button !== 0) return;
      ev.preventDefault();
      ev.stopPropagation();
      endMarquee(true, ev);
    }, true);
    stage.addEventListener("pointercancel", () => endMarquee(false));
    // Escape aborts the sweep without changing the selection.
    window.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && marqueeActive) endMarquee(false);
    });

    stage.addEventListener("contextmenu", (ev) => ev.preventDefault());

    // Left-click frontier semantics are based on a stable app-owned selection snapshot, not
    // on Cytoscape's transient state. With selectionType="additive" Cytoscape toggles a selected
    // node off before emitting tap; reading n.selected() in tap was therefore inherently racy.
    // The cache is maintained by our select/unselect listener and is captured at tapstart,
    // before Cytoscape performs its tap-selection toggle.
    let nodeTapSnapshot = null;
    let frontierHoldNodeId = null;
    const clearFrontierHoldPeek = () => {
      if (!frontierHoldPeek.size && !frontierHoldNodeId) return;
      frontierHoldPeek = new Set();
      frontierHoldNodeId = null;
      syncAllDetail();
    };
    cy.on("tapstart", "node", (e) => {
      const n = e.target;
      if (isContainer(n) || !frontierNode(n)) { nodeTapSnapshot = null; return; }
      nodeTapSnapshot = {
        id: n.id(),
        wasSelected: isNodeSelected(n.id()),
        ids: new Set(Array.from(selectedIdSet()).filter((id) => {
          const c = cy.getElementById(id);
          return c && c.nonempty() && !isParked(c);
        }))
      };
      const ev = e.originalEvent || {};
      if (nodeTapSnapshot.wasSelected && !ev.shiftKey && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
        frontierHoldNodeId = n.id();
        frontierHoldPeek = new Set(
          Array.from(frontierAdditionsFrom(n).values())
            .filter((c) => frontierNode(c))
            .map((c) => c.id())
        );
        syncAllDetail();
        const pointer = ev.clientX != null && ev.clientY != null
          ? stagePoint(ev)
          : n.renderedPosition();
        const heldId = n.id();
        requestAnimationFrame(() => {
          if (frontierHoldNodeId !== heldId || !frontierHoldPeek.size) return;
          let preview = n;
          frontierHoldPeek.forEach((id) => {
            const candidate = cy.getElementById(id);
            if (candidate && candidate.nonempty()) preview = preview.union(candidate);
          });
          zoomOutAroundPointerToFit(preview, pointer);
        });
      }
    });
    cy.on("tapend tapcancel", "node", () => clearFrontierHoldPeek());

    const restoreTapSelection = (ids) => {
      cy.batch(() => {
        cy.nodes().forEach((c) => {
          if (isContainer(c) || isParked(c)) return;
          const want = ids.has(c.id());
          if (want && !c.selected()) c.select();
          else if (!want && c.selected()) c.unselect();
        });
      });
    };

    let pendingNodeTap = null;
    const cancelPendingNodeTap = () => {
      if (!pendingNodeTap) return;
      clearTimeout(pendingNodeTap.timer);
      pendingNodeTap = null;
    };

    const commitNodeTap = (n, ev, snap) => {
      restoreTapSelection(snap.ids);

      if (ev.shiftKey) {
        if (!n.selected()) n.select();
        commitFrontierGrowth(n);
        setFocus({ type: "node", id: n.id() });
        return;
      }

      if (!snap.wasSelected) {
        cy.batch(() => {
          cy.nodes(":selected").forEach((c) => { if (!isParked(c)) c.unselect(); });
          n.select();
        });
        applySelectionHighlight();
        refreshRemovedUi();
      } else {
        if (!n.selected()) n.select();
        const island = selectedIsland(n);
        cy.batch(() => {
          cy.nodes(":selected").forEach((c) => {
            if (isParked(c) || island.has(c.id())) return;
            c.unselect();
          });
        });
        // Use exactly the same growth code path as the known-good right-click handler.
        commitFrontierGrowth(n);
      }
      setFocus({ type: "node", id: n.id() });
    };

    cy.on("tap", "node", (e) => {
      const n = e.target;
      if (isContainer(n) || !frontierNode(n)) return;
      const ev = e.originalEvent || {};
      if (ev.ctrlKey || ev.metaKey || ev.altKey) { nodeTapSnapshot = null; return; }

      const snap = nodeTapSnapshot && nodeTapSnapshot.id === n.id()
        ? nodeTapSnapshot
        : { id: n.id(), wasSelected: isNodeSelected(n.id()), ids: new Set(selectedIdSet()) };
      nodeTapSnapshot = null;
      cancelPendingNodeTap();
      const modifierState = { shiftKey: !!ev.shiftKey };
      const timer = setTimeout(() => {
        pendingNodeTap = null;
        commitNodeTap(n, modifierState, snap);
      }, 220);
      pendingNodeTap = { id: n.id(), timer };
    });

    // Navigation and module zoom are both double-click gestures. A single click stays inside
    // the graph so it can be used for selection -- accidentally leaving the page while marking
    // nodes was the main hazard of the previous single-click navigation, and the same reasoning
    // keeps module zoom off both single left-click and right-click.
    cy.on("dbltap", "node", (e) => {
      const n = e.target;
      if (e.originalEvent) e.originalEvent.preventDefault();
      if (isContainer(n)) return; // handled immediately by the container tap detector above
      // A double-click is navigation only; suppress either pending single-click mutation.
      cancelPendingNodeTap();
      nodeTapSnapshot = null;
      const u = n.data("url");
      if (u) location.href = new URL(u, root).href;
    });

    // Clicking empty background (not on any node/edge) only resets the view to show
    // everything. The selection is deliberately left untouched -- clearing it is the
    // right-click gesture on the background.
    cy.on("tap", (e) => {
      if (e.target !== cy) return; // only the canvas itself, not a node/edge bubbling up
      // A marquee sweep ends with a synthetic background tap -- it must not refit the view.
      if (suppressNextBackgroundTap) { suppressNextBackgroundTap = false; return; }
      stopFocusFollow();
      // Background click is the "deselect everything" gesture: it drops the canvas selection
      // (parked items keep theirs), collapses every box back to level 0 and zooms out to the
      // whole graph.
      cy.nodes(":selected").forEach((c) => { if (!isParked(c)) c.unselect(); });
      umlHoverId = null;
      applySelectionHighlight();   // also collapses every box back to level 0
      refreshRemovedUi();
      clearHover();
      setFocus({ type: "background" });
    });

    // Only a genuine user gesture (wheel, pinch, drag-pan) hands viewport control back to
    // the user. Viewport events emitted by our own fit animations must be ignored, otherwise
    // the auto-fit loop would abort itself immediately after a node is removed/parked.
    cy.on("zoom pan", () => {
      if (isProgrammaticViewportChange()) return;
      stopFocusFollow();
      // A deliberate zoom/pan also ends the reveal watch: the user has taken the wheel.
      stopFocusFollow();
    });

    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        cy.resize();
        applyFocusFraming(false);
        startFocusFollow();
      }, 150);
    });
  }).catch((err) => {
    stage.innerHTML = `<p class="graph-error">${ui.failed}<br><code>${String((err && err.message) || err)}</code></p>`;
    console.error("component graph", err);
  });
})();
