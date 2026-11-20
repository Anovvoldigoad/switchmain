"""Synthetic raw176 byte-diff proof and strict CLI rejection regression."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from native_condition_fixture import baseline_from_main, pc_record
from test_condition_companion import fixture
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools'))
from portlib.condition_raw_audit import compare, _records
from portlib.prm_events import binary_chunks


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(main, output):
    baseline, _ = baseline_from_main(main)
    names = [baseline[i:i+48].split(b'\0', 1)[0].decode('ascii')
             for i in range(0, len(baseline), 112)]
    manager = baseline + pc_record('MOD_NEW')
    stock = fixture(names)
    mod = bytearray(fixture(names+['MOD_NEW']))
    start = binary_chunks(mod)[0][1]
    # Deliberate byte modifications; no fabricated effect field interpretation.
    mod[start+8+103*176+64+13] = 0x7f
    mod[start+8+512*176+64+5] = 0x3a
    mod = bytes(mod)
    result = compare(manager, stock, sha(stock), mod, sha(mod))
    assert result['verified_shared_ordinals'] == 512
    assert result['candidate_rows'] == 513
    assert result['changed_prefix_row_count'] == 1
    assert result['changed_prefix_rows'][0]['ordinal'] == 103
    assert result['changed_prefix_rows'][0]['record_offsets'] == [77]
    assert result['appended_record_hashes'][0]['name'] == 'MOD_NEW'
    assert not result['stock_value_bytes_identical'] and not result['gameplay_verified']
    baseline_check = compare(baseline, stock, sha(stock), stock, sha(stock))
    assert baseline_check['stock_value_bytes_identical']
    assert baseline_check['changed_prefix_rows'] == []
    errors = 0
    bads = [
        (manager, stock, '0'*64, mod, sha(mod)),
        (manager, stock, sha(stock), mod, '0'*64),
        (manager, fixture(names+['MOD_NEW']), sha(fixture(names+['MOD_NEW'])), mod, sha(mod)),
        (manager, stock, sha(stock), fixture(names), sha(fixture(names))),
        (manager, b'', sha(b''), mod, sha(mod)),
        (baseline, stock, sha(stock), mod, sha(mod)),
    ]
    reorder = names[:]
    reorder[0], reorder[1] = reorder[1], reorder[0]
    wrongly_ordered = fixture(reorder)
    bads.append((manager, wrongly_ordered, sha(wrongly_ordered), mod, sha(mod)))
    for args in bads:
        try: compare(*args)
        except ValueError: errors += 1
        else: raise AssertionError('Malformed raw comparison accepted')
    assert errors == len(bads)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        m = d/'manager'; s = d/'stock'; c = d/'candidate'
        m.write_bytes(manager); s.write_bytes(stock); c.write_bytes(mod)
        argv = [sys.executable, str(R/'tools/audit_condition_raw_values.py'),
                '--pc-manager', str(m), '--stock-raw', str(s),
                '--expected-stock-sha256', sha(stock), '--candidate-raw', str(c),
                '--expected-candidate-sha256', sha(mod), '--output', str(d/'ok')]
        subprocess.run(argv, check=True, capture_output=True)
        cli_result = json.loads((d/'ok/condition_raw_value_audit.json').read_text())
        assert cli_result['changed_prefix_rows'] == result['changed_prefix_rows']
        assert not cli_result['input_origin_verified']
        argv[-1] = str(d/'blocked')
        argv[argv.index('--expected-stock-sha256')+1] = '0'*64
        failed = subprocess.run(argv, capture_output=True)
        assert failed.returncode != 0 and not (d/'blocked').exists()
        assert s.read_bytes() == stock and c.read_bytes() == mod
    output.mkdir(parents=True, exist_ok=True)
    summary = {'status': 'PASS', 'synthetic_prefix_changed_rows': 1,
               'synthetic_appended_rows': 1, 'rejections': errors,
               'cli_rejects_before_output': True, 'stock_value_semantics_verified': False,
               'real_switch_raw_input_tested': False, 'gameplay_verified': False}
    (output/'condition_raw_value_audit.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run(a.main, a.output)
