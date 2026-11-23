"""Ordered mixed-source factory precedence regression (offline only)."""
import hashlib
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from portlib.factory_profile import encode, decode
from compose_ordered_factory import compose


def raw(name, owner):
    return name.encode().ljust(24, b"\0") + struct.pack("<H", owner) + bytes(6)


def src(kind, label, data):
    return (kind, label, data, hashlib.sha256(data).hexdigest())


class OrderedFactoryTests(unittest.TestCase):
    def test_interleaved_precedence_and_provenance(self):
        a = src("raw", "first", raw("2dnz", 280))
        b = src("profile", "middle", encode({280: 1}))
        c = src("raw", "last", raw("2dnz", 280))
        result, ledger, sources = compose([a, b, c])
        self.assertEqual(decode(result), {280: 58})
        self.assertEqual([row["selector"] for row in ledger], [58, 1, 58])
        self.assertEqual([row["replaced"] for row in ledger], [False, True, True])
        self.assertEqual([row["label"] for row in sources], ["first", "middle", "last"])
        self.assertEqual(decode(compose([c, b, a])[0]), {280: 58})

    def test_reject_collision_and_same_source_duplicate(self):
        a = src("raw", "a", raw("2dnz", 280))
        b = src("profile", "b", encode({280: 1}))
        with self.assertRaisesRegex(ValueError, "collid"):
            compose([a, b], conflicts="reject")
        with self.assertRaisesRegex(ValueError, "collid"):
            compose([src("raw", "dupe", raw("2dnz", 280) * 2)], conflicts="reject")

    def test_hash_kind_label_and_boundary(self):
        a = src("profile", "a", encode({}))
        self.assertEqual(decode(compose([a])[0]), {})
        with self.assertRaisesRegex(ValueError, "SHA256"):
            compose([(*a[:3], "0" * 64)])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            compose([a, a])
        with self.assertRaisesRegex(ValueError, "kind"):
            compose([("other", "x", b"", hashlib.sha256(b"").hexdigest())])


    def test_remove_middle_and_last_replays_precedence(self):
        a = src("raw", "first", raw("2dnz", 280))
        b = src("profile", "middle", encode({280: 1, 281: 1}))
        c = src("raw", "last", raw("2dnz", 280))
        result, ledger, proof = compose([a, b, c], exclude=["middle", "last"])
        self.assertEqual(decode(result), {280: 58})
        self.assertEqual([r["source"] for r in ledger], ["first"])
        self.assertEqual([r["excluded"] for r in proof], [False, True, True])
        self.assertEqual(decode(compose([a, b, c], exclude=["last"])[0]),
                         {280: 1, 281: 1})
        self.assertEqual(decode(compose([a, b, c], exclude=["first", "last"])[0]),
                         {280: 1, 281: 1})
        self.assertEqual(decode(compose([a, b, c], exclude=["first", "middle", "last"])[0]), {})

    def test_removed_sources_still_authenticated_and_unknown_rejected(self):
        a = src("raw", "first", raw("2dnz", 280))
        with self.assertRaisesRegex(ValueError, "SHA256"):
            compose([(*a[:3], "0" * 64)], exclude=["first"])
        with self.assertRaisesRegex(ValueError, "Unknown excluded"):
            compose([a], exclude=["missing"])
        with self.assertRaisesRegex(ValueError, "Duplicate excluded"):
            compose([a], exclude=["first", "first"])
        with self.assertRaisesRegex(ValueError, "Duplicate source"):
            compose([a, a], exclude=["first"])
        with self.assertRaisesRegex(ValueError, "Unknown source kind"):
            compose([src("invalid", "first", b"")], exclude=["first"])
        # Exclusion must not turn an unknown input format into a valid source.
        with self.assertRaisesRegex(ValueError, "Unknown source kind"):
            compose([src("invalid", "first", b"")], exclude=["first",])

    def test_cli_remove_source_and_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            import json
            d = Path(tmp)
            a, b = d / "first.bin", d / "second.bin"
            a.write_bytes(raw("2dnz", 280))
            b.write_bytes(encode({280: 1}))
            base = [sys.executable, str(ROOT / "tools/compose_ordered_factory.py"),
                    "--source", "raw", "first", str(a), hashlib.sha256(a.read_bytes()).hexdigest(),
                    "--source", "profile", "second", str(b), hashlib.sha256(b.read_bytes()).hexdigest()]
            run = subprocess.run(base + ["--exclude", "second", "--output", str(d / "out")],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(decode((d / "out/factory.profile").read_bytes()), {280: 58})
            proof = json.loads((d / "out/factory_ordered_report.json").read_text())
            self.assertEqual(proof["excluded_labels"], ["second"])
            self.assertTrue(proof["sources"][1]["excluded"])
            self.assertEqual(proof["effective_owners"],
                             [{"owner": 280, "source": "first", "kind": "raw", "selector": 58}])
            bad = subprocess.run(base + ["--exclude", "unknown", "--output", str(d / "bad")],
                                 capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse((d / "bad").exists())

    def test_cli_fail_closed_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            a = d / "raw"
            a.write_bytes(raw("2dnz", 280))
            sha = hashlib.sha256(a.read_bytes()).hexdigest()
            base = [sys.executable, str(ROOT / "tools/compose_ordered_factory.py"),
                    "--source", "raw", "one", str(a), sha]
            ok = subprocess.run(base + ["--output", str(d / "ok")], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(decode((d / "ok/factory.profile").read_bytes()), {280: 58})
            bad = subprocess.run(base[:-1] + ["0" * 64, "--output", str(d / "bad")],
                                 capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse((d / "bad").exists())

    def test_atomic_publication_and_rollback(self):
        from unittest.mock import patch
        from compose_ordered_factory import main
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            source = d / "input.profile"
            source.write_bytes(encode({280: 1}))
            output = d / "out"
            args = ["compose_ordered_factory.py", "--source", "profile", "mod",
                    str(source), hashlib.sha256(source.read_bytes()).hexdigest(),
                    "--output", str(output)]
            with patch.object(sys, "argv", args):
                original_write = Path.write_text
                def fail_report(path, *a, **kw):
                    if path.name == "factory_ordered_report.json":
                        raise OSError("simulated report write failure")
                    return original_write(path, *a, **kw)
                with patch.object(Path, "write_text", fail_report):
                    with self.assertRaisesRegex(OSError, "simulated"):
                        main()
            self.assertFalse(output.exists())
            self.assertEqual(sorted(p.name for p in d.iterdir()), ["input.profile"])
            with patch.object(sys, "argv", args):
                main()
            original = (output / "factory.profile").read_bytes()
            with patch.object(sys, "argv", args):
                with self.assertRaises(OSError):
                    main()
            self.assertEqual((output / "factory.profile").read_bytes(), original)
            self.assertEqual(sorted(p.name for p in d.iterdir()), ["input.profile", "out"])

    def test_racing_destination_preserved(self):
        from unittest.mock import patch
        from compose_ordered_factory import main
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            source = d / "input.profile"
            source.write_bytes(encode({280: 1}))
            output = d / "out"
            args = ["compose_ordered_factory.py", "--source", "profile", "mod",
                    str(source), hashlib.sha256(source.read_bytes()).hexdigest(),
                    "--output", str(output)]
            original = Path.write_text
            def create_racing_output(path, *args, **kwargs):
                result = original(path, *args, **kwargs)
                if path.name == "factory_ordered_report.json":
                    output.mkdir()
                    (output / "sentinel").write_bytes(b"keep")
                return result
            with patch.object(sys, "argv", args), patch.object(Path, "write_text", create_racing_output):
                with self.assertRaises(FileExistsError):
                    main()
            self.assertEqual((output / "sentinel").read_bytes(), b"keep")
            self.assertEqual(sorted(p.name for p in d.iterdir()), ["input.profile", "out"])

    def test_baseline_semantic_delta_and_replay(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            baseline = d / "baseline.profile"
            baseline.write_bytes(encode({280: 1, 281: 1}))
            proposed = d / "proposed.profile"
            proposed.write_bytes(encode({280: 58, 282: 1}))
            sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            cmd = [sys.executable, str(ROOT / "tools/compose_ordered_factory.py"),
                   "--source", "profile", "proposed", str(proposed), sha(proposed),
                   "--baseline-profile", str(baseline), sha(baseline),
                   "--output", str(d / "out")]
            run = lambda *extra: subprocess.run(cmd + list(extra), capture_output=True, text=True)
            created = run()
            self.assertEqual(created.returncode, 0, created.stderr)
            report = json.loads((d / "out/factory_ordered_report.json").read_text())
            self.assertEqual(report["changes"], [
                {"owner": 280, "before": 1, "after": 58, "operation": "replace"},
                {"owner": 281, "before": 1, "after": None, "operation": "remove"},
                {"owner": 282, "before": None, "after": 1, "operation": "add"}])
            self.assertEqual(report["baseline_sha256"], sha(baseline))
            self.assertEqual(run("--verify-output").returncode, 0)
            baseline.write_bytes(encode({280: 1}))
            self.assertNotEqual(run("--verify-output").returncode, 0)
            self.assertEqual(decode((d / "out/factory.profile").read_bytes()),
                             {280: 58, 282: 1})

    def test_baseline_changed_selector_preserves_source_attribution(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            first, second = d / "first.profile", d / "second.profile"
            first.write_bytes(encode({280: 1, 281: 1}))
            second.write_bytes(encode({280: 58, 282: 1}))
            sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            script = str(ROOT / "tools/compose_ordered_factory.py")
            old = subprocess.run([sys.executable, script, "--source", "profile",
                                  "old-mod", str(first), sha(first), "--output", str(d / "old")],
                                 capture_output=True, text=True)
            self.assertEqual(old.returncode, 0, old.stderr)
            baseline = d / "old/factory.profile"
            report = d / "old/factory_ordered_report.json"
            cmd = [sys.executable, script, "--source", "profile", "new-mod",
                   str(second), sha(second), "--baseline-profile", str(baseline),
                   sha(baseline), "--baseline-report", str(report), sha(report),
                   "--output", str(d / "new")]
            run = lambda *args: subprocess.run(cmd + list(args), capture_output=True, text=True)
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            changes = json.loads((d / "new/factory_ordered_report.json").read_text())["changes"]
            self.assertEqual(changes, [
                {"owner": 280, "before": 1, "after": 58, "operation": "replace",
                 "before_source": "old-mod", "after_source": "new-mod"},
                {"owner": 281, "before": 1, "after": None, "operation": "remove",
                 "before_source": "old-mod", "after_source": None},
                {"owner": 282, "before": None, "after": 1, "operation": "add",
                 "before_source": None, "after_source": "new-mod"}])
            self.assertEqual(run("--verify-output").returncode, 0)
            self.assertEqual(decode((d / "new/factory.profile").read_bytes()),
                             {280: 58, 282: 1})

    def test_baseline_same_selector_owner_transfer_and_tamper(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            a, b = d / "a.profile", d / "b.profile"
            a.write_bytes(encode({280: 1}))
            b.write_bytes(encode({280: 1}))
            sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            script = str(ROOT / "tools/compose_ordered_factory.py")
            old = subprocess.run([sys.executable, script, "--source", "profile", "first",
                                  str(a), sha(a), "--output", str(d / "old")],
                                 capture_output=True, text=True)
            self.assertEqual(old.returncode, 0, old.stderr)
            profile = d / "old/factory.profile"
            report = d / "old/factory_ordered_report.json"
            cmd = [sys.executable, script, "--source", "profile", "second",
                   str(b), sha(b), "--baseline-profile", str(profile), sha(profile),
                   "--baseline-report", str(report), sha(report), "--output", str(d / "new")]
            run = lambda *extra: subprocess.run(cmd + list(extra), capture_output=True, text=True)
            created = run()
            self.assertEqual(created.returncode, 0, created.stderr)
            proof = json.loads((d / "new/factory_ordered_report.json").read_text())
            self.assertEqual(proof["changes"], [{"owner": 280, "before": 1, "after": 1,
                "operation": "transfer", "before_source": "first", "after_source": "second"}])
            self.assertEqual(run("--verify-output").returncode, 0)
            self.assertEqual((d / "new/factory.profile").read_bytes(), profile.read_bytes())
            old_report = json.loads(report.read_text())
            old_report["effective_owners"][0]["source"] = "forged"
            report.write_text(json.dumps(old_report))
            self.assertNotEqual(run("--verify-output").returncode, 0)
            self.assertEqual((d / "new/factory.profile").read_bytes(), profile.read_bytes())
            missing = subprocess.run([sys.executable, script, "--source", "profile", "second",
                                      str(b), sha(b), "--baseline-report", str(report), sha(report),
                                      "--output", str(d / "invalid")], capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse((d / "invalid").exists())

    def test_cli_verify_replay_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            import json
            d = Path(tmp)
            a = d / "a.bin"
            b = d / "b.profile"
            a.write_bytes(raw("2dnz", 280))
            b.write_bytes(encode({280: 1}))
            cmd = [sys.executable, str(ROOT / "tools/compose_ordered_factory.py"),
                   "--source", "raw", "a", str(a), hashlib.sha256(a.read_bytes()).hexdigest(),
                   "--source", "profile", "b", str(b), hashlib.sha256(b.read_bytes()).hexdigest(),
                   "--exclude", "b", "--output", str(d / "out")]
            def run(*extra):
                return subprocess.run(cmd + list(extra), capture_output=True, text=True)
            self.assertEqual(run().returncode, 0)
            initial_report = json.loads((d / "out/factory_ordered_report.json").read_text())
            self.assertEqual(initial_report["effective_owners"],
                             [{"owner": 280, "source": "a", "kind": "raw", "selector": 58}])
            self.assertEqual(run("--verify-output").returncode, 0)
            profile = d / "out/factory.profile"
            original = profile.read_bytes()
            profile.write_bytes(original + b"x")
            self.assertNotEqual(run("--verify-output").returncode, 0)
            profile.write_bytes(original)
            report_path = d / "out/factory_ordered_report.json"
            report = json.loads(report_path.read_text())
            report["sources"][1]["excluded"] = False
            report_path.write_text(json.dumps(report))
            self.assertNotEqual(run("--verify-output").returncode, 0)
            report["sources"][1]["excluded"] = True
            report_path.write_text(json.dumps(report))
            self.assertEqual(run("--verify-output").returncode, 0)
            (d / "out/extra").write_text("unexpected")
            self.assertNotEqual(run("--verify-output").returncode, 0)
            (d / "out/extra").unlink()
            b.write_bytes(b.read_bytes() + b"x")
            self.assertNotEqual(run("--verify-output").returncode, 0)


if __name__ == "__main__":
    unittest.main()
