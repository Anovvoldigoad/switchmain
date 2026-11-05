"""Original native FileOpen tail 8 callee body/PLT and W0 evidence CLI."""
import argparse,json
from pathlib import Path
from portlib.native_fileopen_tail_callees import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=inspect(args.main.read_bytes())
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"native_fileopen_tail_callees.json").write_text(
        json.dumps(report,indent=2)+"\n")
    for record in report["per_callsite_original_target_and_import_evidence"]:
        call=record["site"]
        imp=record["plt_import"]
        print("FILEOPEN_TAIL_NATIVE_CALL",call,record["word_le"],
              record["instruction"],"->",record["direct_target"],
              "import",imp["symbol"]["name"] if imp else None)
        for item in record["target_first_words"][:10]:
            print(" CALL_TARGET_ORIGINAL_A64",item["at"],item["word_le"],
                  item["instruction"])
        cfg=record.get("bounded_target_cfg")
        if cfg:
            print(" BOUNDED_CALLEE_CFG",call,"reached",cfg["visited"],
                  "local_ret",cfg["return_sites"],
                  "escape",cfg["other_exits"][:8])
    print("FILEOPEN_TAIL_RETURN_W0",report["original_local_return_register_provenance"])
    print("FILEOPEN_TAIL_EIGHT_CALLEES_STATIC_PASS",report["native_callsite_count"],
          "NO_REAL_CRI_OR_UZUY")
if __name__=="__main__":
    main()
