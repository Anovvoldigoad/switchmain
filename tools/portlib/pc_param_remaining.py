"""Four remaining raw PC ModdingAPI parameter families; NOT Switch loaders.

Provenance (separate from binary source samples):
TheLeonX/UltimateStormAPI @ a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc.
- TeamUltimateJutsuManager.cpp, ReadPairSpSkillManagerParam: 0x18 rows,
  0x10-byte name, two signed int32s; source tolerates one terminal byte.
- BGMManager.cpp, ReadBGMFile: 0x68 rows, two 0x30 byte strings,
  int32 BGM ID and unknown field. CRC calculation is NOT reimplemented.
- SpecialInteractionManager.cpp, ReadSpecialInteractionParam:
  int32 record count, int32 main char, int32 trigger count, trigger IDs int32.
  Source ignores zero trigger IDs and skips main char zero.
- GuardEffectParam.cpp, GuardEffectParamRaw: packed 0xF8 row,
  two uint32 fields and five 0x30-byte fixed buffers.

Treat PC .xfbin filenames as raw ModdingAPI payloads, not NUCC containers.
This read-only tool refuses malformed inputs, never modifies source bytes,
and never installs x64 PC hooks or assumes Switch native ABI/offsets.
"""
import hashlib
import re
import struct

UPSTREAM_PC_API="a2d0f2206f5e5ca81c87eaaecc8bc6f3cbe42bdc"
UPSTREAM_PC_MANAGER="276116ebf5ba398a867793cb02ee6c33c0927645"
MAX_FILE_BYTES=4*1024*1024
MAX_ROWS=10000
SOURCE={
 "pairSpSkillManagerParam":{
  "source_path":"xinput9_1_0/TeamUltimateJutsuManager.cpp",
  "source_git_blob":"89045de50567733417894464663191ded16191ae",
  "source_entrypoint":"TUJManager::ReadPairSpSkillManagerParam"},
 "bgmManagerParam":{
  "source_path":"xinput9_1_0/BGMManager.cpp",
  "source_git_blob":"1790fdbce19f685e3bbcfb792bf81b06c425944a",
  "source_entrypoint":"BGMExpander::ReadBGMFile"},
 "specialInteractionManager":{
  "source_path":"xinput9_1_0/SpecialInteractionManager.cpp",
  "source_git_blob":"36a14c9db0bede3a89a70e89e9676c081d942255",
  "source_entrypoint":"SpecialInteractionManager::ReadSpecialInteractionParam"},
 "guardEffectParam":{
  "source_path":"xinput9_1_0/GuardEffectParam.cpp",
  "source_git_blob":"4dc87f05717a8574d3ed5db05ed54b3c83f89052",
  "source_entrypoint":"GuardEffectParam::ReadGuardEffectParam"}
}
SHA_RE=re.compile(r"[0-9a-f]{64}\Z")


def _pc_string(raw):
    """Preserve each original single byte; PC C++ treats fields as char[].
    Do not guess encoding or normalize case/path/file references."""
    return raw.split(b'\0',1)[0].decode("latin-1")


