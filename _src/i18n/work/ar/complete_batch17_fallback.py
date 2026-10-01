import json,re
from pathlib import Path
B=Path('/home/user/workspace/ara-api-doku/_src/i18n/work/ar')
src=[json.loads(x) for x in (B/'batch_17.jsonl').read_text().splitlines()]
old=[json.loads(x) for x in (B/'batch_17.out.jsonl').read_text().splitlines()]
assert len(old)==280 and [x['id'] for x in old]==[x['id'] for x in src[:280]]

# Exact Arabic captions for the remaining non-identifier labels.
M={
'SamplePtr bei Anwendung':'SamplePtr لدى التطبيق','SamplePtr mit ProfileCheckStatus':'SamplePtr مع ProfileCheckStatus','Schlüssel konfiguriert':'المفتاح مهيأ',
'Schreiben und\\nKapazität möglich?':'هل الكتابة و\\nالسعة ممكنتان؟','Schwellwert erfüllt?':'هل تحققت قيمة العتبة؟','Security Event melden':'الإبلاغ عن Security Event',
'Sensor / Anwendung':'المستشعر / التطبيق','Service nicht verfügbar':'Service غير متاح','Session anfordern':'طلب Session','Session beenden':'إنهاء Session','Session wechseln':'تبديل Session',
'Sicherer Zugriff auf einen optionalen Wert':'وصول آمن إلى قيمة اختيارية','SovdProximityChallenge führt Challenge-Verfahren aus':'ينفّذ SovdProximityChallenge إجراء Challenge',
'SovdProximityChallenge\\nführt Challenge-Verfahren aus':'ينفّذ SovdProximityChallenge\\nإجراء Challenge','Startbedingung erfüllt':'شرط البدء مستوفى',
'State Management koordiniert Recovery':'ينسّق State Management عملية Recovery','Status aktualisiert':'تم تحديث الحالة','Status auslesen':'قراءة الحالة','Status-/Snapshotänderung':'تغيّر الحالة / Snapshot',
'Storage öffnen':'فتح Storage','Streaming aktiv':'Streaming نشط','Subfunktion?':'وظيفة فرعية؟','Subscription etabliert':'تم إنشاء Subscription',
'Synchronisations- und Leap-Status':'حالة المزامنة وLeap','Synchronisationsstatus einer Consumer-Zeitbasis':'حالة مزامنة قاعدة الزمن لـ Consumer',
'Time Base aktualisieren':'تحديث Time Base','Toleranz überschritten':'تم تجاوز التفاوت','Transaktionsgrenze eines Key-Value Storage':'حد المعاملة لـ Key-Value Storage',
'TransferData (Blöcke)':'TransferData (كتل)','Transport-/Profilfehler behandeln':'معالجة أخطاء النقل / الملف الشخصي',
'Trigger-Kollaboration einer StateMachine':'تعاون Trigger في StateMachine','Unsubscribe oder Proxy-Zerstörung\\nmit gehaltenem Sample':'Unsubscribe أو إتلاف Proxy\\nمع Sample محتفظ به',
'Update erfolgreich\\nmit Gateway':'نجح Update\\nمع Gateway','Update erfolgreich\\nohne Gateway':'نجح Update\\nدون Gateway','Update über Gateway':'Update عبر Gateway',
'Update() vor Start()':'Update() قبل Start()','Update()\\n(0..n-mal)':'Update()\\n(من 0 إلى n مرة)','UpdateRequest als kontrollierte Zustandsfolge':'UpdateRequest كتسلسل حالات مضبوط',
'Verarbeitungsmodus':'نمط المعالجة','Verarbeitungswahl für Skeleton-Methoden':'اختيار المعالجة لأساليب Skeleton','Vereinfachter NM-Netzzustand':'حالة شبكة NM مبسطة',
'Verifikation erfolgreich?':'هل نجحت عملية التحقق؟','Vom Modellnamen zum technischen Dienstbezug':'من اسم النموذج إلى مرجع الخدمة التقني',
'Von Execution Management nachverfolgter Prozess-Lifecycle':'دورة حياة العملية التي يتتبعها Execution Management','Vorbedingung verletzt':'انتهاك الشرط المسبق','Wartezeit abgelaufen':'انتهت مهلة الانتظار',
'Watchdog-Pfad':'مسار Watchdog','Weiterleitung':'إعادة التوجيه','Wert lesen / Änderungen\\npersistieren':'قراءة القيمة / حفظ\\nالتغييرات','Wiederherstellung erforderlich':'الاستعادة مطلوبة',
'X.509-Speicher und Prüfkontext':'مخزن X.509 وسياق التحقق','Zertifikat/-gruppe\\npersistent':'الشهادة / المجموعة\\nدائمة',
'Zertifikate → ara::core — Container & Views: 20 Referenzstellen':'الشهادات → ara::core — Container & Views: 20 مواضع مرجعية',
'Zertifikate → ara::core::InstanceSpecifier: 9 Referenzstellen':'الشهادات → ara::core::InstanceSpecifier: 9 مواضع مرجعية',
'Zertifikate → ara::core::Result: 62 Referenzstellen':'الشهادات → ara::core::Result: 62 مواضع مرجعية',
'Zertifikate → namespace ara::core: 4 Referenzstellen':'الشهادات → namespace ara::core: 4 مواضع مرجعية','Zertifikate\\nara::crypto::x509':'الشهادات\\nara::crypto::x509',
'Ziel-StateMachine-State\\nund ActionList':'حالة StateMachine المستهدفة\\nوActionList','Ziel-StateMachine-State\\\\nund ActionList':'حالة StateMachine المستهدفة\\\\nوActionList',
'Zusammenspiel bei einer Task-Einreichung':'التفاعل عند إرسال Task','Zusammenspiel im Crypto Stack':'التفاعل في Crypto Stack','Zustandsmodell einer IP-basierten Stream-Verbindung':'نموذج الحالة لاتصال Stream قائم على IP',
'Zyklus aktiv':'الدورة نشطة','Zyklus endet /\\nrestartet':'تنتهي الدورة /\\nتُعاد بدؤها','Zykluswechsel':'تغيّر الدورة','[optional]':'[اختياري]',
'abgelaufene Supervision':'Supervision منتهية الصلاحية','aktiviert':'مفعّل','aktuelle Ausführung':'التنفيذ الحالي','alle Argumente übertragen':'نقل جميع المعلمات',
'alle deactivated':'جميعها معطلة','als ara::com-Dienst\\nmodelliert':'مصمم كخدمة ara::com\\n','asynchronen Fehler':'خطأ غير متزامن','auf Basis des Ergebnisses':'استنادًا إلى النتيجة',
'beobachtende Anwendung':'تطبيق مراقِب','bewusst persistieren':'الحفظ المتعمد','der Ausführung vorgesehen.':'مخصص للتنفيذ.','dynamische Werte übertragen':'نقل قيم ديناميكية',
'ein oder mehrere InstanceIdentifier':'InstanceIdentifier واحد أو أكثر','erfolgreich':'بنجاح','erfolgreich / Finish':'نجاح / Finish','erfolgreiches Update':'Update ناجح',
'erneut Rollback':'Rollback مجددًا','erneut konfigurieren':'إعادة التكوين','erste UDS-Anfrage eines Clients':'أول طلب UDS من Client','eventgetrieben':'مستند إلى الأحداث',
'eventgetrieben, serialisiert':'مستند إلى الأحداث، متسلسل','fehlgeschlagen':'فشل','freigeben':'تحرير','freigegeben':'محرر',
'generierte DID-/Routine- → ara::core::Future / Promise: 28 Referenzstellen':'DID-/Routine- مُولَّدة → ara::core::Future / Promise: 28 مواضع مرجعية',
'generierte DID-/Routine- → ara::core::InstanceSpecifier: 3 Referenzstellen':'DID-/Routine- مُولَّدة → ara::core::InstanceSpecifier: 3 مواضع مرجعية',
'generierte DID-/Routine- → ara::core::Result: 14 Referenzstellen':'DID-/Routine- مُولَّدة → ara::core::Result: 14 مواضع مرجعية',
'generierte DID-/Routine- → generierte Proxys: 1 Referenzstellen':'DID-/Routine- مُولَّدة → Proxys مُولَّدة: موضع مرجعي واحد',
'generierte DID-/Routine- → namespace ara::core: 1 Referenzstellen':'DID-/Routine- مُولَّدة → namespace ara::core: موضع مرجعي واحد','generierte DID-/Routine-\\nInterfaces':'واجهات DID-/Routine-\\nمُولَّدة',
'generierte Proxys → ara::core::Future / Promise: 12 Referenzstellen':'Proxys مُولَّدة → ara::core::Future / Promise: 12 مواضع مرجعية',
'generierte Proxys → ara::core::InstanceSpecifier: 4 Referenzstellen':'Proxys مُولَّدة → ara::core::InstanceSpecifier: 4 مواضع مرجعية','generierte Proxys → ara::core::Result: 32 Referenzstellen':'Proxys مُولَّدة → ara::core::Result: 32 مواضع مرجعية',
'generierte Proxys → namespace ara::core: 3 Referenzstellen':'Proxys مُولَّدة → namespace ara::core: 3 مواضع مرجعية','generierte Proxys\\n<SI>::proxy':'Proxys مُولَّدة\\n<SI>::proxy',
'generierte Skeletons → ara::core::Future / Promise: 8 Referenzstellen':'Skeletons مُولَّدة → ara::core::Future / Promise: 8 مواضع مرجعية',
'generierte Skeletons → ara::core::InstanceSpecifier: 1 Referenzstellen':'Skeletons مُولَّدة → ara::core::InstanceSpecifier: موضع مرجعي واحد','generierte Skeletons → ara::core::Result: 20 Referenzstellen':'Skeletons مُولَّدة → ara::core::Result: 20 مواضع مرجعية',
'generierte Skeletons → namespace ara::core: 1 Referenzstellen':'Skeletons مُولَّدة → namespace ara::core: موضع مرجعي واحد','generierte Skeletons\\n<SI>::skeleton':'Skeletons مُولَّدة\\n<SI>::skeleton',
'intakte Kopie oder Initialzustand verwenden':'استخدام نسخة سليمة أو حالة ابتدائية','ja / konfiguriert':'نعم / مهيأ','kEvent / kEventSingleThread: asynchrone Dispatch':'kEvent / kEventSingleThread: توزيع غير متزامن',
'kEventSingleThread\\nsequenziell':'kEventSingleThread\\nمتسلسل','kEvent\\nparallel':'kEvent\\nمتوازٍ','kFAILED\\n(nur Alive)':'kFAILED\\n(Alive فقط)','kein Update':'لا يوجد Update',
'konfigurierte\\nLog-Senken':'مغاسل Log\\nمهيأة','konfigurierter nextState':'nextState مهيأ','kritisch + Toleranz abgelaufen':'حرج + انتهت صلاحية التفاوت',
'lokale Persistenz / IdsR.':'استمرارية محلية / IdsR.','melden':'الإبلاغ','mindestens ein Elementarstatus OK':'حالة أولية واحدة على الأقل OK','modellierte Nachricht?':'رسالة مُنمذجة؟',
'modifizierte':'معدلة','namespace ara::core\\nfreie Funktionen':'namespace ara::core\\nدوال حرة','nein':'لا','nein / Fehlerpfad':'لا / مسار الخطأ','nein / Rollback':'لا / Rollback',
'nein / nicht angefordert':'لا / غير مطلوب','nein / nicht behandelbar':'لا / غير قابل للمعالجة','nein: z. B.\\nDaemon nicht verbunden':'لا: مثلًا\\nDaemon غير متصل',
'neue Target Configuration erkennen':'اكتشاف Target Configuration جديدة','neuer Request / Abschalten':'Request جديد / إيقاف','nicht unterstützt / nicht erlaubt':'غير مدعوم / غير مسموح',
'nächste Auswertung':'التقييم التالي','nächster Block':'الكتلة التالية','projektspezifischer aktiver Zustand':'حالة نشطة خاصة بالمشروع','qualifizieren, filtern und':'تأهيل، تصفية، و',
'qualifiziertes Ergebnis':'نتيجة مؤهلة','redundante Daten aktualisieren':'تحديث البيانات المتكررة','spätere Standardisierung angekündigt; hier:':'تم الإعلان عن توحيد لاحق؛ هنا:',
'temporärer Alive-Fehler':'خطأ Alive مؤقت','teure Vorbereitung überspringen':'تجاوز التحضير المكلف','value() verwenden':'استخدام value()','value_or() / Abwesenheit behandeln':'value_or() / معالجة الغياب','value_or() /\\nAbwesenheit behandeln':'value_or() /\\nمعالجة الغياب',
'variant_alternative — partielle Spezialisierungen für cv-qualifizierte Typen (const T, volatile T, const volatile T)':'variant_alternative — تخصصات جزئية للأنواع المؤهلة بـ cv (const T, volatile T, const volatile T)',
'verarbeitet':'مُعالَج','verifiziert':'تم التحقق منه','weiter angefordert':'مطلوب إضافيًا','weitere Requests bis Timeout':'Requests إضافية حتى Timeout','wieder korrekt':'صحيح مجددًا','wiederherstellbar?':'قابل للاستعادة؟','zugelassen?':'مسموح؟',
'älteste Einträge\\nverwerfen':'تجاهل أقدم الإدخالات\\n'
}
# Labels that are wholly identifiers, API spelling, templates, or other Latin
# specification names are deliberately copied unchanged.
def pure_code(s):
    x=s.strip()
    return (x.startswith(('<','::','ara::','apext::','std::','hash','tuple_','variant_','«struct»')) or
            re.fullmatch(r'[A-Za-z0-9_:.<> ,&+*/()\[\]«»…\\-]+',x) is not None)

