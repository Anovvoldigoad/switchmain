#!/usr/bin/env python3
import re, sys
from pathlib import Path

if len(sys.argv) != 2:
    print('usage: analyze_r245g_log.py <uzuy_log.txt>'); sys.exit(2)
text = Path(sys.argv[1]).read_text(errors='replace')
lines = text.splitlines()

def select(tag): return [x for x in lines if tag in x]
ready = select('[NSC:R245G] READY')
enters = select('[NSC:R245G] GATE_ENTER')
exits = select('[NSC:R245G] GATE_EXIT')
regs = select('[NSC:R245G] GATE_REGISTRY_PROCESS')
alts = select('[NSC:R245G] GATE_ALT_READY')
mtob_lookup = [x for x in lines if '[NSC:R204J] RESOURCE_LOOKUP' in x and 'mtobcharsel.xfbin' in x]
mtob_ready = [x for x in lines if '[NSC:R204J] OWNER_READY' in x and 'mtobcharsel.xfbin' in x and 'result=1' in x]

print(f'R245G_READY={len(ready)}')
print(f'MTOB_OWNER_READY1={len(mtob_ready)}')
print(f'GATE_ENTER={len(enters)}')
print(f'GATE_REGISTRY_PROCESS={len(regs)}')
print(f'GATE_ALT_READY={len(alts)}')
print(f'GATE_EXIT={len(exits)}')
print(f'MTOB_RESOURCE_LOOKUP={len(mtob_lookup)}')

matched = [x for x in enters if 'target_match=1' in x]
advanced = [x for x in exits if 'advanced=1' in x]
zero_regs = [x for x in regs if 'result=0' in x]
alt_zero = [x for x in alts if 'result=0' in x]

if not ready:
    decision='INVALID_RUN_R245G_NOT_INSTALLED'
elif mtob_ready and not enters:
    decision='UPSTREAM_GATE_NOT_CALLED_AFTER_TARGET_READY'
elif enters and not matched:
    decision='RECOVERED_GATE_ACTIVE_BUT_TARGET_REGISTRY_NOT_OWNED_BY_OBSERVED_INSTANCE'
elif advanced and not mtob_lookup:
    decision='STATE_GATE_PASS_CONSUMER_DISPATCH_STILL_ABSENT'
elif advanced and mtob_lookup:
    decision='STATE_GATE_PASS_RESOURCE_CONSUMPTION_REACHED'
elif matched and zero_regs:
    decision='STATE_GATE_REGISTRY_READINESS_FAILURE'
elif matched and alt_zero:
    decision='STATE_GATE_ALT_OWNER_STATE_FAILURE'
elif matched:
    decision='STATE_GATE_DID_NOT_ADVANCE_REVIEW_ORDERED_GATE_EVENTS'
else:
    decision='INSUFFICIENT_TARGET_WINDOW'
print('DECISION='+decision)

print('\n--- TARGET-MATCH GATE ENTERS ---')
for x in matched[:20]: print(x)
print('\n--- GATE REGISTRY RESULTS ---')
for x in regs[:80]: print(x)
print('\n--- ALT READY ---')
for x in alts[:40]: print(x)
print('\n--- GATE EXITS ---')
for x in exits[:40]: print(x)
print('\n--- MTOB RESOURCE LOOKUP ---')
for x in mtob_lookup[:40]: print(x)
