#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R248 follows the R247 hardware proof: target Load passes, Create::enter creates
    // a model, but Create::update never advances. Trace the exact model identity
    // lookup and model+0x90 readiness producer. Read-only only.
    return nsc::InstallR248CreateIdentityReadinessTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
