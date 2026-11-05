"""Regression: real pinned relocation-slot reference instructions, not ABI."""
import argparse,json,subprocess,sys,struct,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_cpk_pointer_use import (
    MAIN_SHA256,FOCUS_SLOTS,REQUIRED_RELOCATIONS,inspect,_match_pair,
    _source_records,NEIGHBORHOOD,
)


def _adrp(pc,target,reg):
    delta=((target&~0xfff)-(pc&~0xfff))>>12
    imm=delta&0x1fffff
    return 0x90000000 | ((imm&3)<<29) | (((imm>>2)&0x7ffff)<<5) | reg


def _add(reg,lo):
    return 0x91000000 | (lo<<10) | (reg<<5) | reg


def _ldr(dest,base,imm):
    return 0xf9400000 | ((imm//8)<<10) | (base<<5) | dest


def run(main,out):
    focus=FOCUS_SLOTS[0]
    assert _match_pair(_adrp(0,focus,9),_add(9,focus&0xfff),0)==(
        "ADRP_ADD_ADDRESS",focus)
    assert _match_pair(_adrp(0,focus,9),_ldr(8,9,focus&0xfff),0)==(
        "ADRP_LDR64_SLOT",focus)
    assert _match_pair(_adrp(0,focus,9),_add(8,focus&0xfff),0) is None
    small=bytearray(32)
    struct.pack_into("<II",small,0,_adrp(0,focus,9),_ldr(8,9,focus&0xfff))
    sample=_source_records(bytes(small),{focus:0x106edb8})
    assert len(sample)==1
    assert sample[0]["target_is_relative_relocation_slot"] is True
    assert sample[0]["intervening_register_clobber_ruled_out"] is True
    assert sample[0]["kind"]=="ADRP_LDR64_SLOT"
    original=main.read_bytes()
    report=inspect(original)
    assert report["main_sha256"]==MAIN_SHA256
    assert len(report["regions"])==4
    assert report["focus_slots"]==[f"0x{x:x}" for x in FOCUS_SLOTS]
    byfocus={int(r["focus_slot"],16):r for r in report["regions"]}
    for slot,target in REQUIRED_RELOCATIONS.items():
        for focus,region in byfocus.items():
            if abs(slot-focus)<=NEIGHBORHOOD:
                assert any(int(x["slot"],16)==slot and
                           int(x["target"],16)==target
                           for x in region["nearby_relative_code_targets"])
    assert report["native_ABI_verified"] is False
    assert report["vtable_base_or_constructor_proven"] is False
    assert report["native_hooks_added"] is False
    assert report["gameplay_verified"] is False
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);src=d/"main";src.write_bytes(original)
        cmd=[sys.executable,str(R/"tools/audit_native_cpk_pointer_use.py"),
             "--main",str(src),"--output",str(d/"good")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((d/"good/native_cpk_pointer_use.json").read_text())==report
        altered=bytearray(original);altered[255]^=1;src.write_bytes(altered)
        cmd[-1]=str(d/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (d/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_cpk_pointer_use.json").write_text(json.dumps(report,indent=2)+"\n")
    for area in report["regions"]:
        print("CPK_POINTER_SOURCE_PASSED",area["focus_slot"],
              "relocations",area["nearby_RELATIVE_slot_count"],
              "use_candidates",area["data_address_use_candidate_count"],
              "exact_adjacent_or_ADR",area["exact_slot_adjacent_or_ADR_witness_count"])
    print("Source usage scan PASS, NO ABI/GAMEPLAY PROOF")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
