"""Read-only independent verifier for an offline same-size CPK publication.

Never writes game files and does not establish runtime compatibility.
"""
import hashlib
import mmap

from .cpk_events import canonical, entries
from .compressed_prm_events import SHA, _extract_validated_candidate
from .crilayla import decompress
from .prm_events import mark


def verify_same_size_output(source, output, source_sha256, output_sha256, selected, *, limit=256 * 1024 * 1024):
    if not isinstance(source, (bytes, mmap.mmap)) or not isinstance(output, (bytes, mmap.mmap)):
        raise ValueError("Immutable source/output bytes required")
    if not all(isinstance(x, str) and SHA.fullmatch(x) for x in (source_sha256, output_sha256)):
        raise ValueError("Exact SHA256 pins required")
    if hashlib.sha256(source).hexdigest() != source_sha256:
        raise ValueError("Source SHA256 mismatch")
    if hashlib.sha256(output).hexdigest() != output_sha256:
        raise ValueError("Output SHA256 mismatch")
    if len(source) != len(output):
        raise ValueError("Archive length changed")
    if not isinstance(selected, (list, tuple)) or not selected:
        raise ValueError("Nonempty selected path list required")
    paths = [canonical(p) for p in selected]
    if len({path.casefold() for path in paths}) != len(paths):
        raise ValueError("Duplicate selected path")
    original_index = entries(source)
    if entries(output) != original_index:
        raise ValueError("CPK TOC changed")
    if any(path not in original_index for path in paths):
        raise ValueError("Unknown selected member")
    spans = sorted((row["offset"], row["offset"] + row["stored_size"], name)
                   for name, row in original_index.items())
    if any(start < prior_end for (_, prior_end, _), (start, _, _) in zip(spans, spans[1:])):
        raise ValueError("Overlapping CPK member storage ranges")
    cursor = 0
    selected_set = set(paths)
    for start, end, name in spans:
        if source[cursor:start] != output[cursor:start]:
            raise ValueError("Metadata or padding changed")
        if name not in selected_set:
            if source[start:end] != output[start:end]:
                raise ValueError("Unselected member changed")
        else:
            original = source[start:end]
            packed = output[start:end]
            if original.startswith(b"CRILAYLA"):
                expected, _ = _extract_validated_candidate(
                    source, name, source_sha256, original_index, decoded_limit=limit)
                if not packed.startswith(b"CRILAYLA") or decompress(packed, limit=limit) != expected:
                    raise ValueError("Selected member semantic mismatch")
            else:
                if original_index[name]["size"] != end - start or end - start > limit:
                    raise ValueError("Unsupported plain CPK member")
                expected, report = mark(bytes(original))
                if not report["marked_records"] or bytes(packed) != expected:
                    raise ValueError("Selected plain member semantic mismatch")
        cursor = end
    if source[cursor:] != output[cursor:]:
        raise ValueError("Archive trailing bytes changed")
    return {
        "source_sha256": source_sha256,
        "output_sha256": output_sha256,
        "selected_paths": sorted(paths),
        "metadata_and_other_payloads_unchanged": True,
        "runtime_verified": False,
        "ready_for_gameplay_test": False,
    }
