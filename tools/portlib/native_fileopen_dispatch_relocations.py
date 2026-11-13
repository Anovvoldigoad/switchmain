"""Read-only original-main relocation pairs at two FileOpen dispatch offsets.

An executable RELATIVE relocation at base+offset is only a candidate
function pointer; it does not authenticate the runtime X8 base or a vtable.
"""
import hashlib
import json
from .native_cpk_graph import MAIN_SHA256
from .native_cpk_indirect import _image_and_relocations, RELA_TYPE
from .native_fileopen_dispatch_objects import DISPATCHES

def candidate_pairs(records, text_end, offset):
    if type(offset) is not int or offset < 0 or offset % 8:
        raise ValueError("Unaligned or invalid dispatch offset")
    if type(text_end) is not int or text_end < 4:
        raise ValueError("Invalid executable extent")
    slots = {}
    for slot, kind, addend in records:
        if kind != RELA_TYPE:
            continue
        if slot < 0 or slot % 8 or slot in slots:
            raise ValueError("Duplicate or unaligned RELATIVE relocation")
        slots[slot] = addend
    result = []
    for slot, target in sorted(slots.items()):
        base = slot-offset
        if base < 0 or base % 8 or not (0 <= target < text_end and target % 4 == 0):
            continue
        # A static pointer at base+offset alone is not evidence that X8
        # ever holds base. Require an independently relocated base slot.
        if base not in slots:
            continue
        result.append({"candidate_base":hex(base),
                       "method_slot":hex(slot),
                       "method_target":hex(target),
                       "base_slot_relocation_addend":hex(slots[base])})
    return result

def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    rows, records = _image_and_relocations(nso)
    if rows[0][0] != 0:
        raise ValueError("Unexpected original text base")
    text_end = len(rows[0][1])
    dispatch = []
    for witness in DISPATCHES:
        offset = witness["offset"]
        matches = candidate_pairs(records, text_end, offset)
        fingerprint = hashlib.sha256(json.dumps(matches,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        dispatch.append({"original_load":hex(witness["load"]),
                         "original_branch":hex(witness["branch"]),
                         "observed_indirect_field_offset":offset,
                         "static_relocation_pair_candidates_sample":matches[:8],
                         "all_candidate_pairs_sha256":fingerprint,
                         "candidate_sample_truncated":len(matches)>8,
                         "candidate_count":len(matches),
                         "runtime_x8_base_matched_to_candidate":False})
    return {"status":"PINNED_FILEOPEN_DISPATCH_RELOCATION_PAIR_CENSUS",
            "original_main_sha256":digest,
            "relocation_records_examined":len(records),
            "dispatches":dispatch,
            "static_pairs_do_not_prove_object_identity":True,
            "native_consumer_abi_proven":False,
            "ownership_async_unbind_destructor_proven":False,
            "archive_precedence_proven":False,
            "new_runtime_hook":False,
            "full_moddingapi":False,
            "ready_for_gameplay_test":False,
            "emulator_tested":False}
