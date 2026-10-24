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

// P38: R266 read-only model registration stages, independently fingerprinted.
// These IDs belong to the MAIN function addresses, not a model characode.
constexpr ptrdiff_t kP38ModelChildCreateOffset = 0x6ECEE8;
constexpr ptrdiff_t kP38RegBridgeOffset        = 0x6ED110;
constexpr ptrdiff_t kP38RenderProducerOffset   = 0x594D8;


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
std::atomic<uint64_t> g_process_attempt_sequence{0};
std::atomic<uint32_t> g_status_overflow_once{0};
// Only log model/producer events after the custom mtob code is actually observed.
std::atomic<uint32_t> g_p38_armed{0};
std::atomic<uint32_t> g_p38_child_count{0};
std::atomic<uint32_t> g_p38_bridge_count{0};
std::atomic<uint32_t> g_p38_producer_count{0};

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

// Thread IDs provide reliable process-scope correlation across overlapping
// loads from different threads. Current-thread SVC is read-only; 0 marks an
// unavailable ID and must NOT be used by the P34 parser for definite pairing.
uint64_t CurrentThreadId() {
    u64 tid = 0;
    const Result result = svcGetThreadId(&tid, CUR_THREAD_HANDLE);
    return result == 0 ? static_cast<uint64_t>(tid) : 0;
}

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
    if (id == kFirstCustomCharId && BoundedEqual(code, "mtob")) {
        if (g_p38_armed.exchange(1u, std::memory_order_relaxed) == 0u)
            Logging.Log("[NSC:P38] ARM char=281 code=mtob trace_scope=post_custom_resolution");
    }
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
    // P32 preserves P31: trace every file path containing a discovered
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
    Logging.Log("[NSC:P32] fingerprint FAIL %s off=0x%lx word0=%08x", name,
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
        Logging.Log("[NSC:P32] CPK_BIND path=%s priority=%d result=%u bind_id=%u",
                    kModCpkPath, kModCpkPriority, extra_result, extra_bind_id);
        return original_result;
    }
};

