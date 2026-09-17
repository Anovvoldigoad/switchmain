#include "nsc_cpk_bridge.hpp"

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

// Proven v1.70 native helpers used by the historical generic MovesetPlus event236 port.
constexpr ptrdiff_t kStageObjectLookupOffset   = 0xEC8A44;
constexpr ptrdiff_t kStageSpecificOffset       = 0x535F88;
constexpr ptrdiff_t kStageDefaultOffset        = 0x53643C;
constexpr ptrdiff_t kHandleStageChangeOffset   = 0x6E8EB0;
constexpr ptrdiff_t kFixCharPositionOffset     = 0x48E40C;
constexpr ptrdiff_t kPostStageOffset            = 0x48E61C;
// Actor-local MovesetPlus control block recovered for Switch v1.70.
// PC SC1.70 uses +0x12A34; established PC->Switch player layout shift is -0x10
// in this region, and historical Switch direct-control helper used +0x12A24.
constexpr ptrdiff_t kControlBlockOffset         = 0x12A24;
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
std::atomic<uint32_t> g_ctrl_dump_logs{0};
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

void CopyEventText(char (&out)[31], const uint8_t* event) {
    for (size_t i = 0; i < 30; ++i) {
        const uint8_t c = event ? event[i] : 0;
        if (!c) { out[i] = '\0'; return; }
        out[i] = (c >= 0x20 && c <= 0x7E) ? static_cast<char>(c) : '.';
    }
    out[30] = '\0';
}

