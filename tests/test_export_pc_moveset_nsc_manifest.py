"""Verified PC editor index conversion, not binary moveset conversion."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from export_pc_moveset_nsc_manifest import convert
from pc_moveset_event_preflight import audit


class ExportPCMovesetIndex(unittest.TestCase):
    def test_full_shared_ns4_range_and_nsc_tail(self):
        for version, count in [('ns4', 289), ('nsc', 300)]:
            raw = json.dumps({'source_version': version, 'events': [
                {'event_id': 'e' + str(i), 'function_index': i} for i in range(count)]}).encode()
            output, evidence = convert(raw, hashlib.sha256(raw).hexdigest())
            result = json.loads(output)
            self.assertEqual(result['source_version'], 'nsc')
            self.assertEqual([r['function_index'] for r in result['events']], list(range(count)))
            self.assertEqual(audit(result)['event_count'], count)
            self.assertEqual(hashlib.sha256(output).hexdigest(), evidence['output_sha256'])
            self.assertFalse(evidence['native_switch_abi_verified'])
            self.assertFalse(evidence['binary_layout_verified'])

    def test_wrong_hash_and_invalid_events_fail_closed(self):
        valid = json.dumps({'source_version': 'ns4', 'events': [
            {'event_id': 'a', 'function_index': 0}]}).encode()
        for raw, sha in [(valid, '0' * 64), (valid, 'bad'),
                         (valid, hashlib.sha256(valid).hexdigest()[:-1] + 'z')]:
            with self.assertRaises(ValueError):
                convert(raw, sha)
        for events in [[{'event_id': 'x', 'function_index': 289}],
                       [{'event_id': 'x', 'function_index': True}],
                       [{'event_id': 'x', 'function_index': 1}, {'event_id': 'x', 'function_index': 2}]]:
            raw = json.dumps({'source_version': 'ns4', 'events': events}).encode()
            with self.assertRaises(ValueError):
                convert(raw, hashlib.sha256(raw).hexdigest())

    def test_cli_exact_bytes_and_existing_output_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            raw = json.dumps({'source_version': 'ns4', 'events': [
                {'event_id': 'projectile', 'function_index': 160}]}).encode()
            src, dst, evidence = d/'source.json', d/'out.json', d/'evidence.json'
            src.write_bytes(raw)
            cmd = [sys.executable, str(ROOT/'tools'/'export_pc_moveset_nsc_manifest.py'),
                   '--manifest', str(src), '--expected-sha256', hashlib.sha256(raw).hexdigest(),
                   '--output', str(dst), '--evidence', str(evidence)]
            ok = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(audit(json.loads(dst.read_bytes()))['events'][0]['source_name'], 'ME_ENTRY_PROJECTILE')
            self.assertEqual(json.loads(evidence.read_text())['output_sha256'], hashlib.sha256(dst.read_bytes()).hexdigest())
            self.assertEqual(src.read_bytes(), raw)
            again = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(src.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