HOOK_DEFINE_TRAMPOLINE(CharacodeGetterHook) {
    static const char* Callback(uint32_t id) {
        const char* result = Orig(id);
        if (id > kVanillaMaxCharId && result && *result) TrackCustomCode(id, result);
        if (id >= kFirstCustomCharId && g_char_logs.fetch_add(1, std::memory_order_relaxed) < 96) {
            Logging.Log("[NSC:P32] CHAR id=%u result=%p code=%s", id,
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
            Logging.Log("[NSC:P32] LOAD_REQ manager=%p path=%s options=%p result=%p",
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
            Logging.Log("[NSC:P32] LOAD_CREATE manager=%p path=%s options=%p result=%p",
                        manager, path ? path : "<null>", options, result);
        }
        return result;
    }
};

// Signature proven by 0x11617CC -> 0x1207EFC: x0=manager, x1=path.
// 0x1207EFC returns 4 itself when the path is absent from nuccFileLoadList.
// P32 keeps the first observed status for each custom path and subsequent
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
                Logging.Log("[NSC:P32] STATUS_TABLE_OVERFLOW max=%u",
                            static_cast<unsigned>(sizeof(g_status_entries) / sizeof(g_status_entries[0])));
            }
        }

        if (should_log &&
            g_status_transition_logs.fetch_add(1, std::memory_order_relaxed) < 1024) {
            Logging.Log("[NSC:P32] LOAD_STATUS manager=%p path=%s first=%u prev=%u status=%u",
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
            Logging.Log("[NSC:P32] CHUNK path=%s key=%s result=%p",
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
            const uint64_t tid = CurrentThreadId();
            Logging.Log("[NSC:P32] FILE_OPEN request=%p path=%s slot=%u result=%u",
                        request, path ? path : "<null>", slot, result);
            Logging.Log("[NSC:P34] FILE_OPEN tid=%llu path=%s request=%p slot=%u result=%u",
                        static_cast<unsigned long long>(tid),
                        path ? path : "<null>", request, slot, result);
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
        // Log process boundaries before/after Orig. FILE_OPEN is called from
        // this routine on the same native thread; a per-thread scope catches
        // retries and concurrent attempts without matching unrelated paths.
        const bool trace = IsInterestingPath(path) &&
            g_process_logs.fetch_add(1, std::memory_order_relaxed) < 512;
        const uint64_t attempt = trace ?
            g_process_attempt_sequence.fetch_add(1, std::memory_order_relaxed) + 1 : 0;
        const uint64_t tid = trace ? CurrentThreadId() : 0;
        if (trace) {
            Logging.Log("[NSC:P34] PROCESS_BEGIN tid=%llu attempt=%llu path=%s owner=%p readctx=%p load=%p",
                        static_cast<unsigned long long>(tid),
                        static_cast<unsigned long long>(attempt),
                        path ? path : "<null>", owner, read_context, load_object);
        }

        Orig(owner, read_context, load_object, path);

        if (!trace) return;

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

        Logging.Log("[NSC:P32] PROCESS path=%s owner=%p readctx=%p load=%p status=%u readerr=%u",
                    path ? path : "<null>", owner, read_context, load_object,
                    load_status, read_error);
        Logging.Log("[NSC:P34] PROCESS_END tid=%llu attempt=%llu path=%s status=%u readerr=%u",
                    static_cast<unsigned long long>(tid),
                    static_cast<unsigned long long>(attempt),
                    path ? path : "<null>", load_status, read_error);
    }
};

// P38: take only the read-only ABI/signature evidence from R266, not its
// hardcoded model identity38==46 (the R266 experiment was NOT a mtob proof).
// Observe all model identities after char281->mtob has been seen. There are
// deliberately no writes, resource substitutions, or gameplay return overrides.
struct P38ModelSnapshot {
    uint32_t identity38;
    uint32_t child_count;
    uint32_t flag2b68;
    uint32_t mode2b6c;
    uintptr_t begin2b38;
    uintptr_t end2b40;
};

P38ModelSnapshot P38ReadModel(void* model) {
    P38ModelSnapshot snap{0xFFFFFFFFu, 0xFFFFFFFFu, 0u, 0u, 0u, 0u};
    if (!model) return snap;
    const auto* b = reinterpret_cast<const volatile uint8_t*>(model);
    snap.identity38 = *reinterpret_cast<const volatile uint32_t*>(b + 0x38u);
    snap.begin2b38 = *reinterpret_cast<const volatile uintptr_t*>(b + 0x2B38u);
    snap.end2b40 = *reinterpret_cast<const volatile uintptr_t*>(b + 0x2B40u);
    snap.flag2b68 = *reinterpret_cast<const volatile uint32_t*>(b + 0x2B68u);
    snap.mode2b6c = *reinterpret_cast<const volatile uint32_t*>(b + 0x2B6Cu);
    if (snap.end2b40 >= snap.begin2b38) {
        const uintptr_t diff = snap.end2b40 - snap.begin2b38;
        if ((diff & (sizeof(uintptr_t) - 1)) == 0u && diff <= 4096u * sizeof(uintptr_t))
            snap.child_count = static_cast<uint32_t>(diff / sizeof(uintptr_t));
    }
    return snap;
}

HOOK_DEFINE_TRAMPOLINE(P38ModelChildCreateHook) {
    static void Callback(void* model, uint32_t selector, void* source_obj, uint32_t mode) {
        Orig(model, selector, source_obj, mode);
        if (g_p38_armed.load(std::memory_order_relaxed) == 0u || !model) return;
        const uint32_t seq = g_p38_child_count.fetch_add(1u, std::memory_order_relaxed);
        if (seq >= 512u) return;
        const auto snap = P38ReadModel(model);
        Logging.Log("[NSC:P38] CHILD seq=%u model=%p identity38=%u selector=%u mode=%u source=%p child_count=%u flag=%u reg_mode=%u",
                    seq, model, snap.identity38, selector, mode, source_obj,
                    snap.child_count, snap.flag2b68, snap.mode2b6c);
    }
};

HOOK_DEFINE_TRAMPOLINE(P38RegBridgeHook) {
    static void Callback(void* model, void* source_name_obj, uint32_t mode) {
        // Preserve native register/bridge behavior in all cases.
        if (g_p38_armed.load(std::memory_order_relaxed) != 0u && model) {
            const uint32_t seq = g_p38_bridge_count.fetch_add(1u, std::memory_order_relaxed);
            if (seq < 512u) {
                const auto snap = P38ReadModel(model);
                Logging.Log("[NSC:P38] BRIDGE seq=%u model=%p identity38=%u mode=%u source=%p child_count=%u flag=%u reg_mode=%u",
                            seq, model, snap.identity38, mode, source_name_obj,
                            snap.child_count, snap.flag2b68, snap.mode2b6c);
            }
        }
        Orig(model, source_name_obj, mode);
    }
};

HOOK_DEFINE_TRAMPOLINE(P38RenderProducerHook) {
    static void Callback(void* manager, void* resource, void* base90, void* name_a, void* name_b,
                         uint32_t mode, uint32_t slot, uint32_t identity) {
        if (g_p38_armed.load(std::memory_order_relaxed) != 0u) {
            const uint32_t seq = g_p38_producer_count.fetch_add(1u, std::memory_order_relaxed);
            if (seq < 512u) {
                Logging.Log("[NSC:P38] PRODUCER seq=%u manager=%p resource=%p base90=%p name_a=%p name_b=%p mode=%u slot=%u identity=%u",
                            seq, manager, resource, base90, name_a, name_b, mode, slot, identity);
            }
        }
        Orig(manager, resource, base90, name_a, name_b, mode, slot, identity);
    }
};

bool InstallP38RenderRegistrationProbe() {
    // P38 probes are optional: if main 1.70 fingerprints differ, do not hook.
    static constexpr uint32_t kChildExpected[] = {
        0xD10203FF,0xA9036FFE,0xA90467FA,0xA9055FF8,
        0xA90657F6,0xA9074FF4,0xF000D2A8,0xF9424508,
    };
    static constexpr uint32_t kBridgeExpected[] = {
        0xD10303FF,0xF9003BFE,0xA90867FA,0xA9095FF8,
        0xA90A57F6,0xA90B4FF4,0xD000D2B7,0xF94246F7,
    };
    static constexpr uint32_t kProducerExpected[] = {
        0xD107C3FF,0xFD00C3E8,0xA9197BFD,0xA91A6FFC,
        0xA91B67FA,0xA91C5FF8,0xA91D57F6,0xA91E4FF4,
    };
    const bool child = MatchWords(kP38ModelChildCreateOffset, kChildExpected);
    const bool bridge = MatchWords(kP38RegBridgeOffset, kBridgeExpected);
    const bool producer = MatchWords(kP38RenderProducerOffset, kProducerExpected);
    if (!child) LogFingerprintFail("P38_CHILD", kP38ModelChildCreateOffset);
    if (!bridge) LogFingerprintFail("P38_BRIDGE", kP38RegBridgeOffset);
    if (!producer) LogFingerprintFail("P38_PRODUCER", kP38RenderProducerOffset);
    if (!child || !bridge || !producer) {
        Logging.Log("[NSC:P38] READY installed=0 reason=fingerprint_mismatch hooks=0");
        return false;
    }
    P38ModelChildCreateHook::InstallAtOffset(kP38ModelChildCreateOffset);
    P38RegBridgeHook::InstallAtOffset(kP38RegBridgeOffset);
    P38RenderProducerHook::InstallAtOffset(kP38RenderProducerOffset);
    Logging.Log("[NSC:P38] READY installed=1 readonly=1 hooks=3 binder_unchanged=1 main_patch=0 original_model_id_46_filter_removed=1");
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

void InstallP32Trace() {
    const bool cpk = InstallCpkBridge();
    const bool trace = InstallTraceHooks();
    const bool render_probe = InstallP38RenderRegistrationProbe();
    Logging.Log("[NSC:P38] STATUS cpk=%u xfbin_trace=%u render_probe=%u",
                cpk ? 1u : 0u, trace ? 1u : 0u, render_probe ? 1u : 0u);
    Logging.Log("[NSC:P32] READY cpk=%d trace=%d req=0x%lx create=0x%lx status=0x%lx chunk=0x%lx process=0x%lx open=0x%lx",
                cpk ? 1 : 0, trace ? 1 : 0,
                static_cast<unsigned long>(kFileLoadRequestOffset),
                static_cast<unsigned long>(kFileLoadCreateOffset),
                static_cast<unsigned long>(kFileLoadStatusOffset),
                static_cast<unsigned long>(kChunkBinaryOffset),
                static_cast<unsigned long>(kLoadRequestProcessOffset),
                static_cast<unsigned long>(kFileOpenOffset));
}

} // namespace nsc
