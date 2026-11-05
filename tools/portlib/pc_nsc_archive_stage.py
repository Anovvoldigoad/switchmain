"""Safe Android/Termux intake for actual NSC Mod Manager 2.1.2.1 ZIP mods.

Official TheLeonX/NSC-ModManager source:
  commit 276116ebf5ba398a867793cb02ee6c33c0927645
  ViewModel/TitleViewModel.cs Git blob f7ca7602d12cf9689a08fd6b7e55abc4dc8fd4ca
  InstallMod: .uns/.unse/.nsc/.ensc -> ZipFile.ExtractToDirectory;
  .nus4 -> a DIFFERENT ExtractNus4 transformation, intentionally rejected.

This port stages source bytes and their SHA256, but does not claim any
Switch v1.70 XFBIN/CPK compatibility, modded main, native API hooks,
audio/model/factory loading, resource ownership or gameplay.
"""
import hashlib
import json
import os
import re
import stat
import tempfile
import unicodedata
import zipfile
from pathlib import Path

SUPPORTED={".nsc",".uns",".unse",".ensc"}
MAX_ARCHIVE=4*1024*1024*1024
MAX_MEMBERS=12000
MAX_MEMBER=2*1024*1024*1024
MAX_TOTAL=6*1024*1024*1024
MAX_RATIO=512
MAX_PATH=240
SHA=re.compile(r"[0-9a-f]{64}\Z")

def _safe_name(value):
    if type(value)!=str or not value or len(value)>MAX_PATH:
        raise ValueError("Empty or overlong archive member name")
    if value.startswith(("/", "\\")) or "\\" in value or ":" in value:
        raise ValueError("Absolute/Windows-ambiguous archive path")
    if unicodedata.normalize("NFC",value)!=value:
        raise ValueError("Archive member Unicode path not NFC")
    if any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError("Archive member has control characters")
    directory=value.endswith("/")
    components=value[:-1].split("/") if directory else value.split("/")
    if not components or any(x in ("",".","..") or x.endswith(("."," "))
                             for x in components):
        raise ValueError("Ambiguous, traversal or Windows-unsafe archive path")
    return "/".join(components),directory

def _members(z):
    infos=z.infolist()
    if not infos or len(infos)>MAX_MEMBERS:
        raise ValueError("Empty or excessive mod ZIP entry count")
    seen=set();total=0;rows=[]
    for info in infos:
        name,isdir=_safe_name(info.filename)
        key=name.casefold()
        if key in seen:
            raise ValueError("Duplicate/case-aliased ZIP output path")
        seen.add(key)
        mode=info.external_attr>>16
        kind=stat.S_IFMT(mode)
        if kind not in (0,stat.S_IFREG,stat.S_IFDIR):
            raise ValueError("Symlink/device/special ZIP entry refused")
        if info.flag_bits&1:
            raise ValueError("Encrypted ZIP member cannot be safely inspected")
        if info.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED,
                                      zipfile.ZIP_BZIP2,zipfile.ZIP_LZMA):
            raise ValueError("Unsupported ZIP compression")
        if isdir and (info.file_size or kind==stat.S_IFREG):
            raise ValueError("Directory archive entry has file payload")
        if not isdir:
            if info.file_size>MAX_MEMBER:
                raise ValueError("ZIP member over size budget")
            if info.file_size and (info.compress_size==0 or
                                   info.file_size>info.compress_size*MAX_RATIO):
                raise ValueError("ZIP member exceeds compression-ratio safety budget")
            total+=info.file_size
            if total>MAX_TOTAL:
                raise ValueError("ZIP expands beyond total-size budget")
        rows.append((name,isdir,info))
    # File vs directory prefix collisions are checked independent of order.
    files={n.casefold() for n,d,_ in rows if not d}
    for name,_,_ in rows:
        bits=name.casefold().split("/")
        for i in range(1,len(bits)):
            if "/".join(bits[:i]) in files:
                raise ValueError("ZIP file occupies a required directory path")
    return sorted(rows,key=lambda x:x[0]),total

