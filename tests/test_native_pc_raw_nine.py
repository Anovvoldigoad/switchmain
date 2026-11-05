"""Cross-language PC-only nine native ARM64-compatible reader contract tests.

Compiled C++ source is included in the Switch overlay build, and the same
source is run through a native host shared-library harness to assert exact
PC raw layouts against prior Python evidence. This is NOT an engine call,
asset lifetime, stock gameplay, or native Switch parameter consumer test.
"""
import argparse,ctypes,hashlib,json,struct,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.pc_api_manifest import FAMILY_READERS

NAMES=[
 "susanooCondParam","partnerSlotParam","ougiAwakeningParam","gudoBallParam",
 "charRelationParam","pairSpSkillManagerParam","bgmManagerParam",
 "specialInteractionManager","guardEffectParam"]
class Summary(ctypes.Structure):
    _fields_=[("record_count",ctypes.c_uint32),("consumed_bytes",ctypes.c_uint32),
              ("ignored_terminal_bytes",ctypes.c_uint32),("reserved",ctypes.c_uint32)]
class Row(ctypes.Structure):
    _fields_=[("offset",ctypes.c_uint32),("length",ctypes.c_uint32),
              ("source_field_0",ctypes.c_uint32),("source_field_1",ctypes.c_uint32)]
class API(ctypes.Structure):
    _fields_=[("version",ctypes.c_uint32),("family_count",ctypes.c_uint32),
              ("validate",ctypes.c_void_p),("row_at",ctypes.c_void_p)]
def _fixed(b,n):
    assert len(b)<=n
    return b+bytes(n-len(b))
def fixtures():
    return {
        0:_fixed(b"SSN_2ITC\0",24)+struct.pack("<H",25)+bytes(6),
        1:_fixed(b"PARTNER_TYPE_2PAR\0",24)+struct.pack("<H",43)+bytes(6),
        2:struct.pack("<3I",277,277,0),
        3:struct.pack("<3I",12,101,0),
        4:struct.pack("<I",2)+struct.pack("<2I",5,9)+struct.pack("<I",0),
        5:_fixed(b"TEST_PAIR",16)+struct.pack("<ii",-1,22)+b"\x7f",
        6:_fixed(b"STAGE_TEST",48)+_fixed(b"data/sound/test.acb",48)+struct.pack("<ii",53,-1),
        7:struct.pack("<iiiiiiii",2,24,3,24,0,-3,0,0),
        8:struct.pack("<II",277,1)+b"".join([
            _fixed(b"data/effect/example.nucc",48),_fixed(b"start",48),
            _fixed(b"loop",48),_fixed(b"end",48),_fixed(b"coord",48)])}
def _meta_python(k,row):
    if k in (0,1):return (row["byte_offset"],32,row["character_id_u16"],0)
    if k in (2,3):return (row["ordinal"]*4,4,row["character_id_u32"],0)
    if k==4:return (row["byte_offset"],4+row["id_count"]*4,row["id_count"],0)
    if k==5:return (row["offset"],24,row["unlock_value_i32"]&0xffffffff,row["reserved_i32"]&0xffffffff)
    if k==6:return (row["offset"],104,row["bgm_id_i32"]&0xffffffff,row["unknown_i32"]&0xffffffff)
    if k==7:return (row["offset"],8+4*len(row["trigger_ids_raw_i32"]),row["main_char_id_i32"]&0xffffffff,len(row["trigger_ids_raw_i32"]))
    if k==8:return (row["offset"],248,row["character_id_u32"],row["mode_u32"])
    raise AssertionError("unknown family")

