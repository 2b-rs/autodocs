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

  var index = null;
  var indexWait = null;
  var indexFailed = false;
  var cache = {};

  function join(root, file) {
    return String(root || "") + "versions/packs/" + file;
  }

  function loadIndex(root, signal) {
    if (index) return Promise.resolve(index);
    if (indexFailed) return Promise.resolve(null);
    if (indexWait) return indexWait;
    indexWait = fetch(join(root, "index.json"), { signal: signal }).then(function (res) {
      if (!res.ok) throw new Error("index");
      return res.json();
    }).then(function (data) {
      index = data;
      return data;
    }).catch(function (err) {
      indexWait = null;
      if (err && err.name === "AbortError") throw err;
      indexFailed = true;
      return null;
    });
    return indexWait;
  }

  function locate(root, id, signal) {
    return loadIndex(root, signal).then(function (idx) {
      if (!idx || !idx.loc || !idx.loc[id]) return null;
      var row = idx.loc[id];
      return { pack: idx.pack[row[0]], o: row[1], n: row[2] };
    });
  }

  function buffer(root, pack, signal) {
    var slot = cache[pack] || (cache[pack] = {});
    if (slot.buf) return Promise.resolve(slot.buf);
    if (slot.bufWait) return slot.bufWait;
    var meta = index && index.packs ? index.packs[pack] : null;
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
    var slot = cache[pack] || (cache[pack] = {});
    if (slot.idx) return Promise.resolve(slot.idx);
    if (slot.idxWait) return slot.idxWait;
    var meta = index && index.packs ? index.packs[pack] : null;
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

  function record(root, id, signal) {
    return locate(root, id, signal).then(function (loc) {
      if (!loc) return null;
      return buffer(root, loc.pack, signal).then(function (buf) {
        return buf ? sliceJson(buf, loc.o, loc.n) : null;
      });
    });
  }

  function textAt(root, pack, offset, length, signal) {
    return buffer(root, pack, signal).then(function (buf) {
      return buf ? sliceJson(buf, offset, length) : null;
    });
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
