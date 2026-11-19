"""End-to-end offline compressed Event236 conversion with authentic synthetic CPK parser."""
import hashlib
import contextlib
import io
import json
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest

from convert_compressed_prm_same_size import convert, convert_many, main
from portlib.cpk_events import entries
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

    def test_multi_member_atomic_publish_and_integrity(self):
        second = "data/spc/second.bin.xfbin"
        original = cpk([(self.member, literal_stream(self.decoded)),
                        (second, literal_stream(self.decoded)),
                        ("data/untouched", b"untouched")],
                       lambda rows: [row.update({"ExtractSize": len(self.decoded)})
                                     for row in rows[:2]])
        self.source.write_bytes(original)
        sha = hashlib.sha256(original).hexdigest()
        proof = convert_many(self.source, sha, [self.member, second], self.output)
        expected, _ = mark(self.decoded)
        written = self.output.read_bytes()
        for member in (self.member, second):
            self.assertEqual(read_payload(written, member), expected)
            self.assertIn(member, proof["candidates"])
        self.assertEqual(read_payload(written, "data/untouched"), b"untouched")
        self.assertEqual(len(written), len(original))
        self.assertEqual(hashlib.sha256(written).hexdigest(), proof["output_sha256"])
        self.assertEqual(self.source.read_bytes(), original)

    def test_mixed_compressed_and_plain_member_atomic_integrity(self):
        plain = "data/spc/plain.bin.xfbin"
        original = cpk([(self.member, literal_stream(self.decoded)),
                        (plain, self.decoded),
                        ("data/untouched", b"untouched")],
                       lambda rows: rows[0].update({"ExtractSize": len(self.decoded)}))
        self.source.write_bytes(original)
        sha = hashlib.sha256(original).hexdigest()
        proof = convert_many(self.source, sha, [self.member, plain], self.output)
        expected, _ = mark(self.decoded)
        written = self.output.read_bytes()
        self.assertEqual(read_payload(written, self.member), expected)
        self.assertEqual(read_payload(written, plain), expected)
        self.assertEqual(read_payload(written, "data/untouched"), b"untouched")
        self.assertEqual(len(written), len(original))
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(hashlib.sha256(written).hexdigest(), proof["output_sha256"])
        self.assertEqual(set(proof["candidates"]), {self.member, plain})
        self.assertFalse(proof["ready_for_gameplay_test"])

    def test_mixed_plain_candidate_semantic_tamper_rejected(self):
        from portlib.cpk_same_size import validate_many_same_size
        from portlib.cpk_same_size_verify import verify_same_size_output
        plain = "data/spc/plain.bin.xfbin"
        original = cpk([(plain, self.decoded)])
        sha = hashlib.sha256(original).hexdigest()
        expected, _ = mark(self.decoded)
        tampered = bytearray(expected)
        tampered[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "plain Event236 conversion"):
            validate_many_same_size(original, sha, {plain: bytes(tampered)})
        index = entries(original)
        offset = index[plain]["offset"]
        modified = original[:offset] + bytes(tampered) + original[offset + len(tampered):]
        with self.assertRaisesRegex(ValueError, "Selected plain member semantic mismatch"):
            verify_same_size_output(original, modified, sha,
                                    hashlib.sha256(modified).hexdigest(), [plain])

    def test_mixed_batch_rejects_noop_plain_without_publication(self):
        plain = "data/spc/plain.bin.xfbin"
        marked, _ = mark(self.decoded)
        original = cpk([(self.member, literal_stream(self.decoded)), (plain, marked)],
                       lambda rows: rows[0].update({"ExtractSize": len(self.decoded)}))
        self.source.write_bytes(original)
        sha = hashlib.sha256(original).hexdigest()
        with self.assertRaisesRegex(ValueError, "No Event236 change"):
            convert_many(self.source, sha, [self.member, plain], self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), original)

    def test_mixed_batch_rejects_non_prm_plain_without_publication(self):
        original = cpk([(self.member, literal_stream(self.decoded)),
                        ("data/not_prm", b"not a prm")],
                       lambda rows: rows[0].update({"ExtractSize": len(self.decoded)}))
        self.source.write_bytes(original)
        sha = hashlib.sha256(original).hexdigest()
        with self.assertRaises(ValueError):
            convert_many(self.source, sha, [self.member, "data/not_prm"], self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), original)

    def test_multi_member_validates_source_and_toc_once(self):
        second = "data/spc/second.bin.xfbin"
        original = cpk([(self.member, literal_stream(self.decoded)),
                        (second, literal_stream(self.decoded))],
                       lambda rows: [row.update({"ExtractSize": len(self.decoded)})
                                     for row in rows])
        self.source.write_bytes(original)
        sha = hashlib.sha256(original).hexdigest()
        with patch("convert_compressed_prm_same_size.entries", wraps=entries) as parse, \
             patch("portlib.compressed_prm_events.entries", side_effect=AssertionError(
                 "member must reuse validated TOC")):
            proof = convert_many(self.source, sha, [self.member, second], self.output)
        self.assertEqual(parse.call_count, 1)
        self.assertEqual(set(proof["candidates"]), {self.member, second})

    def test_multi_member_wrong_sha_rejected_before_toc(self):
        with patch("convert_compressed_prm_same_size.entries",
                   side_effect=AssertionError("TOC parsed before SHA")):
            with self.assertRaisesRegex(ValueError, "source SHA256 mismatch"):
                convert_many(self.source, "0" * 64, [self.member], self.output)
        self.assertFalse(self.output.exists())

    def test_multi_member_rejects_invalid_second_without_partial_output(self):
        with self.assertRaises(ValueError):
            convert_many(self.source, self.sha, [self.member, "missing"], self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_multi_member_rejects_duplicates_and_empty_list(self):
        for members in ([], [self.member, self.member]):
            with self.subTest(members=members):
                with self.assertRaises(ValueError):
                    convert_many(self.source, self.sha, members, self.output)
                self.assertFalse(self.output.exists())


    def test_cli_multi_member_matches_api_and_preserves_source(self):
        second = "data/spc/second.bin.xfbin"
        original = cpk([(self.member, literal_stream(self.decoded)),
                        (second, literal_stream(self.decoded)),
                        ("data/untouched", b"untouched")],
                       lambda rows: [row.update({"ExtractSize": len(self.decoded)})
                                     for row in rows[:2]])
        self.source.write_bytes(original)
        sha = hashlib.sha256(original).hexdigest()
        argv = ["convert_compressed_prm_same_size.py", str(self.source), sha,
                self.member, second, str(self.output)]
        with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()) as stdout:
            main()
        proof = json.loads(stdout.getvalue())
        expected, _ = mark(self.decoded)
        written = self.output.read_bytes()
        self.assertEqual(set(proof["candidates"]), {self.member, second})
        for member in (self.member, second):
            self.assertEqual(read_payload(written, member), expected)
        self.assertEqual(read_payload(written, "data/untouched"), b"untouched")
        self.assertEqual(len(written), len(original))
        self.assertEqual(hashlib.sha256(written).hexdigest(), proof["output_sha256"])
        self.assertEqual(self.source.read_bytes(), original)

    def test_cli_invalid_second_rolls_back_without_output(self):
        argv = ["convert_compressed_prm_same_size.py", str(self.source), self.sha,
                self.member, "missing", str(self.output)]
        with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                main()
        self.assertFalse(self.output.exists())
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_cli_single_member_backwards_compatible(self):
        argv = ["convert_compressed_prm_same_size.py", str(self.source), self.sha,
                self.member, str(self.output)]
        with patch("sys.argv", argv), contextlib.redirect_stdout(io.StringIO()) as stdout:
            main()
        proof = json.loads(stdout.getvalue())
        self.assertEqual(set(proof["candidates"]), {self.member})
        self.assertTrue(self.output.exists())
        self.assertFalse(proof["ready_for_gameplay_test"])



if __name__ == "__main__":
    unittest.main()
