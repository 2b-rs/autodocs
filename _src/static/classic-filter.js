/**
 * Classic Cluster Navigation & Live Filtering
 *
 * Provides module pills, kind toggles (Functions / Types), and real-time search
 * for AUTOSAR Classic cluster pages (e.g. classic/diagnostics.html, classic/can.html).
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.ClassicFilter = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", api.init);
    } else {
      api.init();
    }
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  var I18N = {
    de: {
      all: "Alle",
      functions: "Funktionen",
      types: "Typen",
      modulesLabel: "Module",
      searchPlaceholder: "Funktion, Typ oder SWS-ID filtern…",
      searchLabel: "Echtzeit-Suche nach Funktionen, Typen und SWS-IDs",
      clearSearch: "Suche leeren",
      filterModulesLabel: "Nach Modul filtern oder anspringen",
      filterKindLabel: "Nach Element-Art filtern",
      filterRegionLabel: "Modul-Navigation und Filterung",
      showingTotal: function (shown, total) {
        return shown === total
          ? total + " Einträge"
          : shown + " von " + total + " Einträgen";
      },
      showingModule: function (shown, total, mod) {
        return shown === total
          ? total + " Einträge in " + mod
          : shown + " von " + total + " Einträgen in " + mod;
      },
      noMatches: "Keine Einträge für die aktuelle Filterung gefunden.",
      resetFilters: "Filter zurücksetzen",
      jumpTo: "Springe zu",
      jumpToModule: function (mod) {
        return "Zu Modul " + mod + " springen";
      },
      filterByModule: function (mod) {
        return "Nur Modul " + mod + " anzeigen";
      },
      filterAllModules: "Alle Module anzeigen"
    },
    en: {
      all: "All",
      functions: "Functions",
      types: "Types",
      modulesLabel: "Modules",
      searchPlaceholder: "Filter function, type or SWS-ID…",
      searchLabel: "Real-time search for functions, types and SWS-IDs",
      clearSearch: "Clear search",
      filterModulesLabel: "Filter by module or jump to section",
      filterKindLabel: "Filter by element kind",
      filterRegionLabel: "Module Navigation and Filtering",
      showingTotal: function (shown, total) {
        return shown === total
          ? total + " entries"
          : shown + " of " + total + " entries";
      },
      showingModule: function (shown, total, mod) {
        return shown === total
          ? total + " entries in " + mod
          : shown + " of " + total + " entries in " + mod;
      },
      noMatches: "No entries found matching the current filter.",
      resetFilters: "Reset filters",
      jumpTo: "Jump to",
      jumpToModule: function (mod) {
        return "Jump to module " + mod;
      },
      filterByModule: function (mod) {
        return "Show only module " + mod;
      },
      filterAllModules: "Show all modules"
    }
  };

  function getLang() {
    if (typeof document === "undefined") return "de";
    var lang = (document.documentElement.getAttribute("lang") || "de").toLowerCase();
    return lang.startsWith("de") ? "de" : "en";
  }

  function getTexts(lang) {
    return I18N[lang || getLang()] || I18N.en;
  }

  function extractModuleAbbreviation(headingText) {
    if (!headingText) return "";
    var trimmed = headingText.trim();
    // 1. Parenthesized abbreviation, e.g. "Diagnostic Event Manager (DEM)" -> "DEM"
    var parenMatch = trimmed.match(/\(([^)]+)\)/);
    if (parenMatch) {
      return parenMatch[1].trim();
    }
    // 2. "AUTOSAR COM" -> "COM", "AUTOSAR OS" -> "OS", "AUTOSAR RTE" -> "RTE"
    if (/^AUTOSAR\s+/i.test(trimmed)) {
      return trimmed.replace(/^AUTOSAR\s+/i, "").trim();
    }
    return trimmed;
  }

  function slugify(text) {
    return "mod-" + text.toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function extractItemName(h3El) {
    var clone = h3El.cloneNode(true);
    var kindEl = clone.querySelector(".kind");
    if (kindEl) kindEl.remove();
    var swsEl = clone.querySelector(".sws");
    if (swsEl) swsEl.remove();
    return clone.textContent.trim();
  }

  function isClassicPage() {
    if (typeof window === "undefined" || typeof document === "undefined") return false;
    var pathname = window.location.pathname || "";
    if (pathname.indexOf("/classic/") !== -1 || pathname.endsWith("classic") || pathname.endsWith("classic.html")) {
      return true;
    }
    if (document.querySelector('nav.crumbs a[href*="classic/"]')) {
      return true;
    }
    var crumbs = document.querySelector("nav.crumbs");
    if (crumbs && /AUTOSAR Classic/i.test(crumbs.textContent)) {
      return true;
    }
    return false;
  }

  function parseModulesAndItems(recArticle) {
    var children = Array.from(recArticle.children);
    var modules = [];
    var allItems = [];
    var currentModule = null;
    var currentItem = null;

    for (var i = 0; i < children.length; i++) {
      var child = children[i];
      var tag = child.tagName.toLowerCase();

      if (tag === "h2") {
        var headingText = child.textContent.trim();
        var abbrev = extractModuleAbbreviation(headingText);
        var slug = slugify(abbrev);

        currentModule = {
          id: abbrev,
          slug: slug,
          title: headingText,
          h2: child,
          headerElements: [child],
          items: [],
          functionsCount: 0,
          typesCount: 0
        };
        modules.push(currentModule);
        currentItem = null;
      } else if (tag === "p" && child.classList.contains("lead") && currentModule && currentModule.items.length === 0) {
        currentModule.headerElements.push(child);
      } else if (tag === "h3" && child.classList.contains("recname")) {
        var kindSpan = child.querySelector(".kind");
        var kind = kindSpan ? kindSpan.textContent.trim().toLowerCase() : "function";
        var swsSpan = child.querySelector(".sws");
        var swsText = swsSpan ? swsSpan.textContent.trim().replace(/^\[|\]$/g, "") : "";
        var itemName = extractItemName(child);

        var item = {
          name: itemName,
          sws: swsText,
          kind: kind,
          module: currentModule ? currentModule.id : "default",
          h3: child,
          siblings: [],
          searchIndex: (itemName + " " + swsText + " " + (currentModule ? currentModule.id : "")).toLowerCase()
        };

        if (currentModule) {
          currentModule.items.push(item);
          if (kind === "function") {
            currentModule.functionsCount++;
          } else if (kind === "type") {
            currentModule.typesCount++;
          }
        }
        allItems.push(item);
        currentItem = item;
      } else if (child.classList.contains("review-request-panel")) {
        // End of spec items, boundary
        currentItem = null;
      } else if (currentItem) {
        currentItem.siblings.push(child);
      }
    }

    return {
      modules: modules,
      items: allItems
    };
  }

  function init() {
    if (!isClassicPage()) return null;

    var recArticle = document.querySelector("article.rec");
    if (!recArticle || recArticle.dataset.classicFilterInitialized === "true") {
      return null;
    }

    var parsed = parseModulesAndItems(recArticle);
    var modules = parsed.modules;
    var allItems = parsed.items;

    // Only activate if we have items to navigate
    if (allItems.length === 0) return null;

    recArticle.dataset.classicFilterInitialized = "true";

    var lang = getLang();
    var texts = getTexts(lang);

    // 1. Structure the DOM: Wrap items into .classic-entry and modules into .classic-module-section
    modules.forEach(function (mod) {
      var section = document.createElement("section");
      section.className = "classic-module-section";
      section.id = mod.slug;
      section.setAttribute("data-module", mod.id);

      // Anchor in H2
      if (!mod.h2.querySelector(".classic-heading-anchor")) {
        var anchor = document.createElement("a");
        anchor.href = "#" + mod.slug;
        anchor.className = "classic-heading-anchor";
        anchor.title = texts.jumpToModule(mod.id);
        anchor.setAttribute("aria-label", texts.jumpToModule(mod.id));
        anchor.textContent = "#";
        mod.h2.prepend(anchor);
      }

      // Insert section before H2
      recArticle.insertBefore(section, mod.h2);

      // Move header elements into section
      mod.headerElements.forEach(function (el) {
        section.appendChild(el);
      });

      var itemsContainer = document.createElement("div");
      itemsContainer.className = "classic-module-items";
      section.appendChild(itemsContainer);

      // Wrap each item into .classic-entry and place into itemsContainer
      mod.items.forEach(function (item) {
        var entry = document.createElement("div");
        entry.className = "classic-entry";
        entry.setAttribute("data-kind", item.kind);
        entry.setAttribute("data-module", mod.id);
        entry.setAttribute("data-name", item.name);
        if (item.sws) {
          entry.setAttribute("data-sws", item.sws);
        }

        // Assign ID if missing for deep linking
        if (!entry.id) {
          entry.id = item.name;
        }

        entry.appendChild(item.h3);
        item.siblings.forEach(function (sib) {
          entry.appendChild(sib);
        });

        itemsContainer.appendChild(entry);
        item.entryEl = entry;
      });

      mod.sectionEl = section;
    });

    // 2. Build Filter Bar
    var filterBar = document.createElement("nav");
    filterBar.className = "classic-filter-bar";
    filterBar.setAttribute("role", "region");
    filterBar.setAttribute("aria-label", texts.filterRegionLabel);

    // Compute initial totals
    var totalCount = allItems.length;
    var totalFunctions = 0;
    var totalTypes = 0;
    allItems.forEach(function (item) {
      if (item.kind === "function") totalFunctions++;
      else if (item.kind === "type") totalTypes++;
    });

    // Top Bar (Search + Kind Switch + Status)
    var topRow = document.createElement("div");
    topRow.className = "classic-filter-top";

    // Search Box
    var searchBox = document.createElement("div");
    searchBox.className = "classic-filter-search";
    searchBox.setAttribute("role", "search");

    var searchIcon = document.createElement("span");
    searchIcon.className = "classic-search-icon";
    searchIcon.setAttribute("aria-hidden", "true");
    searchIcon.innerHTML =
      '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>';
    searchBox.appendChild(searchIcon);

    var searchInput = document.createElement("input");
    searchInput.type = "search";
    searchInput.className = "classic-search-input";
    searchInput.placeholder = texts.searchPlaceholder;
    searchInput.setAttribute("aria-label", texts.searchLabel);
    searchInput.autocomplete = "off";
    searchInput.spellcheck = false;
    searchBox.appendChild(searchInput);

    var searchClear = document.createElement("button");
    searchClear.type = "button";
    searchClear.className = "classic-search-clear";
    searchClear.title = texts.clearSearch;
    searchClear.setAttribute("aria-label", texts.clearSearch);
    searchClear.hidden = true;
    searchClear.textContent = "✕";
    searchBox.appendChild(searchClear);

    topRow.appendChild(searchBox);

    // Kind Switch (Segmented Button Group)
    var kindSwitch = document.createElement("div");
    kindSwitch.className = "classic-kind-switch";
    kindSwitch.setAttribute("role", "group");
    kindSwitch.setAttribute("aria-label", texts.filterKindLabel);

    var kinds = [
      { id: "all", label: texts.all, count: totalCount },
      { id: "function", label: texts.functions, count: totalFunctions },
      { id: "type", label: texts.types, count: totalTypes }
    ];

    var kindButtons = {};
    kinds.forEach(function (k) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "classic-kind-btn" + (k.id === "all" ? " is-active" : "");
      btn.setAttribute("data-kind", k.id);
      btn.setAttribute("aria-pressed", k.id === "all" ? "true" : "false");

      var labelSpan = document.createElement("span");
      labelSpan.className = "kind-label";
      labelSpan.textContent = k.label;
      btn.appendChild(labelSpan);

      var countBadge = document.createElement("span");
      countBadge.className = "kind-badge";
      countBadge.textContent = String(k.count);
      btn.appendChild(countBadge);

      kindSwitch.appendChild(btn);
      kindButtons[k.id] = btn;
    });

    topRow.appendChild(kindSwitch);

    // Status Count
    var statusBox = document.createElement("div");
    statusBox.className = "classic-filter-status";
    statusBox.setAttribute("aria-live", "polite");

    var statusText = document.createElement("span");
    statusText.className = "classic-count-text";
    statusText.textContent = texts.showingTotal(totalCount, totalCount);
    statusBox.appendChild(statusText);

    topRow.appendChild(statusBox);
    filterBar.appendChild(topRow);

    // Bottom Row: Module Pills
    var modulesRow = document.createElement("div");
    modulesRow.className = "classic-filter-modules";
    modulesRow.setAttribute("role", "toolbar");
    modulesRow.setAttribute("aria-label", texts.filterModulesLabel);

    var pillsLabel = document.createElement("span");
    pillsLabel.className = "classic-pills-label";
    pillsLabel.textContent = texts.modulesLabel + ":";
    modulesRow.appendChild(pillsLabel);

    var pillsScroll = document.createElement("div");
    pillsScroll.className = "classic-pills-scroll";

    var modulePills = {};

    // "Alle" Pill
    var allPill = document.createElement("div");
    allPill.className = "classic-pill is-active";
    allPill.setAttribute("data-module", "all");

    var allBtn = document.createElement("button");
    allBtn.type = "button";
    allBtn.className = "classic-pill-btn";
    allBtn.setAttribute("aria-pressed", "true");
    allBtn.title = texts.filterAllModules;

    var allName = document.createElement("span");
    allName.className = "pill-name";
    allName.textContent = texts.all;
    allBtn.appendChild(allName);

    var allBadge = document.createElement("span");
    allBadge.className = "pill-badge";
    allBadge.textContent = String(totalCount);
    allBtn.appendChild(allBadge);

    allPill.appendChild(allBtn);
    pillsScroll.appendChild(allPill);
    modulePills["all"] = allPill;

    // Per-Module Pills
    modules.forEach(function (mod) {
      var pill = document.createElement("div");
      pill.className = "classic-pill";
      pill.setAttribute("data-module", mod.id);

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "classic-pill-btn";
      btn.setAttribute("aria-pressed", "false");
      btn.title = mod.title + " – " + texts.filterByModule(mod.id);

      var nameSpan = document.createElement("span");
      nameSpan.className = "pill-name";
      nameSpan.textContent = mod.id;
      btn.appendChild(nameSpan);

      var badge = document.createElement("span");
      badge.className = "pill-badge";
      badge.textContent = String(mod.items.length);
      btn.appendChild(badge);

      pill.appendChild(btn);

      // Jump mark link ↗
      var jumpLink = document.createElement("a");
      jumpLink.href = "#" + mod.slug;
      jumpLink.className = "classic-pill-jump";
      jumpLink.title = texts.jumpToModule(mod.id);
      jumpLink.setAttribute("aria-label", texts.jumpToModule(mod.id));
      jumpLink.textContent = "↗";
      pill.appendChild(jumpLink);

      pillsScroll.appendChild(pill);
      modulePills[mod.id] = pill;
    });

    modulesRow.appendChild(pillsScroll);
    filterBar.appendChild(modulesRow);

    // Empty state container
    var emptyBox = document.createElement("div");
    emptyBox.className = "classic-filter-empty";
    emptyBox.hidden = true;

    var emptyMsg = document.createElement("p");
    emptyMsg.className = "classic-empty-msg";
    emptyMsg.textContent = texts.noMatches;
    emptyBox.appendChild(emptyMsg);

    var resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.className = "classic-btn-reset";
    resetBtn.textContent = texts.resetFilters;
    emptyBox.appendChild(resetBtn);

    // Insert filterBar & emptyBox right before recArticle
    recArticle.parentNode.insertBefore(filterBar, recArticle);
    recArticle.parentNode.insertBefore(emptyBox, recArticle);

    // 3. State & Filtering Logic
    var state = {
      activeModule: "all",
      activeKind: "all",
      searchQuery: ""
    };

    function applyFilters() {
      var q = state.searchQuery.trim().toLowerCase();
      var totalVisible = 0;
      var currentModVisible = 0;

      modules.forEach(function (mod) {
        var modMatches = state.activeModule === "all" || state.activeModule === mod.id;
        var modVisibleItems = 0;

        mod.items.forEach(function (item) {
          var kindMatch = state.activeKind === "all" || item.kind === state.activeKind;
          var searchMatch = !q || item.searchIndex.indexOf(q) !== -1;
          var isVisible = modMatches && kindMatch && searchMatch;

          item.entryEl.hidden = !isVisible;
          if (isVisible) {
            modVisibleItems++;
            totalVisible++;
          }
        });

        // Hide whole module section if it is filtered out by module pill,
        // or if search query is active and 0 items match in this module
        if (!modMatches || (q && modVisibleItems === 0)) {
          mod.sectionEl.hidden = true;
        } else {
          mod.sectionEl.hidden = false;
        }

        if (state.activeModule === mod.id) {
          currentModVisible = modVisibleItems;
        }
      });

      // Update Kind Buttons
      Object.keys(kindButtons).forEach(function (k) {
        var btn = kindButtons[k];
        var isActive = state.activeKind === k;
        btn.classList.toggle("is-active", isActive);
        btn.setAttribute("aria-pressed", isActive ? "true" : "false");
      });

      // Update Module Pills
      Object.keys(modulePills).forEach(function (modId) {
        var pill = modulePills[modId];
        var isActive = state.activeModule === modId;
        pill.classList.toggle("is-active", isActive);
        var pillBtn = pill.querySelector(".classic-pill-btn");
        if (pillBtn) {
          pillBtn.setAttribute("aria-pressed", isActive ? "true" : "false");
        }
      });

      // Update Status Text
      if (state.activeModule !== "all") {
        statusText.textContent = texts.showingModule(
          currentModVisible,
          modulePills[state.activeModule] ? modules.find(function(m){ return m.id === state.activeModule; }).items.length : totalCount,
          state.activeModule
        );
      } else {
        statusText.textContent = texts.showingTotal(totalVisible, totalCount);
      }

      // Update Empty State
      emptyBox.hidden = totalVisible > 0;

      // Update Search Clear Button
      searchClear.hidden = searchInput.value.length === 0;
    }

    // 4. Event Listeners

    // Search input
    searchInput.addEventListener("input", function () {
      state.searchQuery = searchInput.value;
      applyFilters();
    });

    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        searchInput.value = "";
        state.searchQuery = "";
        applyFilters();
        searchInput.blur();
      }
    });

    // Global keyboard shortcut: "/" to focus search
    document.addEventListener("keydown", function (e) {
      if (
        e.key === "/" &&
        document.activeElement !== searchInput &&
        !/^(input|textarea|select)$/i.test(document.activeElement.tagName)
      ) {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
    });

    // Search Clear
    searchClear.addEventListener("click", function () {
      searchInput.value = "";
      state.searchQuery = "";
      applyFilters();
      searchInput.focus();
    });

    // Reset button in empty state
    resetBtn.addEventListener("click", function () {
      searchInput.value = "";
      state.searchQuery = "";
      state.activeModule = "all";
      state.activeKind = "all";
      applyFilters();
      searchInput.focus();
    });

    // Kind button clicks
    kindSwitch.addEventListener("click", function (e) {
      var btn = e.target.closest(".classic-kind-btn");
      if (!btn) return;
      var targetKind = btn.getAttribute("data-kind");
      if (targetKind) {
        state.activeKind = targetKind;
        applyFilters();
      }
    });

    // Module pill clicks
    pillsScroll.addEventListener("click", function (e) {
      var jump = e.target.closest(".classic-pill-jump");
      if (jump) {
        // Jump link clicked: unfilter if another module was active, then smooth scroll
        var parentPill = jump.closest(".classic-pill");
        var modId = parentPill.getAttribute("data-module");
        if (state.activeModule !== "all" && state.activeModule !== modId) {
          state.activeModule = "all";
          applyFilters();
        }
        var targetSection = document.getElementById(jump.getAttribute("href").replace("#", ""));
        if (targetSection) {
          targetSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        return;
      }

      var pillBtn = e.target.closest(".classic-pill-btn");
      if (!pillBtn) return;

      var pill = pillBtn.closest(".classic-pill");
      var selectedMod = pill.getAttribute("data-module");

      if (selectedMod === "all") {
        state.activeModule = "all";
        applyFilters();
        filterBar.scrollIntoView({ behavior: "smooth", block: "start" });
      } else if (state.activeModule === selectedMod) {
        // Toggle back to "all" if clicking the active module
        state.activeModule = "all";
        applyFilters();
      } else {
        state.activeModule = selectedMod;
        applyFilters();
        var modObj = modules.find(function (m) { return m.id === selectedMod; });
        if (modObj && modObj.sectionEl) {
          modObj.sectionEl.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    });

    // Hash navigation on load and on hashchange
    function handleHash() {
      var hash = window.location.hash ? window.location.hash.substring(1) : "";
      if (!hash) return;

      // Check if hash matches a module slug or ID
      var matchingMod = modules.find(function (m) {
        return m.slug === hash || m.id.toLowerCase() === hash.toLowerCase();
      });

      if (matchingMod) {
        state.activeModule = matchingMod.id;
        applyFilters();
        matchingMod.sectionEl.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }

      // Check if hash matches an item
      var matchingItem = allItems.find(function (item) {
        return item.name === hash || item.sws === hash || item.entryEl.id === hash;
      });

      if (matchingItem) {
        // If the item's module was filtered out, switch to all or to that module
        if (state.activeModule !== "all" && state.activeModule !== matchingItem.module) {
          state.activeModule = matchingItem.module;
          applyFilters();
        }
        matchingItem.entryEl.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }

    if (window.location.hash) {
      setTimeout(handleHash, 50);
    }
    window.addEventListener("hashchange", handleHash);

    return {
      state: state,
      modules: modules,
      items: allItems,
      applyFilters: applyFilters,
      filterBar: filterBar
    };
  }

  return {
    init: init,
    extractModuleAbbreviation: extractModuleAbbreviation,
    parseModulesAndItems: parseModulesAndItems,
    getTexts: getTexts,
    I18N: I18N
  };
});
