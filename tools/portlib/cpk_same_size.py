"""Fail-closed same-size CRILAYLA replacement; no relocation or runtime hook."""
import hashlib
import mmap
from .cpk_events import entries, canonical
from .compressed_prm_events import extract_candidate, _extract_validated_candidate, SHA
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


def validate_many_same_size(source, expected_sha256, replacements, *, limit=256 * 1024 * 1024):
    """Validate every source-bound edit before publishing a single new archive."""
    if not isinstance(replacements, dict) or not replacements:
        raise ValueError("Nonempty path-to-packed mapping required")
    if not isinstance(source, (bytes, mmap.mmap)) or not isinstance(expected_sha256, str) or not SHA.fullmatch(expected_sha256):
        raise ValueError("Immutable source and exact SHA256 required")
    if hashlib.sha256(source).hexdigest() != expected_sha256:
        raise ValueError("Source archive SHA256 mismatch")
    index = entries(source)
    canonical_paths = [canonical(path) for path in replacements]
    if len({path.casefold() for path in canonical_paths}) != len(canonical_paths):
        raise ValueError("Duplicate CPK path")
    # Reject overlapping TOC storage ranges before any candidate is accepted.
    spans = sorted((row["offset"], row["offset"] + row["stored_size"], name)
                   for name, row in index.items())
    if any(start < previous_end for (_, previous_end, _), (start, _, _) in zip(spans, spans[1:])):
        raise ValueError("Overlapping CPK member storage ranges")
    changes = _validated_changes(source, expected_sha256, replacements, index, canonical_paths, limit)
    return changes, index, canonical_paths


def _validated_changes(source, expected_sha256, replacements, index, canonical_paths, limit):
    changes = []
    for path, packed in replacements.items():
        if not isinstance(packed, (bytes, mmap.mmap)) or path not in index:
            raise ValueError("Unknown member or non-bytes payload")
        entry = index[path]
        start, size = entry["offset"], entry["stored_size"]
        if not source[start:start + size].startswith(b"CRILAYLA") or packed[:8] != b"CRILAYLA":
            raise ValueError("Both streams must be CRILAYLA")
        if len(packed) != size:
            raise ValueError("Stored-size mismatch: relocation forbidden")
        expected, _ = _extract_validated_candidate(source, path, expected_sha256, index, decoded_limit=limit)
        if decompress(packed, limit=limit) != expected:
            raise ValueError("Candidate does not match source-authenticated Event236 conversion")
        changes.append((start, start + size, packed))
    return changes


def replace_many_same_size(source, expected_sha256, replacements, *, limit=256 * 1024 * 1024):
    changes, index, canonical_paths = validate_many_same_size(source, expected_sha256, replacements, limit=limit)
    result = bytearray(source)
    for start, end, packed in changes:
        result[start:end] = packed
    result = bytes(result)
    if entries(result) != index:
        raise ValueError("Archive metadata changed")
    cursor = 0
    for start, end, _ in sorted(changes):
        if result[cursor:start] != source[cursor:start]:
            raise ValueError("Nonselected bytes changed")
        cursor = end
    if result[cursor:] != source[cursor:]:
        raise ValueError("Nonselected bytes changed")
    return result, {
        "source_sha256": expected_sha256,
        "output_sha256": hashlib.sha256(result).hexdigest(),
        "selected_paths": sorted(canonical_paths),
        "metadata_and_other_payloads_unchanged": True,
        "runtime_verified": False,
        "ready_for_gameplay_test": False,
    }
