#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from audit_p35_carrier import (
    parse_listing, compare, classify_path, read_inventory, sha_entry,
)

def listing(*entries):
    header = (f"Files: {len(entries)} ContentOffset: 0x800 "
              "Align: 0x200 TOC: 0x200 ITOC: 0x0")
    rows = [f"{index} 0x{offset:x} {length} {length} {path}"
            for index,(offset,length,path) in enumerate(entries)]
    return "\n".join([header]+rows)

class P35Tests(unittest.TestCase):
    def test_parse_fastcpk_absolute_offsets(self):
        parsed=parse_listing(listing((0,4,"data/spc/mtobbod1.xfbin")),4)
        self.assertEqual(parsed["data/spc/mtobbod1.xfbin"]["offset"],0)

    def test_count_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"count mismatch"):
            parse_listing("Files: 2 ContentOffset: 0x0 Align: 0x200 TOC: 1 ITOC: 0\n"
                          "0 0x0 1 1 data/a.xfbin",3)

    def test_out_of_range_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"out of file range"):
            parse_listing(listing((2,8,"data/a.xfbin")),9)

    def test_duplicate_id_fails_closed(self):
        txt=listing((0,1,"data/a.xfbin"),(1,1,"data/b.xfbin")).replace(
            "1 0x1 1 1","0 0x1 1 1")
        with self.assertRaisesRegex(ValueError,"duplicate"):
            parse_listing(txt,2)

    def test_duplicate_path_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            parse_listing(listing((0,1,"data/a.xfbin"),(1,1,"data/a.xfbin")),2)

    def test_missing_parser_header_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"header"):
            parse_listing("garbage",8)

    def setup_stock(self, stock_bytes=b"ABC", carrier_bytes=b"XYZ",
                    path="data/spc/conditionprm.bin.xfbin"):
        folder=tempfile.TemporaryDirectory()
        root=Path(folder.name)
        stock=root/"stock.cpk"
        carrier=root/"Tobi_Switch.cpk"
        stock.write_bytes(stock_bytes)
        carrier.write_bytes(carrier_bytes)
        stock_records=parse_listing(listing((0,len(stock_bytes),path)),len(stock_bytes))
        carrier_records=parse_listing(listing((0,len(carrier_bytes),path)),len(carrier_bytes))
        result=compare(carrier,carrier_records,[(stock,stock_records)])
        return folder,result,stock,carrier,stock_records,carrier_records

    def test_changed_global_is_highlighted(self):
        folder,r,*_=self.setup_stock()
        with folder:
            self.assertEqual(len(r["different_packed_payloads"]),1)
            self.assertEqual(r["stock_path_collisions"][0]["category"],"unverified_global")
            self.assertTrue(r["stock_path_collisions"][0]["stock_sources"][0]["different_packed_bytes"])

    def test_identical_bytes_not_changed(self):
        folder,r,*_=self.setup_stock(b"ABC",b"ABC")
        with folder:
            self.assertEqual(r["different_packed_payloads"],[])
            self.assertEqual(len(r["stock_path_collisions"]),1)

    def test_v14_table_classification(self):
        self.assertEqual(classify_path("data/spc/appearanceAnm.xfbin"),"v14_parameter_table")

    def test_cross_archive_collision(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            a,b,c=[root/n for n in ("launch.cpk","patch.cpk","mod.cpk")]
            a.write_bytes(b"ABC");b.write_bytes(b"XYZ");c.write_bytes(b"ABC")
            key="data/spc/mtob.xfbin"
            stock=[(a,parse_listing(listing((0,3,key)),3)),
                   (b,parse_listing(listing((0,3,key)),3))]
            carrier=parse_listing(listing((0,3,key)),3)
            report=compare(c,carrier,stock)
            sources=report["stock_path_collisions"][0]["stock_sources"]
            self.assertEqual(len(sources),2)
            self.assertEqual([x["different_packed_bytes"] for x in sources],[False,True])

    def test_case_variants_not_silently_identical(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            a=root/"a.cpk"; b=root/"b.cpk"
            a.write_bytes(b"X");b.write_bytes(b"Y")
            stocks=parse_listing(listing((0,1,"Data/Spc/MTob.xfbin")),1)
            carrier=parse_listing(listing((0,1,"data/spc/mtob.xfbin")),1)
            report=compare(b,carrier,[(a,stocks)])
            self.assertEqual(len(report["case_variant_paths"]),1)
            self.assertEqual(report["stock_path_collisions"],[])

    def test_partial_v4_inventory_not_mislabeled_complete(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"V4.json"
            f.write_text(json.dumps({"resource_count":72,
                "resource_collisions_across_all_cpks":[{"path":"data/a.xfbin"}],
                "ui_assets":[{"path":"data/b.xfbin"}]}))
            known,coverage=read_inventory(f)
            self.assertEqual(coverage,"partial_v4_inventory")
            self.assertEqual(known,{"data/a.xfbin","data/b.xfbin"})

    def test_complete_inventory_if_explicitly_present(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"inventory.json"
            f.write_text(json.dumps({"all_72_resources":[{"path":"data/a.xfbin"}]}))
            known,coverage=read_inventory(f)
            self.assertEqual((known,coverage),({"data/a.xfbin"},"complete_resource_list"))

    def test_absent_resource_not_automatically_failure(self):
        folder,r,*_=self.setup_stock()
        with folder:
            self.assertFalse(r["mtobskl3_present_in_carrier"])
            self.assertTrue(any("does not prove" in msg for msg in r["warnings"]))

    def test_hash_exact_stored_entry(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"archive.cpk";p.write_bytes(b"PADABCEND")
            self.assertEqual(sha_entry(p,{"offset":3,"packed_size":3}),
                             __import__("hashlib").sha256(b"ABC").hexdigest())


    def test_zero_length_file_is_a_valid_toc_entry(self):
        rows=parse_listing(listing((0,0,"data/empty.bin")),0)
        self.assertEqual(rows["data/empty.bin"]["packed_size"],0)

    def test_explicit_inventory_count_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"bad_inventory.json"
            f.write_text(json.dumps({"resource_count":72,
                "all_72_resources":[{"path":"data/only-one.xfbin"}]}))
            with self.assertRaisesRegex(ValueError,"inconsistent count"):
                read_inventory(f)

if __name__=="__main__":
    unittest.main()
