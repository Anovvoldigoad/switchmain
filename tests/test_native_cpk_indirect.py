"""Check exact ARM64 address decoders and read-only native-image pointer references."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.native_cpk_indirect import (
    inspect, adr_target, adrp_page, adrp_add_target, adrp_ldr_slot, ldr_literal_slot)
from portlib.native_cpk_graph import ANCHORS


def encode_adrp(pc,target,rd=5):
    pages=(target & ~0xfff)-(pc & ~0xfff)
    assert pages%4096==0
    value=(pages//4096)&0x1fffff
    return 0x90000000 | ((value&3)<<29) | ((value>>2)<<5) | rd


def run(main,out):
    target=ANCHORS['fileload_process']
    pc=0x4000;reg=5
    adrp=encode_adrp(pc,target,reg)
    add=0x91000000 | ((target&4095)<<10) | (reg<<5) | reg
    assert adrp_page(adrp,pc)==target&~4095
    assert adrp_add_target(adrp,add,pc)==target
    assert adrp_add_target(adrp,add^1,pc) is None
    assert adrp_add_target(0xD503201F,add,pc) is None
    assert adrp_add_target(adrp,0xD503201F,pc) is None
    assert adrp_page(encode_adrp(0x1200000,0x106f000),0x1200000)==0x106f000
    slot=(target&~4095)+40
    ldr=0xf9400000 | (5<<10) | (reg<<5)|2
    assert adrp_ldr_slot(adrp,ldr,pc)==slot
    assert adrp_ldr_slot(adrp,ldr^(1<<5),pc) is None
    assert adr_target(0x10000100,0x100)==0x120
    assert adr_target(0xd503201f,0x100) is None
    assert ldr_literal_slot(0x58000100,0x100)==0x120
    assert ldr_literal_slot(0xD503201F,0x100) is None
    raw=main.read_bytes()
    report=inspect(raw)
    assert report['main_sha256']=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
    assert len(report['anchors'])==len(ANCHORS)
    assert report['relocation_record_count']>=report['relative_relocation_record_count']>0
    assert not report['indirect_calls_fully_resolved']
    assert not report['gameplay_verified']
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)
        p=d/'main';p.write_bytes(raw)
        cmd=[sys.executable,str(R/'tools/audit_native_cpk_indirect.py'),
             '--main',str(p),'--output',str(d/'good')]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((d/'good/native_cpk_indirect_refs.json').read_text())==report
        damaged=bytearray(raw);damaged[256]^=1;p.write_bytes(damaged)
        bad=subprocess.run([*cmd[:-1],str(d/'wrong')],capture_output=True)
        assert bad.returncode and not (d/'wrong').exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/'native_cpk_indirect_refs.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS_PINNED_STATIC CPK indirect references, anchors',len(report['anchors']),
          'relocations',report['relocation_record_count'],
          'function pointers not runtime call proof')
    for entry in report['anchors']:
        types=entry['direct_code_address_materializations']
        slots=entry['load_relocation_slot_candidates']
        print('CPK_INDIRECT_PINNED',entry['name'],
              'relative_relocation_slots',entry['relative_relocation_slots'][:8],
              'adr',types['adr'][:8],
              'adrp_add',types['immediately_adjacent_adrp_add'][:8],
              'adrp_ldr',slots['immediately_adjacent_adrp_ldr'][:8],
              'literal_ldr',slots['literal_ldr'][:8],
              'not_runtime_proof=1')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--main',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    run(a.main,a.output)
