"""Produce a SHA-pinned offline compressed PRM candidate; never repack CPK."""
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
from portlib.compressed_prm_events import extract_candidate
from portlib.crilayla_literal import encode_literals
from portlib.crilayla import decompress


def export(archive, member, sha256, destination, *, limit=256 * 1024 * 1024):
    archive, destination = Path(archive), Path(destination)
    if destination.exists():
        raise ValueError("Destination already exists")
    # Map the read-only source; never allocate the full CPK as a Python bytes copy.
    with archive.open('rb') as source_file:
        with mmap.mmap(source_file.fileno(), 0, access=mmap.ACCESS_READ) as source:
            candidate, report = extract_candidate(source, member, sha256, decoded_limit=limit)
    if len(candidate) < 256:
        raise ValueError("Decoded candidate lacks CRILAYLA prefix")
    packed = encode_literals(candidate, limit=limit)
    if decompress(packed, limit=limit) != candidate:
        raise ValueError("Compressed candidate roundtrip mismatch")
    if hashlib.sha256(candidate).hexdigest() != report["candidate_decoded_sha256"]:
        raise ValueError("Candidate decoded SHA256 mismatch")
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(packed)
            out.flush()
            os.fsync(out.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {**report, "compressed_candidate_sha256": hashlib.sha256(packed).hexdigest(),
            "compressed_candidate_bytes": len(packed), "output": str(destination),
            "output_is_installable": False, "compressed_archive_repacked": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "member", "sha256", "output"):
        parser.add_argument(name)
    parser.add_argument("--decoded-limit", type=int, default=256 * 1024 * 1024)
    args = parser.parse_args(argv)
    if args.decoded_limit < 256:
        parser.error("--decoded-limit must be >= 256")
    print(json.dumps(export(args.archive, args.member, args.sha256, args.output,
                            limit=args.decoded_limit), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
