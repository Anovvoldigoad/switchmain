#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::InstallP76AForkRuntimeProbe();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC P76A fork runtime probe exception");
}
