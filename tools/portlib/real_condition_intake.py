"""Byte-grounded 517-row PC manager and paired Switch CPK audit entrypoint.

This layer does not replace the previously tested condition/CPK parsers.
It calculates real input SHA256 with streaming reads and feeds exact hashes
into the existing archive audit, so users can do one command in Termux.

An observed archive hash DOES NOT authenticate the claimed stock/update
provenance. Without an independently trusted source manifest, a modified
CPK may still be labeled 'stock' by its owner. No such claim is made here.
"""
import hashlib
import os
import re
import stat
from pathlib import Path

from .condition_archive_audit import inspect as inspect_cpk_pair
from .condition_profile import PC_RECORD_SIZE, compile_table

TARGET_PC_ROWS=517
MAX_CPK_BYTES=2*1024*1024*1024
MAX_DISCOVERY_FILES=200000
MAX_MANAGER_CANDIDATES=24
HEX_SHA=re.compile(r"[0-9a-f]{64}\Z")


def _file_info(p,max_bytes):
    path=Path(p)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Expected regular non-symlink source file: "+str(path))
    st=path.stat()
    if not stat.S_ISREG(st.st_mode) or st.st_size<=0 or st.st_size>max_bytes:
        raise ValueError("Input file length/type invalid: "+str(path))
    sha=hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block=stream.read(1024*1024)
            if not block:break
            sha.update(block)
    after=path.stat()
    if (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError("File changed while SHA256 was read")
    return {"name":path.name,"size_bytes":st.st_size,"sha256":sha.hexdigest()},path


def discover_manager(root):
    """Find uniquely matching public-baseline-compatible raw PC 517 manager.

    Only names with 'conditionprmmanager' are opened, and only if size
    matches 517 * 112. Directory symlinks are never followed. Ambiguous
    candidates do not select automatically.
    """
    top=Path(root)
    if top.is_symlink() or not top.is_dir():
        raise ValueError("Invalid discovery root")
    found=[]
    visited=0
    for parent,dirs,files in os.walk(top,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()]
        for name in files:
            visited+=1
            if visited>MAX_DISCOVERY_FILES:
                raise ValueError("PC manager search budget exceeded")
            if "conditionprmmanager" not in name.lower():continue
            p=Path(parent)/name
            if p.is_symlink() or not p.is_file() or p.stat().st_size!=TARGET_PC_ROWS*PC_RECORD_SIZE:
                continue
            raw=p.read_bytes()
            try:
                compile_table(raw) # exact source baseline/append identity
            except (ValueError,UnicodeDecodeError):
                continue
            found.append(p)
            if len(found)>MAX_MANAGER_CANDIDATES:
                raise ValueError("Too many manager517 candidates; select path manually")
    if len(found)!=1:
        raise ValueError("Expected exactly one authenticated-layout 517 PC manager candidate; found "+str(len(found)))
    return found[0]


def inspect(pc_manager,stock_cpk,candidate_cpk,
            expected_pc_manager_sha256=None,expected_stock_sha256=None,
            expected_candidate_sha256=None):
    for n,digest in (
        ("manager",expected_pc_manager_sha256),
        ("stock",expected_stock_sha256),
        ("candidate",expected_candidate_sha256)):
        if digest is not None and (not isinstance(digest,str) or not HEX_SHA.fullmatch(digest)):
            raise ValueError("Invalid expected "+n+" SHA256")
    manager_info,manager_path=_file_info(pc_manager,TARGET_PC_ROWS*PC_RECORD_SIZE)
    if manager_info["size_bytes"]!=TARGET_PC_ROWS*PC_RECORD_SIZE:
        raise ValueError("Required original *merged* PC manager517, not public 512-row template")
    if expected_pc_manager_sha256 and manager_info["sha256"]!=expected_pc_manager_sha256:
        raise ValueError("Expected original merged manager SHA256 mismatch")
    raw_manager=manager_path.read_bytes()
    if hashlib.sha256(raw_manager).hexdigest()!=manager_info["sha256"]:
        raise ValueError("PC manager changed before parsing")
    compile_table(raw_manager)
    stock_info,stock_path=_file_info(stock_cpk,MAX_CPK_BYTES)
    cand_info,cand_path=_file_info(candidate_cpk,MAX_CPK_BYTES)
    if stock_path.resolve()==cand_path.resolve() or (
        stock_info["sha256"]==cand_info["sha256"]):
        raise ValueError("Stock and candidate CPK must be distinct inputs and bytes")
    if expected_stock_sha256 and stock_info["sha256"]!=expected_stock_sha256:
        raise ValueError("Externally pinned stock CPK SHA256 mismatch")
    if expected_candidate_sha256 and cand_info["sha256"]!=expected_candidate_sha256:
        raise ValueError("Externally pinned candidate CPK SHA256 mismatch")
    report=inspect_cpk_pair(raw_manager,stock_path,stock_info["sha256"],
                            cand_path,cand_info["sha256"])
    if (report["stock_rows"],report["candidate_rows"])!=(512,TARGET_PC_ROWS):
        raise ValueError("Unexpected 512-stock/517-merged candidate geometry")
    if report["manager_sha256"]!=manager_info["sha256"]:
        raise ValueError("Manager identity disagrees with archive audit")
    # In the absence of a separately authenticated content manifest the
    # provenance remains unverified, even if the user supplies expected hashes.
    return {
        "status":"REAL_INPUT_BYTES_COMPARED_PROVENANCE_UNAUTHENTICATED",
        "pc_manager":manager_info,
        "stock_cpk":stock_info,
        "candidate_cpk":cand_info,
        "external_expected_sha256_fields_present":{
            "manager":expected_pc_manager_sha256 is not None,
            "stock":expected_stock_sha256 is not None,
            "candidate":expected_candidate_sha256 is not None,
        },
        "audit":report,
        "stock_origin_as_unmodified_game_verified":False,
        "merged_manager_origin_verified":False,
        "archive_lookup_precedence_verified":False,
        "emulator_tested":False,
        "ready_for_gameplay_test":False,
        "gameplay_verified":False,
        "full_moddingapi":False
    }
