#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, struct
import lz4.block

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
MANIFEST=ROOT/'condition_compat_manifest.json'
OUT=ROOT/'deploy/atmosphere/contents/0100FA10190A0000/exefs/main'
REPORT=ROOT/'P50A_MAIN_PATCH_AUDIT.json'
EXPECTED_BASE_SHA='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

def sha(b): return hashlib.sha256(b).hexdigest()
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def p32(b,o,v): struct.pack_into('<I',b,o,v&0xffffffff)

def enc_movz_w(rd,imm):
    if not 0<=imm<=0xffff: raise ValueError('mov imm')
    return 0x52800000 | (imm<<5) | (rd&31)
def enc_cmp_w(rn,imm):
    if not 0<=imm<=0xfff: raise ValueError('cmp imm')
    return 0x7100001F | (imm<<10) | ((rn&31)<<5)

def decode(raw):
    flags=u32(raw,0xC); segs=[]
    specs=[(0x10,0x14,0x18,0x60,0xA0),(0x20,0x24,0x28,0x64,0xC0),(0x30,0x34,0x38,0x68,0xE0)]
    for i,(fo,mo,ds,cs,ho) in enumerate(specs):
        f=u32(raw,fo); m=u32(raw,mo); d=u32(raw,ds); c=u32(raw,cs)
        blob=raw[f:f+c]
        dec=lz4.block.decompress(blob,uncompressed_size=d) if flags&(1<<i) else blob
        if len(dec)!=d: raise RuntimeError(f'seg{i} size mismatch')
        if hashlib.sha256(dec).digest()!=raw[ho:ho+32]: raise RuntimeError(f'seg{i} hash mismatch')
        segs.append({'i':i,'fileoff':f,'memoff':m,'dsz':d,'csz':c,'ho':ho,'dec':bytearray(dec)})
    return flags,segs

def rebuild(raw,segs):
    flags=u32(raw,0xC)
    hdr=bytearray(raw[:segs[0]['fileoff']]); blobs=[]
    for s in segs:
        dec=bytes(s['dec'])
        blob=lz4.block.compress(dec,store_size=False,mode='high_compression',compression=12) if flags&(1<<s['i']) else dec
        blobs.append(blob)
        hdr[s['ho']:s['ho']+32]=hashlib.sha256(dec).digest()
        p32(hdr,[0x18,0x28,0x38][s['i']],len(dec))
    cur=segs[0]['fileoff']
    for i,(fo,cs) in enumerate([(0x10,0x60),(0x20,0x64),(0x30,0x68)]):
        p32(hdr,fo,cur); p32(hdr,cs,len(blobs[i])); cur+=len(blobs[i])
    return bytes(hdr)+b''.join(blobs)

raw=BASE.read_bytes()
if sha(raw)!=EXPECTED_BASE_SHA: raise SystemExit('unsupported restore main SHA '+sha(raw))
m=json.loads(MANIFEST.read_text())
native=int(m['native_condition_count']); total=native+len(m['entries'])
if native!=512: raise SystemExit('this SC1.70 patch expects native condition geometry 512')
if not 513<=total<=4095: raise SystemExit('unexpected total condition count')
flags,segs=decode(raw); text=segs[0]['dec']
if segs[0]['memoff']!=0: raise SystemExit('unexpected text VA')

expected={
  0x747878:0x52804009, # mov w9,#512
  0x7774DC:0x7108031F, # cmp w24,#512
  0x777770:0x7108027F, # cmp w19,#512
  0x777938:0x7108027F,
  0x777A6C:0x7108027F,
}
patches={
  0x747878:enc_movz_w(9,total),
  0x7774DC:enc_cmp_w(24,total),
  0x777770:enc_cmp_w(19,total),
  0x777938:enc_cmp_w(19,total),
  0x777A6C:enc_cmp_w(19,total),
}
for a,e in expected.items():
    g=u32(text,a)
    if g!=e: raise SystemExit(f'fingerprint mismatch {a:#x}: {g:#010x} != {e:#010x}')
before=bytes(text)
for a,v in patches.items(): p32(text,a,v)
# Condition getter itself MUST remain untouched; P50A replaces it via trampoline.
getter_before=before[0x754A80:0x754AA0]
getter_after=bytes(text[0x754A80:0x754AA0])
if getter_before!=getter_after: raise SystemExit('getter changed unexpectedly')
segs[0]['dec']=text
out=rebuild(raw,segs)
# round-trip integrity
_,chk=decode(out)
if len(chk[0]['dec'])!=len(text): raise SystemExit('text size changed')
# exact diff: only 20 bytes across five words may differ in decompressed text
post=bytes(chk[0]['dec']); diffs=[i for i,(a,b) in enumerate(zip(before,post)) if a!=b]
allowed=set()
for a in patches: allowed.update(range(a,a+4))
extra=[i for i in diffs if i not in allowed]
if extra: raise SystemExit('unexpected decoded text diffs '+','.join(hex(x) for x in extra[:16]))
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_bytes(out)
report={
 'format':'NSC2Switch_P50A_CONDITION_LIMIT_PATCH_V1',
 'base_sha256':sha(raw),'output_sha256':sha(out),'build_id':out[0x40:0x54].hex(),
 'native_condition_count':native,'extra_condition_count':len(m['entries']),'total_condition_count':total,
 'patches':{hex(a):{'before':hex(expected[a]),'after':hex(patches[a])} for a in patches},
 'condition_getter_va':'0x754A80','condition_getter_patched_in_main':False,
 'claims':['only five count/loop immediates changed','no text cave','no data/BSS growth','no char-ID alias','paired subsdk9 provides dynamic descriptor getter']
}
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2)); print('OUTPUT',OUT); print('SHA256',sha(out))
