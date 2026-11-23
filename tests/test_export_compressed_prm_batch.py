"""Synthetic atomic compressed batch regression; no engine or Uzuy proof."""
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from portlib.crilayla import decompress
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools" / "export_compressed_prm_batch.py"
spec = importlib.util.spec_from_file_location("compressed_batch", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CompressedBatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = pathlib.Path(self.tmp.name)
        self.archive = root / "source.cpk"
        self.out = root / "output"
        self.out.mkdir()
        self.paths = ["data/spc/one.bin.xfbin", "data/spc/two.bin.xfbin"]
        self.decoded = [fixture([event(14), event(0)]),
                        fixture([event(15), event(0)])]
        source = cpk(list(zip(self.paths, map(literal_stream, self.decoded))),
                     lambda rows: [row.update({"ExtractSize": len(decoded)})
                                   for row, decoded in zip(rows, self.decoded)])
        self.archive.write_bytes(source)
        self.sha = hashlib.sha256(source).hexdigest()
        self.manifest = {"members": [
            {"path": self.paths[0], "output": "one.crilayla"},
            {"path": self.paths[1], "output": "two.crilayla"}]}

    def test_run_encoder_batch_roundtrip_and_integrity(self):
        report = module.export_batch(self.archive, self.sha, self.manifest, self.out, encoder="runs")
        self.assertEqual([r["encoder"] for r in report["members"]], ["runs", "runs"])
        for row in report["members"]:
            packed = (self.out / row["output"]).read_bytes()
            self.assertEqual(hashlib.sha256(packed).hexdigest(), row["compressed_candidate_sha256"])
            self.assertEqual(hashlib.sha256(decompress(packed)).hexdigest(), row["candidate_decoded_sha256"])

    def test_auto_selects_smallest_valid_candidate_and_keeps_source(self):
        from portlib.crilayla_literal import encode_literals
        from portlib.crilayla_rle import encode_runs
        original = self.archive.read_bytes()
        report = module.export_batch(self.archive, self.sha, self.manifest, self.out, encoder="auto")
        for row in report["members"]:
            packed = (self.out / row["output"]).read_bytes()
            decoded = decompress(packed)
            self.assertEqual(hashlib.sha256(decoded).hexdigest(), row["candidate_decoded_sha256"])
            literal = encode_literals(decoded)
            runs = encode_runs(decoded)
            expected = runs if len(runs) < len(literal) else literal
            self.assertEqual(packed, expected)
            self.assertEqual(row["encoder"], "runs" if len(runs) < len(literal) else "literal")
            self.assertEqual(decompress(packed), decoded)
        self.assertEqual(self.archive.read_bytes(), original)

    def test_auto_prefers_literal_for_nonrepeating_payload(self):
        from portlib.crilayla_literal import encode_literals
        from portlib.crilayla_rle import encode_runs
        import random
        rng = random.Random(170)
        decoded = bytes(range(256)) + bytes(rng.randrange(256) for _ in range(2048))
        literal, runs = encode_literals(decoded), encode_runs(decoded)
        self.assertLessEqual(len(literal), len(runs))
        self.assertEqual(decompress(literal), decoded)

    def test_noop_member_reuses_exact_original_stream_in_mixed_batch(self):
        from portlib.prm_events import mark
        from portlib.cpk_events import entries, canonical
        marked, _ = mark(self.decoded[0])
        original_packed = literal_stream(marked)
        changed_packed = literal_stream(self.decoded[1])
        archive = cpk(list(zip(self.paths, [original_packed, changed_packed])),
                      lambda rows: [row.update({"ExtractSize": len(raw)})
                                    for row, raw in zip(rows, [marked, self.decoded[1]])])
        self.archive.write_bytes(archive)
        self.sha = hashlib.sha256(archive).hexdigest()
        for encoder in ("literal", "runs", "auto"):
            with self.subTest(encoder=encoder):
                out = self.out / encoder
                out.mkdir()
                report = module.export_batch(self.archive, self.sha, self.manifest, out, encoder=encoder)
                first, second = report["members"]
                self.assertEqual((out / "one.crilayla").read_bytes(), original_packed)
                self.assertEqual(first["encoder"], "original")
                self.assertTrue(first["original_stored_payload_reused"])
                self.assertEqual(first["compressed_candidate_sha256"], hashlib.sha256(original_packed).hexdigest())
                self.assertEqual(first["compressed_candidate_bytes"], len(original_packed))
                self.assertFalse(second["original_stored_payload_reused"])
                self.assertNotEqual((out / "two.crilayla").read_bytes(), changed_packed)
                self.assertEqual(decompress((out / "two.crilayla").read_bytes()),
                                 module._extract_validated_candidate(
                                     archive, self.paths[1], self.sha, entries(archive),
                                     decoded_limit=256 * 1024 * 1024)[0])
        self.assertEqual(self.archive.read_bytes(), archive)

    def test_noop_reuse_skips_encoder_and_preserves_allocation(self):
        from portlib.prm_events import mark
        marked, _ = mark(self.decoded[0])
        packed = literal_stream(marked)
        archive = cpk([(self.paths[0], packed)],
                      lambda rows: rows[0].update({"ExtractSize": len(marked)}))
        self.archive.write_bytes(archive)
        self.sha = hashlib.sha256(archive).hexdigest()
        one = {"members": [self.manifest["members"][0]]}
        with patch.object(module, "encode_literals", side_effect=AssertionError("reencoded")), \
             patch.object(module, "encode_runs", side_effect=AssertionError("reencoded")):
            report = module.export_batch(self.archive, self.sha, one, self.out, encoder="auto")
        self.assertEqual((self.out / "one.crilayla").read_bytes(), packed)
        self.assertTrue(report["members"][0]["original_stored_payload_reused"])

    def test_unknown_encoder_rejected_before_output(self):
        with self.assertRaises(ValueError):
            module.export_batch(self.archive, self.sha, self.manifest, self.out, encoder="unknown")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_batch_roundtrip_source_preserved(self):
        before = self.archive.read_bytes()
        report = module.export_batch(self.archive, self.sha, self.manifest, self.out)
        self.assertEqual(len(report["members"]), 2)
        self.assertEqual([row["marked_records"] for row in report["members"]], [1, 1])
        self.assertFalse(report["output_is_installable"])
        for row, decoded in zip(report["members"], self.decoded):
            packed = (self.out / row["output"]).read_bytes()
            self.assertEqual(hashlib.sha256(packed).hexdigest(),
                             row["compressed_candidate_sha256"])
            self.assertEqual(hashlib.sha256(decompress(packed)).hexdigest(),
                             row["candidate_decoded_sha256"])
        self.assertEqual(self.archive.read_bytes(), before)

    def test_preflight_rejects_without_partial_output(self):
        cases = [
            ({"members": [self.manifest["members"][0], self.manifest["members"][0]]}, self.sha),
            ({"members": [{"path": self.paths[0], "output": "../escape"}]}, self.sha),
            ({"members": [{"path": "missing", "output": "missing.bin"}]}, self.sha),
            (self.manifest, "0" * 64),
        ]
        for manifest, sha in cases:
            with self.subTest(manifest=manifest, sha=sha):
                with self.assertRaises(ValueError):
                    module.export_batch(self.archive, sha, manifest, self.out)
                self.assertEqual(list(self.out.iterdir()), [])

    def test_existing_output_untouched(self):
        dest = self.out / "two.crilayla"
        dest.write_bytes(b"existing")
        with self.assertRaises(ValueError):
            module.export_batch(self.archive, self.sha, self.manifest, self.out)
        self.assertEqual(dest.read_bytes(), b"existing")
        self.assertEqual(len(list(self.out.iterdir())), 1)

    def test_rollback_on_second_write_failure(self):
        original = module.os.link
        calls = [0]
        def fail_second(*args, **kwargs):
            calls[0] += 1
            if calls[0] == 2:
                raise OSError("injected write failure")
            return original(*args, **kwargs)
        with patch.object(module.os, "link", side_effect=fail_second):
            with self.assertRaises(OSError):
                module.export_batch(self.archive, self.sha, self.manifest, self.out)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_stage_failure_leaves_no_output_or_scratch(self):
        original = module.encode_literals
        calls = [0]
        def fail_second(*args, **kwargs):
            calls[0] += 1
            if calls[0] == 2:
                raise ValueError("injected encode failure")
            return original(*args, **kwargs)
        with patch.object(module, "encode_literals", side_effect=fail_second):
            with self.assertRaises(ValueError):
                module.export_batch(self.archive, self.sha, self.manifest, self.out)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_publish_is_exclusive_and_staging_removed(self):
        with patch.object(module.os, "link", wraps=module.os.link) as publish:
            module.export_batch(self.archive, self.sha, self.manifest, self.out)
        self.assertEqual(publish.call_count, 2)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()),
                         ["one.crilayla", "two.crilayla"])

    def test_one_archive_validation_and_index_for_multiple_members(self):
        from portlib import cpk_events
        with patch.object(module, "entries", wraps=cpk_events.entries) as index:
            report = module.export_batch(self.archive, self.sha, self.manifest, self.out)
        self.assertEqual(index.call_count, 1)
        self.assertEqual(len(report["members"]), 2)
        self.assertEqual([r["candidate_decoded_sha256"] for r in report["members"]],
                         [hashlib.sha256(decompress((self.out / r["output"]).read_bytes())).hexdigest()
                          for r in report["members"]])

    def test_wrong_source_hash_rejects_before_index_or_output(self):
        with patch.object(module, "entries", side_effect=AssertionError("parsed before hash")):
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                module.export_batch(self.archive, "0" * 64, self.manifest, self.out)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_no_full_archive_read(self):
        with patch.object(pathlib.Path, "read_bytes", side_effect=AssertionError("full read")):
            module.export_batch(self.archive, self.sha, self.manifest, self.out)
        self.assertEqual(len(list(self.out.iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
