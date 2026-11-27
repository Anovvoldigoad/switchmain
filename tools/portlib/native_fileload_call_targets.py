"""Bounded direct-callee register-effect inventory for original FileLoad.

This is a read-only call-target census. It records register writes and SP-relative
save/restore candidates from the pinned v1.70 image; it does not infer a calling
convention, function extent, ownership, or consumer ABI.
"""
import hashlib
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG

from .native_cpk_graph import MAIN_SHA256
from .native_cpk_cfg import _edges
from .native_fileload_corridor_cfg import ENTRY, END, inspect as inspect_fileload
from .nso_profile import segments

MAX_REACHED = 384
CALLEE_SPAN = 0x200
MAX_PRESERVATION_DEPTH = 12
MAX_PRESERVATION_TARGETS = 128
TRACKED = tuple(f"x{i}" for i in range(19, 29))
EXPECTED_PREFIX_CALLS = {
    0x116F43C: 0x116D3C0,
    0x116F444: 0x11708D8,
    0x116F458: 0x11709A0,
    0x116F45C: 0x116D420,
    0x116F47C: 0x1170FB0,
    0x116F48C: 0x11705F0,
    0x116F49C: 0x130B8,
    0x116F4E0: 0x12155A0,
    0x116F4F8: 0x12155A0,
    0x116F504: 0x12155A0,
    0x116F514: 0x12155A0,
}


def _canonical(name):
    name = name.lower()
    if name in ("fp", "lr"):
        return "x29" if name == "fp" else "x30"
    if len(name) > 1 and name[0] in ("x", "w") and name[1:].isdigit():
        n = int(name[1:])
        if 0 <= n <= 30:
            return "x" + str(n)
    return name if name in ("sp", "wsp") else None


def _instruction_effect(ins, pc, raw):
    try:
        reads, writes = ins.regs_access()
    except Exception as exc:
        raise ValueError("AArch64 register access decode failed at " + hex(pc)) from exc
    read_names = sorted({_canonical(ins.reg_name(r)) for r in reads} - {None})
    write_names = sorted({_canonical(ins.reg_name(r)) for r in writes} - {None})
    mem_rows = []
    for op in ins.operands:
        if op.type != ARM64_OP_MEM:
            continue
        base = ins.reg_name(op.mem.base) if op.mem.base else None
        index = ins.reg_name(op.mem.index) if op.mem.index else None
        direction = ("write" if ins.mnemonic.startswith("st") else
                     "read" if ins.mnemonic.startswith("ld") else "unknown")
        regs = []
        for candidate in ins.operands:
            if candidate.type == ARM64_OP_REG:
                name = _canonical(ins.reg_name(candidate.reg))
                if name in TRACKED:
                    regs.append(name)
        mem_rows.append({
            "base_register": base,
            "index_register": index,
            "displacement": op.mem.disp,
            "writeback": bool(getattr(ins, "writeback", False)),
            "direction": direction,
            "tracked_registers": sorted(set(regs)),
        })
    return {
        "pc": hex(pc),
        "word_le": raw.hex(),
        "mnemonic": ins.mnemonic,
        "operands": ins.op_str,
        "read_registers": read_names,
        "written_registers": write_names,
        "memory_operands": mem_rows,
    }


