#include "nsc_cpk_bridge.hpp"

#include "lib.hpp"
#include <lib/hook/trampoline.hpp>
#include <lib/hook/inline.hpp>
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
static constexpr size_t kH19AHStemCap = 16;
static constexpr size_t kH19AHSeenCap = 384;

struct H19AHSeenEntry {
    char kind[20];
    char key[kH19AGKeyCap];
};

static char g_h19ah_stems[kH19AHStemCap][kH19AHCodeCap]{};
static size_t g_h19ah_stem_count = 0;
static std::atomic_flag g_h19ah_code_lock = ATOMIC_FLAG_INIT;

static H19AHSeenEntry g_h19ah_seen[kH19AHSeenCap]{};
static size_t g_h19ah_seen_count = 0;
static std::atomic_flag g_h19ah_seen_lock = ATOMIC_FLAG_INIT;

[[maybe_unused]] static bool H19AHContains(const char* s, const char* needle) {
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

[[maybe_unused]] static bool H19AHEndsWith(const char* s, const char* suffix) {
    if (!s || !suffix) return false;
    const size_t ns = H19AGLen(s);
    const size_t nx = H19AGLen(suffix);
    if (ns < nx) return false;
    for (size_t i = 0; i < nx; ++i) {
        if (s[ns - nx + i] != suffix[i]) return false;
    }
    return true;
}

[[maybe_unused]] static const char* H19AHStripScheme(const char* s) {
    if (!s) return s;
    if (H19AGStarts(s, "disc:")) return s + 5;
    if (H19AGStarts(s, "ROM:/")) return s + 5;
    if (H19AGStarts(s, "/")) return s + 1;
    return s;
}

[[maybe_unused]] static void H19AHMaybeDiscoverCode(const char* canonical) {
    if (!canonical)
        return;

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
    if (code_len == 0 || code_len >= kH19AHCodeCap)
        return;

    char stem[kH19AHCodeCap]{};
    for (size_t i = 0; i < code_len; ++i)
        stem[i] = p[i];
    stem[code_len] = '\0';

    H19AGLock(g_h19ah_code_lock);

    for (size_t i = 0; i < g_h19ah_stem_count; ++i) {
        if (H19AGEq(g_h19ah_stems[i], stem)) {
            H19AGUnlock(g_h19ah_code_lock);
            return;
        }
    }

    if (g_h19ah_stem_count < kH19AHStemCap) {
        H19AGCopy(g_h19ah_stems[g_h19ah_stem_count],
                  kH19AHCodeCap,
                  stem);
        ++g_h19ah_stem_count;

        Logging.Log("[NSC:H19AI] DISCOVER_STEM stem=%s canonical=%s count=%u",
                    stem,
                    canonical,
                    static_cast<unsigned>(g_h19ah_stem_count));
    }

    H19AGUnlock(g_h19ah_code_lock);
}

[[maybe_unused]] static bool H19AHRelevant(const char* key) {
    if (!key)
        return false;

    bool relevant = false;

    H19AGLock(g_h19ah_code_lock);
    for (size_t i = 0; i < g_h19ah_stem_count; ++i) {
        if (H19AHContains(key, g_h19ah_stems[i])) {
            relevant = true;
            break;
        }
    }
    H19AGUnlock(g_h19ah_code_lock);

    return relevant;
}

[[maybe_unused]] static bool H19AHMarkSeen(const char* kind, const char* key) {
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

[[maybe_unused]] static void H19AHTraceLoaded(const char* path) {
    H19AHMaybeDiscoverCode(path);

    if (!H19AHRelevant(path))
        return;

    if (H19AHMarkSeen("LOADED", path))
        Logging.Log("[NSC:H19AH] LOADED path=%s", path);
}

[[maybe_unused]] static void H19AHTraceRegistry(void* registry,
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
            Logging.Log("[NSC:H19AH] EXACT registry=%p key=%s result=%p",
                        registry, key, exact_result);
        return;
    }

    if (final_result != nullptr) {
        const char* resolved_mode = (mode && mode[0]) ? mode : "FALLBACK";
        char dedupe_kind[20]{};
        H19AGCopy(dedupe_kind, sizeof(dedupe_kind), resolved_mode);

        if (H19AHMarkSeen(dedupe_kind, key))
            Logging.Log("[NSC:H19AH] RESOLVE mode=%s registry=%p key=%s alt=%s result=%p",
                        resolved_mode,
                        registry,
                        key,
                        (alt && alt[0]) ? alt : "<none>",
                        final_result);
        return;
    }

    if (H19AHMarkSeen("MISS", key))
        Logging.Log("[NSC:H19AH] MISS registry=%p key=%s", registry, key);
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



// ===========================================================================
// R276H19AJB - generic charsel-correlated action-resource causal prefetch
// Diagnostic only: if this proves scheduling, final fix must move back to the
// native prm_load/resource-graph path rather than keeping charsel prefetch.
// ===========================================================================

static constexpr size_t kH19AJBStemCap = 32;
static constexpr size_t kH19AJBStemLen = 32;
static constexpr size_t kH19AJBPathCap = 128;
static constexpr unsigned kH19AJBMaxAttempts = 3;

struct H19AJBState {
    char stem[kH19AJBStemLen];
    unsigned attempts;
    bool done;
};

static H19AJBState g_h19ajb_states[kH19AJBStemCap]{};
static size_t g_h19ajb_state_count = 0;
static std::atomic_flag g_h19ajb_lock = ATOMIC_FLAG_INIT;

static bool H19AJBStarts(const char* s, const char* pfx) {
    if (!s || !pfx) return false;
    size_t i = 0;
    while (pfx[i]) {
        if (s[i] != pfx[i]) return false;
        ++i;
    }
    return true;
}

static size_t H19AJBLen(const char* s) {
    if (!s) return 0;
    size_t n = 0;
    while (n < kH19AJBPathCap - 1 && s[n]) ++n;
    return n;
}

static bool H19AJBEnds(const char* s, const char* suffix) {
    if (!s || !suffix) return false;
    const size_t ns = H19AJBLen(s);
    const size_t nx = H19AJBLen(suffix);
    if (ns < nx) return false;
    for (size_t i = 0; i < nx; ++i) {
        if (s[ns - nx + i] != suffix[i]) return false;
    }
    return true;
}

static bool H19AJBEq(const char* a, const char* b) {
    if (!a || !b) return false;
    size_t i = 0;
    while (a[i] && b[i]) {
        if (a[i] != b[i]) return false;
        ++i;
    }
    return a[i] == b[i];
}

static bool H19AJBCopy(char* dst, size_t cap, const char* src) {
    if (!dst || cap == 0 || !src) return false;
    size_t i = 0;
    for (; i + 1 < cap && src[i]; ++i)
        dst[i] = src[i];
    dst[i] = '\0';
    return src[i] == '\0';
}

static bool H19AJBExtractCharselStem(const char* path,
                                     char* stem,
                                     size_t stem_cap) {
    static constexpr char kPrefix[] = "data/ui/max/crsel/c/";
    static constexpr char kSuffix[] = "charsel.xfbin";

    if (!path || !stem || stem_cap == 0)
        return false;
    if (!H19AJBStarts(path, kPrefix) || !H19AJBEnds(path, kSuffix))
        return false;

    const size_t np = H19AJBLen(kPrefix);
    const size_t n  = H19AJBLen(path);
    const size_t ns = H19AJBLen(kSuffix);
    if (n <= np + ns)
        return false;

    const size_t stem_len = n - np - ns;
    if (stem_len == 0 || stem_len >= stem_cap)
        return false;

    for (size_t i = 0; i < stem_len; ++i)
        stem[i] = path[np + i];
    stem[stem_len] = '\0';
    return true;
}

static bool H19AJBMakeActionPath(const char* stem,
                                 const char* suffix,
                                 char* out,
                                 size_t cap) {
    static constexpr char kPrefix[] = "data/spc/";
    if (!stem || !stem[0] || !suffix || !out || cap == 0)
        return false;

    size_t p = 0;
    for (size_t i = 0; kPrefix[i]; ++i) {
        if (p + 1 >= cap) return false;
        out[p++] = kPrefix[i];
    }
    for (size_t i = 0; stem[i]; ++i) {
        if (p + 1 >= cap) return false;
        out[p++] = stem[i];
    }
    for (size_t i = 0; suffix[i]; ++i) {
        if (p + 1 >= cap) return false;
        out[p++] = suffix[i];
    }
    out[p] = '\0';
    return true;
}

// H19AKB: prm_load uses the game's spcload namespace, not data/spc/.
// Generic by discovered stem; no character IDs/codes or donor aliases.
static bool H19AKBMakeSpcLoadPath(const char* stem,
                                   const char* suffix,
                                   char* out,
                                   size_t cap) {
    static constexpr char kPrefix[] = "data/spcload/";
    if (!stem || !stem[0] || !suffix || !out || cap == 0)
        return false;

    size_t p = 0;
    for (size_t i = 0; kPrefix[i]; ++i) {
        if (p + 1 >= cap) return false;
        out[p++] = kPrefix[i];
    }
    for (size_t i = 0; stem[i]; ++i) {
        if (p + 1 >= cap) return false;
        out[p++] = stem[i];
    }
    for (size_t i = 0; suffix[i]; ++i) {
        if (p + 1 >= cap) return false;
        out[p++] = suffix[i];
    }
    out[p] = '\0';
    return true;
}

// Returns true when this charsel occurrence should attempt a prefetch.
// attempt_out is 1-based. State is marked done only after accepted requests.
static bool H19AJBBeginAttempt(const char* stem, unsigned* attempt_out) {
    if (!stem || !stem[0] || !attempt_out)
        return false;

    H19AGLock(g_h19ajb_lock);

    for (size_t i = 0; i < g_h19ajb_state_count; ++i) {
        H19AJBState& st = g_h19ajb_states[i];
        if (!H19AJBEq(st.stem, stem))
            continue;

        if (st.done || st.attempts >= kH19AJBMaxAttempts) {
            H19AGUnlock(g_h19ajb_lock);
            return false;
        }

        ++st.attempts;
        *attempt_out = st.attempts;
        H19AGUnlock(g_h19ajb_lock);
        return true;
    }

    if (g_h19ajb_state_count >= kH19AJBStemCap) {
        H19AGUnlock(g_h19ajb_lock);
        return false;
    }

    H19AJBState& st = g_h19ajb_states[g_h19ajb_state_count++];
    H19AJBCopy(st.stem, sizeof(st.stem), stem);
    st.attempts = 1;
    st.done = false;
    *attempt_out = 1;

    H19AGUnlock(g_h19ajb_lock);
    return true;
}

static void H19AJBFinishAttempt(const char* stem, bool accepted) {
    if (!stem || !stem[0]) return;

    H19AGLock(g_h19ajb_lock);
    for (size_t i = 0; i < g_h19ajb_state_count; ++i) {
        H19AJBState& st = g_h19ajb_states[i];
        if (H19AJBEq(st.stem, stem)) {
            if (accepted)
                st.done = true;
            break;
        }
    }
    H19AGUnlock(g_h19ajb_lock);
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
    // Calls Orig() directly, intentionally bypassing this hook's Callback.
    // Therefore injected action requests will NOT emit the normal P32 LOAD_REQ
    // line from this callback. H19AJB emits its own NATIVE_REQ markers instead.
    static void* H19AJBNativeRequest(void* manager,
                                     const char* path,
                                     const void* options) {
        return Orig(manager, path, options);
    }

    static void* Callback(void* manager, const char* path, const void* options) {
        void* result = Orig(manager, path, options);

        char h19ajb_stem[kH19AJBStemLen]{};
        unsigned h19ajb_attempt = 0;
        if (H19AJBExtractCharselStem(path, h19ajb_stem, sizeof(h19ajb_stem)) &&
            H19AJBBeginAttempt(h19ajb_stem, &h19ajb_attempt)) {

            char h19ajb_combo[kH19AJBPathCap]{};
            char h19ajb_anmofs[kH19AJBPathCap]{};
            char h19ak_prm[kH19AJBPathCap]{};
            char h19ak_prm_load[kH19AJBPathCap]{};

            const bool combo_ok =
                H19AJBMakeActionPath(h19ajb_stem,
                                     "_comboPrm.xfbin",
                                     h19ajb_combo,
                                     sizeof(h19ajb_combo));
            const bool anmofs_ok =
                H19AJBMakeActionPath(h19ajb_stem,
                                     "_anmofs.xfbin",
                                     h19ajb_anmofs,
                                     sizeof(h19ajb_anmofs));

            const bool h19ak_prm_ok =
                H19AJBMakeActionPath(h19ajb_stem,
                                     "prm.bin.xfbin",
                                     h19ak_prm,
                                     sizeof(h19ak_prm));
            const bool h19ak_prm_load_ok =
                H19AKBMakeSpcLoadPath(h19ajb_stem,
                                      "prm_load.bin.xfbin",
                                      h19ak_prm_load,
                                      sizeof(h19ak_prm_load));

            Logging.Log("[NSC:H19AJB] PREFETCH_ATTEMPT stem=%s attempt=%u manager=%p options=%p combo=%s anmofs=%s",
                        h19ajb_stem,
                        h19ajb_attempt,
                        manager,
                        options,
                        combo_ok ? h19ajb_combo : "<build-fail>",
                        anmofs_ok ? h19ajb_anmofs : "<build-fail>");

            void* combo_req = nullptr;
            void* anmofs_req = nullptr;
            void* h19ak_prm_req = nullptr;
            void* h19ak_prm_load_req = nullptr;

            if (combo_ok) {
                Logging.Log("[NSC:H19AJB] NATIVE_REQ_BEGIN stem=%s family=comboPrm path=%s",
                            h19ajb_stem, h19ajb_combo);
                combo_req = H19AJBNativeRequest(manager, h19ajb_combo, options);
                Logging.Log("[NSC:H19AJB] NATIVE_REQ_RET stem=%s family=comboPrm path=%s result=%p",
                            h19ajb_stem, h19ajb_combo, combo_req);
            }

            if (anmofs_ok) {
                Logging.Log("[NSC:H19AJB] NATIVE_REQ_BEGIN stem=%s family=anmofs path=%s",
                            h19ajb_stem, h19ajb_anmofs);
                anmofs_req = H19AJBNativeRequest(manager, h19ajb_anmofs, options);
                Logging.Log("[NSC:H19AJB] NATIVE_REQ_RET stem=%s family=anmofs path=%s result=%p",
                            h19ajb_stem, h19ajb_anmofs, anmofs_req);
            }

            Logging.Log("[NSC:H19AK] PREFETCH_ATTEMPT stem=%s manager=%p options=%p prm=%s prm_load=%s",
                        h19ajb_stem,
                        manager,
                        options,
                        h19ak_prm_ok ? h19ak_prm : "<build-fail>",
                        h19ak_prm_load_ok ? h19ak_prm_load : "<build-fail>");

            if (h19ak_prm_ok) {
                Logging.Log("[NSC:H19AK] NATIVE_REQ_BEGIN stem=%s family=prm path=%s",
                            h19ajb_stem, h19ak_prm);
                h19ak_prm_req = H19AJBNativeRequest(manager, h19ak_prm, options);
                Logging.Log("[NSC:H19AK] NATIVE_REQ_RET stem=%s family=prm path=%s result=%p",
                            h19ajb_stem, h19ak_prm, h19ak_prm_req);
            }

            if (h19ak_prm_load_ok) {
                Logging.Log("[NSC:H19AK] NATIVE_REQ_BEGIN stem=%s family=prm_load path=%s",
                            h19ajb_stem, h19ak_prm_load);
                h19ak_prm_load_req = H19AJBNativeRequest(manager, h19ak_prm_load, options);
                Logging.Log("[NSC:H19AK] NATIVE_REQ_RET stem=%s family=prm_load path=%s result=%p",
                            h19ajb_stem, h19ak_prm_load, h19ak_prm_load_req);
            }

            Logging.Log("[NSC:H19AK] PREFETCH_RESULT stem=%s accepted=%u prm_req=%p prm_load_req=%p",
                        h19ajb_stem,
                        (h19ak_prm_ok && h19ak_prm_load_ok && h19ak_prm_req && h19ak_prm_load_req) ? 1u : 0u,
                        h19ak_prm_req,
                        h19ak_prm_load_req);

            // R276H19AL: diagnostic child-graph prefetch. Native control shows
            // these per-character families present in the registry while the custom
            // stem has none after prm/prm_load are already loaded. This is a causal
            // test only; final architecture must consume the native prm_load graph.
            if (h19ak_prm_load_req) {
                static constexpr const char* kH19ALChildSuffixes[] = {
                    "acc1.xfbin",
                    "aws.xfbin",
                    "bod1c.xfbin",
                    "bod1l.xfbin",
                    "bod1s.xfbin",
                    "eff1.xfbin",
                    "skl1.xfbin",
                    "skl3.xfbin",
                    "spl1.xfbin",
                    "spl1_fin01.xfbin",
                };

                uint32_t h19al_req_nonnull = 0;
                uint32_t h19al_path_ok = 0;
                for (size_t h19al_i = 0;
                     h19al_i < (sizeof(kH19ALChildSuffixes) / sizeof(kH19ALChildSuffixes[0]));
                     ++h19al_i) {
                    char h19al_path[kH19AJBPathCap]{};
                    const char* h19al_suffix = kH19ALChildSuffixes[h19al_i];
                    const bool h19al_ok =
                        H19AJBMakeActionPath(h19ajb_stem,
                                             h19al_suffix,
                                             h19al_path,
                                             sizeof(h19al_path));
                    if (!h19al_ok) {
                        Logging.Log("[NSC:H19AL] CHILD_PATH_FAIL stem=%s suffix=%s",
                                    h19ajb_stem, h19al_suffix);
                        continue;
                    }
                    ++h19al_path_ok;

                    Logging.Log("[NSC:H19AL] CHILD_REQ_BEGIN stem=%s suffix=%s path=%s",
                                h19ajb_stem, h19al_suffix, h19al_path);
                    void* h19al_req =
                        H19AJBNativeRequest(manager, h19al_path, options);
                    if (h19al_req) ++h19al_req_nonnull;
                    Logging.Log("[NSC:H19AL] CHILD_REQ_RET stem=%s suffix=%s path=%s result=%p",
                                h19ajb_stem, h19al_suffix, h19al_path, h19al_req);
                }

                Logging.Log("[NSC:H19AL] CHILD_PREFETCH_RESULT stem=%s path_ok=%u req_nonnull=%u total=%u",
                            h19ajb_stem,
                            h19al_path_ok,
                            h19al_req_nonnull,
                            static_cast<uint32_t>(sizeof(kH19ALChildSuffixes) / sizeof(kH19ALChildSuffixes[0])));
            }

            const bool accepted = combo_ok && anmofs_ok && combo_req && anmofs_req;
            H19AJBFinishAttempt(h19ajb_stem, accepted);

            Logging.Log("[NSC:H19AJB] PREFETCH_RESULT stem=%s attempt=%u accepted=%u combo_req=%p anmofs_req=%p",
                        h19ajb_stem,
                        h19ajb_attempt,
                        accepted ? 1u : 0u,
                        combo_req,
                        anmofs_req);
        }

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


// R276H19AM: trace the two known callsites that feed main+0x436018.
// Inline hooks faithfully re-emulate only the replaced MOV X2 instruction.
static std::atomic<uint32_t> g_h19am_a_logs{0};
static std::atomic<uint32_t> g_h19am_b_logs{0};

static void H19AMLogRegs(const char* site,
                         uint32_t n,
                         exl::hook::nx64::InlineCtx* ctx) {
    if (!ctx) return;

    Logging.Log(
        "[NSC:H19AM] SITE=%s n=%u "
        "x0=%p x1=%p x2=%p x3=%p x4=%p x5=%p x6=%p x7=%p "
        "x19=%p x20=%p x21=%p x22=%p x23=%p x24=%p x25=%p x26=%p x27=%p x28=%p",
        site, n,
        reinterpret_cast<void*>(ctx->X[0]),
        reinterpret_cast<void*>(ctx->X[1]),
        reinterpret_cast<void*>(ctx->X[2]),
        reinterpret_cast<void*>(ctx->X[3]),
        reinterpret_cast<void*>(ctx->X[4]),
        reinterpret_cast<void*>(ctx->X[5]),
        reinterpret_cast<void*>(ctx->X[6]),
        reinterpret_cast<void*>(ctx->X[7]),
        reinterpret_cast<void*>(ctx->X[19]),
        reinterpret_cast<void*>(ctx->X[20]),
        reinterpret_cast<void*>(ctx->X[21]),
        reinterpret_cast<void*>(ctx->X[22]),
        reinterpret_cast<void*>(ctx->X[23]),
        reinterpret_cast<void*>(ctx->X[24]),
        reinterpret_cast<void*>(ctx->X[25]),
        reinterpret_cast<void*>(ctx->X[26]),
        reinterpret_cast<void*>(ctx->X[27]),
        reinterpret_cast<void*>(ctx->X[28]));
}

HOOK_DEFINE_INLINE(H19AMCallsiteA) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        const uint32_t n = g_h19am_a_logs.fetch_add(1, std::memory_order_relaxed);
        ctx->X[2] = ctx->X[22]; // original MOV X2,X22
        if (n < 64) H19AMLogRegs("7E7EBC", n, ctx);
    }
};

HOOK_DEFINE_INLINE(H19AMCallsiteB) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        const uint32_t n = g_h19am_b_logs.fetch_add(1, std::memory_order_relaxed);
        ctx->X[2] = ctx->X[21]; // original MOV X2,X21
        if (n < 64) H19AMLogRegs("7EBE48", n, ctx);
    }
};


