"""Bounded caller-argument provenance for the one direct FileLoad entry caller.

This is a syntactic, path-sensitive register-origin census over a fixed window.
It is not a function-boundary, pointer-type, ownership, or runtime-ABI proof.
"""
import hashlib
import struct
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64_const import ARM64_OP_MEM

from .native_cpk_cfg import _edges
from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileload_corrected_entry import NEW_CANDIDATE
from .nso_profile import segments

ENTRY = NEW_CANDIDATE
CALLSITE = 0x116F29C
WINDOW_START = CALLSITE - 0x200
WINDOW_END = CALLSITE + 4
TRACKED = ("x1", "x2")
MAX_EXTERNAL_INBOUND = 256


def _canon(name):
    if not name:
        return None
    name = name.lower()
    if name in ("wsp", "sp"):
        return "sp"
    if name in ("wzr", "xzr"):
        return None
    if name.startswith("w") and name[1:].isdigit():
        return "x" + name[1:]
    return name


def _row(ins, pc, raw):
    try:
        read_ids, write_ids = ins.regs_access()
    except Exception as exc:
        raise ValueError("AArch64 register access decode failed at " + hex(pc)) from exc
    reads = sorted({_canon(ins.reg_name(r)) for r in read_ids} - {None})
    writes = sorted({_canon(ins.reg_name(r)) for r in write_ids} - {None})
    memory = []
    for op in ins.operands:
        if op.type != ARM64_OP_MEM:
            continue
        memory.append({
            "base_register": _canon(ins.reg_name(op.mem.base)) if op.mem.base else None,
            "index_register": _canon(ins.reg_name(op.mem.index)) if op.mem.index else None,
            "displacement": op.mem.disp,
            "writeback": bool(getattr(ins, "writeback", False)),
        })
    return {
        "pc": hex(pc),
        "word_le": raw.hex(),
        "mnemonic": ins.mnemonic,
        "operands": ins.op_str,
        "read_registers": reads,
        "written_registers": writes,
        "memory_operands": memory,
    }


def _is_call(mnemonic):
    return mnemonic.startswith("bl") or mnemonic == "svc"


def _origin_kind(row):
    mnemonic = row["mnemonic"]
    reads = row["read_registers"]
    if mnemonic.startswith("ldr"):
        return "memory_load"
    if mnemonic in ("mov", "orr") and reads:
        return "register_copy"
    if mnemonic in ("add", "sub") and "sp" in reads:
        return "stack_relative_address"
    if mnemonic in ("adr", "adrp"):
        return "pc_relative_address"
    return "instruction_definition"


