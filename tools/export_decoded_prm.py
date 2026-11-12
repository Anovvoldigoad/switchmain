"""Export a SHA-pinned, decoded-only CRILAYLA PRM candidate (NOT installable).

Usage: python tools/export_decoded_prm.py archive.cpk path/in/cpk 64hexsha candidate.decoded.bin
The output is an uncompressed PRM, never a repacked CPK.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from portlib.compressed_prm_events import extract_candidate


def export(archive, member, sha256, destination, *, limit=256 * 1024 * 1024):
    archive = Path(archive)
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Destination already exists")
    if not isinstance(sha256, str) or len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
        raise ValueError("Exact lowercase source SHA256 required")
    # A single pinned read: no file modifications or candidate output before validation.
    source = archive.read_bytes()
    if hashlib.sha256(source).hexdigest() != sha256:
        raise ValueError("Source archive SHA256 mismatch")
    candidate, report = extract_candidate(source, member, sha256, decoded_limit=limit)
    if hashlib.sha256(candidate).hexdigest() != report["candidate_decoded_sha256"]:
        raise ValueError("Candidate SHA256 mismatch")
    # Exclusive creation avoids silently overwriting an existing candidate.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(candidate)
            out.flush()
            os.fsync(out.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return {**report, "output": str(destination), "output_sha256": hashlib.sha256(candidate).hexdigest(),
            "output_is_installable": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    parser.add_argument("member")
    parser.add_argument("sha256")
    parser.add_argument("output")
    parser.add_argument("--decoded-limit", type=int, default=256 * 1024 * 1024)
    args = parser.parse_args(argv)
    if args.decoded_limit < 256:
        parser.error("--decoded-limit must be >= 256")
    result = export(args.archive, args.member, args.sha256, args.output, limit=args.decoded_limit)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
