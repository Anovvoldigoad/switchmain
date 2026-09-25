#!/usr/bin/env python3
import re,sys
from collections import Counter,defaultdict
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
lines=open(p,errors='replace').read().splitlines()
S=[x for x in lines if '[NSC:P113A] SESSION' in x]
P=[x for x in lines if '[NSC:P113A] PEER' in x]
R=[x for x in lines if '[NSC:P113A] READY' in x]
print('P113_READY_COUNT',len(R))
if R: print(R[-1])
print('P113_SESSION_COUNT',len(S),'P113_PEER_COUNT',len(P))
rx=re.compile(r'n=(\d+).*?side=(\d+).*?char=(\d+).*?caller_off=0x([0-9a-fA-F]+).*?ret=(\d+).*?action=(\d+)->(\d+).*?e94=(\d+)->(\d+).*?e98=(\d+)->(\d+).*?e9c=(\d+)->(\d+).*?e50=(-?\d+).*?s6=(\d+)->(\d+).*?s9=(\d+)->(\d+).*?s10=(\d+)->(\d+)')
rows=[]
for x in S:
 m=rx.search(x)
 if m:
  vals=list(map(int,m.groups()[:3]))+[int(m.group(4),16)]+list(map(int,m.groups()[4:]))
  keys=['n','side','char','caller','ret','a0','a1','e940','e941','e980','e981','e9c0','e9c1','e50','s60','s61','s90','s91','s100','s101']
  rows.append(dict(zip(keys,vals)))
print('PARSED',len(rows))
print('CALLERS',Counter(hex(r['caller']) for r in rows))
print('CHARS',Counter(r['char'] for r in rows))
print('RET',Counter(r['ret'] for r in rows))
print('TYPE10_TRANSITIONS',Counter((r['s100'],r['s101']) for r in rows))
print('TYPE6_PRE',Counter(r['s60'] for r in rows),'TYPE9_PRE',Counter(r['s90'] for r in rows))
print('\nLIKELY_UJ_RELEVANT:')
for r,x in zip(rows,S):
 if r['a0'] in (74,445,700,707,708,710) or r['a1'] in (700,707,708,710) or r['s100']!=r['s101'] or r['ret']:
  print(x)
# Decision-oriented summary
van=[r for r in rows if r['char']!=281 and (r['s100']!=r['s101'] or r['ret'] or r['a0'] in (700,707,710))]
tob=[r for r in rows if r['char']==281 and (r['a0'] in (74,445,700,707,708,710) or r['ret'] or r['s100']!=r['s101'])]
print('\nVANILLA_RELEVANT_COUNT',len(van),'TOBI_RELEVANT_COUNT',len(tob))
if any(r['s100']==0 and r['s101']==1 for r in van): print('VANILLA_TYPE10_CREATE_OBSERVED=1')
else: print('VANILLA_TYPE10_CREATE_OBSERVED=0')
if not tob:
 print('DECISION=TOBI_NEVER_REACHES_7EF098_IN_UJ_WINDOW')
elif any(r['s60'] or r['s90'] for r in tob if r['ret']==0):
 print('DECISION=TOBI_REACHES_WRAPPER_BUT_TYPE6_OR_TYPE9_BLOCKER_PRESENT')
elif any(r['ret']==0 and r['s60']==0 and r['s90']==0 and r['s100']==0 for r in tob):
 print('DECISION=TOBI_REACHES_WRAPPER_RET0_WITHOUT_TYPE6_9_BLOCKER__PROBE_INNER_7EF128_NEXT')
elif any(r['s100']==0 and r['s101']==1 for r in tob):
 print('DECISION=TOBI_CREATES_TYPE10__FAILURE_IS_DOWNSTREAM')
else:
 print('DECISION=INSPECT_RELEVANT_ROWS')
