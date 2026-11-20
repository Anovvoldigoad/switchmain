#!/usr/bin/env python3
"""Compare every generated NSO segment/hash with its actual AArch64 ELF."""
import argparse, hashlib, json, struct
from pathlib import Path
import lz4.block
from elftools.elf.elffile import ELFFile
ALLOWED_IMPORTS={'_ZN2nn2ro6detail15g_pAutoLoadListE',
                 '_ZN2nn2ro6detail35g_LookupGlobalManualFunctionPointerE'}
def sha(b):return hashlib.sha256(b).hexdigest()
def verify(nso_path,elf_path,output):
    b=nso_path.read_bytes();assert len(b)>=256 and b[:4]==b'NSO0'
    flags=struct.unpack_from('<I',b,12)[0];assert flags&0x38==0x38
    with elf_path.open('rb') as f:
        elf=ELFFile(f);assert elf['e_machine']=='EM_AARCH64' and elf['e_type']=='ET_DYN'
        segs=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
        assert [s['p_flags'] for s in segs]==[5,4,6]
        imports={s.name for s in elf.get_section_by_name('.dynsym').iter_symbols()
                 if s['st_shndx']=='SHN_UNDEF' and s.name}
        assert imports==ALLOWED_IMPORTS,imports
        assert not any(t.entry.d_tag=='DT_NEEDED' for t in elf.get_section_by_name('.dynamic').iter_tags())
        rows=[];last_end=0
        for i,s in enumerate(segs):
            off,va,size=struct.unpack_from('<III',b,16+i*16)
            packed=struct.unpack_from('<I',b,96+i*4)[0]
            stored=packed if flags&(1<<i) else size
            assert off>=256 and off+stored<=len(b) and va%4096==0 and va>=last_end
            raw=b[off:off+stored]
            if flags&(1<<i):raw=lz4.block.decompress(raw,uncompressed_size=size)
            assert len(raw)==size and hashlib.sha256(raw).digest()==b[160+i*32:192+i*32]
            assert va==s['p_vaddr'] and raw==s.data()
            last_end=va+size
            rows.append({'segment':['text','rodata','data'][i],'memory_offset':hex(va),'bytes':size,'sha256':sha(raw)})
        bss=struct.unpack_from('<I',b,60)[0]
        assert bss==segs[2]['p_memsz']-segs[2]['p_filesz']
    report={'status':'PASS','nso_sha256':sha(b),'elf_sha256':sha(elf_path.read_bytes()),
            'build_id':b[64:96].hex(),'segments':rows,'bss_bytes':bss,
            'imports':sorted(imports),'writable_executable_segments':False,
            'elf_nso_segment_identity':True,'emulator_gameplay_tested':False}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--nso',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();verify(a.nso,a.elf,a.output)
