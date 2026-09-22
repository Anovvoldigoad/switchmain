#!/usr/bin/env python3

from pathlib import Path
import hashlib
import re
import struct

ROOT = Path(__file__).resolve().parent

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN_CPP = ROOT / "overlay/source/program/main.cpp"

DEPLOY_MAIN = (
    ROOT
    / "deploy/atmosphere/contents/0100FA10190A0000/exefs/main"
)

PREPARE = ROOT / "prepare_exlaunch_p67a.sh"

required = [
    CPP,
    HPP,
    MAIN_CPP,
    DEPLOY_MAIN,
    PREPARE,
]

for p in required:
    if not p.is_file():
        raise SystemExit("FATAL missing: " + str(p))

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main_cpp = MAIN_CPP.read_text(encoding="utf-8")

b = DEPLOY_MAIN.read_bytes()

EXPECTED_MAIN_SHA = (
    "1adc4dfe948d616cbb7c6d9b3672842a"
    "ba8e7d86bf0763e668505dff84234de0"
)

sha = hashlib.sha256(b).hexdigest()

if sha != EXPECTED_MAIN_SHA:
    raise SystemExit(
        "FATAL deploy main SHA mismatch\n"
        f"got={sha}\n"
        f"expected={EXPECTED_MAIN_SHA}"
    )

print("DEPLOY_MAIN_SHA256=" + sha)

if b[:4] != b"NSO0":
    raise SystemExit("FATAL: deploy main is not NSO0")

flags = struct.unpack_from("<I", b, 0x0C)[0]
text_file_off = struct.unpack_from("<I", b, 0x10)[0]
text_mem_off  = struct.unpack_from("<I", b, 0x14)[0]
text_size     = struct.unpack_from("<I", b, 0x18)[0]

if flags & 1:
    raise SystemExit(
        "FATAL: compressed NSO text unsupported"
    )

def rva_to_file(rva):
    rel = rva - text_mem_off

    if rel < 0 or rel >= text_size:
        raise RuntimeError(
            f"RVA outside text: 0x{rva:X}"
        )

    return text_file_off + rel

def word(rva):
    off = rva_to_file(rva)

    if off + 4 > len(b):
        raise RuntimeError("read outside NSO")

    return struct.unpack_from("<I", b, off)[0]

def words(rva, count):
    return [
        word(rva + i * 4)
        for i in range(count)
    ]

def require_once(text, needle, label):
    count = text.count(needle)

    if count != 1:
        raise SystemExit(
            f"FATAL {label}: count={count}"
        )

def function_body(text, signature):
    start = text.find(signature)

    if start < 0:
        raise SystemExit(
            "FATAL function missing: " + signature
        )

    brace = text.find("{", start)

    if brace < 0:
        raise SystemExit(
            "FATAL function brace missing"
        )

    depth = 0

    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1

            if depth == 0:
                return text[start:i + 1]

    raise SystemExit(
        "FATAL unterminated function: " + signature
    )


# ============================================================
# ACTIVE MAIN
# ============================================================

require_once(
    main_cpp,
    "nsc::InstallP79ADualSubpredicateProbe();",
    "P79 active main"
)

if "nsc::InstallP78ASemanticAltRouteProbe();" in main_cpp:
    raise SystemExit(
        "FATAL: P78 directly active from main"
    )

print("P79_MAIN_CHAIN_VERIFY=PASS")


# ============================================================
# HEADER
# ============================================================

require_once(
    hpp,
    "void InstallP79ADualSubpredicateProbe();",
    "P79 header declaration"
)


# ============================================================
# CONSTANTS
# ============================================================

constant_checks = {
    "kP79PredicateAOffset": "0x7EAC70",
    "kP79PredicateACallerReturnOffset": "0x7EAC40",
    "kP79PredicateBOffset": "0x7EACF0",
    "kP79PredicateBCallerReturnOffset": "0x7EAC60",
}

for name, value in constant_checks.items():
    pat = re.compile(
        rf'constexpr\s+ptrdiff_t\s+{name}\s*=\s*'
        rf'{re.escape(value)}\s*;'
    )

    if not pat.search(cpp):
        raise SystemExit(
            f"FATAL constant mismatch: {name}"
        )

print("P79_CONSTANT_VERIFY=PASS")


# ============================================================
# HOOK SOURCE
# ============================================================

a_tag = "HOOK_DEFINE_TRAMPOLINE(P79PredicateAHook)"
b_tag = "HOOK_DEFINE_TRAMPOLINE(P79PredicateBHook)"
p78_tag = "HOOK_DEFINE_TRAMPOLINE(P78AltRouteHook)"

