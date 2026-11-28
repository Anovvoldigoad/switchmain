"""Read-only census of direct FileLoad-helper inbound sites and local preludes.

The output records raw aligned B/BL candidates and Capstone-confirmed branches.
The bounded prelude records last syntactic writes to X0-X7 only; it is not a
reaching-definition, function-boundary, parameter, or ABI proof.
"""
import hashlib
import json
import struct

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_IMM, ARM64_OP_MEM

from .native_cpk_graph import MAIN_SHA256
from .native_fileload_registration_target import _memory_access_width
from .native_fileload_table_access import scan_direct_b_bl_inbound
from .native_fileopen_import import _read_image

HELPER_TARGET = 0x116B390
PRELUDE_BYTES = 0x40
MAX_PRELUDE_BYTES = 0x100
ARGUMENT_REGISTER_CANDIDATES = tuple("x%d" % index for index in range(8))
KNOWN_TABLE_CALLS = {
    0x116B8A4: 0x116B8A0,
    0x116B928: 0x116B924,
}


def _hex(value):
    return "0x%x" % value


def _register_name(ins, register):
    if not register:
        return None
    name = ins.reg_name(register).lower()
    if name in {"wzr", "xzr"}:
        return "xzr"
    if name in {"wsp", "sp"}:
        return "sp"
    if name == "fp":
        return "x29"
    if name == "lr":
        return "x30"
    if name.startswith("w") and name[1:].isdigit():
        return "x" + name[1:]
    return name


def _decode_one(decoder, text, pc):
    if pc < 0 or pc + 4 > len(text) or (pc & 3):
        return None
    rows = list(decoder.disasm(bytes(text[pc:pc + 4]), pc, count=1))
    if len(rows) != 1 or rows[0].size != 4:
        return None
    return rows[0]


def _is_control_flow(ins):
    name = ins.mnemonic.lower()
    return (
        name in {
            "b", "bl", "br", "blr", "ret", "retaa", "retab", "eret",
            "cbz", "cbnz", "tbz", "tbnz",
        }
        or name.startswith("b.")
    )


def _instruction_record(ins, text, pc):
    try:
        reads, writes = ins.regs_access()
        register_access_supported = True
    except Exception:
        reads, writes = [], []
        register_access_supported = False

    read_names = sorted({
        _register_name(ins, value) for value in reads
    } - {None})
    written_names = sorted({
        _register_name(ins, value) for value in writes
    } - {None})

    memory = []
    immediates = []
    for index, operand in enumerate(ins.operands):
        if operand.type == ARM64_OP_MEM:
            width, width_source = _memory_access_width(ins)
            memory.append({
                "operand_index": index,
                "base_register": _register_name(ins, operand.mem.base),
                "index_register": _register_name(ins, operand.mem.index),
                "displacement": operand.mem.disp,
                "width_bytes": width,
                "width_source": width_source,
                "direction": (
                    "write" if ins.mnemonic.lower().startswith("st")
                    else "read" if ins.mnemonic.lower().startswith("ld")
                    else "unknown"
                ),
                "writeback": bool(getattr(ins, "writeback", False)),
            })
        elif operand.type == ARM64_OP_IMM:
            immediates.append({"operand_index": index, "value": int(operand.imm)})

    return {
        "pc": _hex(pc),
        "word_le": bytes(text[pc:pc + 4]).hex(),
        "mnemonic": ins.mnemonic.lower(),
        "operands": ins.op_str,
        "read_registers": read_names,
        "written_registers": written_names,
        "memory_operands": memory,
        "immediates": immediates,
        "register_access_supported": register_access_supported,
    }


def _signature_shape(last_writes):
    shape = {}
    for register in ARGUMENT_REGISTER_CANDIDATES:
        row = last_writes.get(register)
        if row is None:
            shape[register] = None
            continue
        shape[register] = {
            "mnemonic": row["mnemonic"],
            "read_registers": row["read_registers"],
            "memory_operands": [
                {
                    "base_register": item["base_register"],
                    "index_register": item["index_register"],
                    "displacement": item["displacement"],
                    "width_bytes": item["width_bytes"],
                    "direction": item["direction"],
                }
                for item in row["memory_operands"]
            ],
            "immediates": row["immediates"],
        }
    return shape


