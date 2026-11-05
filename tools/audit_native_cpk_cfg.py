#!/usr/bin/env python3
"""Inspect bounded SHA-pinned ARM64 flow with unresolved branches explicit."""
import argparse,json
from pathlib import Path
from portlib.native_cpk_cfg import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path,help="New report directory")
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_cpk_candidate_cfg.json").write_text(json.dumps(report,indent=2)+"\n")
    for name,reg in report["regions"].items():
        sample=[(i["offset"],i["mnemonic"],i["operands"]) for i in reg["decoded_reachable_instructions"]
                if i["mnemonic"] in ("ldr","str","bl","blr","b","ret")][:24]
        print("NATIVE_CFG_CANDIDATE",name,"reachable_words",reg["reachable_decoded_words"],
              "incoming_direct",reg["direct_B_BL_incoming_count"],
              "incoming_rela",reg["relative_relocation_incoming_slots"],
              "ret_or_indirect_terms",reg["within_window_return_or_indirect_terminators"],
              "calls",reg["direct_calls_found_in_reachable_code"][:25],
              "selected_instructions",sample)
    print("bounded CFG is NOT a safe hook/ABI/async/unbind/gameplay proof")


if __name__=="__main__":main()
