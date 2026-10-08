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


// ===========================================================================
// R276H19AG - Adaptive Resource Compatibility Resolver
// No hardcoded character ID/code/donor/resource identity.
// ===========================================================================

static constexpr size_t kH19AGKeyCap = 128;
static constexpr size_t kH19AGAliasCap = 768;
static constexpr size_t kH19AGUnresolvedCap = 256;

struct H19AGAliasEntry {
    char alias[kH19AGKeyCap];
    char canonical[kH19AGKeyCap];
    bool ambiguous;
};

static H19AGAliasEntry g_h19ag_aliases[kH19AGAliasCap]{};
static size_t g_h19ag_alias_count = 0;
static std::atomic_flag g_h19ag_alias_lock = ATOMIC_FLAG_INIT;

static char g_h19ag_unresolved[kH19AGUnresolvedCap][kH19AGKeyCap]{};
static size_t g_h19ag_unresolved_count = 0;
static std::atomic_flag g_h19ag_unresolved_lock = ATOMIC_FLAG_INIT;

static std::atomic<uint32_t> g_h19ag_registry_success{0};
static std::atomic<uint32_t> g_h19ag_loaded_paths{0};
static std::atomic<uint32_t> g_h19ag_cache_hits{0};
static std::atomic<uint32_t> g_h19ag_transform_hits{0};

// R276H19AHB: compile-order fix only.
static bool H19AGCopy(char* dst, size_t cap, const char* src);
static bool H19AGEq(const char* a, const char* b);
static bool H19AGStarts(const char* s, const char* pfx);
static size_t H19AGLen(const char* s);
static void H19AGLock(std::atomic_flag& f);
static void H19AGUnlock(std::atomic_flag& f);

static constexpr size_t kH19AHCodeCap = 32;
static constexpr size_t kH19AHSeenCap = 384;

struct H19AHSeenEntry {
    char kind[20];
    char key[kH19AGKeyCap];
};

[[maybe_unused]] static char g_h19ah_code[kH19AHCodeCap]{};
[[maybe_unused]] static std::atomic<bool> g_h19ah_code_ready{false};
[[maybe_unused]] static std::atomic_flag g_h19ah_code_lock = ATOMIC_FLAG_INIT;

static H19AHSeenEntry g_h19ah_seen[kH19AHSeenCap]{};
static size_t g_h19ah_seen_count = 0;
static std::atomic_flag g_h19ah_seen_lock = ATOMIC_FLAG_INIT;

static bool H19AHContains(const char* s, const char* needle) {
    if (!s || !needle || !needle[0]) return false;
    for (size_t i = 0; s[i]; ++i) {
        size_t a = i;
        size_t b = 0;
        while (s[a] && needle[b] && s[a] == needle[b]) {
            ++a;
            ++b;
        }
        if (!needle[b]) return true;
    }
    return false;
}

static bool H19AHEndsWith(const char* s, const char* suffix) {
    if (!s || !suffix) return false;
    const size_t ns = H19AGLen(s);
    const size_t nx = H19AGLen(suffix);
    if (ns < nx) return false;
    for (size_t i = 0; i < nx; ++i) {
        if (s[ns - nx + i] != suffix[i]) return false;
    }
    return true;
}

static const char* H19AHStripScheme(const char* s) {
    if (!s) return s;
    if (H19AGStarts(s, "disc:")) return s + 5;
    if (H19AGStarts(s, "ROM:/")) return s + 5;
    if (H19AGStarts(s, "/")) return s + 1;
    return s;
}

// ===========================================================================
// R276H19AI — character-init-correlated resource graph
//
// H19AH incorrectly scoped to the first generic bod1 identity (1cmn).
// H19AI does not assume a numeric custom-ID boundary and does not hardcode
// a character code.
//
// Correlation:
//   body identity -> candidate code
//   native CharacodeGetter(id) -> id/code cache
//   H19X initializer(id) -> activate matching code
//
// A code can also activate when BOTH:
//   - its body identity has been observed, and
//   - CharacodeGetter resolves that same code.
//
// This excludes common resource stems such as 1cmn unless they are actually
// resolved as a character code.
// ===========================================================================

static constexpr size_t kH19AICodeCap = 32;
static constexpr size_t kH19AIBodyCap = 64;
static constexpr size_t kH19AICharMapCap = 96;
static constexpr size_t kH19AIActiveCap = 16;

struct H19AIBodyEntry {
    char code[kH19AICodeCap];
    char canonical[kH19AGKeyCap];
};

struct H19AICharEntry {
    uint32_t id;
    char code[kH19AICodeCap];
    bool valid;
};

static H19AIBodyEntry g_h19ai_bodies[kH19AIBodyCap]{};
static size_t g_h19ai_body_count = 0;
static std::atomic_flag g_h19ai_body_lock = ATOMIC_FLAG_INIT;

static H19AICharEntry g_h19ai_chars[kH19AICharMapCap]{};
static size_t g_h19ai_char_count = 0;
static std::atomic_flag g_h19ai_char_lock = ATOMIC_FLAG_INIT;

static char g_h19ai_active[kH19AIActiveCap][kH19AICodeCap]{};
static size_t g_h19ai_active_count = 0;
static std::atomic_flag g_h19ai_active_lock = ATOMIC_FLAG_INIT;

static std::atomic<uint32_t> g_h19ai_pending_id{0xFFFFFFFFu};

static bool H19AIContains(const char* s, const char* needle) {
    if (!s || !needle || !needle[0]) return false;
    for (size_t i = 0; s[i]; ++i) {
        size_t a = i;
        size_t b = 0;
        while (s[a] && needle[b] && s[a] == needle[b]) {
            ++a;
            ++b;
        }
        if (!needle[b]) return true;
    }
    return false;
}

static bool H19AIBodyKnown(const char* code, char* canonical, size_t cap) {
    if (!code || !code[0]) return false;

    bool found = false;
    H19AGLock(g_h19ai_body_lock);
    for (size_t i = 0; i < g_h19ai_body_count; ++i) {
        if (H19AGEq(g_h19ai_bodies[i].code, code)) {
            if (canonical && cap)
                H19AGCopy(canonical, cap, g_h19ai_bodies[i].canonical);
            found = true;
            break;
        }
    }
    H19AGUnlock(g_h19ai_body_lock);
    return found;
}

