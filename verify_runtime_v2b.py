#!/usr/bin/env python3
from pathlib import Path
import re, struct, sys
try:
    import lz4.block
except Exception:
    lz4=None

root=Path(__file__).resolve().parent
rt=(root/'overlay/source/program/nsc_runtime_v2.cpp').read_text()
h=(root/'overlay/source/program/nsc_runtime_v2.hpp').read_text()
bridge=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
prep=(root/'prepare_exlaunch.sh').read_text()
wf=(root/'.github/workflows/build-runtime-v2b.yml').read_text()


def fn_body(src,name):
    m=re.search(rf'\b(?:bool|void)\s+{re.escape(name)}\s*\([^)]*\)\s*\{{',src)
    if not m: return ''
    i=m.end(); depth=1; j=i
    while j<len(src) and depth:
        if src[j]=='{': depth+=1
        elif src[j]=='}': depth-=1
        j+=1
    return src[m.start():j]

event=fn_body(bridge,'InstallEvent236Dispatcher')
play=fn_body(bridge,'InstallPlayActionProbe')
setter=fn_body(bridge,'InstallP57CentralSetterTrace')

checks={
 'seven_anchors': len(re.findall(r'\{Anchor::[A-Za-z0-9_]+\s*,\s*"[A-Z0-9_]+"',rt))==7,
 'resolver_accessor': 'bool GetResolvedOffset(Anchor anchor' in rt and 'g_resolver_ready' in rt,
 'fail_closed_ambiguous': 'if (hits > 1) return 0' in rt,
 'publish_after_scan': 'g_resolver_ready = true;' in rt,
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallP128AStaticPreciseGateCaveProof();'),
 'bridge_has_runtime_header': '#include "nsc_runtime_v2.hpp"' in bridge,
 'event_dynamic': 'Anchor::Event236' in event and 'InstallAtOffset(off)' in event and 'kEvent236Offset' not in event,
 'play_dynamic': 'Anchor::PlayAction' in play and 'InstallAtOffset(off)' in play and 'kPlayActionProbeOffset' not in play,
 'setter_dynamic': 'Anchor::CentralSetter' in setter and 'InstallAtOffset(off)' in setter and 'kCentralActionSetterOffset' not in setter,
 'event_fail_closed': 'resolver_unavailable' in event and 'return false;' in event,
 'play_fail_closed': 'resolver_unavailable' in play and 'return false;' in play,
 'setter_fail_closed': 'resolver_unavailable' in setter and 'return false;' in setter,
 'three_hook_markers': all(x in bridge for x in ('HOOK name=EVENT236 source=resolver','HOOK name=PLAY_ACTION source=resolver','HOOK name=CENTRAL_SETTER source=resolver')),
 'v2b_ready_marker': '[NSC:V2B] READY' in rt and 'migrated_hook_entries=3' in rt and 'no_offset_fallback=1' in rt,
 'coexists_p128': 'InstallP128AStaticPreciseGateCaveProof();' in main,
 'copies_runtime': 'nsc_runtime_v2.cpp' in prep and 'nsc_runtime_v2.hpp' in prep,
 'workflow_only_v2b': len(list((root/'.github/workflows').glob('*.yml')))==1 and 'NSC-RUNTIME-V2B-dynamic-hook-entry-migration' in wf,
 'workflow_verifier': 'python3 verify_runtime_v2b.py' in wf,
 'logger_include_order': '#include "lib.hpp"' in rt and rt.index('#include "lib.hpp"') < rt.index('#include <program/loggers.hpp>'),
 'no_char281_in_runtime': '281' not in rt,
}

for k,v in checks.items(): print(k,'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)

# Offline signature uniqueness remains mandatory against pristine restore and paired P128 main.
def parse_arr(name):
    m=re.search(rf'{re.escape(name)}\[\]\s*=\s*\{{([^}}]+)\}};',rt,re.S)
    if not m: raise RuntimeError('missing '+name)
    return [int(x,16) for x in re.findall(r'0x[0-9A-Fa-f]+',m.group(1))]

def decode_text(path):
    b=path.read_bytes()
    if b[:4]!=b'NSO0': raise RuntimeError('not NSO0 '+str(path))
    u=lambda o: struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c); fo=u(0x10); va=u(0x14); size=u(0x18); csz=u(0x60)
    blob=b[fo:fo+(csz if flags&1 else size)]
    if flags&1:
        if lz4 is None: return va,None
        blob=lz4.block.decompress(blob,uncompressed_size=size)
    return va,blob

specs=[
 ('CHARACODE_GETTER','kCharVal','kCharMask',0x3F4150),
 ('CPK_BIND','kCpkVal','kCpkMask',0x473190),
 ('EVENT236','kEvent236Val','kEvent236Mask',0x816300),
 ('PLAY_ACTION','kPlayVal','kPlayMask',0x766B8C),
 ('CENTRAL_SETTER','kSetterVal','kSetterMask',0x766320),
 ('UJ_SESSION_OUTER','kOuterVal','kOuterMask',0x7EF098),
 ('STATE137_CONTROLLER','kState137Val','kState137Mask',0x7E6EA8),
]

def scan_unique(text,va,vals,masks):
    pivot=next((i for i,m in enumerate(masks) if m==0xffffffff),0)
    pat=struct.pack('<I',vals[pivot]) if masks[pivot]==0xffffffff else None
    cand=[]
    if pat is not None:
        pos=0
        while True:
            j=text.find(pat,pos)
            if j<0: break
            start=j-pivot*4; pos=j+1
            if start<0 or start%4 or start+4*len(vals)>len(text): continue
            ok=True
            for i,(v,m) in enumerate(zip(vals,masks)):
                w=struct.unpack_from('<I',text,start+4*i)[0]
                if (w&m)!=(v&m): ok=False; break
            if ok: cand.append(va+start)
    return cand

for label in ('restore','paired'):
    p=root/label/'atmosphere/contents/0100FA10190A0000/exefs/main'
    va,text=decode_text(p)
    if text is None:
        print('offline_signature_check',label,'SKIP(no lz4)')
        continue
    for name,vn,mn,expected in specs:
        vals=parse_arr(vn); masks=parse_arr(mn)
        hits=scan_unique(text,va,vals,masks)
        ok=(len(hits)==1 and hits[0]==expected)
        print(f'offline_{label}_{name}', 'PASS' if ok else 'FAIL', 'hits='+','.join(hex(x) for x in hits[:4]))
        if not ok: sys.exit(1)

# Paired main must remain byte-identical to V2A/P128 main; V2B changes subsdk9 source only.
import hashlib
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
print('paired_main_sha256',sha(paired))
print('restore_main_sha256',sha(restore))
if sha(paired)!='904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff':
    print('paired_main_expected FAIL'); sys.exit(1)
if sha(restore)!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9':
    print('restore_main_expected FAIL'); sys.exit(1)
print('paired_main_expected PASS')
print('restore_main_expected PASS')
print('NSC_RUNTIME_V2B_SOURCE_VERIFY=PASS')
