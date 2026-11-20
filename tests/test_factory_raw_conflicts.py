"""Raw PC specialCondParam collision policy before offline factory packaging."""
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
from portlib.factory_profile import compile_records, decode


def record(name, owner):
    return name.encode("ascii").ljust(24, b"\0") + struct.pack("<H", owner) + bytes(6)


class RawFactoryCollisionTests(unittest.TestCase):
    def test_disjoint_and_last_wins_preserved(self):
        a = record("2dnz", 280)
        b = record("2nrt", 281)
        output, rows = compile_records([("a", a), ("b", b)], {280: 280, 281: 281},
                                       conflicts="reject")
        self.assertEqual(decode(output), {280: 58, 281: 1})
        output, rows = compile_records([("a", a), ("b", b.replace(b"\x19\x01", b"\x18\x01"))])
        self.assertEqual(decode(output), {280: 1})
        self.assertTrue(rows[-1]["replaces_previous_mapping"])

    def test_reject_same_owner_and_remapped_collision(self):
        a = record("2dnz", 280)
        b = record("2nrt", 281)
        for inputs, mapping in [
            ([("a", a), ("b", record("2nrt", 280))], {}),
            ([("a", a + record("2nrt", 280))], {}),
            ([("a", a), ("b", b)], {280: 281}),
        ]:
            with self.subTest(mapping=mapping, count=len(inputs)):
                with self.assertRaisesRegex(ValueError, "collides"):
                    compile_records(inputs, mapping, conflicts="reject")

    def test_invalid_policy_and_invalid_record(self):
        with self.assertRaisesRegex(ValueError, "policy"):
            compile_records([], conflicts="typo")
        with self.assertRaises(ValueError):
            compile_records([("bad", bytes(31))], conflicts="reject")

    def test_cli_reject_before_output_and_report_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "a.bin", root / "b.bin"
            a.write_bytes(record("2dnz", 280))
            b.write_bytes(record("2nrt", 280))
            command = [sys.executable, str(ROOT / "tools/compile_factory_profile.py"),
                       "--param", str(a), "--param", str(b), "--conflicts", "reject",
                       "--output", str(root / "reject")]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((root / "reject").exists())
            command[command.index("reject")] = "last"
            command[-1] = str(root / "last")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(decode((root / "last/factory.profile").read_bytes()), {280: 1})
            report = json.loads((root / "last/factory_profile_report.json").read_text())
            self.assertEqual(report["conflicts"], "last")
            self.assertTrue(report["records"][-1]["replaces_previous_mapping"])


if __name__ == "__main__":
    unittest.main()
