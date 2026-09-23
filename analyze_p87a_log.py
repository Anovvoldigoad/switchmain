#!/usr/bin/env python3
import sys
s=open(sys.argv[1],errors='ignore').read().splitlines()
for k in ('READY','PROD','HELPER','ACTOR_PRED'):
 print(k,sum(f'[NSC:P87A] {k}' in x for x in s))
for x in s:
 if '[NSC:P87A]' in x or '[NSC:P85A] F58' in x: print(x)
