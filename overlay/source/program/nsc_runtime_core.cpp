#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R253 traces the Load::enter child-vector construction that R252 proved missing.
    // Read-only only; R250 sound.cpk remains the data carrier.
    return nsc::InstallR253LoadChildConstructionTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