bool ShouldTraceEvent236(int16_t op, int16_t /*p3*/) {
    // P41A focused trace: keep the complete custom Event236 sequence so a single
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

bool ControlRelativeOffset(int16_t control, uint32_t& out) {
    switch (control) {
        case 0:  out = 0x00; return true; // PL_ANM_ATK
        case 19: out = 0x04; return true; // PL_ANM_ATK_FAR / _ANOTHER
        case 1:  out = 0x08; return true; // Ultimate Jutsu
        case 2:  out = 0x10; return true; // Jutsus
        case 3:  out = 0x18; return true; // projectile land/attack
        case 18: out = 0x1C; return true; // chakra projectile land
        case 4:  out = 0x20; return true; // grab
        case 5:  out = 0x24; return true; // substitution
        case 6:  out = 0x28; return true; // guard
        case 7:  out = 0x2C; return true; // chakra load
        case 8:  out = 0x30; return true; // movement + chakra
        case 9:  out = 0x34; return true; // jump
        case 10: out = 0x38; return true; // ninja movement
        case 11: out = 0x3C; return true; // air dash
        case 12: out = 0x40; return true; // land dash
        case 13: out = 0x44; return true; // D-pad items
        case 14: out = 0x48; return true; // leader switch
        case 15: out = 0x4C; return true; // awakening
        case 16: out = 0x50; return true; // supports
        case 17: out = 0x58; return true; // counter attack
        default: return false;
    }
}

struct ControlWriteResult {
    void* target;
    bool valid;
    bool wrote;
    uint32_t relative;
    int32_t old_value;
};

ControlWriteResult EnableControlActorLocal(void* actor, int16_t enemy, int16_t control) {
    ControlWriteResult r{nullptr, false, false, 0, 0};
    void* target = GetEventTargetActor(actor, enemy);
    r.target = target;
    if (!target) return r;

    uint32_t relative = 0;
    if (!ControlRelativeOffset(control, relative)) return r;
    r.valid = true;
    r.relative = relative;

    auto* field = reinterpret_cast<volatile int32_t*>(
        reinterpret_cast<uint8_t*>(target) + kControlBlockOffset + relative);
    const int32_t old = *field;
    r.old_value = old;

    // Fail closed if this does not look like the expected boolean control block.
    // This keeps P41A from corrupting an unrelated structure if the candidate
    // base is wrong on hardware.
    if (old == 0 || old == 1) {
        *field = 1;
        r.wrote = true;
    }

    // Preserve the literal PC SC1.70 source fall-through for selector 19:
    // enabling far-attack also reaches case 1 and enables Ultimate Jutsu.
    if (control == 19) {
        auto* uj = reinterpret_cast<volatile int32_t*>(
            reinterpret_cast<uint8_t*>(target) + kControlBlockOffset + 0x08);
        const int32_t old_uj = *uj;
        if (old_uj == 0 || old_uj == 1) *uj = 1;
    }

    return r;
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
        Logging.Log("[NSC:P41A] ACTION actor=%p target=%p mode=%u text=%s found=0",
                    actor, target, action_mode ? 1u : 0u, text);
        return 1;
    }

    char text[31]{};
    CopyEventText(text, event);
    Logging.Log("[NSC:P41A] ACTION actor=%p target=%p mode=%u text=%s found=1 index=%u",
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
    Logging.Log("[NSC:P41A] fingerprint FAIL %s off=0x%lx word0=%08x", name,
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
        Logging.Log("[NSC:P41A] CPK_BIND path=%s priority=%d result=%u bind_id=%u",
                    kModCpkPath, kModCpkPriority, extra_result, extra_bind_id);
        return original_result;
    }
};

HOOK_DEFINE_TRAMPOLINE(CharacodeGetterHook) {
    static const char* Callback(uint32_t id) {
        const char* result = Orig(id);
        if (id > kVanillaMaxCharId && result && *result) TrackCustomCode(id, result);
        if (id >= kFirstCustomCharId && g_char_logs.fetch_add(1, std::memory_order_relaxed) < 96) {
            Logging.Log("[NSC:P41A] CHAR id=%u result=%p code=%s", id,
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
            Logging.Log("[NSC:P41A] LOAD_REQ manager=%p path=%s options=%p result=%p",
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
            Logging.Log("[NSC:P41A] LOAD_CREATE manager=%p path=%s options=%p result=%p",
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
                Logging.Log("[NSC:P41A] STATUS_TABLE_OVERFLOW max=%u",
                            static_cast<unsigned>(sizeof(g_status_entries) / sizeof(g_status_entries[0])));
            }
        }

        if (should_log &&
            g_status_transition_logs.fetch_add(1, std::memory_order_relaxed) < 1024) {
            Logging.Log("[NSC:P41A] LOAD_STATUS manager=%p path=%s first=%u prev=%u status=%u",
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
            Logging.Log("[NSC:P41A] CHUNK path=%s key=%s result=%p",
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
            Logging.Log("[NSC:P41A] FILE_OPEN request=%p path=%s slot=%u result=%u",
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

        Logging.Log("[NSC:P41A] PROCESS path=%s owner=%p readctx=%p load=%p status=%u readerr=%u",
                    path ? path : "<null>", owner, read_context, load_object,
                    load_status, read_error);
    }
};


// P41A: focused stage/cinematic victim-lifecycle trace inherited from P36. These wrappers are
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
            Logging.Log("[NSC:P41A] EVT235_SHOW actor=%p side=%u char=%u op=%d p2=%d p3=%d ret=%u",
                        actor, side, char_id, static_cast<int>(op), static_cast<int>(p2),
                        static_cast<int>(p3), result);
        }
        return result;
    }
};

// P41A: awakening-condition and UJ-state probes. These hooks are read-only and
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
                b + kControlBlockOffset + 0x4C);
            condition_owner = *reinterpret_cast<void* volatile*>(b + 0x10F80);
        }
        const uint32_t ret = Orig(actor, event_ptr);
        if (actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            post_gate = *reinterpret_cast<volatile int32_t*>(b + 0x12A0);
            post_awake = *reinterpret_cast<volatile int32_t*>(
                b + kControlBlockOffset + 0x4C);
        }
        if (valid && char_id > kVanillaMaxCharId &&
            g_event13_logs.fetch_add(1, std::memory_order_relaxed) < 256) {
            Logging.Log("[NSC:P41A] EVT13_AWAKE actor=%p side=%u char=%u event=%p cond_owner=%p gate=%d->%d ctrl15=%d->%d ret=%u",
                        actor, side, char_id, event_ptr, condition_owner,
                        pre_gate, post_gate, pre_awake, post_awake, ret);
        }
        return ret;
    }
};

HOOK_DEFINE_TRAMPOLINE(Event121Hook) {
    static uint32_t Callback(void* actor, void* event_ptr) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        char text[31]{};
        int16_t op = 0, p2 = 0, p3 = 0;
        uint32_t p4bits = 0;
        if (event_ptr) {
            const auto* event = reinterpret_cast<const uint8_t*>(event_ptr);
            CopyEventText(text, event);
            op = *reinterpret_cast<const int16_t*>(event + 0x24);
            p2 = *reinterpret_cast<const int16_t*>(event + 0x26);
            p3 = *reinterpret_cast<const int16_t*>(event + 0x28);
            p4bits = FloatBits(*reinterpret_cast<const float*>(event + 0x2C));
        }
        const uint32_t ret = Orig(actor, event_ptr);
        if (valid && char_id > kVanillaMaxCharId &&
            g_event121_logs.fetch_add(1, std::memory_order_relaxed) < 512) {
            Logging.Log("[NSC:P41A] EVT121_COND actor=%p side=%u char=%u event=%p text=%s op=%d p2=%d p3=%d p4bits=%08x ret=%u",
                        actor, side, char_id, event_ptr, text, static_cast<int>(op),
                        static_cast<int>(p2), static_cast<int>(p3), p4bits, ret);
        }
        return ret;
    }
};

