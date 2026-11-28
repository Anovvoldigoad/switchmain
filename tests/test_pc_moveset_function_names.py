"""Prove pinned PC Toolbox Moveset index correspondence; no Switch ABI claim."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from pc_moveset_functions import (CATALOG, lookup, compare, commands,
                                  lookup_command)


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


    def test_numeric_me_test_registry_is_separate_from_me_function_indices(self):
        source = commands()
        self.assertEqual(source["source_commit"],
                         "a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc")
        self.assertEqual(source["source_parent_commit"],
                         "1c3460573fa70b595e6bfa70e52f83f1c3f74f12")
        self.assertEqual(source["source_git_blob_sha1"],
                         "d7c5dbbebd60415f8d304321f083897658a86146")
        self.assertEqual(source["parent_source_git_blob_sha1"],
                         "e96af51210e96926a7bdaa70c44b6645f1a2b2b6")
        self.assertEqual([row["id"] for row in source["commands"]], [27, 28, 29])
        self.assertEqual([row["present_in_parent"] for row in source["commands"]],
                         [True, True, False])
        self.assertEqual(source["commands"][0]["dispatch_case"],
                         "MovesetPlus::SetProjectileDeflection(a1, true)")
        self.assertEqual(source["commands"][1]["dispatch_case"],
                         "MovesetPlus::SetProjectileDeflection(a1, false)")
        self.assertEqual(source["commands"][2]["dispatch_case"],
                         "MovesetPlus::TakeOverEnemyProjectiles(a1)")
        self.assertEqual(source["commands"][2]["release_feature"],
                         "Switch Projectiles Target")
        self.assertTrue(all(row["me_function_index"] is None
                            for row in source["commands"]))
        self.assertFalse(source["switch_engine_abi_verified"])
        self.assertFalse(source["native_switch_hook_added"])
        self.assertFalse(source["uzuy_tested"])

    def test_start_stop_deflect_commands_preexist_and_toggle_per_side(self):
        rows = commands()["commands"][:2]
        self.assertEqual([row["id"] for row in rows], [27, 28])
        for row, enabled, action in zip(rows, (True, False),
                                       ("START_DEFLECT", "STOP_DEFLECT")):
            self.assertTrue(row["present_in_parent"])
            self.assertEqual(row["action"], action)
            self.assertEqual(row["pc_implementation"]["valid_side_values"], [0, 1])
            self.assertEqual(
                row["pc_implementation"]["side_offset_rule"],
                'GameVersion == "1.70" ? 0xE60 : 0xC88')
            self.assertTrue(row["pc_implementation"]["state_update"].endswith(
                f"exchange({str(enabled).lower()})"))

    def test_command_29_records_pc_windows_freshness_and_lock_semantics(self):
        row = lookup_command(29)["command"]
        pc = row["pc_implementation"]
        self.assertEqual(pc["side_offset_rule"],
                         'GameVersion == "1.70" ? 0xE60 : 0xC88')
        self.assertEqual(pc["freshness_window_ms"], 250)
        self.assertEqual(pc["pending_takeover_expiry_ms"], 250)
        self.assertEqual(pc["clock"], "GetTickCount64")
        self.assertEqual(pc["mutex"], "g_deflectProjectileMutex")
        self.assertEqual(pc["source_collection"], "g_activeDeflectableProjectiles")
        self.assertFalse(pc["cached_projectile_pointer_dereferenced"])
        self.assertEqual(row["platform"], "Windows x64 PC")

    def test_command_lookup_boundaries_fail_closed(self):
        self.assertEqual(lookup_command(27)["command"]["action"], "START_DEFLECT")
        self.assertEqual(lookup_command(28)["command"]["action"], "STOP_DEFLECT")
        self.assertEqual(lookup_command(29)["command"]["action"], "SWITCH_PROJECTILES_TARGET")
        for value in (26, 30, -1, True, 1.5):
            with self.subTest(command_id=value), self.assertRaises(ValueError):
                lookup_command(value)

    def test_command_registry_cli_and_mode_exclusion(self):
        cmd = [sys.executable, str(ROOT / "tools" / "pc_moveset_functions.py")]
        result = subprocess.run(cmd + ["--commands"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([row["id"] for row in
                          json.loads(result.stdout)["commands"]], [27, 28, 29])
        result = subprocess.run(cmd + ["--command-id", "29"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["command"]["id"], 29)
        for bad in (["--commands", "--compare"],
                    ["--commands", "--index", "0"],
                    ["--command-id", "26"],
                    ["--command-id", "29", "--version", "nsc"]):
            with self.subTest(bad=bad):
                result = subprocess.run(cmd + bad, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
