#!/usr/bin/env python3
import re,sys
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
s=open(p,errors='replace').read().splitlines()
bridge=[]; plays=[]
for ln in s:
    if '[NSC:P108A] BRIDGE' in ln: bridge.append(ln)
    if '[NSC:P59A] PLAY_CALL' in ln and ('index=708' in ln or 'index=710' in ln or 'index=711' in ln or 'index=712' in ln or 'index=713' in ln or 'index=740' in ln): plays.append(ln)
print('P108_BRIDGE_COUNT',len(bridge))
for x in bridge: print(x)
print('FOCUSED_PLAY_CALLS',len(plays))
for x in plays: print(x)
print('HAS_MAP136',any('mapped=136' in x for x in bridge))
print('HAS_710',any('index=710' in x for x in plays))
print('HAS_711_PLUS',any(('index=711' in x or 'index=712' in x or 'index=713' in x) for x in plays))
