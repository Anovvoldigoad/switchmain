#pragma once
#include <cstddef>
#include <cstdint>

namespace nsc::factory {
inline constexpr std::size_t kCapacity = 1024;
inline constexpr std::size_t kProfileSize = 64 + 4 * kCapacity;
// Serialized little-endian profile. No pointers or native struct padding.
struct Profile { std::uint8_t bytes[kProfileSize]; };
class Registry {
    std::uint16_t selectors_[kCapacity]{};
    bool loaded_ = false;
    std::uint32_t count_ = 0;
public:
    // Startup only. A rejected profile leaves any accepted registry intact.
    bool Load(const void* data, std::size_t size);
    std::uint32_t Resolve(std::uint32_t character) const;
    std::uint32_t Count() const { return count_; }
};
bool LoadEmbeddedProfile();
bool InstallFactoryHook();
std::uint32_t Resolve(std::uint32_t character);
std::uint32_t Count();
}
extern "C" nsc::factory::Profile nsc_factory_profile;
