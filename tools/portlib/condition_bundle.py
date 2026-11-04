"""Single-archive condition/profile integration; not a gameplay installer."""
import hashlib
from . import condition_profile, condition_companion, cpk_profile, cpk_events, nso_profile
ENTRY = 'data/spc/conditionprm.bin.xfbin'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compile_bundle(manager, archive, expected_sha256, runtime_path, priority, pc_api_prms):
    if sha(archive) != expected_sha256:
        raise ValueError('Input CPK SHA256 mismatch')
    registration = cpk_profile.encode([{'path': runtime_path, 'priority': priority}])
    table = cpk_events.entries(archive)
    if ENTRY not in table:
        raise ValueError('CPK lacks conditionprm companion')
    entry = table[ENTRY];start = entry['offset']
    raw = archive[start:start + entry['stored_size']]
    if entry['size'] != entry['stored_size'] or raw.startswith(b'CRILAYLA'):
        raise ValueError('Compressed condition companion requires verified repacking')
    pair = condition_companion.validate(manager, raw, sha(raw))
    profile, descriptor = condition_profile.compile_table(manager)
    if ENTRY in pc_api_prms:
        raise ValueError('Condition companion cannot be selected as a PC API moveset PRM')
    converted, events = (cpk_events.mark(archive, pc_api_prms) if pc_api_prms else
                         (archive, {'selected_prms': [], 'conversion_requested': False}))
    if cpk_events.entries(converted) != table or converted[start:start+len(raw)] != raw:
        raise ValueError('Companion or archive metadata changed during event conversion')
    report = {'source_cpk_sha256': sha(archive), 'output_cpk_sha256': sha(converted),
              'runtime_path': runtime_path, 'priority': priority, 'entry': ENTRY,
              'cpk_entry_id': entry['id'], 'cpk_entry_offset': start,
              'companion': pair, 'descriptor': descriptor, 'events': events,
              'condition_profile_sha256': sha(profile), 'cpk_profile_sha256': sha(registration),
              'archive_companion_bound_to_profile': True,
              'runtime_load_precedence_verified': False, 'gameplay_verified': False,
              'full_moddingapi': False, 'ready_for_gameplay_test': False}
    return converted, profile, registration, report


def _embedded_profile(data, magic, size, validator):
    """Read an existing validated profile without replacing its content."""
    if data.count(magic) != 1:
        raise ValueError('Expected exactly one embedded profile')
    at = data.index(magic)
    raw = data[at:at + size]
    validator(raw)
    return raw


def merge_cpk_registration(existing, requested):
    """Append one CPK without deleting earlier rows or guessing archive priority."""
    current = cpk_profile.decode(existing)
    new = cpk_profile.decode(requested)
    if len(new) != 1:
        raise ValueError('Single-archive bundle requires one requested CPK registration')
    target = new[0]
    for item in current:
        if item['path'].lower() == target['path'].lower():
            if item != target:
                raise ValueError('CPK path already configured with different case or priority')
            return existing  # identical registration, preserve exact bytes and ordering
        if item['priority'] == target['priority']:
            raise ValueError('CPK priority already allocated to another archive')
    if len(current) == cpk_profile.CAPACITY:
        raise ValueError('CPK profile capacity exhausted (32)')
    return cpk_profile.encode(current + new)


def configure_module(module, expected_sha256, condition, registration):
    if sha(module) != expected_sha256:
        raise ValueError('Input module SHA256 mismatch')
    data = nso_profile.segments(module)[2][1]
    old_condition = _embedded_profile(data, condition_profile.MAGIC,
                                      condition_profile.PROFILE_SIZE, condition_profile.decode)
    old_cpk = _embedded_profile(data, cpk_profile.MAGIC,
                                cpk_profile.PROFILE_SIZE, cpk_profile.decode)
    condition_profile.decode(condition)
    if condition_profile.decode(old_condition) and old_condition != condition:
        # Additional descriptors are ordinal-dependent: never replace or
        # concatenate two independently compiled condition tables.
        raise ValueError('Existing condition descriptors differ; supply one combined PC manager table')
    merged_cpk = merge_cpk_registration(old_cpk, registration)
    result, first = condition_profile.configure(module, condition, expected_sha256)
    result, second = cpk_profile.configure(result, merged_cpk, sha(result))
    return result, {'condition': first, 'cpk': second,
                    'previous_cpk_entries': len(cpk_profile.decode(old_cpk)),
                    'effective_cpk_entries': len(cpk_profile.decode(merged_cpk)),
                    'cpk_list_extended': merged_cpk != old_cpk,
                    'effective_cpk_profile_sha256': sha(merged_cpk),
                    'old_condition_descriptors_preserved_or_identical': True,
                    'runtime_load_precedence_verified': False,
                    'gameplay_verified': False,
                    'output_sha256': sha(result)}
