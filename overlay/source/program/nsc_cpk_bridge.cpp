#include "nsc_cpk_bridge.hpp"
#include "condition_compat_generated.hpp"

#include "lib.hpp"
#include <lib/hook/trampoline.hpp>
#include <lib/util/modules.hpp>
#include <program/loggers.hpp>

#include <atomic>
#include <cstddef>
#include <cstdint>

namespace nsc {
namespace {

// NSC Switch v1.70 main offsets.
constexpr ptrdiff_t kCpkBindOffset           = 0x473190;
constexpr ptrdiff_t kCharacodeGetterOffset   = 0x3F4150;
constexpr ptrdiff_t kFileLoadRequestOffset   = 0x1206B4C; // nuccFileLoadList request/find-or-create
constexpr ptrdiff_t kFileLoadCreateOffset    = 0x1206C9C; // create new nuccFileLoad object
constexpr ptrdiff_t kFileLoadStatusOffset    = 0x1207EFC; // lookup path -> status, 4 if absent from list
constexpr ptrdiff_t kChunkBinaryOffset        = 0x3EAE70;  // ccGetChunkBinary(full_path, key)
constexpr ptrdiff_t kLoadRequestProcessOffset = 0x116F404; // nuccLoadRequest process/open/read path
constexpr ptrdiff_t kFileOpenOffset           = 0x1170FB0; // low-level file open request; returns 1/0
constexpr ptrdiff_t kEvent236Offset           = 0x816300;  // native ME_ENEMY_DISP_OFF callback
constexpr ptrdiff_t kEvent235Offset           = 0x8162D4;  // native ME_ENEMY_DISP_ON callback
constexpr ptrdiff_t kEvent13Offset            = 0x810614;  // native awakening-condition event callback
constexpr ptrdiff_t kEvent121Offset           = 0x8134F8;  // native ME_ADD_CONDITION_PARAM callback
constexpr ptrdiff_t kOugiCoreOffset           = 0x7E0F58;  // native actor/mode UJ state core containing 0x7E13E4/0x7E1404
constexpr ptrdiff_t kOugiCallerOffset         = 0x488BAC;  // unique direct caller of ougi core (BL at 0x488BBC)
// P44A: OugiFinishParam Create (init-time manager) — first bounded OugiFinish-related function
constexpr ptrdiff_t kOugiFinishCreateOffset   = 0x4726E4;  // ccOugiFinishParamManager Create / load path (init-only, P44A)
// P45A: combat action table handlers (table-dispatched, 0 direct BL callers)
constexpr ptrdiff_t kNormalOugiOffset         = 0x6F44A0;  // NORMAL_OUGI combat action handler (end classifier)
constexpr ptrdiff_t kSpecialOugiFinishOffset  = 0x6F4880;  // SPECIAL_OUGI_FINISH combat action handler (end classifier)
// P50A: keep only the proven PRE/POST PlayAction probe for UJ progression
constexpr ptrdiff_t kPlayActionProbeOffset    = 0x766B8C;  // PlayAction → int32_t ret
// P57A: central actor action setter behind vtable+0xF98. Runtime P56B
// proved vanilla UJ PlayAction(700..740) reaches main+0x766320. The PlayAction
// wrapper calls this as (actor, action, a2, a3) and ignores its return value.
constexpr ptrdiff_t kCentralActionSetterOffset = 0x766320;
// Historical decision-chain probes retained in source but not installed by P50A
constexpr ptrdiff_t kActionLookupOffset        = 0x768E84;  // actor,index,flag -> action entry ptr/null
constexpr ptrdiff_t kActionGateOffset          = 0x769A4C;  // actor -> bool-like completion/timing gate
constexpr ptrdiff_t kActionRemapOffset         = 0x769B04;  // actor,index -> resolved index

// P52A: pre-UJ decision trace. These boundaries are upstream of PlayAction(700).
constexpr ptrdiff_t kUjStartWrapperOffset      = 0x488958;  // actor,mode wrapper; direct route to UJ start state
constexpr ptrdiff_t kUjStartStateOffset        = 0x7E3534;  // mode0 calls PlayAction(700) at 0x7E35E8
constexpr ptrdiff_t kSpecialTypeCtrlOffset     = 0x646190;  // CtrlAct_PL_ACT_NORMAL_SPTYPE_SPSKILL controller

// P54A: direct-jutsu owners in the CtrlAct skill cluster.  These functions
// bypass PlayAction and call actor vtable+0xF98 directly with action 98/100.
// Both have the controller ABI (actor, mode) and are read-only probed here.
constexpr ptrdiff_t kDirectAction98OwnerOffset  = 0x2A472C;
constexpr ptrdiff_t kDirectAction100OwnerOffset = 0x2A51B8;

// P50A: SC 1.70 dynamic condition compatibility port.
// 0x754A80 is the native 32-byte condition-descriptor getter.  The stock
// v1.70 getter and its name/hash loops stop at the vanilla 512-entry geometry.
constexpr ptrdiff_t kConditionGetterOffset      = 0x754A80;
constexpr ptrdiff_t kConditionResolveOffset     = 0x777758;
constexpr ptrdiff_t kConditionOwnerOffset       = 0x7630FC;
constexpr ptrdiff_t kConditionApplyOffset       = 0x776014;

// These sites are patched in the paired P50A main.  They are fingerprints here
// so the module refuses to claim condition compatibility on an unpatched main.
constexpr ptrdiff_t kConditionRawCountOffset    = 0x747878;
constexpr ptrdiff_t kConditionNameLoop0Offset   = 0x7774DC;
constexpr ptrdiff_t kConditionNameLoop1Offset   = 0x777770;
constexpr ptrdiff_t kConditionHashLoopOffset    = 0x777938;
constexpr ptrdiff_t kConditionNameLoop2Offset   = 0x777A6C;

// Proven v1.70 native helpers used by the historical generic MovesetPlus event236 port.
constexpr ptrdiff_t kStageObjectLookupOffset   = 0xEC8A44;
constexpr ptrdiff_t kStageSpecificOffset       = 0x535F88;
constexpr ptrdiff_t kStageDefaultOffset        = 0x53643C;
constexpr ptrdiff_t kHandleStageChangeOffset   = 0x6E8EB0;
constexpr ptrdiff_t kFixCharPositionOffset     = 0x48E40C;
constexpr ptrdiff_t kPostStageOffset            = 0x48E61C;
// Historical control-block candidate ONLY. Hardware P40 rejected +0x12A24
// as the PC-style boolean control block (selector1/UJ read 58, selector2/Jutsu
// read 26). It is retained only by inactive legacy Event13 diagnostics. P56B
// never writes this address and locates the real Switch layout read-only.
constexpr ptrdiff_t kRejectedControlBlockOffset = 0x12A24;

// P56B read-only control-layout locator. The scan is bounded to memory already
// proven inside the actor object: the upper bound plus max source-relative
// field 0x58 lands exactly at +0x12B78, an independently recovered Switch
// D-pad-region boundary. No candidate is ever written.
constexpr uint32_t kControlScanStart = 0x12800;
constexpr uint32_t kControlScanEnd   = 0x12B20;
constexpr ptrdiff_t kActionPreOffset            = 0x7A8438;
constexpr ptrdiff_t kActionEntryLookupOffset    = 0x3F5560;
constexpr ptrdiff_t kActionNameCompareOffset    = 0x12F36E0;
constexpr ptrdiff_t kPlayActionOffset           = 0x766B8C;
constexpr ptrdiff_t kStageGlobalOffset          = 0x2143648;
constexpr ptrdiff_t kStageStateGlobalOffset     = 0x21434C0;
constexpr ptrdiff_t kStageObjectNameOffset      = 0x1A1E84D;

constexpr uint32_t kVanillaMaxCharId = 280;
constexpr uint32_t kFirstCustomCharId = 281;
constexpr int kModCpkPriority = 32;
constexpr const char* kModCpkPath = "sim:data/moddingapi/Tobi_Switch.cpk";

struct CpkPathArg {
    const char* path;
    uint64_t unk08;
    uint64_t unk10;
    uint64_t unk18;
};
static_assert(sizeof(CpkPathArg) == 0x20);

struct TrackedCode {
    uint32_t id;
    char code[16];
};

std::atomic<uint32_t> g_extra_bind_once{0};
std::atomic<uint32_t> g_char_logs{0};
std::atomic<uint32_t> g_request_logs{0};
std::atomic<uint32_t> g_create_logs{0};
std::atomic<uint32_t> g_status_transition_logs{0};
std::atomic<uint32_t> g_chunk_logs{0};
std::atomic<uint32_t> g_process_logs{0};
std::atomic<uint32_t> g_file_open_logs{0};
std::atomic<uint32_t> g_status_overflow_once{0};
std::atomic<uint32_t> g_event236_logs{0};
std::atomic<uint32_t> g_event235_logs{0};
std::atomic<uint32_t> g_stage_handle_logs{0};
std::atomic<uint32_t> g_fix_char_logs{0};
std::atomic<uint32_t> g_post_stage_logs{0};
std::atomic<uint32_t> g_event13_logs{0};
std::atomic<uint32_t> g_event121_logs{0};
std::atomic<uint32_t> g_ougi_core_logs{0};
std::atomic<uint32_t> g_ougi_caller_logs{0};
std::atomic<uint32_t> g_ougi_finish_create_logs{0};
std::atomic<uint32_t> g_normal_ougi_logs{0};
std::atomic<uint32_t> g_special_ougi_finish_logs{0};
std::atomic<uint32_t> g_play_action_logs{0};
std::atomic<uint32_t> g_action_lookup_logs{0};
std::atomic<uint32_t> g_action_gate_logs{0};
std::atomic<uint32_t> g_action_remap_logs{0};
std::atomic<uint32_t> g_condition_get_logs{0};
std::atomic<uint32_t> g_condition_event121_logs{0};
std::atomic<uint32_t> g_uj_start_wrapper_logs{0};
std::atomic<uint32_t> g_uj_start_state_logs{0};
std::atomic<uint32_t> g_special_type_ctrl_logs{0};
std::atomic<uint32_t> g_direct98_owner_logs{0};
std::atomic<uint32_t> g_direct100_owner_logs{0};
std::atomic<uint32_t> g_p56b_vanilla_snapshots{0};
std::atomic<uint32_t> g_p56b_custom_snapshots{0};
std::atomic<uint32_t> g_p57_setter_logs{0};
std::atomic_flag g_track_lock = ATOMIC_FLAG_INIT;
std::atomic_flag g_status_lock = ATOMIC_FLAG_INIT;
TrackedCode g_tracked[32]{};
uint32_t g_tracked_count = 0;

struct StatusEntry {
    char path[256];
    uint32_t last_status;
};
StatusEntry g_status_entries[128]{};
uint32_t g_status_entry_count = 0;

class TrackLock {
public:
    TrackLock() { while (g_track_lock.test_and_set(std::memory_order_acquire)) {} }
    ~TrackLock() { g_track_lock.clear(std::memory_order_release); }
};

class StatusLock {
public:
    StatusLock() { while (g_status_lock.test_and_set(std::memory_order_acquire)) {} }
    ~StatusLock() { g_status_lock.clear(std::memory_order_release); }
};

bool StartsWith(const char* s, const char* prefix) {
    if (!s || !prefix) return false;
    while (*prefix) {
        if (*s++ != *prefix++) return false;
    }
    return true;
}

bool BoundedEqual(const char* a, const char* b, size_t limit = 15) {
    if (!a || !b) return false;
    for (size_t i = 0; i < limit; ++i) {
        if (a[i] != b[i]) return false;
        if (a[i] == '\0') return true;
    }
    return false;
}

bool PathEqual(const char* a, const char* b, size_t limit = 255) {
    if (!a || !b) return false;
    for (size_t i = 0; i < limit; ++i) {
        if (a[i] != b[i]) return false;
        if (a[i] == '\0') return true;
    }
    return false;
}

void CopyPath(char* dst, size_t dst_size, const char* src) {
    if (!dst || !dst_size) return;
    size_t i = 0;
    if (src) {
        for (; i + 1 < dst_size && src[i]; ++i) dst[i] = src[i];
    }
    dst[i] = '\0';
}

bool BoundedContains(const char* haystack, const char* needle, size_t hay_max = 512, size_t needle_max = 32) {
    if (!haystack || !needle || !*needle) return false;
    size_t nlen = 0;
    while (nlen < needle_max && needle[nlen]) ++nlen;
    if (!nlen) return false;
    for (size_t i = 0; i < hay_max && haystack[i]; ++i) {
        size_t j = 0;
        while (j < nlen && (i + j) < hay_max && haystack[i + j] == needle[j]) ++j;
        if (j == nlen) return true;
    }
    return false;
}

void TrackCustomCode(uint32_t id, const char* code) {
    if (id <= kVanillaMaxCharId || !code || !*code) return;
    TrackLock lock;
    for (uint32_t i = 0; i < g_tracked_count; ++i) {
        if (g_tracked[i].id == id || BoundedEqual(g_tracked[i].code, code)) return;
    }
    if (g_tracked_count >= (sizeof(g_tracked) / sizeof(g_tracked[0]))) return;
    auto& dst = g_tracked[g_tracked_count++];
    dst.id = id;
    size_t i = 0;
    for (; i + 1 < sizeof(dst.code) && code[i]; ++i) dst.code[i] = code[i];
    dst.code[i] = '\0';
}

bool PathContainsTrackedCustom(const char* path) {
    if (!path || !*path) return false;
    TrackLock lock;
    for (uint32_t i = 0; i < g_tracked_count; ++i) {
        if (BoundedContains(path, g_tracked[i].code, 512, 15)) return true;
    }
    return false;
}

bool IsInterestingPath(const char* path) {
    if (!path || !*path) return false;
    // P35A preserves P31: trace every file path containing a discovered
    // custom characode, not just the parent prm_load manifest.
    if (PathContainsTrackedCustom(path)) return true;
    // Fixture fallback only, for ordering before ID281 has been observed.
    return BoundedContains(path, "mtob", 512, 8);
}

bool IsInterestingChunk(const char* path, const char* key) {
    if (IsInterestingPath(path)) return true;
    if (key && *key) {
        if (PathContainsTrackedCustom(key)) return true;
        if (BoundedContains(key, "mtob", 256, 8)) return true; // fixture fallback only
    }
    return false;
}

bool ReadActorIdentity(void* actor, uint32_t& side, uint32_t& char_id) {
    if (!actor) return false;
    auto* b = reinterpret_cast<volatile uint8_t*>(actor);
    side = *reinterpret_cast<volatile uint32_t*>(b + 0xE50);
    char_id = *reinterpret_cast<volatile uint32_t*>(b + 0xE54);
    return side <= 1 && char_id < 0x1000;
}

uintptr_t ReadActionSetterTarget(void* actor) {
    if (!actor) return 0;
    const uintptr_t vtable = *reinterpret_cast<const volatile uintptr_t*>(actor);
    if (!vtable) return 0;
    return *reinterpret_cast<const volatile uintptr_t*>(vtable + 0xF98);
}

struct P55ActorState {
    uint32_t action = 0xFFFFFFFFu;
    int32_t e60 = 0x7FFFFFFF;
    int32_t e94 = 0x7FFFFFFF;
    int32_t e9c = 0x7FFFFFFF;
    int32_t ea0 = 0x7FFFFFFF;
    uint32_t skill0 = 0xFFFFFFFFu;
    uint32_t skill1 = 0xFFFFFFFFu;
    uint32_t skill2 = 0xFFFFFFFFu;
};

P55ActorState ReadP55ActorState(void* actor) {
    P55ActorState st{};
    if (!actor) return st;
    const auto* b = reinterpret_cast<const volatile uint8_t*>(actor);
    st.action = *reinterpret_cast<const volatile uint32_t*>(b + 4712);
    st.e60 = *reinterpret_cast<const volatile int32_t*>(b + 0xE60);
    st.e94 = *reinterpret_cast<const volatile int32_t*>(b + 0xE94);
    st.e9c = *reinterpret_cast<const volatile int32_t*>(b + 0xE9C);
    st.ea0 = *reinterpret_cast<const volatile int32_t*>(b + 0xEA0);
    st.skill0 = *reinterpret_cast<const volatile uint32_t*>(b + 0xE68);
    st.skill1 = *reinterpret_cast<const volatile uint32_t*>(b + 0xE6C);
    st.skill2 = *reinterpret_cast<const volatile uint32_t*>(b + 0xE70);
    return st;
}

ptrdiff_t MainRelativeOffset(uintptr_t address) {
    if (!address) return -1;
    const uintptr_t base = exl::util::modules::GetTargetStart();
    if (address < base) return -1;
    const uintptr_t delta = address - base;
    // main .text is 0x12F5FD0 bytes in the pinned 1.70 executable.
    return delta < 0x12F5FD0u ? static_cast<ptrdiff_t>(delta) : -1;
}


struct P56BControlCandidate {
    uint32_t base = 0;
    uint32_t rank = 0;
    uint8_t boolean_count = 0;
    uint8_t ones = 0;
};

constexpr uint32_t kP56BControlRel[] = {
    0x00, // attack
    0x04, // far attack
    0x08, // Ultimate Jutsu
    0x10, // Jutsus
    0x18, // projectile
    0x1C, // chakra projectile
    0x20, // grab
    0x24, // substitution
    0x28, // guard
    0x2C, // chakra load
    0x30, // movement/chakra
    0x34, // jump
    0x38, // ninja movement
    0x3C, // air dash
    0x40, // land dash
    0x44, // D-pad items
    0x48, // leader switch
    0x4C, // awakening
    0x50, // supports
    0x58, // counter attack
};

int32_t ReadActorI32At(const void* actor, uint32_t off) {
    if (!actor) return 0x7FFFFFFF;
    const auto* b = reinterpret_cast<const volatile uint8_t*>(actor);
    return *reinterpret_cast<const volatile int32_t*>(b + off);
}

void InsertP56BCandidate(P56BControlCandidate (&top)[8], const P56BControlCandidate& c) {
    for (size_t i = 0; i < 8; ++i) {
        if (c.rank <= top[i].rank) continue;
        for (size_t j = 7; j > i; --j) top[j] = top[j - 1];
        top[i] = c;
        break;
    }
}

void LogP56BControlSnapshot(void* actor, const char* tag, uint32_t side, uint32_t char_id, uint32_t seq) {
    if (!actor) return;
    P56BControlCandidate top[8]{};
    for (uint32_t base = kControlScanStart; base <= kControlScanEnd; base += 4) {
        uint8_t bools = 0;
        uint8_t ones = 0;
        for (uint32_t rel : kP56BControlRel) {
            const int32_t v = ReadActorI32At(actor, base + rel);
            if (v == 0 || v == 1) {
                ++bools;
                if (v == 1) ++ones;
            }
        }
        // Pure zero padding is intentionally de-prioritized. A real enabled
        // control block should expose at least some 1-valued controls.
        const uint32_t rank = static_cast<uint32_t>(bools) * 16u +
                              static_cast<uint32_t>(ones) * 4u;
        P56BControlCandidate candidate{};
        candidate.base = base;
        candidate.rank = rank;
        candidate.boolean_count = bools;
        candidate.ones = ones;
        InsertP56BCandidate(top, candidate);
    }

    Logging.Log("[NSC:P56B] CONTROL_SNAPSHOT tag=%s seq=%u actor=%p side=%u char=%u scan=0x%x-0x%x hist12a24=%d/%d/%d/%d",
                tag, seq, actor, side, char_id, kControlScanStart, kControlScanEnd,
                ReadActorI32At(actor, 0x12A24), ReadActorI32At(actor, 0x12A28),
                ReadActorI32At(actor, 0x12A2C), ReadActorI32At(actor, 0x12A34));

    for (uint32_t i = 0; i < 8; ++i) {
        const auto& c = top[i];
        if (!c.rank) continue;
        Logging.Log("[NSC:P56B] CONTROL_CAND tag=%s seq=%u rank=%u base=0x%x bool=%u ones=%u atk=%d far=%d uj=%d jutsu=%d guard=%d chakra=%d move=%d dpad=%d awake=%d support=%d counter=%d",
                    tag, seq, c.rank, c.base, static_cast<unsigned>(c.boolean_count),
                    static_cast<unsigned>(c.ones),
                    ReadActorI32At(actor, c.base + 0x00),
                    ReadActorI32At(actor, c.base + 0x04),
                    ReadActorI32At(actor, c.base + 0x08),
                    ReadActorI32At(actor, c.base + 0x10),
                    ReadActorI32At(actor, c.base + 0x28),
                    ReadActorI32At(actor, c.base + 0x2C),
                    ReadActorI32At(actor, c.base + 0x30),
                    ReadActorI32At(actor, c.base + 0x44),
                    ReadActorI32At(actor, c.base + 0x4C),
                    ReadActorI32At(actor, c.base + 0x50),
                    ReadActorI32At(actor, c.base + 0x58));
    }
}

void CopyEventText(char (&out)[31], const uint8_t* event) {
    for (size_t i = 0; i < 30; ++i) {
        const uint8_t c = event ? event[i] : 0;
        if (!c) { out[i] = '\0'; return; }
        out[i] = (c >= 0x20 && c <= 0x7E) ? static_cast<char>(c) : '.';
    }
    out[30] = '\0';
}

bool ShouldTraceEvent236(int16_t op, int16_t /*p3*/) {
    // P43A focused trace: keep the complete custom Event236 sequence so a single
    // Kamui attempt can be correlated without guessing which extension opcode matters.
    return op >= 1 && op <= 29;
}


uint32_t FloatBits(float value) {
    union { float f; uint32_t u; } v{value};
    return v.u;
}

bool IsFiniteAbsLe16(float value) {
    return (FloatBits(value) & 0x7FFFFFFFu) <= 0x41800000u; // |value| <= 16.0 and finite
}

uint32_t Crc30(const uint8_t* text) {
    uint32_t crc = 0xFFFFFFFFu;
    constexpr uint32_t poly = 0x04C11DB7u;
    for (uint32_t i = 0; i < 30; ++i) {
        const uint8_t c = text[i];
        if (!c) break;
        crc ^= static_cast<uint32_t>(c) << 24;
        for (uint32_t bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x80000000u) ? ((crc << 1) ^ poly) : (crc << 1);
        }
    }
    return ~crc;
}

void* GetEventTargetActor(void* actor, int16_t selector) {
    if (!actor) return nullptr;
    if (selector == 0) return actor;
    if (selector != 1) return nullptr;
    auto** vtable = *reinterpret_cast<void***>(actor);
    if (!vtable) return nullptr;
    using GetEnemyFn = void* (*)(void*);
    auto fn = reinterpret_cast<GetEnemyFn>(vtable[0xDD0 / sizeof(void*)]);
    return fn ? fn(actor) : nullptr;
}

uint32_t HandleStageMove(void* actor, const uint8_t* event, int16_t param2) {
    const uintptr_t base = exl::util::modules::GetTargetStart();
    uint32_t stage_crc = 0;
    if (param2 == 0) stage_crc = Crc30(event);

    auto* stage_global = *reinterpret_cast<void**>(base + kStageGlobalOffset);
    if (!stage_global) return 1;
    auto* manager = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(stage_global) + 0x60);
    if (!manager) return 1;

