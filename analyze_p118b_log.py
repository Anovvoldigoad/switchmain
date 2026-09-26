#!/usr/bin/env python3
import re,sys,collections
from pathlib import Path
if len(sys.argv)<2:
    raise SystemExit('usage: analyze_p118b_log.py uzuy_log.txt')
lines=Path(sys.argv[1]).read_text(errors='ignore').splitlines()
ready=[x for x in lines if '[NSC:P118B] READY' in x]
print('READY_LINES',len(ready),'PROBE_OK',sum('probe_ok=1' in x for x in ready))
if not ready or not any('probe_ok=1' in x for x in ready):
    raise SystemExit('P118B READY probe_ok=1 not found')
cur_re=re.compile(r"\[NSC:P118B\] CURSOR n=(\d+) actor=(\S+) actor_valid=(\d+) side=(\d+) char=(\d+) action=(\d+) cursor=(\d+) ptr_idx=(-?\d+) cursor_ptr_match=(\d+) event_ptr_match=(\d+) raw=(\d+).*?name='([^']*)'")
tab_re=re.compile(r"\[NSC:P118B\] TABLE n=(\d+) actor=(\S+) cursor=(\d+) count=(\d+) end_delta=(-?\d+).*?ga8=(\d+) gaa=(\d+) gac=(\d+)")
rec_re=re.compile(r"\[NSC:P118B\] REC n=(\d+) actor=(\S+) center=(\d+) d=(-?\d+) idx=(-?\d+) raw=(\d+).*?name='([^']*)'")
cur=[]; tabs={}; rec=[]
for l in lines:
    m=cur_re.search(l)
    if m:
        cur.append(dict(n=int(m[1]),actor=m[2],valid=int(m[3]),side=int(m[4]),char=int(m[5]),action=int(m[6]),cursor=int(m[7]),ptr_idx=int(m[8]),cm=int(m[9]),em=int(m[10]),raw=int(m[11]),name=m[12]))
    m=tab_re.search(l)
    if m:
        tabs[int(m[1])] = dict(actor=m[2],cursor=int(m[3]),count=int(m[4]),end=int(m[5]),ga8=int(m[6]),gaa=int(m[7]),gac=int(m[8]))
    m=rec_re.search(l)
    if m:
        rec.append(dict(n=int(m[1]),actor=m[2],center=int(m[3]),d=int(m[4]),idx=int(m[5]),raw=int(m[6]),name=m[7]))
print('CURSOR_ROWS',len(cur),'TABLE_ROWS',len(tabs),'REC_ROWS',len(rec))
focus=[x for x in cur if 700 <= x['action'] <= 740]
by=collections.defaultdict(list)
for x in focus: by[(x['char'],x['actor'])].append(x)
for (ch,actor),rows in sorted(by.items(), key=lambda kv:min(x['n'] for x in kv[1])):
    print(f'\nCHAR={ch} ACTOR={actor} FOCUSED_ROWS={len(rows)}')
    for x in rows:
        tb=tabs.get(x['n'],{})
        rr=[r for r in rec if r['actor']==actor and r['center']==x['cursor']]
        t10=[r for r in rr if (r['raw'] & ~1)==10]
        near=min(t10,key=lambda r:abs(r['d'])) if t10 else None
        print(' CURSOR',x['cursor'],'PTR_IDX',x['ptr_idx'],'MATCH',x['cm'],'EVENT_MATCH',x['em'],
              'COUNT',tb.get('count'),'END_DELTA',tb.get('end'),'RAW',x['raw'],'NAME',repr(x['name']))
        if near:
            print('  NEAREST_TYPE10_11 d=',near['d'],'idx=',near['idx'],'raw=',near['raw'],'name=',repr(near['name']))
        else:
            print('  TYPE10_11_IN_DUMP=NONE (not logical-block absence proof)')
        if rr:
            print('  DUMP_RANGE',min(r['idx'] for r in rr),'..',max(r['idx'] for r in rr),'ROWS',len(rr))
    if any(x['cm']!=1 or x['em']!=1 for x in rows):
        print(' VERDICT=CURSOR_OR_POINTER_IDENTITY_MISMATCH__AUDIT_INSTRUMENTATION_OR_NATIVE_STATE')
    elif any(tabs.get(x['n'],{}).get('end') in (0,1,2) for x in rows):
        print(' FACT=CURSOR_IS_AT_OR_VERY_NEAR_GLOBAL_TABLE_END')
    else:
        print(' FACT=CURSOR_POINTER_IDENTITY_CONSISTENT')
print('\nNOTE: names/record neighborhoods are evidence for data-family comparison only; they do not prove logical action-block boundaries.')
