"""Compiled profile/getter with native name/hash lookup and descriptor consumers.

OS hook publication, libc strcmp/strlen and selected caller contexts are modeled.
The native CRC, four lookup loops and original getter instructions execute.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from arm64_module import *
from native_condition_fixture import native_image,baseline_from_main
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.condition_profile import encode,PROFILE_SIZE


def crc_name(name):
    v=0xffffffff
    for ch in name.encode():
        v^=ch<<24
        for _ in range(8):v=((v<<1)^(0x04c11db7 if v&0x80000000 else 0))&0xffffffff
    return (~v)&0xffffffff


def run(main,elf,out):
    image,rel=native_image(main);_,native=baseline_from_main(main)
    u,sym,symbols,end=module(elf);u.mem_map(M,len(image),7);u.mem_write(M,bytes(image))
    for at,value in rel.items():w64(u,M+at,M+value)
    w64(u,sym('s_ModuleBitset'),2);w64(u,sym('s_ModuleInfos')+72,M)
    load=sym('condition_profile11LoadProfile');getter=sym('ConditionGetterHook8Callback')
    PROFILE=H+0x10000;TEXT=H+0x20000;PARAM=H+0x30000;TRAMP=H+0x40000
    # Original getter has one ADRP. Relocate it as a literal load of its native
    # page; all seven following native instructions execute unchanged.
    u.mem_write(TRAMP,struct.pack('<I',0x5800010a)+bytes(image[0x754a84:0x754aa0]))
    w64(u,TRAMP+32,M+0x214d000)
    w64(u,sym('ConditionGetterHookEE7OrigRefEvE7s_FnPtr'),TRAMP)
    stop_sites=set();stopped=0
    installed=[];installer=sym('InstallConditionCompatEv');install_fn=sym('nx644HookEmmb')
    log_sites={D+symbols['snprintf'],sym('SvcLogger6LogRaw')}
    def cstring(p):
        assert p
        out=bytearray()
        for i in range(256):
            c=u.mem_read(p+i,1)[0]
            if not c:return bytes(out)
            out.append(c)
        raise AssertionError('unterminated native name')
    def ret(v):u.reg_write(G[0],v&0xffffffffffffffff);u.reg_write(ar.UC_ARM64_REG_PC,u.reg_read(ar.UC_ARM64_REG_LR))
    def hook(uc,at,n,d):
        nonlocal stopped
        if at==install_fn:
            installed.append(uc.reg_read(G[0])-M);ret(0)
        elif at in log_sites:ret(0)
        elif at in stop_sites:stopped=at;uc.reg_write(ar.UC_ARM64_REG_PC,STOP)
        elif at==M+0x754a80:uc.reg_write(ar.UC_ARM64_REG_PC,getter)
        elif at==M+0x12f36e0:
            a,b=cstring(uc.reg_read(G[0])),cstring(uc.reg_read(G[1]));ret((a>b)-(a<b))
        elif at==M+0x12f36d0:ret(len(cstring(uc.reg_read(G[0]))))
    for at in [M+0x754a80,M+0x12f36e0,M+0x12f36d0,M+0x777504,M+0x777514,M+0x777a44,M+0x777a98,
               M+0x7eb708,M+0x7eb700,M+0x553b44,M+0x553b88,M+0x746d30,M+0x746d84,M+0x1ef2a0,M+0x1ef2a4]:
        u.hook_add(UC_HOOK_CODE,hook,begin=at,end=at)
    for at in [install_fn,*log_sites]:u.hook_add(UC_HOOK_CODE,hook,begin=at,end=at)
    installer_cases=0;installer_rejections=0
    original_table=bytes(u.mem_read(M+0x20736c8,512*32));cases=0;lookups=0;consumer_cases=0
    for n in [0,1,5,512]:
        rows=[dict(name=f'PORT_COND_{i:04}',reaction=(512+(i+1)%n),state=i%25,icon=i%41,status=i%6,aura=i%109) for i in range(n)]
        if n:rows[0].update(state=1,reaction=1,aura=107)
        p=encode(rows);u.mem_write(PROFILE,p)
        assert call(u,load,[PROFILE,len(p)],instruction_budget=50000000)==1
        total=512+n
        for off,reg in [(0x7774dc,24),(0x777770,19),(0x777938,19),(0x777a6c,19)]:
            # Production patch-count generation is independently executed by
            # test_bootstrap. Here install its exact expected ARM64 cmp words.
            u.mem_write(M+off,struct.pack('<I',0x7100001f|(total<<10)|(reg<<5)))
            u.ctl_remove_cache(M+off,M+off+4)
        installed.clear();assert call(u,installer,[])==1
        assert installed==[0x754a80,0x8134f8];installer_cases+=1
        if n==5:
            sites=list(range(0x754a80,0x754aa0,4))+list(range(0x8134f8,0x813518,4))+[0x747878,0x7774dc,0x777770,0x777938,0x777a6c]
            for at in sites:
                old=bytes(u.mem_read(M+at,4));bad=bytes([old[0]^1])+old[1:]
                u.mem_write(M+at,bad);installed.clear()
                assert call(u,installer,[])==0 and not installed
                u.mem_write(M+at,old);u.ctl_remove_cache(M+at,M+at+4);installer_rejections+=1
        w64(u,sym('ConditionGetterHookEE7OrigRefEvE7s_FnPtr'),TRAMP)
        for i in range(total):
            ptr=call(u,getter,[i]);cases+=1
            if i==0:assert ptr==0;continue
            expected=(native[i][0],native[i][1]) if i<512 else (rows[i-512]['name'],tuple(rows[i-512][f] for f in ['reaction','state','icon','status','aura'])+(0,))
            assert (cstring(qword(u,ptr)).decode(),struct.unpack('<6I',u.mem_read(ptr+8,24)))==expected
            if i<512:assert ptr==M+0x20736c8+i*32
        for i in [total,total+1,0xffffffff]:assert call(u,getter,[i])==0;cases+=1
        assert bytes(u.mem_read(M+0x20736c8,512*32))==original_table
        indexes=sorted({1,103,511,*([512,total-1,512+n//2] if n else [])})
        queries=[(native[i][0] if i<512 else rows[i-512]['name'],i) for i in indexes]
        queries += [('ABSENT_CONDITION',0),('DUMMY',0),('',0)]
        for name,expected in queries:
            u.mem_write(TEXT,name.encode()+b'\0');u.mem_write(PARAM+0x1e4,name.encode()+b'\0')
            found=call(u,M+0x777758,[TEXT])
            assert found==expected,(n,name,found,expected)
            assert call(u,M+0x12154d0,[TEXT])==crc_name(name)
            assert call(u,M+0x777920,[crc_name(name)])==expected
            for start,sites,register in [(0x7774d0,[0x777504,0x777514],24),(0x777a58,[0x777a44,0x777a98],19)]:
                stop_sites={M+x for x in sites};stopped=0
                u.reg_write(G[25],TEXT);u.reg_write(G[0],PARAM);u.reg_write(ar.UC_ARM64_REG_SP,S+0xf000)
                u.emu_start(M+start,STOP,count=2000000)
                assert stopped in stop_sites
                got=u.reg_read(G[register]) if stopped==M+sites[0] else 0
                assert got==expected,(n,name,hex(start),got,expected)
                stop_sites=set()
            lookups+=4
        # Native state predicate, reaction, icon/status and state->aura slices.
        for i in indexes+[0,total]:
            ptr=call(u,getter,[i]);fields=struct.unpack('<6I',u.mem_read(ptr+8,24)) if ptr else None
            assert call(u,M+0x775fe0,[0,i])==int(bool(fields and fields[1]==1));consumer_cases+=1
            for start,ends,reg,field in [(0x7eb6fc,[0x7eb708],0,0),(0x553b3c,[0x553b44,0x553b88],0,None),
                                        (0x746d24,[0x746d30,0x746d84],20,3)]:
                stop_sites={M+x for x in ends};stopped=0
                u.reg_write(G[0],i);u.reg_write(ar.UC_ARM64_REG_SP,S+0xf000)
                u.emu_start(M+start,STOP,count=1000);assert stopped in stop_sites
                if fields:
                    if field is None:
                        assert stopped==M+0x553b44
                        stop_sites=set()
                        u.emu_start(M+0x553b44,M+0x553b48,count=1);assert u.reg_read(G[29])==fields[2]
                    else:assert u.reg_read(G[reg])==fields[field]
                consumer_cases+=1;stop_sites=set()
            stop_sites={M+0x1ef2a0,M+0x1ef2a4};stopped=0;u.reg_write(G[0],i);u.reg_write(G[19],PARAM)
            u.emu_start(M+0x1ef284,STOP,count=1000)
            if fields and fields[1]==1:
                assert stopped==M+0x1ef2a0 and u.reg_read(G[0])==PARAM and u.reg_read(G[1])==fields[4]
            else:assert stopped==M+0x1ef2a4
            stop_sites=set();consumer_cases+=1
        # A bad update cannot invalidate active descriptor pointers/count.
        bad=bytearray(p);bad[0]^=1;u.mem_write(PROFILE,bytes(bad))
        assert call(u,load,[PROFILE,len(bad)],instruction_budget=50000000)==0
        assert call(u,getter,[total])==0
    report={'status':'PASS','descriptor_getter_cases':cases,'native_lookup_cases':lookups,
        'native_field_consumer_cases':consumer_cases,'total_count_cases':[512,513,517,1024],
        'installer_count_cases':installer_cases,'installer_fingerprint_rejections':installer_rejections,
        'native_prefix_byte_identical':True,'native_crc_executed':True,'native_fields':['reaction','state','icon','status','aura'],
        'module_elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
        'modeled':['hook publication and original getter ADRP relocation','diagnostic formatting/output','libc strcmp/strlen','caller contexts for two name-loop and field-consumer slices'],
        'not_proven':['raw 176-byte conditionprm packaging/order','effect-resource compatibility','full condition application/retirement','emulator gameplay'],
        'gameplay_verified':False,'full_moddingapi':False}
    out.mkdir(parents=True,exist_ok=True);(out/'native_conditions.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.elf,a.output)
