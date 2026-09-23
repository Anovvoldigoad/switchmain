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

if "[NSC:P79A]" in cpp:
    raise SystemExit("FATAL: P79A already present")

for needle in (
    "void InstallP77AAcceptanceProbe()",
    "void InstallP78ASemanticAltRouteProbe()",
    "HOOK_DEFINE_TRAMPOLINE(P77UjAcceptanceHook)",
):
    if needle not in cpp:
        raise SystemExit(
            "FATAL: source prerequisite missing: " + needle
        )

if main.count(
    "nsc::InstallP78ASemanticAltRouteProbe();"
) != 1:
    raise SystemExit(
        "FATAL: main is not currently P78A"
    )


# ==================================================================
# BACKUPS
# ==================================================================

for p in (CPP, HPP, MAIN):
    backup = p.with_suffix(p.suffix + ".pre_p79a")

    if not backup.exists():
        shutil.copy2(p, backup)


# ==================================================================
# CONSTANTS
# ==================================================================

# Insert only AFTER the complete P78 declaration including semicolon.
m = re.search(
    r'''
    constexpr\s+ptrdiff_t\s+kP78AltCallerReturnOffset\s*=
    \s*0x7F4598\s*;
    ''',
    cpp,
    re.X
)

if not m:
    raise SystemExit(
        "FATAL: complete P78 caller constant not found"
    )

constants = r'''

// P79A:
// Split composite virtual+0x1288 decision into its two proven
// subpredicates.
//
// Parent:
//   main+0x7EAC34
//
// A:
//   BL main+0x7EAC70
//   LR main+0x7EAC40
//
// B:
//   virtual +0x1298
//   concrete Tobi implementation main+0x7EACF0
//   BLR return LR main+0x7EAC60
constexpr ptrdiff_t kP79PredicateAOffset =
    0x7EAC70;

constexpr ptrdiff_t kP79PredicateACallerReturnOffset =
    0x7EAC40;

constexpr ptrdiff_t kP79PredicateBOffset =
    0x7EACF0;

constexpr ptrdiff_t kP79PredicateBCallerReturnOffset =
    0x7EAC60;
'''

cpp = (
    cpp[:m.end()]
    + constants
    + cpp[m.end():]
)


# ==================================================================
# CALLBACK GENERATOR
# ==================================================================

hook_anchor = "HOOK_DEFINE_TRAMPOLINE(P78AltRouteHook)"

idx = cpp.find(hook_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: P78 hook anchor not found"
    )

hooks = r'''
// -----------------------------------------------------------------------------
// P79A Predicate A.
//
// Exact parent call:
//   main+0x7EAC3C BL main+0x7EAC70
//   LR = main+0x7EAC40
//
// Only exact parent calls are inspected.
// Other callers, including Predicate A recursion, immediately preserve native
// behavior without touching semantic diagnostics.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P79PredicateAHook) {
    static uint32_t Callback(void* actor) {
        const uintptr_t caller_lr =
            reinterpret_cast<uintptr_t>(
                __builtin_return_address(0));

        const ptrdiff_t caller_off =
            MainRelativeOffset(caller_lr);

        if (
            caller_off
            != kP79PredicateACallerReturnOffset
        ) {
            return Orig(actor);
        }

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

        const uint32_t ret =
            Orig(actor);

        const bool semantic_post =
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

        if (semantic_pre || semantic_post) {
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
                "[NSC:P79A] PRED_A "
                "seq=%u actor=%p valid=%u "
                "side=%u char=%u "
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


// -----------------------------------------------------------------------------
// P79A Predicate B.
//
// Exact parent virtual call:
//   main+0x7EAC5C BLR X8
//   LR = main+0x7EAC60
//
// Concrete implementation for the proven Tobi vtable:
//   main+0x7EACF0
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P79PredicateBHook) {
    static uint32_t Callback(void* actor) {
        const uintptr_t caller_lr =
            reinterpret_cast<uintptr_t>(
                __builtin_return_address(0));

        const ptrdiff_t caller_off =
            MainRelativeOffset(caller_lr);

        if (
            caller_off
            != kP79PredicateBCallerReturnOffset
        ) {
            return Orig(actor);
        }

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

        const uint32_t ret =
            Orig(actor);

        const bool semantic_post =
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

        if (semantic_pre || semantic_post) {
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
                "[NSC:P79A] PRED_B "
                "seq=%u actor=%p valid=%u "
                "side=%u char=%u "
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

cpp = (
    cpp[:idx]
    + hooks
    + cpp[idx:]
)


# ==================================================================
# INSTALLER
# ==================================================================

namespace_end = "\n} // namespace nsc"

idx = cpp.rfind(namespace_end)

if idx < 0:
    raise SystemExit(
        "FATAL: namespace end not found"
    )

installer = r'''

