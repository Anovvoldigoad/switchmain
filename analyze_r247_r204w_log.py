#!/usr/bin/env python3
import sys
from pathlib import Path

if len(sys.argv) != 2:
    print('usage: analyze_r247_r204w_log.py <uzuy_log.txt>')
    sys.exit(2)
lines = Path(sys.argv[1]).read_text(errors='replace').splitlines()

def pick(token):
    return [x for x in lines if token in x]

ready = pick('[NSC:R247] READY')
capture = pick('[NSC:R247] TARGET_REGISTRY_CAPTURE')
states = pick('[NSC:R247] STATE_CALL')
target = [x for x in states if ' target=1 ' in x]

def target_state(name, callback=None, phase=None):
    out=[]
    for x in target:
        if f'state_name={name}' not in x: continue
        if callback and f'callback={callback}' not in x: continue
        if phase and f'phase={phase}' not in x: continue
        out.append(x)
    return out

load_update = target_state('Load','update')
create = target_state('Create')
wait = target_state('Wait')
wait_update = target_state('Wait','update')
select = target_state('Select')

print(f'R247_READY={len(ready)}')
print(f'TARGET_REGISTRY_CAPTURE={len(capture)}')
print(f'STATE_CALL_TOTAL={len(states)}')
print(f'TARGET_STATE_CALL_TOTAL={len(target)}')
print(f'TARGET_LOAD_UPDATE={len(load_update)}')
print(f'TARGET_CREATE={len(create)}')
print(f'TARGET_WAIT={len(wait)}')
print(f'TARGET_WAIT_UPDATE={len(wait_update)}')
print(f'TARGET_SELECT={len(select)}')

if not ready:
    decision='INVALID_RUN_R247_NOT_INSTALLED'
elif not capture:
    decision='TARGET_REGISTRY_NOT_CAPTURED'
elif not target:
    decision='TARGET_STATE_OBJECT_NOT_IDENTIFIED'
elif wait_update:
    decision='WAIT_STATE_UPDATE_REACHED_TRACE_WAIT_CONSUMER_NEXT'
elif wait:
    decision='WAIT_STATE_ENTERED_BUT_UPDATE_NOT_OBSERVED'
elif select:
    decision='SELECT_STATE_REACHED_WITHOUT_WAIT_UPDATE_REVIEW_TRANSITION_ORDER'
elif create:
    decision='CREATE_STATE_REACHED_BEFORE_WAIT_REVIEW_CREATE_TRANSITION'
elif load_update:
    decision='LOAD_UPDATE_REACHED_BUT_NO_DOWNSTREAM_STATE_DISPATCH'
else:
    decision='TARGET_STATE_IDENTIFIED_WITHOUT_LOAD_UPDATE_REVIEW_ORDER'
print('DECISION='+decision)

print('\n--- TARGET REGISTRY CAPTURE ---')
for x in capture[:20]: print(x)
print('\n--- TARGET STATE CALLS ---')
for x in target[:200]: print(x)
