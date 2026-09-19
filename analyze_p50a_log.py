#!/usr/bin/env python3
from pathlib import Path
import argparse,re,collections
ap=argparse.ArgumentParser(description='Analyze NSC P50A condition compatibility log')
ap.add_argument('log'); args=ap.parse_args(); lines=Path(args.log).read_text(errors='replace').splitlines()
p50=[x for x in lines if '[NSC:P50A]' in x]
ready=[x for x in p50 if '] READY ' in x]
get_re=re.compile(r'COND_GET index=(\d+) slot=(\d+) name=([^ ]+)')
e121_re=re.compile(r'EVT121_SELF .*?char=(\d+).*?text=([^ ]*) .*?resolved=(\d+).*?executed=(\d+).*?apply_ret=(\d+)')
pa_re=re.compile(r'PLAY_ACTION .*?char=(\d+) index=(-?\d+) ret=(-?\d+).*?pre_action=(\d+) post_action=(\d+)')
e13_re=re.compile(r'EVT13_AWAKE .*?char=(\d+)')
gets=[]; ev=[]; pa=[]; e13=[]
for l in p50:
    m=get_re.search(l)
    if m: gets.append((int(m.group(1)),int(m.group(2)),m.group(3)))
    m=e121_re.search(l)
    if m: ev.append((int(m.group(1)),m.group(2),int(m.group(3)),int(m.group(4)),int(m.group(5))))
    m=pa_re.search(l)
    if m: pa.append(tuple(map(int,m.groups())))
    m=e13_re.search(l)
    if m: e13.append(int(m.group(1)))
print('P50A_LOG_ANALYSIS')
print('ready='+('PASS' if ready else 'MISSING'))
if ready: print(ready[-1])
print('custom_condition_gets='+str(len(gets)))
if gets:
    by=collections.Counter((i,n) for i,_,n in gets)
    print('condition_get_summary='+';'.join(f'{i}:{n}x{c}' for (i,n),c in sorted(by.items())))
print('event121_self='+str(len(ev)))
for row in ev[:30]: print('EVT121 char=%d text=%s resolved=%d executed=%d apply_ret=%d'%row)
live=[r for r in ev if r[2]>=512 and r[3]==1]
print('extended_condition_resolution='+('PASS' if live else 'NOT_OBSERVED'))
chars=sorted({r[0] for r in pa if r[0]>280})
for c in chars:
    seq=[r[1] for r in pa if r[0]==c and r[1] in {700,707,708,709,710,711,712,713,714,740}]
    print(f'char_{c}_uj_sequence='+('->'.join(map(str,seq)) if seq else '<none>'))
    print(f'char_{c}_evt13_count={sum(1 for x in e13 if x==c)}')
    if 710 in seq:
        print(f'char_{c}_uj_handoff=REACHED_710')
    elif 708 in seq:
        print(f'char_{c}_uj_handoff=STILL_708')
print('DECISION:')
if live:
    print('- Dynamic custom-condition lookup is live; condition storage/lookup gap is closed.')
    any710=any(r[0]>280 and r[1]==710 for r in pa)
    any708=any(r[0]>280 and r[1]==708 for r in pa)
    if any710:
        print('- Custom UJ reached 710: condition compatibility is causally improving the UJ handoff.')
    elif any708:
        print('- Conditions resolve but custom UJ still reaches 708 without 710: next target is specialCond/ougiAwakening membership consumer.')
    else:
        print('- Re-test Kamui/UJ once; no decisive 708/710 event was captured.')
else:
    print('- No extended condition successfully resolved/applied. Do not patch awakening/UJ yet; inspect COND_GET/EVT121_SELF first.')
