"""Pinned v1.70 code relocation cluster grouping and read-only rejection tests."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.native_cpk_pointer_tables import inspect, WITNESSES, MAIN_SHA256


def run(main,out):
    raw=main.read_bytes()
    audit=inspect(raw)
    assert audit['main_sha256']==MAIN_SHA256
    assert len(audit['known_witnesses'])==4
    assert all(w['observed_in_adjacent_cluster'] for w in audit['known_witnesses'])
    assert audit['nearby_candidate_clusters']>=1
    assert audit['candidate_clusters_returned']>=1
    assert not audit['native_abi_verified']
    assert not audit['CRI_async_completion_verified']
    assert not audit['gameplay_verified']
    grouped={
        int(e['relocation_slot'],16):int(e['code_addend'],16)
        for group in audit['clusters'] for e in group['reported_members']
    }
    # Only require evidence that is known to be in the original pinned image;
    # a truncated report can still show the pinned witnesses in a different cluster.
    assert any(int(w['slot'],16) in WITNESSES for w in audit['known_witnesses'])
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);f=td/'main';f.write_bytes(raw)
        cmd=[sys.executable,str(R/'tools/audit_native_cpk_pointer_tables.py'),
             '--main',str(f),'--output',str(td/'good')]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((td/'good/native_cpk_pointer_candidates.json').read_text())==audit
        changed=bytearray(raw);changed[255]^=1;f.write_bytes(changed)
        cmd[cmd.index('--output')+1]=str(td/'rejected')
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (td/'rejected').exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/'native_cpk_pointer_candidates.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('PINNED_CPK_POINTER_CLUSTERS',audit['nearby_candidate_clusters'],
          'reported',audit['candidate_clusters_returned'],
          'known_witnesses',audit['known_witnesses'],
          'native_vtable_abi=UNKNOWN')
    for g in audit['clusters'][:6]:
        print('PINNED_CPK_POINTER_GROUP',g['first_slot'],g['contiguous_relocated_slot_count'],
              g['reported_members'][:12])


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
