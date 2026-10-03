#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R204B is a temporary read-only diagnostic runtime.
    // It intentionally installs no gameplay patches, no CPK binder, no
    // numeric-ID expansion, and no custom resource mutation.
    return nsc::InstallR204BNativeMtobTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
