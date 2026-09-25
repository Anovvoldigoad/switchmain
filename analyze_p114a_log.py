#!/usr/bin/env python3
import re,sys
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt')
lines=p.read_text(errors='replace').splitlines()
ts_re=re.compile(r'^\[\s*([0-9.]+)\]')
pre_re=re.compile(r'\[NSC:P114A\] PREFLIGHT .*?type=(\d+) ret=(\d+) caller_off=0x([0-9a-fA-F]+)')
play_re=re.compile(r'\[NSC:P59A\] PLAY_CALL .*?side=(\d+) char=(\d+) index=(\d+) .*?caller_off=0x([0-9a-fA-F]+)')
ready=[(i,l) for i,l in enumerate(lines,1) if '[NSC:P114A] READY' in l]
prefs=[]; plays=[]
for i,l in enumerate(lines,1):
 m=ts_re.match(l); t=float(m.group(1)) if m else None
 q=pre_re.search(l)
 if q: prefs.append((i,t,int(q.group(1)),int(q.group(2)),int(q.group(3),16),l))
 q=play_re.search(l)
 if q and t is not None: plays.append((i,t,int(q.group(1)),int(q.group(2)),int(q.group(3)),int(q.group(4),16),l))
print('READY_COUNT',len(ready))
for i,l in ready: print('READY',i,l)
print('PREFLIGHT_COUNT',len(prefs))
for x in prefs: print('PREFLIGHT',x[0],'t',x[1],'type',x[2],'ret',x[3],'caller',hex(x[4]))
# Build side0 UJ windows from action700 until terminal710 or fallback261, bounded to 6s.
starts=[x for x in plays if x[2]==0 and x[4]==700]
windows=[]
for s in starts:
 end=None
 for x in plays:
  if x[1] < s[1]: continue
  if x[1] > s[1]+6.0: break
  if x[2]==0 and x[3]==s[3] and x[4] in (710,261):
   end=x; break
 et=(end[1] if end else s[1]+6.0)
 hit=[q for q in prefs if q[1] is not None and s[1]-0.05 <= q[1] <= et+0.05]
 windows.append((s,end,hit))
print('UJ_WINDOWS',len(windows))
for s,e,hit in windows:
 print('UJ char',s[3],'start',s[1],'terminal',e[4] if e else None,'end',e[1] if e else None,'preflights',[(q[3],q[1]) for q in hit])
# Decision hints, especially custom char281 if present.
custom=[w for w in windows if w[0][3]==281]
if custom:
 h=custom[-1][2]
 if not h:
  print('DECISION=CUSTOM_NEVER_REACHES_77C4B0_TYPE9_PREFLIGHT')
 elif any(q[3]!=0 for q in h):
  print('DECISION=CUSTOM_TYPE9_BLOCKER_RET_NONZERO')
 else:
  print('DECISION=CUSTOM_PASSES_TYPE9_PREFLIGHT_ROOT_IS_DEEPER_795ED0_7F78FC_OR_PAIRING')
else:
 print('DECISION=NO_CUSTOM_UJ_WINDOW_FOUND')
