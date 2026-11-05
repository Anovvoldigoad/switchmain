"""Read paired hash-pinned CPK conditionprm entries and audit their raw176 values.

No CPK priority, load completion, source provenance or effect semantics is inferred.
"""
import hashlib
import mmap
import re
from contextlib import ExitStack
from pathlib import Path
from . import cpk_events
from .condition_bundle import ENTRY
from .condition_raw_audit import compare


def _get_companion(source, expected_sha, stack):
    if not isinstance(expected_sha, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_sha):
        raise ValueError('Require a lowercase 64-character CPK SHA256')
    path = Path(source)
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing or symlinked CPK')
    f = stack.enter_context(path.open('rb'))
    if path.stat().st_size == 0:
        raise ValueError('Empty CPK')
    blob = stack.enter_context(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ))
    actual = hashlib.sha256(blob).hexdigest()
    if actual != expected_sha:
        raise ValueError('CPK SHA256 mismatch: '+str(path))
    table = cpk_events.entries(blob)
    if ENTRY not in table:
        raise ValueError('CPK does not contain data/spc/conditionprm.bin.xfbin')
    row = table[ENTRY]
    start = row['offset']
    n = row['stored_size']
    if n != row['size'] or blob[start:start+8] == b'CRILAYLA':
        raise ValueError('Compressed conditionprm requires separately audited decoder')
    raw = blob[start:start+n]
    return raw, {
        'source':str(path), 'cpk_sha256':actual,
        'cpk_entry':ENTRY, 'cpk_entry_id':row['id'],
        'cpk_entry_offset':start,'raw_xfbin_sha256':hashlib.sha256(raw).hexdigest(),
        'raw_bytes':len(raw)}


def inspect(manager, stock_cpk, stock_sha, candidate_cpk, candidate_sha):
    with ExitStack() as stack:
        stock, stock_meta = _get_companion(stock_cpk, stock_sha, stack)
        candidate, cand_meta = _get_companion(candidate_cpk, candidate_sha, stack)
        report = compare(manager, stock, stock_meta['raw_xfbin_sha256'],
                         candidate, cand_meta['raw_xfbin_sha256'])
    report.update({
        'stock_archive':stock_meta,'candidate_archive':cand_meta,
        'stock_archive_claim_is_not_authenticated_provenance':True,
        'cpk_archive_winner_verified':False,
        'gameplay_verified':False,'full_moddingapi':False,
        'ready_for_gameplay_test':False})
    return report
