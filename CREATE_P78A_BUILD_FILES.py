#!/usr/bin/env python3

from pathlib import Path

ROOT = Path("/storage/emulated/0/Downloads")

CPP   = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP   = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN  = ROOT / "overlay/source/program/main.cpp"

V77   = ROOT / "verify_p77a_kit.py"
V78   = ROOT / "verify_p78a_kit.py"

WF77  = ROOT / ".github/workflows/build-subsdk9-p77a.yml"
WF78  = ROOT / ".github/workflows/build-subsdk9-p78a.yml"

README = ROOT / "README_P78A.txt"

for p in (CPP, HPP, MAIN, V77, WF77):
    if not p.is_file():
        raise SystemExit(
            "FATAL: missing prerequisite: " + str(p)
        )

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

# ================================================================
# SOURCE PREREQUISITES
# ================================================================

for needle in (
    "HOOK_DEFINE_TRAMPOLINE(P78AltRouteHook)",
    "void InstallP78ASemanticAltRouteProbe()",
    "[NSC:P78A] ALT_SEM",
    "[NSC:P78A] READY",
    "kP78AltRouteOffset",
    "kP78AltCallerReturnOffset",
):
    if needle not in cpp:
        raise SystemExit(
            "FATAL: P78 source missing: " + needle
        )

if main.count(
    "nsc::InstallP78ASemanticAltRouteProbe();"
) != 1:
    raise SystemExit(
        "FATAL: main must call P78 exactly once"
    )

if "void InstallP78ASemanticAltRouteProbe();" not in hpp:
    raise SystemExit(
        "FATAL: P78 header declaration missing"
    )

print("P78_SOURCE_PREREQ=PASS")


# ================================================================
# VERIFIER
# ================================================================

s = V77.read_text(encoding="utf-8")

# Active entry moves P77 -> P78.
old_main = "nsc::InstallP77AAcceptanceProbe();"
new_main = "nsc::InstallP78ASemanticAltRouteProbe();"

count = s.count(old_main)

if count < 1:
    raise SystemExit(
        "FATAL: no P77 active-main expectations found"
    )

s = s.replace(old_main, new_main)

# ---------------------------------------------------------------
# Historical P76 UJ hook boundary:
#
# source order is now:
#   P76 UJ
#   P78 ALT
#   P77 UJ
#
# Therefore P76 body must stop at P78, not P77.
# ---------------------------------------------------------------

old_boundary = '''_p64 = _p76_cpp.find(
    "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)",
    _uj0
)

if _p64 < 0:
    _p64 = _p76_cpp.find(
        "HOOK_DEFINE_TRAMPOLINE(P64SemanticUjConsumerHook)",
        _uj0
    )'''

new_boundary = '''_p64 = _p76_cpp.find(
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
    )'''

if old_boundary in s:
    s = s.replace(
        old_boundary,
        new_boundary,
        1
    )
else:
    raise SystemExit(
        "FATAL: historical P76 hook boundary block not found"
    )

# ---------------------------------------------------------------
# Historical P77 installer must stop before P78 installer.
# ---------------------------------------------------------------

old_p77_inst = '''installer = _p77_cpp[i0:]'''

new_p77_inst = '''_p78_inst0 = _p77_cpp.find(
    "void InstallP78ASemanticAltRouteProbe()",
    i0
)

if _p78_inst0 >= 0:
    installer = _p77_cpp[i0:_p78_inst0]
else:
    installer = _p77_cpp[i0:]'''

if old_p77_inst in s:
    s = s.replace(
        old_p77_inst,
        new_p77_inst,
        1
    )

# P77 final marker becomes historical milestone.
marker = 'print("P77A_STATIC_VERIFY=PASS")'

if s.count(marker) != 1:
    raise SystemExit(
        "FATAL: P77 final verifier marker missing"
    )

extra = r'''
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
'''

s = s.replace(
    marker,
    'print("P77A_SOURCE_HISTORY_VERIFY=PASS")\n'
    + extra
    + '\nprint("P78A_STATIC_VERIFY=PASS")',
    1
)

V78.write_text(s, encoding="utf-8")