def analyze_window(code, start, end, max_reached=MAX_REACHED):
    if start < 0 or end > len(code) or end <= start or (start & 3) or (end & 3):
        raise ValueError("Invalid aligned callee analysis window")
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    decoded = {}
    graph = {}
    effects = {}
    for pc in range(start, end, 4):
        raw = code[pc:pc + 4]
        if len(raw) != 4:
            raise ValueError("Partial AArch64 instruction at window boundary")
        rows = list(decoder.disasm(raw, pc))
        if len(rows) != 1 or rows[0].size != 4:
            continue
        ins = rows[0]
        decoded[pc] = ins
        graph[pc] = _edges(pc, ins.mnemonic, ins.op_str)
        effects[pc] = _instruction_effect(ins, pc, raw)
    if start not in decoded:
        raise ValueError("Direct callee target is not a decoded AArch64 instruction")
    pending = deque([start])
    reachable = set()
    returns = set()
    nested_calls = set()
    indirect_calls = set()
    indirect_terminators = set()
    exits = set()
    while pending:
        pc = pending.popleft()
        if pc in reachable:
            continue
        if len(reachable) >= max_reached:
            raise ValueError("Callee CFG node budget exceeded")
        ins = decoded.get(pc)
        if ins is None:
            exits.add((pc, "undecodable", None))
            continue
        reachable.add(pc)
        for kind, target in graph[pc]:
            if kind == "call":
                nested_calls.add((pc, target))
                continue
            if kind == "indirect_call_unresolved":
                indirect_calls.add(pc)
                continue
            if target is None:
                if kind == "return_or_indirect_terminator":
                    if ins.mnemonic in ("ret", "retaa", "retab"):
                        returns.add(pc)
                    else:
                        indirect_terminators.add(pc)
                else:
                    exits.add((pc, kind, None))
                continue
            if not start <= target < end:
                exits.add((pc, kind, target))
                continue
            if target not in decoded:
                exits.add((pc, "undecodable_successor", target))
                continue
            pending.append(target)
    ordered = [effects[pc] for pc in sorted(reachable)]
    register_effects = {}
    for reg in TRACKED:
        writes = []
        stack_accesses = []
        for row in ordered:
            if reg in row["written_registers"]:
                writes.append({k: row[k] for k in ("pc", "word_le", "mnemonic", "operands")})
            for mem in row["memory_operands"]:
                if reg not in mem["tracked_registers"]:
                    continue
                stack_accesses.append({
                    "pc": row["pc"], "word_le": row["word_le"],
                    "mnemonic": row["mnemonic"], "operands": row["operands"],
                    **mem,
                })
        stores = [x for x in stack_accesses
                  if x["direction"] == "write" and x["base_register"] == "sp"
                  and x["index_register"] is None and not x["writeback"]]
        loads = [x for x in stack_accesses
                 if x["direction"] == "read" and x["base_register"] == "sp"
                 and x["index_register"] is None and not x["writeback"]]
        pairs = []
        for store in stores:
            for load in loads:
                if store["displacement"] == load["displacement"] and int(store["pc"], 16) < int(load["pc"], 16):
                    pairs.append({"store_pc": store["pc"], "load_pc": load["pc"],
                                  "sp_displacement": store["displacement"]})
        register_effects[reg] = {
            "writes": writes,
            "stack_accesses": stack_accesses,
            "same_displacement_stack_store_load_candidates": pairs,
            "preservation_proven": False,
        }
    return {
        "target": hex(start),
        "window_end_exclusive": hex(end),
        "window_sha256": hashlib.sha256(code[start:end]).hexdigest(),
        "bounded_window_not_function_extent": True,
        "reachable_instructions": len(reachable),
        "return_sites": [hex(x) for x in sorted(returns)],
        "nested_direct_calls": [{"site": hex(a), "target": hex(b)}
                                for a, b in sorted(nested_calls)],
        "unresolved_indirect_calls": [hex(x) for x in sorted(indirect_calls)],
        "indirect_terminators": [hex(x) for x in sorted(indirect_terminators)],
        "other_or_out_of_window_exits": [
            {"from": hex(a), "kind": b, "target": hex(c) if c is not None else None}
            for a, b, c in sorted(exits, key=lambda x: (x[0], x[1], x[2] or 0))
        ],
        "register_effects": register_effects,
        "preservation_proven": False,
    }