def classify_callsite(text, site, target, prelude_bytes=PRELUDE_BYTES, decoder=None):
    """Describe one exact direct B/BL and its bounded preceding instruction bytes."""
    if not isinstance(text, (bytes, bytearray, memoryview)):
        raise ValueError("AArch64 text must be bytes-like")
    if (
        not isinstance(site, int) or not isinstance(target, int)
        or site < 0 or target < 0 or (site & 3) or (target & 3)
        or site + 4 > len(text)
    ):
        raise ValueError("Invalid aligned direct-branch site or target")
    if (
        not isinstance(prelude_bytes, int) or prelude_bytes < 0
        or (prelude_bytes & 3) or prelude_bytes > MAX_PRELUDE_BYTES
    ):
        raise ValueError("Invalid bounded prelude length")

    word = struct.unpack_from("<I", text, site)[0]
    opcode = word & 0xFC000000
    if opcode not in (0x94000000, 0x14000000):
        raise ValueError("Candidate is not an AArch64 direct B/BL word")
    immediate = word & 0x03FFFFFF
    if immediate & (1 << 25):
        immediate -= 1 << 26
    decoded_target = site + (immediate << 2)
    if decoded_target != target:
        raise ValueError("Direct B/BL target differs from the requested helper")

    own_decoder = decoder is None
    if decoder is None:
        decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        decoder.detail = True
    branch_ins = _decode_one(decoder, text, site)
    expected_mnemonic = "bl" if opcode == 0x94000000 else "b"
    if (
        branch_ins is None or branch_ins.mnemonic.lower() != expected_mnemonic
        or not branch_ins.operands or branch_ins.operands[0].type != ARM64_OP_IMM
        or int(branch_ins.operands[0].imm) != target
    ):
        raise ValueError("Capstone did not confirm the exact direct B/BL target")

    start = max(0, site - prelude_bytes)
    start &= ~3
    last_writes = {}
    prelude = []
    decode_gaps = []
    control_flow_sites = []

    for pc in range(start, site, 4):
        ins = _decode_one(decoder, text, pc)
        if ins is None:
            decode_gaps.append(_hex(pc))
            last_writes.clear()
            prelude.append({"pc": _hex(pc), "decode_status": "undecodable_word"})
            continue

        row = _instruction_record(ins, text, pc)
        prelude.append(row)
        if _is_control_flow(ins):
            control_flow_sites.append({
                "site": row["pc"],
                "mnemonic": row["mnemonic"],
                "operands": row["operands"],
            })
        for register in row["written_registers"]:
            if register in ARGUMENT_REGISTER_CANDIDATES:
                last_writes[register] = row

    signature = _signature_shape(last_writes)
    signature_bytes = json.dumps(
        signature, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    signature_sha256 = hashlib.sha256(signature_bytes).hexdigest()

    return {
        "site": _hex(site),
        "branch_kind": expected_mnemonic.upper(),
        "target": _hex(target),
        "branch_word_le": bytes(text[site:site + 4]).hex(),
        "capstone_confirmed": True,
        "prelude_start": _hex(start),
        "prelude_end_exclusive": _hex(site),
        "prelude_bytes": site - start,
        "prelude_sha256": hashlib.sha256(bytes(text[start:site])).hexdigest(),
        "prelude_instruction_count": len(prelude) - len(decode_gaps),
        "prelude": prelude,
        "decode_gaps": decode_gaps,
        "control_flow_sites": control_flow_sites,
        "last_syntactic_writes_to_x0_x7": {
            register: last_writes.get(register)
            for register in ARGUMENT_REGISTER_CANDIDATES
        },
        "signature_shape": signature,
        "signature_sha256": signature_sha256,
        "architectural_argument_register_candidates_only": True,
        "last_writes_are_not_proven_reaching_definitions": True,
        "path_continuity_proven": False,
        "function_extent_verified": False,
    }


def _verify_known_table_call(callers_by_site, call_site, load_site):
    row = callers_by_site.get(_hex(call_site))
    if row is None or row["branch_kind"] != "BL":
        raise ValueError("Known table-path helper BL is missing at " + _hex(call_site))
    definition = row["last_syntactic_writes_to_x0_x7"]["x0"]
    if (
        definition is None or definition["pc"] != _hex(load_site)
        or definition["mnemonic"] != "ldr"
    ):
        raise ValueError("Known table-path X0 load changed at " + _hex(load_site))
    matches = [
        item for item in definition["memory_operands"]
        if item["base_register"] == "x8"
        and item["index_register"] is None
        and item["displacement"] == 0x28
        and item["width_bytes"] == 8
        and item["direction"] == "read"
    ]
    if len(matches) != 1:
        raise ValueError("Known table-path X0 source is not one 64-bit X8+0x28 load")
    return {
        "call_site": row["site"],
        "call_target": row["target"],
        "load_site": definition["pc"],
        "load_word_le": definition["word_le"],
        "load_mnemonic": definition["mnemonic"],
        "load_operands": definition["operands"],
        "memory_operand": matches[0],
        "value_type_verified": False,
        "function_extent_verified": False,
    }


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")

    rows, _memory = _read_image(nso)
    if len(rows) != 3 or rows[0][0] != 0:
        raise ValueError("Original NSO text layout changed")
    text = rows[0][1]
    raw_candidates = scan_direct_b_bl_inbound(text, HELPER_TARGET)
    if not raw_candidates:
        raise ValueError("No raw aligned direct B/BL candidates target the FileLoad helper")

    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    callers = []
    unconfirmed = []
    for candidate in raw_candidates:
        site = int(candidate["site"], 16)
        try:
            callers.append(classify_callsite(
                text, site, HELPER_TARGET, PRELUDE_BYTES, decoder
            ))
        except ValueError as exc:
            unconfirmed.append({
                **candidate,
                "word_le": bytes(text[site:site + 4]).hex(),
                "capstone_confirmation_error": str(exc),
            })

    callers_by_site = {row["site"]: row for row in callers}
    known_table_calls = [
        _verify_known_table_call(callers_by_site, call_site, load_site)
        for call_site, load_site in sorted(KNOWN_TABLE_CALLS.items())
    ]

    clusters = {}
    branch_kind_counts = {"BL": 0, "B": 0}
    for row in callers:
        branch_kind_counts[row["branch_kind"]] += 1
        key = row["signature_sha256"]
        group = clusters.setdefault(key, {
            "signature_sha256": key,
            "signature_shape": row["signature_shape"],
            "count": 0,
            "branch_kind_counts": {"BL": 0, "B": 0},
            "sites": [],
        })
        group["count"] += 1
        group["branch_kind_counts"][row["branch_kind"]] += 1
        group["sites"].append(row["site"])

    ordered_clusters = sorted(
        clusters.values(), key=lambda row: (-row["count"], row["signature_sha256"])
    )
    return {
        "status": "PINNED_FILELOAD_HELPER_INBOUND_CALLER_CENSUS_STATIC_ONLY",
        "original_main_sha256": digest,
        "text_sha256": hashlib.sha256(text).hexdigest(),
        "text_bytes": len(text),
        "helper_target": _hex(HELPER_TARGET),
        "raw_aligned_direct_b_bl_inbound_count": len(raw_candidates),
        "prelude_bytes_per_caller": PRELUDE_BYTES,
        "capstone_confirmed_direct_branch_count": len(callers),
        "capstone_unconfirmed_raw_candidates": unconfirmed,
        "branch_kind_counts": branch_kind_counts,
        "known_table_path_helper_calls": known_table_calls,
        "callers": callers,
        "signature_clusters": ordered_clusters,
        "scope": {
            "raw_scan_covers_every_aligned_text_word": True,
            "raw_scan_only_recognizes_direct_B_and_BL": True,
            "capstone_confirms_each_reported_branch_instruction": True,
            "prelude_is_fixed_0x40_byte_linear_window": True,
            "prelude_last_writes_are_syntactic_not_reaching_definitions": True,
            "control_flow_sites_are_reported_not_followed": True,
            "indirect_branches_and_conditional_inbound_edges_not_scanned": True,
            "function_extents_are_not_inferred": True,
            "register_values_and_object_types_are_not_inferred": True,
        },
        "limits": {
            "producer_identity_verified": False,
            "table_writer_identity_verified": False,
            "br_x2_target_resolved": False,
            "callback_identity_verified": False,
            "destructor_identity_verified": False,
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
    raise SystemExit("Use tests/test_native_fileload_helper_callers.py")
