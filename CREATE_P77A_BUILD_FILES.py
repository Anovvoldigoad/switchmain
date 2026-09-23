#!/usr/bin/env python3

from pathlib import Path

ROOT = Path("/storage/emulated/0/Downloads")

CPP   = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP   = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN  = ROOT / "overlay/source/program/main.cpp"

V76   = ROOT / "verify_p76a_kit.py"
V77   = ROOT / "verify_p77a_kit.py"

WF76  = ROOT / ".github/workflows/build-subsdk9-p76a.yml"
WF77  = ROOT / ".github/workflows/build-subsdk9-p77a.yml"

README = ROOT / "README_P77A.txt"

for p in (CPP, HPP, MAIN, V76, WF76):
    if not p.is_file():
        raise SystemExit(f"FATAL: missing prerequisite: {p}")

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

# ------------------------------------------------------------------
# Source prerequisites first. Fail closed.
# ------------------------------------------------------------------

required_source = [
    "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)",
    "void InstallP77AAcceptanceProbe()",
    "[NSC:P77A] UJ_ACCEPT",
    "[NSC:P77A] READY",
    "kP77UjAcceptanceOffset",
    "kP77UjCallerReturnOffset",
]

for needle in required_source:
    if needle not in cpp:
        raise SystemExit(
            "FATAL: current P77 source missing: " + needle
        )

if main.count("nsc::InstallP77AAcceptanceProbe();") != 1:
    raise SystemExit(
        "FATAL: main.cpp must call P77A exactly once"
    )

if "nsc::InstallP76AForkRuntimeProbe();" in main:
    raise SystemExit(
        "FATAL: P76A still active from main.cpp"
    )

if "void InstallP77AAcceptanceProbe();" not in hpp:
    raise SystemExit(
        "FATAL: P77A header declaration missing"
    )

print("P77_SOURCE_PREREQ=PASS")


# ==================================================================
# 1. VERIFIER P77A
# ==================================================================

s = V76.read_text(encoding="utf-8")

old_call = "nsc::InstallP76AForkRuntimeProbe();"
new_call = "nsc::InstallP77AAcceptanceProbe();"

count = s.count(old_call)

if count < 1:
    raise SystemExit(
        "FATAL: no P76 main expectation found in verifier"
    )

# There can legitimately be more than one verifier reference:
# inherited main expectation + P76 extension main assertion.
s = s.replace(old_call, new_call)

# Make inherited diagnostic text less misleading where possible.
s = s.replace(
    "main must install P76A exactly once",
    "main must install P77A exactly once"
)

marker = 'print("P76A_STATIC_VERIFY=PASS")'

if s.count(marker) != 1:
    raise SystemExit(
        "FATAL: expected exactly one P76 final marker"
    )

extra = r'''
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
    "nsc::InstallP77AAcceptanceProbe();"
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
'''

s = s.replace(
    marker,
    'print("P76A_SOURCE_HISTORY_VERIFY=PASS")\n'
    + extra
    + '\nprint("P77A_STATIC_VERIFY=PASS")',
    1
)

V77.write_text(s, encoding="utf-8")

print(
    "P77_VERIFIER_CREATE=PASS "
    f"replaced_p76_main_refs={count}"
)


# ==================================================================
# 2. README P77A
# ==================================================================

README.write_text(
r'''NSC P77A — LOW-VOLUME UJ ACCEPTANCE PROBE

BASELINE
========

P77A preserves the complete P67A behavioral baseline.

P76A runtime established an important fact:

  main+0x8B2B70 ret=1

immediately preceded native:

  requested=700
  PlayAction700

on a successful vanilla Ultimate Jutsu.

P76A also revealed a diagnostic limitation:
the hot per-frame corridor loggers reached their n<512 limits before
the later Tobi XXA attempt.


P77A TARGET
===========

Only the native UJ acceptance helper is actively probed:

  target:
    main+0x8B2B70

  exact active caller return:
    main+0x7F4648

Static ABI:

  uint32_t(void* actor)


P77A CALLBACK
=============

The trampoline always:

  1. reads diagnostic state;
  2. calls Orig(actor);
  3. reads diagnostic state again;
  4. logs qualifying evidence;
  5. returns the native result unchanged.

Logging occurs at the exact active caller when:

  - semantic selector1 is active; OR
  - native helper return is nonzero; OR
  - E94 changes; OR
  - E9C changes.

There is NO global n<512 hot-loop cap.


PURPOSE
=======

Capture the actual native helper result during the real Tobi XXA
attempt immediately before the engine requests action445.


REFERENCE
=========

Expected successful vanilla sequence:

  P77A UJ_ACCEPT ret=1
      ->
  requested=700
      ->
  PlayAction700

Target Tobi question:

  semantic selector1 = 1

Does main+0x8B2B70 remain ret=0 before requested445?


NO GAMEPLAY FORCE
=================

P77A contains no:

- char281 gameplay branch
- state87 forcing
- action700 forcing
- selector8 override
- F58 override
- inline BLR replacement
- raw Event236 restore


TARGET BUILD
============

Nintendo Switch
Naruto x Boruto Ultimate Ninja Storm Connections
Update 1.70

Build ID:

48ece454b61412b9fb46fab2be3f5ef7b2804f39
''',
    encoding="utf-8"
)

print("P77_README_CREATE=PASS")


# ==================================================================
# 3. WORKFLOW P77A
# ==================================================================

w = WF76.read_text(encoding="utf-8")

# P76 workflow was already corrected to reuse generic P67 plumbing:
# prepare_exlaunch_p67a.sh + p67a_final.elf.
# Therefore only P76 build identity should become P77 identity.
w = w.replace("P76A", "P77A")
w = w.replace("p76a", "p77a")

# Defensive restoration in case any old mechanical names survive.
w = w.replace(
    "prepare_exlaunch_p77a.sh",
    "prepare_exlaunch_p67a.sh"
)

w = w.replace(
    "p77a_final.elf",
    "p67a_final.elf"
)

lines = w.splitlines()

if not lines:
    raise SystemExit(
        "FATAL: generated workflow unexpectedly empty"
    )

lines[0] = (
    "name: Build NSC P77A "
    "Low-Volume UJ Acceptance Probe"
)

w = "\n".join(lines) + "\n"

# Give artifact an accurate identity.
w = w.replace(
    "NSC-P77A-readonly-uj-fork-probe",
    "NSC-P77A-uj-acceptance-probe"
)

# Final workflow must contain P77 marker + inherited baseline markers.
required_wf = [
    "verify_p77a_kit.py",
    "prepare_exlaunch_p67a.sh",
    "p67a_final.elf",
    "[NSC:P77A] READY",
    "[NSC:P67A] READY",
    "[NSC:P64F] UJ_SEM_SET",
    "[NSC:P50A] READY",
    "README_P77A.txt",
    "229bbd6",
]

for needle in required_wf:
    if needle not in w:
        raise SystemExit(
            "FATAL: generated workflow missing: " + needle
        )

for forbidden in (
    "prepare_exlaunch_p77a.sh",
    "p77a_final.elf",
    "[NSC:P76A] READY",
    "README_P76A.txt",
):
    if forbidden in w:
        raise SystemExit(
            "FATAL: stale workflow reference: " + forbidden
        )

WF77.write_text(w, encoding="utf-8")

print("P77_WORKFLOW_CREATE=PASS")
print("P77A_BUILD_FILES=PASS")
print("VERIFIER=" + str(V77))
print("README=" + str(README))
print("WORKFLOW=" + str(WF77))
