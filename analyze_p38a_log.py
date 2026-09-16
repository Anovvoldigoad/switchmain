#!/usr/bin/env python3
import re,sys,collections
p=sys.argv[1]
lines=open(p,encoding='utf-8',errors='replace').read().splitlines()
rows=[x for x in lines if '[NSC:P38A]' in x]
print('P38A markers=',len(rows))
for key in ('READY','VIS_SHADOW','CTRL14_SHADOW','STAGE_HANDLE','FIX_CHAR','POST_STAGE','EVT235_SHOW','EVT236','FILE_OPEN','PROCESS'):
    print(f'{key}=',sum(f'[NSC:P38A] {key}' in x for x in rows))
print('fingerprint_FAIL=',sum('fingerprint FAIL' in x for x in rows))
print('file_open_result0=',sum('FILE_OPEN' in x and 'result=0' in x for x in rows))
print('process_status5=',sum('PROCESS' in x and 'status=5' in x for x in rows))
print('process_readerr1=',sum('PROCESS' in x and 'readerr=1' in x for x in rows))
rx=re.compile(r'EVT236 actor=(\S+) side=(\d+) char=(\d+) op=(-?\d+) p2=(-?\d+) p3=(-?\d+)')
ops=collections.Counter(); actors=collections.Counter()
for x in rows:
    m=rx.search(x)
    if m:
        a,side,ch,op,p2,p3=m.groups(); actors[a]+=1; ops[(int(op),int(p2),int(p3))]+=1
print('actors=',dict(actors))
print('top_op_tuples=')
for k,v in ops.most_common(30): print(' ',k,v)
