"""Native original FileOpen PLT/GOT -> relocation -> symbol tests."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.native_fileopen_import import (
    inspect, _scan_relocations, _symbol, _tags, PLT, SLOT, MAIN_SHA256
)
def synth():
    mem=bytearray(1024)
    # ELF64 symtab: null symbol at index0, imported _example at index1.
    struct.pack_into("<IBBHQQ",mem,120+24,4,0x12,0,0,0,0)
    mem[280:299]=b"bad\0_example\0tail\0xx"
    struct.pack_into("<QQq",mem,400,SLOT,(1<<32)|1026,0)
    tags={6:120,5:280,10:19,11:24,23:400,2:24,20:7}
    rows=_scan_relocations(mem,tags,SLOT)
    assert len(rows)==1 and rows[0]["type_name"]=="R_AARCH64_JUMP_SLOT"
    sym=_symbol(mem,tags,1)
    assert sym["name"]=="_example"
    assert _symbol(mem,tags,0)["name"] is None
    assert _scan_relocations(mem,tags,SLOT+8)==[]
    invalid=dict(tags);invalid[20]=17
    try:_scan_relocations(mem,invalid,SLOT)
    except ValueError:pass
    else:raise AssertionError("DT_REL PLT relocation wrongly accepted")
    invalid=dict(tags);invalid[10]=2
    try:_symbol(mem,invalid,1)
    except ValueError:pass
    else:raise AssertionError("Out-of-bound ELF symbol accepted")
    # Dynamic tags from an independent in-memory MOD0 metadata fixture.
    copy=bytearray(1024)
    struct.pack_into("<I",copy,4,64)
    struct.pack_into("<i",copy,68,32)
    struct.pack_into("<QQ",copy,96,6,120)
    struct.pack_into("<QQ",copy,112,5,280)
    struct.pack_into("<QQ",copy,128,0,0)
    assert _tags(copy)[6]==120 and _tags(copy)[5]==280

def run(main,out):
    synth()
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["main_sha256"]==MAIN_SHA256
    assert report["fileopen_callsite"]=="0x1171028"
    assert report["plt_thunk"]==hex(PLT)
    assert report["got_slot"]==hex(SLOT)
    assert report["plt_words_le"]==["707200f0","114240f9","10020291","20021fd6"]
    assert len(report["original_dynamic_relocations_to_slot"])<=1
    for k in ("imported_function_implementation_proven",
              "actual_runtime_import_binding_verified",
              "native_callback_lock_async_unbind_proven",
              "object_lifetime_or_allocator_proven",
              "archive_precedence_proven","safe_runtime_hook_ABI_proven",
              "new_native_hook_installed","gameplay_verified",
              "full_moddingapi","ready_for_gameplay_test","emulator_tested"):
        assert report[k] is False
    with tempfile.TemporaryDirectory() as t:
        temp=Path(t);src=temp/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(ROOT/"tools/audit_native_fileopen_import.py"),
             "--main",str(src),"--output",str(temp/"good")]
        r=subprocess.run(cmd,capture_output=True,text=True,check=True)
        assert "ORIGINAL_FILEOPEN_PLT_IMPORT" in r.stdout
        assert json.loads((temp/"good/native_fileopen_import.json").read_text())==report
        bad=bytearray(raw);bad[33]^=1;src.write_bytes(bad)
        cmd[-1]=str(temp/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode!=0
        assert not (temp/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileopen_import.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PLT_GOT_RELOCATION_PROOF",
          [(x["type_name"],x["symbol_index"],
            x["original_dynamic_symbol"].get("name"))
           for x in report["original_dynamic_relocations_to_slot"]],
          "NO_ABI_OR_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.output)
