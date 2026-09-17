#!/usr/bin/env python3
"""Quick counter for P45A Uzuy logs."""
import sys
from collections import Counter

markers = [
    "READY",
    "NORMAL_OUGI",
    "SPECIAL_OUGI_FINISH",
    "OUGI_FINISH_CREATE",
    "OUGI_CORE",
    "OUGI_CALLER",
    "EVT13_AWAKE",
    "CTRL14_SHADOW",
    "EVT236",
]

def main(path):
    c = Counter()
    with open(path, "r", errors="replace") as f:
        for line in f:
            for m in markers:
                if m in line:
                    c[m] += 1
    print("=== P45A log counts ===")
    for m in markers:
        print(f"  {m:24s} {c[m]}")
    if c["READY"] == 0:
        print("\nWARNING: no READY line")
    if c["NORMAL_OUGI"] == 0 and c["SPECIAL_OUGI_FINISH"] == 0:
        print("WARNING: neither combat OUGI handler fired")
    print("\nDecision hints:")
    print(f"  NORMAL_OUGI={c['NORMAL_OUGI']}  SPECIAL_OUGI_FINISH={c['SPECIAL_OUGI_FINISH']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyze_p45a_log.py uzuy_log.txt")
        sys.exit(1)
    main(sys.argv[1])
