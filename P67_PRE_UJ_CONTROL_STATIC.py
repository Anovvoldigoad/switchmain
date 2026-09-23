#!/usr/bin/env python3

from pathlib import Path
import struct
import lz4.block
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

MAIN = Path(
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

TARGET_BID = "48ece454b61412b9fb46fab2be3f5ef7b2804f39"

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

raw = MAIN.read_bytes()

if raw[:4] != b"NSO0":
    raise SystemExit("FATAL: main bukan NSO0")

bid = raw[0x40:0x54].hex()

if bid.lower() != TARGET_BID.lower():
    raise SystemExit(
        f"FATAL: Build ID {bid}"
    )

flags = u32(raw, 0x0C)
fileoff = u32(raw, 0x10)
memoff = u32(raw, 0x14)
size = u32(raw, 0x18)
csize = u32(raw, 0x60)

src = raw[fileoff:fileoff+csize]

if flags & 1:
    text = lz4.block.decompress(
        src,
        uncompressed_size=size
    )
else:
    text = raw[fileoff:fileoff+size]

md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

def dump(lo, hi, title):
    print()
    print("=" * 94)
    print(title)
    print("=" * 94)

    blob = text[
        lo - memoff:
        hi - memoff
    ]

    for ins in md.disasm(blob, lo):
        mark = ""

        if ins.address == 0x7F4448:
            mark = "   <<< NATIVE CONTROL GETTER"
        elif ins.address == 0x7F46B4:
            mark = "   <<< F58 VCALL (TOO LATE FOR TOBI)"

        print(
            f"0x{ins.address:08X}: "
            f"{ins.mnemonic:<8} "
            f"{ins.op_str:<38}"
            f"{mark}"
        )

dump(
    0x7F43B0,
    0x7F4520,
    "A) PRE-F58 UJ INPUT / CONTROL REGION"
)

dump(
    0x7F4400,
    0x7F4470,
    "B) EXACT CONTROL GETTER @ 0x7F4448"
)

print()
print("P67_STATIC_DUMP=PASS")