print(
    "P78_VERIFIER_CREATE=PASS "
    f"replaced_active_refs={count}"
)


# ================================================================
# README
# ================================================================

README.write_text(
r'''NSC P78A — SEMANTIC ALT ROUTE PROBE

BASELINE
========

P78A preserves P77A.

P77A preserves P67A behavioral safety and probes the native UJ helper
at main+0x8B2B70.

P77 runtime proved:

successful vanilla UJ:
  0x8B2B70 ret=1
  -> requested700

failing semantic-enabled Tobi route:
  no active 0x8B2B70 UJ_ACCEPT record
  -> requested445

Therefore P78 investigates the upstream alternate route.


TARGET
======

ALT helper:

  main+0x8B2D04

Exact active caller return:

  main+0x7F4598

ABI:

  uint32_t(void* actor)


LOGGING
=======

P78 logs ALT_SEM only when:

  caller == main+0x7F4598

and:

  semantic selector1 is enabled.

Native behavior is always preserved:

  ret = Orig(actor)
  return ret


PURPOSE
=======

Determine whether the semantic-enabled failing actor enters the ALT
path immediately before requested445.

If ALT_SEM is observed while P77 records no UJ_ACCEPT for the same
actor during that attempt, the early route divergence is runtime-proven.


NO GAMEPLAY FORCE
=================

No:

- char281 gameplay branch
- state87 forcing
- action700 forcing
- helper-return forcing
- selector8 override
- F58 override
- inline BLR replacement
- raw Event236 restore


TARGET
======

Nintendo Switch
Naruto x Boruto Ultimate Ninja Storm Connections
Update 1.70

Build ID:

48ece454b61412b9fb46fab2be3f5ef7b2804f39
''',
    encoding="utf-8"
)

print("P78_README_CREATE=PASS")


# ================================================================
# WORKFLOW
# ================================================================

w = WF77.read_text(encoding="utf-8")

w = w.replace("P77A", "P78A")
w = w.replace("p77a", "p78a")

# Generic P67 plumbing remains intentional.
w = w.replace(
    "prepare_exlaunch_p78a.sh",
    "prepare_exlaunch_p67a.sh"
)

w = w.replace(
    "p78a_final.elf",
    "p67a_final.elf"
)

lines = w.splitlines()

if not lines:
    raise SystemExit(
        "FATAL: generated workflow empty"
    )

lines[0] = (
    "name: Build NSC P78A "
    "Semantic ALT Route Probe"
)

w = "\n".join(lines) + "\n"

w = w.replace(
    "NSC-P78A-uj-acceptance-probe",
    "NSC-P78A-semantic-alt-route-probe"
)

# Clone replacement changes P77 READY -> P78 READY.
# P78 actively installs P77, therefore require both.
p78line = "          grep -aFq '[NSC:P78A] READY' \"$ELF\"\n"
p77line = "          grep -aFq '[NSC:P77A] READY' \"$ELF\"\n"

if p78line not in w:
    raise SystemExit(
        "FATAL: P78 READY assertion missing"
    )

if p77line not in w:
    w = w.replace(
        p78line,
        p78line + p77line,
        1
    )

required = (
    "verify_p78a_kit.py",
    "prepare_exlaunch_p67a.sh",
    "p67a_final.elf",
    "[NSC:P78A] READY",
    "[NSC:P77A] READY",
    "[NSC:P67A] READY",
    "[NSC:P64F] UJ_SEM_SET",
    "[NSC:P50A] READY",
    "README_P78A.txt",
    "229bbd6",
)

for needle in required:
    if needle not in w:
        raise SystemExit(
            "FATAL: workflow missing: " + needle
        )

for forbidden in (
    "prepare_exlaunch_p78a.sh",
    "p78a_final.elf",
    "[NSC:P76A] READY",
    "README_P77A.txt",
):
    if forbidden in w:
        raise SystemExit(
            "FATAL: stale workflow reference: " + forbidden
        )

WF78.write_text(w, encoding="utf-8")

print("P78_WORKFLOW_CREATE=PASS")
print("P78A_BUILD_FILES=PASS")
