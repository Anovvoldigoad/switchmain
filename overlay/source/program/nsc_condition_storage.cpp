#include "nsc_condition_storage.hpp"

namespace nsc::conditions {
void RawStorage::Forget(const void* owner) {
    Lock();
    for (auto& e : entries_) if (e.owner == owner) e = {};
    Unlock();
}
bool RawStorage::Record(const void* owner, const void* allocation, std::uint32_t count) {
    if (!owner) return false;
    Lock();
    Entry* target = nullptr;
    for (auto& e : entries_) {
        if (e.owner == owner) { target = &e; break; }
        if (!e.owner && !target) target = &e;
    }
    if (target) *target = {owner, allocation, count};
    Unlock();
    return target != nullptr;
}
bool RawStorage::Lookup(const void* owner, const void* allocation,
                        std::uint32_t index, void*& result) {
    result = nullptr;
    Lock();
    bool found = false;
    for (const auto& e : entries_) {
        if (e.owner != owner || e.allocation != allocation || !owner) continue;
        found = true;
        if (allocation && index < e.count) {
            const auto base = reinterpret_cast<std::uintptr_t>(allocation);
            const std::uint64_t delta = std::uint64_t(index) * 176u;
            if (delta <= UINTPTR_MAX - base)
                result = reinterpret_cast<void*>(base + delta);
        }
        break;
    }
    Unlock();
    return found;
}
}
