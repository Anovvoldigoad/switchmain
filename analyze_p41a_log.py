#!/usr/bin/env python3
"""Quick P41A Uzuy log summary."""
import re, sys, collections
from pathlib import Path

def main(path):
    text = Path(path).read_text(errors='replace')
    markers = re.findall(r'\[NSC:P41A\] (\w+)', text)
    c = collections.Counter(markers)
    print('=== P41A marker counts ===')
    for k,v in c.most_common():
        print(f'  {k}: {v}')
    ready = re.findall(r'\[NSC:P41A\] READY.*', text)
    print('\nREADY lines:', len(ready))
    for r in ready[:2]:
        print(' ', r[:200])
    print('\nEVT13_AWAKE:', c.get('EVT13_AWAKE', 0))
    print('OUGI_CORE:', c.get('OUGI_CORE', 0))
    print('OUGI_CALLER:', c.get('OUGI_CALLER', 0))
    print('CTRL_DUMP:', c.get('CTRL_DUMP', 0))
    print('CTRL14_DIRECT:', c.get('CTRL14_DIRECT', 0))
    dumps = re.findall(r'\[NSC:P41A\] CTRL_DUMP n=(\d+) base\+(0x[0-9a-fA-F]+): (.+)', text)
    if dumps:
        print('\n=== first CTRL_DUMP rows ===')
        for n, base, vals in dumps[:20]:
            print(f'  n={n} {base}: {vals}')
    wrote = re.findall(r'CTRL14_DIRECT.*?old=(-?\d+) wrote=(\d)', text)
    if wrote:
        wc = collections.Counter((o,w) for o,w in wrote)
        print('\n=== CTRL14 old/wrote pairs (top) ===')
        for (o,w), cnt in wc.most_common(12):
            print(f'  old={o} wrote={w}: {cnt}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: analyze_p41a_log.py uzuy_log.txt')
        sys.exit(1)
    main(sys.argv[1])