HOOK_DEFINE_TRAMPOLINE(OugiCoreHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
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
        if (valid && char_id > kVanillaMaxCharId &&
            g_ougi_core_logs.fetch_add(1, std::memory_order_relaxed) < 512) {
            int32_t ea0_post = 0x7FFFFFFF, ea4_post = 0x7FFFFFFF, ea8_post = 0x7FFFFFFF;
            void* state_ptr_post = nullptr;
            if (actor) {
                auto* b = reinterpret_cast<volatile uint8_t*>(actor);
                ea0_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA0);
                ea4_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA4);
                ea8_post = *reinterpret_cast<volatile int32_t*>(b + 0xEA8);
                state_ptr_post = *reinterpret_cast<void* volatile*>(b + 0x1238);
            }
            Logging.Log("[NSC:P41A] OUGI_CORE actor=%p side=%u char=%u mode=%u state=%p->%p ea0=%d->%d ea4=%d->%d ea8=%d->%d",
                        actor, side, char_id, mode, state_ptr_pre, state_ptr_post,
                        ea0_pre, ea0_post, ea4_pre, ea4_post, ea8_pre, ea8_post);
        }
    }
};


// P41A: unique direct caller of Ougi core. Contract: x0=actor, w1=mode; return ignored.
// If Kamui never reaches this boundary either, the stuck handoff is upstream of UJ state entry.
HOOK_DEFINE_TRAMPOLINE(OugiCallerHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_ougi_caller_logs.fetch_add(1, std::memory_order_relaxed);
        if (valid && char_id > kVanillaMaxCharId && n < 512) {
            int32_t ea0 = 0x7FFFFFFF, ea4 = 0x7FFFFFFF, ea8 = 0x7FFFFFFF;
            void* state_ptr = nullptr;
            if (actor) {
                auto* b = reinterpret_cast<volatile uint8_t*>(actor);
                ea0 = *reinterpret_cast<volatile int32_t*>(b + 0xEA0);
                ea4 = *reinterpret_cast<volatile int32_t*>(b + 0xEA4);
                ea8 = *reinterpret_cast<volatile int32_t*>(b + 0xEA8);
                state_ptr = *reinterpret_cast<void* volatile*>(b + 0x1238);
            }
            Logging.Log("[NSC:P41A] OUGI_CALLER actor=%p side=%u char=%u mode=%u state=%p ea0=%d ea4=%d ea8=%d",
                        actor, side, char_id, mode, state_ptr, ea0, ea4, ea8);
        }
        Orig(actor, mode);
    }
};

HOOK_DEFINE_TRAMPOLINE(StageHandleHook) {
    static void Callback(uint32_t stage_id) {
        const uint32_t n = g_stage_handle_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256) Logging.Log("[NSC:P41A] STAGE_HANDLE phase=0 stage=%u", stage_id);
        Orig(stage_id);
        if (n < 256) Logging.Log("[NSC:P41A] STAGE_HANDLE phase=1 stage=%u", stage_id);
    }
};

HOOK_DEFINE_TRAMPOLINE(FixCharPositionHook) {
    static void Callback(void* actor) {
        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const uint32_t n = g_fix_char_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 384) {
            Logging.Log("[NSC:P41A] FIX_CHAR phase=0 actor=%p valid=%u side=%u char=%u",
                        actor, valid ? 1u : 0u, side, char_id);
        }
        Orig(actor);
        if (n < 384) {
            uint32_t side2 = 0xFFFFFFFFu, char2 = 0xFFFFFFFFu;
            const bool valid2 = ReadActorIdentity(actor, side2, char2);
            Logging.Log("[NSC:P41A] FIX_CHAR phase=1 actor=%p valid=%u side=%u char=%u",
                        actor, valid2 ? 1u : 0u, side2, char2);
        }
    }
};

