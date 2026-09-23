#!/usr/bin/env python3
import sys,re
from collections import Counter
if len(sys.argv)!=2: raise SystemExit("usage: python3 analyze_p89a_log.py uzuy_log.txt")
L=open(sys.argv[1],errors="ignore").read().splitlines()
ready=[x for x in L if "[NSC:P89A] READY" in x]
pred=[x for x in L if "[NSC:P89A] ACTOR_PRED" in x]
print("P89A_READY",len(ready)); print("P89A_ACTOR_PRED",len(pred))
rx=re.compile(r"char=(\d+).*bda4=(\d+).*bdc8=(\d+).*native=(\d+).*semantic=(\d+).*member=(\d+).*bridge=(\d+).*out=(\d+)")
C=Counter()
for x in pred:
    m=rx.search(x)
    if m: C[tuple(map(int,m.groups()))]+=1
for k,n in C.most_common(40): print("P89A_MATRIX",n,k)
for key in ("[NSC:P85A] F58","requested=700","index=700","requested=445","index=445"):
    print(key,sum(key in x for x in L))
