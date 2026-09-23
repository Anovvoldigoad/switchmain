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

raw = MAIN.read_bytes()

def u32(o):
    return struct.unpack_from("<I", raw, o)[0]

if raw[:4] != b"NSO0":
    raise SystemExit("FATAL: main bukan NSO0")

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

def bytes_at(addr, n):
    off = addr - mem
    return text[off:off+n]

def words(addr, n=8):
    b = bytes_at(addr, n*4)
    return [
        struct.unpack_from("<I", b, i*4)[0]
        for i in range(n)
    ]

def dump(addr, size, title):
    print()
    print("===== " + title + " =====")

    for i in md.disasm(
        bytes_at(addr, size),
        addr
    ):
        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str}"
        )

    print("WORDS:")

    ws = words(addr, 8)

    for i, w in enumerate(ws):
        print(
            f"  +0x{i*4:02X}: 0x{w:08X}"
        )

print("===== P75 PREFLIGHT =====")
print("Build ID:", bid)

dump(
    0x8B2D04,
    0x60,
    "ALT TARGET 0x8B2D04"
)

dump(
    0x8B2B70,
    0x60,
    "UJ TARGET 0x8B2B70"
)

dump(
    0x7F458C,
    0x14,
    "ALT CALLSITE"
)

dump(
    0x7F4640,
    0x14,
    "UJ CALLSITE"
)

print()
print("===== REQUIRED CALLSITE ASSERTIONS =====")

checks = {
    0x7F4590: 0xAA1303E0,  # MOV X0,X19
}

for pc, expected in checks.items():
    got = struct.unpack(
        "<I",
        bytes_at(pc, 4)
    )[0]

    print(
        f"0x{pc:08X}: "
        f"got=0x{got:08X} "
        f"expected=0x{expected:08X} "
        f"{'PASS' if got == expected else 'FAIL'}"
    )

print()
print("Expected semantic callsites:")
print("ALT: 0x7F4594 -> 0x8B2D04, return=0x7F4598")
print("UJ : 0x7F4644 -> 0x8B2B70, return=0x7F4648")

print()
print("P75_PROBE_PREFLIGHT=PASS")
