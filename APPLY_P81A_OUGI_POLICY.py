#!/usr/bin/env python3

from pathlib import Path
import re
import shutil

ROOT = Path("/storage/emulated/0/Downloads")

CPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN = ROOT / "overlay/source/program/main.cpp"
DATA = ROOT / "overlay/source/program/p81_ougi_awake_ids.hpp"

for p in (CPP, HPP, MAIN, DATA):
    if not p.is_file():
        raise SystemExit("FATAL missing: " + str(p))

cpp = CPP.read_text(encoding="utf-8")
hpp = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

if main.count(
    "nsc::InstallP80BDeepConditionTrace();"
) != 1:
    raise SystemExit(
        "FATAL: active main is not clean P80B"
    )

if "P81OugiAwakeningPolicyHook" in cpp:
    raise SystemExit(
        "FATAL: P81 source already partly present"
    )

for x in (
    "void InstallP80BDeepConditionTrace()",
    "void InstallP77AAcceptanceProbe()",
    "HOOK_DEFINE_TRAMPOLINE(P80BContextHook)",
    "P64QuerySemanticUltimateJutsu",
    "ReadActorIdentity",
    "MainRelativeOffset",
    "MatchWords",
    "LogFingerprintFail",
):
    if x not in cpp:
        raise SystemExit(
            "FATAL prerequisite missing: " + x
        )

for p in (CPP, HPP, MAIN):
    b = p.with_suffix(p.suffix + ".pre_p81a")

    if not b.exists():
        shutil.copy2(p, b)


# ------------------------------------------------------------
# include generated membership data
# ------------------------------------------------------------

inc = '#include "p81_ougi_awake_ids.hpp"'

if inc not in cpp:
    anchor = '#include "nsc_cpk_bridge.hpp"'

    if anchor not in cpp:
        raise SystemExit(
            "FATAL include anchor missing"
        )

    cpp = cpp.replace(
        anchor,
        anchor + "\n" + inc,
        1,
    )


# ------------------------------------------------------------
# constants
# ------------------------------------------------------------

anchor = re.search(
    r'constexpr\s+ptrdiff_t\s+'
    r'kP80BActorCollectionOffset'
    r'\s*=\s*0x10F80\s*;',
    cpp,
)

if not anchor:
    raise SystemExit(
        "FATAL P80B constant anchor missing"
    )

block = r'''

// P81A — data-driven OugiAwakening policy bridge.
//
// Exact UJ decision:
//   0x7F4588 BLR virtual+0x1288
//   LR = 0x7F458C
//
// Resolved vfunc for proven actor vtable:
//   main+0x7EAC34
//
// Native result is always evaluated first.
constexpr ptrdiff_t kP81UjPolicyParentOffset =
    0x7EAC34;

constexpr ptrdiff_t kP81UjPolicyCallerReturnOffset =
    0x7F458C;

std::atomic<uint32_t> g_p81_policy_seq{0};

'''

cpp = (
    cpp[:anchor.end()]
    + block
    + cpp[anchor.end():]
)


# ------------------------------------------------------------
# hook
# ------------------------------------------------------------

hook_anchor = (
    "HOOK_DEFINE_TRAMPOLINE(P80BContextHook)"
)

pos = cpp.find(hook_anchor)

if pos < 0:
    raise SystemExit(
        "FATAL P80B hook anchor missing"
    )

