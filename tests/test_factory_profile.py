"""Actual C++ registry, malformed PC input, and real NSO data-only packaging."""
import argparse, ctypes, hashlib, json, random, struct, subprocess, sys, tempfile
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools'))
from portlib.factory_profile import encode, decode, compile_records, catalog, seal, PROFILE_SIZE
from portlib.nso_profile import configure, segments, decompress_lz4


def record(name, owner):
    raw = name.encode('ascii')
    assert len(raw) <= 24
    return raw.ljust(24, b'\0') + struct.pack('<H', owner) + bytes(6)


def run(module, output):
    src = R/'overlay/source/program'
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        subprocess.run(['gcc','-O2','-fPIC','-c',str(src/'nsc_sha256.c'),'-o',str(tmp/'sha.o')],check=True)
        subprocess.run(['g++','-std=c++20','-O2','-fPIC','-shared','-Wall','-Wextra','-Werror',
                        '-I'+str(src),str(R/'tests/host/factory_harness.cpp'),str(src/'nsc_factory.cpp'),
                        str(src/'nsc_factory_profile.cpp'),str(tmp/'sha.o'),'-o',str(tmp/'factory.so')],check=True)
        lib = ctypes.CDLL(str(tmp/'factory.so'))
        lib.load_profile.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        lib.load_profile.restype = ctypes.c_int
        lib.resolve_profile.argtypes = [ctypes.c_uint32]
        lib.resolve_profile.restype = ctypes.c_uint32
        def load(b): return lib.load_profile(b, len(b))
        assert lib.resolve_profile(281) == 281
        assert load(encode({281:58})) == 1
        assert lib.resolve_profile(281) == 58 and lib.resolve_profile(280) == 280
        valid = encode({0:0, 145:58, 276:276, 281:58, 1023:1})
        assert load(valid) == 1 and lib.count_profile() == 5
        rejected = 0
        for i in range(PROFILE_SIZE):
            bad = bytearray(valid); bad[i] ^= 1
            assert load(bytes(bad)) == 0
            assert lib.resolve_profile(281) == 58 and lib.count_profile() == 5
            rejected += 1
        bads = []
        for off, fmt, value in [(16,'<I',2),(20,'<I',1025),(56,'<B',1),
                                (64,'<H',1024),(66,'<H',11),(68,'<H',0),(84,'<B',1)]:
            b = bytearray(valid); struct.pack_into(fmt,b,off,value); bads.append(seal(b))
        bads += [valid[:-1], valid+b'\0']
        for b in bads:
            assert load(b) == 0 and lib.resolve_profile(281) == 58
            rejected += 1
        assert lib.load_profile(None,PROFILE_SIZE) == 0
        supported = [r['selector'] for r in catalog().values() if r['supported']]
        mappings = {i:supported[i%len(supported)] for i in range(1024)}
        assert load(encode(mappings)) == 1 and lib.count_profile() == 1024
        for owner, selector in mappings.items(): assert lib.resolve_profile(owner) == selector
        for owner in [1024,65535,0xffffffff]: assert lib.resolve_profile(owner) == owner
        assert load(encode({})) == 1 and lib.count_profile() == 0
        for owner in range(1024): assert lib.resolve_profile(owner) == owner
        records = 0
        for name, row in catalog().items():
            for variant in [name,name.lower(),name[5:]]:
                if row['supported']:
                    profile, trace = compile_records([('test',record(variant,280))],{280:281})
                    assert decode(profile) == {281:row['selector']}
                    assert trace[0]['pc_owner']==280 and trace[0]['switch_owner']==281
                    records += 1
                else:
                    try: compile_records([('test',record(variant,281))])
                    except ValueError: pass
                    else: raise AssertionError(('accepted unverified placeholder',name))
        b,trace=compile_records([('a',record('2dnz',280)),('b',record('2nrt',280))],{280:281})
        assert decode(b)=={281:1} and trace[-1]['replaces_previous_mapping']
        malformed = [b'x',b'NUCC'+bytes(28),bytes(32),record('BAD',281),record('2dnz',65535),b'\xff'+bytes(31)]
        for raw in malformed:
            try: compile_records([('bad',raw)])
            except ValueError: pass
            else: raise AssertionError('bad PC record accepted')
        nso = module.read_bytes(); digest=hashlib.sha256(nso).hexdigest()
        configured, report = configure(nso,valid,digest)
        before=segments(nso); after=segments(configured); at=report['profile_data_offset']
        assert before[:2]==after[:2]
        assert before[2][1][:at]==after[2][1][:at]
        assert before[2][1][at+PROFILE_SIZE:]==after[2][1][at+PROFILE_SIZE:]
        assert after[2][1][at:at+PROFILE_SIZE]==valid
        assert configured[64:96]==nso[64:96] # original module build ID retained
        assert load(after[2][1][at:at+PROFILE_SIZE]) == 1
        roundtrip,_ = configure(configured,encode({}),hashlib.sha256(configured).hexdigest())
        assert [r[:2] for r in segments(roundtrip)]==[r[:2] for r in before]
        for data, profile, expected in [(nso,valid,'0'*64),(nso,bytes(PROFILE_SIZE),digest),
                                        (nso[:-1],valid,hashlib.sha256(nso[:-1]).hexdigest())]:
            try: configure(data,profile,expected)
            except ValueError: pass
            else: raise AssertionError('invalid module input accepted')
        # Differential decompression against liblz4, including overlapping copies.
        import lz4.block
        rng=random.Random(236)
        for n in [1,4,15,16,255,256,4096,65536]:
            for raw in [bytes(n),(b'abc'*n)[:n],rng.randbytes(n)]:
                packed=lz4.block.compress(raw,store_size=False)
                assert decompress_lz4(packed,n)==raw
        for packed,n in [(b'\xff',20),(b'\x10a\0\0',5),(b'\x10a\x02\0',5),(b'\xf0\xff',20)]:
            try: decompress_lz4(packed,n)
            except ValueError: pass
            else: raise AssertionError('invalid LZ4 accepted')
    result={'status':'PASS','cpp_corruption_rejections':rejected+1,'supported_selectors':len(supported),
            'normalized_pc_record_cases':records,'placeholder_names_rejected':53,'max_owner_mappings':1024,
            'mapping_lookup_cases':2051,'lz4_differential_cases':24,'nso_profile_edit':report,
            'scope':'class-selector profile parsing and packaging; no game execution',
            'gameplay_verified':False,'full_moddingapi':False}
    output.mkdir(parents=True,exist_ok=True)
    (output/'factory_profile.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.module,a.output)