def analyze_caller_window(code, start, end, callsite, sink_target=None,
                          external_inbound=()):
    if start < 0 or end > len(code) or end <= start or (start & 3) or (end & 3):
        raise ValueError("Invalid aligned caller analysis window")
    if callsite < start or callsite + 4 > end or (callsite & 3):
        raise ValueError("Callsite is outside the caller analysis window")

    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoder.detail = True
    decoded = {}
    rows = {}
    decode_failures = []
    for pc in range(start, end, 4):
        raw = code[pc:pc + 4]
        insns = list(decoder.disasm(raw, pc))
        if len(insns) != 1 or insns[0].size != 4:
            decode_failures.append(hex(pc))
            continue
        decoded[pc] = insns[0]
        rows[pc] = _row(insns[0], pc, raw)
    if callsite not in decoded:
        raise ValueError("FileLoad caller BL is not a decoded AArch64 instruction")
    if sink_target is not None:
        word = struct.unpack_from("<I", code, callsite)[0]
        if direct_branch(word, callsite) != ("BL", sink_target):
            raise ValueError("Caller sink does not branch to the pinned FileLoad entry")

    graph = {}
    out_edges = []
    undecodable_targets = []
    for pc, ins in decoded.items():
        successors = set()
        if pc == callsite:
            graph[pc] = successors
            continue
        for kind, target in _edges(pc, ins.mnemonic, ins.op_str):
            if kind in ("call", "indirect_call_unresolved") or target is None:
                continue
            if start <= target < end:
                if target in decoded:
                    successors.add(target)
                else:
                    undecodable_targets.append({"from": hex(pc), "to": hex(target), "kind": kind})
            else:
                out_edges.append({"from": hex(pc), "to": hex(target), "kind": kind})
        graph[pc] = successors

    predecessors = {pc: set() for pc in decoded}
    for pc, successors in graph.items():
        for successor in successors:
            predecessors[successor].add(pc)

    external_rows = []
    external_targets = set()
    for edge in external_inbound:
        target = edge.get("target")
        if isinstance(target, int) and target in decoded:
            external_targets.add(target)
            if len(external_rows) < MAX_EXTERNAL_INBOUND:
                external_rows.append({
                    "from": hex(edge["source"]),
                    "to": hex(target),
                    "kind": edge.get("kind"),
                })

    roots = {pc for pc in decoded if not predecessors[pc]} | external_targets
    if not roots:
        roots = {min(decoded)}
    origin_info = {}

    def add_origin(key, info):
        origin_info[key] = info
        return key

    state_in = {pc: {reg: set() for reg in TRACKED} for pc in decoded}
    for root in roots:
        for reg in TRACKED:
            key = f"window_entry:{reg}:{root:x}"
            add_origin(key, {"kind": "window_entry_unknown", "register": reg, "at": hex(root)})
            state_in[root][reg].add(key)
    for target in external_targets:
        for reg in TRACKED:
            key = f"external_entry:{reg}:{target:x}"
            add_origin(key, {"kind": "external_entry_unknown", "register": reg, "at": hex(target)})
            state_in[target][reg].add(key)

    pending = deque(sorted(roots))
    queued = set(roots)
    while pending:
        pc = pending.popleft()
        queued.discard(pc)
        if pc == callsite:
            continue
        row = rows[pc]
        outgoing = {reg: set(state_in[pc][reg]) for reg in TRACKED}
        if _is_call(row["mnemonic"]):
            for reg in TRACKED:
                key = f"call_barrier:{reg}:{pc:x}"
                add_origin(key, {
                    "kind": "call_barrier",
                    "register": reg,
                    "at": hex(pc),
                    "instruction": row,
                })
                outgoing[reg] = {key}
        else:
            for reg in TRACKED:
                if reg in row["written_registers"]:
                    key = f"definition:{reg}:{pc:x}"
                    add_origin(key, {
                        "kind": "definition",
                        "register": reg,
                        "at": hex(pc),
                        "definition_kind": _origin_kind(row),
                        "instruction": row,
                    })
                    outgoing[reg] = {key}
        for successor in graph[pc]:
            changed = False
            for reg in TRACKED:
                before = len(state_in[successor][reg])
                state_in[successor][reg].update(outgoing[reg])
                changed |= len(state_in[successor][reg]) != before
            if changed and successor not in queued:
                pending.append(successor)
                queued.add(successor)

    sink_origins = {}
    for reg in TRACKED:
        sink_origins[reg] = [
            origin_info[key]
            for key in sorted(state_in[callsite][reg])
        ]

    complete = not decode_failures and not external_rows and not out_edges and not undecodable_targets
    return {
        "window_start": hex(start),
        "window_end_exclusive": hex(end),
        "window_sha256": hashlib.sha256(code[start:end]).hexdigest(),
        "window_is_not_a_proven_function_extent": True,
        "decoded_instruction_count": len(decoded),
        "expected_instruction_count": (end - start) // 4,
        "decode_failures": decode_failures[:64],
        "decode_failures_truncated": len(decode_failures) > 64,
        "callsite": hex(callsite),
        "callsite_word_le": code[callsite:callsite + 4].hex(),
        "sink_target": hex(sink_target) if sink_target is not None else None,
        "sink_reachable_from_bounded_window": bool(
            any(state_in[callsite][reg] for reg in TRACKED)
        ),
        "window_entry_roots": [hex(x) for x in sorted(roots)],
        "external_inbound_count": len(external_inbound),
        "external_inbound_scope": "direct B/BL only; conditional and indirect external entries remain unresolved",
        "external_inbound_edges": external_rows,
        "external_inbound_truncated": len(external_inbound) > MAX_EXTERNAL_INBOUND,
        "out_of_window_control_flow_edges": out_edges[:64],
        "out_of_window_edges_truncated": len(out_edges) > 64,
        "undecodable_branch_targets": undecodable_targets[:64],
        "bounded_window_complete": complete,
        "possible_reaching_definitions": sink_origins,
        "single_definition_proven_within_window": {
            reg: complete and len(sink_origins[reg]) == 1
                 and sink_origins[reg][0]["kind"] == "definition"
            for reg in TRACKED
        },
        "instructions": [rows[pc] for pc in sorted(rows)],
        "source_identity_proven": False,
        "source_register_origins_not_traced": True,
        "pointer_type_verified": False,
        "allocation_or_destructor_verified": False,
        "ownership_verified": False,
        "native_consumer_abi_verified": False,
    }


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original exact Switch v1.70 main SHA256 required")
    va, code, _ = segments(nso)[0]
    if va != 0 or WINDOW_END > len(code):
        raise ValueError("Pinned original text extent mismatch")
    word = struct.unpack_from("<I", code, CALLSITE)[0]
    if direct_branch(word, CALLSITE) != ("BL", ENTRY):
        raise ValueError("Unique FileLoad caller BL witness changed")

    incoming = []
    external = []
    for pc in range(0, len(code) - 3, 4):
        edge = direct_branch(struct.unpack_from("<I", code, pc)[0], pc)
        if edge is None:
            continue
        kind, target = edge
        if target == ENTRY:
            incoming.append({"source": pc, "kind": kind, "word_le": code[pc:pc + 4].hex()})
        if WINDOW_START <= target < WINDOW_END and not WINDOW_START <= pc < WINDOW_END:
            external.append({"source": pc, "target": target, "kind": kind})
    if incoming != [{"source": CALLSITE, "kind": "BL", "word_le": code[CALLSITE:CALLSITE + 4].hex()}]:
        raise ValueError("Original FileLoad direct caller census changed")
    caller = analyze_caller_window(
        code, WINDOW_START, WINDOW_END, CALLSITE, ENTRY, external
    )
    return {
        "status": "SHA_PINNED_FILELOAD_SINGLE_DIRECT_CALLER_ARGUMENT_ORIGINS_STATIC_ONLY",
        "original_main_sha256": digest,
        "entry": hex(ENTRY),
        "incoming_direct_call_count": len(incoming),
        "incoming_direct_calls": [
            {"source": hex(x["source"]), "kind": x["kind"], "word_le": x["word_le"]}
            for x in incoming
        ],
        "caller_window": caller,
        "caller_function_extent_verified": False,
        "caller_argument_identity_verified": False,
        "object_type_or_ownership_verified": False,
        "constructor_or_destructor_verified": False,
        "native_consumer_abi_verified": False,
        "callback_async_rollback_unbind_verified": False,
        "archive_precedence_verified": False,
        "native_hook_added": False,
        "gameplay_verified": False,
        "full_moddingapi": False,
        "ready_for_gameplay_test": False,
        "emulator_tested": False,
    }
