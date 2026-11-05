"""Exact-string PC ModdingAPI resource-name to CPK TOC cross-reference.

Unlike an audio/effect loader this reads *only* TOC metadata of an explicitly
SHA-pinned CPK and source-verified PC raw parameter files. It does not assume
BGM stage sound names equal archive paths, infer extensions, use fuzzy
substring matches, open resource data, claim priority across archives, or
patch/provide copyrighted game data. Names are candidates, not proof of CRI
runtime resolution or platform compatibility.
"""
import hashlib
import mmap
import re
import stat
from contextlib import ExitStack
from pathlib import Path

from .cpk_events import entries,canonical
from .pc_api_manifest import build_manifest

MAX_ARCHIVES=24
MAX_ARCHIVE_SIZE=2*1024*1024*1024
SHA_RE=re.compile(r"[0-9a-f]{64}\Z")


def _index_archive(spec,stack):
    if type(spec)!=dict or set(spec)!={"label","path","sha256"}:
        raise ValueError("Archive must explicitly name label, path and SHA256")
    label=spec["label"]
    if not isinstance(label,str) or not label or len(label)>80:
        raise ValueError("Invalid archive label")
    wanted=spec["sha256"]
    if not isinstance(wanted,str) or not SHA_RE.fullmatch(wanted):
        raise ValueError("Explicit lowercase archive SHA256 required")
    p=Path(spec["path"])
    if p.is_symlink() or not p.is_file():
        raise ValueError("Only regular non-symlink CPK input permitted")
    before=p.stat()
    if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=MAX_ARCHIVE_SIZE:
        raise ValueError("Invalid CPK source file size/type")
    f=stack.enter_context(p.open("rb"))
    blob=stack.enter_context(mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ))
    actual=hashlib.sha256(blob).hexdigest()
    if actual!=wanted:
        raise ValueError("Archive SHA256 mismatch: "+label)
    table=entries(blob)
    after=p.stat()
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(
        after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError("Archive changed during metadata audit")
    # Never return mmap or file handles, and do not copy archive payloads.
    return {
        "label":label,
        "filename":p.name,
        "sha256":actual,
        "file_size_bytes":before.st_size,
        "entries":table,
    }


def _valid_raw_path(value):
    if type(value)!=str or not value:
        return False
    try:
        return canonical(value)==value
    except ValueError:
        return False


def audit(source_specs,archive_specs,require_all_nine=False):
    if type(archive_specs)!=list or not 1<=len(archive_specs)<=MAX_ARCHIVES:
        raise ValueError("Require one to 24 explicit CPK archives")
    manifest=build_manifest(source_specs,require_all_nine=require_all_nine)
    seen_labels=set();seen_hashes=set()
    with ExitStack() as stack:
        archives=[]
        for spec in archive_specs:
            row=_index_archive(spec,stack)
            if row["label"] in seen_labels or row["sha256"] in seen_hashes:
                raise ValueError("Duplicate archive label or byte-identical archive")
            seen_labels.add(row["label"])
            seen_hashes.add(row["sha256"])
            archives.append(row)
    archives.sort(key=lambda a:a["label"])
    index={}
    for archive in archives:
        for path,row in archive["entries"].items():
            index.setdefault(path,[]).append({
                "archive_label":archive["label"],
                "entry_path":path,
                "cpk_entry_id":row["id"],
                "cpk_stored_size":row["stored_size"],
                "cpk_extracted_size":row["size"],
                "cpk_entry_compressed":row["stored_size"]!=row["size"],
            })
    lower={}
    for path in index:
        lower.setdefault(path.casefold(),[]).append(path)
    matches=[]
    exact_count=0
    collision_count=0
    case_only=0
    for candidate in manifest["unresolved_audio_effect_name_candidates"]:
        token=candidate["PC_string"]
        valid=_valid_raw_path(token)
        exact=index.get(token,[]) if valid else []
        folded=sorted(p for p in lower.get(token.casefold(),[]) if p!=token) if valid else []
        if exact:exact_count+=1
        if len(exact)>1:collision_count+=1
        if folded and not exact:case_only+=1
        matches.append({
            "family":candidate["family"],
            "record_ordinal":candidate["record_ordinal"],
            "field":candidate["field"],
            "PC_raw_string":token,
            "CPK_canonical_path_syntax":valid,
            "literal_case_sensitive_TOC_matches":exact,
            "casefold_only_path_candidates":folded[:24],
            "casefold_candidates_truncated":len(folded)>24,
            "number_of_literal_archive_occurrences":len(exact),
            "cross_archive_duplicate_path":len(exact)>1,
            "resource_runtime_resolution_proven":False,
        })
    return {
        "status":"PC_RESOURCE_LITERAL_CPK_TOC_CROSS_REFERENCE_ONLY",
        "manifest_identity_sha256":manifest["manifest_identity_sha256"],
        "PC_families":manifest["PC_raw_family_count"],
        "archives":[
            {key:a[key] for key in ("label","filename","sha256","file_size_bytes")}
            | {"TOC_path_count":len(a["entries"])}
            for a in archives
        ],
        "PC_resource_name_candidates":len(matches),
        "literal_case_sensitive_TOC_hit_candidates":exact_count,
        "cross_archive_duplicate_literal_path_candidates":collision_count,
        "casefold_only_candidates":case_only,
        "candidates":matches,
        "only_original_unmodified_bytes_hashed_and_read":True,
        "archive_origin_is_trusted_stock_verified":False,
        "archive_runtime_priority_or_winning_path_verified":False,
        "exact_TOC_path_match_is_not_audio_effect_loader_proof":True,
        "compressed_resource_payloads_not_decoded":True,
        "native_Switch_factory_or_actor_ABI_verified":False,
        "native_hooks_added":False,
        "gameplay_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False
    }
