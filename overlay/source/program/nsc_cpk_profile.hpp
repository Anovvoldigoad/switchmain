#pragma once
#include <cstddef>
#include <cstdint>

namespace nsc::cpk {
inline constexpr std::size_t kCapacity = 32;
inline constexpr std::size_t kPathSize = 192;
inline constexpr std::size_t kRecordSize = 208;
inline constexpr std::size_t kProfileSize = 64 + kCapacity*kRecordSize;
struct Profile { std::uint8_t bytes[kProfileSize]; };
struct PathArg { const char* path; std::uint64_t flags, reserved10, reserved18; };
static_assert(sizeof(PathArg) == 0x20);
using Bind = std::uint32_t (*)(PathArg*, std::uint32_t*, int);
// Startup only, before game code. Failed validation leaves accepted state intact.
bool LoadProfile(const void* data, std::size_t size);
bool LoadEmbeddedProfile();
std::uint32_t Count();
std::uint32_t RegisteredCount();
bool BindingId(std::uint32_t index, std::uint32_t* out);
// Retry only pending entries after a successful original sim: bind. A busy
// nested/concurrent callback returns immediately. This is registration, not
// proof of CRI async completion, asset availability, or game loader lifecycle.
void AfterBind(const PathArg* request, std::uint32_t result, Bind original);
}
extern "C" nsc::cpk::Profile nsc_cpk_profile;
