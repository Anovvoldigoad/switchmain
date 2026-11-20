"""Synthetic source-bound candidate verification; no game-runtime proof."""
import hashlib
import importlib.util
import pathlib
from unittest.mock import patch
import unittest
from test_export_compressed_prm_batch import CompressedBatch, module as exporter

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools" / "verify_compressed_prm_batch.py"
spec = importlib.util.spec_from_file_location("candidate_verifier", SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

class CandidateVerification(CompressedBatch):
    def _export(self):
        return exporter.export_batch(self.archive, self.sha, self.manifest, self.out, encoder="auto")

    def test_verifier_does_not_trust_exporter_candidate_builder(self):
        report = self._export()
        with patch("portlib.compressed_prm_events._extract_validated_candidate",
                   side_effect=AssertionError("exporter must not be called")):
            result = verifier.verify_batch(self.archive, self.sha, report, self.out)
        self.assertEqual(result["verified_members"], 2)

    def test_forged_provenance_and_matching_candidate_digest_rejected(self):
        report = self._export()
        row = report["members"][0]
        row["event236_provenance"] = []
        with self.assertRaisesRegex(ValueError, "provenance"):
            verifier.verify_batch(self.archive, self.sha, report, self.out)

    def test_source_bound_exact_match(self):
        report = self._export()
        result = verifier.verify_batch(self.archive, self.sha, report, self.out)
        self.assertEqual(result["verified_members"], 2)
        self.assertTrue(result["byte_exact_decoded_match"])
        self.assertFalse(result["gameplay_verified"])

    def test_tampered_candidate_even_with_updated_hash_rejected(self):
        from portlib.crilayla_literal import encode_literals
        from portlib.crilayla import decompress
        report = self._export()
        row = report["members"][0]
        path = self.out / row["output"]
        decoded = bytearray(decompress(path.read_bytes()))
        decoded[-1] ^= 1
        packed = encode_literals(bytes(decoded))
        path.write_bytes(packed)
        row["compressed_candidate_sha256"] = hashlib.sha256(packed).hexdigest()
        row["compressed_candidate_bytes"] = len(packed)
        with self.assertRaisesRegex(ValueError, "differs from pinned source"):
            verifier.verify_batch(self.archive, self.sha, report, self.out)

    def test_provenance_and_wrong_source_rejected(self):
        report = self._export()
        report["members"][0]["candidate_decoded_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance"):
            verifier.verify_batch(self.archive, self.sha, report, self.out)
        with self.assertRaises(ValueError):
            verifier.verify_batch(self.archive, "0" * 64, report, self.out)

    def test_symlink_and_duplicate_output_rejected(self):
        report = self._export()
        path = self.out / report["members"][0]["output"]
        path.unlink()
        path.symlink_to(self.out / report["members"][1]["output"])
        with self.assertRaisesRegex(ValueError, "symlink"):
            verifier.verify_batch(self.archive, self.sha, report, self.out)
        report["members"][1]["output"] = report["members"][0]["output"]
        with self.assertRaises(ValueError):
            verifier.verify_batch(self.archive, self.sha, report, self.out)

if __name__ == "__main__":
    unittest.main()
