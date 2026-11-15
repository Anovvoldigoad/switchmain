"""Restoration of per-mod NSC editor index artifacts is offline-only."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from merge_pc_moveset_nsc_manifests import merge
from split_pc_moveset_nsc_manifests import restore


def fixture():
    sources = []
    for name, event in (("a/unsafe", "first"), ("b", "second")):
        raw = json.dumps({"source_version": "nsc", "events": [
            {"event_id": event, "function_index": 0}]}).encode()
        sources.append((name, raw, hashlib.sha256(raw).hexdigest()))
    return merge(sources)


class RestoreTests(unittest.TestCase):
    def test_roundtrip_and_safe_filenames(self):
        payload, proof = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = restore(payload, proof, out)
            self.assertEqual([x["file"] for x in result],
                             ["00.nsc.json", "01.nsc.json"])
            self.assertEqual(result[0]["name"], "a/unsafe")
            for row in result:
                raw = (out / row["file"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
            self.assertEqual(json.loads((out / result[1]["file"]).read_bytes())
                             ["events"][0]["event_id"], "second")

    def test_tamper_and_preexisting_output_do_not_write(self):
        payload, proof = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with self.assertRaises(ValueError):
                restore(payload + b" ", proof, out)
            self.assertEqual(list(out.iterdir()), [])
            (out / "01.nsc.json").write_text("original")
            with self.assertRaisesRegex(ValueError, "already exists"):
                restore(payload, proof, out)
            self.assertEqual((out / "01.nsc.json").read_text(), "original")
            self.assertFalse((out / "00.nsc.json").exists())

    def test_failure_rolls_back_only_new_files(self):
        payload, proof = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            original_open = Path.open
            def fail_second(path, *args, **kwargs):
                if path.name == "01.nsc.json":
                    raise OSError("injected disk failure")
                return original_open(path, *args, **kwargs)
            with patch.object(Path, "open", fail_second):
                with self.assertRaisesRegex(OSError, "disk failure"):
                    restore(payload, proof, out)
            self.assertEqual(list(out.iterdir()), [])

    def test_missing_directory_and_forged_provenance(self):
        payload, proof = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            with self.assertRaisesRegex(ValueError, "already exist"):
                restore(payload, proof, out / "missing")
            forged = json.loads(json.dumps(proof))
            forged["sources"][0]["converted_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "Source converted"):
                restore(payload, forged, out)
            self.assertEqual(list(out.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
