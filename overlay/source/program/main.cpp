#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::InstallP65ASourceParityActiveUjBridge();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC P65A source-parity active UJ bridge exception");
}
