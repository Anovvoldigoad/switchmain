"""Execute original SHA-pinned Switch ARM64 status setter with modeled locks.

This tests the real original main code at 0x120661C, not an assistant-written
reimplementation of its branches. External lock/unlock services 0x1215358
and 0x1215374 are modeled as transparent no-ops, so it is a bounded
native-code slice, NEVER real CRI async completion or Uzuy gameplay.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
import unicorn.arm64_const as ar
from arm64_module import M,H,align,call,module
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from portlib.nso_profile import segments
from portlib.native_fileload_status import MAIN_SHA256,inspect,STATUS_HELPER

OBJECT=H+0x18000
STATUS_OFFSET=0x68
LOCK_AT=0x1215358
UNLOCK_AT=0x1215374

PINNED_NATIVE_BODY={
    0x1206624:("add","x19, x0, #0x18"),
    0x1206628:("mov","x21, x0"),
    0x1206630:("mov","w20, w1"),
    0x1206634:("bl","#0x1215358"),
    0x1206638:("ldr","w8, [x21, #0x68]"),
    0x120663c:("cmp","w8, #3"),
    0x1206640:("ccmp","w8, #5, #4, ne"),
    0x1206644:("b.ne","#0x1206658"),
    0x1206658:("str","w20, [x21, #0x68]"),
    0x1206668:("b","#0x1215374"),
}


def run(main,elf,out):
    raw=main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MAIN_SHA256:
        raise ValueError("Original v1.70 main SHA256 mismatch")
    evidence=inspect(raw)
    by_at={int(item["at"],16):item
           for item in evidence["helper_code"]["instructions"]}
    for offset,(mnemonic,operands) in PINNED_NATIVE_BODY.items():
        observed=by_at[offset]
        if (observed["mnemonic"],observed["operands"])!=(mnemonic,operands):
            raise ValueError("Pinned native helper body differs at "+hex(offset))
    u,_,_,_=module(elf)
    code=segments(raw)[0][1]
    u.mem_map(M,align(len(code)),7)
    u.mem_write(M,code)
    u.mem_write(OBJECT,bytes(0x100))
    mocked={LOCK_AT:0,UNLOCK_AT:0}
    def modeled_locks(uc,at,n,d):
        offset=at-M
        if offset not in mocked:
            raise AssertionError("Unexpected native external helper")
        mocked[offset]+=1
        uc.reg_write(ar.UC_ARM64_REG_PC,uc.reg_read(ar.UC_ARM64_REG_LR))
    for offset in mocked:
        u.hook_add(UC_HOOK_CODE,modeled_locks,begin=M+offset,end=M+offset)
    trials=[]
    old_values=(0,1,2,3,4,5,6,0xffffffff)
    requested=(0,2,5,6)
    for prev in old_values:
        for next_value in requested:
            u.mem_write(OBJECT+STATUS_OFFSET,struct.pack("<I",prev))
            before=tuple(mocked.values())
            call(u,M+STATUS_HELPER,[OBJECT,next_value],instruction_budget=2000)
            after=struct.unpack("<I",u.mem_read(OBJECT+STATUS_OFFSET,4))[0]
            expected=prev if prev in (3,5) else next_value
            if after!=expected:
                raise AssertionError((prev,next_value,after,expected))
            assert mocked[LOCK_AT]==before[0]+1
            assert mocked[UNLOCK_AT]==before[1]+1
            trials.append({"initial_status":prev,"requested_status":next_value,
                           "actual_status":after,"expected_status":expected,
                           "preserved_old_terminal_3_or_5":prev in (3,5)})
    assert len(trials)==32
    out.mkdir(parents=True,exist_ok=True)
    result={
        "status":"PASS_ORIGINAL_ARM64_NATIVE_STATUS_SETTER_WITH_MODELED_LOCKS",
        "original_main_sha256":MAIN_SHA256,
        "helper_address":"0x120661c",
        "actual_native_instructions_executed":True,
        "status_field_offset":STATUS_OFFSET,
        "observed_unchanged_old_state_values":[3,5],
        "native_scenarios":len(trials),
        "cases":trials,
        "external_lock_service_was_modeled":True,
        "external_unlock_service_was_modeled":True,
        "lock_model_calls":mocked[LOCK_AT],
        "unlock_model_calls":mocked[UNLOCK_AT],
        "original_CRI_multithreaded_lock_semantics_verified":False,
        "FileOpen_failure_and_XFBIN_read_failure_end_to_end_verified":False,
        "CPK_async_completed":False,
        "archive_lookup_precedence_verified":False,
        "safe_new_hook_ABI_verified":False,
        "native_hook_added":False,
        "emulator_tested":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
    }
    (out/"native_fileload_status_slice.json").write_text(json.dumps(result,indent=2)+"\n")
    print("ORIGINAL_NATIVE_FILELOAD_STATUS_SLICE_PASS",
          len(trials),"old status 3/5 guarded, other statuses updated",
          "main",MAIN_SHA256,
          "lock_calls",mocked[LOCK_AT],"unlock_calls",mocked[UNLOCK_AT],
          "LOCKS_MODELED, NOT CRI RUNTIME")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--elf",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.elf,a.output)
