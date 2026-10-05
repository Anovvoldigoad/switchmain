#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R265 extends the proven R264 target chain into the downstream per-render-object gate.
    // Read-only only; no return/path/ID/state overrides.
    return nsc::InstallR265DownstreamRenderGateTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
