"""Exact-main NSO PLT import evidence for native FileOpen BL 0x1171028.

Decode original ADRP/LDR/ADD/BR thunk and the dynamic relocation for its GOT
slot. Resolve an ELF64 symbol only when metadata supports it. A symbol name
is not an implementation, correct ABI/lifecycle proof, or runtime invocation.
"""
import hashlib
import struct

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_cpk_indirect import adrp_ldr_slot, MAX_MAPPED_IMAGE
from .nso_profile import segments

CALLSITE=0x1171028
PLT=0x12F39A0
SLOT=0x2142080
PLT_WORDS=(0xf0007270,0xf9404211,0x91020210,0xd61f0220)
RELA=7
JMPREL=23
DT_RELASZ=8
DT_RELAENT=9
DT_PLTRELSZ=2
DT_PLTREL=20
DT_SYMTAB=6
DT_STRTAB=5
DT_STRSZ=10
DT_SYMENT=11
REL_TYPES={1025:"R_AARCH64_GLOB_DAT",1026:"R_AARCH64_JUMP_SLOT",
           1027:"R_AARCH64_RELATIVE"}

def _read_image(nso):
    rows=segments(nso)
    end=max(va+len(raw) for va,raw,_ in rows)
    bss=struct.unpack_from("<I",nso,60)[0]
    end=max(end,rows[-1][0]+len(rows[-1][1])+bss)
    if end>MAX_MAPPED_IMAGE:
        raise ValueError("Invalid original image size")
    mem=bytearray(end)
    for va,raw,_ in rows:
        mem[va:va+len(raw)]=raw
    return rows,mem

def _tags(mem):
    if len(mem)<16:raise ValueError("Image truncated")
    mod0=struct.unpack_from("<I",mem,4)[0]
    if not 0<=mod0<len(mem)-8:raise ValueError("Bad MOD0 pointer")
    delta=struct.unpack_from("<i",mem,mod0+4)[0]
    dyn=mod0+delta
    if dyn<0 or dyn%8 or dyn+16>len(mem):
        raise ValueError("Invalid MOD0 dynamic pointer")
    result={}
    for at in range(dyn,min(dyn+8192,len(mem)-15),16):
        typ,value=struct.unpack_from("<QQ",mem,at)
        if typ==0:
            return result
        if typ in (DT_SYMTAB,DT_STRTAB,DT_STRSZ,DT_SYMENT,RELA,
                   DT_RELASZ,DT_RELAENT,JMPREL,DT_PLTRELSZ,DT_PLTREL):
            if typ in result and result[typ]!=value:
                raise ValueError("Conflicting imported-symbol dynamic tag")
        result[typ]=value
    raise ValueError("Original NSO dynamic tags unterminated")

def _scan_relocations(mem,tags,slot):
    tables=[]
    if RELA in tags and DT_RELASZ in tags:
        if tags.get(DT_RELAENT,24)!=24:
            raise ValueError("Bad .rela.dyn entry size")
        tables.append(("DT_RELA",tags[RELA],tags[DT_RELASZ]))
    if JMPREL in tags and DT_PLTRELSZ in tags:
        if tags.get(DT_PLTREL,RELA)!=RELA:
            raise ValueError("Non-RELA PLT relocation not supported")
        tables.append(("DT_JMPREL",tags[JMPREL],tags[DT_PLTRELSZ]))
    found=[]
    for name,offset,size in tables:
        if offset%8 or size%24 or offset+size>len(mem):
            raise ValueError("Native dynamic relocation bounds invalid")
        for p in range(offset,offset+size,24):
            r_offset,info,addend=struct.unpack_from("<QQq",mem,p)
            if r_offset==slot:
                found.append({
                    "table":name,"relocation_record_offset":hex(p),
                    "slot":hex(r_offset),
                    "type_number":info & 0xffffffff,
                    "type_name":REL_TYPES.get(info & 0xffffffff,"UNKNOWN_AARCH64_TYPE"),
                    "symbol_index":info>>32,
                    "addend":addend
                })
    # The .rela.dyn and .rela.plt table extents might overlap. Report the
    # presence of duplicate records and refuse to choose a winner.
    unique={(v["relocation_record_offset"],v["type_number"],
             v["symbol_index"]) for v in found}
    if len(unique)!=len(found):
        raise ValueError("Overlapping dynamic relocation lists for GOT slot")
    return found

