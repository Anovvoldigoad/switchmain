"""Offline per-mod removal must preserve replay of every retained source."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from merge_pc_moveset_nsc_manifests import merge, split
from remove_pc_moveset_nsc_mod import remove_mod, remove_verified
from verify_pc_moveset_nsc_sources import verify


def source(name, version, eid, index):
    raw = json.dumps({"source_version": version, "events": [
        {"event_id": eid, "function_index": index}]}).encode()
    return name, raw, hashlib.sha256(raw).hexdigest()


class RemoveModTests(unittest.TestCase):
    def setUp(self):
        self.sources = [source("alpha", "ns4", "a", 0),
                        source("beta", "nsc", "b", 299),
                        source("gamma", "ns4", "c", 160)]
        self.payload, self.proof = merge(self.sources)

    def test_remove_middle_preserves_exact_source_replay(self):
        result, proof = remove_mod(self.payload, self.proof, "beta")
        self.assertEqual([x[0] for x in split(result, proof)], ["alpha", "gamma"])
        self.assertEqual([x["start"] for x in proof["sources"]], [0, 1])
        self.assertEqual(verify(result, proof, [self.sources[0], self.sources[2]])["source_count"], 2)
        expected, expected_proof = merge([self.sources[0], self.sources[2]])
        self.assertEqual((result, proof), (expected, expected_proof))
        self.assertEqual(remove_mod(self.payload, self.proof, "alpha")[1]["event_count"], 2)
        self.assertEqual(remove_mod(self.payload, self.proof, "gamma")[1]["event_count"], 2)

    def test_fail_closed_missing_final_and_forged_proof(self):
        with self.assertRaises(ValueError):
            remove_mod(self.payload, self.proof, "missing")
        one, evidence = merge(self.sources[:1])
        with self.assertRaises(ValueError):
            remove_mod(one, evidence, "alpha")
        forged = json.loads(json.dumps(self.proof))
        forged["sources"][1]["converted_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            remove_mod(self.payload, forged, "beta")
        with self.assertRaises(ValueError):
            remove_mod(self.payload + b" ", self.proof, "beta")

    def test_authenticated_removal_rejects_rewritten_hashes_and_wrong_order(self):
        result, proof = remove_verified(self.payload, self.proof, 'beta', self.sources)
        verify(result, proof, [self.sources[0], self.sources[2]])
        with self.assertRaises(ValueError):
            remove_verified(self.payload, self.proof, 'beta', list(reversed(self.sources)))
        forged = json.loads(json.dumps(self.proof))
        forged['sources'][0]['input_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            remove_verified(self.payload, forged, 'beta', self.sources)
        changed = list(self.sources)
        name, raw, sha = changed[0]
        altered = raw + b' '
        changed[0] = (name, altered, hashlib.sha256(altered).hexdigest())
        with self.assertRaises(ValueError):
            remove_verified(self.payload, self.proof, 'beta', changed)
        with self.assertRaises(ValueError):
            remove_verified(self.payload, self.proof, 'beta', self.sources[:-1])

    def test_cli_atomic_publication_and_wrong_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            merged, evidence = d / "merged.json", d / "proof.json"
            merged.write_bytes(self.payload)
            evidence.write_text(json.dumps(self.proof))
            out, report = d / "result.json", d / "result-proof.json"
            source_args = []
            for name, raw, sha in self.sources:
                path = d / (name + ".json")
                path.write_bytes(raw)
                source_args.extend(["--source", name, str(path), sha])
            cmd = [sys.executable, str(ROOT / "tools" / "remove_pc_moveset_nsc_mod.py"),
                   "--merged", str(merged), "--evidence", str(evidence),
                   "--remove", "beta", "--output", str(out),
                   "--output-evidence", str(report)] + source_args
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((out.read_bytes(), json.loads(report.read_text())),
                             remove_mod(self.payload, self.proof, "beta"))
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(merged.read_bytes(), self.payload)
            out.unlink()
            report.unlink()
            cmd[cmd.index("--remove") + 1] = "missing"
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(out.exists())
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
