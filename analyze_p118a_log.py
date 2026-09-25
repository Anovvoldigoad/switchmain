#!/usr/bin/env python3
import re,sys
from collections import Counter
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
rows=[]; actions=[]; ready=0
rxn=re.compile(r'\[NSC:P118A\] NEIGH n=(\d+) event=(0x[0-9a-f]+) idx=(-?\d+) raw=(\d+) norm=(\d+) type10_11=(\d+) gate_ret=(\d+) near10_delta=(-?\d+) m4=(\d+) m3=(\d+) m2=(\d+) m1=(\d+) cur=(\d+) p1=(\d+) p2=(\d+) p3=(\d+) p4=(\d+) mask48=0x([0-9a-f]+)',re.I)
rxa=re.compile(r'\[NSC:P59A\] PLAY_CALL .*?char=(\d+) index=(\d+) .*?pre=(\d+) post=(\d+)')
rt=re.compile(r'^\[\s*([0-9.]+)\]')
with open(p,errors='replace') as f:
 for ln,line in enumerate(f,1):
  if '[NSC:P118A] READY' in line: ready+=1
  tm=rt.search(line); t=float(tm.group(1)) if tm else None
  m=rxn.search(line)
  if m:
   g=m.groups(); rows.append({'line':ln,'t':t,'n':int(g[0]),'event':g[1],'idx':int(g[2]),'raw':int(g[3]),'norm':int(g[4]),'t1011':int(g[5]),'ret':int(g[6]),'near10':int(g[7]),'near':[int(x) for x in g[8:17]],'mask':g[17]})
  a=rxa.search(line)
  if a: actions.append({'line':ln,'t':t,'char':int(a.group(1)),'index':int(a.group(2)),'pre':int(a.group(3)),'post':int(a.group(4))})
print('P118_READY',ready)
print('NEIGH_ROWS',len(rows))
print('RAW_TYPE_COUNTS',dict(sorted(Counter(x['raw'] for x in rows).items())))
for x in rows: print(' NEIGH',x)
custom=[x for x in actions if x['char']==281]
print('CUSTOM281_ACTIONS')
for x in custom: print(' ',x)
if custom:
 lo=min(x['t'] for x in custom if x['t'] is not None)-1
 hi=max(x['t'] for x in custom if x['t'] is not None)+1
 cw=[x for x in rows if x['t'] is not None and lo<=x['t']<=hi]
 print('CUSTOM281_WINDOW',lo,hi,'ROWS',len(cw),'RAW',dict(Counter(x['raw'] for x in cw)))
 for x in cw: print(' ',x)
 if cw:
  direct=any(x['t1011'] for x in cw)
  nearby=[x for x in cw if x['near10'] != 127]
  print('CUSTOM_DIRECT_TYPE10',int(direct),'CUSTOM_NEAR_TYPE10_ROWS',len(nearby))
  if not direct and not nearby:
   print('DECISION=CUSTOM_LOCAL_EVENT_NEIGHBORHOODS_HAVE_NO_TYPE10_WITHIN_PM32')
   print('NEXT=back-slice action707 event-block/data selection; do not force session/state')
  elif not direct and nearby:
   print('DECISION=TYPE10_EXISTS_NEAR_CUSTOM_CURSOR_BUT_IS_NOT_DISPATCHED')
   print('NEXT=trace event-index/cursor selection producer before main+0x77B560')
van=[x for x in actions if x['char']<=280 and x['index']==710 and x['post']==710]
if van:
 v=van[0]; lo=v['t']-3 if v['t'] is not None else 0; hi=v['t']+0.5 if v['t'] is not None else 0
 vw=[x for x in rows if x['t'] is not None and lo<=x['t']<=hi]
 print('VANILLA710',v)
 print('VANILLA_WINDOW_ROWS',len(vw))
 for x in vw: print(' ',x)
