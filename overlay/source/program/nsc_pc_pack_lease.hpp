#pragma once
#include "nsc_pc_pack.hpp"
#include <cstddef>
#include <cstdint>
#include <cstring>

// OFFLINE/STAGING ONLY. Not an original Switch engine parameter consumer.
// Owner supplies stable writable arena for the entire bound lifetime.
// Single-threaded; external synchronization is mandatory. No CRI callbacks.
struct NSCPcPackLease {
    std::uint8_t* arena = nullptr;
    std::size_t capacity = 0;
    std::size_t length = 0;
    bool bound = false;

    // No dynamic allocation; copy only AFTER validating source hashes and rows.
    // Reject rebind without explicit unbind to avoid overwriting live resources.
    bool bind(void* storage, std::size_t storage_size,
              const void* source, std::size_t source_size) {
        if (bound || !storage || !source || !source_size ||
            source_size > storage_size) return false;
        NSCPcPackSummary summary{};
        if (!nsc_pc_pack_validate(source, source_size, &summary)) return false;
        // Validate source before touching the caller's arena. Source and
        // destination MUST NOT overlap, including identity.
        const auto a = reinterpret_cast<std::uintptr_t>(storage);
        const auto s = reinterpret_cast<std::uintptr_t>(source);
        if (a > UINTPTR_MAX - storage_size || s > UINTPTR_MAX - source_size)
            return false;
        if (a < s + source_size && s < a + storage_size) return false;
        std::memcpy(storage, source, source_size);
        arena = static_cast<std::uint8_t*>(storage);
        capacity = storage_size;
        length = source_size;
        bound = true;
        return true;
    }

    bool row(std::uint32_t family, std::uint32_t ordinal,
             NSCPcRawRow* out) const {
        if (!bound || !arena || !out) return false;
        // Revalidate every read to reject mutable-arena corruption.
        // Only scalar row metadata is returned; never an arena pointer.
        NSCPcRawRow temporary{};
        if (!nsc_pc_pack_row_at(arena, length, family, ordinal, &temporary))
            return false;
        *out = temporary;
        return true;
    }

    // Does not dereference arena: owner may retire storage before unbind,
    // provided no concurrent row operation is running. No destructor hook.
    void unbind() {
        arena = nullptr;
        capacity = 0;
        length = 0;
        bound = false;
    }
};
