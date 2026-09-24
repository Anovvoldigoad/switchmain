#!/usr/bin/env python3
import re, sys
from pathlib import Path
if len(sys.argv)<2:
    raise SystemExit('usage: python3 analyze_p93a_log.py uzuy_log.txt')
lines=Path(sys.argv[1]).read_text(errors='replace').splitlines()
core=[x for x in lines if '[NSC:P93A] CORE' in x]
print('P93_CORE_RECORDS',len(core))
# High-value timeline only: 700..740 action or E94/E98 UJ states.
rx=re.compile(r'tag=(\S+).*char=(\d+).*caller_off=(0x[0-9a-fA-F]+).*code=(-?\d+).*action=(\d+).*e90=([0-9a-fA-F]+).*e94=([0-9a-fA-F]+).*e98=([0-9a-fA-F]+).*e9c=([0-9a-fA-F]+).*ea4=([0-9a-fA-F]+).*bda4=(\d+).*bdc8=(\d+)')
for x in core:
    m=rx.search(x)
    if not m: continue
    tag,cid,caller,code,act,e90,e94,e98,e9c,ea4,bda4,bdc8=m.groups()
    ai=int(act); ci=int(code)
    if 700<=ai<=740 or 700<=ci<=740 or int(e94,16) in range(135,139) or int(e98,16) in range(135,139):
        print(f'char={cid} tag={tag} caller={caller} code={code} action={act} e90={e90} e94={e94} e98={e98} e9c={e9c} ea4={ea4} bda4={bda4} bdc8={bdc8}')
