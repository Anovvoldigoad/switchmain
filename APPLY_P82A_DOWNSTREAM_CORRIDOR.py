#!/usr/bin/env python3

from pathlib import Path
import shutil

ROOT = Path("/storage/emulated/0/Downloads")

CPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN = ROOT / "overlay/source/program/main.cpp"

for p in (CPP, HPP, MAIN):
    if not p.is_file():
        raise SystemExit("FATAL missing: " + str(p))

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")


# ============================================================
# FAIL-CLOSED BASELINE
# ============================================================

if main.count(
    "nsc::InstallP81AOugiAwakeningPolicyBridge();"
) != 1:
    raise SystemExit(
        "FATAL: active main is not clean P81A"
    )

if "InstallP82ADownstreamCorridorProbe" in main:
    raise SystemExit(
        "FATAL: P82A already active"
    )

required = (
    "HOOK_DEFINE_TRAMPOLINE(P81OugiAwakeningPolicyHook)",
    "void InstallP81AOugiAwakeningPolicyBridge()",
    "P64QuerySemanticUltimateJutsu",
    "ReadActorIdentity",
    "MainRelativeOffset",
    "MatchWords",
    "LogFingerprintFail",
)

for x in required:
    if x not in cpp:
        raise SystemExit(
            "FATAL prerequisite missing: " + x
        )


# ============================================================
# BACKUP
# ============================================================

for p in (CPP, HPP, MAIN):
    bak = p.with_suffix(p.suffix + ".pre_p82a")

    if not bak.exists():
        shutil.copy2(p, bak)


# ============================================================
# CONSTANTS
# ============================================================

anchor = "std::atomic<uint32_t> g_p81_policy_seq{0};"

if anchor not in cpp:
    raise SystemExit(
        "FATAL P81 constant anchor missing"
    )

block = r'''

// ============================================================================
// P82A — full downstream UJ corridor trace.
//
// P81A proved:
//   +0x1288 native=1 -> policy=0
//
// P77 runtime then proved:
//   0x8B2B70 can return 1 while action445 still wins.
//
// P82A traces every safe normal-function boundary from that point forward.
// Read-only. All Orig() returns are preserved.
// ============================================================================

constexpr ptrdiff_t kP82StatePredicateOffset =
    0x794EC8;
constexpr ptrdiff_t kP82StatePredicateReturnOffset =
    0x7F4660;

constexpr ptrdiff_t kP82MidPredicateOffset =
    0x64A030;
constexpr ptrdiff_t kP82MidPredicateReturnOffset =
    0x7F4680;

constexpr ptrdiff_t kP82MaskPredicateOffset =
    0x7C5FFC;
constexpr ptrdiff_t kP82MaskPredicateReturnOffset =
    0x7F4698;

constexpr ptrdiff_t kP82PostGateOffset =
    0x7D2DE4;
constexpr ptrdiff_t kP82PostGateReturn0Offset =
    0x7F46C8;
constexpr ptrdiff_t kP82PostGateReturn1Offset =
    0x7F4780;

constexpr ptrdiff_t kP82ControlGetterOffset =
    0x7C6280;
constexpr ptrdiff_t kP82ControlReturn8AOffset =
    0x7F4790;
constexpr ptrdiff_t kP82ControlReturn40Offset =
    0x7F47E4;
constexpr ptrdiff_t kP82ControlReturn8BOffset =
    0x7F4814;

std::atomic<uint32_t> g_p82_state_seq{0};
std::atomic<uint32_t> g_p82_mid_seq{0};
std::atomic<uint32_t> g_p82_mask_seq{0};
std::atomic<uint32_t> g_p82_post_seq{0};
std::atomic<uint32_t> g_p82_ctrl_seq{0};

'''

cpp = cpp.replace(
    anchor,
    anchor + block,
    1,
)


# ============================================================
# HOOKS
# ============================================================

hook_anchor = (
    "HOOK_DEFINE_TRAMPOLINE(P80BContextHook)"
)

pos = cpp.find(hook_anchor)

if pos < 0:
    raise SystemExit(
        "FATAL P80B hook anchor missing"
    )

