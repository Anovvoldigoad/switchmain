"""Read-only direct-reference census for the 64-slot FileLoad table.

This follows only ADRP-derived addresses within bounded linear instruction windows.
It does not resolve arbitrary pointer aliases, infer C++ object layout, or identify
a callback/destructor/consumer ABI.
"""
import hashlib
import struct

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG

from .native_cpk_graph import MAIN_SHA256
from .native_fileload_guard_state import _decode_adrp_page
from .native_fileload_registration_target import _memory_access_width
from .native_fileopen_import import _read_image, _tags

TABLE_START = 0x4371800
TABLE_END = 0x4371A00
TABLE_PAGE = TABLE_START & ~0xFFF
WINDOW_BYTES = 0x100
CLEANUP_START = 0x116B8C4
CLEANUP_END = 0x116B904


def _hex(value):
    return "0x%x" % value


def _reg_name(ins, register):
    if not register:
        return None
    name = ins.reg_name(register).lower()
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
        name in {"b", "bl", "br", "blr", "ret", "retaa", "retab",
                 "eret", "cbz", "cbnz", "tbz", "tbnz"}
        or name.startswith("b.")
    )


def _direction(mnemonic):
    name = mnemonic.lower()
    if name.startswith("st"):
        return "write"
    if name.startswith("ld"):
        return "read"
    return "unknown"


def _overlaps(address, width, start, end):
    extent = width if isinstance(width, int) and width > 0 else 1
    return address < end and address + extent > start


def _trace_page_candidate(text, start, page, destination, window_bytes, decoder,
                          target_start, target_end):
    end = min(len(text), start + window_bytes)
    known = {
        "x%d" % destination: {
            "address": page,
            "chain": [{
                "site": _hex(start),
                "kind": "ADRP",
                "page": _hex(page),
                "destination_register": "x%d" % destination,
            }],
        }
    }
    accesses = []
    indexed = []

    for pc in range(start + 4, end, 4):
        ins = _decode_one(decoder, text, pc)
        if ins is None:
            break
        try:
            reads, writes = ins.regs_access()
        except Exception:
            break
        read_names = sorted({_reg_name(ins, value) for value in reads} - {None})
        written_names = sorted({_reg_name(ins, value) for value in writes} - {None})

        for operand_index, operand in enumerate(ins.operands):
            if operand.type != ARM64_OP_MEM:
                continue
            base = _reg_name(ins, operand.mem.base)
            index = _reg_name(ins, operand.mem.index)
            if base not in known:
                continue
            base_address = known[base]["address"] + operand.mem.disp
            width, width_source = _memory_access_width(ins)
            if index:
                if _overlaps(base_address, width, target_start, target_end):
                    indexed.append({
                        "site": _hex(pc),
                        "word_le": bytes(text[pc:pc + 4]).hex(),
                        "mnemonic": ins.mnemonic,
                        "operands": ins.op_str,
                        "base_register": base,
                        "index_register": index,
                        "base_plus_displacement": _hex(base_address),
                        "displacement": operand.mem.disp,
                        "width_bytes": width,
                        "direction": _direction(ins.mnemonic),
                        "effective_address_resolved": False,
                        "origin_chain": list(known[base]["chain"]),
                    })
                continue
            if not _overlaps(base_address, width, target_start, target_end):
                continue
            accesses.append({
                "site": _hex(pc),
                "operand_index": operand_index,
                "word_le": bytes(text[pc:pc + 4]).hex(),
                "mnemonic": ins.mnemonic,
                "operands": ins.op_str,
                "direction": _direction(ins.mnemonic),
                "effective_address": _hex(base_address),
                "width_bytes": width,
                "width_source": width_source,
                "base_register": base,
                "index_register": None,
                "displacement": operand.mem.disp,
                "writeback": bool(getattr(ins, "writeback", False)),
                "read_registers": read_names,
                "written_registers": written_names,
                "effective_address_resolved": True,
                "origin_chain": list(known[base]["chain"]),
            })

        handled_destination = None
        if ins.mnemonic == "adrp" and len(ins.operands) >= 2:
            op0, op1 = ins.operands[0], ins.operands[1]
            if op0.type == ARM64_OP_REG and op1.type == ARM64_OP_IMM:
                word = struct.unpack_from("<I", text, pc)[0]
                target_page, rd = _decode_adrp_page(word, pc)
                name = "x%d" % rd
                known[name] = {
                    "address": target_page,
                    "chain": [{
                        "site": _hex(pc),
                        "kind": "ADRP",
                        "page": _hex(target_page),
                        "destination_register": name,
                    }],
                }
                handled_destination = name
        elif ins.mnemonic == "add" and len(ins.operands) >= 3:
            op0, op1, op2 = ins.operands[:3]
            if (op0.type == ARM64_OP_REG and op1.type == ARM64_OP_REG
                    and op2.type == ARM64_OP_IMM):
                destination_name = _reg_name(ins, op0.reg)
                source_name = _reg_name(ins, op1.reg)
                shift = getattr(getattr(op2, "shift", None), "value", 0) or 0
                if source_name in known and shift in (0, 12):
                    immediate = int(op2.imm) << shift
                    known[destination_name] = {
                        "address": known[source_name]["address"] + immediate,
                        "chain": known[source_name]["chain"] + [{
                            "site": _hex(pc),
                            "kind": "ADD_IMMEDIATE",
                            "source_register": source_name,
                            "destination_register": destination_name,
                            "immediate": immediate,
                        }],
                    }
                else:
                    known.pop(destination_name, None)
                handled_destination = destination_name
        elif ins.mnemonic == "mov" and len(ins.operands) >= 2:
            op0, op1 = ins.operands[:2]
            if op0.type == ARM64_OP_REG and op1.type == ARM64_OP_REG:
                destination_name = _reg_name(ins, op0.reg)
                source_name = _reg_name(ins, op1.reg)
                if source_name in known:
                    known[destination_name] = {
                        "address": known[source_name]["address"],
                        "chain": known[source_name]["chain"] + [{
                            "site": _hex(pc),
                            "kind": "MOV_REGISTER",
                            "source_register": source_name,
                            "destination_register": destination_name,
                        }],
                    }
                else:
                    known.pop(destination_name, None)
                handled_destination = destination_name

        for name in written_names:
            if name != handled_destination:
                known.pop(name, None)
        if any(bool(getattr(ins, "writeback", False)) for op in ins.operands
               if op.type == ARM64_OP_MEM):
            for op in ins.operands:
                if op.type == ARM64_OP_MEM:
                    known.pop(_reg_name(ins, op.mem.base), None)
        if _is_control_flow(ins):
            break

    return end, accesses, indexed