void InstallP79ADualSubpredicateProbe() {
    // P78's ALT-route result is already runtime-proven.
    // Do not install its hot per-frame logger again.
    //
    // Preserve:
    //   P67 behavioral baseline
    //   P77 UJ negative-control probe
    InstallP77AAcceptanceProbe();

    static constexpr uint32_t kAExpected[] = {
        0xA9BF4FFE,
        0xB94E9408,
        0x7101F11F,
        0x54000081,
        0x52800020,
        0xA8C14FFE,
        0xD65F03C0,
        0xAA0003F3,
    };

    static constexpr uint32_t kBExpected[] = {
        0xF81F0FFE,
        0x5281F008,
        0x72A00028,
        0x52800021,
        0xF8686800,
        0x97FE31A1,
        0xF100001F,
        0x1A9F07E0,
    };

    bool ok = true;

    if (!MatchWords(
            kP79PredicateAOffset,
            kAExpected)) {
        LogFingerprintFail(
            "P79_PRED_A",
            kP79PredicateAOffset);

        ok = false;
    }

    if (!MatchWords(
            kP79PredicateBOffset,
            kBExpected)) {
        LogFingerprintFail(
            "P79_PRED_B",
            kP79PredicateBOffset);

        ok = false;
    }

    if (ok) {
        P79PredicateAHook::InstallAtOffset(
            kP79PredicateAOffset);

        P79PredicateBHook::InstallAtOffset(
            kP79PredicateBOffset);
    }

    Logging.Log(
        "[NSC:P79A] READY "
        "baseline_p77=1 "
        "probe_ok=%u "
        "a=0x%lx "
        "a_return=0x%lx "
        "b=0x%lx "
        "b_return=0x%lx "
        "semantic_only=1 "
        "p78_alt_probe_installed=0 "
        "p77_uj_probe=1 "
        "readonly=1 "
        "preserve_orig=1 "
        "no_force_return=1 "
        "no_force87=1 "
        "no_force700=1 "
        "no_selector8=1 "
        "no_f58_override=1 "
        "no_char281_branch=1",
        ok ? 1u : 0u,
        static_cast<unsigned long>(
            kP79PredicateAOffset),
        static_cast<unsigned long>(
            kP79PredicateACallerReturnOffset),
        static_cast<unsigned long>(
            kP79PredicateBOffset),
        static_cast<unsigned long>(
            kP79PredicateBCallerReturnOffset));
}

'''

cpp = (
    cpp[:idx]
    + installer
    + cpp[idx:]
)


# ==================================================================
# HEADER
# ==================================================================

decl = "void InstallP78ASemanticAltRouteProbe();"

if decl not in hpp:
    raise SystemExit(
        "FATAL: P78 declaration missing"
    )

hpp = hpp.replace(
    decl,
    decl
    + "\n"
    + "void InstallP79ADualSubpredicateProbe();",
    1
)


# ==================================================================
# MAIN
# ==================================================================

old_main = "nsc::InstallP78ASemanticAltRouteProbe();"

if main.count(old_main) != 1:
    raise SystemExit(
        "FATAL: expected exactly one P78 main call"
    )

main = main.replace(
    old_main,
    "nsc::InstallP79ADualSubpredicateProbe();",
    1
)

main = main.replace(
    "NSC P78A semantic ALT route probe exception",
    "NSC P79A dual subpredicate probe exception"
)


# ==================================================================
# SAVE
# ==================================================================

CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P79A_SOURCE_PATCH=PASS")
