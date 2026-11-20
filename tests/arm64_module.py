"""Minimal test loader. OS imports/JIT publication are explicitly modeled."""
import struct
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
import unicorn.arm64_const as ar
M=0x7100000000; D=0x7200000000; H=0x7300000000; S=0x7400000000
STOP=H+0x1ff000
G=[getattr(ar,'UC_ARM64_REG_X'+str(i)) for i in range(31)]
def align(n): return (n+4095)&~4095
def w64(u,p,v): u.mem_write(p,struct.pack('<Q',v))
def qword(u,p): return struct.unpack('<Q',u.mem_read(p,8))[0]
def call(u,at,args,instruction_budget=2000000):
    saved=[0xa0000000+i for i in range(11)]
    for i,v in enumerate(saved): u.reg_write(G[19+i],v)
    for i,v in enumerate(args): u.reg_write(G[i],v)
    u.reg_write(ar.UC_ARM64_REG_SP,S+0xfff0);u.reg_write(ar.UC_ARM64_REG_LR,STOP)
    u.emu_start(at,STOP,count=instruction_budget)
    assert u.reg_read(ar.UC_ARM64_REG_PC)==STOP, hex(u.reg_read(ar.UC_ARM64_REG_PC))
    assert u.reg_read(ar.UC_ARM64_REG_SP)==S+0xfff0
    assert [u.reg_read(G[19+i]) for i in range(11)]==saved
    return u.reg_read(G[0])
def module(path):
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
    u.mem_map(H,0x200000,7);u.mem_map(S,0x10000,3)
    u.reg_write(ar.UC_ARM64_REG_CPACR_EL1,3<<20)
    with path.open('rb') as f:
        elf=ELFFile(f);segs=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
        end=align(max(s['p_vaddr']+s['p_memsz'] for s in segs))
        u.mem_map(D,end,7)
        for s in segs: u.mem_write(D+s['p_vaddr'],s.data())
        symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        dyn=elf.get_section_by_name('.dynsym');unresolved=set()
        for r in elf.get_section_by_name('.rela.dyn').iter_relocations():
            typ=r['r_info_type'];value=r['r_addend']
            if typ==1027: value+=D
            elif typ==1025:
                s=dyn.get_symbol(r['r_info_sym'])
                if s['st_shndx']=='SHN_UNDEF': unresolved.add(s.name);value=0
                else: value+=D+s['st_value']
            else: raise AssertionError(('relocation',typ))
            w64(u,D+r['r_offset'],value)
    assert unresolved=={'_ZN2nn2ro6detail15g_pAutoLoadListE','_ZN2nn2ro6detail35g_LookupGlobalManualFunctionPointerE'}
    def sym(fragment):
        matches=[D+v for k,v in symbols.items() if fragment in k]
        assert len(matches)==1,(fragment,matches)
        return matches[0]
    return u,sym,symbols,end
