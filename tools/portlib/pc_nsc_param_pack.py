"""PC Mod Manager ZIP -> source-authenticated, native-validated nine-family pack.

Only source-valid PC raw *bytes* are included. Explicit family/source mapping
is mandatory; .xfbin extension must NEVER imply NUCC, moveset, model or a
Switch resource ABI. Cross-mod same-family winner is refused while original
archive precedence and engine consumer ownership remain unresolved.

The pack is a CALLER-OWNED source-data input for compiled nsc_pc_pack_*.
It is not an Atmosphere mod or game parameter patch.
"""
import hashlib
import json
import os
import struct
import tempfile
import zipfile
from pathlib import Path
from .pc_api_manifest import FAMILY_READERS, MAX_INPUT_BYTES
from .native_cpk_graph import MAIN_SHA256
from .pc_nsc_archive_stage import _source_archive, _members, _safe_name
from .pc_nsc_cpk_candidates import _regular_staged, _verified_file

FAMILIES=(
    "susanooCondParam","partnerSlotParam","ougiAwakeningParam",
    "gudoBallParam","charRelationParam","pairSpSkillManagerParam",
    "bgmManagerParam","specialInteractionManager","guardEffectParam")
MAGIC=b"NSC_PC_PACK_V1\x00\x00"
HEADER=64
RECORD=48
DATA_START=HEADER+len(FAMILIES)*RECORD
MAX_MODS=16

def _byte_sha(raw):
    return hashlib.sha256(raw).digest()

def _input_spec(spec):
    if type(spec)!=dict or set(spec)!={"original_main","mods"}:
        raise ValueError("Only original_main/mods are allowed")
    origin=spec["original_main"]
    if type(origin)!=dict or set(origin)!={"path","sha256"} or origin["sha256"]!=MAIN_SHA256:
        raise ValueError("Original Switch 1.70 main must match pinned SHA256")
    mods=spec["mods"]
    if type(mods)!=list or not 1<=len(mods)<=MAX_MODS:
        raise ValueError("Expected one to 16 source mods")
    names=set();families=set();resource_paths=set()
    for mod in mods:
        if type(mod)!=dict or set(mod)!={"mod_id","staged_path","original_archive","source_sha256","resources"}:
            raise ValueError("Explicit staged ZIP source and resources required")
        name=mod["mod_id"]
        if type(name)!=str or not name or len(name)>32 or not all(c in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in name) or name in names:
            raise ValueError("Invalid or duplicate mod_id")
        names.add(name)
        rows=mod["resources"]
        if type(rows)!=list or not rows or len(rows)>len(FAMILIES):
            raise ValueError("Each participating mod must declare PC raw sources")
        for item in rows:
            if type(item)!=dict or set(item)!={"family","source_path"}:
                raise ValueError("Explicit PC family/source_path required")
            name_raw,is_dir=_safe_name(item["source_path"])
            if is_dir:
                raise ValueError("PC raw source cannot be directory")
            # A PC archive path cannot have two independent family owners, even
            # when the families differ. Never guess source-path precedence.
            canonical_path=name_raw.casefold()
            if canonical_path in resource_paths:
                raise ValueError("Duplicate or casefold-colliding PC source path across mods")
            resource_paths.add(canonical_path)
            if item["family"] not in FAMILIES or item["family"] in families:
                raise ValueError("Unknown or conflicting PC raw family: refuse precedence guess")
            families.add(item["family"])
    return families

