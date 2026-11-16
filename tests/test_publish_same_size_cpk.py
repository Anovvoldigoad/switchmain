"""End-to-end exclusive CPK publication using real synthetic parsers."""
import hashlib
import json
from unittest.mock import patch
import tempfile
import unittest
from pathlib import Path

from publish_same_size_cpk import publish
from portlib.cpk_events import read_payload
from portlib.prm_events import mark
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream


class PublishCPKTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        original = fixture([event(14), event(0), event(15)])
        converted, _ = mark(original)
        packed = literal_stream(original)
        self.candidate = self.root / "candidate.cri"
        self.candidate.write_bytes(literal_stream(converted))
        self.path = "data/spc/selected.bin.xfbin"
        self.source = self.root / "source.cpk"
        self.source.write_bytes(cpk(
            [(self.path, packed), ("data/untouched", b"original")],
            lambda rows: rows[0].update({"ExtractSize": len(original)}),
        ))
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({self.path: str(self.candidate)}))
        self.output = self.root / "result.cpk"

    def test_publish_preserves_other_member_and_source(self):
        before = self.source.read_bytes()
        proof = publish(self.source, self.sha, self.manifest, self.output)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(read_payload(self.output.read_bytes(), "data/untouched"), b"original")
        self.assertEqual(proof["output_sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertFalse(proof["runtime_verified"])

    def test_publisher_uses_readonly_mmap_not_full_source_read(self):
        candidate_bytes = self.candidate.read_bytes()
        with patch.object(Path, "read_bytes", autospec=True, side_effect=lambda path: (_ for _ in ()).throw(AssertionError("source read_bytes")) if path == self.source else candidate_bytes) as read:
            # The candidate is read normally; the large source archive must be mapped.
            proof = publish(self.source, self.sha, self.manifest, self.output)
        self.assertEqual(proof["source_sha256"], self.sha)
        self.assertEqual(read.call_count, 1)
        self.assertTrue(self.output.exists())

    def test_independent_persisted_verification_blocks_publication(self):
        with patch("publish_same_size_cpk.verify_same_size_output", side_effect=ValueError("persisted verification failed")) as verify:
            with self.assertRaisesRegex(ValueError, "persisted verification failed"):
                publish(self.source, self.sha, self.manifest, self.output)
        verify.assert_called_once()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".cpk-stage-*")), [])

    def test_existing_output_is_never_overwritten(self):
        self.output.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            publish(self.source, self.sha, self.manifest, self.output)
        self.assertEqual(self.output.read_bytes(), b"keep")

    def test_duplicate_manifest_member_does_not_publish(self):
        for names in [(self.path, self.path), (self.path, self.path.upper())]:
            with self.subTest(names=names):
                self.manifest.write_text("{" + ",".join(json.dumps(k) + ":" + json.dumps(str(self.candidate)) for k in names) + "}")
                with self.assertRaisesRegex(ValueError, "Duplicate manifest member"):
                    publish(self.source, self.sha, self.manifest, self.output)
                self.assertFalse(self.output.exists())

    def test_wrong_sha_does_not_publish(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            publish(self.source, "0" * 64, self.manifest, self.output)
        self.assertFalse(self.output.exists())

    def test_invalid_candidate_does_not_publish(self):
        self.candidate.write_bytes(b"wrong")
        with self.assertRaises(ValueError):
            publish(self.source, self.sha, self.manifest, self.output)
        self.assertFalse(self.output.exists())

    def test_source_is_never_overwritten(self):
        before = self.source.read_bytes()
        with self.assertRaises((FileExistsError, ValueError)):
            publish(self.source, self.sha, self.manifest, self.source)
        self.assertEqual(self.source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
