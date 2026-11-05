"""Fail-closed PC ModdingAPI raw streams, NOT Switch XFBIN runtime readers.

Source evidence, pinned publicly:
  TheLeonX/UltimateStormAPI a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc
  OugiAwakeningParam.cpp blob 69456b8b1823d8f6d79e572088c756879e96bd40
  GudoBallParam.cpp blob 755c6dd2e4104afdcae54408a7d3443dcc6eb614
  CharRelationParam.cpp blob 4dc5ceb3ebce831fe41abb076e68fa479f38c504

These are bytes loaded with FileParser::ReadAllBytes on PC, despite .xfbin
file names. They are NOT NUCC XFBIN wrappers. The first two contain
uint32 little-endian ID lists; CharRelation contains repeated
uint32(count), followed by count uint32 IDs, allowing empty lists.
No Switch native ABI, authorizations, resource lifetime, or gameplay proof.
"""
import hashlib
import re
import struct

MAX_INPUT_BYTES=4*1024*1024
MAX_ROWS=10000
SHA=re.compile(r'[0-9a-f]{64}\Z')
SOURCE={
    'ougiAwakeningParam':('xinput9_1_0/OugiAwakeningParam.cpp','69456b8b1823d8f6d79e572088c756879e96bd40'),
    'gudoBallParam':('xinput9_1_0/GudoBallParam.cpp','755c6dd2e4104afdcae54408a7d3443dcc6eb614'),
    'charRelationParam':('xinput9_1_0/CharRelationParam.cpp','4dc5ceb3ebce831fe41abb076e68fa479f38c504'),
}
UPSTREAM_COMMIT='a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc'


def inspect(raw,family,expected_sha256):
    if family not in SOURCE:
        raise ValueError('Unrecognized PC ModdingAPI family')
    if not isinstance(raw, bytes):
        raise ValueError('PC raw input must be bytes')
    if type(expected_sha256) is not str or not SHA.fullmatch(expected_sha256):
        raise ValueError('Explicit lowercase SHA256 required')
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected_sha256:
        raise ValueError('Source SHA256 mismatch')
    if not raw or len(raw)>MAX_INPUT_BYTES or len(raw)%4:
        raise ValueError('Nonempty uint32-aligned PC raw data required, max 4 MiB')
    rows=[]
    if family in ('ougiAwakeningParam','gudoBallParam'):
        if len(raw)//4>MAX_ROWS:
            raise ValueError('Excessive PC character entries')
        ids=[i[0] for i in struct.iter_unpack('<I',raw)]
        rows=[{'ordinal':i,'character_id_u32':id} for i,id in enumerate(ids)]
        mode='ordered_uint32_character_ids'
        unique_count=len(set(ids))
        duplicate_count=len(ids)-unique_count
    else:
        # C++ expands a table on PC and parses length-prefixed ID arrays.
        # In particular it permits count==0 and only breaks on malformed
        # bytes. We reject all partial/trailing input to avoid partial maps.
        offset=0
        while offset<len(raw):
            if len(rows)==MAX_ROWS:
                raise ValueError('Too many PC relation records')
            if len(raw)-offset<4:
                raise ValueError('Truncated PC relation record header')
            at=offset
            count=struct.unpack_from('<I',raw,offset)[0]
            offset+=4
            if count>(len(raw)-offset)//4:
                raise ValueError('Truncated or excessive PC relation ID list')
            # No external pointers; no access to game memory.
            ids=[v[0] for v in struct.iter_unpack('<I',raw[offset:offset+count*4])]
            rows.append({'ordinal':len(rows),'byte_offset':at,'id_count':count,
                         'character_ids_u32':ids})
            offset+=count*4
        mode='count_prefixed_uint32_id_arrays'
        unique_count=None
        duplicate_count=None
    path,blob=SOURCE[family]
    return {
        'status':'PASS_PC_SOURCE_FORMAT_ONLY',
        'family':family,'source_commit':UPSTREAM_COMMIT,
        'source_path':path,'source_git_blob':blob,
        'source_bytes_sha256':digest,'source_length_bytes':len(raw),
        'format':mode,'record_count':len(rows),
        'unique_character_ids':unique_count,
        'duplicate_occurrences_preserved_in_order':duplicate_count,
        'records':rows,'source_is_PC_raw_not_NUCC_XFBIN':True,
        'public_source_sample_sha256_authenticated':False,
        'native_Switch_v170_reader_integrated':False,
        'PC_x64_binary_hooks_not_ported_to_ARM64':True,
        'original_game_behavior_preserved':True,
        'actual_Uzuy_gameplay_tested':False,'full_moddingapi':False
    }
