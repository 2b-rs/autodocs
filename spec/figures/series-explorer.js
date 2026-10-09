
(function () {
  "use strict";
  // Fassungen dieser Bildreihe: wortgenauer Vergleich der KI-Beschreibungen (static/text-diff.js, wie im
  // Versions-Explorer) mit dem gespeicherten „Delta laut KI“ daneben. Standard: diese Fassung gegen ihre
  // Vorgängerin; ohne Skript bleibt der Nachbarvergleich (Deltas) als Rückfall stehen.
  var box = document.querySelector(".fig-explorer[data-series]");
  if (!box || !window.TextDiff || !window.FIG_SERIES || !window.FIG_SERIES[box.dataset.series]) return;
  var S = window.FIG_SERIES[box.dataset.series], cur = box.dataset.current;
  box.innerHTML = '<h4>KI-Beschreibungen der Fassungen vergleichen <span class="ai-model">KI-generiert</span></h4>' +
    '<p class="fx-hint">Wortgenauer Vergleich der Agentenbeschreibungen zweier Fassungen dieser Bildreihe; ' +
    'daneben das gespeicherte Delta laut KI zum Abgleich mit dem berechneten Vergleich.</p><div class="fx-diff"></div>';
  window.TextDiff.seriesDiff(box.querySelector(".fx-diff"), S, {
    current: cur,
    pageHref: function (id) { return id && id !== cur ? id + ".html" : null; }
  });
})();
