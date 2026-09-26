#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::InstallP125AP107GuidedSessionQualifiedState137Fallback();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC P125A P107-guided session-qualified state137 fallback exception");
}