HOOK_DEFINE_TRAMPOLINE(PostStageHook) {
    static void Callback() {
        const uint32_t n = g_post_stage_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256) Logging.Log("[NSC:P41A] POST_STAGE phase=0");
        Orig();
        if (n < 256) Logging.Log("[NSC:P41A] POST_STAGE phase=1");
    }
};

// P41A: P38A-safe baseline plus actor-local O14 direct-control parity candidate.
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
            Logging.Log("[NSC:P41A] EVT236 actor=%p side=%u char=%u op=%d p2=%d p3=%d p4bits=%08x text=%s",
                        actor, side, char_id, static_cast<int>(op), static_cast<int>(p2),
                        static_cast<int>(p3), FloatBits(p4), text);
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

            case 12: { // P41A inherited A/B: shadow source me_SetPlayerVisibility only
                // P34A (all event236 no-op) made victim-UJ restore normal, while
                // P35A/P36 re-enabled O12/O14/... and conditional disappearance returned.
                // Do NOT mutate visibility in this build; O14 is independently shadowed below for P39A.
                if (g_event235_logs.fetch_add(1, std::memory_order_relaxed) < 256) {
                    Logging.Log("[NSC:P41A] VIS_SHADOW actor=%p side=%u char=%u p2=%d",
                                actor, side, char_id, static_cast<int>(p2));
                }
                return 1;
            }

            case 13: // source me_enable_dpad_animation
                *reinterpret_cast<volatile int32_t*>(reinterpret_cast<uint8_t*>(actor) + 0xF30) = p2;
                return 1;

            case 14: { // P41A: actor-local me_enable_control source parity candidate
                const auto wr = EnableControlActorLocal(actor, p2, p3);
                if (g_event236_logs.load(std::memory_order_relaxed) < 4096) {
                    Logging.Log("[NSC:P41A] CTRL14_DIRECT actor=%p target=%p side=%u char=%u p2=%d p3=%d rel=%03x old=%d wrote=%u",
                                actor, wr.target, side, char_id, p2, p3, wr.relative, wr.old_value, wr.wrote ? 1u : 0u);
                }
                // P41A: one-shot control-block window dump to locate true boolean flags.
                // Dumps int32s at actor+0x12900 .. actor+0x12B00 (stride 4) for the first few custom O14 hits.
                const uint32_t dump_n = g_ctrl_dump_logs.fetch_add(1, std::memory_order_relaxed);
                if (dump_n < 4 && wr.target) {
                    auto* base = reinterpret_cast<volatile int32_t*>(
                        reinterpret_cast<uint8_t*>(wr.target) + 0x12900);
                    // 128 dwords = 0x200 bytes covering 0x12900..0x12B00
                    for (int row = 0; row < 16; ++row) {
                        const int off = row * 8;
                        Logging.Log("[NSC:P41A] CTRL_DUMP n=%u base+0x%03x: %d %d %d %d %d %d %d %d",
                                    dump_n, 0x12900 + off * 4,
                                    base[off+0], base[off+1], base[off+2], base[off+3],
                                    base[off+4], base[off+5], base[off+6], base[off+7]);
                    }
                }
                return 1;
            }

            case 15:
                // Historical safe Switch port intentionally treated disable_control as no-op.
                return 1;

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

bool InstallStateTrace() {
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

bool InstallLifecycleTrace() {
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

bool InstallTraceHooks() {
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

} // namespace

void InstallP41AControlDiag() {
    const bool cpk = InstallCpkBridge();
    const bool trace = InstallTraceHooks();
    const bool lifecycle = InstallLifecycleTrace();
    const bool state_trace = InstallStateTrace();
    const bool event236 = InstallEvent236Dispatcher();
    Logging.Log("[NSC:P41A] READY cpk=%d trace=%d lifecycle=%d state_trace=%d event236=%d vis12_shadow=1 ctrl14_direct=1 control_base=0x12a24 ctrl_dump=1 ougi_caller=1 evt13=0x%lx evt121=0x%lx ougi=0x%lx ougi_caller=0x%lx evt235=0x%lx evt236=0x%lx",
                cpk ? 1 : 0, trace ? 1 : 0, lifecycle ? 1 : 0, state_trace ? 1 : 0, event236 ? 1 : 0,
                static_cast<unsigned long>(kEvent13Offset),
                static_cast<unsigned long>(kEvent121Offset),
                static_cast<unsigned long>(kOugiCoreOffset),
                static_cast<unsigned long>(kOugiCallerOffset),
                static_cast<unsigned long>(kEvent235Offset),
                static_cast<unsigned long>(kEvent236Offset));
}

} // namespace nsc
