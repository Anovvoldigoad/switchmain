"""Regression: release booleans cannot be inferred from native/static CI."""
import argparse,copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from portlib.release_flag_guard import validate
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--status",type=Path,required=True)
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    status=json.loads(a.status.read_text())
    checkpoint=json.loads(a.checkpoint.read_text())
    report=validate(status,checkpoint)
    rejected=0
    def reject(s,c):
        nonlocal rejected
        try:validate(s,c)
        except ValueError:rejected+=1
        else:raise AssertionError("Unsafe release flag accepted")
    for flag in ("full_moddingapi","ready_for_gameplay_test","emulator_tested"):
        for value in (True,0,None,"false"):
            x=copy.deepcopy(status);x[flag]=value
            reject(x,checkpoint)
            y=copy.deepcopy(checkpoint);y["port_status"][flag]=value
            reject(status,y)
    x=copy.deepcopy(status);x.pop("stage")
    reject(x,checkpoint)
    y=copy.deepcopy(checkpoint);y["port_status"]["stage"]="GAMEPLAY_PASS"
    reject(status,y)
    a.output.mkdir(parents=True,exist_ok=True)
    report["negative_invalid_statuses_rejected"]=rejected
    (a.output/"release_flag_guard.json").write_text(json.dumps(report,indent=2)+"\n")
    print("RELEASE_FLAGS_FALSE_STATIC_CI_GUARD_PASS",rejected,"NO_UZUY_PROOF")
if __name__=="__main__":main()
