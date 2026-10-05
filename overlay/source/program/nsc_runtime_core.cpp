#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R245G is a temporary read-only diagnostic runtime.
    // It preserves the proven R204J loader/registry visibility and adds only
    // the exact ccUiCharacterSelect3DModel state-advance gate trace.
    // No gameplay patches, CPK binder, numeric-ID expansion, or resource mutation.
    return nsc::InstallR245GPreviewStateGateTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