// R276H19AN: capture the real game's X30/LR inside main+0x436018 before
// any BL instruction executes.
//
// Static v1.70 prologue:
//   +0x00  D10303FF  SUB SP,SP,#0xC0
//   +0x04  A9067BFD  STP X29,X30,[SP,#0x60]
//   +0x08  A9076FFC  STP X28,X27,[SP,#0x70]
//   +0x0C  A90867FA  STP X26,X25,[SP,#0x80]
//   +0x10  A9095FF8  STP X24,X23,[SP,#0x90]
//   +0x14  A90A57F6  STP X22,X21,[SP,#0xA0]
//   +0x18  A90B4FF4  STP X20,X19,[SP,#0xB0]
//   +0x1C  52863908  MOV W8,#0x31C8
//
// Hooking +0x1C preserves the original X30 from the actual game caller.
// The replaced instruction is faithfully re-emulated by writing W8=0x31C8.
// No pointer fabrication, donor alias, or character-specific mutation.
static std::atomic<uint32_t> g_h19an_logs{0};


// R276H19AO: compact upstream structure scan on the proven caller path.
// Diagnostic only: no donor, no fabricated pointer, no ID/code special case.
static void H19AOScanStruct(const char* regname,
                            uint64_t base,
                            uint64_t live_x21,
                            uint64_t live_x27) {
    if (base < 0x100000000ULL) {
        Logging.Log("[NSC:H19AO] SCAN_SKIP reg=%s base=%p",
                    regname, reinterpret_cast<void*>(base));
        return;
    }

    const volatile uint64_t* q =
        reinterpret_cast<const volatile uint64_t*>(base);

    for (uint32_t i = 0; i < 16; i += 4) {
        const uint64_t v0 = q[i + 0];
        const uint64_t v1 = q[i + 1];
        const uint64_t v2 = q[i + 2];
        const uint64_t v3 = q[i + 3];

        Logging.Log(
            "[NSC:H19AO] SCAN reg=%s base=%p off=0x%02x q0=%p q1=%p q2=%p q3=%p",
            regname,
            reinterpret_cast<void*>(base),
            i * 8,
            reinterpret_cast<void*>(v0),
            reinterpret_cast<void*>(v1),
            reinterpret_cast<void*>(v2),
            reinterpret_cast<void*>(v3));

        const uint64_t vals[4] = {v0, v1, v2, v3};
        for (uint32_t j = 0; j < 4; ++j) {
            const uint32_t off = (i + j) * 8;
            if (live_x21 != 0 && vals[j] == live_x21) {
                Logging.Log(
                    "[NSC:H19AO] MATCH_X21 reg=%s base=%p off=0x%02x value=%p",
                    regname,
                    reinterpret_cast<void*>(base),
                    off,
                    reinterpret_cast<void*>(vals[j]));
            }
            if (live_x27 != 0 && vals[j] == live_x27) {
                Logging.Log(
                    "[NSC:H19AO] MATCH_X27 reg=%s base=%p off=0x%02x value=0x%llx",
                    regname,
                    reinterpret_cast<void*>(base),
                    off,
                    static_cast<unsigned long long>(vals[j]));
            }
        }
    }
}


