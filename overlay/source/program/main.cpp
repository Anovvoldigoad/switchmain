#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::InstallP109State137ProvenanceProbe();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC P109A state137 provenance probe exception");
}
