"""Byte-proof correction of old wrong FileLoad offset, not a replacement hook."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.native_fileload_corrected_entry import inspect,MAIN_SHA256,NEW_CANDIDATE,RECORDED_PROLOGUE


def run(main,out):
    raw=main.read_bytes()
    report=inspect(raw)
    assert report["main_sha256"]==MAIN_SHA256
    assert report["prologue_candidate_verified"]==f"0x{NEW_CANDIDATE:x}"
    assert report["source_prologue_word_count"]==len(RECORDED_PROLOGUE)
    assert report["prologue_words_match_original_main"]
    assert report["offset_discrepancy_bytes"]==0x100000
    assert report["legacy_actual"]=={"kind":"BL","target":"0xfff6a0"}
    assert report["native_file_open_edge"]["target"]=="0x1170fb0"
    assert all(x["mnemonic"]!="UNPARSED_A64"
               for x in report["nearby_instruction_window"]["words"][:8])
    assert not report["AAPCS64_argument_semantics_verified"]
    assert not report["legacy_hook_was_relocated_or_enabled"]
    assert not report["gameplay_verified"]
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);src=d/"main";src.write_bytes(raw)
        cmd=[sys.executable,str(R/"tools/audit_native_fileload_corrected_entry.py"),
             "--main",str(src),"--output",str(d/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        assert json.loads((d/"ok/native_fileload_corrected_entry.json").read_text())==report
        modified=bytearray(raw);modified[255]^=1;src.write_bytes(modified)
        cmd[-1]=str(d/"reject")
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (d/"reject").exists()
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_corrected_entry.json").write_text(json.dumps(report,indent=2)+"\n")
    print("FILELOAD_CORRECTED_PROLOGUE_PROOF",report["prologue_candidate_verified"],
          "caller",report["commented_inbound_site"],
          "fileopen",report["native_file_open_edge"],
          "uncertain_failure_word_520",report["commented_failure_locations_words"]["0x116f520"],
          "uncertain_failure_word_5c0",report["commented_failure_locations_words"]["0x116f5c0"])
    for word in report["nearby_instruction_window"]["words"]:
        at=int(word["at"],16)
        if 0x116F500<=at<=0x116F540 or 0x116F5A0<=at<=0x116F5E0:
            print("CORRECTED_FILELOAD_MACHINE_WORD",word["at"],word["mnemonic"],word["operands"])
    print("NO INTEGRATION/HOOK/GAMEPLAY CLAIM")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();run(a.main,a.output)