static void H19AIObserveBody(const char* code, const char* canonical) {
    if (!code || !code[0] || !canonical || !canonical[0]) return;

    H19AGLock(g_h19ai_body_lock);

    for (size_t i = 0; i < g_h19ai_body_count; ++i) {
        if (H19AGEq(g_h19ai_bodies[i].code, code)) {
            H19AGUnlock(g_h19ai_body_lock);
            return;
        }
    }

    if (g_h19ai_body_count < kH19AIBodyCap) {
        auto& e = g_h19ai_bodies[g_h19ai_body_count++];
        H19AGCopy(e.code, sizeof(e.code), code);
        H19AGCopy(e.canonical, sizeof(e.canonical), canonical);
    }

    H19AGUnlock(g_h19ai_body_lock);
}

static bool H19AIIsActive(const char* code) {
    if (!code || !code[0]) return false;

    bool found = false;
    H19AGLock(g_h19ai_active_lock);
    for (size_t i = 0; i < g_h19ai_active_count; ++i) {
        if (H19AGEq(g_h19ai_active[i], code)) {
            found = true;
            break;
        }
    }
    H19AGUnlock(g_h19ai_active_lock);
    return found;
}

static void H19AIActivateCode(uint32_t id, const char* code, const char* reason) {
    if (!code || !code[0]) return;
    if (H19AIIsActive(code)) return;

    bool added = false;
    H19AGLock(g_h19ai_active_lock);

    bool duplicate = false;
    for (size_t i = 0; i < g_h19ai_active_count; ++i) {
        if (H19AGEq(g_h19ai_active[i], code)) {
            duplicate = true;
            break;
        }
    }

    if (!duplicate && g_h19ai_active_count < kH19AIActiveCap) {
        H19AGCopy(g_h19ai_active[g_h19ai_active_count++],
                  kH19AICodeCap, code);
        added = true;
    }

    H19AGUnlock(g_h19ai_active_lock);

    if (added) {
        char body[kH19AGKeyCap]{};
        const bool body_known = H19AIBodyKnown(code, body, sizeof(body));

        Logging.Log("[NSC:H19AI] ACTIVATE id=%u code=%s reason=%s body=%s",
                    id,
                    code,
                    reason ? reason : "<none>",
                    body_known ? body : "<unknown>");
    }
}

static void H19AIObserveChar(uint32_t id, const char* code) {
    if (!code || !code[0]) return;

    H19AGLock(g_h19ai_char_lock);

    bool updated = false;
    for (size_t i = 0; i < g_h19ai_char_count; ++i) {
        if (g_h19ai_chars[i].valid && g_h19ai_chars[i].id == id) {
            H19AGCopy(g_h19ai_chars[i].code, sizeof(g_h19ai_chars[i].code), code);
            updated = true;
            break;
        }
    }

    if (!updated && g_h19ai_char_count < kH19AICharMapCap) {
        auto& e = g_h19ai_chars[g_h19ai_char_count++];
        e.id = id;
        e.valid = true;
        H19AGCopy(e.code, sizeof(e.code), code);
    }

    H19AGUnlock(g_h19ai_char_lock);

    if (H19AIBodyKnown(code, nullptr, 0))
        H19AIActivateCode(id, code, "body+char");

    const uint32_t pending =
        g_h19ai_pending_id.load(std::memory_order_acquire);
    if (pending == id)
        H19AIActivateCode(id, code, "h19x+char");
}

static void H19AIActivateId(uint32_t id) {
    g_h19ai_pending_id.store(id, std::memory_order_release);

    char code[kH19AICodeCap]{};
    bool found = false;

    H19AGLock(g_h19ai_char_lock);
    for (size_t i = 0; i < g_h19ai_char_count; ++i) {
        if (g_h19ai_chars[i].valid && g_h19ai_chars[i].id == id) {
            H19AGCopy(code, sizeof(code), g_h19ai_chars[i].code);
            found = true;
            break;
        }
    }
    H19AGUnlock(g_h19ai_char_lock);

    if (found)
        H19AIActivateCode(id, code, "h19x-id");
}

static bool H19AIRelevant(const char* key) {
    if (!key || !key[0]) return false;

    bool relevant = false;
    H19AGLock(g_h19ai_active_lock);
    for (size_t i = 0; i < g_h19ai_active_count; ++i) {
        if (H19AIContains(key, g_h19ai_active[i])) {
            relevant = true;
            break;
        }
    }
    H19AGUnlock(g_h19ai_active_lock);

    return relevant;
}


static void H19AHMaybeDiscoverCode(const char* canonical) {
    if (!canonical) return;

    const char* p = H19AHStripScheme(canonical);
    if (!p || !H19AGStarts(p, "data/spc/"))
        return;

    p += 9;

    const char* suffix = nullptr;
    if (H19AHEndsWith(p, "bod1.xfbin"))
        suffix = "bod1.xfbin";
    else if (H19AHEndsWith(p, "bod1"))
        suffix = "bod1";
    else
        return;

    const size_t np = H19AGLen(p);
    const size_t ns = H19AGLen(suffix);
    if (np <= ns)
        return;

    const size_t code_len = np - ns;
    if (code_len == 0 || code_len >= kH19AICodeCap)
        return;

    char code[kH19AICodeCap]{};
    for (size_t i = 0; i < code_len; ++i)
        code[i] = p[i];
    code[code_len] = '\0';

    H19AIObserveBody(code, canonical);
}

static bool H19AHRelevant(const char* key) {
    return H19AIRelevant(key);
}

static bool H19AHMarkSeen(const char* kind, const char* key) {
    if (!kind || !key) return false;

    bool fresh = false;
    H19AGLock(g_h19ah_seen_lock);

    for (size_t i = 0; i < g_h19ah_seen_count; ++i) {
        if (H19AGEq(g_h19ah_seen[i].kind, kind) &&
            H19AGEq(g_h19ah_seen[i].key, key)) {
            H19AGUnlock(g_h19ah_seen_lock);
            return false;
        }
    }

    if (g_h19ah_seen_count < kH19AHSeenCap) {
        auto& e = g_h19ah_seen[g_h19ah_seen_count++];
        H19AGCopy(e.kind, sizeof(e.kind), kind);
        H19AGCopy(e.key, sizeof(e.key), key);
        fresh = true;
    }

    H19AGUnlock(g_h19ah_seen_lock);
    return fresh;
}

static void H19AHTraceLoaded(const char* path) {
    H19AHMaybeDiscoverCode(path);

    if (!H19AHRelevant(path))
        return;

    if (H19AHMarkSeen("LOADED", path))
        Logging.Log("[NSC:H19AI] LOADED path=%s", path);
}

