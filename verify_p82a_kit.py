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
        raise SystemExit("FATAL missing: " + str(p))

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
            "FATAL missing function: " + signature
        )

    brace = text.find("{", start)

    if brace < 0:
        raise SystemExit(
            "FATAL missing brace: " + signature
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
        "FATAL unterminated: " + signature
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

flags = struct.unpack_from("<I", b, 0x0C)[0]
fo = struct.unpack_from("<I", b, 0x10)[0]
mo = struct.unpack_from("<I", b, 0x14)[0]
ts = struct.unpack_from("<I", b, 0x18)[0]

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
# ACTIVE CHAIN
# ============================================================

if main.count(
    "nsc::InstallP82ADownstreamCorridorProbe();"
) != 1:
    raise SystemExit(
        "FATAL P82 active main count"
    )

if (
    "nsc::InstallP81AOugiAwakeningPolicyBridge();"
    in main
):
    raise SystemExit(
        "FATAL P81 directly active in main"
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

print("P82_MAIN_CHAIN_VERIFY=PASS")
print("P82_BASELINE_VERIFY=PASS")


# ============================================================
# GENERATED OUGI DATA STILL PRESENT
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
            "FATAL P81 data missing: " + token
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
        "FATAL current audited fixture mismatch"
    )

print(
    "P82_P81_OUGI_DATA_VERIFY=PASS ids="
    + ",".join(map(str, ids))
)


# ============================================================
# PREPARE PIPELINE
# ============================================================

matches = re.findall(
    r'(?m)^\s*cp\s+.*'
    r'p81_ougi_awake_ids\.hpp'
    r'.*$',
    prep,
)

if len(matches) != 1:
    raise SystemExit(
        "FATAL generated-header copy command count="
        + str(len(matches))
    )

print("P82_PREPARE_VERIFY=PASS")


# ============================================================
# SOURCE HOOK CONTRACT
# ============================================================

required_hooks = (
    "P82StatePredicateHook",
    "P82MidPredicateHook",
    "P82MaskPredicateHook",
    "P82PostGateHook",
    "P82ControlGetterHook",
    "[NSC:P82A] H794EC8",
    "[NSC:P82A] H64A030",
    "[NSC:P82A] H7C5FFC",
    "[NSC:P82A] H7D2DE4",
    "[NSC:P82A] CTRL_GET",
    "[NSC:P82A] READY",
)

for token in required_hooks:
    if token not in cpp:
        raise SystemExit(
            "FATAL P82 source token missing: "
            + token
        )

section_start = cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P82StatePredicateHook)"
)

section_end = cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P80BContextHook)",
    section_start,
)

if section_start < 0 or section_end < 0:
    raise SystemExit(
        "FATAL P82 hook section bounds"
    )

sec = cpp[section_start:section_end]

if re.search(
    r'char_id\s*[!=]=\s*281',
    sec,
):
    raise SystemExit(
        "FATAL char281 gameplay branch"
    )

for forbidden in (
    "return 700",
    "return 0u;",
    "return 1u;",
    "= 0x87",
):
    if forbidden in sec:
        raise SystemExit(
            "FATAL forced behavior token: "
            + forbidden
        )

print("P82_CALLBACK_VERIFY=PASS")


# ============================================================
# CONSTANTS
# ============================================================

constants = {
    "kP82StatePredicateOffset": "0x794EC8",
    "kP82StatePredicateReturnOffset": "0x7F4660",
    "kP82MidPredicateOffset": "0x64A030",
    "kP82MidPredicateReturnOffset": "0x7F4680",
    "kP82MaskPredicateOffset": "0x7C5FFC",
    "kP82MaskPredicateReturnOffset": "0x7F4698",
    "kP82PostGateOffset": "0x7D2DE4",
    "kP82PostGateReturn0Offset": "0x7F46C8",
    "kP82PostGateReturn1Offset": "0x7F4780",
    "kP82ControlGetterOffset": "0x7C6280",
    "kP82ControlReturn8AOffset": "0x7F4790",
    "kP82ControlReturn40Offset": "0x7F47E4",
    "kP82ControlReturn8BOffset": "0x7F4814",
}

for name, value in constants.items():
    pat = re.compile(
        rf'constexpr\s+ptrdiff_t\s+'
        rf'{name}\s*=\s*'
        rf'{re.escape(value)}\s*;'
    )

    if not pat.search(cpp):
        raise SystemExit(
            "FATAL constant mismatch: " + name
        )

