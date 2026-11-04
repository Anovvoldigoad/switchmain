#include "nsc_factory.hpp"
#include "nsc_factory_catalog.hpp"
extern "C" {
#include "nsc_sha256.h"
}

namespace nsc::factory {
namespace {
Registry registry;
std::uint32_t Read32(const std::uint8_t* p) {
    return p[0] | (std::uint32_t(p[1]) << 8) |
           (std::uint32_t(p[2]) << 16) | (std::uint32_t(p[3]) << 24);
}
std::uint16_t Read16(const std::uint8_t* p) {
    return p[0] | (std::uint16_t(p[1]) << 8);
}
bool Supported(std::uint16_t selector) {
    for (auto candidate : kSupportedSelectors) if (candidate == selector) return true;
    return false;
}
}
bool Registry::Load(const void* data, std::size_t size) {
    if (!data || size != kProfileSize) return false;
    const auto* b = static_cast<const std::uint8_t*>(data);
    constexpr std::uint8_t magic[16] = {'N','S','C','_','F','A','C','T','O','R','Y','_','V','1',0,0};
    for (unsigned i = 0; i < sizeof(magic); ++i) if (b[i] != magic[i]) return false;
    if (Read32(b + 16) != 1) return false;
    const auto count = Read32(b + 20);
    if (count > kCapacity) return false;
    for (unsigned i = 56; i < 64; ++i) if (b[i]) return false;
    SHA256_CTX ctx;
    std::uint8_t digest[32];
    nsc_sha256_init(&ctx);
    nsc_sha256_update(&ctx, b, 24);
    nsc_sha256_update(&ctx, b + 56, kProfileSize - 56);
    nsc_sha256_final(&ctx, digest);
    for (unsigned i = 0; i < sizeof(digest); ++i) if (digest[i] != b[24+i]) return false;
    std::uint16_t previous = 0;
    for (std::uint32_t i = 0; i < count; ++i) {
        const auto owner = Read16(b + 64 + 4*i);
        const auto selector = Read16(b + 66 + 4*i);
        if (owner >= kCapacity || (i && owner <= previous) || !Supported(selector)) return false;
        previous = owner;
    }
    for (std::size_t i = 64 + 4*count; i < kProfileSize; ++i) if (b[i]) return false;
    // All validation completes before publishing a new mapping. This is only
    // called during module initialization, before any factory callback runs.
    for (auto& selector : selectors_) selector = UINT16_MAX;
    for (std::uint32_t i = 0; i < count; ++i)
        selectors_[Read16(b + 64 + 4*i)] = Read16(b + 66 + 4*i);
    count_ = count;
    loaded_ = true;
    return true;
}
std::uint32_t Registry::Resolve(std::uint32_t character) const {
    if (!loaded_ || character >= kCapacity || selectors_[character] == UINT16_MAX) return character;
    return selectors_[character];
}
bool LoadEmbeddedProfile() { return registry.Load(&nsc_factory_profile, sizeof(nsc_factory_profile)); }
std::uint32_t Resolve(std::uint32_t character) { return registry.Resolve(character); }
std::uint32_t Count() { return registry.Count(); }
}