static void H19AHTraceRegistry(void* registry,
                               const char* key,
                               void* exact_result,
                               void* final_result,
                               const char* mode,
                               const char* alt) {
    if (final_result != nullptr) {
        H19AHMaybeDiscoverCode(key);
        if (alt && alt[0])
            H19AHMaybeDiscoverCode(alt);
    }

    const bool relevant =
        H19AHRelevant(key) || (alt && alt[0] && H19AHRelevant(alt));

    if (!relevant)
        return;

    if (exact_result != nullptr) {
        if (H19AHMarkSeen("EXACT", key))
            Logging.Log("[NSC:H19AI] EXACT registry=%p key=%s result=%p",
                        registry, key, exact_result);
        return;
    }

    if (final_result != nullptr) {
        const char* resolved_mode = (mode && mode[0]) ? mode : "FALLBACK";
        char dedupe_kind[20]{};
        H19AGCopy(dedupe_kind, sizeof(dedupe_kind), resolved_mode);

        if (H19AHMarkSeen(dedupe_kind, key))
            Logging.Log("[NSC:H19AI] RESOLVE mode=%s registry=%p key=%s alt=%s result=%p",
                        resolved_mode,
                        registry,
                        key,
                        (alt && alt[0]) ? alt : "<none>",
                        final_result);
        return;
    }

    if (H19AHMarkSeen("MISS", key))
        Logging.Log("[NSC:H19AI] MISS registry=%p key=%s", registry, key);
}


static bool H19AGCopy(char* dst, size_t cap, const char* src) {
    if (!dst || cap == 0 || !src) return false;
    size_t i = 0;
    for (; i + 1 < cap && src[i] != '\0'; ++i) dst[i] = src[i];
    dst[i] = '\0';
    return src[i] == '\0';
}

static bool H19AGEq(const char* a, const char* b) {
    if (!a || !b) return false;
    size_t i = 0;
    while (a[i] && b[i]) {
        if (a[i] != b[i]) return false;
        ++i;
    }
    return a[i] == b[i];
}

static bool H19AGStarts(const char* s, const char* pfx) {
    if (!s || !pfx) return false;
    size_t i = 0;
    while (pfx[i]) {
        if (s[i] != pfx[i]) return false;
        ++i;
    }
    return true;
}

static size_t H19AGLen(const char* s) {
    if (!s) return 0;
    size_t n = 0;
    while (n < kH19AGKeyCap - 1 && s[n]) ++n;
    return n;
}

static bool H19AGEndsXfbin(const char* s) {
    static constexpr char kSuffix[] = ".xfbin";
    constexpr size_t kSuffixLen = 6;
    const size_t n = H19AGLen(s);
    if (n < kSuffixLen) return false;
    for (size_t i = 0; i < kSuffixLen; ++i) {
        if (s[n - kSuffixLen + i] != kSuffix[i]) return false;
    }
    return true;
}

static bool H19AGMakeStripXfbin(const char* s, char* out, size_t cap) {
    if (!s || !out || !H19AGEndsXfbin(s)) return false;
    const size_t n = H19AGLen(s);
    if (n < 6 || n - 6 + 1 > cap) return false;
    size_t i = 0;
    for (; i < n - 6; ++i) out[i] = s[i];
    out[i] = '\0';
    return true;
}

static bool H19AGMakeAddXfbin(const char* s, char* out, size_t cap) {
    if (!s || !out) return false;
    static constexpr char kSuffix[] = ".xfbin";
    size_t p = 0;
    for (; s[p] && p + 1 < cap; ++p) out[p] = s[p];
    if (s[p] != '\0') return false;
    for (size_t i = 0; kSuffix[i] && p + 1 < cap; ++i) out[p++] = kSuffix[i];
    out[p] = '\0';
    return true;
}

static bool H19AGMakePrefix(const char* pfx, const char* s, char* out, size_t cap) {
    if (!pfx || !s || !out) return false;
    size_t p = 0;
    for (size_t i = 0; pfx[i] && p + 1 < cap; ++i) out[p++] = pfx[i];
    for (size_t i = 0; s[i] && p + 1 < cap; ++i) out[p++] = s[i];
    out[p] = '\0';
    return true;
}

static void H19AGLock(std::atomic_flag& f) {
    while (f.test_and_set(std::memory_order_acquire)) {}
}

static void H19AGUnlock(std::atomic_flag& f) {
    f.clear(std::memory_order_release);
}

static void H19AGAddAlias(const char* alias, const char* canonical) {
    if (!alias || !canonical || !alias[0] || !canonical[0]) return;
    if (H19AGEq(alias, canonical)) return;

    H19AGLock(g_h19ag_alias_lock);

    for (size_t i = 0; i < g_h19ag_alias_count; ++i) {
        if (!H19AGEq(g_h19ag_aliases[i].alias, alias)) continue;
        if (!H19AGEq(g_h19ag_aliases[i].canonical, canonical))
            g_h19ag_aliases[i].ambiguous = true;
        H19AGUnlock(g_h19ag_alias_lock);
        return;
    }

    if (g_h19ag_alias_count < kH19AGAliasCap) {
        auto& e = g_h19ag_aliases[g_h19ag_alias_count++];
        H19AGCopy(e.alias, sizeof(e.alias), alias);
        H19AGCopy(e.canonical, sizeof(e.canonical), canonical);
        e.ambiguous = false;
    }

    H19AGUnlock(g_h19ag_alias_lock);
}

static bool H19AGFindAlias(const char* alias, char* canonical, size_t cap) {
    if (!alias || !canonical || cap == 0) return false;

    bool found = false;
    H19AGLock(g_h19ag_alias_lock);

    for (size_t i = 0; i < g_h19ag_alias_count; ++i) {
        const auto& e = g_h19ag_aliases[i];
        if (!e.ambiguous && H19AGEq(e.alias, alias)) {
            found = H19AGCopy(canonical, cap, e.canonical);
            break;
        }
    }

    H19AGUnlock(g_h19ag_alias_lock);
    return found;
}

static void H19AGObserveCanonical(const char* canonical) {
    if (!canonical || !canonical[0]) return;

    char stripped[kH19AGKeyCap]{};
    char added[kH19AGKeyCap]{};

    if (H19AGStarts(canonical, "disc:data/"))
        H19AGAddAlias(canonical + 5, canonical);

    if (H19AGStarts(canonical, "/data/"))
        H19AGAddAlias(canonical + 1, canonical);

    if (H19AGStarts(canonical, "data/spc/"))
        H19AGAddAlias(canonical + 9, canonical);

    if (H19AGEndsXfbin(canonical)) {
        if (H19AGMakeStripXfbin(canonical, stripped, sizeof(stripped))) {
            H19AGAddAlias(stripped, canonical);

            if (H19AGStarts(canonical, "data/spc/"))
                H19AGAddAlias(stripped + 9, canonical);

            if (H19AGStarts(canonical, "disc:data/"))
                H19AGAddAlias(stripped + 5, canonical);

            if (H19AGStarts(canonical, "/data/"))
                H19AGAddAlias(stripped + 1, canonical);
        }
    } else {
        if (H19AGMakeAddXfbin(canonical, added, sizeof(added)))
            H19AGAddAlias(added, canonical);
    }
}

