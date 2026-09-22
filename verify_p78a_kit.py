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
    "nsc::InstallP78ASemanticAltRouteProbe();"
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
    "nsc::InstallP78ASemanticAltRouteProbe();"
) != 1:
    raise SystemExit(
        "P76A_VERIFY_FAIL: main must install P77A exactly once"
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
# P77A is inserted after the historical P76 UJ hook.
# Bound the P76 UJ body at P77 when present, otherwise fall back
# to the original P64 boundary.
_p64 = _p76_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P78AltRouteHook)",
    _uj0
)

if _p64 < 0:
    _p64 = _p76_cpp.find(
        "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)",
        _uj0
    )

if _p64 < 0:
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

# P77A installer is appended after the historical P76 installer.
# Bound the P76 installer slice so P77's own P67 wrapper call is not
# counted as part of P76.
_p77_inst0 = _p76_cpp.find(
    "void InstallP77AAcceptanceProbe()",
    _inst0
)

if _p77_inst0 >= 0:
    _inst = _p76_cpp[_inst0:_p77_inst0]
else:
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

print("P76A_SOURCE_HISTORY_VERIFY=PASS")

# =====================================================================
# P77A — low-volume native UJ acceptance probe verification
# =====================================================================

_p77_cpp = CPP.read_text(encoding="utf-8")
_p77_hpp = HPP.read_text(encoding="utf-8")
_p77_main = MAINCPP.read_text(encoding="utf-8")

def _p77_need(label, haystack, needle):
    if needle not in haystack:
        raise SystemExit(
            "P77A_VERIFY_FAIL: "
            + label
            + " missing: "
            + needle
        )


# ---------------------------------------------------------------
# Active architecture
# ---------------------------------------------------------------

_p77_need(
    "header",
    _p77_hpp,
    "void InstallP77AAcceptanceProbe();"
)

if _p77_main.count(
    "nsc::InstallP78ASemanticAltRouteProbe();"
) != 1:
    raise SystemExit(
        "P77A_VERIFY_FAIL: main must install P77A exactly once"
    )

if (
    "nsc::InstallP76AForkRuntimeProbe();"
    in _p77_main
):
    raise SystemExit(
        "P77A_VERIFY_FAIL: P76A must not be active from main"
    )

if (
    "nsc::InstallP67AActiveSelector1ConsumerBridge();"
    in _p77_main
):
    raise SystemExit(
        "P77A_VERIFY_FAIL: main must not independently install P67A"
    )


# ---------------------------------------------------------------
# Exact P77 target / caller
# ---------------------------------------------------------------

for needle in (
    "kP77UjAcceptanceOffset",
    "0x8B2B70",
    "kP77UjCallerReturnOffset",
    "0x7F4648",
    "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)",
    "[NSC:P77A] UJ_ACCEPT",
    "[NSC:P77A] UJ_OTHER_POSITIVE",
    "[NSC:P77A] READY",
):
    _p77_need(
        "probe",
        _p77_cpp,
        needle
    )


# ---------------------------------------------------------------
# Proven function-entry fingerprint
# ---------------------------------------------------------------

for word in (
    "0xF81E0FFE",
    "0xA9014FF4",
    "0x9108A014",
    "0xAA0003F3",
    "0xAA1403E0",
    "0x52800101",
    "0x97FC4DBE",
    "0x340000A0",
):
    _p77_need(
        "fingerprint",
        _p77_cpp,
        word
    )


# ---------------------------------------------------------------
# Bound exact P77 hook body
# ---------------------------------------------------------------

h0 = _p77_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)"
)

h1 = _p77_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P64SemanticUjConsumerHook)",
    h0
)

if h0 < 0 or h1 < 0 or h1 <= h0:
    raise SystemExit(
        "P77A_VERIFY_FAIL: cannot bound P77 hook body"
    )

body = _p77_cpp[h0:h1]

if body.count("Orig(actor)") != 1:
    raise SystemExit(
        "P77A_VERIFY_FAIL: Orig(actor) count != 1"
    )

if body.count("return ret;") != 1:
    raise SystemExit(
        "P77A_VERIFY_FAIL: native return is not preserved"
    )

if "return 1;" in body:
    raise SystemExit(
        "P77A_VERIFY_FAIL: forced return 1 detected"
    )

if "return 0;" in body:
    raise SystemExit(
        "P77A_VERIFY_FAIL: forced return 0 detected"
    )

for needle in (
    "semantic_pre",
    "semantic_post",
    "pre_e94",
    "post_e94",
    "pre_e9c",
    "post_e9c",
    "ret != 0",
):
    _p77_need(
        "callback",
        body,
        needle
    )


# ---------------------------------------------------------------
# Installer invariants
# ---------------------------------------------------------------

i0 = _p77_cpp.find(
    "void InstallP77AAcceptanceProbe()"
)

if i0 < 0:
    raise SystemExit(
        "P77A_VERIFY_FAIL: installer missing"
    )

_p78_inst0 = _p77_cpp.find(
    "void InstallP78ASemanticAltRouteProbe()",
    i0
)

if _p78_inst0 >= 0:
    installer = _p77_cpp[i0:_p78_inst0]
else:
    installer = _p77_cpp[i0:]

if installer.count(
    "InstallP67AActiveSelector1ConsumerBridge();"
) != 1:
    raise SystemExit(
        "P77A_VERIFY_FAIL: P77A must wrap P67A exactly once"
    )

if (
    "InstallP76AForkRuntimeProbe();"
    in installer
):
    raise SystemExit(
        "P77A_VERIFY_FAIL: P77A must not install P76A"
    )

if (
    "P76AltCorridorHook::InstallAtOffset"
    in installer
):
    raise SystemExit(
        "P77A_VERIFY_FAIL: P76 ALT hook active in P77 installer"
    )

