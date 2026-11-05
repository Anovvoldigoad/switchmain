"""Multi-CPK batch tests using genuine parsers, synthetic assets and compiled NSO."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from native_condition_fixture import baseline_from_main,pc_record
from test_condition_companion import fixture as condition_fixture
from test_cpk_events import cpk
from test_prm_marker import fixture as prm_fixture,event
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib import condition_batch,cpk_events,cpk_profile,condition_profile,nso_profile


def run(main,module,out):
    baseline,_=baseline_from_main(main)
    names=[baseline[i:i+48].split(b'\0')[0].decode() for i in range(0,len(baseline),112)]
    manager=baseline+pc_record('BATCH_TEST')
    raw=condition_fixture(names+['BATCH_TEST'])
    prm=prm_fixture([event(14),event(0),event(15)])
    first_path='data/spc/firstprm.bin.xfbin'
    second_path='data/spc/secondprm.bin.xfbin'
    first=cpk([('data/spc/conditionprm.bin.xfbin',raw),(first_path,prm),
               ('data/opaque/item',b'keep')])
    second=cpk([(second_path,prm),('data/opaque/second',b'keep')])
    with tempfile.TemporaryDirectory() as d:
        d=Path(d);a=d/'first.cpk';b=d/'second.cpk';a.write_bytes(first);b.write_bytes(second)
        owner='sim:data/moddingapi/first.cpk'
        rows=[{'source':str(a),'sha256':condition_batch.sha(first),'path':owner,'priority':10,
               'pc_api_prms':[first_path]},
              {'source':str(b),'sha256':condition_batch.sha(second),
               'path':'sim:data/moddingapi/second.cpk','priority':20,
               'pc_api_prms':[second_path]}]
        manifest={'condition_owner':owner,'archives':rows}
        native=module.read_bytes()
        result=condition_batch.build(manifest,manager,condition_batch.sha(manager),
                                     d/'out',native,condition_batch.sha(native))
        assert result['archive_count']==2 and result['effective_cpk_entries']==2
        assert not result['gameplay_verified'] and not result['runtime_archive_winner_verified']
        converted1=(d/'out/component_data/first.cpk').read_bytes()
        converted2=(d/'out/component_data/second.cpk').read_bytes()
        assert converted1!=first and converted2!=second
        assert cpk_events.entries(converted1)==cpk_events.entries(first)
        assert cpk_events.entries(converted2)==cpk_events.entries(second)
        assert a.read_bytes()==first and b.read_bytes()==second
        assert [r['name'] for r in condition_profile.decode((d/'out/condition.profile').read_bytes())]==['BATCH_TEST']
        assert cpk_profile.decode((d/'out/cpk.profile').read_bytes())==[
            {'path':owner,'priority':10},{'path':rows[1]['path'],'priority':20}]
        built=(d/'out/subsdk9.COMPONENT_NOT_GAMEPLAY_RELEASE').read_bytes()
        assert nso_profile.segments(native)[:2]==nso_profile.segments(built)[:2]
        m=d/'manager';m.write_bytes(manager);j=d/'manifest.json';j.write_text(json.dumps(manifest))
        cli=[sys.executable,str(R/'tools/compile_condition_batch.py'),
             '--manifest',str(j),'--pc-manager',str(m),
             '--expected-manager-sha256',condition_batch.sha(manager),
             '--module',str(module),'--expected-module-sha256',condition_batch.sha(native),
             '--output',str(d/'cli')]
        subprocess.run(cli,check=True,capture_output=True)
        assert (d/'cli/cpk.profile').read_bytes()==(d/'out/cpk.profile').read_bytes()
        assert (d/'cli/subsdk9.COMPONENT_NOT_GAMEPLAY_RELEASE').read_bytes()==built
        assert (d/'cli/batch_report.json').read_bytes()==(d/'out/batch_report.json').read_bytes()
        # Rejected manifests must not create an output, even after valid first file.
        bads=[]
        def invalid(fn):
            x=json.loads(json.dumps(manifest));fn(x);bads.append(x)
        invalid(lambda x:x['archives'][0].update(sha256='0'*64))
        invalid(lambda x:x['archives'][1].update(priority=10))
        invalid(lambda x:x.update(condition_owner='sim:data/moddingapi/missing.cpk'))
        invalid(lambda x:x['archives'][1].update(path=owner))
        invalid(lambda x:x['archives'][0]['pc_api_prms'].append('data/spc/missing.xfbin'))
        invalid(lambda x:x['archives'][0]['pc_api_prms'].append(first_path))
        invalid(lambda x:x['archives'][1].update(pc_api_prms='bad'))
        invalid(lambda x:x['archives'][1].update(path='sim:data/moddingapi/../bad.cpk'))
        invalid(lambda x:x['archives'][0]['pc_api_prms'].append('data/spc/conditionprm.bin.xfbin'))
        duplicate_raw=cpk([('data/spc/conditionprm.bin.xfbin',raw),(second_path,prm)])
        p=d/'dup.cpk';p.write_bytes(duplicate_raw)
        invalid(lambda x:x['archives'][1].update(source=str(p),sha256=condition_batch.sha(duplicate_raw)))
        overlap=cpk([(first_path,b'different'),(second_path,prm)])
        p=d/'overlap.cpk';p.write_bytes(overlap)
        invalid(lambda x:x['archives'][1].update(source=str(p),sha256=condition_batch.sha(overlap)))
        invalid(lambda x:x['archives'][0].update(priority=True))
        rejected=0
        for i,x in enumerate(bads):
            dest=d/f'invalid{i}'
            try:condition_batch.build(x,manager,condition_batch.sha(manager),
                                      dest,native,condition_batch.sha(native))
            except ValueError:rejected+=1
            else:raise AssertionError('Accepted invalid CPK batch')
            assert not dest.exists()
        assert rejected==len(bads)
        for i,(mdata,mhash,nso,nhash) in enumerate([
            (manager,'0'*64,native,condition_batch.sha(native)),
            (manager,condition_batch.sha(manager),native,'0'*64),
            (baseline,condition_batch.sha(baseline),native,condition_batch.sha(native)),
            (manager,condition_batch.sha(manager),native,None)]):
            dest=d/f'badinput{i}'
            try:condition_batch.build(manifest,mdata,mhash,dest,nso,nhash)
            except ValueError:pass
            else:raise AssertionError('Invalid manager/module accepted')
            assert not dest.exists()
        empty=condition_batch.build(manifest,manager,condition_batch.sha(manager),d/'standalone')
        assert empty['effective_cpk_entries']==2
        assert not (d/'standalone/subsdk9.COMPONENT_NOT_GAMEPLAY_RELEASE').exists()
        old_reg=cpk_profile.encode([{'path':'sim:data/moddingapi/old.cpk','priority':3}])
        prior,_=cpk_profile.configure(native,old_reg,condition_batch.sha(native))
        pre=condition_batch.build(manifest,manager,condition_batch.sha(manager),
                                  d/'preloaded',prior,condition_batch.sha(prior))
        assert pre['effective_cpk_entries']==3
        assert cpk_profile.decode((d/'preloaded/cpk.profile').read_bytes())[0]['priority']==3
        try:condition_batch.build(manifest,manager,condition_batch.sha(manager),d/'out')
        except ValueError:pass
        else:raise AssertionError('Clobbered existing output')
    out.mkdir(parents=True,exist_ok=True)
    summary={'status':'PASS_COMPONENT','archives':2,'invalid_manifests_rejected':rejected,
             'additional_invalid_hash_or_manager_cases_rejected':4,
             'effective_profile_preserves_old_registrations':True,
             'global_condition_owner_enforced':True,
             'cross_archive_collisions_rejected':True,
             'source_and_output_immutability_tested':True,
             'real_game_archives_tested':False,'emulator_gameplay_tested':False}
    (out/'condition_batch.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--main',required=True,type=Path)
    p.add_argument('--module',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run(a.main,a.module,a.output)
