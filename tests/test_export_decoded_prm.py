"""Offline-only decoded PRM CLI regression, no runtime/CPK repacking."""
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest

from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools" / "export_decoded_prm.py"
spec = importlib.util.spec_from_file_location("export_decoded_prm", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExportDecodedPRM(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.member = "data/spc/testprm.bin.xfbin"
        raw = fixture([event(14), event(0), event(15)])
        packed = literal_stream(raw)
        self.source = cpk([(self.member, packed)],
                          lambda rows: rows[0].update({"ExtractSize": len(raw)}))
        self.archive = self.root / "stock.cpk"
        self.archive.write_bytes(self.source)
        self.sha = hashlib.sha256(self.source).hexdigest()
        self.output = self.root / "candidate.decoded.bin"

    def test_export_exact_integrity_and_noninstallable(self):
        report = module.export(self.archive, self.member, self.sha, self.output)
        self.assertEqual(report["output_sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(report["candidate_decoded_sha256"], report["output_sha256"])
        self.assertEqual(report["marked_records"], 2)
        self.assertFalse(report["output_is_installable"])
        self.assertFalse(report["compressed_archive_repacked"])
        self.assertEqual(self.archive.read_bytes(), self.source)

    def test_wrong_hash_path_and_size_do_not_create_output(self):
        for member, sha, limit in (
            (self.member, "0" * 64, 256 * 1024 * 1024),
            ("data/spc/missing", self.sha, 256 * 1024 * 1024),
            (self.member, self.sha, 256),
        ):
            with self.subTest(member=member, sha=sha, limit=limit):
                with self.assertRaises(ValueError):
                    module.export(self.archive, member, sha, self.output, limit=limit)
                self.assertFalse(self.output.exists())
        self.assertEqual(self.archive.read_bytes(), self.source)

    def test_never_overwrites_existing_candidate(self):
        self.output.write_bytes(b"keep")
        with self.assertRaises(ValueError):
            module.export(self.archive, self.member, self.sha, self.output)
        self.assertEqual(self.output.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
