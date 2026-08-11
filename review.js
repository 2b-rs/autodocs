// review.js — Sammel- und Abgabe-Workflow fuer Requirement-Reviews.
// Paket-Drawer, GitHub-Verbindungsdialog und Panel-Interaktion.
(function () {
  "use strict";

  var STORE = "ara-review-package-v1", TOKEN = "ara-review-github-token-v1";

  var L = {
    en: {
      count: "Reviews in package", review: "Validate requirement", accept: "Approve", reject: "Reject",
      who: "Decided by", why: "Rationale", save: "Add to package", saved: "Decision added to the package.",
      submit: "Submit package", token: "Connect GitHub", connected: "GitHub connected",
      fallback: "Export JSON", empty: "The package is empty.",
      emptyHint: "Approve or reject a requirement to collect it here.",
      required: "Outcome and rationale are required.",
      idTitle: "Who is reviewing?", idLead: "Your name is stored with every decision so the package can be attributed.",
      idLabel: "Name or handle", idHint: "At least 2 characters. Stored locally in this browser only.",
      idSave: "Use this name", idInvalid: "Please enter a name with at least 2 characters.",
      idChange: "Change reviewer", idAuthNote: "Signed in as %s via GitHub.", idSelfNote: "Reviewing as %s (self-declared).",
      warn: "Unauthenticated fallback: the stated identity is self-declared, so the acceptance rate may be lower.",
      sent: "Review package submitted as a GitHub issue.",
      pkgTitle: "Review package", pkgSub: "Collected decisions, stored in this browser only.",
      close: "Close", remove: "Remove", clear: "Clear all", edit: "Show requirement",
      ghTitle: "Connect GitHub",
      ghIntro: "Submitting an authenticated package opens a GitHub issue in your name. That makes the decision traceable to a real account, which is why authenticated reviews are accepted more readily.",
      ghScope: "A fine-grained token with issue write access to the target repository is sufficient.",
      ghCreate: "Create a token on GitHub", ghLabel: "Personal access token",
      ghRemember: "Remember token in this browser", ghConnect: "Connect", ghDisconnect: "Disconnect",
      ghChecking: "Checking token…", ghBad: "Token rejected by GitHub.", ghRepo: "Target repository",
      ghNone: "Not connected", ghSkip: "You can also export the package as JSON without a token.",
      cancel: "Cancel", decisions: "decisions", decision: "decision"
    },
    de: {
      count: "Reviews im Paket", review: "Requirement validieren", accept: "Freigeben", reject: "Ablehnen",
      why: "Begründung", save: "Zum Paket hinzufügen", saved: "Entscheidung wurde zum Paket hinzugefügt.",
      idTitle: "Wer reviewt?", idLead: "Der Name wird bei jeder Entscheidung mitgespeichert, damit das Paket zuordenbar bleibt.",
      idLabel: "Name oder Handle", idHint: "Mindestens 2 Zeichen. Wird nur lokal in diesem Browser gespeichert.",
      idSave: "Diesen Namen verwenden", idInvalid: "Bitte einen Namen mit mindestens 2 Zeichen eingeben.",
      idChange: "Reviewer wechseln", idAuthNote: "Angemeldet als %s über GitHub.", idSelfNote: "Review als %s (selbst angegeben).",
      submit: "Paket absenden", token: "GitHub verbinden", connected: "GitHub verbunden",
      fallback: "JSON exportieren", empty: "Das Paket ist leer.",
      emptyHint: "Gib eine Anforderung frei oder lehne sie ab, um sie hier zu sammeln.",
      required: "Entscheidung, Person und Begründung sind erforderlich.",
      warn: "Fallback ohne authentifizierte Identität: Die Angabe zur Person ist Selbstauskunft, deshalb kann die Akzeptanzquote geringer sein.",
      sent: "Review-Paket wurde als GitHub-Issue abgesendet.",
      pkgTitle: "Review-Paket", pkgSub: "Gesammelte Entscheidungen, nur in diesem Browser gespeichert.",
      close: "Schließen", remove: "Entfernen", clear: "Alle verwerfen", edit: "Anforderung anzeigen",
      ghTitle: "GitHub verbinden",
      ghIntro: "Ein authentifiziert abgesendetes Paket eröffnet ein GitHub-Issue in deinem Namen. Damit ist die Entscheidung einem echten Konto zuzuordnen — deshalb werden authentifizierte Reviews eher übernommen.",
      ghScope: "Ein fein granulierter Token mit Schreibrecht für Issues im Zielrepository genügt.",
      ghCreate: "Token auf GitHub erstellen", ghLabel: "Persönlicher Zugriffstoken",
      ghRemember: "Token in diesem Browser merken", ghConnect: "Verbinden", ghDisconnect: "Trennen",
      ghChecking: "Token wird geprüft…", ghBad: "Token von GitHub abgelehnt.", ghRepo: "Zielrepository",
      ghNone: "Nicht verbunden", ghSkip: "Du kannst das Paket auch ohne Token als JSON exportieren.",
      cancel: "Abbrechen", decisions: "Entscheidungen", decision: "Entscheidung"
    },
    es: { count: "Revisiones en el paquete", review: "Validar requisito", accept: "Aprobar", reject: "Rechazar", who: "Decidido por", why: "Justificación", save: "Añadir al paquete", saved: "Decisión añadida al paquete.", submit: "Enviar paquete", token: "Conectar GitHub", connected: "GitHub conectado", fallback: "Exportar JSON", empty: "El paquete está vacío.", required: "Se requieren decisión, identidad y justificación.", warn: "Alternativa sin autenticación: la identidad es autodeclarada, por lo que la tasa de aceptación puede ser menor.", sent: "Paquete de revisión enviado como incidencia de GitHub.", pkgTitle: "Paquete de revisión", close: "Cerrar", remove: "Quitar", clear: "Vaciar", ghTitle: "Conectar GitHub", ghConnect: "Conectar", ghDisconnect: "Desconectar", cancel: "Cancelar" },
    pt: { count: "Revisões no pacote", review: "Validar requisito", accept: "Aprovar", reject: "Rejeitar", who: "Decidido por", why: "Justificativa", save: "Adicionar ao pacote", saved: "Decisão adicionada ao pacote.", submit: "Enviar pacote", token: "Conectar GitHub", connected: "GitHub conectado", fallback: "Exportar JSON", empty: "O pacote está vazio.", required: "Decisão, identidade e justificativa são obrigatórias.", warn: "Alternativa sem autenticação: a identidade é autodeclarada, portanto a taxa de aceitação pode ser menor.", sent: "Pacote de revisão enviado como issue do GitHub.", pkgTitle: "Pacote de revisão", close: "Fechar", remove: "Remover", clear: "Limpar", ghTitle: "Conectar GitHub", ghConnect: "Conectar", ghDisconnect: "Desconectar", cancel: "Cancelar" },
    fr: { count: "Revues dans le lot", review: "Valider l'exigence", accept: "Approuver", reject: "Rejeter", who: "Décidé par", why: "Justification", save: "Ajouter au lot", saved: "Décision ajoutée au lot.", submit: "Envoyer le lot", token: "Connecter GitHub", connected: "GitHub connecté", fallback: "Exporter le JSON", empty: "Le lot est vide.", required: "Décision, identité et justification sont obligatoires.", warn: "Repli sans authentification : l'identité est déclarative, le taux d'acceptation peut donc être plus faible.", sent: "Lot de revue envoyé comme ticket GitHub.", pkgTitle: "Lot de revue", close: "Fermer", remove: "Retirer", clear: "Tout effacer", ghTitle: "Connecter GitHub", ghConnect: "Connecter", ghDisconnect: "Déconnecter", cancel: "Annuler" },
    ru: { count: "Проверок в пакете", review: "Проверить требование", accept: "Принять", reject: "Отклонить", who: "Решение принял", why: "Обоснование", save: "Добавить в пакет", saved: "Решение добавлено в пакет.", submit: "Отправить пакет", token: "Подключить GitHub", connected: "GitHub подключён", fallback: "Экспорт JSON", empty: "Пакет пуст.", required: "Требуются решение, личность и обоснование.", warn: "Резервный путь без аутентификации: личность указывается самостоятельно, поэтому доля принятых решений может быть ниже.", sent: "Пакет проверок отправлен как issue на GitHub.", pkgTitle: "Пакет проверок", close: "Закрыть", remove: "Убрать", clear: "Очистить", ghTitle: "Подключить GitHub", ghConnect: "Подключить", ghDisconnect: "Отключить", cancel: "Отмена" },
    ar: { count: "المراجعات في الحزمة", review: "التحقق من المتطلب", accept: "اعتماد", reject: "رفض", who: "قرَّره", why: "التبرير", save: "إضافة إلى الحزمة", saved: "تمت إضافة القرار إلى الحزمة.", submit: "إرسال الحزمة", token: "ربط GitHub", connected: "تم ربط GitHub", fallback: "تصدير JSON", empty: "الحزمة فارغة.", required: "القرار والهوية والتبرير مطلوبة.", warn: "مسار بديل بدون توثيق: الهوية مُصرَّح بها ذاتيًا، لذلك قد تكون نسبة القبول أقل.", sent: "تم إرسال حزمة المراجعة كمسألة على GitHub.", pkgTitle: "حزمة المراجعة", close: "إغلاق", remove: "إزالة", clear: "مسح الكل", ghTitle: "ربط GitHub", ghConnect: "ربط", ghDisconnect: "فصل", cancel: "إلغاء" },
    hi: { count: "पैकेज में समीक्षाएँ", review: "आवश्यकता सत्यापित करें", accept: "स्वीकृत करें", reject: "अस्वीकार करें", who: "निर्णयकर्ता", why: "औचित्य", save: "पैकेज में जोड़ें", saved: "निर्णय पैकेज में जोड़ा गया।", submit: "पैकेज भेजें", token: "GitHub जोड़ें", connected: "GitHub जुड़ा", fallback: "JSON निर्यात करें", empty: "पैकेज खाली है।", required: "निर्णय, पहचान और औचित्य आवश्यक हैं।", warn: "बिना प्रमाणीकरण वाला विकल्प: पहचान स्वयं-घोषित है, इसलिए स्वीकृति दर कम हो सकती है।", sent: "समीक्षा पैकेज GitHub issue के रूप में भेजा गया।", pkgTitle: "समीक्षा पैकेज", close: "बंद करें", remove: "हटाएँ", clear: "सब हटाएँ", ghTitle: "GitHub जोड़ें", ghConnect: "जोड़ें", ghDisconnect: "हटाएँ", cancel: "रद्द करें" },
    ko: { count: "패키지 내 검토", review: "요구사항 검증", accept: "승인", reject: "거부", who: "결정자", why: "근거", save: "패키지에 추가", saved: "결정이 패키지에 추가되었습니다.", submit: "패키지 제출", token: "GitHub 연결", connected: "GitHub 연결됨", fallback: "JSON 내보내기", empty: "패키지가 비어 있습니다.", required: "결정, 신원, 근거가 모두 필요합니다.", warn: "인증 없는 대체 경로: 신원이 자기 신고이므로 수용률이 낮을 수 있습니다.", sent: "검토 패키지를 GitHub 이슈로 제출했습니다.", pkgTitle: "검토 패키지", close: "닫기", remove: "제거", clear: "모두 삭제", ghTitle: "GitHub 연결", ghConnect: "연결", ghDisconnect: "연결 해제", cancel: "취소" },
    zh: { count: "包中的评审", review: "验证需求", accept: "批准", reject: "拒绝", who: "决定人", why: "理由", save: "加入包", saved: "决定已加入包。", submit: "提交数据包", token: "连接 GitHub", connected: "GitHub 已连接", fallback: "导出 JSON", empty: "数据包为空。", required: "必须填写决定、身份和理由。", warn: "未认证的备用方式：身份为自行声明，因此接受率可能较低。", sent: "评审包已作为 GitHub issue 提交。", pkgTitle: "评审包", close: "关闭", remove: "移除", clear: "全部清除", ghTitle: "连接 GitHub", ghConnect: "连接", ghDisconnect: "断开", cancel: "取消" }
  };

  var lang = (document.documentElement.lang || "en").split("-")[0];
  var t = Object.assign({}, L.en, L[lang] || {});

  var ICON = {
    pkg: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8v13H3V8M1 3h22v5H1zM10 12h4"/></svg>',
    gh: '<svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>',
    send: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>',
    down: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>',
    x: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    ok: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    no: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    ext: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3"/></svg>',
    auth: '<span class="rv-auth-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 12.3-4.6M16 19l2 2 4-5"/></svg></span>',
    noauth: '<span class="rv-auth-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 11.7-5.2M16 16l6 6M22 16l-6 6"/></svg></span>'
  };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function safe(fn, dflt) { try { return fn(); } catch (e) { return dflt; } }
  function load() { return safe(function () { return JSON.parse(localStorage.getItem(STORE) || "[]"); }, []); }
  function store(v) { safe(function () { localStorage.setItem(STORE, JSON.stringify(v)); }); update(); }
  function token() { return safe(function () { return localStorage.getItem(TOKEN) || ""; }, ""); }
  function clearLogin() { ghLogin = ""; renderIdentityHints(); }
  function setToken(v) {
    safe(function () { v ? localStorage.setItem(TOKEN, v) : localStorage.removeItem(TOKEN); });
    update();
  }
  function repo() {
    var m = document.querySelector('meta[name="review-github-repo"]');
    return (m && m.content) || "2b-rs/autodocs";
  }

  // ---------------------------------------------------------------- Toast
  var toastHost;
  function toast(msg, kind) {
    if (!toastHost) {
      toastHost = document.createElement("div");
      toastHost.className = "rv-toasts";
      document.body.appendChild(toastHost);
    }
    var el = document.createElement("div");
    el.className = "rv-toast" + (kind ? " is-" + kind : "");
    el.innerHTML = (kind === "error" ? ICON.no : ICON.ok) + "<span></span>";
    el.querySelector("span").textContent = msg;
    toastHost.appendChild(el);
    requestAnimationFrame(function () { el.classList.add("is-in"); });
    setTimeout(function () {
      el.classList.remove("is-in");
      setTimeout(function () { el.remove(); }, 260);
    }, kind === "error" ? 6000 : 3200);
  }

  // ---------------------------------------------------------------- Drawer
  var drawer;
  function buildDrawer() {
    drawer = document.createElement("div");
    drawer.className = "rv-drawer";
    drawer.hidden = true;
    drawer.innerHTML =
      '<div class="rv-drawer-scrim" data-close></div>' +
      '<aside class="rv-drawer-panel" role="dialog" aria-modal="true" aria-labelledby="rv-drawer-title">' +
        '<header class="rv-drawer-head">' +
          '<div><h2 id="rv-drawer-title">' + esc(t.pkgTitle) + '</h2>' +
          '<p class="rv-drawer-sub">' + esc(t.pkgSub) + '</p></div>' +
          '<button type="button" class="rv-icon-btn" data-close aria-label="' + esc(t.close) + '">' + ICON.x + '</button>' +
        '</header>' +
        '<div class="rv-drawer-body"></div>' +
        '<footer class="rv-drawer-foot">' +
          '<button type="button" class="rv-btn rv-btn-quiet" data-clear>' + esc(t.clear) + '</button>' +
          '<div class="rv-spacer"></div>' +
          '<button type="button" class="rv-btn" data-export data-auth="fallback" title="' + esc(t.warn) + '">' + ICON.noauth + '<span>' + esc(t.fallback) + '</span></button>' +
          '<button type="button" class="rv-btn rv-btn-primary" data-submit data-auth="authenticated" title="GitHub-authenticated">' + ICON.auth + '<span>' + esc(t.submit) + '</span></button>' +
        '</footer>' +
      '</aside>';
    document.body.appendChild(drawer);

    drawer.addEventListener("click", function (e) {
      if (e.target.closest("[data-close]")) closeDrawer();
      var rm = e.target.closest("[data-remove]");
      if (rm) {
        var id = rm.getAttribute("data-remove");
        store(load().filter(function (x) { return x.id !== id; }));
        renderDrawer();
      }
      if (e.target.closest("[data-clear]") && load().length) { store([]); renderDrawer(); }
      if (e.target.closest("[data-export]")) exportPackage();
      if (e.target.closest("[data-submit]")) submitPackage();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !drawer.hidden) closeDrawer();
    });
  }

  function renderDrawer() {
    var body = drawer.querySelector(".rv-drawer-body"), items = load();
    if (!items.length) {
      body.innerHTML = '<div class="rv-empty">' + ICON.pkg +
        '<p class="rv-empty-title">' + esc(t.empty) + '</p>' +
        '<p class="rv-empty-hint">' + esc(t.emptyHint) + '</p></div>';
    } else {
      body.innerHTML = '<ul class="rv-list">' + items.map(function (d) {
        var ok = d.outcome === "accept";
        return '<li class="rv-item">' +
          '<div class="rv-item-head">' +
            '<span class="rv-chip ' + (ok ? "is-accept" : "is-reject") + '">' +
              (ok ? ICON.ok : ICON.no) + esc(ok ? t.accept : t.reject) + '</span>' +
            '<a class="rv-item-id" href="#review-' + esc(d.id) + '" title="' + esc(t.edit) + '">' + esc(d.id) + '</a>' +
            '<button type="button" class="rv-icon-btn rv-icon-btn-sm" data-remove="' + esc(d.id) + '" aria-label="' + esc(t.remove) + '">' + ICON.x + '</button>' +
          '</div>' +
          '<p class="rv-item-why">' + esc(d.rationale) + '</p>' +
          '<p class="rv-item-meta">' + esc(d.decided_by) + ' · ' + esc(new Date(d.decided_at).toLocaleString(lang)) + '</p>' +
        '</li>';
      }).join("") + '</ul>';
    }
    drawer.querySelector("[data-clear]").disabled = !items.length;
    drawer.querySelector("[data-export]").disabled = !items.length;
    drawer.querySelector("[data-submit]").disabled = !items.length;
  }

  function openDrawer() {
    renderDrawer();
    drawer.hidden = false;
    requestAnimationFrame(function () { drawer.classList.add("is-open"); });
    document.querySelectorAll("[data-review-open]").forEach(function (b) { b.setAttribute("aria-expanded", "true"); });
    var c = drawer.querySelector(".rv-icon-btn"); if (c) c.focus();
  }
  function closeDrawer() {
    drawer.classList.remove("is-open");
    document.querySelectorAll("[data-review-open]").forEach(function (b) { b.setAttribute("aria-expanded", "false"); });
    setTimeout(function () { drawer.hidden = true; }, 220);
  }

  // ------------------------------------------------------- GitHub-Dialog
  var gh;
  function buildGithub() {
    gh = document.createElement("div");
    gh.className = "rv-modal";
    gh.hidden = true;
    var url = "https://github.com/settings/tokens/new?description=ARA%20requirement%20review&scopes=public_repo";
    gh.innerHTML =
      '<div class="rv-modal-scrim" data-close></div>' +
      '<div class="rv-modal-card" role="dialog" aria-modal="true" aria-labelledby="rv-gh-title">' +
        '<header class="rv-modal-head">' +
          '<span class="rv-gh-mark">' + ICON.gh + '</span>' +
          '<h2 id="rv-gh-title">' + esc(t.ghTitle) + '</h2>' +
          '<button type="button" class="rv-icon-btn" data-close aria-label="' + esc(t.close) + '">' + ICON.x + '</button>' +
        '</header>' +
        '<div class="rv-modal-body">' +
          '<p class="rv-modal-lead">' + esc(t.ghIntro) + '</p>' +
          '<div class="rv-status" data-gh-status></div>' +
          '<dl class="rv-facts"><dt>' + esc(t.ghRepo) + '</dt><dd><code>' + esc(repo()) + '</code></dd></dl>' +
          '<p class="rv-modal-note">' + esc(t.ghScope) + ' <a href="' + url + '" target="_blank" rel="noopener noreferrer">' + esc(t.ghCreate) + ICON.ext + '</a></p>' +
          '<label class="rv-field"><span>' + esc(t.ghLabel) + '</span>' +
            '<input type="password" class="rv-input" data-gh-token placeholder="github_pat_…" autocomplete="off" spellcheck="false">' +
          '</label>' +
          '<label class="rv-check"><input type="checkbox" data-gh-remember checked><span>' + esc(t.ghRemember) + '</span></label>' +
          '<p class="rv-modal-note rv-modal-note-quiet">' + esc(t.ghSkip) + '</p><p class="rv-auth-legend">' + (activeToken() ? ICON.auth + esc(t.connected) : ICON.noauth + esc(t.ghNone)) + '</p>' +
        '</div>' +
        '<footer class="rv-modal-foot">' +
          '<button type="button" class="rv-btn rv-btn-quiet" data-gh-forget hidden>' + esc(t.ghDisconnect) + '</button>' +
          '<div class="rv-spacer"></div>' +
          '<button type="button" class="rv-btn" data-close>' + esc(t.cancel) + '</button>' +
          '<button type="button" class="rv-btn rv-btn-primary" data-gh-connect>' + esc(t.ghConnect) + '</button>' +
        '</footer>' +
      '</div>';
    document.body.appendChild(gh);

    gh.addEventListener("click", function (e) {
      if (e.target.closest("[data-close]")) closeGithub();
      if (e.target.closest("[data-gh-forget]")) { setToken(""); ghStatus(null); toast(t.ghNone); }
      if (e.target.closest("[data-gh-connect]")) connectGithub();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !gh.hidden) closeGithub();
    });
  }

  // ------------------------------------------------------ Reviewer-Identität
  var IDENT = "ara-review-identity";
  var ghLogin = "";

  function cleanName(v) { return String(v == null ? "" : v).replace(/\s+/g, " ").trim().slice(0, 80); }
  function validName(v) { return cleanName(v).length >= 2; }
  function selfName() { return safe(function () { return cleanName(localStorage.getItem(IDENT) || ""); }, ""); }
  function setSelfName(v) { safe(function () { localStorage.setItem(IDENT, cleanName(v)); }); }

  /** Aktuelle Identität ohne Nachfrage, falls bereits bekannt. */
  function knownIdentity() {
    if (activeToken() && ghLogin) return { name: ghLogin, mode: "github_authenticated" };
    var s = selfName();
    if (!activeToken() && validName(s)) return { name: s, mode: "self_declared" };
    return null;
  }

  /** Löst die Identität auf: GitHub-Login gewinnt, sonst einmalige Selbstauskunft. */
  function resolveIdentity() {
    var known = knownIdentity();
    if (known) return Promise.resolve(known);
    if (activeToken()) {
      return verify(activeToken())
        .then(function (user) { ghLogin = user.login; return { name: ghLogin, mode: "github_authenticated" }; })
        .catch(function () { return askIdentity(); });
    }
    return askIdentity();
  }

  var idModal = null;
  function askIdentity() {
    return new Promise(function (resolve, reject) {
      if (!idModal) {
        idModal = document.createElement("div");
        idModal.className = "rv-modal";
        idModal.hidden = true;
        idModal.innerHTML =
          '<div class="rv-modal-scrim" data-id-cancel></div>' +
          '<div class="rv-modal-card" role="dialog" aria-modal="true" aria-labelledby="rv-id-title">' +
            '<header class="rv-modal-head">' +
              '<span class="rv-gh-mark">' + ICON.noauth + '</span>' +
              '<h2 id="rv-id-title">' + esc(t.idTitle) + '</h2>' +
              '<button type="button" class="rv-icon-btn" data-id-cancel aria-label="' + esc(t.cancel) + '">' + ICON.x + '</button>' +
            '</header>' +
            '<div class="rv-modal-body">' +
              '<p class="rv-modal-lead">' + esc(t.idLead) + '</p>' +
              '<label class="rv-field"><span>' + esc(t.idLabel) + '</span>' +
              '<input type="text" data-id-input autocomplete="nickname" spellcheck="false" maxlength="80" required aria-describedby="rv-id-hint"></label>' +
              '<p class="rv-modal-note" id="rv-id-hint">' + esc(t.idHint) + '</p>' +
            '</div>' +
            '<footer class="rv-modal-foot">' +
              '<span class="rv-spacer"></span>' +
              '<button type="button" class="rv-btn rv-btn-quiet" data-id-cancel>' + esc(t.cancel) + '</button>' +
              '<button type="button" class="rv-btn rv-btn-primary" data-id-ok disabled>' + esc(t.idSave) + '</button>' +
            '</footer>' +
          '</div>';
        document.body.appendChild(idModal);
      }
      var input = idModal.querySelector("[data-id-input]");
      var okBtn = idModal.querySelector("[data-id-ok]");
      input.value = selfName();
      okBtn.disabled = !validName(input.value);

      function close() {
        idModal.classList.remove("is-open");
        setTimeout(function () { idModal.hidden = true; }, 200);
        input.removeEventListener("input", onInput);
        input.removeEventListener("keydown", onKey);
        okBtn.removeEventListener("click", onOk);
        idModal.querySelectorAll("[data-id-cancel]").forEach(function (e) { e.removeEventListener("click", onCancel); });
      }
      function onInput() { okBtn.disabled = !validName(input.value); }
      function onOk() {
        if (!validName(input.value)) { toast(t.idInvalid, "error"); input.focus(); return; }
        var name = cleanName(input.value);
        setSelfName(name);
        close();
        update();
        resolve({ name: name, mode: "self_declared" });
      }
      function onCancel() { close(); reject(new Error("cancelled")); }
      function onKey(e) { if (e.key === "Enter") { e.preventDefault(); onOk(); } }

      input.addEventListener("input", onInput);
      input.addEventListener("keydown", onKey);
      okBtn.addEventListener("click", onOk);
      idModal.querySelectorAll("[data-id-cancel]").forEach(function (e) { e.addEventListener("click", onCancel); });

      idModal.hidden = false;
      requestAnimationFrame(function () { idModal.classList.add("is-open"); });
      input.focus();
      input.select();
    });
  }

  /** Identitätszeile in jedem Panel aktualisieren. */
  function renderIdentityHints() {
    var id = knownIdentity();
    document.querySelectorAll("[data-review-identity]").forEach(function (el) {
      if (!id) { el.hidden = true; el.innerHTML = ""; return; }
      var tpl = id.mode === "github_authenticated" ? t.idAuthNote : t.idSelfNote;
      var icon = id.mode === "github_authenticated" ? ICON.auth : ICON.noauth;
      el.hidden = false;
      el.innerHTML = icon + "<span>" + esc(tpl.replace("%s", id.name)) + "</span>" +
        (id.mode === "self_declared" ? ' <button type="button" class="review-identity-change" data-identity-change>' + esc(t.idChange) + "</button>" : "");
    });
  }

  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-identity-change]")) { e.preventDefault(); askIdentity().then(renderIdentityHints).catch(function () {}); }
  });

  function ghStatus(user, msg, kind) {
    var box = gh.querySelector("[data-gh-status]");
    gh.querySelector("[data-gh-forget]").hidden = !token();
    if (user) {
      box.className = "rv-status is-ok";
      box.innerHTML = '<img class="rv-avatar" src="' + esc(user.avatar_url) + '" alt="" width="28" height="28">' +
        '<div><strong>' + esc(user.login) + '</strong><span>' + esc(t.connected) + '</span></div>';
    } else if (msg) {
      box.className = "rv-status is-" + (kind || "error");
      box.innerHTML = '<div><strong>' + esc(msg) + '</strong></div>';
    } else {
      box.className = "rv-status";
      box.innerHTML = '<div><strong>' + esc(t.ghNone) + '</strong></div>';
    }
  }

  async function verify(tok) {
    var r = await fetch("https://api.github.com/user", {
      headers: { Accept: "application/vnd.github+json", Authorization: "Bearer " + tok }
    });
    if (!r.ok) throw new Error(t.ghBad);
    var user = await r.json();
    ghLogin = user.login || "";
    renderIdentityHints();
    return user;
  }

  async function connectGithub() {
    var input = gh.querySelector("[data-gh-token]");
    var tok = (input.value || token()).trim();
    if (!tok) { input.focus(); return; }
    ghStatus(null, t.ghChecking, "busy");
    try {
      var user = await verify(tok);
      if (gh.querySelector("[data-gh-remember]").checked) setToken(tok);
      else { sessionToken = tok; update(); }
      ghStatus(user);
      input.value = "";
      toast(t.connected);
    } catch (e) { ghStatus(null, e.message || t.ghBad, "error"); }
  }

  var sessionToken = "";
  function activeToken() { return token() || sessionToken; }

  function openGithub() {
    gh.hidden = false;
    requestAnimationFrame(function () { gh.classList.add("is-open"); });
    ghStatus(null);
    if (activeToken()) {
      ghStatus(null, t.ghChecking, "busy");
      verify(activeToken()).then(ghStatus).catch(function () { ghStatus(null, t.ghBad, "error"); });
    }
    var f = gh.querySelector("[data-gh-token]"); if (f) f.focus();
  }
  function closeGithub() {
    gh.classList.remove("is-open");
    setTimeout(function () { gh.hidden = true; }, 200);
  }

  // ------------------------------------------------------------- Aktionen
  function exportPackage() {
    var d = load();
    if (!d.length) { toast(t.empty, "error"); return; }
    var data = { schema: "review-package@v1", identity: "self_declared",
                 submitted_at: new Date().toISOString(), warning: t.warn, decisions: d };
    var blob = new Blob([JSON.stringify(data, null, 2) + "\n"], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "ara-review-" + new Date().toISOString().replace(/[:.]/g, "-") + ".json";
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }

  async function submitPackage() {
    var decisions = load();
    if (!decisions.length) { toast(t.empty, "error"); return; }
    if (!activeToken()) { openGithub(); return; }
    var payload = { schema: "review-package@v1", identity: "github_authenticated",
                    submitted_at: new Date().toISOString(), decisions: decisions };
    try {
      var r = await fetch("https://api.github.com/repos/" + repo() + "/issues", {
        method: "POST",
        headers: { Accept: "application/vnd.github+json", Authorization: "Bearer " + activeToken(),
                   "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json" },
        body: JSON.stringify({ title: "Requirement review package (" + decisions.length + ")",
                               body: "```json\n" + JSON.stringify(payload, null, 2) + "\n```" })
      });
      if (!r.ok) throw new Error("GitHub: " + r.status + " " + (await r.text()).slice(0, 200));
      var issue = await r.json();
      store([]);
      renderDrawer();
      toast(t.sent);
      window.open(issue.html_url, "_blank", "noopener");
    } catch (e) { toast(e.message, "error"); }
  }

  // --------------------------------------------------------------- Panels
  function initPanel(p) {
    var data = safe(function () { return JSON.parse(p.querySelector(".review-data").textContent); }, null);
    if (!data) return;
    p.querySelectorAll("[data-i18n]").forEach(function (e) { e.textContent = t[e.dataset.i18n] || e.textContent; });
    var actionButtons = p.querySelectorAll("[data-review-outcome]");
    if (!actionButtons.length) return;
    actionButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        var why = p.querySelector(".review-why").value.trim();
        if (!why) { toast(t.required, "error"); return; }
        actionButtons.forEach(function (b) { b.disabled = true; });
        resolveIdentity().then(function (who) {
          commit(button.getAttribute("data-review-outcome"), why, who);
        }).catch(function () {
          actionButtons.forEach(function (b) { b.disabled = false; });
        });
      });
    });

    function commit(outcome, why, who) {
      var d = { id: data.id, flag_id: data.flag_id, text_hash: data.text_hash,
                kind: data.kind || "requirement_text",
                outcome: outcome, decided_by: who.name, identity: who.mode,
                decided_at: new Date().toISOString(),
                rationale: why, decision_basis: data.decision_basis };
      var a = load().filter(function (x) { return x.id !== d.id; });
      a.push(d);
      store(a);
      p.classList.add("is-done");
      p.open = false;
      p.hidden = true;
      toast(t.saved);
    }

    renderIdentityHints();
  }

  function update() {
    var n = load().length;
    document.querySelectorAll("[data-review-count]").forEach(function (e) { e.textContent = n; });
    document.querySelectorAll("[data-review-open]").forEach(function (e) {
      e.classList.toggle("has-items", n > 0);
      e.setAttribute("aria-label", t.count + ": " + n);
    });
    renderIdentityHints();
    document.querySelectorAll("[data-review-token]").forEach(function (e) {
      e.classList.toggle("is-connected", !!activeToken());
      var lbl = e.querySelector("[data-gh-label]");
      if (lbl) lbl.textContent = activeToken() ? t.connected : t.token;
    });
    if (drawer && !drawer.hidden) renderDrawer();
    renderPageNotice();
  }

  // Bereits entschiedene Elemente aus der Seiten-Notiz und aus den
  // Signatur-Badges ausblenden. Quelle der Wahrheit ist das lokale Paket
  // (localStorage), deshalb rein clientseitig und bei jedem update().
  function renderPageNotice() {
    var decided = {};
    load().forEach(function (d) { if (d && d.id) decided[d.id] = true; });

    document.querySelectorAll("a.review-needed-badge[href^='#review-']").forEach(function (a) {
      var id = a.getAttribute("href").slice(8);
      a.hidden = !!decided[id];
    });

    document.querySelectorAll(".page-review-notice").forEach(function (notice) {
      var links = notice.querySelectorAll("[data-review-link]");
      var open = 0;
      links.forEach(function (a) {
        var hit = !!decided[a.getAttribute("data-review-link")];
        a.hidden = hit;
        if (!hit) open++;
      });
      if (!links.length) return;

      notice.hidden = open === 0;
      var title = notice.querySelector("#page-review-title");
      if (title) {
        title.textContent = open + " API-Element" + (open === 1 ? "" : "e") + " mit Review-Bedarf";
      }
    });
  }

  function init() {
    if (!document.querySelector(".reviewbar")) return;
    buildDrawer();
    buildGithub();
    document.querySelectorAll(".review-panel").forEach(initPanel);
    document.querySelectorAll("[data-review-open]").forEach(function (b) {
      b.addEventListener("click", function () { drawer.hidden ? openDrawer() : closeDrawer(); });
    });
    document.querySelectorAll("[data-review-token]").forEach(function (b) {
      b.addEventListener("click", openGithub);
    });
    document.querySelectorAll("[data-review-submit]").forEach(function (b) {
      b.addEventListener("click", submitPackage);
    });
    document.querySelectorAll("[data-review-export]").forEach(function (b) {
      b.addEventListener("click", exportPackage);
    });
    document.querySelectorAll("[data-review-warning]").forEach(function (e) { e.textContent = t.warn; });
    update();
  }

  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", init) : init();
})();
