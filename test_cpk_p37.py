#!/usr/bin/env python3
"""Synthetic P37 tests for original CPK storage and @UTF Sorted restoration."""
from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from cpk_p37_compat import (
    _transform_utf, get_cpk_sorted, set_cpk_sorted, locate_sorted,
    read_stored_entry, staged_raw_storage, assert_original_stored_unchanged,
)


def mini_header(sorted_flag: int) -> bytes:
    """Build a minimal CRI @UTF CpkHeader with row-stored numeric columns."""
    strings = b"CpkHeader\x00Files\x00Sorted\x00Align\x00"
    descriptors = bytearray()
    for name, kind in (("Files", 4), ("Sorted", 2), ("Align", 2)):
        descriptors.append(0x50 | kind)
        descriptors.extend(struct.pack(">I", strings.index(name.encode() + b"\x00")))
    values = struct.pack(">IHH", 93, sorted_flag, 512)
    row_offset = 0x20 + len(descriptors)
    str_offset = row_offset + len(values)
    data_offset = str_offset + len(strings)
    total = data_offset
    prefix = (
        b"@UTF"
        + struct.pack(">I", total - 8)
        + struct.pack(">I", row_offset - 8)
        + struct.pack(">I", str_offset - 8)
        + struct.pack(">I", data_offset - 8)
        + struct.pack(">I", 0)
        + struct.pack(">H", 3)
        + struct.pack(">H", len(values))
        + struct.pack(">I", 1)
    )
    return prefix + descriptors + values + strings


def fake_cpk(path: Path, sorted_flag: int, obfuscated: bool = False):
    packet = bytearray(mini_header(sorted_flag))
    if obfuscated:
        _transform_utf(packet)
    path.write_bytes(b"CPK " + b"\xff\x00\x00\x00" +
                     len(packet).to_bytes(8, "little") + packet)


class P37Tests(unittest.TestCase):
    def test_parse_unsorted_header(self):
        offset, flag = locate_sorted(bytearray(mini_header(0)))
        self.assertEqual(flag, 0)
        self.assertEqual(mini_header(0)[offset:offset + 2], b"\x00\x00")

    def test_restore_sorted_zero_plain_header(self):
        with tempfile.TemporaryDirectory() as dir:
            path = Path(dir) / "carrier.cpk"
            fake_cpk(path, 1)
            old, current = set_cpk_sorted(path, 0)
            self.assertEqual((old, current), (1, 0))
            self.assertEqual(get_cpk_sorted(path), 0)

    def test_restore_sorted_zero_obfuscated_header(self):
        with tempfile.TemporaryDirectory() as dir:
            path = Path(dir) / "carrier.cpk"
            fake_cpk(path, 1, obfuscated=True)
            self.assertEqual(get_cpk_sorted(path), 1)
            self.assertEqual(set_cpk_sorted(path, 0), (1, 0))
            self.assertEqual(get_cpk_sorted(path), 0)

    def test_reject_bad_sorted_value(self):
        with self.assertRaisesRegex(ValueError, "boolean"):
            locate_sorted(bytearray(mini_header(2)))

    def test_reject_missing_utf_sorted(self):
        with self.assertRaises(ValueError):
            locate_sorted(bytearray(b"invalid"))

    def test_read_stored_exact_byte_slice(self):
        with tempfile.TemporaryDirectory() as dir:
            p=Path(dir)/"carrier.cpk"
            p.write_bytes(b"CPK " + b"AABBCCDDEEFF")
            self.assertEqual(read_stored_entry(p, {"offset":6,"packed_size":4}),b"BBCC")

    def test_stage_keeps_original_stored_nontarget_payload(self):
        with tempfile.TemporaryDirectory() as dir:
            folder=Path(dir)
            source=folder/"carrier.cpk"
            source.write_bytes(b"PREsecretPOST")
            root=folder/"stage"; (root/"data").mkdir(parents=True)
            (root/"data"/"a.xfbin").write_bytes(b"decoded")
            (root/"data"/"b.xfbin").write_bytes(b"keep this")
            rows={"data/a.xfbin":{"offset":3,"packed_size":6,"extracted_size":6},
                  "data/b.xfbin":{"offset":9,"packed_size":4,"extracted_size":4}}
            staged_raw_storage(source,rows,root,{"data/b.xfbin"})
            self.assertEqual((root/"data"/"a.xfbin").read_bytes(),b"secret")
            self.assertEqual((root/"data"/"b.xfbin").read_bytes(),b"keep this")

    def test_compressed_source_rejected(self):
        with tempfile.TemporaryDirectory() as dir:
            folder=Path(dir)
            source=folder/"carrier.cpk"
            source.write_bytes(b"ABCDEF")
            root=folder/"stage"; (root/"data").mkdir(parents=True)
            (root/"data"/"a.xfbin").write_bytes(b"decoded")
            rows={"data/a.xfbin":{"offset":0,"packed_size":6,"extracted_size":7}}
            with self.assertRaisesRegex(ValueError, "compressed entry"):
                staged_raw_storage(source,rows,root,set())

    def test_stored_payload_integrity_detects_mutation(self):
        with tempfile.TemporaryDirectory() as dir:
            folder=Path(dir)
            old=folder/"old.cpk";new=folder/"new.cpk"
            old.write_bytes(b"ABCD");new.write_bytes(b"ABXD")
            rows={"data/a.xfbin":{"offset":0,"packed_size":4,"extracted_size":4}}
            with self.assertRaisesRegex(ValueError, "stored payload changed"):
                assert_original_stored_unchanged(old,rows,new,rows,set())

    def test_stored_payload_integrity_passes_exact_bytes(self):
        with tempfile.TemporaryDirectory() as dir:
            folder=Path(dir)
            old=folder/"old.cpk";new=folder/"new.cpk"
            old.write_bytes(b"ABCD");new.write_bytes(b"ABCD")
            rows={"data/a.xfbin":{"offset":0,"packed_size":4,"extracted_size":4}}
            self.assertEqual(assert_original_stored_unchanged(old,rows,new,rows,set()),1)

    def test_changed_entry_excluded_from_raw_comparison(self):
        with tempfile.TemporaryDirectory() as dir:
            folder=Path(dir)
            old=folder/"old.cpk";new=folder/"new.cpk"
            old.write_bytes(b"ABCD");new.write_bytes(b"ABXD")
            rows={"data/a.xfbin":{"offset":0,"packed_size":4,"extracted_size":4}}
            self.assertEqual(
                assert_original_stored_unchanged(old,rows,new,rows,{"data/a.xfbin"}),0
            )


if __name__ == "__main__":
    unittest.main()
