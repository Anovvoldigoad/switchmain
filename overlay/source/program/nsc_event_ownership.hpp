#pragma once
#include <cstdint>

namespace nsc::events {
// The converter marks only PC API236 records. Native 0x81d120/0x81d0f8
// copies this uint16 into the runtime event; native event236 ignores it.
inline constexpr std::uint16_t kApiMarker = 0x4E53;
enum class Ownership : unsigned { Native, Api, InvalidApi };
inline Ownership Classify(const void* event) {
    if (!event) return Ownership::Native;
    const auto* p = static_cast<const std::uint8_t*>(event);
    const auto read16 = [p](unsigned offset) {
        return std::uint16_t(p[offset] | (unsigned(p[offset+1]) << 8));
    };
    if (read16(0x22) != 236 || read16(0x2A) != kApiMarker) return Ownership::Native;
    const auto op = read16(0x24);
    return op >= 1 && op <= 29 ? Ownership::Api : Ownership::InvalidApi;
}
}
