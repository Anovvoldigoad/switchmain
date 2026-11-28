"""Bounded return-register provenance for the pinned FileLoad dispatch candidate.

This is read-only static evidence. Calls are not followed; post-call register
provenance is killed rather than inferred from an assumed ABI. Memory reads
remain symbolic. No function identity, object type, ownership, or hook is
established by this module.
"""
import hashlib
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG

from .native_cpk_graph import MAIN_SHA256
from .native_fileload_registration_dispatch import inspect as inspect_dispatch
from .native_fileload_registration_target import analyze_window
from .native_fileload_table_access import TABLE_START, TABLE_END
from .native_fileopen_import import _read_image

TARGET = 0x116B82C
CALL_SITE = 0x116B3B0
WINDOW_BYTES = 0x100
MAX_ITERATIONS = 8192
MAX_ORIGINS = 8
RETURN_MNEMONICS = {"ret", "retaa", "retab"}
GPR_KEYS = tuple("x%d" % index for index in range(31)) + ("sp", "xzr")


def _hex(value):
    return "0x%x" % value


def _reg_key(ins, register):
    if not register:
        return None
    name = ins.reg_name(register).lower()
    if name == "fp":
        return "x29"
    if name == "lr":
        return "x30"
    if name in ("sp", "wsp"):
        return "sp"
    if name in ("xzr", "wzr"):
        return "xzr"
    if name.startswith("w") and name[1:].isdigit():
        return "x" + name[1:]
    if name.startswith("x") and name[1:].isdigit():
        return name
    return None


def _raw_reg_name(ins, operand):
    return ins.reg_name(operand.reg).lower() if operand.type == ARM64_OP_REG else ""


def _values(state, register):
    return state.get(register, frozenset({"UNKNOWN_REGISTER_" + str(register)}))


def _cap(values):
    values = frozenset(values)
    if len(values) > MAX_ORIGINS:
        return frozenset({"UNKNOWN_MANY_ORIGINS"})
    if any(value.startswith("UNKNOWN") for value in values) and len(values) > 1:
        return frozenset({"UNKNOWN_MERGE"})
    return values


def _merge_value(left, right):
    return _cap(set(left) | set(right))


def _merge_state(old, new):
    if old is None:
        return {key: frozenset(value) for key, value in new.items()}, True
    merged = {}
    changed = False
    for key in set(old) | set(new):
        value = _merge_value(
            old.get(key, frozenset({"UNKNOWN_MISSING"})),
            new.get(key, frozenset({"UNKNOWN_MISSING"})),
        )
        merged[key] = value
        changed |= value != old.get(key)
    return merged, changed


def _const_value(value):
    if not value.startswith("CONST(") or not value.endswith(")"):
        return None
    try:
        return int(value[6:-1], 16)
    except ValueError:
        return None


def _width_wrap(values, raw_name):
    if raw_name.startswith("w") and raw_name[1:].isdigit():
        return _cap("ZEXT32(" + value + ")" for value in values)
    return frozenset(values)


def _source_values(state, ins, operand):
    key = _reg_key(ins, operand.reg)
    if key == "xzr":
        return frozenset({"CONST(0x0)"})
    values = _values(state, key)
    raw = _raw_reg_name(ins, operand)
    if raw.startswith("w") and raw[1:].isdigit():
        return _cap("LOW32(" + value + ")" for value in values)
    return values


def _add_values(left_values, right_values, subtract=False):
    result = set()
    for left in left_values:
        for right in right_values:
            left_const = _const_value(left)
            right_const = _const_value(right)
            if left_const is not None and right_const is not None:
                value = left_const - right_const if subtract else left_const + right_const
                result.add("CONST(" + _hex(value) + ")")
            else:
                op = "SUB" if subtract else "ADD"
                result.add(op + "(" + left + "," + right + ")")
    return _cap(result)


def _memory_origin(state, ins, operand):
    base = _reg_key(ins, operand.mem.base)
    index = _reg_key(ins, operand.mem.index)
    displacement = int(operand.mem.disp)
    bases = _values(state, base) if base else frozenset({"UNKNOWN_MEMORY_BASE"})
    indexes = _values(state, index) if index else frozenset({""})
    result = set()
    for base_value in bases:
        for index_value in indexes:
            base_const = _const_value(base_value)
            index_const = _const_value(index_value) if index_value else 0
            if base_const is not None and index_const is not None:
                address = base_const + displacement + index_const
                result.add("MEM(" + _hex(address) + ")")
            else:
                suffix = "+" + index_value if index_value else ""
                disp = ("%+d" % displacement) if displacement else ""
                result.add("MEM(" + base_value + suffix + disp + ")")
    return _cap(result)


