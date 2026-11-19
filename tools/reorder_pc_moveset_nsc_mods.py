#!/usr/bin/env python3
"""Reorder authenticated PC MovesetPlus editor manifests, not Switch runtime."""
import argparse
import json
from pathlib import Path

from merge_pc_moveset_nsc_manifests import merge
from verify_pc_moveset_nsc_sources import verify


def reorder_verified(payload, proof, sources, order):
    """Authenticate old composition, then replay exact bytes in requested order."""
    verify(payload, proof, sources)
    names = [name for name, _, _ in sources]
    if not isinstance(order, (list, tuple)) or len(order) != len(names):
        raise ValueError("Order must contain each source exactly once")
    if any(not isinstance(name, str) for name in order) or set(order) != set(names):
        raise ValueError("Order must be a permutation of source names")
    lookup = {name: item for name, *rest in sources for item in [(name, *rest)]}
    ordered = [lookup[name] for name in order]
    result, evidence = merge(ordered)
    verify(result, evidence, ordered)
    return result, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--merged", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--source", nargs=3, action="append", required=True,
                   metavar=("NAME", "PATH", "SHA256"))
    p.add_argument("--order", nargs="+", required=True, metavar="NAME")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--output-evidence", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.output == args.output_evidence or args.output.exists() or args.output_evidence.exists():
            raise ValueError("Outputs must be distinct and absent")
        sources = [(n, Path(path).read_bytes(), sha) for n, path, sha in args.source]
        result, evidence = reorder_verified(
            args.merged.read_bytes(), json.loads(args.evidence.read_bytes()),
            sources, args.order)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output_evidence.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as out:
            out.write(result)
        try:
            with args.output_evidence.open("xb") as out:
                out.write((json.dumps(evidence, indent=2) + "\n").encode())
        except BaseException:
            args.output.unlink()
            raise
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        p.error(str(exc))
    print("PC_EDITOR_MODS_REORDERED", len(args.order), "NOT_SWITCH_ABI")


if __name__ == "__main__":
    main()
