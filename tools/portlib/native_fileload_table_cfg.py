"""Bounded FileLoad table CFG and static pointer-alias evidence.

This follows in-window AArch64 branch paths from exact ADRP references and
resolves only single-level pointer loads backed by file bytes or
R_AARCH64_RELATIVE relocations. Calls clobber tracked address state. It does
not scan runtime BSS/heap values, infer function extents, or prove a consumer
ABI, ownership, callback, lifecycle, or archive precedence.
"""
import hashlib
import struct
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_MEM, ARM64_OP_REG

from .native_cpk_cfg import _edges
from .native_cpk_graph import MAIN_SHA256
from .native_fileload_guard_state import _decode_adrp_page
from .native_fileload_registration_target import _memory_access_width
from .native_fileload_table_access import (
    PREFIX_BYTES,
    TABLE_END,
    TABLE_PAGE,
    TABLE_START,
    _decode_one,
    _direction,
    _hex,
    _overlaps,
    _reg_name,
    _update_known,
    _zero_register_state,
    scan_address_page,
)
from .native_fileopen_import import _read_image, _tags

MAX_PAGES = 64
MAX_REFERENCES = 4096
DEFAULT_WINDOW_BYTES = 0x100
DEFAULT_MAX_STATES = 256
RELATIVE_RELOCATION_TYPE = 1027
CALL_KINDS = {"call", "indirect_call_unresolved"}
TERMINATOR_KINDS = {"return_or_indirect_terminator"}


def _clone_known(known):
    return {
        name: {
            "address": value["address"],
            "dynamic_terms": [dict(term) for term in value.get("dynamic_terms", [])],
            "chain": [dict(step) for step in value.get("chain", [])],
        }
        for name, value in known.items()
    }


def _state_signature(known, branch_reachable):
    """Identify semantic register states, not every distinct branch history."""
    registers = []
    for name, value in sorted(known.items()):
        terms = tuple(
            (term.get("register"), term.get("extension"), term.get("scale"))
            for term in value.get("dynamic_terms", [])
        )
        # Keep provenance distinct: equal addresses reached through different
        # ADRP/ADD or static-cell chains must not collapse into one state.
        chain = tuple(repr(step) for step in value.get("chain", []))
        registers.append((name, value["address"], terms, chain))
    # Keep one branchless and one branch-reachable representative. Different
    # branch histories with identical register provenance are equivalent for
    # subsequent memory-address analysis.
    return tuple(registers), bool(branch_reachable)


def _target_page(target_start):
    return target_start & ~0xFFF