// R276H19AP: dump the real caller code around the proven BL site.
//
// H19AN proved LR == main+0x75F0C8, so the BL itself is main+0x75F0C4.
// We dump raw AArch64 words from -0x100 through +0x20 relative to LR.
// This is read-only and executes only once.
static std::atomic<uint32_t> g_h19ap_dumped{0};

static void H19APDumpCallerCode(uint64_t lr) {
    // H19APB: valid Switch main text is in the 0x80xxxxxx range.
    // The old 4 GiB guard wrongly rejected the proven LR 0x8075F0C8.
    if (lr < 0x80000000ULL || lr > 0x90000000ULL) {
        Logging.Log("[NSC:H19APB] LR_REJECT lr=%p",
                    reinterpret_cast<void*>(lr));
        return;
    }

    uint32_t expected = 0;
    if (!g_h19ap_dumped.compare_exchange_strong(
            expected, 1, std::memory_order_relaxed)) {
        return;
    }

    const uint64_t start = lr - 0x100;
    const uint64_t end   = lr + 0x20;

    for (uint64_t pc = start; pc <= end; pc += 4) {
        const uint32_t word =
            *reinterpret_cast<const volatile uint32_t*>(pc);

        const int64_t delta =
            static_cast<int64_t>(pc) - static_cast<int64_t>(lr);
        const uint64_t rel =
            static_cast<uint64_t>(static_cast<int64_t>(0x75F0C8) + delta);

        Logging.Log(
            "[NSC:H19AP] CODE pc=%p rel=0x%llx word=0x%08x delta=%lld",
            reinterpret_cast<void*>(pc),
            static_cast<unsigned long long>(rel),
            word,
            static_cast<long long>(delta));
    }
}

