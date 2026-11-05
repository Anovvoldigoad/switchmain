"""Offline stock/candidate CPK source/entry/ordinal audit regression."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from native_condition_fixture import baseline_from_main,pc_record
from test_condition_companion import fixture
from test_cpk_events import cpk
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.condition_archive_audit import inspect
from portlib.condition_bundle import ENTRY


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(main, output):
    baseline,_=baseline_from_main(main)
    names=[baseline[i:i+48].split(b'\0',1)[0].decode()
           for i in range(0,len(baseline),112)]
    manager=baseline+pc_record('TEST_APPEND')
    stock_raw=fixture(names)
    cand_raw=fixture(names+['TEST_APPEND'])
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);stock=td/'stock.cpk';candidate=td/'candidate.cpk';m=td/'manager'
        a=cpk([(ENTRY,stock_raw),('data/test/stock',b'other')])
        b=cpk([(ENTRY,cand_raw),('data/test/candidate',b'other')])
        stock.write_bytes(a);candidate.write_bytes(b);m.write_bytes(manager)
        report=inspect(manager,stock,sha(a),candidate,sha(b))
        assert report['stock_rows']==512 and report['candidate_rows']==513
        assert not report['changed_prefix_rows']
        assert report['stock_archive']['raw_xfbin_sha256']==sha(stock_raw)
        assert report['candidate_archive']['raw_xfbin_sha256']==sha(cand_raw)
        assert len(report['appended_record_hashes'])==1
        assert not report['cpk_archive_winner_verified']
        cmd=[sys.executable,str(R/'tools/audit_condition_cpk_pair.py'),
             '--pc-manager',str(m),'--stock-cpk',str(stock),'--stock-cpk-sha256',sha(a),
             '--candidate-cpk',str(candidate),'--candidate-cpk-sha256',sha(b),
             '--output',str(td/'ok')]
        subprocess.run(cmd,check=True,capture_output=True)
        result=json.loads((td/'ok/condition_cpk_pair_audit.json').read_text())
        assert result['stock_archive']['cpk_entry_id']==report['stock_archive']['cpk_entry_id']
        bad_cmd=cmd.copy();bad_cmd[bad_cmd.index('--stock-cpk-sha256')+1]='0'*64
        bad_cmd[-1]=str(td/'invalid')
        assert subprocess.run(bad_cmd,capture_output=True).returncode and not (td/'invalid').exists()
        attempts=[
            (manager,stock,sha(a),candidate,'0'*64),
            (manager,stock,sha(a),candidate,'A'*64),
            (manager,stock,sha(a),stock,sha(a)),
            (manager,stock,sha(a),td/'missing.cpk',sha(b)),
        ]
        bad=0
        for args in attempts:
            try:inspect(*args)
            except ValueError:bad+=1
            else:raise AssertionError('invalid archive pair accepted')
        # Correct hash is insufficient without actual companion entry and count.
        wrong=cpk([('data/other/data.bin',b'opaque')]);candidate.write_bytes(wrong)
        try:inspect(manager,stock,sha(a),candidate,sha(wrong))
        except ValueError:bad+=1
        else:raise AssertionError('missing companion accepted')
        wrong=cpk([(ENTRY,b'CRILAYLA'+cand_raw)])
        candidate.write_bytes(wrong)
        try:inspect(manager,stock,sha(a),candidate,sha(wrong))
        except ValueError:bad+=1
        else:raise AssertionError('compressed companion accepted')
        assert bad==6
    output.mkdir(parents=True,exist_ok=True)
    summary={'status':'PASS_SYNTHETIC','source_archive_hashes_verified':True,
             'actual_companion_extracted_from_cpk':True,
             'stock_records':512,'synthetic_candidate_records':513,
             'rejected_bad_pairs':bad,
             'real_stock_switch_archive_tested':False,
             'source_provenance_verified':False,
             'effect_semantics_verified':False,
             'gameplay_verified':False}
    (output/'condition_archive_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
