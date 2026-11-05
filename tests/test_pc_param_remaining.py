"""Authentic pinned PC manager raw fixture format, malformed inputs, CLI SHA guard."""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.pc_param_remaining import inspect, SOURCE


def sha(buf):
    return hashlib.sha256(buf).hexdigest()


FIXTURES={
    "pairSpSkillManagerParam":("NSC_pairSpSkillManagerParam.raw.bin",
       "a5505c2fee7d48fc13f96e69873151502d51a082",
       "45f753590ea2dd0a187b19baa672965dcb7ef6a7a40cca4c8dfb7d020a907d1a",1320,55),
    "bgmManagerParam":("NSC_bgmManagerParam.raw.bin",
       "b2b5439891eb6fc9ab89d3839be3e344df7cf18d",
       "37624a482fe4a7e3b110ef897337ba1013ca2ecd2fb049d41debd1e83ff2ab04",104,1),
    "specialInteractionManager":("NSC_specialInteractionManager.raw.bin",
       "07a5c0691ddf57dfa8d40177948b8c40ea9e27ae",
       "bc567cf4b536d48012d55937dc094dee1e086837fb5cde0d6925b7a345b1e367",200,4),
    "guardEffectParam":("NSC_guardEffectParam.raw.bin",
       "cad85b19e411c800ce8ad930f622c2fb7b9fc42b",
       "f6c7b12e849f4c23a295d8c3fb968223845b53ea57ec7e8c6e3bb7de4899f958",496,2),
}


def run(out):
    good={}
    originals={}
    for family,(name,blob,expected,length,rows) in FIXTURES.items():
        raw=(ROOT/"tests/fixtures/pc_source"/name).read_bytes()
        assert len(raw)==length
        got_blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        assert got_blob==blob and sha(raw)==expected
        result=inspect(raw,family,expected)
        assert result["record_count"]==rows
        assert not result["native_Switch_loader_integrated"]
        assert not result["gameplay_verified"]
        assert result["input_is_PC_raw_payload_not_NUCC_XFBIN"]
        if family=="pairSpSkillManagerParam":
            assert result["records"][0]["name"]
            assert result["effective_pc_payload_bytes"]==1320
        if family=="bgmManagerParam":
            assert result["records"][0]["stage_name"]=="STAGE_TEST"
            assert result["native_crc32_and_bgm_function_ownership_unverified"]
        if family=="specialInteractionManager":
            assert result["records"][0]["main_char_id_i32"]!=0
        if family=="guardEffectParam":
            assert "effect_path" in result["records"][0]
        good[family]={"sha256":expected,"source_git_blob":blob,
                      "rows":rows,"length":length}
        originals[family]=raw
        print("PC_FOUR_PUBLIC_FIXTURE",family,"SHA256",expected,
              "GitBlob",blob,"rows",rows,"Switch_native=UNVERIFIED")
    pair=originals["pairSpSkillManagerParam"]
    plus=inspect(pair+b"\x7f","pairSpSkillManagerParam",sha(pair+b"\x7f"))
    assert plus["record_count"]==55 and plus["trailing_byte_ignored_by_pc_source"]==0x7f
    # Strings are fixed bytes, not magic XFBIN or UTF-8; retain Latin-1 bytes.
    synthetic_bgm=(b"X"*48)+(b"\xff"*48)+struct.pack("<ii",-123,99)
    bg=inspect(synthetic_bgm,"bgmManagerParam",sha(synthetic_bgm))
    assert bg["records"][0]["stage_name"]=="X"*48
    assert bg["records"][0]["stage_sound"]=="ÿ"*48
    assert bg["records"][0]["bgm_id_i32"]==-123
    zero_interaction=struct.pack("<iiiiii",1,0,3,0,17,0)
    zz=inspect(zero_interaction,"specialInteractionManager",sha(zero_interaction))
    assert zz["records"][0]["pc_source_skips_zero_main_char"]
    assert zz["records"][0]["nonzero_trigger_ids_i32"]==[17]
    guard=struct.pack("<II",0xFFFFFFFF,2)+bytes(5*0x30)
    g=inspect(guard,"guardEffectParam",sha(guard))
    assert g["records"][0]["character_id_u32"]==0xffffffff
    assert g["records"][0]["mode_u32"]==2
    reject=[
        ("bgmManagerParam",b"",sha(b"")),
        ("bgmManagerParam",b"\0"*103,sha(b"\0"*103)),
        ("bgmManagerParam",originals["bgmManagerParam"],"0"*64),
        ("pairSpSkillManagerParam",pair+b"\x11\x22",sha(pair+b"\x11\x22")),
        ("pairSpSkillManagerParam",pair,sha(pair).upper()),
        ("specialInteractionManager",b"\0"*3,sha(b"\0"*3)),
        ("specialInteractionManager",struct.pack("<i",-1),sha(struct.pack("<i",-1))),
        ("specialInteractionManager",struct.pack("<i",100000),sha(struct.pack("<i",100000))),
        ("specialInteractionManager",struct.pack("<iii",1,3,-1),sha(struct.pack("<iii",1,3,-1))),
        ("specialInteractionManager",struct.pack("<iii",1,3,10),sha(struct.pack("<iii",1,3,10))),
        ("specialInteractionManager",struct.pack("<i",0)+b"\0",sha(struct.pack("<i",0)+b"\0")),
        ("guardEffectParam",b"\0"*247,sha(b"\0"*247)),
        ("guardEffectParam",b"\0"*249,sha(b"\0"*249)),
        ("bogus",pair,sha(pair)),
    ]
    count=0
    for family,raw,digest in reject:
        try:
            inspect(raw,family,digest)
        except ValueError:
            count+=1
        else:
            raise AssertionError("Invalid PC format accepted: "+family)
    assert count==len(reject)
    with tempfile.TemporaryDirectory() as t:
        d=Path(t);src=d/"real";src.write_bytes(pair)
        cmd=[sys.executable,str(ROOT/"tools/audit_pc_param_remaining.py"),
             "--family","pairSpSkillManagerParam",
             "--input",str(src),"--expected-sha256",sha(pair),
             "--output",str(d/"good")]
        subprocess.run(cmd,capture_output=True,check=True)
        parsed=json.loads((d/"good/pc_remaining_parameter_audit.json").read_text())
        assert parsed==inspect(pair,"pairSpSkillManagerParam",sha(pair))
        bad=cmd[:]
        bad[bad.index("--expected-sha256")+1]="0"*64
        bad[bad.index("--output")+1]=str(d/"reject")
        assert subprocess.run(bad,capture_output=True).returncode
        assert not (d/"reject").exists()
        assert src.read_bytes()==pair
    for family,raw in originals.items():
        assert (ROOT/"tests/fixtures/pc_source"/FIXTURES[family][0]).read_bytes()==raw
    out.mkdir(parents=True,exist_ok=True)
    report={"status":"PASS_4_REAL_PUBLIC_PC_RAW_FIXTURES_ONLY",
            "source_upstream":"TheLeonX/UltimateStormAPI@a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc",
            "template_upstream":"TheLeonX/NSC-ModManager@276116ebf5ba398a867793cb02ee6c33c0927645",
            "families":good,"invalid_cases_rejected":count,
            "PC_loader_behaviors_not_Switch_calls":True,
            "original_inputs_unchanged":True,
            "native_Switch_hooks_installed":False,
            "gameplay_verified":False,"full_moddingapi":False}
    (out/"pc_param_remaining.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS_PC_FOUR_REAL_TEMPLATES",len(good),
          "malformed_rejected",count,"No native Switch runtime proof")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    run(p.parse_args().output)