HOOK_DEFINE_INLINE(H19ANRealCallerLRHook) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        if (!ctx) return;

        ctx->X[8] = 0x31C8u;

        const uint32_t n =
            g_h19an_logs.fetch_add(1, std::memory_order_relaxed);

        H19APDumpCallerCode(ctx->X[30]);

        Logging.Log(
            "[NSC:H19AN] CALL n=%u "
            "lr=%p x0=%p x1=%p x2=%p x3=%p x4=%p x5=%p x6=%p x7=%p "
            "x19=%p x20=%p x21=%p x22=%p x23=%p x24=%p x25=%p x26=%p x27=%p x28=%p",
            n,
            reinterpret_cast<void*>(ctx->X[30]),
            reinterpret_cast<void*>(ctx->X[0]),
            reinterpret_cast<void*>(ctx->X[1]),
            reinterpret_cast<void*>(ctx->X[2]),
            reinterpret_cast<void*>(ctx->X[3]),
            reinterpret_cast<void*>(ctx->X[4]),
            reinterpret_cast<void*>(ctx->X[5]),
            reinterpret_cast<void*>(ctx->X[6]),
            reinterpret_cast<void*>(ctx->X[7]),
            reinterpret_cast<void*>(ctx->X[19]),
            reinterpret_cast<void*>(ctx->X[20]),
            reinterpret_cast<void*>(ctx->X[21]),
            reinterpret_cast<void*>(ctx->X[22]),
            reinterpret_cast<void*>(ctx->X[23]),
            reinterpret_cast<void*>(ctx->X[24]),
            reinterpret_cast<void*>(ctx->X[25]),
            reinterpret_cast<void*>(ctx->X[26]),
            reinterpret_cast<void*>(ctx->X[27]),
            reinterpret_cast<void*>(ctx->X[28]));

        H19AOScanStruct("x19", ctx->X[19], ctx->X[21], ctx->X[27]);
        H19AOScanStruct("x24", ctx->X[24], ctx->X[21], ctx->X[27]);
        H19AOScanStruct("x28", ctx->X[28], ctx->X[21], ctx->X[27]);
    }
};


// R276H19AQ: trace the exact node returned by the native resolver.
//
// H19APB decoded the proven caller block (runtime/module-relative addresses):
//   0x75F040  MOV X0,X19
//   0x75F044  MOV W1,W27
//   0x75F04C  BL  0x7988E8
//   0x75F050  LDR X21,[X0]
//   0x75F054  MOV X0,X19
//   0x75F058  MOV W1,W27
//   0x75F05C  BL  0x7988E8
//   0x75F068  LDR W27,[X0,#8]
//
// Exlaunch InstallAtOffset() is text-relative and therefore 0x4000 lower:
//   runtime 0x75F050 -> exlaunch 0x75B050
//   runtime 0x75F068 -> exlaunch 0x75B068
//   runtime resolver 0x7988E8 -> exlaunch 0x7948E8
//
// These inline hooks only log the resolver node and faithfully re-emulate
// the replaced native loads. No pointer is fabricated or borrowed.
static std::atomic<uint32_t> g_h19aq_q0_logs{0};
static std::atomic<uint32_t> g_h19aq_q8_logs{0};


// R276H19AR: dump the implementation of the native resolver that produced
// the H19AQ node.
//
// H19AQ proved:
//   custom node != NULL, but [node+0] == 0 and [node+8] == 0
//   native node != NULL, [node+0] != 0 and [node+8] == 0x3F1
//
// At H19AQ Q0 site, X30 is the return address immediately after:
//   runtime main+0x75F04C BL runtime main+0x7988E8
// Therefore:
//   main_base = X30 - 0x75F050
//   resolver  = main_base + 0x7988E8
//
// Dump once, read-only, from resolver-0x40 through resolver+0x200.
static std::atomic<uint32_t> g_h19ar_dumped{0};

static void H19ARDumpResolverCode(uint64_t lr_after_resolver) {
    uint32_t expected = 0;
    if (!g_h19ar_dumped.compare_exchange_strong(
            expected, 1, std::memory_order_relaxed)) {
        return;
    }

    if (lr_after_resolver < 0x80000000ULL ||
        lr_after_resolver > 0x90000000ULL) {
        Logging.Log("[NSC:H19AR] LR_REJECT lr=%p",
                    reinterpret_cast<void*>(lr_after_resolver));
        return;
    }

    const uint64_t main_base = lr_after_resolver - 0x75F050ULL;
    const uint64_t resolver  = main_base + 0x7988E8ULL;
    const uint64_t start     = resolver - 0x40ULL;
    const uint64_t end       = resolver + 0x200ULL;

    Logging.Log(
        "[NSC:H19AR] RESOLVER_BASE main=%p resolver=%p range=%p..%p",
        reinterpret_cast<void*>(main_base),
        reinterpret_cast<void*>(resolver),
        reinterpret_cast<void*>(start),
        reinterpret_cast<void*>(end));

    for (uint64_t pc = start; pc <= end; pc += 4) {
        const uint32_t word =
            *reinterpret_cast<const volatile uint32_t*>(pc);

        const int64_t rel =
            static_cast<int64_t>(pc) - static_cast<int64_t>(main_base);

        Logging.Log(
            "[NSC:H19AR] CODE pc=%p rel=0x%llx word=0x%08x delta=%lld",
            reinterpret_cast<void*>(pc),
            static_cast<unsigned long long>(rel),
            word,
            static_cast<long long>(
                static_cast<int64_t>(pc) -
                static_cast<int64_t>(resolver)));
    }
}

