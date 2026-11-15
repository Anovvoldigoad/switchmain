#!/usr/bin/env python3
"""Apply multiple source-authenticated PC editor mod removals/replacements at once.

This only emits NSC editor index manifests, never game binaries or hooks.
"""
import argparse
import json
from pathlib import Path

from merge_pc_moveset_nsc_manifests import merge
from verify_pc_moveset_nsc_sources import verify


def patch_verified(payload, evidence, sources, removals=(), replacements=()):
    """Replay old sources, apply all edits simultaneously, replay final sources."""
    verify(payload, evidence, sources)
    removed = list(removals)
    replacement_list = list(replacements)
    names = [name for name, _, _ in sources]
    changed = removed + [name for name, _, _ in replacement_list]
    if not changed or len(changed) != len(set(changed)):
        raise ValueError('Expected nonempty, disjoint mod changes')
    if any(name not in names for name in changed):
        raise ValueError('Unknown mod name')
    replacement_map = {name: (name, raw, sha) for name, raw, sha in replacement_list}
    updated = [replacement_map.get(name, (name, raw, sha))
               for name, raw, sha in sources if name not in removed]
    if not updated:
        raise ValueError('Cannot remove all mods')
    result, proof = merge(updated)
    verify(result, proof, updated)
    return result, proof


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--merged', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--source', nargs=3, action='append', required=True,
                   metavar=('NAME', 'PATH', 'SHA256'))
    p.add_argument('--remove', action='append', default=[], metavar='NAME')
    p.add_argument('--replace', nargs=3, action='append', default=[],
                   metavar=('NAME', 'PATH', 'SHA256'))
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--output-evidence', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.output == args.output_evidence or args.output.exists() or args.output_evidence.exists():
            raise ValueError('Outputs must be distinct and absent')
        sources = [(name, Path(path).read_bytes(), sha) for name, path, sha in args.source]
        replacements = [(name, Path(path).read_bytes(), sha) for name, path, sha in args.replace]
        result, proof = patch_verified(args.merged.read_bytes(),
                                       json.loads(args.evidence.read_bytes()),
                                       sources, args.remove, replacements)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output_evidence.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as f:
            f.write(result)
        try:
            with args.output_evidence.open('xb') as f:
                f.write((json.dumps(proof, indent=2) + '\n').encode())
        except BaseException:
            args.output.unlink()
            raise
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        p.error(str(exc))
    print('PC_EDITOR_BATCH_PATCHED', len(args.remove) + len(args.replace), 'NOT_SWITCH_ABI')


if __name__ == '__main__':
    main()
