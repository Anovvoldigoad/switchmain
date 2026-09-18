#!/usr/bin/env python3
"""Analyze P46A Uzuy logs — PLAY_ACTION index histogram."""
import sys, re
from collections import Counter

def main(path):
    c = Counter()
    play = Counter()
    with open(path, errors="replace") as f:
        for line in f:
            if "P46A" not in line and "NSC:P46A" not in line:
                continue
            for m in ["READY", "PLAY_ACTION", "NORMAL_OUGI", "SPECIAL_OUGI_FINISH",
                      "OUGI_FINISH_CREATE", "CTRL14_SHADOW", "EVT236"]:
                if m in line:
                    c[m] += 1
            m = re.search(r"PLAY_ACTION.*?index=(-?\d+)", line)
            if m:
                play[int(m.group(1))] += 1
    print("=== P46A markers ===")
    for k, v in c.most_common():
        print(f"  {k:24s} {v}")
    print("\n=== PLAY_ACTION index top 40 ===")
    for idx, n in play.most_common(40):
        print(f"  index={idx:4d}  count={n}")
    if c["READY"] == 0:
        print("\nWARNING: no READY")
    if c["PLAY_ACTION"] == 0:
        print("WARNING: no PLAY_ACTION hits")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyze_p46a_log.py uzuy_log.txt")
        sys.exit(1)
    main(sys.argv[1])
