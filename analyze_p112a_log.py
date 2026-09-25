#!/usr/bin/env python3
import re,sys
from pathlib import Path
if len(sys.argv)!=2:
    print('usage: python3 analyze_p112a_log.py uzuy_log.txt'); raise SystemExit(2)
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
ready=[(i+1,l) for i,l in enumerate(lines) if '[NSC:P112A] READY' in l]
rx=re.compile(r'\[NSC:P112A\] ENTRY n=(\d+) actor=(0x[0-9a-f]+) side=(\d+) char=(\d+) caller_off=(0x[0-9a-f]+) '
              r'action=(\d+)->(\d+) e94=(\d+)->(\d+) e98=(\d+)->(\d+) e9c=(\d+)->(\d+) '
              r'bda4=(\d+)->(\d+) bda8=(\d+)->(\d+) bdc8=(\d+)->(\d+) '
              r'peer=(0x[0-9a-f]+|\(nil\)) pvalid=(\d+) pside=(\d+) pchar=(\d+) paction=(\d+) pe94=(\d+) pe9c=(\d+)')
rows=[]
for i,l in enumerate(lines):
    m=rx.search(l)
    if not m: continue
    g=m.groups()
    keys=['n','actor','side','char','caller','action0','action1','e940','e941','e980','e981','e9c0','e9c1',
          'bda40','bda41','bda80','bda81','bdc80','bdc81','peer','pvalid','pside','pchar','paction','pe94','pe9c']
    d=dict(zip(keys,g)); d['line']=i+1
    for k in keys:
        if k not in ('actor','caller','peer'): d[k]=int(d[k])
    rows.append(d)
print('P112_READY',len(ready),ready[:3])
print('P112_ENTRY_COUNT',len(rows))
for d in rows:
    print('ENTRY',f"line={d['line']}",f"n={d['n']}",f"actor={d['actor']}",f"side={d['side']}",f"char={d['char']}",
          f"caller={d['caller']}",f"action={d['action0']}->{d['action1']}",f"e94={d['e940']}->{d['e941']}",
          f"e9c={d['e9c0']}->{d['e9c1']}",f"peer={d['peer']}",f"pside={d['pside']}",f"pchar={d['pchar']}",
          f"paction={d['paction']}",f"pe94={d['pe94']}")
# Same-session roles inferred only from concrete runtime state/identity.
vanilla_victim=[d for d in rows if d['side']==1 and d['action0']==74 and d['e940']==1 and d['pvalid']==1 and d['pside']==0 and d['pchar']!=281]
custom_victim=[d for d in rows if d['side']==1 and d['action0']==74 and d['e940']==1 and d['pvalid']==1 and d['pside']==0 and d['pchar']==281]
custom_cleanup=[d for d in rows if d['side']==0 and d['char']==281 and d['action0']==708]
print('VANILLA_VICTIM_ENTRY_COUNT',len(vanilla_victim))
for d in vanilla_victim: print('VANILLA_VICTIM_ENTRY',f"line={d['line']}",f"caller={d['caller']}",f"victim_char={d['char']}",f"attacker_char={d['pchar']}")
print('CUSTOM_TOBI_VICTIM_ENTRY_COUNT',len(custom_victim))
for d in custom_victim: print('CUSTOM_TOBI_VICTIM_ENTRY',f"line={d['line']}",f"caller={d['caller']}",f"victim_char={d['char']}")
print('CUSTOM_TOBI_ATTACKER_CLEANUP_COUNT',len(custom_cleanup))
for d in custom_cleanup: print('CUSTOM_TOBI_ATTACKER_CLEANUP',f"line={d['line']}",f"caller={d['caller']}",f"peer_char={d['pchar']}",f"peer_action={d['paction']}",f"peer_e94={d['pe94']}")
vc=sorted(set(d['caller'] for d in vanilla_victim)); cc=sorted(set(d['caller'] for d in custom_cleanup))
print('VANILLA_VICTIM_CALLERS',vc)
print('CUSTOM_ATTACKER_CLEANUP_CALLERS',cc)
if vanilla_victim and not custom_victim and custom_cleanup:
    print('DECISION=MISSING_CUSTOM_VICTIM_PRODUCER_ENTRY')
    if vc and cc and set(vc)!=set(cc): print('DETAIL=vanilla victim and custom attacker cleanup originate from different caller sets')
    elif vc and cc: print('DETAIL=same caller set but native call targets different actor roles; inspect target selection before call')
elif custom_victim:
    print('DECISION=CUSTOM_VICTIM_DOES_ENTER_PRODUCER')
    print('DETAIL=compare caller and post-state; missing admission is downstream/inside producer rather than producer absence')
elif not vanilla_victim:
    print('DECISION=NO_VANILLA_VICTIM_ENTRY_CAPTURED')
    print('DETAIL=test must include one successful vanilla UJ before Tobi own-UJ')
else:
    print('DECISION=INCOMPLETE_CUSTOM_FAILURE_WINDOW')
