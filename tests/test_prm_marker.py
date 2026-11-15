"""Structural PRM conversion and negative-input checks, independent of gameplay."""
import argparse,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.prm_events import mark,records,binary_chunks,MARKER


def event(op,name=b'',event_id=236,width=64):
    b=bytearray(width);b[:len(name)]=name
    struct.pack_into('<Hhhh',b,34,event_id,op,0,0)
    return bytes(b)


def fixture(events):
    payload=bytearray(68+212);payload[4:12]=b'ver0.000'
    struct.pack_into('<I',payload,52,1);payload[68:80]=b'PL_ANM_TEST\0'
    struct.pack_into('<I',payload,68+80,len(events))
    payload+=b''.join(events);struct.pack_into('>I',payload,0,len(payload)-4)
    types=b'nuccChunkBinary\0nuccChunkPage\0';paths=b'\0';names=b'testprm_mot\0page\0'
    header=bytearray(68);header[:4]=b'NUCC';struct.pack_into('>I',header,4,121)
    struct.pack_into('>10I',header,28,2,len(types),1,len(paths),2,len(names),2,24,2,0)
    header+=types+paths+names;header+=bytes((-len(header))%4)
    header+=struct.pack('>6I',0,0,0,1,0,1)+struct.pack('>2I',0,1)
    header+=struct.pack('>IIHH',len(payload),0,121,0)+payload
    header+=struct.pack('>IIHHII',8,1,121,0,2,0)
    return bytes(header)


def run(out):
    # Sound strings containing DMG must NOT be mistaken for damage extensions.
    raw=fixture([event(26,b'S_PL_DMG_cmn_vS_rv'),event(3),event(0),event(1,event_id=94,width=160),event(-1)])
    parsed=records(raw);assert len(parsed)==5 and [x['size'] for x in parsed]==[64,64,64,160,64]
    changed,report=mark(raw);assert report['marked_records']==2 and report['native_event236_preserved']==2
    again,repeat=mark(changed);assert again==changed and repeat['already_marked']==2 and repeat['marked_records']==0
    allowed={r['offset']+i for r in parsed[:2] for i in [42,43]}
    assert {i for i in range(len(raw)) if raw[i]!=changed[i]}==allowed
    rejected=0
    bads=[b'',raw[:67],raw[:-1],raw+b'\0']
    for off,value in [(28,0xffffffff),(64,0xffffffff)]:
        b=bytearray(raw);struct.pack_into('>I',b,off,value);bads.append(bytes(b))
    start=binary_chunks(raw)[0][1]
    for off,fmt,value in [(start,'>I',0),(start+52,'<I',0xffffffff),(start+68+80,'<I',0xffffffff),
                          (parsed[0]['offset']+42,'<H',0x1234),(parsed[2]['offset']+42,'<H',MARKER)]:
        b=bytearray(raw);struct.pack_into(fmt,b,off,value);bads.append(bytes(b))
    b=bytearray(raw);b[start+4:start+12]=b'ver9.999';bads.append(bytes(b))
    for b in bads:
        try:mark(b)
        except ValueError:rejected+=1
        else:raise AssertionError('Malformed PRM accepted')
    result={'status':'PASS','malformed_inputs_rejected':rejected,'marked_records':2,
            'native_records_unchanged':3,'idempotent':True,'sound_string_not_used_as_record_size':True,
            'gameplay_verified':False}
    out.mkdir(parents=True,exist_ok=True);(out/'prm_marker.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
