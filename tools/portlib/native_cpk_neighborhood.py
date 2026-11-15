"""Static nearby-target reconnaissance, not a native lifecycle/hook implementation.

The previous exact-address scan could miss entrypoint offsets near an anchor.
On the pinned Switch 1.70 NSO, enumerate branches entering bounded nearby
regions, bounded indirect BR/BLR sites and RELATIVE relocation addends landing
in those regions. No function boundaries or callback ownership are inferred.
"""
from collections import defaultdict
from .nso_profile import segments
from .native_cpk_graph import direct_branch, MAIN_SHA256
from .native_cpk_indirect import _image_and_relocations, RELA_TYPE
import hashlib
import struct

WINDOWS={
    'fileload_process_neighborhood':(0x106F404,0x800),
    'cpk_bind_manager_neighborhood':(0x115E80C,0x400),
    'cpk_adapter_neighborhood':(0x115FBB8,0x300),
    'file_open_neighborhood':(0x1170FB0,0x400),
    'fileload_status_neighborhood':(0x1207EFC,0x300),
}
MAX_REPORT_SAMPLES=64


def indirect_kind(word):
    op=word & 0xFFFFFC1F
    if op==0xD63F0000:return 'BLR'
    if op==0xD61F0000:return 'BR'
    if op==0xD65F0000:return 'RET'
    return None


def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError('Exact SHA-pinned R180 Switch 1.70 main required')
    rows,relocs=_image_and_relocations(nso)
    va,code,_=rows[0]
    if va!=0 or max(c+radius for c,radius in WINDOWS.values())>=len(code):
        raise ValueError('Unexpected native text address span')
    windows={}
    for name,(center,radius) in WINDOWS.items():
        windows[name]={'name':name,'anchor_offset':f'0x{center:x}',
                       'radius_bytes':radius,'incoming_counts':defaultdict(int),
                       'incoming_samples':[],'direct_target_frequencies':defaultdict(int),
                       'nearby_indirect_branch_sites':[],
                       'relative_relocation_addend_samples':[],
                       'relative_relocation_addend_count':0}
    for pc in range(0,len(code)-3,4):
        word=struct.unpack_from('<I',code,pc)[0]
        direct=direct_branch(word,pc)
        for name,(center,radius) in WINDOWS.items():
            if direct:
                kind,target=direct
                if center-radius<=target<=center+radius:
                    w=windows[name]
                    is_outside=not (center-radius<=pc<=center+radius)
                    w['incoming_counts'][kind+'_outside' if is_outside else kind+'_inside']+=1
                    w['direct_target_frequencies'][f'0x{target:x}']+=1
                    if is_outside and len(w['incoming_samples'])<MAX_REPORT_SAMPLES:
                        w['incoming_samples'].append({'caller_offset':f'0x{pc:x}',
                                                     'target_offset':f'0x{target:x}',
                                                     'kind':kind})
            if center-radius<=pc<=center+radius:
                kind=indirect_kind(word)
                if kind:
                    windows[name]['nearby_indirect_branch_sites'].append({
                        'offset':f'0x{pc:x}','kind':kind,
                        'target_register':(word>>5)&31})
    for place,kind,target in relocs:
        if kind!=RELA_TYPE:continue
        for name,(center,radius) in WINDOWS.items():
            if center-radius<=target<=center+radius:
                w=windows[name]
                w['relative_relocation_addend_count']+=1
                if len(w['relative_relocation_addend_samples'])<MAX_REPORT_SAMPLES:
                    w['relative_relocation_addend_samples'].append({
                        'patch_slot':f'0x{place:x}','code_addend':f'0x{target:x}',
                        'delta_from_anchor':target-center})
    report=[]
    for name,(center,radius) in WINDOWS.items():
        w=windows[name]
        frequencies=sorted(w.pop('direct_target_frequencies').items(),
                           key=lambda item:(-item[1],abs(int(item[0],16)-center),item[0]))
        w['common_nearby_direct_targets']=[{
            'target_offset':target,'direct_refs':freq,
            'delta_from_anchor':int(target,16)-center
        } for target,freq in frequencies[:MAX_REPORT_SAMPLES]]
        w['distinct_direct_target_addresses']=len(frequencies)
        w['incoming_counts']=dict(w['incoming_counts'])
        w['nearby_indirect_branch_count']=len(w['nearby_indirect_branch_sites'])
        w['nearby_indirect_branch_sites']=w['nearby_indirect_branch_sites'][:MAX_REPORT_SAMPLES]
        w['nearby_branch_sites_are_not_callers_of_anchor']=True
        report.append(w)
    return {
        'status':'PINNED_STATIC_NEARBY_TARGET_CENSUS_ONLY',
        'main_sha256':digest,
        'regions':report,
        'source_relocation_records':len(relocs),
        'indirect_calls_to_exact_anchor_verified':False,
        'nearby_target_not_a_function_entry_proof':True,
        'CRI_async_completion_verified':False,
        'CRI_unbind_verified':False,'archive_lookup_precedence_verified':False,
        'native_ABI_verified':False,'gameplay_verified':False,'full_moddingapi':False
    }
