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
for p in [SRC,MAINCPP,RESTORE,DEPLOY,MAN,ROOT/'README_P53A.txt',ROOT/'analyze_p53a_log.py']: assert p.is_file(),p
rr=RESTORE.read_bytes(); dr=DEPLOY.read_bytes(); assert sha(rr)==EXPECTED_RESTORE; assert sha(dr)==EXPECTED_DEPLOY
assert rr[0x40:0x54].hex()==EXPECTED_BUILD_ID and dr[0x40:0x54].hex()==EXPECTED_BUILD_ID
s=SRC.read_text(); m=MAINCPP.read_text()
for tok in ['index == 84','index == 930','index >= 700 && index <= 740','[NSC:P53A] ACTION_ROUTE','InstallP53AInputPromotionProbe()','total_trampolines=5']:
 assert tok in s,tok
assert 'nsc::InstallP53AInputPromotionProbe();' in m
assert 'nsc::InstallP52APreUjProbe();' not in m
body=re.search(r'void InstallP53AInputPromotionProbe\(\) \{(.*?)\n\}',s,re.S); assert body
assert body.group(1).count('InstallP50AConditionCompat();')==1
assert 'InstallP52PreUjTraceHooks' not in body.group(1)
# P50 active installer remains exactly the proven four installer calls -> five trampolines.
p50=re.search(r'void InstallP50AConditionCompat\(\) \{(.*?)\n\}',s,re.S); assert p50
called=re.findall(r'Install(?:CpkBridge|Event236Dispatcher|PlayActionProbe|ConditionCompat)\(\)',p50.group(1))
assert called==['InstallCpkBridge()','InstallEvent236Dispatcher()','InstallPlayActionProbe()','InstallConditionCompat()'],called
for bad in ['char_id == 281','char_id!=281','char_id != 281','COND_2DNZ','SW_2TOB']:
 assert bad not in s,bad
# Exact SC1.70 action84 proof on paired main decoded text.
t=dec_text(dr)
expect={0x2A4514:0xD100C3FF,0x2A4518:0xA90157FE,0x2A451C:0xA9024FF4,0x2A4520:0xAA0003F3,
        0x2A4524:0x7100083F,0x2A4528:0x54000600,0x2A4550:0x52800A81,0x2A456C:0x94130988,
        0x766B8C:0xA9BE57FE}
for a,w in expect.items(): assert u32(t,a)==w,(hex(a),hex(u32(t,a)),hex(w))
manifest=json.loads(MAN.read_text()); assert int(manifest['native_condition_count'])+len(manifest['entries'])==517
print('P53A_KIT_VERIFY=PASS')
print('restore_main_sha256='+sha(rr)); print('deploy_main_sha256='+sha(dr)); print('build_id='+EXPECTED_BUILD_ID)
print('active_trampolines=5'); print('observed_actions=84,930,700..740')
