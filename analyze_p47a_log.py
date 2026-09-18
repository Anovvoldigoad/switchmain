#!/usr/bin/env python3
"""Analyze P47A logs — PLAY_ACTION ret by index."""
import sys, re
from collections import defaultdict, Counter

def main(path):
    by_idx = defaultdict(list)
    markers = Counter()
    with open(path, errors="replace") as f:
        for line in f:
            if "P47A" not in line:
                continue
            for m in ["READY", "PLAY_ACTION", "NORMAL_OUGI", "SPECIAL_OUGI_FINISH"]:
                if m in line:
                    markers[m] += 1
            m = re.search(
                r"PLAY_ACTION actor=(0x[0-9a-f]+) index=(-?\d+) ret=(-?\d+) n=(\d+).*?"
                r"f3668=(\d+) f4708=(\d+) f4712=(\d+) f4740=(\d+) f4756=(\d+) f536=(0x[0-9a-f]+|0)",
                line,
            )
            if m:
                by_idx[int(m.group(2))].append({
                    "actor": m.group(1), "ret": int(m.group(3)), "n": int(m.group(4)),
                    "f3668": m.group(5), "f4708": m.group(6), "f4712": m.group(7),
                    "f4740": m.group(8), "f4756": m.group(9), "f536": m.group(10),
                })
    print("=== markers ===")
    for k, v in markers.most_common():
        print(f"  {k}: {v}")
    print("\n=== PLAY_ACTION by index (ret summary) ===")
    for idx in sorted(by_idx):
        rets = Counter(x["ret"] for x in by_idx[idx])
        print(f"  index={idx:4d}  count={len(by_idx[idx]):3d}  rets={dict(rets)}")
        if idx in (700, 707, 708, 710, 711, 712, 713, 714, 740, 487):
            for x in by_idx[idx][:3]:
                print(f"    actor={x['actor']} ret={x['ret']} "
                      f"f3668={x['f3668']} f4708={x['f4708']} f4712={x['f4712']} "
                      f"f4740={x['f4740']} f4756={x['f4756']} f536={x['f536']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyze_p47a_log.py uzuy_log.txt")
        sys.exit(1)
    main(sys.argv[1])