static void H19AGObserveRegistrySuccess(const char* key) {
    if (!key || !key[0]) return;
    g_h19ag_registry_success.fetch_add(1, std::memory_order_relaxed);
    H19AGObserveCanonical(key);
}

static void H19AGObserveLoadedPath(const char* path) {
    if (!path || !path[0]) return;
    g_h19ag_loaded_paths.fetch_add(1, std::memory_order_relaxed);
    H19AGObserveCanonical(path);
    H19AHTraceLoaded(path);
}

[[maybe_unused]] static void H19AGLogUnresolvedOnce(void* registry, const char* key) {
    if (!key || !key[0]) return;

    bool fresh = false;
    H19AGLock(g_h19ag_unresolved_lock);

    for (size_t i = 0; i < g_h19ag_unresolved_count; ++i) {
        if (H19AGEq(g_h19ag_unresolved[i], key)) {
            H19AGUnlock(g_h19ag_unresolved_lock);
            return;
        }
    }

    if (g_h19ag_unresolved_count < kH19AGUnresolvedCap) {
        H19AGCopy(g_h19ag_unresolved[g_h19ag_unresolved_count++],
                  kH19AGKeyCap, key);
        fresh = true;
    }

    H19AGUnlock(g_h19ag_unresolved_lock);

    if (fresh)
        Logging.Log("[NSC:H19AG] UNRESOLVED registry=%p key=%s", registry, key);
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
        H19AIObserveChar(id, result);
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
        if (status == 2 && path)
            H19AGObserveLoadedPath(path);
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
            Logging.Log("[NSC:P32] FILE_OPEN request=%p path=%s slot=%u result=%u",
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

        Logging.Log("[NSC:P32] PROCESS path=%s owner=%p readctx=%p load=%p status=%u readerr=%u",
                    path ? path : "<null>", owner, read_context, load_object,
                    load_status, read_error);
    }
};

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



// R276H19S: read-only trace for the proven null virtual call at main+0x11A1C20.
// Native chain at main+0x11A1C00:
//   child = *(arg0+0x18); vtable = *child; fn = *(vtable+0x10); BLR fn.
// This hook does not alter pointers, IDs, resources, or return state.
static std::atomic<uint32_t> g_h19s_vcall_logs{0};

HOOK_DEFINE_TRAMPOLINE(NullVcallTraceHook) {
    static void Callback(void* arg0, void* arg1) {
        void* child = nullptr;
        void* vtable = nullptr;
        void* slot10 = nullptr;
        uint32_t field170 = 0xFFFFFFFFu;
        uint32_t field172 = 0xFFFFFFFFu;

        if (arg0) {
            auto* p = reinterpret_cast<uint8_t*>(arg0);
            child = *reinterpret_cast<void**>(p + 0x18);
            field170 = *reinterpret_cast<volatile uint16_t*>(p + 0x170);
            field172 = *reinterpret_cast<volatile uint16_t*>(p + 0x172);
            if (child) {
                vtable = *reinterpret_cast<void**>(child);
                if (vtable) {
                    slot10 = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(vtable) + 0x10);
                }
            }
        }

        const uint32_t n = g_h19s_vcall_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256 || slot10 == nullptr) {
            Logging.Log("[NSC:H19S] VCALL n=%u arg0=%p arg1=%p child=%p vtable=%p slot10=%p f170=%u f172=%u",
                        n, arg0, arg1, child, vtable, slot10, field170, field172);
        }

        Orig(arg0, arg1);
    }
};



// R276H19U: read-only upstream trace for the object that feeds H19S.
// Proven native path:
//   main+0x439FDC: x25 = outer(arg0)
//   main+0x43A43C: x0 = *(x25+0x20)
//   main+0x43A440: x1 = sp+0x70
//   main+0x43A444: BL main+0x11A1C00
// H19S proved that callee arg0 is NULL, therefore outer+0x20 is the immediate missing pointer.
static std::atomic<uint32_t> g_h19u_outer_logs{0};

HOOK_DEFINE_TRAMPOLINE(OuterField20TraceHook) {
    static void Callback(void* outer, void* arg1, uint32_t arg2) {
        void* f18 = nullptr;
        void* f20 = nullptr;
        void* f28 = nullptr;
        void* f50 = nullptr;
        uint32_t f3608 = 0xFFFFFFFFu;

        if (outer) {
            auto* p = reinterpret_cast<uint8_t*>(outer);
            f18 = *reinterpret_cast<void**>(p + 0x18);
            f20 = *reinterpret_cast<void**>(p + 0x20);
            f28 = *reinterpret_cast<void**>(p + 0x28);
            f50 = *reinterpret_cast<void**>(p + 0x50);
            f3608 = *reinterpret_cast<volatile uint32_t*>(p + 0x3608);
        }

        const uint32_t n = g_h19u_outer_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 128 || f20 == nullptr) {
            Logging.Log("[NSC:H19U] OUTER n=%u outer=%p arg1=%p arg2=%u f18=%p f20=%p f28=%p f50=%p f3608=%u",
                        n, outer, arg1, arg2, f18, f20, f28, f50, f3608);
        }

        Orig(outer, arg1, arg2);
    }
};


// R276H19W: trace the exact native initializer that owns outer+0x20.
// Static v1.70 proof:
//   main+0x4332B4  BL 0x120A3D4
//   main+0x4332B8  CBZ X0, 0x433444
//   main+0x4332FC  STR X20,[X19,#0x20]
//   main+0x433444  STR XZR,[X19,#0x20]
static std::atomic<uint32_t> g_h19w_init_logs{0};
static std::atomic<uint32_t> g_h19w_lookup_logs{0};
static std::atomic<uintptr_t> g_h19w_active_outer{0};

