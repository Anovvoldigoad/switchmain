#!/usr/bin/env python3
import re,sys
from collections import Counter,defaultdict
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
lines=open(p,errors='replace').read().splitlines()
rows=[]
pat=re.compile(r'\[NSC:P116A\] CALL n=(\d+) actor=(\S+) side=(\d+) char=(\d+) caller_off=0x([0-9a-fA-F]+) bucket=(\d+) known=(\d+) ret=(\d+) action=(\d+)->(\d+) e94=(\d+)->(\d+) e98=(\d+)->(\d+) e9c=(\d+)->(\d+) .*?s9=(\d+)->(\d+) s10=(\d+)->(\d+)')
for i,l in enumerate(lines,1):
 m=pat.search(l)
 if not m: continue
 g=m.groups(); rows.append(dict(line=i,n=int(g[0]),actor=g[1],side=int(g[2]),char=int(g[3]),caller=int(g[4],16),bucket=int(g[5]),known=int(g[6]),ret=int(g[7]),a0=int(g[8]),a1=int(g[9]),e940=int(g[10]),e941=int(g[11]),e980=int(g[12]),e981=int(g[13]),e9c0=int(g[14]),e9c1=int(g[15]),s90=int(g[16]),s91=int(g[17]),s100=int(g[18]),s101=int(g[19])))
print('P116_READY',sum('[NSC:P116A] READY' in l and 'probe_ok=1' in l for l in lines))
print('CALL_ROWS',len(rows))
print('BY_CALLER')
for k,v in Counter((r['caller'],r['bucket']) for r in rows).most_common(): print(v,hex(k[0]),'bucket',k[1])
print('BY_CHAR_CALLER')
for k,v in Counter((r['char'],r['caller'],r['bucket']) for r in rows).most_common(): print(v,'char',k[0],hex(k[1]),'bucket',k[2])
creates=[r for r in rows if r['s100']==0 and r['s101']!=0]
print('S10_CREATION_ROWS',len(creates))
for r in creates: print(' CREATE line',r['line'],'char',r['char'],'caller',hex(r['caller']),'bucket',r['bucket'],'action',f"{r['a0']}->{r['a1']}",'ret',r['ret'])
custom=[r for r in rows if r['char']==281]
print('CUSTOM281_CALLS',len(custom))
for r in custom: print(' CUSTOM line',r['line'],'caller',hex(r['caller']),'bucket',r['bucket'],'action',f"{r['a0']}->{r['a1']}",'s10',f"{r['s100']}->{r['s101']}",'ret',r['ret'])
if not custom:
 print('DECISION=CUSTOM281_NEVER_REACHES_OUTER_7EF098')
 print('NEXT=use vanilla S10 creation caller bucket, then compare its upstream producer requirements against custom 707/708')
elif any(r['s100']==0 and r['s101']!=0 for r in custom):
 print('DECISION=CUSTOM281_CREATES_TYPE10')
 print('NEXT=divergence is downstream of outer setup')
else:
 print('DECISION=CUSTOM281_REACHES_OUTER_BUT_DOES_NOT_CREATE_TYPE10')
 print('NEXT=inspect inner blocker/peer context for the exact custom caller')
