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

if "[NSC:P77A]" in cpp:
    raise SystemExit("FATAL: P77A already present")

# ------------------------------------------------------------------
# Backups
# ------------------------------------------------------------------

for p in (CPP, HPP, MAIN):
    b = p.with_suffix(p.suffix + ".pre_p77a")

    if not b.exists():
        shutil.copy2(p, b)


# ==================================================================
# 1. CONSTANTS
# ==================================================================

anchor = re.search(
    r"^.*kP76UjCallerReturnOffset.*$",
    cpp,
    flags=re.M
)

if not anchor:
    raise SystemExit(
        "FATAL: P76 constant anchor not found"
    )

constants = r'''

// P77A:
// Low-volume / non-saturating native UJ acceptance probe.
//
// P76 runtime proved:
//   main+0x8B2B70 ret=1
// immediately precedes native requested action700.
//
// P77 focuses only on that helper and keeps semantic-enabled actors
// visible for the entire battle without a fixed global log cap.
constexpr ptrdiff_t kP77UjAcceptanceOffset =
    0x8B2B70;

constexpr ptrdiff_t kP77UjCallerReturnOffset =
    0x7F4648;
'''

pos = anchor.end()

cpp = (
    cpp[:pos]
    + constants
    + cpp[pos:]
)


# ==================================================================
# 2. P77 HOOK
# ==================================================================

hook_anchor = "HOOK_DEFINE_TRAMPOLINE(P64SemanticUjConsumerHook)"

idx = cpp.find(hook_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: P64 hook anchor not found"
    )

hook = r'''
// -----------------------------------------------------------------------------
// P77A — native UJ acceptance probe.
//
// Target:
//   main+0x8B2B70
//
// ABI proven by P75:
//   uint32_t(void* actor)
//
// Active classifier caller:
//   BL 0x8B2B70 @ main+0x7F4644
//   LR          = main+0x7F4648
//
// Logging rule:
//
//   active caller AND
//   (
//       semantic selector1 enabled
//       OR native return != 0
//       OR E94 changed during Orig
//       OR E9C changed during Orig
//   )
//
// There is intentionally NO n<512 cap.
//
// For a semantic-enabled custom actor we need continuous evidence until the
// actual XXA attempt occurs. This remains diagnostic only.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook) {
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

        if (caller_off == kP77UjCallerReturnOffset) {
            const bool interesting =
                semantic_pre
                || semantic_post
                || (ret != 0)
                || (pre_e94 != post_e94)
                || (pre_e9c != post_e9c);

            if (interesting) {
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
                    "[NSC:P77A] UJ_ACCEPT "
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
        } else if (ret != 0) {
            // Very small diagnostic for an unexpected positive return
            // from another caller. No gameplay behavior is changed.
            static std::atomic<uint32_t> other_positive{0};

            const uint32_t n =
                other_positive.fetch_add(
                    1,
                    std::memory_order_relaxed);

            if (n < 8) {
                Logging.Log(
                    "[NSC:P77A] UJ_OTHER_POSITIVE "
                    "n=%u actor=%p ret=%u "
                    "caller_off=0x%lx",
                    n,
                    actor,
                    ret,
                    static_cast<unsigned long>(
                        caller_off));
            }
        }

        return ret;
    }
};


'''

cpp = cpp[:idx] + hook + cpp[idx:]


# ==================================================================
# 3. P77 INSTALLER
# ==================================================================

end_anchor = "\n} // namespace nsc"

idx = cpp.rfind(end_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: final namespace anchor not found"
    )

installer = r'''

void InstallP77AAcceptanceProbe() {
    // Behavioral baseline stays P67A.
    //
    // P76 hooks are deliberately NOT installed here.
    // P76 source remains only as historical diagnostic code.
    InstallP67AActiveSelector1ConsumerBridge();

    static constexpr uint32_t kUjExpected[] = {
        0xF81E0FFE,
        0xA9014FF4,
        0x9108A014,
        0xAA0003F3,
        0xAA1403E0,
        0x52800101,
        0x97FC4DBE,
        0x340000A0,
    };

    bool ok = true;

    if (!MatchWords(
            kP77UjAcceptanceOffset,
            kUjExpected)) {
        LogFingerprintFail(
            "P77_UJ_ACCEPT",
            kP77UjAcceptanceOffset);

        ok = false;
    }

    if (ok) {
        P77UjAcceptanceHook::InstallAtOffset(
            kP77UjAcceptanceOffset);
    }

    Logging.Log(
        "[NSC:P77A] READY "
        "baseline_p67=1 "
        "probe_ok=%u "
        "uj=0x%lx "
        "uj_return=0x%lx "
        "semantic_focus=1 "
        "positive_ret_always_log=1 "
        "global_hot_cap=0 "
        "alt_probe_installed=0 "
        "readonly=1 "
        "preserve_orig=1 "
        "no_force87=1 "
        "no_force700=1 "
        "no_selector8=1 "
        "no_f58_override=1 "
        "no_char281_branch=1",
        ok ? 1u : 0u,
        static_cast<unsigned long>(
            kP77UjAcceptanceOffset),
        static_cast<unsigned long>(
            kP77UjCallerReturnOffset));
}

'''

cpp = cpp[:idx] + installer + cpp[idx:]


# ==================================================================
# 4. HEADER
# ==================================================================

decl_anchor = "void InstallP76AForkRuntimeProbe();"

if decl_anchor not in hpp:
    raise SystemExit(
        "FATAL: P76 declaration missing"
    )

hpp = hpp.replace(
    decl_anchor,
    decl_anchor
    + "\n"
    + "void InstallP77AAcceptanceProbe();",
    1
)


# ==================================================================
# 5. MAIN ENTRY
# ==================================================================

old = "nsc::InstallP76AForkRuntimeProbe();"

if main.count(old) != 1:
    raise SystemExit(
        "FATAL: expected exactly one P76 main call"
    )

main = main.replace(
    old,
    "nsc::InstallP77AAcceptanceProbe();",
    1
)

main = main.replace(
    "NSC P76A fork runtime probe exception",
    "NSC P77A UJ acceptance probe exception"
)


# ==================================================================
# SAVE
# ==================================================================

CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P77A_SOURCE_PATCH=PASS")
print("CPP=" + str(CPP))
print("HPP=" + str(HPP))
print("MAIN=" + str(MAIN))
