#include "lib.hpp"
#include "nsc_cpk_bridge.hpp"

extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    nsc::InstallP62APersistentUjControlGetter();
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC P62A persistent UJ control getter exception");
}
