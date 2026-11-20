#pragma once
#include "nsc_pc_pack.hpp"
#include <cstddef>
#include <cstdint>
#include <cstring>

// OFFLINE/STAGING ONLY. Not an original Switch engine parameter consumer.
// Owner supplies stable writable arena for the entire bound lifetime.
// Single-threaded; external synchronization is mandatory. No CRI callbacks.
struct NSCPcPackLease {
    NSCPcPackLease() = default;
    // A lease cannot be duplicated or transferred implicitly: doing so would
    // create two independently bound handles to the same caller-owned arena.
    NSCPcPackLease(const NSCPcPackLease&) = delete;
    NSCPcPackLease& operator=(const NSCPcPackLease&) = delete;
    NSCPcPackLease(NSCPcPackLease&&) = delete;
    NSCPcPackLease& operator=(NSCPcPackLease&&) = delete;
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
        // Reject a source view into this control object before parsing any bytes.
        // A malformed caller must not cause pack validation to read past lease state.
        const auto self = reinterpret_cast<std::uintptr_t>(this);
        const auto s = reinterpret_cast<std::uintptr_t>(source);
        if (self > UINTPTR_MAX - sizeof(*this) ||
            s > UINTPTR_MAX - source_size ||
            (self < s + source_size && s < self + sizeof(*this))) return false;
        NSCPcPackSummary summary{};
        if (!nsc_pc_pack_validate(source, source_size, &summary)) return false;
        // Validate source before touching the caller's arena. Source and
        // destination MUST NOT overlap, including identity.
        const auto a = reinterpret_cast<std::uintptr_t>(storage);
        if (a > UINTPTR_MAX - storage_size || s > UINTPTR_MAX - source_size)
            return false;
        if (a < s + source_size && s < a + storage_size) return false;
        // A caller-owned arena may not be placed over this lease object.
        // Otherwise memcpy overwrites control fields before bind publishes state.
        if (self > UINTPTR_MAX - sizeof(*this) ||
            (a < self + sizeof(*this) && self < a + storage_size))
            return false;
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
        // Never write row metadata over the source arena or this lease.
        // A caller must supply a separate writable output object.
        const auto a = reinterpret_cast<std::uintptr_t>(arena);
        const auto o = reinterpret_cast<std::uintptr_t>(out);
        const auto self = reinterpret_cast<std::uintptr_t>(this);
        if (a > UINTPTR_MAX - capacity ||
            o > UINTPTR_MAX - sizeof(*out) ||
            self > UINTPTR_MAX - sizeof(*this) ||
            (a < o + sizeof(*out) && o < a + capacity) ||
            (self < o + sizeof(*out) && o < self + sizeof(*this)))
            return false;
        // Revalidate every read to reject mutable-arena corruption.
        // Only scalar row metadata is returned; never an arena pointer.
        NSCPcRawRow temporary{};
        if (!nsc_pc_pack_row_at(arena, length, family, ordinal, &temporary))
            return false;
        *out = temporary;
        return true;
    }


    // Offline consumer boundary: copy a validated raw row into caller storage.
    // Never expose a borrowed arena pointer; no game allocator or hook.
    // Destination must not alias any part of the staging arena.
    bool copy_row(std::uint32_t family, std::uint32_t ordinal,
                  void* destination, std::size_t destination_capacity,
                  std::size_t* copied) const {
        if (!bound || !arena || !destination || !copied ||
            family >= 9u || destination_capacity == 0u) return false;
        NSCPcRawRow record{};
        if (!row(family, ordinal, &record)) return false;
        const std::size_t dir = 64u + 48u * family;
        if (length < dir + 48u) return false;
        const auto read32 = [](const std::uint8_t* p) -> std::uint32_t {
            return std::uint32_t(p[0]) | (std::uint32_t(p[1]) << 8) |
                   (std::uint32_t(p[2]) << 16) | (std::uint32_t(p[3]) << 24);
        };
        const std::size_t base = read32(arena + dir);
        const std::size_t size = read32(arena + dir + 4u);
        if (record.offset > size || record.length > size - record.offset ||
            base > length || size > length - base ||
            record.length == 0u || record.length > destination_capacity)
            return false;
        const auto a = reinterpret_cast<std::uintptr_t>(arena);
        const auto d = reinterpret_cast<std::uintptr_t>(destination);
        if (a > UINTPTR_MAX - capacity ||
            d > UINTPTR_MAX - destination_capacity) return false;
        if (a < d + destination_capacity && d < a + capacity) return false;
        // Reject payload writes over the lease control object itself.
        const auto self = reinterpret_cast<std::uintptr_t>(this);
        if (self > UINTPTR_MAX - sizeof(*this) ||
            (self < d + destination_capacity && d < self + sizeof(*this)))
            return false;
        // The output-length pointer is caller-owned metadata, not an arena or
        // destination alias. Reject before either payload or metadata writes.
        const auto c = reinterpret_cast<std::uintptr_t>(copied);
        if (c > UINTPTR_MAX - sizeof(*copied) ||
            (self < c + sizeof(*copied) && c < self + sizeof(*this)) ||
            (a < c + sizeof(*copied) && c < a + capacity) ||
            (d < c + sizeof(*copied) && c < d + destination_capacity))
            return false;
        std::memcpy(destination, arena + base + record.offset, record.length);
        *copied = record.length;
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
