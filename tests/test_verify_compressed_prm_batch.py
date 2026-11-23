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

    def test_noop_requires_original_compressed_bitstream(self):
        from portlib.prm_events import mark
        from test_compressed_prm_events import literal_stream
        from test_cpk_events import cpk
        from portlib.crilayla_rle import encode_runs
        from portlib.crilayla import decompress
        marked, _ = mark(self.decoded[0])
        original = literal_stream(marked)
        archive = cpk([(self.paths[0], original)],
                      lambda rows: rows[0].update({"ExtractSize": len(marked)}))
        self.archive.write_bytes(archive)
        self.sha = hashlib.sha256(archive).hexdigest()
        manifest = {"members": [self.manifest["members"][0]]}
        report = exporter.export_batch(self.archive, self.sha, manifest, self.out)
        self.assertEqual(verifier.verify_batch(self.archive, self.sha, report, self.out)["verified_members"], 1)
        row = report["members"][0]
        alternate = encode_runs(marked)
        self.assertEqual(decompress(alternate), marked)
        self.assertNotEqual(alternate, original)
        (self.out / row["output"]).write_bytes(alternate)
        row["compressed_candidate_sha256"] = hashlib.sha256(alternate).hexdigest()
        row["compressed_candidate_bytes"] = len(alternate)
        with self.assertRaisesRegex(ValueError, "No-op compressed payload"):
            verifier.verify_batch(self.archive, self.sha, report, self.out)

    def test_reuse_and_encoder_provenance_cannot_be_forged(self):
        report = self._export()
        report["members"][0]["original_stored_payload_reused"] = True
        with self.assertRaisesRegex(ValueError, "reuse provenance"):
            verifier.verify_batch(self.archive, self.sha, report, self.out)
        report["members"][0]["original_stored_payload_reused"] = False
        report["members"][0]["encoder"] = "original"
        with self.assertRaisesRegex(ValueError, "encoder provenance"):
            verifier.verify_batch(self.archive, self.sha, report, self.out)

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
