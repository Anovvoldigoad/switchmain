#!/usr/bin/env python3
"""Source-SHA-pinned CPK payload evidence extraction; read-only game input.

This deliberately does not repack CPKs, bind native consumers, or declare
compatibility with Uzuy. All selected payloads must validate before output.
"""
import argparse
import hashlib
import json
import mmap
import re
import shutil
from contextlib import contextmanager
from pathlib import Path

from portlib.cpk_events import canonical, entries, read_payload

MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 16


@contextmanager
def _verified_archive(source, expected_sha256):
    """Hash source by streaming, then map it read-only instead of copying the CPK."""
    with source.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != expected_sha256.lower():
            raise ValueError("CPK source SHA256 mismatch")
        if handle.seek(0, 2) == 0:
            raise ValueError("Empty CPK source")
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as archive:
            yield archive, digest


def inventory(cpk_path, expected_sha256, *, suffix=None):
    """Enumerate exact TOC paths before selecting payloads; never writes game data."""
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("Expected a full CPK SHA256 pin")
    if suffix is not None and (not isinstance(suffix, str) or not suffix or "/" in suffix or "\\" in suffix):
        raise ValueError("Invalid inventory suffix")
    source = Path(cpk_path)
    with _verified_archive(source, expected_sha256) as (archive, digest):
        index = entries(archive)
        rows = []
        for name, item in sorted(index.items()):
            if suffix is not None and not name.casefold().endswith(suffix.casefold()):
                continue
            start = item["offset"]
            stored_bytes = item["stored_size"]
            rows.append({
                "entry": name, "id": item["id"], "offset": start,
                "stored_bytes": stored_bytes, "extract_bytes": item["size"],
                "stored_sha256": hashlib.sha256(memoryview(archive)[start:start + stored_bytes]).hexdigest(),
                "encoding": "CRILAYLA" if archive[start:start + 8] == b"CRILAYLA" else
                            ("identity" if stored_bytes == item["size"] else "unknown")
            })
    return {
        "status": "CPK_READ_ONLY_INVENTORY_NO_CONSUMER_ABI",
        "cpk_filename": source.name, "cpk_sha256": digest,
        "cpk_bytes": len(archive), "indexed_entries": len(index),
        "selected_entries": len(rows), "entries": rows,
        "native_engine_abi_verified": False, "uzuy_tested": False
    }


def capture(cpk_path, expected_sha256, selected, out_dir, *, max_total_bytes=MAX_TOTAL_BYTES):
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("Expected a full CPK SHA256 pin")
    if type(max_total_bytes) is not int or not 0 < max_total_bytes <= 512 * 1024 * 1024:
        raise ValueError("Invalid aggregate decoded-byte limit")
    if not 1 <= len(selected) <= MAX_ENTRIES:
        raise ValueError("Select one to sixteen CPK entries")
    paths = [canonical(path) for path in selected]
    if len({path.casefold() for path in paths}) != len(paths):
        raise ValueError("Duplicate case-insensitive CPK selection")

    source = Path(cpk_path)
    destination = Path(out_dir)
    with _verified_archive(source, expected_sha256) as (archive, actual_sha256):
        index = entries(archive)
        outputs = []
        metadata = []
        total = 0
        for number, name in enumerate(paths):
            info = index.get(name)
            if info is None:
                raise ValueError("CPK entry absent: " + name)
            remaining = max_total_bytes - total
            if info["size"] > remaining:
                raise ValueError("Selected CPK decoded payloads exceed aggregate limit")
            payload = read_payload(archive, name, limit=remaining)
            if len(payload) != info["size"]:
                raise ValueError("CPK output size mismatch")
            start = info["offset"]
            compressed = archive[start:start + 8] == b"CRILAYLA"
            filename = f"{number:04d}.bin"
            outputs.append((filename, payload))
            metadata.append({
                "entry": name, "id": info["id"], "offset": start,
                "stored_bytes": info["stored_size"], "decoded_bytes": len(payload),
                "encoding": "CRILAYLA" if compressed else "identity",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "output": filename
            })
            total += len(payload)

    manifest = {
        "status": "SOURCE_PINNED_CPK_PAYLOAD_EVIDENCE_READ_ONLY_NOT_GAMEPLAY",
        "cpk_filename": source.name, "cpk_sha256": actual_sha256,
        "cpk_bytes": len(archive), "total_decoded_bytes": total,
        "entries": metadata, "native_engine_abi_verified": False,
        "archive_precedence_verified": False, "uzuy_tested": False
    }
    # No directory or payload is created until the full source and every
    # selected compressed/uncompressed entry have passed validation.
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for filename, payload in outputs:
            with (destination / filename).open("xb") as handle:
                handle.write(payload)
        with (destination / "manifest.json").open("x", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")
    except Exception:
        shutil.rmtree(destination)
        raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpk", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--entry", action="append", help="Exact CPK TOC path; repeat as needed")
    parser.add_argument("--inventory", action="store_true", help="Print source-pinned TOC inventory as JSON; no output files")
    parser.add_argument("--suffix", help="Optional case-insensitive filename suffix for inventory only")
    parser.add_argument("--out-dir", type=Path, help="New output directory, never overwrites existing files")
    parser.add_argument("--max-total-bytes", type=int, default=MAX_TOTAL_BYTES)
    args = parser.parse_args()
    if args.inventory:
        if args.entry or args.out_dir or args.suffix is not None and not args.suffix:
            parser.error("--inventory accepts --suffix but not --entry or --out-dir")
        try:
            result = inventory(args.cpk, args.expected_sha256, suffix=args.suffix)
        except (ValueError, OSError, UnicodeError) as error:
            parser.error(str(error))
        print(json.dumps(result, indent=2))
        return
    if not args.entry or args.suffix is not None or not args.out_dir:
        parser.error("Payload extraction requires --entry and --out-dir; --suffix is inventory-only")
    try:
        result = capture(args.cpk, args.expected_sha256, args.entry, args.out_dir,
                         max_total_bytes=args.max_total_bytes)
    except (ValueError, OSError, UnicodeError) as error:
        parser.error(str(error))
    print("CPK_READ_ONLY_EVIDENCE", result["cpk_sha256"], len(result["entries"]),
          "entries; no engine ABI or Uzuy proof")


if __name__ == "__main__":
    main()
