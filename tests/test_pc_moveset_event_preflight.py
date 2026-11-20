"""Source-index preservation is PC editor preflight, not binary conversion."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from pc_moveset_event_preflight import audit


class PCEventPreflight(unittest.TestCase):
    def test_complete_shared_range_and_nsc_only_boundaries(self):
        events = [{"event_id": str(i), "function_index": i} for i in range(289)]
        a = audit({"source_version": "ns4", "events": events})
        self.assertEqual(a["event_count"], 289)
        self.assertEqual([x["target_nsc_index"] for x in a["events"]], list(range(289)))
        self.assertTrue(all(x["source_name"] == x["target_nsc_name"] for x in a["events"]))
        self.assertFalse(a["native_switch_abi_verified"])
        b = audit({"source_version": "nsc", "events": [{"event_id": "last", "function_index": 299}]})
        self.assertEqual(b["events"][0]["target_nsc_index"], 299)

    def test_fail_closed_invalid_and_unsupported(self):
        good = {"source_version": "ns4", "events": [{"event_id": "one", "function_index": 0}]}
        bad = [
            {"source_version": "ns4", "events": []},
            {"source_version": "ns4", "events": [{"event_id": "x", "function_index": 289}]},
            {"source_version": "nsc", "events": [{"event_id": "x", "function_index": 300}]},
            {"source_version": "ns4", "events": [{"event_id": "x", "function_index": True}]},
            {"source_version": "ns4", "events": [{"event_id": "x", "function_index": -1}]},
            {"source_version": "ns4", "events": [{"event_id": "x", "function_index": 1.0}]},
            {"source_version": "ns4", "events": [{"event_id": "x", "function_index": 0}, {"event_id": "x", "function_index": 1}]},
            {"source_version": "ns4", "events": [{"event_id": "x", "function_index": 0, "payload": "unverified"}]},
            {"source_version": "unknown", "events": good["events"]},
            {**good, "native_abi": True},
        ]
        for entry in bad:
            with self.subTest(entry=entry), self.assertRaises(ValueError):
                audit(entry)

    def test_cli_sha_pinning_exact_bytes_and_no_output_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = root / "input.json"
            payload = {"source_version": "ns4", "events": [{"event_id": "one", "function_index": 160}]}
            raw = json.dumps(payload).encode()
            manifest.write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            cmd = [sys.executable, str(ROOT / "tools" / "pc_moveset_event_preflight.py"),
                   "--manifest", str(manifest), "--expected-sha256", sha,
                   "--output", str(root / "result.json")]
            ok = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            result = json.loads((root / "result.json").read_text())
            self.assertEqual(result["events"][0]["source_name"], "ME_ENTRY_PROJECTILE")
            self.assertEqual(manifest.read_bytes(), raw)
            wrong = cmd.copy()
            wrong[wrong.index("--expected-sha256") + 1] = "0" * 64
            wrong[-1] = str(root / "invalid.json")
            failed = subprocess.run(wrong, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertFalse((root / "invalid.json").exists())
            self.assertEqual(manifest.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