def _source_archive(path,sha256):
    src=Path(path)
    if src.is_symlink() or not src.is_file() or src.suffix.lower() not in SUPPORTED:
        raise ValueError("Expected actual ZIP-format .nsc/.uns/.unse/.ensc input")
    if type(sha256)!=str or not SHA.fullmatch(sha256):
        raise ValueError("Explicit lowercase expected archive SHA256 required")
    before=src.stat()
    if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=MAX_ARCHIVE:
        raise ValueError("Archive file size/type invalid")
    digest=hashlib.sha256()
    with src.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    if digest.hexdigest()!=sha256:
        raise ValueError("Source mod archive SHA256 mismatch")
    after=src.stat()
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(
        after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError("Mod ZIP source changed during hashing")
    return src,after

def _asset_kind(path):
    low=path.lower()
    if low.endswith(".cpk"):
        return "CPK_UNVERIFIED"
    if low.endswith((".xfbin",".xfbin.bak")):
        return "XFBIN_UNVERIFIED"
    if low.endswith((".nus3bank",".nus3audio",".wav",".wem",".ogg")):
        return "AUDIO_UNVERIFIED"
    if low.endswith((".png",".dds",".tga",".tex")):
        return "TEXTURE_UNVERIFIED"
    if low.endswith((".ini",".txt",".json")):
        return "METADATA_OR_CONFIG_UNVERIFIED"
    return "OTHER_UNVERIFIED"

def stage(archive,expected_sha256,output):
    """Publish a byte-identical, hash-indexed OFFLINE input folder atomically.

    Output must not exist and is a NEW directory. No original source, CPK
    or game file is mutated. No Switch install/mod release is generated.
    """
    src,before=_source_archive(archive,expected_sha256)
    destination=Path(output)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Refusing overwrite of existing staging output")
    parent=destination.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ValueError("Output parent must be an existing real directory")
    with zipfile.ZipFile(src,"r") as z:
        items,total=_members(z)
        with tempfile.TemporaryDirectory(prefix=".nsc-stage-",dir=parent) as temp:
            staged=Path(temp)/"output"
            modroot=staged/"mod"
            modroot.mkdir(parents=True)
            report=[]
            for name,isdir,info in items:
                dst=modroot.joinpath(*name.split("/"))
                if isdir:
                    dst.mkdir(parents=True,exist_ok=True)
                    continue
                dst.parent.mkdir(parents=True,exist_ok=True)
                digest=hashlib.sha256()
                size=0
                # ZipFile.open validates CRC at end; exclusive create prevents
                # duplicate archive paths from being silently overwritten.
                with z.open(info,"r") as reader, dst.open("xb") as writer:
                    while True:
                        chunk=reader.read(1024*1024)
                        if not chunk:
                            break
                        size+=len(chunk)
                        if size>MAX_MEMBER or size>info.file_size:
                            raise ValueError("Extracted ZIP member exceeds declared size")
                        digest.update(chunk)
                        writer.write(chunk)
                if size!=info.file_size:
                    raise ValueError("ZIP member size changed during extraction")
                report.append({"path":name,"source_member_size":size,
                    "stored_zip_member_size":info.compress_size,
                    "sha256":digest.hexdigest(),"asset_class":_asset_kind(name),
                    "switch_CPK_or_XFBIN_compatibility_verified":False})
            current=src.stat()
            if (current.st_dev,current.st_ino,current.st_size,current.st_mtime_ns)!=(
                before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns):
                raise ValueError("Source mod archive changed before publication")
            result={
                "status":"STAGED_OFFLINE_NSC_PC_ZIP_INPUT_NOT_SWITCH_MOD_RELEASE",
                "source_original_manager_repo":"TheLeonX/NSC-ModManager",
                "source_original_manager_commit":"276116ebf5ba398a867793cb02ee6c33c0927645",
                "source_original_manager_installmod_blob":"f7ca7602d12cf9689a08fd6b7e55abc4dc8fd4ca",
                "source_archive_filename":src.name,
                "source_archive_sha256":expected_sha256,
                "source_archive_size":before.st_size,
                "extracted_file_count":len(report),
                "total_extracted_bytes":total,
                "files":report,
                "staged_mod_subdirectory":"mod",
                "original_mod_extensions_zip_only":sorted(SUPPORTED),
                "nus4_special_conversion_supported":False,
                "actual_runtime_native_abi_verified":False,
                "actual_PC_mod_gameplay_compatibility_verified":False,
                "original_stock_CPK_authenticated":False,
                "merged_PC_manager517_authenticated":False,
                "CPK_archive_precedence_verified":False,
                "model_audio_SFX_JP_voice_runtime_verified":False,
                "new_native_hook_added":False,
                "full_moddingapi":False,
                "ready_for_gameplay_test":False,
                "emulator_tested":False,
            }
            (staged/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
            if destination.exists():
                raise ValueError("Output appeared before publication")
            os.replace(staged,destination)
            return result
