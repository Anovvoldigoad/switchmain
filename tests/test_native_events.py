"""Real PRM reader -> explicit API marker -> compiled Event236 callback.
Native dispatch timing/filtering and vanilla enemy-hide execute unmodified.
"""
import argparse, hashlib, json, struct, sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from arm64_module import *
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.prm_events import records, mark, has_damage, MARKER
from portlib.nso_profile import segments


def run(main,elf_path,out,prm=None):
    raw=main.read_bytes();assert hashlib.sha256(raw).hexdigest()=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
    segs=segments(raw);bss=struct.unpack_from('<I',raw,60)[0]
    size=align(segs[-1][0]+len(segs[-1][1])+bss)
    image=bytearray(size)
    for va,data,_ in segs:image[va:va+len(data)]=data
    mod0=struct.unpack_from('<I',image,4)[0];dynamic=mod0+struct.unpack_from('<i',image,mod0+4)[0];tags={}
    for off in range(dynamic,dynamic+4096,16):
        key,value=struct.unpack_from('<QQ',image,off)
        if not key:break
        tags[key]=value
    u,sym,symbols,module_end=module(elf_path);u.mem_map(M,size,7);u.mem_write(M,bytes(image))
    for off in range(tags[7],tags[7]+tags[8],24):
        at,kind,value=struct.unpack_from('<QQq',image,off)
        if kind==1027:w64(u,M+at,M+value)
    SRC=H+0x1000;DST=H+0x3000;MAN=H+0x4000;DAMAGE=H+0x5000
    ACTOR=H+0x10000;ENEMY=H+0x30000;VTABLE=H+0x60000;EVTABLE=H+0x62000
    ENEMY_FN=H+0x64000;HIDE_FN=H+0x65000;STATE=H+0x66000
    CLOCK=H+0x67000;SPEEDPTR=H+0x68000;SPEED=H+0x69000
    w64(u,M+0x2143718,CLOCK);u.mem_write(CLOCK,struct.pack('<I',30))
    w64(u,M+0x2143658,SPEEDPTR);w64(u,SPEEDPTR,SPEED);u.mem_write(SPEED+0xa02,b'\x1e')
    counts={'hide':0,'enemy':0,'damage_allocations':0}
    enemy_present=True
    def ret(value=0):u.reg_write(G[0],value&0xffffffffffffffff);u.reg_write(ar.UC_ARM64_REG_PC,u.reg_read(ar.UC_ARM64_REG_LR))
    def cstring(p):
        b=bytes(u.mem_read(p,256));assert b'\0' in b;return b.split(b'\0',1)[0]
    def external(uc,at,n,d):
        if at==M+0x116ae60:
            assert uc.reg_read(G[0])==96;counts['damage_allocations']+=1;u.mem_write(DAMAGE,b'\xa5'*96);ret(DAMAGE)
        elif at==M+0x12f3770:
            a,b=cstring(uc.reg_read(G[0])),cstring(uc.reg_read(G[1]));ret((a>b)-(a<b))
        elif at==M+0x12f36d0:ret(len(cstring(uc.reg_read(G[0]))))
        elif at==M+0x3f4b40:ret(42)
        elif at==ENEMY_FN:
            assert uc.reg_read(G[0])==ACTOR;counts['enemy']+=1;ret(ENEMY if enemy_present else 0)
        elif at==HIDE_FN:
            assert uc.reg_read(G[0])==ENEMY;counts['hide']+=1;ret()
        else:ret() # diagnostic snprintf/LogRaw only
    for at in [M+0x116ae60,M+0x12f3770,M+0x12f36d0,M+0x3f4b40,ENEMY_FN,HIDE_FN,D+symbols['snprintf'],sym('SvcLogger6LogRaw')]:
        u.hook_add(UC_HOOK_CODE,external,begin=at,end=at)
    # The exact native reader produces a 72-byte event from a 64/160-byte raw
    # record, replacing damage payload with a pointer while preserving params.
    reader_cases=0
    def read_record(record,width):
        nonlocal reader_cases
        u.mem_write(SRC,record+bytes(256));u.mem_write(DST-16,b'\xa5'*104)
        w64(u,MAN+8,DST)
        u.reg_write(ar.UC_ARM64_REG_SP,S+0x8000)
        u.mem_write(S+0x80c0,struct.pack('<I',1))
        for reg,val in [(27,SRC),(29,MAN),(28,0),(24,0),(26,0)]:u.reg_write(G[reg],val)
        # Native event-specific damage predicate and all field copies execute.
        u.emu_start(M+0x81d120,M+0x81d384,count=100000)
        assert u.reg_read(ar.UC_ARM64_REG_PC)==M+0x81d384
        assert u.reg_read(G[27])==SRC+width,(record[34:36].hex(),width,hex(u.reg_read(G[27])))
        result=bytes(u.mem_read(DST,72))
        assert result[:48]==record[:48]
        assert result[56:68]==record[52:64]
        assert bytes(u.mem_read(DST-16,16))==b'\xa5'*16
        assert bytes(u.mem_read(DST+72,16))==b'\xa5'*16
        reader_cases+=1
        return result
    # Independent native predicate for every in-range event and signed extremes.
    predicate_cases=0
    for event in list(range(302))+[0x7fff,0x8000,0xffff]:
        v=call(u,M+0x7938d0,[event]);expected=event==94 or (193<=event<=217 and (0x015502A5>>(event-193))&1)
        assert v==int(bool(expected));predicate_cases+=1
    for event in list(range(302))+[0x7fff,0xffff]:
        for following in [b'none\0',b'SKL_ATK_TEST\0',b'SPSKILL_END\0']:
            record=bytearray(160);record[64:64+len(following)]=following
            struct.pack_into('<H',record,34,event);struct.pack_into('<H',record,42,MARKER)
            read_record(bytes(record),160 if has_damage(event,following) else 64)
    real_report=None
    if prm:
        original=prm.read_bytes();converted,real_report=mark(original)
        assert mark(converted)[0]==converted
        parsed=records(original)
        for row in parsed:
            off=row['offset'];width=row['size']
            before=read_record(original[off:off+width],width)
            after=read_record(converted[off:off+width],width)
            expected=bytearray(before)
            if row['event']==236 and 1<=struct.unpack_from('<h',original,off+36)[0]<=29:
                struct.pack_into('<H',expected,42,MARKER)
            assert after==expected
        real_report={k:v for k,v in real_report.items() if k!='changes'}
    callback=D+symbols['_ZN3nsc12_GLOBAL__N_112Event236Hook8CallbackEPvS2_']
    w64(u,sym('Event236HookEE7OrigRefEvE7s_FnPtr'),M+0x816300)
    # Publish callback in the exact native member-function table. The callback
    # still invokes the original native handler for every unmarked record.
    w64(u,M+0x2078f68,callback)
    dispatch_cases=0
    for char in [0,145,276,280,281,1023,1024]:
        for side in [0,1,2]:
            for marker in [0,MARKER,0x1234]:
                for operation in [0,3,30]:
                    for enemy_present in [False,True]:
                        u.mem_write(ACTOR,bytes(0x20000));u.mem_write(ENEMY,bytes(0x20000))
                        w64(u,ACTOR,VTABLE);w64(u,ENEMY,EVTABLE)
                        w64(u,VTABLE+0xdd0,ENEMY_FN);w64(u,EVTABLE+0xbc0,HIDE_FN)
                        u.mem_write(ACTOR+0xe50,struct.pack('<II',side,char))
                        event=bytearray(64);struct.pack_into('<hhhhHH',event,32,0,236,operation,0,6,marker)
                        loaded=read_record(bytes(event),64);u.mem_write(DST,loaded)
                        u.mem_write(STATE,bytes(512));w64(u,S+0xfff0,STATE)
                        before=bytes(u.mem_read(ACTOR,0x20000));old_hide=counts['hide'];old_enemy=counts['enemy']
                        # Run native dispatcher at frame0 with no event filter.
                        call(u,M+0x782e44,[ACTOR,DST,1,0xffffffff,0xffffffff,1,1,0])
                        tagged=marker==MARKER
                        applied=tagged and operation==3 and side<=1 and char<1024
                        expected=bytearray(before)
                        if applied:struct.pack_into('<I',expected,0xe68,6)
                        assert bytes(u.mem_read(ACTOR,0x20000))==expected
                        assert counts['enemy']-old_enemy==int(not tagged)
                        assert counts['hide']-old_hide==int(not tagged and enemy_present)
                        assert struct.unpack('<I',u.mem_read(STATE,4))[0]==2
                        dispatch_cases+=1
    report={'status':'PASS','native_reader_cases':reader_cases,'native_damage_predicate_cases':predicate_cases,
            'native_dispatch_cases':dispatch_cases,'real_prm':real_report,
            'module_elf_sha256':hashlib.sha256(elf_path.read_bytes()).hexdigest(),
            'native_functions':['reader 0x81d120..0x81d384','damage predicate 0x7938d0','dispatcher 0x782e44','enemy-hide 0x816300'],
            'compiled_callback_executed':True,'marker':hex(MARKER),'roster_id_threshold_removed':True,
            'modeled':['OS/RTLD relocation','table callback publication','damage allocator/string helpers','enemy lookup and enemy visibility method bodies','diagnostic output'],
            'not_proven':['complete resource loader lifetime','all API operation effects','emulator gameplay'],
            'gameplay_verified':False,'full_moddingapi':False}
    out.mkdir(parents=True,exist_ok=True);(out/('native_events_real_prm.json' if prm else 'native_events.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('Native PRM reader',reader_cases,'cases; event dispatch',dispatch_cases,'cases PASS')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--prm',type=Path)
    a=p.parse_args();run(a.main,a.elf,a.output,a.prm)
