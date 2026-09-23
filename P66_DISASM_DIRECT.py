#!/usr/bin/env python3

from pathlib import Path
import struct
import lz4.block
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

TARGET_BID = "48ece454b61412b9fb46fab2be3f5ef7b2804f39"

DEPLOY = Path(
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

def die(x):
    raise SystemExit("FATAL: " + x)

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

def load_nso(path):
    raw = path.read_bytes()

    if raw[:4] != b"NSO0":
        die("not NSO0")

    bid = raw[0x40:0x54].hex()
    if bid.lower() != TARGET_BID.lower():
        die("Build ID mismatch: " + bid)

    flags = u32(raw, 0x0C)

    text_file = u32(raw, 0x10)
    text_mem  = u32(raw, 0x14)
    text_size = u32(raw, 0x18)
    comp_size = u32(raw, 0x60)

    src = raw[text_file:text_file + comp_size]

    if flags & 1:
        text = lz4.block.decompress(
            src,
            uncompressed_size=text_size
        )
    else:
        text = raw[text_file:text_file + text_size]

    if len(text) != text_size:
        die("text size mismatch")

    return text, text_mem

text, base = load_nso(DEPLOY)

md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
md.detail = False

def dump(start, end, title):
    off = start - base

    if off < 0 or end - base > len(text):
        die(f"range outside text: {start:X}-{end:X}")

    blob = text[off:off + (end-start)]

    print()
    print("=" * 88)
    print(title)
    print("=" * 88)

    for ins in md.disasm(blob, start):
        marker = ""

        if ins.address == 0x7F46B4:
            marker = "    <<< ACTIVE BLR"
        elif ins.address == 0x7F46B8:
            marker = "    <<< RESULT GATE"
        elif ins.address == 0x7F46C4:
            marker = "    <<< POST GATE"
        elif ins.address == 0x7F2A9C:
            marker = "    <<< P65 NOP"

        print(
            f"0x{ins.address:08X}: "
            f"{ins.mnemonic:<8} {ins.op_str:<34}"
            f"{marker}"
        )

dump(
    0x7F4580,
    0x7F47B8,
    "A) FULL ACTIVE CLASSIFIER"
)

dump(
    0x7F4680,
    0x7F46D8,
    "B) EXACT VIRTUAL UJ CALL WINDOW"
)

dump(
    0x7F2A50,
    0x7F2AD0,
    "C) P65 SOURCE-PARITY NOP"
)

dump(
    0x7D30E0,
    0x7D31A0,
    "D) VANILLA F58 IMPLEMENTATION 0x7D3138"
)

print()
print("P66_RAW_DISASM=PASS")
