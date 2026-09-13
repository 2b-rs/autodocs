// backlog-evolution-embed.js
// Optional start-page embed. Missing data is a silent no-op.

(function () {
  'use strict';

  var host = document.getElementById('tr-backlog-evolution');
  if (!host) return;

  var STORAGE_KEY = 'backlogEvolutionEmbed.open';

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

  function mount() {
    var wrap = document.createElement('details');
    wrap.className = 'fold';
    wrap.open = getPersistedOpen();
    wrap.innerHTML =
      '<summary><h2 class="sect" style="display:inline">Feature completion over time (internal)</h2></summary>' +
      '<p class="dim" style="margin:.4rem 0 .8rem">Scrub git history of the legacy TODO.md backlog and the current issue-store catalog. Open the standalone viewer for a larger canvas.</p>' +
      '<iframe src="tools/backlog-evolution-visualizer.html?v=feature-top2" title="Feature completion over time" ' +
      'style="width:100%;height:540px;border:1px solid #d9dce3;border-radius:10px;background:#080c14;display:block;"></iframe>' +
      '<p class="dim" style="margin:.5rem 0 0"><a href="tools/backlog-evolution-visualizer.html?v=feature-top2">Open full visualizer</a></p>';
    wrap.addEventListener('toggle', function () {
      setPersistedOpen(wrap.open);
    });
    host.replaceWith(wrap);
  }

  fetch('issues/_views/backlog-evolution.json', { cache: 'no-store' })
    .then(function (res) {
      if (res.ok) {
        mount();
        return;
      }
      return fetch('issues/_views/dependency-graph.json', { cache: 'no-store' }).then(function (graphRes) {
        if (graphRes.ok) mount();
        else if (host.parentNode) host.parentNode.removeChild(host);
      });
    })
    .catch(function () {
      if (host && host.parentNode) host.parentNode.removeChild(host);
    });
})();
