#!/usr/bin/env python3

from pathlib import Path
import shutil
import re

ROOT = Path("/storage/emulated/0/Downloads")

CPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN = ROOT / "overlay/source/program/main.cpp"

for p in (CPP, HPP, MAIN):
    if not p.is_file():
        raise SystemExit("FATAL: missing " + str(p))

cpp  = CPP.read_text(encoding="utf-8")
hpp  = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

if "[NSC:P78A]" in cpp:
    raise SystemExit("FATAL: P78A already present")

# ------------------------------------------------------------------
# Preconditions
# ------------------------------------------------------------------

required = [
    "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)",
    "void InstallP77AAcceptanceProbe()",
    "nsc::InstallP77AAcceptanceProbe();",
]

for needle in required[:2]:
    if needle not in cpp:
        raise SystemExit(
            "FATAL: missing P77 source prerequisite: " + needle
        )

if required[2] not in main:
    raise SystemExit(
        "FATAL: active main is not P77A baseline"
    )

# ------------------------------------------------------------------
# Backups
# ------------------------------------------------------------------

for p in (CPP, HPP, MAIN):
    b = p.with_suffix(p.suffix + ".pre_p78a")

    if not b.exists():
        shutil.copy2(p, b)

# ==================================================================
# 1. CONSTANTS
# ==================================================================

anchor = re.search(
    r"^.*kP77UjCallerReturnOffset.*$",
    cpp,
    flags=re.M
)

if not anchor:
    raise SystemExit(
        "FATAL: P77 constant anchor not found"
    )

constants = r'''

// P78A:
// Semantic-enabled ALT-route runtime probe.
//
// P77 runtime proved that the failing semantic-enabled custom actor
// does not reach the active 0x8B2B70 UJ helper call.
//
// P78 now probes the normal function-entry ALT helper reached from:
//
//   0x7F4590 MOV X0,X19
//   0x7F4594 BL  0x8B2D04
//   0x7F4598 ...
//
// ABI was locked in P75 as:
//   uint32_t(void* actor)
constexpr ptrdiff_t kP78AltRouteOffset =
    0x8B2D04;

constexpr ptrdiff_t kP78AltCallerReturnOffset =
    0x7F4598;
'''

pos = anchor.end()

cpp = (
    cpp[:pos]
    + constants
    + cpp[pos:]
)

# ==================================================================
# 2. P78 ALT HOOK
# ==================================================================

hook_anchor = "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)"

idx = cpp.find(hook_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: P77 hook anchor not found"
    )

hook = r'''
// -----------------------------------------------------------------------------
// P78A — semantic ALT-route probe.
//
// Target:
//   main+0x8B2D04
//
// Active caller:
//   BL 0x8B2D04 @ main+0x7F4594
//   LR          = main+0x7F4598
//
// ABI:
//   uint32_t(void* actor)
//
// Logging:
//   exact active caller only
//   AND semantic selector1 enabled.
//
// There is intentionally no char-ID branch and no gameplay write.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P78AltRouteHook) {
    static uint32_t Callback(void* actor) {
        const uintptr_t caller_lr =
            reinterpret_cast<uintptr_t>(
                __builtin_return_address(0));

        const ptrdiff_t caller_off =
            MainRelativeOffset(caller_lr);

        uint32_t pre_e94 = 0xFFFFFFFFu;
        uint32_t pre_e9c = 0xFFFFFFFFu;

        if (actor) {
            const auto* b =
                reinterpret_cast<
                    const volatile uint8_t*>(actor);

            pre_e94 =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE94);

            pre_e9c =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE9C);
        }

        const bool semantic_pre =
            P64QuerySemanticUltimateJutsu(actor);

        // Native behavior always executes.
        const uint32_t ret =
            Orig(actor);

        uint32_t post_e94 = 0xFFFFFFFFu;
        uint32_t post_e9c = 0xFFFFFFFFu;

        if (actor) {
            const auto* b =
                reinterpret_cast<
                    const volatile uint8_t*>(actor);

            post_e94 =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE94);

            post_e9c =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE9C);
        }

        const bool semantic_post =
            P64QuerySemanticUltimateJutsu(actor);

        if (
            caller_off == kP78AltCallerReturnOffset
            && (semantic_pre || semantic_post)
        ) {
            static std::atomic<uint32_t> seq{0};

            const uint32_t n =
                seq.fetch_add(
                    1,
                    std::memory_order_relaxed);

            uint32_t side = 0xFFFFFFFFu;
            uint32_t char_id = 0xFFFFFFFFu;

            const bool valid =
                ReadActorIdentity(
                    actor,
                    side,
                    char_id);

            Logging.Log(
                "[NSC:P78A] ALT_SEM "
                "seq=%u "
                "actor=%p valid=%u side=%u char=%u "
                "semantic=%u->%u "
                "ret=%u "
                "caller_off=0x%lx "
                "e94=%u->%u "
                "e9c=%u->%u",
                n,
                actor,
                valid ? 1u : 0u,
                side,
                char_id,
                semantic_pre ? 1u : 0u,
                semantic_post ? 1u : 0u,
                ret,
                static_cast<unsigned long>(
                    caller_off),
                pre_e94,
                post_e94,
                pre_e9c,
                post_e9c);
        }

        return ret;
    }
};


'''

