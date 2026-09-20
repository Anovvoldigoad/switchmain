#!/usr/bin/env python3
import re,sys,collections
from pathlib import Path
if len(sys.argv)!=2:
    raise SystemExit('usage: analyze_p58a_log.py uzuy_log.txt')
t=Path(sys.argv[1]).read_text(errors='replace')
ready='[NSC:P58A] READY' in t
pat=re.compile(r'\[NSC:P58A\] PLAY_CALL n=(\d+) actor=(\S+) valid=(\d+) side=(\d+) char=(\d+) index=(-?\d+) a2=(-?\d+) a3=(-?\d+) a4=(-?\d+) a5=(-?\d+) pre=(\d+) post=(\d+) ret=(-?\d+) caller_lr=(\S+) caller_main=(\d+) caller_off=0x([0-9a-fA-F]+) callsite_off=0x([0-9a-fA-F]+) call_m8=([0-9a-fA-F]{8}) call_m4=([0-9a-fA-F]{8})')
rows=[]
for m in pat.finditer(t):
    g=m.groups()
    rows.append({
      'n':int(g[0]),'char':int(g[4]),'index':int(g[5]),'a2':int(g[6]),'a3':int(g[7]),
      'pre':int(g[10]),'post':int(g[11]),'ret':int(g[12]),'main':int(g[14]),
      'caller':int(g[15],16),'callsite':int(g[16],16),'m8':g[17],'m4':g[18]
    })
print('P58A_READY='+('PASS' if ready else 'FAIL'))
print('PLAY_CALL_ROWS='+str(len(rows)))
print('BY_CHAR='+repr(dict(collections.Counter(r['char'] for r in rows))))
custom=[r for r in rows if r['char']>280]
print('CUSTOM_INDEX_COUNTS='+repr(dict(collections.Counter(r['index'] for r in custom))))
for r in custom:
    print('CUSTOM n={n} index={index} pre={pre} post={post} ret={ret} caller_main={main} caller_off=0x{caller:x} callsite=0x{callsite:x} m8={m8} m4={m4}'.format(**r))
rows445=[r for r in custom if r['index']==445]
print('CUSTOM_445_ROWS='+str(len(rows445)))
print('CUSTOM_445_CALLERS='+repr(dict(collections.Counter(hex(r['caller']) for r in rows445))))
print('CUSTOM_445_CALLSITES='+repr(dict(collections.Counter(hex(r['callsite']) for r in rows445))))
if rows445 and all(r['main']==1 for r in rows445):
    print('P58A_445_CALLER_PROVEN=YES')
else:
    print('P58A_445_CALLER_PROVEN=NO')
