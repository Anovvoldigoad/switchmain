#!/usr/bin/env python3

from pathlib import Path
import re
import shutil

ROOT = Path("/storage/emulated/0/Downloads")

CPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.cpp"
HPP  = ROOT / "overlay/source/program/nsc_cpk_bridge.hpp"
MAIN = ROOT / "overlay/source/program/main.cpp"

for p in (CPP, HPP, MAIN):
    if not p.is_file():
        raise SystemExit("FATAL missing: " + str(p))

cpp  = CPP.read_text(encoding="utf-8")
hpp  = HPP.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")

if "[NSC:P80B]" in cpp:
    raise SystemExit("FATAL: P80B already present")

for needle in (
    "void InstallP77AAcceptanceProbe()",
    "HOOK_DEFINE_TRAMPOLINE(P79PredicateBHook)",
):
    if needle not in cpp:
        raise SystemExit(
            "FATAL prerequisite missing: " + needle
        )

active_candidates = [
    "nsc::InstallP79ADualSubpredicateProbe();",
    "nsc::InstallP80AExactConditionMatchProbe();",
]

active_found = [
    x for x in active_candidates
    if x in main
]

if len(active_found) != 1:
    raise SystemExit(
        "FATAL: expected exactly one P79/P80A active main call, got "
        + repr(active_found)
    )

for p in (CPP, HPP, MAIN):
    bak = p.with_suffix(p.suffix + ".pre_p80b")

    if not bak.exists():
        shutil.copy2(p, bak)


# ================================================================
# CONSTANTS
# ================================================================

anchor_patterns = [
    r'''
    constexpr\s+ptrdiff_t\s+
    kP79PredicateBCallerReturnOffset\s*=
    \s*0x7EAC60\s*;
    ''',
    r'''
    constexpr\s+ptrdiff_t\s+
    kP80ConditionMatchCallerReturnOffset\s*=
    \s*0x7EAD08\s*;
    ''',
]

m = None

for pat in anchor_patterns:
    hits = list(re.finditer(pat, cpp, re.X))

    if hits:
        m = hits[-1]
        break

if m is None:
    raise SystemExit(
        "FATAL: no safe P79/P80 constant anchor"
    )

constants = r'''

// ============================================================================
// P80B DEEP CONDITION TRACE
//
// Predicate B:
//   main+0x7EACF0
//   parent LR main+0x7EAC60
//
// B calls:
//   main+0x7EAD04 BL main+0x777388
//   return LR main+0x7EAD08
//
// 0x777388:
//   iterates actor condition collection,
//   entry+0x08 -> condition index,
//   0x754A80(index) -> native condition descriptor,
//   descriptor+0x0C compared against wanted_type.
// ============================================================================

constexpr ptrdiff_t kP80BPredicateBOffset =
    0x7EACF0;

constexpr ptrdiff_t kP80BPredicateBReturnOffset =
    0x7EAC60;

constexpr ptrdiff_t kP80BConditionQueryOffset =
    0x777388;

constexpr ptrdiff_t kP80BConditionQueryReturnOffset =
    0x7EAD08;

constexpr ptrdiff_t kP80BConditionGetterOffset =
    0x754A80;

constexpr ptrdiff_t kP80BActorCollectionOffset =
    0x10F80;

std::atomic<uintptr_t> g_p80b_actor{0};
std::atomic<uintptr_t> g_p80b_collection{0};

std::atomic<uint32_t> g_p80b_query_seq{0};
std::atomic<uint32_t> g_p80b_dump_seq{0};

std::atomic<uint64_t> g_p80b_last_dump_key{
    0xFFFFFFFFFFFFFFFFull
};

'''

cpp = cpp[:m.end()] + constants + cpp[m.end():]


# ================================================================
# HOOKS
# ================================================================

hook_anchor = "HOOK_DEFINE_TRAMPOLINE(P79PredicateAHook)"

idx = cpp.find(hook_anchor)

if idx < 0:
    raise SystemExit(
        "FATAL: P79 hook anchor missing"
    )

