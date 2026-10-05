#include "nsc_runtime_core.hpp"
#include "nsc_cpk_bridge.hpp"

namespace nsc::runtime {

bool Initialize() {
    // R270 follows log44: source188 and populate are healthy, but matcher returns 0.
    // Read-only exact fallback compare capture at main+0x11A2E34.
    return nsc::InstallR270MatcherFallbackCompareTrace();
}

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize() {
    return nsc::runtime::Initialize();
}
