"""Read-only public original PC manager512 authentication for Termux."""
import argparse,json
from pathlib import Path
from portlib.pc_public_baseline import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manager512",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.manager512.is_symlink() or not a.manager512.is_file():
        raise ValueError("Expected regular non-symlink public manager512 input")
    r=inspect(a.manager512.read_bytes())
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"pc_public_baseline.json").write_text(json.dumps(r,indent=2)+"\n")
    print("PUBLIC_ORIGINAL_PC_MANAGER512_AUTHENTIC",r["raw_sha256"],
          r["original_git_blob_sha1"],"NOT_517_OR_SWITCH_CPK")
if __name__=="__main__":main()
