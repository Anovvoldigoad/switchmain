#pragma once

namespace nsc::runtime {

// Loader-neutral runtime entrypoint. The bootstrap (currently exlaunch/subsdk9)
// only has to initialize its hook backend, then call this function.
// Returns false on fail-closed initialization failures.
bool Initialize();

} // namespace nsc::runtime

extern "C" bool nsc_runtime_initialize();