HOOK_DEFINE_INLINE(H19AQResolverNodeQ0) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        if (!ctx) return;

        const uint64_t node = ctx->X[0];

        H19ARDumpResolverCode(ctx->X[30]);

        const volatile uint64_t* q =
            reinterpret_cast<const volatile uint64_t*>(node);

        // Original instruction: LDR X21,[X0]
        const uint64_t q0 = q[0];
        const uint64_t q8 = q[1];
        ctx->X[21] = q0;

        const uint32_t n =
            g_h19aq_q0_logs.fetch_add(1, std::memory_order_relaxed);

        Logging.Log(
            "[NSC:H19AQ] NODE_Q0 n=%u node=%p q0=%p q8=0x%llx "
            "x19=%p w27_in=0x%x x22=0x%llx x26=%p",
            n,
            reinterpret_cast<void*>(node),
            reinterpret_cast<void*>(q0),
            static_cast<unsigned long long>(q8),
            reinterpret_cast<void*>(ctx->X[19]),
            static_cast<unsigned>(ctx->X[27] & 0xffffffffu),
            static_cast<unsigned long long>(ctx->X[22]),
            reinterpret_cast<void*>(ctx->X[26]));
    }
};

HOOK_DEFINE_INLINE(H19AQResolverNodeQ8) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        if (!ctx) return;

        const uint64_t node = ctx->X[0];
        const volatile uint64_t* q =
            reinterpret_cast<const volatile uint64_t*>(node);

        const uint64_t q0 = q[0];
        const uint32_t q8w = *reinterpret_cast<const volatile uint32_t*>(node + 8);

        // Original instruction: LDR W27,[X0,#8]
        ctx->X[27] = static_cast<uint64_t>(q8w);

        const uint32_t n =
            g_h19aq_q8_logs.fetch_add(1, std::memory_order_relaxed);

        Logging.Log(
            "[NSC:H19AQ] NODE_Q8 n=%u node=%p q0=%p q8w=0x%x "
            "x19=%p x22=0x%llx x26=%p",
            n,
            reinterpret_cast<void*>(node),
            reinterpret_cast<void*>(q0),
            static_cast<unsigned>(q8w),
            reinterpret_cast<void*>(ctx->X[19]),
            static_cast<unsigned long long>(ctx->X[22]),
            reinterpret_cast<void*>(ctx->X[26]));
    }
};


// R276H19AS: trace the node-factory boundary used by the H19AR resolver.
//
// H19AR decoded:
//   runtime main+0x79893C  MOV W3,W19
//   runtime main+0x798940  BL  main+0x81D4E4
//   runtime main+0x798944  MOV X8,X0
//   runtime main+0x798948  STR X0,[X22]
//
// Exlaunch offsets = runtime/module-relative - 0x4000:
//   PRE  = 0x79493C
//   POST = 0x794944
//
// PRE re-emulates MOV W3,W19.
// POST re-emulates MOV X8,X0.
static std::atomic<uint32_t> g_h19as_pre_logs{0};
static std::atomic<uint32_t> g_h19as_post_logs{0};
static std::atomic<uint32_t> g_h19as_dumped{0};

static void H19ASDumpFactoryCode(uint64_t lr_after_factory) {
    uint32_t expected = 0;
    if (!g_h19as_dumped.compare_exchange_strong(
            expected, 1, std::memory_order_relaxed)) {
        return;
    }

    if (lr_after_factory < 0x80000000ULL ||
        lr_after_factory > 0x90000000ULL) {
        Logging.Log("[NSC:H19AS] FACTORY_LR_REJECT lr=%p",
                    reinterpret_cast<void*>(lr_after_factory));
        return;
    }

    const uint64_t main_base = lr_after_factory - 0x798944ULL;
    const uint64_t factory   = main_base + 0x81D4E4ULL;
    const uint64_t start     = factory - 0x20ULL;
    const uint64_t end       = factory + 0x280ULL;

    Logging.Log(
        "[NSC:H19AS] FACTORY_BASE main=%p factory=%p range=%p..%p",
        reinterpret_cast<void*>(main_base),
        reinterpret_cast<void*>(factory),
        reinterpret_cast<void*>(start),
        reinterpret_cast<void*>(end));

    for (uint64_t pc = start; pc <= end; pc += 4) {
        const uint32_t word =
            *reinterpret_cast<const volatile uint32_t*>(pc);
        const int64_t rel =
            static_cast<int64_t>(pc) - static_cast<int64_t>(main_base);

        Logging.Log(
            "[NSC:H19AS] CODE pc=%p rel=0x%llx word=0x%08x delta=%lld",
            reinterpret_cast<void*>(pc),
            static_cast<unsigned long long>(rel),
            word,
            static_cast<long long>(
                static_cast<int64_t>(pc) -
                static_cast<int64_t>(factory)));
    }
}


// R276H19AU: read-only static runtime scan for direct actor+0xE50/E54 refs.
//
// H19ATC hardware proved:
//   custom: E50=0, aux=0, same vtable/vfunc48 as native
//   native: E50=1, aux=1
//
// vfunc48:
//   LDR W0,[X0,#0xE50]
//   RET
//
// The unresolved boundary is now the native writer/populator of actor+0xE50.
// H19AU does not add hooks. It scans mapped main text once from the existing
// stable H19ASFactoryPre callback.
static std::atomic<uint32_t> g_h19au_scanned{0};

static void H19AUDumpContext(uint64_t main_base,
                             uint64_t pc,
                             const char* kind,
                             uint32_t field) {
    const uint64_t start = pc >= 0x20ULL ? pc - 0x20ULL : pc;
    const uint64_t end = pc + 0x20ULL;

    Logging.Log(
        "[NSC:H19AU] CONTEXT_BEGIN kind=%s field=0x%x pc=%p rel=0x%llx",
        kind,
        field,
        reinterpret_cast<void*>(pc),
        static_cast<unsigned long long>(pc - main_base));

    for (uint64_t q = start; q <= end; q += 4) {
        const uint32_t w =
            *reinterpret_cast<const volatile uint32_t*>(q);
        Logging.Log(
            "[NSC:H19AU] CODE pc=%p rel=0x%llx word=0x%08x delta=%lld",
            reinterpret_cast<void*>(q),
            static_cast<unsigned long long>(q - main_base),
            w,
            static_cast<long long>(
                static_cast<int64_t>(q) - static_cast<int64_t>(pc)));
    }

    Logging.Log(
        "[NSC:H19AU] CONTEXT_END kind=%s field=0x%x pc=%p",
        kind,
        field,
        reinterpret_cast<void*>(pc));
}

