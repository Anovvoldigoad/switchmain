"""Pinned FileLoad static-guard and registration-table evidence.

This traces only original-main instruction/relocation facts. It does not identify
the helper at 0x290, imported implementations, callback semantics, ownership,
or a native consumer ABI.
"""
import hashlib
import struct

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileopen_import import _read_image, _scan_relocations, _tags
from .native_fileload_imports import inspect as inspect_imports


def _word(text, at):
    if at < 0 or at + 4 > len(text) or at & 3:
        raise ValueError("Instruction address outside aligned original text")
    return struct.unpack_from("<I", text, at)[0]


def _require_word(text, at, expected):
    actual = _word(text, at)
    if actual != expected:
        raise ValueError("Pinned instruction changed at " + hex(at))
    return actual


def _decode_adrp_page(word, pc):
    if word & 0x9F000000 != 0x90000000 or pc < 0 or pc & 3:
        raise ValueError("Expected aligned AArch64 ADRP")
    immlo = (word >> 29) & 3
    immhi = (word >> 5) & 0x7FFFF
    imm21 = (immhi << 2) | immlo
    if imm21 & (1 << 20):
        imm21 -= 1 << 21
    return (pc & ~0xFFF) + (imm21 << 12), word & 31


def _decode_adrp_add_words(pc, adrp_word, add_word, expected_register=None):
    page, adrp_rd = _decode_adrp_page(adrp_word, pc)
    if add_word & 0xFF000000 != 0x91000000:
        raise ValueError("Expected 64-bit ADD-immediate after ADRP")
    rd = add_word & 31
    rn = (add_word >> 5) & 31
    imm12 = (add_word >> 10) & 0xFFF
    shift = (add_word >> 22) & 1
    if shift or rd != adrp_rd or rn != adrp_rd:
        raise ValueError("ADRP/ADD register or shift chain is inconsistent")
    if expected_register is not None and rd != expected_register:
        raise ValueError("ADRP/ADD destination register changed")
    return page + imm12


def _adrp_add_target(text, pc, expected_register):
    return _decode_adrp_add_words(
        pc, _word(text, pc), _word(text, pc + 4), expected_register
    )


def _decode_adrp_ldr_words(pc, adrp_word, ldr_word, expected_base_register):
    page, adrp_rd = _decode_adrp_page(adrp_word, pc)
    if ldr_word & 0xFFC00000 != 0xF9400000:
        raise ValueError("Expected 64-bit unsigned-offset LDR after ADRP")
    rt = ldr_word & 31
    rn = (ldr_word >> 5) & 31
    imm12 = (ldr_word >> 10) & 0xFFF
    if rn != adrp_rd or rn != expected_base_register:
        raise ValueError("ADRP/LDR base register changed")
    return page + imm12 * 8, rt


def _adrp_ldr_cell(text, adrp_pc, ldr_pc, expected_base_register):
    # ADRP and its consuming LDR need not be adjacent; intervening instructions
    # may use other registers while preserving the page register.
    return _decode_adrp_ldr_words(
        adrp_pc, _word(text, adrp_pc), _word(text, ldr_pc), expected_base_register
    )


def _classify_range(address, width, regions):
    if not isinstance(address, int) or address < 0:
        raise ValueError("Image address must be a non-negative integer")
    if not isinstance(width, int) or width <= 0:
        raise ValueError("Image range width must be positive")
    end = address + width
    for name, start, limit in regions:
        if start <= address and end <= limit:
            return name
    if any(address < limit and end > start for _, start, limit in regions):
        return "crosses_image_region_boundary"
    return "outside_main_image"


def _cell_evidence(memory, tags, address, regions):
    if address < 0 or address + 8 > len(memory):
        raise ValueError("Pointer cell outside original mapped image")
    relocations = _scan_relocations(memory, tags, address)
    value = struct.unpack_from("<Q", memory, address)[0]
    return {
        "address": hex(address),
        "region": _classify_range(address, 8, regions),
        "raw_u64": hex(value),
        "raw_value_region": (_classify_range(value, 1, regions)
                             if value else "zero"),
        "relocation_status": ("none" if not relocations
                              else "one_record" if len(relocations) == 1
                              else "ambiguous_multiple_records"),
        "relocations": relocations,
        "runtime_relocated_value_verified": False,
    }


