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

if main.count(
    "nsc::InstallP83ASlot1928PolicyBridge();"
) != 1:
    raise SystemExit(
        "FATAL active main is not P83A"
    )

for token in (
    "void InstallP82ADownstreamCorridorProbe()",
    "P83Slot1928PolicyHook",
    "ReadActorIdentity",
    "MainRelativeOffset",
):
    if token not in cpp:
        raise SystemExit(
            "FATAL prerequisite missing: " + token
        )

for p in (CPP, HPP, MAIN):
    bak = p.with_suffix(
        p.suffix + ".pre_p84a"
    )
    if not bak.exists():
        shutil.copy2(p, bak)

anchor = (
    "std::atomic<uint32_t> "
    "g_p83_slot1928_seq{0};"
)

if anchor not in cpp:
    raise SystemExit(
        "FATAL P83 counter anchor missing"
    )

cpp = cpp.replace(
    anchor,
    anchor + r'''

// ============================================================================
// P84A — XA vs XXA intent discriminator.
//
// IMPORTANT:
// P83 behavior override is NOT installed.
//
// This build returns to P82 behavior and only observes the native eligibility
// path so ordinary jutsu is not converted into UJ by the diagnostic build.
// ============================================================================

constexpr ptrdiff_t kP84GlobalPredicateOffset =
    0x750170;
constexpr ptrdiff_t kP84GlobalPredicateReturnOffset =
    0x7D3508;

std::atomic<uint32_t> g_p84_global_seq{0};
std::atomic<uint32_t> g_p84_slot_seq{0};

''',
    1,
)

hook_anchor = (
    "HOOK_DEFINE_TRAMPOLINE(P80BContextHook)"
)

pos = cpp.find(hook_anchor)

if pos < 0:
    raise SystemExit("FATAL hook anchor missing")

hooks = r'''
// -----------------------------------------------------------------------------
// P84A — internal predicate called by 0x7D34E0 before E94==0x3F.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P84GlobalPredicateHook) {
    static uint32_t Callback(void* arg0) {
        const ptrdiff_t caller_off =
            MainRelativeOffset(
                reinterpret_cast<uintptr_t>(
                    __builtin_return_address(0)));

        const uint32_t ret = Orig(arg0);

        if (
            caller_off
            == kP84GlobalPredicateReturnOffset
        ) {
            const uint32_t seq =
                g_p84_global_seq.fetch_add(
                    1,
                    std::memory_order_relaxed);

            Logging.Log(
                "[NSC:P84A] H750170 "
                "seq=%u arg0=%p ret=%u "
                "caller_off=0x%lx",
                seq,
                arg0,
                ret,
                static_cast<unsigned long>(
                    caller_off));
        }

        return ret;
    }
};


// -----------------------------------------------------------------------------
// P84A — read-only observation of the +0x1928 target itself.
//
// NO override.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P84Slot1928ReadOnlyHook) {
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

        if (!valid) {
            return native_ret;
        }

        const auto* b =
            reinterpret_cast<
                const volatile uint8_t*>(
                actor);

        const uint32_t e60 =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0xE60);

        const uint32_t e94 =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0xE94);

        const uint32_t e98 =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0xE98);

        const uint32_t e9c =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0xE9C);

        const uint32_t ea0 =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0xEA0);

        const uint32_t gate10f40 =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0x10F40);

        const uint32_t state106f4 =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0x106F4);

        const uint8_t flags11710 =
            *reinterpret_cast<
                const volatile uint8_t*>(
                b + 0x11710);

        const uint32_t statebdc8 =
            *reinterpret_cast<
                const volatile uint32_t*>(
                b + 0xBDC8);

        const uint32_t seq =
            g_p84_slot_seq.fetch_add(
                1,
                std::memory_order_relaxed);

        Logging.Log(
            "[NSC:P84A] SLOT1928_NATIVE "
            "seq=%u actor=%p "
            "side=%u char=%u mode=%u "
            "native=%u "
            "e60=%u e94=%u e98=%u "
            "e9c=%u ea0=%u "
            "gate10f40=%u "
            "state106f4=%u "
            "flags11710=0x%02x "
            "statebdc8=%u "
            "caller_off=0x%lx",
            seq,
            actor,
            side,
            char_id,
            mode,
            native_ret,
            e60,
            e94,
            e98,
            e9c,
            ea0,
            gate10f40,
            static_cast<unsigned>(
                state106f4),
            static_cast<unsigned>(
                flags11710),
            static_cast<unsigned>(
                statebdc8),
            static_cast<unsigned long>(
                caller_off));

        return native_ret;
    }
};


'''

cpp = cpp[:pos] + hooks + cpp[pos:]

installer_anchor = (
    "void InstallP80BDeepConditionTrace()"
)

pos = cpp.find(installer_anchor)

if pos < 0:
    raise SystemExit(
        "FATAL installer anchor missing"
    )

installer = r'''
void InstallP84AIntentDiscriminator() {
    // P83 policy intentionally NOT installed.
    // Return to P82 read-only downstream baseline.
    InstallP82ADownstreamCorridorProbe();

    static constexpr uint32_t
        kGlobalExpected[] = {
            0xB000CFE8,
            0xF9404108,
            0xF9400109,
            0xB4000149,
            0x91002128,
            0xF9400929,
            0xEB08013F,
            0x540000C0,
        };

    static constexpr uint32_t
        kSlotExpected[] = {
            0xF81D0FFE,
            0xA90157F6,
            0xA9024FF4,
            0x5281E808,
            0x72A00028,
            0xB8686808,
            0x34000328,
            0x2A0103F4,
        };

    const bool ok_global =
        MatchWords(
            kP84GlobalPredicateOffset,
            kGlobalExpected);

    const bool ok_slot =
        MatchWords(
            kP83Slot1928TargetOffset,
            kSlotExpected);

    if (!ok_global) {
        LogFingerprintFail(
            "P84_750170",
            kP84GlobalPredicateOffset);
    }

    if (!ok_slot) {
        LogFingerprintFail(
            "P84_SLOT1928",
            kP83Slot1928TargetOffset);
    }

    if (ok_global) {
        P84GlobalPredicateHook::
            InstallAtOffset(
                kP84GlobalPredicateOffset);
    }

    if (ok_slot) {
        P84Slot1928ReadOnlyHook::
            InstallAtOffset(
                kP83Slot1928TargetOffset);
    }

    Logging.Log(
        "[NSC:P84A] READY "
        "baseline_p82=1 "
        "p83_policy_installed=0 "
        "global750170=%u "
        "slot1928_readonly=%u "
        "xa_xxa_compare=1 "
        "readonly=1 "
        "preserve_orig=1 "
        "no_force_return=1 "
        "no_force87=1 "
        "no_force700=1 "
        "no_char281_branch=1",
        ok_global ? 1u : 0u,
        ok_slot ? 1u : 0u);
}


'''

cpp = cpp[:pos] + installer + cpp[pos:]

p83_decl = (
    "void InstallP83ASlot1928PolicyBridge();"
)

p84_decl = (
    "void InstallP84AIntentDiscriminator();"
)

if p84_decl not in hpp:
    if p83_decl not in hpp:
        raise SystemExit(
            "FATAL P83 declaration missing"
        )

    hpp = hpp.replace(
        p83_decl,
        p83_decl + "\n" + p84_decl,
        1,
    )

main = main.replace(
    "nsc::InstallP83ASlot1928PolicyBridge();",
    "nsc::InstallP84AIntentDiscriminator();",
    1,
)

CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P84A_SOURCE_PATCH=PASS")
