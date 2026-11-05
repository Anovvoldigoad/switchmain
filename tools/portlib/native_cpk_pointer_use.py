"""Pin-verified ARM64 address-use links for observed CPK/FileLoad relocation slots.

Adds a NEW evidence layer beyond earlier code-target relocation grouping:
look for PC-relative ADR and ADRP+ADD / ADRP+LDR sequences that reference
the *data-side relocation slots*, rather than merely the executable targets.

A local linear instruction pair is not proof of object ownership: there may
be register clobbers on longer horizons, conditional branches, unrelated
tables, or PC-relative materializations from non-covered instruction forms.
No native callback ABI, CRI async state, unbind or runtime priority inferred.
"""
import hashlib
import struct
from collections import defaultdict
from .native_cpk_graph import MAIN_SHA256
from .native_cpk_indirect import (
    _image_and_relocations, RELA_TYPE, adr_target, adrp_page,
    adrp_add_target, adrp_ldr_slot,
)

FOCUS_SLOTS=(0x212B5F0,0x212B728,0x212B7A0,0x215C478)
REQUIRED_RELOCATIONS={
    0x212B5F0:0x106EDB8,
    0x212B5F8:0x106EDC4,
    0x212B600:0x106EDE0,
    0x212B608:0x106EDE8,
    0x215C478:0x106F394,
}
NEIGHBORHOOD=0x80
SCAN_INSTRUCTION_LOOKAHEAD=4
MAX_SAMPLES=36


def _match_pair(first,second,pc):
    """Return (kind,target) for exact A64 ADRP+64-bit ADD/LDR encodings."""
    t=adrp_add_target(first,second,pc)
    if t is not None:
        return "ADRP_ADD_ADDRESS",t
    t=adrp_ldr_slot(first,second,pc)
    if t is not None:
        return "ADRP_LDR64_SLOT",t
    return None


def _source_records(text,lookup_slots):
    """Find bounded A64 code-site candidates for relocation-slot addresses.

    Exact adjacent pairs are machine-word witnesses. Non-adjacent pairs are
    candidates only: this does not establish register non-clobber or flow.
    """
    focus_pages={
        ((slot+delta)&~0xfff)
        for slot in FOCUS_SLOTS for delta in (-NEIGHBORHOOD,0,NEIGHBORHOOD)
    }
    candidates=[]
    for pc in range(0,len(text)-3,4):
        first=struct.unpack_from("<I",text,pc)[0]
        direct=adr_target(first,pc)
        if direct is not None and any(abs(direct-slot)<=NEIGHBORHOOD for slot in FOCUS_SLOTS):
            candidates.append({
                "adrp_instruction":None, "use_instruction":f"0x{pc:x}",
                "kind":"ADR_ADDRESS",
                "target_data_address":f"0x{direct:x}","steps":0,
                "target_is_relative_relocation_slot":direct in lookup_slots,
                "relocated_code_addend":f"0x{lookup_slots[direct]:x}" if direct in lookup_slots else None,
                "intervening_register_clobber_ruled_out":True
            })
        page=adrp_page(first,pc)
        if page not in focus_pages:
            continue
        for step in range(1,SCAN_INSTRUCTION_LOOKAHEAD+1):
            use=pc+step*4
            if use+4>len(text):break
            word=struct.unpack_from("<I",text,use)[0]
            found=_match_pair(first,word,pc)
            if found is None:continue
            kind,target=found
            if not any(abs(target-slot)<=NEIGHBORHOOD for slot in FOCUS_SLOTS):
                continue
            # Do not silently promote non-adjacent linear sequences into
            # compiler-proven register-flow edges.
            candidates.append({
                "adrp_instruction":f"0x{pc:x}",
                "use_instruction":f"0x{use:x}",
                "kind":kind,
                "target_data_address":f"0x{target:x}",
                "steps":step,
                "target_is_relative_relocation_slot":target in lookup_slots,
                "relocated_code_addend":f"0x{lookup_slots[target]:x}" if target in lookup_slots else None,
                "intervening_register_clobber_ruled_out":step==1
            })
    # Some compiler shapes use ADRP outside the above small page range
    # and LDR via register/index arithmetic, which this cannot resolve.
    return candidates


def inspect(nso):
    if hashlib.sha256(nso).hexdigest()!=MAIN_SHA256:
        raise ValueError("Expected byte-exact pinned NSC Switch 1.70 main")
    rows,relocs=_image_and_relocations(nso)
    va,code,_=rows[0]
    if va or len(code)<=0x1170FB0:
        raise ValueError("Unexpected original text layout")
    reloc_lookup={}
    for slot,kind,addend in relocs:
        if kind!=RELA_TYPE:continue
        if slot in reloc_lookup and reloc_lookup[slot]!=addend:
            raise ValueError("Ambiguous duplicate R_AARCH64_RELATIVE slot")
        reloc_lookup[slot]=addend
    for slot,addend in REQUIRED_RELOCATIONS.items():
        if reloc_lookup.get(slot)!=addend:
            raise ValueError("Original pinned pointer slot/addend mismatch")
    candidate_sources=_source_records(code,reloc_lookup)
    regions=[]
    for focus in FOCUS_SLOTS:
        mapped=sorted((slot,target) for slot,target in reloc_lookup.items()
                      if abs(slot-focus)<=NEIGHBORHOOD)
        machine_uses=[record for record in candidate_sources
                      if abs(int(record["target_data_address"],16)-focus)<=NEIGHBORHOOD]
        kind_counts=dict(sorted((kind,sum(x["kind"]==kind for x in machine_uses))
                                for kind in ("ADR_ADDRESS","ADRP_ADD_ADDRESS","ADRP_LDR64_SLOT")))
        direct_exact=[r for r in machine_uses
                     if r["target_is_relative_relocation_slot"]
                     and r["intervening_register_clobber_ruled_out"]]
        regions.append({
            "focus_slot":f"0x{focus:x}",
            "radius_bytes":NEIGHBORHOOD,
            "nearby_RELATIVE_slot_count":len(mapped),
            "nearby_relative_code_targets":[
                {"slot":f"0x{slot:x}","target":f"0x{target:x}",
                 "target_in_executable_text":0<=target<len(code)}
                for slot,target in mapped[:MAX_SAMPLES]],
            "data_address_use_candidate_count":len(machine_uses),
            "use_instruction_kind_counts":kind_counts,
            "exact_slot_adjacent_or_ADR_witness_count":len(direct_exact),
            "data_address_use_samples":machine_uses[:MAX_SAMPLES],
            "bounded_linear_scan_does_not_prove_owning_class":True,
        })
    return {
        "status":"PINNED_STATIC_CPK_DATA_POINTER_USE_CANDIDATES_ONLY",
        "main_sha256":MAIN_SHA256,
        "source_relocation_records":len(relocs),
        "focus_slots":[f"0x{v:x}" for v in FOCUS_SLOTS],
        "lookahead_max_instructions":SCAN_INSTRUCTION_LOOKAHEAD,
        "regions":regions,
        "vtable_base_or_constructor_proven":False,
        "object_owner_proven":False,
        "allocator_ownership_verified":False,
        "native_ABI_verified":False,
        "CRI_async_completion_verified":False,
        "CRI_unbind_or_destruction_verified":False,
        "archive_precedence_verified":False,
        "native_hooks_added":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
