#!/usr/bin/env python3

from pathlib import Path
import re
import struct
import hashlib
import lz4.block

ROOT = Path(__file__).resolve().parent

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAINCPP = ROOT / "overlay/source/program/main.cpp"

DEPLOY = ROOT / (
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

RESTORE = ROOT / (
    "restore/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

TARGET_BID = (
    "48ece454b61412b9fb46fab2be3f5ef"
    "7b2804f39"
)


def die(s):
    raise SystemExit("FAIL: " + s)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load_text(path):
    raw = path.read_bytes()

    if raw[:4] != b"NSO0":
        die(f"{path}: not NSO0")

    bid = raw[0x40:0x54].hex()

    if bid.lower() != TARGET_BID.lower():
        die(
            f"{path}: Build ID mismatch "
            f"{bid}"
        )

    flags = u32(raw, 0x0C)

    fileoff = u32(raw, 0x10)
    memoff = u32(raw, 0x14)
    size = u32(raw, 0x18)
    csize = u32(raw, 0x60)

    src = raw[
        fileoff:
        fileoff + csize
    ]

    if flags & 1:
        text = lz4.block.decompress(
            src,
            uncompressed_size=size
        )
    else:
        text = raw[
            fileoff:
            fileoff + size
        ]

    if len(text) != size:
        die("text size mismatch")

    return raw, text, memoff


def word(text, mem, va):
    off = va - mem

    if off < 0 or off + 4 > len(text):
        die(f"VA 0x{va:X} outside text")

    return struct.unpack_from(
        "<I",
        text,
        off
    )[0]


cpp = CPP.read_text(
    encoding="utf-8"
)

hpp = HPP.read_text(
    encoding="utf-8"
)

maincpp = MAINCPP.read_text(
    encoding="utf-8"
)

required = [
    "P66ActiveUjVirtualCallHook",
    "InstallP66ActiveUjVirtualCallBridge",
    "InstallP66AVirtualUjSemanticBridge",
    "[NSC:P66A] UJ_VCALL_GATE",
    "kP66ActiveUjVirtualCallOffset = 0x7F46B4",
    "P64QuerySemanticUltimateJutsu(actor)",
    "ctx->W[0] = out",
]

for x in required:
    if x not in cpp:
        die(
            "missing source marker: " + x
        )

if (
    "void InstallP66AVirtualUjSemanticBridge();"
    not in hpp
):
    die("missing HPP declaration")

if (
    "nsc::InstallP66AVirtualUjSemanticBridge();"
    not in maincpp
):
    die("main does not call P66")

if (
    "nsc::InstallP65ASourceParityActiveUjBridge();"
    in maincpp
):
    die("main still calls P65")

a = cpp.find(
    "void InstallP66AVirtualUjSemanticBridge()"
)

b = cpp.find(
    "void InstallP65ASourceParityActiveUjBridge()",
    a
)

if a < 0 or b < 0:
    die(
        "cannot isolate P66 top-level"
    )

body = cpp[a:b]

for forbidden in (
    "InstallP65ActiveUjEligibilityBridge()",
    "InstallP64SemanticUjBridge()",
    "InstallP63UjRouterTrace()",
):
    if forbidden in body:
        die(
            "P66 active path contains "
            + forbidden
        )

if (
    "InstallP66ActiveUjVirtualCallBridge()"
    not in body
):
    die("P66 bridge not active")

for pat in (
    r"char_id\s*==\s*281",
    r"char_id\s*!=\s*281",
    r"char_id\s*==\s*0x119",
    r"char_id\s*!=\s*0x119",
):
    if re.search(pat, cpp):
        die(
            "character-specific branch: "
            + pat
        )

raw, text, mem = load_text(DEPLOY)

if (
    word(text, mem, 0x7F2A9C)
    != 0xD503201F
):
    die(
        "paired main missing "
        "0x7F2A9C NOP"
    )

expected = {
    0x7F46A4: 0xF9400268,
    0x7F46A8: 0xAA1303E0,
    0x7F46AC: 0x2A1F03E1,
    0x7F46B0: 0xF947AD08,
    0x7F46B4: 0xD63F0100,
    0x7F46B8: 0x34000400,
    0x7F46BC: 0xAA1303E0,
    0x7F46C0: 0x2A1F03E1,
    0x7F46C4: 0x97FF79C8,
}

for va, exp in expected.items():
    got = word(
        text,
        mem,
        va
    )

    if got != exp:
        die(
            f"callsite fingerprint "
            f"0x{va:X}: "
            f"{got:08X} != {exp:08X}"
        )

_, restore_text, restore_mem = (
    load_text(RESTORE)
)

if (
    word(
        restore_text,
        restore_mem,
        0x7F2A9C
    )
    != 0xBD001FE0
):
    die(
        "restore main is not pristine "
        "at 0x7F2A9C"
    )

print("P66_SOURCE_VERIFY=PASS")
print("P66_VCALL_FINGERPRINT=PASS")
print(
    "P66_MAIN_PREREQ_VERIFY=PASS "
    "0x7F2A9C=D503201F"
)
print(
    "DEPLOY_MAIN_SHA256="
    + hashlib.sha256(
        raw
    ).hexdigest()
)
print("P66A_STATIC_VERIFY=PASS")
