#include "nsc_factory.hpp"
#include "lib.hpp"

namespace nsc::factory {
namespace {
HOOK_DEFINE_TRAMPOLINE(PlayerFactoryHook) {
    static void* Callback(std::uint32_t character, std::int32_t mode) {
        // Remap the class selector only. The native caller retains the original
        // roster ID and initializes identity/resources separately after return.
        return Orig(Resolve(character), mode);
    }
};
}
bool InstallFactoryHook() {
    if (!Count()) return true;
    const auto base = exl::util::modules::GetTargetStart();
    const auto* words = reinterpret_cast<const std::uint32_t*>(base + 0x7CAB00);
    static constexpr std::uint32_t expected[] = {
        0xF81E0FFE, 0xA9014FF4, 0x51015008, 0x2A0003F3,
        0x7100B91F, 0x54000548};
    for (unsigned i = 0; i < sizeof(expected)/sizeof(expected[0]); ++i)
        if (words[i] != expected[i]) return false;
    PlayerFactoryHook::InstallAtOffset(0x7CAB00);
    Logging.Log("[NSC:PORT] FACTORY_PROFILE entries=%u gameplay_verified=0", Count());
    return true;
}
}
