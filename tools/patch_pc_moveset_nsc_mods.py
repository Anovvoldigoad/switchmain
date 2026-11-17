#!/usr/bin/env python3
"""Apply multiple source-authenticated PC editor mod removals/replacements/additions at once.

This only emits NSC editor index manifests, never game binaries or hooks.
"""
import argparse
import json
from pathlib import Path

from merge_pc_moveset_nsc_manifests import merge
from verify_pc_moveset_nsc_sources import verify


def patch_verified(payload, evidence, sources, removals=(), replacements=(), additions=(), order=None):
    """Replay old sources, apply all edits simultaneously, replay final sources."""
    verify(payload, evidence, sources)
    removed = list(removals)
    replacement_list = list(replacements)
    additions = list(additions)
    names = [name for name, _, _ in sources]
    added_names = [name for name, _, _ in additions]
    changed = removed + [name for name, _, _ in replacement_list]
    if (not changed and not additions and order is None) or len(changed) != len(set(changed)):
        raise ValueError('Expected nonempty, disjoint mod changes')
    if (len(added_names) != len(set(added_names)) or
            any(name in names for name in added_names)):
        raise ValueError('Added mod name already exists or is duplicated')
    if any(name not in names for name in changed):
        raise ValueError('Unknown mod name')
    replacement_map = {name: (name, raw, sha) for name, raw, sha in replacement_list}
    updated = [replacement_map.get(name, (name, raw, sha))
               for name, raw, sha in sources if name not in removed]
    updated.extend(additions)
    if not updated:
        raise ValueError('Cannot remove all mods')
    if order is not None:
        final_names = [name for name, _, _ in updated]
        if len(order) != len(final_names) or set(order) != set(final_names) or len(set(order)) != len(order):
            raise ValueError('Order must be an exact permutation of final mod names')
        by_name = {name: item for item in updated for name in [item[0]]}
        updated = [by_name[name] for name in order]
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
    p.add_argument('--add', nargs=3, action='append', default=[],
                   metavar=('NAME', 'PATH', 'SHA256'))
    p.add_argument('--replace', nargs=3, action='append', default=[],
                   metavar=('NAME', 'PATH', 'SHA256'))
    p.add_argument('--order', nargs='+', metavar='NAME', help='Exact final mod order')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--output-evidence', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.output == args.output_evidence or args.output.exists() or args.output_evidence.exists():
            raise ValueError('Outputs must be distinct and absent')
        sources = [(name, Path(path).read_bytes(), sha) for name, path, sha in args.source]
        replacements = [(name, Path(path).read_bytes(), sha) for name, path, sha in args.replace]
        additions = [(name, Path(path).read_bytes(), sha) for name, path, sha in args.add]
        result, proof = patch_verified(args.merged.read_bytes(),
                                       json.loads(args.evidence.read_bytes()),
                                       sources, args.remove, replacements, additions, args.order)
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
    print('PC_EDITOR_BATCH_PATCHED', len(args.remove) + len(args.replace) + len(args.add) + int(args.order is not None), 'NOT_SWITCH_ABI')


if __name__ == '__main__':
    main()
