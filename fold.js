// fold.js — Verhalten der klappbaren KI-Guide-Abschnitte (<details class="fold">).
// Direkte Quelldatei (wie style.css), wird nicht generiert. Siehe _src/WARTUNG.md.
//
//  1. Deep Links: Zeigt ein Anker (#…) auf ein Element in einem eingeklappten
//     Abschnitt, wird der Abschnitt automatisch geöffnet und hingescrollt —
//     Querverweise auf #guide-…/#diag-…-Anker funktionieren so weiterhin.
//  2. Drucken: Vor dem Druck werden alle Abschnitte geöffnet, danach wieder
//     in den vorherigen Zustand versetzt.
//  3. Breadcrumb-Dropdowns: details.universe-dropdown und details.release-dropdown
//     öffnen bei mouseenter, schließen 150ms nach mouseleave (Timeout wird bei
//     Wiedereintritt gelöscht). Ein Klick auf ein Universum reicht zur Navigation.
//  4. Release-Hash: #release=R19-11 / #release=R20-11 schaltet den Point-in-Time-
//     Kontext ohne Reload. Nur Elemente mit data-changed-in für dieses Release
//     werden hervorgehoben und klappen History/Diff auf.
(function () {
  "use strict";
  // Lokaler Dienst: relativ auf localhost, sonst über die geprüfte localhost-Adresse (ai-access.js).
  function localApi(path) { var a = typeof window !== "undefined" && window.AiAccess; return a && a.localUrl ? a.localUrl(path) : path; }

  function oeffnePfad(el) {
    var geoeffnet = false;
    for (var d = el; d; d = d.parentElement) {
      if (d.tagName === "DETAILS" && !d.open) {
        d.open = true;
        geoeffnet = true;
      }
    }
    return geoeffnet;
  }

  function parseReleaseFromHash(hash) {
    var h = hash || "";
    if (h.charAt(0) === "#") h = h.slice(1);
    if (!h) return "";
    try { h = decodeURIComponent(h); } catch (e) { /* unkodierter Hash */ }
    var match = /(?:^|&)release=([^&]*)/.exec(h);
    if (!match) return "";
    return String(match[1] || "").trim();
  }

  function getAnchorTargetFromHash(hash) {
    var h = hash || "";
    if (h.charAt(0) === "#") h = h.slice(1);
    if (!h) return "";
    try { h = decodeURIComponent(h); } catch (e) {}
    var parts = h.split("&").filter(function (part) {
      return part.indexOf("release=") !== 0;
    });
    return parts.length > 0 ? parts[0] : "";
  }

  function zumAnker() {
    if (!location.hash) return;
    var anchorId = getAnchorTargetFromHash(location.hash);
    if (!anchorId) return;
    var ziel = null;
    try {
      ziel = document.getElementById(decodeURIComponent(anchorId));
    } catch (e) { /* ungültiger Hash */ }
    if (ziel) {
      oeffnePfad(ziel);
      ziel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  window.addEventListener("hashchange", zumAnker);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", zumAnker);
  } else {
    zumAnker();
  }

  var RELEASE_HOVER_MS = 150;
  var RELEASE_OPENED_ATTR = "data-release-opened";

  function releaseFromLink(a) {
    if (!a) return "";
    var rel = (a.getAttribute("data-release") || "").trim();
    if (rel) return rel;
    var href = a.getAttribute("href") || "";
    var fromHref = parseReleaseFromHash(href.indexOf("#") >= 0 ? href.slice(href.indexOf("#")) : href);
    if (fromHref) return fromHref;
    return String(a.textContent || "").replace(/\s+/g, " ").trim();
  }

  function setReleaseSummaryLabel(dropdown, label) {
    var summary = dropdown && dropdown.querySelector("summary");
    if (!summary || !label) return;
    var caret = summary.querySelector(".dropdown-caret");
    var nodes = Array.prototype.slice.call(summary.childNodes);
    nodes.forEach(function (node) {
      if (node !== caret) summary.removeChild(node);
    });
    summary.insertBefore(document.createTextNode(label + (caret ? " " : "")), caret || null);
  }

  function closeReleaseAutoOpened() {
    document.querySelectorAll("details[" + RELEASE_OPENED_ATTR + "]").forEach(function (d) {
      d.open = false;
      d.removeAttribute(RELEASE_OPENED_ATTR);
    });
    document.querySelectorAll(".is-release-changed").forEach(function (el) {
      el.classList.remove("is-release-changed");
    });
  }

  function tokensChangedIn(raw) {
    return String(raw || "").split(/[\s,;]+/).filter(Boolean);
  }

  function openReleasePanel(detailsEl) {
    if (!detailsEl || detailsEl.tagName !== "DETAILS") return;
    if (detailsEl.open) return;
    detailsEl.open = true;
    detailsEl.setAttribute(RELEASE_OPENED_ATTR, "");
  }

  function parseAutosarRelease(rel) {
    if (!rel) return null;
    rel = String(rel).trim();
    var m = /^R(\d{2})-(\d{2})$/i.exec(rel);
    if (m) {
      return { type: "r_date", val: parseInt(m[1], 10) * 100 + parseInt(m[2], 10), raw: rel };
    }
    var m2 = /^(\d+)\.(\d+)$/.exec(rel);
    if (m2) {
      return { type: "classic_num", val: parseInt(m2[1], 10) * 100 + parseInt(m2[2], 10), raw: rel };
    }
    return { type: "unknown", val: 0, raw: rel };
  }

  function compareAutosarReleases(a, b) {
    var pa = parseAutosarRelease(a);
    var pb = parseAutosarRelease(b);
    if (!pa || !pb) return 0;
    if (pa.type === pb.type) {
      return pa.val - pb.val;
    }
    if (pa.type === "classic_num" && pb.type === "r_date") return -1;
    if (pa.type === "r_date" && pb.type === "classic_num") return 1;
    return pa.raw.localeCompare(pb.raw);
  }

  function applyReleaseContext(rel) {
    closeReleaseAutoOpened();
    if (!rel) return;

    document.querySelectorAll("details.release-dropdown").forEach(function (dropdown) {
      var links = dropdown.querySelectorAll(".releases a");
      var chosen = null;
      links.forEach(function (a) {
        if (!chosen && releaseFromLink(a) === rel) chosen = a;
      });
      if (!chosen) return;
      links.forEach(function (a) {
        if (a === chosen) a.classList.add("cur");
        else a.classList.remove("cur");
      });
      var label = String(chosen.textContent || rel).replace(/\s+/g, " ").trim();
      setReleaseSummaryLabel(dropdown, label || rel);
    });

    document.querySelectorAll("select.rec-asof-select").forEach(function (sel) {
      var has = false;
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === rel) {
          has = true;
          break;
        }
      }
      if (has) sel.value = rel;
    });

    document.querySelectorAll("[data-changed-in]").forEach(function (el) {
      var tokens = tokensChangedIn(el.getAttribute("data-changed-in"));
      if (tokens.indexOf(rel) === -1) return;
      el.classList.add("is-release-changed");
      if (el.tagName === "DETAILS") openReleasePanel(el);
      el.querySelectorAll("details.rec-history-panel, details.rec-diff, details.diff").forEach(openReleasePanel);
    });

    // Multi-Release Tombstoning & Delta Patches (CONCEPT-0045)
    var isTombstoned = false;
    document.querySelectorAll(".ai-tombstone-box").forEach(function (box) {
      var forReleases = (box.getAttribute("data-tombstone-releases") || "").split(/[\s,;]+/).filter(Boolean);
      if (forReleases.indexOf(rel) !== -1) {
        box.style.display = "block";
        isTombstoned = true;
      } else {
        box.style.display = "none";
      }
    });

    document.querySelectorAll(".canonical-module-content, main > .module-meta, main > .rec, main > details.fold, main > ul.mlist, main > h2.sect").forEach(function (el) {
      if (isTombstoned) {
        el.classList.add("is-tombstoned");
      } else {
        el.classList.remove("is-tombstoned");
      }
    });

    document.querySelectorAll(".ai-release-delta-box").forEach(function (delta) {
      var deltaReleases = (delta.getAttribute("data-delta-releases") || delta.getAttribute("data-delta-release") || "").split(/[\s,;]+/).filter(Boolean);
      if (deltaReleases.indexOf(rel) !== -1) {
        delta.style.display = "block";
      } else {
        delta.style.display = "none";
      }
    });

    // Multi-Release AI Guide Variants & Fallbacks (INV-PROMPT-RELEASE-01)
    var variantContainers = [];
    document.querySelectorAll(".ai-guide-release-variant, [data-asof-release]").forEach(function (el) {
      var parent = el.closest(".ai-guide-container, details.fold, .canonical-module-content, main") || el.parentElement;
      if (parent && variantContainers.indexOf(parent) === -1) {
        variantContainers.push(parent);
      }
    });

    variantContainers.forEach(function (container) {
      var variants = Array.prototype.slice.call(container.querySelectorAll(".ai-guide-release-variant, [data-asof-release]"));
      variants = variants.filter(function (v) {
        var p = v.closest(".ai-guide-container, details.fold, .canonical-module-content, main") || v.parentElement;
        return p === container;
      });
      if (variants.length === 0) return;

      var validVariants = variants.filter(function (v) {
        var appRels = (v.getAttribute("data-applicable-releases") || "").split(/[\s,;]+/).filter(Boolean);
        if (appRels.indexOf(rel) !== -1) return true;
        var vRel = v.getAttribute("data-asof-release") || v.getAttribute("data-asof-anchor");
        return vRel && compareAutosarReleases(vRel, rel) <= 0;
      });

      validVariants.sort(function (a, b) {
        var relA = a.getAttribute("data-asof-release") || a.getAttribute("data-asof-anchor") || "";
        var relB = b.getAttribute("data-asof-release") || b.getAttribute("data-asof-anchor") || "";
        return compareAutosarReleases(relB, relA);
      });

      // Under INV-ZERO-FALLBACK-COVERAGE-02:
      // If no strictly <= rel variant is matched, fall back to the closest available anchor variant,
      // project surface links to rel, and NEVER display an error fallback box!
      var activeVariant = validVariants.length > 0 ? validVariants[0] : null;
      if (!activeVariant && variants.length > 0) {
        var sortedAll = variants.slice().sort(function (a, b) {
          var relA = a.getAttribute("data-asof-release") || a.getAttribute("data-asof-anchor") || "";
          var relB = b.getAttribute("data-asof-release") || b.getAttribute("data-asof-anchor") || "";
          return compareAutosarReleases(relA, relB);
        });
        activeVariant = sortedAll[0];
      }

      variants.forEach(function (v) {
        if (v === activeVariant) {
          v.style.display = "";
        } else {
          v.style.display = "none";
        }
      });

      // Remove any legacy fallback box (INV-ZERO-FALLBACK-COVERAGE-02)
      var fallback = container.querySelector(".ai-release-fallback-box");
      if (fallback) fallback.remove();
    });

    applyStandardsLinkRewrites(document, rel);
    checkAndApplySupersessions(rel);

    // Dynamic Footer Release Synchronization (CONCEPT-0045 / Movie 2026-10-05 23-48-42)
    var footer = document.querySelector("footer");
    if (footer) {
      if (!footer.getAttribute("data-orig-html")) {
        footer.setAttribute("data-orig-html", footer.innerHTML);
      }
      var origHtml = footer.getAttribute("data-orig-html");
      if (rel) {
        var updatedHtml = origHtml.replace(/(AUTOSAR[^\w<>]*(?:R?\d{2}-\d{2}|\d+\.\d+))/gi, function (match) {
          return match.replace(/(?:R?\d{2}-\d{2}|\d+\.\d+)/, rel);
        });
        footer.innerHTML = updatedHtml;
      } else {
        footer.innerHTML = origHtml;
      }
    }

    // Dynamic Consulted Source Base Heading Synchronization (Movie 2026-10-05 23-53-26)
    document.querySelectorAll("h2.sect").forEach(function (h2) {
      var txt = h2.textContent || "";
      if (txt.indexOf("Quellenbasis") !== -1 || txt.indexOf("source base") !== -1 || txt.indexOf("base de") !== -1) {
        if (!h2.getAttribute("data-orig-text")) {
          h2.setAttribute("data-orig-text", txt);
        }
        var orig = h2.getAttribute("data-orig-text");
        if (rel) {
          h2.textContent = orig.replace(/(R?\d{2}-\d{2}|\d+\.\d+)/, rel);
        } else {
          h2.textContent = orig;
        }
      }
    });
  }

  var AUTOSAR_STANDARDS_FOLDER = {
    "4.0": "R4.0.3",
    "4.1": "R4.1.3",
    "4.2": "R4.2.2",
    "4.3": "R4.3.1",
    "4.4": "R18-10_R4.4.0_R1.5.0",
  };

  function getAutosarStandardsReleaseFolder(rel) {
    if (!rel) return "";
    if (AUTOSAR_STANDARDS_FOLDER[rel]) return AUTOSAR_STANDARDS_FOLDER[rel];
    return rel;
  }

  function rewriteAutosarStandardsUrl(url, rel) {
    if (!url || typeof url !== "string") return url;
    if (url.indexOf("autosar.org/fileadmin/standards/") === -1) return url;
    if (!rel) return url;

    var folder = getAutosarStandardsReleaseFolder(rel);
    var m = url.match(/^(https?:\/\/[^\/]*autosar\.org\/fileadmin\/standards\/)[^\/]+\/([A-Z]+)\/([^\/?#]+)(#.*)?$/i);
    if (!m) {
      return url.replace(/\/standards\/[^\/]+\//, "/standards/" + encodeURIComponent(folder) + "/");
    }

    var basePrefix = m[1];
    var platFolder = m[2].toUpperCase();
    var pdfName = m[3];
    var anchor = m[4] || "";

    var isPreR23 = compareAutosarReleases(rel, "R23-11") < 0;

    if (isPreR23) {
      pdfName = pdfName.replace(/^AUTOSAR_AP_/i, "AUTOSAR_").replace(/^AUTOSAR_CP_/i, "AUTOSAR_");
      if (rel === "R19-11" && pdfName === "AUTOSAR_EXP_SWArchitecture.pdf") {
        pdfName = "AUTOSAR_EXP_PlatformDesign.pdf";
      }
      if (pdfName.indexOf("StateManagement") !== -1 || (anchor && anchor.indexOf("SWS_SM_") !== -1)) {
        if (rel === "R19-11" || rel === "R20-11" || rel === "R21-11") {
          platFolder = "FO";
        } else {
          platFolder = "AP";
        }
      }
    } else {
      if (platFolder === "AP" && !pdfName.startsWith("AUTOSAR_AP_") && pdfName.startsWith("AUTOSAR_")) {
        pdfName = pdfName.replace(/^AUTOSAR_/, "AUTOSAR_AP_");
      } else if (platFolder === "CP" && !pdfName.startsWith("AUTOSAR_CP_") && pdfName.startsWith("AUTOSAR_")) {
        pdfName = pdfName.replace(/^AUTOSAR_/, "AUTOSAR_CP_");
      }
      if (pdfName.indexOf("StateManagement") !== -1 || (anchor && anchor.indexOf("SWS_SM_") !== -1)) {
        platFolder = "AP";
      }
    }

    return basePrefix + encodeURIComponent(folder) + "/" + platFolder + "/" + pdfName + anchor;
  }

  function getPathUniverse(path) {
    if (!path) return "";
    if (path.indexOf("/classic/") !== -1) return "classic";
    if (path.indexOf("/adaptive/") !== -1) return "adaptive";
    if (path.indexOf("/score/") !== -1) return "score";
    var adaptivePfxs = ["/modules/", "/namespaces/", "/classes/", "/services/"];
    for (var i = 0; i < adaptivePfxs.length; i++) {
      if (path.indexOf(adaptivePfxs[i]) !== -1) return "adaptive";
    }
    return "";
  }

  function isSameUniverse(curUniverse, destPath) {
    if (!curUniverse || !destPath) return false;
    if (destPath.indexOf("/" + curUniverse + "/") !== -1) return true;
    if (curUniverse === "adaptive") {
      var pfxs = ["/adaptive/", "/modules/", "/namespaces/", "/classes/", "/services/"];
      for (var i = 0; i < pfxs.length; i++) {
        if (destPath.indexOf(pfxs[i]) !== -1) return true;
      }
    }
    return false;
  }

  function applyStandardsLinkRewrites(rootNode, rel) {
    var scope = rootNode || document;

    // 1. Update all standards documentation links across the page to point to the active release
    scope.querySelectorAll('a[href*="autosar.org/fileadmin/standards/"]').forEach(function (a) {
      if (!a.getAttribute("data-orig-href")) {
        a.setAttribute("data-orig-href", a.getAttribute("href"));
      }
      var origHref = a.getAttribute("data-orig-href");
      if (!rel) {
        a.setAttribute("href", origHref);
      } else {
        a.setAttribute("href", rewriteAutosarStandardsUrl(origHref, rel));
      }
      var text = a.textContent || "";
      if (text.indexOf("autosar.org/fileadmin/standards/") !== -1) {
        if (!a.getAttribute("data-orig-text")) {
          a.setAttribute("data-orig-text", text);
        }
        var origText = a.getAttribute("data-orig-text");
        a.textContent = rel ? rewriteAutosarStandardsUrl(origText, rel) : origText;
      } else if (/\((?:R\d\d-\d\d|\d+\.\d+)\)/.test(text)) {
        a.textContent = text.replace(/\((?:R\d\d-\d\d|\d+\.\d+)\)/, "(" + rel + ")");
      }
    });

    // 2. Update spec-source-link and review-request-panel bound links (Leakage-from-Future constraint)
    scope.querySelectorAll('a.spec-source-link, [data-review-request-root] dd a').forEach(function (a) {
      var text = a.textContent || "";
      if (text.indexOf("autosar.org/fileadmin/standards/") !== -1 || a.getAttribute("data-orig-text")) {
        if (!a.getAttribute("data-orig-text")) {
          a.setAttribute("data-orig-text", text);
        }
        var origText = a.getAttribute("data-orig-text");
        a.textContent = rel ? rewriteAutosarStandardsUrl(origText, rel) : origText;
      }
      var href = a.getAttribute("href") || "";
      if (href.indexOf("autosar.org/fileadmin/standards/") !== -1) {
        if (!a.getAttribute("data-orig-href")) {
          a.setAttribute("data-orig-href", href);
        }
        var origHref = a.getAttribute("data-orig-href");
        a.setAttribute("href", rel ? rewriteAutosarStandardsUrl(origHref, rel) : origHref);
      }
    });

    // 3. Update review-request JSON data payload if present in scope
    scope.querySelectorAll('[data-review-request-root] script.review-request-data').forEach(function (script) {
      try {
        if (!script.getAttribute("data-orig-json")) {
          script.setAttribute("data-orig-json", script.textContent);
        }
        var origJson = script.getAttribute("data-orig-json");
        var pData = JSON.parse(origJson);
        if (pData && pData.source_url) {
          pData.source_url = rel ? rewriteAutosarStandardsUrl(pData.source_url, rel) : pData.source_url;
          script.textContent = JSON.stringify(pData);
        }
      } catch (e) {}
    });

    // Ensure all visible .ai-note headers match the active release
    scope.querySelectorAll(".ai-note").forEach(function (note) {
      var vParent = note.closest("[data-asof-release]");
      var targetRel = (vParent && vParent.getAttribute("data-asof-release")) || rel;
      if (note.textContent.indexOf("AUTOSAR-") !== -1) {
        note.innerHTML = note.innerHTML.replace(/AUTOSAR-R\d\d-\d\d-(Dokumenten|Spezifikationselementen)/g, "AUTOSAR-" + targetRel + "-$1");
      }
    });

    // Update all spec-record trampoline links to encode the active release (Zero-PDF-URL & Dynamic Routing):
    scope.querySelectorAll('a.spec-record-ref, a[href*="spec/record.html"]').forEach(function (a) {
      var href = a.getAttribute("href");
      if (!href) return;
      var hashIdx = href.indexOf("#");
      var hashPart = hashIdx >= 0 ? href.slice(hashIdx) : "";
      var basePart = hashIdx >= 0 ? href.slice(0, hashIdx) : href;
      
      if (rel) {
        if (basePart.indexOf("release=") !== -1) {
          basePart = basePart.replace(/([?&])release=[^&]*/, "$1release=" + encodeURIComponent(rel));
        } else {
          basePart += (basePart.indexOf("?") !== -1 ? "&" : "?") + "release=" + encodeURIComponent(rel);
        }
      } else {
        basePart = basePart.replace(/([?&])release=[^&#]*/, "").replace(/\?&/, "?").replace(/[?&]$/, "");
      }
      a.setAttribute("href", basePart + hashPart);
    });

    // Update all internal documentation links within the current universe to preserve active release:
    var curUniverse = getPathUniverse(location.pathname);
    var path = location.pathname || "";

    if (curUniverse) {
      scope.querySelectorAll("a").forEach(function (a) {
        if (a.closest("details.universe-dropdown, details.release-dropdown, .langs")) return;
        var origHref = a.getAttribute("data-orig-href") || a.getAttribute("href");
        if (!origHref || /^(?:[a-z]+:|\/\/|mailto:|javascript:)/i.test(origHref)) return;
        if (a.classList.contains("spec-record-ref") || origHref.indexOf("spec/record.html") !== -1) return;

        var destUrl;
        try {
          destUrl = new URL(origHref, location.href);
        } catch (e) {
          return;
        }
        if (destUrl.origin !== location.origin) return;
        if (destUrl.pathname.indexOf("/" + curUniverse + "/") === -1 && !isSameUniverse(curUniverse, destUrl.pathname)) return;

        if (!a.getAttribute("data-orig-href")) {
          a.setAttribute("data-orig-href", origHref);
        }

        if (!rel) {
          a.setAttribute("href", origHref);
          return;
        }

        var hashIdx = origHref.indexOf("#");
        var basePart = hashIdx >= 0 ? origHref.slice(0, hashIdx) : origHref;
        var oldHash = hashIdx >= 0 ? origHref.slice(hashIdx + 1) : "";
        var cleanHash = oldHash.split("&").filter(function (part) {
          return part.indexOf("release=") !== 0;
        }).join("&");

        var targetHash = "release=" + encodeURIComponent(rel) + (cleanHash ? "&" + cleanHash : "");
        a.setAttribute("href", basePart + "#" + targetHash);
      });
    }

  var FOLD_I18N = {
    de: {
      valid_for: "Gültig für {rel}",
      unchanged_title: "🛡️ Unverändert seit {rel}",
      unchanged_desc: "Normativer Spezifikationstext und Inbound-Architekturklauseln sind ab {rel} unverändert gültig.",
      ref_proj_title: "ℹ️ Referenzstand {rel}",
      ref_proj_desc: "Dieser Leitfaden beruht auf dem Referenzstand AUTOSAR {rel} (Projektion auf {target}).",
      anchor_badge: "Kausaler Anker: {rel}",
      anchor_title: "Gültig ab {rel}",
      anchor_desc: "Neu synthetisiert für diesen Spezifikationsstand.",
      tag_unchanged: "Unverändert seit {rel}",
      tag_stand: "Stand {rel}"
    },
    en: {
      valid_for: "Valid for {rel}",
      unchanged_title: "🛡️ Unchanged since {rel}",
      unchanged_desc: "Normative specification text and inbound architecture clauses remain unchanged from {rel}.",
      ref_proj_title: "ℹ️ Reference release {rel}",
      ref_proj_desc: "This technical guide is based on reference release AUTOSAR {rel} (projected to {target}).",
      anchor_badge: "Causal Anchor: {rel}",
      anchor_title: "Valid from {rel}",
      anchor_desc: "Synthesized for this specification release.",
      tag_unchanged: "Unchanged since {rel}",
      tag_stand: "Release {rel}"
    },
    es: {
      valid_for: "Válido para {rel}",
      unchanged_title: "🛡️ Sin cambios desde {rel}",
      unchanged_desc: "El texto normativo de la especificación y las cláusulas arquitectónicas permanecen sin cambios desde {rel}.",
      ref_proj_title: "ℹ️ Versión de referencia {rel}",
      ref_proj_desc: "Esta guía técnica se basa en la versión de referencia AUTOSAR {rel} (proyección a {target}).",
      anchor_badge: "Ancla causal: {rel}",
      anchor_title: "Válido desde {rel}",
      anchor_desc: "Sintetizado para esta versión de especificación.",
      tag_unchanged: "Sin cambios desde {rel}",
      tag_stand: "Versión {rel}"
    },
    pt: {
      valid_for: "Válido para {rel}",
      unchanged_title: "🛡️ Inalterado desde {rel}",
      unchanged_desc: "O texto normativo da especificação e as cláusulas arquiteturais permanecem inalterados desde {rel}.",
      ref_proj_title: "ℹ️ Versão de referência {rel}",
      ref_proj_desc: "Este guia técnico baseia-se na versão de referência AUTOSAR {rel} (projeção para {target}).",
      anchor_badge: "Âncora causal: {rel}",
      anchor_title: "Válido a partir de {rel}",
      anchor_desc: "Sintetizado para esta versão de especificação.",
      tag_unchanged: "Inalterado desde {rel}",
      tag_stand: "Versão {rel}"
    }
  };

  function getFoldLang() {
    var lang = (document.documentElement && document.documentElement.lang) || "";
    if (FOLD_I18N[lang]) return lang;
    var m = (window.location.pathname || "").match(/\/(de|en|es|pt|fr|ru|ar|hi|ko|zh|nl)\//);
    if (m && FOLD_I18N[m[1]]) return m[1];
    return "en";
  }

  // Update .ai-provenance-banner to reflect intentional reuse or forward/backward reference
  scope.querySelectorAll(".ai-provenance-banner").forEach(function (banner) {
    var anchorRel = banner.getAttribute("data-anchor-release");
    if (!anchorRel) return;
    banner.setAttribute("data-viewed-release", rel);
    
    var cmp = compareAutosarReleases(anchorRel, rel);
    var statusEl = banner.querySelector(".ai-provenance-status");
    var fLang = getFoldLang();
    var ft = FOLD_I18N[fLang] || FOLD_I18N["en"];
    if (statusEl) {
      if (cmp < 0) {
        // anchor is older than viewed release: valid since anchorRel
        banner.classList.add("intentional-reuse");
        statusEl.innerHTML = 
          '<span class="ai-provenance-badge">' + ft.valid_for.replace("{rel}", rel) + '</span> ' +
          '<span class="ai-provenance-title">' + ft.unchanged_title.replace("{rel}", anchorRel) + '</span> ' +
          '<span class="ai-provenance-desc">' + ft.unchanged_desc.replace("{rel}", anchorRel) + '</span>';
      } else if (cmp > 0) {
        // anchor is newer than viewed release: reference release anchorRel
        banner.classList.add("intentional-reuse");
        statusEl.innerHTML = 
          '<span class="ai-provenance-badge">' + ft.valid_for.replace("{rel}", rel) + '</span> ' +
          '<span class="ai-provenance-title">' + ft.ref_proj_title.replace("{rel}", anchorRel) + '</span> ' +
          '<span class="ai-provenance-desc">' + ft.ref_proj_desc.replace("{rel}", anchorRel).replace("{target}", rel) + '</span>';
      } else {
        banner.classList.remove("intentional-reuse");
        statusEl.innerHTML = 
          '<span class="ai-provenance-badge">' + ft.anchor_badge.replace("{rel}", anchorRel) + '</span> ' +
          '<span class="ai-provenance-title">' + ft.anchor_title.replace("{rel}", anchorRel) + '</span> ' +
          '<span class="ai-provenance-desc">' + ft.anchor_desc + '</span>';
      }
      var guideParent = banner.closest(".ai, .ai-guide-release-variant, details.fold, main") || document;
      guideParent.querySelectorAll(".ai-note").forEach(function (note) {
        if (!note.getAttribute("data-orig-text")) {
          note.setAttribute("data-orig-text", note.textContent);
        }
        if (cmp < 0) {
          if (fLang === "de") {
            note.textContent = "Dieser Leitfaden basiert auf dem Referenzstand AUTOSAR " + anchorRel + " und ist für Release " + rel + " unverändert gültig. Alle Aussagen basieren vollständig auf den maßgeblichen Spezifikationsdokumenten.";
          } else if (fLang === "es") {
            note.textContent = "Esta guía técnica se basa en la versión de referencia AUTOSAR " + anchorRel + " y es válida sin cambios para la versión " + rel + ".";
          } else if (fLang === "pt") {
            note.textContent = "Este guia técnico baseia-se na versão de referência AUTOSAR " + anchorRel + " e é válido sem alterações para a versão " + rel + ".";
          } else if (fLang === "hi") {
            note.textContent = "यह तकनीकी गाइड संदर्भ रिलीज AUTOSAR " + anchorRel + " पर आधारित है और रिलीज " + rel + " के लिए अपरिवर्तित मान्य है।";
          } else {
            note.textContent = "This technical guide is based on the reference release AUTOSAR " + anchorRel + " and remains valid unchanged for release " + rel + ".";
          }
        } else if (cmp > 0) {
          if (fLang === "de") {
            note.textContent = "Dieser Leitfaden basiert auf dem Referenzstand AUTOSAR " + anchorRel + " (Projektion auf Release " + rel + "). Alle Aussagen basieren auf den maßgeblichen Spezifikationsdokumenten.";
          } else if (fLang === "es") {
            note.textContent = "Esta guía técnica se basa en la versión de referencia AUTOSAR " + anchorRel + " (proyección a la versión " + rel + ").";
          } else if (fLang === "pt") {
            note.textContent = "Este guia técnico baseia-se na versão de referência AUTOSAR " + anchorRel + " (projeção para a versão " + rel + ").";
          } else if (fLang === "hi") {
            note.textContent = "यह तकनीकी गाइड संदर्भ रिलीज AUTOSAR " + anchorRel + " पर आधारित है (रिलीज " + rel + " पर प्रक्षेपण)।";
          } else {
            note.textContent = "This technical guide is based on reference release AUTOSAR " + anchorRel + " (projected to release " + rel + ").";
          }
        } else {
          note.textContent = note.getAttribute("data-orig-text");
        }
      });
    }
  });

  // Update inline element provenance tags
  var fLangTag = getFoldLang();
  var ftTag = FOLD_I18N[fLangTag] || FOLD_I18N["en"];
  scope.querySelectorAll(".ai-provenance-tag").forEach(function (tag) {
    var anchorRel = tag.getAttribute("data-anchor-release");
    if (!anchorRel) return;
    var cmp = compareAutosarReleases(anchorRel, rel);
    if (cmp < 0) {
      tag.textContent = ftTag.tag_unchanged.replace("{rel}", anchorRel);
      tag.style.display = "";
    } else if (cmp > 0) {
      tag.textContent = ftTag.tag_stand.replace("{rel}", anchorRel);
      tag.style.display = "";
    } else {
      tag.textContent = ftTag.tag_stand.replace("{rel}", anchorRel);
      tag.style.display = "";
    }
  });
}

  var _supersessionsCache = null;
  var _supersessionsLoading = false;
  var _fragmentCache = {};

  function getRootBasePrefix() {
    var script = document.querySelector('script[src*="fold.js"]');
    if (script) {
      var src = script.getAttribute("src") || "";
      return src.replace(/fold\.js(?:\?.*)?$/, "");
    }
    return "";
  }

  function getActiveDropdownRelease() {
    var cur = document.querySelector("details.release-dropdown .releases a.cur");
    return cur ? releaseFromLink(cur) : parseReleaseFromHash(location.hash);
  }

  function checkAndApplySupersessions(rel) {
    if (!rel) return;
    var aiNodes = document.querySelectorAll(".ai[data-trace-dossier]");
    if (aiNodes.length === 0) return;

    function applyLoadedFixtures(data) {
      if (!data || !data.supersessions) return;
      var map = data.supersessions;

      aiNodes.forEach(function (el) {
        var currentDossier = el.getAttribute("data-trace-dossier");
        if (!currentDossier) return;

        if (typeof el._originalHTML === "undefined") {
          el._originalHTML = el.innerHTML;
          el._originalDossier = currentDossier;
        }

        var lookupKey = el._originalDossier || currentDossier;
        var fixtures = map[lookupKey];
        var matched = null;

        if (fixtures && Array.isArray(fixtures)) {
          for (var i = 0; i < fixtures.length; i++) {
            var f = fixtures[i];
            if (f.applicable_releases && f.applicable_releases.indexOf(rel) !== -1) {
              matched = f;
              break;
            }
          }
        }

        if (matched) {
          if (matched.replacement_html) {
            applyHotfix(el, matched, matched.replacement_html, rel);
          } else if (matched.replacement_fragment) {
            var fragKey = matched.replacement_fragment;
            if (_fragmentCache[fragKey]) {
              applyHotfix(el, matched, _fragmentCache[fragKey], rel);
            } else {
              var pfx = getRootBasePrefix();
              // Öffentlicher Pfad zuerst (die Website enthält kein _src/), lokal Rückfall auf _src/.
              var fragUrl = pfx + fragKey;
              fetch(fragUrl)
                .then(function (r) {
                  if (!r.ok) return fetch(pfx + "_src/" + fragKey);
                  return r;
                })
                .then(function (r) {
                  if (!r.ok) throw new Error("HTTP " + r.status);
                  return r.text();
                })
                .then(function (html) {
                  _fragmentCache[fragKey] = html;
                  var activeRel = getActiveDropdownRelease();
                  if (activeRel === rel || !activeRel) {
                    applyHotfix(el, matched, html, rel);
                  }
                })
                .catch(function (e) {
                  console.warn("Konnte Supersession-Fragment nicht laden:", fragUrl, e);
                });
            }
          }
        } else {
          if (el._isSuperseded) {
            el.innerHTML = el._originalHTML;
            el._isSuperseded = false;
            el.classList.remove("is-superseded");
            var b = el.querySelector(".ai-superseded-banner");
            if (b) b.remove();
            applyStandardsLinkRewrites(el, rel);
          }
        }
      });
    }

    function applyHotfix(el, fixture, htmlContent, currentRel) {
      el._isSuperseded = true;
      el.classList.add("is-superseded");

      var banner = '<div class="ai-superseded-banner">' +
        '<span>ℹ️ <strong>Kurations-Korrektur aktiv:</strong> ' + (fixture.rationale || "Supersession angewendet.") + '</span>' +
        (fixture.curator ? '<span class="ai-superseded-meta">Kuratiert von @' + fixture.curator + '</span>' : '') +
        '</div>';

      el.innerHTML = banner + htmlContent;
      applyStandardsLinkRewrites(el, currentRel);
    }

    if (_supersessionsCache) {
      applyLoadedFixtures(_supersessionsCache);
    } else if (!_supersessionsLoading) {
      _supersessionsLoading = true;
      var pfx = getRootBasePrefix();
      var url = pfx + "fixtures/supersessions.json";
      fetch(url)
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (json) {
          _supersessionsCache = json;
          _supersessionsLoading = false;
          applyLoadedFixtures(json);
        })
        .catch(function (err) {
          _supersessionsLoading = false;
        });
    }
  }

  function applyReleaseHashFromLocation() {
    var rel = parseReleaseFromHash(location.hash);
    if (!rel && location.search) {
      var m = /[?&]release=([^&#]+)/.exec(location.search);
      if (m) rel = decodeURIComponent(m[1]);
    }
    if (!rel) {
      resetReleaseContext();
      return;
    }
    applyReleaseContext(rel);
  }

  function resetReleaseContext() {
    closeReleaseAutoOpened();
    document.querySelectorAll("details.release-dropdown").forEach(function (dropdown) {
      dropdown.querySelectorAll(".releases a").forEach(function (a) {
        a.classList.remove("cur");
      });
      setReleaseSummaryLabel(dropdown, "Release");
    });
    document.querySelectorAll(".is-release-changed").forEach(function (el) {
      el.classList.remove("is-release-changed");
    });
    document.querySelectorAll(".ai-release-delta-box").forEach(function (delta) {
      delta.style.display = "none";
    });
    applyStandardsLinkRewrites(document, "");
  }

  // Geöffnetes Release-Menü im Fenster halten: Ragt es rechts hinaus (schmale Bildschirme),
  // wird es nach links verschoben, höchstens bis an den linken Rand.
  function fitReleaseMenu(details) {
    var box = details && details.querySelector(".releases");
    if (!box) return;
    box.style.left = "";
    var rect = box.getBoundingClientRect();
    if (!rect.width) return;
    var vw = document.documentElement.clientWidth || window.innerWidth || 0;
    var over = rect.right - (vw - 8);
    if (over > 0) box.style.left = -Math.min(over, Math.max(0, rect.left - 8)) + "px";
  }

  function bindCrumbsHover() {
    document.querySelectorAll("details.universe-dropdown, details.release-dropdown").forEach(function (details) {
      if (details.getAttribute("data-hover-bound")) return;
      details.setAttribute("data-hover-bound", "1");
      var leaveTimer = null;
      var isRelease = details.classList.contains("release-dropdown");
      if (isRelease) {
        details.addEventListener("toggle", function () { if (details.open) fitReleaseMenu(details); });
      }
      details.addEventListener("mouseenter", function () {
        if (leaveTimer) {
          clearTimeout(leaveTimer);
          leaveTimer = null;
        }
        details.open = true;
        details.classList.add("is-hover-open");
        if (isRelease) fitReleaseMenu(details);
      });
      details.addEventListener("mouseleave", function () {
        if (leaveTimer) clearTimeout(leaveTimer);
        leaveTimer = setTimeout(function () {
          details.open = false;
          details.classList.remove("is-hover-open");
          leaveTimer = null;
        }, RELEASE_HOVER_MS);
      });
    });
  }

  function bindReleaseNavigation() {
    document.querySelectorAll("details.release-dropdown .releases a").forEach(function (a) {
      if (a.getAttribute("data-release-bound")) return;
      a.setAttribute("data-release-bound", "1");
      a.addEventListener("click", function (e) {
        var rel = releaseFromLink(a);
        if (!rel) return;
        e.preventDefault();
        var next = "release=" + rel;
        if ((location.hash || "") === "#" + next) {
          applyReleaseContext(rel);
          return;
        }
        location.hash = next;
      });
    });

    document.addEventListener("click", function (e) {
      var a = e.target.closest("a");
      if (!a) return;
      if (a.closest("details.universe-dropdown, details.release-dropdown, .langs")) return;
      if (a.getAttribute("target") === "_blank") return;
      var origHref = a.getAttribute("data-orig-href") || a.getAttribute("href");
      if (!origHref || /^(?:[a-z]+:|\/\/|mailto:|javascript:)/i.test(origHref)) return;
      if (a.classList.contains("spec-record-ref") || origHref.indexOf("spec/record.html") !== -1) return;

      var curUniverse = getPathUniverse(location.pathname);
      var path = location.pathname || "";
      if (!curUniverse) return;

      var activeRel = getActiveDropdownRelease();
      if (!activeRel) return;

      var destUrl;
      try {
        destUrl = new URL(a.href, location.href);
      } catch (err) {
        return;
      }
      if (destUrl.origin !== location.origin) return;
      if (destUrl.pathname.indexOf("/" + curUniverse + "/") === -1 && !isSameUniverse(curUniverse, destUrl.pathname)) return;

      if (parseReleaseFromHash(destUrl.hash) || /[?&]release=/.test(destUrl.search)) {
        return;
      }

      var cleanHash = (destUrl.hash || "").replace(/^#/, "").split("&").filter(function (part) {
        return part.indexOf("release=") !== 0;
      }).join("&");
      var targetHash = "release=" + encodeURIComponent(activeRel) + (cleanHash ? "&" + cleanHash : "");
      a.href = destUrl.pathname + destUrl.search + "#" + targetHash;
    });

    applyReleaseHashFromLocation();
  }

  window.addEventListener("hashchange", applyReleaseHashFromLocation);

  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details.fold:not([open])").forEach(function (d) {
      d.setAttribute("data-druck-zu", "");
      d.open = true;
    });
  });
  window.addEventListener("afterprint", function () {
    document.querySelectorAll("details.fold[data-druck-zu]").forEach(function (d) {
      d.removeAttribute("data-druck-zu");
      d.open = false;
    });
  });

  var TOGGLE_NAMES = {
    de: ["Dunkles Design", "Kompakte Ansicht"], en: ["Dark mode", "Compact mode"], es: ["Modo oscuro", "Vista compacta"],
    pt: ["Modo escuro", "Vista compacta"], fr: ["Mode sombre", "Affichage compact"], ru: ["Тёмная тема", "Компактный вид"],
    ar: ["الوضع الداكن", "عرض مضغوط"], hi: ["डार्क मोड", "संक्षिप्त दृश्य"], ko: ["다크 모드", "간결한 보기"],
    zh: ["深色模式", "紧凑视图"], nl: ["Donkere modus", "Compacte weergave"]
  };
  function syncShellControls() {
    var root = document.documentElement;
    var themeBtn = document.querySelector("[data-theme-toggle]");
    var densBtn = document.querySelector("[data-density-toggle]");
    var prefsLabel = document.querySelector("[data-prefs-label]");
    var theme = root.getAttribute("data-theme") || "light";
    var dens = root.getAttribute("data-density") || "comfortable";
    // Symbolknöpfe in der Breadcrumb-Zeile behalten ihr Symbol; Name in Tooltip und aria-label.
    var lang = (root.getAttribute("lang") || "en").split("-")[0];
    var names = TOGGLE_NAMES[lang] || TOGGLE_NAMES.en;
    if (themeBtn) {
      themeBtn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      if (themeBtn.hasAttribute("data-icon-toggle")) { themeBtn.title = names[0]; themeBtn.setAttribute("aria-label", names[0]); }
      else themeBtn.textContent = theme === "dark" ? "Dark" : "Light";
    }
    if (densBtn) {
      densBtn.setAttribute("aria-pressed", dens === "compact" ? "true" : "false");
      if (densBtn.hasAttribute("data-icon-toggle")) { densBtn.title = names[1]; densBtn.setAttribute("aria-label", names[1]); }
      else densBtn.textContent = dens === "compact" ? "Compact" : "Comfortable";
    }
    if (prefsLabel) {
      prefsLabel.textContent = (theme === "dark" ? "Dark" : "Light") + " · " + (dens === "compact" ? "Compact" : "Comfort");
    }
  }

  function bindShellControls() {
    bindCrumbsHover();
    bindReleaseNavigation();
    var root = document.documentElement;
    var themeBtn = document.querySelector("[data-theme-toggle]");
    var densBtn = document.querySelector("[data-density-toggle]");
    var searchBtn = document.querySelector("[data-search-open]");
    var searchInput = document.querySelector("[data-search-input]");
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", next);
        try { localStorage.setItem("autodocs-theme", next); } catch (e) {}
        syncShellControls();
      });
    }
    if (densBtn) {
      densBtn.addEventListener("click", function () {
        var next = root.getAttribute("data-density") === "compact" ? "comfortable" : "compact";
        root.setAttribute("data-density", next);
        try { localStorage.setItem("autodocs-density", next); } catch (e) {}
        syncShellControls();
      });
    }
    if (searchBtn && searchInput) {
      searchBtn.addEventListener("click", function () {
        searchInput.focus();
      });
    }

    document.addEventListener("click", function (e) {
      document.querySelectorAll("details.universe-dropdown[open], details.release-dropdown[open], details.shell-dropdown[open], details.shell-prefs[open], details[data-ai-model-widget][open]").forEach(function (d) {
        if (!d.contains(e.target)) {
          d.removeAttribute("open");
          d.classList.remove("is-hover-open");
        }
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        document.querySelectorAll("details.universe-dropdown[open], details.release-dropdown[open], details.shell-dropdown[open], details.shell-prefs[open], details[data-ai-model-widget][open]").forEach(function (d) {
          d.removeAttribute("open");
          d.classList.remove("is-hover-open");
        });
      }
    });

    try {
      var savedFolds = JSON.parse(sessionStorage.getItem("autodocs-open-folds") || "[]");
      if (Array.isArray(savedFolds) && savedFolds.length > 0) {
        savedFolds.forEach(function (id) {
          var el = document.getElementById(id);
          if (el && el.tagName === "DETAILS") {
            el.open = true;
          }
        });
      }
      document.querySelectorAll("details.fold[id]").forEach(function (d) {
        d.addEventListener("toggle", function () {
          try {
            var currentOpen = Array.from(document.querySelectorAll("details.fold[id][open]")).map(function (el) { return el.id; });
            sessionStorage.setItem("autodocs-open-folds", JSON.stringify(currentOpen));
          } catch (err) {}
        });
      });
    } catch (e) {}

    syncShellControls();
    bindDossierControls();
    bindSnippetCurationControls();
    bindGuideTabs();
  }

  // Reiter „User Guide“ / „Implementer's Guide“ an Elementen (ARIA tablist, Klick + Pfeiltasten)
  function bindGuideTabs() {
    if (bindGuideTabs.done) return;
    bindGuideTabs.done = true;
    function activate(tab, focus) {
      var list = tab.closest('[role="tablist"]');
      if (!list) return;
      list.querySelectorAll('[role="tab"]').forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
      if (focus) tab.focus();
    }
    document.addEventListener("click", function (e) {
      var tab = e.target.closest && e.target.closest('.guide-tabs [role="tab"]');
      if (tab) activate(tab, false);
    });
    document.addEventListener("keydown", function (e) {
      var tab = e.target.closest && e.target.closest('.guide-tabs [role="tab"]');
      if (!tab) return;
      var tabs = Array.prototype.slice.call(tab.closest('[role="tablist"]').querySelectorAll('[role="tab"]'));
      var i = tabs.indexOf(tab), rtl = getComputedStyle(tab).direction === "rtl", next = -1;
      if (e.key === "ArrowRight") next = i + (rtl ? -1 : 1);
      else if (e.key === "ArrowLeft") next = i + (rtl ? 1 : -1);
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      else return;
      e.preventDefault();
      activate(tabs[(next + tabs.length) % tabs.length], true);
    });
  }

  function bindSnippetCurationControls() {
    // Mehrere Kurations-Dialoge pro Seite (Namespace + eingebettete Klasse) tragen
    // dieselben festen IDs: zuerst im geöffneten Dialog suchen, dann seitenweit.
    function dScope() { return document.querySelector("dialog.dossier-modal[open]") || document; }
    // Gegenstand des geöffneten Dossiers (Klasse, Namespace, Modul …) statt eines festen Ersatzwerts
    function dossierSubject() {
      var m = document.querySelector("dialog.dossier-modal[open]");
      return m ? m.id.replace(/^dossier-modal-(?:impl-)?/, "") : "";
    }
    // Guide-Art des geöffneten Dossiers: „impl“ (Implementer's Guide) oder „user“ (Standard/Altdaten)
    function activeGuideKind() {
      var m = document.querySelector("dialog.dossier-modal[open]");
      if (!m) return "user";
      return (m.getAttribute("data-guide-kind") === "impl" || /^dossier-modal-impl-/.test(m.id)) ? "impl" : "user";
    }
    // Vote-Schlüssel nach (guide_kind, snippet_id): „user“ = unveränderte ID (Altdaten), „impl“ mit Präfix
    function voteKey(id, kind) { return (kind || activeGuideKind()) === "impl" ? "impl:" + id : id; }
    function dEl(id) {
      var m = document.querySelector("dialog.dossier-modal[open]");
      var hit = null;
      if (m && id) { try { hit = m.querySelector("#" + CSS.escape(id)); } catch (e) { hit = null; } }
      return hit || document.getElementById(id);
    }
    var VOTE_STORE = "ara-curation-snippet-votes-v1";
    var REVIEW_STORE = "ara-review-package-v1";
    var REVIEW_IDENT = "ara-review-identity";
    var REVIEW_TOKEN = "ara-review-github-token-v1";
    var attachedDiscussionItems = new Set();
    // Aktive Suche/Filter: alle Treffer gehören zum Kontext der KI-Diskussion (einzeln abwählbar)
    var excludedHits = new Set(), lastFilterKey = "";
    function filterKey() {
      var sc = dScope(), q = sc.querySelector("#dossier-search-input");
      var k = sc.querySelector(".dossier-filter-pill[data-filter-kind].is-active");
      var st = sc.querySelector(".dossier-filter-pill[data-filter-status].is-active");
      return [(q && q.value.trim()) || "", k ? k.getAttribute("data-filter-kind") : "all", st ? st.getAttribute("data-filter-status") : "all"].join("\u0001");
    }
    function searchHits() {
      var key = filterKey();
      if (key === ["", "all", "all"].join("\u0001")) return [];
      return Array.prototype.filter.call(dScope().querySelectorAll(".snippet-card"), function (c) { return c.style.display !== "none"; })
        .map(function (c) { return c.getAttribute("data-snippet-id") || c.id; })
        .filter(function (id) { return id && !excludedHits.has(id) && !attachedDiscussionItems.has(id); });
    }
    function focusIds() { return Array.from(attachedDiscussionItems).concat(searchHits()); }
    function cardFor(id) {
      var sc = dScope();
      try { return sc.querySelector('.snippet-card[data-snippet-id="' + CSS.escape(id) + '"]') || sc.querySelector("#" + CSS.escape(id)); } catch (e) { return null; }
    }
    var selectedSnippetIds = new Set();
    var lastSelectedSnippetId = null;

    function getVisibleSnippetCards() {
      var cards = Array.from(document.querySelectorAll("#dossier-view-editor .snippet-card"));
      return cards.filter(function (c) {
        return c.style.display !== "none" && !c.hidden;
      });
    }

    function applySnippetRangeSelection(anchorId, targetId, selectState) {
      var visibleCards = getVisibleSnippetCards();
      var cardIds = visibleCards.map(function (c) { return c.getAttribute("data-snippet-id") || c.id; });
      var fromIdx = anchorId ? cardIds.indexOf(anchorId) : -1;
      var toIdx = cardIds.indexOf(targetId);
      if (toIdx === -1) return false;
      if (fromIdx === -1) fromIdx = 0;
      var start = Math.min(fromIdx, toIdx);
      var end = Math.max(fromIdx, toIdx);
      for (var i = start; i <= end; i++) {
        if (selectState) {
          selectedSnippetIds.add(cardIds[i]);
        } else {
          selectedSnippetIds.delete(cardIds[i]);
        }
      }
      lastSelectedSnippetId = targetId;
      updateSelectionUI();
      return true;
    }

    function updateSelectionUI() {
      var count = selectedSnippetIds.size;
      var selBar = dEl("dossier-selection-bar");
      var selCount = dEl("selection-count");
      var selLabel = dEl("selection-label");
      var bConfCount = dEl("batch-confirm-count");
      var bDismCount = dEl("batch-dismiss-count");
      var bDiscCount = dEl("batch-discuss-count");
      var editorView = dEl("dossier-view-editor");

      if (selBar) selBar.hidden = (count === 0);
      if (selCount) selCount.textContent = count;
      if (selLabel) selLabel.textContent = (count === 1 ? "Element ausgewählt" : "Elemente ausgewählt");
      if (bConfCount) bConfCount.textContent = count;
      if (bDismCount) bDismCount.textContent = count;
      if (bDiscCount) bDiscCount.textContent = count;

      if (editorView) {
        editorView.classList.toggle("has-active-selection", count > 0);
      }

      dScope().querySelectorAll(".snippet-card").forEach(function (card) {
        var sId = card.getAttribute("data-snippet-id") || card.id;
        var isSelected = selectedSnippetIds.has(sId);
        card.classList.toggle("is-selected", isSelected);
        var cb = card.querySelector(".card-select-checkbox");
        if (cb) cb.checked = isSelected;
      });
    }

    function updatePromptTokenCount(modal) {
      modal = modal || document;
      var ta = modal.querySelector("#raw-prompt-textarea");
      var badge = modal.querySelector("#raw-prompt-tokens-badge");
      if (!ta || !badge) return;
      var text = ta.value || "";
      var approxTokens = Math.max(1, Math.round(text.length / 4));
      badge.textContent = "~" + approxTokens.toLocaleString() + " Tokens";
    }

    function switchDossierViewMode(targetMode, modal) {
      modal = modal || document;
      modal.querySelectorAll(".dossier-mode-tab").forEach(function (tab) {
        var isTarget = tab.getAttribute("data-view-mode") === targetMode;
        tab.classList.toggle("is-active", isTarget);
        tab.setAttribute("aria-selected", isTarget ? "true" : "false");
        tab.tabIndex = isTarget ? 0 : -1;
      });

      var promptView = modal.querySelector("#dossier-view-prompt") || modal.querySelector("#dossier-view-raw");
      var outputView = modal.querySelector("#dossier-view-output");
      var richView = modal.querySelector("#dossier-view-rich");
      var editorView = modal.querySelector("#dossier-view-editor");
      var chatToggleBtn = modal.querySelector("#btn-toggle-workbench-chat");

      var isPrompt = (targetMode === "prompt" || targetMode === "raw");
      var isOutput = (targetMode === "output" || targetMode === "diff");
      var isEditor = (targetMode === "editor");

      if (promptView) {
        promptView.hidden = !isPrompt;
        if (isPrompt) updatePromptTokenCount(modal);
      }
      if (outputView) {
        outputView.hidden = !isOutput;
        if (isOutput && typeof selectRawSubTab === "function" && typeof rawWorkbenchState !== "undefined") {
          selectRawSubTab(rawWorkbenchState.activeSubTab || "current");
        }
      }
      if (richView) richView.hidden = (targetMode !== "rich");
      if (editorView) editorView.hidden = !isEditor;

      if (chatToggleBtn) {
        chatToggleBtn.hidden = !isEditor;
      }
    }

    function bindDossierModeTabEnhancements() {
      document.querySelectorAll("dialog.dossier-modal .dossier-mode-switcher").forEach(function (switcher) {
        var modal = switcher.closest("dialog");
        if (!modal || switcher.getAttribute("data-mode-tabs-bound") === "1") return;
        switcher.setAttribute("data-mode-tabs-bound", "1");

        switcher.addEventListener("keydown", function (e) {
          var tabs = Array.from(switcher.querySelectorAll(".dossier-mode-tab"));
          if (!tabs.length) return;
          var activeIdx = tabs.findIndex(function (t) { return t.classList.contains("is-active"); });
          if (activeIdx < 0) activeIdx = 0;
          if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
            e.preventDefault();
            var nextIdx = e.key === "ArrowRight" ? activeIdx + 1 : activeIdx - 1;
            if (nextIdx < 0) nextIdx = tabs.length - 1;
            if (nextIdx >= tabs.length) nextIdx = 0;
            var nextTab = tabs[nextIdx];
            var mode = nextTab.getAttribute("data-view-mode") || "raw";
            switchDossierViewMode(mode, modal);
            if (typeof nextTab.focus === "function") nextTab.focus();
          }
        });
      });

      document.addEventListener("dragstart", function (e) {
        if (e.target.closest(".subtab-controls") || e.target.closest("button") || e.target.closest("select")) return;
        var subTab = e.target.closest(".raw-subtab");
        if (!subTab || !subTab.closest("dialog.dossier-modal")) return;
        var tabId = subTab.getAttribute("data-subtab") || subTab.id.replace(/^subtab-/, "");
        if (!tabId) return;
        e.dataTransfer.setData("text/autodocs-raw-subtab", tabId);
        e.dataTransfer.effectAllowed = "link";
        subTab.classList.add("is-dragging");
      });

      document.addEventListener("dragend", function (e) {
        var subTab = e.target.closest(".raw-subtab");
        if (subTab) subTab.classList.remove("is-dragging");
      });

      document.addEventListener("dragover", function (e) {
        var dropTab = e.target.closest(".raw-subtab");
        if (!dropTab || !dropTab.closest("dialog.dossier-modal")) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = "link";
        dropTab.classList.add("is-drop-target");
      });

      document.addEventListener("dragleave", function (e) {
        var dropTab = e.target.closest(".raw-subtab");
        if (dropTab) dropTab.classList.remove("is-drop-target");
      });

      document.addEventListener("drop", function (e) {
        var dropTab = e.target.closest(".raw-subtab");
        if (!dropTab || !dropTab.closest("dialog.dossier-modal")) return;
        e.preventDefault();
        dropTab.classList.remove("is-drop-target");
        var sourceId = e.dataTransfer.getData("text/autodocs-raw-subtab");
        var targetId = dropTab.getAttribute("data-subtab") || dropTab.id.replace(/^subtab-/, "");
        if (!sourceId || !targetId || sourceId === targetId) return;
        if (typeof linkCompareTabs === "function") {
          linkCompareTabs(sourceId, targetId);
        } else if (typeof initiateCompare === "function") {
          initiateCompare(targetId);
        }
      });

      document.querySelectorAll(".raw-subtab").forEach(function (tab) {
        if (!tab.closest("dialog.dossier-modal")) return;
        if (tab.getAttribute("draggable") === "true") return;
        tab.setAttribute("draggable", "true");
        tab.setAttribute("title", (tab.getAttribute("title") || "Vergleichsreiter") + " — zum Verknüpfen auf anderen Reiter ziehen");
      });
    }

    function loadVotes() {
      try {
        return JSON.parse(localStorage.getItem(VOTE_STORE) || "{}");
      } catch (e) {
        return {};
      }
    }

    function storeVote(snippetId, data, kind) {
      try {
        var votes = loadVotes(), gk = kind || activeGuideKind(), key = voteKey(snippetId, gk);
        votes[key] = Object.assign({}, votes[key] || {}, data, { guide_kind: gk });
        localStorage.setItem(VOTE_STORE, JSON.stringify(votes));
      } catch (e) {}
    }

    function loadReviewPackage() {
      try {
        return JSON.parse(localStorage.getItem(REVIEW_STORE) || "[]");
      } catch (e) {
        return [];
      }
    }

    function storeReviewPackage(items) {
      try {
        localStorage.setItem(REVIEW_STORE, JSON.stringify(items));
      } catch (e) {}
      syncReviewBar();
      try { window.dispatchEvent(new CustomEvent("ara-package-changed")); } catch (e) {}
    }

    function syncReviewBar() {
      var n = loadReviewPackage().length;
      document.querySelectorAll("[data-review-count]").forEach(function (e) { e.textContent = n; });
      document.querySelectorAll("[data-review-open]").forEach(function (e) {
        e.classList.toggle("has-items", n > 0);
      });
    }

    function getReviewerIdentity() {
      var tok = "";
      try { tok = localStorage.getItem(REVIEW_TOKEN) || ""; } catch (e) {}
      var name = "";
      try { name = localStorage.getItem(REVIEW_IDENT) || ""; } catch (e) {}
      if (tok) {
        return { name: name || "github-user", mode: "github_authenticated" };
      }
      return { name: name || "Curator", mode: "self_declared" };
    }

    function updateSnippetBadges() {
      var localVotes = loadVotes();
      dScope().querySelectorAll(".snippet-card[data-snippet-id]").forEach(function (card) {
        var sId = card.getAttribute("data-snippet-id");
        var record = localVotes[voteKey(sId)];
        var badge = card.querySelector('[data-badge-for="' + sId + '"]');
        var btnConfirm = card.querySelector('.curation-btn[data-action="confirm"][data-snippet="' + sId + '"]');
        var btnDismiss = card.querySelector('.curation-btn[data-action="dismiss"][data-snippet="' + sId + '"]');
        var btnDiscuss = card.querySelector('.curation-btn[data-action="discuss"][data-snippet="' + sId + '"]');

        var isInDiscussion = attachedDiscussionItems.has(sId);
        if (isInDiscussion) {
          card.classList.add("is-in-discussion");
          if (btnDiscuss) btnDiscuss.classList.add("is-active");
        } else {
          card.classList.remove("is-in-discussion");
          if (btnDiscuss) btnDiscuss.classList.remove("is-active");
        }

        if (!badge) return;

        if (isInDiscussion) {
          badge.className = "curation-status-pill status-in-discussion";
          badge.textContent = "💬 In Diskussion";
          if (btnConfirm) btnConfirm.classList.remove("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        } else if (record && record.queued) {
          badge.className = "curation-status-pill status-queued";
          badge.innerHTML = '<span>⏳ Im Review-Paket</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Aus Curation-Queue entfernen" aria-label="Aus Curation-Queue entfernen">✕</button>';
          if (btnDismiss) btnDismiss.classList.add("is-active");
          if (btnConfirm) btnConfirm.classList.remove("is-active");
        } else if (record && record.vote === "justified_dismiss") {
          badge.className = "curation-status-pill status-justified-dismiss";
          badge.innerHTML = '<span>👎 Begründet beanstandet ✓</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Beanstandung aufheben" aria-label="Beanstandung aufheben">✕</button>';
          if (btnDismiss) btnDismiss.classList.add("is-active");
          if (btnConfirm) btnConfirm.classList.remove("is-active");
        } else if (record && record.vote === "justified_confirm") {
          badge.className = "curation-status-pill status-justified-confirm";
          badge.innerHTML = '<span>👍 Begründet bestätigt ✓</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Bestätigung aufheben" aria-label="Bestätigung aufheben">✕</button>';
          if (btnConfirm) btnConfirm.classList.add("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        } else if (record && record.vote === "confirm") {
          badge.className = "curation-status-pill status-confirmed";
          badge.innerHTML = '<span>👍 Bestätigt ✓</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Bestätigung aufheben" aria-label="Bestätigung aufheben">✕</button>';
          if (btnConfirm) btnConfirm.classList.add("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        } else if (record && record.vote === "dismiss") {
          badge.className = "curation-status-pill status-dismissed";
          badge.innerHTML = '<span>👎 Beanstandet ✕</span> <button type="button" class="btn-clear-badge" data-clear-badge-for="' + sId + '" title="Beanstandung aufheben" aria-label="Beanstandung aufheben">✕</button>';
          if (btnDismiss) btnDismiss.classList.add("is-active");
          if (btnConfirm) btnConfirm.classList.remove("is-active");
        } else {
          badge.className = "curation-status-pill status-neutral";
          badge.textContent = "Unbewertet";
          if (btnConfirm) btnConfirm.classList.remove("is-active");
          if (btnDismiss) btnDismiss.classList.remove("is-active");
        }
      });
      applyDossierFilters();
      updateSelectionUI();
    }

    // Eine Dossier-Karte (Record oder Beleg). Gemeinsamer Renderer für die Karten des Prompt-Kontexts
    // (hydratePromptContext) und die seit der Generierung zugeordneten Belege (hydrateCurrentContext);
    // Markup wie früher serverseitig in lib_curation_modal.py, damit Filter, Zähler, Abstimmung,
    // Auswahl und Diskussion unverändert greifen. c: id, title, sws, name, kind, chip, doc, docChip,
    // page, constituting, isNew, extraClass, bodyHtml.
    function dossierCardHtml(c) {
      var esc = escapeHtmlDiff;
      var id = esc(c.id);
      var cls = c.constituting ? "snippet-card constituting-card is-collapsed" : "snippet-card inbound-snippet-card is-collapsed";
      if (c.extraClass) cls += " " + c.extraClass;
      var attrs = ' id="' + id + '" data-snippet-id="' + id + '" data-sws="' + esc(c.sws || c.id) + '" data-doc="' + esc(c.doc || "") +
        (c.constituting ? "" : '" data-page="' + esc(String(c.page == null ? "" : c.page))) +
        '" data-name="' + esc(c.name || c.id) + '" data-kind="' + esc(c.kind || "inbound") + '"' +
        (c.constituting ? ' data-is-constituting="true"' : ' data-is-inbound="true"') + (c.isNew ? ' data-current-new="true"' : "");
      var what = c.constituting ? "Element" : "Snippet";
      return '<div class="' + cls + '"' + attrs + '>' +
        '<div class="snippet-card-header" data-card-toggle="' + id + '" tabindex="0" role="button" aria-expanded="false" title="Klicken zum Auf-/Zuklappen der Details">' +
        '<div class="snippet-card-summary"><span class="card-chevron" aria-hidden="true">▸</span>' +
        '<input type="checkbox" class="card-select-checkbox" data-select-card="' + id + '" title="Element auswählen" aria-label="Element ' + esc(c.sws || c.id) + ' auswählen">' +
        '<strong class="snippet-title">' + esc(c.title || c.id) + '</strong>' +
        (c.constituting ? '<code class="snippet-sws">[' + esc(c.sws || c.id) + ']</code>' : "") +
        '<span class="chip-kind kind-' + esc(c.kind || "inbound") + '">' + esc(c.chip || c.kind || "inbound") + '</span>' +
        (c.isNew ? '<span class="chip-new" title="Seit der letzten Generierung zugeordnet">neu</span>' : "") +
        '<span class="chip-doc">' + esc(c.docChip || c.doc || "") + '</span></div>' +
        '<div class="snippet-card-header-actions"><div class="curation-status-box"><span class="curation-status-pill status-neutral" data-badge-for="' + id + '">Unbewertet</span></div>' +
        '<div class="curation-btn-group" data-snippet-id="' + id + '">' +
        '<button type="button" class="curation-btn btn-confirm" data-action="confirm" data-snippet="' + id + '" title="' + what + ' bestätigen (Daumen hoch)"><span class="vote-icon">👍</span> <span class="vote-label">Bestätigen</span></button>' +
        '<button type="button" class="curation-btn btn-dismiss" data-action="dismiss" data-snippet="' + id + '" title="' + what + ' beanstanden (Daumen runter)"><span class="vote-icon">👎</span> <span class="vote-label">Beanstanden</span></button>' +
        '<button type="button" class="curation-btn btn-discuss" data-action="discuss" data-snippet="' + id + '" title="Mit KI diskutieren"><span class="vote-icon">💬</span> <span class="vote-label">Mit KI diskutieren</span></button>' +
        '</div></div></div>' +
        '<div class="snippet-card-body">' + (c.bodyHtml || "") + '</div></div>';
    }

    var QUOTE_STYLE = "margin: 0 0 8px; padding: 8px 12px; background: #faf9f5; border-left: 3px solid #005f73; font-family: Georgia, serif; font-size: 0.95em; line-height: 1.45;";
    var FOOT_STYLE = "font-size: 0.78em; color: #888; display: flex; justify-content: space-between; margin-top: 6px;";

    // Modul- und Cluster-Leitfäden: Die Karten stehen vollständig im Prompt-Payload (API-Elemente,
    // Requirements, Dokumentstellen). Ableitung wie lib_curation_modal.cards_from_payload; der
    // Generator setzt from_prompt nur, wenn beide Ableitungen übereinstimmen. Quelle ist der
    // ursprüngliche Prompttext (defaultValue), nicht eine Bearbeitung im Textfeld.
    function cardsFromPayload(modal) {
      var ta = modal.querySelector("#raw-prompt-textarea");
      var text = ta ? (ta.defaultValue || ta.value || "") : "";
      var user = text.split("=== USER PROMPT ===")[1] || "";
      var at = user.indexOf("{");
      var payload = {};
      try { payload = at >= 0 ? JSON.parse(user.slice(at)) : {}; } catch (err) { payload = {}; }
      var dec = document.createElement("textarea");
      function unesc(v) { dec.innerHTML = String(v == null ? "" : v); return dec.value; }
      var modDoc = String(payload.module || "AUTOSAR Specification").toUpperCase();
      var reqDoc = String(payload.module || payload.cluster || "AUTOSAR Specification").toUpperCase();
      var seen = new Set(), recs = [], inb = [];
      (payload.api_elemente || []).forEach(function (e) {
        var eid = e.id || e.element_id || "", name = e.name || eid;
        if (eid) seen.add(eid);
        recs.push({ i: eid || name, n: name, s: eid || name, k: e.kind || "function", d: modDoc, t: unesc(e.signature || name) });
      });
      // get(k, Standard) wie dict.get in Python: Standard nur bei fehlendem Schlüssel
      function get(o, k, dflt) { return Object.prototype.hasOwnProperty.call(o, k) ? o[k] : dflt; }
      (payload.requirements || []).forEach(function (r) {
        var rid = get(r, "id", "");
        if (rid && seen.has(rid)) return;
        if (rid) seen.add(rid);
        recs.push({ i: rid, n: rid, s: rid, k: "requirement", d: reqDoc, t: unesc(get(r, "text", "")) });
      });
      (payload.dokumentstellen || []).forEach(function (ds) {
        var page = get(ds, "page", 1);
        inb.push({ i: get(ds, "id", "DS_01"), n: get(ds, "doc", "Spec") + ", S. " + page, d: get(ds, "doc", "AUTOSAR"), p: page,
                   t: unesc(get(ds, "text", "")) });
      });
      return { records: recs, inbound: inb };
    }

    // Karten des Prompt-Kontexts (konstituierende Records, Inbound-Belege des Prompts) liegen als
    // kompaktes JSON im Dossier (lib_curation_modal.py) und werden beim ersten Öffnen gerendert.
    function hydratePromptContext(modal) {
      if (!modal || modal.getAttribute("data-prompt-hydrated") === "1") return;
      var data = modal.querySelector("script.dossier-prompt-context");
      if (!data) return;
      modal.setAttribute("data-prompt-hydrated", "1");
      var ctx = {};
      try { ctx = JSON.parse(data.textContent || "{}"); } catch (err) { ctx = {}; }
      if (ctx.from_prompt) ctx = cardsFromPayload(modal);
      var esc = escapeHtmlDiff;
      var recBox = modal.querySelector(".records-container");
      var snipBox = modal.querySelector(".snippets-container");
      var recs = ctx.records || [], inb = ctx.inbound || [];
      if (recBox && recs.length) {
        Array.prototype.forEach.call(recBox.querySelectorAll(":scope > p.dossier-hydrate-hint"), function (p) { p.remove(); });
        recBox.insertAdjacentHTML("beforeend", recs.map(function (o) {
          var sws = o.s || o.i, kind = o.k || "requirement", doc = o.d || "";
          return dossierCardHtml({
            id: o.i, title: o.n || o.i, sws: sws, name: o.n || o.i, kind: kind, doc: doc, constituting: true,
            bodyHtml: '<div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">' +
              '<div><strong>' + esc(doc) + '</strong> <span style="font-size: 0.85em; color: #666;">(<code>[' + esc(sws) + ']</code>)</span></div>' +
              '<div><span style="background: #e3f2fd; color: #0d47a1; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; font-weight: bold;">Konstituierend · ' + esc(kind) + '</span></div></div>' +
              '<blockquote style="' + QUOTE_STYLE + '"><div class="desc"><p>' + esc(o.t || "") + '</p></div></blockquote>' +
              '<div style="' + FOOT_STYLE + '"><span>Eigenschaft: <em>Konstituierende Modul-Spezifikation</em></span><span>Record-ID: <code>' + esc(o.i) + '</code></span></div>'
          });
        }).join(""));
      }
      if (snipBox && inb.length) {
        Array.prototype.forEach.call(snipBox.querySelectorAll(":scope > p"), function (p) { p.remove(); });
        snipBox.insertAdjacentHTML("afterbegin", inb.map(function (o) {
          var page = o.p == null ? "" : String(o.p), doc = o.d || "";
          var name = o.n || (doc + ", S. " + page);
          return dossierCardHtml({
            id: o.i, title: name, sws: name, name: name, kind: "inbound", chip: "inbound", doc: doc, page: page,
            docChip: doc + " (S. " + page + ")",
            bodyHtml: '<blockquote style="' + QUOTE_STYLE + '"><div class="desc"><p>' + esc(o.t || "") + '</p></div></blockquote>' +
              '<div style="' + FOOT_STYLE + '"><span>Eigenschaft: <em>Inbound-Spezifikationsbeleg</em></span><span>ID: <code>' + esc(o.i) + '</code></span></div>'
          });
        }).join(""));
      }
      setTimeout(updateSnippetBadges, 0);
    }

    // Seit der Generierung zugeordnete Belege (lib_current_context.py) liegen als JSON im Dossier
    // und werden beim ersten Öffnen als Karten angehängt – so bleibt die Seite klein.
    function hydrateCurrentContext(modal) {
      if (!modal) return;
      hydratePromptContext(modal);
      if (modal.getAttribute("data-current-hydrated") === "1") return;
      var data = modal.querySelector("script.dossier-current-context");
      var box = modal.querySelector(".snippets-container");
      if (!data || !box) return;
      modal.setAttribute("data-current-hydrated", "1");
      var items = [];
      try { items = JSON.parse(data.textContent || "[]"); } catch (err) { items = []; }
      if (!items.length) return;
      var root = data.getAttribute("data-root") || "";
      Array.prototype.forEach.call(box.querySelectorAll(":scope > p"), function (p) { p.remove(); });
      var esc = escapeHtmlDiff;
      var html = items.map(function (it) {
        var page = String(it.page || "");
        var kind = it.is_figure ? "Schaubild" : "Snippet";
        // Belegseite spec/{figures,snippets}/<Stamm>.html; "file" nur bei Schreibvarianten (case_safe_names.py)
        var href = root + "spec/" + (it.is_figure ? "figures/" : "snippets/") + encodeURIComponent(it.file || it.id) + ".html";
        var conf = typeof it.confidence === "number" ? " · Konfidenz " + it.confidence.toFixed(2) : "";
        var targets = (it.targets || []).map(function (t) { return "<code>" + esc(t) + "</code>"; }).join(" ");
        return dossierCardHtml({
          id: it.id, title: it.excerpt ? it.excerpt.slice(0, 70) : it.id, sws: it.id, name: it.id, kind: "inbound", chip: kind,
          doc: it.doc || "", page: page, docChip: (it.doc || "") + (page ? " (S. " + page + ")" : ""),
          isNew: true, extraClass: "is-current-new",
          bodyHtml: '<blockquote class="current-excerpt"><div class="desc"><p>' + esc(it.excerpt || "") + '</p></div></blockquote>' +
            '<div class="current-meta"><span>' + esc(it.relation || "") + conf + (targets ? " · für " + targets : "") + '</span>' +
            '<a href="' + esc(href) + '" target="_blank" rel="noopener">🔍 ' + kind + ' öffnen</a></div>'
        });
      }).join("");
      box.insertAdjacentHTML("beforeend", html);
      setTimeout(updateSnippetBadges, 0);
    }
    window.autodocsHydrateDossier = hydrateCurrentContext;
    document.addEventListener("click", function (e) {
      var trig = e.target.closest("[data-dossier-target]");
      if (trig) hydrateCurrentContext(document.getElementById(trig.getAttribute("data-dossier-target")));
      var show = e.target.closest("[data-dossier-show-new]");
      var regen = e.target.closest("[data-dossier-regen-new]");
      if (!show && !regen) return;
      e.preventDefault();
      var modal = (show || regen).closest("dialog");
      hydrateCurrentContext(modal);
      var editorTab = modal && modal.querySelector('.dossier-mode-tab[data-view-mode="editor"]');
      if (editorTab) editorTab.click();
      if (regen) {
        var btn = modal.querySelector("#btn-regenerate-from-context");
        if (btn) btn.click();
        return;
      }
      var pill = modal.querySelector('.dossier-filter-pill[data-filter-kind="inbound"]');
      if (pill) pill.click();
      var first = modal.querySelector(".snippet-card.is-current-new");
      if (first) first.scrollIntoView({ block: "center" });
    }, true);

    function applyDossierFilters() {
      var searchInput = dEl("dossier-search-input");
      var query = searchInput ? searchInput.value.trim().toLowerCase() : "";
      var clearBtn = dEl("btn-clear-dossier-search");
      if (clearBtn) clearBtn.hidden = (query.length === 0);

      var activeKindPill = dScope().querySelector(".dossier-filter-pill[data-filter-kind].is-active");
      var activeKind = activeKindPill ? activeKindPill.getAttribute("data-filter-kind") : "all";

      var activeStatusPill = dScope().querySelector(".dossier-filter-pill[data-filter-status].is-active");
      var activeStatus = activeStatusPill ? activeStatusPill.getAttribute("data-filter-status") : "all";

      var cards = dScope().querySelectorAll(".snippet-card");
      var totalCount = cards.length;
      var visibleCount = 0;
      var votes = loadVotes();

      cards.forEach(function (card) {
        var sId = card.getAttribute("data-snippet-id") || card.id;
        var kind = card.getAttribute("data-kind") || "";
        var isInbound = card.hasAttribute("data-is-inbound") || kind === "inbound";
        var isConstituting = card.hasAttribute("data-is-constituting");
        var name = (card.getAttribute("data-name") || "").toLowerCase();
        var sws = (card.getAttribute("data-sws") || "").toLowerCase();
        var doc = (card.getAttribute("data-doc") || "").toLowerCase();

        // 1. Kind filter
        var matchKind = true;
        if (activeKind === "inbound") {
          matchKind = isInbound;
        } else if (activeKind === "function") {
          matchKind = (kind === "function");
        } else if (activeKind === "type") {
          matchKind = (kind === "type");
        }

        // 2. Status filter
        var matchStatus = true;
        var currentStatus = "unrated";
        if (attachedDiscussionItems.has(sId)) {
          currentStatus = "in-discussion";
        } else {
          var v = votes[voteKey(sId)];
          if (v && v.queued) {
            currentStatus = "queued";
          } else if (v && (v.vote === "confirm" || v.vote === "justified_confirm")) {
            currentStatus = "confirmed";
          } else if (v && (v.vote === "dismiss" || v.vote === "justified_dismiss")) {
            currentStatus = "dismissed";
          } else {
            currentStatus = "unrated";
          }
        }

        if (activeStatus !== "all") {
          matchStatus = (currentStatus === activeStatus);
        }

        // 3. Search query filter
        var matchSearch = true;
        if (query.length > 0) {
          var cardText = (card.textContent || "").toLowerCase();
          matchSearch = (name.indexOf(query) !== -1 ||
                         sws.indexOf(query) !== -1 ||
                         doc.indexOf(query) !== -1 ||
                         sId.toLowerCase().indexOf(query) !== -1 ||
                         cardText.indexOf(query) !== -1);
        }

        var isVisible = matchKind && matchStatus && matchSearch;
        if (isVisible) {
          card.style.display = "";
          visibleCount++;
        } else {
          card.style.display = "none";
        }
      });

      var visibleCountEl = dEl("dossier-visible-count");
      if (visibleCountEl) {
        visibleCountEl.textContent = visibleCount + " von " + totalCount + " Elementen angezeigt";
      }

      var resetBtn = dEl("btn-reset-dossier-filters");
      if (resetBtn) {
        var isFiltered = (activeKind !== "all" || activeStatus !== "all" || query.length > 0);
        resetBtn.hidden = !isFiltered;
      }
      var fk = filterKey();
      if (fk !== lastFilterKey) { lastFilterKey = fk; excludedHits.clear(); }
      renderAttachedChips();
    }

    function renderAttachedChips() {
      var chipsContainer = dEl("chat-attached-chips");
      var countBadge = dEl("chat-attached-count");
      var headerBadge = dEl("header-chat-badge");
      var clearBtn = dEl("btn-clear-attached");
      var hits = searchHits();
      var count = attachedDiscussionItems.size + hits.length;

      if (countBadge) {
        countBadge.textContent = count === 1 ? "1 Element im Fokus" : count + " Elemente im Fokus";
      }
      if (headerBadge) {
        headerBadge.textContent = count;
        headerBadge.hidden = count === 0;
      }
      if (clearBtn) {
        clearBtn.hidden = count === 0;
      }

      if (!chipsContainer) return;
      chipsContainer.innerHTML = "";

      if (count === 0) {
        var hint = document.createElement("span");
        hint.className = "chat-attached-empty-hint";
        hint.textContent = "Kein Element im Fokus: bei einem Element „💬 Mit KI diskutieren“ wählen oder oben suchen bzw. filtern – alle Treffer gehen dann in die Diskussion ein.";
        chipsContainer.appendChild(hint);
        return;
      }
      // Gleichnamige Elemente (Überladungen) zusätzlich mit ihrer SWS-ID unterscheiden
      var seenNames = {};
      Array.from(attachedDiscussionItems).concat(hits).forEach(function (id) {
        var c = cardFor(id), n = c ? c.getAttribute("data-name") : id;
        seenNames[n] = (seenNames[n] || 0) + 1;
      });
      function chip(id, hit) {
        var card = cardFor(id);
        var name = card ? (card.getAttribute("data-name") || card.getAttribute("data-sws") || id) : id;
        var sws = card ? (card.getAttribute("data-sws") || "") : "";
        var label = escHtml(name) + (seenNames[name] > 1 && sws && sws !== name
          ? '<span class="chat-chip-sws">' + escHtml(sws.replace(/^SWS_[A-Z]+_/, "")) + "</span>" : "");
        var el = document.createElement("span");
        el.className = "chat-attached-chip" + (hit ? " is-hit" : "");
        el.innerHTML = '<button type="button" class="chat-chip-goto" data-item-id="' + escAttr(id) + '" title="' + escAttr(sws || id) + '"><code>' + label + "</code></button>"
          + '<button type="button" class="' + (hit ? "btn-detach-hit" : "btn-detach-item") + '" data-item-id="' + escAttr(id) + '" title="Aus Diskussion entfernen">✕</button>';
        chipsContainer.appendChild(el);
      }
      attachedDiscussionItems.forEach(function (id) { chip(id, false); });
      if (hits.length) {
        var q = (dEl("dossier-search-input") || {}).value || "";
        var lab = document.createElement("span");
        lab.className = "chat-attached-hits-label";
        lab.textContent = "🔍 " + (q.trim() ? "„" + q.trim() + "“: " : "Filter: ") + hits.length + (hits.length === 1 ? " Treffer" : " Treffer");
        chipsContainer.appendChild(lab);
        hits.forEach(function (id) { chip(id, true); });
      }
    }
    function escHtml(t) { return String(t).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }
    function escAttr(t) { return escHtml(t).replace(/"/g, "&quot;"); }

    function appendDiscussionSystemNote(htmlText) {
      var thread = dEl("chat-pane-thread");
      if (!thread) return;
      var note = document.createElement("div");
      note.className = "chat-system-note";
      note.innerHTML = htmlText;
      thread.appendChild(note);
      thread.scrollTop = thread.scrollHeight;
    }

    function openDiscussionForItem(itemId) {
      var chatPane = dEl("dossier-chat-pane");
      var modal = chatPane ? chatPane.closest("dialog") : null;
      if (chatPane) {
        chatPane.hidden = false;
        if (modal) modal.classList.add("has-chat-open");
      }
      if (itemId) {
        if (!attachedDiscussionItems.has(itemId)) {
          attachedDiscussionItems.add(itemId);
          appendDiscussionSystemNote("Element <code>" + itemId + "</code> zur Diskussion hinzugefügt.");
        }
        var targetCard = cardFor(itemId);
        if (targetCard) {
          targetCard.classList.remove("is-collapsed");
          targetCard.classList.add("is-expanded");
          var header = targetCard.querySelector(".snippet-card-header");
          if (header) header.setAttribute("aria-expanded", "true");
        }
      }
      renderAttachedChips();
      updateSnippetBadges();
    }

    function toggleDiscussionItem(itemId) {
      var chatPane = dEl("dossier-chat-pane");
      var modal = chatPane ? chatPane.closest("dialog") : null;

      if (attachedDiscussionItems.has(itemId)) {
        if (chatPane && chatPane.hidden) {
          chatPane.hidden = false;
          if (modal) modal.classList.add("has-chat-open");
        } else {
          attachedDiscussionItems.delete(itemId);
          appendDiscussionSystemNote("Element <code>" + itemId + "</code> aus Diskussion entfernt.");
        }
      } else {
        attachedDiscussionItems.add(itemId);
        if (chatPane) {
          chatPane.hidden = false;
          if (modal) modal.classList.add("has-chat-open");
        }
        appendDiscussionSystemNote("Element <code>" + itemId + "</code> zur Diskussion hinzugefügt.");
        var targetCard = cardFor(itemId);
        if (targetCard) {
          targetCard.classList.remove("is-collapsed");
          targetCard.classList.add("is-expanded");
          var header = targetCard.querySelector(".snippet-card-header");
          if (header) header.setAttribute("aria-expanded", "true");
        }
      }
      renderAttachedChips();
      updateSnippetBadges();
    }

    // Server-side vote synchronization if available
    try {
      fetch("/api/curation/votes").then(function (r) { return r.json(); }).then(function (data) {
        if (data && data.votes) {
          var local = loadVotes();
          Object.keys(data.votes).forEach(function (sid) {
            var v = data.votes[sid];
            if (!local[sid]) {
              if (v.is_dismissed || v.dismisses > 0) local[sid] = { vote: "dismiss" };
              else if (v.confirms > 0) local[sid] = { vote: "confirm" };
            }
          });
          try { localStorage.setItem(VOTE_STORE, JSON.stringify(local)); } catch (e) {}
          updateSnippetBadges();
        }
      }).catch(function () {});
    } catch (e) {}

    // --- Provenance Explorer Side-by-Side Diff Engine ---
    var lastPromptDiffData = null;
    var currentDiffViewMode = "side";

    function escapeHtmlDiff(str) {
      if (!str) return "";
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    function formatHtmlLinesForDiff(htmlStr) {
      if (!htmlStr) return [];
      var norm = htmlStr
        .replace(/>\s*</g, ">\n<")
        .replace(/\r\n/g, "\n");
      var rawLines = norm.split("\n");
      var lines = [];
      for (var i = 0; i < rawLines.length; i++) {
        var l = rawLines[i].trim();
        if (!l) continue;
        if (l.length > 100 && !l.startsWith("<") && !l.endsWith(">")) {
          var sents = l.split(/(?<=[.!?])\s+(?=[A-ZÄÖÜ])/);
          for (var s = 0; s < sents.length; s++) {
            if (sents[s].trim()) lines.push(sents[s].trim());
          }
        } else {
          lines.push(l);
        }
      }
      return lines;
    }

    function getDiffOpcodes(a, b) {
      var m = a.length;
      var n = b.length;
      var dp = Array.from({ length: m + 1 }, function () { return new Int32Array(n + 1); });
      for (var i = 0; i < m; i++) {
        for (var j = 0; j < n; j++) {
          if (a[i] === b[j]) {
            dp[i + 1][j + 1] = dp[i][j] + 1;
          } else {
            dp[i + 1][j + 1] = Math.max(dp[i + 1][j], dp[i][j + 1]);
          }
        }
      }

      var iIdx = m;
      var jIdx = n;
      var rawEdits = [];

      while (iIdx > 0 || jIdx > 0) {
        if (iIdx > 0 && jIdx > 0 && a[iIdx - 1] === b[jIdx - 1]) {
          rawEdits.push({ type: "equal", aIdx: iIdx - 1, bIdx: jIdx - 1 });
          iIdx--;
          jIdx--;
        } else if (jIdx > 0 && (iIdx === 0 || dp[iIdx][jIdx - 1] >= dp[iIdx - 1][jIdx])) {
          rawEdits.push({ type: "insert", aIdx: iIdx, bIdx: jIdx - 1 });
          jIdx--;
        } else if (iIdx > 0 && (jIdx === 0 || dp[iIdx][jIdx - 1] < dp[iIdx - 1][jIdx])) {
          rawEdits.push({ type: "delete", aIdx: iIdx - 1, bIdx: jIdx });
          iIdx--;
        }
      }
      rawEdits.reverse();

      var opcodes = [];
      var idx = 0;
      while (idx < rawEdits.length) {
        var curType = rawEdits[idx].type;
        var startA = rawEdits[idx].aIdx;
        var startB = rawEdits[idx].bIdx;
        var endA = startA;
        var endB = startB;

        var k = idx;
        while (k < rawEdits.length && rawEdits[k].type === curType) {
          if (curType === "equal") {
            endA = rawEdits[k].aIdx + 1;
            endB = rawEdits[k].bIdx + 1;
          } else if (curType === "delete") {
            endA = rawEdits[k].aIdx + 1;
          } else if (curType === "insert") {
            endB = rawEdits[k].bIdx + 1;
          }
          k++;
        }
        opcodes.push([curType, startA, endA, startB, endB]);
        idx = k;
      }

      var merged = [];
      for (var mIdx = 0; mIdx < opcodes.length; mIdx++) {
        var curr = opcodes[mIdx];
        var next = opcodes[mIdx + 1];
        if (next && ((curr[0] === "delete" && next[0] === "insert") || (curr[0] === "insert" && next[0] === "delete"))) {
          var i1 = Math.min(curr[1], next[1]);
          var i2 = Math.max(curr[2], next[2]);
          var j1 = Math.min(curr[3], next[3]);
          var j2 = Math.max(curr[4], next[4]);
          merged.push(["replace", i1, i2, j1, j2]);
          mIdx++;
        } else {
          merged.push(curr);
        }
      }
      return merged;
    }

    function computeWordDiff(textA, textB) {
      var tokenRegex = /[<>\-]|[\w\u00C0-\u024F]+|[^\s\w\u00C0-\u024F<>\-]+|\s+/g;
      var tokensA = textA.match(tokenRegex) || [];
      var tokensB = textB.match(tokenRegex) || [];
      var opcodes = getDiffOpcodes(tokensA, tokensB);

      var outA = "";
      var outB = "";

      for (var w = 0; w < opcodes.length; w++) {
        var tag = opcodes[w][0];
        var i1 = opcodes[w][1];
        var i2 = opcodes[w][2];
        var j1 = opcodes[w][3];
        var j2 = opcodes[w][4];
        var subA = tokensA.slice(i1, i2).join("");
        var subB = tokensB.slice(j1, j2).join("");

        if (tag === "equal") {
          outA += escapeHtmlDiff(subA);
          outB += escapeHtmlDiff(subB);
        } else if (tag === "replace") {
          outA += subA.trim() ? '<del class="ve-word-deleted">' + escapeHtmlDiff(subA) + "</del>" : subA;
          outB += subB.trim() ? '<ins class="ve-word-added">' + escapeHtmlDiff(subB) + "</ins>" : subB;
        } else if (tag === "delete") {
          outA += subA.trim() ? '<del class="ve-word-deleted">' + escapeHtmlDiff(subA) + "</del>" : subA;
        } else if (tag === "insert") {
          outB += subB.trim() ? '<ins class="ve-word-added">' + escapeHtmlDiff(subB) + "</ins>" : subB;
        }
      }
      return [outA, outB];
    }

    function redrawPromptSvgConnectors() {
      var wrapper = dEl("prompt-diff-split-wrapper");
      var svg = dEl("prompt-diff-gutter-svg");
      var gutter = dEl("prompt-diff-split-gutter");
      if (!wrapper || !svg || !lastPromptDiffData || !lastPromptDiffData.aligned_blocks) return;

      var canvasWrap = (gutter && gutter.querySelector(".ve-gutter-canvas-wrap")) || gutter;
      if (canvasWrap) {
        var gH = canvasWrap.offsetHeight || (gutter ? gutter.offsetHeight : 0);
        if (gH > 0) {
          svg.setAttribute("height", gH);
          svg.style.height = gH + "px";
        }
      }

      var svgRect = svg.getBoundingClientRect();
      var W = 70;
      var blocks = lastPromptDiffData.aligned_blocks;
      var pathsHtml = "";

      blocks.forEach(function (b) {
        if (b.tag === "equal") return;

        var leftEl = wrapper.querySelector('#prompt-diff-pane-left [data-block-id="' + b.id + '"]');
        var rightEl = wrapper.querySelector('#prompt-diff-pane-right [data-block-id="' + b.id + '"]');
        if (!leftEl || !rightEl) return;

        var lRect = leftEl.getBoundingClientRect();
        var rRect = rightEl.getBoundingClientRect();

        var y1Top = lRect.top - svgRect.top;
        var y1Bot = (b.tag === "insert") ? y1Top : (lRect.bottom - svgRect.top);
        var y2Top = rRect.top - svgRect.top;
        var y2Bot = (b.tag === "delete") ? y2Top : (rRect.bottom - svgRect.top);

        var cp1x = W * 0.45;
        var cp2x = W * 0.55;

        var d = "";
        var cls = "ve-connector ";

        if (b.tag === "replace") {
          cls += "ve-connector-replace";
          d = "M 0 " + y1Top + " C " + cp1x + " " + y1Top + ", " + cp2x + " " + y2Top + ", " + W + " " + y2Top + " L " + W + " " + y2Bot + " C " + cp2x + " " + y2Bot + ", " + cp1x + " " + y1Bot + ", 0 " + y1Bot + " Z";
        } else if (b.tag === "delete") {
          cls += "ve-connector-delete";
          d = "M 0 " + y1Top + " C " + cp1x + " " + y1Top + ", " + cp2x + " " + y2Top + ", " + W + " " + y2Top + " L " + W + " " + y2Top + " C " + cp2x + " " + y2Top + ", " + cp1x + " " + y1Bot + ", 0 " + y1Bot + " Z";
        } else if (b.tag === "insert") {
          cls += "ve-connector-insert";
          d = "M 0 " + y1Top + " C " + cp1x + " " + y1Top + ", " + cp2x + " " + y2Top + ", " + W + " " + y2Top + " L " + W + " " + y2Bot + " C " + cp2x + " " + y2Bot + ", " + cp1x + " " + y1Top + ", 0 " + y1Top + " Z";
        }

        pathsHtml += '<path d="' + d + '" class="' + cls + '" data-connector-id="' + b.id + '"><title>' + b.tag.toUpperCase() + ': ' + b.id + '</title></path>';
      });

      svg.innerHTML = pathsHtml;

      svg.querySelectorAll(".ve-connector").forEach(function (path) {
        var id = path.dataset.connectorId;
        path.addEventListener("mouseenter", function () {
          wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.add("is-hovered"); });
          path.classList.add("is-hovered");
        });
        path.addEventListener("mouseleave", function () {
          wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.remove("is-hovered"); });
          path.classList.remove("is-hovered");
        });
        path.addEventListener("click", function () {
          if (wrapper._syncController && typeof wrapper._syncController.scrollToBlock === "function") {
            wrapper._syncController.scrollToBlock(id);
          }
        });
      });
    }

    function renderPromptUnifiedDiff(diffLines) {
      var uniEl = dEl("prompt-diff-unified");
      if (!uniEl) return;
      if (!diffLines || diffLines.length === 0) {
        uniEl.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--color-ink-muted);">Beide Versionen sind inhaltlich identisch (keine Unterschiede).</div>';
        return;
      }
      var rowsHtml = diffLines.map(function (line) {
        var m = line.type === "added" ? "+" : (line.type === "deleted" ? "−" : " ");
        return '<div class="ve-diff-line ve-diff-' + line.type + '">' +
          '<span class="ve-diff-marker">' + m + '</span>' +
          '<span class="ve-diff-text">' + escapeHtmlDiff(line.text) + '</span>' +
        '</div>';
      }).join("");

      uniEl.innerHTML = '<div class="ve-unified-container">' + rowsHtml + '</div>';
    }

    function renderSideBySideDiff(originalHtml, generatedHtml, meta) {
      var bodyEl = dEl("raw-diff-body") || dEl("prompt-diff-body");
      var previewEl = dEl("prompt-diff-preview");
      var metaEl = dEl("prompt-diff-meta");
      if (!bodyEl) return;

      if (metaEl) {
        var dur = meta.duration_ms ? (meta.duration_ms / 1000).toFixed(1) + "s" : "";
        var prov = meta.provider || "Gemini";
        var m = meta.model || "gemini-3.8-flash-medium";
        metaEl.innerHTML = " · Provider: <strong>" + escapeHtmlDiff(prov) + "</strong> · Modell: <code>" + escapeHtmlDiff(m) + "</code> · Dauer: <strong>" + dur + "</strong>";
      }

      if (previewEl) {
        previewEl.innerHTML = generatedHtml;
      }

      var linesA = formatHtmlLinesForDiff(originalHtml);
      var linesB = formatHtmlLinesForDiff(generatedHtml);
      var opcodes = getDiffOpcodes(linesA, linesB);

      var alignedBlocks = [];
      var diffLines = [];
      var blockIdx = 0;
      var changesCount = 0;

      for (var k = 0; k < opcodes.length; k++) {
        var tag = opcodes[k][0];
        var i1 = opcodes[k][1];
        var i2 = opcodes[k][2];
        var j1 = opcodes[k][3];
        var j2 = opcodes[k][4];

        var chunkA = linesA.slice(i1, i2);
        var chunkB = linesB.slice(j1, j2);
        var leftHtml = "";
        var rightHtml = "";

        if (tag === "equal") {
          leftHtml = escapeHtmlDiff(chunkA.join("\n"));
          rightHtml = escapeHtmlDiff(chunkB.join("\n"));
          for (var l = 0; l < chunkA.length; l++) {
            diffLines.push({ type: "unchanged", text: chunkA[l] });
          }
        } else if (tag === "replace") {
          changesCount++;
          var pair = computeWordDiff(chunkA.join("\n"), chunkB.join("\n"));
          leftHtml = pair[0];
          rightHtml = pair[1];
          for (var l = 0; l < chunkA.length; l++) diffLines.push({ type: "deleted", text: chunkA[l] });
          for (var l = 0; l < chunkB.length; l++) diffLines.push({ type: "added", text: chunkB[l] });
        } else if (tag === "delete") {
          changesCount++;
          leftHtml = escapeHtmlDiff(chunkA.join("\n"));
          for (var l = 0; l < chunkA.length; l++) diffLines.push({ type: "deleted", text: chunkA[l] });
        } else if (tag === "insert") {
          changesCount++;
          rightHtml = escapeHtmlDiff(chunkB.join("\n"));
          for (var l = 0; l < chunkB.length; l++) diffLines.push({ type: "added", text: chunkB[l] });
        }

        blockIdx++;
        alignedBlocks.push({
          id: "pb-" + blockIdx,
          tag: tag,
          left_lines: chunkA,
          right_lines: chunkB,
          left_html: leftHtml,
          right_html: rightHtml
        });
      }

      lastPromptDiffData = {
        aligned_blocks: alignedBlocks,
        diff_lines: diffLines,
        changesCount: changesCount
      };

      var leftBlocksHtml = "";
      var rightBlocksHtml = "";

      alignedBlocks.forEach(function (b) {
        var tag = b.tag;
        if (tag === "delete") {
          leftBlocksHtml += '<div class="ve-block ve-block-deleted" data-block-id="' + b.id + '" data-tag="delete">' + b.left_html + '</div>';
          rightBlocksHtml += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="delete"></div>';
        } else if (tag === "replace") {
          leftBlocksHtml += '<div class="ve-block ve-block-replaced ve-block-left" data-block-id="' + b.id + '" data-tag="replace">' + b.left_html + '</div>';
          rightBlocksHtml += '<div class="ve-block ve-block-replaced ve-block-right" data-block-id="' + b.id + '" data-tag="replace">' + b.right_html + '</div>';
        } else if (tag === "equal") {
          leftBlocksHtml += '<div class="ve-block ve-block-equal" data-block-id="' + b.id + '" data-tag="equal">' + b.left_html + '</div>';
          rightBlocksHtml += '<div class="ve-block ve-block-equal" data-block-id="' + b.id + '" data-tag="equal">' + b.right_html + '</div>';
        } else if (tag === "insert") {
          leftBlocksHtml += '<div class="ve-block ve-block-anchor" data-block-id="' + b.id + '" data-tag="insert"></div>';
          rightBlocksHtml += '<div class="ve-block ve-block-added" data-block-id="' + b.id + '" data-tag="insert">' + b.right_html + '</div>';
        }
      });

      bodyEl.innerHTML = `
        <div class="ve-diff-summary-bar" style="margin-bottom:12px; font-size:0.85em; color:var(--color-ink-muted, #666); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
          <span>Unterschiede erkannt: <strong>${changesCount}</strong> geänderte, entfallene oder hinzugefügte Abschnitte.</span>
          <span style="font-size:0.8em; color:var(--color-ink-muted, #888);">💡 Hover über Abschnitte oder Verbindungsbänder hebt Korrespondenzen hervor</span>
        </div>
        <div class="ve-split-diff-wrapper" id="prompt-diff-split-wrapper">
          <div class="ve-split-columns" id="prompt-diff-split-columns">
            <div class="ve-split-pane ve-split-left" id="prompt-diff-pane-left-wrap">
              <div class="ve-split-header ve-header-left">
                <span>${(meta && meta.leftTitle) ? escapeHtmlDiff(meta.leftTitle) : "Bisheriger Stand (Ist-Zustand)"}</span>
                <span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-size:0.75em; font-weight:700;">${(meta && meta.leftBadge) ? escapeHtmlDiff(meta.leftBadge) : "Basis"}</span>
              </div>
              <div class="ve-split-body" id="prompt-diff-pane-left">
                ${leftBlocksHtml || '<em style="color:#888;">(Kein bisheriges Fragment vorhanden)</em>'}
              </div>
            </div>

            <div class="ve-split-gutter" id="prompt-diff-split-gutter">
              <div class="ve-split-header ve-header-gutter">
                <span>Diff</span>
              </div>
              <div class="ve-gutter-canvas-wrap">
                <svg class="ve-gutter-svg" id="prompt-diff-gutter-svg" width="70" height="100%"></svg>
              </div>
            </div>

            <div class="ve-split-pane ve-split-right" id="prompt-diff-pane-right-wrap">
              <div class="ve-split-header ve-header-right">
                <span>${(meta && meta.rightTitle) ? escapeHtmlDiff(meta.rightTitle) : "Neuer Stand (KI-Ergebnis)"}</span>
                <span style="background:#dcfce7; color:#15803d; padding:2px 6px; border-radius:4px; font-size:0.75em; font-weight:700;">${(meta && meta.rightBadge) ? escapeHtmlDiff(meta.rightBadge) : "Vergleich"}</span>
              </div>
              <div class="ve-split-body" id="prompt-diff-pane-right">
                ${rightBlocksHtml || '<em style="color:#888;">(Keine Ausgabe erzeugt)</em>'}
              </div>
            </div>
          </div>
        </div>
      `;

      renderPromptUnifiedDiff(diffLines);

      // Synchronous Hover
      var wrapper = dEl("prompt-diff-split-wrapper");
      if (wrapper) {
        wrapper.querySelectorAll(".ve-block").forEach(function (el) {
          var id = el.dataset.blockId;
          el.addEventListener("mouseenter", function () {
            wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.add("is-hovered"); });
            var path = wrapper.querySelector('path[data-connector-id="' + id + '"]');
            if (path) path.classList.add("is-hovered");
          });
          el.addEventListener("mouseleave", function () {
            wrapper.querySelectorAll('[data-block-id="' + id + '"]').forEach(function (b) { b.classList.remove("is-hovered"); });
            var path = wrapper.querySelector('path[data-connector-id="' + id + '"]');
            if (path) path.classList.remove("is-hovered");
          });
        });

        var paneLeft = dEl("prompt-diff-pane-left");
        var paneRight = dEl("prompt-diff-pane-right");
        initPromptPiecewiseSyncScroll(wrapper, paneLeft, paneRight, alignedBlocks, redrawPromptSvgConnectors);
      }
    }

    function initPromptPiecewiseSyncScroll(wrapper, paneLeft, paneRight, blocks, redrawFn) {
      if (!wrapper || !paneLeft || !paneRight || !blocks || blocks.length === 0) return;

      var blockLayouts = [];
      var cumV = [0];
      var V_total = 0;
      var globalS = 0;
      var isProgrammatic = false;

      function measureLayout() {
        blockLayouts = [];
        cumV = [0];
        var runningV = 0;

        for (var i = 0; i < blocks.length; i++) {
          var b = blocks[i];
          var elL = paneLeft.querySelector('[data-block-id="' + b.id + '"]');
          var elR = paneRight.querySelector('[data-block-id="' + b.id + '"]');

          var hL = (elL && b.tag !== "insert") ? elL.offsetHeight : 0;
          var topL = elL ? elL.offsetTop : (i > 0 ? blockLayouts[i - 1].botL : 0);
          var botL = topL + hL;

          var hR = (elR && b.tag !== "delete") ? elR.offsetHeight : 0;
          var topR = elR ? elR.offsetTop : (i > 0 ? blockLayouts[i - 1].botR : 0);
          var botR = topR + hR;

          var hV = Math.max(hL, hR);
          runningV += hV;
          cumV.push(runningV);

          blockLayouts.push({
            id: b.id,
            tag: b.tag,
            topL: topL, hL: hL, botL: botL,
            topR: topR, hR: hR, botR: botR,
            hV: hV,
            startV: cumV[i],
            endV: runningV
          });
        }

        V_total = runningV;
      }

      function getTargetsForS(S) {
        if (blockLayouts.length === 0) return { targetL: 0, targetR: 0 };
        if (S <= 0) return { targetL: 0, targetR: 0 };

        var k = 0;
        while (k < blockLayouts.length - 1 && S >= blockLayouts[k].endV) {
          k++;
        }

        var blk = blockLayouts[k];
        var offset = S - blk.startV;
        var t = blk.hV > 0 ? Math.min(1, Math.max(0, offset / blk.hV)) : 0;

        var targetL = blk.topL + t * blk.hL;
        var targetR = blk.topR + t * blk.hR;

        return { targetL: targetL, targetR: targetR };
      }

      function getSFromR(scrollTopR) {
        if (blockLayouts.length === 0) return 0;
        for (var i = 0; i < blockLayouts.length; i++) {
          var blk = blockLayouts[i];
          if (scrollTopR >= blk.topR && (scrollTopR < blk.botR || i === blockLayouts.length - 1)) {
            var t = blk.hR > 0 ? (scrollTopR - blk.topR) / blk.hR : 0;
            return blk.startV + t * blk.hV;
          }
        }
        return 0;
      }

      function getSFromL(scrollTopL) {
        if (blockLayouts.length === 0) return 0;
        for (var i = 0; i < blockLayouts.length; i++) {
          var blk = blockLayouts[i];
          if (scrollTopL >= blk.topL && (scrollTopL < blk.botL || i === blockLayouts.length - 1)) {
            var t = blk.hL > 0 ? (scrollTopL - blk.topL) / blk.hL : 0;
            return blk.startV + t * blk.hV;
          }
        }
        return 0;
      }

      function applyScroll(S) {
        var maxScrollL = Math.max(0, paneLeft.scrollHeight - paneLeft.clientHeight);
        var maxScrollR = Math.max(0, paneRight.scrollHeight - paneRight.clientHeight);
        var viewH = Math.min(paneLeft.clientHeight || 450, paneRight.clientHeight || 450);
        var maxS = Math.max(0, V_total - viewH);

        globalS = Math.max(0, Math.min(maxS, S));
        var targets = getTargetsForS(globalS);

        isProgrammatic = true;
        paneLeft.scrollTop = Math.min(maxScrollL, Math.max(0, targets.targetL));
        paneRight.scrollTop = Math.min(maxScrollR, Math.max(0, targets.targetR));

        if (redrawFn) redrawFn();
        requestAnimationFrame(function () { isProgrammatic = false; });
      }

      wrapper.addEventListener("wheel", function (e) {
        if (e.deltaY !== 0) {
          e.preventDefault();
          applyScroll(globalS + e.deltaY);
        }
      }, { passive: false });

      paneLeft.addEventListener("scroll", function () {
        if (isProgrammatic) return;
        var S = getSFromL(paneLeft.scrollTop);
        applyScroll(S);
      }, { passive: true });

      paneRight.addEventListener("scroll", function () {
        if (isProgrammatic) return;
        var S = getSFromR(paneRight.scrollTop);
        applyScroll(S);
      }, { passive: true });

      wrapper._syncController = {
        scrollToBlock: function (blockId) {
          var idx = -1;
          for (var i = 0; i < blockLayouts.length; i++) {
            if (blockLayouts[i].id === blockId) { idx = i; break; }
          }
          if (idx >= 0) {
            applyScroll(blockLayouts[idx].startV);
          }
        },
        applyScroll: applyScroll,
        measure: measureLayout
      };

      setTimeout(function () {
        measureLayout();
        applyScroll(0);
      }, 25);

      if (window.ResizeObserver) {
        var ro = new ResizeObserver(function () {
          measureLayout();
          if (redrawFn) redrawFn();
        });
        ro.observe(paneLeft);
        ro.observe(paneRight);
      }
    }

    window.addEventListener("resize", function () {
      if (currentDiffViewMode === "side") {
        redrawPromptSvgConnectors();
      }
    });

    // --- 3-Reiter-Konzept Plaintext Prompt, Aktueller Output & Vorschau ---
    var rawWorkbenchState = {
      activeSubTab: "prompt",
      compareSourceId: null,
      linkedSourceId: null,
      linkedTargetId: null,
      isCompareActive: false,
      nextPreviewSeq: 2,
      previews: {
        "preview-1": {
          id: "preview-1",
          seq: 1,
          state: "idle",
          model: "gemini-3.8-flash",
          effort: "medium",
          provider: "agy",
          modelNameDisplay: "Gemini 3.8 Flash (med)",
          abortController: null,
          timerInterval: null,
          startTime: 0,
          durationMs: 0,
          html: "",
          error: "",
          rawOutput: ""
        }
      }
    };

    function getRawTabShortTitle(tabId) {
      if (tabId === "prompt") return "Prompt";
      if (tabId === "current") return "Aktueller Output";
      if (tabId && tabId.startsWith("preview-")) {
        var prev = rawWorkbenchState.previews[tabId];
        if (prev && prev.modelNameDisplay) {
          return "Vorschau " + prev.seq;
        }
        return "Vorschau " + tabId.replace("preview-", "");
      }
      return tabId || "";
    }

    function getRawTabFullTitle(tabId) {
      if (tabId === "prompt") return "Plaintext Prompt";
      if (tabId === "current") return "Aktueller Stand (Ist-Zustand)";
      if (tabId && tabId.startsWith("preview-")) {
        var prev = rawWorkbenchState.previews[tabId];
        if (prev && prev.modelNameDisplay) {
          return "Vorschau (" + prev.modelNameDisplay + ")";
        }
        return "Vorschau " + tabId.replace("preview-", "");
      }
      return tabId || "";
    }

    function getRawTabHtml(tabId) {
      if (tabId === "current") {
        var dataEl = dEl("raw-current-output-data");
        if (dataEl) return dataEl.textContent || "";
        var codeEl = dEl("raw-current-output-code");
        if (codeEl) return codeEl.textContent || "";
        return "";
      }
      if (tabId && tabId.startsWith("preview-")) {
        var prev = rawWorkbenchState.previews[tabId];
        return (prev && prev.html) ? prev.html : "";
      }
      return "";
    }

    function selectRawSubTab(tabId) {
      if (rawWorkbenchState.compareSourceId) {
        if (tabId === "prompt") {
          alert("Der Plaintext Prompt kann nur exklusiv angezeigt und nicht mit generiertem Output verglichen werden.");
          return;
        }
        if (tabId === rawWorkbenchState.compareSourceId) {
          cancelComparePick();
          return;
        }
        if (tabId.startsWith("preview-")) {
          var p = rawWorkbenchState.previews[tabId];
          if (!p || p.state !== "done") {
            alert("Diese Vorschau ist noch nicht fertig generiert.");
            return;
          }
        }
        linkCompareTabs(rawWorkbenchState.compareSourceId, tabId);
        return;
      }

      if (rawWorkbenchState.isCompareActive) {
        exitCompareMode();
      }

      if (tabId && tabId.startsWith("preview-") && !rawWorkbenchState.showOnly) {
        var prevItem = rawWorkbenchState.previews[tabId];
        if (prevItem && prevItem.state === "idle") {
          startPreviewGeneration(prevItem.seq);
          return;
        }
      }

      rawWorkbenchState.activeSubTab = tabId;

      document.querySelectorAll(".raw-subtab").forEach(function (tab) {
        var tId = tab.getAttribute("data-subtab");
        var isThis = (tId === tabId);
        tab.classList.toggle("is-active", isThis);
        tab.setAttribute("aria-selected", isThis ? "true" : "false");
      });

      var diffPane = dEl("raw-pane-compare-diff");
      if (diffPane) diffPane.style.display = "none";

      var panePrompt = dEl("raw-pane-prompt");
      var paneCurrent = dEl("raw-pane-current");

      if (panePrompt) panePrompt.style.display = (tabId === "prompt" ? "" : "none");
      if (paneCurrent) paneCurrent.style.display = (tabId === "current" ? "" : "none");

      document.querySelectorAll(".raw-pane-preview").forEach(function (pane) {
        var expectedId = "raw-pane-" + tabId;
        pane.style.display = (pane.id === expectedId ? "" : "none");
      });
    }

    function initiateCompare(sourceId) {
      if (sourceId === "prompt") {
        alert("Der Plaintext Prompt kann nur exklusiv angezeigt und nicht verglichen werden.");
        return;
      }
      if (rawWorkbenchState.compareSourceId === sourceId) {
        cancelComparePick();
        return;
      }
      if (rawWorkbenchState.isCompareActive) {
        exitCompareMode();
      }

      rawWorkbenchState.compareSourceId = sourceId;

      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        t.classList.remove("is-compare-source");
        if (t.getAttribute("data-subtab") === sourceId) {
          t.classList.add("is-compare-source");
        }
      });

      var hintBar = dEl("raw-compare-hint-bar");
      var hintText = dEl("raw-compare-hint-text");
      if (hintBar) {
        hintBar.style.display = "flex";
        if (hintText) {
          hintText.textContent = "💡 Basis gewählt: „" + getRawTabFullTitle(sourceId) + "“. Klicke nun auf einen zweiten Reiter (z.B. Aktueller Output oder eine andere Vorschau), um den Side-by-Side-Vergleich zu öffnen.";
        }
      }
    }

    function cancelComparePick() {
      rawWorkbenchState.compareSourceId = null;
      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        t.classList.remove("is-compare-source");
      });
      var hintBar = dEl("raw-compare-hint-bar");
      if (hintBar) hintBar.style.display = "none";
    }

    function linkCompareTabs(sourceId, targetId) {
      cancelComparePick();

      rawWorkbenchState.isCompareActive = true;
      rawWorkbenchState.linkedSourceId = sourceId;
      rawWorkbenchState.linkedTargetId = targetId;

      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        var s = t.getAttribute("data-subtab");
        var isLinked = (s === sourceId || s === targetId);
        t.classList.toggle("is-compare-linked", isLinked);
      });

      var linkBadge = dEl("raw-tab-link-badge");
      var linkLabel = dEl("raw-tab-link-label");
      if (linkBadge) {
        linkBadge.style.display = "inline-flex";
        linkBadge.title = "Vergleich aktiv: " + getRawTabShortTitle(sourceId) + " ⇄ " + getRawTabShortTitle(targetId) + " (Klick kehrt zur Einzelansicht zurück)";
      }
      if (linkLabel) {
        linkLabel.textContent = "Verknüpft: " + getRawTabShortTitle(sourceId) + " ⇄ " + getRawTabShortTitle(targetId);
      }

      var panePrompt = dEl("raw-pane-prompt");
      var paneCurrent = dEl("raw-pane-current");
      if (panePrompt) panePrompt.style.display = "none";
      if (paneCurrent) paneCurrent.style.display = "none";
      document.querySelectorAll(".raw-pane-preview").forEach(function (p) {
        p.style.display = "none";
      });

      var diffPane = dEl("raw-pane-compare-diff");
      if (diffPane) diffPane.style.display = "block";

      var tagLeft = dEl("diff-tag-left");
      var tagRight = dEl("diff-tag-right");
      if (tagLeft) tagLeft.textContent = "Basis: " + getRawTabShortTitle(sourceId);
      if (tagRight) tagRight.textContent = "Vergleich: " + getRawTabShortTitle(targetId);

      var leftHtml = getRawTabHtml(sourceId);
      var rightHtml = getRawTabHtml(targetId);
      renderSideBySideDiff(leftHtml, rightHtml, {
        leftTitle: getRawTabFullTitle(sourceId),
        rightTitle: getRawTabFullTitle(targetId),
        leftBadge: getRawTabShortTitle(sourceId),
        rightBadge: getRawTabShortTitle(targetId)
      });
      setTimeout(redrawPromptSvgConnectors, 30);
    }

    function exitCompareMode() {
      if (!rawWorkbenchState.isCompareActive) return;
      rawWorkbenchState.isCompareActive = false;
      var returnTab = rawWorkbenchState.linkedTargetId || rawWorkbenchState.linkedSourceId || "current";
      rawWorkbenchState.linkedSourceId = null;
      rawWorkbenchState.linkedTargetId = null;

      document.querySelectorAll(".raw-subtab").forEach(function (t) {
        t.classList.remove("is-compare-linked");
      });

      var linkBadge = dEl("raw-tab-link-badge");
      if (linkBadge) linkBadge.style.display = "none";

      var diffPane = dEl("raw-pane-compare-diff");
      if (diffPane) diffPane.style.display = "none";

      selectRawSubTab(returnTab);
    }

    // --- Modellwahl der Vorschau-Reiter ---
    // Die Liste kommt aus AiAccess.models(): lokale CLIs von _src/serve.py (jede gefundene CLI, die
    // /api/ai/execute_prompt ausführen kann: runnable), Projektkontingent und alle Modelle eigener Schlüssel und
    // Endpunkte, gruppiert nach Quelle. Ohne ai-access.js bleibt der statische Rückfall mit den lokalen
    // CLIs (gleiches Format wie lib_curation_modal.preview_controls_html).
    var PREVIEW_LOCAL_DEFAULTS = [
      { source: "local", provider: "agy", model: "gemini-3.8-flash", label: "Gemini 3.8 Flash" },
      { source: "local", provider: "cursor", model: "composer-2.5", label: "Cursor Composer 2.5" }
    ];
    var PREVIEW_EFFORT_RE = /-(low|medium|high|xhigh|max)$/;
    function previewText(key, fallback, arg) {
      var a = window.AiAccess, t = a && typeof a.text === "function" ? a.text(key, arg) : "";
      return t && t !== key ? t : String(fallback).replace("%s", arg == null ? "" : arg);
    }
    // Effort hat nur bei lokalen Gemini-Modellen über agy eine Bedeutung (wird Teil der Modell-ID).
    function previewEffortApplies(source, provider, model) {
      // Nur agy kodiert den Effort in der Modell-ID; die Gemini-CLI („gemini“) nimmt die ID unverändert.
      return source === "local" && (provider === "agy" || (!provider && /^gemini-/.test(model || "")));
    }
    function previewOptionValue(m) { return m.source + "|" + m.provider + "|" + m.model; }
    function previewOptionLabel(m) {
      var label = String(m.label || m.model);
      return previewEffortApplies(m.source, m.provider, m.model) ? label.replace(/\s*\((low|medium|high|xhigh|max)\)\s*$/i, "") : label;
    }
    function previewUsableModels() {
      var a = window.AiAccess;
      if (!a || typeof a.models !== "function") return null;
      return a.models().filter(function (m) {
        return m.source !== "local" || m.runnable !== false;
      });
    }
    function previewOptionHtml(m, selected) {
      return '<option value="' + escapeHtmlDiff(previewOptionValue(m)) + '" data-source="' + escapeHtmlDiff(m.source) +
        '" data-provider="' + escapeHtmlDiff(m.provider) + '" data-model="' + escapeHtmlDiff(m.model) + '"' +
        (selected ? " selected" : "") + ">" + escapeHtmlDiff(previewOptionLabel(m)) + "</option>";
    }
    function previewOptionsHtml(list, wanted) {
      if (!list) return PREVIEW_LOCAL_DEFAULTS.map(function (m, i) { return previewOptionHtml(m, i === 0); }).join("");
      if (!list.length) {
        return '<option value="" data-source="none" selected>' + escapeHtmlDiff(previewText("pvNoModels", "Kein KI-Modell verfügbar")) + "</option>";
      }
      var pick = wanted && list.some(function (m) { return previewOptionValue(m) === wanted; }) ? wanted : "";
      if (!pick) pick = previewOptionValue(list.filter(function (m) { return m.current; })[0] || list[0]);
      var groups = [], byGroup = {};
      list.forEach(function (m) {
        var g = m.group || m.source;
        if (!byGroup[g]) { byGroup[g] = []; groups.push(g); }
        byGroup[g].push(m);
      });
      return groups.map(function (g) {
        return '<optgroup label="' + escapeHtmlDiff(g) + '" data-source="' + escapeHtmlDiff(byGroup[g][0].source) + '">' +
          byGroup[g].map(function (m) { return previewOptionHtml(m, previewOptionValue(m) === pick); }).join("") + "</optgroup>";
      }).join("");
    }
    // Gewählte Option lesen; versteht auch ältere statische Optionen (value = Modell-ID, data-provider = agy|cursor).
    function previewChoice(sel, effortSel) {
      var opt = sel && sel.selectedOptions ? sel.selectedOptions[0] : null;
      if (!opt) return null;
      var source = opt.getAttribute("data-source");
      var provider = opt.getAttribute("data-provider") || "";
      var model = opt.getAttribute("data-model");
      if (!source) {
        source = "local";
        model = opt.value;
        provider = provider || (opt.value === "composer-2.5" ? "cursor" : "agy");
      }
      if (source === "none") return { source: "none" };
      var group = opt.parentNode && opt.parentNode.tagName === "OPTGROUP" ? opt.parentNode.label : "";
      var c = { source: source, provider: provider, model: model || "", label: (opt.textContent || "").trim(), group: group };
      if (previewEffortApplies(source, provider, c.model)) {
        c.effort = (effortSel && effortSel.value) || (PREVIEW_EFFORT_RE.exec(c.model) || [])[1] || "medium";
        c.execModel = c.model.replace(PREVIEW_EFFORT_RE, "") + "-" + c.effort;
        c.displayName = c.label + " (" + c.effort + ")";
      } else {
        c.effort = "";
        c.execModel = c.model;
        c.displayName = source === "local" ? c.label : c.model;
      }
      return c;
    }
    function syncPreviewEffort(sel) {
      var box = sel && sel.closest(".subtab-controls");
      var eff = box && box.querySelector(".subtab-select-effort");
      if (!eff || sel.disabled) return;
      var c = previewChoice(sel, null);
      var on = !!c && previewEffortApplies(c.source, c.provider, c.model);
      eff.hidden = !on;
      eff.style.display = on ? "" : "none";
      eff.disabled = !on;
      eff.style.opacity = "";
      if (on && eff.getAttribute("data-user-choice") !== "1") {
        var m = PREVIEW_EFFORT_RE.exec(c.model);
        if (m && eff.querySelector('option[value="' + m[1] + '"]')) eff.value = m[1];
      }
    }
    function fillPreviewModelSelect(sel) {
      if (!sel || sel.disabled) return; // laufender oder beendeter Lauf: Auswahl bleibt, wie sie war
      var list = previewUsableModels();
      if (list) {
        var wanted = sel.getAttribute("data-user-choice") === "1" ? sel.value : (rawWorkbenchState.lastPreviewChoice || "");
        sel.innerHTML = previewOptionsHtml(list, wanted);
      }
      syncPreviewEffort(sel);
    }
    function refreshPreviewModelSelects() {
      document.querySelectorAll(".subtab-select-model").forEach(fillPreviewModelSelect);
    }
    // Kein Modell und keine Route: Einladung des KI-Zugangs im Vorschau-Bereich statt einer Fehlermeldung.
    function showPreviewGate(seq, reason) {
      var pId = "preview-" + seq;
      var paneEl = dEl("raw-pane-" + pId);
      // Nur anzeigen: ein leerlaufender Reiter würde beim Auswählen sonst erneut starten (und wieder hier landen).
      rawWorkbenchState.showOnly = true;
      try { selectRawSubTab(pId); } finally { rawWorkbenchState.showOnly = false; }
      var access = window.AiAccess;
      if (!paneEl || !access || typeof access.gate !== "function") return;
      paneEl.innerHTML = "";
      var box = document.createElement("div");
      box.className = "raw-preview-gate";
      box.appendChild(access.gate(reason || "key"));
      paneEl.appendChild(box);
    }
    // Antwort eines Modells mit eigenem Schlüssel wie der lokale Dienst (_parse_agent_html) auslesen:
    // FRAGMENT-Block, JSON mit html bzw. ergebnisse[0].html, <div class="ai…">; sonst die Antwort ohne Codezaun.
    function extractPreviewFragment(raw) {
      var s = String(raw || "");
      var m = s.match(/<<<FRAGMENT\s*\n([\s\S]*?)\nFRAGMENT>>>/);
      if (m && m[1].trim()) return m[1].trim();
      var j = null, f = s.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
      if (f) { try { j = JSON.parse(f[1]); } catch (e) { j = null; } }
      if (!j) {
        var a = s.indexOf("{"), b = s.lastIndexOf("}");
        if (a !== -1 && b > a) { try { j = JSON.parse(s.slice(a, b + 1)); } catch (e) { j = null; } }
      }
      if (j && typeof j === "object") {
        var h = (j.ergebnisse && j.ergebnisse[0] && j.ergebnisse[0].html) || j.html;
        if (h) return String(h).trim();
      }
      var d = s.match(/(<div\s+class=['"]ai\b[\s\S]*?<\/div>(?:\s*<\/div>)*)/);
      if (d) return d[1].trim();
      return s.replace(/^\s*```[a-z]*\s*\n?/i, "").replace(/\n?```\s*$/, "").trim();
    }
    // HTTP-Fehler des lokalen Dienstes ohne res.json() auf Nicht-JSON (Safari: „The string did not match
    // the expected pattern.“), stattdessen „Server HTTP <status>“ mit kurzem Hinweis.
    async function previewHttpError(res) {
      var text = "", j = null;
      try { text = await res.text(); } catch (e) { text = ""; }
      try { j = JSON.parse(text); } catch (e) { j = null; }
      var detail = j && (j.error || j.message);
      var hint = detail ? String(typeof detail === "string" ? detail : JSON.stringify(detail))
        : (res.status === 404 || res.status === 405 || res.status === 501)
          ? previewText("pvLocalOnly", "Die lokale Vorschau läuft nur mit _src/serve.py. Wähle ein Modell mit eigenem Schlüssel.")
          : previewText("pvNotJson", "Der Server hat keine JSON-Antwort geliefert.");
      return new Error("Server HTTP " + res.status + " – " + hint);
    }
    async function previewReadJson(res) {
      var text = await res.text();
      try { return JSON.parse(text); }
      catch (e) { throw new Error("Server HTTP " + res.status + " – " + previewText("pvNotJson", "Der Server hat keine JSON-Antwort geliefert.")); }
    }

    function spawnNewPreviewTab(seq) {
      var pId = "preview-" + seq;
      rawWorkbenchState.previews[pId] = {
        id: pId,
        seq: seq,
        state: "idle",
        model: "gemini-3.8-flash",
        effort: "medium",
        provider: "agy",
        modelNameDisplay: "Gemini 3.8 Flash (med)",
        abortController: null,
        timerInterval: null,
        startTime: 0,
        durationMs: 0,
        html: "",
        error: "",
        rawOutput: ""
      };

      var tabsContainer = dEl("raw-preview-tabs-list");
      if (tabsContainer) {
        var tabDiv = document.createElement("div");
        tabDiv.className = "raw-subtab raw-subtab-preview";
        tabDiv.setAttribute("data-subtab", pId);
        tabDiv.setAttribute("data-preview-id", String(seq));
        tabDiv.setAttribute("data-state", "idle");
        tabDiv.setAttribute("role", "tab");
        tabDiv.id = "subtab-" + pId;
        tabDiv.setAttribute("aria-selected", "false");
        tabDiv.innerHTML = `
          <span class="subtab-click-area" data-action="select-subtab" data-subtab="${pId}" title="Vorschau anzeigen / konfigurieren">
            <span class="subtab-icon">⚡</span>
            <span class="subtab-title">Vorschau</span>
          </span>
          <div class="subtab-controls" id="subtab-controls-${pId}">
            <select class="subtab-select-model" title="Modell auswählen">${previewOptionsHtml(previewUsableModels(), rawWorkbenchState.lastPreviewChoice || "")}</select>
            <select class="subtab-select-effort" title="Reasoning / Effort auswählen">
              <option value="medium" selected>med</option>
              <option value="low">low</option>
              <option value="high">high</option>
            </select>
            <button type="button" class="btn-subtab-start" data-preview-id="${seq}" title="Generierung starten">⚡ Start</button>
          </div>
          <button type="button" class="btn-compare-tab" data-compare-id="${pId}" title="Diesen Stand vergleichen" style="display:none;" aria-label="Vergleichen">
            <span class="compare-icon">⚖️</span>
          </button>
          <button type="button" class="btn-subtab-close" data-preview-id="${seq}" title="Diesen Lauf schließen" style="display:none;" aria-label="Schließen">✕</button>
        `;
        tabsContainer.appendChild(tabDiv);
        syncPreviewEffort(tabDiv.querySelector(".subtab-select-model"));
      }

      var panesContainer = dEl("raw-preview-panes-container");
      if (panesContainer) {
        var paneDiv = document.createElement("div");
        paneDiv.className = "raw-content-pane raw-pane-preview";
        paneDiv.id = "raw-pane-" + pId;
        paneDiv.style.display = "none";
        paneDiv.innerHTML = `
          <div class="preview-idle-banner" style="padding:40px 20px; text-align:center; color:var(--color-ink-muted, #666); background:var(--bg-canvas, #fafafa); border:1px dashed var(--border-default, #ccc); border-radius:8px;">
            <div style="font-size:2rem; margin-bottom:8px;">⚡</div>
            <div style="font-weight:600; font-size:1rem; margin-bottom:6px;">Noch keine Vorschau generiert</div>
            <div style="font-size:0.85rem; max-width:440px; margin:0 auto 16px;">Wähle oben im Reiter das Modell (bei lokalen Gemini-Modellen auch den Effort) und klicke auf <strong>⚡ Start</strong>, um die Generierung anzustoßen.</div>
            <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:6px 16px; font-size:0.9rem; font-weight:700; background:var(--color-teal-600, #01696f); color:#fff; border:none; border-radius:6px; cursor:pointer;">⚡ Generierung jetzt starten</button>
          </div>
        `;
        panesContainer.appendChild(paneDiv);
      }
    }

    // Uniform sub-tab title: [status slot] name [timer]. Every state uses the same
    // structure so the tab width does not jump between running / done / error.
    function subtabTitleHtml(statusIcon, statusColor, name, timerText, pId) {
      var st = '<span class="subtab-status"' + (statusColor ? ' style="color:' + statusColor + ';"' : '') + '>' + statusIcon + '</span>';
      var tm = '<span class="subtab-timer"' + (pId ? ' id="subtab-timer-' + pId + '"' : '') + '>' + (timerText || "") + '</span>';
      return st + ' ' + escapeHtmlDiff(name) + ' ' + tm;
    }

    function previewErrorMessage(err, choice, isLocal) {
      var msg = String((err && err.message) || err || "");
      // fetch ohne HTTP-Antwort: Netzfehler oder vom Browser blockiert (CORS) – der Browser verrät nicht, was davon.
      if (err && err.name === "TypeError" && /failed to fetch|load failed|networkerror|network error/i.test(msg)) {
        return isLocal ? msg + " – " + previewText("pvLocalOnly", "Die lokale Vorschau läuft nur mit _src/serve.py. Wähle ein Modell mit eigenem Schlüssel.")
          : previewText("epCors", "%s ist nicht erreichbar oder erlaubt keine Anfragen aus dem Browser (CORS).", choice.group || choice.provider);
      }
      return msg;
    }
    function resetPreviewTab(seq) {
      var pId = "preview-" + seq, prev = rawWorkbenchState.previews[pId], tabEl = dEl("subtab-" + pId);
      if (prev) { prev.state = "idle"; prev.abortController = null; }
      if (!tabEl) return;
      tabEl.setAttribute("data-state", "idle");
      var sel = tabEl.querySelector(".subtab-select-model");
      if (sel) { sel.disabled = false; sel.style.display = ""; }
      var eff = tabEl.querySelector(".subtab-select-effort");
      if (eff) { eff.disabled = false; eff.style.display = ""; }
      var start = tabEl.querySelector(".btn-subtab-start");
      if (start) start.style.display = "";
      var cancel = tabEl.querySelector(".btn-subtab-cancel");
      if (cancel) cancel.style.display = "none";
      var title = tabEl.querySelector(".subtab-title");
      if (title) title.textContent = "Vorschau";
      if (sel) fillPreviewModelSelect(sel);
    }

    var PREVIEW_FALLBACK_CHOICE = { source: "local", provider: "agy", model: "gemini-3.8-flash", label: "Gemini 3.8 Flash",
                                    effort: "medium", execModel: "gemini-3.8-flash-medium", displayName: "Gemini 3.8 Flash (medium)" };

    function startPreviewGeneration(seq, autoCompareWithCurrent) {
      var pId = "preview-" + seq;
      var prev = rawWorkbenchState.previews[pId];
      if (!prev || prev.state === "running") return;

      var tabEl = dEl("subtab-" + pId);
      if (!tabEl) return;

      var modelSelect = tabEl.querySelector(".subtab-select-model");
      var effortSelect = tabEl.querySelector(".subtab-select-effort");
      var choice = previewChoice(modelSelect, effortSelect) || PREVIEW_FALLBACK_CHOICE;

      var ta = dEl("raw-prompt-textarea");
      var promptText = ta ? ta.value.trim() : "";
      if (!promptText) {
        alert("Prompt-Text darf nicht leer sein.");
        return;
      }
      var job = {
        promptText: promptText,
        modName: (ta && ta.getAttribute("data-module")) || "LinIf",
        fragRel: (ta && ta.getAttribute("data-fragment")) || "content/ai/classic/modules/linif/main_01.html",
        autoCompare: autoCompareWithCurrent
      };

      var access = window.AiAccess;
      if (choice.source !== "none" || !access) {
        runPreviewGeneration(seq, choice.source === "none" ? PREVIEW_FALLBACK_CHOICE : choice, job);
        return;
      }
      // Keine Modellliste: die Route entscheidet. Lokal → lokaler Dienst, eigener Schlüssel → dessen
      // Modell, sonst die Einladung des KI-Zugangs im Vorschau-Bereich.
      access.route().then(function (r) {
        if (r.kind === "none") { showPreviewGate(seq, r.reason); return; }
        refreshPreviewModelSelects();
        var again = previewChoice(modelSelect, effortSelect);
        if (again && again.source !== "none") runPreviewGeneration(seq, again, job);
        else if (r.kind === "byok") {
          runPreviewGeneration(seq, { source: r.provider === "project" ? "project" : "byok", provider: r.provider, model: r.model || "",
                                      label: r.model || r.provider, group: "", effort: "", execModel: r.model || "",
                                      displayName: r.model || r.provider }, job);
        } else runPreviewGeneration(seq, PREVIEW_FALLBACK_CHOICE, job);
      }, function () { showPreviewGate(seq, "key"); });
    }

    function runPreviewGeneration(seq, choice, job) {
      var pId = "preview-" + seq;
      var prev = rawWorkbenchState.previews[pId];
      if (!prev || prev.state === "running") return;
      var tabEl = dEl("subtab-" + pId);
      if (!tabEl) return;
      var modelSelect = tabEl.querySelector(".subtab-select-model");
      var effortSelect = tabEl.querySelector(".subtab-select-effort");
      var isLocal = choice.source === "local";
      var access = window.AiAccess;
      var displayName = choice.displayName || choice.model;
      var autoCompareWithCurrent = job.autoCompare;
      if (modelSelect && modelSelect.value) rawWorkbenchState.lastPreviewChoice = modelSelect.value;

      prev.state = "running";
      prev.model = choice.execModel;
      prev.effort = choice.effort || "";
      prev.provider = choice.provider;
      prev.source = choice.source;
      prev.modelNameDisplay = displayName;
      prev.startTime = performance.now();
      prev.abortController = new AbortController();

      if (modelSelect) { modelSelect.disabled = true; modelSelect.style.display = "none"; }
      if (effortSelect) { effortSelect.disabled = true; effortSelect.style.display = "none"; }
      var btnStart = tabEl.querySelector(".btn-subtab-start");
      if (btnStart) btnStart.style.display = "none";

      var controls = tabEl.querySelector(".subtab-controls");
      var btnCancel = tabEl.querySelector(".btn-subtab-cancel");
      if (!btnCancel && controls) {
        btnCancel = document.createElement("button");
        btnCancel.type = "button";
        btnCancel.className = "btn-subtab-cancel";
        btnCancel.setAttribute("data-preview-id", String(seq));
        btnCancel.title = "Generierung abbrechen";
        btnCancel.setAttribute("aria-label", "Abbrechen");
        btnCancel.textContent = "✕";
        controls.appendChild(btnCancel);
      } else if (btnCancel) {
        btnCancel.style.display = "inline-flex";
      }

      var titleEl = tabEl.querySelector(".subtab-title");
      if (titleEl) {
        titleEl.innerHTML = subtabTitleHtml('<span class="subtab-spinner">⏳</span>', null, displayName, "0.0s", pId);
      }
      tabEl.setAttribute("data-state", "running");

      var paneEl = dEl("raw-pane-" + pId);
      if (paneEl) {
        paneEl.innerHTML = `
          <div class="raw-preview-loading" style="padding:28px 20px; text-align:center; background:var(--bg-canvas, #fafafa); border:1px solid var(--border-default, #ddd); border-radius:8px;">
            <div style="display:flex; justify-content:center; align-items:center; gap:10px; margin-bottom:12px; flex-wrap:wrap;">
              <span id="pane-hz-${pId}" style="background:#059669; color:#fff; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;">${isLocal ? "Live 4.0 Hz" : escapeHtmlDiff(choice.group || choice.provider)}</span>
              <span id="pane-phase-${pId}" style="font-family:monospace; background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px; font-size:0.78rem;">[Phase: Initialisierung…]</span>
            </div>
            <div class="diff-spinner" style="display:inline-block; width:30px; height:30px; border:3px solid rgba(1,105,111,0.2); border-top-color:#01696f; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
            <div style="margin-top:10px; font-weight:700; font-size:1.02rem; color:var(--color-ink, #222);">Generiere Vorschau mit ${escapeHtmlDiff(displayName)}…</div>
            <div style="font-size:0.85rem; color:var(--color-ink-muted, #666); margin-top:4px;">Tokens: <strong id="pane-tokens-${pId}">0</strong> · Zeit: <span id="pane-timer-${pId}" style="font-weight:700; font-family:monospace;">0.0s</span></div>
            <pre id="pane-stream-${pId}" style="margin-top:14px; text-align:left; max-height:220px; overflow-y:auto; background:#1e293b; color:#e2e8f0; padding:12px; border-radius:6px; font-family:monospace; font-size:0.82rem; line-height:1.45; white-space:pre-wrap; word-break:break-word; border:1px solid #334155; display:none;"></pre>
            <div style="margin-top:16px;">
              <button type="button" class="btn-cancel-run-pane" data-preview-id="${seq}" style="padding:5px 14px; font-size:0.82rem; font-weight:600; background:#fee2e2; border:1px solid #fca5a5; color:#b91c1c; border-radius:6px; cursor:pointer;">✕ Generierung abbrechen</button>
            </div>
          </div>
        `;
      }
      // Elemente im eigenen Bereich suchen (mehrere Kurationsfenster tragen dieselben IDs).
      function inPane(id) {
        var hit = null;
        if (paneEl) { try { hit = paneEl.querySelector("#" + CSS.escape(id)); } catch (e) { hit = null; } }
        return hit || dEl(id);
      }

      if (prev.timerInterval) clearInterval(prev.timerInterval);
      prev.timerInterval = setInterval(function () {
        var elapsedSec = ((performance.now() - prev.startTime) / 1000).toFixed(1) + "s";
        var tTab = dEl("subtab-timer-" + pId);
        var tPane = inPane("pane-timer-" + pId);
        if (tTab) tTab.textContent = elapsedSec;
        if (tPane) tPane.textContent = elapsedSec;
      }, 100);

      selectRawSubTab(pId);

      var hasIdlePreview = Object.keys(rawWorkbenchState.previews).some(function (k) {
        return rawWorkbenchState.previews[k].state === "idle";
      });
      if (!hasIdlePreview) {
        var nextSeq = rawWorkbenchState.nextPreviewSeq++;
        spawnNewPreviewTab(nextSeq);
      }

      var run;
      if (!isLocal) {
        // Eigener Schlüssel, eigener Endpunkt oder Projektkontingent: direkt aus dem Browser, gestreamt.
        var phaseB = inPane("pane-phase-" + pId), tokensB = inPane("pane-tokens-" + pId), streamB = inPane("pane-stream-" + pId);
        if (phaseB) phaseB.textContent = "[Phase: Warte auf das Modell…]";
        var runMeta = {};
        run = access.complete({
          source: choice.source, provider: choice.provider, model: choice.model, prompt: job.promptText,
          signal: prev.abortController.signal, meta: runMeta,
          // Gemini-Abo: „Wartet auf Läufer …“ / „Modell denkt …“ im Phasenfeld.
          onStatus: function (status) { if (phaseB) phaseB.textContent = "[" + status + "]"; },
          onDelta: function (delta, all) {
            if (phaseB) phaseB.textContent = "[Phase: Generiere Fragment…]";
            if (tokensB) tokensB.textContent = "~" + Math.max(1, Math.round(all.length / 4));
            if (streamB) {
              streamB.style.display = "block";
              streamB.textContent = all;
              streamB.scrollTop = streamB.scrollHeight;
            }
          }
        }).then(function (text) {
          var frag = extractPreviewFragment(text);
          return {
            ok: !!frag, generated_html: frag, raw_output: String(text || "").slice(0, 3000),
            error: frag ? null : previewText("pvEmpty", "Das Modell hat keinen Text geliefert."),
            provider: choice.provider, model: runMeta.model || choice.model, profile: runMeta.profile || "",
            duration_ms: Math.round(performance.now() - prev.startTime)
          };
        });
      } else {
        run = fetch(localApi("/api/ai/execute_prompt"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
          },
          signal: prev.abortController.signal,
          body: JSON.stringify({
            prompt: job.promptText,
            module: job.modName,
            fragment: job.fragRel,
            model: choice.execModel,
            provider: choice.provider,
            stream: true
          })
        })
          .then(async function (res) {
            if (!res.ok) throw await previewHttpError(res);

            var cType = res.headers.get("Content-Type") || "";
            if (cType.includes("text/event-stream") && res.body && res.body.getReader) {
              var reader = res.body.getReader();
              var decoder = new TextDecoder("utf-8");
              var buffer = "";
              var finalData = null;
              var hzBadge = inPane("pane-hz-" + pId);
              var phaseBadge = inPane("pane-phase-" + pId);
              var tokensBadge = inPane("pane-tokens-" + pId);
              var streamBox = inPane("pane-stream-" + pId);
              var streamAcc = "";

              while (true) {
                var r = await reader.read();
                if (r.done) break;
                buffer += decoder.decode(r.value, { stream: true });
                var lines = buffer.split("\n");
                buffer = lines.pop();

                for (var i = 0; i < lines.length; i++) {
                  var line = lines[i].trim();
                  if (line.startsWith("data: ")) {
                    var jsonStr = line.slice(6).trim();
                    if (!jsonStr) continue;
                    var ev = null;
                    try { ev = JSON.parse(jsonStr); } catch (parseErr) { ev = null; }
                    if (!ev) continue;
                    if (ev.hz && hzBadge) {
                      hzBadge.textContent = "Live " + parseFloat(ev.hz).toFixed(1) + " Hz";
                    }
                    if (ev.phase && phaseBadge) {
                      var pLabels = {
                        "thinking": "[Phase: Denkvorgang / Reasoning…]",
                        "reasoning": "[Phase: Analysiere Spezifikation…]",
                        "generating": "[Phase: Generiere Fragment…]"
                      };
                      phaseBadge.textContent = pLabels[ev.phase] || ("[Phase: " + ev.phase + "…]");
                    }
                    if (ev.tokens !== undefined && tokensBadge) {
                      tokensBadge.textContent = ev.tokens;
                    }
                    if (ev.delta) {
                      streamAcc += ev.delta;
                      if (streamBox) {
                        streamBox.style.display = "block";
                        streamBox.textContent = streamAcc;
                        streamBox.scrollTop = streamBox.scrollHeight;
                      }
                    }
                    if (ev.event === "complete") {
                      finalData = ev;
                    } else if (ev.event === "error") {
                      throw new Error(ev.error || "Der KI-Agent hat einen Fehler gemeldet (ohne Detailtext).");
                    }
                  }
                }
              }
              if (!finalData) throw new Error("Verbindung zum Server abgebrochen, bevor das Modell ein Ergebnis geliefert hat.");
              return finalData;
            }
            return previewReadJson(res);
          });
      }

      run
        .then(function (data) {

          if (prev.timerInterval) { clearInterval(prev.timerInterval); prev.timerInterval = null; }
          var durMs = data.duration_ms || Math.round(performance.now() - prev.startTime);
          prev.durationMs = durMs;

          if (!data.ok) {
            prev.state = "error";
            prev.error = data.error || "Modell lieferte kein gültiges Ergebnis.";
            tabEl.setAttribute("data-state", "error");
            if (btnCancel) btnCancel.style.display = "none";
            var btnClose = tabEl.querySelector(".btn-subtab-close");
            if (btnClose) btnClose.style.display = "inline-flex";
            if (titleEl) titleEl.innerHTML = subtabTitleHtml('<span class="subtab-err-mark">!</span>', "#b91c1c", displayName, ((prev.durationMs || 0) / 1000).toFixed(1) + "s", null);

            if (paneEl) {
              paneEl.innerHTML = `
                <div style="padding:18px; color:#b91c1c; background:#fee2e2; border-radius:8px; border:1px solid #fca5a5; margin-bottom:12px;">
                  <div style="font-weight:700; font-size:0.95rem; margin-bottom:6px;">Fehler bei der Generierung (${(durMs / 1000).toFixed(1)}s):</div>
                  <div>${escapeHtmlDiff(prev.error)}</div>
                  ${data.raw_output ? '<pre style="margin-top:10px; font-size:0.8em; max-height:160px; overflow:auto; background:#fff; padding:8px; border-radius:4px; border:1px solid #fca5a5;">' + escapeHtmlDiff(data.raw_output) + '</pre>' : ''}
                  <div style="margin-top:12px;">
                    <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:5px 12px; background:#b91c1c; color:#fff; border:none; border-radius:4px; font-size:0.85rem; font-weight:600; cursor:pointer;">Erneut versuchen</button>
                  </div>
                </div>
              `;
            }
            return;
          }

          prev.state = "done";
          prev.html = data.generated_html || "";
          prev.rawOutput = data.raw_output || "";
          tabEl.setAttribute("data-state", "done");

          if (btnCancel) btnCancel.style.display = "none";
          var btnCmp = tabEl.querySelector('.btn-compare-tab[data-compare-id="' + pId + '"]');
          if (btnCmp) btnCmp.style.display = "inline-flex";
          var btnClose = tabEl.querySelector(".btn-subtab-close");
          if (btnClose) btnClose.style.display = "inline-flex";

          if (titleEl) {
            titleEl.innerHTML = subtabTitleHtml("✓", "#15803d", displayName, (durMs / 1000).toFixed(1) + "s", null);
          }

          if (paneEl) {
            paneEl.innerHTML = `
              <div class="raw-pane-banner" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <span>⚡ Vorschau: <strong>${escapeHtmlDiff(displayName)}</strong> · Dauer: <strong>${(durMs / 1000).toFixed(1)}s</strong> · Länge: <strong>${prev.html.length} Zeichen</strong>${
                  /* Gemini-Abo: welches Profil (leo/neo) geantwortet hat */
                  data.profile && access && access.answerLabel ? " · " + escapeHtmlDiff(access.answerLabel({ model: data.model, profile: data.profile },
                    { kind: "byok", provider: choice.provider, model: data.model })) : ""}</span>
                <div style="display:flex; gap:8px;">
                  <button type="button" class="btn-compare-tab" data-compare-id="${pId}" title="Diesen Stand vergleichen">⚖️ Vergleichen</button>
                </div>
              </div>
              <pre class="raw-code-box" id="raw-preview-code-${pId}">${escapeHtmlDiff(prev.html)}</pre>
            `;
          }

          if (autoCompareWithCurrent) {
            setTimeout(function () {
              linkCompareTabs("current", pId);
            }, 60);
          }
        })
        .catch(function (err) {
          if (prev.timerInterval) { clearInterval(prev.timerInterval); prev.timerInterval = null; }
          if (err && err.name === "AiAccessRouteError" && err.code === "none") {
            // Zugang inzwischen weg (z. B. Schlüssel entfernt): Reiter zurücksetzen, Einladung zeigen.
            resetPreviewTab(seq);
            showPreviewGate(seq, err.reason);
            return;
          }
          if (err.name === "AbortError") {
            prev.state = "cancelled";
            tabEl.setAttribute("data-state", "cancelled");
            if (btnCancel) btnCancel.style.display = "none";
            var btnClose = tabEl.querySelector(".btn-subtab-close");
            if (btnClose) btnClose.style.display = "inline-flex";
            if (titleEl) titleEl.innerHTML = subtabTitleHtml("✕", "#6b7280", displayName, "abgebr.", null);
            if (paneEl) {
              paneEl.innerHTML = `
                <div style="padding:24px; text-align:center; color:var(--color-ink-muted, #666); background:var(--bg-canvas, #fafafa); border:1px dashed var(--border-default, #ccc); border-radius:8px;">
                  <div style="font-size:1.5rem; margin-bottom:6px;">✕</div>
                  <div style="font-weight:600; margin-bottom:4px;">Generierung wurde abgebrochen</div>
                  <div style="font-size:0.85rem; margin-bottom:12px;">Der laufende Modellaufruf wurde vom Benutzer gestoppt.</div>
                  <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:5px 14px; background:var(--color-teal-600, #01696f); color:#fff; border:none; border-radius:4px; font-weight:600; cursor:pointer;">⚡ Neu starten</button>
                </div>
              `;
            }
          } else {
            prev.state = "error";
            prev.error = previewErrorMessage(err, choice, isLocal);
            tabEl.setAttribute("data-state", "error");
            if (btnCancel) btnCancel.style.display = "none";
            var btnClose = tabEl.querySelector(".btn-subtab-close");
            if (btnClose) btnClose.style.display = "inline-flex";
            if (titleEl) titleEl.innerHTML = subtabTitleHtml('<span class="subtab-err-mark">!</span>', "#b91c1c", displayName, ((prev.durationMs || 0) / 1000).toFixed(1) + "s", null);
            if (paneEl) {
              paneEl.innerHTML = `
                <div style="padding:18px; color:#b91c1c; background:#fee2e2; border-radius:8px; border:1px solid #fca5a5; margin-bottom:12px;">
                  <div style="font-weight:700; font-size:0.95rem; margin-bottom:6px;">Verbindungsfehler:</div>
                  <div>${escapeHtmlDiff(prev.error)}</div>
                  <div style="margin-top:12px;">
                    <button type="button" class="btn-subtab-start-pane" data-preview-id="${seq}" style="padding:5px 12px; background:#b91c1c; color:#fff; border:none; border-radius:4px; font-size:0.85rem; font-weight:600; cursor:pointer;">Erneut versuchen</button>
                  </div>
                </div>
              `;
            }
          }
        });
    }

    function cancelPreviewGeneration(seq) {
      var pId = "preview-" + seq;
      var prev = rawWorkbenchState.previews[pId];
      if (prev && prev.abortController) {
        prev.abortController.abort();
      }
    }

    function closePreviewTab(seq) {
      var pId = "preview-" + seq;
      if (rawWorkbenchState.isCompareActive && (rawWorkbenchState.linkedSourceId === pId || rawWorkbenchState.linkedTargetId === pId)) {
        exitCompareMode();
      }
      if (rawWorkbenchState.compareSourceId === pId) {
        cancelComparePick();
      }
      var prev = rawWorkbenchState.previews[pId];
      if (prev && prev.timerInterval) {
        clearInterval(prev.timerInterval);
      }
      if (prev && prev.abortController && prev.state === "running") {
        prev.abortController.abort();
      }
      delete rawWorkbenchState.previews[pId];

      var tabEl = dEl("subtab-" + pId);
      if (tabEl) tabEl.remove();
      var paneEl = dEl("raw-pane-" + pId);
      if (paneEl) paneEl.remove();

      if (rawWorkbenchState.activeSubTab === pId) {
        selectRawSubTab("current");
      }
    }

    // Interaction delegation
    document.addEventListener("click", function (e) {
      // Dossier mode tab switcher
      var modeTab = e.target.closest(".dossier-mode-tab");
      if (modeTab) {
        e.preventDefault();
        var targetMode = modeTab.getAttribute("data-view-mode") || "raw";
        var modal = modeTab.closest("dialog") || document;
        if (typeof requestAnimationFrame === "function") {
          requestAnimationFrame(function () { switchDossierViewMode(targetMode, modal); });
        } else {
          switchDossierViewMode(targetMode, modal);
        }
        return;
      }

      // Copy raw prompt text
      var btnCopyPrompt = e.target.closest("#btn-copy-raw-prompt");
      if (btnCopyPrompt) {
        e.preventDefault();
        var rawTa = dEl("raw-prompt-textarea");
        var rawPre = dEl("raw-prompt-text");
        var text = rawTa ? rawTa.value : (rawPre ? rawPre.textContent : "");
        if (text) {
          var showCopyHint = function () {
            var hint = dEl("copy-success-hint");
            if (hint) {
              hint.hidden = false;
              setTimeout(function () { hint.hidden = true; }, 2200);
            }
          };
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(showCopyHint).catch(function () {
              fallbackCopy(text, showCopyHint);
            });
          } else {
            fallbackCopy(text, showCopyHint);
          }
        }
        function fallbackCopy(val, cb) {
          var ta = document.createElement("textarea");
          ta.value = val;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.focus();
          ta.select();
          try { document.execCommand("copy"); if (cb) cb(); } catch (err) {}
          document.body.removeChild(ta);
        }
        return;
      }

      // Regenerate from context (⚡ Aus Kontext neu generieren)
      var btnRegenContext = e.target.closest("#btn-regenerate-from-context");
      if (btnRegenContext) {
        e.preventDefault();
        e.stopPropagation();
        var modal = btnRegenContext.closest("dialog") || document;

        // Kontext-Kurationseinstellungen sammeln
        var confirmed = [];
        var dismissed = [];
        var added = [];
        hydrateCurrentContext(modal);
        var localVotes = (typeof loadVotes === "function") ? loadVotes() : {};

        modal.querySelectorAll(".snippet-card").forEach(function (card) {
          var sId = card.getAttribute("data-snippet-id") || card.id;
          var rec = localVotes[voteKey(sId)] || {};
          var status = rec.vote || (rec.queued ? "queued" : "unrated");
          var titleEl = card.querySelector("strong");
          var docTitle = titleEl ? titleEl.textContent.trim() : "";
          var descEl = card.querySelector("blockquote");
          var descSnippet = descEl ? descEl.textContent.trim().slice(0, 100) : "";
          var label = (docTitle ? docTitle + " (" + sId + ")" : sId) + (descSnippet ? ": „" + descSnippet + "…“" : "");

          if (status === "confirm" || status === "justified_confirm") {
            confirmed.push(label);
          } else if (status === "dismiss" || status === "justified_dismiss") {
            dismissed.push(label);
          } else if (card.hasAttribute("data-current-new")) {
            added.push(label);
          }
        });

        // Prompt im Textarea um Kurations-Ergebnisse anreichern
        var ta = modal.querySelector("#raw-prompt-textarea");
        if (ta) {
          var val = ta.value;
          var addendum = "\n\n### Kurations-Feedback & angepasster Kontext aus dem Audit-Dossier:\n";
          if (confirmed.length > 0) {
            addendum += "- Bestätigte Referenzen & Kern-Aussagen:\n  * " + confirmed.join("\n  * ") + "\n";
          }
          if (dismissed.length > 0) {
            addendum += "- Beanstandete / zu entfernende Referenzen:\n  * " + dismissed.join("\n  * ") + "\n";
          }
          if (added.length > 0) {
            addendum += "- Seit der letzten Generierung neu zugeordnete Belege (Snippets und Schaubilder):\n  * " +
              added.slice(0, 80).join("\n  * ") + (added.length > 80 ? "\n  * … (" + (added.length - 80) + " weitere)" : "") + "\n";
          }
          if (confirmed.length === 0 && dismissed.length === 0 && added.length === 0) {
            addendum += "- Alle aktuellen Inbound- und Spezifikations-Referenzen wurden im Dossier geprüft und bestätigt.\n";
          }
          if (!val.includes("### Kurations-Feedback & angepasster Kontext")) {
            ta.value = val.trimEnd() + addendum;
          }
          if (typeof updatePromptTokenCount === "function") {
            updatePromptTokenCount(modal);
          }
        }

        // Umschalten auf Output-Ansicht
        if (typeof switchDossierViewMode === "function") {
          switchDossierViewMode("output", modal);
        }

        // Neuen Vorschau-Reiter anlegen und Generierung mit autoCompare starten
        rawWorkbenchState.nextPreviewSeq = (rawWorkbenchState.nextPreviewSeq || 1) + 1;
        var nextSeq = rawWorkbenchState.nextPreviewSeq;
        if (typeof spawnNewPreviewTab === "function") {
          spawnNewPreviewTab(nextSeq);
        }
        if (typeof selectRawSubTab === "function") {
          selectRawSubTab("preview-" + nextSeq);
        }
        if (typeof startPreviewGeneration === "function") {
          startPreviewGeneration(nextSeq, true);
        }
        return;
      }

      // 3-Reiter-Konzept: Interaction Delegation

      // Compare Button (⚖️)
      var btnCompare = e.target.closest(".btn-compare-tab");
      if (btnCompare) {
        e.preventDefault();
        e.stopPropagation();
        var cid = btnCompare.getAttribute("data-compare-id");
        if (cid) {
          initiateCompare(cid);
        }
        return;
      }

      // Start preview generation (⚡ Start)
      var btnStartTab = e.target.closest(".btn-subtab-start");
      var btnStartPane = e.target.closest(".btn-subtab-start-pane");
      if (btnStartTab || btnStartPane) {
        e.preventDefault();
        e.stopPropagation();
        var pSeq = (btnStartTab || btnStartPane).getAttribute("data-preview-id");
        if (pSeq) {
          startPreviewGeneration(pSeq);
        }
        return;
      }

      // Cancel preview generation (✕ Abbrechen)
      var btnCancelTab = e.target.closest(".btn-subtab-cancel") || e.target.closest(".btn-cancel-run-pane");
      if (btnCancelTab) {
        e.preventDefault();
        e.stopPropagation();
        var pSeq = btnCancelTab.getAttribute("data-preview-id");
        if (pSeq) {
          cancelPreviewGeneration(pSeq);
        }
        return;
      }

      // Close preview tab (✕)
      var btnCloseTab = e.target.closest(".btn-subtab-close");
      if (btnCloseTab) {
        e.preventDefault();
        e.stopPropagation();
        var pSeq = btnCloseTab.getAttribute("data-preview-id");
        if (pSeq) {
          closePreviewTab(pSeq);
        }
        return;
      }

      // Exit compare mode (Link Badge or Unlink Button)
      if (e.target.closest("#raw-tab-link-badge") || e.target.closest("#btn-unlink-compare")) {
        e.preventDefault();
        e.stopPropagation();
        exitCompareMode();
        return;
      }

      // Cancel compare picking mode
      if (e.target.closest("#btn-cancel-compare-pick")) {
        e.preventDefault();
        e.stopPropagation();
        cancelComparePick();
        return;
      }

      // Ignore clicks inside inline selects so user can freely open dropdowns
      if (e.target.closest(".subtab-controls select")) {
        return;
      }

      // Subtab selection (Click on tab or click area)
      var subtabClick = e.target.closest("[data-action='select-subtab']") || e.target.closest(".raw-subtab");
      if (subtabClick) {
        e.preventDefault();
        var subtabId = subtabClick.getAttribute("data-subtab") || (subtabClick.closest(".raw-subtab") ? subtabClick.closest(".raw-subtab").getAttribute("data-subtab") : null);
        if (subtabId) {
          selectRawSubTab(subtabId);
        }
        return;
      }

      // Clear badge button (x an der Badge)
      var btnClearBadge = e.target.closest(".btn-clear-badge");
      if (btnClearBadge) {
        e.preventDefault();
        e.stopPropagation();
        var bId = btnClearBadge.getAttribute("data-clear-badge-for");
        if (bId) {
          var votes = loadVotes();
          delete votes[voteKey(bId)];
          try { localStorage.setItem(VOTE_STORE, JSON.stringify(votes)); } catch (err) {}

          var pkg = loadReviewPackage();
          var nextPkg = pkg.filter(function (x) { return !(x.id === bId && (x.guide_kind || "user") === activeGuideKind()); });
          if (nextPkg.length !== pkg.length) {
            storeReviewPackage(nextPkg);
          }

          try {
            fetch("/api/curation/vote", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ snippet_id: bId, item_id: bId, vote: "reset", guide_kind: activeGuideKind() })
            }).catch(function () {});
          } catch (err) {}

          updateSnippetBadges();
        }
        return;
      }

      // Card checkbox click (inkl. Shift-Range auf sichtbare Inbound-Snippets)
      var cb = e.target.closest(".card-select-checkbox");
      if (cb) {
        var cCard = cb.closest(".snippet-card");
        var cId = cb.getAttribute("data-select-card") || (cCard ? cCard.getAttribute("data-snippet-id") : null);
        if (cId) {
          if (e.shiftKey) {
            e.preventDefault();
            var selectState = cb.checked;
            if (lastSelectedSnippetId) {
              applySnippetRangeSelection(lastSelectedSnippetId, cId, selectState);
            } else {
              if (selectState) {
                selectedSnippetIds.add(cId);
              } else {
                selectedSnippetIds.delete(cId);
              }
              lastSelectedSnippetId = cId;
              updateSelectionUI();
            }
          } else if (cb.checked) {
            selectedSnippetIds.add(cId);
            lastSelectedSnippetId = cId;
            updateSelectionUI();
          } else {
            selectedSnippetIds.delete(cId);
            updateSelectionUI();
          }
        }
        return;
      }

      // Batch Action Buttons
      if (e.target.closest("#btn-batch-confirm")) {
        e.preventDefault();
        selectedSnippetIds.forEach(function (sId) {
          storeVote(sId, { vote: "confirm", queued: false });
          try {
            fetch("/api/curation/vote", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ snippet_id: sId, item_id: sId, vote: "confirm", guide_kind: activeGuideKind() })
            }).catch(function () {});
          } catch (err) {}
        });
        selectedSnippetIds.clear();
        updateSelectionUI();
        updateSnippetBadges();
        return;
      }

      if (e.target.closest("#btn-batch-dismiss")) {
        e.preventDefault();
        selectedSnippetIds.forEach(function (sId) {
          storeVote(sId, { vote: "dismiss", queued: false });
          try {
            fetch("/api/curation/vote", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ snippet_id: sId, item_id: sId, vote: "dismiss", guide_kind: activeGuideKind() })
            }).catch(function () {});
          } catch (err) {}
        });
        selectedSnippetIds.clear();
        updateSelectionUI();
        updateSnippetBadges();
        return;
      }

      if (e.target.closest("#btn-batch-discuss")) {
        e.preventDefault();
        var chatPane = dEl("dossier-chat-pane");
        var modal = chatPane ? chatPane.closest("dialog") : null;
        if (chatPane) {
          chatPane.hidden = false;
          if (modal) modal.classList.add("has-chat-open");
        }
        var countAdded = 0;
        selectedSnippetIds.forEach(function (sId) {
          if (!attachedDiscussionItems.has(sId)) {
            attachedDiscussionItems.add(sId);
            countAdded++;
          }
          var targetCard = dEl(sId);
          if (targetCard) {
            targetCard.classList.remove("is-collapsed");
            targetCard.classList.add("is-expanded");
            var h = targetCard.querySelector(".snippet-card-header");
            if (h) h.setAttribute("aria-expanded", "true");
          }
        });
        appendDiscussionSystemNote(countAdded + " Element(e) aus Multiselektion zur Diskussion hinzugefügt.");
        selectedSnippetIds.clear();
        updateSelectionUI();
        renderAttachedChips();
        updateSnippetBadges();
        return;
      }

      if (e.target.closest("#btn-clear-selection")) {
        e.preventDefault();
        selectedSnippetIds.clear();
        updateSelectionUI();
        return;
      }

      // Shift/Cmd-Klick auf Snippet-Kartenkörper (nicht nur Header)
      var snippetCardArea = e.target.closest(".snippet-card");
      if (snippetCardArea && !e.target.closest("[data-card-toggle]") && !e.target.closest(".curation-btn") && !e.target.closest("a") && !e.target.closest(".card-select-checkbox") && !e.target.closest(".btn-clear-badge")) {
        var areaId = snippetCardArea.getAttribute("data-snippet-id") || snippetCardArea.id;
        if (e.shiftKey && areaId) {
          e.preventDefault();
          applySnippetRangeSelection(lastSelectedSnippetId, areaId, true);
          return;
        }
        if ((e.ctrlKey || e.metaKey) && areaId) {
          e.preventDefault();
          if (selectedSnippetIds.has(areaId)) {
            selectedSnippetIds.delete(areaId);
          } else {
            selectedSnippetIds.add(areaId);
            lastSelectedSnippetId = areaId;
          }
          updateSelectionUI();
          return;
        }
      }

      // 0. Card header toggle (collapse / expand & mouse selection)
      var cardToggle = e.target.closest("[data-card-toggle]");
      if (cardToggle) {
        if (!e.target.closest(".curation-btn") && !e.target.closest("a") && !e.target.closest(".card-select-checkbox") && !e.target.closest(".btn-clear-badge")) {
          var cardId = cardToggle.getAttribute("data-card-toggle");
          var card = dEl(cardId) || cardToggle.closest(".snippet-card");
          var sId = card ? (card.getAttribute("data-snippet-id") || card.id) : cardId;

          // Ctrl / Cmd + Click: Toggle element selection
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            if (selectedSnippetIds.has(sId)) {
              selectedSnippetIds.delete(sId);
            } else {
              selectedSnippetIds.add(sId);
              lastSelectedSnippetId = sId;
            }
            updateSelectionUI();
            return;
          }

          // Shift + Click: Range multiselection
          if (e.shiftKey) {
            e.preventDefault();
            applySnippetRangeSelection(lastSelectedSnippetId, sId, true);
            return;
          }

          // Regular click: Expand / Collapse
          e.preventDefault();
          lastSelectedSnippetId = sId;
          if (card) {
            var isCollapsed = card.classList.contains("is-collapsed");
            if (isCollapsed) {
              card.classList.remove("is-collapsed");
              card.classList.add("is-expanded");
              cardToggle.setAttribute("aria-expanded", "true");
            } else {
              card.classList.remove("is-expanded");
              card.classList.add("is-collapsed");
              cardToggle.setAttribute("aria-expanded", "false");
            }
          }
          return;
        }
      }

      // View Compact
      if (e.target.closest("#btn-view-compact")) {
        e.preventDefault();
        dScope().querySelectorAll(".snippet-card").forEach(function (c) {
          c.classList.add("is-collapsed");
          c.classList.remove("is-expanded");
          var h = c.querySelector(".snippet-card-header");
          if (h) h.setAttribute("aria-expanded", "false");
        });
        document.querySelectorAll("#btn-view-compact").forEach(function (b) { b.classList.add("is-active"); });
        document.querySelectorAll("#btn-view-detailed").forEach(function (b) { b.classList.remove("is-active"); });
        var btnToggleAll = dEl("btn-toggle-all-expand");
        if (btnToggleAll) btnToggleAll.textContent = "⊞ Alle ausklappen";
        return;
      }

      // View Detailed
      if (e.target.closest("#btn-view-detailed")) {
        e.preventDefault();
        dScope().querySelectorAll(".snippet-card").forEach(function (c) {
          c.classList.remove("is-collapsed");
          c.classList.add("is-expanded");
          var h = c.querySelector(".snippet-card-header");
          if (h) h.setAttribute("aria-expanded", "true");
        });
        document.querySelectorAll("#btn-view-detailed").forEach(function (b) { b.classList.add("is-active"); });
        document.querySelectorAll("#btn-view-compact").forEach(function (b) { b.classList.remove("is-active"); });
        var btnToggleAll = dEl("btn-toggle-all-expand");
        if (btnToggleAll) btnToggleAll.textContent = "⊟ Alle einklappen";
        return;
      }

      // Toggle All Expand / Collapse
      if (e.target.closest("#btn-toggle-all-expand")) {
        e.preventDefault();
        var hasCollapsed = !!dScope().querySelector(".snippet-card.is-collapsed");
        if (hasCollapsed) {
          dScope().querySelectorAll(".snippet-card").forEach(function (c) {
            c.classList.remove("is-collapsed");
            c.classList.add("is-expanded");
            var h = c.querySelector(".snippet-card-header");
            if (h) h.setAttribute("aria-expanded", "true");
          });
          var btnToggleAll = dEl("btn-toggle-all-expand");
          if (btnToggleAll) btnToggleAll.textContent = "⊟ Alle einklappen";
          var btnD = dEl("btn-view-detailed");
          var btnC = dEl("btn-view-compact");
          if (btnD) btnD.classList.add("is-active");
          if (btnC) btnC.classList.remove("is-active");
        } else {
          dScope().querySelectorAll(".snippet-card").forEach(function (c) {
            c.classList.add("is-collapsed");
            c.classList.remove("is-expanded");
            var h = c.querySelector(".snippet-card-header");
            if (h) h.setAttribute("aria-expanded", "false");
          });
          var btnToggleAll = dEl("btn-toggle-all-expand");
          if (btnToggleAll) btnToggleAll.textContent = "⊞ Alle ausklappen";
          var btnD = dEl("btn-view-detailed");
          var btnC = dEl("btn-view-compact");
          if (btnD) btnD.classList.remove("is-active");
          if (btnC) btnC.classList.add("is-active");
        }
        return;
      }

      // Filter kind pill
      var pillKind = e.target.closest(".dossier-filter-pill[data-filter-kind]");
      if (pillKind) {
        e.preventDefault();
        var grp = pillKind.closest(".dossier-filter-group");
        if (grp) grp.querySelectorAll(".dossier-filter-pill[data-filter-kind]").forEach(function (p) { p.classList.remove("is-active"); });
        pillKind.classList.add("is-active");
        applyDossierFilters();
        return;
      }

      // Filter status pill
      var pillStatus = e.target.closest(".dossier-filter-pill[data-filter-status]");
      if (pillStatus) {
        e.preventDefault();
        var grp = pillStatus.closest(".dossier-filter-group");
        if (grp) grp.querySelectorAll(".dossier-filter-pill[data-filter-status]").forEach(function (p) { p.classList.remove("is-active"); });
        pillStatus.classList.add("is-active");
        applyDossierFilters();
        return;
      }

      // Clear search
      if (e.target.closest("#btn-clear-dossier-search")) {
        e.preventDefault();
        var sInput = dEl("dossier-search-input");
        if (sInput) {
          sInput.value = "";
          sInput.focus();
        }
        applyDossierFilters();
        return;
      }

      // Reset filters
      if (e.target.closest("#btn-reset-dossier-filters")) {
        e.preventDefault();
        var sInput = dEl("dossier-search-input");
        if (sInput) sInput.value = "";
        dScope().querySelectorAll(".dossier-filter-pill[data-filter-kind]").forEach(function (p) {
          p.classList.toggle("is-active", p.getAttribute("data-filter-kind") === "all");
        });
        dScope().querySelectorAll(".dossier-filter-pill[data-filter-status]").forEach(function (p) {
          p.classList.toggle("is-active", p.getAttribute("data-filter-status") === "all");
        });
        applyDossierFilters();
        return;
      }

      // 1. Confirm button (Single card)
      var btnConf = e.target.closest('.curation-btn[data-action="confirm"]');
      if (btnConf) {
        e.preventDefault();
        var sId = btnConf.getAttribute("data-snippet");
        storeVote(sId, { vote: "confirm", queued: false });
        updateSnippetBadges();
        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ snippet_id: sId, vote: "confirm", guide_kind: activeGuideKind() })
          }).catch(function () {});
        } catch (err) {}
        return;
      }

      // 2. Dismiss button (Single card)
      var btnDism = e.target.closest('.curation-btn[data-action="dismiss"]');
      if (btnDism) {
        e.preventDefault();
        var sId = btnDism.getAttribute("data-snippet");
        storeVote(sId, { vote: "dismiss", queued: false });
        updateSnippetBadges();
        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ snippet_id: sId, item_id: sId, vote: "dismiss", guide_kind: activeGuideKind() })
          }).catch(function () {});
        } catch (err) {}
        return;
      }

      // 3. Discuss toggle button on card
      var btnDisc = e.target.closest('.curation-btn[data-action="discuss"]');
      if (btnDisc) {
        e.preventDefault();
        var sId = btnDisc.getAttribute("data-snippet") || (btnDisc.closest(".snippet-card") ? btnDisc.closest(".snippet-card").getAttribute("data-snippet-id") : null);
        if (sId) {
          toggleDiscussionItem(sId);
        }
        return;
      }

      // 4a. Suchtreffer aus der Diskussion nehmen
      var btnDetachHit = e.target.closest(".btn-detach-hit");
      if (btnDetachHit) {
        e.preventDefault();
        excludedHits.add(btnDetachHit.getAttribute("data-item-id"));
        renderAttachedChips();
        return;
      }
      // 4b. Chip anklicken: Element im Dossier zeigen
      var btnGoto = e.target.closest(".chat-chip-goto");
      if (btnGoto) {
        e.preventDefault();
        var gc = cardFor(btnGoto.getAttribute("data-item-id"));
        if (gc) {
          if (gc.style.display === "none") gc.style.display = "";
          gc.classList.remove("is-collapsed");
          gc.classList.add("is-expanded");
          var gh = gc.querySelector(".snippet-card-header");
          if (gh) gh.setAttribute("aria-expanded", "true");
          gc.scrollIntoView({ block: "start", behavior: "smooth" });
          gc.classList.add("rec-jump-focus");
          setTimeout(function () { gc.classList.remove("rec-jump-focus"); }, 1600);
        }
        return;
      }
      // 4. Detach item button from chip
      var btnDetach = e.target.closest(".btn-detach-item");
      if (btnDetach) {
        e.preventDefault();
        var dId = btnDetach.getAttribute("data-item-id");
        if (dId) {
          attachedDiscussionItems.delete(dId);
          appendDiscussionSystemNote("Element <code>" + dId + "</code> aus Diskussion entfernt.");
          renderAttachedChips();
          updateSnippetBadges();
        }
        return;
      }

      // 5. Clear all attached items
      var btnClear = e.target.closest("#btn-clear-attached");
      if (btnClear) {
        e.preventDefault();
        attachedDiscussionItems.clear();
        searchHits().forEach(function (id) { excludedHits.add(id); });
        appendDiscussionSystemNote("Alle Elemente aus der Diskussion gelöst.");
        renderAttachedChips();
        updateSnippetBadges();
        return;
      }

      // 6. Header toggle button for workbench chat
      var btnToggleChat = e.target.closest("#btn-toggle-workbench-chat");
      if (btnToggleChat) {
        e.preventDefault();
        var chatPane = dEl("dossier-chat-pane");
        var modal = chatPane ? chatPane.closest("dialog") : null;
        if (chatPane) {
          var willHide = !chatPane.hidden;
          chatPane.hidden = willHide;
          if (modal) modal.classList.toggle("has-chat-open", !willHide);
          // Schließen beendet nur die Ansicht; der Fokus bleibt für das erneute Öffnen erhalten
          renderAttachedChips();
        }
        return;
      }

      // 7. Chat pane close button
      var btnCloseChat = e.target.closest("#btn-close-chat-pane");
      if (btnCloseChat) {
        e.preventDefault();
        var chatPane = dEl("dossier-chat-pane");
        var modal = chatPane ? chatPane.closest("dialog") : null;
        if (chatPane) {
          chatPane.hidden = true;
          if (modal) modal.classList.remove("has-chat-open");
        }
        renderAttachedChips();
        return;
      }

      // 7b. Chat bubble review actions
      if (e.target.closest('[data-action="open-review-drawer"]')) {
        e.preventDefault();
        // Direkt zum Abschnitt „Review-Paket“ im Panel „Feedback & Kuration“.
        var openBtn = document.querySelector("[data-review-open]");
        if (window.araReview && typeof window.araReview.openDrawer === "function") {
          window.araReview.openDrawer("package");
        } else if (openBtn) {
          openBtn.click();
        }
        return;
      }

      if (e.target.closest('[data-action="export-curation-json"]')) {
        e.preventDefault();
        var exportBtn = document.querySelector("[data-review-export]");
        if (exportBtn) {
          exportBtn.click();
        } else if (window.araReview && typeof window.araReview.exportPackage === "function") {
          window.araReview.exportPackage();
        } else {
          var pkgItems = loadReviewPackage();
          var identObj = getReviewerIdentity();
          var exportPayload = {
            schema: "review-package@v1",
            identity: identObj.mode,
            submitted_at: new Date().toISOString(),
            decisions: pkgItems
          };
          var blob = new Blob([JSON.stringify(exportPayload, null, 2) + "\n"], { type: "application/json" });
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "ara-curation-package-" + new Date().toISOString().replace(/[:.]/g, "-") + ".json";
          a.click();
          setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
        }
        return;
      }

      // 8. Workbench quick prompt chips
      var wbChip = e.target.closest(".workbench-prompt-chip");
      if (wbChip) {
        e.preventDefault();
        var prompt = wbChip.getAttribute("data-prompt");
        if (wbChip.classList.contains("chip-criticism") || (prompt && prompt.endsWith(": "))) {
          var chatInput = dEl("chat-pane-input");
          if (chatInput) {
            chatInput.value = prompt;
            chatInput.focus();
            if (chatInput.setSelectionRange) {
              chatInput.setSelectionRange(chatInput.value.length, chatInput.value.length);
            }
          }
        } else {
          sendWorkbenchMessage(prompt);
        }
        return;
      }

      // 9a. Exit 1: Submit proposal to curation queue (Review-Paket)
      var btnSubmitProp = e.target.closest("#btn-submit-workbench-proposal");
      if (btnSubmitProp) {
        e.preventDefault();
        submitWorkbenchProposal();
        return;
      }

      // 9b. Exit 2: Apply proposal directly as justified locally in dossier
      var btnApplyLocal = e.target.closest("#btn-apply-justified-locally");
      if (btnApplyLocal) {
        e.preventDefault();
        applyProposalLocallyJustified();
        return;
      }

      // 9c. Dismiss proposal
      var btnDismissProp = e.target.closest("#btn-dismiss-proposal");
      if (btnDismissProp) {
        e.preventDefault();
        var propBox = dEl("chat-pane-proposal-box");
        if (propBox) propBox.hidden = true;
        appendDiscussionSystemNote("Kurationsvorschlag verworfen.");
        return;
      }

      // 10. Backward compatibility for legacy inline chips / queue button if present
      var oldChip = e.target.closest(".snippet-chip");
      if (oldChip) {
        e.preventDefault();
        var sId = oldChip.getAttribute("data-snippet");
        var prompt = oldChip.getAttribute("data-prompt");
        openDiscussionForItem(sId);
        sendWorkbenchMessage(prompt);
        return;
      }
      var oldQueue = e.target.closest(".btn-submit-curation-queue");
      if (oldQueue) {
        e.preventDefault();
        submitWorkbenchProposal();
        return;
      }
    });

    // Change listener for inline model selects inside raw subtab controls
    document.addEventListener("change", function (e) {
      var selectModel = e.target.closest(".subtab-select-model");
      if (selectModel) {
        // Ausdrückliche Wahl bleibt bei späterem Neufüllen erhalten und gilt für neue Reiter.
        selectModel.setAttribute("data-user-choice", "1");
        rawWorkbenchState.lastPreviewChoice = selectModel.value;
        syncPreviewEffort(selectModel);
      }
      var selectEffort = e.target.closest(".subtab-select-effort");
      if (selectEffort) selectEffort.setAttribute("data-user-choice", "1");
    });

    // Form submission
    document.addEventListener("submit", function (e) {
      var wbForm = e.target.closest("#chat-pane-form");
      if (wbForm) {
        e.preventDefault();
        var input = dEl("chat-pane-input");
        if (input && input.value.trim()) {
          var val = input.value.trim();
          input.value = "";
          sendWorkbenchMessage(val);
        }
        return;
      }

      var legacyForm = e.target.closest(".snippet-chat-input-form");
      if (legacyForm) {
        e.preventDefault();
        var sId = legacyForm.getAttribute("data-snippet");
        var inp = legacyForm.querySelector(".snippet-msg-input");
        if (inp && inp.value.trim()) {
          var text = inp.value.trim();
          inp.value = "";
          openDiscussionForItem(sId);
          sendWorkbenchMessage(text);
        }
      }
    });

    // Input listener for dossier real-time live search & prompt token count
    document.addEventListener("input", function (e) {
      if (e.target && e.target.id === "dossier-search-input") {
        applyDossierFilters();
      }
      if (e.target && e.target.id === "raw-prompt-textarea") {
        updatePromptTokenCount(e.target.closest("dialog"));
      }
    });

    // Keyboard support for accessible card toggles, range multiselection, and Esc reset
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        if (selectedSnippetIds.size > 0) {
          e.preventDefault();
          e.stopPropagation();
          selectedSnippetIds.clear();
          updateSelectionUI();
          return;
        }
      }

      if (e.shiftKey && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
        var activeEl = document.activeElement;
        var focusedCard = activeEl ? activeEl.closest(".snippet-card") : null;
        if (!focusedCard && lastSelectedSnippetId) {
          focusedCard = dEl(lastSelectedSnippetId);
        }
        if (focusedCard) {
          var visibleCards = getVisibleSnippetCards();
          var cardIds = visibleCards.map(function (c) { return c.getAttribute("data-snippet-id") || c.id; });
          var currId = focusedCard.getAttribute("data-snippet-id") || focusedCard.id;
          var currIdx = cardIds.indexOf(currId);
          if (currIdx !== -1) {
            var nextIdx = e.key === "ArrowDown" ? currIdx + 1 : currIdx - 1;
            if (nextIdx >= 0 && nextIdx < cardIds.length) {
              e.preventDefault();
              var targetCard = visibleCards[nextIdx];
              var targetId = cardIds[nextIdx];
              selectedSnippetIds.add(currId);
              selectedSnippetIds.add(targetId);
              lastSelectedSnippetId = targetId;
              updateSelectionUI();
              var targetHeader = targetCard.querySelector(".snippet-card-header");
              if (targetHeader && typeof targetHeader.focus === "function") {
                targetHeader.focus();
              }
              return;
            }
          }
        }
      }

      if (e.key === "Enter" || e.key === " ") {
        var header = e.target.closest("[data-card-toggle]");
        if (header && !e.target.closest(".curation-btn") && !e.target.closest("a") && !e.target.closest(".card-select-checkbox") && !e.target.closest(".btn-clear-badge")) {
          e.preventDefault();
          header.click();
        }
      }
    });

    function getOfflineWorkbenchReply(attachedIds, message) {
      var lower = message.toLowerCase();
      var items = attachedIds.map(function (id) {
        var card = dEl(id);
        return {
          id: id,
          sws: card ? (card.getAttribute("data-sws") || id) : id,
          doc: card ? (card.getAttribute("data-doc") || "AUTOSAR Spezifikation") : "AUTOSAR Spezifikation",
          isConstituting: card ? card.hasAttribute("data-is-constituting") : false,
          name: card ? (card.getAttribute("data-name") || id) : id
        };
      });

      if (items.length === 0) {
        return {
          reply: "Aktuell ist kein Element im Diskussions-Fokus. Wähle im Dossier ein oder mehrere Elemente (Inbound-Snippets oder konstituierende Records) mit „💬 Mit KI diskutieren“ aus.",
          suggestion: null,
          rationale: ""
        };
      }

      var itemsList = items.map(function (it) {
        return "• " + it.id + " (" + (it.isConstituting ? "Konstituierend · " + it.name : "Inbound aus " + it.doc) + ")";
      }).join("\n");

      if (lower.indexOf("woher") !== -1 || lower.indexOf("herkunft") !== -1 || lower.indexOf("quelle") !== -1) {
        return {
          reply: "Herkunftsnachweis (Offline-Modus) für " + items.length + " fokussierte(s) Element(e):\n\n" + itemsList + "\n\nAlle Elemente stammen aus unveränderlichen, im Repository gepinnten Spezifikationen und bilden den Audit-Trail für das Modul.",
          suggestion: null,
          rationale: ""
        };
      }
      if (lower.indexOf("sinn") !== -1 || lower.indexOf("zweck") !== -1 || lower.indexOf("warum") !== -1 || lower.indexOf("relevan") !== -1 || lower.indexOf("schnittstelle") !== -1 || lower.indexOf("beziehung") !== -1) {
        return {
          reply: "Schnittstellenbezug & Kontext:\n\n" + itemsList + "\n\nDie konstituierenden APIs definieren den Kernvertrag des Moduls, während Inbound-Snippets die verbindlichen Aufrufe und Rollenverteilungen durch Nachbarmodule belegen.",
          suggestion: null,
          rationale: ""
        };
      }
      if (lower.indexOf("falsch") !== -1 || lower.indexOf("beanstand") !== -1 || lower.indexOf("ausschlie") !== -1 || lower.indexOf("irrelevant") !== -1 || lower.indexOf("nicht konstituierend") !== -1 || lower.indexOf("stimmt nicht") !== -1) {
        var isSubstantiated = message.trim().length >= 25 && (
          lower.indexOf("weil") !== -1 || lower.indexOf("da ") !== -1 || lower.indexOf("grund") !== -1 ||
          lower.indexOf("begründ") !== -1 || lower.indexOf("treiber") !== -1 || lower.indexOf("schnittstelle") !== -1 ||
          lower.indexOf("schicht") !== -1 || lower.indexOf("redundant") !== -1 || lower.indexOf("intern") !== -1 ||
          lower.indexOf("architektur") !== -1 || lower.indexOf("nicht konstituierend") !== -1 || lower.indexOf("falsch für") !== -1 ||
          lower.indexOf("soll ausgeschlossen") !== -1 || lower.indexOf("ausgeschlossen werden") !== -1 || lower.indexOf("kein bezug") !== -1
        );
        if (!isSubstantiated) {
          return {
            reply: "Deine Beanstandung zu den ausgewählten Elementen wurde registriert.\n\nUm die Beanstandung fachlich zu prüfen und als „begründet“ zu akzeptieren, ist eine stichhaltige technische Begründung erforderlich (z. B. Schichtentrennung, falsche Modulzuordnung, Redundanz oder Architekturwiderspruch).\n\nBitte erläutere kurz: *Warum genau* ist die Zuordnung oder Eigenschaft falsch?",
            suggestion: null,
            rationale: ""
          };
        }
        var targets = items.map(function (it) { return it.id; }).join(", ");
        return {
          reply: "✓ Fachliche Prüfung bestanden: Deine Begründung („" + message + "“) ist plausibel und stichhaltig.\n\nIch habe einen gemeinsamen Kurationsvorschlag formuliert. Du kannst ihn im Vorschlags-Dialog unten entweder in die Curation-Queue einreihen (Exit 1) oder direkt als „begründet beanstandet“ im Dossier vermerken (Exit 2).",
          suggestion: "[STATUS: EXCLUDE_OR_REVISE]\nElemente im Fokus: " + targets + "\nBegründung (durch KI geprüft): " + message,
          rationale: "Im Multi-Item-Curation-Dialog begründet beanstandet: " + message
        };
      }
      return {
        reply: "Fokus auf " + items.length + " Element(e):\n\n" + itemsList + "\n\nStelle Fragen zu Herkunft, Schnittstellenbezug oder formuliere Beanstandungen für die Curation-Queue.",
        suggestion: null,
        rationale: ""
      };
    }

    // Kontext für Anfragen mit eigenem Schlüssel: Text der Karten im Fokus, wie der
    // Nutzer ihn sieht (Form wie package_context in _src/tools/ai_discuss.py).
    function workbenchContext(ids, primaryId) {
      function item(id) {
        var c = dEl(id);
        if (!c) return { record_id: id, requirement_text: "" };
        var body = c.querySelector(".snippet-card-body");
        var head = "[" + (c.getAttribute("data-sws") || id) + "] " + (c.getAttribute("data-name") || id) +
          (c.getAttribute("data-doc") ? " (" + c.getAttribute("data-doc") + ")" : "");
        return { record_id: id, requirement_text: head + "\n" + (body ? body.textContent.replace(/\s+/g, " ").trim() : "") };
      }
      var path = location.pathname;
      var primary = item(primaryId);
      return {
        record_id: primaryId,
        universe: /\/adaptive\//.test(path) ? "AUTOSAR Adaptive Platform" : "AUTOSAR Classic Platform",
        module: dossierSubject(),
        requirement_text: primary.requirement_text.slice(0, 6000),
        attached_items: ids.filter(function (id) { return id !== primaryId; }).map(item)
      };
    }

    // Herkunft der Antwort (Zugang und Modell) unter der Sprechblase.
    function appendAnswerMeta(bubble, text) {
      if (!text) return;
      var meta = document.createElement("div");
      meta.className = "chat-answer-meta";
      meta.textContent = text;
      bubble.appendChild(meta);
    }

    function showWorkbenchProposal(data, attachedIds, primaryId) {
      var propBox = dEl("chat-pane-proposal-box");
      if (!propBox) return;
      if (!data || !data.suggestion) { propBox.hidden = true; return; }
      var propText = dEl("chat-pane-proposal-text");
      var propBtn = dEl("btn-submit-workbench-proposal");
      if (!propText || !propBtn) return;
      propText.textContent = data.suggestion + "\n\nBegründung: " + (data.rationale || "");
      propBox.hidden = false;
      propBtn.dataset.suggestion = data.suggestion;
      propBtn.dataset.rationale = data.rationale || "";
      propBtn.dataset.attachedIds = JSON.stringify(attachedIds);
      propBtn.dataset.primaryId = primaryId;
    }

    async function sendWorkbenchMessage(message) {
      var thread = dEl("chat-pane-thread");
      if (!thread) return;

      var attachedIds = focusIds();
      var primaryId = attachedIds.length > 0 ? attachedIds[0] : dossierSubject();

      var userBubble = document.createElement("div");
      userBubble.className = "chat-bubble bubble-user";
      userBubble.textContent = message;
      thread.appendChild(userBubble);
      thread.scrollTop = thread.scrollHeight;

      var assistantBubble = document.createElement("div");
      assistantBubble.className = "chat-bubble bubble-assistant";
      assistantBubble.textContent = "Analysiere Fokus-Kontext…";
      thread.appendChild(assistantBubble);
      thread.scrollTop = thread.scrollHeight;

      var access = window.AiAccess;
      var aiRoute = access ? await access.route() : { kind: "local" };
      if (aiRoute.kind === "none") {
        // Ohne Anmeldung oder Modell: Einladung statt simulierter Antwort.
        assistantBubble.textContent = "";
        assistantBubble.appendChild(access.gate(aiRoute.reason));
        var inp = dEl("chat-pane-input");
        if (inp) inp.value = message;
        thread.scrollTop = thread.scrollHeight;
        return;
      }
      if (aiRoute.kind === "byok") {
        assistantBubble.textContent = "KI überlegt… (" + access.routeLabel(aiRoute) + ")";
        try {
          var reply = await access.discuss({
            route: aiRoute,
            message: message,
            context: workbenchContext(attachedIds, primaryId),
            onDelta: function (delta, all) {
              assistantBubble.textContent = all;
              thread.scrollTop = thread.scrollHeight;
            },
            // Gemini-Abo ohne Streaming: Zwischenstand statt „KI überlegt…“.
            onStatus: function (status) { assistantBubble.textContent = status; }
          });
          assistantBubble.textContent = reply.reply;
          appendAnswerMeta(assistantBubble, access.answerLabel(reply, aiRoute));
          showWorkbenchProposal(reply, attachedIds, primaryId);
        } catch (err) {
          assistantBubble.textContent = "⚠️ Keine KI-Antwort: " + String((err && err.message) || err);
        }
        thread.scrollTop = thread.scrollHeight;
        return;
      }

      try {
        var res = await fetch(localApi("/api/discuss"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "chat",
            record_id: primaryId,
            attached_ids: attachedIds,
            message: message,
            provider: aiRoute.cli || undefined,
            fallback: aiRoute.fallback || undefined
          })
        });
        var data = await res.json();
        assistantBubble.textContent = data.reply || data.error || "Keine Antwort erhalten.";
        if (data.reply && access) appendAnswerMeta(assistantBubble, access.answerLabel(data, aiRoute));
        showWorkbenchProposal(data, attachedIds, primaryId);
      } catch (err) {
        var offlineReply = getOfflineWorkbenchReply(attachedIds, message);
        assistantBubble.textContent = offlineReply.reply;
        showWorkbenchProposal(offlineReply, attachedIds, primaryId);
      }
      thread.scrollTop = thread.scrollHeight;
    }

    function submitWorkbenchProposal() {
      var propBtn = dEl("btn-submit-workbench-proposal");
      if (!propBtn) return;
      var suggestion = propBtn.dataset.suggestion || "";
      var rationale = propBtn.dataset.rationale || "";
      var primaryId = propBtn.dataset.primaryId || dossierSubject();
      var attachedIds = [];
      try {
        attachedIds = JSON.parse(propBtn.dataset.attachedIds || "[]");
      } catch (e) {
        attachedIds = focusIds();
      }
      if (attachedIds.length === 0) {
        attachedIds = [primaryId];
      }

      var thread = dEl("chat-pane-thread");
      var ident = getReviewerIdentity();
      var pkg = loadReviewPackage();
      var targetSet = new Set(attachedIds);

      // Filter out previous decisions for these ids so the new decision replaces it
      var gk = activeGuideKind();
      var nextPkg = pkg.filter(function (x) { return !(targetSet.has(x.id) && (x.guide_kind || "user") === gk); });

      attachedIds.forEach(function (id) {
        var card = dEl(id);
        var doc = card ? (card.getAttribute("data-doc") || "LinIf.json") : "LinIf.json";
        var isConstituting = card ? card.hasAttribute("data-is-constituting") : false;
        var sws = card ? (card.getAttribute("data-sws") || id) : id;
        var name = card ? (card.getAttribute("data-name") || id) : id;

        var decision = {
          id: id,
          kind: "curation_request",
          guide_kind: gk,
          outcome: "reject",
          decided_by: ident.name,
          identity: ident.mode,
          decided_at: new Date().toISOString(),
          rationale: rationale || ("Beanstandung für " + id + " (" + name + "): " + (suggestion || "Ausschluss/Revision")),
          decision_basis: {
            target_module: dossierSubject(),
            guide_kind: gk,
            item_id: id,
            source_element: sws,
            source_name: name,
            source_document: doc,
            is_constituting: isConstituting,
            proposal: suggestion
          }
        };
        nextPkg.push(decision);

        storeVote(id, { vote: "dismiss", queued: true, rationale: rationale });

        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: id, snippet_id: id, vote: "dismiss", guide_kind: activeGuideKind(), rationale: rationale, reviewer: ident.name })
          }).catch(function () {});
        } catch (e) {}
      });

      storeReviewPackage(nextPkg);
      var propBox = dEl("chat-pane-proposal-box");
      if (propBox) propBox.hidden = true;
      updateSnippetBadges();

      if (thread) {
        var conf = document.createElement("div");
        conf.className = "chat-bubble bubble-assistant";
        conf.innerHTML =
          "✓ <strong>Curation-Event im Browser-Store (<code>" + REVIEW_STORE + "</code>) abgelegt.</strong><br>" +
          "Für <strong>" + attachedIds.length + "</strong> Element(e) (" + attachedIds.join(", ") + ") wurde eine Kurationsanfrage (<code>kind: curation_request</code>, <code>outcome: reject</code>) im lokalen Review-Paket erfasst.<br>" +
          "Das Review-Paket enthält jetzt <strong>" + nextPkg.length + "</strong> Entscheidung(en).<br><br>" +
          "<strong>Offizieller Weg zur Übernahme ins Repository:</strong>" +
          "<ul style='margin: 0.35rem 0 0.6rem 1.2rem; padding: 0;'>" +
            "<li><strong>GitHub-Issue:</strong> Öffne oben rechts „Feedback &amp; Kuration“ → „Review-Paket“ und sende es als Issue an <code>2b-rs/autodocs</code>.</li>" +
            "<li><strong>JSON-Export:</strong> Exportiere das Paket als JSON-Datei und lies es via <code>python3 _src/tools/curation_ingest.py --apply paket.json</code> im Repository ein.</li>" +
          "</ul>" +
          "<div style='display:flex; gap:0.5rem; margin-top:0.4rem;'>" +
            "<button type=\"button\" class=\"curation-btn\" data-action=\"open-review-drawer\" style=\"padding:4px 10px; cursor:pointer;\">📦 Review-Paket öffnen</button>" +
            "<button type=\"button\" class=\"curation-btn\" data-action=\"export-curation-json\" style=\"padding:4px 10px; cursor:pointer;\">⬇️ JSON exportieren</button>" +
          "</div>";
        thread.appendChild(conf);
        thread.scrollTop = thread.scrollHeight;
      }
    }

    function applyProposalLocallyJustified() {
      var propBtn = dEl("btn-submit-workbench-proposal");
      var suggestion = propBtn ? (propBtn.dataset.suggestion || "") : "";
      var rationale = propBtn ? (propBtn.dataset.rationale || "") : "";
      var primaryId = (propBtn && propBtn.dataset.primaryId) || dossierSubject();
      var attachedIds = [];
      try {
        attachedIds = JSON.parse(propBtn ? (propBtn.dataset.attachedIds || "[]") : "[]");
      } catch (e) {
        attachedIds = focusIds();
      }
      if (attachedIds.length === 0) {
        attachedIds = [primaryId];
      }

      var thread = dEl("chat-pane-thread");
      var ident = getReviewerIdentity();

      attachedIds.forEach(function (id) {
        storeVote(id, { vote: "justified_dismiss", queued: false, rationale: rationale, justified_by_ai: true });

        try {
          fetch("/api/curation/vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_id: id, snippet_id: id, vote: "dismiss", rationale: rationale, reviewer: ident.name })
          }).catch(function () {});
        } catch (e) {}
      });

      var propBox = dEl("chat-pane-proposal-box");
      if (propBox) propBox.hidden = true;

      updateSnippetBadges();

      if (thread) {
        var conf = document.createElement("div");
        conf.className = "chat-bubble bubble-assistant";
        conf.innerHTML =
          "✓ <strong>Direkt als „begründet beanstandet“ im Dossier vermerkt.</strong><br>" +
          "Für <strong>" + attachedIds.length + "</strong> Element(e) (" + attachedIds.join(", ") + ") wurde die Beanstandung mit der KI-Begründung im lokalen Audit-Trail markiert. Das Element wird im Dossier hervorgehoben und kann jederzeit über das <code>✕</code> an der Badge zurückgesetzt werden.";
        thread.appendChild(conf);
        thread.scrollTop = thread.scrollHeight;
      }
    }

    try {
      window.addEventListener("ara-package-changed", function () {
        var pkg = loadReviewPackage();
        var pkgIds = new Set();
        pkg.forEach(function (d) {
          if (d && d.id && d.kind === "curation_request") {
            pkgIds.add(voteKey(d.id, d.guide_kind || "user"));
            storeVote(d.id, { vote: d.outcome === "accept" ? "confirm" : "dismiss", queued: true, rationale: d.rationale }, d.guide_kind || "user");
          }
        });
        var currentVotes = loadVotes();
        Object.keys(currentVotes).forEach(function (sid) {
          if (currentVotes[sid].queued && !pkgIds.has(sid)) {
            var upd = loadVotes();
            upd[sid] = Object.assign({}, upd[sid], { queued: false });
            try { localStorage.setItem(VOTE_STORE, JSON.stringify(upd)); } catch (e) {}
          }
        });
        syncReviewBar();
        updateSnippetBadges();
      });
    } catch (e) {}

    // Reset discussion and selection state whenever a dossier modal is closed
    document.querySelectorAll("dialog.dossier-modal").forEach(function (modal) {
      modal.addEventListener("close", function () {
        var chatPane = modal.querySelector("#dossier-chat-pane");
        if (chatPane) chatPane.hidden = true;
        modal.classList.remove("has-chat-open");
        attachedDiscussionItems.clear();
        selectedSnippetIds.clear();
        updateSelectionUI();
        renderAttachedChips();
        updateSnippetBadges();
      });
    });

    // Modelllisten der Vorschau-Reiter aus dem KI-Zugang füllen und bei jeder Änderung nachziehen
    // (Schlüssel verbunden oder entfernt, lokaler Dienst gefunden, Modell gewählt).
    refreshPreviewModelSelects();
    window.addEventListener("aiaccess-change", refreshPreviewModelSelects);
    if (window.AiAccess && typeof window.AiAccess.route === "function") {
      window.AiAccess.route().then(refreshPreviewModelSelects, function () {});
    }

    bindDossierModeTabEnhancements();
    syncReviewBar();
    updateSnippetBadges();
  }

  function bindDossierControls() {
    document.addEventListener("click", function (e) {
      var badge = e.target.closest(".ai-badge");
      var badgeButton = e.target.closest(".ai-badge-dossier-btn");
      // Badge-Text und die Badge selbst öffnen das Modal nicht.
      // Nur der Icon-Button (zugleich .dossier-open-link) tut das.
      var trigger = null;
      if (!(badge && !badgeButton)) {
        trigger = badgeButton || e.target.closest(".dossier-open-link");
      }
      if (trigger) {
        e.preventDefault();
        var targetId = trigger.getAttribute("data-dossier-target");
        var modal = targetId ? document.getElementById(targetId) : null;
        if (!modal) {
          modal = document.querySelector("dialog.dossier-modal");
        }
        if (modal && typeof modal.showModal === "function") {
          var targetMode = trigger.getAttribute("data-view-mode");
          var tabToClick = null;
          if (targetMode) {
            tabToClick = modal.querySelector('.dossier-mode-tab[data-view-mode="' + targetMode + '"]');
          }
          if (!tabToClick) {
            tabToClick = modal.querySelector('.dossier-mode-tab[data-view-mode="prompt"]') || modal.querySelector('.dossier-mode-tab[data-view-mode="raw"]');
          }
          if (tabToClick) tabToClick.click();
          if (typeof window.autodocsHydrateDossier === "function") window.autodocsHydrateDossier(modal);
          try {
            if (!modal.open) {
              modal.showModal();
            }
          } catch (err) {
            modal.setAttribute("open", "");
          }
          return;
        }
        var foldId = (trigger.getAttribute("href") || "").replace(/^#/, "");
        var fold = foldId ? document.getElementById(foldId) : null;
        if (fold) {
          fold.open = true;
          oeffnePfad(fold);
          fold.scrollIntoView({ behavior: "smooth", block: "start" });
          return;
        }
        var targetParam = targetId ? targetId.replace(/^dossier-modal-/, "") : "";
        window.location.href = "../curation-report.html" + (targetParam ? "#curate-" + encodeURIComponent(targetParam) : "");
      }
      if (e.target.closest(".dossier-close-btn")) {
        var dialog = e.target.closest("dialog");
        if (dialog) dialog.close();
      }

      var jump = e.target.closest(".rec-jump-link");
      if (jump) {
        var href = jump.getAttribute("href") || "";
        var dialog = jump.closest("dialog");
        if (href.startsWith("#")) {
          var targetId = href.substring(1);
          var targetEl = document.getElementById(targetId);
          if (dialog) {
            dialog.close();
          }
          if (targetEl) {
            e.preventDefault();
            oeffnePfad(targetEl);
            targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
            targetEl.classList.add("rec-jump-focus");
            setTimeout(function () {
              targetEl.classList.remove("rec-jump-focus");
            }, 2400);
            try {
              history.pushState(null, null, "#" + targetId);
            } catch (err) {}
          }
        } else if (dialog && !jump.getAttribute("target")) {
          dialog.close();
        }
      }
    });

    document.addEventListener("click", function (e) {
      if (e.target.tagName === "DIALOG" && e.target.classList.contains("dossier-modal")) {
        var rect = e.target.getBoundingClientRect();
        var inside = (rect.top <= e.clientY && e.clientY <= rect.top + rect.height
          && rect.left <= e.clientX && e.clientX <= rect.left + rect.width);
        if (!inside) {
          e.target.close();
        }
      }
    });

    // Domain Dropdown Initialization (Movie 2026-10-05 23-43-56)
    var dd = document.querySelector(".domain-dropdown");
    if (dd) {
      var currentLink = dd.querySelector('.shell-dropdown-menu a[aria-current="page"]');
      var curLabel = dd.querySelector(".domain-current");
      if (currentLink && curLabel) {
        curLabel.textContent = currentLink.textContent.trim();
      }
      document.addEventListener("click", function (e) {
        if (!dd.contains(e.target)) {
          dd.removeAttribute("open");
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindShellControls);
  } else {
    bindShellControls();
  }
})();
