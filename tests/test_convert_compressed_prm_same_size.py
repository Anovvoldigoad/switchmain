"""End-to-end offline compressed Event236 conversion with authentic synthetic CPK parser."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from convert_compressed_prm_same_size import convert
from portlib.cpk_events import read_payload
from portlib.prm_events import mark
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream


class ConvertCompressedSameSize(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.member = "data/spc/test.bin.xfbin"
        self.decoded = fixture([event(14), event(0), event(15)])
        self.original = cpk([(self.member, literal_stream(self.decoded)),
                             ("data/untouched", b"untouched")],
                            lambda rows: rows[0].update({"ExtractSize": len(self.decoded)}))
        self.source = self.root / "source.cpk"
        self.output = self.root / "output.cpk"
        self.source.write_bytes(self.original)
        self.sha = hashlib.sha256(self.original).hexdigest()

    def test_publish_exact_size_and_preserve_unselected_bytes(self):
        proof = convert(self.source, self.sha, self.member, self.output)
        expected, report = mark(self.decoded)
        self.assertGreater(report["marked_records"], 0)
        self.assertEqual(read_payload(self.output.read_bytes(), self.member), expected)
        self.assertEqual(read_payload(self.output.read_bytes(), "data/untouched"), b"untouched")
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(len(self.output.read_bytes()), len(self.original))
        self.assertEqual(hashlib.sha256(self.output.read_bytes()).hexdigest(), proof["output_sha256"])
        self.assertFalse(proof["gameplay_verified"])

    def test_wrong_sha_and_missing_member_publish_nothing(self):
        for member, sha in ((self.member, "0" * 64), ("missing", self.sha)):
            with self.subTest(member=member):
                with self.assertRaises(ValueError):
                    convert(self.source, sha, member, self.output)
                self.assertFalse(self.output.exists())

    def test_noop_refused_without_publication(self):
        converted, _ = mark(self.decoded)
        source = cpk([(self.member, literal_stream(converted))],
                     lambda rows: rows[0].update({"ExtractSize": len(converted)}))
        self.source.write_bytes(source)
        with self.assertRaisesRegex(ValueError, "No Event236 change"):
            convert(self.source, hashlib.sha256(source).hexdigest(), self.member, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_never_overwritten(self):
        self.output.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            convert(self.source, self.sha, self.member, self.output)
        self.assertEqual(self.output.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
