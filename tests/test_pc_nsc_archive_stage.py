"""Safe real NSC Mod Manager 2.1.2.1 .nsc ZIP import regression/negatives."""
import argparse,hashlib,json,stat,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.pc_nsc_archive_stage import stage

def _zip(where,entries,compress=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(where,"w",compression=compress) as z:
        for name,value in entries:
            if isinstance(value,zipfile.ZipInfo):
                z.writestr(value,b"relative-file-target")
            else:
                z.writestr(name,value)
    return hashlib.sha256(where.read_bytes()).hexdigest()

def run(out):
    count=0
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); source=root/"pc_mod.nsc"
        digest=_zip(source,[
            ("Characters/Tobi/model.xfbin",b"xfbin-opaque"),
            ("Resources/CPKs/custom.cpk",b"CPK not authenticated"),
            ("ModInfo.ini",b"[ModManager]\nVersion=1.0\n"),
            ("Resources/audio/jp_voice.nus3bank",b"audio-opaque")])
        stagepath=root/"stage"
        result=stage(source,digest,stagepath)
        assert result["extracted_file_count"]==4
        assert result["total_extracted_bytes"]==sum(
            x["source_member_size"] for x in result["files"])
        assert result["status"]=="STAGED_OFFLINE_NSC_PC_ZIP_INPUT_NOT_SWITCH_MOD_RELEASE"
        assert (stagepath/"mod/Resources/CPKs/custom.cpk").read_bytes()==b"CPK not authenticated"
        assert result["new_native_hook_added"] is False
        assert result["model_audio_SFX_JP_voice_runtime_verified"] is False
        assert result["full_moddingapi"] is False
        assert json.loads((stagepath/"manifest.json").read_text())==result
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
        def invalid(entries,rename=None,sha=None):
            nonlocal count
            path=root/(rename or "pc_mod.nsc")
            val=_zip(path,entries)
            output=root/("bad_"+str(count))
            try:stage(path,sha if sha is not None else val,output)
            except (ValueError,zipfile.BadZipFile,RuntimeError,NotImplementedError):
                count+=1
                assert not output.exists()
            else:
                raise AssertionError("Unsafe ZIP archive accepted")
        invalid([("../escape.xfbin",b"x")])
        invalid([("C:/absolute.xfbin",b"x")])
        invalid([("dir\\escape.cpk",b"x")])
        invalid([("Characters/../escape.xfbin",b"x")])
        invalid([("a/file.cpk",b"first"),("A/File.CPK",b"second")])
        invalid([("parent",b"file"),("parent/child.xfbin",b"nested")])
        symlink=zipfile.ZipInfo("link")
        symlink.create_system=3
        symlink.external_attr=(stat.S_IFLNK | 0o777)<<16
        invalid([("link",symlink)])
        invalid([("a.cpk",b"content")],sha="0"*64)
        invalid([("a.cpk",b"content")],rename="pc_mod.nus4")
        invalid([("a.cpk",b"content")],rename="pc_mod.nsc",sha="not-an-sha")
        invalid([("a.cpk",b"0"*(2*1024*1024))])
        # CLI parity on a distinct verified archive (new output).
        source=root/"pc_mod.nsc"
        digest=_zip(source,[("Resources/CPKs/test.cpk",b"Cpk byte source")])
        p=root/"out_cli"
        command=[sys.executable,str(ROOT/"tools/stage_pc_nsc_mod.py"),
                 "--archive",str(source),"--sha256",digest,"--output",str(p)]
        cp=subprocess.run(command,capture_output=True,text=True,check=True)
        assert "PC_MOD_ARCHIVE_STAGED_ONLY" in cp.stdout
        assert (p/"mod/Resources/CPKs/test.cpk").read_bytes()==b"Cpk byte source"
        assert (p/"manifest.json").is_file()
        try:stage(source,digest,p)
        except ValueError:count+=1
        else:raise AssertionError("Existing output was overwritten")
    out.mkdir(parents=True,exist_ok=True)
    report={"status":"PASS_SAFE_PC_NSC_SOURCE_ZIP_STAGING_ONLY",
            "malicious_or_wrong_input_rejected":count,
            "real_PC_mod_binary_not_tested":True,
            "Switch_XFBIN_CPK_audio_model_ABI_verified":False,
            "gameplay_verified":False,"full_moddingapi":False}
    (out/"pc_nsc_archive_stage_summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PC_NSC_MOD_STAGE_STATIC_PASS",count,"NO_GAMEPLAY_OR_SWITCH_CONVERSION")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    run(p.parse_args().output)
