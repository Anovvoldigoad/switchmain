#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R269 follows R268: count20==1 but child[0]==NULL.
    // Read-only: source188 link -> visual population -> descriptor matcher -> final list slot.
    return nsc::InstallR269BaseVisualPopulationTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
