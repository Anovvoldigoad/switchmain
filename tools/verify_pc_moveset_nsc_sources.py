#!/usr/bin/env python3
"""Replay original PC editor manifests against a merged NSC index artifact.

This is source-authentication for offline editor indices, not Switch ABI proof.
"""
import argparse
import hashlib
import json
from pathlib import Path

from merge_pc_moveset_nsc_manifests import merge


def verify(payload, proof, sources):
    """Require exact source bytes, order, conversion and provenance."""
    if not 1 <= len(sources) <= 64:
        raise ValueError("Expected 1..64 original sources")
    if not isinstance(proof, dict) or not isinstance(proof.get("sources"), list):
        raise ValueError("Invalid merge evidence")
    if len(sources) != len(proof["sources"]):
        raise ValueError("Source count mismatch")
    for (name, raw, expected_sha), origin in zip(sources, proof["sources"]):
        if not isinstance(origin, dict) or origin.get("name") != name:
            raise ValueError("Source order/name mismatch")
        if origin.get("input_sha256") != hashlib.sha256(raw).hexdigest():
            raise ValueError("Original source digest mismatch")
        if origin["input_sha256"] != expected_sha.lower():
            raise ValueError("Pinned source digest mismatch")
    rebuilt, rebuilt_proof = merge(sources)
    if rebuilt != payload or rebuilt_proof != proof:
        raise ValueError("Merged artifact/provenance differs from original source replay")
    return {"status": "PC_EDITOR_SOURCE_REPLAY_VERIFIED",
            "source_count": len(sources),
            "output_sha256": hashlib.sha256(payload).hexdigest(),
            "native_switch_abi_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merged", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--source", nargs=3, action="append",
                        metavar=("NAME", "PATH", "SHA256"), required=True)
    args = parser.parse_args()
    try:
        sources = [(name, Path(path).read_bytes(), sha)
                   for name, path, sha in args.source]
        result = verify(args.merged.read_bytes(),
                        json.loads(args.evidence.read_bytes()), sources)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
