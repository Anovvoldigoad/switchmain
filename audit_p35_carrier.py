#!/usr/bin/env python3
"""P35 v2: read-only comparison of Tobi carrier with stock CPKs.

Uses the already verified FastCPK --list output to obtain absolute offsets.
Compares packed/stored bytes only. No extraction, patching, or game mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path

HEAD = re.compile(r"^Files:\s*(\d+)\s+ContentOffset:\s*(\S+)\s+Align:\s*(\S+)\s+TOC:\s*(\S+)\s+ITOC:\s*(\S+)", re.M)
ROW = re.compile(r"^\s*(\d+)\s+0x([0-9a-fA-F]+)\s+(\d+)\s+(\d+)\s+(.+?)\s*$")
FASTCPK = Path.home()/".cache/naruto-fastcpk/target/release/fastcpk"

UNVERIFIED_GLOBALS = {
    "data/message/SWITCH/eng/messageInfo.bin.xfbin",
    "data/message/SWITCH/idid/messageInfo.bin.xfbin",
    "data/message/SWITCH/thth/messageInfo.bin.xfbin",
    "data/sound/cmnparam.xfbin",
    "data/spc/conditionprm.bin.xfbin",
    "data/spc/damageprm.bin.xfbin",
    "data/spc/privateCamera.bin.xfbin",
    "data/ui/flash/OTHER/charicon_s/charicon_s.gfx",
}
V14_TABLES = {
    "data/rpg/param/costumeParam.bin.xfbin",
    "data/spc/appearanceAnm.xfbin",
    "data/spc/characode.bin.xfbin",
    "data/spc/costumeBreakParam.xfbin",
    "data/spc/duelPlayerParam.xfbin",
    "data/spc/playerSettingParam.bin.xfbin",
    "data/spc/player_icon.xfbin",
    "data/spc/skillCustomizeParam.xfbin",
    "data/spc/skillIndexSettingParam.xfbin",
    "data/spc/spSkillCustomizeParam.xfbin",
    "data/spc/spTypeSupportParam.xfbin",
    "data/spc/supportActionParam.xfbin",
    "data/ui/max/select/characterSelectParam.xfbin",
}

def classify_path(path: str) -> str:
    if path in UNVERIFIED_GLOBALS:
        return "unverified_global"
    if path in V14_TABLES:
        return "v14_parameter_table"
    if path.lower().endswith(".xfbin"):
        return "other_xfbin"
    return "other"

def parse_listing(text: str, archive_bytes: int) -> dict[str, dict]:
    header = HEAD.search(text)
    if not header:
        raise ValueError("FastCPK --list header missing/unsupported")
    expected = int(header[1])
    if expected < 1 or expected > 1000000:
        raise ValueError("unreasonable CPK Files count")
    records = {}
    used_ids = set()
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        ident, hex_offset, packed, extracted, path = match.groups()
        ident = int(ident)
        offset, size = int(hex_offset,16), int(packed)
        path = path.strip().replace("\\", "/")
        if (not path or path.startswith("/") or ".." in Path(path).parts
                or path in records or ident in used_ids):
            raise ValueError("invalid/duplicate CPK path or ID: " + path)
        if offset < 0 or size < 0 or offset + size > archive_bytes:
            raise ValueError("CPK entry out of file range: " + path)
        records[path] = {
            "id":ident, "offset":offset, "packed_size":size,
            "extracted_size":int(extracted)
        }
        used_ids.add(ident)
    if len(records) != expected:
        raise ValueError(f"FastCPK file count mismatch: expected={expected} actual={len(records)}")
    return records

def list_archive(archive: Path, fastcpk: Path) -> dict[str, dict]:
    if not archive.is_file():
        raise FileNotFoundError(archive)
    if not fastcpk.is_file() or not os.access(fastcpk, os.X_OK):
        raise FileNotFoundError("FastCPK executable unavailable: " + str(fastcpk))
    cmd = [str(fastcpk), "--list", str(archive)]
    cp = subprocess.run(cmd, capture_output=True, text=True,
                        timeout=180, check=True)
    return parse_listing(cp.stdout, archive.stat().st_size)

def sha_entry(archive: Path, item: dict) -> str:
    h = hashlib.sha256()
    left = item["packed_size"]
    with archive.open("rb") as f:
        f.seek(item["offset"])
        while left:
            chunk = f.read(min(left, 1024 * 1024))
            if not chunk:
                raise ValueError("truncated packed entry in " + str(archive))
            h.update(chunk)
            left -= len(chunk)
    return h.hexdigest()

def read_inventory(manifest_path: Path | None):
    if manifest_path is None:
        return set(), "not_provided"
    src = json.loads(manifest_path.read_text("utf-8"))
    full = src.get("all_72_resources")
    if isinstance(full, list) and all(isinstance(x,dict) and "path" in x for x in full):
        paths = {x["path"] for x in full}
        if len(paths) != len(full) or (
            src.get("resource_count") is not None
            and len(full) != src["resource_count"]
        ):
            raise ValueError("explicit inventory has duplicates or inconsistent count")
        return paths, "complete_resource_list"
    # V4_RESOURCE_ROUTING.json contains resource_count=72, but not a
    # full all_72_resources array. It lists only collision and UI rows.
    partial = (src.get("resource_collisions_across_all_cpks") or [])
    partial += (src.get("ui_assets") or [])
    paths = {x["path"] for x in partial if isinstance(x, dict) and "path" in x}
    return paths, "partial_v4_inventory"

def compare(carrier_path: Path, carrier: dict,
            stock_archives: list[tuple[Path, dict]],
            inventory_paths: set[str] | None = None,
            coverage: str = "not_provided") -> dict:
    indexed = defaultdict(list)
    folded = defaultdict(set)
    for archive, listing in stock_archives:
        for name, row in listing.items():
            indexed[name].append((archive, row))
            folded[name.casefold()].add(name)
    collisions, new_paths, casing = [], [], []
    for name, row in sorted(carrier.items()):
        if name not in indexed:
            new_paths.append(name)
            other = sorted(x for x in folded.get(name.casefold(), ()) if x != name)
            if other:
                casing.append({"carrier_path":name,"stock_case_variants":other})
            continue
        carrier_hash = sha_entry(carrier_path, row)
        sources = []
        for stock_path, stock_row in indexed[name]:
            stock_hash = sha_entry(stock_path, stock_row)
            sources.append({
                "archive":str(stock_path),
                "id":stock_row["id"],
                "packed_size":stock_row["packed_size"],
                "sha256_stored":stock_hash,
                "different_packed_bytes":stock_hash != carrier_hash,
            })
        collisions.append({
            "path":name, "category":classify_path(name),
            "carrier_id":row["id"], "carrier_size":row["packed_size"],
            "carrier_sha256_stored":carrier_hash,
            "stock_sources":sources
        })
    missing = (sorted(inventory_paths - carrier.keys())
               if inventory_paths is not None else None)
    return {
        "carrier_entry_count":len(carrier),
        "stock_cpk_count":len(stock_archives),
        "stock_path_collisions":collisions,
        "different_packed_payloads": [
            entry for entry in collisions
            if any(x["different_packed_bytes"] for x in entry["stock_sources"])
        ],
        "carrier_paths_not_found_in_stock":new_paths,
        "case_variant_paths":casing,
        "resource_inventory_coverage":coverage,
        "missing_checked_inventory_paths":missing,
        "mtobskl3_present_in_carrier": any("mtobskl3" in name.casefold() for name in carrier),
        "warnings":[
            "Compares STORED/PACKED bytes, not decoded/decrypted XFBIN structures.",
            "Same bytes do not establish same CPK mount priority or runtime routing.",
            "Cross-archive path collisions are not necessarily harmful.",
            "No path in carrier does not prove that a runtime request exists.",
            "Runtime status=2 or chunk pointer does not prove battle actor/render readiness.",
            "CPK bind in prior P34 used subsdk9; ROMFS-only mounting is unproven."
        ],
    }

def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--stock",type=Path,help="one stock common.cpk (partial check)")
    group.add_argument("--stock-romfs",type=Path,help="scan all stock CPKs, including data/sim/data2.cpk")
    p.add_argument("--carrier",type=Path,required=True)
    p.add_argument("--fastcpk",type=Path,default=FASTCPK)
    p.add_argument("--resource-inventory",type=Path,help="V4 routing JSON (partial inventory)")
    p.add_argument("--output",type=Path,help="JSON; refuses overwrite")
    args=p.parse_args()
    if args.stock:
        cpks = [args.stock]
    else:
        root = args.stock_romfs.resolve()
        if not root.is_dir():
            p.error("Stock RomFS directory unavailable")
        # Restrict to known retail CPK namespaces from the V4 inventory.
        # Exclude moddingapi/custom carriers even if placed under this RomFS.
        allowed = {"disc", "launch", "patch", "sim"}
        cpks = sorted(
            candidate for candidate in root.rglob("*.cpk")
            if candidate.is_file()
            and not candidate.is_symlink()
            and (relative := candidate.relative_to(root)).parts[:1] == ("data",)
            and len(relative.parts) >= 3
            and relative.parts[1] in allowed
        )
    if any(path.resolve() == args.carrier.resolve() for path in cpks):
        p.error("The carrier cannot also be a stock CPK")
    if not cpks:
        p.error("No stock CPK files found")
    # Fail closed: if ANY stock CPK cannot list, no incomplete result is reported.
    stock=[(path, list_archive(path,args.fastcpk)) for path in cpks]
    carrier=list_archive(args.carrier,args.fastcpk)
    known, coverage=read_inventory(args.resource_inventory)
    report=compare(args.carrier,carrier,stock,
                   known if args.resource_inventory else None,coverage)
    report["stock_archives"]=[str(path) for path in cpks]
    if args.stock_romfs and len(cpks) != 28:
        report["warnings"].append(
            f"Expected 28 original CPKs from V4; found {len(cpks)}. Verify stock completeness/provenance."
        )
    blob=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if args.output:
        with args.output.open("x",encoding="utf-8") as out:
            out.write(blob)
        print("Report: "+str(args.output))
    else:
        print(blob)

if __name__=="__main__":
    main()
