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


def convert(source_path, source_sha256, member, output_path):
    source_path, output_path = Path(source_path), Path(output_path)
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError(output_path)
    if output_path.resolve() == source_path.resolve():
        raise ValueError("Source and output must differ")
    with source_path.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as source:
            packed, candidate = reencode_candidate(source, member, source_sha256)
    if not candidate["changed_decoded_offsets"]:
        raise ValueError("No Event236 change; refusing redundant archive publication")
    if candidate["stored_size_delta"] != 0:
        raise ValueError("Compressed candidate changes stored size; CPK relocation not supported")
    if hashlib.sha256(packed).hexdigest() != candidate["candidate_stored_sha256"]:
        raise ValueError("Candidate SHA256 mismatch")
    with tempfile.TemporaryDirectory(prefix=".cpk-candidate-", dir=output_path.parent) as folder:
        packed_path = Path(folder) / "candidate.crilayla"
        manifest_path = Path(folder) / "manifest.json"
        packed_path.write_bytes(packed)
        manifest_path.write_text(json.dumps({candidate["path"]: str(packed_path)}), encoding="utf-8")
        proof = publish(source_path, source_sha256, manifest_path, output_path)
    return {**proof, "candidate_stored_sha256": candidate["candidate_stored_sha256"],
            "candidate_decoded_sha256": candidate["candidate_decoded_sha256"],
            "marked_records": candidate["marked_records"],
            "gameplay_verified": False, "ready_for_gameplay_test": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("source_sha256")
    parser.add_argument("member")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(convert(args.source, args.source_sha256, args.member, args.output), sort_keys=True))


if __name__ == "__main__":
    main()
