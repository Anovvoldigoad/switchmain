"""Fail-closed PC NSC multi-mod -> Switch 1.70 CPK registration CANDIDATE staging.

Unlike a mere manifest audit, this builds a binary profile using the actual
Switch runtime profile encoder and copies source-authenticated original CPK
bytes into the corresponding sim:data/moddingapi/... data tree. A ZIP staging
manifest is not enough: original .nsc/.unse/.uns/.ensc ZIP SHA, each selected
original ZIP entry and staged CPK bytes must all match, and the original
Switch v1.70 main is pinned exactly.

Every CPK TOC path must be unique across all candidates and optional reference
archives. On conflict refuse the build; real CRI archive lookup order is not
known. No main patch, native loader, claimed runtime-safe API, or installable
Atmosphere/Uzuy release is produced.
"""
import hashlib
import json
import mmap
import os
import re
import shutil
import stat
import tempfile
import zipfile
from contextlib import ExitStack
from pathlib import Path

from . import cpk_events,cpk_profile
from .native_cpk_graph import MAIN_SHA256
from .pc_nsc_archive_stage import _safe_name,_source_archive,_members

MOD_ID=re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")
SHA256=re.compile(r"[0-9a-f]{64}\Z")
MAX_CPK_BYTES=2*1024*1024*1024
MAX_REFS=16

