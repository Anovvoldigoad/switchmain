"""End-to-end original PC ZIP -> native source pack -> compiled C++ row reader.

All nine fixture byte streams are real public NSC Mod Manager 2.1.2.1 source
templates already provenance-checked elsewhere. The ZIP wrapping is a
synthetic fixture, NOT an authentic installed PC mod or gameplay proof.
"""
import argparse,ctypes,hashlib,json,struct,subprocess,sys,tempfile,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.pc_nsc_archive_stage import stage
from portlib.pc_nsc_param_pack import assemble,FAMILIES,HEADER,RECORD,DATA_START,MAGIC
from portlib.native_cpk_graph import MAIN_SHA256
from portlib.pc_api_manifest import FAMILY_READERS
from test_native_pc_raw_arm64 import TEMPLATES
from test_native_pc_raw_nine import _meta_python

class PackSummary(ctypes.Structure):
    _fields_=[("mask",ctypes.c_uint32),("sources",ctypes.c_uint32),
              ("bytes",ctypes.c_uint32),("records",ctypes.c_uint32)]
class Row(ctypes.Structure):
    _fields_=[("offset",ctypes.c_uint32),("size",ctypes.c_uint32),
              ("value0",ctypes.c_uint32),("value1",ctypes.c_uint32)]
class API(ctypes.Structure):
    _fields_=[("version",ctypes.c_uint32),("family_count",ctypes.c_uint32),
              ("validate",ctypes.c_void_p),("row_at",ctypes.c_void_p)]

def case(root,main):
    """Make a byte-identical staged ZIP of nine authentic public PC sources."""
    path=root/"source_fixture.nsc"
    sources={}
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as z:
        for family,filename in zip(FAMILIES,TEMPLATES):
            raw=(ROOT/"tests/fixtures/pc_source"/filename).read_bytes()
            source_path="PC/param/"+filename
            z.writestr(source_path,raw)
            sources[family]=(source_path,raw)
    zip_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    staged=root/"staged"
    stage(path,zip_sha,staged)
    spec={
        "original_main":{"path":str(main),"sha256":MAIN_SHA256},
        "mods":[{"mod_id":"pc_source","staged_path":str(staged),
                 "original_archive":str(path),"source_sha256":zip_sha,
                 "resources":[{"family":family,"source_path":source_path}
                              for family,(source_path,_) in sources.items()]}]}
    output=root/"candidate"
    manifest=assemble(spec,output)
    return spec,output,manifest,sources

