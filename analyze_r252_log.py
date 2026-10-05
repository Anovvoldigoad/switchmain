#!/usr/bin/env python3
import re,sys
from pathlib import Path
if len(sys.argv)!=2:
    print('usage: analyze_r252_log.py <uzuy_log>'); sys.exit(2)
s=Path(sys.argv[1]).read_text(errors='replace')
ready=re.findall(r'\[NSC:R252\] WAIT_READY_GATE .*?result=(\d+)',s)
secondary=re.findall(r'\[NSC:R252\] WAIT_SECONDARY_GATE .*?result=(\d+)',s)
consume=re.findall(r'\[NSC:R252\] WAIT_CONSUME ',s)
children=re.findall(r'\[NSC:R252\] WAIT_CHILD .*?idx=(\d+) .*?e0=(\d+) e4=(\d+)',s)
print('R252_READY_MARKER=', '[NSC:R252] READY installed=1' in s)
print('WAIT_READY_CALLS=',len(ready),'READY_NONZERO=',sum(x!='0' for x in ready))
print('WAIT_SECONDARY_CALLS=',len(secondary),'SECONDARY_NONZERO=',sum(x!='0' for x in secondary))
print('WAIT_CONSUME_CALLS=',len(consume))
print('WAIT_CHILD_SAMPLES=',len(children))
if ready and all(x=='0' for x in ready): decision='WAIT_CHILD_READY_GATE_BLOCKER'
elif any(x!='0' for x in ready) and secondary and all(x=='0' for x in secondary): decision='WAIT_SECONDARY_GATE_BLOCKER'
elif consume: decision='WAIT_CONSUMER_REACHED_TRACE_POST_CONSUMER'
elif not ready: decision='WAIT_UPDATE_CHILD_GATE_NOT_REACHED_OR_EMPTY_VECTOR'
else: decision='REVIEW_MIXED_RESULTS'
print('R252_DECISION='+decision)
