"""Multi-mod editor index merge, not binary moveset conversion."""
import hashlib
import json
import sys
import unittest
import subprocess
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from merge_pc_moveset_nsc_manifests import merge, split, analyze_collisions
from pc_moveset_event_preflight import audit

def source(name, version, rows):
    raw = json.dumps({"source_version": version, "events": rows}).encode()
    return name, raw, hashlib.sha256(raw).hexdigest()

class MultiModIndexMerge(unittest.TestCase):
    def test_authenticated_collision_report_and_negative_sources(self):
        a = source("alpha", "nsc", [{"event_id": "same", "function_index": 0},
                                     {"event_id": "only_a", "function_index": 0}])
        b = source("beta", "nsc", [{"event_id": "same", "function_index": 1}])
        c = source("gamma", "nsc", [{"event_id": "same", "function_index": 2}])
        report = analyze_collisions([a, b, c])
        self.assertEqual(report["collisions"], [
            {"event_id": "same", "first_source": "alpha", "second_source": "beta"},
            {"event_id": "same", "first_source": "alpha", "second_source": "gamma"}])
        self.assertEqual([x["input_sha256"] for x in report["sources"]],
                         [a[2], b[2], c[2]])
        self.assertFalse(report["native_switch_abi_verified"])
        self.assertEqual(analyze_collisions([a])["collisions"], [])
        with self.assertRaises(ValueError):
            analyze_collisions([a, ("beta", b[1] + b" ", b[2])])
        with self.assertRaises(ValueError):
            analyze_collisions([a, a])
        with self.assertRaises(ValueError):
            analyze_collisions([])
        with self.assertRaises(ValueError):
            analyze_collisions([a] * 65)

    def test_collision_cli_report_and_fail_closed_publication(self):
        a = source("alpha", "nsc", [{"event_id": "shared", "function_index": 0}])
        b = source("beta", "nsc", [{"event_id": "shared", "function_index": 1}])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [root / "a.json", root / "b.json"]
            for path, item in zip(paths, (a, b)):
                path.write_bytes(item[1])
            output, evidence = root / "report.json", root / "proof.json"
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] /
                   "tools" / "merge_pc_moveset_nsc_manifests.py"),
                   "--collisions-only", "--source", a[0], str(paths[0]), a[2],
                   "--source", b[0], str(paths[1]), b[2],
                   "--output", str(output), "--evidence", str(evidence)]
            completed = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(output.read_bytes())
            proof = json.loads(evidence.read_bytes())
            self.assertEqual(report["collisions"], [
                {"event_id": "shared", "first_source": "alpha", "second_source": "beta"}])
            self.assertEqual(proof["report_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(proof["collision_count"], 1)
            self.assertFalse(proof["native_switch_abi_verified"])
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            output.unlink()
            evidence.unlink()
            paths[1].write_bytes(b[1] + b" ")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(output.exists())
            self.assertFalse(evidence.exists())

    def test_mixed_sources_exact_order_and_sha(self):
        a = source("alpha", "ns4", [{"event_id": "a", "function_index": 288}])
        b = source("beta", "nsc", [{"event_id": "b", "function_index": 299}])
        payload, proof = merge([a, b])
        self.assertEqual([x["function_index"] for x in json.loads(payload)["events"]], [288, 299])
        self.assertEqual(audit(json.loads(payload))["event_count"], 2)
        self.assertEqual(proof["output_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual([x["input_sha256"] for x in proof["sources"]], [a[2], b[2]])
        self.assertFalse(proof["native_switch_abi_verified"])
    def test_collisions_and_wrong_hash_fail_closed(self):
        a = source("alpha", "ns4", [{"event_id": "same", "function_index": 0}])
        b = source("beta", "nsc", [{"event_id": "same", "function_index": 1}])
        with self.assertRaisesRegex(ValueError, "collision"):
            merge([a, b])
        with self.assertRaisesRegex(ValueError, "duplicate mod"):
            merge([a, a])
        with self.assertRaises(ValueError):
            merge([("alpha", a[1], "0" * 64)])
        with self.assertRaises(ValueError):
            merge([source("bad", "ns4", [{"event_id": "x", "function_index": 289}])])
    def test_reversible_provenance_and_tamper(self):
        a = source("alpha", "ns4", [{"event_id": "a", "function_index": 288}])
        b = source("beta", "nsc", [{"event_id": "b", "function_index": 299}])
        payload, proof = merge([a, b])
        parts = split(payload, proof)
        self.assertEqual([name for name, _ in parts], ["alpha", "beta"])
        self.assertEqual([json.loads(raw)["events"][0]["event_id"] for _, raw in parts], ["a", "b"])
        with self.assertRaisesRegex(ValueError, "Merged payload SHA256"):
            split(payload + b" ", proof)
        forged = json.loads(json.dumps(proof))
        forged["sources"][1]["start"] = 0
        with self.assertRaisesRegex(ValueError, "source event range"):
            split(payload, forged)
        forged = json.loads(json.dumps(proof))
        forged["sources"][0]["converted_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Source converted SHA256"):
            split(payload, forged)

    def test_missing_source_ranges_and_unattributed_events(self):
        a = source("first", "nsc", [{"event_id": "a", "function_index": 0}])
        b = source("second", "nsc", [{"event_id": "b", "function_index": 0}])
        payload, proof = merge([a, b])
        self.assertEqual([len(json.loads(raw)["events"]) for _, raw in split(payload, proof)], [1, 1])
        forged = json.loads(json.dumps(proof))
        forged["sources"].pop()
        with self.assertRaisesRegex(ValueError, "Unattributed"):
            split(payload, forged)

    def test_limits(self):
        with self.assertRaises(ValueError):
            merge([])
        a = source("a", "nsc", [{"event_id": "a", "function_index": 0}])
        with self.assertRaises(ValueError):
            merge([(str(i), a[1], a[2]) for i in range(65)])

if __name__ == "__main__":
    unittest.main()
