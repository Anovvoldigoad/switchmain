#!/usr/bin/env python3
"""Remove one mod from a verified PC-only merged editor index manifest.

No binary moveset, Switch ABI or runtime consumer is modified.
"""
import argparse
import hashlib
import json
from pathlib import Path

from merge_pc_moveset_nsc_manifests import split
from verify_pc_moveset_nsc_sources import verify


def remove_mod(payload, proof, name):
    if not isinstance(name, str) or not name:
        raise ValueError("A nonempty mod name is required")
    parts = split(payload, proof)
    if len(parts) < 2:
        raise ValueError("Cannot remove the final mod")
    names = [item[0] for item in parts]
    if names.count(name) != 1:
        raise ValueError("Mod not found or ambiguous")
    retained = [(origin, part) for origin, (_, part) in zip(proof["sources"], parts)
                if origin["name"] != name]
    events = []
    origins = []
    for origin, part in retained:
        rows = json.loads(part)["events"]
        entry = dict(origin)
        entry["start"] = len(events)
        entry["event_count"] = len(rows)
        origins.append(entry)
        events.extend(rows)
    result = (json.dumps({"source_version": "nsc", "events": events},
                         ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    evidence = dict(proof)
    evidence["sources"] = origins
    evidence["event_count"] = len(events)
    evidence["output_sha256"] = hashlib.sha256(result).hexdigest()
    # Independently check the new range/digest structure before publication.
    if [part for _, part in split(result, evidence)] != [part for _, part in
                                                          (x for x in parts if x[0] != name)]:
        raise ValueError("Retained source replay mismatch")
    return result, evidence


def remove_verified(payload, proof, name, sources):
    """Authenticate original source bytes before and after removal."""
    verify(payload, proof, sources)
    result, evidence = remove_mod(payload, proof, name)
    retained = [item for item in sources if item[0] != name]
    verify(result, evidence, retained)
    return result, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--merged", required=True, type=Path)
    p.add_argument("--evidence", required=True, type=Path)
    p.add_argument("--remove", required=True)
    p.add_argument("--source", nargs=3, action="append", required=True,
                   metavar=("NAME", "PATH", "SHA256"),
                   help="All original PC editor sources in merge order")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--output-evidence", required=True, type=Path)
    args = p.parse_args()
    try:
        if args.output == args.output_evidence or args.output.exists() or args.output_evidence.exists():
            raise ValueError("Outputs must be distinct and absent")
        sources = [(name, Path(path).read_bytes(), sha)
                   for name, path, sha in args.source]
        payload, proof = remove_verified(args.merged.read_bytes(),
                                         json.loads(args.evidence.read_bytes()),
                                         args.remove, sources)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output_evidence.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as out:
            out.write(payload)
        try:
            with args.output_evidence.open("xb") as out:
                out.write((json.dumps(proof, indent=2) + "\n").encode())
        except BaseException:
            args.output.unlink()
            raise
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        p.error(str(exc))
    print("PC_EDITOR_MOD_REMOVED", args.remove, "NOT_SWITCH_ABI")


if __name__ == "__main__":
    main()
