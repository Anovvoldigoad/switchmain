"""Compiled CPK hook/profile against the native game binder wrapper/manager.

The native manager's real error branches execute, including success-without-ID.
CRI file IO, allocation, object construction, priority service and locking are
modeled; this proves registration routing, not completed archive/resource loads.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from arm64_module import *
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.cpk_profile import encode,PROFILE_SIZE
from portlib.nso_profile import segments


def run(main,elf_path,out):
    raw=main.read_bytes();assert hashlib.sha256(raw).hexdigest()=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
    segs=segments(raw);bss=struct.unpack_from('<I',raw,60)[0]
    im=bytearray(align(segs[-1][0]+len(segs[-1][1])+bss))
    for va,b,_ in segs:im[va:va+len(b)]=b
    mod=struct.unpack_from('<I',im,4)[0];dyn=mod+struct.unpack_from('<i',im,mod+4)[0];tags={}
    for off in range(dyn,dyn+4096,16):
        k,v=struct.unpack_from('<QQ',im,off)
        if not k:break
        tags[k]=v
    u,sym,symbols,_=module(elf_path);u.mem_map(M,len(im),7);u.mem_write(M,bytes(im))
    for off in range(tags[7],tags[7]+tags[8],24):
        at,k,v=struct.unpack_from('<QQq',im,off)
        if k==1027:w64(u,M+at,M+v)
    callback=D+symbols['_ZN3nsc12_GLOBAL__N_111CpkBindHook8CallbackEPNS_3cpk7PathArgEPji']
    w64(u,sym('CpkBindHookEE7OrigRefEvE7s_FnPtr'),M+0x473190)
    load=sym('cpk11LoadProfile');count=sym('cpk15RegisteredCount');binding=sym('cpk9BindingId')
    PROFILE=H+0x1000;DESC=H+0x4000;PATH=H+0x5000;OUT=H+0x6000
    GLOBAL=H+0x7000;ROOT=H+0x8000;HANDLE=H+0x9000;V=H+0xa000;DELETE=H+0xb000
    POOL=H+0x20000;VECTOR=H+0x100000
    w64(u,M+0x2149bd8,GLOBAL);w64(u,GLOBAL,ROOT);w64(u,ROOT+0x18,HANDLE)
    w64(u,ROOT+0x20,VECTOR);w64(u,ROOT+0x28,VECTOR);w64(u,ROOT+0x30,VECTOR+0x10000)
    w64(u,V+8,DELETE)
    wrapper_calls=[];priority_calls=[];deletions=[];plans={};current={};allocations=0;next_id=100
    def text_at(p):
        raw=bytes(u.mem_read(p,256));assert b'\0' in raw;return raw.split(b'\0',1)[0].decode()
    def ret(v=0):u.reg_write(G[0],v&0xffffffffffffffff);u.reg_write(ar.UC_ARM64_REG_PC,u.reg_read(ar.UC_ARM64_REG_LR))
    def native_entry(uc,at,n,d):
        nonlocal current
        desc=uc.reg_read(G[0]);path=text_at(qword(uc,desc));priority=uc.reg_read(G[2])&0xffffffff
        queue=plans.get(path,[]);mode=queue.pop(0) if queue else 'success'
        current={'path':path,'mode':mode,'priority':priority}
        wrapper_calls.append((path,priority,bytes(uc.mem_read(desc+8,24))))
        w64(uc,GLOBAL,0 if mode=='no_root' else ROOT)
        w64(uc,ROOT+0x18,0 if mode=='no_binder' else HANDLE)
    u.hook_add(UC_HOOK_CODE,native_entry,begin=M+0x473190,end=M+0x473190)
    def external(uc,at,n,d):
        nonlocal allocations,next_id
        if at==M+0x116ae60:
            assert uc.reg_read(G[0])==0x50
            if current['mode']=='no_allocation':ret(0)
            else:
                p=POOL+allocations*0x100;allocations+=1
                assert p+0x100<VECTOR;u.mem_write(p,bytes(0x100));ret(p)
        elif at==M+0x115ee28:
            w64(uc,uc.reg_read(G[0]),V);ret(uc.reg_read(G[0]))
        elif at==M+0x115ef14:
            assert text_at(uc.reg_read(G[2]))==current['path']
            assert uc.reg_read(G[1])==HANDLE
            if current['mode']=='bind_rejected':ret(0)
            else:
                # Out ID belongs to the native object, then real manager code
                # copies it to the caller's output and retains the object.
                if current['mode']!='zero_id':
                    next_id+=1;uc.mem_write(uc.reg_read(G[0])+8,struct.pack('<I',next_id))
                ret(1)
        elif at==M+0x10ad050:
            priority_calls.append((uc.reg_read(G[0])&0xffffffff,uc.reg_read(G[1])&0xffffffff));ret(0)
        elif at==DELETE:
            deletions.append(uc.reg_read(G[0]));ret()
        else:ret() # diagnostics and native locking only
    for at in [M+0x116ae60,M+0x115ee28,M+0x115ef14,M+0x10ad050,DELETE,
               M+0x116d3c0,M+0x116d420,M+0x12155a0,D+symbols['snprintf'],sym('SvcLogger6LogRaw')]:
        u.hook_add(UC_HOOK_CODE,external,begin=at,end=at)
    def profile(rows):
        data=encode(rows);u.mem_write(PROFILE,data);assert call(u,load,[PROFILE,PROFILE_SIZE])==1
    def request(path='sim:data/base.cpk',priority=7,mode='success',hook=True):
        plans[path]=[mode];u.mem_write(PATH,path.encode()+b'\0');u.mem_write(OUT,b'\0'*4)
        u.mem_write(DESC,struct.pack('<QQQQ',PATH,0,0xaabbccdd,0x11223344))
        before=bytes(u.mem_read(DESC,32));old=len(wrapper_calls)
        result=call(u,callback if hook else M+0x473190,[DESC,OUT,priority])
        assert bytes(u.mem_read(DESC,32))==before
        return result,struct.unpack('<I',u.mem_read(OUT,4))[0],wrapper_calls[old:]
    # Independently establish native return/ID behavior before testing adapter.
    native_cases=[]
    for mode in ['no_root','no_binder','no_allocation','bind_rejected','zero_id','success']:
        result,id,trace=request(mode=mode,hook=False)
        assert result==int(mode not in ('no_root','bind_rejected'))
        assert bool(id)==(mode=='success')
        native_cases.append({'mode':mode,'return':result,'valid_id':bool(id)})
    rows=[{'path':'sim:data/moddingapi/A.cpk','priority':32},
          {'path':'sim:data/moddingapi/sub/B.cpk','priority':0},
          {'path':'sim:data/moddingapi/C.cpk','priority':0x7fffffff}]
    cases=0
    profile([]);_,_,trace=request();assert len(trace)==1 and call(u,count,[])==0;cases+=1
    for failure in ['no_root','no_binder','no_allocation','bind_rejected','zero_id']:
        profile(rows)
        plans[rows[0]['path']]=[failure,'success']
        result,id,trace=request();assert result==1 and id
        assert [x[:2] for x in trace]==[('sim:data/base.cpk',7)]+[(r['path'],r['priority']) for r in rows]
        assert all(x[2]==bytes(24) for x in trace[1:])
        assert call(u,count,[])==2
        # ID getter must distinguish the failed entry from successful entries.
        for i in range(3):
            u.mem_write(OUT+8,struct.pack('<I',0xabcdef))
            assert call(u,binding,[i,OUT+8])==int(i!=0)
            if i==0:assert struct.unpack('<I',u.mem_read(OUT+8,4))[0]==0xabcdef
        _,_,retry=request();assert [x[0] for x in retry]==['sim:data/base.cpk',rows[0]['path']]
        assert call(u,count,[])==3
        _,_,again=request();assert len(again)==1
        cases+=1
    # Stock return and output ID are preserved, including failed outer binds.
    for mode in ['no_root','no_binder','no_allocation','bind_rejected','zero_id']:
        profile(rows);result,id,trace=request(mode=mode)
        assert len(trace)==1 and call(u,count,[])==0
        assert result==int(mode not in ('no_root','bind_rejected')) and id==0;cases+=1
    # A native early failure does not touch the caller's output pointer. The
    # hook must not add a dereference on that failure path either.
    profile(rows);u.mem_write(PATH,b'sim:data/base.cpk\0')
    u.mem_write(DESC,struct.pack('<QQQQ',PATH,0,0,0));plans['sim:data/base.cpk']=['no_root']
    old=len(wrapper_calls)
    assert call(u,callback,[DESC,0x1234,7])==0
    assert len(wrapper_calls)==old+1 and call(u,count,[])==0;cases+=1
    for path in ['rom:data/base.cpk','s','si','sim','Sim:data/base.cpk']:
        profile(rows);result,id,trace=request(path=path);assert result==1 and id and len(trace)==1
        assert call(u,count,[])==0;cases+=1
    # Capacity and bit31, stable configured order, distinct priorities/IDs.
    full=[{'path':f'sim:data/moddingapi/mod_{i}.cpk','priority':1000-i} for i in range(32)]
    profile(full);_,_,trace=request();assert [x[:2] for x in trace[1:]]==[(r['path'],r['priority']) for r in full]
    assert call(u,count,[])==32
    assert call(u,binding,[31,OUT+8])==1
    assert call(u,binding,[32,OUT+8])==0 and call(u,binding,[0,0])==0
    _,_,trace=request();assert len(trace)==1;cases+=1
    # Verify the native wrapper sends its exact requested priority after the
    # manager's internal default priority. It must use the same returned ID.
    profile([rows[0]]);old=len(priority_calls);_,stock_id,trace=request(priority=19)
    new=priority_calls[old:];assert len(new)==4
    assert new[0]==(stock_id,0) and new[1]==(stock_id,19)
    assert new[2][0]==new[3][0] and new[2][1]==0 and new[3][1]==32
    result={'status':'PASS','native_failure_modes':native_cases,'registration_scenarios':cases+1,
            'capacity':32,'failed_only_retry':True,'original_result_and_id_preserved':True,
            'native_priority_argument_chain_verified':True,'no_new_hook_sites':True,
            'native_functions':['0x473190 binder wrapper','0x115fbb8 normal path adapter',
                                '0x115e80c manager including allocation-failure return',
                                '0x115e8e0 vector insertion (preallocated)','0x115f2bc default priority wrapper'],
            'module_elf_sha256':hashlib.sha256(elf_path.read_bytes()).hexdigest(),
            'modeled':['RTLD/hook publication','native allocator and object constructor',
                       'CRI bind operation/returned ID','CRI priority service','locking and logging'],
            'not_proven':['CRI async completion','archive lookup precedence','game loader teardown/rebind',
                          'directory discovery','parameter merging','emulator gameplay'],
            'gameplay_verified':False,'full_moddingapi':False}
    out.mkdir(parents=True,exist_ok=True);(out/'native_cpk.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Native CPK PASS:',cases+1,'registration scenarios; six native failure/success branches')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--main',type=Path,required=True);p.add_argument('--elf',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.main,a.elf,a.output)
