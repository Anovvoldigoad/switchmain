#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, struct
import lz4.block

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
OUT = ROOT / 'p41_main/atmosphere/contents/0100FA10190A0000/exefs/main'
REPORT = ROOT / 'P41A_CONDITION_MAIN_AUDIT.json'

EXPECTED_BASE_SHA = '2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
TEXT_NEW_SIZE = 0x12F6000
DATA_NEW_SIZE = 0x2AF000
HIGH_TABLE_VA = 0x21616C8
DT_INIT_VA = 0x12F5FD0
DT_INIT_ENTRY_VA = 0x2141EB0
TOTAL_DATA_PLUS_BSS = 0x2619000

# Current fixture native condition-manager high-bank records recovered from the
# previously hardware-stable R9A/R3 split-bank build. Only the five names are
# restored to the current source namespace (MTOB, not the historical 2TOB alias).
HIGH_BANK = bytes.fromhex(
    'a000000000000000010200000100000008000000050000000500000000000000'
    '8b00000000000000000000000a00000007000000050000000500000000000000'
    '7600000000000000010200000100000009000000050000000500000000000000'
    '6000000000000000000000000000000000000000050000000500000000000000'
    '4e00000000000000000000000000000003000000050000000500000000000000'
    '53575f4d544f425f584800'
    '53575f4d544f425f535400'
    '59584e515f4d544f4200'
    '53575f4d544f425f425245414b00'
    '57435f4d544f425f425245414b00'
)

# Exact 36-byte R3/R9A condition-only DT_INIT relocator. The historical 12-byte
# Event236 trampoline that followed this block is deliberately NOT restored.
DT_INIT_STUB = bytes.fromhex(
    '6973009029211b91aa0080d22b0140f96b01098b2b0502f84a0500f181ffff541028b417'
)
assert len(DT_INIT_STUB) == 36

# Exact verified current->517 instruction changes. The getter consumes its
# preceding 12-byte zero cave and retains the native split-bank rule.
WORD_PATCHES = {
    0x747878: 0x528040A9,  # static count 512 -> 517
    0x754A74: 0xB000CFCA,  # split-bank getter entry (ADRP manager)
    0x754A78: 0xF9405D4A,
    0x754A7C: 0x14000002,
    0x754A80: 0x17FFFFFD,
    0x754A84: 0x36480040,  # TBZ index bit9 -> low bank
    0x754A88: 0x9143A94A,  # high bank base += 0xEA000
    0x754A8C: 0x8B001549,  # record = base + index*0x20
    0x754A90: 0x51000408,  # index-1
    0x754A94: 0x71080D1F,  # <= 515 => IDs 0..516
    # 0x754A98 is already the required CSEL and stays byte-identical.
    0x7774DC: 0x7108171F,  # condition-name loop 512 -> 517
    0x777770: 0x7108167F,
    0x777938: 0x7108167F,
    0x777A6C: 0x7108167F,
}

EXPECTED_CURRENT_WORDS = {
    0x747878: 0x52804009,
    0x754A74: 0x00000000,
    0x754A78: 0x00000000,
    0x754A7C: 0x00000000,
    0x754A80: 0xB000CFCA,
    0x754A84: 0xF9405D4A,
    0x754A88: 0x2A0003E9,
    0x754A8C: 0x51000408,
    0x754A90: 0x7107F91F,
    0x754A94: 0x8B091549,
    0x7774DC: 0x7108031F,
    0x777770: 0x7108027F,
    0x777938: 0x7108027F,
    0x777A6C: 0x7108027F,
}

def sha(b): return hashlib.sha256(b).hexdigest()
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def p32(b,o,v): struct.pack_into('<I',b,o,v & 0xffffffff)
def u64(b,o): return struct.unpack_from('<Q',b,o)[0]
def p64(b,o,v): struct.pack_into('<Q',b,o,v & 0xffffffffffffffff)

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
    flags,_=decode(raw)
    hdr=bytearray(raw[:segs[0]['fileoff']]); blobs=[]
    for s in segs:
        dec=bytes(s['dec'])
        blob=lz4.block.compress(dec,store_size=False,mode='high_compression',compression=12) if flags&(1<<s['i']) else dec
        blobs.append(blob)
        hdr[s['ho']:s['ho']+32]=hashlib.sha256(dec).digest()
        p32(hdr, [0x18,0x28,0x38][s['i']], len(dec))
    # Keep mapped data+BSS total identical while consuming old BSS bytes as data.
    p32(hdr,0x3C,TOTAL_DATA_PLUS_BSS-len(segs[2]['dec']))
    cur=segs[0]['fileoff']
    for i,(fo,cs) in enumerate([(0x10,0x60),(0x20,0x64),(0x30,0x68)]):
        p32(hdr,fo,cur); p32(hdr,cs,len(blobs[i])); cur+=len(blobs[i])
    return bytes(hdr)+b''.join(blobs)

