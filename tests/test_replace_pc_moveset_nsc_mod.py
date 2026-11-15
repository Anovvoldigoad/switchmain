"""SHA-pinned PC editor replacement must rebuild rather than splice untrusted events."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from merge_pc_moveset_nsc_manifests import merge
from replace_pc_moveset_nsc_mod import replace_verified
from verify_pc_moveset_nsc_sources import verify


def source(name, eid):
    raw = json.dumps({"source_version": "nsc", "events": [
        {"event_id": eid, "function_index": 0}]}).encode()
    return name, raw, hashlib.sha256(raw).hexdigest()


class ReplaceModTests(unittest.TestCase):
    def setUp(self):
        self.sources = [source("a", "a"), source("b", "b"), source("c", "c")]
        self.payload, self.proof = merge(self.sources)

    def test_rebuild_preserves_order_and_exact_provenance(self):
        replacement = source("b", "new")
        result, proof = replace_verified(self.payload, self.proof, self.sources, "b", replacement)
        updated = [self.sources[0], replacement, self.sources[2]]
        self.assertEqual((result, proof), merge(updated))
        self.assertEqual(verify(result, proof, updated)["source_count"], 3)

    def test_rejects_collision_and_wrong_digest(self):
        with self.assertRaisesRegex(ValueError, "collision"):
            replace_verified(self.payload, self.proof, self.sources, "b", source("b", "a"))
        name, raw, sha = source("b", "new")
        with self.assertRaises(ValueError):
            replace_verified(self.payload, self.proof, self.sources, "b", (name, raw, "0" * 64))

    def test_rejects_missing_wrong_name_and_forged_original(self):
        with self.assertRaises(ValueError):
            replace_verified(self.payload, self.proof, self.sources, "missing", source("missing", "x"))
        with self.assertRaises(ValueError):
            replace_verified(self.payload, self.proof, self.sources, "b", source("other", "x"))
        forged = dict(self.proof)
        forged["output_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            replace_verified(self.payload, forged, self.sources, "b", source("b", "new"))

    def test_single_mod_boundary_and_original_immutability(self):
        original = [source("solo", "old")]
        payload, proof = merge(original)
        replacement = source("solo", "new")
        result, evidence = replace_verified(payload, proof, original, "solo", replacement)
        self.assertEqual((result, evidence), merge([replacement]))
        self.assertEqual((payload, proof), merge(original))


if __name__ == "__main__":
    unittest.main()
