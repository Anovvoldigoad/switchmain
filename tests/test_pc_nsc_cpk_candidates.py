"""Actual candidate CPK profile encoder + source-identical PC mod archive integration."""
import argparse,copy,hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from test_cpk_events import cpk
from portlib.pc_nsc_archive_stage import stage
from portlib.pc_nsc_cpk_candidates import assemble
from portlib.cpk_profile import decode

def sha(data):return hashlib.sha256(data).hexdigest()

def run(main,out):
    original=main.read_bytes()
    assert len(original)>0
    good=0;rejected=0
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        mods=[]
        for i in range(2):
            tag="first" if i==0 else "second"
            path="data/effect/unique_01.bin" if i==0 else "data/audio/unique_02.bin"
            asset=cpk([(path,b"ORIGINAL_PC_ASSET_"+tag.encode())])
            zipfile_path=root/(tag+".nsc")
            with zipfile.ZipFile(zipfile_path,"w",zipfile.ZIP_DEFLATED) as z:
                z.writestr("Resources/CPKs/"+tag+".cpk",asset)
                z.writestr("Characters/Tobi/5tbobd1.xfbin",b"OPAQUE-PC-XFBIN-"+tag.encode())
            zipsha=sha(zipfile_path.read_bytes())
            staged=root/("stage_"+tag)
            stage(zipfile_path,zipsha,staged)
            mods.append({"mod_id":tag,"staged_path":str(staged),
                         "original_archive":str(zipfile_path),
                         "source_sha256":zipsha,
                         "cpks":[{"source_path":"Resources/CPKs/"+tag+".cpk",
                                  "runtime_path":"sim:data/moddingapi/"+tag+"/"+tag+".cpk",
                                  "priority":i+10}]})
        spec={"original_main":{"path":str(main),"sha256":sha(original)},
              "mods":mods,"reference_archives":[]}
        output=root/"candidate"
        report=assemble(spec,output);good+=1
        assert report["candidate_cpk_count"]==2
        assert report["unique_CPK_TOC_paths"]==2
        assert report["real_CRI_archive_precedence_proven"] is False
        assert report["native_fileopen_lifecycle_and_hooks_proven"] is False
        assert report["real_Uzuy_gameplay_verified"] is False
        assert report["full_moddingapi"] is False
        assert report["emulator_tested"] is False
        assert decode((output/"candidate_cpk_registration_profile.bin").read_bytes())==report["profile_rows"]
        assert json.loads((output/"candidate_manifest.json").read_text())==report
        for mod in mods:
            filename=mod["mod_id"]+".cpk"
            deployed=output/"candidate_data_root"/"data"/"moddingapi"/mod["mod_id"]/filename
            original_bytes=(Path(mod["staged_path"])/"mod"/"Resources"/"CPKs"/filename).read_bytes()
            assert deployed.read_bytes()==original_bytes
        spec_file=root/"spec.json";spec_file.write_text(json.dumps(spec))
        cli_dir=root/"candidate_cli"
        cmd=[sys.executable,str(R/"tools/assemble_pc_nsc_cpk_candidates.py"),
             "--spec",str(spec_file),"--output",str(cli_dir)]
        cli=subprocess.run(cmd,capture_output=True,text=True,check=True)
        assert "PC_NSC_CPK_CANDIDATES_STAGED 2" in cli.stdout
        assert json.loads((cli_dir/"candidate_manifest.json").read_text())==report
        good+=1
        def reject(s):
            nonlocal rejected
            dest=root/("rejected_"+str(rejected))
            try:assemble(s,dest)
            except (ValueError,FileNotFoundError,zipfile.BadZipFile):
                assert not dest.exists()
                rejected+=1
            else:raise AssertionError("Unsafe PC/CPK candidate unexpectedly accepted")
        reject(spec) if False else None
        reject(dict(spec,original_main={"path":str(main),"sha256":"0"*64}))
        wrong=copy.deepcopy(spec);wrong["mods"][0]["source_sha256"]="0"*64
        reject(wrong)
        wrong=copy.deepcopy(spec);wrong["mods"][0]["cpks"][0]["runtime_path"]="sim:data/moddingapi/second/wrong.cpk"
        reject(wrong)
        wrong=copy.deepcopy(spec);wrong["mods"][1]["cpks"][0]["priority"]=10
        reject(wrong)
        wrong=copy.deepcopy(spec);wrong["mods"][1]["mod_id"]="first"
        reject(wrong)
        wrong=copy.deepcopy(spec);wrong["mods"][0]["cpks"][0]["source_path"]="../outside.cpk"
        reject(wrong)
        wrong=copy.deepcopy(spec);wrong["mods"][0]["cpks"][0]["source_path"]="Characters/Tobi/5tbobd1.xfbin"
        reject(wrong)
        wrong=copy.deepcopy(spec);wrong["mods"][0]["cpks"][0]["source_path"]="Resources/CPKs/missing.cpk"
        reject(wrong)
        reject(dict(spec,extra=1))
        reject(dict(spec,mods=[]))
        # A real, source-pinned synthetic reference archive with a conflicting
        # TOC key is rejected without choosing runtime winner/priority.
        stock=cpk([("data/effect/unique_01.bin",b"COMPETING_STOCK_ASSET")])
        stock_path=root/"reference.cpk";stock_path.write_bytes(stock)
        wrong=copy.deepcopy(spec)
        wrong["reference_archives"]=[{"label":"reference","path":str(stock_path),"sha256":sha(stock)}]
        reject(wrong)
        wrong=copy.deepcopy(spec)
        wrong["reference_archives"]=[{"label":"reference","path":str(stock_path),"sha256":"0"*64}]
        reject(wrong)
        # Forge stage entry, keeping original ZIP intact: recompute the staged
        # manifest hash then verify original member SHA still blocks promotion.
        stage_p=Path(mods[0]["staged_path"])
        target=stage_p/"mod"/"Resources"/"CPKs"/"first.cpk"
        legit=target.read_bytes()
        target.write_bytes(legit[:-1]+bytes([legit[-1]^1]))
        report_p=stage_p/"manifest.json"
        manifest=json.loads(report_p.read_text())
        for f in manifest["files"]:
            if f["path"]=="Resources/CPKs/first.cpk":
                f["sha256"]=sha(target.read_bytes())
        report_p.write_text(json.dumps(manifest))
        reject(spec)
        assert rejected==13
        assert sha(mods[0]["source_sha256"].encode()) # not a game fingerprint
        assert (output/"candidate_cpk_registration_profile.bin").is_file()
        assert original==main.read_bytes()
    out.mkdir(parents=True,exist_ok=True)
    summary={"status":"PASS_PC_MULTI_MOD_CPK_CANDIDATE_ASSEMBLY_STATIC_ONLY",
             "positive_cases":good,"negative_cases_rejected":rejected,
             "original_main_sha256":sha(original),"case_sensitive_CPK_TOC_overlap_rejected":True,
             "staged_original_CPK_bytes_preserved":True,"synthetic_CPKs_only":True,
             "source_gameplay_tested":False,"full_moddingapi":False,
             "ready_for_gameplay_test":False,"emulator_tested":False}
    (out/"pc_nsc_multi_mod_candidate_test.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("PC_NSC_MULTI_MOD_CPK_CANDIDATE_STATIC_PASS",good,rejected,
          "NO_ABI_OR_UZUY_PROOF")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.main,a.output)
