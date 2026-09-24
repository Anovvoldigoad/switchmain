#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::InstallP102AExactFallback74SuppressionCandidate();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC P102A exact fallback74 suppression exception");
}
