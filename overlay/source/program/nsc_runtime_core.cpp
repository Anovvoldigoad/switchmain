#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R204V is a temporary read-only post-registry state-gate diagnostic.
    // Historical R204J + R238A proved the primary mtob registry reaches result=1.
    // This run isolates the native ccUiCharacterSelect3DModel gates that must pass
    // before state fields +0x6C=1 and +0x5C=2 are committed.
    return nsc::InstallR204VCharselStateGateTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