def inspect(raw, family, expected_sha256):
    if family not in SOURCE:
        raise ValueError("Unknown PC raw parameter family")
    if not isinstance(raw,bytes):
        raise ValueError("PC raw input bytes required")
    if not isinstance(expected_sha256,str) or not SHA_RE.fullmatch(expected_sha256):
        raise ValueError("Exact lowercase input SHA256 required")
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected_sha256:
        raise ValueError("PC input SHA256 mismatch")
    if not 0<len(raw)<=MAX_FILE_BYTES:
        raise ValueError("PC input must be nonempty and <=4 MiB")
    rows=[]
    extra={}
    if family=="pairSpSkillManagerParam":
        count,tail=divmod(len(raw),0x18)
        if tail not in (0,1) or not count or count>MAX_ROWS:
            raise ValueError("Invalid PC TUJ raw 0x18 row geometry")
        # Upstream accepts one extra terminal byte, regardless of value.
        extra["trailing_byte_ignored_by_pc_source"]=raw[-1] if tail else None
        extra["effective_pc_payload_bytes"]=count*0x18
        for n in range(count):
            at=n*0x18
            unlock,reserved=struct.unpack_from('<ii',raw,at+0x10)
            rows.append({"ordinal":n,"offset":at,
                         "name":_pc_string(raw[at:at+0x10]),
                         "unlock_value_i32":unlock,"reserved_i32":reserved})
    elif family=="bgmManagerParam":
        if len(raw)%0x68 or len(raw)//0x68>MAX_ROWS:
            raise ValueError("Invalid PC BGM raw 0x68 row geometry")
        for n in range(len(raw)//0x68):
            at=n*0x68
            bgm_id,unknown=struct.unpack_from('<ii',raw,at+0x60)
            rows.append({"ordinal":n,"offset":at,
                         "stage_name":_pc_string(raw[at:at+0x30]),
                         "stage_sound":_pc_string(raw[at+0x30:at+0x60]),
                         "bgm_id_i32":bgm_id,"unknown_i32":unknown})
        extra["native_crc32_and_bgm_function_ownership_unverified"]=True
    elif family=="guardEffectParam":
        if len(raw)%0xF8 or len(raw)//0xF8>MAX_ROWS:
            raise ValueError("Invalid PC GuardEffect raw 0xF8 row geometry")
        fields=("effect_path","start_effect","loop_effect","end_effect","coord")
        for n in range(len(raw)//0xF8):
            at=n*0xF8
            char_id,mode=struct.unpack_from('<II',raw,at)
            row={"ordinal":n,"offset":at,"character_id_u32":char_id,
                 "mode_u32":mode}
            for i,name in enumerate(fields):
                p=at+8+i*0x30
                row[name]=_pc_string(raw[p:p+0x30])
            rows.append(row)
        extra["effect_resource_paths_not_loaded_or_verified"]=True
    else:
        # PC source reads int32 record count; skipping zero IDs in runtime
        # does not alter raw stored values in this read-only audit.
        if len(raw)<4:
            raise ValueError("Truncated PC interaction header")
        count=struct.unpack_from('<i',raw,0)[0]
        if count<0 or count>MAX_ROWS:
            raise ValueError("Invalid PC interaction record count")
        pos=4
        for n in range(count):
            if len(raw)-pos<8:
                raise ValueError("Truncated PC interaction record header")
            at=pos
            main,triggers=struct.unpack_from('<ii',raw,pos)
            pos+=8
            if triggers<0 or triggers>(len(raw)-pos)//4:
                raise ValueError("Invalid PC interaction trigger count")
            ids=list(struct.unpack_from('<'+'i'*triggers,raw,pos)) if triggers else []
            pos+=triggers*4
            rows.append({"ordinal":n,"offset":at,"main_char_id_i32":main,
                         "trigger_ids_raw_i32":ids,
                         "nonzero_trigger_ids_i32":[i for i in ids if i!=0],
                         "pc_source_skips_zero_main_char":main==0})
        if pos!=len(raw):
            raise ValueError("Unparsed trailing PC interaction bytes")
        extra["source_ignores_zero_trigger_ids"]=True
        extra["source_skips_zero_main_char_entries"]=True
    return {
        "status":"PC_RAW_FORMAT_VALIDATED_ONLY",
        "family":family,
        "upstream_api_commit":UPSTREAM_PC_API,
        "upstream_manager_commit":UPSTREAM_PC_MANAGER,
        "source":SOURCE[family],
        "input_sha256":digest,
        "input_length":len(raw),
        "record_count":len(rows),
        "records":rows,
        **extra,
        "input_is_PC_raw_payload_not_NUCC_XFBIN":True,
        "native_Switch_loader_integrated":False,
        "native_Switch_abi_verified":False,
        "PC_runtime_call_semantics_ported":False,
        "audio_effect_resources_verified":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
    }
