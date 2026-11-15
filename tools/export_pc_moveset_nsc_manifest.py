#!/usr/bin/env python3
"""Export a source-pinned PC MovesetPlus index manifest for NSC editor use.

This converts only verified PC editor function indices; it never edits moveset
binaries or asserts Switch engine function IDs, argument ABI or runtime support.
"""
import argparse
import hashlib
import json
from pathlib import Path

from pc_moveset_event_preflight import audit


def convert(raw, expected_sha256):
    if len(raw) > 4 * 1024 * 1024 or len(expected_sha256) != 64 or any(c not in '0123456789abcdefABCDEF' for c in expected_sha256):
        raise ValueError('Invalid source size or SHA256')
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256.lower():
        raise ValueError('Source SHA256 mismatch')
    checked = audit(json.loads(raw))
    target = {'source_version': 'nsc', 'events': [
        {'event_id': row['event_id'], 'function_index': row['target_nsc_index']}
        for row in checked['events']
    ]}
    verified = audit(target)
    if [r['target_nsc_name'] for r in verified['events']] != [r['source_name'] for r in checked['events']]:
        raise ValueError('Source/target function name mismatch')
    payload = (json.dumps(target, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    evidence = {'status': 'PC_MOVESET_NSC_EDITOR_INDEX_ONLY',
                'input_sha256': digest, 'output_sha256': hashlib.sha256(payload).hexdigest(),
                'source_version': checked['source_version'], 'event_count': checked['event_count'],
                'source_catalog_commit': checked['source_catalog_commit'],
                'source_catalog_blob': checked['source_catalog_blob'],
                'binary_layout_verified': False, 'native_switch_abi_verified': False,
                'gameplay_verified': False}
    return payload, evidence


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    args = p.parse_args()
    try:
        if args.output == args.evidence or args.output.exists() or args.evidence.exists():
            raise ValueError('Outputs must be distinct and absent')
        raw = args.manifest.read_bytes()
        payload, evidence = convert(raw, args.expected_sha256)
        evidence_bytes = (json.dumps(evidence, indent=2) + '\n').encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('xb') as f:
            f.write(payload)
        try:
            with args.evidence.open('xb') as f:
                f.write(evidence_bytes)
        except BaseException:
            args.output.unlink()
            raise
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    print('PC_MOVESET_NSC_INDEX_EXPORT', evidence['event_count'], 'NOT_SWITCH_ABI')


if __name__ == '__main__':
    main()
