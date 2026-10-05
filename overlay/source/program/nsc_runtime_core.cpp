#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R249 follows R248 hardware: identity=46 resolves non-null, but model+0x90 stays null.
    // Trace the exact post-identity file-resource, chunk, and allocation gates. Read-only only.
    return nsc::InstallR249PostLookupResourceTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