    using LookupFn = void* (*)(void*, const char*);
    auto lookup = reinterpret_cast<LookupFn>(base + kStageObjectLookupOffset);
    auto* object = lookup(manager, reinterpret_cast<const char*>(base + kStageObjectNameOffset));
    if (!object) return 1;
    auto* object_inner = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(object) + 0x8);
    if (!object_inner) return 1;
    auto* stage_context = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(object_inner) + 0x10);
    if (!stage_context) return 1;

    if (param2 == 0) {
        using SpecificFn = void (*)(void*, uint32_t);
        reinterpret_cast<SpecificFn>(base + kStageSpecificOffset)(stage_context, stage_crc);
    } else {
        using DefaultFn = void (*)(void*);
        reinterpret_cast<DefaultFn>(base + kStageDefaultOffset)(stage_context);
    }

    auto* stage_state_global = *reinterpret_cast<void**>(base + kStageStateGlobalOffset);
    if (!stage_state_global) return 1;
    auto* stage_state = *reinterpret_cast<void**>(stage_state_global);
    if (!stage_state) return 1;
    const uint32_t stage_id = *reinterpret_cast<volatile uint32_t*>(reinterpret_cast<uint8_t*>(stage_state) + 0x8);

    using HandleFn = void (*)(uint32_t);
    using ActorFn = void (*)(void*);
    using VoidFn = void (*)();
    reinterpret_cast<HandleFn>(base + kHandleStageChangeOffset)(stage_id);
    reinterpret_cast<ActorFn>(base + kFixCharPositionOffset)(actor);
    reinterpret_cast<VoidFn>(base + kPostStageOffset)();
    return 1;
}

