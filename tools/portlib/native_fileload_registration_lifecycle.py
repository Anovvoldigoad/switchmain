"""Read-only FileLoad registration helper and alternate-tail-call evidence.

The report is pinned to the exact Switch v1.70 original main. It records
relocations, bounded AArch64 CFGs and the three stored 64-bit record fields.
It does not infer callback/destructor identity or a native engine ABI.
"""
import hashlib
import struct

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileload_guard_state import (
    _adrp_add_target,
    _adrp_ldr_cell,
    _cell_evidence,
    _classify_range,
    inspect as inspect_guard_state,
)
from .native_fileload_imports import _decode_plt, _resolve_slot
from .native_fileload_registration_dispatch import inspect as inspect_dispatch
from .native_fileload_registration_target import (
    analyze_window,
    inspect as inspect_registration_target,
)
from .native_fileopen_import import _read_image, _tags


HELPER_START = 0x290
HELPER_END = 0x318
ABORT_PATH_START = 0x116D820
ABORT_PLT = 0x12F49B0
ERROR_CALLSITE = 0x116B864
ERROR_TARGET = 0x12155A0
ERROR_STRING_ADDRESS = 0x1AE9D22


def _hex(value):
    return "0x%x" % value


def _word(text, address):
    if (not isinstance(address, int) or address < 0 or (address & 3)
            or address + 4 > len(text)):
        raise ValueError("Unaligned or out-of-range AArch64 word")
    return struct.unpack_from("<I", text, address)[0]


def require_direct_branch(text, site, kind, target):
    if direct_branch(_word(text, site), site) != (kind, target):
        raise ValueError("Pinned direct branch changed at " + _hex(site))


def trace_bounded_window(text, start, window_bytes):
    if not isinstance(text, (bytes, bytearray, memoryview)):
        raise ValueError("AArch64 text must be bytes-like")
    if (not isinstance(start, int) or not isinstance(window_bytes, int)
            or start < 0 or (start & 3) or window_bytes <= 0
            or (window_bytes & 3) or start + window_bytes > len(text)):
        raise ValueError("Invalid bounded AArch64 analysis window")
    return analyze_window(text, start, start + window_bytes)


def decode_plt_thunk(text, pc):
    if (not isinstance(text, (bytes, bytearray, memoryview))
            or not isinstance(pc, int) or pc < 0 or (pc & 3)
            or pc + 16 > len(text)):
        raise ValueError("Invalid bounded PLT thunk")
    words = struct.unpack_from("<4I", text, pc)
    slot, _ = _decode_plt(text, pc, words)
    return {"got_slot": slot, "words": words}


def read_c_string(memory, address, region_start, region_end, max_bytes=512):
    if (not isinstance(address, int) or not isinstance(region_start, int)
            or not isinstance(region_end, int) or not isinstance(max_bytes, int)
            or max_bytes <= 0 or region_start < 0 or region_end > len(memory)
            or region_start >= region_end or not region_start <= address < region_end):
        raise ValueError("C-string address is outside its bounded source region")
    limit = min(region_end, address + max_bytes)
    end = memory.find(0, address, limit)
    if end < 0:
        raise ValueError("C-string terminator not found within bounded region")
    return bytes(memory[address:end])


def _instruction_map(cfg):
    return {row["pc"]: row for row in cfg["decoded_reachable_instructions"]}


def _require_instruction(rows, address, mnemonic):
    row = rows.get(_hex(address))
    if row is None or row["mnemonic"] != mnemonic:
        raise ValueError("Pinned instruction changed at " + _hex(address))
    return row


def _one_relative_target(cell):
    rows = cell["relocations"]
    if (len(rows) != 1 or rows[0]["type_name"] != "R_AARCH64_RELATIVE"
            or rows[0]["symbol_index"] != 0):
        raise ValueError("Expected one unambiguous R_AARCH64_RELATIVE cell")
    return rows[0]["addend"]


def _regions(nso, rows):
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
    return regions


