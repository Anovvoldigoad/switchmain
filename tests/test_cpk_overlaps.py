"""Real Python CPK parser, mmap source hashes and fail-closed overlap tests."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from test_cpk_events import cpk
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools'))
from portlib.cpk_overlap import inspect


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(out):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        first = cpk([('data/spc/conditionprm.bin.xfbin', b'RAW0'),
                     ('data/spc/shared.xfbin', b'SAME'),
                     ('data/spc/case.xfbin', b'CASE')])
        second = cpk([('data/spc/conditionprm.bin.xfbin', b'RAW1'),
                      ('data/spc/shared.xfbin', b'SAME'),
                      ('data/spc/Case.xfbin', b'CASE')])
        paths = [root/'A.cpk', root/'B.cpk']
        for p, b in zip(paths, [first, second]):
            p.write_bytes(b)
        rows = [
            {'source': str(paths[0]), 'path': 'sim:data/moddingapi/A.cpk',
             'priority': 5, 'sha256': sha(first)},
            {'source': str(paths[1]), 'path': 'sim:data/moddingapi/B.cpk',
             'priority': 6, 'sha256': sha(second)}
        ]
        result = inspect({'archives': rows})
        assert result['overlapping_paths'] == 3
        assert result['divergent_or_unresolved_paths'] == 2
        assert result['condition_companion_overlap']
        overlap = {r['path_casefold']:r for r in result['collisions']}
        assert overlap['data/spc/shared.xfbin']['uncompressed_content_identical']
        assert not overlap['data/spc/shared.xfbin']['requires_manual_resolution']
        assert not overlap['data/spc/conditionprm.bin.xfbin']['stored_bytes_identical']
        assert overlap['data/spc/case.xfbin']['stored_bytes_identical']
        assert not overlap['data/spc/case.xfbin']['exact_case_match']
        assert not result['effective_archive_winner_verified']
        assert not result['gameplay_verified']
        assert inspect({'archives':rows[:1]})['overlapping_paths'] == 0
        m = root/'manifest.json'
        m.write_text(json.dumps({'archives':rows}))
        cli = [sys.executable, str(R/'tools/audit_cpk_overlaps.py'),
               '--manifest',str(m),'--output',str(root/'review')]
        subprocess.run(cli, check=True, capture_output=True)
        report = json.loads((root/'review/cpk_overlap_report.json').read_text())
        assert report['divergent_or_unresolved_paths'] == 2
        strict = cli[:-1]+[str(root/'blocked'),'--reject-unresolved']
        assert subprocess.run(strict, capture_output=True).returncode
        assert not (root/'blocked').exists()
        rejects = 0
        wrong = [dict(rows[0], sha256='0'*64), dict(rows[0], priority=True),
                 dict(rows[0], source=str(root/'missing.cpk')),
                 dict(rows[0], path='sim:data/moddingapi/../A.cpk')]
        for bad in wrong:
            try:inspect({'archives':[bad]})
            except ValueError: rejects += 1
            else:raise AssertionError('invalid manifest accepted')
        for cfg in [
            {'archives':rows+[dict(rows[0],source=str(paths[1]),sha256=sha(second))]},
            {'archives':[rows[0],dict(rows[1],priority=5)]},
            {'archives':[dict(rows[0],sha256=sha(second))]},
            {'archives':[]}, [], {'wrong':rows}, {'archives':'bad'}]:
            try:inspect(cfg)
            except ValueError: rejects += 1
            else:raise AssertionError('invalid manifest accepted')
        assert rejects == 11
        assert paths[0].read_bytes()==first and paths[1].read_bytes()==second
    out.mkdir(parents=True,exist_ok=True)
    summary = {'status':'PASS_SYNTHETIC',
               'archives':2, 'overlapping_paths':3, 'unresolved':2,
               'malformed_manifests_rejected':rejects,
               'exact_case_and_casefold_distinguished':True,
               'same_stored_content_distinguished':True,
               'condition_companion_collision_visible':True,
               'strict_failure_before_output':True,
               'archive_priority_winner_verified':False,
               'real_game_archives_tested':False,'gameplay_verified':False}
    (out/'cpk_overlaps.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    run(args.output)
