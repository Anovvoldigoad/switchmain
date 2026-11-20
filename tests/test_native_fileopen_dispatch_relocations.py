"""Original-main read-only FileOpen indirect relocation pair proof."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from portlib.native_fileopen_dispatch_relocations import candidate_pairs, inspect
from portlib.native_cpk_indirect import RELA_TYPE

def run(main, output):
    rows=[(0x1000,RELA_TYPE,0x200),(0x10c0,RELA_TYPE,0x300),
          (0x1058,RELA_TYPE,0x400),(0x2000,42,0x500)]
    assert candidate_pairs(rows,0x1000,0xc0)==[
        {"candidate_base":"0x1000","method_slot":"0x10c0",
         "method_target":"0x300","base_slot_relocation_addend":"0x200"}]
    assert candidate_pairs(rows,0x1000,0x58)==[
        {"candidate_base":"0x1000","method_slot":"0x1058",
         "method_target":"0x400","base_slot_relocation_addend":"0x200"}]
    assert candidate_pairs([(0x10c0,RELA_TYPE,0x300)],0x1000,0xc0)==[]
    assert candidate_pairs([(0x1000,RELA_TYPE,0x200),
                            (0x10c0,RELA_TYPE,0x1000)],0x1000,0xc0)==[]
    for bad in (-8,3):
        try: candidate_pairs(rows,0x1000,bad)
        except ValueError: pass
        else: raise AssertionError("Invalid offset accepted")
    for bad in ([(0x1000,RELA_TYPE,0),(0x1000,RELA_TYPE,4)],
                [(0x1001,RELA_TYPE,0)]):
        try: candidate_pairs(bad,0x1000,0)
        except ValueError: pass
        else: raise AssertionError("Invalid RELATIVE slots accepted")
    raw=main.read_bytes()
    result=inspect(raw)
    assert len(result["dispatches"])==2
    assert [x["observed_indirect_field_offset"] for x in result["dispatches"]]==[0xc0,0x58]
    assert all(x["runtime_x8_base_matched_to_candidate"] is False for x in result["dispatches"])
    for flag in ("native_consumer_abi_proven","ownership_async_unbind_destructor_proven",
                 "archive_precedence_proven","new_runtime_hook",
                 "full_moddingapi","ready_for_gameplay_test","emulator_tested"):
        assert result[flag] is False
    output.mkdir(parents=True,exist_ok=True)
    (output/"native_fileopen_dispatch_relocations.json").write_text(
        json.dumps(result,indent=2)+"\n")
    print("ORIGINAL_FILEOPEN_DISPATCH_RELOCATION_PAIRS_STATIC_PASS",
          [(x["observed_indirect_field_offset"],x["candidate_count"])
           for x in result["dispatches"]],"NOT_RUNTIME_ABI")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    run(a.main,a.output)