HOOK_DEFINE_TRAMPOLINE(Field20InitTraceHook) {
    static void Callback(void* outer, void* arg1, void* arg2) {
        uint32_t id18 = 0xFFFFFFFFu;
        void* pre20 = nullptr;
        void* pre50 = nullptr;

        if (outer) {
            auto* p = reinterpret_cast<uint8_t*>(outer);
            id18 = *reinterpret_cast<volatile uint32_t*>(p + 0x18);
            pre20 = *reinterpret_cast<void**>(p + 0x20);
            pre50 = *reinterpret_cast<void**>(p + 0x50);
        }

        const uint32_t n = g_h19w_init_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 256) {
            Logging.Log("[NSC:H19W] INIT_PRE n=%u outer=%p id18=%u arg1=%p arg2=%p f20=%p f50=%p",
                        n, outer, id18, arg1, arg2, pre20, pre50);
        }

        g_h19w_active_outer.store(reinterpret_cast<uintptr_t>(outer), std::memory_order_release);
        Orig(outer, arg1, arg2);
        g_h19w_active_outer.store(0, std::memory_order_release);

        void* post20 = nullptr;
        void* post50 = nullptr;
        if (outer) {
            auto* p = reinterpret_cast<uint8_t*>(outer);
            post20 = *reinterpret_cast<void**>(p + 0x20);
            post50 = *reinterpret_cast<void**>(p + 0x50);
        }

        if (n < 256 || post20 == nullptr) {
            Logging.Log("[NSC:H19W] INIT_POST n=%u outer=%p id18=%u f20=%p->%p f50=%p->%p",
                        n, outer, id18, pre20, post20, pre50, post50);
        }
    }
};

HOOK_DEFINE_TRAMPOLINE(Field20LookupTraceHook) {
    static void* Callback(void* a0, void* a1, void* a2) {
        void* result = Orig(a0, a1, a2);
        const uintptr_t active = g_h19w_active_outer.load(std::memory_order_acquire);
        if (active != 0) {
            const uint32_t n = g_h19w_lookup_logs.fetch_add(1, std::memory_order_relaxed);
            if (n < 256) {
                Logging.Log("[NSC:H19W] LOOKUP n=%u outer=%p a0=%p a1=%p a2=%p result=%p",
                            n, reinterpret_cast<void*>(active), a0, a1, a2, result);
            }
        }
        return result;
    }
};


// R276H19X: trace the stronger field+0x20 initializer candidate at main+0x436018.
// Static v1.70 sequence:
//   main+0x436074  STR W20,[X19,#0x18]      ; W20 came from W6
//   main+0x4360D4  BL  main+0x120A3D4
//   main+0x4360D8  CBZ X0,main+0x436178
//   main+0x436128  STR X28,[X19,#0x20]      ; success
//   main+0x43617C  STR XZR,[X19,#0x20]      ; lookup failed
//
// H19U observed Tobi outer+0x18 low32 == 281 and outer+0x20 == NULL.
// This hook is read-only and preserves all register + stack arguments to Orig.
static std::atomic<uint32_t> g_h19x_init_logs{0};
static std::atomic<uint32_t> g_h19x_lookup_logs{0};
static std::atomic<uintptr_t> g_h19x_active_outer{0};
static std::atomic<uint32_t> g_h19x_active_id{0xFFFFFFFFu};

HOOK_DEFINE_TRAMPOLINE(RealField20InitTraceHook) {
    static void Callback(uintptr_t a0, uintptr_t a1, uintptr_t a2, uintptr_t a3,
                         uintptr_t a4, uintptr_t a5, uintptr_t a6, uintptr_t a7,
                         uintptr_t a8, uintptr_t a9) {
        void* outer = reinterpret_cast<void*>(a0);
        uint32_t pre18 = 0xFFFFFFFFu;
        void* pre20 = nullptr;
        void* pre50 = nullptr;

        if (outer) {
            auto* p = reinterpret_cast<uint8_t*>(outer);
            pre18 = *reinterpret_cast<volatile uint32_t*>(p + 0x18);
            pre20 = *reinterpret_cast<void**>(p + 0x20);
            pre50 = *reinterpret_cast<void**>(p + 0x50);
        }

        const uint32_t id_arg = static_cast<uint32_t>(a6);
        H19AIActivateId(id_arg);
        const uint32_t n = g_h19x_init_logs.fetch_add(1, std::memory_order_relaxed);

        if (n < 256 || id_arg >= 281) {
            Logging.Log("[NSC:H19X] INIT_PRE n=%u outer=%p id_arg=%u pre18=%u f20=%p f50=%p a1=%p a2=%p a3=%p",
                        n, outer, id_arg, pre18, pre20, pre50,
                        reinterpret_cast<void*>(a1),
                        reinterpret_cast<void*>(a2),
                        reinterpret_cast<void*>(a3));
        }

        g_h19x_active_outer.store(a0, std::memory_order_release);
        g_h19x_active_id.store(id_arg, std::memory_order_release);

        Orig(a0, a1, a2, a3, a4, a5, a6, a7, a8, a9);

        g_h19x_active_outer.store(0, std::memory_order_release);
        g_h19x_active_id.store(0xFFFFFFFFu, std::memory_order_release);

        uint32_t post18 = 0xFFFFFFFFu;
        void* post20 = nullptr;
        void* post50 = nullptr;
        if (outer) {
            auto* p = reinterpret_cast<uint8_t*>(outer);
            post18 = *reinterpret_cast<volatile uint32_t*>(p + 0x18);
            post20 = *reinterpret_cast<void**>(p + 0x20);
            post50 = *reinterpret_cast<void**>(p + 0x50);
        }

        if (n < 256 || id_arg >= 281 || post20 == nullptr) {
            Logging.Log("[NSC:H19X] INIT_POST n=%u outer=%p id_arg=%u id18=%u->%u f20=%p->%p f50=%p->%p",
                        n, outer, id_arg, pre18, post18, pre20, post20, pre50, post50);
        }
    }
};

HOOK_DEFINE_TRAMPOLINE(H19XLookupTraceHook) {
    static void* Callback(void* a0, void* a1, void* a2) {
        void* result = Orig(a0, a1, a2);

        const uintptr_t outer = g_h19x_active_outer.load(std::memory_order_acquire);
        if (outer != 0) {
            const uint32_t id_arg = g_h19x_active_id.load(std::memory_order_acquire);
            const uint32_t n = g_h19x_lookup_logs.fetch_add(1, std::memory_order_relaxed);
            if (n < 256 || id_arg >= 281) {
                Logging.Log("[NSC:H19X] LOOKUP n=%u outer=%p id_arg=%u a0=%p a1=%p a2=%p result=%p",
                            n, reinterpret_cast<void*>(outer), id_arg, a0, a1, a2, result);
            }
        }
        return result;
    }
};


