#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"
#include "nsc_runtime_v2.hpp"
#include "nsc_image_guard.hpp"
#include "nsc_condition_storage.hpp"
#include "nsc_factory.hpp"
#include "nsc_controls.hpp"
#include "nsc_cpk_profile.hpp"
#include "lib.hpp"

namespace nsc::runtime {

bool Initialize() {
    const auto& main = exl::util::GetMainModuleInfo();
    const auto profile = nsc::image::Identify(
        reinterpret_cast<const void*>(main.m_Text.m_Start), main.m_Text.m_Size);
    if (profile == nsc::image::Profile::Unsupported) {
        Logging.Log("[NSC:PORT] INIT_REJECT reason=unknown_main_text game_writes=0");
        return false;
    }
    Logging.Log("[NSC:PORT] IMAGE_VERIFIED profile=%u", static_cast<unsigned>(profile));
    if (!nsc::factory::LoadEmbeddedProfile()) {
        Logging.Log("[NSC:PORT] INIT_REJECT reason=invalid_factory_profile game_writes=0");
        return false;
    }
    if (!nsc::cpk::LoadEmbeddedProfile()) {
        Logging.Log("[NSC:PORT] INIT_REJECT reason=invalid_cpk_profile game_writes=0");
        return false;
    }
    if (!nsc::controls::Initialize()) {
        Logging.Log("[NSC:PORT] INIT_REJECT reason=native_controls_mismatch game_writes=0");
        return false;
    }
    // Keep the proven R181 install order unchanged. This file intentionally
    // contains no exlaunch entrypoint so another bootstrap can call the same
    // runtime ABI later without moving gameplay/core initialization again.
    nsc::v2::InstallResolverHookMigrationProbe();
    if (!nsc::v2::InstallR181DpadFullEligibilityRollback()) return false;
    if (!nsc::v2::InstallOriginalMainRuntimePatches()) return false;

    nsc::InstallP128AStaticPreciseGateCaveProof();
    nsc::InstallR172UjMissAnmDirectParity();
    nsc::InstallR175DpadLookupMatrixTrace();
    nsc::InstallR176ActionRegistryMatrixTrace();
    nsc::InstallR177ActionDescriptorMatrixTrace();
    nsc::InstallV2NStageRegistryProof();
    nsc::InstallV2PPassiveOrderProbe();
    // Install after the legacy descriptor setup has checked the untouched
    // raw-getter fingerprint. All installations occur before game startup.
    if (!nsc::conditions::InstallRawStorageHooks()) return false;
    if (!nsc::factory::InstallFactoryHook()) return false;
    return true;
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
