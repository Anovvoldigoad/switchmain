#include "nsc_runtime_v2.hpp"
#include "condition_compat_generated.hpp"
#include "lib.hpp"
#include <lib/patch/random_access_patcher.hpp>
#include <lib/util/modules.hpp>
#include <program/loggers.hpp>
#include <cstddef>
#include <cstdint>

namespace nsc::v2 {
namespace {

// V2D extends the hardware-PASS V2C resolver and removes the patched-main
// deployment dependency. The on-disk main stays original; after every required
// site resolves uniquely and every original fingerprint validates, V2D recreates
// the exact 30 instruction-word changes of the proven P128 paired main in memory.
// No write occurs until the entire patch plan has validated (fail closed).
constexpr std::size_t kScanSpan = 0x12F5FD0;

struct Pattern {
    Anchor anchor;
    const char* name;
    const std::uint32_t* value;
    const std::uint32_t* mask;
    std::size_t count;
    std::ptrdiff_t v170_expected;
};

static std::ptrdiff_t g_resolved_offsets[static_cast<unsigned>(Anchor::Count)] = {
    -1, -1, -1, -1, -1, -1, -1
};
static bool g_resolver_ready = false;
static std::ptrdiff_t g_uj_session_post_offset = -1;
static std::ptrdiff_t g_uj_gate_load_offset = -1;
static bool g_runtime_main_patches_ready = false;

bool MatchAt(std::uintptr_t base, std::size_t off, const Pattern& p) {
    const auto* q = reinterpret_cast<const volatile std::uint32_t*>(base + off);
    for (std::size_t i = 0; i < p.count; ++i) {
        const std::uint32_t w = q[i];
        if ((w & p.mask[i]) != (p.value[i] & p.mask[i])) return false;
    }
    return true;
}

std::uintptr_t ResolveUnique(std::uintptr_t base, const Pattern& p, std::uint32_t& hits) {
    hits = 0;
    std::uintptr_t found = 0;
    const std::size_t bytes = p.count * sizeof(std::uint32_t);
    if (bytes == 0 || bytes > kScanSpan) return 0;
    for (std::size_t off = 0; off + bytes <= kScanSpan; off += 4) {
        if (!MatchAt(base, off, p)) continue;
        ++hits;
        if (hits == 1) found = base + off;
        if (hits > 1) return 0; // fail closed: ambiguous signature
    }
    return hits == 1 ? found : 0;
}


bool DecodeBlTargetOffset(std::size_t call_off, std::uint32_t word, std::ptrdiff_t& out_target) {
    if ((word & 0xFC000000u) != 0x94000000u) return false;
    std::int64_t imm26 = static_cast<std::int64_t>(word & 0x03FFFFFFu);
    if (imm26 & (1ll << 25)) imm26 -= (1ll << 26);
    out_target = static_cast<std::ptrdiff_t>(call_off) +
        static_cast<std::ptrdiff_t>(imm26 << 2);
    return true;
}

std::ptrdiff_t ResolveUjSessionPostUnique(std::uintptr_t base, std::ptrdiff_t outer_off,
                                          std::uint32_t& hits) {
    hits = 0;
    std::ptrdiff_t found = -1;
    // Proven native corridor shape at v1.70:
    //   MOV X0,X23 ; BL UJ_SESSION_OUTER ; LDR W8,[X20,#0x50]
    // We bind to the resolved OUTER target rather than any absolute callsite.
    for (std::size_t off = 4; off + 8 <= kScanSpan; off += 4) {
        const auto* q = reinterpret_cast<const volatile std::uint32_t*>(base + off - 4);
        const std::uint32_t prev = q[0];
        const std::uint32_t call = q[1];
        const std::uint32_t next = q[2];
        if (prev != 0xAA1703E0u || next != 0xB9405288u) continue;
        std::ptrdiff_t target = -1;
        if (!DecodeBlTargetOffset(off, call, target) || target != outer_off) continue;
        ++hits;
        if (hits == 1) found = static_cast<std::ptrdiff_t>(off + 4);
        if (hits > 1) return -1;
    }
    return hits == 1 ? found : -1;
}


std::ptrdiff_t ResolveExactUnique(std::uintptr_t base, const std::uint32_t* words,
                                  std::size_t count, std::uint32_t& hits) {
    hits = 0;
    std::ptrdiff_t found = -1;
    const std::size_t bytes = count * sizeof(std::uint32_t);
    if (!count || bytes > kScanSpan) return -1;
    for (std::size_t off = 0; off + bytes <= kScanSpan; off += 4) {
        const auto* q = reinterpret_cast<const volatile std::uint32_t*>(base + off);
        bool ok = true;
        for (std::size_t i = 0; i < count; ++i) {
            if (q[i] != words[i]) { ok = false; break; }
        }
        if (!ok) continue;
        ++hits;
        if (hits == 1) found = static_cast<std::ptrdiff_t>(off);
        if (hits > 1) return -1;
    }
    return hits == 1 ? found : -1;
}

std::ptrdiff_t ResolveUjGateLoadNearPost(std::uintptr_t base, std::ptrdiff_t post_off,
                                         std::uint32_t& hits) {
    static constexpr std::uint32_t kGateNative[] = {
        0xB9405288u, 0x121F7909u, 0x7100293Fu, 0x54000B81u
    };
    hits = 0;
    std::ptrdiff_t found = -1;
    if (post_off < 0x400) return -1;
    const std::ptrdiff_t begin = post_off - 0x400;
    for (std::ptrdiff_t off = begin; off + 16 <= post_off; off += 4) {
        const auto* q = reinterpret_cast<const volatile std::uint32_t*>(
            base + static_cast<std::uintptr_t>(off));
        bool ok = true;
        for (std::size_t i = 0; i < 4; ++i) {
            if (q[i] != kGateNative[i]) { ok = false; break; }
        }
        if (!ok) continue;
        ++hits;
        if (hits == 1) found = off;
        if (hits > 1) return -1;
    }
    return hits == 1 ? found : -1;
}

struct WordPatch {
    std::ptrdiff_t off;
    std::uint32_t before;
    std::uint32_t after;
};

bool ReadWord(std::uintptr_t base, std::ptrdiff_t off, std::uint32_t& out) {
    if (off < 0 || static_cast<std::size_t>(off) + 4 > kScanSpan) return false;
    out = *reinterpret_cast<const volatile std::uint32_t*>(
        base + static_cast<std::uintptr_t>(off));
    return true;
}

#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))

// Masks keep stable opcode/register structure while ignoring relocatable
// immediates in ADRP/B/BL/CBZ/B.cond where appropriate.
static constexpr std::uint32_t kCharVal[] = {
    0xF000EA68,0xF9424508,0xF9760908,0x2A0003E1,0xF9409500,0x1410AC93,
    0x00000000,0x00000000,0xF81E0FFE,0xA9014FF4,0xF000EA68,0xF9424508};
static constexpr std::uint32_t kCharMask[] = {
    0x9F00001F,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFC000000,
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0x9F00001F,0xFFFFFFFF};

static constexpr std::uint32_t kCpkVal[] = {
    0xF81D0FFE,0xA90157F6,0xA9024FF4,0xD000E6A8,0xF945ED08,0xAA0003F5,
    0xF9400100,0xB4000200,0xAA0103F4,0xB9400AA8,0x2A0203F3,0xF94002A1};
static constexpr std::uint32_t kCpkMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0x9F00001F,0xFFFFFFFF,0xFFFFFFFF,
    0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kEvent236Val[] = {
    0xF81F0FFE,0xF9400008,0xF946E908,0xD63F0100,0xB4000080,0xF9400008,
    0xF945E108,0xD63F0100,0x52800020,0xF84107FE,0xD65F03C0,0x52800020};
static constexpr std::uint32_t kEvent236Mask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kPlayVal[] = {
    0xA9BE57FE,0xA9014FF4,0xB9529408,0x2A0403F4,0xAA0003F3,0x7100091F,
    0x54000080,0xB9528668,0x7100051F,0x540000A1,0x2A1F03E2,0x52800028};
static constexpr std::uint32_t kPlayMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,
    0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kSetterVal[] = {
    0xD10303FF,0x6D0523E9,0xA9067BFD,0xA9076FFC,0xA90867FA,0xA9095FF8,
    0xA90A57F6,0xA90B4FF4,0xF9410C08,0x4EA01C08,0x2A0303F4,0x2A0203F6};
static constexpr std::uint32_t kSetterMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kOuterVal[] = {
    0xF81E0FFE,0xA9014FF4,0xAA0003F3,0x940023EE,0x350002A0,0x9000CAA8,
    0xF9424508,0xF9762514,0xB4000234,0xF9400268,0xAA1303E0,0xF9402508};
static constexpr std::uint32_t kOuterMask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFC000000,0xFF00001F,0x9F00001F,
    0xFFFFFFFF,0xFFFFFFFF,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF};

static constexpr std::uint32_t kState137Val[] = {
    0x528058C1,0xF94027F8,0x1E2E1000,0x12800002,0xAA1303E0,0x2A1F03E3,
    0x2A1F03E4,0x97FDFF32,0x340004C0,0x528002C1,0xAA1303E0,0x97FEB5B6};
static constexpr std::uint32_t kState137Mask[] = {
    0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,0xFFFFFFFF,
    0xFFFFFFFF,0xFC000000,0xFF00001F,0xFFFFFFFF,0xFFFFFFFF,0xFC000000};

static constexpr Pattern kPatterns[] = {
    {Anchor::CharacodeGetter, "CHARACODE_GETTER", kCharVal, kCharMask, ARRAY_COUNT(kCharVal), 0x3F4150},
    {Anchor::CpkBind, "CPK_BIND", kCpkVal, kCpkMask, ARRAY_COUNT(kCpkVal), 0x473190},
    {Anchor::Event236, "EVENT236", kEvent236Val, kEvent236Mask, ARRAY_COUNT(kEvent236Val), 0x816300},
    {Anchor::PlayAction, "PLAY_ACTION", kPlayVal, kPlayMask, ARRAY_COUNT(kPlayVal), 0x766B8C},
    {Anchor::CentralSetter, "CENTRAL_SETTER", kSetterVal, kSetterMask, ARRAY_COUNT(kSetterVal), 0x766320},
    {Anchor::UjSessionOuter, "UJ_SESSION_OUTER", kOuterVal, kOuterMask, ARRAY_COUNT(kOuterVal), 0x7EF098},
    {Anchor::State137Controller, "STATE137_CONTROLLER", kState137Val, kState137Mask, ARRAY_COUNT(kState137Val), 0x7E6EA8},
};

} // namespace

