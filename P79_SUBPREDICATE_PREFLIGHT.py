#!/usr/bin/env python3

from pathlib import Path
import struct

try:
    from capstone import (
        Cs,
        CS_ARCH_ARM64,
        CS_MODE_ARM,
    )
except Exception as e:
    raise SystemExit(
        "FATAL: python capstone tidak tersedia: " + str(e)
    )

ROOT = Path("/storage/emulated/0/Downloads")

candidates = [
    ROOT / "deploy/atmosphere/contents/0100FA10190A0000/exefs/main",
    ROOT / "restore/atmosphere/contents/0100FA10190A0000/exefs/main",
    ROOT / "main",
]

MAIN = next((p for p in candidates if p.is_file()), None)

if MAIN is None:
    raise SystemExit(
        "FATAL: main Switch 1.70 tidak ditemukan"
    )

b = MAIN.read_bytes()

if b[:4] != b"NSO0":
    raise SystemExit(
        "FATAL: target bukan NSO0"
    )

# Existing project layout:
# NSO text RVA maps to file offset RVA + 0x100.
TEXT_FILE_BIAS = 0x100

md = Cs(
    CS_ARCH_ARM64,
    CS_MODE_ARM
)

targets = {
    "PARENT": (0x7EAC34, 0x90),
    "A":      (0x7EAC70, 0x80),
    "B":      (0x7EACF0, 0x80),
}

print("MAIN=" + str(MAIN))
print()

for name, (rva, size) in targets.items():
    off = TEXT_FILE_BIAS + rva

    if off + size > len(b):
        raise SystemExit(
            f"FATAL: {name} outside file"
        )

    blob = b[off:off + size]

    print(
        f"===== {name} RVA=0x{rva:X} ====="
    )

    words = [
        struct.unpack_from("<I", blob, i)[0]
        for i in range(0, 32, 4)
    ]

    print(
        "FIRST8="
        + ",".join(
            f"0x{x:08X}" for x in words
        )
    )

    for ins in md.disasm(blob, rva):
        print(
            f"0x{ins.address:08X}: "
            f"{ins.mnemonic:<7} {ins.op_str}"
        )

    print()

print("===== REQUIRED CALLSITE CHECK =====")

parent_off = TEXT_FILE_BIAS + 0x7EAC34
parent = b[parent_off:parent_off + 0x40]

seen_a = False
seen_b = False

for ins in md.disasm(parent, 0x7EAC34):
    if ins.address == 0x7EAC3C:
        print(
            "A_CALLSITE:",
            f"{ins.mnemonic} {ins.op_str}",
            "LR_EXPECT=0x7EAC40"
        )
        seen_a = True

    if ins.address == 0x7EAC5C:
        print(
            "B_CALLSITE:",
            f"{ins.mnemonic} {ins.op_str}",
            "LR_EXPECT=0x7EAC60"
        )
        seen_b = True

if not seen_a:
    print("A_CALLSITE=NOT_SEEN")

if not seen_b:
    print("B_CALLSITE=NOT_SEEN")

print()
print("P79_SUBPREDICATE_PREFLIGHT=DONE")
