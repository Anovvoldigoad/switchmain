#!/usr/bin/env python3
from pathlib import Path
import hashlib, re, struct, sys
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
wf=(root/'.github/workflows/build-runtime-v2c.yml').read_text()

def fn_body(src,name):
    m=re.search(rf'\b(?:bool|void)\s+{re.escape(name)}\s*\([^)]*\)\s*\{{',src)
    if not m:return ''
    i=m.end();depth=1;j=i
    while j<len(src) and depth:
        if src[j]=='{':depth+=1
        elif src[j]=='}':depth-=1
        j+=1
    return src[m.start():j]

event=fn_body(bridge,'InstallEvent236Dispatcher')
play=fn_body(bridge,'InstallPlayActionProbe')
setter=fn_body(bridge,'InstallP57CentralSetterTrace')
cpk=fn_body(bridge,'InstallCpkBridge')
char=fn_body(bridge,'InstallCharacodeGetterDynamic')
p128post=fn_body(bridge,'InstallP128PostOuter')
p77=fn_body(bridge,'InstallP77AAcceptanceProbe')
p50=fn_body(bridge,'InstallP50AConditionCompat')

checks={
 'seven_anchors': len(re.findall(r'\{Anchor::[A-Za-z0-9_]+\s*,\s*"[A-Z0-9_]+"',rt))==7,
 'resolver_accessor': 'bool GetResolvedOffset(Anchor anchor' in rt and 'g_resolver_ready' in rt,
 'uj_post_accessor': 'GetDerivedUjSessionPostOffset' in rt and 'ResolveUjSessionPostUnique' in rt,
 'uj_post_shape': 'prev != 0xAA1703E0u' in rt and 'next != 0xB9405288u' in rt and 'target != outer_off' in rt,
 'fail_closed_ambiguous': 'if (hits > 1) return 0' in rt and 'if (hits > 1) return -1' in rt,
 'main_order': main.index('InstallResolverHookMigrationProbe();') < main.index('InstallP128AStaticPreciseGateCaveProof();'),
 'event_dynamic': 'Anchor::Event236' in event and 'InstallAtOffset(off)' in event,
 'play_dynamic': 'Anchor::PlayAction' in play and 'InstallAtOffset(off)' in play,
 'setter_dynamic': 'Anchor::CentralSetter' in setter and 'InstallAtOffset(off)' in setter,
 'cpk_dynamic': 'Anchor::CpkBind' in cpk and 'InstallAtOffset(off)' in cpk and 'resolver_unavailable' in cpk,
 'char_dynamic': 'Anchor::CharacodeGetter' in char and 'InstallAtOffset(off)' in char and 'resolver_unavailable' in char,
 'p50_char_active': 'InstallCharacodeGetterDynamic()' in p50 and 'installed_trampolines=6' in p50,
 'p77_reclaimed': 'P77UjAcceptanceHook::InstallAtOffset' not in p77 and 'trampoline_reclaimed_for_characode=1' in p77,
 'p128post_dynamic': 'GetDerivedUjSessionPostOffset' in p128post and 'InstallAtOffset(off)' in p128post and 'resolver_unavailable' in p128post,
 'no_cpk_absolute_constant': 'kCpkBindOffset' not in bridge,
 'no_char_absolute_constant': 'kCharacodeGetterOffset' not in bridge,
 'no_p128post_absolute_constant': 'kP128PostOuterOffset' not in bridge,
 'six_hook_markers': all(x in bridge for x in (
    'HOOK name=EVENT236 source=resolver','HOOK name=PLAY_ACTION source=resolver',
    'HOOK name=CENTRAL_SETTER source=resolver','HOOK name=CPK_BIND source=resolver',
    'HOOK name=CHARACODE_GETTER source=resolver','HOOK name=UJ_SESSION_POST source=resolver_derived')),
 'v2c_ready': '[NSC:V2C] READY' in rt and 'migrated_hook_entries=6' in rt and 'no_offset_fallback=1' in rt,
 'coexists_p128': 'InstallP128AStaticPreciseGateCaveProof();' in main,
 'workflow_only_v2c': len(list((root/'.github/workflows').glob('*.yml')))==1 and 'NSC-RUNTIME-V2C-dynamic-core-migration' in wf,
 'workflow_verifier': 'python3 verify_runtime_v2c.py' in wf,
 'logger_include_order': rt.index('#include "lib.hpp"') < rt.index('#include <program/loggers.hpp>'),
 'no_char281_in_runtime': '281' not in rt,
}
for k,v in checks.items(): print(k,'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)

def parse_arr(name):
    m=re.search(rf'{re.escape(name)}\[\]\s*=\s*\{{([^}}]+)\}};',rt,re.S)
    if not m: raise RuntimeError('missing '+name)
    return [int(x,16) for x in re.findall(r'0x[0-9A-Fa-f]+',m.group(1))]

def decode_text(path):
    b=path.read_bytes()
    if b[:4]!=b'NSO0': raise RuntimeError('not NSO0')
    u=lambda o:struct.unpack_from('<I',b,o)[0]
    flags=u(0x0c);fo=u(0x10);va=u(0x14);size=u(0x18);csz=u(0x60)
    blob=b[fo:fo+(csz if flags&1 else size)]
    if flags&1:
        if lz4 is None:return va,None
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
    out=[]
    for start in range(0,len(text)-4*len(vals)+1,4):
        ok=True
        for i,(v,m) in enumerate(zip(vals,masks)):
            w=struct.unpack_from('<I',text,start+4*i)[0]
            if (w&m)!=(v&m):ok=False;break
        if ok:out.append(va+start)
    return out

def bl_target(off,w):
    if (w&0xFC000000)!=0x94000000:return None
    imm=w&0x03ffffff
    if imm&(1<<25):imm-=1<<26
    return off+(imm<<2)

def derive_post(text,outer):
    hits=[]
    for off in range(4,len(text)-8,4):
        prev=struct.unpack_from('<I',text,off-4)[0]
        call=struct.unpack_from('<I',text,off)[0]
        nxt=struct.unpack_from('<I',text,off+4)[0]
        if prev==0xAA1703E0 and nxt==0xB9405288 and bl_target(off,call)==outer:
            hits.append(off+4)
    return hits

for label in ('restore','paired'):
    p=root/label/'atmosphere/contents/0100FA10190A0000/exefs/main'
    va,text=decode_text(p)
    if text is None:
        print('offline_signature_check',label,'SKIP(no lz4)');continue
    for name,vn,mn,expected in specs:
        hits=scan_unique(text,va,parse_arr(vn),parse_arr(mn))
        ok=len(hits)==1 and hits[0]==expected
        print(f'offline_{label}_{name}','PASS' if ok else 'FAIL','hits='+','.join(hex(x) for x in hits[:4]))
        if not ok:sys.exit(1)
    ph=derive_post(text,0x7EF098)
    ok=len(ph)==1 and ph[0]==0x77C5EC
    print(f'offline_{label}_UJ_SESSION_POST','PASS' if ok else 'FAIL','hits='+','.join(hex(x) for x in ph))
    if not ok:sys.exit(1)

paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
print('paired_main_sha256',sha(paired));print('restore_main_sha256',sha(restore))
if sha(paired)!='904a0405d04360ff3969909cdd7197c9e8c2aba2467151a7eaad4c821fcebbff':sys.exit(1)
if sha(restore)!='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9':sys.exit(1)
print('NSC_RUNTIME_V2C_SOURCE_VERIFY=PASS')
