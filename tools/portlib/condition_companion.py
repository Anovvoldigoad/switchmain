"""Validate positional identity, not effect semantics, of raw176 companions."""
import hashlib
import re
import struct
from .condition_profile import compile_table, PC_RECORD_SIZE
from .prm_events import binary_chunks


def validate(manager, companion, expected_sha256):
    if not isinstance(expected_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('Expected explicit lowercase companion SHA256')
    digest = hashlib.sha256(companion).hexdigest()
    if digest != expected_sha256:
        raise ValueError('Raw condition companion SHA256 mismatch')
    # Includes pinned baseline, capacity and duplicate appended-name checks.
    _, report = compile_table(manager)
    chunks = binary_chunks(companion)
    if len(chunks) != 1 or chunks[0][0] != 'conditionprm':
        raise ValueError('Expected exactly one conditionprm binary chunk')
    _, start, size = chunks[0]
    if size < 8:
        raise ValueError('Truncated conditionprm count')
    count = struct.unpack_from('<I', companion, start + 4)[0]
    if count != len(manager) // PC_RECORD_SIZE or size != 8 + count * 176:
        raise ValueError('Descriptor/raw condition count or record length mismatch')
    names = []
    for i in range(count):
        raw_name = companion[start + 8 + i * 176:start + 8 + i * 176 + 64]
        if b'\0' not in raw_name:
            raise ValueError(f'Unterminated raw condition name at index {i}')
        name = raw_name.split(b'\0', 1)[0]
        expected = manager[i * PC_RECORD_SIZE:i * PC_RECORD_SIZE + 48].split(b'\0', 1)[0]
        if name != expected:
            raise ValueError(f'Descriptor/raw condition name mismatch at index {i}')
        names.append(name.decode('ascii'))
    return {
        'manager_sha256': report['input_sha256'], 'raw_xfbin_sha256': digest,
        'records': count, 'record_bytes': 176, 'ordinal_names_verified': count,
        'appended_names': names[512:], 'raw_bytes_modified': False,
        'raw_native_prefix_values_verified': False, 'effect_semantics_verified': False,
        'cpk_load_precedence_verified': False, 'gameplay_verified': False,
        'full_moddingapi': False,
    }
