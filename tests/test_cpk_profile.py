"""Production C++ profile validation, retry/reentry/concurrency, Android NSO edits."""
import argparse,ctypes,hashlib,json,struct,subprocess,tempfile,threading,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.cpk_profile import *
from portlib.nso_profile import segments
from portlib import factory_profile,nso_profile


def run(module_path,out):
    source=R/'overlay/source/program'
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        subprocess.run(['gcc','-O2','-fPIC','-c',str(source/'nsc_sha256.c'),'-o',str(td/'sha.o')],check=True)
        subprocess.run(['g++','-std=c++20','-O2','-Werror','-Wall','-Wextra','-shared','-fPIC',
                        '-I'+str(source),str(R/'tests/host/cpk_profile_harness.cpp'),
                        str(source/'nsc_cpk_profile.cpp'),str(source/'nsc_cpk_profile_data.cpp'),
                        str(td/'sha.o'),'-o',str(td/'cpk.so')],check=True)
        lib=ctypes.CDLL(str(td/'cpk.so'))
        lib.load_cpk.argtypes=[ctypes.c_void_p,ctypes.c_size_t];lib.load_cpk.restype=ctypes.c_bool
        lib.cpk_id.argtypes=[ctypes.c_uint32,ctypes.POINTER(ctypes.c_uint32)];lib.cpk_id.restype=ctypes.c_bool
        class Arg(ctypes.Structure):_fields_=[('path',ctypes.c_char_p),('flags',ctypes.c_uint64),('r10',ctypes.c_uint64),('r18',ctypes.c_uint64)]
        Bind=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.POINTER(Arg),ctypes.POINTER(ctypes.c_uint32),ctypes.c_int)
        lib.cpk_after.argtypes=[ctypes.POINTER(Arg),ctypes.c_uint32,Bind]
        rows=[{'path':'sim:data/moddingapi/sub/Mod A.cpk','priority':32},
              {'path':'sim:data/moddingapi/Second.CPK','priority':0x7fffffff}]
        valid=encode(rows);assert decode(valid)==rows
        assert lib.load_cpk(valid,len(valid));assert lib.cpk_count()==2
        rejects=0
        for i in range(PROFILE_SIZE):
            bad=bytearray(valid);bad[i]^=1
            assert not lib.load_cpk(bytes(bad),len(bad));assert lib.cpk_count()==2
            try:decode(bad)
            except ValueError:pass
            else:raise AssertionError(i)
            rejects+=1
        def resign(b):
            b[24:56]=hashlib.sha256(b[:24]+b[56:]).digest();return bytes(b)
        bads=[]
        for off,value in [(16,2),(20,33),(56,1),(64,0x80000000),(68,1),(64+2*RECORD_SIZE,1)]:
            b=bytearray(valid);struct.pack_into('<I',b,off,value);bads.append(resign(b))
        b=bytearray(valid);b[80+RECORD_SIZE:80+RECORD_SIZE+PATH_SIZE]=b[80:80+PATH_SIZE];bads.append(resign(b))
        b=bytearray(valid);b[64+RECORD_SIZE:68+RECORD_SIZE]=b[64:68];bads.append(resign(b))
        bad_paths=['sim:data/moddingapi/../A.cpk','sim:data/moddingapi//A.cpk','sim:data/moddingapi/./A.cpk',
                   'sim:data/moddingapi/ A.cpk','sim:data/moddingapi/A.cpk ', 'sim:data/moddingapi/.cpk',
                   'sim:data/moddingapi/A\\B.cpk','sim:data/moddingapi/A:foo.cpk',
                   'sdmc:data/moddingapi/A.cpk','sim:data/moddingapi/'+('x'*180)+'.cpk','sim:data/moddingapi/é.cpk']
        for name in bad_paths:
            try:encode([{'path':name,'priority':1}])
            except ValueError:pass
            else:raise AssertionError(name)
            raw=name.encode();b=bytearray(valid);b[80:80+PATH_SIZE]=raw[:PATH_SIZE].ljust(PATH_SIZE,b'\0');bads.append(resign(b))
        b=bytearray(valid);b[80+len(rows[0]['path'])+1]=1;bads.append(resign(b))
        for b in bads:
            assert not lib.load_cpk(b,len(b))
            try:decode(b)
            except ValueError:pass
            else:raise AssertionError('Signed invalid profile accepted')
            rejects+=1
        assert not lib.load_cpk(None,PROFILE_SIZE) and not lib.load_cpk(valid,PROFILE_SIZE-1)
        invalid_manifests=[{},rows*17,[{'path':rows[0]['path']}],
                           [{'path':rows[0]['path'],'priority':True}],
                           [{'path':rows[0]['path'],'priority':-1}],
                           [{'path':rows[0]['path'],'priority':1.0}],
                           [{'path':rows[0]['path'],'priority':2**31}],
                           [rows[0],dict(rows[0])]]
        for invalid in invalid_manifests:
            try:encode(invalid)
            except ValueError:pass
            else:raise AssertionError('Invalid manifest accepted')
        for count in [0,1,31,32]:
            data=encode([{'path':f'sim:data/moddingapi/{i}.cpk','priority':i} for i in range(count)])
            assert lib.load_cpk(data,len(data)) and lib.cpk_count()==count
        assert lib.load_cpk(valid,len(valid))
        trigger=Arg(b'sim:data/base.cpk',0,0,0);seen=[];errors=[]
        @Bind
        def reenter(p,out_id,priority):
            try:
                seen.append((p.contents.path.decode(),priority))
                assert p.contents.flags==p.contents.r10==p.contents.r18==0
                lib.cpk_after(ctypes.byref(trigger),1,reenter) # must return, not wait/deadlock
                out_id[0]=100+len(seen);return 1
            except BaseException as e:errors.append(str(e));return 0
        lib.cpk_after(ctypes.byref(trigger),1,reenter)
        assert not errors and seen==[(r['path'],r['priority']) for r in rows]
        assert lib.cpk_registered()==2
        lib.cpk_after(ctypes.byref(trigger),1,reenter);assert len(seen)==2
        id_value=ctypes.c_uint32(0)
        assert lib.cpk_id(0,ctypes.byref(id_value)) and id_value.value==101
        assert not lib.cpk_id(32,ctypes.byref(id_value)) and not lib.cpk_id(0,None)
        # Rejected replacements must not erase successfully registered IDs.
        assert not lib.load_cpk(bads[0],len(bads[0]))
        assert lib.cpk_registered()==2 and lib.cpk_id(0,ctypes.byref(id_value)) and id_value.value==101
        assert lib.load_cpk(valid,len(valid))
        entered=threading.Event();release=threading.Event();seen.clear();errors.clear()
        @Bind
        def concurrent(p,out_id,priority):
            try:
                seen.append(p.contents.path.decode())
                if len(seen)==1:
                    entered.set();assert release.wait(5)
                out_id[0]=200+len(seen);return 1
            except BaseException as e:errors.append(str(e));return 0
        first=threading.Thread(target=lib.cpk_after,args=(ctypes.byref(trigger),1,concurrent))
        first.start();assert entered.wait(5)
        second=threading.Thread(target=lib.cpk_after,args=(ctypes.byref(trigger),1,concurrent))
        second.start();second.join(2);assert not second.is_alive()
        assert seen==[rows[0]['path']];release.set();first.join(5)
        assert not first.is_alive() and not errors and seen==[r['path'] for r in rows]
        assert lib.cpk_registered()==2
        # Android standard-library packaging; both profile edits must commute.
        nso=module_path.read_bytes();sha=hashlib.sha256(nso).hexdigest()
        cpk_nso,pack_report=configure(nso,valid,sha)
        fp=factory_profile.encode({281:58})
        both_a,_=nso_profile.configure(cpk_nso,fp,hashlib.sha256(cpk_nso).hexdigest())
        factory_nso,_=nso_profile.configure(nso,fp,sha)
        both_b,_=configure(factory_nso,valid,hashlib.sha256(factory_nso).hexdigest())
        assert both_a==both_b
        before=segments(nso);after=segments(cpk_nso)
        assert before[:2]==after[:2]
        pos=pack_report['profile_data_offset']
        assert before[2][1][:pos]==after[2][1][:pos]
        assert before[2][1][pos+PROFILE_SIZE:]==after[2][1][pos+PROFILE_SIZE:]
        empty,_=configure(cpk_nso,encode([]),hashlib.sha256(cpk_nso).hexdigest())
        assert segments(empty)==segments(nso) or [x[:2] for x in segments(empty)]==[x[:2] for x in segments(nso)]
        manifest=td/'cpks.json';manifest.write_text(json.dumps(rows));mod=td/'subsdk9';mod.write_bytes(nso)
        dest=td/'output'
        subprocess.run([sys.executable,str(R/'tools/compile_cpk_profile.py'),'--manifest',str(manifest),
                        '--module',str(mod),'--expected-module-sha256',sha,'--output',str(dest)],check=True,capture_output=True)
        assert (dest/'subsdk9.cpk_component_NOT_GAMEPLAY_RELEASE').read_bytes()==cpk_nso
        result={'status':'PASS','corrupt_profiles_rejected':rejects,'invalid_manifests_rejected':len(invalid_manifests),'capacity_cases':[0,1,31,32],
                'reentry_no_duplicate_registration':True,'concurrent_callback_no_duplicate_registration':True,
                'invalid_replacement_preserves_registered_ids':True,'factory_cpk_edits_commute':True,
                'module_edit':pack_report,'gameplay_verified':False,'full_moddingapi':False}
        out.mkdir(parents=True,exist_ok=True);(out/'cpk_profile.json').write_text(json.dumps(result,indent=2)+'\n')
        print('CPK profiles PASS:',rejects,'corrupt profiles, reentry/concurrency and composed Android packaging')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.module,a.output)
