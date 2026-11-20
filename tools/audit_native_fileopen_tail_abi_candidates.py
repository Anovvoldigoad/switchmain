"""Print original ARM64 FileOpen tail argument/BR-writer candidates."""
import argparse,json
from pathlib import Path
from portlib.native_fileopen_tail_abi_candidates import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"native_fileopen_tail_abi_candidates.json").write_text(
        json.dumps(result,indent=2)+"\n")
    for record in result["callsite_provenance"]:
        print("FILEOPEN_ORIGINAL_ARG_CALL",record["site"],
              record["original_instruction"],"to",record["callee_target"])
        for reg,row in record["source_tail_implicit_argument_register_writers"].items():
            print(" ORIGINAL_CALL_ARG",record["site"],reg,
                  [(x["at"],x["instruction"]) for x in row["possible_immediate_reaching_writers"]],
                  "unresolved",len(row["unresolved_entry_or_bounded_paths"]))
        for item in record.get("original_machine_word_sample",[]):
            print(" ORIGINAL_A64_CALLEE_WORD",record["site"],
                  item["at"],item["word_le"],item["instruction"])
        for item in record.get("native_indirect_br_register_sources",[]):
            print(" ORIGINAL_INDIRECT_BR_WRITER",record["site"],item)
    print("FILEOPEN_ORIGINAL_ARG_BR_STATIC_PASS",len(result["callsite_provenance"]),
          "NO_ORIGINAL_RUNTIME_OR_SAFE_HOOK_PROOF")
if __name__=="__main__":main()
