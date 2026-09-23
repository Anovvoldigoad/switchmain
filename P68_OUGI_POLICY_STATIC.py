#!/usr/bin/env python3

from pathlib import Path
import struct
import hashlib
import lz4.block

from capstone import (
    Cs,
    CS_ARCH_ARM64,
    CS_MODE_ARM,
)

TARGET_BID = "48ece454b61412b9fb46fab2be3f5ef7b2804f39"

DEPLOY = Path(
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

# ----------------------------------------------------------------
# Proven / current anchors
# ----------------------------------------------------------------

ACTIVE_LO = 0x7F4400
ACTIVE_HI = 0x7F4FC0

F58_BLR = 0x7F46B4
P65_NOP = 0x7F2A9C

# PC source anchors.
PC_A33 = 0xA33C60
PC_A20 = 0xA20C00

# Only a geographic prediction.
DELTA_FROM_A33 = PC_A33 - P65_NOP
PRED_A20 = PC_A20 - DELTA_FROM_A33

# Inspect enough around predicted region.
PRED_LO = PRED_A20 - 0x1000
PRED_HI = PRED_A20 + 0x1000


def fatal(msg):
    raise SystemExit("FATAL: " + msg)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def sign(v, bits):
    m = 1 << (bits - 1)
    return (v ^ m) - m


def decode_nso(path):
    raw = path.read_bytes()

    if raw[:4] != b"NSO0":
        fatal("deploy main bukan NSO0")

    bid = raw[0x40:0x54].hex()

    if bid.lower() != TARGET_BID.lower():
        fatal(
            "Build ID mismatch: "
            + bid
        )

    flags = u32(raw, 0x0C)
    foff = u32(raw, 0x10)
    mem = u32(raw, 0x14)
    size = u32(raw, 0x18)
    csize = u32(raw, 0x60)

    src = raw[foff:foff+csize]

    if flags & 1:
        text = lz4.block.decompress(
            src,
            uncompressed_size=size
        )
    else:
        text = raw[foff:foff+size]

    if len(text) != size:
        fatal("decoded text size mismatch")

    return {
        "raw": raw,
        "text": text,
        "mem": mem,
        "size": size,
    }


IMG = decode_nso(DEPLOY)
TEXT = IMG["text"]
BASE = IMG["mem"]

md = Cs(
    CS_ARCH_ARM64,
    CS_MODE_ARM
)


def get_bytes(lo, hi):
    a = lo - BASE
    b = hi - BASE

    if a < 0 or b > len(TEXT):
        fatal(
            f"range outside text "
            f"0x{lo:X}..0x{hi:X}"
        )

    return TEXT[a:b]


def insns(lo, hi):
    return list(
        md.disasm(
            get_bytes(lo, hi),
            lo
        )
    )


def one(pc):
    xs = insns(pc, pc+4)
    return xs[0] if xs else None


def word(pc):
    o = pc - BASE

    if o < 0 or o + 4 > len(TEXT):
        fatal(f"word outside text 0x{pc:X}")

    return struct.unpack_from(
        "<I",
        TEXT,
        o
    )[0]


def decode_bl(pc, w):
    if (w & 0xFC000000) != 0x94000000:
        return None

    imm = sign(
        w & 0x03FFFFFF,
        26
    ) << 2

    return pc + imm


def is_w0_consumer(ins):
    if not ins:
        return False

    m = ins.mnemonic
    op = ins.op_str.lower()

    if m in (
        "cbz",
        "cbnz",
    ) and op.startswith("w0"):
        return True

    if m in (
        "cmp",
        "cmn",
        "tst",
    ) and (
        op.startswith("w0")
        or op.startswith("x0")
    ):
        return True

    return False


def direct_calls(lo, hi):
    out = []

    for pc in range(lo, hi, 4):
        dst = decode_bl(
            pc,
            word(pc)
        )

        if dst is not None:
            out.append(
                (pc, dst)
            )

    return out


def all_callers(target):
    out = []

    for off in range(
        0,
        len(TEXT) - 3,
        4
    ):
        pc = BASE + off
        w = struct.unpack_from(
            "<I",
            TEXT,
            off
        )[0]

        dst = decode_bl(pc, w)

        if dst == target:
            out.append(pc)

    return out


def fmt(ins):
    if not ins:
        return "<decode fail>"

    return (
        f"{ins.mnemonic:<8} "
        f"{ins.op_str}"
    )


def dump(lo, hi, title):
    print()
    print("=" * 104)
    print(title)
    print("=" * 104)

    for i in insns(lo, hi):
        mark = ""

        if i.address == P65_NOP:
            mark = "   <<< P65 SOURCE-PARITY NOP"

        if i.address == F58_BLR:
            mark = "   <<< ACTIVE F58 BLR"

        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str:<42}"
            f"{mark}"
        )


