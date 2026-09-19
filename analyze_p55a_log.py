#!/usr/bin/env python3
import sys,re,collections
p=sys.argv[1]
lines=open(p,errors="replace").read().splitlines()
keys=["[NSC:P50A] READY","[NSC:P55A] READY","[NSC:P55A] STATE236","[NSC:P55A] SKILL_WRITE","[NSC:P55A] STATE121","[NSC:P55A] ACTION_ROUTE"]
for k in keys:
    xs=[x for x in lines if k in x]
    print(f"{k}: {len(xs)}")
    for x in xs[:80]: print(x)
a=collections.Counter()
for x in lines:
    if "[NSC:P55A] STATE121" in x or "[NSC:P55A] STATE236" in x:
        m=re.search(r"action=(?:\d+->)?(\d+)",x)
        if m:a[int(m.group(1))]+=1
print("action_counts",dict(a))