hooks = r'''
// -----------------------------------------------------------------------------
// P82A 0x794EC8
// Exact central-corridor return: 0x7F4660.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P82StatePredicateHook) {
    static uint32_t Callback(void* actor) {
        const ptrdiff_t caller_off =
            MainRelativeOffset(
                reinterpret_cast<uintptr_t>(
                    __builtin_return_address(0)));

        const uint32_t ret =
            Orig(actor);

        if (
            caller_off
            != kP82StatePredicateReturnOffset
        ) {
            return ret;
        }

        uint32_t side = 0xFFFFFFFFu;
        uint32_t char_id = 0xFFFFFFFFu;

        const bool valid =
            ReadActorIdentity(
                actor,
                side,
                char_id);

        const bool semantic =
            actor
            && P64QuerySemanticUltimateJutsu(
                actor);

        if (valid && semantic) {
            uint32_t e94 = 0xFFFFFFFFu;
            uint32_t e9c = 0xFFFFFFFFu;

            const auto* b =
                reinterpret_cast<
                    const volatile uint8_t*>(
                    actor);

            e94 =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE94);

            e9c =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE9C);

            const uint32_t seq =
                g_p82_state_seq.fetch_add(
                    1,
                    std::memory_order_relaxed);

            Logging.Log(
                "[NSC:P82A] H794EC8 "
                "seq=%u actor=%p "
                "side=%u char=%u "
                "semantic=%u ret=%u "
                "caller_off=0x%lx "
                "e94=%u e9c=%u",
                seq,
                actor,
                side,
                char_id,
                semantic ? 1u : 0u,
                ret,
                static_cast<unsigned long>(
                    caller_off),
                e94,
                e9c);
        }

        return ret;
    }
};


// -----------------------------------------------------------------------------
// P82A 0x64A030
// Exact return: 0x7F4680.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P82MidPredicateHook) {
    static uint32_t Callback(void* actor) {
        const ptrdiff_t caller_off =
            MainRelativeOffset(
                reinterpret_cast<uintptr_t>(
                    __builtin_return_address(0)));

        const uint32_t ret =
            Orig(actor);

        if (
            caller_off
            != kP82MidPredicateReturnOffset
        ) {
            return ret;
        }

        uint32_t side = 0xFFFFFFFFu;
        uint32_t char_id = 0xFFFFFFFFu;

        const bool valid =
            ReadActorIdentity(
                actor,
                side,
                char_id);

        const bool semantic =
            actor
            && P64QuerySemanticUltimateJutsu(
                actor);

        if (valid && semantic) {
            const uint32_t seq =
                g_p82_mid_seq.fetch_add(
                    1,
                    std::memory_order_relaxed);

            Logging.Log(
                "[NSC:P82A] H64A030 "
                "seq=%u actor=%p "
                "side=%u char=%u "
                "semantic=%u ret=%u "
                "caller_off=0x%lx",
                seq,
                actor,
                side,
                char_id,
                semantic ? 1u : 0u,
                ret,
                static_cast<unsigned long>(
                    caller_off));
        }

        return ret;
    }
};


// -----------------------------------------------------------------------------
// P82A 0x7C5FFC
// Generic bitmask helper.
// Exact central-corridor return: 0x7F4698.
// x0 is intentionally NOT assumed to be actor.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P82MaskPredicateHook) {
    static uint32_t Callback(void* object) {
        const ptrdiff_t caller_off =
            MainRelativeOffset(
                reinterpret_cast<uintptr_t>(
                    __builtin_return_address(0)));

        const uint32_t ret =
            Orig(object);

        if (
            caller_off
            == kP82MaskPredicateReturnOffset
        ) {
            const uint32_t seq =
                g_p82_mask_seq.fetch_add(
                    1,
                    std::memory_order_relaxed);

            Logging.Log(
                "[NSC:P82A] H7C5FFC "
                "seq=%u object=%p "
                "ret=%u caller_off=0x%lx",
                seq,
                object,
                ret,
                static_cast<unsigned long>(
                    caller_off));
        }

        return ret;
    }
};


// -----------------------------------------------------------------------------
// P82A 0x7D2DE4
//
// Two proven calls inside the same UJ corridor:
//
// 0x7F46C4 -> LR 0x7F46C8
// 0x7F477C -> LR 0x7F4780
//
// Presence of the first call also proves the preceding virtual +0xF58
// returned non-zero. No F58 behavior is changed.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P82PostGateHook) {
    static uint32_t Callback(
        void* actor,
        uint32_t mode
    ) {
        const ptrdiff_t caller_off =
            MainRelativeOffset(
                reinterpret_cast<uintptr_t>(
                    __builtin_return_address(0)));

        const uint32_t ret =
            Orig(actor, mode);

        if (
            caller_off
                != kP82PostGateReturn0Offset
            &&
            caller_off
                != kP82PostGateReturn1Offset
        ) {
            return ret;
        }

        uint32_t side = 0xFFFFFFFFu;
        uint32_t char_id = 0xFFFFFFFFu;

        const bool valid =
            ReadActorIdentity(
                actor,
                side,
                char_id);

        const bool semantic =
            actor
            && P64QuerySemanticUltimateJutsu(
                actor);

        if (valid && semantic) {
            uint32_t e94 = 0xFFFFFFFFu;
            uint32_t e9c = 0xFFFFFFFFu;

            const auto* b =
                reinterpret_cast<
                    const volatile uint8_t*>(
                    actor);

            e94 =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE94);

            e9c =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0xE9C);

            const uint32_t seq =
                g_p82_post_seq.fetch_add(
                    1,
                    std::memory_order_relaxed);

            Logging.Log(
                "[NSC:P82A] H7D2DE4 "
                "seq=%u actor=%p "
                "side=%u char=%u "
                "semantic=%u mode=%u "
                "ret=%u caller_off=0x%lx "
                "e94=%u e9c=%u",
                seq,
                actor,
                side,
                char_id,
                semantic ? 1u : 0u,
                mode,
                ret,
                static_cast<unsigned long>(
                    caller_off),
                e94,
                e9c);
        }

        return ret;
    }
};


// -----------------------------------------------------------------------------
// P82A native control getter 0x7C6280.
//
// Do NOT infer object identity here.
// Log exact caller, selector, and return only.
//
// Proven corridor calls:
//   0x7F478C -> LR 0x7F4790, selector 8
//   0x7F47E0 -> LR 0x7F47E4, selector 40
//   0x7F4810 -> LR 0x7F4814, selector 8
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P82ControlGetterHook) {
    static uint32_t Callback(
        void* base,
        uint32_t selector
    ) {
        const ptrdiff_t caller_off =
            MainRelativeOffset(
                reinterpret_cast<uintptr_t>(
                    __builtin_return_address(0)));

        const uint32_t ret =
            Orig(base, selector);

        const bool relevant =
            caller_off
                == kP82ControlReturn8AOffset
            ||
            caller_off
                == kP82ControlReturn40Offset
            ||
            caller_off
                == kP82ControlReturn8BOffset;

        if (relevant) {
            const uint32_t seq =
                g_p82_ctrl_seq.fetch_add(
                    1,
                    std::memory_order_relaxed);

            Logging.Log(
                "[NSC:P82A] CTRL_GET "
                "seq=%u base=%p "
                "selector=%u ret=%u "
                "caller_off=0x%lx",
                seq,
                base,
                selector,
                ret,
                static_cast<unsigned long>(
                    caller_off));
        }

        return ret;
    }
};


'''

