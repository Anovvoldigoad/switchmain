"""Conservative, read-only FileLoad CFG SP-offset evidence; no engine ABI claim."""
from collections import deque
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG
from .native_cpk_cfg import _edges

def trace(data, start, max_states=1024):
    if len(data) % 4:
        raise ValueError("Unaligned ARM64 instruction window")
    cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    cs.detail = True
    decoded = {}
    for off in range(0, len(data), 4):
        ins = list(cs.disasm(data[off:off+4], start+off))
        if len(ins) != 1 or ins[0].size != 4:
            raise ValueError("Undecodable instruction at " + hex(start+off))
        decoded[start+off] = ins[0]
    end = start+len(data)
    queue = deque([(start, 0)])
    visited = set()
    at = {}
    barriers = []
    exits = []
    transitions = {}
    while queue:
        pc, delta = queue.popleft()
        if (pc,delta) in visited:
            continue
        if len(visited) >= max_states:
            raise ValueError("CFG state limit exceeded")
        visited.add((pc,delta))
        if not start <= pc < end:
            exits.append({"pc":hex(pc),"sp_delta":delta})
            continue
        ins = decoded[pc]
        at.setdefault(pc,set()).add(delta)
        next_delta = delta
        op = ins.operands
        if ins.mnemonic in ("add","sub") and ins.op_str.startswith("sp, sp, #"):
            if len(op) != 3 or op[2].type != ARM64_OP_IMM:
                next_delta = None
            elif delta is not None:
                next_delta += op[2].imm * (1 if ins.mnemonic == "add" else -1)
        elif ins.writeback and any(x.type == ARM64_OP_MEM and ins.reg_name(x.mem.base) == "sp" for x in op):
            if "]!" in ins.op_str:
                amount = next(x.mem.disp for x in op if x.type == ARM64_OP_MEM)
            elif "], #" in ins.op_str and op[-1].type == ARM64_OP_IMM:
                amount = op[-1].imm
            else:
                amount = None
            next_delta = delta+amount if delta is not None and amount is not None else None
        elif op and op[0].type == ARM64_OP_REG and ins.reg_name(op[0].reg) == "sp":
            next_delta = None
        edges = _edges(pc,ins.mnemonic,ins.op_str)
        if any(kind == "call" for kind,_ in edges) or ins.mnemonic in ("blr","bl"):
            barriers.append(hex(pc))
            next_delta = None  # Do not infer SP preservation across unknown calls.
        transitions[(pc,delta)] = []
        for kind,target in edges:
            if kind == "call" or target is None:
                continue
            successor = (target,next_delta)
            transitions[(pc,delta)].append((kind,successor))
            queue.append(successor)
    def byte_width(ins):
        """Width of a recognized single/pair stack transfer; unknown is not proof."""
        if not (ins.mnemonic.startswith("ld") or ins.mnemonic.startswith("st")):
            return None
        regs = [ins.reg_name(o.reg) for o in ins.operands if o.type == ARM64_OP_REG]
        if not regs:
            return None
        # Memory width is not always the destination register width:
        # LDRB/LDRH/LDRSW sign/zero extend after reading 1/2/4 bytes.
        # Treat unsupported variants as unknown rather than inventing aliases.
        mnemonic = ins.mnemonic.lower()
        if mnemonic in ("ldrb", "ldrsb", "strb", "ldurb", "ldursb"):
            return 1 if len(regs) == 1 else None
        if mnemonic in ("ldrh", "ldrsh", "strh", "ldurh", "ldursh"):
            return 2 if len(regs) == 1 else None
        if mnemonic in ("ldrsw", "ldursw"):
            return 4 if len(regs) == 1 else None
        sizes = {"w": 4, "x": 8, "s": 4, "d": 8, "q": 16}
        widths = [sizes.get(r[0]) for r in regs]
        if any(w is None for w in widths):
            return None
        if mnemonic in ("ldp", "stp", "ldnp", "stnp") and len(widths) == 2 and widths[0] == widths[1]:
            return sum(widths)
        if mnemonic in ("ldr", "str", "ldur", "stur", "ldtr", "sttr") and len(widths) == 1:
            return widths[0]
        return None
    accesses = []
    for pc,values in sorted(at.items()):
        ins = decoded[pc]
        for op in ins.operands:
            if op.type != ARM64_OP_MEM or ins.reg_name(op.mem.base) != "sp":
                continue
            offsets = sorted({v+op.mem.disp for v in values if v is not None})
            ambiguous = None in values or len(offsets) != 1
            width = byte_width(ins)
            byte_range = ([offsets[0], offsets[0]+width]
                          if not ambiguous and width is not None else None)
            accesses.append({"byte_width":width,
                            "entry_sp_relative_byte_range":byte_range,
                            "pc":hex(pc),"word_le":data[pc-start:pc-start+4].hex(),
                            "memory_direction": "read" if ins.mnemonic.startswith("ld") else ("write" if ins.mnemonic.startswith("st") else "unknown"),
                            "sp_displacement":op.mem.disp,
                            "entry_sp_relative_offsets":offsets if not ambiguous else [],
                            "path_ambiguous":ambiguous,
                            "observed_sp_deltas":sorted(v for v in values if v is not None),
                            "unknown_path":None in values})
    access_by_pc = {int(a["pc"],16): a for a in accesses}
    def path_witness(writer_pc, reader_pc, slot):
        """Find a CFG state path, excluding opaque calls and unknown SP."""
        starts = [(pc,delta) for pc,delta in visited if pc == writer_pc and delta is not None]
        for origin in sorted(starts):
            pending = deque([(origin,[origin])])
            seen = {origin}
            while pending:
                state,path = pending.popleft()
                current = access_by_pc.get(state[0])
                # A store through a non-SP base may alias the tracked stack slot.
                # Without register provenance its destination is unknown: fail closed.
                intermediate = decoded.get(state[0])
                if state != origin and intermediate is not None:
                    memory_operands = [o for o in intermediate.operands if o.type == ARM64_OP_MEM]
                    if memory_operands and (intermediate.mnemonic.startswith("st") or
                            not intermediate.mnemonic.startswith("ld")):
                        if any(intermediate.reg_name(o.mem.base) != "sp" for o in memory_operands):
                            continue
                if (state != origin and current is not None and current["memory_direction"] != "read":
                    # An intervening store (or unclassified memory operation) may kill the value.
                    target_range = slot
                    observed_range = current["entry_sp_relative_byte_range"]
                    if (current["path_ambiguous"] or observed_range is None
                            or max(target_range[0], observed_range[0]) < min(target_range[1], observed_range[1])
                            or current["memory_direction"] == "unknown"):
                        continue
                for kind,nxt in transitions.get(state,()):
                    if (kind.startswith("fallthrough_after_") or nxt[1] is None
                            or nxt in seen):
                        continue
                    candidate_path = path+[nxt]
                    if nxt[0] == reader_pc:
                        return [{"pc":hex(pc),"sp_delta":delta} for pc,delta in candidate_path]
                    seen.add(nxt)
                    pending.append((nxt,candidate_path))
        return None
    # CFG reachability proves only a possible path, not actual execution or dataflow.
    candidates = []
    for writer in accesses:
        if (writer["memory_direction"] != "write" or writer["path_ambiguous"]
                or writer["entry_sp_relative_byte_range"] is None):
            continue
        for reader in accesses:
            if (reader["memory_direction"] != "read" or reader["path_ambiguous"]
                    or reader["entry_sp_relative_byte_range"] is None
                    or int(reader["pc"], 16) <= int(writer["pc"], 16)):
                continue
            if writer["entry_sp_relative_byte_range"] == reader["entry_sp_relative_byte_range"]:
                witness = path_witness(int(writer["pc"],16),int(reader["pc"],16),writer["entry_sp_relative_byte_range"])
                if witness is None:
                    continue
                candidates.append({"writer_pc":writer["pc"], "reader_pc":reader["pc"],
                                   "entry_sp_relative_offset":writer["entry_sp_relative_offsets"][0],
                                   "cfg_path_witness":witness,
                                   "same_executed_path_proven":False,
                                   "register_value_proven":False,
                                   "intervening_overlapping_write_excluded_on_witness":True,
                                   "intervening_same_slot_write_excluded_on_witness":True})
    return {"possible_stack_write_read_pairs":candidates,
            "candidate_pairs_are_not_dataflow_proof":True,
            "reachable_states":len(visited),"reachable_instructions":len(at),
            "accesses":accesses,"call_barriers":sorted(set(barriers)),
            "out_of_window_edges":exits[:32],"out_of_window_edges_truncated":len(exits)>32,
            "consumer_abi_proven":False,"stack_ownership_proven":False,
            "cross_call_sp_preservation_assumed":False}
