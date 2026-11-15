"""Pinned PC source raw32 schemas: exact widths, hash gate and fail-closed types."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.pc_param_rows import inspect,PARTNER,SUSANOO


def sha(b):
    return hashlib.sha256(b).hexdigest()


def row(name,id,opaque=b'\0'*6,pad_byte=0):
    assert len(opaque)==6
    data=bytearray(32)
    name=name.encode('ascii')
    assert len(name)<24
    data[:len(name)]=name
    data[len(name)]=0
    if pad_byte:data[23]=pad_byte
    data[24:26]=id.to_bytes(2,'little')
    data[26:32]=opaque
    return bytes(data)


def run(out):
    a=row('SSN_2ITC',0x1234,b'\x01\x02\x03\x04\x05\x06',3)
    b=row('SSN_BSSZ',0x5ee0)
    partner=row('PARTNER_TYPE_2PAR',0xBEEF)+row('PARTNER_TYPE_8AEM',0xFEDC)
    p=inspect(a+b,'susanooCondParam',sha(a+b))
    assert p['record_count']==2 and p['rows'][0]['character_id_u16']==0x1234
    assert p['rows'][0]['pc_source_associated_selector']==0x19
    assert p['rows'][0]['name_padding_contains_nonzero']
    assert p['rows'][1]['pc_source_associated_selector']==0xc1
    assert p['bytes_after_character_id_opaque']
    assert p['source_blob_sha']=='f738deb9b6bf93221ba6855bdd59552f43e8f0ae'
    q=inspect(partner,'partnerSlotParam',sha(partner))
    assert q['record_count']==2 and q['rows'][0]['pc_source_associated_selector']==0x2B
    assert q['rows'][1]['pc_source_associated_selector']==0xE6
    assert q['source_blob_sha']=='ce8978d8b01998d8c16b00fb434cbe4ee8c62fdd'
    assert len(PARTNER)==8 and len(SUSANOO)==5
    bads=[
        ('susanooCondParam',a+b,'0'*64),
        ('susanooCondParam',a+b,sha(a+b).upper()),
        ('susanooCondParam',a+b,sha(a)),
        ('susanooCondParam',a+b+b'\0',sha(a+b+b'\0')),
        ('susanooCondParam',b'',sha(b'')),
        ('susanooCondParam',a+row('SSN_3SSK',0x1234),sha(a+row('SSN_3SSK',0x1234))),
        ('susanooCondParam',row('SSN_UNKNOWN',0x1234),sha(row('SSN_UNKNOWN',0x1234))),
        ('partnerSlotParam',row('SSN_2ITC',1),sha(row('SSN_2ITC',1))),
        ('susanooCondParam',bytes(24)+bytes(8),sha(bytes(32))),
        ('bogus',a,sha(a)),
    ]
    rejected=0
    for family,raw,digest in bads:
        try:inspect(raw,family,digest)
        except ValueError:rejected+=1
        else:raise AssertionError('Invalid PC raw32 table accepted')
    assert rejected==len(bads)
    # Exact public PC manager templates from TheLeonX/NSC-ModManager pinned
    # commit 276116ebf5ba398a867793cb02ee6c33c0927645.
    template_hashes={}
    fixtures=[
        ('susanooCondParam','NSC_susanooCondParam.raw32.bin',
         'd983860d4bbaa58440ea1b3ba2b6e6e33fa48b17',5),
        ('partnerSlotParam','NSC_partnerSlotParam.raw32.bin',
         '8155d1e0a76add995051b45fe68d27f19cca49dc',8)]
    for family,filename,blob_sha,expected_rows in fixtures:
        source=(R/'tests/fixtures/pc_source'/filename).read_bytes()
        calculated_blob=hashlib.sha1(
            b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()
        assert calculated_blob==blob_sha
        result=inspect(source,family,sha(source))
        assert result['record_count']==expected_rows
        assert not result['switch_v170_reader_integrated']
        template_hashes[family]=sha(source)
        print('PC_UPSTREAM_TEMPLATE',family,
              'git_blob',blob_sha,'sha256',sha(source),
              'records',expected_rows,'Switch_native_runtime=UNVERIFIED')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        file=root/'pc.bin';file.write_bytes(partner)
        cmd=[sys.executable,str(R/'tools/audit_pc_parameter_rows.py'),
             '--family','partnerSlotParam','--input',str(file),
             '--expected-sha256',sha(partner),'--output',str(root/'valid')]
        subprocess.run(cmd,check=True,capture_output=True)
        report=json.loads((root/'valid/pc_parameter_audit.json').read_text())
        assert report['source_data_sha256']==sha(partner)
        assert not report['switch_v170_reader_integrated']
        bad=cmd.copy();bad[bad.index('--expected-sha256')+1]='0'*64
        bad[bad.index('--output')+1]=str(root/'rejected')
        assert subprocess.run(bad,capture_output=True).returncode and not (root/'rejected').exists()
        assert file.read_bytes()==partner
    out.mkdir(parents=True,exist_ok=True)
    result={'status':'PASS_PC_SOURCE_FORMAT_SYNTHETIC',
            'families':['susanooCondParam','partnerSlotParam'],
            'record_size':32,'name_bytes':24,'character_id_offset':24,
            'unmodified_opaque_tail_preserved':True,
            'rejected_invalid_cases':rejected,
            'actual_PC_mod_sample_tested':False,
            'authentic_public_PC_manager_templates_tested':True,
            'public_template_sha256':template_hashes,
            'switch_native_parameter_reader_integrated':False,
            'gameplay_verified':False,'full_moddingapi':False}
    (out/'pc_param_rows.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PC raw32 source-format tests PASS:',rejected,
          'malformed inputs rejected. Switch reader NOT integrated.')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.output)
