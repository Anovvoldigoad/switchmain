"""Produce SHA-pinned original FileOpen callee/source evidence, read-only."""
import argparse
import json
from pathlib import Path
from portlib.native_fileopen_callees import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=inspect(args.main.read_bytes())
    args.output.mkdir(parents=True,exist_ok=True)
    path=args.output/"native_fileopen_callees.json"
    path.write_text(json.dumps(result,indent=2)+"\n")
    for call in result["original_callsite_target_windows"]:
        src=call["original_target_evidence"]
        print("ORIGINAL_FILEOPEN_NATIVE_CALL",
              src["at"],src["word_le"],src["instruction"],
              "target",src["direct_original_target"],
              "bounded_return_sites",
              src.get("bounded_callee_cfg",{}).get("return_sites",[]),
              "bounded_exits",
              src.get("bounded_callee_cfg",{}).get("other_exits",[])[:5])
        for w in src.get("target_first_words",[])[:10]:
            print(" ORIGINAL_CALLEE_WORD",w["at"],w["word_le"],w["instruction"])
    for branch in result["branch_sites_with_source_producers"]:
        source=branch["original_machine_condition_source"]
        print("ORIGINAL_FILEOPEN_CONDITION",
              branch["at"],branch["word_le"],branch["instruction"],
              "source",source["consulted_register"],
              "writers",[(x["at"],x["instruction"]) for x in
                         source["possible_immediate_reaching_writers"]],
              "unresolved",len(source["unresolved_entry_or_bounded_paths"]))
    print("FILEOPEN_CALLEE_SOURCE_STATIC_PASS",
          result["original_condition_site_count"],
          result["original_callsite_count"],
          "NO_CRI_ABI_NO_GAMEPLAY")
if __name__=="__main__":
    main()
