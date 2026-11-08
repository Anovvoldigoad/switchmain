"""Real intake workflow test with synthetic CPKs; never claims original-game proof."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_cpk_events import cpk
from test_crilayla_readonly import fixture
from inspect_cpk_payloads import capture

PLAIN = "data/spc/ordinary.bin.xfbin"
PACKED = "data/spc/compressed.bin.xfbin"
ROOT = Path(__file__).resolve().parents[1]


def archive_fixture(compressed= None):
    packed = fixture(b"ABCABC") if compressed is None else compressed
    def adjust(rows):
        rows[1]["ExtractSize"] = 262
    return cpk([(PLAIN, b"\x00ABC\xff"), (PACKED, packed)], mutator=adjust)


class CPKEvidenceIntake(unittest.TestCase):
    def test_source_pins_exact_output_manifest_and_no_source_change(self):
        archive = archive_fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "stock.cpk"
            source.write_bytes(archive)
            digest = hashlib.sha256(archive).hexdigest()
            report = capture(source, digest.upper(), [PLAIN, PACKED], root / "evidence")
            self.assertEqual(source.read_bytes(), archive)
            self.assertEqual(report["cpk_sha256"], digest)
            self.assertEqual(report["total_decoded_bytes"], 267)
            self.assertEqual([e["encoding"] for e in report["entries"]],
                             ["identity", "CRILAYLA"])
            for item, value in zip(report["entries"],
                                   (b"\x00ABC\xff", bytes(range(256)) + b"ABCABC")):
                recovered = (root / "evidence" / item["output"]).read_bytes()
                self.assertEqual(recovered, value)
                self.assertEqual(item["sha256"], hashlib.sha256(value).hexdigest())
            self.assertEqual(json.loads((root / "evidence" / "manifest.json").read_text()), report)
            self.assertFalse(report["native_engine_abi_verified"])
            self.assertFalse(report["uzuy_tested"])

    def test_fail_closed_before_outputs_for_hash_paths_and_limits(self):
        raw = archive_fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "stock.cpk"
            source.write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            cases = [
                ("0" * 64, [PLAIN], 267),
                (sha, [PLAIN, PLAIN], 267),
                (sha, [PLAIN, PLAIN.upper()], 267),
                (sha, ["../" + PLAIN], 267),
                (sha, ["data/spc/missing"], 267),
                (sha, [PLAIN, PACKED], 266),
                (sha, [PLAIN, PACKED], 0),
                (sha, [], 267),
                (sha, [PLAIN] * 17, 267)
            ]
            for i, (digest, paths, limit) in enumerate(cases):
                target = root / f"bad_{i}"
                with self.subTest(index=i), self.assertRaises(ValueError):
                    capture(source, digest, paths, target, max_total_bytes=limit)
                self.assertFalse(target.exists())
            self.assertEqual(source.read_bytes(), raw)

    def test_corrupt_compression_and_existing_destination_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "corrupt.cpk"
            source.write_bytes(archive_fixture(compressed=fixture(b"ABCABC")[:-1]))
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                capture(source, sha, [PACKED], root / "invalid")
            self.assertFalse((root / "invalid").exists())
            source.write_bytes(archive_fixture())
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            occupied = root / "occupied"
            occupied.mkdir()
            (occupied / "sentinel").write_bytes(b"unchanged")
            with self.assertRaises(FileExistsError):
                capture(source, sha, [PACKED], occupied)
            self.assertEqual((occupied / "sentinel").read_bytes(), b"unchanged")

    def test_cli_end_to_end_and_wrong_sha_nonzero(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "stock.cpk"
            source.write_bytes(archive_fixture())
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            cmd = [sys.executable, str(ROOT / "tools" / "inspect_cpk_payloads.py"),
                   "--cpk", str(source), "--expected-sha256", sha,
                   "--entry", PACKED, "--out-dir", str(root / "out")]
            successful = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(successful.returncode, 0, successful.stderr)
            self.assertIn("CPK_READ_ONLY_EVIDENCE", successful.stdout)
            self.assertEqual((root / "out" / "0000.bin").read_bytes(),
                             bytes(range(256)) + b"ABCABC")
            invalid = cmd.copy()
            invalid[invalid.index("--expected-sha256") + 1] = "f" * 64
            invalid[invalid.index("--out-dir") + 1] = str(root / "bad")
            result = subprocess.run(invalid, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "bad").exists())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), sha)


    def test_inventory_exact_index_hashes_and_suffix_cli(self):
        from inspect_cpk_payloads import inventory
        from portlib.cpk_events import entries
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "stock.cpk"
            raw = archive_fixture()
            source.write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            index = entries(raw)
            report = inventory(source, sha, suffix=".bin.xfbin")
            self.assertEqual(report["indexed_entries"], 2)
            self.assertEqual(report["selected_entries"], 2)
            self.assertEqual([r["entry"] for r in report["entries"]], sorted(index))
            for row in report["entries"]:
                item = index[row["entry"]]
                payload = raw[item["offset"]:item["offset"] + item["stored_size"]]
                self.assertEqual(row["stored_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(inventory(source, sha, suffix=".notfound")["entries"], [])
            cmd = [sys.executable, str(ROOT / "tools" / "inspect_cpk_payloads.py"),
                   "--cpk", str(source), "--expected-sha256", sha,
                   "--inventory", "--suffix", ".xfbin"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), report)
            self.assertEqual(sorted(root.iterdir()), [source])
            for wrong in (
                cmd + ["--entry", PLAIN],
                cmd + ["--out-dir", str(root / "bad")],
                cmd[:-1] + ["../invalid"],
            ):
                failed = subprocess.run(wrong, capture_output=True, text=True)
                self.assertNotEqual(failed.returncode, 0)
            with self.assertRaises(ValueError):
                inventory(source, "0" * 64)
            self.assertEqual(source.read_bytes(), raw)



if __name__ == "__main__":
    unittest.main()
