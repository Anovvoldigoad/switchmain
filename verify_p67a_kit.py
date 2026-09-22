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

BID = (
    "48ece454b61412b9fb46fab2be3f5ef"
    "7b2804f39"
)


def die(s):
    raise SystemExit("FAIL: " + s)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def load(path):
    raw = path.read_bytes()

    if raw[:4] != b"NSO0":
        die(f"{path}: not NSO0")

    bid = raw[0x40:0x54].hex()

    if bid.lower() != BID.lower():
        die(
            f"{path}: Build ID mismatch {bid}"
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
        die("text size mismatch")

    return raw, text, mem


def word(text, mem, va):
    off = va - mem

    if off < 0 or off + 4 > len(text):
        die(f"VA 0x{va:X} outside text")

    return struct.unpack_from(
        "<I",
        text,
        off
    )[0]


def bl_target(pc, w):
    if (w & 0xFC000000) != 0x94000000:
        return None

    imm = w & 0x03FFFFFF

    if imm & 0x02000000:
        imm -= 0x04000000

    return pc + (imm << 2)


cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
maincpp = MAINCPP.read_text(encoding="utf-8")

required = [
    "kUjSemanticActivePlayerReturnOffset = 0x7F4730",
    "caller_off == kUjSemanticActivePlayerReturnOffset",
    "InstallP67ActiveSelector1ConsumerBridge",
    "InstallP67AActiveSelector1ConsumerBridge",
    "[NSC:P67A] READY",
]

for x in required:
    if x not in cpp:
        die("missing source marker: " + x)

if (
    "void InstallP67AActiveSelector1ConsumerBridge();"
    not in hpp
):
    die("P67 HPP declaration missing")

if (
    "nsc::InstallP67AActiveSelector1ConsumerBridge();"
    not in maincpp
):
    die("main does not call P67")

for forbidden in (
    "nsc::InstallP66AVirtualUjSemanticBridge();",
    "nsc::InstallP65ASourceParityActiveUjBridge();",
    "nsc::InstallP64FUjSemanticBridge();",
):
    if forbidden in maincpp:
        die(
            "legacy installer still active: "
            + forbidden
        )

# Make sure the P67 top-level itself does NOT install
# P65/P66/F58 routes.
a = cpp.find(
    "void InstallP67AActiveSelector1ConsumerBridge()"
)

if a < 0:
    die("P67 body missing")

next_candidates = [
    x for x in (
        cpp.find(
            "void InstallP66AVirtualUjSemanticBridge()",
            a + 1
        ),
        cpp.find(
            "void InstallP65ASourceParityActiveUjBridge()",
            a + 1
        ),
        cpp.find(
            "void InstallP52APreUjProbe()",
            a + 1
        ),
    )
    if x >= 0
]

b = min(next_candidates) if next_candidates else len(cpp)

body = cpp[a:b]

for forbidden in (
    "InstallP65ActiveUjEligibilityBridge()",
    "InstallP66ActiveUjVirtualCallBridge()",
    "InstallP63UjRouterTrace()",
):
    if forbidden in body:
        die(
            "P67 body installs forbidden route: "
            + forbidden
        )

if (
    "InstallP67ActiveSelector1ConsumerBridge()"
    not in body
):
    die("P67 functional installer missing")

for pat in (
    r"char_id\s*==\s*281",
    r"char_id\s*!=\s*281",
    r"char_id\s*==\s*0x119",
    r"char_id\s*!=\s*0x119",
):
    if re.search(pat, cpp):
        die(
            "character-specific branch found: "
            + pat
        )

raw, text, mem = load(DEPLOY)

# Source parity NOP remains.
if (
    word(text, mem, 0x7F2A9C)
    != 0xD503201F
):
    die(
        "paired main missing "
        "0x7F2A9C NOP"
    )

# Active player call to semantic/native selector1 helper.
if (
    word(text, mem, 0x7F4728)
    != 0xAA1303E0
):
    die("0x7F4728 fingerprint")

w = word(text, mem, 0x7F472C)

if (
    bl_target(0x7F472C, w)
    != 0x7ABE9C
):
    die(
        "0x7F472C does not call 0x7ABE9C"
    )

if (
    word(text, mem, 0x7F4730)
    != 0x35FFEE40
):
    die("0x7F4730 fingerprint")

# Inside helper: selector1 must be loaded immediately
# before native control getter.
if (
    word(text, mem, 0x7ABF2C)
    != 0x52800021
):
    die(
        "0x7ABF2C is not MOV W1,#1"
    )

w = word(text, mem, 0x7ABF30)

if (
    bl_target(0x7ABF30, w)
    != 0x7C6280
):
    die(
        "0x7ABF30 does not call "
        "native control getter"
    )

_, restore_text, restore_mem = load(RESTORE)

if (
    word(
        restore_text,
        restore_mem,
        0x7F2A9C
    )
    != 0xBD001FE0
):
    die(
        "restore main not pristine "
        "at 0x7F2A9C"
    )

print("P67_SOURCE_VERIFY=PASS")
print(
    "P67_ACTIVE_CALL_VERIFY=PASS "
    "0x7F472C->0x7ABE9C"
)
print(
    "P67_SELECTOR1_VERIFY=PASS "
    "0x7ABF2C=W1#1 "
    "0x7ABF30->0x7C6280"
)
print(
    "P67_MAIN_PREREQ_VERIFY=PASS "
    "0x7F2A9C=D503201F"
)
print(
    "DEPLOY_MAIN_SHA256="
    + hashlib.sha256(raw).hexdigest()
)
print("P67A_STATIC_VERIFY=PASS")
