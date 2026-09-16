#!/usr/bin/env python3
import re,sys,collections
p=sys.argv[1]
lines=open(p,encoding="utf-8",errors="replace").read().splitlines()
rows=[x for x in lines if "[NSC:P39A]" in x]
print("P39A markers=",len(rows))
for key in ("READY","VIS_SHADOW","CTRL14_DIRECT","STAGE_HANDLE","FIX_CHAR","POST_STAGE","EVT235_SHOW","EVT236","FILE_OPEN","PROCESS"):
    print(f"{key}=",sum(f"[NSC:P39A] {key}" in x for x in rows))
print("fingerprint_FAIL=",sum("fingerprint FAIL" in x for x in rows))
print("file_open_result0=",sum("FILE_OPEN" in x and "result=0" in x for x in rows))
print("process_status5=",sum("PROCESS" in x and "status=5" in x for x in rows))
print("process_readerr1=",sum("PROCESS" in x and "readerr=1" in x for x in rows))
rx_evt=re.compile(r"EVT236 actor=(\S+) side=(\d+) char=(\d+) op=(-?\d+) p2=(-?\d+) p3=(-?\d+)")
rx_ctl=re.compile(r"CTRL14_DIRECT actor=(\S+) target=(\S+) side=(\d+) char=(\d+) p2=(-?\d+) p3=(-?\d+) rel=([0-9a-fA-F]+) old=(-?\d+) wrote=(\d+)")
ops=collections.Counter(); actors=collections.Counter(); ctl=collections.Counter(); olds=collections.Counter()
for x in rows:
    m=rx_evt.search(x)
    if m:
        a,side,ch,op,p2,p3=m.groups()
        actors[a]+=1; ops[(int(op),int(p2),int(p3))]+=1
    c=rx_ctl.search(x)
    if c:
        a,t,side,ch,p2,p3,rel,old,wrote=c.groups()
        ctl[(int(p2),int(p3),int(rel,16),int(wrote))]+=1
        olds[(int(p3),int(old),int(wrote))]+=1
print("actors=",dict(actors))
print("control_tuples=")
for k,v in sorted(ctl.items()): print(" ",k,v)
print("control_old_values=")
for k,v in sorted(olds.items()): print(" ",k,v)
print("top_op_tuples=")
for k,v in ops.most_common(40): print(" ",k,v)
