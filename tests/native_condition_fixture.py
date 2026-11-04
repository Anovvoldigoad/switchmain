"""Reconstruct PC baseline from the supplied native image, with one audited delta."""
import hashlib,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.nso_profile import segments
from portlib.condition_profile import PC_BASELINE_SHA256

def native_image(main):
    raw=main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
    segs=segments(raw);size=segs[-1][0]+len(segs[-1][1])+struct.unpack_from('<I',raw,60)[0]
    image=bytearray((size+4095)&~4095)
    for va,data,_ in segs:image[va:va+len(data)]=data
    mod0=struct.unpack_from('<I',image,4)[0];dynamic=mod0+struct.unpack_from('<i',image,mod0+4)[0];tags={}
    for off in range(dynamic,dynamic+4096,16):
        k,v=struct.unpack_from('<QQ',image,off)
        if not k:break
        tags[k]=v
    rel={a:v for off in range(tags[7],tags[7]+tags[8],24) for a,k,v in [struct.unpack_from('<QQq',image,off)] if k==1027}
    return image,rel

def baseline_from_main(main):
    image,rel=native_image(main);base=rel[0x214d0b8];rows=[]
    assert base==0x20736c8
    for i in range(512):
        p=rel[base+i*32];name=bytes(image[p:image.index(0,p)]).decode('ascii')
        vals=struct.unpack_from('<6I',image,base+i*32+8)
        assert vals[0]<512 and vals[5]==0
        rows.append((name,vals))
    raw=bytearray()
    for i,(name,vals) in enumerate(rows):
        reaction=rows[vals[0]][0] if vals[0] else ''
        values=list(vals[1:5])
        if i==103:
            assert (name,tuple(vals))==('AWAKE_1SKR',(104,1,8,5,107,0))
            values[3]=5 # exact upstream PC template difference; runtime retains 107
        raw+=name.encode().ljust(48,b'\0')+reaction.encode().ljust(48,b'\0')+struct.pack('<4I',*values)
    assert hashlib.sha256(raw).hexdigest()==PC_BASELINE_SHA256
    return bytes(raw),rows

def pc_record(name,reaction='',state=0,icon=0,status=5,aura=5):
    assert len(name.encode())<=48 and len(reaction.encode())<=48
    return name.encode().ljust(48,b'\0')+reaction.encode().ljust(48,b'\0')+struct.pack('<4I',state,icon,status,aura)
