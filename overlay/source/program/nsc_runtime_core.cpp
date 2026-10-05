#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R264 traces the exact target secondary preview object (+0x98) and draw submit.
    // Read-only only; no return/path/ID/state overrides.
    return nsc::InstallR264SecondaryPreviewDrawTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
