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
from split_pc_moveset_nsc_manifests import restore, restore_verified


def fixture():
    sources = []
    for name, event in (("a/unsafe", "first"), ("b", "second")):
        raw = json.dumps({"source_version": "nsc", "events": [
            {"event_id": event, "function_index": 0}]}).encode()
        sources.append((name, raw, hashlib.sha256(raw).hexdigest()))
    return merge(sources)


def source_fixture():
    sources = []
    for name, event in (("a", "first"), ("b", "second")):
        raw = json.dumps({"source_version": "nsc", "events": [
            {"event_id": event, "function_index": 0}]}).encode()
        sources.append((name, raw, hashlib.sha256(raw).hexdigest()))
    return sources


class RestoreTests(unittest.TestCase):
    def test_authenticated_restore_replays_original_bytes(self):
        sources = source_fixture()
        payload, proof = merge(sources)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = restore_verified(payload, proof, sources, out)
            self.assertEqual(len(result), 2)
            self.assertEqual([name for name, _ in
                              __import__('merge_pc_moveset_nsc_manifests').split(payload, proof)],
                             [row["name"] for row in result])
            self.assertEqual([hashlib.sha256((out / row["file"]).read_bytes()).hexdigest()
                              for row in result], [row["sha256"] for row in result])

    def test_authenticated_restore_rejects_forged_replay_and_order(self):
        sources = source_fixture()
        payload, proof = merge(sources)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            wrong = [(name, raw, '0' * 64) for name, raw, _ in sources]
            for candidate in (wrong, list(reversed(sources)),
                              sources[:1],
                              [(sources[0][0], sources[0][1] + b' ', sources[0][2]), sources[1]]):
                with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                    restore_verified(payload, proof, candidate, out)
                self.assertEqual(list(out.iterdir()), [])
            forged = dict(proof, output_sha256='0' * 64)
            with self.assertRaises(ValueError):
                restore_verified(payload, forged, sources, out)
            self.assertEqual(list(out.iterdir()), [])

    def test_selective_authenticated_restore_preserves_original_index(self):
        sources = source_fixture()
        payload, proof = merge(sources)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = restore_verified(payload, proof, sources, out, "b")
            self.assertEqual([row["file"] for row in result], ["01.nsc.json"])
            self.assertEqual(result[0]["name"], "b")
            self.assertEqual(hashlib.sha256((out / "01.nsc.json").read_bytes()).hexdigest(),
                             result[0]["sha256"])
            self.assertFalse((out / "00.nsc.json").exists())
            with self.assertRaisesRegex(ValueError, "Unknown"):
                restore_verified(payload, proof, sources, out, "missing")
            self.assertEqual(sorted(path.name for path in out.iterdir()), ["01.nsc.json"])

    def test_selective_restore_checks_only_target_collision_and_all_provenance(self):
        sources = source_fixture()
        payload, proof = merge(sources)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "00.nsc.json").write_bytes(b"untouched")
            result = restore_verified(payload, proof, sources, out, "b")
            self.assertEqual(len(result), 1)
            self.assertEqual((out / "00.nsc.json").read_bytes(), b"untouched")
            with self.assertRaisesRegex(ValueError, "already exists"):
                restore_verified(payload, proof, sources, out, "b")
            forged = dict(proof, output_sha256="0" * 64)
            with self.assertRaises(ValueError):
                restore_verified(payload, forged, sources, out, "a")
            self.assertEqual((out / "00.nsc.json").read_bytes(), b"untouched")

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
