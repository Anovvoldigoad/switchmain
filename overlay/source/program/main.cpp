#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"
#include "nsc_runtime_v2.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::v2::InstallResolverHookMigrationProbe();
    if (!nsc::v2::InstallOriginalMainRuntimePatches()) return;
    if (!nsc::v2::InstallR179DpadAnimationEligibilityParity()) return;
    nsc::InstallP128AStaticPreciseGateCaveProof();
    nsc::InstallR172UjMissAnmDirectParity();
    nsc::InstallR175DpadLookupMatrixTrace();
    nsc::InstallR176ActionRegistryMatrixTrace();
    nsc::InstallR177ActionDescriptorMatrixTrace();
    nsc::InstallV2NStageRegistryProof();
    nsc::InstallV2PPassiveOrderProbe();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC V2D original-main runtime patch exception");
}
