#!/usr/bin/env python3
"""Restore verified per-mod PC editor manifests from a merged index artifact."""
import argparse
import hashlib
import json
from pathlib import Path
from merge_pc_moveset_nsc_manifests import split
from verify_pc_moveset_nsc_sources import verify


def restore(payload, proof, directory):
    """Publish all validated parts exclusively, or leave no new files."""
    parts = split(payload, proof)
    if not 1 <= len(parts) <= 64:
        raise ValueError("Invalid source count")
    if not directory.is_dir():
        raise ValueError("Output directory must already exist")
    targets = [directory / f"{i:02d}.nsc.json" for i in range(len(parts))]
    if any(path.exists() or path.is_symlink() for path in targets):
        raise ValueError("Output already exists")
    created = []
    try:
        for target, (_, raw) in zip(targets, parts):
            with target.open("xb") as stream:
                created.append(target)
                stream.write(raw)
    except BaseException:
        for target in reversed(created):
            target.unlink()
        raise
    return [{"name": name, "file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
            for (name, raw), path in zip(parts, targets)]


def restore_verified(payload, proof, sources, directory):
    """Authenticate original PC sources before publishing converted per-mod indices."""
    verify(payload, proof, sources)
    return restore(payload, proof, directory)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--merged", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--source", nargs=3, action="append", required=True,
                   metavar=("NAME", "PATH", "SHA256"))
    args = p.parse_args()
    try:
        sources = [(name, Path(path).read_bytes(), sha) for name, path, sha in args.source]
        result = restore_verified(args.merged.read_bytes(),
                                  json.loads(args.evidence.read_bytes()), sources,
                                  args.directory)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        p.error(str(exc))
    print(json.dumps({"status": "PC_EDITOR_INDEX_ONLY", "restored": result},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
