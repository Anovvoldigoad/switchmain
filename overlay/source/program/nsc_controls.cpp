#include "nsc_controls.hpp"
#include "lib.hpp"

namespace nsc::controls {
namespace {
std::uintptr_t main_base = 0;
// PC a2d0f220 MovesetPlus.cpp: permission indices, not PC actor offsets.
// Native consumer call sites are executed by test_native_controls.py.
constexpr std::uint8_t indexes[] = {0,2,4,6,8,9,10,11,12,13,14,15,16,17,18,19,20,22,7,1};
template<std::size_t N>
bool Matches(std::uintptr_t at, const std::uint32_t (&expected)[N]) {
    const auto* actual = reinterpret_cast<const std::uint32_t*>(at);
    for (std::size_t i = 0; i < N; ++i) if (actual[i] != expected[i]) return false;
    return true;
}
}
bool Initialize() {
    const auto base = exl::util::modules::GetTargetStart();
    static constexpr std::uint32_t disable[] = {
        0x8B214808,0x52842989,0x72A00029,0xB829691F,0xD65F03C0};
    static constexpr std::uint32_t enable[] = {
        0x8B214808,0x52842989,0x72A00029,0x5280002A,0xB829690A,0xD65F03C0};
    static constexpr std::uint32_t getter[] = {
        0x8B214808,0x52842989,0x72A00029,0xB8696900,0xD65F03C0};
    main_base = 0;
    if (!base || !Matches(base+0x93C4,disable) || !Matches(base+0x93D8,enable) ||
        !Matches(base+0x7D4588,getter)) return false;
    main_base = base;
    return true;
}
void* Apply(void* actor, std::int16_t enemy, std::int16_t selector, bool enabled) {
    if (!main_base || !actor || selector < 0 || selector >= 20) return nullptr;
    void* target = actor;
    if (enemy != 0) {
        // Native Event236 uses this ccPlayer virtual enemy lookup at +0xDD0.
        const auto* table = *reinterpret_cast<const std::uintptr_t* const*>(actor);
        if (!table || !table[0xDD0/sizeof(std::uintptr_t)]) return nullptr;
        using Enemy = void* (*)(void*);
        target = reinterpret_cast<Enemy>(table[0xDD0/sizeof(std::uintptr_t)])(actor);
        if (!target) return nullptr;
    }
    using Set = void (*)(void*, std::uint32_t);
    const auto set = reinterpret_cast<Set>(main_base + (enabled ? 0x93D8 : 0x93C4));
    set(target,indexes[selector]);
    // Source enable19 deliberately falls through to enable1; disable19 does not.
    if (enabled && selector == 19) set(target,2);
    return target;
}
}
