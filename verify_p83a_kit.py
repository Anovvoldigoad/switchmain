#!/usr/bin/env python3

from pathlib import Path
import hashlib
import re
import struct

ROOT = Path(__file__).resolve().parent

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN_CPP = ROOT / "overlay/source/program/main.cpp"
DATA_HPP = ROOT / "overlay/source/program/p81_ougi_awake_ids.hpp"
PREP = ROOT / "prepare_exlaunch_p67a.sh"

DEPLOY_MAIN = (
    ROOT
    / "deploy/atmosphere/contents/0100FA10190A0000/exefs/main"
)

for p in (
    CPP,
    HPP,
    MAIN_CPP,
    DATA_HPP,
    PREP,
    DEPLOY_MAIN,
):
    if not p.is_file():
        raise SystemExit(
            "FATAL missing: " + str(p)
        )

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main = MAIN_CPP.read_text(encoding="utf-8")
data = DATA_HPP.read_text(encoding="utf-8")
prep = PREP.read_text(encoding="utf-8")

b = DEPLOY_MAIN.read_bytes()


def function_body(text, signature):
    start = text.find(signature)

    if start < 0:
        raise SystemExit(
            "FATAL missing function: "
            + signature
        )

    brace = text.find("{", start)

    if brace < 0:
        raise SystemExit(
            "FATAL missing brace: "
            + signature
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
        "FATAL unterminated: "
        + signature
    )


EXPECTED_MAIN_SHA = (
    "1adc4dfe948d616cbb7c6d9b3672842a"
    "ba8e7d86bf0763e668505dff84234de0"
)

sha = hashlib.sha256(b).hexdigest()

print("DEPLOY_MAIN_SHA256=" + sha)

if sha != EXPECTED_MAIN_SHA:
    raise SystemExit(
        "FATAL paired main SHA mismatch"
    )

if b[:4] != b"NSO0":
    raise SystemExit("FATAL not NSO0")

flags = struct.unpack_from(
    "<I", b, 0x0C
)[0]

fo = struct.unpack_from(
    "<I", b, 0x10
)[0]

mo = struct.unpack_from(
    "<I", b, 0x14
)[0]

ts = struct.unpack_from(
    "<I", b, 0x18
)[0]

if flags & 1:
    raise SystemExit(
        "FATAL compressed text unsupported"
    )


def word(rva):
    rel = rva - mo

    if not 0 <= rel <= ts - 4:
        raise SystemExit(
            f"FATAL RVA outside text 0x{rva:X}"
        )

    return struct.unpack_from(
        "<I",
        b,
        fo + rel,
    )[0]


def verify_words(label, rva, expected):
    got = [
        word(rva + i * 4)
        for i in range(len(expected))
    ]

    if got != expected:
        print("FINGERPRINT_MISMATCH=" + label)

        for i, (g, e) in enumerate(
            zip(got, expected)
        ):
            print(
                f"0x{rva+i*4:X} "
                f"got=0x{g:08X} "
                f"expected=0x{e:08X}"
            )

        raise SystemExit(
            "FATAL fingerprint mismatch: "
            + label
        )

    print(label + "=PASS")


# ============================================================
# ACTIVE INSTALL CHAIN
# ============================================================

if main.count(
    "nsc::InstallP83ASlot1928PolicyBridge();"
) != 1:
    raise SystemExit(
        "FATAL P83 active main count"
    )

if (
    "nsc::InstallP82ADownstreamCorridorProbe();"
    in main
):
    raise SystemExit(
        "FATAL P82 directly active in main"
    )

p83 = function_body(
    cpp,
    "void InstallP83ASlot1928PolicyBridge()"
)

if p83.count(
    "InstallP82ADownstreamCorridorProbe();"
) != 1:
    raise SystemExit(
        "FATAL P83 -> P82 baseline"
    )

p82 = function_body(
    cpp,
    "void InstallP82ADownstreamCorridorProbe()"
)

if p82.count(
    "InstallP81AOugiAwakeningPolicyBridge();"
) != 1:
    raise SystemExit(
        "FATAL P82 -> P81 baseline"
    )

p81 = function_body(
    cpp,
    "void InstallP81AOugiAwakeningPolicyBridge()"
)

if p81.count(
    "InstallP77AAcceptanceProbe();"
) != 1:
    raise SystemExit(
        "FATAL P81 -> P77 baseline"
    )

print("P83_MAIN_CHAIN_VERIFY=PASS")
print("P83_BASELINE_VERIFY=PASS")


# ============================================================
# GENERATED MEMBERSHIP
# ============================================================

EXPECTED_OUGI_SHA = (
    "4322e4ab30547321abc6cd24322a5ba98"
    "f8e7d0ddafa853039234c397ccfe6cb"
)

for token in (
    "kOugiAwakeningIds",
    "ContainsOugiAwakeningId",
    EXPECTED_OUGI_SHA,
):
    if token not in data:
        raise SystemExit(
            "FATAL Ougi data missing: "
            + token
        )

m = re.search(
    r'kOugiAwakeningIds\[\]\s*=\s*\{(.*?)\};',
    data,
    re.S,
)

if not m:
    raise SystemExit(
        "FATAL cannot parse Ougi IDs"
    )

ids = [
    int(x)
    for x in re.findall(
        r'(\d+)u',
        m.group(1)
    )
]

if ids != [281]:
    raise SystemExit(
        "FATAL audited fixture mismatch: "
        + repr(ids)
    )

