#!/usr/bin/env python3
"""Reassemble SHA-authenticated PC editor owner partitions; never a Switch consumer."""
import argparse
import hashlib
import json
from pathlib import Path
from merge_pc_moveset_nsc_manifests import merge_resolved, reassemble_owner_partitions, partition_resolved

def restore(directory, proof, sources):
    expected, authentic = merge_resolved(sources, proof.get("resolved_owners"))
    if proof != authentic:
        raise ValueError("Source provenance mismatch")
    parts = partition_resolved(expected, proof, sources)
    index = {"status": "PC_EDITOR_STANDALONE_PARTITIONS_ONLY",
             "merged_sha256": hashlib.sha256(expected).hexdigest(),
             "partitions": [], "native_switch_abi_verified": False}
    names = {"index.json"}
    for i, (name, data, digest) in enumerate(parts):
        filename = f"{i:03d}.json"
        names.add(filename)
        index["partitions"].append({"source": name, "file": filename, "sha256": digest})
        path = directory / filename
        if path.is_symlink() or path.read_bytes() != data:
            raise ValueError("Partition byte mismatch")
    index_bytes = (json.dumps(index, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path = directory / "index.json"
    if path.is_symlink() or path.read_bytes() != index_bytes:
        raise ValueError("Index byte mismatch")
    if {p.name for p in directory.iterdir()} != names:
        raise ValueError("Unexpected partition entry")
    result = reassemble_owner_partitions(parts, proof)
    if result != expected:
        raise ValueError("Restored bytes mismatch")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", nargs=3, action="append", required=True, metavar=("NAME", "FILE", "SHA256"))
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.output == args.evidence:
        p.error("Output must be absent and distinct")
    try:
        sources = [(name, Path(file).read_bytes(), sha) for name, file, sha in args.source]
        proof = json.loads(args.evidence.read_bytes())
        data = restore(args.directory, proof, sources)
        with args.output.open("xb") as out:
            out.write(data)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        p.error(str(exc))
    print("PC_EDITOR_REASSEMBLED NOT_SWITCH_ABI")

if __name__ == "__main__":
    main()
