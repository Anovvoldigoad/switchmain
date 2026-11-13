"""Offline atomic batch of SHA-pinned compressed PRM candidates; never repacks CPK."""
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path

from portlib.compressed_prm_events import extract_candidate
from portlib.crilayla import decompress
from portlib.crilayla_literal import encode_literals


def export_batch(archive, sha256, manifest, output_dir, *, limit=256 * 1024 * 1024):
    archive, output_dir = Path(archive), Path(output_dir)
    if not output_dir.is_dir():
        raise ValueError("Existing output directory required")
    rows = manifest.get("members") if isinstance(manifest, dict) else None
    if not isinstance(rows, list) or not 1 <= len(rows) <= 128:
        raise ValueError("Expected 1..128 members")
    planned, paths, outputs = [], set(), set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "output"}:
            raise ValueError("Each member requires path and output")
        path, name = row["path"], row["output"]
        if (not isinstance(path, str) or not path or not isinstance(name, str)
                or not name or name in (".", "..") or Path(name).name != name
                or "\\" in name or "/" in name):
            raise ValueError("Unsafe member or output")
        key, outkey = path.replace("\\", "/").casefold(), name.casefold()
        if key in paths or outkey in outputs:
            raise ValueError("Duplicate source or destination")
        paths.add(key)
        outputs.add(outkey)
        destination = output_dir / name
        if destination.exists() or destination.is_symlink():
            raise ValueError("Destination exists")
        planned.append((path, destination))

    staged = []
    with archive.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as source:
            for path, destination in planned:
                candidate, report = extract_candidate(source, path, sha256, decoded_limit=limit)
                if hashlib.sha256(candidate).hexdigest() != report["candidate_decoded_sha256"]:
                    raise ValueError("Decoded candidate SHA mismatch")
                packed = encode_literals(candidate, limit=limit)
                if decompress(packed, limit=limit) != candidate:
                    raise ValueError("Compressed roundtrip mismatch")
                staged.append((destination, packed, {
                    **report,
                    "output": destination.name,
                    "compressed_candidate_sha256": hashlib.sha256(packed).hexdigest(),
                    "compressed_candidate_bytes": len(packed),
                }))
    created = []
    try:
        for destination, packed, _ in staged:
            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            created.append(destination)
            with os.fdopen(fd, "wb") as output:
                output.write(packed)
                output.flush()
                os.fsync(output.fileno())
    except BaseException:
        for destination in created:
            destination.unlink(missing_ok=True)
        raise
    return {"source_sha256": sha256, "output_is_installable": False,
            "compressed_archive_repacked": False,
            "members": [report for _, _, report in staged]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "sha256", "manifest", "output_dir"):
        parser.add_argument(name)
    parser.add_argument("--decoded-limit", type=int, default=256 * 1024 * 1024)
    args = parser.parse_args()
    if args.decoded_limit < 256:
        parser.error("decoded limit must be at least 256")
    manifest = json.loads(Path(args.manifest).read_text())
    report = export_batch(args.archive, args.sha256, manifest, args.output_dir,
                          limit=args.decoded_limit)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