static void H19AUScanE50Refs(uint64_t lr_after_vfunc) {
    uint32_t expected = 0;
    if (!g_h19au_scanned.compare_exchange_strong(
            expected, 1, std::memory_order_relaxed)) {
        return;
    }

    if (lr_after_vfunc < 0x80000000ULL ||
        lr_after_vfunc > 0x90000000ULL) {
        Logging.Log("[NSC:H19AU] SCAN_SKIP lr=%p reason=bad_lr",
                    reinterpret_cast<void*>(lr_after_vfunc));
        return;
    }

    // H19AR/H19AT proved this BLR returns to runtime main+0x798930.
    const uint64_t main_base = lr_after_vfunc - 0x798930ULL;

    // v1.70 main .text envelope from the existing main audit.
    const uint64_t start = main_base + 0x4000ULL;
    const uint64_t end   = main_base + 0x12F5FD0ULL;

    constexpr uint32_t kE50W = 0xE50u / 4u;
    constexpr uint32_t kE54W = 0xE54u / 4u;
    constexpr uint32_t kE50X = 0xE50u / 8u;

    uint32_t refs = 0;
    uint32_t writes = 0;
    uint32_t contexts = 0;

    Logging.Log(
        "[NSC:H19AU] SCAN_BEGIN main=%p range=%p..%p "
        "fields=E50|E54 direct_unsigned_imm=1",
        reinterpret_cast<void*>(main_base),
        reinterpret_cast<void*>(start),
        reinterpret_cast<void*>(end));

    for (uint64_t pc = start; pc + 4 <= end; pc += 4) {
        const uint32_t word =
            *reinterpret_cast<const volatile uint32_t*>(pc);
        const uint32_t op = word & 0xFFC00000u;
        const uint32_t imm12 = (word >> 10) & 0xFFFu;
        const uint32_t rn = (word >> 5) & 0x1Fu;
        const uint32_t rt = word & 0x1Fu;

        const char* kind = nullptr;
        uint32_t field = 0;
        bool is_write = false;

        if (op == 0xB9000000u && (imm12 == kE50W || imm12 == kE54W)) {
            kind = "STRW";
            field = imm12 * 4u;
            is_write = true;
        } else if (op == 0xB9400000u &&
                   (imm12 == kE50W || imm12 == kE54W)) {
            kind = "LDRW";
            field = imm12 * 4u;
        } else if (op == 0xF9000000u && imm12 == kE50X) {
            kind = "STRX";
            field = 0xE50u;
            is_write = true;
        } else if (op == 0xF9400000u && imm12 == kE50X) {
            kind = "LDRX";
            field = 0xE50u;
        }

        if (!kind) continue;

        ++refs;
        if (is_write) ++writes;

        Logging.Log(
            "[NSC:H19AU] REF n=%u kind=%s field=0x%x pc=%p rel=0x%llx "
            "word=0x%08x rn=x%u rt=%u",
            refs - 1,
            kind,
            field,
            reinterpret_cast<void*>(pc),
            static_cast<unsigned long long>(pc - main_base),
            word,
            rn,
            rt);

        if (is_write && contexts < 32) {
            H19AUDumpContext(main_base, pc, kind, field);
            ++contexts;
        }
    }

    Logging.Log(
        "[NSC:H19AU] SCAN_END refs=%u writes=%u contexts=%u",
        refs, writes, contexts);
}


// R276H19AV: focused read-only code dump around the strongest E50 writer sites.
//
// H19AU hardware found 38 direct E50 STRW writers but only 2 direct E54 STRW
// writers. One E54 writer is paired tightly with an E50 writer:
//
//   main+0x75C994 STR W24,[X19,#0xE54]
//   main+0x75C9C0 STR W25,[X19,#0xE50]
//
// This is the strongest current initializer candidate because the same X19
// base receives both ID-like E54 and aux-like E50 fields in one code cluster.
//
// H19AV adds no hooks and mutates nothing. It dumps two focused regions once:
//   region A: main+0x759F80..0x75A0A0 (standalone E50 writer 0x75A040)
//   region B: main+0x75C880..0x75CAB0 (paired E54/E50 initializer cluster)
static std::atomic<uint32_t> g_h19av_dumped{0};

static void H19AVDumpRange(uint64_t main_base,
                           uint64_t start_rel,
                           uint64_t end_rel,
                           const char* name) {
    Logging.Log(
        "[NSC:H19AV] RANGE_BEGIN name=%s start_rel=0x%llx end_rel=0x%llx",
        name,
        static_cast<unsigned long long>(start_rel),
        static_cast<unsigned long long>(end_rel));

    for (uint64_t rel = start_rel; rel <= end_rel; rel += 4) {
        const uint64_t pc = main_base + rel;
        const uint32_t word =
            *reinterpret_cast<const volatile uint32_t*>(pc);
        Logging.Log(
            "[NSC:H19AV] CODE name=%s pc=%p rel=0x%llx word=0x%08x",
            name,
            reinterpret_cast<void*>(pc),
            static_cast<unsigned long long>(rel),
            word);
    }

    Logging.Log("[NSC:H19AV] RANGE_END name=%s", name);
}

static void H19AVDumpInitClusters(uint64_t lr_after_vfunc) {
    uint32_t expected = 0;
    if (!g_h19av_dumped.compare_exchange_strong(
            expected, 1, std::memory_order_relaxed)) {
        return;
    }

    if (lr_after_vfunc < 0x80000000ULL ||
        lr_after_vfunc > 0x90000000ULL) {
        Logging.Log("[NSC:H19AV] DUMP_SKIP lr=%p reason=bad_lr",
                    reinterpret_cast<void*>(lr_after_vfunc));
        return;
    }

    const uint64_t main_base = lr_after_vfunc - 0x798930ULL;

    Logging.Log(
        "[NSC:H19AV] DUMP_BEGIN main=%p candidate_a=0x75a040 "
        "candidate_pair_e54=0x75c994 candidate_pair_e50=0x75c9c0",
        reinterpret_cast<void*>(main_base));

    H19AVDumpRange(main_base, 0x759F80ULL, 0x75A0A0ULL, "E50_A");
    H19AVDumpRange(main_base, 0x75C880ULL, 0x75CAB0ULL, "E54_E50_PAIR");

    Logging.Log("[NSC:H19AV] DUMP_END");
}

HOOK_DEFINE_INLINE(H19ASFactoryPre) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        if (!ctx) return;

        // Original instruction: MOV W3,W19
        ctx->X[3] = static_cast<uint32_t>(ctx->X[19]);

        // H19AV: broad H19AU scan retired after hardware candidate discovery.

        H19AVDumpInitClusters(ctx->X[30]);

        const uint32_t idx = static_cast<uint32_t>(ctx->X[19]);
        const uint64_t slot = ctx->X[22];
        const uint64_t actor =
            slot - 0x11660ULL - static_cast<uint64_t>(idx) * 8ULL;

        const uint32_t field_e50 =
            *reinterpret_cast<const volatile uint32_t*>(actor + 0xE50ULL);
        const uint64_t vtable =
            *reinterpret_cast<const volatile uint64_t*>(actor);
        uint64_t vfunc48 = 0;
        if (vtable >= 0x80000000ULL && vtable <= 0x90000000ULL) {
            vfunc48 =
                *reinterpret_cast<const volatile uint64_t*>(vtable + 0x48ULL);
        }

        Logging.Log(
            "[NSC:H19ATC] FACTORY_AUX n=%u actor=%p field_e50=%u "
            "id_arg=%u aux_arg=%u index=%u vtable=%p vfunc48=%p slot=%p",
            g_h19as_pre_logs.load(std::memory_order_relaxed),
            reinterpret_cast<void*>(actor),
            static_cast<unsigned>(field_e50),
            static_cast<unsigned>(ctx->X[1] & 0xffffffffu),
            static_cast<unsigned>(ctx->X[2] & 0xffffffffu),
            static_cast<unsigned>(ctx->X[19] & 0xffffffffu),
            reinterpret_cast<void*>(vtable),
            reinterpret_cast<void*>(vfunc48),
            reinterpret_cast<void*>(slot));

        const uint32_t n =
            g_h19as_pre_logs.fetch_add(1, std::memory_order_relaxed);

        Logging.Log(
            "[NSC:H19AS] FACTORY_PRE n=%u actor=%p slot=%p "
            "manager=%p id=%u aux=%u index=%u "
            "x20=%p x21=%u x22=%p",
            n,
            reinterpret_cast<void*>(actor),
            reinterpret_cast<void*>(slot),
            reinterpret_cast<void*>(ctx->X[0]),
            static_cast<unsigned>(ctx->X[1] & 0xffffffffu),
            static_cast<unsigned>(ctx->X[2] & 0xffffffffu),
            idx,
            reinterpret_cast<void*>(ctx->X[20]),
            static_cast<unsigned>(ctx->X[21] & 0xffffffffu),
            reinterpret_cast<void*>(ctx->X[22]));
    }
};

