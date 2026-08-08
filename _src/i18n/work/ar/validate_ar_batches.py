import json,re,sys
from pathlib import Path
B=Path('/home/user/workspace/ara-api-doku/_src/i18n/work/ar')
PH=re.compile(r'⟦\d+⟧')
TAG=re.compile(r'</?[^>]+>')
SWS=re.compile(r'\[SWS_[^\]]+\]')
for b in ['batch_16','batch_17']:
 s=(B/f'{b}.jsonl').read_text(encoding='utf-8').splitlines(); o=(B/f'{b}.out.jsonl').read_text(encoding='utf-8').splitlines()
 assert len(s)==len(o), (b,len(s),len(o))
 errs=[]
 for n,(a,z) in enumerate(zip(s,o),1):
  try: x=json.loads(a); y=json.loads(z)
  except Exception as e: errs.append((n,'json',str(e))); continue
  if set(y)!={'id','t'}: errs.append((n,'keys',set(y)))
  if x['id']!=y['id']: errs.append((n,'id',x['id'],y['id']))
  if sorted(PH.findall(x['de']))!=sorted(PH.findall(y['t'])): errs.append((n,'placeholders',PH.findall(x['de']),PH.findall(y['t'])))
  if TAG.findall(x['de'])!=TAG.findall(y['t']): errs.append((n,'tags',TAG.findall(x['de']),TAG.findall(y['t'])))
  if SWS.findall(x['de'])!=SWS.findall(y['t']): errs.append((n,'sws',SWS.findall(x['de']),SWS.findall(y['t'])))
  if x['de'].count('\\n')!=y['t'].count('\\n'): errs.append((n,'literal_n',x['de'].count('\\n'),y['t'].count('\\n')))
  if y['t'].count('¤'): errs.append((n,'opaque token',y['t']))
 print(b,'lines',len(o),'errors',len(errs))
 for e in errs[:20]:print(' ',e)
 if errs:sys.exit(1)
