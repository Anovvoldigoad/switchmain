"""Verify direct branch decoder and scan of exact SHA-pinned main text."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.native_cpk_graph import analyze,direct_branch,ANCHORS


def run(main,out):
    assert direct_branch(0xD503201F,0x100) is None
    assert direct_branch(0x94000008,0x100)==('BL',0x120)
    assert direct_branch(0x17FFFFF8,0x100)==('B',0xE0)
    assert direct_branch(0x97FFFFF8,0x100)==('BL',0xE0)
    original=main.read_bytes()
    report=analyze(original)
    assert len(report['anchors'])==len(ANCHORS)
    assert all(a['name'] in ANCHORS and a['first_word_le'] for a in report['anchors'])
    assert report['text_bytes_scanned']>max(ANCHORS.values())+0x100
    assert report['candidate_direct_branches']>0
    assert not report['native_abi_or_lifecycle_established']
    assert not report['async_completion_verified']
    assert not report['gameplay_verified']
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);file=d/'main';file.write_bytes(original)
        cmd=[sys.executable,str(R/'tools/audit_native_cpk_graph.py'),
             '--main',str(file),'--output',str(d/'edges')]
        subprocess.run(cmd,check=True,capture_output=True)
        cli=json.loads((d/'edges/native_cpk_call_edges.json').read_text())
        assert cli==report
        wrong=bytearray(original);wrong[256]^=1
        try:analyze(bytes(wrong))
        except ValueError:pass
        else:raise AssertionError('Unpinned main image accepted')
        file.write_bytes(wrong)
        bad=subprocess.run([*cmd[:-1],str(d/'invalid')],capture_output=True)
        assert bad.returncode and not (d/'invalid').exists()
    out.mkdir(parents=True,exist_ok=True)
    report['real_main_image_pinned']=True
    (out/'native_cpk_call_edges.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CPK native static call edges inspected:',report['candidate_direct_branches'],
          'candidate instructions,',len(ANCHORS),'anchor windows. NOT runtime proof.')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--main',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    run(a.main,a.output)
