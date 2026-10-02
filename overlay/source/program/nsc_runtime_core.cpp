#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"
#include "nsc_runtime_v2.hpp"

namespace nsc::runtime {

bool Initialize() {
    // Keep the proven R181 install order unchanged. This file intentionally
    // contains no exlaunch entrypoint so another bootstrap can call the same
    // runtime ABI later without moving gameplay/core initialization again.
    nsc::v2::InstallResolverHookMigrationProbe();
    if (!nsc::v2::InstallOriginalMainRuntimePatches()) return false;
    if (!nsc::v2::InstallR181DpadFullEligibilityRollback()) return false;

    nsc::InstallP128AStaticPreciseGateCaveProof();
    nsc::InstallR172UjMissAnmDirectParity();
    nsc::InstallR175DpadLookupMatrixTrace();
    nsc::InstallR176ActionRegistryMatrixTrace();
    nsc::InstallR177ActionDescriptorMatrixTrace();
    nsc::InstallV2NStageRegistryProof();
    nsc::InstallV2PPassiveOrderProbe();
    return true;
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
