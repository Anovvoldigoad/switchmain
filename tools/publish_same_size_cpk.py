"""Offline, fail-closed publication of a SHA-pinned same-size CPK edit.

No runtime hook or claim of compatibility with authentic Switch archives.
"""
import argparse
from contextlib import ExitStack
import hashlib
import json
import mmap
import os
from pathlib import Path
import tempfile

from portlib.cpk_same_size import validate_many_same_size
from portlib.cpk_same_size_verify import verify_same_size_output


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
    with ExitStack() as stack:
        replacements = {}
        for member, candidate in manifest.items():
            if not isinstance(member, str) or not isinstance(candidate, str):
                raise ValueError("Manifest keys and values must be strings")
            candidate_handle = stack.enter_context(Path(candidate).open("rb"))
            replacements[member] = stack.enter_context(mmap.mmap(candidate_handle.fileno(), 0, access=mmap.ACCESS_READ))
        source_handle = stack.enter_context(source_path.open("rb"))
        source = stack.enter_context(mmap.mmap(source_handle.fileno(), 0, access=mmap.ACCESS_READ))
        changes, _, paths = validate_many_same_size(source, source_sha256, replacements)
        if output_path.resolve() == source_path.resolve():
            raise ValueError("Output must differ from source")
        fd, staged = tempfile.mkstemp(prefix=".cpk-stage-", dir=output_path.parent)
        try:
            digest = hashlib.sha256()
            with os.fdopen(fd, "wb") as target:
                cursor = 0
                for start, end, packed in sorted(changes):
                    for offset in range(cursor, start, 1024 * 1024):
                        chunk = source[offset:min(offset + 1024 * 1024, start)]
                        target.write(chunk)
                        digest.update(chunk)
                    target.write(packed)
                    digest.update(packed)
                    cursor = end
                for offset in range(cursor, len(source), 1024 * 1024):
                    chunk = source[offset:min(offset + 1024 * 1024, len(source))]
                    target.write(chunk)
                    digest.update(chunk)
                target.flush()
                os.fsync(target.fileno())
            proof = {"source_sha256": source_sha256, "output_sha256": digest.hexdigest(),
                     "selected_paths": sorted(paths), "metadata_and_other_payloads_unchanged": True,
                     "runtime_verified": False, "ready_for_gameplay_test": False}
            with open(staged, "rb") as written_handle:
                with mmap.mmap(written_handle.fileno(), 0, access=mmap.ACCESS_READ) as written:
                    verify_same_size_output(source, written, source_sha256,
                                            proof["output_sha256"], proof["selected_paths"])
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
