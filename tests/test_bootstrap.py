"""Exercise production C/C++ preflight/resolver/patcher on real decoded NSOs.
Only platform memory writes/cache flush and downstream hook installation are
modeled here. Native gameplay execution is a separate test.
"""
import argparse, ctypes, hashlib, json, struct, subprocess, tempfile, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.condition_profile import encode as condition_encode
def run(stock,r180,output):
    src=R/'overlay/source/program'
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        subprocess.run(['gcc','-O2','-fPIC','-c',str(src/'nsc_sha256.c'),'-o',str(td/'sha.o')],check=True)
        subprocess.run(['g++','-std=c++20','-O2','-shared','-fPIC','-Werror','-Wall','-Wextra',
            '-I'+str(R/'tests/host'),'-I'+str(src),str(R/'tests/host/harness.cpp'),
            str(src/'nsc_runtime_core.cpp'),str(src/'nsc_controls.cpp'),str(src/'nsc_condition_profile.cpp'),str(src/'nsc_condition_profile_data.cpp'),str(src/'nsc_cpk_profile.cpp'),str(src/'nsc_cpk_profile_data.cpp'),str(src/'nsc_factory.cpp'),str(src/'nsc_factory_profile.cpp'),str(src/'nsc_runtime_v2.cpp'),str(src/'nsc_image_guard.cpp'),
            str(td/'sha.o'),'-o',str(td/'core.so')],check=True)
        lib=ctypes.CDLL(str(td/'core.so'))
        for name in ['run_init','run_patch','profile']:
            getattr(lib,name).argtypes=[ctypes.c_void_p,ctypes.c_size_t]
            getattr(lib,name).restype=ctypes.c_int
        lib.writes.restype=ctypes.c_size_t
        lib.digest.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p]
        for n in [0,1,31,55,56,63,64,65,119,120,127,128,4097,1048576]:
            data=bytes((i*37+11)%256 for i in range(n)); d=ctypes.create_string_buffer(32)
            lib.digest(data,n,d); assert d.raw==hashlib.sha256(data).digest()
        a=stock.read_bytes(); b=r180.read_bytes(); assert len(a)==len(b)==0x12f5fd0
        assert lib.profile(None,len(a))==0
        # Invalid embedded factory data must reject the entire startup before
        # even the existing RAM patch plan or legacy hooks are touched.
        embedded=(ctypes.c_ubyte*4160).in_dll(lib,'nsc_factory_profile')
        embedded[0]^=1
        buf=ctypes.create_string_buffer(a,len(a))
        assert lib.run_init(buf,len(a))==0 and lib.writes()==0 and lib.hooks()==0
        embedded[0]^=1
        cpk_profile=(ctypes.c_ubyte*(64+32*208)).in_dll(lib,'nsc_cpk_profile')
        cpk_profile[0]^=1
        assert lib.run_init(buf,len(a))==0 and lib.writes()==0 and lib.hooks()==0
        cpk_profile[0]^=1
        condition_profile=(ctypes.c_ubyte*(64+512*80)).in_dll(lib,'nsc_condition_profile')
        condition_profile[0]^=1
        assert lib.run_init(buf,len(a))==0 and lib.writes()==0 and lib.hooks()==0
        condition_profile[0]^=1
        final=[]
        for data,p,changed in [(a,1,29),(b,2,26)]:
            buf=ctypes.create_string_buffer(data,len(data))
            assert lib.profile(buf,len(data))==p
            assert lib.profile(buf,len(data)-1)==0
            assert lib.run_init(buf,len(data))==1
            assert lib.writes()==33 and lib.hooks()==9
            result=buf.raw
            sites=[i for i in range(0,len(a),4) if result[i:i+4]!=data[i:i+4]]
            assert len(sites)==changed,(p,len(sites))
            final.append(result)
            # An already patched image must not be hooked a second time.
            assert lib.run_init(buf,len(data))==0 and lib.writes()==0 and lib.hooks()==0
        assert final[0]==final[1]
        sites=[i for i in range(0,len(a),4) if a[i:i+4]!=final[0][i:i+4]]
        # Every unsupported full-image mutation is rejected BEFORE writes/hooks.
        mutation_sites=sorted(set(sites+[0x7774dc,0x777770,0x777938,0x777a6c,0,0x2000,len(a)-1]))
        for off in mutation_sites:
            bad=bytearray(a); bad[off]^=1
            buf=ctypes.create_string_buffer(bytes(bad),len(bad))
            assert lib.run_init(buf,len(bad))==0
            assert lib.writes()==0 and lib.hooks()==0
        # Directly exercise whole-plan validation without the image guard.
        # The four new baseline words and existing cave are independently checked.
        for off in [0x80fb64,0x80fb78,0x80fbe4,0x876188,sites[-1]]:
            bad=bytearray(a);bad[off]^=1
            buf=ctypes.create_string_buffer(bytes(bad),len(bad))
            assert lib.run_patch(buf,len(bad))==0 and lib.writes()==0
        condition_counts=[]
        for count in [0,1,5,512]:
            payload=condition_encode([dict(name=f'TEST_{i}',reaction=0,state=0,icon=0,status=5,aura=5) for i in range(count)])
            ctypes.memmove(condition_profile,payload,len(payload))
            buf=ctypes.create_string_buffer(a,len(a))
            assert lib.run_init(buf,len(a))==1 and lib.writes()==33
            for off,reg in [(0x7774dc,24),(0x777770,19),(0x777938,19),(0x777a6c,19)]:
                assert struct.unpack_from('<I',buf.raw,off)[0]==0x7100001f|((512+count)<<10)|(reg<<5)
            condition_counts.append(512+count)
        ctypes.memmove(condition_profile,condition_encode([]),len(payload))
        output.mkdir(parents=True,exist_ok=True)
        (output/'patched.text').write_bytes(final[0])
        report={'status':'PASS','sha256_cases':14,'supported_profiles':2,
          'rejected_mutated_images':len(mutation_sites),'direct_patch_rejections':5,'invalid_profile_before_writes':True,'invalid_cpk_profile_before_writes':True,
          'invalid_condition_profile_before_writes':True,
          'configured_condition_counts':condition_counts,'stock_changed_words':29,'r180_changed_words':26,'outputs_identical':True,
          'patched_text_sha256':hashlib.sha256(final[0]).hexdigest(),
          'words':[{'offset':hex(i),'before':hex(struct.unpack_from('<I',a,i)[0]),
                    'after':hex(struct.unpack_from('<I',final[0],i)[0])} for i in sites],
          'modeled':['platform patch write/cache flush','downstream hook installers'],
          'emulator_gameplay_tested':False}
        (output/'bootstrap.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k!='words'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stock-text',type=Path,required=True)
    p.add_argument('--r180-text',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();run(args.stock_text,args.r180_text,args.output)
