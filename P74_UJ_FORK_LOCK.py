#!/usr/bin/env python3

from pathlib import Path
import struct
import lz4.block
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

MAIN = Path(
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

BID = "48ece454b61412b9fb46fab2be3f5ef7b2804f39"

LO = 0x7F4520
HI = 0x7F46D0

raw = MAIN.read_bytes()

def u32(o):
    return struct.unpack_from("<I", raw, o)[0]

if raw[:4] != b"NSO0":
    raise SystemExit("FATAL: not NSO0")

bid = raw[0x40:0x54].hex()

if bid.lower() != BID.lower():
    raise SystemExit("FATAL: Build ID mismatch " + bid)

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

ins = list(
    md.disasm(
        text[LO-mem:HI-mem],
        LO
    )
)

imap = {i.address: i for i in ins}


marks = {
    0x7F4588: "   <<< FORK VCALL",
    0x7F458C: "   <<< FORK RESULT",
    0x7F4590: "   <<< ALTERNATE ENTRY",
    0x7F45F4: "   <<< GATE A",
    0x7F4640: "   <<< UJ CORRIDOR ENTRY",
    0x7F4644: "   <<< UJ PREDICATE A",
    0x7F4650: "   <<< UJ PREDICATE B",
    0x7F465C: "   <<< UJ PREDICATE C",
    0x7F4694: "   <<< INPUT/MASK PREDICATE",
    0x7F46A4: "   <<< F58 SETUP",
    0x7F46B4: "   <<< F58 VCALL",
    0x7F46B8: "   <<< F58 RESULT",
}

print("===== P74 COMPLETE FORK CORRIDOR =====")

for i in ins:
    mark = marks.get(i.address, "")

    print(
        f"0x{i.address:08X}: "
        f"{i.mnemonic:<8} "
        f"{i.op_str:<38}"
        f"{mark}"
    )


print()
print("===== P74 VCALL SETUP 0x7F4588 =====")

for pc in range(0x7F4570, 0x7F4594, 4):
    i = imap.get(pc)

    if not i:
        continue

    mark = marks.get(pc, "")

    print(
        f"0x{i.address:08X}: "
        f"{i.mnemonic:<8} "
        f"{i.op_str:<38}"
        f"{mark}"
    )


print()
print("===== P74 DIRECT BRANCHES INTO KEY ENTRIES =====")

targets = {
    0x7F4590: "ALT",
    0x7F4640: "UJ",
    0x7F4690: "PRE_F58",
    0x7F46A0: "F58_ENTRY",
}

for i in ins:
    if not (
        i.mnemonic == "b"
        or i.mnemonic.startswith("b.")
        or i.mnemonic in ("cbz", "cbnz", "tbz", "tbnz")
    ):
        continue

    op = i.op_str.split(",")[-1].strip()

    if not op.startswith("#0x"):
        continue

    try:
        dst = int(op[1:], 16)
    except ValueError:
        continue

    if dst in targets:
        print(
            f"{targets[dst]:<9} "
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<7} "
            f"{i.op_str}"
        )


print()
print("===== P74 PATH ASSERTIONS =====")

required = {
    0x7F4588,
    0x7F458C,
    0x7F4590,
    0x7F4640,
    0x7F46A4,
    0x7F46B4,
    0x7F46B8,
}

missing = sorted(
    x for x in required
    if x not in imap
)

if missing:
    print(
        "MISSING=" +
        ",".join(hex(x) for x in missing)
    )
    raise SystemExit("P74=FAIL")

print("fork_vcall=0x7F4588")
print("fork_branch=0x7F458C")
print("alternate_entry=0x7F4590")
print("uj_corridor_entry=0x7F4640")
print("f58_call=0x7F46B4")
print("P74_UJ_FORK_LOCK=PASS")
