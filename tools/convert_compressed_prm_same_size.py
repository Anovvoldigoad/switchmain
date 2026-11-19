"""Offline source-bound Event236 conversion and same-size CPK publication.

Supports exact-size CRILAYLA and uncompressed PRMs; no relocation or game hook.
"""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import tempfile

from portlib.compressed_prm_events import reencode_candidate
from portlib.cpk_events import entries, canonical
from portlib.prm_events import mark
from publish_same_size_cpk import publish


def convert_many(source_path, source_sha256, members, output_path):
    """Atomically publish multiple exact-size compressed Event236 edits offline."""
    source_path, output_path = Path(source_path), Path(output_path)
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError(output_path)
    if output_path.resolve() == source_path.resolve():
        raise ValueError("Source and output must differ")
    if not isinstance(members, (list, tuple)) or not members:
        raise ValueError("Nonempty member list required")
    if any(not isinstance(member, str) for member in members):
        raise ValueError("Member names must be strings")
    if len({member.casefold() for member in members}) != len(members):
        raise ValueError("Duplicate member")

    candidates = {}
    with tempfile.TemporaryDirectory(prefix=".cpk-candidate-", dir=output_path.parent) as folder:
        manifest = {}
        with source_path.open("rb") as handle:
            with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as source:
                if hashlib.sha256(source).hexdigest() != source_sha256:
                    raise ValueError("CPK source SHA256 mismatch")
                index = entries(source)
                for number, member in enumerate(members):
                    path = canonical(member)
                    if path not in index:
                        raise ValueError("CPK entry not found")
                    entry = index[path]
                    stored = source[entry["offset"]:entry["offset"] + entry["stored_size"]]
                    if stored.startswith(b"CRILAYLA"):
                        packed, candidate = reencode_candidate(
                            source, path, source_sha256, _validated_index=index)
                        if not candidate["changed_decoded_offsets"]:
                            raise ValueError("No Event236 change; refusing redundant archive publication")
                        if candidate["stored_size_delta"] != 0:
                            raise ValueError("Compressed candidate changes stored size; CPK relocation not supported")
                    else:
                        if entry["stored_size"] != entry["size"]:
                            raise ValueError("Unsupported CPK entry encoding")
                        packed, report = mark(bytes(stored))
                        if not report["marked_records"]:
                            raise ValueError("No Event236 change; refusing redundant archive publication")
                        if len(packed) != entry["stored_size"]:
                            raise ValueError("Uncompressed PRM changes stored size")
                        candidate = {
                            "path": path,
                            "candidate_stored_sha256": hashlib.sha256(packed).hexdigest(),
                            "candidate_decoded_sha256": hashlib.sha256(packed).hexdigest(),
                            "marked_records": report["marked_records"],
                        }
                    if hashlib.sha256(packed).hexdigest() != candidate["candidate_stored_sha256"]:
                        raise ValueError("Candidate SHA256 mismatch")
                    packed_path = Path(folder) / f"{number}.crilayla"
                    packed_path.write_bytes(packed)
                    manifest[candidate["path"]] = str(packed_path)
                    candidates[candidate["path"]] = {
                        "candidate_stored_sha256": candidate["candidate_stored_sha256"],
                        "candidate_decoded_sha256": candidate["candidate_decoded_sha256"],
                        "marked_records": candidate["marked_records"],
                    }
        manifest_path = Path(folder) / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        proof = publish(source_path, source_sha256, manifest_path, output_path)
    return {**proof, "candidates": candidates,
            "gameplay_verified": False, "ready_for_gameplay_test": False}


def convert(source_path, source_sha256, member, output_path):
    proof = convert_many(source_path, source_sha256, [member], output_path)
    candidate = next(iter(proof["candidates"].values()))
    return {**proof, **candidate}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("source_sha256")
    parser.add_argument("members", nargs="+", metavar="member",
                        help="One or more CPK member paths (output path last)")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(convert_many(args.source, args.source_sha256, args.members, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
