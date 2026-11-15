"""Source-hash + archive-hash exact TOC path provenance, no audio/gameplay."""
import argparse,hashlib,json,struct,subprocess,sys,tempfile
from pathlib import Path
from test_cpk_events import cpk
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.pc_cpk_resource_audit import audit


def sha(b):return hashlib.sha256(b).hexdigest()


def _fixed(raw,n):
    return raw+bytes(n-len(raw))


def run(out):
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);bgm=d/"bgmManagerParam.xfbin";guard=d/"guardEffectParam.xfbin"
        bgm_data=_fixed(b"STAGE_TEST\0",0x30)+_fixed(b"data/sound/test.acb\0",0x30)+struct.pack("<ii",53,0)
        guard_data=struct.pack("<II",277,1)+b"".join([
            _fixed(b"data/effect/test.nucc\0",0x30),
            _fixed(b"START_EFFECT\0",0x30),
            bytes(0x30),bytes(0x30),bytes(0x30)
        ])
        assert len(bgm_data)==0x68 and len(guard_data)==0xF8
        bgm.write_bytes(bgm_data);guard.write_bytes(guard_data)
        sources=[{"family":"bgmManagerParam","path":str(bgm),"sha256":sha(bgm_data)},
                 {"family":"guardEffectParam","path":str(guard),"sha256":sha(guard_data)}]
        first=cpk([("data/sound/test.acb",b"TEST_SOUND_PAYLOAD"),
                   ("data/effect/test.nucc",b"TEST_EFFECT_PAYLOAD"),
                   ("data/misc/unused.bin",b"UNCHANGED")])
        second=cpk([("data/sound/test.acb",b"OVERRIDE_UNRESOLVED"),
                    ("data/effect/extra.nucc",b"OPAQUE")])
        f1=d/"stock.cpk";f2=d/"mod.cpk"
        f1.write_bytes(first);f2.write_bytes(second)
        archives=[{"label":"stock_source_unverified","path":str(f1),"sha256":sha(first)},
                  {"label":"mod_candidate_unverified","path":str(f2),"sha256":sha(second)}]
        report=audit(sources,archives)
        assert report["PC_families"]==2
        assert report["PC_resource_name_candidates"]==3
        assert report["literal_case_sensitive_TOC_hit_candidates"]==2
        assert report["cross_archive_duplicate_literal_path_candidates"]==1
        match={(c["family"],c["field"]):c for c in report["candidates"]}
        assert len(match[("bgmManagerParam","stage_sound")]["literal_case_sensitive_TOC_matches"])==2
        assert len(match[("guardEffectParam","effect_path")]["literal_case_sensitive_TOC_matches"])==1
        assert match[("guardEffectParam","start_effect")]["literal_case_sensitive_TOC_matches"]==[]
        assert not report["archive_origin_is_trusted_stock_verified"]
        assert not report["archive_runtime_priority_or_winning_path_verified"]
        assert not report["native_Switch_factory_or_actor_ABI_verified"]
        assert not report["gameplay_verified"]
        assert audit(list(reversed(sources)),list(reversed(archives)))==report
        spec=d/"spec.json";spec.write_text(json.dumps({"sources":sources,"archives":archives}))
        cmd=[sys.executable,str(R/"tools/audit_pc_cpk_resource_paths.py"),
             "--spec",str(spec),"--output",str(d/"good")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((d/"good/pc_cpk_resource_paths.json").read_text())==report
        rejected=0
        def bad(f):
            nonlocal rejected
            try:f()
            except ValueError:rejected+=1
            else:raise AssertionError("Unsafe source/CPK input passed validation")
        bad(lambda:audit(sources,[dict(archives[0],sha256="0"*64)]))
        bad(lambda:audit(sources,archives+[archives[0]]))
        bad(lambda:audit([dict(sources[0],sha256="0"*64)],archives))
        bad(lambda:audit([sources[0],sources[0]],archives))
        bad(lambda:audit(sources,[dict(archives[0],extra="forbidden")]))
        bad(lambda:audit(sources,archives,require_all_nine=True))
        corrupt=cpk([("data/sound/test.acb",b"A")],header_change={"EnableFileCrc":1})
        f1.write_bytes(corrupt)
        bad(lambda:audit(sources,[dict(archives[0],sha256=sha(corrupt))]))
        assert rejected==7
        assert f2.read_bytes()==second and bgm.read_bytes()==bgm_data
    out.mkdir(parents=True,exist_ok=True)
    summary={
        "status":"PASS_SYNTHETIC_CPK_TOC_PC_RESOURCE_LITERAL_PROBE",
        "PC_source_families":2,
        "PC_names":3,
        "literal_CPK_hits":2,
        "cross_archive_duplicate_paths":1,
        "untrusted_source_failures_rejected":rejected,
        "genuine_stock_CPK_or_sound_bank_verified":False,
        "audio_or_effect_playback_verified":False,
        "native_ABI_verified":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
    (out/"pc_cpk_resource_audit_synthetic.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("PC_CPK_RESOURCE_TOC_SYNTHETIC_PASS",summary)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    run(p.parse_args().output)
