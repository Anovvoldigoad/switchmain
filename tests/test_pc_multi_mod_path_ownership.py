"""Fail-closed multi-mod PC source-path ownership; no game ABI claim."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from portlib.pc_nsc_param_pack import _input_spec, FAMILIES
from portlib.native_cpk_graph import MAIN_SHA256

def mod(mid, family, path):
    return {"mod_id":mid,"staged_path":"unused","original_archive":"unused",
            "source_sha256":"0"*64,"resources":[{"family":family,"source_path":path}]}

def spec(mods):
    return {"original_main":{"path":"unused","sha256":MAIN_SHA256},"mods":mods}

class MultiModOwnership(unittest.TestCase):
    def test_disjoint_paths_and_families(self):
        self.assertEqual(_input_spec(spec([mod("a",FAMILIES[0],"A/one.bin"),
                                            mod("b",FAMILIES[1],"B/two.bin")])),
                         {FAMILIES[0],FAMILIES[1]})
    def test_exact_path_collision_across_families(self):
        with self.assertRaisesRegex(ValueError,"source path"):
            _input_spec(spec([mod("a",FAMILIES[0],"A/one.bin"),
                              mod("b",FAMILIES[1],"A/one.bin")]))
    def test_casefold_collision_across_families(self):
        with self.assertRaisesRegex(ValueError,"source path"):
            _input_spec(spec([mod("a",FAMILIES[0],"A/ONE.bin"),
                              mod("b",FAMILIES[1],"a/one.BIN")]))
    def test_same_mod_path_collision(self):
        m=mod("a",FAMILIES[0],"A/one.bin")
        m["resources"].append({"family":FAMILIES[1],"source_path":"A/one.bin"})
        with self.assertRaisesRegex(ValueError,"source path"):
            _input_spec(spec([m]))
    def test_family_collision_with_distinct_paths(self):
        with self.assertRaisesRegex(ValueError,"family"):
            _input_spec(spec([mod("a",FAMILIES[0],"A/one.bin"),
                              mod("b",FAMILIES[0],"B/two.bin")]))

if __name__=="__main__":
    unittest.main()
