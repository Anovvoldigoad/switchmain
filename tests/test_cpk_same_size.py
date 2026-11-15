import hashlib
import unittest
from unittest.mock import patch
from portlib.cpk_same_size import replace_same_size

ORIGINAL = b"header" + b"CRILAYLAold!" + b"tail"
PACKED = b"CRILAYLAnew!"
INDEX = {"a.prm": {"offset": 6, "stored_size": 12, "size": 256, "id": 1}}
SHA = hashlib.sha256(ORIGINAL).hexdigest()


class SameSizeTests(unittest.TestCase):
    def run_patch(self, packed=PACKED, sha=SHA, decoded=b"expected"):
        with patch("portlib.cpk_same_size.entries", return_value=INDEX), patch(
            "portlib.cpk_same_size.extract_candidate",
            return_value=(b"expected", {"candidate_decoded_sha256": hashlib.sha256(b"expected").hexdigest()})
        ), patch("portlib.cpk_same_size.decompress", return_value=decoded):
            return replace_same_size(ORIGINAL, sha, "a.prm", packed)

    def test_preserves_all_other_bytes(self):
        output, report = self.run_patch()
        self.assertEqual(output, b"header" + PACKED + b"tail")
        self.assertTrue(report["metadata_and_other_payloads_unchanged"])
        self.assertFalse(report["runtime_verified"])

    def test_wrong_source_sha(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            self.run_patch(sha="0" * 64)

    def test_size_mismatch(self):
        with self.assertRaisesRegex(ValueError, "Stored-size mismatch"):
            self.run_patch(packed=PACKED + b"x")

    def test_invalid_compression(self):
        with self.assertRaisesRegex(ValueError, "CRILAYLA"):
            self.run_patch(packed=b"x" * 12)

    def test_wrong_decoded_semantics(self):
        with self.assertRaisesRegex(ValueError, "source-authenticated"):
            self.run_patch(decoded=b"wrong")


if __name__ == "__main__":
    unittest.main()
