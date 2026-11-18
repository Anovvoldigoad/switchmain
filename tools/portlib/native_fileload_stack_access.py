"""Read-only exact-main FileLoad stack memory operand census (NOT ownership proof)."""
import hashlib
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_MEM
from .native_cpk_graph import MAIN_SHA256
from .native_fileload_corridor_cfg import ENTRY, END
from .nso_profile import segments

MEMORY = {"ldr","ldrb","ldrh","ldrsb","ldrsh","ldrsw","str","strb","strh",
          "ldp","stp","ldur","stur","ldurb","sturb","ldurh","sturh","ldpsw"}

def census(data, start):
    if len(data) % 4:
        raise ValueError("Unaligned ARM64 instruction window")
    cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    cs.detail = True
    out = []
    for offset in range(0, len(data), 4):
        decoded = list(cs.disasm(data[offset:offset+4], start+offset))
        if len(decoded) != 1 or decoded[0].size != 4:
            raise ValueError("Undecodable original instruction at "+hex(start+offset))
        ins = decoded[0]
        if ins.mnemonic not in MEMORY:
            continue
        for operand in ins.operands:
            if operand.type != ARM64_OP_MEM:
                continue
            base = ins.reg_name(operand.mem.base)
            if base not in ("sp","x29","fp"):
                continue
            out.append({"pc":hex(ins.address),"word_le":data[offset:offset+4].hex(),
                        "instruction":ins.mnemonic+" "+ins.op_str,
                        "base":"x29" if base=="fp" else base,
                        "displacement":operand.mem.disp,"writeback":bool(ins.writeback),
                        "object_identity_proven":False})
    return out

def straight_line_sp_prefix(data, start):
    """Track SP-relative byte offsets only until first control-transfer instruction.

    This is a syntactic prefix, not a path-sensitive alias/ownership proof.
    Unrecognized SP writers stop the trace rather than fabricate an offset.
    """
    if len(data) % 4:
        raise ValueError("Unaligned ARM64 instruction window")
    cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    cs.detail = True
    delta = 0
    events = []
    for off in range(0, len(data), 4):
        insns = list(cs.disasm(data[off:off+4], start+off))
        if len(insns) != 1 or insns[0].size != 4:
            raise ValueError("Undecodable instruction at " + hex(start+off))
        ins = insns[0]
        mnemonic = ins.mnemonic
        if mnemonic in ("bl", "blr", "br", "ret", "b", "cbz", "cbnz", "tbz", "tbnz") or mnemonic.startswith("b."):
            return {"stop_pc": hex(ins.address), "stop_reason": "control_transfer",
                    "events": events, "final_sp_delta": delta}
        before = delta
        if mnemonic in ("add", "sub") and ins.op_str.startswith("sp, sp, #"):
            operands = ins.operands
            if len(operands) != 3 or operands[2].type != 2:
                return {"stop_pc": hex(ins.address), "stop_reason": "unresolved_sp_write",
                        "events": events, "final_sp_delta": delta}
            amount = operands[2].imm
            delta += amount if mnemonic == "add" else -amount
        elif ins.writeback:
            for operand in ins.operands:
                if operand.type == ARM64_OP_MEM and ins.reg_name(operand.mem.base) == "sp":
                    return {"stop_pc": hex(ins.address), "stop_reason": "sp_writeback_unresolved",
                            "events": events, "final_sp_delta": delta}
        elif ins.operands and ins.reg_name(ins.operands[0].reg) == "sp" if ins.operands and ins.operands[0].type == 1 else False:
            return {"stop_pc": hex(ins.address), "stop_reason": "unresolved_sp_write",
                    "events": events, "final_sp_delta": delta}
        events.append({"pc": hex(ins.address), "word_le": data[off:off+4].hex(),
                       "sp_delta_before": before, "sp_delta_after": delta})
    return {"stop_pc": hex(start+len(data)), "stop_reason": "window_end",
            "events": events, "final_sp_delta": delta}


def inspect(nso):
    sha = hashlib.sha256(nso).hexdigest()
    if sha != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    va, text, _ = segments(nso)[0]
    if va != 0 or END > len(text):
        raise ValueError("Pinned original executable layout mismatch")
    window = text[ENTRY:END]
    return {"status":"PINNED_FILELOAD_STACK_OPERANDS_ONLY",
            "original_main_sha256":sha,"window_start":hex(ENTRY),
            "window_end_exclusive":hex(END),
            "window_sha256":hashlib.sha256(window).hexdigest(),
            "accesses":census(window,ENTRY),
            "stack_pointer_delta_proven":False,
            "stack_slot_dataflow_proven":False,
            "ownership_lifecycle_async_destructor_proven":False,
            "native_consumer_abi_proven":False,"hook_added":False,
            "Uzuy_gameplay_verified":False}
