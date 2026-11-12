"""Read-only decoded event-marker feasibility for a CRILAYLA CPK PRM.

Decoded byte offsets are NOT compressed-stream offsets. Never writes an archive.
"""
import hashlib
import mmap
import re
import struct
from .cpk_events import entries, read_payload, canonical
from .prm_events import mark, records, MARKER

SHA = re.compile(r"[0-9a-f]{64}\Z")


def _inspect_with_candidate(data, path, expected_sha256, *, decoded_limit=256 * 1024 * 1024):
    if not isinstance(data, (bytes, mmap.mmap)) or not isinstance(expected_sha256, str) or not SHA.fullmatch(expected_sha256):
        raise ValueError("Exact CPK source SHA256 required")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("CPK source SHA256 mismatch")
    index = entries(data)
    path = canonical(path)
    if path not in index:
        raise ValueError("CPK entry not found")
    entry = index[path]
    stored = data[entry["offset"]:entry["offset"] + entry["stored_size"]]
    if not stored.startswith(b"CRILAYLA"):
        raise ValueError("Selected entry is not CRILAYLA")
    decoded = read_payload(data, path, limit=decoded_limit, index=index)
    candidate, report = mark(decoded)
    changed = [i for i, (a, b) in enumerate(zip(decoded, candidate)) if a != b]
    expected = sorted(i for row in report["changes"] for i in (row["offset"] + 42, row["offset"] + 43))
    if len(candidate) != len(decoded) or changed != expected:
        raise ValueError("Unexpected decoded PRM mutation")
    # Exact decoded record provenance: never interpret these as compressed offsets.
    provenance = []
    for row in records(decoded):
        if row["event"] != 236:
            continue
        offset = row["offset"]
        opcode = struct.unpack_from("<h", decoded, offset + 36)[0]
        before = struct.unpack_from("<H", decoded, offset + 42)[0]
        after = struct.unpack_from("<H", candidate, offset + 42)[0]
        kind = ("native_preserved" if not 1 <= opcode <= 29 else
                "already_marked" if before == MARKER else "newly_marked")
        provenance.append({
            "chunk": row["chunk"], "animation": row["animation"],
            "function": row["function"], "decoded_offset": offset,
            "opcode": opcode, "marker_before": before,
            "marker_after": after, "classification": kind,
        })
    if (sum(r["classification"] == "newly_marked" for r in provenance) != report["marked_records"]
            or sum(r["classification"] == "already_marked" for r in provenance) != report["already_marked"]
            or sum(r["classification"] == "native_preserved" for r in provenance) != report["native_event236_preserved"]):
        raise ValueError("Event236 provenance mismatch")
    report = {
        "status": "COMPRESSED_PRM_DECODED_MARKER_FEASIBILITY_ONLY",
        "archive_sha256": expected_sha256,
        "path": path,
        "stored_sha256": hashlib.sha256(stored).hexdigest(),
        "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        "candidate_decoded_sha256": hashlib.sha256(candidate).hexdigest(),
        "stored_bytes": len(stored),
        "decoded_bytes": len(decoded),
        "changed_decoded_offsets": changed,
        "event236_provenance": provenance,
        "marked_records": report["marked_records"],
        "already_marked": report["already_marked"],
        "native_event236_preserved": report["native_event236_preserved"],
        "compressed_archive_repacked": False,
        "compressed_offset_mapping_verified": False,
        "original_archive_unchanged": True,
        "gameplay_verified": False,
        "full_moddingapi": False,
    }
    return candidate, report


def inspect(data, path, expected_sha256, *, decoded_limit=256 * 1024 * 1024):
    return _inspect_with_candidate(data, path, expected_sha256, decoded_limit=decoded_limit)[1]


def extract_candidate(data, path, expected_sha256, *, decoded_limit=256 * 1024 * 1024):
    """Return a validated decoded PRM candidate, never a CPK or installable asset.

    The candidate is produced only after the same source-integrity and mutation
    checks as inspect(). The source archive remains caller-owned and unchanged.
    """
    candidate, report = _inspect_with_candidate(data, path, expected_sha256, decoded_limit=decoded_limit)
    if hashlib.sha256(candidate).hexdigest() != report["candidate_decoded_sha256"]:
        raise ValueError("Decoded candidate integrity mismatch")
    return candidate, report
