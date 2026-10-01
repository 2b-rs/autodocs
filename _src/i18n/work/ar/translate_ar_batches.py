import json, re, sys, time
from pathlib import Path
from deep_translator import GoogleTranslator

BASE=Path('/home/user/workspace/ara-api-doku/_src/i18n/work/ar')

# Phrases and technical terms that must remain in their original Latin spelling.
PROTECTED_PHRASES = [
 'Adaptive Platform','Functional Cluster','Functional Clusters','Service Discovery','Diagnostic Management','Diagnostic Manager','Diagnostic Server',
 'Communication Management','State Management','Execution Management','Platform Health Management','Update and Configuration Management',
 'Update and Configuration','ServiceInterface','InstanceSpecifier','InstanceIdentifier','InstanceIdentifier','MethodCallProcessingMode',
 'Global Supervision','Alive Supervision','Operation Cycle','Function Group','Reporting Mode','Vehicle-Announcement','File Storage','File Storages',
 'Key-Value Storage','Key-Value Storages','Shared State','Error Domain','ErrorDomain','Error-Domain','Error Domain','ErrorDomain',
 'End-to-End','E2E','SecOC','Freshness','Manifest','ARXML','SOVD','UDS','DoIP','DTC','NRC','PHM','DM','EM','ARA','IdsM','FVM','SHWA',
 'thread-safe','not thread-safe','non-thread-safe','exception-safe','exception safe','not exception-safe','conditional','rollback_semantics',
 'Default Session','Non-default Session','Normal Operation','Ready Sleep','Prepare Bus-Sleep','Bus-Sleep','NO_COM','FULL_COM',
 'Future','Promise','Result','Optional','Monostate','Array','Map','Buffer','Accessor','Logger','LogStream','Executor','Notifier','Callback','Handler',
 'Provider','Consumer','Proxy','Skeleton','Event','Trigger','Field','SamplePtr','Queue','Device','Certificate','Authentication','Conversation',
 'Context','Output','Formatter','Format','Polling','Backup','Gateway','Kernel','Host','PackageManagement','CleanUpPersistency',
 'Create','CreateLogger','Initialize','Deinitialize','Finish','Cancel','Connect','Activate','Clear','Reset','Get','Set','GetValue','Log','Domain',
 'Error','Exception','Condition','Indicator','Idle','Off','Output','Argument','Application','Framework','Access','Range','Rate','Recovery',
 'Repeat Message','Reporting','RequestResults','ResolveInstanceIDs','ResetToDefaultSession','ErrorRecoveryTable','Global Time Master',
 'LT/DLT network sink','C++-Binding','Logging Backend','Method Calls','API','APIs','API-Detail','ISO-C++','C++','std','Runtime',
 'non-verbose','verbose','in-place','Default-Konstruktor','Move-Konstruktor','Move-Konstruktion','Move-Zuweisung','Copy','Move'
]
# Longer terms first, preventing components from being separately handled.
PROTECTED_PHRASES.sort(key=len, reverse=True)

# Identifier-shaped tokens (C++ punctuation, calls, underscores, digits, or
# internal capitalization).  Deliberately do not treat every capitalized word
# as an identifier: German capitalizes ordinary nouns.
ID_RE=re.compile(r'(?<![\w:])(?:[A-Za-z_]\w*(?:(?:::|->|\.)[A-Za-z_]\w*)+|[A-Za-z_]\w*\([^\s()]{0,100}\)|[A-Za-z_]*_[A-Za-z_\d]*|[A-Za-z]+\d+[A-Za-z_\d]*|[A-Za-z]*[a-z][A-Z][A-Za-z_\d]*)(?![\w:])')
PLACEHOLDER_RE=re.compile(r'⟦\d+⟧|\[SWS_[^\]]+\]|AUTOSAR_AP_SWS_[A-Za-z0-9_]+|EXP_[A-Za-z0-9_]+|FO_[A-Za-z0-9_]+')
TAG_RE=re.compile(r'</?[^>]+>')
QUOTED_RE=re.compile(r'„[^“]*[A-Za-z][^“]*“|"[^"]*[A-Za-z][^"]*"')

