"""Nine authentic public PC source fixtures, unified read-only manifest tests."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from portlib.pc_api_manifest import build_manifest,ALL_FAMILIES

FIXTURES={
 "susanooCondParam":("NSC_susanooCondParam.raw32.bin",
  "a0b1dabfa72634c71e601c1fb9cc938c9fb00820591e44972771aeee6c3aed7c"),
 "partnerSlotParam":("NSC_partnerSlotParam.raw32.bin",
  "f7190ee92bbcca9e157ecfc7aa497a699e32b858bb865e9012e9df40e5103055"),
 "ougiAwakeningParam":("NSC_ougiAwakeningParam.raw.bin",
  "aafe5c9d06106459ae1b56891f2cae5751596c24db3cf15898160499b7c88509"),
 "gudoBallParam":("NSC_gudoBallParam.raw.bin",
  "7516b57455c49ab9508b6fc12bc644aae797d96b5ef8253e2f809f0319df467f"),
 "charRelationParam":("NSC_charRelationParam.raw.bin",
  "80edf5c8fcb60825fad9a2ff4c1c82864b6b5656ecb7775e5d4c77a3ca47ce2a"),
 "pairSpSkillManagerParam":("NSC_pairSpSkillManagerParam.raw.bin",
  "45f753590ea2dd0a187b19baa672965dcb7ef6a7a40cca4c8dfb7d020a907d1a"),
 "bgmManagerParam":("NSC_bgmManagerParam.raw.bin",
  "37624a482fe4a7e3b110ef897337ba1013ca2ecd2fb049d41debd1e83ff2ab04"),
 "specialInteractionManager":("NSC_specialInteractionManager.raw.bin",
  "bc567cf4b536d48012d55937dc094dee1e086837fb5cde0d6925b7a345b1e367"),
 "guardEffectParam":("NSC_guardEffectParam.raw.bin",
  "f6c7b12e849f4c23a295d8c3fb968223845b53ea57ec7e8c6e3bb7de4899f958")
}


def run(out):
    assert set(FIXTURES)==ALL_FAMILIES
    entries=[]
    for family,(name,sha) in FIXTURES.items():
        path=R/"tests/fixtures/pc_source"/name
        raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==sha
        entries.append({"family":family,"path":str(path),"sha256":sha})
    a=build_manifest(entries,require_all_nine=True)
    assert a["PC_raw_family_count"]==9
    assert a["all_nine_PC_raw_formats_supplied"]
    assert a["missing_PC_families"]==[]
    assert not a["native_switch_170_integration_verified"]
    assert not a["gameplay_verified"]
    assert a["unresolved_audio_effect_name_count"]>0
    assert all(not v["switch_native_reader_integrated"]
               for v in a["source_families"].values())
    reordered=build_manifest(list(reversed(entries)),require_all_nine=True)
    assert a==reordered
    subset=build_manifest([entries[0]])
    assert subset["PC_raw_family_count"]==1
    assert not subset["all_nine_PC_raw_formats_supplied"]
    assert len(subset["missing_PC_families"])==8
    rejected=0
    def invalid(f):
        nonlocal rejected
        try:f()
        except ValueError:rejected+=1
        else:raise AssertionError("Unsafe PC API spec accepted")
    invalid(lambda:build_manifest(entries[:8],require_all_nine=True))
    invalid(lambda:build_manifest(entries+[entries[0]]))
    invalid(lambda:build_manifest([entries[0],entries[0]]))
    invalid(lambda:build_manifest([dict(entries[0],sha256="0"*64)]))
    invalid(lambda:build_manifest([dict(entries[0],family="unknown")]))
    invalid(lambda:build_manifest([dict(entries[0],extra="unsafe")]))
    invalid(lambda:build_manifest([]))
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp)
        spec=d/"spec.json";spec.write_text(json.dumps({"sources":entries}))
        cmd=[sys.executable,str(R/"tools/audit_pc_api_manifest.py"),
             "--spec",str(spec),"--require-all-nine","--output",str(d/"good")]
        subprocess.run(cmd,check=True,capture_output=True)
        parsed=json.loads((d/"good/pc_api_manifest.json").read_text())
        assert parsed==a
        spec.write_text(json.dumps({"sources":entries+[entries[0]]}))
        cmd[-1]=str(d/"bad")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (d/"bad").exists()
    out.mkdir(parents=True,exist_ok=True)
    summary={
        "status":"PASS_NINE_REAL_PUBLIC_PC_RAW_FIXTURES_MANIFEST_ONLY",
        "families":9,
        "unresolved_resource_names":a["unresolved_audio_effect_name_count"],
        "manifest_identity_sha256":a["manifest_identity_sha256"],
        "invalid_inputs_rejected":rejected,
        "native_switch_170_integration_verified":False,
        "real_PC_mod_pack_sample_tested":False,
        "gameplay_verified":False,"full_moddingapi":False
    }
    (out/"pc_api_manifest_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("ALL_NINE_PC_SOURCE_MANIFEST_PASS",summary)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    run(p.parse_args().output)