def run(main,out):
    if hashlib.sha256(main.read_bytes()).hexdigest()!=MAIN_SHA256:
        raise ValueError("Main SHA mismatch")
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        spec,output,manifest,sources=case(root,main)
        blob=(output/"pc_native_sources.pack").read_bytes()
        assert len(blob)==manifest["packed_bytes"] and blob[:16]==MAGIC
        assert struct.unpack_from("<IIII",blob,16)==(1,9,len(blob),0x1ff)
        assert manifest["family_count"]==9
        assert manifest["original_Switch_engine_param_consumers_connected"] is False
        assert json.loads((output/"manifest.json").read_text())==manifest
        assert hashlib.sha256(blob).hexdigest()==manifest["packed_sha256"]
        for family in range(9):
            offset,size=struct.unpack_from("<II",blob,HEADER+family*RECORD)
            raw=sources[FAMILIES[family]][1]
            assert blob[offset:offset+size]==raw
            assert blob[HEADER+family*RECORD+8:HEADER+family*RECORD+40]==hashlib.sha256(raw).digest()

        source=ROOT/"overlay/source/program"
        obj=root/"sha.o"
        subprocess.run(["gcc","-O2","-fPIC","-c",str(source/"nsc_sha256.c"),"-o",str(obj)],
                       check=True,capture_output=True)
        so=root/"nscpcpack.so"
        subprocess.run(["g++","-O2","-std=c++17","-fPIC","-shared",
                        "-Werror","-Wall","-Wextra",
                        str(source/"nsc_pc_raw.cpp"),str(source/"nsc_pc_pack.cpp"),
                        str(obj),"-o",str(so)],check=True,capture_output=True)
        lib=ctypes.CDLL(str(so))
        lib.nsc_pc_pack_get_api.restype=ctypes.POINTER(API)
        api=lib.nsc_pc_pack_get_api().contents
        assert api.version==1 and api.family_count==9 and api.validate and api.row_at
        lib.nsc_pc_pack_validate.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(PackSummary)]
        lib.nsc_pc_pack_validate.restype=ctypes.c_int
        lib.nsc_pc_pack_row_at.argtypes=[ctypes.c_void_p,ctypes.c_size_t,
            ctypes.c_uint32,ctypes.c_uint32,ctypes.POINTER(Row)]
        lib.nsc_pc_pack_row_at.restype=ctypes.c_int

        def inspect(raw,family=None,row=0):
            buffer=ctypes.create_string_buffer(raw,len(raw))
            summary=PackSummary(123,123,123,123)
            good=lib.nsc_pc_pack_validate(buffer,len(raw),ctypes.byref(summary))
            value=None
            if family is not None:
                result=Row(456,456,456,456)
                row_ok=lib.nsc_pc_pack_row_at(buffer,len(raw),family,row,ctypes.byref(result))
                value=(row_ok,(result.offset,result.size,result.value0,result.value1))
            return good,summary,value

        good,summary,_=inspect(blob)
        expected_count=sum(x["record_count"] for x in manifest["families"])
        assert good and (summary.mask,summary.sources,summary.bytes,summary.records)==(
            0x1ff,9,len(blob),expected_count)
        negatives=0
        # The native reader must reject metadata output aliases to the
        # caller-owned source pack, including partial boundary overlaps.
        for api_name,offset,output_type in (
            ("validate",0,PackSummary),
            ("validate",len(blob)-1,PackSummary),
            ("row",0,Row),
            ("row",len(blob)-1,Row),
        ):
            buf=ctypes.create_string_buffer(blob,len(blob)+64)
            original=bytes(buf.raw)
            output=ctypes.cast(ctypes.byref(buf,offset),ctypes.POINTER(output_type))
            if api_name=="validate":
                accepted=lib.nsc_pc_pack_validate(buf,len(blob),output)
            else:
                accepted=lib.nsc_pc_pack_row_at(buf,len(blob),0,0,output)
            assert accepted==0 and buf.raw==original
            negatives+=1
        positives=1
        for k,family in enumerate(FAMILIES):
            raw=sources[family][1]
            rows=FAMILY_READERS[family](raw,family,hashlib.sha256(raw).hexdigest())
            entries=rows.get("rows",rows.get("records"))
            for ordinal in {0,len(entries)//2,len(entries)-1}:
                if ordinal<0:continue
                ok,_,read=inspect(blob,k,ordinal)
                assert ok and read==(1,_meta_python(k,entries[ordinal]))
                positives+=1
        def invalid(data):
            nonlocal negatives
            valid,summary,_=inspect(data)
            assert valid==0
            assert (summary.mask,summary.sources,summary.bytes,summary.records)==(123,123,123,123)
            negatives+=1
        wrong=bytearray(blob);wrong[-1]^=1;invalid(bytes(wrong))
        wrong[32:64]=hashlib.sha256(wrong[:32]+wrong[64:]).digest()
        invalid(bytes(wrong)) # per-family SHA still pins bytes
        wrong=bytearray(blob);wrong[0]^=1;invalid(bytes(wrong))
        wrong=bytearray(blob);struct.pack_into("<I",wrong,24,len(wrong)+1)
        invalid(bytes(wrong))
        wrong=bytearray(blob);struct.pack_into("<I",wrong,16,7)
        invalid(bytes(wrong))
        wrong=bytearray(blob);struct.pack_into("<I",wrong,28,0)
        invalid(bytes(wrong))
        wrong=bytearray(blob);wrong[HEADER+44]=1
        wrong[32:64]=hashlib.sha256(wrong[:32]+wrong[64:]).digest()
        invalid(bytes(wrong))
        wrong=bytearray(blob);struct.pack_into("<I",wrong,HEADER,100)
        wrong[32:64]=hashlib.sha256(wrong[:32]+wrong[64:]).digest()
        invalid(bytes(wrong))
        wrong=bytearray(blob);wrong.extend(b"\0")
        wrong[32:64]=hashlib.sha256(wrong[:32]+wrong[64:]).digest()
        invalid(bytes(wrong))
        for k in range(9):
            ok,_,(success,old)=inspect(blob,k,0xffffffff)
            assert ok and success==0 and old==(456,456,456,456)
            negatives+=1
        ok,_,(success,old)=inspect(blob,9,0)
        assert ok and success==0 and old==(456,456,456,456)
        negatives+=1
        # A one-family pack is valid; omitted families must be all-zero rows.
        partial=json.loads(json.dumps(spec))
        partial["mods"][0]["resources"]=partial["mods"][0]["resources"][:1]
        part_dir=root/"partial"
        part_manifest=assemble(partial,part_dir)
        part=(part_dir/"pc_native_sources.pack").read_bytes()
        partial_ok,partial_s,_=inspect(part)
        assert partial_ok and partial_s.mask==1 and partial_s.sources==1
        assert part_manifest["family_mask"]==1
        positives+=1
        for i in range(1,9):
            assert part[HEADER+i*RECORD:HEADER+(i+1)*RECORD]==bytes(RECORD)
        # Source-precedence conflicts are rejected BEFORE assembly.
        def reject(s):
            nonlocal negatives
            dest=root/("rejected_"+str(negatives))
            try:assemble(s,dest)
            except (ValueError,FileNotFoundError,zipfile.BadZipFile):
                assert not dest.exists()
                negatives+=1
            else:raise AssertionError("Unsafe source spec accepted")
        reject(dict(spec,original_main={"path":str(main),"sha256":"0"*64}))
        broken=json.loads(json.dumps(spec))
        broken["mods"][0]["resources"].append(broken["mods"][0]["resources"][0])
        reject(broken)
        broken=json.loads(json.dumps(spec))
        broken["mods"][0]["resources"][0]["source_path"]="../escape.raw"
        reject(broken)
        broken=json.loads(json.dumps(spec))
        broken["mods"][0]["resources"][0]["source_path"]="PC/param/not_in_original.zip"
        reject(broken)
        broken=json.loads(json.dumps(spec))
        broken["mods"][0]["source_sha256"]="0"*64
        reject(broken)
        broken=json.loads(json.dumps(spec))
        broken["mods"].append({**broken["mods"][0],"mod_id":"another"})
        reject(broken)
        # Same source hash copied into staged source and manifest must never
        # override the bytes in the independently verified original ZIP.
        original_name=spec["mods"][0]["resources"][0]["source_path"]
        source_file=Path(spec["mods"][0]["staged_path"])/"mod"/Path(*original_name.split("/"))
        raw=source_file.read_bytes();source_file.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
        stage_manifest=Path(spec["mods"][0]["staged_path"])/"manifest.json"
        original_stage_manifest=stage_manifest.read_text()
        stage_info=json.loads(original_stage_manifest)
        for entry in stage_info["files"]:
            if entry["path"]==original_name:
                entry["sha256"]=hashlib.sha256(source_file.read_bytes()).hexdigest()
        stage_manifest.write_text(json.dumps(stage_info))
        reject(spec)
        # CLI integration on a separate newly staged source after resetting.
        source_file.write_bytes(raw)
        stage_manifest.write_text(original_stage_manifest)
        result_dir=root/"cli"
        config=root/"config.json";config.write_text(json.dumps(spec))
        command=[sys.executable,str(ROOT/"tools/assemble_pc_nsc_param_pack.py"),
                 "--spec",str(config),"--output",str(result_dir)]
        cp=subprocess.run(command,capture_output=True,text=True,check=True)
        assert "PC_NATIVE_SOURCE_PACK_STAGED 9" in cp.stdout
        assert (result_dir/"pc_native_sources.pack").read_bytes()==blob
        assert (result_dir/"manifest.json").is_file()
        positives+=1
        result={
            "status":"PASS_PC_NSC_ZIP_NATIVE_SOURCE_PACK_HOST_CPP",
            "original_main_sha256":MAIN_SHA256,
            "authentic_public_PC_source_families":9,
            "original_PC_ZIP_bytes_and_stage_crosschecked":True,
            "native_cpp_positive_pack_and_row_checks":positives,
            "negative_format_or_source_conditions_rejected":negatives,
            "authentic_installed_PC_mod_tested":False,
            "Switch_native_engine_parameter_consumer_connected":False,
            "Switch_CRI_resource_ABI_proven":False,
            "gameplay_verified":False,"full_moddingapi":False,
            "ready_for_gameplay_test":False,"emulator_tested":False}
        out.mkdir(parents=True,exist_ok=True)
        (out/"pc_native_pack_host.json").write_text(json.dumps(result,indent=2)+"\n")
        print("PC_NSC_NATIVE_PACK_HOST_PASS",positives,negatives,"NO_GAMEPLAY")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    run(a.main,a.output)
