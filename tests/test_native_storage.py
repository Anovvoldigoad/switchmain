"""Real ARM64 module callbacks + native Switch allocation/copy/getter slices.
Requires user-supplied decoded main; this test never launches the full game.
"""
import argparse, json, struct, hashlib, sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from portlib.factory_profile import encode
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
import unicorn.arm64_const as ar
M=0x7100000000; D=0x7200000000; H=0x7300000000; S=0x7400000000
STOP=H+0x1ff000
G=[getattr(ar,'UC_ARM64_REG_X'+str(i)) for i in range(31)]
def align(n):return (n+4095)&~4095
def word(u,p):return struct.unpack('<I',u.mem_read(p,4))[0]
def qword(u,p):return struct.unpack('<Q',u.mem_read(p,8))[0]
def w64(u,p,v):u.mem_write(p,struct.pack('<Q',v))
def call(u,at,args):
    preserved=[0xa0000000+i for i in range(11)]
    for i,v in enumerate(preserved):u.reg_write(G[19+i],v)
    for i,v in enumerate(args):u.reg_write(G[i],v)
    u.reg_write(ar.UC_ARM64_REG_SP,S+0xfff0);u.reg_write(ar.UC_ARM64_REG_LR,STOP)
    u.emu_start(at,STOP,count=2000000)
    assert u.reg_read(ar.UC_ARM64_REG_PC)==STOP
    assert u.reg_read(ar.UC_ARM64_REG_SP)==S+0xfff0
    assert [u.reg_read(G[19+i]) for i in range(11)]==preserved
    return u.reg_read(G[0])