def dump_function_head(target, max_bytes=0x100):
    print(
        f"\n--- TARGET 0x{target:08X} ---"
    )

    callers = all_callers(target)

    print(
        f"direct_callers={len(callers)} "
        + " ".join(
            f"0x{x:X}"
            for x in callers[:20]
        )
    )

    interesting = False
    count = 0

    for i in insns(
        target,
        min(
            target + max_bytes,
            BASE + len(TEXT)
        )
    ):
        txt = (
            i.mnemonic
            + " "
            + i.op_str
        ).lower()

        marks = []

        for field in (
            "#0xe54",
            "#0xe60",
            "#0xe94",
            "#0xe98",
            "#0xe9c",
            "#0xea0",
            "#0xea4",
            "#0xea8",
            "#0x1238",
            "#0x10f40",
        ):
            if field in txt:
                marks.append(field)
                interesting = True

        if (
            i.mnemonic in (
                "cset",
                "cinc",
                "csinc",
                "csel",
            )
            or (
                i.mnemonic == "mov"
                and i.op_str.startswith("w0, #")
            )
        ):
            marks.append("BOOLISH")
            interesting = True

        mark = (
            "   <<< " + ",".join(marks)
            if marks else ""
        )

        print(
            f"0x{i.address:08X}: "
            f"{i.mnemonic:<8} "
            f"{i.op_str:<42}"
            f"{mark}"
        )

        count += 1

        if i.mnemonic == "ret":
            break

        if count >= 64:
            break

    print(
        "interesting_fields_or_bool="
        + (
            "YES"
            if interesting
            else "NO"
        )
    )


print("===== TARGET =====")
print("BUILD_ID=" + TARGET_BID)
print(
    "DEPLOY_SHA256="
    + hashlib.sha256(
        IMG["raw"]
    ).hexdigest()
)
print(
    f"TEXT_MEM=0x{BASE:X}"
)
print(
    f"TEXT_SIZE=0x{len(TEXT):X}"
)

print()
print("===== SOURCE PARITY ANCHOR =====")
print(
    f"PC_A33=0x{PC_A33:X}"
)
print(
    f"SW_A33=0x{P65_NOP:X}"
)
print(
    f"DELTA=0x{DELTA_FROM_A33:X}"
)
print(
    f"PREDICTED_PC_A20_SWITCH≈0x{PRED_A20:X}"
)
print(
    "NOTE=PREDICTED ONLY, NOT A PATCH ADDRESS"
)

print()
print("===== ACTIVE DIRECT CALLS =====")

calls = direct_calls(
    ACTIVE_LO,
    ACTIVE_HI
)

targets = []

for pc, dst in calls:
    prev3 = [
        one(pc - 12),
        one(pc - 8),
        one(pc - 4),
    ]

    nxt = one(pc + 4)

    consumed = is_w0_consumer(nxt)

    argtxt = " | ".join(
        fmt(x)
        for x in prev3
        if x
    )

    print(
        f"CALL 0x{pc:08X} "
        f"-> 0x{dst:08X} "
        f"next=[{fmt(nxt)}] "
        f"w0_consumed={int(consumed)}"
    )

    print(
        "   PRE: "
        + argtxt
    )

    targets.append(
        (
            0 if consumed else 1,
            abs(dst - PRED_A20),
            pc,
            dst,
        )
    )

# Remove duplicate targets, prioritize:
# 1. immediate W0-consumed predicate calls
# 2. closeness to predicted A20 neighborhood
uniq = {}
for row in targets:
    key = row[3]

    if (
        key not in uniq
        or row < uniq[key]
    ):
        uniq[key] = row

ranked = sorted(
    uniq.values()
)

print()
print(
    "===== RANKED ACTIVE PREDICATE TARGETS ====="
)

for rank, row in enumerate(
    ranked,
    1
):
    consumed_class, dist, pc, dst = row

    print(
        f"{rank:02d}. "
        f"target=0x{dst:08X} "
        f"caller=0x{pc:08X} "
        f"w0_consumed={int(consumed_class == 0)} "
        f"distance_to_pred=0x{dist:X}"
    )

# Dump every unique target whose return is directly consumed,
# plus anything close to predicted A20.
selected = []

for row in ranked:
    consumed_class, dist, pc, dst = row

    if (
        consumed_class == 0
        or dist <= 0x4000
    ):
        if dst not in selected:
            selected.append(dst)

print()
print(
    "===== SELECTED TARGET FUNCTION WINDOWS ====="
)

for dst in selected:
    dump_function_head(
        dst,
        0x140
    )

dump(
    PRED_LO,
    PRED_HI,
    (
        "PREDICTED A20C00 HOMOLOG NEIGHBORHOOD "
        f"0x{PRED_LO:X}..0x{PRED_HI:X}"
    )
)

# Also dump the actual P65 source-parity region for context.
dump(
    0x7F2A70,
    0x7F2AC0,
    "P65 A33C60 SOURCE-PARITY CONTEXT"
)

print()
print("===== DECISION RULE =====")
print(
    "Do NOT patch any candidate from this output yet."
)
print(
    "Next target must satisfy BOTH:"
)
print(
    "1) static predicate contract compatible with actor/UJ eligibility"
)
print(
    "2) runtime reachability on Tobi XXA before requested=445"
)
print(
    "P68_STATIC_SWEEP=PASS"
)
