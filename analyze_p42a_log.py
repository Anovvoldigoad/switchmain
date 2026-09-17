#!/usr/bin/env python3
import re, sys, collections
from pathlib import Path

def main(path):
    text = Path(path).read_text(errors='replace')
    markers = re.findall(r'\[NSC:P42A\] (\w+)', text)
    c = collections.Counter(markers)
    print('=== P42A marker counts ===')
    for k,v in c.most_common():
        print(f'  {k}: {v}')
    for k in ['READY','CTRL14_SHADOW','OP15_SHADOW','OP17_SHADOW','OP18_SHADOW',
              'OUGI_CALLER','OUGI_CORE','EVT13_AWAKE','EVT121_COND','STAGE_HANDLE']:
        print(f'{k}: {c.get(k,0)}')
    for r in re.findall(r'\[NSC:P42A\] READY.*', text)[:1]:
        print('READY:', r[:240])

if __name__ == '__main__':
    if len(sys.argv)<2:
        print('usage: analyze_p42a_log.py uzuy_log.txt'); sys.exit(1)
    main(sys.argv[1])
