#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R267 follows the actual character-select base-model vtable draw path.
    // Read-only: typed nuccChunkAnm+0x08 -> secondary98+0x18 -> base visual draw.
    return nsc::InstallR267SecondaryInnerBaseDrawTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