def _unknown_written_registers(ins, state, handled, pc):
    # Capstone 5 reports the left compare operand as written for CMP aliases.
    # CMP/CMN/TST/CCMP/CCMN update flags, not the GPR operands.
    if ins.mnemonic.lower() in {"cmp", "cmn", "tst", "ccmp", "ccmn"}:
        return
    try:
        _reads, writes = ins.regs_access()
    except Exception as exc:
        raise ValueError("Register access decode failed at " + _hex(pc)) from exc
    for register in writes:
        key = _reg_key(ins, register)
        if key in GPR_KEYS and key not in handled:
            state[key] = frozenset({"UNKNOWN_WRITE@" + _hex(pc)})


def _transfer(ins, state, pc):
    state = {key: frozenset(value) for key, value in state.items()}
    handled = set()
    mnemonic = ins.mnemonic.lower()
    operands = ins.operands

    if mnemonic == "mov" and len(operands) >= 2 and operands[0].type == ARM64_OP_REG:
        dest = _reg_key(ins, operands[0].reg)
        raw_dest = _raw_reg_name(ins, operands[0])
        if operands[1].type == ARM64_OP_REG:
            values = _source_values(state, ins, operands[1])
        elif operands[1].type == ARM64_OP_IMM:
            values = frozenset({"CONST(" + _hex(int(operands[1].imm)) + ")"})
        else:
            values = frozenset({"UNKNOWN_MOV_SOURCE@" + _hex(pc)})
        if dest in GPR_KEYS:
            state[dest] = _width_wrap(values, raw_dest)
            handled.add(dest)

    elif mnemonic in ("adr", "adrp") and len(operands) >= 2:
        if operands[0].type == ARM64_OP_REG and operands[1].type == ARM64_OP_IMM:
            dest = _reg_key(ins, operands[0].reg)
            raw_dest = _raw_reg_name(ins, operands[0])
            if dest in GPR_KEYS:
                state[dest] = _width_wrap(
                    frozenset({"CONST(" + _hex(int(operands[1].imm)) + ")"}),
                    raw_dest,
                )
                handled.add(dest)

    elif mnemonic in ("add", "sub") and len(operands) >= 3:
        if operands[0].type == ARM64_OP_REG and operands[1].type == ARM64_OP_REG:
            dest = _reg_key(ins, operands[0].reg)
            raw_dest = _raw_reg_name(ins, operands[0])
            left = _source_values(state, ins, operands[1])
            right_operand = operands[2]
            if right_operand.type == ARM64_OP_IMM:
                shift = getattr(getattr(right_operand, "shift", None), "value", 0) or 0
                right = frozenset({"CONST(" + _hex(int(right_operand.imm) << shift) + ")"})
            elif right_operand.type == ARM64_OP_REG:
                right = _source_values(state, ins, right_operand)
                if "uxtw" in ins.op_str.lower():
                    right = _cap("UXTW(" + value + ")" for value in right)
                elif "sxtw" in ins.op_str.lower():
                    right = _cap("SXTW(" + value + ")" for value in right)
                shift = getattr(getattr(right_operand, "shift", None), "value", 0) or 0
                if shift:
                    right = _cap("LSL(" + value + "," + str(shift) + ")" for value in right)
            else:
                right = frozenset({"UNKNOWN_ADD_SOURCE@" + _hex(pc)})
            if dest in GPR_KEYS:
                state[dest] = _width_wrap(
                    _add_values(left, right, subtract=(mnemonic == "sub")),
                    raw_dest,
                )
                handled.add(dest)

    elif mnemonic in ("ldr", "ldur", "ldrb", "ldrh", "ldrsb", "ldrsh", "ldrsw",
                      "ldurb", "ldurh", "ldursb", "ldursh", "ldursw"):
        if operands and operands[0].type == ARM64_OP_REG:
            memory = next((op for op in operands if op.type == ARM64_OP_MEM), None)
            dest = _reg_key(ins, operands[0].reg)
            raw_dest = _raw_reg_name(ins, operands[0])
            if memory is not None and dest in GPR_KEYS:
                state[dest] = _width_wrap(
                    _cap("LOAD(" + value + ")" for value in _memory_origin(state, ins, memory)),
                    raw_dest,
                )
                handled.add(dest)

    elif mnemonic == "ldp" and len(operands) >= 3:
        memory = next((op for op in operands if op.type == ARM64_OP_MEM), None)
        destinations = [op for op in operands if op.type == ARM64_OP_REG][:2]
        if memory is not None and len(destinations) == 2:
            base_values = _memory_origin(state, ins, memory)
            for index, operand in enumerate(destinations):
                dest = _reg_key(ins, operand.reg)
                raw_dest = _raw_reg_name(ins, operand)
                if dest in GPR_KEYS:
                    state[dest] = _width_wrap(
                        _cap("LOAD_PAIR" + str(index) + "(" + value + ")"
                             for value in base_values),
                        raw_dest,
                    )
                    handled.add(dest)

    for key in GPR_KEYS:
        if key not in state:
            state[key] = frozenset({"UNKNOWN_UNINITIALIZED_" + key.upper()})
    _unknown_written_registers(ins, state, handled, pc)
    return state