print(
    "P83_OUGI_DATA_VERIFY=PASS ids="
    + ",".join(map(str, ids))
)


# ============================================================
# PREPARE HEADER PIPELINE
# ============================================================

copies = re.findall(
    r'(?m)^\s*cp\s+.*'
    r'p81_ougi_awake_ids\.hpp'
    r'.*$',
    prep,
)

if len(copies) != 1:
    raise SystemExit(
        "FATAL generated-header copy commands="
        + str(len(copies))
    )

print("P83_PREPARE_VERIFY=PASS")


# ============================================================
# SOURCE POLICY CONTRACT
# ============================================================

hook_start = cpp.find(
    "HOOK_DEFINE_TRAMPOLINE("
    "P83Slot1928PolicyHook)"
)

hook_end = cpp.find(
    "HOOK_DEFINE_TRAMPOLINE("
    "P80BContextHook)",
    hook_start,
)

if hook_start < 0 or hook_end < 0:
    raise SystemExit(
        "FATAL P83 hook bounds"
    )

hook = cpp[hook_start:hook_end]

required = (
    "Orig(actor, mode)",
    "kP83Slot1928CallerReturnOffset",
    "P64QuerySemanticUltimateJutsu",
    "ContainsOugiAwakeningId",
    "native_ret == 0",
    "policy_ret",
    "gate_10f40",
    "[NSC:P83A] SLOT1928_POLICY",
    "return policy_ret;",
)

for token in required:
    if token not in hook:
        raise SystemExit(
            "FATAL P83 hook missing: "
            + token
        )

if re.search(
    r'char_id\s*[!=]=\s*281',
    hook,
):
    raise SystemExit(
        "FATAL char281 gameplay branch"
    )

for forbidden in (
    "return 700",
    "= 0x87",
):
    if forbidden in hook:
        raise SystemExit(
            "FATAL forced behavior: "
            + forbidden
        )

print("P83_POLICY_CALLBACK_VERIFY=PASS")


# ============================================================
# CONSTANTS
# ============================================================

constants = {
    "kP83Slot1928TargetOffset":
        "0x7D34E0",

    "kP83Slot1928CallerReturnOffset":
        "0x7F474C",
}

for name, value in constants.items():
    pat = re.compile(
        rf'constexpr\s+ptrdiff_t\s+'
        rf'{name}\s*=\s*'
        rf'{re.escape(value)}\s*;'
    )

    if not pat.search(cpp):
        raise SystemExit(
            "FATAL constant mismatch: "
            + name
        )

print("P83_CONSTANT_VERIFY=PASS")


# ============================================================
# TARGET FUNCTION
# ============================================================

verify_words(
    "P83_SLOT1928_TARGET_STATIC_VERIFY",
    0x7D34E0,
    [
        0xF81D0FFE,
        0xA90157F6,
        0xA9024FF4,
        0x5281E808,
        0x72A00028,
        0xB8686808,
        0x34000328,
        0x2A0103F4,
    ],
)


# ============================================================
# EXACT UJ CALLSITE
# ============================================================

callsite = {
    0x7F4738: 0xF9400268,
    0x7F473C: 0xAA1303E0,
    0x7F4740: 0x2A1F03E1,
    0x7F4744: 0xF94C9508,
    0x7F4748: 0xD63F0100,
    0x7F474C: 0x34FFF220,
}

for rva, expected in callsite.items():
    got = word(rva)

    if got != expected:
        raise SystemExit(
            f"FATAL callsite 0x{rva:X}: "
            f"got=0x{got:08X} "
            f"expected=0x{expected:08X}"
        )

print(
    "P83_SLOT1928_CALLSITE_STATIC_VERIFY=PASS"
)


# ============================================================
# P81 SOURCE-PARITY PREREQ
# ============================================================

if word(0x7F2A9C) != 0xD503201F:
    raise SystemExit(
        "FATAL source-parity NOP missing"
    )

print("P83_MAIN_PREREQ_VERIFY=PASS")


# ============================================================
# P82 DOWNSTREAM TRACE PRESERVED
# ============================================================

for token in (
    "P82StatePredicateHook",
    "P82MidPredicateHook",
    "P82MaskPredicateHook",
    "P82PostGateHook",
    "P82ControlGetterHook",
    "[NSC:P82A] READY",
):
    if token not in cpp:
        raise SystemExit(
            "FATAL P82 baseline source missing: "
            + token
        )

print("P83_P82_TRACE_PRESERVE_VERIFY=PASS")


# ============================================================
# INSTALLER CONTRACT
# ============================================================

for token in (
    "P83Slot1928PolicyHook::",
    "kP83Slot1928TargetOffset",
    "[NSC:P83A] READY",
    "native_first=1",
    "exact_uj_call_only=1",
    "semantic_required=1",
    "no_force87=1",
    "no_force700=1",
    "no_action445_rewrite=1",
    "no_char281_branch=1",
):
    if token not in p83:
        raise SystemExit(
            "FATAL P83 installer missing: "
            + token
        )

print("P83_INSTALLER_VERIFY=PASS")


if (
    "void InstallP83ASlot1928PolicyBridge();"
    not in hpp
):
    raise SystemExit(
        "FATAL P83 header declaration"
    )

print("P83_HEADER_VERIFY=PASS")

print(
    "P83_NSO_LAYOUT_VERIFY=PASS "
    f"text_file_off=0x{fo:x} "
    f"text_mem_off=0x{mo:x}"
)

print("P83_STATIC_VERIFY=PASS")
print("P83_SOURCE_VERIFY=PASS")
