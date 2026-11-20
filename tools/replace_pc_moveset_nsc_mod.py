#!/usr/bin/env python3
"""Replace one SHA-pinned PC MovesetPlus editor source; no Switch runtime writes."""
import argparse
import json
from pathlib import Path

from merge_pc_moveset_nsc_manifests import merge
from verify_pc_moveset_nsc_sources import verify


def replace_verified(payload, proof, sources, name, replacement):
    """Authenticate the old composition, then rebuild from exact replacement bytes."""
    verify(payload, proof, sources)
    if [s[0] for s in sources].count(name) != 1:
        raise ValueError("Replacement mod name must occur exactly once")
    updated = [replacement if s[0] == name else s for s in sources]
    if replacement[0] != name:
        raise ValueError("Replacement must retain the original mod name")
    result, evidence = merge(updated)
    verify(result, evidence, updated)
    return result, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--merged", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    p.add_argument("--source", nargs=3, action="append", required=True,
                   metavar=("NAME", "PATH", "SHA256"))
    p.add_argument("--replace", required=True)
    p.add_argument("--replacement", nargs=2, required=True, metavar=("PATH", "SHA256"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--output-evidence", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.output == args.output_evidence or args.output.exists() or args.output_evidence.exists():
            raise ValueError("Outputs must be distinct and absent")
        sources = [(n, Path(path).read_bytes(), sha) for n, path, sha in args.source]
        replacement = (args.replace, Path(args.replacement[0]).read_bytes(), args.replacement[1])
        result, evidence = replace_verified(args.merged.read_bytes(),
                                            json.loads(args.evidence.read_bytes()),
                                            sources, args.replace, replacement)
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
    print("PC_EDITOR_MOD_REPLACED", args.replace, "NOT_SWITCH_ABI")


if __name__ == "__main__":
    main()