def _require_branch(text, site, target):
    if direct_branch(_word(text, site), site) != ("BL", target):
        raise ValueError("Pinned direct BL changed at " + hex(site))


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    rows, memory = _read_image(nso)
    if len(rows) != 3 or rows[0][0] != 0:
        raise ValueError("Original NSO segment layout changed")
    text = rows[0][1]
    bss_size = struct.unpack_from("<I", nso, 60)[0]
    bss_start = rows[2][0] + len(rows[2][1])
    bss_end = bss_start + bss_size
    regions = [
        ("text", rows[0][0], rows[0][0] + len(rows[0][1])),
        ("rodata", rows[1][0], rows[1][0] + len(rows[1][1])),
        ("data", rows[2][0], rows[2][0] + len(rows[2][1])),
    ]
    if bss_size:
        regions.append(("bss", bss_start, bss_end))

    guard_from_flag_load = _adrp_add_target(text, 0x116B7B4, 8)
    guard_from_guard_call = _adrp_add_target(text, 0x116B7D4, 19)
    object_from_early_return = _adrp_add_target(text, 0x116B7C4, 0)
    object_from_late_return = _adrp_add_target(text, 0x116B81C, 0)
    if guard_from_flag_load != guard_from_guard_call:
        raise ValueError("Guard-byte and guard-call addresses disagree")
    if object_from_early_return != object_from_late_return:
        raise ValueError("Early/late X0 object-address materializations disagree")
    if object_from_early_return != guard_from_guard_call + 8:
        raise ValueError("Static object address is not guard address + 8")

    expected_words = {
        0x116B7BC: 0x08DFFD08,  # ldarb w8, [x8]
        0x116B7C0: 0x360000A8,  # tbz w8, #0, 0x116b7d4
        0x116B7CC: 0xA8C14FFE,  # ldp x30, x19, [sp], #0x10
        0x116B7DC: 0xAA1303E0,  # mov x0, x19
        0x116B7EC: 0xAA1303E1,  # mov x1, x19
        0x116B7F4: 0xF8008C28,  # str x8, [x1, #8]!
        0x116B7F8: 0xA9012668,  # stp x8, x9, [x19, #0x10]
        0x116B800: 0xF900127F,  # str xzr, [x19, #0x20]
        0x116B804: 0xF9415800,  # ldr x0, [x0, #0x2b0]
        0x116B80C: 0x91000042,  # add x2, x2, #0
        0x116B814: 0xAA1303E0,  # mov x0, x19
        0x116B824: 0xA8C14FFE,  # ldp x30, x19, [sp], #0x10
        0x116B828: 0xD65F03C0,  # ret
        0x0290: 0xAA0003E8,     # mov x8, x0
        0x02E0: 0xC85FFD8B,     # ldaxr x11, [x12]
        0x02E8: 0xC80EFD8D,     # stlxr w14, x13, [x12]
        0x02EC: 0x35FFFFAE,     # cbnz w14, 0x2e0
        0x02F8: 0x5280030A,     # mov w10, #0x18
        0x02FC: 0x9B0A2569,     # madd x9, x11, x10, x9
        0x0304: 0xA9000528,     # stp x8, x1, [x9]
        0x0308: 0xF9000922,     # str x2, [x9, #0x10]
        0x030C: 0xD65F03C0,     # ret
        0x0314: 0xD65F03C0,     # ret
    }
    for address, word in expected_words.items():
        _require_word(text, address, word)
    _require_branch(text, 0x116B7E0, 0x12F3690)
    _require_branch(text, 0x116B810, 0x00000290)
    _require_branch(text, 0x116B818, 0x12F36A0)

    imports_report = inspect_imports(nso)
    imports = imports_report["imports"]
    acquire = imports["fileload_nested_import_0x116b7e0"]
    release = imports["fileload_nested_import_0x116b818"]
    if (acquire["resolution"] != "DYNAMIC_SYMBOL_NAME_RESOLVED"
            or acquire["symbol"]["name"] != "__cxa_guard_acquire"):
        raise ValueError("Original guard-acquire dynamic symbol changed")
    if (release["resolution"] != "DYNAMIC_SYMBOL_NAME_RESOLVED"
            or release["symbol"]["name"] != "__cxa_guard_release"):
        raise ValueError("Original guard-release dynamic symbol changed")

    explicit_stores = [
        {
            "site": "0x116b7f4", "encoding": "str x8, [x1, #8]!",
            "base_origin": "x1 copied from x19 at 0x116b7ec",
            "address": hex(guard_from_guard_call + 8),
            "width": 8,
            "region": _classify_range(guard_from_guard_call + 8, 8, regions),
        },
        {
            "site": "0x116b7f8", "encoding": "stp x8, x9, [x19, #0x10]",
            "base_origin": "x19 materialized by ADRP+ADD at 0x116b7d4/0x116b7d8",
            "address": hex(guard_from_guard_call + 0x10),
            "width": 16,
            "region": _classify_range(guard_from_guard_call + 0x10, 16, regions),
        },
        {
            "site": "0x116b800", "encoding": "str xzr, [x19, #0x20]",
            "base_origin": "x19 materialized by ADRP+ADD at 0x116b7d4/0x116b7d8",
            "address": hex(guard_from_guard_call + 0x20),
            "width": 8,
            "region": _classify_range(guard_from_guard_call + 0x20, 8, regions),
        },
    ]
    object_extent_region = _classify_range(object_from_early_return, 0x20, regions)

    registration_arg_cell, registration_arg_register = _adrp_ldr_cell(
        text, 0x116B7FC, 0x116B804, 0
    )
    registration_context = _adrp_add_target(text, 0x116B808, 2)
    counter_load_cell, counter_load_register = _adrp_ldr_cell(
        text, 0x029C, 0x02A8, 10
    )
    counter_update_cell = _adrp_add_target(text, 0x02D8, 12)
    table_base_cell, table_base_register = _adrp_ldr_cell(
        text, 0x02A0, 0x02A4, 9
    )
    table_limit_cell, table_limit_register = _adrp_ldr_cell(
        text, 0x02AC, 0x02B4, 10
    )
    if counter_load_cell != counter_update_cell:
        raise ValueError("Atomic counter load/update addresses disagree")
    if (registration_arg_register != 0 or counter_load_register != 11
            or table_base_register != 9 or table_limit_register != 10):
        raise ValueError("Pinned registration-helper load destination changed")

    tags = _tags(memory)
    cells = {
        "registration_value": _cell_evidence(memory, tags, registration_arg_cell, regions),
        "table_base_pointer": _cell_evidence(memory, tags, table_base_cell, regions),
        "table_limit_pointer": _cell_evidence(memory, tags, table_limit_cell, regions),
        "atomic_counter": _cell_evidence(memory, tags, counter_update_cell, regions),
    }
    all_explicit_stores_in_bss = (
        bool(explicit_stores)
        and all(row["region"] == "bss" for row in explicit_stores)
        and object_extent_region == "bss"
    )
    return {
        "status": "SHA_PINNED_FILELOAD_STATIC_GUARD_AND_REGISTRATION_EVIDENCE_ONLY",
        "original_main_sha256": digest,
        "original_main_bss": {
            "start": hex(bss_start), "end_exclusive": hex(bss_end),
            "size": bss_size,
        },
        "guarded_object_candidate": {
            "guard_address": hex(guard_from_guard_call),
            "guard_region": _classify_range(guard_from_guard_call, 1, regions),
            "guard_byte_load_site": "0x116b7bc",
            "guard_byte_load_word_le": text[0x116B7BC:0x116B7C0].hex(),
            "acquire_import": {
                "callsite": acquire["callsite"], "plt": acquire["plt"],
                "got_slot": acquire["got_slot"],
                "relocation": acquire["relocation"],
                "symbol": acquire["symbol"]["name"],
                "argument_register_setup": "mov x0, x19 at 0x116b7dc",
                "argument_register_value": hex(guard_from_guard_call),
            },
            "release_import": {
                "callsite": release["callsite"], "plt": release["plt"],
                "got_slot": release["got_slot"],
                "relocation": release["relocation"],
                "symbol": release["symbol"]["name"],
                "argument_register_setup": "mov x0, x19 at 0x116b814",
                "argument_register_value": hex(guard_from_guard_call),
            },
            "static_object_address": hex(object_from_early_return),
            "static_object_region": _classify_range(object_from_early_return, 1, regions),
            "early_return_x0_address": hex(object_from_early_return),
            "late_return_x0_address": hex(object_from_late_return),
            "object_extent": {
                "start": hex(object_from_early_return),
                "end_exclusive": hex(object_from_early_return + 0x20),
                "width": 0x20,
                "region": object_extent_region,
            },
            "explicit_stores": explicit_stores,
            "explicit_stores_all_in_bss": all_explicit_stores_in_bss,
        },
        "registration_helper_candidate": {
            "callsite": "0x116b810",
            "target": "0x290",
            "target_window": {
                "start": "0x290", "end_exclusive": "0x318",
                "sha256": hashlib.sha256(text[0x290:0x318]).hexdigest(),
                "bounded_window_not_function_extent": True,
            },
            "register_setup": {
                "x0": {"source": "64-bit load from pointer cell",
                       "cell": hex(registration_arg_cell),
                       "cell_evidence": cells["registration_value"]},
                "x1": {"source": "pre-index STR writeback from x19 + 8",
                       "value_at_callsite": hex(object_from_early_return)},
                "x2": {"source": "ADRP+ADD",
                       "value_at_callsite": hex(registration_context)},
            },
            "helper_observed": {
                "atomic_counter_address": hex(counter_update_cell),
                "atomic_counter_cell": cells["atomic_counter"],
                "table_base_pointer_cell": cells["table_base_pointer"],
                "table_limit_pointer_cell": cells["table_limit_pointer"],
                "atomic_increment_sites": ["0x2e0", "0x2e8", "0x2ec"],
                "record_stride_bytes": 24,
                "stride_source": "mov w10, #0x18 at 0x2f8; madd x9, x11, x10, x9 at 0x2fc",
                "stored_value_registers": ["x8", "x1", "x2"],
                "record_store_sites": ["0x304", "0x308"],
                "return_sites": ["0x30c", "0x314"],
                "table_pointer_values_runtime_resolved": False,
                "semantic_identity_verified": False,
                "callback_identity_verified": False,
                "destructor_identity_verified": False,
                "function_extent_verified": False,
            },
        },
        "stack_and_abi_limits": {
            "explicit_guarded_object_stores_proven_in_main_bss": all_explicit_stores_in_bss,
            "explicit_guarded_object_stores_use_sp_relative_base": False,
            "explicit_bss_stores_do_not_address_parent_entry_sp_minus_8": all_explicit_stores_in_bss,
            "opaque_guard_import_side_effects_resolved": False,
            "registration_helper_table_target_resolved": False,
            "parent_x19_stack_preservation_proven": False,
            "native_consumer_abi_verified": False,
            "ownership_lifecycle_async_rollback_unbind_destructor_verified": False,
            "archive_precedence_verified": False,
            "safe_new_hook_abi_proven": False,
            "native_hook_added": False,
            "gameplay_verified": False,
            "full_moddingapi": False,
            "ready_for_gameplay_test": False,
            "emulator_tested": False,
        },
    }


if __name__ == "__main__":
    raise SystemExit("Use tests/test_native_fileload_guard_state.py")
