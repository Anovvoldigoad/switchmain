"""Compiled Event236 -> native permission writers -> native virtual consumers.

Enemy lookup and diagnostic output are modeled. Real setters/getter, the
callback, and 20 native consumer slices execute; this is not an emulator test.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from unicorn import UC_HOOK_CODE
from arm64_module import *
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.nso_profile import segments
from portlib.prm_events import MARKER

# Independent source contract: PC a2d0f220 MovesetPlus.cpp enable/disable cases.
# These are byte offsets inside the PC permission array, NOT Switch actor fields.
PC_OFFSETS={0:0,19:4,1:8,2:16,3:24,18:28,4:32,5:36,6:40,7:44,
            8:48,9:52,10:56,11:60,12:64,13:68,14:72,15:76,16:80,17:88}
SITES={0:0x7aa33c,1:0x7aa720,2:0x731ea0,4:0x731b0c,6:0x7aa86c,
       7:0x7aac1c,8:0x7aaa78,9:0x7f0264,10:0x7a9af0,11:0x7d00fc,
       12:0x7a9dbc,13:0x7aa1ac,14:0x7a99ac,15:0x7a8fc8,16:0x7a9338,
       17:0x7f6204,18:0x47f598,19:0x7ea78c,20:0x7e1b58,22:0x8046fc}
# Native call instruction -> action table entry. Names are read from the game,
# never supplied as the result of a mocked action lookup.
ACTION_BINDINGS={
 0:[(0x7aa328,191,'PL_ANM_ATK00')],
 3:[(0x7aa8a0,151,'PL_ANM_PRJ_LAND')],
 18:[(0x7aac08,185,'PL_ANM_PRJ_CHA_LAND')],
 4:[(0x7aaa50,248,'PL_ANM_THROW_BEGIN'),(0x7aaa64,247,'PL_ANM_ATK_GUARD_IMP')],
 6:[(0x7a9adc,102,'PL_ANM_GUARDPOSE_0')],
 8:[(0x7a9d8c,77,'PL_ANM_RUN1')],
 9:[(0x7aa184,83,'PL_ANM_JMP0'),(0x7aa198,84,'PL_ANM_JMP1')],
 10:[(0x7a9998,94,'PL_ANM_DSH_BK')],
 12:[(0x7a92e8,97,'PL_ANM_CHADASH_BEGIN'),(0x7a92fc,98,'PL_ANM_CHADASH_LOOP')],
}


def run(main,elf_path,out):
    raw=main.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
    segs=segments(raw);bss=struct.unpack_from('<I',raw,60)[0]
    image=bytearray(align(segs[-1][0]+len(segs[-1][1])+bss))
    for va,data,_ in segs:image[va:va+len(data)]=data
    mod0=struct.unpack_from('<I',image,4)[0];dynamic=mod0+struct.unpack_from('<i',image,mod0+4)[0];tags={}
    for off in range(dynamic,dynamic+4096,16):
        k,v=struct.unpack_from('<QQ',image,off)
        if not k:break
        tags[k]=v
    rel={a:v for off in range(tags[7],tags[7]+tags[8],24)
         for a,k,v in [struct.unpack_from('<QQq',image,off)] if k==1027}
    u,sym,symbols,_=module(elf_path);u.mem_map(M,len(image),7);u.mem_write(M,bytes(image))
    for at,value in rel.items():w64(u,M+at,M+value)
    w64(u,sym('s_ModuleBitset'),2);w64(u,sym('s_ModuleInfos')+72,M)
    init=D+symbols['_ZN3nsc8controls10InitializeEv']
    apply=D+symbols['_ZN3nsc8controls5ApplyEPvssb']
    callback=D+symbols['_ZN3nsc12_GLOBAL__N_112Event236Hook8CallbackEPvS2_']
    w64(u,sym('Event236HookEE7OrigRefEvE7s_FnPtr'),M+0x816300)
    A=H+0x10000;B=H+0x40000;V=H+0x70000;E=H+0x73000
    ENEMY_FN=H+0x74000;HIDE_FN=H+0x75000
    target=B;enemy_calls=0;hide_calls=0
    def ret(v=0):u.reg_write(G[0],v);u.reg_write(ar.UC_ARM64_REG_PC,u.reg_read(ar.UC_ARM64_REG_LR))
    def external(uc,at,n,d):
        nonlocal enemy_calls,hide_calls
        if at==ENEMY_FN:
            assert uc.reg_read(G[0])==A;enemy_calls+=1;ret(target)
        elif at==HIDE_FN:
            assert uc.reg_read(G[0])==B;hide_calls+=1;ret()
        else:ret() # diagnostics only
    for at in [ENEMY_FN,HIDE_FN,D+symbols['snprintf'],sym('SvcLogger6LogRaw')]:
        u.hook_add(UC_HOOK_CODE,external,begin=at,end=at)
    w64(u,V+0xdd0,ENEMY_FN);w64(u,V+0xbc0,HIDE_FN);w64(u,V+0x14c8,M+0x7d4588)
    def reset(char=281,side=0):
        initial=bytearray(b'\xa5'*0x20000);struct.pack_into('<Q',initial,0,V)
        struct.pack_into('<II',initial,0xe50,side,char)
        # Start at a value different from both writers to detect missing writes.
        for i in range(23):struct.pack_into('<I',initial,0x1214c+4*i,0x12345678)
        u.mem_write(A,bytes(initial));u.mem_write(B,bytes(initial));return initial
    def unchanged(initial):
        assert bytes(u.mem_read(A,0x20000))==initial
        assert bytes(u.mem_read(B,0x20000))==initial
    def event(op,selector,enemy=0,marker=MARKER,actor=A):
        data=bytearray(72);struct.pack_into('<HhhhH',data,34,236,op,enemy,selector,marker)
        u.mem_write(E,bytes(data));return call(u,callback,[actor,E])
    initial=reset();assert call(u,apply,[A,0,0,1])==0;unchanged(initial)
    assert call(u,init,[])==1
    rejected=0
    # Each setter/getter fingerprint corruption rejects and clears prior state.
    for base,words in [(0x93c4,5),(0x93d8,6),(0x7d4588,5)]:
        for i in range(words):
            at=M+base+4*i;old=bytes(u.mem_read(at,4))
            u.mem_write(at,bytes([old[0]^1])+old[1:])
            assert call(u,init,[])==0
            initial=reset();assert call(u,apply,[A,0,0,1])==0;unchanged(initial)
            u.mem_write(at,old);assert call(u,init,[])==1;rejected+=1
    cases=0
    for char in [145,281,1023]:
        for enabled in [False,True]:
            for selector,offset in PC_OFFSETS.items():
                for enemy in [0,1,-1,2,-32768,32767]:
                    initial=reset(char);old_enemy=enemy_calls;old_hide=hide_calls
                    assert event(14 if enabled else 15,selector,enemy)==1
                    changed=B if enemy else A;other=A if enemy else B
                    want=bytearray(initial);struct.pack_into('<I',want,0x1214c+offset,int(enabled))
                    if enabled and selector==19:struct.pack_into('<I',want,0x1214c+8,1)
                    assert bytes(u.mem_read(changed,0x20000))==want,(char,enabled,selector,enemy)
                    assert bytes(u.mem_read(other,0x20000))==initial
                    assert enemy_calls-old_enemy==int(enemy!=0) and hide_calls==old_hide
                    assert call(u,M+0x7d4588,[changed,offset//4])==int(enabled)
                    cases+=1
    negatives=0
    for enabled in [False,True]:
        for selector in [-32768,-1,20,21,32767]:
            for enemy in [0,1,-1]:
                initial=reset();old=enemy_calls
                assert event(14 if enabled else 15,selector,enemy)==1
                unchanged(initial);assert enemy_calls==old;negatives+=1
        for missing in ['enemy','vtable','method']:
            initial=reset()
            if missing=='enemy':target=0
            elif missing=='vtable':w64(u,A,0);struct.pack_into('<Q',initial,0,0);w64(u,B,0)
            else:w64(u,V+0xdd0,0)
            assert event(14 if enabled else 15,0,1)==1;unchanged(initial);negatives+=1
            target=B;w64(u,V+0xdd0,ENEMY_FN)
        for char,side in [(1024,0),(281,2),(0xffffffff,0)]:
            initial=reset(char,side);old=enemy_calls
            assert event(14 if enabled else 15,0,1)==1;unchanged(initial)
            assert enemy_calls==old;negatives+=1
        initial=reset();assert call(u,apply,[0,0,0,int(enabled)])==0;unchanged(initial);negatives+=1
    # Numeric control operands must never claim an ordinary native event.
    for op in [14,15]:
        for marker in [0,0x1234]:
            initial=reset();old=hide_calls
            event(op,1,0,marker);unchanged(initial);assert hide_calls-old==1
            negatives+=1
    # Native base-class vtable is relocated from the real game, not guessed.
    native_vtable=rel[0x21436b8]+16
    assert rel[native_vtable+0x14c8]==0x7d4588
    observed=[]
    u.hook_add(UC_HOOK_CODE,lambda uc,a,n,d:observed.append((uc.reg_read(G[0]),uc.reg_read(G[1]))),begin=M+0x7d4588,end=M+0x7d4588)
    cs=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);consumer_rows=[]
    for selector,offset in sorted(PC_OFFSETS.items()):
        index=offset//4;at=SITES[index]
        ins=list(cs.disasm(bytes(image[at-24:at+32]),at-24))
        roots=[i for i in ins if i.address<at and i.mnemonic=='ldr' and i.op_str.startswith('x8, [') and ',' not in i.op_str[5:]]
        start=roots[-1].address
        call_ins=next(i for i in ins if i.address>at and i.mnemonic=='blr')
        assert call_ins.op_str=='x8'
        for enabled in [False,True]:
            reset();assert call(u,apply,[A,0,selector,int(enabled)])==A
            for reg in G:u.reg_write(reg,A)
            u.reg_write(ar.UC_ARM64_REG_SP,S+0xfff0);before=len(observed)
            u.emu_start(M+start,M+call_ins.address+4,count=100)
            assert u.reg_read(ar.UC_ARM64_REG_PC)==M+call_ins.address+4
            assert observed[before:]==[(A,index)]
            assert u.reg_read(G[0])==int(enabled)
        consumer_rows.append({'selector':selector,'index':index,'start':hex(start),'call':hex(call_ins.address)})
    action_rows=[]
    for selector,bindings in ACTION_BINDINGS.items():
        for at,index,name in bindings:
            ins=list(cs.disasm(bytes(image[at-24:at+4]),at-24))
            assert ins[-1].mnemonic=='bl' and ins[-1].op_str=='#0x768e84'
            arg=next(i for i in reversed(ins[:-1]) if i.mnemonic=='mov' and i.op_str.startswith('w1, #'))
            assert int(arg.op_str.split('#')[1],0)==index,(hex(at),arg.op_str,index)
            p=call(u,M+0x80f170,[0,index]);actual=bytes(u.mem_read(p,128)).split(b'\0',1)[0].decode()
            assert actual==name,(selector,index,actual,name)
            action_rows.append({'selector':selector,'call':hex(at),'action_id':index,'native_name':actual})
    report={'status':'PASS','event_control_cases':cases,'negative_cases':negatives,
      'fingerprint_mutations_rejected':rejected,'native_consumer_cases':len(consumer_rows)*2,
      'native_consumers':consumer_rows,'native_action_bindings':action_rows,
      'compiled_callback_executed':True,'source_enable19_fallthrough_preserved':True,
      'native_setter_offset':'0x93d8','native_clear_offset':'0x93c4','native_permission_array':'0x1214c',
      'module_elf_sha256':hashlib.sha256(elf_path.read_bytes()).hexdigest(),
      'modeled':['OS/RTLD loading','live actor allocations','enemy virtual method','diagnostic output'],
      'not_proven':['semantic action labels for every selector','all subclass permission overrides',
                    'full surrounding consumer functions','legacy UJ latch lifetime','emulator gameplay'],
      'gameplay_verified':False,'full_moddingapi':False}
    out.mkdir(parents=True,exist_ok=True);(out/'native_controls.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Native controls:',cases,'event cases,',negatives,'negative cases,',len(consumer_rows)*2,'consumer cases PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.elf,a.output)
