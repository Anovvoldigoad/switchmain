"""Exact-byte FileLoad SP/FP inventory, synthetic and pinned-original tests."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from portlib.native_fileload_stack_access import census,inspect
from portlib.native_cpk_graph import MAIN_SHA256

def run(main,out):
    # STR X0,[SP,#8]; LDR X1,[SP,#8]; STR X0,[X2]; RET
    data=bytes.fromhex("e00700f9e10740f9400000f9c0035fd6")
    got=census(data,0x1000)
    assert [(x["pc"],x["base"],x["displacement"]) for x in got]==[
        ("0x1000","sp",8),("0x1004","sp",8)]
    assert all(not x["object_identity_proven"] for x in got)
    try:
        census(data[:-1],0x1000)
    except ValueError:
        pass
    else:
        raise AssertionError("Accepted truncated ARM64 instruction")
    raw=main.read_bytes()
    report=inspect(raw)
    assert hashlib.sha256(raw).hexdigest()==MAIN_SHA256
    assert all(not report[k] for k in (
        "stack_pointer_delta_proven","stack_slot_dataflow_proven",
        "ownership_lifecycle_async_destructor_proven",
        "native_consumer_abi_proven","hook_added","Uzuy_gameplay_verified"))
    assert all(not a["object_identity_proven"] for a in report["accesses"])
    mutated=bytearray(raw)
    mutated[255]^=1
    try:
        inspect(mutated)
    except ValueError:
        pass
    else:
        raise AssertionError("Accepted modified original main")
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_stack_access.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PINNED_FILELOAD_STACK_CENSUS_PASS",len(report["accesses"]),
          "NO_OWNERSHIP_OR_CONSUMER_ABI")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    run(a.main,a.output)