def analyze_stack_register_restore(
        code, start, end, reg, max_states=4096,
        initial_register_offsets=None, entry_sp_delta=0,
        protected_slots=(), active_targets=(), depth=0, budget=None):
    """Prove bounded X-register preservation with interprocedural stack aliases.

    Stack-relative pointer arguments are propagated through exact MOV/ADD/SUB
    definitions. Direct callees are recursively checked for register restore,
    balanced SP, and writes that could alias protected caller stack slots.
    Unknown pointers, indirect calls, unresolved edges, and bounded-window
    escapes fail closed. This is static evidence, not a platform ABI claim.
    """
    if reg not in TRACKED:
        raise ValueError("Stack restore analysis supports only tracked X19-X28")
    if start < 0 or end > len(code) or end <= start or (start & 3) or (end & 3):
        raise ValueError("Invalid aligned stack-restore analysis window")
    if not isinstance(entry_sp_delta, int):
        raise ValueError("Entry SP delta must be a proven integer")

    def failed(reason):
        digest = (hashlib.sha256(code[start:end]).hexdigest()
                  if 0 <= start < end <= len(code) else None)
        return {
            "target": hex(start),
            "window_end_exclusive": hex(end),
            "window_sha256": digest,
            "bounded_window_not_function_extent": True,
            "reachable_instructions": [],
            "return_states": [],
            "save_sites": [],
            "restore_sites": [],
            "nested_calls": [],
            "nested_call_proofs": [],
            "unknown_memory_writes_while_saved": [],
            "protected_slot_clobbers": [],
            "unresolved_control_flow_edges": [],
            "all_return_paths_restore_entry_register": False,
            "sp_balanced_on_all_returns": False,
            "sp_delta_trusted_on_all_returns": False,
            "state_budget_exceeded": reason in (
                "STACK_RESTORE_STATE_BUDGET", "CALL_DEPTH_LIMIT",
                "CALL_TARGET_BUDGET"),
            "local_restore_on_all_returns": False,
            "preservation_proven": False,
            "initial_register_offsets": dict(initial_register_offsets or {}),
            "entry_sp_delta": entry_sp_delta,
            "protected_slots": sorted(set(protected_slots)),
            "reason": reason,
        }

    if start in active_targets:
        return failed("CALL_GRAPH_CYCLE")
    if depth >= MAX_PRESERVATION_DEPTH:
        return failed("CALL_DEPTH_LIMIT")
    if budget is None:
        budget = {"targets": 0}
    budget["targets"] = budget.get("targets", 0) + 1
    if budget["targets"] > MAX_PRESERVATION_TARGETS:
        return failed("CALL_TARGET_BUDGET")

    active_targets = tuple(active_targets) + (start,)
    protected_slots = tuple(sorted(set(
        x for x in protected_slots if isinstance(x, int)
    )))
    initial_offsets = {}
    for name, value in (initial_register_offsets or {}).items():
        canonical = _canonical(name)
        if canonical and canonical != "sp" and isinstance(value, int):
            initial_offsets[canonical] = value

    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    decoded = {}
    rows = {}
    for pc in range(start, end, 4):
        raw = code[pc:pc + 4]
        if len(raw) != 4:
            return failed("PARTIAL_INSTRUCTION_WINDOW")
        insns = list(decoder.disasm(raw, pc))
        if len(insns) == 1 and insns[0].size == 4:
            decoded[pc] = insns[0]
            rows[pc] = _instruction_effect(insns[0], pc, raw)
    if start not in decoded:
        return failed("STACK_RESTORE_TARGET_UNDECODED")

    def reg_width(name):
        name = name.lower()
        if name in ("xzr", "fp", "lr"):
            return 8
        if name == "wzr":
            return 4
        if name.startswith("x") and name[1:].isdigit():
            return 8
        if name.startswith("w") and name[1:].isdigit():
            return 4
        if name.startswith("s") and name[1:].isdigit():
            return 4
        if name.startswith("d") and name[1:].isdigit():
            return 8
        if name.startswith("q") and name[1:].isdigit():
            return 16
        return None

    def is_64_register(name):
        name = name.lower()
        return name.startswith("x") and name[1:].isdigit() or name in ("fp", "lr")

    def transfers(ins, mem_index):
        mnemonic = ins.mnemonic.lower()
        if mnemonic not in (
            "str", "stur", "stp", "stnp", "strb", "sturb", "strh", "sturh",
            "ldr", "ldur", "ldp", "ldnp", "ldrb", "ldurb", "ldrh", "ldurh",
        ):
            return None
        override = (1 if mnemonic in ("strb", "sturb", "ldrb", "ldurb")
                    else 2 if mnemonic in ("strh", "sturh", "ldrh", "ldurh")
                    else None)
        result = []
        for operand in ins.operands[:mem_index]:
            if operand.type != ARM64_OP_REG:
                continue
            raw_name = ins.reg_name(operand.reg)
            result.append((_canonical(raw_name),
                           override if override is not None else reg_width(raw_name)))
        pair = mnemonic in ("stp", "stnp", "ldp", "ldnp")
        if len(result) != (2 if pair else 1):
            return None
        if any(width is None or width <= 0 for _, width in result):
            return None
        return result

    def overlaps(a, aw, b, bw=8):
        return a < b + bw and b < a + aw

    pending = deque([(
        start, entry_sp_delta, True, "entry", (),
        tuple(sorted(initial_offsets.items())), ()
    )])
    visited = set()
    return_states = []
    nested_calls = {}
    nested_call_proofs = {}
    unknown_memory_writes = {}
    protected_slot_clobbers = {}
    unresolved_edges = {}
    save_sites = {}
    restore_sites = {}
    reachable_rows = {}
    budget_exceeded = False

    while pending:
        pc, sp_delta, sp_trusted, origin, slot_items, pointer_items, pointer_slot_items = pending.popleft()
        state = (pc, sp_delta, sp_trusted, origin, slot_items, pointer_items, pointer_slot_items)
        if state in visited:
            continue
        if len(visited) >= max_states:
            budget_exceeded = True
            break
        visited.add(state)
        ins = decoded.get(pc)
        if ins is None:
            unresolved_edges[(pc, "undecodable", None)] = True
            continue

        reachable_rows[pc] = rows[pc]
        slots = dict(slot_items)
        pointer_offsets = dict(pointer_items)
        pointer_slots = dict(pointer_slot_items)
        old_pointer_offsets = dict(pointer_offsets)
        pointer_restores = {}
        pointer_writeback_updates = {}
        next_delta = sp_delta
        next_trusted = sp_trusted
        next_origin = origin
        restored_register = False
        sp_writeback_handled = False
        current_sp_delta = sp_delta
        mem_ops = [(i, op) for i, op in enumerate(ins.operands)
                   if op.type == ARM64_OP_MEM]

        def apply_transfer(address, transfer_rows, base_is_sp):
            nonlocal next_origin, restored_register
            offset = address
            for name, width in transfer_rows:
                if ins.mnemonic.lower().startswith("st"):
                    for saved_offset in list(slots):
                        if overlaps(offset, width, saved_offset):
                            slots[saved_offset] = "other"
                    for protected in protected_slots:
                        if overlaps(offset, width, protected):
                            protected_slot_clobbers[(pc, protected, offset, width)] = True
                    for pointer_slot in list(pointer_slots):
                        if overlaps(offset, width, pointer_slot):
                            pointer_slots.pop(pointer_slot, None)
                    if base_is_sp and name == reg:
                        slots[offset] = origin if width == 8 else "other"
                        save_sites[(pc, offset, width, origin)] = True
                    if (base_is_sp and name is not None and width == 8
                            and name in old_pointer_offsets):
                        pointer_slots[offset] = old_pointer_offsets[name]
                elif ins.mnemonic.lower().startswith("ld"):
                    if base_is_sp and name == reg:
                        if width == 8 and slots.get(offset) == "entry":
                            next_origin = "entry"
                            restored_register = True
                            slots.pop(offset, None)
                            restore_sites[(pc, offset, width)] = True
                        else:
                            next_origin = "other"
                    if base_is_sp and name is not None:
                        if width == 8 and offset in pointer_slots:
                            pointer_restores[name] = pointer_slots.pop(offset)
                        else:
                            pointer_restores.pop(name, None)
                    elif not base_is_sp and name == reg:
                        next_origin = "other"
                offset += width

        for mem_index, operand in mem_ops:
            base = (_canonical(ins.reg_name(operand.mem.base))
                    if operand.mem.base else None)
            index = (_canonical(ins.reg_name(operand.mem.index))
                     if operand.mem.index else None)
            mnemonic = ins.mnemonic.lower()
            is_store = mnemonic.startswith("st")
            is_load = mnemonic.startswith("ld")
            if base == "sp":
                if index is not None:
                    if is_store and (slots or protected_slots):
                        unknown_memory_writes[(pc, base, index, ins.op_str)] = True
                    if ins.writeback:
                        next_delta = None
                        next_trusted = False
                        sp_writeback_handled = True
                    if is_load and reg in rows[pc]["written_registers"]:
                        next_origin = "other"
                    continue
                pre_index = bool(ins.writeback and "]!" in ins.op_str)
                post_index = bool(ins.writeback and "], #" in ins.op_str)
                if ins.writeback and not (pre_index or post_index):
                    next_delta = None
                    next_trusted = False
                    sp_writeback_handled = True
                    continue
                if pre_index:
                    address = (next_delta + operand.mem.disp
                               if next_delta is not None else None)
                    next_delta = address
                    if address is None:
                        next_trusted = False
                    sp_writeback_handled = True
                elif post_index:
                    address = next_delta
                    post = (ins.operands[-1].imm
                            if ins.operands and ins.operands[-1].type == ARM64_OP_IMM
                            else None)
                    if next_delta is not None and post is not None:
                        next_delta += post
                    else:
                        next_delta = None
                        next_trusted = False
                    sp_writeback_handled = True
                else:
                    address = (next_delta + operand.mem.disp
                               if next_delta is not None else None)
                if not (is_store or is_load):
                    continue
                transfer_rows = transfers(ins, mem_index)
                if address is None or transfer_rows is None:
                    if is_store and (slots or protected_slots):
                        unknown_memory_writes[(pc, base, index, ins.op_str)] = True
                    if is_load and reg in rows[pc]["written_registers"]:
                        next_origin = "other"
                    continue
                apply_transfer(address, transfer_rows, True)
                continue

            if base in pointer_offsets and index is None:
                base_offset = pointer_offsets[base]
                pre_index = bool(ins.writeback and "]!" in ins.op_str)
                post_index = bool(ins.writeback and "], #" in ins.op_str)
                if ins.writeback and not (pre_index or post_index):
                    address = None
                    pointer_writeback_updates[base] = None
                elif pre_index:
                    address = base_offset + operand.mem.disp
                    pointer_writeback_updates[base] = address
                elif post_index:
                    address = base_offset
                    post = (ins.operands[-1].imm
                            if ins.operands and ins.operands[-1].type == ARM64_OP_IMM
                            else None)
                    pointer_writeback_updates[base] = (
                        base_offset + post if post is not None else None
                    )
                else:
                    address = base_offset + operand.mem.disp
                if not (is_store or is_load):
                    continue
                transfer_rows = transfers(ins, mem_index)
                if address is None or transfer_rows is None:
                    if is_store and (slots or protected_slots):
                        unknown_memory_writes[(pc, base, index, ins.op_str)] = True
                    if is_load and reg in rows[pc]["written_registers"]:
                        next_origin = "other"
                    continue
                apply_transfer(address, transfer_rows, False)
                continue

            if is_store and (slots or protected_slots):
                unknown_memory_writes[(pc, base, index, ins.op_str)] = True
            if is_load and reg in rows[pc]["written_registers"]:
                next_origin = "other"
            if ins.writeback and base is not None:
                pointer_writeback_updates[base] = None

        reads, writes = ins.regs_access()
        read_names = {_canonical(ins.reg_name(x)) for x in reads}
        write_names = {_canonical(ins.reg_name(x)) for x in writes}
        if reg in write_names and not restored_register:
            if not (ins.mnemonic.lower() in ("mov", "orr") and reg in read_names):
                next_origin = "other"

        for name in write_names:
            if name is not None:
                pointer_offsets.pop(name, None)
        pointer_offsets.update(pointer_restores)
        for name, value in pointer_writeback_updates.items():
            if value is None:
                pointer_offsets.pop(name, None)
            else:
                pointer_offsets[name] = value

        ops = ins.operands
        mnemonic = ins.mnemonic.lower()
        if (mnemonic == "mov" and len(ops) == 2
                and ops[0].type == ARM64_OP_REG and ops[1].type == ARM64_OP_REG):
            dest_raw = ins.reg_name(ops[0].reg)
            source_raw = ins.reg_name(ops[1].reg)
            dest = _canonical(dest_raw)
            source = _canonical(source_raw)
            if is_64_register(dest_raw) and is_64_register(source_raw):
                if source in old_pointer_offsets and dest != "sp":
                    pointer_offsets[dest] = old_pointer_offsets[source]
                elif source == "sp" and dest != "sp" and current_sp_delta is not None:
                    pointer_offsets[dest] = current_sp_delta
        elif (mnemonic in ("add", "sub") and len(ops) == 3
              and ops[0].type == ARM64_OP_REG
              and ops[1].type == ARM64_OP_REG
              and ops[2].type == ARM64_OP_IMM):
            dest_raw = ins.reg_name(ops[0].reg)
            source_raw = ins.reg_name(ops[1].reg)
            dest = _canonical(dest_raw)
            source = _canonical(source_raw)
            shift = getattr(ops[2], "shift", None)
            shift_value = getattr(shift, "value", 0) if shift is not None else 0
            if is_64_register(dest_raw) and dest != "sp" and shift_value == 0:
                base_offset = (current_sp_delta if source == "sp"
                               else old_pointer_offsets.get(source))
                if base_offset is not None:
                    amount = ops[2].imm * (1 if mnemonic == "add" else -1)
                    pointer_offsets[dest] = base_offset + amount

        if "sp" in write_names and not sp_writeback_handled:
            if (mnemonic in ("add", "sub") and len(ops) == 3
                    and ops[0].type == ARM64_OP_REG
                    and ops[1].type == ARM64_OP_REG
                    and ops[2].type == ARM64_OP_IMM
                    and _canonical(ins.reg_name(ops[0].reg)) == "sp"
                    and _canonical(ins.reg_name(ops[1].reg)) == "sp"):
                amount = ops[2].imm * (1 if mnemonic == "add" else -1)
                next_delta = next_delta + amount if next_delta is not None else None
            else:
                next_delta = None
                next_trusted = False

        for kind, target in _edges(pc, ins.mnemonic, ins.op_str):
            if kind == "call":
                nested_calls[(pc, target)] = True
                child = failed("BOUNDED_WINDOW_OUT_OF_RANGE")
                if (target is not None and next_delta is not None
                        and 0 <= target and not (target & 3)
                        and target + CALLEE_SPAN <= len(code)):
                    child = analyze_stack_register_restore(
                        code, target, target + CALLEE_SPAN, reg,
                        max_states=max_states,
                        initial_register_offsets=pointer_offsets,
                        entry_sp_delta=next_delta,
                        protected_slots=tuple(sorted(
                            set(protected_slots) | set(slots.keys())
                        )),
                        active_targets=active_targets,
                        depth=depth + 1,
                        budget=budget,
                    )
                nested_call_proofs[(pc, target)] = {
                    "site": hex(pc),
                    "target": hex(target) if target is not None else None,
                    "preserved": child["preservation_proven"],
                    "reason": child["reason"],
                    "window_sha256": child.get("window_sha256"),
                    "reachable_instructions": len(child.get("reachable_instructions", [])),
                    "sp_balanced_on_all_returns": child["sp_balanced_on_all_returns"],
                    "sp_delta_trusted_on_all_returns": child["sp_delta_trusted_on_all_returns"],
                    "unknown_memory_write_count": len(child["unknown_memory_writes_while_saved"]),
                    "protected_slot_clobber_count": len(child["protected_slot_clobbers"]),
                }
                if child["preservation_proven"]:
                    next_trusted = (next_trusted
                                    and child["sp_balanced_on_all_returns"]
                                    and child["sp_delta_trusted_on_all_returns"])
                    pointer_offsets = ({reg: pointer_offsets[reg]}
                                       if reg in pointer_offsets else {})
                    pointer_slots = {}
                else:
                    next_origin = "other"
                    next_trusted = False
                    pointer_offsets = {}
                    pointer_slots = {}
                    for clobber in child["protected_slot_clobbers"]:
                        slot = clobber["protected_slot"]
                        if slot in slots:
                            slots[slot] = "other"
                if child["state_budget_exceeded"]:
                    budget_exceeded = True
                continue
            if kind == "indirect_call_unresolved":
                nested_calls[(pc, None)] = True
                nested_call_proofs[(pc, None)] = {
                    "site": hex(pc), "target": None, "preserved": False,
                    "reason": "INDIRECT_CALL_UNRESOLVED",
                    "window_sha256": None, "reachable_instructions": 0,
                    "sp_balanced_on_all_returns": False,
                    "sp_delta_trusted_on_all_returns": False,
                    "unknown_memory_write_count": 0,
                    "protected_slot_clobber_count": 0,
                }
                next_origin = "other"
                next_trusted = False
                pointer_offsets = {}
                pointer_slots = {}
                continue
            if kind == "return_or_indirect_terminator":
                if ins.mnemonic.lower() in ("ret", "retaa", "retab"):
                    return_states.append({
                        "pc": hex(pc),
                        "sp_delta": next_delta,
                        "sp_delta_trusted": next_trusted,
                        "register_origin": next_origin,
                        "saved_entry_slots": sorted(
                            hex(offset) for offset, value in slots.items()
                            if value == "entry"
                        ),
                    })
                else:
                    unresolved_edges[(pc, kind, None)] = True
                continue
            if target is None:
                unresolved_edges[(pc, kind, None)] = True
                continue
            if not start <= target < end:
                unresolved_edges[(pc, kind, target)] = True
                continue
            if target not in decoded:
                unresolved_edges[(pc, "undecodable_successor", target)] = True
                continue
            pending.append((
                target, next_delta, next_trusted, next_origin,
                tuple(sorted(slots.items())),
                tuple(sorted(pointer_offsets.items())),
                tuple(sorted(pointer_slots.items())),
            ))

    all_return_paths_restore = bool(return_states) and all(
        row["register_origin"] == "entry" for row in return_states
    )
    sp_balanced = bool(return_states) and all(
        row["sp_delta"] == entry_sp_delta for row in return_states
    )
    sp_trusted = bool(return_states) and all(
        row["sp_delta_trusted"] for row in return_states
    )
    nested = [
        {"site": hex(site), "target": hex(target) if target is not None else None}
        for site, target in sorted(nested_calls, key=lambda x: (x[0], x[1] or 0))
    ]
    nested_proofs = [
        nested_call_proofs[key]
        for key in sorted(nested_call_proofs, key=lambda x: (x[0], x[1] or 0))
    ]
    unknown_writes = [
        {"pc": hex(pc), "base_register": base, "index_register": index,
         "instruction": operands}
        for pc, base, index, operands in sorted(unknown_memory_writes)
    ]
    protected_clobbers = [
        {"pc": hex(pc), "protected_slot": slot,
         "write_address": hex(address), "write_width": width}
        for pc, slot, address, width in sorted(protected_slot_clobbers)
    ]
    unresolved = [
        {"from": hex(pc), "kind": kind,
         "target": hex(target) if target is not None else None}
        for pc, kind, target in sorted(unresolved_edges, key=lambda x: (x[0], x[1], x[2] or 0))
    ]
    nested_failed = any(not row["preserved"] for row in nested_proofs)
    proven = (all_return_paths_restore and sp_balanced and sp_trusted
              and not nested_failed and not unknown_writes
              and not protected_clobbers and not unresolved
              and not budget_exceeded)
    if budget_exceeded:
        reason = "STACK_RESTORE_STATE_OR_CALL_BUDGET"
    elif not return_states:
        reason = "NO_REACHABLE_RETURN"
    elif not all_return_paths_restore:
        reason = "ENTRY_REGISTER_NOT_RESTORED_ON_ALL_RETURNS"
    elif not sp_balanced:
        reason = "SP_NOT_BALANCED_ON_ALL_RETURNS"
    elif not sp_trusted:
        reason = "SP_DELTA_UNVERIFIED"
    elif nested_failed:
        reason = "NESTED_CALL_STACK_EFFECT_UNPROVEN"
    elif unknown_writes:
        reason = "UNKNOWN_MEMORY_ALIAS_STORE"
    elif protected_clobbers:
        reason = "PROTECTED_CALLER_STACK_SLOT_CLOBBERED"
    elif unresolved:
        reason = "UNRESOLVED_CONTROL_FLOW_EDGE"
    elif not any(reg in row["written_registers"] for row in reachable_rows.values()):
        reason = "REGISTER_UNCHANGED_ALL_RETURN_PATHS"
    else:
        reason = "STACK_SLOT_RESTORED_ALL_RETURN_PATHS"

    return {
        "target": hex(start),
        "window_end_exclusive": hex(end),
        "window_sha256": hashlib.sha256(code[start:end]).hexdigest(),
        "bounded_window_not_function_extent": True,
        "reachable_instructions": [reachable_rows[pc] for pc in sorted(reachable_rows)],
        "return_states": return_states,
        "save_sites": [
            {"pc": hex(pc), "entry_sp_slot": hex(offset), "width": width,
             "saved_register_origin": value}
            for pc, offset, width, value in sorted(save_sites)
        ],
        "restore_sites": [
            {"pc": hex(pc), "entry_sp_slot": hex(offset), "width": width}
            for pc, offset, width in sorted(restore_sites)
        ],
        "nested_calls": nested,
        "nested_call_proofs": nested_proofs,
        "unknown_memory_writes_while_saved": unknown_writes,
        "protected_slot_clobbers": protected_clobbers,
        "unresolved_control_flow_edges": unresolved,
        "all_return_paths_restore_entry_register": all_return_paths_restore,
        "sp_balanced_on_all_returns": sp_balanced,
        "sp_delta_trusted_on_all_returns": sp_trusted,
        "state_budget_exceeded": budget_exceeded,
        "local_restore_on_all_returns": all_return_paths_restore,
        "preservation_proven": proven,
        "initial_register_offsets": dict(initial_offsets),
        "entry_sp_delta": entry_sp_delta,
        "protected_slots": list(protected_slots),
        "stack_memory_alias_proven": not unknown_writes and not protected_clobbers and not nested_failed,
        "nested_call_stack_effects_proven": not nested_failed,
        "reason": reason,
    }