HOOK_DEFINE_INLINE(H19ASFactoryPost) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        if (!ctx) return;

        const uint64_t node = ctx->X[0];

        // Original instruction: MOV X8,X0
        ctx->X[8] = node;

        uint64_t q0 = 0;
        uint64_t q8 = 0;
        if (node >= 0x100000000ULL) {
            const volatile uint64_t* q =
                reinterpret_cast<const volatile uint64_t*>(node);
            q0 = q[0];
            q8 = q[1];
        }

        const uint32_t idx = static_cast<uint32_t>(ctx->X[19]);
        const uint64_t slot = ctx->X[22];
        const uint64_t actor =
            slot - 0x11660ULL - static_cast<uint64_t>(idx) * 8ULL;

        const uint32_t n =
            g_h19as_post_logs.fetch_add(1, std::memory_order_relaxed);

        Logging.Log(
            "[NSC:H19AS] FACTORY_POST n=%u actor=%p slot=%p "
            "node=%p q0=%p q8=0x%llx id_saved=%u index=%u lr=%p",
            n,
            reinterpret_cast<void*>(actor),
            reinterpret_cast<void*>(slot),
            reinterpret_cast<void*>(node),
            reinterpret_cast<void*>(q0),
            static_cast<unsigned long long>(q8),
            static_cast<unsigned>(ctx->X[21] & 0xffffffffu),
            idx,
            reinterpret_cast<void*>(ctx->X[30]));

        H19ASDumpFactoryCode(ctx->X[30]);
    }
};


// R276H19AT: trace actor virtual method slot +0x48.
//
// H19ASB runtime:
//   custom factory input : aux=0
//   native factory input : aux=1
//
// H19AR decoded:
//   runtime 0x79891C  LDR X8,[X0]
//   runtime 0x798924  LDR W21,[X0,#0xE54]
//   runtime 0x798928  LDR X8,[X8,#0x48]
//   runtime 0x79892C  BLR X8
//   runtime 0x798930  MOV W2,W0
//
// Exlaunch offsets = runtime-relative - 0x4000:
//   PRE  = 0x794928
//   POST = 0x794930
static std::atomic<uint32_t> g_h19at_pre_logs{0};
static std::atomic<uint32_t> g_h19at_post_logs{0};
static std::atomic<uint64_t> g_h19at_fn1{0};
static std::atomic<uint64_t> g_h19at_fn2{0};

static void H19ATDumpVFuncCode(uint64_t fn) {
    if (fn < 0x80000000ULL || fn > 0x90000000ULL) {
        Logging.Log("[NSC:H19AT] VFUNC_DUMP_SKIP fn=%p reason=outside_main_window",
                    reinterpret_cast<void*>(fn));
        return;
    }

    bool should_dump = false;
    uint64_t cur1 = g_h19at_fn1.load(std::memory_order_relaxed);
    if (cur1 == fn) return;

    if (cur1 == 0) {
        uint64_t expected = 0;
        if (g_h19at_fn1.compare_exchange_strong(
                expected, fn, std::memory_order_relaxed)) {
            should_dump = true;
        } else if (expected == fn) {
            return;
        }
    }

    if (!should_dump) {
        uint64_t cur2 = g_h19at_fn2.load(std::memory_order_relaxed);
        if (cur2 == fn) return;
        if (cur2 == 0) {
            uint64_t expected = 0;
            if (g_h19at_fn2.compare_exchange_strong(
                    expected, fn, std::memory_order_relaxed)) {
                should_dump = true;
            }
        }
    }

    if (!should_dump) return;

    const uint64_t start = fn;
    const uint64_t end   = fn + 0x08ULL;

    Logging.Log("[NSC:H19AT] VFUNC_BASE fn=%p range=%p..%p",
                reinterpret_cast<void*>(fn),
                reinterpret_cast<void*>(start),
                reinterpret_cast<void*>(end));

    for (uint64_t pc = start; pc <= end; pc += 4) {
        const uint32_t word =
            *reinterpret_cast<const volatile uint32_t*>(pc);
        Logging.Log(
            "[NSC:H19AT] CODE pc=%p fn=%p delta=%lld word=0x%08x",
            reinterpret_cast<void*>(pc),
            reinterpret_cast<void*>(fn),
            static_cast<long long>(
                static_cast<int64_t>(pc) - static_cast<int64_t>(fn)),
            word);
    }
}

HOOK_DEFINE_INLINE(H19ATVFunc48Pre) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        if (!ctx) return;

        const uint64_t vtable = ctx->X[8];
        const uint64_t fn =
            *reinterpret_cast<const volatile uint64_t*>(vtable + 0x48ULL);

        // Original: LDR X8,[X8,#0x48]
        ctx->X[8] = fn;

        const uint32_t idx = static_cast<uint32_t>(ctx->X[1]);
        const uint64_t slot = ctx->X[22];
        const uint64_t actor =
            slot - 0x11660ULL - static_cast<uint64_t>(idx) * 8ULL;
        const uint32_t field_e50 =
            *reinterpret_cast<const volatile uint32_t*>(actor + 0xE50ULL);
        const uint32_t id =
            *reinterpret_cast<const volatile uint32_t*>(actor + 0xE54ULL);

        const uint32_t n =
            g_h19at_pre_logs.fetch_add(1, std::memory_order_relaxed);

        Logging.Log(
            "[NSC:H19ATB] VFUNC_PRE n=%u actor=%p field_e50=%u id=%u index=%u "
            "vtable=%p fn=%p slot=%p",
            n,
            reinterpret_cast<void*>(actor),
            static_cast<unsigned>(field_e50),
            static_cast<unsigned>(id),
            idx,
            reinterpret_cast<void*>(vtable),
            reinterpret_cast<void*>(fn),
            reinterpret_cast<void*>(slot));

        H19ATDumpVFuncCode(fn);
    }
};

