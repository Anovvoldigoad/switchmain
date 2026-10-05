#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R266 follows the proven R265 objects=0 result upstream into the exact
    // model-child -> registration-bridge -> render-producer chain.
    // Read-only only; no return/path/ID/state overrides.
    return nsc::InstallR266RenderRegistrationProducerTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