a_start = cpp.find(a_tag)
b_start = cpp.find(b_tag)
p78_start = cpp.find(p78_tag)

if min(a_start, b_start, p78_start) < 0:
    raise SystemExit(
        "FATAL: P79/P78 hook boundary missing"
    )

if not (a_start < b_start < p78_start):
    raise SystemExit(
        "FATAL: unexpected P79 hook ordering"
    )

a = cpp[a_start:b_start]
bb = cpp[b_start:p78_start]

for label, section, caller_const, marker in (
    (
        "A",
        a,
        "kP79PredicateACallerReturnOffset",
        "[NSC:P79A] PRED_A",
    ),
    (
        "B",
        bb,
        "kP79PredicateBCallerReturnOffset",
        "[NSC:P79A] PRED_B",
    ),
):
    required_strings = [
        caller_const,
        "P64QuerySemanticUltimateJutsu(actor)",
        "const uint32_t ret",
        "Orig(actor)",
        "return ret;",
        marker,
    ]

    for needle in required_strings:
        if needle not in section:
            raise SystemExit(
                f"FATAL P79 {label}: missing {needle}"
            )

    if "281" in section:
        raise SystemExit(
            f"FATAL P79 {label}: char281-specific logic found"
        )

print("P79_CALLBACK_VERIFY=PASS")


# ============================================================
# INSTALL CHAIN
# ============================================================

installer = function_body(
    cpp,
    "void InstallP79ADualSubpredicateProbe()"
)

if installer.count(
    "InstallP77AAcceptanceProbe();"
) != 1:
    raise SystemExit(
        "FATAL: P79 must install P77 exactly once"
    )

if "InstallP78ASemanticAltRouteProbe();" in installer:
    raise SystemExit(
        "FATAL: P79 must not install P78 ALT probe"
    )

for needle in (
    "P79PredicateAHook::InstallAtOffset",
    "P79PredicateBHook::InstallAtOffset",
    "[NSC:P79A] READY",
    "preserve_orig=1",
    "no_force_return=1",
    "no_char281_branch=1",
):
    if needle not in installer:
        raise SystemExit(
            "FATAL P79 installer missing: " + needle
        )

p77 = function_body(
    cpp,
    "void InstallP77AAcceptanceProbe()"
)

if (
    "InstallP67AActiveSelector1ConsumerBridge();"
    not in p77
):
    raise SystemExit(
        "FATAL: P77->P67 chain missing"
    )

print("P79_BASELINE_VERIFY=PASS")


# ============================================================
# STATIC MAIN PREREQUISITE
# ============================================================

if word(0x7F2A9C) != 0xD503201F:
    raise SystemExit(
        "FATAL: main+0x7F2A9C is not NOP"
    )

print("P79_MAIN_PREREQ_VERIFY=PASS")


# ============================================================
# EXACT STATIC FINGERPRINTS
# ============================================================

expected_parent = [
    0xA9BF4FFE,
    0xAA0003F3,
    0x9400000D,
    0x34000080,
    0x52800020,
    0xA8C14FFE,
    0xD65F03C0,
    0xF9400268,
]

expected_a = [
    0xA9BF4FFE,
    0xB94E9408,
    0x7101F11F,
    0x54000081,
    0x52800020,
    0xA8C14FFE,
    0xD65F03C0,
    0xAA0003F3,
]

expected_b = [
    0xF81F0FFE,
    0x5281F008,
    0x72A00028,
    0x52800021,
    0xF8686800,
    0x97FE31A1,
    0xF100001F,
    0x1A9F07E0,
]

for label, rva, expected in (
    ("PARENT", 0x7EAC34, expected_parent),
    ("PRED_A", 0x7EAC70, expected_a),
    ("PRED_B", 0x7EACF0, expected_b),
):
    got = words(rva, len(expected))

    if got != expected:
        raise SystemExit(
            f"FATAL {label} fingerprint mismatch"
        )

# exact A BL
if word(0x7EAC3C) != 0x9400000D:
    raise SystemExit(
        "FATAL A direct call mismatch"
    )

# exact B +0x1298 virtual dispatch
if word(0x7EAC58) != 0xF9494D08:
    raise SystemExit(
        "FATAL B vtable load mismatch"
    )

if word(0x7EAC5C) != 0xD63F0100:
    raise SystemExit(
        "FATAL B BLR mismatch"
    )

print(
    "P79_NSO_LAYOUT_VERIFY=PASS "
    f"text_file_off=0x{text_file_off:x} "
    f"text_mem_off=0x{text_mem_off:x}"
)

print("P79_STATIC_VERIFY=PASS")
print("P79_SOURCE_VERIFY=PASS")
