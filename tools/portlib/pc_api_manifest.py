"""Common provenance-preserving read-only view of nine PC ModdingAPI payloads.

This adapter invokes existing, CI-verified PC raw parsers. It does NOT make
their outputs native Switch parameter tables. Identifiers/asset names are
candidate references only: CRI resource resolution and actor ownership need
verified native ABI, priority, factory and lifecycle evidence.
"""
import hashlib
import json
import re
from pathlib import Path
from . import pc_param_rows,pc_param_streams,pc_param_remaining

FAMILY_READERS={
    **{key:pc_param_rows.inspect for key in pc_param_rows.FAMILIES},
    **{key:pc_param_streams.inspect for key in pc_param_streams.SOURCE},
    **{key:pc_param_remaining.inspect for key in pc_param_remaining.SOURCE},
}
ALL_FAMILIES=frozenset(FAMILY_READERS)
MAX_INPUT_BYTES=4*1024*1024
MAX_MANIFEST_INPUTS=9
MAX_RESOURCE_REFS=100000
SHA_RE=re.compile(r"[0-9a-f]{64}\Z")


def _read_source(spec):
    if type(spec)!=dict or set(spec)!={"family","path","sha256"}:
        raise ValueError("Each source must declare only family, path, sha256")
    family=spec["family"]
    if not isinstance(family,str) or family not in ALL_FAMILIES:
        raise ValueError("Unrecognized PC source family")
    sha=spec["sha256"]
    if not isinstance(sha,str) or not SHA_RE.fullmatch(sha):
        raise ValueError("PC source must use exact lowercase SHA256")
    path=Path(spec["path"])
    if path.is_symlink() or not path.is_file():
        raise ValueError("PC source file is missing or symlinked")
    size=path.stat().st_size
    if not 0<size<=MAX_INPUT_BYTES:
        raise ValueError("PC source size is invalid or over limit")
    raw=path.read_bytes()
    if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:
        raise ValueError("PC source changed or differs from SHA256")
    return family,raw,sha,path.name


def _candidate_resources(family,rows):
    fields=()
    if family=="guardEffectParam":
        fields=("effect_path","start_effect","loop_effect","end_effect")
    elif family=="bgmManagerParam":
        fields=("stage_sound",)
    for row in rows:
        for field in fields:
            value=row[field]
            if value:
                yield {"family":family,"record_ordinal":row["ordinal"],
                       "field":field,"PC_string":value,
                       "resource_resolution_verified":False}


def build_manifest(sources,require_all_nine=False):
    if type(sources)!=list or not sources or len(sources)>MAX_MANIFEST_INPUTS:
        raise ValueError("Expected one to nine PC source records")
    source_names=set();reports={};resources=[];sha_inputs=[]
    # Sorted to keep JSON identity deterministic regardless of spec order.
    indexed=[]
    for spec in sources:
        family,raw,sha,name=_read_source(spec)
        if family in source_names:
            raise ValueError("Duplicate PC family would hide source precedence")
        source_names.add(family)
        indexed.append((family,raw,sha,name))
    if require_all_nine and source_names!=ALL_FAMILIES:
        raise ValueError("Incomplete nine-family PC source manifest")
    for family,raw,sha,name in sorted(indexed):
        result=FAMILY_READERS[family](raw,family,sha)
        rows=result.get("rows",result.get("records"))
        if not isinstance(rows,list) or len(rows)!=result["record_count"]:
            raise ValueError("Incompatible read-only PC source reader output")
        if result.get("gameplay_verified") or result.get("full_moddingapi"):
            raise ValueError("Cannot claim PC parser supplies gameplay proof")
        resources.extend(_candidate_resources(family,rows))
        if len(resources)>MAX_RESOURCE_REFS:
            raise ValueError("Excessive unresolved PC resource candidates")
        reports[family]={
            "source_filename":name,"input_sha256":sha,"bytes":len(raw),
            "record_count":result["record_count"],
            "decoded_PC_rows":rows,
            "resource_strings_not_verified_in_CPK":True,
            "switch_native_ABI_verified":False,
            "switch_native_reader_integrated":False
        }
        sha_inputs.append((family,sha))
    canonical=json.dumps(sha_inputs,separators=(",",":"),ensure_ascii=True).encode()
    return {
        "status":"PC_API_SOURCES_VALIDATED_AND_INDEXED_ONLY",
        "manifest_identity_sha256":hashlib.sha256(canonical).hexdigest(),
        "PC_raw_family_count":len(reports),
        "all_nine_PC_raw_formats_supplied":set(reports)==ALL_FAMILIES,
        "missing_PC_families":sorted(ALL_FAMILIES-set(reports)),
        "source_families":reports,
        "unresolved_audio_effect_name_candidates":resources,
        "unresolved_audio_effect_name_count":len(resources),
        "resource_strings_are_not_loader_paths_or_verified_assets":True,
        "character_ID_lists_not_verified_ownership_or_factory_mapping":True,
        "code_patch_or_native_hook_written":False,
        "native_switch_170_integration_verified":False,
        "CRI_async_completion_verified":False,
        "CRI_archive_priority_winner_verified":False,
        "effect_and_audio_banks_verified":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False
    }
