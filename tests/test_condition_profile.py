"""Production descriptor registry + actual PC baseline + Android NSO packaging."""
import argparse,ctypes,hashlib,itertools,json,struct,subprocess,sys,tempfile
from pathlib import Path
from native_condition_fixture import baseline_from_main,pc_record
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.condition_profile import *
from portlib import factory_profile,cpk_profile,nso_profile

class Descriptor(ctypes.Structure):
    _fields_=[('name',ctypes.c_char_p)]+[(k,ctypes.c_uint32) for k in (*FIELDS,'reserved')]

def run(main,module,output):
    baseline,native=baseline_from_main(main)
    raw=baseline+pc_record('MOD_A','MOD_B',0x201,8,5,5)+pc_record('MOD_B','AWAKE_2NRT',10,7,5,5)
    valid,trace=compile_table(raw);rows=decode(valid);assert rows[0]['reaction']==513 and rows[1]['reaction']==1
    assert decode(compile_table(baseline)[0])==[]
    assert decode(compile_table(baseline+pc_record('N'*48,'MISSING'))[0])[0]['reaction']==0
    assert compile_table(baseline+pc_record('N','MISSING'))[1]['missing_reactions_native_zero_fallback']==[{'index':512,'reaction':'MISSING','resolved':0}]
    invalid_inputs=[b'',b'NUCC'+raw[4:],raw[:-1],raw+b'X',baseline+pc_record('AWAKE_2NRT'),
                    baseline+pc_record('DUP')+pc_record('DUP'),baseline+pc_record(''),baseline+pc_record('bad\n')]
    changed=bytearray(raw);changed[103*112+108]^=1;invalid_inputs.append(bytes(changed))
    for b in invalid_inputs:
        try:compile_table(b)
        except ValueError:pass
        else:raise AssertionError('invalid PC table accepted')
    src=R/'overlay/source/program'
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        subprocess.run(['gcc','-O2','-fPIC','-c',str(src/'nsc_sha256.c'),'-o',str(td/'sha.o')],check=True)
        subprocess.run(['g++','-std=c++20','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-I'+str(src),
            str(R/'tests/host/condition_profile_harness.cpp'),str(src/'nsc_condition_profile.cpp'),str(src/'nsc_condition_profile_data.cpp'),str(td/'sha.o'),'-o',str(td/'condition.so')],check=True)
        lib=ctypes.CDLL(str(td/'condition.so'));lib.condition_load.argtypes=[ctypes.c_void_p,ctypes.c_size_t];lib.condition_load.restype=ctypes.c_bool
        lib.condition_get.argtypes=[ctypes.c_uint32];lib.condition_get.restype=ctypes.POINTER(Descriptor)
        def load(b):return lib.condition_load(b,len(b))
        assert lib.condition_count()==0 and lib.condition_total()==512
        assert load(valid) and lib.condition_total()==514
        def check():
            assert lib.condition_count()==2
            for i,row in enumerate(rows,512):
                e=lib.condition_get(i).contents
                assert e.name==row['name'].encode() and e.reserved==0
                assert [getattr(e,f) for f in FIELDS]==[row[f] for f in FIELDS]
        check();rejected=0
        for i in range(PROFILE_SIZE):
            b=bytearray(valid);b[i]^=1
            assert not load(bytes(b));rejected+=1
        bad=[]
        for at,fmt,value in [(16,'<I',2),(20,'<I',513),(56,'B',1),(64,'B',0),(65,'B',255),
              (64+49,'B',1),(64+76,'<I',1),(64+56,'<I',514),(64+160,'B',1)]:
            b=bytearray(valid);struct.pack_into(fmt,b,at,value);bad.append(seal(b))
        b=bytearray(valid);b[144:193]=b[64:113];bad.append(seal(b))
        b=bytearray(valid);b[64:113]=b'x'*49;bad.append(seal(b))
        bad += [valid[:-1],valid+b'\0']
        for b in bad:
            assert not load(b);check();rejected+=1
            try:decode(b)
            except ValueError:pass
            else:raise AssertionError('invalid serialized profile')
        assert not lib.condition_load(None,PROFILE_SIZE)
        for n in [0,1,5,511,512]:
            many=[dict(name=f'C{i}',reaction=512+n-1,state=i,icon=i,status=5,aura=5) for i in range(n)]
            assert load(encode(many)) and lib.condition_total()==512+n
            for i in range(n):assert lib.condition_get(512+i).contents.state==i
            for i in [0,1,511,512+n,1024,0xffffffff]:assert not lib.condition_get(i)
        assert load(valid);check()
        nso=module.read_bytes();result,pack=configure(nso,valid,hashlib.sha256(nso).hexdigest())
        before=nso_profile.segments(nso);after=nso_profile.segments(result);at=pack['profile_data_offset']
        assert before[:2]==after[:2] and before[2][1][:at]==after[2][1][:at] and before[2][1][at+PROFILE_SIZE:]==after[2][1][at+PROFILE_SIZE:]
        assert after[2][1][at:at+PROFILE_SIZE]==valid
        edits=[(configure,valid),(nso_profile.configure,factory_profile.encode({281:58})),(cpk_profile.configure,cpk_profile.encode([dict(path='sim:data/moddingapi/test.cpk',priority=32)]))]
        results=[]
        for order in itertools.permutations(edits):
            b=nso
            for fn,profile in order:b,_=fn(b,profile,hashlib.sha256(b).hexdigest())
            results.append(b)
        assert all(b==results[0] for b in results)
        param=td/'conditionprmManager.xfbin';param.write_bytes(raw);nso_path=td/'subsdk9';nso_path.write_bytes(nso)
        subprocess.run([sys.executable,str(R/'tools/compile_condition_profile.py'),'--param',str(param),'--module',str(nso_path),'--expected-module-sha256',hashlib.sha256(nso).hexdigest(),'--output',str(td/'out')],check=True)
        assert (td/'out/subsdk9.condition_component_NOT_GAMEPLAY_RELEASE').read_bytes()==result
        param.write_bytes(raw[:-1]);badout=td/'badout'
        fail=subprocess.run([sys.executable,str(R/'tools/compile_condition_profile.py'),'--param',str(param),'--output',str(badout)],capture_output=True)
        assert fail.returncode and not badout.exists()
    report={'status':'PASS','corrupt_profiles_rejected':rejected,'invalid_pc_tables_rejected':len(invalid_inputs),
        'capacity_cases':[0,1,5,511,512],'native_prefix_rows_verified':512,
        'pc_switch_baseline_differences':[{'index':103,'name':'AWAKE_1SKR','field':'aura','pc':5,'switch':107,'runtime':'preserve native'}],
        'three_profile_edit_orders_identical':6,'module_edit':pack,'pc_input':trace,
        'raw_conditionprm_integrated':False,'gameplay_verified':False,'full_moddingapi':False}
    output.mkdir(parents=True,exist_ok=True);(output/'condition_profile.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.module,a.output)
