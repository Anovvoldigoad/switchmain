#!/usr/bin/env python3

from pathlib import Path
import struct

try:
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
except Exception as e:
    raise SystemExit(
        "FATAL: capstone unavailable: " + str(e)
    )

ROOT = Path("/storage/emulated/0/Downloads")

candidates = [
    ROOT / "deploy/atmosphere/contents/0100FA10190A0000/exefs/main",
    ROOT / "restore/atmosphere/contents/0100FA10190A0000/exefs/main",
    ROOT / "main",
]

MAIN = next((p for p in candidates if p.is_file()), None)

if MAIN is None:
    raise SystemExit("FATAL: main tidak ditemukan")

b = MAIN.read_bytes()

if b[:4] != b"NSO0":
    raise SystemExit("FATAL: bukan NSO0")

flags = struct.unpack_from("<I", b, 0x0C)[0]

text_file_off = struct.unpack_from("<I", b, 0x10)[0]
text_mem_off  = struct.unpack_from("<I", b, 0x14)[0]
text_size     = struct.unpack_from("<I", b, 0x18)[0]

print("MAIN=" + str(MAIN))
print(f"NSO_FLAGS=0x{flags:X}")
print(f"TEXT_FILE_OFF=0x{text_file_off:X}")
print(f"TEXT_MEM_OFF=0x{text_mem_off:X}")
print(f"TEXT_SIZE=0x{text_size:X}")

# NSO flag bit0 = compressed text.
# This main must expose uncompressed text for direct RVA->file mapping.
if flags & 1:
    raise SystemExit(
        "FATAL: text segment compressed; direct mapper invalid"
    )

def rva_to_file(rva):
    rel = rva - text_mem_off

    if rel < 0 or rel >= text_size:
        raise RuntimeError(
            f"RVA 0x{rva:X} outside text"
        )

    return text_file_off + rel

def word(rva):
    off = rva_to_file(rva)

    if off + 4 > len(b):
        raise RuntimeError("read outside file")

    return struct.unpack_from("<I", b, off)[0]

def words(rva, count):
    return [
        word(rva + i * 4)
        for i in range(count)
    ]

def sign_extend(v, bits):
    sign = 1 << (bits - 1)
    return (v ^ sign) - sign

def decode_bl_target(pc, w):
    if (w & 0xFC000000) != 0x94000000:
        raise RuntimeError(
            f"0x{pc:X}: expected BL, got 0x{w:08X}"
        )

    imm26 = w & 0x03FFFFFF
    imm26 = sign_extend(imm26, 26)

    return pc + (imm26 << 2)

md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)

PARENT = 0x7EAC34
A      = 0x7EAC70
B      = 0x7EACF0


# ================================================================
# EXACT FINGERPRINTS
# ================================================================

parent_expected = [
    0xA9BF4FFE,
    0xAA0003F3,
    0x9400000D,
    0x34000080,
    0x52800020,
    0xA8C14FFE,
    0xD65F03C0,
    0xF9400268,
]

a_expected = [
    0xA9BF4FFE,
    0xB94E9408,
    0x7101F11F,
    0x54000081,
    0x52800020,
    0xA8C14FFE,
    0xD65F03C0,
    0xAA0003F3,
]

b_expected = [
    0xF81F0FFE,
    0x5281F008,
    0x72A00028,
    0x52800021,
    0xF8686800,
    0x97FE31A1,
    0xF100001F,
    0x1A9F07E0,
]

for name, rva, expected in (
    ("PARENT", PARENT, parent_expected),
    ("A", A, a_expected),
    ("B", B, b_expected),
):
    got = words(rva, len(expected))

    print()
    print(f"===== {name} RVA=0x{rva:X} =====")
    print(
        "FIRST8="
        + ",".join(
            f"0x{x:08X}" for x in got
        )
    )

    if got != expected:
        print("EXPECTED=")
        print(
            ",".join(
                f"0x{x:08X}" for x in expected
            )
        )
        raise SystemExit(
            f"FATAL: {name} fingerprint mismatch"
        )

    print(f"{name}_FINGERPRINT=PASS")


