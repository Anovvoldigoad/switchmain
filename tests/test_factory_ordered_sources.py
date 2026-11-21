"""Ordered mixed-source factory precedence regression (offline only)."""
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from portlib.factory_profile import encode, decode
from compose_ordered_factory import compose


def raw(name, owner):
    return name.encode().ljust(24, b"\0") + struct.pack("<H", owner) + bytes(6)


def src(kind, label, data):
    return (kind, label, data, hashlib.sha256(data).hexdigest())


class OrderedFactoryTests(unittest.TestCase):
    def test_interleaved_precedence_and_provenance(self):
        a = src("raw", "first", raw("2dnz", 280))
        b = src("profile", "middle", encode({280: 1}))
        c = src("raw", "last", raw("2dnz", 280))
        result, ledger, sources = compose([a, b, c])
        self.assertEqual(decode(result), {280: 58})
        self.assertEqual([row["selector"] for row in ledger], [58, 1, 58])
        self.assertEqual([row["replaced"] for row in ledger], [False, True, True])
        self.assertEqual([row["label"] for row in sources], ["first", "middle", "last"])
        self.assertEqual(decode(compose([c, b, a])[0]), {280: 58})

    def test_reject_collision_and_same_source_duplicate(self):
        a = src("raw", "a", raw("2dnz", 280))
        b = src("profile", "b", encode({280: 1}))
        with self.assertRaisesRegex(ValueError, "collid"):
            compose([a, b], conflicts="reject")
        with self.assertRaisesRegex(ValueError, "collid"):
            compose([src("raw", "dupe", raw("2dnz", 280) * 2)], conflicts="reject")

    def test_hash_kind_label_and_boundary(self):
        a = src("profile", "a", encode({}))
        self.assertEqual(decode(compose([a])[0]), {})
        with self.assertRaisesRegex(ValueError, "SHA256"):
            compose([(*a[:3], "0" * 64)])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compose([a, a])
        with self.assertRaisesRegex(ValueError, "kind"):
            compose([("other", "x", b"", hashlib.sha256(b"").hexdigest())])

    def test_cli_fail_closed_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            a = d / "raw"
            a.write_bytes(raw("2dnz", 280))
            sha = hashlib.sha256(a.read_bytes()).hexdigest()
            base = [sys.executable, str(ROOT / "tools/compose_ordered_factory.py"),
                    "--source", "raw", "one", str(a), sha]
            ok = subprocess.run(base + ["--output", str(d / "ok")], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(decode((d / "ok/factory.profile").read_bytes()), {280: 58})
            bad = subprocess.run(base[:-1] + ["0" * 64, "--output", str(d / "bad")],
                                 capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse((d / "bad").exists())


if __name__ == "__main__":
    unittest.main()
