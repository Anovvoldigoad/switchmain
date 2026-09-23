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

LO = 0x7F4404
HI = 0x7F5000

raw = MAIN.read_bytes()

def u32(o):
    return struct.unpack_from("<I", raw, o)[0]

if raw[:4] != b"NSO0":
    raise SystemExit("FATAL: main bukan NSO0")

bid = raw[0x40:0x54].hex()

if bid.lower() != BID.lower():
    raise SystemExit(
        "FATAL: Build ID mismatch " + bid
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

ins = list(
    md.disasm(
        text[LO-mem:HI-mem],
        LO
    )
)

imap = {
    i.address: i
    for i in ins
}

def norm(s):
    return s.lower().replace(" ", "")

def show_context(addr):
    for pc in range(
        max(LO, addr - 0x10),
        min(HI, addr + 0x18),
        4
    ):
        i = imap.get(pc)

        if not i:
            continue

        mark = "   <<<" if pc == addr else ""

        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str:<34}"
            f"{mark}"
        )

print("===== P71 W21 STATE ASSIGNMENTS =====")

assign = []

for i in ins:
    op = norm(i.op_str)

    # Literal state loaded into selector register.
    if (
        i.mnemonic in ("mov", "movz")
        and op.startswith("w21,#")
    ):
        assign.append(i)

print("count =", len(assign))

for i in assign:
    print()
    print(
        f"--- 0x{i.address:08X}: "
        f"{i.mnemonic} {i.op_str} ---"
    )

    show_context(i.address)


print()
print("===== P71 ALL W21 USES =====")

for i in ins:
    op = norm(i.op_str)

    if "w21" not in op:
        continue

    print(
        f"0x{i.address:08X}: "
        f"{i.mnemonic:<8} "
        f"{i.op_str}"
    )


print()
print("===== P71 KNOWN BRANCH DESTINATIONS =====")

for base in (
    0x7F4840,
    0x7F48E8,
    0x7F4900,
    0x7F490C,
    0x7F4A38,
    0x7F4F10,
):
    print()
    print(f"--- DEST 0x{base:08X} ---")

    for pc in range(
        base,
        min(base + 0x28, HI),
        4
    ):
        i = imap.get(pc)

        if not i:
            continue

        op = norm(i.op_str)

        # Keep only state/control relevant instructions.
        if (
            "w21" in op
            or "w25" in op
            or i.mnemonic in (
                "mov",
                "b",
                "bl",
                "blr",
                "cbz",
                "cbnz",
                "tbz",
                "tbnz",
                "cmp",
                "tst",
                "cset",
                "csel",
            )
        ):
            print(
                f"0x{i.address:08X}: "
                f"{i.mnemonic:<8} "
                f"{i.op_str}"
            )


print()
print("===== P71 UJ ANCHOR =====")

for pc in range(
    0x7F47A8,
    0x7F47D0,
    4
):
    i = imap.get(pc)

    if not i:
        continue

    mark = ""

    if pc == 0x7F47B8:
        mark = "   <<< UJ STATE 0x87"

    print(
        f"0x{i.address:08X}: "
        f"{i.mnemonic:<8} "
        f"{i.op_str:<34}"
        f"{mark}"
    )

print()
print("P71_STATE_SELECTOR_MAP=PASS")
