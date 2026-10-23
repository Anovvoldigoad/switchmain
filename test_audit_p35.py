#!/usr/bin/env python3
"""P35 regressions: no real mod files or Switch hardware required."""
import tempfile
import unittest
from pathlib import Path

from audit_p35_carrier import compare, parse_utf


def make_utf():
    strings = b"Name\x00Number\x00hello\x00"
    # Two per-row fields: UTF string reference + uint32.
    columns = bytes([0x5A]) + (0).to_bytes(4, "big") + bytes([0x54]) + (5).to_bytes(4, "big")
    row_offset = 32 + len(columns)
    data = ((12).to_bytes(4, "big") + (7).to_bytes(4, "big"))
    str_offset = row_offset + len(data)
    data_offset = str_offset + len(strings)
    header = (b"@UTF" + (data_offset - 8).to_bytes(4, "big")
              + (row_offset - 8).to_bytes(4, "big")
              + (str_offset - 8).to_bytes(4, "big")
              + (data_offset - 8).to_bytes(4, "big")
              + b"\x00" * 4
              + (2).to_bytes(2, "big")
              + (8).to_bytes(2, "big")
              + (1).to_bytes(4, "big"))
    return header + columns + data + strings


class P35Tests(unittest.TestCase):
    def test_utf_parser(self):
        self.assertEqual(parse_utf(make_utf()), [{"Name": "hello", "Number": 7}])

    def case(self, source_bytes=b"A", carrier_bytes=b"B",
             path="data/spc/conditionprm.bin.xfbin", expected=None):
        with tempfile.TemporaryDirectory() as d:
            original, carrier = Path(d) / "stock", Path(d) / "carrier"
            original.write_bytes(source_bytes)
            carrier.write_bytes(carrier_bytes)
            base = {path: {"offset": 0, "size": len(source_bytes)}}
            override = {path: {"offset": 0, "size": len(carrier_bytes)}}
            return compare(original, carrier, base, override, expected)

    def test_changed_global_is_flagged(self):
        r = self.case()
        self.assertEqual(len(r["changed_overrides"]), 1)
        self.assertEqual(r["changed_overrides"][0]["kind"], "unverified_global")

    def test_identical_bytes_not_changed(self):
        r = self.case(b"ABC", b"ABC")
        self.assertEqual(len(r["changed_overrides"]), 0)
        self.assertEqual(len(r["overrides_relative_to_this_stock_cpk"]), 1)

    def test_v14_table_is_distinct_from_unverified_global(self):
        r = self.case(path="data/spc/appearanceAnm.xfbin")
        self.assertEqual(r["changed_overrides"][0]["kind"], "v14_table")

    def test_stock_collision_resource(self):
        r = self.case(path="data/bossNrt/08/b01cmneff1.xfbin")
        self.assertEqual(r["changed_overrides"][0]["kind"], "other_stock_collision")

    def test_missing_expected_resource_and_skl3_unproven(self):
        p = "data/spc/mtobbod1.xfbin"
        r = self.case(path=p, expected={p, "data/spc/mtobskl3.xfbin"})
        self.assertEqual(r["missing_known_resource_paths"], ["data/spc/mtobskl3.xfbin"])
        self.assertFalse(r["mtobskl3_present_in_carrier"])


if __name__ == "__main__":
    unittest.main()
