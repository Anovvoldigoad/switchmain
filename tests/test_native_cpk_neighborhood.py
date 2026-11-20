"""Pinned main near-anchor B/BL incoming + bounded indirect sites, read-only."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.native_cpk_neighborhood import inspect,indirect_kind,WINDOWS


def run(main,out):
    assert indirect_kind(0xD63F0100)=='BLR'
    assert indirect_kind(0xD61F0100)=='BR'
    assert indirect_kind(0xD65F03C0)=='RET'
    assert indirect_kind(0xD503201F) is None
    assert indirect_kind(0x94000000) is None
    original=main.read_bytes()
    result=inspect(original)
    assert result['status']=='PINNED_STATIC_NEARBY_TARGET_CENSUS_ONLY'
    assert result['main_sha256']=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
    assert len(result['regions'])==len(WINDOWS)
    assert result['source_relocation_records']>1000
    for w in result['regions']:
        assert w['radius_bytes']==WINDOWS[w['name']][1]
        assert w['nearby_indirect_branch_count']>=0
        assert not w['nearby_branch_sites_are_not_callers_of_anchor'] is False
    assert not result['CRI_async_completion_verified']
    assert not result['gameplay_verified']
    with tempfile.TemporaryDirectory() as tmp:
        td=Path(tmp);source=td/'main';source.write_bytes(original)
        cmd=[sys.executable,str(R/'tools/audit_native_cpk_neighborhood.py'),
             '--main',str(source),'--output',str(td/'good')]
        subprocess.run(cmd,capture_output=True,check=True)
        assert json.loads((td/'good/native_cpk_neighborhood.json').read_text())==result
        changed=bytearray(original);changed[260]^=1;source.write_bytes(changed)
        bad=[*cmd[:-1],str(td/'bad')]
        assert subprocess.run(bad,capture_output=True).returncode
        assert not (td/'bad').exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/'native_cpk_neighborhood.json').write_text(json.dumps(result,indent=2)+'\n')
    for w in result['regions']:
        print('NATIVE_NEARBY',w['name'],'incoming',w['incoming_counts'],
              'top_targets',w['common_nearby_direct_targets'][:6],
              'indirect_branch_sites',w['nearby_indirect_branch_sites'][:4],
              'reloc_addends',w['relative_relocation_addend_samples'][:4])
    print('PASS_STATIC_NEARBY_CANDIDATES_ONLY. NO CRI runtime, unbind or gameplay evidence.')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
