#!/usr/bin/env python3

from pathlib import Path
import shutil
import re

ROOT = Path("/storage/emulated/0/Downloads")

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN = ROOT / "overlay/source/program/main.cpp"

for p in (CPP, HPP, MAIN):
    if not p.is_file():
        raise SystemExit(f"FATAL: missing {p}")

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

if "[NSC:P76A]" in cpp:
    raise SystemExit("FATAL: P76A already present")

# ------------------------------------------------------------------
# Backups
# ------------------------------------------------------------------

for p in (CPP, HPP, MAIN):
    backup = p.with_suffix(p.suffix + ".pre_p76a")
    if not backup.exists():
        shutil.copy2(p, backup)

# ------------------------------------------------------------------
# 1. Constants
# ------------------------------------------------------------------

anchor = re.search(
    r"^.*kUjSemanticConsumerOffset.*$",
    cpp,
    flags=re.M
)

if not anchor:
    raise SystemExit(
        "FATAL: kUjSemanticConsumerOffset anchor not found"
    )

constants = r'''
// P76A: read-only early UJ/alternate corridor probes.
constexpr ptrdiff_t kP76AltCorridorOffset      = 0x8B2D04;
constexpr ptrdiff_t kP76UjCorridorOffset       = 0x8B2B70;
constexpr ptrdiff_t kP76AltCallerReturnOffset  = 0x7F4598;
constexpr ptrdiff_t kP76UjCallerReturnOffset   = 0x7F4648;
'''

pos = anchor.end()

cpp = (
    cpp[:pos]
    + "\n"
    + constants
    + cpp[pos:]
)

# ------------------------------------------------------------------
# 2. Hook definitions
# Insert after all helper functions needed by the callbacks and
# immediately before the already-existing P64 consumer hook.
# ------------------------------------------------------------------

hook_anchor = "HOOK_DEFINE_TRAMPOLINE(P64SemanticUjConsumerHook)"

idx = cpp.find(hook_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: P64SemanticUjConsumerHook anchor not found"
    )

hooks = r'''
// -----------------------------------------------------------------------------
// P76A — read-only fork probes.
//
// Static ABI lock:
//   0x8B2D04 : uint32_t(actor)
//   0x8B2B70 : uint32_t(actor)
//
// IMPORTANT:
// - normal function-entry trampolines only;
// - Orig(actor) always executes;
// - native return is returned unchanged;
// - no gameplay field is written.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P76AltCorridorHook) {
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
                reinterpret_cast<const volatile uint8_t*>(actor);

            pre_e94 =
                *reinterpret_cast<const volatile uint32_t*>(
                    b + 0xE94);

            pre_e9c =
                *reinterpret_cast<const volatile uint32_t*>(
                    b + 0xE9C);
        }

        const uint32_t ret = Orig(actor);

        // Exact active classifier caller only.
        if (caller_off == kP76AltCallerReturnOffset) {
            static std::atomic<uint32_t> logs{0};
            const uint32_t n =
                logs.fetch_add(
                    1,
                    std::memory_order_relaxed);

            if (n < 512) {
                uint32_t side = 0xFFFFFFFFu;
                uint32_t char_id = 0xFFFFFFFFu;

                const bool valid =
                    ReadActorIdentity(
                        actor,
                        side,
                        char_id);

                const bool semantic =
                    P64QuerySemanticUltimateJutsu(actor);

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

                Logging.Log(
                    "[NSC:P76A] ALT_CORRIDOR "
                    "n=%u actor=%p valid=%u side=%u char=%u "
                    "semantic=%u ret=%u "
                    "caller_off=0x%lx "
                    "e94=%u->%u e9c=%u->%u",
                    n,
                    actor,
                    valid ? 1u : 0u,
                    side,
                    char_id,
                    semantic ? 1u : 0u,
                    ret,
                    static_cast<unsigned long>(caller_off),
                    pre_e94,
                    post_e94,
                    pre_e9c,
                    post_e9c);
            }
        } else {
            // Tiny diagnostic in case LR provenance differs from
            // the static caller expectation. This does not alter
            // the return value.
            static std::atomic<uint32_t> other_logs{0};

            const uint32_t n =
                other_logs.fetch_add(
                    1,
                    std::memory_order_relaxed);

            if (n < 4) {
                Logging.Log(
                    "[NSC:P76A] ALT_OTHER "
                    "actor=%p ret=%u caller_off=0x%lx",
                    actor,
                    ret,
                    static_cast<unsigned long>(caller_off));
            }
        }

        return ret;
    }
};


HOOK_DEFINE_TRAMPOLINE(P76UjCorridorHook) {
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
                reinterpret_cast<const volatile uint8_t*>(actor);

            pre_e94 =
                *reinterpret_cast<const volatile uint32_t*>(
                    b + 0xE94);

            pre_e9c =
                *reinterpret_cast<const volatile uint32_t*>(
                    b + 0xE9C);
        }

        const uint32_t ret = Orig(actor);

        if (caller_off == kP76UjCallerReturnOffset) {
            static std::atomic<uint32_t> logs{0};
            const uint32_t n =
                logs.fetch_add(
                    1,
                    std::memory_order_relaxed);

            if (n < 512) {
                uint32_t side = 0xFFFFFFFFu;
                uint32_t char_id = 0xFFFFFFFFu;

                const bool valid =
                    ReadActorIdentity(
                        actor,
                        side,
                        char_id);

                const bool semantic =
                    P64QuerySemanticUltimateJutsu(actor);

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

                Logging.Log(
                    "[NSC:P76A] UJ_CORRIDOR "
                    "n=%u actor=%p valid=%u side=%u char=%u "
                    "semantic=%u ret=%u "
                    "caller_off=0x%lx "
                    "e94=%u->%u e9c=%u->%u",
                    n,
                    actor,
                    valid ? 1u : 0u,
                    side,
                    char_id,
                    semantic ? 1u : 0u,
                    ret,
                    static_cast<unsigned long>(caller_off),
                    pre_e94,
                    post_e94,
                    pre_e9c,
                    post_e9c);
            }
        } else {
            static std::atomic<uint32_t> other_logs{0};

            const uint32_t n =
                other_logs.fetch_add(
                    1,
                    std::memory_order_relaxed);

            if (n < 4) {
                Logging.Log(
                    "[NSC:P76A] UJ_OTHER "
                    "actor=%p ret=%u caller_off=0x%lx",
                    actor,
                    ret,
                    static_cast<unsigned long>(caller_off));
            }
        }

        return ret;
    }
};


'''

