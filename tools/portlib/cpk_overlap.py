"""Provenance-pinned inter-CPK path/content audit, NOT runtime load precedence.

A registered bind ID is not evidence of an asynchronously loaded archive.
CPK TOC paths and stored bytes are compared without guessing winner semantics.
"""
import hashlib
import mmap
import re
from contextlib import ExitStack
from pathlib import Path
from . import cpk_events, cpk_profile

SHA256 = re.compile(r'[0-9a-f]{64}\Z')
CONDITION = 'data/spc/conditionprm.bin.xfbin'


def inspect(manifest):
    if not isinstance(manifest, dict) or set(manifest) != {'archives'}:
        raise ValueError('Expected object with exactly archives list')
    archives = manifest['archives']
    if not isinstance(archives, list) or not archives:
        raise ValueError('Expected one or more explicitly pinned archives')
    rows = []
    for item in archives:
        if not isinstance(item, dict) or set(item) != {'source', 'path', 'priority', 'sha256'}:
            raise ValueError('Archive requires source/path/priority/sha256')
        if not isinstance(item['source'], str) or not item['source']:
            raise ValueError('Archive source path required')
        if not isinstance(item['sha256'], str) or not SHA256.fullmatch(item['sha256']):
            raise ValueError('Expected lowercase SHA256')
        rows.append({'path': item['path'], 'priority': item['priority']})
    # Reuse the production manifest's capacity, priority and ASCII-path gate.
    cpk_profile.validate_rows(rows)
    index = {}
    descriptions = []
    with ExitStack() as stack:
        for item in archives:
            source = Path(item['source'])
            if not source.is_file() or source.is_symlink():
                raise ValueError('Missing or symlinked CPK source: '+str(source))
            handle = stack.enter_context(source.open('rb'))
            if source.stat().st_size == 0:
                raise ValueError('Empty CPK source')
            data = stack.enter_context(mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ))
            sha = hashlib.sha256(data).hexdigest()
            if sha != item['sha256']:
                raise ValueError('CPK source SHA256 mismatch: '+str(source))
            entries = cpk_events.entries(data)
            descriptions.append({
                'source': str(source), 'runtime_path': item['path'],
                'priority': item['priority'], 'source_sha256': sha,
                'entry_count': len(entries)})
            for entry_path, entry in entries.items():
                at = entry['offset']
                n = entry['stored_size']
                stored = memoryview(data)[at:at+n]
                digest = hashlib.sha256(stored).hexdigest()
                compressed = n != entry['size'] or stored[:8].tobytes() == b'CRILAYLA'
                stored.release()
                index.setdefault(entry_path.casefold(), []).append({
                    'archive_index': len(descriptions)-1,
                    'path': entry_path, 'entry_id': entry['id'],
                    'stored_size': n, 'extracted_size': entry['size'],
                    'stored_sha256': digest, 'compressed_or_codec_unknown': compressed})
    collisions = []
    for casefold_path, owners in sorted(index.items()):
        if len(owners) < 2:
            continue
        same_name = len({o['path'] for o in owners}) == 1
        same_stored = len({(o['stored_sha256'], o['stored_size'], o['extracted_size']) for o in owners}) == 1
        decoded = all(not o['compressed_or_codec_unknown'] for o in owners)
        collisions.append({
            'path_casefold': casefold_path, 'owners': owners,
            'exact_case_match': same_name,
            'stored_bytes_identical': same_stored,
            'uncompressed_content_identical': same_stored and decoded,
            'requires_manual_resolution': not same_name or not (same_stored and decoded),
            'condition_companion_collision': casefold_path == CONDITION.casefold(),
            'effective_archive_winner_verified': False})
    return {
        'status': 'STATIC_CPK_COLLISION_AUDIT',
        'archives': descriptions,
        'unique_path_keys': len(index),
        'overlapping_paths': len(collisions),
        'divergent_or_unresolved_paths': sum(c['requires_manual_resolution'] for c in collisions),
        'condition_companion_overlap': any(c['condition_companion_collision'] for c in collisions),
        'collisions': collisions,
        'registration_priority_is_not_lookup_precedence_proof': True,
        'async_load_or_unbind_verified': False,
        'effective_archive_winner_verified': False,
        'gameplay_verified': False, 'full_moddingapi': False,
        'ready_for_gameplay_test': False}
