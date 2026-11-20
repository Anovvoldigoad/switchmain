"""Offline multi-member decoded PRM export; never emits an installable CPK.

Manifest JSON: {"members":[{"path":"data/...xfbin","output":"name.decoded.bin"}]}.
All members must belong to the same SHA-pinned archive. No output on validation failure.
"""
import argparse
import hashlib
import json
import mmap
import os
import tempfile
from pathlib import Path
from portlib.compressed_prm_events import _extract_validated_candidate, SHA
from portlib.cpk_events import entries


def export_batch(archive, sha256, manifest, output_dir, *, limit=256 * 1024 * 1024):
    archive, output_dir = Path(archive), Path(output_dir)
    if not output_dir.is_dir():
        raise ValueError("Existing output directory required")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("members"), list) or not manifest["members"]:
        raise ValueError("Nonempty members array required")
    if len(manifest["members"]) > 128:
        raise ValueError("Too many members")
    planned, seen_paths, seen_outputs = [], set(), set()
    for row in manifest["members"]:
        if not isinstance(row, dict) or set(row) != {"path", "output"}:
            raise ValueError("Each member requires path and output only")
        path, name = row["path"], row["output"]
        if not isinstance(path, str) or not path or not isinstance(name, str) or not name or name in (".", "..") or Path(name).name != name or "\\" in name:
            raise ValueError("Unsafe member or output")
        path_key, output_key = path.replace("\\", "/").casefold(), name.casefold()
        if path_key in seen_paths or output_key in seen_outputs:
            raise ValueError("Duplicate source path or output name")
        seen_paths.add(path_key)
        seen_outputs.add(output_key)
        dest = output_dir / name
        if dest.exists() or dest.is_symlink():
            raise ValueError("Output already exists")
        planned.append((path, dest))
    staged, created = [], []
    with tempfile.TemporaryDirectory(prefix=".decoded-prm-stage-", dir=output_dir) as scratch:
        with archive.open("rb") as handle:
            with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as source:
                if not isinstance(sha256, str) or not SHA.fullmatch(sha256):
                    raise ValueError("Exact source SHA256 required")
                if hashlib.sha256(source).hexdigest() != sha256:
                    raise ValueError("Source SHA256 mismatch")
                index = entries(source)
                for number, (path, dest) in enumerate(planned):
                    candidate, report = _extract_validated_candidate(
                        source, path, sha256, index, decoded_limit=limit)
                    if hashlib.sha256(candidate).hexdigest() != report["candidate_decoded_sha256"]:
                        raise ValueError("Candidate integrity mismatch")
                    temporary = Path(scratch) / str(number)
                    with temporary.open("xb") as output:
                        output.write(candidate)
                        output.flush()
                        os.fsync(output.fileno())
                    staged.append((dest, temporary, report))
                    del candidate
        try:
            for dest, temporary, _ in staged:
                os.link(temporary, dest)
                created.append(dest)
        except BaseException:
            for dest in created:
                dest.unlink(missing_ok=True)
            raise
    return {"source_sha256": sha256, "output_is_installable": False,
            "compressed_archive_repacked": False,
            "members": [{**report, "output": dest.name} for dest, _, report in staged]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive")
    p.add_argument("sha256")
    p.add_argument("manifest")
    p.add_argument("output_dir")
    args = p.parse_args()
    report = export_batch(args.archive, args.sha256, json.loads(Path(args.manifest).read_text()), args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
