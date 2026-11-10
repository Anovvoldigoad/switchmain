"""Conservative read-only ARM64 direct-edge census near pinned FileOpen BR sites.

Edges are syntactic; a bounded window cannot establish complete predecessors,
runtime pointer values, call contracts, or engine consumer ownership.
"""
import hashlib
import struct
from .native_cpk_graph import MAIN_SHA256
from .nso_profile import segments
from .native_fileopen_br_provenance import SITES


def _signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def decode_edge(word, pc):
    """Return (kind, target, falls_through), never infer an indirect target."""
    if word & 0x7c000000 == 0x14000000:  # B / BL
        displacement = _signed(word & 0x3ffffff, 26) << 2
        call = bool(word & 0x80000000)
        return ("call" if call else "jump", pc + displacement, call)
    if word & 0xff000010 == 0x54000000:  # B.cond
        return ("conditional", pc + (_signed((word >> 5) & 0x7ffff, 19) << 2), True)
    if word & 0x7e000000 == 0x34000000:  # CBZ / CBNZ
        return ("conditional", pc + (_signed((word >> 5) & 0x7ffff, 19) << 2), True)
    if word & 0x7e000000 == 0x36000000:  # TBZ / TBNZ
        return ("conditional", pc + (_signed((word >> 5) & 0x3fff, 14) << 2), True)
    if word & 0xfffffc1f == 0xd63f0000:  # BLR: opaque indirect callee, returns syntactically
        return ("indirect_call", None, True)
    if word in (0xd65f0bff, 0xd65f0fff):  # RETAA / RETAB (authenticated returns)
        return ("indirect_or_return", None, False)
    if word & 0xfffffc1f in (0xd61f0000, 0xd65f0000, 0xd69f0000):
        return ("indirect_or_return", None, False)
    return ("linear_or_unclassified", None, True)


def census(code, base, site, window=128):
    if not 1 <= window <= 512 or base % 4 or site % 4 or site < base or site + 4 > base + len(code):
        raise ValueError("Invalid aligned bounded code window")
    start = max(base, site - 4 * window)
    edges = []
    unresolved = []
    indirect_calls = []
    incoming = {}
    for pc in range(start, site + 4, 4):
        word = struct.unpack_from("<I", code, pc - base)[0]
        kind, target, fallthrough = decode_edge(word, pc)
        if kind == "indirect_call":
            indirect_calls.append(hex(pc))
        if target is not None:
            row = {"from": hex(pc), "to": hex(target), "kind": kind,
                   "within_window": start <= target <= site}
            edges.append(row)
            if row["within_window"]:
                incoming.setdefault(target, []).append(pc)
            else:
                unresolved.append(row)
        if fallthrough and pc < site:
            incoming.setdefault(pc + 4, []).append(pc)
    # Window start is only a hypothetical entry, not a proven function entry.
    successors = {}
    for pc in range(start, site + 4, 4):
        word = struct.unpack_from("<I", code, pc - base)[0]
        kind, target, fallthrough = decode_edge(word, pc)
        next_pc = []
        if target is not None and start <= target <= site and kind != "call":
            next_pc.append(target)
        if fallthrough and pc < site:
            next_pc.append(pc + 4)
        successors[pc] = next_pc
    reachable = set()
    pending = [start]
    while pending:
        pc = pending.pop()
        if pc in reachable:
            continue
        reachable.add(pc)
        pending.extend(x for x in successors[pc] if x not in reachable)
    reachable_merges = [hex(pc) for pc, preds in sorted(incoming.items())
                        if pc in reachable and len({p for p in preds
                        if p in reachable and pc in successors[p]}) > 1]
    merges = [{"address": hex(pc), "predecessors": sorted(hex(x) for x in set(pred))}
              for pc, pred in sorted(incoming.items())
              if len(set(pred)) > 1]
    return {"site": hex(site), "window_start": hex(start),
            "window_entry_reachable_instructions": len(reachable),
            "site_reachable_from_window_start": site in reachable,
            "window_entry_reachable_merges": reachable_merges,
            "window_instruction_count": (site - start) // 4 + 1,
            "direct_edges": edges, "indirect_calls_unknown": indirect_calls,
            "out_of_window_edges": unresolved,
            "in_window_merges": merges,
            "site_in_window_predecessors": sorted(hex(x) for x in set(incoming.get(site, []))),
            "external_predecessors_unknown": True,
            "complete_cfg_proven": False, "memory_values_proven": False,
            "engine_consumer_abi_verified": False}