def run(text_path,elf_path,out):
    text=text_path.read_bytes();assert len(text)==0x12f5fd0
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
    u.mem_map(M,align(len(text)),5);u.mem_write(M,text)
    u.mem_map(H,0x200000,3);u.mem_map(S,0x10000,3)
    u.reg_write(ar.UC_ARM64_REG_CPACR_EL1,3<<20)
    with elf_path.open('rb') as f:
        elf=ELFFile(f);segs=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
        module_end=align(max(s['p_vaddr']+s['p_memsz'] for s in segs))
        u.mem_map(D,module_end,7)
        for s in segs:u.mem_write(D+s['p_vaddr'],s.data())
        symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        dyn=elf.get_section_by_name('.dynsym');unresolved=set()
        for r in elf.get_section_by_name('.rela.dyn').iter_relocations():
            typ=r['r_info_type'];value=r['r_addend']
            if typ==1027:value+=D
            elif typ==1025:
                s=dyn.get_symbol(r['r_info_sym'])
                if s['st_shndx']=='SHN_UNDEF':unresolved.add(s.name);value=0
                else:value+=D+s['st_value']
            else:raise AssertionError(('relocation',typ))
            w64(u,D+r['r_offset'],value)
    assert unresolved=={'_ZN2nn2ro6detail15g_pAutoLoadListE',
                        '_ZN2nn2ro6detail35g_LookupGlobalManualFunctionPointerE'}
    def sym(fragment):
        matches=[D+v for k,v in symbols.items() if fragment in k]
        assert len(matches)==1,(fragment,matches)
        return matches[0]
    capture=sym('RawAllocationHook8Callback');getter=sym('RawGetterHook8Callback')
    manager=H+0x100;source=H+0x10000;heap=H+0x70000;ctx=H+0x160000;chunk=H+0x1000
    allocation=[];mode='condition';native_count=0
    def external(uc,at,size,data):
        nonlocal allocation
        if at==M+0x116aee0:
            n=uc.reg_read(G[0]);assert n==native_count*(176 if mode=='condition' else 8)
            allocation.append(n);uc.reg_write(G[0],heap)
        elif at==M+0x12f37d0:
            dst=uc.reg_read(G[0]);v=uc.reg_read(G[1]);n=uc.reg_read(G[2])
            assert dst==heap and v==0 and n==native_count*176
            uc.mem_write(dst,bytes(n))
        elif at in (M+0x12155a0,M+0x12f38a0,D+symbols['snprintf']):uc.reg_write(G[0],0)
        elif at==sym('SvcLogger6LogRaw'):pass
        else:raise AssertionError(hex(at))
        uc.reg_write(ar.UC_ARM64_REG_PC,uc.reg_read(ar.UC_ARM64_REG_LR))
    for at in [M+0x116aee0,M+0x12f37d0,M+0x12155a0,M+0x12f38a0,
               D+symbols['snprintf'],sym('SvcLogger6LogRaw')]:
        u.hook_add(UC_HOOK_CODE,external,begin=at,end=at)
    rows=[]
    for native_count in [0,1,511,512,517,1024]:
        allocation.clear();payload=bytes((i*17+3)%256 for i in range(native_count*176))
        u.mem_write(source,struct.pack('<I',native_count)+payload);w64(u,chunk+0x10,source)
        u.mem_write(heap,b'\xa5'*(176*1024+64))
        u.reg_write(G[0],chunk);u.reg_write(G[19],manager);u.reg_write(ar.UC_ARM64_REG_SP,S+0x8000)
        # Run original reader through its actual count-dependent allocation.
        u.emu_start(M+0x74777c,M+0x7477b0,count=1000)
        assert u.reg_read(ar.UC_ARM64_REG_PC)==M+0x7477b0
        saved=[u.reg_read(x) for x in G];sp=u.reg_read(ar.UC_ARM64_REG_SP);flags=u.reg_read(ar.UC_ARM64_REG_NZCV)
        u.mem_write(ctx,struct.pack('<31Q',*saved))
        # Real compiled inline callback; exlaunch register save/restore modeled.
        call(u,capture,[ctx])
        for r,v in zip(G,saved):u.reg_write(r,v)
        u.reg_write(ar.UC_ARM64_REG_SP,sp);u.reg_write(ar.UC_ARM64_REG_NZCV,flags)
        u.emu_start(M+0x7477b0,M+0x74784c,count=100000)
        assert u.reg_read(ar.UC_ARM64_REG_PC)==M+0x74784c
        assert allocation==[native_count*176]
        assert bytes(u.mem_read(heap,len(payload)))==payload
        assert bytes(u.mem_read(heap+len(payload),64))==b'\xa5'*64
        indexes=sorted({0,1,510,511,512,516,517,1023,1024,0xffffffff,native_count})
        for index in indexes:
            result=call(u,getter,[manager,index])
            assert result==(heap+176*index if index<native_count else 0),(native_count,index,hex(result))
        rows.append({'native_records':native_count,'allocated_bytes':native_count*176,'boundary_cases':len(indexes)})
    # Unknown owner, changed allocation, null table, and null owner fail closed.
    for owner,pointer in [(manager+64,heap),(manager,heap+8),(manager,0)]:
        w64(u,owner+0x18,pointer);assert call(u,getter,[owner,0])==0
    assert call(u,getter,[0,0])==0
    # Reuse beyond registry capacity with native release callbacks. Each
    # destruction must retire its slot, including when the allocator reuses
    # the identical address for the following manager.
    release=sym('RawReleaseHook8Callback')
    for i in range(40):
        owner=manager+0x100+i*0x40
        regs=[0]*31;regs[0]=heap;regs[19]=owner;regs[21]=512
        u.mem_write(ctx,struct.pack('<31Q',*regs));call(u,capture,[ctx]);w64(u,owner+0x18,heap)
        assert call(u,getter,[owner,511])==heap+511*176
        call(u,release,[ctx])
        assert call(u,getter,[owner,0])==0
    # Exercise exlaunch's actual register-saving assembly with the exact entry
    # layout emitted by pinned inline_impl.cpp, then a displaced STR. The
    # entry/trampoline construction is modeled; their instructions execute.
    J=D+module_end;u.mem_map(J,4096,7)
    impl=D+symbols['exl_inline_hook_impl']
    def branch(at,target,link=False):
        delta=target-at;assert delta%4==0 and -(1<<27)<=delta<(1<<27)
        return (0x94000000 if link else 0x14000000)|((delta>>2)&0x3ffffff)
    for callback,displaced in [(capture,0xf9000e60),(release,0xf9000e7f)]:
        entry=struct.pack('<4IQ',0xf81f03fe,branch(J+4,impl,True),0xf85f03fe,branch(J+12,J+0x100),callback)
        u.mem_write(J,entry);u.mem_write(J+0x100,struct.pack('<I',displaced))
        for iteration in range(10):
            values=[0x10000000+i*17+iteration for i in range(31)]
            values[0]=heap;values[19]=manager;values[21]=517;values[30]=STOP
            for r,value in zip(G,values):u.reg_write(r,value)
            u.reg_write(ar.UC_ARM64_REG_SP,S+0x8000)
            u.emu_start(J,J+0x104,count=100000)
            assert u.reg_read(ar.UC_ARM64_REG_PC)==J+0x104
            assert [u.reg_read(r) for r in G]==values
            assert u.reg_read(ar.UC_ARM64_REG_SP)==S+0x8000
            assert qword(u,manager+0x18)==(heap if callback==capture else 0)
    # Run the real compiled installer, modeling only final hook publication.
    w64(u,sym('s_ModuleBitset'),2);w64(u,sym('s_ModuleInfos')+72,M)
    installed=[]
    def install_mock(uc,at,size,data):
        installed.append((uc.reg_read(G[0])-M,uc.reg_read(G[1]),uc.reg_read(G[2])))
        uc.reg_write(G[0],0);uc.reg_write(ar.UC_ARM64_REG_PC,uc.reg_read(ar.UC_ARM64_REG_LR))
    for name in ['nx644HookEmmb','nx6410HookInlineEmmb']:
        at=sym(name);u.hook_add(UC_HOOK_CODE,install_mock,begin=at,end=at)
    installer=D+symbols['_ZN3nsc10conditions22InstallRawStorageHooksEv']
    assert call(u,installer,[])==1
    assert [row[0] for row in installed]==[0x7477b0,0x747658,0x7476ac,0x747708,0x747870]
    fingerprint_sites=list(range(0x747870,0x747890,4))+[0x7477b0,0x747658,0x7476ac,0x747708]
    for off in fingerprint_sites:
        old=bytes(u.mem_read(M+off,4));u.mem_write(M+off,bytes([old[0]^1])+old[1:]);installed.clear()
        assert call(u,installer,[])==0 and not installed
        u.mem_write(M+off,old)
    # Execute the legacy installation chain too, with resolver results already
    # independently verified by the production host resolver test.
    u.mem_write(sym('g_resolved_offsets'),struct.pack('<7q',0x3f4150,0x473190,0x816300,0x766b8c,0x766320,0x7ef098,0x7e6ea8))
    for name,value in [('g_resolver_ready',1),('g_runtime_main_patches_ready',1)]:u.mem_write(sym(name),bytes([value]))
    w64(u,sym('g_uj_session_post_offset'),0x77c5ec);w64(u,sym('g_uj_gate_load_offset'),0x77c474)
    installed.clear()
    legacy=D+next(v for k,v in symbols.items() if 'InstallP128AStaticPreciseGateCaveProofEv' in k)
    call(u,legacy,[])
    assert call(u,installer,[])==1
    u.mem_write(D+symbols['nsc_factory_profile'],encode({281:58}))
    assert call(u,D+symbols['_ZN3nsc7factory19LoadEmbeddedProfileEv'],[])==1
    assert call(u,D+symbols['_ZN3nsc7factory18InstallFactoryHookEv'],[])==1
    hook_offsets=[row[0] for row in installed]
    assert len(hook_offsets)==len(set(hook_offsets)),hook_offsets
    # Inline hooks allocate one trampoline; replacement getter allocates none.
    assert sum(1 for row in installed if row[0]!=0x747870)==19
    assert len(hook_offsets)==20 and installed[-2][2]==0 and 19<=4096//200
    print('Combined installation hook sites:',[hex(x) for x in hook_offsets])
    # PRM manager: run actual patched allocation and prove loop ends at 1024.
    mode='condition';native_count=1024
    # Temporarily replace only the allocation and memset mocks for PRM layout.
    # A separate UC instance prevents overlapping handlers.
    v=Uc(UC_ARCH_ARM64,UC_MODE_ARM);v.mem_map(M,align(len(text)),5);v.mem_write(M,text);v.mem_map(H,0x10000,3)
    v.reg_write(G[0],H);v.mem_write(H+0x1000,b'\xa5'*0x5000)
    def prm_external(uc,at,size,data):
        if at==M+0x116aee0:
            assert uc.reg_read(G[0])==16384;uc.reg_write(G[0],H+0x1000)
        else:
            assert (uc.reg_read(G[0]),uc.reg_read(G[1]),uc.reg_read(G[2]))==(H+0x1000,0,16384)
            uc.mem_write(H+0x1000,bytes(16384))
        uc.reg_write(ar.UC_ARM64_REG_PC,uc.reg_read(ar.UC_ARM64_REG_LR))
    for at in [M+0x116aee0,M+0x12f37d0]:v.hook_add(UC_HOOK_CODE,prm_external,begin=at,end=at)
    v.emu_start(M+0x80fb64,M+0x80fb9c,count=100)
    assert qword(v,H)==H+0x1000 and word(v,H+8)==1024
    assert bytes(v.mem_read(H+0x5000,64))==b'\xa5'*64
    for i in range(1024):
        v.reg_write(G[21],i);v.emu_start(M+0x80fbe0,M+0x80fbec,count=3)
        assert v.reg_read(ar.UC_ARM64_REG_PC)==M+(0x81009c if i==1023 else 0x80fbec)
        v.reg_write(G[20],i);v.emu_start(M+0x876184,M+0x876190,count=3)
        assert v.reg_read(ar.UC_ARM64_REG_PC)==M+(0x876324 if i==1023 else 0x876190)
    # Native char-code loader/getter dynamically bounds stock and larger tables.
    mode='charcode';chars=[]
    for native_count in [281,282,286,400,1024]:
        codes=b''.join(('c%06d'%i).encode()+b'\0' for i in range(1,native_count))
        u.mem_write(source,struct.pack('<I',native_count-1)+codes);u.mem_write(heap,b'\xa5'*0x3000)
        allocation.clear()
        for r,vv in [(19,manager),(24,source),(22,281),(28,int.from_bytes(b'dumm','little')),(29,ord('y'))]:u.reg_write(G[r],vv)
        u.reg_write(ar.UC_ARM64_REG_SP,S+0x8000)
        u.emu_start(M+0x81eb00,M+0x81ebb0,count=30000)
        assert u.reg_read(ar.UC_ARM64_REG_PC)==M+0x81ebb0
        assert allocation==[native_count*8] and word(u,manager+0x18)==native_count
        assert bytes(u.mem_read(heap+8,len(codes)))==codes
        assert bytes(u.mem_read(heap+native_count*8,64))==b'\xa5'*64
        for index in [0,1,280,281,285,399,1023,1024,0xffffffff,native_count]:
            assert call(u,M+0x81f3b0,[manager,index])==(heap+8*index if index<native_count else 0)
        chars.append(native_count)
    report={'status':'PASS','condition_cases':rows,'raw_unknown_rejections':4,'manager_lifecycle_cycles':40,'installer_rejections':12,'inline_register_cases':20,
        'prm_slots':1024,'prm_allocation_bytes':16384,'prm_loop_cases':1024,'spcload_loop_cases':1024,
        'charcode_loader_counts':chars,'charcode_getter_cases':50,
        'combined_hook_sites':[hex(x) for x in hook_offsets],
        'module_sha256':hashlib.sha256(elf_path.read_bytes()).hexdigest(),
        'actual_arm64_executed':True,'emulator_gameplay_tested':False,
        'modeled':['heap allocation','memset','diagnostic formatting/log output',
                   'inline register save/restore in loader orchestration (separately executed in 20 real assembly cases)','hook publication','RTLD relocation; unused imports zeroed'],
        'not_proven':['whole game startup','actual JIT entry/trampoline construction and executable memory publication','resource availability',
                      'actor construction/lifetime','full roster capacity','API completeness']}
    out.mkdir(parents=True,exist_ok=True);(out/'native_storage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--text',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.text,a.elf,a.output)