uint32_t HandleActionAnimation(void* actor, const uint8_t* event, int16_t param2,
                               int16_t param3, bool action_mode) {
    const uintptr_t base = exl::util::modules::GetTargetStart();
    void* target = actor;
    if (param2 == 1) target = GetEventTargetActor(actor, 1);
    if (!target || event[0] == 0) return 1;

    if (action_mode) {
        using PreFn = void (*)(void*, int32_t);
        reinterpret_cast<PreFn>(base + kActionPreOffset)(target, param3);
    }

    using EntryFn = void* (*)(uint32_t);
    using CompareFn = uint32_t (*)(const void*, const void*);
    auto entry_fn = reinterpret_cast<EntryFn>(base + kActionEntryLookupOffset);
    auto compare_fn = reinterpret_cast<CompareFn>(base + kActionNameCompareOffset);

    uint32_t index = 0;
    bool found = false;
    for (; index < 0x3F1; ++index) {
        auto* candidate = reinterpret_cast<uint8_t*>(entry_fn(index));
        if (!candidate) continue;
        if (compare_fn(candidate, event) == 0 || compare_fn(candidate + 7, event) == 0) {
            found = true;
            break;
        }
    }
    if (!found) {
        char text[31]{};
        CopyEventText(text, event);
        Logging.Log("[NSC:P50A] ACTION actor=%p target=%p mode=%u text=%s found=0",
                    actor, target, action_mode ? 1u : 0u, text);
        return 1;
    }

    char text[31]{};
    CopyEventText(text, event);
    Logging.Log("[NSC:P50A] ACTION actor=%p target=%p mode=%u text=%s found=1 index=%u",
                actor, target, action_mode ? 1u : 0u, text, index);

    using PlayFn = void (*)(void*, int32_t, int32_t, int32_t, int32_t, int32_t, float);
    reinterpret_cast<PlayFn>(base + kPlayActionOffset)(target, static_cast<int32_t>(index),
                                                       -1, 0, 0, 0, 1.0f);
    return 1;
}

template <size_t N>
bool MatchWords(ptrdiff_t offset, const uint32_t (&expected)[N]) {
    const auto base = exl::util::modules::GetTargetStart();
    const auto* p = reinterpret_cast<const volatile uint32_t*>(base + offset);
    for (size_t i = 0; i < N; ++i) {
        if (p[i] != expected[i]) return false;
    }
    return true;
}

void LogFingerprintFail(const char* name, ptrdiff_t offset) {
    const auto base = exl::util::modules::GetTargetStart();
    const auto actual = *reinterpret_cast<const volatile uint32_t*>(base + offset);
    Logging.Log("[NSC:P50A] fingerprint FAIL %s off=0x%lx word0=%08x", name,
                static_cast<unsigned long>(offset), actual);
}

HOOK_DEFINE_TRAMPOLINE(CpkBindHook) {
    static uint32_t Callback(CpkPathArg* desc, uint32_t* out_bind_id, int priority) {
        const uint32_t original_result = Orig(desc, out_bind_id, priority);
        if (!desc || original_result == 0 || !desc->path || !StartsWith(desc->path, "sim:")) {
            return original_result;
        }
        uint32_t expected = 0;
        if (!g_extra_bind_once.compare_exchange_strong(expected, 1, std::memory_order_acq_rel)) {
            return original_result;
        }
        CpkPathArg extra{kModCpkPath, 0, 0, 0};
        uint32_t extra_bind_id = 0;
        const uint32_t extra_result = Orig(&extra, &extra_bind_id, kModCpkPriority);
        Logging.Log("[NSC:P50A] CPK_BIND path=%s priority=%d result=%u bind_id=%u",
                    kModCpkPath, kModCpkPriority, extra_result, extra_bind_id);
        return original_result;
    }
};

HOOK_DEFINE_TRAMPOLINE(CharacodeGetterHook) {
    static const char* Callback(uint32_t id) {
        const char* result = Orig(id);
        if (id > kVanillaMaxCharId && result && *result) TrackCustomCode(id, result);
        if (id >= kFirstCustomCharId && g_char_logs.fetch_add(1, std::memory_order_relaxed) < 96) {
            Logging.Log("[NSC:P50A] CHAR id=%u result=%p code=%s", id,
                        static_cast<const void*>(result), result ? result : "<null>");
        }
        return result;
    }
};

// Signature proven by v1.70 disassembly at 0x1206B4C:
// x0=nuccFileLoadList manager, x1=path C string, x2=options pointer.
HOOK_DEFINE_TRAMPOLINE(FileLoadRequestHook) {
    static void* Callback(void* manager, const char* path, const void* options) {
        void* result = Orig(manager, path, options);
        if (IsInterestingPath(path) &&
            g_request_logs.fetch_add(1, std::memory_order_relaxed) < 256) {
            Logging.Log("[NSC:P50A] LOAD_REQ manager=%p path=%s options=%p result=%p",
                        manager, path ? path : "<null>", options, result);
        }
        return result;
    }
};

// Called only when 0x1206B4C needs to construct a fresh load object.
HOOK_DEFINE_TRAMPOLINE(FileLoadCreateHook) {
    static void* Callback(void* manager, const char* path, const void* options) {
        void* result = Orig(manager, path, options);
        if (IsInterestingPath(path) &&
            g_create_logs.fetch_add(1, std::memory_order_relaxed) < 128) {
            Logging.Log("[NSC:P50A] LOAD_CREATE manager=%p path=%s options=%p result=%p",
                        manager, path ? path : "<null>", options, result);
        }
        return result;
    }
};

// Signature proven by 0x11617CC -> 0x1207EFC: x0=manager, x1=path.
// 0x1207EFC returns 4 itself when the path is absent from nuccFileLoadList.
// P35A keeps the first observed status for each custom path and subsequent
// status transitions. This prevents one repeatedly-polled failure from consuming
// the entire trace budget before later prm_load children are reached.
HOOK_DEFINE_TRAMPOLINE(FileLoadStatusHook) {
    static uint32_t Callback(void* manager, const char* path) {
        const uint32_t status = Orig(manager, path);
        if (!IsInterestingPath(path)) return status;

        bool should_log = false;
        bool first = false;
        uint32_t previous = 0xFFFFFFFFu;
        bool overflow = false;
        {
            StatusLock lock;
            uint32_t i = 0;
            for (; i < g_status_entry_count; ++i) {
                if (PathEqual(g_status_entries[i].path, path)) break;
            }
            if (i < g_status_entry_count) {
                previous = g_status_entries[i].last_status;
                if (previous != status) {
                    g_status_entries[i].last_status = status;
                    should_log = true;
                }
            } else if (g_status_entry_count < (sizeof(g_status_entries) / sizeof(g_status_entries[0]))) {
                auto& entry = g_status_entries[g_status_entry_count++];
                CopyPath(entry.path, sizeof(entry.path), path);
                entry.last_status = status;
                first = true;
                should_log = true;
            } else {
                overflow = true;
            }
        }

        if (overflow) {
            uint32_t expected = 0;
            if (g_status_overflow_once.compare_exchange_strong(expected, 1, std::memory_order_acq_rel)) {
                Logging.Log("[NSC:P50A] STATUS_TABLE_OVERFLOW max=%u",
                            static_cast<unsigned>(sizeof(g_status_entries) / sizeof(g_status_entries[0])));
            }
        }

        if (should_log &&
            g_status_transition_logs.fetch_add(1, std::memory_order_relaxed) < 1024) {
            Logging.Log("[NSC:P50A] LOAD_STATUS manager=%p path=%s first=%u prev=%u status=%u",
                        manager, path ? path : "<null>", first ? 1u : 0u, previous, status);
        }
        return status;
    }
};

// main+0x3EAE70 is ccGetChunkBinary(full_path, key) -> resource pointer.
// It first resolves the XFBIN file object, then resolves the named chunk. A null
// result therefore identifies an exact file/key boundary to investigate.
HOOK_DEFINE_TRAMPOLINE(ChunkBinaryHook) {
    static void* Callback(const char* full_path, const char* key) {
        void* result = Orig(full_path, key);
        if (IsInterestingChunk(full_path, key) &&
            g_chunk_logs.fetch_add(1, std::memory_order_relaxed) < 1024) {
            Logging.Log("[NSC:P50A] CHUNK path=%s key=%s result=%p",
                        full_path ? full_path : "<null>",
                        key ? key : "<null>", result);
        }
        return result;
    }
};

// main+0x1170FB0 copies the candidate path into the request and asks the
// underlying mounted-file provider to open it. Native caller 0x116F4D8 marks
// the nuccFileLoad object status=5 when this returns 0.
//
// x0=request object, x1=path C-string, w2=request/file slot; w0=1 success / 0 fail.
HOOK_DEFINE_TRAMPOLINE(FileOpenHook) {
    static uint32_t Callback(void* request, const char* path, uint32_t slot) {
        const uint32_t result = Orig(request, path, slot);
        if (IsInterestingPath(path) &&
            g_file_open_logs.fetch_add(1, std::memory_order_relaxed) < 512) {
            Logging.Log("[NSC:P50A] FILE_OPEN request=%p path=%s slot=%u result=%u",
                        request, path ? path : "<null>", slot, result);
        }
        return result;
    }
};

// main+0x116F404 is the native nuccLoadRequest processing routine that owns
// BOTH proven status=5 branches:
//   0x116F520 -> status=5 after FILE_OPEN returned 0 ("file could not be opened")
//   0x116F5C0 -> status=5 after the XFBIN read path reports failure.
//
// Proven register contract at the callsite 0x116F29C:
//   x0=request owner, x1=read context, x2=nuccFileLoad object, x3=path.
// The caller ignores a return value, so this diagnostic trampoline is void.
// After native processing returns, we log the load object's state and the
// read-context error field checked natively at +0x1D8.
HOOK_DEFINE_TRAMPOLINE(LoadRequestProcessHook) {
    static void Callback(void* owner, void* read_context, void* load_object, const char* path) {
        Orig(owner, read_context, load_object, path);

        if (!IsInterestingPath(path) ||
            g_process_logs.fetch_add(1, std::memory_order_relaxed) >= 512) {
            return;
        }

        uint32_t load_status = 0xFFFFFFFFu;
        uint32_t read_error = 0xFFFFFFFFu;
        if (load_object) {
            const auto* p = reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const uint8_t*>(load_object) + 0x68);
            load_status = *p;
        }
        if (read_context) {
            const auto* p = reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const uint8_t*>(read_context) + 0x1D8);
            read_error = *p;
        }

        Logging.Log("[NSC:P50A] PROCESS path=%s owner=%p readctx=%p load=%p status=%u readerr=%u",
                    path ? path : "<null>", owner, read_context, load_object,
                    load_status, read_error);
    }
};


// P43A: focused stage/cinematic victim-lifecycle trace inherited from P36. These wrappers are
// read-only: they log native boundaries and return/call Orig unchanged.
HOOK_DEFINE_TRAMPOLINE(Event235Hook) {
    static uint32_t Callback(void* actor, void* event_ptr) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        int16_t op = 0, p2 = 0, p3 = 0;
        if (event_ptr) {
            const auto* event = reinterpret_cast<const uint8_t*>(event_ptr);
            op = *reinterpret_cast<const int16_t*>(event + 0x24);
            p2 = *reinterpret_cast<const int16_t*>(event + 0x26);
            p3 = *reinterpret_cast<const int16_t*>(event + 0x28);
        }
        const uint32_t result = Orig(actor, event_ptr);
        if (valid && char_id > kVanillaMaxCharId &&
            g_event235_logs.fetch_add(1, std::memory_order_relaxed) < 256) {
            Logging.Log("[NSC:P50A] EVT235_SHOW actor=%p side=%u char=%u op=%d p2=%d p3=%d ret=%u",
                        actor, side, char_id, static_cast<int>(op), static_cast<int>(p2),
                        static_cast<int>(p3), result);
        }
        return result;
    }
};

// P43A: awakening-condition and UJ-state probes. These hooks are read-only and
// call native Orig exactly once; they do not alias names or force state.
HOOK_DEFINE_TRAMPOLINE(Event13Hook) {
    static uint32_t Callback(void* actor, void* event_ptr) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        int32_t pre_gate = 0x7FFFFFFF, post_gate = 0x7FFFFFFF;
        int32_t pre_awake = 0x7FFFFFFF, post_awake = 0x7FFFFFFF;
        void* condition_owner = nullptr;
        if (actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            pre_gate = *reinterpret_cast<volatile int32_t*>(b + 0x12A0);
            pre_awake = *reinterpret_cast<volatile int32_t*>(
                b + kRejectedControlBlockOffset + 0x4C);
            condition_owner = *reinterpret_cast<void* volatile*>(b + 0x10F80);
        }
        const uint32_t ret = Orig(actor, event_ptr);
        if (actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            post_gate = *reinterpret_cast<volatile int32_t*>(b + 0x12A0);
            post_awake = *reinterpret_cast<volatile int32_t*>(
                b + kRejectedControlBlockOffset + 0x4C);
        }
        const uint32_t n = g_event13_logs.fetch_add(1, std::memory_order_relaxed);
        // P43A: unfiltered — log vanilla AND custom
        if (valid && n < 1024) {
            Logging.Log("[NSC:P50A] EVT13_AWAKE actor=%p side=%u char=%u event=%p cond_owner=%p gate=%d->%d ctrl15=%d->%d ret=%u",
                        actor, side, char_id, event_ptr, condition_owner,
                        pre_gate, post_gate, pre_awake, post_awake, ret);
        }
        return ret;
    }
};

