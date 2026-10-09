// ai-access.js — Anmeldung, eigene KI-Schlüssel (BYOK) und Modellwahl für die KI-Diskussion.
//
// * Anmeldung über Firebase Authentication (Google oder E-Mail-Link), ganz im Browser.
//   Konfiguration: ai-access.config.json neben diesem Skript. Fehlt sie, bleibt die
//   Anmeldung „in Einrichtung“; lokal (localhost) geht es auch ohne Anmeldung.
// * Schlüssel liegen je Konto im Browser-Speicher (localStorage, wahlweise nur für die
//   Sitzung) und gehen ausschließlich direkt an den gewählten Anbieter. Kein Backend sieht sie.
// * Lokal (serve.py) werden zusätzlich die vom Backend erkannten KI-CLIs angeboten.
// * Vorschläge gehen auf der öffentlichen Seite als vorausgefülltes GitHub-Issue an den
//   Kurationseingang (curation-gate.yml, Titel mit „Kuration“).
// * Leser-Feedback (AiAccess.feedback): Firestore feedback/{id}, ohne Anmeldung über ein anonymes Konto in
//   der eigenen App-Instanz „autodocs-feedback“; Sichtung in der Verwaltung (CONCEPT-0062).
(function (root, factory) {
  var api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  root.AiAccess = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", api.init);
    else api.init();
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";

  var SCRIPT_BASE = (function () {
    try {
      var s = root.document && root.document.currentScript;
      if (s && s.src) return s.src.replace(/[^/]*$/, "");
    } catch (e) { /* ignore */ }
    return "";
  })();
  var DEFAULT_SDK = "https://www.gstatic.com/firebasejs/10.14.1";
  var SESSION_FLAG = "autodocs-auth-session";
  var PENDING_EMAIL = "autodocs-auth-email-pending";
  var VAULT_PREFIX = "autodocs-ai-vault:";

  // ------------------------------------------------------------------ Texte
  var L = {
    de: {
      signIn: "Anmelden", account: "Konto", close: "Schließen",
      heroTitle: "Diskutiere die Spezifikation mit KI",
      heroLead: "Frag nach Zusammenhängen, prüfe Abhängigkeiten und schlag Verbesserungen vor – direkt neben dem Text.", reqView: "Anfragestatus ansehen", reqAgain: "Neu anfragen", reqUpdate: "Begründung speichern", reqUpdated: "Begründung gespeichert.", icoKeyOk: "Eigener Schlüssel funktioniert", icoKeyBad: "Eigener Schlüssel abgelehnt", icoGiftOpen: "Projektkontingent bewilligt", icoGiftPending: "Projektkontingent angefragt", icoGiftBad: "Projektkontingent abgelehnt oder abgelaufen", icoLocalOk: "Lokale KI verfügbar", icoLocalBad: "Keine lokale KI verfügbar", noAccessHint: "Kein KI-Zugang. Hier einrichten.", answeredBy: "Geantwortet von", icoKeyPart: "Eigene Schlüssel teilweise abgelehnt", localProbe: "Lokal prüfen", localFoundAway: "Lokaler Server unter %s gefunden.", localOpen: "Seite dort öffnen", localNotFound: "Unter %s antwortet kein lokaler Server.", secByok: "Eigene Schlüssel (BYOK)", storeLocal: "im Browser-Speicher dieser Website gespeichert", storeSession: "nur für diese Sitzung gespeichert", stNoKeys: "Noch kein eigener Schlüssel.", secLocal: "Lokale KI-CLIs (localhost)", localNoServer: "Kein lokaler Server erreichbar. Starte _src/serve.py.", localOnlyLocal: "Nur verfügbar, wenn die Seite lokal über _src/serve.py läuft.", back: "Zurück", tabStatus: "Status", tabAdd: "BYOK hinzufügen", stSources: "Deine KI-Zugänge für Diskussionen", stKeyFailed: "zuletzt abgelehnt", stWorks: "funktioniert", stSignedVia: "Angemeldet mit %s", stNoSources: "Noch kein Zugang. Füge einen eigenen Schlüssel hinzu oder frag Kontingent an.", stLocalTitle: "Lokale KI", stProjExpired: "Projektkontingent abgelaufen am %s", hdrOk: "KI-Zugang funktioniert", hdrPartial: "KI-Zugang teilweise verfügbar", hdrNone: "kein funktionierender KI-Zugang", appleSetup: "Die Anmeldung mit Apple ist noch nicht eingerichtet.", stProjActive: "aktiv bis %s", stProjNone: "nicht angefragt", dlgTitle: "Dein KI-Zugang", tabByok: "BYOK", tabQuota: "Kontingent anfragen", stDiscuss: "Diskussionen", stBackend: "Backend-Aktionen", stBackendHint: "Kommentare generieren, Prompts ausführen", stAccount: "Anmeldung", stGithub: "GitHub (Kuration, Feedback)", stNone: "nicht verbunden", stSignedOut: "nicht angemeldet", stViaAction: "über die GitHub Action des Betreibers", stGhOn: "Token hinterlegt", stGhLater: "wird beim Absenden im Review-Paket verbunden", stProjUntil: "Projektkontingent bis %s", stProjPending: "Projektkontingent angefragt", recheck: "Prüfen", hdrKi: "KI", stViaMail: "E-Mail-Link", stLocal: "lokale CLI", apple: "Mit Apple fortfahren", admBilling: "Abrechnung", admBillVia: "Projektkontingent läuft über", admAcc1: "Konto 1", admAcc2: "Konto 2", admAcc12: "Konto 1, bei Bedarf Konto 2", admOpenai: "OpenAI-Modelle anbieten", admName: "Name", admSave: "Speichern", admBillHint: "Gilt ab der nächsten Anfrage (nach höchstens 30 Sekunden).", projDenied: "Keine gültige Freigabe für das Projektkontingent.", admD90: "90 Tage", admD30: "30 Tage", admD7: "1 Woche", admD1: "1 Tag", admExpired: "abgelaufen %s", admUntil: "bis %s", admDuration: "Freischalten für", projLabel: "Projektkontingent · Nexos", reqExpired: "Deine Freigabe ist am %s abgelaufen.", github: "Mit GitHub fortfahren", reqLink: "Kein eigener Schlüssel? Projektkontingent anfragen", reqTitle: "Projektkontingent anfragen", reqLead: "Du hast keinen eigenen Schlüssel? Bitte den Betreiber, dich für eine bestimmte Zeit für das Projektkontingent freizuschalten. Die Anfragen laufen dann über das Projekt; dein Browser sieht keinen Schlüssel.", reqReason: "Wofür brauchst du es?", reqReasonPh: "Zum Beispiel: Ich prüfe die COM-Anforderungen für unser Steuergerät.", reqSend: "Anfrage senden", reqPending: "Deine Anfrage vom %s wartet auf Freigabe.", reqWithdraw: "Anfrage zurückziehen", reqRejected: "Deine Anfrage wurde abgelehnt.", reqGranted: "Freigeschaltet bis %s.", reqSignIn: "Melde dich an, damit die Freigabe dir zugeordnet werden kann.", reqDone: "Anfrage gesendet.", grantedToast: "Projektkontingent freigeschaltet.", viaProject: "Projektkontingent", adm: "Verwaltung", admTitle: "Anfragen zum Projektkontingent", admNone: "Keine offenen Anfragen.", admModel: "Modell (optional)", admNote: "Notiz an die Person (optional)", admGrant: "Freischalten", admReject: "Ablehnen", admGrants: "Freigeschaltet", admRevoke: "Entziehen", admRevokeHint: "Wirkt sofort: Der Dienst prüft die Freigabe bei jeder Anfrage.", admDone: "Gespeichert.", provPick: "Von welchem Anbieter ist der Schlüssel?", orSignIn: "Oder anmelden", signInRequired: "Zusätzlich anmelden", optSignIn: "Optional: mit Konto anmelden", welcomeByok: "Danach verbindest du deinen eigenen API-Schlüssel eines KI-Anbieters.", headerConnect: "KI verbinden", geminiNote: "Im kostenlosen Kontingent darf Google deine Eingaben zur Verbesserung seiner Produkte verwenden. Für vertrauliche Inhalte einen Schlüssel mit Abrechnung nutzen.", byokLead: "Dafür bringst du einen eigenen API-Schlüssel eines KI-Anbieters mit. Den Verbrauch rechnet der Anbieter direkt mit dir ab.",
      b1t: "Dein Schlüssel", b1: "Er bleibt in diesem Browser und geht nur direkt an den Anbieter, nie an uns.",
      b2t: "Deine Kosten", b2: "Du zahlst nur, was du beim Anbieter verbrauchst. Gemini bietet ein begrenztes kostenloses Kontingent.",
      b3t: "Wirksam", b3: "Gute Vorschläge landen mit einem Klick bei den Kuratoren.",
      google: "Mit Google fortfahren", orMail: "oder mit E-Mail-Link",
      mailPh: "name@beispiel.de", sendLink: "Link senden",
      fine: "Kein Passwort nötig. Für die Anmeldung speichern wir nur deine E-Mail-Adresse.",
      setup: "Die Anmeldung wird gerade eingerichtet.",
      localSkip: "Ohne Anmeldung weiter",
      sentTitle: "Schau in dein Postfach",
      sentLead: "Wir haben dir einen Anmeldelink an %s geschickt. Klick ihn an – du landest wieder hier und bist angemeldet.",
      otherDevice: "Mail auf einem anderen Gerät geöffnet?",
      pasteLead: "Kopiere den Link aus der Mail und füge ihn hier ein:",
      pastePh: "https://…", pasteGo: "Anmelden",
      resend: "Erneut senden", otherMail: "Andere Adresse", noMail: "Nichts angekommen? Schau auch im Spam-Ordner nach.",
      resent: "Link erneut gesendet.",
      confirmTitle: "Fast geschafft",
      confirmLead: "Bitte bestätige die E-Mail-Adresse, an die der Link ging.",
      confirmGo: "Bestätigen",
      welcome: "Willkommen, %s!", welcomeAnon: "Willkommen!",
      connectLead: "Noch ein Schritt: Verbinde ein KI-Modell. Dein Schlüssel bleibt in diesem Browser.",
      recommended: "Empfohlen", freeKey: "kostenloses Kontingent",
      keyLabel: "API-Schlüssel", keyCreate: "Schlüssel erstellen", show: "Anzeigen", hide: "Verbergen",
      remember: "Auf diesem Gerät merken", connect: "Verbinden",
      checking: "Schlüssel wird geprüft…", keyOk: "Verbunden – %n Modelle verfügbar.",
      keyNoList: "Schlüssel gespeichert. Die Modellliste ist bei diesem Anbieter nicht abrufbar; trag die Modell-ID unten ein.",
      keyBad: "Der Anbieter hat den Schlüssel abgelehnt.", keyNet: "Der Anbieter ist gerade nicht erreichbar.",
      local: "Lokale KI-CLIs", localFound: "Auf diesem Rechner gefunden:", useThis: "Verwenden",
      activeModel: "Aktives Modell", modelId: "Modell-ID", providers: "Verbundene Anbieter",
      addProvider: "Weiteren Anbieter verbinden", remove: "Entfernen", signOut: "Abmelden", session: "Sitzung",
      storeNote: "Schlüssel liegen im Browser-Speicher dieser Website. Auf gemeinsam genutzten Rechnern „merken“ abwählen.",
      viaKey: "eigener Schlüssel", viaLocal: "lokal",
      chipSignIn: "Anmelden für KI-Diskussion", chipConnect: "KI-Modell verbinden", chipSetup: "KI-Diskussion bald verfügbar",
      gateSignIn: "Melde dich kurz an, um mit der KI zu diskutieren – kostenlos, mit Google oder per E-Mail-Link.",
      gateKey: "Für die KI-Diskussion brauchst du einen eigenen API-Schlüssel, zum Beispiel von Google AI Studio, Anthropic oder OpenAI.",
      gateSetup: "Die KI-Diskussion ist auf der öffentlichen Seite bald verfügbar. Lokal mit _src/serve.py geht sie schon.",
      gateBtnSignIn: "Anmelden", gateBtnKey: "Modell verbinden",
      errMail: "Bitte gib eine gültige E-Mail-Adresse ein.",
      errDomain: "Diese Adresse ist für die Anmeldung noch nicht freigeschaltet.",
      errLink: "Der Link ist abgelaufen oder wurde schon benutzt. Fordere einfach einen neuen an.",
      errNet: "Keine Verbindung. Bitte versuch es gleich noch einmal.",
      errOff: "Diese Anmeldeart ist noch nicht aktiviert.",
      errGeneric: "Das hat nicht geklappt: %s",
      signedIn: "Angemeldet als %s.", signedOut: "Abgemeldet.",
      issueClip: "Der Vorschlag ist lang und liegt in der Zwischenablage – füge ihn im geöffneten GitHub-Formular ein.",
      issueOpened: "GitHub-Formular geöffnet. Mit „Submit new issue“ geht der Vorschlag an die Kuratoren.",
      pasteHere: "<!-- Inhalt aus der Zwischenablage hier einfügen -->"
    },
    en: {
      signIn: "Sign in", account: "Account", close: "Close",
      heroTitle: "Discuss the specification with AI",
      heroLead: "Ask about relationships, check dependencies and suggest improvements – right next to the text.", reqView: "View request status", reqAgain: "Request again", reqUpdate: "Save reason", reqUpdated: "Reason saved.", icoKeyOk: "Own key works", icoKeyBad: "Own key rejected", icoGiftOpen: "Project quota approved", icoGiftPending: "Project quota requested", icoGiftBad: "Project quota declined or expired", icoLocalOk: "Local AI available", icoLocalBad: "No local AI available", noAccessHint: "No AI access. Set it up here.", answeredBy: "Answer from", icoKeyPart: "Some own keys rejected", localProbe: "Check locally", localFoundAway: "Local server found at %s.", localOpen: "Open the page there", localNotFound: "No local server answers at %s.", secByok: "Own keys (BYOK)", storeLocal: "stored in this website's browser storage", storeSession: "stored for this session only", stNoKeys: "No key of your own yet.", secLocal: "Local AI CLIs (localhost)", localNoServer: "No local server reachable. Start _src/serve.py.", localOnlyLocal: "Only available when the page runs locally via _src/serve.py.", back: "Back", tabStatus: "Status", tabAdd: "Add BYOK", stSources: "Your AI access for discussions", stKeyFailed: "last rejected", stWorks: "works", stSignedVia: "Signed in with %s", stNoSources: "No access yet. Add your own key or request quota.", stLocalTitle: "Local AI", stProjExpired: "Project quota expired on %s", hdrOk: "AI access works", hdrPartial: "AI access partly available", hdrNone: "no working AI access", appleSetup: "Sign-in with Apple is not set up yet.", stProjActive: "active until %s", stProjNone: "not requested", dlgTitle: "Your AI access", tabByok: "BYOK", tabQuota: "Request quota", stDiscuss: "Discussions", stBackend: "Backend actions", stBackendHint: "generate commentary, run prompts", stAccount: "Sign-in", stGithub: "GitHub (curation, feedback)", stNone: "not connected", stSignedOut: "not signed in", stViaAction: "through the operator's GitHub Action", stGhOn: "token stored", stGhLater: "connected when you submit the review package", stProjUntil: "Project quota until %s", stProjPending: "Project quota requested", recheck: "Check", hdrKi: "AI", stViaMail: "email link", stLocal: "local CLI", apple: "Continue with Apple", admBilling: "Billing", admBillVia: "Project quota runs through", admAcc1: "Account 1", admAcc2: "Account 2", admAcc12: "Account 1, account 2 if needed", admOpenai: "Offer OpenAI models", admName: "Name", admSave: "Save", admBillHint: "Applies from the next request (within 30 seconds).", projDenied: "No valid access to the project quota.", admD90: "90 days", admD30: "30 days", admD7: "1 week", admD1: "1 day", admExpired: "expired %s", admUntil: "until %s", admDuration: "Enable for", projLabel: "Project quota · Nexos", reqExpired: "Your access expired on %s.", github: "Continue with GitHub", reqLink: "No key of your own? Request project quota", reqTitle: "Request project quota", reqLead: "No key of your own? Ask the operator to enable you for the project quota for a limited time. Requests then run through the project; your browser never sees a key.", reqReason: "What do you need it for?", reqReasonPh: "For example: I am reviewing the COM requirements for our ECU.", reqSend: "Send request", reqPending: "Your request from %s is waiting for approval.", reqWithdraw: "Withdraw request", reqRejected: "Your request was declined.", reqGranted: "Enabled until %s.", reqSignIn: "Sign in so the approval can be assigned to you.", reqDone: "Request sent.", grantedToast: "Project quota enabled.", viaProject: "project quota", adm: "Admin", admTitle: "Project quota requests", admNone: "No open requests.", admModel: "Model (optional)", admNote: "Note to the person (optional)", admGrant: "Enable", admReject: "Decline", admGrants: "Enabled", admRevoke: "Revoke", admRevokeHint: "Takes effect immediately: the service checks access on every request.", admDone: "Saved.", provPick: "Which provider is the key from?", orSignIn: "Or sign in", signInRequired: "Also sign in", optSignIn: "Optional: sign in with an account", welcomeByok: "Next you connect your own API key from an AI provider.", headerConnect: "Connect AI", geminiNote: "In the free tier, Google may use your inputs to improve its products. For confidential content, use a key with billing enabled.", byokLead: "For this you bring your own API key from an AI provider. The provider bills your usage directly.",
      b1t: "Your key", b1: "It stays in this browser and only goes directly to the provider, never to us.",
      b2t: "Your costs", b2: "You only pay what you use with the provider. Gemini offers a limited free tier.",
      b3t: "Effective", b3: "Good suggestions reach the curators with one click.",
      google: "Continue with Google", orMail: "or with an email link",
      mailPh: "name@example.com", sendLink: "Send link",
      fine: "No password needed. For sign-in we only store your email address.",
      setup: "Sign-in is being set up.",
      localSkip: "Continue without signing in",
      sentTitle: "Check your inbox",
      sentLead: "We sent a sign-in link to %s. Click it – you will land back here, signed in.",
      otherDevice: "Opened the email on another device?",
      pasteLead: "Copy the link from the email and paste it here:",
      pastePh: "https://…", pasteGo: "Sign in",
      resend: "Send again", otherMail: "Use another address", noMail: "Nothing arrived? Check your spam folder too.",
      resent: "Link sent again.",
      confirmTitle: "Almost there",
      confirmLead: "Please confirm the email address the link was sent to.",
      confirmGo: "Confirm",
      welcome: "Welcome, %s!", welcomeAnon: "Welcome!",
      connectLead: "One more step: connect an AI model. Your key stays in this browser.",
      recommended: "Recommended", freeKey: "free tier",
      keyLabel: "API key", keyCreate: "Create a key", show: "Show", hide: "Hide",
      remember: "Remember on this device", connect: "Connect",
      checking: "Checking key…", keyOk: "Connected – %n models available.",
      keyNoList: "Key saved. This provider does not list its models; enter the model ID below.",
      keyBad: "The provider rejected the key.", keyNet: "The provider cannot be reached right now.",
      local: "Local AI CLIs", localFound: "Found on this machine:", useThis: "Use",
      activeModel: "Active model", modelId: "Model ID", providers: "Connected providers",
      addProvider: "Connect another provider", remove: "Remove", signOut: "Sign out", session: "session",
      storeNote: "Keys are kept in this website's browser storage. On shared computers, untick “remember”.",
      viaKey: "own key", viaLocal: "local",
      chipSignIn: "Sign in for AI discussion", chipConnect: "Connect an AI model", chipSetup: "AI discussion coming soon",
      gateSignIn: "Sign in to discuss with the AI – free, with Google or an email link.",
      gateKey: "The AI discussion needs your own API key, for example from Google AI Studio, Anthropic or OpenAI.",
      gateSetup: "The AI discussion is coming soon on the public site. It already works locally with _src/serve.py.",
      gateBtnSignIn: "Sign in", gateBtnKey: "Connect a model",
      errMail: "Please enter a valid email address.",
      errDomain: "This address is not yet enabled for sign-in.",
      errLink: "The link has expired or was already used. Just request a new one.",
      errNet: "No connection. Please try again in a moment.",
      errOff: "This sign-in method is not enabled yet.",
      errGeneric: "That did not work: %s",
      signedIn: "Signed in as %s.", signedOut: "Signed out.",
      issueClip: "The suggestion is long and is on your clipboard – paste it into the GitHub form that just opened.",
      issueOpened: "GitHub form opened. “Submit new issue” sends the suggestion to the curators.",
      pasteHere: "<!-- Paste the content from your clipboard here -->"
    },
    es: {
      signIn: "Iniciar sesión", account: "Cuenta", close: "Cerrar",
      heroTitle: "Debate la especificación con IA",
      heroLead: "Pregunta por relaciones, revisa dependencias y propone mejoras, justo al lado del texto.", reqView: "Ver estado de la solicitud", reqAgain: "Solicitar de nuevo", reqUpdate: "Guardar motivo", reqUpdated: "Motivo guardado.", icoKeyOk: "La clave propia funciona", icoKeyBad: "Clave propia rechazada", icoGiftOpen: "Cuota del proyecto aprobada", icoGiftPending: "Cuota del proyecto solicitada", icoGiftBad: "Cuota del proyecto rechazada o caducada", icoLocalOk: "IA local disponible", icoLocalBad: "No hay IA local disponible", noAccessHint: "Sin acceso a la IA. Configúralo aquí.", answeredBy: "Respuesta de", icoKeyPart: "Algunas claves propias rechazadas", localProbe: "Comprobar en local", localFoundAway: "Servidor local encontrado en %s.", localOpen: "Abrir la página allí", localNotFound: "Ningún servidor local responde en %s.", secByok: "Claves propias (BYOK)", storeLocal: "guardada en el almacenamiento del navegador de este sitio", storeSession: "guardada solo para esta sesión", stNoKeys: "Aún no hay clave propia.", secLocal: "CLI de IA locales (localhost)", localNoServer: "No hay servidor local accesible. Inicia _src/serve.py.", localOnlyLocal: "Solo disponible si la página se ejecuta localmente con _src/serve.py.", back: "Volver", tabStatus: "Estado", tabAdd: "Añadir BYOK", stSources: "Tus accesos de IA para debates", stKeyFailed: "rechazada la última vez", stWorks: "funciona", stSignedVia: "Sesión iniciada con %s", stNoSources: "Aún no hay acceso. Añade tu propia clave o solicita cuota.", stLocalTitle: "IA local", stProjExpired: "La cuota del proyecto caducó el %s", hdrOk: "El acceso a la IA funciona", hdrPartial: "Acceso a la IA disponible en parte", hdrNone: "ningún acceso a la IA funciona", appleSetup: "El inicio de sesión con Apple aún no está configurado.", stProjActive: "activa hasta el %s", stProjNone: "no solicitada", dlgTitle: "Tu acceso a la IA", tabByok: "BYOK", tabQuota: "Solicitar cuota", stDiscuss: "Debates", stBackend: "Acciones de backend", stBackendHint: "generar comentarios, ejecutar prompts", stAccount: "Inicio de sesión", stGithub: "GitHub (curación, comentarios)", stNone: "no conectado", stSignedOut: "sin iniciar sesión", stViaAction: "mediante la GitHub Action del responsable", stGhOn: "token guardado", stGhLater: "se conecta al enviar el paquete de revisión", stProjUntil: "Cuota del proyecto hasta el %s", stProjPending: "Cuota del proyecto solicitada", recheck: "Comprobar", hdrKi: "IA", stViaMail: "enlace por correo", stLocal: "CLI local", apple: "Continuar con Apple", projDenied: "No tienes acceso válido a la cuota del proyecto.", projLabel: "Cuota del proyecto · Nexos", reqExpired: "Tu acceso caducó el %s.", github: "Continuar con GitHub", reqLink: "¿No tienes clave propia? Solicitar cuota del proyecto", reqTitle: "Solicitar cuota del proyecto", reqLead: "¿No tienes clave propia? Pide al responsable que te habilite la cuota del proyecto durante un tiempo. Las solicitudes pasan entonces por el proyecto; tu navegador nunca ve una clave.", reqReason: "¿Para qué la necesitas?", reqReasonPh: "Por ejemplo: reviso los requisitos de COM para nuestra ECU.", reqSend: "Enviar solicitud", reqPending: "Tu solicitud del %s está pendiente de aprobación.", reqWithdraw: "Retirar solicitud", reqRejected: "Tu solicitud fue rechazada.", reqGranted: "Habilitado hasta el %s.", reqSignIn: "Inicia sesión para que la aprobación se te pueda asignar.", reqDone: "Solicitud enviada.", grantedToast: "Cuota del proyecto habilitada.", viaProject: "cuota del proyecto", provPick: "¿De qué proveedor es la clave?", orSignIn: "O inicia sesión", signInRequired: "Inicia sesión también", optSignIn: "Opcional: iniciar sesión con una cuenta", welcomeByok: "Después conectas tu propia clave de API de un proveedor de IA.", headerConnect: "Conectar IA", geminiNote: "En el nivel gratuito, Google puede usar tus entradas para mejorar sus productos. Para contenido confidencial, usa una clave con facturación.", byokLead: "Para ello aportas tu propia clave de API de un proveedor de IA. El proveedor te factura el consumo directamente.",
      b1t: "Tu clave", b1: "Se queda en este navegador y solo va directamente al proveedor, nunca a nosotros.",
      b2t: "Tus costes", b2: "Solo pagas lo que consumes con el proveedor. Gemini ofrece un nivel gratuito limitado.",
      b3t: "Útil", b3: "Las buenas propuestas llegan a los curadores con un clic.",
      google: "Continuar con Google", orMail: "o con un enlace por correo",
      mailPh: "nombre@ejemplo.com", sendLink: "Enviar enlace",
      fine: "Sin contraseña. Para iniciar sesión solo guardamos tu correo electrónico.",
      setup: "El inicio de sesión se está configurando.", localSkip: "Continuar sin iniciar sesión",
      sentTitle: "Revisa tu correo", sentLead: "Te hemos enviado un enlace de acceso a %s. Haz clic en él y volverás aquí con la sesión iniciada.",
      otherDevice: "¿Abriste el correo en otro dispositivo?", pasteLead: "Copia el enlace del correo y pégalo aquí:", pastePh: "https://…", pasteGo: "Iniciar sesión",
      resend: "Enviar de nuevo", otherMail: "Usar otra dirección", noMail: "¿No ha llegado nada? Revisa también la carpeta de spam.", resent: "Enlace enviado de nuevo.",
      confirmTitle: "Casi listo", confirmLead: "Confirma la dirección de correo a la que se envió el enlace.", confirmGo: "Confirmar",
      welcome: "¡Bienvenido/a, %s!", welcomeAnon: "¡Bienvenido/a!",
      connectLead: "Un paso más: conecta un modelo de IA. Tu clave se queda en este navegador.",
      recommended: "Recomendado", freeKey: "nivel gratuito", keyLabel: "Clave de API", keyCreate: "Crear una clave", show: "Mostrar", hide: "Ocultar",
      remember: "Recordar en este dispositivo", connect: "Conectar", checking: "Comprobando la clave…", keyOk: "Conectado: %n modelos disponibles.",
      keyNoList: "Clave guardada. Este proveedor no publica su lista de modelos; introduce el ID del modelo abajo.",
      keyBad: "El proveedor rechazó la clave.", keyNet: "No se puede contactar con el proveedor en este momento.",
      local: "CLI de IA locales", localFound: "Encontradas en este equipo:", useThis: "Usar",
      activeModel: "Modelo activo", modelId: "ID del modelo", providers: "Proveedores conectados", addProvider: "Conectar otro proveedor",
      remove: "Quitar", signOut: "Cerrar sesión", session: "sesión",
      storeNote: "Las claves se guardan en el almacenamiento del navegador de este sitio. En equipos compartidos, desmarca «recordar».",
      viaKey: "clave propia", viaLocal: "local",
      chipSignIn: "Inicia sesión para debatir con IA", chipConnect: "Conectar un modelo de IA", chipSetup: "Debate con IA próximamente",
      gateSignIn: "Inicia sesión para debatir con la IA: gratis, con Google o con un enlace por correo.",
      gateKey: "El debate con IA necesita tu propia clave de API, por ejemplo de Google AI Studio, Anthropic u OpenAI.",
      gateSetup: "El debate con IA llegará pronto al sitio público. En local, con _src/serve.py, ya funciona.",
      gateBtnSignIn: "Iniciar sesión", gateBtnKey: "Conectar un modelo",
      errMail: "Introduce una dirección de correo válida.", errDomain: "Esta dirección aún no está habilitada para iniciar sesión.",
      errLink: "El enlace ha caducado o ya se usó. Solicita uno nuevo.", errNet: "Sin conexión. Inténtalo de nuevo en un momento.",
      errOff: "Este método de inicio de sesión aún no está activado.", errGeneric: "No ha funcionado: %s",
      signedIn: "Sesión iniciada como %s.", signedOut: "Sesión cerrada.",
      issueClip: "La propuesta es larga y está en el portapapeles: pégala en el formulario de GitHub que se acaba de abrir.",
      issueOpened: "Formulario de GitHub abierto. «Submit new issue» envía la propuesta a los curadores.",
      pasteHere: "<!-- Pega aquí el contenido del portapapeles -->"
    },
    pt: {
      signIn: "Entrar", account: "Conta", close: "Fechar",
      heroTitle: "Discuta a especificação com IA",
      heroLead: "Pergunte sobre relações, verifique dependências e sugira melhorias, logo ao lado do texto.", reqView: "Ver status da solicitação", reqAgain: "Solicitar novamente", reqUpdate: "Salvar justificativa", reqUpdated: "Justificativa salva.", icoKeyOk: "A chave própria funciona", icoKeyBad: "Chave própria recusada", icoGiftOpen: "Cota do projeto aprovada", icoGiftPending: "Cota do projeto solicitada", icoGiftBad: "Cota do projeto recusada ou expirada", icoLocalOk: "IA local disponível", icoLocalBad: "Nenhuma IA local disponível", noAccessHint: "Sem acesso à IA. Configure aqui.", answeredBy: "Resposta de", icoKeyPart: "Algumas chaves próprias recusadas", localProbe: "Verificar localmente", localFoundAway: "Servidor local encontrado em %s.", localOpen: "Abrir a página lá", localNotFound: "Nenhum servidor local responde em %s.", secByok: "Chaves próprias (BYOK)", storeLocal: "salva no armazenamento do navegador deste site", storeSession: "salva apenas para esta sessão", stNoKeys: "Ainda sem chave própria.", secLocal: "CLIs de IA locais (localhost)", localNoServer: "Nenhum servidor local acessível. Inicie _src/serve.py.", localOnlyLocal: "Disponível só quando a página roda localmente via _src/serve.py.", back: "Voltar", tabStatus: "Status", tabAdd: "Adicionar BYOK", stSources: "Seus acessos de IA para discussões", stKeyFailed: "recusada da última vez", stWorks: "funciona", stSignedVia: "Conectado com %s", stNoSources: "Ainda sem acesso. Adicione sua própria chave ou solicite cota.", stLocalTitle: "IA local", stProjExpired: "A cota do projeto expirou em %s", hdrOk: "O acesso à IA funciona", hdrPartial: "Acesso à IA disponível em parte", hdrNone: "nenhum acesso à IA funcionando", appleSetup: "O login com a Apple ainda não está configurado.", stProjActive: "ativa até %s", stProjNone: "não solicitada", dlgTitle: "Seu acesso à IA", tabByok: "BYOK", tabQuota: "Solicitar cota", stDiscuss: "Discussões", stBackend: "Ações de backend", stBackendHint: "gerar comentários, executar prompts", stAccount: "Login", stGithub: "GitHub (curadoria, feedback)", stNone: "não conectado", stSignedOut: "não conectado", stViaAction: "pela GitHub Action do responsável", stGhOn: "token salvo", stGhLater: "conectado ao enviar o pacote de revisão", stProjUntil: "Cota do projeto até %s", stProjPending: "Cota do projeto solicitada", recheck: "Verificar", hdrKi: "IA", stViaMail: "link por e-mail", stLocal: "CLI local", apple: "Continuar com a Apple", projDenied: "Sem acesso válido à cota do projeto.", projLabel: "Cota do projeto · Nexos", reqExpired: "Seu acesso expirou em %s.", github: "Continuar com o GitHub", reqLink: "Sem chave própria? Solicitar cota do projeto", reqTitle: "Solicitar cota do projeto", reqLead: "Sem chave própria? Peça ao responsável para liberar a cota do projeto para você por um período. As solicitações passam pelo projeto; seu navegador nunca vê uma chave.", reqReason: "Para que você precisa?", reqReasonPh: "Por exemplo: estou revisando os requisitos de COM para a nossa ECU.", reqSend: "Enviar solicitação", reqPending: "Sua solicitação de %s aguarda aprovação.", reqWithdraw: "Retirar solicitação", reqRejected: "Sua solicitação foi recusada.", reqGranted: "Liberado até %s.", reqSignIn: "Entre para que a liberação possa ser atribuída a você.", reqDone: "Solicitação enviada.", grantedToast: "Cota do projeto liberada.", viaProject: "cota do projeto", provPick: "De qual provedor é a chave?", orSignIn: "Ou entre", signInRequired: "Entre também", optSignIn: "Opcional: entrar com uma conta", welcomeByok: "Em seguida você conecta sua própria chave de API de um provedor de IA.", headerConnect: "Conectar IA", geminiNote: "No nível gratuito, o Google pode usar suas entradas para melhorar os produtos dele. Para conteúdo confidencial, use uma chave com faturamento.", byokLead: "Para isso você traz sua própria chave de API de um provedor de IA. O provedor cobra o uso diretamente de você.",
      b1t: "Sua chave", b1: "Ela fica neste navegador e vai apenas diretamente ao provedor, nunca para nós.",
      b2t: "Seus custos", b2: "Você paga só o que usar no provedor. O Gemini oferece um nível gratuito limitado.",
      b3t: "Eficaz", b3: "Boas sugestões chegam aos curadores com um clique.",
      google: "Continuar com o Google", orMail: "ou com um link por e-mail",
      mailPh: "nome@exemplo.com", sendLink: "Enviar link",
      fine: "Sem senha. Para o login guardamos apenas seu endereço de e-mail.",
      setup: "O login está sendo configurado.", localSkip: "Continuar sem login",
      sentTitle: "Confira sua caixa de entrada", sentLead: "Enviamos um link de acesso para %s. Clique nele e você voltará aqui já conectado.",
      otherDevice: "Abriu o e-mail em outro dispositivo?", pasteLead: "Copie o link do e-mail e cole aqui:", pastePh: "https://…", pasteGo: "Entrar",
      resend: "Enviar novamente", otherMail: "Usar outro endereço", noMail: "Nada chegou? Verifique também a pasta de spam.", resent: "Link enviado novamente.",
      confirmTitle: "Quase lá", confirmLead: "Confirme o endereço de e-mail para o qual o link foi enviado.", confirmGo: "Confirmar",
      welcome: "Boas-vindas, %s!", welcomeAnon: "Boas-vindas!",
      connectLead: "Só mais um passo: conecte um modelo de IA. Sua chave fica neste navegador.",
      recommended: "Recomendado", freeKey: "nível gratuito", keyLabel: "Chave de API", keyCreate: "Criar uma chave", show: "Mostrar", hide: "Ocultar",
      remember: "Lembrar neste dispositivo", connect: "Conectar", checking: "Verificando a chave…", keyOk: "Conectado – %n modelos disponíveis.",
      keyNoList: "Chave salva. Este provedor não lista seus modelos; informe o ID do modelo abaixo.",
      keyBad: "O provedor recusou a chave.", keyNet: "O provedor não está acessível no momento.",
      local: "CLIs de IA locais", localFound: "Encontradas nesta máquina:", useThis: "Usar",
      activeModel: "Modelo ativo", modelId: "ID do modelo", providers: "Provedores conectados", addProvider: "Conectar outro provedor",
      remove: "Remover", signOut: "Sair", session: "sessão",
      storeNote: "As chaves ficam no armazenamento do navegador deste site. Em computadores compartilhados, desmarque “lembrar”.",
      viaKey: "chave própria", viaLocal: "local",
      chipSignIn: "Entre para discutir com IA", chipConnect: "Conectar um modelo de IA", chipSetup: "Discussão com IA em breve",
      gateSignIn: "Entre para discutir com a IA – grátis, com Google ou com um link por e-mail.",
      gateKey: "A discussão com IA precisa da sua própria chave de API, por exemplo do Google AI Studio, da Anthropic ou da OpenAI.",
      gateSetup: "A discussão com IA chega em breve ao site público. Localmente, com _src/serve.py, já funciona.",
      gateBtnSignIn: "Entrar", gateBtnKey: "Conectar um modelo",
      errMail: "Informe um endereço de e-mail válido.", errDomain: "Este endereço ainda não está liberado para login.",
      errLink: "O link expirou ou já foi usado. Basta pedir um novo.", errNet: "Sem conexão. Tente de novo em instantes.",
      errOff: "Este método de login ainda não está ativado.", errGeneric: "Não funcionou: %s",
      signedIn: "Conectado como %s.", signedOut: "Você saiu.",
      issueClip: "A sugestão é longa e está na área de transferência – cole-a no formulário do GitHub que acabou de abrir.",
      issueOpened: "Formulário do GitHub aberto. “Submit new issue” envia a sugestão aos curadores.",
      pasteHere: "<!-- Cole aqui o conteúdo da área de transferência -->"
    },
    fr: {
      signIn: "Se connecter", account: "Compte", close: "Fermer",
      heroTitle: "Discutez de la spécification avec l'IA",
      heroLead: "Interrogez les liens, vérifiez les dépendances et proposez des améliorations, juste à côté du texte.", reqView: "Voir l'état de la demande", reqAgain: "Demander à nouveau", reqUpdate: "Enregistrer la justification", reqUpdated: "Justification enregistrée.", icoKeyOk: "La clé personnelle fonctionne", icoKeyBad: "Clé personnelle refusée", icoGiftOpen: "Quota du projet accordé", icoGiftPending: "Quota du projet demandé", icoGiftBad: "Quota du projet refusé ou expiré", icoLocalOk: "IA locale disponible", icoLocalBad: "Aucune IA locale disponible", noAccessHint: "Pas d'accès à l'IA. Configurez-le ici.", answeredBy: "Réponse de", icoKeyPart: "Certaines clés personnelles refusées", localProbe: "Vérifier en local", localFoundAway: "Serveur local trouvé à %s.", localOpen: "Ouvrir la page là-bas", localNotFound: "Aucun serveur local ne répond à %s.", secByok: "Clés personnelles (BYOK)", storeLocal: "enregistrée dans le stockage du navigateur de ce site", storeSession: "enregistrée pour cette session uniquement", stNoKeys: "Pas encore de clé personnelle.", secLocal: "CLI d'IA locales (localhost)", localNoServer: "Aucun serveur local joignable. Lancez _src/serve.py.", localOnlyLocal: "Disponible uniquement si la page tourne en local via _src/serve.py.", back: "Retour", tabStatus: "Statut", tabAdd: "Ajouter BYOK", stSources: "Vos accès IA pour les discussions", stKeyFailed: "refusée la dernière fois", stWorks: "fonctionne", stSignedVia: "Connecté avec %s", stNoSources: "Pas encore d'accès. Ajoutez votre propre clé ou demandez un quota.", stLocalTitle: "IA locale", stProjExpired: "Quota du projet expiré le %s", hdrOk: "L'accès à l'IA fonctionne", hdrPartial: "Accès à l'IA partiellement disponible", hdrNone: "aucun accès à l'IA ne fonctionne", appleSetup: "La connexion avec Apple n'est pas encore configurée.", stProjActive: "actif jusqu'au %s", stProjNone: "non demandé", dlgTitle: "Votre accès à l'IA", tabByok: "BYOK", tabQuota: "Demander un quota", stDiscuss: "Discussions", stBackend: "Actions backend", stBackendHint: "générer des commentaires, exécuter des prompts", stAccount: "Connexion", stGithub: "GitHub (curation, retours)", stNone: "non connecté", stSignedOut: "non connecté", stViaAction: "via la GitHub Action du responsable", stGhOn: "jeton enregistré", stGhLater: "connecté lors de l'envoi du lot de revue", stProjUntil: "Quota du projet jusqu'au %s", stProjPending: "Quota du projet demandé", recheck: "Vérifier", hdrKi: "IA", stViaMail: "lien par e-mail", stLocal: "CLI locale", apple: "Continuer avec Apple", projDenied: "Aucun accès valide au quota du projet.", projLabel: "Quota du projet · Nexos", reqExpired: "Votre accès a expiré le %s.", github: "Continuer avec GitHub", reqLink: "Pas de clé personnelle ? Demander un quota du projet", reqTitle: "Demander un quota du projet", reqLead: "Pas de clé personnelle ? Demandez au responsable de vous ouvrir le quota du projet pour une durée limitée. Les requêtes passent alors par le projet ; votre navigateur ne voit jamais de clé.", reqReason: "Pour quoi en avez-vous besoin ?", reqReasonPh: "Par exemple : je vérifie les exigences COM pour notre calculateur.", reqSend: "Envoyer la demande", reqPending: "Votre demande du %s attend une validation.", reqWithdraw: "Retirer la demande", reqRejected: "Votre demande a été refusée.", reqGranted: "Activé jusqu'au %s.", reqSignIn: "Connectez-vous pour que l'autorisation puisse vous être attribuée.", reqDone: "Demande envoyée.", grantedToast: "Quota du projet activé.", viaProject: "quota du projet", provPick: "De quel fournisseur vient la clé ?", orSignIn: "Ou connectez-vous", signInRequired: "Connectez-vous aussi", optSignIn: "Facultatif : se connecter avec un compte", welcomeByok: "Ensuite, vous connectez votre propre clé d'API d'un fournisseur d'IA.", headerConnect: "Connecter l'IA", geminiNote: "Dans le niveau gratuit, Google peut utiliser vos saisies pour améliorer ses produits. Pour un contenu confidentiel, utilisez une clé avec facturation.", byokLead: "Pour cela, vous apportez votre propre clé d'API d'un fournisseur d'IA. Le fournisseur vous facture directement l'utilisation.",
      b1t: "Votre clé", b1: "Elle reste dans ce navigateur et va uniquement directement au fournisseur, jamais à nous.",
      b2t: "Vos coûts", b2: "Vous ne payez que ce que vous consommez chez le fournisseur. Gemini propose un niveau gratuit limité.",
      b3t: "Efficace", b3: "Les bonnes propositions parviennent aux curateurs en un clic.",
      google: "Continuer avec Google", orMail: "ou avec un lien par e-mail",
      mailPh: "nom@exemple.fr", sendLink: "Envoyer le lien",
      fine: "Aucun mot de passe. Pour la connexion, nous n'enregistrons que votre adresse e-mail.",
      setup: "La connexion est en cours de mise en place.", localSkip: "Continuer sans connexion",
      sentTitle: "Consultez votre boîte de réception", sentLead: "Nous avons envoyé un lien de connexion à %s. Cliquez dessus : vous reviendrez ici, connecté.",
      otherDevice: "E-mail ouvert sur un autre appareil ?", pasteLead: "Copiez le lien de l'e-mail et collez-le ici :", pastePh: "https://…", pasteGo: "Se connecter",
      resend: "Renvoyer", otherMail: "Utiliser une autre adresse", noMail: "Rien reçu ? Vérifiez aussi le dossier spam.", resent: "Lien renvoyé.",
      confirmTitle: "Presque terminé", confirmLead: "Confirmez l'adresse e-mail à laquelle le lien a été envoyé.", confirmGo: "Confirmer",
      welcome: "Bienvenue, %s !", welcomeAnon: "Bienvenue !",
      connectLead: "Encore une étape : connectez un modèle d'IA. Votre clé reste dans ce navigateur.",
      recommended: "Recommandé", freeKey: "niveau gratuit", keyLabel: "Clé d'API", keyCreate: "Créer une clé", show: "Afficher", hide: "Masquer",
      remember: "Mémoriser sur cet appareil", connect: "Connecter", checking: "Vérification de la clé…", keyOk: "Connecté – %n modèles disponibles.",
      keyNoList: "Clé enregistrée. Ce fournisseur ne liste pas ses modèles ; saisissez l'identifiant du modèle ci-dessous.",
      keyBad: "Le fournisseur a refusé la clé.", keyNet: "Le fournisseur est injoignable pour le moment.",
      local: "CLI d'IA locales", localFound: "Trouvées sur cette machine :", useThis: "Utiliser",
      activeModel: "Modèle actif", modelId: "Identifiant du modèle", providers: "Fournisseurs connectés", addProvider: "Connecter un autre fournisseur",
      remove: "Retirer", signOut: "Se déconnecter", session: "session",
      storeNote: "Les clés sont conservées dans le stockage du navigateur pour ce site. Sur un ordinateur partagé, décochez « mémoriser ».",
      viaKey: "clé personnelle", viaLocal: "local",
      chipSignIn: "Se connecter pour discuter avec l'IA", chipConnect: "Connecter un modèle d'IA", chipSetup: "Discussion IA bientôt disponible",
      gateSignIn: "Connectez-vous pour discuter avec l'IA – gratuit, avec Google ou un lien par e-mail.",
      gateKey: "La discussion avec l'IA nécessite votre propre clé d'API, par exemple de Google AI Studio, Anthropic ou OpenAI.",
      gateSetup: "La discussion avec l'IA arrive bientôt sur le site public. En local avec _src/serve.py, elle fonctionne déjà.",
      gateBtnSignIn: "Se connecter", gateBtnKey: "Connecter un modèle",
      errMail: "Veuillez saisir une adresse e-mail valide.", errDomain: "Cette adresse n'est pas encore autorisée pour la connexion.",
      errLink: "Le lien a expiré ou a déjà été utilisé. Demandez-en simplement un nouveau.", errNet: "Pas de connexion. Réessayez dans un instant.",
      errOff: "Ce mode de connexion n'est pas encore activé.", errGeneric: "Cela n'a pas fonctionné : %s",
      signedIn: "Connecté en tant que %s.", signedOut: "Déconnecté.",
      issueClip: "La proposition est longue et se trouve dans le presse-papiers – collez-la dans le formulaire GitHub qui vient de s'ouvrir.",
      issueOpened: "Formulaire GitHub ouvert. « Submit new issue » transmet la proposition aux curateurs.",
      pasteHere: "<!-- Collez ici le contenu du presse-papiers -->"
    },
    ru: {
      signIn: "Войти", account: "Аккаунт", close: "Закрыть",
      heroTitle: "Обсуждайте спецификацию с ИИ",
      heroLead: "Спрашивайте о связях, проверяйте зависимости и предлагайте улучшения прямо рядом с текстом.", reqView: "Статус запроса", reqAgain: "Запросить снова", reqUpdate: "Сохранить обоснование", reqUpdated: "Обоснование сохранено.", icoKeyOk: "Собственный ключ работает", icoKeyBad: "Собственный ключ отклонён", icoGiftOpen: "Квота проекта одобрена", icoGiftPending: "Квота проекта запрошена", icoGiftBad: "Квота проекта отклонена или истекла", icoLocalOk: "Локальный ИИ доступен", icoLocalBad: "Локальный ИИ недоступен", noAccessHint: "Нет доступа к ИИ. Настройте здесь.", answeredBy: "Ответ от", icoKeyPart: "Часть собственных ключей отклонена", localProbe: "Проверить локально", localFoundAway: "Локальный сервер найден: %s.", localOpen: "Открыть страницу там", localNotFound: "По адресу %s локальный сервер не отвечает.", secByok: "Собственные ключи (BYOK)", storeLocal: "хранится в хранилище браузера этого сайта", storeSession: "хранится только для этого сеанса", stNoKeys: "Собственного ключа пока нет.", secLocal: "Локальные CLI для ИИ (localhost)", localNoServer: "Локальный сервер недоступен. Запустите _src/serve.py.", localOnlyLocal: "Доступно, только если страница запущена локально через _src/serve.py.", back: "Назад", tabStatus: "Статус", tabAdd: "Добавить BYOK", stSources: "Ваши доступы к ИИ для обсуждений", stKeyFailed: "в последний раз отклонён", stWorks: "работает", stSignedVia: "Вход через %s", stNoSources: "Доступа пока нет. Добавьте свой ключ или запросите квоту.", stLocalTitle: "Локальный ИИ", stProjExpired: "Квота проекта истекла %s", hdrOk: "Доступ к ИИ работает", hdrPartial: "Доступ к ИИ частично доступен", hdrNone: "нет работающего доступа к ИИ", appleSetup: "Вход через Apple ещё не настроен.", stProjActive: "активна до %s", stProjNone: "не запрошена", dlgTitle: "Ваш доступ к ИИ", tabByok: "BYOK", tabQuota: "Запросить квоту", stDiscuss: "Обсуждения", stBackend: "Действия на сервере", stBackendHint: "генерация комментариев, запуск промптов", stAccount: "Вход", stGithub: "GitHub (курирование, отзывы)", stNone: "не подключено", stSignedOut: "вход не выполнен", stViaAction: "через GitHub Action владельца", stGhOn: "токен сохранён", stGhLater: "подключается при отправке пакета проверок", stProjUntil: "Квота проекта до %s", stProjPending: "Квота проекта запрошена", recheck: "Проверить", hdrKi: "ИИ", stViaMail: "ссылка по почте", stLocal: "локальный CLI", apple: "Продолжить с Apple", projDenied: "Нет действующего доступа к квоте проекта.", projLabel: "Квота проекта · Nexos", reqExpired: "Ваш доступ истёк %s.", github: "Продолжить с GitHub", reqLink: "Нет своего ключа? Запросить квоту проекта", reqTitle: "Запросить квоту проекта", reqLead: "Нет своего ключа? Попросите владельца открыть вам квоту проекта на определённое время. Запросы будут идти через проект; ваш браузер не увидит ключа.", reqReason: "Для чего он вам нужен?", reqReasonPh: "Например: я проверяю требования COM для нашего ЭБУ.", reqSend: "Отправить запрос", reqPending: "Ваш запрос от %s ожидает одобрения.", reqWithdraw: "Отозвать запрос", reqRejected: "Ваш запрос отклонён.", reqGranted: "Доступ открыт до %s.", reqSignIn: "Войдите, чтобы одобрение можно было закрепить за вами.", reqDone: "Запрос отправлен.", grantedToast: "Квота проекта включена.", viaProject: "квота проекта", provPick: "От какого провайдера ключ?", orSignIn: "Или войдите", signInRequired: "Также войдите", optSignIn: "Необязательно: войти с аккаунтом", welcomeByok: "Затем вы подключите собственный API-ключ провайдера ИИ.", headerConnect: "Подключить ИИ", geminiNote: "На бесплатном уровне Google может использовать ваши запросы для улучшения своих продуктов. Для конфиденциального содержимого используйте ключ с оплатой.", byokLead: "Для этого нужен собственный API-ключ провайдера ИИ. Провайдер выставляет счёт за использование напрямую вам.",
      b1t: "Ваш ключ", b1: "Он остаётся в этом браузере и отправляется только напрямую провайдеру, но никогда нам.",
      b2t: "Ваши расходы", b2: "Вы платите только за то, что используете у провайдера. У Gemini есть ограниченный бесплатный уровень.",
      b3t: "Результативно", b3: "Хорошие предложения попадают к кураторам одним щелчком.",
      google: "Продолжить с Google", orMail: "или по ссылке из письма",
      mailPh: "name@example.com", sendLink: "Отправить ссылку",
      fine: "Пароль не нужен. Для входа мы храним только ваш адрес электронной почты.",
      setup: "Вход пока настраивается.", localSkip: "Продолжить без входа",
      sentTitle: "Проверьте почту", sentLead: "Мы отправили ссылку для входа на %s. Перейдите по ней — вы вернётесь сюда уже авторизованными.",
      otherDevice: "Открыли письмо на другом устройстве?", pasteLead: "Скопируйте ссылку из письма и вставьте её сюда:", pastePh: "https://…", pasteGo: "Войти",
      resend: "Отправить снова", otherMail: "Другой адрес", noMail: "Письмо не пришло? Проверьте папку «Спам».", resent: "Ссылка отправлена повторно.",
      confirmTitle: "Почти готово", confirmLead: "Подтвердите адрес, на который была отправлена ссылка.", confirmGo: "Подтвердить",
      welcome: "Добро пожаловать, %s!", welcomeAnon: "Добро пожаловать!",
      connectLead: "Ещё один шаг: подключите модель ИИ. Ключ остаётся в этом браузере.",
      recommended: "Рекомендуется", freeKey: "бесплатный уровень", keyLabel: "API-ключ", keyCreate: "Создать ключ", show: "Показать", hide: "Скрыть",
      remember: "Запомнить на этом устройстве", connect: "Подключить", checking: "Проверка ключа…", keyOk: "Подключено — доступно моделей: %n.",
      keyNoList: "Ключ сохранён. Этот провайдер не выдаёт список моделей; укажите ID модели ниже.",
      keyBad: "Провайдер отклонил ключ.", keyNet: "Провайдер сейчас недоступен.",
      local: "Локальные CLI для ИИ", localFound: "Найдено на этом компьютере:", useThis: "Использовать",
      activeModel: "Активная модель", modelId: "ID модели", providers: "Подключённые провайдеры", addProvider: "Подключить другого провайдера",
      remove: "Удалить", signOut: "Выйти", session: "сеанс",
      storeNote: "Ключи хранятся в хранилище браузера этого сайта. На общих компьютерах снимите отметку «запомнить».",
      viaKey: "свой ключ", viaLocal: "локально",
      chipSignIn: "Войдите для обсуждения с ИИ", chipConnect: "Подключить модель ИИ", chipSetup: "Обсуждение с ИИ скоро появится",
      gateSignIn: "Войдите, чтобы обсуждать с ИИ, — бесплатно, через Google или по ссылке из письма.",
      gateKey: "Для обсуждения с ИИ нужен собственный API-ключ, например от Google AI Studio, Anthropic или OpenAI.",
      gateSetup: "Обсуждение с ИИ скоро появится на публичном сайте. Локально с _src/serve.py оно уже работает.",
      gateBtnSignIn: "Войти", gateBtnKey: "Подключить модель",
      errMail: "Введите корректный адрес электронной почты.", errDomain: "Этот адрес пока не разрешён для входа.",
      errLink: "Ссылка устарела или уже использована. Просто запросите новую.", errNet: "Нет соединения. Попробуйте чуть позже.",
      errOff: "Этот способ входа ещё не включён.", errGeneric: "Не получилось: %s",
      signedIn: "Вы вошли как %s.", signedOut: "Вы вышли.",
      issueClip: "Предложение длинное и скопировано в буфер обмена — вставьте его в открывшуюся форму GitHub.",
      issueOpened: "Форма GitHub открыта. Кнопка «Submit new issue» отправит предложение кураторам.",
      pasteHere: "<!-- Вставьте сюда содержимое буфера обмена -->"
    },
    ar: {
      signIn: "تسجيل الدخول", account: "الحساب", close: "إغلاق",
      heroTitle: "ناقش المواصفة مع الذكاء الاصطناعي",
      heroLead: "اسأل عن العلاقات، وتحقّق من التبعيات، واقترح تحسينات مباشرة بجوار النص.", reqView: "عرض حالة الطلب", reqAgain: "الطلب مجددًا", reqUpdate: "حفظ التبرير", reqUpdated: "حُفظ التبرير.", icoKeyOk: "المفتاح الخاص يعمل", icoKeyBad: "رُفض المفتاح الخاص", icoGiftOpen: "تمت الموافقة على حصة المشروع", icoGiftPending: "طُلبت حصة المشروع", icoGiftBad: "رُفضت حصة المشروع أو انتهت", icoLocalOk: "ذكاء اصطناعي محلي متاح", icoLocalBad: "لا يتوفر ذكاء اصطناعي محلي", noAccessHint: "لا يوجد وصول إلى الذكاء الاصطناعي. أعدّه هنا.", answeredBy: "إجابة من", icoKeyPart: "رُفض بعض المفاتيح الخاصة", localProbe: "تحقق محليًا", localFoundAway: "عُثر على خادم محلي في %s.", localOpen: "افتح الصفحة هناك", localNotFound: "لا يستجيب أي خادم محلي على %s.", secByok: "مفاتيح خاصة (BYOK)", storeLocal: "محفوظ في تخزين المتصفح لهذا الموقع", storeSession: "محفوظ لهذه الجلسة فقط", stNoKeys: "لا يوجد مفتاح خاص بعد.", secLocal: "أدوات CLI محلية للذكاء الاصطناعي (localhost)", localNoServer: "لا يوجد خادم محلي متاح. شغّل _src/serve.py.", localOnlyLocal: "متاح فقط عند تشغيل الصفحة محليًا عبر _src/serve.py.", back: "رجوع", tabStatus: "الحالة", tabAdd: "إضافة BYOK", stSources: "وصولك إلى الذكاء الاصطناعي للمناقشات", stKeyFailed: "رُفض آخر مرة", stWorks: "يعمل", stSignedVia: "تم تسجيل الدخول عبر %s", stNoSources: "لا يوجد وصول بعد. أضف مفتاحك الخاص أو اطلب حصة.", stLocalTitle: "ذكاء اصطناعي محلي", stProjExpired: "انتهت حصة المشروع في %s", hdrOk: "الوصول إلى الذكاء الاصطناعي يعمل", hdrPartial: "الوصول إلى الذكاء الاصطناعي متاح جزئيًا", hdrNone: "لا يوجد وصول عامل إلى الذكاء الاصطناعي", appleSetup: "تسجيل الدخول عبر Apple غير مُعدّ بعد.", stProjActive: "نشطة حتى %s", stProjNone: "لم تُطلب", dlgTitle: "وصولك إلى الذكاء الاصطناعي", tabByok: "BYOK", tabQuota: "طلب حصة", stDiscuss: "المناقشات", stBackend: "إجراءات الخادم", stBackendHint: "توليد التعليقات وتشغيل الأوامر", stAccount: "تسجيل الدخول", stGithub: "GitHub (التنسيق والملاحظات)", stNone: "غير متصل", stSignedOut: "لم يتم تسجيل الدخول", stViaAction: "عبر GitHub Action الخاص بالمسؤول", stGhOn: "الرمز محفوظ", stGhLater: "يُربط عند إرسال حزمة المراجعة", stProjUntil: "حصة المشروع حتى %s", stProjPending: "طُلبت حصة المشروع", recheck: "تحقق", hdrKi: "ذكاء اصطناعي", stViaMail: "رابط بالبريد", stLocal: "CLI محلي", apple: "المتابعة باستخدام Apple", projDenied: "لا يوجد وصول صالح إلى حصة المشروع.", projLabel: "حصة المشروع · Nexos", reqExpired: "انتهت صلاحية وصولك في %s.", github: "المتابعة باستخدام GitHub", reqLink: "ليس لديك مفتاح خاص؟ اطلب حصة من المشروع", reqTitle: "طلب حصة من المشروع", reqLead: "ليس لديك مفتاح خاص؟ اطلب من المسؤول تفعيل حصة المشروع لك لفترة محددة. تمر الطلبات عندها عبر المشروع، ولا يرى متصفحك أي مفتاح.", reqReason: "لماذا تحتاج إليها؟", reqReasonPh: "مثال: أراجع متطلبات COM لوحدة التحكم لدينا.", reqSend: "إرسال الطلب", reqPending: "طلبك بتاريخ %s بانتظار الموافقة.", reqWithdraw: "سحب الطلب", reqRejected: "رُفض طلبك.", reqGranted: "مفعّل حتى %s.", reqSignIn: "سجّل الدخول ليمكن ربط الموافقة بك.", reqDone: "أُرسل الطلب.", grantedToast: "فُعّلت حصة المشروع.", viaProject: "حصة المشروع", provPick: "من أي مزوّد هذا المفتاح؟", orSignIn: "أو سجّل الدخول", signInRequired: "سجّل الدخول أيضًا", optSignIn: "اختياري: تسجيل الدخول بحساب", welcomeByok: "بعد ذلك تربط مفتاح API الخاص بك من مزوّد ذكاء اصطناعي.", headerConnect: "ربط الذكاء الاصطناعي", geminiNote: "في المستوى المجاني يجوز لـ Google استخدام مدخلاتك لتحسين منتجاتها. للمحتوى السري استخدم مفتاحًا مع تفعيل الفوترة.", byokLead: "لذلك تحتاج إلى مفتاح API خاص بك من مزوّد ذكاء اصطناعي. يحاسبك المزوّد على الاستخدام مباشرة.",
      b1t: "مفتاحك", b1: "يبقى في هذا المتصفح ولا يُرسل إلا مباشرة إلى المزوّد، وليس إلينا أبدًا.",
      b2t: "تكاليفك", b2: "تدفع فقط مقابل ما تستخدمه لدى المزوّد. يوفّر Gemini مستوى مجانيًا محدودًا.",
      b3t: "فعّال", b3: "تصل الاقتراحات الجيدة إلى المنسقين بنقرة واحدة.",
      google: "المتابعة باستخدام Google", orMail: "أو برابط عبر البريد الإلكتروني",
      mailPh: "name@example.com", sendLink: "إرسال الرابط",
      fine: "لا حاجة لكلمة مرور. لتسجيل الدخول نحفظ عنوان بريدك الإلكتروني فقط.",
      setup: "يجري إعداد تسجيل الدخول.", localSkip: "المتابعة دون تسجيل الدخول",
      sentTitle: "تفقّد بريدك الوارد", sentLead: "أرسلنا رابط تسجيل الدخول إلى %s. انقر عليه لتعود إلى هنا وقد سجّلت الدخول.",
      otherDevice: "فتحت الرسالة على جهاز آخر؟", pasteLead: "انسخ الرابط من الرسالة والصقه هنا:", pastePh: "https://…", pasteGo: "تسجيل الدخول",
      resend: "إعادة الإرسال", otherMail: "استخدام عنوان آخر", noMail: "لم يصلك شيء؟ تحقّق أيضًا من مجلد الرسائل غير المرغوب فيها.", resent: "أُعيد إرسال الرابط.",
      confirmTitle: "أوشكت على الانتهاء", confirmLead: "يُرجى تأكيد عنوان البريد الذي أُرسل إليه الرابط.", confirmGo: "تأكيد",
      welcome: "مرحبًا، %s!", welcomeAnon: "مرحبًا!",
      connectLead: "خطوة أخيرة: اربط نموذج ذكاء اصطناعي. يبقى مفتاحك في هذا المتصفح.",
      recommended: "موصى به", freeKey: "مستوى مجاني", keyLabel: "مفتاح API", keyCreate: "إنشاء مفتاح", show: "إظهار", hide: "إخفاء",
      remember: "التذكّر على هذا الجهاز", connect: "ربط", checking: "جارٍ التحقق من المفتاح…", keyOk: "تم الربط – عدد النماذج المتاحة: %n.",
      keyNoList: "حُفظ المفتاح. هذا المزوّد لا يعرض قائمة نماذجه؛ أدخل معرّف النموذج أدناه.",
      keyBad: "رفض المزوّد المفتاح.", keyNet: "تعذّر الوصول إلى المزوّد حاليًا.",
      local: "أدوات CLI محلية للذكاء الاصطناعي", localFound: "وُجدت على هذا الجهاز:", useThis: "استخدام",
      activeModel: "النموذج النشط", modelId: "معرّف النموذج", providers: "المزوّدون المرتبطون", addProvider: "ربط مزوّد آخر",
      remove: "إزالة", signOut: "تسجيل الخروج", session: "الجلسة",
      storeNote: "تُحفظ المفاتيح في تخزين المتصفح لهذا الموقع. على الأجهزة المشتركة ألغِ تحديد «التذكّر».",
      viaKey: "مفتاح خاص", viaLocal: "محلي",
      chipSignIn: "سجّل الدخول لمناقشة الذكاء الاصطناعي", chipConnect: "ربط نموذج ذكاء اصطناعي", chipSetup: "مناقشة الذكاء الاصطناعي قريبًا",
      gateSignIn: "سجّل الدخول لتناقش مع الذكاء الاصطناعي – مجانًا، عبر Google أو برابط في البريد.",
      gateKey: "تحتاج مناقشة الذكاء الاصطناعي إلى مفتاح API خاص بك، مثلًا من Google AI Studio أو Anthropic أو OpenAI.",
      gateSetup: "ستتوفر مناقشة الذكاء الاصطناعي قريبًا على الموقع العام. وهي تعمل محليًا بالفعل مع _src/serve.py.",
      gateBtnSignIn: "تسجيل الدخول", gateBtnKey: "ربط نموذج",
      errMail: "يُرجى إدخال عنوان بريد إلكتروني صالح.", errDomain: "هذا العنوان غير مفعّل بعد لتسجيل الدخول.",
      errLink: "انتهت صلاحية الرابط أو استُخدم من قبل. اطلب رابطًا جديدًا.", errNet: "لا يوجد اتصال. حاول مرة أخرى بعد قليل.",
      errOff: "طريقة تسجيل الدخول هذه غير مفعّلة بعد.", errGeneric: "لم ينجح ذلك: %s",
      signedIn: "سجّلت الدخول باسم %s.", signedOut: "تم تسجيل الخروج.",
      issueClip: "الاقتراح طويل وهو في الحافظة – الصقه في نموذج GitHub الذي فُتح للتو.",
      issueOpened: "فُتح نموذج GitHub. زر «Submit new issue» يرسل الاقتراح إلى المنسقين.",
      pasteHere: "<!-- الصق محتوى الحافظة هنا -->"
    },
    hi: {
      signIn: "साइन इन करें", account: "खाता", close: "बंद करें",
      heroTitle: "एआई के साथ स्पेसिफ़िकेशन पर चर्चा करें",
      heroLead: "संबंधों के बारे में पूछें, निर्भरताएँ जाँचें और सुधार सुझाएँ – सीधे टेक्स्ट के बगल में।", reqView: "अनुरोध स्थिति देखें", reqAgain: "फिर से अनुरोध करें", reqUpdate: "औचित्य सहेजें", reqUpdated: "औचित्य सहेजा गया।", icoKeyOk: "अपनी कुंजी काम करती है", icoKeyBad: "अपनी कुंजी अस्वीकृत", icoGiftOpen: "प्रोजेक्ट कोटा स्वीकृत", icoGiftPending: "प्रोजेक्ट कोटा माँगा गया", icoGiftBad: "प्रोजेक्ट कोटा अस्वीकृत या समाप्त", icoLocalOk: "स्थानीय एआई उपलब्ध", icoLocalBad: "कोई स्थानीय एआई उपलब्ध नहीं", noAccessHint: "कोई एआई पहुँच नहीं। यहाँ सेट करें।", answeredBy: "उत्तर स्रोत", icoKeyPart: "कुछ अपनी कुंजियाँ अस्वीकृत", localProbe: "स्थानीय रूप से जाँचें", localFoundAway: "%s पर स्थानीय सर्वर मिला।", localOpen: "पेज वहाँ खोलें", localNotFound: "%s पर कोई स्थानीय सर्वर जवाब नहीं देता।", secByok: "अपनी कुंजियाँ (BYOK)", storeLocal: "इस वेबसाइट के ब्राउज़र स्टोरेज में सहेजी गई", storeSession: "केवल इस सत्र के लिए सहेजी गई", stNoKeys: "अभी कोई अपनी कुंजी नहीं।", secLocal: "स्थानीय एआई CLI (localhost)", localNoServer: "कोई स्थानीय सर्वर उपलब्ध नहीं। _src/serve.py चलाएँ।", localOnlyLocal: "केवल तब उपलब्ध जब पेज _src/serve.py से स्थानीय रूप से चले।", back: "वापस", tabStatus: "स्थिति", tabAdd: "BYOK जोड़ें", stSources: "चर्चाओं के लिए आपकी एआई पहुँच", stKeyFailed: "पिछली बार अस्वीकृत", stWorks: "काम करता है", stSignedVia: "%s से साइन इन", stNoSources: "अभी कोई पहुँच नहीं। अपनी कुंजी जोड़ें या कोटा माँगें।", stLocalTitle: "स्थानीय एआई", stProjExpired: "प्रोजेक्ट कोटा %s को समाप्त हुआ", hdrOk: "एआई पहुँच काम कर रही है", hdrPartial: "एआई पहुँच आंशिक रूप से उपलब्ध", hdrNone: "कोई काम करती एआई पहुँच नहीं", appleSetup: "Apple से साइन-इन अभी सेट नहीं है।", stProjActive: "%s तक सक्रिय", stProjNone: "माँगा नहीं गया", dlgTitle: "आपकी एआई पहुँच", tabByok: "BYOK", tabQuota: "कोटा माँगें", stDiscuss: "चर्चाएँ", stBackend: "बैकएंड क्रियाएँ", stBackendHint: "टिप्पणियाँ बनाना, प्रॉम्प्ट चलाना", stAccount: "साइन-इन", stGithub: "GitHub (क्यूरेशन, फ़ीडबैक)", stNone: "जुड़ा नहीं", stSignedOut: "साइन इन नहीं", stViaAction: "संचालक के GitHub Action के ज़रिए", stGhOn: "टोकन सहेजा गया", stGhLater: "समीक्षा पैकेज भेजते समय जुड़ता है", stProjUntil: "%s तक प्रोजेक्ट कोटा", stProjPending: "प्रोजेक्ट कोटा माँगा गया", recheck: "जाँचें", hdrKi: "एआई", stViaMail: "ईमेल लिंक", stLocal: "स्थानीय CLI", apple: "Apple के साथ जारी रखें", projDenied: "प्रोजेक्ट कोटा की कोई मान्य पहुँच नहीं है।", projLabel: "प्रोजेक्ट कोटा · Nexos", reqExpired: "आपकी पहुँच %s को समाप्त हो गई।", github: "GitHub के साथ जारी रखें", reqLink: "अपनी कुंजी नहीं है? प्रोजेक्ट कोटा माँगें", reqTitle: "प्रोजेक्ट कोटा माँगें", reqLead: "अपनी कुंजी नहीं है? संचालक से कहें कि वे आपको कुछ समय के लिए प्रोजेक्ट कोटा दें। अनुरोध तब प्रोजेक्ट के ज़रिए चलते हैं; आपके ब्राउज़र को कोई कुंजी नहीं दिखती।", reqReason: "आपको इसकी ज़रूरत किसलिए है?", reqReasonPh: "उदाहरण: मैं हमारे ECU के लिए COM आवश्यकताएँ जाँच रहा/रही हूँ।", reqSend: "अनुरोध भेजें", reqPending: "%s का आपका अनुरोध मंज़ूरी की प्रतीक्षा में है।", reqWithdraw: "अनुरोध वापस लें", reqRejected: "आपका अनुरोध अस्वीकार कर दिया गया।", reqGranted: "%s तक सक्रिय।", reqSignIn: "साइन इन करें ताकि मंज़ूरी आपसे जोड़ी जा सके।", reqDone: "अनुरोध भेजा गया।", grantedToast: "प्रोजेक्ट कोटा सक्रिय हुआ।", viaProject: "प्रोजेक्ट कोटा", provPick: "यह कुंजी किस प्रदाता की है?", orSignIn: "या साइन इन करें", signInRequired: "साथ में साइन इन भी करें", optSignIn: "वैकल्पिक: खाते से साइन इन करें", welcomeByok: "इसके बाद आप किसी एआई प्रदाता की अपनी API कुंजी जोड़ते हैं।", headerConnect: "एआई जोड़ें", geminiNote: "मुफ़्त स्तर में Google आपके इनपुट का उपयोग अपने उत्पाद सुधारने के लिए कर सकता है। गोपनीय सामग्री के लिए बिलिंग वाली कुंजी इस्तेमाल करें।", byokLead: "इसके लिए आप किसी एआई प्रदाता की अपनी API कुंजी लाते हैं। प्रदाता उपयोग का बिल सीधे आपको देता है।",
      b1t: "आपकी कुंजी", b1: "यह इसी ब्राउज़र में रहती है और केवल सीधे प्रदाता तक जाती है, हम तक कभी नहीं।",
      b2t: "आपकी लागत", b2: "आप केवल उतना भुगतान करते हैं जितना प्रदाता के पास उपयोग करते हैं। Gemini सीमित मुफ़्त स्तर देता है।",
      b3t: "असरदार", b3: "अच्छे सुझाव एक क्लिक में क्यूरेटरों तक पहुँचते हैं।",
      google: "Google के साथ जारी रखें", orMail: "या ईमेल लिंक से",
      mailPh: "name@example.com", sendLink: "लिंक भेजें",
      fine: "पासवर्ड की ज़रूरत नहीं। साइन-इन के लिए हम केवल आपका ईमेल पता सहेजते हैं।",
      setup: "साइन-इन अभी सेट किया जा रहा है।", localSkip: "बिना साइन इन किए जारी रखें",
      sentTitle: "अपना इनबॉक्स देखें", sentLead: "हमने %s पर साइन-इन लिंक भेजा है। उस पर क्लिक करें – आप साइन इन होकर यहीं लौट आएँगे।",
      otherDevice: "ईमेल किसी दूसरे डिवाइस पर खोला?", pasteLead: "ईमेल से लिंक कॉपी करके यहाँ पेस्ट करें:", pastePh: "https://…", pasteGo: "साइन इन करें",
      resend: "फिर से भेजें", otherMail: "दूसरा पता इस्तेमाल करें", noMail: "कुछ नहीं आया? स्पैम फ़ोल्डर भी देखें।", resent: "लिंक फिर से भेजा गया।",
      confirmTitle: "बस हो गया", confirmLead: "कृपया वह ईमेल पता पुष्टि करें जिस पर लिंक भेजा गया था।", confirmGo: "पुष्टि करें",
      welcome: "स्वागत है, %s!", welcomeAnon: "स्वागत है!",
      connectLead: "एक और क़दम: कोई एआई मॉडल जोड़ें। आपकी कुंजी इसी ब्राउज़र में रहती है।",
      recommended: "अनुशंसित", freeKey: "मुफ़्त स्तर", keyLabel: "API कुंजी", keyCreate: "कुंजी बनाएँ", show: "दिखाएँ", hide: "छिपाएँ",
      remember: "इस डिवाइस पर याद रखें", connect: "जोड़ें", checking: "कुंजी जाँची जा रही है…", keyOk: "जुड़ गया – %n मॉडल उपलब्ध।",
      keyNoList: "कुंजी सहेजी गई। यह प्रदाता अपने मॉडलों की सूची नहीं देता; नीचे मॉडल ID डालें।",
      keyBad: "प्रदाता ने कुंजी अस्वीकार कर दी।", keyNet: "प्रदाता अभी उपलब्ध नहीं है।",
      local: "स्थानीय एआई CLI", localFound: "इस मशीन पर मिले:", useThis: "इस्तेमाल करें",
      activeModel: "सक्रिय मॉडल", modelId: "मॉडल ID", providers: "जुड़े प्रदाता", addProvider: "दूसरा प्रदाता जोड़ें",
      remove: "हटाएँ", signOut: "साइन आउट करें", session: "सत्र",
      storeNote: "कुंजियाँ इस वेबसाइट के ब्राउज़र स्टोरेज में रहती हैं। साझा कंप्यूटरों पर “याद रखें” हटा दें।",
      viaKey: "अपनी कुंजी", viaLocal: "स्थानीय",
      chipSignIn: "एआई चर्चा के लिए साइन इन करें", chipConnect: "एआई मॉडल जोड़ें", chipSetup: "एआई चर्चा जल्द उपलब्ध",
      gateSignIn: "एआई से चर्चा करने के लिए साइन इन करें – मुफ़्त, Google या ईमेल लिंक से।",
      gateKey: "एआई चर्चा के लिए आपकी अपनी API कुंजी चाहिए, जैसे Google AI Studio, Anthropic या OpenAI से।",
      gateSetup: "एआई चर्चा जल्द ही सार्वजनिक साइट पर आएगी। स्थानीय रूप से _src/serve.py के साथ यह पहले से चलती है।",
      gateBtnSignIn: "साइन इन करें", gateBtnKey: "मॉडल जोड़ें",
      errMail: "कृपया एक मान्य ईमेल पता दर्ज करें।", errDomain: "यह पता अभी साइन-इन के लिए सक्षम नहीं है।",
      errLink: "लिंक की अवधि समाप्त हो गई या वह पहले ही इस्तेमाल हो चुका है। बस नया लिंक माँगें।", errNet: "कनेक्शन नहीं है। थोड़ी देर में फिर कोशिश करें।",
      errOff: "यह साइन-इन तरीका अभी सक्रिय नहीं है।", errGeneric: "यह नहीं हो पाया: %s",
      signedIn: "%s के रूप में साइन इन।", signedOut: "साइन आउट हो गए।",
      issueClip: "सुझाव लंबा है और क्लिपबोर्ड में है – इसे अभी खुले GitHub फ़ॉर्म में पेस्ट करें।",
      issueOpened: "GitHub फ़ॉर्म खुल गया। “Submit new issue” सुझाव क्यूरेटरों को भेजता है।",
      pasteHere: "<!-- क्लिपबोर्ड की सामग्री यहाँ पेस्ट करें -->"
    },
    ko: {
      signIn: "로그인", account: "계정", close: "닫기",
      heroTitle: "AI와 함께 사양을 토론하세요",
      heroLead: "관계를 묻고, 의존성을 확인하고, 개선안을 제안하세요. 텍스트 바로 옆에서 할 수 있습니다.", reqView: "요청 상태 보기", reqAgain: "다시 요청", reqUpdate: "사유 저장", reqUpdated: "사유를 저장했습니다.", icoKeyOk: "본인 키 작동", icoKeyBad: "본인 키 거부됨", icoGiftOpen: "프로젝트 할당량 승인됨", icoGiftPending: "프로젝트 할당량 요청됨", icoGiftBad: "프로젝트 할당량 거절 또는 만료", icoLocalOk: "로컬 AI 사용 가능", icoLocalBad: "사용 가능한 로컬 AI 없음", noAccessHint: "AI 접근이 없습니다. 여기서 설정하세요.", answeredBy: "응답 출처", icoKeyPart: "일부 본인 키 거부됨", localProbe: "로컬 확인", localFoundAway: "%s에서 로컬 서버를 찾았습니다.", localOpen: "그곳에서 페이지 열기", localNotFound: "%s에서 응답하는 로컬 서버가 없습니다.", secByok: "본인 키 (BYOK)", storeLocal: "이 웹사이트의 브라우저 저장소에 저장됨", storeSession: "이 세션에만 저장됨", stNoKeys: "아직 본인 키가 없습니다.", secLocal: "로컬 AI CLI (localhost)", localNoServer: "로컬 서버에 연결할 수 없습니다. _src/serve.py를 실행하세요.", localOnlyLocal: "페이지를 _src/serve.py로 로컬 실행할 때만 사용할 수 있습니다.", back: "뒤로", tabStatus: "상태", tabAdd: "BYOK 추가", stSources: "토론용 AI 접근", stKeyFailed: "최근 거부됨", stWorks: "작동함", stSignedVia: "%s(으)로 로그인됨", stNoSources: "아직 접근 권한이 없습니다. 본인 키를 추가하거나 할당량을 요청하세요.", stLocalTitle: "로컬 AI", stProjExpired: "프로젝트 할당량이 %s에 만료됨", hdrOk: "AI 접근이 작동합니다", hdrPartial: "AI 접근이 일부만 가능합니다", hdrNone: "작동하는 AI 접근이 없습니다", appleSetup: "Apple 로그인이 아직 설정되지 않았습니다.", stProjActive: "%s까지 활성", stProjNone: "요청 안 함", dlgTitle: "내 AI 접근", tabByok: "BYOK", tabQuota: "할당량 요청", stDiscuss: "토론", stBackend: "백엔드 작업", stBackendHint: "주석 생성, 프롬프트 실행", stAccount: "로그인", stGithub: "GitHub (큐레이션, 피드백)", stNone: "연결 안 됨", stSignedOut: "로그인 안 됨", stViaAction: "운영자의 GitHub Action을 통해", stGhOn: "토큰 저장됨", stGhLater: "검토 패키지를 제출할 때 연결됨", stProjUntil: "%s까지 프로젝트 할당량", stProjPending: "프로젝트 할당량 요청됨", recheck: "확인", hdrKi: "AI", stViaMail: "이메일 링크", stLocal: "로컬 CLI", apple: "Apple로 계속하기", projDenied: "프로젝트 할당량에 대한 유효한 권한이 없습니다.", projLabel: "프로젝트 할당량 · Nexos", reqExpired: "접근 권한이 %s에 만료되었습니다.", github: "GitHub 계정으로 계속하기", reqLink: "본인 키가 없나요? 프로젝트 할당량 요청", reqTitle: "프로젝트 할당량 요청", reqLead: "본인 키가 없나요? 운영자에게 일정 기간 프로젝트 할당량을 열어 달라고 요청하세요. 요청은 프로젝트를 통해 처리되며 브라우저에는 키가 전달되지 않습니다.", reqReason: "어디에 필요하신가요?", reqReasonPh: "예: 저희 ECU의 COM 요구사항을 검토하고 있습니다.", reqSend: "요청 보내기", reqPending: "%s에 보낸 요청이 승인을 기다리고 있습니다.", reqWithdraw: "요청 취소", reqRejected: "요청이 거절되었습니다.", reqGranted: "%s까지 활성화됨.", reqSignIn: "승인을 본인에게 연결할 수 있도록 로그인하세요.", reqDone: "요청을 보냈습니다.", grantedToast: "프로젝트 할당량이 활성화되었습니다.", viaProject: "프로젝트 할당량", provPick: "어느 제공업체의 키인가요?", orSignIn: "또는 로그인", signInRequired: "로그인도 해 주세요", optSignIn: "선택 사항: 계정으로 로그인", welcomeByok: "그다음 AI 제공업체의 본인 API 키를 연결합니다.", headerConnect: "AI 연결", geminiNote: "무료 등급에서는 Google이 입력 내용을 제품 개선에 사용할 수 있습니다. 기밀 내용에는 결제가 설정된 키를 사용하세요.", byokLead: "이를 위해 AI 제공업체의 본인 API 키가 필요합니다. 사용 요금은 제공업체가 직접 청구합니다.",
      b1t: "본인 키", b1: "키는 이 브라우저에만 남고 제공업체로만 직접 전송되며, 저희에게는 절대 전송되지 않습니다.",
      b2t: "본인 비용", b2: "제공업체에서 사용한 만큼만 지불합니다. Gemini는 제한된 무료 등급을 제공합니다.",
      b3t: "효과적", b3: "좋은 제안은 클릭 한 번으로 큐레이터에게 전달됩니다.",
      google: "Google 계정으로 계속하기", orMail: "또는 이메일 링크로",
      mailPh: "name@example.com", sendLink: "링크 보내기",
      fine: "비밀번호가 필요 없습니다. 로그인을 위해 이메일 주소만 저장합니다.",
      setup: "로그인을 설정하는 중입니다.", localSkip: "로그인 없이 계속하기",
      sentTitle: "받은편지함을 확인하세요", sentLead: "%s(으)로 로그인 링크를 보냈습니다. 링크를 클릭하면 로그인된 상태로 이곳에 돌아옵니다.",
      otherDevice: "다른 기기에서 메일을 열었나요?", pasteLead: "메일의 링크를 복사해 여기에 붙여넣으세요:", pastePh: "https://…", pasteGo: "로그인",
      resend: "다시 보내기", otherMail: "다른 주소 사용", noMail: "메일이 오지 않았나요? 스팸 폴더도 확인하세요.", resent: "링크를 다시 보냈습니다.",
      confirmTitle: "거의 다 됐습니다", confirmLead: "링크를 받은 이메일 주소를 확인해 주세요.", confirmGo: "확인",
      welcome: "%s님, 환영합니다!", welcomeAnon: "환영합니다!",
      connectLead: "한 단계만 더: AI 모델을 연결하세요. 키는 이 브라우저에 남습니다.",
      recommended: "추천", freeKey: "무료 등급", keyLabel: "API 키", keyCreate: "키 만들기", show: "표시", hide: "숨기기",
      remember: "이 기기에서 기억하기", connect: "연결", checking: "키 확인 중…", keyOk: "연결됨 – 사용 가능한 모델 %n개.",
      keyNoList: "키를 저장했습니다. 이 제공업체는 모델 목록을 제공하지 않으므로 아래에 모델 ID를 입력하세요.",
      keyBad: "제공업체가 키를 거부했습니다.", keyNet: "지금은 제공업체에 연결할 수 없습니다.",
      local: "로컬 AI CLI", localFound: "이 컴퓨터에서 찾음:", useThis: "사용",
      activeModel: "활성 모델", modelId: "모델 ID", providers: "연결된 제공업체", addProvider: "다른 제공업체 연결",
      remove: "제거", signOut: "로그아웃", session: "세션",
      storeNote: "키는 이 웹사이트의 브라우저 저장소에 보관됩니다. 공용 컴퓨터에서는 ‘기억하기’를 해제하세요.",
      viaKey: "개인 키", viaLocal: "로컬",
      chipSignIn: "AI 토론을 위해 로그인", chipConnect: "AI 모델 연결", chipSetup: "AI 토론 곧 제공",
      gateSignIn: "AI와 토론하려면 로그인하세요. Google 또는 이메일 링크로 무료로 이용할 수 있습니다.",
      gateKey: "AI 토론에는 Google AI Studio, Anthropic, OpenAI 등에서 받은 본인 API 키가 필요합니다.",
      gateSetup: "AI 토론은 곧 공개 사이트에서 제공됩니다. 로컬에서는 _src/serve.py로 이미 사용할 수 있습니다.",
      gateBtnSignIn: "로그인", gateBtnKey: "모델 연결",
      errMail: "올바른 이메일 주소를 입력하세요.", errDomain: "이 주소는 아직 로그인이 허용되지 않았습니다.",
      errLink: "링크가 만료되었거나 이미 사용되었습니다. 새 링크를 요청하세요.", errNet: "연결이 없습니다. 잠시 후 다시 시도하세요.",
      errOff: "이 로그인 방식은 아직 활성화되지 않았습니다.", errGeneric: "실패했습니다: %s",
      signedIn: "%s(으)로 로그인했습니다.", signedOut: "로그아웃했습니다.",
      issueClip: "제안이 길어서 클립보드에 복사했습니다. 방금 열린 GitHub 양식에 붙여넣으세요.",
      issueOpened: "GitHub 양식이 열렸습니다. “Submit new issue”를 누르면 제안이 큐레이터에게 전달됩니다.",
      pasteHere: "<!-- 클립보드 내용을 여기에 붙여넣으세요 -->"
    },
    zh: {
      signIn: "登录", account: "账号", close: "关闭",
      heroTitle: "与 AI 一起讨论规范",
      heroLead: "就在正文旁边询问关联、检查依赖并提出改进建议。", reqView: "查看申请状态", reqAgain: "重新申请", reqUpdate: "保存理由", reqUpdated: "理由已保存。", icoKeyOk: "自有密钥可用", icoKeyBad: "自有密钥被拒绝", icoGiftOpen: "项目额度已批准", icoGiftPending: "项目额度已申请", icoGiftBad: "项目额度被拒绝或已过期", icoLocalOk: "本地 AI 可用", icoLocalBad: "没有可用的本地 AI", noAccessHint: "没有 AI 访问。在此设置。", answeredBy: "回答来自", icoKeyPart: "部分自有密钥被拒绝", localProbe: "本地检查", localFoundAway: "在 %s 找到本地服务器。", localOpen: "在那里打开页面", localNotFound: "%s 上没有本地服务器响应。", secByok: "自有密钥 (BYOK)", storeLocal: "保存在本网站的浏览器存储中", storeSession: "仅为本次会话保存", stNoKeys: "还没有自己的密钥。", secLocal: "本地 AI 命令行工具 (localhost)", localNoServer: "无法连接本地服务器。请启动 _src/serve.py。", localOnlyLocal: "仅当页面通过 _src/serve.py 在本地运行时可用。", back: "返回", tabStatus: "状态", tabAdd: "添加 BYOK", stSources: "你用于讨论的 AI 访问", stKeyFailed: "上次被拒绝", stWorks: "正常", stSignedVia: "已通过 %s 登录", stNoSources: "暂无访问。请添加自己的密钥或申请额度。", stLocalTitle: "本地 AI", stProjExpired: "项目额度已于 %s 过期", hdrOk: "AI 访问正常", hdrPartial: "AI 访问部分可用", hdrNone: "没有可用的 AI 访问", appleSetup: "使用 Apple 登录尚未配置。", stProjActive: "有效期至 %s", stProjNone: "未申请", dlgTitle: "你的 AI 访问", tabByok: "BYOK", tabQuota: "申请额度", stDiscuss: "讨论", stBackend: "后端操作", stBackendHint: "生成评注、运行提示词", stAccount: "登录", stGithub: "GitHub（审校、反馈）", stNone: "未连接", stSignedOut: "未登录", stViaAction: "通过运营者的 GitHub Action", stGhOn: "已保存令牌", stGhLater: "提交评审包时连接", stProjUntil: "项目额度有效期至 %s", stProjPending: "已申请项目额度", recheck: "检查", hdrKi: "AI", stViaMail: "邮件链接", stLocal: "本地 CLI", apple: "通过 Apple 继续", projDenied: "没有有效的项目额度权限。", projLabel: "项目额度 · Nexos", reqExpired: "你的权限已于 %s 过期。", github: "使用 GitHub 账号继续", reqLink: "没有自己的密钥？申请项目额度", reqTitle: "申请项目额度", reqLead: "没有自己的密钥？请运营者在一段时间内为你开通项目额度。请求将通过项目处理，你的浏览器不会接触任何密钥。", reqReason: "你需要它做什么？", reqReasonPh: "例如：我正在审查我们 ECU 的 COM 需求。", reqSend: "发送申请", reqPending: "你于 %s 提交的申请正在等待批准。", reqWithdraw: "撤回申请", reqRejected: "你的申请已被拒绝。", reqGranted: "已开通，有效期至 %s。", reqSignIn: "请登录，以便将批准分配给你。", reqDone: "申请已发送。", grantedToast: "项目额度已开通。", viaProject: "项目额度", provPick: "这个密钥来自哪个服务商？", orSignIn: "或者登录", signInRequired: "还需要登录", optSignIn: "可选：使用账号登录", welcomeByok: "接下来连接你自己的 AI 服务商 API 密钥。", headerConnect: "连接 AI", geminiNote: "在免费层级中，Google 可能会使用你的输入来改进其产品。处理机密内容时，请使用已开通计费的密钥。", byokLead: "为此你需要自备一个 AI 服务商的 API 密钥。用量费用由服务商直接向你收取。",
      b1t: "你的密钥", b1: "密钥只保存在此浏览器中，只直接发送给服务商，绝不会发给我们。",
      b2t: "你的费用", b2: "你只需为在服务商处的实际用量付费。Gemini 提供有限的免费层级。",
      b3t: "有效", b3: "好的建议一键即可送达审校人员。",
      google: "使用 Google 账号继续", orMail: "或使用邮件链接",
      mailPh: "name@example.com", sendLink: "发送链接",
      fine: "无需密码。登录时我们只保存你的电子邮件地址。",
      setup: "登录功能正在配置中。", localSkip: "不登录继续",
      sentTitle: "请查看你的收件箱", sentLead: "我们已向 %s 发送登录链接。点击链接后会回到此处并已登录。",
      otherDevice: "在其他设备上打开了邮件？", pasteLead: "复制邮件中的链接并粘贴到这里：", pastePh: "https://…", pasteGo: "登录",
      resend: "重新发送", otherMail: "使用其他地址", noMail: "没有收到？也请查看垃圾邮件文件夹。", resent: "已重新发送链接。",
      confirmTitle: "马上就好", confirmLead: "请确认接收链接的电子邮件地址。", confirmGo: "确认",
      welcome: "欢迎，%s！", welcomeAnon: "欢迎！",
      connectLead: "还差一步：连接一个 AI 模型。你的密钥只保存在此浏览器中。",
      recommended: "推荐", freeKey: "免费层级", keyLabel: "API 密钥", keyCreate: "创建密钥", show: "显示", hide: "隐藏",
      remember: "在此设备上记住", connect: "连接", checking: "正在检查密钥…", keyOk: "已连接 – 可用模型 %n 个。",
      keyNoList: "密钥已保存。此服务商不提供模型列表，请在下方输入模型 ID。",
      keyBad: "服务商拒绝了该密钥。", keyNet: "暂时无法连接服务商。",
      local: "本地 AI 命令行工具", localFound: "在本机找到：", useThis: "使用",
      activeModel: "当前模型", modelId: "模型 ID", providers: "已连接的服务商", addProvider: "连接其他服务商",
      remove: "移除", signOut: "退出登录", session: "会话",
      storeNote: "密钥保存在本网站的浏览器存储中。在共用电脑上请取消勾选“记住”。",
      viaKey: "自有密钥", viaLocal: "本地",
      chipSignIn: "登录后可与 AI 讨论", chipConnect: "连接 AI 模型", chipSetup: "AI 讨论即将推出",
      gateSignIn: "登录后即可与 AI 讨论——免费，可用 Google 或邮件链接登录。",
      gateKey: "AI 讨论需要你自己的 API 密钥，例如来自 Google AI Studio、Anthropic 或 OpenAI。",
      gateSetup: "公开网站即将提供 AI 讨论。在本地使用 _src/serve.py 已可使用。",
      gateBtnSignIn: "登录", gateBtnKey: "连接模型",
      errMail: "请输入有效的电子邮件地址。", errDomain: "此地址尚未开通登录。",
      errLink: "链接已过期或已被使用，请重新获取。", errNet: "没有网络连接，请稍后再试。",
      errOff: "此登录方式尚未启用。", errGeneric: "操作未成功：%s",
      signedIn: "已以 %s 登录。", signedOut: "已退出登录。",
      issueClip: "建议内容较长，已复制到剪贴板——请粘贴到刚打开的 GitHub 表单中。",
      issueOpened: "已打开 GitHub 表单。点击“Submit new issue”即可将建议发送给审校人员。",
      pasteHere: "<!-- 在此粘贴剪贴板内容 -->"
    },
    nl: {
      signIn: "Inloggen", account: "Account", close: "Sluiten",
      heroTitle: "Bespreek de specificatie met AI",
      heroLead: "Vraag naar samenhang, controleer afhankelijkheden en stel verbeteringen voor – direct naast de tekst.", reqView: "Aanvraagstatus bekijken", reqAgain: "Opnieuw aanvragen", reqUpdate: "Motivering opslaan", reqUpdated: "Motivering opgeslagen.", icoKeyOk: "Eigen sleutel werkt", icoKeyBad: "Eigen sleutel geweigerd", icoGiftOpen: "Projectquotum goedgekeurd", icoGiftPending: "Projectquotum aangevraagd", icoGiftBad: "Projectquotum afgewezen of verlopen", icoLocalOk: "Lokale AI beschikbaar", icoLocalBad: "Geen lokale AI beschikbaar", noAccessHint: "Geen AI-toegang. Hier instellen.", answeredBy: "Antwoord van", icoKeyPart: "Sommige eigen sleutels geweigerd", localProbe: "Lokaal controleren", localFoundAway: "Lokale server gevonden op %s.", localOpen: "Pagina daar openen", localNotFound: "Op %s antwoordt geen lokale server.", secByok: "Eigen sleutels (BYOK)", storeLocal: "opgeslagen in de browseropslag van deze website", storeSession: "alleen voor deze sessie opgeslagen", stNoKeys: "Nog geen eigen sleutel.", secLocal: "Lokale AI-CLI's (localhost)", localNoServer: "Geen lokale server bereikbaar. Start _src/serve.py.", localOnlyLocal: "Alleen beschikbaar als de pagina lokaal via _src/serve.py draait.", back: "Terug", tabStatus: "Status", tabAdd: "BYOK toevoegen", stSources: "Jouw AI-toegang voor discussies", stKeyFailed: "laatst geweigerd", stWorks: "werkt", stSignedVia: "Ingelogd met %s", stNoSources: "Nog geen toegang. Voeg je eigen sleutel toe of vraag quotum aan.", stLocalTitle: "Lokale AI", stProjExpired: "Projectquotum verlopen op %s", hdrOk: "AI-toegang werkt", hdrPartial: "AI-toegang deels beschikbaar", hdrNone: "geen werkende AI-toegang", appleSetup: "Inloggen met Apple is nog niet ingericht.", stProjActive: "actief tot %s", stProjNone: "niet aangevraagd", dlgTitle: "Jouw AI-toegang", tabByok: "BYOK", tabQuota: "Quotum aanvragen", stDiscuss: "Discussies", stBackend: "Backend-acties", stBackendHint: "commentaar genereren, prompts uitvoeren", stAccount: "Inloggen", stGithub: "GitHub (curatie, feedback)", stNone: "niet verbonden", stSignedOut: "niet ingelogd", stViaAction: "via de GitHub Action van de beheerder", stGhOn: "token opgeslagen", stGhLater: "wordt verbonden bij het versturen van het reviewpakket", stProjUntil: "Projectquotum tot %s", stProjPending: "Projectquotum aangevraagd", recheck: "Controleren", hdrKi: "AI", stViaMail: "e-maillink", stLocal: "lokale CLI", apple: "Doorgaan met Apple", projDenied: "Geen geldige toegang tot het projectquotum.", projLabel: "Projectquotum · Nexos", reqExpired: "Je toegang is verlopen op %s.", github: "Doorgaan met GitHub", reqLink: "Geen eigen sleutel? Projectquotum aanvragen", reqTitle: "Projectquotum aanvragen", reqLead: "Geen eigen sleutel? Vraag de beheerder je voor een bepaalde tijd vrij te geven voor het projectquotum. Verzoeken lopen dan via het project; je browser ziet nooit een sleutel.", reqReason: "Waarvoor heb je het nodig?", reqReasonPh: "Bijvoorbeeld: ik controleer de COM-eisen voor onze ECU.", reqSend: "Aanvraag versturen", reqPending: "Je aanvraag van %s wacht op goedkeuring.", reqWithdraw: "Aanvraag intrekken", reqRejected: "Je aanvraag is afgewezen.", reqGranted: "Vrijgegeven tot %s.", reqSignIn: "Log in zodat de vrijgave aan jou gekoppeld kan worden.", reqDone: "Aanvraag verstuurd.", grantedToast: "Projectquotum vrijgegeven.", viaProject: "projectquotum", provPick: "Van welke aanbieder is de sleutel?", orSignIn: "Of log in", signInRequired: "Log ook in", optSignIn: "Optioneel: inloggen met een account", welcomeByok: "Daarna koppel je je eigen API-sleutel van een AI-aanbieder.", headerConnect: "AI koppelen", geminiNote: "In het gratis niveau mag Google je invoer gebruiken om zijn producten te verbeteren. Gebruik voor vertrouwelijke inhoud een sleutel met facturering.", byokLead: "Daarvoor neem je je eigen API-sleutel van een AI-aanbieder mee. De aanbieder rekent het gebruik rechtstreeks met je af.",
      b1t: "Jouw sleutel", b1: "Hij blijft in deze browser en gaat alleen rechtstreeks naar de aanbieder, nooit naar ons.",
      b2t: "Jouw kosten", b2: "Je betaalt alleen wat je bij de aanbieder gebruikt. Gemini heeft een beperkt gratis niveau.",
      b3t: "Effectief", b3: "Goede voorstellen bereiken de curatoren met één klik.",
      google: "Doorgaan met Google", orMail: "of met een e-maillink",
      mailPh: "naam@voorbeeld.nl", sendLink: "Link versturen",
      fine: "Geen wachtwoord nodig. Voor het inloggen bewaren we alleen je e-mailadres.",
      setup: "Inloggen wordt nog ingericht.", localSkip: "Doorgaan zonder in te loggen",
      sentTitle: "Kijk in je inbox", sentLead: "We hebben een inloglink naar %s gestuurd. Klik erop – je komt hier terug en bent ingelogd.",
      otherDevice: "Mail op een ander apparaat geopend?", pasteLead: "Kopieer de link uit de mail en plak hem hier:", pastePh: "https://…", pasteGo: "Inloggen",
      resend: "Opnieuw versturen", otherMail: "Ander adres gebruiken", noMail: "Niets ontvangen? Kijk ook in je spammap.", resent: "Link opnieuw verstuurd.",
      confirmTitle: "Bijna klaar", confirmLead: "Bevestig het e-mailadres waar de link naartoe ging.", confirmGo: "Bevestigen",
      welcome: "Welkom, %s!", welcomeAnon: "Welkom!",
      connectLead: "Nog één stap: koppel een AI-model. Je sleutel blijft in deze browser.",
      recommended: "Aanbevolen", freeKey: "gratis niveau", keyLabel: "API-sleutel", keyCreate: "Sleutel aanmaken", show: "Tonen", hide: "Verbergen",
      remember: "Onthouden op dit apparaat", connect: "Koppelen", checking: "Sleutel wordt gecontroleerd…", keyOk: "Gekoppeld – %n modellen beschikbaar.",
      keyNoList: "Sleutel opgeslagen. Deze aanbieder geeft geen modellenlijst; vul hieronder de model-ID in.",
      keyBad: "De aanbieder heeft de sleutel geweigerd.", keyNet: "De aanbieder is nu niet bereikbaar.",
      local: "Lokale AI-CLI's", localFound: "Gevonden op deze computer:", useThis: "Gebruiken",
      activeModel: "Actief model", modelId: "Model-ID", providers: "Gekoppelde aanbieders", addProvider: "Andere aanbieder koppelen",
      remove: "Verwijderen", signOut: "Uitloggen", session: "sessie",
      storeNote: "Sleutels staan in de browseropslag van deze website. Vink op gedeelde computers ‘onthouden’ uit.",
      viaKey: "eigen sleutel", viaLocal: "lokaal",
      chipSignIn: "Log in voor de AI-discussie", chipConnect: "AI-model koppelen", chipSetup: "AI-discussie binnenkort beschikbaar",
      gateSignIn: "Log in om met de AI te discussiëren – gratis, met Google of een e-maillink.",
      gateKey: "De AI-discussie heeft je eigen API-sleutel nodig, bijvoorbeeld van Google AI Studio, Anthropic of OpenAI.",
      gateSetup: "De AI-discussie komt binnenkort op de openbare site. Lokaal met _src/serve.py werkt ze al.",
      gateBtnSignIn: "Inloggen", gateBtnKey: "Model koppelen",
      errMail: "Vul een geldig e-mailadres in.", errDomain: "Dit adres is nog niet vrijgegeven om in te loggen.",
      errLink: "De link is verlopen of al gebruikt. Vraag gewoon een nieuwe aan.", errNet: "Geen verbinding. Probeer het zo meteen opnieuw.",
      errOff: "Deze manier van inloggen is nog niet ingeschakeld.", errGeneric: "Dat is niet gelukt: %s",
      signedIn: "Ingelogd als %s.", signedOut: "Uitgelogd.",
      issueClip: "Het voorstel is lang en staat op je klembord – plak het in het GitHub-formulier dat net is geopend.",
      issueOpened: "GitHub-formulier geopend. ‘Submit new issue’ stuurt het voorstel naar de curatoren.",
      pasteHere: "<!-- Plak hier de inhoud van je klembord -->"
    }
  };
  function lang() {
    var l = (root.document && root.document.documentElement.getAttribute("lang")) || "de";
    return l.slice(0, 2).toLowerCase();
  }
  var L2 = {
    de: { prioUp: "Höher priorisieren", prioDown: "Niedriger priorisieren", prioHint: "Reihenfolge = Priorität. Ziehen oder Pfeile nutzen.", admBtn: "Verwaltung", viaLocalhost: "über %s" },
    en: { prioUp: "Raise priority", prioDown: "Lower priority", prioHint: "Order = priority. Drag or use the arrows.", admBtn: "Admin", viaLocalhost: "via %s" },
    es: { prioUp: "Subir prioridad", prioDown: "Bajar prioridad", prioHint: "Orden = prioridad. Arrastra o usa las flechas.", admBtn: "Administración", viaLocalhost: "vía %s" },
    pt: { prioUp: "Aumentar prioridade", prioDown: "Baixar prioridade", prioHint: "Ordem = prioridade. Arraste ou use as setas.", admBtn: "Administração", viaLocalhost: "via %s" },
    fr: { prioUp: "Augmenter la priorité", prioDown: "Baisser la priorité", prioHint: "Ordre = priorité. Glisser ou utiliser les flèches.", admBtn: "Administration", viaLocalhost: "via %s" },
    ru: { prioUp: "Повысить приоритет", prioDown: "Понизить приоритет", prioHint: "Порядок = приоритет. Перетащите или используйте стрелки.", admBtn: "Управление", viaLocalhost: "через %s" },
    ar: { prioUp: "رفع الأولوية", prioDown: "خفض الأولوية", prioHint: "الترتيب = الأولوية. اسحب أو استخدم الأسهم.", admBtn: "الإدارة", viaLocalhost: "عبر %s" },
    hi: { prioUp: "प्राथमिकता बढ़ाएँ", prioDown: "प्राथमिकता घटाएँ", prioHint: "क्रम = प्राथमिकता। खींचें या तीर इस्तेमाल करें।", admBtn: "प्रबंधन", viaLocalhost: "%s के ज़रिए" },
    ko: { prioUp: "우선순위 올리기", prioDown: "우선순위 내리기", prioHint: "순서 = 우선순위. 끌어서 옮기거나 화살표를 사용하세요.", admBtn: "관리", viaLocalhost: "%s 경유" },
    zh: { prioUp: "提高优先级", prioDown: "降低优先级", prioHint: "顺序即优先级。拖动或使用箭头。", admBtn: "管理", viaLocalhost: "经由 %s" },
    nl: { prioUp: "Prioriteit verhogen", prioDown: "Prioriteit verlagen", prioHint: "Volgorde = prioriteit. Sleep of gebruik de pijlen.", admBtn: "Beheer", viaLocalhost: "via %s" }
  };
  Object.keys(L2).forEach(function (k) { if (L[k]) Object.assign(L[k], L2[k]); });
  // Eigene Endpunkte, Verbinden per Kartenklick, Vorschau im Kurationsfenster (fold.js über AiAccess.text).
  var L3 = {
    de: { keyFirst: "Bitte zuerst den API-Schlüssel eingeben. Enter verbindet dann mit %s.", epLabel: "Weiterer Endpunkt (OpenAI-kompatibel)", epHint: "Basis-URL eingeben und Enter drücken. Der Endpunkt muss Anfragen aus dem Browser (CORS) erlauben.", epBad: "Bitte eine https://-Adresse angeben (http:// nur für localhost oder 127.0.0.1).", epCors: "%s ist nicht erreichbar oder erlaubt keine Anfragen aus dem Browser (CORS). Der Endpunkt muss Anfragen von dieser Seite zulassen.", epNoJson: "%s hat keine JSON-Antwort geliefert. Stimmt die Basis-URL (meist mit /v1 am Ende)?", epTag: "eigener Endpunkt", pvLocalOnly: "Die lokale Vorschau läuft nur mit _src/serve.py. Wähle ein Modell mit eigenem Schlüssel.", pvNotJson: "Der Server hat keine JSON-Antwort geliefert.", pvEmpty: "Das Modell hat keinen Text geliefert.", pvNoModels: "Kein KI-Modell verfügbar" },
    en: { keyFirst: "Enter your API key first. Enter then connects to %s.", epLabel: "Other endpoint (OpenAI-compatible)", epHint: "Enter the base URL and press Enter. The endpoint must allow requests from the browser (CORS).", epBad: "Please enter an https:// address (http:// only for localhost or 127.0.0.1).", epCors: "%s cannot be reached or does not allow requests from the browser (CORS). The endpoint must accept requests from this site.", epNoJson: "%s did not return JSON. Is the base URL right (usually ending in /v1)?", epTag: "own endpoint", pvLocalOnly: "The local preview only runs with _src/serve.py. Choose a model with your own key.", pvNotJson: "The server did not return a JSON response.", pvEmpty: "The model returned no text.", pvNoModels: "No AI model available" },
    es: { keyFirst: "Introduce primero tu clave de API. Después, Intro conecta con %s.", epLabel: "Otro endpoint (compatible con OpenAI)", epHint: "Introduce la URL base y pulsa Intro. El endpoint debe permitir solicitudes desde el navegador (CORS).", epBad: "Indica una dirección https:// (http:// solo para localhost o 127.0.0.1).", epCors: "%s no está accesible o no permite solicitudes desde el navegador (CORS). El endpoint debe aceptar solicitudes de este sitio.", epNoJson: "%s no ha devuelto JSON. ¿Es correcta la URL base (normalmente termina en /v1)?", epTag: "endpoint propio", pvLocalOnly: "La vista previa local solo funciona con _src/serve.py. Elige un modelo con tu propia clave.", pvNotJson: "El servidor no ha devuelto una respuesta JSON.", pvEmpty: "El modelo no ha devuelto texto.", pvNoModels: "Ningún modelo de IA disponible" },
    pt: { keyFirst: "Digite primeiro sua chave de API. Depois, Enter conecta com %s.", epLabel: "Outro endpoint (compatível com OpenAI)", epHint: "Digite a URL base e pressione Enter. O endpoint precisa permitir solicitações do navegador (CORS).", epBad: "Informe um endereço https:// (http:// só para localhost ou 127.0.0.1).", epCors: "%s não está acessível ou não permite solicitações do navegador (CORS). O endpoint precisa aceitar solicitações deste site.", epNoJson: "%s não retornou JSON. A URL base está correta (geralmente termina em /v1)?", epTag: "endpoint próprio", pvLocalOnly: "A prévia local só funciona com _src/serve.py. Escolha um modelo com sua própria chave.", pvNotJson: "O servidor não retornou uma resposta JSON.", pvEmpty: "O modelo não retornou texto.", pvNoModels: "Nenhum modelo de IA disponível" },
    fr: { keyFirst: "Saisissez d'abord votre clé API. Entrée connecte ensuite à %s.", epLabel: "Autre point de terminaison (compatible OpenAI)", epHint: "Saisissez l'URL de base et appuyez sur Entrée. Le point de terminaison doit autoriser les requêtes du navigateur (CORS).", epBad: "Indiquez une adresse https:// (http:// uniquement pour localhost ou 127.0.0.1).", epCors: "%s est injoignable ou n'autorise pas les requêtes du navigateur (CORS). Le point de terminaison doit accepter les requêtes de ce site.", epNoJson: "%s n'a pas renvoyé de JSON. L'URL de base est-elle correcte (généralement terminée par /v1) ?", epTag: "point de terminaison personnel", pvLocalOnly: "L'aperçu local ne fonctionne qu'avec _src/serve.py. Choisissez un modèle avec votre propre clé.", pvNotJson: "Le serveur n'a pas renvoyé de réponse JSON.", pvEmpty: "Le modèle n'a renvoyé aucun texte.", pvNoModels: "Aucun modèle d'IA disponible" },
    ru: { keyFirst: "Сначала введите API-ключ. Затем Enter подключит %s.", epLabel: "Другой эндпоинт (совместимый с OpenAI)", epHint: "Введите базовый URL и нажмите Enter. Эндпоинт должен разрешать запросы из браузера (CORS).", epBad: "Укажите адрес https:// (http:// только для localhost или 127.0.0.1).", epCors: "%s недоступен или не разрешает запросы из браузера (CORS). Эндпоинт должен принимать запросы с этого сайта.", epNoJson: "%s не вернул JSON. Верен ли базовый URL (обычно оканчивается на /v1)?", epTag: "собственный эндпоинт", pvLocalOnly: "Локальный предпросмотр работает только с _src/serve.py. Выберите модель с собственным ключом.", pvNotJson: "Сервер не вернул ответ в формате JSON.", pvEmpty: "Модель не вернула текст.", pvNoModels: "Нет доступной модели ИИ" },
    ar: { keyFirst: "أدخل مفتاح API أولًا، ثم يتصل Enter بـ %s.", epLabel: "نقطة نهاية أخرى (متوافقة مع OpenAI)", epHint: "أدخل عنوان URL الأساسي واضغط Enter. يجب أن تسمح نقطة النهاية بالطلبات من المتصفح (CORS).", epBad: "أدخل عنوانًا يبدأ بـ https:// (يُسمح بـ http:// فقط لـ localhost أو 127.0.0.1).", epCors: "لا يمكن الوصول إلى %s أو أنه لا يسمح بالطلبات من المتصفح (CORS). يجب أن تقبل نقطة النهاية الطلبات من هذا الموقع.", epNoJson: "لم يُرجع %s استجابة JSON. هل عنوان URL الأساسي صحيح (ينتهي عادةً بـ /v1)؟", epTag: "نقطة نهاية خاصة", pvLocalOnly: "المعاينة المحلية تعمل فقط مع _src/serve.py. اختر نموذجًا بمفتاحك الخاص.", pvNotJson: "لم يُرجع الخادم استجابة JSON.", pvEmpty: "لم يُرجع النموذج أي نص.", pvNoModels: "لا يتوفر نموذج ذكاء اصطناعي" },
    hi: { keyFirst: "पहले अपनी API कुंजी दर्ज करें। फिर Enter %s से जोड़ देगा।", epLabel: "अन्य एंडपॉइंट (OpenAI-संगत)", epHint: "बेस URL दर्ज करें और Enter दबाएँ। एंडपॉइंट को ब्राउज़र से आने वाले अनुरोध (CORS) स्वीकार करने चाहिए।", epBad: "कृपया https:// पता दें (http:// केवल localhost या 127.0.0.1 के लिए)।", epCors: "%s तक पहुँचा नहीं जा सकता या वह ब्राउज़र से अनुरोध (CORS) की अनुमति नहीं देता। एंडपॉइंट को इस साइट से अनुरोध स्वीकार करने चाहिए।", epNoJson: "%s ने JSON नहीं लौटाया। क्या बेस URL सही है (आमतौर पर /v1 पर खत्म होता है)?", epTag: "अपना एंडपॉइंट", pvLocalOnly: "स्थानीय पूर्वावलोकन केवल _src/serve.py के साथ चलता है। अपनी कुंजी वाला मॉडल चुनें।", pvNotJson: "सर्वर ने JSON उत्तर नहीं लौटाया।", pvEmpty: "मॉडल ने कोई टेक्स्ट नहीं लौटाया।", pvNoModels: "कोई AI मॉडल उपलब्ध नहीं" },
    ko: { keyFirst: "먼저 API 키를 입력하세요. 그런 다음 Enter를 누르면 %s에 연결됩니다.", epLabel: "다른 엔드포인트(OpenAI 호환)", epHint: "기본 URL을 입력하고 Enter를 누르세요. 엔드포인트는 브라우저 요청(CORS)을 허용해야 합니다.", epBad: "https:// 주소를 입력하세요(http://는 localhost 또는 127.0.0.1만 허용).", epCors: "%s에 연결할 수 없거나 브라우저 요청(CORS)을 허용하지 않습니다. 엔드포인트가 이 사이트의 요청을 허용해야 합니다.", epNoJson: "%s이(가) JSON을 반환하지 않았습니다. 기본 URL이 맞나요(보통 /v1로 끝남)?", epTag: "자체 엔드포인트", pvLocalOnly: "로컬 미리보기는 _src/serve.py에서만 동작합니다. 본인 키가 있는 모델을 선택하세요.", pvNotJson: "서버가 JSON 응답을 반환하지 않았습니다.", pvEmpty: "모델이 텍스트를 반환하지 않았습니다.", pvNoModels: "사용 가능한 AI 모델 없음" },
    zh: { keyFirst: "请先输入 API 密钥，然后按 Enter 连接 %s。", epLabel: "其他端点（兼容 OpenAI）", epHint: "输入基础 URL 并按 Enter。该端点必须允许来自浏览器的请求（CORS）。", epBad: "请填写 https:// 地址（http:// 仅限 localhost 或 127.0.0.1）。", epCors: "无法访问 %s，或它不允许来自浏览器的请求（CORS）。该端点必须接受来自本网站的请求。", epNoJson: "%s 未返回 JSON。基础 URL 是否正确（通常以 /v1 结尾）？", epTag: "自有端点", pvLocalOnly: "本地预览只能配合 _src/serve.py 使用。请选择使用自有密钥的模型。", pvNotJson: "服务器未返回 JSON 响应。", pvEmpty: "模型没有返回文本。", pvNoModels: "没有可用的 AI 模型" },
    nl: { keyFirst: "Vul eerst je API-sleutel in. Enter koppelt daarna met %s.", epLabel: "Ander endpoint (OpenAI-compatibel)", epHint: "Vul de basis-URL in en druk op Enter. Het endpoint moet verzoeken vanuit de browser (CORS) toestaan.", epBad: "Geef een https://-adres op (http:// alleen voor localhost of 127.0.0.1).", epCors: "%s is niet bereikbaar of staat geen verzoeken vanuit de browser toe (CORS). Het endpoint moet verzoeken van deze site accepteren.", epNoJson: "%s gaf geen JSON terug. Klopt de basis-URL (meestal eindigend op /v1)?", epTag: "eigen endpoint", pvLocalOnly: "De lokale voorvertoning werkt alleen met _src/serve.py. Kies een model met je eigen sleutel.", pvNotJson: "De server gaf geen JSON-antwoord.", pvEmpty: "Het model gaf geen tekst terug.", pvNoModels: "Geen AI-model beschikbaar" }
  };
  Object.keys(L3).forEach(function (k) { if (L[k]) Object.assign(L[k], L3[k]); });
  // Verwaltung: als wer man handelt und wer anfragt (mehrere Verwalter, mehrere eigene Konten).
  var L4 = {
    de: { admActing: "Du verwaltest als: %s", admActingHint: "Entscheidungen werden unter dieser Anmeldung gespeichert. Weitere Verwalter sehen dieselben Anfragen.", admSelf: "(du selbst)", admReqBy: "Angefragt von", admGrantedBy: "freigegeben von %s", admGrantedBySelf: "von dir freigegeben" },
    en: { admActing: "You are managing as: %s", admActingHint: "Decisions are recorded under this sign-in. Other admins see the same requests.", admSelf: "(you)", admReqBy: "Requested by", admGrantedBy: "approved by %s", admGrantedBySelf: "approved by you" },
    es: { admActing: "Administras como: %s", admActingHint: "Las decisiones se guardan con este inicio de sesión. Los demás administradores ven las mismas solicitudes.", admSelf: "(tú)", admReqBy: "Solicitado por", admGrantedBy: "aprobado por %s", admGrantedBySelf: "aprobado por ti" },
    pt: { admActing: "Você administra como: %s", admActingHint: "As decisões são registradas com este login. Outros administradores veem as mesmas solicitações.", admSelf: "(você)", admReqBy: "Solicitado por", admGrantedBy: "aprovado por %s", admGrantedBySelf: "aprovado por você" },
    fr: { admActing: "Vous administrez en tant que : %s", admActingHint: "Les décisions sont enregistrées sous cette connexion. Les autres administrateurs voient les mêmes demandes.", admSelf: "(vous)", admReqBy: "Demandé par", admGrantedBy: "approuvé par %s", admGrantedBySelf: "approuvé par vous" },
    ru: { admActing: "Вы управляете как: %s", admActingHint: "Решения сохраняются под этим входом. Другие администраторы видят те же запросы.", admSelf: "(вы)", admReqBy: "Запросил(а)", admGrantedBy: "одобрено: %s", admGrantedBySelf: "одобрено вами" },
    ar: { admActing: "أنت تدير بصفتك: %s", admActingHint: "تُحفظ القرارات باسم تسجيل الدخول هذا. يرى المسؤولون الآخرون الطلبات نفسها.", admSelf: "(أنت)", admReqBy: "مقدَّم من", admGrantedBy: "وافق عليه %s", admGrantedBySelf: "وافقتَ عليه أنت" },
    hi: { admActing: "आप इस खाते से प्रबंधन कर रहे हैं: %s", admActingHint: "निर्णय इसी साइन-इन के साथ सहेजे जाते हैं। अन्य प्रबंधक वही अनुरोध देखते हैं।", admSelf: "(आप स्वयं)", admReqBy: "अनुरोधकर्ता", admGrantedBy: "%s द्वारा स्वीकृत", admGrantedBySelf: "आपके द्वारा स्वीकृत" },
    ko: { admActing: "관리 계정: %s", admActingHint: "결정은 이 로그인으로 기록됩니다. 다른 관리자도 같은 요청을 봅니다.", admSelf: "(본인)", admReqBy: "요청자", admGrantedBy: "승인자: %s", admGrantedBySelf: "내가 승인함" },
    zh: { admActing: "你当前的管理身份：%s", admActingHint: "决定将以此登录身份记录。其他管理员会看到相同的申请。", admSelf: "（你自己）", admReqBy: "申请人", admGrantedBy: "批准人：%s", admGrantedBySelf: "由你批准" },
    nl: { admActing: "Je beheert als: %s", admActingHint: "Beslissingen worden onder deze aanmelding vastgelegd. Andere beheerders zien dezelfde aanvragen.", admSelf: "(jijzelf)", admReqBy: "Aangevraagd door", admGrantedBy: "goedgekeurd door %s", admGrantedBySelf: "door jou goedgekeurd" }
  };
  Object.keys(L4).forEach(function (k) { if (L[k]) Object.assign(L[k], L4[k]); });
  // Projektkontingent über das Gemini-Abo des Verwalters (agy auf einem GitHub-Läufer); fehlende Sprachen nehmen Englisch.
  var L5 = {
    de: { aboLabel: "Projektkontingent · Gemini-Abo", aboSending: "Auftrag wird gesendet …",
          aboWait: "Wartet auf Läufer … %s", aboWaitBusy: "Wartet auf Läufer – er beantwortet gerade einen anderen Auftrag … %s",
          aboWaitStart: "Wartet auf Läufer – er wird gestartet (etwa 1–2 Minuten) … %s",
          aboWaitFailed: "Wartet auf Läufer – der Start ist fehlgeschlagen (GitHub HTTP %d) … %s",
          aboWaitNone: "Wartet auf Läufer – kein automatischer Start eingerichtet … %s", aboThinking: "Modell denkt … %s",
          aboErrExhausted: "Das Gemini-Abo ist auf beiden Profilen (leo, neo) gerade ausgeschöpft. Wieder frei in etwa %s.",
          aboErrLogin: "Das Gemini-Abo ist auf dem Läufer nicht angemeldet (leo, neo). Der Verwalter muss die Anmeldung erneuern.",
          aboErrNoRunner: "Es hat sich kein Läufer gemeldet; der Auftrag wurde nach 6 Minuten beendet. Bitte später erneut versuchen.",
          aboErrTimeout: "Keine Antwort vom Gemini-Abo innerhalb von 12 Minuten. Der Auftrag wurde abgebrochen.",
          aboErrDenied: "Das Modell wollte ein gesperrtes Werkzeug benutzen und hat keine Antwort geliefert. Bitte die Frage anders stellen.",
          aboErrModel: "Dieses Modell ist für das Gemini-Abo nicht freigegeben oder wird von agy nicht angeboten.",
          aboOnlyOwn: "Das Gemini-Abo ist nur für die eigenen Konten des Verwalters vorgesehen.",
          aboErrGrant: "Keine gültige Freigabe für das Gemini-Abo.", aboErrTooLarge: "Der Prompt ist für das Gemini-Abo zu lang (höchstens etwa 120 KB).",
          aboErrOff: "Das Gemini-Abo ist am Dienst noch nicht eingerichtet.",
          aboErrKey: "Dienst und Läufer haben verschiedene Schlüssel (ABO_RELAY_KEY). Der Verwalter muss sie angleichen.",
          aboErrCancelled: "Der Auftrag wurde abgebrochen.", aboErrOther: "Gemini-Abo: Fehler %s.",
          admBackend: "Backend", admBackendNexos: "Nexos (Projektschlüssel)", admBackendAbo: "Gemini-Abo (leo/neo)",
          admBackendAboOff: "Gemini-Abo (leo/neo) – nur für eigene Konten", admModelSel: "Modell",
          admModelAllNexos: "Alle Nexos-Modelle", admModelAllAbo: "Alle Gemini-Modelle des Abos", admModelAll: "alle Modelle",
          admAboHint: "Das Gemini-Abo läuft über agy auf einem GitHub-Läufer (Profile leo, neo). Antworten dauern 1–3 Minuten länger.",
          stAboActive: "aktiv bis %s · Gemini-Abo über agy (leo/neo)" },
    en: { aboLabel: "Project quota · Gemini subscription", aboSending: "Sending the job …",
          aboWait: "Waiting for the runner … %s", aboWaitBusy: "Waiting for the runner – it is answering another job … %s",
          aboWaitStart: "Waiting for the runner – it is starting (about 1–2 minutes) … %s",
          aboWaitFailed: "Waiting for the runner – starting it failed (GitHub HTTP %d) … %s",
          aboWaitNone: "Waiting for the runner – no automatic start configured … %s", aboThinking: "Model is thinking … %s",
          aboErrExhausted: "The Gemini subscription is exhausted on both profiles (leo, neo). Available again in about %s.",
          aboErrLogin: "The Gemini subscription is not signed in on the runner (leo, neo). The operator has to renew the sign-in.",
          aboErrNoRunner: "No runner reported in; the job was ended after 6 minutes. Please try again later.",
          aboErrTimeout: "No answer from the Gemini subscription within 12 minutes. The job was cancelled.",
          aboErrDenied: "The model tried to use a blocked tool and returned no answer. Please rephrase the question.",
          aboErrModel: "This model is not granted for the Gemini subscription or not offered by agy.",
          aboOnlyOwn: "The Gemini subscription is reserved for the operator's own accounts.",
          aboErrGrant: "No valid grant for the Gemini subscription.", aboErrTooLarge: "The prompt is too long for the Gemini subscription (at most about 120 KB).",
          aboErrOff: "The Gemini subscription is not set up on the service yet.",
          aboErrKey: "Service and runner use different keys (ABO_RELAY_KEY). The operator has to align them.",
          aboErrCancelled: "The job was cancelled.", aboErrOther: "Gemini subscription: error %s.",
          admBackend: "Backend", admBackendNexos: "Nexos (project key)", admBackendAbo: "Gemini subscription (leo/neo)",
          admBackendAboOff: "Gemini subscription (leo/neo) – own accounts only", admModelSel: "Model",
          admModelAllNexos: "All Nexos models", admModelAllAbo: "All Gemini models of the subscription", admModelAll: "all models",
          admAboHint: "The Gemini subscription runs through agy on a GitHub runner (profiles leo, neo). Answers take 1–3 minutes longer.",
          stAboActive: "active until %s · Gemini subscription via agy (leo/neo)" },
    es: { aboLabel: "Cuota del proyecto · suscripción Gemini" }, pt: { aboLabel: "Cota do projeto · assinatura Gemini" },
    fr: { aboLabel: "Quota du projet · abonnement Gemini" }, ru: { aboLabel: "Квота проекта · подписка Gemini" },
    ar: { aboLabel: "حصة المشروع · اشتراك Gemini" }, hi: { aboLabel: "प्रोजेक्ट कोटा · Gemini सदस्यता" },
    ko: { aboLabel: "프로젝트 할당량 · Gemini 구독" }, zh: { aboLabel: "项目额度 · Gemini 订阅" },
    nl: { aboLabel: "Projectquotum · Gemini-abonnement" }
  };
  Object.keys(L5).forEach(function (k) { if (L[k]) Object.assign(L[k], L5[k]); });
  // Reihenfolge per Griff (Maus, Finger, Pfeiltasten), Modellwahl je Abschnitt, lokale CLIs mit Ausweichliste,
  // Symbole im Kopf setzen ihre Quelle an Rang 1. Fehlende Sprachen nehmen Englisch.
  var L6 = {
    de: { prioHint: "Reihenfolge = Priorität: Es antwortet der oberste nutzbare Zugang. Am Griff ziehen oder mit den Pfeiltasten verschieben.",
          gripLabel: "%s verschieben, Rang %n",
          prioMoved: "%s jetzt an Rang %n von %t.", answersNow: "antwortet", secModel: "Modell",
          srcLocal: "Lokale KI-CLIs", srcProject: "Projektkontingent", srcByok: "Eigene Schlüssel",
          prioTop: "%s steht jetzt an Rang 1 und antwortet.", prioTopWait: "%s steht jetzt an Rang 1.",
          prioAlready: "%s steht schon an Rang 1.",
          prioUnhealthy: "%s ist gerade nicht nutzbar (%r). Die Reihenfolge bleibt; hier lässt es sich prüfen oder einrichten.",
          icoPromote: "Klick: an Rang 1 setzen",
          cliActive: "Aktive CLI", cliFallback: "Ausweichen, wenn das Kontingent erschöpft oder die CLI nicht erreichbar ist",
          cliFallbackNone: "– kein Ausweichen –", cliFallbackN: "Ausweich-CLI %s", cliFbShort: "Ausweich %s", cliDefaultModel: "Standardmodell",
          cliChecking: "Prüfe alle CLIs …", cliFoundN: "%n CLIs gefunden.", cliFound1: "1 CLI gefunden.",
          st_healthy: "bereit", st_unauthenticated: "nicht angemeldet", st_error: "Fehler", st_quota: "Kontingent erschöpft",
          st_unreachable: "nicht installiert", st_untested: "ungeprüft",
          kind_quota: "Kontingent erschöpft", kind_auth: "nicht angemeldet", kind_unavailable: "nicht erreichbar",
          kind_timeout: "Zeitüberschreitung", kind_error: "Fehler",
          answeredInstead: "statt %s: %r", fallbackNow: "%s: %r – %t antwortet …" },
    en: { prioHint: "Order = priority: the topmost usable access answers. Drag by the handle or move with the arrow keys.",
          gripLabel: "Move %s, rank %n",
          prioMoved: "%s is now rank %n of %t.", answersNow: "answers", secModel: "Model",
          srcLocal: "Local AI CLIs", srcProject: "Project quota", srcByok: "Own keys",
          prioTop: "%s is now rank 1 and answers.", prioTopWait: "%s is now rank 1.",
          prioAlready: "%s is already rank 1.",
          prioUnhealthy: "%s is not usable right now (%r). The order stays; you can check or set it up here.",
          icoPromote: "Click: make rank 1",
          cliActive: "Active CLI", cliFallback: "Fall back when the quota is used up or the CLI cannot be reached",
          cliFallbackNone: "– no fallback –", cliFallbackN: "Fallback CLI %s", cliFbShort: "fallback %s", cliDefaultModel: "default model",
          cliChecking: "Checking all CLIs …", cliFoundN: "%n CLIs found.", cliFound1: "1 CLI found.",
          st_healthy: "ready", st_unauthenticated: "not signed in", st_error: "error", st_quota: "quota used up",
          st_unreachable: "not installed", st_untested: "not checked",
          kind_quota: "quota used up", kind_auth: "not signed in", kind_unavailable: "not reachable",
          kind_timeout: "timed out", kind_error: "error",
          answeredInstead: "instead of %s: %r", fallbackNow: "%s: %r – %t answers …" },
    es: { prioHint: "Orden = prioridad: responde el primer acceso utilizable. Arrastra por el asa o muévelo con las flechas.",
          answersNow: "responde", secModel: "Modelo", cliActive: "CLI activa", icoPromote: "Clic: poner en el puesto 1" },
    pt: { prioHint: "Ordem = prioridade: responde o primeiro acesso utilizável. Arraste pela alça ou mova com as setas.",
          answersNow: "responde", secModel: "Modelo", cliActive: "CLI ativa", icoPromote: "Clique: colocar em 1º" },
    fr: { prioHint: "Ordre = priorité : le premier accès utilisable répond. Glisser par la poignée ou déplacer avec les flèches.",
          answersNow: "répond", secModel: "Modèle", cliActive: "CLI active", icoPromote: "Clic : mettre au rang 1" },
    ru: { prioHint: "Порядок = приоритет: отвечает первый доступный вариант. Перетащите за ручку или используйте стрелки.",
          answersNow: "отвечает", secModel: "Модель", cliActive: "Активный CLI", icoPromote: "Щелчок: на первое место" },
    ar: { prioHint: "الترتيب = الأولوية: يجيب أول وصول قابل للاستخدام. اسحب من المقبض أو حرّك بمفاتيح الأسهم.",
          answersNow: "يجيب", secModel: "النموذج", cliActive: "واجهة CLI النشطة", icoPromote: "انقر: إلى المرتبة 1" },
    hi: { prioHint: "क्रम = प्राथमिकता: सबसे ऊपर का उपयोगी एक्सेस जवाब देता है। हैंडल से खींचें या तीर कुंजियों से खिसकाएँ।",
          answersNow: "जवाब देता है", secModel: "मॉडल", cliActive: "सक्रिय CLI", icoPromote: "क्लिक: पहले स्थान पर" },
    ko: { prioHint: "순서 = 우선순위: 사용 가능한 맨 위 항목이 답합니다. 손잡이를 끌거나 화살표 키로 옮기세요.",
          answersNow: "응답", secModel: "모델", cliActive: "활성 CLI", icoPromote: "클릭: 1순위로" },
    zh: { prioHint: "顺序即优先级：由最上方可用的访问方式回答。拖动手柄或用方向键移动。",
          answersNow: "回答", secModel: "模型", cliActive: "当前 CLI", icoPromote: "点击：设为第 1 位" },
    nl: { prioHint: "Volgorde = prioriteit: de bovenste bruikbare toegang antwoordt. Sleep aan de greep of verplaats met de pijltjestoetsen.",
          answersNow: "antwoordt", secModel: "Model", cliActive: "Actieve CLI", icoPromote: "Klik: naar plek 1" }
  };
  Object.keys(L6).forEach(function (k) { if (L[k]) Object.assign(L[k], L6[k]); });
  // Mehrere Platzhalter: %s, %n, %t, %r der Reihe nach aus vals.
  function trf(key, vals) {
    var s = tr(key);
    Object.keys(vals || {}).forEach(function (k) { s = s.split("%" + k).join(String(vals[k])); });
    return s;
  }
  // Leser-Feedback: Sichtung in der Verwaltung und Stand der eigenen Meldungen (review.js liest sie über AiAccess.text).
  var L7 = {
    de: { fbAdmTitle: "Eingegangenes Feedback", fbAdmLead: "Meldungen von Leserinnen und Lesern. Fehler und Hinweise prüft zusätzlich der Prüf-Agent als Befund; hier setzt du den Stand und kannst der meldenden Person antworten.", fbAdmNone: "Nichts Offenes.", fbAdmBtn: "Feedback sichten", fbAdmNew: "%s neu", fbAdmStatus: "Stand", fbAdmNote: "Antwort (sieht die meldende Person unter „Meine Meldungen“)", fbAdmDel: "Löschen", fbAdmShowOpen: "Offen", fbAdmShowAll: "Alle", fbAdmSwitch: "Melden über die Website", fbAdmOpen: "Melden erlaubt", fbAdmAnon: "auch ohne Anmeldung", fbAdmSwitchHint: "Gilt sofort für alle Besucher (Firestore-Regeln). Abschalten, wenn Spam eingeht.", fbAdmContact: "Antwort erwünscht an", fbAdmFinding: "Befund", fbAdmSaved: "Gespeichert.", fbKonto: "Konto", fbAnon: "ohne Anmeldung", fbSt_neu: "Neu", fbSt_in_pruefung: "In Prüfung", fbSt_erledigt: "Erledigt", fbSt_verworfen: "Verworfen", fbArt_hinweis: "Hinweis", fbArt_fehler: "Fehler", fbArt_wunsch: "Wunsch" },
    en: { fbAdmTitle: "Incoming feedback", fbAdmLead: "Reports from readers. The review agent also checks errors and notes as findings; here you set the state and can reply to the reporter.", fbAdmNone: "Nothing open.", fbAdmBtn: "Review feedback", fbAdmNew: "%s new", fbAdmStatus: "State", fbAdmNote: "Reply (the reporter sees it under “My reports”)", fbAdmDel: "Delete", fbAdmShowOpen: "Open", fbAdmShowAll: "All", fbAdmSwitch: "Reporting through the website", fbAdmOpen: "Reporting allowed", fbAdmAnon: "also without signing in", fbAdmSwitchHint: "Applies immediately to all visitors (Firestore rules). Switch off if spam arrives.", fbAdmContact: "Reply requested to", fbAdmFinding: "Finding", fbAdmSaved: "Saved.", fbKonto: "Account", fbAnon: "not signed in", fbSt_neu: "New", fbSt_in_pruefung: "Under review", fbSt_erledigt: "Done", fbSt_verworfen: "Dismissed", fbArt_hinweis: "Note", fbArt_fehler: "Error", fbArt_wunsch: "Suggestion" },
    es: { fbAdmTitle: "Comentarios recibidos", fbAdmLead: "Avisos de lectores. El agente revisor también comprueba errores y observaciones como hallazgos; aquí fijas el estado y puedes responder a quien informó.", fbAdmNone: "Nada pendiente.", fbAdmBtn: "Revisar comentarios", fbAdmNew: "%s nuevos", fbAdmStatus: "Estado", fbAdmNote: "Respuesta (la persona la ve en «Mis avisos»)", fbAdmDel: "Eliminar", fbAdmShowOpen: "Abiertos", fbAdmShowAll: "Todos", fbAdmSwitch: "Avisos a través del sitio web", fbAdmOpen: "Avisos permitidos", fbAdmAnon: "también sin iniciar sesión", fbAdmSwitchHint: "Se aplica de inmediato a todos los visitantes (reglas de Firestore). Desactívalo si llega spam.", fbAdmContact: "Respuesta solicitada a", fbAdmFinding: "Hallazgo", fbAdmSaved: "Guardado.", fbKonto: "Cuenta", fbAnon: "sin iniciar sesión", fbSt_neu: "Nuevo", fbSt_in_pruefung: "En revisión", fbSt_erledigt: "Resuelto", fbSt_verworfen: "Descartado", fbArt_hinweis: "Observación", fbArt_fehler: "Error", fbArt_wunsch: "Sugerencia" },
    pt: { fbAdmTitle: "Feedback recebido", fbAdmLead: "Relatos de leitores. O agente revisor também verifica erros e observações como achados; aqui você define o estado e pode responder a quem relatou.", fbAdmNone: "Nada em aberto.", fbAdmBtn: "Revisar feedback", fbAdmNew: "%s novos", fbAdmStatus: "Estado", fbAdmNote: "Resposta (a pessoa vê em “Meus relatos”)", fbAdmDel: "Excluir", fbAdmShowOpen: "Abertos", fbAdmShowAll: "Todos", fbAdmSwitch: "Relatos pelo site", fbAdmOpen: "Relatos permitidos", fbAdmAnon: "também sem login", fbAdmSwitchHint: "Vale imediatamente para todos os visitantes (regras do Firestore). Desative se chegar spam.", fbAdmContact: "Resposta desejada para", fbAdmFinding: "Achado", fbAdmSaved: "Salvo.", fbKonto: "Conta", fbAnon: "sem login", fbSt_neu: "Novo", fbSt_in_pruefung: "Em análise", fbSt_erledigt: "Concluído", fbSt_verworfen: "Descartado", fbArt_hinweis: "Observação", fbArt_fehler: "Erro", fbArt_wunsch: "Sugestão" },
    fr: { fbAdmTitle: "Retours reçus", fbAdmLead: "Signalements des lecteurs. L'agent de contrôle vérifie aussi les erreurs et remarques comme constats ; ici vous fixez l'état et pouvez répondre à la personne.", fbAdmNone: "Rien en attente.", fbAdmBtn: "Examiner les retours", fbAdmNew: "%s nouveaux", fbAdmStatus: "État", fbAdmNote: "Réponse (visible par la personne sous « Mes signalements »)", fbAdmDel: "Supprimer", fbAdmShowOpen: "Ouverts", fbAdmShowAll: "Tous", fbAdmSwitch: "Signalement via le site", fbAdmOpen: "Signalement autorisé", fbAdmAnon: "aussi sans connexion", fbAdmSwitchHint: "S'applique immédiatement à tous les visiteurs (règles Firestore). À désactiver en cas de spam.", fbAdmContact: "Réponse souhaitée à", fbAdmFinding: "Constat", fbAdmSaved: "Enregistré.", fbKonto: "Compte", fbAnon: "sans connexion", fbSt_neu: "Nouveau", fbSt_in_pruefung: "En examen", fbSt_erledigt: "Traité", fbSt_verworfen: "Écarté", fbArt_hinweis: "Remarque", fbArt_fehler: "Erreur", fbArt_wunsch: "Souhait" },
    ru: { fbAdmTitle: "Поступившие отзывы", fbAdmLead: "Сообщения читателей. Агент проверки также проверяет ошибки и замечания как находки; здесь вы задаёте статус и можете ответить автору.", fbAdmNone: "Открытых нет.", fbAdmBtn: "Разобрать отзывы", fbAdmNew: "новых: %s", fbAdmStatus: "Статус", fbAdmNote: "Ответ (автор увидит его в «Мои сообщения»)", fbAdmDel: "Удалить", fbAdmShowOpen: "Открытые", fbAdmShowAll: "Все", fbAdmSwitch: "Сообщения через сайт", fbAdmOpen: "Сообщения разрешены", fbAdmAnon: "в том числе без входа", fbAdmSwitchHint: "Действует сразу для всех посетителей (правила Firestore). Отключите при спаме.", fbAdmContact: "Ответ нужен по адресу", fbAdmFinding: "Находка", fbAdmSaved: "Сохранено.", fbKonto: "Аккаунт", fbAnon: "без входа", fbSt_neu: "Новое", fbSt_in_pruefung: "На проверке", fbSt_erledigt: "Решено", fbSt_verworfen: "Отклонено", fbArt_hinweis: "Замечание", fbArt_fehler: "Ошибка", fbArt_wunsch: "Пожелание" },
    ar: { fbAdmTitle: "الملاحظات الواردة", fbAdmLead: "بلاغات من القرّاء. يفحص وكيل المراجعة أيضًا الأخطاء والملاحظات كنتائج؛ هنا تحدد الحالة ويمكنك الرد على المُبلِّغ.", fbAdmNone: "لا شيء مفتوح.", fbAdmBtn: "مراجعة الملاحظات", fbAdmNew: "%s جديدة", fbAdmStatus: "الحالة", fbAdmNote: "الرد (يراه المُبلِّغ في «بلاغاتي»)", fbAdmDel: "حذف", fbAdmShowOpen: "مفتوحة", fbAdmShowAll: "الكل", fbAdmSwitch: "الإبلاغ عبر الموقع", fbAdmOpen: "الإبلاغ مسموح", fbAdmAnon: "حتى بدون تسجيل الدخول", fbAdmSwitchHint: "يسري فورًا على جميع الزوار (قواعد Firestore). أوقفه عند وصول رسائل مزعجة.", fbAdmContact: "الرد مطلوب إلى", fbAdmFinding: "نتيجة", fbAdmSaved: "تم الحفظ.", fbKonto: "حساب", fbAnon: "بدون تسجيل دخول", fbSt_neu: "جديد", fbSt_in_pruefung: "قيد المراجعة", fbSt_erledigt: "مُنجَز", fbSt_verworfen: "مرفوض", fbArt_hinweis: "ملاحظة", fbArt_fehler: "خطأ", fbArt_wunsch: "اقتراح" },
    hi: { fbAdmTitle: "प्राप्त फ़ीडबैक", fbAdmLead: "पाठकों की रिपोर्टें। समीक्षा एजेंट गलतियों और टिप्पणियों को निष्कर्ष के रूप में भी जाँचता है; यहाँ आप स्थिति तय करते हैं और रिपोर्ट करने वाले को उत्तर दे सकते हैं।", fbAdmNone: "कुछ भी लंबित नहीं।", fbAdmBtn: "फ़ीडबैक देखें", fbAdmNew: "%s नए", fbAdmStatus: "स्थिति", fbAdmNote: "उत्तर (रिपोर्ट करने वाला इसे “मेरी रिपोर्टें” में देखता है)", fbAdmDel: "हटाएँ", fbAdmShowOpen: "खुले", fbAdmShowAll: "सभी", fbAdmSwitch: "वेबसाइट से रिपोर्ट करना", fbAdmOpen: "रिपोर्ट करने की अनुमति", fbAdmAnon: "बिना साइन इन के भी", fbAdmSwitchHint: "सभी आगंतुकों पर तुरंत लागू (Firestore नियम)। स्पैम आने पर बंद करें।", fbAdmContact: "उत्तर यहाँ चाहिए", fbAdmFinding: "निष्कर्ष", fbAdmSaved: "सहेजा गया।", fbKonto: "खाता", fbAnon: "बिना साइन इन", fbSt_neu: "नया", fbSt_in_pruefung: "समीक्षा में", fbSt_erledigt: "पूर्ण", fbSt_verworfen: "अस्वीकृत", fbArt_hinweis: "टिप्पणी", fbArt_fehler: "त्रुटि", fbArt_wunsch: "सुझाव" },
    ko: { fbAdmTitle: "받은 피드백", fbAdmLead: "독자의 신고입니다. 검토 에이전트도 오류와 의견을 발견 사항으로 확인합니다. 여기서 상태를 정하고 신고자에게 답할 수 있습니다.", fbAdmNone: "열린 항목이 없습니다.", fbAdmBtn: "피드백 검토", fbAdmNew: "새 항목 %s개", fbAdmStatus: "상태", fbAdmNote: "답변(신고자가 ‘내 신고’에서 봅니다)", fbAdmDel: "삭제", fbAdmShowOpen: "열림", fbAdmShowAll: "전체", fbAdmSwitch: "웹사이트를 통한 신고", fbAdmOpen: "신고 허용", fbAdmAnon: "로그인 없이도", fbAdmSwitchHint: "모든 방문자에게 즉시 적용됩니다(Firestore 규칙). 스팸이 오면 끄세요.", fbAdmContact: "답변 받을 곳", fbAdmFinding: "발견 사항", fbAdmSaved: "저장했습니다.", fbKonto: "계정", fbAnon: "로그인 안 함", fbSt_neu: "새 항목", fbSt_in_pruefung: "검토 중", fbSt_erledigt: "완료", fbSt_verworfen: "기각", fbArt_hinweis: "의견", fbArt_fehler: "오류", fbArt_wunsch: "제안" },
    zh: { fbAdmTitle: "收到的反馈", fbAdmLead: "读者的报告。审查代理也会把错误和意见作为发现进行核查；你在这里设置状态，并可以回复报告者。", fbAdmNone: "没有待处理项。", fbAdmBtn: "查看反馈", fbAdmNew: "%s 条新反馈", fbAdmStatus: "状态", fbAdmNote: "回复（报告者可在“我的报告”中看到）", fbAdmDel: "删除", fbAdmShowOpen: "未处理", fbAdmShowAll: "全部", fbAdmSwitch: "通过网站报告", fbAdmOpen: "允许报告", fbAdmAnon: "未登录也可以", fbAdmSwitchHint: "立即对所有访客生效（Firestore 规则）。收到垃圾信息时请关闭。", fbAdmContact: "希望回复至", fbAdmFinding: "发现", fbAdmSaved: "已保存。", fbKonto: "账号", fbAnon: "未登录", fbSt_neu: "新", fbSt_in_pruefung: "审查中", fbSt_erledigt: "已完成", fbSt_verworfen: "已驳回", fbArt_hinweis: "意见", fbArt_fehler: "错误", fbArt_wunsch: "建议" },
    nl: { fbAdmTitle: "Ontvangen feedback", fbAdmLead: "Meldingen van lezers. De controle-agent controleert fouten en opmerkingen ook als bevinding; hier stel je de status in en kun je de melder antwoorden.", fbAdmNone: "Niets open.", fbAdmBtn: "Feedback bekijken", fbAdmNew: "%s nieuw", fbAdmStatus: "Status", fbAdmNote: "Antwoord (de melder ziet het onder ‘Mijn meldingen’)", fbAdmDel: "Verwijderen", fbAdmShowOpen: "Open", fbAdmShowAll: "Alle", fbAdmSwitch: "Melden via de website", fbAdmOpen: "Melden toegestaan", fbAdmAnon: "ook zonder aanmelden", fbAdmSwitchHint: "Geldt meteen voor alle bezoekers (Firestore-regels). Uitzetten bij spam.", fbAdmContact: "Antwoord gewenst aan", fbAdmFinding: "Bevinding", fbAdmSaved: "Opgeslagen.", fbKonto: "Account", fbAnon: "niet aangemeld", fbSt_neu: "Nieuw", fbSt_in_pruefung: "In behandeling", fbSt_erledigt: "Afgehandeld", fbSt_verworfen: "Verworpen", fbArt_hinweis: "Opmerking", fbArt_fehler: "Fout", fbArt_wunsch: "Wens" }
  };
  Object.keys(L7).forEach(function (k) { if (L[k]) Object.assign(L[k], L7[k]); });
  function tr(key, arg) {
    var d = L[lang()] || L.en;
    var s = d[key] != null ? d[key] : (L.en[key] != null ? L.en[key] : key);
    return arg == null ? s : s.replace("%s", arg).replace("%n", arg);
  }

  // --------------------------------------------------------------- Helfer
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function store(kind) {
    try { return kind === "session" ? root.sessionStorage : root.localStorage; } catch (e) { return null; }
  }
  function sget(kind, key) { var s = store(kind); try { return s ? s.getItem(key) : null; } catch (e) { return null; } }
  function sset(kind, key, val) {
    var s = store(kind);
    try { if (!s) return; if (val == null) s.removeItem(key); else s.setItem(key, val); } catch (e) { /* voll/gesperrt */ }
  }
  function isLocalHost() {
    var loc = root.location || {};
    return loc.protocol === "file:" || /^(localhost|127\.0\.0\.1|\[::1\]|::1)$/.test(loc.hostname || "");
  }
  function emit() {
    try { root.dispatchEvent(new CustomEvent("aiaccess-change", { detail: snapshot() })); } catch (e) { /* alt */ }
    renderHeader();
    if ((dlg && dlg.open) || (sub && sub.open)) renderDialog();
  }

  // ------------------------------------------------------------- Prompt
  // Wortgleich mit _build_discuss_prompt / _extract_finding_from_reply in
  // _src/tools/ai_discuss.py (Paritätstest: _src/tests/test_ai_access_js.py).
  function cp(s, n) { return Array.from(String(s)).slice(0, n).join(""); }
  function clen(s) { return Array.from(s).length; }
  function pyStrip(s) { return String(s).replace(/^\s+|\s+$/g, ""); }
  function buildDiscussPrompt(message, context) {
    context = context || {};
    var recId = context.record_id != null ? context.record_id : "";
    var univ = context.universe != null ? context.universe : "AUTOSAR Classic";
    var mod = context.module != null ? context.module : "";
    var reqText = cp(context.requirement_text || "", 4000);
    var diagramText = cp(context.diagram_text || "", 2000);
    var cites = (context.cited_references || []).map(function (c) {
      return String((c && (c.id || c.document)) || "");
    }).join(", ");
    var parts = [
      "Du bist der AUTOSAR-KI-Experte im Dokumentationsportal Autodocs.",
      "Der Benutzer diskutiert mit dir über folgenden Kontext:",
      "- ID / Element: " + recId,
      "- Universum: " + univ,
      "- Modul / Cluster: " + mod,
      "- Inhalt / Spezifikation / Guide:\n" + reqText
    ];
    if (diagramText) parts.push("- Sequenzdiagramm-Schritte:\n" + diagramText);
    if (cites) parts.push("- Referenzen: " + cites);
    var others = (context.attached_items || []).filter(function (it) {
      return it && typeof it === "object" && it.record_id && it.record_id !== recId;
    });
    if (others.length) {
      var budget = 12000;
      var lines = ["- Weitere " + others.length + " Elemente im Fokus der Diskussion:"];
      for (var i = 0; i < others.length; i++) {
        var it = others[i];
        var text = String(it.requirement_text || "").split(/\s+/).filter(Boolean).join(" ");
        var entry = "  * " + it.record_id + ": " + cp(text, 900);
        if (budget - clen(entry) < 0) {
          lines.push("  * … weitere " + (others.length - (lines.length - 1)) + " Elemente aus Platzgründen nur mit ID: " +
            others.slice(lines.length - 1).map(function (o) { return String(o.record_id); }).join(", "));
          break;
        }
        budget -= clen(entry);
        lines.push(entry);
      }
      parts.push(lines.join("\n"));
    }
    parts.push(
      "",
      "Benutzer-Nachricht:\n\"" + pyStrip(message) + "\"",
      "",
      "Instruktionen für deine Antwort:",
      "1. Antworte fachlich fundiert, sachlich, präzise und auf Deutsch.",
      "2. Beantworte Fragen offen und direkt: Erkläre Zusammenhänge, zeige Abhängigkeiten auf oder erläutere SWS-Anforderungen.",
      "3. Keine Einengung / kein Tunnelblick auf Fehlersuche: Ein Gespräch kann eine reine Wissensabfrage, Architekturerklärung, Validierung oder ein allgemeiner technischer Diskurs sein.",
      "4. Eskalation in ein Review-Finding: Falls der Nutzer explizit ein Review-Finding wünscht (z. B. 'Leg das als Finding an', 'Eskalieren', 'Erstelle ein Review-Ticket') ODER wenn sich im Dialog ein tatsächlicher, belegbarer Fehler oder eine Inkonsistenz in der Dokumentation/im Diagramm herausstellt und du eine formale Korrektur für geboten hältst, formuliere am Ende deiner Antwort einen strukturierten Block:",
      "   [REVIEW-FINDING]",
      "   Titel: <Kurzer, präziser Titel des Befunds>",
      "   Schweregrad: <Kritisch | Mittel | Niedrig | Hinweis>",
      "   Betroffenes Element: <ID / Modul / Diagrammschritt>",
      "   Befund & Begründung: <Konkrete Abweichung zur SWS-Norm>",
      "   Empfohlene Korrektur: <Konkreter Änderungsvorschlag>",
      "   [ENDE-REVIEW-FINDING]",
      "   Dieser Block wird vom System automatisch erkannt und dem Nutzer als 1-Klick-Aktion 'Als Review-Finding anlegen' angeboten.",
      "5. Formatiere die Antwort übersichtlich in 2-4 Absätzen oder Aufzählungspunkten."
    );
    return parts.join("\n");
  }
  var FINDING_RE = /\[REVIEW-FINDING\]([\s\S]*?)\[(?:ENDE-REVIEW-FINDING|\/REVIEW-FINDING)\]/i;
  var COMPLAINT_WORDS = ["finding", "review-ticket", "ticket", "eskalier", "falsch", "korrektur", "fehler", "mangel",
                         "ändern", "ausschließen", "entfernen", "stimmt nicht"];
  function extractFinding(out, message, recId) {
    var m = FINDING_RE.exec(out || "");
    var lower = String(message || "").toLowerCase();
    if (m) {
      var raw = pyStrip(m[1]);
      return {
        suggestion: "[REVIEW-FINDING für " + recId + "]\n" + raw,
        rationale: "Als Review-Finding im KI-Diskurs eskaliert: " + cp(pyStrip(message), 200),
        finding: { title: "Review-Finding: " + recId, body: raw, target: recId }
      };
    }
    if (COMPLAINT_WORDS.some(function (w) { return lower.indexOf(w) !== -1; })) {
      var sug = "[KORREKTUR-VORSCHLAG für " + recId + "]\n" + cp(pyStrip(out || ""), 600);
      return {
        suggestion: sug,
        rationale: "Im Diskussionsdialog mit KI erörtert: " + cp(pyStrip(message), 200),
        finding: { title: "Review-Finding: " + recId, body: sug, target: recId }
      };
    }
    return { suggestion: null, rationale: "", finding: null };
  }
  var SECRET_RES = [
    /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
    /\b(api[_-]?key|secret|password|passwd|bearer)\b\s*[:=]\s*\S+/gi,
    /\b(ghp_|github_pat_|sk-|xai-|AKIA)[A-Za-z0-9_\-]{8,}/g
  ];
  function redact(text) {
    var out = String(text || "");
    SECRET_RES.forEach(function (re) { out = out.replace(re, "[REDACTED]"); });
    return out;
  }

  // ------------------------------------------------------------ Anbieter
  async function readSSE(res, onData) {
    var reader = res.body.getReader();
    var dec = new TextDecoder("utf-8");
    var buf = "";
    function flush(line) {
      line = line.replace(/\r$/, "");
      if (line.indexOf("data:") !== 0) return;
      var payload = line.slice(5).trim();
      if (!payload || payload === "[DONE]") return;
      var obj = null;
      try { obj = JSON.parse(payload); } catch (e) { return; }
      onData(obj);
    }
    for (;;) {
      var r = await reader.read();
      if (r.done) break;
      buf += dec.decode(r.value, { stream: true });
      var lines = buf.split("\n");
      buf = lines.pop();
      lines.forEach(flush);
    }
    if (buf) flush(buf);
  }
  async function failFrom(res) {
    var detail = "HTTP " + res.status;
    try {
      var j = await res.json();
      var m = (j && j.error && (j.error.message || j.error)) || (j && j.message);
      if (m) detail += " – " + (typeof m === "string" ? m : JSON.stringify(m));
    } catch (e) { /* kein JSON */ }
    var err = new Error(detail);
    err.status = res.status;
    return err;
  }
  // JSON sicher lesen: Eine HTML-Seite (falsche Basis-URL, 404 einer statischen Seite) wird zu einem
  // verständlichen Fehler statt zu Safaris „The string did not match the expected pattern.“
  async function readJson(res) {
    var text = await res.text();
    try { return JSON.parse(text); }
    catch (e) {
      var err = new Error("HTTP " + res.status + " – " + tr("pvNotJson"));
      err.notJson = true;
      err.httpStatus = res.status;
      throw err;
    }
  }
  function versionKey(id) {
    return (String(id).match(/\d+(?:\.\d+)?/g) || []).map(Number);
  }
  function newestFirst(a, b) {
    var x = versionKey(a), y = versionKey(b);
    for (var i = 0; i < Math.max(x.length, y.length); i++) {
      var d = (y[i] || 0) - (x[i] || 0);
      if (d) return d;
    }
    return a < b ? -1 : 1;
  }
  function pickDefault(ids, prefer, avoid) {
    var sorted = ids.slice().sort(newestFirst);
    var good = sorted.filter(function (id) { return prefer.test(id) && !(avoid && avoid.test(id)); });
    return good[0] || sorted.filter(function (id) { return prefer.test(id); })[0] || sorted[0] || "";
  }
  function openAiCompatible(base, filter) {
    return {
      list: async function (key) {
        var res = await fetch(base + "/models", { headers: { Authorization: "Bearer " + key } });
        if (!res.ok) throw await failFrom(res);
        var j = await readJson(res);
        return (j.data || []).map(function (m) { return m.id; }).filter(filter || Boolean);
      },
      chat: async function (key, model, prompt, onDelta, opt) {
        var res = await fetch(base + "/chat/completions", {
          method: "POST",
          signal: opt && opt.signal,
          headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
          body: JSON.stringify({ model: model, stream: true, messages: [{ role: "user", content: prompt }] })
        });
        if (!res.ok) throw await failFrom(res);
        var text = "";
        await readSSE(res, function (ev) {
          if (ev.error) throw new Error(ev.error.message || "stream error");
          var d = ev.choices && ev.choices[0] && ev.choices[0].delta;
          if (d && d.content) { text += d.content; if (onDelta) onDelta(d.content, text); }
        });
        return text;
      }
    };
  }
  var GEMINI = "https://generativelanguage.googleapis.com/v1beta";
  var ANTHROPIC_HEADERS = function (key) {
    return { "x-api-key": key, "anthropic-version": "2023-06-01",
             "anthropic-dangerous-direct-browser-access": "true", "Content-Type": "application/json" };
  };
  var PROVIDERS = {
    gemini: {
      label: "Google Gemini", recommended: true, free: true,
      keyUrl: "https://aistudio.google.com/apikey", keyPh: "AIza…",
      pick: function (ids) { return pickDefault(ids, /flash/, /lite|exp|preview|thinking|image|tts|live/); },
      list: async function (key) {
        var res = await fetch(GEMINI + "/models?pageSize=1000", { headers: { "x-goog-api-key": key } });
        if (!res.ok) throw await failFrom(res);
        var j = await readJson(res);
        return (j.models || []).filter(function (m) {
          return (m.supportedGenerationMethods || []).indexOf("generateContent") !== -1 &&
            /gemini/.test(m.name) && !/embedding|aqa|imagen|tts|image|live|native-audio/.test(m.name);
        }).map(function (m) { return m.name.replace(/^models\//, ""); });
      },
      chat: async function (key, model, prompt, onDelta, opt) {
        var res = await fetch(GEMINI + "/models/" + encodeURIComponent(model) + ":streamGenerateContent?alt=sse", {
          method: "POST",
          signal: opt && opt.signal,
          headers: { "x-goog-api-key": key, "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ role: "user", parts: [{ text: prompt }] }] })
        });
        if (!res.ok) throw await failFrom(res);
        var text = "";
        await readSSE(res, function (ev) {
          if (ev.error) throw new Error(ev.error.message || "stream error");
          var c = ev.candidates && ev.candidates[0];
          ((c && c.content && c.content.parts) || []).forEach(function (p) {
            if (p.text && !p.thought) { text += p.text; if (onDelta) onDelta(p.text, text); }
          });
        });
        return text;
      }
    },
    anthropic: {
      label: "Anthropic Claude", keyUrl: "https://console.anthropic.com/settings/keys", keyPh: "sk-ant-…",
      pick: function (ids) { return pickDefault(ids, /sonnet/); },
      list: async function (key) {
        var res = await fetch("https://api.anthropic.com/v1/models?limit=100", { headers: ANTHROPIC_HEADERS(key) });
        if (!res.ok) throw await failFrom(res);
        var j = await readJson(res);
        return (j.data || []).map(function (m) { return m.id; });
      },
      chat: async function (key, model, prompt, onDelta, opt) {
        var res = await fetch("https://api.anthropic.com/v1/messages", {
          method: "POST",
          signal: opt && opt.signal,
          headers: ANTHROPIC_HEADERS(key),
          body: JSON.stringify({ model: model, max_tokens: (opt && opt.maxTokens) || 2048, stream: true,
                                 messages: [{ role: "user", content: prompt }] })
        });
        if (!res.ok) throw await failFrom(res);
        var text = "";
        await readSSE(res, function (ev) {
          if (ev.type === "error") throw new Error((ev.error && ev.error.message) || "stream error");
          if (ev.type === "content_block_delta" && ev.delta && ev.delta.type === "text_delta") {
            text += ev.delta.text; if (onDelta) onDelta(ev.delta.text, text);
          }
        });
        return text;
      }
    },
    openai: Object.assign({
      label: "OpenAI", keyUrl: "https://platform.openai.com/api-keys", keyPh: "sk-…",
      pick: function (ids) { return pickDefault(ids, /^gpt-[\d.]+-mini$/, null) || pickDefault(ids, /^gpt-/); }
    }, openAiCompatible("https://api.openai.com/v1", function (id) {
      return /^(gpt-|o\d|chatgpt)/.test(id) &&
        !/audio|realtime|tts|transcribe|image|search|embedding|instruct|moderation|codex/.test(id);
    })),
    nexos: Object.assign({
      label: "Nexos.ai", keyUrl: "https://nexos.ai/", keyPh: "nexos-…",
      // Nexos nennt Modelle mit Anzeigenamen („GPT 4o mini“, „Gemini 2.5 Flash“).
      pick: function (ids) { return pickDefault(ids, /flash|mini|sonnet/i, /lite|preview|image|audio|embed/i); }
    }, openAiCompatible("https://api.nexos.ai/v1", function (id) { return !/embed/.test(id); }))
  };
  var ORDER = ["gemini", "anthropic", "openai", "nexos"];
  // Weitere OpenAI-kompatible Endpunkte (z. B. OpenRouter, ein lokales Ollama): je Endpunkt ein Eintrag
  // im Schlüsselbund mit Basis-URL, ID „custom:<host>“, Bezeichnung = Host. Der Schlüssel geht nur an
  // diesen Endpunkt. Erlaubt sind https:// und http:// nur für localhost/127.0.0.1.
  var CUSTOM = "custom:";
  function isCustom(id) { return String(id || "").indexOf(CUSTOM) === 0; }
  function normalizeEndpoint(raw) {
    var s = String(raw || "").trim(), u;
    if (!s) return null;
    try { u = new URL(s); } catch (e) { return null; }
    var local = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(u.hostname);
    if (!(u.protocol === "https:" || (u.protocol === "http:" && local))) return null;
    if (u.username || u.password || u.search || u.hash) return null;
    // Eingefügte Pfade wie …/v1/models oder …/v1/chat/completions auf die Basis kürzen.
    var path = u.pathname.replace(/\/+$/, "").replace(/\/(models|chat\/completions)$/, "");
    return { base: u.origin + path, host: u.host, label: u.host };
  }
  function customFilter(id) { return !/embed|whisper|tts|dall-e|moderation|rerank/i.test(id); }
  function customProvider(rec, id) {
    return Object.assign({
      label: rec.label || String(id).slice(CUSTOM.length), custom: true, base: rec.base,
      pick: function (ids) { return pickDefault(ids, /flash|mini|sonnet|chat/i, /embed|image|audio|tts|vision|preview/i); }
    }, openAiCompatible(rec.base, customFilter));
  }
  // Anbieter zu einer ID: eingebaut oder eigener Endpunkt aus dem Schlüsselbund.
  function provOf(id, v) {
    if (!isCustom(id)) return PROVIDERS[id] || null;
    var rec = (v || vault()).providers[id];
    return rec && rec.base ? customProvider(rec, id) : null;
  }
  function providerLabel(id, v) { var p = provOf(id, v); return p ? p.label : String(id || ""); }
  function keyGroupLabel(id, v) { return providerLabel(id, v) + " · " + tr("viaKey"); }
  // Verbundene Schlüssel in fester Reihenfolge: erst die eingebauten Anbieter, dann eigene Endpunkte.
  function keyIds(v) {
    v = v || vault();
    return ORDER.filter(function (id) { return v.providers[id]; }).concat(
      Object.keys(v.providers).filter(function (id) { return isCustom(id) && v.providers[id] && v.providers[id].base; }).sort());
  }
  // Projektkontingent: läuft über den Dienst (proxy/nexos-worker.mjs). Der Browser schickt nur sein
  // Firebase-ID-Token; der Dienst prüft die Freigabe (grants/{uid}: until, backend, model).
  // Zwei Backends: "nexos" (Projektschlüssel, Route-ID "project") und "abo" (Gemini-Abo des Verwalters über
  // agy auf einem GitHub-Läufer, Route-ID "abo", nur für die Konten in abo_uids; proxy/abo-relay.mjs).
  function projectBase() { return String((state.config && state.config.projekt_dienst) || "").replace(/\/$/, ""); }
  PROVIDERS.project = Object.assign({ label: "Nexos", pick: function (ids) { return PROVIDERS.nexos.pick(ids); } },
    { list: function (tok) { return openAiCompatible(projectBase() + "/v1").list(tok); },
      chat: function (tok, model, prompt, onDelta, opt) { return openAiCompatible(projectBase() + "/v1").chat(tok, model, prompt, onDelta, opt); } });
  // Gemini-Modelle, die agy anbietet (`agy models`, agy 1.3.2, 09.10.2026); die Effort-Stufe ist Teil der ID.
  // Dieselbe Liste steht in proxy/abo-relay.mjs; ai-access.config.json kann sie mit abo_modelle ersetzen.
  var ABO_MODELS = [
    "gemini-3.8-flash-high", "gemini-3.8-flash-medium", "gemini-3.8-flash-low",
    "gemini-3.7-flash-high", "gemini-3.7-flash-medium", "gemini-3.7-flash-low",
    "gemini-3.6-flash-high", "gemini-3.6-flash-medium", "gemini-3.6-flash-low",
    "gemini-3.1-pro-high", "gemini-3.1-pro-low"
  ];
  var ABO_DEFAULT = "gemini-3.8-flash-medium";
  function aboModels() {
    var c = state.config && state.config.abo_modelle;
    return Array.isArray(c) && c.length ? c.map(String) : ABO_MODELS.slice();
  }
  // Nur diese Konten (Firebase-UIDs) können das Gemini-Abo bekommen; der Worker prüft es mit ABO_ALLOWED_UIDS erneut.
  function aboAllowed(uid) {
    var c = state.config && state.config.abo_uids;
    return Array.isArray(c) && c.map(String).indexOf(String(uid || "")) !== -1;
  }
  PROVIDERS.abo = { label: "Gemini-Abo",
    pick: function (ids) { return ids.indexOf(ABO_DEFAULT) !== -1 ? ABO_DEFAULT : ids[0] || ""; },
    list: function () { return Promise.resolve(aboModels()); },
    chat: function (tok, model, prompt, onDelta, opt) { return aboChat(model, prompt, onDelta, opt); } };
  function grantActive() { return !!(quota.grant && quota.grant.until && Date.parse(quota.grant.until) > Date.now()); }
  // Backend einer Freigabe; ohne Feld (ältere Freigaben) Nexos.
  function grantBackend(g) { g = g === undefined ? quota.grant : g; return g && g.backend === "abo" ? "abo" : "nexos"; }
  function isQuota(id) { return id === "project" || id === "abo"; }
  // Route-ID der eigenen Freigabe: "project" (Nexos) oder "abo".
  function grantProvider() { return grantBackend() === "abo" ? "abo" : "project"; }
  function quotaUsable(id) { return grantActive() && !!projectBase() && (id === undefined || grantProvider() === id); }
  // Modelle der eigenen Freigabe: ein vom Verwalter gewähltes Modell oder alle Modelle des Backends.
  function grantModels() {
    if (!quota.grant) return [];
    if (quota.grant.model) return [quota.grant.model];
    return grantBackend() === "abo" ? aboModels() : (quota.models || []).slice();
  }
  function quotaLabel(id) { return tr(id === "abo" ? "aboLabel" : "projLabel"); }
  function projectOffered() { return signInOffered() && !!projectBase(); }

  // --------------------------------------------------------------- Ablage
  // Ein Schlüsselbund je Browser: Der Schlüssel funktioniert auch ohne Anmeldung.
  function scope() { return "browser"; }
  function readVault(kind) {
    var sc = scope();
    if (!sc) return { providers: {}, choice: null };
    try { return JSON.parse(sget(kind, VAULT_PREFIX + sc) || "null") || { providers: {}, choice: null }; }
    catch (e) { return { providers: {}, choice: null }; }
  }
  function vault() {
    var a = readVault("local"), b = readVault("session");
    var out = { providers: Object.assign({}, a.providers || {}), choice: b.choice || a.choice || null, picks: a.picks || null };
    Object.keys(b.providers || {}).forEach(function (k) { out.providers[k] = Object.assign({ session: true }, b.providers[k]); });
    return out;
  }
  function saveProvider(id, rec, remember) {
    var sc = scope();
    if (!sc) return;
    ["local", "session"].forEach(function (kind) {
      var v = readVault(kind);
      v.providers = v.providers || {};
      delete v.providers[id];
      if ((kind === "local") === !!remember) v.providers[id] = rec;
      sset(kind, VAULT_PREFIX + sc, JSON.stringify(v));
    });
  }
  function removeProvider(id) {
    var sc = scope();
    if (!sc) return;
    ["local", "session"].forEach(function (kind) {
      var v = readVault(kind);
      if (v.providers) delete v.providers[id];
      if (v.choice && v.choice.provider === id) v.choice = null;
      if (v.picks && v.picks.byok && v.picks.byok.provider === id) delete v.picks.byok;
      sset(kind, VAULT_PREFIX + sc, JSON.stringify(v));
    });
    emit();
  }
  // Modellwahl je Quelle (Abschnitt im Dialog): picks.local = { cli, fallback: [...] }, picks.project = { provider, model },
  // picks.byok = { provider, model }. Welche Quelle antwortet, entscheidet allein die Reihenfolge (accessOrder);
  // eine Wahl in einem Abschnitt gilt nur für diese Quelle. Frühere Fassungen hatten eine Wahl über alle Quellen
  // (choice), die die Reihenfolge überstimmte; sie wird als Wahl ihrer Quelle übernommen.
  function sourceOf(provider) { return provider === "local" ? "local" : isQuota(provider) ? "project" : "byok"; }
  function picks(v) {
    v = v || vault();
    var out = {};
    Object.keys(v.picks || {}).forEach(function (k) { if (v.picks[k]) out[k] = v.picks[k]; });
    var ch = v.choice;
    if (ch && ch.provider) {
      var src = sourceOf(ch.provider);
      if (!out[src]) out[src] = src === "local" ? { cli: ch.model, fallback: [] } : { provider: ch.provider, model: ch.model };
    }
    return out;
  }
  function setPick(src, val) {
    var sc = scope();
    if (!sc) return;
    var all = picks();
    if (val) all[src] = val; else delete all[src];
    var v = readVault("local");
    v.picks = all;
    v.choice = null;
    sset("local", VAULT_PREFIX + sc, JSON.stringify(v));
    var s = readVault("session");
    if (s.choice) { s.choice = null; sset("session", VAULT_PREFIX + sc, JSON.stringify(s)); }
    emit();
  }
  // Ältere Schnittstelle (Tests, Verbinden eines Schlüssels): { provider, model } wird die Wahl der passenden Quelle.
  function setChoice(choice) {
    if (!choice || !choice.provider) return;
    var src = sourceOf(choice.provider);
    if (src === "local") {
      var cur = picks().local || {};
      setPick("local", { cli: choice.model, fallback: (cur.fallback || []).filter(function (x) { return x !== choice.model; }) });
    } else setPick(src, { provider: choice.provider, model: choice.model });
  }

  // ----------------------------------------------------------- Anmeldung
  var state = { config: null, auth: "idle", user: null, error: "", view: "", pendingEmail: "",
                backend: null, fb: null };
  var configPromise = null;
  function loadConfig() {
    if (configPromise) return configPromise;
    configPromise = fetch(SCRIPT_BASE + "ai-access.config.json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : {}; })
      .catch(function () { return {}; })
      .then(function (cfg) {
        state.config = cfg || {};
        var fb = state.config.firebase || {};
        if (!fb.apiKey || !fb.authDomain || signInMode() === "aus") state.auth = "unconfigured";
        return state.config;
      });
    return configPromise;
  }
  function linkInUrl(href) { return /[?&]oobCode=/.test(href || "") && /[?&]mode=signIn\b/.test(href || ""); }
  var fbPromise = null;
  function ensureFirebase() {
    if (fbPromise) return fbPromise;
    fbPromise = loadConfig().then(async function (cfg) {
      if (state.auth === "unconfigured") return null;
      state.auth = "loading";
      emit();
      var sdk = cfg.sdk || DEFAULT_SDK;
      var appMod = await import(/* webpackIgnore: true */ sdk + "/firebase-app.js");
      var authMod = await import(/* webpackIgnore: true */ sdk + "/firebase-auth.js");
      var app = appMod.initializeApp(cfg.firebase, "autodocs");
      var auth = authMod.getAuth(app);
      try { auth.languageCode = lang(); } catch (e) { /* ignore */ }
      state.fb = { mod: authMod, auth: auth };
      await new Promise(function (resolve) {
        var first = true;
        authMod.onAuthStateChanged(auth, function (u) {
          setUser(u);
          if (first) { first = false; resolve(); }
        });
      });
      try { await authMod.getRedirectResult(auth); } catch (e) { fail(e); }
      return state.fb;
    }).catch(function (e) {
      fbPromise = null;
      state.auth = "signed-out";
      fail(e);
      return null;
    });
    return fbPromise;
  }
  function setUser(u) {
    var before = state.user && state.user.uid;
    var pid = u && u.providerData && u.providerData[0] ? u.providerData[0].providerId : (u && u.providerId) || "";
    state.user = u ? { uid: u.uid, email: u.email || "", name: u.displayName || "", photo: u.photoURL || "", provider: pid } : null;
    state.auth = u ? "signed-in" : "signed-out";
    sset("local", SESSION_FLAG, u ? "1" : null);
    var changed = before !== (state.user && state.user.uid);
    if (changed && state.user && dlg && dlg.open && (state.view === "sent" || state.view === "confirm")) {
      // Nach der Anmeldung per E-Mail-Link zurück zur Anfrage, sonst zur Statusseite.
      state.view = state.afterSignIn || (projectOffered() ? "request" : "account");
    }
    emit();
    if (changed) syncQuota();
  }
  function friendly(e) {
    var code = (e && e.code) || "";
    if (state.lastProvider === "apple.com" && /invalid-oauth-client-id|invalid-credential|operation-not-allowed|internal-error|argument-error/.test(code)) return tr("appleSetup");
    if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") return "";
    if (code === "auth/invalid-email" || code === "auth/missing-email") return tr("errMail");
    if (code === "auth/unauthorized-domain" || code === "auth/unauthorized-continue-uri") return tr("errDomain");
    if (code === "auth/invalid-action-code" || code === "auth/expired-action-code") return tr("errLink");
    if (code === "auth/network-request-failed") return tr("errNet");
    if (code === "auth/operation-not-allowed" || code === "auth/admin-restricted-operation") return tr("errOff");
    return tr("errGeneric", (e && (e.message || e.code)) || String(e));
  }
  function fail(e) { state.error = friendly(e); emit(); }
  async function signInGoogle() { return signInWith("GoogleAuthProvider"); }
  async function signInWith(kind, arg) {
    state.error = "";
    state.lastProvider = arg || kind;
    var fb = await ensureFirebase();
    if (!fb) return;
    var provider = arg ? new fb.mod[kind](arg) : new fb.mod[kind]();
    try {
      await fb.mod.signInWithPopup(fb.auth, provider);
    } catch (e) {
      if (e && (e.code === "auth/popup-blocked" || e.code === "auth/operation-not-supported-in-this-environment")) {
        try { await fb.mod.signInWithRedirect(fb.auth, provider); } catch (e2) { fail(e2); }
      } else fail(e);
    }
  }
  function cleanHref() {
    var u = new URL(root.location.href);
    ["apiKey", "oobCode", "mode", "lang", "continueUrl", "tenantId"].forEach(function (k) { u.searchParams.delete(k); });
    return u.toString();
  }
  async function sendLink(email) {
    state.error = "";
    email = String(email || "").trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { state.error = tr("errMail"); emit(); return false; }
    var fb = await ensureFirebase();
    if (!fb) return false;
    try {
      await fb.mod.sendSignInLinkToEmail(fb.auth, email, { url: cleanHref(), handleCodeInApp: true });
      sset("local", PENDING_EMAIL, email);
      state.pendingEmail = email;
      state.view = "sent";
      emit();
      return true;
    } catch (e) { fail(e); return false; }
  }
  async function completeLink(href, email) {
    state.error = "";
    var fb = await ensureFirebase();
    if (!fb) return false;
    if (!fb.mod.isSignInWithEmailLink(fb.auth, href)) { state.error = tr("errLink"); emit(); return false; }
    email = email || sget("local", PENDING_EMAIL) || "";
    if (!email) { state.view = "confirm"; state.pendingLink = href; openDialog("confirm"); return false; }
    try {
      await fb.mod.signInWithEmailLink(fb.auth, email, href);
      sset("local", PENDING_EMAIL, null);
      if (href === root.location.href && root.history && root.history.replaceState) {
        root.history.replaceState(null, "", cleanHref());
      }
      return true;
    } catch (e) { fail(e); return false; }
  }
  async function signOut() {
    var fb = state.fb;
    if (fb) { try { await fb.mod.signOut(fb.auth); } catch (e) { fail(e); } }
    state.view = defaultView();
    toast(tr("signedOut"));
  }

  // ------------------------------------------- Projektkontingent (Firestore)
  // Firestore über REST mit dem ID-Token der angemeldeten Person; die Regeln stehen in
  // firestore.rules. requests/{uid}: Anfrage; grants/{uid}: freigegebener Nexos-Schlüssel
  // (nur für die Person selbst und Verwalter lesbar); admins/{uid}: Verwalter (nur Konsole).
  function fsBase() {
    var c = state.config || {};
    if (c.firestore_base) return c.firestore_base.replace(/\/$/, "");
    return "https://firestore.googleapis.com/v1/projects/" + encodeURIComponent((c.firebase || {}).projectId || "") +
      "/databases/(default)/documents";
  }
  function fsVal(v) {
    if (v === null || v === undefined) return { nullValue: null };
    if (typeof v === "boolean") return { booleanValue: v };
    if (typeof v === "number") return Number.isInteger(v) ? { integerValue: String(v) } : { doubleValue: v };
    return { stringValue: String(v) };
  }
  // Firestore-Wert als einfacher Wert; Zeitpunkte bleiben als Text (ISO) erhalten, damit sie unverändert
  // zurückgeschrieben werden können (Zähler der Feedback-Mengenbegrenzung), Maps werden zu Objekten.
  function fsPlainValue(f) {
    return "stringValue" in f ? f.stringValue : "integerValue" in f ? Number(f.integerValue) :
      "doubleValue" in f ? f.doubleValue : "booleanValue" in f ? f.booleanValue :
      "timestampValue" in f ? f.timestampValue : "mapValue" in f ? fsPlain(f.mapValue) : null;
  }
  function fsPlain(doc) {
    var out = {};
    Object.keys((doc && doc.fields) || {}).forEach(function (k) { out[k] = fsPlainValue(doc.fields[k]); });
    if (doc && doc.name) out._id = doc.name.split("/").pop();
    return out;
  }
  async function fsFetch(path, opts) {
    opts = opts || {};
    var headers = {};
    if (opts.token) headers.Authorization = "Bearer " + opts.token;
    else if (!opts.public) {
      var fb = state.fb;
      var u = fb && fb.auth && fb.auth.currentUser;
      if (!u) throw new Error("not-signed-in");
      headers.Authorization = "Bearer " + await u.getIdToken();
    }
    if (opts.body) headers["Content-Type"] = "application/json";
    var res = await fetch(fsBase() + path, { method: opts.method || "GET", headers: headers, body: opts.body });
    if (res.status === 404 && (opts.method || "GET") === "GET") return null;
    if (res.status === 403 && opts.quiet) return null;
    if (!res.ok) throw await failFrom(res);
    var txt = await res.text();
    return txt ? JSON.parse(txt) : {};
  }
  function fsGet(path, quiet) { return fsFetch("/" + path, { quiet: quiet }).then(function (d) { return d ? fsPlain(d) : null; }); }
  function fsSet(path, obj, mask) {
    var q = mask ? "?" + mask.map(function (f) { return "updateMask.fieldPaths=" + encodeURIComponent(f); }).join("&") : "";
    var fields = {};
    Object.keys(obj).forEach(function (k) { fields[k] = fsVal(obj[k]); });
    return fsFetch("/" + path + q, { method: "PATCH", body: JSON.stringify({ fields: fields }) });
  }
  function fsDelete(path) { return fsFetch("/" + path, { method: "DELETE" }); }
  async function fsList(collection, field, value) {
    var where = field ? { fieldFilter: { field: { fieldPath: field }, op: "EQUAL", value: fsVal(value) } } : undefined;
    var rows = await fsFetch(":runQuery", { method: "POST",
      body: JSON.stringify({ structuredQuery: { from: [{ collectionId: collection }], where: where } }) });
    return (rows || []).filter(function (r) { return r.document; }).map(function (r) { return fsPlain(r.document); });
  }
  var GRANT_SEEN = "autodocs-ai-grant-seen";
  var quota = { request: null, grant: null, admin: false, open: [], grants: [], loaded: false };
  // Beim Anmelden: Freigabe übernehmen bzw. entzogene entfernen, Anfrage und Verwalterrolle lesen.
  async function syncQuota() {
    if (!state.user || !state.fb || !projectOffered()) {
      quota = { request: null, grant: null, admin: false, open: [], grants: [], loaded: false, models: null };
      fbAdm.items = []; fbAdm.loaded = false;
      // Feedback sichten geht auch ohne Projektkontingent; dafür nur die Verwalterrolle lesen.
      if (state.user && state.fb && fbConfigured()) {
        try { quota.admin = !!(await fsGet("admins/" + state.user.uid, true)); if (quota.admin) await loadFeedbackAdmin(); }
        catch (e) { if (root.console) root.console.warn("ai-access: Verwalterrolle nicht lesbar", e); }
      }
      emit(); emitFeedback(); return;
    }
    var uid = state.user.uid;
    try {
      var res = await Promise.all([fsGet("grants/" + uid, true), fsGet("requests/" + uid, true), fsGet("admins/" + uid, true)]);
      quota.grant = res[0]; quota.request = res[1]; quota.admin = !!res[2]; quota.loaded = true;
      var v = vault();
      if (grantActive() && projectBase()) {
        // Nexos-Modelle kommen vom Dienst; die Modelle des Gemini-Abos stehen fest (aboModels).
        if (!quota.models && grantBackend() === "nexos") {
          try { quota.models = await PROVIDERS.project.list(await state.fb.auth.currentUser.getIdToken()); }
          catch (e) { quota.models = []; }
        }
        // Gespeicherte Wahl eines anderen Backends (Freigabe geändert) oder eines nicht freigegebenen Modells verwerfen.
        if (v.choice && isQuota(v.choice.provider) &&
            (v.choice.provider !== grantProvider() || (quota.grant.model && v.choice.model !== quota.grant.model))) setChoice(null);
        // Die Reihenfolge ergibt sich aus routeSync; hier nur einmal je Freigabe melden.
        if (sget("local", GRANT_SEEN) !== quota.grant.until) {
          sset("local", GRANT_SEEN, quota.grant.until);
          toast(tr("grantedToast"));
        }
      } else if (v.choice && isQuota(v.choice.provider)) {
        setChoice(null);
      }
      if (quota.admin) await loadAdmin();
      if (quota.admin) await loadFeedbackAdmin().catch(function (e) { if (root.console) root.console.warn("ai-access: Feedback nicht lesbar", e); });
    } catch (e) {
      // Hintergrundabgleich: kein Fehlerhinweis im Dialog, die Statusseite zeigt den bekannten Stand.
      if (root.console) root.console.warn("ai-access: Abgleich des Projektkontingents fehlgeschlagen", e);
    }
    emit();
  }
  async function loadAdmin() {
    var rows = await Promise.all([fsList("requests"), fsList("grants")]);
    quota.open = rows[0].filter(function (r) { return r.status === "offen"; });
    quota.people = {};
    rows[0].forEach(function (r) { quota.people[r._id] = { uid: r._id, name: r.name || "", email: r.email || "", provider: r.provider || "" }; });
    quota.grants = rows[1];
    quota.settings = (await fsGet("settings/projekt", true)) || { nexos: "1", openai: "nein", name1: "", name2: "" };
    // Modellauswahl beim Freischalten: vollständige Nexos-Liste (der Dienst erlaubt sie Verwaltern mit ?all=1).
    if (!quota.adminModels && projectBase()) {
      var nx = [];
      try {
        var res = await fetch(projectBase() + "/v1/models?all=1", { headers: { Authorization: "Bearer " + await state.fb.auth.currentUser.getIdToken() } });
        if (res.ok) nx = ((await readJson(res)).data || []).map(function (m) { return m.id; }).filter(Boolean);
      } catch (e) { nx = []; }
      quota.adminModels = { nexos: nx };
    }
  }
  async function saveSettings(form) {
    await fsSet("settings/projekt", { nexos: form.nexos.value, openai: form.openai.checked ? "ja" : "nein",
      updated: new Date().toISOString(), updated_by: state.user.uid });
    await loadAdmin();
    toast(tr("admDone"));
    emit();
  }
  async function sendRequest(reason) {
    var u = state.user;
    // Eine erledigte Anfrage (abgelaufene Freigabe) zuerst entfernen; die Regeln erlauben kein Überschreiben.
    if (quota.request && quota.request.status === "freigegeben") await fsDelete("requests/" + u.uid);
    await fsSet("requests/" + u.uid, { uid: u.uid, email: u.email || "", name: u.name || "", reason: reason,
      status: "offen", created: new Date().toISOString(), lang: lang(), page: root.location.pathname });
    await noteRequestProvider(u);
    toast(tr("reqDone"));
    // Betreiber benachrichtigen (GitHub-Issue, Push); Fehler hier halten die Anfrage nicht auf.
    if (projectBase()) {
      try {
        await fetch(projectBase() + "/notify", { method: "POST",
          headers: { Authorization: "Bearer " + await state.fb.auth.currentUser.getIdToken() } });
      } catch (e) { /* Anfrage liegt trotzdem in Firestore */ }
    }
    await syncQuota();
  }
  async function updateRequest(reason) {
    var u = state.user, r = quota.request;
    await fsSet("requests/" + u.uid, { uid: u.uid, email: u.email || "", name: u.name || "", reason: reason,
      status: "offen", created: r.created, lang: lang(), page: root.location.pathname });
    await noteRequestProvider(u);
    toast(tr("reqUpdated"));
    await syncQuota();
  }
  // Anmeldeweg (google.com, github.com, …) an der Anfrage vermerken, damit Verwalter Anfragende eindeutig
  // zuordnen können. Eigener Schreibvorgang: Kennen die bereitgestellten Firestore-Regeln das Feld noch
  // nicht, wird er abgelehnt, und die Anfrage selbst bleibt unberührt.
  async function noteRequestProvider(u) {
    if (!u || !u.provider) return;
    try { await fsSet("requests/" + u.uid, { provider: u.provider }, ["provider"]); } catch (e) { /* ältere Regeln */ }
  }
  async function withdrawRequest() { await fsDelete("requests/" + state.user.uid); await syncQuota(); }
  async function decide(uid, grant, form) {
    var now = new Date().toISOString(), me = state.user.uid;
    if (grant) {
      var days = parseInt(form.days.value, 10) || 7;
      var until = new Date(Date.now() + days * 86400000).toISOString();
      var backend = form.backend && form.backend.value === "abo" ? "abo" : "nexos";
      // Das Gemini-Abo nur für die eigenen Konten des Verwalters (abo_uids); der Worker prüft es erneut.
      if (backend === "abo" && !aboAllowed(uid)) throw new Error(tr("aboOnlyOwn"));
      await fsSet("grants/" + uid, { until: until, backend: backend, model: String(form.model.value || "").trim(),
                                     note: form.note.value.trim(), granted: now, granted_by: me });
    }
    await fsSet("requests/" + uid, { status: grant ? "freigegeben" : "abgelehnt", note: form.note.value.trim(),
                                     decided: now, decided_by: me }, ["status", "note", "decided", "decided_by"]);
    toast(tr("admDone"));
    await afterAdminChange(uid);
  }
  async function revoke(uid) { await fsDelete("grants/" + uid); await afterAdminChange(uid); }
  // Betrifft die Entscheidung das eigene Konto, auch die eigene Freigabe neu lesen (Kopfleiste, Knöpfe).
  async function afterAdminChange(uid) {
    if (state.user && uid === state.user.uid) { await syncQuota(); return; }
    await loadAdmin();
    emit();
  }

  // ------------------------------------------------------------ Leser-Feedback
  // Konzept: docs/concepts/fachkonzept-feedback-und-rollen.md. Melden kann jede Person:
  //   * lokal (serve.py erreichbar): POST /api/user-feedback → _src/spec/feedback-queue/user/
  //   * öffentlich mit Firebase: Firestore feedback/{id}; angemeldet mit dem eigenen Konto, sonst mit einem
  //     anonymen Firebase-Konto in einer eigenen App-Instanz („autodocs-feedback“), das erst beim ersten Senden
  //     entsteht (kein stilles Anlegen beim Seitenaufruf). Die Mengenbegrenzung (feedback_quota/{uid}) schreibt
  //     derselbe Schreibvorgang fort; die Regeln prüfen beides (firestore.rules).
  //   * sonst: vorausgefülltes, öffentliches GitHub-Issue (der Dialog sagt das vorher).
  // Danach optional die Spiegelung als Issue im privaten Repository über den Worker (POST /feedback/notify).
  var FB_SCHEMA = "user-feedback@v2";
  var FB_ANON = "autodocs-feedback-anon";
  var FB_ARTS = ["hinweis", "fehler", "wunsch"];
  var FB_STATUSES = ["neu", "in_pruefung", "erledigt", "verworfen"];
  var FB_CTX = { page: 300, title: 200, target: 256, fold: 200, selection: 1000, release: 40, lang: 8 };
  var FB_GAP_MS = 30000, FB_DAY_MS = 86400000, FB_PER_DAY = 20;
  var fbAnonPromise = null, fbSettingsCache = null;
  var fbAdm = { items: [], loaded: false, settings: { offen: true, anonym: true }, filter: "open" };
  function fbConfigured() {
    var c = state.config || {}, f = c.firebase || {};
    return !!(f.apiKey && f.projectId) && c.feedback !== "issue" && c.feedback !== "aus";
  }
  function fbDocName(path) {
    return "projects/" + ((state.config && state.config.firebase) || {}).projectId + "/databases/(default)/documents/" + path;
  }
  function fbErr(code, extra) { var e = new Error(code); e.code = code; if (extra) Object.assign(e, extra); return e; }
  // Eingaben wie die Regeln normalisieren: Text 3–4000 Zeichen, Bezug nur bekannte Felder, Kontakt höchstens 120.
  function fbNormalize(input) {
    input = input || {};
    var text = String(input.text == null ? "" : input.text).replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, "").trim();
    // Längen in Unicode-Zeichen wie size() der Regeln und len() in Python.
    if (Array.from(text).length < 3) throw fbErr("text_short");
    if (Array.from(text).length > 4000) throw fbErr("text_long");
    var art = FB_ARTS.indexOf(input.art) === -1 ? "hinweis" : input.art;
    var ctx = {};
    Object.keys(input.ctx || {}).forEach(function (k) {
      var v = input.ctx[k];
      if (!FB_CTX[k] || v == null) return;
      v = String(v).replace(/\s+/g, " ").trim();
      if (v) ctx[k] = Array.from(v).slice(0, FB_CTX[k]).join("");
    });
    var out = { schema: FB_SCHEMA, art: art, text: text };
    if (Object.keys(ctx).length) out.ctx = ctx;
    var contact = Array.from(String(input.contact == null ? "" : input.contact).replace(/\s+/g, " ").trim()).slice(0, 120).join("");
    if (contact) out.contact = contact;
    return out;
  }
  function fbNewId() {
    var abc = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", b = new Uint8Array(20), s = "fb";
    (root.crypto || {}).getRandomValues ? root.crypto.getRandomValues(b) : b.forEach(function (_, i) { b[i] = Math.floor(Math.random() * 256); });
    for (var i = 0; i < 18; i++) s += abc[b[i] % abc.length];
    return s;
  }
  // Wert für das REST-Format; Maps für den Bezug, Zeitpunkte als timestampValue.
  function fbVal(v) {
    if (v && typeof v === "object" && v.timestampValue) return { timestampValue: v.timestampValue };
    if (v && typeof v === "object") {
      var f = {};
      Object.keys(v).forEach(function (k) { f[k] = fbVal(v[k]); });
      return { mapValue: { fields: f } };
    }
    return fsVal(v);
  }
  function fbFields(obj) { var f = {}; Object.keys(obj).forEach(function (k) { f[k] = fbVal(obj[k]); }); return f; }
  // Anonymes Konto in eigener App-Instanz: lässt die eigentliche Anmeldung unberührt (Kopfleiste, Kontingent).
  async function fbAnonAuth(create) {
    await loadConfig();
    if (!fbConfigured()) return null;
    if (!create && !sget("local", FB_ANON)) return null;
    if (!fbAnonPromise) {
      fbAnonPromise = (async function () {
        var sdk = state.config.sdk || DEFAULT_SDK;
        var appMod = await import(/* webpackIgnore: true */ sdk + "/firebase-app.js");
        var authMod = await import(/* webpackIgnore: true */ sdk + "/firebase-auth.js");
        var app = appMod.initializeApp(state.config.firebase, "autodocs-feedback");
        var auth = authMod.getAuth(app);
        await new Promise(function (resolve) {
          var done = false;
          authMod.onAuthStateChanged(auth, function () { if (!done) { done = true; resolve(); } });
        });
        return { mod: authMod, auth: auth };
      })().catch(function (e) { fbAnonPromise = null; throw e; });
    }
    var fa = await fbAnonPromise;
    if (!fa.auth.currentUser && create) {
      await fa.mod.signInAnonymously(fa.auth);
      sset("local", FB_ANON, "1");
    }
    return fa.auth.currentUser ? fa : null;
  }
  // Wer meldet: das angemeldete Konto, sonst (create) das anonyme Konto dieses Browsers.
  async function fbIdentity(create) {
    await loadConfig();
    if (state.auth !== "unconfigured" && sget("local", SESSION_FLAG)) await ensureFirebase();
    var u = state.fb && state.fb.auth && state.fb.auth.currentUser;
    if (state.user && u) {
      var tok, claims = {};
      if (typeof u.getIdTokenResult === "function") { var r = await u.getIdTokenResult(); tok = r.token; claims = r.claims || {}; }
      else tok = await u.getIdToken();
      return { kind: "konto", uid: u.uid, token: tok, name: claims.name ? String(claims.name) : "" };
    }
    var a = await fbAnonAuth(create);
    if (!a) return null;
    return { kind: "anonym", uid: a.auth.currentUser.uid, token: await a.auth.currentUser.getIdToken() };
  }
  // Not-Aus des Verwalters (settings/feedback, öffentlich lesbar); fehlt das Dokument, ist das Melden offen.
  async function fbSettings(fresh) {
    if (!fresh && fbSettingsCache && Date.now() - fbSettingsCache.at < 60000) return fbSettingsCache.value;
    var d = null;
    try { d = await fsFetch("/settings/feedback", { public: true, quiet: true }); } catch (e) { d = null; }
    var p = d ? fsPlain(d) : {};
    var value = { offen: p.offen !== false, anonym: p.anonym !== false };
    fbSettingsCache = { at: Date.now(), value: value };
    return value;
  }
  // Wohin eine Meldung geht und wer gerade meldet (für den Dialog).
  async function fbChannel() {
    await loadConfig();
    if (isLocalHost() && root.location.protocol !== "file:" && await backendStatus()) return { kind: "local" };
    if (!fbConfigured()) return { kind: "issue", repo: repo() };
    if (state.auth !== "unconfigured" && sget("local", SESSION_FLAG)) await ensureFirebase();
    var st = await fbSettings();
    return { kind: "firestore", open: st.offen, anonym: st.anonym, signedIn: !!state.user,
             name: state.user ? (state.user.name || state.user.email || "") : "", email: state.user ? state.user.email || "" : "",
             canSignIn: signInOffered() };
  }
  async function fbSend(input) {
    var rec = fbNormalize(input);
    var ch = await fbChannel();
    if (ch.kind === "local") {
      var res = await fetch("/api/user-feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(rec) });
      var j = null;
      try { j = await res.json(); } catch (e) { j = null; }
      if (!res.ok || !j || !j.ok) throw fbErr("local", { detail: (j && j.error) || ("HTTP " + res.status) });
      return { kind: "local", id: j.feedback_id, path: j.path || "" };
    }
    if (ch.kind !== "firestore") throw fbErr("channel");
    if (!ch.open) throw fbErr("paused");
    if (!ch.signedIn && !ch.anonym) throw fbErr("anon_off");
    var who;
    try { who = await fbIdentity(true); }
    catch (e) {
      // Anonyme Anmeldung in Firebase (noch) nicht aktiviert: wie „ohne Anmeldung abgeschaltet“ behandeln.
      if (e && /operation-not-allowed|admin-restricted-operation/.test(String(e.code || e.message))) throw fbErr("anon_off");
      throw fbErr("net", { detail: (e && e.message) || String(e) });
    }
    if (!who) throw fbErr("channel");
    var q = await fsGetWith("feedback_quota/" + who.uid, who.token);
    var now = Date.now();
    if (q && q.last && Date.parse(q.last) + FB_GAP_MS > now) throw fbErr("wait", { wait: Math.ceil((Date.parse(q.last) + FB_GAP_MS - now) / 1000) });
    var sameDay = !!(q && q.day && Date.parse(q.day) + FB_DAY_MS > now);
    if (sameDay && (q.n || 0) >= FB_PER_DAY) throw fbErr("day");
    var id = fbNewId();
    var doc = Object.assign({ uid: who.uid, auth: who.kind, status: "neu" }, rec);
    if (who.kind === "konto" && who.name) doc.name = Array.from(who.name).slice(0, 80).join("");
    var quotaDoc = sameDay ? { day: { timestampValue: q.day }, n: (q.n || 0) + 1, ref: id } : { n: 1, ref: id };
    var writes = [
      { update: { name: fbDocName("feedback/" + id), fields: fbFields(doc) }, currentDocument: { exists: false },
        updateTransforms: [{ fieldPath: "created", setToServerValue: "REQUEST_TIME" }] },
      { update: { name: fbDocName("feedback_quota/" + who.uid), fields: fbFields(quotaDoc) },
        updateTransforms: [{ fieldPath: "last", setToServerValue: "REQUEST_TIME" }]
          .concat(sameDay ? [] : [{ fieldPath: "day", setToServerValue: "REQUEST_TIME" }]) }
    ];
    try {
      await fsFetch(":commit", { method: "POST", token: who.token, body: JSON.stringify({ writes: writes }) });
    } catch (e) {
      if (e && e.status === 403) { fbSettingsCache = null; throw fbErr("rules"); }
      throw fbErr("net", { detail: (e && e.message) || String(e) });
    }
    // Spiegelung als Issue im privaten Repository (optional, der Dienst entscheidet); Fehler halten nichts auf.
    if (projectBase()) {
      try {
        fetch(projectBase() + "/feedback/notify", { method: "POST", headers: { Authorization: "Bearer " + who.token, "Content-Type": "application/json" },
          body: JSON.stringify({ id: id }) }).catch(function () {});
      } catch (e) { /* Meldung liegt trotzdem in Firestore */ }
    }
    emitFeedback();
    return { kind: "firestore", id: id, auth: who.kind };
  }
  async function fsGetWith(path, token) {
    var d = await fsFetch("/" + path, { token: token, quiet: true });
    return d ? fsPlain(d) : null;
  }
  async function fbOwn(who) {
    var rows = await fsFetch(":runQuery", { method: "POST", token: who.token, body: JSON.stringify({ structuredQuery: {
      from: [{ collectionId: "feedback" }], limit: 50,
      where: { fieldFilter: { field: { fieldPath: "uid" }, op: "EQUAL", value: { stringValue: who.uid } } } } }) });
    return (rows || []).filter(function (r) { return r.document; }).map(function (r) { var x = fsPlain(r.document); x._who = who.kind; return x; });
  }
  function byCreatedDesc(a, b) { return String(b.created || "").localeCompare(String(a.created || "")); }
  // Eigene Meldungen: die des angemeldeten Kontos und die des anonymen Kontos dieses Browsers.
  async function fbMine() {
    var ch = await fbChannel();
    if (ch.kind !== "firestore") return { kind: ch.kind, items: [] };
    var out = [], seen = {};
    var konto = state.user ? await fbIdentity(false) : null;
    if (konto && konto.kind === "konto") (await fbOwn(konto)).forEach(function (x) { seen[x._id] = 1; out.push(x); });
    var a = await fbAnonAuth(false);
    if (a) {
      var anon = { kind: "anonym", uid: a.auth.currentUser.uid, token: await a.auth.currentUser.getIdToken() };
      (await fbOwn(anon)).forEach(function (x) { if (!seen[x._id]) out.push(x); });
    }
    out.sort(byCreatedDesc);
    return { kind: "firestore", items: out, signedIn: !!state.user, anonKnown: !!a, canSignIn: signInOffered() };
  }
  async function fbWithdraw(id, whoKind) {
    var who = whoKind === "anonym" ? null : state.user ? await fbIdentity(false) : null;
    if (!who || who.kind !== whoKind) {
      var a = await fbAnonAuth(false);
      if (a) who = { kind: "anonym", uid: a.auth.currentUser.uid, token: await a.auth.currentUser.getIdToken() };
    }
    if (!who) throw fbErr("channel");
    await fsFetch("/feedback/" + encodeURIComponent(id), { method: "DELETE", token: who.token });
    emitFeedback();
  }
  function emitFeedback() {
    try { root.dispatchEvent(new CustomEvent("aiaccess-feedback")); } catch (e) { /* alt */ }
  }
  // ---- Verwaltung: Sichtung (Status, Antwort), Löschen, Not-Aus
  async function loadFeedbackAdmin() {
    if (!quota.admin || !fbConfigured()) return;
    var rows = await fsFetch(":runQuery", { method: "POST", body: JSON.stringify({ structuredQuery: {
      from: [{ collectionId: "feedback" }], orderBy: [{ field: { fieldPath: "created" }, direction: "DESCENDING" }], limit: 200 } }) });
    fbAdm.items = (rows || []).filter(function (r) { return r.document; }).map(function (r) { return fsPlain(r.document); });
    fbAdm.settings = await fbSettings(true);
    fbAdm.loaded = true;
    emitFeedback();
  }
  function fbNewCount() { return quota.admin ? fbAdm.items.filter(function (x) { return x.status === "neu"; }).length : 0; }
  async function fbTriage(id, form) {
    var status = FB_STATUSES.indexOf(form.status.value) === -1 ? "neu" : form.status.value;
    var fields = { status: status, note: String(form.note.value || "").trim().slice(0, 1000), triaged_by: state.user.uid };
    // Zeit der Sichtung als Serverzeit über einen Commit mit Transformation.
    await fsFetch(":commit", { method: "POST", body: JSON.stringify({ writes: [{
      update: { name: fbDocName("feedback/" + id), fields: fbFields(fields) }, updateMask: { fieldPaths: ["status", "note", "triaged_by"] },
      currentDocument: { exists: true }, updateTransforms: [{ fieldPath: "triaged", setToServerValue: "REQUEST_TIME" }] }] }) });
    toast(tr("fbAdmSaved"));
    await loadFeedbackAdmin();
    emit();
  }
  async function fbAdminDelete(id) {
    await fsFetch("/feedback/" + encodeURIComponent(id), { method: "DELETE" });
    await loadFeedbackAdmin();
    emit();
  }
  async function fbSaveSwitch(form) {
    await fsSet("settings/feedback", { offen: !!form.offen.checked, anonym: !!form.anonym.checked,
      updated: new Date().toISOString(), updated_by: state.user.uid });
    toast(tr("fbAdmSaved"));
    await loadFeedbackAdmin();
    emit();
  }
  function openFeedbackAdmin() {
    ensureDialogs();
    state.error = "";
    if (dlg.open) dlg.close();
    state.view = "fbadmin";
    renderDialog();
    loadFeedbackAdmin().then(emit).catch(fail);
  }

  // -------------------------------------------------------- Lokales Backend
  var backendPromise = null;
  function backendStatus() {
    if (!isLocalHost() || root.location.protocol === "file:") return Promise.resolve(null);
    if (backendPromise) return backendPromise;
    var ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, 2500) : null;
    backendPromise = fetch("/api/ai/status", { cache: "no-store", signal: ctl && ctl.signal })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (j) {
        if (timer) clearTimeout(timer);
        state.backend = j ? localState(j, "") : null;
        emit();
        return state.backend;
      });
    return backendPromise;
  }
  // Gefundene CLIs aus /api/ai/status bzw. /api/ai/check: jede installierte CLI mit Zustand, in der Reihenfolge des Dienstes.
  // { id, cli (Name der CLI), model, label (Modell bzw. CLI · Modell), version, status, healthy, error, runnable }
  function cliList(j) {
    var provs = (j && j.providers) || {}, keys = Object.keys(provs);
    var order = (j && Array.isArray(j.order) ? j.order : []).filter(function (k) { return provs[k]; });
    keys.forEach(function (k) { if (order.indexOf(k) === -1) order.push(k); });
    var list = [];
    order.forEach(function (k) {
      var p = provs[k] || {};
      if (!p.available) return;
      list.push({ id: k, cli: p.cli_name || p.name || k, model: p.model || "", label: p.display_name || p.cli_name || k,
                  version: p.cli_version || "", status: p.status || "untested", healthy: p.status === "healthy",
                  error: p.error || "", runnable: p.runnable !== false });
    });
    return list;
  }
  function localState(j, base) {
    var st = { ok: true, clis: cliList(j), active: j.active_provider || "", max: Number(j.max_chain) || MAX_LOCAL };
    if (base) st.base = base;
    return st;
  }

  // Von einer öffentlichen Seite aus prüfen, ob unter localhost ein _src/serve.py mit KI-CLIs läuft.
  // Nur auf Knopfdruck: Browser fragen dabei ggf. nach Zugriff auf das lokale Netzwerk.
  function localBase() { return String((state.config && state.config.lokaler_dienst) || "http://localhost:8100").replace(/\/$/, ""); }
  var LOCAL_OK = "autodocs-ai-local";
  // Höchstens so viele lokale CLIs je Anfrage: die aktive und bis zu zwei Ausweich-CLIs (wie MAX_CHAIN in ai_agent_bridge.py).
  var MAX_LOCAL = 3;
  // Adresse für Aufrufe an den lokalen Dienst: relativ auf localhost, sonst die geprüfte localhost-Adresse.
  function localUrl(path) { return ((state.backend && state.backend.base) || "") + path; }
  async function probeLocal(quiet) {
    var base = localBase();
    state.away = { base: base, busy: !quiet };
    emit();
    var ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, 3000) : null;
    try {
      var r = await fetch(base + "/api/ai/status", { cache: "no-store", signal: ctl && ctl.signal });
      var j = r.ok ? await r.json() : null;
      state.backend = j ? localState(j, base) : null;
      state.away = { base: base, found: !!j, clis: state.backend ? state.backend.clis : [] };
      sset("local", LOCAL_OK, j ? "1" : null);
    } catch (e) {
      state.away = { base: base, found: false, clis: [] };
      if (state.backend && state.backend.base) state.backend = null;
    }
    if (timer) clearTimeout(timer);
    emit();
  }

  // ------------------------------------------------------------- Route
  // anmeldung: "aus" (Standard), "optional" oder "pflicht" (ai-access.config.json); lokal nie Pflicht.
  function signInMode() {
    var m = state.config && state.config.anmeldung;
    return m === "pflicht" || m === "optional" ? m : "aus";
  }
  function signInOffered() { return signInMode() !== "aus" && state.auth !== "unconfigured"; }
  function requiresSignIn() { return !isLocalHost() && signInMode() === "pflicht"; }
  function snapshot() {
    var v = vault();
    return { auth: state.auth, user: state.user, providers: Object.keys(v.providers), choice: v.choice, picks: picks(v),
             order: accessOrder(), backend: state.backend, local: isLocalHost() };
  }
  // Firebase-ID-Token der angemeldeten Person für eigene Dienste (z. B. geschützte Schaubilder,
  // proxy/figure-access.mjs); null ohne Anmeldung. Stellt eine gemerkte Sitzung wieder her, zeigt aber nichts an.
  async function idToken(force) {
    await loadConfig();
    if (state.auth === "unconfigured") return null;
    if (!state.fb && sget("local", SESSION_FLAG)) await ensureFirebase();
    var u = state.fb && state.fb.auth && state.fb.auth.currentUser;
    return u ? u.getIdToken(!!force) : null;
  }
  async function route() {
    await loadConfig();
    // Das Google-SDK nur laden, wenn es eine Sitzung wiederherzustellen gibt.
    if (requiresSignIn() && state.auth !== "unconfigured" && !state.user && sget("local", SESSION_FLAG)) await ensureFirebase();
    await backendStatus();
    return routeSync();
  }
  // Alle Zugänge für Diskussionen mit ihrem Zustand: grün = alle funktionieren, gelb = nur manche, rot = keiner.
  function accessHealth() {
    var v = vault(), src = [];
    keyIds(v).forEach(function (id) { src.push({ kind: "key", id: id, ok: !v.providers[id].failed }); });
    if (quota.grant) src.push({ kind: "project", ok: grantActive() && !!projectBase() });
    ((state.backend && state.backend.clis) || []).forEach(function (c) { src.push({ kind: "local", id: c.id, ok: c.healthy }); });
    var good = src.filter(function (x) { return x.ok; }).length;
    return { state: !good ? "none" : good < src.length ? "partial" : "ok", sources: src };
  }
  // Bis zu drei Symbole: eigener Schlüssel, Geschenkbox fürs Projektkontingent, Terminal für lokale CLIs.
  function accessIcons() {
    var v = vault(), out = [];
    var ids = keyIds(v);
    if (ids.length) {
      var bad = ids.filter(function (id) { return v.providers[id].failed; }).length;
      out.push({ src: "byok", ico: ICO.key, cls: bad === ids.length ? "is-bad" : bad ? "is-warn" : "is-ok",
                 tip: tr(bad === ids.length ? "icoKeyBad" : bad ? "icoKeyPart" : "icoKeyOk") });
    }
    if (projectOffered() && (quota.grant || quota.request)) {
      // Angefragt, aber noch nicht bewilligt: nicht nutzbar (gelb), deshalb beim Klick ein Hinweis statt Rang 1.
      if (grantActive()) out.push({ src: "project", ico: ICO.giftOpen, cls: "is-ok", tip: tr("icoGiftOpen") });
      else if (quota.request && quota.request.status === "offen") out.push({ src: "project", ico: ICO.giftClosed, cls: "is-warn", usable: false, tip: tr("icoGiftPending") });
      else out.push({ src: "project", ico: ICO.giftClosed, cls: "is-bad", tip: tr("icoGiftBad") });
    }
    if (isLocalHost() || (state.backend && state.backend.base)) {
      var ok = ((state.backend && state.backend.clis) || []).some(function (c) { return c.healthy; });
      out.push({ src: "local", ico: ICO.terminal, cls: ok ? "is-ok" : "is-bad", tip: tr(ok ? "icoLocalOk" : "icoLocalBad") });
    }
    return out;
  }
  // Reihenfolge der Zugänge = Priorität; pro Browser gemerkt, Standard: lokal, Kontingent, eigener Schlüssel.
  var ORDER_KEY = "autodocs-ai-order", SOURCES = ["local", "project", "byok"];
  // Frühere Fassungen hießen die Quelle „byot“; eine gespeicherte Reihenfolge wird übernommen und umgeschrieben.
  var LEGACY_SOURCES = { byot: "byok" };
  function accessOrder() {
    var o = [], raw = sget("local", ORDER_KEY);
    try { o = JSON.parse(raw || "[]"); } catch (e) { o = []; }
    o = Array.isArray(o) ? o : [];
    if (o.some(function (x) { return LEGACY_SOURCES[x]; })) {
      o = o.map(function (x) { return LEGACY_SOURCES[x] || x; });
      sset("local", ORDER_KEY, JSON.stringify(o.filter(function (x, i, a) { return a.indexOf(x) === i; })));
    }
    o = o.filter(function (x, i, a) { return SOURCES.indexOf(x) !== -1 && a.indexOf(x) === i; });
    SOURCES.forEach(function (x) { if (o.indexOf(x) === -1) o.push(x); });
    return o;
  }
  function moveSource(id, to) {
    var o = accessOrder().filter(function (x) { return x !== id; });
    o.splice(Math.max(0, Math.min(o.length, to)), 0, id);
    sset("local", ORDER_KEY, JSON.stringify(o));
    emit();
  }
  function markKey(id, failed) {
    var v = vault(), rec = v.providers[id];
    if (!rec || !!rec.failed === failed) return;
    rec.failed = failed;
    saveProvider(id, rec, !rec.session);
    emit();
  }
  // Lokale CLIs der Route: die gewählte (sonst die aktive des Dienstes, die erste gesunde, die erste) und die
  // Ausweichliste in ihrer Reihenfolge, nur gefundene CLIs, zusammen höchstens MAX_LOCAL.
  function localChain(pk) {
    var b = state.backend, clis = (b && b.clis) || [];
    var ids = clis.map(function (c) { return c.id; });
    var want = pk && pk.local && pk.local.cli;
    var healthy = clis.filter(function (c) { return c.healthy; });
    var cli = ids.indexOf(want) !== -1 ? want
      : (b && b.active && healthy.some(function (c) { return c.id === b.active; })) ? b.active
      : (healthy[0] || clis[0] || {}).id;
    var max = Math.max(1, Math.min(MAX_LOCAL, (b && b.max) || MAX_LOCAL));
    var fb = ((pk && pk.local && pk.local.fallback) || []).filter(function (id, i, a) {
      return id !== cli && ids.indexOf(id) !== -1 && a.indexOf(id) === i;
    }).slice(0, max - 1);
    return { cli: cli, fallback: fb };
  }
  function localRoute(c) {
    var r = { kind: "local" };
    if (c.cli) r.cli = c.cli;
    if (c.fallback.length) r.fallback = c.fallback.slice();
    return r;
  }
  // Route je Quelle mit der Modellwahl ihres Abschnitts; null, wenn die Quelle gerade nicht nutzbar ist.
  function sourceRoute(src, v, pk) {
    var backend = state.backend;
    if (src === "local") {
      if (!backend) return null;
      var clis = backend.clis;
      if (!clis) return { kind: "local" };
      var c = localChain(pk), chain = [c.cli].concat(c.fallback);
      return clis.some(function (x) { return x.healthy && chain.indexOf(x.id) !== -1; }) ? localRoute(c) : null;
    }
    if (src === "project") {
      if (!quotaUsable()) return null;
      var gp = grantProvider(), gm = grantModels(), pp = pk.project;
      var model = pp && pp.provider === gp && gm.indexOf(pp.model) !== -1 ? pp.model : quota.grant.model || PROVIDERS[gp].pick(gm);
      return { kind: "byok", provider: gp, model: model };
    }
    var ids = keyIds(v);
    if (!ids.length) return null;
    var pb = pk.byok;
    if (pb && v.providers[pb.provider] && provOf(pb.provider, v)) {
      return { kind: "byok", provider: pb.provider, model: pb.model || v.providers[pb.provider].model };
    }
    return { kind: "byok", provider: ids[0], model: v.providers[ids[0]].model };
  }
  function routeSource(r) { return !r || r.kind === "none" ? "" : r.kind === "local" ? "local" : isQuota(r.provider) ? "project" : "byok"; }
  // Aktuelle Route aus dem bekannten Zustand (ohne Netz) – für Kopfleiste und Übersicht.
  // Es antwortet die oberste nutzbare Quelle der Reihenfolge (Standard: lokal, Kontingent, Schlüssel); die Wahl
  // in einem Abschnitt legt nur fest, mit welchem Modell bzw. welcher CLI diese Quelle antwortet.
  function routeSync() {
    var backend = state.backend;
    if (requiresSignIn() && !state.user) return { kind: "none", reason: state.auth === "unconfigured" ? "setup" : "signin" };
    var v = vault(), pk = picks(v);
    var order = accessOrder();
    for (var i = 0; i < order.length; i++) { var r = sourceRoute(order[i], v, pk); if (r) return r; }
    if (backend) return backend.clis ? localRoute(localChain(pk)) : { kind: "local" };
    return { kind: "none", reason: "key" };
  }
  function cliInfo(id) { return ((state.backend && state.backend.clis) || []).filter(function (c) { return c.id === id; })[0] || null; }
  function cliName(id) { var c = cliInfo(id); return c ? c.cli : String(id || ""); }
  function routeLabel(r) {
    if (!r) return "";
    if (r.kind === "byok") return isQuota(r.provider) ? quotaLabel(r.provider) + " · " + (r.model || "?")
      : providerLabel(r.provider) + " · " + (r.model || "?") + " · " + tr("viaKey");
    if (r.kind === "local") return (r.cli ? cliName(r.cli) : (state.backend && state.backend.active) || "CLI") + " · " + tr("viaLocal");
    return tr(r.reason === "setup" ? "chipSetup" : r.reason === "key" ? "chipConnect" : "chipSignIn");
  }
  // Herkunft einer Antwort für die Anzeige in der Diskussion („Antwort von …“).
  function answerLabel(answer, r) {
    // Gemini-Abo: Modell aus der Antwort und das Profil, das geantwortet hat (leo oder neo).
    if (r && r.kind === "byok" && r.provider === "abo") {
      var m = (answer && answer.model) || r.model;
      return tr("answeredBy") + ": " + quotaLabel("abo") + " · " + (m || "?") + (answer && answer.profile ? " (" + answer.profile + ")" : "");
    }
    if (r && r.kind === "byok") return tr("answeredBy") + ": " + routeLabel(r);
    if (answer && answer.provider) {
      // Lokal: die CLI, die wirklich geantwortet hat, und welche davor übersprungen wurden (Ausweichliste).
      var skipped = (answer.fallback_from || []).map(function (f) {
        return trf("answeredInstead", { s: f.cli_name || cliName(f.provider), r: tr("kind_" + (f.kind || "error")) });
      });
      if (skipped.length) refreshLocalSoon();
      return tr("answeredBy") + ": " + tr("stLocalTitle") + " · " + (answer.cli_name || cliName(answer.provider)) +
        (answer.model ? " · " + answer.model : "") + (skipped.length ? " (" + skipped.join("; ") + ")" : "");
    }
    return "";
  }
  // Zwischenstand, wenn die gewählte CLI am Kontingent/an der Erreichbarkeit scheitert und die nächste übernimmt.
  function fallbackText(ev) {
    ev = ev || {};
    return trf("fallbackNow", { s: ev.from_name || cliName(ev.from), r: tr("kind_" + (ev.kind || "error")), t: ev.to_name || cliName(ev.to) });
  }
  // Nach einem Ausweichen den Zustand der CLIs neu holen (die übersprungene steht dann z. B. auf „Kontingent erschöpft“).
  var refreshTimer = null;
  function refreshLocalSoon() {
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(function () {
      if (state.backend && state.backend.base) probeLocal(true);
      else { backendPromise = null; backendStatus(); }
    }, 300);
  }
  // Fehler mit Art statt Text: "local" = lokalen Dienst nehmen, "none" = kein Zugang (reason für gate()).
  function routeError(code, r) {
    var e = new Error(code === "local" ? "local-route" : "no-route");
    e.name = "AiAccessRouteError";
    e.code = code;
    e.route = r || null;
    e.reason = (r && r.reason) || (code === "none" ? "key" : "");
    return e;
  }
  // Ein Aufruf beim Anbieter der Route (eigener Schlüssel, eigener Endpunkt oder Projektkontingent).
  async function runChat(r, prompt, onDelta, opt) {
    var v = vault(), p = provOf(r.provider, v), quotaRoute = isQuota(r.provider);
    if (quotaRoute ? !(quotaUsable(r.provider) && state.fb) : !(p && v.providers[r.provider])) {
      throw routeError("none", { kind: "none", reason: requiresSignIn() && !state.user ? "signin" : "key" });
    }
    var cred = quotaRoute ? await state.fb.auth.currentUser.getIdToken() : v.providers[r.provider].key;
    // Lange Wartezeiten (Gemini-Abo): bei jeder Abfrage ein frisches ID-Token.
    if (quotaRoute) opt = Object.assign({}, opt || {}, { token: function () { return state.fb.auth.currentUser.getIdToken(); } });
    var reply;
    try { reply = await p.chat(cred, r.model, prompt, onDelta, opt); }
    catch (e) {
      if (e && e.name === "AbortError") throw e;
      if (r.provider === "project" && e.status === 403) throw new Error(tr("projDenied"));
      if (!quotaRoute && [401, 402, 403].indexOf(e.status) !== -1) markKey(r.provider, true);
      throw e;
    }
    if (!quotaRoute) markKey(r.provider, false);
    return reply;
  }
  // Gemini-Abo: Auftrag an den Dienst (POST /abo/jobs), dann Status abfragen, bis der Läufer geantwortet hat.
  // Kein Streaming; opt.onStatus bekommt „Wartet auf Läufer…“ bzw. „Modell denkt…“ mit der Wartezeit.
  function aboWait(ms, signal) {
    return new Promise(function (resolve, reject) {
      var t = setTimeout(resolve, ms);
      if (signal) signal.addEventListener("abort", function () { clearTimeout(t); reject(abortErr()); }, { once: true });
    });
  }
  function abortErr() {
    try { return new DOMException("The operation was aborted.", "AbortError"); }
    catch (e) { var x = new Error("aborted"); x.name = "AbortError"; return x; }
  }
  function clock(ms) {
    var s = Math.max(0, Math.round(ms / 1000));
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  }
  function waitSpan(sec) {
    var m = Math.max(1, Math.round((sec || 0) / 60));
    return m >= 60 ? Math.floor(m / 60) + " h " + (m % 60 ? (m % 60) + " min" : "") : m + " min";
  }
  function aboStatusText(job, ms) {
    if (job.status === "running") return tr("aboThinking", clock(ms));
    var k = { busy: "aboWaitBusy", starting: "aboWaitStart", failed: "aboWaitFailed", none: "aboWaitNone" }[job.runner] || "aboWait";
    return tr(k, clock(ms)).replace("%d", String(job.dispatch_status || ""));
  }
  // Fehlercodes von Dienst und Läufer in Klartext (exhausted = agy_switch 75, login = 77).
  function aboError(code, detail, status) {
    var map = { exhausted: "aboErrExhausted", login: "aboErrLogin", no_runner: "aboErrNoRunner", timeout: "aboErrTimeout",
                denied: "aboErrDenied", empty: "pvEmpty", model_unavailable: "aboErrModel", abo_model: "aboErrModel",
                abo_model_not_granted: "aboErrModel", abo_not_allowed: "aboOnlyOwn", abo_no_grant: "aboErrGrant",
                abo_too_large: "aboErrTooLarge", abo_off: "aboErrOff", decrypt: "aboErrKey", cancelled: "aboErrCancelled",
                too_large: "aboErrTooLarge" };
    var key = map[code];
    var e = new Error(key ? tr(key, code === "exhausted" ? waitSpan(detail && detail.wait_s) : undefined) : tr("aboErrOther", String(code || status || "?")));
    e.code = code || "";
    if (status) e.status = status;
    return e;
  }
  async function aboFail(res) {
    var j = null;
    try { j = await res.json(); } catch (e) { j = null; }
    var c = j && j.error && j.error.code;
    if (c) return aboError(c, null, res.status);
    var e = new Error("HTTP " + res.status + (j && j.error && j.error.message ? " – " + j.error.message : ""));
    e.status = res.status;
    return e;
  }
  async function aboChat(model, prompt, onDelta, opt) {
    opt = opt || {};
    var cfg = state.config || {};
    var pollMs = Number(cfg.abo_poll_ms) || 2000, maxMs = Number(cfg.abo_max_ms) || 12 * 60000;
    var token = opt.token || function () { return state.fb.auth.currentUser.getIdToken(); };
    var status = opt.onStatus || function () {};
    var signal = opt.signal;
    var t0 = Date.now();
    status(tr("aboSending"), null);
    var res = await fetch(projectBase() + "/abo/jobs", { method: "POST", signal: signal,
      headers: { Authorization: "Bearer " + await token(), "Content-Type": "application/json" },
      body: JSON.stringify({ model: model, prompt: prompt }) });
    if (!res.ok) throw await aboFail(res);
    var job = await readJson(res), id = job.id;
    var cancel = function () {
      token().then(function (t) {
        return fetch(projectBase() + "/abo/jobs/" + encodeURIComponent(id), { method: "DELETE", headers: { Authorization: "Bearer " + t } });
      }).catch(function () { /* der Dienst räumt nach Ablauf selbst auf */ });
    };
    var misses = 0;
    try {
      for (;;) {
        status(aboStatusText(job, Date.now() - t0), job);
        if (Date.now() - t0 > maxMs) { cancel(); throw aboError("timeout"); }
        await aboWait(pollMs, signal);
        var r;
        try {
          r = await fetch(projectBase() + "/abo/jobs/" + encodeURIComponent(id), { signal: signal,
            headers: { Authorization: "Bearer " + await token() } });
        } catch (e) {
          if (e && e.name === "AbortError") throw e;
          if (++misses > 5) throw e;          // kurze Netzstörung: weiter abfragen
          continue;
        }
        if (!r.ok) throw await aboFail(r);
        misses = 0;
        job = await readJson(r);
        if (job.status === "done") {
          var text = String(job.answer || "");
          if (opt.meta) { opt.meta.profile = job.profile || ""; opt.meta.model = job.model || model; }
          if (onDelta && text) onDelta(text, text);
          return text;
        }
        if (job.status === "error" || job.status === "cancelled") throw aboError(job.status === "cancelled" ? "cancelled" : job.error, job.detail);
      }
    } catch (e) {
      if (e && e.name === "AbortError") cancel();
      throw e;
    }
  }
  // Alle nutzbaren Modelle über alle Quellen, in der Reihenfolge der Statusseite – für Auswahllisten
  // außerhalb des Dialogs (Vorschau im Kurationsfenster). Je Eintrag:
  // { source: "local"|"project"|"byok", provider, model, label, group, current[, healthy|failed] }.
  function models() {
    if (requiresSignIn() && !state.user) return [];
    var v = vault(), r = routeSync(), b = state.backend, by = { local: [], project: [], byok: [] };
    ((b && b.clis) || []).forEach(function (c) {
      by.local.push({ source: "local", provider: c.id, model: c.model, label: c.label || c.id, group: tr("local"), healthy: !!c.healthy,
                      cli: c.cli || c.id, status: c.status || "", runnable: c.runnable !== false });
    });
    if (quotaUsable()) {
      var gp = grantProvider();
      grantModels().forEach(function (m) {
        by.project.push({ source: "project", provider: gp, model: m, label: m, group: quotaLabel(gp) });
      });
    }
    keyIds(v).forEach(function (id) {
      // „eigener Schlüssel“ im Gruppennamen, damit z. B. Nexos mit eigenem Schlüssel nicht wie das Projektkontingent aussieht.
      var rec = v.providers[id], label = keyGroupLabel(id, v);
      (rec.models && rec.models.length ? rec.models : [rec.model]).filter(Boolean).forEach(function (m) {
        by.byok.push({ source: "byok", provider: id, model: m, label: m, group: label, failed: !!rec.failed });
      });
    });
    var out = [];
    accessOrder().forEach(function (k) { out = out.concat(by[k] || []); });
    var firstLocal = by.local.filter(function (x) { return x.healthy; })[0] || by.local[0];
    out.forEach(function (x) {
      // current = genau das Modell, das jetzt antworten würde (Reihenfolge + Wahl im Abschnitt).
      x.current = r.kind === "local" ? x.source === "local" && (r.cli ? x.provider === r.cli : x === firstLocal)
        : r.kind === "byok" && x.source !== "local" && x.provider === r.provider && x.model === r.model;
    });
    return out;
  }
  // Einfacher Prompt ohne Diskussionsrahmen über die angegebene oder die aktuelle Route.
  // opts: { route | source+provider+model, prompt, onDelta(delta, all), signal, maxTokens } → Promise<string>.
  // Lokale Route: wirft AiAccessRouteError mit code "local" (der Aufrufer nimmt localUrl(...));
  // kein Zugang: code "none" und reason für gate(reason).
  async function complete(opts) {
    opts = opts || {};
    var r = opts.route;
    if (!r && opts.provider) {
      r = opts.source === "local" || opts.provider === "local" ? { kind: "local", cli: opts.provider === "local" ? opts.model : opts.provider }
        : { kind: "byok", provider: opts.provider, model: opts.model };
    }
    if (!r) r = await route();
    if (r.kind === "local") throw routeError("local", r);
    if (r.kind !== "byok") throw routeError("none", r);
    var meta = {};
    var reply = await runChat(r, redact(String(opts.prompt || "")), opts.onDelta,
                              { signal: opts.signal, maxTokens: opts.maxTokens || 8192, onStatus: opts.onStatus, meta: meta });
    if (!pyStrip(reply || "")) throw new Error(tr("pvEmpty"));
    if (opts.meta) Object.assign(opts.meta, meta);
    return reply;
  }
  // opts.onStatus(text, job): Zwischenstand bei Routen ohne Streaming (Gemini-Abo: „Wartet auf Läufer…“, „Modell denkt…“).
  async function discuss(opts) {
    var r = opts.route || await route();
    if (r.kind !== "byok") throw new Error("no-byok-route");
    var prompt = redact(buildDiscussPrompt(opts.message, opts.context));
    var meta = {};
    var reply = await runChat(r, prompt, opts.onDelta, { onStatus: opts.onStatus, signal: opts.signal, meta: meta });
    if (!pyStrip(reply)) throw new Error("Leere Antwort vom Modell.");
    var recId = (opts.context && opts.context.record_id) || "";
    var f = extractFinding(reply, opts.message, recId);
    return { ok: true, reply: pyStrip(reply), suggestion: f.suggestion, rationale: f.rationale, finding: f.finding,
             provider: r.provider, model: meta.model || r.model, profile: meta.profile || "", mode: "byok" };
  }

  // --------------------------------------------------- Übergabe als Issue
  function repo() {
    var m = root.document && root.document.querySelector('meta[name="review-github-repo"]');
    return (m && m.content) || "2b-rs/autodocs";
  }
  function proposalIssue(p) {
    var payload = {
      schema: "ai-discussion-proposal@v1",
      record_id: p.record_id,
      attached_ids: p.attached_ids || [],
      suggestion: redact(p.suggestion),
      rationale: redact(p.rationale),
      provider: p.provider || "", model: p.model || "",
      page: root.location ? root.location.pathname : "",
      submitted_at: new Date().toISOString(),
      client: "autodocs-web", authority: "proposal-only"
    };
    var title = "Kuration: KI-Diskussionsvorschlag zu " + p.record_id;
    var body = "**KI-Diskussionsvorschlag** zu `" + p.record_id + "`\n\n" +
      "> " + payload.rationale.replace(/\n/g, "\n> ") + "\n\n" +
      "```json\n" + JSON.stringify(payload, null, 2) + "\n```\n";
    return { title: title, body: body, payload: payload };
  }
  async function openIssue(title, body) {
    var base = "https://github.com/" + repo() + "/issues/new?title=" + encodeURIComponent(title) + "&body=";
    var url = base + encodeURIComponent(body);
    var mode = "url";
    if (url.length > 7500) {
      try { await root.navigator.clipboard.writeText(body); } catch (e) { /* bleibt ohne Kopie */ }
      url = base + encodeURIComponent(tr("pasteHere"));
      mode = "clipboard";
    }
    root.open(url, "_blank", "noopener");
    toast(tr(mode === "clipboard" ? "issueClip" : "issueOpened"));
    return { mode: mode, url: url };
  }

  // ---------------------------------------------------------------- UI
  var dlg = null, sub = null, headerBtn = null;
  var G_LOGO = '<svg viewBox="0 0 48 48" width="18" height="18" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>';
  var APPLE_LOGO = '<svg viewBox="0 0 384 512" width="16" height="18" fill="currentColor" aria-hidden="true"><path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>';
  // Farbige Symbole für den KI-Knopf; die Verläufe stehen einmal in ICO_DEFS (mountHeader).
  var ICO_DEFS = '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>' +
    '<linearGradient id="aiaGold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff6c2"/><stop offset=".35" stop-color="#f7c948"/><stop offset=".7" stop-color="#c98a0b"/><stop offset="1" stop-color="#8a5a00"/></linearGradient>' +
    '<linearGradient id="aiaRed" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff7a7a"/><stop offset=".55" stop-color="#e02424"/><stop offset="1" stop-color="#9b1010"/></linearGradient>' +
    '<linearGradient id="aiaLid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff9a9a"/><stop offset="1" stop-color="#c81e1e"/></linearGradient>' +
    '<linearGradient id="aiaSteel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4f6f8"/><stop offset=".5" stop-color="#b9c0c8"/><stop offset="1" stop-color="#7d8792"/></linearGradient>' +
    '<linearGradient id="aiaScreen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#26324a"/><stop offset="1" stop-color="#0b1020"/></linearGradient>' +
    '<radialGradient id="aiaShine" cx=".3" cy=".25" r=".6"><stop offset="0" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>' +
    '<filter id="aiaGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation=".8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
    '<filter id="aiaDrop" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="1.2" stdDeviation="1" flood-color="#000" flood-opacity=".35"/></filter>' +
    "</defs></svg>";
  var ICO = {
    key: '<svg viewBox="0 0 32 32" aria-hidden="true"><g filter="url(#aiaDrop)">' +
      '<path d="M15.6 15.4 27 4l2.4 2.4-2 2 2 2-2.2 2.2-2-2-1.4 1.4 1.6 1.6-2.2 2.2-1.6-1.6-4.6 4.6z" fill="url(#aiaGold)" stroke="#7a4f00" stroke-width=".7"/>' +
      '<circle cx="10.5" cy="21.5" r="8" fill="url(#aiaGold)" stroke="#7a4f00" stroke-width=".8"/>' +
      '<circle cx="8.6" cy="23.4" r="2.6" fill="#5b3a00" opacity=".85"/><ellipse cx="8" cy="17.6" rx="4" ry="2.4" fill="url(#aiaShine)"/></g></svg>',
    giftClosed: '<svg viewBox="0 0 32 32" aria-hidden="true"><g filter="url(#aiaDrop)">' +
      '<rect x="5" y="14" width="22" height="15" rx="1.6" fill="url(#aiaRed)"/>' +
      '<rect x="3.5" y="10" width="25" height="5.5" rx="1.4" fill="url(#aiaLid)"/>' +
      '<rect x="14" y="10" width="4" height="19" fill="url(#aiaGold)"/>' +
      '<path d="M16 10c-1-4.5-6.5-6.5-7.5-3.4C7.7 9 12 10.2 16 10zM16 10c1-4.5 6.5-6.5 7.5-3.4C24.3 9 20 10.2 16 10z" fill="url(#aiaGold)" stroke="#8a5a00" stroke-width=".6"/>' +
      '<rect x="5.5" y="10.6" width="10" height="2" rx="1" fill="#fff" opacity=".35"/></g></svg>',
    giftOpen: '<svg viewBox="0 0 32 32" aria-hidden="true"><g filter="url(#aiaDrop)">' +
      '<rect x="5" y="16" width="22" height="13" rx="1.6" fill="url(#aiaRed)"/>' +
      '<rect x="14" y="16" width="4" height="13" fill="url(#aiaGold)"/>' +
      '<ellipse cx="16" cy="16.2" rx="11" ry="1.6" fill="#5c0b0b" opacity=".55"/>' +
      '<g transform="rotate(-24 5 12)"><rect x="3" y="9" width="24" height="5" rx="1.4" fill="url(#aiaLid)"/><rect x="13.5" y="9" width="4" height="5" fill="url(#aiaGold)"/></g>' +
      '<g fill="#ffe066" filter="url(#aiaGlow)"><path d="M20 3l.9 2.4 2.4.9-2.4.9L20 9.6l-.9-2.4-2.4-.9 2.4-.9z"/><path d="M26 8l.6 1.5 1.5.6-1.5.6L26 12.2l-.6-1.5-1.5-.6 1.5-.6z"/><circle cx="23.5" cy="13.2" r=".9"/></g></g></svg>',
    terminal: '<svg viewBox="0 0 32 32" aria-hidden="true"><g filter="url(#aiaDrop)">' +
      '<rect x="2.5" y="5" width="27" height="21" rx="3" fill="url(#aiaSteel)" stroke="#5f6873" stroke-width=".6"/>' +
      '<rect x="4.5" y="7" width="23" height="17" rx="1.6" fill="url(#aiaScreen)"/>' +
      '<g filter="url(#aiaGlow)" stroke="#3dff8b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"><path d="m8 11.5 4 3.5-4 3.5"/><path d="M14.5 19.5h6"/></g>' +
      '<path d="M4.5 7h23v5c-8 1.5-15 1.5-23 0z" fill="#fff" opacity=".08"/><rect x="11" y="26" width="10" height="2" rx="1" fill="url(#aiaSteel)"/></g></svg>'
  };
  var GH_LOGO = '<svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/></svg>';
  var SPARK = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg>';
  function initials(u) {
    var s = (u && (u.name || u.email)) || "?";
    return s.trim().charAt(0).toUpperCase();
  }
  function firstName(u) { return u ? ((u.name || "").split(/\s+/)[0] || (u.email || "").split("@")[0]) : ""; }
  function avatar(u, size) {
    if (u && u.photo) return '<img class="aia-avatar" src="' + esc(u.photo) + '" alt="" width="' + size + '" height="' + size + '" referrerpolicy="no-referrer">';
    return '<span class="aia-avatar aia-avatar-i" style="width:' + size + "px;height:" + size + 'px">' + esc(initials(u)) + "</span>";
  }
  function shortSource(r) {
    if (r.kind === "local") return r.cli ? cliName(r.cli) : (state.backend && state.backend.active) || tr("stLocal");
    if (r.provider === "project") return tr("viaProject");
    if (r.provider === "abo") return "Gemini-Abo";
    return { gemini: "Gemini", anthropic: "Claude", openai: "OpenAI", nexos: "Nexos" }[r.provider] || providerLabel(r.provider);
  }
  function renderHeader() {
    if (!headerBtn) return;
    headerBtn.hidden = false;
    var r = routeSync(), ok = r.kind !== "none", h = accessHealth();
    var badge = "";
    var label = ok ? tr("hdrKi") + ": " + shortSource(r) : tr("headerConnect");
    var icons = accessIcons();
    var label2 = icons.length ? tr("hdrKi") : tr("headerConnect");
    // Ein Klick auf ein Symbol setzt dessen Quelle an Rang 1 (promoteSource); sonst öffnet der Knopf den Dialog.
    headerBtn.innerHTML = SPARK + '<span class="aia-hname">' + esc(label2) + "</span>" +
      icons.map(function (i) {
        return '<span class="aia-ico ' + i.cls + '" data-aia-src="' + i.src + '" title="' + esc(i.tip + " · " + tr("icoPromote")) + '">' + i.ico + "</span>";
      }).join("") + badge;
    var htxt = icons.map(function (i) { return i.tip; }).join(", ") || tr("hdrNone");
    headerBtn.setAttribute("aria-label", label2 + " – " + htxt);
    headerBtn.title = htxt;
    syncDiscussControls(ok);
    headerBtn.classList.toggle("is-in", !!state.user);
    if (adminBtn) {
      adminBtn.hidden = !quota.admin;
      var fbNew = fbNewCount(), pending = quota.open.length + fbNew;
      adminBtn.innerHTML = ICO_ADMIN + "<span>" + esc(tr("admBtn")) + "</span>" +
        (pending ? '<span class="aia-badge">' + pending + "</span>" : "");
      adminBtn.title = tr("admTitle") + ": " + quota.open.length + " · " + tr("fbAdmTitle") + ": " + tr("fbAdmNew", String(fbNew));
    }
    document.querySelectorAll("[data-aia-chip]").forEach(updateChip);
  }
  var DISCUSS_CONTROLS = "[data-open-discuss], .curation-btn[data-action=\"discuss\"], .btn-toggle-workbench-chat";
  function syncDiscussControls(ok) {
    document.querySelectorAll(DISCUSS_CONTROLS).forEach(function (el) {
      el.classList.toggle("aia-off", !ok);
      // Bedienbar bleiben (der Klick öffnet den KI-Dialog); der Hinweis steht im Tooltip.
      if (ok) { if (el.dataset.aiaTitle != null) { el.title = el.dataset.aiaTitle; delete el.dataset.aiaTitle; } }
      else { if (el.dataset.aiaTitle == null) el.dataset.aiaTitle = el.title || ""; el.title = tr("noAccessHint"); }
    });
  }
  function guardDiscussClicks() {
    document.addEventListener("click", function (e) {
      var el = e.target.closest && e.target.closest(DISCUSS_CONTROLS);
      if (!el || !el.classList.contains("aia-off")) return;
      e.preventDefault();
      e.stopImmediatePropagation();
      openDialog();
    }, true);
  }
  // Symbole wachsen bei Annäherung des Mauszeigers (wie ein Dock); bei reduzierter Bewegung nicht.
  function magnify(btn) {
    var mq = root.matchMedia && root.matchMedia("(prefers-reduced-motion: reduce)");
    var area = btn.closest("header") || document;
    function reset() { btn.querySelectorAll(".aia-ico").forEach(function (i) { i.style.transform = ""; }); }
    area.addEventListener("mousemove", function (e) {
      if (mq && mq.matches) return;
      btn.querySelectorAll(".aia-ico").forEach(function (i) {
        var r = i.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
        var f = Math.max(0, 1 - Math.sqrt(dx * dx + dy * dy) / 70);
        i.style.transform = f ? "scale(" + (1 + 0.75 * f).toFixed(3) + ")" : "";
      });
    });
    area.addEventListener("mouseleave", reset);
  }
  function srcName(src) { return tr(src === "local" ? "srcLocal" : src === "project" ? "srcProject" : "srcByok"); }
  // Quellen, die im Dialog als Abschnitt stehen, in ihrer Reihenfolge (Rang 1 = erster Eintrag).
  function shownSources() {
    return accessOrder().filter(function (k) { return k !== "project" || projectOffered(); });
  }
  // Kopfleiste: Symbol angeklickt → diese Quelle an Rang 1. Eine gerade nicht nutzbare Quelle (rot, oder Kontingent
  // nur angefragt) wird nicht still nach oben gesetzt: Hinweis und Dialog an ihrem Abschnitt, dort lässt sie sich
  // prüfen, einrichten oder trotzdem verschieben.
  function promoteSource(src) {
    var info = accessIcons().filter(function (i) { return i.src === src; })[0];
    var name = srcName(src);
    if (!info) { openDialog(); return; }
    if (info.cls === "is-bad" || info.usable === false) {
      openDialog();
      toast(trf("prioUnhealthy", { s: name, r: info.tip }));
      focusGrip(src);
      // openDialog setzt den Fokus kurz darauf auf das erste Bedienelement; danach wieder auf den Griff.
      setTimeout(function () { focusGrip(src); }, 80);
      return;
    }
    var shown = shownSources();
    if (shown[0] === src) { toast(trf("prioAlready", { s: name })); return; }
    moveSource(src, 0);
    var answers = routeSource(routeSync()) === src;
    toast(trf(answers ? "prioTop" : "prioTopWait", { s: name }));
    announce(trf("prioMoved", { s: name, n: 1, t: shownSources().length }));
  }
  var adminBtn = null;
  var ICO_ADMIN = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/><path d="m9 12 2 2 4-4"/></svg>';
  function mountHeader() {
    var host = document.querySelector("header.shell .shell-controls");
    if (!host || host.querySelector("[data-ai-account]")) return;
    headerBtn = document.createElement("button");
    headerBtn.type = "button";
    headerBtn.className = "aia-account-btn";
    headerBtn.setAttribute("data-ai-account", "");
    headerBtn.setAttribute("aria-haspopup", "dialog");
    headerBtn.hidden = true;
    var before = host.querySelector(".feedback-open, .reviewbar");
    host.insertBefore(headerBtn, before || null);
    headerBtn.addEventListener("click", function (e) {
      var ico = e.target && e.target.closest ? e.target.closest("[data-aia-src]") : null;
      if (ico && headerBtn.contains(ico)) { promoteSource(ico.getAttribute("data-aia-src")); return; }
      openDialog();
    });
    adminBtn = document.createElement("button");
    adminBtn.type = "button";
    adminBtn.className = "aia-admin-btn";
    adminBtn.setAttribute("data-ai-admin", "");
    adminBtn.setAttribute("aria-haspopup", "dialog");
    adminBtn.hidden = true;
    host.insertBefore(adminBtn, headerBtn.nextSibling);
    adminBtn.addEventListener("click", openAdmin);
    if (!document.getElementById("aiaGold")) document.body.insertAdjacentHTML("afterbegin", ICO_DEFS);
    magnify(headerBtn);
    renderHeader();
  }
  function defaultView() { return "account"; }
  // Verwaltung als eigenes Fenster (Knopf neben dem KI-Knopf), ohne die Statusseite darunter.
  function openAdmin() {
    ensureDialogs();
    state.error = "";
    if (dlg.open) dlg.close();
    state.view = "admin";
    renderDialog();
    loadAdmin().then(emit).catch(fail);
  }
  // Hauptdialog = Statusseite; BYOK hinzufügen, Kontingent anfragen und Verwaltung als modales Popup darüber.
  function makeDialog(cls, label) {
    var d = document.createElement("dialog");
    d.className = cls;
    d.setAttribute("aria-labelledby", label);
    document.body.appendChild(d);
    d.addEventListener("click", onDialogClick);
    d.addEventListener("submit", onDialogSubmit);
    d.addEventListener("change", onDialogChange);
    d.addEventListener("input", onDialogInput);
    d.addEventListener("keydown", onDialogKeydown);
    d.addEventListener("click", function (e) { if (e.target === d) d.close(); });
    return d;
  }
  function ensureDialogs() {
    if (!dlg) {
      dlg = makeDialog("aia-dialog", "aia-title");
      sub = makeDialog("aia-dialog aia-sub", "aia-subtitle");
      dlg.addEventListener("close", function () { if (sub.open) sub.close(); });
      sub.addEventListener("close", function () {
        if (state.view !== "account") { state.view = "account"; state.error = ""; renderDialog(); }
      });
      bindReorder(dlg);
    }
  }
  function openDialog(view) {
    ensureDialogs();
    state.error = "";
    state.view = view || defaultView();
    // Statusseite zuerst öffnen, damit ein Popup (BYOK, Anfrage, Verwaltung) darüber liegt.
    if (!dlg.open) { if (sub.open) sub.close(); try { dlg.showModal(); } catch (e) { dlg.setAttribute("open", ""); } }
    renderDialog();
    loadConfig().then(function () {
      backendStatus();
      // Vorladen, damit der Klick auf „Mit Google fortfahren“ das Popup direkt öffnen darf.
      if (state.auth !== "unconfigured" && (signInOffered() || sget("local", SESSION_FLAG))) ensureFirebase();
      renderDialog();
    });
    var f = dlg.querySelector("[autofocus]") || dlg.querySelector("button.aia-google, input, button");
    if (f) setTimeout(function () { try { f.focus(); } catch (e) { /* ignore */ } }, 30);
  }
  function errLine() { return state.error ? '<p class="aia-error" role="alert">' + esc(state.error) + "</p>" : ""; }
  function closeBtn() {
    return '<button type="button" class="aia-x" data-aia="close" aria-label="' + esc(tr("close")) + '">✕</button>';
  }
  // Anmeldung als zweiter Weg zum selben Ziel (nur wenn zugeschaltet), unter dem Schlüsselfeld.
  // Welche Anmeldewege angeboten werden: ai-access.config.json "anbieter" (Standard Google, GitHub, E-Mail).
  function offers(name) {
    var list = (state.config && state.config.anbieter) || ["google", "github", "email"];
    return list.indexOf(name) !== -1;
  }
  function signInBlock(plain) {
    var off = state.auth === "unconfigured";
    var busy = state.auth === "loading";
    var dis = off || busy ? " disabled" : "";
    return '<section class="aia-sec aia-signin">' + (plain ? "" : '<div class="aia-or"><span>' +
      esc(tr(requiresSignIn() ? "signInRequired" : "orSignIn")) + "</span></div>") +
      (off ? '<p class="aia-note">' + esc(tr("setup")) + "</p>" : "") +
      (offers("google") ? '<button type="button" class="aia-google" data-aia="google"' + dis + ">" + G_LOGO + "<span>" + esc(tr("google")) + "</span></button>" : "") +
      (offers("apple") ? '<button type="button" class="aia-google aia-apple" data-aia="apple"' + dis + ">" + APPLE_LOGO + "<span>" + esc(tr("apple")) + "</span></button>" : "") +
      (offers("github") ? '<button type="button" class="aia-google aia-github" data-aia="github"' + dis + ">" + GH_LOGO + "<span>" + esc(tr("github")) + "</span></button>" : "") +
      (offers("email") ? '<form class="aia-row" data-aia-form="mail"><input type="email" name="email" required autocomplete="email" placeholder="' +
        esc(tr("mailPh")) + '" aria-label="E-Mail"' + (off ? " disabled" : "") + ' value="' + esc(state.pendingEmail || "") + '">' +
        '<button type="submit" class="aia-btn"' + dis + ">" + esc(tr("sendLink")) + "</button></form>" : "") +
      '<p class="aia-fine">' + esc(tr("fine")) + "</p></section>";
  }
  function viewSent() {
    return closeBtn() +
      '<div class="aia-hero"><div class="aia-mark aia-mail">✉</div><h2 id="aia-title">' + esc(tr("sentTitle")) + "</h2>" +
      "<p>" + tr("sentLead", "<strong>" + esc(state.pendingEmail) + "</strong>") + "</p></div>" +
      '<details class="aia-other"><summary>' + esc(tr("otherDevice")) + "</summary><p>" + esc(tr("pasteLead")) + "</p>" +
      '<form class="aia-row" data-aia-form="paste"><input type="url" name="link" required placeholder="' + esc(tr("pastePh")) + '" aria-label="Link">' +
      '<button type="submit" class="aia-btn">' + esc(tr("pasteGo")) + "</button></form></details>" +
      errLine() +
      '<p class="aia-fine">' + esc(tr("noMail")) + ' <button type="button" class="aia-link" data-aia="resend">' + esc(tr("resend")) +
      '</button> · <button type="button" class="aia-link" data-aia="restart">' + esc(tr("otherMail")) + "</button></p>";
  }
  function viewConfirm() {
    return closeBtn() +
      '<div class="aia-hero"><div class="aia-mark aia-mail">✉</div><h2 id="aia-title">' + esc(tr("confirmTitle")) + "</h2><p>" +
      esc(tr("confirmLead")) + "</p></div>" +
      '<form class="aia-row" data-aia-form="confirm"><input type="email" name="email" required autocomplete="email" autofocus placeholder="' +
      esc(tr("mailPh")) + '" aria-label="E-Mail"><button type="submit" class="aia-btn">' + esc(tr("confirmGo")) + "</button></form>" + errLine();
  }
  var connectSel = "gemini", keyStatus = { text: "", kind: "" };
  // Ein Klick auf eine Karte verbindet sofort mit dem eingegebenen Schlüssel; ohne Schlüssel merkt
  // sie sich den Anbieter, und Enter im Schlüsselfeld verbindet dann.
  function providerCards() {
    var v = vault();
    return '<p class="aia-label" id="aia-provpick">' + esc(tr("provPick")) + '</p><div class="aia-provs" role="group" aria-labelledby="aia-provpick">' +
      ORDER.map(function (id) {
        var p = PROVIDERS[id];
        // Hinweis nur über dem Info-Zeichen (Maus oder Tastaturfokus), nicht über der ganzen Karte.
        var tag = p.free ? '<span class="aia-tag">' + esc(tr("freeKey")) +
          ' <span class="aia-info" tabindex="0" role="img" aria-label="Info" aria-describedby="aia-tip-' + id + '">ⓘ</span></span>' : "";
        var tip = p.free ? '<span class="aia-tip" role="tooltip" id="aia-tip-' + id + '">' + esc(tr("geminiNote")) + "</span>" : "";
        var done = v.providers[id] ? ' <span class="aia-ok" aria-hidden="true">✓</span>' : "";
        return '<div class="aia-prov' + (connectSel === id ? " is-sel" : "") + '" data-aia-card="' + id + '">' +
          '<button type="button" class="aia-prov-pick" aria-pressed="' + (connectSel === id) + '" data-aia-prov="' + id + '">' +
          "<strong>" + esc(p.label) + done + "</strong></button>" + tag +
          '<a class="aia-prov-key" href="' + esc(p.keyUrl) + '" target="_blank" rel="noopener">' + esc(tr("keyCreate")) + " ↗</a>" + tip + "</div>";
      }).join("") + "</div>";
  }
  function localSection() {
    var b = state.backend;
    if (!b || !b.clis.length) return "";
    var active = localChain(picks()).cli;
    return '<section class="aia-sec"><h3>' + esc(tr("local")) + '</h3><p class="aia-fine">' + esc(tr("localFound")) + "</p><ul class=\"aia-list\">" +
      b.clis.map(function (c) {
        var on = active === c.id;
        return "<li><span><strong>" + esc(c.cli || c.label) + "</strong> " + esc(c.model) + "</span>" +
          (on ? '<span class="aia-ok">✓</span>' : '<button type="button" class="aia-btn aia-btn-quiet" data-aia-local="' + esc(c.id) + '">' + esc(tr("useThis")) + "</button>") + "</li>";
      }).join("") + "</ul></section>";
  }
  function providerName(id) {
    return { "google.com": "Google", "github.com": "GitHub", "apple.com": "Apple", password: tr("stViaMail"), emailLink: tr("stViaMail") }[id] || id || "";
  }
  function awayHtml() {
    var a = state.away, host = localBase().replace(/^https?:\/\//, "");
    var out = '<p class="aia-fine aia-left">' + esc(tr("localOnlyLocal")) + "</p>";
    if (a && a.found) {
      out = '<ul class="aia-list">' + a.clis.map(function (c) {
          return '<li><span><span class="aia-dot ' + (c.healthy ? "is-ok" : "is-bad") + '"></span>' + esc(c.label) + "</span></li>";
        }).join("") + '</ul><p class="aia-left">' + esc(tr("localFoundAway", host)) + ' <a href="' +
        esc(a.base + root.location.pathname + root.location.search) + '">' + esc(tr("localOpen")) + " ↗</a></p>";
    } else if (a && !a.busy) {
      out += '<p class="aia-fine aia-left">' + esc(tr("localNotFound", host)) + "</p>";
    }
    return out + '<p><button type="button" class="aia-btn aia-btn-quiet" data-aia="probe"' + (a && a.busy ? " disabled" : "") + ">↻ " +
      esc(tr("localProbe")) + "</button></p>";
  }
  // Verwalter: über welches Nexos-Konto (und in welcher Reihenfolge) das Projektkontingent abgerechnet wird.
  function billingForm() {
    var st = quota.settings || { nexos: "1", openai: "nein" };
    var acc = function (n) { return tr("admAcc" + n); };
    return '<section class="aia-sec"><h3>' + esc(tr("admBilling")) + '</h3><form class="aia-key" data-aia-form="settings">' +
      '<label class="aia-label" for="aia-billvia">' + esc(tr("admBillVia")) + '</label><select id="aia-billvia" class="aia-input" name="nexos">' +
      [["1", acc(1)], ["2", acc(2)], ["1,2", acc(1) + " → " + acc(2)], ["2,1", acc(2) + " → " + acc(1)]].map(function (o) {
        return '<option value="' + o[0] + '"' + (st.nexos === o[0] ? " selected" : "") + ">" + esc(o[1]) + "</option>";
      }).join("") + "</select>" +

      '<label class="aia-check"><input type="checkbox" name="openai"' + (st.openai === "ja" ? " checked" : "") + "> " + esc(tr("admOpenai")) + "</label>" +
      '<button type="submit" class="aia-btn">' + esc(tr("admSave")) + '</button><p class="aia-fine">' + esc(tr("admBillHint")) + "</p></form></section>";
  }
  // Kopf eines verschiebbaren Abschnitts: Griff (ziehen mit Maus/Finger, Pfeiltasten), Rangnummer, Titel und
  // „antwortet“ am Abschnitt, der gerade antworten würde. Rang und Beschriftung setzt statusPanel.
  function secHead(id, title, answering) {
    return '<section class="aia-sec aia-prio" data-aia-sec="' + id + '"><div class="aia-sechead">' +
      '<button type="button" class="aia-grip" data-aia-grip="' + id + '" aria-describedby="aia-prio-help" aria-keyshortcuts="ArrowUp ArrowDown"></button>' +
      '<span class="aia-rank" data-aia-prio-n aria-hidden="true"></span><h3>' + esc(title) + "</h3>" +
      (answering ? '<span class="aia-now">' + esc(tr("answersNow")) + "</span>" : "") + "</div>";
  }
  // Ansage für Screenreader (Verschieben per Tastatur oder Symbol); bleibt beim Neuzeichnen erhalten.
  var liveEl = null;
  function announce(msg) {
    if (!root.document || !msg) return;
    if (!liveEl) {
      liveEl = document.createElement("div");
      liveEl.className = "visually-hidden";
      liveEl.setAttribute("aria-live", "polite");
      liveEl.setAttribute("data-aia-live", "");
    }
    var host = dlg && dlg.open ? dlg : document.body;
    if (liveEl.parentNode !== host) host.appendChild(liveEl);
    liveEl.textContent = "";
    setTimeout(function () { liveEl.textContent = msg; }, 30);
  }
  function focusGrip(src) {
    var g = dlg && dlg.querySelector('[data-aia-grip="' + src + '"]');
    if (!g) return;
    try { g.focus(); } catch (e) { /* ignore */ }
    if (g.scrollIntoView) try { g.scrollIntoView({ block: "nearest" }); } catch (e) { /* ignore */ }
  }
  // Abschnitt src vor den Abschnitt before setzen (null = ans Ende der angezeigten), in der vollen Reihenfolge.
  function placeSource(src, before) {
    var shown = shownSources(), o = accessOrder().filter(function (x) { return x !== src; });
    var at;
    if (before) at = o.indexOf(before);
    else {
      var last = shown.filter(function (x) { return x !== src; }).pop();
      at = last ? o.indexOf(last) + 1 : o.length;
    }
    o.splice(Math.max(0, at), 0, src);
    if (o.join() === accessOrder().join()) return false;
    sset("local", ORDER_KEY, JSON.stringify(o));
    emit();
    var n = shownSources().indexOf(src) + 1;
    announce(trf("prioMoved", { s: srcName(src), n: n, t: shownSources().length }));
    return true;
  }
  // Sortieren mit Zeigerereignissen statt HTML5-Drag&Drop (kein durchscheinendes Abbild mit blauem Schatten):
  // ein kleines deckendes Schild mit Griff, Rang und Titel folgt dem Zeiger senkrecht, der Abschnitt bleibt als
  // ruhige Fläche stehen, eine schmale Linie zeigt, wo er landet. Die anderen Abschnitte bleiben sichtbar.
  // Tastatur: Griff fokussieren, Pfeil hoch/runter (Pos1/Ende: ganz nach oben/unten). Esc bricht das Ziehen ab.
  function bindReorder(d) {
    var drag = null;
    function sections() { return Array.prototype.slice.call(d.querySelectorAll("[data-aia-sec]")); }
    function cleanup() {
      if (!drag) return;
      drag.sec.classList.remove("is-source");
      if (drag.chip && drag.chip.parentNode) drag.chip.parentNode.removeChild(drag.chip);
      if (drag.line && drag.line.parentNode) drag.line.parentNode.removeChild(drag.line);
      d.classList.remove("aia-sorting");
      try { drag.grip.releasePointerCapture(drag.pointerId); } catch (x) { /* schon frei */ }
      drag = null;
    }
    function start() {
      var body = drag.sec.parentNode, secs = sections();
      drag.others = secs.filter(function (x) { return x !== drag.sec; });
      var head = drag.sec.querySelector(".aia-sechead"), hr = head.getBoundingClientRect();
      var top = secs[0].getBoundingClientRect().top, bottom = secs[secs.length - 1].getBoundingClientRect().bottom;
      drag.body = body;
      drag.line = document.createElement("div");
      drag.line.className = "aia-drop-line";
      drag.line.setAttribute("aria-hidden", "true");
      body.appendChild(drag.line);
      // Schild: Griff, Rang, Titel; deckend, liegt in der obersten Ebene des Dialogs.
      drag.chip = document.createElement("div");
      drag.chip.className = "aia-drag-chip";
      drag.chip.setAttribute("aria-hidden", "true");
      var rank = head.querySelector("[data-aia-prio-n]"), h3 = head.querySelector("h3");
      drag.chip.innerHTML = '<span class="aia-grip" aria-hidden="true"></span><span class="aia-rank" data-aia-prio-n="' +
        esc(rank ? rank.getAttribute("data-aia-prio-n") : "") + '"></span><span class="aia-drag-title">' + esc(h3 ? h3.textContent : "") + "</span>";
      d.appendChild(drag.chip);
      drag.chip.style.left = Math.round(hr.left - 6) + "px";
      drag.chipY0 = hr.top - 5;
      drag.minY = top - 5;
      drag.maxY = bottom - drag.chip.offsetHeight;
      drag.chip.style.top = Math.round(drag.chipY0) + "px";
      drag.sec.classList.add("is-source");
      d.classList.add("aia-sorting");
      drag.started = true;
    }
    function target(y) {
      var i = 0;
      drag.others.forEach(function (x) { var b = x.getBoundingClientRect(); if (y > b.top + b.height / 2) i++; });
      return i;
    }
    function showLine(i) {
      var br = drag.body.getBoundingClientRect(), o = drag.others, y;
      if (!o.length) return;
      if (i < o.length) y = o[i].getBoundingClientRect().top - 7;
      else y = o[o.length - 1].getBoundingClientRect().bottom + 5;
      drag.line.style.top = Math.round(y - br.top) + "px";
    }
    d.addEventListener("pointerdown", function (e) {
      var grip = e.target.closest && e.target.closest("[data-aia-grip]");
      if (!grip || e.button !== 0 || !d.contains(grip)) return;
      var sec = grip.closest("[data-aia-sec]");
      if (!sec) return;
      e.preventDefault();
      try { grip.setPointerCapture(e.pointerId); } catch (x) { /* ältere Browser */ }
      drag = { id: sec.getAttribute("data-aia-sec"), sec: sec, grip: grip, y0: e.clientY, pointerId: e.pointerId, started: false, index: null };
    });
    d.addEventListener("pointermove", function (e) {
      if (!drag || e.pointerId !== drag.pointerId) return;
      var dy = e.clientY - drag.y0;
      if (!drag.started) { if (Math.abs(dy) < 4) return; start(); }
      e.preventDefault();
      drag.chip.style.top = Math.round(Math.max(drag.minY, Math.min(drag.maxY, drag.chipY0 + dy))) + "px";
      drag.index = target(e.clientY);
      showLine(drag.index);
    });
    function finish(e) {
      if (!drag || (e && e.pointerId !== drag.pointerId)) return;
      var id = drag.id, idx = drag.index, others = (drag.others || []).map(function (x) { return x.getAttribute("data-aia-sec"); });
      var moved = drag.started && idx !== null;
      var grip = drag.grip;
      cleanup();
      if (!moved) return;
      if (placeSource(id, idx < others.length ? others[idx] : null)) focusGrip(id);
      else try { grip.focus(); } catch (x) { /* ignore */ }
    }
    d.addEventListener("pointerup", finish);
    d.addEventListener("pointercancel", function () { cleanup(); });
    d.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && drag) { e.preventDefault(); e.stopPropagation(); cleanup(); return; }
      var grip = e.target.closest && e.target.closest("[data-aia-grip]");
      if (!grip || e.altKey || e.ctrlKey || e.metaKey) return;
      var id = grip.getAttribute("data-aia-grip");
      var shown = sections().map(function (x) { return x.getAttribute("data-aia-sec"); });
      var i = shown.indexOf(id), j = { ArrowUp: i - 1, ArrowDown: i + 1, Home: 0, End: shown.length - 1 }[e.key];
      if (j === undefined) return;
      e.preventDefault();
      if (j < 0 || j >= shown.length || j === i) { announce(trf("prioMoved", { s: srcName(id), n: i + 1, t: shown.length })); return; }
      var rest = shown.filter(function (x) { return x !== id; });
      placeSource(id, j < rest.length ? rest[j] : null);
      focusGrip(id);
    });
  }
  // Abschnitt „Lokale KI-CLIs“: jede gefundene CLI mit Zustand, genau eine aktiv (Auswahlknopf), dazu optional bis
  // zu MAX_LOCAL - 1 Ausweich-CLIs in fester Reihenfolge. Die nächste antwortet nur, wenn die vorige am Kontingent
  // oder an der Erreichbarkeit scheitert (ai_agent_bridge.stream_with_fallback).
  // „codex-cli 0.162.0“, „2.1.287 (Claude Code)“, „grok 1.0.41 (4220f3b) [stable]“ → nur die Versionsnummer.
  function shortVersion(v) {
    var m = String(v || "").match(/\d+(?:\.\d+)+(?:-[0-9a-z]+)?/i);
    return m ? m[0] : String(v || "").slice(0, 24);
  }
  function cliMeta(c) {
    var model = !c.model ? tr("cliDefaultModel") : c.label && c.label !== c.cli && c.label.indexOf(c.cli + " · ") !== 0 ? c.label : c.model;
    return [c.version ? shortVersion(c.version) : "", model].filter(Boolean).join(" · ");
  }
  function localClis(pk) {
    var b = state.backend, clis = (b && b.clis) || [];
    if (!clis.length) return "";
    var c = localChain(pk), max = Math.max(1, Math.min(MAX_LOCAL, b.max || MAX_LOCAL));
    var rows = clis.map(function (x) {
      var on = x.id === c.cli, fbn = c.fallback.indexOf(x.id);
      var st = x.healthy ? "is-ok" : x.status === "untested" ? "is-off" : x.status === "quota" ? "is-warn" : "is-bad";
      return '<li class="aia-cli' + (on ? " is-active" : "") + '"><label class="aia-cli-pick">' +
        '<input type="radio" name="aia-cli" value="' + esc(x.id) + '" data-aia-cli' + (on ? " checked" : "") + ">" +
        '<span class="aia-dot ' + st + '"></span><span class="aia-cli-text"><strong>' + esc(x.cli) + "</strong>" +
        (cliMeta(x) ? " <small>" + esc(cliMeta(x)) + "</small>" : "") + "</span></label>" +
        '<span class="aia-cli-st ' + st + '"' + (x.error && !x.healthy ? ' title="' + esc(x.error) + '"' : "") + ">" +
        esc((fbn !== -1 ? trf("cliFbShort", { s: fbn + 1 }) + " · " : "") + (tr("st_" + x.status) !== "st_" + x.status ? tr("st_" + x.status) : x.status)) + "</span></li>";
    }).join("");
    var fb = "";
    if (clis.length > 1 && max > 1) {
      var sel = [];
      for (var i = 0; i < max - 1; i++) {
        if (i > 0 && !c.fallback[i - 1]) break;
        var taken = [c.cli].concat(c.fallback.slice(0, i));
        sel.push('<select class="aia-input aia-fb-sel" data-aia-fb="' + i + '" aria-label="' + esc(trf("cliFallbackN", { s: i + 1 })) + '">' +
          '<option value="">' + esc(tr("cliFallbackNone")) + "</option>" +
          clis.filter(function (x) { return taken.indexOf(x.id) === -1; }).map(function (x) {
            return '<option value="' + esc(x.id) + '"' + (c.fallback[i] === x.id ? " selected" : "") + ">" + esc(x.cli) + "</option>";
          }).join("") + "</select>");
      }
      fb = '<div class="aia-fb"><p class="aia-label" id="aia-fb-label">' + esc(tr("cliFallback")) + "</p>" +
        '<div class="aia-fb-row" role="group" aria-labelledby="aia-fb-label">' + sel.join('<span class="aia-fb-arrow" aria-hidden="true">→</span>') + "</div></div>";
    }
    return '<ul class="aia-list aia-clis" role="radiogroup" aria-label="' + esc(tr("cliActive")) + '">' + rows + "</ul>" + fb;
  }
  // Modellwahl im Abschnitt Projektkontingent: alle Modelle der eigenen Freigabe.
  function projectModelField(pk) {
    if (!quotaUsable()) return "";
    var gp = grantProvider(), gm = grantModels();
    if (!gm.length) return "";
    var cur = sourceRoute("project", vault(), pk);
    return '<div class="aia-modelrow"><label class="aia-label" for="aia-model-project">' + esc(tr("secModel")) + "</label>" +
      '<select id="aia-model-project" class="aia-input" data-aia-model="project"><optgroup label="' + esc(quotaLabel(gp)) + '" data-aia-group="' + gp + '">' +
      gm.map(function (m) {
        return '<option value="' + esc(gp + "|" + m) + '"' + (cur && cur.model === m ? " selected" : "") + ">" + esc(m) + "</option>";
      }).join("") + "</optgroup></select></div>";
  }
  // Modellwahl im Abschnitt Eigene Schlüssel: Modelle aller verbundenen Schlüssel, gruppiert nach Anbieter.
  function byokModelField(v, pk) {
    var ids = keyIds(v);
    if (!ids.length) return "";
    var cur = sourceRoute("byok", v, pk) || {};
    var groups = ids.map(function (id) {
      var rec = v.providers[id];
      var models = (rec.models && rec.models.length ? rec.models : [rec.model]).filter(Boolean);
      if (cur.provider === id && cur.model && models.indexOf(cur.model) === -1) models = [cur.model].concat(models);
      if (!models.length) models = [""];
      return '<optgroup label="' + esc(keyGroupLabel(id, v)) + '" data-aia-group="key">' + models.map(function (m) {
        return '<option value="' + esc(id + "|" + m) + '"' + (cur.provider === id && (cur.model || "") === m ? " selected" : "") + ">" + esc(m || tr("modelId")) + "</option>";
      }).join("") + "</optgroup>";
    });
    var manual = "", rec = cur.provider && v.providers[cur.provider];
    if (rec && !(rec.models && rec.models.length)) {
      manual = '<label class="aia-label" for="aia-mid">' + esc(tr("modelId")) + '</label><input id="aia-mid" class="aia-input" data-aia-manual="' +
        esc(cur.provider) + '" value="' + esc(cur.model || rec.model || "") + '">';
    }
    return '<div class="aia-modelrow"><label class="aia-label" for="aia-model-byok">' + esc(tr("secModel")) + "</label>" +
      '<select id="aia-model-byok" class="aia-input" data-aia-model="byok">' + groups.join("") + "</select>" + manual + "</div>";
  }
  function statusPanel() {
    var v = vault(), pk = picks(v), titles = {};
    var answering = routeSource(routeSync());
    var keys = keyIds(v).map(function (id) {
      var rec = v.providers[id];
      return '<li><span><span class="aia-dot ' + (rec.failed ? "is-bad" : "is-ok") + '"></span><strong>' + esc(providerLabel(id, v)) + "</strong> ••••" +
        esc((rec.key || "").slice(-4)) + " · " + esc(tr(rec.failed ? "stKeyFailed" : "stWorks")) +
        (isCustom(id) ? "<br><small>" + esc(tr("epTag")) + ": " + esc(rec.base) + "</small>" : "") +
        "<br><small>" + esc(tr(rec.session ? "storeSession" : "storeLocal")) + "</small>" +
        '</span><button type="button" class="aia-btn aia-btn-quiet" data-aia-remove="' + esc(id) + '">' + esc(tr("remove")) + "</button></li>";
    }).join("");
    titles.byok = tr("secByok");
    var byok = secHead("byok", titles.byok, answering === "byok") +
      (keys ? '<ul class="aia-list">' + keys + "</ul>" + byokModelField(v, pk) : '<p class="aia-fine aia-left">' + esc(tr("stNoKeys")) + "</p>") +
      '<p><button type="button" class="aia-btn' + (keys ? "" : " aia-btn-primary") + '" data-aia="connect">+ ' + esc(tr("tabAdd")) + "</button></p></section>";
    var project = "";
    if (projectOffered()) {
      var pr = grantActive() ? ["is-ok", tr(grantBackend() === "abo" ? "stAboActive" : "stProjActive", fmtDate(quota.grant.until))]
        : quota.grant ? ["is-bad", tr("stProjExpired", fmtDate(quota.grant.until))]
        : quota.request && quota.request.status === "offen" ? ["is-warn", tr("stProjPending")]
        : ["is-off", tr("stProjNone")];
      // Ohne Freigabe der allgemeine Titel; mit Freigabe das Backend („Projektkontingent · Gemini-Abo“ bzw. „· Nexos“).
      // Anmeldung und Modell gehören zum Kontingent und wandern mit dem Abschnitt.
      titles.project = quota.grant ? quotaLabel(grantProvider()) : tr("viaProject").replace(/^./, function (c) { return c.toUpperCase(); });
      project = secHead("project", titles.project, answering === "project") +
        '<p class="aia-left"><span class="aia-dot ' + pr[0] + '"></span>' + esc(pr[1]) + "</p>" +
        projectModelField(pk) +
        (grantActive() ? "" : '<p><button type="button" class="aia-btn" data-aia="request">' + esc(tr(
          quota.request && quota.request.status === "offen" ? "reqView" : (quota.grant || (quota.request && quota.request.status === "abgelehnt")) ? "reqAgain" : "tabQuota")) +
          "</button></p>") + signedLine() + "</section>";
    }
    var clis = (state.backend && state.backend.clis) || [];
    var remote = state.backend && state.backend.base;
    var checking = state.checking ? " disabled" : "";
    titles.local = tr("secLocal");
    var local = secHead("local", titles.local, answering === "local") +
      (clis.length ? localClis(pk) + (remote ? '<p class="aia-fine aia-left">' + esc(tr("viaLocalhost", remote.replace(/^https?:\/\//, ""))) + "</p>" : "") +
        '<p class="aia-checkrow"><button type="button" class="aia-btn aia-btn-quiet" data-aia="recheck"' + checking + ">↻ " +
        esc(tr(state.checking ? "cliChecking" : "recheck")) + "</button>" +
        (state.checkedN != null && !state.checking ? ' <span class="aia-fine" role="status">' +
          esc(state.checkedN === 1 ? tr("cliFound1") : trf("cliFoundN", { n: state.checkedN })) + "</span>" : "") + "</p>"
        : isLocalHost() ? '<p class="aia-fine aia-left">' + esc(tr("localNoServer")) + "</p>" : awayHtml()) + "</section>";
    var parts = { byok: byok, project: project, local: local };
    var shown = accessOrder().filter(function (k) { return parts[k]; });
    return '<p class="aia-fine aia-left aia-prio-hint" id="aia-prio-help">' + esc(tr("prioHint")) + "</p>" +
      shown.map(function (k, i) {
        var title = titles[k];
        return parts[k].replace("data-aia-prio-n", 'data-aia-prio-n="' + (i + 1) + '"').replace("<section class=\"aia-sec", "<section class=\"aia-sec" + (i ? "" : " aia-sec-first"))
          .replace('data-aia-grip="' + k + '"', 'data-aia-grip="' + k + '" aria-label="' + esc(trf("gripLabel", { s: title, n: (i + 1) + "/" + shown.length })) +
            '" title="' + esc(trf("gripLabel", { s: title, n: (i + 1) + "/" + shown.length })) + '"');
      }).join("") +
      (!state.user && requiresSignIn() ? signInBlock() : "");
  }
  // Man ist immer nur auf eine Weise angemeldet; zum Wechseln abmelden.
  function signedLine() {
    var via = providerName(state.user && state.user.provider);
    // Abgemeldet: Anmelden ohne Umweg über eine Anfrage (z. B. für Verwalter).
    if (!state.user && signInOffered() && state.auth !== "unconfigured") {
      return '<p class="aia-signed">' + esc(tr("stSignedOut")) + ' <button type="button" class="aia-link" data-aia="signin">' + esc(tr("signIn")) + "</button></p>";
    }
    return state.user ? '<p class="aia-signed">' + esc(via ? tr("stSignedVia", via) : tr("stAccount")) + ": <strong>" +
      esc(state.user.email || state.user.name) + '</strong> <button type="button" class="aia-link" data-aia="signout">' + esc(tr("signOut")) + "</button></p>" : "";
  }
  function byokForm() {
    var p = PROVIDERS[connectSel] || PROVIDERS.gemini;
    var hasAny = Object.keys(vault().providers).length > 0;
    // Reihenfolge: worum es geht, Schlüssel, Merken, Anbieter. Verbunden wird per Klick auf die
    // Anbieterkarte oder mit Enter im Schlüsselfeld; ein eigener Bestätigungsknopf entfällt.
    return (hasAny ? "" : '<p class="aia-lead">' + esc(tr("byokLead")) + "</p>" + '<ul class="aia-benefits">' + ["b1", "b2"].map(function (k) {
        return "<li><strong>" + esc(tr(k + "t")) + "</strong> " + esc(tr(k)) + "</li>";
      }).join("") + "</ul>") +
      '<form class="aia-key" id="aia-keyform" data-aia-form="key">' +
      '<label class="aia-label" for="aia-key">' + esc(tr("keyLabel")) + "</label>" +
      '<div class="aia-row"><input id="aia-key" type="password" name="key" required autocomplete="off" spellcheck="false" autofocus enterkeyhint="go" placeholder="' + esc(p.keyPh) + '">' +
      '<button type="button" class="aia-btn aia-btn-quiet" data-aia="reveal">' + esc(tr("show")) + "</button></div>" +
      '<div class="aia-tipwrap"><label class="aia-check" aria-describedby="aia-tip-store"><input type="checkbox" name="remember" checked> ' +
      esc(tr("remember")) + ' <span class="aia-info" aria-hidden="true">ⓘ</span></label>' +
      '<span class="aia-tip" role="tooltip" id="aia-tip-store">' + esc(tr("storeNote")) + "</span></div>" +
      providerCards() + endpointRow() +
      (keyStatus.text ? '<p class="aia-status is-' + keyStatus.kind + '" role="status">' + esc(keyStatus.text) + "</p>" : "") +
      "</form>" +
      (!state.user && requiresSignIn() ? signInBlock() : "") +
      errLine() +
      localSection();
  }
  // Alternative zu den vier Karten: ein weiterer OpenAI-kompatibler Endpunkt; Enter verbindet.
  function endpointRow() {
    return '<div class="aia-ep' + (connectSel === "custom" ? " is-sel" : "") + '"><label class="aia-label" for="aia-endpoint">' + esc(tr("epLabel")) + "</label>" +
      '<div class="aia-row"><input id="aia-endpoint" type="url" name="endpoint" inputmode="url" autocomplete="off" spellcheck="false" enterkeyhint="go"' +
      ' placeholder="https://openrouter.ai/api/v1" aria-describedby="aia-ep-hint"></div>' +
      '<p class="aia-fine aia-left" id="aia-ep-hint">' + esc(tr("epHint")) + "</p></div>";
  }
  function fmtDate(iso) {
    try { return new Date(iso).toLocaleDateString(root.document.documentElement.lang || "de"); } catch (e) { return iso || ""; }
  }
  function viewRequest() {
    var r = quota.request, body;
    if (!state.user) body = '<p class="aia-lead">' + esc(tr("reqSignIn")) + "</p>" + signInBlock(true);
    else if (grantActive()) body = '<p class="aia-status is-ok">' + esc(tr("reqGranted", fmtDate(quota.grant.until))) + "</p>";
    else if (r && r.status === "offen") body = '<p class="aia-status is-busy">' + esc(tr("reqPending", fmtDate(r.created))) + "</p>" +
      '<form class="aia-key" data-aia-form="reqedit"><label class="aia-label" for="aia-reason">' + esc(tr("reqReason")) + "</label>" +
      '<textarea id="aia-reason" name="reason" class="aia-input" rows="3" maxlength="1000" required>' + esc(r.reason || "") + "</textarea>" +
      '<div class="aia-row"><button type="submit" class="aia-btn">' + esc(tr("reqUpdate")) + "</button>" +
      '<button type="button" class="aia-btn aia-btn-quiet" data-aia="withdraw">' + esc(tr("reqWithdraw")) + "</button></div></form>";
    else body = (quota.grant && !grantActive() ? '<p class="aia-status is-error">' + esc(tr("reqExpired", fmtDate(quota.grant.until))) + "</p>" :
        r && r.status === "abgelehnt" ? '<p class="aia-status is-error">' + esc(tr("reqRejected")) + (r.note ? " " + esc(r.note) : "") + "</p>" : "") +
      '<form class="aia-key" data-aia-form="request"><label class="aia-label" for="aia-reason">' + esc(tr("reqReason")) + "</label>" +
      '<textarea id="aia-reason" name="reason" class="aia-input" rows="3" maxlength="1000" required autofocus placeholder="' +
      esc(tr("reqReasonPh")) + '"></textarea><button type="submit" class="aia-btn aia-btn-primary">' + esc(tr("reqSend")) + "</button></form>";
    return '<p class="aia-lead">' + esc(tr("reqLead")) + "</p>" + body + errLine();
  }
  function shortUid(uid) { uid = String(uid || ""); return uid.length > 10 ? uid.slice(0, 8) + "…" : uid; }
  // Eine Person eindeutig: Name, E-Mail, Anmeldeweg (falls bekannt) und UID-Kurzform; das eigene Konto mit „(du selbst)“.
  function personHtml(p) {
    var me = state.user && p.uid === state.user.uid;
    var via = providerName(p.provider || (me ? state.user.provider : ""));
    var meta = (via ? via + " · " : "") + "UID " + shortUid(p.uid);
    return '<span class="aia-person">' + (p.name ? "<strong>" + esc(p.name) + "</strong> " : "") +
      (p.email ? '<span class="aia-mail">' + esc(p.email) + "</span> " : "") +
      '<span class="aia-who" title="UID ' + esc(p.uid) + '">(' + esc(meta) + ")</span>" +
      (me ? ' <span class="aia-self">' + esc(tr("admSelf")) + "</span>" : "") + "</span>";
  }
  // Kopf der Verwaltung: als welches Konto man gerade handelt (es kann mehrere Verwalter geben).
  function actingHtml() {
    var u = state.user;
    if (!u) return "";
    var who = '<strong>' + esc(u.email || u.name || u.uid) + "</strong> (" + esc((providerName(u.provider) ? providerName(u.provider) + " · " : "") +
      "UID " + shortUid(u.uid)) + ")";
    return '<div class="aia-acting" data-aia-acting><p>' + esc(tr("admActing", "\u0000")).replace("\u0000", who) + "</p>" +
      '<p class="aia-fine aia-left">' + esc(tr("admActingHint")) + "</p></div>";
  }
  // Modellauswahl je Backend; leer = alle Modelle dieses Backends.
  function adminModelOptions(backend, current) {
    var ids = backend === "abo" ? aboModels() : ((quota.adminModels && quota.adminModels.nexos) || []);
    if (current && ids.indexOf(current) === -1) ids = [current].concat(ids);
    return '<option value="">' + esc(tr(backend === "abo" ? "admModelAllAbo" : "admModelAllNexos")) + "</option>" +
      ids.map(function (m) { return '<option value="' + esc(m) + '"' + (m === current ? " selected" : "") + ">" + esc(m) + "</option>"; }).join("");
  }
  // Backend der Freigabe: Nexos für alle; das Gemini-Abo nur für die Konten in abo_uids (sonst ausgegraut).
  function backendFields(uid) {
    var own = aboAllowed(uid);
    return '<div class="aia-row"><label class="aia-field"><span class="aia-label">' + esc(tr("admBackend")) + "</span>" +
      '<select class="aia-input" name="backend" data-aia-backend>' +
      '<option value="nexos" selected>' + esc(tr("admBackendNexos")) + "</option>" +
      '<option value="abo"' + (own ? "" : " disabled") + ">" + esc(tr(own ? "admBackendAbo" : "admBackendAboOff")) + "</option></select></label>" +
      '<label class="aia-field"><span class="aia-label">' + esc(tr("admModelSel")) + "</span>" +
      '<select class="aia-input" name="model" data-aia-models>' + adminModelOptions("nexos", "") + "</select></label></div>" +
      (own ? '<p class="aia-fine aia-left" data-aia-abo-hint hidden>' + esc(tr("admAboHint")) + "</p>" : "");
  }
  function viewAdmin() {
    var open = quota.open.map(function (r) {
      var mine = state.user && r._id === state.user.uid;
      return '<li class="aia-req' + (mine ? " is-self" : "") + '" data-aia-req="' + esc(r._id) + '"><div><span class="aia-label">' + esc(tr("admReqBy")) + "</span> " +
        personHtml({ uid: r._id, name: r.name, email: r.email, provider: r.provider }) + " <span>· " + esc(fmtDate(r.created)) +
        "</span></div><p>" + esc(r.reason) + "</p>" +
        '<form class="aia-key" data-aia-form="decide" data-uid="' + esc(r._id) + '">' +
        '<label class="aia-label">' + esc(tr("admDuration")) + '</label><select class="aia-input" name="days">' +
        [["1", "admD1"], ["7", "admD7"], ["30", "admD30"], ["90", "admD90"]].map(function (d) {
          return '<option value="' + d[0] + '"' + (d[0] === "7" ? " selected" : "") + ">" + esc(tr(d[1])) + "</option>";
        }).join("") + "</select>" +
        backendFields(r._id) +
        '<div class="aia-row"><input class="aia-input" name="note" placeholder="' + esc(tr("admNote")) + '"></div>' +
        '<div class="aia-row"><button type="submit" class="aia-btn aia-btn-primary" data-decide="grant">' + esc(tr("admGrant")) +
        '</button><button type="submit" class="aia-btn" data-decide="reject">' + esc(tr("admReject")) + "</button></div></form></li>";
    }).join("");
    var grants = quota.grants.map(function (g) {
      var who = (quota.people && quota.people[g._id]) || { uid: g._id };
      var live = g.until && Date.parse(g.until) > Date.now();
      var by = !g.granted_by ? "" : state.user && g.granted_by === state.user.uid ? tr("admGrantedBySelf") : tr("admGrantedBy", "UID " + shortUid(g.granted_by));
      return '<li class="' + (live ? "" : "is-expired") + '" data-aia-grant="' + esc(g._id) + '"><span>' + personHtml(who) + "<br><small>" +
        esc(tr(live ? "admUntil" : "admExpired", fmtDate(g.until))) + " · " + esc(grantBackend(g) === "abo" ? tr("admBackendAbo") : "Nexos") +
        " · " + esc(g.model || tr("admModelAll")) +
        (by ? " · " + esc(by) : "") + "</small>" +
        '</span><button type="button" class="aia-btn aia-btn-quiet" data-aia-revoke="' + esc(g._id) + '">' + esc(tr("admRevoke")) + "</button></li>";
    }).join("");
    var fbRow = fbConfigured() ? '<p class="aia-fb-entry"><button type="button" class="aia-btn" data-aia="fbadmin">' + esc(tr("fbAdmBtn")) +
      (fbNewCount() ? ' <span class="aia-badge">' + esc(tr("fbAdmNew", String(fbNewCount()))) + "</span>" : "") + "</button></p>" : "";
    return actingHtml() + fbRow + '<h3 class="aia-h3">' + esc(tr("admTitle")) + "</h3>" +
      (open ? '<ul class="aia-list aia-reqs">' + open + "</ul>" : '<p class="aia-lead">' + esc(tr("admNone")) + "</p>") +
      (grants ? '<section class="aia-sec"><h3>' + esc(tr("admGrants")) + '</h3><ul class="aia-list">' + grants + "</ul>" +
        '<p class="aia-fine">' + esc(tr("admRevokeHint")) + "</p></section>" : "") + billingForm() + errLine();
  }
  function fbDate(iso) {
    try { return new Date(iso).toLocaleString(root.document.documentElement.lang || "de", { dateStyle: "short", timeStyle: "short" }); } catch (e) { return iso || ""; }
  }
  function fbCtxHtml(c) {
    c = c || {};
    var bits = [];
    if (c.title || c.page) bits.push(c.page ? '<a href="' + esc(c.page) + '" target="_blank" rel="noopener">' + esc(c.title || c.page) + "</a>" : esc(c.title));
    if (c.fold) bits.push(esc(c.fold));
    if (c.target) bits.push("<code>" + esc(c.target) + "</code>");
    if (c.release) bits.push(esc(c.release));
    if (c.lang) bits.push(esc(String(c.lang).toUpperCase()));
    var sel = c.selection ? '<br><span class="aia-fb-sel">„' + esc(c.selection) + "“</span>" : "";
    return bits.length || sel ? '<p class="aia-fb-ctx">' + bits.join(" · ") + sel + "</p>" : "";
  }
  function viewFeedbackAdmin() {
    var all = fbAdm.filter === "all";
    var items = fbAdm.items.filter(function (x) { return all || x.status === "neu" || x.status === "in_pruefung"; });
    var list = items.map(function (x) {
      var who = x.auth === "konto" ? tr("fbKonto") + (x.name ? " " + x.name : "") : tr("fbAnon");
      var opts = FB_STATUSES.map(function (s) {
        return '<option value="' + s + '"' + (s === x.status ? " selected" : "") + ">" + esc(tr("fbSt_" + s)) + "</option>";
      }).join("");
      return '<li class="aia-fb is-' + esc(x.status || "neu") + '" data-aia-fb="' + esc(x._id) + '">' +
        '<div class="aia-fb-head"><span class="aia-fb-art is-' + esc(x.art) + '">' + esc(tr("fbArt_" + (x.art || "hinweis"))) + "</span>" +
        '<span class="aia-fb-st">' + esc(tr("fbSt_" + (x.status || "neu"))) + "</span>" +
        '<span class="aia-fine">' + esc(fbDate(x.created)) + " · " + esc(who) + ' · <span title="UID ' + esc(x.uid) + '">UID ' + esc(shortUid(x.uid)) + "</span></span></div>" +
        '<p class="aia-fb-text">' + esc(x.text) + "</p>" + fbCtxHtml(x.ctx) +
        (x.contact ? '<p class="aia-fine aia-left">' + esc(tr("fbAdmContact")) + ": <strong>" + esc(x.contact) + "</strong></p>" : "") +
        (x.finding ? '<p class="aia-fine aia-left">' + esc(tr("fbAdmFinding")) + ": <code>" + esc(x.finding) + "</code></p>" : "") +
        '<form class="aia-key aia-fb-form" data-aia-form="fbtriage" data-id="' + esc(x._id) + '"><div class="aia-row">' +
        '<label class="aia-field"><span class="aia-label">' + esc(tr("fbAdmStatus")) + '</span><select class="aia-input" name="status">' + opts + "</select></label>" +
        '<label class="aia-field aia-fb-note"><span class="aia-label">' + esc(tr("fbAdmNote")) + '</span><input class="aia-input" name="note" maxlength="1000" value="' + esc(x.note || "") + '"></label></div>' +
        '<div class="aia-row"><button type="submit" class="aia-btn aia-btn-primary">' + esc(tr("admSave")) + "</button>" +
        '<button type="button" class="aia-btn aia-btn-quiet" data-aia-fbdel="' + esc(x._id) + '">' + esc(tr("fbAdmDel")) + "</button></div></form></li>";
    }).join("");
    var sw = fbAdm.settings || { offen: true, anonym: true };
    var openCount = fbAdm.items.filter(function (x) { return x.status === "neu" || x.status === "in_pruefung"; }).length;
    return actingHtml() + '<p class="aia-lead">' + esc(tr("fbAdmLead")) + "</p>" +
      '<div class="aia-tabs aia-fb-filter" role="group"><button type="button" class="aia-tab' + (all ? "" : " is-on") + '" data-aia-fbfilter="open" aria-pressed="' + !all + '">' +
      esc(tr("fbAdmShowOpen")) + " (" + openCount + ')</button><button type="button" class="aia-tab' + (all ? " is-on" : "") + '" data-aia-fbfilter="all" aria-pressed="' + all + '">' +
      esc(tr("fbAdmShowAll")) + " (" + fbAdm.items.length + ")</button></div>" +
      (!fbAdm.loaded ? '<p class="aia-fine aia-left">' + esc(tr("checking")) + "</p>" :
        list ? '<ul class="aia-list aia-fbs">' + list + "</ul>" : '<p class="aia-lead">' + esc(tr("fbAdmNone")) + "</p>") +
      '<section class="aia-sec"><form class="aia-key" data-aia-form="fbswitch"><h3>' + esc(tr("fbAdmSwitch")) + "</h3>" +
      '<label class="aia-check"><input type="checkbox" name="offen"' + (sw.offen ? " checked" : "") + "><span>" + esc(tr("fbAdmOpen")) + "</span></label>" +
      '<label class="aia-check"><input type="checkbox" name="anonym"' + (sw.anonym ? " checked" : "") + "><span>" + esc(tr("fbAdmAnon")) + "</span></label>" +
      '<div class="aia-row"><button type="submit" class="aia-btn">' + esc(tr("admSave")) + "</button></div>" +
      '<p class="aia-fine aia-left">' + esc(tr("fbAdmSwitchHint")) + "</p></form></section>" + errLine();
  }
  // Fokus über das Neuzeichnen retten: Eingaben über id/name, Griffe, Ausweichfelder und CLI-Auswahl über ihre Daten.
  function focusKey(x) {
    if (!x || !x.getAttribute) return null;
    var g = x.getAttribute("data-aia-grip"), fb = x.getAttribute("data-aia-fb"), n = x.getAttribute("name");
    if (g) return '[data-aia-grip="' + g + '"]';
    if (fb != null) return '[data-aia-fb="' + fb + '"]';
    if (x.hasAttribute("data-aia-cli")) return 'input[data-aia-cli][value="' + String(x.value).replace(/["\\]/g, "") + '"]';
    if (x.id && /^[\w-]+$/.test(x.id)) return "#" + x.id;
    return n ? '[name="' + n + '"]' : null;
  }
  function paint(el, html, cls) {
    var activeKey = document.activeElement && el.contains(document.activeElement) ? focusKey(document.activeElement) : null;
    var kept = {};
    el.querySelectorAll("input[name]").forEach(function (x) { if (x.type !== "checkbox" && x.value) kept[x.name] = x.value; });
    var keptCheck = el.querySelector('input[name="remember"]');
    keptCheck = keptCheck ? keptCheck.checked : null;
    el.innerHTML = '<div class="aia-body ' + (cls || "") + '">' + html + "</div>";
    Object.keys(kept).forEach(function (n) { var x = el.querySelector('input[name="' + n + '"]'); if (x && !x.value) x.value = kept[n]; });
    var rc = el.querySelector('input[name="remember"]');
    if (rc && keptCheck !== null) rc.checked = keptCheck;
    if (activeKey) { var f = el.querySelector(activeKey); if (f) try { f.focus({ preventScroll: true }); } catch (e) { f.focus(); } }
  }
  function renderDialog() {
    if (!dlg) return;
    var v = state.view;
    if (["sent", "confirm", "account", "connect", "request", "admin", "signin", "fbadmin"].indexOf(v) === -1) v = state.view = "account";
    if (v === "signin" && state.user) v = state.view = "account";
    if ((v === "admin" || v === "fbadmin") && !quota.admin) v = state.view = "account";
    if (v === "request" && !projectOffered()) v = state.view = "account";
    // Die Anmeldung steht im Abschnitt Projektkontingent (nur dafür wird sie gebraucht); ohne diesen Abschnitt
    // (z. B. Verwalter ohne Projektdienst) unten wie bisher.
    paint(dlg, closeBtn() + '<h2 id="aia-title" class="aia-dtitle"><span class="aia-mark">' + SPARK + "</span>" + esc(tr("dlgTitle")) + "</h2>" +
      statusPanel() + errLine() + (projectOffered() ? "" : signedLine()), "is-main");
    if (liveEl && dlg.open) dlg.appendChild(liveEl);
    if (v === "account") {
      if (sub && sub.open) sub.close();
    } else {
      var title = { connect: tr("tabAdd"), request: tr("tabQuota"), admin: tr("admBtn"), signin: tr("signIn"), fbadmin: tr("fbAdmTitle") }[v];
      var body = v === "sent" ? viewSent() : v === "confirm" ? viewConfirm() : v === "connect" ? byokForm() :
        v === "request" ? viewRequest() : v === "signin" ? signInBlock(true) : v === "fbadmin" ? viewFeedbackAdmin() : viewAdmin();
      paint(sub, (title ? (dlg.open ? '<button type="button" class="aia-back" data-aia="account">← ' + esc(tr("back")) + "</button>" : "") + closeBtn() +
        '<h2 id="aia-subtitle" class="aia-dtitle">' + esc(title) + "</h2>" + body + (body.indexOf('class="aia-error"') === -1 ? errLine() : "") : body), "is-sub");
      if (!sub.open) { try { sub.showModal(); } catch (e) { sub.setAttribute("open", ""); } }
    }
    var host = sub && sub.open ? sub : dlg;
    if (toastEl && toastEl.classList.contains("is-on") && toastEl.parentNode !== host) host.appendChild(toastEl);
  }
  // Ohne Schlüssel: Anbieter merken, ins Schlüsselfeld springen und kurz erklären, wie es weitergeht.
  function askForKey(form, label) {
    keyStatus = { text: tr("keyFirst", label), kind: "hint" };
    renderDialog();
    var inp = (sub && sub.querySelector("#aia-key")) || (form && form.key);
    if (inp) try { inp.focus(); } catch (e) { /* ignore */ }
  }
  function keyForm(from) {
    return (from && from.querySelector && from.querySelector("#aia-keyform")) || (sub && sub.querySelector("#aia-keyform"));
  }
  function connected(form, text) {
    // Schlüssel nicht im (nur geschlossenen) Popup stehen lassen: der nächste Kartenklick würde ihn sonst erneut verwenden.
    if (form) Array.prototype.forEach.call(form.querySelectorAll('input[name="key"],input[name="endpoint"]'), function (x) { x.value = ""; });
    keyStatus = { text: "", kind: "" };
    state.view = "account";
    renderDialog();
    toast(text);
  }
  async function connectKey(form, id) {
    id = id || connectSel;
    if (!form || keyStatus.kind === "busy") return;
    var key = form.key.value.trim();
    var remember = form.remember.checked;
    if (!key) { askForKey(form, PROVIDERS[id].label); return; }
    keyStatus = { text: tr("checking"), kind: "busy" };
    renderDialog();
    var models = [], listed = true;
    try {
      models = await PROVIDERS[id].list(key);
    } catch (e) {
      if (e && (e.status === 401 || e.status === 403 || e.status === 400)) {
        keyStatus = { text: tr("keyBad") + " (" + e.message + ")", kind: "error" };
        renderDialog();
        return;
      }
      if (id !== "nexos" || !(e && e.status === 404)) {
        keyStatus = { text: tr("keyNet") + " (" + ((e && e.message) || e) + ")", kind: "error" };
        renderDialog();
        return;
      }
      listed = false;
    }
    var model = listed ? PROVIDERS[id].pick(models) : "";
    saveProvider(id, { key: key, models: models, model: model, checkedAt: new Date().toISOString() }, remember);
    setChoice({ provider: id, model: model });
    connected(form, listed ? tr("keyOk", String(models.length)) : tr("keyNoList"));
  }
  async function connectEndpoint(form) {
    if (!form || keyStatus.kind === "busy") return;
    connectSel = "custom";
    var ep = normalizeEndpoint(form.endpoint.value);
    if (!ep) {
      keyStatus = { text: tr("epBad"), kind: "error" };
      renderDialog();
      var inp = sub && sub.querySelector("#aia-endpoint");
      if (inp) try { inp.focus(); } catch (e) { /* ignore */ }
      return;
    }
    var key = form.key.value.trim();
    if (!key) { askForKey(form, ep.label); return; }
    var remember = form.remember.checked;
    var id = CUSTOM + ep.host;
    keyStatus = { text: tr("checking"), kind: "busy" };
    renderDialog();
    var models;
    try {
      models = await openAiCompatible(ep.base, customFilter).list(key);
    } catch (e) {
      var st = e && e.status;
      var text = st === 401 || st === 403 || st === 400 ? tr("keyBad") + " (" + e.message + ")"
        : e && e.notJson ? tr("epNoJson", ep.label)
        : st === 404 ? "HTTP 404 – " + tr("epNoJson", ep.label)
        // Ohne HTTP-Status: Netzfehler oder vom Browser blockiert (CORS) – der Browser verrät nicht, was davon.
        : !st ? tr("epCors", ep.label)
        : tr("keyNet") + " (" + ((e && e.message) || e) + ")";
      keyStatus = { text: text, kind: "error" };
      renderDialog();
      return;
    }
    var model = customProvider({ base: ep.base, label: ep.label }, id).pick(models);
    saveProvider(id, { key: key, models: models, model: model, base: ep.base, label: ep.label,
                       checkedAt: new Date().toISOString() }, remember);
    setChoice({ provider: id, model: model });
    connected(form, models.length ? tr("keyOk", String(models.length)) : tr("keyNoList"));
  }
  function onDialogClick(e) {
    if (e.target.closest("a, .aia-info, .aia-tip")) return;
    var rv = e.target.closest("[data-aia-revoke]");
    if (rv) { revoke(rv.getAttribute("data-aia-revoke")).catch(fail); return; }
    var fd = e.target.closest("[data-aia-fbdel]");
    if (fd) { fbAdminDelete(fd.getAttribute("data-aia-fbdel")).catch(fail); return; }
    var ff = e.target.closest("[data-aia-fbfilter]");
    if (ff) { fbAdm.filter = ff.getAttribute("data-aia-fbfilter"); renderDialog(); return; }
    var t = e.target.closest("[data-aia],[data-aia-prov],[data-aia-remove],[data-aia-local],[data-aia-card]");
    if (!t) return;
    if (t.hasAttribute("data-aia-card")) t = t.querySelector("[data-aia-prov]");
    var a = t.getAttribute("data-aia");
    if (a === "close") { if (e.currentTarget === sub) { state.view = "account"; renderDialog(); } else dlg.close(); }
    else if (a === "google") signInGoogle();
    else if (a === "probe") probeLocal();
    else if (a === "recheck") recheckLocal();
    else if (a === "github") signInWith("GithubAuthProvider");
    else if (a === "apple") signInWith("OAuthProvider", "apple.com");
    else if (a === "request") { state.view = "request"; renderDialog(); ensureFirebase(); }
    else if (a === "withdraw") withdrawRequest().catch(fail);
    else if (a === "signin") { state.afterSignIn = "account"; state.view = "signin"; renderDialog(); ensureFirebase(); }
    else if (a === "admin") { state.view = "admin"; renderDialog(); loadAdmin().then(emit).catch(fail); }
    else if (a === "fbadmin") { state.view = "fbadmin"; renderDialog(); loadFeedbackAdmin().then(emit).catch(fail); }
    else if (a === "skip") { state.view = Object.keys(vault().providers).length ? "account" : "connect"; renderDialog(); }
    else if (a === "resend") sendLink(state.pendingEmail).then(function (ok) { if (ok) toast(tr("resent")); });
    else if (a === "restart") { state.view = "connect"; renderDialog(); ensureFirebase(); }
    else if (a === "signout") signOut();
    else if (a === "connect") { keyStatus = { text: "", kind: "" }; state.view = "connect"; renderDialog(); }
    else if (a === "account") { state.view = "account"; renderDialog(); }
    else if (a === "reveal") {
      var inp = e.currentTarget.querySelector("#aia-key");
      inp.type = inp.type === "password" ? "text" : "password";
      t.textContent = inp.type === "password" ? tr("show") : tr("hide");
    } else if (t.hasAttribute("data-aia-prov")) {
      if (keyStatus.kind === "busy") return; // eine Prüfung läuft schon
      connectSel = t.getAttribute("data-aia-prov");
      keyStatus = { text: "", kind: "" };
      connectKey(keyForm(e.currentTarget), connectSel);
    } else if (t.hasAttribute("data-aia-remove")) removeProvider(t.getAttribute("data-aia-remove"));
    else if (t.hasAttribute("data-aia-local")) setChoice({ provider: "local", model: t.getAttribute("data-aia-local") });
  }
  // „Prüfen“: der Dienst sucht und prüft alle bekannten CLIs (PATH, --version, Anmeldung; kein Modellaufruf) und
  // antwortet mit dem neuen Stand. Kommt keine Antwort (z. B. CORS von der öffentlichen Seite), Status neu laden.
  function recheckLocal() {
    if (state.checking) return;
    state.checking = true;
    state.checkedN = null;
    emit();
    var remote = state.backend && state.backend.base;
    fetch(localUrl("/api/ai/check"), { method: "POST", cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (j) {
        if (j && j.providers) { state.backend = localState(j, remote || ""); backendPromise = Promise.resolve(state.backend); return null; }
        if (remote) return probeLocal(true);
        backendPromise = null;
        return backendStatus();
      })
      .then(function () {
        state.checking = false;
        state.checkedN = ((state.backend && state.backend.clis) || []).length;
        emit();
      });
  }
  function onDialogSubmit(e) {
    var f = e.target.closest ? e.target.closest("[data-aia-form]") : null;
    if (!f) return;
    e.preventDefault();
    var k = f.getAttribute("data-aia-form");
    if (k === "mail") sendLink(f.email.value);
    else if (k === "paste") completeLink(f.link.value.trim());
    else if (k === "confirm") completeLink(state.pendingLink || root.location.href, f.email.value.trim());
    else if (k === "key") { if (connectSel === "custom") connectEndpoint(f); else connectKey(f, connectSel); }
    else if (k === "request") sendRequest(f.reason.value.trim()).catch(fail);
    else if (k === "reqedit") updateRequest(f.reason.value.trim()).catch(fail);
    else if (k === "settings") saveSettings(f).catch(fail);
    else if (k === "fbtriage") fbTriage(f.getAttribute("data-id"), f).catch(fail);
    else if (k === "fbswitch") fbSaveSwitch(f).catch(fail);
    else if (k === "decide") {
      var which = e.submitter && e.submitter.getAttribute("data-decide");
      decide(f.getAttribute("data-uid"), which !== "reject", f).catch(fail);
    }
  }
  // Anbieter am Präfix des eingefügten Schlüssels erkennen.
  function providerOfKey(key) {
    if (/^AIza/.test(key)) return "gemini";
    if (/^sk-or-/.test(key)) return "";
    if (/^sk-ant-/.test(key)) return "anthropic";
    if (/^sk-/.test(key)) return "openai";
    return "";
  }
  function onDialogInput(e) {
    // Eine Fehlermeldung zum vorigen Versuch verschwindet, sobald Schlüssel oder Adresse geändert werden.
    if ((e.target.id === "aia-endpoint" || e.target.id === "aia-key") && keyStatus.kind === "error") {
      keyStatus = { text: "", kind: "" };
      var st = e.currentTarget.querySelector(".aia-status.is-error");
      if (st) st.remove();
    }
    if (e.target.id === "aia-endpoint") {
      // Ohne neues Zeichnen (Cursor bleibt stehen): Endpunkt als Ziel markieren, Karten abwählen.
      var on = !!e.target.value.trim();
      if (on) connectSel = "custom";
      else if (connectSel === "custom") connectSel = providerOfKey(((keyForm(e.currentTarget) || {}).key || {}).value || "") || "gemini";
      var d = e.currentTarget;
      var ep = d.querySelector(".aia-ep");
      if (ep) ep.classList.toggle("is-sel", connectSel === "custom");
      d.querySelectorAll("[data-aia-card]").forEach(function (c) {
        var sel = c.getAttribute("data-aia-card") === connectSel;
        c.classList.toggle("is-sel", sel);
        var b = c.querySelector("[data-aia-prov]");
        if (b) b.setAttribute("aria-pressed", String(sel));
      });
      return;
    }
    if (e.target.id !== "aia-key") return;
    if (connectSel === "custom") return;
    var id = providerOfKey(e.target.value.trim());
    if (id && id !== connectSel) { connectSel = id; keyStatus = { text: "", kind: "" }; renderDialog(); }
  }
  function onDialogKeydown(e) {
    if (e.key !== "Enter" || e.isComposing || e.shiftKey || e.altKey || e.ctrlKey || e.metaKey) return;
    var form = keyForm(e.currentTarget);
    if (e.target.id === "aia-endpoint") { e.preventDefault(); connectEndpoint(form); return; }
    if (e.target.id !== "aia-key") return;
    e.preventDefault();
    if (connectSel === "custom" && form && form.endpoint && form.endpoint.value.trim()) connectEndpoint(form);
    else connectKey(form, connectSel === "custom" ? providerOfKey(e.target.value.trim()) || "gemini" : connectSel);
  }
  function onDialogChange(e) {
    if (e.target.matches("[data-aia-backend]")) {
      var form = e.target.closest("form");
      var sel = form && form.querySelector("[data-aia-models]");
      if (sel) sel.innerHTML = adminModelOptions(e.target.value, "");
      var hint = form && form.querySelector("[data-aia-abo-hint]");
      if (hint) hint.hidden = e.target.value !== "abo";
      return;
    }
    if (e.target.matches("[data-aia-model]")) {
      var parts = e.target.value.split("|");
      setChoice({ provider: parts[0], model: parts.slice(1).join("|") });
    } else if (e.target.matches("[data-aia-cli]")) {
      setChoice({ provider: "local", model: e.target.value });
    } else if (e.target.matches("[data-aia-fb]")) {
      // Ausweichliste: Feld i setzt den i-ten Eintrag; leer kürzt die Liste ab hier.
      var i = Number(e.target.getAttribute("data-aia-fb")), cur = localChain(picks());
      var fb = cur.fallback.slice(0, i);
      if (e.target.value) fb.push(e.target.value);
      fb = fb.concat(cur.fallback.slice(i + 1).filter(function (x) { return e.target.value && fb.indexOf(x) === -1; }));
      setPick("local", { cli: cur.cli, fallback: fb });
    } else if (e.target.matches("[data-aia-manual]")) {
      var id = e.target.getAttribute("data-aia-manual");
      var v = vault();
      var rec = v.providers[id];
      if (rec) {
        rec.model = e.target.value.trim();
        saveProvider(id, rec, !rec.session);
        setChoice({ provider: id, model: rec.model });
      }
    }
  }

  // Modell-Chip und Hinweis-Karte für die Diskussionsfenster
  function chip() {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "aia-chip";
    b.setAttribute("data-aia-chip", "");
    b.addEventListener("click", function () { openDialog(); });
    updateChip(b);
    return b;
  }
  function updateChip(b) {
    route().then(function (r) {
      b.classList.toggle("is-ready", r.kind !== "none");
      b.innerHTML = SPARK + "<span>" + esc(routeLabel(r)) + "</span>";
    });
  }
  function gate(reason) {
    var box = document.createElement("div");
    box.className = "aia-gate";
    var btn = reason === "setup" ? "" :
      '<button type="button" class="aia-btn aia-btn-primary" data-aia-gate>' + esc(tr(reason === "key" ? "gateBtnKey" : "gateBtnSignIn")) + "</button>";
    box.innerHTML = '<div class="aia-mark">' + SPARK + "</div><p>" +
      esc(tr(reason === "setup" ? "gateSetup" : reason === "key" ? "gateKey" : "gateSignIn")) + "</p>" + btn;
    var bt = box.querySelector("[data-aia-gate]");
    if (bt) bt.addEventListener("click", function () { openDialog(reason === "key" ? "connect" : undefined); });
    return box;
  }

  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!root.document || !msg) return;
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "aia-toast";
      toastEl.setAttribute("role", "status");
    }
    // Ein offener Dialog liegt in der obersten Ebene; dort muss auch die Meldung hin.
    var host = sub && sub.open ? sub : dlg && dlg.open ? dlg : document.body;
    if (toastEl.parentNode !== host) host.appendChild(toastEl);
    toastEl.textContent = msg;
    toastEl.classList.add("is-on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("is-on"); }, 4200);
  }

  var inited = false;
  function init() {
    if (inited || !root.document) return;
    inited = true;
    mountHeader();
    guardDiscussClicks();
    // Wartet eine Anfrage, beim Zurückkehren auf die Seite nachsehen, ob sie inzwischen entschieden ist.
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible" && state.user && quota.request && quota.request.status === "offen") syncQuota();
    });
    document.querySelectorAll("[data-aia-slot]").forEach(function (slot) {
      if (!slot.querySelector("[data-aia-chip]")) slot.appendChild(chip());
    });
    loadConfig().then(function () {
      backendStatus();
      // Einmal gefundener lokaler Dienst: auch auf der öffentlichen Seite still wieder prüfen.
      if (!isLocalHost() && sget("local", LOCAL_OK)) probeLocal(true);
      var href = root.location.href;
      if (state.auth !== "unconfigured" && (sget("local", SESSION_FLAG) || linkInUrl(href))) {
        ensureFirebase().then(function () {
          if (linkInUrl(href)) completeLink(href).then(function (ok) {
            if (ok) { toast(tr("signedIn", state.user && state.user.email)); openDialog(); }
          });
        });
      }
      renderHeader();
    });
  }

  return {
    init: init, route: route, localUrl: localUrl, answerLabel: answerLabel, routeLabel: routeLabel, discuss: discuss, open: openDialog, chip: chip, gate: gate,
    models: models, complete: complete, text: tr, fallbackText: fallbackText,
    // Leser-Feedback (review_request.js: Dialog, review.js: „Meine Meldungen“, Verwaltung: Sichtung)
    feedback: { channel: fbChannel, send: fbSend, mine: fbMine, withdraw: fbWithdraw, openAdmin: openFeedbackAdmin,
                isAdmin: function () { return !!quota.admin && fbConfigured(); }, newCount: fbNewCount, normalize: fbNormalize,
                signIn: function () { state.afterSignIn = "account"; openDialog("signin"); } },
    proposalIssue: proposalIssue, openIssue: openIssue, toast: toast, snapshot: snapshot, idToken: idToken,
    // für Tests
    _buildDiscussPrompt: buildDiscussPrompt, _extractFinding: extractFinding, _redact: redact,
    _providers: PROVIDERS, _pickDefault: pickDefault, _state: state, _accessOrder: accessOrder, _routeSync: routeSync,
    _normalizeEndpoint: normalizeEndpoint, _provOf: provOf, _keyIds: keyIds, _viewAdmin: viewAdmin, _quota: function () { return quota; },
    _statusPanel: statusPanel, _decide: decide, _aboModels: aboModels, _setChoice: setChoice,
    _picks: picks, _setPick: setPick, _localChain: localChain, _localState: localState, _promoteSource: promoteSource,
    _accessIcons: accessIcons,
    _viewFeedbackAdmin: viewFeedbackAdmin, _fbAdm: function () { return fbAdm; }
  };
});
