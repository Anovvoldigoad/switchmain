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

DEPLOY_MAIN = (
    ROOT
    / "deploy/atmosphere/contents/0100FA10190A0000/exefs/main"
)

PREPARE = ROOT / "prepare_exlaunch_p67a.sh"

for p in (
    CPP,
    HPP,
    MAIN_CPP,
    DATA_HPP,
    DEPLOY_MAIN,
    PREPARE,
):
    if not p.is_file():
        raise SystemExit(
            "FATAL missing: " + str(p)
        )

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main_cpp = MAIN_CPP.read_text(encoding="utf-8")
data_hpp = DATA_HPP.read_text(encoding="utf-8")
prepare = PREPARE.read_text(encoding="utf-8")

b = DEPLOY_MAIN.read_bytes()


# ============================================================
# HELPERS
# ============================================================

def require_once(text, token, label):
    n = text.count(token)

    if n != 1:
        raise SystemExit(
            f"FATAL {label}: count={n}"
        )


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
        "FATAL unterminated function: "
        + signature
    )


# ============================================================
# DEPLOY MAIN IDENTITY / NSO MAPPING
# ============================================================

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
    raise SystemExit(
        "FATAL deploy main not NSO0"
    )

flags = struct.unpack_from(
    "<I", b, 0x0C
)[0]

text_file_off = struct.unpack_from(
    "<I", b, 0x10
)[0]

text_mem_off = struct.unpack_from(
    "<I", b, 0x14
)[0]

text_size = struct.unpack_from(
    "<I", b, 0x18
)[0]

