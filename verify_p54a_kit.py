#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,struct
import lz4.block
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'overlay/source/program/nsc_cpk_bridge.cpp'; MAINCPP=ROOT/'overlay/source/program/main.cpp'
RESTORE=ROOT/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
DEPLOY=ROOT/'deploy/atmosphere/contents/0100FA10190A0000/exefs/main'
MAN=ROOT/'condition_compat_manifest.json'
EXPECTED_RESTORE='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
EXPECTED_DEPLOY='8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be'
EXPECTED_BUILD_ID='48ece454b61412b9fb46fab2be3f5ef7b2804f39'
def sha(b): return hashlib.sha256(b).hexdigest()
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def dec_text(raw):
 flags=u32(raw,0xc); f=u32(raw,0x10); sz=u32(raw,0x18); c=u32(raw,0x60); blob=raw[f:f+(c if flags&1 else sz)]
 return lz4.block.decompress(blob,uncompressed_size=sz) if flags&1 else blob
for p in [SRC,MAINCPP,RESTORE,DEPLOY,MAN,ROOT/'README_P54A.txt',ROOT/'P54A_STATIC_AUDIT.txt',ROOT/'analyze_p54a_log.py']: assert p.is_file(),p
rr=RESTORE.read_bytes(); dr=DEPLOY.read_bytes(); assert sha(rr)==EXPECTED_RESTORE; assert sha(dr)==EXPECTED_DEPLOY
assert rr[0x40:0x54].hex()==EXPECTED_BUILD_ID and dr[0x40:0x54].hex()==EXPECTED_BUILD_ID
s=SRC.read_text(); m=MAINCPP.read_text()
for tok in ['kDirectAction98OwnerOffset  = 0x2A472C','kDirectAction100OwnerOffset = 0x2A51B8',
            '[NSC:P54A] DIRECT98_OWNER','[NSC:P54A] DIRECT100_OWNER','InstallP54ADirectJutsuProbe()',
            'total_trampolines=7','index == 98','index == 100','index == 937','index == 938']:
 assert tok in s,tok
assert 'nsc::InstallP54ADirectJutsuProbe();' in m
assert 'nsc::InstallP53AInputPromotionProbe();' not in m
body=re.search(r'void InstallP54ADirectJutsuProbe\(\) \{(.*?)\n\}',s,re.S); assert body
assert body.group(1).count('InstallP50AConditionCompat();')==1
assert body.group(1).count('InstallP54DirectJutsuOwnerProbes();')==1
# P50 remains the proven 5-trampoline core.
p50=re.search(r'void InstallP50AConditionCompat\(\) \{(.*?)\n\}',s,re.S); assert p50
called=re.findall(r'Install(?:CpkBridge|Event236Dispatcher|PlayActionProbe|ConditionCompat)\(\)',p50.group(1))
assert called==['InstallCpkBridge()','InstallEvent236Dispatcher()','InstallPlayActionProbe()','InstallConditionCompat()'],called
# No one-character executable solution.
for bad in ['char_id == 281','char_id!=281','char_id != 281','COND_2DNZ','SW_2TOB']:
 assert bad not in s,bad
# Exact main fingerprints, including both owner entries/direct setter sites.
t=dec_text(dr)
expect={
 0x2A472C:0xD10243FF,0x2A4730:0xFD0023E8,0x2A4734:0xF90027FE,0x2A4738:0xA90567FA,
 0x2A50B8:0xF9400268,0x2A50C0:0x52800C41,0x2A50C4:0xF947CD08,0x2A50D4:0xD63F0100,
 0x2A51B8:0xF81D0FFE,0x2A51BC:0xA90157F6,0x2A51C0:0xA9024FF4,0x2A51C4:0x7100203F,
 0x2A568C:0xF9400268,0x2A5694:0x52800C81,0x2A5698:0xF947CD08,0x2A56A8:0xD63F0100,
 0x766B8C:0xA9BE57FE,
}
for a,w in expect.items(): assert u32(t,a)==w,(hex(a),hex(u32(t,a)),hex(w))
manifest=json.loads(MAN.read_text()); assert int(manifest['native_condition_count'])+len(manifest['entries'])==517
print('P54A_KIT_VERIFY=PASS')
print('restore_main_sha256='+sha(rr)); print('deploy_main_sha256='+sha(dr)); print('build_id='+EXPECTED_BUILD_ID)
print('active_trampolines=7'); print('new_read_only_hooks=0x2A472C,0x2A51B8')
print('direct_setter_actions=98,100'); print('playaction_observed_extra=98,100,937,938')
