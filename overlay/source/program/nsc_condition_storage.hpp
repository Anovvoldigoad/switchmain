#pragma once
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace nsc::conditions {
// Native conditionprm records (176 bytes) are a different table from the
// 32-byte ModdingAPI condition descriptors. Never share their count.
class RawStorage {
    struct Entry { const void* owner; const void* allocation; std::uint32_t count; };
    Entry entries_[16]{};
    std::atomic_flag lock_ = ATOMIC_FLAG_INIT;
    void Lock() { while (lock_.test_and_set(std::memory_order_acquire)) {} }
    void Unlock() { lock_.clear(std::memory_order_release); }
public:
    bool Record(const void* owner, const void* allocation, std::uint32_t count);
    void Forget(const void* owner);
    // false means this exact owner/allocation was not observed; true with a
    // null result means a captured table rejected the requested index.
    bool Lookup(const void* owner, const void* allocation, std::uint32_t index, void*& result);
};
bool InstallRawStorageHooks();
}
