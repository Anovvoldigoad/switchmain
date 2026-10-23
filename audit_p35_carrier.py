#!/usr/bin/env python3
"""P35 read-only audit of an already-mounted Tobi carrier CPK vs stock common.cpk.

Does not build, patch, mount or change any game files.
CPK TOC parsing uses the same CRI @UTF layout as the V14 offline builder.
Stored-byte comparison is evidence of an override, NOT proof of XFBIN validity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SIZES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 8, 7: 8, 8: 4, 9: 8, 10: 4, 11: 8}
EXTRA_GLOBALS = {
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


def be32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def parse_utf(data: bytes) -> list[dict]:
    if data[:4] != b"@UTF":
        raise ValueError("not a CRI @UTF table")
    size = be32(data, 4) + 8
    if size > len(data) or size < 32:
        raise ValueError("truncated @UTF")
    row_off, str_off, data_off = (be32(data, n) + 8 for n in (8, 12, 16))
    cols = int.from_bytes(data[24:26], "big")
    stride = int.from_bytes(data[26:28], "big")
    count = be32(data, 28)
    if not 0 < cols < 100 or count > 100000 or row_off + stride * count > str_off or str_off > data_off or data_off > size:
        raise ValueError("unexpected @UTF dimensions")

    def string(offset: int) -> str:
        start = str_off + offset
        end = data.find(b"\x00", start, data_off)
        if start < str_off or start >= data_off or end < 0:
            raise ValueError("invalid @UTF string offset")
        return data[start:end].decode("utf-8")

    fields = []
    pos = 32
    for _ in range(cols):
        storage, kind = data[pos] & 0xF0, data[pos] & 0x0F
        if storage not in (0x10, 0x30, 0x50) or kind not in SIZES:
            raise ValueError("unsupported @UTF column")
        key = string(be32(data, pos + 1))
        pos += 5
        const = None
        if storage == 0x30:
            const = int.from_bytes(data[pos:pos + SIZES[kind]], "big")
            pos += SIZES[kind]
        fields.append((key, storage, kind, const))
    if pos != row_off:
        raise ValueError("unexpected @UTF column layout")
    rows = []
    for n in range(count):
        pos = row_off + n * stride
        row = {}
        for key, storage, kind, const in fields:
            val = const
            if storage == 0x50:
                val = int.from_bytes(data[pos:pos + SIZES[kind]], "big")
                pos += SIZES[kind]
            row[key] = string(val) if kind == 10 and val is not None else val
        if pos != row_off + (n + 1) * stride:
            raise ValueError("unexpected @UTF row stride")
        rows.append(row)
    return rows


def read_cpk(path: Path) -> tuple[dict, dict[str, dict]]:
    with path.open("rb") as f:
        f.seek(0, 2)
        archive_size = f.tell()
        f.seek(0)
        header = f.read(2048)
        if header[:4] != b"CPK ":
            raise ValueError(f"not a CPK: {path}")
        hsize = int.from_bytes(header[8:16], "little")
        if hsize > len(header) - 16:
            raise ValueError("unsupported large CPK header")
        meta = parse_utf(header[16:16 + hsize])[0]
        f.seek(meta["TocOffset"])
        tag = f.read(16)
        if tag[:4] != b"TOC ":
            raise ValueError("CPK has no normal TOC")
        tsize = int.from_bytes(tag[8:16], "little")
        if tsize > 16 * 1024 * 1024:
            raise ValueError("TOC too large")
        rows = parse_utf(f.read(tsize))
    if meta["Files"] != len(rows):
        raise ValueError("CPK entry count mismatch")
    result = {}
    for row in rows:
        name = (row["DirName"] + "/" if row["DirName"] else "") + row["FileName"]
        start = meta["TocOffset"] + row["FileOffset"]
        size = row["FileSize"]
        if name in result or start < 0 or size < 0 or start + size > archive_size:
            raise ValueError("duplicate or invalid CPK entry: " + name)
        result[name] = {"offset": start, "size": size, "extract_size": row["ExtractSize"], "id": row["ID"]}
    return meta, result


def sha_entry(path: Path, row: dict) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        stream.seek(row["offset"])
        left = row["size"]
        while left:
            chunk = stream.read(min(left, 1024 * 1024))
            if not chunk:
                raise ValueError("truncated entry")
            result.update(chunk)
            left -= len(chunk)
    return result.hexdigest()


def compare(stock_path: Path, carrier_path: Path, stock: dict, carrier: dict,
            known_resources: set[str] | None = None) -> dict:
    common = []
    for name in sorted(set(stock) & set(carrier)):
        left, right = stock[name], carrier[name]
        left_hash = sha_entry(stock_path, left)
        right_hash = sha_entry(carrier_path, right)
        common.append({
            "path": name,
            "kind": ("unverified_global" if name in EXTRA_GLOBALS else
                     "v14_table" if name in V14_TABLES else "other_stock_collision"),
            "different_packed_bytes": left_hash != right_hash,
            "stock_sha256": left_hash,
            "carrier_sha256": right_hash,
            "stock_size": left["size"],
            "carrier_size": right["size"],
        })
    new_paths = sorted(set(carrier) - set(stock))
    missing_known = sorted(known_resources - set(carrier)) if known_resources is not None else None
    return {
        "stock_entries": len(stock),
        "carrier_entries": len(carrier),
        "overrides_relative_to_this_stock_cpk": common,
        "changed_overrides": [x for x in common if x["different_packed_bytes"]],
        "new_relative_to_this_stock_cpk": new_paths,
        "missing_known_resource_paths": missing_known,
        "mtobskl3_present_in_carrier": any("mtobskl3" in s.lower() for s in carrier),
        "warnings": [
            "An identical packed payload does not prove identical runtime resolution priority.",
            "Other stock CPKs may also contain paths not present in common.cpk.",
            "No asset compatibility, actor rendering or gameplay success is claimed.",
            "The separate CPK in romfs is mounted by the P32/P34 subsdk9 hook in the supplied log; ROMFS-only autonomous loading is unproven.",
        ],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stock", type=Path, required=True, help="original patch/170/common.cpk")
    p.add_argument("--carrier", type=Path, required=True, help="romfs/data/moddingapi/Tobi_Switch.cpk")
    p.add_argument("--resource-inventory", type=Path, help="optional V4_RESOURCE_ROUTING.json")
    p.add_argument("--output", type=Path, help="optional JSON report; never replaces existing file")
    args = p.parse_args()
    stock_meta, stock = read_cpk(args.stock)
    carrier_meta, carrier = read_cpk(args.carrier)
    known = None
    if args.resource_inventory:
        manifest = json.loads(args.resource_inventory.read_text("utf-8"))
        known = {r["path"] for r in manifest["all_72_resources"]}
    report = compare(args.stock, args.carrier, stock, carrier, known)
    report["stock_header"] = {k: stock_meta[k] for k in ("Files", "Sorted", "Align")}
    report["carrier_header"] = {k: carrier_meta[k] for k in ("Files", "Sorted", "Align")}
    data = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as f:
            f.write(data)
        print(f"Report: {args.output}")
    else:
        print(data)


if __name__ == "__main__":
    main()
