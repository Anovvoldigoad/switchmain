#!/usr/bin/env python3
"""Static use-site scan of pinned CPK pointer-table data slots; no hooks."""
import argparse,json
from pathlib import Path
from portlib.native_cpk_pointer_use import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"native_cpk_pointer_use.json").write_text(json.dumps(report,indent=2)+"\n")
    for area in report["regions"]:
        print("CPK_DATA_SLOT_USE",area["focus_slot"],
              "nearby_relocs",area["nearby_RELATIVE_slot_count"],
              "uses",area["data_address_use_candidate_count"],
              "exact_adjacent",area["exact_slot_adjacent_or_ADR_witness_count"],
              "kind_counts",area["use_instruction_kind_counts"],
              "sample",area["data_address_use_samples"][:14])
    print("Vtable ownership / ABI / async / unbind / gameplay NOT PROVEN")


if __name__=="__main__":main()
