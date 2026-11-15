"""Read-only pinned FileOpen branch dependency report."""
import argparse
import json
from pathlib import Path
from portlib.native_fileopen_branch_dependencies import inspect

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--main", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    result=inspect(a.main.read_bytes())
    a.output.mkdir(parents=True,exist_ok=True)
    path=a.output/"native_fileopen_branch_dependencies.json"
    path.write_text(json.dumps(result,indent=2)+"\n")
    print("FILEOPEN_BRANCH_DEPENDENCIES_STATIC_PASS",
          "branches",len(result["conditional_branch_edge_census"]),
          "calls",len(result["reachable_external_callsite_census"]),
          "NO_CRI_OR_GAMEPLAY")
if __name__=="__main__":main()
