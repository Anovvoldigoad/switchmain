"""Prove pinned PC Toolbox Moveset index correspondence; no Switch ABI claim."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from pc_moveset_functions import CATALOG, lookup, compare


class SourcePinnedMovesetNames(unittest.TestCase):
    def test_full_source_index_catalog_and_prefix(self):
        source = json.loads(CATALOG.read_text())
        self.assertEqual(source["source_git_blob_sha"],
                         "9d5f3e0dfa4ed51cf7924b503081a87b12146f64")
        self.assertEqual(len(source["ns4"]), 289)
        self.assertEqual(len(source["nsc"]), 300)
        self.assertEqual(source["nsc"][:289], source["ns4"])
        self.assertEqual(len(set(source["nsc"])), 300)
        self.assertFalse(source["engine_function_ids_verified"])

    def test_new_nsc_only_names_and_release_gap(self):
        report = compare()
        self.assertEqual(report["shared_same_index"], 289)
        self.assertEqual([r["index"] for r in report["nsc_only"]], list(range(289, 300)))
        self.assertEqual(report["nsc_only"][0]["name"], "ME_REMINISCENEBATTLE_CUTIN_FRAME")
        self.assertEqual(report["nsc_only"][-1]["name"], "ME_NOT_NOMALCOMBO_CAMERA_DIST_RESET")
        self.assertFalse(report["switch_projectiles_target_index_proven"])
        self.assertFalse(report["start_stop_deflect_index_proven"])

    def test_lookup_exact_indices_and_reject_unknown(self):
        self.assertEqual(lookup("nsc", 0)["name"], "ME_SPSKILL_END_MOVE")
        self.assertEqual(lookup("nsc", 160)["name"], "ME_ENTRY_PROJECTILE")
        self.assertEqual(lookup("nsc", 299)["name"], "ME_NOT_NOMALCOMBO_CAMERA_DIST_RESET")
        self.assertEqual(lookup("ns4", 288)["name"], lookup("nsc", 288)["name"])
        for version, index in [("nsc", 300), ("ns4", 289), ("nsc", -1),
                               ("invalid", 0), ("nsc", 1.5), ("nsc", True)]:
            with self.subTest(version=version, index=index), self.assertRaises(ValueError):
                lookup(version, index)

    def test_cli_compare_lookup_and_invalid(self):
        cmd = [sys.executable, str(ROOT / "tools" / "pc_moveset_functions.py")]
        result = subprocess.run(cmd + ["--compare"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(json.loads(result.stdout)["nsc_only"]), 11)
        result = subprocess.run(cmd + ["--version", "nsc", "--index", "299"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["index"], 299)
        for bad in (["--version", "nsc", "--index", "300"],
                    ["--compare", "--index", "0"], ["--version", "nsc"]):
            with self.subTest(bad=bad):
                result = subprocess.run(cmd + bad, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
