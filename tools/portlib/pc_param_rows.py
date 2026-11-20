"""PC ModdingAPI raw 0x20 parameter readers. NOT Switch XFBIN/native loaders.

Pinned upstream PC source at TheLeonX/UltimateStormAPI
commit a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc:
  SusanooCondParam.cpp blob f738deb9b6bf93221ba6855bdd59552f43e8f0ae
  PartnerSlotParam.cpp blob ce8978d8b01998d8c16b00fb434cbe4ee8c62fdd

PC source uses raw FileParser::ReadAllBytes, divides by 0x20, reads type
string from [0:0x18] and the little-endian 16-bit char ID at +0x18.
Bytes +0x1A..+0x1F are opaque. Native Switch semantics are NOT inferred.
"""
import hashlib
import re
import struct

RECORD_SIZE=0x20
TYPE_WIDTH=0x18
MAX_RECORDS=8192
SHA=re.compile(r'[0-9a-f]{64}\Z')
SUSANOO={
    'SSN_2ITC':0x19,
    'SSN_2SSZ':0x38,
    'SSN_3SSK':0x55,
    'SSN_4SSI':0x60,
    'SSN_BSSZ':0xC1,
}
PARTNER={
    'PARTNER_TYPE_2PAR':0x2B,
    'PARTNER_TYPE_2KKG':0x2C,
    'PARTNER_TYPE_2AKM':0x29,
    'PARTNER_TYPE_2KRS':0x2A,
    'PARTNER_TYPE_1AKM':0x66,
    'PARTNER_TYPE_1KRS':0x6A,
    'PARTNER_TYPE_2SCX':0x45,
    'PARTNER_TYPE_8AEM':0xE6,
}
FAMILIES={
    'susanooCondParam':('xinput9_1_0/SusanooCondParam.cpp',
                        'f738deb9b6bf93221ba6855bdd59552f43e8f0ae',SUSANOO),
    'partnerSlotParam':('xinput9_1_0/PartnerSlotParam.cpp',
                        'ce8978d8b01998d8c16b00fb434cbe4ee8c62fdd',PARTNER),
}


def inspect(data, family, expected_sha256):
    if family not in FAMILIES:
        raise ValueError('Unsupported PC raw parameter family')
    if type(expected_sha256) is not str or not SHA.fullmatch(expected_sha256):
        raise ValueError('Explicit lowercase input SHA256 required')
    digest=hashlib.sha256(data).hexdigest()
    if digest!=expected_sha256:
        raise ValueError('PC raw parameter SHA256 mismatch')
    if len(data)==0 or len(data)%RECORD_SIZE or len(data)//RECORD_SIZE>MAX_RECORDS:
        raise ValueError('Expected nonempty aligned 0x20-byte PC source records')
    source,blob,mapping=FAMILIES[family]
    items=[];seen_charcodes=set()
    for i in range(len(data)//RECORD_SIZE):
        offset=i*RECORD_SIZE
        name_field=data[offset:offset+TYPE_WIDTH]
        if b'\0' not in name_field:
            raise ValueError(f'Unterminated PC type in raw record {i}')
        raw_name,padding=name_field.split(b'\0',1)
        try:
            name=raw_name.decode('ascii')
        except UnicodeDecodeError:
            raise ValueError(f'Non-ASCII PC type in raw record {i}') from None
        if name not in mapping:
            raise ValueError(f'Unknown PC {family} type at ordinal {i}: {name!r}')
        charcode=struct.unpack_from('<H',data,offset+TYPE_WIDTH)[0]
        if charcode in seen_charcodes:
            raise ValueError(f'Ambiguous duplicate PC character ID: {charcode}')
        seen_charcodes.add(charcode)
        opaque=data[offset+0x1a:offset+RECORD_SIZE]
        items.append({
            'ordinal':i, 'byte_offset':offset,
            'pc_type':name,'character_id_u16':charcode,
            'pc_source_associated_selector':mapping[name],
            'name_padding_contains_nonzero':any(padding),
            'opaque_six_bytes_sha256':hashlib.sha256(opaque).hexdigest(),
        })
    return {
        'status':'PC_RAW32_SOURCE_FORMAT_VALIDATED_ONLY',
        'family':family,'source_commit':'a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc',
        'source_path':source,'source_blob_sha':blob,
        'source_data_sha256':digest,'record_bytes':RECORD_SIZE,
        'type_width_bytes':TYPE_WIDTH,'pc_character_id_offset':TYPE_WIDTH,
        'record_count':len(items),'rows':items,
        'unknown_pc_type_rejected':True,'duplicate_character_id_rejected':True,
        'bytes_after_character_id_opaque':True,
        'source_format_is_raw_PC_payload_not_XFBIN':True,
        'pc_selector_mapping_not_native_Switch_factory_proof':True,
        'actual_pc_mod_sample_tested':False,
        'switch_v170_reader_integrated':False,
        'resource_lifecycle_verified':False,
        'gameplay_verified':False,'full_moddingapi':False,
    }
