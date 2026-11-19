"""Offline source-bound Event236 conversion and same-size CPK publication.

Only exact-size CRILAYLA candidates can be published; no relocation or game hook.
"""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import tempfile

from portlib.compressed_prm_events import reencode_candidate
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
                for number, member in enumerate(members):
                    packed, candidate = reencode_candidate(source, member, source_sha256)
                    if not candidate["changed_decoded_offsets"]:
                        raise ValueError("No Event236 change; refusing redundant archive publication")
                    if candidate["stored_size_delta"] != 0:
                        raise ValueError("Compressed candidate changes stored size; CPK relocation not supported")
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