const char* AnchorName(Anchor anchor) {
    for (const auto& p : kPatterns) {
        if (p.anchor == anchor) return p.name;
    }
    return "UNKNOWN";
}

bool GetResolvedOffset(Anchor anchor, std::ptrdiff_t& out_offset) {
    const unsigned i = static_cast<unsigned>(anchor);
    if (!g_resolver_ready || i >= static_cast<unsigned>(Anchor::Count)) return false;
    const std::ptrdiff_t off = g_resolved_offsets[i];
    if (off < 0) return false;
    out_offset = off;
    return true;
}

bool GetDerivedUjSessionPostOffset(std::ptrdiff_t& out_offset) {
    if (!g_resolver_ready || g_uj_session_post_offset < 0) return false;
    out_offset = g_uj_session_post_offset;
    return true;
}

void InstallResolverHookMigrationProbe() {
    const std::uintptr_t base = exl::util::modules::GetTargetStart();
    for (auto& off : g_resolved_offsets) off = -1;
    g_uj_session_post_offset = -1;
    g_uj_gate_load_offset = -1;
    g_runtime_main_patches_ready = false;
    g_resolver_ready = false;

    std::uint32_t ok = 0;
    Logging.Log("[NSC:V2D] RESOLVER_START base=%p span=0x%lx original_main=1 hook_migration=EVENT236,PLAY_ACTION,CENTRAL_SETTER,CPK_BIND,CHARACODE_GETTER,UJ_SESSION_POST",
                reinterpret_cast<void*>(base), static_cast<unsigned long>(kScanSpan));
    for (const auto& p : kPatterns) {
        std::uint32_t hits = 0;
        const std::uintptr_t addr = ResolveUnique(base, p, hits);
        const std::ptrdiff_t off = addr ? static_cast<std::ptrdiff_t>(addr - base) : -1;
        const bool expected = addr && off == p.v170_expected;
        if (addr) {
            ++ok;
            g_resolved_offsets[static_cast<unsigned>(p.anchor)] = off;
        }
        Logging.Log("[NSC:V2D] RESOLVE name=%s hits=%u addr=%p off=0x%lx v170_expected=0x%lx exact=%u",
                    p.name, hits, reinterpret_cast<void*>(addr),
                    static_cast<unsigned long>(off),
                    static_cast<unsigned long>(p.v170_expected), expected ? 1u : 0u);
    }
    std::uint32_t post_hits = 0;
    const std::ptrdiff_t outer_off =
        g_resolved_offsets[static_cast<unsigned>(Anchor::UjSessionOuter)];
    if (outer_off >= 0) {
        g_uj_session_post_offset = ResolveUjSessionPostUnique(base, outer_off, post_hits);
    }
    Logging.Log("[NSC:V2D] DERIVE name=UJ_SESSION_POST hits=%u outer_off=0x%lx post_off=0x%lx exact_v170=%u",
                post_hits, static_cast<unsigned long>(outer_off),
                static_cast<unsigned long>(g_uj_session_post_offset),
                g_uj_session_post_offset == 0x77C5EC ? 1u : 0u);

    // Publish only after every slot and derived continuation are finalized.
    g_resolver_ready = true;
    Logging.Log("[NSC:V2D] RESOLVER_READY resolved=%u total=%u fail_closed=1 migrated_hook_entries=6 no_offset_fallback=1 original_main=1 uj_post_derived=%u",
                ok, static_cast<unsigned>(ARRAY_COUNT(kPatterns)),
                g_uj_session_post_offset >= 0 ? 1u : 0u);
}


