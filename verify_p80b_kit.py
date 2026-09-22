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

for p in (
    CPP,
    HPP,
    MAIN_CPP,
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

b = DEPLOY_MAIN.read_bytes()


# ============================================================
# MAIN IDENTITY
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
    raise SystemExit("FATAL: main not NSO0")

flags = struct.unpack_from("<I", b, 0x0C)[0]

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
        "FATAL: compressed text unsupported"
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
            f"read outside file at 0x{rva:X}"
        )

    return struct.unpack_from(
        "<I", b, off
    )[0]


def words(rva, n):
    return [
        word(rva + i * 4)
        for i in range(n)
    ]


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
        "FATAL unterminated function"
    )


def sign_extend(v, bits):
    sign = 1 << (bits - 1)
    return (v ^ sign) - sign


def bl_target(pc, insn):
    if (
        insn & 0xFC000000
    ) != 0x94000000:
        raise RuntimeError(
            f"not BL at 0x{pc:X}: "
            f"0x{insn:08X}"
        )

    imm = sign_extend(
        insn & 0x03FFFFFF,
        26
    )

    return pc + (imm << 2)


# ============================================================
# ACTIVE MAIN
# ============================================================

require_once(
    main_cpp,
    "nsc::InstallP80BDeepConditionTrace();",
    "P80B active main"
)

for forbidden in (
    "nsc::InstallP79ADualSubpredicateProbe();",
    "nsc::InstallP80AExactConditionMatchProbe();",
):
    if forbidden in main_cpp:
        raise SystemExit(
            "FATAL stale active call: "
            + forbidden
        )

print("P80B_MAIN_CHAIN_VERIFY=PASS")


# ============================================================
# HEADER
# ============================================================

require_once(
    hpp,
    "void InstallP80BDeepConditionTrace();",
    "P80B header"
)


# ============================================================
# CONSTANTS
# ============================================================

expected_constants = {
    "kP80BPredicateBOffset":
        "0x7EACF0",

    "kP80BPredicateBReturnOffset":
        "0x7EAC60",

    "kP80BConditionQueryOffset":
        "0x777388",

    "kP80BConditionQueryReturnOffset":
        "0x7EAD08",

    "kP80BConditionGetterOffset":
        "0x754A80",

    "kP80BActorCollectionOffset":
        "0x10F80",
}

for name, value in expected_constants.items():
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

print("P80B_CONSTANT_VERIFY=PASS")


# ============================================================
# HOOK SOURCE
# ============================================================

ctx_tag = (
    "HOOK_DEFINE_TRAMPOLINE("
    "P80BContextHook)"
)

query_tag = (
    "HOOK_DEFINE_TRAMPOLINE("
    "P80BConditionQueryHook)"
)

p79_tag = (
    "HOOK_DEFINE_TRAMPOLINE("
    "P79PredicateAHook)"
)

ctx_start = cpp.find(ctx_tag)
query_start = cpp.find(query_tag)
p79_start = cpp.find(p79_tag)

if min(
    ctx_start,
    query_start,
    p79_start,
) < 0:
    raise SystemExit(
        "FATAL hook boundary missing"
    )

if not (
    ctx_start
    < query_start
    < p79_start
):
    raise SystemExit(
        "FATAL unexpected hook ordering"
    )

ctx = cpp[
    ctx_start:query_start
]

query = cpp[
    query_start:p79_start
]

for token in (
    "P64QuerySemanticUltimateJutsu(actor)",
    "Orig(actor)",
    "return ret;",
):
    if token not in ctx:
        raise SystemExit(
            "FATAL context hook missing: "
            + token
        )

for token in (
    "Orig(",
    "[NSC:P80B] QUERY",
    "[NSC:P80B] DUMP_BEGIN",
    "[NSC:P80B] CAND",
    "[NSC:P80B] DUMP_END",
    "matched_index",
    "field_c",
    "type_match",
    "native_return",
    "return result;",
):
    if token not in query:
        raise SystemExit(
            "FATAL query hook missing: "
            + token
        )

if re.search(
    r'char_id\s*[!=]=\s*281',
    ctx + query
):
    raise SystemExit(
        "FATAL char281-specific branch"
    )

