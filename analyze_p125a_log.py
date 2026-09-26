#!/usr/bin/env python3
import re,sys
p=sys.argv[1] if len(sys.argv)>1 else 'uzuy_log.txt'
s=open(p,errors='ignore').read().splitlines()
keys=('P124A] GATE','P124A] AFTER_ACTOR','P124A] AFTER_PEER','P124A] TYPE9_ZERO','P125A] POST_OUTER','P125A] CLEANUP','requested=710','code=710','index=710')
rows=[x for x in s if any(k in x for k in keys)]
for x in rows: print(x)
print('\n--- P125 decision ---')
has=lambda k:any(k in x for x in rows)
if not has('P124A] GATE'):
 print('NO_GATE: custom attempt did not hit focused bucket5 gate.')
elif not has('P124A] AFTER_ACTOR'):
 print('BLOCKER=ACTOR_C48: gate bridged/reached but actor C48 did not pass.')
elif not has('P124A] AFTER_PEER'):
 print('BLOCKER=PEER_C48: actor C48 passed; peer C48 did not.')
elif not has('P124A] TYPE9_ZERO'):
 print('BLOCKER=TYPE9_OR_BRANCH: both C48 passed but zero-type9 branch not reached.')
elif not has('P125A] POST_OUTER'):
 print('BLOCKER=PAIRING_77C514_77C5E8: type9 zero reached, outer setup call not completed.')
else:
 post=[x for x in rows if 'P125A] POST_OUTER' in x]
 if any(re.search(r' ret=1 .*session_latch=1',x) for x in post):
  print('OUTER_SETUP=SUCCESS: native 7EF098 returned success and session latch armed.')
 else:
  print('OUTER_SETUP=REACHED_BUT_FAILED: inspect POST_OUTER ret.')
clean=[x for x in rows if 'P125A] CLEANUP' in x]
if clean:
 print('CLEANUP_LAST:',clean[-1].split('DebugString:17: ')[-1])
 if 'bridge=1' in clean[-1]: print('P107_ENDPOINT_FALLBACK=FIRED_AFTER_QUALIFIED_SESSION')
 elif 'session=1' in clean[-1] and 'mature=0' in clean[-1]: print('SESSION_EXISTS_BUT_CONTEXT_NOT_MATURE: do NOT force137.')
 elif 'session=0' in clean[-1]: print('NO_SESSION_AT_CLEANUP: P107 direct137 remains unsafe.')
print('NATIVE_710_SEEN=', has('requested=710') or has('code=710') or has('index=710'))