def reaching_writers(code, base, site, register, window=128):
    """Enumerate path-sensitive last writers from a hypothetical window entry.

    Any path entering from outside the window, a call, or an unsupported
    instruction leaves the register's runtime value unresolved.
    """
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM, CS_GRP_CALL
    from capstone.arm64 import ARM64_OP_REG
    graph = census(code, base, site, window)
    start = int(graph["window_start"], 16)
    if not graph["site_reachable_from_window_start"]:
        return {"writers": [], "unknown_paths": ["site_not_reachable_from_window_entry"],
                "external_predecessors_unknown": True, "abi_verified": False}
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    instructions = {}
    predecessors = {pc: set() for pc in range(start, site + 4, 4)}
    for pc in predecessors:
        ins = list(md.disasm(code[pc-base:pc-base+4], pc))
        if len(ins) != 1 or ins[0].address != pc or ins[0].size != 4:
            raise ValueError("Unrecognized instruction in bounded window")
        instructions[pc] = ins[0]
        kind, target, fallthrough = decode_edge(struct.unpack_from("<I", code, pc-base)[0], pc)
        if target is not None and kind != "call" and target in predecessors:
            predecessors[target].add(pc)
        if fallthrough and pc < site:
            predecessors[pc+4].add(pc)
    # Ignore syntactic predecessors unreachable from the hypothetical entry.
    successors = {pc: set() for pc in predecessors}
    for pc, preds in predecessors.items():
        for predecessor in preds:
            successors[predecessor].add(pc)
    reachable = set()
    todo = [start]
    while todo:
        pc = todo.pop()
        if pc in reachable:
            continue
        reachable.add(pc)
        todo.extend(successors[pc] - reachable)
    predecessors = {pc: preds & reachable for pc, preds in predecessors.items()}
    target_reg = md.reg_name(instructions[site].operands[0].reg)
    if target_reg != register or instructions[site].mnemonic != "br":
        raise ValueError("Pinned branch register mismatch")
    writers = set()
    unknown = set()
    pending = [(site, register)]
    visited = set()
    while pending:
        pc, wanted = pending.pop()
        if (pc, wanted) in visited:
            continue
        visited.add((pc, wanted))
        if pc == start:
            # Include the first instruction as a possible reaching definition.
            ins = instructions[pc]
            if ins.group(CS_GRP_CALL):
                unknown.add("call_clobber_or_side_effect")
            elif wanted in {md.reg_name(x) for x in ins.regs_access()[1]}:
                writers.add((pc, ins.bytes.hex(), ins.mnemonic, ins.op_str))
            else:
                unknown.add("hypothetical_window_entry")
        for predecessor in predecessors[pc]:
            ins = instructions[predecessor]
            if ins.group(CS_GRP_CALL):
                unknown.add("call_clobber_or_side_effect")
                continue
            reads, writes = ins.regs_access()
            written = {md.reg_name(x) for x in writes}
            if wanted in written:
                writers.add((predecessor, ins.bytes.hex(), ins.mnemonic, ins.op_str))
            else:
                pending.append((predecessor, wanted))
    return {"writers": [{"address": hex(pc), "bytes_le": raw,
                         "mnemonic": mnemonic, "operands": operands}
                        for pc, raw, mnemonic, operands in sorted(writers)],
            "unknown_paths": sorted(unknown),
            "external_predecessors_unknown": True,
            "memory_values_proven": False, "abi_verified": False}

def analyze(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original main SHA mismatch")
    base, code, _ = segments(nso)[0]
    sites = {}
    for name, (site, register) in SITES.items():
        evidence = census(code, base, site)
        evidence["reaching_register_writers"] = reaching_writers(code, base, site, register)
        sites[name] = evidence
    return {"main_sha256": digest, "text_sha256": hashlib.sha256(code).hexdigest(),
            "sites": sites,
            "scope": "bounded syntactic direct-edge census; external predecessors unknown",
            "ownership_verified": False, "archive_precedence_verified": False,
            "gameplay_verified": False}