// R276H19Y: trace registry lookup used by the strongest upstream producer of
// H19X arg2. Static v1.70 candidate path:
//
//   main+0x7EBD58  BL  main+0x1207B38
//   main+0x7EBD5C  MOV X21,X0
//   ...
//   main+0x7EBE48  MOV X2,X21
//   main+0x7EBE74  BL  main+0x436018
//
// Nearby string construction appends literal "bod3" before the 0x1207B38 lookup.
// This hook is read-only: native return is preserved unchanged.
static std::atomic<uint32_t> g_h19y_reg_logs{0};

static std::atomic<uintptr_t> g_h19z_active_actor{0};
static std::atomic<uint32_t> g_h19z_active_char{0xFFFFFFFFu};
static std::atomic<uint32_t> g_h19z_parent_logs{0};
static std::atomic<uint32_t> g_h19z_reg_logs{0};

static std::atomic<uintptr_t> g_h19aa_active_actor{0};
static std::atomic<uint32_t> g_h19aa_active_char{0xFFFFFFFFu};
static std::atomic<uint32_t> g_h19aa_parent_logs{0};
static std::atomic<uint32_t> g_h19aa_reg_logs{0};

// R276H19AA: scope the generic 0x1207B38 registry tracer to the large native
// actor-init function that contains the actually active H19X callsite.
//
// Function entry:
//   main+0x7E64D4
//
// Active candidate path:
//   main+0x7E7DE4  BL  main+0x1207B38
//   main+0x7E7DE8  CBZ X0, ...
//   main+0x7E7DEC  MOV X22,X0
//   ...
//   main+0x7E7EBC  MOV X2,X22
//   main+0x7E7EE0  BL  main+0x436018
//
// H19X runtime arg1=...3501 is also consistent with this callsite's tagged
// inline-string form (SP+0x110)|1.
//
// Read-only only: no return values or actor state are changed.
HOOK_DEFINE_TRAMPOLINE(H19AAParentHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t char_id = 0xFFFFFFFFu;
        if (actor) {
            auto* p = reinterpret_cast<volatile uint8_t*>(actor);
            char_id = *reinterpret_cast<volatile uint32_t*>(p + 0xE54);
        }

        const uint32_t n =
            g_h19aa_parent_logs.fetch_add(1, std::memory_order_relaxed);
        const bool custom = char_id > 280u;

        if (custom || n < 16) {
            Logging.Log("[NSC:H19AA] ENTER n=%u actor=%p char=%u mode=%u",
                        n, actor, char_id, mode);
        }

        if (custom) {
            g_h19aa_active_char.store(char_id, std::memory_order_release);
            g_h19aa_active_actor.store(reinterpret_cast<uintptr_t>(actor),
                                       std::memory_order_release);
        }

        Orig(actor, mode);

        if (custom) {
            g_h19aa_active_actor.store(0, std::memory_order_release);
            g_h19aa_active_char.store(0xFFFFFFFFu, std::memory_order_release);
            Logging.Log("[NSC:H19AA] EXIT n=%u actor=%p char=%u mode=%u",
                        n, actor, char_id, mode);
        }
    }
};


// R276H19Z: caller-scoped trace for the function that statically feeds X21 into
// X2 of main+0x436018.
//
// main+0x7EB94C is the function entry.
// Inside it:
//   main+0x7EBD58  BL  main+0x1207B38
//   main+0x7EBD5C  MOV X21,X0
//   main+0x7EBE48  MOV X2,X21
//   main+0x7EBE74  BL  main+0x436018
//
// Important correction: local "bod3" is passed as X1 to 0x436018,
// not as the 0x1207B38 registry key.
HOOK_DEFINE_TRAMPOLINE(H19ZParentHook) {
    static void Callback(void* actor, uint32_t mode) {
        uint32_t char_id = 0xFFFFFFFFu;
        if (actor) {
            auto* p = reinterpret_cast<volatile uint8_t*>(actor);
            char_id = *reinterpret_cast<volatile uint32_t*>(p + 0xE54);
        }

        const uint32_t n = g_h19z_parent_logs.fetch_add(1, std::memory_order_relaxed);
        const bool custom = char_id > 280u;

        if (custom || n < 16) {
            Logging.Log("[NSC:H19Z] ENTER n=%u actor=%p char=%u mode=%u",
                        n, actor, char_id, mode);
        }

        if (custom) {
            g_h19z_active_char.store(char_id, std::memory_order_release);
            g_h19z_active_actor.store(reinterpret_cast<uintptr_t>(actor),
                                      std::memory_order_release);
        }

        Orig(actor, mode);

        if (custom) {
            g_h19z_active_actor.store(0, std::memory_order_release);
            g_h19z_active_char.store(0xFFFFFFFFu, std::memory_order_release);
            Logging.Log("[NSC:H19Z] EXIT n=%u actor=%p char=%u mode=%u",
                        n, actor, char_id, mode);
        }
    }
};


