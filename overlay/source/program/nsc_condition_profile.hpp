#pragma once
#include <cstddef>
#include <cstdint>
namespace nsc::condition_profile {
inline constexpr std::uint32_t kNativeCount=512, kCapacity=512;
inline constexpr std::size_t kRecordSize=80, kProfileSize=64+kCapacity*kRecordSize;
struct Profile { std::uint8_t bytes[kProfileSize]; };
struct Descriptor {
    const char* name;
    std::uint32_t reaction, state, icon, status, aura, reserved;
};
static_assert(sizeof(Descriptor)==32);
// Startup only. No hot reload. A rejected profile leaves prior state intact.
bool LoadProfile(const void*,std::size_t);
bool LoadEmbeddedProfile();
std::uint32_t Count();
std::uint32_t TotalCount();
const Descriptor* Get(std::uint32_t index);
}
extern "C" nsc::condition_profile::Profile nsc_condition_profile;
