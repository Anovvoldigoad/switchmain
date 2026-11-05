"""Byte-level audit of raw176 condition records; no effect-field semantics inferred."""
import hashlib
import re
import struct
from .condition_companion import validate as validate_companion
from .condition_profile import NATIVE_COUNT, PC_RECORD_SIZE
from .prm_events import binary_chunks

RECORD_SIZE = 176
NAME_SIZE = 64


def _records(raw, expected_sha256):
    if not isinstance(expected_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('Expected explicit lowercase raw XFBIN SHA256')
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError('Raw XFBIN SHA256 mismatch')
    chunks = binary_chunks(raw)
    if len(chunks) != 1 or chunks[0][0] != 'conditionprm':
        raise ValueError('Expected exactly one conditionprm binary chunk')
    _, start, size = chunks[0]
    if size < 8:
        raise ValueError('Truncated raw condition count')
    count = struct.unpack_from('<I', raw, start + 4)[0]
    if count < NATIVE_COUNT or count > 1024 or size != 8 + count * RECORD_SIZE:
        raise ValueError('Invalid raw176 record count/size')
    result = []
    for i in range(count):
        at = start + 8 + i * RECORD_SIZE
        name = raw[at:at + NAME_SIZE]
        if b'\0' not in name:
            raise ValueError(f'Unterminated raw name at index {i}')
        name = name.split(b'\0', 1)[0]
        try:
            name = name.decode('ascii')
        except UnicodeDecodeError:
            raise ValueError(f'Non-ASCII raw name at index {i}') from None
        result.append((name, raw[at + NAME_SIZE:at + RECORD_SIZE]))
    return result, digest


def compare(manager, stock, stock_sha256, candidate, candidate_sha256):
    """Stock must be a 512-row raw file; candidate must follow pinned PC manager ordinals.

    No proof of source-platform provenance or gameplay compatibility is implied.
    """
    # Validate the entire candidate via the already-audited count/name/manager
    # binding. This also rejects unpinned or reordered PC baseline descriptors.
    companion = validate_companion(manager, candidate, candidate_sha256)
    native, native_digest = _records(stock, stock_sha256)
    mod, mod_digest = _records(candidate, candidate_sha256)
    if len(native) != NATIVE_COUNT or len(mod) != len(manager) // PC_RECORD_SIZE:
        raise ValueError('Expected exactly 512 stock rows and candidate matching manager')
    changed = []
    for i in range(NATIVE_COUNT):
        expected = manager[i * PC_RECORD_SIZE:i * PC_RECORD_SIZE + 48].split(b'\0', 1)[0].decode('ascii')
        if native[i][0] != expected or mod[i][0] != expected:
            raise ValueError(f'Native/PC stock ordinal mismatch at {i}')
        before, after = native[i][1], mod[i][1]
        offsets = [j for j, (x, y) in enumerate(zip(before, after)) if x != y]
        if offsets:
            changed.append({'ordinal': i, 'name': expected,
                            'record_offsets': [NAME_SIZE + j for j in offsets],
                            'stock_data_sha256': hashlib.sha256(before).hexdigest(),
                            'candidate_data_sha256': hashlib.sha256(after).hexdigest()})
    extras = [{'ordinal': i, 'name': name, 'data_sha256': hashlib.sha256(data).hexdigest()}
              for i, (name, data) in enumerate(mod) if i >= NATIVE_COUNT]
    return {
        'status': 'STATIC_BYTE_COMPARISON',
        'stock_input_sha256': native_digest, 'candidate_input_sha256': mod_digest,
        'manager_sha256': companion['manager_sha256'],
        'stock_rows': len(native), 'candidate_rows': len(mod),
        'verified_shared_ordinals': NATIVE_COUNT,
        'changed_prefix_rows': changed, 'changed_prefix_row_count': len(changed),
        'stock_value_bytes_identical': len(changed) == 0,
        'appended_record_hashes': extras,
        'native_values_preserved': len(changed) == 0,
        'input_origin_verified': False,
        'field_semantics_verified': False,
        'effect_dependencies_verified': False,
        'runtime_precedence_verified': False,
        'gameplay_verified': False,
        'full_moddingapi': False,
        'ready_for_gameplay_test': False,
    }
