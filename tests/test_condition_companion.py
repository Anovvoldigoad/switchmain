"""Ordinal/count corruption and CLI no-output-on-invalid-pair regression."""
import argparse, hashlib, json, struct, subprocess, sys, tempfile
from pathlib import Path
from native_condition_fixture import baseline_from_main, pc_record
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.condition_companion import validate
from portlib.prm_events import binary_chunks


def fixture(names):
    payload=struct.pack('>I',4+len(names)*176)+struct.pack('<I',len(names))
    payload+=b''.join(n.encode().ljust(64,b'\0')+bytes(112) for n in names)
    types=b'nuccChunkBinary\0nuccChunkPage\0';paths=b'\0';strings=b'conditionprm\0page\0'
    b=bytearray(68);b[:4]=b'NUCC';struct.pack_into('>I',b,4,121)
    struct.pack_into('>10I',b,28,2,len(types),1,1,2,len(strings),2,24,2,0)
    b+=types+paths+strings;b+=bytes(-len(b)%4)
    b+=struct.pack('>6I',0,0,0,1,0,1)+struct.pack('>2I',0,1)
    b+=struct.pack('>IIHH',len(payload),0,121,0)+payload
    b+=struct.pack('>IIHHII',8,1,121,0,2,0)
    return bytes(b)


def run(main, output):
    baseline,_=baseline_from_main(main)
    base_names=[baseline[i:i+48].split(b'\0')[0].decode() for i in range(0,len(baseline),112)]
    checked=[]
    for extra in [0,1,5,512]:
        manager=baseline+b''.join(pc_record(f'MOD_{i}') for i in range(extra))
        raw=fixture(base_names+[f'MOD_{i}' for i in range(extra)])
        assert validate(manager,raw,hashlib.sha256(raw).hexdigest())['ordinal_names_verified']==512+extra
        checked.append(512+extra)
    manager=baseline+b''.join(pc_record(f'MOD_{i}') for i in range(5))
    raw=fixture(base_names+[f'MOD_{i}' for i in range(5)])
    bads=[raw[:-1], raw+b'X', fixture(base_names), b'', raw[:67]]
    names=base_names+[f'MOD_{i}' for i in range(5)]
    reordered=names[:];reordered[512],reordered[513]=reordered[513],reordered[512]
    bads.append(fixture(reordered))
    reordered=names[:];reordered[1],reordered[2]=reordered[2],reordered[1]
    bads.append(fixture(reordered))
    duplicate=names[:];duplicate[516]=duplicate[515];bads.append(fixture(duplicate))
    start=binary_chunks(raw)[0][1]
    b=bytearray(raw);struct.pack_into('<I',b,start+4,0xffffffff);bads.append(bytes(b))
    b=bytearray(raw);b[start+8:start+72]=b'X'*64;bads.append(bytes(b))
    b=raw.replace(b'conditionprm\0',b'wrong_name__\0',1);bads.append(b)
    for b in bads:
        try:validate(manager,b,hashlib.sha256(b).hexdigest())
        except ValueError:pass
        else:raise AssertionError('invalid companion accepted')
    for h in ['0'*64, '', None, 'A'*64]:
        try:validate(manager,raw,h)
        except ValueError:pass
        else:raise AssertionError('bad hash accepted')
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);m=td/'manager';r=td/'raw';m.write_bytes(manager);r.write_bytes(raw)
        args=[sys.executable,str(R/'tools/compile_condition_profile.py'),'--param',str(m),'--raw-condition',str(r),'--expected-raw-sha256',hashlib.sha256(raw).hexdigest()]
        subprocess.run(args+['--output',str(td/'ok')],check=True)
        assert (td/'ok/conditionprm.COMPANION_NOT_GAMEPLAY_RELEASE.xfbin').read_bytes()==raw
        report=json.loads((td/'ok/condition_profile_report.json').read_text())
        assert report['companion']['ordinal_names_verified']==517 and not report['raw_conditionprm_packaged']
        # Correct SHA of a wrong-order file must still fail before output exists.
        r.write_bytes(bads[5]);args[-1]=hashlib.sha256(bads[5]).hexdigest()
        fail=subprocess.run(args+['--output',str(td/'bad')],capture_output=True)
        assert fail.returncode and not (td/'bad').exists()
        assert m.read_bytes()==manager and r.read_bytes()==bads[5]
        # Existing output is never overwritten.
        old=(td/'ok/condition.profile').read_bytes();r.write_bytes(raw);args[-1]=hashlib.sha256(raw).hexdigest()
        fail=subprocess.run(args+['--output',str(td/'ok')],capture_output=True)
        assert fail.returncode and (td/'ok/condition.profile').read_bytes()==old
    result={'status':'PASS','valid_counts':checked,'malformed_or_wrong_order_companions_rejected':len(bads),
            'invalid_hashes_rejected':4,'cli_rejects_before_output':True,'source_and_existing_output_preserved':True,
            'copied_companion_byte_identical':True,'gameplay_verified':False,'raw_value_semantics_verified':False}
    output.mkdir(parents=True,exist_ok=True);(output/'condition_companion.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
