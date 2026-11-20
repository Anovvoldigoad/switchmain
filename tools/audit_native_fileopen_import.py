"""Audit exact original FileOpen imported function identity at PLT/GOT."""
import argparse,json
from pathlib import Path
from portlib.native_fileopen_import import inspect
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"native_fileopen_import.json").write_text(json.dumps(r,indent=2)+"\n")
    print("ORIGINAL_FILEOPEN_PLT_IMPORT",r["fileopen_callsite"],
          r["plt_thunk"],r["got_slot"],
          [(x["type_name"],x["original_dynamic_symbol"].get("name"))
           for x in r["original_dynamic_relocations_to_slot"]],
          "NOT_CRI_ABI_OR_GAMEPLAY")
if __name__=="__main__":main()