bool GetDerivedUjGateLoadOffset(std::ptrdiff_t& out_offset) {
    if (!g_resolver_ready || !g_runtime_main_patches_ready || g_uj_gate_load_offset < 0) return false;
    out_offset = g_uj_gate_load_offset;
    return true;
}

bool RuntimeMainPatchesReady() {
    return g_runtime_main_patches_ready;
}

bool InstallOriginalMainRuntimePatches() {
    using namespace condition_compat_generated;
    if (!g_resolver_ready || g_uj_session_post_offset < 0) {
        Logging.Log("[NSC:V2D] PATCH_FAIL reason=resolver_not_ready");
        return false;
    }

    const std::uintptr_t base = exl::util::modules::GetTargetStart();

    // Exact source-v1.70 native signatures for the five condition-count sites
    // and the P67 source-parity prerequisite. These locate the instructions;
    // no absolute address is used as a fallback.
    static constexpr std::uint32_t kCond0[] = {
        0xF9400C08u,0xF100011Fu,0x52804009u,0x7A491022u,0x52801609u};
    static constexpr std::uint32_t kCond1[] = {
        0x14000004u,0x11000718u,0x7108031Fu,0x540001A0u,0x2A1803E0u,
        0x97FF7566u,0xB4FFFF60u,0xF9400000u,0xB4FFFF20u};
    static constexpr std::uint32_t kCond2[] = {
        0xF81E0FFEu,0xA9014FF4u,0xAA0003F4u,0x2A1F03F3u,0x14000004u,0x11000673u,
        0x7108027Fu,0x540001A0u,0x2A1303E0u,0x97FF74C1u,0xB4FFFF60u,0xF9400000u};
    static constexpr std::uint32_t kCond3[] = {
        0xF81E0FFEu,0xA9014FF4u,0x2A0003F4u,0x2A1F03F3u,0x14000004u,0x11000673u,
        0x7108027Fu,0x540001A0u,0x2A1303E0u,0x97FF744Fu,0xB4FFFF60u,0xF9400000u};
    static constexpr std::uint32_t kCond4[] = {
        0x97F1F1B7u,0x2A1F03F3u,0xB4FFFF40u,0x91079014u,0x14000004u,0x11000673u,
        0x7108027Fu,0x54000140u,0x2A1303E0u,0x97FF7402u,0xB4FFFF60u,0xF9400000u};
    static constexpr std::uint32_t kP67[] = {
        0xBD4006E0u,0x1E202008u,0x5400008Du,0xBD401FE1u,0x1E200820u,
        0xBD001FE0u,0xF9762716u,0xB4000336u,0xF9400268u,0xAA1303E0u};

    const std::uint32_t* sigs[] = {kCond0,kCond1,kCond2,kCond3,kCond4,kP67};
    const std::size_t lens[] = {
        ARRAY_COUNT(kCond0),ARRAY_COUNT(kCond1),ARRAY_COUNT(kCond2),
        ARRAY_COUNT(kCond3),ARRAY_COUNT(kCond4),ARRAY_COUNT(kP67)};
    const std::size_t patch_index[] = {2,2,6,6,6,5};
    std::ptrdiff_t sites[6] = {-1,-1,-1,-1,-1,-1};
    for (std::size_t i = 0; i < 6; ++i) {
        std::uint32_t hits = 0;
        const std::ptrdiff_t start = ResolveExactUnique(base, sigs[i], lens[i], hits);
        if (start < 0) {
            Logging.Log("[NSC:V2D] PATCH_FAIL reason=site_resolve index=%u hits=%u",
                        static_cast<unsigned>(i), hits);
            return false;
        }
        sites[i] = start + static_cast<std::ptrdiff_t>(patch_index[i] * 4);
    }

    std::uint32_t gate_hits = 0;
    const std::ptrdiff_t gate = ResolveUjGateLoadNearPost(base, g_uj_session_post_offset, gate_hits);
    if (gate < 0) {
        Logging.Log("[NSC:V2D] PATCH_FAIL reason=uj_gate_resolve hits=%u post=0x%lx",
                    gate_hits, static_cast<unsigned long>(g_uj_session_post_offset));
        return false;
    }

    static constexpr std::uint32_t kCaveBefore[] = {
        0xF0009619u,0x913C2339u,0xAA1903E0u,0x942A6437u,0xF9400268u,
        0xAA1303E0u,0xF9402508u,0xD63F0100u,0x11000401u,0xB0009680u,
        0x91292C00u,0x942A642Fu,0xF94002E8u,0xAA1703E0u,0xF9402508u,
        0xD63F0100u,0x11000401u,0xB0009940u,0x91086800u};
    static constexpr std::uint32_t kCaveAfter[] = {
        0x7100291Fu,0x54000220u,0x71002D1Fu,0x540001E0u,0x71003D1Fu,
        0x54000181u,0xB94E56EAu,0x7104615Fu,0x54000129u,0x7140055Fu,
        0x540000E2u,0xF9410EEAu,0xB40000AAu,0xB9402D4Au,0x710B0D5Fu,
        0x54000041u,0x14000002u,0x1400003Du,0x17FFFFE1u};

    static_assert(kTotalConditionCount <= 0xFFFu, "condition count immediate overflow");
    const std::uint32_t cond_raw = 0x52800000u | (kTotalConditionCount << 5) | 9u;
    const std::uint32_t cond_w24 = 0x7100001Fu | (kTotalConditionCount << 10) | (24u << 5);
    const std::uint32_t cond_w19 = 0x7100001Fu | (kTotalConditionCount << 10) | (19u << 5);

    WordPatch plan[30]{};
    std::size_t n = 0;
    plan[n++] = {sites[0],0x52804009u,cond_raw};
    plan[n++] = {sites[1],0x7108031Fu,cond_w24};
    plan[n++] = {sites[2],0x7108027Fu,cond_w19};
    plan[n++] = {sites[3],0x7108027Fu,cond_w19};
    plan[n++] = {sites[4],0x7108027Fu,cond_w19};
    plan[n++] = {sites[5],0xBD001FE0u,0xD503201Fu};

    plan[n++] = {gate + 0x0C,0x54000B81u,0x1400000Eu};
    plan[n++] = {gate + 0x20,0x34000AC0u,0xD503201Fu};
    plan[n++] = {gate + 0x34,0x34000A20u,0xD503201Fu};
    plan[n++] = {gate + 0x40,0x34000300u,0x14000018u};
    for (std::size_t i = 0; i < ARRAY_COUNT(kCaveBefore); ++i) {
        plan[n++] = {gate + 0x44 + static_cast<std::ptrdiff_t>(i * 4),
                     kCaveBefore[i], kCaveAfter[i]};
    }
    plan[n++] = {gate + 0xAC,0xB40003E0u,0x1400001Fu};
    if (n != ARRAY_COUNT(plan)) {
        Logging.Log("[NSC:V2D] PATCH_FAIL reason=plan_count n=%u", static_cast<unsigned>(n));
        return false;
    }

    // Validate ALL original words before the first write.
    for (std::size_t i = 0; i < n; ++i) {
        std::uint32_t got = 0;
        if (!ReadWord(base, plan[i].off, got) || got != plan[i].before) {
            Logging.Log("[NSC:V2D] PATCH_FAIL reason=fingerprint i=%u off=0x%lx got=%08x expected=%08x",
                        static_cast<unsigned>(i), static_cast<unsigned long>(plan[i].off),
                        got, plan[i].before);
            return false;
        }
    }

    {
        exl::patch::RandomAccessPatcher patcher;
        for (std::size_t i = 0; i < n; ++i) {
            patcher.Write<std::uint32_t>(static_cast<std::uintptr_t>(plan[i].off), plan[i].after);
        }
        patcher.Flush();
    }

    for (std::size_t i = 0; i < n; ++i) {
        std::uint32_t got = 0;
        if (!ReadWord(base, plan[i].off, got) || got != plan[i].after) {
            Logging.Log("[NSC:V2D] PATCH_FAIL reason=verify_after i=%u off=0x%lx got=%08x expected=%08x",
                        static_cast<unsigned>(i), static_cast<unsigned long>(plan[i].off),
                        got, plan[i].after);
            return false;
        }
    }

    g_uj_gate_load_offset = gate;
    g_runtime_main_patches_ready = true;
    Logging.Log("[NSC:V2D] RUNTIME_PATCH_READY words=%u condition_words=5 p67_words=1 p128_words=24 original_main=1 paired_main_file=0 gate_off=0x%lx post_off=0x%lx",
                static_cast<unsigned>(n), static_cast<unsigned long>(gate),
                static_cast<unsigned long>(g_uj_session_post_offset));
    return true;
}

} // namespace nsc::v2
