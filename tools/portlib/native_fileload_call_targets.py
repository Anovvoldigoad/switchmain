"""Bounded direct-callee register-effect inventory for original FileLoad.

This is a read-only call-target census. It records register writes and SP-relative
save/restore candidates from the pinned v1.70 image; it does not infer a calling
convention, function extent, ownership, or consumer ABI.
"""
import hashlib
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_MEM, ARM64_OP_REG

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


def prove_register_preservation(code, target, reg, cache=None, active=(), depth=0):
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
    if key in active:
        return {"target": hex(target), "register": reg, "preserved": False,
                "reason": "CALL_GRAPH_CYCLE", "bounded_window_not_function_extent": True}
    if key in cache:
        return dict(cache[key])
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
    cache[key] = result
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