def collect_static_pointer_cells(rows, memory, tags, target_start=TABLE_START,
                                 target_end=TABLE_END):
    """Find file-backed or RELATIVE-relocated 64-bit cells into the target page.

    BSS/heap cells without a file-backed value or relocation are deliberately
    not inferred. Values anywhere in the target 4 KiB page are retained so a
    later ADD can reach the exact 64-slot table range.
    """
    if not isinstance(memory, (bytes, bytearray, memoryview)):
        raise ValueError("Mapped NSO memory must be bytes-like")
    if not isinstance(rows, (list, tuple)) or not isinstance(tags, dict):
        raise ValueError("Invalid file-backed segment or dynamic-tag input")
    if (not isinstance(target_start, int) or not isinstance(target_end, int)
            or target_start < 0 or target_end <= target_start
            or (target_start & 7) or (target_end & 7)
            or _target_page(target_start) != _target_page(target_end - 1)):
        raise ValueError("Invalid target range for pointer-cell scan")

    page_start = _target_page(target_start)
    page_end = page_start + 0x1000
    result = {}

    def add(cell, value, source):
        if (not isinstance(cell, int) or cell < 0 or (cell & 7)
                or cell + 8 > len(memory)):
            raise ValueError("Static pointer cell is outside mapped NSO memory")
        if not isinstance(value, int) or not page_start <= value < page_end:
            return
        entries = result.setdefault(cell, [])
        row = {"value": value, "source": source}
        if row not in entries:
            entries.append(row)

    for segment_index, segment in enumerate(rows):
        if segment_index == 0:
            continue  # NSO segment 0 is executable text, not a data pointer-cell pool.
        if not isinstance(segment, (list, tuple)) or len(segment) < 2:
            raise ValueError("Malformed file-backed NSO segment row")
        va, raw = segment[0], segment[1]
        if (not isinstance(va, int) or va < 0
                or not isinstance(raw, (bytes, bytearray, memoryview))
                or va + len(raw) > len(memory)):
            raise ValueError("File-backed NSO segment exceeds mapped memory")
        first = (va + 7) & ~7
        end = va + len(raw)
        byte_count = ((end - first) // 8) * 8
        if byte_count <= 0:
            continue
        view = memoryview(raw)[first - va:first - va + byte_count]
        for index, (value,) in enumerate(struct.iter_unpack("<Q", view)):
            if page_start <= value < page_end:
                add(first + index * 8, value, "FILE_BACKED_LITERAL")

    if (7 in tags) != (8 in tags):
        raise ValueError("Incomplete DT_RELA tag pair")
    if (23 in tags) != (2 in tags):
        raise ValueError("Incomplete DT_JMPREL tag pair")

    tables = []
    if 7 in tags:
        if tags.get(9, 24) != 24:
            raise ValueError("Unexpected DT_RELA entry size")
        tables.append(("DT_RELA", tags[7], tags[8]))
    if 23 in tags:
        if tags.get(20, 7) != 7:
            raise ValueError("DT_JMPREL is not RELA")
        tables.append(("DT_JMPREL", tags[23], tags[2]))

    seen_records = set()
    for name, offset, size in tables:
        if (not isinstance(offset, int) or not isinstance(size, int)
                or offset < 0 or (offset & 7) or size < 0 or (size % 24)
                or offset + size > len(memory)):
            raise ValueError("Dynamic RELA table bounds are invalid")
        for record_offset in range(offset, offset + size, 24):
            if record_offset in seen_records:
                raise ValueError("Overlapping dynamic RELA table records")
            seen_records.add(record_offset)
            destination, info, addend = struct.unpack_from(
                "<QQq", memory, record_offset
            )
            relocation_type = info & 0xFFFFFFFF
            symbol_index = info >> 32
            if relocation_type == RELATIVE_RELOCATION_TYPE and symbol_index == 0:
                add(destination, addend, name + ":R_AARCH64_RELATIVE")

    for entries in result.values():
        entries.sort(key=lambda row: (row["value"], row["source"]))
    return result


def _pointer_cell_report(pointer_cells, target_start=TABLE_START):
    literal_count = 0
    relative_count = 0
    cells = []
    for cell, entries in sorted(pointer_cells.items()):
        sources = sorted({row["source"] for row in entries})
        values = sorted({row["value"] for row in entries})
        literal_count += sum(row["source"] == "FILE_BACKED_LITERAL" for row in entries)
        relative_count += sum(row["source"].endswith(":R_AARCH64_RELATIVE") for row in entries)
        cells.append({
            "cell": _hex(cell),
            "candidate_values": [_hex(value) for value in values],
            "sources": sources,
            "unique_value": len(values) == 1,
        })
    return {
        "target_page": _hex(_target_page(target_start)),
        "candidate_cell_count": len(cells),
        "file_backed_literal_rows": literal_count,
        "relative_relocation_rows": relative_count,
        "cells": cells,
        "non_text_file_backed_segments_scanned": True,
        "executable_text_segment_literal_words_scanned": False,
        "dynamic_relative_relocations_scanned": True,
        "bss_or_heap_cells_without_relocations_scanned": False,
        "runtime_pointer_values_resolved": False,
    }


def _trace_reference_cfg(text, pc, page, destination, pointer_cells,
                         target_start, target_end, window_bytes, max_states,
                         decoder):
    prefix_start = max(0, pc - PREFIX_BYTES)
    window_end = min(len(text), pc + window_bytes)
    known = _zero_register_state()

    for prefix_pc in range(prefix_start, pc, 4):
        instruction = _decode_one(decoder, text, prefix_pc)
        if instruction is None:
            known = _zero_register_state()
            continue
        prefix_edges = _edges(prefix_pc, instruction.mnemonic, instruction.op_str)
        if any(kind in CALL_KINDS or kind in TERMINATOR_KINDS
               or kind in {"conditional", "unconditional"}
               for kind, _ in prefix_edges):
            known = _zero_register_state()
            continue
        if not _update_known(instruction, text, prefix_pc, known):
            known = _zero_register_state()

    adrp = _decode_one(decoder, text, pc)
    if adrp is None or adrp.mnemonic != "adrp":
        raise ValueError("Page reference is not a decoded ADRP")
    if not _update_known(adrp, text, pc, known):
        raise ValueError("Unable to seed ADRP reaching state")

    start = pc + 4
    queue = deque([(start, known, ())])
    visited = {}
    equivalent_branch_histories_merged = 0
    decoded_sites = set()
    direct = {}
    indexed = {}
    aliases = {}
    ambiguous = {}
    calls = {}
    outside = {}
    undecodable = set()
    reached_branches = set()
    budget_exceeded = False
    page_start = _target_page(target_start)
    page_end = page_start + 0x1000

    def add_access(collection, key, row):
        existing = collection.get(key)
        if existing is None:
            existing = dict(row)
            existing["branch_path_witnesses"] = []
            collection[key] = existing
        if row["branch_sites"]:
            witness = list(row["branch_sites"])
            if witness not in existing["branch_path_witnesses"]:
                existing["branch_path_witnesses"].append(witness)

    while queue:
        current_pc, current_known, branch_sites = queue.popleft()
        if current_pc < start or current_pc >= window_end or (current_pc & 3):
            outside[(current_pc, "queued_target")] = {
                "from": _hex(pc),
                "kind": "queued_target",
                "target": _hex(current_pc),
            }
            continue
        reached_branches.update(branch_sites)
        signature = _state_signature(current_known, bool(branch_sites))
        state_key = (current_pc, signature)
        if state_key in visited:
            if visited[state_key] != tuple(branch_sites):
                equivalent_branch_histories_merged += 1
            continue
        if len(visited) >= max_states:
            budget_exceeded = True
            break
        visited[state_key] = tuple(branch_sites)
        instruction = _decode_one(decoder, text, current_pc)
        if instruction is None:
            undecodable.add(current_pc)
            continue
        decoded_sites.add(current_pc)

        try:
            reads, writes = instruction.regs_access()
        except Exception:
            undecodable.add(current_pc)
            continue
        read_names = sorted({_reg_name(instruction, value) for value in reads} - {None})
        written_names = sorted({_reg_name(instruction, value) for value in writes} - {None})

        next_known = _clone_known(current_known)
        alias_to_apply = None
        for operand_index, operand in enumerate(instruction.operands):
            if operand.type != ARM64_OP_MEM:
                continue
            base = _reg_name(instruction, operand.mem.base)
            index = _reg_name(instruction, operand.mem.index)
            if base not in current_known:
                continue
            base_info = current_known[base]
            address = base_info["address"] + operand.mem.disp
            width, width_source = _memory_access_width(instruction)
            terms = [dict(term) for term in base_info.get("dynamic_terms", [])]
            if index:
                terms.append({
                    "register": index,
                    "extension": "MEMORY_INDEX_UNRESOLVED",
                    "scale": None,
                })
            direction = _direction(instruction.mnemonic)
            if terms:
                if _overlaps(address, width, target_start, target_end):
                    primary = terms[0]
                    row = {
                        "site": _hex(current_pc),
                        "operand_index": operand_index,
                        "word_le": bytes(text[current_pc:current_pc + 4]).hex(),
                        "mnemonic": instruction.mnemonic,
                        "operands": instruction.op_str,
                        "direction": direction,
                        "base_register": base,
                        "index_register": primary.get("register"),
                        "index_scale": primary.get("scale"),
                        "index_extension": primary.get("extension"),
                        "dynamic_index_terms": terms,
                        "base_plus_displacement": _hex(address),
                        "displacement": operand.mem.disp,
                        "width_bytes": width,
                        "width_source": width_source,
                        "effective_address_resolved": False,
                        "origin_chain": list(base_info["chain"]),
                        "branch_sites": list(branch_sites),
                    }
                    key = (
                        row["site"], operand_index, direction, row["base_plus_displacement"],
                        tuple((x.get("register"), x.get("extension"), x.get("scale")) for x in terms),
                        width,
                    )
                    add_access(indexed, key, row)
            elif _overlaps(address, width, target_start, target_end):
                row = {
                    "site": _hex(current_pc),
                    "operand_index": operand_index,
                    "word_le": bytes(text[current_pc:current_pc + 4]).hex(),
                    "mnemonic": instruction.mnemonic,
                    "operands": instruction.op_str,
                    "direction": direction,
                    "effective_address": _hex(address),
                    "width_bytes": width,
                    "width_source": width_source,
                    "base_register": base,
                    "index_register": None,
                    "displacement": operand.mem.disp,
                    "writeback": bool(getattr(instruction, "writeback", False)),
                    "read_registers": read_names,
                    "written_registers": written_names,
                    "effective_address_resolved": True,
                    "origin_chain": list(base_info["chain"]),
                    "branch_sites": list(branch_sites),
                }
                key = (row["site"], operand_index, direction, row["effective_address"], width)
                add_access(direct, key, row)

            if (direction == "read" and width == 8 and index is None and not terms
                    and instruction.mnemonic.lower() in {"ldr", "ldur"}
                    and address in pointer_cells):
                entries = pointer_cells[address]
                values = sorted({entry["value"] for entry in entries})
                sources = sorted({entry["source"] for entry in entries})
                destination_operand = (
                    instruction.operands[0] if instruction.operands else None
                )
                destination_raw = (
                    instruction.reg_name(destination_operand.reg).lower()
                    if destination_operand is not None
                    and destination_operand.type == ARM64_OP_REG else ""
                )
                destination_name = (
                    _reg_name(instruction, destination_operand.reg)
                    if destination_operand is not None
                    and destination_operand.type == ARM64_OP_REG else None
                )
                if (len(values) == 1 and page_start <= values[0] < page_end
                        and destination_raw.startswith("x")
                        and destination_name is not None):
                    alias_to_apply = (destination_name, values[0], address, sources, base_info)
                    alias_row = {
                        "site": _hex(current_pc),
                        "cell_address": _hex(address),
                        "loaded_value": _hex(values[0]),
                        "destination_register": destination_name,
                        "sources": sources,
                        "origin_chain": list(base_info["chain"]),
                        "branch_sites": list(branch_sites),
                        "static_candidate_only": True,
                    }
                    aliases[(alias_row["site"], alias_row["cell_address"],
                             alias_row["loaded_value"], destination_name)] = alias_row
                else:
                    ambiguous_row = {
                        "site": _hex(current_pc),
                        "cell_address": _hex(address),
                        "candidate_values": [_hex(value) for value in values],
                        "destination_register": destination_name,
                        "sources": sources,
                        "branch_sites": list(branch_sites),
                        "reason": "ambiguous_or_outside_target_page",
                    }
                    ambiguous[(ambiguous_row["site"], ambiguous_row["cell_address"])] = ambiguous_row

        if not _update_known(instruction, text, current_pc, next_known):
            next_known = _zero_register_state()
        if alias_to_apply is not None:
            destination_name, value, cell, sources, base_info = alias_to_apply
            next_known[destination_name] = {
                "address": value,
                "dynamic_terms": [],
                "chain": list(base_info["chain"]) + [{
                    "site": _hex(current_pc),
                    "kind": "STATIC_POINTER_LOAD",
                    "cell_address": _hex(cell),
                    "loaded_value": _hex(value),
                    "sources": sources,
                    "destination_register": destination_name,
                }],
            }

        edges = _edges(current_pc, instruction.mnemonic, instruction.op_str)
        is_call = any(kind in CALL_KINDS for kind, _ in edges)
        if is_call:
            for kind, target in edges:
                if kind in CALL_KINDS:
                    calls[(current_pc, kind, target)] = {
                        "site": _hex(current_pc),
                        "kind": kind,
                        "target": _hex(target) if target is not None else None,
                    }
                elif kind.startswith("fallthrough_after"):
                    if target is not None and start <= target < window_end:
                        queue.append((target, _zero_register_state(), branch_sites))
                    elif target is not None:
                        outside[(current_pc, kind, target)] = {
                            "from": _hex(current_pc),
                            "kind": kind,
                            "target": _hex(target),
                        }
            continue

        for kind, target in edges:
            if kind in TERMINATOR_KINDS:
                continue
            if kind in CALL_KINDS:
                calls[(current_pc, kind, target)] = {
                    "site": _hex(current_pc),
                    "kind": kind,
                    "target": _hex(target) if target is not None else None,
                }
                continue
            if target is None:
                outside[(current_pc, kind, None)] = {
                    "from": _hex(current_pc),
                    "kind": kind,
                    "target": None,
                }
                continue
            next_branches = branch_sites
            if kind in {"conditional", "unconditional"}:
                site = _hex(current_pc)
                next_branches = branch_sites if site in branch_sites else branch_sites + (site,)
            if start <= target < window_end and not (target & 3):
                queue.append((target, _clone_known(next_known), next_branches))
            else:
                outside[(current_pc, kind, target)] = {
                    "from": _hex(current_pc),
                    "kind": kind,
                    "target": _hex(target),
                }

    reference = {
        "site": _hex(pc),
        "destination_register": "x%d" % destination,
        "target_page": _hex(page),
        "prefix_start": _hex(prefix_start),
        "prefix_sha256": hashlib.sha256(text[prefix_start:pc]).hexdigest(),
        "window_end_exclusive": _hex(window_end),
        "window_sha256": hashlib.sha256(text[pc:window_end]).hexdigest(),
        "reachable_state_count": len(visited),
        "decoded_instruction_count": len(decoded_sites),
        "branch_sites_reached": sorted(reached_branches, key=lambda value: int(value, 16)),
        "state_budget_exceeded": budget_exceeded,
        "equivalent_branch_histories_merged": equivalent_branch_histories_merged,
        "branch_path_witnesses_exhaustive": (
            equivalent_branch_histories_merged == 0 and not budget_exceeded
        ),
        "undecodable_words": [_hex(value) for value in sorted(undecodable)],
        "bounded_in_window_cfg_complete": not budget_exceeded and not undecodable,
        "calls_are_clobber_barriers": True,
        "out_of_window_edges": list(outside.values()),
    }
    return {
        "reference": reference,
        "direct_accesses": list(direct.values()),
        "indexed_access_candidates": list(indexed.values()),
        "memory_loaded_aliases": list(aliases.values()),
        "ambiguous_pointer_loads": list(ambiguous.values()),
        "call_barriers": list(calls.values()),
    }


def scan_address_pages_cfg(text, pages, pointer_cells=None, target_start=TABLE_START,
                           target_end=TABLE_END, window_bytes=DEFAULT_WINDOW_BYTES,
                           max_states=DEFAULT_MAX_STATES, max_references=MAX_REFERENCES):
    """Trace bounded branch paths from ADRP references to selected pages."""
    if not isinstance(text, (bytes, bytearray, memoryview)) or len(text) < 4:
        raise ValueError("AArch64 text must contain complete instructions")
    if not isinstance(pages, (list, tuple, set, frozenset)) or not pages:
        raise ValueError("At least one ADRP target page is required")
    page_set = set(pages)
    if (len(page_set) > MAX_PAGES
            or any(not isinstance(page, int) or page < 0 or (page & 0xFFF)
                   for page in page_set)):
        raise ValueError("Invalid or excessive ADRP target page set")
    if (not isinstance(target_start, int) or not isinstance(target_end, int)
            or target_start < 0 or (target_start & 7) or (target_end & 7)
            or target_end <= target_start
            or _target_page(target_start) != _target_page(target_end - 1)):
        raise ValueError("Invalid target memory range")
    if (not isinstance(window_bytes, int) or window_bytes < 8
            or (window_bytes & 3) or not isinstance(max_states, int)
            or max_states <= 0 or not isinstance(max_references, int)
            or max_references <= 0):
        raise ValueError("Invalid CFG window or state budget")
    if pointer_cells is None:
        pointer_cells = {}
    if not isinstance(pointer_cells, dict):
        raise ValueError("Pointer-cell map must be a dictionary")
    for cell, entries in pointer_cells.items():
        if (not isinstance(cell, int) or cell < 0 or (cell & 7)
                or not isinstance(entries, list) or not entries
                or any(not isinstance(row, dict)
                       or not isinstance(row.get("value"), int)
                       or not isinstance(row.get("source"), str)
                       for row in entries)):
            raise ValueError("Malformed static pointer-cell map")

    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    candidates = {page: [] for page in page_set}
    for pc in range(0, len(text) - 3, 4):
        word = struct.unpack_from("<I", text, pc)[0]
        if word & 0x9F000000 != 0x90000000:
            continue
        page, rd = _decode_adrp_page(word, pc)
        if page not in candidates or rd == 31:
            continue
        instruction = _decode_one(decoder, text, pc)
        if instruction is not None and instruction.mnemonic == "adrp":
            candidates[page].append((pc, rd))

    references = []
    direct = {}
    indexed = {}
    aliases = {}
    ambiguous = {}
    calls = {}
    outside = {}
    undecodable = set()
    state_budget_exceeded = False

    def merge(collection, row, key):
        existing = collection.get(key)
        if existing is None:
            existing = dict(row)
            existing["origin_candidates"] = []
            collection[key] = existing
        origin = {
            "adrp_site": row.get("adrp_site"),
            "origin_chain": row.get("origin_chain", []),
            "branch_sites": row.get("branch_sites", []),
        }
        if origin not in existing["origin_candidates"]:
            existing["origin_candidates"].append(origin)

    target_page = _target_page(target_start)
    page_order = ([target_page] if target_page in page_set else []) + sorted(
        page for page in page_set if page != target_page
    )
    processed_pages = []
    skipped_pages = []
    for page in page_order:
        page_candidates = candidates.get(page, [])
        remaining = max_references - len(references)
        if len(page_candidates) > remaining:
            if page == target_page:
                raise ValueError("Target-page ADRP reference budget exceeded")
            skipped_pages.append({
                "page": _hex(page),
                "candidate_reference_count": len(page_candidates),
                "remaining_reference_budget": remaining,
                "reason": "reference_budget_exceeded",
            })
            continue
        processed_pages.append(page)
        for pc, rd in page_candidates:
            trace = _trace_reference_cfg(
                text, pc, page, rd, pointer_cells, target_start, target_end,
                window_bytes, max_states, decoder
            )
            reference = trace["reference"]
            references.append(reference)
            state_budget_exceeded = state_budget_exceeded or reference["state_budget_exceeded"]
            undecodable.update(int(value, 16) for value in reference["undecodable_words"])
            for row in trace["direct_accesses"]:
                row["adrp_site"] = _hex(pc)
                key = (row["site"], row["operand_index"], row["direction"],
                       row["effective_address"], row["width_bytes"])
                merge(direct, row, key)
            for row in trace["indexed_access_candidates"]:
                row["adrp_site"] = _hex(pc)
                terms = tuple((x.get("register"), x.get("extension"), x.get("scale"))
                              for x in row["dynamic_index_terms"])
                key = (row["site"], row["operand_index"], row["direction"],
                       row["base_plus_displacement"], terms, row["width_bytes"])
                merge(indexed, row, key)
            for row in trace["memory_loaded_aliases"]:
                row["adrp_site"] = _hex(pc)
                key = (row["site"], row["cell_address"], row["loaded_value"],
                       row["destination_register"])
                merge(aliases, row, key)
            for row in trace["ambiguous_pointer_loads"]:
                row["adrp_site"] = _hex(pc)
                key = (row["site"], row["cell_address"],
                       tuple(row["candidate_values"]))
                merge(ambiguous, row, key)
            for row in trace["call_barriers"]:
                calls[(row["site"], row["kind"], row["target"])] = row
            for row in reference["out_of_window_edges"]:
                outside[(row["from"], row["kind"], row["target"])] = row

    direct_rows = sorted(direct.values(), key=lambda row: (
        int(row["site"], 16), row["operand_index"], row["direction"]
    ))
    indexed_rows = sorted(indexed.values(), key=lambda row: (
        int(row["site"], 16), row["operand_index"], row["direction"]
    ))
    alias_rows = sorted(aliases.values(), key=lambda row: int(row["site"], 16))
    ambiguous_rows = sorted(ambiguous.values(), key=lambda row: int(row["site"], 16))
    branch_rows = [
        row for row in direct_rows + indexed_rows
        if row["branch_path_witnesses"]
    ]
    target_page_scanned = target_page in page_set
    target_references = [
        row for row in references if row["target_page"] == _hex(target_page)
    ]
    pointer_references = [
        row for row in references if row["target_page"] != _hex(target_page)
    ]
    target_page_reference_budget_complete = (
        target_page_scanned
        and len(target_references) == len(candidates.get(target_page, []))
    )
    target_page_state_budget_exceeded = any(
        row["state_budget_exceeded"] for row in target_references
    )
    target_page_undecodable_words = sorted({
        value for row in target_references for value in row["undecodable_words"]
    }, key=lambda value: int(value, 16))
    target_page_cfg_complete = (
        target_page_reference_budget_complete
        and not target_page_state_budget_exceeded
        and not target_page_undecodable_words
    )
    pointer_alias_trace_complete = (
        not skipped_pages
        and all(row["bounded_in_window_cfg_complete"] for row in pointer_references)
    )
    return {
        "pages_scanned": [_hex(page) for page in processed_pages],
        "pages_skipped": skipped_pages,
        "candidate_reference_count": sum(len(rows) for rows in candidates.values()),
        "page_reference_count": len(references),
        "target_page_scanned": target_page_scanned,
        "target_page_reference_count": len(target_references),
        "target_page_reference_budget_complete": target_page_reference_budget_complete,
        "target_page_state_budget_exceeded": target_page_state_budget_exceeded,
        "target_page_undecodable_words": target_page_undecodable_words,
        "target_page_cfg_complete": target_page_cfg_complete,
        "pointer_alias_trace_complete": pointer_alias_trace_complete,
        "reference_budget": max_references,
        "reference_budget_exceeded": bool(skipped_pages),
        "page_references": references,
        "direct_accesses": direct_rows,
        "indexed_access_candidates": indexed_rows,
        "memory_loaded_aliases": alias_rows,
        "ambiguous_pointer_loads": ambiguous_rows,
        "branch_path_accesses": branch_rows,
        "branch_path_table_writes": [
            row for row in branch_rows if row["direction"] == "write"
        ],
        "call_barriers": sorted(calls.values(), key=lambda row: (
            int(row["site"], 16), row["kind"]
        )),
        "out_of_window_edges": sorted(outside.values(), key=lambda row: (
            int(row["from"], 16), row["kind"]
        )),
        "undecodable_words": [_hex(value) for value in sorted(undecodable)],
        "state_budget_exceeded": state_budget_exceeded,
        "equivalent_branch_histories_merged": sum(
            row["equivalent_branch_histories_merged"] for row in references
        ),
        "branch_path_witnesses_exhaustive": (
            not skipped_pages and all(
                row["branch_path_witnesses_exhaustive"] for row in references
            )
        ),
        "state_identity": (
            "pc+tracked-address-registers+dynamic-terms+origin-chain+"
            "branch-reachable-class; one representative path per equivalent state"
        ),
        "bounded_in_window_cfg_complete": (
            target_page_cfg_complete and pointer_alias_trace_complete
            and not state_budget_exceeded and not undecodable
        ),
        "branch_targets_outside_window_followed": False,
        "calls_followed": False,
        "function_extents_verified": False,
    }



def _decode_absolute(decoder, text, base_address, pc):
    offset = pc - base_address
    if offset < 0 or offset + 4 > len(text) or (offset & 3):
        return None
    rows = list(decoder.disasm(bytes(text[offset:offset + 4]), pc))
    if len(rows) != 1 or rows[0].size != 4:
        return None
    return rows[0]


def _summarize_counted_slot_loop(text, site, base_address=0):
    """Recognize the exact 64-slot FileLoad loop shape; never infer its callee."""
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True

    def decode(pc):
        instruction = _decode_absolute(decoder, text, base_address, pc)
        if instruction is None:
            raise ValueError("Undecodable instruction at " + _hex(pc))
        return instruction

    def expect(pc, mnemonic, operands):
        instruction = decode(pc)
        if instruction.mnemonic != mnemonic or instruction.op_str != operands:
            raise ValueError("Unexpected instruction at " + _hex(pc))
        return instruction

    def edge_target(instruction, pc, kind):
        return next(
            (target for edge_kind, target in _edges(
                pc, instruction.mnemonic, instruction.op_str
            ) if edge_kind == kind),
            None,
        )

    init_site = site - 8
    expect(init_site, "mov", "x20, xzr")
    adrp = decode(site)
    if adrp.mnemonic != "adrp":
        raise ValueError("Missing table-page ADRP")
    word_offset = site - base_address
    if word_offset < 0 or word_offset + 4 > len(text):
        raise ValueError("ADRP word outside supplied bytes")
    page, register = _decode_adrp_page(
        struct.unpack_from("<I", text, word_offset)[0], site
    )
    if page != TABLE_PAGE or register != 21:
        raise ValueError("Unexpected table-page ADRP destination")
    expect(site + 4, "add", "x21, x21, #0x7d8")

    initial_branch = expect(site + 8, "b", "#0x%x" % (site + 0x18))
    update_site = site + 0x0C
    expect(update_site, "add", "x20, x20, #8")
    expect(site + 0x10, "cmp", "x20, #0x200")
    exit_branch = expect(site + 0x14, "b.eq", "#0x%x" % (site + 0x38))
    if edge_target(initial_branch, site + 8, "unconditional") != site + 0x18:
        raise ValueError("Initial branch does not skip the first counter update")
    if edge_target(exit_branch, site + 0x14, "conditional") != site + 0x38:
        raise ValueError("Counter equality does not branch to loop exit")

    expect(site + 0x18, "add", "x8, x21, x20")
    expect(site + 0x1C, "ldr", "x0, [x8, #0x28]")
    null_branch = expect(site + 0x20, "cbz", "x0, #0x%x" % update_site)
    expect(site + 0x24, "ldr", "x8, [x0]")
    dispatch = decode(site + 0x28)
    if dispatch.mnemonic != "ldr" or dispatch.op_str not in {
        "x8, [x8, #0x60]", "x8, [x8, #0x68]"
    }:
        raise ValueError("Indirect target load is not one of the pinned offsets")
    dispatch_offset = 0x60 if "#0x60]" in dispatch.op_str else 0x68
    expect(site + 0x2C, "blr", "x8")
    expect(site + 0x30, "add", "x19, x0, x19")
    loop_branch = expect(site + 0x34, "b", "#0x%x" % update_site)
    if edge_target(null_branch, site + 0x20, "conditional") != update_site:
        raise ValueError("Null-entry path does not reach the counter update")
    if edge_target(loop_branch, site + 0x34, "unconditional") != update_site:
        raise ValueError("Callback path does not reach the counter update")

    # The caller itself has no other explicit X20 write in the bounded loop.
    # The indirect callee is unresolved, so its callee-saved-register behavior
    # is deliberately not promoted to a verified fact.
    for pc in range(update_site + 4, site + 0x38, 4):
        instruction = decode(pc)
        if instruction.mnemonic in {"cmp", "cmn", "tst", "ccmp", "ccmn"}:
            continue
        try:
            _, writes = instruction.regs_access()
        except Exception as exc:
            raise ValueError("Register effects unavailable at " + _hex(pc)) from exc
        if "x20" in {
            _reg_name(instruction, register_id) for register_id in writes
        }:
            raise ValueError("Unexpected explicit X20 write in loop body")

    table_base = page + 0x7D8 + 0x28
    stride = 8
    limit = 0x200
    if (table_base != TABLE_START or table_base + limit != TABLE_END
            or limit % stride):
        raise ValueError("Loop range does not exactly cover the pinned 64-slot table")
    loop_start = init_site
    loop_end = site + 0x38
    loop_offset = loop_start - base_address
    loop_end_offset = loop_end - base_address
    if loop_offset < 0 or loop_end_offset > len(text):
        raise ValueError("Loop evidence bytes are outside the supplied image")
    return {
        "site": _hex(site),
        "state": "PROVEN_STATIC_LOOP_STRUCTURE_CONDITIONAL_ON_X20_PRESERVATION",
        "loop_bytes_sha256": hashlib.sha256(
            text[loop_offset:loop_end_offset]
        ).hexdigest(),
        "counter": {
            "register": "x20",
            "initial_value": 0,
            "initialization_site": _hex(init_site),
            "initialization": "mov x20, xzr",
            "stride": stride,
            "increment_site": _hex(update_site),
            "comparison_site": _hex(site + 0x10),
            "limit": limit,
            "exit_branch_site": _hex(site + 0x14),
            "exit_condition": "b.eq",
            "iteration_count_if_preserved": limit // stride,
        },
        "table_read": {
            "site": _hex(site + 0x1C),
            "base": _hex(table_base),
            "first_slot": _hex(table_base),
            "last_slot_if_counter_preserved": _hex(table_base + limit - stride),
            "end_exclusive_if_counter_preserved": _hex(table_base + limit),
            "slot_stride_bytes": stride,
            "slot_count_if_counter_preserved": limit // stride,
            "direction": "read",
            "width_bytes": 8,
            "operand": "ldr x0, [x8, #0x28]",
        },
        "control_flow": {
            "initial_skip_update_site": _hex(site + 8),
            "initial_skip_target": _hex(site + 0x18),
            "null_entry_branch_site": _hex(site + 0x20),
            "null_entry_target": _hex(update_site),
            "callback_back_edge_site": _hex(site + 0x34),
            "callback_back_edge_target": _hex(update_site),
            "loop_exit_target": _hex(site + 0x38),
            "caller_explicit_x20_writes_beyond_increment": 0,
        },
        "indirect_dispatch": {
            "object_pointer_load": "ldr x8, [x0]",
            "target_load": dispatch.op_str,
            "target_load_offset": dispatch_offset,
            "call_site": _hex(site + 0x2C),
            "call": "blr x8",
            "target_resolved": False,
            "callback_identity_verified": False,
            "callee_preserves_x20_verified": False,
        },
        "return_accumulator": {
            "register": "x19",
            "instruction_site": _hex(site + 0x30),
            "instruction": "add x19, x0, x19",
        },
        "limits": {
            "runtime_iteration_count_verified": False,
            "all_64_slots_runtime_visited": False,
            "native_consumer_abi_verified": False,
            "object_type_verified": False,
            "ownership_lifecycle_verified": False,
            "lock_unlock_verified": False,
            "async_verified": False,
            "rollback_unbind_verified": False,
            "destructor_identity_verified": False,
            "archive_precedence_verified": False,
            "native_hook_added": False,
            "uzuy_verified": False,
            "gameplay_verified": False,
        },
    }


def _bounded_reference_disassembly(text, site, window_bytes=DEFAULT_WINDOW_BYTES):
    """Retain exact bytes and decoded control-flow edges for a pinned window."""
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    end = min(len(text), site + window_bytes)
    rows = []
    for pc in range(site, end, 4):
        word = bytes(text[pc:pc + 4])
        instruction = _decode_one(decoder, text, pc)
        if instruction is None:
            rows.append({
                "site": _hex(pc),
                "word_le": word.hex(),
                "decoded": False,
                "edges": [],
            })
            continue
        edges = _edges(pc, instruction.mnemonic, instruction.op_str)
        rows.append({
            "site": _hex(pc),
            "word_le": word.hex(),
            "decoded": True,
            "mnemonic": instruction.mnemonic,
            "operands": instruction.op_str,
            "edges": [
                {
                    "kind": kind,
                    "target": _hex(target) if target is not None else None,
                }
                for kind, target in edges
            ],
        })
    return {
        "site": _hex(site),
        "window_end_exclusive": _hex(end),
        "window_sha256": hashlib.sha256(text[site:end]).hexdigest(),
        "instruction_count": len(rows),
        "decoded_instruction_count": sum(row["decoded"] for row in rows),
        "rows": rows,
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

    baseline = scan_address_page(text)
    pointer_cells = collect_static_pointer_cells(rows, memory, _tags(memory))
    pages = {_target_page(TABLE_START)}
    pages.update(cell & ~0xFFF for cell in pointer_cells)
    cfg = scan_address_pages_cfg(text, pages, pointer_cells)
    target_budget_refs = [
        row for row in cfg["page_references"]
        if row["target_page"] == _hex(_target_page(TABLE_START))
        and row["state_budget_exceeded"]
    ]
    target_page_budget_disassembly = [
        _bounded_reference_disassembly(text, int(row["site"], 16))
        for row in target_budget_refs
    ]
    target_page_counted_loops = []
    for row in target_budget_refs:
        try:
            target_page_counted_loops.append(
                _summarize_counted_slot_loop(text, int(row["site"], 16))
            )
        except ValueError as exc:
            target_page_counted_loops.append({
                "site": row["site"],
                "state": "UNRESOLVED",
                "reason": str(exc),
            })

    def access_key(row):
        return (
            row["site"], row.get("operand_index", 1 if "base_plus_displacement" in row else None), row["direction"],
            row.get("effective_address", row.get("base_plus_displacement")),
            row.get("width_bytes"),
        )

    cfg_keys = {
        access_key(row)
        for row in cfg["direct_accesses"] + cfg["indexed_access_candidates"]
    }
    baseline_keys = {
        access_key(row)
        for row in baseline["direct_accesses"] + baseline["indexed_access_candidates"]
    }
    missing_baseline = sorted(baseline_keys - cfg_keys, key=repr)
    if missing_baseline:
        raise ValueError("CFG scan lost a previously verified linear table witness")

    return {
        "status": "PINNED_FILELOAD_TABLE_CFG_BRANCH_AND_STATIC_ALIAS_CENSUS_STATIC_ONLY",
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
        "linear_baseline": {
            "page_reference_count": baseline["page_reference_count"],
            "direct_access_count": len(baseline["direct_accesses"]),
            "indexed_access_count": len(baseline["indexed_access_candidates"]),
            "all_baseline_witnesses_preserved": True,
        },
        "static_pointer_cells": _pointer_cell_report(pointer_cells),
        "target_page_budget_reference_disassembly": target_page_budget_disassembly,
        "target_page_counted_slot_loops": target_page_counted_loops,
        "branch_cfg_scan": cfg,
        "analysis_scope": {
            "all_aligned_adrp_words_for_selected_pages_scanned": True,
            "conditional_and_unconditional_in_window_edges_followed": True,
            "out_of_window_edges_recorded_not_followed": True,
            "direct_and_authenticated_calls_are_clobber_barriers": True,
            "non_text_file_backed_8_byte_pointer_literals_scanned": True,
            "executable_text_segment_literal_words_scanned": False,
            "R_AARCH64_RELATIVE_pointer_addends_scanned": True,
            "single_level_static_pointer_loads_traced": True,
            "bss_or_heap_pointer_cells_without_relocations_scanned": False,
            "dynamic_pointer_values_resolved": False,
            "complete_branch_path_writer_census": False,
            "function_extents_or_object_types_inferred": False,
        },
        "limits": {
            "producer_identity_verified": False,
            "complete_branch_path_writer_census_verified": False,
            "complete_pointer_alias_census_verified": False,
            "runtime_table_values_verified": False,
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
    raise SystemExit("Use tests/test_native_fileload_table_cfg.py")