def run(out):
    with tempfile.TemporaryDirectory() as d:
        d=Path(d)
        source=ROOT/"overlay/source/program"
        sha_obj=d/"sha.o"
        subprocess.run(["gcc","-fPIC","-O2","-c",str(source/"nsc_sha256.c"),"-o",str(sha_obj)],check=True,capture_output=True)
        libname=d/"pcnative.so"
        subprocess.run(["g++","-std=c++17","-fPIC","-shared","-O2","-Wall","-Wextra","-Werror",
                        str(source/"nsc_pc_raw.cpp"),str(sha_obj),"-o",str(libname)],
                       check=True,capture_output=True)
        lib=ctypes.CDLL(str(libname))
        lib.nsc_pc_raw_get_api.restype=ctypes.POINTER(API)
        api=lib.nsc_pc_raw_get_api().contents
        assert (api.version,api.family_count)==(1,9) and api.validate and api.row_at
        lib.nsc_pc_raw_validate.argtypes=[ctypes.c_uint32,ctypes.c_void_p,ctypes.c_size_t,
                                           ctypes.c_void_p,ctypes.POINTER(Summary)]
        lib.nsc_pc_raw_validate.restype=ctypes.c_int
        lib.nsc_pc_raw_row_at.argtypes=[ctypes.c_uint32,ctypes.c_void_p,ctypes.c_size_t,
                                         ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(Row)]
        lib.nsc_pc_raw_row_at.restype=ctypes.c_int
        neg=0;good=0;details=[]
        def invoke(family,raw,expected=None,which=None):
            sha=bytes.fromhex(expected or hashlib.sha256(raw).hexdigest())
            b=(ctypes.c_ubyte*max(1,len(raw))).from_buffer_copy(raw or b"\0")
            expected_buf=(ctypes.c_ubyte*32).from_buffer_copy(sha)
            s=Summary(88,88,88,88)
            ok=lib.nsc_pc_raw_validate(family,b,len(raw),expected_buf,ctypes.byref(s))
            if not ok:return 0,s,None
            rr=None
            if which is not None:
                row=Row(99,99,99,99)
                row_ok=lib.nsc_pc_raw_row_at(family,b,len(raw),expected_buf,which,ctypes.byref(row))
                if row_ok:rr=(row.offset,row.length,row.source_field_0,row.source_field_1)
            return ok,s,rr
        for k,raw in fixtures().items():
            family=NAMES[k]
            py=FAMILY_READERS[family](raw,family,hashlib.sha256(raw).hexdigest())
            rows=py.get("rows",py.get("records"))
            ok,s,first=invoke(k,raw,which=0)
            assert ok and s.record_count==len(rows)
            assert first==_meta_python(k,rows[0]),(family,first,rows[0])
            for i,row in enumerate(rows):
                okay,summary,native=invoke(k,raw,which=i)
                assert okay and native==_meta_python(k,row)
                good+=1
            okay,_,bad_row=invoke(k,raw,which=len(rows))
            assert okay and bad_row is None
            expected_tail=1 if k==5 else 0
            assert (s.consumed_bytes,s.ignored_terminal_bytes)==(len(raw)-expected_tail,expected_tail)
            wrong="0"*64 if hashlib.sha256(raw).hexdigest()!="0"*64 else "1"*64
            rejected,_,_=invoke(k,raw,expected=wrong)
            assert rejected==0
            neg+=1
            details.append({"family":family,"source_bytes":len(raw),"records":len(rows),
                            "native_rows_match_PC_python_reader":True})
        # Public raw templates are already bundled in this repository and
        # independently checked against upstream Git blob IDs by earlier tests.
        # Check all nine actual public NSC Mod Manager 2.1.2.1 inputs, not only
        # synthetic records. They are PC raw bytes, not Switch XFBIN assets.
        real_names=[
            "NSC_susanooCondParam.raw32.bin",
            "NSC_partnerSlotParam.raw32.bin",
            "NSC_ougiAwakeningParam.raw.bin",
            "NSC_gudoBallParam.raw.bin",
            "NSC_charRelationParam.raw.bin",
            "NSC_pairSpSkillManagerParam.raw.bin",
            "NSC_bgmManagerParam.raw.bin",
            "NSC_specialInteractionManager.raw.bin",
            "NSC_guardEffectParam.raw.bin",
        ]
        authentic=[]
        for k,name in enumerate(real_names):
            raw=(ROOT/"tests/fixtures/pc_source"/name).read_bytes()
            digest=hashlib.sha256(raw).hexdigest()
            report=FAMILY_READERS[NAMES[k]](raw,NAMES[k],digest)
            rows=report.get("rows",report.get("records"))
            ok,summary,_=invoke(k,raw)
            assert ok and summary.record_count==len(rows),(k,name,summary.record_count,len(rows))
            for i,row in enumerate(rows):
                okay,_,native=invoke(k,raw,which=i)
                assert okay and native==_meta_python(k,row),(k,i,native,row)
                good+=1
            expected_tail=1 if len(raw)%24==1 and k==5 else 0
            assert summary.consumed_bytes==len(raw)-expected_tail
            assert summary.ignored_terminal_bytes==expected_tail
            authentic.append({"family":NAMES[k],"filename":name,
                              "actual_public_template_sha256":digest,
                              "bytes":len(raw),"records":len(rows),
                              "native_CPP_rows_match_original_PC_fixture":True})
        invalid={
          0:[b"x"*32,fixtures()[0]*2,fixtures()[0][:-1]],
          1:[b"x"*32,fixtures()[1]*2],
          2:[b"a",b"\0"*40004],
          3:[b"abc",b"\0"*40004],
          4:[struct.pack("<I",2)+struct.pack("<I",17),b"\0"*40004],
          5:[fixtures()[5]+b"X",b"a"*23],
          6:[fixtures()[6][:-1]],
          7:[struct.pack("<ii",1,2),struct.pack("<iii",1,25,-1)],
          8:[fixtures()[8][:-1]]}
        for family,values in invalid.items():
            for value in values:
                ok,_,_=invoke(family,value)
                assert ok==0,(family,len(value))
                neg+=1
        for family in (9,10,0xffffffff):
            ok,_,_=invoke(family,fixtures()[0])
            assert not ok;neg+=1
        for family in range(9):
            ok,_,_=invoke(family,b"")
            assert not ok;neg+=1
        special=struct.pack("<i",0)
        assert invoke(7,special)[1].record_count==0 and invoke(7,special)[0]==1
        result={"status":"NATIVE_CPP_PC_RAW_NINE_FAMILY_CROSS_LANGUAGE_PASS",
                "source":"compiled shared C++ reader also built into overlay",
                "families":details,"actual_public_manager_raw_fixtures":authentic,
                "authentic_public_PC_families_checked":len(authentic),
                "matching_PC_row_views":good,
                "invalid_and_wrong_SHA_rejected":neg,
                "native_engine_consumers_connected":False,
                "native_game_ABI_or_owned_buffer_lifetimes_verified":False,
                "real_PC_mod_source_sample_tested":False,
                "switch_gameplay_verified":False,
                "full_moddingapi":False,"ready_for_gameplay_test":False,
                "emulator_tested":False}
        out.mkdir(parents=True,exist_ok=True)
        (out/"native_pc_raw_nine_families.json").write_text(json.dumps(result,indent=2)+"\n")
        print("NATIVE_PC_RAW_NINE_FAMILY_CPP_PASS",len(details),good,neg,"NO_GAMEPLAY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    run(p.parse_args().output)
