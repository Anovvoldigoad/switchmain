#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R247 reconstructs the already-designed R204W four-state table tracer
    // on the materially changed R245C real-Tobi carrier. Read-only only.
    return nsc::InstallR252WaitChildReadinessTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
