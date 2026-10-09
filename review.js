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
      processDoc: "Read the curator decision process",
      cancel: "Cancel", decisions: "decisions", decision: "decision",
      pageReviewTitle: "%n API element%s with review needed",
      ghWeb: "Submit via GitHub in the browser", ghWebHint: "No token needed: GitHub opens a pre-filled issue, you only click “Submit new issue”.",
      ghWebOpened: "GitHub form opened. “Submit new issue” sends the package.",
      ghWebClip: "The package is long and is on your clipboard – paste it into the GitHub form.",
      ghPaste: "<!-- Paste the content from your clipboard here -->"
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
      processDoc: "Ablauf des Curator-Entscheidungsprozesses lesen",
      cancel: "Abbrechen", decisions: "Entscheidungen", decision: "Entscheidung",
      pageReviewTitle: "%n API-Element%s mit Review-Bedarf",
      ghWeb: "Über GitHub im Browser absenden", ghWebHint: "Kein Token nötig: GitHub öffnet ein vorausgefülltes Issue, du klickst nur noch auf „Submit new issue“.",
      ghWebOpened: "GitHub-Formular geöffnet. Mit „Submit new issue“ geht das Paket ab.",
      ghWebClip: "Das Paket ist lang und liegt in der Zwischenablage – füge es im GitHub-Formular ein.",
      ghPaste: "<!-- Inhalt aus der Zwischenablage hier einfügen -->"
    },
    es: { count: "Revisiones en el paquete", review: "Validar requisito", accept: "Aprobar", reject: "Rechazar", who: "Decidido por", why: "Justificación", save: "Añadir al paquete", saved: "Decisión añadida al paquete.", submit: "Enviar paquete", token: "Conectar GitHub", connected: "GitHub conectado", fallback: "Exportar JSON", empty: "El paquete está vacío.", required: "Se requieren decisión, identidad y justificación.", warn: "Alternativa sin autenticación: la identidad es autodeclarada, por lo que la tasa de aceptación puede ser menor.", sent: "Paquete de revisión enviado como incidencia de GitHub.", pkgTitle: "Paquete de revisión", close: "Cerrar", remove: "Quitar", clear: "Vaciar", ghTitle: "Conectar GitHub", ghConnect: "Conectar", ghDisconnect: "Desconectar", cancel: "Cancelar", pageReviewTitle: "%n elemento%s de API con revisión pendiente", processDoc: "Leer el proceso de decisión del curador", ghWeb: "Enviar mediante GitHub en el navegador", ghWebHint: "Sin token: GitHub abre una incidencia rellenada, solo tienes que pulsar «Submit new issue».", ghWebOpened: "Formulario de GitHub abierto. «Submit new issue» envía el paquete.", ghWebClip: "El paquete es largo y está en el portapapeles: pégalo en el formulario de GitHub.", ghPaste: "<!-- Pega aquí el contenido del portapapeles -->" },
    pt: { count: "Revisões no pacote", review: "Validar requisito", accept: "Aprovar", reject: "Rejeitar", who: "Decidido por", why: "Justificativa", save: "Adicionar ao pacote", saved: "Decisão adicionada ao pacote.", submit: "Enviar pacote", token: "Conectar GitHub", connected: "GitHub conectado", fallback: "Exportar JSON", empty: "O pacote está vazio.", required: "Decisão, identidade e justificativa são obrigatórias.", warn: "Alternativa sem autenticação: a identidade é autodeclarada, portanto a taxa de aceitação pode ser menor.", sent: "Pacote de revisão enviado como issue do GitHub.", pkgTitle: "Pacote de revisão", close: "Fechar", remove: "Remover", clear: "Limpar", ghTitle: "Conectar GitHub", ghConnect: "Conectar", ghDisconnect: "Desconectar", cancel: "Cancelar", pageReviewTitle: "%n elemento%s de API com necessidade de revisão", processDoc: "Ler o processo de decisão do curador", ghWeb: "Enviar pelo GitHub no navegador", ghWebHint: "Sem token: o GitHub abre uma issue preenchida, basta clicar em “Submit new issue”.", ghWebOpened: "Formulário do GitHub aberto. “Submit new issue” envia o pacote.", ghWebClip: "O pacote é longo e está na área de transferência – cole-o no formulário do GitHub.", ghPaste: "<!-- Cole aqui o conteúdo da área de transferência -->" },
    fr: { count: "Revues dans le lot", review: "Valider l'exigence", accept: "Approuver", reject: "Rejeter", who: "Décidé par", why: "Justification", save: "Ajouter au lot", saved: "Décision ajoutée au lot.", submit: "Envoyer le lot", token: "Connecter GitHub", connected: "GitHub connecté", fallback: "Exporter le JSON", empty: "Le lot est vide.", required: "Décision, identité et justification sont obligatoires.", warn: "Repli sans authentification : l'identité est déclarative, le taux d'acceptation peut donc être plus faible.", sent: "Lot de revue envoyé comme ticket GitHub.", pkgTitle: "Lot de revue", close: "Fermer", remove: "Retirer", clear: "Tout effacer", ghTitle: "Connecter GitHub", ghConnect: "Connecter", ghDisconnect: "Déconnecter", cancel: "Annuler", pageReviewTitle: "%n élément%s d'API nécessitant une revue", processDoc: "Lire le processus de décision du curateur", ghWeb: "Envoyer via GitHub dans le navigateur", ghWebHint: "Sans jeton : GitHub ouvre un ticket prérempli, il suffit de cliquer sur « Submit new issue ».", ghWebOpened: "Formulaire GitHub ouvert. « Submit new issue » envoie le lot.", ghWebClip: "Le lot est long et se trouve dans le presse-papiers – collez-le dans le formulaire GitHub.", ghPaste: "<!-- Collez ici le contenu du presse-papiers -->" },
    ru: { count: "Проверок в пакете", review: "Проверить требование", accept: "Принять", reject: "Отклонить", who: "Решение принял", why: "Обоснование", save: "Добавить в пакет", saved: "Решение добавлено в пакет.", submit: "Отправить пакет", token: "Подключить GitHub", connected: "GitHub подключён", fallback: "Экспорт JSON", empty: "Пакет пуст.", required: "Требуются решение, личность и обоснование.", warn: "Резервный путь без аутентификации: личность указывается самостоятельно, поэтому доля принятых решений может быть ниже.", sent: "Пакет проверок отправлен как issue на GitHub.", pkgTitle: "Пакет проверок", close: "Закрыть", remove: "Убрать", clear: "Очистить", ghTitle: "Подключить GitHub", ghConnect: "Подключить", ghDisconnect: "Отключить", cancel: "Отмена", pageReviewTitle: "%n элемент%s API, требующ%s проверки", processDoc: "Ознакомиться с процессом решений куратора", ghWeb: "Отправить через GitHub в браузере", ghWebHint: "Токен не нужен: GitHub откроет заполненный issue, останется нажать «Submit new issue».", ghWebOpened: "Форма GitHub открыта. «Submit new issue» отправит пакет.", ghWebClip: "Пакет длинный и скопирован в буфер обмена — вставьте его в форму GitHub.", ghPaste: "<!-- Вставьте сюда содержимое буфера обмена -->" },
    ar: { count: "المراجعات في الحزمة", review: "التحقق من المتطلب", accept: "اعتماد", reject: "رفض", who: "قرَّره", why: "التبرير", save: "إضافة إلى الحزمة", saved: "تمت إضافة القرار إلى الحزمة.", submit: "إرسال الحزمة", token: "ربط GitHub", connected: "تم ربط GitHub", fallback: "تصدير JSON", empty: "الحزمة فارغة.", required: "القرار والهوية والتبرير مطلوبة.", warn: "مسار بديل بدون توثيق: الهوية مُصرَّح بها ذاتيًا، لذلك قد تكون نسبة القبول أقل.", sent: "تم إرسال حزمة المراجعة كمسألة على GitHub.", pkgTitle: "حزمة المراجعة", close: "إغلاق", remove: "إزالة", clear: "مسح الكل", ghTitle: "ربط GitHub", ghConnect: "ربط", ghDisconnect: "فصل", cancel: "إلغاء", pageReviewTitle: "%n عنصر%s API يحتاج إلى مراجعة", processDoc: "الاطلاع على عملية اتخاذ قرار المنسق", ghWeb: "الإرسال عبر GitHub في المتصفح", ghWebHint: "لا حاجة إلى رمز: يفتح GitHub مسألة معبأة مسبقًا، وما عليك إلا النقر على «Submit new issue».", ghWebOpened: "فُتح نموذج GitHub. زر «Submit new issue» يرسل الحزمة.", ghWebClip: "الحزمة طويلة وهي في الحافظة – الصقها في نموذج GitHub.", ghPaste: "<!-- الصق محتوى الحافظة هنا -->" },
    hi: { count: "पैकेज में समीक्षाएँ", review: "आवश्यकता सत्यापित करें", accept: "स्वीकृत करें", reject: "अस्वीकार करें", who: "निर्णयकर्ता", why: "औचित्य", save: "पैकेज में जोड़ें", saved: "निर्णय पैकेज में जोड़ा गया।", submit: "पैकेज भेजें", token: "GitHub जोड़ें", connected: "GitHub जुड़ा", fallback: "JSON निर्यात करें", empty: "पैकेज खाली है।", required: "निर्णय, पहचान और औचित्य आवश्यक हैं।", warn: "बिना प्रमाणीकरण वाला विकल्प: पहचान स्वयं-घोषित है, इसलिए स्वीकृति दर कम हो सकती है।", sent: "समीक्षा पैकेज GitHub issue के रूप में भेजा गया।", pkgTitle: "समीक्षा पैकेज", close: "बंद करें", remove: "हटाएँ", clear: "सब हटाएँ", ghTitle: "GitHub जोड़ें", ghConnect: "जोड़ें", ghDisconnect: "हटाएँ", cancel: "रद्द करें", pageReviewTitle: "समीक्षा आवश्यक %n API तत्व", processDoc: "क्यूरेटर निर्णय प्रक्रिया पढ़ें", ghWeb: "ब्राउज़र में GitHub से भेजें", ghWebHint: "टोकन की ज़रूरत नहीं: GitHub पहले से भरा issue खोलता है, बस “Submit new issue” पर क्लिक करें।", ghWebOpened: "GitHub फ़ॉर्म खुल गया। “Submit new issue” पैकेज भेजता है।", ghWebClip: "पैकेज लंबा है और क्लिपबोर्ड में है – इसे GitHub फ़ॉर्म में पेस्ट करें।", ghPaste: "<!-- क्लिपबोर्ड की सामग्री यहाँ पेस्ट करें -->" },
    ko: { count: "패키지 내 검토", review: "요구사항 검증", accept: "승인", reject: "거부", who: "결정자", why: "근거", save: "패키지에 추가", saved: "결정이 패키지에 추가되었습니다.", submit: "패키지 제출", token: "GitHub 연결", connected: "GitHub 연결됨", fallback: "JSON 내보내기", empty: "패키지가 비어 있습니다.", required: "결정, 신원, 근거가 모두 필요합니다.", warn: "인증 없는 대체 경로: 신원이 자기 신고이므로 수용률이 낮을 수 있습니다.", sent: "검토 패키지를 GitHub 이슈로 제출했습니다.", pkgTitle: "검토 패키지", close: "닫기", remove: "제거", clear: "모두 삭제", ghTitle: "GitHub 연결", ghConnect: "연결", ghDisconnect: "연결 해제", cancel: "취소", pageReviewTitle: "검토가 필요한 API 요소 %n개", processDoc: "큐레이터 결정 프로세스 보기", ghWeb: "브라우저에서 GitHub로 제출", ghWebHint: "토큰이 필요 없습니다. GitHub가 미리 채운 이슈를 열면 “Submit new issue”만 누르세요.", ghWebOpened: "GitHub 양식이 열렸습니다. “Submit new issue”를 누르면 패키지가 제출됩니다.", ghWebClip: "패키지가 길어서 클립보드에 복사했습니다. GitHub 양식에 붙여넣으세요.", ghPaste: "<!-- 클립보드 내용을 여기에 붙여넣으세요 -->" },
    zh: { count: "包中的评审", review: "验证需求", accept: "批准", reject: "拒绝", who: "决定人", why: "理由", save: "加入包", saved: "决定已加入包。", submit: "提交数据包", token: "连接 GitHub", connected: "GitHub 已连接", fallback: "导出 JSON", empty: "数据包为空。", required: "必须填写决定、身份和理由。", warn: "未认证的备用方式：身份为自行声明，因此接受率可能较低。", sent: "评审包已作为 GitHub issue 提交。", pkgTitle: "评审包", close: "关闭", remove: "移除", clear: "全部清除", ghTitle: "连接 GitHub", ghConnect: "连接", ghDisconnect: "断开", cancel: "取消", pageReviewTitle: "需要审查的 %n 个 API 元素", processDoc: "阅读策展人决策流程", ghWeb: "在浏览器中通过 GitHub 提交", ghWebHint: "无需令牌：GitHub 会打开已填写的 issue，只需点击“Submit new issue”。", ghWebOpened: "已打开 GitHub 表单。点击“Submit new issue”即可提交数据包。", ghWebClip: "数据包较长，已复制到剪贴板——请粘贴到 GitHub 表单中。", ghPaste: "<!-- 在此粘贴剪贴板内容 -->" },
    nl: { count: "Reviews in pakket", review: "Requirement valideren", accept: "Goedkeuren", reject: "Afwijzen", who: "Beslist door", why: "Motivering", save: "Aan pakket toevoegen", saved: "Beslissing aan het pakket toegevoegd.", submit: "Pakket verzenden", token: "GitHub verbinden", connected: "GitHub verbonden", fallback: "JSON exporteren", empty: "Het pakket is leeg.", required: "Beslissing, identiteit en motivering zijn verplicht.", warn: "Fallback zonder geäuthenticeerde identiteit: de opgegeven identiteit is zelfverklaard, daarom kan de acceptatiegraad lager zijn.", sent: "Reviewpakket als GitHub-issue verzonden.", pkgTitle: "Reviewpakket", close: "Sluiten", remove: "Verwijderen", clear: "Alles wissen", ghTitle: "GitHub verbinden", ghConnect: "Verbinden", ghDisconnect: "Verbreken", cancel: "Annuleren", pageReviewTitle: "%n API-element%s met beoordelingsbehoefte", processDoc: "Lees het besluitvormingsproces van de curator", ghWeb: "Via GitHub in de browser versturen", ghWebHint: "Geen token nodig: GitHub opent een vooraf ingevuld issue, je klikt alleen nog op ‘Submit new issue’.", ghWebOpened: "GitHub-formulier geopend. ‘Submit new issue’ verstuurt het pakket.", ghWebClip: "Het pakket is lang en staat op je klembord – plak het in het GitHub-formulier.", ghPaste: "<!-- Plak hier de inhoud van je klembord -->" }
  };

  var lang = (document.documentElement.lang || "en").split("-")[0];
  // Beschriftung der Guide-Art „Implementer's Guide“ in Kurationseinträgen des Pakets
  var IMPL_GUIDE_LABEL = {
    de: "Implementer's Guide", en: "Implementer's Guide", es: "Guía del implementador", pt: "Guia do implementador",
    fr: "Guide de l'implémenteur", ru: "Руководство разработчика реализации", ar: "دليل المنفِّذ",
    hi: "इम्प्लीमेंटर गाइड", ko: "구현자 가이드", zh: "实现者指南", nl: "Implementer's Guide"
  };
  // Drawer: Feedback-Einstieg und GitHub-Status (Kopfleiste hat nur noch einen Knopf).
  var L2 = {
    de: { drawerTitle: "Feedback & Kuration", fbBtn: "Feedback / Mangel melden", ghRow: "GitHub", ghAs: "angemeldet als %s", ghOn: "Token hinterlegt", ghNone: "nicht verbunden – Absenden über ein vorausgefülltes Issue", ghConnect: "Verbinden", ghManage: "Verwalten" },
    en: { drawerTitle: "Feedback & Curation", fbBtn: "Send feedback / report a defect", ghRow: "GitHub", ghAs: "signed in as %s", ghOn: "token stored", ghNone: "not connected – submit through a prefilled issue", ghConnect: "Connect", ghManage: "Manage" },
    es: { drawerTitle: "Comentarios y curación", fbBtn: "Enviar comentarios / informar de un defecto", ghAs: "conectado como %s", ghOn: "token guardado", ghNone: "no conectado – envío mediante una incidencia rellenada", ghConnect: "Conectar", ghManage: "Gestionar" },
    pt: { drawerTitle: "Feedback e curadoria", fbBtn: "Enviar feedback / relatar defeito", ghAs: "conectado como %s", ghOn: "token guardado", ghNone: "não conectado – envio por uma issue pré-preenchida", ghConnect: "Conectar", ghManage: "Gerir" },
    fr: { drawerTitle: "Avis et modération", fbBtn: "Donner un avis / signaler un défaut", ghAs: "connecté en tant que %s", ghOn: "jeton enregistré", ghNone: "non connecté – envoi via un ticket prérempli", ghConnect: "Connecter", ghManage: "Gérer" },
    ru: { drawerTitle: "Отзывы и курация", fbBtn: "Отзыв / сообщить о дефекте", ghAs: "вход выполнен как %s", ghOn: "токен сохранён", ghNone: "не подключено – отправка через заполненный issue", ghConnect: "Подключить", ghManage: "Управлять" },
    ar: { drawerTitle: "الملاحظات والتقييم", fbBtn: "إرسال ملاحظات / الإبلاغ عن خلل", ghAs: "مسجّل الدخول باسم %s", ghOn: "الرمز محفوظ", ghNone: "غير متصل – الإرسال عبر بلاغ معبأ مسبقًا", ghConnect: "اتصال", ghManage: "إدارة" },
    hi: { drawerTitle: "प्रतिक्रिया और क्यूरेशन", fbBtn: "प्रतिक्रिया / दोष की सूचना दें", ghAs: "%s के रूप में साइन इन", ghOn: "टोकन सहेजा गया", ghNone: "कनेक्ट नहीं – पहले से भरे issue से भेजें", ghConnect: "कनेक्ट करें", ghManage: "प्रबंधित करें" },
    ko: { drawerTitle: "피드백 및 큐레이션", fbBtn: "피드백 / 결함 신고", ghAs: "%s(으)로 로그인됨", ghOn: "토큰 저장됨", ghNone: "연결 안 됨 – 미리 채운 이슈로 제출", ghConnect: "연결", ghManage: "관리" },
    zh: { drawerTitle: "反馈与策展", fbBtn: "反馈 / 报告缺陷", ghAs: "已登录为 %s", ghOn: "已保存令牌", ghNone: "未连接 – 通过预填的 issue 提交", ghConnect: "连接", ghManage: "管理" },
    nl: { drawerTitle: "Feedback & curatie", fbBtn: "Feedback / defect melden", ghAs: "aangemeld als %s", ghOn: "token opgeslagen", ghNone: "niet verbonden – indienen via een vooraf ingevuld issue", ghConnect: "Verbinden", ghManage: "Beheren" }
  };
  // Panel: Abschnitte „Feedback“ (Melden, Meine Meldungen, für Verwalter: Eingegangenes Feedback) und „Review-Paket“.
  var L3 = {
    de: {"roles": "Melden kann jede Person, auch ohne Anmeldung. Das Review-Paket sammelt deine Kurationsentscheidungen; sichten und freigeben können die Verwalter.", "fbSec": "Feedback", "fbBtn": "Feedback melden", "mine": "Meine Meldungen", "mineEmpty": "Noch keine Meldungen.", "mineEmptyAnon": "Noch keine Meldungen aus diesem Browser.", "mineSignIn": "Mit Anmeldung siehst du deine Meldungen auf allen Geräten.", "signIn": "Anmelden", "withdraw": "Zurückziehen", "answer": "Antwort", "loading": "Wird geladen …", "mineLocal": "Lokal abgelegte Meldungen liegen in _src/spec/feedback-queue/user/.", "mineIssue": "Meldungen über GitHub findest du dort unter deinen Issues.", "mineErr": "Deine Meldungen sind gerade nicht abrufbar.", "adminIn": "Eingegangenes Feedback", "adminNew": "%n neu", "adminOpen": "Sichten", "pkgSec": "Review-Paket", "pkgLead": "Kurationsentscheidungen aus dem Kurations-Editor und den Anforderungs-Reviews. Sie bleiben in diesem Browser, bis du das Paket absendest.", "pkgEmpty": "Noch leer. Stimmen und Vorschläge aus dem Kurations-Editor landen hier.", "ghNone2": "Absenden öffnet ein vorausgefülltes GitHub-Issue – dafür brauchst du ein GitHub-Konto.", "ghConnect2": "Token hinterlegen", "submit2": "Als GitHub-Issue senden"},
    en: {"roles": "Anyone can report, also without signing in. The review package collects your curation decisions; administrators review and approve.", "fbSec": "Feedback", "fbBtn": "Report feedback", "mine": "My reports", "mineEmpty": "No reports yet.", "mineEmptyAnon": "No reports from this browser yet.", "mineSignIn": "Signed in, you see your reports on every device.", "signIn": "Sign in", "withdraw": "Withdraw", "answer": "Reply", "loading": "Loading …", "mineLocal": "Locally saved reports are in _src/spec/feedback-queue/user/.", "mineIssue": "Reports sent via GitHub are listed there under your issues.", "mineErr": "Your reports cannot be loaded right now.", "adminIn": "Incoming feedback", "adminNew": "%n new", "adminOpen": "Review", "pkgSec": "Review package", "pkgLead": "Curation decisions from the curation editor and the requirement reviews. They stay in this browser until you submit the package.", "pkgEmpty": "Still empty. Votes and proposals from the curation editor end up here.", "ghNone2": "Submitting opens a prefilled GitHub issue – you need a GitHub account for it.", "ghConnect2": "Store a token", "submit2": "Submit as GitHub issue"},
    es: {"roles": "Cualquiera puede informar, también sin iniciar sesión. El paquete de revisión reúne tus decisiones de curación; los administradores revisan y aprueban.", "fbSec": "Comentarios", "fbBtn": "Enviar comentarios", "mine": "Mis avisos", "mineEmpty": "Todavía no hay avisos.", "mineEmptyAnon": "Todavía no hay avisos desde este navegador.", "mineSignIn": "Con sesión iniciada ves tus avisos en todos tus dispositivos.", "signIn": "Iniciar sesión", "withdraw": "Retirar", "answer": "Respuesta", "loading": "Cargando…", "mineLocal": "Los avisos guardados localmente están en _src/spec/feedback-queue/user/.", "mineIssue": "Los avisos enviados por GitHub están allí, entre tus incidencias.", "mineErr": "Ahora no se pueden cargar tus avisos.", "adminIn": "Comentarios recibidos", "adminNew": "%n nuevos", "adminOpen": "Revisar", "pkgSec": "Paquete de revisión", "pkgLead": "Decisiones de curación del editor de curación y de las revisiones de requisitos. Se quedan en este navegador hasta que envíes el paquete.", "pkgEmpty": "Aún vacío. Aquí llegan los votos y propuestas del editor de curación.", "ghNone2": "Enviar abre una incidencia de GitHub rellenada; necesitas una cuenta de GitHub.", "ghConnect2": "Guardar un token", "submit2": "Enviar como incidencia de GitHub"},
    pt: {"roles": "Qualquer pessoa pode relatar, também sem login. O pacote de revisão reúne suas decisões de curadoria; os administradores revisam e aprovam.", "fbSec": "Feedback", "fbBtn": "Enviar feedback", "mine": "Meus relatos", "mineEmpty": "Ainda não há relatos.", "mineEmptyAnon": "Ainda não há relatos deste navegador.", "mineSignIn": "Com login, você vê seus relatos em todos os dispositivos.", "signIn": "Entrar", "withdraw": "Retirar", "answer": "Resposta", "loading": "Carregando…", "mineLocal": "Relatos salvos localmente ficam em _src/spec/feedback-queue/user/.", "mineIssue": "Relatos enviados pelo GitHub estão lá, entre suas issues.", "mineErr": "Seus relatos não podem ser carregados agora.", "adminIn": "Feedback recebido", "adminNew": "%n novos", "adminOpen": "Revisar", "pkgSec": "Pacote de revisão", "pkgLead": "Decisões de curadoria do editor de curadoria e das revisões de requisitos. Ficam neste navegador até você enviar o pacote.", "pkgEmpty": "Ainda vazio. Votos e propostas do editor de curadoria chegam aqui.", "ghNone2": "Enviar abre uma issue do GitHub pré-preenchida – é preciso ter uma conta GitHub.", "ghConnect2": "Guardar um token", "submit2": "Enviar como issue do GitHub"},
    fr: {"roles": "Tout le monde peut signaler, même sans connexion. Le lot de revue rassemble vos décisions de curation ; les administrateurs examinent et valident.", "fbSec": "Avis", "fbBtn": "Signaler un retour", "mine": "Mes signalements", "mineEmpty": "Aucun signalement pour l'instant.", "mineEmptyAnon": "Aucun signalement depuis ce navigateur pour l'instant.", "mineSignIn": "Connecté, vous voyez vos signalements sur tous vos appareils.", "signIn": "Se connecter", "withdraw": "Retirer", "answer": "Réponse", "loading": "Chargement …", "mineLocal": "Les signalements enregistrés localement sont dans _src/spec/feedback-queue/user/.", "mineIssue": "Les signalements envoyés via GitHub y figurent parmi vos tickets.", "mineErr": "Vos signalements ne peuvent pas être chargés pour le moment.", "adminIn": "Retours reçus", "adminNew": "%n nouveaux", "adminOpen": "Examiner", "pkgSec": "Lot de revue", "pkgLead": "Décisions de curation issues de l'éditeur de modération et des revues d'exigences. Elles restent dans ce navigateur jusqu'à l'envoi du lot.", "pkgEmpty": "Encore vide. Les votes et propositions de l'éditeur de modération arrivent ici.", "ghNone2": "L'envoi ouvre un ticket GitHub prérempli – il faut un compte GitHub.", "ghConnect2": "Enregistrer un jeton", "submit2": "Envoyer comme ticket GitHub"},
    ru: {"roles": "Сообщить может любой, даже без входа. Пакет проверок собирает ваши решения по курации; разбирают и утверждают администраторы.", "fbSec": "Отзывы", "fbBtn": "Оставить отзыв", "mine": "Мои сообщения", "mineEmpty": "Сообщений пока нет.", "mineEmptyAnon": "Из этого браузера сообщений пока нет.", "mineSignIn": "После входа ваши сообщения видны на всех устройствах.", "signIn": "Войти", "withdraw": "Отозвать", "answer": "Ответ", "loading": "Загрузка…", "mineLocal": "Локально сохранённые сообщения лежат в _src/spec/feedback-queue/user/.", "mineIssue": "Сообщения через GitHub находятся там среди ваших issue.", "mineErr": "Сейчас ваши сообщения недоступны.", "adminIn": "Поступившие отзывы", "adminNew": "новых: %n", "adminOpen": "Разобрать", "pkgSec": "Пакет проверок", "pkgLead": "Решения по курации из редактора курации и проверок требований. Хранятся в этом браузере, пока вы не отправите пакет.", "pkgEmpty": "Пока пусто. Сюда попадают голоса и предложения из редактора курации.", "ghNone2": "Отправка открывает заполненный issue на GitHub — нужен аккаунт GitHub.", "ghConnect2": "Сохранить токен", "submit2": "Отправить как issue на GitHub"},
    ar: {"roles": "يمكن لأي شخص الإبلاغ، حتى دون تسجيل الدخول. تجمع حزمة المراجعة قرارات التقييم الخاصة بك؛ ويراجع المسؤولون ويعتمدون.", "fbSec": "الملاحظات", "fbBtn": "إرسال ملاحظات", "mine": "بلاغاتي", "mineEmpty": "لا توجد بلاغات بعد.", "mineEmptyAnon": "لا توجد بلاغات من هذا المتصفح بعد.", "mineSignIn": "عند تسجيل الدخول ترى بلاغاتك على جميع أجهزتك.", "signIn": "تسجيل الدخول", "withdraw": "سحب", "answer": "الرد", "loading": "جارٍ التحميل…", "mineLocal": "البلاغات المحفوظة محليًا موجودة في _src/spec/feedback-queue/user/.", "mineIssue": "البلاغات المرسلة عبر GitHub تجدها هناك ضمن مسائلك.", "mineErr": "لا يمكن تحميل بلاغاتك الآن.", "adminIn": "الملاحظات الواردة", "adminNew": "%n جديدة", "adminOpen": "مراجعة", "pkgSec": "حزمة المراجعة", "pkgLead": "قرارات التقييم من محرر التقييم ومراجعات المتطلبات. تبقى في هذا المتصفح حتى ترسل الحزمة.", "pkgEmpty": "فارغة حتى الآن. تصل إلى هنا الأصوات والمقترحات من محرر التقييم.", "ghNone2": "الإرسال يفتح مسألة GitHub معبأة مسبقًا – تحتاج إلى حساب GitHub.", "ghConnect2": "حفظ رمز", "submit2": "إرسال كمسألة GitHub"},
    hi: {"roles": "कोई भी रिपोर्ट कर सकता है, बिना साइन इन के भी। समीक्षा पैकेज आपके क्यूरेशन निर्णय इकट्ठा करता है; प्रशासक समीक्षा और स्वीकृति करते हैं।", "fbSec": "फीडबैक", "fbBtn": "फीडबैक दें", "mine": "मेरी रिपोर्टें", "mineEmpty": "अभी कोई रिपोर्ट नहीं।", "mineEmptyAnon": "इस ब्राउज़र से अभी कोई रिपोर्ट नहीं।", "mineSignIn": "साइन इन करने पर आपकी रिपोर्टें हर डिवाइस पर दिखती हैं।", "signIn": "साइन इन करें", "withdraw": "वापस लें", "answer": "उत्तर", "loading": "लोड हो रहा है…", "mineLocal": "स्थानीय रूप से सहेजी गई रिपोर्टें _src/spec/feedback-queue/user/ में हैं।", "mineIssue": "GitHub से भेजी गई रिपोर्टें वहाँ आपके issues में हैं।", "mineErr": "आपकी रिपोर्टें अभी लोड नहीं हो सकतीं।", "adminIn": "प्राप्त फ़ीडबैक", "adminNew": "%n नए", "adminOpen": "देखें", "pkgSec": "समीक्षा पैकेज", "pkgLead": "क्यूरेशन संपादक और आवश्यकता समीक्षाओं से क्यूरेशन निर्णय। पैकेज भेजने तक ये इसी ब्राउज़र में रहते हैं।", "pkgEmpty": "अभी खाली है। क्यूरेशन संपादक के वोट और प्रस्ताव यहाँ आते हैं।", "ghNone2": "भेजने पर पहले से भरा GitHub issue खुलता है – इसके लिए GitHub खाता चाहिए।", "ghConnect2": "टोकन सहेजें", "submit2": "GitHub issue के रूप में भेजें"},
    ko: {"roles": "누구나 로그인 없이도 신고할 수 있습니다. 검토 패키지는 내 큐레이션 결정을 모으며, 검토와 승인은 관리자가 합니다.", "fbSec": "피드백", "fbBtn": "피드백 보내기", "mine": "내 신고", "mineEmpty": "아직 신고가 없습니다.", "mineEmptyAnon": "이 브라우저에서 보낸 신고가 아직 없습니다.", "mineSignIn": "로그인하면 모든 기기에서 내 신고를 볼 수 있습니다.", "signIn": "로그인", "withdraw": "철회", "answer": "답변", "loading": "불러오는 중…", "mineLocal": "로컬에 저장된 신고는 _src/spec/feedback-queue/user/에 있습니다.", "mineIssue": "GitHub로 보낸 신고는 그곳의 내 이슈에 있습니다.", "mineErr": "지금은 내 신고를 불러올 수 없습니다.", "adminIn": "받은 피드백", "adminNew": "새 항목 %n개", "adminOpen": "검토", "pkgSec": "검토 패키지", "pkgLead": "큐레이션 편집기와 요구사항 검토에서 나온 큐레이션 결정입니다. 패키지를 보낼 때까지 이 브라우저에 남습니다.", "pkgEmpty": "아직 비어 있습니다. 큐레이션 편집기의 투표와 제안이 여기에 모입니다.", "ghNone2": "보내면 미리 채워진 GitHub 이슈가 열립니다. GitHub 계정이 필요합니다.", "ghConnect2": "토큰 저장", "submit2": "GitHub 이슈로 보내기"},
    zh: {"roles": "任何人都可以报告，无需登录。评审包收集你的策展决定；由管理员审阅和批准。", "fbSec": "反馈", "fbBtn": "提供反馈", "mine": "我的报告", "mineEmpty": "还没有报告。", "mineEmptyAnon": "此浏览器还没有报告。", "mineSignIn": "登录后，你可以在所有设备上看到自己的报告。", "signIn": "登录", "withdraw": "撤回", "answer": "回复", "loading": "正在加载…", "mineLocal": "本地保存的报告位于 _src/spec/feedback-queue/user/。", "mineIssue": "通过 GitHub 提交的报告可在那里你的 issue 中找到。", "mineErr": "暂时无法加载你的报告。", "adminIn": "收到的反馈", "adminNew": "%n 条新反馈", "adminOpen": "查看", "pkgSec": "评审包", "pkgLead": "来自策展编辑器和需求评审的策展决定。在你提交评审包之前，它们只保存在此浏览器中。", "pkgEmpty": "还是空的。策展编辑器中的投票和建议会出现在这里。", "ghNone2": "提交会打开一个预填的 GitHub issue——需要 GitHub 账号。", "ghConnect2": "保存令牌", "submit2": "作为 GitHub issue 提交"},
    nl: {"roles": "Iedereen kan melden, ook zonder aan te melden. Het reviewpakket verzamelt je curatiebeslissingen; beheerders beoordelen en keuren goed.", "fbSec": "Feedback", "fbBtn": "Feedback melden", "mine": "Mijn meldingen", "mineEmpty": "Nog geen meldingen.", "mineEmptyAnon": "Nog geen meldingen vanuit deze browser.", "mineSignIn": "Aangemeld zie je je meldingen op al je apparaten.", "signIn": "Aanmelden", "withdraw": "Intrekken", "answer": "Antwoord", "loading": "Laden …", "mineLocal": "Lokaal opgeslagen meldingen staan in _src/spec/feedback-queue/user/.", "mineIssue": "Meldingen via GitHub vind je daar onder je issues.", "mineErr": "Je meldingen kunnen nu niet worden geladen.", "adminIn": "Ontvangen feedback", "adminNew": "%n nieuw", "adminOpen": "Bekijken", "pkgSec": "Reviewpakket", "pkgLead": "Curatiebeslissingen uit de curatie-editor en de requirement-reviews. Ze blijven in deze browser tot je het pakket verstuurt.", "pkgEmpty": "Nog leeg. Stemmen en voorstellen uit de curatie-editor komen hier terecht.", "ghNone2": "Versturen opent een vooraf ingevuld GitHub-issue – daarvoor heb je een GitHub-account nodig.", "ghConnect2": "Token opslaan", "submit2": "Als GitHub-issue versturen"}
  };
  var t = Object.assign({}, L.en, L2.en, L3.en, L[lang] || {}, L2[lang] || {}, L3[lang] || {});

  // %n -> open count, %s -> plural suffix ("e" for German, "s" for most
  // Latin-script languages, dropped entirely for languages without plural
  // marking such as zh/ko/hi/ar). Falls back to L.en's template if the
  // active language has no pageReviewTitle key.
  var PLURAL_SUFFIX = { de: "e", en: "s", es: "s", pt: "s", fr: "s", nl: "en" };
  function formatPageReviewTitle(open) {
    var tpl = t.pageReviewTitle || L.en.pageReviewTitle;
    var suffix = open === 1 ? "" : (PLURAL_SUFFIX[lang] || "");
    return tpl.replace(/%n/g, String(open)).replace(/%s/g, suffix);
  }

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
  function store(v) {
    safe(function () { localStorage.setItem(STORE, JSON.stringify(v)); });
    update();
    try { window.dispatchEvent(new CustomEvent("ara-package-changed")); } catch (e) {}
  }
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

  function processDocHref(anchor) {
    var sheet = document.querySelector('link[rel="stylesheet"]');
    var href = sheet && sheet.getAttribute("href");
    var marker = "style.css";
    var index = href ? href.lastIndexOf(marker) : -1;
    return (index >= 0 ? href.slice(0, index) : "") + "process.html#" + anchor;
  }
  function processDocLink(anchor, label) {
    var url = processDocHref(anchor);
    return '<a class="rv-process-doc-link" href="' + esc(url) + '" aria-label="' + esc(label) + '" title="' + esc(label) + '">' + esc(label) + ICON.ext + '</a>';
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
          '<div><h2 id="rv-drawer-title">' + esc(t.drawerTitle) + '</h2>' +
          '<p class="rv-drawer-sub">' + esc(t.roles) + '</p></div>' +
          '<button type="button" class="rv-icon-btn" data-close aria-label="' + esc(t.close) + '">' + ICON.x + '</button>' +
        '</header>' +
        '<div class="rv-drawer-body">' +
          '<section class="rv-sec rv-sec-fb" data-sec="feedback" aria-labelledby="rv-sec-fb">' +
            '<div class="rv-sec-head"><h3 id="rv-sec-fb">' + esc(t.fbSec) + '</h3>' +
            '<button type="button" class="rv-btn rv-btn-primary" data-feedback-open aria-haspopup="dialog" aria-controls="feedback-dialog">' + esc(t.fbBtn) + '</button></div>' +
            '<div class="rv-fb-admin" data-fb-admin hidden></div>' +
            '<h4 class="rv-sub-h" id="rv-fb-mine" tabindex="-1">' + esc(t.mine) + '</h4>' +
            '<div class="rv-fb-mine" data-fb-mine aria-live="polite"></div>' +
          '</section>' +
          '<section class="rv-sec rv-sec-pkg" data-sec="package" aria-labelledby="rv-sec-pkg">' +
            '<div class="rv-sec-head"><h3 id="rv-sec-pkg">' + esc(t.pkgSec) + ' <span class="rv-count" data-pkg-count>0</span></h3></div>' +
            '<p class="rv-sec-lead">' + esc(t.pkgLead) + '</p>' +
            '<div data-pkg-list></div>' +
            '<div class="rv-pkg-actions">' +
              '<button type="button" class="rv-btn rv-btn-quiet" data-clear>' + esc(t.clear) + '</button>' +
              '<div class="rv-spacer"></div>' +
              '<button type="button" class="rv-btn" data-export data-auth="fallback" title="' + esc(t.warn) + '">' + ICON.down + '<span>' + esc(t.fallback) + '</span></button>' +
              '<button type="button" class="rv-btn rv-btn-primary" data-submit data-auth="authenticated">' + ICON.gh + '<span>' + esc(t.submit2) + '</span></button>' +
            '</div>' +
            '<div class="rv-gh-row" data-gh-row></div>' +
            '<p class="rv-modal-note">' + processDocLink("curator-decision-protocol", t.processDoc) + '</p>' +
          '</section>' +
        '</div>' +
      '</aside>';
    document.body.appendChild(drawer);

    drawer.addEventListener("click", function (e) {
      if (e.target.closest("[data-close]")) closeDrawer();
      var rm = e.target.closest("[data-remove]");
      if (rm) {
        var id = rm.getAttribute("data-remove"), gk = rm.getAttribute("data-guide-kind") || "user";
        store(load().filter(function (x) { return !(x.id === id && (x.guide_kind || "user") === gk); }));
        renderDrawer();
      }
      if (e.target.closest("[data-clear]") && load().length) { store([]); renderDrawer(); }
      if (e.target.closest("[data-export]")) exportPackage();
      if (e.target.closest("[data-submit]")) submitPackage();
      if (e.target.closest("[data-gh-manage]")) openGithub(false);
      var wd = e.target.closest("[data-fb-withdraw]");
      if (wd && feedbackApi()) {
        wd.disabled = true;
        feedbackApi().withdraw(wd.getAttribute("data-fb-withdraw"), wd.getAttribute("data-fb-who"))
          .then(renderFeedback, function () { wd.disabled = false; toast(t.mineErr, "error"); });
      }
      if (e.target.closest("[data-fb-signin]") && feedbackApi()) { closeDrawer(); feedbackApi().signIn(); }
      if (e.target.closest("[data-fb-admin-open]") && feedbackApi()) { closeDrawer(); feedbackApi().openAdmin(); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !drawer.hidden) closeDrawer();
    });
  }

  function renderGhRow() {
    var row = drawer.querySelector("[data-gh-row]");
    if (!row) return;
    var on = !!activeToken();
    var state = on ? (ghLogin ? t.ghAs.replace("%s", "@" + ghLogin) : t.ghOn) : t.ghNone2;
    row.innerHTML = '<span class="rv-gh-ico' + (on ? " is-on" : "") + '">' + ICON.gh + '</span>' +
      '<span class="rv-gh-text">' + (on ? '<strong>' + esc(t.ghRow || "GitHub") + '</strong> ' : "") + esc(state) + '</span>' +
      '<button type="button" class="rv-btn rv-btn-quiet" data-gh-manage>' + esc(on ? t.ghManage : t.ghConnect2) + '</button>';
    if (on && !ghLogin && !renderGhRow.pending) {
      renderGhRow.pending = true;
      verify(activeToken()).then(function (u) { ghLogin = u.login; }).catch(function () {})
        .then(function () { renderGhRow.pending = false; if (ghLogin) renderGhRow(); });
    }
  }
  function renderDrawer() {
    renderGhRow();
    var body = drawer.querySelector("[data-pkg-list]"), items = load();
    drawer.querySelector("[data-pkg-count]").textContent = items.length;
    renderFeedback();
    if (!items.length) {
      body.innerHTML = '<div class="rv-empty rv-empty-sm">' + ICON.pkg +
        '<p class="rv-empty-hint">' + esc(t.pkgEmpty) + '</p></div>';
    } else {
      body.innerHTML = '<ul class="rv-list">' + items.map(function (d) {
        if (d.item_kind === "review-request" || d.kind === "review-request") {
          var cid = d.canonical_id || d.id;
          return '<li class="rv-item rv-item-request">' +
            '<div class="rv-item-head">' +
              '<span class="rv-chip is-request">Review Request</span>' +
              '<a class="rv-item-id" href="#' + esc(cid) + '" title="' + esc(t.edit) + '">' + esc(cid) + '</a>' +
              '<button type="button" class="rv-icon-btn rv-icon-btn-sm" data-remove="' + esc(d.id) + '" aria-label="' + esc(t.remove) + '">' + ICON.x + '</button>' +
            '</div>' +
            '<p class="rv-item-why">' + esc(d.rationale) + '</p>' +
            '<p class="rv-item-meta">' + esc((d.actor_claim && d.actor_claim.display_name) || d.decided_by || "local-only") + ' · ' + esc(new Date(d.created_at || d.decided_at || Date.now()).toLocaleString(lang)) + ' (local-only)</p>' +
          '</li>';
        }
        if (d.kind === "curation_request") {
          var ok = d.outcome === "accept";
          var clabel = ok ? (lang === "de" ? "Kuration: Freigabe" : "Curation: Approve") : (lang === "de" ? "Kuration: Beanstandung" : "Curation: Reject");
          return '<li class="rv-item rv-item-curation">' +
            '<div class="rv-item-head">' +
              '<span class="rv-chip ' + (ok ? "is-accept" : "is-reject") + '">' +
                (ok ? ICON.ok : ICON.no) + esc(clabel) + '</span>' +
              '<a class="rv-item-id" href="#' + esc(d.id) + '" title="' + esc(t.edit) + '">' + esc(d.id) + '</a>' +
              (d.guide_kind === "impl" ? '<span class="rv-chip is-impl" data-guide-kind="impl">' + esc(IMPL_GUIDE_LABEL[lang] || IMPL_GUIDE_LABEL.en) + '</span>' : '') +
              '<button type="button" class="rv-icon-btn rv-icon-btn-sm" data-remove="' + esc(d.id) + '" data-guide-kind="' + esc(d.guide_kind || "user") + '" aria-label="' + esc(t.remove) + '">' + ICON.x + '</button>' +
            '</div>' +
            '<p class="rv-item-why">' + esc(d.rationale) + '</p>' +
            '<p class="rv-item-meta">' + esc(d.decided_by) + ' · ' + esc(new Date(d.decided_at).toLocaleString(lang)) + '</p>' +
          '</li>';
        }
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

  function openDrawer(section) {
    renderDrawer();
    drawer.hidden = false;
    requestAnimationFrame(function () { drawer.classList.add("is-open"); });
    document.querySelectorAll("[data-review-open]").forEach(function (b) { b.setAttribute("aria-expanded", "true"); });
    var target = section === "feedback" ? drawer.querySelector("#rv-fb-mine") : section === "package" ? drawer.querySelector("#rv-sec-pkg") : null;
    if (target) { target.setAttribute("tabindex", "-1"); target.focus(); if (target.scrollIntoView) target.scrollIntoView({ block: "start" }); }
    else { var c = drawer.querySelector(".rv-icon-btn"); if (c) c.focus(); }
  }

  // ------------------------------------------------- Meine Meldungen (ai-access.js)
  function feedbackApi() { return window.AiAccess && window.AiAccess.feedback ? window.AiAccess.feedback : null; }
  function aiText(key, arg) { var a = window.AiAccess; return a && a.text ? a.text(key, arg) : key; }
  var fbSeq = 0;
  function fbItem(x) {
    var st = x.status || "neu";
    var when = "";
    try { when = new Date(x.created).toLocaleString(lang, { dateStyle: "short", timeStyle: "short" }); } catch (e) { when = x.created || ""; }
    var c = x.ctx || {};
    var where = [c.title, c.fold].filter(Boolean).join(" · ");
    return '<li class="rv-item rv-fb-item is-' + esc(st) + '">' +
      '<div class="rv-item-head"><span class="rv-chip rv-fb-art is-' + esc(x.art || "hinweis") + '">' + esc(aiText("fbArt_" + (x.art || "hinweis"))) + '</span>' +
      '<span class="rv-chip rv-fb-st is-' + esc(st) + '">' + esc(aiText("fbSt_" + st)) + '</span>' +
      '<span class="rv-item-meta rv-fb-when">' + esc(when) + '</span>' +
      '<button type="button" class="rv-btn rv-btn-quiet rv-btn-sm" data-fb-withdraw="' + esc(x._id) + '" data-fb-who="' + esc(x._who || x.auth || "") + '">' + esc(t.withdraw) + '</button></div>' +
      '<p class="rv-item-why">' + esc(x.text) + '</p>' +
      (where ? '<p class="rv-item-meta">' + esc(where) + '</p>' : '') +
      (x.note ? '<p class="rv-fb-note"><strong>' + esc(t.answer) + ':</strong> ' + esc(x.note) + '</p>' : '') +
    '</li>';
  }
  function renderFeedback() {
    if (!drawer) return;
    var box = drawer.querySelector("[data-fb-mine]"), adm = drawer.querySelector("[data-fb-admin]");
    var api = feedbackApi();
    if (!box) return;
    if (adm) {
      var isAdm = !!(api && api.isAdmin && api.isAdmin());
      adm.hidden = !isAdm;
      if (isAdm) {
        var n = api.newCount();
        adm.innerHTML = '<span><strong>' + esc(t.adminIn) + '</strong>' + (n ? ' <span class="rv-count is-new">' + esc(t.adminNew.replace("%n", n)) + '</span>' : '') + '</span>' +
          '<button type="button" class="rv-btn" data-fb-admin-open>' + esc(t.adminOpen) + '</button>';
      }
    }
    if (!api) { box.innerHTML = '<p class="rv-empty-hint">' + esc(t.mineIssue) + '</p>'; return; }
    var seq = ++fbSeq;
    if (!box.childElementCount) box.innerHTML = '<p class="rv-empty-hint">' + esc(t.loading) + '</p>';
    api.mine().then(function (res) {
      if (seq !== fbSeq) return;
      if (res.kind === "local") { box.innerHTML = '<p class="rv-empty-hint">' + esc(t.mineLocal) + '</p>'; return; }
      if (res.kind !== "firestore") { box.innerHTML = '<p class="rv-empty-hint">' + esc(t.mineIssue) + '</p>'; return; }
      // Hinweis auf die Anmeldung nur mit wirksamer Aktion (Anmeldung eingerichtet).
      var hint = res.signedIn || !res.canSignIn ? "" : '<p class="rv-empty-hint">' + esc(t.mineSignIn) + ' <button type="button" class="rv-link" data-fb-signin>' + esc(t.signIn) + '</button></p>';
      box.innerHTML = res.items.length ? '<ul class="rv-list">' + res.items.map(fbItem).join("") + '</ul>' + hint
        : '<p class="rv-empty-hint">' + esc(res.signedIn ? t.mineEmpty : t.mineEmptyAnon) + '</p>' + hint;
    }, function () {
      if (seq === fbSeq) box.innerHTML = '<p class="rv-empty-hint">' + esc(t.mineErr) + '</p>';
    });
  }
  // Verwalter: neue Meldungen als zweiter Zähler am Knopf „Feedback & Kuration“.
  function renderAdminCount() {
    var api = feedbackApi();
    var n = api && api.isAdmin && api.isAdmin() ? api.newCount() : 0;
    document.querySelectorAll("[data-review-open].reviewbar-package").forEach(function (b) {
      var el = b.querySelector("[data-feedback-new]");
      if (!n) { if (el) el.remove(); return; }
      if (!el) { el = document.createElement("span"); el.className = "review-count is-feedback"; el.setAttribute("data-feedback-new", ""); b.appendChild(el); }
      el.textContent = n;
      el.title = t.adminIn + ": " + t.adminNew.replace("%n", n);
    });
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
          '<p class="rv-modal-note">' + processDocLink("curator-decision-protocol", t.processDoc) + '</p>' +
          '<div class="rv-status" data-gh-status></div>' +
          '<dl class="rv-facts"><dt>' + esc(t.ghRepo) + '</dt><dd><code>' + esc(repo()) + '</code></dd></dl>' +
          '<p class="rv-modal-note">' + esc(t.ghScope) + ' <a href="' + url + '" target="_blank" rel="noopener noreferrer">' + esc(t.ghCreate) + ICON.ext + '</a></p>' +
          '<label class="rv-field"><span>' + esc(t.ghLabel) + '</span>' +
            '<input type="password" class="rv-input" data-gh-token placeholder="github_pat_…" autocomplete="off" spellcheck="false">' +
          '</label>' +
          '<label class="rv-check"><input type="checkbox" data-gh-remember checked><span>' + esc(t.ghRemember) + '</span></label>' +
          '<div class="rv-web" data-gh-web-box hidden><button type="button" class="rv-btn rv-btn-primary" data-gh-web>' + ICON.gh + '<span>' + esc(t.ghWeb) + '</span></button><p class="rv-modal-note">' + esc(t.ghWebHint) + '</p></div>' +
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
      if (e.target.closest("[data-gh-web]")) { closeGithub(); submitViaBrowser(); }
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

  function openGithub(forSubmit) {
    gh.querySelector("[data-gh-web-box]").hidden = !forSubmit;
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

  // Kurationsanfragen (kind=curation_request) gehen an den Eingang curation-gate.yml,
  // der nur Issues mit „Kuration“ im Titel aufnimmt.
  function packageTitle(decisions) {
    var cur = decisions.some(function (d) { return d.kind === "curation_request"; });
    return (cur ? "Kuration: Review-Paket (" : "Requirement review package (") + decisions.length + ")";
  }

  // Ohne Token: vorausgefülltes Issue im Browser; GitHub ordnet es dem angemeldeten Konto zu.
  async function submitViaBrowser() {
    var decisions = load();
    if (!decisions.length) { toast(t.empty, "error"); return; }
    var payload = { schema: "review-package@v1", identity: "self_declared",
                    submitted_at: new Date().toISOString(), decisions: decisions };
    var body = "```json\n" + JSON.stringify(payload, null, 2) + "\n```";
    var base = "https://github.com/" + repo() + "/issues/new?title=" + encodeURIComponent(packageTitle(decisions)) + "&body=";
    var url = base + encodeURIComponent(body);
    var clip = false;
    if (url.length > 7500) {
      try { await navigator.clipboard.writeText(body); } catch (e) {}
      url = base + encodeURIComponent(t.ghPaste);
      clip = true;
    }
    window.open(url, "_blank", "noopener");
    toast(clip ? t.ghWebClip : t.ghWebOpened);
  }

  async function submitPackage() {
    var decisions = load();
    if (!decisions.length) { toast(t.empty, "error"); return; }
    if (!activeToken()) { openGithub(true); return; }
    var payload = { schema: "review-package@v1", identity: "github_authenticated",
                    submitted_at: new Date().toISOString(), decisions: decisions };
    try {
      var r = await fetch("https://api.github.com/repos/" + repo() + "/issues", {
        method: "POST",
        headers: { Accept: "application/vnd.github+json", Authorization: "Bearer " + activeToken(),
                   "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json" },
        body: JSON.stringify({ title: packageTitle(decisions),
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
        title.textContent = formatPageReviewTitle(open);
      }
    });
  }

  function init() {
    if (!document.querySelector(".reviewbar") && !document.querySelector(".dossier-modal, .snippet-card, [data-review-open]")) return;
    buildDrawer();
    buildGithub();
    document.querySelectorAll(".review-panel").forEach(initPanel);
    document.querySelectorAll("[data-review-open]").forEach(function (b) {
      b.addEventListener("click", function () { drawer.hidden ? openDrawer(b.getAttribute("data-review-section") || "") : closeDrawer(); });
    });
    document.querySelectorAll("[data-review-token]").forEach(function (b) {
      b.addEventListener("click", function () { openGithub(false); });
    });
    document.querySelectorAll("[data-review-submit]").forEach(function (b) {
      b.addEventListener("click", submitPackage);
    });
    document.querySelectorAll("[data-review-export]").forEach(function (b) {
      b.addEventListener("click", exportPackage);
    });
    document.querySelectorAll("[data-review-warning]").forEach(function (e) { e.textContent = t.warn; });
    try { window.addEventListener("ara-package-changed", update); } catch (e) {}
    try {
      window.addEventListener("aiaccess-feedback", function () { renderAdminCount(); if (drawer && !drawer.hidden) renderFeedback(); });
      window.addEventListener("aiaccess-change", function () { renderAdminCount(); });
    } catch (e) {}
    update();
  }

  window.araReview = {
    openDrawer: openDrawer,
    closeDrawer: closeDrawer,
    exportPackage: exportPackage,
    submitPackage: submitPackage,
    update: update
  };

  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", init) : init();
})();