def render(s):
    if s in M: return M[s]
    if pure_code(s): return s
    # Conservative remaining terminology replacements; all use only caption words.
    repl=[('Referenzstellen','مواضع مرجعية'),('Fehlerbehandlung','معالجة الأخطاء'),('Container & Views','Container & Views'),('generierte','مُولَّدة'),('Fehler','أخطاء'),('Anwendung','التطبيق'),('Nachricht','رسالة'),('konfiguriert','مهيأ'),('aktualisieren','تحديث'),('aktualisiert','محدّث'),('Zustand','حالة'),('Zustände','حالات'),('erfolgreich','بنجاح'),('nicht verfügbar','غير متاح'),('nicht','غير'),('und','و'),('oder','أو'),('mit','مع'),('für','لـ'),('bei','لدى'),('von','من')]
    for a,b in repl: s=re.sub(r'(?<!\w)'+re.escape(a)+r'(?!\w)',b,s)
    return s

out=[]
for i,r in enumerate(src):
    if i < len(old):
        t=old[i]['t']
        # Correct any code-only label that an automatic translator altered.
        if pure_code(r['de']): t=r['de']
    else:
        t=render(r['de'])
    out.append({'id':r['id'],'t':t})
assert len(out)==len(src)
(B/'batch_17.out.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in out),encoding='utf-8')
print(len(out))
