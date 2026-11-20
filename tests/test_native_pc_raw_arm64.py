"""Execute compiled AArch64 PC raw readers against 9 authentic PC templates.

This is ARM64 code from the generated module ELF, executed using Unicorn.
There is no game actor, native engine parameter loader, CRI archive, emulator
Uzuy gameplay or CPK owner modeled/verified in this test.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from arm64_module import module,call,H,D
from test_native_pc_raw_nine import NAMES,_meta_python
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.pc_api_manifest import FAMILY_READERS

TEMPLATES=[
 "NSC_susanooCondParam.raw32.bin",
 "NSC_partnerSlotParam.raw32.bin",
 "NSC_ougiAwakeningParam.raw.bin",
 "NSC_gudoBallParam.raw.bin",
 "NSC_charRelationParam.raw.bin",
 "NSC_pairSpSkillManagerParam.raw.bin",
 "NSC_bgmManagerParam.raw.bin",
 "NSC_specialInteractionManager.raw.bin",
 "NSC_guardEffectParam.raw.bin"
]
ORIGINAL_MAIN="2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9"

def run(main,elf,out):
    if hashlib.sha256(main.read_bytes()).hexdigest()!=ORIGINAL_MAIN:
        raise ValueError("Original stock NSO main SHA256 guard failed")
    u,sym,symbols,_=module(elf)
    validate=sym("nsc_pc_raw_validate")
    row=sym("nsc_pc_raw_row_at")
    api=D+symbols["nsc_pc_raw_get_api"]
    api_ptr=call(u,api,[])
    version,families,validator,reader=struct.unpack("<IIQQ",u.mem_read(api_ptr,24))
    assert (version,families,validator,reader)==(1,9,validate,row)
    data=H+0x10000
    sha_addr=H+0x80000
    summary=H+0x90000
    row_result=H+0xa0000
    sentinel=bytes([0xa5])*16
    accepted=0;rejected=0;cases=[]
    for kind,filename in enumerate(TEMPLATES):
        raw=(ROOT/"tests/fixtures/pc_source"/filename).read_bytes()
        digest=hashlib.sha256(raw).digest()
        expected=FAMILY_READERS[NAMES[kind]](raw,NAMES[kind],digest.hex())
        originals=expected.get("rows",expected.get("records"))
        u.mem_write(data,raw)
        u.mem_write(sha_addr,digest)
        u.mem_write(summary,sentinel)
        assert call(u,validate,[kind,data,len(raw),sha_addr,summary])==1
        count,consumed,ignored,reserved=struct.unpack("<IIII",u.mem_read(summary,16))
        assert count==len(originals),(kind,count,len(originals))
        assert ignored==(len(raw)%24 if kind==5 else 0)
        assert consumed==len(raw)-ignored and reserved==0
        accepted+=1
        sample=sorted({0,len(originals)//2,len(originals)-1})
        for index in sample:
            if index<0:continue
            u.mem_write(row_result,sentinel)
            assert call(u,row,[kind,data,len(raw),sha_addr,index,row_result])==1
            fields=struct.unpack("<IIII",u.mem_read(row_result,16))
            assert fields==_meta_python(kind,originals[index]),(kind,index,fields)
            accepted+=1
        u.mem_write(row_result,sentinel)
        assert call(u,row,[kind,data,len(raw),sha_addr,len(originals),row_result])==0
        assert bytes(u.mem_read(row_result,16))==sentinel
        rejected+=1
        u.mem_write(sha_addr,bytes(32))
        u.mem_write(summary,sentinel)
        assert call(u,validate,[kind,data,len(raw),sha_addr,summary])==0
        assert bytes(u.mem_read(summary,16))==sentinel
        rejected+=1
        cases.append({"family":NAMES[kind],"upstream_filename":filename,
                      "source_SHA256":digest.hex(),
                      "authentic_public_rows":count,
                      "AArch64_native_accessor_against_python":True})
    u.mem_write(data,b"\x7f")
    u.mem_write(sha_addr,hashlib.sha256(b"\x7f").digest())
    u.mem_write(summary,sentinel)
    assert call(u,validate,[5,data,1,sha_addr,summary])==0
    assert bytes(u.mem_read(summary,16))==sentinel
    rejected+=1
    result={
        "status":"PASS_COMPILED_AARCH64_PC_RAW_NINE_FAMILIES_PUBLIC_TEMPLATE_SLICES",
        "original_main_sha256":ORIGINAL_MAIN,
        "AArch64_ELF_SHA256":hashlib.sha256(elf.read_bytes()).hexdigest(),
        "public_PC_families":cases,
        "AArch64_successful_api_and_row_calls":accepted,
        "AArch64_invalid_source_or_row_rejections":rejected,
        "source_template_provenance":"TheLeonX/NSC-ModManager 2.1.2.1 pinned fixtures",
        "real_native_engine_parameter_consumers_executed":False,
        "native_game_object_ABI_proven":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False,
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_pc_raw_arm64.json").write_text(json.dumps(result,indent=2)+"\n")
    print("NATIVE_ARM64_PC_RAW_NINE_FAMILY_PASS",len(cases),accepted,rejected,
          "NOT_A_GAMEPLAY_RELEASE")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--elf",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    run(a.main,a.elf,a.output)
