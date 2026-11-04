#include "lib.hpp"
#include "nsc_runtime_core.hpp"

// exlaunch is only the bootstrap adapter. Gameplay/runtime initialization lives
// behind nsc_runtime_initialize(), so a future external loader can call the same
// stable entrypoint without rewriting the NSC2Switch core.
extern "C" void exl_main(void* x0, void* x1) {
    (void)x0;
    (void)x1;
    exl::hook::Initialize();
    const bool initialized = nsc_runtime_initialize();
    Logging.Log("[NSC:PORT] BOOTSTRAP_RETURN initialized=%u api_complete=0 gameplay_verified=0",
                initialized ? 1u : 0u);
}

extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("NSC runtime bootstrap exception");
}
