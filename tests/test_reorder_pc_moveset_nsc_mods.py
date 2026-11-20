"""Source-authenticated offline multi-mod reordering regressions."""
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
from reorder_pc_moveset_nsc_mods import reorder_verified
from verify_pc_moveset_nsc_sources import verify


def source(name, event):
    raw = json.dumps({"source_version": "nsc", "events": [
        {"event_id": event, "function_index": 0}]}).encode()
    return (name, raw, hashlib.sha256(raw).hexdigest())


class ReorderTests(unittest.TestCase):
    def setUp(self):
        self.sources = [source("alpha", "a"), source("beta", "b"), source("gamma", "c")]
        self.payload, self.proof = merge(self.sources)

    def test_permutation_exact_replay_and_roundtrip(self):
        order = ["gamma", "alpha", "beta"]
        result, evidence = reorder_verified(self.payload, self.proof, self.sources, order)
        expected = merge([self.sources[2], self.sources[0], self.sources[1]])
        self.assertEqual((result, evidence), expected)
        self.assertEqual([name for name, _ in split(result, evidence)], order)
        restored = reorder_verified(result, evidence,
                                   [self.sources[2], self.sources[0], self.sources[1]],
                                   ["alpha", "beta", "gamma"])
        self.assertEqual(restored, (self.payload, self.proof))
        self.assertFalse(evidence["native_switch_abi_verified"])

    def test_invalid_permutations_and_forged_sources_fail_closed(self):
        for order in ([], ["alpha"], ["alpha", "alpha", "gamma"],
                      ["alpha", "beta", "unknown"], ["alpha", 5, "gamma"]):
            with self.subTest(order=order), self.assertRaises(ValueError):
                reorder_verified(self.payload, self.proof, self.sources, order)
        forged = list(self.sources)
        forged[1] = (forged[1][0], forged[1][1] + b" ", forged[1][2])
        with self.assertRaises(ValueError):
            reorder_verified(self.payload, self.proof, forged,
                             ["gamma", "alpha", "beta"])
        with self.assertRaises(ValueError):
            reorder_verified(self.payload + b" ", self.proof, self.sources,
                             ["gamma", "alpha", "beta"])

    def test_cli_publishes_both_or_neither(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "merged.json").write_bytes(self.payload)
            (d / "proof.json").write_text(json.dumps(self.proof))
            argv = []
            for name, raw, sha in self.sources:
                file = d / (name + ".json")
                file.write_bytes(raw)
                argv += ["--source", name, str(file), sha]
            out, evidence = d / "out.json", d / "out-proof.json"
            cmd = [sys.executable, str(ROOT / "tools" / "reorder_pc_moveset_nsc_mods.py"),
                   "--merged", str(d / "merged.json"), "--evidence", str(d / "proof.json"),
                   *argv, "--order", "gamma", "alpha", "beta",
                   "--output", str(out), "--output-evidence", str(evidence)]
            run = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((out.read_bytes(), json.loads(evidence.read_text())),
                             reorder_verified(self.payload, self.proof, self.sources,
                                              ["gamma", "alpha", "beta"]))
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            out.unlink()
            evidence.unlink()
            cmd[cmd.index("gamma")] = "unknown"
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(out.exists())
            self.assertFalse(evidence.exists())


if __name__ == "__main__":
    unittest.main()