if flags & 1:
    raise SystemExit(
        "FATAL compressed text unsupported"
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
        raise RuntimeError(
            f"read outside NSO at 0x{rva:X}"
        )

    return struct.unpack_from(
        "<I", b, off
    )[0]


def words(rva, count):
    return [
        word(rva + i * 4)
        for i in range(count)
    ]


# ============================================================
# ACTIVE MAIN
# ============================================================

require_once(
    main_cpp,
    "nsc::InstallP81AOugiAwakeningPolicyBridge();",
    "P81 active main"
)

for forbidden in (
    "nsc::InstallP80BDeepConditionTrace();",
    "nsc::InstallP79ADualSubpredicateProbe();",
    "nsc::InstallP78ASemanticAltRouteProbe();",
):
    if forbidden in main_cpp:
        raise SystemExit(
            "FATAL stale active main call: "
            + forbidden
        )

print("P81_MAIN_CHAIN_VERIFY=PASS")


# ============================================================
# GENERATED OUGI DATA
# ============================================================

EXPECTED_OUGI_SHA = (
    "4322e4ab30547321abc6cd24322a5ba98"
    "f8e7d0ddafa853039234c397ccfe6cb"
)

for token in (
    "kOugiAwakeningIds",
    "kOugiAwakeningIdCount",
    "ContainsOugiAwakeningId",
    EXPECTED_OUGI_SHA,
):
    if token not in data_hpp:
        raise SystemExit(
            "FATAL generated Ougi data missing: "
            + token
        )

m = re.search(
    r'kOugiAwakeningIds\[\]\s*=\s*\{(.*?)\};',
    data_hpp,
    re.S,
)

if not m:
    raise SystemExit(
        "FATAL cannot parse Ougi membership table"
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
        "FATAL audited P81 fixture membership mismatch: "
        + repr(ids)
    )

print(
    "P81_OUGI_MEMBERSHIP_VERIFY=PASS "
    "ids="
    + ",".join(map(str, ids))
)

print(
    "P81_OUGI_SOURCE_SHA256="
    + EXPECTED_OUGI_SHA
)


# ============================================================
# INCLUDE / HEADER
# ============================================================

require_once(
    cpp,
    '#include "p81_ougi_awake_ids.hpp"',
    "P81 generated header include"
)

require_once(
    hpp,
    "void InstallP81AOugiAwakeningPolicyBridge();",
    "P81 declaration"
)

print("P81_HEADER_VERIFY=PASS")


# ============================================================
# CONSTANTS
# ============================================================

constants = {
    "kP81UjPolicyParentOffset":
        "0x7EAC34",

    "kP81UjPolicyCallerReturnOffset":
        "0x7F458C",
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

print("P81_CONSTANT_VERIFY=PASS")


# ============================================================
# POLICY HOOK CONTRACT
# ============================================================

hook_start = cpp.find(
    "HOOK_DEFINE_TRAMPOLINE("
    "P81OugiAwakeningPolicyHook)"
)

hook_end = cpp.find(
    "HOOK_DEFINE_TRAMPOLINE("
    "P80BContextHook)",
    hook_start,
)

if hook_start < 0 or hook_end < 0:
    raise SystemExit(
        "FATAL P81 hook boundaries missing"
    )

hook = cpp[
    hook_start:hook_end
]

required_hook = (
    "Orig(actor)",
    "kP81UjPolicyCallerReturnOffset",
    "P64QuerySemanticUltimateJutsu",
    "ContainsOugiAwakeningId",
    "native_ret != 0",
    "policy_ret",
    "[NSC:P81A] POLICY",
    "return policy_ret;",
)

for token in required_hook:
    if token not in hook:
        raise SystemExit(
            "FATAL P81 hook missing: "
            + token
        )

if re.search(
    r'char_id\s*[!=]=\s*281',
    hook
):
    raise SystemExit(
        "FATAL char281-specific gameplay branch"
    )

if "return 700" in hook:
    raise SystemExit(
        "FATAL direct action700 return detected"
    )

if "0x87" in hook:
    raise SystemExit(
        "FATAL state87 literal in P81 hook"
    )

print("P81_POLICY_CALLBACK_VERIFY=PASS")


# ============================================================
# INSTALLER / BASELINE
# ============================================================

installer = function_body(
    cpp,
    "void InstallP81AOugiAwakeningPolicyBridge()"
)

if installer.count(
    "InstallP77AAcceptanceProbe();"
) != 1:
    raise SystemExit(
        "FATAL P77 baseline count"
    )

for token in (
    "P81OugiAwakeningPolicyHook::",
    "kP81UjPolicyParentOffset",
    "[NSC:P81A] READY",
    "no_condition_mutation=1",
    "no_force87=1",
    "no_force700=1",
    "no_char281_branch=1",
):
    if token not in installer:
        raise SystemExit(
            "FATAL installer missing: "
            + token
        )

for forbidden in (
    "P80BConditionQueryHook::InstallAtOffset",
    "InstallP79ADualSubpredicateProbe();",
    "InstallP78ASemanticAltRouteProbe();",
):
    if forbidden in installer:
        raise SystemExit(
            "FATAL noisy/old installer dependency: "
            + forbidden
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
        "FATAL P77 -> P67 baseline missing"
    )

print("P81_BASELINE_VERIFY=PASS")


# ============================================================
# HISTORICAL P80 SOURCE RETAINED
# ============================================================

for token in (
    "void InstallP80BDeepConditionTrace()",
    "HOOK_DEFINE_TRAMPOLINE(P80BContextHook)",
    "HOOK_DEFINE_TRAMPOLINE(P80BConditionQueryHook)",
):
    if token not in cpp:
        raise SystemExit(
            "FATAL historical P80 source missing: "
            + token
        )

print("P81_P80_SOURCE_PRESERVE_VERIFY=PASS")


# ============================================================
# PREPARE SCRIPT
# ============================================================

# Count actual copy COMMANDS, not raw filename occurrences.
#
# A valid command naturally contains the filename twice:
#
#   cp source/p81_ougi_awake_ids.hpp dest/p81_ougi_awake_ids.hpp
#
# so prepare.count(filename) == 2 is expected.

p81_copy_commands = re.findall(
    r'(?m)^\s*cp\s+.*'
    r'p81_ougi_awake_ids\.hpp'
    r'.*$',
    prepare,
)

if len(p81_copy_commands) != 1:
    raise SystemExit(
        "FATAL P81 generated-header copy command count: "
        + str(len(p81_copy_commands))
    )

for token in (
    "main.cpp",
    "nsc_cpk_bridge.cpp",
    "nsc_cpk_bridge.hpp",
    "p81_ougi_awake_ids.hpp",
):
    if token not in prepare:
        raise SystemExit(
            "FATAL prepare copy missing: "
            + token
        )

print(
    "P81_PREPARE_HEADER_COPY="
    + p81_copy_commands[0].strip()
)

print("P81_PREPARE_VERIFY=PASS")


# ============================================================
# STATIC PARENT FUNCTION
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

got_parent = words(
    0x7EAC34,
    len(expected_parent)
)

if got_parent != expected_parent:
    raise SystemExit(
        "FATAL P81 parent fingerprint mismatch"
    )

print("P81_PARENT_STATIC_VERIFY=PASS")


# ============================================================
# EXACT UJ CALLSITE
# ============================================================

if word(0x7F4584) != 0xF9494508:
    raise SystemExit(
        "FATAL +0x1288 load mismatch"
    )

if word(0x7F4588) != 0xD63F0100:
    raise SystemExit(
        "FATAL UJ decision is not BLR X8"
    )

cbz = word(0x7F458C)

if (
    cbz & 0x7F000000
) != 0x34000000:
    raise SystemExit(
        "FATAL 0x7F458C is not CBZ W0"
    )

print("P81_UJ_CALLSITE_STATIC_VERIFY=PASS")


# ============================================================
# MAIN PREREQUISITES
# ============================================================

if word(0x7F2A9C) != 0xD503201F:
    raise SystemExit(
        "FATAL source-parity NOP missing"
    )

print("P81_MAIN_PREREQ_VERIFY=PASS")


print(
    "P81_NSO_LAYOUT_VERIFY=PASS "
    f"text_file_off=0x{text_file_off:x} "
    f"text_mem_off=0x{text_mem_off:x}"
)

print("P81_STATIC_VERIFY=PASS")
print("P81_SOURCE_VERIFY=PASS")