hooks = r'''
// -----------------------------------------------------------------------------
// P80B Predicate-B context hook.
//
// No behavior change.
// No per-frame B-return logging here.
// It only exposes actor + collection to the nested 0x777388 query.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P80BContextHook) {
    static uint32_t Callback(void* actor) {
        const uintptr_t caller_lr =
            reinterpret_cast<uintptr_t>(
                __builtin_return_address(0));

        const ptrdiff_t caller_off =
            MainRelativeOffset(caller_lr);

        if (
            caller_off
            != kP80BPredicateBReturnOffset
        ) {
            return Orig(actor);
        }

        if (!P64QuerySemanticUltimateJutsu(actor)) {
            return Orig(actor);
        }

        uintptr_t collection = 0;

        if (actor) {
            const auto* b =
                reinterpret_cast<
                    const volatile uint8_t*>(
                    actor);

            collection =
                reinterpret_cast<uintptr_t>(
                    *reinterpret_cast<
                        void* const volatile*>(
                        b
                        + kP80BActorCollectionOffset));
        }

        g_p80b_actor.store(
            reinterpret_cast<uintptr_t>(actor),
            std::memory_order_release);

        g_p80b_collection.store(
            collection,
            std::memory_order_release);

        const uint32_t ret =
            Orig(actor);

        uintptr_t expected_collection =
            collection;

        g_p80b_collection.compare_exchange_strong(
            expected_collection,
            0,
            std::memory_order_acq_rel);

        uintptr_t expected_actor =
            reinterpret_cast<uintptr_t>(actor);

        g_p80b_actor.compare_exchange_strong(
            expected_actor,
            0,
            std::memory_order_acq_rel);

        return ret;
    }
};


// -----------------------------------------------------------------------------
// P80B deep condition query.
//
// Native:
//   void* 0x777388(void* collection, uint32_t wanted_type)
//
// Exact Predicate-B caller:
//   LR = main+0x7EAD08
//
// Result pointer is the matching collection payload.
// payload+0x08 is the condition index.
//
// This probe:
//   1. preserves Orig result;
//   2. logs EVERY focused B-query result;
//   3. dumps the entire native collection on first unique
//      (wanted_type, matched_index) state;
//   4. resolves every candidate through native condition getter 0x754A80;
//   5. logs descriptor fields used by the classifier.
//
// No result is replaced.
// -----------------------------------------------------------------------------

HOOK_DEFINE_TRAMPOLINE(P80BConditionQueryHook) {
    static void* Callback(
        void* collection,
        uint32_t wanted_type) {

        const uintptr_t caller_lr =
            reinterpret_cast<uintptr_t>(
                __builtin_return_address(0));

        const ptrdiff_t caller_off =
            MainRelativeOffset(caller_lr);

        if (
            caller_off
            != kP80BConditionQueryReturnOffset
        ) {
            return Orig(
                collection,
                wanted_type);
        }

        const uintptr_t active_actor =
            g_p80b_actor.load(
                std::memory_order_acquire);

        const uintptr_t active_collection =
            g_p80b_collection.load(
                std::memory_order_acquire);

        const bool focused =
            active_actor != 0
            && active_collection != 0
            && active_collection
                == reinterpret_cast<uintptr_t>(
                    collection);

        void* const result =
            Orig(
                collection,
                wanted_type);

        if (!focused) {
            return result;
        }

        uint32_t matched_index =
            0xFFFFFFFFu;

        if (result) {
            const auto* entry =
                reinterpret_cast<
                    const volatile uint8_t*>(
                    result);

            matched_index =
                *reinterpret_cast<
                    const volatile uint32_t*>(
                    entry + 0x08);
        }

        void* actor =
            reinterpret_cast<void*>(
                active_actor);

        uint32_t side =
            0xFFFFFFFFu;

        uint32_t char_id =
            0xFFFFFFFFu;

        const bool valid =
            ReadActorIdentity(
                actor,
                side,
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

        const uint32_t query_seq =
            g_p80b_query_seq.fetch_add(
                1,
                std::memory_order_relaxed);

        // Keep every query so we can correlate directly against
        // requested445 / requested700.
        Logging.Log(
            "[NSC:P80B] QUERY "
            "seq=%u "
            "actor=%p valid=%u "
            "side=%u char=%u "
            "collection=%p "
            "wanted=%u "
            "result=%p "
            "matched_index=%u "
            "caller_off=0x%lx "
            "semantic=%u "
            "e94=%u "
            "e9c=%u",
            query_seq,
            actor,
            valid ? 1u : 0u,
            side,
            char_id,
            collection,
            wanted_type,
            result,
            matched_index,
            static_cast<unsigned long>(
                caller_off),
            P64QuerySemanticUltimateJutsu(actor)
                ? 1u
                : 0u,
            e94,
            e9c);

        // Full collection snapshot whenever classification state changes.
        const uint64_t dump_key =
            (
                static_cast<uint64_t>(
                    wanted_type)
                << 32
            )
            | matched_index;

        const uint64_t previous_key =
            g_p80b_last_dump_key.exchange(
                dump_key,
                std::memory_order_acq_rel);

        if (previous_key == dump_key) {
            return result;
        }

        const uint32_t dump_seq =
            g_p80b_dump_seq.fetch_add(
                1,
                std::memory_order_relaxed);

        Logging.Log(
            "[NSC:P80B] DUMP_BEGIN "
            "dump=%u "
            "actor=%p "
            "collection=%p "
            "wanted=%u "
            "native_result=%p "
            "native_matched_index=%u",
            dump_seq,
            actor,
            collection,
            wanted_type,
            result,
            matched_index);

        using ConditionGetterFn =
            void* (*)(uint32_t);

        const uintptr_t main_base =
            exl::util::modules::GetTargetStart();

        const auto condition_getter =
            reinterpret_cast<
                ConditionGetterFn>(
                main_base
                + kP80BConditionGetterOffset);

        uint32_t candidate_count = 0;
        bool truncated = false;

        if (collection) {
            const auto* c =
                reinterpret_cast<
                    const volatile uint8_t*>(
                    collection);

            const uintptr_t tree =
                reinterpret_cast<uintptr_t>(
                    *reinterpret_cast<
                        void* const volatile*>(
                        c + 0x18));

            if (tree) {
                const uintptr_t end_node =
                    tree + 0x20;

                uintptr_t node =
                    reinterpret_cast<uintptr_t>(
                        *reinterpret_cast<
                            void* const volatile*>(
                            reinterpret_cast<
                                const volatile uint8_t*>(
                                tree)
                            + 0x28));

                // Diagnostic hard bound against corrupted/cyclic trees.
                for (
                    uint32_t ordinal = 0;
                    ordinal < 256;
                    ++ordinal
                ) {
                    if (
                        node == 0
                        || node == end_node
                    ) {
                        break;
                    }

                    const auto* nb =
                        reinterpret_cast<
                            const volatile uint8_t*>(
                            node);

                    const uintptr_t payload =
                        reinterpret_cast<uintptr_t>(
                            *reinterpret_cast<
                                void* const volatile*>(
                                nb + 0x10));

                    uintptr_t next_node =
                        reinterpret_cast<uintptr_t>(
                            *reinterpret_cast<
                                void* const volatile*>(
                                nb + 0x08));

                    if (payload) {
                        const auto* eb =
                            reinterpret_cast<
                                const volatile uint8_t*>(
                                payload);

                        const uint32_t index =
                            *reinterpret_cast<
                                const volatile uint32_t*>(
                                eb + 0x08);

                        void* descriptor =
                            condition_getter(index);

                        uintptr_t name_ptr = 0;

                        uint32_t after_index =
                            0xFFFFFFFFu;

                        uint32_t field_c =
                            0xFFFFFFFFu;

                        uint32_t field_10 =
                            0xFFFFFFFFu;

                        uint32_t field_14 =
                            0xFFFFFFFFu;

                        uint32_t field_18 =
                            0xFFFFFFFFu;

                        if (descriptor) {
                            const auto* db =
                                reinterpret_cast<
                                    const volatile uint8_t*>(
                                    descriptor);

                            name_ptr =
                                reinterpret_cast<uintptr_t>(
                                    *reinterpret_cast<
                                        void* const volatile*>(
                                        db + 0x00));

                            after_index =
                                *reinterpret_cast<
                                    const volatile uint32_t*>(
                                    db + 0x08);

                            field_c =
                                *reinterpret_cast<
                                    const volatile uint32_t*>(
                                    db + 0x0C);

                            field_10 =
                                *reinterpret_cast<
                                    const volatile uint32_t*>(
                                    db + 0x10);

                            field_14 =
                                *reinterpret_cast<
                                    const volatile uint32_t*>(
                                    db + 0x14);

                            field_18 =
                                *reinterpret_cast<
                                    const volatile uint32_t*>(
                                    db + 0x18);
                        }

                        const bool type_match =
                            descriptor
                            && field_c
                                == wanted_type;

                        const bool native_return =
                            result
                            && payload
                                == reinterpret_cast<uintptr_t>(
                                    result);

                        Logging.Log(
                            "[NSC:P80B] CAND "
                            "dump=%u "
                            "ord=%u "
                            "node=%p "
                            "entry=%p "
                            "index=%u "
                            "desc=%p "
                            "name_ptr=%p "
                            "after=%u "
                            "f0c=%u "
                            "f10=%u "
                            "f14=%u "
                            "f18=%u "
                            "wanted=%u "
                            "type_match=%u "
                            "native_return=%u",
                            dump_seq,
                            ordinal,
                            reinterpret_cast<void*>(
                                node),
                            reinterpret_cast<void*>(
                                payload),
                            index,
                            descriptor,
                            reinterpret_cast<void*>(
                                name_ptr),
                            after_index,
                            field_c,
                            field_10,
                            field_14,
                            field_18,
                            wanted_type,
                            type_match ? 1u : 0u,
                            native_return ? 1u : 0u);

                        ++candidate_count;
                    }

                    if (next_node == node) {
                        truncated = true;
                        break;
                    }

                    node = next_node;

                    if (ordinal == 255) {
                        truncated = true;
                    }
                }
            }
        }

        Logging.Log(
            "[NSC:P80B] DUMP_END "
            "dump=%u "
            "candidates=%u "
            "truncated=%u "
            "wanted=%u "
            "native_matched_index=%u",
            dump_seq,
            candidate_count,
            truncated ? 1u : 0u,
            wanted_type,
            matched_index);

        return result;
    }
};


'''

