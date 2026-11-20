import hashlib
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from merge_factory_profiles import merge
from portlib.factory_profile import encode, decode, seal


class MergeFactoryProfiles(unittest.TestCase):
    def source(self, name, data):
        return name, data, hashlib.sha256(data).hexdigest()

    def test_priority_and_disjoint(self):
        a = encode({1: 1, 2: 2})
        b = encode({2: 3, 1023: 4})
        output, ledger = merge([self.source("a", a), self.source("b", b)])
        self.assertEqual(decode(output), {1: 1, 2: 3, 1023: 4})
        self.assertEqual([x["replaced"] for x in ledger], [False, False, True, False])
        self.assertEqual(ledger[2]["previous_selector"], 2)
        reverse, _ = merge([self.source("b", b), self.source("a", a)])
        self.assertEqual(decode(reverse)[2], 2)
        self.assertNotEqual(output, reverse)

    def test_reject_collision_before_publication(self):
        a = encode({2: 2})
        b = encode({2: 3})
        with self.assertRaisesRegex(ValueError, "collides"):
            merge([self.source("a", a), self.source("b", b)], conflicts="reject")

    def test_corruption_and_wrong_digest(self):
        a = encode({1: 1})
        damaged = bytearray(a)
        damaged[100] ^= 1
        with self.assertRaisesRegex(ValueError, "SHA256"):
            merge([("a", a, "0" * 64)])
        with self.assertRaises(ValueError):
            merge([self.source("a", bytes(damaged))])
        with self.assertRaises(ValueError):
            merge([self.source("a", a)], conflicts="invalid")

    def test_empty_and_capacity(self):
        output, ledger = merge([])
        self.assertEqual(decode(output), {})
        self.assertEqual(ledger, [])
        full = encode({i: 1 for i in range(1024)})
        self.assertEqual(decode(merge([self.source("full", full)])[0]), decode(full))

    def test_cli_exclusive_output_and_no_partial_on_error(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = root / "input.profile"
            profile.write_bytes(encode({5: 1}))
            digest = hashlib.sha256(profile.read_bytes()).hexdigest()
            out = root / "out"
            command = [sys.executable, "tools/merge_factory_profiles.py",
                       "--source", "mod", str(profile), digest, "--output", str(out)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(decode((out / "factory.profile").read_bytes()), {5: 1})
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            wrong = root / "bad"
            command[-1] = str(wrong)
            command[-3] = "0" * 64
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertFalse(wrong.exists())


if __name__ == "__main__":
    unittest.main()
