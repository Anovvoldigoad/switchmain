#!/usr/bin/env python3
from pathlib import Path
import re,struct,sys
try:
    import lz4.block
except Exception:
    lz4=None
root=Path(__file__).resolve().parent
cpp=(root/'overlay/source/program/nsc_runtime_v2.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
prep=(root/'prepare_exlaunch.sh').read_text()
wf=(root/'.github/workflows/build-runtime-v2a.yml').read_text()
checks={
 'seven_anchors': len(re.findall(r'\{"[A-Z0-9_]+"\s*,',cpp))==7,
 'fail_closed_ambiguous': 'if (hits > 1) return 0' in cpp,
 'readonly_marker': 'no_runtime_patch=1' in cpp and 'no_new_hook=1' in cpp,
 'coexists_p128': 'InstallResolverCoexistenceProbe();' in main and 'InstallP128AStaticPreciseGateCaveProof();' in main,
 'copies_resolver': 'nsc_runtime_v2.cpp' in prep and 'nsc_runtime_v2.hpp' in prep,
 'workflow_marker': 'NSC-RUNTIME-V2A-resolver-coexistence' in wf,
 'no_char281': '281' not in cpp,
}

def parse_arr(name):
    m=re.search(rf'{re.escape(name)}\[\]\s*=\s*\{{([^}}]+)\}};',cpp,re.S)
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
    # Candidate on first exact word when possible; avoids an expensive full Python scan.
    pivot=next((i for i,m in enumerate(masks) if m==0xffffffff),0)
    pat=struct.pack('<I',vals[pivot]) if masks[pivot]==0xffffffff else None
    cand=[]
    if pat is not None:
        pos=0
        while True:
            j=text.find(pat,pos)
            if j<0: break
            start=j-pivot*4
            pos=j+1
            if start<0 or start%4 or start+4*len(vals)>len(text): continue
            ok=True
            for i,(v,m) in enumerate(zip(vals,masks)):
                w=struct.unpack_from('<I',text,start+4*i)[0]
                if (w&m)!=(v&m): ok=False; break
            if ok: cand.append(va+start)
    return cand

for k,v in checks.items(): print(k,'PASS' if v else 'FAIL')
if not all(checks.values()): sys.exit(1)

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
print('NSC_RUNTIME_V2A_SOURCE_VERIFY=PASS')
