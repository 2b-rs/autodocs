// issue-graph-public-embed.js
// Client enhancement for the published public issue graph. The SVG and
// accessible list are already in the HTML (no-JS fallback). This script
// never fetches the backlog file, internal views, or the internal catalog.
(function (global) {
  'use strict';

  function parseEmbedded(host) {
    if (!host) return null;
    var node = host.querySelector('#issue-graph-public-data');
    if (!node || !node.textContent) return null;
    return JSON.parse(node.textContent);
  }

  function itemCount(payload) {
    return (payload && payload.items) ? payload.items.length : 0;
  }

  function renderList(payload) {
    var items = (payload && payload.items) || [];
    return items.map(function (item) {
      var id = String(item.id);
      return {
        id: id,
        href: 'issues.html#' + id,
        title_key: item.title_key || id,
        state_coarse: item.state_coarse || '',
      };
    });
  }

  function enhance(host) {
    var payload = parseEmbedded(host);
    if (!payload) return;
    host.setAttribute('data-client-rendered', '1');
    host.setAttribute('data-client-item-count', String(itemCount(payload)));
    var links = host.querySelectorAll('.public-issue-list a');
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute('href') || '';
      if (href.indexOf('issues.html#') !== 0) {
        links[i].setAttribute('href', 'issues.html#' + (links[i].textContent || '').trim());
      }
    }
  }

  global.PublicIssueGraph = {
    parseEmbedded: parseEmbedded,
    itemCount: itemCount,
    renderList: renderList,
    enhance: enhance,
  };

  var host = global.document && global.document.getElementById('public-issue-graph');
  if (host) {
    try {
      enhance(host);
    } catch (e) {
      host.setAttribute('data-client-error', '1');
    }
  }
})(typeof window !== 'undefined' ? window : this);