// P50A: generic dynamic extension of the native 32-byte condition descriptor table.
// The generated payload can contain entries from any compiled mod set; this
// callback has no character-ID/name special case.
HOOK_DEFINE_TRAMPOLINE(ConditionGetterHook) {
    static void* Callback(uint32_t index) {
        using namespace condition_compat_generated;
        if (index >= kNativeConditionCount && index < kTotalConditionCount) {
            const uint32_t slot = index - kNativeConditionCount;
            const auto* result = &kExtraConditions[slot];
            const uint32_t n = g_condition_get_logs.fetch_add(1, std::memory_order_relaxed);
            if (n < 512) {
                Logging.Log("[NSC:P50A] COND_GET index=%u slot=%u name=%s result=%p",
                            index, slot, result->name, static_cast<const void*>(result));
            }
            return const_cast<condition_compat_generated::ConditionDescriptor*>(result);
        }
        return Orig(index);
    }
};

HOOK_DEFINE_TRAMPOLINE(Event121Hook) {
    static uint32_t Callback(void* actor, void* event_ptr) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);

        char text[31]{};
        int16_t op = 0, p2 = 0, p3 = 0;
        float p4 = 0.0f;
        uint32_t p4bits = 0;
        if (event_ptr) {
            const auto* event = reinterpret_cast<const uint8_t*>(event_ptr);
            CopyEventText(text, event);
            op = *reinterpret_cast<const int16_t*>(event + 0x24);
            p2 = *reinterpret_cast<const int16_t*>(event + 0x26);
            p3 = *reinterpret_cast<const int16_t*>(event + 0x28);
            p4 = *reinterpret_cast<const float*>(event + 0x2C);
            p4bits = FloatBits(p4);
        }

        // UltimateStormAPI Event121 semantics use p2==1 for SELF.  Native SC
        // 1.70 selects a related actor instead.  Preserve native behavior for
        // vanilla actors and every other selector; only custom SELF records take
        // the parity route.  The condition lookup itself remains fully generic.
        if (valid && char_id > kVanillaMaxCharId && char_id < 0x1000u &&
            event_ptr && p2 == 1) {
            const P55ActorState p55_pre = ReadP55ActorState(actor);
            const uintptr_t base = exl::util::modules::GetTargetStart();
            using OwnerFn = void* (*)(void*);
            using ResolveFn = uint32_t (*)(const char*);
            using ApplyFn = uint32_t (*)(void*, uint32_t, int32_t, float);

            auto owner_fn = reinterpret_cast<OwnerFn>(base + kConditionOwnerOffset);
            auto resolve_fn = reinterpret_cast<ResolveFn>(base + kConditionResolveOffset);
            auto apply_fn = reinterpret_cast<ApplyFn>(base + kConditionApplyOffset);

            void* owner = owner_fn(actor);
            const uint32_t resolved = resolve_fn(reinterpret_cast<const char*>(event_ptr));
            uint32_t apply_ret = 0;
            uint32_t executed = 0;
            if (owner && resolved > 0 &&
                resolved < condition_compat_generated::kTotalConditionCount) {
                // Mirror the native helper chain: reacquire the owner immediately
                // before applying, just as 0x813520..0x813534 does.
                owner = owner_fn(actor);
                if (owner) {
                    apply_ret = apply_fn(owner, resolved, static_cast<int32_t>(op), p4);
                    executed = 1;
                }
            }

            const uint32_t n = g_condition_event121_logs.fetch_add(1, std::memory_order_relaxed);
            if (n < 1024) {
                Logging.Log("[NSC:P50A] EVT121_SELF actor=%p side=%u char=%u text=%s op=%d p2=%d p3=%d p4bits=%08x resolved=%u owner=%p executed=%u apply_ret=%u",
                            actor, side, char_id, text, static_cast<int>(op),
                            static_cast<int>(p2), static_cast<int>(p3), p4bits, resolved,
                            owner, executed, apply_ret);
                const P55ActorState p55_post = ReadP55ActorState(actor);
                Logging.Log("[NSC:P55A] STATE121 actor=%p side=%u char=%u text=%s resolved=%u executed=%u action=%u->%u e60=%d->%d e94=%d->%d e9c=%d->%d ea0=%d->%d skills=%u/%u/%u->%u/%u/%u",
                            actor, side, char_id, text, resolved, executed,
                            p55_pre.action, p55_post.action,
                            p55_pre.e60, p55_post.e60, p55_pre.e94, p55_post.e94,
                            p55_pre.e9c, p55_post.e9c, p55_pre.ea0, p55_post.ea0,
                            p55_pre.skill0, p55_pre.skill1, p55_pre.skill2,
                            p55_post.skill0, p55_post.skill1, p55_post.skill2);
            }
            // Event callbacks conventionally report handled=1.
            return 1;
        }

        return Orig(actor, event_ptr);
    }
};

HOOK_DEFINE_TRAMPOLINE(OugiCoreHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_ougi_core_logs.fetch_add(1, std::memory_order_relaxed);
        int32_t ea0_pre = 0x7FFFFFFF, ea4_pre = 0x7FFFFFFF, ea8_pre = 0x7FFFFFFF;
        void* state_ptr_pre = nullptr;
        if (actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            ea0_pre = *reinterpret_cast<volatile int32_t*>(b + 0xEA0);
            ea4_pre = *reinterpret_cast<volatile int32_t*>(b + 0xEA4);
            ea8_pre = *reinterpret_cast<volatile int32_t*>(b + 0xEA8);
            state_ptr_pre = *reinterpret_cast<void* volatile*>(b + 0x1238);
        }
        Orig(actor, mode);
        // P43A: unfiltered — log vanilla AND custom (control comparison)
        if (valid && n < 1024) {
            int32_t ea0_post = 0x7FFFFFFF, ea4_post = 0x7FFFFFFF, ea8_post = 0x7FFFFFFF;
            void* state_ptr_post = nullptr;
            if (actor) {
                auto* b = reinterpret_cast<volatile uint8_t*>(actor);
                ea0_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA0);
                ea4_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA4);
                ea8_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA8);
                state_ptr_post = *reinterpret_cast<void* volatile*>(b + 0x1238);
            }
            Logging.Log("[NSC:P50A] OUGI_CORE actor=%p side=%u char=%u mode=%u state=%p->%p ea0=%d->%d ea4=%d->%d ea8=%d->%d",
                        actor, side, char_id, mode, state_ptr_pre, state_ptr_post,
                        ea0_pre, ea0_post, ea4_pre, ea4_post, ea8_pre, ea8_post);
        }
    }
};


// P43A: unique direct caller of Ougi core. Contract: x0=actor, w1=mode; return ignored.
// If Kamui never reaches this boundary either, the stuck handoff is upstream of UJ state entry.
HOOK_DEFINE_TRAMPOLINE(OugiCallerHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_ougi_caller_logs.fetch_add(1, std::memory_order_relaxed);
        if (valid && n < 1024) {
            int32_t ea0 = 0x7FFFFFFF, ea4 = 0x7FFFFFFF, ea8 = 0x7FFFFFFF;
            void* state_ptr = nullptr;
            if (actor) {
                auto* b = reinterpret_cast<volatile uint8_t*>(actor);
                ea0 = *reinterpret_cast<volatile int32_t*>(b + 0xEA0);
                ea4 = *reinterpret_cast<volatile int32_t*>(b + 0xEA4);
                ea8 = *reinterpret_cast<volatile int32_t*>(b + 0xEA8);
                state_ptr = *reinterpret_cast<void* volatile*>(b + 0x1238);
            }
            Logging.Log("[NSC:P50A] OUGI_CALLER actor=%p side=%u char=%u mode=%u state=%p ea0=%d ea4=%d ea8=%d",
                        actor, side, char_id, mode, state_ptr, ea0, ea4, ea8);
        }
        Orig(actor, mode);
    }
};

// P52A: first boundary on the UJ-start path. Naruto UJ must hit mode0 here before
// 0x7E3534 can reach PlayAction(700). Read-only: no return/state modification.
HOOK_DEFINE_TRAMPOLINE(UjStartWrapperHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_uj_start_wrapper_logs.fetch_add(1, std::memory_order_relaxed);
        uint32_t action_pre = 0xFFFFFFFFu;
        int32_t e60_pre = 0x7FFFFFFF, e94_pre = 0x7FFFFFFF, e9c_pre = 0x7FFFFFFF;
        int32_t ea0_pre = 0x7FFFFFFF, ea4_pre = 0x7FFFFFFF, ea8_pre = 0x7FFFFFFF;
        if (actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            action_pre = *reinterpret_cast<volatile uint32_t*>(b + 4712);
            e60_pre = *reinterpret_cast<volatile int32_t*>(b + 0xE60);
            e94_pre = *reinterpret_cast<volatile int32_t*>(b + 0xE94);
            e9c_pre = *reinterpret_cast<volatile int32_t*>(b + 0xE9C);
            ea0_pre = *reinterpret_cast<volatile int32_t*>(b + 0xEA0);
            ea4_pre = *reinterpret_cast<volatile int32_t*>(b + 0xEA4);
            ea8_pre = *reinterpret_cast<volatile int32_t*>(b + 0xEA8);
        }
        if (valid && n < 1024) {
            Logging.Log("[NSC:P52A] UJ_WRAPPER phase=pre actor=%p side=%u char=%u mode=%u action=%u e60=%d e94=%d e9c=%d ea0=%d ea4=%d ea8=%d n=%u",
                        actor, side, char_id, mode, action_pre, e60_pre, e94_pre, e9c_pre,
                        ea0_pre, ea4_pre, ea8_pre, n);
        }
        Orig(actor, mode);
        if (valid && n < 1024 && actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            const uint32_t action_post = *reinterpret_cast<volatile uint32_t*>(b + 4712);
            const int32_t e60_post = *reinterpret_cast<volatile int32_t*>(b + 0xE60);
            const int32_t e94_post = *reinterpret_cast<volatile int32_t*>(b + 0xE94);
            const int32_t e9c_post = *reinterpret_cast<volatile int32_t*>(b + 0xE9C);
            const int32_t ea0_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA0);
            const int32_t ea4_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA4);
            const int32_t ea8_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA8);
            Logging.Log("[NSC:P52A] UJ_WRAPPER phase=post actor=%p side=%u char=%u mode=%u action=%u e60=%d e94=%d e9c=%d ea0=%d ea4=%d ea8=%d n=%u",
                        actor, side, char_id, mode, action_post, e60_post, e94_post, e9c_post,
                        ea0_post, ea4_post, ea8_post, n);
        }
    }
};

// P52A: exact state core whose mode0 body calls PlayAction(700). Read-only.
HOOK_DEFINE_TRAMPOLINE(UjStartStateHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_uj_start_state_logs.fetch_add(1, std::memory_order_relaxed);
        uint32_t action_pre = 0xFFFFFFFFu;
        int32_t e60 = 0x7FFFFFFF, e94 = 0x7FFFFFFF, e9c = 0x7FFFFFFF;
        if (actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            action_pre = *reinterpret_cast<volatile uint32_t*>(b + 4712);
            e60 = *reinterpret_cast<volatile int32_t*>(b + 0xE60);
            e94 = *reinterpret_cast<volatile int32_t*>(b + 0xE94);
            e9c = *reinterpret_cast<volatile int32_t*>(b + 0xE9C);
        }
        if (valid && n < 1024) {
            Logging.Log("[NSC:P52A] UJ_STATE phase=pre actor=%p side=%u char=%u mode=%u action=%u e60=%d e94=%d e9c=%d n=%u",
                        actor, side, char_id, mode, action_pre, e60, e94, e9c, n);
        }
        Orig(actor, mode);
        if (valid && n < 1024 && actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            const uint32_t action_post = *reinterpret_cast<volatile uint32_t*>(b + 4712);
            Logging.Log("[NSC:P52A] UJ_STATE phase=post actor=%p side=%u char=%u mode=%u action=%u n=%u",
                        actor, side, char_id, mode, action_post, n);
        }
    }
};