def _symbol(mem,tags,index):
    if index==0:
        return {"index":0,"name":None,
                "reason":"ELF_STN_UNDEF_zero_index_is_not_named_import"}
    if not all(k in tags for k in (DT_SYMTAB,DT_STRTAB,DT_STRSZ)):
        return {"index":index,"name":None,
                "reason":"missing_dynamic_symbol_or_string_table"}
    size=tags.get(DT_SYMENT,24)
    if size!=24:raise ValueError("Unexpected ELF64 symbol record size")
    at=tags[DT_SYMTAB]+index*24
    if at<0 or at+24>len(mem):
        raise ValueError("Symbol index outside original NSO memory")
    st_name,st_info,st_other,st_shndx,st_value,st_size=struct.unpack_from(
        "<IBBHQQ",mem,at)
    if st_name>=tags[DT_STRSZ]:
        raise ValueError("ELF symbol name offset outside DT_STRSZ")
    start=tags[DT_STRTAB]+st_name
    max_end=min(tags[DT_STRTAB]+tags[DT_STRSZ],len(mem),start+1024)
    if start<0 or start>=len(mem) or start>=max_end:
        raise ValueError("Invalid symbol string table bounds")
    end=mem.find(0,start,max_end)
    if end<0:
        raise ValueError("Missing terminator in original symbol string")
    raw=bytes(mem[start:end])
    try:name=raw.decode("ascii")
    except UnicodeDecodeError:
        name=None
    return {"index":index,"name":name,"name_raw_hex":raw.hex(),
            "st_info":st_info,"st_other":st_other,
            "st_shndx":st_shndx,"st_value":hex(st_value),
            "st_size":st_size,"original_git_and_runtime_semantics_unresolved":True}

def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    rows,mem=_read_image(nso)
    va,text,_=rows[0]
    if va!=0 or PLT+16>len(text):
        raise ValueError("Pinned PLT outside original executable")
    word=struct.unpack_from("<I",text,CALLSITE)[0]
    if direct_branch(word,CALLSITE)!=("BL",PLT):
        raise ValueError("Native FileOpen import BL source changed")
    words=struct.unpack_from("<4I",text,PLT)
    if words!=PLT_WORDS:
        raise ValueError("Original PLT instruction words changed")
    slot=adrp_ldr_slot(words[0],words[1],PLT)
    if slot!=SLOT:
        raise ValueError("Original ADRP+LDR X17 GOT address differs")
    if words[2]!=0x91020210 or words[3]!=0xd61f0220:
        raise ValueError("Original PLT tail branch is not known ADD/BR")
    tags=_tags(mem)
    relocs=_scan_relocations(mem,tags,slot)
    imports=[]
    for row in relocs:
        imports.append({**row,"original_dynamic_symbol":_symbol(
            mem,tags,row["symbol_index"])})
    if len(relocs)>1:
        # Never select arbitrary symbol from duplicate original relocations.
        raise ValueError("GOT import relocation ambiguous")
    return {
        "status":"SHA_PINNED_ORIGINAL_FILEOPEN_PLT_IMPORT_GOT_EVIDENCE_ONLY",
        "main_sha256":digest,
        "fileopen_callsite":hex(CALLSITE),
        "fileopen_callsite_word_le":text[CALLSITE:CALLSITE+4].hex(),
        "plt_thunk":hex(PLT),
        "plt_words_le":[text[PLT+i:PLT+i+4].hex() for i in (0,4,8,12)],
        "plt_literal_instructions":["ADRP X16","LDR X17,[X16,#0x80]",
                                     "ADD X16,X16,#0x80","BR X17"],
        "got_slot":hex(slot),
        "original_dynamic_relocations_to_slot":imports,
        "symbol_name_proven_if_resolved":bool(imports and
                    imports[0]["original_dynamic_symbol"].get("name")),
        "imported_function_implementation_proven":False,
        "actual_runtime_import_binding_verified":False,
        "native_callback_lock_async_unbind_proven":False,
        "object_lifetime_or_allocator_proven":False,
        "archive_precedence_proven":False,
        "safe_runtime_hook_ABI_proven":False,
        "new_native_hook_installed":False,
        "gameplay_verified":False,"full_moddingapi":False,
        "ready_for_gameplay_test":False,"emulator_tested":False
    }
