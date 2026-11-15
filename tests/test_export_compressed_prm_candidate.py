"""Compressed candidate export: synthetic byte-level positive and rejection tests."""
import hashlib
import importlib.util
import pathlib
import tempfile
from unittest.mock import patch
from portlib import compressed_prm_events
import unittest
from portlib.crilayla import decompress
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools" / "export_compressed_prm_candidate.py"
spec = importlib.util.spec_from_file_location("export_compressed_prm_candidate", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CompressedCandidate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.member = "data/spc/testprm.bin.xfbin"
        self.decoded = fixture([event(14), event(0), event(15)])
        self.source = cpk([(self.member, literal_stream(self.decoded))],
                          lambda rows: rows[0].update({"ExtractSize": len(self.decoded)}))
        self.archive = root / "stock.cpk"
        self.archive.write_bytes(self.source)
        self.sha = hashlib.sha256(self.source).hexdigest()
        self.output = root / "candidate.crilayla"

    def test_exact_roundtrip_and_source_unchanged(self):
        report = module.export(self.archive, self.member, self.sha, self.output)
        decoded = decompress(self.output.read_bytes())
        self.assertEqual(hashlib.sha256(decoded).hexdigest(), report["candidate_decoded_sha256"])
        self.assertEqual(hashlib.sha256(self.output.read_bytes()).hexdigest(), report["compressed_candidate_sha256"])
        self.assertEqual(report["marked_records"], 2)
        self.assertFalse(report["output_is_installable"])
        self.assertFalse(report["compressed_archive_repacked"])
        self.assertEqual(self.archive.read_bytes(), self.source)

    def test_single_decode_and_mark_per_export(self):
        original_read = compressed_prm_events.read_payload
        original_mark = compressed_prm_events.mark
        with patch.object(compressed_prm_events, 'read_payload', wraps=original_read) as reader, \
             patch.object(compressed_prm_events, 'mark', wraps=original_mark) as marker:
            report = module.export(self.archive, self.member, self.sha, self.output)
        self.assertEqual(reader.call_count, 1)
        self.assertEqual(marker.call_count, 1)
        self.assertEqual(report['marked_records'], 2)
        self.assertEqual(decompress(self.output.read_bytes()).__len__(), len(self.decoded))

    def test_mapped_archive_never_calls_read_bytes(self):
        with patch.object(pathlib.Path, 'read_bytes', side_effect=AssertionError('full archive read')):
            report = module.export(self.archive, self.member, self.sha, self.output)
        self.assertEqual(report['archive_sha256'], self.sha)
        self.assertTrue(self.output.is_file())

    def test_reject_before_output(self):
        for member, sha, limit in ((self.member, "0"*64, 100000),
                                   ("missing", self.sha, 100000),
                                   (self.member, self.sha, 256)):
            with self.subTest(member=member, limit=limit):
                with self.assertRaises(ValueError):
                    module.export(self.archive, member, sha, self.output, limit=limit)
                self.assertFalse(self.output.exists())
        self.assertEqual(self.archive.read_bytes(), self.source)

    def test_existing_output_preserved(self):
        self.output.write_bytes(b"keep")
        with self.assertRaises(ValueError):
            module.export(self.archive, self.member, self.sha, self.output)
        self.assertEqual(self.output.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