cpp = cpp[:idx] + hooks + cpp[idx:]


# ================================================================
# INSTALLER
# ================================================================

namespace_end = "\n} // namespace nsc"
idx = cpp.rfind(namespace_end)

if idx < 0:
    raise SystemExit(
        "FATAL namespace end missing"
    )

installer = r'''

void InstallP80BDeepConditionTrace() {
    // P67/P50 behavior + semantic producer + P77 UJ negative control.
    InstallP77AAcceptanceProbe();

    // main+0x7EACF0
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

    // main+0x777388
    static constexpr uint32_t kQueryExpected[] = {
        0xF81D0FFE,
        0xA90157F6,
        0xA9024FF4,
        0xF9400C08,
        0x91008109,
        0xF9401516,
        0xEB0902DF,
        0x54000240,
    };

    bool ok = true;

    if (!MatchWords(
            kP80BPredicateBOffset,
            kBExpected)) {
        LogFingerprintFail(
            "P80B_CONTEXT",
            kP80BPredicateBOffset);

        ok = false;
    }

    if (!MatchWords(
            kP80BConditionQueryOffset,
            kQueryExpected)) {
        LogFingerprintFail(
            "P80B_QUERY",
            kP80BConditionQueryOffset);

        ok = false;
    }

    if (ok) {
        P80BContextHook::InstallAtOffset(
            kP80BPredicateBOffset);

        P80BConditionQueryHook::InstallAtOffset(
            kP80BConditionQueryOffset);
    }

    Logging.Log(
        "[NSC:P80B] READY "
        "baseline_p77=1 "
        "probe_ok=%u "
        "b=0x%lx "
        "b_return=0x%lx "
        "query=0x%lx "
        "query_return=0x%lx "
        "getter=0x%lx "
        "collection_off=0x%lx "
        "query_log_all=1 "
        "candidate_snapshot_on_change=1 "
        "candidate_cap=256 "
        "p79_hot_probe_installed=0 "
        "p78_alt_probe_installed=0 "
        "readonly=1 "
        "preserve_orig=1 "
        "no_force_return=1 "
        "no_char281_branch=1",
        ok ? 1u : 0u,
        static_cast<unsigned long>(
            kP80BPredicateBOffset),
        static_cast<unsigned long>(
            kP80BPredicateBReturnOffset),
        static_cast<unsigned long>(
            kP80BConditionQueryOffset),
        static_cast<unsigned long>(
            kP80BConditionQueryReturnOffset),
        static_cast<unsigned long>(
            kP80BConditionGetterOffset),
        static_cast<unsigned long>(
            kP80BActorCollectionOffset));
}

'''