raw=BASE.read_bytes()
if sha(raw)!=EXPECTED_BASE_SHA: raise SystemExit('unsupported restore main SHA '+sha(raw))
flags,segs=decode(raw)
text=segs[0]['dec']; data=segs[2]['dec']
assert segs[0]['memoff']==0 and len(text)==0x12F5FD0
assert segs[2]['memoff']==0x1EB3000 and len(data)==0x2AE234
assert len(data)+u32(raw,0x3C)==TOTAL_DATA_PLUS_BSS

for va,expect in EXPECTED_CURRENT_WORDS.items():
    got=u32(text,va)
    if got!=expect: raise RuntimeError(f'fingerprint mismatch {va:#x}: {got:#010x} != {expect:#010x}')

before_text=bytes(text); before_data=bytes(data)
for va,w in WORD_PATCHES.items(): p32(text,va,w)
# Ensure split getter terminal CSEL/RET are still exact current native instructions.
assert u32(text,0x754A98)==0x9A8983E0 and u32(text,0x754A9C)==0xD65F03C0

# Consume the exact existing text->rodata alignment gap. No Ougi/Event236 code.
text.extend(b'\0'*(TEXT_NEW_SIZE-len(text)))
text[DT_INIT_VA:DT_INIT_VA+len(DT_INIT_STUB)] = DT_INIT_STUB
for va in range(DT_INIT_VA+len(DT_INIT_STUB),TEXT_NEW_SIZE,4): p32(text,va,0xD503201F) # NOP

# Consume old BSS up to the historical split high bank; zero-fill all new data,
# then install only the current five condition descriptors+strings.
data.extend(b'\0'*(DATA_NEW_SIZE-len(data)))
ho=HIGH_TABLE_VA-segs[2]['memoff']
data[ho:ho+len(HIGH_BANK)] = HIGH_BANK
# DT_INIT dynamic entry: call the five-record relocator before normal main init.
p64(data,DT_INIT_ENTRY_VA-segs[2]['memoff'],DT_INIT_VA)

segs[0]['dec']=text; segs[2]['dec']=data
out_raw=rebuild(raw,segs)
# Full decode/header integrity check.
flags2,segs2=decode(out_raw)
assert len(segs2[0]['dec'])==TEXT_NEW_SIZE
assert len(segs2[2]['dec'])==DATA_NEW_SIZE
assert u32(out_raw,0x3C)==TOTAL_DATA_PLUS_BSS-DATA_NEW_SIZE

# Validate runtime pointer geometry after DT_INIT: each record's relative qword
# must resolve to the exact embedded name.
d2=segs2[2]['dec']; dbo=HIGH_TABLE_VA-segs2[2]['memoff']
names=[]
for i in range(5):
    ro=dbo+i*0x20; rel=u64(d2,ro); so=ro+rel
    end=d2.find(b'\0',so,so+64)
    if end<0: raise RuntimeError('unterminated condition name')
    names.append(bytes(d2[so:end]).decode('ascii'))
expected_names=['SW_MTOB_XH','SW_MTOB_ST','YXNQ_MTOB','SW_MTOB_BREAK','WC_MTOB_BREAK']
assert names==expected_names, names

# Audit changed decoded-text bytes. Every difference must be either a whitelisted
# word patch or the appended DT_INIT block/padding.
changed=[]
for i,(a,b) in enumerate(zip(before_text,text[:len(before_text)])):
    if a!=b: changed.append(i)
allowed=set()
for va in WORD_PATCHES: allowed.update(range(va,va+4))
extra=[x for x in changed if x not in allowed]
if extra: raise RuntimeError('unexpected text changes '+','.join(hex(x) for x in extra[:20]))

OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_bytes(out_raw)
report={
 'format':'NSC2Switch_P41A_CONDITION_SPLIT_BANK_V1',
 'base_sha256':sha(raw),'output_sha256':sha(out_raw),
 'build_id':out_raw[0x40:0x54].hex(),
 'text':{'old_size':hex(len(before_text)),'new_size':hex(TEXT_NEW_SIZE),'condition_stub_va':hex(DT_INIT_VA),'stub_size':len(DT_INIT_STUB),'patched_words':{hex(k):hex(v) for k,v in WORD_PATCHES.items()}},
 'data':{'old_size':hex(len(before_data)),'new_size':hex(DATA_NEW_SIZE),'high_table_va':hex(HIGH_TABLE_VA),'high_table_payload_size':len(HIGH_BANK),'names':names,'dt_init_entry_va':hex(DT_INIT_ENTRY_VA),'dt_init_value':hex(u64(segs2[2]['dec'],DT_INIT_ENTRY_VA-segs2[2]['memoff']))},
 'bss':{'old_size':hex(u32(raw,0x3C)),'new_size':hex(u32(out_raw,0x3C)),'mapped_data_plus_bss':hex(TOTAL_DATA_PLUS_BSS)},
 'excluded_legacy_changes':['0x6CBF74','0x7E1404/0x7E1408','0x876188 legacy endpoint','0x887A64','0x887B44','old Event236 relocation/trampoline at 0x12F5FF4'],
 'claims':['generic 517 native condition descriptor range restored','native split-bank getter restored','current MTOB namespace retained','no donor char-id alias','no old Ougi patch','no old Event236 trampoline']
}
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2)); print('OUTPUT',OUT); print('SHA256',sha(out_raw))
