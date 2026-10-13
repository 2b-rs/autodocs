
(function () {
  "use strict";
  // Fassungen dieser Bildreihe: wortgenauer Vergleich der KI-Beschreibungen (static/text-diff.js, wie im
  // Versions-Explorer); das gespeicherte „Delta laut KI“ als Tooltip am Änderungsklassen-Chip und gesammelt in
  // der Ansicht „KI-Deltas“. Standard: diese Fassung gegen ihre Vorgängerin; ohne Skript bleibt der
  // Nachbarvergleich (Deltas) als Rückfall stehen.
  var box = document.querySelector(".fig-explorer[data-series]");
  if (!box || !window.TextDiff || !window.FIG_SERIES || !window.FIG_SERIES[box.dataset.series]) return;
  var S = window.FIG_SERIES[box.dataset.series], cur = box.dataset.current;
  box.innerHTML = '<h4>KI-Beschreibungen der Fassungen vergleichen <span class="ai-model">KI-generiert</span></h4>' +
    '<p class="fx-hint">Wortgenauer Vergleich der Agentenbeschreibungen zweier Fassungen dieser Bildreihe. ' +
    'Das gespeicherte Delta laut KI zeigt der Änderungsklassen-Chip einer Fassung; alle Übergänge listet die ' +
    'Ansicht „KI-Deltas“.</p><div class="fx-diff"></div>';
  window.TextDiff.seriesDiff(box.querySelector(".fx-diff"), S, {
    current: cur, viewer: "fig-page",
    pageHref: function (id) { return id && id !== cur ? id + ".html" : null; }
  });
})();
