"""Execute the compiled ARM64 PC source-pack API against original PC templates.

Unicorn maps the exact built ELF and CPU instructions, not a Switch engine.
Neither game object memory nor CRI archive ownership is modeled.
"""
import argparse,hashlib,json,struct,sys,tempfile
from pathlib import Path
from arm64_module import module,call,H,D
from test_pc_native_pack import case
from test_native_pc_raw_arm64 import ORIGINAL_MAIN
from test_native_pc_raw_nine import _meta_python
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.pc_api_manifest import FAMILY_READERS
from portlib.pc_nsc_param_pack import FAMILIES,HEADER,RECORD

def run(main,elf,out):
    if hashlib.sha256(main.read_bytes()).hexdigest()!=ORIGINAL_MAIN:
        raise ValueError("Original Switch main SHA256 mismatch")
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        _,staged,manifest,sources=case(root,main)
        blob=(staged/"pc_native_sources.pack").read_bytes()
        assert len(blob)<0x170000,"Unicorn H region cannot hold oversized fixture"
        u,sym,symbols,_=module(elf)
        v=D+symbols["nsc_pc_pack_validate"]
        row=D+symbols["nsc_pc_pack_row_at"]
        api=D+symbols["nsc_pc_pack_get_api"]
        api_ptr=call(u,api,[])
        version,family_count,validator,reader=struct.unpack("<IIQQ",u.mem_read(api_ptr,24))
        assert (version,family_count,validator,reader)==(1,9,v,row)
        data=H+0x10000
        summary=H+0x190000
        item=H+0x191000
        sentinel=bytes([0xa5])*16
        u.mem_write(data,blob)
        u.mem_write(summary,sentinel)
        assert call(u,v,[data,len(blob),summary])==1
        mask,count,total,records=struct.unpack("<4I",u.mem_read(summary,16))
        assert mask==0x1ff and count==9 and total==len(blob)
        assert records==sum(x["record_count"] for x in manifest["families"])
        success=1;rejected=0
        for family,source_name in enumerate(FAMILIES):
            raw=sources[source_name][1]
            reader_report=FAMILY_READERS[source_name](
                raw,source_name,hashlib.sha256(raw).hexdigest())
            rows=reader_report.get("rows",reader_report.get("records"))
            indexes={0,len(rows)//2,len(rows)-1}
            for index in indexes:
                if index<0:continue
                u.mem_write(item,sentinel)
                assert call(u,row,[data,len(blob),family,index,item])==1
                values=struct.unpack("<4I",u.mem_read(item,16))
                assert values==_meta_python(family,rows[index])
                success+=1
            u.mem_write(item,sentinel)
            assert call(u,row,[data,len(blob),family,len(rows),item])==0
            assert bytes(u.mem_read(item,16))==sentinel
            rejected+=1
        u.mem_write(item,sentinel)
        assert call(u,row,[data,len(blob),9,0,item])==0
        assert bytes(u.mem_read(item,16))==sentinel
        rejected+=1
        bad=bytearray(blob);bad[-1]^=1
        u.mem_write(data,bytes(bad))
        u.mem_write(summary,sentinel)
        assert call(u,v,[data,len(bad),summary])==0
        assert bytes(u.mem_read(summary,16))==sentinel
        rejected+=1
        # Recompute top-level digest, retain original per-family digest:
        # the native reader must reject independently corrupted source bytes.
        bad[32:64]=hashlib.sha256(bad[:32]+bad[64:]).digest()
        u.mem_write(data,bytes(bad))
        assert call(u,v,[data,len(bad),summary])==0
        rejected+=1
        u.mem_write(data,blob)
        result={
            "status":"ARM64_PC_NATIVE_PACK_VALIDATED_PUBLISHED_ZIP_SOURCE_BYTES_ONLY",
            "original_main_sha256":ORIGINAL_MAIN,
            "aarch64_elf_sha256":hashlib.sha256(elf.read_bytes()).hexdigest(),
            "upstream_public_PC_families":9,
            "original_pc_source_SHA256_crosschecks":9,
            "AArch64_positive_pack_and_row_calls":success,
            "AArch64_fail_closed_rejections":rejected,
            "original_game_runtime_abi_or_ownership_verified":False,
            "gameplay_verified":False,"full_moddingapi":False,
            "ready_for_gameplay_test":False,"emulator_tested":False}
        out.mkdir(parents=True,exist_ok=True)
        (out/"pc_native_pack_arm64.json").write_text(json.dumps(result,indent=2)+"\n")
        print("PC_NSC_NATIVE_PACK_AARCH64_PASS",success,rejected,
              "NOT_NATIVE_ENGINE_OR_UZUY")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--elf",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    run(args.main,args.elf,args.output)