// P52A: controller identified by exact xref to
// "CtrlAct_PL_ACT_NORMAL_SPTYPE_SPSKILL". It selects SPTYPE actions and passes
// 921..930 (including SPTYPE_ACTION10=930) into the native special-type path.
// Log first vanilla controls plus every generic custom-ID actor; do not alter behavior.
HOOK_DEFINE_TRAMPOLINE(SpecialTypeCtrlHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_special_type_ctrl_logs.fetch_add(1, std::memory_order_relaxed);
        uint32_t action_pre = 0xFFFFFFFFu;
        int32_t e60_pre = 0x7FFFFFFF, e94_pre = 0x7FFFFFFF, e9c_pre = 0x7FFFFFFF;
        if (actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            action_pre = *reinterpret_cast<volatile uint32_t*>(b + 4712);
            e60_pre = *reinterpret_cast<volatile int32_t*>(b + 0xE60);
            e94_pre = *reinterpret_cast<volatile int32_t*>(b + 0xE94);
            e9c_pre = *reinterpret_cast<volatile int32_t*>(b + 0xE9C);
        }
        const bool log_this = valid && (n < 192 || char_id >= kFirstCustomCharId);
        if (log_this && n < 4096) {
            Logging.Log("[NSC:P52A] SPTYPE_CTRL phase=pre actor=%p side=%u char=%u mode=%u action=%u e60=%d e94=%d e9c=%d n=%u",
                        actor, side, char_id, mode, action_pre, e60_pre, e94_pre, e9c_pre, n);
        }
        Orig(actor, mode);
        if (log_this && n < 4096 && actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            const uint32_t action_post = *reinterpret_cast<volatile uint32_t*>(b + 4712);
            const int32_t e60_post = *reinterpret_cast<volatile int32_t*>(b + 0xE60);
            const int32_t e94_post = *reinterpret_cast<volatile int32_t*>(b + 0xE94);
            const int32_t e9c_post = *reinterpret_cast<volatile int32_t*>(b + 0xE9C);
            Logging.Log("[NSC:P52A] SPTYPE_CTRL phase=post actor=%p side=%u char=%u mode=%u action=%u e60=%d e94=%d e9c=%d n=%u",
                        actor, side, char_id, mode, action_post, e60_post, e94_post, e9c_post, n);
        }
    }
};

HOOK_DEFINE_TRAMPOLINE(StageHandleHook) {
    static void Callback(uint32_t stage_id) {
        const uint32_t n = g_stage_handle_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256) Logging.Log("[NSC:P50A] STAGE_HANDLE phase=0 stage=%u", stage_id);
        Orig(stage_id);
        if (n < 256) Logging.Log("[NSC:P50A] STAGE_HANDLE phase=1 stage=%u", stage_id);
    }
};

HOOK_DEFINE_TRAMPOLINE(FixCharPositionHook) {
    static void Callback(void* actor) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_fix_char_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 384) {
            Logging.Log("[NSC:P50A] FIX_CHAR phase=0 actor=%p valid=%u side=%u char=%u",
                        actor, valid ? 1u : 0u, side, char_id);
        }
        Orig(actor);
        if (n < 384) {
            uint32_t side2 = 0xFFFFFFFFu, char2 = 0xFFFFFFFFu;
            const bool valid2 = ReadActorIdentity(actor, side2, char2);
            Logging.Log("[NSC:P50A] FIX_CHAR phase=1 actor=%p valid=%u side=%u char=%u",
                        actor, valid2 ? 1u : 0u, side2, char2);
        }
    }
};

HOOK_DEFINE_TRAMPOLINE(PostStageHook) {
    static void Callback() {
        const uint32_t n = g_post_stage_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256) Logging.Log("[NSC:P50A] POST_STAGE phase=0");
        Orig();
        if (n < 256) Logging.Log("[NSC:P50A] POST_STAGE phase=1");
    }
};

// P43A: O14 pure shadow (layout rejected) + explicit OP15/17/18 Kamui shadows.
// ME_ENEMY_DISP_OFF, but UltimateStormAPI uses event236 as an extension
// container with opcode at +0x24. Valid extension opcodes never fall back to
// native enemy-hide; unported operations are intentionally shadow/no-op.
HOOK_DEFINE_TRAMPOLINE(Event236Hook) {
    static uint32_t Callback(void* actor, void* event_ptr) {
        if (!actor || !event_ptr) return Orig(actor, event_ptr);

        auto* actor_bytes = reinterpret_cast<volatile uint8_t*>(actor);
        const uint32_t side = *reinterpret_cast<volatile uint32_t*>(actor_bytes + 0xE50);
        const uint32_t char_id = *reinterpret_cast<volatile uint32_t*>(actor_bytes + 0xE54);
        auto* event = reinterpret_cast<const uint8_t*>(event_ptr);
        const int16_t op = *reinterpret_cast<const int16_t*>(event + 0x24);
        const int16_t p2 = *reinterpret_cast<const int16_t*>(event + 0x26);
        const int16_t p3 = *reinterpret_cast<const int16_t*>(event + 0x28);
        const float p4 = *reinterpret_cast<const float*>(event + 0x2C);
        const P55ActorState p55_pre = ReadP55ActorState(actor);

        // Fail closed to exact native semantics for vanilla/non-custom actors or
        // implausible event data. v1.70 vanilla max charID is proven as 280;
        // custom compiler IDs begin at 281, so this remains generic for future mods.
        if (side > 1 || char_id <= kVanillaMaxCharId || char_id >= 0x1000 ||
            op < 1 || op > 29) {
            return Orig(actor, event_ptr);
        }

        if (ShouldTraceEvent236(op, p3) &&
            g_event236_logs.fetch_add(1, std::memory_order_relaxed) < 2048) {
            char text[31]{};
            CopyEventText(text, event);
            Logging.Log("[NSC:P50A] EVT236 actor=%p side=%u char=%u op=%d p2=%d p3=%d p4bits=%08x text=%s",
                        actor, side, char_id, static_cast<int>(op), static_cast<int>(p2),
                        static_cast<int>(p3), FloatBits(p4), text);
            if (op == 3 || op == 8 || op == 13 || op == 22 || op == 23) {
                Logging.Log("[NSC:P55A] STATE236 phase=pre actor=%p side=%u char=%u op=%d p2=%d p3=%d action=%u e60=%d e94=%d e9c=%d ea0=%d skills=%u/%u/%u",
                            actor, side, char_id, static_cast<int>(op), static_cast<int>(p2),
                            static_cast<int>(p3), p55_pre.action, p55_pre.e60, p55_pre.e94,
                            p55_pre.e9c, p55_pre.ea0, p55_pre.skill0, p55_pre.skill1,
                            p55_pre.skill2);
            }
        }

        switch (op) {
            case 2: // source me_test_switch_stage
                return HandleStageMove(actor, event, p2);

            case 3: { // source me_change_skill
                if (p2 < 0 || p2 > 2 || p3 < 0 || p3 > 6) return 1;
                auto* slot = reinterpret_cast<volatile uint32_t*>(
                    reinterpret_cast<uint8_t*>(actor) + 0xE68 + static_cast<uint32_t>(p2) * 4);
                const uint32_t current = *slot;
                if (current <= 6) *slot = static_cast<uint32_t>(p3);
                const P55ActorState p55_post = ReadP55ActorState(actor);
                Logging.Log("[NSC:P55A] SKILL_WRITE actor=%p side=%u char=%u slot=%d requested=%d old=%u new=%u action=%u e60=%d e94=%d e9c=%d ea0=%d skills=%u/%u/%u",
                            actor, side, char_id, static_cast<int>(p2), static_cast<int>(p3),
                            current, *slot, p55_post.action, p55_post.e60, p55_post.e94,
                            p55_post.e9c, p55_post.ea0, p55_post.skill0, p55_post.skill1,
                            p55_post.skill2);
                return 1;
            }

            case 4: { // source me_change_speed
                if (p2 < 0 || p2 > 1 || !IsFiniteAbsLe16(p4)) return 1;
                void* target = GetEventTargetActor(actor, p2);
                if (!target) return 1;
                auto* speed = reinterpret_cast<volatile float*>(reinterpret_cast<uint8_t*>(target) + 0x214);
                const float old = *speed;
                if (IsFiniteAbsLe16(old)) *speed = p4;
                return 1;
            }

            case 8: { // source me_change_walk_speed
                if (!IsFiniteAbsLe16(p4)) return 1;
                auto* walk = reinterpret_cast<volatile float*>(reinterpret_cast<uint8_t*>(actor) + 0x10D34);
                const float old = *walk;
                if (IsFiniteAbsLe16(old)) *walk = p4;
                return 1;
            }

            case 12: { // P43A inherited A/B: shadow source me_SetPlayerVisibility only
                // P34A (all event236 no-op) made victim-UJ restore normal, while
                // P35A/P36 re-enabled O12/O14/... and conditional disappearance returned.
                // Do NOT mutate visibility in this build; O14 is independently shadowed below for P39A.
                if (g_event235_logs.fetch_add(1, std::memory_order_relaxed) < 256) {
                    Logging.Log("[NSC:P50A] VIS_SHADOW actor=%p side=%u char=%u p2=%d",
                                actor, side, char_id, static_cast<int>(p2));
                }
                return 1;
            }

            case 13: // source me_enable_dpad_animation
                *reinterpret_cast<volatile int32_t*>(reinterpret_cast<uint8_t*>(actor) + 0xF30) = p2;
                return 1;

            case 14: {
                // P56B: source-grounded locator trigger. UltimateStormAPI's
                // me_enable_control uses p2=self/enemy and p3=control selector;
                // selector 1 is Ultimate Jutsu. Snapshot BEFORE the P50 shadow
                // so this is the untouched Switch state when the mod requests UJ enable.
                if (p2 == 0 && p3 == 1) {
                    const uint32_t seq = g_p56b_custom_snapshots.fetch_add(1, std::memory_order_relaxed);
                    if (seq < 3) LogP56BControlSnapshot(actor, "CUSTOM_O14_UJ_ENABLE", side, char_id, seq);
                }
                // P43A: pure shadow. P41A CTRL_DUMP rejected +0x12A24 as PC-style
                // boolean control block. Victim-UJ HARD PASS is from not calling the
                // broken native O14 route; direct writes were mostly fail-closed no-ops.
                if (g_event236_logs.load(std::memory_order_relaxed) < 4096) {
                    Logging.Log("[NSC:P50A] CTRL14_SHADOW actor=%p side=%u char=%u p2=%d p3=%d",
                                actor, side, char_id, static_cast<int>(p2), static_cast<int>(p3));
                }
                return 1;
            }

            case 15: {
                // P43A: explicit shadow for me_disable_control / disable path.
                // Logged for Kamui sequence reconstruction (seen repeatedly around UJ).
                if (g_event236_logs.load(std::memory_order_relaxed) < 4096) {
                    Logging.Log("[NSC:P50A] OP15_SHADOW actor=%p side=%u char=%u p2=%d p3=%d",
                                actor, side, char_id, static_cast<int>(p2), static_cast<int>(p3));
                }
                return 1;
            }

            case 17: {
                // P43A: explicit Kamui-candidate shadow. Previously fell through default.
                // A/B next: only flip this to a proven native/port after sequence evidence.
                if (g_event236_logs.load(std::memory_order_relaxed) < 4096) {
                    Logging.Log("[NSC:P50A] OP17_SHADOW actor=%p side=%u char=%u p2=%d p3=%d p4bits=%08x",
                                actor, side, char_id, static_cast<int>(p2), static_cast<int>(p3),
                                FloatBits(p4));
                }
                return 1;
            }

            case 18: {
                // P43A: explicit Kamui-candidate shadow. Previously fell through default.
                if (g_event236_logs.load(std::memory_order_relaxed) < 4096) {
                    Logging.Log("[NSC:P50A] OP18_SHADOW actor=%p side=%u char=%u p2=%d p3=%d p4bits=%08x",
                                actor, side, char_id, static_cast<int>(p2), static_cast<int>(p3),
                                FloatBits(p4));
                }
                return 1;
            }

            case 22: // source me_play_pl_anm
                return HandleActionAnimation(actor, event, p2, p3, false);

            case 23: // source me_play_action
                return HandleActionAnimation(actor, event, p2, p3, true);

            default:
                // Valid MovesetPlus opcode but not yet Switch-proven: shadow/no-op.
                // Critically, DO NOT call native ME_ENEMY_DISP_OFF here.
                return 1;
        }
    }
};


