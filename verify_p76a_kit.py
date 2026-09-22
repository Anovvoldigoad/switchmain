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
    "nsc::InstallP76AForkRuntimeProbe();"
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

# =====================================================================
# P76A read-only fork-probe invariants.
# Keep all P67A baseline verification above; P76A wraps P67A.
# =====================================================================

_p76_cpp = CPP.read_text(encoding="utf-8")
_p76_hpp = HPP.read_text(encoding="utf-8")
_p76_main = MAINCPP.read_text(encoding="utf-8")

def _p76_need(label, haystack, needle):
    if needle not in haystack:
        raise SystemExit(
            "P76A_VERIFY_FAIL: "
            + label
            + " missing: "
            + needle
        )

# Public architecture.
_p76_need(
    "header",
    _p76_hpp,
    "void InstallP76AForkRuntimeProbe();"
)

if _p76_main.count(
    "nsc::InstallP76AForkRuntimeProbe();"
) != 1:
    raise SystemExit(
        "P76A_VERIFY_FAIL: main must install P76A exactly once"
    )

if (
    "nsc::InstallP67AActiveSelector1ConsumerBridge();"
    in _p76_main
):
    raise SystemExit(
        "P76A_VERIFY_FAIL: main must not independently install P67A"
    )

# Exact static targets.
for needle in (
    "kP76AltCorridorOffset",
    "0x8B2D04",
    "kP76UjCorridorOffset",
    "0x8B2B70",
    "kP76AltCallerReturnOffset",
    "0x7F4598",
    "kP76UjCallerReturnOffset",
    "0x7F4648",
):
    _p76_need(
        "target",
        _p76_cpp,
        needle
    )

# Hooks and markers.
for needle in (
    "HOOK_DEFINE_TRAMPOLINE(P76AltCorridorHook)",
    "HOOK_DEFINE_TRAMPOLINE(P76UjCorridorHook)",
    "[NSC:P76A] ALT_CORRIDOR",
    "[NSC:P76A] UJ_CORRIDOR",
    "[NSC:P76A] READY",
):
    _p76_need(
        "probe",
        _p76_cpp,
        needle
    )

# Fingerprints established by P75 preflight.
for word in (
    # ALT 0x8B2D04
    "0xF81D0FFE",
    "0xA90157F6",
    "0xA9024FF4",
    "0x5282E208",
    "0x72A00028",
    "0xAA0003F3",
    "0xB8686814",
    "0x97FBE29D",

    # UJ 0x8B2B70
    "0xF81E0FFE",
    "0xA9014FF4",
    "0x9108A014",
    "0xAA1403E0",
    "0x52800101",
    "0x97FC4DBE",
    "0x340000A0",
):
    _p76_need(
        "fingerprint",
        _p76_cpp,
        word
    )

# Slice exact probe bodies.
_alt0 = _p76_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P76AltCorridorHook)"
)
_uj0 = _p76_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P76UjCorridorHook)"
)
_p64 = _p76_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P64SemanticUjConsumerHook)",
    _uj0
)

if min(_alt0, _uj0, _p64) < 0:
    raise SystemExit(
        "P76A_VERIFY_FAIL: unable to bound probe hook bodies"
    )

_alt = _p76_cpp[_alt0:_uj0]
_uj = _p76_cpp[_uj0:_p64]

for name, body in (
    ("ALT", _alt),
    ("UJ", _uj),
):
    if body.count(
        "const uint32_t ret = Orig(actor);"
    ) != 1:
        raise SystemExit(
            "P76A_VERIFY_FAIL: "
            + name
            + " must call Orig(actor) exactly once"
        )

    if body.count("return ret;") != 1:
        raise SystemExit(
            "P76A_VERIFY_FAIL: "
            + name
            + " must return native ret exactly once"
        )

    if "return 1;" in body:
        raise SystemExit(
            "P76A_VERIFY_FAIL: "
            + name
            + " contains forced return 1"
        )

# Installer.
_inst0 = _p76_cpp.find(
    "void InstallP76AForkRuntimeProbe()"
)

if _inst0 < 0:
    raise SystemExit(
        "P76A_VERIFY_FAIL: installer missing"
    )

_inst = _p76_cpp[_inst0:]

if _inst.count(
    "InstallP67AActiveSelector1ConsumerBridge();"
) != 1:
    raise SystemExit(
        "P76A_VERIFY_FAIL: P76A must wrap P67A exactly once"
    )

for needle in (
    "P76AltCorridorHook::InstallAtOffset",
    "P76UjCorridorHook::InstallAtOffset",
    'LogFingerprintFail(',
    '"P76_ALT_CORRIDOR"',
    '"P76_UJ_CORRIDOR"',
    "readonly=1",
    "preserve_orig=1",
    "no_force87=1",
    "no_force700=1",
    "no_selector8=1",
    "no_f58_override=1",
    "no_char281_branch=1",
):
    _p76_need(
        "installer",
        _inst,
        needle
    )

print("P76A_EXTENSION_VERIFY=PASS")

print("P76A_STATIC_VERIFY=PASS")
