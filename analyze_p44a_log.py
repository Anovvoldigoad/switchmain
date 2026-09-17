#!/usr/bin/env python3
"""Quick counter for P44A Uzuy logs."""
import sys
from collections import Counter

markers = [
    "OUGI_FINISH_CREATE",
    "OUGI_CORE",
    "OUGI_CALLER",
    "EVT13_AWAKE",
    "CTRL14_SHADOW",
    "EVT236",
    "READY",
]

def main(path):
    c = Counter()
    with open(path, "r", errors="replace") as f:
        for line in f:
            for m in markers:
                if m in line:
                    c[m] += 1
    print("=== P44A log counts ===")
    for m in markers:
        print(f"  {m:24s} {c[m]}")
    if c["READY"] == 0:
        print("\nWARNING: no READY line — boot failed or wrong binary")
    if c["OUGI_FINISH_CREATE"] == 0:
        print("WARNING: OUGI_FINISH_CREATE never logged — fingerprint or path issue")
    else:
        print(f"\nOUGI_FINISH_CREATE hit {c['OUGI_FINISH_CREATE']} time(s) (expected small, init-time)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyze_p44a_log.py uzuy_log.txt")
        sys.exit(1)
    main(sys.argv[1])