cpp = cpp[:idx] + installer + cpp[idx:]


# ================================================================
# HEADER
# ================================================================

if (
    "void InstallP80BDeepConditionTrace();"
    not in hpp
):
    anchor = None

    for candidate in (
        "void InstallP80AExactConditionMatchProbe();",
        "void InstallP79ADualSubpredicateProbe();",
    ):
        if candidate in hpp:
            anchor = candidate
            break

    if anchor is None:
        raise SystemExit(
            "FATAL no safe header declaration anchor"
        )

    hpp = hpp.replace(
        anchor,
        anchor
        + "\n"
        + "void InstallP80BDeepConditionTrace();",
        1
    )


# ================================================================
# ACTIVE MAIN
# ================================================================

old = active_found[0]

main = main.replace(
    old,
    "nsc::InstallP80BDeepConditionTrace();",
    1
)

main = main.replace(
    "NSC P79A dual subpredicate probe exception",
    "NSC P80B deep condition trace exception"
)

main = main.replace(
    "NSC P80A exact condition match probe exception",
    "NSC P80B deep condition trace exception"
)


CPP.write_text(cpp, encoding="utf-8")
HPP.write_text(hpp, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")

print("P80B_SOURCE_PATCH=PASS")
print("PREVIOUS_ACTIVE=" + old)
