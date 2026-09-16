#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,struct,lz4.block,re,sys
R=Path(__file__).resolve().parent
BASE=R/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
MAIN=R/'p41_main/atmosphere/contents/0100FA10190A0000/exefs/main'
CPP=R/'overlay/source/program/nsc_cpk_bridge.cpp'
BASE_SHA='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
MAIN_SHA='407ff7247a2c70941c05eb2cdfbd65a2a25fffc247845274b096ed0b5aee6ae7'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def u64(b,o):return struct.unpack_from('<Q',b,o)[0]
def decode(p):
 raw=p.read_bytes(); flags=u32(raw,0xC); ss=[]
 for i,(fo,mo,ds,cs,ho) in enumerate([(0x10,0x14,0x18,0x60,0xA0),(0x20,0x24,0x28,0x64,0xC0),(0x30,0x34,0x38,0x68,0xE0)]):
  f=u32(raw,fo);m=u32(raw,mo);d=u32(raw,ds);c=u32(raw,cs);bb=raw[f:f+c]
  x=lz4.block.decompress(bb,uncompressed_size=d) if flags&(1<<i) else bb
  assert len(x)==d and hashlib.sha256(x).digest()==raw[ho:ho+32]
  ss.append((m,x))
 return raw,ss
assert sha(BASE)==BASE_SHA,(sha(BASE),'base')
assert sha(MAIN)==MAIN_SHA,(sha(MAIN),'main')
rb,sb=decode(BASE); rp,sp=decode(MAIN)
assert rp[0x40:0x54]==rb[0x40:0x54]
assert len(sp[0][1])==0x12F6000 and len(sp[2][1])==0x2AF000
assert len(sp[2][1])+u32(rp,0x3C)==0x2619000
# Condition count / split getter / name loops.
words={
0x747878:0x528040A9,0x754A74:0xB000CFCA,0x754A78:0xF9405D4A,0x754A7C:0x14000002,
0x754A80:0x17FFFFFD,0x754A84:0x36480040,0x754A88:0x9143A94A,0x754A8C:0x8B001549,
0x754A90:0x51000408,0x754A94:0x71080D1F,0x754A98:0x9A8983E0,
0x7774DC:0x7108171F,0x777770:0x7108167F,0x777938:0x7108167F,0x777A6C:0x7108167F}
for va,w in words.items(): assert u32(sp[0][1],va)==w,(hex(va),hex(u32(sp[0][1],va)),hex(w))
# Forbidden old Ougi patch sites remain exact parent.
for va,n in [(0x7E13E4,4),(0x7E1404,8),(0x6CBF74,4),(0x876188,4),(0x887A64,4),(0x887B44,4)]:
 assert sp[0][1][va:va+n]==sb[0][1][va:va+n],('legacy change leaked',hex(va))
# Current hook boundaries untouched.
for va in [0x810614,0x8134F8,0x8162D4,0x816300,0x7E0F58]:
 assert sp[0][1][va:va+32]==sb[0][1][va:va+32],('hook boundary changed',hex(va))
# High bank relative-pointer geometry.
dv,dd=sp[2]; base=0x21616C8; bo=base-dv
names=[]
for i in range(5):
 ro=bo+i*0x20; rel=u64(dd,ro); so=ro+rel; e=dd.find(b'\0',so,so+64); assert e>so
 names.append(dd[so:e].decode())
assert names==['SW_MTOB_XH','SW_MTOB_ST','YXNQ_MTOB','SW_MTOB_BREAK','WC_MTOB_BREAK']
assert u64(dd,0x2141EB0-dv)==0x12F5FD0
# Condition-only DT_INIT + NOP tail, no old Event236 trampoline.
stub=bytes.fromhex('6973009029211b91aa0080d22b0140f96b01098b2b0502f84a0500f181ffff541028b417')
assert sp[0][1][0x12F5FD0:0x12F5FD0+36]==stub
assert sp[0][1][0x12F5FD0+36:0x12F6000]==b'\x1f\x20\x03\xd5'*3
# Source contract.
s=CPP.read_text()
for token in ['EVT121_SELF','CTRL14_SHADOW','EVT13_RAW','OUGI_RAW','kConditionResolveOffset    = 0x777758','r.resolved <= 0']:
 assert token in s,token
assert 'EnableControlActorLocal' not in s
# Gameplay source must not contain old aliases/donor condition.
assert 'SW_2TOB' not in s and 'COND_2DNZ' not in s
print('P41A_KIT_VERIFY=PASS')
print('base_main_sha256='+sha(BASE))
print('p41_main_sha256='+sha(MAIN))
print('build_id='+rp[0x40:0x54].hex())
print('condition_names='+','.join(names))
