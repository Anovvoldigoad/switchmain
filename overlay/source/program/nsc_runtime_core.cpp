#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R268 continues only after R267 proved base visual draw is reached.
    // Read-only: inspect secondary+0x28 visual list -> 0x11A3E3C child gate -> 0x11A2444 child draw.
    return nsc::InstallR268BaseVisualChildGateTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
