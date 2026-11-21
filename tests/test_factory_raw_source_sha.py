"""Authenticated raw PC factory source input regression (offline only)."""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from portlib.factory_profile import decode


def record(name, owner):
    return name.encode("ascii").ljust(24, b"\0") + struct.pack("<H", owner) + bytes(6)


class AuthenticatedRawFactoryTests(unittest.TestCase):
    def test_ordered_pinned_inputs_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "a.bin", root / "b.bin"
            a.write_bytes(record("2dnz", 280))
            b.write_bytes(record("2nrt", 281))
            da, db = (hashlib.sha256(p.read_bytes()).hexdigest() for p in (a, b))
            base = [sys.executable, str(ROOT / "tools/compile_factory_profile.py"),
                    "--param", str(a), "--param", str(b),
                    "--param-sha256", da, "--param-sha256", db, "--output"]
            out = root / "good"
            result = subprocess.run(base + [str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(decode((out / "factory.profile").read_bytes()), {280: 58, 281: 1})
            report = json.loads((out / "factory_profile_report.json").read_text())
            self.assertEqual([x["sha256"] for x in report["sources"]], [da, db])
            self.assertTrue(all(x["authenticated"] for x in report["sources"]))
            for index, args in enumerate((
                base[:-3] + ["--output", str(root / "missing")],
                base[:6] + ["--param-sha256", db, "--param-sha256", da, "--output", str(root / "reversed")],
            )):
                bad = subprocess.run(args, capture_output=True, text=True)
                self.assertNotEqual(bad.returncode, 0, bad.stderr)
            self.assertFalse((root / "missing").exists())
            self.assertFalse((root / "reversed").exists())
            b.write_bytes(record("2nrt", 282))
            tampered = root / "tampered"
            self.assertNotEqual(subprocess.run(base + [str(tampered)], capture_output=True).returncode, 0)
            self.assertFalse(tampered.exists())


if __name__ == "__main__":
    unittest.main()
