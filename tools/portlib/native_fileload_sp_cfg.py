"""Conservative, read-only FileLoad CFG SP-offset evidence; no engine ABI claim."""
from collections import deque
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG
from .native_cpk_cfg import _edges, AUTHENTICATED_CALLS

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
    def memory_index_register(ins, operand):
        index = getattr(operand.mem, "index", 0)
        return ins.reg_name(index) if index else None

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
            sp_memory = [x for x in op if x.type == ARM64_OP_MEM and ins.reg_name(x.mem.base) == "sp"]
            if len(sp_memory) != 1 or getattr(sp_memory[0].mem, "index", 0):
                amount = None
            elif "]!" in ins.op_str:
                amount = sp_memory[0].mem.disp
            elif "], #" in ins.op_str and op[-1].type == ARM64_OP_IMM:
                amount = op[-1].imm
            else:
                amount = None
            next_delta = delta+amount if delta is not None and amount is not None else None
        elif op and op[0].type == ARM64_OP_REG and ins.reg_name(op[0].reg) == "sp":
            next_delta = None
        # Authenticated indirect calls must not be treated as plain fallthrough.
        edges = _edges(pc,ins.mnemonic,ins.op_str)
        if any(kind == "call" for kind,_ in edges) or ins.mnemonic in ({"blr", "bl"} | AUTHENTICATED_CALLS):
            barriers.append(hex(pc))
            next_delta = None  # Do not infer SP preservation across unknown calls.
        transitions[(pc,delta)] = []
        for kind,target in edges:
            if kind == "call" or target is None:
                continue
            successor = (target,next_delta)
            transitions[(pc,delta)].append((kind,successor))
            queue.append(successor)
    gpr_names = tuple("x" + str(i) for i in range(31))
    def canonical_gpr(name):
        if name in ("sp", "wsp"):
            return "sp"
        if name == "fp":
            return "x29"
        if name == "lr":
            return "x30"
        if len(name) > 1 and name[0] in ("x", "w") and name[1:].isdigit():
            number = int(name[1:])
            if 0 <= number <= 30:
                return "x" + str(number)
        return None
    def immediate_constant(ins):
        """Exact MOV-immediate value only; no arithmetic or ABI propagation."""
        if ins.mnemonic != "mov" or len(ins.operands) != 2:
            return None
        destination, source = ins.operands
        if destination.type != ARM64_OP_REG or source.type != ARM64_OP_IMM:
            return None
        register = ins.reg_name(destination.reg)
        if (not register.startswith(("w", "x"))
                or not register[1:].isdigit()):
            return None
        width_bits = 32 if register.startswith("w") else 64
        value = source.imm & ((1 << width_bits) - 1)
        return {
            "register": register,
            "width_bits": width_bits,
            "unsigned_value": value,
            "hex": f"0x{value:0{width_bits // 4}x}",
            "x_register_value": value,
            "zero_extended_from_w": width_bits == 32,
        }
    def register_origin_flow():
        # Track reaching definitions, not values or ABI-preserved registers.
        initial = {name: frozenset({("entry",)}) for name in gpr_names}
        initial["sp"] = frozenset({("entry_sp",)})
        incoming = {(start, 0): initial}
        pending = deque([(start, 0)])
        updates = 0
        while pending:
            state = pending.popleft()
            pc, delta = state
            ins = decoded[pc]
            current = dict(incoming[state])
            edges = _edges(pc, ins.mnemonic, ins.op_str)
            is_call = (any(kind == "call" for kind, _ in edges)
                       or ins.mnemonic in ({"bl", "blr"} | AUTHENTICATED_CALLS))
            if is_call:
                for name in gpr_names:
                    current[name] = frozenset({("call", pc, delta)})
                current["sp"] = frozenset({("call_sp", pc, delta)})
            else:
                _, writes = ins.regs_access()
                for reg in writes:
                    name = canonical_gpr(ins.reg_name(reg))
                    if name is not None:
                        current[name] = frozenset({("def", pc, delta)})
            for _, nxt in transitions.get(state, ()):
                if nxt[0] not in decoded:
                    continue
                previous = incoming.get(nxt)
                if previous is None:
                    merged = current
                else:
                    merged = {name: previous[name] | current[name]
                              for name in gpr_names + ("sp",)}
                if previous is None or merged != previous:
                    incoming[nxt] = merged
                    pending.append(nxt)
                    updates += 1
                    if updates > max_states * 64:
                        raise ValueError("Register-origin dataflow budget exceeded")
        return incoming
    register_origins = register_origin_flow()
    def origin_token_summary(token):
        if token[0] == "entry":
            return {"kind": "entry_value"}
        if token[0] == "entry_sp":
            return {"kind": "entry_stack_pointer"}
        if token[0] == "call":
            return {"kind": "call_clobber", "pc": hex(token[1])}
        if token[0] == "call_sp":
            return {"kind": "call_boundary", "pc": hex(token[1])}
        def_pc, def_delta = token[1], token[2]
        ins = decoded[def_pc]
        summary = {"kind": "instruction_definition", "pc": hex(def_pc),
                   "sp_delta_before": def_delta,
                   "word_le": data[def_pc-start:def_pc-start+4].hex(),
                   "mnemonic": ins.mnemonic, "operands": ins.op_str}
        constant = immediate_constant(ins)
        if constant is not None:
            summary["immediate_constant"] = constant
        return summary
    def detailed_origin(token):
        summary = origin_token_summary(token)
        if token[0] != "def":
            return summary
        def_state = (token[1], token[2])
        ins = decoded[token[1]]
        reads, _ = ins.regs_access()
        names = sorted({name for reg in reads
                        if (name := canonical_gpr(ins.reg_name(reg))) is not None})
        sources = {}
        for name in names:
            source_tokens = register_origins.get(def_state, {}).get(name, frozenset())
            sources[name] = [origin_token_summary(value)
                             for value in sorted(source_tokens, key=repr)]
        summary["read_registers"] = names
        summary["source_register_origins"] = sources
        return summary
    def register_evidence(state, register):
        name = canonical_gpr(register)
        values = (register_origins.get(state, {}).get(name, frozenset())
                  if name is not None else frozenset())
        ordered = sorted(values, key=repr)
        definitions = [detailed_origin(value) for value in ordered]
        constant = (definitions[0].get("immediate_constant")
                    if len(definitions) == 1 else None)
        return {"register": register,
                "reaching_definitions": definitions,
                "single_reaching_definition": len(ordered) == 1,
                "entry_value_only": values == frozenset({("entry",)}),
                "call_clobbered": any(value[0] == "call" for value in values),
                "constant_value": constant,
                "numeric_value_proven": constant is not None}
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
    indexed_memory_operands = []
    for pc,values in sorted(at.items()):
        ins = decoded[pc]
        for op in ins.operands:
            if op.type != ARM64_OP_MEM:
                continue
            base_register = ins.reg_name(op.mem.base)
            index_register = memory_index_register(ins, op)
            if index_register is not None:
                indexed_memory_operands.append({
                    "pc":hex(pc),"word_le":data[pc-start:pc-start+4].hex(),
                    "base_register":base_register,"index_register":index_register,
                    "sp_displacement":op.mem.disp,
                    "memory_direction":"read" if ins.mnemonic.startswith("ld") else ("write" if ins.mnemonic.startswith("st") else "unknown"),
                    "observed_sp_deltas":sorted(v for v in values if v is not None),
                    "unknown_path":None in values,
                    "effective_address_resolved":False,
                    "index_value_proven":False})
            if base_register != "sp":
                continue
            indexed_address = index_register is not None
            offsets = ([] if indexed_address else
                       sorted({v+op.mem.disp for v in values if v is not None}))
            ambiguous = indexed_address or None in values or len(offsets) != 1
            width = byte_width(ins)
            byte_range = ([offsets[0], offsets[0]+width]
                          if not ambiguous and width is not None else None)
            accesses.append({"byte_width":width,
                            "entry_sp_relative_byte_range":byte_range,
                            "pc":hex(pc),"word_le":data[pc-start:pc-start+4].hex(),
                            "memory_direction": "read" if ins.mnemonic.startswith("ld") else ("write" if ins.mnemonic.startswith("st") else "unknown"),
                            "sp_displacement":op.mem.disp,
                            "index_register":index_register,
                            "indexed_address_unresolved":indexed_address,
                            "entry_sp_relative_offsets":offsets if not ambiguous else [],
                            "path_ambiguous":ambiguous,
                            "observed_sp_deltas":sorted(v for v in values if v is not None),
                            "unknown_path":None in values})
    indexed_register_origins = []
    for operand in indexed_memory_operands:
        pc = int(operand["pc"], 16)
        states = sorted((state for state in register_origins if state[0] == pc),
                        key=lambda state: (state[1] is None, state[1] if state[1] is not None else 0))
        indexed_register_origins.append({
            "pc": operand["pc"],
            "base_register": operand["base_register"],
            "index_register": operand["index_register"],
            "state_observations": [
                {"sp_delta": state[1],
                 "base": register_evidence(state, operand["base_register"]),
                 "index": register_evidence(state, operand["index_register"])}
                for state in states
            ]
        })
    callsite_register_names = gpr_names + ("sp",)
    callsite_register_origins = []
    for state in sorted(register_origins,
                        key=lambda item: (item[0], item[1] is None,
                                          item[1] if item[1] is not None else 0)):
        pc, delta = state
        ins = decoded[pc]
        edges = _edges(pc, ins.mnemonic, ins.op_str)
        call_edges = [(kind, target) for kind, target in edges
                      if kind in ("call", "indirect_call_unresolved")]
        if not call_edges:
            continue
        direct_targets = sorted({hex(target) for kind, target in call_edges
                                 if kind == "call" and target is not None})
        register_rows = {
            name: register_evidence(state, name)
            for name in callsite_register_names
        }
        immediate_constants = {
            name: evidence["constant_value"]
            for name, evidence in register_rows.items()
            if evidence["numeric_value_proven"]
        }
        callsite_register_origins.append({
            "pc": hex(pc),
            "word_le": data[pc-start:pc-start+4].hex(),
            "mnemonic": ins.mnemonic,
            "operands": ins.op_str,
            "call_kind": "direct" if direct_targets else "indirect_unresolved",
            "direct_targets": direct_targets,
            "target_unresolved": not bool(direct_targets),
            "sp_delta_before_call": delta,
            "register_origins": register_rows,
            "immediate_constants": immediate_constants,
            "abi_register_semantics_assumed": False,
            "numeric_register_values_proven": bool(immediate_constants)
        })
    access_by_pc = {int(a["pc"],16): a for a in accesses}
    def advance_aliases(state, aliases):
        intermediate = decoded.get(state[0])
        if intermediate is None:
            return dict(aliases)
        next_aliases = dict(aliases)
        if intermediate is not None:
            _, writes = intermediate.regs_access()
            for reg in writes:
                name = intermediate.reg_name(reg)
                # A Wn write zero-extends into Xn on AArch64. Keeping an
                # earlier Xn stack alias would invent pointer provenance.
                if name.startswith("w") and name[1:].isdigit():
                    next_aliases.pop("x" + name[1:], None)
                next_aliases.pop(name, None)
            ops = intermediate.operands
            if (intermediate.mnemonic in ("add", "sub") and len(ops) == 3
                    and ops[0].type == ARM64_OP_REG
                    and ops[1].type == ARM64_OP_REG
                    and ops[2].type == ARM64_OP_IMM):
                base = intermediate.reg_name(ops[1].reg)
                offset = state[1] if base == "sp" else aliases.get(base)
                if offset is not None:
                    next_aliases[intermediate.reg_name(ops[0].reg)] = (
                        offset + ops[2].imm * (1 if intermediate.mnemonic == "add" else -1))
            elif (intermediate.mnemonic == "mov" and len(ops) == 2
                    and ops[0].type == ARM64_OP_REG and ops[1].type == ARM64_OP_REG):
                base = intermediate.reg_name(ops[1].reg)
                offset = state[1] if base == "sp" else aliases.get(base)
                if offset is not None:
                    next_aliases[intermediate.reg_name(ops[0].reg)] = offset
        return next_aliases
    def writer_prefixes(writer_pc):
        pending = deque([((start, 0), {})])
        seen = set()
        results = []
        while pending:
            state, aliases = pending.popleft()
            key = (state, tuple(sorted(aliases.items())))
            if key in seen:
                continue
            if len(seen) >= max_states * 16:
                return []
            seen.add(key)
            if state[0] == writer_pc and state[1] is not None:
                results.append((state, aliases))
                continue
            if state[1] is None:
                continue
            next_aliases = advance_aliases(state, aliases)
            for kind, nxt in transitions.get(state, ()):
                if not kind.startswith("fallthrough_after_") and nxt[1] is not None:
                    pending.append((nxt, next_aliases))
        return results
    def path_witness(writer_pc, reader_pc, slot):
        """Find a CFG state path, excluding opaque calls and unknown SP."""
        for origin, initial_aliases in writer_prefixes(writer_pc):
            pending = deque([(origin,[origin],initial_aliases)])
            seen = {(origin,tuple(sorted(initial_aliases.items())))}
            while pending:
                state,path,aliases = pending.popleft()
                current = access_by_pc.get(state[0])
                intermediate = decoded.get(state[0])
                if state != origin and intermediate is not None:
                    memory_operands = [o for o in intermediate.operands if o.type == ARM64_OP_MEM]
                    if memory_operands and (intermediate.mnemonic.startswith("st") or
                            not intermediate.mnemonic.startswith("ld")):
                        for mem in memory_operands:
                            base = intermediate.reg_name(mem.mem.base)
                            if base == "sp":
                                continue  # Existing SP byte-range check below.
                            width = byte_width(intermediate)
                            offset = aliases.get(base)
                            if (offset is None or width is None or intermediate.writeback
                                    or getattr(mem.mem, "index", 0)
                                    or max(slot[0], offset+mem.mem.disp)
                                       < min(slot[1], offset+mem.mem.disp+width)):
                                break
                        else:
                            memory_operands = []  # Proven disjoint alias stores.
                        if memory_operands:
                            continue
                if (state != origin and current is not None and current["memory_direction"] != "read"):
                    # An intervening store (or unclassified memory operation) may kill the value.
                    target_range = slot
                    observed_range = current["entry_sp_relative_byte_range"]
                    if (current["path_ambiguous"] or observed_range is None
                            or max(target_range[0], observed_range[0]) < min(target_range[1], observed_range[1])
                            or current["memory_direction"] == "unknown"):
                        continue
                next_aliases = advance_aliases(state, aliases)
                for kind,nxt in transitions.get(state,()):
                    if kind.startswith("fallthrough_after_") or nxt[1] is None:
                        continue
                    key = (nxt,tuple(sorted(next_aliases.items())))
                    if key in seen:
                        continue
                    candidate_path = path+[nxt]
                    if nxt[0] == reader_pc:
                        return [{"pc":hex(pc),"sp_delta":delta} for pc,delta in candidate_path]
                    seen.add(key)
                    pending.append((nxt,candidate_path,next_aliases))
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
                    or reader["pc"] == writer["pc"]):
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
            "accesses":accesses,"indexed_memory_operands":indexed_memory_operands,
            "indexed_memory_operand_count":len(indexed_memory_operands),
            "indexed_register_origins":indexed_register_origins,
            "callsite_register_origin_state_count":len(callsite_register_origins),
            "callsite_register_origins":callsite_register_origins,
            "callsite_register_origin_policy":"raw reaching definitions at each reachable direct/indirect call; no AAPCS64 argument mapping, numeric value, or preservation assumption",
            "register_origin_call_policy":"all x0-x30 and SP origins become unknown after calls; no callee-saved ABI assumption",
            "call_barriers":sorted(set(barriers)),
            "out_of_window_edges":exits[:32],"out_of_window_edges_truncated":len(exits)>32,
            "consumer_abi_proven":False,"stack_ownership_proven":False,
            "cross_call_sp_preservation_assumed":False}
