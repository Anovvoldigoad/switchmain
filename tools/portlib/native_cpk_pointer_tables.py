"""Read-only candidate adjacent AArch64 code-pointer relocation clusters.

Pinned v1.70 main has RELATIVE relocation addends near 0x106F404 at
0x212B5F0..0x212B608; these are relocation facts, NOT verified vtables.
Walk adjacent relocated 8-byte slots and retain groups referencing the
bounded fileload neighborhood. Do NOT infer ABI, method offsets or lifecycle.
"""
import hashlib
from .native_cpk_graph import MAIN_SHA256
from .native_cpk_indirect import _image_and_relocations, RELA_TYPE

FOCUS=0x106F404
RADIUS=0x800
MAX_RETURNED_CLUSTERS=32
MAX_MEMBERS_REPORTED=96
WITNESSES={0x212B5F0:0x106EDB8,0x212B5F8:0x106EDC4,
           0x212B600:0x106EDE0,0x212B608:0x106EDE8}


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError('Only exact Switch v1.70 pinned main supported')
    rows,records=_image_and_relocations(nso)
    text_end=rows[0][0]+len(rows[0][1])
    candidates=sorted(
        (slot,target) for slot,kind,target in records
        if kind==RELA_TYPE and 0<=target<text_end and slot%8==0)
    if len(candidates)!=len({slot for slot,_ in candidates}):
        raise ValueError('Repeated executable-target relocation slot')
    grouped=[];cluster=[]
    def append_cluster():
        if cluster and len(cluster)>=2 and any(abs(target-FOCUS)<=RADIUS for _,target in cluster):
            grouped.append(tuple(cluster))
    for slot,target in candidates:
        if cluster and slot!=cluster[-1][0]+8:
            append_cluster()
            cluster=[]
        cluster.append((slot,target))
    append_cluster()
    ordered=sorted(grouped,key=lambda g:(min(abs(t-FOCUS) for _,t in g),-len(g),g[0][0]))
    selected=[]
    for g in ordered[:MAX_RETURNED_CLUSTERS]:
        rows_out=[]
        for slot,target in g[:MAX_MEMBERS_REPORTED]:
            which=next((name for name,(va,raw,_) in zip(('text','rodata','data'),rows)
                        if va<=slot<va+len(raw)), 'bss_or_unmapped')
            rows_out.append({
                'relocation_slot':f'0x{slot:x}',
                'code_addend':f'0x{target:x}',
                'delta_from_fileload_anchor':target-FOCUS,
                'relocation_slot_segment':which,
                'target_first_word_le':rows[0][1][target:target+4].hex()
            })
        selected.append({
            'first_slot':f'0x{g[0][0]:x}',
            'contiguous_relocated_slot_count':len(g),
            'reported_members':rows_out,
            'all_members_in_report':len(g)<=MAX_MEMBERS_REPORTED,
            'contains_nearby_code_target':True,
            'candidate_pointer_table_not_proven_vtable':True})
    seen={slot:target for group in grouped for slot,target in group}
    witnesses=[{'slot':f'0x{k:x}','target':f'0x{v:x}',
                'observed_in_adjacent_cluster':seen.get(k)==v} for k,v in WITNESSES.items()]
    if any(not w['observed_in_adjacent_cluster'] for w in witnesses):
        raise ValueError('Known pinned main relocation evidence is not reproducible')
    return {
        'status':'PINNED_STATIC_ADJACENT_CODE_RELOCATION_CANDIDATES',
        'main_sha256':digest,
        'near_fileload_offset':f'0x{FOCUS:x}',
        'search_radius_bytes':RADIUS,
        'total_relocation_records':len(records),
        'code_target_relative_relocations':len(candidates),
        'nearby_candidate_clusters':len(grouped),
        'candidate_clusters_returned':len(selected),
        'clusters':selected,'known_witnesses':witnesses,
        'adjacent_relocation_slots_not_verified_vtables':True,
        'targets_not_verified_function_starts':True,
        'CRI_async_completion_verified':False,
        'CRI_unbind_verified':False,
        'lookup_precedence_verified':False,
        'native_abi_verified':False,
        'gameplay_verified':False,'full_moddingapi':False
    }
