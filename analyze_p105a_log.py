#!/usr/bin/env python3
from pathlib import Path
import re,sys,collections
if len(sys.argv)!=2:
    raise SystemExit('usage: analyze_p105a_log.py <uzuy_log.txt>')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
ready=[(i+1,x) for i,x in enumerate(lines) if '[NSC:P105A] READY' in x]
rows=[]
rx=re.compile(r'\[NSC:P105A\] CTRL seq=(\d+) ctrl=(4C0|520) phase=(\d+) entry_off=0x([0-9a-fA-F]+).*?side=(\d+) char=(\d+) mode=(\d+) caller_off=0x([0-9a-fA-F]+) callsite_off=0x([0-9a-fA-F]+) action=(\d+)->(\d+).*?slot4c0_off=0x([0-9a-fA-F]+) slot520_off=0x([0-9a-fA-F]+)')
for i,x in enumerate(lines):
    m=rx.search(x)
    if not m: continue
    seq=int(m.group(1)); ctrl=m.group(2); phase=int(m.group(3)); entry=int(m.group(4),16)
    side=int(m.group(5)); cid=int(m.group(6)); mode=int(m.group(7)); caller=int(m.group(8),16); callsite=int(m.group(9),16)
    pre=int(m.group(10)); post=int(m.group(11)); s4=int(m.group(12),16); s5=int(m.group(13),16)
    rows.append(dict(line=i+1,seq=seq,ctrl=ctrl,phase=phase,entry=entry,side=side,cid=cid,mode=mode,caller=caller,callsite=callsite,pre=pre,post=post,s4=s4,s5=s5,text=x))
print('READY',len(ready))
for n,x in ready: print(' ready_line',n,x)
print('CTRL_ROWS',len(rows))
assert ready,'missing P105A READY'
expected_entry={'4C0':0x7DDD94,'520':0x7E64D4}
bad=[r for r in rows if r['side']!=0 or r['entry']!=expected_entry[r['ctrl']] or r['s4']!=0x7DDD94 or r['s5']!=0x7E64D4]
print('BAD_VALIDATION_ROWS',len(bad))
if bad:
    for r in bad[:20]: print(' BAD',r['text'])
    raise SystemExit(2)

for cid,label in [(91,'VANILLA91'),(281,'CUSTOM281')]:
    rr=[r for r in rows if r['cid']==cid]
    print('\n'+label,'rows',len(rr))
    for r in rr:
        print(f" line={r['line']} seq={r['seq']} phase={r['phase']} ctrl={r['ctrl']} mode={r['mode']} caller=0x{r['caller']:x} callsite=0x{r['callsite']:x} action={r['pre']}->{r['post']}")
    by=collections.Counter((r['ctrl'],r['mode'],r['caller']) for r in rr if r['phase']==0)
    print(' ENTER signatures:')
    for k,n in sorted(by.items()): print('  ',k,'x',n)

print('\nFOCUSED transitions around known producers from generic P59/P93 logs:')
for i,x in enumerate(lines):
    if ('caller_off=0x7e6ec8' in x.lower() and ('code=710' in x or 'index=710' in x)) or ('caller_off=0x7de558' in x.lower() and ('code=261' in x or 'index=261' in x)):
        print(i+1,x)
print('\nInterpretation target: compare which controller+mode ENTER surrounds vanilla 707->710 versus custom 708->261. P105A is observation-only; do not infer a dispatch fix unless the same pattern reproduces.')
