/*
 * frozen-pack.js — Cluster-Packs lesen.
 *
 * versions/packs/index.json bildet eine Kennung auf (Pack, Offset, Länge) ab.
 * Die Pack-Datei ist JSONL. Die Modul-Ansicht nimmt die Offset-Liste aus
 * <pack>.idx.json. Fassungen sind weitere Offsets in dieselbe Datei:
 * {r, o, n} für den Wortlaut, {ao, an} für den KI-Text.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.FrozenPack = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  // Zustand je Site-Wurzel (absolut aufgelöst): Ein Abruf mit falscher Wurzel (z. B. ein relativer
  // Präfix, der nach einem Inhaltsaustausch nicht mehr zur Adresse passt) darf den Index der echten
  // Wurzel nicht als „fehlt“ markieren. Ein fehlender Index bleibt je Wurzel gemerkt (kein erneuter 404).
  var sites = {};

  function join(root, file) {
    return String(root || "") + "versions/packs/" + file;
  }

  function site(root) {
    var key = String(root || "");
    try {
      if (typeof location !== "undefined" && location.href) key = new URL(key || "./", location.href).href;
    } catch (e) { /* Node-Prüfungen: Wurzel wörtlich */ }
    return sites[key] || (sites[key] = { index: null, wait: null, failed: false, cache: {} });
  }

  function loadIndex(root, signal) {
    var st = site(root);
    if (st.index) return Promise.resolve(st.index);
    if (st.failed) return Promise.resolve(null);
    if (st.wait) return st.wait;
    st.wait = fetch(join(root, "index.json"), { signal: signal }).then(function (res) {
      if (!res.ok) throw new Error("index");
      return res.json();
    }).then(function (data) {
      st.index = data;
      st.wait = null;
      return data;
    }).catch(function (err) {
      st.wait = null;
      if (err && err.name === "AbortError") throw err;
      // Nur ein fehlender Index (HTTP-Fehler) gilt dauerhaft; ein Netzfehler (z. B. Safari bricht beim
      // Verlassen der Seite ab, „Load failed“) darf die Packs nach der Rückkehr nicht abschalten.
      if (!(err && err.name === "TypeError")) st.failed = true;
      return null;
    });
    return st.wait;
  }

  function locate(root, id, signal) {
    return loadIndex(root, signal).then(function (idx) {
      if (!idx || !idx.loc || !idx.loc[id]) return null;
      var row = idx.loc[id];
      return { pack: idx.pack[row[0]], o: row[1], n: row[2] };
    });
  }

  function packMeta(root, pack) {
    var idx = site(root).index;
    return idx && idx.packs ? idx.packs[pack] : null;
  }

  function slotFor(root, pack) {
    var cache = site(root).cache;
    return cache[pack] || (cache[pack] = {});
  }

  function buffer(root, pack, signal) {
    var slot = slotFor(root, pack);
    if (slot.buf) return Promise.resolve(slot.buf);
    if (slot.bufWait) return slot.bufWait;
    var meta = packMeta(root, pack);
    if (!meta) return Promise.resolve(null);
    slot.bufWait = fetch(join(root, meta.file), { signal: signal }).then(function (res) {
      if (!res.ok) throw new Error("pack");
      return res.arrayBuffer();
    }).then(function (raw) {
      slot.buf = new Uint8Array(raw);
      slot.bufWait = null;
      return slot.buf;
    }).catch(function (err) {
      slot.bufWait = null;
      throw err;
    });
    return slot.bufWait;
  }

  function packIndex(root, pack, signal) {
    var slot = slotFor(root, pack);
    if (slot.idx) return Promise.resolve(slot.idx);
    if (slot.idxWait) return slot.idxWait;
    var meta = packMeta(root, pack);
    if (!meta) return Promise.resolve(null);
    slot.idxWait = fetch(join(root, meta.idx), { signal: signal }).then(function (res) {
      if (!res.ok) throw new Error("idx");
      return res.json();
    }).then(function (data) {
      slot.idx = data;
      slot.idxWait = null;
      return data;
    }).catch(function (err) {
      slot.idxWait = null;
      throw err;
    });
    return slot.idxWait;
  }

  function sliceJson(buf, offset, length) {
    return JSON.parse(new TextDecoder().decode(buf.subarray(offset, offset + length)));
  }

  // Eine Zeile über einen Range-Abruf, ohne die ganze Pack-Datei zu laden (Packs sind bis zu ~35 MB groß;
  // ein Beleg braucht wenige KB). Liegt das Pack schon im Speicher, wird daraus geschnitten. Liefert der
  // Server statt 206 die ganze Datei (200), wird sie wie bei buffer() behalten.
  function rangeJson(root, pack, offset, length, signal) {
    var slot = slotFor(root, pack);
    if (slot.buf) return Promise.resolve(sliceJson(slot.buf, offset, length));
    var meta = packMeta(root, pack);
    if (!meta) return Promise.resolve(null);
    return fetch(join(root, meta.file), {
      signal: signal,
      headers: { Range: "bytes=" + offset + "-" + (offset + length - 1) }
    }).then(function (res) {
      if (res.status === 206) {
        return res.arrayBuffer().then(function (raw) { return sliceJson(new Uint8Array(raw), 0, length); });
      }
      if (!res.ok) throw new Error("pack");
      return res.arrayBuffer().then(function (raw) {
        slot.buf = new Uint8Array(raw);
        return sliceJson(slot.buf, offset, length);
      });
    });
  }

  function record(root, id, signal) {
    return locate(root, id, signal).then(function (loc) {
      if (!loc) return null;
      return rangeJson(root, loc.pack, loc.o, loc.n, signal);
    });
  }

  function textAt(root, pack, offset, length, signal) {
    return rangeJson(root, pack, offset, length, signal);
  }

  // Alle Zeilen eines Moduls, ohne die übrigen Module des Clusters zu parsen.
  function moduleRecords(root, pack, module, signal) {
    return loadIndex(root, signal).then(function () {
      return Promise.all([buffer(root, pack, signal), packIndex(root, pack, signal)]);
    }).then(function (pair) {
      var buf = pair[0], idx = pair[1];
      if (!buf || !idx || !idx.modules || !idx.modules[module]) return [];
      return idx.modules[module].map(function (span) { return sliceJson(buf, span[0], span[1]); });
    });
  }

  // Fassungen einer Kennung: Wortlaut und, wo vorhanden, der KI-Text.
  function fassungen(root, id, signal) {
    return locate(root, id, signal).then(function (loc) {
      if (!loc) return [];
      return packIndex(root, loc.pack, signal).then(function (idx) {
        var rows = (idx && idx.fassungen && idx.fassungen[id]) || [];
        return Promise.all(rows.map(function (row) {
          var jobs = [];
          if (row.n) jobs.push(textAt(root, loc.pack, row.o, row.n, signal));
          else jobs.push(Promise.resolve(null));
          if (row.an) jobs.push(textAt(root, loc.pack, row.ao, row.an, signal));
          else jobs.push(Promise.resolve(null));
          return Promise.all(jobs).then(function (both) {
            return { r: row.r, text: both[0], ai: both[1] };
          });
        }));
      });
    });
  }

  return {
    loadIndex: loadIndex,
    locate: locate,
    record: record,
    moduleRecords: moduleRecords,
    fassungen: fassungen,
    sliceJson: sliceJson
  };
});