# Exact label improvements applied after machine translation. These correct recurrent
# short diagram captions while retaining code terms untouched.
FIXED = {
 'Typ':'النوع','Angebot, Antwort und Eskalation':'العرض والاستجابة والتصعيد','Bewertungsgrenzen':'حدود التقييم','Vertrag der Session':'عقد الجلسة',
 'Konstanten / Variablen':'الثوابت / المتغيرات','Keine Kopie des Signalbesitzes':'لا نسخ لملكية الإشارة','Wann aufrufen':'متى يُستدعى',
 'Fehler weitergeben':'تمرير الخطأ','Zykluswechsel abonnieren':'الاشتراك في تغيّر الدورة','Vom Request zum Zielzustand':'من Request إلى الحالة المستهدفة',
 'Update-Sitzung als Zustandskoordination':'جلسة Update كتنسـيق للحالة','Nutzungsgrenze':'حد الاستخدام','Schlüssel- und Zugriffskonzept':'مفهوم المفتاح والوصول',
 'Fehlerkontext weitergeben':'تمرير سياق الخطأ','Fehler trennen':'فصل الأخطاء','SOVD-Kontext':'سياق SOVD','Praktische Reihenfolge':'التسلسل العملي',
 'Einordnung':'التصنيف','Fehlerstrategie':'استراتيجية الأخطاء','Architekturkontext':'السياق المعماري','Fehlerbehandlung':'معالجة الأخطاء',
 'Fehlercodes auswerten':'تقييم رموز الأخطاء','Exception-Sicherheit':'سلامة الاستثناءات','Kompatibilität':'التوافق','Parameter':'المعلمات',
 'Zugriffsobjekt für einen durch InstanceSpecifier referenzierten Netzwerk-Handle; vorgesehen für State Management.':'كائن وصول لمقبض شبكة مشار إليه بواسطة InstanceSpecifier؛ مخصص لـ State Management.',
}

def protect(text):
    saved=[]
    def add(m):
        token=f'¤{len(saved)}¤'
        saved.append(m.group(0))
        return token
    # Preserve the literal two-character line-break escape, directional symbols,
    # tags, protected placeholders/IDs, quoted source-language spec text, fixed
    # AUTOSAR terminology, then code identifiers.
    text=TAG_RE.sub(add,text)
    text=PLACEHOLDER_RE.sub(add,text)
    text=QUOTED_RE.sub(add,text)
    def add_identifier(m):
        # Do not remask opaque tokens already inserted by an earlier protection
        # pass.
        return m.group(0) if re.fullmatch(r'¤\d+¤', m.group(0)) else add(m)
    text=ID_RE.sub(add_identifier,text)
    for p in PROTECTED_PHRASES:
        text=re.sub(re.escape(p), lambda m:add(m), text)
    # These are inserted last, so their mnemonic letters cannot be treated as
    # identifiers by the preceding protection pass.
    text=text.replace('\\n', '¤L¤')
    text=text.replace('→','¤A¤').replace('·','¤M¤')
    return text,saved

def unprotect(text,saved):
    text=text.replace('¤L¤','\\n').replace('¤A¤','→').replace('¤M¤','·')
    for i,s in enumerate(saved):
        # Google occasionally inserts whitespace around opaque tokens; normalize it.
        text=re.sub(r'¤\s*'+str(i)+r'\s*¤', s, text)
    return text

def translate_chunk(rows):
    inputs=[]; details=[]
    for r in rows:
        if r['de'] in FIXED:
            inputs.append(None); details.append(None)
        else:
            p,s=protect(r['de']); inputs.append(p); details.append(s)
    active=[x for x in inputs if x is not None]
    results=[]
    if active:
        # Translate at a deliberately low, documented-safe request rate.  This
        # avoids service throttling on the large label batch.
        engine=GoogleTranslator(source='de', target='ar')
        for item in active:
            results.append(engine.translate(item))
            time.sleep(.36)
    out=[]; j=0
    for r,p,s in zip(rows,inputs,details):
        if p is None: t=FIXED[r['de']]
        else:
            t=unprotect(results[j],s); j+=1
        out.append({'id':r['id'],'t':t})
    return out

def run(batch):
    src=BASE/f'{batch}.jsonl'; dst=BASE/f'{batch}.out.jsonl'
    rows=[json.loads(x) for x in src.read_text(encoding='utf-8').splitlines()]
    # Resume any already committed 40-entry chunks after an external-service
    # interruption; each completed chunk has been written atomically enough for
    # this line-oriented workflow.
    done=0
    if dst.exists():
        existing=[json.loads(x) for x in dst.read_text(encoding='utf-8').splitlines() if x]
        if all(r['id']==rows[i]['id'] for i,r in enumerate(existing)):
            done=len(existing)
        else:
            raise RuntimeError(f'{dst} does not match its source ordering')
    else:
        dst.write_text('',encoding='utf-8')
    for start in range(done,len(rows),40):
        chunk=rows[start:start+40]
        out=translate_chunk(chunk)
        with dst.open('a',encoding='utf-8') as f:
            for r in out:
                f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
        print(f'{batch}: committed {min(start+40,len(rows))}/{len(rows)}',flush=True)
        time.sleep(.25)

if __name__=='__main__':
    run(sys.argv[1])
