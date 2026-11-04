"""Actual archive/profile binding, explicit event conversion and failure cases."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from native_condition_fixture import baseline_from_main,pc_record
from test_condition_companion import fixture as condition_fixture
from test_cpk_events import cpk
from test_prm_marker import fixture as prm_fixture,event
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.condition_bundle import *
from portlib.prm_events import records


def run(main,output,module=None):
    baseline,_=baseline_from_main(main)
    names=[baseline[i:i+48].split(b'\0')[0].decode() for i in range(0,len(baseline),112)]
    manager=baseline+pc_record('TEST_A')+pc_record('TEST_B')
    raw=condition_fixture(names+['TEST_A','TEST_B']);prm=prm_fixture([event(3),event(0),event(14)])
    path='data/spc/testprm.bin.xfbin';opaque='data/other/keep'
    payloads=[(ENTRY,raw),(path,prm),(opaque,bytes(range(256)))]
    archive=cpk(payloads);runtime='sim:data/moddingapi/fixture/conditions.cpk'
    result,profile,registration,report=compile_bundle(manager,archive,sha(archive),runtime,42,[path])
    table=cpk_events.entries(archive)
    assert cpk_events.entries(result)==table
    expected={table[path]['offset']+r['offset']+i for r in records(prm) if r['event']==236 and r['function'] in (0,2) for i in (42,43)}
    assert {i for i,(a,b) in enumerate(zip(archive,result)) if a!=b}==expected
    assert report['companion']['ordinal_names_verified']==514
    assert cpk_profile.decode(registration)==[{'path':runtime,'priority':42}]
    assert [r['name'] for r in condition_profile.decode(profile)]==['TEST_A','TEST_B']
    assert compile_bundle(manager,result,sha(result),runtime,42,[path])[0]==result
    assert compile_bundle(manager,archive,sha(archive),runtime,42,[])[0]==archive
    malformed=[cpk([(path,prm)]),cpk([(ENTRY,condition_fixture(names)),(path,prm)]),
               cpk([(ENTRY,condition_fixture(names+['TEST_B','TEST_A'])),(path,prm)]),
               cpk(payloads,lambda rows:rows[0].update(ExtractSize=len(raw)+1)),archive[:-20]]
    rejected=0
    for b in malformed:
        try:compile_bundle(manager,b,sha(b),runtime,42,[path])
        except ValueError:rejected+=1
        else:raise AssertionError('malformed archive accepted')
    for h,p,priority,paths in [('0'*64,runtime,42,[path]),(sha(archive),'sim:data/moddingapi/../bad.cpk',42,[]),
            (sha(archive),runtime,-1,[]),(sha(archive),runtime,42,[ENTRY]),
            (sha(archive),runtime,42,['data/spc/missing']),(sha(archive),runtime,42,[path,path])]:
        try:compile_bundle(manager,archive,h,p,priority,paths)
        except ValueError:rejected+=1
        else:raise AssertionError('invalid arguments accepted')
    module_checks=False
    if module:
        original=module.read_bytes();built,info=configure_module(original,sha(original),profile,registration)
        reverse,_=cpk_profile.configure(original,registration,sha(original))
        reverse,_=condition_profile.configure(reverse,profile,sha(reverse))
        assert built==reverse
        before=nso_profile.segments(original);after=nso_profile.segments(built)
        assert before[:2]==after[:2]
        allowed=set()
        for magic,size in [(condition_profile.MAGIC,condition_profile.PROFILE_SIZE),(cpk_profile.MAGIC,cpk_profile.PROFILE_SIZE)]:
            start=before[2][1].index(magic);allowed.update(range(start,start+size))
        assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(before[2][1],after[2][1])))
        assert configure_module(built,sha(built),profile,registration)[0]==built
        other=cpk_profile.encode([{'path':'sim:data/moddingapi/other.cpk','priority':10}])
        conflict,_=cpk_profile.configure(original,other,sha(original))
        try:configure_module(conflict,sha(conflict),profile,registration)
        except ValueError:pass
        else:raise AssertionError('existing archive list discarded')
        module_checks=True
    with tempfile.TemporaryDirectory() as d:
        d=Path(d);m=d/'manager';a=d/'input.cpk';m.write_bytes(manager);a.write_bytes(archive)
        cmd=[sys.executable,str(R/'tools/compile_condition_bundle.py'),'--param',str(m),'--cpk',str(a),'--expected-cpk-sha256',sha(archive),'--runtime-path',runtime,'--priority','42','--pc-api-prm',path]
        if module:cmd+=['--module',str(module),'--expected-module-sha256',sha(module.read_bytes())]
        subprocess.run(cmd+['--output',str(d/'ok')],check=True)
        assert (d/'ok/component_data/fixture/conditions.cpk').read_bytes()==result
        r=json.loads((d/'ok/condition_bundle_report.json').read_text())
        assert r['output_cpk_sha256']==sha(result) and not r['ready_for_gameplay_test']
        m.write_bytes(baseline)
        fail=subprocess.run(cmd+['--output',str(d/'bad')],capture_output=True)
        assert fail.returncode and not (d/'bad').exists()
        assert a.read_bytes()==archive
    out={'status':'PASS','invalid_archives_or_arguments_rejected':rejected,'exact_marker_diff_verified':True,
         'archive_profile_identity_verified':True,'no_conversion_preserves_archive':True,
         'module_composition_and_conflict_checks':module_checks,'gameplay_verified':False}
    output.mkdir(parents=True,exist_ok=True);(output/'condition_bundle.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--module',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.output,a.module)
