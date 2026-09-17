#!/usr/bin/env python3
import re, sys, collections
from pathlib import Path

def main(path):
    text = Path(path).read_text(errors='replace')
    markers = re.findall(r'\[NSC:P43A\] (\w+)', text)
    c = collections.Counter(markers)
    print('=== P43A marker counts ===')
    for k,v in c.most_common():
        print(f'  {k}: {v}')
    for k in ['READY','OUGI_CORE','OUGI_CALLER','EVT13_AWAKE','CTRL14_SHADOW','EVT236']:
        print(f'{k}: {c.get(k,0)}')
    print('=== OUGI_CORE by char ===')
    chars = re.findall(r'OUGI_CORE[^\\n]*char=(\d+)', text)
    print(collections.Counter(chars))
    print('=== OUGI_CALLER by char ===')
    chars = re.findall(r'OUGI_CALLER[^\\n]*char=(\d+)', text)
    print(collections.Counter(chars))
    for r in re.findall(r'\[NSC:P43A\] READY.*', text)[:1]:
        print('READY:', r[:280])

if __name__ == '__main__':
    if len(sys.argv)<2:
        print('usage: analyze_p43a_log.py uzuy_log.txt'); sys.exit(1)
    main(sys.argv[1])