print("P82_CONSTANT_VERIFY=PASS")


# ============================================================
# FUNCTION FINGERPRINTS
# ============================================================

verify_words(
    "P82_794EC8_STATIC_VERIFY",
    0x794EC8,
    [
        0xA9BF4FFE,
        0xF9400008,
        0xF9402508,
        0xB94E5413,
        0xD63F0100,
        0x9403AC7D,
        0xB4000160,
        0xF9400008,
    ],
)

verify_words(
    "P82_64A030_STATIC_VERIFY",
    0x64A030,
    [
        0xA9BC67FE,
        0xA9015FF8,
        0xA90257F6,
        0xA9034FF4,
        0xB000D7D7,
        0xF94262F7,
        0xF9400008,
        0xAA0003F3,
    ],
)

verify_words(
    "P82_7C5FFC_STATIC_VERIFY",
    0x7C5FFC,
    [
        0xB9459C08,
        0xB9440409,
        0x6A08013F,
        0x1A9F07E0,
        0xD65F03C0,
    ],
)

verify_words(
    "P82_7D2DE4_STATIC_VERIFY",
    0x7D2DE4,
    [
        0xF81E0FFE,
        0xA9014FF4,
        0xF9400008,
        0x2A0103F4,
        0xAA0003F3,
        0xF946E508,
        0xD63F0100,
        0x34000320,
    ],
)

verify_words(
    "P82_7C6280_STATIC_VERIFY",
    0x7C6280,
    [
        0xF81E0FFE,
        0xA9014FF4,
        0x2A0103F3,
        0xAA0003F4,
        0x71004C3F,
        0x54000161,
        0xB000CBE8,
        0xF9424508,
    ],
)


# ============================================================
# CORRIDOR CALLSITES
# ============================================================

callsites = {
    0x7F4658: 0xAA1303E0,
    0x7F465C: 0x97FE821B,
    0x7F4660: 0x34000200,

    0x7F4674: 0xAA1303E0,
    0x7F467C: 0x97F9566D,
    0x7F4680: 0x7100001F,

    0x7F4690: 0xAA1403E0,
    0x7F4694: 0x97FF465A,
    0x7F4698: 0x35001D00,

    0x7F46BC: 0xAA1303E0,
    0x7F46C0: 0x2A1F03E1,
    0x7F46C4: 0x97FF79C8,
    0x7F46C8: 0x350005E0,

    0x7F4778: 0x2A1F03E1,
    0x7F477C: 0x97FF799A,
    0x7F4780: 0x340001A0,

    0x7F4784: 0xAA1403E0,
    0x7F4788: 0x52800101,
    0x7F478C: 0x97FF46BD,
    0x7F4790: 0x35000120,

    0x7F47D8: 0x52800501,
    0x7F47DC: 0xAA1403E0,
    0x7F47E0: 0x97FF46A8,
    0x7F47E4: 0x7100001F,

    0x7F4808: 0xAA1403E0,
    0x7F480C: 0x52800101,
    0x7F4810: 0x97FF469C,
    0x7F4814: 0x340000C0,
}

for rva, expected in callsites.items():
    got = word(rva)

    if got != expected:
        raise SystemExit(
            f"FATAL callsite 0x{rva:X}: "
            f"got=0x{got:08X} "
            f"expected=0x{expected:08X}"
        )

print("P82_CORRIDOR_CALLSITE_VERIFY=PASS")


# ============================================================
# EXISTING MAIN PREREQUISITE
# ============================================================

if word(0x7F2A9C) != 0xD503201F:
    raise SystemExit(
        "FATAL source-parity NOP missing"
    )

print("P82_MAIN_PREREQ_VERIFY=PASS")

if (
    "void InstallP82ADownstreamCorridorProbe();"
    not in hpp
):
    raise SystemExit(
        "FATAL P82 declaration missing"
    )

print("P82_HEADER_VERIFY=PASS")

print(
    "P82_NSO_LAYOUT_VERIFY=PASS "
    f"text_file_off=0x{fo:x} "
    f"text_mem_off=0x{mo:x}"
)

print("P82_STATIC_VERIFY=PASS")
print("P82_SOURCE_VERIFY=PASS")
