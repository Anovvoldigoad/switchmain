"""Offline, fail-closed publication of a SHA-pinned same-size CPK edit.

No runtime hook or claim of compatibility with authentic Switch archives.
"""
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import tempfile

from portlib.cpk_same_size import replace_many_same_size


def publish(source_path, source_sha256, manifest_path, output_path):
    source_path, manifest_path, output_path = map(Path, (source_path, manifest_path, output_path))
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError(output_path)
    def unique_members(pairs):
        result = {}
        seen = set()
        for key, value in pairs:
            folded = key.casefold()
            if folded in seen:
                raise ValueError("Duplicate manifest member")
            seen.add(folded)
            result[key] = value
        return result

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"), object_pairs_hook=unique_members)
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError("Nonempty JSON path-to-candidate-file mapping required")
    replacements = {}
    for member, candidate in manifest.items():
        if not isinstance(member, str) or not isinstance(candidate, str):
            raise ValueError("Manifest keys and values must be strings")
        replacements[member] = Path(candidate).read_bytes()
    with source_path.open("rb") as handle:
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as source:
            output, proof = replace_many_same_size(source, source_sha256, replacements)
    # Never overwrite the source or another existing output. Stage in the target
    # directory and publish with an exclusive hard link, then remove staging.
    if output_path.resolve() == source_path.resolve():
        raise ValueError("Output must differ from source")
    fd, staged = tempfile.mkstemp(prefix=".cpk-stage-", dir=output_path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(output)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(staged, output_path)
    finally:
        os.unlink(staged)
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("source_sha256")
    parser.add_argument("manifest", help="JSON mapping CPK member paths to packed candidate files")
    parser.add_argument("output")
    args = parser.parse_args()
    proof = publish(args.source, args.source_sha256, args.manifest, args.output)
    print(json.dumps(proof, sort_keys=True))


if __name__ == "__main__":
    main()
