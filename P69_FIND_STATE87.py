#!/usr/bin/env python3

from pathlib import Path
import struct
import lz4.block
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

MAIN = Path(
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

raw = MAIN.read_bytes()

def u32(o):
    return struct.unpack_from("<I", raw, o)[0]

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

# Relevant battle/input neighborhood only.
LO = 0x7A0000
HI = 0x800000

blob = text[LO-mem:HI-mem]
all_ins = list(md.disasm(blob, LO))

hits = []

for idx, ins in enumerate(all_ins):
    op = ins.op_str.lower()

    # Exact UJ state literal.
    if "#0x87" in op:
        hits.append((idx, ins))

print("===== STATE 0x87 HITS =====")
print("count =", len(hits))

for n, (idx, hit) in enumerate(hits, 1):
    print()
    print(
        f"===== HIT {n} @ 0x{hit.address:08X} ====="
    )

    a = max(0, idx - 10)
    b = min(len(all_ins), idx + 13)

    for ins in all_ins[a:b]:
        mark = ""

        if ins.address == hit.address:
            mark = "   <<< STATE 0x87"

        print(
            f"0x{ins.address:08X}: "
            f"{ins.mnemonic:<8} "
            f"{ins.op_str:<38}"
            f"{mark}"
        )

print()
print("P69_STATE87_SCAN=PASS")
