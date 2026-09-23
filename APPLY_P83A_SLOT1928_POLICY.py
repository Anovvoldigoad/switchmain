#!/usr/bin/env python3

from pathlib import Path
import shutil

ROOT = Path("/storage/emulated/0/Downloads")

CPP = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN = ROOT / "overlay/source/program/main.cpp"

for p in (CPP, HPP, MAIN):
    if not p.is_file():
        raise SystemExit("FATAL missing: " + str(p))

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")


# ============================================================
# BASELINE
# ============================================================

if main.count(
    "nsc::InstallP82ADownstreamCorridorProbe();"
) != 1:
    raise SystemExit(
        "FATAL active main is not clean P82A"
    )

if "InstallP83ASlot1928PolicyBridge" in main:
    raise SystemExit(
        "FATAL P83 already active"
    )

required = (
    "void InstallP82ADownstreamCorridorProbe()",
    "P64QuerySemanticUltimateJutsu",
    "ContainsOugiAwakeningId",
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
# BACKUPS
# ============================================================

for p in (CPP, HPP, MAIN):
    bak = p.with_suffix(
        p.suffix + ".pre_p83a"
    )

    if not bak.exists():
        shutil.copy2(p, bak)


# ============================================================
# CONSTANTS / COUNTER
# ============================================================

anchor = (
    "std::atomic<uint32_t> "
    "g_p82_ctrl_seq{0};"
)

if anchor not in cpp:
    raise SystemExit(
        "FATAL P82 counter anchor missing"
    )

block = r'''

// ============================================================================
// P83A — exact +0x1928 UJ-corridor compatibility policy.
//
// P82 runtime:
//   P81 allow=1
//   P77 ret=1
//   0x794EC8 ret=0
//   downstream 0x7D2DE4 never reached
//   action445 wins.
//
// Static relocation proof for the observed custom actor vtable:
//   vtable RVA            = 0x201BF58
//   vtable + 0x1928       = 0x201D880
//   RELA addend            = 0x7D34E0
//
// Native callsite:
//   0x7F4744 LDR X8,[X8,#0x1928]
//   0x7F4748 BLR X8
//   0x7F474C CBZ W0,0x7F4590
//
// Policy is native-first and exact-call-only.
// ============================================================================

constexpr ptrdiff_t kP83Slot1928TargetOffset =
    0x7D34E0;

constexpr ptrdiff_t kP83Slot1928CallerReturnOffset =
    0x7F474C;

std::atomic<uint32_t> g_p83_slot1928_seq{0};

'''

cpp = cpp.replace(
    anchor,
    anchor + block,
    1,
)


# ============================================================
# HOOK
# ============================================================

hook_anchor = (
    "HOOK_DEFINE_TRAMPOLINE(P80BContextHook)"
)

pos = cpp.find(hook_anchor)

if pos < 0:
    raise SystemExit(
        "FATAL hook anchor missing"
    )

hook = r'''
// -----------------------------------------------------------------------------
// P83A — +0x1928 exact-call policy bridge.
//
// Native first.
// Only changes false -> true when:
//
//   exact UJ-corridor caller
//   AND semantic UJ is active
//   AND char belongs to generated OugiAwakening membership
//
// No direct action/state mutation.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P83Slot1928PolicyHook) {
    static uint32_t Callback(
        void* actor,
        uint32_t mode
    ) {
        const ptrdiff_t caller_off =
            MainRelativeOffset(
                reinterpret_cast<uintptr_t>(
                    __builtin_return_address(0)));

        const uint32_t native_ret =
            Orig(actor, mode);

        if (
            caller_off
            != kP83Slot1928CallerReturnOffset
        ) {
            return native_ret;
        }

        uint32_t side = 0xFFFFFFFFu;
        uint32_t char_id = 0xFFFFFFFFu;

        const bool valid =
            ReadActorIdentity(
                actor,
                side,
                char_id);

        const bool semantic =
            valid
            && P64QuerySemanticUltimateJutsu(
                actor);

        const bool member =
            valid
            && p81_data::
                ContainsOugiAwakeningId(
                    char_id);

        uint32_t e94 = 0xFFFFFFFFu;
        uint32_t e9c = 0xFFFFFFFFu;
        uint32_t gate_10f40 = 0xFFFFFFFFu;

        if (actor) {
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

            gate_10f40 =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    b + 0x10F40);
        }

        const bool allow =
            valid
            && semantic
            && member
            && native_ret == 0;

        const uint32_t policy_ret =
            allow
                ? 1u
                : native_ret;

        const uint32_t seq =
            g_p83_slot1928_seq.fetch_add(
                1,
                std::memory_order_relaxed);

        Logging.Log(
            "[NSC:P83A] SLOT1928_POLICY "
            "seq=%u actor=%p "
            "valid=%u side=%u char=%u "
            "mode=%u member=%u semantic=%u "
            "gate10f40=%u "
            "native=%u policy=%u allow=%u "
            "caller_off=0x%lx "
            "e94=%u e9c=%u",
            seq,
            actor,
            valid ? 1u : 0u,
            side,
            char_id,
            mode,
            member ? 1u : 0u,
            semantic ? 1u : 0u,
            gate_10f40,
            native_ret,
            policy_ret,
            allow ? 1u : 0u,
            static_cast<unsigned long>(
                caller_off),
            e94,
            e9c);

        return policy_ret;
    }
};


'''

cpp = cpp[:pos] + hook + cpp[pos:]


# ============================================================
# INSTALLER
# ============================================================

installer_anchor = (
    "void InstallP80BDeepConditionTrace()"
)

pos = cpp.find(installer_anchor)

if pos < 0:
    raise SystemExit(
        "FATAL installer anchor missing"
    )

installer = r'''
void InstallP83ASlot1928PolicyBridge() {
    // Preserve P81 policy + entire P82 downstream trace.
    InstallP82ADownstreamCorridorProbe();

    static constexpr uint32_t
        kExpected[] = {
            0xF81D0FFE,
            0xA90157F6,
            0xA9024FF4,
            0x5281E808,
            0x72A00028,
            0xB8686808,
            0x34000328,
            0x2A0103F4,
        };

    const bool ok =
        MatchWords(
            kP83Slot1928TargetOffset,
            kExpected);

    if (!ok) {
        LogFingerprintFail(
            "P83_SLOT1928",
            kP83Slot1928TargetOffset);
    }

    if (ok) {
        P83Slot1928PolicyHook::
            InstallAtOffset(
                kP83Slot1928TargetOffset);
    }

    Logging.Log(
        "[NSC:P83A] READY "
        "baseline_p82=1 "
        "slot1928=0x%lx "
        "caller_return=0x%lx "
        "probe_ok=%u "
        "native_first=1 "
        "exact_uj_call_only=1 "
        "ougi_membership=1 "
        "semantic_required=1 "
        "no_inline_vcall_hook=1 "
        "no_force87=1 "
        "no_force700=1 "
        "no_action445_rewrite=1 "
        "no_char281_branch=1",
        static_cast<unsigned long>(
            kP83Slot1928TargetOffset),
        static_cast<unsigned long>(
            kP83Slot1928CallerReturnOffset),
        ok ? 1u : 0u);
}


'''

cpp = cpp[:pos] + installer + cpp[pos:]


# ============================================================
# HEADER
# ============================================================

p82 = (
    "void InstallP82ADownstreamCorridorProbe();"
)

p83 = (
    "void InstallP83ASlot1928PolicyBridge();"
)

if p83 not in hpp:
    if p82 not in hpp:
        raise SystemExit(
            "FATAL P82 declaration missing"
        )

    hpp = hpp.replace(
        p82,
        p82 + "\n" + p83,
        1,
    )


# ============================================================
# ACTIVE MAIN
# ============================================================

main = main.replace(
    "nsc::InstallP82ADownstreamCorridorProbe();",
    "nsc::InstallP83ASlot1928PolicyBridge();",
    1,
)


CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P83A_SOURCE_PATCH=PASS")
