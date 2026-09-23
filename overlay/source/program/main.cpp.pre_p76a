#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::InstallP67AActiveSelector1ConsumerBridge();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC P67A active selector1 consumer bridge exception");
}