def prove_register_preservation(code, target, reg, cache=None, active=(), depth=0, initial_register_offsets=None):
    """Conservatively prove one register untouched across a bounded direct callee.

    No platform ABI is assumed. A proof requires every reachable path to return
    inside the bounded window, no writes to the tracked register, no indirect or
    out-of-window exits, and recursively proven direct callees. Spill/restore
    patterns are intentionally unresolved until their stack effects are proven.
    """
    if reg not in TRACKED:
        raise ValueError("Register-preservation proof supports only tracked X19-X28")
    if cache is None:
        cache = {}
    key = (target, reg)
    cache_key = (target, reg, tuple(sorted((initial_register_offsets or {}).items())))
    if not initial_register_offsets:
        cache_key = key
    if key in active:
        return {"target": hex(target), "register": reg, "preserved": False,
                "reason": "CALL_GRAPH_CYCLE", "bounded_window_not_function_extent": True}
    if cache_key in cache:
        return dict(cache[cache_key])
    if depth >= MAX_PRESERVATION_DEPTH:
        return {"target": hex(target), "register": reg, "preserved": False,
                "reason": "CALL_DEPTH_LIMIT", "bounded_window_not_function_extent": True}
    if len(cache) >= MAX_PRESERVATION_TARGETS:
        return {"target": hex(target), "register": reg, "preserved": False,
                "reason": "CALL_TARGET_BUDGET", "bounded_window_not_function_extent": True}
    end = target + CALLEE_SPAN
    if target < 0 or target & 3 or end > len(code):
        return {"target": hex(target), "register": reg, "preserved": False,
                "reason": "BOUNDED_WINDOW_OUT_OF_RANGE",
                "bounded_window_not_function_extent": True}
    try:
        report = analyze_window(code, target, end)
    except ValueError as exc:
        return {"target": hex(target), "register": reg, "preserved": False,
                "reason": "BOUNDED_CFG_UNRESOLVED", "detail": str(exc),
                "bounded_window_not_function_extent": True}
    base = {
        "target": hex(target), "register": reg,
        "window_end_exclusive": hex(end),
        "window_sha256": report["window_sha256"],
        "reachable_instructions": report["reachable_instructions"],
        "return_sites": report["return_sites"],
        "bounded_window_not_function_extent": True,
        "register_write_sites": report["register_effects"][reg]["writes"],
        "unresolved_indirect_calls": report["unresolved_indirect_calls"],
        "indirect_terminators": report["indirect_terminators"],
        "other_or_out_of_window_exits": report["other_or_out_of_window_exits"],
        "nested_direct_calls": report["nested_direct_calls"],
    }
    if base["register_write_sites"]:
        if reg == "x19":
            try:
                stack_restore = analyze_stack_register_restore(
                    code, target, end, reg,
                    initial_register_offsets=initial_register_offsets,
                    active_targets=tuple(x[0] for x in active), depth=depth,
                )
            except ValueError as exc:
                stack_restore = {
                    "target": hex(target), "register": reg,
                    "preservation_proven": False,
                    "reason": "STACK_RESTORE_ANALYSIS_UNRESOLVED",
                    "detail": str(exc),
                    "bounded_window_not_function_extent": True,
                }
            base["stack_restore_analysis"] = stack_restore
            result = {
                **base,
                "preserved": stack_restore.get("preservation_proven") is True,
                "reason": (stack_restore.get("reason") if
                           stack_restore.get("preservation_proven") is not True
                           else "STACK_SLOT_RESTORED_ALL_RETURN_PATHS"),
            }
        else:
            result = {**base, "preserved": False, "reason": "REGISTER_WRITTEN"}
    elif base["other_or_out_of_window_exits"]:
        result = {**base, "preserved": False,
                  "reason": "OUT_OF_WINDOW_OR_UNDECODABLE_EDGE"}
    elif not base["return_sites"]:
        result = {**base, "preserved": False, "reason": "NO_REACHABLE_RETURN"}
    elif base["unresolved_indirect_calls"]:
        result = {**base, "preserved": False, "reason": "INDIRECT_CALL_UNRESOLVED"}
    elif base["indirect_terminators"]:
        result = {**base, "preserved": False, "reason": "INDIRECT_TERMINATOR_UNRESOLVED"}
    else:
        children = []
        for call in base["nested_direct_calls"]:
            child = prove_register_preservation(
                code, int(call["target"], 16), reg, cache,
                active + (key,), depth + 1
            )
            children.append({
                "site": call["site"], "target": call["target"],
                "preserved": child["preserved"], "reason": child["reason"]
            })
        failed = [x for x in children if not x["preserved"]]
        result = {
            **base, "nested_call_proofs": children,
            "preserved": not failed,
            "reason": ("NESTED_CALLEE_UNPROVEN" if failed else
                       "NO_REGISTER_WRITES_ALL_DIRECT_CALLEES_PROVEN")
        }
    cache[cache_key] = result
    return dict(result)


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Exact original Switch v1.70 main SHA256 required")
    va, code, _ = segments(nso)[0]
    if va != 0 or END > len(code):
        raise ValueError("Pinned original FileLoad text geometry invalid")
    corridor = inspect_fileload(nso)
    instructions = {int(row["offset"], 16): row
                    for row in corridor["reachable_instructions"]
                    if "offset" in row}
    calls = []
    for site in sorted(instructions):
        row = instructions[site]
        if row["mnemonic"] != "bl":
            continue
        target = int(row["operands"].split("#", 1)[1], 0)
        calls.append({"site": hex(site), "target": hex(target),
                      "word_le": row["word_le"], "instruction": row["operands"]})
    prefix = [x for x in calls if int(x["site"], 16) <= 0x116F514]
    observed = {int(x["site"], 16): int(x["target"], 16) for x in prefix}
    if observed != EXPECTED_PREFIX_CALLS:
        raise ValueError("Pinned FileLoad pre-status direct-call census changed")
    targets = sorted({int(x["target"], 16) for x in prefix})
    reports = []
    for target in targets:
        end = min(target + CALLEE_SPAN, len(code) & ~3)
        reports.append(analyze_window(code, target, end))
    last_prefix_site = max(int(x["site"], 16) for x in prefix)
    additional_calls = [x for x in calls
                        if int(x["site"], 16) > last_prefix_site]
    additional_targets = sorted(
        {int(x["target"], 16) for x in additional_calls} - set(targets)
    )
    additional_reports = []
    for target in additional_targets:
        end = min(target + CALLEE_SPAN, len(code) & ~3)
        try:
            additional_reports.append(analyze_window(code, target, end))
        except ValueError as exc:
            # A direct BL target which cannot be decoded stays explicit and
            # unresolved; it is never silently omitted from the call graph.
            additional_reports.append({
                "target": hex(target),
                "status": "UNRESOLVED",
                "reason": str(exc),
                "bounded_window_not_function_extent": True,
                "preservation_proven": False,
            })
    preservation_cache = {}
    call_preservation = []
    for call in prefix:
        target = int(call["target"], 16)
        call_preservation.append({
            "site": call["site"], "target": call["target"],
            "registers": {
                reg: prove_register_preservation(code, target, reg, preservation_cache)
                for reg in ("x20", "x22")
            }
        })
    return {
        "status": "PINNED_FILELOAD_DIRECT_CALLEE_REGISTER_EFFECT_INVENTORY_STATIC_ONLY",
        "original_main_sha256": digest,
        "fileload_entry": hex(ENTRY),
        "fileload_window_end_exclusive": hex(END),
        "pre_status_direct_calls": prefix,
        "all_reachable_direct_calls": calls,
        "unique_pre_status_targets": [hex(x) for x in targets],
        "target_reports": reports,
        "pre_status_call_register_preservation": call_preservation,
        "call_preservation_method": "exact-main bounded recursive direct-callee proof; no writes, all paths return, no indirect/out-of-window edges, nested direct calls recursively proven; stack spill/restore remains unresolved",
        "no_platform_calling_convention_assumed": True,
        "additional_reachable_direct_calls": additional_calls,
        "additional_unique_targets": [hex(x) for x in additional_targets],
        "additional_target_reports": additional_reports,
        "call_target_windows_are_not_function_boundaries": True,
        "register_preservation_proven": False,
        "consumer_abi_proven": False,
        "object_ownership_lifetime_proven": False,
        "callback_lock_async_rollback_unbind_destructor_proven": False,
        "archive_precedence_proven": False,
        "native_hook_installed": False,
        "gameplay_verified": False,
        "full_moddingapi": False,
        "ready_for_gameplay_test": False,
        "emulator_tested": False,
    }