def _cleanup_observations(text, cleanup_window):
    rows = _instruction_map(cleanup_window)
    for address, mnemonic in (
        (0x116B890, "mov"),
        (0x116B894, "adrp"),
        (0x116B898, "add"),
        (0x116B89C, "add"),
        (0x116B8A0, "ldr"),
        (0x116B8A4, "bl"),
        (0x116B8A8, "add"),
        (0x116B8AC, "cmp"),
        (0x116B8B0, "b.ne"),
        (0x116B8B4, "movi"),
        (0x116B8BC, "adrp"),
        (0x116B8C0, "add"),
    ):
        _require_instruction(rows, address, mnemonic)

    object_base = _adrp_add_target(text, 0x116B894, 20)
    table_base = _adrp_add_target(text, 0x116B8BC, 8)
    if table_base != object_base + 0x28 or table_base != 0x4371800:
        raise ValueError("Cleanup table base no longer follows object + 0x28")
    require_direct_branch(text, 0x116B8A4, "BL", 0x116B390)

    load = rows["0x116b8a0"]["memory_operands"]
    if (len(load) != 1 or load[0]["base_register"] != "x8"
            or load[0]["displacement"] != 0x28
            or load[0]["access_size_bytes"] != 8
            or load[0]["direction"] != "read"):
        raise ValueError("Cleanup pointer-slot load changed")

    increment = rows["0x116b8a8"]["operands"]
    limit = rows["0x116b8ac"]["operands"]
    loop_edges = rows["0x116b8b0"]["successors"]
    if "#8" not in increment or "#0x200" not in limit:
        raise ValueError("Cleanup loop increment or bound changed")
    if not any(edge["target"] == "0x116b89c"
               and edge["kind"] == "conditional" for edge in loop_edges):
        raise ValueError("Cleanup loop back-edge changed")

    clear_offsets = []
    for address in range(0x116B8C4, 0x116B904, 4):
        row = rows.get(_hex(address))
        if row is None or row["mnemonic"] != "stp":
            raise ValueError("Cleanup zero-store sequence changed at " + _hex(address))
        operands = row["memory_operands"]
        if (len(operands) != 1 or operands[0]["base_register"] != "x8"
                or operands[0]["access_size_bytes"] != 32
                or operands[0]["direction"] != "write"):
            raise ValueError("Cleanup zero-store width/base changed at " + _hex(address))
        clear_offsets.append(operands[0]["displacement"])
    expected_offsets = list(range(0x1E0, -1, -0x20))
    if clear_offsets != expected_offsets:
        raise ValueError("Cleanup zero-store offsets are not the pinned 0x200-byte range")

    return {
        "object_base": _hex(object_base),
        "slot_base": _hex(table_base),
        "slot_stride_bytes": 8,
        "slot_count": 0x200 // 8,
        "loop_increment": 8,
        "loop_limit_bytes": 0x200,
        "per_slot_direct_call": "0x116b390",
        "clear_store_sites": [_hex(x) for x in range(0x116B8C4, 0x116B904, 4)],
        "clear_store_offsets": [_hex(x) for x in clear_offsets],
        "clear_store_width_bytes": 32,
        "clear_covered_bytes": 0x200,
        "cleanup_or_destructor_identity_verified": False,
    }


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")

    guard = inspect_guard_state(nso)
    dispatch = inspect_dispatch(nso)
    registration = inspect_registration_target(nso)
    rows, memory = _read_image(nso)
    if len(rows) != 3 or rows[0][0] != 0:
        raise ValueError("Original NSO text layout changed")
    text = rows[0][1]
    tags = _tags(memory)
    regions = _regions(nso, rows)

    # The helper call is reached after the caller materializes three 64-bit values.
    require_direct_branch(text, 0x116B810, "BL", HELPER_START)
    helper = trace_bounded_window(text, HELPER_START, HELPER_END - HELPER_START)
    helper_rows = _instruction_map(helper)
    for address, mnemonic in (
        (0x290, "mov"),
        (0x2E0, "ldaxr"),
        (0x2E8, "stlxr"),
        (0x2EC, "cbnz"),
        (0x2F8, "mov"),
        (0x2FC, "madd"),
        (0x304, "stp"),
        (0x308, "str"),
        (0x30C, "ret"),
        (0x314, "ret"),
    ):
        _require_instruction(helper_rows, address, mnemonic)
    if helper["return_sites"] != ["0x30c", "0x314"]:
        raise ValueError("Registration helper return-site inventory changed")

    record_stp = helper_rows["0x304"]["memory_operands"]
    record_str = helper_rows["0x308"]["memory_operands"]
    if (len(record_stp) != 1 or record_stp[0]["base_register"] != "x9"
            or record_stp[0]["displacement"] != 0
            or record_stp[0]["access_size_bytes"] != 16
            or record_stp[0]["direction"] != "write"):
        raise ValueError("First two registration-record fields changed")
    if (len(record_str) != 1 or record_str[0]["base_register"] != "x9"
            or record_str[0]["displacement"] != 0x10
            or record_str[0]["access_size_bytes"] != 8
            or record_str[0]["direction"] != "write"):
        raise ValueError("Third registration-record field changed")

    helper_observed = guard["registration_helper_candidate"]["helper_observed"]
    register_setup = guard["registration_helper_candidate"]["register_setup"]
    code_cell = register_setup["x0"]["cell_evidence"]
    code_target = _one_relative_target(code_cell)
    if code_target != 0x116B888:
        raise ValueError("Registration code-pointer relocation changed")
    object_pointer = int(register_setup["x1"]["value_at_callsite"], 16)
    context_pointer = int(register_setup["x2"]["value_at_callsite"], 16)
    base_cell = helper_observed["table_base_pointer_cell"]
    limit_cell = helper_observed["table_limit_pointer_cell"]
    base_target = _one_relative_target(base_cell)
    limit_target = _one_relative_target(limit_cell)
    if base_target != limit_target:
        raise ValueError("Registration table base/limit relocation targets differ")
    if helper_observed["record_stride_bytes"] != 24:
        raise ValueError("Registration record stride changed")
    if helper_observed["atomic_counter_address"] != "0x21620d8":
        raise ValueError("Registration atomic counter address changed")

    cleanup = registration["target"]
    if cleanup["address"] != _hex(code_target):
        raise ValueError("Registered code pointer and analyzed target disagree")
    cleanup_observations = _cleanup_observations(text, cleanup["window"])

    # Alternate tail path: exact pointer cell -> PLT thunk -> dynamic symbol.
    abort_path = trace_bounded_window(text, ABORT_PATH_START, 0x40)
    abort_rows = _instruction_map(abort_path)
    for address, mnemonic in (
        (0x116D820, "cbz"),
        (0x116D824, "mov"),
        (0x116D828, "adrp"),
        (0x116D82C, "ldr"),
        (0x116D830, "b"),
        (0x116D834, "ret"),
    ):
        _require_instruction(abort_rows, address, mnemonic)
    require_direct_branch(text, 0x116D830, "B", ABORT_PLT)
    abort_cell, abort_register = _adrp_ldr_cell(
        text, 0x116D828, 0x116D82C, 0
    )
    if abort_register != 0 or abort_cell != 0x215D2E8:
        raise ValueError("Alternate tail pointer-cell materialization changed")
    abort_cell_evidence = _cell_evidence(memory, tags, abort_cell, regions)
    allocator_receiver = _one_relative_target(abort_cell_evidence)
    if allocator_receiver != 0x4371A00:
        raise ValueError("Alternate tail allocator receiver relocation changed")
    plt = decode_plt_thunk(text, ABORT_PLT)
    resolved = _resolve_slot(memory, tags, plt["got_slot"])
    if (resolved["resolution"] != "DYNAMIC_SYMBOL_NAME_RESOLVED"
            or not resolved["symbol"] or not resolved["symbol"].get("name")
            or resolved["symbol"]["name"] != "_ZN2nn3mem17StandardAllocator4FreeEPv"
            or not resolved["relocation"]
            or resolved["relocation"]["type_name"] != "R_AARCH64_JUMP_SLOT"):
        raise ValueError("Alternate tail is not the pinned StandardAllocator::Free import")
    if abort_rows["0x116d824"]["operands"] != "x1, x0":
        raise ValueError("Free argument is no longer copied from the alternate-path X0")
    alternate_source = dispatch["dispatch_flow"]["conditional_paths"]["alternate_path_x0_source"]
    if alternate_source != "x19":
        raise ValueError("Alternate-path Free argument no longer originates from X19")

    guard_object = guard["guarded_object_candidate"]
    if (guard_object["acquire_import"]["symbol"] != "__cxa_guard_acquire"
            or guard_object["release_import"]["symbol"] != "__cxa_guard_release"):
        raise ValueError("Static guard import pair changed")

    # The index-error path passes a bounded rodata literal to another direct target.
    require_direct_branch(text, ERROR_CALLSITE, "BL", ERROR_TARGET)
    literal_address = _adrp_add_target(text, 0x116B85C, 0)
    if literal_address != ERROR_STRING_ADDRESS:
        raise ValueError("Pinned FileLoad error literal address changed")
    rodata_start = rows[1][0]
    rodata_end = rows[1][0] + len(rows[1][1])
    literal = read_c_string(memory, literal_address, rodata_start, rodata_end)
    error_target = trace_bounded_window(text, ERROR_TARGET, 0x100)

    dispatch_traces = dispatch["bounded_target_traces"]
    required_dispatch = {"0x116b7b0", "0x116d380", "0x116b82c", "0x116d820"}
    if set(dispatch_traces) != required_dispatch:
        raise ValueError("Registration dispatch target inventory changed")

    return {
        "status": "PINNED_FILELOAD_REGISTRATION_LIFECYCLE_STATIC_TRACE_ONLY",
        "original_main_sha256": digest,
        "registration_helper": {
            "callsite": "0x116b810",
            "target": _hex(HELPER_START),
            "window": helper,
            "argument_candidates": {
                "field_0_code_pointer": {
                    "source_cell": code_cell["address"],
                    "relocation": code_cell["relocations"][0],
                    "target": _hex(code_target),
                    "target_region": "text",
                    "callback_or_destructor_identity_verified": False,
                },
                "field_1_object_pointer": {
                    "value": _hex(object_pointer),
                    "region": _classify_range(object_pointer, 1, regions),
                    "object_type_verified": False,
                },
                "field_2_context_pointer": {
                    "value": _hex(context_pointer),
                    "region": _classify_range(context_pointer, 1, regions),
                    "semantic_identity_verified": False,
                },
            },
            "record_layout": {
                "stride_bytes": 24,
                "index_source": "atomic counter load/increment",
                "field_writes": [
                    {"site": "0x304", "register": "x8", "offset": 0, "width": 8},
                    {"site": "0x304", "register": "x1", "offset": 8, "width": 8},
                    {"site": "0x308", "register": "x2", "offset": 0x10, "width": 8},
                ],
                "table_base_pointer_cell": base_cell,
                "table_limit_pointer_cell": limit_cell,
                "relocated_base_target": _hex(base_target),
                "relocated_limit_target": _hex(limit_target),
                "atomic_counter": helper_observed["atomic_counter_cell"],
                "table_runtime_values_verified": False,
                "registration_order_or_invocation_verified": False,
            },
        },
        "registered_code_pointer_target": {
            "address": cleanup["address"],
            "window": cleanup["window"],
            "cleanup_observations": cleanup_observations,
            "function_extent_verified": False,
            "destructor_identity_verified": False,
            "invocation_order_verified": False,
        },
        "guard_protocol": {
            "guard_address": guard_object["guard_address"],
            "static_object_address": guard_object["static_object_address"],
            "acquire_import": guard_object["acquire_import"],
            "release_import": guard_object["release_import"],
            "guard_runtime_state_verified": False,
        },
        "alternate_tail_import": {
            "path_window": abort_path,
            "branch_site": "0x116d830",
            "plt": _hex(ABORT_PLT),
            "plt_words_le": [text[ABORT_PLT + i:ABORT_PLT + i + 4].hex()
                             for i in (0, 4, 8, 12)],
            "got_slot": _hex(plt["got_slot"]),
            "relocation": resolved["relocation"],
            "symbol": resolved["symbol"],
            "resolved_import_role": "nn::mem::StandardAllocator::Free(void*)",
            "allocator_receiver_cell": abort_cell_evidence,
            "allocator_receiver_target": _hex(allocator_receiver),
            "argument_register_flow": {
                "alternate_path_source": alternate_source,
                "copy_site": "0x116d824",
                "copy_encoding": "mov x1, x0",
                "argument_value_type_verified": False,
            },
            "x0_value_at_runtime_verified": False,
            "tail_call_target_implementation_verified": False,
        },
        "index_error_path": {
            "callsite": _hex(ERROR_CALLSITE),
            "target": _hex(ERROR_TARGET),
            "literal_address": _hex(literal_address),
            "literal_region": "rodata",
            "literal_bytes_hex": literal.hex(),
            "literal_text": literal.decode("utf-8", errors="replace"),
            "target_window": error_target,
            "function_identity_verified": False,
        },
        "registration_dispatch_windows": dispatch_traces,
        "limits": {
            "callback_identity_verified": False,
            "destructor_identity_verified": False,
            "destructor_invocation_verified": False,
            "object_type_verified": False,
            "ownership_lifecycle_verified": False,
            "lock_unlock_semantics_verified": False,
            "async_behavior_verified": False,
            "rollback_unbind_verified": False,
            "native_consumer_abi_verified": False,
            "archive_precedence_verified": False,
            "native_hook_added": False,
            "gameplay_verified": False,
            "full_moddingapi": False,
            "ready_for_gameplay_test": False,
            "emulator_tested": False,
        },
    }


if __name__ == "__main__":
    raise SystemExit("Use tests/test_native_fileload_registration_lifecycle.py")
