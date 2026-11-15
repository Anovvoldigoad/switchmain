"""Original-source replay of PC-only multi-mod editor index artifacts."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from merge_pc_moveset_nsc_manifests import merge
from verify_pc_moveset_nsc_sources import verify


def sample(name, version, event):
    raw = json.dumps({"source_version": version, "events": [
        {"event_id": event, "function_index": 0}]}).encode()
    return name, raw, hashlib.sha256(raw).hexdigest()


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.sources = [sample("one", "ns4", "a"), sample("two", "nsc", "b")]
        self.payload, self.proof = merge(self.sources)

    def test_exact_replay(self):
        result = verify(self.payload, self.proof, self.sources)
        self.assertEqual(result["source_count"], 2)
        self.assertFalse(result["native_switch_abi_verified"])

    def test_modified_original_even_with_unchanged_merged_evidence(self):
        changed = sample("one", "ns4", "different")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            verify(self.payload, self.proof, [changed, self.sources[1]])

    def test_reordered_and_missing_sources(self):
        with self.assertRaisesRegex(ValueError, "order/name"):
            verify(self.payload, self.proof, list(reversed(self.sources)))
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            verify(self.payload, self.proof, self.sources[:1])

    def test_forged_merged_payload_and_evidence(self):
        with self.assertRaisesRegex(ValueError, "differs"):
            verify(self.payload + b" ", self.proof, self.sources)
        forged = json.loads(json.dumps(self.proof))
        forged["sources"][0]["converted_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "differs"):
            verify(self.payload, forged, self.sources)

    def test_pinned_digest_and_bounds(self):
        wrong = (self.sources[0][0], self.sources[0][1], "0" * 64)
        with self.assertRaisesRegex(ValueError, "Pinned"):
            verify(self.payload, self.proof, [wrong, self.sources[1]])
        with self.assertRaises(ValueError):
            verify(self.payload, self.proof, self.sources * 33)


if __name__ == "__main__":
    unittest.main()
