#pragma once
#include <cstddef>
#include <cstdint>

namespace nsc::image {
constexpr std::size_t kTextSize = 0x12f5fd0;
enum class Profile : unsigned { Unsupported, Stock170, R180 };
// Called before any game hook or text write. Both accepted inputs were audited
// against the user-provided NSOs, not merely a shared build ID.
Profile Identify(const void* text, std::size_t mapped_size);
}
