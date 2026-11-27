"""Execute pinned FileLoad service wrappers with leaf calls modeled.

The original ARM64 wrapper bodies are executed. Four direct leaf targets are
intercepted as opaque stubs; this proves only the wrapper's observed owner/count
state transitions under those modeled returns, not OS mutex semantics,
concurrency, native consumer ABI, or Uzuy gameplay.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
import unicorn.arm64_const as ar
from arm64_module import M,H,align,call,module

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.nso_profile import segments
from portlib.native_fileload_status import MAIN_SHA256,inspect

OBJECT=H+0x18000
SUBOBJECT=OBJECT+0x18
STATUS_OFFSET=0x68
GATE_OFFSET=0x28
OWNER_OFFSET=0x08
COUNT_OFFSET=0x0c
STATUS_HELPER=0x120661c
LOCK_DISPATCH=0x1215358
UNLOCK_DISPATCH=0x1215374
THREAD_CONTEXT=0x12f4cf0
THREAD_TOKEN=0x12f50e0
LOCK_PRIMITIVE=0x12a35b4
UNLOCK_PRIMITIVE=0x12a35bc


def read32(u,address):
    return struct.unpack("<I",u.mem_read(address,4))[0]


def write32(u,address,value):
    u.mem_write(address,struct.pack("<I",value&0xffffffff))


def run(main,elf,out):
    raw=main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    evidence=inspect(raw)
    required={
        THREAD_CONTEXT:(0x1158c9c,"BL"),
        THREAD_TOKEN:(0x1158ca4,"BL"),
        LOCK_PRIMITIVE:(0x1158cbc,"BL"),
        UNLOCK_PRIMITIVE:(0x1158d2c,"B"),
    }
    dep_edges=evidence["service_dependency_incoming_direct_edges"]
    for target,(caller,kind) in required.items():
        if not any(x["caller"]==hex(caller) and x["kind"]==kind
                   for x in dep_edges[hex(target)]):
            raise ValueError("Pinned service dependency edge changed at "+hex(caller))

    u,_,_,_=module(elf)
    code=segments(raw)[0][1]
    u.mem_map(M,align(len(code)),7)
    u.mem_write(M,code)
    u.mem_write(OBJECT,bytes(0x100))

    state={
        "thread_context_result":1,
        "thread_token_result":0x1234,
        "thread_context_calls":0,
        "thread_token_calls":0,
        "lock_calls":[],
        "unlock_calls":[],
    }

    def modeled_leaf(uc,at,size,data):
        offset=at-M
        if offset==THREAD_CONTEXT:
            state["thread_context_calls"]+=1
            uc.reg_write(ar.UC_ARM64_REG_X0,state["thread_context_result"])
        elif offset==THREAD_TOKEN:
            state["thread_token_calls"]+=1
            uc.reg_write(ar.UC_ARM64_REG_X0,state["thread_token_result"])
        elif offset==LOCK_PRIMITIVE:
            state["lock_calls"].append(uc.reg_read(ar.UC_ARM64_REG_X0))
        elif offset==UNLOCK_PRIMITIVE:
            state["unlock_calls"].append(uc.reg_read(ar.UC_ARM64_REG_X0))
        else:
            raise AssertionError("Unexpected modeled leaf "+hex(offset))
        uc.reg_write(ar.UC_ARM64_REG_PC,uc.reg_read(ar.UC_ARM64_REG_LR))

    for offset in (THREAD_CONTEXT,THREAD_TOKEN,LOCK_PRIMITIVE,UNLOCK_PRIMITIVE):
        u.hook_add(UC_HOOK_CODE,modeled_leaf,begin=M+offset,end=M+offset)

    def reset_state():
        write32(u,SUBOBJECT+GATE_OFFSET,1)
        write32(u,SUBOBJECT+OWNER_OFFSET,0)
        write32(u,SUBOBJECT+COUNT_OFFSET,0)
        state.update({
            "thread_context_calls":0,"thread_token_calls":0,
            "lock_calls":[],"unlock_calls":[],
        })

    scenarios=[]

    reset_state()
    call(u,M+LOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert read32(u,SUBOBJECT+OWNER_OFFSET)==0x1234
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==1
    assert state["lock_calls"]==[SUBOBJECT]
    assert state["thread_context_calls"]==1 and state["thread_token_calls"]==1
    scenarios.append({"case":"first_acquire","owner":0x1234,"count":1,
                      "lock_calls":len(state["lock_calls"])})
    call(u,M+LOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert read32(u,SUBOBJECT+OWNER_OFFSET)==0x1234
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==2
    assert state["lock_calls"]==[SUBOBJECT]
    scenarios.append({"case":"same_token_recursive_acquire","owner":0x1234,
                      "count":2,"lock_calls":len(state["lock_calls"])})
    call(u,M+UNLOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert read32(u,SUBOBJECT+OWNER_OFFSET)==0x1234
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==1
    assert state["unlock_calls"]==[]
    scenarios.append({"case":"nonfinal_release","owner":0x1234,"count":1,
                      "unlock_calls":0})
    call(u,M+UNLOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert read32(u,SUBOBJECT+OWNER_OFFSET)==0
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==0
    assert state["unlock_calls"]==[SUBOBJECT]
    scenarios.append({"case":"final_release","owner":0,"count":0,
                      "unlock_calls":len(state["unlock_calls"])})

    reset_state()
    write32(u,SUBOBJECT+OWNER_OFFSET,0x777)
    call(u,M+UNLOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert read32(u,SUBOBJECT+OWNER_OFFSET)==0x777
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==0
    assert state["unlock_calls"]==[]
    scenarios.append({"case":"zero_count_release_underflow","owner":0x777,
                      "count":0,"unlock_calls":0})

    reset_state()
    state["thread_context_result"]=0
    call(u,M+LOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert state["thread_context_calls"]==1
    assert state["thread_token_calls"]==0
    assert read32(u,SUBOBJECT+OWNER_OFFSET)==0
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==1
    assert state["lock_calls"]==[]
    call(u,M+UNLOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==0
    assert len(state["unlock_calls"])==1
    scenarios.append({"case":"zero_context_result","owner":0,"count":0,
                      "token_provider_calls":0,"unlock_calls":1})

    reset_state()
    state["thread_context_result"]=1
    write32(u,SUBOBJECT+OWNER_OFFSET,0x777)
    write32(u,SUBOBJECT+COUNT_OFFSET,1)
    call(u,M+LOCK_DISPATCH,[SUBOBJECT],instruction_budget=5000)
    assert state["lock_calls"]==[SUBOBJECT]
    assert read32(u,SUBOBJECT+OWNER_OFFSET)==0x1234
    assert read32(u,SUBOBJECT+COUNT_OFFSET)==2
    scenarios.append({"case":"different_owner_token","owner":0x1234,
                      "count":2,"modeled_lock_return":"immediate"})

    state["thread_context_result"]=1
    state["thread_token_result"]=0x1234
    state["thread_context_calls"]=0
    state["thread_token_calls"]=0
    state["lock_calls"]=[]
    state["unlock_calls"]=[]
    trials=[]
    for previous in (0,1,2,3,4,5,6,0xffffffff):
        for requested in (0,2,5,6):
            reset_state()
            write32(u,OBJECT+STATUS_OFFSET,previous)
            before_lock=len(state["lock_calls"])
            before_unlock=len(state["unlock_calls"])
            call(u,M+STATUS_HELPER,[OBJECT,requested],instruction_budget=5000)
            actual=read32(u,OBJECT+STATUS_OFFSET)
            expected=previous if previous in (3,5) else requested
            assert actual==expected,(previous,requested,actual,expected)
            assert read32(u,SUBOBJECT+OWNER_OFFSET)==0
            assert read32(u,SUBOBJECT+COUNT_OFFSET)==0
            assert len(state["lock_calls"])==before_lock+1
            assert len(state["unlock_calls"])==before_unlock+1
            trials.append({
                "initial_status":previous,"requested_status":requested,
                "actual_status":actual,"expected_status":expected,
                "terminal_3_or_5_preserved":previous in (3,5),
            })
    assert len(trials)==32

    out.mkdir(parents=True,exist_ok=True)
    result={
        "status":"PASS_ORIGINAL_ARM64_FILELOAD_SERVICE_WRAPPERS_WITH_MODELED_LEAVES",
        "original_main_sha256":MAIN_SHA256,
        "dispatch_entrypoints":[hex(LOCK_DISPATCH),hex(UNLOCK_DISPATCH)],
        "wrapper_targets":["0x1158c90","0x1158d10"],
        "leaf_targets_modeled":[hex(THREAD_CONTEXT),hex(THREAD_TOKEN),
                                hex(LOCK_PRIMITIVE),hex(UNLOCK_PRIMITIVE)],
        "actual_original_wrapper_instructions_executed":True,
        "wrapper_owner_count_state_machine_verified":True,
        "wrapper_scenarios":scenarios,
        "status_helper_trials":len(trials),
        "status_helper_cases":trials,
        "external_leaf_services_modeled":True,
        "thread_token_provider_semantics_verified":False,
        "mutex_primitive_semantics_verified":False,
        "concurrent_behavior_verified":False,
        "native_consumer_abi_verified":False,
        "ownership_lifecycle_async_rollback_unbind_destructor_verified":False,
        "archive_precedence_verified":False,
        "safe_new_hook_abi_verified":False,
        "native_hook_added":False,
        "emulated_arm64_tested":True,
        "uzuy_tested":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False,
    }
    (out/"native_fileload_service_slice.json").write_text(
        json.dumps(result,indent=2)+"\n")
    print("PINNED_FILELOAD_SERVICE_WRAPPERS_EMULATED_PASS",
          "scenarios",len(scenarios),"status_trials",len(trials),
          "original wrappers executed; four leaf targets modeled",
          "NO_MUTEX_CONCURRENCY_ABI_OR_UZUY_PROOF")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--elf",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    run(a.main,a.elf,a.output)
