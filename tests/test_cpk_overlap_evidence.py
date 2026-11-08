"""Synthetic multi-archive conflict evidence; never asserts a runtime winner."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_cpk_events import cpk
from test_crilayla_readonly import fixture
from compare_cpk_overlays import compare, MAX_DECODED_COMPARE

ROOT = Path(__file__).resolve().parents[1]


class CPKOverlapEvidence(unittest.TestCase):
    def test_disjoint_equal_different_and_casefold_collision(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            names = ("data/a.xfbin", "data/b.xfbin", "data/c.xfbin")
            raw1 = cpk([(names[0], b"same"), (names[1], b"old")])
            raw2 = cpk([(names[0].upper(), b"same"), (names[1], b"new"), (names[2], b"only")])
            paths = [root / "patch160.cpk", root / "patch170.cpk"]
            for path, raw in zip(paths, (raw1, raw2)):
                path.write_bytes(raw)
            pins = [(p, hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
            report = compare(pins, suffix=".xfbin")
            self.assertEqual(report["overlapping_paths"], 2)
            collisions = {x["casefold_path"]: x for x in report["conflicts"]}
            self.assertTrue(collisions[names[0]]["stored_payloads_identical"])
            self.assertFalse(collisions[names[1]]["stored_payloads_identical"])
            self.assertEqual(collisions[names[0]]["occurrences"][1]["entry"], names[0].upper())
            self.assertIsNone(collisions[names[1]]["native_winner"])
            self.assertFalse(report["native_archive_precedence_verified"])
            self.assertEqual(compare(pins, suffix=".notfound")["overlapping_paths"], 0)
            self.assertEqual([p.read_bytes() for p in paths], [raw1, raw2])
            cmd = [sys.executable, str(ROOT / "tools" / "compare_cpk_overlays.py")]
            for path, sha in pins:
                cmd.extend(["--archive", str(path), sha])
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), compare(pins))

    def test_decoded_overlap_equivalence_and_integrity(self):
        # CRILAYLA and uncompressed storage differ but decode identically.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            name = "data/a.xfbin"
            raw = bytes(range(256)) + b"ABC"
            packed = fixture(b"ABC")
            def compressed_size(rows):
                rows[0]["ExtractSize"] = len(raw)
            files = [root / "one.cpk", root / "two.cpk"]
            before = [cpk([(name, raw)]), cpk([(name, packed)], mutator=compressed_size)]
            for path, value in zip(files, before):
                path.write_bytes(value)
            pins = [(p, hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
            result = compare(pins, decoded=True)
            overlap = result["conflicts"][0]
            self.assertFalse(overlap["stored_payloads_identical"])
            self.assertTrue(overlap["decoded_payloads_identical"])
            self.assertEqual([r["decoded_sha256"] for r in overlap["occurrences"]],
                             [hashlib.sha256(raw).hexdigest()] * 2)
            self.assertIsNone(overlap["native_winner"])
            with self.assertRaises(ValueError):
                compare(pins, decoded=True, max_decoded_bytes=len(raw) * 2 - 1)
            self.assertEqual([p.read_bytes() for p in files], before)
            cmd = [sys.executable, str(ROOT / "tools" / "compare_cpk_overlays.py"),
                   "--compare-decoded", "--max-decoded-bytes", str(len(raw) * 2)]
            for path, sha in pins:
                cmd.extend(["--archive", str(path), sha])
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(json.loads(proc.stdout)["conflicts"][0]["decoded_payloads_identical"])

    def test_decoded_overlap_corrupt_stream_and_different_payloads(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            name = "data/a.xfbin"
            files = [root / "one.cpk", root / "two.cpk"]
            def size(rows):
                rows[0]["ExtractSize"] = 259
            original = cpk([(name, bytes(range(256)) + b"ABC")])
            corrupt = cpk([(name, fixture(b"ABC")[:-1])], mutator=size)
            files[0].write_bytes(original)
            files[1].write_bytes(corrupt)
            pins = [(p, hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
            with self.assertRaises(ValueError):
                compare(pins, decoded=True)
            self.assertFalse(compare(pins)["conflicts"][0]["stored_payloads_identical"])
            files[1].write_bytes(cpk([(name, bytes(range(256)) + b"ABD")]))
            pins[1] = (files[1], hashlib.sha256(files[1].read_bytes()).hexdigest())
            result = compare(pins, decoded=True)
            self.assertFalse(result["conflicts"][0]["decoded_payloads_identical"])
            self.assertFalse(result["native_archive_precedence_verified"])
            for invalid in (0, -1, MAX_DECODED_COMPARE + 1):
                with self.assertRaises(ValueError):
                    compare(pins, decoded=True, max_decoded_bytes=invalid)

    def test_fail_closed_invalid_sha_duplicate_archive_and_count(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a, b = root / "a.cpk", root / "b.cpk"
            a.write_bytes(cpk([("data/a.xfbin", b"A")]))
            b.write_bytes(cpk([("data/a.xfbin", b"B")]))
            pin_a = (a, hashlib.sha256(a.read_bytes()).hexdigest())
            pin_b = (b, hashlib.sha256(b.read_bytes()).hexdigest())
            for rows in ([], [pin_a], [pin_a, pin_a],
                         [pin_a, (b, "0" * 64)], [pin_a] * 17):
                with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                    compare(rows)
            self.assertEqual(compare([pin_a, pin_b])["overlapping_paths"], 1)
            self.assertEqual(set(root.iterdir()), {a, b})


if __name__ == "__main__":
    unittest.main()
