"""Fail-closed same-size CRILAYLA replacement; no relocation or runtime hook."""
import hashlib
from .cpk_events import entries, canonical
from .compressed_prm_events import extract_candidate, SHA
from .crilayla import decompress


def replace_same_size(source, expected_sha256, path, packed, *, limit=256 * 1024 * 1024):
    if not isinstance(source, bytes) or not isinstance(packed, bytes):
        raise ValueError("Immutable archive and packed bytes required")
    if not isinstance(expected_sha256, str) or not SHA.fullmatch(expected_sha256):
        raise ValueError("Exact source SHA256 required")
    if hashlib.sha256(source).hexdigest() != expected_sha256:
        raise ValueError("Source archive SHA256 mismatch")
    index = entries(source)
    path = canonical(path)
    if path not in index:
        raise ValueError("Unknown CPK member")
    entry = index[path]
    start, size = entry["offset"], entry["stored_size"]
    original = source[start:start + size]
    if not original.startswith(b"CRILAYLA") or not packed.startswith(b"CRILAYLA"):
        raise ValueError("Both streams must be CRILAYLA")
    if len(packed) != size:
        raise ValueError("Stored-size mismatch: relocation forbidden")
    expected, proof = extract_candidate(source, path, expected_sha256, decoded_limit=limit)
    if decompress(packed, limit=limit) != expected:
        raise ValueError("Candidate does not match source-authenticated Event236 conversion")
    result = source[:start] + packed + source[start + size:]
    if len(result) != len(source) or entries(result) != index:
        raise ValueError("Archive metadata changed")
    if result[:start] != source[:start] or result[start + size:] != source[start + size:]:
        raise ValueError("Nonselected bytes changed")
    return result, {
        "source_sha256": expected_sha256,
        "output_sha256": hashlib.sha256(result).hexdigest(),
        "path": path, "stored_bytes": size,
        "candidate_decoded_sha256": proof["candidate_decoded_sha256"],
        "metadata_and_other_payloads_unchanged": True,
        "runtime_verified": False, "ready_for_gameplay_test": False,
    }