def scan_address_page(text, page=TABLE_PAGE, target_start=TABLE_START,
                      target_end=TABLE_END, window_bytes=WINDOW_BYTES):
    """Find every aligned ADRP to one page and follow bounded local address chains."""
    if not isinstance(text, (bytes, bytearray, memoryview)):
        raise ValueError("AArch64 text must be bytes-like")
    if (not isinstance(page, int) or page < 0 or (page & 0xFFF)
            or not isinstance(target_start, int) or not isinstance(target_end, int)
            or target_start < page or (target_start & 7) or (target_end & 7)
            or target_end <= target_start
            or ((target_end - 1) & ~0xFFF) != page
            or not isinstance(window_bytes, int) or window_bytes < 4
            or (window_bytes & 3)):
        raise ValueError("Invalid page/range/window bounds")
    if len(text) < 4:
        raise ValueError("AArch64 text is shorter than one instruction")

    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    references = []
    accesses_by_key = {}
    indexed_by_key = {}

    for pc in range(0, len(text) - 3, 4):
        word = struct.unpack_from("<I", text, pc)[0]
        if word & 0x9F000000 != 0x90000000:
            continue
        target_page, rd = _decode_adrp_page(word, pc)
        if target_page != page or rd == 31:
            continue
        ins = _decode_one(decoder, text, pc)
        if ins is None or ins.mnemonic != "adrp":
            continue
        window_end, accesses, indexed = _trace_page_candidate(
            text, pc, target_page, rd, window_bytes, decoder,
            target_start, target_end
        )
        references.append({
            "site": _hex(pc),
            "destination_register": "x%d" % rd,
            "target_page": _hex(target_page),
            "window_end_exclusive": _hex(window_end),
            "window_sha256": hashlib.sha256(text[pc:window_end]).hexdigest(),
            "bounded_linear_window_not_function_extent": True,
        })
        for row in accesses:
            key = (row["site"], row["operand_index"])
            if key not in accesses_by_key:
                row["origin_candidates"] = []
                accesses_by_key[key] = row
            origin = {"adrp_site": _hex(pc), "chain": row["origin_chain"]}
            if origin not in accesses_by_key[key]["origin_candidates"]:
                accesses_by_key[key]["origin_candidates"].append(origin)
        for row in indexed:
            key = row["site"]
            if key not in indexed_by_key:
                row["origin_candidates"] = []
                indexed_by_key[key] = row
            origin = {"adrp_site": _hex(pc), "chain": row["origin_chain"]}
            if origin not in indexed_by_key[key]["origin_candidates"]:
                indexed_by_key[key]["origin_candidates"].append(origin)

    ordered_accesses = [
        accesses_by_key[key] for key in sorted(
            accesses_by_key, key=lambda item: (int(item[0], 16), item[1])
        )
    ]
    ordered_indexed = [
        indexed_by_key[key] for key in sorted(indexed_by_key, key=lambda item: int(item, 16))
    ]
    return {
        "target_page": _hex(page),
        "target_range": {"start": _hex(target_start), "end_exclusive": _hex(target_end)},
        "page_reference_count": len(references),
        "page_references": references,
        "direct_accesses": ordered_accesses,
        "indexed_access_candidates": ordered_indexed,
        "page_reference_census_complete": True,
        "direct_access_census_complete": False,
        "window_bytes_per_reference": window_bytes,
        "indirect_register_aliases_traced": False,
        "function_extents_verified": False,
    }


