#!/usr/bin/env python3
import re,sys
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
s=open(p,'r',errors='ignore').read().splitlines()
f58=[x for x in s if '[NSC:P63A] UJ_F58' in x]
post=[x for x in s if '[NSC:P63A] UJ_POST_GATE' in x]
ctrl=[x for x in s if '[NSC:P63A] UJ_CTRL_GET' in x]
p445=[x for x in s if '[NSC:P59A] PLAY_CALL' in x and 'char=281 ' in x and 'index=445 ' in x]
p700=[x for x in s if '[NSC:P59A] PLAY_CALL' in x and 'char=281 ' in x and 'index=700 ' in x]
print('P63A_F58_CALLS=',len(f58),sep='')
print('P63A_F58_EXACT_ROUTER=',sum('exact_router=1' in x for x in f58),sep='')
print('P63A_POST_GATE_CALLS=',len(post),sep='')
print('P63A_POST_GATE_EXACT_ROUTER=',sum('exact_router=1' in x for x in post),sep='')
for tag in ('PRE0','UJ8_A','SEL40','UJ8_B'):
 print(f'P63A_CTRL_{tag}=',sum(f'tag={tag}' in x for x in ctrl),sep='')
print('CUSTOM_445=',len(p445),sep='')
print('CUSTOM_700=',len(p700),sep='')
# conservative classification only; no guessed root cause
if p700:
 print('P63A_RESULT=CUSTOM_REACHED_UJ700_NO_PATCH')
elif not f58:
 print('P63A_RESULT=UPSTREAM_DIVERGENCE_BEFORE_F58')
elif not any('exact_router=1' in x for x in f58):
 print('P63A_RESULT=F58_NOT_CALLED_FROM_EXPECTED_UJ_ROUTER')
elif any('exact_router=1' in x and 'ret=0' in x for x in f58):
 print('P63A_RESULT=NATIVE_F58_REJECTED_ON_UJ_ROUTER')
elif not any('exact_router=1' in x for x in post):
 print('P63A_RESULT=F58_PASSED_BUT_POST_GATE_NOT_REACHED')
elif any('exact_router=1' in x and 'ret=0' in x for x in post):
 print('P63A_RESULT=POST_F58_HELPER_REJECTED')
elif not any('tag=UJ8_A' in x or 'tag=UJ8_B' in x for x in ctrl):
 print('P63A_RESULT=POST_GATE_PASSED_BUT_SELECTOR8_NOT_REACHED')
else:
 print('P63A_RESULT=ROUTER_REACHED_DOWNSTREAM_CONTROL_CHECKS_BUT_NO_UJ700')