hook = r'''
HOOK_DEFINE_TRAMPOLINE(P81OugiAwakeningPolicyHook) {
    static uint32_t Callback(void* actor) {
        const uintptr_t caller_lr =
            reinterpret_cast<uintptr_t>(
                __builtin_return_address(0));

        const ptrdiff_t caller_off =
            MainRelativeOffset(caller_lr);

        // Native result FIRST.
        const uint32_t native_ret =
            Orig(actor);

        // Exact UJ-decision caller only.
        if (
            caller_off
            != kP81UjPolicyCallerReturnOffset
        ) {
            return native_ret;
        }

        uint32_t side =
            0xFFFFFFFFu;

        uint32_t char_id =
            0xFFFFFFFFu;

        const bool valid =
            ReadActorIdentity(
                actor,
                side,
                char_id);

        const bool semantic =
            actor
            && P64QuerySemanticUltimateJutsu(
                actor);

        const bool member =
            valid
            && p81_data::
                ContainsOugiAwakeningId(
                    char_id);

        uint32_t e94 =
            0xFFFFFFFFu;

        uint32_t e9c =
            0xFFFFFFFFu;

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
        }

        // +0x1288:
        //
        // nonzero -> ALT corridor
        // zero    -> native UJ corridor
        //
        // Membership grants only the OugiAwakening
        // exception. Nothing downstream is forced.
        const bool allow =
            native_ret != 0
            && semantic
            && member;

        const uint32_t policy_ret =
            allow
            ? 0u
            : native_ret;

        const uint32_t seq =
            g_p81_policy_seq.fetch_add(
                1,
                std::memory_order_relaxed);

        Logging.Log(
            "[NSC:P81A] POLICY "
            "seq=%u actor=%p "
            "valid=%u side=%u char=%u "
            "member=%u semantic=%u "
            "native=%u policy=%u allow=%u "
            "caller_off=0x%lx "
            "e94=%u e9c=%u",
            seq,
            actor,
            valid ? 1u : 0u,
            side,
            char_id,
            member ? 1u : 0u,
            semantic ? 1u : 0u,
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


# ------------------------------------------------------------
# installer
# ------------------------------------------------------------

installer_anchor = (
    "void InstallP80BDeepConditionTrace()"
)

pos = cpp.find(installer_anchor)

if pos < 0:
    raise SystemExit(
        "FATAL P80B installer anchor missing"
    )

installer = r'''
void InstallP81AOugiAwakeningPolicyBridge() {
    // P50/P67 compatibility + P77 native UJ acceptance.
    InstallP77AAcceptanceProbe();

    static constexpr uint32_t
        kParentExpected[] = {
            0xA9BF4FFE,
            0xAA0003F3,
            0x9400000D,
            0x34000080,
            0x52800020,
            0xA8C14FFE,
            0xD65F03C0,
            0xF9400268,
        };

    bool ok = true;

    if (!MatchWords(
            kP81UjPolicyParentOffset,
            kParentExpected)) {
        LogFingerprintFail(
            "P81_UJ_POLICY_PARENT",
            kP81UjPolicyParentOffset);

        ok = false;
    }

    if (ok) {
        P81OugiAwakeningPolicyHook::
            InstallAtOffset(
                kP81UjPolicyParentOffset);
    }

    Logging.Log(
        "[NSC:P81A] READY "
        "baseline_p77=1 "
        "probe_ok=%u "
        "parent=0x%lx "
        "caller_return=0x%lx "
        "ougi_ids=%lu "
        "ougi_sha=%s "
        "exact_uj_call_only=1 "
        "native_first=1 "
        "p80_query_installed=0 "
        "p79_probe_installed=0 "
        "p78_probe_installed=0 "
        "no_condition_mutation=1 "
        "no_force87=1 "
        "no_force700=1 "
        "no_char281_branch=1",
        ok ? 1u : 0u,
        static_cast<unsigned long>(
            kP81UjPolicyParentOffset),
        static_cast<unsigned long>(
            kP81UjPolicyCallerReturnOffset),
        static_cast<unsigned long>(
            p81_data::
                kOugiAwakeningIdCount),
        p81_data::
            kOugiAwakeningSourceSha256);
}


'''

cpp = cpp[:pos] + installer + cpp[pos:]


# ------------------------------------------------------------
# header
# ------------------------------------------------------------

old_decl = (
    "void InstallP80BDeepConditionTrace();"
)

new_decl = (
    "void InstallP81AOugiAwakeningPolicyBridge();"
)

if new_decl not in hpp:
    if old_decl not in hpp:
        raise SystemExit(
            "FATAL P80B header anchor missing"
        )

    hpp = hpp.replace(
        old_decl,
        old_decl + "\n" + new_decl,
        1,
    )


# ------------------------------------------------------------
# active main
# ------------------------------------------------------------

main = main.replace(
    "nsc::InstallP80BDeepConditionTrace();",
    "nsc::InstallP81AOugiAwakeningPolicyBridge();",
    1,
)


CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P81A_SOURCE_PATCH=PASS")
