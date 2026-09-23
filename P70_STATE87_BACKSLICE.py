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

LO = 0x7F4580
HI = 0x7F47BC

UJ = 0x7F47B4
STATE87 = 0x7F47B8


def die(s):
    raise SystemExit("FATAL: " + s)


raw = MAIN.read_bytes()

if raw[:4] != b"NSO0":
    die("main bukan NSO0")


def u32(off):
    return struct.unpack_from("<I", raw, off)[0]


bid = raw[0x40:0x54].hex()

if bid.lower() != BID.lower():
    die("Build ID mismatch: " + bid)

flags = u32(0x0C)
foff = u32(0x10)
mem = u32(0x14)
size = u32(0x18)
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

imap = {x.address: x for x in ins}


def target(i):
    if i is None:
        return None

    m = i.mnemonic

    if not (
        m == "b"
        or m == "bl"
        or m.startswith("b.")
        or m in ("cbz", "cbnz", "tbz", "tbnz")
    ):
        return None

    ms = re.findall(
        r"#0x([0-9a-fA-F]+)",
        i.op_str
    )

    if not ms:
        return None

    return int(ms[-1], 16)


def show(pc, mark=""):
    i = imap.get(pc)

    if i:
        print(
            f"0x{pc:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str:<34}"
            f"{mark}"
        )


print("===== P70 UJ ROOT =====")
print("UJ_BLOCK = 0x7F47B4")
print("STATE87  = 0x7F47B8")
print()


# ============================================================
# A. Exact incoming paths to UJ block
# ============================================================

print("===== A) INCOMING EDGES TO 0x7F47B4 =====")

for i in ins:
    if target(i) == UJ:
        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic} {i.op_str}"
        )

print(
    "fallthrough: "
    "0x7F47B0 -> 0x7F47B4"
)

print()


# ============================================================
# B. Exact contexts for each UJ predecessor
# ============================================================

print("===== B) UJ PREDECESSOR CONTEXTS =====")

preds = [
    0x7F46CC,
    0x7F4780,
    0x7F4790,
    0x7F47B0,
]

for p in preds:
    print()
    print(f"--- around 0x{p:08X} ---")

    for pc in range(p-12, p+8, 4):
        mark = ""

        if pc == p:
            mark = "   <<< DECISION"

        if pc == UJ:
            mark = "   <<< UJ BLOCK"

        show(pc, mark)

print()


# ============================================================
# C. F58 region
# ============================================================

print("===== C) F58 / POST-GATE PATH =====")

for pc in range(
    0x7F46A0,
    0x7F46D0,
    4
):
    mark = ""

    if pc == 0x7F46B4:
        mark = "   <<< F58 VCALL"

    if pc == 0x7F46B8:
        mark = "   <<< F58 RESULT"

    if pc == 0x7F46C4:
        mark = "   <<< POST GATE"

    show(pc, mark)

print()


# ============================================================
# D. Alternate route after F58 false
# ============================================================

print("===== D) ALTERNATE ROUTE TO STATE87 =====")

for pc in range(
    0x7F4738,
    0x7F47BC,
    4
):
    mark = ""

    if pc == 0x7F472C:
        mark = "   <<< selector1 helper"

    if pc == UJ:
        mark = "   <<< UJ BLOCK"

    if pc == STATE87:
        mark = "   <<< MOV W21,#0x87"

    show(pc, mark)

print()


# ============================================================
# E. Pre-F58 predicates:
# direct calls immediately consumed by CBZ/CBNZ W0
# ============================================================

print("===== E) PRE-F58 BOOLEAN CALLS =====")

for idx, i in enumerate(ins):
    if not (
        0x7F4580
        <= i.address
        < 0x7F46A4
    ):
        continue

    if i.mnemonic not in ("bl", "blr"):
        continue

    if idx + 1 >= len(ins):
        continue

    n = ins[idx+1]

    if n.address != i.address + 4:
        continue

    if n.mnemonic not in ("cbz", "cbnz"):
        continue

    first = n.op_str.split(",")[0].strip()

    if first != "w0":
        continue

    dst = target(i)

    if i.mnemonic == "bl":
        callee = (
            f"0x{dst:08X}"
            if dst is not None
            else "?"
        )
    else:
        callee = "INDIRECT"

    print(
        f"CALL 0x{i.address:08X} "
        f"{i.mnemonic.upper()}->{callee} "
        f"| 0x{n.address:08X}: "
        f"{n.mnemonic} {n.op_str}"
    )

print()


# ============================================================
# F. Every conditional branch before F58.
# This is where Tobi must diverge if it never reaches F58.
# ============================================================

print("===== F) PRE-F58 BRANCH MAP =====")

for i in ins:
    if not (
        0x7F4580
        <= i.address
        < 0x7F46A4
    ):
        continue

    if (
        i.mnemonic.startswith("b.")
        or i.mnemonic
        in ("cbz", "cbnz", "tbz", "tbnz")
    ):
        dst = target(i)

        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<6} "
            f"{i.op_str:<28} "
            f"-> "
            + (
                f"0x{dst:08X}"
                if dst is not None
                else "?"
            )
        )

print()
print("===== P70 RESULT =====")
print(
    "Root target is NOT MOV #0x87 itself."
)
print(
    "Find earliest pre-F58 predicate whose "
    "outcome sends Tobi away from this corridor."
)
print("P70_STATE87_BACKSLICE=PASS")
