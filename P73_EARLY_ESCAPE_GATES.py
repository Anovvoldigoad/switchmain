#!/usr/bin/env python3

from pathlib import Path
import struct
import re
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

def die(s):
    raise SystemExit("FATAL: " + s)

if raw[:4] != b"NSO0":
    die("main bukan NSO0")

bid = raw[0x40:0x54].hex()

if bid.lower() != BID.lower():
    die("Build ID mismatch: " + bid)

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

def dis(lo, hi):
    return list(
        md.disasm(
            text[lo-mem:hi-mem],
            lo
        )
    )

def dump(lo, hi, title, marks=None):
    marks = marks or {}

    print()
    print("===== " + title + " =====")

    for i in dis(lo, hi):
        mark = marks.get(i.address, "")

        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str:<38}"
            f"{mark}"
        )

print("===== P73 TARGET =====")
print("Build ID:", bid)

dump(
    0x7F45C0,
    0x7F4644,
    "A) ACTIVE CLASSIFIER EARLY ESCAPE CORRIDOR",
    {
        0x7F45F4: "   <<< GATE A CALL",
        0x7F45F8: "   <<< GATE A RESULT -> 0x7F490C",
        0x7F4634: "   <<< GATE B CALL",
        0x7F4638: "   <<< GATE B RESULT",
        0x7F463C: "   <<< ESCAPE -> 0x7F490C",
    }
)

dump(
    0x7C553C,
    0x7C55C0,
    "B) HELPER 0x7C553C"
)

dump(
    0x7C5FC0,
    0x7C6020,
    "C) HELPER 0x7C5FC0"
)

print()
print("===== D) DIRECT CALLER COUNT =====")

targets = {
    0x7C553C: [],
    0x7C5FC0: [],
}

for i in dis(0x700000, 0x850000):
    if i.mnemonic != "bl":
        continue

    m = re.findall(
        r"#0x([0-9a-fA-F]+)",
        i.op_str
    )

    if not m:
        continue

    dst = int(m[-1], 16)

    if dst in targets:
        targets[dst].append(i.address)

for target, callers in targets.items():
    print(
        f"target=0x{target:08X} "
        f"direct_callers={len(callers)}"
    )

    # Keep output bounded.
    for pc in callers[:12]:
        print(
            f"  caller=0x{pc:08X}"
        )

print()
print("===== E) ACTIVE CALL ARGUMENT SUMMARY =====")

corridor = {
    i.address: i
    for i in dis(0x7F45D8, 0x7F4640)
}

for call in (0x7F45F4, 0x7F4634):
    print()
    print(f"--- CALL 0x{call:08X} ---")

    for pc in range(call - 0x14, call + 8, 4):
        i = corridor.get(pc)

        if i:
            mark = "   <<< CALL" if pc == call else ""

            print(
                f"0x{i.address:08X}: "
                f"{i.mnemonic:<8} "
                f"{i.op_str:<38}"
                f"{mark}"
            )

print()
print("P73_EARLY_ESCAPE_GATES=PASS")
