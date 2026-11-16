"""Independent verifier integration: real synthetic CPK/UTF/CRILAYLA parsers."""
import hashlib
import mmap
import tempfile
from pathlib import Path
import unittest

from portlib.cpk_same_size import replace_many_same_size
from portlib.cpk_same_size_verify import verify_same_size_output
from portlib.prm_events import mark
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream


class IndependentVerificationTests(unittest.TestCase):
    def setUp(self):
        original = fixture([event(14), event(0), event(15)])
        converted, _ = mark(original)
        self.name = "data/spc/selected.bin.xfbin"
        self.source = cpk(
            [(self.name, literal_stream(original)), ("data/untouched", b"untouched")],
            lambda rows: rows[0].update({"ExtractSize": len(original)}),
        )
        self.source_sha = hashlib.sha256(self.source).hexdigest()
        self.output, _ = replace_many_same_size(
            self.source, self.source_sha, {self.name: literal_stream(converted)})
        self.output_sha = hashlib.sha256(self.output).hexdigest()

    def verify(self, output=None, **kwargs):
        return verify_same_size_output(
            self.source, self.output if output is None else output,
            kwargs.get("source_sha", self.source_sha),
            kwargs.get("output_sha", self.output_sha),
            kwargs.get("selected", [self.name]),
        )

    def test_verified_output_and_provenance(self):
        proof = self.verify()
        self.assertEqual(proof["selected_paths"], [self.name])
        self.assertFalse(proof["runtime_verified"])

    def test_readonly_mapped_archives_match_bytes_and_reject_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.cpk"
            output_path = Path(directory) / "output.cpk"
            source_path.write_bytes(self.source)
            output_path.write_bytes(self.output)
            with source_path.open("rb") as src, output_path.open("rb") as dst:
                with mmap.mmap(src.fileno(), 0, access=mmap.ACCESS_READ) as source:
                    with mmap.mmap(dst.fileno(), 0, access=mmap.ACCESS_READ) as output:
                        proof = verify_same_size_output(
                            source, output, self.source_sha, self.output_sha, [self.name])
                        self.assertEqual(proof, self.verify())
                        with self.assertRaisesRegex(ValueError, "Output SHA256 mismatch"):
                            verify_same_size_output(
                                source, output, self.source_sha, "0" * 64, [self.name])
            self.assertEqual(source_path.read_bytes(), self.source)
            self.assertEqual(output_path.read_bytes(), self.output)

    def test_rejects_wrong_hashes_and_missing_selection(self):
        for key, value in (("source_sha", "0" * 64), ("output_sha", "0" * 64),
                           ("selected", []), ("selected", ["missing"]),
                           ("selected", [self.name, self.name])):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.verify(**{key: value})

    def test_rejects_tampered_unselected_member_even_with_updated_output_hash(self):
        from portlib.cpk_events import entries
        start = entries(self.output)["data/untouched"]["offset"]
        tampered = self.output[:start] + b"UNCHANGED" + self.output[start + 9:]
        self.assertEqual(len(tampered), len(self.output))
        with self.assertRaisesRegex(ValueError, "Unselected member"):
            self.verify(tampered, output_sha=hashlib.sha256(tampered).hexdigest())

    def test_rejects_tampered_selected_stream_even_with_updated_output_hash(self):
        from portlib.cpk_events import entries
        start = entries(self.output)[self.name]["offset"]
        tampered = bytearray(self.output)
        tampered[start + 8:start + 12] = bytes((255, 255, 255, 127))
        tampered = bytes(tampered)
        with self.assertRaises(ValueError):
            self.verify(tampered, output_sha=hashlib.sha256(tampered).hexdigest())

    def test_rejects_casefold_duplicate_selection(self):
        with self.assertRaisesRegex(ValueError, "Duplicate selected path"):
            self.verify(selected=[self.name, self.name.upper()])

    def test_rejects_overlapping_toc_spans(self):
        from unittest.mock import patch
        from portlib.cpk_events import entries
        original = entries(self.source)
        overlap = {name: dict(row) for name, row in original.items()}
        overlap["data/untouched"]["offset"] = overlap[self.name]["offset"] + 1
        with patch("portlib.cpk_same_size_verify.entries", return_value=overlap):
            with self.assertRaisesRegex(ValueError, "Overlapping CPK member"):
                self.verify()

    def test_multi_member_verification_reuses_authenticated_index(self):
        from unittest.mock import patch
        from portlib.cpk_events import entries as parse_entries
        from portlib.compressed_prm_events import _extract_validated_candidate
        from test_cpk_events import cpk
        from test_compressed_prm_events import literal_stream
        from test_prm_marker import fixture, event
        from portlib.prm_events import mark
        original = fixture([event(14), event(0), event(15)])
        converted, _ = mark(original)
        paths = ["data/spc/a.bin.xfbin", "data/spc/b.bin.xfbin"]
        source = cpk(
            [(name, literal_stream(original)) for name in paths],
            lambda rows: [row.update({"ExtractSize": len(original)}) for row in rows],
        )
        source_sha = hashlib.sha256(source).hexdigest()
        output, _ = replace_many_same_size(
            source, source_sha, {name: literal_stream(converted) for name in paths})
        output_sha = hashlib.sha256(output).hexdigest()
        with patch("portlib.cpk_same_size_verify.entries", wraps=parse_entries) as parse, \
             patch("portlib.cpk_same_size_verify._extract_validated_candidate",
                   wraps=_extract_validated_candidate) as extract:
            proof = verify_same_size_output(source, output, source_sha, output_sha, paths)
        self.assertEqual(parse.call_count, 2)
        self.assertEqual(extract.call_count, 2)
        self.assertTrue(all(call.args[3] == parse_entries(source)
                            for call in extract.call_args_list))
        self.assertEqual(proof["selected_paths"], paths)

    def test_rejects_archive_length_change(self):
        longer = self.output + b"x"
        with self.assertRaisesRegex(ValueError, "Archive length"):
            self.verify(longer, output_sha=hashlib.sha256(longer).hexdigest())


if __name__ == "__main__":
    unittest.main()