if (
    "P76UjCorridorHook::InstallAtOffset"
    in installer
):
    raise SystemExit(
        "P77A_VERIFY_FAIL: P76 UJ hook active in P77 installer"
    )

for needle in (
    "P77UjAcceptanceHook::InstallAtOffset",
    '"P77_UJ_ACCEPT"',
    "semantic_focus=1",
    "positive_ret_always_log=1",
    "global_hot_cap=0",
    "alt_probe_installed=0",
    "readonly=1",
    "preserve_orig=1",
    "no_force87=1",
    "no_force700=1",
    "no_selector8=1",
    "no_f58_override=1",
    "no_char281_branch=1",
):
    _p77_need(
        "installer",
        installer,
        needle
    )

print("P77A_EXTENSION_VERIFY=PASS")

print("P77A_SOURCE_HISTORY_VERIFY=PASS")

# =====================================================================
# P78A semantic ALT-route probe verification
# =====================================================================

_p78_cpp = CPP.read_text(encoding="utf-8")
_p78_hpp = HPP.read_text(encoding="utf-8")
_p78_main = MAINCPP.read_text(encoding="utf-8")

def _p78_need(label, haystack, needle):
    if needle not in haystack:
        raise SystemExit(
            "P78A_VERIFY_FAIL: "
            + label
            + " missing: "
            + needle
        )


# ---------------------------------------------------------------
# Active architecture
# ---------------------------------------------------------------

_p78_need(
    "header",
    _p78_hpp,
    "void InstallP78ASemanticAltRouteProbe();"
)

if _p78_main.count(
    "nsc::InstallP78ASemanticAltRouteProbe();"
) != 1:
    raise SystemExit(
        "P78A_VERIFY_FAIL: main must install P78 exactly once"
    )

for forbidden in (
    "nsc::InstallP77AAcceptanceProbe();",
    "nsc::InstallP76AForkRuntimeProbe();",
    "nsc::InstallP67AActiveSelector1ConsumerBridge();",
):
    if forbidden in _p78_main:
        raise SystemExit(
            "P78A_VERIFY_FAIL: main contains direct lower-layer install: "
            + forbidden
        )


# ---------------------------------------------------------------
# Target / active caller
# ---------------------------------------------------------------

for needle in (
    "kP78AltRouteOffset",
    "0x8B2D04",
    "kP78AltCallerReturnOffset",
    "0x7F4598",
    "HOOK_DEFINE_TRAMPOLINE(P78AltRouteHook)",
    "[NSC:P78A] ALT_SEM",
    "[NSC:P78A] READY",
):
    _p78_need(
        "probe",
        _p78_cpp,
        needle
    )


# ---------------------------------------------------------------
# Exact ALT fingerprint
# ---------------------------------------------------------------

for word in (
    "0xF81D0FFE",
    "0xA90157F6",
    "0xA9024FF4",
    "0x5282E208",
    "0x72A00028",
    "0xAA0003F3",
    "0xB8686814",
    "0x97FBE29D",
):
    _p78_need(
        "fingerprint",
        _p78_cpp,
        word
    )


# ---------------------------------------------------------------
# Bound exact P78 callback body
# ---------------------------------------------------------------

h0 = _p78_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P78AltRouteHook)"
)

h1 = _p78_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)",
    h0
)

if h0 < 0 or h1 < 0 or h1 <= h0:
    raise SystemExit(
        "P78A_VERIFY_FAIL: cannot bound P78 callback"
    )

body = _p78_cpp[h0:h1]

if body.count("Orig(actor)") != 1:
    raise SystemExit(
        "P78A_VERIFY_FAIL: Orig(actor) count != 1"
    )

if body.count("return ret;") != 1:
    raise SystemExit(
        "P78A_VERIFY_FAIL: native return not preserved"
    )

if "return 1;" in body or "return 0;" in body:
    raise SystemExit(
        "P78A_VERIFY_FAIL: forced return detected"
    )

for needle in (
    "semantic_pre",
    "semantic_post",
    "caller_off == kP78AltCallerReturnOffset",
    "semantic_pre || semantic_post",
    "pre_e94",
    "post_e94",
    "pre_e9c",
    "post_e9c",
):
    _p78_need(
        "callback",
        body,
        needle
    )


# ---------------------------------------------------------------
# Installer
# ---------------------------------------------------------------

i0 = _p78_cpp.find(
    "void InstallP78ASemanticAltRouteProbe()"
)

if i0 < 0:
    raise SystemExit(
        "P78A_VERIFY_FAIL: installer missing"
    )

installer78 = _p78_cpp[i0:]

if installer78.count(
    "InstallP77AAcceptanceProbe();"
) != 1:
    raise SystemExit(
        "P78A_VERIFY_FAIL: P78 must wrap P77 exactly once"
    )

for forbidden in (
    "InstallP67AActiveSelector1ConsumerBridge();",
    "InstallP76AForkRuntimeProbe();",
):
    if forbidden in installer78:
        raise SystemExit(
            "P78A_VERIFY_FAIL: P78 installer bypasses layer: "
            + forbidden
        )

for needle in (
    "P78AltRouteHook::InstallAtOffset",
    '"P78_ALT_ROUTE"',
    "baseline_p77=1",
    "semantic_only=1",
    "global_hot_cap=0",
    "readonly=1",
    "preserve_orig=1",
    "p77_uj_probe=1",
    "no_force87=1",
    "no_force700=1",
    "no_selector8=1",
    "no_f58_override=1",
    "no_char281_branch=1",
):
    _p78_need(
        "installer",
        installer78,
        needle
    )

print("P78A_EXTENSION_VERIFY=PASS")

print("P78A_STATIC_VERIFY=PASS")
