#!/usr/bin/env python3
import re,sys,collections
from pathlib import Path
if len(sys.argv)<2:
    raise SystemExit('usage: analyze_p119a_log.py uzuy_log.txt')
lines=Path(sys.argv[1]).read_text(errors='ignore').splitlines()
ready=[x for x in lines if '[NSC:P119A] READY' in x]
print('READY_LINES',len(ready),'PROBE_OK',sum('probe_ok=1' in x for x in ready))
if not ready or not any('probe_ok=1' in x for x in ready):
    raise SystemExit('P119A READY probe_ok=1 not found')
link_re=re.compile(r"\[NSC:P119A\] LINK n=(\d+) pair_ok=(\d+) atk=(\S+) atk_side=(\d+) atk_char=(\d+) atk_action=(\d+) atk_sem=(\d+) atk_e44=([0-9a-fA-F]+) atk_e94=(\d+) atk_e98=(\d+) atk_e9c=(\d+) atk_ea4=([0-9a-fA-F]+) atk_trace=(\d+) trace_gap=(\d+)")
dmg_re=re.compile(r"\[NSC:P119A\] DAMAGE n=(\d+) victim=(\S+) vic_side=(\d+) vic_char=(\d+) vic_action=(\d+) cursor=(\d+) ptr_idx=(-?\d+) raw=(\d+) gate10=(\d+) count=(\d+) end_delta=(-?\d+) name='([^']*)'")
links={}; dmgs={}
for l in lines:
    m=link_re.search(l)
    if m:
        links[int(m[1])] = dict(n=int(m[1]),pair=int(m[2]),atk=m[3],side=int(m[4]),char=int(m[5]),action=int(m[6]),sem=int(m[7]),e44=int(m[8],16),e94=int(m[9]),e98=int(m[10]),e9c=int(m[11]),ea4=int(m[12],16),trace=int(m[13]),gap=int(m[14]))
    m=dmg_re.search(l)
    if m:
        dmgs[int(m[1])] = dict(n=int(m[1]),victim=m[2],side=int(m[3]),char=int(m[4]),action=int(m[5]),cursor=int(m[6]),ptr_idx=int(m[7]),raw=int(m[8]),gate=int(m[9]),count=int(m[10]),end=int(m[11]),name=m[12])
ids=sorted(set(links)&set(dmgs))
print('LINK_ROWS',len(links),'DAMAGE_ROWS',len(dmgs),'PAIRED_ROWS',len(ids))
if not ids:
    raise SystemExit('No paired P119A LINK/DAMAGE rows found')
rows=[]
for n in ids:
    a=links[n]; d=dmgs[n]
    row={**a, **{f'v_{k}':v for k,v in d.items() if k!='n'}}
    rows.append(row)
    print(f"n={n} ATK char={a['char']} actor={a['atk']} action={a['action']} sem={a['sem']} ea4=0x{a['ea4']:x} e94={a['e94']} e98={a['e98']} e9c={a['e9c']} gap={a['gap']} -> VIC char={d['char']} actor={d['victim']} action={d['action']} cursor={d['cursor']} ptr_idx={d['ptr_idx']} raw={d['raw']} gate10={d['gate']} count={d['count']} end={d['end']} name={d['name']!r}")
    if d['cursor'] != d['ptr_idx']:
        print('  WARNING=CURSOR_PTR_MISMATCH')
    if a['gap']>16:
        print('  WARNING=STALE_ATTACKER_PAIR')
by=collections.defaultdict(list)
for r in rows:
    by[(r['char'],r['atk'])].append(r)
for (ch,actor),rr in sorted(by.items(), key=lambda kv:min(x['n'] for x in kv[1])):
    print(f"\nATTACKER char={ch} actor={actor} rows={len(rr)}")
    gates=[x for x in rr if x['v_gate']==1]
    names=[]
    for x in rr:
        nm=x['v_name']
        if nm not in names: names.append(nm)
    print(' DAMAGE_NAMES',names)
    print(' GATE10_ROWS',len(gates))
    print(' EA4_RANGE',hex(min(x['ea4'] for x in rr)),'..',hex(max(x['ea4'] for x in rr)))
    if gates:
        print(' FACT=CAPTURED_CINEMATIC_DAMAGE_GATE_INPUT')
    else:
        print(' FACT=NO_CINEMATIC_GATE_INPUT_IN_CAPTURED_PAIRED_DAMAGE')
print('\nINTERPRETATION_RULES:')
print('1) Treat victim cursor/name/raw as victim-owned damage state, not attacker event-stream ownership.')
print('2) A gate10=1 row proves a cinematic-family damage record reached bucket5 for that paired attacker snapshot.')
print('3) No gate10 row is evidence only for the captured paired window; combine with the full UJ timeline/source events before patching.')
print('4) Do not infer that 707->708 is erroneous from these rows; P97 already falsified suppression as a fix.')
