#!/usr/bin/env python3
"""Analyze P53A action routing. No third-party modules required."""
from __future__ import annotations
import argparse,re
from collections import Counter,defaultdict
from pathlib import Path

R=re.compile(r'\[NSC:P53A\] ACTION_ROUTE route=(\S+) actor=(\S+) valid=(\d+) side=(\d+) char=(\d+) index=(-?\d+) ret=(-?\d+) n=(\d+) a2=(-?\d+) pre_action=(\d+) post_action=(\d+)')
T=re.compile(r'^\[\s*([0-9.]+)\]')
READY='[NSC:P53A] READY'

def main():
 ap=argparse.ArgumentParser(description='Summarize P53A XXA -> JUTSU84/UJ routing')
 ap.add_argument('log'); a=ap.parse_args()
 lines=Path(a.log).read_text(errors='replace').splitlines()
 print('P53A_READY='+('YES' if any(READY in x for x in lines) else 'NO'))
 rows=[]
 for line in lines:
  m=R.search(line)
  if not m: continue
  tm=T.match(line)
  rows.append(dict(time=float(tm.group(1)) if tm else -1.0,route=m.group(1),actor=m.group(2),valid=int(m.group(3)),side=int(m.group(4)),char=int(m.group(5)),index=int(m.group(6)),ret=int(m.group(7)),n=int(m.group(8)),a2=int(m.group(9)),pre=int(m.group(10)),post=int(m.group(11))))
 print('ACTION_ROUTE_RECORDS='+str(len(rows)))
 by=defaultdict(list)
 for x in rows: by[x['char']].append(x)
 for char,xs in sorted(by.items()):
  c=Counter(x['route'] for x in xs)
  seq=' -> '.join(f"{x['route']}:{x['index']}" for x in xs)
  print(f'CHAR {char}: JUTSU84={c["JUTSU84"]} SPTYPE930={c["SPTYPE930"]} UJ={c["UJ"]}')
  print('  SEQ '+seq)
 print('\nDECISION_GUIDE')
 print('  Press XXA once with vanilla control, then XXA once with the custom awakened character.')
 print('  Custom shows JUTSU84: command fell back to ordinary XA/jutsu before UJ state entry.')
 print('  Custom shows UJ:700: command promotion succeeded; continue downstream UJ-chain diagnosis.')
 print('  Custom shows SPTYPE930 without UJ:700: special-type route is consuming the command upstream.')
 print('  No custom route record: failure is upstream of PlayAction; capture full log and exact test timing.')
if __name__=='__main__': main()
