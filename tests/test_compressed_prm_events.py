"""Compressed PRM event feasibility: synthetic only; no compressed repacker."""
import hashlib
import unittest
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from portlib.compressed_prm_events import inspect, extract_candidate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def literal_stream(raw):
    bits = []
    for b in reversed(raw[256:]):
        bits.append(0)
        bits.extend((b >> i) & 1 for i in range(7, -1, -1))
    bits.extend([0] * (-len(bits) % 8))
    encoded = bytes(sum(bits[j+k] << (7-k) for k in range(8))
                    for j in range(0, len(bits), 8))[::-1]
    return (b"CRILAYLA" + (len(raw)-256).to_bytes(4, "little") +
            len(encoded).to_bytes(4, "little") + encoded + raw[:256])


class CompressedPRMFeasibility(unittest.TestCase):
    def test_decoded_marker_and_original_integrity(self):
        raw = fixture([event(14), event(0), event(15)])
        self.assertGreater(len(raw), 256)
        packed = literal_stream(raw)
        path = "data/spc/testprm.bin.xfbin"
        archive = cpk([(path, packed)], lambda rows: rows[0].update({"ExtractSize":len(raw)}))
        before = bytes(archive)
        report = inspect(archive, path, digest(archive))
        self.assertEqual(report["marked_records"], 2)
        self.assertEqual(report["native_event236_preserved"], 1)
        self.assertEqual(len(report["changed_decoded_offsets"]), 4)
        self.assertEqual(report["decoded_sha256"], digest(raw))
        self.assertFalse(report["compressed_archive_repacked"])
        self.assertEqual(archive, before)
        self.assertEqual(inspect(archive, path, digest(archive)), report)

    def test_extract_decoded_candidate_byte_integrity(self):
        raw = fixture([event(14), event(0), event(15)])
        path = "data/spc/testprm.bin.xfbin"
        archive = cpk([(path, literal_stream(raw))],
                      lambda rows: rows[0].update({"ExtractSize": len(raw)}))
        original = bytes(archive)
        candidate, report = extract_candidate(archive, path, digest(archive))
        self.assertEqual(len(candidate), len(raw))
        self.assertEqual(digest(candidate), report["candidate_decoded_sha256"])
        self.assertEqual([i for i, (a, b) in enumerate(zip(raw, candidate)) if a != b],
                         report["changed_decoded_offsets"])
        self.assertEqual(archive, original)
        self.assertFalse(report["compressed_archive_repacked"])
        self.assertEqual(extract_candidate(archive, path, digest(archive)),
                         (candidate, report))
        with self.assertRaises(ValueError):
            extract_candidate(archive, path, "0" * 64)
        with self.assertRaises(ValueError):
            extract_candidate(archive, path, digest(archive), decoded_limit=len(raw)-1)
        with self.assertRaises(ValueError):
            extract_candidate(archive, "data/spc/missing", digest(archive))

    def test_fail_closed(self):
        raw = fixture([event(14)])
        path = "data/spc/testprm.bin.xfbin"
        packed = literal_stream(raw)
        archive = cpk([(path, packed)], lambda rows: rows[0].update({"ExtractSize":len(raw)}))
        cases = [
            (archive, path, "0"*64, 256*1024*1024),
            (archive, "data/spc/missing", digest(archive), 256*1024*1024),
            (archive, path, digest(archive), len(raw)-1),
            (cpk([(path, packed[:-1])], lambda rows: rows[0].update({"ExtractSize":len(raw)})), path, None, 256*1024*1024),
            (cpk([(path, raw)]), path, None, 256*1024*1024),
        ]
        for data, name, sha, limit in cases:
            with self.subTest(name=name, size=len(data)), self.assertRaises(ValueError):
                inspect(data, name, sha or digest(data), decoded_limit=limit)


if __name__ == "__main__":
    unittest.main()
