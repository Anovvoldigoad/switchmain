import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from portlib.cpk_same_size import replace_many_same_size
from portlib.prm_events import mark
from portlib.cpk_events import entries
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "verify_same_size_cpk.py"


class VerifyCliTests(unittest.TestCase):
    def setUp(self):
        original = fixture([event(14), event(0), event(15)])
        converted, _ = mark(original)
        self.member = "data/spc/selected.bin.xfbin"
        self.source = cpk(
            [(self.member, literal_stream(original)), ("data/other", b"untouched")],
            lambda rows: rows[0].update({"ExtractSize": len(original)}))
        self.source_sha = hashlib.sha256(self.source).hexdigest()
        self.output, _ = replace_many_same_size(
            self.source, self.source_sha, {self.member: literal_stream(converted)})
        self.output_sha = hashlib.sha256(self.output).hexdigest()

    def invoke(self, output=None, output_sha=None, selected=None):
        with tempfile.TemporaryDirectory() as directory:
            src, dst = Path(directory) / "source.cpk", Path(directory) / "output.cpk"
            src.write_bytes(self.source)
            dst.write_bytes(self.output if output is None else output)
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(src), str(dst),
                 self.source_sha, self.output_sha if output_sha is None else output_sha,
                 *(selected if selected is not None else [self.member])],
                capture_output=True, text=True)

    def test_valid_archive(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        proof = json.loads(result.stdout)
        self.assertEqual(proof["output_sha256"], self.output_sha)
        self.assertFalse(proof["runtime_verified"])

    def test_wrong_hash(self):
        result = self.invoke(output_sha="0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(result.stdout)

    def test_tampered_unselected_with_updated_hash(self):
        start = entries(self.output)["data/other"]["offset"]
        changed = self.output[:start] + b"CHANGED!!" + self.output[start + 9:]
        result = self.invoke(output=changed, output_sha=hashlib.sha256(changed).hexdigest())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unselected member", result.stderr)

    def test_unknown_member(self):
        result = self.invoke(selected=["missing"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown selected member", result.stderr)


if __name__ == "__main__":
    unittest.main()
