"""Synthetic CFG path joins and SHA-pinned original FileLoad evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from portlib.native_fileload_sp_cfg import trace
from portlib.native_fileload_corridor_cfg import ENTRY, END
from portlib.native_cpk_graph import MAIN_SHA256
from portlib.nso_profile import segments

def word(x):
    return x.to_bytes(4,"little")
def run(main,out):
    # SUB SP,#16; STR X1,[SP,#8]; RET: entry-relative -8.
    linear=b"".join(map(word,[0xd10043ff,0xf90007e1,0xd65f03c0]))
    r=trace(linear,0x1000)
    assert len(r["accesses"])==1
    assert r["accesses"][0]["entry_sp_relative_offsets"]==[-8]
    # CBZ X0,+12 bypasses ADD SP,#16, creating two distinct SP offsets.
    fork=b"".join(map(word,[0xd10043ff,0xb4000060,0x910043ff,
                           0x14000002,0xd503201f,0xf90007e1,0xd65f03c0]))
    # At 0x2004 CBZ +12 goes to 0x2010; branch at 0x200c goes to 0x2014.
    # Both paths meet at 0x2014 after the NOP.
    r=trace(fork,0x2000)
    assert len(r["accesses"])==1
    assert r["accesses"][0]["path_ambiguous"]
    assert r["accesses"][0]["observed_sp_deltas"]==[-16,0]
    # A call is a hard evidence barrier, not assumed to preserve SP.
    call=b"".join(map(word,[0xd10043ff,0x94000002,0xf90007e1,0xd65f03c0]))
    r=trace(call,0x3000)
    assert r["call_barriers"]==["0x3004"]
    assert r["accesses"][0]["unknown_path"]
    for bad in (linear[:-1],):
        try: trace(bad,0x1000)
        except ValueError: pass
        else: raise AssertionError("Accepted partial ARM64 word")
    try: trace(linear,0x1000,max_states=1)
    except ValueError: pass
    else: raise AssertionError("Accepted state-budget overflow")
    raw=main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==MAIN_SHA256
    va,text,_=segments(raw)[0]
    assert va==0 and END<=len(text)
    window=text[ENTRY:END]
    report=trace(window,ENTRY)
    report["original_main_sha256"]=MAIN_SHA256
    report["window_sha256"]=hashlib.sha256(window).hexdigest()
    assert not report["consumer_abi_proven"] and not report["stack_ownership_proven"]
    out.mkdir(parents=True,exist_ok=True)
    (out/"native_fileload_sp_cfg.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PINNED_FILELOAD_SP_CFG_PASS",report["reachable_states"],len(report["accesses"]),"NO_CONSUMER_ABI")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    run(a.main,a.output)