// P44A: OugiFinishParam Create — init-time only. Log once (or few) to confirm manager path.
// Fingerprint 8 words @ 0x4726E4:
//   D102C3FF A9057BFD A9066FFC A90767FA A9085FF8 A90957F6 A90A4FF4 F000AFB3
HOOK_DEFINE_TRAMPOLINE(OugiFinishCreateHook) {
    static void Callback(void* this_ptr) {
        const uint32_t n = g_ougi_finish_create_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 32) {
            Logging.Log("[NSC:P50A] OUGI_FINISH_CREATE this=%p n=%u", this_ptr, n);
        }
        Orig(this_ptr);
    }
};

// P45A: NORMAL_OUGI combat action handler (table-dispatched).
// Fingerprint @ 0x6F44A0:
//   F81F0FFE F000D268 F9424508 2A0003E1 F9762500 2A1F03E2 9400B71A 79401808
HOOK_DEFINE_TRAMPOLINE(NormalOugiHook) {
    static uint64_t Callback(uint64_t x0) {
        const uint32_t n = g_normal_ougi_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256) {
            Logging.Log("[NSC:P50A] NORMAL_OUGI x0=%p n=%u", reinterpret_cast<void*>(x0), n);
        }
        return Orig(x0);
    }
};

// P45A: SPECIAL_OUGI_FINISH combat action handler (table-dispatched).
// Fingerprint @ 0x6F4880:
//   F81F0FFE 7100001F 1A9F17E0 94062E11 B40000A0 52800081 94037B8E 7100001F
HOOK_DEFINE_TRAMPOLINE(SpecialOugiFinishHook) {
    static uint64_t Callback(uint64_t x0) {
        const uint32_t n = g_special_ougi_finish_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256) {
            Logging.Log("[NSC:P50A] SPECIAL_OUGI_FINISH x0=%p n=%u", reinterpret_cast<void*>(x0), n);
        }
        return Orig(x0);
    }
};

// P53A: zero-extra-trampoline action-route probe. The already-proven PlayAction
// hook now observes the ordinary jutsu route (84), SPTYPE action10 (930), and
// the cinematic UJ range (700..740). This distinguishes XXA->UJ from XXA->XA
// without adding another hook or changing any gameplay decision.
// Fingerprint @ 0x766B8C:
//   A9BE57FE A9014FF4 B9529408 2A0403F4 AA0003F3 7100091F 54000080 B9528668
HOOK_DEFINE_TRAMPOLINE(PlayActionProbeHook) {
    static int32_t Callback(void* actor, int32_t index, int32_t a2, int32_t a3, int32_t a4, int32_t a5, float rate) {
        const bool ordinary_jutsu = index == 84;
        const bool direct_cluster_action = index == 98 || index == 100 || index == 937 || index == 938;
        const bool uj = index >= 700 && index <= 740;
        const bool sptype_action10 = index == 930;
        const bool relevant = ordinary_jutsu || direct_cluster_action || uj || sptype_action10;
        if (!relevant) {
            return Orig(actor, index, a2, a3, a4, a5, rate);
        }

        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        if (index == 700 && valid && char_id <= kVanillaMaxCharId) {
            const uint32_t seq = g_p56b_vanilla_snapshots.fetch_add(1, std::memory_order_relaxed);
            if (seq < 2) LogP56BControlSnapshot(actor, "VANILLA_PLAY700", side, char_id, seq);
        }
        uint32_t pre_action = 0xFFFFFFFFu;
        const uintptr_t setter_target = ReadActionSetterTarget(actor);
        const ptrdiff_t setter_off = MainRelativeOffset(setter_target);
        if (actor) {
            pre_action = *reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        }

        const int32_t ret = Orig(actor, index, a2, a3, a4, a5, rate);

        uint32_t post_action = 0xFFFFFFFFu;
        if (actor) {
            post_action = *reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        }
        const char* route = ordinary_jutsu ? "JUTSU84" :
                            (index == 98 ? "PLAY98" :
                            (index == 100 ? "PLAY100" :
                            (index == 937 ? "PLAY937" :
                            (index == 938 ? "PLAY938" :
                            (sptype_action10 ? "SPTYPE930" : "UJ")))));
        const uint32_t n = g_play_action_logs.fetch_add(1, std::memory_order_relaxed);
        Logging.Log("[NSC:P55A] ACTION_ROUTE route=%s actor=%p valid=%u side=%u char=%u index=%d ret=%d n=%u a2=%d pre_action=%u post_action=%u setter=%p setter_off=0x%lx",
                    route, actor, valid ? 1u : 0u, side, char_id, index, ret, n, a2,
                    pre_action, post_action, reinterpret_cast<void*>(setter_target),
                    static_cast<unsigned long>(setter_off));
        return ret;
    }
};

// P57A: central action-setter provenance trace. This is diagnostic only.
//
// Runtime provenance:
//   actor vtable+0xF98 -> main+0x766320 for vanilla UJ action700..740.
// Static ABI provenance from the first instructions of 0x766320:
//   mov w20,w3; mov w22,w2; mov x19,x0; mov w21,w1
// so the entry contract is (actor, action, a2, a3). The PlayAction wrapper
// does not consume a return value from this call, therefore Callback is void.
//
// We log every valid generic custom actor request and only vanilla UJ requests.
// No action/argument/actor field is modified.
HOOK_DEFINE_TRAMPOLINE(CentralActionSetterHook) {
    static void Callback(void* actor, int32_t action, int32_t a2, int32_t a3) {
        uintptr_t caller_lr = 0;
        asm volatile("mov %0, x30" : "=r"(caller_lr));

        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const bool custom = valid && char_id > kVanillaMaxCharId && char_id < 0x1000u;
        const bool vanilla_uj = valid && char_id <= kVanillaMaxCharId && action >= 700 && action <= 740;
        const bool log_this = custom || vanilla_uj;

        uint32_t pre_action = 0xFFFFFFFFu;
        int32_t pre_e94 = 0x7FFFFFFF;
        if (actor) {
            const auto* b = reinterpret_cast<const volatile uint8_t*>(actor);
            pre_action = *reinterpret_cast<const volatile uint32_t*>(b + 4712);
            pre_e94 = *reinterpret_cast<const volatile int32_t*>(b + 0xE94);
        }

        const ptrdiff_t caller_off = MainRelativeOffset(caller_lr);
        uint32_t call_m8 = 0, call_m4 = 0;
        if (caller_off >= 8) {
            const uintptr_t base = exl::util::modules::GetTargetStart();
            call_m8 = *reinterpret_cast<const volatile uint32_t*>(base + caller_off - 8);
            call_m4 = *reinterpret_cast<const volatile uint32_t*>(base + caller_off - 4);
        }

        Orig(actor, action, a2, a3);

        uint32_t post_action = 0xFFFFFFFFu;
        int32_t post_e94 = 0x7FFFFFFF;
        if (actor) {
            const auto* b = reinterpret_cast<const volatile uint8_t*>(actor);
            post_action = *reinterpret_cast<const volatile uint32_t*>(b + 4712);
            post_e94 = *reinterpret_cast<const volatile int32_t*>(b + 0xE94);
        }

        if (log_this) {
            const uint32_t n = g_p57_setter_logs.fetch_add(1, std::memory_order_relaxed);
            if (n < 4096) {
                Logging.Log("[NSC:P57A] SETTER n=%u actor=%p valid=%u side=%u char=%u requested=%d a2=%d a3=%d pre=%u post=%u e94=%d->%d caller_lr=%p caller_main=%u caller_off=0x%lx call_m8=%08x call_m4=%08x",
                            n, actor, valid ? 1u : 0u, side, char_id, action, a2, a3,
                            pre_action, post_action, pre_e94, post_e94,
                            reinterpret_cast<void*>(caller_lr), caller_off >= 0 ? 1u : 0u,
                            static_cast<unsigned long>(caller_off), call_m8, call_m4);
            }
        }
    }
};

// P54A: direct-action owner probes.  P53A proved that the visible Tobi jutsu
// produced by XXA does NOT pass through PlayAction(84/930/700..740).  Static
// v1.70 RE found two neighbouring controller functions that bypass PlayAction
// and call actor vtable+0xF98 directly with action 98 and 100 respectively.
// These entry hooks never change mode, action, actor fields, or return state.
//
// Fingerprint @ 0x2A472C:
//   D10243FF FD0023E8 F90027FE A90567FA A9065FF8 A90757F6 A9084FF4 52848C08
HOOK_DEFINE_TRAMPOLINE(DirectAction98OwnerHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uintptr_t setter_target = ReadActionSetterTarget(actor);
        const ptrdiff_t setter_off = MainRelativeOffset(setter_target);
        uint32_t pre_action = 0xFFFFFFFFu;
        int32_t pre_e94 = -1, pre_e9c = -1, pre_ea0 = -1;
        if (actor) {
            auto* b = reinterpret_cast<const volatile uint8_t*>(actor);
            pre_action = *reinterpret_cast<const volatile uint32_t*>(b + 4712);
            pre_e94 = *reinterpret_cast<const volatile int32_t*>(b + 0xE94);
            pre_e9c = *reinterpret_cast<const volatile int32_t*>(b + 0xE9C);
            pre_ea0 = *reinterpret_cast<const volatile int32_t*>(b + 0xEA0);
        }
        Orig(actor, mode);
        uint32_t post_action = 0xFFFFFFFFu;
        if (actor) {
            post_action = *reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        }
        const uint32_t n = g_direct98_owner_logs.fetch_add(1, std::memory_order_relaxed);
        if (valid && (char_id >= kFirstCustomCharId || side == 0u) && n < 512) {
            Logging.Log("[NSC:P54A] DIRECT98_OWNER actor=%p side=%u char=%u mode=%u pre_action=%u post_action=%u e94=%d e9c=%d ea0=%d setter=%p setter_off=0x%lx n=%u",
                        actor, side, char_id, mode, pre_action, post_action,
                        pre_e94, pre_e9c, pre_ea0, reinterpret_cast<void*>(setter_target),
                        static_cast<unsigned long>(setter_off), n);
        }
    }
};

// Fingerprint @ 0x2A51B8:
//   F81D0FFE A90157F6 A9024FF4 7100203F 54000C48 5280D588 72A00028 F000C469
HOOK_DEFINE_TRAMPOLINE(DirectAction100OwnerHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uintptr_t setter_target = ReadActionSetterTarget(actor);
        const ptrdiff_t setter_off = MainRelativeOffset(setter_target);
        uint32_t pre_action = 0xFFFFFFFFu;
        int32_t pre_e94 = -1, pre_e9c = -1, pre_ea0 = -1;
        if (actor) {
            auto* b = reinterpret_cast<const volatile uint8_t*>(actor);
            pre_action = *reinterpret_cast<const volatile uint32_t*>(b + 4712);
            pre_e94 = *reinterpret_cast<const volatile int32_t*>(b + 0xE94);
            pre_e9c = *reinterpret_cast<const volatile int32_t*>(b + 0xE9C);
            pre_ea0 = *reinterpret_cast<const volatile int32_t*>(b + 0xEA0);
        }
        Orig(actor, mode);
        uint32_t post_action = 0xFFFFFFFFu;
        if (actor) {
            post_action = *reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        }
        const uint32_t n = g_direct100_owner_logs.fetch_add(1, std::memory_order_relaxed);
        if (valid && (char_id >= kFirstCustomCharId || side == 0u) && n < 512) {
            Logging.Log("[NSC:P54A] DIRECT100_OWNER actor=%p side=%u char=%u mode=%u pre_action=%u post_action=%u e94=%d e9c=%d ea0=%d setter=%p setter_off=0x%lx n=%u",
                        actor, side, char_id, mode, pre_action, post_action,
                        pre_e94, pre_e9c, pre_ea0, reinterpret_cast<void*>(setter_target),
                        static_cast<unsigned long>(setter_off), n);
        }
    }
};