def _verified_file(path,want_sha,size_limit=None):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Expected regular non-symlink file: "+str(p))
    before=p.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size<=0 or (
        size_limit is not None and before.st_size>size_limit):
        raise ValueError("Unacceptable source file size: "+str(p))
    if not isinstance(want_sha,str) or not SHA256.fullmatch(want_sha):
        raise ValueError("Expected explicit lowercase SHA256")
    sha=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            sha.update(block)
    if sha.hexdigest()!=want_sha:
        raise ValueError("File SHA256 mismatch: "+str(p))
    after=p.stat()
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(
        after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError("Source changed while hashing: "+str(p))
    return p,before.st_size

def _regular_staged(root,relative):
    """Reject symlink traversals beneath staging root, including parents."""
    p=Path(root)
    if p.is_symlink() or not p.is_dir():
        raise ValueError("Staging root must be a regular directory")
    name,isdir=_safe_name(relative)
    if isdir:
        raise ValueError("Archive source must be a file")
    current=p
    for component in ("mod",*name.split("/")):
        current=current/component
        if current.is_symlink():
            raise ValueError("Staging path traverses a symlink")
    if not current.is_file():
        raise ValueError("Staged archive member missing: "+name)
    return current

def _source_zip_selected_sha(z,member):
    """Prove the staged CPK matches exact selected original compressed ZIP member."""
    sha=hashlib.sha256()
    size=0
    with z.open(member,"r") as inp:
        while True:
            block=inp.read(1024*1024)
            if not block:
                break
            sha.update(block);size+=len(block)
            if size>MAX_CPK_BYTES:
                raise ValueError("Original ZIP CPK exceeds source budget")
    return sha.hexdigest(),size

def _cpk_entries(source,want_sha):
    p,n=_verified_file(source,want_sha,MAX_CPK_BYTES)
    with p.open("rb") as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as blob:
        toc=cpk_events.entries(blob)
        if not toc:
            raise ValueError("Candidate CPK cannot have empty TOC")
        # No extracted bytes are interpreted as model/effect/audio. The caller
        # intentionally fails closed on ANY duplicated TOC casefold key.
        return sorted((name.casefold(),name) for name in toc),n

def _validate_spec(spec):
    if type(spec)!=dict or set(spec)!={"original_main","mods","reference_archives"}:
        raise ValueError("Require only original_main/mods/reference_archives")
    orig=spec["original_main"]
    if type(orig)!=dict or set(orig)!={"path","sha256"} or orig["sha256"]!=MAIN_SHA256:
        raise ValueError("Require exact known-original Switch v1.70 main fingerprint")
    mods=spec["mods"]
    refs=spec["reference_archives"]
    if (type(mods)!=list or not 1<=len(mods)<=16 or
        type(refs)!=list or len(refs)>MAX_REFS):
        raise ValueError("One to 16 mods, zero to 16 reference CPKs required")
    seen=set();total_cpks=0
    for mod in mods:
        if type(mod)!=dict or set(mod)!={
            "mod_id","staged_path","original_archive","source_sha256","cpks"}:
            raise ValueError("Explicit mod source and CPK paths required")
        mod_id=mod["mod_id"]
        if type(mod_id)!=str or not MOD_ID.fullmatch(mod_id) or mod_id in seen:
            raise ValueError("Invalid/duplicated mod_id")
        seen.add(mod_id)
        rows=mod["cpks"]
        if type(rows)!=list or not rows:
            raise ValueError("Each mod must list at least one CPK")
        total_cpks+=len(rows)
        for item in rows:
            if type(item)!=dict or set(item)!={
                "source_path","runtime_path","priority"}:
                raise ValueError("CPK must explicitly name source_path/runtime_path/priority")
            name,isdir=_safe_name(item["source_path"])
            if isdir or not name.casefold().endswith(".cpk"):
                raise ValueError("Explicit CPK source must name a .cpk member")
            runtime=item["runtime_path"]
            cpk_profile.validate_path(runtime)
            if not runtime.startswith(cpk_profile.PREFIX+mod_id+"/"):
                raise ValueError("CPK registration path must belong to declared mod_id")
    if total_cpks>cpk_profile.CAPACITY:
        raise ValueError("Exceeded 32 registered CPK capacity")
    for ref in refs:
        if type(ref)!=dict or set(ref)!={"label","path","sha256"}:
            raise ValueError("Reference CPK label/path/sha256 required")
        label=ref["label"]
        if (type(label)!=str or not MOD_ID.fullmatch(label) or
            label in seen):
            raise ValueError("Duplicate/invalid reference label")
        seen.add(label)
    registrations=[{"path":c["runtime_path"],"priority":c["priority"]}
                   for m in mods for c in m["cpks"]]
    cpk_profile.validate_rows(registrations)
    return registrations

def assemble(spec,output):
    """Publish a noninstallable candidate CPK tree and binary profile atomically."""
    registrations=_validate_spec(spec)
    _verified_file(spec["original_main"]["path"],MAIN_SHA256)
    root=Path(output)
    if root.exists() or root.is_symlink():
        raise ValueError("Candidate output already exists")
    parent=root.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ValueError("Candidate output parent must already exist")
    selected=[];catalog={};descriptions=[]
    for mod in spec["mods"]:
        archive,arc_stat=_source_archive(mod["original_archive"],mod["source_sha256"])
        stage=Path(mod["staged_path"])
        manifest_path=stage/"manifest.json"
        if stage.is_symlink() or manifest_path.is_symlink():
            raise ValueError("Symlinked stage/manifest refused")
        manifest=json.loads(manifest_path.read_text())
        if (manifest.get("source_archive_sha256")!=mod["source_sha256"] or
            manifest.get("source_archive_filename")!=archive.name or
            manifest.get("source_archive_size")!=arc_stat.st_size or
            manifest.get("status")!="STAGED_OFFLINE_NSC_PC_ZIP_INPUT_NOT_SWITCH_MOD_RELEASE"):
            raise ValueError("Original ZIP provenance does not match staged source")
        files=manifest.get("files")
        if type(files)!=list:
            raise ValueError("Staging manifest source file array required")
        indexed={}
        for item in files:
            if type(item)!=dict or not all(k in item for k in
                    ("path","sha256","source_member_size","asset_class")):
                raise ValueError("Staged source manifest file metadata invalid")
            name,isdir=_safe_name(item["path"])
            if isdir or name in indexed:
                raise ValueError("Staged member is not a unique filename")
            indexed[name]=item
        with zipfile.ZipFile(archive,"r") as z:
            members,_=_members(z)
            original={name:entry for name,isdir,entry in members if not isdir}
            if set(original)!=set(indexed):
                raise ValueError("Staged manifest source entries differ from original ZIP")
            for entry in mod["cpks"]:
                name=entry["source_path"]
                item=indexed.get(name)
                if item is None or item["asset_class"]!="CPK_UNVERIFIED":
                    raise ValueError("Declared CPK is missing or incorrectly classified")
                path=_regular_staged(stage,name)
                hashed,n=_verified_file(path,item["sha256"],MAX_CPK_BYTES)
                if type(item["source_member_size"]) is not int or (
                    item["source_member_size"]!=n):
                    raise ValueError("Staged CPK length differs from declared length")
                archive_sha,archive_length=_source_zip_selected_sha(z,original[name])
                if archive_sha!=item["sha256"] or archive_length!=n:
                    raise ValueError("Staged CPK and original ZIP entry differ")
                toc,_=_cpk_entries(hashed,item["sha256"])
                source_id=mod["mod_id"]+":"+name
                for key,path_name in toc:
                    catalog.setdefault(key,[]).append({
                        "owner":source_id,"original_TOC_path":path_name})
                selected.append({"mod_id":mod["mod_id"],"source_path":name,
                                 "verified_file_path":str(hashed),
                                 "sha256":item["sha256"],
                                 "runtime_path":entry["runtime_path"],
                                 "priority":entry["priority"],
                                 "file_size_bytes":n,"TOC_entry_count":len(toc)})
        descriptions.append({"mod_id":mod["mod_id"],
                             "source_archive_sha256":mod["source_sha256"],
                             "verified_selected_CPK_count":len(mod["cpks"])})
    reference=[]
    for item in spec["reference_archives"]:
        table,n=_cpk_entries(item["path"],item["sha256"])
        for key,path in table:
            catalog.setdefault(key,[]).append({
                "owner":"reference:"+item["label"],"original_TOC_path":path})
        reference.append({"label":item["label"],"sha256":item["sha256"],
                          "entry_count":len(table),"bytes":n,
                          "original_stock_provenance_verified":False})
    overlaps={key:owners for key,owners in sorted(catalog.items())
              if len(owners)>1}
    if overlaps:
        example=next(iter(overlaps))
        raise ValueError("Unresolved original CPK TOC collision: "+example+
                         " (no trusted CRI archive precedence)")
    profile=cpk_profile.encode(registrations)
    if cpk_profile.decode(profile)!=registrations:
        raise ValueError("Generated CPK profile could not round-trip")
    result={
        "status":"SOURCE_VERIFIED_CONFLICT_FREE_CPK_CANDIDATE_TREE_NOT_GAMEPLAY",
        "source_original_main_sha256":MAIN_SHA256,
        "candidate_cpk_count":len(selected),
        "reference_cpk_count":len(reference),
        "source_mods":descriptions,
        "candidate_cpks":[{k:v for k,v in x.items() if k!="verified_file_path"}
                          for x in selected],
        "reference_CPks":reference,
        "unique_CPK_TOC_paths":len(catalog),
        "duplicate_CPK_TOC_paths":0,
        "profile_sha256":hashlib.sha256(profile).hexdigest(),
        "profile_rows":registrations,
        "profile_would_be_used_by_native_runtime_only_if_ABI_verified":True,
        "profile_is_not_directly_installed":True,
        "staged_CPK_payloads_are_byte_identical_to_original_ZIP":True,
        "reference_archive_origin_stock_or_mod_proven":False,
        "real_CRI_archive_precedence_proven":False,
        "native_fileopen_lifecycle_and_hooks_proven":False,
        "model_moveset_effect_audio_SFX_JP_voice_compatibility_proven":False,
        "real_Uzuy_gameplay_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False,
    }
    with tempfile.TemporaryDirectory(prefix=".nsc-cpk-candidate-",dir=parent) as tmp:
        stage=Path(tmp)/"output"
        stage.mkdir()
        for item in selected:
            suffix=item["runtime_path"][len("sim:"):]
            output_file=stage/"candidate_data_root"/Path(*suffix.split("/"))
            output_file.parent.mkdir(parents=True,exist_ok=True)
            digest=hashlib.sha256()
            with Path(item["verified_file_path"]).open("rb") as a,output_file.open("xb") as b:
                while True:
                    chunk=a.read(1024*1024)
                    if not chunk:
                        break
                    digest.update(chunk);b.write(chunk)
            if digest.hexdigest()!=item["sha256"]:
                raise ValueError("Copied CPK bytes changed while staging")
        (stage/"candidate_cpk_registration_profile.bin").write_bytes(profile)
        (stage/"candidate_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
        if root.exists():
            raise ValueError("Candidate output created concurrently")
        os.replace(stage,root)
    return result
