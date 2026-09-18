#!/usr/bin/env python3
import sys, re
from collections import Counter, defaultdict

def main(path):
    markers = Counter()
    plays, members, gates = [], [], []
    with open(path, errors="replace") as f:
        for line in f:
            if "P48A" not in line: continue
            for m in ["READY","PLAY_ACTION","MEMBER8800D0","MEMBER880150","GATE769A4C","fingerprint FAIL"]:
                if m in line: markers[m]+=1
            m=re.search(r"PLAY_ACTION actor=(0x[0-9a-f]+) index=(-?\d+) ret=(-?\d+).*f3668=(\d+)", line)
            if m: plays.append((int(m.group(2)), int(m.group(3)), int(m.group(4))))
            m=re.search(r"MEMBER8800D0 x0=(0x[0-9a-f]+) ret=(0x[0-9a-f]+|0) n=(\d+)", line)
            if m: members.append(("D0", m.group(1), m.group(2)))
            m=re.search(r"MEMBER880150 x0=(0x[0-9a-f]+) x1=(0x[0-9a-f]+) ret=(0x[0-9a-f]+|0)", line)
            if m: members.append(("150", m.group(1), m.group(3)))
            m=re.search(r"GATE769A4C actor=(0x[0-9a-f]+) ret=(0x[0-9a-f]+|0) n=(\d+) f3668=(\d+) f4708=(\d+)", line)
            if m: gates.append((m.group(1), m.group(2), int(m.group(4)), int(m.group(5))))
    print("markers", dict(markers))
    print("\nPLAY cinematic indices:")
    for idx,ret,ch in plays:
        if idx in (700,707,708,710,711,712,713,714,740) or idx>=700:
            print(f"  idx={idx} ret={ret} char={ch}")
    print("\nMEMBER sample (first 20):")
    for x in members[:20]: print(" ", x)
    print("MEMBER ret nonzero:", sum(1 for _,_,r in members if r not in ("0","0x0")))
    print("\nGATE769:")
    for g in gates[:20]: print(" ", g)
    print("GATE with char 281:", [g for g in gates if g[2]==281])
    print("GATE with nonzero ret:", [g for g in gates if g[1] not in ("0","0x0")])

if __name__=="__main__":
    if len(sys.argv)!=2: print("Usage: analyze_p48a_log.py log.txt"); sys.exit(1)
    main(sys.argv[1])