def scan_relocations_to_range(memory, tags, target_start=TABLE_START,
                              target_end=TABLE_END):
    """Inventory RELA cells in the table range and addends pointing into it."""
    if (not isinstance(memory, (bytes, bytearray, memoryview))
            or not isinstance(tags, dict)
            or not isinstance(target_start, int) or not isinstance(target_end, int)
            or target_start < 0 or target_end <= target_start):
        raise ValueError("Invalid relocation scan inputs")
    rela, rela_size, rela_ent = 7, 8, 9
    jmprel, pltrelsz, pltrel = 23, 2, 20
    tables = []
    if rela in tags and rela_size in tags:
        if tags.get(rela_ent, 24) != 24:
            raise ValueError("Unexpected DT_RELA entry size")
        tables.append(("DT_RELA", tags[rela], tags[rela_size]))
    if jmprel in tags and pltrelsz in tags:
        if tags.get(pltrel, rela) != rela:
            raise ValueError("DT_JMPREL is not RELA")
        tables.append(("DT_JMPREL", tags[jmprel], tags[pltrelsz]))

    seen_records = set()
    destinations = []
    addends = []
    total = 0
    for name, offset, size in tables:
        if (not isinstance(offset, int) or not isinstance(size, int)
                or offset < 0 or offset & 7 or size < 0 or size % 24
                or offset + size > len(memory)):
            raise ValueError("Dynamic RELA table bounds are invalid")
        for record_offset in range(offset, offset + size, 24):
            if record_offset in seen_records:
                raise ValueError("Overlapping dynamic RELA table records")
            seen_records.add(record_offset)
            total += 1
            r_offset, info, addend = struct.unpack_from("<QQq", memory, record_offset)
            row = {
                "table": name,
                "record_offset": _hex(record_offset),
                "destination": _hex(r_offset),
                "type_number": info & 0xFFFFFFFF,
                "symbol_index": info >> 32,
                "addend": addend,
            }
            if target_start <= r_offset < target_end:
                destinations.append(row)
            if target_start <= addend < target_end:
                addends.append(row)
    return {
        "record_count_scanned": total,
        "destinations_in_table_range": destinations,
        "addends_pointing_into_table_range": addends,
        "range_end_exclusive": _hex(target_end),
    }


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
    if not (bss_start <= TABLE_START < TABLE_END <= bss_end):
        raise ValueError("Pinned 64-slot table range is no longer fully inside BSS")

    scan = scan_address_page(text)
    accesses = scan["direct_accesses"]
    by_site = {row["site"]: row for row in accesses}
    read = by_site.get("0x116b8a0")
    if (read is None or read["direction"] != "read"
            or read["effective_address"] != _hex(TABLE_START)
            or read["width_bytes"] != 8):
        raise ValueError("Expected direct first-slot load at 0x116b8a0 was not reproduced")

    cleanup_offsets = list(range(0x1E0, -1, -0x20))
    cleanup_sites = list(range(CLEANUP_START, CLEANUP_END, 4))
    if len(cleanup_sites) != 16 or len(cleanup_offsets) != 16:
        raise ValueError("Cleanup clear-range boundary constants are inconsistent")
    cleanup_writes = []
    for site, offset in zip(cleanup_sites, cleanup_offsets):
        row = by_site.get(_hex(site))
        if (row is None or row["direction"] != "write"
                or row["effective_address"] != _hex(TABLE_START + offset)
                or row["width_bytes"] != 32):
            raise ValueError("Expected 32-byte table clear store changed at " + _hex(site))
        cleanup_writes.append(row)

    cleanup_set = {_hex(site) for site in cleanup_sites}
    direct_writes = [row for row in accesses if row["direction"] == "write"]
    outside_cleanup = [row for row in direct_writes if row["site"] not in cleanup_set]
    relocations = scan_relocations_to_range(memory, _tags(memory))

    return {
        "status": "PINNED_FILELOAD_TABLE_DIRECT_REFERENCE_CENSUS_STATIC_ONLY",
        "original_main_sha256": digest,
        "table": {
            "base": _hex(TABLE_START),
            "end_exclusive": _hex(TABLE_END),
            "slot_count": (TABLE_END - TABLE_START) // 8,
            "slot_stride_bytes": 8,
            "bss_start": _hex(bss_start),
            "bss_end": _hex(bss_end),
            "runtime_slot_values_verified": False,
        },
        "adrp_page_scan": scan,
        "first_slot_load": read,
        "cleanup_clear_writes": cleanup_writes,
        "direct_write_candidates_outside_cleanup": outside_cleanup,
        "relocations": relocations,
        "analysis_scope": {
            "all_aligned_adrp_words_to_page_scanned": True,
            "each_candidate_followed_linearly_until_control_flow_or_0x100_bytes": True,
            "only_adrp_derived_register_addresses_are_followed": True,
            "indirect_pointer_aliases_and_indexed_effective_addresses_not_resolved": True,
            "a_missing_direct_writer_does_not_exclude_dynamic_or_aliased_writers": True,
            "no_function_extent_or_cxx_object_layout_inference": True,
        },
        "limits": {
            "producer_identity_verified": False,
            "slot_writer_lifecycle_verified": False,
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
    raise SystemExit("Use tests/test_native_fileload_table_access.py")
