"""Read-only direct AArch64 branch-edge census around verified v1.70 anchors.

A direct BL/B xref is only a static control-flow candidate. It does not
establish invocation, ABI, CRI completion, unloading, or priority precedence.
"""
import hashlib
import struct
from .nso_profile import segments

MAIN_SHA256='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

# Anchors are already identified in nsc_cpk_bridge.cpp/test_native_cpk.py.
# No new native addresses/ABI are inferred from this table.
ANCHORS={
    'cpk_bind_wrapper': 0x473190,
    'cpk_manager_bind': 0x115E80C,
    'cpk_path_adapter': 0x115FBB8,
    'cpk_priority_wrapper': 0x115F2BC,
    'cpk_vector_insert': 0x115E8E0,
    'fileload_request': 0x1206B4C,
    'fileload_create': 0x1206C9C,
    'fileload_status': 0x1207EFC,
    'fileload_process': 0x106F404,
    'file_open_request': 0x1170FB0,
}


def direct_branch(word, pc):
    op=word & 0xFC000000
    if op not in (0x94000000, 0x14000000):
        return None
    imm=word & 0x03FFFFFF
    if imm & (1<<25):
        imm -= 1<<26
    return ('BL' if op==0x94000000 else 'B',pc+(imm<<2))


def analyze(nso):
    actual=hashlib.sha256(nso).hexdigest()
    if actual!=MAIN_SHA256:
        raise ValueError('Not the exact pinned Switch 1.70 main input')
    image=segments(nso)
    va,text,_=image[0]
    if va!=0 or any(at+0x100>len(text) for at in ANCHORS.values()):
        raise ValueError('Pinned main text has incompatible anchor geometry')
    incoming={k:[] for k in ANCHORS}
    lookup={v:k for k,v in ANCHORS.items()}
    direct_total=0
    for pc in range(0,len(text)-3,4):
        word=struct.unpack_from('<I',text,pc)[0]
        decoded=direct_branch(word,pc)
        if not decoded:
            continue
        direct_total+=1
        kind,target=decoded
        name=lookup.get(target)
        if name is not None:
            incoming[name].append({'caller_offset':f'0x{pc:x}','kind':kind})
    anchors=[]
    for name,at in ANCHORS.items():
        out=[]
        for pc in range(at,at+0x100,4):
            decoded=direct_branch(struct.unpack_from('<I',text,pc)[0],pc)
            if decoded:
                kind,target=decoded
                out.append({'at':f'0x{pc:x}','kind':kind,
                            'target':f'0x{target:x}',
                            'known_anchor':lookup.get(target)})
        anchors.append({
            'name':name,'offset':f'0x{at:x}',
            'first_word_le':text[at:at+4].hex(),
            'incoming_count':len(incoming[name]),
            'incoming_samples':incoming[name][:32],
            'bounded_window_bytes':0x100,
            'outgoing_edges_in_bounded_window':out,
            'function_boundary_proven':False,
        })
    return {'status':'READ_ONLY_STATIC_CALL_EDGE_CENSUS',
            'source_main_sha256':actual,'segment_text_sha256':hashlib.sha256(text).hexdigest(),
            'text_bytes_scanned':len(text),'candidate_direct_branches':direct_total,
            'anchors':anchors,
            'bounded_windows_are_not_function_bounds':True,
            'indirect_calls_not_resolved':True,
            'native_abi_or_lifecycle_established':False,
            'async_completion_verified':False,
            'unbinding_verified':False,
            'runtime_archive_precedence_verified':False,
            'gameplay_verified':False,'full_moddingapi':False}
