"""Append PC condition descriptors while retaining the native Switch prefix.

The 512-row NSC manager baseline is pinned, not inferred from file extension.
This does not append the separate 176-byte conditionprm data or port effects.
"""
import hashlib
import struct
from .nso_profile import configure_payload
MAGIC=b'NSC_COND_V1'.ljust(16,b'\0')
NATIVE_COUNT=512
CAPACITY=512
RECORD_SIZE=80
PROFILE_SIZE=64+CAPACITY*RECORD_SIZE
PC_RECORD_SIZE=112
PC_BASELINE_SHA256='fae4c1e1a510f895a7b9b9acbf5b710e7472e9b47f3471087dd4b1c97b7b86c5'
FIELDS=('reaction','state','icon','status','aura')


def seal(b):
    b=bytearray(b);b[24:56]=hashlib.sha256(b[:24]+b[56:]).digest();return bytes(b)


def name_bytes(name):
    if not isinstance(name,str):raise ValueError('Name must be a string')
    try:b=name.encode('ascii')
    except UnicodeEncodeError:raise ValueError('Non-ASCII name') from None
    if not 1<=len(b)<=48 or any(c<32 or c>126 for c in b):raise ValueError('Expected 1..48 printable ASCII name bytes')
    return b


def encode(rows):
    if not isinstance(rows,list) or len(rows)>CAPACITY:raise ValueError('At most 512 appended descriptors')
    b=bytearray(PROFILE_SIZE);b[:16]=MAGIC;struct.pack_into('<II',b,16,1,len(rows));names=set()
    for i,row in enumerate(rows):
        if not isinstance(row,dict) or set(row)!=set(FIELDS)|{'name'}:raise ValueError('Descriptor fields')
        name=name_bytes(row['name'])
        if name in names:raise ValueError('Duplicate condition name')
        names.add(name)
        vals=[row[k] for k in FIELDS]
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in vals):raise ValueError('Expected uint32 fields')
        if vals[0]>=NATIVE_COUNT+len(rows):raise ValueError('Reaction outside descriptor table')
        at=64+i*RECORD_SIZE;b[at:at+len(name)]=name;struct.pack_into('<5I',b,at+56,*vals)
    return seal(b)


def decode(b):
    if len(b)!=PROFILE_SIZE or b[:16]!=MAGIC:raise ValueError('Condition profile size/magic')
    version,count=struct.unpack_from('<II',b,16)
    if version!=1 or count>CAPACITY or any(b[56:64]):raise ValueError('Condition profile header')
    if seal(b)!=b:raise ValueError('Condition profile SHA256')
    rows=[]
    for i in range(count):
        at=64+i*RECORD_SIZE;name=b[at:at+49]
        if b'\0' not in name:raise ValueError('Unterminated name')
        n,pad=name.split(b'\0',1)
        if any(pad) or any(b[at+49:at+56]) or any(b[at+76:at+80]):raise ValueError('Nonzero reserved bytes')
        try:n=n.decode('ascii')
        except UnicodeDecodeError:raise ValueError('Non-ASCII name') from None
        rows.append(dict(name=n,**dict(zip(FIELDS,struct.unpack_from('<5I',b,at+56)))))
    if any(b[64+count*RECORD_SIZE:]) or encode(rows)!=b:raise ValueError('Noncanonical profile')
    return rows


def compile_table(raw):
    """One fully merged PC table; stable native prefix, preserve appended ordinals."""
    if len(raw)%PC_RECORD_SIZE or not NATIVE_COUNT<=len(raw)//PC_RECORD_SIZE<=NATIVE_COUNT+CAPACITY:
        raise ValueError('Expected 512..1024 raw 112-byte conditionprmManager rows')
    if hashlib.sha256(raw[:NATIVE_COUNT*PC_RECORD_SIZE]).hexdigest()!=PC_BASELINE_SHA256:
        raise ValueError('PC baseline prefix differs; edits/reordering of stock descriptors are not verified')
    parsed=[]
    for off in range(0,len(raw),PC_RECORD_SIZE):
        row=raw[off:off+PC_RECORD_SIZE]
        try:name=row[:48].split(b'\0',1)[0].decode('ascii');reaction=row[48:96].split(b'\0',1)[0].decode('ascii')
        except UnicodeDecodeError:raise ValueError('Non-ASCII PC condition name') from None
        name_bytes(name)
        if reaction:name_bytes(reaction)
        parsed.append((name,reaction,struct.unpack_from('<4I',row,96)))
    first={}
    for i,(name,_,_) in enumerate(parsed):
        if i>=NATIVE_COUNT and name in first:raise ValueError('Appended name collides with an earlier descriptor')
        first.setdefault(name,i)
    rows=[];missing=[]
    for i,(name,reaction,values) in enumerate(parsed[NATIVE_COUNT:],NATIVE_COUNT):
        if reaction and reaction not in first:missing.append({'index':i,'reaction':reaction,'resolved':0})
        rows.append(dict(name=name,reaction=first.get(reaction,0),**dict(zip(FIELDS[1:],values))))
    profile=encode(rows)
    return profile,{'input_sha256':hashlib.sha256(raw).hexdigest(),'pc_baseline_sha256':PC_BASELINE_SHA256,
        'native_prefix_preserved':NATIVE_COUNT,'appended_descriptors':len(rows),
        'raw_conditionprm_required_rows':len(parsed),'missing_reactions_native_zero_fallback':missing,
        'raw_conditionprm_packaged':False,'gameplay_verified':False,'full_moddingapi':False}


def configure(nso,profile,expected_sha256):
    result,report=configure_payload(nso,profile,expected_sha256,MAGIC,PROFILE_SIZE,decode)
    report['appended_descriptors']=len(decode(profile));return result,report
