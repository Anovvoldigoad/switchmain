#pragma once
#include <cstdint>

namespace nsc::controls {
// Called after the exact supported main-image guard, before any game writes.
bool Initialize();
// Returns affected actor, or nullptr when no permission was written.
// No actor pointers survive the call. Any nonzero enemy value selects enemy.
void* Apply(void* actor, std::int16_t enemy, std::int16_t selector, bool enabled);
}
