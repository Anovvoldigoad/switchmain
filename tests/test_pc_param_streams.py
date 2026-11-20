"""Test source-grounded PC parameter parsing with exact public NSC templates."""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.pc_param_streams import inspect, SOURCE, MAX_INPUT_BYTES


def sha(b):return hashlib.sha256(b).hexdigest()


def run(out):
    fixtures={
        'ougiAwakeningParam':('NSC_ougiAwakeningParam.raw.bin','091143ccde86ef2a8ecd0c33aa3485726f67f7ab',4),
        'gudoBallParam':('NSC_gudoBallParam.raw.bin','934435c5a1e58a1040d62976ff32affd6383e239',8),
        'charRelationParam':('NSC_charRelationParam.raw.bin','6e680f5c919af3536cc38f8b14fe8138a601770f',548)
    }
    hashed={}
    for family,(name,blob_hash,expected_length) in fixtures.items():
        data=(R/'tests/fixtures/pc_source'/name).read_bytes()
        assert len(data)==expected_length
        actual_git=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert actual_git==blob_hash
        report=inspect(data,family,sha(data))
        assert report['family']==family
        assert report['record_count']>=1
        assert not report['native_Switch_v170_reader_integrated']
        hashed[family]={'git_blob':actual_git,'sha256':sha(data),
                        'records':report['record_count'],
                        'bytes':len(data)}
        print('PINNED_PC_STREAM',family,'blob',actual_git,
              'sha256',sha(data),'rows',report['record_count'],
              'Switch_gameplay=UNVERIFIED')
    # Source faithfully uses 32-bit values, accepts duplicate list IDs,
    # and preserves empty relation records.
    u=struct.pack('<IIII',0x12345678,0xDEADBEEF,0x12345678,0)
    a=inspect(u,'ougiAwakeningParam',sha(u))
    assert a['record_count']==4 and a['unique_character_ids']==3
    assert a['duplicate_occurrences_preserved_in_order']==1
    assert a['records'][1]['character_id_u32']==0xDEADBEEF
    relation=struct.pack('<IIIIII',0,2,0x123,0x456,1,0xABCD)
    b=inspect(relation,'charRelationParam',sha(relation))
    assert [z['id_count'] for z in b['records']]==[0,2,1]
    assert b['records'][2]['character_ids_u32']==[0xABCD]
    reject=[
        ('ougiAwakeningParam',b'',sha(b'')),
        ('gudoBallParam',u+b'\0',sha(u+b'\0')),
        ('charRelationParam',struct.pack('<I',4),sha(struct.pack('<I',4))),
        ('charRelationParam',struct.pack('<II',1,42)+b'\0',sha(struct.pack('<II',1,42)+b'\0')),
        ('charRelationParam',struct.pack('<I',0xFFFFFFFF),sha(struct.pack('<I',0xFFFFFFFF))),
        ('ougiAwakeningParam',u,'0'*64),
        ('gudoBallParam',u,sha(u).upper()),
        ('unknown',u,sha(u)),
        ('ougiAwakeningParam',b'\x01\0\0\0'*(MAX_INPUT_BYTES//4+1),
         sha(b'\x01\0\0\0'*(MAX_INPUT_BYTES//4+1))),
    ]
    rejected=0
    for family,raw,digest in reject:
        try:inspect(raw,family,digest)
        except ValueError:rejected+=1
        else:raise AssertionError('Invalid PC stream accepted')
    assert rejected==len(reject)
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);src=temp/'input';src.write_bytes(relation)
        cmd=[sys.executable,str(R/'tools/audit_pc_parameter_streams.py'),
             '--family','charRelationParam','--input',str(src),
             '--expected-sha256',sha(relation),'--output',str(temp/'good')]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((temp/'good/pc_parameter_stream_audit.json').read_text())==b
        cmd[cmd.index('--expected-sha256')+1]='0'*64
        cmd[cmd.index('--output')+1]=str(temp/'bad')
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (temp/'bad').exists()
        assert src.read_bytes()==relation
    out.mkdir(parents=True,exist_ok=True)
    result={
        'status':'PASS_PC_REAL_PUBLIC_TEMPLATES_AND_SYNTHETIC_NEGATIVE_TESTS',
        'source_repo':'TheLeonX/NSC-ModManager',
        'source_ref':'276116ebf5ba398a867793cb02ee6c33c0927645',
        'upstream_readers':'TheLeonX/UltimateStormAPI @ a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc',
        'verified_templates':hashed,
        'invalid_cases_rejected':rejected,
        'native_Switch_runtime_untested':True,
        'gameplay_verified':False,'full_moddingapi':False}
    (out/'pc_param_streams.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS authentic PC stream templates',len(hashed),'rejects',rejected,
          'Switch hooks unavailable.')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.output)
