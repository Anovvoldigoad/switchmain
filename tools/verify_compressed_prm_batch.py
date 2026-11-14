"""Verify offline CRILAYLA candidates against original SHA-pinned CPK bytes; no repacking."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
from portlib.compressed_prm_events import _extract_validated_candidate, SHA
from portlib.cpk_events import entries
from portlib.crilayla import decompress

def verify_batch(archive, sha256, report, output_dir, *, limit=256 * 1024 * 1024):
    if not isinstance(sha256, str) or not SHA.fullmatch(sha256):
        raise ValueError("Exact source SHA256 required")
    if not isinstance(limit, int) or limit < 256:
        raise ValueError("Invalid decoded limit")
    if (not isinstance(report, dict) or report.get("source_sha256") != sha256
            or report.get("output_is_installable") is not False
            or report.get("compressed_archive_repacked") is not False):
        raise ValueError("Invalid source-bound report")
    rows = report.get("members")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 128:
        raise ValueError("Expected 1..128 report members")
    root = Path(output_dir)
    if not root.is_dir():
        raise ValueError("Output directory missing")
    seen = set()
    with Path(archive).open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as source:
        if hashlib.sha256(source).hexdigest() != sha256:
            raise ValueError("Source CPK SHA256 mismatch")
        index = entries(source)
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Malformed member")
            name = row.get("output")
            if (not isinstance(name, str) or not name or name in (".", "..")
                    or Path(name).name != name or "/" in name or "\\" in name):
                raise ValueError("Unsafe output name")
            if name.casefold() in seen:
                raise ValueError("Duplicate output")
            seen.add(name.casefold())
            expected, original = _extract_validated_candidate(
                source, row.get("path"), sha256, index, decoded_limit=limit)
            for field in ("path", "stored_sha256", "decoded_sha256",
                          "candidate_decoded_sha256", "changed_decoded_offsets",
                          "event236_provenance", "marked_records", "already_marked",
                          "native_event236_preserved"):
                if row.get(field) != original[field]:
                    raise ValueError("Candidate provenance mismatch: " + field)
            path = root / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("Candidate missing or symlink")
            if path.stat().st_size > limit * 2 + 272:
                raise ValueError("Candidate exceeds stored bound")
            packed = path.read_bytes()
            if (hashlib.sha256(packed).hexdigest() != row.get("compressed_candidate_sha256")
                    or len(packed) != row.get("compressed_candidate_bytes")):
                raise ValueError("Compressed candidate integrity mismatch")
            if decompress(packed, limit=limit) != expected:
                raise ValueError("Decoded candidate differs from pinned source")
    return {"verified_members": len(rows), "source_sha256": sha256,
            "byte_exact_decoded_match": True, "gameplay_verified": False,
            "compressed_archive_repacked": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "sha256", "report", "output_dir"):
        parser.add_argument(name)
    parser.add_argument("--decoded-limit", type=int, default=256 * 1024 * 1024)
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text())
    print(json.dumps(verify_batch(args.archive, args.sha256, report, args.output_dir,
                                  limit=args.decoded_limit), sort_keys=True))

if __name__ == "__main__":
    main()
