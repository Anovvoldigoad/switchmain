#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, re, struct
import lz4.block

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'overlay/source/program/nsc_cpk_bridge.cpp'
HDR=ROOT/'overlay/source/program/condition_compat_generated.hpp'
MAN=ROOT/'condition_compat_manifest.json'
RESTORE=ROOT/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
DEPLOY=ROOT/'deploy/atmosphere/contents/0100FA10190A0000/exefs/main'
WORKFLOW=ROOT/'.github/workflows/build-subsdk9-p52a.yml'
EXPECTED_RESTORE='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
EXPECTED_BUILD_ID='48ece454b61412b9fb46fab2be3f5ef7b2804f39'

def sha(b): return hashlib.sha256(b).hexdigest()
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def decode(raw):
    flags=u32(raw,0xC); segs=[]
    specs=[(0x10,0x14,0x18,0x60,0xA0),(0x20,0x24,0x28,0x64,0xC0),(0x30,0x34,0x38,0x68,0xE0)]
    for i,(fo,mo,ds,cs,ho) in enumerate(specs):
        f=u32(raw,fo); m=u32(raw,mo); d=u32(raw,ds); c=u32(raw,cs); blob=raw[f:f+c]
        dec=lz4.block.decompress(blob,uncompressed_size=d) if flags&(1<<i) else blob
        assert len(dec)==d, f'seg{i} size'
        assert hashlib.sha256(dec).digest()==raw[ho:ho+32], f'seg{i} hash'
        segs.append((m,dec))
    return segs

def enc_movz_w(rd,imm): return 0x52800000 | (imm<<5) | (rd&31)
def enc_cmp_w(rn,imm): return 0x7100001F | (imm<<10) | ((rn&31)<<5)

ap=argparse.ArgumentParser(); ap.add_argument('--pre-build',action='store_true'); args=ap.parse_args()
for p in [SRC,HDR,MAN,RESTORE,DEPLOY,WORKFLOW]: assert p.is_file(), f'missing {p}'
m=json.loads(MAN.read_text()); assert m['format']=='NSC2SwitchConditionCompatManifestV1'
native=int(m['native_condition_count']); entries=m['entries']; total=native+len(entries)
assert native==512 and total==517
assert [e['name'] for e in entries]==['SW_MTOB_XH','SW_MTOB_ST','YXNQ_MTOB','SW_MTOB_BREAK','WC_MTOB_BREAK']

rr=RESTORE.read_bytes(); dr=DEPLOY.read_bytes()
assert sha(rr)==EXPECTED_RESTORE
assert rr[0x40:0x54].hex()==EXPECTED_BUILD_ID
assert dr[0x40:0x54].hex()==EXPECTED_BUILD_ID
rs=decode(rr); ds=decode(dr); rt=rs[0][1]; dt=ds[0][1]
assert len(rt)==len(dt)==0x12F5FD0
stock={0x747878:0x52804009,0x7774DC:0x7108031F,0x777770:0x7108027F,0x777938:0x7108027F,0x777A6C:0x7108027F}
patched={0x747878:enc_movz_w(9,total),0x7774DC:enc_cmp_w(24,total),0x777770:enc_cmp_w(19,total),0x777938:enc_cmp_w(19,total),0x777A6C:enc_cmp_w(19,total)}
for a,w in stock.items(): assert u32(rt,a)==w,(hex(a),hex(u32(rt,a)),hex(w))
for a,w in patched.items(): assert u32(dt,a)==w,(hex(a),hex(u32(dt,a)),hex(w))
# Getter remains stock; trampoline owns the extension.
getter=bytes.fromhex('cacf00b04a5d40f9e903002a080400511ff907714915098be083899ac0035fd6')
assert rt[0x754A80:0x754AA0]==getter and dt[0x754A80:0x754AA0]==getter
# Exact decompressed text delta is confined to the five immediate words.
diffs={i for i,(a,b) in enumerate(zip(rt,dt)) if a!=b}; allowed=set()
for a in patched: allowed.update(range(a,a+4))
assert diffs and diffs <= allowed, sorted(diffs-allowed)[:16]
# Other decompressed sections unchanged.
assert rs[1][1]==ds[1][1] and rs[2][1]==ds[2][1]

s=SRC.read_text()
required=['HOOK_DEFINE_TRAMPOLINE(ConditionGetterHook)','HOOK_DEFINE_TRAMPOLINE(Event121Hook)',
          'ConditionGetterHook::InstallAtOffset(kConditionGetterOffset)',
          'Event121Hook::InstallAtOffset(kEvent121Offset)',
          'InstallP50AConditionCompat()', 'installed_trampolines=5',
          'condition_compat_generated::kTotalConditionCount']
for token in required: assert token in s, token
# Gameplay source must stay data-driven; current ID may exist only as generic threshold constant/comment.
for bad in ['char_id == 281','char_id!=281','char_id != 281','COND_2DNZ','SW_2TOB']:
    assert bad not in s, bad
# Active path must be exactly the five intended trampoline installs via called installer functions.
body=re.search(r'void InstallP50AConditionCompat\(\) \{(.*?)\n\}',s,re.S); assert body
called=re.findall(r'Install(?:CpkBridge|Event236Dispatcher|PlayActionProbe|ConditionCompat)\(\)',body.group(1))
assert called==['InstallCpkBridge()','InstallEvent236Dispatcher()','InstallPlayActionProbe()','InstallConditionCompat()'],called
wf=WORKFLOW.read_text(); assert 'P48C' not in wf and 'build-subsdk9-p52a.yml' in wf
assert 'deploy/atmosphere/contents/0100FA10190A0000/exefs/main' in wf

# P52A read-only probe invariants.
for token in ['InstallP52APreUjProbe()', 'HOOK_DEFINE_TRAMPOLINE(UjStartWrapperHook)',
              'HOOK_DEFINE_TRAMPOLINE(UjStartStateHook)', 'HOOK_DEFINE_TRAMPOLINE(SpecialTypeCtrlHook)',
              'kUjStartWrapperOffset      = 0x488958', 'kUjStartStateOffset        = 0x7E3534',
              'kSpecialTypeCtrlOffset     = 0x646190', 'total_trampolines=10']:
    assert token in s, token
# P52 must not carry P51A speculative 0x7F2A9C main patch. Deploy main remains exact P50A.
assert sha(dr)=='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be'
print('P52A_KIT_VERIFY=PASS')
print('restore_main_sha256='+sha(rr))
print('deploy_main_sha256='+sha(dr))
print('build_id='+EXPECTED_BUILD_ID)
print(f'condition_count={native}+{len(entries)}={total}')
print('condition_names='+','.join(e['name'] for e in entries))
print('active_trampolines=5')
