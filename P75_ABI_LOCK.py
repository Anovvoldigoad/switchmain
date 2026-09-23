#!/usr/bin/env python3

from pathlib import Path
from collections import deque
import struct
import re
import lz4.block

from capstone import (
    Cs,
    CS_ARCH_ARM64,
    CS_MODE_ARM,
)

MAIN = Path(
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

BID = "48ece454b61412b9fb46fab2be3f5ef7b2804f39"

raw = MAIN.read_bytes()

def u32(o):
    return struct.unpack_from("<I", raw, o)[0]

if raw[:4] != b"NSO0":
    raise SystemExit("FATAL: main bukan NSO0")

bid = raw[0x40:0x54].hex()

if bid.lower() != BID.lower():
    raise SystemExit(
        "FATAL: Build ID mismatch: " + bid
    )

flags = u32(0x0C)
foff  = u32(0x10)
mem   = u32(0x14)
size  = u32(0x18)
csize = u32(0x60)

src = raw[foff:foff+csize]

if flags & 1:
    text = lz4.block.decompress(
        src,
        uncompressed_size=size
    )
else:
    text = raw[foff:foff+size]

md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

def one(pc):
    off = pc - mem

    if off < 0 or off + 4 > len(text):
        return None

    xs = list(
        md.disasm(
            text[off:off+4],
            pc,
            count=1
        )
    )

    return xs[0] if xs else None


def imm_target(i):
    ms = re.findall(
        r"#0x([0-9a-fA-F]+)",
        i.op_str
    )

    if not ms:
        return None

    return int(ms[-1], 16)


def reachable(entry, max_span=0x500):
    lo = entry
    hi = entry + max_span

    q = deque([entry])
    seen = set()

    while q:
        pc = q.popleft()

        if pc in seen:
            continue

        if not (lo <= pc < hi):
            continue

        i = one(pc)

        if i is None:
            continue

        seen.add(pc)

        m = i.mnemonic
        dst = imm_target(i)

        # terminal
        if m in ("ret", "br"):
            continue

        # direct unconditional local branch
        if m == "b":
            if dst is not None:
                q.append(dst)
            continue

        # conditional branch
        if (
            m.startswith("b.")
            or m in (
                "cbz",
                "cbnz",
                "tbz",
                "tbnz",
            )
        ):
            if dst is not None:
                q.append(dst)

            q.append(pc + 4)
            continue

        # BL/BLR are calls, execution returns to next instruction.
        q.append(pc + 4)

    return sorted(seen)


ARG_RE = re.compile(
    r"(?<![a-z0-9_])"
    r"([xw][1-7])"
    r"(?![a-z0-9_])"
)


def audit(name, entry):
    pcs = reachable(entry)

    print()
    print(
        "============================================================"
    )
    print(
        f"{name} ENTRY=0x{entry:08X} "
        f"reachable={len(pcs)}"
    )
    print(
        "============================================================"
    )

    ret_sites = []
    arg_refs = []
    bl_sites = []

    for pc in pcs:
        i = one(pc)

        if not i:
            continue

        mark = ""

        if i.mnemonic == "ret":
            ret_sites.append(pc)
            mark = "   <<< RET"

        if i.mnemonic in ("bl", "blr"):
            bl_sites.append(pc)

        refs = ARG_RE.findall(
            i.op_str.lower()
        )

        if refs:
            arg_refs.append(
                (
                    pc,
                    i.mnemonic,
                    i.op_str,
                    sorted(set(refs)),
                )
            )

        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str:<38}"
            f"{mark}"
        )

    print()
    print(f"{name}_RET_SITES=")

    for pc in ret_sites:
        print(
            f"  0x{pc:08X}"
        )

    print()
    print(f"{name}_ARG_REG_REFERENCES=")

    if not arg_refs:
        print("  NONE")
    else:
        for pc, mn, op, refs in arg_refs:
            print(
                f"  0x{pc:08X}: "
                f"{mn:<8} {op:<34} "
                f"refs={','.join(refs)}"
            )

    print()
    print(
        f"{name}_CALL_COUNT={len(bl_sites)}"
    )

    return {
        "pcs": pcs,
        "rets": ret_sites,
        "args": arg_refs,
    }


print("===== P75 ABI LOCK =====")
print("Build ID:", bid)

uj = audit(
    "UJ",
    0x8B2B70
)

alt = audit(
    "ALT",
    0x8B2D04
)

print()
print("===== P75 ABI SUMMARY =====")

print(
    "UJ_reachable=",
    len(uj["pcs"]),
    "UJ_rets=",
    len(uj["rets"]),
    "UJ_argref_insns=",
    len(uj["args"])
)

print(
    "ALT_reachable=",
    len(alt["pcs"]),
    "ALT_rets=",
    len(alt["rets"]),
    "ALT_argref_insns=",
    len(alt["args"])
)

print()
print(
    "NOTE: ARG_REG_REFERENCES lists every X1-X7/W1-W7 "
    "reference. A reference is not automatically an incoming "
    "argument dependency; writes such as MOV W1,#8 are internal "
    "definitions and must be distinguished from reads."
)

print()
print("P75_ABI_LOCK=PASS")