// P50A: low-perturbation action entry lookup / availability resolver.
// Only UJ-range indexes 700..740 are inspected; all other calls go straight to Orig().
// Fingerprint @ 0x768E84:
//   A9BE57FE A9014FF4 B94E5408 2A0203F5 2A0103F3 AA0003F4 7100411F 54000081
HOOK_DEFINE_TRAMPOLINE(ActionLookupProbeHook) {
    static void* Callback(void* actor, int32_t index, int32_t flag) {
        if (index < 700 || index > 740) {
            return Orig(actor, index, flag);
        }

        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        uint32_t pre_action = 0xFFFFFFFFu;
        if (actor) {
            pre_action = *reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        }

        void* const result = Orig(actor, index, flag);

        uint32_t post_action = 0xFFFFFFFFu;
        if (actor) {
            post_action = *reinterpret_cast<const volatile uint32_t*>(
                reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        }
        const uint32_t n = g_action_lookup_logs.fetch_add(1, std::memory_order_relaxed);
        Logging.Log("[NSC:P50A] ACTION_LOOKUP actor=%p valid=%u side=%u char=%u index=%d flag=%d result=%p n=%u pre_action=%u post_action=%u",
                    actor, valid ? 1u : 0u, side, char_id, index, flag, result, n,
                    pre_action, post_action);
        return result;
    }
};

// P50A: completion/timing gate used by the 707/708/709 state handler.
// Fingerprint @ 0x769A4C:
//   FC1D0FE8 A90157FE A9024FF4 AA0003F3 F9410C00 B4000160 97F34520 D000CEC8
HOOK_DEFINE_TRAMPOLINE(ActionGateProbeHook) {
    static uint32_t Callback(void* actor) {
        const uint32_t n = g_action_gate_logs.fetch_add(1, std::memory_order_relaxed);
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        uint32_t pre_action = 0xFFFFFFFFu;
        if (actor) pre_action = *reinterpret_cast<const volatile uint32_t*>(reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        const uint32_t ret = Orig(actor);
        uint32_t post_action = 0xFFFFFFFFu;
        if (actor) post_action = *reinterpret_cast<const volatile uint32_t*>(reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        const bool relevant = (pre_action >= 700 && pre_action <= 740) || (post_action >= 700 && post_action <= 740);
        if (relevant || n < 192) {
            Logging.Log("[NSC:P50A] ACTION_GATE actor=%p valid=%u side=%u char=%u ret=%u n=%u pre_action=%u post_action=%u",
                        actor, valid ? 1u : 0u, side, char_id, ret, n, pre_action, post_action);
        }
        return ret;
    }
};

// P50A: optional index remap called from ActionLookup when flag != 0.
// Fingerprint @ 0x769B04:
//   F81D0FFE A90157F6 A9024FF4 510AF028 2A0103F3 7103411F 54000588 AA0003F5
HOOK_DEFINE_TRAMPOLINE(ActionRemapProbeHook) {
    static int32_t Callback(void* actor, int32_t index) {
        const uint32_t n = g_action_remap_logs.fetch_add(1, std::memory_order_relaxed);
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        uint32_t action = 0xFFFFFFFFu;
        if (actor) action = *reinterpret_cast<const volatile uint32_t*>(reinterpret_cast<const volatile uint8_t*>(actor) + 4712);
        const int32_t resolved = Orig(actor, index);
        const bool relevant = (index >= 700 && index <= 740) || (resolved >= 700 && resolved <= 900) || (action >= 700 && action <= 740);
        if (relevant || n < 192) {
            Logging.Log("[NSC:P50A] ACTION_REMAP actor=%p valid=%u side=%u char=%u index=%d resolved=%d n=%u action=%u",
                        actor, valid ? 1u : 0u, side, char_id, index, resolved, n, action);
        }
        return resolved;
    }
};

bool InstallEvent236Dispatcher() {
    static constexpr uint32_t kEvent236Expected[] = {
        0xF81F0FFE, 0xF9400008, 0xF946E908, 0xD63F0100,
        0xB4000080, 0xF9400008, 0xF945E108, 0xD63F0100,
    };
    if (!MatchWords(kEvent236Offset, kEvent236Expected)) {
        LogFingerprintFail("EVENT236", kEvent236Offset);
        return false;
    }
    Event236Hook::InstallAtOffset(kEvent236Offset);
    return true;
}

[[maybe_unused]] bool InstallStateTrace() {
    static constexpr uint32_t kEvent13Expected[] = {
        0xF81E0FFE, 0xA9014FF4, 0x5281F014, 0x72A00034,
        0xAA0003F3, 0xF8746800, 0x97FD9CE5, 0xB912A27F,
    };
    static constexpr uint32_t kEvent121Expected[] = {
        0xA9BE57FE, 0xA9014FF4, 0xAA0103F3, 0x97FE0BA0,
        0xB4000180, 0xAA0003F4, 0x97FD3EFB, 0xAA1303E0,
    };
    static constexpr uint32_t kOugiCoreExpected[] = {
        0xD10103FF, 0xF9000BFE, 0xA90257F6, 0xA9034FF4,
        0xF9400008, 0x2A0103F5, 0xAA0003F3, 0xF946E908,
    };
    static constexpr uint32_t kOugiCallerExpected[] = {
        0xF81E0FFE, 0xA9014FF4, 0x2A0103F4, 0xAA0003F3,
        0x940D60E7, 0x34000094, 0xA9414FF4, 0xF84207FE,
    };
    bool ok = true;
    if (!MatchWords(kEvent13Offset, kEvent13Expected)) {
        LogFingerprintFail("EVENT13_AWAKE", kEvent13Offset); ok = false;
    }
    if (!MatchWords(kEvent121Offset, kEvent121Expected)) {
        LogFingerprintFail("EVENT121_COND", kEvent121Offset); ok = false;
    }
    if (!MatchWords(kOugiCoreOffset, kOugiCoreExpected)) {
        LogFingerprintFail("OUGI_CORE", kOugiCoreOffset); ok = false;
    }
    if (!MatchWords(kOugiCallerOffset, kOugiCallerExpected)) {
        LogFingerprintFail("OUGI_CALLER", kOugiCallerOffset); ok = false;
    }
    if (!ok) return false;
    Event13Hook::InstallAtOffset(kEvent13Offset);
    Event121Hook::InstallAtOffset(kEvent121Offset);
    OugiCoreHook::InstallAtOffset(kOugiCoreOffset);
    OugiCallerHook::InstallAtOffset(kOugiCallerOffset);
    return true;
}

[[maybe_unused]] bool InstallLifecycleTrace() {
    static constexpr uint32_t kEvent235Expected[] = {
        0xF81F0FFE, 0xF9400008, 0xF946E908, 0xD63F0100,
        0xB4000080, 0xF9400008, 0xF945DD08, 0xD63F0100,
    };
    static constexpr uint32_t kHandleExpected[] = {
        0xF81E0FFE, 0xA9014FF4, 0x9000D334, 0xF944C694,
        0x2A0003F3, 0xF9400280, 0x97FFE41A, 0xF000D2C8,
    };
    static constexpr uint32_t kFixExpected[] = {
        0xA9BD5FFE, 0xA90157F6, 0xA9024FF4, 0xAA0003F3,
        0x2A1F03F4, 0x52800028, 0x52848C16, 0x72A00036,
    };
    static constexpr uint32_t kPostExpected[] = {
        0xA9BF4FFE, 0x2A1F03E0, 0x2A1F03E1, 0x940FC6CA,
        0xB4000100, 0x52800021, 0xAA0003F3, 0x940BC56F,
    };

    bool ok = true;
    if (!MatchWords(kEvent235Offset, kEvent235Expected)) {
        LogFingerprintFail("EVENT235", kEvent235Offset); ok = false;
    }
    if (!MatchWords(kHandleStageChangeOffset, kHandleExpected)) {
        LogFingerprintFail("STAGE_HANDLE", kHandleStageChangeOffset); ok = false;
    }
    if (!MatchWords(kFixCharPositionOffset, kFixExpected)) {
        LogFingerprintFail("FIX_CHAR", kFixCharPositionOffset); ok = false;
    }
    if (!MatchWords(kPostStageOffset, kPostExpected)) {
        LogFingerprintFail("POST_STAGE", kPostStageOffset); ok = false;
    }
    if (!ok) return false;

    Event235Hook::InstallAtOffset(kEvent235Offset);
    StageHandleHook::InstallAtOffset(kHandleStageChangeOffset);
    FixCharPositionHook::InstallAtOffset(kFixCharPositionOffset);
    PostStageHook::InstallAtOffset(kPostStageOffset);
    return true;
}

bool InstallCpkBridge() {
    static constexpr uint32_t kExpected[] = {
        0xF81D0FFE, 0xA90157F6, 0xA9024FF4, 0xD000E6A8,
        0xF945ED08, 0xAA0003F5, 0xF9400100, 0xB4000200,
    };
    if (!MatchWords(kCpkBindOffset, kExpected)) {
        LogFingerprintFail("CPK_BIND", kCpkBindOffset);
        return false;
    }
    CpkBindHook::InstallAtOffset(kCpkBindOffset);
    return true;
}

[[maybe_unused]] bool InstallTraceHooks() {
    static constexpr uint32_t kCharExpected[] = {
        0xF000EA68, 0xF9424508, 0xF9760908, 0x2A0003E1, 0xF9409500, 0x1410AC93,
    };
    static constexpr uint32_t kRequestExpected[] = {
        0xF81D0FFE, 0xA90157F6, 0xA9024FF4, 0xF9400008,
        0xAA0203F4, 0xAA0103F6, 0xAA0003F3, 0xF9400908,
    };
    static constexpr uint32_t kCreateExpected[] = {
        0xD102C3FF, 0xF9003BFE, 0xA9085FF8, 0xA90957F6,
        0xA90A4FF4, 0xAA0203F6, 0xAA0103F5, 0xAA0003F4,
    };
    static constexpr uint32_t kStatusExpected[] = {
        0xF81F0FFE, 0x97FFFB36, 0xB4000060, 0xF84107FE,
        0x17FFF9D8, 0x52800080, 0xF84107FE, 0xD65F03C0,
    };
    static constexpr uint32_t kChunkExpected[] = {
        0xD100C3FF, 0xA90157FE, 0xA9024FF4, 0xAA0003F5,
        0xB000EAC0, 0xF942F000, 0xAA0103F3, 0xAA1503E1,
    };
    static constexpr uint32_t kProcessExpected[] = {
        0xA9BC7BFD, 0xA9015FF8, 0xA90257F6, 0xA9034FF4,
        0xD10A03FF, 0xD0019008, 0xB9807058, 0xAA0003F5,
    };
    static constexpr uint32_t kFileOpenExpected[] = {
        0xA9BD5FFE, 0xA90157F6, 0xA9024FF4, 0x6F00E400,
        0xAA0003F6, 0xB0007ED7, 0x3C838EC0, 0xB90106C2,
    };

    bool ok = true;
    if (!MatchWords(kCharacodeGetterOffset, kCharExpected)) {
        LogFingerprintFail("CHAR", kCharacodeGetterOffset); ok = false;
    }
    if (!MatchWords(kFileLoadRequestOffset, kRequestExpected)) {
        LogFingerprintFail("LOAD_REQ", kFileLoadRequestOffset); ok = false;
    }
    if (!MatchWords(kFileLoadCreateOffset, kCreateExpected)) {
        LogFingerprintFail("LOAD_CREATE", kFileLoadCreateOffset); ok = false;
    }
    if (!MatchWords(kFileLoadStatusOffset, kStatusExpected)) {
        LogFingerprintFail("LOAD_STATUS", kFileLoadStatusOffset); ok = false;
    }
    if (!MatchWords(kChunkBinaryOffset, kChunkExpected)) {
        LogFingerprintFail("CHUNK", kChunkBinaryOffset); ok = false;
    }
    if (!MatchWords(kLoadRequestProcessOffset, kProcessExpected)) {
        LogFingerprintFail("PROCESS", kLoadRequestProcessOffset); ok = false;
    }
    if (!MatchWords(kFileOpenOffset, kFileOpenExpected)) {
        LogFingerprintFail("FILE_OPEN", kFileOpenOffset); ok = false;
    }
    if (!ok) return false;

    CharacodeGetterHook::InstallAtOffset(kCharacodeGetterOffset);
    FileLoadRequestHook::InstallAtOffset(kFileLoadRequestOffset);
    FileLoadCreateHook::InstallAtOffset(kFileLoadCreateOffset);
    FileLoadStatusHook::InstallAtOffset(kFileLoadStatusOffset);
    ChunkBinaryHook::InstallAtOffset(kChunkBinaryOffset);
    LoadRequestProcessHook::InstallAtOffset(kLoadRequestProcessOffset);
    FileOpenHook::InstallAtOffset(kFileOpenOffset);
    return true;
}

bool InstallP52PreUjTraceHooks() {
    static constexpr uint32_t kUjWrapperExpected[] = {
        0xF81E0FFE, 0xA9014FF4, 0xAA0003F3, 0x34000201,
        0xAA1303E0, 0x2A0103F4, 0x940D6AF1, 0x71000A9F,
    };
    static constexpr uint32_t kUjStateExpected[] = {
        0xF81C0FFD, 0xA9015FFE, 0xA90257F6, 0xA9034FF4,
        0xD10943FF, 0x52979D08, 0xAA0003F3, 0x7100083F,
    };
    static constexpr uint32_t kSpecialTypeExpected[] = {
        0xD10203FF, 0xFD001BE8, 0xA90467FE, 0xA9055FF8,
        0xA90657F6, 0xA9074FF4, 0x7100203F, 0x54007F48,
    };
    static constexpr uint32_t kOugiCoreExpected[] = {
        0xD10103FF, 0xF9000BFE, 0xA90257F6, 0xA9034FF4,
        0xF9400008, 0x2A0103F5, 0xAA0003F3, 0xF946E908,
    };
    static constexpr uint32_t kOugiCallerExpected[] = {
        0xF81E0FFE, 0xA9014FF4, 0x2A0103F4, 0xAA0003F3,
        0x940D60E7, 0x34000094, 0xA9414FF4, 0xF84207FE,
    };
    bool ok = true;
    if (!MatchWords(kUjStartWrapperOffset, kUjWrapperExpected)) {
        LogFingerprintFail("P52_UJ_WRAPPER", kUjStartWrapperOffset); ok = false;
    }
    if (!MatchWords(kUjStartStateOffset, kUjStateExpected)) {
        LogFingerprintFail("P52_UJ_STATE", kUjStartStateOffset); ok = false;
    }
    if (!MatchWords(kSpecialTypeCtrlOffset, kSpecialTypeExpected)) {
        LogFingerprintFail("P52_SPTYPE_CTRL", kSpecialTypeCtrlOffset); ok = false;
    }
    if (!MatchWords(kOugiCoreOffset, kOugiCoreExpected)) {
        LogFingerprintFail("P52_OUGI_CORE", kOugiCoreOffset); ok = false;
    }
    if (!MatchWords(kOugiCallerOffset, kOugiCallerExpected)) {
        LogFingerprintFail("P52_OUGI_CALLER", kOugiCallerOffset); ok = false;
    }
    if (!ok) return false;
    UjStartWrapperHook::InstallAtOffset(kUjStartWrapperOffset);
    UjStartStateHook::InstallAtOffset(kUjStartStateOffset);
    SpecialTypeCtrlHook::InstallAtOffset(kSpecialTypeCtrlOffset);
    OugiCoreHook::InstallAtOffset(kOugiCoreOffset);
    OugiCallerHook::InstallAtOffset(kOugiCallerOffset);
    return true;
}

} // namespace

bool InstallPlayActionProbe() {
    static constexpr uint32_t kPlayActionExpected[] = {
        0xA9BE57FE, 0xA9014FF4, 0xB9529408, 0x2A0403F4,
        0xAA0003F3, 0x7100091F, 0x54000080, 0xB9528668,
    };
    if (!MatchWords(kPlayActionProbeOffset, kPlayActionExpected)) {
        LogFingerprintFail("PLAY_ACTION", kPlayActionProbeOffset);
        return false;
    }
    PlayActionProbeHook::InstallAtOffset(kPlayActionProbeOffset);
    return true;
}

bool InstallP57CentralSetterTrace() {
    // Fingerprint the exact v1.70 function entry. These words also prove the
    // 4-argument ABI used by the callback: prologue then w3/w2/x0/w1 saves.
    static constexpr uint32_t kSetterExpected[] = {
        0xD10303FF, 0x6D0523E9, 0xA9067BFD, 0xA9076FFC,
        0xA90867FA, 0xA9095FF8, 0xA90A57F6, 0xA90B4FF4,
        0xF9410C08, 0x4EA01C08, 0x2A0303F4, 0x2A0203F6,
        0xAA0003F3, 0x2A0103F5,
    };
    if (!MatchWords(kCentralActionSetterOffset, kSetterExpected)) {
        LogFingerprintFail("CENTRAL_SETTER", kCentralActionSetterOffset);
        return false;
    }
    CentralActionSetterHook::InstallAtOffset(kCentralActionSetterOffset);
    return true;
}

bool InstallP54DirectJutsuOwnerProbes() {
    static constexpr uint32_t kDirect98Expected[] = {
        0xD10243FF, 0xFD0023E8, 0xF90027FE, 0xA90567FA,
        0xA9065FF8, 0xA90757F6, 0xA9084FF4, 0x52848C08,
    };
    static constexpr uint32_t kDirect100Expected[] = {
        0xF81D0FFE, 0xA90157F6, 0xA9024FF4, 0x7100203F,
        0x54000C48, 0x5280D588, 0x72A00028, 0xF000C469,
    };
    bool ok = true;
    if (!MatchWords(kDirectAction98OwnerOffset, kDirect98Expected)) {
        LogFingerprintFail("P54_DIRECT98_OWNER", kDirectAction98OwnerOffset); ok = false;
    }
    if (!MatchWords(kDirectAction100OwnerOffset, kDirect100Expected)) {
        LogFingerprintFail("P54_DIRECT100_OWNER", kDirectAction100OwnerOffset); ok = false;
    }
    if (!ok) return false;
    DirectAction98OwnerHook::InstallAtOffset(kDirectAction98OwnerOffset);
    DirectAction100OwnerHook::InstallAtOffset(kDirectAction100OwnerOffset);
    return true;
}

bool InstallConditionCompat() {
    using namespace condition_compat_generated;
    static constexpr uint32_t kGetterExpected[] = {
        0xB000CFCA, 0xF9405D4A, 0x2A0003E9, 0x51000408,
        0x7107F91F, 0x8B091549, 0x9A8983E0, 0xD65F03C0,
    };
    static constexpr uint32_t kEvent121Expected[] = {
        0xA9BE57FE, 0xA9014FF4, 0xAA0103F3, 0x97FE0BA0,
        0xB4000180, 0xAA0003F4, 0x97FD3EFB, 0xAA1303E0,
    };

    // Paired-main fingerprints are derived from the generated manifest count.
    // Regenerating the condition table + paired main therefore stays data-driven.
    static_assert(kTotalConditionCount > kNativeConditionCount &&
                  kTotalConditionCount <= 0xFFFu,
                  "generated condition count must fit the paired-main immediates");
    static constexpr uint32_t kRawCountWord =
        0x52800000u | (kTotalConditionCount << 5) | 9u; // mov w9,#count
    static constexpr uint32_t kLoopW24Word =
        0x7100001Fu | (kTotalConditionCount << 10) | (24u << 5); // cmp w24,#count
    static constexpr uint32_t kLoopW19Word =
        0x7100001Fu | (kTotalConditionCount << 10) | (19u << 5); // cmp w19,#count
    static constexpr uint32_t kRawCountExpected[]  = {kRawCountWord};
    static constexpr uint32_t kLoopW24Expected[]   = {kLoopW24Word};
    static constexpr uint32_t kLoopW19Expected[]   = {kLoopW19Word};

    bool ok = true;
    if (!MatchWords(kConditionGetterOffset, kGetterExpected)) {
        LogFingerprintFail("COND_GETTER", kConditionGetterOffset); ok = false;
    }
    if (!MatchWords(kEvent121Offset, kEvent121Expected)) {
        LogFingerprintFail("EVENT121", kEvent121Offset); ok = false;
    }
    if (!MatchWords(kConditionRawCountOffset, kRawCountExpected)) {
        LogFingerprintFail("COND_RAW_COUNT", kConditionRawCountOffset); ok = false;
    }
    if (!MatchWords(kConditionNameLoop0Offset, kLoopW24Expected)) {
        LogFingerprintFail("COND_LOOP0", kConditionNameLoop0Offset); ok = false;
    }
    if (!MatchWords(kConditionNameLoop1Offset, kLoopW19Expected)) {
        LogFingerprintFail("COND_LOOP1", kConditionNameLoop1Offset); ok = false;
    }
    if (!MatchWords(kConditionHashLoopOffset, kLoopW19Expected)) {
        LogFingerprintFail("COND_HASH_LOOP", kConditionHashLoopOffset); ok = false;
    }
    if (!MatchWords(kConditionNameLoop2Offset, kLoopW19Expected)) {
        LogFingerprintFail("COND_LOOP2", kConditionNameLoop2Offset); ok = false;
    }
    if (!ok) return false;

    ConditionGetterHook::InstallAtOffset(kConditionGetterOffset);
    Event121Hook::InstallAtOffset(kEvent121Offset);
    return true;
}

void InstallP50AConditionCompat() {
    // Functional core: preserve the P48C Event236 compatibility behavior, add
    // the SC1.70 dynamic condition lookup port and custom Event121 SELF parity,
    // and keep only the already-proven PlayAction probe for UJ progression.
    // Active trampolines: CpkBind + Event236 + PlayAction + ConditionGetter + Event121.
    const bool cpk = InstallCpkBridge();
    const bool event236 = InstallEvent236Dispatcher();
    const bool play = InstallPlayActionProbe();
    const bool cond = InstallConditionCompat();
    Logging.Log("[NSC:P50A] READY cpk=%d event236=%d play=%d cond=%d installed_trampolines=5 "
                "condition_native=%u condition_extra=%u condition_total=%u "
                "event121_self=1 vis12_shadow=1 ctrl14_shadow=1 op15_shadow=1 op17_shadow=1 op18_shadow=1",
                cpk ? 1 : 0, event236 ? 1 : 0, play ? 1 : 0, cond ? 1 : 0,
                condition_compat_generated::kNativeConditionCount,
                condition_compat_generated::kExtraConditionCount,
                condition_compat_generated::kTotalConditionCount);
}


void InstallP53AInputPromotionProbe() {
    // P53A intentionally returns to the hardware-proven P50A five-trampoline
    // core. No P52A pre-UJ hooks are installed. The existing PlayAction hook
    // itself logs action 84 / 930 / 700..740, so there are zero extra
    // trampolines and zero gameplay writes in this probe.
    InstallP50AConditionCompat();
    Logging.Log("[NSC:P53A] READY inherited_p50=1 route_probe=1 added_trampolines=0 total_trampolines=5 "
                "jutsu_action=84 sptype_action10=930 uj_range=700-740");
}

void InstallP54ADirectJutsuProbe() {
    // P54A keeps the hardware-proven P50A five-trampoline functional core and
    // adds only the two direct-action owner probes proven above.  No gameplay
    // writes and no character-specific branch are introduced.
    InstallP50AConditionCompat();
    const bool direct = InstallP54DirectJutsuOwnerProbes();
    Logging.Log("[NSC:P54A] READY inherited_p50=1 direct_owner_probe=%d added_trampolines=2 total_trampolines=7 direct98_owner=0x2a472c direct100_owner=0x2a51b8",
                direct ? 1 : 0);
}

void InstallP55AStateSampler() {
    // P55A removes the eliminated P54 direct-owner probes and returns to the
    // five-trampoline P50 functional core. State is sampled only inside the
    // already-installed Event236/Event121/PlayAction callbacks: zero extra hooks.
    InstallP50AConditionCompat();
    Logging.Log("[NSC:P55A] READY inherited_p50=1 state_sampler=1 added_trampolines=0 total_trampolines=5 sample_event236=1 sample_event121=1 sample_playaction=1");
}


void InstallP56BControlLocator() {
    // P56B corrects the unsupported P55->74/77 causal leap. It adds ZERO
    // trampolines and ZERO gameplay writes. The existing P50 Event236 hook
    // snapshots custom selector1 (UJ-enable request); the existing PlayAction
    // hook snapshots vanilla at proven UJ entry 700. The bounded scan is read-only.
    InstallP50AConditionCompat();
    Logging.Log("[NSC:P56B] READY inherited_p50=1 control_locator=1 added_trampolines=0 total_trampolines=5 writes=0 scan_start=0x%x scan_end=0x%x custom_trigger=event236_op14_p2_0_p3_1 vanilla_trigger=play700",
                kControlScanStart, kControlScanEnd);
}

void InstallP57ACentralSetterTrace() {
    // P57A follows the P56B negative result: no common PC-style boolean control
    // block was located, so no actor field is guessed or written. Keep the
    // stable P50 functional core and add exactly one read-only central setter
    // hook to recover the actual custom action and its caller.
    InstallP50AConditionCompat();
    const bool setter = InstallP57CentralSetterTrace();
    Logging.Log("[NSC:P57A] READY inherited_p50=1 central_setter=%d added_trampolines=1 total_trampolines=6 writes=0 setter=0x766320 generic_custom_trace=1",
                setter ? 1 : 0);
}

void InstallP52APreUjProbe() {
    // P52A is deliberately diagnostic. Start from the hardware-proven P50A
    // functional core, then add five read-only decision/state traces.
    // Event121 is NOT installed twice. P51A's speculative main NOP is absent.
    InstallP50AConditionCompat();
    const bool trace = InstallP52PreUjTraceHooks();
    Logging.Log("[NSC:P52A] READY inherited_p50=1 preuj_trace=%d added_trampolines=5 total_trampolines=10 "
                "uj_wrapper=0x488958 uj_state=0x7e3534 sptype_ctrl=0x646190 ougi_caller=0x488bac ougi_core=0x7e0f58",
                trace ? 1 : 0);
}

} // namespace nsc