# ================================================================
# EXACT PARENT CALLSITE A
# ================================================================

a_call_rva = 0x7EAC3C
a_call_word = word(a_call_rva)

a_target = decode_bl_target(
    a_call_rva,
    a_call_word
)

print()
print("===== A CALLSITE =====")
print(
    f"RVA=0x{a_call_rva:X} "
    f"WORD=0x{a_call_word:08X} "
    f"TARGET=0x{a_target:X} "
    f"LR=0x{a_call_rva + 4:X}"
)

if a_target != A:
    raise SystemExit(
        "FATAL: A target mismatch"
    )

if a_call_rva + 4 != 0x7EAC40:
    raise SystemExit(
        "FATAL: A LR mismatch"
    )

print("A_CALLSITE=PASS")


# ================================================================
# EXACT PARENT VIRTUAL +0x1298 CALLSITE B
# ================================================================

slot_load_rva = 0x7EAC58
blr_rva       = 0x7EAC5C

slot_word = word(slot_load_rva)
blr_word  = word(blr_rva)

print()
print("===== B CALLSITE =====")
print(
    f"SLOT_LOAD RVA=0x{slot_load_rva:X} "
    f"WORD=0x{slot_word:08X}"
)
print(
    f"BLR RVA=0x{blr_rva:X} "
    f"WORD=0x{blr_word:08X} "
    f"LR=0x{blr_rva + 4:X}"
)

# LDR X8,[X8,#0x1298]
if slot_word != 0xF9494D08:
    raise SystemExit(
        "FATAL: +0x1298 slot load mismatch"
    )

imm12 = (slot_word >> 10) & 0xFFF
slot_offset = imm12 * 8

print(f"VTABLE_SLOT_OFFSET=0x{slot_offset:X}")

if slot_offset != 0x1298:
    raise SystemExit(
        "FATAL: expected vtable +0x1298"
    )

# BLR X8
if blr_word != 0xD63F0100:
    raise SystemExit(
        "FATAL: expected BLR X8"
    )

if blr_rva + 4 != 0x7EAC60:
    raise SystemExit(
        "FATAL: B LR mismatch"
    )

print("B_CALLSITE=PASS")


# ================================================================
# B ABI-CRITICAL PROLOGUE
# ================================================================

# B:
#   save LR
#   W8 = 0x10F80
#   W1 = 1
#   X0 = [X0 + X8]
#   BL 0x777388
#   result -> bool
b10 = words(B, 10)

if b10[3] != 0x52800021:
    raise SystemExit(
        "FATAL: B does not define W1=1"
    )

if b10[4] != 0xF8686800:
    raise SystemExit(
        "FATAL: B actor-derived X0 load mismatch"
    )

if b10[8] != 0xF84107FE:
    raise SystemExit(
        "FATAL: B frame restore mismatch"
    )

if b10[9] != 0xD65F03C0:
    raise SystemExit(
        "FATAL: B RET mismatch"
    )

print()
print("B_ABI_BOOL_ACTOR_ONLY=PASS")


# ================================================================
# DISASSEMBLY — HUMAN AUDIT
# ================================================================

for name, rva, size in (
    ("PARENT", PARENT, 0x3C),
    ("A", A, 0x80),
    ("B", B, 0x28),
):
    print()
    print(
        f"===== DISASM {name} 0x{rva:X} ====="
    )

    off = rva_to_file(rva)
    blob = b[off:off + size]

    insns = list(md.disasm(blob, rva))

    if not insns:
        raise SystemExit(
            f"FATAL: capstone failed at {name}"
        )

    for ins in insns:
        print(
            f"0x{ins.address:08X}: "
            f"{ins.mnemonic:<7} {ins.op_str}"
        )


print()
print("P79_SUBPREDICATE_PREFLIGHT_V2=PASS")
print("A_TARGET=0x7EAC70")
print("A_CALLER_LR=0x7EAC40")
print("B_TARGET=0x7EACF0")
print("B_CALLER_LR=0x7EAC60")
