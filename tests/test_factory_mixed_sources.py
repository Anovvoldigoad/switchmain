"""Mixed raw-PC and authenticated factory profile composition regression."""
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
from portlib.factory_profile import encode, decode


class MixedFactoryTests(unittest.TestCase):
    def test_priority_collision_and_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            raw = d / "raw"
            raw.write_bytes(b"2dnz".ljust(24, b"\0") + struct.pack("<H", 280) + bytes(6))
            profile = d / "profile"
            profile.write_bytes(encode({280: 1, 281: 58}))
            digest = hashlib.sha256(profile.read_bytes()).hexdigest()
            base = [sys.executable, str(ROOT / "tools/compile_factory_profile.py"),
                    "--param", str(raw), "--profile", "mod2", str(profile), digest]
            result = subprocess.run(base + ["--output", str(d / "ok")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(decode((d / "ok/factory.profile").read_bytes()), {280: 1, 281: 58})
            report = json.loads((d / "ok/factory_profile_report.json").read_text())
            self.assertTrue(report["records"][-2]["replaces_previous_mapping"])
            self.assertEqual(report["sources"][-1]["sha256"], digest)
            rejected = subprocess.run(base + ["--conflicts", "reject", "--output", str(d / "reject")],
                                      capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertFalse((d / "reject").exists())
            profile.write_bytes(encode({281: 58, 282: 1}))
            tampered = subprocess.run(base + ["--output", str(d / "tampered")],
                                     capture_output=True, text=True)
            self.assertNotEqual(tampered.returncode, 0)
            self.assertFalse((d / "tampered").exists())

    def test_disjoint_and_duplicate_label(self):
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            a = d / "a"
            a.write_bytes(encode({1: 2}))
            sha = hashlib.sha256(a.read_bytes()).hexdigest()
            cmd = [sys.executable, str(ROOT / "tools/compile_factory_profile.py"),
                   "--profile", "a", str(a), sha]
            ok = subprocess.run(cmd + ["--conflicts", "reject", "--output", str(d / "ok")],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(decode((d / "ok/factory.profile").read_bytes()), {1: 2})
            bad = subprocess.run(cmd + ["--profile", "a", str(a), sha,
                                        "--output", str(d / "bad")], capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse((d / "bad").exists())


if __name__ == "__main__":
    unittest.main()
