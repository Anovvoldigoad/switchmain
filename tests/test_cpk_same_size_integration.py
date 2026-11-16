"""Integration tests with real synthetic CPK/UTF, PRM and CRILAYLA parsers.

These do not establish authentic Switch archive or runtime compatibility.
"""
import hashlib
import unittest

from portlib.cpk_same_size import replace_same_size
from portlib.cpk_events import entries, read_payload
from portlib.prm_events import mark
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream


PATH = "data/spc/selected.bin.xfbin"
OTHER = "data/other/untouched.bin"


class SameSizeArchiveIntegration(unittest.TestCase):
    def setUp(self):
        self.decoded = fixture([event(14), event(0), event(15)])
        self.converted, _ = mark(self.decoded)
        self.old_packed = literal_stream(self.decoded)
        self.new_packed = literal_stream(self.converted)
        self.assertEqual(len(self.old_packed), len(self.new_packed))
        self.source = cpk(
            [(PATH, self.old_packed), (OTHER, b"untouched bytes")],
            lambda rows: rows[0].update({"ExtractSize": len(self.decoded)}),
        )
        self.sha = hashlib.sha256(self.source).hexdigest()

    def test_real_parser_roundtrip_and_nonselected_integrity(self):
        before = entries(self.source)
        result, proof = replace_same_size(self.source, self.sha, PATH, self.new_packed)
        self.assertEqual(entries(result), before)
        self.assertEqual(read_payload(result, PATH), self.converted)
        self.assertEqual(read_payload(result, OTHER), b"untouched bytes")
        start = before[PATH]["offset"]
        end = start + before[PATH]["stored_size"]
        self.assertEqual(result[:start], self.source[:start])
        self.assertEqual(result[end:], self.source[end:])
        self.assertEqual(result[start:end], self.new_packed)
        self.assertEqual(proof["output_sha256"], hashlib.sha256(result).hexdigest())
        self.assertFalse(proof["runtime_verified"])
        self.assertFalse(proof["ready_for_gameplay_test"])

    def test_rejects_same_size_wrong_decoded_candidate(self):
        wrong = literal_stream(self.decoded)
        with self.assertRaisesRegex(ValueError, "source-authenticated"):
            replace_same_size(self.source, self.sha, PATH, wrong)

    def test_rejects_wrong_sha_and_missing_member(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            replace_same_size(self.source, "0" * 64, PATH, self.new_packed)
        with self.assertRaisesRegex(ValueError, "Unknown CPK member"):
            replace_same_size(self.source, self.sha, "missing", self.new_packed)

    def test_rejects_size_change_and_corruption(self):
        with self.assertRaisesRegex(ValueError, "Stored-size mismatch"):
            replace_same_size(self.source, self.sha, PATH, self.new_packed + b"x")
        corrupt = bytearray(self.new_packed)
        corrupt[8:12] = bytes.fromhex("ffffff7f")
        with self.assertRaises(ValueError):
            replace_same_size(self.source, self.sha, PATH, bytes(corrupt), limit=1024 * 1024)

    def test_rejects_crc_archive(self):
        guarded = cpk(
            [(PATH, self.old_packed)],
            lambda rows: rows[0].update({"ExtractSize": len(self.decoded)}),
            header_change={"EnableFileCrc": 1},
        )
        with self.assertRaisesRegex(ValueError, "CRC"):
            replace_same_size(guarded, hashlib.sha256(guarded).hexdigest(), PATH, self.new_packed)


    def test_batch_two_members_and_unchanged_third(self):
        from portlib.cpk_same_size import replace_many_same_size
        second = "data/spc/second.bin.xfbin"
        source = cpk(
            [(PATH, self.old_packed), (second, self.old_packed), (OTHER, b"untouched bytes")],
            lambda rows: [row.update({"ExtractSize": len(self.decoded)}) for row in rows[:2]],
        )
        sha = hashlib.sha256(source).hexdigest()
        result, proof = replace_many_same_size(source, sha, {
            PATH: self.new_packed, second: self.new_packed,
        })
        self.assertEqual(entries(source), entries(result))
        self.assertEqual(read_payload(result, PATH), self.converted)
        self.assertEqual(read_payload(result, second), self.converted)
        self.assertEqual(read_payload(result, OTHER), b"untouched bytes")
        self.assertEqual(proof["selected_paths"], sorted([PATH, second]))
        self.assertFalse(proof["runtime_verified"])

    def test_batch_rejects_casefold_duplicate_before_edit(self):
        from portlib.cpk_same_size import replace_many_same_size
        with self.assertRaisesRegex(ValueError, "Duplicate CPK path"):
            replace_many_same_size(self.source, self.sha, {
                PATH: self.new_packed, PATH.upper(): self.new_packed,
            })

    def test_batch_rejects_one_bad_member_without_mutating_source(self):
        from portlib.cpk_same_size import replace_many_same_size
        second = "data/spc/second.bin.xfbin"
        source = cpk(
            [(PATH, self.old_packed), (second, self.old_packed)],
            lambda rows: [row.update({"ExtractSize": len(self.decoded)}) for row in rows],
        )
        before = hashlib.sha256(source).hexdigest()
        with self.assertRaisesRegex(ValueError, "source-authenticated"):
            replace_many_same_size(source, before, {
                PATH: self.new_packed, second: self.old_packed,
            })
        self.assertEqual(hashlib.sha256(source).hexdigest(), before)
        with self.assertRaisesRegex(ValueError, "Stored-size mismatch"):
            replace_many_same_size(source, before, {
                PATH: self.new_packed, second: self.new_packed + b"x",
            })
        with self.assertRaises(ValueError):
            replace_many_same_size(source, "0" * 64, {PATH: self.new_packed})
        with self.assertRaises(ValueError):
            replace_many_same_size(source, before, {})

if __name__ == "__main__":
    unittest.main()
