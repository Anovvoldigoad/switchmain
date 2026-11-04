"""Compiled profile + callback against the real native Switch factory.

All selected native dispatch branches execute. Concrete constructors/OS state
are modeled in routing tests; a separate identity slice executes the 2dnz
wrappers with only deep base construction and selected helpers modeled.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from arm64_module import *
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
from portlib.factory_profile import encode, catalog
from portlib.nso_profile import segments


def run(main,elf_path,out):
    original=main.read_bytes()
    assert hashlib.sha256(original).hexdigest()=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
    rows=segments(original)
    bss=struct.unpack_from('<I',original,60)[0]
    image=bytearray(align(rows[-1][0]+len(rows[-1][1])+bss))
    for va,raw,_ in rows: image[va:va+len(raw)]=raw
    mod0=struct.unpack_from('<I',image,4)[0]
    dynamic=mod0+struct.unpack_from('<i',image,mod0+4)[0];tags={}
    for off in range(dynamic,dynamic+4096,16):
        k,v=struct.unpack_from('<QQ',image,off)
        if k==0: break
        tags[k]=v
    rel={}
    for off in range(tags[7],tags[7]+tags[8],24):
        a,k,v=struct.unpack_from('<QQq',image,off)
        if k==1027: rel[a]=v
    table={struct.unpack_from('<I',image,0x205e010+16*i)[0]:rel[0x205e008+16*i] for i in range(82)}
    assert table[58]==0x7cc8e0
    u,sym,symbols,module_end=module(elf_path)
    u.mem_map(M,len(image),7);u.mem_write(M,bytes(image))
    for at,value in rel.items(): w64(u,M+at,M+value)
    J=D+module_end;u.mem_map(J,4096,7)
    factory=M+0x7cab00
    callback=sym('PlayerFactoryHook8Callback')
    def abs_jump(target): return struct.pack('<IIQ',0x58000051,0xd61f0220,target) # ldr x17,+8; br x17
    # Modeled publication with the exact position-independent displaced prefix;
    # no code in this prefix requires instruction relocation.
    u.mem_write(J,bytes(image[0x7cab00:0x7cab10])+abs_jump(M+0x7cab10))
    trampoline=sym('PlayerFactoryHookEE7OrigRefEvE7s_FnPtr')
    w64(u,trampoline,J)
    load=sym('LoadEmbeddedProfileEv');installer=D+symbols['_ZN3nsc7factory18InstallFactoryHookEv']
    profile=D+symbols['nsc_factory_profile']
    w64(u,sym('s_ModuleBitset'),2);w64(u,sym('s_ModuleInfos')+72,M)
    installed=[]
    def ret(value=0):
        u.reg_write(G[0],value);u.reg_write(ar.UC_ARM64_REG_PC,u.reg_read(ar.UC_ARM64_REG_LR))
    def install_mock(uc,at,size,data):
        installed.append((uc.reg_read(G[0]),uc.reg_read(G[1]),uc.reg_read(G[2])))
        ret(J)
    u.hook_add(UC_HOOK_CODE,install_mock,begin=sym('nx644HookEmmb'),end=sym('nx644HookEmmb'))
    for at in [D+symbols['snprintf'],sym('SvcLogger6LogRaw')]:
        u.hook_add(UC_HOOK_CODE,lambda uc,a,n,d:ret(),begin=at,end=at)
    assert call(u,load,[])==1 and call(u,installer,[])==1 and not installed
    supported=[r['selector'] for r in catalog().values() if r['supported']]
    mappings={400+i:selector for i,selector in enumerate(supported)}
    mappings.update({145:58,276:1,281:58,1023:280})
    u.mem_write(profile,encode(mappings));assert call(u,load,[])==1
    assert call(u,installer,[])==1
    assert len(installed)==1 and installed[0][0]==factory and installed[0][1]==callback
    # Every fingerprint word independently rejects before publication.
    for off in range(0,24,4):
        at=factory+off;old=bytes(u.mem_read(at,4));u.mem_write(at,bytes([old[0]^1])+old[1:]);installed.clear()
        assert call(u,installer,[])==0 and not installed
        u.mem_write(at,old)
    # Installer mock does not update the template's real s_Trampoline member.
    w64(u,trampoline,J)
    flags=set();trace=[];entry=[]
    ACTOR=H+0x10000;MANAGER=H+0x40000;GLOBAL=H+0x50000;FLAGS=H+0x60000
    MODEPTR=H+0x70000;MODE=H+0x71000;SPECIALPTR=H+0x72000;SPECIAL=H+0x73000
    VTABLE=H+0x74000;VGET=J+0x200
    w64(u,M+0x2143488,GLOBAL);w64(u,GLOBAL+0x6c88,MANAGER);w64(u,MANAGER+0x50,0)
    w64(u,M+0x2143648,FLAGS);w64(u,FLAGS+0x50,FLAGS+0x100)
    w64(u,M+0x21434c0,MODEPTR);w64(u,MODEPTR,MODE)
    w64(u,M+0x21445b8,SPECIALPTR);w64(u,SPECIALPTR,SPECIAL)
    w64(u,VTABLE+0x20,VGET);u.mem_write(VGET,struct.pack('<I',0xd65f03c0))
    md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    calls={int(i.op_str[1:],16) for i in md.disasm(bytes(image[0x7cab00:0x7cbc7c]),0x7cab00) if i.mnemonic=='bl'}
    constructors=calls-{0xecad40,0x116ae60}
    table_functions=set(table.values())|{0x7cbc80}
    def external(uc,at,size,data):
        off=at-M
        if at==VGET: ret(41)
        elif off==0xecad40:
            flag=uc.reg_read(G[1]);trace.append(('flag',flag));ret(int(flag in flags))
        elif off==0x116ae60:
            trace.append(('allocate',uc.reg_read(G[0]),uc.reg_read(G[2])));ret(ACTOR)
        elif off in table_functions:
            trace.append(('table',off));ret(H+0x10000000+off)
        elif off in constructors:
            trace.append(('constructor',off));w64(u,ACTOR,VTABLE)
            u.mem_write(ACTOR+0x48,struct.pack('<I',41));ret(ACTOR)
        else: raise AssertionError(hex(at))
    handles={}
    for off in table_functions|calls:
        handles[off]=u.hook_add(UC_HOOK_CODE,external,begin=M+off,end=M+off)
    u.hook_add(UC_HOOK_CODE,external,begin=VGET,end=VGET)
    def entry_hook(uc,a,n,d):entry.append((uc.reg_read(G[0])&0xffffffff,uc.reg_read(G[1])&0xffffffff))
    u.hook_add(UC_HOOK_CODE,entry_hook,begin=M+0x7cab10,end=M+0x7cab10)
    def native(code,mode):
        trace.clear();entry.clear()
        result=call(u,factory,[code,mode])
        assert entry==[(code,mode)]
        return result,list(trace)
    def adapted(code,mode):
        trace.clear();entry.clear()
        result=call(u,callback,[code,mode])
        assert entry==[(mappings.get(code,code),mode)]
        return result,list(trace)
    # Native game flags are inputs, not patched bypasses. Execute each chained
    # single-flag fallback as well as all enabled/all disabled.
    flag_ids=[0xa2,0xa5,0xaf,0xc5,0xe6,0x115,0x118,0x11a,0x11c,0x11e,0x120,0x121,0x123,0x125,0x127]
    states=[set(),set(flag_ids)]+[{x} for x in flag_ids]
    routes=set();cases=0
    for state_index,flags in enumerate(states):
        u.mem_write(MODE+0xb90,struct.pack('<I',[0,0x1a,0xcc][state_index%3]))
        u.mem_write(SPECIAL+0x68,struct.pack('<I',2 if state_index%2 else 0))
        for owner,selector in mappings.items():
            for mode in [0,1,0xffffffff]:
                want=native(selector,mode);got=adapted(owner,mode)
                assert got==want,(owner,selector,mode,flags,got,want)
                routes.update(tuple(r) for r in got[1]);cases+=1
        for owner in [0,11,280,282,399,1024,65535,0xffffffff]:
            for mode in [0,1,0xffffffff]:
                assert adapted(owner,mode)==native(owner,mode);cases+=1
    # Real caller through modeled entry publication: preserve original roster ID.
    # Let the native 2dnz allocation/registration wrapper and constructors run.
    u.hook_del(handles[0x7cc8e0])
    base_calls=[]
    vtable=rel[0x2149cc0]+16
    reset=rel[vtable+0x10]
    def base_model(uc,at,size,data):
        off=at-M;base_calls.append(off)
        if off==0x7cf3dc:
            assert uc.reg_read(G[0])==ACTOR and uc.reg_read(G[1])==MANAGER
            uc.mem_write(ACTOR,bytes(0x12460));uc.mem_write(ACTOR+0x48,struct.pack('<I',41));uc.mem_write(ACTOR+0xcc4,b'\xff'*4);ret(ACTOR)
        elif off==0x116d3c0:assert uc.reg_read(G[0])==12;ret()
        elif off in [0x116d420,0x75bfac,reset]:ret()
        else:raise AssertionError(hex(off))
    for off in [0x7cf3dc,0x116d3c0,0x116d420,0x75bfac,reset]:
        u.hook_add(UC_HOOK_CODE,base_model,begin=M+off,end=M+off)
    u.mem_write(factory,abs_jump(callback));u.ctl_remove_cache(factory,factory+16)
    CODE=H+0x76000;SLOTREC=H+0x77000;CONFIG=H+0x78000
    identity_cases=[]
    for owner in [145,281,400+supported.index(58)]:
        for mode in [0,1,0xffffffff]:
            for side in [0,1]:
                trace.clear();base_calls.clear()
                u.mem_write(ACTOR-64,b'\xa5'*(0x12460+128))
                u.mem_write(CODE,struct.pack('<I',owner));u.mem_write(SLOTREC+0x2fc,struct.pack('<I',mode))
                for reg,val in [(26,CODE),(28,SLOTREC),(21,side),(25,7),(24,CONFIG),(29,123)]:u.reg_write(G[reg],val)
                u.reg_write(ar.UC_ARM64_REG_SP,S+0x8000);u.reg_write(ar.UC_ARM64_REG_LR,STOP)
                u.emu_start(M+0x722f24,M+0x7589a0,count=200000)
                assert u.reg_read(ar.UC_ARM64_REG_PC)==M+0x7589a0
                assert qword(u,ACTOR)==M+vtable
                assert struct.unpack('<III',u.mem_read(ACTOR+0xe54,12))==(owner,7,0)
                assert struct.unpack('<I',u.mem_read(ACTOR+0xe60,4))[0]==mode
                assert u.reg_read(G[25])==side
                assert bytes(u.mem_read(CODE,4))==struct.pack('<I',owner)
                assert bytes(u.mem_read(ACTOR-64,64))==b'\xa5'*64
                assert bytes(u.mem_read(ACTOR+0x12460,64))==b'\xa5'*64
                assert trace==[('allocate',0x12460,0x26)],trace
                assert base_calls.count(0x7cf3dc)==1
                identity_cases.append({'owner':owner,'mode':mode,'side':side})
    report={'status':'PASS','routing_cases':cases,'native_state_scenarios':len(states),'supported_selectors':len(supported),
            'mapping_count':len(mappings),'native_routes_observed':[list(r) for r in sorted(routes)],
            'identity_cases':identity_cases,'installer_fingerprint_rejections':6,
            'module_elf_sha256':hashlib.sha256(elf_path.read_bytes()).hexdigest(),
            'modeled':['OS/RTLD relocation','hook entry/trampoline publication (instructions execute)',
                       'game global flags/mode values','all concrete constructors in dispatch comparison',
                       'allocator, empty registration tree, locks, deep base constructor and selected reset helpers in identity test'],
            'executed':['compiled registry/profile SHA256 checks','compiled factory installer and callback',
                        'full native factory dispatch','2dnz wrapper + two outer constructors for identity tests',
                        'native caller and initialization prefix through 0x75899c'],
            'not_proven':['deep actor construction','nonempty registration tree','initialization after 0x75899c',
                          'new-slot resources','actor destruction','PC globals reset parity','gameplay or emulator compatibility'],
            'gameplay_verified':False,'full_moddingapi':False}
    out.mkdir(parents=True,exist_ok=True);(out/'native_factory.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Factory native dispatch:',cases,'cases;',len(identity_cases),'identity cases PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.elf,a.output)
