"""Independent verifier integration: real synthetic CPK/UTF/CRILAYLA parsers."""
import hashlib
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

    def test_rejects_wrong_hashes_and_missing_selection(self):
        for key, value in (("source_sha", "0" * 64), ("output_sha", "0" * 64),
                           ("selected", []), ("selected", ["missing"]),
                           ("selected", [self.name, self.name])):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.verify(**{key: value})

    def test_rejects_tampered_unselected_member_even_with_updated_output_hash(self):
        tampered = self.output.replace(b"untouched", b"UNCHANGED")
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

    def test_rejects_archive_length_change(self):
        longer = self.output + b"x"
        with self.assertRaisesRegex(ValueError, "Archive length"):
            self.verify(longer, output_sha=hashlib.sha256(longer).hexdigest())


if __name__ == "__main__":
    unittest.main()
