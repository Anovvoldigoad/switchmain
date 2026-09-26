#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"
#include "nsc_runtime_v2.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::v2::InstallResolverHookMigrationProbe();
    nsc::InstallP128AStaticPreciseGateCaveProof();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC V2C dynamic core migration exception");
}