HOOK_DEFINE_TRAMPOLINE(H19YRegistryLookupHook) {
    static void* Callback(void* registry, const char* key) {
        void* result = Orig(registry, key);
        void* h19ah_exact_result = result;
        const char* h19ah_mode = result ? "EXACT" : "MISS";
        char h19ah_alt[kH19AGKeyCap]{};

        if (result != nullptr)
            H19AGObserveRegistrySuccess(key);

        char text[65]{};
        if (key) {
            for (size_t i = 0; i < 64; ++i) {
                const unsigned char c = static_cast<unsigned char>(key[i]);
                if (c == 0) {
                    text[i] = '\0';
                    break;
                }
                text[i] = (c >= 0x20 && c <= 0x7E) ? static_cast<char>(c) : '.';
                if (i == 63) text[64] = '\0';
            }
        }

        bool interesting = (result == nullptr);
        if (key) {
            // Fixture filter only, diagnostic-not-final.
            const char* needles[] = {"mtob", "bod3"};
            for (const char* n : needles) {
                const char* h = text;
                while (*h) {
                    const char* a = h;
                    const char* b = n;
                    while (*a && *b && *a == *b) { ++a; ++b; }
                    if (*b == '\0') { interesting = true; break; }
                    ++h;
                }
                if (interesting) break;
            }
        }

        const uint32_t n = g_h19y_reg_logs.fetch_add(1, std::memory_order_relaxed);

        bool h19ab_match = false;
        if (key) {
            const char* needles[] = {"mtob", "bod1"};
            for (const char* nd : needles) {
                const char* h = text;
                while (*h) {
                    const char* a = h;
                    const char* b = nd;
                    while (*a && *b && *a == *b) { ++a; ++b; }
                    if (*b == '\0') { h19ab_match = true; break; }
                    ++h;
                }
                if (h19ab_match) break;
            }
        }

        if (false && h19ab_match) {
            Logging.Log("[NSC:H19AB] REG registry=%p keyptr=%p key=%s result=%p",
                        registry, key, key ? text : "<null>", result);
        }

        // R276H19AG adaptive compatibility path.
        if (result == nullptr && key) {
            auto accept_candidate = [&](const char* candidate, bool cache_hit) {
                if (result != nullptr || !candidate || candidate[0] == '\0')
                    return;

                void* native = Orig(registry, candidate);
                if (native == nullptr)
                    return;

                result = native;
                H19AGAddAlias(key, candidate);
                H19AGObserveRegistrySuccess(candidate);

                h19ah_mode = cache_hit ? "CACHE" : "TRANSFORM";
                H19AGCopy(h19ah_alt, sizeof(h19ah_alt), candidate);
                H19AHMaybeDiscoverCode(candidate);

                if (cache_hit)
                    g_h19ag_cache_hits.fetch_add(1, std::memory_order_relaxed);
                else
                    g_h19ag_transform_hits.fetch_add(1, std::memory_order_relaxed);
            };

            char cached[kH19AGKeyCap]{};
            if (H19AGFindAlias(key, cached, sizeof(cached)))
                accept_candidate(cached, true);

            const bool ends_xfbin = H19AGEndsXfbin(key);

            if (result == nullptr && !H19AGStarts(key, "data/") &&
                !H19AGStarts(key, "/data/") &&
                !H19AGStarts(key, "disc:") &&
                ends_xfbin) {
                char candidate[kH19AGKeyCap]{};
                if (H19AGMakePrefix("data/spc/", key, candidate, sizeof(candidate)))
                    accept_candidate(candidate, false);
            }

            if (result == nullptr && H19AGStarts(key, "data/") && !ends_xfbin) {
                char candidate[kH19AGKeyCap]{};
                if (H19AGMakeAddXfbin(key, candidate, sizeof(candidate)))
                    accept_candidate(candidate, false);
            }

            if (result == nullptr && H19AGStarts(key, "data/") && ends_xfbin) {
                char candidate[kH19AGKeyCap]{};
                if (H19AGMakeStripXfbin(key, candidate, sizeof(candidate)))
                    accept_candidate(candidate, false);
            }

            if (result == nullptr && H19AGStarts(key, "/data/"))
                accept_candidate(key + 1, false);

            if (result == nullptr && H19AGStarts(key, "disc:data/"))
                accept_candidate(key + 5, false);

            if (result == nullptr && H19AGStarts(key, "data/")) {
                char candidate[kH19AGKeyCap]{};
                if (H19AGMakePrefix("disc:", key, candidate, sizeof(candidate)))
                    accept_candidate(candidate, false);
            }

            // H19AH replaces global unresolved dumping with scoped telemetry.
        }

        H19AHTraceRegistry(registry,
                           key,
                           h19ah_exact_result,
                           result,
                           h19ah_mode,
                           h19ah_alt);

        // R276H19AC: diagnostic-only key normalization probe.\n        if (result == nullptr && key) {\n            size_t klen = 0;\n            bool has_sep = false;\n            while (klen < 80 && key[klen] != '\0') {\n                if (key[klen] == '/' || key[klen] == ':') has_sep = true;\n                ++klen;\n            }\n            const char suffix[] = ".xfbin";\n            constexpr size_t suffix_len = 6;\n            bool ends_xfbin = klen > suffix_len;\n            if (ends_xfbin) {\n                for (size_t i=0;i<suffix_len;++i) if (key[klen-suffix_len+i] != suffix[i]) { ends_xfbin=false; break; }\n            }\n            if (!has_sep && ends_xfbin) {\n                char pfxext[96]{}; char strip[96]{}; char pfxstrip[96]{};\n                const char prefix[] = "data/spc/"; constexpr size_t plen=9;\n                const size_t blen=klen-suffix_len;\n                size_t p=0; for(;p<plen && p+1<sizeof(pfxext);++p) pfxext[p]=prefix[p];\n                for(size_t i=0;i<klen && p+1<sizeof(pfxext);++i,++p) pfxext[p]=key[i];\n                size_t s=0; for(;s<blen && s+1<sizeof(strip);++s) strip[s]=key[s];\n                p=0; for(;p<plen && p+1<sizeof(pfxstrip);++p) pfxstrip[p]=prefix[p];\n                for(size_t i=0;i<blen && p+1<sizeof(pfxstrip);++i,++p) pfxstrip[p]=key[i];\n                void* a=Orig(registry,pfxext); void* b=Orig(registry,strip); void* c=Orig(registry,pfxstrip);\n                Logging.Log("[NSC:H19AC] PROBE key=%s pfxext=%s:%p strip=%s:%p pfxstrip=%s:%p",\n                            text,pfxext,a,strip,b,pfxstrip,c);\n            }\n        }\n\n
        const uintptr_t aa_actor =
            g_h19aa_active_actor.load(std::memory_order_acquire);
        if (aa_actor != 0) {
            const uint32_t aa_char =
                g_h19aa_active_char.load(std::memory_order_acquire);
            const uint32_t aa_n =
                g_h19aa_reg_logs.fetch_add(1, std::memory_order_relaxed);
            if (aa_n < 128) {
                Logging.Log("[NSC:H19AA] REG n=%u actor=%p char=%u registry=%p keyptr=%p key=%s result=%p",
                            aa_n, reinterpret_cast<void*>(aa_actor), aa_char,
                            registry, key, key ? text : "<null>", result);
            }
        }


        const uintptr_t active_actor =
            g_h19z_active_actor.load(std::memory_order_acquire);
        if (active_actor != 0) {
            const uint32_t char_id =
                g_h19z_active_char.load(std::memory_order_acquire);
            const uint32_t zn =
                g_h19z_reg_logs.fetch_add(1, std::memory_order_relaxed);
            if (zn < 128) {
                Logging.Log("[NSC:H19Z] REG n=%u actor=%p char=%u registry=%p keyptr=%p key=%s result=%p",
                            zn, reinterpret_cast<void*>(active_actor), char_id,
                            registry, key, key ? text : "<null>", result);
            }
        }

        if (false && interesting && n < 64) {
            Logging.Log("[NSC:H19Y] REG n=%u registry=%p keyptr=%p key=%s result=%p",
                        n, registry, key, key ? text : "<null>", result);
        }

        return result;
    }
};

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

    static constexpr uint32_t kNullVcallExpected[] = {
        0xF81D0FFE, 0xA90157F6, 0xA9024FF4, 0xAA0003F4,
        0xF9400C00, 0xAA0103F3, 0xF9400008, 0xF9400908,
    };

    static constexpr uint32_t kH19UOuterExpected[] = {
        0xD10443FF, 0xA90B7BFD, 0xA90C6FFC, 0xA90D67FA,
        0xA90E5FF8, 0xA90F57F6, 0xA9104FF4, 0xAA0003F9,
    };

    static constexpr uint32_t kH19WInitExpected[] = {
        0xD100C3FF, 0xA90157FE, 0xA9024FF4, 0xF9400008,
        0xAA0203F5, 0xAA0103F4, 0xAA0003F3, 0xF9400908,
    };
    static constexpr uint32_t kH19WLookupExpected[] = {
        0xD10143FF, 0xA90357FE, 0xA9044FF4, 0xAA0203F3,
        0xAA0103F4, 0xB90003FF, 0xAA0003F5, 0x390013FF,
    };

    static constexpr uint32_t kH19XInitExpected[] = {
        0xD10303FF, 0xA9067BFD, 0xA9076FFC, 0xA90867FA,
        0xA9095FF8, 0xA90A57F6, 0xA90B4FF4, 0x52863908,
    };

    static constexpr uint32_t kH19YRegistryExpected[] = {
        0xF81F0FFE, 0x97FFFC27, 0xB4000060, 0xF84107FE,
        0x17FFFACB, 0xF84107FE, 0xD65F03C0,
    };

    static constexpr uint32_t kH19ZParentExpected[] = {
        0xD10783FF, 0xA9187BFD, 0xA9196FFC, 0xA91A67FA,
        0xA91B5FF8, 0xA91C57F6, 0xA91D4FF4, 0x5281F888,
    };

    static constexpr uint32_t kH19AAParentExpected[] = {
        0xD10683FF, 0xA9147BFD, 0xA9156FFC, 0xA91667FA,
        0xA9175FF8, 0xA91857F6, 0xA9194FF4, 0x5280E408,
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
    if (!MatchWords(0x11A1C00, kNullVcallExpected)) {
        LogFingerprintFail("H19S_VCALL", 0x11A1C00); ok = false;
    }
    if (!MatchWords(0x439FDC, kH19UOuterExpected)) {
        LogFingerprintFail("H19U_OUTER", 0x439FDC); ok = false;
    }
    if (!MatchWords(0x433258, kH19WInitExpected)) {
        LogFingerprintFail("H19W_INIT", 0x433258); ok = false;
    }
    if (!MatchWords(0x120A3D4, kH19WLookupExpected)) {
        LogFingerprintFail("H19W_LOOKUP", 0x120A3D4); ok = false;
    }
    if (!MatchWords(0x436018, kH19XInitExpected)) {
        LogFingerprintFail("H19X_INIT", 0x436018); ok = false;
    }
    if (!MatchWords(0x1207B38, kH19YRegistryExpected)) {
        LogFingerprintFail("H19Y_REG", 0x1207B38); ok = false;
    }
    if (!MatchWords(0x7EB94C, kH19ZParentExpected)) {
        LogFingerprintFail("H19Z_PARENT", 0x7EB94C); ok = false;
    }
    if (!MatchWords(0x7E64D4, kH19AAParentExpected)) {
        LogFingerprintFail("H19AA_PARENT", 0x7E64D4); ok = false;
    }
    if (!ok) return false;

    CharacodeGetterHook::InstallAtOffset(kCharacodeGetterOffset);
    FileLoadRequestHook::InstallAtOffset(kFileLoadRequestOffset);
    FileLoadCreateHook::InstallAtOffset(kFileLoadCreateOffset);
    FileLoadStatusHook::InstallAtOffset(kFileLoadStatusOffset);
    ChunkBinaryHook::InstallAtOffset(kChunkBinaryOffset);
    LoadRequestProcessHook::InstallAtOffset(kLoadRequestProcessOffset);
    FileOpenHook::InstallAtOffset(kFileOpenOffset);
    NullVcallTraceHook::InstallAtOffset(0x11A1C00);
    Logging.Log("[NSC:H19S] READY vcall=1 off=0x11a1c00");
    OuterField20TraceHook::InstallAtOffset(0x439FDC);
    Logging.Log("[NSC:H19U] READY outer=1 off=0x439fdc");
    Field20InitTraceHook::InstallAtOffset(0x433258);
    // R276H19X: H19W lookup hook superseded by H19X at the same offset.
    Logging.Log("[NSC:H19W] READY init=1 off=0x433258 lookup=0 superseded=H19X");
    RealField20InitTraceHook::InstallAtOffset(0x436018);
    H19XLookupTraceHook::InstallAtOffset(0x120A3D4);
    Logging.Log("[NSC:H19X] READY init=1 off=0x436018 lookup=1 off=0x120a3d4");
    H19YRegistryLookupHook::InstallAtOffset(0x1207B38);
    Logging.Log("[NSC:H19Y] READY reg=1 off=0x1207b38");
    H19ZParentHook::InstallAtOffset(0x7EB94C);
    Logging.Log("[NSC:H19Z] READY parent=1 off=0x7eb94c reg_scope=0x1207b38");
    H19AAParentHook::InstallAtOffset(0x7E64D4);
    Logging.Log("[NSC:H19AA] READY parent=1 off=0x7e64d4 reg_scope=0x1207b38");
    Logging.Log("[NSC:H19AB] READY uncapped_filter=mtob|bod1 reg=0x1207b38");
    Logging.Log("[NSC:H19AC] READY bare_xfbin_probe=1 forms=pfxext|strip|pfxstrip");
    Logging.Log("[NSC:H19AD] READY exact_prefix_probe=mtobbod1.xfbin->data/spc/mtobbod1.xfbin");
    Logging.Log("[NSC:H19AG] READY adaptive=1 success_keys=1 loaded_paths=1 alias_cache=1 unresolved_only=1 hardcoded_id=0 hardcoded_code=0");
    Logging.Log("[NSC:H19AH] READY scoped_graph=1 runtime_code_discovery=1 exact=1 cache=1 transform=1 miss=1 loaded=1 hardcoded_id=0 hardcoded_code=0");
    Logging.Log("[NSC:H19AHB] READY build_fix=forward_decls+unused_annotation runtime_semantics=unchanged");
    Logging.Log("[NSC:H19AI] READY scope=charcode+x19x body_candidates=1 multi_code=1 hardcoded_id=0 hardcoded_code=0");
    return true;
}

} // namespace

void InstallP32Trace() {
    const bool cpk = InstallCpkBridge();
    const bool trace = InstallTraceHooks();
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
