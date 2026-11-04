#include "nsc_condition_storage.hpp"
#include "lib.hpp"

namespace nsc::conditions {
namespace {
RawStorage storage;
HOOK_DEFINE_INLINE(RawAllocationHook) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        auto* owner = reinterpret_cast<std::uint8_t*>(ctx->X[19]);
        void* allocation = reinterpret_cast<void*>(ctx->X[0]);
        // exlaunch's trampoline executes STR X0,[X19,#0x18] after this
        // callback. X21 is the file's signed allocation count. Only record
        // metadata here; the original instruction publishes the pointer.
        const auto signed_count = static_cast<std::int64_t>(ctx->X[21]);
        const auto count = signed_count > 0 && signed_count <= INT32_MAX
            ? static_cast<std::uint32_t>(signed_count) : 0u;
        const bool captured = storage.Record(owner, allocation, count);
        Logging.Log("[NSC:PORT] RAW_CONDITION_TABLE owner=%p data=%p count=%u captured=%u",
                    owner, allocation, count, captured ? 1u : 0u);
    }
};
HOOK_DEFINE_INLINE(RawReleaseHook) {
    static void Callback(exl::hook::nx64::InlineCtx* ctx) {
        // The three native free paths next clear owner+0x18. Retire metadata
        // on both destructors and the reload path, before pointer reuse.
        storage.Forget(reinterpret_cast<void*>(ctx->X[19]));
    }
};
HOOK_DEFINE_REPLACE(RawGetterHook) {
    static void* Callback(void* owner, std::uint32_t index) {
        if (!owner) return nullptr;
        const auto* bytes = static_cast<const std::uint8_t*>(owner);
        const void* allocation = *reinterpret_cast<void* const*>(bytes + 0x18);
        if (!allocation) return nullptr;
        void* result = nullptr;
        if (storage.Lookup(owner, allocation, index, result)) return result;
        // Unknown storage is not proven to have even 512 entries. Reject it;
        // do not invent a bound when capture failed or the allocation changed.
        return nullptr;
    }
};
}
bool InstallRawStorageHooks() {
    const auto base = exl::util::modules::GetTargetStart();
    const auto* getter = reinterpret_cast<const std::uint32_t*>(base + 0x747870);
    static constexpr std::uint32_t expected[] = {
        0xF9400C08,0xF100011F,0x52804009,0x7A491022,
        0x52801609,0x9BA92028,0x9A9F3100,0xD65F03C0};
    for (unsigned i = 0; i < 8; ++i) if (getter[i] != expected[i]) return false;
    const auto allocation_word = *reinterpret_cast<const std::uint32_t*>(base + 0x7477B0);
    if (allocation_word != 0xF9000E60u) return false;
    static constexpr std::ptrdiff_t clear_sites[] = {0x747658,0x7476AC,0x747708};
    for (auto off : clear_sites)
        if (*reinterpret_cast<const std::uint32_t*>(base + off) != 0xF9000E7Fu) return false;
    RawAllocationHook::InstallAtOffset(0x7477B0);
    for (auto off : clear_sites) RawReleaseHook::InstallAtOffset(off);
    RawGetterHook::InstallAtOffset(0x747870);
    return true;
}
}
