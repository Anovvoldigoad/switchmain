"""True byte-grounded intake wrapper, synthetic CPK regression, no stock claim."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from native_condition_fixture import baseline_from_main,pc_record
from test_condition_companion import fixture
from test_cpk_events import cpk
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/"tools"))
from portlib.condition_bundle import ENTRY
from portlib.real_condition_intake import inspect,discover_manager


def digest(data):return hashlib.sha256(data).hexdigest()


def run(main,out):
    baseline,_=baseline_from_main(main)
    names=[baseline[i:i+48].split(b'\0',1)[0].decode()
           for i in range(0,len(baseline),112)]
    suffix=[f"TEST_NEW_{n}" for n in range(5)]
    manager=baseline+b"".join(pc_record(x) for x in suffix)
    stock_raw=fixture(names)
    candidate_raw=fixture(names+suffix)
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);source=root/"src";source.mkdir()
        sf=source/"stock.cpk";cf=source/"candidate.cpk"
        mf=source/"conditionprmManager517.xfbin"
        a=cpk([(ENTRY,stock_raw),("data/test/stock",b"A")])
        b=cpk([(ENTRY,candidate_raw),("data/test/candidate",b"B")])
        sf.write_bytes(a);cf.write_bytes(b);mf.write_bytes(manager)
        report=inspect(mf,sf,cf,digest(manager),digest(a),digest(b))
        assert report["status"]=="REAL_INPUT_BYTES_COMPARED_PROVENANCE_UNAUTHENTICATED"
        assert report["audit"]["stock_rows"]==512
        assert report["audit"]["candidate_rows"]==517
        assert report["audit"]["native_values_preserved"]
        assert len(report["audit"]["appended_record_hashes"])==5
        assert not report["stock_origin_as_unmodified_game_verified"]
        assert not report["gameplay_verified"]
        assert all(report["external_expected_sha256_fields_present"].values())
        assert discover_manager(source)==mf
        cmd=[sys.executable,str(R/"tools/audit_real_condition_intake.py"),
             "--discover-manager-root",str(source),
             "--stock-cpk",str(sf),"--candidate-cpk",str(cf),
             "--output",str(root/"ok")]
        subprocess.run(cmd,check=True,capture_output=True)
        result=json.loads((root/"ok/real_condition_intake.json").read_text())
        assert result["pc_manager"]["sha256"]==digest(manager)
        assert result["stock_cpk"]["sha256"]==digest(a)
        assert not result["external_expected_sha256_fields_present"]["stock"]
        rejects=0
        def bad(call):
            nonlocal rejects
            try:call()
            except ValueError:rejects+=1
            else:raise AssertionError("bad input unexpectedly accepted")
        bad(lambda:inspect(mf,sf,cf,digest(manager),"0"*64,digest(b)))
        bad(lambda:inspect(mf,sf,cf,"0"*64,digest(a),digest(b)))
        bad(lambda:inspect(mf,sf,sf))
        wrong=source/"public_template_512";wrong.write_bytes(baseline)
        bad(lambda:inspect(wrong,sf,cf))
        # Discovery must not select public baseline.
        mf.unlink()
        bad(lambda:discover_manager(source))
        mf.write_bytes(manager)
        dupe=source/"conditionprmManager_alt.xfbin";dupe.write_bytes(manager)
        bad(lambda:discover_manager(source))
        dupe.unlink()
        assert discover_manager(source)==mf
        try:
            link=source/"conditionprmManager_link.xfbin";link.symlink_to(mf)
            assert discover_manager(source)==mf
            bad(lambda:inspect(link,sf,cf))
        except (OSError,NotImplementedError):
            pass
        assert sf.read_bytes()==a and cf.read_bytes()==b
        assert mf.read_bytes()==manager
        cmd[-1]=str(root/"second")
        cmd+=["--expected-stock-sha256","0"*64]
        assert subprocess.run(cmd,capture_output=True).returncode
        assert not (root/"second").exists()
        assert rejects>=6
    out.mkdir(parents=True,exist_ok=True)
    result={"status":"PASS_SYNTHETIC_517_INPUT_AUDIT",
            "manager_records":517,"stock_records":512,"candidate_records":517,
            "source_file_hashes_explicit":True,
            "actual_manager517_attached":False,
            "actual_unmodified_switch_stock_verified":False,
            "archive_priority_verified":False,"real_Uzuy_tested":False,
            "failure_cases_rejected":rejects,
            "gameplay_verified":False,"full_moddingapi":False}
    (out/"real_condition_intake_synthetic.json").write_text(json.dumps(result,indent=2)+"\n")
    print("REAL_INTAKE_SYNTHETIC_517",result,"NOT_REAL_STOCK_PROOF")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--main",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args();run(a.main,a.output)