cpp = cpp[:pos] + hooks + cpp[pos:]


# ============================================================
# INSTALLER
# ============================================================

installer_anchor = (
    "void InstallP80BDeepConditionTrace()"
)

pos = cpp.find(installer_anchor)

if pos < 0:
    raise SystemExit(
        "FATAL P80B installer anchor missing"
    )

installer = r'''
void InstallP82ADownstreamCorridorProbe() {
    // Keep the P81 OugiAwakening bridge fully active.
    InstallP81AOugiAwakeningPolicyBridge();

    static constexpr uint32_t
        kStateExpected[] = {
            0xA9BF4FFE,
            0xF9400008,
            0xF9402508,
            0xB94E5413,
            0xD63F0100,
            0x9403AC7D,
            0xB4000160,
            0xF9400008,
        };

    static constexpr uint32_t
        kMidExpected[] = {
            0xA9BC67FE,
            0xA9015FF8,
            0xA90257F6,
            0xA9034FF4,
            0xB000D7D7,
            0xF94262F7,
            0xF9400008,
            0xAA0003F3,
        };

    static constexpr uint32_t
        kMaskExpected[] = {
            0xB9459C08,
            0xB9440409,
            0x6A08013F,
            0x1A9F07E0,
            0xD65F03C0,
        };

    static constexpr uint32_t
        kPostExpected[] = {
            0xF81E0FFE,
            0xA9014FF4,
            0xF9400008,
            0x2A0103F4,
            0xAA0003F3,
            0xF946E508,
            0xD63F0100,
            0x34000320,
        };

    static constexpr uint32_t
        kControlExpected[] = {
            0xF81E0FFE,
            0xA9014FF4,
            0x2A0103F3,
            0xAA0003F4,
            0x71004C3F,
            0x54000161,
            0xB000CBE8,
            0xF9424508,
        };

    const bool ok_state =
        MatchWords(
            kP82StatePredicateOffset,
            kStateExpected);

    const bool ok_mid =
        MatchWords(
            kP82MidPredicateOffset,
            kMidExpected);

    const bool ok_mask =
        MatchWords(
            kP82MaskPredicateOffset,
            kMaskExpected);

    const bool ok_post =
        MatchWords(
            kP82PostGateOffset,
            kPostExpected);

    const bool ok_ctrl =
        MatchWords(
            kP82ControlGetterOffset,
            kControlExpected);

    if (!ok_state) {
        LogFingerprintFail(
            "P82_794EC8",
            kP82StatePredicateOffset);
    }

    if (!ok_mid) {
        LogFingerprintFail(
            "P82_64A030",
            kP82MidPredicateOffset);
    }

    if (!ok_mask) {
        LogFingerprintFail(
            "P82_7C5FFC",
            kP82MaskPredicateOffset);
    }

    if (!ok_post) {
        LogFingerprintFail(
            "P82_7D2DE4",
            kP82PostGateOffset);
    }

    if (!ok_ctrl) {
        LogFingerprintFail(
            "P82_7C6280",
            kP82ControlGetterOffset);
    }

    if (ok_state) {
        P82StatePredicateHook::
            InstallAtOffset(
                kP82StatePredicateOffset);
    }

    if (ok_mid) {
        P82MidPredicateHook::
            InstallAtOffset(
                kP82MidPredicateOffset);
    }

    if (ok_mask) {
        P82MaskPredicateHook::
            InstallAtOffset(
                kP82MaskPredicateOffset);
    }

    if (ok_post) {
        P82PostGateHook::
            InstallAtOffset(
                kP82PostGateOffset);
    }

    if (ok_ctrl) {
        P82ControlGetterHook::
            InstallAtOffset(
                kP82ControlGetterOffset);
    }

    Logging.Log(
        "[NSC:P82A] READY "
        "baseline_p81=1 "
        "state794ec8=%u "
        "mid64a030=%u "
        "mask7c5ffc=%u "
        "post7d2de4=%u "
        "ctrl7c6280=%u "
        "readonly=1 "
        "preserve_orig=1 "
        "no_f58_hook=1 "
        "no_force_return=1 "
        "no_force87=1 "
        "no_force700=1 "
        "no_char281_branch=1",
        ok_state ? 1u : 0u,
        ok_mid ? 1u : 0u,
        ok_mask ? 1u : 0u,
        ok_post ? 1u : 0u,
        ok_ctrl ? 1u : 0u);
}


'''

cpp = cpp[:pos] + installer + cpp[pos:]


# ============================================================
# HEADER
# ============================================================

p81_decl = (
    "void InstallP81AOugiAwakeningPolicyBridge();"
)

p82_decl = (
    "void InstallP82ADownstreamCorridorProbe();"
)

if p82_decl not in hpp:
    if p81_decl not in hpp:
        raise SystemExit(
            "FATAL P81 header anchor missing"
        )

    hpp = hpp.replace(
        p81_decl,
        p81_decl + "\n" + p82_decl,
        1,
    )


# ============================================================
# ACTIVE MAIN
# ============================================================

main = main.replace(
    "nsc::InstallP81AOugiAwakeningPolicyBridge();",
    "nsc::InstallP82ADownstreamCorridorProbe();",
    1,
)


CPP.write_text(
    cpp,
    encoding="utf-8"
)

HPP.write_text(
    hpp,
    encoding="utf-8"
)

MAIN.write_text(
    main,
    encoding="utf-8"
)

print("P82A_SOURCE_PATCH=PASS")
