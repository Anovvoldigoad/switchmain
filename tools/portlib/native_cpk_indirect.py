"""Read-only function-pointer reference audit on the exact SHA-pinned NSO main.

Checks RELATIVE relocation addends and immediately adjacent ADR/ADRP+ADD
address materializations. Does not resolve virtual dispatch, call lifetimes,
CRI async status, unbind or archive priority winner. A pointer is not a call.
"""
import hashlib
import struct
from .nso_profile import segments
from .native_cpk_graph import ANCHORS, MAIN_SHA256

RELA_TYPE=1027  # R_AARCH64_RELATIVE
MAX_MAPPED_IMAGE=128*1024*1024


def sign_extend(v, bits):
    if v & (1 << (bits-1)):
        v -= 1 << bits
    return v


def adr_target(word, pc):
    if (word & 0x9f000000) != 0x10000000:
        return None
    immediate=((word >> 5) & 0x7ffff)<<2 | ((word >> 29)&3)
    return pc+sign_extend(immediate,21)


def adrp_page(word, pc):
    if (word & 0x9f000000) != 0x90000000:
        return None
    immediate=((word >> 5) & 0x7ffff)<<2 | ((word >> 29)&3)
    return (pc & ~0xfff) + (sign_extend(immediate,21)<<12)


def adrp_add_target(adrp, add, pc):
    base=adrp_page(adrp,pc)
    if base is None or (add & 0xff000000)!=0x91000000:
        return None
    rd=adrp&31
    if rd!=((add >> 5)&31) or rd!=(add&31):
        return None
    shift=(add >> 22)&3
    if shift not in (0,1):
        return None
    return base+(((add >> 10)&0xfff) << (12 if shift else 0))


def adrp_ldr_slot(adrp, ldr, pc):
    """LDR Xd,[Xn,#imm12*8] immediately following ADRP is a *slot* reference."""
    base=adrp_page(adrp,pc)
    if base is None or (ldr & 0xffc00000)!=0xf9400000:
        return None
    if (adrp&31)!=((ldr>>5)&31):
        return None
    return base + (((ldr>>10)&0xfff)*8)


def ldr_literal_slot(word, pc):
    if (word & 0xff000000)!=0x58000000:
        return None
    return pc + (sign_extend((word>>5)&0x7ffff,19)<<2)


def _image_and_relocations(nso):
    rows=segments(nso)
    end=max(va+len(raw) for va,raw,_ in rows)
    bss=struct.unpack_from('<I',nso,60)[0]
    end=max(end,rows[-1][0]+len(rows[-1][1])+bss)
    if end>MAX_MAPPED_IMAGE:
        raise ValueError('Implausible NSO mapped size')
    memory=bytearray(end)
    for va,raw,_ in rows:
        memory[va:va+len(raw)]=raw
    def read_u32(at):
        if at<0 or at+4>len(memory):raise ValueError('NSO relocation metadata out of bounds')
        return struct.unpack_from('<I',memory,at)[0]
    module=read_u32(4)
    dyn=module+struct.unpack_from('<i',memory,module+4)[0]
    if dyn<0 or dyn%8 or dyn+16>len(memory):
        raise ValueError('Invalid dynamic table pointer')
    tags={}
    for off in range(dyn,min(dyn+8192,len(memory)-15),16):
        typ,value=struct.unpack_from('<QQ',memory,off)
        if not typ:break
        if typ in tags and tags[typ]!=value:
            raise ValueError('Ambiguous dynamic tag')
        tags[typ]=value
    else:
        raise ValueError('Dynamic table unterminated')
    if not all(k in tags for k in (7,8)) or tags.get(9,24)!=24:
        raise ValueError('Expected AArch64 RELA table')
    at,size=tags[7],tags[8]
    if at<0 or size%24 or at+size>len(memory):
        raise ValueError('RELA size/offset invalid')
    relocs=[]
    for i in range(size//24):
        pos,info,addend=struct.unpack_from('<QQq',memory,at+i*24)
        if pos+8>len(memory):
            raise ValueError('RELA patch target out of bounds')
        relocs.append((pos,info&0xffffffff,addend))
    return rows,relocs


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError('Not exact hash-pinned Switch v1.70 main')
    rows,relocs=_image_and_relocations(nso)
    textva,text,_=rows[0]
    if textva!=0 or max(ANCHORS.values())+4>len(text):
        raise ValueError('Unexpected NSO text layout')
    aliases={v:k for k,v in ANCHORS.items()}
    ref_slots={k:[] for k in ANCHORS}
    for at,typ,addend in relocs:
        if typ==RELA_TYPE and addend in aliases:
            ref_slots[aliases[addend]].append(at)
    slots_to_anchors={}
    for name,positions in ref_slots.items():
        for pos in positions:slots_to_anchors.setdefault(pos,[]).append(name)
    refs={k:{'adr':[],'adrp_add':[],'adrp_ldr_relocation_slots':[],
             'literal_ldr_relocation_slots':[]} for k in ANCHORS}
    for pc in range(0,len(text)-3,4):
        word=struct.unpack_from('<I',text,pc)[0]
        adr=adr_target(word,pc)
        if adr in aliases:
            refs[aliases[adr]]['adr'].append(f'0x{pc:x}')
        literal=ldr_literal_slot(word,pc)
        if literal in slots_to_anchors:
            for name in slots_to_anchors[literal]:
                refs[name]['literal_ldr_relocation_slots'].append(
                    {'instruction':f'0x{pc:x}','slot':f'0x{literal:x}'})
        if pc+8>len(text):continue
        following=struct.unpack_from('<I',text,pc+4)[0]
        calculated=adrp_add_target(word,following,pc)
        if calculated in aliases:
            refs[aliases[calculated]]['adrp_add'].append(f'0x{pc:x}')
        slot=adrp_ldr_slot(word,following,pc)
        if slot in slots_to_anchors:
            for name in slots_to_anchors[slot]:
                refs[name]['adrp_ldr_relocation_slots'].append(
                    {'instruction':f'0x{pc:x}','slot':f'0x{slot:x}'})
    anchors=[]
    for name,at in ANCHORS.items():
        group=refs[name]
        anchors.append({'name':name,'code_offset':f'0x{at:x}',
                        'relative_relocation_slots':[f'0x{p:x}' for p in ref_slots[name]],
                        'relocation_slot_count':len(ref_slots[name]),
                        'direct_code_address_materializations':{
                            'adr':group['adr'],'immediately_adjacent_adrp_add':group['adrp_add']},
                        'load_relocation_slot_candidates':{
                            'immediately_adjacent_adrp_ldr':group['adrp_ldr_relocation_slots'],
                            'literal_ldr':group['literal_ldr_relocation_slots']},
                        'all_indirect_callers_resolved':False})
    return {'status':'STATIC_PINNED_ADDRESS_REFERENCE_CENSUS',
            'main_sha256':digest,
            'relocation_record_count':len(relocs),
            'relative_relocation_record_count':sum(t==RELA_TYPE for _,t,_ in relocs),
            'anchors':anchors,
            'only_immediately_adjacent_adrp_sequences_tested':True,
            'function_pointer_candidates_not_execution_proof':True,
            'indirect_calls_fully_resolved':False,'native_abi_verified':False,
            'async_completion_verified':False,'unbind_verified':False,
            'archive_precedence_verified':False,
            'gameplay_verified':False,'full_moddingapi':False}
