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


def configure_module(module, expected_sha256, condition, registration):
    if sha(module) != expected_sha256:
        raise ValueError('Input module SHA256 mismatch')
    # Single-archive scope: never silently discard another registration list.
    data = nso_profile.segments(module)[2][1]
    if data.count(cpk_profile.MAGIC) != 1:
        raise ValueError('Expected one CPK profile')
    at = data.index(cpk_profile.MAGIC)
    old = cpk_profile.decode(data[at:at+cpk_profile.PROFILE_SIZE])
    requested = cpk_profile.decode(registration)
    if old and old != requested:
        raise ValueError('Existing CPK registrations differ; multi-archive merge is not verified')
    result, first = condition_profile.configure(module, condition, expected_sha256)
    result, second = cpk_profile.configure(result, registration, sha(result))
    return result, {'condition': first, 'cpk': second, 'output_sha256': sha(result)}
