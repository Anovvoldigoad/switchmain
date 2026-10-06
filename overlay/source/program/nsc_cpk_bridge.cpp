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

// Switch v1.70 native CPK bind-with-priority boundary.
constexpr ptrdiff_t kCpkBindOffset = 0x473190;
constexpr int kModCpkPriority = 32;
constexpr const char* kModCpkPath = "sim:data/moddingapi/Tobi_Switch.cpk";

struct CpkPathArg {
    const char* path;
    uint64_t unk08;
    uint64_t unk10;
    uint64_t unk18;
};
static_assert(sizeof(CpkPathArg) == 0x20);

std::atomic<uint32_t> g_extra_bind_once{0};

bool StartsWith(const char* value, const char* prefix) {
    if (!value || !prefix) return false;
    while (*prefix) {
        if (*value++ != *prefix++) return false;
    }
    return true;
}

template <size_t N>
bool MatchWords(ptrdiff_t offset, const uint32_t (&expected)[N]) {
    const uintptr_t base = exl::util::modules::GetTargetStart();
    const auto* words = reinterpret_cast<const volatile uint32_t*>(base + offset);
    for (size_t i = 0; i < N; ++i) {
        if (words[i] != expected[i]) return false;
    }
    return true;
}

void LogFingerprintFail(ptrdiff_t offset) {
    const uintptr_t base = exl::util::modules::GetTargetStart();
    const auto* words = reinterpret_cast<const volatile uint32_t*>(base + offset);
    Logging.Log("[NSC:R276H19B] fingerprint FAIL CPK_BIND off=0x%lx word0=%08x",
                static_cast<unsigned long>(offset), words[0]);
}

HOOK_DEFINE_TRAMPOLINE(CpkBindHook) {
    static uint32_t Callback(CpkPathArg* desc, uint32_t* out_bind_id, int priority) {
        // Preserve the game's original bind first.
        const uint32_t original_result = Orig(desc, out_bind_id, priority);

        if (!desc || original_result == 0 || !desc->path ||
            !StartsWith(desc->path, "sim:")) {
            return original_result;
        }

        // Mount the external mod carrier only once per process.
        uint32_t expected = 0;
        if (!g_extra_bind_once.compare_exchange_strong(
                expected, 1, std::memory_order_acq_rel)) {
            return original_result;
        }

        // Zeroed descriptor fields preserve the historical plaintext/encryption=0 contract.
        CpkPathArg extra{kModCpkPath, 0, 0, 0};
        uint32_t extra_bind_id = 0;
        const uint32_t extra_result = Orig(&extra, &extra_bind_id, kModCpkPriority);

        Logging.Log("[NSC:R276H19B] CPK_BIND path=%s priority=%d result=%u bind_id=%u",
                    kModCpkPath, kModCpkPriority, extra_result, extra_bind_id);
        return original_result;
    }
};

} // namespace

bool InstallMinimalCpkBridge() {
    // Exact v1.70 prefix proven for main+0x473190. Fail closed on any drift.
    static constexpr uint32_t kExpected[] = {
        0xF81D0FFE, 0xA90157F6, 0xA9024FF4, 0xD000E6A8,
        0xF945ED08, 0xAA0003F5, 0xF9400100, 0xB4000200,
    };

    if (!MatchWords(kCpkBindOffset, kExpected)) {
        LogFingerprintFail(kCpkBindOffset);
        Logging.Log("[NSC:R276H19B] READY cpk=0 hooks=0 fail_closed=1");
        return false;
    }

    CpkBindHook::InstallAtOffset(kCpkBindOffset);
    Logging.Log("[NSC:R276H19B] READY cpk=1 hooks=1 mount_only=1 priority=32 plaintext=1");
    return true;
}

} // namespace nsc