cpp = cpp[:idx] + hooks + cpp[idx:]

# ------------------------------------------------------------------
# 3. New public installer wraps P67A.
# ------------------------------------------------------------------

end_anchor = "\n} // namespace nsc"

idx = cpp.rfind(end_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: final namespace anchor not found"
    )

installer = r'''

void InstallP76AForkRuntimeProbe() {
    // Preserve the complete P67A behavior first.
    InstallP67AActiveSelector1ConsumerBridge();

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
            kP76AltCorridorOffset,
            kAltExpected)) {
        LogFingerprintFail(
            "P76_ALT_CORRIDOR",
            kP76AltCorridorOffset);

        ok = false;
    }

    if (!MatchWords(
            kP76UjCorridorOffset,
            kUjExpected)) {
        LogFingerprintFail(
            "P76_UJ_CORRIDOR",
            kP76UjCorridorOffset);

        ok = false;
    }

    if (ok) {
        P76AltCorridorHook::InstallAtOffset(
            kP76AltCorridorOffset);

        P76UjCorridorHook::InstallAtOffset(
            kP76UjCorridorOffset);
    }

    Logging.Log(
        "[NSC:P76A] READY "
        "baseline_p67=1 "
        "probe_ok=%u "
        "alt=0x%lx alt_return=0x%lx "
        "uj=0x%lx uj_return=0x%lx "
        "readonly=1 preserve_orig=1 "
        "no_force87=1 no_force700=1 "
        "no_selector8=1 no_f58_override=1 "
        "no_char281_branch=1",
        ok ? 1u : 0u,
        static_cast<unsigned long>(
            kP76AltCorridorOffset),
        static_cast<unsigned long>(
            kP76AltCallerReturnOffset),
        static_cast<unsigned long>(
            kP76UjCorridorOffset),
        static_cast<unsigned long>(
            kP76UjCallerReturnOffset));
}

'''

cpp = cpp[:idx] + installer + cpp[idx:]

# ------------------------------------------------------------------
# 4. Header.
# ------------------------------------------------------------------

old_decl = "void InstallP67AActiveSelector1ConsumerBridge();"

if old_decl not in hpp:
    raise SystemExit(
        "FATAL: P67 declaration not found in header"
    )

new_decl = (
    old_decl
    + "\n"
    + "void InstallP76AForkRuntimeProbe();"
)

hpp = hpp.replace(
    old_decl,
    new_decl,
    1
)

# ------------------------------------------------------------------
# 5. main.cpp: new public installer.
# ------------------------------------------------------------------

old_call = (
    "nsc::InstallP67AActiveSelector1ConsumerBridge();"
)

if main.count(old_call) != 1:
    raise SystemExit(
        "FATAL: expected exactly one P67 install call"
    )

main = main.replace(
    old_call,
    "nsc::InstallP76AForkRuntimeProbe();",
    1
)

main = main.replace(
    "NSC P67A active selector1 consumer bridge exception",
    "NSC P76A fork runtime probe exception"
)

CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P76A_SOURCE_PATCH=PASS")
print("CPP=" + str(CPP))
print("HPP=" + str(HPP))
print("MAIN=" + str(MAIN))