HOOK_DEFINE_INLINE(H19ATVFunc48Post) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        if (!ctx) return;

        const uint32_t ret = static_cast<uint32_t>(ctx->X[0]);

        // Original: MOV W2,W0
        ctx->X[2] = static_cast<uint64_t>(ret);

        const uint32_t idx = static_cast<uint32_t>(ctx->X[19]);
        const uint64_t slot = ctx->X[22];
        const uint64_t actor =
            slot - 0x11660ULL - static_cast<uint64_t>(idx) * 8ULL;
        const uint32_t id =
            *reinterpret_cast<const volatile uint32_t*>(actor + 0xE54ULL);

        const uint32_t n =
            g_h19at_post_logs.fetch_add(1, std::memory_order_relaxed);

        Logging.Log(
            "[NSC:H19AT] VFUNC_POST n=%u actor=%p id=%u index=%u "
            "ret=%u slot=%p",
            n,
            reinterpret_cast<void*>(actor),
            static_cast<unsigned>(id),
            idx,
            static_cast<unsigned>(ret),
            reinterpret_cast<void*>(slot));
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

    static constexpr uint32_t kH19AMCallAExpected[] = {
        0xAA1603E2,
    };
    static constexpr uint32_t kH19AMCallBExpected[] = {
        0xAA1503E2,
    };

    static constexpr uint32_t kH19ANExpected[] = {
        0x52863908,
    };

    static constexpr uint32_t kH19AQNodeQ0Expected[] = {
        0xF9400015,
    };
    static constexpr uint32_t kH19AQNodeQ8Expected[] = {
        0xB940081B,
    };

    static constexpr uint32_t kH19ASPreExpected[] = {
        0x2A1303E3,
    };
    static constexpr uint32_t kH19ASPostExpected[] = {
        0xAA0003E8,
    };

    static constexpr uint32_t kH19ATPreExpected[] = {
        0xF9402508,
    };
    static constexpr uint32_t kH19ATPostExpected[] = {
        0x2A0003E2,
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
    if (!MatchWords(0x7E7EBC, kH19AMCallAExpected)) {
        LogFingerprintFail("H19AM_CALL_A", 0x7E7EBC); ok = false;
    }
    if (!MatchWords(0x7EBE48, kH19AMCallBExpected)) {
        LogFingerprintFail("H19AM_CALL_B", 0x7EBE48); ok = false;
    }
    if (!MatchWords(0x436034, kH19ANExpected)) {
        LogFingerprintFail("H19AN_CALLER_LR", 0x436034); ok = false;
    }
    if (!MatchWords(0x75B050, kH19AQNodeQ0Expected)) {
        LogFingerprintFail("H19AQ_NODE_Q0", 0x75B050); ok = false;
    }
    if (!MatchWords(0x75B068, kH19AQNodeQ8Expected)) {
        LogFingerprintFail("H19AQ_NODE_Q8", 0x75B068); ok = false;
    }
    if (!MatchWords(0x79493C, kH19ASPreExpected)) {
        LogFingerprintFail("H19AS_FACTORY_PRE", 0x79493C); ok = false;
    }
    if (!MatchWords(0x794944, kH19ASPostExpected)) {
        LogFingerprintFail("H19AS_FACTORY_POST", 0x794944); ok = false;
    }
    if (!MatchWords(0x794928, kH19ATPreExpected)) {
        LogFingerprintFail("H19AT_VFUNC48_PRE", 0x794928); ok = false;
    }
    if (!MatchWords(0x794930, kH19ATPostExpected)) {
        LogFingerprintFail("H19AT_VFUNC48_POST", 0x794930); ok = false;
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
    // R276H19AN: H19X entry trampoline disabled so original caller LR is preserved.
    H19XLookupTraceHook::InstallAtOffset(0x120A3D4);
    Logging.Log("[NSC:H19X] READY init=0 superseded=H19AN caller_lr=1 lookup=1 off=0x120a3d4");
    H19YRegistryLookupHook::InstallAtOffset(0x1207B38);
    Logging.Log("[NSC:H19Y] READY reg=1 off=0x1207b38");
    // H19ASB disabled superseded diagnostic: H19ZParentHook::InstallAtOffset(0x7EB94C);
    Logging.Log("[NSC:H19Z] READY parent=0 superseded=H19ASB off=0x7eb94c reg_scope=0x1207b38");
    // H19ASB disabled superseded diagnostic: H19AAParentHook::InstallAtOffset(0x7E64D4);
    Logging.Log("[NSC:H19AA] READY parent=0 superseded=H19ASB off=0x7e64d4 reg_scope=0x1207b38");
    Logging.Log("[NSC:H19AB] READY uncapped_filter=mtob|bod1 reg=0x1207b38");
    Logging.Log("[NSC:H19AC] READY bare_xfbin_probe=1 forms=pfxext|strip|pfxstrip");
    Logging.Log("[NSC:H19AD] READY exact_prefix_probe=mtobbod1.xfbin->data/spc/mtobbod1.xfbin");
    Logging.Log("[NSC:H19AG] READY adaptive=1 success_keys=1 loaded_paths=1 alias_cache=1 unresolved_only=1 hardcoded_id=0 hardcoded_code=0");
    Logging.Log("[NSC:H19AH] READY scoped_graph=1 runtime_code_discovery=1 exact=1 cache=1 transform=1 miss=1 loaded=1 hardcoded_id=0 hardcoded_code=0");
    Logging.Log("[NSC:H19AHB] READY build_fix=forward_decls+unused_annotation runtime_semantics=unchanged");
    Logging.Log("[NSC:H19AI] READY multi_stem_scope=1 stem_cap=16 hardcoded_id=0 hardcoded_code=0");
    Logging.Log("[NSC:H19AJB] READY charsel_prefetch=1 families=comboPrm|anmofs retry_cap=3 hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AK] READY charsel_prm_prefetch=1 families=prm|prm_load hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AKB] READY prm_load_namespace=spcload prm_namespace=spc hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AL] READY child_graph_prefetch=1 families=acc1|aws|bod1c|bod1l|bod1s|eff1|skl1|skl3|spl1|spl1_fin01 hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    // H19ASB disabled superseded diagnostic: H19AMCallsiteA::InstallAtOffset(0x7E7EBC);
    // H19ASB disabled superseded diagnostic: H19AMCallsiteB::InstallAtOffset(0x7EBE48);
    Logging.Log("[NSC:H19AM] READY x3_producer_trace=0 superseded=H19ASB callsites=0x7e7ebc|0x7ebe48 mutation=original_mov_only hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    H19ANRealCallerLRHook::InstallAtOffset(0x436034);
    Logging.Log("[NSC:H19AN] READY real_caller_lr=1 hook=0x436034 original=mov_w8_31c8 h19x_entry_trampoline=0 mutation=original_mov_only hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AO] READY x21_source_scan=1 regs=x19|x24|x28 range=0x00-0x78 hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AP] READY caller_code_dump=1 proven_bl=0x75f0c4 range=lr-0x100..lr+0x20 mutation=none hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19APB] READY caller_code_dump_guard_fix=1 valid_lr=0x80000000-0x90000000 proven_lr=0x8075f0c8 mutation=none hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    // H19AT retired proven H19AQ runtime hook: H19AQResolverNodeQ0::InstallAtOffset(0x75B050);
    // H19AT retired proven H19AQ runtime hook: H19AQResolverNodeQ8::InstallAtOffset(0x75B068);
    Logging.Log("[NSC:H19AQ] READY resolver_node_trace=0 superseded=H19AT resolver_exl=0x7948e8 q0_site_exl=0x75b050 q8_site_exl=0x75b068 runtime_bias=0x4000 mutation=original_loads_only hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AR] READY resolver_code_dump=1 resolver_runtime_rel=0x7988e8 range=-0x40..+0x200 mutation=none hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19ASB] READY trampoline_cleanup=1 disabled=H19Z|H19AA|H19AM_A|H19AM_B freed_hooks=4 keep=H19AN|H19AQ|H19AS mutation=none hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19ATC] READY factory_side_aux_trace=1 vfunc_site_hooks=0 field_e50_trace=1 vfunc48_pointer_trace=1 h19as_factory_trace=1 trampoline_delta_from_h19atb=-1 mutation=none hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AV] READY e50_init_cluster_dump=1 hooks_added=0 broad_scan=0 ranges=0x759f80-0x75a0a0|0x75c880-0x75cab0 target_pair=0x75c994|0x75c9c0 mutation=none hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19AU] READY e50_writer_scan=0 superseded=H19AV hooks_added=0 scan_fields=E50|E54 scan_ops=STRW|LDRW|STRX|LDRX context_writers=1 mutation=none hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    H19ASFactoryPre::InstallAtOffset(0x79493C);
    H19ASFactoryPost::InstallAtOffset(0x794944);
    Logging.Log("[NSC:H19AS] READY node_factory_trace=1 factory_runtime_rel=0x81d4e4 pre_exl=0x79493c post_exl=0x794944 cache_base=0x11660 mutation=original_mov_only hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    Logging.Log("[NSC:H19ATB] READY safe_vfunc48_trace=0 superseded=H19ATC pre_exl=0x794928 post_hook=0 field_e50_trace=1 h19as_factory_trace=1 trampoline_delta_from_h19at=-1 mutation=original_pre_instruction_only hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
    // H19ATC disabled unsafe vfunc-site PRE hook at 0x794928.
    // H19ATB disabled unsafe return-site POST hook at 0x794930.
    Logging.Log("[NSC:H19AT] READY vfunc48_trace=0 superseded=H19ATC pre_exl=0x794928 post_exl=0x794930 retired_h19aq_hooks=2 trampoline_net_delta=0 mutation=original_instructions_only hardcoded_id=0 hardcoded_code=0 donor_alias=0 fabricated_ptr=0 diagnostic_only=1");
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
