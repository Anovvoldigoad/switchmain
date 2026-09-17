#include "nsc_cpk_bridge.hpp"

#include "lib.hpp"
#include <lib/hook/trampoline.hpp>
#include <lib/util/modules.hpp>
#include <program/loggers.hpp>

#include <atomic>
#include <cstdint>

namespace nsc {
namespace {

// v1.70 offsets
constexpr ptrdiff_t kCpkBindOffset        = 0x473190;
constexpr ptrdiff_t kOugiFinishIndexOffset = 0x44F264;

constexpr uint32_t kOugiFinishIndexFp[] = {
    0xD10203FF, 0xF9001BFE, 0xA90467FA, 0xA9055FF8,
    0xA90657F6, 0xA9074FF4, 0xAA0003F3, 0xAA0103E0,
};

std::atomic<uint32_t> g_ougi_finish_logs{0};

bool MatchWords(ptrdiff_t offset, const uint32_t* expected, size_t count = 8) {
    auto* p = reinterpret_cast<const uint32_t*>(exl::util::GetMainModuleInfo().m_Text.m_Start + offset);
    for (size_t i = 0; i < count; i++) {
        if (p[i] != expected[i]) return false;
    }
    return true;
}

// Minimal CPK bind (keep mod loading alive)
HOOK_DEFINE_TRAMPOLINE(CpkBindHook) {
    static uint64_t Callback(void* a0, void* a1, void* a2, void* a3) {
        static std::atomic<uint32_t> once{0};
        if (once.fetch_add(1) == 0) {
            // bind Tobi CPK once
            // (full bind logic can be restored from P43A if needed)
            Logging.Log("[NSC:P44A] CPK_BIND attempt");
        }
        return Orig(a0, a1, a2, a3);
    }
};

// P44A main probe
HOOK_DEFINE_TRAMPOLINE(OugiFinishIndexHook) {
    static void Callback(void* a0, void* a1) {
        const uint32_t n = g_ougi_finish_logs.fetch_add(1, std::memory_order_relaxed);
        if (n < 1024) {
            Logging.Log("[NSC:P44A] OUGI_FINISH_INDEX a0=%p a1=%p n=%u", a0, a1, n);
        }
        Orig(a0, a1);
    }
};

} // namespace

void InstallP44A() {
    bool cpk = false;
    bool ougi = false;

    // CPK (optional keep-alive)
    if (true) {
        CpkBindHook::InstallAtOffset(kCpkBindOffset);
        cpk = true;
    }

    // Main probe
    if (MatchWords(kOugiFinishIndexOffset, kOugiFinishIndexFp)) {
        OugiFinishIndexHook::InstallAtOffset(kOugiFinishIndexOffset);
        ougi = true;
    } else {
        Logging.Log("[NSC:P44A] FINGERPRINT FAIL ougi_finish_index @ 0x%lx", 
                    (unsigned long)kOugiFinishIndexOffset);
    }

    Logging.Log("[NSC:P44A] READY cpk=%d ougi_finish_index=%d offset=0x%lx",
                cpk ? 1 : 0, ougi ? 1 : 0, (unsigned long)kOugiFinishIndexOffset);
}

} // namespace nsc
