"""SHA-pinned original native X8 indirect dispatch owner-source evidence."""
import argparse,json
from pathlib import Path
from portlib.native_fileopen_dispatch_objects import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"native_fileopen_dispatch_objects.json").write_text(
        json.dumps(report,indent=2)+"\n")
    for item in report["dispatch_origins"]:
        writers=item["X8_nearest_syntactic_original_writers"]["possible_immediate_reaching_writers"]
        print("NATIVE_FILEOPEN_DISPATCH_OBJECT",item["callee_callsite"],
              item["eight_callee_direct_target"],
              item["original_br_site"],"X8_FIELD",hex(item["indirect_method_field_offset"]),
              "X8_WRITERS",[(w["at"],w["instruction"]) for w in writers])
        for word in item["original_instruction_transcript"][-12:]:
            print(" DISPATCH_NATIVE_A64",word["at"],word["word_le"],word["instruction"])
    print("NATIVE_FILEOPEN_DISPATCH_OBJECTS_PASS",len(report["dispatch_origins"]),
          "NO_ACTUAL_ABI_OR_UZUY")
if __name__=="__main__":
    main()