print("P80B_CALLBACK_VERIFY=PASS")


# ============================================================
# INSTALL CHAIN
# ============================================================

installer = function_body(
    cpp,
    "void InstallP80BDeepConditionTrace()"
)

if installer.count(
    "InstallP77AAcceptanceProbe();"
) != 1:
    raise SystemExit(
        "FATAL P77 baseline count"
    )

for forbidden in (
    "InstallP79ADualSubpredicateProbe();",
    "InstallP78ASemanticAltRouteProbe();",
):
    if forbidden in installer:
        raise SystemExit(
            "FATAL noisy installer: "
            + forbidden
        )

for token in (
    "P80BContextHook::InstallAtOffset",
    "P80BConditionQueryHook::InstallAtOffset",
    "[NSC:P80B] READY",
    "readonly=1",
    "preserve_orig=1",
    "no_force_return=1",
    "no_char281_branch=1",
):
    if token not in installer:
        raise SystemExit(
            "FATAL installer missing: "
            + token
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
        "FATAL P77->P67 chain missing"
    )

print("P80B_BASELINE_VERIFY=PASS")


# ============================================================
# STATIC B
# ============================================================

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

if words(
    0x7EACF0,
    len(expected_b)
) != expected_b:
    raise SystemExit(
        "FATAL Predicate-B fingerprint"
    )

if bl_target(
    0x7EAD04,
    word(0x7EAD04)
) != 0x777388:
    raise SystemExit(
        "FATAL B->query BL mismatch"
    )

print("P80B_B_STATIC_VERIFY=PASS")


# ============================================================
# STATIC QUERY LOOP
# ============================================================

expected_query = [
    0xF81D0FFE,
    0xA90157F6,
    0xA9024FF4,
    0xF9400C08,
    0x91008109,
    0xF9401516,
    0xEB0902DF,
    0x54000240,
]

if words(
    0x777388,
    len(expected_query)
) != expected_query:
    raise SystemExit(
        "FATAL query fingerprint"
    )

static_words = {
    0x7773C8: 0xF9400AD5,
    0x7773D0: 0xB9400AA0,
    0x7773D4: 0x97FF75AB,
    0x7773D8: 0xB4FFFEE0,
    0x7773DC: 0xB9400C08,
    0x7773E0: 0x6B13011F,
}

for rva, expected in static_words.items():
    got = word(rva)

    if got != expected:
        raise SystemExit(
            f"FATAL static word "
            f"0x{rva:X}: "
            f"got=0x{got:08X} "
            f"expected=0x{expected:08X}"
        )

if bl_target(
    0x7773D4,
    word(0x7773D4)
) != 0x754A80:
    raise SystemExit(
        "FATAL query->getter BL mismatch"
    )

print("P80B_QUERY_STATIC_VERIFY=PASS")


# ============================================================
# ACTIVE MAIN PREREQUISITES
# ============================================================

# Do NOT assert the historical P41A getter-entry word here.
#
# 0x754A80 == 0x17FFFFFD belonged to the older P41 main:
#
#   SHA256
#   407ff7247a2c70941c05eb2cdfbd65a2a25fffc247845274b096ed0b5aee6ae7
#
# P80B is pinned to the current paired main:
#
#   1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0
#
# For the current baseline, what P80B requires statically is:
#
#   0x7773D4 -> 0x754A80
#
# which is already verified above.
#
# Runtime P50 independently proves extended indices 512..516 are
# available. Do not mix the historical P41 implementation fingerprint
# with the current P67/P79/P80 main.

getter_entry_word = word(0x754A80)

print(
    "P80B_CONDITION_GETTER_ENTRY="
    f"0x{getter_entry_word:08X}"
)

if word(0x7F2A9C) != 0xD503201F:
    raise SystemExit(
        "FATAL source-parity NOP missing"
    )

print("P80B_MAIN_PREREQ_VERIFY=PASS")


print(
    "P80B_NSO_LAYOUT_VERIFY=PASS "
    f"text_file_off=0x{text_file_off:x} "
    f"text_mem_off=0x{text_mem_off:x}"
)

print("P80B_STATIC_VERIFY=PASS")
print("P80B_SOURCE_VERIFY=PASS")