def _call_clobber(state, pc):
    unknown = frozenset({"UNKNOWN_AFTER_CALL@" + _hex(pc)})
    result = {key: unknown for key in GPR_KEYS}
    result["xzr"] = frozenset({"CONST(0x0)"})
    return result


def trace_return_registers(text, window, max_iterations=MAX_ITERATIONS):
    """Trace X0 origins at every reachable RET in one already-bounded CFG."""
    if not isinstance(text, (bytes, bytearray, memoryview)):
        raise ValueError("AArch64 text must be bytes-like")
    if not isinstance(window, dict):
        raise ValueError("CFG window must be an object")
    if not isinstance(max_iterations, int) or max_iterations <= 0:
        raise ValueError("Dataflow iteration limit must be positive")
    try:
        start = int(window["window_start"], 16)
        end = int(window["window_end_exclusive"], 16)
        rows = window["decoded_reachable_instructions"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("CFG window metadata is incomplete") from exc
    if (start < 0 or end <= start or end > len(text)
            or (start & 3) or (end & 3) or not isinstance(rows, list)):
        raise ValueError("CFG window bounds or instruction rows are invalid")

    row_map = {int(row["pc"], 16): row for row in rows}
    if start not in row_map:
        raise ValueError("CFG start instruction is not reachable")
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True

    initial = {key: frozenset({"ENTRY_" + key.upper()}) for key in GPR_KEYS}
    initial["xzr"] = frozenset({"CONST(0x0)"})
    incoming = {start: initial}
    processed = {}
    queue = deque([start])
    queued = {start}
    returns = {}
    call_barriers = set()
    indirect_terminators = set()
    unresolved_edges = []
    iterations = 0

    while queue:
        pc = queue.popleft()
        queued.discard(pc)
        iterations += 1
        if iterations > max_iterations:
            raise ValueError("Return provenance dataflow did not converge")
        row = row_map.get(pc)
        if row is None:
            raise ValueError("CFG successor has no decoded instruction row")
        signature = tuple((key, tuple(sorted(value)))
                          for key, value in sorted(incoming[pc].items()))
        if processed.get(pc) == signature:
            continue
        processed[pc] = signature

        decoded = list(decoder.disasm(text[pc:pc + 4], pc))
        if len(decoded) != 1 or decoded[0].size != 4:
            raise ValueError("Reachable instruction cannot be decoded at " + _hex(pc))
        ins = decoded[0]
        out_state = _transfer(ins, incoming[pc], pc)
        successors = row.get("successors", [])
        for successor in successors:
            kind = successor.get("kind")
            target_text = successor.get("target")
            if kind in ("call", "indirect_call_unresolved"):
                if kind == "call":
                    call_barriers.add(pc)
                continue
            if kind == "return_or_indirect_terminator":
                if ins.mnemonic.lower() in RETURN_MNEMONICS:
                    value = _values(incoming[pc], "x0")
                    returns[pc] = (_merge_value(returns[pc], value)
                                   if pc in returns else value)
                else:
                    indirect_terminators.add(pc)
                continue
            if target_text is None:
                unresolved_edges.append({
                    "site": _hex(pc), "kind": kind, "target": None,
                })
                continue
            target = int(target_text, 16)
            if not start <= target < end or not successor.get("inside_analysis_window"):
                unresolved_edges.append({
                    "site": _hex(pc), "kind": kind, "target": target_text,
                })
                continue
            next_state = out_state
            if kind in ("fallthrough_after_call", "fallthrough_after_indirect_call"):
                call_barriers.add(pc)
                next_state = _call_clobber(out_state, pc)
            merged, changed = _merge_state(incoming.get(target), next_state)
            if changed:
                incoming[target] = merged
                if target not in queued:
                    queue.append(target)
                    queued.add(target)

    expected_returns = {int(value, 16) for value in window.get("return_sites", [])}
    observed_returns = set(returns)
    if expected_returns != observed_returns:
        raise ValueError("Return-state coverage differs from the bounded CFG return inventory")

    rows_out = []
    all_origins = set()
    for pc in sorted(returns):
        values = sorted(returns[pc])
        all_origins.update(values)
        rows_out.append({
            "return_site": _hex(pc),
            "x0_origins": values,
            "value_is_runtime_pointer": False,
            "semantic_return_type_verified": False,
        })
    if not rows_out:
        classification = "NO_RETURN_IN_BOUNDED_CFG"
    elif any(value.startswith("UNKNOWN") for value in all_origins):
        classification = "UNKNOWN_ON_ONE_OR_MORE_PATHS"
    elif len(all_origins) == 1:
        classification = "SINGLE_ORIGIN_ACROSS_RETURNS"
    else:
        classification = "PATH_DEPENDENT_ORIGINS"

    return {
        "classification": classification,
        "return_site_count": len(rows_out),
        "return_sites": rows_out,
        "x0_origin_union": sorted(all_origins),
        "call_barrier_sites": [_hex(value) for value in sorted(call_barriers)],
        "unresolved_indirect_terminators": [
            _hex(value) for value in sorted(indirect_terminators)
        ],
        "unresolved_edges": sorted(
            unresolved_edges,
            key=lambda row: (int(row["site"], 16), row["kind"], row["target"] or ""),
        ),
        "reachable_instruction_count": len(rows),
        "dataflow_iterations": iterations,
        "post_call_registers_are_unknown_without_callee_proof": True,
        "memory_values_are_symbolic_not_read_from_runtime_objects": True,
        "function_extent_verified": False,
    }


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    dispatch = inspect_dispatch(nso)
    call_rows = [
        row for row in dispatch["dispatch_flow"]["direct_call_sequence"]
        if row["site"] == _hex(CALL_SITE)
    ]
    if len(call_rows) != 1 or call_rows[0]["x0_source_before_call"] != "x20":
        raise ValueError("Pinned X0 source into the 0x116b82c call changed")

    rows, _memory = _read_image(nso)
    if len(rows) != 3 or rows[0][0] != 0:
        raise ValueError("Original NSO text layout changed")
    text = rows[0][1]
    window = analyze_window(text, TARGET, TARGET + WINDOW_BYTES)
    if window["return_sites"] != ["0x116b858", "0x116b870"]:
        raise ValueError("Pinned 0x116b82c bounded return-site inventory changed")
    expected_call = {"site": "0x116b864", "target": "0x12155a0"}
    if expected_call not in window["direct_calls_not_walked"]:
        raise ValueError("Pinned bounded diagnostic call at 0x116b864 changed")

    provenance = trace_return_registers(text, window)
    instruction_rows = {
        row["pc"]: row for row in window["decoded_reachable_instructions"]
    }

    def required_instruction(pc, mnemonic, operands):
        row = instruction_rows.get(pc)
        if row is None or row["mnemonic"] != mnemonic or row["operands"] != operands:
            raise ValueError("Pinned FileLoad table lookup instruction changed at " + pc)
        return row

    bounds_cmp = required_instruction("0x116b830", "cmp", "w1, #0x3f")
    bounds_branch = required_instruction("0x116b834", "b.hi", "#0x116b868")
    table_adrp = required_instruction("0x116b838", "adrp", "x8, #0x4371000")
    table_add = required_instruction("0x116b83c", "add", "x8, x8, #0x7d8")
    index_add = required_instruction("0x116b840", "add", "x8, x8, w1, uxtw #3")
    slot_load = required_instruction("0x116b844", "ldr", "x0, [x8, #0x28]")
    sentinel_value = required_instruction("0x116b848", "mov", "w8, #0x3f800000")
    sentinel_cmp = required_instruction("0x116b84c", "cmp", "x0, x8")
    sentinel_branch = required_instruction("0x116b850", "b.eq", "#0x116b85c")
    null_value = required_instruction("0x116b868", "mov", "x0, xzr")

    page = int(table_adrp["immediates"][0], 16)
    table_offset = int(table_add["immediates"][0], 16)
    load_displacement = slot_load["memory_operands"][0]["displacement"]
    computed_slot_base = page + table_offset + load_displacement
    slot_count = (TABLE_END - TABLE_START) // 8
    if computed_slot_base != TABLE_START or slot_count != 64:
        raise ValueError("Indexed helper load no longer resolves to the 64-slot table")
    if "uxtw #3" not in index_add["operands"] or "w1" not in index_add["operands"]:
        raise ValueError("Indexed helper no longer uses UXTW(W1)*8")
    return_sites = {row["return_site"]: row["x0_origins"]
                    for row in provenance["return_sites"]}
    if return_sites.get("0x116b858", [""])[0].startswith("UNKNOWN"):
        raise ValueError("Valid-slot return provenance remains unknown")
    if return_sites.get("0x116b870") != ["CONST(0x0)"]:
        raise ValueError("Error-path return is no longer proven null")

    table_lookup = {
        "slot_base": _hex(computed_slot_base),
        "slot_end_exclusive": _hex(TABLE_END),
        "slot_count": slot_count,
        "slot_stride_bytes": 8,
        "address_expression": "0x4371800 + UXTW(w1)*8",
        "index_register": "w1",
        "index_extension": "UXTW",
        "index_scale_bytes": 8,
        "index_min": 0,
        "index_max_inclusive": 0x3f,
        "bounds_compare_site": bounds_cmp["pc"],
        "bounds_compare_immediate": bounds_cmp["immediates"][0],
        "out_of_range_branch_site": bounds_branch["pc"],
        "out_of_range_branch_target": bounds_branch["immediates"][0],
        "slot_load_site": slot_load["pc"],
        "slot_load_width_bytes": slot_load["memory_operands"][0]["access_size_bytes"],
        "loaded_value_compare_site": sentinel_cmp["pc"],
        "loaded_value_sentinel": sentinel_value["immediates"][0],
        "sentinel_equal_branch_site": sentinel_branch["pc"],
        "valid_non_sentinel_return_site": "0x116b858",
        "valid_non_sentinel_return_x0_origins": return_sites["0x116b858"],
        "out_of_range_or_sentinel_return_site": "0x116b870",
        "out_of_range_or_sentinel_return_x0_origins": return_sites["0x116b870"],
        "runtime_slot_values_verified": False,
        "slot_value_semantic_type_verified": False,
    }
    return {
        "status": "PINNED_FILELOAD_RETURN_REGISTER_PROVENANCE_STATIC_ONLY",
        "original_main_sha256": digest,
        "target": _hex(TARGET),
        "target_window_sha256": window["window_sha256"],
        "target_window_reachable_instructions": window["reachable_decoded_words"],
        "caller_context": {
            "call_site": _hex(CALL_SITE),
            "x0_source_before_call": "x20",
            "x20_source": "post_call_x0_from_0x116b7b0",
            "x1_source_before_call": "w0_from_post_call_0x116d380",
            "caller_null_check": "0x116b3b8",
            "first_object_dereference": "0x116b3bc: LDR X8,[X0]",
            "second_object_dereference": "0x116b3c4: LDR X2,[X8,#0x58]",
            "indirect_branch": "0x116b3d0: BR X2",
            "semantic_object_type_verified": False,
        },
        "bounded_cfg": {
            "window_start": window["window_start"],
            "window_end_exclusive": window["window_end_exclusive"],
            "return_sites": window["return_sites"],
            "direct_calls_not_walked": window["direct_calls_not_walked"],
            "indirect_terminators": window["indirect_terminators"],
            "decoded_instructions": window["decoded_reachable_instructions"],
            "capstone_reported_x0_write_candidates": [
                row for row in window["decoded_reachable_instructions"]
                if {"x0", "w0"} & set(row["written_registers"])
            ],
            "compare_alias_write_candidates": [
                row for row in window["decoded_reachable_instructions"]
                if row["mnemonic"] in {"cmp", "cmn", "tst", "ccmp", "ccmn"}
                and {"x0", "w0"} & set(row["written_registers"])
            ],
        },
        "return_provenance": provenance,
        "table_lookup": table_lookup,
        "limits": {
            "function_identity_verified": False,
            "return_semantics_verified": False,
            "object_type_verified": False,
            "br_x2_target_resolved": False,
            "callback_identity_verified": False,
            "ownership_lifecycle_verified": False,
            "lock_unlock_async_rollback_unbind_destructor_verified": False,
            "native_consumer_abi_verified": False,
            "archive_precedence_verified": False,
            "native_hook_added": False,
            "emulated_arm64": False,
            "uzuy": False,
            "gameplay_verified": False,
            "full_moddingapi": False,
            "ready_for_gameplay_test": False,
            "emulator_tested": False,
        },
    }


if __name__ == "__main__":
    raise SystemExit("Use tests/test_fileload_return_provenance.py")
