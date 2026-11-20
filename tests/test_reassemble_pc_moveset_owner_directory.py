import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from merge_pc_moveset_nsc_manifests import merge_resolved, publish_partition_directory
from reassemble_pc_moveset_owner_directory import restore

def source(name, events):
    raw = (json.dumps({"source_version": "nsc", "events": events}) + "\n").encode()
    return (name, raw, hashlib.sha256(raw).hexdigest())

class ReassembleTests(unittest.TestCase):
    def test_replay_and_fail_closed(self):
        a = source("a", [{"event_id": "same", "function_index": 1},
                         {"event_id": "only_a", "function_index": 3}])
        b = source("b", [{"event_id": "same", "function_index": 2}])
        sources = [a, b]
        merged, proof = merge_resolved(sources, {"same": "b"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "parts"
            publish_partition_directory(directory, merged, proof, sources)
            self.assertEqual(restore(directory, proof, sources), merged)
            pa, pb = root / "a.json", root / "b.json"
            pa.write_bytes(a[1]); pb.write_bytes(b[1])
            evidence, output = root / "proof.json", root / "out.json"
            evidence.write_text(json.dumps(proof))
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] / "tools" /
                   "reassemble_pc_moveset_owner_directory.py"), "--source", "a", str(pa), a[2],
                   "--source", "b", str(pb), b[2], "--directory", str(directory),
                   "--evidence", str(evidence), "--output", str(output)]
            def run():
                return subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run().returncode, 0)
            self.assertEqual(output.read_bytes(), merged)
            self.assertNotEqual(run().returncode, 0)
            output.unlink()
            for path in (directory / "000.json", directory / "index.json"):
                saved = path.read_bytes()
                path.write_bytes(saved + b" ")
                self.assertNotEqual(run().returncode, 0)
                self.assertFalse(output.exists())
                path.write_bytes(saved)
            (directory / "extra").write_bytes(b"x")
            self.assertNotEqual(run().returncode, 0)
            (directory / "extra").unlink()
            pb.write_bytes(b[1] + b" ")
            self.assertNotEqual(run().returncode, 0)
            self.assertFalse(output.exists())
            with self.assertRaises(ValueError):
                restore(directory, dict(proof, output_sha256="0" * 64), sources)

if __name__ == "__main__":
    unittest.main()
