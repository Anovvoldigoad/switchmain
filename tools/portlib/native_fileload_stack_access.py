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
