#!/usr/bin/env python3
"""Synthetic offline regressions for P36. No user game resources are bundled."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_p36_stock_battle_globals import (
    BATTLE_GLOBALS, EXPECTED_CARRIER_COUNT, EXPECTED_STOCK_COUNT,
    inside, preflight, select_stock_global_replacements, validate_repack,
)


class P36Tests(unittest.TestCase):
    def make_hashes(self):
        original = {f"data/spc/other{index}.xfbin": f"orig{index}" for index in range(90)}
        original.update({name: "mod" + str(i) for i, name in enumerate(BATTLE_GLOBALS)})
        stock = {name: "stock" + str(i) for i, name in enumerate(BATTLE_GLOBALS)}
        return original, stock

    def test_three_globals_are_replaced_and_other_90_untouched(self):
        original, stock = self.make_hashes()
        built = original | stock
        ids = {name: index for index, name in enumerate(original)}
        result = validate_repack(ids, ids.copy(), original, built, stock)
        self.assertEqual(set(result["modified_entries"]), set(BATTLE_GLOBALS))
        self.assertEqual(result["unchanged_entries"], 90)
        self.assertTrue(result["all_paths_ids_and_decoded_contents_checked"])

    def test_unrelated_file_mutation_fails(self):
        original, stock = self.make_hashes()
        built = original | stock
        built["data/spc/other0.xfbin"] = "unexpected"
        ids = {name: index for index, name in enumerate(original)}
        with self.assertRaisesRegex(ValueError, "Unrelated decoded payload"):
            validate_repack(ids, ids, original, built, stock)

    def test_unchanged_bad_global_fails(self):
        original, stock = self.make_hashes()
        built = original | stock
        built[BATTLE_GLOBALS[0]] = original[BATTLE_GLOBALS[0]]
        ids = {name: index for index, name in enumerate(original)}
        with self.assertRaisesRegex(ValueError, "battle global"):
            validate_repack(ids, ids, original, built, stock)

    def test_template_file_id_mutation_fails(self):
        original, stock = self.make_hashes()
        ids = {name: index for index, name in enumerate(original)}
        changed = dict(ids)
        changed[BATTLE_GLOBALS[0]] = 400
        with self.assertRaisesRegex(ValueError, "path order or numeric IDs"):
            validate_repack(ids, changed, original, original | stock, stock)

    def test_template_file_order_mutation_fails(self):
        original, stock = self.make_hashes()
        ids = {name: index for index, name in enumerate(original)}
        reordered = dict(reversed(list(ids.items())))
        with self.assertRaisesRegex(ValueError, "path order or numeric IDs"):
            validate_repack(ids, reordered, original, original | stock, stock)

    def test_template_missing_file_fails(self):
        original, stock = self.make_hashes()
        ids = {name: index for index, name in enumerate(original)}
        modified = original | stock
        modified.pop("data/spc/other0.xfbin")
        with self.assertRaisesRegex(ValueError, "Decoded carrier file set"):
            validate_repack(ids, ids, original, modified, stock)

    def test_no_op_restore_is_rejected(self):
        original, stock = self.make_hashes()
        with self.assertRaisesRegex(ValueError, "no P36 candidate"):
            select_stock_global_replacements(original | stock, stock)

    def test_partial_restore_is_explicit(self):
        original, stock = self.make_hashes()
        original[BATTLE_GLOBALS[1]] = stock[BATTLE_GLOBALS[1]]
        selected = select_stock_global_replacements(original, stock)
        self.assertEqual(selected, [BATTLE_GLOBALS[0], BATTLE_GLOBALS[2]])

    def test_missing_reference_hash_fails(self):
        original, stock = self.make_hashes()
        stock.pop(BATTLE_GLOBALS[0])
        with self.assertRaisesRegex(ValueError, "missing"):
            select_stock_global_replacements(original, stock)

    def test_inside_directory_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.assertTrue(inside(root / "a" / "b", root))
            self.assertFalse(inside(root.parent / "another", root))

    def test_preflight_rejects_unpinned_stock_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = root / "stock.cpk", root / "carrier.cpk"
            a.write_bytes(b"CPK STOCK")
            b.write_bytes(b"CPK MOD")
            exe = root / "fastcpk"
            exe.write_text("#!/bin/sh\nexit 0\n")
            exe.chmod(0o755)
            with self.assertRaisesRegex(ValueError, "SHA256"):
                preflight(a, b, root / "newfolder", exe, exe, False)

    def test_preflight_expected_counts_guard(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b = root / "stock.cpk", root / "carrier.cpk"
            a.write_bytes(b"CPK STOCK")
            b.write_bytes(b"CPK MOD")
            exe = root / "fastcpk"
            exe.write_text("#!/bin/sh\nexit 0\n")
            exe.chmod(0o755)
            with patch("build_p36_stock_battle_globals.list_archive", side_effect=[
                {name: {"id":i} for i,name in enumerate(BATTLE_GLOBALS)},
                {name: {"id":i} for i,name in enumerate(BATTLE_GLOBALS)},
            ]):
                with self.assertRaisesRegex(ValueError, "Unexpected CPK entry counts"):
                    preflight(a, b, root / "newfolder", exe, exe, True)

    def test_expected_counts_are_pinned(self):
        self.assertEqual((EXPECTED_STOCK_COUNT, EXPECTED_CARRIER_COUNT), (728, 93))


if __name__ == "__main__":
    unittest.main()
