"""Multi-mod editor index merge, not binary moveset conversion."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from merge_pc_moveset_nsc_manifests import merge, split
from pc_moveset_event_preflight import audit

def source(name, version, rows):
    raw = json.dumps({"source_version": version, "events": rows}).encode()
    return name, raw, hashlib.sha256(raw).hexdigest()

class MultiModIndexMerge(unittest.TestCase):
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