cpp = cpp[:idx] + hook + cpp[idx:]

# ==================================================================
# 3. P78 INSTALLER
# ==================================================================

end_anchor = "\n} // namespace nsc"

idx = cpp.rfind(end_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: namespace end anchor not found"
    )

installer = r'''

void InstallP78ASemanticAltRouteProbe() {
    // Preserve P77 exactly:
    // P67 behavioral baseline + P77 UJ acceptance probe.
    InstallP77AAcceptanceProbe();

    static constexpr uint32_t kAltExpected[] = {
        0xF81D0FFE,
        0xA90157F6,
        0xA9024FF4,
        0x5282E208,
        0x72A00028,
        0xAA0003F3,
        0xB8686814,
        0x97FBE29D,
    };

    bool ok = true;

    if (!MatchWords(
            kP78AltRouteOffset,
            kAltExpected)) {
        LogFingerprintFail(
            "P78_ALT_ROUTE",
            kP78AltRouteOffset);

        ok = false;
    }

    if (ok) {
        P78AltRouteHook::InstallAtOffset(
            kP78AltRouteOffset);
    }

    Logging.Log(
        "[NSC:P78A] READY "
        "baseline_p77=1 "
        "probe_ok=%u "
        "alt=0x%lx "
        "alt_return=0x%lx "
        "semantic_only=1 "
        "global_hot_cap=0 "
        "readonly=1 "
        "preserve_orig=1 "
        "p77_uj_probe=1 "
        "no_force87=1 "
        "no_force700=1 "
        "no_selector8=1 "
        "no_f58_override=1 "
        "no_char281_branch=1",
        ok ? 1u : 0u,
        static_cast<unsigned long>(
            kP78AltRouteOffset),
        static_cast<unsigned long>(
            kP78AltCallerReturnOffset));
}

'''

cpp = cpp[:idx] + installer + cpp[idx:]

# ==================================================================
# 4. HEADER
# ==================================================================

decl_anchor = "void InstallP77AAcceptanceProbe();"

if decl_anchor not in hpp:
    raise SystemExit(
        "FATAL: P77 declaration missing"
    )

hpp = hpp.replace(
    decl_anchor,
    decl_anchor
    + "\n"
    + "void InstallP78ASemanticAltRouteProbe();",
    1
)

# ==================================================================
# 5. MAIN
# ==================================================================

old = "nsc::InstallP77AAcceptanceProbe();"

if main.count(old) != 1:
    raise SystemExit(
        "FATAL: expected exactly one active P77 call"
    )

main = main.replace(
    old,
    "nsc::InstallP78ASemanticAltRouteProbe();",
    1
)

main = main.replace(
    "NSC P77A UJ acceptance probe exception",
    "NSC P78A semantic ALT route probe exception"
)

# ==================================================================
# SAVE
# ==================================================================

CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P78A_SOURCE_PATCH=PASS")
print("CPP=" + str(CPP))
print("HPP=" + str(HPP))
print("MAIN=" + str(MAIN))
