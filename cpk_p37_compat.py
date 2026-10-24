#!/usr/bin/env python3
"""P37 helpers: preserve original CPK stored entries and original Sorted flag.

The input carrier is always READ-ONLY. Header adjustments are applied only
to the newly generated temporary candidate after FastCPK template packing.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

TYPE_LENGTH = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4,
               6: 8, 7: 8, 8: 4, 9: 8, 10: 4, 11: 8}


def read_stored_entry(archive: Path, entry: dict) -> bytes:
    offset = entry["offset"]
    length = entry["packed_size"]
    if offset < 0 or length < 0 or offset + length > archive.stat().st_size:
        raise ValueError("Invalid stored entry range")
    with archive.open("rb") as reader:
        reader.seek(offset)
        payload = reader.read(length)
    if len(payload) != length:
        raise ValueError("Short read while preserving original stored payload")
    return payload


def staged_raw_storage(archive: Path, indexes: dict,
                       stage_root: Path, modified_names: set[str]) -> None:
    """Use precisely original stored bytes for every unchanged CPK entry.

    Current input carrier has 0 CRILAYLA files; prohibit payloads where stored
    length differs from the decoded length (which would need TOC size handling).
    """
    for name, entry in indexes.items():
        if entry["packed_size"] != entry["extracted_size"]:
            raise ValueError("Original carrier contains compressed entry; P37 refuses: " + name)
        if name in modified_names:
            continue
        target = stage_root.joinpath(*name.split("/"))
        if not target.is_file() or target.is_symlink():
            raise ValueError("Missing/unsafe staged file: " + name)
        target.write_bytes(read_stored_entry(archive, entry))


def assert_original_stored_unchanged(original: Path, original_index: dict,
                                     candidate: Path, candidate_index: dict,
                                     changed_names: set[str]) -> int:
    checked = 0
    for name, entry in original_index.items():
        if name in changed_names:
            continue
        candidate_entry = candidate_index.get(name)
        if candidate_entry is None:
            raise ValueError("Missing candidate stored path: " + name)
        original_blob = read_stored_entry(original, entry)
        candidate_blob = read_stored_entry(candidate, candidate_entry)
        if hashlib.sha256(original_blob).digest() != hashlib.sha256(candidate_blob).digest():
            raise ValueError("Original stored payload changed: " + name)
        checked += 1
    return checked


def _transform_utf(table: bytearray) -> None:
    key = 0x5f
    for i in range(len(table)):
        table[i] ^= key
        key = (key * 0x15) & 0xff


def _u16(buf: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(buf):
        raise ValueError("Truncated CPK UTF u16")
    return int.from_bytes(buf[offset:offset+2], "big")


def _u32(buf: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(buf):
        raise ValueError("Truncated CPK UTF u32")
    return int.from_bytes(buf[offset:offset+4], "big")


def locate_sorted(table: bytearray) -> tuple[int, int]:
    """Return offset and value of Sorted from decoded CRI @UTF CPK header."""
    if table[:4] != b"@UTF":
        raise ValueError("Unsupported CPK @UTF header magic")
    if _u32(table, 4) + 8 > len(table):
        raise ValueError("Truncated @UTF packet length")
    row_start = _u32(table, 8) + 8
    string_start = _u32(table, 12) + 8
    count = _u16(table, 24)
    row_width = _u16(table, 26)
    row_count = _u32(table, 28)
    if row_count != 1 or count < 1 or count > 128:
        raise ValueError("Unsupported CPK @UTF header dimensions")
    if row_start + row_width > len(table) or string_start >= len(table):
        raise ValueError("CPK @UTF header points outside data")
    descriptor = 32
    row_cursor = row_start
    found = []
    for _ in range(count):
        if descriptor + 5 > len(table):
            raise ValueError("Truncated CPK @UTF column")
        flag = table[descriptor]
        descriptor += 1
        name_offset = _u32(table, descriptor)
        descriptor += 4
        name_start = string_start + name_offset
        if name_start >= len(table):
            raise ValueError("Invalid CPK @UTF column string")
        end = table.find(b"\x00", name_start)
        if end < 0:
            raise ValueError("Unterminated CPK @UTF column string")
        name = bytes(table[name_start:end]).decode("ascii", errors="strict")
        size = TYPE_LENGTH.get(flag & 0x0f)
        if size is None:
            raise ValueError("Unsupported CPK @UTF column type")
        storage = flag & 0xf0
        if storage == 0x10:
            continue
        if storage == 0x30:
            current = descriptor
            descriptor += size
        elif storage == 0x50:
            current = row_cursor
            row_cursor += size
        else:
            raise ValueError("Unsupported CPK @UTF column storage")
        if current + size > len(table):
            raise ValueError("CPK @UTF value out of range")
        if name == "Sorted":
            if size != 2 or (flag & 0x0f) != 2:
                raise ValueError("Sorted is not a U16")
            found.append((current, _u16(table, current)))
    if row_cursor > row_start + row_width:
        raise ValueError("CPK UTF row exceeds allocated length")
    if len(found) != 1:
        raise ValueError("Sorted must occur exactly once in CPK header")
    offset, value = found[0]
    if value not in (0, 1):
        raise ValueError("CPK Sorted must be boolean")
    return offset, value


def get_cpk_sorted(archive: Path) -> int:
    _, _, value = _read_header_utf(archive)
    return value


def _read_header_utf(archive: Path) -> tuple[bytearray, bool, int]:
    with archive.open("rb") as src:
        header = src.read(16)
        if len(header) != 16 or header[:4] != b"CPK ":
            raise ValueError("Not a CPK header")
        packet_length = int.from_bytes(header[8:16], "little")
        if packet_length < 32 or packet_length > 1024 * 1024:
            raise ValueError("Unreasonable CPK header @UTF packet")
        data = bytearray(src.read(packet_length))
        if len(data) != packet_length:
            raise ValueError("Truncated CPK header @UTF packet")
    obfuscated = data[:4] != b"@UTF"
    if obfuscated:
        _transform_utf(data)
    _, value = locate_sorted(data)
    return data, obfuscated, value


def set_cpk_sorted(archive: Path, target: int) -> tuple[int, int]:
    """Safely change only Sorted in a disposable rebuilt CPK header."""
    if target not in (0, 1):
        raise ValueError("Sorted must be 0 or 1")
    decoded, obfuscated, old = _read_header_utf(archive)
    offset, _ = locate_sorted(decoded)
    decoded[offset:offset+2] = target.to_bytes(2, "big")
    if obfuscated:
        _transform_utf(decoded)
    with archive.open("r+b") as dst:
        dst.seek(16)
        dst.write(decoded)
        dst.flush()
    actual = get_cpk_sorted(archive)
    if actual != target:
        raise ValueError("Failed to preserve CPK Sorted template metadata")
    return old, actual
