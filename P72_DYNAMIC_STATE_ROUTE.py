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

def dump(lo, hi, title):
    print()
    print("===== " + title + " =====")

    for i in dis(lo, hi):
        mark = ""

        if i.address == 0x7F47B8:
            mark = "   <<< UJ W21=0x87"

        elif i.address == 0x7F4820:
            mark = "   <<< W21 FORWARDED"

        elif i.address == 0x7F4890:
            mark = "   <<< W21=0x8D"

        elif i.address == 0x7F4910:
            mark = "   <<< CALL 0x795350"

        elif i.address == 0x7F4914:
            mark = "   <<< W21=RETURN"

        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str:<36}"
            f"{mark}"
        )

print("===== P72 TARGET =====")
print("Build ID:", bid)
print("Dynamic selector: 0x795350")

dump(
    0x7F47BC,
    0x7F4840,
    "A) 0x87 / 0x8D COMMON DISPATCHER"
)

dump(
    0x7F4878,
    0x7F489C,
    "B) 0x8D FORK"
)

dump(
    0x7F48E8,
    0x7F49A8,
    "C) DYNAMIC STATE ROUTE"
)

print()
print("===== D) BRANCHES INTO IMPORTANT BLOCKS =====")

wanted = {
    0x7F47BC,
    0x7F4890,
    0x7F490C,
}

for i in dis(0x7F4404, 0x7F5000):
    if not (
        i.mnemonic == "b"
        or i.mnemonic.startswith("b.")
        or i.mnemonic in (
            "cbz",
            "cbnz",
            "tbz",
            "tbnz",
        )
    ):
        continue

    m = re.findall(
        r"#0x([0-9a-fA-F]+)",
        i.op_str
    )

    if not m:
        continue

    dst = int(m[-1], 16)

    if dst in wanted:
        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<7} "
            f"{i.op_str}"
        )

print()
print("===== E) HELPER 0x795350 BODY =====")

for i in dis(0x795350, 0x795450):
    mark = ""
    op = i.op_str.lower()

    if any(x in op for x in (
        "#0xe54",
        "#0xe94",
        "#0xe98",
        "#0xe9c",
    )):
        mark = "   <<< ACTOR CHAR/STATE"

    if i.mnemonic == "ret":
        mark = "   <<< RET"

    print(
        f"0x{i.address:08X}: "
        f"{i.mnemonic:<8} "
        f"{i.op_str:<36}"
        f"{mark}"
    )

print()
print("===== F) DIRECT CALLERS OF 0x795350 =====")

count = 0

for i in dis(0x700000, 0x850000):
    if i.mnemonic != "bl":
        continue

    m = re.findall(
        r"#0x([0-9a-fA-F]+)",
        i.op_str
    )

    if not m:
        continue

    if int(m[-1], 16) == 0x795350:
        count += 1
        print(
            f"{count:02d}. caller=0x{i.address:08X}"
        )

print("caller_count =", count)

print()
print("P72_DYNAMIC_STATE_ROUTE=PASS")