def _sources(spec):
    selected={}
    for mod in spec["mods"]:
        archive,archive_stat=_source_archive(mod["original_archive"],mod["source_sha256"])
        stage_root=Path(mod["staged_path"])
        manifest_file=stage_root/"manifest.json"
        if stage_root.is_symlink() or manifest_file.is_symlink() or not manifest_file.is_file():
            raise ValueError("Missing or symlinked source stage manifest")
        manifest=json.loads(manifest_file.read_text())
        if (manifest.get("status")!="STAGED_OFFLINE_NSC_PC_ZIP_INPUT_NOT_SWITCH_MOD_RELEASE" or
            manifest.get("source_archive_sha256")!=mod["source_sha256"] or
            manifest.get("source_archive_filename")!=archive.name or
            manifest.get("source_archive_size")!=archive_stat.st_size):
            raise ValueError("Source stage manifest lacks original ZIP provenance")
        entries=manifest.get("files")
        if type(entries)!=list:
            raise ValueError("Original stage members missing")
        index={}
        for item in entries:
            if type(item)!=dict or type(item.get("path"))!=str or type(item.get("sha256"))!=str:
                raise ValueError("Malformed original ZIP manifest row")
            canonical,is_dir=_safe_name(item["path"])
            if is_dir or canonical in index:
                raise ValueError("Duplicate or malformed original source path")
            index[canonical]=item
        with zipfile.ZipFile(archive) as z:
            original={name:info for name,is_dir,info in _members(z)[0] if not is_dir}
            if set(original)!=set(index):
                raise ValueError("Original ZIP differs from staged source manifest")
            for item in mod["resources"]:
                family=item["family"]
                name=item["source_path"]
                record=index.get(name)
                if record is None:
                    raise ValueError("Explicit PC raw file is not in original mod ZIP")
                src=_regular_staged(stage_root,name)
                _verified_file(src,record["sha256"],MAX_INPUT_BYTES)
                raw=src.read_bytes()
                if not raw or len(raw)>MAX_INPUT_BYTES:
                    raise ValueError("PC raw source exceeds capacity")
                zip_info=original[name]
                if zip_info.file_size!=len(raw):
                    raise ValueError("Original archive raw source length changed")
                with z.open(zip_info) as reader:
                    from_zip=reader.read(MAX_INPUT_BYTES+1)
                if from_zip!=raw:
                    raise ValueError("Original ZIP raw source differs from staged bytes")
                digest=hashlib.sha256(raw).hexdigest()
                if digest!=record["sha256"]:
                    raise ValueError("Original PC raw payload digest mismatch")
                report=FAMILY_READERS[family](raw,family,digest)
                rows=report.get("rows",report.get("records"))
                if not isinstance(rows,list) or report["record_count"]!=len(rows):
                    raise ValueError("Native PC family source lacks valid parser contract")
                selected[FAMILIES.index(family)]={
                    "raw":raw,"family":family,"mod_id":mod["mod_id"],
                    "original_source_path":name,
                    "source_archive_sha256":mod["source_sha256"],
                    "source_sha256":digest,"record_count":len(rows)}
    return selected

def _encode(rows):
    out=bytearray(DATA_START)
    out[:16]=MAGIC
    struct.pack_into("<IIII",out,16,1,9,0,sum(1<<family for family in rows))
    for family in sorted(rows):
        entry=HEADER+RECORD*family
        record=rows[family]
        padding=(-len(out))%16
        out.extend(bytes(padding))
        offset=len(out)
        raw=record["raw"]
        out.extend(raw)
        struct.pack_into("<II",out,entry,offset,len(raw))
        out[entry+8:entry+40]=bytes.fromhex(record["source_sha256"])
        struct.pack_into("<II",out,entry+40,record["record_count"],0)
    if len(out)>0xffffffff:
        raise ValueError("PC native pack > uint32 capacity")
    struct.pack_into("<I",out,24,len(out))
    out[32:64]=hashlib.sha256(out[:32]+out[64:]).digest()
    return bytes(out)

def assemble(spec,output):
    """Atomic source-verified pack staging, never game install."""
    _input_spec(spec)
    _verified_file(spec["original_main"]["path"],MAIN_SHA256)
    root=Path(output)
    if root.exists() or root.is_symlink():
        raise ValueError("Refusing to overwrite PC native pack output")
    parent=root.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ValueError("Output parent must be existing non-symlink directory")
    rows=_sources(spec)
    pack=_encode(rows)
    info={
        "status":"PC_ZIP_NINE_NATIVE_SOURCE_PACK_NOT_ENGINE_HOOK_OR_GAMEPLAY",
        "original_main_sha256":MAIN_SHA256,
        "format_magic":"NSC_PC_PACK_V1",
        "format_version":1,
        "family_mask":sum(1<<k for k in rows),
        "family_count":len(rows),
        "packed_sha256":hashlib.sha256(pack).hexdigest(),
        "packed_bytes":len(pack),
        "families":[
            {k:v for k,v in rows[i].items() if k!="raw"} for i in sorted(rows)],
        "duplicate_PC_family_precedence_assumed":False,
        "raw_PC_bytes_byte_equal_to_original_ZIP":True,
        "container_compiled_ARM64_reader_supported":True,
        "original_Switch_engine_param_consumers_connected":False,
        "native_loader_resource_lifetime_verified":False,
        "CRI_archive_priority_or_ownership_verified":False,
        "model_effect_audio_SFX_Japanese_voice_runtime_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False
    }
    with tempfile.TemporaryDirectory(prefix=".nsc-parampack-",dir=parent) as temp:
        dst=Path(temp)/"output"
        dst.mkdir()
        (dst/"pc_native_sources.pack").write_bytes(pack)
        (dst/"manifest.json").write_text(json.dumps(info,indent=2)+"\n")
        if root.exists():
            raise ValueError("Output appeared before atomic publication")
        os.replace(dst,root)
    return info
