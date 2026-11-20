"""Multi-mod editor index merge, not binary moveset conversion."""
import hashlib
import json
import sys
import unittest
import subprocess
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from merge_pc_moveset_nsc_manifests import merge, split, analyze_collisions, merge_resolved, verify_resolved, partition_resolved, build_partition_bundle, verify_partition_bundle
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

    def test_explicit_owner_semantic_selection_and_rejection(self):
        a = source("alpha", "nsc", [{"event_id": "shared", "function_index": 1},
                                     {"event_id": "unique", "function_index": 3}])
        b = source("beta", "nsc", [{"event_id": "shared", "function_index": 2}])
        payload, proof = merge_resolved([a, b], {"shared": "beta"})
        self.assertEqual([(r["event_id"], r["function_index"]) for r in
                          json.loads(payload)["events"]], [("shared", 2), ("unique", 3)])
        self.assertEqual(proof["output_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(proof["resolved_owners"], {"shared": "beta"})
        self.assertEqual(proof["event_owners"], [
            {"event_id": "shared", "source": "beta"},
            {"event_id": "unique", "source": "alpha"}])
        self.assertFalse(proof["native_switch_abi_verified"])
        for choices in ({}, {"shared": "gamma"}, {"unique": "alpha"},
                        {"shared": "beta", "unique": "alpha"}, []):
            with self.assertRaises(ValueError):
                merge_resolved([a, b], choices)
        with self.assertRaises(ValueError):
            merge_resolved([a, ("beta", b[1] + b" ", b[2])], {"shared": "beta"})
        with self.assertRaises(ValueError):
            merge_resolved([a, a], {"shared": "alpha"})

    def test_explicit_owner_cli_publication_and_rollback(self):
        a = source("alpha", "nsc", [{"event_id": "same", "function_index": 1}])
        b = source("beta", "nsc", [{"event_id": "same", "function_index": 2}])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pa, pb, policy = root / "a.json", root / "b.json", root / "owners.json"
            out, evidence = root / "merged.json", root / "proof.json"
            pa.write_bytes(a[1])
            pb.write_bytes(b[1])
            policy.write_text(json.dumps({"same": "beta"}))
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] /
                   "tools" / "merge_pc_moveset_nsc_manifests.py"),
                   "--source", "alpha", str(pa), a[2],
                   "--source", "beta", str(pb), b[2],
                   "--resolve", str(policy), "--output", str(out),
                   "--evidence", str(evidence)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(out.read_bytes())["events"][0]["function_index"], 2)
            self.assertEqual(json.loads(evidence.read_bytes())["output_sha256"],
                             hashlib.sha256(out.read_bytes()).hexdigest())
            out.unlink()
            evidence.unlink()
            policy.write_text(json.dumps({"same": "unknown"}))
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(out.exists())
            self.assertFalse(evidence.exists())

    def test_resolved_replay_verifier_and_cli_fail_closed(self):
        a = source("alpha", "nsc", [{"event_id": "same", "function_index": 1}])
        b = source("beta", "nsc", [{"event_id": "same", "function_index": 2}])
        payload, proof = merge_resolved([a, b], {"same": "beta"})
        self.assertTrue(verify_resolved(payload, proof, [a, b]))
        for bad_payload, bad_proof, bad_sources in (
            (payload + b" ", proof, [a, b]),
            (payload, dict(proof, output_sha256="0" * 64), [a, b]),
            (payload, dict(proof, sources=[]), [a, b]),
            (payload, dict(proof, event_owners=[]), [a, b]),
            (payload, dict(proof, event_owners=[{"event_id": "same", "source": "alpha"}]), [a, b]),
            (payload, proof, [a, ("beta", b[1] + b" ", b[2])]),
            (payload, dict(proof, resolved_owners={"same": "alpha"}), [a, b]),
        ):
            with self.assertRaises(ValueError):
                verify_resolved(bad_payload, bad_proof, bad_sources)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pa, pb = root / "a.json", root / "b.json"
            out, evidence = root / "out.json", root / "proof.json"
            pa.write_bytes(a[1])
            pb.write_bytes(b[1])
            out.write_bytes(payload)
            evidence.write_text(json.dumps(proof))
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] /
                   "tools" / "merge_pc_moveset_nsc_manifests.py"),
                   "--verify-resolved", "--source", "alpha", str(pa), a[2],
                   "--source", "beta", str(pb), b[2],
                   "--output", str(out), "--evidence", str(evidence)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(out.read_bytes(), payload)
            out.write_bytes(payload + b" ")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(out.read_bytes(), payload + b" ")

    def test_partition_resolved_owner_selection_and_tamper(self):
        a = source("alpha", "nsc", [{"event_id": "shared", "function_index": 1},
                                     {"event_id": "a", "function_index": 3}])
        b = source("beta", "nsc", [{"event_id": "shared", "function_index": 2},
                                    {"event_id": "b", "function_index": 4}])
        payload, proof = merge_resolved([a, b], {"shared": "beta"})
        parts = partition_resolved(payload, proof, [a, b])
        self.assertEqual([name for name, _, _ in parts], ["alpha", "beta"])
        self.assertEqual([[r["event_id"] for r in json.loads(raw)["events"]]
                          for _, raw, _ in parts], [["a"], ["shared", "b"]])
        for _, raw, digest in parts:
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        with self.assertRaises(ValueError):
            partition_resolved(payload + b" ", proof, [a, b])
        with self.assertRaises(ValueError):
            partition_resolved(payload, dict(proof, event_owners=[]), [a, b])
        with self.assertRaises(ValueError):
            partition_resolved(payload, proof, [a, ("beta", b[1] + b" ", b[2])])

    def test_partition_cli_verified_bundle_and_rejections(self):
        a = source("alpha", "nsc", [{"event_id": "shared", "function_index": 1},
                                     {"event_id": "a", "function_index": 3}])
        b = source("beta", "nsc", [{"event_id": "shared", "function_index": 2}])
        payload, proof = merge_resolved([a, b], {"shared": "beta"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pa, pb = root / "a.json", root / "b.json"
            out, evidence, bundle = root / "merged.json", root / "proof.json", root / "parts.json"
            pa.write_bytes(a[1])
            pb.write_bytes(b[1])
            out.write_bytes(payload)
            evidence.write_text(json.dumps(proof))
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] /
                   "tools" / "merge_pc_moveset_nsc_manifests.py"),
                   "--verify-resolved", "--partition-output", str(bundle),
                   "--source", "alpha", str(pa), a[2],
                   "--source", "beta", str(pb), b[2],
                   "--output", str(out), "--evidence", str(evidence)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            doc = json.loads(bundle.read_bytes())
            self.assertEqual(doc["merged_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual([p["source"] for p in doc["partitions"]], ["alpha", "beta"])
            self.assertEqual([[r["event_id"] for r in p["manifest"]["events"]]
                              for p in doc["partitions"]], [["a"], ["shared"]])
            for part in doc["partitions"]:
                raw = (json.dumps(part["manifest"], ensure_ascii=False, indent=2) + "\n").encode()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), part["sha256"])
            original = bundle.read_bytes()
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(bundle.read_bytes(), original)
            bundle.unlink()
            out.write_bytes(payload + b" ")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(bundle.exists())
            out.write_bytes(payload)
            pb.write_bytes(b[1] + b" ")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertFalse(bundle.exists())

    def test_partition_bundle_replay_positive_negative_and_cli_read_only(self):
        a = source("alpha", "nsc", [{"event_id": "same", "function_index": 1},
                                     {"event_id": "only_a", "function_index": 3}])
        b = source("beta", "nsc", [{"event_id": "same", "function_index": 2}])
        sources = [a, b]
        payload, proof = merge_resolved(sources, {"same": "beta"})
        bundle = build_partition_bundle(payload, proof, sources)
        self.assertTrue(verify_partition_bundle(bundle, payload, proof, sources))
        for altered in (bundle + b" ", bundle.replace(b'"source": "alpha"', b'"source": "beta"', 1),
                        bundle.replace(b'"sha256": "', b'"sha256": "0', 1)):
            with self.assertRaises(ValueError):
                verify_partition_bundle(altered, payload, proof, sources)
        with self.assertRaises(ValueError):
            verify_partition_bundle(bundle, payload, proof, [a, ("beta", b[1] + b" ", b[2])])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pa, pb = root / "a.json", root / "b.json"
            merged, evidence, partition = root / "merged.json", root / "proof.json", root / "partition.json"
            pa.write_bytes(a[1])
            pb.write_bytes(b[1])
            merged.write_bytes(payload)
            evidence.write_text(json.dumps(proof))
            partition.write_bytes(bundle)
            cmd = [sys.executable, str(Path(__file__).resolve().parents[1] /
                   "tools" / "merge_pc_moveset_nsc_manifests.py"),
                   "--verify-resolved", "--verify-partition-bundle", str(partition),
                   "--source", "alpha", str(pa), a[2],
                   "--source", "beta", str(pb), b[2],
                   "--output", str(merged), "--evidence", str(evidence)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(partition.read_bytes(), bundle)
            partition.write_bytes(bundle + b" ")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(partition.read_bytes(), bundle + b" ")
            partition.write_bytes(bundle)
            pa.write_bytes(a[1] + b" ")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(partition.read_bytes(), bundle)

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
